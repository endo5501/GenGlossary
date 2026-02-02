"""Ollama API schemas."""

from pydantic import BaseModel, Field


class OllamaModelInfo(BaseModel):
    """Information about an Ollama model."""

    name: str = Field(..., description="Model name")


class OllamaModelsResponse(BaseModel):
    """Response for Ollama models list."""

    models: list[OllamaModelInfo] = Field(..., description="List of available models")
