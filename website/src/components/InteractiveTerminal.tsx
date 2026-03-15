import { useState, useRef, useEffect, type KeyboardEvent } from "react";
import { SectionWrapper } from "./SectionWrapper";
import { type Lang } from "../i18n";

const PROMPT = "guest@prowlrbot ~ % ";

const COMMANDS: Record<
  string,
  string | ((lang: Lang) => string)
> = {
  help: (lang) =>
    lang === "zh"
      ? `可用命令:
  help        显示此帮助
  ls          列出项目结构
  whoami      当前用户与项目信息
  prowlr       ProwlrBot CLI 预览
  skills      技能与扩展
  roar        ROAR 协议简介
  about       关于项目与作者
  clear       清空终端`
      : `Available commands:
  help        Show this help
  ls          List project structure
  whoami      Current user & project info
  prowlr      ProwlrBot CLI preview
  skills      Skills & extensions
  roar        ROAR protocol intro
  about       About the project & who built it
  clear       Clear terminal`,

  ls: `agents          channels       config         docs
skills          protocols      marketplace    swarm
roar-protocol   console        .prowlrbot     README.md`,

  whoami: (lang) =>
    lang === "zh"
      ? `guest   (当前是演示模式，你是访客)

ProwlrBot 作者：kdairatchi
  GitHub  https://github.com/kdairatchi
  项目    https://github.com/ProwlrBot/prowlrbot

想用真机？ pip install prowlrbot && prowlr init --defaults`
      : `guest   (you're viewing the demo — that's you!)

Built by kdairatchi
  GitHub   https://github.com/kdairatchi
  ProwlrBot  https://github.com/ProwlrBot/prowlrbot

Want the real thing? pip install prowlrbot && prowlr init --defaults`,

  prowlr: `Usage: prowlr [OPTIONS] COMMAND [ARGS]...

  Self-hosted AI agent — monitor, automate, respond.

Commands:
  app         Start the server (console at :8088)
  init        Initialize config (API keys, channels, skills)
  channels    Discord, Telegram, DingTalk, Feishu...
  models      OpenAI, Anthropic, Groq, Ollama, local
  skills      List, enable, install from marketplace
  cron        Schedule tasks
  warroom     Multi-agent coordination
  market      Credits, tiers, marketplace CLI

  prowlr --help  for global options`,

  "prowlr --help": `Usage: prowlr [OPTIONS] COMMAND [ARGS]...
  Self-hosted AI agent — monitor, automate, respond.
Commands: app, init, channels, models, skills, cron, warroom, market
  prowlr --help  for global options`,

  skills: `Installed skills (sample):
  ✓ web-monitor    Watch URLs for changes
  ✓ pdf            Read & extract PDFs
  ✓ browser        Playwright automation
  ✓ shell          Safe command execution
  ✓ mcp            Model Context Protocol clients

  prowlr skills list     # list all
  prowlr market install  # install from marketplace`,

  roar: `ROAR — Reliable Open Agent Relay
  One protocol. Any agent. Identity · Discovery · Connect · Exchange · Stream

  Live endpoints (no auth):
    GET  /roar/health   → {"status":"ok","protocol":"roar/1.0"}
    GET  /roar/card     → Agent identity & endpoints

  Try the demo: https://prowlrbot.com/demo/roar-demo.html
  pip install roar-protocol   →  https://pypi.org/project/roar-protocol/`,

  about: (lang) =>
    lang === "zh"
      ? `ProwlrBot — Always watching. Always ready.

  自托管 AI 智能体：监控、定时任务、8 个通道、
  War Room、技能市场、ROAR 协议。你的密钥，你的数据。

  作者  kdairatchi  https://github.com/kdairatchi
  项目  https://github.com/ProwlrBot/prowlrbot
  License  Apache-2.0`
      : `ProwlrBot — Always watching. Always ready.

  Self-hosted AI agent: monitoring, cron, 8 channels,
  War Room, skills marketplace, ROAR protocol. Your keys, your data.

  Built by kdairatchi
    GitHub   https://github.com/kdairatchi
    Project  https://github.com/ProwlrBot/prowlrbot
  License  Apache-2.0`,

  clear: "",
};

function getOutput(cmd: string, lang: Lang): string {
  const raw = cmd.trim();
  const key = raw.toLowerCase();
  if (key === "clear") return "";
  const out = COMMANDS[key] ?? COMMANDS[raw];
  if (out === undefined) {
    return `prowlr: command not found: ${raw}\nTry 'help' to see available commands.`;
  }
  return typeof out === "function" ? out(lang) : out;
}

