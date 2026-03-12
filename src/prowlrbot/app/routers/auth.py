# -*- coding: utf-8 -*-
"""Authentication API endpoints."""

from __future__ import annotations

import logging
import os
import sqlite3
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException

from ...auth.jwt_handler import JWTHandler
from ...auth.middleware import get_current_user, require_role, _JWT_SECRET
from ...auth.models import AuthResponse, Permission, Role, ROLE_PERMISSIONS, User
from ...auth.store import UserStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# ------------------------------------------------------------------
# Shared helpers (request-scoped singletons are fine for a single
# process; the UserStore already uses check_same_thread=False).
# ------------------------------------------------------------------

_store: Optional[UserStore] = None


def _get_store() -> UserStore:
    global _store
    if _store is None:
        _store = UserStore()
    return _store


def _get_jwt() -> JWTHandler:
    expiry = int(os.environ.get("PROWLRBOT_JWT_EXPIRY_MINUTES", "60"))
    return JWTHandler(secret_key=_JWT_SECRET, expiry_minutes=expiry)


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------


@router.post(
    "/register",
    summary="Register a new user",
    response_model=AuthResponse,
)
async def register(
    username: str = Body(...),
    password: str = Body(...),
    email: str = Body(""),
) -> AuthResponse:
    if len(password) < 12:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 12 characters",
        )
    store = _get_store()
    try:
        user = store.create_user(
            username=username,
            password=password,
            email=email,
            role=Role.viewer,
        )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Username already exists") from exc

    jwt = _get_jwt()
    token = jwt.create_token(user)
    return AuthResponse(
        access_token=token,
        expires_in=jwt._expiry_minutes * 60,
        user_id=user.id,
        role=user.role,
    )


@router.post(
    "/login",
    summary="Authenticate and obtain a JWT",
    response_model=AuthResponse,
)
async def login(
    username: str = Body(...),
    password: str = Body(...),
) -> AuthResponse:
    store = _get_store()
    user = store.authenticate(username, password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    jwt = _get_jwt()
    token = jwt.create_token(user)
    return AuthResponse(
        access_token=token,
        expires_in=jwt._expiry_minutes * 60,
        user_id=user.id,
        role=user.role,
    )


@router.get(
    "/me",
    summary="Get current authenticated user",
)
async def me(user: User = Depends(get_current_user)) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "permissions": user.permissions,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "last_login": user.last_login,
    }


@router.post(
    "/refresh",
    summary="Refresh an existing JWT",
    response_model=AuthResponse,
)
async def refresh(user: User = Depends(get_current_user)) -> AuthResponse:
    jwt = _get_jwt()
    token = jwt.create_token(user)
    return AuthResponse(
        access_token=token,
        expires_in=jwt._expiry_minutes * 60,
        user_id=user.id,
        role=user.role,
    )


@router.get(
    "/users",
    summary="List all users (admin only)",
)
async def list_users(
    _admin: User = Depends(require_role(Role.admin)),
) -> list[dict]:
    store = _get_store()
    users = store.list_users()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "permissions": u.permissions,
            "is_active": u.is_active,
            "created_at": u.created_at,
            "last_login": u.last_login,
        }
        for u in users
    ]


@router.put(
    "/users/{user_id}/role",
    summary="Change a user's role (admin only)",
)
async def change_role(
    user_id: str,
    role: Role = Body(..., embed=True),
    _admin: User = Depends(require_role(Role.admin)),
) -> dict:
    store = _get_store()
    target = store.get_user_by_id(user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")

    new_perms = list(ROLE_PERMISSIONS.get(role, []))
    updated = store.update_user(user_id, role=role, permissions=new_perms)
    if updated is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": updated.id,
        "username": updated.username,
        "role": updated.role,
        "permissions": updated.permissions,
    }


@router.delete(
    "/users/{user_id}",
    summary="Delete a user (admin only)",
)
async def delete_user(
    user_id: str,
    _admin: User = Depends(require_role(Role.admin)),
) -> dict:
    store = _get_store()
    if not store.delete_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return {"deleted": user_id}
