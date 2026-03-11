# -*- coding: utf-8 -*-
"""Agent template store with built-in and custom templates."""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from prowlrbot.compat import StrEnum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TemplateCategory(StrEnum):
    PRODUCTIVITY = "productivity"
    CREATIVE = "creative"
    DEVELOPER = "developer"
    BUSINESS = "business"
    EDUCATION = "education"
    PERSONAL = "personal"
    CUSTOM = "custom"


class AgentTemplate(BaseModel):
    """A pre-configured agent template."""

    id: str = Field(default_factory=lambda: f"tmpl_{uuid.uuid4().hex[:8]}")
    name: str
    description: str = ""
    category: TemplateCategory = TemplateCategory.CUSTOM
    soul: str = ""  # SOUL.md content
    profile: str = ""  # PROFILE.md content
    skills: List[str] = Field(default_factory=list)  # skill names to install
    tools: List[str] = Field(default_factory=list)  # tools to enable
    avatar_base: str = "cat"
    avatar_color: str = "#00E5FF"
    autonomy_level: str = "watch"
    config_overrides: Dict[str, Any] = Field(default_factory=dict)
    is_builtin: bool = False
    author: str = ""
    downloads: int = 0
    rating: float = 0.0
    created_at: float = 0.0


# Built-in templates
BUILTIN_TEMPLATES: List[AgentTemplate] = [
    AgentTemplate(
        id="tmpl_assistant",
        name="General Assistant",
        description="A helpful general-purpose AI assistant for everyday tasks.",
        category=TemplateCategory.PRODUCTIVITY,
        soul="You are a helpful, friendly AI assistant. You provide clear, accurate answers and help users accomplish their goals efficiently.",
        skills=["file_reader", "news"],
        tools=["shell", "file_io"],
        avatar_base="cat",
        avatar_color="#00E5FF",
        is_builtin=True,
    ),
    AgentTemplate(
        id="tmpl_developer",
        name="Dev Partner",
        description="A coding-focused agent with development tools and code review skills.",
        category=TemplateCategory.DEVELOPER,
        soul="You are an expert software developer. You write clean, well-tested code and provide thoughtful code reviews. You follow best practices and explain your reasoning.",
        skills=["file_reader", "browser_visible"],
        tools=["shell", "file_io", "file_search"],
        avatar_base="robot",
        avatar_color="#4CAF50",
        autonomy_level="guide",
        is_builtin=True,
    ),
    AgentTemplate(
        id="tmpl_writer",
        name="Creative Writer",
        description="A creative writing assistant for content creation and editing.",
        category=TemplateCategory.CREATIVE,
        soul="You are a talented creative writer. You craft engaging, well-structured content. You adapt your writing style to match the audience and purpose.",
        skills=["file_reader"],
        tools=["file_io"],
        avatar_base="owl",
        avatar_color="#9C27B0",
        is_builtin=True,
    ),
    AgentTemplate(
        id="tmpl_researcher",
        name="Research Analyst",
        description="An analytical agent for deep research and report generation.",
        category=TemplateCategory.BUSINESS,
        soul="You are a meticulous research analyst. You gather information from multiple sources, cross-reference facts, and produce well-cited research reports.",
        skills=["news", "browser_visible", "file_reader"],
        tools=["shell", "file_io", "browser_control"],
        avatar_base="fox",
        avatar_color="#FF9800",
        autonomy_level="delegate",
        is_builtin=True,
    ),
    AgentTemplate(
        id="tmpl_tutor",
        name="Personal Tutor",
        description="A patient, adaptive tutor for learning any subject.",
        category=TemplateCategory.EDUCATION,
        soul="You are a patient and encouraging tutor. You adapt explanations to the student's level, use examples and analogies, and check understanding regularly.",
        skills=["file_reader"],
        tools=["file_io"],
        avatar_base="owl",
        avatar_color="#2196F3",
        is_builtin=True,
    ),
    AgentTemplate(
        id="tmpl_devops",
        name="DevOps Engineer",
        description="Infrastructure and deployment specialist with monitoring capabilities.",
        category=TemplateCategory.DEVELOPER,
        soul="You are an experienced DevOps engineer. You manage infrastructure, CI/CD pipelines, and monitoring. You prioritize reliability and security.",
        skills=["file_reader", "browser_visible"],
        tools=["shell", "file_io", "file_search"],
        avatar_base="robot",
        avatar_color="#F44336",
        autonomy_level="delegate",
        is_builtin=True,
    ),
]


