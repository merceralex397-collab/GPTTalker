"""LLM routing tools for chat_llm."""

import time
from typing import TYPE_CHECKING, Any

from src.shared.logging import get_logger
from src.shared.models import LLMServiceInfo, SchedulerInput, TaskClass

# Type hints for forward references
if TYPE_CHECKING:
    from src.hub.policy.distributed_scheduler import DistributedScheduler
    from src.hub.policy.llm_service_policy import LLMServicePolicy
    from src.hub.policy.task_routing_policy import TaskRoutingPolicy
    from src.hub.services.llm_client import LLMServiceClient

logger = get_logger(__name__)


async def chat_llm_handler(
    service_id: str | None = None,
    service_name: str | None = None,
    prompt: str = "",
    max_tokens: int = 1000,
    temperature: float = 0.7,
    system_prompt: str | None = None,
    session_id: str | None = None,
    task_class: TaskClass | None = None,
    scheduler_input: SchedulerInput | None = None,
    llm_service_policy: "LLMServicePolicy | None" = None,
    llm_client: "LLMServiceClient | None" = None,
    task_routing_policy: "TaskRoutingPolicy | None" = None,
    distributed_scheduler: "DistributedScheduler | None" = None,
) -> dict[str, Any]:
    """Handle chat_llm tool invocation.

    This tool routes LLM requests to approved backends after validating
    the service alias against the registry. If no service is specified,
    it uses task classification to select an appropriate backend.

    Optionally accepts SchedulerInput for distributed scheduling with
    node-aware selection, health filtering, and fallback handling.

    Args:
        service_id: Service identifier (validated against registry).
        service_name: Service name (alternative to service_id).
        prompt: User prompt to send to LLM.
        max_tokens: Maximum tokens in response.
        temperature: Sampling temperature.
        system_prompt: Optional system prompt.
        session_id: Optional session ID for conversation continuity.
        task_class: Optional task classification for auto-routing.
        scheduler_input: Optional scheduler input for distributed scheduling.
        llm_service_policy: LLMServicePolicy for service validation.
        llm_client: LLMServiceClient for making HTTP calls.
        task_routing_policy: TaskRoutingPolicy for auto-routing.
        distributed_scheduler: DistributedScheduler for node-aware routing.

    Returns:
        Dictionary with LLM response and metadata.
    """
    # Use distributed scheduler if provided with scheduler input
    if scheduler_input and distributed_scheduler:
        return await chat_llm_with_distributed_scheduler(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt,
            session_id=session_id,
            task_class=task_class,
            scheduler_input=scheduler_input,
            llm_service_policy=llm_service_policy,
            llm_client=llm_client,
            distributed_scheduler=distributed_scheduler,
        )
    if llm_service_policy is None:
        return {"success": False, "error": "LLMServicePolicy not available"}

    if llm_client is None:
        return {"success": False, "error": "LLMServiceClient not available"}

    if not prompt:
        return {"success": False, "error": "Prompt is required"}

    # If no service specified, use task routing
    if not service_id and not service_name:
        if task_routing_policy is None:
            return {
                "success": False,
                "error": "Either service_id/service_name or task_class is required",
            }

        return await chat_llm_with_routing(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt,
            session_id=session_id,
            task_class=task_class,
            llm_service_policy=llm_service_policy,
            llm_client=llm_client,
            task_routing_policy=task_routing_policy,
        )

    return await chat_llm_impl(
        service_id=service_id,
        service_name=service_name,
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        system_prompt=system_prompt,
        session_id=session_id,
        llm_service_policy=llm_service_policy,
        llm_client=llm_client,
    )


