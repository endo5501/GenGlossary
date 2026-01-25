"""Refined API endpoints."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import PlainTextResponse

from genglossary.api.dependencies import get_project_db
from genglossary.api.schemas.refined_schemas import RefinedResponse
from genglossary.db.refined_repository import get_refined_term, list_all_refined

router = APIRouter(prefix="/api/projects/{project_id}/refined", tags=["refined"])


@router.get("", response_model=list[RefinedResponse])
async def list_refined(
    project_id: int = Path(..., description="Project ID"),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> list[RefinedResponse]:
    """List all refined glossary terms for a project.

    Args:
        project_id: Project ID (path parameter).
        project_db: Project database connection.

    Returns:
        list[RefinedResponse]: List of all refined terms.
    """
    rows = list_all_refined(project_db)
    return [
        RefinedResponse(
            id=row["id"],
            term_name=row["term_name"],
            definition=row["definition"],
            confidence=row["confidence"],
            occurrences=row["occurrences"],
        )
        for row in rows
    ]


@router.get("/export-md", response_class=PlainTextResponse)
async def export_markdown(
    project_id: int = Path(..., description="Project ID"),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> PlainTextResponse:
    """Export refined glossary as Markdown.

    Args:
        project_id: Project ID (path parameter).
        project_db: Project database connection.

    Returns:
        PlainTextResponse: Markdown formatted glossary.
    """
    rows = list_all_refined(project_db)

    # Generate Markdown
    lines = ["# 用語集\n"]

    for row in rows:
        lines.append(f"## {row['term_name']}\n")
        lines.append(f"**定義**: {row['definition']}\n")
        lines.append(f"**信頼度**: {row['confidence']:.2f}\n")

        if row["occurrences"]:
            lines.append("\n**出現箇所**:\n")
            for occ in row["occurrences"]:
                lines.append(f"- {occ.document_path}:{occ.line_number}\n")

        lines.append("\n---\n\n")

    markdown_content = "".join(lines)

    return PlainTextResponse(
        content=markdown_content,
        media_type="text/markdown; charset=utf-8",
    )


@router.get("/{term_id}", response_model=RefinedResponse)
async def get_refined_by_id(
    project_id: int = Path(..., description="Project ID"),
    term_id: int = Path(..., description="Term ID"),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> RefinedResponse:
    """Get a specific refined term by ID.

    Args:
        project_id: Project ID (path parameter).
        term_id: Term ID to retrieve.
        project_db: Project database connection.

    Returns:
        RefinedResponse: The requested term.

    Raises:
        HTTPException: 404 if term not found.
    """
    row = get_refined_term(project_db, term_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Term {term_id} not found")

    return RefinedResponse(
        id=row["id"],
        term_name=row["term_name"],
        definition=row["definition"],
        confidence=row["confidence"],
        occurrences=row["occurrences"],
    )
