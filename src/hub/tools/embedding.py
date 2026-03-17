"""Embedding tool handler for MCP protocol."""

from typing import TYPE_CHECKING

from fastapi import Request
from pydantic import BaseModel, Field

from src.shared.logging import get_logger
from src.shared.models import LLMServiceType, SchedulerInput, TaskClass

# Type hints for forward references
if TYPE_CHECKING:
    from src.hub.policy.distributed_scheduler import DistributedScheduler
    from src.hub.policy.llm_service_policy import LLMServicePolicy
    from src.hub.policy.task_routing_policy import TaskRoutingPolicy

logger = get_logger(__name__)


class ChatEmbeddingsParams(BaseModel):
    """Parameters for the chat_embeddings tool."""

    service_id: str | None = Field(None, description="LLM service identifier from the registry")
    service_name: str | None = Field(
        None, description="Human-readable service name (alternative to service_id)"
    )
    text: str | None = Field(None, description="Text to generate embeddings for (single)")
    texts: list[str] | None = Field(None, description="Texts to generate embeddings for (batch)")
    encoding_format: str = Field("float", description="Encoding format: float, base64, or int8")
    task_class: TaskClass | None = Field(
        None, description="Task classification for auto-routing (defaults to EMBEDDING)"
    )
    scheduler_input: SchedulerInput | None = Field(
        None, description="Optional scheduler input for distributed scheduling"
    )


async def chat_embeddings_handler(
    request: Request,
    params: ChatEmbeddingsParams,
    llm_policy: "LLMServicePolicy | None" = None,
    task_routing_policy: "TaskRoutingPolicy | None" = None,
    distributed_scheduler: "DistributedScheduler | None" = None,
) -> dict:
    """Generate embeddings for text using an approved embedding service.

    This handler validates the service against the registry and routes
    embedding requests to the configured embedding service. If no service
    is specified, it uses task classification to select an appropriate backend.

    Optionally accepts SchedulerInput for distributed scheduling with
    node-aware selection, health filtering, and fallback handling.

    Args:
        request: FastAPI request for context.
        params: Tool parameters.
        llm_policy: LLM service policy for validation.
        task_routing_policy: Task routing policy for auto-routing.
        distributed_scheduler: Distributed scheduler for node-aware routing.

    Returns:
        Dictionary with embedding results or error.
    """
    if llm_policy is None:
        return {
            "success": False,
            "error": "LLMServicePolicy not available",
        }

    # Get service_id from either parameter
    service_id = params.service_id or params.service_name

    # If no service specified, use task routing with EMBEDDING task class
    if not service_id:
        # Use distributed scheduler if provided with scheduler input
        if params.scheduler_input and distributed_scheduler:
            return await chat_embeddings_with_distributed_scheduler(
                params=params,
                llm_policy=llm_policy,
                distributed_scheduler=distributed_scheduler,
            )

        if task_routing_policy is None:
            return {
                "success": False,
                "error": "Either service_id/service_name is required",
            }

        return await chat_embeddings_with_routing(
            params=params,
            llm_policy=llm_policy,
            task_routing_policy=task_routing_policy,
        )

    # Validate service exists and is of type EMBEDDING
    service = await llm_policy.get_service(service_id)
    if service is None:
        return {
            "success": False,
            "error": f"Service '{service_id}' not found in registry",
        }

    # Verify service type is EMBEDDING
    if service.type != LLMServiceType.EMBEDDING:
        return {
            "success": False,
            "error": f"Service '{service_id}' is not an embedding service (type: {service.type})",
        }

    return await do_embedding_request(
        service=service,
        params=params,
        request=request,
    )


