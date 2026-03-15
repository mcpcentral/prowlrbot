# -*- coding: utf-8 -*-
"""Usage analytics tracking with SQLite persistence."""

import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class UsageStat(BaseModel):
    """A single usage record."""

    session_id: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: float
    timestamp: float


class UsageSummary(BaseModel):
    """Aggregated usage statistics over a time period."""

    total_tokens: int = 0
    total_cost: float = 0.0
    total_queries: int = 0
    avg_latency_ms: float = 0.0
    model_breakdown: Dict[str, "ModelStats"] = Field(default_factory=dict)
    period_start: Optional[float] = None
    period_end: Optional[float] = None


class ModelStats(BaseModel):
    """Per-model aggregated statistics."""

    total_tokens: int = 0
    total_cost: float = 0.0
    total_queries: int = 0
    avg_latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0


# Resolve forward reference
UsageSummary.model_rebuild()


# Period durations in seconds
_PERIOD_SECONDS = {
    "day": 86400,
    "week": 86400 * 7,
    "month": 86400 * 30,
}


class AnalyticsTracker:
    """SQLite-backed usage analytics tracker."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        if db_path is None:
            from prowlrbot.constant import WORKING_DIR

            db_path = WORKING_DIR / "analytics.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usage_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                model TEXT NOT NULL,
                input_tokens INTEGER NOT NULL DEFAULT 0,
                output_tokens INTEGER NOT NULL DEFAULT 0,
                cost_usd REAL NOT NULL DEFAULT 0.0,
                latency_ms REAL NOT NULL DEFAULT 0.0,
                timestamp REAL NOT NULL
            )
        """,
        )
        self._conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_usage_timestamp
            ON usage_stats(timestamp DESC)
        """,
        )
        self._conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_usage_model
            ON usage_stats(model, timestamp DESC)
        """,
        )
        self._conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_usage_session
            ON usage_stats(session_id, timestamp DESC)
        """,
        )
        self._conn.commit()

    def record(
        self,
        session_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        latency_ms: float,
    ) -> int:
        """Insert a usage record. Returns the record ID."""
        cursor = self._conn.execute(
            """INSERT INTO usage_stats
               (session_id, model, input_tokens, output_tokens, cost_usd, latency_ms, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                model,
                input_tokens,
                output_tokens,
                cost_usd,
                latency_ms,
                time.time(),
            ),
        )
        self._conn.commit()
        return cursor.lastrowid

    def _period_cutoff(self, period: str) -> Optional[float]:
        """Return the timestamp cutoff for a period, or None for 'all'."""
        if period == "all":
            return None
        seconds = _PERIOD_SECONDS.get(period)
        if seconds is None:
            return None
        return time.time() - seconds

    def get_summary(self, period: str = "day") -> UsageSummary:
        """Get aggregated usage summary for a time period.

        Args:
            period: One of "day", "week", "month", "all".
        """
        cutoff = self._period_cutoff(period)
        now = time.time()

        if cutoff is not None:
            row = self._conn.execute(
                """SELECT
                    COALESCE(SUM(input_tokens + output_tokens), 0) as total_tokens,
                    COALESCE(SUM(cost_usd), 0) as total_cost,
                    COUNT(*) as total_queries,
                    COALESCE(AVG(latency_ms), 0) as avg_latency_ms,
                    MIN(timestamp) as period_start,
                    MAX(timestamp) as period_end
                FROM usage_stats WHERE timestamp >= ?""",
                (cutoff,),
            ).fetchone()
        else:
            row = self._conn.execute(
                """SELECT
                    COALESCE(SUM(input_tokens + output_tokens), 0) as total_tokens,
                    COALESCE(SUM(cost_usd), 0) as total_cost,
                    COUNT(*) as total_queries,
                    COALESCE(AVG(latency_ms), 0) as avg_latency_ms,
                    MIN(timestamp) as period_start,
                    MAX(timestamp) as period_end
                FROM usage_stats""",
            ).fetchone()

        # Build model breakdown for the same period
        model_breakdown = self._build_model_breakdown(cutoff)

        return UsageSummary(
            total_tokens=row["total_tokens"],
            total_cost=round(row["total_cost"], 6),
            total_queries=row["total_queries"],
            avg_latency_ms=round(row["avg_latency_ms"], 2),
            model_breakdown=model_breakdown,
            period_start=row["period_start"] or (cutoff if cutoff else None),
            period_end=row["period_end"] or now,
        )

    def _build_model_breakdown(
        self,
        cutoff: Optional[float] = None,
    ) -> Dict[str, ModelStats]:
        """Build per-model statistics."""
        if cutoff is not None:
            rows = self._conn.execute(
                """SELECT
                    model,
                    COALESCE(SUM(input_tokens + output_tokens), 0) as total_tokens,
                    COALESCE(SUM(input_tokens), 0) as input_tokens,
                    COALESCE(SUM(output_tokens), 0) as output_tokens,
                    COALESCE(SUM(cost_usd), 0) as total_cost,
                    COUNT(*) as total_queries,
                    COALESCE(AVG(latency_ms), 0) as avg_latency_ms
                FROM usage_stats
                WHERE timestamp >= ?
                GROUP BY model
                ORDER BY total_cost DESC""",
                (cutoff,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """SELECT
                    model,
                    COALESCE(SUM(input_tokens + output_tokens), 0) as total_tokens,
                    COALESCE(SUM(input_tokens), 0) as input_tokens,
                    COALESCE(SUM(output_tokens), 0) as output_tokens,
                    COALESCE(SUM(cost_usd), 0) as total_cost,
                    COUNT(*) as total_queries,
                    COALESCE(AVG(latency_ms), 0) as avg_latency_ms
                FROM usage_stats
                GROUP BY model
                ORDER BY total_cost DESC""",
            ).fetchall()

        return {
            row["model"]: ModelStats(
                total_tokens=row["total_tokens"],
                input_tokens=row["input_tokens"],
                output_tokens=row["output_tokens"],
                total_cost=round(row["total_cost"], 6),
                total_queries=row["total_queries"],
                avg_latency_ms=round(row["avg_latency_ms"], 2),
            )
            for row in rows
        }

    def get_model_breakdown(self) -> Dict[str, ModelStats]:
        """Get per-model usage statistics (all time)."""
        return self._build_model_breakdown(cutoff=None)

    def get_cost_over_time(self, days: int = 30) -> List[Dict]:
        """Get daily cost data for charting.

        Returns a list of dicts with 'date', 'cost', 'tokens', 'queries' keys.
        """
        cutoff = time.time() - (days * 86400)
        rows = self._conn.execute(
            """SELECT
                DATE(timestamp, 'unixepoch') as date,
                COALESCE(SUM(cost_usd), 0) as cost,
                COALESCE(SUM(input_tokens + output_tokens), 0) as tokens,
                COUNT(*) as queries
            FROM usage_stats
            WHERE timestamp >= ?
            GROUP BY DATE(timestamp, 'unixepoch')
            ORDER BY date ASC""",
            (cutoff,),
        ).fetchall()

        return [
            {
                "date": row["date"],
                "cost": round(row["cost"], 6),
                "tokens": row["tokens"],
                "queries": row["queries"],
            }
            for row in rows
        ]

    def get_recent(self, limit: int = 50) -> List[UsageStat]:
        """Get the most recent usage records."""
        rows = self._conn.execute(
            """SELECT session_id, model, input_tokens, output_tokens,
                      cost_usd, latency_ms, timestamp
            FROM usage_stats
            ORDER BY timestamp DESC
            LIMIT ?""",
            (limit,),
        ).fetchall()

        return [
            UsageStat(
                session_id=row["session_id"],
                model=row["model"],
                input_tokens=row["input_tokens"],
                output_tokens=row["output_tokens"],
                cost_usd=row["cost_usd"],
                latency_ms=row["latency_ms"],
                timestamp=row["timestamp"],
            )
            for row in rows
        ]

    def cleanup(self, older_than_days: int = 90) -> int:
        """Delete records older than the specified number of days.

        Returns the number of deleted records.
        """
        cutoff = time.time() - (older_than_days * 86400)
        cursor = self._conn.execute(
            "DELETE FROM usage_stats WHERE timestamp < ?",
            (cutoff,),
        )
        self._conn.commit()
        return cursor.rowcount

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()