async def chat_llm_with_distributed_scheduler(
    prompt: str,
    max_tokens: int,
    temperature: float,
    system_prompt: str | None,
    session_id: str | None,
    task_class: TaskClass | None,
    scheduler_input: SchedulerInput,
    llm_service_policy: "LLMServicePolicy",
    llm_client: "LLMServiceClient",
    distributed_scheduler: "DistributedScheduler",
) -> dict[str, Any]:
    """Handle chat_llm with distributed scheduler.

    This implementation uses the distributed scheduler for node-aware
    service selection with health filtering and fallback handling.

    Args:
        prompt: User prompt.
        max_tokens: Maximum tokens.
        temperature: Sampling temperature.
        system_prompt: Optional system prompt.
        session_id: Optional session ID.
        task_class: Optional task classification.
        scheduler_input: Scheduler input for distributed scheduling.
        llm_service_policy: Policy for validation.
        llm_client: Client for HTTP calls.
        distributed_scheduler: Distributed scheduler instance.

    Returns:
        Response dictionary with metadata.
    """
    from src.hub.policy.task_routing_policy import TaskRoutingPolicy

    start_time = int(time.time() * 1000)
    attempted_services: list[str] = []
    attempted_nodes: list[str] = []
    errors: list[str] = []

    # Use distributed scheduler for selection
    try:
        # Ensure task class is set
        if scheduler_input.task_class is None:
            scheduler_input.task_class = task_class or TaskClass.CHAT

        # Get scheduling result
        schedule_result = await distributed_scheduler.schedule(scheduler_input)

        # Try the selected service
        service = schedule_result.selected_service
        node = schedule_result.selected_node
        attempted_services.append(service.service_id)
        attempted_nodes.append(node.node_id)

        # Check if service has endpoint
        if not service.endpoint:
            logger.warning(
                "llm_distributed_no_endpoint",
                service_id=service.service_id,
                trace_id=scheduler_input.trace_id,
            )
            # Try fallback chain
            return await _try_fallback_chain(
                fallback_chain=schedule_result.fallback_chain,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                system_prompt=system_prompt,
                session_id=session_id,
                llm_client=llm_client,
                start_time=start_time,
                task_class=scheduler_input.task_class,
                attempted_services=attempted_services,
                attempted_nodes=attempted_nodes,
                errors=errors,
            )

        # Make the request
        result = await llm_client.chat(
            service=service,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt,
            session_id=session_id,
        )

        latency_ms = int(time.time() * 1000) - start_time

        logger.info(
            "llm_distributed_request_success",
            service_id=service.service_id,
            node_id=node.node_id,
            latency_ms=latency_ms,
            tokens_used=result.get("tokens_used"),
            trace_id=scheduler_input.trace_id,
        )

        return {
            "success": True,
            "response": result.get("response"),
            "model": result.get("model"),
            "service_id": service.service_id,
            "service_name": service.name,
            "node_id": node.node_id,
            "node_name": node.name,
            "task_class": scheduler_input.task_class.value,
            "latency_ms": latency_ms,
            "tokens_used": result.get("tokens_used"),
            "finish_reason": result.get("finish_reason"),
            "routing_used": "distributed",
            "fallback_chain": [
                {
                    "service_id": fb.selected_service.service_id,
                    "node_id": fb.selected_node.node_id,
                }
                for fb in schedule_result.fallback_chain
            ],
        }

    except ValueError as e:
        latency_ms = int(time.time() * 1000) - start_time
        logger.warning(
            "llm_distributed_scheduler_error",
            error=str(e),
            trace_id=scheduler_input.trace_id,
        )

        # Fall back to simple routing
        routing_policy = TaskRoutingPolicy(
            llm_service_policy=llm_service_policy,
            task_class=scheduler_input.task_class or TaskClass.CHAT,
        )
        return await chat_llm_with_routing(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt,
            session_id=session_id,
            task_class=scheduler_input.task_class,
            llm_service_policy=llm_service_policy,
            llm_client=llm_client,
            task_routing_policy=routing_policy,
        )

    except Exception as e:
        latency_ms = int(time.time() * 1000) - start_time
        logger.error(
            "llm_distributed_request_failed",
            error=str(e),
            trace_id=scheduler_input.trace_id,
        )

        # Try fallback chain if enabled
        if scheduler_input.allow_fallback:
            return await _try_fallback_chain(
                fallback_chain=[],  # Fallback not available in error case
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                system_prompt=system_prompt,
                session_id=session_id,
                llm_client=llm_client,
                start_time=start_time,
                task_class=scheduler_input.task_class,
                attempted_services=attempted_services,
                attempted_nodes=attempted_nodes,
                errors=errors,
            )

        return {
            "success": False,
            "error": f"LLM request failed: {e}",
            "attempted_services": attempted_services,
            "attempted_nodes": attempted_nodes,
            "latency_ms": latency_ms,
        }


