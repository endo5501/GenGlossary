"""Database access layer for GenGlossary."""

# Connection management
from genglossary.db.connection import database_connection, get_connection

# Schema management
from genglossary.db.schema import get_schema_version, initialize_db

# Metadata repository
from genglossary.db.metadata_repository import (
    clear_metadata,
    get_metadata,
    upsert_metadata,
)

# Document repository
from genglossary.db.document_repository import (
    create_document,
    get_document,
    get_document_by_path,
    list_all_documents,
)

# Term repository
from genglossary.db.term_repository import (
    create_term,
    delete_all_terms,
    delete_term,
    get_term,
    list_all_terms,
    update_term,
)

# Provisional glossary repository
from genglossary.db.provisional_repository import (
    create_provisional_term,
    delete_all_provisional,
    get_provisional_term,
    list_all_provisional,
    update_provisional_term,
)

# Issue repository
from genglossary.db.issue_repository import (
    create_issue,
    delete_all_issues,
    get_issue,
    list_all_issues,
)

# Refined glossary repository
from genglossary.db.refined_repository import (
    create_refined_term,
    delete_all_refined,
    get_refined_term,
    list_all_refined,
    update_refined_term,
)

# Database models
from genglossary.db.models import (
    GlossaryTermRow,
    deserialize_occurrences,
    serialize_occurrences,
)

__all__ = [
    # Connection
    "get_connection",
    "database_connection",
    # Schema
    "initialize_db",
    "get_schema_version",
    # Metadata
    "get_metadata",
    "upsert_metadata",
    "clear_metadata",
    # Documents
    "create_document",
    "get_document",
    "get_document_by_path",
    "list_all_documents",
    # Terms
    "create_term",
    "get_term",
    "list_all_terms",
    "update_term",
    "delete_term",
    "delete_all_terms",
    # Provisional glossary
    "create_provisional_term",
    "get_provisional_term",
    "list_all_provisional",
    "update_provisional_term",
    "delete_all_provisional",
    # Issues
    "create_issue",
    "get_issue",
    "list_all_issues",
    "delete_all_issues",
    # Refined glossary
    "create_refined_term",
    "get_refined_term",
    "list_all_refined",
    "update_refined_term",
    "delete_all_refined",
    # Models
    "GlossaryTermRow",
    "serialize_occurrences",
    "deserialize_occurrences",
]
