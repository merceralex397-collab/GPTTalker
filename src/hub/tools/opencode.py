"""OpenCode-specific tool handler with session support."""

import time
from typing import TYPE_CHECKING, Any

from src.shared.logging import get_logger
from src.shared.models import LLMServiceInfo, SchedulerInput, TaskClass

# Type hints for forward references
if TYPE_CHECKING:
    from src.hub.policy.distributed_scheduler import DistributedScheduler
    from src.hub.policy.llm_service_policy import LLMServicePolicy
    from src.hub.policy.task_routing_policy import TaskRoutingPolicy
    from src.hub.services.opencode_adapter import OpenCodeAdapter

logger = get_logger(__name__)


async def chat_opencode_handler(
    service_id: str | None = None,
    service_name: str | None = None,
    prompt: str = "",
    session_id: str | None = None,
    working_dir: str | None = None,
    system_prompt: str | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.7,
    include_history: bool = True,
    task_class: TaskClass | None = None,
    scheduler_input: SchedulerInput | None = None,
    llm_service_policy: "LLMServicePolicy | None" = None,
    opencode_adapter: "OpenCodeAdapter | None" = None,
    task_routing_policy: "TaskRoutingPolicy | None" = None,
    distributed_scheduler: "DistributedScheduler | None" = None,
) -> dict[str, Any]:
    """Handle chat_opencode tool invocation.

    This tool provides specialized OpenCode interaction with session support
    for coding-agent workflows. It maintains conversation history and working
    directory context across requests. If no service is specified, it uses
    task classification to select an appropriate backend.

    Optionally accepts SchedulerInput for distributed scheduling with
    node-aware selection, health filtering, and fallback handling.

    Args:
        service_id: Service identifier (validated against registry).
        service_name: Service name (alternative to service_id).
        prompt: User prompt to send to OpenCode.
        session_id: Optional session ID for conversation continuity.
        working_dir: Optional working directory for file operations.
        system_prompt: Optional system prompt.
        max_tokens: Maximum tokens in response.
        temperature: Sampling temperature.
        include_history: Whether to include conversation history.
        task_class: Optional task classification for auto-routing.
        scheduler_input: Optional scheduler input for distributed scheduling.
        llm_service_policy: LLMServicePolicy for service validation.
        opencode_adapter: OpenCodeAdapter for making requests.
        task_routing_policy: TaskRoutingPolicy for auto-routing.
        distributed_scheduler: DistributedScheduler for node-aware routing.

    Returns:
        Dictionary with OpenCode response and metadata.
    """
    if llm_service_policy is None:
        return {"success": False, "error": "LLMServicePolicy not available"}

    if opencode_adapter is None:
        return {"success": False, "error": "OpenCodeAdapter not available"}

    if not prompt:
        return {"success": False, "error": "Prompt is required"}

    # If no service specified, use task routing or distributed scheduler
    if not service_id and not service_name:
        # Use distributed scheduler if provided with scheduler input
        if scheduler_input and distributed_scheduler:
            return await chat_opencode_with_distributed_scheduler(
                prompt=prompt,
                session_id=session_id,
                working_dir=working_dir,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                include_history=include_history,
                task_class=task_class,
                scheduler_input=scheduler_input,
                llm_service_policy=llm_service_policy,
                opencode_adapter=opencode_adapter,
                distributed_scheduler=distributed_scheduler,
            )

        if task_routing_policy is None:
            return {
                "success": False,
                "error": "Either service_id/service_name or task_class is required",
            }

        return await chat_opencode_with_routing(
            prompt=prompt,
            session_id=session_id,
            working_dir=working_dir,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            include_history=include_history,
            task_class=task_class,
            llm_service_policy=llm_service_policy,
            opencode_adapter=opencode_adapter,
            task_routing_policy=task_routing_policy,
        )

    return await chat_opencode_impl(
        service_id=service_id,
        service_name=service_name,
        prompt=prompt,
        session_id=session_id,
        working_dir=working_dir,
        system_prompt=system_prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        include_history=include_history,
        llm_service_policy=llm_service_policy,
        opencode_adapter=opencode_adapter,
    )


