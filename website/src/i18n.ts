export type Lang = "zh" | "en";

export const i18n: Record<Lang, Record<string, string>> = {
  zh: {
    "nav.docs": "Docs",
    "nav.github": "GitHub",
    "nav.lang": "EN",
    "hero.slogan": "Your AI agents never sleep.",
    "hero.sub":
      "Deploy autonomous agents that monitor competitors, automate workflows, and respond across 8 channels — while you focus on what matters. Used by developers who refuse to do repetitive work.",
    "hero.cta": "Get Early Access",
    "hero.badge": "Early Access — Limited Beta",
    "brandstory.title": "Why developers are switching",
    "brandstory.para1":
      "Manus costs $200/month and was just acquired. Devin has a 15% success rate at $500/month. AutoGPT can't talk to your team. We built ProwlrBot because every existing option is either overpriced, unreliable, or locked in a silo.",
    "brandstory.para2":
      "One agent. Eight channels. Seven AI providers. Your infrastructure. No vendor lock-in, no per-seat pricing, no data leaving your servers unless you want it to.",
    "brandstory.para3":
      "Most agent platforms are all-or-nothing. ProwlrBot has four autonomy levels — Watch, Guide, Delegate, Autonomous. Start cautious. Scale up when you trust it. Your agents earn their freedom.",
    "brandstory.para4":
      "We're the only platform supporting all three agent protocols (MCP, ACP, A2A). That means your agents can talk to any other agent ecosystem, not just ours.",
    "brandstory.cta": "Join the Beta",
    "features.title": "Core capabilities",
    "features.warroom.title": "War Room",
    "features.warroom.desc":
      "Multi-agent coordination with mission board, file locks, shared context, and real-time broadcasts. Zero merge conflicts.",
    "features.channels.title": "Every channel",
    "features.channels.desc":
      "Discord, Telegram, DingTalk, Feishu, QQ, iMessage, and a built-in web console. One agent, every platform.",
    "features.private.title": "Security first",
    "features.private.desc":
      "API auth, rate limiting, path sandboxing, shell blocklist, prompt injection detection, and secret redaction. Your data stays yours.",
    "features.skills.title": "Skills & MCP",
    "features.skills.desc":
      "Extensible skill packs for PDF, Office, email, browser. Full MCP client with hot-reload.",
    "features.monitoring.title": "Web Monitoring",
    "features.monitoring.desc":
      "Watch websites and APIs for changes. Content diffing, price tracking, competitor monitoring with instant alerts.",
    "features.providers.title": "7 AI Providers",
    "features.providers.desc":
      "OpenAI, Anthropic, Groq, Z.ai, Ollama, llama.cpp, MLX. Smart routing picks the best model automatically.",
    "features.agentverse.title": "AgentVerse",
    "features.agentverse.desc":
      "A virtual world where your agents live, form guilds, trade, and battle. Club Penguin meets AI.",
    "features.autonomy.title": "Graduated Autonomy",
    "features.autonomy.desc":
      "Four levels: Watch, Guide, Delegate, Autonomous. You choose how much freedom your agent gets.",
    "features.roar.title": "ROAR Protocol",
    "features.roar.desc":
      "The first 5-layer agent communication protocol. Built-in MCP + ACP + A2A backward compatibility.",
    "usecases.title": "What you can build with ProwlrBot",
    "usecases.sub": "These are real workflows people run today — not demos.",
    "usecases.category.social": "Monitoring & alerts",
    "usecases.category.creative": "Creative & building",
    "usecases.category.productivity": "Productivity",
    "usecases.category.research": "Research & intelligence",
    "usecases.category.assistant": "Desktop & files",
    "usecases.category.explore": "Explore more",
    "usecases.social.1":
      "Monitor competitor pricing across 50+ sites and get instant Telegram alerts when prices drop below your threshold.",
    "usecases.social.2":
      "Track Reddit, Hacker News, and Twitter for brand mentions — auto-summarize sentiment and flag urgent issues in Discord.",
    "usecases.social.3":
      "Watch GitHub repos, npm packages, or API changelogs for breaking changes and notify your team before deployments break.",
    "usecases.creative.1":
      "Describe a side project at midnight, set ProwlrBot to autonomous mode, and wake up to a working prototype with tests.",
    "usecases.creative.2":
      "Generate blog posts, social media copy, and video scripts from a single brief — then schedule publishing across channels.",
    "usecases.productivity.1":
      "Auto-respond to Discord and Telegram support tickets using your docs, escalating edge cases to humans.",
    "usecases.productivity.2":
      "Summarize 200+ daily emails into a 5-minute brief delivered to your preferred channel every morning at 8am.",
    "usecases.productivity.3":
      "Auto-file expense receipts, extract amounts with OCR, and push weekly spending reports to your team chat.",
    "usecases.research.1":
      "Track 30+ AI company earnings, patent filings, and funding rounds — get a weekly intelligence digest with trend analysis.",
    "usecases.research.2":
      "Build a personal knowledge base from papers, articles, and bookmarks — then query it in natural language from any channel.",
    "usecases.assistant.1":
      "Search, organize, and summarize local documents. Ask for a file in Telegram and receive it instantly — no cloud upload needed.",
    "usecases.explore.1":
      "Chain skills, cron jobs, and MCP tools into custom agentic workflows — the only limit is your imagination.",
    "quickstart.title": "Quick start",
    "quickstart.hintBefore":
      "Install → init → start. Configure channels to use ProwlrBot on Discord, Telegram, etc. See ",
    "quickstart.hintLink": "docs",
    "quickstart.hintAfter": ".",
    "docs.backToTop": "Back to top",
    "docs.copy": "Copy",
    "docs.copied": "Copied",
    "docs.searchPlaceholder": "Search docs",
    "docs.searchLoading": "Loading…",
    "docs.searchNoResults": "No results",
    "docs.searchResultsTitle": "Search results",
    "docs.searchResultsTitleEmpty": "Search docs",
    "docs.searchHint": "Enter a keyword and press Enter to search.",
    "comparison.label": "Why ProwlrBot?",
    "comparison.title": "How we compare",
    "comparison.description": "8 channels, 7 providers, multi-agent coordination, and graduated autonomy. The most capable agent platform, period.",
    "community.label": "Community",
    "community.title": "Join the pack",
    "community.description": "Shape the platform with us. Beta members get direct access to the team, priority feature requests, and early access to Pro features.",
    "community.path.bugs.title": "Report bugs",
    "community.path.bugs.desc": "Found something broken? Open an issue with reproduction steps and we will fix it fast.",
    "community.path.prs.title": "Submit PRs",
    "community.path.prs.desc": "Pick up an issue, fork the repo, and submit a pull request. We review within 48 hours.",
    "community.path.skills.title": "Build skills",
    "community.path.skills.desc": "Create skill packs that extend ProwlrBot with new capabilities. Share them in the marketplace.",
    "community.discussions": "GitHub Discussions",
    "community.discord": "Join Discord",
    "community.contributing": "Contributing Guide",
    "roadmap.label": "Roadmap",
    "roadmap.title": "Where we are headed",
    "roadmap.description": "A three-phase plan to build the most capable agent platform.",
    "roadmap.phase1.title": "Core Platform",
    "roadmap.phase1.subtitle": "Foundation complete",
    "roadmap.phase1.items": "8 channels integrated|7 AI providers with smart routing|Multi-agent war room|Web and API monitoring|Security hardening",
    "roadmap.phase2.title": "Marketplace & Cloud",
    "roadmap.phase2.subtitle": "Building now",
    "roadmap.phase2.items": "Skill marketplace with revenue sharing|Hosted agent deployment|Team workspaces|Advanced analytics dashboard",
    "roadmap.phase3.title": "AgentVerse",
    "roadmap.phase3.subtitle": "On the horizon",
    "roadmap.phase3.items": "Virtual world for agents|Guilds, trading, and battles|Cross-platform agent federation|Community-driven governance",
  },
  en: {
    "nav.docs": "Docs",
    "nav.github": "GitHub",
    "nav.lang": "中文",
    "hero.slogan": "Your AI agents never sleep.",
    "hero.sub":
      "Deploy autonomous agents that monitor competitors, automate workflows, and respond across 8 channels — while you focus on what matters. Used by developers who refuse to do repetitive work.",
    "hero.cta": "Get Early Access",
    "hero.badge": "Early Access — Limited Beta",
    "brandstory.title": "Why we built ProwlrBot",
    "brandstory.para1":
      "We built ProwlrBot because existing AI agent platforms are either locked behind expensive subscriptions or too complex to self-host. There had to be a better way.",
    "brandstory.para2":
      "We wanted one platform that works everywhere — not a Discord bot AND a Telegram bot AND a Slack bot. One agent, eight channels. And when you connect a new AI provider, it should just work.",
    "brandstory.para3":
      "Most agent platforms are all-or-nothing: either the AI does everything or nothing. We believe autonomy should be gradual. Start by watching. Then guiding. Then delegating. Then full autopilot — only when you're ready.",
    "brandstory.para4":
      "ProwlrBot is built on open protocols (MCP, ACP, A2A) with a generous free tier and powerful Pro features for teams that need more.",
    "brandstory.cta": "Get Started Free",
    "features.title": "Core capabilities",
    "features.warroom.title": "War Room",
    "features.warroom.desc":
      "Multi-agent coordination with mission board, file locks, shared context, and real-time broadcasts. Zero merge conflicts.",
    "features.channels.title": "Every channel",
    "features.channels.desc":
      "Discord, Telegram, DingTalk, Feishu, QQ, iMessage, and a built-in web console. One agent, every platform.",
    "features.private.title": "Security first",
    "features.private.desc":
      "API auth, rate limiting, path sandboxing, shell blocklist, prompt injection detection, and secret redaction. Your data stays yours.",
    "features.skills.title": "Skills & MCP",
    "features.skills.desc":
      "Extensible skill packs for PDF, Office docs, email, browser automation. Full MCP client with hot-reload.",
    "features.monitoring.title": "Web Monitoring",
    "features.monitoring.desc":
      "Watch websites and APIs for changes. Content diffing, price tracking, competitor monitoring with instant alerts.",
    "features.providers.title": "7 AI Providers",
    "features.providers.desc":
      "OpenAI, Anthropic, Groq, Z.ai, Ollama, llama.cpp, MLX. Smart routing picks the cheapest, fastest, most available model.",
    "features.agentverse.title": "AgentVerse",
    "features.agentverse.desc":
      "A virtual world where your agents live, form guilds, trade, and battle. Club Penguin meets AI.",
    "features.autonomy.title": "Graduated Autonomy",
    "features.autonomy.desc":
      "Four levels: Watch, Guide, Delegate, Autonomous. You choose how much freedom your agent gets.",
    "features.roar.title": "ROAR Protocol",
    "features.roar.desc":
      "The first 5-layer agent communication protocol. Built-in MCP + ACP + A2A backward compatibility.",
    "usecases.title": "What you can build with ProwlrBot",
    "usecases.sub": "These are real workflows people run today — not demos.",
    "usecases.category.social": "Monitoring & alerts",
    "usecases.category.creative": "Creative & building",
    "usecases.category.productivity": "Productivity",
    "usecases.category.research": "Research & intelligence",
    "usecases.category.assistant": "Desktop & files",
    "usecases.category.explore": "Explore more",
    "usecases.social.1":
      "Monitor competitor pricing across 50+ sites and get instant Telegram alerts when prices drop below your threshold.",
    "usecases.social.2":
      "Track Reddit, Hacker News, and Twitter for brand mentions — auto-summarize sentiment and flag urgent issues in Discord.",
    "usecases.social.3":
      "Watch GitHub repos, npm packages, or API changelogs for breaking changes and notify your team before deployments break.",
    "usecases.creative.1":
      "Describe a side project at midnight, set ProwlrBot to autonomous mode, and wake up to a working prototype with tests.",
    "usecases.creative.2":
      "Generate blog posts, social media copy, and video scripts from a single brief — then schedule publishing across channels.",
    "usecases.productivity.1":
      "Auto-respond to Discord and Telegram support tickets using your docs, escalating edge cases to humans.",
    "usecases.productivity.2":
      "Summarize 200+ daily emails into a 5-minute brief delivered to your preferred channel every morning at 8am.",
    "usecases.productivity.3":
      "Auto-file expense receipts, extract amounts with OCR, and push weekly spending reports to your team chat.",
    "usecases.research.1":
      "Track 30+ AI company earnings, patent filings, and funding rounds — get a weekly intelligence digest with trend analysis.",
    "usecases.research.2":
      "Build a personal knowledge base from papers, articles, and bookmarks — then query it in natural language from any channel.",
    "usecases.assistant.1":
      "Search, organize, and summarize local documents. Ask for a file in Telegram and receive it instantly — no cloud upload needed.",
    "usecases.explore.1":
      "Chain skills, cron jobs, and MCP tools into custom agentic workflows — the only limit is your imagination.",
    "quickstart.title": "Quick start",
    "quickstart.hintBefore":
      "Install → init → start. Configure channels to use ProwlrBot on Discord, Telegram, etc. See ",
    "quickstart.hintLink": "docs",
    "quickstart.hintAfter": ".",
    "docs.backToTop": "Back to top",
    "docs.copy": "Copy",
    "docs.copied": "Copied",
    "docs.searchPlaceholder": "Search docs",
    "docs.searchLoading": "Loading…",
    "docs.searchNoResults": "No results",
    "docs.searchResultsTitle": "Search results",
    "docs.searchResultsTitleEmpty": "Search docs",
    "docs.searchHint": "Enter a keyword and press Enter to search.",
    "comparison.label": "Why ProwlrBot?",
    "comparison.title": "How we compare",
    "comparison.description": "8 channels, 7 providers, multi-agent coordination, and graduated autonomy. The most capable agent platform, period.",
    "community.label": "Community",
    "community.title": "Join the pack",
    "community.description": "Shape the platform with us. Beta members get direct access to the team, priority feature requests, and early access to Pro features.",
    "community.path.bugs.title": "Report bugs",
    "community.path.bugs.desc": "Found something broken? Open an issue with reproduction steps and we will fix it fast.",
    "community.path.prs.title": "Submit PRs",
    "community.path.prs.desc": "Pick up an issue, fork the repo, and submit a pull request. We review within 48 hours.",
    "community.path.skills.title": "Build skills",
    "community.path.skills.desc": "Create skill packs that extend ProwlrBot with new capabilities. Share them in the marketplace.",
    "community.discussions": "GitHub Discussions",
    "community.discord": "Join Discord",
    "community.contributing": "Contributing Guide",
    "roadmap.label": "Roadmap",
    "roadmap.title": "Where we are headed",
    "roadmap.description": "A three-phase plan to build the most capable agent platform.",
    "roadmap.phase1.title": "Core Platform",
    "roadmap.phase1.subtitle": "Foundation complete",
    "roadmap.phase1.items": "8 channels integrated|7 AI providers with smart routing|Multi-agent war room|Web and API monitoring|Security hardening",
    "roadmap.phase2.title": "Marketplace & Cloud",
    "roadmap.phase2.subtitle": "Building now",
    "roadmap.phase2.items": "Skill marketplace with revenue sharing|Hosted agent deployment|Team workspaces|Advanced analytics dashboard",
    "roadmap.phase3.title": "AgentVerse",
    "roadmap.phase3.subtitle": "On the horizon",
    "roadmap.phase3.items": "Virtual world for agents|Guilds, trading, and battles|Cross-platform agent federation|Community-driven governance",
  },
};

export function t(lang: Lang, key: string): string {
  return i18n[lang][key] ?? key;
}
