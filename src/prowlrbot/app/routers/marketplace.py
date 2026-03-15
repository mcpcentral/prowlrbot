# -*- coding: utf-8 -*-
"""FastAPI router for the ProwlrBot Marketplace."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from pydantic import BaseModel as PydanticBaseModel

from prowlrbot.auth.middleware import get_current_user


class TipRequest(PydanticBaseModel):
    amount: float
    message: str = ""


class ScanRequest(PydanticBaseModel):
    content: str
    filename: str = "SKILL.md"


class SubscribeRequest(PydanticBaseModel):
    user_id: str = "default"
    success_url: str = ""
    cancel_url: str = ""


from ...marketplace.install_helper import materialize_install
from ...marketplace.models import (
    Bundle,
    CreditBalance,
    CreditTransactionType,
    InstallRecord,
    MarketplaceCategory,
    MarketplaceListing,
    PREMIUM_CONTENT_PRICES,
    PricingModel,
    ReviewEntry,
    TipRecord,
)
from ...marketplace.store import MarketplaceStore

router = APIRouter(prefix="/marketplace", tags=["marketplace"])

# Lazily initialized singleton store.
_store: MarketplaceStore | None = None


def _get_store() -> MarketplaceStore:
    """Get or create the global MarketplaceStore instance."""
    global _store
    if _store is None:
        _store = MarketplaceStore()
    return _store


# ------------------------------------------------------------------
# Listings
# ------------------------------------------------------------------


@router.post("/listings", response_model=MarketplaceListing)
async def publish_listing(
    listing: MarketplaceListing,
    _user=Depends(get_current_user),
) -> MarketplaceListing:
    """Publish a new listing to the marketplace."""
    return _get_store().publish_listing(listing)


@router.get("/listings", response_model=list[MarketplaceListing])
async def search_listings(
    query: str = "",
    q: str = "",
    category: Optional[str] = None,
    persona: Optional[str] = None,
    difficulty: Optional[str] = None,
    sort: str = "popular",
    limit: int = 50,
) -> list[MarketplaceListing]:
    """Search marketplace listings."""
    search_query = q or query  # accept both q and query
    limit = max(1, min(limit, 200))
    return _get_store().search_listings(
        query=search_query,
        category=category,
        persona=persona,
        difficulty=difficulty,
        sort=sort,
        limit=limit,
    )


# ------------------------------------------------------------------
# Bundles
# ------------------------------------------------------------------


@router.get("/bundles")
async def list_bundles() -> list[dict]:
    """List all curated bundles."""
    bundles = _get_store().list_bundles()
    return [b.model_dump() for b in bundles]


@router.get("/bundles/{bundle_id}")
async def get_bundle(bundle_id: str) -> dict:
    """Get bundle detail with full listing objects."""
    store = _get_store()
    bundle = store.get_bundle(bundle_id)
    if bundle is None:
        raise HTTPException(status_code=404, detail="Bundle not found")
    listings = [store.get_listing(lid) for lid in bundle.listing_ids]
    listings = [l for l in listings if l is not None]
    return {
        "bundle": bundle.model_dump(),
        "listings": [l.model_dump() for l in listings],
    }


@router.post("/bundles/{bundle_id}/install")
async def install_bundle(
    bundle_id: str,
    _user=Depends(get_current_user),
) -> dict:
    """Install all listings in a bundle. Continues on failure. Paid listings cost credits."""
    store = _get_store()
    bundle = store.get_bundle(bundle_id)
    if bundle is None:
        raise HTTPException(status_code=404, detail="Bundle not found")

    user_id = _user.id
    installed = []
    failed = []
    for lid in bundle.listing_ids:
        listing = store.get_listing(lid)
        if listing is None:
            failed.append({"slug": lid, "error": "Listing not found"})
            continue
        try:
            if listing.pricing_model != PricingModel.free and listing.price > 0:
                store.spend_credits(
                    user_id,
                    int(listing.price),
                    CreditTransactionType.listing_purchase,
                    reference_id=lid,
                    description=f"Install: {listing.title}",
                )
            record = InstallRecord(
                listing_id=lid,
                user_id=user_id,
                version=listing.version,
            )
            store.record_install(record)
            installed.append(lid)
            try:
                materialize_install(listing)
            except Exception:
                pass  # already recorded; materialize is best-effort
        except ValueError as e:
            failed.append({"slug": lid, "error": str(e)})
        except Exception as e:
            failed.append({"slug": lid, "error": str(e)})

    store.increment_bundle_installs(bundle_id)
    return {
        "installed": installed,
        "failed": failed,
        "total": len(bundle.listing_ids),
    }


@router.get("/listings/{listing_id}", response_model=MarketplaceListing)
async def get_listing(listing_id: str) -> MarketplaceListing:
    """Get a single listing by ID."""
    listing = _get_store().get_listing(listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


@router.get("/listings/{listing_id}/detail")
async def get_listing_detail(listing_id: str) -> dict:
    """Full detail: listing, reviews, computed fields, related listings."""
    store = _get_store()
    listing = store.get_listing(listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")

    reviews = store.get_reviews(listing_id, limit=50)
    tip_total = store.get_tip_total(listing.author_id)

    # Bundle membership
    bundles = [b.name for b in store.list_bundles() if listing_id in b.listing_ids]

    # Related listings: same category, max 4, excluding current
    related = store.search_listings(
        category=listing.category.value,
        sort="popular",
        limit=5,
    )
    related = [r for r in related if r.id != listing_id][:4]

    # Author's other listings
    author_listings = store.list_by_author(listing.author_id)
    author_others = [l for l in author_listings if l.id != listing_id][:4]

    return {
        "listing": listing.model_dump(),
        "install_command": f"prowlr market install {listing_id}",
        "tip_total": tip_total,
        "reviews": [r.model_dump() for r in reviews],
        "bundles": bundles,
        "related": [r.model_dump() for r in related],
        "author_listings": [l.model_dump() for l in author_others],
    }


@router.post("/listings/{listing_id}/scan")
async def scan_listing_content(
    listing_id: str,
    body: ScanRequest,
    _user=Depends(get_current_user),
) -> dict:
    """Security-scan markdown content for a listing and store the result.

    The scan result is persisted to the listing's `skill_scan` field.
    Returns the full scan summary including risk level and any findings.
    """
    import tempfile
    from pathlib import Path
    from prowlrbot.marketplace.scanner import scan_file

    listing = _get_store().get_listing(listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")

    with tempfile.NamedTemporaryFile(
        suffix=".md",
        mode="w",
        delete=False,
        encoding="utf-8",
    ) as tf:
        tf.write(body.content)
        tmp_path = Path(tf.name)

    try:
        result = scan_file(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    scan_data = {
        "risk_level": result.risk_level.value,
        "blocked": result.blocked,
        "findings": [
            {
                "risk": f.risk.value,
                "category": f.category,
                "detail": f.detail,
                "line": f.line,
            }
            for f in result.findings
        ],
        "filename": body.filename,
    }

    # Persist scan result to listing
    _get_store().update_listing(listing_id, {"skill_scan": scan_data})

    return {
        "listing_id": listing_id,
        "scan": scan_data,
        "summary": result.summary(),
    }


@router.put("/listings/{listing_id}", response_model=MarketplaceListing)
async def update_listing(
    listing_id: str,
    updates: dict,
    _user=Depends(get_current_user),
) -> MarketplaceListing:
    """Partially update a listing."""
    listing = _get_store().update_listing(listing_id, updates)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


@router.get(
    "/listings/author/{author_id}",
    response_model=list[MarketplaceListing],
)
async def list_by_author(author_id: str) -> list[MarketplaceListing]:
    """Get all listings by a specific author."""
    return _get_store().list_by_author(author_id)


# ------------------------------------------------------------------
# Reviews
# ------------------------------------------------------------------


@router.post("/listings/{listing_id}/reviews", response_model=ReviewEntry)
async def add_review(
    listing_id: str,
    review: ReviewEntry,
    _user=Depends(get_current_user),
) -> ReviewEntry:
    """Add a review to a listing."""
    listing = _get_store().get_listing(listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    review.listing_id = listing_id
    return _get_store().add_review(review)


@router.get("/listings/{listing_id}/reviews", response_model=list[ReviewEntry])
async def get_reviews(listing_id: str, limit: int = 50) -> list[ReviewEntry]:
    """Get reviews for a listing."""
    return _get_store().get_reviews(listing_id, limit=min(limit, 200))


# ------------------------------------------------------------------
# Installs
# ------------------------------------------------------------------


@router.post("/listings/{listing_id}/install", response_model=InstallRecord)
async def record_install(
    listing_id: str,
    record: Optional[InstallRecord] = Body(None),
    _user=Depends(get_current_user),
) -> InstallRecord:
    """Record an installation of a listing.

    Body is optional (console sends POST with no body). For paid listings,
    deducts credits (listing.price) before recording.
    Blocked if the listing's security scan risk level is HIGH or above.
    """
    store = _get_store()
    listing = store.get_listing(listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")

    scan = listing.skill_scan
    if scan.get("blocked", False):
        raise HTTPException(
            status_code=403,
            detail=(
                f"Installation blocked: security scan found "
                f"{scan.get('risk_level', 'high')} risk content. "
                "Review the scan results at "
                f"POST /marketplace/listings/{listing_id}/scan"
            ),
        )

    user_id = _user.id
    if record is None:
        record = InstallRecord(
            listing_id=listing_id,
            user_id=user_id,
            version=listing.version,
        )
    else:
        record.user_id = user_id
        record.listing_id = listing_id

    # Paid listing: spend credits before recording install
    if listing.pricing_model != PricingModel.free and listing.price > 0:
        amount = int(listing.price)
        try:
            store.spend_credits(
                user_id,
                amount,
                CreditTransactionType.listing_purchase,
                reference_id=listing_id,
                description=f"Install: {listing.title}",
            )
        except ValueError as e:
            balance = store.get_balance(user_id)
            raise HTTPException(
                status_code=402,
                detail={
                    "code": "insufficient_credits",
                    "message": str(e),
                    "balance": balance.balance,
                    "required": amount,
                },
            )

    record = store.record_install(record)
    try:
        materialize_install(listing)
    except Exception:
        pass  # already recorded; materialize is best-effort
    return record


# ------------------------------------------------------------------
# Discovery
# ------------------------------------------------------------------


@router.get("/popular", response_model=list[MarketplaceListing])
async def get_popular(limit: int = 20) -> list[MarketplaceListing]:
    """Get the most popular listings by download count."""
    return _get_store().get_popular(limit=min(limit, 100))


@router.get("/top-rated", response_model=list[MarketplaceListing])
async def get_top_rated(limit: int = 20) -> list[MarketplaceListing]:
    """Get the highest-rated listings."""
    return _get_store().get_top_rated(limit=min(limit, 100))


@router.get("/categories", response_model=list[str])
async def list_categories() -> list[str]:
    """Return all available marketplace categories."""
    return [c.value for c in MarketplaceCategory]


# Free trial days for Pro (and Team) when upgrading from Free
FREE_TRIAL_DAYS = 14


@router.get("/tiers")
async def get_tiers():
    """Return available subscription tiers with pricing and feature lists."""
    return [
        {
            "id": "free",
            "name": "Free",
            "price_monthly": 0,
            "price_label": "$0/mo",
            "credits_per_month": 1000,
            "free_trial_days": FREE_TRIAL_DAYS,
            "features": [
                "1 agent",
                "1,000 credits/mo",
                "Basic monitoring",
                "Community support",
                f"{FREE_TRIAL_DAYS}-day Pro trial",
            ],
            "color": "default",
            "cta": "Start free trial",
            "cta_disabled": False,
        },
        {
            "id": "pro",
            "name": "Pro",
            "price_monthly": 19,
            "price_label": "$19/mo",
            "credits_per_month": 10000,
            "features": [
                "5 agents",
                "10,000 credits/mo",
                "Advanced monitoring",
                "Priority support",
                "API access",
                "Console plugins (add tabs & pages)",
            ],
            "color": "blue",
            "cta": "Upgrade to Pro",
            "cta_disabled": False,
        },
        {
            "id": "team",
            "name": "Team",
            "price_monthly": 49,
            "price_label": "$49/mo",
            "credits_per_month": 50000,
            "features": [
                "Unlimited agents",
                "50,000 credits/mo",
                "War Room",
                "Console plugins (add tabs & pages)",
                "Team collaboration",
                "SLA support",
            ],
            "color": "purple",
            "cta": "Upgrade to Team",
            "cta_disabled": False,
        },
    ]


# Tier config: id → (display_name, price_cents, credits_per_month)
_TIER_CONFIG: dict[str, tuple[str, int, int]] = {
    "pro": ("ProwlrBot Pro", 1900, 10_000),
    "team": ("ProwlrBot Team", 4900, 50_000),
}


def _get_or_create_subscription_price(stripe_module, tier_id: str) -> str:
    """Return a live Stripe Price ID for a monthly subscription tier.

    Uses ``lookup_key`` so repeated calls are idempotent — the first call
    creates the Product + Price; subsequent calls return the same Price ID.
    """
    name, amount_cents, _ = _TIER_CONFIG[tier_id]
    lookup_key = f"prowlrbot_{tier_id}_monthly"

    existing = stripe_module.Price.list(lookup_keys=[lookup_key], limit=1)
    if existing.data:
        return existing.data[0].id

    product = stripe_module.Product.create(
        name=name,
        metadata={"prowlrbot_tier": tier_id},
    )
    price = stripe_module.Price.create(
        unit_amount=amount_cents,
        currency="usd",
        recurring={"interval": "month"},
        product=product.id,
        lookup_key=lookup_key,
        transfer_lookup_key=True,
    )
    return price.id


@router.post("/subscribe/{tier_id}")
async def subscribe(
    tier_id: str,
    body: SubscribeRequest,
    request: Request,
    _user=Depends(get_current_user),
) -> dict:
    """Create a Stripe Checkout Session for a monthly subscription tier.

    Returns ``{"checkout_url": "<stripe_url>"}`` on success.
    When Stripe is not configured, returns ``{"checkout_url": null, "message": "..."}``
    so the UI can show instructions (e.g. use CLI: prowlr market upgrade <tier>).
    """
    import os

    if tier_id not in _TIER_CONFIG:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown tier: {tier_id!r}",
        )

    stripe_key = os.environ.get("STRIPE_SECRET_KEY")
    if not stripe_key:
        return {
            "checkout_url": None,
            "message": "Stripe not configured. Set STRIPE_SECRET_KEY for paid upgrades, or use CLI: prowlr market upgrade <tier> for local tier changes.",
        }

    # Use canonical app URL so Stripe redirects to app.prowlrbot.com/credits, not prowlrbot.fly.dev.
    base = (os.environ.get("PROWLRBOT_BASE_URL") or str(request.base_url)).rstrip("/")
    success_url = body.success_url or f"{base}/credits?subscribed=true&tier={tier_id}"
    cancel_url = body.cancel_url or f"{base}/credits"

    try:
        import stripe

        stripe.api_key = stripe_key
        price_id = _get_or_create_subscription_price(stripe, tier_id)

        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            subscription_data={
                "trial_period_days": FREE_TRIAL_DAYS,
            },
            metadata={
                "user_id": body.user_id,
                "tier_id": tier_id,
            },
        )
        return {"checkout_url": session.url}
    except ImportError:
        raise HTTPException(status_code=503, detail="Stripe SDK not installed")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Stripe error: {exc}")


PERSONA_CATALOG = [
    {
        "id": "parent",
        "label": "Parent & Family",
        "icon": "home",
        "description": "Automate family life",
    },
    {
        "id": "business",
        "label": "Small Business",
        "icon": "briefcase",
        "description": "Run your business smarter",
    },
    {
        "id": "student",
        "label": "Student",
        "icon": "book-open",
        "description": "Study smarter, not harder",
    },
    {
        "id": "creator",
        "label": "Content Creator",
        "icon": "palette",
        "description": "Create more, manage less",
    },
    {
        "id": "freelancer",
        "label": "Freelancer",
        "icon": "laptop",
        "description": "Handle the admin so you can do the work",
    },
    {
        "id": "developer",
        "label": "Developer",
        "icon": "code",
        "description": "Automate your dev workflow",
    },
    {
        "id": "everyone",
        "label": "Everyone",
        "icon": "globe",
        "description": "Daily life, automated",
    },
]


@router.get("/personas", response_model=list[dict])
async def list_personas() -> list[dict]:
    """Return all persona categories for onboarding."""
    return PERSONA_CATALOG


@router.get("/for/{persona}", response_model=list[MarketplaceListing])
async def get_listings_for_persona(
    persona: str,
    limit: int = 20,
) -> list[MarketplaceListing]:
    """Get curated listings for a specific persona."""
    return _get_store().search_listings(persona=persona, limit=min(limit, 100))


# ------------------------------------------------------------------
# Tips
# ------------------------------------------------------------------


@router.post("/listings/{listing_id}/tip")
async def tip_author(
    listing_id: str,
    tip_req: TipRequest,
    _user=Depends(get_current_user),
) -> dict:
    """Create a Stripe checkout session for tipping, or record locally."""
    import os

    store = _get_store()
    listing = store.get_listing(listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Validate amount range
    if tip_req.amount < 1 or tip_req.amount > 100:
        raise HTTPException(
            status_code=400,
            detail="Tip amount must be between $1 and $100",
        )

    stripe_key = os.environ.get("STRIPE_SECRET_KEY")
    if not stripe_key:
        # No Stripe configured — record tip locally as fallback
        tip = TipRecord(
            listing_id=listing_id,
            author_id=listing.author_id,
            amount=tip_req.amount,
            message=tip_req.message,
        )
        store.add_tip(tip)
        return {
            "checkout_url": None,
            "tip_id": tip.id,
            "note": "Tip recorded locally (Stripe not configured)",
        }

    # Create Stripe checkout — tip recorded in webhook after payment
    try:
        import stripe

        stripe.api_key = stripe_key
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": int(tip_req.amount * 100),
                        "product_data": {
                            "name": f"Tip for {listing.title}",
                        },
                    },
                    "quantity": 1,
                },
            ],
            success_url=f"/marketplace/listings/{listing_id}?tipped=true",
            cancel_url=f"/marketplace/listings/{listing_id}",
            payment_intent_data={
                "statement_descriptor": (
                    os.environ.get("STRIPE_STATEMENT_DESCRIPTOR") or "ProwlrBot"
                )[:22],
            },
            metadata={
                "listing_id": listing_id,
                "author_id": listing.author_id,
                "amount": str(tip_req.amount),
                "message": tip_req.message,
            },
        )
        return {"checkout_url": session.url}
    except ImportError:
        # stripe package not installed — record locally
        tip = TipRecord(
            listing_id=listing_id,
            author_id=listing.author_id,
            amount=tip_req.amount,
            message=tip_req.message,
        )
        store.add_tip(tip)
        return {
            "checkout_url": None,
            "tip_id": tip.id,
            "note": "Stripe SDK not installed",
        }


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request) -> dict:
    """Stripe webhook — handles tip payments and subscription lifecycle."""
    import os

    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    if not webhook_secret:
        raise HTTPException(status_code=503, detail="Webhook not configured")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        import stripe

        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            webhook_secret,
        )
    except ImportError:
        raise HTTPException(status_code=503, detail="Stripe SDK not installed")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid signature")

    store = _get_store()
    event_type = event["type"]

    # ------------------------------------------------------------------
    # One-time tip payment
    # ------------------------------------------------------------------
    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        listing_id = metadata.get("listing_id")
        author_id = metadata.get("author_id")
        amount = float(metadata.get("amount", 0))
        message = metadata.get("message", "")

        if listing_id and author_id and amount > 0:
            tip = TipRecord(
                listing_id=listing_id,
                author_id=author_id,
                amount=amount,
                message=message,
            )
            store.add_tip(tip)

    # ------------------------------------------------------------------
    # Subscription created — award initial monthly credits
    # ------------------------------------------------------------------
    elif event_type == "customer.subscription.created":
        sub = event["data"]["object"]
        metadata = sub.get("metadata", {})
        user_id = metadata.get("user_id", "default")
        tier_id = metadata.get("tier_id", "")
        _, _, credits = _TIER_CONFIG.get(tier_id, ("", 0, 0))
        if credits > 0:
            store.add_credits(
                user_id=user_id,
                amount=credits,
                transaction_type=CreditTransactionType("purchased"),
                description=f"{tier_id.title()} subscription — initial credits",
            )

    # ------------------------------------------------------------------
    # Invoice paid — monthly credit refresh on renewal
    # ------------------------------------------------------------------
    elif event_type == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        # Only act on subscription renewals (billing_reason != subscription_create
        # to avoid double-awarding on the first invoice, which fires alongside
        # customer.subscription.created).
        if invoice.get("billing_reason") == "subscription_cycle":
            sub_id = invoice.get("subscription")
            if sub_id:
                try:
                    import stripe as _stripe

                    _stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
                    sub = _stripe.Subscription.retrieve(sub_id)
                    meta = sub.get("metadata", {})
                    user_id = meta.get("user_id", "default")
                    tier_id = meta.get("tier_id", "")
                    _, _, credits = _TIER_CONFIG.get(tier_id, ("", 0, 0))
                    if credits > 0:
                        store.add_credits(
                            user_id=user_id,
                            amount=credits,
                            transaction_type=CreditTransactionType(
                                "purchased",
                            ),
                            description=f"{tier_id.title()} subscription — monthly renewal",
                        )
                except Exception:
                    pass  # best-effort; Stripe will retry on failure

    return {"status": "received"}


# ------------------------------------------------------------------
# Credits
# ------------------------------------------------------------------


@router.get("/credits/{user_id}", response_model=CreditBalance)
async def get_credits(user_id: str) -> CreditBalance:
    """Get a user's credit balance. New users get welcome credits when PROWLR_FREE_TIER_WELCOME_CREDITS is set (default 100)."""
    return _get_store().get_balance(user_id)


