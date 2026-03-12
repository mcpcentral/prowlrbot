# -*- coding: utf-8 -*-
"""Marketplace CLI commands — search, install, publish, list, update, tip."""

from __future__ import annotations

import json
from pathlib import Path

import click

from ..constant import WORKING_DIR
from ..marketplace.models import (
    CREDIT_PURCHASE_PACKS,
    CreditTransactionType,
    InstallRecord,
    MarketplaceCategory,
    MarketplaceListing,
    PREMIUM_CONTENT_PRICES,
    PRO_TIER_LIMITS,
    PricingModel,
    ProTier,
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


@click.group(
    name="market", help="Community marketplace — browse, install, publish, tip"
)
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
    click.echo(
        f"  {'Title':<25} {'Category':<14} {'Rating':<8} {'Downloads':<10} {'Price'}"
    )
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
            click.echo(
                f"Package '{listing_id}' not found. Try 'prowlr market search <query>'."
            )
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
        price = (
            _format_price(MarketplaceListing(**manifest))
            if "pricing_model" in manifest
            else "—"
        )
        click.echo(
            f"  {name:<14} {manifest.get('title', '?'):<25} "
            f"v{manifest.get('version', '?'):<10} {price}"
        )
    click.echo()


# ── Publish ──────────────────────────────────────────────────────────────────


@market_group.command(name="publish")
@click.argument("path", type=click.Path(exists=True))
@click.option("--price", "-p", type=float, default=0.0, help="Price (0 = free)")
@click.option(
    "--pricing",
    type=click.Choice(["free", "one_time", "subscription", "usage_based"]),
    default="free",
)
@click.option(
    "--category",
    "-c",
    type=click.Choice([c.value for c in MarketplaceCategory]),
    required=True,
)
def market_publish(path: str, price: float, pricing: str, category: str):
    """Package and publish a marketplace item."""
    manifest_path = Path(path) / "manifest.json"
    if not manifest_path.exists():
        # Try SKILL.md for skill packages
        skill_md = Path(path) / "SKILL.md"
        if skill_md.exists():
            click.echo("  Detected skill package (SKILL.md found)")
        else:
            click.echo(
                "Error: No manifest.json or SKILL.md found in package directory."
            )
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
        click.echo(
            f"  Revenue:   ${author_share:.2f} per sale ({int(published.revenue_split * 100)}% split)"
        )

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
        click.echo(
            f"  {i:<4} {item.title[:25]:<25} {item.downloads:<10} {_format_price(item)}"
        )
    click.echo()
    store.close()


# ── Update registry ──────────────────────────────────────────────────────────


@market_group.command(name="update")
@click.option(
    "--token",
    envvar="GITHUB_TOKEN",
    default=None,
    help="GitHub token (or set GITHUB_TOKEN)",
)
def market_update(token: "str | None"):
    """Sync marketplace registry from ProwlrBot/prowlr-marketplace on GitHub."""
    from ..marketplace.registry import sync_registry

    click.echo("  Syncing from ProwlrBot/prowlr-marketplace...")
    store = _get_store()
    try:
        added, updated, total = sync_registry(store, token=token)
        click.echo(f"\n  Registry synced: {total} listings")
        click.echo(f"    New:     {added}")
        click.echo(f"    Updated: {updated}")
        click.echo()
    except Exception as exc:
        click.echo(f"  Sync failed: {exc}")
        click.echo("  Tip: Set GITHUB_TOKEN for higher rate limits.")
    finally:
        store.close()


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
        click.echo(f'  Message: "{message}"')

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
@click.option(
    "--rating", "-r", type=click.IntRange(1, 5), required=True, help="Rating 1-5"
)
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
    click.echo(
        f"  Review added: {'*' * rating}{'.' * (5 - rating)} for {listing.title}"
    )
    store.close()


# ── Bundles ─────────────────────────────────────────────────────────────────


@market_group.command(name="bundles")
def market_bundles():
    """List curated skill bundles."""
    store = _get_store()
    bundles = store.list_bundles()
    if not bundles:
        click.echo("No bundles available.")
        store.close()
        return

    click.echo("\n  Curated Bundles:")
    click.echo(f"  {'ID':<22} {'Name':<20} {'Items':<6} {'Installs'}")
    click.echo(f"  {'─'*22} {'─'*20} {'─'*6} {'─'*10}")
    for b in bundles:
        click.echo(
            f"  {b.id:<22} {b.name:<20} {len(b.listing_ids):<6} {b.install_count}"
        )
    click.echo()
    store.close()


@market_group.command(name="install-bundle")
@click.argument("bundle_id")
def market_install_bundle(bundle_id: str):
    """Install all skills in a curated bundle."""
    store = _get_store()
    bundle = store.get_bundle(bundle_id)
    if not bundle:
        click.echo(
            f"Bundle '{bundle_id}' not found. Run 'prowlr market bundles' to see available."
        )
        store.close()
        return

    click.echo(f"\n  Installing bundle: {bundle.name}")
    click.echo(f"  {len(bundle.listing_ids)} items\n")

    installed = 0
    for lid in bundle.listing_ids:
        listing = store.get_listing(lid)
        if listing is None:
            click.echo(f"    SKIP  {lid} (not found)")
            continue
        record = InstallRecord(
            listing_id=lid, user_id="local", version=listing.version
        )
        store.record_install(record)
        click.echo(f"    OK    {listing.title}")
        installed += 1

    store.increment_bundle_installs(bundle_id)
    click.echo(f"\n  Installed {installed}/{len(bundle.listing_ids)} items")
    store.close()


# ── Detail ──────────────────────────────────────────────────────────────────


@market_group.command(name="detail")
@click.argument("listing_id")
def market_detail(listing_id: str):
    """Show full details for a marketplace listing."""
    store = _get_store()
    listing = store.get_listing(listing_id)
    if not listing:
        click.echo(f"Package '{listing_id}' not found.")
        store.close()
        return

    badge = (
        "OFFICIAL"
        if getattr(listing, "trust_tier", "") == "official"
        else "VERIFIED"
    )
    click.echo(f"\n  {listing.title} [{badge}]")
    click.echo(f"  {'─' * 50}")
    click.echo(
        f"  Author:      {getattr(listing, 'author_name', listing.author_id)}"
    )
    click.echo(f"  Version:     {listing.version}")
    click.echo(f"  Category:    {listing.category}")
    click.echo(f"  License:     {getattr(listing, 'license', 'MIT')}")
    click.echo(f"  Downloads:   {listing.downloads}")
    click.echo(
        f"  Rating:      {'%.1f' % listing.rating}/5 ({listing.ratings_count} reviews)"
    )
    click.echo(f"  Install:     prowlr market install {listing.id}")
    if listing.description:
        click.echo(f"\n  {listing.description}")

    reviews = store.get_reviews(listing_id, limit=5)
    if reviews:
        click.echo(f"\n  Recent Reviews:")
        for r in reviews:
            stars = "*" * r.rating + "." * (5 - r.rating)
            click.echo(
                f"    {stars}  {r.comment[:60] if r.comment else '(no comment)'}"
            )

    click.echo()
    store.close()


# ── Categories ───────────────────────────────────────────────────────────────


@market_group.command(name="categories")
def market_categories():
    """List all marketplace categories."""
    click.echo("\n  Marketplace Categories:")
    for cat in MarketplaceCategory:
        click.echo(f"    {cat.value}")
    click.echo()


# ── Ecosystem repos ─────────────────────────────────────────────────────────


@market_group.command(name="repos")
def market_repos():
    """Show all ProwlrBot ecosystem repositories."""
    from ..marketplace.registry import get_ecosystem_repos

    repos = get_ecosystem_repos()
    click.echo()
    click.echo(f"  {'Repo':<22} {'Description'}")
    click.echo(f"  {'─'*22} {'─'*50}")
    for name, info in repos.items():
        click.echo(f"  {name:<22} {info['description'][:50]}")
    click.echo()
    click.echo("  Browse: https://github.com/ProwlrBot")
    click.echo()


# ── Credits ──────────────────────────────────────────────────────────────────


@market_group.command(name="credits")
@click.option("--user", "-u", default="local", help="User ID")
def market_credits(user: str):
    """Show your credit balance and recent transactions."""
    store = _get_store()
    balance = store.get_balance(user)
    tier_limits = PRO_TIER_LIMITS.get(ProTier(balance.tier), {})

    click.echo()
    click.echo("  ╔══════════════════════════════════════╗")
    click.echo(f"  ║   Credits: {balance.balance:>6}                    ║")
    click.echo("  ╚══════════════════════════════════════╝")
    click.echo()
    click.echo(f"  Tier:         {balance.tier.upper()}")
    click.echo(f"  Balance:      {balance.balance} credits")
    click.echo(f"  Total earned: {balance.total_earned}")
    click.echo(f"  Total spent:  {balance.total_spent}")
    click.echo(f"  Monthly:      +{tier_limits.get('monthly_credits', 0)} credits/mo")
    click.echo(
        f"  Earn bonus:   {tier_limits.get('credit_earn_multiplier', 1)}x multiplier"
    )

    txns = store.get_transactions(user, limit=10)
    if txns:
        click.echo(f"\n  Recent transactions:")
        for t in txns:
            sign = "+" if t.amount > 0 else ""
            click.echo(
                f"    {sign}{t.amount:>6}  {t.transaction_type:<22} {t.description}"
            )

    click.echo()
    store.close()


@market_group.command(name="buy-credits")
@click.option("--user", "-u", default="local", help="User ID")
def market_buy_credits(user: str):
    """Purchase credit packs."""
    click.echo("\n  Credit Packs:")
    click.echo(f"  {'Pack':<10} {'Credits':<10} {'Price':<10} {'Bonus'}")
    click.echo(f"  {'─'*10} {'─'*10} {'─'*10} {'─'*10}")

    packs = list(CREDIT_PURCHASE_PACKS.items())
    for i, (name, info) in enumerate(packs, 1):
        base = info["credits"]
        price = info["price"]
        per_dollar = base / price
        click.echo(
            f"  {i}) {name:<8} {base:<10} ${price:<9.2f} {per_dollar:.0f} credits/$"
        )

    click.echo()
    choice = click.prompt("  Select pack [1-4]", type=int)
    if choice < 1 or choice > len(packs):
        click.echo("  Invalid choice.")
        return

    pack_name, pack_info = packs[choice - 1]
    credits = pack_info["credits"]
    price = pack_info["price"]

    click.echo(f"\n  Purchasing {credits} credits for ${price:.2f}")
    if not click.confirm("  Confirm purchase?"):
        click.echo("  Cancelled.")
        return

    store = _get_store()
    balance = store.add_credits(
        user_id=user,
        amount=credits,
        transaction_type=CreditTransactionType.purchased,
        description=f"Purchased {pack_name} pack ({credits} credits)",
    )
    click.echo(f"\n  Added {credits} credits!")
    click.echo(f"  New balance: {balance.balance} credits")
    click.echo()
    store.close()


@market_group.command(name="unlock")
@click.argument("content_key")
@click.option("--user", "-u", default="local", help="User ID")
def market_unlock(content_key: str, user: str):
    """Unlock premium content with credits."""
    if content_key not in PREMIUM_CONTENT_PRICES:
        click.echo(f"  Unknown content: '{content_key}'")
        click.echo(f"\n  Available premium content:")
        for key, price in sorted(PREMIUM_CONTENT_PRICES.items()):
            click.echo(f"    {key:<30} {price:>5} credits")
        return

    cost = PREMIUM_CONTENT_PRICES[content_key]
    store = _get_store()
    balance = store.get_balance(user)

    click.echo(f"\n  Unlock: {content_key}")
    click.echo(f"  Cost:   {cost} credits")
    click.echo(f"  Balance: {balance.balance} credits")

    if balance.balance < cost:
        click.echo(f"\n  Insufficient credits! Need {cost - balance.balance} more.")
        click.echo("  Run 'prowlr market buy-credits' to purchase more.")
        store.close()
        return

    if not click.confirm("  Confirm unlock?"):
        click.echo("  Cancelled.")
        store.close()
        return

    # Determine transaction type from content key
    if content_key.startswith("workflow"):
        txn_type = CreditTransactionType.workflow_unlock
    elif content_key.startswith("spec"):
        txn_type = CreditTransactionType.spec_generate
    elif content_key.startswith("insight"):
        txn_type = CreditTransactionType.insight_purchase
    elif content_key.startswith("blueprint"):
        txn_type = CreditTransactionType.blueprint_unlock
    else:
        txn_type = CreditTransactionType.listing_purchase

    new_balance = store.spend_credits(
        user_id=user,
        amount=cost,
        transaction_type=txn_type,
        reference_id=content_key,
        description=f"Unlocked {content_key}",
    )
    click.echo(f"\n  Unlocked: {content_key}")
    click.echo(f"  Remaining: {new_balance.balance} credits")
    click.echo()
    store.close()


@market_group.command(name="tiers")
def market_tiers():
    """Show detailed subscription tiers with all features."""
    w = 62  # box width

    click.echo()
    click.echo(f"  ╔{'═' * w}╗")
    click.echo(f"  ║{'ProwlrBot Pro Tiers':^{w}}║")
    click.echo(f"  ║{'Always watching. Always ready.':^{w}}║")
    click.echo(f"  ╚{'═' * w}╝")

    _tier_details = {
        "free": {
            "label": "FREE",
            "price": "$0/mo",
            "tagline": "Get started, no commitment",
            "features": [
                ("Agents", "Up to 2 external agents"),
                ("Teams", "1 team"),
                ("Credits", "50/month"),
                ("Earn Multiplier", "1x base rate"),
                ("Marketplace", "Browse & install free packages"),
                ("Channels", "Console + 1 messaging channel"),
                ("Monitoring", "Basic web change detection"),
                ("Storage", "Local SQLite databases"),
                ("Support", "Community (GitHub Discussions)"),
            ],
            "not_included": [
                "Marketplace publishing",
                "Premium content",
                "Priority support",
                "Custom workflows",
                "Business insights",
                "Agent blueprints",
            ],
        },
        "starter": {
            "label": "STARTER",
            "price": "$5/mo",
            "tagline": "For individual developers",
            "features": [
                ("Agents", "Up to 3 external agents"),
                ("Teams", "1 team"),
                ("Credits", "500/month"),
                ("Earn Multiplier", "2x earn rate on contributions"),
                ("Marketplace", "Browse, install, review, tip"),
                ("Channels", "Console + 3 messaging channels"),
                ("Monitoring", "Web + API monitoring with alerts"),
                ("Prompt Libraries", "Access starter prompt packs"),
                ("Workflow Templates", "Basic workflow templates"),
                ("Storage", "Local SQLite + encrypted secrets"),
                ("Support", "Community + email support"),
            ],
            "not_included": [
                "Marketplace publishing",
                "Business insights & roadmaps",
                "Agent blueprints",
                "Custom spec generation",
                "Priority support",
            ],
        },
        "pro": {
            "label": "PRO",
            "price": "$15/mo",
            "tagline": "For power users & small teams",
            "popular": True,
            "features": [
                ("Agents", "Unlimited external agents"),
                ("Teams", "Up to 5 teams"),
                ("Credits", "2,000/month"),
                ("Earn Multiplier", "3x earn rate on contributions"),
                ("Marketplace", "Full access: browse, install, PUBLISH"),
                ("Revenue Share", "70/30 split on paid listings"),
                ("Channels", "All 8 channels (Discord, Telegram, etc.)"),
                ("Monitoring", "Advanced monitoring + competitor tracking"),
                ("Workflow Templates", "All basic + advanced workflows"),
                ("Business Specs", "Custom job specs tailored to you"),
                ("Insight Packs", "Market analysis & competitor reports"),
                ("Roadmap Generators", "Auto-generate product roadmaps"),
                ("Agent Blueprints", "Pre-configured agent teams"),
                ("Prompt Libraries", "Full prompt collection access"),
                ("Hub Access", "Multi-agent coordination via hub"),
                ("AgentVerse", "Full world access + guilds"),
                ("Storage", "SQLite + Redis + encrypted vault"),
                ("Support", "Priority email + Discord channel"),
            ],
            "not_included": [
                "Enterprise team features",
                "Custom SLA",
            ],
        },
        "team": {
            "label": "TEAM",
            "price": "$29/mo",
            "tagline": "For teams & businesses",
            "features": [
                ("Agents", "Unlimited external agents"),
                ("Teams", "Unlimited teams"),
                ("Credits", "10,000/month"),
                ("Earn Multiplier", "5x earn rate on contributions"),
                ("Marketplace", "Full access + priority review queue"),
                ("Revenue Share", "70/30 split + featured placement"),
                ("Channels", "All 8 channels + custom channel support"),
                ("Monitoring", "Enterprise monitoring + SLA tracking"),
                ("Workflow Templates", "All templates + custom creation"),
                ("Business Specs", "Unlimited custom specs"),
                ("Insight Packs", "Full market intelligence suite"),
                ("Roadmap Generators", "Detailed + enterprise roadmaps"),
                ("Agent Blueprints", "All blueprints + custom design"),
                ("Prompt Libraries", "Master collection + private prompts"),
                ("Hub Access", "Priority hub + dedicated bridge"),
                ("AgentVerse", "Premium zones + tournaments"),
                ("Swarm Mode", "Docker-based multi-node agents"),
                ("Custom Workflows", "Build & save custom automations"),
                ("API Access", "Full REST API for integrations"),
                ("Storage", "SQLite + Redis + S3-compatible"),
                ("Audit Log", "Full activity and compliance logging"),
                ("Support", "Priority support + onboarding call"),
            ],
            "not_included": [],
        },
    }

    for tier_key, info in _tier_details.items():
        is_popular = info.get("popular", False)

        click.echo()
        if is_popular:
            click.echo(f"  {'* MOST POPULAR *':^{w}}")
        click.echo(f"  ┌{'─' * w}┐")
        click.echo(f"  │{info['label'] + '  ' + info['price']:^{w}}│")
        click.echo(f"  │{info['tagline']:^{w}}│")
        click.echo(f"  ├{'─' * w}┤")

        # Features
        click.echo(f"  │{'  INCLUDED:':>{14}}{'':<{w - 14}}│")
        for label, desc in info["features"]:
            line = f"    [+] {label:<22} {desc}"
            click.echo(f"  │{line:<{w}}│")

        # Not included
        if info.get("not_included"):
            click.echo(f"  │{'':─<{w}}│")
            click.echo(f"  │{'  NOT INCLUDED:':>{16}}{'':<{w - 16}}│")
            for item in info["not_included"]:
                line = f"    [ ] {item}"
                click.echo(f"  │{line:<{w}}│")

        click.echo(f"  └{'─' * w}┘")

    # Comparison table
    click.echo()
    click.echo(f"  {'Quick Comparison':^{w}}")
    click.echo()
    click.echo(
        f"  {'Feature':<26} {'Free':<8} {'Starter':<10} {'Pro':<10} {'Team':<10}"
    )
    click.echo(f"  {'─'*26} {'─'*8} {'─'*10} {'─'*10} {'─'*10}")
    _rows = [
        ("Price", "$0", "$5/mo", "$15/mo", "$29/mo"),
        ("External Agents", "2", "3", "Unlimited", "Unlimited"),
        ("Teams", "1", "1", "5", "Unlimited"),
        ("Monthly Credits", "50", "500", "2,000", "10,000"),
        ("Earn Multiplier", "1x", "2x", "3x", "5x"),
        ("Channels", "2", "4", "All 8", "All 8+"),
        ("Marketplace Publish", "—", "—", "Yes", "Yes"),
        ("Workflow Templates", "—", "Basic", "All", "All+Custom"),
        ("Business Specs", "—", "—", "Yes", "Unlimited"),
        ("Insight Packs", "—", "—", "Yes", "Full Suite"),
        ("Roadmap Generators", "—", "—", "Yes", "Enterprise"),
        ("Agent Blueprints", "—", "—", "Yes", "All+Custom"),
        ("Prompt Libraries", "—", "Starter", "Full", "Master"),
        ("Hub/Swarm", "—", "—", "Hub", "Hub+Swarm"),
        ("AgentVerse", "Basic", "Basic", "Full", "Premium"),
        ("Support", "Community", "Email", "Priority", "Priority+"),
    ]
    for row in _rows:
        click.echo(f"  {row[0]:<26} {row[1]:<8} {row[2]:<10} {row[3]:<10} {row[4]:<10}")

    click.echo()
    click.echo("  Upgrade: prowlr market upgrade <tier>")
    click.echo("  Credits: prowlr market buy-credits")
    click.echo()


# ── Upgrade ──────────────────────────────────────────────────────────────────


@market_group.command(name="upgrade")
@click.argument("tier", type=click.Choice(["starter", "pro", "team"]))
@click.option("--user", "-u", default="local", help="User ID")
def market_upgrade(tier: str, user: str):
    """Upgrade your subscription tier."""
    store = _get_store()
    balance = store.get_balance(user)
    tier_prices = {"starter": 5, "pro": 15, "team": 29}
    price = tier_prices[tier]

    current = balance.tier
    if current == tier:
        click.echo(f"  Already on {tier.upper()} tier.")
        store.close()
        return

    tier_order = ["free", "starter", "pro", "team"]
    if tier_order.index(tier) < tier_order.index(current):
        click.echo(f"  Downgrade from {current.upper()} to {tier.upper()}?")
        click.echo("  Note: Downgrades take effect at next billing cycle.")
    else:
        click.echo(f"  Upgrade from {current.upper()} to {tier.upper()}")

    limits = PRO_TIER_LIMITS[ProTier(tier)]
    click.echo()
    click.echo(f"  Tier:         {tier.upper()}")
    click.echo(f"  Price:        ${price}/mo")
    click.echo(f"  Credits/mo:   {limits['monthly_credits']}")
    click.echo(
        f"  Agents:       {'Unlimited' if limits['agents'] >= 999 else limits['agents']}"
    )
    click.echo(
        f"  Teams:        {'Unlimited' if limits['teams'] >= 999 else limits['teams']}"
    )
    click.echo(f"  Earn bonus:   {limits['credit_earn_multiplier']}x")
    click.echo(f"  Publish:      {'Yes' if limits['marketplace_publish'] else 'No'}")
    click.echo()

    if not click.confirm(f"  Confirm upgrade to {tier.upper()} (${price}/mo)?"):
        click.echo("  Cancelled.")
        store.close()
        return

    # Set tier and grant monthly credits
    store.set_tier(user, tier)
    new_balance = store.add_credits(
        user_id=user,
        amount=limits["monthly_credits"],
        transaction_type=CreditTransactionType.monthly_grant,
        description=f"Welcome to {tier.upper()} — monthly credit grant",
    )

    click.echo()
    click.echo(f"  Upgraded to {tier.upper()}!")
    click.echo(f"  +{limits['monthly_credits']} credits added")
    click.echo(f"  New balance: {new_balance.balance} credits")
    click.echo()
    store.close()
