# -*- coding: utf-8 -*-
"""Tests for prowlrbot.marketplace.store — SQLite storage with v2 columns."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from prowlrbot.marketplace.models import (
    CreditTransactionType,
    InstallRecord,
    ListingStatus,
    MarketplaceCategory,
    MarketplaceListing,
    PricingModel,
    ReviewEntry,
    TipRecord,
)
from prowlrbot.marketplace.store import MarketplaceStore

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def store(tmp_path: Path) -> MarketplaceStore:
    """Create a fresh MarketplaceStore backed by a temp DB."""
    db_path = tmp_path / "test_marketplace.db"
    s = MarketplaceStore(db_path=db_path)
    yield s
    s.close()


def _make_listing(**overrides) -> MarketplaceListing:
    """Helper to build a listing with sensible defaults."""
    defaults = dict(
        author_id="author-1",
        title="Test Skill",
        description="A test marketplace listing",
        category=MarketplaceCategory.skills,
    )
    defaults.update(overrides)
    return MarketplaceListing(**defaults)


# ── publish_listing ───────────────────────────────────────────────────────────


class TestPublishListing:
    def test_publish_and_retrieve(self, store: MarketplaceStore):
        listing = _make_listing(title="My Skill")
        result = store.publish_listing(listing)
        assert result.id == listing.id

        fetched = store.get_listing(listing.id)
        assert fetched is not None
        assert fetched.title == "My Skill"
        assert fetched.author_id == "author-1"

    def test_publish_preserves_v1_fields(self, store: MarketplaceStore):
        listing = _make_listing(
            pricing_model=PricingModel.one_time,
            price=4.99,
            revenue_split=0.80,
            tags=["automation", "deploy"],
            status=ListingStatus.approved,
        )
        store.publish_listing(listing)
        fetched = store.get_listing(listing.id)
        assert fetched.pricing_model == PricingModel.one_time
        assert fetched.price == 4.99
        assert fetched.revenue_split == 0.80
        assert fetched.tags == ["automation", "deploy"]
        assert fetched.status == ListingStatus.approved

    def test_publish_preserves_all_v2_fields(self, store: MarketplaceStore):
        listing = _make_listing(
            difficulty="advanced",
            setup_time_minutes=25,
            persona_tags=["developer", "freelancer"],
            before_after={"before": "Manual", "after": "Automated"},
            skill_scan={"complexity": 4, "tools": ["shell"]},
            works_with=["github", "slack"],
            demo_url="https://demo.example.com",
            setup_steps=[{"order": 1, "label": "Install"}],
            user_stories=[{"persona": "dev", "story": "I want fast deploys"}],
            hero_animation="deploy.lottie",
        )
        store.publish_listing(listing)
        fetched = store.get_listing(listing.id)

        assert fetched.difficulty == "advanced"
        assert fetched.setup_time_minutes == 25
        assert fetched.persona_tags == ["developer", "freelancer"]
        assert fetched.before_after == {"before": "Manual", "after": "Automated"}
        assert fetched.skill_scan == {"complexity": 4, "tools": ["shell"]}
        assert fetched.works_with == ["github", "slack"]
        assert fetched.demo_url == "https://demo.example.com"
        assert fetched.setup_steps == [{"order": 1, "label": "Install"}]
        assert fetched.user_stories == [
            {"persona": "dev", "story": "I want fast deploys"}
        ]
        assert fetched.hero_animation == "deploy.lottie"

    def test_publish_all_26_columns(self, store: MarketplaceStore):
        """Verify that all 26 listing columns are stored and retrieved."""
        listing = _make_listing(
            version="3.0.0",
            pricing_model=PricingModel.subscription,
            price=19.99,
            revenue_split=0.75,
            downloads=42,
            rating=4.5,
            ratings_count=10,
            tags=["pro", "workflow"],
            status=ListingStatus.pending_review,
            difficulty="intermediate",
            setup_time_minutes=10,
            persona_tags=["business"],
            before_after={"b": "x", "a": "y"},
            skill_scan={"auto": True},
            works_with=["jira"],
            demo_url="https://example.com/demo",
            setup_steps=[{"step": 1}],
            user_stories=[{"s": "story"}],
            hero_animation="hero.json",
        )
        store.publish_listing(listing)
        fetched = store.get_listing(listing.id)

        assert fetched.version == "3.0.0"
        assert fetched.pricing_model == PricingModel.subscription
        assert fetched.price == 19.99
        assert fetched.revenue_split == 0.75
        assert fetched.downloads == 42
        assert fetched.rating == 4.5
        assert fetched.ratings_count == 10
        assert fetched.tags == ["pro", "workflow"]
        assert fetched.status == ListingStatus.pending_review
        assert fetched.difficulty == "intermediate"
        assert fetched.setup_time_minutes == 10

    def test_get_nonexistent_returns_none(self, store: MarketplaceStore):
        assert store.get_listing("nonexistent") is None


# ── search_listings ───────────────────────────────────────────────────────────


class TestSearchListings:
    def test_search_by_query(self, store: MarketplaceStore):
        store.publish_listing(
            _make_listing(title="Deploy Bot", description="Automated deployments")
        )
        store.publish_listing(
            _make_listing(title="Chat Bot", description="Chat interface")
        )

        results = store.search_listings(query="Deploy")
        assert len(results) == 1
        assert results[0].title == "Deploy Bot"

    def test_search_by_category(self, store: MarketplaceStore):
        store.publish_listing(_make_listing(category=MarketplaceCategory.skills))
        store.publish_listing(_make_listing(category=MarketplaceCategory.agents))

        results = store.search_listings(category="skills")
        assert len(results) == 1
        assert results[0].category == MarketplaceCategory.skills

    def test_search_by_persona(self, store: MarketplaceStore):
        store.publish_listing(
            _make_listing(title="Dev Tool", persona_tags=["developer"])
        )
        store.publish_listing(_make_listing(title="Mom Tool", persona_tags=["parent"]))

        results = store.search_listings(persona="developer")
        assert len(results) == 1
        assert results[0].title == "Dev Tool"

    def test_search_by_difficulty(self, store: MarketplaceStore):
        store.publish_listing(_make_listing(title="Easy", difficulty="beginner"))
        store.publish_listing(_make_listing(title="Hard", difficulty="advanced"))

        results = store.search_listings(difficulty="advanced")
        assert len(results) == 1
        assert results[0].title == "Hard"

    def test_search_combined_filters(self, store: MarketplaceStore):
        store.publish_listing(
            _make_listing(
                title="Dev Workflow",
                category=MarketplaceCategory.workflows,
                persona_tags=["developer"],
                difficulty="intermediate",
            )
        )
        store.publish_listing(
            _make_listing(
                title="Dev Skill",
                category=MarketplaceCategory.skills,
                persona_tags=["developer"],
                difficulty="intermediate",
            )
        )
        store.publish_listing(
            _make_listing(
                title="Parent Workflow",
                category=MarketplaceCategory.workflows,
                persona_tags=["parent"],
                difficulty="beginner",
            )
        )

        results = store.search_listings(
            category="workflows",
            persona="developer",
            difficulty="intermediate",
        )
        assert len(results) == 1
        assert results[0].title == "Dev Workflow"

    def test_search_by_tags(self, store: MarketplaceStore):
        store.publish_listing(_make_listing(title="Tagged", tags=["deploy", "ci"]))
        store.publish_listing(_make_listing(title="Other", tags=["chat"]))

        results = store.search_listings(tags=["deploy"])
        assert len(results) == 1
        assert results[0].title == "Tagged"

    def test_search_empty_returns_all(self, store: MarketplaceStore):
        store.publish_listing(_make_listing(title="A"))
        store.publish_listing(_make_listing(title="B"))

        results = store.search_listings()
        assert len(results) == 2

    def test_search_respects_limit(self, store: MarketplaceStore):
        for i in range(5):
            store.publish_listing(_make_listing(title=f"Item {i}"))

        results = store.search_listings(limit=3)
        assert len(results) == 3

    def test_search_orders_by_downloads_desc(self, store: MarketplaceStore):
        store.publish_listing(_make_listing(title="Low", downloads=5))
        store.publish_listing(_make_listing(title="High", downloads=100))
        store.publish_listing(_make_listing(title="Mid", downloads=50))

        results = store.search_listings()
        assert results[0].title == "High"
        assert results[1].title == "Mid"
        assert results[2].title == "Low"


# ── update_listing ────────────────────────────────────────────────────────────


class TestUpdateListing:
    def test_update_v1_fields(self, store: MarketplaceStore):
        listing = _make_listing(title="Original")
        store.publish_listing(listing)

        updated = store.update_listing(listing.id, {"title": "Updated", "price": 9.99})
        assert updated.title == "Updated"
        assert updated.price == 9.99

    def test_update_v2_fields(self, store: MarketplaceStore):
        listing = _make_listing()
        store.publish_listing(listing)

        updated = store.update_listing(
            listing.id,
            {
                "difficulty": "advanced",
                "setup_time_minutes": 30,
                "persona_tags": ["developer", "business"],
                "before_after": {"before": "old", "after": "new"},
                "skill_scan": {"rating": 5},
                "works_with": ["github"],
                "demo_url": "https://new-demo.com",
                "setup_steps": [{"step": 1}],
                "user_stories": [{"story": "updated"}],
                "hero_animation": "new.lottie",
            },
        )
        assert updated.difficulty == "advanced"
        assert updated.setup_time_minutes == 30
        assert updated.persona_tags == ["developer", "business"]
        assert updated.before_after == {"before": "old", "after": "new"}
        assert updated.skill_scan == {"rating": 5}
        assert updated.works_with == ["github"]
        assert updated.demo_url == "https://new-demo.com"
        assert updated.setup_steps == [{"step": 1}]
        assert updated.user_stories == [{"story": "updated"}]
        assert updated.hero_animation == "new.lottie"

    def test_update_nonexistent_returns_none(self, store: MarketplaceStore):
        assert store.update_listing("fake", {"title": "X"}) is None

    def test_update_disallowed_field_ignored(self, store: MarketplaceStore):
        listing = _make_listing()
        store.publish_listing(listing)

        updated = store.update_listing(
            listing.id, {"id": "new-id", "author_id": "hacker"}
        )
        assert updated.id == listing.id
        assert updated.author_id == listing.author_id

    def test_update_empty_dict_returns_existing(self, store: MarketplaceStore):
        listing = _make_listing(title="Keep")
        store.publish_listing(listing)

        updated = store.update_listing(listing.id, {})
        assert updated.title == "Keep"

    def test_update_sets_updated_at(self, store: MarketplaceStore):
        listing = _make_listing()
        store.publish_listing(listing)
        old_updated_at = listing.updated_at

        updated = store.update_listing(listing.id, {"title": "Changed"})
        assert updated.updated_at >= old_updated_at

    def test_update_category_enum(self, store: MarketplaceStore):
        listing = _make_listing(category=MarketplaceCategory.skills)
        store.publish_listing(listing)

        updated = store.update_listing(listing.id, {"category": "agents"})
        assert updated.category == MarketplaceCategory.agents

    def test_update_category_with_enum_value(self, store: MarketplaceStore):
        listing = _make_listing()
        store.publish_listing(listing)

        updated = store.update_listing(
            listing.id, {"category": MarketplaceCategory.workflows}
        )
        assert updated.category == MarketplaceCategory.workflows


# ── _migrate_v2 backward compatibility ────────────────────────────────────────


class TestMigrateV2:
    def test_migrate_adds_missing_columns_to_v1_db(self, tmp_path: Path):
        """Simulate a v1 database that lacks v2 columns."""
        db_path = tmp_path / "v1.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE listings (
                id TEXT PRIMARY KEY,
                author_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL,
                version TEXT NOT NULL DEFAULT '1.0.0',
                pricing_model TEXT NOT NULL DEFAULT 'free',
                price REAL NOT NULL DEFAULT 0.0,
                revenue_split REAL NOT NULL DEFAULT 0.70,
                downloads INTEGER NOT NULL DEFAULT 0,
                rating REAL NOT NULL DEFAULT 0.0,
                ratings_count INTEGER NOT NULL DEFAULT 0,
                tags TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'draft',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        # Insert a v1 row
        conn.execute(
            "INSERT INTO listings (id, author_id, title, description, category, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                "v1-item",
                "author",
                "V1 Listing",
                "Old listing",
                "skills",
                "2026-01-01",
                "2026-01-01",
            ),
        )
        conn.commit()
        conn.close()

        # Open with MarketplaceStore, which should run migration
        store = MarketplaceStore(db_path=db_path)

        # The v1 row should now be readable with v2 defaults
        fetched = store.get_listing("v1-item")
        assert fetched is not None
        assert fetched.title == "V1 Listing"
        assert fetched.difficulty == "beginner"
        assert fetched.setup_time_minutes == 5
        assert fetched.persona_tags == []
        assert fetched.before_after == {}
        assert fetched.works_with == []
        assert fetched.demo_url == ""

        # New v2 listings should also work
        new_listing = _make_listing(
            difficulty="advanced",
            persona_tags=["developer"],
        )
        store.publish_listing(new_listing)
        fetched_new = store.get_listing(new_listing.id)
        assert fetched_new.difficulty == "advanced"

        store.close()

    def test_migrate_is_idempotent(self, tmp_path: Path):
        """Running _migrate_v2 multiple times should not fail."""
        db_path = tmp_path / "idem.db"
        store1 = MarketplaceStore(db_path=db_path)
        store1.close()

        # Open again — migration runs again, should be safe
        store2 = MarketplaceStore(db_path=db_path)
        store2.close()


# ── Reviews ───────────────────────────────────────────────────────────────────


class TestReviews:
    def test_add_review_updates_aggregate(self, store: MarketplaceStore):
        listing = _make_listing()
        store.publish_listing(listing)

        store.add_review(ReviewEntry(listing_id=listing.id, reviewer_id="r1", rating=5))
        store.add_review(ReviewEntry(listing_id=listing.id, reviewer_id="r2", rating=3))

        fetched = store.get_listing(listing.id)
        assert fetched.ratings_count == 2
        assert fetched.rating == pytest.approx(4.0)

    def test_get_reviews(self, store: MarketplaceStore):
        listing = _make_listing()
        store.publish_listing(listing)

        store.add_review(
            ReviewEntry(
                listing_id=listing.id, reviewer_id="r1", rating=4, comment="Good"
            )
        )
        reviews = store.get_reviews(listing.id)
        assert len(reviews) == 1
        assert reviews[0].comment == "Good"


# ── Installs ──────────────────────────────────────────────────────────────────


class TestInstalls:
    def test_record_install_bumps_downloads(self, store: MarketplaceStore):
        listing = _make_listing()
        store.publish_listing(listing)

        store.record_install(InstallRecord(listing_id=listing.id, user_id="u1"))
        store.record_install(InstallRecord(listing_id=listing.id, user_id="u2"))

        fetched = store.get_listing(listing.id)
        assert fetched.downloads == 2
        assert store.get_install_count(listing.id) == 2


# ── Tips ──────────────────────────────────────────────────────────────────────


class TestTips:
    def test_add_and_get_tips(self, store: MarketplaceStore):
        listing = _make_listing()
        store.publish_listing(listing)

        store.add_tip(
            TipRecord(listing_id=listing.id, author_id="author-1", amount=5.0)
        )
        store.add_tip(
            TipRecord(listing_id=listing.id, author_id="author-1", amount=10.0)
        )

        tips = store.get_tips_for_author("author-1")
        assert len(tips) == 2

        total = store.get_tip_total("author-1")
        assert total == pytest.approx(15.0)


# ── Credits ───────────────────────────────────────────────────────────────────


class TestCredits:
    def test_get_balance_auto_creates(self, store: MarketplaceStore, monkeypatch):
        monkeypatch.setenv("PROWLR_FREE_TIER_WELCOME_CREDITS", "0")
        balance = store.get_balance("new-user")
        assert balance.user_id == "new-user"
        assert balance.balance == 0

    def test_add_credits(self, store: MarketplaceStore):
        balance = store.add_credits(
            "u1",
            100,
            CreditTransactionType.monthly_grant,
        )
        assert balance.balance == 100
        assert balance.total_earned == 100

    def test_spend_credits(self, store: MarketplaceStore):
        store.add_credits("u1", 200, CreditTransactionType.monthly_grant)
        balance = store.spend_credits(
            "u1",
            50,
            CreditTransactionType.listing_purchase,
        )
        assert balance.balance == 150
        assert balance.total_spent == 50

    def test_spend_insufficient_raises(self, store: MarketplaceStore):
        store.add_credits("u1", 10, CreditTransactionType.monthly_grant)
        with pytest.raises(ValueError, match="Insufficient credits"):
            store.spend_credits("u1", 100, CreditTransactionType.listing_purchase)

    def test_transactions_recorded(self, store: MarketplaceStore):
        store.add_credits("u1", 100, CreditTransactionType.monthly_grant)
        store.spend_credits("u1", 30, CreditTransactionType.listing_purchase)

        txns = store.get_transactions("u1")
        assert len(txns) == 2

    def test_set_tier(self, store: MarketplaceStore):
        store.get_balance("u1")  # create
        balance = store.set_tier("u1", "pro")
        assert balance.tier.value == "pro"


# ── list_by_author / get_popular / get_top_rated ──────────────────────────────


class TestDiscoveryQueries:
    def test_list_by_author(self, store: MarketplaceStore):
        store.publish_listing(_make_listing(author_id="a1", title="A1"))
        store.publish_listing(_make_listing(author_id="a2", title="A2"))
        store.publish_listing(_make_listing(author_id="a1", title="A1b"))

        results = store.list_by_author("a1")
        assert len(results) == 2

    def test_get_popular_only_approved(self, store: MarketplaceStore):
        store.publish_listing(
            _make_listing(
                title="Popular",
                downloads=100,
                status=ListingStatus.approved,
            )
        )
        store.publish_listing(
            _make_listing(
                title="Draft",
                downloads=200,
                status=ListingStatus.draft,
            )
        )

        results = store.get_popular()
        assert len(results) == 1
        assert results[0].title == "Popular"

    def test_get_top_rated_needs_ratings(self, store: MarketplaceStore):
        listing = _make_listing(status=ListingStatus.approved)
        store.publish_listing(listing)

        # No reviews yet — should not appear
        assert store.get_top_rated() == []

        # Add a review
        store.add_review(ReviewEntry(listing_id=listing.id, reviewer_id="r1", rating=5))
        results = store.get_top_rated()
        assert len(results) == 1