@router.post("/credits/{user_id}/grant-monthly", response_model=CreditBalance)
async def grant_monthly_credits(user_id: str) -> CreditBalance:
    """Grant monthly credits for the user's tier if at least 30 days since last grant.

    Intended for cron (e.g. daily). Idempotent: only adds credits once per calendar month per user.
    """
    from ...marketplace.models import ProTier, PRO_TIER_LIMITS

    store = _get_store()
    balance = store.get_balance(user_id)
    tier = getattr(ProTier, balance.tier, ProTier.free)
    limits = PRO_TIER_LIMITS.get(tier, PRO_TIER_LIMITS[ProTier.free])
    monthly = limits.get("monthly_credits", 0)
    if monthly <= 0:
        return balance

    # Last monthly_grant transaction for this user
    txns = store.get_transactions(user_id, limit=100)
    from ...marketplace.models import CreditTransactionType

    last_grant = None
    for t in txns:
        if t.transaction_type == CreditTransactionType.monthly_grant:
            last_grant = t.created_at
            break
    if last_grant:
        from datetime import datetime, timezone, timedelta

        try:
            dt = datetime.fromisoformat(last_grant.replace("Z", "+00:00"))
            if (datetime.now(timezone.utc) - dt).days < 30:
                return store.get_balance(user_id)
        except Exception:
            pass

    return store.add_credits(
        user_id=user_id,
        amount=monthly,
        transaction_type=CreditTransactionType.monthly_grant,
        description=f"Monthly credit grant ({balance.tier} tier)",
    )


