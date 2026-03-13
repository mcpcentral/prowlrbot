import { useEffect, useState } from "react";
import { Space } from "antd";
import api from "../api";

const POLL_MS = 5_000;

const AUTONOMY_LABELS: Record<string, string> = {
  observe: "Observe",
  guide: "Guide",
  act: "Act",
};

export default function StatusLine() {
  const [active, setActive] = useState(false);
  const [autonomy, setAutonomy] = useState("guide");
  const [heartbeat, setHeartbeat] = useState<string | null>(null);
  const [version, setVersion] = useState("");

  useEffect(() => {
    const poll = async () => {
      try {
        const v = await api.getVersion();
        setVersion(v?.version ?? "");
      } catch {
        // ignore
      }
      try {
        await api.getAgentRunningConfig();
        setActive(true);
      } catch {
        setActive(false);
      }
      try {
        const cfg = await api.getAgentRunningConfig() as any;
        if (cfg?.autonomy) setAutonomy(cfg.autonomy as string);
      } catch {
        // ignore
      }
      try {
        const hb = await (api as any).getHeartbeatConfig?.();
        if (hb?.enabled) setHeartbeat(new Date().toLocaleTimeString());
      } catch {
        // ignore
      }
    };

    poll();
    const id = setInterval(poll, POLL_MS);
    return () => clearInterval(id);
  }, []);

  return (
    <div
      style={{
        height: 30,
        background: "var(--pb-bg-elevated)",
        borderTop: "1px solid var(--pb-border)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 16px",
        fontSize: 11,
        color: "var(--pb-text-secondary)",
        flexShrink: 0,
        userSelect: "none",
      }}
    >
      <Space size={8}>
        <span style={{ color: active ? "var(--pb-status-success)" : "var(--pb-status-error)", fontSize: 8 }}>●</span>
        <span>ProwlrBot</span>
      </Space>
      <span>Autonomy: {AUTONOMY_LABELS[autonomy] ?? autonomy}</span>
      <Space size={12}>
        {heartbeat && <span>♥ {heartbeat}</span>}
        {version && <span>v{version}</span>}
      </Space>
    </div>
  );
}
