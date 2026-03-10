import { useState, useEffect, useCallback } from "react";
import {
  Button,
  Alert,
  Descriptions,
  Tag,
  Table,
} from "antd";
import { request } from "../../../api";
import styles from "./index.module.less";

/* ------------------------------------------------------------------ */
/* Types                                                               */
/* ------------------------------------------------------------------ */

interface AuditLogEntry {
  timestamp: string;
  actor: string;
  action: string;
  resource: string;
}

interface RateLimitTier {
  tier: string;
  requests_per_minute: number;
  requests_per_hour: number;
  burst: number;
}

interface TrustLevel {
  level: string;
  description: string;
  allowed_tools: string[];
  network_access: boolean;
  filesystem_access: string;
}

interface HealthStatus {
  status: string;
  jwt_enabled?: boolean;
  session_expiry_minutes?: number;
  uptime_seconds?: number;
  version?: string;
}

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

function statusColor(status: string): string {
  if (status === "healthy" || status === "ok") return "green";
  if (status === "degraded" || status === "warning") return "yellow";
  return "red";
}

function statusDotClass(status: string): string {
  const color = statusColor(status);
  if (color === "green") return styles.statusGreen;
  if (color === "yellow") return styles.statusYellow;
  return styles.statusRed;
}

/* ------------------------------------------------------------------ */
/* Audit Log Columns                                                   */
/* ------------------------------------------------------------------ */

const auditColumns = [
  {
    title: "Timestamp",
    dataIndex: "timestamp",
    key: "timestamp",
    width: 200,
    render: (ts: string) => new Date(ts).toLocaleString(),
  },
  {
    title: "Actor",
    dataIndex: "actor",
    key: "actor",
    width: 150,
  },
  {
    title: "Action",
    dataIndex: "action",
    key: "action",
    width: 180,
    render: (action: string) => {
      const color =
        action.startsWith("delete") || action.startsWith("remove")
          ? "red"
          : action.startsWith("create") || action.startsWith("add")
            ? "green"
            : "blue";
      return <Tag color={color}>{action}</Tag>;
    },
  },
  {
    title: "Resource",
    dataIndex: "resource",
    key: "resource",
    ellipsis: true,
  },
];

/* ------------------------------------------------------------------ */
/* Rate Limit Columns                                                  */
/* ------------------------------------------------------------------ */

const rateLimitColumns = [
  {
    title: "Tier",
    dataIndex: "tier",
    key: "tier",
    render: (tier: string) => <Tag color="purple">{tier}</Tag>,
  },
  {
    title: "Requests / min",
    dataIndex: "requests_per_minute",
    key: "requests_per_minute",
  },
  {
    title: "Requests / hour",
    dataIndex: "requests_per_hour",
    key: "requests_per_hour",
  },
  {
    title: "Burst",
    dataIndex: "burst",
    key: "burst",
  },
];

/* ------------------------------------------------------------------ */
/* Sandbox Trust Level Columns                                         */
/* ------------------------------------------------------------------ */

const trustLevelColumns = [
  {
    title: "Level",
    dataIndex: "level",
    key: "level",
    render: (level: string) => {
      const colorMap: Record<string, string> = {
        untrusted: "red",
        basic: "orange",
        standard: "blue",
        trusted: "green",
        system: "purple",
      };
      return (
        <Tag color={colorMap[level] || "default"} className={styles.trustTag}>
          {level}
        </Tag>
      );
    },
  },
  {
    title: "Description",
    dataIndex: "description",
    key: "description",
    ellipsis: true,
  },
  {
    title: "Network",
    dataIndex: "network_access",
    key: "network_access",
    width: 100,
    render: (v: boolean) =>
      v ? <Tag color="green">Yes</Tag> : <Tag color="red">No</Tag>,
  },
  {
    title: "Filesystem",
    dataIndex: "filesystem_access",
    key: "filesystem_access",
    width: 140,
  },
];

/* ------------------------------------------------------------------ */
/* Default data (shown when API is not yet available)                   */
/* ------------------------------------------------------------------ */

const defaultRateLimits: RateLimitTier[] = [
  { tier: "free", requests_per_minute: 20, requests_per_hour: 200, burst: 5 },
  {
    tier: "standard",
    requests_per_minute: 60,
    requests_per_hour: 1000,
    burst: 15,
  },
  {
    tier: "premium",
    requests_per_minute: 200,
    requests_per_hour: 5000,
    burst: 50,
  },
];

const defaultTrustLevels: TrustLevel[] = [
  {
    level: "untrusted",
    description: "New or unverified skills — no privileged access",
    allowed_tools: ["shell (read-only)"],
    network_access: false,
    filesystem_access: "none",
  },
  {
    level: "basic",
    description: "Community-reviewed skills — limited access",
    allowed_tools: ["shell", "file_read"],
    network_access: false,
    filesystem_access: "read-only",
  },
  {
    level: "standard",
    description: "Verified skills — standard access",
    allowed_tools: ["shell", "file_io", "browser"],
    network_access: true,
    filesystem_access: "workspace only",
  },
  {
    level: "trusted",
    description: "Fully trusted skills — broad access",
    allowed_tools: ["all"],
    network_access: true,
    filesystem_access: "full",
  },
  {
    level: "system",
    description: "Built-in system skills — unrestricted",
    allowed_tools: ["all"],
    network_access: true,
    filesystem_access: "full",
  },
];

