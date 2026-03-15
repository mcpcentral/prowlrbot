# -*- coding: utf-8 -*-
"""API endpoints for the embedded IDE workspace."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...constant import WORKING_DIR
from ...ide.models import (
    EditOperation,
    FileContent,
    FileDiff,
    FileEntry,
    IDESession,
)
from ...ide.workspace import IDEWorkspace

router = APIRouter(prefix="/ide", tags=["ide"])

_workspace = IDEWorkspace(db_path=WORKING_DIR / "ide.db")


# --- File operations ---


@router.get("/files")
async def list_files(
    root: str = "",
    max_depth: int = 3,
    include_hidden: bool = False,
) -> FileEntry:
    path = root or str(WORKING_DIR)
    return _workspace.list_files(
        path,
        max_depth=max_depth,
        include_hidden=include_hidden,
    )


@router.get("/files/content")
async def read_file(path: str) -> FileContent:
    try:
        return _workspace.read_file(path)
    except FileNotFoundError:
        raise HTTPException(404, f"File not found: {path}")
    except ValueError as e:
        raise HTTPException(400, str(e))


class WriteFileRequest(BaseModel):
    path: str
    content: str


@router.post("/files/write")
async def write_file(req: WriteFileRequest) -> FileContent:
    return _workspace.write_file(req.path, req.content)


class DiffRequest(BaseModel):
    path: str
    original: str
    modified: str


@router.post("/files/diff")
async def diff_files(req: DiffRequest) -> FileDiff:
    return _workspace.diff_files(req.path, req.original, req.modified)


@router.post("/files/edit")
async def apply_edit(edit: EditOperation) -> FileContent:
    try:
        return _workspace.apply_edit(edit.path, edit)
    except FileNotFoundError:
        raise HTTPException(404, f"File not found: {edit.path}")


# --- Sessions ---


class CreateSessionRequest(BaseModel):
    workspace_root: str = ""


@router.post("/sessions", response_model=IDESession)
async def create_session(req: CreateSessionRequest) -> IDESession:
    root = req.workspace_root or str(WORKING_DIR)
    return _workspace.create_session(root)


@router.get("/sessions/{session_id}", response_model=IDESession)
async def get_session(session_id: str) -> IDESession:
    session = _workspace.get_session(session_id)
    if not session:
        raise HTTPException(404, f"Session '{session_id}' not found")
    return session


class UpdateSessionRequest(BaseModel):
    open_files: Optional[List[str]] = None
    active_file: Optional[str] = None


@router.put("/sessions/{session_id}", response_model=IDESession)
async def update_session(
    session_id: str,
    req: UpdateSessionRequest,
) -> IDESession:
    session = _workspace.update_session(
        session_id,
        open_files=req.open_files,
        active_file=req.active_file,
    )
    if not session:
        raise HTTPException(404, f"Session '{session_id}' not found")
    return session


# --- Edit history ---


@router.post("/sessions/{session_id}/edits")
async def record_edit(session_id: str, edit: EditOperation) -> EditOperation:
    session = _workspace.get_session(session_id)
    if not session:
        raise HTTPException(404, f"Session '{session_id}' not found")
    return _workspace.record_edit(session_id, edit)


@router.get("/sessions/{session_id}/history")
async def get_edit_history(
    session_id: str,
    path: Optional[str] = None,
    limit: int = 100,
) -> List[EditOperation]:
    return _workspace.get_edit_history(
        session_id=session_id,
        path=path,
        limit=limit,
    )
