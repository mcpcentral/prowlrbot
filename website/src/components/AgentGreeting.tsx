import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Briefcase,
  GraduationCap,
  Palette,
  Laptop,
  Heart,
  Compass,
  Wrench,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

const GREETING_KEY = "prowlr-greeted";
const PERSONA_KEY = "prowlr-persona";

/* ── Agent particle floating in the background ── */
interface Particle {
  id: number;
  x: number;
  y: number;
  size: number;
  delay: number;
  duration: number;
}

function makeParticles(count: number): Particle[] {
  return Array.from({ length: count }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    y: Math.random() * 100,
    size: 3 + Math.random() * 5,
    delay: Math.random() * 3,
    duration: 4 + Math.random() * 6,
  }));
}

const PERSONAS = [
  {
    id: "business",
    label: "Business Owner",
    icon: Briefcase,
    desc: "Automate ops, track competitors, manage teams",
    color: "#00E5FF",
  },
  {
    id: "student",
    label: "Student",
    icon: GraduationCap,
    desc: "Research, study plans, deadline tracking",
    color: "#7C4DFF",
  },
  {
    id: "creator",
    label: "Creator",
    icon: Palette,
    desc: "Content scheduling, analytics, growth",
    color: "#FF6D00",
  },
  {
    id: "developer",
    label: "Developer",
    icon: Laptop,
    desc: "CI/CD, code review, monitoring agents",
    color: "#00E676",
  },
  {
    id: "parent",
    label: "Parent",
    icon: Heart,
    desc: "Family schedules, meal plans, reminders",
    color: "#FF4081",
  },
  {
    id: "freelancer",
    label: "Freelancer",
    icon: Wrench,
    desc: "Invoices, client follow-ups, time tracking",
    color: "#FFD740",
  },
  {
    id: "explorer",
    label: "Just Exploring",
    icon: Compass,
    desc: "Show me everything",
    color: "#00E5FF",
  },
] as const;

/* ── Typing effect ── */
function useTyping(text: string, speed = 40, startDelay = 0) {
  const [displayed, setDisplayed] = useState("");
  const [done, setDone] = useState(false);

  useEffect(() => {
    let i = 0;
    let timeout: ReturnType<typeof setTimeout>;

    const startTyping = () => {
      const tick = () => {
        if (i < text.length) {
          setDisplayed(text.slice(0, i + 1));
          i++;
          timeout = setTimeout(tick, speed);
        } else {
          setDone(true);
        }
      };
      tick();
    };

    timeout = setTimeout(startTyping, startDelay);
    return () => clearTimeout(timeout);
  }, [text, speed, startDelay]);

  return { displayed, done };
}

/* ── Floating agent nodes background ── */
function AgentField({ particles }: { particles: Particle[] }) {
  return (
    <div
      aria-hidden
      style={{
        position: "absolute",
        inset: 0,
        overflow: "hidden",
        pointerEvents: "none",
      }}
    >
      {/* Radial glow */}
      <div
        style={{
          position: "absolute",
          top: "30%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          width: "60vw",
          height: "60vw",
          maxWidth: 700,
          maxHeight: 700,
          borderRadius: "50%",
          background:
            "radial-gradient(circle, rgba(0,229,255,0.08) 0%, transparent 70%)",
        }}
      />

      {/* Connection lines */}
      <svg
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
        }}
      >
        {particles.slice(0, 8).map((p, i) => {
          const next = particles[(i + 3) % particles.length];
          return (
            <motion.line
              key={`line-${p.id}`}
              x1={`${p.x}%`}
              y1={`${p.y}%`}
              x2={`${next.x}%`}
              y2={`${next.y}%`}
              stroke="rgba(0,229,255,0.06)"
              strokeWidth={1}
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{
                duration: 2 + i * 0.3,
                delay: 0.5 + i * 0.2,
                ease: "easeInOut",
              }}
            />
          );
        })}
      </svg>

      {/* Particles */}
      {particles.map((p) => (
        <motion.div
          key={p.id}
          style={{
            position: "absolute",
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: p.size,
            height: p.size,
            borderRadius: "50%",
            background: "var(--accent)",
            boxShadow: `0 0 ${p.size * 3}px rgba(0,229,255,0.3)`,
          }}
          initial={{ opacity: 0, scale: 0 }}
          animate={{
            opacity: [0, 0.7, 0.3, 0.7, 0],
            scale: [0, 1, 0.8, 1, 0],
            y: [0, -20, 10, -15, 0],
          }}
          transition={{
            duration: p.duration,
            delay: p.delay,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      ))}
    </div>
  );
}

