# -*- coding: utf-8 -*-
"""Smart provider routing with scoring engine and fallback chains."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from .models import ProviderDefinition

logger = logging.getLogger(__name__)

COST_SCORES: Dict[str, float] = {
    "free": 1.0,
    "low": 0.8,
    "standard": 0.5,
    "premium": 0.2,
}

PERF_SCORES: Dict[str, float] = {
    "free": 0.5,
    "low": 0.8,
    "standard": 0.6,
    "premium": 0.8,
}


class SmartRouter:
    """Select the best available provider using a weighted scoring model.

    Score = w_cost * cost_score + w_perf * perf_score + w_avail * avail_score

    Default weights: cost=0.3, perf=0.4, avail=0.3
    """

    def __init__(
        self,
        providers: List[ProviderDefinition],
        health_status: Optional[Dict[str, bool]] = None,
        cost_weight: float = 0.3,
        perf_weight: float = 0.4,
        avail_weight: float = 0.3,
    ) -> None:
        self.providers = providers
        self.health_status = health_status or {}
        self.cost_weight = cost_weight
        self.perf_weight = perf_weight
        self.avail_weight = avail_weight

    def score(self, provider: ProviderDefinition) -> float:
        """Calculate composite score for a provider."""
        cost = COST_SCORES.get(provider.cost_tier, 0.5)
        perf = PERF_SCORES.get(provider.cost_tier, 0.5)
        avail = 1.0 if self.health_status.get(provider.id, False) else 0.0
        return (
            self.cost_weight * cost
            + self.perf_weight * perf
            + self.avail_weight * avail
        )

    def select(self) -> Optional[ProviderDefinition]:
        """Select the highest-scoring healthy provider."""
        healthy = [
            p for p in self.providers if self.health_status.get(p.id, False)
        ]
        if not healthy:
            return None
        ranked = sorted(healthy, key=lambda p: self.score(p), reverse=True)
        selected = ranked[0]
        logger.info(
            "Router selected: %s (score=%.2f)",
            selected.name,
            self.score(selected),
        )
        return selected

    def get_fallback_chain(self) -> List[ProviderDefinition]:
        """Return healthy providers ordered by descending score."""
        healthy = [
            p for p in self.providers if self.health_status.get(p.id, False)
        ]
        return sorted(healthy, key=lambda p: self.score(p), reverse=True)
