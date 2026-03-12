"""Tests for MarketplaceStore v3 migration and trust tier fields."""
import tempfile

from prowlrbot.marketplace.models import MarketplaceCategory, MarketplaceListing, TrustTier
from prowlrbot.marketplace.store import MarketplaceStore


def _tmp_store():
    """Create a store backed by a temp file."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    return MarketplaceStore(db_path=tmp.name)


def test_v3_columns_exist():
    """v3 migration creates trust_tier and related columns."""
    store = _tmp_store()
    cur = store._conn.cursor()
    cols = {row["name"] for row in cur.execute("PRAGMA table_info(listings)").fetchall()}
    assert "trust_tier" in cols
    assert "author_name" in cols
    assert "source_repo" in cols
    assert "license" in cols
    assert "changelog" in cols
    assert "compatibility" in cols
    assert "author_url" in cols
    assert "author_avatar_url" in cols
    store.close()


def test_publish_and_read_v3_fields():
    """publish_listing() stores v3 fields, get_listing() reads them back."""
    store = _tmp_store()
    listing = MarketplaceListing(
        author_id="prowlrbot",
        title="Test Skill",
        description="A test",
        category=MarketplaceCategory.skills,
        trust_tier="official",
        author_name="ProwlrBot",
        author_url="https://github.com/ProwlrBot",
        author_avatar_url="https://avatars.githubusercontent.com/ProwlrBot",
        source_repo="https://github.com/ProwlrBot/prowlrbot",
        license="MIT",
        changelog="## 1.0.0\nInitial",
        compatibility=">=1.0.0",
    )
    published = store.publish_listing(listing)
    fetched = store.get_listing(published.id)
    assert fetched is not None
    assert fetched.trust_tier == TrustTier.official
    assert fetched.author_name == "ProwlrBot"
    assert fetched.license == "MIT"
    assert fetched.source_repo == "https://github.com/ProwlrBot/prowlrbot"
    store.close()


def test_update_listing_v3_fields():
    """update_listing() can update trust_tier and author_name."""
    store = _tmp_store()
    listing = MarketplaceListing(
        author_id="test",
        title="Updatable",
        description="test",
        category=MarketplaceCategory.agents,
    )
    store.publish_listing(listing)
    updated = store.update_listing(listing.id, {
        "trust_tier": "official",
        "author_name": "Updated Author",
        "license": "Apache-2.0",
    })
    assert updated is not None
    assert updated.trust_tier == TrustTier.official
    assert updated.author_name == "Updated Author"
    assert updated.license == "Apache-2.0"
    store.close()
