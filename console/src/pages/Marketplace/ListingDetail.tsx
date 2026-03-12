import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Button, Tabs, Rate, Spin, message, Tag } from "antd";
import { ArrowLeft, Download, Copy, ExternalLink } from "lucide-react";
import { request } from "../../api/request";
import { transformListing, formatDownloads, CATEGORY_COLORS } from "./utils";
import type { ListingDetail as ListingDetailType } from "./types";
import TrustBadge from "./components/TrustBadge";
import ListingCard from "./components/ListingCard";

export default function ListingDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [detail, setDetail] = useState<ListingDetailType | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    request<any>(`/marketplace/listings/${id}/detail`)
      .then((data) => {
        setDetail({
          ...data,
          listing: transformListing(data.listing),
          related: (data.related || []).map(transformListing),
          author_listings: (data.author_listings || []).map(transformListing),
        });
      })
      .catch(() => setDetail(null))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div style={{ padding: 40, textAlign: "center" }}><Spin size="large" /></div>;
  if (!detail) return <div style={{ padding: 40, color: "var(--pb-text-muted)" }}>Listing not found.</div>;

  const { listing } = detail;

  const handleInstall = async () => {
    try {
      await request(`/marketplace/listings/${listing.id}/install`, { method: "POST" });
      message.success(`Installed "${listing.name}"`);
    } catch {
      message.error("Install failed");
    }
  };

  const copyCommand = () => {
    navigator.clipboard.writeText(detail.install_command);
    message.success("Copied to clipboard");
  };

  const tabItems = [
    {
      key: "overview",
      label: "Overview",
      children: (
        <div style={{ color: "var(--pb-market-text-desc)", lineHeight: 1.7 }}>
          <p>{listing.description}</p>
          {listing.compatibility && (
            <p style={{ fontSize: 12, color: "var(--pb-market-text-meta)" }}>
              Compatibility: {listing.compatibility}
            </p>
          )}
          {detail.bundles.length > 0 && (
            <p style={{ fontSize: 12, color: "var(--pb-text-muted)" }}>
              Part of bundle: {detail.bundles.join(", ")}
            </p>
          )}
          <div style={{ marginTop: 12, display: "flex", gap: 6, flexWrap: "wrap" }}>
            {listing.tags.map((t) => (
              <Tag key={t}>{t}</Tag>
            ))}
          </div>
        </div>
      ),
    },
    {
      key: "changelog",
      label: "Changelog",
      children: (
        <pre style={{ color: "var(--pb-market-text-desc)", whiteSpace: "pre-wrap", fontSize: 13 }}>
          {listing.changelog || "No changelog available."}
        </pre>
      ),
    },
    {
      key: "reviews",
      label: `Reviews (${detail.reviews.length})`,
      children: (
        <div>
          {detail.reviews.length === 0 ? (
            <p style={{ color: "var(--pb-market-text-meta)" }}>No reviews yet.</p>
          ) : (
            detail.reviews.map((r) => (
              <div key={r.id} style={{ padding: "12px 0", borderBottom: "1px solid var(--pb-border-light)" }}>
                <Rate disabled defaultValue={r.rating} style={{ fontSize: 12 }} />
                <span style={{ fontSize: 11, color: "var(--pb-market-text-meta)", marginLeft: 8 }}>{r.reviewer_id}</span>
                {r.comment && <p style={{ color: "var(--pb-text-secondary)", fontSize: 13, marginTop: 4 }}>{r.comment}</p>}
              </div>
            ))
          )}
        </div>
      ),
    },
    {
      key: "source",
      label: "Source",
      children: (
        <div style={{ color: "var(--pb-market-text-desc)" }}>
          <p>License: <strong>{listing.license}</strong></p>
          {listing.sourceRepo && (
            <a href={listing.sourceRepo} target="_blank" rel="noopener noreferrer" style={{ color: "var(--pb-market-accent)" }}>
              <ExternalLink size={12} /> View source on GitHub
            </a>
          )}
        </div>
      ),
    },
  ];

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: "24px 16px" }}>
      <Button type="text" onClick={() => navigate("/marketplace")} style={{ color: "var(--pb-text-muted)", marginBottom: 16 }}>
        <ArrowLeft size={14} /> Back to Marketplace
      </Button>

      {/* Header */}
      <div style={{ display: "flex", gap: 16, marginBottom: 24 }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
            <h1 style={{ color: "var(--pb-market-text-name)", fontSize: 24, margin: 0 }}>{listing.name}</h1>
            <TrustBadge tier={listing.trustTier} size="default" />
          </div>
          <div style={{ fontSize: 13, color: "var(--pb-text-muted)" }}>
            by {listing.authorName} &middot; v{listing.version} &middot; {listing.license}
          </div>
          <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
            <Button
              type="primary"
              size="large"
              icon={<Download size={16} />}
              onClick={handleInstall}
              style={{ background: "var(--pb-market-accent)", borderColor: "var(--pb-market-accent)" }}
            >
              {listing.category === "themes" ? "Apply Theme" : "Install"}
            </Button>
            <Button size="large" onClick={copyCommand} icon={<Copy size={14} />}>
              {detail.install_command}
            </Button>
          </div>
        </div>
        <div style={{ textAlign: "right", color: "var(--pb-text-muted)", fontSize: 13 }}>
          <div><Download size={12} /> {formatDownloads(listing.downloads)} downloads</div>
          <div style={{ marginTop: 4 }}>
            <Rate disabled defaultValue={listing.rating} allowHalf style={{ fontSize: 14 }} />
            <span style={{ marginLeft: 4 }}>({listing.ratingCount})</span>
          </div>
          <Tag color={CATEGORY_COLORS[listing.category]} style={{ marginTop: 8 }}>
            {listing.category}
          </Tag>
          {detail.tip_total > 0 && (
            <div style={{ marginTop: 4, color: "var(--pb-accent-gold)" }}>
              ${detail.tip_total.toFixed(2)} in tips
            </div>
          )}
        </div>
      </div>

      {/* Tabbed Content */}
      <Tabs items={tabItems} />

      {/* Related */}
      {detail.related.length > 0 && (
        <div style={{ marginTop: 32 }}>
          <h3 style={{ color: "var(--pb-market-text-name)", fontSize: 15, fontWeight: 600 }}>Related</h3>
          <div style={{ display: "flex", gap: 12, overflowX: "auto" }}>
            {detail.related.map((r) => (
              <div key={r.id} style={{ minWidth: 250 }}>
                <ListingCard
                  listing={r}
                  onInstall={handleInstall}
                  onClick={(l) => navigate(`/marketplace/${l.id}`)}
                />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
