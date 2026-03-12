import { Button, message } from "antd";
import { Download } from "lucide-react";
import { useState } from "react";
import { request } from "../../../api/request";
import type { Bundle } from "../types";

interface BundleCardProps {
  bundle: Bundle;
  onInstalled?: () => void;
}

export default function BundleCard({ bundle, onInstalled }: BundleCardProps) {
  const [installing, setInstalling] = useState(false);

  const handleInstall = async () => {
    setInstalling(true);
    try {
      const result = await request<{ installed: string[]; failed: { slug: string; error: string }[] }>(
        `/marketplace/bundles/${bundle.id}/install`,
        { method: "POST" },
      );
      const count = result.installed?.length ?? 0;
      message.success(`Installed ${count} items from "${bundle.name}"`);
      onInstalled?.();
    } catch {
      message.error(`Failed to install bundle "${bundle.name}"`);
    } finally {
      setInstalling(false);
    }
  };

  return (
    <div
      style={{
        background: `linear-gradient(135deg, ${bundle.color}15, ${bundle.color}08)`,
        border: `1px solid ${bundle.color}30`,
        borderRadius: 12,
        padding: "16px 20px",
        minWidth: 200,
        cursor: "pointer",
        transition: "transform 0.2s, box-shadow 0.2s",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = "translateY(-2px)";
        e.currentTarget.style.boxShadow = `0 4px 12px ${bundle.color}20`;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = "translateY(0)";
        e.currentTarget.style.boxShadow = "none";
      }}
    >
      <div style={{ fontSize: 24, marginBottom: 8 }}>{bundle.emoji}</div>
      <div style={{ fontWeight: 600, fontSize: 14, color: "#fff", marginBottom: 4 }}>
        {bundle.name}
      </div>
      <div style={{ fontSize: 12, color: "#888", marginBottom: 12 }}>
        {bundle.description}
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: 11, color: "#666" }}>
          {bundle.listing_ids.length} items
        </span>
        <Button
          size="small"
          type="primary"
          loading={installing}
          onClick={(e) => { e.stopPropagation(); handleInstall(); }}
          icon={<Download size={12} />}
          style={{ background: "#00e5ff", borderColor: "#00e5ff", fontSize: 11 }}
        >
          Install All
        </Button>
      </div>
    </div>
  );
}
