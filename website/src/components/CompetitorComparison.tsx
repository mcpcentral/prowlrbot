import { Check, X, Minus } from "lucide-react";
import { t, type Lang } from "../i18n";
import { SectionWrapper } from "./SectionWrapper";

interface CompetitorComparisonProps {
  lang: Lang;
}

type Support = "yes" | "no" | "partial";

interface Row {
  feature: string;
  prowlrbot: Support;
  manus: Support;
  devin: Support;
  autogpt: Support;
  crewai: Support;
}

const rows: Row[] = [
  {
    feature: "Open Source",
    prowlrbot: "yes",
    manus: "no",
    devin: "no",
    autogpt: "yes",
    crewai: "yes",
  },
  {
    feature: "Self-Hosted",
    prowlrbot: "yes",
    manus: "no",
    devin: "no",
    autogpt: "yes",
    crewai: "yes",
  },
  {
    feature: "Multi-Channel (8)",
    prowlrbot: "yes",
    manus: "no",
    devin: "no",
    autogpt: "no",
    crewai: "no",
  },
  {
    feature: "Multi-Agent War Room",
    prowlrbot: "yes",
    manus: "partial",
    devin: "no",
    autogpt: "no",
    crewai: "partial",
  },
  {
    feature: "Web Monitoring",
    prowlrbot: "yes",
    manus: "no",
    devin: "no",
    autogpt: "no",
    crewai: "no",
  },
  {
    feature: "Provider Agnostic (7)",
    prowlrbot: "yes",
    manus: "no",
    devin: "no",
    autogpt: "partial",
    crewai: "partial",
  },
  {
    feature: "Graduated Autonomy",
    prowlrbot: "yes",
    manus: "no",
    devin: "no",
    autogpt: "no",
    crewai: "no",
  },
  {
    feature: "MCP + A2A Support",
    prowlrbot: "yes",
    manus: "partial",
    devin: "no",
    autogpt: "no",
    crewai: "no",
  },
];

const competitors = [
  { key: "prowlrbot" as const, label: "ProwlrBot" },
  { key: "manus" as const, label: "Manus" },
  { key: "devin" as const, label: "Devin" },
  { key: "autogpt" as const, label: "AutoGPT" },
  { key: "crewai" as const, label: "CrewAI" },
];

const competitorSubtitles: Record<string, string> = {
  manus: "Proprietary, acquired by Meta",
  devin: "15% success rate, $500/mo",
  autogpt: "No multi-agent",
  crewai: "No channels",
};

function StatusIcon({ status }: { status: Support }) {
  if (status === "yes") {
    return (
      <Check
        size={18}
        strokeWidth={2.5}
        style={{ color: "var(--accent)" }}
        aria-label="Supported"
      />
    );
  }
  if (status === "partial") {
    return (
      <Minus
        size={18}
        strokeWidth={2.5}
        style={{ color: "var(--text-muted)" }}
        aria-label="Partial support"
      />
    );
  }
  return (
    <X
      size={18}
      strokeWidth={2.5}
      style={{ color: "#666" }}
      aria-label="Not supported"
    />
  );
}

export function CompetitorComparison({ lang }: CompetitorComparisonProps) {
  return (
    <SectionWrapper
      id="comparison"
      label={t(lang, "comparison.label")}
      title={t(lang, "comparison.title")}
      description={t(lang, "comparison.description")}
    >
      <div
        style={{
          overflowX: "auto",
          border: "1px solid var(--border)",
          borderRadius: "0.75rem",
          background: "var(--surface)",
        }}
      >
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            fontSize: "0.875rem",
            minWidth: "600px",
          }}
        >
          <thead>
            <tr>
              <th
                style={{
                  textAlign: "left",
                  padding: "var(--space-3) var(--space-3)",
                  fontWeight: 600,
                  color: "var(--text-muted)",
                  borderBottom: "1px solid var(--border)",
                  fontSize: "0.75rem",
                  textTransform: "uppercase",
                  letterSpacing: "0.1em",
                }}
              >
                Feature
              </th>
              {competitors.map((c) => (
                <th
                  key={c.key}
                  style={{
                    textAlign: "center",
                    padding: "var(--space-3) var(--space-2)",
                    fontWeight: c.key === "prowlrbot" ? 700 : 600,
                    color:
                      c.key === "prowlrbot" ? "var(--accent)" : "var(--text)",
                    borderBottom: "1px solid var(--border)",
                    fontSize: "0.8125rem",
                    whiteSpace: "nowrap",
                  }}
                >
                  <div>{c.label}</div>
                  {competitorSubtitles[c.key] && (
                    <div
                      style={{
                        fontSize: "0.6875rem",
                        fontWeight: 400,
                        color: "var(--text-muted)",
                        marginTop: "2px",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {competitorSubtitles[c.key]}
                    </div>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr
                key={row.feature}
                className="comparison-row"
                style={{
                  background:
                    i % 2 === 0 ? "transparent" : "rgba(255,255,255,0.01)",
                }}
              >
                <td
                  style={{
                    padding: "var(--space-2) var(--space-3)",
                    fontWeight: 500,
                    color: "var(--text)",
                    borderBottom:
                      i < rows.length - 1 ? "1px solid var(--border)" : "none",
                  }}
                >
                  {row.feature}
                </td>
                {competitors.map((c) => (
                  <td
                    key={c.key}
                    style={{
                      textAlign: "center",
                      padding: "var(--space-2) var(--space-2)",
                      borderBottom:
                        i < rows.length - 1
                          ? "1px solid var(--border)"
                          : "none",
                      background:
                        c.key === "prowlrbot"
                          ? "rgba(0, 229, 255, 0.03)"
                          : "transparent",
                    }}
                  >
                    <StatusIcon status={row[c.key]} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <style>{`
        .comparison-row:hover {
          background: rgba(255,255,255,0.02) !important;
        }
      `}</style>
    </SectionWrapper>
  );
}
