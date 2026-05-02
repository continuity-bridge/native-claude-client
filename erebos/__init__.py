"""erebos - Network-agnostic LLM harness."""

from .providers import (
    ProviderClient,
    ProviderStatus,
    ProviderError,
    ProviderConnectionError,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderModelNotFoundError,
    ProviderResponseError,
    ProviderCapabilityError,
    OllamaClient,
)
from .discovery import OllamaDiscovery

__version__ = "0.1.0-dev"

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
    "OllamaDiscovery",
]
