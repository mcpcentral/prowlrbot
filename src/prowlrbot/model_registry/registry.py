# -*- coding: utf-8 -*-
"""SQLite-backed model registry."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Optional

from .models import ModelCapability, ModelComparison, ModelEntry, ModelType


class ModelRegistry:
    """Persistent registry of LLM models backed by SQLite."""

    def __init__(self, db_path: Optional[str | Path] = None) -> None:
        if db_path is None:
            from ..constant import WORKING_DIR

            db_path = WORKING_DIR / "model_registry.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS models (
                id                TEXT PRIMARY KEY,
                name              TEXT NOT NULL,
                provider          TEXT NOT NULL,
                model_type        TEXT NOT NULL DEFAULT 'chat',
                capabilities      TEXT NOT NULL DEFAULT '[]',
                context_window    INTEGER NOT NULL DEFAULT 4096,
                max_output_tokens INTEGER NOT NULL DEFAULT 4096,
                cost_per_1k_input REAL NOT NULL DEFAULT 0.0,
                cost_per_1k_output REAL NOT NULL DEFAULT 0.0,
                is_local          INTEGER NOT NULL DEFAULT 0,
                metadata          TEXT NOT NULL DEFAULT '{}',
                added_at          REAL NOT NULL DEFAULT 0.0,
                last_used         REAL NOT NULL DEFAULT 0.0
            )
            """,
        )
        self._conn.commit()

    # -- helpers --

    def _row_to_entry(self, row: sqlite3.Row) -> ModelEntry:
        return ModelEntry(
            id=row["id"],
            name=row["name"],
            provider=row["provider"],
            model_type=ModelType(row["model_type"]),
            capabilities=[ModelCapability(c) for c in json.loads(row["capabilities"])],
            context_window=row["context_window"],
            max_output_tokens=row["max_output_tokens"],
            cost_per_1k_input=row["cost_per_1k_input"],
            cost_per_1k_output=row["cost_per_1k_output"],
            is_local=bool(row["is_local"]),
            metadata=json.loads(row["metadata"]),
            added_at=row["added_at"],
            last_used=row["last_used"],
        )

    # -- CRUD --

    def register(self, entry: ModelEntry) -> ModelEntry:
        """Register a new model. Sets added_at if not already set."""
        if entry.added_at == 0.0:
            entry.added_at = time.time()
        self._conn.execute(
            """
            INSERT INTO models (
                id, name, provider, model_type, capabilities,
                context_window, max_output_tokens,
                cost_per_1k_input, cost_per_1k_output,
                is_local, metadata, added_at, last_used
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.id,
                entry.name,
                entry.provider,
                entry.model_type.value,
                json.dumps([c.value for c in entry.capabilities]),
                entry.context_window,
                entry.max_output_tokens,
                entry.cost_per_1k_input,
                entry.cost_per_1k_output,
                int(entry.is_local),
                json.dumps(entry.metadata),
                entry.added_at,
                entry.last_used,
            ),
        )
        self._conn.commit()
        return entry

    def get(self, model_id: str) -> Optional[ModelEntry]:
        """Get a model by its unique id."""
        row = self._conn.execute(
            "SELECT * FROM models WHERE id = ?",
            (model_id,),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_entry(row)

    def get_by_name(self, name: str, provider: str) -> Optional[ModelEntry]:
        """Get a model by name and provider."""
        row = self._conn.execute(
            "SELECT * FROM models WHERE name = ? AND provider = ?",
            (name, provider),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_entry(row)

    def list_models(
        self,
        model_type: Optional[ModelType] = None,
        provider: Optional[str] = None,
        capability: Optional[ModelCapability] = None,
    ) -> list[ModelEntry]:
        """List models with optional filters."""
        query = "SELECT * FROM models WHERE 1=1"
        params: list = []

        if model_type is not None:
            query += " AND model_type = ?"
            params.append(model_type.value)
        if provider is not None:
            query += " AND provider = ?"
            params.append(provider)

        rows = self._conn.execute(query, params).fetchall()
        entries = [self._row_to_entry(r) for r in rows]

        if capability is not None:
            entries = [e for e in entries if capability in e.capabilities]

        return entries

    def update(self, model_id: str, **kwargs) -> Optional[ModelEntry]:
        """Update fields on an existing model entry."""
        existing = self.get(model_id)
        if existing is None:
            return None

        allowed = {
            "name",
            "provider",
            "model_type",
            "capabilities",
            "context_window",
            "max_output_tokens",
            "cost_per_1k_input",
            "cost_per_1k_output",
            "is_local",
            "metadata",
        }
        sets: list[str] = []
        params: list = []
        for key, value in kwargs.items():
            if key not in allowed:
                continue
            if key == "capabilities":
                sets.append("capabilities = ?")
                params.append(
                    json.dumps(
                        [
                            c.value if isinstance(c, ModelCapability) else c
                            for c in value
                        ],
                    ),
                )
            elif key == "model_type":
                sets.append("model_type = ?")
                params.append(
                    value.value if isinstance(value, ModelType) else value,
                )
            elif key == "metadata":
                sets.append("metadata = ?")
                params.append(json.dumps(value))
            elif key == "is_local":
                sets.append("is_local = ?")
                params.append(int(value))
            else:
                sets.append(f"{key} = ?")
                params.append(value)

        if not sets:
            return existing

        params.append(model_id)
        self._conn.execute(
            f"UPDATE models SET {', '.join(sets)} WHERE id = ?",
            params,
        )
        self._conn.commit()
        return self.get(model_id)

    def delete(self, model_id: str) -> bool:
        """Delete a model by id. Returns True if a row was deleted."""
        cur = self._conn.execute(
            "DELETE FROM models WHERE id = ?",
            (model_id,),
        )
        self._conn.commit()
        return cur.rowcount > 0

    def search(self, query: str) -> list[ModelEntry]:
        """Search models by name (case-insensitive substring match)."""
        rows = self._conn.execute(
            "SELECT * FROM models WHERE name LIKE ?",
            (f"%{query}%",),
        ).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def compare(self, model_ids: list[str]) -> ModelComparison:
        """Build a side-by-side comparison for the given model ids."""
        models: list[ModelEntry] = []
        for mid in model_ids:
            entry = self.get(mid)
            if entry is not None:
                models.append(entry)

        matrix: dict = {}
        if models:
            matrix["context_window"] = {m.id: m.context_window for m in models}
            matrix["max_output_tokens"] = {m.id: m.max_output_tokens for m in models}
            matrix["cost_per_1k_input"] = {m.id: m.cost_per_1k_input for m in models}
            matrix["cost_per_1k_output"] = {m.id: m.cost_per_1k_output for m in models}
            matrix["capabilities"] = {
                m.id: [c.value for c in m.capabilities] for m in models
            }
            matrix["is_local"] = {m.id: m.is_local for m in models}

        return ModelComparison(models=models, comparison_matrix=matrix)

    def record_usage(self, model_id: str) -> None:
        """Update the last_used timestamp to now."""
        self._conn.execute(
            "UPDATE models SET last_used = ? WHERE id = ?",
            (time.time(), model_id),
        )
        self._conn.commit()

    def get_recommended(self, task: str) -> list[ModelEntry]:
        """Return models recommended for a task based on capabilities.

        Supported tasks:
        - "chat": models with text_generation capability
        - "code": models with text_generation, preferring code type
        - "vision": models with vision capability
        """
        task = task.lower().strip()

        if task == "vision":
            return self.list_models(capability=ModelCapability.vision)

        if task == "code":
            all_text = self.list_models(
                capability=ModelCapability.text_generation,
            )
            # Sort so that code-type models come first
            all_text.sort(
                key=lambda m: (0 if m.model_type == ModelType.code else 1),
            )
            return all_text

        # Default / "chat"
        return self.list_models(capability=ModelCapability.text_generation)
