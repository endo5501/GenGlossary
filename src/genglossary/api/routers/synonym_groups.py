"""Synonym Groups API endpoints."""

import sqlite3

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status

from genglossary.api.dependencies import get_project_db
from genglossary.api.schemas.synonym_group_schemas import (
    SynonymGroupCreateRequest,
    SynonymGroupListResponse,
    SynonymGroupResponse,
    SynonymGroupUpdateRequest,
    SynonymMemberCreateRequest,
    SynonymMemberResponse,
)
from genglossary.db.connection import transaction
from genglossary.db.synonym_repository import (
    add_member as repo_add_member,
    create_group,
    delete_group,
    list_groups,
    remove_member,
    update_primary_term,
)

router = APIRouter(
    prefix="/api/projects/{project_id}/synonym-groups",
    tags=["synonym-groups"],
)


@router.get("", response_model=SynonymGroupListResponse)
async def list_synonym_groups(
    project_id: int = Path(..., description="Project ID"),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> SynonymGroupListResponse:
    """List all synonym groups for a project."""
    groups = list_groups(project_db)
    items = SynonymGroupResponse.from_models(groups)
    return SynonymGroupListResponse(items=items, total=len(items))


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SynonymGroupResponse)
async def create_synonym_group(
    project_id: int = Path(..., description="Project ID"),
    request: SynonymGroupCreateRequest = Body(...),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> SynonymGroupResponse:
    """Create a new synonym group."""
    try:
        with transaction(project_db):
            group_id = create_group(
                project_db, request.primary_term_text, request.member_texts
            )
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="One or more member terms already belong to another group",
        )

    groups = list_groups(project_db)
    group = next(g for g in groups if g.id == group_id)
    return SynonymGroupResponse.from_model(group)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_synonym_group(
    project_id: int = Path(..., description="Project ID"),
    group_id: int = Path(..., description="Synonym group ID"),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> None:
    """Delete a synonym group."""
    with transaction(project_db):
        deleted = delete_group(project_db, group_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Synonym group {group_id} not found",
        )


@router.patch("/{group_id}", response_model=SynonymGroupResponse)
async def update_synonym_group(
    project_id: int = Path(..., description="Project ID"),
    group_id: int = Path(..., description="Synonym group ID"),
    request: SynonymGroupUpdateRequest = Body(...),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> SynonymGroupResponse:
    """Update the primary term of a synonym group."""
    with transaction(project_db):
        updated = update_primary_term(
            project_db, group_id, request.primary_term_text
        )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Synonym group {group_id} not found",
        )

    groups = list_groups(project_db)
    group = next(g for g in groups if g.id == group_id)
    return SynonymGroupResponse.from_model(group)


@router.post(
    "/{group_id}/members",
    status_code=status.HTTP_201_CREATED,
    response_model=SynonymMemberResponse,
)
async def add_member_to_group(
    project_id: int = Path(..., description="Project ID"),
    group_id: int = Path(..., description="Synonym group ID"),
    request: SynonymMemberCreateRequest = Body(...),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> SynonymMemberResponse:
    """Add a member to a synonym group."""
    try:
        with transaction(project_db):
            member_id = repo_add_member(project_db, group_id, request.term_text)
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Term '{request.term_text}' already belongs to a group",
        )

    return SynonymMemberResponse(
        id=member_id, group_id=group_id, term_text=request.term_text
    )


@router.delete(
    "/{group_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_member_from_group(
    project_id: int = Path(..., description="Project ID"),
    group_id: int = Path(..., description="Synonym group ID"),
    member_id: int = Path(..., description="Member ID"),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> None:
    """Remove a member from a synonym group."""
    with transaction(project_db):
        removed = remove_member(project_db, member_id)

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Member {member_id} not found",
        )
