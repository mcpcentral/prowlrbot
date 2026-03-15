# -*- coding: utf-8 -*-
"""Tests for agentverse guild→team bridge and battle credit awards."""

import importlib
import sys
import tempfile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from prowlrbot.agentverse.models import ArenaBattle, Guild
from prowlrbot.agentverse.world import AgentVerseWorld
from prowlrbot.dashboard.agent_teams import TeamStore
from prowlrbot.marketplace.models import CreditTransactionType
from prowlrbot.marketplace.store import MarketplaceStore


def _get_agentverse_module():
    """Return the agentverse router module (import or retrieve from cache)."""
    module_name = "prowlrbot.app.routers.agentverse"
    if module_name in sys.modules:
        return sys.modules[module_name]
    return importlib.import_module(module_name)


@pytest.fixture
def world():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    w = AgentVerseWorld(db_path=tmp.name)
    yield w
    w.close()


@pytest.fixture
def team_store():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    s = TeamStore(db_path=tmp.name)
    yield s
    s.close()


@pytest.fixture
def marketplace_store():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    s = MarketplaceStore(db_path=tmp.name)
    yield s
    s.close()


@pytest.fixture
def client(world, team_store, marketplace_store):
    mod = _get_agentverse_module()
    app = FastAPI()
    app.include_router(mod.router)

    original_world = mod._world
    original_get_team_store = mod._get_team_store
    original_get_marketplace_store = mod._get_marketplace_store

    mod._world = world
    mod._get_team_store = lambda: team_store
    mod._get_marketplace_store = lambda: marketplace_store

    try:
        yield TestClient(app)
    finally:
        mod._world = original_world
        mod._get_team_store = original_get_team_store
        mod._get_marketplace_store = original_get_marketplace_store


# ---------------------------------------------------------------------------
# Guild → Team bridge tests
# ---------------------------------------------------------------------------


def test_create_guild_also_creates_team(client, team_store):
    """Creating a guild via POST /agentverse/guilds should auto-create a linked team."""
    payload = {
        "id": "guild_testbridge",
        "name": "Bridge Guild",
        "description": "A test guild",
        "leader_id": "agent1",
        "members": [],
        "combined_xp": 0,
        "created_at": 0.0,
    }
    resp = client.post("/agentverse/guilds", json=payload)
    assert resp.status_code == 200
    guild = resp.json()
    assert guild["id"] == "guild_testbridge"

    # Team should now exist with same id
    team = team_store.get_team("guild_testbridge")
    assert team is not None
    assert team.name == "Bridge Guild"
    assert team.description == "A test guild"


def test_create_guild_team_name_matches(client, team_store):
    """The auto-created team name must equal the guild name."""
    payload = {
        "id": "guild_namematch",
        "name": "Alpha Squadron",
        "description": "Desc",
        "leader_id": "",
        "members": [],
        "combined_xp": 0,
        "created_at": 0.0,
    }
    client.post("/agentverse/guilds", json=payload)
    team = team_store.get_team("guild_namematch")
    assert team is not None
    assert team.name == "Alpha Squadron"


def test_get_guild_team_endpoint(client, team_store):
    """GET /agentverse/guilds/{guild_id}/team returns the linked team."""
    payload = {
        "id": "guild_gettest",
        "name": "Getters",
        "description": "for get test",
        "leader_id": "",
        "members": [],
        "combined_xp": 0,
        "created_at": 0.0,
    }
    client.post("/agentverse/guilds", json=payload)
    resp = client.get("/agentverse/guilds/guild_gettest/team")
    assert resp.status_code == 200
    team = resp.json()
    assert team["id"] == "guild_gettest"
    assert team["name"] == "Getters"


def test_get_guild_team_not_found(client):
    """GET /agentverse/guilds/{unknown}/team returns 404 when guild was never created."""
    resp = client.get("/agentverse/guilds/does_not_exist/team")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Battle credits tests
# ---------------------------------------------------------------------------


