# -*- coding: utf-8 -*-
"""SQLite-backed user store for authentication."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Optional

from .models import Permission, Role, ROLE_PERMISSIONS, User
from ..constant import WORKING_DIR

logger = logging.getLogger(__name__)

# Store auth DB in the secret directory (mode 0o700) since it contains
# password hashes. Falls back to WORKING_DIR if the secret dir doesn't exist.
_SECRET_DIR = Path.home() / ".prowlrbot.secret"
_DB_PATH = _SECRET_DIR / "auth.db" if _SECRET_DIR.exists() else WORKING_DIR / "auth.db"

_SCHEMA = """\
CREATE TABLE IF NOT EXISTS users (
    id              TEXT PRIMARY KEY,
    username        TEXT UNIQUE NOT NULL,
    email           TEXT NOT NULL DEFAULT '',
    role            TEXT NOT NULL DEFAULT 'viewer',
    permissions     TEXT NOT NULL DEFAULT '[]',
    hashed_password TEXT NOT NULL DEFAULT '',
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      REAL NOT NULL DEFAULT 0,
    last_login      REAL NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS oauth_identities (
    provider        TEXT NOT NULL,
    provider_id     TEXT NOT NULL,
    user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email           TEXT NOT NULL DEFAULT '',
    avatar_url      TEXT NOT NULL DEFAULT '',
    created_at      REAL NOT NULL DEFAULT 0,
    PRIMARY KEY (provider, provider_id)
);
CREATE INDEX IF NOT EXISTS idx_oauth_user ON oauth_identities(user_id);
"""


def _hash_password(password: str, salt: Optional[bytes] = None) -> str:
    """Hash *password* with PBKDF2-HMAC-SHA256.

    Returns ``"salt_hex:hash_hex"``.
    """
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations=260_000)
    return f"{salt.hex()}:{dk.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    """Verify *password* against a ``"salt_hex:hash_hex"`` string."""
    if ":" not in stored:
        return False
    salt_hex, _ = stored.split(":", 1)
    try:
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        return False
    return _hash_password(password, salt) == stored


class UserStore:
    """SQLite-backed CRUD store for :class:`User` records."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_user(row: sqlite3.Row) -> User:
        d = dict(row)
        d["is_active"] = bool(d["is_active"])
        d["permissions"] = [Permission(p) for p in json.loads(d["permissions"])]
        d["role"] = Role(d["role"])
        return User(**d)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_user(
        self,
        username: str,
        password: str,
        email: str = "",
        role: Role = Role.viewer,
        permissions: Optional[list[Permission]] = None,
    ) -> User:
        """Create a new user and return the :class:`User` record."""
        user_id = uuid.uuid4().hex
        now = time.time()
        if permissions is None:
            permissions = list(ROLE_PERMISSIONS.get(role, []))
        hashed = _hash_password(password)
        self._conn.execute(
            "INSERT INTO users (id, username, email, role, permissions, "
            "hashed_password, is_active, created_at, last_login) "
            "VALUES (?, ?, ?, ?, ?, ?, 1, ?, 0)",
            (
                user_id,
                username,
                email,
                role.value,
                json.dumps([p.value for p in permissions]),
                hashed,
                now,
            ),
        )
        self._conn.commit()
        return User(
            id=user_id,
            username=username,
            email=email,
            role=role,
            permissions=permissions,
            hashed_password=hashed,
            is_active=True,
            created_at=now,
            last_login=0,
        )

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        row = self._conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return self._row_to_user(row) if row else None

    def get_user_by_username(self, username: str) -> Optional[User]:
        row = self._conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        return self._row_to_user(row) if row else None

    def list_users(self) -> list[User]:
        rows = self._conn.execute(
            "SELECT * FROM users ORDER BY created_at DESC"
        ).fetchall()
        return [self._row_to_user(r) for r in rows]

    def update_user(self, user_id: str, **fields: object) -> Optional[User]:
        """Update arbitrary fields on a user record.

        Supported keys: ``username``, ``email``, ``role``, ``permissions``,
        ``is_active``.
        """
        allowed = {"username", "email", "role", "permissions", "is_active"}
        updates: dict[str, object] = {}
        for key, value in fields.items():
            if key not in allowed:
                continue
            if key == "permissions":
                updates[key] = json.dumps([p.value for p in value])  # type: ignore[union-attr]
            elif key == "role":
                updates[key] = value.value if isinstance(value, Role) else value
            elif key == "is_active":
                updates[key] = int(value)  # type: ignore[arg-type]
            else:
                updates[key] = value
        if not updates:
            return self.get_user_by_id(user_id)
        # Validate column names to prevent SQL injection via dynamic keys
        import re

        for k in updates:
            if not re.match(r"^[a-z_]+$", k):
                raise ValueError(f"Invalid column name: {k}")
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [user_id]
        self._conn.execute(
            f"UPDATE users SET {set_clause} WHERE id = ?", values  # noqa: S608
        )
        self._conn.commit()
        return self.get_user_by_id(user_id)

    def delete_user(self, user_id: str) -> bool:
        cursor = self._conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        self._conn.commit()
        return cursor.rowcount > 0

    def update_last_login(self, user_id: str) -> None:
        self._conn.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (time.time(), user_id),
        )
        self._conn.commit()

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Verify credentials and return :class:`User` if valid."""
        user = self.get_user_by_username(username)
        if user is None or not user.is_active:
            return None
        if not _verify_password(password, user.hashed_password):
            return None
        self.update_last_login(user.id)
        return self.get_user_by_id(user.id)

    def update_password(self, username: str, new_password: str) -> bool:
        """Set a new password for the user with the given username. Returns True if updated."""
        user = self.get_user_by_username(username)
        if user is None:
            return False
        hashed = _hash_password(new_password)
        self._conn.execute(
            "UPDATE users SET hashed_password = ? WHERE id = ?",
            (hashed, user.id),
        )
        self._conn.commit()
        return True

    # ------------------------------------------------------------------
    # OAuth identity linking
    # ------------------------------------------------------------------

    def find_user_by_oauth(self, provider: str, provider_id: str) -> Optional[User]:
        """Find a user linked to an OAuth identity."""
        row = self._conn.execute(
            "SELECT user_id FROM oauth_identities WHERE provider = ? AND provider_id = ?",
            (provider, provider_id),
        ).fetchone()
        if row is None:
            return None
        return self.get_user_by_id(row["user_id"])

    def link_oauth(
        self,
        user_id: str,
        provider: str,
        provider_id: str,
        email: str = "",
        avatar_url: str = "",
    ) -> None:
        """Link an OAuth identity to an existing user."""
        self._conn.execute(
            "INSERT OR REPLACE INTO oauth_identities "
            "(provider, provider_id, user_id, email, avatar_url, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (provider, provider_id, user_id, email, avatar_url, time.time()),
        )
        self._conn.commit()

    def authenticate_oauth(
        self,
        provider: str,
        provider_id: str,
        email: str,
        username: str,
        avatar_url: str = "",
    ) -> User:
        """Find or create a user from an OAuth login.

        If an OAuth identity exists, return the linked user.
        If a user with matching email exists, link and return.
        Otherwise, create a new user.
        """
        # 1. Check existing OAuth link
        user = self.find_user_by_oauth(provider, provider_id)
        if user is not None:
            self.update_last_login(user.id)
            return user

        # 2. Check if a user with this email already exists
        if email:
            row = self._conn.execute(
                "SELECT * FROM users WHERE email = ?", (email,)
            ).fetchone()
            if row:
                user = self._row_to_user(row)
                self.link_oauth(user.id, provider, provider_id, email, avatar_url)
                self.update_last_login(user.id)
                return user

        # 3. Create a new user (no password — OAuth only)
        # Ensure unique username by appending suffix if needed
        base_username = username or email.split("@")[0] if email else provider_id
        final_username = base_username
        suffix = 1
        while self.get_user_by_username(final_username) is not None:
            final_username = f"{base_username}{suffix}"
            suffix += 1

        user = self.create_user(
            username=final_username,
            password=os.urandom(32).hex(),  # random password (OAuth users don't use it)
            email=email,
            role=Role.viewer,
        )
        self.link_oauth(user.id, provider, provider_id, email, avatar_url)
        return user

    # ------------------------------------------------------------------
    # Clerk identity (same pattern as OAuth: link by provider='clerk')
    # ------------------------------------------------------------------

    def find_user_by_clerk_id(self, clerk_user_id: str) -> Optional[User]:
        """Find a user linked to a Clerk identity (provider='clerk', provider_id=clerk_user_id)."""
        return self.find_user_by_oauth("clerk", clerk_user_id)

    def get_or_create_user_by_clerk(
        self,
        clerk_user_id: str,
        email: str = "",
        username: str = "",
    ) -> User:
        """Find or create a user for a Clerk sign-in.

        If a user is already linked to this Clerk id, returns that user.
        Otherwise creates a new user (no password) and links the Clerk identity.
        """
        user = self.find_user_by_clerk_id(clerk_user_id)
        if user is not None:
            self.update_last_login(user.id)
            return user

        base_username = username or (email.split("@")[0] if email else f"clerk_{clerk_user_id[:12]}")
        final_username = base_username
        suffix = 1
        while self.get_user_by_username(final_username) is not None:
            final_username = f"{base_username}{suffix}"
            suffix += 1

        user = self.create_user(
            username=final_username,
            password=os.urandom(32).hex(),
            email=email,
            role=Role.viewer,
        )
        self.link_oauth(user.id, "clerk", clerk_user_id, email, "")
        return user
