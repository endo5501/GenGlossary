"""Runs API endpoints."""

import json
import sqlite3
from typing import AsyncIterator

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from fastapi.responses import StreamingResponse

from genglossary.api.dependencies import get_project_db
from genglossary.api.schemas.run_schemas import RunResponse, RunStartRequest
from genglossary.db.runs_repository import get_run, list_runs
from genglossary.runs.manager import RunManager

router = APIRouter(prefix="/api/projects/{project_id}/runs", tags=["runs"])


def get_run_manager(project_db: sqlite3.Connection = Depends(get_project_db)) -> RunManager:
    """Get RunManager instance for the project.

    Args:
        project_db: Project database connection.

    Returns:
        RunManager: RunManager instance.
    """
    return RunManager(project_db)


@router.post("", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
async def start_run(
    project_id: int = Path(..., description="Project ID"),
    request: RunStartRequest = Body(...),
    project_db: sqlite3.Connection = Depends(get_project_db),
    manager: RunManager = Depends(get_run_manager),
) -> RunResponse:
    """Start a new run for the project.

    Args:
        project_id: Project ID (path parameter).
        request: Run start request.
        project_db: Project database connection.
        manager: RunManager instance.

    Returns:
        RunResponse: The created run.

    Raises:
        HTTPException: 409 if a run is already running.
    """
    try:
        run_id = manager.start_run(scope=request.scope)
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))

    row = get_run(project_db, run_id)
    assert row is not None

    return RunResponse.from_db_row(row)


@router.delete("/{run_id}", status_code=status.HTTP_200_OK)
async def cancel_run(
    project_id: int = Path(..., description="Project ID"),
    run_id: int = Path(..., description="Run ID"),
    project_db: sqlite3.Connection = Depends(get_project_db),
    manager: RunManager = Depends(get_run_manager),
) -> dict:
    """Cancel a running run.

    Args:
        project_id: Project ID (path parameter).
        run_id: Run ID to cancel.
        project_db: Project database connection.
        manager: RunManager instance.

    Returns:
        dict: Success message.

    Raises:
        HTTPException: 404 if run not found.
    """
    # Check if run exists
    row = get_run(project_db, run_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    manager.cancel_run(run_id)

    return {"message": "Run cancelled successfully"}


@router.get("", response_model=list[RunResponse])
async def list_project_runs(
    project_id: int = Path(..., description="Project ID"),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> list[RunResponse]:
    """List all runs for a project.

    Args:
        project_id: Project ID (path parameter).
        project_db: Project database connection.

    Returns:
        list[RunResponse]: List of all runs, most recent first.
    """
    rows = list_runs(project_db)
    return RunResponse.from_db_rows(rows)


@router.get("/current", response_model=RunResponse)
async def get_current_run(
    project_id: int = Path(..., description="Project ID"),
    manager: RunManager = Depends(get_run_manager),
) -> RunResponse:
    """Get the currently active run for a project.

    Args:
        project_id: Project ID (path parameter).
        manager: RunManager instance.

    Returns:
        RunResponse: The active run.

    Raises:
        HTTPException: 404 if no active run.
    """
    row = manager.get_active_run()
    if row is None:
        raise HTTPException(status_code=404, detail="No active run")

    return RunResponse.from_db_row(row)


@router.get("/{run_id}", response_model=RunResponse)
async def get_run_by_id(
    project_id: int = Path(..., description="Project ID"),
    run_id: int = Path(..., description="Run ID"),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> RunResponse:
    """Get a specific run by ID.

    Args:
        project_id: Project ID (path parameter).
        run_id: Run ID to retrieve.
        project_db: Project database connection.

    Returns:
        RunResponse: The requested run.

    Raises:
        HTTPException: 404 if run not found.
    """
    row = get_run(project_db, run_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    return RunResponse.from_db_row(row)


@router.get("/{run_id}/logs")
async def stream_run_logs(
    project_id: int = Path(..., description="Project ID"),
    run_id: int = Path(..., description="Run ID"),
    project_db: sqlite3.Connection = Depends(get_project_db),
    manager: RunManager = Depends(get_run_manager),
) -> StreamingResponse:
    """Stream run logs using Server-Sent Events (SSE).

    Args:
        project_id: Project ID (path parameter).
        run_id: Run ID.
        project_db: Project database connection.
        manager: RunManager instance.

    Returns:
        StreamingResponse: SSE stream of log messages.

    Raises:
        HTTPException: 404 if run not found.
    """
    # Check if run exists
    row = get_run(project_db, run_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    async def event_generator() -> AsyncIterator[str]:
        """Generate SSE events from log queue."""
        log_queue = manager.get_log_queue()

        while True:
            # Get log message from queue (with timeout)
            try:
                log_msg = log_queue.get(timeout=1)
                if log_msg is None:
                    # Sentinel value - end of stream
                    yield "event: complete\ndata: {}\n\n"
                    break

                # Send log message as SSE event
                yield f"data: {json.dumps(log_msg)}\n\n"
            except:
                # Timeout - send keepalive
                yield ": keepalive\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
