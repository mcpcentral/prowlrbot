# -*- coding: utf-8 -*-
"""Pydantic models for the ProwlrBot Marketplace."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from prowlrbot.compat import StrEnum
from typing import Optional

from pydantic import BaseModel, Field


class MarketplaceCategory(StrEnum):
    """The 6 marketplace listing categories (aligned with mcpcentral/prowlr-marketplace)."""

    skills = "skills"
    agents = "agents"
    prompts = "prompts"
    mcp_servers = "mcp-servers"
    themes = "themes"
    workflows = "workflows"


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


class TipRecord(BaseModel):
    """A tip from a user to a listing author."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    listing_id: str
    author_id: str
    tipper_id: str = "anonymous"
    amount: float = Field(gt=0, description="Tip amount in USD")
    message: str = ""
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )


class ProTier(StrEnum):
    """Platform subscription tiers."""

    free = "free"
    starter = "starter"  # $5/mo
    pro = "pro"  # $15/mo
    team = "team"  # $29/mo


PRO_TIER_LIMITS = {
    ProTier.free: {
        "agents": 2,
        "teams": 1,
        "marketplace_publish": False,
        "monthly_credits": 50,
        "credit_earn_multiplier": 1,
    },
    ProTier.starter: {
        "agents": 3,
        "teams": 1,
        "marketplace_publish": False,
        "monthly_credits": 500,
        "credit_earn_multiplier": 2,
    },
    ProTier.pro: {
        "agents": 999,
        "teams": 5,
        "marketplace_publish": True,
        "monthly_credits": 2000,
        "credit_earn_multiplier": 3,
    },
    ProTier.team: {
        "agents": 999,
        "teams": 999,
        "marketplace_publish": True,
        "monthly_credits": 10000,
        "credit_earn_multiplier": 5,
    },
}


# ── Credits system ───────────────────────────────────────────────────────────


class CreditTransactionType(StrEnum):
    """How credits were earned or spent."""

    # Earning
    monthly_grant = "monthly_grant"
    publish_bonus = "publish_bonus"  # +100 for publishing a free listing
    download_milestone = "download_milestone"  # +50 per 10 downloads
    review_bonus = "review_bonus"  # +25 for 5-star review received
    tip_kickback = "tip_kickback"  # +10% of tip amount as credits
    referral = "referral"  # +200 for referring a user
    bug_report = "bug_report"  # +50 for confirmed bug report
    purchased = "purchased"  # bought with real money

    # Spending
    listing_purchase = "listing_purchase"  # spent on a marketplace item
    workflow_unlock = "workflow_unlock"  # unlock a premium workflow
    spec_generate = "spec_generate"  # generate a custom spec
    insight_purchase = "insight_purchase"  # buy an insight pack
    blueprint_unlock = "blueprint_unlock"  # unlock an agent blueprint


class CreditTransaction(BaseModel):
    """A single credit transaction (earn or spend)."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    user_id: str
    amount: int  # positive = earn, negative = spend
    transaction_type: CreditTransactionType
    reference_id: str = ""  # listing_id, tip_id, etc.
    description: str = ""
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )


class CreditBalance(BaseModel):
    """A user's credit balance snapshot."""

    user_id: str
    balance: int = 0
    total_earned: int = 0
    total_spent: int = 0
    tier: ProTier = ProTier.free


# ── Premium content pricing (in credits) ─────────────────────────────────────

PREMIUM_CONTENT_PRICES = {
    # Workflow Templates
    "workflow_basic": 50,
    "workflow_advanced": 200,
    "workflow_enterprise": 500,
    # Business Specs
    "spec_basic": 200,
    "spec_custom": 500,
    "spec_enterprise": 1000,
    # Insight Packs
    "insight_market": 100,
    "insight_competitor": 200,
    "insight_full": 300,
    # Roadmap Generators
    "roadmap_basic": 150,
    "roadmap_detailed": 300,
    "roadmap_enterprise": 500,
    # Agent Blueprints
    "blueprint_starter": 200,
    "blueprint_pro": 500,
    "blueprint_enterprise": 800,
    # Prompt Libraries
    "prompts_pack": 50,
    "prompts_collection": 100,
    "prompts_master": 200,
}

# Credits earned for platform actions
CREDIT_EARN_RATES = {
    "publish_free_listing": 100,
    "downloads_10": 50,
    "five_star_review": 25,
    "tip_kickback_pct": 0.10,  # 10% of tip amount
    "referral": 200,
    "bug_report_confirmed": 50,
}

# Credits purchasable with real money
CREDIT_PURCHASE_PACKS = {
    "small": {"credits": 500, "price": 4.99},
    "medium": {"credits": 1200, "price": 9.99},  # 20% bonus
    "large": {"credits": 3000, "price": 19.99},  # 50% bonus
    "mega": {"credits": 8000, "price": 39.99},  # 100% bonus
}
