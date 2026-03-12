# -*- coding: utf-8 -*-
"""Tests for prowlrbot.marketplace.models — v2 fields, enums, tiers, credits."""

from __future__ import annotations

import json

import pytest

from prowlrbot.marketplace.models import (
    CREDIT_EARN_RATES,
    CREDIT_PURCHASE_PACKS,
    CreditBalance,
    CreditTransaction,
    CreditTransactionType,
    Difficulty,
    InstallRecord,
    ListingStatus,
    MarketplaceCategory,
    MarketplaceListing,
    PRO_TIER_LIMITS,
    PREMIUM_CONTENT_PRICES,
    PricingModel,
    ProTier,
    ReviewEntry,
    TipRecord,
)


# ── Enum values ───────────────────────────────────────────────────────────────


class TestEnums:
    def test_marketplace_categories(self):
        expected = {"skills", "agents", "prompts", "mcp-servers", "themes", "workflows", "specs"}
        assert {c.value for c in MarketplaceCategory} == expected

    def test_listing_status_values(self):
        expected = {"draft", "pending_review", "approved", "rejected", "suspended"}
        assert {s.value for s in ListingStatus} == expected

    def test_pricing_model_values(self):
        expected = {"free", "one_time", "subscription", "usage_based"}
        assert {p.value for p in PricingModel} == expected

    def test_difficulty_values(self):
        expected = {"beginner", "intermediate", "advanced"}
        assert {d.value for d in Difficulty} == expected

    def test_pro_tier_values(self):
        expected = {"free", "starter", "pro", "team"}
        assert {t.value for t in ProTier} == expected

    def test_credit_transaction_type_earning(self):
        earning = {
            "monthly_grant", "publish_bonus", "download_milestone",
            "review_bonus", "tip_kickback", "referral", "bug_report", "purchased",
        }
        all_vals = {t.value for t in CreditTransactionType}
        assert earning.issubset(all_vals)

    def test_credit_transaction_type_spending(self):
        spending = {
            "listing_purchase", "workflow_unlock", "spec_generate",
            "insight_purchase", "blueprint_unlock",
        }
        all_vals = {t.value for t in CreditTransactionType}
        assert spending.issubset(all_vals)


# ── MarketplaceListing defaults ───────────────────────────────────────────────


class TestMarketplaceListingDefaults:
    def test_required_fields(self):
        listing = MarketplaceListing(
            author_id="user1",
            title="My Skill",
            description="A cool skill",
            category=MarketplaceCategory.skills,
        )
        assert listing.author_id == "user1"
        assert listing.title == "My Skill"
        assert listing.category == MarketplaceCategory.skills

    def test_v1_defaults(self):
        listing = MarketplaceListing(
            author_id="u", title="T", description="D",
            category=MarketplaceCategory.skills,
        )
        assert listing.version == "1.0.0"
        assert listing.pricing_model == PricingModel.free
        assert listing.price == 0.0
        assert listing.revenue_split == 0.70
        assert listing.downloads == 0
        assert listing.rating == 0.0
        assert listing.ratings_count == 0
        assert listing.tags == []
        assert listing.status == ListingStatus.draft
        assert listing.created_at  # non-empty
        assert listing.updated_at  # non-empty

    def test_v2_defaults(self):
        listing = MarketplaceListing(
            author_id="u", title="T", description="D",
            category=MarketplaceCategory.skills,
        )
        assert listing.difficulty == "beginner"
        assert listing.setup_time_minutes == 5
        assert listing.persona_tags == []
        assert listing.before_after == {}
        assert listing.skill_scan == {}
        assert listing.works_with == []
        assert listing.demo_url == ""
        assert listing.setup_steps == []
        assert listing.user_stories == []
        assert listing.hero_animation == ""

    def test_auto_id_is_unique(self):
        a = MarketplaceListing(
            author_id="u", title="A", description="D",
            category=MarketplaceCategory.skills,
        )
        b = MarketplaceListing(
            author_id="u", title="B", description="D",
            category=MarketplaceCategory.skills,
        )
        assert a.id != b.id

    def test_auto_id_is_hex(self):
        listing = MarketplaceListing(
            author_id="u", title="T", description="D",
            category=MarketplaceCategory.skills,
        )
        # uuid4().hex is 32 hex chars
        assert len(listing.id) == 32
        int(listing.id, 16)  # should not raise


# ── MarketplaceListing v2 fields ──────────────────────────────────────────────


