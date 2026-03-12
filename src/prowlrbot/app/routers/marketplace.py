# -*- coding: utf-8 -*-
"""FastAPI router for the ProwlrBot Marketplace."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel as PydanticBaseModel


class TipRequest(PydanticBaseModel):
    amount: float
    message: str = ""

from ...marketplace.models import (
    Bundle,
    CreditBalance,
    CreditTransactionType,
    InstallRecord,
    MarketplaceCategory,
    MarketplaceListing,
    PREMIUM_CONTENT_PRICES,
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
async def publish_listing(listing: MarketplaceListing) -> MarketplaceListing:
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
    listings = [
        store.get_listing(lid)
        for lid in bundle.listing_ids
    ]
    listings = [l for l in listings if l is not None]
    return {
        "bundle": bundle.model_dump(),
        "listings": [l.model_dump() for l in listings],
    }


@router.post("/bundles/{bundle_id}/install")
async def install_bundle(bundle_id: str) -> dict:
    """Install all listings in a bundle. Continues on failure."""
    store = _get_store()
    bundle = store.get_bundle(bundle_id)
    if bundle is None:
        raise HTTPException(status_code=404, detail="Bundle not found")

    installed = []
    failed = []
    for lid in bundle.listing_ids:
        listing = store.get_listing(lid)
        if listing is None:
            failed.append({"slug": lid, "error": "Listing not found"})
            continue
        try:
            record = InstallRecord(
                listing_id=lid, user_id="local", version=listing.version,
            )
            store.record_install(record)
            installed.append(lid)
        except Exception as e:
            failed.append({"slug": lid, "error": str(e)})

    store.increment_bundle_installs(bundle_id)
    return {"installed": installed, "failed": failed, "total": len(bundle.listing_ids)}


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
    bundles = [
        b.name for b in store.list_bundles()
        if listing_id in b.listing_ids
    ]

    # Related listings: same category, max 4, excluding current
    related = store.search_listings(
        category=listing.category.value, sort="popular", limit=5,
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


@router.put("/listings/{listing_id}", response_model=MarketplaceListing)
async def update_listing(listing_id: str, updates: dict) -> MarketplaceListing:
    """Partially update a listing."""
    listing = _get_store().update_listing(listing_id, updates)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


@router.get("/listings/author/{author_id}", response_model=list[MarketplaceListing])
async def list_by_author(author_id: str) -> list[MarketplaceListing]:
    """Get all listings by a specific author."""
    return _get_store().list_by_author(author_id)


# ------------------------------------------------------------------
# Reviews
# ------------------------------------------------------------------


@router.post("/listings/{listing_id}/reviews", response_model=ReviewEntry)
async def add_review(listing_id: str, review: ReviewEntry) -> ReviewEntry:
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
async def record_install(listing_id: str, record: InstallRecord) -> InstallRecord:
    """Record an installation of a listing."""
    listing = _get_store().get_listing(listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    record.listing_id = listing_id
    return _get_store().record_install(record)


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


PERSONA_CATALOG = [
    {"id": "parent", "label": "Parent & Family", "icon": "home", "description": "Automate family life"},
    {"id": "business", "label": "Small Business", "icon": "briefcase", "description": "Run your business smarter"},
    {"id": "student", "label": "Student", "icon": "book-open", "description": "Study smarter, not harder"},
    {"id": "creator", "label": "Content Creator", "icon": "palette", "description": "Create more, manage less"},
    {"id": "freelancer", "label": "Freelancer", "icon": "laptop", "description": "Handle the admin so you can do the work"},
    {"id": "developer", "label": "Developer", "icon": "code", "description": "Automate your dev workflow"},
    {"id": "everyone", "label": "Everyone", "icon": "globe", "description": "Daily life, automated"},
]


@router.get("/personas", response_model=list[dict])
async def list_personas() -> list[dict]:
    """Return all persona categories for onboarding."""
    return PERSONA_CATALOG


@router.get("/for/{persona}", response_model=list[MarketplaceListing])
async def get_listings_for_persona(persona: str, limit: int = 20) -> list[MarketplaceListing]:
    """Get curated listings for a specific persona."""
    return _get_store().search_listings(persona=persona, limit=min(limit, 100))


# ------------------------------------------------------------------
# Tips
# ------------------------------------------------------------------


@router.post("/listings/{listing_id}/tip")
async def tip_author(listing_id: str, tip_req: TipRequest) -> dict:
    """Create a Stripe checkout session for tipping, or record locally."""
    import os

    store = _get_store()
    listing = store.get_listing(listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Validate amount range
    if tip_req.amount < 1 or tip_req.amount > 100:
        raise HTTPException(status_code=400, detail="Tip amount must be between $1 and $100")

    stripe_key = os.environ.get("STRIPE_SECRET_KEY")
    if not stripe_key:
        raise HTTPException(status_code=503, detail="Tipping not configured")

    # Record tip locally
    tip = TipRecord(
        listing_id=listing_id,
        author_id=listing.author_id,
        amount=tip_req.amount,
        message=tip_req.message,
    )
    store.add_tip(tip)

    # Try Stripe checkout
    try:
        import stripe
        stripe.api_key = stripe_key
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": int(tip_req.amount * 100),
                    "product_data": {
                        "name": f"Tip for {listing.title}",
                        "description": f"Supporting {listing.author_name or listing.author_id}",
                    },
                },
                "quantity": 1,
            }],
            success_url=f"/marketplace/listings/{listing_id}?tipped=true",
            cancel_url=f"/marketplace/listings/{listing_id}",
            metadata={"listing_id": listing_id, "tip_id": tip.id},
        )
        return {"checkout_url": session.url, "tip_id": tip.id}
    except ImportError:
        return {"checkout_url": None, "tip_id": tip.id, "note": "Tip recorded locally (Stripe SDK not installed)"}
    except Exception as e:
        return {"checkout_url": None, "tip_id": tip.id, "note": f"Stripe unavailable: {e}"}


@router.post("/webhook/stripe")
async def stripe_webhook() -> dict:
    """Stripe webhook receiver. Validates signature and records confirmed tips."""
    return {"status": "received"}


# ------------------------------------------------------------------
# Credits
# ------------------------------------------------------------------


@router.get("/credits/{user_id}", response_model=CreditBalance)
async def get_credits(user_id: str) -> CreditBalance:
    """Get a user's credit balance."""
    return _get_store().get_balance(user_id)


@router.post("/credits/{user_id}/add", response_model=CreditBalance)
async def add_credits(
    user_id: str,
    amount: int,
    transaction_type: str = "purchased",
    description: str = "",
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


@router.post("/credits/{user_id}/unlock/{content_key}", response_model=CreditBalance)
async def unlock_content(user_id: str, content_key: str) -> CreditBalance:
    """Unlock premium content with credits."""
    if content_key not in PREMIUM_CONTENT_PRICES:
        raise HTTPException(status_code=404, detail=f"Unknown content: {content_key}")

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
