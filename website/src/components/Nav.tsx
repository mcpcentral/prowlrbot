import { useState } from "react";
import { Link } from "react-router-dom";
import { Menu, X, BookOpen, Github } from "lucide-react";
import { t, type Lang } from "../i18n";

interface NavProps {
  projectName: string;
  lang: Lang;
  onLangClick: () => void;
  docsPath: string;
  repoUrl: string;
}

export function Nav({
  projectName,
  lang,
  onLangClick: _onLangClick,
  docsPath,
  repoUrl: _repoUrl,
}: NavProps) {
  const [open, setOpen] = useState(false);
  const linkClass =
    "nav-item text-[var(--text-muted)] hover:text-[var(--text)] transition-colors";
  return (
    <header
      style={{
        position: "sticky",
        top: 0,
        zIndex: 10,
        background: "rgba(10, 10, 15, 0.92)",
        backdropFilter: "blur(12px)",
        borderBottom: "1px solid var(--border)",
      }}
    >
      <nav
        style={{
          margin: "0 auto",
          maxWidth: "var(--container)",
          padding: "var(--space-2) var(--space-4)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "var(--space-3)",
        }}
      >
        <Link
          to="/"
          className="nav-brand-link"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "var(--space-2)",
            fontWeight: 700,
            fontSize: "1.125rem",
            color: "var(--text)",
          }}
          aria-label={projectName}
        >
          <img
            src="/prowlrlogo.png"
            alt={projectName}
            style={{ height: 36, width: "auto" }}
          />
        </Link>
        <div
          className="nav-links"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "var(--space-4)",
          }}
        >
          <Link
            to={docsPath.replace(/\/$/, "") || "/docs"}
            className={linkClass}
          >
            <BookOpen size={18} strokeWidth={1.5} aria-hidden />
            <span>{t(lang, "nav.docs")}</span>
          </Link>
          <a
            href="https://github.com/mcpcentral/prowlrbot"
            target="_blank"
            rel="noopener noreferrer"
            className={linkClass}
            title="ProwlrBot on GitHub"
          >
            <Github size={18} strokeWidth={1.5} aria-hidden />
            <span>{t(lang, "nav.github")}</span>
          </a>
        </div>
        <button
          type="button"
          className="nav-mobile-toggle"
          onClick={() => setOpen((o) => !o)}
          aria-expanded={open}
          aria-label={open ? "Close menu" : "Open menu"}
          style={{
            display: "none",
            background: "none",
            border: "none",
            padding: "var(--space-2)",
            color: "var(--text)",
          }}
        >
          {open ? <X size={24} /> : <Menu size={24} />}
        </button>
      </nav>
      <div
        className="nav-mobile"
        style={{
          display: open ? "flex" : "none",
          padding: "var(--space-2) var(--space-4)",
          borderTop: "1px solid var(--border)",
          background: "var(--surface)",
          flexDirection: "column",
          gap: "var(--space-2)",
        }}
      >
        <Link
          to={docsPath.replace(/\/$/, "") || "/docs"}
          className={linkClass}
          onClick={() => setOpen(false)}
        >
          <BookOpen size={18} /> {t(lang, "nav.docs")}
        </Link>
        <a
          href="https://github.com/mcpcentral/prowlrbot"
          target="_blank"
          rel="noopener noreferrer"
          className={linkClass}
          onClick={() => setOpen(false)}
          title="ProwlrBot on GitHub"
        >
          <Github size={18} /> {t(lang, "nav.github")}
        </a>
      </div>
      <style>{`
        @media (max-width: 640px) {
          .nav-links { display: none !important; }
          .nav-mobile-toggle { display: flex !important; }
        }
        @media (min-width: 641px) {
          .nav-mobile { display: none !important; }
        }
      `}</style>
    </header>
  );
}
