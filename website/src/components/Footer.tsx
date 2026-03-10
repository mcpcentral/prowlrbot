import { type Lang } from "../i18n";

export function Footer({ lang: _lang }: { lang: Lang }) {
  return (
    <footer
      style={{
        marginTop: "auto",
        padding: "var(--space-4) var(--space-4)",
        borderTop: "1px solid var(--border)",
        textAlign: "center",
        fontSize: "0.875rem",
        color: "var(--text-muted)",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          gap: "var(--space-4)",
          flexWrap: "wrap",
          marginBottom: "var(--space-3)",
        }}
      >
        <a
          href="https://github.com/mcpcentral/prowlrbot"
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: "inherit", transition: "color 0.2s" }}
          onMouseEnter={(e) => (e.currentTarget.style.color = "var(--accent)")}
          onMouseLeave={(e) =>
            (e.currentTarget.style.color = "var(--text-muted)")
          }
        >
          GitHub
        </a>
        <a
          href="https://github.com/mcpcentral/roar-protocol"
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: "inherit", transition: "color 0.2s" }}
          onMouseEnter={(e) => (e.currentTarget.style.color = "var(--accent)")}
          onMouseLeave={(e) =>
            (e.currentTarget.style.color = "var(--text-muted)")
          }
        >
          ROAR Protocol
        </a>
        <a
          href="https://github.com/mcpcentral/prowlr-marketplace"
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: "inherit", transition: "color 0.2s" }}
          onMouseEnter={(e) => (e.currentTarget.style.color = "var(--accent)")}
          onMouseLeave={(e) =>
            (e.currentTarget.style.color = "var(--text-muted)")
          }
        >
          Marketplace
        </a>
        <a
          href="https://github.com/mcpcentral/agentverse"
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: "inherit", transition: "color 0.2s" }}
          onMouseEnter={(e) => (e.currentTarget.style.color = "var(--accent)")}
          onMouseLeave={(e) =>
            (e.currentTarget.style.color = "var(--text-muted)")
          }
        >
          AgentVerse
        </a>
      </div>
      <div style={{ fontSize: "0.8125rem", opacity: 0.7 }}>
        &copy; {new Date().getFullYear()} ProwlrBot. Always watching. Always
        ready.
      </div>
    </footer>
  );
}
