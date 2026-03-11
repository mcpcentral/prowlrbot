# -*- coding: utf-8 -*-
"""IDE data models — file operations, sessions, diffs."""

from __future__ import annotations

import uuid
from prowlrbot.compat import StrEnum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FileType(StrEnum):
    TEXT = "text"
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JSON = "json"
    YAML = "yaml"
    MARKDOWN = "markdown"
    HTML = "html"
    CSS = "css"
    SHELL = "shell"
    OTHER = "other"


FILE_EXTENSION_MAP: Dict[str, FileType] = {
    ".py": FileType.PYTHON,
    ".js": FileType.JAVASCRIPT,
    ".ts": FileType.TYPESCRIPT,
    ".tsx": FileType.TYPESCRIPT,
    ".jsx": FileType.JAVASCRIPT,
    ".json": FileType.JSON,
    ".yaml": FileType.YAML,
    ".yml": FileType.YAML,
    ".md": FileType.MARKDOWN,
    ".html": FileType.HTML,
    ".css": FileType.CSS,
    ".sh": FileType.SHELL,
    ".bash": FileType.SHELL,
    ".zsh": FileType.SHELL,
    ".txt": FileType.TEXT,
}


class FileEntry(BaseModel):
    """A file in the IDE workspace."""

    path: str
    name: str = ""
    file_type: FileType = FileType.TEXT
    size: int = 0
    is_directory: bool = False
    children: List["FileEntry"] = Field(default_factory=list)
    modified_at: float = 0.0


class FileContent(BaseModel):
    """File content with metadata."""

    path: str
    content: str = ""
    file_type: FileType = FileType.TEXT
    line_count: int = 0
    encoding: str = "utf-8"


class DiffHunk(BaseModel):
    """A single hunk in a diff."""

    start_line: int
    end_line: int
    original_lines: List[str] = Field(default_factory=list)
    modified_lines: List[str] = Field(default_factory=list)


class FileDiff(BaseModel):
    """A diff between two versions of a file."""

    path: str
    original: str = ""
    modified: str = ""
    hunks: List[DiffHunk] = Field(default_factory=list)
    created_at: float = 0.0


class EditOperation(BaseModel):
    """An edit operation on a file."""

    id: str = Field(default_factory=lambda: f"edit_{uuid.uuid4().hex[:8]}")
    path: str
    operation: str  # "insert", "replace", "delete"
    line_start: int = 0
    line_end: int = 0
    content: str = ""
    agent_id: str = ""
    created_at: float = 0.0


class IDESession(BaseModel):
    """An IDE editing session."""

    id: str = Field(default_factory=lambda: f"ide_{uuid.uuid4().hex[:8]}")
    workspace_root: str
    open_files: List[str] = Field(default_factory=list)
    active_file: str = ""
    edits: List[EditOperation] = Field(default_factory=list)
    created_at: float = 0.0
    updated_at: float = 0.0


# Fix forward reference
FileEntry.model_rebuild()