def test_complete_battle_awards_credits_to_winner(client, marketplace_store):
    """Completing a battle awards 50 credits to the winner."""
    # Create a battle first
    battle_payload = {
        "id": "battle_credits1",
        "challenger_id": "agent_chall",
        "defender_id": "agent_def",
        "benchmark": "general",
        "status": "waiting",
        "challenger_score": 0.0,
        "defender_score": 0.0,
        "winner_id": "",
        "created_at": 0.0,
    }
    resp = client.post("/agentverse/battles", json=battle_payload)
    assert resp.status_code == 200

    # Complete with challenger winning
    complete_payload = {
        "battle_id": "battle_credits1",
        "challenger_score": 90.0,
        "defender_score": 60.0,
    }
    resp = client.post("/agentverse/battles/complete", json=complete_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["winner"] == "agent_chall"
    assert data["credits_awarded"] == 50

    # Check credits in marketplace store
    balance = marketplace_store.get_balance("agent_chall")
    assert balance.balance == 50


def test_complete_battle_loser_gets_no_credits(
    client,
    marketplace_store,
    monkeypatch,
):
    """The losing agent does not receive credits."""
    monkeypatch.setenv("PROWLR_FREE_TIER_WELCOME_CREDITS", "0")
    battle_payload = {
        "id": "battle_credits2",
        "challenger_id": "agent_c2",
        "defender_id": "agent_d2",
        "benchmark": "general",
        "status": "waiting",
        "challenger_score": 0.0,
        "defender_score": 0.0,
        "winner_id": "",
        "created_at": 0.0,
    }
    client.post("/agentverse/battles", json=battle_payload)

    complete_payload = {
        "battle_id": "battle_credits2",
        "challenger_score": 40.0,
        "defender_score": 80.0,
    }
    client.post("/agentverse/battles/complete", json=complete_payload)

    # Defender wins; challenger should have no balance
    chall_balance = marketplace_store.get_balance("agent_c2")
    assert chall_balance.balance == 0

    def_balance = marketplace_store.get_balance("agent_d2")
    assert def_balance.balance == 50


def test_complete_battle_tie_no_credits(client, marketplace_store):
    """A tie (equal scores) means no winner, so no credits are awarded."""
    battle_payload = {
        "id": "battle_tie1",
        "challenger_id": "agent_tie_c",
        "defender_id": "agent_tie_d",
        "benchmark": "general",
        "status": "waiting",
        "challenger_score": 0.0,
        "defender_score": 0.0,
        "winner_id": "",
        "created_at": 0.0,
    }
    client.post("/agentverse/battles", json=battle_payload)

    complete_payload = {
        "battle_id": "battle_tie1",
        "challenger_score": 75.0,
        "defender_score": 75.0,
    }
    resp = client.post("/agentverse/battles/complete", json=complete_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["winner"] == ""
    assert data["credits_awarded"] == 0


def test_complete_battle_not_found(client):
    """Completing a nonexistent battle returns 404."""
    complete_payload = {
        "battle_id": "battle_ghost",
        "challenger_score": 10.0,
        "defender_score": 5.0,
    }
    resp = client.post("/agentverse/battles/complete", json=complete_payload)
    assert resp.status_code == 404


def test_battle_win_credit_transaction_type(client, marketplace_store):
    """The credit transaction for a battle win uses CreditTransactionType.earned."""
    battle_payload = {
        "id": "battle_txtype",
        "challenger_id": "agent_txc",
        "defender_id": "agent_txd",
        "benchmark": "general",
        "status": "waiting",
        "challenger_score": 0.0,
        "defender_score": 0.0,
        "winner_id": "",
        "created_at": 0.0,
    }
    client.post("/agentverse/battles", json=battle_payload)
    client.post(
        "/agentverse/battles/complete",
        json={
            "battle_id": "battle_txtype",
            "challenger_score": 100.0,
            "defender_score": 50.0,
        },
    )

    transactions = marketplace_store.get_transactions("agent_txc")
    assert len(transactions) == 1
    assert transactions[0].transaction_type == CreditTransactionType.earned
    assert transactions[0].description == "Won arena battle"
    assert transactions[0].amount == 50
