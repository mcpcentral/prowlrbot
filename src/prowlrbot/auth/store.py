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
