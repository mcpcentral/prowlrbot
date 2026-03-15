import { useState, useMemo, useEffect } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { motion, AnimatePresence } from "motion/react";
import {
  Search,
  Star,
  Clock,
  Download,
  Shield,
  ChevronRight,
  Home,
  Briefcase,
  BookOpen,
  Palette,
  Laptop,
  Code,
  Globe,
  Zap,
  Target,
  Lock,
  RefreshCw,
  MessageSquare,
  Terminal,
  AlertTriangle,
  CheckCircle,
  Copy,
  Check,
  Eye,
} from "lucide-react";
import { Nav } from "../components/Nav";
import { Footer } from "../components/Footer";
import type { SiteConfig } from "../config";
import { type Lang } from "../i18n";

/* ── Listing data (embedded for static site) ─────────────────────────── */

interface SkillScan {
  automation: number;
  ease: number;
  privacy: number;
  reliability: number;
  personalization: number;
}

interface Listing {
  id: string;
  title: string;
  description: string;
  category: string;
  difficulty: "beginner" | "intermediate" | "advanced";
  setup_time_minutes: number;
  persona_tags: string[];
  tags: string[];
  skill_scan: SkillScan;
  before_after: { before: string; after: string; time_saved: string };
  works_with: string[];
  user_stories: { quote: string; name: string; role: string }[];
  hero_animation: string;
  downloads: number;
  rating: number;
  install_cmd: string;
  risk_level: "low" | "medium" | "high";
  permissions: string[];
  preview_commands: string[];
}