async def chat_opencode_with_routing(
    prompt: str,
    session_id: str | None,
    working_dir: str | None,
    system_prompt: str | None,
    max_tokens: int,
    temperature: float,
    include_history: bool,
    task_class: TaskClass | None,
    llm_service_policy: "LLMServicePolicy",
    opencode_adapter: "OpenCodeAdapter",
    task_routing_policy: "TaskRoutingPolicy",
) -> dict[str, Any]:
    """Internal implementation using task routing.

    Args:
        prompt: User prompt.
        session_id: Optional session ID.
        working_dir: Optional working directory.
        system_prompt: Optional system prompt.
        max_tokens: Maximum tokens.
        temperature: Sampling temperature.
        include_history: Whether to include history.
        task_class: Task classification.
        llm_service_policy: Policy for validation.
        opencode_adapter: Adapter for requests.
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
            "error": f"No available OpenCode services found for task class: {task_class or TaskClass.CODING}",
            "task_class": (task_class or TaskClass.CODING).value,
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
            result = await opencode_adapter.chat(
                service=service,
                prompt=prompt,
                session_id=session_id,
                working_dir=working_dir,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                include_history=include_history,
            )

            result["service_id"] = service.service_id
            result["service_name"] = service.name
            result["session_id"] = session_id
            result["task_class"] = (task_class or TaskClass.CODING).value
            result["routing_used"] = True
            result["fallback_attempted"] = len(attempted_services) > 1

            return result

        except Exception as e:
            last_error = e
            errors.append(f"{service.service_id}: {str(e)}")
            logger.warning(
                "opencode_request_fallback",
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
        "opencode_request_all_services_failed",
        task_class=(task_class or TaskClass.CODING).value,
        attempted_services=attempted_services,
        errors=errors,
        latency_ms=latency_ms,
    )

    return {
        "success": False,
        "error": f"All OpenCode services failed. Last error: {last_error}",
        "task_class": (task_class or TaskClass.CODING).value,
        "attempted_services": attempted_services,
        "errors": errors,
        "latency_ms": latency_ms,
    }


async def chat_opencode_with_distributed_scheduler(
    prompt: str,
    session_id: str | None,
    working_dir: str | None,
    system_prompt: str | None,
    max_tokens: int,
    temperature: float,
    include_history: bool,
    task_class: TaskClass | None,
    scheduler_input: SchedulerInput,
    llm_service_policy: "LLMServicePolicy",
    opencode_adapter: "OpenCodeAdapter",
    distributed_scheduler: "DistributedScheduler",
) -> dict[str, Any]:
    """Handle chat_opencode with distributed scheduler.

    This implementation uses the distributed scheduler for node-aware
    service selection with health filtering and fallback handling.

    Args:
        prompt: User prompt.
        session_id: Optional session ID.
        working_dir: Optional working directory.
        system_prompt: Optional system prompt.
        max_tokens: Maximum tokens.
        temperature: Sampling temperature.
        include_history: Whether to include history.
        task_class: Task classification.
        scheduler_input: Scheduler input for distributed scheduling.
        llm_service_policy: Policy for validation.
        opencode_adapter: Adapter for requests.
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
        # Ensure task class is set to CODING for OpenCode
        if scheduler_input.task_class is None:
            scheduler_input.task_class = task_class or TaskClass.CODING

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
                "opencode_distributed_no_endpoint",
                service_id=service.service_id,
                trace_id=scheduler_input.trace_id,
            )
            # Try fallback chain
            return await _opencode_try_fallback_chain(
                fallback_chain=schedule_result.fallback_chain,
                prompt=prompt,
                session_id=session_id,
                working_dir=working_dir,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                include_history=include_history,
                opencode_adapter=opencode_adapter,
                start_time=start_time,
                task_class=scheduler_input.task_class,
                attempted_services=attempted_services,
                attempted_nodes=attempted_nodes,
                errors=errors,
            )

        # Make the request
        result = await opencode_adapter.chat(
            service=service,
            prompt=prompt,
            session_id=session_id,
            working_dir=working_dir,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            include_history=include_history,
        )

        latency_ms = int(time.time() * 1000) - start_time

        logger.info(
            "opencode_distributed_request_success",
            service_id=service.service_id,
            node_id=node.node_id,
            latency_ms=latency_ms,
            trace_id=scheduler_input.trace_id,
        )

        result["service_id"] = service.service_id
        result["service_name"] = service.name
        result["node_id"] = node.node_id
        result["node_name"] = node.name
        result["task_class"] = scheduler_input.task_class.value
        result["latency_ms"] = latency_ms
        result["routing_used"] = "distributed"
        result["fallback_chain"] = [
            {
                "service_id": fb.selected_service.service_id,
                "node_id": fb.selected_node.node_id,
            }
            for fb in schedule_result.fallback_chain
        ]

        return result

    except ValueError as e:
        latency_ms = int(time.time() * 1000) - start_time
        logger.warning(
            "opencode_distributed_scheduler_error",
            error=str(e),
            trace_id=scheduler_input.trace_id,
        )

        # Fall back to simple routing
        routing_policy = TaskRoutingPolicy(
            llm_service_policy=llm_service_policy,
            task_class=scheduler_input.task_class or TaskClass.CODING,
        )
        return await chat_opencode_with_routing(
            prompt=prompt,
            session_id=session_id,
            working_dir=working_dir,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            include_history=include_history,
            task_class=scheduler_input.task_class,
            llm_service_policy=llm_service_policy,
            opencode_adapter=opencode_adapter,
            task_routing_policy=routing_policy,
        )

    except Exception as e:
        latency_ms = int(time.time() * 1000) - start_time
        logger.error(
            "opencode_distributed_request_failed",
            error=str(e),
            trace_id=scheduler_input.trace_id,
        )

        # Try fallback chain if enabled
        if scheduler_input.allow_fallback:
            schedule_result = getattr(distributed_scheduler, "_last_result", None)
            if schedule_result:
                return await _opencode_try_fallback_chain(
                    fallback_chain=schedule_result.fallback_chain,
                    prompt=prompt,
                    session_id=session_id,
                    working_dir=working_dir,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    include_history=include_history,
                    opencode_adapter=opencode_adapter,
                    start_time=start_time,
                    task_class=scheduler_input.task_class,
                    attempted_services=attempted_services,
                    attempted_nodes=attempted_nodes,
                    errors=errors,
                )

        return {
            "success": False,
            "error": f"OpenCode request failed: {e}",
            "attempted_services": attempted_services,
            "attempted_nodes": attempted_nodes,
            "latency_ms": latency_ms,
        }