interface Line {
  type: "prompt" | "output";
  content: string;
}

const HINT_EN = "Try: help | whoami | prowlr | skills | roar | about";
const HINT_ZH = "试试: help | whoami | prowlr | skills | roar | about";

interface InteractiveTerminalProps {
  lang: Lang;
}

export function InteractiveTerminal({ lang }: InteractiveTerminalProps) {
  const [lines, setLines] = useState<Line[]>([
    {
      type: "output",
      content: lang === "zh"
        ? "ProwlrBot 终端演示 — 输入 help 查看命令。"
        : "ProwlrBot terminal demo — type help to see commands.",
    },
  ]);
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [lines, input]);

  const run = (raw: string) => {
    const cmd = raw.trim();
    if (!cmd) return;
    setLines((prev) => [...prev, { type: "prompt", content: cmd }]);
    const out = getOutput(cmd, lang);
    if (out) {
      setLines((prev) => [...prev, { type: "output", content: out }]);
    }
    setInput("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      run(input);
    }
  };

  return (
    <SectionWrapper
      id="terminal"
      label="Try it"
      title="See what you're getting into"
      description={
        lang === "zh"
          ? "在浏览器里体验 ProwlrBot 与 ROAR 协议 — 输入命令，查看示例输出。"
          : "Experience ProwlrBot and the ROAR protocol in your browser — type commands and see sample output."
      }
    >
      <div
        style={{
          background: "#0d1117",
          border: "1px solid var(--border)",
          borderRadius: "12px",
          overflow: "hidden",
          fontFamily: "ui-monospace, 'SF Mono', Menlo, monospace",
          fontSize: "0.8125rem",
          lineHeight: 1.65,
          maxWidth: "40rem",
          margin: "0 auto",
          boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
            padding: "0.5rem 1rem",
            borderBottom: "1px solid var(--border)",
            background: "rgba(0,0,0,0.3)",
          }}
        >
          <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#ff5f57" }} />
          <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#febc2e" }} />
          <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#28c840" }} />
          <span
            style={{
              marginLeft: "auto",
              fontSize: "0.6875rem",
              color: "var(--text-muted)",
              letterSpacing: "0.06em",
            }}
          >
            prowlr — demo
          </span>
        </div>
        <div
          ref={scrollRef}
          onClick={() => inputRef.current?.focus()}
          style={{
            padding: "1rem 1.25rem",
            minHeight: "18rem",
            maxHeight: "24rem",
            overflowY: "auto",
            cursor: "text",
          }}
        >
          {lines.map((line, i) => (
            <div key={i} style={{ marginBottom: line.type === "output" ? "0.5rem" : 0 }}>
              {line.type === "prompt" ? (
                <div>
                  <span style={{ color: "#28c840" }}>{PROMPT}</span>
                  <span style={{ color: "var(--accent)" }}>{line.content}</span>
                </div>
              ) : (
                <pre
                  style={{
                    margin: 0,
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                    color: "#8b949e",
                    fontFamily: "inherit",
                    fontSize: "inherit",
                    lineHeight: "inherit",
                  }}
                >
                  {line.content}
                </pre>
              )}
            </div>
          ))}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "0.25rem",
            }}
          >
            <span style={{ color: "#28c840" }}>{PROMPT}</span>
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              autoCapitalize="off"
              autoCorrect="off"
              autoComplete="off"
              spellCheck={false}
              aria-label="Terminal input"
              style={{
                flex: 1,
                minWidth: "8rem",
                background: "transparent",
                border: "none",
                outline: "none",
                color: "var(--text)",
                fontFamily: "inherit",
                fontSize: "inherit",
                caretColor: "var(--accent)",
              }}
            />
            <span
              style={{
                display: "inline-block",
                width: "0.5em",
                height: "1em",
                background: "var(--accent)",
                marginLeft: "1px",
                verticalAlign: "text-bottom",
                animation: "terminal-blink 1s step-end infinite",
              }}
              aria-hidden
            />
          </div>
        </div>
        <div
          style={{
            padding: "0.5rem 1rem",
            borderTop: "1px solid var(--border)",
            background: "rgba(0,0,0,0.2)",
            fontSize: "0.6875rem",
            color: "var(--text-muted)",
          }}
        >
          {lang === "zh" ? HINT_ZH : HINT_EN}
        </div>
      </div>
      <style>{`
        @keyframes terminal-blink {
          50% { opacity: 0; }
        }
      `}</style>
    </SectionWrapper>
  );
}
