import { Link } from "react-router-dom";
import { Bug, GitPullRequest, Puzzle, MessageCircle, BookOpen } from "lucide-react";
import { t, type Lang } from "../i18n";
import { SectionWrapper } from "./SectionWrapper";

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
        {paths.map(({ key, icon: Icon, titleKey, descKey, href, linkLabel, internal }: any) => (
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
                <span aria-hidden style={{ fontSize: "0.75rem" }}>&#8594;</span>
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
                <span aria-hidden style={{ fontSize: "0.75rem" }}>&#8594;</span>
              </a>
            )}
          </div>
        ))}
      </div>

      {/* Discussion + links */}
      <div
        style={{
          marginTop: "var(--space-5)",
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
        @media (max-width: 768px) {
          .community-grid {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </SectionWrapper>
  );
}
