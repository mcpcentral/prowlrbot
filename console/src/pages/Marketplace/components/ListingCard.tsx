import { Button, Rate, Tag } from "antd";
import { Download } from "lucide-react";
import TrustBadge from "./TrustBadge";
import { CATEGORY_COLORS, formatDownloads } from "../utils";
import type { MarketplaceListing } from "../types";
import styles from "../index.module.less";

interface ListingCardProps {
  listing: MarketplaceListing;
  onInstall: (listing: MarketplaceListing) => void;
  onClick?: (listing: MarketplaceListing) => void;
}

export default function ListingCard({ listing, onInstall, onClick }: ListingCardProps) {
  const categoryColor = CATEGORY_COLORS[listing.category] || "default";
  const isTheme = listing.category === "themes";

  return (
    <div
      className={styles.card}
      onClick={() => onClick?.(listing)}
      style={{ cursor: onClick ? "pointer" : undefined }}
    >
      <div className={styles.cardInfo}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
              <h3 className={styles.cardTitle}>{listing.name}</h3>
              <TrustBadge tier={listing.trustTier} />
            </div>
            <p className={styles.cardAuthor}>
              by {listing.authorName || listing.title} &middot; v{listing.version}
            </p>
          </div>
          <Tag color={categoryColor} className={styles.categoryBadge}>
            {listing.category}
          </Tag>
        </div>

        <p className={styles.cardDescription}>{listing.description}</p>

        <div className={styles.cardStats}>
          <span className={styles.rating}>
            <Rate disabled defaultValue={listing.rating} allowHalf style={{ fontSize: 12 }} />
            <span className={styles.ratingCount}>({listing.ratingCount})</span>
          </span>
          <span className={styles.downloads}>
            <Download size={12} />
            {formatDownloads(listing.downloads)}
          </span>
          <span style={{ fontSize: 11, color: "#666" }}>
            {listing.license}
          </span>
        </div>
      </div>

      <div className={styles.cardFooter}>
        <div className={styles.tags}>
          {listing.tags.slice(0, 3).map((tag) => (
            <span key={tag} className={styles.tag}>{tag}</span>
          ))}
        </div>
        <Button
          type={listing.installed ? "default" : "primary"}
          size="small"
          className={`${styles.installButton} ${listing.installed ? styles.installed : ""}`}
          onClick={(e) => {
            e.stopPropagation();
            if (!listing.installed) onInstall(listing);
          }}
          disabled={listing.installed}
          style={!listing.installed ? { background: "#00e5ff", borderColor: "#00e5ff" } : undefined}
        >
          {listing.installed ? "Installed" : isTheme ? "Apply" : "Install"}
        </Button>
      </div>
    </div>
  );
}
