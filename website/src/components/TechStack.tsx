import { useState } from "react";
import { type Lang } from "../i18n";
import { SectionWrapper } from "./SectionWrapper";

interface TechTile {
  name: string;
  color: string;
  glow: string;
  category: string;
  desc: string;
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

  const filtered = activeCategory
    ? tiles.filter((t) => t.category === activeCategory)
    : tiles;

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
              onMouseEnter={() => setHoveredTile(tile.name)}
              onMouseLeave={() => setHoveredTile(null)}
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

      <style>{`
        .tech-tile:active {
          transform: translateY(2px) rotateX(0deg) !important;
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
