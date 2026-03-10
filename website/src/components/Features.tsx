import type { LucideProps } from "lucide-react";
import {
  MessageSquare,
  Shield,
  Puzzle,
  Globe,
  Sliders,
  Layers,
  Users,
  Radar,
  Zap,
} from "lucide-react";
import { t, type Lang } from "../i18n";
import { SectionWrapper } from "./SectionWrapper";

const items: Array<{
  key: string;
  icon: React.ComponentType<LucideProps>;
}> = [
  { key: "warroom", icon: Users },
  { key: "channels", icon: MessageSquare },
  { key: "private", icon: Shield },
  { key: "skills", icon: Puzzle },
  { key: "monitoring", icon: Radar },
  { key: "providers", icon: Zap },
  { key: "agentverse", icon: Globe },
  { key: "autonomy", icon: Sliders },
  { key: "roar", icon: Layers },
];

interface FeaturesProps {
  lang: Lang;
}

export function Features({ lang }: FeaturesProps) {
  return (
    <SectionWrapper
      id="features"
      label="Capabilities"
      title={t(lang, "features.title")}
      description="Everything you need to deploy, coordinate, and scale autonomous AI agents across any channel."
    >
      {/* 1px-border grid: bg color shows through 1px gap as borders */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "1px",
          background: "var(--border)",
          borderRadius: "0.75rem",
          overflow: "hidden",
          border: "1px solid var(--border)",
        }}
        className="features-grid"
      >
        {items.map(({ key, icon: Icon }) => (
          <div
            key={key}
            className="feature-card"
            style={{
              background: "var(--bg)",
              padding: "var(--space-5) var(--space-4)",
              transition: "background 0.2s ease",
            }}
          >
            <div
              className="feature-icon"
              style={{
                marginBottom: "var(--space-3)",
                color: "var(--text-muted)",
                transition: "color 0.2s ease",
              }}
            >
              <Icon size={24} strokeWidth={1.5} aria-hidden />
            </div>
            <h3
              style={{
                margin: "0 0 var(--space-1)",
                fontSize: "0.9375rem",
                fontWeight: 600,
                color: "var(--text)",
              }}
            >
              {t(lang, `features.${key}.title`)}
            </h3>
            <p
              style={{
                margin: 0,
                fontSize: "0.8125rem",
                lineHeight: 1.6,
                color: "var(--text-muted)",
              }}
            >
              {t(lang, `features.${key}.desc`)}
            </p>
          </div>
        ))}
      </div>

      <style>{`
        .feature-card:hover {
          background: rgba(255,255,255,0.015) !important;
        }
        .feature-card:hover .feature-icon {
          color: var(--accent) !important;
        }
        @media (max-width: 768px) {
          .features-grid {
            grid-template-columns: 1fr !important;
          }
        }
        @media (min-width: 769px) and (max-width: 1024px) {
          .features-grid {
            grid-template-columns: repeat(2, 1fr) !important;
          }
        }
      `}</style>
    </SectionWrapper>
  );
}
