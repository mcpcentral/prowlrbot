import { Github } from "lucide-react";
import { motion } from "motion/react";
import { t, type Lang } from "../i18n";
import { AnimatedTerminal } from "./AnimatedTerminal";
import { EarlyAccessForm } from "./EarlyAccessForm";

interface HeroProps {
  projectName: string;
  tagline: string;
  lang: Lang;
  docsPath: string;
  /** When set, show "Open app" CTA and sign-up-on-app copy. */
  consoleUrl?: string;
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
  docsPath: _docsPath,
  consoleUrl,
}: HeroProps) {
  return (
    <section
      className="hero-section"
      style={{
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Gradient background — more dramatic */}
      <div
        aria-hidden
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse 80% 60% at 50% -10%, rgba(0,229,255,0.12) 0%, transparent 60%), radial-gradient(circle at 80% 80%, rgba(0,229,255,0.04) 0%, transparent 40%)",
          pointerEvents: "none",
        }}
      />

      {/* Scan line animation overlay */}
      <div
        aria-hidden
        className="hero-scanline"
        style={{
          position: "absolute",
          inset: 0,
          pointerEvents: "none",
          opacity: 0.03,
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
          {/* Badge — pulsing dot + compelling text */}
          <motion.div
            variants={item}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "var(--space-1)",
              padding: "0.3rem 0.875rem",
              marginBottom: "var(--space-3)",
              fontSize: "0.75rem",
              fontWeight: 600,
              fontFamily: "ui-monospace, 'SF Mono', Menlo, monospace",
              color: "var(--accent)",
              background: "var(--accent-dim)",
              border: "1px solid rgba(0,229,255,0.2)",
              borderRadius: "9999px",
              letterSpacing: "0.05em",
            }}
          >
            <span
              className="hero-pulse-dot"
              style={{
                width: 6,
                height: 6,
                borderRadius: "50%",
                background: "var(--accent)",
                display: "inline-block",
                flexShrink: 0,
              }}
            />
            {t(lang, "hero.badge")}
          </motion.div>

          <motion.h1
            variants={item}
            style={{
              margin: "0 0 var(--space-2)",
              fontSize: "clamp(2.25rem, 5vw, 3.5rem)",
              fontWeight: 800,
              lineHeight: 1.08,
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
              fontSize: "clamp(1.125rem, 2.5vw, 1.375rem)",
              fontWeight: 700,
              color: "var(--text)",
              lineHeight: 1.3,
            }}
          >
            {t(lang, "hero.slogan")}
          </motion.p>

          <motion.p
            variants={item}
            style={{
              margin: "0 0 var(--space-4)",
              maxWidth: "30rem",
              fontSize: "1rem",
              color: "var(--text-muted)",
              lineHeight: 1.65,
            }}
          >
            {t(lang, "hero.sub")}
          </motion.p>
          {consoleUrl && (
            <motion.p
              variants={item}
              style={{
                margin: "0 0 var(--space-3)",
                fontSize: "0.9375rem",
                color: "var(--text-muted)",
                lineHeight: 1.5,
              }}
            >
              Sign up on the app to get free credits and your dashboard.
            </motion.p>
          )}

          {/* Email capture form */}
          <motion.div
            variants={item}
            style={{ marginBottom: "var(--space-4)" }}
          >
            <EarlyAccessForm variant="hero" />
          </motion.div>

          {/* Secondary CTA */}
          <motion.div
            variants={item}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "var(--space-3)",
              marginBottom: "var(--space-5)",
              flexWrap: "wrap",
            }}
          >
            {consoleUrl && (
              <a
                href={consoleUrl}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "var(--space-1)",
                  fontSize: "0.875rem",
                  fontWeight: 600,
                  color: "var(--accent)",
                  textDecoration: "none",
                  padding: "0.5rem 0.75rem",
                  border: "1px solid var(--accent)",
                  borderRadius: "0.375rem",
                }}
              >
                Open app
              </a>
            )}
            <a
              href="https://github.com/prowlrbot/prowlrbot"
              target="_blank"
              rel="noopener noreferrer"
              className="hero-github-link"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "var(--space-1)",
                fontSize: "0.875rem",
                fontWeight: 600,
                color: "var(--text-muted)",
                textDecoration: "none",
                transition: "color 0.2s ease",
              }}
            >
              <Github size={16} strokeWidth={2} aria-hidden />
              Star on GitHub
            </a>
            <span style={{ color: "var(--border)", fontSize: "0.75rem" }}>
              |
            </span>
            <span
              style={{
                fontSize: "0.8125rem",
                color: "var(--text-muted)",
                opacity: 0.7,
              }}
            >
              Free during beta
            </span>
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
                  className="hero-stat-value"
                  style={{
                    fontSize: "1.75rem",
                    fontWeight: 800,
                    color: "var(--accent)",
                    lineHeight: 1.2,
                    fontFamily: "ui-monospace, 'SF Mono', Menlo, monospace",
                  }}
                >
                  {value}
                </div>
                <div
                  style={{
                    fontSize: "0.6875rem",
                    color: "var(--text-muted)",
                    fontWeight: 500,
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
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
        @keyframes hero-pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.4; transform: scale(0.8); }
        }
        @keyframes hero-scanline-move {
          0% { transform: translateY(-100%); }
          100% { transform: translateY(100vh); }
        }
        .hero-pulse-dot {
          animation: hero-pulse 2s ease-in-out infinite;
        }
        .hero-scanline::after {
          content: '';
          position: absolute;
          left: 0;
          right: 0;
          height: 1px;
          background: linear-gradient(90deg, transparent, var(--accent), transparent);
          animation: hero-scanline-move 8s linear infinite;
        }
        .hero-github-link:hover {
          color: var(--accent) !important;
        }
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
      `}</style>
    </section>
  );
}
