# -*- coding: utf-8 -*-
"""Tests for the marketplace persona catalog and persona-based listing endpoints."""

from __future__ import annotations

import pytest

from prowlrbot.app.routers.marketplace import PERSONA_CATALOG


# ── PERSONA_CATALOG data structure ────────────────────────────────────────────


class TestPersonaCatalog:
    def test_catalog_is_nonempty(self):
        assert len(PERSONA_CATALOG) > 0

    def test_each_persona_has_required_fields(self):
        required = {"id", "label", "icon", "description"}
        for persona in PERSONA_CATALOG:
            missing = required - set(persona.keys())
            assert not missing, f"Persona {persona.get('id', '?')} missing fields: {missing}"

    def test_persona_ids_are_unique(self):
        ids = [p["id"] for p in PERSONA_CATALOG]
        assert len(ids) == len(set(ids)), "Persona IDs must be unique"

    def test_expected_personas_present(self):
        ids = {p["id"] for p in PERSONA_CATALOG}
        expected = {"parent", "business", "student", "creator", "freelancer", "developer", "everyone"}
        assert expected.issubset(ids)

    def test_all_personas_have_nonempty_values(self):
        for persona in PERSONA_CATALOG:
            assert persona["id"], "id must not be empty"
            assert persona["label"], "label must not be empty"
            assert persona["icon"], "icon must not be empty"
            assert persona["description"], "description must not be empty"

    def test_persona_labels_are_readable(self):
        """Labels should be human-readable (not just IDs)."""
        for persona in PERSONA_CATALOG:
            # Labels typically have spaces or capital letters
            assert persona["label"] != persona["id"], (
                f"Persona '{persona['id']}' label should differ from id"
            )

    def test_persona_count(self):
        assert len(PERSONA_CATALOG) == 7


# ── Persona filtering logic (unit-level, no HTTP) ────────────────────────────


class TestPersonaFiltering:
    """Test that persona-tag based filtering works at the store level.

    These tests import the store directly rather than going through FastAPI,
    keeping them fast and dependency-free.
    """

    @pytest.fixture()
    def store(self, tmp_path):
        from prowlrbot.marketplace.store import MarketplaceStore
        s = MarketplaceStore(db_path=tmp_path / "test.db")
        yield s
        s.close()

    def test_search_by_persona_returns_matching(self, store):
        from prowlrbot.marketplace.models import MarketplaceCategory, MarketplaceListing

        store.publish_listing(MarketplaceListing(
            author_id="a",
            title="Developer Tool",
            description="For devs",
            category=MarketplaceCategory.skills,
            persona_tags=["developer"],
        ))
        store.publish_listing(MarketplaceListing(
            author_id="a",
            title="Parent Helper",
            description="For parents",
            category=MarketplaceCategory.skills,
            persona_tags=["parent"],
        ))

        results = store.search_listings(persona="developer")
        assert len(results) == 1
        assert results[0].title == "Developer Tool"

    def test_search_by_persona_multiple_tags(self, store):
        from prowlrbot.marketplace.models import MarketplaceCategory, MarketplaceListing

        store.publish_listing(MarketplaceListing(
            author_id="a",
            title="Universal Tool",
            description="For everyone",
            category=MarketplaceCategory.skills,
            persona_tags=["developer", "freelancer", "everyone"],
        ))

        # Should match on any of the tags
        for persona in ["developer", "freelancer", "everyone"]:
            results = store.search_listings(persona=persona)
            assert len(results) == 1, f"Should match persona '{persona}'"

    def test_search_by_nonexistent_persona(self, store):
        from prowlrbot.marketplace.models import MarketplaceCategory, MarketplaceListing

        store.publish_listing(MarketplaceListing(
            author_id="a",
            title="Dev Only",
            description="Only for devs",
            category=MarketplaceCategory.skills,
            persona_tags=["developer"],
        ))

        results = store.search_listings(persona="astronaut")
        assert len(results) == 0

    def test_persona_with_difficulty_filter(self, store):
        from prowlrbot.marketplace.models import MarketplaceCategory, MarketplaceListing

        store.publish_listing(MarketplaceListing(
            author_id="a",
            title="Easy Dev",
            description="Beginner dev tool",
            category=MarketplaceCategory.skills,
            persona_tags=["developer"],
            difficulty="beginner",
        ))
        store.publish_listing(MarketplaceListing(
            author_id="a",
            title="Hard Dev",
            description="Advanced dev tool",
            category=MarketplaceCategory.skills,
            persona_tags=["developer"],
            difficulty="advanced",
        ))

        results = store.search_listings(persona="developer", difficulty="beginner")
        assert len(results) == 1
        assert results[0].title == "Easy Dev"