async def _try_fallback_chain(
    fallback_chain: list,
    prompt: str,
    max_tokens: int,
    temperature: float,
    system_prompt: str | None,
    session_id: str | None,
    llm_client: "LLMServiceClient",
    start_time: int,
    task_class: TaskClass,
    attempted_services: list[str],
    attempted_nodes: list[str],
    errors: list[str],
) -> dict[str, Any]:
    """Try fallback chain for LLM requests.

    Args:
        fallback_chain: List of fallback SchedulerResults.
        prompt: User prompt.
        max_tokens: Maximum tokens.
        temperature: Sampling temperature.
        system_prompt: Optional system prompt.
        session_id: Optional session ID.
        llm_client: HTTP client.
        start_time: Start time for latency calculation.
        task_class: Task classification.
        attempted_services: Services already attempted.
        attempted_nodes: Nodes already attempted.
        errors: Errors from previous attempts.

    Returns:
        Response dictionary.
    """
    for fb in fallback_chain:
        service = fb.selected_service
        node = fb.selected_node
        attempted_services.append(service.service_id)
        attempted_nodes.append(node.node_id)

        if not service.endpoint:
            errors.append(f"Service {service.service_id} has no endpoint")
            continue

        try:
            result = await llm_client.chat(
                service=service,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                system_prompt=system_prompt,
                session_id=session_id,
            )

            latency_ms = int(time.time() * 1000) - start_time

            return {
                "success": True,
                "response": result.get("response"),
                "model": result.get("model"),
                "service_id": service.service_id,
                "service_name": service.name,
                "node_id": node.node_id,
                "node_name": node.name,
                "task_class": task_class.value,
                "latency_ms": latency_ms,
                "tokens_used": result.get("tokens_used"),
                "finish_reason": result.get("finish_reason"),
                "routing_used": "distributed_fallback",
                "fallback_attempted": True,
            }

        except Exception as e:
            errors.append(f"{service.service_id}: {str(e)}")
            logger.warning(
                "llm_fallback_failed",
                service_id=service.service_id,
                error=str(e),
            )

    # All fallbacks exhausted
    latency_ms = int(time.time() * 1000) - start_time
    return {
        "success": False,
        "error": f"All LLM services and fallbacks failed: {errors[-1] if errors else 'unknown'}",
        "task_class": task_class.value,
        "attempted_services": attempted_services,
        "attempted_nodes": attempted_nodes,
        "errors": errors,
        "latency_ms": latency_ms,
    }


async def chat_llm_with_routing(
    prompt: str,
    max_tokens: int,
    temperature: float,
    system_prompt: str | None,
    session_id: str | None,
    task_class: TaskClass | None,
    llm_service_policy: "LLMServicePolicy",
    llm_client: "LLMServiceClient",
    task_routing_policy: "TaskRoutingPolicy",
) -> dict[str, Any]:
    """Internal implementation using task routing.

    Args:
        prompt: User prompt.
        max_tokens: Maximum tokens.
        temperature: Sampling temperature.
        system_prompt: Optional system prompt.
        session_id: Optional session ID.
        task_class: Optional task classification.
        llm_service_policy: Policy for validation.
        llm_client: Client for HTTP calls.
        task_routing_policy: Routing policy.

    Returns:
        Response dictionary with metadata.
    """
    start_time = int(time.time() * 1000)
    attempted_services: list[str] = []
    errors: list[str] = []

    # Use routing policy to get fallback chain
    fallback_chain = await task_routing_policy.get_fallback_chain()

    if not fallback_chain:
        return {
            "success": False,
            "error": f"No available LLM services found for task class: {task_class or TaskClass.CHAT}",
            "task_class": (task_class or TaskClass.CHAT).value,
            "latency_ms": int(time.time() * 1000) - start_time,
        }

    # Try each service in the fallback chain
    last_error: Exception | None = None
    for service in fallback_chain:
        attempted_services.append(service.service_id)

        # Skip if no endpoint
        if not service.endpoint:
            errors.append(f"Service {service.service_id} has no endpoint configured")
            continue

        try:
            result = await llm_client.chat(
                service=service,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                system_prompt=system_prompt,
                session_id=session_id,
            )

            latency_ms = int(time.time() * 1000) - start_time

            logger.info(
                "llm_request_success_with_routing",
                service_id=service.service_id,
                service_name=service.name,
                task_class=(task_class or TaskClass.CHAT).value,
                latency_ms=latency_ms,
                tokens_used=result.get("tokens_used"),
            )

            return {
                "success": True,
                "response": result.get("response"),
                "model": result.get("model"),
                "service_id": service.service_id,
                "service_name": service.name,
                "task_class": (task_class or TaskClass.CHAT).value,
                "latency_ms": latency_ms,
                "tokens_used": result.get("tokens_used"),
                "finish_reason": result.get("finish_reason"),
                "routing_used": True,
                "fallback_attempted": len(attempted_services) > 1,
            }

        except Exception as e:
            last_error = e
            errors.append(f"{service.service_id}: {str(e)}")
            logger.warning(
                "llm_request_fallback",
                service_id=service.service_id,
                service_name=service.name,
                error=str(e),
                error_type=type(e).__name__,
            )

            # Check if we should fallback
            if not task_routing_policy.should_fallback(e):
                break

    # All services failed
    latency_ms = int(time.time() * 1000) - start_time
    logger.error(
        "llm_request_all_services_failed",
        task_class=(task_class or TaskClass.CHAT).value,
        attempted_services=attempted_services,
        errors=errors,
        latency_ms=latency_ms,
    )

    return {
        "success": False,
        "error": f"All LLM services failed. Last error: {last_error}",
        "task_class": (task_class or TaskClass.CHAT).value,
        "attempted_services": attempted_services,
        "errors": errors,
        "latency_ms": latency_ms,
    }