async def chat_embeddings_with_routing(
    params: ChatEmbeddingsParams,
    llm_policy: "LLMServicePolicy",
    task_routing_policy: "TaskRoutingPolicy",
) -> dict:
    """Internal implementation using task routing for embeddings.

    Args:
        params: Tool parameters.
        llm_policy: LLM service policy.
        task_routing_policy: Task routing policy.

    Returns:
        Embedding results or error.
    """
    from src.hub.policy.task_routing_policy import TaskRoutingPolicy as RoutingPolicy

    # Create a specific routing policy for EMBEDDING task class
    embedding_routing = RoutingPolicy(
        llm_service_policy=llm_policy,
        task_class=TaskClass.EMBEDDING,
        preferred_service_id=None,
    )

    # Get fallback chain
    fallback_chain = await embedding_routing.get_fallback_chain()

    # Filter to only EMBEDDING type services
    embedding_services = [s for s in fallback_chain if s.type == LLMServiceType.EMBEDDING]

    if not embedding_services:
        return {
            "success": False,
            "error": "No embedding services available",
            "task_class": TaskClass.EMBEDDING.value,
        }

    # Try each embedding service
    last_error: Exception | None = None
    attempted_services: list[str] = []
    errors: list[str] = []

    for service in embedding_services:
        attempted_services.append(service.service_id)

        if not service.endpoint:
            errors.append(f"Service {service.service_id} has no endpoint configured")
            continue

        try:
            result = await do_embedding_request(
                service=service,
                params=params,
                request=None,
            )

            if result.get("success"):
                result["task_class"] = TaskClass.EMBEDDING.value
                result["routing_used"] = True
                result["fallback_attempted"] = len(attempted_services) > 1
                return result

            last_error = Exception(result.get("error", "Unknown error"))
            errors.append(f"{service.service_id}: {result.get('error')}")

        except Exception as e:
            last_error = e
            errors.append(f"{service.service_id}: {str(e)}")

            if not embedding_routing.should_fallback(e):
                break

    return {
        "success": False,
        "error": f"All embedding services failed. Last error: {last_error}",
        "attempted_services": attempted_services,
        "errors": errors,
    }


async def chat_embeddings_with_distributed_scheduler(
    params: ChatEmbeddingsParams,
    llm_policy: "LLMServicePolicy",
    distributed_scheduler: "DistributedScheduler",
) -> dict:
    """Handle embeddings with distributed scheduler.

    This implementation uses the distributed scheduler for node-aware
    service selection with health filtering and fallback handling.

    Args:
        params: Tool parameters.
        llm_policy: LLM service policy.
        distributed_scheduler: Distributed scheduler instance.

    Returns:
        Embedding results or error.
    """
    from src.hub.services.embedding_client import EmbeddingServiceClient
    from src.hub.policy.task_routing_policy import TaskRoutingPolicy

    # Ensure task class is set to EMBEDDING
    scheduler_input = params.scheduler_input
    if scheduler_input.task_class is None:
        scheduler_input.task_class = TaskClass.EMBEDDING

    # Use distributed scheduler for selection
    try:
        # Get scheduling result
        schedule_result = await distributed_scheduler.schedule(scheduler_input)

        # Get the selected service
        service = schedule_result.selected_service
        node = schedule_result.selected_node

        # Verify it's an embedding service
        if service.type != LLMServiceType.EMBEDDING:
            logger.warning(
                "embedding_distributed_not_embedding_service",
                service_id=service.service_id,
                service_type=service.type.value,
            )
            # Fall back to routing
            embedding_routing = TaskRoutingPolicy(
                llm_service_policy=llm_policy,
                task_class=TaskClass.EMBEDDING,
            )
            return await chat_embeddings_with_routing(
                params=params,
                llm_policy=llm_policy,
                task_routing_policy=embedding_routing,
            )

        # Check if service has endpoint
        if not service.endpoint:
            logger.warning(
                "embedding_distributed_no_endpoint",
                service_id=service.service_id,
            )
            # Try fallback chain
            return await _embedding_try_fallback_chain(
                fallback_chain=schedule_result.fallback_chain,
                params=params,
                task_class=scheduler_input.task_class,
            )

        # Get embedding client - this is a simplified version
        # In practice, you'd get this from request.app.state or DI
        embedding_client: EmbeddingServiceClient | None = None

        if not embedding_client:
            return {
                "success": False,
                "error": "Embedding service client not initialized",
            }

        # Get text inputs
        texts: list[str]
        if params.texts:
            texts = params.texts
        elif params.text:
            texts = [params.text]
        else:
            return {
                "success": False,
                "error": "Either 'text' or 'texts' parameter must be provided",
            }

        # Make embedding request
        result = await embedding_client.embed_batch(
            service=service,
            texts=texts,
            encoding_format=params.encoding_format,
        )

        if result.get("success"):
            return {
                "success": True,
                "embeddings": result.get("embeddings"),
                "model": result.get("model"),
                "tokens_used": result.get("tokens_used"),
                "latency_ms": result.get("latency_ms"),
                "text_count": len(texts),
                "service_id": service.service_id,
                "service_name": service.name,
                "node_id": node.node_id,
                "node_name": node.name,
                "task_class": scheduler_input.task_class.value,
                "routing_used": "distributed",
                "fallback_chain": [
                    {
                        "service_id": fb.selected_service.service_id,
                        "node_id": fb.selected_node.node_id,
                    }
                    for fb in schedule_result.fallback_chain
                ],
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Embedding request failed"),
                "latency_ms": result.get("latency_ms"),
            }

    except ValueError as e:
        logger.warning(
            "embedding_distributed_scheduler_error",
            error=str(e),
        )

        # Fall back to simple routing
        embedding_routing = TaskRoutingPolicy(
            llm_service_policy=llm_policy,
            task_class=scheduler_input.task_class or TaskClass.EMBEDDING,
        )
        return await chat_embeddings_with_routing(
            params=params,
            llm_policy=llm_policy,
            task_routing_policy=embedding_routing,
        )

    except Exception as e:
        logger.error(
            "embedding_distributed_request_failed",
            error=str(e),
        )
        return {
            "success": False,
            "error": f"Embedding request failed: {e}",
        }


