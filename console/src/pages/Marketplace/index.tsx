import { useState, useEffect, useCallback, useRef } from "react";
import { Input, Spin, Select, message } from "antd";
import { Search, LayoutGrid, List, Store } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { request } from "../../api/request";
import { transformListing } from "./utils";
import type { MarketplaceListing, Bundle } from "./types";
import ListingCard from "./components/ListingCard";
import ListingListItem from "./components/ListingListItem";
import CategoryPills from "./components/CategoryPills";
import BundleCard from "./components/BundleCard";
import styles from "./index.module.less";

function MarketplacePage() {
  const navigate = useNavigate();
  const [listings, setListings] = useState<MarketplaceListing[]>([]);
  const [bundles, setBundles] = useState<Bundle[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [categoryCounts, setCategoryCounts] = useState<Record<string, number>>({});
  const [selectedCategory, setSelectedCategory] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [sort, setSort] = useState("popular");
  const [viewMode, setViewMode] = useState<"grid" | "list">(() => {
    return (localStorage.getItem("marketplace-view") as "grid" | "list") || "grid";
  });
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchListings = useCallback(
    async (sortBy: string, category?: string, query?: string) => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        params.set("sort", sortBy);
        if (category) params.set("category", category);
        if (query) params.set("q", query);
        params.set("limit", "200");
        const data = await request<any[]>(`/marketplace/listings?${params.toString()}`);
        const items = Array.isArray(data) ? data.map(transformListing) : [];
        setListings(items);

        if (!category && !query) {
          const counts: Record<string, number> = {};
          items.forEach((l) => { counts[l.category] = (counts[l.category] || 0) + 1; });
          setCategoryCounts(counts);
        }
      } catch {
        setListings([]);
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const fetchCategories = useCallback(async () => {
    try {
      const data = await request<string[]>("/marketplace/categories");
      setCategories(Array.isArray(data) ? data : []);
    } catch {
      setCategories([]);
    }
  }, []);

  const fetchBundles = useCallback(async () => {
    try {
      const data = await request<Bundle[]>("/marketplace/bundles");
      setBundles(Array.isArray(data) ? data : []);
    } catch {
      setBundles([]);
    }
  }, []);

  useEffect(() => {
    fetchCategories();
    fetchBundles();
    fetchListings("popular");
  }, [fetchCategories, fetchBundles, fetchListings]);

  const handleCategorySelect = (category: string) => {
    setSelectedCategory(category);
    fetchListings(sort, category || undefined, searchQuery || undefined);
  };

  const handleSearch = (value: string) => {
    setSearchQuery(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      fetchListings(sort, selectedCategory || undefined, value || undefined);
    }, 400);
  };

  const handleSortChange = (value: string) => {
    setSort(value);
    fetchListings(value, selectedCategory || undefined, searchQuery || undefined);
  };

  const handleViewToggle = (mode: "grid" | "list") => {
    setViewMode(mode);
    localStorage.setItem("marketplace-view", mode);
  };

  const handleInstall = async (listing: MarketplaceListing) => {
    try {
      await request(`/marketplace/listings/${listing.id}/install`, { method: "POST" });
      message.success(`Installed "${listing.name}"`);
      setListings((prev) =>
        prev.map((l) => (l.id === listing.id ? { ...l, installed: true } : l)),
      );
    } catch {
      message.error(`Failed to install "${listing.name}"`);
    }
  };

  const handleListingClick = (listing: MarketplaceListing) => {
    navigate(`/marketplace/${listing.id}`);
  };

  const totalCount = Object.values(categoryCounts).reduce((a, b) => a + b, 0) || listings.length;

  return (
    <div className={styles.marketplace}>
      {/* Hero */}
      <div className={styles.header}>
        <div className={styles.headerInfo}>
          <div className={styles.headerIcon}><Store size={22} /></div>
          <div className={styles.headerText}>
            <h1 className={styles.title}>Prowlr Marketplace</h1>
            <p className={styles.subtitle}>
              Skills, agents, and tools — verified and ready
            </p>
            <p style={{ fontSize: 12, color: "#666", marginTop: 4 }}>
              {totalCount} listings &middot; All reviewed &middot; Official + Verified only
            </p>
          </div>
        </div>
      </div>

      {/* Search */}
      <div className={styles.searchBar}>
        <Input.Search
          placeholder="Search by name, tag, or what you need to do..."
          allowClear
          size="large"
          prefix={<Search size={16} color="#bfbfbf" />}
          value={searchQuery}
          onChange={(e) => handleSearch(e.target.value)}
          onSearch={(value) => {
            if (debounceRef.current) clearTimeout(debounceRef.current);
            fetchListings(sort, selectedCategory || undefined, value || undefined);
          }}
        />
      </div>

      {/* Category Pills */}
      <CategoryPills
        categories={categories}
        counts={categoryCounts}
        selected={selectedCategory}
        onSelect={handleCategorySelect}
        totalCount={totalCount}
      />

      {/* Bundles */}
      {bundles.length > 0 && !searchQuery && (
        <div style={{ marginBottom: 24 }}>
          <h3 style={{ color: "#fff", fontSize: 15, fontWeight: 600, marginBottom: 12 }}>
            Curated Bundles
          </h3>
          <div style={{ display: "flex", gap: 12, overflowX: "auto", paddingBottom: 8 }}>
            {bundles.map((b) => (
              <BundleCard key={b.id} bundle={b} />
            ))}
          </div>
        </div>
      )}

      {/* Sort + View Toggle */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h3 style={{ color: "#fff", fontSize: 15, fontWeight: 600, margin: 0 }}>
          All Listings
        </h3>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <Select
            value={sort}
            onChange={handleSortChange}
            size="small"
            style={{ width: 120 }}
            options={[
              { label: "Popular", value: "popular" },
              { label: "Top Rated", value: "top_rated" },
              { label: "Newest", value: "newest" },
              { label: "A-Z", value: "alpha" },
            ]}
          />
          <div style={{ display: "flex", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 6 }}>
            <button
              onClick={() => handleViewToggle("grid")}
              style={{
                padding: "4px 8px",
                background: viewMode === "grid" ? "rgba(0,229,255,0.1)" : "transparent",
                border: "none",
                cursor: "pointer",
                color: viewMode === "grid" ? "#00e5ff" : "#666",
                borderRadius: "5px 0 0 5px",
              }}
            >
              <LayoutGrid size={14} />
            </button>
            <button
              onClick={() => handleViewToggle("list")}
              style={{
                padding: "4px 8px",
                background: viewMode === "list" ? "rgba(0,229,255,0.1)" : "transparent",
                border: "none",
                cursor: "pointer",
                color: viewMode === "list" ? "#00e5ff" : "#666",
                borderRadius: "0 5px 5px 0",
              }}
            >
              <List size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* Listings */}
      {loading ? (
        <div className={styles.loadingContainer}><Spin size="large" /></div>
      ) : listings.length > 0 ? (
        viewMode === "grid" ? (
          <div className={styles.grid}>
            {listings.map((listing) => (
              <ListingCard
                key={listing.id}
                listing={listing}
                onInstall={handleInstall}
                onClick={handleListingClick}
              />
            ))}
          </div>
        ) : (
          <div>
            {listings.map((listing) => (
              <ListingListItem
                key={listing.id}
                listing={listing}
                onInstall={handleInstall}
                onClick={handleListingClick}
              />
            ))}
          </div>
        )
      ) : (
        <div className={styles.emptyState}>
          <div className={styles.emptyText}>
            {searchQuery
              ? `No results for "${searchQuery}"`
              : "No listings available yet. Run 'prowlr market update' to sync."}
          </div>
        </div>
      )}
    </div>
  );
}

export default MarketplacePage;
