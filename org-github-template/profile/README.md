<p align="center">
  <img src="https://img.shields.io/badge/ProwlrBot-Always%20Watching-00E5FF?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJDNi40OCAyIDIgNi40OCAyIDEyczQuNDggMTAgMTAgMTAgMTAtNC40OCAxMC0xMFMxNy41MiAyIDEyIDJ6bTAgMThjLTQuNDIgMC04LTMuNTgtOC04czMuNTgtOCA4LTggOCAzLjU4IDggOC0zLjU4IDgtOCA4eiIgZmlsbD0iIzAwRTVGRiIvPjwvc3ZnPg==&logoColor=white" alt="ProwlrBot" />
</p>

<h1 align="center">ProwlrBot</h1>

<p align="center">
  <strong>Always watching. Always ready.</strong><br/>
  <sub>The open-source AI agent platform that actually ships.</sub>
</p>

<p align="center">
  <a href="https://github.com/ProwlrBot/prowlrbot"><img src="https://img.shields.io/github/stars/ProwlrBot/prowlrbot?style=flat-square&color=00E5FF&label=stars" /></a>
  <a href="https://github.com/ProwlrBot/prowlrbot/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue?style=flat-square" /></a>
  <a href="https://github.com/ProwlrBot/prowlrbot/actions"><img src="https://img.shields.io/github/actions/workflow/status/ProwlrBot/prowlrbot/ci.yml?style=flat-square&label=CI" /></a>
</p>

---

> *"The best way to predict the future is to build it."* — Alan Kay
>
> So we did. And we gave it claws.

---

## What is ProwlrBot?

We got tired of AI agents that live in walled gardens, cost a fortune, and break when you sneeze. So we built an open-source platform where **your agents live on your machine**, talk to **any AI provider**, and coordinate like a pack.

**8 channels.** Discord, Telegram, DingTalk, Feishu, QQ, iMessage, Console, and custom.
**7 providers.** OpenAI, Anthropic, Groq, Z.ai, Ollama, llama.cpp, MLX.
**1 War Room.** Multi-agent coordination that actually works.

```bash
pip install prowlrbot
prowlr init --defaults
prowlr app
# That's it. Open localhost:8088 and start talking.
```

---

## The Ecosystem

We don't just build one repo and call it a day. ProwlrBot is a full ecosystem:

| | Repo | What it does |
|---|------|-------------|
| :brain: | **[prowlrbot](https://github.com/ProwlrBot/prowlrbot)** | The core. CLI, agents, channels, providers, monitoring, marketplace, War Room. |
| :handshake: | **[roar-protocol](https://github.com/ProwlrBot/roar-protocol)** | How agents talk to each other. 5-layer spec: Identity, Discovery, Connect, Exchange, Stream. |
| :package: | **[prowlr-marketplace](https://github.com/ProwlrBot/prowlr-marketplace)** | Community registry — skills, agents, prompts, MCP servers, themes, workflows. 70/30 revenue share. |
| :earth_americas: | **[agentverse](https://github.com/ProwlrBot/agentverse)** | Virtual world where agents live, level up, join guilds, and battle. Yes, really. |
| :book: | **[prowlr-docs](https://github.com/ProwlrBot/prowlr-docs)** | Docs that don't suck. Getting started, API reference, channel guides, architecture. |

---

## Why ProwlrBot?

Because every other "AI agent platform" is either:
- Closed source (Manus, Devin, Cursor)
- Cloud-only (can't self-host)
- Single-channel (just a chatbot)
- Single-provider (vendor lock-in)
- No coordination (agents can't work together)

We said no to all of that.

| | ProwlrBot | The Others |
|---|:---------:|:----------:|
| Open Source | Apache 2.0 | Mostly proprietary |
| Self-Hosted | Your machine, your data | Their cloud, their rules |
| Multi-Channel | 8 built-in + custom | 1-2 if lucky |
| Multi-Agent | War Room coordination | Solo agents |
| Provider Agnostic | 7 providers, auto-fallback | Locked to one |
| Graduated Autonomy | Watch > Guide > Delegate > Auto | All or nothing |
| Marketplace | Community + revenue sharing | Closed ecosystems |

---

## Get Involved

We're building something genuinely new and we want you in.

- :mag: **Find a task:** [`good first issue`](https://github.com/ProwlrBot/prowlrbot/labels/good%20first%20issue) labels
- :book: **Read the guide:** [CONTRIBUTING.md](https://github.com/ProwlrBot/prowlrbot/blob/main/CONTRIBUTING.md)
- :speech_balloon: **Join the conversation:** [GitHub Discussions](https://github.com/ProwlrBot/prowlrbot/discussions)
- :package: **Publish to marketplace:** [Submission guide](https://github.com/ProwlrBot/prowlr-marketplace)
- :shield: **Report vulnerabilities:** [Security Policy](https://github.com/ProwlrBot/prowlrbot/blob/main/SECURITY.md)

---

<p align="center">
  <sub>Built with obsession by the ProwlrBot community.</sub><br/>
  <sub>If you're reading this, you're early.</sub>
</p>
