"""HTTP client for direct LLM service communication."""

import time
from typing import Any

import httpx

from src.shared.logging import get_logger
from src.shared.models import LLMServiceInfo, LLMServiceType

logger = get_logger(__name__)


class LLMServiceClient:
    """HTTP client for communicating with LLM services.

    This client is used when LLM services are accessible directly
    (e.g., local llama.cpp server, remote API endpoints).
    """

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        default_timeout: float = 120.0,
    ):
        """Initialize the LLM service client.

        Args:
            http_client: The underlying async HTTP client.
            default_timeout: Default request timeout in seconds.
        """
        self._client = http_client
        self._default_timeout = default_timeout

    async def chat(
        self,
        service: LLMServiceInfo,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: str | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Send a chat request to an LLM service.

        Args:
            service: LLM service configuration.
            prompt: User prompt.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.
            system_prompt: Optional system prompt.
            session_id: Optional session ID.

        Returns:
            Dictionary with response text and metadata.
        """
        # Build request payload based on service type
        if service.type == LLMServiceType.LLAMA:
            payload = self._build_llama_payload(prompt, max_tokens, temperature, system_prompt)
        elif service.type == LLMServiceType.OPENCODE:
            payload = self._build_opencode_payload(
                prompt, max_tokens, temperature, system_prompt, session_id
            )
        elif service.type == LLMServiceType.HELPER:
            payload = self._build_helper_payload(prompt, max_tokens, temperature, system_prompt)
        else:
            raise ValueError(f"Unsupported service type: {service.type}")

        # Build headers
        headers = {}
        if service.api_key:
            headers["Authorization"] = f"Bearer {service.api_key}"

        # Make the request
        response = await self._client.post(
            service.endpoint,
            json=payload,
            timeout=self._default_timeout,
            headers=headers,
        )

        response.raise_for_status()
        return self._parse_response(response.json(), service)

    async def chat_helper(
        self,
        service: LLMServiceInfo,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: str | None = None,
        use_chat_format: bool = False,
    ) -> dict[str, Any]:
        """Send a request to a helper-model service.

        Helper models are lighter-weight models for quick tasks like
        summarization, classification, and simple transformations.

        Args:
            service: Helper LLM service configuration.
            prompt: User prompt.
            max_tokens: Maximum tokens in response (default 500 for quick tasks).
            temperature: Sampling temperature.
            system_prompt: Optional system prompt.
            use_chat_format: If True, use chat-style messages format instead of prompt.

        Returns:
            Dictionary with response text and metadata.
        """
        start_time = int(time.time() * 1000)
        timeout = 60.0  # Shorter timeout for helper models

        # Build request payload
        if use_chat_format:
            payload = self._build_llama_payload(prompt, max_tokens, temperature, system_prompt)
        else:
            payload = self._build_helper_payload(prompt, max_tokens, temperature, system_prompt)

        # Build headers
        headers = {}
        if service.api_key:
            headers["Authorization"] = f"Bearer {service.api_key}"

        # Make the request with timeout handling
        try:
            response = await self._client.post(
                service.endpoint,
                json=payload,
                timeout=timeout,
                headers=headers,
            )
            response.raise_for_status()
            result = self._parse_response(response.json(), service)
            latency_ms = int(time.time() * 1000) - start_time

            return {
                "success": True,
                **result,
                "latency_ms": latency_ms,
            }

        except httpx.TimeoutException:
            latency_ms = int(time.time() * 1000) - start_time
            logger.error(
                "helper_request_timeout",
                service_id=service.service_id,
                timeout=timeout,
                latency_ms=latency_ms,
            )
            return {
                "success": False,
                "error": f"Request timeout after {timeout}s",
                "latency_ms": latency_ms,
            }

        except httpx.HTTPStatusError as e:
            latency_ms = int(time.time() * 1000) - start_time
            logger.error(
                "helper_request_failed",
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
                "helper_request_error",
                service_id=service.service_id,
                error=str(e),
                latency_ms=latency_ms,
            )
            return {
                "success": False,
                "error": f"Request failed: {e}",
                "latency_ms": latency_ms,
            }

    def _build_llama_payload(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: str | None,
    ) -> dict:
        """Build payload for llama.cpp-compatible API."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }

    def _build_opencode_payload(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: str | None,
        session_id: str | None,
    ) -> dict:
        """Build payload for OpenCode API."""
        # OpenCode-specific format
        return {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt,
            "session_id": session_id,
        }

    def _build_helper_payload(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: str | None,
    ) -> dict:
        """Build payload for helper model API."""
        return {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system_prompt": system_prompt,
        }

    def _parse_response(self, response: dict, service: LLMServiceInfo) -> dict:
        """Parse LLM service response into standardized format."""
        # Handle different response formats
        if "choices" in response:  # OpenAI-compatible
            choice = response["choices"][0]
            return {
                "response": choice.get("message", {}).get("content", ""),
                "model": response.get("model", service.name),
                "tokens_used": response.get("usage", {}).get("total_tokens"),
                "finish_reason": choice.get("finish_reason"),
            }
        elif "response" in response:  # llama.cpp format
            return {
                "response": response["response"],
                "model": response.get("model", service.name),
                "tokens_used": response.get("tokens_used"),
                "finish_reason": response.get("stop", "length"),
            }
        else:
            # Generic fallback
            return {
                "response": str(response),
                "model": service.name,
                "tokens_used": None,
                "finish_reason": None,
            }
