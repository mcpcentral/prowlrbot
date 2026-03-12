# -*- coding: utf-8 -*-
"""Seed marketplace with launch bundles and official listings."""

from __future__ import annotations

import logging

from .models import Bundle
from .store import MarketplaceStore

logger = logging.getLogger(__name__)

LAUNCH_BUNDLES = [
    Bundle(
        id="security-starter",
        name="Security Starter",
        description="OWASP audit, JWT review, dependency scan",
        emoji="shield",
        color="#ef4444",
        listing_ids=[
            "security-auditor",
            "api-security-audit",
            "dependency-scan",
            "jwt-review",
            "owasp-check",
        ],
    ),
    Bundle(
        id="full-stack-dev",
        name="Full-Stack Dev",
        description="API design, frontend, testing, CI/CD, deploy",
        emoji="rocket",
        color="#3b82f6",
        listing_ids=[
            "frontend-design",
            "backend-architect",
            "database-designer",
            "test-automator",
            "ci-cd-builder",
            "deployment-engineer",
            "code-reviewer",
            "api-documenter",
        ],
    ),
    Bundle(
        id="data-analytics",
        name="Data & Analytics",
        description="SQL, BigQuery, visualization, RAG pipeline",
        emoji="chart",
        color="#8b5cf6",
        listing_ids=[
            "sql-expert",
            "data-scientist",
            "rag-architect",
            "data-engineer",
            "ml-engineer",
            "visualization",
        ],
    ),
    Bundle(
        id="document-pro",
        name="Document Pro",
        description="PDF, DOCX, PPTX, XLSX processing suite",
        emoji="memo",
        color="#f59e0b",
        listing_ids=["pdf", "docx", "pptx", "xlsx"],
    ),
]


def seed_bundles(store: MarketplaceStore) -> int:
    """Seed launch bundles. Returns number of bundles created."""
    created = 0
    for bundle in LAUNCH_BUNDLES:
        existing = store.get_bundle(bundle.id)
        if existing is None:
            store.create_bundle(bundle)
            created += 1
            logger.info("Created bundle: %s", bundle.name)
    return created
