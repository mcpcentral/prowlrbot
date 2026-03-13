import { useEffect, useState } from "react";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import {
  getAnalyticsSummary,
  getCostOverTime,
  getModelBreakdown,
  getRecentUsage,
} from "../../api";
import type {
  UsageSummary,
  CostDataPoint,
  ModelStats,
  UsageStat,
} from "../../api/modules/analytics";
import styles from "./index.module.less";

type Period = "day" | "week" | "month" | "all";

function formatCost(val: number): string {
  return `$${val.toFixed(2)}`;
}

function formatTokens(val: number): string {
  if (val >= 1_000_000) return `${(val / 1_000_000).toFixed(1)}M`;
  if (val >= 1_000) return `${(val / 1_000).toFixed(0)}K`;
  return String(val);
}

function timeAgo(iso: string): string {
  const secs = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (secs < 60) return "now";
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
  if (secs < 86400) return `${Math.floor(secs / 3600)}h ago`;
  return `${Math.floor(secs / 86400)}d ago`;
}

const PERIOD_DAYS: Record<Period, number> = {
  day: 1,
  week: 7,
  month: 30,
  all: 365,
};

export default function AnalyticsPage() {
  const [period, setPeriod] = useState<Period>("week");
  const [summary, setSummary] = useState<UsageSummary | null>(null);
  const [costData, setCostData] = useState<CostDataPoint[]>([]);
  const [models, setModels] = useState<Record<string, ModelStats>>({});
  const [recent, setRecent] = useState<UsageStat[]>([]);

  useEffect(() => {
    getAnalyticsSummary(period).then(setSummary).catch(() => {});
    getCostOverTime(PERIOD_DAYS[period]).then(setCostData).catch(() => {});
    getModelBreakdown().then(setModels).catch(() => {});
    getRecentUsage(30).then((r) => { if (Array.isArray(r)) setRecent(r); }).catch(() => {});
  }, [period]);

  const modelEntries = Object.entries(models).sort(([, a], [, b]) => b.total_cost - a.total_cost);

  const ChartTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;
    return (
      <div style={{ background: "var(--pb-bg-card)", border: "1px solid var(--pb-border)", borderRadius: 8, padding: "8px 12px", fontSize: 12 }}>
        <div style={{ color: "var(--pb-text-tertiary)", marginBottom: 4 }}>{label}</div>
        {payload.map((p: any) => (
          <div key={p.dataKey} style={{ color: p.color }}>
            {p.name}: {p.dataKey === "cost" ? formatCost(p.value) : formatTokens(p.value)}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className={styles.analytics}>
      {/* Header */}
      <div className={styles.header}>
        <div>
          <div className={styles.headerTitle}>Analytics</div>
          <div className={styles.headerBreadcrumb}>
            Dashboard / Analytics
            {summary ? ` \u00b7 ${summary.total_queries} queries` : ""}
          </div>
        </div>
        <div className={styles.periodTabs}>
          {(["day", "week", "month", "all"] as Period[]).map((p) => (
            <button
              key={p}
              className={`${styles.periodTab} ${period === p ? styles.periodTabActive : ""}`}
              onClick={() => setPeriod(p)}
            >
              {p === "all" ? "All" : p.charAt(0).toUpperCase() + p.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className={styles.grid}>
        {/* Stat cards */}
        <div className={`${styles.panel} ${styles.col1}`}>
          <div className={styles.statPanel}>
            <div className={styles.statValue} style={{ color: "var(--pb-accent-blue)" }}>
              {summary?.total_queries ?? "\u2014"}
            </div>
            <div className={styles.statLabel}>Total Queries</div>
          </div>
        </div>
        <div className={`${styles.panel} ${styles.col1}`}>
          <div className={styles.statPanel}>
            <div className={styles.statValue} style={{ color: "var(--pb-status-success)" }}>
              {summary ? formatCost(summary.total_cost) : "\u2014"}
            </div>
            <div className={styles.statLabel}>Total Cost</div>
          </div>
        </div>
        <div className={`${styles.panel} ${styles.col1}`}>
          <div className={styles.statPanel}>
            <div className={styles.statValue} style={{ color: "var(--pb-text-secondary)" }}>
              {summary ? formatTokens(summary.total_tokens) : "\u2014"}
            </div>
            <div className={styles.statLabel}>Total Tokens</div>
          </div>
        </div>
        <div className={`${styles.panel} ${styles.col1}`}>
          <div className={styles.statPanel}>
            <div className={styles.statValue} style={{ color: "var(--pb-accent-orange)" }}>
              {summary ? `${Math.round(summary.avg_latency_ms)}ms` : "\u2014"}
            </div>
            <div className={styles.statLabel}>Avg Latency</div>
          </div>
        </div>

        {/* Cost over time chart */}
        <div className={`${styles.panel} ${styles.col2}`}>
          <div className={styles.panelHeader}>
            <div className={styles.panelTitle}>Cost Over Time</div>
          </div>
          <div className={styles.panelBody} style={{ height: 240 }}>
            {costData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={costData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid stroke="var(--pb-border)" strokeDasharray="4 4" />
                  <XAxis
                    dataKey="date"
                    tick={{ fill: "var(--pb-text-tertiary)", fontSize: 11 }}
                    axisLine={{ stroke: "var(--pb-border)" }}
                    tickLine={false}
                    tickFormatter={(v) => {
                      const d = new Date(v);
                      return `${d.getMonth() + 1}/${d.getDate()}`;
                    }}
                  />
                  <YAxis
                    tick={{ fill: "var(--pb-text-tertiary)", fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(v) => `$${v}`}
                  />
                  <Tooltip content={<ChartTooltip />} />
                  <defs>
                    <linearGradient id="costGradAnalytics" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--pb-accent-purple)" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="var(--pb-accent-purple)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <Area type="monotone" dataKey="cost" stroke="var(--pb-accent-purple)" strokeWidth={2} fill="url(#costGradAnalytics)" name="Cost" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className={styles.emptyState}>No cost data available for this period</div>
            )}
          </div>
        </div>

        {/* Token usage bar chart */}
        <div className={`${styles.panel} ${styles.col2}`}>
          <div className={styles.panelHeader}>
            <div className={styles.panelTitle}>Token Usage</div>
          </div>
          <div className={styles.panelBody} style={{ height: 240 }}>
            {costData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={costData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid stroke="var(--pb-border)" strokeDasharray="4 4" />
                  <XAxis
                    dataKey="date"
                    tick={{ fill: "var(--pb-text-tertiary)", fontSize: 11 }}
                    axisLine={{ stroke: "var(--pb-border)" }}
                    tickLine={false}
                    tickFormatter={(v) => {
                      const d = new Date(v);
                      return `${d.getMonth() + 1}/${d.getDate()}`;
                    }}
                  />
                  <YAxis
                    tick={{ fill: "var(--pb-text-tertiary)", fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(v) => formatTokens(v)}
                  />
                  <Tooltip content={<ChartTooltip />} />
                  <Bar dataKey="tokens" fill="var(--pb-accent-purple)" radius={[4, 4, 0, 0]} name="Tokens" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className={styles.emptyState}>No token data available for this period</div>
            )}
          </div>
        </div>

        {/* Model breakdown table */}
        <div className={`${styles.panel} ${styles.col2}`}>
          <div className={styles.panelHeader}>
            <div className={styles.panelTitle}>Model Breakdown</div>
          </div>
          <div className={styles.panelBody}>
            {modelEntries.length > 0 ? (
              <table className={styles.modelTable}>
                <thead>
                  <tr>
                    <th>Model</th>
                    <th>Queries</th>
                    <th>Tokens</th>
                    <th>Latency</th>
                    <th>Cost</th>
                  </tr>
                </thead>
                <tbody>
                  {modelEntries.map(([name, stats]) => (
                    <tr key={name}>
                      <td className={styles.modelName}>{name}</td>
                      <td className={styles.modelValue}>{stats.query_count}</td>
                      <td className={styles.modelValue}>
                        {formatTokens(stats.input_tokens + stats.output_tokens)}
                      </td>
                      <td className={styles.modelValue}>{Math.round(stats.avg_latency_ms)}ms</td>
                      <td className={styles.modelCost}>{formatCost(stats.total_cost)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className={styles.emptyState}>No model data yet</div>
            )}
          </div>
        </div>

        {/* Recent usage */}
        <div className={`${styles.panel} ${styles.col2}`}>
          <div className={styles.panelHeader}>
            <div className={styles.panelTitle}>Recent Queries</div>
          </div>
          <div className={`${styles.panelBody} ${styles.scrollBody}`}>
            {recent.length > 0 ? (
              recent.map((r) => (
                <div key={r.id} className={styles.recentItem}>
                  <span className={styles.recentModel}>{r.model}</span>
                  <span className={styles.recentTokens}>
                    {formatTokens(r.input_tokens + r.output_tokens)} tokens
                  </span>
                  <span className={styles.recentCost}>{formatCost(r.cost)}</span>
                  <span className={styles.recentTime}>{timeAgo(r.timestamp)}</span>
                </div>
              ))
            ) : (
              <div className={styles.emptyState}>No recent queries</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
