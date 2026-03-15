# -*- coding: utf-8 -*-
"""Research project storage — SQLite backed."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import List, Optional

from .models import (
    ResearchFinding,
    ResearchProject,
    ResearchStatus,
    ResearchSummary,
    Source,
    SourceType,
)


class ResearchStore:
    """Persistent storage for research projects."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS research_projects (
                id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                objective TEXT DEFAULT '',
                search_queries TEXT DEFAULT '[]',
                sources TEXT DEFAULT '[]',
                findings TEXT DEFAULT '[]',
                synthesis TEXT DEFAULT '',
                status TEXT DEFAULT 'planning',
                max_sources INTEGER DEFAULT 20,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_research_status ON research_projects(status);
        """,
        )
        self._conn.commit()

    def save_project(self, project: ResearchProject) -> ResearchProject:
        now = time.time()
        if not project.created_at:
            project.created_at = now
        project.updated_at = now

        self._conn.execute(
            "INSERT OR REPLACE INTO research_projects "
            "(id, topic, objective, search_queries, sources, findings, "
            "synthesis, status, max_sources, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                project.id,
                project.topic,
                project.objective,
                json.dumps(project.search_queries),
                json.dumps([s.model_dump() for s in project.sources]),
                json.dumps([f.model_dump() for f in project.findings]),
                project.synthesis,
                project.status,
                project.max_sources,
                project.created_at,
                project.updated_at,
            ),
        )
        self._conn.commit()
        return project

    def get_project(self, project_id: str) -> Optional[ResearchProject]:
        row = self._conn.execute(
            "SELECT * FROM research_projects WHERE id = ?",
            (project_id,),
        ).fetchone()
        if not row:
            return None
        return self._row_to_project(row)

    def list_projects(
        self,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[ResearchSummary]:
        query = "SELECT id, topic, status, sources, findings, created_at FROM research_projects"
        params: list = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        rows = self._conn.execute(query, params).fetchall()
        return [
            ResearchSummary(
                id=r["id"],
                topic=r["topic"],
                status=ResearchStatus(r["status"]),
                source_count=len(json.loads(r["sources"])),
                finding_count=len(json.loads(r["findings"])),
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def delete_project(self, project_id: str) -> bool:
        cursor = self._conn.execute(
            "DELETE FROM research_projects WHERE id = ?",
            (project_id,),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def update_status(self, project_id: str, status: ResearchStatus) -> bool:
        cursor = self._conn.execute(
            "UPDATE research_projects SET status = ?, updated_at = ? WHERE id = ?",
            (status, time.time(), project_id),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    @staticmethod
    def _row_to_project(row: sqlite3.Row) -> ResearchProject:
        sources_data = json.loads(row["sources"]) if row["sources"] else []
        findings_data = json.loads(row["findings"]) if row["findings"] else []
        return ResearchProject(
            id=row["id"],
            topic=row["topic"],
            objective=row["objective"],
            search_queries=(
                json.loads(row["search_queries"]) if row["search_queries"] else []
            ),
            sources=[Source(**s) for s in sources_data],
            findings=[ResearchFinding(**f) for f in findings_data],
            synthesis=row["synthesis"],
            status=ResearchStatus(row["status"]),
            max_sources=row["max_sources"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def close(self) -> None:
        self._conn.close()
