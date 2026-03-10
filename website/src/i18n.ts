export type Lang = "zh" | "en";

export const i18n: Record<Lang, Record<string, string>> = {
  zh: {
    "nav.docs": "Docs",
    "nav.github": "GitHub",
    "nav.lang": "EN",
    "hero.slogan": "Always watching. Always ready.",
    "hero.sub":
      "Autonomous AI agent platform for monitoring, automation, and multi-channel communication. Deploy intelligent agents that watch your systems and respond across every channel.",
    "hero.cta": "Get Started",
    "brandstory.title": "Why we built ProwlrBot",
    "brandstory.para1":
      "We were tired of paying $200/month for AI agent platforms that lock your data in someone else's cloud. Your conversations, your documents, your automations — they should live on YOUR machine, under YOUR control.",
    "brandstory.para2":
      "We wanted one platform that works everywhere — not a Discord bot AND a Telegram bot AND a Slack bot. One agent, eight channels, zero vendor lock-in.",
    "brandstory.para3":
      "Most agent platforms are all-or-nothing. We believe autonomy should be gradual. Start by watching. Then guiding. Then delegating. Then full autopilot — only when you're ready.",
    "brandstory.para4":
      "ProwlrBot is open source, built on open protocols, and will never charge you a subscription to run your own agents.",
    "brandstory.cta": "Star us on GitHub",
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
  },
  en: {
    "nav.docs": "Docs",
    "nav.github": "GitHub",
    "nav.lang": "中文",
    "hero.slogan": "Always watching. Always ready.",
    "hero.sub":
      "Autonomous AI agent platform for monitoring, automation, and multi-channel communication. Deploy intelligent agents that watch your systems and respond across every channel.",
    "hero.cta": "Get Started",
    "brandstory.title": "Why we built ProwlrBot",
    "brandstory.para1":
      "We were tired of paying $200/month for AI agent platforms that lock your data in someone else's cloud. Your conversations, your documents, your automations — they should live on YOUR machine, under YOUR control.",
    "brandstory.para2":
      "We wanted one platform that works everywhere — not a Discord bot AND a Telegram bot AND a Slack bot. One agent, eight channels, zero vendor lock-in. And when you connect a new AI provider, it should just work.",
    "brandstory.para3":
      "Most agent platforms are all-or-nothing: either the AI does everything or nothing. We believe autonomy should be gradual. Start by watching. Then guiding. Then delegating. Then full autopilot — only when you're ready.",
    "brandstory.para4":
      "ProwlrBot is open source, built on open protocols (MCP, ACP, A2A), and will never charge you a subscription to run your own agents. This is the agent platform we wished existed.",
    "brandstory.cta": "Star us on GitHub",
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
  },
};

export function t(lang: Lang, key: string): string {
  return i18n[lang][key] ?? key;
}
