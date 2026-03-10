import { useState, useCallback, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import { Terminal, Copy } from "lucide-react";
import type { SiteConfig } from "../config";
import { t, type Lang } from "../i18n";
import { SectionWrapper } from "./SectionWrapper";

const COMMANDS = {
  pip: ["pip install prowlrbot", "prowlr init --defaults", "prowlr app"],
  docker: [
    "docker pull mcpcentral/prowlrbot:latest",
    "docker run -p 8088:8088 -v prowlrbot-data:/app/working mcpcentral/prowlrbot:latest",
  ],
} as const;

const TABS = ["pip", "docker"] as const;
type OsTab = (typeof TABS)[number];

interface QuickStartProps {
  config: SiteConfig;
  lang: Lang;
}

export function QuickStart({ config, lang }: QuickStartProps) {
  const [activeTab, setActiveTab] = useState<OsTab>("pip");
  const [copied, setCopied] = useState(false);
  const [hasOverflow, setHasOverflow] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const docsBase = config.docsPath.replace(/\/$/, "") || "/docs";

  const lines = COMMANDS[activeTab];
  const fullCommand = lines.join("\n");

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollLeft = 0;
    const check = () => setHasOverflow(el.scrollWidth > el.clientWidth);
    check();
    const ro = new ResizeObserver(check);
    ro.observe(el);
    return () => ro.disconnect();
  }, [activeTab]);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(fullCommand);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }, [fullCommand]);

  return (
    <SectionWrapper
      id="quickstart"
      label="Get Started"
      title={t(lang, "quickstart.title")}
      description="Up and running in under a minute. Choose your install method."
    >
      <div
        style={{
          maxWidth: "36rem",
          margin: "0 auto",
        }}
      >
        {/* Terminal-styled install card */}
        <div
          style={{
            background: "#0d1117",
            border: "1px solid #30363d",
            borderRadius: "0.75rem",
            overflow: "hidden",
          }}
        >
          {/* Tab bar */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0",
              borderBottom: "1px solid #30363d",
              background: "#161b22",
            }}
          >
            {TABS.map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => setActiveTab(tab)}
                style={{
                  flex: 1,
                  padding: "0.625rem 1rem",
                  fontSize: "0.8125rem",
                  fontWeight: 500,
                  fontFamily: "ui-monospace, 'SF Mono', Menlo, monospace",
                  color:
                    activeTab === tab ? "var(--accent)" : "var(--text-muted)",
                  background: activeTab === tab ? "#0d1117" : "transparent",
                  border: "none",
                  borderBottom:
                    activeTab === tab
                      ? "2px solid var(--accent)"
                      : "2px solid transparent",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                {tab === "pip" ? "pip install" : "Docker"}
              </button>
            ))}
          </div>

          {/* Commands */}
          <div style={{ position: "relative", padding: "1.25rem" }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "var(--space-2)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "var(--space-1)",
                }}
              >
                <Terminal
                  size={14}
                  strokeWidth={1.5}
                  style={{ color: "#484f58" }}
                />
                <span
                  style={{
                    fontSize: "0.6875rem",
                    color: "#484f58",
                    letterSpacing: "0.05em",
                  }}
                >
                  terminal
                </span>
              </div>
              <button
                type="button"
                onClick={handleCopy}
                aria-label={t(lang, "docs.copy")}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.25rem",
                  padding: "0.25rem 0.5rem",
                  fontSize: "0.6875rem",
                  color: "#484f58",
                  background: "rgba(255,255,255,0.06)",
                  border: "1px solid rgba(255,255,255,0.1)",
                  borderRadius: "0.25rem",
                  cursor: "pointer",
                }}
              >
                <Copy size={12} strokeWidth={1.5} />
                {copied ? "Copied!" : "Copy"}
              </button>
            </div>

            <div
              ref={scrollRef}
              style={{
                overflowX: "auto",
                display: "flex",
                flexDirection: "column",
                gap: "0.375rem",
                fontFamily: "ui-monospace, 'SF Mono', Menlo, monospace",
                fontSize: "0.8125rem",
                lineHeight: 1.7,
                scrollbarWidth: "none",
              }}
            >
              {lines.map((line) => (
                <div key={line} style={{ whiteSpace: "nowrap" }}>
                  <span style={{ color: "#28c840" }}>$</span>{" "}
                  <span style={{ color: "#f0f6fc" }}>{line}</span>
                </div>
              ))}
            </div>

            {hasOverflow && (
              <div
                aria-hidden
                style={{
                  position: "absolute",
                  top: 0,
                  right: 0,
                  bottom: 0,
                  width: "3rem",
                  background:
                    "linear-gradient(to left, #0d1117 0%, transparent)",
                  pointerEvents: "none",
                }}
              />
            )}
          </div>
        </div>

        <p
          style={{
            margin: "var(--space-3) 0 0",
            fontSize: "0.8125rem",
            color: "var(--text-muted)",
            lineHeight: 1.5,
            textAlign: "center",
          }}
        >
          Then{" "}
          <Link
            to={`${docsBase}/channels`}
            style={{
              color: "var(--accent)",
              textDecoration: "underline",
              textUnderlineOffset: "2px",
            }}
          >
            configure a channel
          </Link>{" "}
          and start chatting with your agent.
        </p>
      </div>
    </SectionWrapper>
  );
}