class TestMarketplaceListingV2Fields:
    def test_difficulty_set(self):
        listing = MarketplaceListing(
            author_id="u", title="T", description="D",
            category=MarketplaceCategory.agents,
            difficulty="advanced",
        )
        assert listing.difficulty == "advanced"

    def test_setup_time_minutes(self):
        listing = MarketplaceListing(
            author_id="u", title="T", description="D",
            category=MarketplaceCategory.agents,
            setup_time_minutes=30,
        )
        assert listing.setup_time_minutes == 30

    def test_persona_tags(self):
        listing = MarketplaceListing(
            author_id="u", title="T", description="D",
            category=MarketplaceCategory.skills,
            persona_tags=["developer", "freelancer"],
        )
        assert listing.persona_tags == ["developer", "freelancer"]

    def test_before_after(self):
        ba = {"before": "Manual process", "after": "Automated"}
        listing = MarketplaceListing(
            author_id="u", title="T", description="D",
            category=MarketplaceCategory.workflows,
            before_after=ba,
        )
        assert listing.before_after == ba

    def test_skill_scan(self):
        scan = {"complexity": 3, "tools_used": ["shell", "browser"]}
        listing = MarketplaceListing(
            author_id="u", title="T", description="D",
            category=MarketplaceCategory.skills,
            skill_scan=scan,
        )
        assert listing.skill_scan == scan

    def test_works_with(self):
        listing = MarketplaceListing(
            author_id="u", title="T", description="D",
            category=MarketplaceCategory.agents,
            works_with=["slack", "github", "jira"],
        )
        assert listing.works_with == ["slack", "github", "jira"]

    def test_demo_url(self):
        listing = MarketplaceListing(
            author_id="u", title="T", description="D",
            category=MarketplaceCategory.themes,
            demo_url="https://demo.example.com",
        )
        assert listing.demo_url == "https://demo.example.com"

    def test_setup_steps(self):
        steps = [
            {"order": 1, "label": "Install", "command": "pip install prowlrbot"},
            {"order": 2, "label": "Configure", "command": "prowlr init"},
        ]
        listing = MarketplaceListing(
            author_id="u", title="T", description="D",
            category=MarketplaceCategory.skills,
            setup_steps=steps,
        )
        assert len(listing.setup_steps) == 2
        assert listing.setup_steps[0]["label"] == "Install"

    def test_user_stories(self):
        stories = [
            {"persona": "developer", "story": "As a developer, I want to automate deploys"},
        ]
        listing = MarketplaceListing(
            author_id="u", title="T", description="D",
            category=MarketplaceCategory.workflows,
            user_stories=stories,
        )
        assert listing.user_stories[0]["persona"] == "developer"

    def test_hero_animation(self):
        listing = MarketplaceListing(
            author_id="u", title="T", description="D",
            category=MarketplaceCategory.themes,
            hero_animation="lottie://animations/deploy.json",
        )
        assert listing.hero_animation == "lottie://animations/deploy.json"

    def test_full_v2_listing(self):
        listing = MarketplaceListing(
            author_id="author-1",
            title="Smart Deploy",
            description="One-click deployment workflow",
            category=MarketplaceCategory.workflows,
            version="2.0.0",
            pricing_model=PricingModel.one_time,
            price=9.99,
            tags=["deploy", "ci-cd"],
            difficulty="intermediate",
            setup_time_minutes=15,
            persona_tags=["developer", "freelancer"],
            before_after={"before": "Manual SSH", "after": "One click"},
            skill_scan={"tools": ["shell"], "complexity": 2},
            works_with=["github", "docker"],
            demo_url="https://demo.prowlrbot.com/smart-deploy",
            setup_steps=[{"order": 1, "label": "Clone", "command": "git clone ..."}],
            user_stories=[{"persona": "developer", "story": "Deploy in seconds"}],
            hero_animation="deploy-hero.lottie",
        )
        assert listing.category == MarketplaceCategory.workflows
        assert listing.pricing_model == PricingModel.one_time
        assert listing.price == 9.99
        assert len(listing.persona_tags) == 2
        assert listing.setup_time_minutes == 15


# ── MarketplaceListing serialization ──────────────────────────────────────────


class TestMarketplaceListingSerialization:
    def test_roundtrip(self):
        listing = MarketplaceListing(
            author_id="u1",
            title="Test",
            description="Desc",
            category=MarketplaceCategory.skills,
            persona_tags=["parent"],
            before_after={"before": "x", "after": "y"},
            works_with=["slack"],
        )
        data = json.loads(listing.model_dump_json())
        restored = MarketplaceListing(**data)
        assert restored.title == listing.title
        assert restored.persona_tags == ["parent"]
        assert restored.before_after == {"before": "x", "after": "y"}
        assert restored.works_with == ["slack"]

    def test_dict_export_contains_v2_fields(self):
        listing = MarketplaceListing(
            author_id="u", title="T", description="D",
            category=MarketplaceCategory.skills,
        )
        d = listing.model_dump()
        v2_keys = {
            "difficulty", "setup_time_minutes", "persona_tags", "before_after",
            "skill_scan", "works_with", "demo_url", "setup_steps",
            "user_stories", "hero_animation",
        }
        assert v2_keys.issubset(d.keys())


# ── PRO_TIER_LIMITS ──────────────────────────────────────────────────────────


