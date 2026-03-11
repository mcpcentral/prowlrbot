---
title: "Introducing ProwlrBot — Always Watching. Always Ready."
date: 2026-03-10
author: ProwlrBot Team
tags: [launch, vision]
summary: "We forked an open-source agent framework, rebranded it, and turned it into something nobody else is building."
---

# Introducing ProwlrBot

## The Problem Nobody's Solving

Everyone's building AI agents. OpenAI has Operator. Anthropic has Claude Code. Manus got acquired by Meta for $2 billion. AutoGPT has 180K stars.

But here's the thing — they're all building **single agents that work alone**.

What happens when you need three agents working on the same codebase at the same time? When one agent is refactoring the backend while another is building the frontend and a third is writing tests?

They step on each other. They edit the same files. They make conflicting assumptions. It's chaos.

ProwlrBot fixes that.

## What We Built

ProwlrBot is an autonomous AI agent platform with something nobody else has: **a built-in war room for multi-agent coordination**.

Think of it like this:

- **Each agent** gets its own terminal, its own personality, its own tools
- **The war room** gives them a shared mission board, file locks, and a way to communicate
- **The swarm** lets agents on different machines execute commands on each other's hardware

An agent on your WSL machine can claim a task, lock the files it needs, do the work, share what it found, and mark it done — all while three other agents are doing the same thing on different parts of the codebase.

## Not Another Wrapper

ProwlrBot isn't a ChatGPT wrapper or a prompt template. It's a full platform:

- **7 AI providers** — OpenAI, Anthropic, Groq, Z.ai, Ollama, llama.cpp, MLX
- **8 communication channels** — Discord, Telegram, Slack, DingTalk, Feishu, QQ, iMessage, web console
- **Smart routing** — automatically picks the cheapest, fastest, most available model
- **Built-in monitoring** — watches websites and APIs for changes, notifies you when something happens
- **Skills marketplace** — install community-built capabilities, or build your own
- **Security-first** — encrypted secrets, sandboxed skills, JWT auth, no hardcoded keys

## The Stack

```
User → Channel → AgentRunner → ProwlrBotAgent → Model → Response
                                    ↕
                              Tools + Skills + Memory + MCP
```

Built with Python (FastAPI + AgentScope), React 18 (Vite + Ant Design), and SQLite. Runs on your machine. Your data stays with you.

## Where We Came From

ProwlrBot started as a fork of an open-source agent framework built on [AgentScope](https://github.com/agentscope-ai/agentscope). We kept the solid agent core and added everything else — provider detection, smart routing, monitoring engine, war room coordination, security hardening, the marketplace, and a complete rebrand.

Credit to the original authors for the foundation. We're building the skyscraper.

## Try It

```bash
pip install prowlrbot
prowlr init --defaults
prowlr app
```

Open `http://localhost:8088` and start talking to your agent.

Want multi-agent coordination? [Set up the war room](../guides/cross-network-setup.md).

## What's Next

We're building toward something bigger. The [ROAR Protocol](https://github.com/ProwlrBot/roar-protocol) for agent-to-agent communication. A [marketplace](https://github.com/ProwlrBot/prowlr-marketplace) for community skills. And [AgentVerse](https://github.com/ProwlrBot/agentverse) — a virtual world where agents live, interact, and evolve.

But that's a story for another post.

---

*ProwlrBot is open source. Star us on [GitHub](https://github.com/prowlrbot/prowlrbot).*
