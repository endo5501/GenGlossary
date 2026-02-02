"""Ollama API endpoints."""

import httpx
from fastapi import APIRouter, HTTPException, Query

from genglossary.api.schemas.ollama_schemas import OllamaModelInfo, OllamaModelsResponse
from genglossary.llm.ollama_client import OllamaClient

router = APIRouter(prefix="/ollama", tags=["ollama"])

DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"


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
    if not base_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid base URL format")

    client = OllamaClient(base_url=base_url, timeout=5.0)
    try:
        model_names = client.list_models()
        models = [OllamaModelInfo(name=name) for name in model_names]
        return OllamaModelsResponse(models=models)
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Failed to connect to Ollama server")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Ollama server timeout")
