# -*- coding: utf-8 -*-
"""Marketplace CLI commands — search, install, publish, list, update, tip."""

from __future__ import annotations

import json
from pathlib import Path

import click

from ..constant import WORKING_DIR
from ..marketplace.models import (
    InstallRecord,
    MarketplaceCategory,
    MarketplaceListing,
    PricingModel,
    ReviewEntry,
    TipRecord,
)
from ..marketplace.store import MarketplaceStore


def _get_store() -> MarketplaceStore:
    return MarketplaceStore(db_path=WORKING_DIR / "marketplace.db")


def _format_price(listing: MarketplaceListing) -> str:
    """Format pricing info for display."""
    if listing.pricing_model == PricingModel.free:
        return "FREE"
    if listing.pricing_model == PricingModel.one_time:
        return f"${listing.price:.2f}"
    if listing.pricing_model == PricingModel.subscription:
        return f"${listing.price:.2f}/mo"
    return f"${listing.price:.2f} (usage)"


# ── Group ────────────────────────────────────────────────────────────────────


@click.group(name="market", help="Community marketplace — browse, install, publish, tip")
def market_group():
    """Manage marketplace packages."""
    pass


# ── Search ───────────────────────────────────────────────────────────────────


@market_group.command(name="search")
@click.argument("query")
@click.option("--category", "-c", default="", help="Filter by category")
@click.option("--limit", "-l", default=20, help="Max results")
def market_search(query: str, category: str, limit: int):
    """Search the marketplace."""
    store = _get_store()
    results = store.search_listings(
        query=query,
        category=category if category else None,
        limit=limit,
    )

    if not results:
        click.echo(f"No results for '{query}'")
        store.close()
        return

    click.echo()
    click.echo(f"  {'Title':<25} {'Category':<14} {'Rating':<8} {'Downloads':<10} {'Price'}")
    click.echo(f"  {'─'*25} {'─'*14} {'─'*8} {'─'*10} {'─'*10}")
    for item in results:
        stars = f"{item.rating:.1f}" if item.ratings_count > 0 else "—"
        click.echo(
            f"  {item.title[:25]:<25} {item.category:<14} {stars:<8} "
            f"{item.downloads:<10} {_format_price(item)}"
        )
    click.echo(f"\n  {len(results)} result(s)")
    store.close()


# ── Install ──────────────────────────────────────────────────────────────────


@market_group.command(name="install")
@click.argument("listing_id")
def market_install(listing_id: str):
    """Install a marketplace package by ID."""
    store = _get_store()
    listing = store.get_listing(listing_id)

    if not listing:
        # Try searching by title
        results = store.search_listings(query=listing_id, limit=5)
        if results:
            click.echo(f"Package '{listing_id}' not found by ID. Did you mean:")
            for r in results:
                click.echo(f"  {r.id[:12]}  {r.title} ({_format_price(r)})")
        else:
            click.echo(f"Package '{listing_id}' not found. Try 'prowlr market search <query>'.")
        store.close()
        return

    click.echo(f"\n  Installing: {listing.title} v{listing.version}")
    click.echo(f"  Author:     {listing.author_id}")
    click.echo(f"  Price:      {_format_price(listing)}")
    click.echo(f"  Category:   {listing.category}")
    click.echo(f"  Downloads:  {listing.downloads}")

    if listing.pricing_model != PricingModel.free:
        click.echo(f"\n  This is a paid package ({_format_price(listing)}).")
        if not click.confirm("  Proceed with purchase?"):
            click.echo("  Cancelled.")
            store.close()
            return

    # Record installation
    record = InstallRecord(
        listing_id=listing.id,
        user_id="local",
        version=listing.version,
    )
    store.record_install(record)

    # Create local install directory
    install_dir = WORKING_DIR / "marketplace" / listing_id[:12]
    install_dir.mkdir(parents=True, exist_ok=True)
    (install_dir / "manifest.json").write_text(
        json.dumps(listing.model_dump(), indent=2, default=str)
    )

    click.echo(f"\n  Installed to {install_dir}")
    click.echo(f"  Total downloads: {listing.downloads + 1}")
    store.close()


# ── List installed ───────────────────────────────────────────────────────────


@market_group.command(name="list")
def market_list():
    """Show installed marketplace packages."""
    market = WORKING_DIR / "marketplace"
    if not market.exists():
        click.echo("No marketplace packages installed.")
        return

    installed = [
        d.name
        for d in market.iterdir()
        if d.is_dir() and (d / "manifest.json").exists()
    ]
    if not installed:
        click.echo("No marketplace packages installed.")
        return

    click.echo()
    for name in sorted(installed):
        manifest = json.loads((market / name / "manifest.json").read_text())
        price = _format_price(MarketplaceListing(**manifest)) if "pricing_model" in manifest else "—"
        click.echo(
            f"  {name:<14} {manifest.get('title', '?'):<25} "
            f"v{manifest.get('version', '?'):<10} {price}"
        )
    click.echo()


# ── Publish ──────────────────────────────────────────────────────────────────


