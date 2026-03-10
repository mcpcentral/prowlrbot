import { t, type Lang } from "../i18n";
import { SectionWrapper } from "./SectionWrapper";

interface BrandStoryProps {
  lang: Lang;
}

export function BrandStory({ lang }: BrandStoryProps) {
  return (
    <SectionWrapper
      id="story"
      label="Our Story"
      title={t(lang, "brandstory.title")}
    >
      <div
        style={{
          maxWidth: "36rem",
          margin: "0 auto",
          textAlign: "center",
        }}
      >
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
            margin: "0 0 var(--space-4)",
            fontSize: "0.9375rem",
            color: "var(--text-muted)",
            lineHeight: 1.8,
          }}
        >
          {t(lang, "brandstory.para4")}
        </p>
        <a
          href="https://github.com/mcpcentral/prowlrbot"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: "inline-block",
            padding: "0.75rem 2rem",
            fontSize: "0.9375rem",
            fontWeight: 600,
            color: "var(--bg)",
            background: "var(--accent)",
            borderRadius: "0.5rem",
            textDecoration: "none",
            transition: "opacity 0.2s ease, transform 0.15s ease",
          }}
          onMouseEnter={(e) => {
            (e.target as HTMLElement).style.opacity = "0.9";
            (e.target as HTMLElement).style.transform = "translateY(-1px)";
          }}
          onMouseLeave={(e) => {
            (e.target as HTMLElement).style.opacity = "1";
            (e.target as HTMLElement).style.transform = "translateY(0)";
          }}
        >
          {t(lang, "brandstory.cta")}
        </a>
      </div>
    </SectionWrapper>
  );
}
