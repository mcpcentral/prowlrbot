import { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { Menu, X, BookOpen, Github, Newspaper } from "lucide-react";
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
  const [scrolled, setScrolled] = useState(false);
  const location = useLocation();
  const isHome = location.pathname === "/";

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const linkClass =
    "nav-item text-[var(--text-muted)] hover:text-[var(--text)] transition-colors";

  const scrollTo = (id: string) => {
    setOpen(false);
    if (!isHome) return;
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <header
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        zIndex: 50,
        background: scrolled
          ? "rgba(10, 10, 15, 0.9)"
          : "rgba(10, 10, 15, 0)",
        backdropFilter: scrolled ? "blur(12px)" : "none",
        borderBottom: scrolled
          ? "1px solid var(--border)"
          : "1px solid transparent",
        transition:
          "background 0.3s ease, border-color 0.3s ease, backdrop-filter 0.3s ease",
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
            src="/logo.png"
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
          {isHome && (
            <>
              <button
                type="button"
                onClick={() => scrollTo("features")}
                className={linkClass}
                style={{
                  background: "none",
                  border: "none",
                  padding: 0,
                  cursor: "pointer",
                  font: "inherit",
                }}
              >
                Features
              </button>
              <button
                type="button"
                onClick={() => scrollTo("quickstart")}
                className={linkClass}
                style={{
                  background: "none",
                  border: "none",
                  padding: 0,
                  cursor: "pointer",
                  font: "inherit",
                }}
              >
                Get Started
              </button>
            </>
          )}
          <Link
            to={docsPath.replace(/\/$/, "") || "/docs"}
            className={linkClass}
          >
            <BookOpen size={18} strokeWidth={1.5} aria-hidden />
            <span>{t(lang, "nav.docs")}</span>
          </Link>
          <a
            href="https://github.com/mcpcentral/prowlrbot/tree/main/docs/blog"
            target="_blank"
            rel="noopener noreferrer"
            className={linkClass}
            title="ProwlrBot Blog"
          >
            <Newspaper size={18} strokeWidth={1.5} aria-hidden />
            <span>Blog</span>
          </a>
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
        {isHome && (
          <>
            <button
              type="button"
              onClick={() => scrollTo("features")}
              className={linkClass}
              style={{
                background: "none",
                border: "none",
                padding: "var(--space-1) 0",
                cursor: "pointer",
                font: "inherit",
                textAlign: "left",
              }}
            >
              Features
            </button>
            <button
              type="button"
              onClick={() => scrollTo("quickstart")}
              className={linkClass}
              style={{
                background: "none",
                border: "none",
                padding: "var(--space-1) 0",
                cursor: "pointer",
                font: "inherit",
                textAlign: "left",
              }}
            >
              Get Started
            </button>
          </>
        )}
        <Link
          to={docsPath.replace(/\/$/, "") || "/docs"}
          className={linkClass}
          onClick={() => setOpen(false)}
        >
          <BookOpen size={18} /> {t(lang, "nav.docs")}
        </Link>
        <a
          href="https://github.com/mcpcentral/prowlrbot/tree/main/docs/blog"
          target="_blank"
          rel="noopener noreferrer"
          className={linkClass}
          onClick={() => setOpen(false)}
          title="ProwlrBot Blog"
        >
          <Newspaper size={18} /> Blog
        </a>
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
