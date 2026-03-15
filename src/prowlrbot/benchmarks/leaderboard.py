# -*- coding: utf-8 -*-
"""Model leaderboard — track and compare AI model performance."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BenchmarkResult(BaseModel):
    """Result of a single benchmark run."""

    id: str = ""
    model: str
    benchmark: str  # "tool_use", "reasoning", "code", "memory", "speed", "custom"
    score: float  # 0-100
    latency_ms: int = 0
    cost_usd: float = 0.0
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)


class ModelRanking(BaseModel):
    """Aggregated ranking for a model."""

    rank: int
    model: str
    avg_score: float
    total_runs: int
    avg_latency_ms: int
    avg_cost_per_1k: float
    best_category: str = ""
    last_run: float = 0.0


class BenchmarkSuite(BaseModel):
    """A custom benchmark suite definition."""

    id: str
    name: str
    description: str = ""
    tasks: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)


class ModelLeaderboard:
    """SQLite-backed model leaderboard."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS benchmark_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model TEXT NOT NULL,
                benchmark TEXT NOT NULL,
                score REAL NOT NULL,
                latency_ms INTEGER DEFAULT 0,
                cost_usd REAL DEFAULT 0.0,
                details TEXT DEFAULT '{}',
                timestamp REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_bench_model
            ON benchmark_results(model, benchmark);

            CREATE TABLE IF NOT EXISTS benchmark_suites (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                tasks TEXT DEFAULT '[]',
                created_at REAL NOT NULL
            );
        """,
        )
        self._conn.commit()

    def record_result(self, result: BenchmarkResult) -> int:
        """Record a benchmark result."""
        cursor = self._conn.execute(
            "INSERT INTO benchmark_results (model, benchmark, score, latency_ms, cost_usd, details, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                result.model,
                result.benchmark,
                result.score,
                result.latency_ms,
                result.cost_usd,
                json.dumps(result.details),
                result.timestamp,
            ),
        )
        self._conn.commit()
        return cursor.lastrowid

    def get_leaderboard(
        self,
        benchmark: Optional[str] = None,
        limit: int = 20,
    ) -> List[ModelRanking]:
        """Get model rankings, optionally filtered by benchmark category."""
        if benchmark:
            sql = """
                SELECT model,
                       AVG(score) as avg_score,
                       COUNT(*) as total_runs,
                       AVG(latency_ms) as avg_latency,
                       AVG(cost_usd) as avg_cost,
                       MAX(timestamp) as last_run
                FROM benchmark_results
                WHERE benchmark = ?
                GROUP BY model
                ORDER BY avg_score DESC
                LIMIT ?
            """
            rows = self._conn.execute(sql, (benchmark, limit)).fetchall()
        else:
            sql = """
                SELECT model,
                       AVG(score) as avg_score,
                       COUNT(*) as total_runs,
                       AVG(latency_ms) as avg_latency,
                       AVG(cost_usd) as avg_cost,
                       MAX(timestamp) as last_run
                FROM benchmark_results
                GROUP BY model
                ORDER BY avg_score DESC
                LIMIT ?
            """
            rows = self._conn.execute(sql, (limit,)).fetchall()

        rankings = []
        for i, row in enumerate(rows, 1):
            # Find best category for this model
            best = self._conn.execute(
                "SELECT benchmark, AVG(score) as s FROM benchmark_results "
                "WHERE model = ? GROUP BY benchmark ORDER BY s DESC LIMIT 1",
                (row["model"],),
            ).fetchone()

            rankings.append(
                ModelRanking(
                    rank=i,
                    model=row["model"],
                    avg_score=round(float(row["avg_score"]), 1),
                    total_runs=int(row["total_runs"]),
                    avg_latency_ms=int(row["avg_latency"]),
                    avg_cost_per_1k=(
                        round(float(row["avg_cost"]) * 1000, 4)
                        if row["avg_cost"]
                        else 0.0
                    ),
                    best_category=best["benchmark"] if best else "",
                    last_run=float(row["last_run"]),
                ),
            )
        return rankings

    def get_model_history(
        self,
        model: str,
        limit: int = 50,
    ) -> List[BenchmarkResult]:
        """Get benchmark history for a specific model."""
        rows = self._conn.execute(
            "SELECT * FROM benchmark_results WHERE model = ? ORDER BY timestamp DESC LIMIT ?",
            (model, limit),
        ).fetchall()
        return [
            BenchmarkResult(
                id=str(row["id"]),
                model=row["model"],
                benchmark=row["benchmark"],
                score=row["score"],
                latency_ms=row["latency_ms"],
                cost_usd=row["cost_usd"],
                details=json.loads(row["details"]),
                timestamp=row["timestamp"],
            )
            for row in rows
        ]

    def get_categories(self) -> List[str]:
        """Get all benchmark categories that have results."""
        rows = self._conn.execute(
            "SELECT DISTINCT benchmark FROM benchmark_results ORDER BY benchmark",
        ).fetchall()
        return [row["benchmark"] for row in rows]

    # --- Suites ---

    def save_suite(self, suite: BenchmarkSuite) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO benchmark_suites (id, name, description, tasks, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                suite.id,
                suite.name,
                suite.description,
                json.dumps(suite.tasks),
                suite.created_at,
            ),
        )
        self._conn.commit()

    def list_suites(self) -> List[BenchmarkSuite]:
        rows = self._conn.execute(
            "SELECT * FROM benchmark_suites ORDER BY created_at DESC",
        ).fetchall()
        return [
            BenchmarkSuite(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                tasks=json.loads(row["tasks"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def close(self) -> None:
        self._conn.close()
