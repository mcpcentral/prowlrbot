import { Link } from "react-router-dom";
import {
  Bug,
  GitPullRequest,
  Puzzle,
  MessageCircle,
  BookOpen,
} from "lucide-react";
import { t, type Lang } from "../i18n";
import { SectionWrapper } from "./SectionWrapper";

const DISCORD_INVITE = "https://discord.gg/Mx4ptu2s5J";

function DiscordIcon({ size = 20 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden
    >
      <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" />
    </svg>
  );
}

interface CommunitySectionProps {
  lang: Lang;
}

const paths = [
  {
    key: "bugs",
    icon: Bug,
    titleKey: "community.path.bugs.title",
    descKey: "community.path.bugs.desc",
    href: "https://github.com/prowlrbot/prowlrbot/issues/new?template=bug_report.md",
    linkLabel: "Open an issue",
  },
  {
    key: "prs",
    icon: GitPullRequest,
    titleKey: "community.path.prs.title",
    descKey: "community.path.prs.desc",
    href: "/docs/contributing",
    linkLabel: "Read Contributing Guide",
    internal: true,
  },
  {
    key: "skills",
    icon: Puzzle,
    titleKey: "community.path.skills.title",
    descKey: "community.path.skills.desc",
    href: "https://github.com/prowlrbot/prowlrbot/labels/good%20first%20issue",
    linkLabel: "Good first issues",
  },
];

export function CommunitySection({ lang }: CommunitySectionProps) {
  return (
    <SectionWrapper
      id="community"
      label={t(lang, "community.label")}
      title={t(lang, "community.title")}
      description={t(lang, "community.description")}
    >
      {/* GitHub stars badge */}
      <div style={{ textAlign: "center", marginBottom: "var(--space-5)" }}>
        <a
          href="https://github.com/prowlrbot/prowlrbot"
          target="_blank"
          rel="noopener noreferrer"
        >
          <img
            src="https://img.shields.io/github/stars/prowlrbot/prowlrbot?style=for-the-badge&logo=github&logoColor=white&labelColor=0a0a0f&color=00E5FF"
            alt="GitHub stars"
            style={{ height: "28px", border: "none", boxShadow: "none" }}
          />
        </a>
      </div>

      {/* Contribution paths */}
      <div
        className="community-grid"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "var(--space-3)",
        }}
      >
        {paths.map(
          ({
            key,
            icon: Icon,
            titleKey,
            descKey,
            href,
            linkLabel,
            internal,
          }: any) => (
            <div
              key={key}
              className="community-card"
              style={{
                background: "var(--surface)",
                border: "1px solid var(--border)",
                borderRadius: "0.75rem",
                padding: "var(--space-4)",
                display: "flex",
                flexDirection: "column",
                gap: "var(--space-2)",
                transition: "border-color 0.2s ease, box-shadow 0.2s ease",
              }}
            >
              <div
                className="community-icon"
                style={{
                  color: "var(--text-muted)",
                  transition: "color 0.2s ease",
                }}
              >
                <Icon size={24} strokeWidth={1.5} aria-hidden />
              </div>
              <h3
                style={{
                  margin: 0,
                  fontSize: "0.9375rem",
                  fontWeight: 600,
                  color: "var(--text)",
                }}
              >
                {t(lang, titleKey)}
              </h3>
              <p
                style={{
                  margin: 0,
                  fontSize: "0.8125rem",
                  lineHeight: 1.6,
                  color: "var(--text-muted)",
                  flex: 1,
                }}
              >
                {t(lang, descKey)}
              </p>
              {internal ? (
                <Link
                  to={href}
                  style={{
                    fontSize: "0.8125rem",
                    fontWeight: 600,
                    color: "var(--accent)",
                    textDecoration: "none",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "0.25rem",
                    marginTop: "var(--space-1)",
                  }}
                >
                  {linkLabel}
                  <span aria-hidden style={{ fontSize: "0.75rem" }}>
                    &#8594;
                  </span>
                </Link>
              ) : (
                <a
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    fontSize: "0.8125rem",
                    fontWeight: 600,
                    color: "var(--accent)",
                    textDecoration: "none",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "0.25rem",
                    marginTop: "var(--space-1)",
                  }}
                >
                  {linkLabel}
                  <span aria-hidden style={{ fontSize: "0.75rem" }}>
                    &#8594;
                  </span>
                </a>
              )}
            </div>
          ),
        )}
      </div>

      {/* Discord CTA */}
      <div style={{ marginTop: "var(--space-5)", textAlign: "center" }}>
        <a
          href={DISCORD_INVITE}
          target="_blank"
          rel="noopener noreferrer"
          className="community-discord-cta"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "var(--space-2)",
            padding: "0.875rem 1.5rem",
            fontSize: "1rem",
            fontWeight: 600,
            color: "var(--text)",
            background: "var(--surface)",
            border: "2px solid var(--border)",
            borderRadius: "0.75rem",
            textDecoration: "none",
            transition:
              "border-color 0.2s ease, color 0.2s ease, box-shadow 0.2s ease",
            boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
          }}
        >
          <DiscordIcon size={22} />
          {t(lang, "community.discord")}
        </a>
      </div>

      {/* Discussion + links */}
      <div
        style={{
          marginTop: "var(--space-4)",
          display: "flex",
          justifyContent: "center",
          gap: "var(--space-4)",
          flexWrap: "wrap",
        }}
      >
        <a
          href="https://github.com/prowlrbot/prowlrbot/discussions"
          target="_blank"
          rel="noopener noreferrer"
          className="community-link"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "var(--space-1)",
            padding: "0.625rem 1.25rem",
            fontSize: "0.875rem",
            fontWeight: 600,
            color: "var(--text)",
            background: "transparent",
            border: "1px solid var(--border)",
            borderRadius: "0.5rem",
            textDecoration: "none",
            transition: "border-color 0.2s ease, color 0.2s ease",
          }}
        >
          <MessageCircle size={16} strokeWidth={2} aria-hidden />
          {t(lang, "community.discussions")}
        </a>
        <Link
          to="/docs/contributing"
          className="community-link"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "var(--space-1)",
            padding: "0.625rem 1.25rem",
            fontSize: "0.875rem",
            fontWeight: 600,
            color: "var(--text)",
            background: "transparent",
            border: "1px solid var(--border)",
            borderRadius: "0.5rem",
            textDecoration: "none",
            transition: "border-color 0.2s ease, color 0.2s ease",
          }}
        >
          <BookOpen size={16} strokeWidth={2} aria-hidden />
          {t(lang, "community.contributing")}
        </Link>
      </div>

      <style>{`
        .community-card:hover {
          border-color: var(--accent) !important;
          box-shadow: 0 0 20px var(--accent-dim);
        }
        .community-card:hover .community-icon {
          color: var(--accent) !important;
        }
        .community-link:hover {
          border-color: var(--accent) !important;
          color: var(--accent) !important;
        }
        .community-discord-cta:hover {
          border-color: var(--accent) !important;
          color: var(--accent) !important;
          box-shadow: 0 4px 16px var(--accent-dim) !important;
        }
        @media (max-width: 768px) {
          .community-grid {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </SectionWrapper>
  );
}
