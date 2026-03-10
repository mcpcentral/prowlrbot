import { useState, useEffect, useRef } from "react";

const TERMINAL_LINES = [
  { prompt: "prowlr", text: "warroom status", delay: 600 },
  { output: "War Room: ACTIVE  |  Agents: 3/3 online", delay: 400 },
  { output: "  scout-1    ▸ scanning marketplace repos", delay: 200 },
  { output: "  builder-2  ▸ implementing auth module", delay: 200 },
  { output: "  reviewer-3 ▸ reviewing PR #42", delay: 200 },
  { prompt: "prowlr", text: "broadcast 'Phase 2 complete'", delay: 800 },
  { output: "✓ Broadcast sent to 3 agents", delay: 400 },
  { prompt: "prowlr", text: "board", delay: 600 },
  { output: "┌─ Mission Board ────────────────┐", delay: 300 },
  { output: "│ ✅ Auth system     scout-1     │", delay: 150 },
  { output: "│ 🔄 API endpoints  builder-2   │", delay: 150 },
  { output: "│ ⏳ Test suite      unassigned  │", delay: 150 },
  { output: "└────────────────────────────────┘", delay: 300 },
  { prompt: "prowlr", text: "claim 'Test suite' --agent reviewer-3", delay: 700 },
  { output: "✓ Task claimed by reviewer-3", delay: 400 },
  { output: "✓ File locks acquired: tests/*", delay: 300 },
];

interface Line {
  type: "prompt" | "output";
  text: string;
}

export function AnimatedTerminal() {
  const [lines, setLines] = useState<Line[]>([]);
  const [currentText, setCurrentText] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const lineIndex = useRef(0);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let timeout: ReturnType<typeof setTimeout>;
    let charIndex = 0;

    function processNext() {
      if (lineIndex.current >= TERMINAL_LINES.length) {
        // Loop
        timeout = setTimeout(() => {
          lineIndex.current = 0;
          setLines([]);
          setCurrentText("");
          processNext();
        }, 2000);
        return;
      }

      const line = TERMINAL_LINES[lineIndex.current];

      if ("prompt" in line && line.prompt) {
        // Type out command character by character
        setIsTyping(true);
        charIndex = 0;
        const typeChar = () => {
          if (charIndex <= line.text.length) {
            setCurrentText(line.text.slice(0, charIndex));
            charIndex++;
            timeout = setTimeout(typeChar, 35 + Math.random() * 25);
          } else {
            // Typing done, commit line
            setIsTyping(false);
            setLines((prev) => [
              ...prev,
              { type: "prompt", text: line.text },
            ]);
            setCurrentText("");
            lineIndex.current++;
            timeout = setTimeout(processNext, line.delay);
          }
        };
        timeout = setTimeout(typeChar, line.delay);
      } else if ("output" in line && line.output) {
        // Instant output
        setLines((prev) => [
          ...prev,
          { type: "output" as const, text: line.output },
        ]);
        lineIndex.current++;
        timeout = setTimeout(processNext, line.delay);
      }
    }

    timeout = setTimeout(processNext, 800);
    return () => clearTimeout(timeout);
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [lines, currentText]);

  return (
    <div
      style={{
        background: "#0d1117",
        border: "1px solid #30363d",
        borderRadius: "0.75rem",
        overflow: "hidden",
        fontFamily: "ui-monospace, 'SF Mono', Menlo, monospace",
        fontSize: "0.8125rem",
        lineHeight: 1.7,
        width: "100%",
        maxWidth: "32rem",
      }}
    >
      {/* Title bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
          padding: "0.625rem 1rem",
          borderBottom: "1px solid #30363d",
          background: "#161b22",
        }}
      >
        <span
          style={{
            width: 12,
            height: 12,
            borderRadius: "50%",
            background: "#ff5f57",
          }}
        />
        <span
          style={{
            width: 12,
            height: 12,
            borderRadius: "50%",
            background: "#febc2e",
          }}
        />
        <span
          style={{
            width: 12,
            height: 12,
            borderRadius: "50%",
            background: "#28c840",
          }}
        />
        <span
          style={{
            marginLeft: "auto",
            fontSize: "0.6875rem",
            color: "#484f58",
            letterSpacing: "0.05em",
          }}
        >
          prowlr — war room
        </span>
      </div>
      {/* Terminal body */}
      <div
        ref={scrollRef}
        style={{
          padding: "1rem",
          maxHeight: "22rem",
          overflowY: "auto",
          scrollbarWidth: "none",
        }}
      >
        {lines.map((line, i) => (
          <div key={i}>
            {line.type === "prompt" ? (
              <span>
                <span style={{ color: "#28c840" }}>❯</span>{" "}
                <span style={{ color: "var(--accent)" }}>{line.text}</span>
              </span>
            ) : (
              <span style={{ color: "#8b949e" }}>{line.text}</span>
            )}
          </div>
        ))}
        {isTyping && (
          <div>
            <span style={{ color: "#28c840" }}>❯</span>{" "}
            <span style={{ color: "var(--accent)" }}>{currentText}</span>
            <span
              style={{
                display: "inline-block",
                width: "0.5em",
                height: "1.1em",
                background: "var(--accent)",
                marginLeft: "1px",
                verticalAlign: "text-bottom",
                animation: "blink 1s step-end infinite",
              }}
            />
          </div>
        )}
      </div>
      <style>{`
        @keyframes blink {
          50% { opacity: 0; }
        }
      `}</style>
    </div>
  );
}