const LISTINGS: Listing[] = [
  {
    id: "morning-briefing",
    title: "Morning Briefing",
    description:
      "Your entire day summarized in 30 seconds — email, calendar, weather, and news before your coffee's ready",
    category: "skills",
    difficulty: "beginner",
    setup_time_minutes: 2,
    persona_tags: ["parent", "business", "everyone"],
    tags: ["email", "daily", "productivity"],
    downloads: 1247,
    rating: 4.6,
    skill_scan: {
      automation: 8,
      ease: 10,
      privacy: 8,
      reliability: 9,
      personalization: 7,
    },
    before_after: {
      before: "45 min sorting email every morning",
      after: "30-second glance, done",
      time_saved: "~6 hrs/week",
    },
    works_with: ["Gmail", "Outlook", "Google Calendar", "iCal", "RSS"],
    user_stories: [
      {
        quote: "I haven't opened my email app in a month.",
        name: "Sarah K.",
        role: "Working mom",
      },
    ],
    hero_animation: "sort",
    install_cmd: "prowlr market install morning-briefing",
    risk_level: "low",
    permissions: ["Read email (headers only)", "Read calendar", "Weather API"],
    preview_commands: [
      "prowlr run morning-briefing",
      "prowlr briefing --preview",
    ],
  },
  {
    id: "homework-helper",
    title: "Homework Helper",
    description:
      "Walks your kids through problems step-by-step with hints — never gives away the answer",
    category: "agents",
    difficulty: "beginner",
    setup_time_minutes: 3,
    persona_tags: ["parent", "student"],
    tags: ["education", "kids", "math", "science"],
    downloads: 892,
    rating: 4.8,
    skill_scan: {
      automation: 6,
      ease: 10,
      privacy: 9,
      reliability: 8,
      personalization: 9,
    },
    before_after: {
      before: "2 hrs helping with homework after work",
      after: "Kids work independently, you review",
      time_saved: "~8 hrs/week",
    },
    works_with: ["Any browser", "PDF textbooks"],
    user_stories: [
      {
        quote: "My daughter went from C to A- in math.",
        name: "James R.",
        role: "Father of two",
      },
    ],
    hero_animation: "write",
    install_cmd: "prowlr market install homework-helper",
    risk_level: "low",
    permissions: ["Read uploaded files", "AI model access"],
    preview_commands: [
      "prowlr run homework-helper",
      "prowlr agent chat homework-helper",
    ],
  },
  {
    id: "invoice-chaser",
    title: "Invoice Chaser",
    description:
      "Tracks every unpaid invoice, sends polite follow-ups on schedule — you never chase money again",
    category: "agents",
    difficulty: "beginner",
    setup_time_minutes: 5,
    persona_tags: ["business", "freelancer"],
    tags: ["invoicing", "finance", "email", "automation"],
    downloads: 1034,
    rating: 4.7,
    skill_scan: {
      automation: 9,
      ease: 8,
      privacy: 7,
      reliability: 9,
      personalization: 8,
    },
    before_after: {
      before: "Manually tracking 15+ invoices, forgetting follow-ups",
      after: "Zero missed payments, automated reminders",
      time_saved: "~4 hrs/week",
    },
    works_with: ["Gmail", "Outlook", "QuickBooks", "Stripe", "PayPal"],
    user_stories: [
      {
        quote: "Got paid $12K in overdue invoices the first week.",
        name: "Lisa M.",
        role: "Freelance designer",
      },
    ],
    hero_animation: "monitor",
    install_cmd: "prowlr market install invoice-chaser",
    risk_level: "medium",
    permissions: ["Send email", "Read invoices", "Payment API access"],
    preview_commands: [
      "prowlr run invoice-chaser --dry-run",
      "prowlr invoices list",
    ],
  },
  {
    id: "study-planner",
    title: "Study Planner",
    description:
      "Builds smart study schedules from your syllabus and exam dates — adapts when life gets in the way",
    category: "agents",
    difficulty: "beginner",
    setup_time_minutes: 3,
    persona_tags: ["student"],
    tags: ["education", "planning", "productivity"],
    downloads: 756,
    rating: 4.5,
    skill_scan: {
      automation: 7,
      ease: 9,
      privacy: 9,
      reliability: 8,
      personalization: 9,
    },
    before_after: {
      before: "Cramming the night before every exam",
      after: "Steady daily study, no all-nighters",
      time_saved: "~5 hrs/week",
    },
    works_with: ["Google Calendar", "iCal", "PDF syllabi"],
    user_stories: [
      {
        quote: "Went from 2.8 to 3.6 GPA in one semester.",
        name: "Tyler J.",
        role: "College sophomore",
      },
    ],
    hero_animation: "write",
    install_cmd: "prowlr market install study-planner",
    risk_level: "low",
    permissions: ["Read calendar", "Read uploaded files"],
    preview_commands: [
      "prowlr run study-planner",
      "prowlr study schedule --this-week",
    ],
  },
  {
    id: "content-scheduler",
    title: "Content Scheduler",
    description:
      "Plan, write, and schedule social media posts across Twitter, Instagram, LinkedIn from one place with AI-optimized posting times",
    category: "workflows",
    difficulty: "intermediate",
    setup_time_minutes: 10,
    persona_tags: ["creator", "business"],
    tags: ["social-media", "scheduling", "marketing", "content"],
    downloads: 1456,
    rating: 4.6,
    skill_scan: {
      automation: 9,
      ease: 7,
      privacy: 6,
      reliability: 8,
      personalization: 9,
    },
    before_after: {
      before: "Logging into 4 platforms daily, posting inconsistently",
      after: "Full week queued in one 30-minute Sunday session",
      time_saved: "~6 hrs/week",
    },
    works_with: [
      "Twitter/X",
      "Instagram",
      "LinkedIn",
      "Buffer",
      "Google Sheets",
    ],
    user_stories: [
      {
        quote: "Engagement went up 40% just by posting at the right times.",
        name: "Kayla J.",
        role: "Small business owner",
      },
    ],
    hero_animation: "sort",
    install_cmd: "prowlr market install content-scheduler",
    risk_level: "medium",
    permissions: [
      "Post to social media",
      "Read analytics",
      "OAuth to platforms",
    ],
    preview_commands: [
      "prowlr run content-scheduler --preview",
      "prowlr schedule list",
    ],
  },
  {
    id: "competitor-watch",
    title: "Competitor Watch",
    description:
      "Monitors competitor websites for pricing changes, new features, and content updates — alerts you instantly",
    category: "skills",
    difficulty: "intermediate",
    setup_time_minutes: 5,
    persona_tags: ["business", "freelancer"],
    tags: ["monitoring", "competitive-intel", "alerts"],
    downloads: 823,
    rating: 4.4,
    skill_scan: {
      automation: 9,
      ease: 8,
      privacy: 8,
      reliability: 8,
      personalization: 7,
    },
    before_after: {
      before: "Manually checking competitor sites weekly",
      after: "Instant alerts when anything changes",
      time_saved: "~3 hrs/week",
    },
    works_with: ["Any website", "Slack", "Email", "Discord"],
    user_stories: [
      {
        quote:
          "Caught a competitor's price drop 2 hours after they posted it. Matched immediately.",
        name: "Marcus D.",
        role: "E-commerce owner",
      },
    ],
    hero_animation: "monitor",
    install_cmd: "prowlr market install competitor-watch",
    risk_level: "low",
    permissions: ["Web scraping (public pages only)", "Send notifications"],
    preview_commands: [
      "prowlr monitor add https://competitor.com",
      "prowlr monitor list",
    ],
  },
  {
    id: "client-followup",
    title: "Client Follow-up",
    description:
      "Automated, personalized check-ins that keep leads warm and clients happy — like a CRM that actually works",
    category: "agents",
    difficulty: "intermediate",
    setup_time_minutes: 8,
    persona_tags: ["freelancer", "business"],
    tags: ["crm", "email", "sales", "automation"],
    downloads: 645,
    rating: 4.5,
    skill_scan: {
      automation: 8,
      ease: 7,
      privacy: 7,
      reliability: 9,
      personalization: 9,
    },
    before_after: {
      before: "Leads going cold because you forgot to follow up",
      after: "Every client gets personal attention on schedule",
      time_saved: "~5 hrs/week",
    },
    works_with: ["Gmail", "Outlook", "Google Contacts", "Notion", "Airtable"],
    user_stories: [
      {
        quote:
          "Closed 3 deals in my first month just from reactivated cold leads.",
        name: "Jordan P.",
        role: "Freelance consultant",
      },
    ],
    hero_animation: "write",
    install_cmd: "prowlr market install client-followup",
    risk_level: "medium",
    permissions: ["Send email", "Read contacts", "Calendar access"],
    preview_commands: [
      "prowlr run client-followup --dry-run",
      "prowlr clients list",
    ],
  },
  {
    id: "site-monitor",
    title: "Site Monitor",
    description:
      "Uptime monitoring, SSL expiry alerts, and content change detection — know before your users do",
    category: "skills",
    difficulty: "intermediate",
    setup_time_minutes: 3,
    persona_tags: ["developer", "business"],
    tags: ["monitoring", "uptime", "devops", "alerts"],
    downloads: 1102,
    rating: 4.7,
    skill_scan: {
      automation: 10,
      ease: 8,
      privacy: 9,
      reliability: 9,
      personalization: 6,
    },
    before_after: {
      before: "Finding out your site is down from angry customers",
      after: "Alert in 30 seconds, fix before anyone notices",
      time_saved: "~2 hrs/week",
    },
    works_with: ["Any URL", "Slack", "Discord", "PagerDuty", "Email"],
    user_stories: [
      {
        quote:
          "Caught an SSL expiry 3 days before it would have blocked our checkout page.",
        name: "Nina K.",
        role: "CTO, startup",
      },
    ],
    hero_animation: "monitor",
    install_cmd: "prowlr market install site-monitor",
    risk_level: "low",
    permissions: ["HTTP requests (public URLs only)", "Send notifications"],
    preview_commands: [
      "prowlr monitor add https://mysite.com",
      "prowlr monitor status",
    ],
  },
  {
    id: "email-declutterer",
    title: "Email Declutterer",
    description:
      "Unsubscribes from junk, sorts what matters, drafts quick replies — your inbox finally at zero",
    category: "skills",
    difficulty: "beginner",
    setup_time_minutes: 3,
    persona_tags: ["everyone"],
    tags: ["email", "productivity", "cleanup"],
    downloads: 1589,
    rating: 4.4,
    skill_scan: {
      automation: 9,
      ease: 9,
      privacy: 7,
      reliability: 8,
      personalization: 7,
    },
    before_after: {
      before: "300+ unread emails, constant anxiety",
      after: "Inbox zero every morning",
      time_saved: "~5 hrs/week",
    },
    works_with: ["Gmail", "Outlook", "Yahoo", "iCloud Mail"],
    user_stories: [
      {
        quote: "I had 14,000 unread emails. Now I have zero.",
        name: "David P.",
        role: "Small business owner",
      },
    ],
    hero_animation: "sort",
    install_cmd: "prowlr market install email-declutterer",
    risk_level: "medium",
    permissions: ["Read/write email", "Unsubscribe actions"],
    preview_commands: [
      "prowlr run email-declutterer --dry-run",
      "prowlr inbox stats",
    ],
  },
  {
    id: "meeting-summarizer",
    title: "Meeting Summarizer",
    description:
      "Turns meeting notes into clean action items and emails them to everyone — no more 'what did we decide?'",
    category: "skills",
    difficulty: "beginner",
    setup_time_minutes: 3,
    persona_tags: ["business", "freelancer"],
    tags: ["meetings", "productivity", "email"],
    downloads: 934,
    rating: 4.6,
    skill_scan: {
      automation: 8,
      ease: 9,
      privacy: 8,
      reliability: 9,
      personalization: 6,
    },
    before_after: {
      before: "Scribbled notes nobody reads",
      after: "Clear action items sent in 60 seconds",
      time_saved: "~3 hrs/week",
    },
    works_with: ["Google Docs", "Notion", "Gmail", "Slack"],
    user_stories: [
      {
        quote:
          "Our meetings are half as long now. Everyone knows their action items.",
        name: "Priya S.",
        role: "Product manager",
      },
    ],
    hero_animation: "write",
    install_cmd: "prowlr market install meeting-summarizer",
    risk_level: "low",
    permissions: ["Read documents", "Send email/Slack messages"],
    preview_commands: [
      "prowlr run meeting-summarizer --input notes.md",
      "prowlr meetings list",
    ],
  },
  {
    id: "meal-planner",
    title: "Meal Planner",
    description:
      "Weekly meal plans based on your budget, dietary needs, and what's already in your fridge",
    category: "workflows",
    difficulty: "beginner",
    setup_time_minutes: 5,
    persona_tags: ["parent", "everyone"],
    tags: ["food", "planning", "family", "budget"],
    downloads: 678,
    rating: 4.3,
    skill_scan: {
      automation: 7,
      ease: 9,
      privacy: 9,
      reliability: 7,
      personalization: 10,
    },
    before_after: {
      before: "'What's for dinner?' panic at 5 PM every day",
      after: "Week planned in 2 minutes, grocery list ready",
      time_saved: "~4 hrs/week",
    },
    works_with: ["Any browser", "Grocery delivery apps"],
    user_stories: [
      {
        quote: "We cut our grocery bill by 30% and eat better.",
        name: "Maria G.",
        role: "Mom of three",
      },
    ],
    hero_animation: "pulse",
    install_cmd: "prowlr market install meal-planner",
    risk_level: "low",
    permissions: ["AI model access", "Local file storage"],
    preview_commands: ["prowlr run meal-planner", "prowlr meals --this-week"],
  },
  {
    id: "contract-reviewer",
    title: "Contract Reviewer",
    description:
      "Scans contracts for red flags and explains every clause in plain English — your AI paralegal",
    category: "skills",
    difficulty: "beginner",
    setup_time_minutes: 2,
    persona_tags: ["freelancer", "business"],
    tags: ["legal", "contracts", "review"],
    downloads: 567,
    rating: 4.5,
    skill_scan: {
      automation: 7,
      ease: 10,
      privacy: 9,
      reliability: 8,
      personalization: 5,
    },
    before_after: {
      before: "Signing contracts you don't fully understand",
      after: "Every clause explained, red flags highlighted",
      time_saved: "~2 hrs/contract",
    },
    works_with: ["PDF files", "Word documents"],
    user_stories: [
      {
        quote:
          "Caught a non-compete clause that would have cost me my next client.",
        name: "Alex T.",
        role: "Freelance developer",
      },
    ],
    hero_animation: "scan",
    install_cmd: "prowlr market install contract-reviewer",
    risk_level: "low",
    permissions: ["Read uploaded files only", "AI model access"],
    preview_commands: [
      "prowlr run contract-reviewer --file contract.pdf",
      "prowlr review scan",
    ],
  },
  {
    id: "daily-digest",
    title: "Daily Digest",
    description:
      "Everything that matters — email, calendar, news, weather — delivered as a morning snapshot",
    category: "workflows",
    difficulty: "beginner",
    setup_time_minutes: 2,
    persona_tags: ["everyone"],
    tags: ["daily", "productivity", "news", "email"],
    downloads: 2103,
    rating: 4.7,
    skill_scan: {
      automation: 9,
      ease: 10,
      privacy: 7,
      reliability: 9,
      personalization: 8,
    },
    before_after: {
      before: "Checking 6 different apps every morning",
      after: "One summary, 30 seconds, done",
      time_saved: "~7 hrs/week",
    },
    works_with: ["Gmail", "Outlook", "Google Calendar", "RSS", "Weather APIs"],
    user_stories: [
      {
        quote:
          "It's the first thing I read every morning. Better than any news app.",
        name: "Rachel W.",
        role: "Marketing director",
      },
    ],
    hero_animation: "sort",
    install_cmd: "prowlr market install daily-digest",
    risk_level: "low",
    permissions: ["Read email", "Read calendar", "Weather/News APIs"],
    preview_commands: [
      "prowlr run daily-digest --preview",
      "prowlr digest today",
    ],
  },
  {
    id: "smart-reminder",
    title: "Smart Reminder",
    description:
      "Context-aware reminders that know the right time and place — not just dumb alarms",
    category: "skills",
    difficulty: "beginner",
    setup_time_minutes: 1,
    persona_tags: ["everyone"],
    tags: ["reminders", "productivity", "daily"],
    downloads: 1890,
    rating: 4.5,
    skill_scan: {
      automation: 8,
      ease: 10,
      privacy: 9,
      reliability: 9,
      personalization: 8,
    },
    before_after: {
      before: "Forgetting tasks, missing appointments",
      after: "Right reminder, right time, every time",
      time_saved: "~3 hrs/week",
    },
    works_with: ["Google Calendar", "iCal", "Slack", "Email"],
    user_stories: [
      {
        quote:
          "It reminded me to take my medication when I actually walked into the kitchen. Genius.",
        name: "Robert H.",
        role: "Retiree",
      },
    ],
    hero_animation: "pulse",
    install_cmd: "prowlr market install smart-reminder",
    risk_level: "low",
    permissions: ["Read calendar", "Send notifications"],
    preview_commands: [
      "prowlr remind 'Pick up kids' --smart",
      "prowlr reminders list",
    ],
  },
];

