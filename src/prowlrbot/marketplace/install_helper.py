# -*- coding: utf-8 -*-
"""Materialize marketplace installs: write manifest to disk and, for skills, fetch and enable."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from ..constant import CUSTOMIZED_SKILLS_DIR, WORKING_DIR
from .models import MarketplaceCategory, MarketplaceListing
from .registry import RegistryClient

logger = logging.getLogger(__name__)


def materialize_install(listing: MarketplaceListing) -> None:
    """Write install manifest to WORKING_DIR/marketplace/<id> and, for skills, fetch content and enable."""
    install_dir = (
        WORKING_DIR
        / "marketplace"
        / (listing.id[:12] if len(listing.id) > 12 else listing.id)
    )
    install_dir.mkdir(parents=True, exist_ok=True)
    try:
        manifest_path = install_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(listing.model_dump(mode="json"), indent=2, default=str),
            encoding="utf-8",
        )
        logger.debug("Wrote marketplace manifest to %s", manifest_path)
    except Exception as e:
        logger.warning("Could not write marketplace manifest: %s", e)

    if listing.category != MarketplaceCategory.skills:
        return

    try:
        with RegistryClient() as client:
            files = client.fetch_listing_files(
                listing.category.value,
                listing.id,
            )
        if not files:
            logger.debug("No files fetched for skill listing %s", listing.id)
            return
        from ..agents.skills_manager import SkillService

        skill_dir = CUSTOMIZED_SKILLS_DIR / listing.id
        skill_dir.mkdir(parents=True, exist_ok=True)
        for rel_path, content in files.items():
            out_path = skill_dir / rel_path
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(content, encoding="utf-8")
        SkillService.enable_skill(listing.id, force=True)
        logger.info("Installed and enabled skill %s", listing.id)
    except Exception as e:
        logger.warning("Could not fetch/enable skill %s: %s", listing.id, e)
