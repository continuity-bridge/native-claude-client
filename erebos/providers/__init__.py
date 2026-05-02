"""erebos provider clients and interfaces."""

from .base import (
    ProviderClient,
    ProviderStatus,
    ProviderError,
    ProviderConnectionError,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderModelNotFoundError,
    ProviderResponseError,
    ProviderCapabilityError,
)
from .ollama import OllamaClient

__all__ = [
    "ProviderClient",
    "ProviderStatus",
    "ProviderError",
    "ProviderConnectionError",
    "ProviderAuthError",
    "ProviderRateLimitError",
    "ProviderModelNotFoundError",
    "ProviderResponseError",
    "ProviderCapabilityError",
    "OllamaClient",
]
