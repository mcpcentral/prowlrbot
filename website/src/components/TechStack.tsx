import { useState, useEffect } from "react";
import { type Lang } from "../i18n";
import { SectionWrapper } from "./SectionWrapper";

interface TechTile {
  name: string;
  color: string;
  glow: string;
  category: string;
  desc: string;
  /** Optional link for "Learn more" (e.g. docs or official site) */
  link?: string;
}

const tiles: TechTile[] = [
  // Backend
  {
    name: "Python",
    color: "#3776AB",
    glow: "#3776AB44",
    category: "Backend",
    desc: "3.10 – 3.13 async core",
  },
  {
    name: "FastAPI",
    color: "#009688",
    glow: "#00968844",
    category: "Backend",
    desc: "Async REST & WebSocket API",
  },
  {
    name: "Pydantic",
    color: "#E92063",
    glow: "#E9206344",
    category: "Backend",
    desc: "Config & data validation",
  },
  {
    name: "SQLite",
    color: "#003B57",
    glow: "#003B5744",
    category: "Backend",
    desc: "Local-first persistence",
  },
  {
    name: "APScheduler",
    color: "#FF6F00",
    glow: "#FF6F0044",
    category: "Backend",
    desc: "Cron & interval jobs",
  },
  {
    name: "AgentScope",
    color: "#7C4DFF",
    glow: "#7C4DFF44",
    category: "Backend",
    desc: "Multi-agent framework",
  },
  // Frontend
  {
    name: "React 18",
    color: "#61DAFB",
    glow: "#61DAFB44",
    category: "Frontend",
    desc: "Component-driven UI",
  },
  {
    name: "TypeScript",
    color: "#3178C6",
    glow: "#3178C644",
    category: "Frontend",
    desc: "Type-safe frontend",
  },
  {
    name: "Vite",
    color: "#646CFF",
    glow: "#646CFF44",
    category: "Frontend",
    desc: "Lightning-fast bundler",
  },
  {
    name: "Ant Design",
    color: "#1677FF",
    glow: "#1677FF44",
    category: "Frontend",
    desc: "Enterprise component library",
  },
  // Protocols
  {
    name: "MCP",
    color: "#00E5FF",
    glow: "#00E5FF44",
    category: "Protocols",
    desc: "Model Context Protocol",
  },
  {
    name: "ACP",
    color: "#FF4081",
    glow: "#FF408144",
    category: "Protocols",
    desc: "Agent Communication Protocol",
  },
  {
    name: "A2A",
    color: "#FFD740",
    glow: "#FFD74044",
    category: "Protocols",
    desc: "Agent-to-Agent protocol",
  },
  {
    name: "ROAR",
    color: "#FF3D00",
    glow: "#FF3D0044",
    category: "Protocols",
    desc: "ProwlrBot/roar-protocol — 5-layer agent interop",
  },
  // Infrastructure
  {
    name: "Docker",
    color: "#2496ED",
    glow: "#2496ED44",
    category: "Infra",
    desc: "Container orchestration",
  },
  {
    name: "Redis",
    color: "#DC382D",
    glow: "#DC382D44",
    category: "Infra",
    desc: "Pub/sub & swarm bridge",
  },
  {
    name: "uvicorn",
    color: "#2ECC71",
    glow: "#2ECC7144",
    category: "Infra",
    desc: "ASGI server",
  },
  {
    name: "Playwright",
    color: "#45BA4B",
    glow: "#45BA4B44",
    category: "Infra",
    desc: "Browser automation",
  },
  // AI Providers
  {
    name: "OpenAI",
    color: "#10A37F",
    glow: "#10A37F44",
    category: "AI",
    desc: "GPT model provider",
  },
  {
    name: "Anthropic",
    color: "#D4A574",
    glow: "#D4A57444",
    category: "AI",
    desc: "Claude model provider",
  },
  {
    name: "Groq",
    color: "#F55036",
    glow: "#F5503644",
    category: "AI",
    desc: "Ultra-fast inference",
  },
  {
    name: "Ollama",
    color: "#FFFFFF",
    glow: "#FFFFFF22",
    category: "AI",
    desc: "Local model runtime",
  },
  // Ecosystem (ProwlrBot org repos)
  {
    name: "Marketplace",
    color: "#AB47BC",
    glow: "#AB47BC44",
    category: "Ecosystem",
    desc: "ProwlrBot/prowlr-marketplace — revenue-sharing store",
  },
  {
    name: "AgentVerse",
    color: "#26C6DA",
    glow: "#26C6DA44",
    category: "Ecosystem",
    desc: "ProwlrBot/agentverse — virtual agent world",
  },
  {
    name: "Prowlr Docs",
    color: "#78909C",
    glow: "#78909C44",
    category: "Ecosystem",
    desc: "ProwlrBot/prowlr-docs — official documentation",
  },
];

