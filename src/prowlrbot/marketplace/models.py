# -*- coding: utf-8 -*-
"""Pydantic models for the ProwlrBot Marketplace."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from prowlrbot.compat import StrEnum
from typing import Optional

from pydantic import BaseModel, Field


class MarketplaceCategory(StrEnum):
    """The 12 marketplace listing categories."""

    skills = "skills"
    agents = "agents"
    prompts = "prompts"
    workflows = "workflows"
    integrations = "integrations"
    templates = "templates"
    datasets = "datasets"
    models = "models"
    plugins = "plugins"
    themes = "themes"
    channels = "channels"
    tools = "tools"


class ListingStatus(StrEnum):
    """Lifecycle status of a marketplace listing."""

    draft = "draft"
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"
    suspended = "suspended"


class PricingModel(StrEnum):
    """How a listing is priced."""

    free = "free"
    one_time = "one_time"
    subscription = "subscription"
    usage_based = "usage_based"


class MarketplaceListing(BaseModel):
    """A single item published to the marketplace."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    author_id: str
    title: str
    description: str
    category: MarketplaceCategory
    version: str = "1.0.0"
    pricing_model: PricingModel = PricingModel.free
    price: float = 0.0
    revenue_split: float = 0.70  # 70% to author
    downloads: int = 0
    rating: float = 0.0
    ratings_count: int = 0
    tags: list[str] = Field(default_factory=list)
    status: ListingStatus = ListingStatus.draft
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )


class ReviewEntry(BaseModel):
    """A user review on a marketplace listing."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    listing_id: str
    reviewer_id: str
    rating: int = Field(ge=1, le=5)
    comment: str = ""
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )


class InstallRecord(BaseModel):
    """Record of a user installing a marketplace listing."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    listing_id: str
    user_id: str
    version: str = "1.0.0"
    installed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )
