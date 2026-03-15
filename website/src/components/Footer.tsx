import { Link } from "react-router-dom";
import { Github, BookOpen, MessageCircle } from "lucide-react";
import { type Lang } from "../i18n";

const DISCORD_INVITE = "https://discord.gg/Mx4ptu2s5J";

function DiscordIcon({ size = 14 }: { size?: number }) {
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
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "var(--space-1)",
              }}
            >
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
              <Link to="/docs" style={linkStyle} className="footer-link">
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
              <a
                href={DISCORD_INVITE}
                target="_blank"
                rel="noopener noreferrer"
                style={linkStyle}
                className="footer-link"
              >
                <DiscordIcon size={14} />
                Discord
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
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "var(--space-1)",
              }}
            >
              <a
                href={DISCORD_INVITE}
                target="_blank"
                rel="noopener noreferrer"
                style={linkStyle}
                className="footer-link"
              >
                <DiscordIcon size={14} />
                Join Discord
              </a>
              <Link to="/blog" style={linkStyle} className="footer-link">
                Blog
              </Link>
              <a
                href="https://github.com/prowlrbot/prowlrbot/discussions"
                target="_blank"
                rel="noopener noreferrer"
                style={linkStyle}
                className="footer-link"
              >
                Discussions
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
            &copy; {new Date().getFullYear()} ProwlrBot. Always watching. Always
            ready.
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
            <Link
              to="/docs/privacy"
              style={{ color: "inherit", textDecoration: "none" }}
            >
              Privacy
            </Link>
            <span>&middot;</span>
            <Link
              to="/docs/terms"
              style={{ color: "inherit", textDecoration: "none" }}
            >
              Terms
            </Link>
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
