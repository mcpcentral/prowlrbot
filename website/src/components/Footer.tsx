import { Link } from "react-router-dom";
import { Github, BookOpen, MessageCircle } from "lucide-react";
import { type Lang } from "../i18n";

const linkStyle = {
  color: "var(--text-muted)",
  textDecoration: "none",
  transition: "color 0.2s ease",
  display: "inline-flex",
  alignItems: "center",
  gap: "0.375rem",
  fontSize: "0.8125rem",
} as const;

export function Footer({ lang: _lang }: { lang: Lang }) {
  return (
    <footer
      style={{
        marginTop: "auto",
        borderTop: "1px solid var(--border)",
        background: "var(--surface)",
      }}
    >
      <div
        style={{
          maxWidth: "var(--container)",
          margin: "0 auto",
          padding: "var(--space-5) var(--space-4) var(--space-4)",
        }}
      >
        {/* Top row: columns */}
        <div
          className="footer-grid"
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: "var(--space-4)",
            marginBottom: "var(--space-5)",
          }}
        >
          {/* Brand */}
          <div>
            <div
              style={{
                fontWeight: 700,
                fontSize: "1rem",
                color: "var(--text)",
                marginBottom: "var(--space-1)",
              }}
            >
              ProwlrBot
            </div>
            <p
              style={{
                margin: 0,
                fontSize: "0.8125rem",
                color: "var(--text-muted)",
                lineHeight: 1.6,
              }}
            >
              Always watching. Always ready.
            </p>
          </div>

          {/* Resources */}
          <div>
            <div
              style={{
                fontWeight: 600,
                fontSize: "0.75rem",
                color: "var(--text-muted)",
                textTransform: "uppercase",
                letterSpacing: "0.1em",
                marginBottom: "var(--space-2)",
              }}
            >
              Resources
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-1)" }}>
              <a
                href="https://github.com/prowlrbot/prowlrbot"
                target="_blank"
                rel="noopener noreferrer"
                style={linkStyle}
                className="footer-link"
              >
                <Github size={14} strokeWidth={2} aria-hidden />
                GitHub
              </a>
              <Link
                to="/docs"
                style={linkStyle}
                className="footer-link"
              >
                <BookOpen size={14} strokeWidth={2} aria-hidden />
                Docs
              </Link>
              <a
                href="https://github.com/prowlrbot/prowlrbot/discussions"
                target="_blank"
                rel="noopener noreferrer"
                style={linkStyle}
                className="footer-link"
              >
                <MessageCircle size={14} strokeWidth={2} aria-hidden />
                Discussions
              </a>
            </div>
          </div>

          {/* Community */}
          <div>
            <div
              style={{
                fontWeight: 600,
                fontSize: "0.75rem",
                color: "var(--text-muted)",
                textTransform: "uppercase",
                letterSpacing: "0.1em",
                marginBottom: "var(--space-2)",
              }}
            >
              Community
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-1)" }}>
              <a
                href="https://discord.gg/prowlrbot"
                target="_blank"
                rel="noopener noreferrer"
                style={linkStyle}
                className="footer-link"
              >
                Discord
              </a>
              <a
                href="https://x.com/prowlrbot"
                target="_blank"
                rel="noopener noreferrer"
                style={linkStyle}
                className="footer-link"
              >
                X / Twitter
              </a>
              <Link
                to="/docs/contributing"
                style={linkStyle}
                className="footer-link"
              >
                Contributing
              </Link>
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div
          style={{
            borderTop: "1px solid var(--border)",
            paddingTop: "var(--space-3)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "var(--space-2)",
          }}
        >
          <div
            style={{
              fontSize: "0.75rem",
              color: "var(--text-muted)",
              opacity: 0.7,
            }}
          >
            &copy; {new Date().getFullYear()} ProwlrBot. Always watching. Always ready.
          </div>
          <div
            style={{
              fontSize: "0.75rem",
              color: "var(--text-muted)",
              opacity: 0.5,
              display: "flex",
              gap: "var(--space-2)",
            }}
          >
            <span>Privacy</span>
            <span>&middot;</span>
            <span>Terms</span>
          </div>
        </div>
      </div>

      <style>{`
        .footer-link:hover {
          color: var(--accent) !important;
        }
        @media (max-width: 768px) {
          .footer-grid {
            grid-template-columns: 1fr !important;
            gap: var(--space-3) !important;
          }
        }
      `}</style>
    </footer>
  );
}
