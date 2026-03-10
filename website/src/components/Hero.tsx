import { Link } from "react-router-dom";
import { ArrowRight, Github } from "lucide-react";
import { motion } from "motion/react";
import { t, type Lang } from "../i18n";
import { AnimatedTerminal } from "./AnimatedTerminal";

interface HeroProps {
  projectName: string;
  tagline: string;
  lang: Lang;
  docsPath: string;
}

const container = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.12, delayChildren: 0.05 },
  },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
};

export function Hero({
  projectName,
  tagline: _tagline,
  lang,
  docsPath,
}: HeroProps) {
  return (
    <section
      className="hero-section"
      style={{
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Gradient background */}
      <div
        aria-hidden
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse 60% 50% at 50% 0%, rgba(0,229,255,0.06) 0%, transparent 70%)",
          pointerEvents: "none",
        }}
      />

      <motion.div
        variants={container}
        initial="hidden"
        animate="visible"
        style={{
          position: "relative",
          margin: "0 auto",
          maxWidth: "var(--container)",
          padding: "var(--space-8) var(--space-4) var(--space-7)",
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "var(--space-6)",
          alignItems: "center",
        }}
        className="hero-grid"
      >
        {/* Left — Text */}
        <div>
          <motion.div
            variants={item}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "var(--space-1)",
              padding: "0.25rem 0.75rem",
              marginBottom: "var(--space-3)",
              fontSize: "0.75rem",
              fontWeight: 500,
              fontFamily: "ui-monospace, 'SF Mono', Menlo, monospace",
              color: "var(--accent)",
              background: "var(--accent-dim)",
              border: "1px solid rgba(0,229,255,0.15)",
              borderRadius: "9999px",
              letterSpacing: "0.05em",
            }}
          >
            v0.1.0 — Now Open Source
          </motion.div>

          <motion.h1
            variants={item}
            style={{
              margin: "0 0 var(--space-3)",
              fontSize: "clamp(2rem, 5vw, 3.25rem)",
              fontWeight: 800,
              lineHeight: 1.1,
              letterSpacing: "-0.03em",
              color: "var(--text)",
            }}
          >
            {projectName}
          </motion.h1>

          <motion.p
            variants={item}
            style={{
              margin: "0 0 var(--space-2)",
              fontSize: "clamp(1rem, 2vw, 1.25rem)",
              fontWeight: 600,
              color: "var(--text)",
              lineHeight: 1.4,
            }}
          >
            {t(lang, "hero.slogan")}
          </motion.p>

          <motion.p
            variants={item}
            style={{
              margin: "0 0 var(--space-4)",
              maxWidth: "28rem",
              fontSize: "0.9375rem",
              color: "var(--text-muted)",
              lineHeight: 1.6,
            }}
          >
            {t(lang, "hero.sub")}
          </motion.p>

          <motion.div
            variants={item}
            style={{
              display: "flex",
              gap: "var(--space-2)",
              flexWrap: "wrap",
              marginBottom: "var(--space-5)",
            }}
          >
            <Link
              to={docsPath.replace(/\/$/, "") || "/docs"}
              className="hero-cta-primary"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "var(--space-1)",
                padding: "0.75rem 1.5rem",
                background: "var(--accent)",
                color: "var(--bg)",
                borderRadius: "0.5rem",
                fontSize: "0.9375rem",
                fontWeight: 700,
                border: "none",
                transition: "all 0.2s ease",
              }}
            >
              {t(lang, "hero.cta")}
              <ArrowRight size={18} strokeWidth={2} aria-hidden />
            </Link>
            <a
              href="https://github.com/mcpcentral/prowlrbot"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "var(--space-1)",
                padding: "0.75rem 1.5rem",
                background: "transparent",
                color: "var(--text)",
                border: "1px solid var(--border)",
                borderRadius: "0.5rem",
                fontSize: "0.9375rem",
                fontWeight: 600,
                transition: "all 0.2s ease",
              }}
            >
              <Github size={18} strokeWidth={2} aria-hidden />
              GitHub
            </a>
          </motion.div>

          {/* Stats row */}
          <motion.div
            variants={item}
            style={{
              display: "flex",
              gap: "var(--space-5)",
              flexWrap: "wrap",
            }}
          >
            {[
              { value: "7", label: "AI Providers" },
              { value: "8", label: "Channels" },
              { value: "60+", label: "Features" },
              { value: "3", label: "Protocols" },
            ].map(({ value, label }) => (
              <div key={label}>
                <div
                  style={{
                    fontSize: "1.5rem",
                    fontWeight: 700,
                    color: "var(--accent)",
                    lineHeight: 1.2,
                  }}
                >
                  {value}
                </div>
                <div
                  style={{
                    fontSize: "0.75rem",
                    color: "var(--text-muted)",
                    fontWeight: 500,
                  }}
                >
                  {label}
                </div>
              </div>
            ))}
          </motion.div>
        </div>

        {/* Right — Animated Terminal */}
        <motion.div
          variants={item}
          style={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <AnimatedTerminal />
        </motion.div>
      </motion.div>

      <style>{`
        @media (max-width: 768px) {
          .hero-grid {
            grid-template-columns: 1fr !important;
            text-align: center;
            padding-top: var(--space-6) !important;
            padding-bottom: var(--space-5) !important;
          }
          .hero-grid > div:first-child {
            display: flex;
            flex-direction: column;
            align-items: center;
          }
        }
        .hero-cta-primary:hover {
          opacity: 0.9;
          transform: translateY(-1px);
          box-shadow: 0 4px 20px var(--accent-glow);
        }
      `}</style>
    </section>
  );
}
