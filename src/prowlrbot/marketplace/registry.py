# -*- coding: utf-8 -*-
"""Fetch and sync the marketplace registry from ProwlrBot/prowlr-marketplace on GitHub."""

from __future__ import annotations

import json
import logging
from base64 import b64decode
from pathlib import Path
from typing import Optional

import httpx

from .models import ListingStatus, MarketplaceCategory, MarketplaceListing, PricingModel

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

REGISTRY_OWNER = "ProwlrBot"
REGISTRY_REPO = "prowlr-marketplace"
GITHUB_API = "https://api.github.com"
GITHUB_RAW = "https://raw.githubusercontent.com"

# Map prowlr-marketplace directory names → MarketplaceCategory values
CATEGORY_DIR_MAP: dict[str, str] = {
    "skills": "skills",
    "agents": "agents",
    "prompts": "prompts",
    "mcp-servers": "mcp-servers",
    "themes": "themes",
    "workflows": "workflows",
    "consumer": "consumer",
    "specs": "specs",
}

# index.json URL — single request replaces N+1 GitHub API directory crawl
INDEX_JSON_URL = (
    f"{GITHUB_RAW}/ProwlrBot/prowlr-marketplace/main/index.json"
)

# ── Ecosystem repos ──────────────────────────────────────────────────────────

ECOSYSTEM_REPOS = {
    "prowlrbot": {
        "owner": "ProwlrBot",
        "description": "Core platform — autonomous AI agent for monitoring, automation, multi-channel comms",
        "url": "https://github.com/ProwlrBot/prowlrbot",
    },
    "prowlr-marketplace": {
        "owner": "ProwlrBot",
        "description": "Community marketplace — skills, agents, prompts, MCP servers, themes, workflows",
        "url": "https://github.com/ProwlrBot/prowlr-marketplace",
    },
    "agentverse": {
        "owner": "ProwlrBot",
        "description": "Virtual agent world — zones, XP, guilds, tournaments",
        "url": "https://github.com/ProwlrBot/agentverse",
    },
    "roar-protocol": {
        "owner": "ProwlrBot",
        "description": "5-layer agent interop specification (ROAR)",
        "url": "https://github.com/ProwlrBot/roar-protocol",
    },
    "prowlr-docs": {
        "owner": "ProwlrBot",
        "description": "Official ProwlrBot documentation (en + zh)",
        "url": "https://github.com/ProwlrBot/prowlr-docs",
    },
}


# ── Registry client ──────────────────────────────────────────────────────────


