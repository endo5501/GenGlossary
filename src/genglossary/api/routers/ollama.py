"""Ollama API endpoints."""

import ipaddress
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Query

from genglossary.api.schemas.ollama_schemas import OllamaModelInfo, OllamaModelsResponse
from genglossary.llm.ollama_client import OllamaClient

router = APIRouter(prefix="/ollama", tags=["ollama"])

DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"

# Allowed hostnames for Ollama server (SSRF protection)
ALLOWED_HOSTNAMES = {"localhost", "127.0.0.1", "::1"}


def _validate_ollama_url(url: str) -> str:
    """Validate and normalize Ollama server URL.

    Args:
        url: URL to validate.

    Returns:
        Normalized URL string.

    Raises:
        HTTPException: If URL is invalid or not allowed.
    """
    url = url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Base URL cannot be empty")

    try:
        parsed = urlparse(url)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid URL format")

    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="URL must use http or https scheme")

    if not parsed.netloc:
        raise HTTPException(status_code=400, detail="URL must include a host")

    # Extract hostname (without port)
    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(status_code=400, detail="URL must include a valid hostname")

    # SSRF protection: only allow localhost or explicitly configured hosts
    if hostname not in ALLOWED_HOSTNAMES:
        # Check if it's a private IP address
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                # Allow loopback addresses
                if not ip.is_loopback:
                    raise HTTPException(
                        status_code=400,
                        detail="Only localhost URLs are allowed for security reasons",
                    )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Only localhost URLs are allowed for security reasons",
                )
        except ValueError:
            # Not an IP address, check if it's an allowed hostname
            raise HTTPException(
                status_code=400,
                detail="Only localhost URLs are allowed for security reasons",
            )

    return url


@router.get("/models", response_model=OllamaModelsResponse)
async def list_models(
    base_url: str = Query(
        default=DEFAULT_OLLAMA_BASE_URL,
        description="Ollama server base URL",
    ),
) -> OllamaModelsResponse:
    """List available models from Ollama server.

    Args:
        base_url: Base URL of the Ollama server.

    Returns:
        OllamaModelsResponse: List of available models.

    Raises:
        HTTPException: If connection fails or URL is invalid.
    """
    validated_url = _validate_ollama_url(base_url)

    client = OllamaClient(base_url=validated_url, timeout=5.0)
    try:
        model_names = client.list_models()
        models = [OllamaModelInfo(name=name) for name in model_names]
        return OllamaModelsResponse(models=models)
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Failed to connect to Ollama server")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Ollama server timeout")
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="Ollama server error")