/* ------------------------------------------------------------------ */
/* Main Page                                                           */
/* ------------------------------------------------------------------ */

function SecurityPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [rateLimits, setRateLimits] =
    useState<RateLimitTier[]>(defaultRateLimits);
  const [trustLevels, setTrustLevels] =
    useState<TrustLevel[]>(defaultTrustLevels);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch health status — this endpoint should always exist
      const healthData = await request<HealthStatus>("/health").catch(
        () => null,
      );
      setHealth(healthData);

      // Fetch audit logs — may not be implemented yet
      const logs = await request<AuditLogEntry[]>("/audit/logs").catch(
        () => [],
      );
      setAuditLogs(Array.isArray(logs) ? logs : []);

      // Fetch rate limits if available
      const limits = await request<RateLimitTier[]>(
        "/security/rate-limits",
      ).catch(() => null);
      if (Array.isArray(limits) && limits.length > 0) {
        setRateLimits(limits);
      }

      // Fetch trust levels if available
      const levels = await request<TrustLevel[]>(
        "/security/trust-levels",
      ).catch(() => null);
      if (Array.isArray(levels) && levels.length > 0) {
        setTrustLevels(levels);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load security data",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const overallStatus = health?.status || "unknown";

  /* ---- render ---- */

  return (
    <div className={styles.page}>
      {/* ---- Page header ---- */}
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>Security</h2>
        <p className={styles.sectionDesc}>
          Monitor security status, audit trails, authentication, rate limiting,
          and skill sandbox configurations.
        </p>
      </div>

      {loading ? (
        <div className={styles.centerState}>
          <span className={styles.stateText}>Loading security data...</span>
        </div>
      ) : error ? (
        <div className={styles.centerState}>
          <span className={styles.stateTextError}>{error}</span>
          <Button size="small" onClick={fetchData} style={{ marginTop: 12 }}>
            Retry
          </Button>
        </div>
      ) : (
        <>
          {/* ---- Overall Status ---- */}
          <div className={styles.statusRow}>
            <span
              className={`${styles.statusDot} ${statusDotClass(overallStatus)}`}
            />
            <span className={styles.statusLabel}>
              System Status:{" "}
              {overallStatus.charAt(0).toUpperCase() + overallStatus.slice(1)}
            </span>
          </div>

          {/* ---- Authentication ---- */}
          <div className={styles.cardSection}>
            <div className={styles.cardSectionTitle}>Authentication</div>
            <div className={styles.descriptionsBlock}>
              <Descriptions column={2} bordered size="small">
                <Descriptions.Item label="JWT Enabled">
                  <Tag color={health?.jwt_enabled ? "green" : "orange"}>
                    {health?.jwt_enabled ? "Enabled" : "Disabled"}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Session Expiry">
                  {health?.session_expiry_minutes
                    ? `${health.session_expiry_minutes} minutes`
                    : "Not configured"}
                </Descriptions.Item>
                <Descriptions.Item label="Server Version">
                  {health?.version || "Unknown"}
                </Descriptions.Item>
                <Descriptions.Item label="Uptime">
                  {health?.uptime_seconds
                    ? `${Math.floor(health.uptime_seconds / 3600)}h ${Math.floor((health.uptime_seconds % 3600) / 60)}m`
                    : "Unknown"}
                </Descriptions.Item>
              </Descriptions>
            </div>
            {!health?.jwt_enabled && (
              <Alert
                type="warning"
                showIcon
                message="JWT authentication is not enabled. Consider enabling it for production deployments."
                style={{ marginTop: 12 }}
              />
            )}
          </div>

          {/* ---- Audit Trail ---- */}
          <div className={styles.cardSection}>
            <div className={styles.cardSectionTitle}>Audit Trail</div>
            {auditLogs.length === 0 ? (
              <Alert
                type="info"
                showIcon
                message="No audit log entries yet. Audit logging captures security-relevant actions like configuration changes, skill installations, and authentication events."
              />
            ) : (
              <div className={styles.auditTable}>
                <Table
                  dataSource={auditLogs}
                  columns={auditColumns}
                  rowKey={(record, idx) => `${record.timestamp}-${idx}`}
                  size="small"
                  pagination={{ pageSize: 10, showSizeChanger: false }}
                />
              </div>
            )}
          </div>

          {/* ---- Rate Limiting ---- */}
          <div className={styles.cardSection}>
            <div className={styles.cardSectionTitle}>Rate Limiting</div>
            <p style={{ color: "#666", fontSize: 13, marginBottom: 16 }}>
              Current rate limit configurations per tier. These limits apply to
              API requests and agent interactions.
            </p>
            <Table
              dataSource={rateLimits}
              columns={rateLimitColumns}
              rowKey="tier"
              size="small"
              pagination={false}
            />
          </div>

          {/* ---- Skill Sandbox ---- */}
          <div className={styles.cardSection}>
            <div className={styles.cardSectionTitle}>
              Skill Sandbox Trust Levels
            </div>
            <p style={{ color: "#666", fontSize: 13, marginBottom: 16 }}>
              Skills are assigned trust levels that determine their access to
              system resources. Higher trust levels allow more capabilities.
            </p>
            <Table
              dataSource={trustLevels}
              columns={trustLevelColumns}
              rowKey="level"
              size="small"
              pagination={false}
            />
          </div>
        </>
      )}
    </div>
  );
}

export default SecurityPage;