const categories = [
  "Backend",
  "Frontend",
  "Protocols",
  "Infra",
  "AI",
  "Ecosystem",
];

const categoryColors: Record<string, string> = {
  Backend: "#3776AB",
  Frontend: "#61DAFB",
  Protocols: "#00E5FF",
  Infra: "#2496ED",
  AI: "#10A37F",
  Ecosystem: "#AB47BC",
};

interface TechStackProps {
  lang: Lang;
}

export function TechStack({ lang: _lang }: TechStackProps) {
  const [hoveredTile, setHoveredTile] = useState<string | null>(null);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [selectedTile, setSelectedTile] = useState<TechTile | null>(null);

  const filtered = activeCategory
    ? tiles.filter((t) => t.category === activeCategory)
    : tiles;

  useEffect(() => {
    if (!selectedTile) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setSelectedTile(null);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [selectedTile]);

  return (
    <SectionWrapper
      id="tech-stack"
      label="Built With"
      title="The Stack"
      description="Every technology powering ProwlrBot — tap a tile to learn more"
    >
      {/* Category filter row */}
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          gap: "0.5rem",
          flexWrap: "wrap",
          marginBottom: "var(--space-4)",
        }}
      >
        <button
          onClick={() => setActiveCategory(null)}
          style={{
            padding: "0.375rem 0.875rem",
            fontSize: "0.75rem",
            fontWeight: 600,
            border: `1px solid ${
              activeCategory === null ? "var(--accent)" : "var(--border)"
            }`,
            borderRadius: "2rem",
            background:
              activeCategory === null ? "var(--accent)" : "transparent",
            color: activeCategory === null ? "#0a0a0f" : "var(--text-muted)",
            cursor: "pointer",
            transition: "all 0.2s ease",
          }}
        >
          All
        </button>
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() =>
              setActiveCategory(activeCategory === cat ? null : cat)
            }
            style={{
              padding: "0.375rem 0.875rem",
              fontSize: "0.75rem",
              fontWeight: 600,
              border: `1px solid ${
                activeCategory === cat ? categoryColors[cat] : "var(--border)"
              }`,
              borderRadius: "2rem",
              background:
                activeCategory === cat ? categoryColors[cat] : "transparent",
              color: activeCategory === cat ? "#0a0a0f" : "var(--text-muted)",
              cursor: "pointer",
              transition: "all 0.2s ease",
            }}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Keyboard-style 2.5D grid */}
      <div
        className="tech-grid"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(120px, 1fr))",
          gap: "0.75rem",
          perspective: "800px",
        }}
      >
        {filtered.map((tile) => {
          const isHovered = hoveredTile === tile.name;
          return (
            <div
              key={tile.name}
              className="tech-tile"
              role="button"
              tabIndex={0}
              onMouseEnter={() => setHoveredTile(tile.name)}
              onMouseLeave={() => setHoveredTile(null)}
              onClick={() => setSelectedTile(tile)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  setSelectedTile(tile);
                }
              }}
              style={{
                position: "relative",
                borderRadius: "0.625rem",
                cursor: "pointer",
                transition: "transform 0.25s ease, box-shadow 0.25s ease",
                transform: isHovered
                  ? "translateY(-4px) rotateX(2deg)"
                  : "translateY(0) rotateX(0)",
                transformStyle: "preserve-3d",
              }}
            >
              {/* Keycap top face */}
              <div
                style={{
                  position: "relative",
                  zIndex: 1,
                  padding: "1rem 0.75rem",
                  borderRadius: "0.625rem",
                  background: `linear-gradient(135deg, ${tile.color}18, ${tile.color}08)`,
                  border: `1px solid ${
                    isHovered ? tile.color : "var(--border)"
                  }`,
                  boxShadow: isHovered
                    ? `0 8px 24px ${tile.glow}, 0 4px 8px rgba(0,0,0,0.3), inset 0 1px 0 ${tile.color}33`
                    : `0 4px 0 var(--surface), 0 4px 8px rgba(0,0,0,0.2), inset 0 1px 0 ${tile.color}22`,
                  transition: "all 0.25s ease",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: "0.375rem",
                  minHeight: "80px",
                  justifyContent: "center",
                }}
              >
                <span
                  style={{
                    fontSize: "0.8125rem",
                    fontWeight: 700,
                    color: isHovered ? tile.color : "var(--text)",
                    transition: "color 0.2s ease",
                    textAlign: "center",
                    lineHeight: 1.2,
                  }}
                >
                  {tile.name}
                </span>
                <span
                  style={{
                    fontSize: "0.625rem",
                    fontWeight: 500,
                    color: "var(--text-muted)",
                    textTransform: "uppercase",
                    letterSpacing: "0.08em",
                    opacity: 0.7,
                  }}
                >
                  {tile.category}
                </span>
              </div>

              {/* Tooltip on hover */}
              {isHovered && (
                <div
                  style={{
                    position: "absolute",
                    bottom: "calc(100% + 8px)",
                    left: "50%",
                    transform: "translateX(-50%)",
                    padding: "0.5rem 0.75rem",
                    borderRadius: "0.5rem",
                    background: "var(--bg)",
                    border: `1px solid ${tile.color}66`,
                    boxShadow: `0 4px 16px ${tile.glow}`,
                    fontSize: "0.75rem",
                    color: "var(--text)",
                    whiteSpace: "nowrap",
                    zIndex: 10,
                    pointerEvents: "none",
                  }}
                >
                  {tile.desc}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Tile detail modal */}
      {selectedTile && (
        <div
          className="tech-stack-modal-overlay"
          role="dialog"
          aria-modal="true"
          aria-labelledby="tech-stack-modal-title"
          onClick={() => setSelectedTile(null)}
        >
          <div
            className="tech-stack-modal"
            onClick={(e) => e.stopPropagation()}
            style={{
              borderColor: `${selectedTile.color}66`,
              boxShadow: `0 8px 32px ${selectedTile.glow}, 0 4px 16px rgba(0,0,0,0.3)`,
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: "var(--space-3)",
                gap: "1rem",
              }}
            >
              <span
                style={{
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                  color: selectedTile.color,
                }}
              >
                {selectedTile.category}
              </span>
              <button
                type="button"
                className="tech-stack-modal-close"
                onClick={() => setSelectedTile(null)}
                aria-label="Close"
              >
                ×
              </button>
            </div>
            <h3
              id="tech-stack-modal-title"
              style={{
                fontSize: "1.5rem",
                fontWeight: 700,
                color: "var(--text)",
                marginBottom: "var(--space-2)",
              }}
            >
              {selectedTile.name}
            </h3>
            <p
              style={{
                fontSize: "0.9375rem",
                color: "var(--text-muted)",
                lineHeight: 1.5,
                marginBottom: selectedTile.link ? "var(--space-4)" : 0,
              }}
            >
              {selectedTile.desc}
            </p>
            {selectedTile.link && (
              <a
                href={selectedTile.link}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.375rem",
                  fontSize: "0.875rem",
                  fontWeight: 600,
                  color: selectedTile.color,
                  textDecoration: "none",
                }}
              >
                Learn more →
              </a>
            )}
          </div>
        </div>
      )}

      <style>{`
        .tech-tile:active {
          transform: translateY(2px) rotateX(0deg) !important;
        }
        .tech-stack-modal-overlay {
          position: fixed;
          inset: 0;
          z-index: 1000;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 1rem;
          background: rgba(0, 0, 0, 0.6);
          backdrop-filter: blur(4px);
          animation: tech-stack-fadeIn 0.2s ease;
        }
        .tech-stack-modal {
          max-width: 400px;
          width: 100%;
          padding: var(--space-5);
          border-radius: 1rem;
          border: 1px solid var(--border);
          background: var(--bg);
          animation: tech-stack-slideUp 0.25s ease;
        }
        .tech-stack-modal-close {
          width: 2rem;
          height: 2rem;
          display: flex;
          align-items: center;
          justify-content: center;
          border: none;
          border-radius: 0.5rem;
          background: var(--surface);
          color: var(--text-muted);
          font-size: 1.25rem;
          line-height: 1;
          cursor: pointer;
          transition: background 0.2s, color 0.2s;
        }
        .tech-stack-modal-close:hover {
          background: var(--border);
          color: var(--text);
        }
        @keyframes tech-stack-fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes tech-stack-slideUp {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @media (max-width: 640px) {
          .tech-grid {
            grid-template-columns: repeat(3, 1fr) !important;
            gap: 0.5rem !important;
          }
        }
      `}</style>
    </SectionWrapper>
  );
}
