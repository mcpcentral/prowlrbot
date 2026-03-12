"""Tests for marketplace model enums and new fields."""
from prowlrbot.marketplace.models import MarketplaceCategory, MarketplaceListing, TrustTier


def test_specs_category_exists():
    """specs must be a valid MarketplaceCategory."""
    cat = MarketplaceCategory("specs")
    assert cat == MarketplaceCategory.specs
    assert cat.value == "specs"


def test_all_seven_categories():
    """All 7 categories are present."""
    expected = {"skills", "agents", "prompts", "mcp-servers", "themes", "workflows", "specs"}
    actual = {c.value for c in MarketplaceCategory}
    assert actual == expected


def test_trust_tier_enum():
    from prowlrbot.marketplace.models import TrustTier
    assert TrustTier("official") == TrustTier.official
    assert TrustTier("verified") == TrustTier.verified


def test_listing_has_v3_fields():
    """MarketplaceListing should have trust_tier, author_name, etc."""
    listing = MarketplaceListing(
        author_id="test",
        title="Test",
        description="desc",
        category=MarketplaceCategory.skills,
        trust_tier="official",
        author_name="ProwlrBot",
        author_url="https://github.com/ProwlrBot",
        author_avatar_url="",
        source_repo="https://github.com/ProwlrBot/prowlrbot",
        license="MIT",
        changelog="## 1.0.0\nInitial release",
        compatibility=">=1.0.0",
    )
    assert listing.trust_tier == TrustTier.official
    assert listing.author_name == "ProwlrBot"
    assert listing.license == "MIT"