@router.get("/credits/{user_id}/transactions")
async def get_credit_transactions(user_id: str, limit: int = 20) -> list:
    """Get a user's credit transaction history."""
    store = _get_store()
    transactions = (
        store.get_transactions(user_id, limit=min(limit, 100))
        if hasattr(store, "get_transactions")
        else []
    )
    return transactions


@router.post("/credits/{user_id}/add", response_model=CreditBalance)
async def add_credits(
    user_id: str,
    amount: int,
    transaction_type: str = "purchased",
    description: str = "",
    _user=Depends(get_current_user),
) -> CreditBalance:
    """Add credits to a user's balance."""
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    return _get_store().add_credits(
        user_id=user_id,
        amount=amount,
        transaction_type=CreditTransactionType(transaction_type),
        description=description,
    )


@router.post("/credits/{user_id}/spend", response_model=CreditBalance)
async def spend_credits(
    user_id: str,
    amount: int,
    transaction_type: str = "listing_purchase",
    reference_id: str = "",
    description: str = "",
    _user=Depends(get_current_user),
) -> CreditBalance:
    """Spend credits from a user's balance."""
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    try:
        return _get_store().spend_credits(
            user_id=user_id,
            amount=amount,
            transaction_type=CreditTransactionType(transaction_type),
            reference_id=reference_id,
            description=description,
        )
    except ValueError as e:
        raise HTTPException(status_code=402, detail=str(e))


@router.post(
    "/credits/{user_id}/unlock/{content_key}",
    response_model=CreditBalance,
)
async def unlock_content(
    user_id: str,
    content_key: str,
    _user=Depends(get_current_user),
) -> CreditBalance:
    """Unlock premium content with credits."""
    if content_key not in PREMIUM_CONTENT_PRICES:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown content: {content_key}",
        )

    cost = PREMIUM_CONTENT_PRICES[content_key]
    try:
        return _get_store().spend_credits(
            user_id=user_id,
            amount=cost,
            transaction_type=CreditTransactionType.listing_purchase,
            reference_id=content_key,
            description=f"Unlocked {content_key}",
        )
    except ValueError as e:
        raise HTTPException(status_code=402, detail=str(e))


@router.get("/premium-content", response_model=dict)
async def list_premium_content() -> dict:
    """List all available premium content and prices."""
    return PREMIUM_CONTENT_PRICES


# ------------------------------------------------------------------
# Ecosystem
# ------------------------------------------------------------------


@router.get("/repos", response_model=dict)
async def list_ecosystem_repos() -> dict:
    """List all ProwlrBot ecosystem repositories."""
    from ...marketplace.registry import get_ecosystem_repos

    return get_ecosystem_repos()