/* ── Personas ────────────────────────────────────────────────────────── */

const PERSONAS = [
  { id: "all", label: "All Agents", icon: Globe, color: "#00E5FF" },
  { id: "parent", label: "Parents", icon: Home, color: "#FF6B9D" },
  { id: "business", label: "Business", icon: Briefcase, color: "#F5A623" },
  { id: "student", label: "Students", icon: BookOpen, color: "#7C6CFF" },
  { id: "creator", label: "Creators", icon: Palette, color: "#4FC3F7" },
  { id: "freelancer", label: "Freelancers", icon: Laptop, color: "#00D4AA" },
  { id: "developer", label: "Developers", icon: Code, color: "#FF5252" },
] as const;

const DIFFICULTY_COLORS = {
  beginner: "#00E5FF",
  intermediate: "#F5A623",
  advanced: "#FF5252",
};

const SCAN_ICONS = [
  { key: "automation" as const, label: "Automation", icon: Zap },
  { key: "ease" as const, label: "Ease of Setup", icon: Target },
  { key: "privacy" as const, label: "Privacy", icon: Lock },
  { key: "reliability" as const, label: "Reliability", icon: RefreshCw },
  {
    key: "personalization" as const,
    label: "Personalization",
    icon: MessageSquare,
  },
];

/* ── Skill Scan Bar ──────────────────────────────────────────────────── */

