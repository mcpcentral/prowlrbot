import { Link } from "react-router-dom";
import { ArrowRight, Github } from "lucide-react";
import { motion } from "motion/react";
import { t, type Lang } from "../i18n";

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
    transition: { staggerChildren: 0.1, delayChildren: 0.05 },
  },
};

const item = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0 },
};

export function Hero({
  projectName,
  tagline: _tagline,
  lang,
  docsPath,
}: HeroProps) {
  return (
    <motion.section
      className="hero-section"
      style={{
        margin: "0 auto",
        maxWidth: "var(--container)",
        padding: "var(--space-8) var(--space-4) var(--space-7)",
        textAlign: "center",
      }}
      variants={container}
      initial="hidden"
      animate="visible"
    >
      <motion.div
        variants={item}
        className="hero-brand-row"
        style={{
          marginBottom: "var(--space-4)",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <img
          src="/prowlrlogo.png"
          alt={projectName}
          style={{
            height: 220,
            width: "auto",
            filter: "drop-shadow(0 0 40px rgba(0, 229, 255, 0.2))",
          }}
        />
      </motion.div>
      <motion.p
        variants={item}
        style={{
          margin: "var(--space-3) 0 var(--space-2)",
          fontSize: "clamp(1.125rem, 2.5vw, 1.375rem)",
          color: "var(--text)",
          maxWidth: "32rem",
          marginLeft: "auto",
          marginRight: "auto",
          lineHeight: 1.5,
          fontWeight: 600,
        }}
      >
        {t(lang, "hero.slogan")}
      </motion.p>
      <motion.p
        variants={item}
        style={{
          margin: "0 auto var(--space-4)",
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
          marginBottom: "var(--space-5)",
          display: "flex",
          gap: "var(--space-3)",
          justifyContent: "center",
          flexWrap: "wrap",
        }}
      >
        <Link
          to={docsPath.replace(/\/$/, "") || "/docs"}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "var(--space-1)",
            padding: "var(--space-2) var(--space-4)",
            background: "var(--accent)",
            color: "var(--bg)",
            borderRadius: "0.5rem",
            fontSize: "1rem",
            fontWeight: 700,
            transition: "all 0.2s ease",
          }}
        >
          {t(lang, "hero.cta")}
          <ArrowRight size={20} strokeWidth={2} aria-hidden />
        </Link>
        <a
          href="https://github.com/mcpcentral/prowlrbot"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "var(--space-1)",
            padding: "var(--space-2) var(--space-4)",
            background: "transparent",
            color: "var(--text)",
            border: "1px solid var(--border)",
            borderRadius: "0.5rem",
            fontSize: "1rem",
            fontWeight: 600,
            transition: "all 0.2s ease",
          }}
        >
          <Github size={18} strokeWidth={2} aria-hidden />
          GitHub
        </a>
      </motion.div>
    </motion.section>
  );
}
