import { Tag } from "antd";

interface TrustBadgeProps {
  tier: string;
  size?: "small" | "default";
}

export default function TrustBadge({ tier, size = "small" }: TrustBadgeProps) {
  if (tier === "official") {
    return (
      <Tag
        color="gold"
        style={{
          color: "var(--pb-text-primary)",
          fontWeight: 600,
          fontSize: size === "small" ? 10 : 12,
          lineHeight: size === "small" ? "18px" : "22px",
          border: "none",
        }}
      >
        OFFICIAL
      </Tag>
    );
  }
  return (
    <Tag
      color="blue"
      style={{
        color: "var(--pb-text-primary)",
        fontWeight: 600,
        fontSize: size === "small" ? 10 : 12,
        lineHeight: size === "small" ? "18px" : "22px",
        border: "none",
      }}
    >
      VERIFIED
    </Tag>
  );
}
