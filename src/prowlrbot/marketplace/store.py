# -*- coding: utf-8 -*-
"""SQLite-backed storage for the ProwlrBot Marketplace."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .models import (
    InstallRecord,
    MarketplaceCategory,
    MarketplaceListing,
    ReviewEntry,
    TipRecord,
)


def _dict_factory(cursor: sqlite3.Cursor, row: tuple) -> dict:
    """Row factory that returns dicts keyed by column name."""
    return {col[0]: row[i] for i, col in enumerate(cursor.description)}


class MarketplaceStore:
    """SQLite-backed marketplace storage."""

    def __init__(self, db_path: Optional[str | Path] = None) -> None:
        if db_path is None:
            from prowlrbot.constant import WORKING_DIR

            db_path = WORKING_DIR / "marketplace.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = _dict_factory
        self._init_db()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        cur = self._conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS listings (
                id             TEXT PRIMARY KEY,
                author_id      TEXT NOT NULL,
                title          TEXT NOT NULL,
                description    TEXT NOT NULL DEFAULT '',
                category       TEXT NOT NULL,
                version        TEXT NOT NULL DEFAULT '1.0.0',
                pricing_model  TEXT NOT NULL DEFAULT 'free',
                price          REAL NOT NULL DEFAULT 0.0,
                revenue_split  REAL NOT NULL DEFAULT 0.70,
                downloads      INTEGER NOT NULL DEFAULT 0,
                rating         REAL NOT NULL DEFAULT 0.0,
                ratings_count  INTEGER NOT NULL DEFAULT 0,
                tags           TEXT NOT NULL DEFAULT '[]',
                status         TEXT NOT NULL DEFAULT 'draft',
                created_at     TEXT NOT NULL,
                updated_at     TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reviews (
                id          TEXT PRIMARY KEY,
                listing_id  TEXT NOT NULL,
                reviewer_id TEXT NOT NULL,
                rating      INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
                comment     TEXT NOT NULL DEFAULT '',
                created_at  TEXT NOT NULL,
                FOREIGN KEY (listing_id) REFERENCES listings(id)
            );

            CREATE TABLE IF NOT EXISTS installs (
                id           TEXT PRIMARY KEY,
                listing_id   TEXT NOT NULL,
                user_id      TEXT NOT NULL,
                version      TEXT NOT NULL DEFAULT '1.0.0',
                installed_at TEXT NOT NULL,
                FOREIGN KEY (listing_id) REFERENCES listings(id)
            );

            CREATE TABLE IF NOT EXISTS tips (
                id         TEXT PRIMARY KEY,
                listing_id TEXT NOT NULL,
                author_id  TEXT NOT NULL,
                tipper_id  TEXT NOT NULL DEFAULT 'anonymous',
                amount     REAL NOT NULL CHECK(amount > 0),
                message    TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY (listing_id) REFERENCES listings(id)
            );
            """)
        self._conn.commit()

    # ------------------------------------------------------------------
    # Listings
    # ------------------------------------------------------------------

    def publish_listing(self, listing: MarketplaceListing) -> MarketplaceListing:
        """Insert a new listing into the store."""
        self._conn.execute(
            """
            INSERT INTO listings
                (id, author_id, title, description, category, version,
                 pricing_model, price, revenue_split, downloads, rating,
                 ratings_count, tags, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                listing.id,
                listing.author_id,
                listing.title,
                listing.description,
                listing.category.value,
                listing.version,
                listing.pricing_model.value,
                listing.price,
                listing.revenue_split,
                listing.downloads,
                listing.rating,
                listing.ratings_count,
                json.dumps(listing.tags),
                listing.status.value,
                listing.created_at,
                listing.updated_at,
            ),
        )
        self._conn.commit()
        return listing

    def get_listing(self, listing_id: str) -> Optional[MarketplaceListing]:
        """Fetch a single listing by ID."""
        row = self._conn.execute(
            "SELECT * FROM listings WHERE id = ?", (listing_id,)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_listing(row)

    def search_listings(
        self,
        query: str = "",
        category: Optional[str] = None,
        tags: Optional[list[str]] = None,
        limit: int = 50,
    ) -> list[MarketplaceListing]:
        """Search listings by text query, category, and/or tags."""
        conditions: list[str] = []
        params: list[object] = []

        if query:
            conditions.append("(title LIKE ? OR description LIKE ? OR tags LIKE ?)")
            like = f"%{query}%"
            params.extend([like, like, like])

        if category:
            conditions.append("category = ?")
            params.append(category)

        if tags:
            tag_clauses = ["tags LIKE ?" for _ in tags]
            conditions.append(f"({' OR '.join(tag_clauses)})")
            params.extend(f"%{t}%" for t in tags)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT * FROM listings {where} ORDER BY downloads DESC LIMIT ?"
        params.append(limit)

        rows = self._conn.execute(sql, params).fetchall()
        return [self._row_to_listing(r) for r in rows]

    def update_listing(
        self, listing_id: str, updates: dict
    ) -> Optional[MarketplaceListing]:
        """Partially update a listing. Returns updated listing or None."""
        existing = self.get_listing(listing_id)
        if existing is None:
            return None

        allowed = {
            "title",
            "description",
            "category",
            "version",
            "pricing_model",
            "price",
            "revenue_split",
            "tags",
            "status",
        }
        filtered = {k: v for k, v in updates.items() if k in allowed}
        if not filtered:
            return existing

        if "tags" in filtered:
            filtered["tags"] = json.dumps(filtered["tags"])

        filtered["updated_at"] = datetime.now(timezone.utc).isoformat()

        set_clause = ", ".join(f"{k} = ?" for k in filtered)
        params = list(filtered.values()) + [listing_id]
        self._conn.execute(f"UPDATE listings SET {set_clause} WHERE id = ?", params)
        self._conn.commit()
        return self.get_listing(listing_id)

    def list_by_author(self, author_id: str) -> list[MarketplaceListing]:
        """Return all listings by a given author."""
        rows = self._conn.execute(
            "SELECT * FROM listings WHERE author_id = ? ORDER BY created_at DESC",
            (author_id,),
        ).fetchall()
        return [self._row_to_listing(r) for r in rows]

    def get_popular(self, limit: int = 20) -> list[MarketplaceListing]:
        """Return top listings by download count."""
        rows = self._conn.execute(
            "SELECT * FROM listings WHERE status = 'approved' "
            "ORDER BY downloads DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [self._row_to_listing(r) for r in rows]

    def get_top_rated(self, limit: int = 20) -> list[MarketplaceListing]:
        """Return top listings by rating (with at least 1 review)."""
        rows = self._conn.execute(
            "SELECT * FROM listings WHERE status = 'approved' AND ratings_count > 0 "
            "ORDER BY rating DESC, ratings_count DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [self._row_to_listing(r) for r in rows]

    # ------------------------------------------------------------------
    # Reviews
    # ------------------------------------------------------------------

    def add_review(self, review: ReviewEntry) -> ReviewEntry:
        """Add a review and update the listing's aggregate rating."""
        self._conn.execute(
            """
            INSERT INTO reviews (id, listing_id, reviewer_id, rating, comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                review.id,
                review.listing_id,
                review.reviewer_id,
                review.rating,
                review.comment,
                review.created_at,
            ),
        )
        # Recompute aggregate rating for the listing.
        self._conn.execute(
            """
            UPDATE listings SET
                rating = (SELECT AVG(rating) FROM reviews WHERE listing_id = ?),
                ratings_count = (SELECT COUNT(*) FROM reviews WHERE listing_id = ?),
                updated_at = ?
            WHERE id = ?
            """,
            (
                review.listing_id,
                review.listing_id,
                datetime.now(timezone.utc).isoformat(),
                review.listing_id,
            ),
        )
        self._conn.commit()
        return review

    def get_reviews(self, listing_id: str, limit: int = 50) -> list[ReviewEntry]:
        """Return reviews for a listing, newest first."""
        rows = self._conn.execute(
            "SELECT * FROM reviews WHERE listing_id = ? ORDER BY created_at DESC LIMIT ?",
            (listing_id, limit),
        ).fetchall()
        return [ReviewEntry(**r) for r in rows]

    # ------------------------------------------------------------------
    # Installs
    # ------------------------------------------------------------------

    def record_install(self, record: InstallRecord) -> InstallRecord:
        """Record an installation and bump the listing's download count."""
        self._conn.execute(
            """
            INSERT INTO installs (id, listing_id, user_id, version, installed_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                record.id,
                record.listing_id,
                record.user_id,
                record.version,
                record.installed_at,
            ),
        )
        self._conn.execute(
            "UPDATE listings SET downloads = downloads + 1, updated_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), record.listing_id),
        )
        self._conn.commit()
        return record

    def get_install_count(self, listing_id: str) -> int:
        """Return total install count for a listing."""
        row = self._conn.execute(
            "SELECT COUNT(*) AS cnt FROM installs WHERE listing_id = ?",
            (listing_id,),
        ).fetchone()
        return row["cnt"] if row else 0

    # ------------------------------------------------------------------
    # Tips
    # ------------------------------------------------------------------

    def add_tip(self, tip: TipRecord) -> TipRecord:
        """Record a tip for a listing author."""
        self._conn.execute(
            """
            INSERT INTO tips (id, listing_id, author_id, tipper_id, amount, message, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tip.id,
                tip.listing_id,
                tip.author_id,
                tip.tipper_id,
                tip.amount,
                tip.message,
                tip.created_at,
            ),
        )
        self._conn.commit()
        return tip

    def get_tips_for_author(self, author_id: str) -> list[TipRecord]:
        """Return all tips received by an author."""
        rows = self._conn.execute(
            "SELECT * FROM tips WHERE author_id = ? ORDER BY created_at DESC",
            (author_id,),
        ).fetchall()
        return [TipRecord(**r) for r in rows]

    def get_tip_total(self, author_id: str) -> float:
        """Return total tip amount for an author."""
        row = self._conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM tips WHERE author_id = ?",
            (author_id,),
        ).fetchone()
        return row["total"] if row else 0.0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_listing(row: dict) -> MarketplaceListing:
        """Convert a DB row dict into a MarketplaceListing."""
        row = dict(row)  # shallow copy
        tags_raw = row.get("tags", "[]")
        if isinstance(tags_raw, str):
            row["tags"] = json.loads(tags_raw)
        return MarketplaceListing(**row)

    def close(self) -> None:
        self._conn.close()
