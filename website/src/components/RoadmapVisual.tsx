import { CheckCircle2, Loader2, Rocket } from "lucide-react";
import { t, type Lang } from "../i18n";
import { SectionWrapper } from "./SectionWrapper";

interface RoadmapVisualProps {
  lang: Lang;
}

const phases = [
  {
    key: "phase1",
    status: "done" as const,
    icon: CheckCircle2,
    titleKey: "roadmap.phase1.title",
    subtitleKey: "roadmap.phase1.subtitle",
    itemsKey: "roadmap.phase1.items",
    statusLabel: "DONE",
    statusColor: "var(--accent)",
  },
  {
    key: "phase2",
    status: "progress" as const,
    icon: Loader2,
    titleKey: "roadmap.phase2.title",
    subtitleKey: "roadmap.phase2.subtitle",
    itemsKey: "roadmap.phase2.items",
    statusLabel: "IN PROGRESS",
    statusColor: "#f59e0b",
  },
  {
    key: "phase3",
    status: "coming" as const,
    icon: Rocket,
    titleKey: "roadmap.phase3.title",
    subtitleKey: "roadmap.phase3.subtitle",
    itemsKey: "roadmap.phase3.items",
    statusLabel: "COMING",
    statusColor: "#8b5cf6",
  },
];

export function RoadmapVisual({ lang }: RoadmapVisualProps) {
  return (
    <SectionWrapper
      id="roadmap"
      label={t(lang, "roadmap.label")}
      title={t(lang, "roadmap.title")}
      description={t(lang, "roadmap.description")}
    >
      <div
        className="roadmap-grid"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "var(--space-3)",
          position: "relative",
        }}
      >
        {phases.map(
          ({
            key,
            icon: Icon,
            titleKey,
            subtitleKey,
            itemsKey,
            statusLabel,
            statusColor,
            status,
          }) => (
            <div
              key={key}
              className="roadmap-card"
              style={{
                background: "var(--surface)",
                border: "1px solid var(--border)",
                borderRadius: "0.75rem",
                padding: "var(--space-4)",
                display: "flex",
                flexDirection: "column",
                gap: "var(--space-2)",
                position: "relative",
                overflow: "hidden",
                transition: "border-color 0.2s ease, box-shadow 0.2s ease",
              }}
            >
              {/* Top accent line */}
              <div
                aria-hidden
                style={{
                  position: "absolute",
                  top: 0,
                  left: 0,
                  right: 0,
                  height: "2px",
                  background: statusColor,
                  opacity: status === "done" ? 1 : 0.5,
                }}
              />

              {/* Status badge */}
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.375rem",
                  alignSelf: "flex-start",
                  padding: "0.2rem 0.625rem",
                  fontSize: "0.625rem",
                  fontWeight: 600,
                  fontFamily: "ui-monospace, 'SF Mono', Menlo, monospace",
                  letterSpacing: "0.1em",
                  color: statusColor,
                  background: `${statusColor}15`,
                  border: `1px solid ${statusColor}30`,
                  borderRadius: "9999px",
                }}
              >
                <Icon
                  size={12}
                  strokeWidth={2}
                  aria-hidden
                  style={
                    status === "progress"
                      ? { animation: "spin 2s linear infinite" }
                      : undefined
                  }
                />
                {statusLabel}
              </div>

              <h3
                style={{
                  margin: 0,
                  fontSize: "1.125rem",
                  fontWeight: 700,
                  color: "var(--text)",
                }}
              >
                {t(lang, titleKey)}
              </h3>

              <p
                style={{
                  margin: 0,
                  fontSize: "0.8125rem",
                  fontWeight: 500,
                  color: "var(--text-muted)",
                }}
              >
                {t(lang, subtitleKey)}
              </p>

              <ul
                style={{
                  margin: "var(--space-1) 0 0 0",
                  padding: 0,
                  listStyle: "none",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.375rem",
                }}
              >
                {t(lang, itemsKey)
                  .split("|")
                  .map((item, i) => (
                    <li
                      key={i}
                      style={{
                        fontSize: "0.8125rem",
                        color: "var(--text-muted)",
                        paddingLeft: "var(--space-2)",
                        position: "relative",
                      }}
                    >
                      <span
                        aria-hidden
                        style={{
                          position: "absolute",
                          left: 0,
                          top: "0.55em",
                          width: "4px",
                          height: "4px",
                          borderRadius: "50%",
                          background: statusColor,
                          opacity: 0.6,
                        }}
                      />
                      {item.trim()}
                    </li>
                  ))}
              </ul>
            </div>
          ),
        )}
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .roadmap-card:hover {
          border-color: var(--accent) !important;
          box-shadow: 0 0 20px var(--accent-dim);
        }
        @media (max-width: 768px) {
          .roadmap-grid {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </SectionWrapper>
  );
}