function SkillScanBar({ scan }: { scan: SkillScan }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.375rem" }}>
      {SCAN_ICONS.map(({ key, label, icon: Icon }) => (
        <div
          key={key}
          style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}
        >
          <Icon
            size={12}
            style={{ color: "var(--text-muted)", flexShrink: 0 }}
          />
          <span
            style={{
              fontSize: "0.6875rem",
              color: "var(--text-muted)",
              width: 80,
              flexShrink: 0,
            }}
          >
            {label}
          </span>
          <div
            style={{
              flex: 1,
              height: 6,
              background: "var(--border)",
              borderRadius: 3,
              overflow: "hidden",
            }}
          >
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${scan[key] * 10}%` }}
              transition={{ duration: 0.8, delay: 0.1 }}
              style={{
                height: "100%",
                background: "var(--accent)",
                borderRadius: 3,
                boxShadow: "0 0 6px var(--accent-glow)",
              }}
            />
          </div>
          <span
            style={{
              fontSize: "0.625rem",
              color: "var(--text-muted)",
              width: 20,
              textAlign: "right",
            }}
          >
            {scan[key]}
          </span>
        </div>
      ))}
    </div>
  );
}

/* ── Listing Card ────────────────────────────────────────────────────── */

const RISK_CONFIG = {
  low: {
    color: "#00E676",
    label: "Low Risk",
    icon: CheckCircle,
    desc: "No sensitive data access",
  },
  medium: {
    color: "#F5A623",
    label: "Medium Risk",
    icon: AlertTriangle,
    desc: "Sends emails or accesses external APIs",
  },
  high: {
    color: "#FF5252",
    label: "High Risk",
    icon: Shield,
    desc: "Writes to external systems",
  },
};

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      onClick={(e) => {
        e.stopPropagation();
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      }}
      style={{
        background: "none",
        border: "none",
        cursor: "pointer",
        padding: "0.125rem",
        color: "var(--text-muted)",
        display: "inline-flex",
      }}
      title="Copy"
    >
      {copied ? <Check size={12} color="#00E676" /> : <Copy size={12} />}
    </button>
  );
}

function ListingCard({ listing, index }: { listing: Listing; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const diffColor = DIFFICULTY_COLORS[listing.difficulty];
  const risk = RISK_CONFIG[listing.risk_level];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.06 }}
      className="marketplace-card"
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: "0.75rem",
        padding: "var(--space-3)",
        cursor: "pointer",
        transition: "all 0.2s ease",
      }}
      onClick={() => setExpanded(!expanded)}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: "0.75rem",
        }}
      >
        <div>
          <h3
            style={{
              fontSize: "1.125rem",
              fontWeight: 700,
              color: "var(--text)",
              margin: 0,
            }}
          >
            {listing.title}
          </h3>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              marginTop: "0.375rem",
              flexWrap: "wrap",
            }}
          >
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.25rem",
                padding: "0.125rem 0.5rem",
                fontSize: "0.6875rem",
                fontWeight: 600,
                color: diffColor,
                background: `${diffColor}18`,
                borderRadius: "1rem",
                border: `1px solid ${diffColor}30`,
                textTransform: "capitalize",
              }}
            >
              {listing.difficulty}
            </span>
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.25rem",
                fontSize: "0.75rem",
                color: "var(--text-muted)",
              }}
            >
              <Clock size={12} /> {listing.setup_time_minutes} min
            </span>
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.25rem",
                fontSize: "0.75rem",
                color: "var(--text-muted)",
              }}
            >
              <Download size={12} /> {listing.downloads.toLocaleString()}
            </span>
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.25rem",
                fontSize: "0.75rem",
                color: "#F5A623",
              }}
            >
              <Star size={12} fill="#F5A623" /> {listing.rating}
            </span>
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.25rem",
                fontSize: "0.6875rem",
                color: risk.color,
              }}
            >
              <risk.icon size={11} /> {risk.label.split(" ")[0]}
            </span>
          </div>
        </div>
        <span
          style={{
            padding: "0.25rem 0.625rem",
            fontSize: "0.6875rem",
            fontWeight: 600,
            color: "var(--accent)",
            background: "var(--accent-dim)",
            borderRadius: "0.375rem",
            textTransform: "uppercase",
          }}
        >
          {listing.category}
        </span>
      </div>

      {/* Description */}
      <p
        style={{
          fontSize: "0.875rem",
          color: "var(--text-muted)",
          lineHeight: 1.6,
          margin: "0 0 0.75rem 0",
        }}
      >
        {listing.description}
      </p>

      {/* Skill Scan */}
      <SkillScanBar scan={listing.skill_scan} />

      {/* Expanded details */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            style={{ overflow: "hidden" }}
          >
            <div
              style={{
                paddingTop: "var(--space-3)",
                borderTop: "1px solid var(--border)",
                marginTop: "var(--space-3)",
              }}
            >
              {/* Before / After */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: "0.75rem",
                  marginBottom: "var(--space-2)",
                }}
              >
                <div
                  style={{
                    padding: "0.75rem",
                    background: "#ff525218",
                    borderRadius: "0.5rem",
                    border: "1px solid #ff525230",
                  }}
                >
                  <div
                    style={{
                      fontSize: "0.625rem",
                      fontWeight: 700,
                      color: "#FF5252",
                      textTransform: "uppercase",
                      marginBottom: "0.25rem",
                    }}
                  >
                    Before
                  </div>
                  <div
                    style={{
                      fontSize: "0.8125rem",
                      color: "var(--text-muted)",
                    }}
                  >
                    {listing.before_after.before}
                  </div>
                </div>
                <div
                  style={{
                    padding: "0.75rem",
                    background: "var(--accent-dim)",
                    borderRadius: "0.5rem",
                    border: "1px solid var(--accent)",
                  }}
                >
                  <div
                    style={{
                      fontSize: "0.625rem",
                      fontWeight: 700,
                      color: "var(--accent)",
                      textTransform: "uppercase",
                      marginBottom: "0.25rem",
                    }}
                  >
                    After
                  </div>
                  <div
                    style={{
                      fontSize: "0.8125rem",
                      color: "var(--text-muted)",
                    }}
                  >
                    {listing.before_after.after}
                  </div>
                </div>
              </div>
              <div
                style={{
                  fontSize: "0.75rem",
                  color: "var(--accent)",
                  fontWeight: 600,
                  marginBottom: "var(--space-2)",
                }}
              >
                Time saved: {listing.before_after.time_saved}
              </div>

              {/* User story */}
              {listing.user_stories[0] && (
                <blockquote
                  style={{
                    borderLeft: "3px solid var(--accent)",
                    paddingLeft: "0.75rem",
                    margin: "0 0 var(--space-2) 0",
                    fontStyle: "italic",
                  }}
                >
                  <p
                    style={{
                      fontSize: "0.8125rem",
                      color: "var(--text-muted)",
                      margin: 0,
                    }}
                  >
                    "{listing.user_stories[0].quote}"
                  </p>
                  <footer
                    style={{
                      fontSize: "0.6875rem",
                      color: "var(--text-muted)",
                      marginTop: "0.25rem",
                      opacity: 0.7,
                    }}
                  >
                    — {listing.user_stories[0].name},{" "}
                    {listing.user_stories[0].role}
                  </footer>
                </blockquote>
              )}

              {/* Works with */}
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "0.375rem",
                  marginBottom: "var(--space-2)",
                }}
              >
                {listing.works_with.map((w) => (
                  <span
                    key={w}
                    style={{
                      padding: "0.125rem 0.5rem",
                      fontSize: "0.6875rem",
                      color: "var(--text-muted)",
                      background: "var(--bg)",
                      borderRadius: "0.25rem",
                      border: "1px solid var(--border)",
                    }}
                  >
                    {w}
                  </span>
                ))}
              </div>

              {/* Risk & Permissions */}
              <div
                style={{
                  padding: "0.75rem",
                  background: `${risk.color}08`,
                  borderRadius: "0.5rem",
                  border: `1px solid ${risk.color}25`,
                  marginBottom: "var(--space-2)",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                    marginBottom: "0.5rem",
                  }}
                >
                  <risk.icon size={14} color={risk.color} />
                  <span
                    style={{
                      fontSize: "0.75rem",
                      fontWeight: 700,
                      color: risk.color,
                    }}
                  >
                    {risk.label}
                  </span>
                  <span
                    style={{
                      fontSize: "0.6875rem",
                      color: "var(--text-muted)",
                    }}
                  >
                    — {risk.desc}
                  </span>
                </div>
                <div
                  style={{ display: "flex", flexWrap: "wrap", gap: "0.375rem" }}
                >
                  {listing.permissions.map((p) => (
                    <span
                      key={p}
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "0.25rem",
                        padding: "0.125rem 0.5rem",
                        fontSize: "0.6875rem",
                        color: "var(--text-muted)",
                        background: "var(--bg)",
                        borderRadius: "0.25rem",
                        border: "1px solid var(--border)",
                      }}
                    >
                      <Eye size={10} /> {p}
                    </span>
                  ))}
                </div>
              </div>

              {/* Install Command */}
              <div
                style={{
                  padding: "0.625rem 0.75rem",
                  background: "#0d0d14",
                  borderRadius: "0.5rem",
                  border: "1px solid var(--border)",
                  marginBottom: "var(--space-2)",
                  fontFamily: "ui-monospace, 'SF Mono', Menlo, monospace",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                  }}
                >
                  <Terminal size={14} color="var(--accent)" />
                  <code style={{ fontSize: "0.75rem", color: "var(--accent)" }}>
                    {listing.install_cmd}
                  </code>
                </div>
                <CopyButton text={listing.install_cmd} />
              </div>

              {/* Preview Commands */}
              <div style={{ marginBottom: "var(--space-2)" }}>
                <div
                  style={{
                    fontSize: "0.6875rem",
                    fontWeight: 600,
                    color: "var(--text-muted)",
                    textTransform: "uppercase",
                    marginBottom: "0.375rem",
                  }}
                >
                  Commands you'll get
                </div>
                {listing.preview_commands.map((cmd) => (
                  <div
                    key={cmd}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "0.375rem 0.625rem",
                      marginBottom: "0.25rem",
                      background: "#0d0d14",
                      borderRadius: "0.25rem",
                      border: "1px solid var(--border)",
                      fontFamily: "ui-monospace, 'SF Mono', Menlo, monospace",
                    }}
                  >
                    <code style={{ fontSize: "0.6875rem", color: "#888899" }}>
                      $ {cmd}
                    </code>
                    <CopyButton text={cmd} />
                  </div>
                ))}
              </div>

              {/* CTA */}
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    navigator.clipboard.writeText(listing.install_cmd);
                  }}
                  style={{
                    flex: 1,
                    padding: "0.625rem",
                    fontSize: "0.8125rem",
                    fontWeight: 700,
                    color: "var(--bg)",
                    background: "var(--accent)",
                    border: "none",
                    borderRadius: "0.375rem",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "0.375rem",
                  }}
                >
                  <Terminal size={14} /> Copy Install Command
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {!expanded && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "flex-end",
            marginTop: "0.5rem",
          }}
        >
          <span
            style={{
              fontSize: "0.75rem",
              color: "var(--accent)",
              display: "flex",
              alignItems: "center",
              gap: "0.25rem",
            }}
          >
            Details <ChevronRight size={14} />
          </span>
        </div>
      )}
    </motion.div>
  );
}

/* ── Main Page ───────────────────────────────────────────────────────── */

interface MarketplaceProps {
  config: SiteConfig;
  lang: Lang;
  theme: "dark" | "light";
  onThemeToggle: () => void;
}

export function Marketplace({
  config,
  lang,
  theme,
  onThemeToggle,
}: MarketplaceProps) {
  const [searchParams] = useSearchParams();
  const [activePersona, setActivePersona] = useState(
    () => searchParams.get("persona") || "all",
  );
  const [searchQuery, setSearchQuery] = useState("");
  const [activeDifficulty, setActiveDifficulty] = useState<string | null>(null);

  // Sync persona from URL query param (e.g. redirected from greeting quiz)
  useEffect(() => {
    const p = searchParams.get("persona");
    if (p && PERSONAS.some((t: { id: string }) => t.id === p)) {
      setActivePersona(p);
    }
  }, [searchParams]);

  const filtered = useMemo(() => {
    let results = LISTINGS;
    if (activePersona !== "all") {
      results = results.filter((l) => l.persona_tags.includes(activePersona));
    }
    if (activeDifficulty) {
      results = results.filter((l) => l.difficulty === activeDifficulty);
    }
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      results = results.filter(
        (l) =>
          l.title.toLowerCase().includes(q) ||
          l.description.toLowerCase().includes(q) ||
          l.tags.some((t) => t.includes(q)),
      );
    }
    return results;
  }, [activePersona, activeDifficulty, searchQuery]);

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
        consoleUrl={config.consoleUrl}
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
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          style={{ textAlign: "center", marginBottom: "var(--space-5)" }}
        >
          <h1
            style={{
              fontSize: "2.5rem",
              fontWeight: 800,
              color: "var(--text)",
              marginBottom: "var(--space-2)",
            }}
          >
            Pick Your Life. We Handle the Rest.
          </h1>
          <p
            style={{
              fontSize: "1.0625rem",
              color: "var(--text-muted)",
              maxWidth: 560,
              margin: "0 auto var(--space-3)",
              lineHeight: 1.6,
            }}
          >
            Real AI agents that automate the things you don't want to do. Not
            chatbots — autonomous crews that work on autopilot.
          </p>

          {/* Search */}
          <div
            style={{ position: "relative", maxWidth: 480, margin: "0 auto" }}
          >
            <Search
              size={18}
              style={{
                position: "absolute",
                left: 12,
                top: "50%",
                transform: "translateY(-50%)",
                color: "var(--text-muted)",
              }}
            />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search agents, skills, workflows..."
              style={{
                width: "100%",
                padding: "0.75rem 0.75rem 0.75rem 2.5rem",
                fontSize: "0.875rem",
                background: "var(--surface)",
                border: "1px solid var(--border)",
                borderRadius: "0.5rem",
                color: "var(--text)",
                outline: "none",
              }}
            />
          </div>
        </motion.div>

        {/* Persona tabs */}
        <div
          style={{
            display: "flex",
            gap: "0.5rem",
            marginBottom: "var(--space-3)",
            overflowX: "auto",
            paddingBottom: "0.5rem",
          }}
        >
          {PERSONAS.map(({ id, label, icon: Icon, color }) => (
            <button
              key={id}
              type="button"
              onClick={() => setActivePersona(id)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.375rem",
                padding: "0.5rem 1rem",
                fontSize: "0.8125rem",
                fontWeight: 600,
                color: activePersona === id ? "var(--bg)" : "var(--text-muted)",
                background: activePersona === id ? color : "var(--surface)",
                border: `1px solid ${
                  activePersona === id ? color : "var(--border)"
                }`,
                borderRadius: "2rem",
                cursor: "pointer",
                whiteSpace: "nowrap",
                transition: "all 0.2s ease",
              }}
            >
              <Icon size={16} />
              {label}
            </button>
          ))}
        </div>

        {/* Difficulty filter */}
        <div
          style={{
            display: "flex",
            gap: "0.375rem",
            marginBottom: "var(--space-4)",
          }}
        >
          {(["beginner", "intermediate", "advanced"] as const).map((d) => (
            <button
              key={d}
              type="button"
              onClick={() =>
                setActiveDifficulty(activeDifficulty === d ? null : d)
              }
              style={{
                padding: "0.25rem 0.75rem",
                fontSize: "0.75rem",
                fontWeight: 600,
                color:
                  activeDifficulty === d ? "var(--bg)" : DIFFICULTY_COLORS[d],
                background:
                  activeDifficulty === d
                    ? DIFFICULTY_COLORS[d]
                    : `${DIFFICULTY_COLORS[d]}18`,
                border: `1px solid ${DIFFICULTY_COLORS[d]}30`,
                borderRadius: "1rem",
                cursor: "pointer",
                textTransform: "capitalize",
                transition: "all 0.2s ease",
              }}
            >
              {d}
            </button>
          ))}
          <span
            style={{
              fontSize: "0.75rem",
              color: "var(--text-muted)",
              display: "flex",
              alignItems: "center",
              marginLeft: "0.5rem",
            }}
          >
            <Shield size={14} style={{ marginRight: "0.25rem" }} />
            {filtered.length} agent{filtered.length !== 1 ? "s" : ""} found
          </span>
        </div>

        {/* Listings grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))",
            gap: "var(--space-3)",
          }}
        >
          {filtered.map((listing, i) => (
            <ListingCard key={listing.id} listing={listing} index={i} />
          ))}
        </div>

        {filtered.length === 0 && (
          <div
            style={{
              textAlign: "center",
              padding: "var(--space-5)",
              color: "var(--text-muted)",
            }}
          >
            <p style={{ fontSize: "1.125rem" }}>
              No agents match your filters.
            </p>
            <button
              type="button"
              onClick={() => {
                setActivePersona("all");
                setActiveDifficulty(null);
                setSearchQuery("");
              }}
              style={{
                color: "var(--accent)",
                background: "none",
                border: "none",
                cursor: "pointer",
                fontSize: "0.875rem",
              }}
            >
              Clear all filters
            </button>
          </div>
        )}

        {/* Coming soon */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          style={{
            textAlign: "center",
            marginTop: "var(--space-5)",
            padding: "var(--space-4)",
            background: "var(--surface)",
            borderRadius: "0.75rem",
            border: "1px solid var(--border)",
          }}
        >
          <h2
            style={{
              fontSize: "1.25rem",
              fontWeight: 700,
              color: "var(--text)",
              marginBottom: "var(--space-1)",
            }}
          >
            38 more agents coming soon
          </h2>
          <p
            style={{
              fontSize: "0.875rem",
              color: "var(--text-muted)",
              margin: 0,
            }}
          >
            Content creators, entrepreneurs, developers, and more. Join early
            access to get them first.
          </p>
          <Link
            to="/"
            style={{
              display: "inline-block",
              marginTop: "var(--space-2)",
              padding: "0.5rem 1.25rem",
              fontSize: "0.8125rem",
              fontWeight: 700,
              color: "var(--bg)",
              background: "var(--accent)",
              borderRadius: "0.375rem",
              textDecoration: "none",
            }}
          >
            Get Early Access
          </Link>
        </motion.div>
      </main>

      <Footer lang={lang} />

      <style>{`
        .marketplace-card:hover {
          border-color: var(--accent) !important;
          transform: translateY(-2px);
          box-shadow: 0 4px 20px rgba(0, 229, 255, 0.1);
        }
        @media (max-width: 640px) {
          .marketplace-card {
            min-width: 0 !important;
          }
        }
      `}</style>
    </div>
  );
}
