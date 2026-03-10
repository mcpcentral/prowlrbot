import type { ReactNode, CSSProperties } from "react";
import { useInView } from "../hooks/useInView";

interface SectionWrapperProps {
  id?: string;
  label?: string;
  title?: string;
  description?: string;
  children: ReactNode;
  style?: CSSProperties;
}

export function SectionWrapper({
  id,
  label,
  title,
  description,
  children,
  style,
}: SectionWrapperProps) {
  const { ref, isInView } = useInView(0.08);

  return (
    <section
      id={id}
      ref={ref as React.RefObject<HTMLElement>}
      style={{
        margin: "0 auto",
        maxWidth: "var(--container)",
        padding: "var(--space-8) var(--space-4)",
        opacity: isInView ? 1 : 0,
        transform: isInView ? "translateY(0)" : "translateY(32px)",
        transition: "opacity 0.7s ease, transform 0.7s ease",
        ...style,
      }}
    >
      {(label || title || description) && (
        <div style={{ marginBottom: "var(--space-6)", textAlign: "center" }}>
          {label && (
            <span
              style={{
                display: "block",
                fontFamily: "ui-monospace, 'SF Mono', Menlo, monospace",
                fontSize: "0.6875rem",
                fontWeight: 500,
                letterSpacing: "0.15em",
                textTransform: "uppercase",
                color: "var(--accent)",
                marginBottom: "var(--space-2)",
              }}
            >
              {label}
            </span>
          )}
          {title && (
            <h2
              style={{
                margin: "0 0 var(--space-2)",
                fontSize: "clamp(1.75rem, 4vw, 2.5rem)",
                fontWeight: 700,
                color: "var(--text)",
                lineHeight: 1.15,
                letterSpacing: "-0.02em",
              }}
            >
              {title}
            </h2>
          )}
          {description && (
            <p
              style={{
                margin: "0 auto",
                maxWidth: "36rem",
                fontSize: "0.9375rem",
                lineHeight: 1.6,
                color: "var(--text-muted)",
              }}
            >
              {description}
            </p>
          )}
        </div>
      )}
      {children}
    </section>
  );
}