async def _opencode_try_fallback_chain(
    fallback_chain: list,
    prompt: str,
    session_id: str | None,
    working_dir: str | None,
    system_prompt: str | None,
    max_tokens: int,
    temperature: float,
    include_history: bool,
    opencode_adapter: "OpenCodeAdapter",
    start_time: int,
    task_class: TaskClass,
    attempted_services: list[str],
    attempted_nodes: list[str],
    errors: list[str],
) -> dict[str, Any]:
    """Try fallback chain for OpenCode requests.

    Args:
        fallback_chain: List of fallback SchedulerResults.
        prompt: User prompt.
        session_id: Optional session ID.
        working_dir: Optional working directory.
        system_prompt: Optional system prompt.
        max_tokens: Maximum tokens.
        temperature: Sampling temperature.
        include_history: Whether to include history.
        opencode_adapter: HTTP adapter.
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
            result = await opencode_adapter.chat(
                service=service,
                prompt=prompt,
                session_id=session_id,
                working_dir=working_dir,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                include_history=include_history,
            )

            latency_ms = int(time.time() * 1000) - start_time

            result["service_id"] = service.service_id
            result["service_name"] = service.name
            result["node_id"] = node.node_id
            result["node_name"] = node.name
            result["task_class"] = task_class.value
            result["latency_ms"] = latency_ms
            result["routing_used"] = "distributed_fallback"
            result["fallback_attempted"] = True

            return result

        except Exception as e:
            errors.append(f"{service.service_id}: {str(e)}")
            logger.warning(
                "opencode_fallback_failed",
                service_id=service.service_id,
                error=str(e),
            )

    # All fallbacks exhausted
    latency_ms = int(time.time() * 1000) - start_time
    return {
        "success": False,
        "error": f"All OpenCode services and fallbacks failed: {errors[-1] if errors else 'unknown'}",
        "task_class": task_class.value,
        "attempted_services": attempted_services,
        "attempted_nodes": attempted_nodes,
        "errors": errors,
        "latency_ms": latency_ms,
    }


async def chat_opencode_impl(
    service_id: str | None,
    service_name: str | None,
    prompt: str,
    session_id: str | None,
    working_dir: str | None,
    system_prompt: str | None,
    max_tokens: int,
    temperature: float,
    include_history: bool,
    llm_service_policy: "LLMServicePolicy",
    opencode_adapter: "OpenCodeAdapter",
) -> dict[str, Any]:
    """Internal implementation for chat_opencode.

    Args:
        service_id: Service identifier.
        service_name: Service name.
        prompt: User prompt.
        session_id: Optional session ID.
        working_dir: Optional working directory.
        system_prompt: Optional system prompt.
        max_tokens: Maximum tokens.
        temperature: Sampling temperature.
        include_history: Whether to include history.
        llm_service_policy: Policy for validation.
        opencode_adapter: Adapter for requests.

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
            "opencode_service_validation_failed",
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

    # Step 2: Check service has endpoint configured
    if not service.endpoint:
        logger.warning("opencode_service_no_endpoint", service_id=service.service_id)
        return {
            "success": False,
            "error": f"Service {service.name} has no endpoint configured",
            "service_id": service.service_id,
            "service_name": service.name,
            "latency_ms": int(time.time() * 1000) - start_time,
        }

    # Step 3: Send request to OpenCode with session support
    try:
        result = await opencode_adapter.chat(
            service=service,
            prompt=prompt,
            session_id=session_id,
            working_dir=working_dir,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            include_history=include_history,
        )

        # Add service metadata to response
        result["service_id"] = service.service_id
        result["service_name"] = service.name
        result["session_id"] = session_id

        return result

    except Exception as e:
        latency_ms = int(time.time() * 1000) - start_time
        logger.error(
            "opencode_request_failed",
            service_id=service.service_id,
            service_name=service.name,
            error=str(e),
            latency_ms=latency_ms,
        )

        return {
            "success": False,
            "error": f"OpenCode request failed: {e}",
            "service_id": service.service_id,
            "service_name": service.name,
            "latency_ms": latency_ms,
        }
