# -*- coding: utf-8 -*-
"""Data models for JWT authentication and RBAC."""

from __future__ import annotations

from prowlrbot.compat import StrEnum
from typing import List

from pydantic import BaseModel, Field


class Role(StrEnum):
    """User roles with hierarchical access levels."""

    admin = "admin"
    operator = "operator"
    viewer = "viewer"
    agent = "agent"


class Permission(StrEnum):
    """Granular permissions assignable to roles and users."""

    read = "read"
    write = "write"
    execute = "execute"
    manage_users = "manage_users"
    manage_agents = "manage_agents"
    manage_config = "manage_config"
    manage_marketplace = "manage_marketplace"
    view_audit = "view_audit"


ROLE_PERMISSIONS: dict[Role, list[Permission]] = {
    Role.admin: list(Permission),
    Role.operator: [
        Permission.read,
        Permission.write,
        Permission.execute,
        Permission.manage_agents,
    ],
    Role.viewer: [Permission.read],
    Role.agent: [Permission.read, Permission.execute],
}


class User(BaseModel):
    """Authenticated user record."""

    id: str = ""
    username: str = ""
    email: str = ""
    role: Role = Role.viewer
    permissions: List[Permission] = Field(default_factory=list)
    hashed_password: str = ""
    is_active: bool = True
    created_at: float = 0
    last_login: float = 0


class TokenPayload(BaseModel):
    """JWT token payload (claims)."""

    sub: str  # user_id
    username: str
    role: Role
    exp: float
    iat: float
    iss: str = "prowlrbot"


class AuthResponse(BaseModel):
    """Response returned after successful authentication."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    role: Role
