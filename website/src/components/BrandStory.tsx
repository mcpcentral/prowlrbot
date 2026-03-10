/**
 * Brand story: Why we built ProwlrBot — emotional narrative with CTA.
 */
import { motion } from "motion/react";
import { t, type Lang } from "../i18n";

interface BrandStoryProps {
  lang: Lang;
  delay?: number;
}

export function BrandStory({ lang, delay = 0 }: BrandStoryProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      style={{
        margin: "0 auto",
        maxWidth: "var(--container)",
        padding: "var(--space-6) var(--space-4)",
        textAlign: "center",
      }}
    >
      <div
        style={{
          maxWidth: "36rem",
          margin: "0 auto",
          padding: "var(--space-4)",
          borderTop: "1px solid var(--border)",
        }}
      >
        <h2
          style={{
            margin: "0 0 var(--space-3)",
            fontSize: "1.125rem",
            fontWeight: 600,
            color: "var(--accent)",
            letterSpacing: "0.02em",
          }}
        >
          {t(lang, "brandstory.title")}
        </h2>
        <p
          style={{
            margin: "0 0 var(--space-2)",
            fontSize: "0.9375rem",
            color: "var(--text)",
            lineHeight: 1.8,
          }}
        >
          {t(lang, "brandstory.para1")}
        </p>
        <p
          style={{
            margin: "0 0 var(--space-2)",
            fontSize: "0.9375rem",
            color: "var(--text)",
            lineHeight: 1.8,
          }}
        >
          {t(lang, "brandstory.para2")}
        </p>
        <p
          style={{
            margin: "0 0 var(--space-2)",
            fontSize: "0.9375rem",
            color: "var(--text-muted)",
            lineHeight: 1.8,
          }}
        >
          {t(lang, "brandstory.para3")}
        </p>
        <p
          style={{
            margin: "0 0 var(--space-3)",
            fontSize: "0.9375rem",
            color: "var(--text-muted)",
            lineHeight: 1.8,
          }}
        >
          {t(lang, "brandstory.para4")}
        </p>
        <a
          href="https://github.com/prowlrbot/prowlrbot"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: "inline-block",
            padding: "0.625rem 1.5rem",
            fontSize: "0.875rem",
            fontWeight: 600,
            color: "var(--bg)",
            background: "var(--accent)",
            borderRadius: "6px",
            textDecoration: "none",
            transition: "opacity 0.2s ease",
          }}
          onMouseEnter={(e) => ((e.target as HTMLElement).style.opacity = "0.85")}
          onMouseLeave={(e) => ((e.target as HTMLElement).style.opacity = "1")}
        >
          {t(lang, "brandstory.cta")}
        </a>
      </div>
    </motion.section>
  );
}
