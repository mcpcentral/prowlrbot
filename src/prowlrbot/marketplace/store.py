# -*- coding: utf-8 -*-
"""SQLite-backed storage for the ProwlrBot Marketplace."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def _escape_like(value: str) -> str:
    """Escape SQL LIKE wildcards in user input."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


import os

from .models import (
    Bundle,
    ConsolePluginManifest,
    CreditBalance,
    CreditTransaction,
    CreditTransactionType,
    InstallRecord,
    MarketplaceCategory,
    MarketplaceListing,
    ProTier,
    PRO_TIER_LIMITS,
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
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = _dict_factory
        self._init_db()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        cur = self._conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS listings (
                id                  TEXT PRIMARY KEY,
                author_id           TEXT NOT NULL,
                title               TEXT NOT NULL,
                description         TEXT NOT NULL DEFAULT '',
                category            TEXT NOT NULL,
                version             TEXT NOT NULL DEFAULT '1.0.0',
                pricing_model       TEXT NOT NULL DEFAULT 'free',
                price               REAL NOT NULL DEFAULT 0.0,
                revenue_split       REAL NOT NULL DEFAULT 0.70,
                downloads           INTEGER NOT NULL DEFAULT 0,
                rating              REAL NOT NULL DEFAULT 0.0,
                ratings_count       INTEGER NOT NULL DEFAULT 0,
                tags                TEXT NOT NULL DEFAULT '[]',
                status              TEXT NOT NULL DEFAULT 'draft',
                created_at          TEXT NOT NULL,
                updated_at          TEXT NOT NULL,
                difficulty          TEXT NOT NULL DEFAULT 'beginner',
                setup_time_minutes  INTEGER NOT NULL DEFAULT 5,
                persona_tags        TEXT NOT NULL DEFAULT '[]',
                before_after        TEXT NOT NULL DEFAULT '{}',
                skill_scan          TEXT NOT NULL DEFAULT '{}',
                works_with          TEXT NOT NULL DEFAULT '[]',
                demo_url            TEXT NOT NULL DEFAULT '',
                setup_steps         TEXT NOT NULL DEFAULT '[]',
                user_stories        TEXT NOT NULL DEFAULT '[]',
                hero_animation      TEXT NOT NULL DEFAULT ''
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

            CREATE TABLE IF NOT EXISTS credit_transactions (
                id               TEXT PRIMARY KEY,
                user_id          TEXT NOT NULL,
                amount           INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                reference_id     TEXT NOT NULL DEFAULT '',
                description      TEXT NOT NULL DEFAULT '',
                created_at       TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_credits_user
                ON credit_transactions(user_id);

            CREATE TABLE IF NOT EXISTS credit_balances (
                user_id      TEXT PRIMARY KEY,
                balance      INTEGER NOT NULL DEFAULT 0,
                total_earned INTEGER NOT NULL DEFAULT 0,
                total_spent  INTEGER NOT NULL DEFAULT 0,
                tier         TEXT NOT NULL DEFAULT 'free'
            );

            CREATE TABLE IF NOT EXISTS bundles (
                id            TEXT PRIMARY KEY,
                name          TEXT NOT NULL,
                description   TEXT NOT NULL,
                emoji         TEXT DEFAULT '',
                color         TEXT DEFAULT '#00e5ff',
                listing_ids   TEXT DEFAULT '[]',
                install_count INTEGER DEFAULT 0,
                created_at    TEXT DEFAULT (datetime('now'))
            );
            """)
        self._conn.commit()
        self._migrate_v2()
        self._migrate_v3()
        self._migrate_console_plugin()

    def _migrate_console_plugin(self) -> None:
        """Add console_plugin column for marketplace listings that add UI tabs."""
        cur = self._conn.cursor()
        existing = {
            row["name"] for row in cur.execute("PRAGMA table_info(listings)").fetchall()
        }
        if "console_plugin" not in existing:
            cur.execute(
                "ALTER TABLE listings ADD COLUMN console_plugin TEXT DEFAULT NULL"
            )
        self._conn.commit()

    def _migrate_v3(self) -> None:
        """Add v3 trust-tier columns (safe to run multiple times)."""
        cur = self._conn.cursor()
        existing = {
            row["name"] for row in cur.execute("PRAGMA table_info(listings)").fetchall()
        }
        v3_columns = {
            "trust_tier": "TEXT NOT NULL DEFAULT 'verified'",
            "author_name": "TEXT NOT NULL DEFAULT ''",
            "author_url": "TEXT NOT NULL DEFAULT ''",
            "author_avatar_url": "TEXT NOT NULL DEFAULT ''",
            "source_repo": "TEXT NOT NULL DEFAULT ''",
            "license": "TEXT NOT NULL DEFAULT 'MIT'",
            "changelog": "TEXT NOT NULL DEFAULT ''",
            "compatibility": "TEXT NOT NULL DEFAULT ''",
        }
        for col, typedef in v3_columns.items():
            if col not in existing:
                cur.execute(f"ALTER TABLE listings ADD COLUMN {col} {typedef}")
        self._conn.commit()

    def _migrate_v2(self) -> None:
        """Add v2 columns to existing databases (safe to run multiple times)."""
        cur = self._conn.cursor()
        existing = {
            row["name"] for row in cur.execute("PRAGMA table_info(listings)").fetchall()
        }
        v2_columns = {
            "difficulty": "TEXT NOT NULL DEFAULT 'beginner'",
            "setup_time_minutes": "INTEGER NOT NULL DEFAULT 5",
            "persona_tags": "TEXT NOT NULL DEFAULT '[]'",
            "before_after": "TEXT NOT NULL DEFAULT '{}'",
            "skill_scan": "TEXT NOT NULL DEFAULT '{}'",
            "works_with": "TEXT NOT NULL DEFAULT '[]'",
            "demo_url": "TEXT NOT NULL DEFAULT ''",
            "setup_steps": "TEXT NOT NULL DEFAULT '[]'",
            "user_stories": "TEXT NOT NULL DEFAULT '[]'",
            "hero_animation": "TEXT NOT NULL DEFAULT ''",
        }
        for col, typedef in v2_columns.items():
            if col not in existing:
                cur.execute(f"ALTER TABLE listings ADD COLUMN {col} {typedef}")
        self._conn.commit()

    # ------------------------------------------------------------------
    # Listings
    # ------------------------------------------------------------------

    def publish_listing(self, listing: MarketplaceListing) -> MarketplaceListing:
        """Insert a new listing into the store."""
        console_plugin_json = None
        if listing.console_plugin is not None:
            console_plugin_json = listing.console_plugin.model_dump_json()

        self._conn.execute(
            """
            INSERT INTO listings
                (id, author_id, title, description, category, version,
                 pricing_model, price, revenue_split, downloads, rating,
                 ratings_count, tags, status, created_at, updated_at,
                 difficulty, setup_time_minutes, persona_tags, before_after,
                 skill_scan, works_with, demo_url, setup_steps,
                 user_stories, hero_animation,
                 trust_tier, author_name, author_url, author_avatar_url,
                 source_repo, license, changelog, compatibility, console_plugin)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                listing.difficulty,
                listing.setup_time_minutes,
                json.dumps(listing.persona_tags),
                json.dumps(listing.before_after),
                json.dumps(listing.skill_scan),
                json.dumps(listing.works_with),
                listing.demo_url,
                json.dumps(listing.setup_steps),
                json.dumps(listing.user_stories),
                listing.hero_animation,
                (
                    listing.trust_tier.value
                    if hasattr(listing.trust_tier, "value")
                    else listing.trust_tier
                ),
                listing.author_name,
                listing.author_url,
                listing.author_avatar_url,
                listing.source_repo,
                listing.license,
                listing.changelog,
                listing.compatibility,
                console_plugin_json,
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
        persona: Optional[str] = None,
        difficulty: Optional[str] = None,
        sort: str = "popular",
        limit: int = 50,
    ) -> list[MarketplaceListing]:
        """Search listings by text, category, tags, persona, and/or difficulty."""
        conditions: list[str] = []
        params: list[object] = []

        if query:
            conditions.append(
                "(title LIKE ? ESCAPE '\\' OR description LIKE ? ESCAPE '\\'"
                " OR tags LIKE ? ESCAPE '\\')"
            )
            like = f"%{_escape_like(query)}%"
            params.extend([like, like, like])

        if category:
            conditions.append("category = ?")
            params.append(category)

        if tags:
            tag_clauses = ["tags LIKE ? ESCAPE '\\'" for _ in tags]
            conditions.append(f"({' OR '.join(tag_clauses)})")
            params.extend(f"%{_escape_like(t)}%" for t in tags)

        if persona:
            conditions.append("persona_tags LIKE ? ESCAPE '\\'")
            params.append(f"%{_escape_like(persona)}%")

        if difficulty:
            conditions.append("difficulty = ?")
            params.append(difficulty)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sort_map = {
            "popular": "downloads DESC",
            "top_rated": "rating DESC",
            "newest": "created_at DESC",
            "alpha": "title ASC",
        }
        order = sort_map.get(sort, "downloads DESC")
        sql = f"SELECT * FROM listings {where} ORDER BY {order} LIMIT ?"
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
            "difficulty",
            "setup_time_minutes",
            "persona_tags",
            "before_after",
            "skill_scan",
            "works_with",
            "demo_url",
            "setup_steps",
            "user_stories",
            "hero_animation",
            "trust_tier",
            "author_name",
            "author_url",
            "author_avatar_url",
            "source_repo",
            "license",
            "changelog",
            "compatibility",
            "console_plugin",
        }
        filtered = {k: v for k, v in updates.items() if k in allowed}
        if not filtered:
            return existing

        # Serialize list/dict fields to JSON for DB storage
        for json_field in (
            "tags",
            "persona_tags",
            "works_with",
            "setup_steps",
            "user_stories",
            "before_after",
            "skill_scan",
        ):
            if json_field in filtered and not isinstance(filtered[json_field], str):
                filtered[json_field] = json.dumps(filtered[json_field])

        # Normalize enum fields to their .value for DB storage
        if "category" in filtered:
            val = filtered["category"]
            if hasattr(val, "value"):
                filtered["category"] = val.value
            else:
                try:
                    filtered["category"] = MarketplaceCategory(val).value
                except ValueError:
                    pass  # store as-is, will be caught on read

        if "pricing_model" in filtered:
            val = filtered["pricing_model"]
            if hasattr(val, "value"):
                filtered["pricing_model"] = val.value

        if "status" in filtered:
            val = filtered["status"]
            if hasattr(val, "value"):
                filtered["status"] = val.value

        if "trust_tier" in filtered:
            val = filtered["trust_tier"]
            if hasattr(val, "value"):
                filtered["trust_tier"] = val.value

        if "console_plugin" in filtered:
            val = filtered["console_plugin"]
            if val is None:
                filtered["console_plugin"] = None
            elif isinstance(val, dict):
                filtered["console_plugin"] = json.dumps(val)
            elif isinstance(val, ConsolePluginManifest):
                filtered["console_plugin"] = val.model_dump_json()
            else:
                filtered["console_plugin"] = None

        filtered["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Validate column names to prevent SQL injection via dynamic keys
        import re

        for k in filtered:
            if not re.match(r"^[a-z_]+$", k):
                raise ValueError(f"Invalid column name: {k}")
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
    # Credits
    # ------------------------------------------------------------------

    def get_balance(self, user_id: str) -> CreditBalance:
        """Get or create a user's credit balance."""
        row = self._conn.execute(
            "SELECT * FROM credit_balances WHERE user_id = ?", (user_id,)
        ).fetchone()
        if row:
            return CreditBalance(**row)
        # Auto-create for new users
        self._conn.execute(
            "INSERT INTO credit_balances (user_id, balance, total_earned, total_spent, tier) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, 0, 0, 0, "free"),
        )
        self._conn.commit()
        # Optional one-time welcome credits for free tier (set PROWLR_FREE_TIER_WELCOME_CREDITS to enable, e.g. 100)
        welcome = int(os.environ.get("PROWLR_FREE_TIER_WELCOME_CREDITS", "0"))
        if welcome > 0:
            self.add_credits(
                user_id=user_id,
                amount=welcome,
                transaction_type=CreditTransactionType.earned,
                description="Welcome credits (free tier)",
            )
        return self.get_balance(user_id)

    def add_credits(
        self,
        user_id: str,
        amount: int,
        transaction_type: CreditTransactionType,
        reference_id: str = "",
        description: str = "",
    ) -> CreditBalance:
        """Add credits to a user's balance (earn)."""
        if amount <= 0:
            raise ValueError("Credit amount must be positive")

        txn = CreditTransaction(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            reference_id=reference_id,
            description=description,
        )
        self._conn.execute(
            "INSERT INTO credit_transactions (id, user_id, amount, transaction_type, reference_id, description, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                txn.id,
                txn.user_id,
                txn.amount,
                txn.transaction_type,
                txn.reference_id,
                txn.description,
                txn.created_at,
            ),
        )

        # Upsert balance
        self._conn.execute(
            "INSERT INTO credit_balances (user_id, balance, total_earned, total_spent, tier) "
            "VALUES (?, ?, ?, 0, 'free') "
            "ON CONFLICT(user_id) DO UPDATE SET balance = balance + ?, total_earned = total_earned + ?",
            (user_id, amount, amount, amount, amount),
        )
        self._conn.commit()
        return self.get_balance(user_id)

    def spend_credits(
        self,
        user_id: str,
        amount: int,
        transaction_type: CreditTransactionType,
        reference_id: str = "",
        description: str = "",
    ) -> CreditBalance:
        """Spend credits from a user's balance. Raises ValueError if insufficient."""
        if amount <= 0:
            raise ValueError("Spend amount must be positive")

        balance = self.get_balance(user_id)
        if balance.balance < amount:
            raise ValueError(
                f"Insufficient credits: have {balance.balance}, need {amount}"
            )

        txn = CreditTransaction(
            user_id=user_id,
            amount=-amount,
            transaction_type=transaction_type,
            reference_id=reference_id,
            description=description,
        )
        self._conn.execute(
            "INSERT INTO credit_transactions (id, user_id, amount, transaction_type, reference_id, description, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                txn.id,
                txn.user_id,
                txn.amount,
                txn.transaction_type,
                txn.reference_id,
                txn.description,
                txn.created_at,
            ),
        )
        self._conn.execute(
            "UPDATE credit_balances SET balance = balance - ?, total_spent = total_spent + ? WHERE user_id = ?",
            (amount, amount, user_id),
        )
        self._conn.commit()
        return self.get_balance(user_id)

    def get_transactions(
        self, user_id: str, limit: int = 50
    ) -> list[CreditTransaction]:
        """Get recent credit transactions for a user."""
        rows = self._conn.execute(
            "SELECT * FROM credit_transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [CreditTransaction(**r) for r in rows]

    def set_tier(self, user_id: str, tier: str) -> CreditBalance:
        """Update a user's subscription tier."""
        self.get_balance(user_id)  # ensure exists
        self._conn.execute(
            "UPDATE credit_balances SET tier = ? WHERE user_id = ?",
            (tier, user_id),
        )
        self._conn.commit()
        return self.get_balance(user_id)

    # ------------------------------------------------------------------
    # Gamification Credit Helpers
    # ------------------------------------------------------------------

    def award_publish_credits(self, author_id: str, listing_id: str) -> None:
        """Award +100 credits for publishing a listing."""
        self.add_credits(
            user_id=author_id,
            amount=100,
            transaction_type=CreditTransactionType.publish_bonus,
            reference_id=listing_id,
            description="Published a listing",
        )

    def award_install_credits(self, listing_id: str, installer_user_id: str) -> None:
        """Award +5 credits to listing author per unique install."""
        # Dedup: check if this user already triggered credits for this listing
        existing = self._conn.execute(
            "SELECT 1 FROM credit_transactions WHERE transaction_type = ? "
            "AND reference_id = ? AND description LIKE ?",
            ("download_milestone", listing_id, f"%{installer_user_id}%"),
        ).fetchone()
        if existing:
            return

        listing = self.get_listing(listing_id)
        if listing is None:
            return
        self.add_credits(
            user_id=listing.author_id,
            amount=5,
            transaction_type=CreditTransactionType.download_milestone,
            reference_id=listing_id,
            description=f"Install by {installer_user_id}",
        )

    def award_review_credits(self, reviewer_id: str, review_id: str) -> None:
        """Award +5 credits to reviewer for writing a review."""
        self.add_credits(
            user_id=reviewer_id,
            amount=5,
            transaction_type=CreditTransactionType.review_bonus,
            reference_id=review_id,
            description="Wrote a review",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_listing(row: dict) -> MarketplaceListing:
        """Convert a DB row dict into a MarketplaceListing."""
        row = dict(row)  # shallow copy
        # Deserialize all JSON-stored fields
        for field, default in (
            ("tags", "[]"),
            ("persona_tags", "[]"),
            ("works_with", "[]"),
            ("setup_steps", "[]"),
            ("user_stories", "[]"),
            ("before_after", "{}"),
            ("skill_scan", "{}"),
        ):
            raw = row.get(field, default)
            if isinstance(raw, str):
                try:
                    row[field] = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    row[field] = json.loads(default)
        # Parse console_plugin JSON into ConsolePluginManifest or None
        cp = row.get("console_plugin")
        if cp is None or (isinstance(cp, str) and cp.strip() in ("", "null")):
            row["console_plugin"] = None
        elif isinstance(cp, str):
            try:
                row["console_plugin"] = ConsolePluginManifest(**json.loads(cp))
            except (json.JSONDecodeError, TypeError, ValueError):
                row["console_plugin"] = None
        return MarketplaceListing(**row)

    def get_installed_listing_ids(
        self, user_id: Optional[str] = None
    ) -> list[str]:
        """Return listing IDs that have been installed (optionally for a user)."""
        if user_id:
            rows = self._conn.execute(
                "SELECT DISTINCT listing_id FROM installs WHERE user_id = ?",
                (user_id,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT DISTINCT listing_id FROM installs"
            ).fetchall()
        return [r["listing_id"] for r in rows]

    def get_console_plugins(
        self, user_id: Optional[str] = None
    ) -> list[dict]:
        """Return console plugin manifests: built-ins plus from installed listings."""
        # Built-in plugins (always available; can later be made installable-only)
        builtins: list[dict] = [
            {
                "path": "/warroom",
                "label": "War Room",
                "icon": "Radio",
                "entry": "warroom",
            },
        ]
        installed_ids = self.get_installed_listing_ids(user_id)
        from_installed: list[dict] = []
        for lid in installed_ids:
            listing = self.get_listing(lid)
            if listing and listing.console_plugin:
                cp = listing.console_plugin
                # Avoid duplicate paths (installed overrides built-in if same path)
                from_installed.append({
                    "path": cp.path,
                    "label": cp.label,
                    "icon": cp.icon,
                    "entry": cp.entry,
                })
        # Merge: built-ins first, then installed (installed can override by path)
        seen_paths: set[str] = set()
        result: list[dict] = []
        for p in from_installed + builtins:
            if p["path"] not in seen_paths:
                seen_paths.add(p["path"])
                result.append(p)
        return result

    # ------------------------------------------------------------------
    # Bundles
    # ------------------------------------------------------------------

    def create_bundle(self, bundle: Bundle) -> Bundle:
        """Insert a new bundle."""
        self._conn.execute(
            "INSERT INTO bundles (id, name, description, emoji, color, listing_ids, install_count, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                bundle.id,
                bundle.name,
                bundle.description,
                bundle.emoji,
                bundle.color,
                json.dumps(bundle.listing_ids),
                bundle.install_count,
                bundle.created_at,
            ),
        )
        self._conn.commit()
        return bundle

    def get_bundle(self, bundle_id: str) -> Optional[Bundle]:
        """Fetch a single bundle by ID."""
        row = self._conn.execute(
            "SELECT * FROM bundles WHERE id = ?", (bundle_id,)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_bundle(row)

    def list_bundles(self) -> list[Bundle]:
        """Return all bundles."""
        rows = self._conn.execute("SELECT * FROM bundles ORDER BY name").fetchall()
        return [self._row_to_bundle(r) for r in rows]

    def increment_bundle_installs(self, bundle_id: str) -> None:
        """Increment a bundle's install count."""
        self._conn.execute(
            "UPDATE bundles SET install_count = install_count + 1 WHERE id = ?",
            (bundle_id,),
        )
        self._conn.commit()

    @staticmethod
    def _row_to_bundle(row: dict) -> Bundle:
        """Convert a DB row dict into a Bundle."""
        row = dict(row)
        raw = row.get("listing_ids", "[]")
        if isinstance(raw, str):
            try:
                row["listing_ids"] = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                row["listing_ids"] = []
        return Bundle(**row)

    def close(self) -> None:
        self._conn.close()
