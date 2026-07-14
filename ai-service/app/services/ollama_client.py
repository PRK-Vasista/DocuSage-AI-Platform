# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
HTTP client for the Ollama runtime container.

This is the only component that speaks directly to Ollama. The rest of the AI
service depends on this client so the provider can be swapped later.
"""

import logging
from typing import Any

import httpx

from ..core.config import ai_settings
from ..core.exceptions import OllamaInferenceError, OllamaUnavailableError

logger = logging.getLogger("ai_service.ollama_client")


async def check_ollama_health() -> bool:
    """
    Probe the Ollama tags endpoint to verify connectivity.

    Returns:
        bool: True when Ollama responds successfully.
    """
    url = f"{ai_settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            logger.info("Ollama health check succeeded.")
            return True
    except Exception as exc:
        logger.warning("Ollama health check failed: %s", exc)
        return False


async def is_configured_model_present() -> bool:
    """
    Return True when the configured model name appears in Ollama's local list.

    Returns:
        bool: True if model is listed (warmed/pulled enough to use).
    """
    url = f"{ai_settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags"
    target = ai_settings.OLLAMA_MODEL.lower()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            models = response.json().get("models") or []
            for entry in models:
                name = str(entry.get("name") or "").lower()
                if name == target or name.startswith(f"{target}:"):
                    return True
            return False
    except Exception as exc:
        logger.warning("Ollama model list check failed: %s", exc)
        return False


async def ensure_model_available() -> None:
    """
    Request Ollama to pull the configured model if it is not already present.

    Raises:
        OllamaUnavailableError: If Ollama cannot be reached.
        OllamaInferenceError: If the pull request fails.
    """
    if not ai_settings.OLLAMA_PULL_ON_STARTUP:
        logger.info("Skipping Ollama model pull (disabled by config).")
        return

    url = f"{ai_settings.OLLAMA_BASE_URL.rstrip('/')}/api/pull"
    payload = {"name": ai_settings.OLLAMA_MODEL, "stream": False}
    logger.info("Ensuring Ollama model is available: %s", ai_settings.OLLAMA_MODEL)

    try:
        async with httpx.AsyncClient(timeout=ai_settings.OLLAMA_TIMEOUT_SECONDS) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            logger.info("Ollama model pull completed for %s", ai_settings.OLLAMA_MODEL)
    except httpx.RequestError as exc:
        logger.error("Failed to reach Ollama for model pull: %s", exc)
        raise OllamaUnavailableError(
            "Cannot reach Ollama to pull the configured model."
        ) from exc
    except httpx.HTTPStatusError as exc:
        logger.error("Ollama model pull failed: %s", exc)
        raise OllamaInferenceError("Failed to pull the configured Ollama model.") from exc


async def generate_completion(prompt: str) -> str:
    """
    Run a non-streaming completion against Ollama.

    Args:
        prompt: Full prompt text for the model.

    Returns:
        str: Generated model text.

    Raises:
        OllamaUnavailableError: If Ollama cannot be reached.
        OllamaInferenceError: If generation fails or returns empty output.
    """
    url = f"{ai_settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
    payload: dict[str, Any] = {
        "model": ai_settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    logger.info(
        "Requesting Ollama completion: model=%s prompt_chars=%s",
        ai_settings.OLLAMA_MODEL,
        len(prompt),
    )

    try:
        async with httpx.AsyncClient(timeout=ai_settings.OLLAMA_TIMEOUT_SECONDS) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.RequestError as exc:
        logger.error("Ollama generate request failed: %s", exc)
        raise OllamaUnavailableError("Cannot reach Ollama for generation.") from exc
    except httpx.HTTPStatusError as exc:
        logger.error("Ollama generate returned HTTP error: %s", exc)
        raise OllamaInferenceError("Ollama generation request failed.") from exc

    text = (data.get("response") or "").strip()
    if not text:
        logger.error("Ollama returned an empty completion response.")
        raise OllamaInferenceError("Ollama returned an empty response.")

    logger.info("Ollama completion succeeded: response_chars=%s", len(text))
    return text


async def generate_chat(messages: list[dict[str, str]]) -> str:
    """
    Run a non-streaming chat completion against Ollama.

    Args:
        messages: Chat messages in OpenAI-like role/content format.

    Returns:
        str: Assistant reply text.

    Raises:
        OllamaUnavailableError: If Ollama cannot be reached.
        OllamaInferenceError: If chat generation fails or returns empty output.
    """
    url = f"{ai_settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat"
    payload: dict[str, Any] = {
        "model": ai_settings.OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
    }
    logger.info(
        "Requesting Ollama chat: model=%s messages=%s",
        ai_settings.OLLAMA_MODEL,
        len(messages),
    )

    try:
        async with httpx.AsyncClient(timeout=ai_settings.OLLAMA_TIMEOUT_SECONDS) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.RequestError as exc:
        logger.error("Ollama chat request failed: %s", exc)
        raise OllamaUnavailableError("Cannot reach Ollama for chat.") from exc
    except httpx.HTTPStatusError as exc:
        logger.error("Ollama chat returned HTTP error: %s", exc)
        raise OllamaInferenceError("Ollama chat request failed.") from exc

    message = data.get("message") or {}
    text = (message.get("content") or "").strip()
    if not text:
        logger.error("Ollama returned an empty chat response.")
        raise OllamaInferenceError("Ollama returned an empty chat response.")

    logger.info("Ollama chat succeeded: response_chars=%s", len(text))
    return text
