import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Check, Zap, Crown, Users, ChevronDown, ChevronUp } from "lucide-react";
import { Nav } from "../components/Nav";
import { Footer } from "../components/Footer";
import type { SiteConfig } from "../config";
import { type Lang } from "../i18n";

interface PricingProps {
  config: SiteConfig;
  lang: Lang;
  theme: "dark" | "light";
  onThemeToggle: () => void;
}

const TIERS = [
  {
    name: "Free",
    price: "$0",
    period: "/mo",
    credits: "1,000 credits/mo",
    description: "Perfect for individuals exploring AI automation.",
    icon: Zap,
    iconColor: "#9ca3af",
    featured: false,
    cta: "Get Started Free",
    ctaStyle: "outline" as const,
    features: [
      "1 agent",
      "1,000 credits/mo",
      "Basic monitoring",
      "Community support",
    ],
  },
  {
    name: "Pro",
    price: "$19",
    period: "/mo",
    credits: "10,000 credits/mo",
    description: "For power users who need more agents and advanced tooling.",
    icon: Crown,
    iconColor: "#60a5fa",
    featured: true,
    cta: "Upgrade to Pro",
    ctaStyle: "primary" as const,
    features: [
      "5 agents",
      "10,000 credits/mo",
      "Advanced monitoring",
      "Priority support",
      "API access",
    ],
  },
  {
    name: "Team",
    price: "$49",
    period: "/mo",
    credits: "50,000 credits/mo",
    description: "For teams running production AI workflows at scale.",
    icon: Users,
    iconColor: "#a78bfa",
    featured: false,
    cta: "Upgrade to Team",
    ctaStyle: "outline" as const,
    features: [
      "Unlimited agents",
      "50,000 credits/mo",
      "War Room",
      "Team collaboration",
      "SLA support",
    ],
  },
];

const FAQS = [
  {
    q: "What are credits?",
    a: "Credits are consumed when agents run tasks — things like monitoring a website, executing a cron job, calling an API, or running a tool. Each operation costs a small number of credits depending on complexity.",
  },
  {
    q: "Can I cancel anytime?",
    a: "Yes. There are no long-term contracts or cancellation fees. You can downgrade or cancel your plan at any time from your account settings and keep access until the end of your billing period.",
  },
  {
    q: "Is there a free trial?",
    a: "The Free tier is permanent — not a time-limited trial. You get 1,000 credits every month, forever, with no credit card required. Upgrade only when you need more.",
  },
  {
    q: "What happens when credits run out?",
    a: "Agents pause automatically when your monthly credit balance reaches zero. They resume at the start of the next billing cycle, or immediately if you upgrade your plan.",
  },
];

function FaqItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div
      style={{
        borderBottom: "1px solid var(--border)",
        padding: "var(--space-3) 0",
      }}
    >
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: "none",
          border: "none",
          padding: 0,
          cursor: "pointer",
          font: "inherit",
          color: "var(--text)",
          fontWeight: 600,
          fontSize: "1rem",
          textAlign: "left",
          gap: "var(--space-2)",
        }}
      >
        <span>{q}</span>
        {open ? (
          <ChevronUp size={18} style={{ flexShrink: 0, color: "var(--text-muted)" }} />
        ) : (
          <ChevronDown size={18} style={{ flexShrink: 0, color: "var(--text-muted)" }} />
        )}
      </button>
      {open && (
        <p
          style={{
            margin: "var(--space-2) 0 0",
            fontSize: "0.9375rem",
            color: "var(--text-muted)",
            lineHeight: 1.7,
          }}
        >
          {a}
        </p>
      )}
    </div>
  );
}

