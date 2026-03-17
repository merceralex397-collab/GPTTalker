"""OpenCode-specific adapter with session support for coding-agent workflows."""

import time
from typing import Any

import httpx

from src.hub.services.session_store import SessionStore
from src.shared.logging import get_logger
from src.shared.models import LLMServiceInfo

logger = get_logger(__name__)


class OpenCodeAdapter:
    """OpenCode-specific adapter with session support.

    This adapter extends the base LLM client functionality with OpenCode-specific
    features including conversation history management, working directory context,
    and coding-agent response formatting.
    """

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        session_store: SessionStore,
        default_timeout: float = 180.0,
    ):
        """Initialize the OpenCode adapter.

        Args:
            http_client: HTTP client for making requests.
            session_store: Session store for conversation history.
            default_timeout: Default request timeout in seconds (longer for coding tasks).
        """
        self._client = http_client
        self._sessions = session_store
        self._default_timeout = default_timeout

    async def chat(
        self,
        service: LLMServiceInfo,
        prompt: str,
        session_id: str | None = None,
        working_dir: str | None = None,
        system_prompt: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        tools: list[dict] | None = None,
        include_history: bool = True,
    ) -> dict[str, Any]:
        """Send a chat request to OpenCode with session support.

        Args:
            service: OpenCode service configuration.
            prompt: User prompt.
            session_id: Optional session ID for conversation continuity.
            working_dir: Optional working directory for file operations.
            system_prompt: Optional system prompt.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.
            tools: Optional list of tools available to OpenCode.
            include_history: Whether to include conversation history.

        Returns:
            Dictionary with response and metadata.
        """
        start_time = int(time.time() * 1000)

        # Handle session management
        history: list[dict[str, Any]] = []
        effective_session_id = session_id

        if session_id:
            # Get or create session
            session = await self._sessions.get_session(session_id)
            if session is None and service.service_id:
                session = await self._sessions.create_session(
                    session_id=session_id,
                    service_id=service.service_id,
                    working_dir=working_dir,
                )

            if session and include_history:
                history = await self._sessions.get_history(session_id)

            # Update working directory if provided
            if working_dir and session:
                await self._sessions.update_working_dir(session_id, working_dir)

        # Build OpenCode-specific payload
        payload = self._build_payload(
            prompt=prompt,
            session_id=effective_session_id,
            working_dir=working_dir,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            tools=tools,
            history=history,
        )

        # Build headers
        headers = {}
        if service.api_key:
            headers["Authorization"] = f"Bearer {service.api_key}"

        # Make the request
        try:
            response = await self._client.post(
                service.endpoint,
                json=payload,
                timeout=self._default_timeout,
                headers=headers,
            )
            response.raise_for_status()
            result = response.json()

        except httpx.TimeoutException:
            latency_ms = int(time.time() * 1000) - start_time
            logger.error(
                "opencode_request_timeout",
                service_id=service.service_id,
                timeout=self._default_timeout,
                latency_ms=latency_ms,
            )
            return {
                "success": False,
                "error": f"Request timeout after {self._default_timeout}s",
                "latency_ms": latency_ms,
            }

        except httpx.HTTPStatusError as e:
            latency_ms = int(time.time() * 1000) - start_time
            logger.error(
                "opencode_request_failed",
                service_id=service.service_id,
                status_code=e.response.status_code,
                latency_ms=latency_ms,
            )
            return {
                "success": False,
                "error": f"HTTP error: {e.response.status_code}",
                "latency_ms": latency_ms,
            }

        except Exception as e:
            latency_ms = int(time.time() * 1000) - start_time
            logger.error(
                "opencode_request_error",
                service_id=service.service_id,
                error=str(e),
                latency_ms=latency_ms,
            )
            return {
                "success": False,
                "error": f"Request failed: {e}",
                "latency_ms": latency_ms,
            }

        # Parse response
        parsed = self._parse_response(result)
        latency_ms = int(time.time() * 1000) - start_time

        # Store conversation in session if session_id provided
        if session_id:
            # Add user message
            await self._sessions.add_message(
                session_id=session_id,
                role="user",
                content=prompt,
            )
            # Add assistant response
            if parsed.get("response"):
                await self._sessions.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=parsed["response"],
                    metadata={
                        "model": parsed.get("model"),
                        "tokens_used": parsed.get("tokens_used"),
                    },
                )

        logger.info(
            "opencode_request_success",
            service_id=service.service_id,
            latency_ms=latency_ms,
            tokens_used=parsed.get("tokens_used"),
            has_session=session_id is not None,
        )

        return {
            "success": True,
            **parsed,
            "latency_ms": latency_ms,
        }

    def _build_payload(
        self,
        prompt: str,
        session_id: str | None,
        working_dir: str | None,
        system_prompt: str | None,
        max_tokens: int,
        temperature: float,
        tools: list[dict] | None,
        history: list[dict[str, Any]] | None,
    ) -> dict[str, Any]:
        """Build OpenCode-specific request payload.

        Args:
            prompt: User prompt.
            session_id: Session ID for continuity.
            working_dir: Working directory for file operations.
            system_prompt: Optional system prompt.
            max_tokens: Maximum tokens.
            temperature: Sampling temperature.
            tools: Available tools.
            history: Conversation history.

        Returns:
            OpenCode-formatted payload.
        """
        payload: dict[str, Any] = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if session_id:
            payload["session_id"] = session_id

        if working_dir:
            payload["working_dir"] = working_dir

        if system_prompt:
            payload["system"] = system_prompt

        if tools:
            payload["tools"] = tools

        if history:
            # Include conversation history in the payload
            payload["history"] = [
                {"role": msg["role"], "content": msg["content"]} for msg in history
            ]

        return payload

    def _parse_response(self, response: dict[str, Any]) -> dict[str, Any]:
        """Parse OpenCode response into MCP-compatible format.

        Args:
            response: Raw OpenCode response.

        Returns:
            Parsed response with standardized fields.
        """
        # OpenCode response format handling
        # Try multiple common response formats

        # Format 1: Direct response field
        if "response" in response:
            return {
                "response": response["response"],
                "model": response.get("model"),
                "tokens_used": response.get("tokens_used"),
                "finish_reason": response.get("finish_reason"),
                "artifacts": response.get("artifacts", []),
                "tool_calls": response.get("tool_calls", []),
            }

        # Format 2: message field (OpenAI-compatible)
        if "message" in response:
            msg = response["message"]
            return {
                "response": msg.get("content", ""),
                "model": response.get("model"),
                "tokens_used": response.get("usage", {}).get("total_tokens"),
                "finish_reason": response.get("choices", [{}])[0].get("finish_reason")
                if response.get("choices")
                else None,
                "artifacts": [],
                "tool_calls": msg.get("tool_calls", []),
            }

        # Format 3: choices array
        if "choices" in response and response["choices"]:
            choice = response["choices"][0]
            return {
                "response": choice.get("message", {}).get("content", ""),
                "model": response.get("model"),
                "tokens_used": response.get("usage", {}).get("total_tokens"),
                "finish_reason": choice.get("finish_reason"),
                "artifacts": [],
                "tool_calls": choice.get("message", {}).get("tool_calls", []),
            }

        # Fallback: convert entire response to string
        logger.warning("opencode_unrecognized_response_format", response_keys=list(response.keys()))
        return {
            "response": str(response),
            "model": None,
            "tokens_used": None,
            "finish_reason": None,
            "artifacts": [],
            "tool_calls": [],
        }
