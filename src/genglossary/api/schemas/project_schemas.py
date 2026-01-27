"""Schemas for Projects API."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from genglossary.models.project import Project, ProjectStatus


def _validate_project_name(v: str) -> str:
    """Validate project name is not empty.

    Args:
        v: The project name to validate.

    Returns:
        The validated project name.

    Raises:
        ValueError: If the name is empty.
    """
    stripped = v.strip()
    if not stripped:
        raise ValueError("Project name cannot be empty")
    return stripped


def _validate_llm_base_url(v: str | None) -> str | None:
    """Validate LLM base URL format.

    Args:
        v: The base URL to validate.

    Returns:
        The validated URL or None.

    Raises:
        ValueError: If the URL format is invalid.
    """
    if v is None or v == "":
        return v
    stripped = v.strip()
    if not stripped:
        return ""
    # Validate URL scheme
    if not stripped.startswith(("http://", "https://")):
        raise ValueError("Base URL must start with http:// or https://")
    return stripped


class ProjectResponse(BaseModel):
    """Response schema for a project."""

    id: int = Field(..., description="Project ID")
    name: str = Field(..., description="Project name")
    doc_root: str = Field(..., description="Document root path")
    llm_provider: str = Field(..., description="LLM provider name")
    llm_model: str = Field(..., description="LLM model name")
    llm_base_url: str = Field(..., description="LLM base URL")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_run_at: datetime | None = Field(None, description="Last run timestamp")
    status: ProjectStatus = Field(..., description="Project status")

    @classmethod
    def from_project(cls, project: Project) -> "ProjectResponse":
        """Create from Project model.

        Args:
            project: Project model instance.

        Returns:
            ProjectResponse: Response instance.
        """
        return cls(
            id=project.id,  # type: ignore[arg-type]
            name=project.name,
            doc_root=project.doc_root,
            llm_provider=project.llm_provider,
            llm_model=project.llm_model,
            llm_base_url=project.llm_base_url,
            created_at=project.created_at,
            updated_at=project.updated_at,
            last_run_at=project.last_run_at,
            status=project.status,
        )


class ProjectCreateRequest(BaseModel):
    """Request schema for creating a project."""

    name: str = Field(..., description="Project name (must be unique)")
    doc_root: str = Field(..., description="Absolute path to document directory")
    llm_provider: str = Field(default="ollama", description="LLM provider name")
    llm_model: str = Field(default="", description="LLM model name")
    llm_base_url: str = Field(default="", description="LLM base URL")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate project name is not empty."""
        return _validate_project_name(v)

    @field_validator("llm_base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Validate LLM base URL format."""
        result = _validate_llm_base_url(v)
        return result if result is not None else ""


class ProjectCloneRequest(BaseModel):
    """Request schema for cloning a project."""

    new_name: str = Field(..., description="Name for the cloned project")

    @field_validator("new_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate project name is not empty."""
        return _validate_project_name(v)


class ProjectUpdateRequest(BaseModel):
    """Request schema for updating a project."""

    name: str | None = Field(None, description="New project name")
    llm_provider: str | None = Field(None, description="New LLM provider name")
    llm_model: str | None = Field(None, description="New LLM model name")
    llm_base_url: str | None = Field(None, description="New LLM base URL")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate project name if provided."""
        if v is None:
            return None
        return _validate_project_name(v)

    @field_validator("llm_base_url")
    @classmethod
    def validate_base_url(cls, v: str | None) -> str | None:
        """Validate LLM base URL format if provided."""
        return _validate_llm_base_url(v)
