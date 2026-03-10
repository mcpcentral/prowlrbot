# -*- coding: utf-8 -*-
"""Tests for SmartRouter — provider selection with scoring engine."""

from prowlrbot.providers.router import SmartRouter
from prowlrbot.providers.models import ProviderDefinition


def _make(id: str, cost_tier: str = "standard", env_var: str = "X") -> ProviderDefinition:
    return ProviderDefinition(id=id, name=id.title(), cost_tier=cost_tier, env_var=env_var)


def test_router_selects_best_scored_provider():
    providers = [
        _make("cheap", cost_tier="free"),
        _make("fast", cost_tier="premium"),
    ]
    router = SmartRouter(providers, health_status={"cheap": True, "fast": True})
    selected = router.select()
    # Free tier scores higher on cost (1.0 vs 0.2), default weights favor cost+avail
    assert selected is not None
    assert selected.id == "cheap"


def test_router_excludes_unhealthy():
    providers = [
        _make("healthy", cost_tier="standard"),
        _make("dead", cost_tier="free"),
    ]
    router = SmartRouter(providers, health_status={"healthy": True, "dead": False})
    selected = router.select()
    assert selected is not None
    assert selected.id == "healthy"


def test_router_returns_none_when_all_unhealthy():
    providers = [_make("a"), _make("b")]
    router = SmartRouter(providers, health_status={"a": False, "b": False})
    assert router.select() is None


def test_fallback_chain_ordered_by_score():
    providers = [
        _make("premium", cost_tier="premium"),
        _make("free", cost_tier="free"),
        _make("low", cost_tier="low"),
    ]
    health = {"premium": True, "free": True, "low": True}
    router = SmartRouter(providers, health_status=health)
    chain = router.get_fallback_chain()
    ids = [p.id for p in chain]
    # low scores highest (cost=0.24+perf=0.32+avail=0.3=0.86), then free (0.80), then premium (0.68)
    assert ids[0] == "low"
    assert ids[-1] == "premium"


def test_fallback_chain_excludes_unhealthy():
    providers = [_make("up"), _make("down")]
    router = SmartRouter(providers, health_status={"up": True, "down": False})
    chain = router.get_fallback_chain()
    assert len(chain) == 1
    assert chain[0].id == "up"


def test_custom_weights():
    providers = [
        _make("cheap", cost_tier="free"),
        _make("fast", cost_tier="premium"),
    ]
    # Heavily weight performance — premium tier has higher perf score
    router = SmartRouter(
        providers,
        health_status={"cheap": True, "fast": True},
        cost_weight=0.0,
        perf_weight=1.0,
        avail_weight=0.0,
    )
    selected = router.select()
    assert selected is not None
    assert selected.id == "fast"


def test_score_calculation():
    p = _make("test", cost_tier="standard")
    router = SmartRouter([p], health_status={"test": True})
    score = router.score(p)
    # cost=0.5*0.3 + perf=0.6*0.4 + avail=1.0*0.3 = 0.15 + 0.24 + 0.3 = 0.69
    assert abs(score - 0.69) < 0.01
