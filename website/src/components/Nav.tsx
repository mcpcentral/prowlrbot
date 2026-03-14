import { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { Menu, X, BookOpen, Github, Newspaper, Sun, Moon, Store, DollarSign } from "lucide-react";
import { UserButton, useUser } from "@clerk/react";
import { useAuthEnabled } from "../contexts/AuthContext";
import { t, type Lang } from "../i18n";

function NavAuthClerk({ onNavigate }: { onNavigate?: () => void }) {
  const { isSignedIn } = useUser();
  if (isSignedIn) {
    return (
      <div style={{ display: "flex", alignItems: "center" }}>
        <UserButton />
      </div>
    );
  }
  return (
    <>
      <Link
        to="/sign-in"
        className="nav-item"
        style={{ fontSize: "0.875rem", fontWeight: 500 }}
        onClick={onNavigate}
      >
        Log in
      </Link>
      <Link
        to="/sign-up"
        className="nav-signup-btn"
        style={{
          padding: "0.5rem 1rem",
          fontSize: "0.8125rem",
          fontWeight: 700,
          color: "var(--bg)",
          background: "var(--accent)",
          border: "none",
          borderRadius: "0.375rem",
          textDecoration: "none",
          transition: "all 0.2s ease",
          whiteSpace: "nowrap",
        }}
        onClick={onNavigate}
      >
        Sign up
      </Link>
    </>
  );
}

interface NavProps {
  projectName: string;
  lang: Lang;
  theme: "dark" | "light";
  onThemeToggle: () => void;
  docsPath: string;
  repoUrl: string;
}

export function Nav({
  projectName,
  lang,
  theme,
  onThemeToggle,
  docsPath,
  repoUrl: _repoUrl,
}: NavProps) {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const location = useLocation();
  const isHome = location.pathname === "/";
  const authEnabled = useAuthEnabled();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const linkClass = "nav-item";

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
          ? "var(--nav-bg-scrolled, rgba(10, 10, 15, 0.9))"
          : "transparent",
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
            src={`${import.meta.env.BASE_URL}logo.svg`}
            alt={projectName}
            style={{ height: 56, width: "auto", maxWidth: 180 }}
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
          <Link
            to="/marketplace"
            className={linkClass}
            title="ProwlrBot Marketplace"
          >
            <Store size={18} strokeWidth={1.5} aria-hidden />
            <span>Marketplace</span>
          </Link>
          <Link
            to="/blog"
            className={linkClass}
            title="ProwlrBot Blog"
          >
            <Newspaper size={18} strokeWidth={1.5} aria-hidden />
            <span>Blog</span>
          </Link>
          <Link
            to="/pricing"
            className={linkClass}
            title="ProwlrBot Pricing"
          >
            <DollarSign size={18} strokeWidth={1.5} aria-hidden />
            <span>Pricing</span>
          </Link>
          <a
            href="https://github.com/prowlrbot/prowlrbot"
            target="_blank"
            rel="noopener noreferrer"
            className={linkClass}
            title="ProwlrBot on GitHub"
          >
            <Github size={18} strokeWidth={1.5} aria-hidden />
            <span>{t(lang, "nav.github")}</span>
          </a>
          <button
            type="button"
            onClick={onThemeToggle}
            className={linkClass}
            title={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}
            style={{
              background: "none",
              border: "none",
              padding: 0,
              cursor: "pointer",
              font: "inherit",
            }}
          >
            {theme === "light" ? (
              <Moon size={18} strokeWidth={1.5} aria-hidden />
            ) : (
              <Sun size={18} strokeWidth={1.5} aria-hidden />
            )}
          </button>
          {authEnabled ? (
            <NavAuthClerk />
          ) : (
            <button
              type="button"
              onClick={() => {
                const hero = document.querySelector('.hero-section');
                if (hero) {
                  hero.scrollIntoView({ behavior: 'smooth', block: 'start' });
                  setTimeout(() => {
                    const input = hero.querySelector('input[type="email"]');
                    if (input) (input as HTMLElement).focus();
                  }, 600);
                }
              }}
              className="nav-signup-btn"
              style={{
                padding: "0.5rem 1rem",
                fontSize: "0.8125rem",
                fontWeight: 700,
                color: "var(--bg)",
                background: "var(--accent)",
                border: "none",
                borderRadius: "0.375rem",
                cursor: "pointer",
                transition: "all 0.2s ease",
                whiteSpace: "nowrap",
              }}
            >
              Get Early Access
            </button>
          )}
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
        <Link
          to="/marketplace"
          className={linkClass}
          onClick={() => setOpen(false)}
          title="ProwlrBot Marketplace"
        >
          <Store size={18} /> Marketplace
        </Link>
        <Link
          to="/blog"
          className={linkClass}
          onClick={() => setOpen(false)}
          title="ProwlrBot Blog"
        >
          <Newspaper size={18} /> Blog
        </Link>
        <Link
          to="/pricing"
          className={linkClass}
          onClick={() => setOpen(false)}
          title="ProwlrBot Pricing"
        >
          <DollarSign size={18} /> Pricing
        </Link>
        <a
          href="https://github.com/prowlrbot/prowlrbot"
          target="_blank"
          rel="noopener noreferrer"
          className={linkClass}
          onClick={() => setOpen(false)}
          title="ProwlrBot on GitHub"
        >
          <Github size={18} /> {t(lang, "nav.github")}
        </a>
        <button
          type="button"
          onClick={() => {
            onThemeToggle();
            setOpen(false);
          }}
          className={linkClass}
          title={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}
          style={{
            background: "none",
            border: "none",
            padding: "var(--space-1) 0",
            cursor: "pointer",
            font: "inherit",
            textAlign: "left",
          }}
        >
          {theme === "light" ? (
            <><Moon size={18} /> Dark mode</>
          ) : (
            <><Sun size={18} /> Light mode</>
          )}
        </button>
        {authEnabled ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)", marginTop: "var(--space-1)" }}>
            <NavAuthClerk onNavigate={() => setOpen(false)} />
          </div>
        ) : (
          <button
            type="button"
            onClick={() => {
              setOpen(false);
              const hero = document.querySelector('.hero-section');
              if (hero) {
                hero.scrollIntoView({ behavior: 'smooth' });
                setTimeout(() => {
                  const form = hero.querySelector('input[type="email"]');
                  if (form) (form as HTMLElement).focus();
                }, 500);
              }
            }}
            style={{
              marginTop: "var(--space-1)",
              padding: "0.625rem 1.25rem",
              fontSize: "0.875rem",
              fontWeight: 700,
              color: "var(--bg)",
              background: "var(--accent)",
              border: "none",
              borderRadius: "0.375rem",
              cursor: "pointer",
              textAlign: "center",
            }}
          >
            Get Early Access
          </button>
        )}
      </div>

      <style>{`
        .nav-item {
          color: var(--text-muted);
          transition: color 0.2s ease;
          display: inline-flex;
          align-items: center;
          gap: 0.375rem;
          font-size: 0.875rem;
          text-decoration: none;
        }
        .nav-item:hover {
          color: var(--text);
        }
        .nav-signup-btn:hover {
          opacity: 0.9;
          transform: translateY(-1px);
          box-shadow: 0 2px 12px var(--accent-glow);
        }
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
