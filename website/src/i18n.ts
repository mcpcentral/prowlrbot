export type Lang = "zh" | "en";

export const i18n: Record<Lang, Record<string, string>> = {
  zh: {
    "nav.docs": "文档",
    "nav.github": "GitHub",
    "nav.githubComingSoon": "Coming Soon",
    "nav.lang": "EN",
    "nav.agentscopeTeam": "AgentScope",
    "hero.slogan": "懂你所需，伴你左右",
    "hero.sub":
      "你的AI个人助理；安装极简、本地与云上均可部署；支持多端接入、能力轻松扩展。",
    "hero.cta": "查看文档",
    "brandstory.title": "Why ProwlrBot?",
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
    "features.skills.desc": "Extensible skill packs for PDF, Office, email, browser. Full MCP client with hot-reload.",
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
    "testimonials.title": "社区怎么说",
    "testimonials.viewAll": "查看全部",
    "testimonials.1": "ProwlrBot 就该这样：多频道一个入口，Python 好改好部署。",
    "testimonials.2": "定时和心跳很实用，Skills 自己加，数据都在本地。",
    "testimonials.3": "想完全掌控的团队用着很顺手。",
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
    "stats.features.value": "60+",
    "stats.features.label": "Features",
    "stats.channels.value": "8",
    "stats.channels.label": "Channels",
    "stats.skills.value": "20+",
    "stats.skills.label": "Skills",
    "stats.protocols.value": "3",
    "stats.protocols.label": "Protocols",
    "stats.autonomy.value": "4",
    "stats.autonomy.label": "Autonomy Levels",
    "quickstart.title": "快速开始",
    "quickstart.hintBefore": "安装 → 初始化 → 启动；频道配置见 ",
    "quickstart.hintLink": "文档",
    "quickstart.hintAfter": "，即可通过钉钉、飞书、QQ 等频道使用 ProwlrBot。",
    "quickstart.optionLocal": "一键安装（uv 建虚拟环境并安装，无需 Python）",
    "quickstart.badgeRecommended": "推荐",
    "quickstart.badgeBeta": "Beta",
    "quickstart.optionPip": "pip 安装",
    "quickstart.tabPip": "pip 安装 (推荐)",
    "quickstart.tabPipMain": "pip 安装",
    "quickstart.tabPipSub": "(推荐)",
    "quickstart.tabUnix": "macOS / Linux (Beta)",
    "quickstart.tabUnixMain": "macOS / Linux",
    "quickstart.tabUnixSub": "(Beta)",
    "quickstart.tabWindows": "Windows (Beta)",
    "quickstart.tabWindowsMain": "Windows",
    "quickstart.tabWindowsSub": "(Beta)",
    "quickstart.tabDocker": "Docker",
    "quickstart.tabDockerShort": "Docker",
    "quickstart.optionDocker": "Docker 镜像（Docker Hub，国内可选 ACR）",
    "quickstart.tabAliyun": "阿里云 ECS",
    "quickstart.tabAliyunMain": "阿里云 ECS",
    "quickstart.tabAliyunSub": "",
    "quickstart.tabPipShort": "pip",
    "quickstart.tabUnixShort": "Mac/Linux",
    "quickstart.tabWindowsShort": "Windows",
    "quickstart.tabAliyunShort": "阿里云",
    "quickstart.optionAliyun": "阿里云 ECS 一键部署",
    "quickstart.aliyunDeployLink": "部署链接",
    "quickstart.aliyunDocLink": "说明文档",
    footer: "ProwlrBot — 懂你所需，伴你左右",
    "footer.poweredBy.p1": "由 ",
    "footer.poweredBy.p2": " 基于 ",
    "footer.poweredBy.p3": "、",
    "footer.poweredBy.p3b": " 与 ",
    "footer.poweredBy.p4": " 打造。",
    "footer.poweredBy.team": "AgentScope 团队",
    "footer.poweredBy.agentscope": "AgentScope",
    "footer.poweredBy.runtime": "AgentScope Runtime",
    "footer.poweredBy.reme": "ReMe",
    "footer.inspiredBy": "部分灵感来源于 ",
    "footer.inspiredBy.name": "OpenClaw",
    "footer.thanksSkills": "感谢 ",
    "footer.thanksSkills.name": "anthropics/skills",
    "footer.thanksSkills.suffix": " 提供 Agent Skills 规范与示例。",
    "docs.backToTop": "返回顶部",
    "docs.copy": "复制",
    "docs.copied": "已复制",
    "docs.searchPlaceholder": "搜索文档",
    "docs.searchLoading": "加载中…",
    "docs.searchNoResults": "无结果",
    "docs.searchResultsTitle": "搜索结果",
    "docs.searchResultsTitleEmpty": "搜索文档",
    "docs.searchHint": "在左侧输入关键词后按回车搜索。",
  },
  en: {
    "nav.docs": "Docs",
    "nav.github": "GitHub",
    "nav.githubComingSoon": "Coming Soon",
    "nav.lang": "中文",
    "nav.agentscopeTeam": "AgentScope",
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
    "testimonials.title": "What people say",
    "testimonials.viewAll": "View all",
    "testimonials.1":
      "This is what a personal assistant should be: one entry, every channel.",
    "testimonials.2":
      "Cron and heartbeat are super practical. Add your own skills; data stays local.",
    "testimonials.3": "Teams who want full control love it.",
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
    "stats.features.value": "60+",
    "stats.features.label": "Features",
    "stats.channels.value": "8",
    "stats.channels.label": "Channels",
    "stats.skills.value": "20+",
    "stats.skills.label": "Skills",
    "stats.protocols.value": "3",
    "stats.protocols.label": "Protocols",
    "stats.autonomy.value": "4",
    "stats.autonomy.label": "Autonomy Levels",
    "quickstart.title": "Quick start",
    "quickstart.hintBefore":
      "Install → init → start. Configure channels to use ProwlrBot on Discord, Telegram, etc. See ",
    "quickstart.hintLink": "docs",
    "quickstart.hintAfter": ".",
    "quickstart.optionLocal":
      "One-click: uv creates venv & installs, no Python needed",
    "quickstart.badgeRecommended": "Recommended",
    "quickstart.badgeBeta": "Beta",
    "quickstart.optionPip": "pip install",
    "quickstart.tabPip": "pip install (recommended)",
    "quickstart.tabPipMain": "pip install",
    "quickstart.tabPipSub": "(recommended)",
    "quickstart.tabUnix": "macOS / Linux (Beta)",
    "quickstart.tabUnixMain": "macOS / Linux",
    "quickstart.tabUnixSub": "(Beta)",
    "quickstart.tabWindows": "Windows (Beta)",
    "quickstart.tabWindowsMain": "Windows",
    "quickstart.tabWindowsSub": "(Beta)",
    "quickstart.tabDocker": "Docker",
    "quickstart.tabDockerShort": "Docker",
    "quickstart.optionDocker":
      "Docker image (Docker Hub; ACR optional in China)",
    "quickstart.tabAliyun": "Alibaba Cloud ECS",
    "quickstart.tabAliyunMain": "Alibaba Cloud ECS",
    "quickstart.tabAliyunSub": "",
    "quickstart.tabPipShort": "pip",
    "quickstart.tabUnixShort": "Mac/Linux",
    "quickstart.tabWindowsShort": "Windows",
    "quickstart.tabAliyunShort": "Alibaba Cloud",
    "quickstart.optionAliyun": "Deploy on Alibaba Cloud ECS",
    "quickstart.aliyunDeployLink": "Deployment link",
    "quickstart.aliyunDocLink": "Guide",
    footer: "ProwlrBot — Always watching. Always ready.",
    "footer.poweredBy.p1": "Built by ",
    "footer.poweredBy.p2": " with ",
    "footer.poweredBy.p3": ", ",
    "footer.poweredBy.p3b": ", and ",
    "footer.poweredBy.p4": ".",
    "footer.poweredBy.team": "AgentScope team",
    "footer.poweredBy.agentscope": "AgentScope",
    "footer.poweredBy.runtime": "AgentScope Runtime",
    "footer.poweredBy.reme": "ReMe",
    "footer.inspiredBy": "Partly inspired by ",
    "footer.inspiredBy.name": "OpenClaw",
    "footer.thanksSkills": "Thanks to ",
    "footer.thanksSkills.name": "anthropics/skills",
    "footer.thanksSkills.suffix": " for the Agent Skills spec and examples.",
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