class TestProTierLimits:
    def test_all_tiers_present(self):
        assert set(PRO_TIER_LIMITS.keys()) == {ProTier.free, ProTier.starter, ProTier.pro, ProTier.team}

    def test_unlimited_agents_all_tiers(self):
        for tier in ProTier:
            assert PRO_TIER_LIMITS[tier]["agents"] == -1, f"{tier} should have unlimited agents"

    def test_unlimited_teams_all_tiers(self):
        for tier in ProTier:
            assert PRO_TIER_LIMITS[tier]["teams"] == -1, f"{tier} should have unlimited teams"

    def test_pro_has_unlimited_workflows(self):
        assert PRO_TIER_LIMITS[ProTier.pro]["active_workflows"] == -1

    def test_team_has_unlimited_workflows(self):
        assert PRO_TIER_LIMITS[ProTier.team]["active_workflows"] == -1

    def test_free_has_limited_workflows(self):
        assert PRO_TIER_LIMITS[ProTier.free]["active_workflows"] == 5

    def test_free_cannot_publish_paid(self):
        assert PRO_TIER_LIMITS[ProTier.free]["marketplace_publish_paid"] is False

    def test_pro_can_publish_paid(self):
        assert PRO_TIER_LIMITS[ProTier.pro]["marketplace_publish_paid"] is True

    def test_credit_multiplier_increases_with_tier(self):
        tiers_ordered = [ProTier.free, ProTier.starter, ProTier.pro, ProTier.team]
        multipliers = [PRO_TIER_LIMITS[t]["credit_earn_multiplier"] for t in tiers_ordered]
        assert multipliers == sorted(multipliers)
        assert multipliers[0] < multipliers[-1]

    def test_monthly_credits_increase_with_tier(self):
        tiers_ordered = [ProTier.free, ProTier.starter, ProTier.pro, ProTier.team]
        credits = [PRO_TIER_LIMITS[t]["monthly_credits"] for t in tiers_ordered]
        assert credits == sorted(credits)


# ── ReviewEntry, InstallRecord, TipRecord ─────────────────────────────────────


class TestReviewEntry:
    def test_valid_review(self):
        review = ReviewEntry(listing_id="l1", reviewer_id="r1", rating=5, comment="Great!")
        assert review.rating == 5
        assert review.listing_id == "l1"

    def test_rating_bounds(self):
        with pytest.raises(Exception):
            ReviewEntry(listing_id="l1", reviewer_id="r1", rating=0)
        with pytest.raises(Exception):
            ReviewEntry(listing_id="l1", reviewer_id="r1", rating=6)


class TestInstallRecord:
    def test_defaults(self):
        record = InstallRecord(listing_id="l1", user_id="u1")
        assert record.version == "1.0.0"
        assert record.installed_at  # non-empty


class TestTipRecord:
    def test_valid_tip(self):
        tip = TipRecord(listing_id="l1", author_id="a1", tipper_id="t1", amount=5.0)
        assert tip.amount == 5.0
        assert tip.tipper_id == "t1"

    def test_zero_amount_rejected(self):
        with pytest.raises(Exception):
            TipRecord(listing_id="l1", author_id="a1", amount=0)

    def test_negative_amount_rejected(self):
        with pytest.raises(Exception):
            TipRecord(listing_id="l1", author_id="a1", amount=-1)

    def test_anonymous_default(self):
        tip = TipRecord(listing_id="l1", author_id="a1", amount=1.0)
        assert tip.tipper_id == "anonymous"


# ── CreditTransaction / CreditBalance ────────────────────────────────────────


class TestCreditTransaction:
    def test_creation(self):
        txn = CreditTransaction(
            user_id="u1",
            amount=100,
            transaction_type=CreditTransactionType.monthly_grant,
        )
        assert txn.user_id == "u1"
        assert txn.amount == 100
        assert txn.reference_id == ""

    def test_negative_amount_for_spending(self):
        txn = CreditTransaction(
            user_id="u1",
            amount=-50,
            transaction_type=CreditTransactionType.listing_purchase,
        )
        assert txn.amount == -50


class TestCreditBalance:
    def test_defaults(self):
        balance = CreditBalance(user_id="u1")
        assert balance.balance == 0
        assert balance.total_earned == 0
        assert balance.total_spent == 0
        assert balance.tier == ProTier.free


# ── Constants ─────────────────────────────────────────────────────────────────


class TestConstants:
    def test_premium_content_prices_all_positive(self):
        for key, price in PREMIUM_CONTENT_PRICES.items():
            assert price > 0, f"{key} should have a positive price"

    def test_credit_earn_rates_populated(self):
        assert len(CREDIT_EARN_RATES) > 0
        assert "publish_free_listing" in CREDIT_EARN_RATES

    def test_credit_purchase_packs_have_required_keys(self):
        for pack_name, pack in CREDIT_PURCHASE_PACKS.items():
            assert "credits" in pack, f"{pack_name} missing credits"
            assert "price" in pack, f"{pack_name} missing price"
            assert pack["credits"] > 0
            assert pack["price"] > 0