async def chat_llm_impl(
    service_id: str | None,
    service_name: str | None,
    prompt: str,
    max_tokens: int,
    temperature: float,
    system_prompt: str | None,
    session_id: str | None,
    llm_service_policy: "LLMServicePolicy",
    llm_client: "LLMServiceClient",
) -> dict[str, Any]:
    """Internal implementation for chat_llm.

    Args:
        service_id: Service identifier.
        service_name: Service name.
        prompt: User prompt.
        max_tokens: Maximum tokens.
        temperature: Sampling temperature.
        system_prompt: Optional system prompt.
        session_id: Optional session ID.
        llm_service_policy: Policy for validation.
        llm_client: Client for HTTP calls.

    Returns:
        Response dictionary with metadata.
    """
    start_time = int(time.time() * 1000)

    # Step 1: Validate service access
    service: LLMServiceInfo | None = None
    try:
        if service_id:
            service = await llm_service_policy.validate_service_access(service_id)
        elif service_name:
            service = await llm_service_policy.validate_service_by_name(service_name)
    except ValueError as e:
        logger.warning(
            "llm_service_validation_failed",
            service_id=service_id,
            service_name=service_name,
            error=str(e),
        )
        return {
            "success": False,
            "error": f"Service validation failed: {e}",
            "latency_ms": int(time.time() * 1000) - start_time,
        }

    if not service:
        return {
            "success": False,
            "error": "Service not found",
            "latency_ms": int(time.time() * 1000) - start_time,
        }

    # Step 2: Check if service has endpoint configured
    if not service.endpoint:
        logger.warning("llm_service_no_endpoint", service_id=service.service_id)
        return {
            "success": False,
            "error": f"Service {service.name} has no endpoint configured",
            "service_id": service.service_id,
            "service_name": service.name,
            "latency_ms": int(time.time() * 1000) - start_time,
        }

    # Step 3: Route to service
    # For now, we support direct HTTP calls to services
    # Future: Route through node agent if service is hosted on a managed node
    try:
        result = await llm_client.chat(
            service=service,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt,
            session_id=session_id,
        )

        latency_ms = int(time.time() * 1000) - start_time

        logger.info(
            "llm_request_success",
            service_id=service.service_id,
            service_name=service.name,
            latency_ms=latency_ms,
            tokens_used=result.get("tokens_used"),
        )

        return {
            "success": True,
            "response": result.get("response"),
            "model": result.get("model"),
            "service_id": service.service_id,
            "service_name": service.name,
            "latency_ms": latency_ms,
            "tokens_used": result.get("tokens_used"),
            "finish_reason": result.get("finish_reason"),
        }

    except Exception as e:
        latency_ms = int(time.time() * 1000) - start_time
        logger.error(
            "llm_request_failed",
            service_id=service.service_id,
            service_name=service.name,
            error=str(e),
            latency_ms=latency_ms,
        )

        return {
            "success": False,
            "error": f"LLM request failed: {e}",
            "service_id": service.service_id,
            "service_name": service.name,
            "latency_ms": latency_ms,
        }