export function Pricing({ config, lang, theme, onThemeToggle }: PricingProps) {
  const navigate = useNavigate();
  const consoleUrl = config.consoleUrl ?? "https://prowlrbot.fly.dev";
  const creditsUrl = `${consoleUrl.replace(/\/$/, "")}/credits`;
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        minHeight: "100vh",
        background: "var(--bg)",
      }}
    >
      <Nav
        projectName={config.projectName}
        lang={lang}
        theme={theme}
        onThemeToggle={onThemeToggle}
        docsPath="/docs"
        repoUrl={config.repoUrl}
      />

      <main
        style={{
          flex: 1,
          padding: "calc(var(--space-5) + 64px) var(--space-4) var(--space-5)",
          maxWidth: "var(--container)",
          margin: "0 auto",
          width: "100%",
        }}
      >
        {/* Header */}
        <div
          style={{
            textAlign: "center",
            marginBottom: "var(--space-5)",
          }}
        >
          <h1
            style={{
              fontSize: "2.5rem",
              fontWeight: 800,
              color: "var(--text)",
              margin: "0 0 var(--space-2) 0",
              lineHeight: 1.2,
            }}
          >
            Simple, transparent pricing
          </h1>
          <p
            style={{
              fontSize: "1.125rem",
              color: "var(--text-muted)",
              margin: 0,
              lineHeight: 1.6,
            }}
          >
            Start free. Scale when you&apos;re ready.
          </p>
        </div>

        {/* Tier cards */}
        <div className="pricing-grid">
          {TIERS.map((tier) => {
            const Icon = tier.icon;
            return (
              <div
                key={tier.name}
                className={`pricing-card${tier.featured ? " pricing-card--featured" : ""}`}
                style={{
                  position: "relative",
                  display: "flex",
                  flexDirection: "column",
                  padding: "var(--space-4)",
                  background: tier.featured ? "var(--surface)" : "var(--bg-card, var(--surface))",
                  border: tier.featured
                    ? "2px solid var(--accent)"
                    : "1px solid var(--border)",
                  borderRadius: "1rem",
                }}
              >
                {tier.featured && (
                  <div
                    style={{
                      position: "absolute",
                      top: "-1px",
                      left: "50%",
                      transform: "translateX(-50%)",
                      background: "var(--accent)",
                      color: "var(--bg)",
                      fontSize: "0.6875rem",
                      fontWeight: 700,
                      letterSpacing: "0.08em",
                      textTransform: "uppercase",
                      padding: "0.25rem 0.875rem",
                      borderRadius: "0 0 0.5rem 0.5rem",
                      whiteSpace: "nowrap",
                    }}
                  >
                    Most Popular
                  </div>
                )}

                <div style={{ marginBottom: "var(--space-3)" }}>
                  <div
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      justifyContent: "center",
                      width: 40,
                      height: 40,
                      borderRadius: "0.625rem",
                      background: `${tier.iconColor}18`,
                      border: `1px solid ${tier.iconColor}30`,
                      marginBottom: "var(--space-2)",
                    }}
                  >
                    <Icon size={20} color={tier.iconColor} strokeWidth={1.75} />
                  </div>
                  <div
                    style={{
                      fontSize: "1.125rem",
                      fontWeight: 700,
                      color: "var(--text)",
                      marginBottom: "0.25rem",
                    }}
                  >
                    {tier.name}
                  </div>
                  <p
                    style={{
                      margin: 0,
                      fontSize: "0.875rem",
                      color: "var(--text-muted)",
                      lineHeight: 1.5,
                    }}
                  >
                    {tier.description}
                  </p>
                </div>

                <div style={{ marginBottom: "var(--space-3)" }}>
                  <span
                    style={{
                      fontSize: "2.25rem",
                      fontWeight: 800,
                      color: "var(--text)",
                      lineHeight: 1,
                    }}
                  >
                    {tier.price}
                  </span>
                  <span
                    style={{
                      fontSize: "0.9375rem",
                      color: "var(--text-muted)",
                      marginLeft: "0.125rem",
                    }}
                  >
                    {tier.period}
                  </span>
                  <div
                    style={{
                      marginTop: "0.375rem",
                      fontSize: "0.8125rem",
                      color: "var(--text-muted)",
                      fontWeight: 500,
                    }}
                  >
                    {tier.credits}
                  </div>
                </div>

                <ul
                  style={{
                    listStyle: "none",
                    margin: "0 0 var(--space-4) 0",
                    padding: 0,
                    display: "flex",
                    flexDirection: "column",
                    gap: "0.625rem",
                    flex: 1,
                  }}
                >
                  {tier.features.map((feature) => (
                    <li
                      key={feature}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "0.5rem",
                        fontSize: "0.875rem",
                        color: "var(--text-muted)",
                      }}
                    >
                      <Check
                        size={15}
                        strokeWidth={2.5}
                        style={{ flexShrink: 0, color: "var(--accent)" }}
                      />
                      {feature}
                    </li>
                  ))}
                </ul>

                {tier.name === "Free" ? (
                  <button
                    type="button"
                    className={`pricing-cta pricing-cta--${tier.ctaStyle}`}
                    style={{
                      width: "100%",
                      padding: "0.6875rem 1rem",
                      fontSize: "0.9375rem",
                      fontWeight: 700,
                      borderRadius: "0.5rem",
                      cursor: "pointer",
                      transition: "all 0.2s ease",
                      border:
                        tier.ctaStyle === "primary"
                          ? "none"
                          : "1px solid var(--border)",
                      background:
                        tier.ctaStyle === "primary"
                          ? "var(--accent)"
                          : "transparent",
                      color:
                        tier.ctaStyle === "primary"
                          ? "var(--bg)"
                          : "var(--text-muted)",
                    }}
                    onClick={() => {
                      const hero = document.querySelector(".hero-section");
                      if (hero) {
                        hero.scrollIntoView({ behavior: "smooth" });
                      } else {
                        navigate("/");
                      }
                    }}
                  >
                    {tier.cta}
                  </button>
                ) : (
                  <a
                    href={creditsUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`pricing-cta pricing-cta--${tier.ctaStyle}`}
                    style={{
                      display: "block",
                      width: "100%",
                      padding: "0.6875rem 1rem",
                      fontSize: "0.9375rem",
                      fontWeight: 700,
                      borderRadius: "0.5rem",
                      cursor: "pointer",
                      transition: "all 0.2s ease",
                      border:
                        tier.ctaStyle === "primary"
                          ? "none"
                          : "1px solid var(--border)",
                      background:
                        tier.ctaStyle === "primary"
                          ? "var(--accent)"
                          : "transparent",
                      color:
                        tier.ctaStyle === "primary"
                          ? "var(--bg)"
                          : "var(--text-muted)",
                      textAlign: "center",
                      textDecoration: "none",
                      boxSizing: "border-box",
                    }}
                  >
                    {tier.cta}
                  </a>
                )}
              </div>
            );
          })}
        </div>

        {/* FAQ */}
        <div
          style={{
            maxWidth: 680,
            margin: "calc(var(--space-5) * 1.5) auto 0",
          }}
        >
          <h2
            style={{
              fontSize: "1.5rem",
              fontWeight: 700,
              color: "var(--text)",
              marginBottom: "var(--space-3)",
              textAlign: "center",
            }}
          >
            Frequently asked questions
          </h2>
          <div>
            {FAQS.map((item) => (
              <FaqItem key={item.q} q={item.q} a={item.a} />
            ))}
          </div>
        </div>
      </main>

      <Footer lang={lang} />

      <style>{`
        .pricing-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: var(--space-3);
          align-items: start;
        }
        .pricing-card--featured {
          box-shadow: 0 4px 32px rgba(0, 212, 170, 0.12);
        }
        .pricing-cta--outline:hover {
          border-color: var(--accent) !important;
          color: var(--accent) !important;
        }
        .pricing-cta--primary:hover {
          opacity: 0.9;
          transform: translateY(-1px);
          box-shadow: 0 2px 16px var(--accent-glow, rgba(0, 212, 170, 0.3));
        }
        @media (max-width: 900px) {
          .pricing-grid {
            grid-template-columns: 1fr 1fr;
          }
        }
        @media (max-width: 600px) {
          .pricing-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
}
