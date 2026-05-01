"""
Ollama LLM client with event system integration.
"""

import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Simple Ollama API client that emits events on success/failure.

    This demonstrates how the event system integrates with LLM calls.
    """

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.event_emitter = None

    def chat(self, model: str, prompt: str, stream: bool = False) -> str:
        """
        Send chat request to Ollama.

        Args:
            model: Model name (e.g., "llama3.2", "mistral")
            prompt: User prompt
            stream: Whether to stream response (not implemented yet)

        Returns:
            Model response text

        Raises:
            Exception: On API errors or connection failures
        """
        tool_name = f"ollama:{model}"
        tool_family = "ollama"

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": stream,
                },
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()["message"]["content"]

                # Emit success event
                if self.event_emitter:
                    self.event_emitter.tool_succeeded(tool_name, tool_family)

                logger.info(f"Ollama {model} response: {len(result)} chars")
                return result
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"

                # Emit failure event
                if self.event_emitter:
                    self.event_emitter.tool_failed(
                        tool_name=tool_name,
                        tool_family=tool_family,
                        error_type="api_error",
                        error_message=error_msg,
                    )

                raise Exception(f"Ollama API error: {error_msg}")

        except requests.exceptions.ConnectionError as e:
            error_msg = f"Cannot connect to Ollama at {self.base_url}"

            # Emit failure event
            if self.event_emitter:
                self.event_emitter.tool_failed(
                    tool_name=tool_name,
                    tool_family=tool_family,
                    error_type="connection_error",
                    error_message=error_msg,
                )

            logger.error(error_msg)
            raise Exception(error_msg) from e

        except requests.exceptions.Timeout as e:
            error_msg = "Request timed out"

            # Emit failure event
            if self.event_emitter:
                self.event_emitter.tool_failed(
                    tool_name=tool_name,
                    tool_family=tool_family,
                    error_type="timeout",
                    error_message=error_msg,
                )

            raise Exception(error_msg) from e

    def list_models(self) -> list:
        """Get list of available models from Ollama."""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                return [m["name"] for m in response.json().get("models", [])]
            return []
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
