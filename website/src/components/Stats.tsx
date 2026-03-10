/**
 * Stats section — key numbers at a glance.
 */
import { motion } from "motion/react";
import { t, type Lang } from "../i18n";

const STATS: Array<{ key: string }> = [
  { key: "features" },
  { key: "channels" },
  { key: "skills" },
  { key: "protocols" },
  { key: "autonomy" },
];

interface StatsProps {
  lang: Lang;
  delay?: number;
}

export function Stats({ lang, delay = 0 }: StatsProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      style={{
        margin: "0 auto",
        maxWidth: "var(--container)",
        padding: "var(--space-5) var(--space-4)",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          flexWrap: "wrap",
          gap: "var(--space-4)",
        }}
      >
        {STATS.map(({ key }, i) => (
          <motion.div
            key={key}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: delay + i * 0.08 }}
            style={{
              textAlign: "center",
              minWidth: "7rem",
              padding: "var(--space-3) var(--space-3)",
              borderRadius: "8px",
              background: "var(--accent-dim)",
              border: "1px solid var(--border)",
            }}
          >
            <div
              style={{
                fontSize: "2.25rem",
                fontWeight: 700,
                color: "var(--accent)",
                lineHeight: 1.1,
                marginBottom: "0.375rem",
              }}
            >
              {t(lang, `stats.${key}.value`)}
            </div>
            <div
              style={{
                fontSize: "0.8125rem",
                color: "var(--text-muted)",
                fontWeight: 500,
                letterSpacing: "0.01em",
              }}
            >
              {t(lang, `stats.${key}.label`)}
            </div>
          </motion.div>
        ))}
      </div>
    </motion.section>
  );
}