@market_group.command(name="publish")
@click.argument("path", type=click.Path(exists=True))
@click.option("--price", "-p", type=float, default=0.0, help="Price (0 = free)")
@click.option("--pricing", type=click.Choice(["free", "one_time", "subscription", "usage_based"]), default="free")
@click.option("--category", "-c", type=click.Choice([c.value for c in MarketplaceCategory]), required=True)
def market_publish(path: str, price: float, pricing: str, category: str):
    """Package and publish a marketplace item."""
    manifest_path = Path(path) / "manifest.json"
    if not manifest_path.exists():
        # Try SKILL.md for skill packages
        skill_md = Path(path) / "SKILL.md"
        if skill_md.exists():
            click.echo("  Detected skill package (SKILL.md found)")
        else:
            click.echo("Error: No manifest.json or SKILL.md found in package directory.")
            raise SystemExit(1)

    store = _get_store()

    # Build listing from manifest or defaults
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
    else:
        manifest = {"title": Path(path).name, "description": ""}

    listing = MarketplaceListing(
        author_id="local",
        title=manifest.get("title", manifest.get("name", Path(path).name)),
        description=manifest.get("description", ""),
        category=MarketplaceCategory(category),
        version=manifest.get("version", "1.0.0"),
        pricing_model=PricingModel(pricing),
        price=price,
        tags=manifest.get("tags", []),
    )

    published = store.publish_listing(listing)
    click.echo(f"\n  Published: {published.title}")
    click.echo(f"  ID:        {published.id[:12]}")
    click.echo(f"  Category:  {published.category}")
    click.echo(f"  Price:     {_format_price(published)}")
    click.echo(f"  Status:    {published.status} (pending review)")

    if price > 0:
        author_share = price * published.revenue_split
        click.echo(f"  Revenue:   ${author_share:.2f} per sale ({int(published.revenue_split * 100)}% split)")

    click.echo()
    store.close()


# ── Popular / Top Rated ──────────────────────────────────────────────────────


@market_group.command(name="popular")
@click.option("--limit", "-l", default=10, help="Number of results")
def market_popular(limit: int):
    """Show most downloaded packages."""
    store = _get_store()
    results = store.get_popular(limit=limit)

    if not results:
        click.echo("No approved listings yet.")
        store.close()
        return

    click.echo("\n  Most Popular:")
    click.echo(f"  {'#':<4} {'Title':<25} {'Downloads':<10} {'Price'}")
    click.echo(f"  {'─'*4} {'─'*25} {'─'*10} {'─'*10}")
    for i, item in enumerate(results, 1):
        click.echo(f"  {i:<4} {item.title[:25]:<25} {item.downloads:<10} {_format_price(item)}")
    click.echo()
    store.close()


# ── Update registry ──────────────────────────────────────────────────────────


@market_group.command(name="update")
def market_update():
    """Update the marketplace registry index."""
    click.echo("Updating marketplace registry...")
    # TODO: Fetch from GitHub registry repo or ProwlrBot marketplace API
    click.echo("Registry up to date.")


# ── Tip ──────────────────────────────────────────────────────────────────────


@market_group.command(name="tip")
@click.argument("listing_id")
@click.argument("amount", type=float)
@click.option("--message", "-m", default="", help="Thank-you message")
def market_tip(listing_id: str, amount: float, message: str):
    """Tip a package developer. Shows appreciation and supports development."""
    if amount <= 0:
        click.echo("Tip amount must be positive.")
        return

    store = _get_store()
    listing = store.get_listing(listing_id)
    if not listing:
        click.echo(f"Package '{listing_id}' not found.")
        store.close()
        return

    click.echo(f"\n  Tipping ${amount:.2f} to {listing.title} by {listing.author_id}")
    if message:
        click.echo(f"  Message: \"{message}\"")

    if not click.confirm("  Confirm tip?"):
        click.echo("  Cancelled.")
        store.close()
        return

    # Record tip in marketplace DB
    tip = TipRecord(
        listing_id=listing_id,
        author_id=listing.author_id,
        tipper_id="local",
        amount=amount,
        message=message,
    )
    store.add_tip(tip)

    total = store.get_tip_total(listing.author_id)
    click.echo(f"\n  Tip of ${amount:.2f} recorded!")
    click.echo(f"  {listing.author_id}'s total tips: ${total:.2f}")
    click.echo(f"  Thank you for supporting open development!")
    click.echo()
    store.close()


# ── Review ───────────────────────────────────────────────────────────────────


@market_group.command(name="review")
@click.argument("listing_id")
@click.option("--rating", "-r", type=click.IntRange(1, 5), required=True, help="Rating 1-5")
@click.option("--comment", "-c", default="", help="Review comment")
def market_review(listing_id: str, rating: int, comment: str):
    """Leave a review for a marketplace package."""
    store = _get_store()
    listing = store.get_listing(listing_id)
    if not listing:
        click.echo(f"Package '{listing_id}' not found.")
        store.close()
        return

    review = ReviewEntry(
        listing_id=listing_id,
        reviewer_id="local",
        rating=rating,
        comment=comment,
    )
    store.add_review(review)
    click.echo(f"  Review added: {'*' * rating}{'.' * (5 - rating)} for {listing.title}")
    store.close()


# ── Categories ───────────────────────────────────────────────────────────────


@market_group.command(name="categories")
def market_categories():
    """List all marketplace categories."""
    click.echo("\n  Marketplace Categories:")
    for cat in MarketplaceCategory:
        click.echo(f"    {cat.value}")
    click.echo()