# ── FastAPI endpoint tests (optional, depends on httpx/TestClient) ────────────


class TestMarketplacePersonaEndpoints:
    """Test actual FastAPI endpoints via TestClient.

    These tests are skipped if fastapi[test] / httpx is not available.
    """

    @pytest.fixture()
    def client(self, tmp_path, monkeypatch):
        try:
            from fastapi import FastAPI
            from fastapi.testclient import TestClient
        except ImportError:
            pytest.skip("fastapi[test] not available")

        from prowlrbot.app.routers import marketplace as mp_module
        from prowlrbot.auth.middleware import get_current_user
        from prowlrbot.marketplace.store import MarketplaceStore

        # Use a temp store
        test_store = MarketplaceStore(db_path=tmp_path / "endpoint_test.db")
        monkeypatch.setattr(mp_module, "_store", test_store)

        app = FastAPI()
        # Override auth dependency so POST endpoints work without JWT
        app.dependency_overrides[get_current_user] = lambda: {"sub": "test-user", "role": "admin"}
        app.include_router(mp_module.router)

        yield TestClient(app)
        test_store.close()

    def test_list_personas_endpoint(self, client):
        resp = client.get("/marketplace/personas")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 7
        ids = {p["id"] for p in data}
        assert "developer" in ids
        assert "parent" in ids

    def test_list_categories_endpoint(self, client):
        resp = client.get("/marketplace/categories")
        assert resp.status_code == 200
        cats = resp.json()
        assert "skills" in cats
        assert "workflows" in cats

    def test_for_persona_endpoint_empty(self, client):
        resp = client.get("/marketplace/for/developer")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_for_persona_endpoint_with_data(self, client):
        from prowlrbot.marketplace.models import MarketplaceCategory

        # Publish a listing tagged for developer
        listing_data = {
            "author_id": "a1",
            "title": "Dev Automation",
            "description": "Automate dev tasks",
            "category": MarketplaceCategory.skills.value,
            "persona_tags": ["developer"],
        }
        resp = client.post("/marketplace/listings", json=listing_data)
        assert resp.status_code == 200

        # Query for developer persona
        resp = client.get("/marketplace/for/developer")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "Dev Automation"

    def test_for_persona_endpoint_no_cross_contamination(self, client):
        from prowlrbot.marketplace.models import MarketplaceCategory

        listing_data = {
            "author_id": "a1",
            "title": "Parent Tool",
            "description": "For parents",
            "category": MarketplaceCategory.skills.value,
            "persona_tags": ["parent"],
        }
        client.post("/marketplace/listings", json=listing_data)

        resp = client.get("/marketplace/for/developer")
        assert resp.status_code == 200
        assert len(resp.json()) == 0

    def test_search_with_difficulty_filter(self, client):
        from prowlrbot.marketplace.models import MarketplaceCategory

        for diff in ["beginner", "advanced"]:
            listing_data = {
                "author_id": "a1",
                "title": f"{diff.title()} Skill",
                "description": f"A {diff} skill",
                "category": MarketplaceCategory.skills.value,
                "difficulty": diff,
            }
            client.post("/marketplace/listings", json=listing_data)

        resp = client.get("/marketplace/listings", params={"difficulty": "beginner"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["difficulty"] == "beginner"
