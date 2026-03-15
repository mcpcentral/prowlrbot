import { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Check, ArrowRight, Loader2 } from "lucide-react";

interface EarlyAccessFormProps {
  variant?: "hero" | "section";
  webhookUrl?: string;
}

interface WaitlistEntry {
  email: string;
  timestamp: number;
}

const STORAGE_KEY = "prowlrbot-waitlist";

function getWaitlist(): WaitlistEntry[] {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
  } catch {
    return [];
  }
}

function addToWaitlist(email: string): boolean {
  const list = getWaitlist();
  if (list.some((e) => e.email === email)) return false;
  list.push({ email, timestamp: Date.now() });
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
  return true;
}

export function EarlyAccessForm({
  variant = "hero",
  webhookUrl,
}: EarlyAccessFormProps) {
  const [email, setEmail] = useState("");
  const [state, setState] = useState<
    "idle" | "loading" | "success" | "duplicate" | "error"
  >("idle");
  const [count, setCount] = useState(0);

  useEffect(() => {
    setCount(getWaitlist().length);
  }, []);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const trimmed = email.trim().toLowerCase();
      if (!trimmed || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) {
        setState("error");
        setTimeout(() => setState("idle"), 2000);
        return;
      }

      setState("loading");

      const isNew = addToWaitlist(trimmed);
      if (!isNew) {
        setState("duplicate");
        setTimeout(() => setState("idle"), 3000);
        return;
      }

      // Fire-and-forget webhook
      if (webhookUrl) {
        fetch(webhookUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: trimmed, source: "website" }),
        }).catch(() => {});
      }

      await new Promise((r) => setTimeout(r, 600));
      setCount((c) => c + 1);
      setState("success");
      setEmail("");
    },
    [email, webhookUrl],
  );

  const isHero = variant === "hero";

  if (state === "success") {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        style={{
          display: "flex",
          alignItems: "center",
          gap: "var(--space-2)",
          padding: isHero ? "0.875rem 1.25rem" : "0.75rem 1rem",
          background: "rgba(0, 229, 255, 0.08)",
          border: "1px solid rgba(0, 229, 255, 0.2)",
          borderRadius: "0.5rem",
        }}
      >
        <div
          style={{
            width: 24,
            height: 24,
            borderRadius: "50%",
            background: "var(--accent)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          <Check size={14} strokeWidth={3} style={{ color: "var(--bg)" }} />
        </div>
        <div>
          <div
            style={{
              fontSize: "0.9375rem",
              fontWeight: 700,
              color: "var(--text)",
            }}
          >
            You're on the list!
          </div>
          <div
            style={{
              fontSize: "0.75rem",
              color: "var(--text-muted)",
            }}
          >
            We'll email you when your spot opens up.
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <div>
      <form
        onSubmit={handleSubmit}
        className="early-access-form"
        style={{
          display: "flex",
          gap: "0.5rem",
          maxWidth: isHero ? "28rem" : "24rem",
        }}
      >
        <div style={{ flex: 1, position: "relative" }}>
          <input
            type="email"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              if (state === "error" || state === "duplicate") setState("idle");
            }}
            placeholder="you@company.com"
            required
            style={{
              width: "100%",
              padding: isHero ? "0.75rem 1rem" : "0.625rem 0.875rem",
              fontSize: isHero ? "0.9375rem" : "0.875rem",
              fontFamily: "ui-monospace, 'SF Mono', Menlo, monospace",
              color: "var(--text)",
              background: "rgba(255,255,255,0.05)",
              border:
                state === "error"
                  ? "1px solid #ff4444"
                  : state === "duplicate"
                  ? "1px solid #ffaa00"
                  : "1px solid var(--border)",
              borderRadius: "0.5rem",
              outline: "none",
              transition: "border-color 0.2s ease, box-shadow 0.2s ease",
            }}
            onFocus={(e) => {
              e.target.style.borderColor = "var(--accent)";
              e.target.style.boxShadow = "0 0 0 2px var(--accent-dim)";
            }}
            onBlur={(e) => {
              if (state !== "error" && state !== "duplicate") {
                e.target.style.borderColor = "var(--border)";
                e.target.style.boxShadow = "none";
              }
            }}
          />
          <AnimatePresence>
            {state === "duplicate" && (
              <motion.div
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                style={{
                  position: "absolute",
                  top: "calc(100% + 4px)",
                  left: 0,
                  fontSize: "0.75rem",
                  color: "#ffaa00",
                  whiteSpace: "nowrap",
                }}
              >
                You're already on the list!
              </motion.div>
            )}
            {state === "error" && (
              <motion.div
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                style={{
                  position: "absolute",
                  top: "calc(100% + 4px)",
                  left: 0,
                  fontSize: "0.75rem",
                  color: "#ff4444",
                  whiteSpace: "nowrap",
                }}
              >
                Enter a valid email
              </motion.div>
            )}
          </AnimatePresence>
        </div>
        <button
          type="submit"
          disabled={state === "loading"}
          className="early-access-btn"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.375rem",
            padding: isHero ? "0.75rem 1.25rem" : "0.625rem 1rem",
            fontSize: isHero ? "0.9375rem" : "0.875rem",
            fontWeight: 700,
            color: "var(--bg)",
            background: "var(--accent)",
            border: "none",
            borderRadius: "0.5rem",
            cursor: state === "loading" ? "wait" : "pointer",
            transition: "all 0.2s ease",
            whiteSpace: "nowrap",
            flexShrink: 0,
          }}
        >
          {state === "loading" ? (
            <Loader2
              size={16}
              strokeWidth={2}
              className="early-access-spinner"
            />
          ) : (
            <>
              Get Access
              <ArrowRight size={16} strokeWidth={2.5} />
            </>
          )}
        </button>
      </form>

      {count > 0 && (
        <div
          style={{
            marginTop: "var(--space-2)",
            fontSize: "0.75rem",
            color: "var(--text-muted)",
            display: "flex",
            alignItems: "center",
            gap: "0.375rem",
          }}
        >
          <span
            style={{
              width: 6,
              height: 6,
              borderRadius: "50%",
              background: "#28c840",
              display: "inline-block",
            }}
          />
          {count} {count === 1 ? "developer" : "developers"} joined
        </div>
      )}

      <style>{`
        .early-access-btn:hover:not(:disabled) {
          opacity: 0.9;
          transform: translateY(-1px);
          box-shadow: 0 4px 20px var(--accent-glow);
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .early-access-spinner {
          animation: spin 1s linear infinite;
        }
        @media (max-width: 480px) {
          .early-access-form {
            flex-direction: column !important;
          }
        }
      `}</style>
    </div>
  );
}