class RegistryClient:
    """Fetches listing manifests from the ProwlrBot/prowlr-marketplace GitHub repo."""

    def __init__(self, token: Optional[str] = None) -> None:
        headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.Client(
            base_url=GITHUB_API,
            headers=headers,
            timeout=30.0,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "RegistryClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    # ── Public API ───────────────────────────────────────────────────────

    def fetch_categories(self) -> list[str]:
        """List available category directories in the repo."""
        resp = self._client.get(f"/repos/{REGISTRY_OWNER}/{REGISTRY_REPO}/contents")
        if resp.status_code != 200:
            logger.warning("Failed to fetch repo contents: %s", resp.status_code)
            return []

        entries = resp.json()
        return [
            e["name"]
            for e in entries
            if e["type"] == "dir" and e["name"] in CATEGORY_DIR_MAP
        ]

    def fetch_category_listings(self, category: str) -> list[dict]:
        """Fetch all listing manifests within a category directory."""
        resp = self._client.get(
            f"/repos/{REGISTRY_OWNER}/{REGISTRY_REPO}/contents/{category}"
        )
        if resp.status_code != 200:
            logger.warning("Failed to list %s: %s", category, resp.status_code)
            return []

        entries = resp.json()
        listings: list[dict] = []

        for entry in entries:
            if entry["type"] != "dir":
                continue
            manifest = self._fetch_manifest(category, entry["name"])
            if manifest:
                manifest["_dir_name"] = entry["name"]
                manifest["_category"] = category
                listings.append(manifest)

        return listings

    def fetch_all_listings(self) -> list[dict]:
        """Fetch every listing — prefers index.json (1 request) over directory crawl."""
        index_listings = self._fetch_via_index()
        if index_listings is not None:
            logger.info("Loaded %d listings from index.json", len(index_listings))
            return index_listings
        logger.info("index.json unavailable, falling back to directory crawl")
        all_listings: list[dict] = []
        for category in self.fetch_categories():
            all_listings.extend(self.fetch_category_listings(category))
        return all_listings

    def _fetch_via_index(self) -> list[dict] | None:
        """Fetch the pre-built index.json (single request, CDN-cached).

        Returns a normalised list of raw manifest dicts, or None if unavailable.
        Each entry is augmented with ``_category`` and ``_dir_name`` keys so
        ``sync_registry`` can process them identically to the crawl path.
        """
        try:
            raw_client = httpx.Client(timeout=15.0)
            resp = raw_client.get(INDEX_JSON_URL)
            raw_client.close()
        except httpx.RequestError as exc:
            logger.warning("Could not reach index.json: %s", exc)
            return None

        if resp.status_code != 200:
            logger.warning("index.json returned %s", resp.status_code)
            return None

        try:
            index = resp.json()
        except Exception as exc:
            logger.warning("index.json parse error: %s", exc)
            return None

        listings = index.get("listings", [])
        if not listings:
            return None

        # Normalise: add _category and _dir_name so sync_registry works unchanged
        result = []
        for entry in listings:
            entry = dict(entry)
            entry["_category"] = entry.get("category", "skills")
            entry["_dir_name"] = entry.get("slug", entry.get("id", "unknown"))
            result.append(entry)
        return result

    # ── Private helpers ──────────────────────────────────────────────────

    def _fetch_manifest(self, category: str, name: str) -> Optional[dict]:
        """Fetch manifest.json (or package.json / SKILL.md) for a single listing."""
        for filename in ("manifest.json", "package.json"):
            resp = self._client.get(
                f"/repos/{REGISTRY_OWNER}/{REGISTRY_REPO}/contents/{category}/{name}/{filename}"
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("content", "")
                if content:
                    try:
                        decoded = b64decode(content).decode("utf-8")
                        return json.loads(decoded)
                    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                        logger.warning(
                            "Bad manifest %s/%s/%s: %s", category, name, filename, exc
                        )
        return None


# ── Sync to local store ──────────────────────────────────────────────────────


def sync_registry(
    store: "MarketplaceStore",  # noqa: F821
    token: Optional[str] = None,
) -> tuple[int, int, int]:
    """Pull all listings from GitHub and upsert into the local store.

    Returns (added, updated, total) counts.
    """
    from .store import MarketplaceStore as _Store  # avoid circular

    added = 0
    updated = 0

    with RegistryClient(token=token) as client:
        raw_listings = client.fetch_all_listings()

    for raw in raw_listings:
        category_str = CATEGORY_DIR_MAP.get(raw.get("_category", ""), "skills")
        dir_name = raw.get("_dir_name", "unknown")

        # Normalise the manifest into a MarketplaceListing
        listing_id = raw.get("id", f"{category_str}-{dir_name}")
        title = raw.get("title", raw.get("name", dir_name))
        description = raw.get("description", "")
        version = raw.get("version", "1.0.0")
        author = raw.get("author", raw.get("author_id", "unknown"))
        tags = raw.get("tags", raw.get("keywords", []))
        pricing = raw.get("pricing_model", "free")
        price = float(raw.get("price", 0))

        author_str = (
            author if isinstance(author, str) else author.get("name", "unknown")
        )
        is_official = author_str.lower() in ("prowlrbot", "prowlr", "prowlrbot-team")

        try:
            cat = MarketplaceCategory(category_str)
        except ValueError:
            cat = MarketplaceCategory.skills

        existing = store.get_listing(listing_id)
        if existing:
            store.update_listing(
                listing_id,
                {
                    "title": title,
                    "description": description,
                    "version": version,
                    "tags": tags,
                    "category": cat.value,
                    "author_name": author_str,
                    "source_repo": raw.get("source_repo", raw.get("repository", "")),
                    "license": raw.get("license", "MIT"),
                },
            )
            updated += 1
        else:
            try:
                pm = PricingModel(pricing)
            except ValueError:
                logger.warning(
                    "Unknown pricing model '%s' for %s, defaulting to free",
                    pricing,
                    dir_name,
                )
                pm = PricingModel.free

            listing = MarketplaceListing(
                id=listing_id,
                author_id=author_str,
                title=title,
                description=description,
                category=cat,
                version=version,
                pricing_model=pm,
                price=price,
                tags=tags if isinstance(tags, list) else [],
                status=ListingStatus.approved,
                trust_tier="official" if is_official else "verified",
                author_name=author_str,
                source_repo=raw.get("source_repo", raw.get("repository", "")),
                license=raw.get("license", "MIT"),
            )
            store.publish_listing(listing)
            added += 1

    total = len(raw_listings)
    return added, updated, total


def get_ecosystem_repos() -> dict[str, dict]:
    """Return metadata for all ProwlrBot ecosystem repos."""
    return dict(ECOSYSTEM_REPOS)
