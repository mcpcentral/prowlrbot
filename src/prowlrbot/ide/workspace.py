# -*- coding: utf-8 -*-
"""IDE workspace manager — file operations and session management."""

from __future__ import annotations

import difflib
import json
import os
import sqlite3
import time
from pathlib import Path
from typing import List, Optional

from .models import (
    DiffHunk,
    EditOperation,
    FILE_EXTENSION_MAP,
    FileContent,
    FileDiff,
    FileEntry,
    FileType,
    IDESession,
)


class IDEWorkspace:
    """Manages file operations and IDE sessions."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS ide_sessions (
                id TEXT PRIMARY KEY,
                workspace_root TEXT NOT NULL,
                open_files TEXT DEFAULT '[]',
                active_file TEXT DEFAULT '',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS edit_history (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                path TEXT NOT NULL,
                operation TEXT NOT NULL,
                line_start INTEGER DEFAULT 0,
                line_end INTEGER DEFAULT 0,
                content TEXT DEFAULT '',
                agent_id TEXT DEFAULT '',
                created_at REAL NOT NULL,
                FOREIGN KEY (session_id) REFERENCES ide_sessions(id)
            );
            CREATE INDEX IF NOT EXISTS idx_edits_session ON edit_history(session_id);
            CREATE INDEX IF NOT EXISTS idx_edits_path ON edit_history(path);
        """,
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------

    def list_files(
        self,
        root: str,
        max_depth: int = 3,
        include_hidden: bool = False,
    ) -> FileEntry:
        """List files in a directory tree."""
        root_path = Path(root)
        if not root_path.exists():
            return FileEntry(path=root, name=root_path.name, is_directory=True)

        return self._scan_dir(
            root_path,
            depth=0,
            max_depth=max_depth,
            include_hidden=include_hidden,
        )

    def read_file(self, path: str) -> FileContent:
        """Read a file's content."""
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if not file_path.is_file():
            raise ValueError(f"Not a file: {path}")

        ext = file_path.suffix.lower()
        file_type = FILE_EXTENSION_MAP.get(ext, FileType.OTHER)

        content = file_path.read_text(encoding="utf-8", errors="replace")
        return FileContent(
            path=str(file_path),
            content=content,
            file_type=file_type,
            line_count=content.count("\n") + 1,
        )

    def write_file(self, path: str, content: str) -> FileContent:
        """Write content to a file."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

        ext = file_path.suffix.lower()
        file_type = FILE_EXTENSION_MAP.get(ext, FileType.OTHER)
        return FileContent(
            path=str(file_path),
            content=content,
            file_type=file_type,
            line_count=content.count("\n") + 1,
        )

    def diff_files(self, path: str, original: str, modified: str) -> FileDiff:
        """Compute diff between original and modified content."""
        orig_lines = original.splitlines(keepends=True)
        mod_lines = modified.splitlines(keepends=True)

        hunks: List[DiffHunk] = []
        matcher = difflib.SequenceMatcher(None, orig_lines, mod_lines)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != "equal":
                hunks.append(
                    DiffHunk(
                        start_line=i1 + 1,
                        end_line=i2,
                        original_lines=list(orig_lines[i1:i2]),
                        modified_lines=list(mod_lines[j1:j2]),
                    ),
                )

        return FileDiff(
            path=path,
            original=original,
            modified=modified,
            hunks=hunks,
            created_at=time.time(),
        )

    def apply_edit(self, path: str, edit: EditOperation) -> FileContent:
        """Apply an edit operation to a file."""
        file_content = self.read_file(path)
        lines = file_content.content.splitlines(keepends=True)

        if edit.operation == "insert":
            pos = max(0, min(edit.line_start, len(lines)))
            new_lines = edit.content.splitlines(keepends=True)
            lines[pos:pos] = new_lines
        elif edit.operation == "replace":
            start = max(0, edit.line_start - 1)
            end = min(len(lines), edit.line_end)
            new_lines = edit.content.splitlines(keepends=True)
            lines[start:end] = new_lines
        elif edit.operation == "delete":
            start = max(0, edit.line_start - 1)
            end = min(len(lines), edit.line_end)
            del lines[start:end]

        new_content = "".join(lines)
        return self.write_file(path, new_content)

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    def create_session(self, workspace_root: str) -> IDESession:
        """Create a new IDE session."""
        now = time.time()
        session = IDESession(
            workspace_root=workspace_root,
            created_at=now,
            updated_at=now,
        )
        self._conn.execute(
            "INSERT INTO ide_sessions (id, workspace_root, open_files, active_file, "
            "created_at, updated_at) VALUES (?,?,?,?,?,?)",
            (
                session.id,
                session.workspace_root,
                json.dumps(session.open_files),
                session.active_file,
                session.created_at,
                session.updated_at,
            ),
        )
        self._conn.commit()
        return session

    def get_session(self, session_id: str) -> Optional[IDESession]:
        row = self._conn.execute(
            "SELECT * FROM ide_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        if not row:
            return None
        return IDESession(
            id=row["id"],
            workspace_root=row["workspace_root"],
            open_files=json.loads(row["open_files"]),
            active_file=row["active_file"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def update_session(
        self,
        session_id: str,
        open_files: Optional[List[str]] = None,
        active_file: Optional[str] = None,
    ) -> Optional[IDESession]:
        session = self.get_session(session_id)
        if not session:
            return None
        if open_files is not None:
            session.open_files = open_files
        if active_file is not None:
            session.active_file = active_file
        session.updated_at = time.time()
        self._conn.execute(
            "UPDATE ide_sessions SET open_files = ?, active_file = ?, updated_at = ? "
            "WHERE id = ?",
            (
                json.dumps(session.open_files),
                session.active_file,
                session.updated_at,
                session_id,
            ),
        )
        self._conn.commit()
        return session

    def record_edit(
        self,
        session_id: str,
        edit: EditOperation,
    ) -> EditOperation:
        """Record an edit in the history."""
        edit.created_at = time.time()
        self._conn.execute(
            "INSERT INTO edit_history (id, session_id, path, operation, "
            "line_start, line_end, content, agent_id, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (
                edit.id,
                session_id,
                edit.path,
                edit.operation,
                edit.line_start,
                edit.line_end,
                edit.content,
                edit.agent_id,
                edit.created_at,
            ),
        )
        self._conn.commit()
        return edit

    def get_edit_history(
        self,
        session_id: Optional[str] = None,
        path: Optional[str] = None,
        limit: int = 100,
    ) -> List[EditOperation]:
        query = "SELECT * FROM edit_history WHERE 1=1"
        params: list = []
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        if path:
            query += " AND path = ?"
            params.append(path)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = self._conn.execute(query, params).fetchall()
        return [
            EditOperation(
                id=r["id"],
                path=r["path"],
                operation=r["operation"],
                line_start=r["line_start"],
                line_end=r["line_end"],
                content=r["content"],
                agent_id=r["agent_id"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _scan_dir(
        self,
        path: Path,
        depth: int,
        max_depth: int,
        include_hidden: bool,
    ) -> FileEntry:
        entry = FileEntry(
            path=str(path),
            name=path.name,
            is_directory=path.is_dir(),
            modified_at=path.stat().st_mtime if path.exists() else 0,
        )

        if not path.is_dir() or depth >= max_depth:
            if path.is_file():
                ext = path.suffix.lower()
                entry.file_type = FILE_EXTENSION_MAP.get(ext, FileType.OTHER)
                entry.size = path.stat().st_size
            return entry

        try:
            for child in sorted(path.iterdir()):
                if not include_hidden and child.name.startswith("."):
                    continue
                if child.name in ("__pycache__", "node_modules", ".git"):
                    continue
                entry.children.append(
                    self._scan_dir(
                        child,
                        depth + 1,
                        max_depth,
                        include_hidden,
                    ),
                )
        except PermissionError:
            pass

        return entry

    def close(self) -> None:
        self._conn.close()
