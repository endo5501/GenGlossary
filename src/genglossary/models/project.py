"""Project model for managing glossary projects."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class ProjectStatus(str, Enum):
    """Status of a glossary project.

    Attributes:
        CREATED: Project has been created but not yet run.
        RUNNING: Project is currently being processed.
        COMPLETED: Project processing has completed successfully.
        ERROR: Project processing encountered an error.
    """

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


class Project(BaseModel):
    """Represents a glossary generation project.

    A project encapsulates all the information needed to manage
    a glossary generation workflow, including the document source,
    LLM settings, and processing state.

    Attributes:
        id: Unique project identifier (auto-generated).
        name: Human-readable project name (must be unique).
        doc_root: Absolute path to the document directory.
        db_path: Absolute path to the project's database file.
        llm_provider: LLM provider name (e.g., "ollama", "openai").
        llm_model: LLM model name (e.g., "llama3.2", "gpt-4").
        created_at: Timestamp when the project was created.
        updated_at: Timestamp when the project was last updated.
        last_run_at: Timestamp when the project was last run (None if never run).
        status: Current processing status of the project.
    """

    id: int | None = None
    name: str
    doc_root: str
    db_path: str
    llm_provider: str = "ollama"
    llm_model: str = ""
    llm_base_url: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_run_at: datetime | None = None
    status: ProjectStatus = ProjectStatus.CREATED

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and normalize the project name.

        Args:
            v: The project name to validate.

        Returns:
            The validated project name.

        Raises:
            ValueError: If the name is empty or contains only whitespace.
        """
        stripped = v.strip()
        if not stripped:
            raise ValueError("Project name cannot be empty")
        return stripped

    @field_validator("db_path")
    @classmethod
    def validate_non_empty_path(cls, v: str) -> str:
        """Validate that db_path is not empty.

        Args:
            v: The path to validate.

        Returns:
            The validated path.

        Raises:
            ValueError: If the path is empty.
        """
        if not v:
            raise ValueError("Path cannot be empty")
        return v
