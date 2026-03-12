import { Button, Rate } from "antd";
import { Download } from "lucide-react";
import TrustBadge from "./TrustBadge";
import { formatDownloads } from "../utils";
import type { MarketplaceListing } from "../types";

interface ListingListItemProps {
  listing: MarketplaceListing;
  onInstall: (listing: MarketplaceListing) => void;
  onClick?: (listing: MarketplaceListing) => void;
}

export default function ListingListItem({ listing, onInstall, onClick }: ListingListItemProps) {
  const isTheme = listing.category === "themes";

  return (
    <div
      onClick={() => onClick?.(listing)}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 16,
        padding: "12px 16px",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
        cursor: onClick ? "pointer" : undefined,
        transition: "background 0.15s",
      }}
      onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(255,255,255,0.02)"; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = "transparent"; }}
    >
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontWeight: 600, color: "#fff", fontSize: 14 }}>{listing.name}</span>
          <TrustBadge tier={listing.trustTier} size="small" />
          <span style={{ fontSize: 11, color: "#666" }}>v{listing.version}</span>
        </div>
        <div style={{ fontSize: 12, color: "#888", marginTop: 2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {listing.description}
        </div>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 16, flexShrink: 0 }}>
        <span style={{ fontSize: 12, color: "#888" }}>
          <Download size={11} /> {formatDownloads(listing.downloads)}
        </span>
        <Rate disabled defaultValue={listing.rating} allowHalf style={{ fontSize: 10 }} />
        <span style={{ fontSize: 11, color: "#666" }}>{listing.license}</span>
        <Button
          size="small"
          type={listing.installed ? "default" : "primary"}
          onClick={(e) => { e.stopPropagation(); if (!listing.installed) onInstall(listing); }}
          disabled={listing.installed}
          style={!listing.installed ? { background: "#00e5ff", borderColor: "#00e5ff" } : undefined}
        >
          {listing.installed ? "Installed" : isTheme ? "Apply" : "Install"}
        </Button>
      </div>
    </div>
  );
}