class TemplateStore:
    """Manages agent templates — both built-in and custom."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._create_tables()
        self._seed_builtins()

    def _create_tables(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS templates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                category TEXT DEFAULT 'custom',
                soul TEXT DEFAULT '',
                profile TEXT DEFAULT '',
                skills TEXT DEFAULT '[]',
                tools TEXT DEFAULT '[]',
                avatar_base TEXT DEFAULT 'cat',
                avatar_color TEXT DEFAULT '#00E5FF',
                autonomy_level TEXT DEFAULT 'watch',
                config_overrides TEXT DEFAULT '{}',
                is_builtin INTEGER DEFAULT 0,
                author TEXT DEFAULT '',
                downloads INTEGER DEFAULT 0,
                rating REAL DEFAULT 0,
                created_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_tmpl_category ON templates(category);
        """)
        self._conn.commit()

    def _seed_builtins(self) -> None:
        for tmpl in BUILTIN_TEMPLATES:
            existing = self._conn.execute(
                "SELECT id FROM templates WHERE id = ?", (tmpl.id,)
            ).fetchone()
            if not existing:
                tmpl.created_at = time.time()
                self._save(tmpl)

    def get(self, template_id: str) -> Optional[AgentTemplate]:
        row = self._conn.execute(
            "SELECT * FROM templates WHERE id = ?", (template_id,)
        ).fetchone()
        if not row:
            return None
        return self._row_to_template(row)

    def list_templates(
        self, category: Optional[str] = None, builtin_only: bool = False
    ) -> List[AgentTemplate]:
        query = "SELECT * FROM templates WHERE 1=1"
        params: list = []
        if category:
            query += " AND category = ?"
            params.append(category)
        if builtin_only:
            query += " AND is_builtin = 1"
        query += " ORDER BY downloads DESC"
        rows = self._conn.execute(query, params).fetchall()
        return [self._row_to_template(r) for r in rows]

    def create(self, template: AgentTemplate) -> AgentTemplate:
        template.created_at = time.time()
        template.is_builtin = False
        self._save(template)
        return template

    def update(self, template_id: str, **kwargs: Any) -> Optional[AgentTemplate]:
        template = self.get(template_id)
        if not template or template.is_builtin:
            return None
        for k, v in kwargs.items():
            if hasattr(template, k):
                setattr(template, k, v)
        self._save(template)
        return template

    def delete(self, template_id: str) -> bool:
        cursor = self._conn.execute(
            "DELETE FROM templates WHERE id = ? AND is_builtin = 0",
            (template_id,),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def record_download(self, template_id: str) -> bool:
        cursor = self._conn.execute(
            "UPDATE templates SET downloads = downloads + 1 WHERE id = ?",
            (template_id,),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def search(self, query: str) -> List[AgentTemplate]:
        rows = self._conn.execute(
            "SELECT * FROM templates WHERE name LIKE ? OR description LIKE ? "
            "ORDER BY downloads DESC",
            (f"%{query}%", f"%{query}%"),
        ).fetchall()
        return [self._row_to_template(r) for r in rows]

    def _save(self, template: AgentTemplate) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO templates "
            "(id, name, description, category, soul, profile, skills, tools, "
            "avatar_base, avatar_color, autonomy_level, config_overrides, "
            "is_builtin, author, downloads, rating, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                template.id,
                template.name,
                template.description,
                template.category,
                template.soul,
                template.profile,
                json.dumps(template.skills),
                json.dumps(template.tools),
                template.avatar_base,
                template.avatar_color,
                template.autonomy_level,
                json.dumps(template.config_overrides),
                1 if template.is_builtin else 0,
                template.author,
                template.downloads,
                template.rating,
                template.created_at,
            ),
        )
        self._conn.commit()

    @staticmethod
    def _row_to_template(row: sqlite3.Row) -> AgentTemplate:
        return AgentTemplate(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            category=TemplateCategory(row["category"]),
            soul=row["soul"],
            profile=row["profile"],
            skills=json.loads(row["skills"]) if row["skills"] else [],
            tools=json.loads(row["tools"]) if row["tools"] else [],
            avatar_base=row["avatar_base"],
            avatar_color=row["avatar_color"],
            autonomy_level=row["autonomy_level"],
            config_overrides=(
                json.loads(row["config_overrides"]) if row["config_overrides"] else {}
            ),
            is_builtin=bool(row["is_builtin"]),
            author=row["author"],
            downloads=row["downloads"],
            rating=row["rating"],
            created_at=row["created_at"],
        )

    def close(self) -> None:
        self._conn.close()