async def _embedding_try_fallback_chain(
    fallback_chain: list,
    params: ChatEmbeddingsParams,
    task_class: TaskClass,
) -> dict:
    """Try fallback chain for embedding requests.

    Args:
        fallback_chain: List of fallback SchedulerResults.
        params: Tool parameters.
        task_class: Task classification.

    Returns:
        Embedding results or error.
    """
    from src.hub.services.embedding_client import EmbeddingServiceClient

    embedding_client: EmbeddingServiceClient | None = None

    if not embedding_client:
        return {
            "success": False,
            "error": "Embedding service client not initialized",
        }

    # Get text inputs
    texts: list[str]
    if params.texts:
        texts = params.texts
    elif params.text:
        texts = [params.text]
    else:
        return {
            "success": False,
            "error": "Either 'text' or 'texts' parameter must be provided",
        }

    for fb in fallback_chain:
        service = fb.selected_service
        node = fb.selected_node

        if service.type != LLMServiceType.EMBEDDING:
            continue

        if not service.endpoint:
            continue

        try:
            result = await embedding_client.embed_batch(
                service=service,
                texts=texts,
                encoding_format=params.encoding_format,
            )

            if result.get("success"):
                return {
                    "success": True,
                    "embeddings": result.get("embeddings"),
                    "model": result.get("model"),
                    "tokens_used": result.get("tokens_used"),
                    "latency_ms": result.get("latency_ms"),
                    "text_count": len(texts),
                    "service_id": service.service_id,
                    "service_name": service.name,
                    "node_id": node.node_id,
                    "node_name": node.name,
                    "task_class": task_class.value,
                    "routing_used": "distributed_fallback",
                    "fallback_attempted": True,
                }

        except Exception as e:
            logger.warning(
                "embedding_fallback_failed",
                service_id=service.service_id,
                error=str(e),
            )

    return {
        "success": False,
        "error": "All embedding services and fallbacks failed",
    }


async def do_embedding_request(
    service,
    params: ChatEmbeddingsParams,
    request: Request | None,
) -> dict:
    """Execute embedding request to a service.

    Args:
        service: LLMServiceInfo for the embedding service.
        params: Tool parameters.
        request: FastAPI request (optional, for getting client).

    Returns:
        Embedding results.
    """
    # Validate encoding format
    valid_encodings = {"float", "base64", "int8"}
    if params.encoding_format not in valid_encodings:
        return {
            "success": False,
            "error": f"Invalid encoding_format: {params.encoding_format}. Must be one of {valid_encodings}",
        }

    # Get text inputs
    texts: list[str]
    if params.texts:
        texts = params.texts
    elif params.text:
        texts = [params.text]
    else:
        return {
            "success": False,
            "error": "Either 'text' or 'texts' parameter must be provided",
        }

    # Get embedding client from app state
    from src.hub.services.embedding_client import EmbeddingServiceClient

    embedding_client: EmbeddingServiceClient | None = None
    if request is not None:
        embedding_client = request.app.state.embedding_client

    if embedding_client is None:
        logger.error("embedding_client_not_initialized")
        return {
            "success": False,
            "error": "Embedding service not initialized",
        }

    # Make embedding request
    result = await embedding_client.embed_batch(
        service=service,
        texts=texts,
        encoding_format=params.encoding_format,
    )

    # Return response
    if result.get("success"):
        return {
            "success": True,
            "embeddings": result.get("embeddings"),
            "model": result.get("model"),
            "tokens_used": result.get("tokens_used"),
            "latency_ms": result.get("latency_ms"),
            "text_count": len(texts),
            "service_id": service.service_id,
            "service_name": service.name,
        }
    else:
        return {
            "success": False,
            "error": result.get("error", "Embedding request failed"),
            "latency_ms": result.get("latency_ms"),
        }
