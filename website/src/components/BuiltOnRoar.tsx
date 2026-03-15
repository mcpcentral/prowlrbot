import { type Lang } from "../i18n";
import { SectionWrapper } from "./SectionWrapper";

const ROAR_GITHUB = "https://github.com/ProwlrBot/roar-protocol";
const ROAR_PYPI = "https://pypi.org/project/roar-protocol/";
const DEMO_PATH = "/demo/roar-demo.html";

const copy: Record<Lang, { label: string; title: string; tagline: string; desc: string; pip: string; tryDemo: string; github: string; pypi: string }> = {
  en: {
    label: "Protocol",
    title: "Built on ROAR",
    tagline: "One protocol. Any agent.",
    desc: "ProwlrBot speaks ROAR — the open agent communication protocol. Discover agents, fetch cards, send tasks over HTTP or WebSocket. Build compatible agents in minutes.",
    pip: "pip install roar-protocol",
    tryDemo: "Open live demo",
    github: "GitHub",
    pypi: "PyPI",
  },
  zh: {
    label: "协议",
    title: "基于 ROAR 构建",
    tagline: "一个协议，任意智能体。",
    desc: "ProwlrBot 使用 ROAR — 开放的智能体通信协议。发现智能体、获取卡片、通过 HTTP 或 WebSocket 发送任务。安装即用，快速构建兼容智能体。",
    pip: "pip install roar-protocol",
    tryDemo: "打开现场演示",
    github: "GitHub",
    pypi: "PyPI",
  },
};

interface BuiltOnRoarProps {
  lang: Lang;
}

export function BuiltOnRoar({ lang }: BuiltOnRoarProps) {
  const c = copy[lang];

  return (
    <SectionWrapper
      id="built-on-roar"
      label={c.label}
      title={c.title}
      description={c.desc}
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "var(--space-6)",
          maxWidth: "36rem",
          margin: "0 auto",
        }}
      >
        <p
          style={{
            margin: 0,
            fontSize: "1rem",
            fontWeight: 600,
            color: "var(--accent)",
            letterSpacing: "-0.01em",
          }}
        >
          {c.tagline}
        </p>
        <div
          style={{
            fontFamily: "ui-monospace, 'SF Mono', Menlo, monospace",
            fontSize: "0.875rem",
            padding: "0.75rem 1.25rem",
            borderRadius: "0.5rem",
            background: "var(--surface)",
            border: "1px solid var(--border)",
            color: "var(--text)",
            width: "100%",
            textAlign: "center",
          }}
        >
          <code>{c.pip}</code>
        </div>

        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "center",
            gap: "0.75rem",
          }}
        >
          <a
            href={DEMO_PATH}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem",
              padding: "0.75rem 1.5rem",
              borderRadius: "0.5rem",
              background: "var(--accent)",
              color: "#0a0a0f",
              fontWeight: 600,
              fontSize: "0.9375rem",
              textDecoration: "none",
              transition: "transform 0.2s ease, box-shadow 0.2s ease",
              boxShadow: "0 4px 14px rgba(255, 61, 0, 0.35)",
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.transform = "translateY(-2px)";
              e.currentTarget.style.boxShadow = "0 6px 20px rgba(255, 61, 0, 0.45)";
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.transform = "translateY(0)";
              e.currentTarget.style.boxShadow = "0 4px 14px rgba(255, 61, 0, 0.35)";
            }}
          >
            <span aria-hidden style={{ fontSize: "0.75rem" }}>▶</span> {c.tryDemo}
          </a>
          <a
            href={ROAR_GITHUB}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: "inline-flex",
              alignItems: "center",
              padding: "0.75rem 1.25rem",
              borderRadius: "0.5rem",
              border: "1px solid var(--border)",
              color: "var(--text)",
              fontWeight: 500,
              fontSize: "0.875rem",
              textDecoration: "none",
              transition: "border-color 0.2s ease, color 0.2s ease",
            }}
          >
            {c.github}
          </a>
          <a
            href={ROAR_PYPI}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: "inline-flex",
              alignItems: "center",
              padding: "0.75rem 1.25rem",
              borderRadius: "0.5rem",
              border: "1px solid var(--border)",
              color: "var(--text)",
              fontWeight: 500,
              fontSize: "0.875rem",
              textDecoration: "none",
              transition: "border-color 0.2s ease, color 0.2s ease",
            }}
          >
            {c.pypi}
          </a>
        </div>

        <p
          style={{
            margin: 0,
            fontSize: "0.8125rem",
            color: "var(--text-muted)",
            textAlign: "center",
          }}
        >
          The live demo runs in your browser — point at any ROAR endpoint, check health, fetch the card, send a message. No install, no backend.
        </p>
      </div>
    </SectionWrapper>
  );
}