/* ── Main Component ── */
export function AgentGreeting() {
  const [show, setShow] = useState(false);
  const [phase, setPhase] = useState<"greeting" | "quiz" | "done">("greeting");
  const [particles] = useState(() => makeParticles(20));
  const navigate = useNavigate();

  useEffect(() => {
    if (!localStorage.getItem(GREETING_KEY)) {
      setShow(true);
      document.body.style.overflow = "hidden";
    }
  }, []);

  const { displayed: greetText, done: greetDone } = useTyping(
    "Hello. I'm Prowlr — your personal automation agent.",
    45,
    800,
  );

  const { displayed: subText, done: subDone } = useTyping(
    "Tell me about yourself, and I'll set up agents tailored just for you.",
    35,
    greetDone ? 0 : 99999,
  );

  const handlePersona = useCallback(
    (personaId: string) => {
      localStorage.setItem(GREETING_KEY, "1");
      localStorage.setItem(PERSONA_KEY, personaId);
      setPhase("done");

      setTimeout(() => {
        document.body.style.overflow = "";
        setShow(false);
        if (personaId !== "explorer") {
          navigate(`/marketplace?persona=${personaId}`);
        }
      }, 800);
    },
    [navigate],
  );

  const skip = useCallback(() => {
    localStorage.setItem(GREETING_KEY, "1");
    setPhase("done");
    setTimeout(() => {
      document.body.style.overflow = "";
      setShow(false);
    }, 500);
  }, []);

  if (!show) return null;

  return (
    <AnimatePresence>
      {phase !== "done" && (
        <motion.div
          key="greeting-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.6 }}
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 9999,
            background: "#0a0a0f",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <AgentField particles={particles} />

          {/* Skip button */}
          <button
            type="button"
            onClick={skip}
            style={{
              position: "absolute",
              top: "var(--space-4)",
              right: "var(--space-4)",
              background: "none",
              border: "1px solid rgba(255,255,255,0.15)",
              borderRadius: "0.375rem",
              padding: "0.375rem 0.875rem",
              color: "rgba(255,255,255,0.4)",
              fontSize: "0.75rem",
              cursor: "pointer",
              zIndex: 10,
              transition: "all 0.2s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = "rgba(255,255,255,0.8)";
              e.currentTarget.style.borderColor = "rgba(255,255,255,0.3)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = "rgba(255,255,255,0.4)";
              e.currentTarget.style.borderColor = "rgba(255,255,255,0.15)";
            }}
          >
            Skip
          </button>

          {/* Greeting Phase */}
          <AnimatePresence mode="wait">
            {phase === "greeting" && (
              <motion.div
                key="greet"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0, y: -30 }}
                transition={{ duration: 0.5 }}
                style={{
                  position: "relative",
                  zIndex: 5,
                  textAlign: "center",
                  maxWidth: 600,
                  padding: "0 var(--space-4)",
                }}
              >
                {/* Prowlr eye / logo */}
                <motion.div
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ duration: 0.8, ease: "easeOut" }}
                  style={{ marginBottom: "var(--space-4)" }}
                >
                  <div
                    style={{
                      width: 72,
                      height: 72,
                      margin: "0 auto",
                      borderRadius: "50%",
                      background:
                        "radial-gradient(circle, rgba(0,229,255,0.2) 0%, transparent 70%)",
                      border: "2px solid rgba(0,229,255,0.3)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      boxShadow: "0 0 40px rgba(0,229,255,0.15)",
                    }}
                  >
                    <Sparkles size={32} color="#00E5FF" strokeWidth={1.5} />
                  </div>
                </motion.div>

                <p
                  style={{
                    fontSize: "clamp(1.25rem, 3vw, 1.75rem)",
                    fontWeight: 700,
                    color: "#f0f0f5",
                    lineHeight: 1.4,
                    minHeight: "2.5em",
                    fontFamily: "inherit",
                  }}
                >
                  {greetText}
                  {!greetDone && (
                    <span
                      style={{
                        display: "inline-block",
                        width: 2,
                        height: "1.2em",
                        background: "var(--accent)",
                        marginLeft: 2,
                        verticalAlign: "text-bottom",
                        animation: "cursor-blink 1s step-end infinite",
                      }}
                    />
                  )}
                </p>

                {greetDone && (
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    style={{
                      marginTop: "var(--space-2)",
                      fontSize: "1rem",
                      color: "rgba(255,255,255,0.5)",
                      lineHeight: 1.5,
                      minHeight: "1.5em",
                    }}
                  >
                    {subText}
                    {!subDone && (
                      <span
                        style={{
                          display: "inline-block",
                          width: 2,
                          height: "1em",
                          background: "var(--accent)",
                          marginLeft: 2,
                          verticalAlign: "text-bottom",
                          animation: "cursor-blink 1s step-end infinite",
                        }}
                      />
                    )}
                  </motion.p>
                )}

                {subDone && (
                  <motion.button
                    type="button"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    onClick={() => setPhase("quiz")}
                    style={{
                      marginTop: "var(--space-4)",
                      padding: "0.75rem 2rem",
                      fontSize: "0.9375rem",
                      fontWeight: 700,
                      color: "#0a0a0f",
                      background: "#00E5FF",
                      border: "none",
                      borderRadius: "0.5rem",
                      cursor: "pointer",
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "0.5rem",
                      transition: "transform 0.2s, box-shadow 0.2s",
                    }}
                    whileHover={{
                      scale: 1.03,
                      boxShadow: "0 4px 24px rgba(0,229,255,0.3)",
                    }}
                    whileTap={{ scale: 0.97 }}
                  >
                    Pick Your Life <ArrowRight size={18} />
                  </motion.button>
                )}
              </motion.div>
            )}

            {/* Quiz Phase */}
            {phase === "quiz" && (
              <motion.div
                key="quiz"
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.5 }}
                style={{
                  position: "relative",
                  zIndex: 5,
                  textAlign: "center",
                  maxWidth: 720,
                  padding: "0 var(--space-4)",
                  width: "100%",
                }}
              >
                <motion.h2
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  style={{
                    fontSize: "clamp(1.25rem, 3vw, 1.625rem)",
                    fontWeight: 700,
                    color: "#f0f0f5",
                    marginBottom: "var(--space-1)",
                  }}
                >
                  What describes you best?
                </motion.h2>
                <p
                  style={{
                    fontSize: "0.875rem",
                    color: "rgba(255,255,255,0.4)",
                    marginBottom: "var(--space-4)",
                  }}
                >
                  We'll curate agents and workflows for your world
                </p>

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                    gap: "var(--space-2)",
                    maxWidth: 640,
                    margin: "0 auto",
                  }}
                >
                  {PERSONAS.map((p, i) => {
                    const Icon = p.icon;
                    return (
                      <motion.button
                        type="button"
                        key={p.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 + i * 0.06 }}
                        onClick={() => handlePersona(p.id)}
                        whileHover={{
                          scale: 1.04,
                          borderColor: p.color,
                          boxShadow: `0 0 20px ${p.color}22`,
                        }}
                        whileTap={{ scale: 0.96 }}
                        style={{
                          background: "rgba(255,255,255,0.03)",
                          border: "1px solid rgba(255,255,255,0.08)",
                          borderRadius: "0.75rem",
                          padding: "var(--space-3) var(--space-2)",
                          cursor: "pointer",
                          display: "flex",
                          flexDirection: "column",
                          alignItems: "center",
                          gap: "0.5rem",
                          transition: "border-color 0.2s, box-shadow 0.2s",
                        }}
                      >
                        <Icon size={28} color={p.color} strokeWidth={1.5} />
                        <span
                          style={{
                            fontSize: "0.875rem",
                            fontWeight: 600,
                            color: "#f0f0f5",
                          }}
                        >
                          {p.label}
                        </span>
                        <span
                          style={{
                            fontSize: "0.6875rem",
                            color: "rgba(255,255,255,0.4)",
                            lineHeight: 1.4,
                          }}
                        >
                          {p.desc}
                        </span>
                      </motion.button>
                    );
                  })}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <style>{`
            @keyframes cursor-blink {
              0%, 100% { opacity: 1; }
              50% { opacity: 0; }
            }
          `}</style>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
