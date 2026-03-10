# Introduction

This page describes what ProwlrBot is, what it can do, and how to get started by
following the docs.

---

## What is ProwlrBot?

ProwlrBot is an **autonomous AI agent platform** that runs in your own environment. Always watching. Always ready.

> Unlike closed-source alternatives like Manus.ai ($2B acquisition), Devin ($500/mo), or OpenAI Operator, ProwlrBot is fully open source (Apache 2.0), self-hosted, and free — with more features than any of them. See the [full comparison](./comparison).

- **Multi-channel chat** — Talk to your agent via DingTalk, Feishu, QQ, Discord, Telegram, iMessage, and more.
- **Scheduled execution** — Run tasks automatically on your configured schedule.
- **Driven by Skills — the possibilities are open-ended** — Built-in skills include cron (scheduled jobs), PDF and forms, Word/Excel/PPT handling, news digest, file reading, and more; add custom skills as described in [Skills](./skills).
- **Web monitoring** — Detect website changes, monitor APIs, and get smart notifications automatically.
- **All data stays local** — No third-party hosting. Your secrets, your servers.

ProwlrBot is a fork of [CoPaw](https://github.com/agentscope-ai/CoPaw), fully rebranded and enhanced, built on
[AgentScope](https://github.com/agentscope-ai/agentscope),
[AgentScope Runtime](https://github.com/agentscope-ai/agentscope-runtime), and
[ReMe](https://github.com/agentscope-ai/ReMe).

---

## How do you use ProwlrBot?

You use ProwlrBot in two main ways:

1. **Chat in your messaging apps**
   Send messages in DingTalk, Feishu, QQ, Discord, Telegram, or iMessage (Mac only); ProwlrBot replies
   in the same app and can look things up, manage todos, answer questions —
   whatever the enabled Skills support. One ProwlrBot instance can be connected to
   several apps; it replies in the channel where you last talked.

2. **Run on a schedule**
   Without sending a message each time, ProwlrBot can run at set times:
   - Send a fixed message to a channel (e.g. "Good morning" to DingTalk at 9am);
   - Ask ProwlrBot a question and send the answer to a channel (e.g. every 2 hours
     ask "What are my todos?" and post the reply to DingTalk);
   - Run a "check-in" or digest: ask ProwlrBot a block of questions you wrote and
     send the answer to the channel you last used.

After you install, connect at least one channel, and start the server, you can
chat with ProwlrBot in DingTalk, Feishu, QQ, etc. and use scheduled messages and check-ins;
what it actually does depends on which Skills you enable.

---

## Terms you'll see in the docs

- **Channel** — Where you talk to ProwlrBot (DingTalk, Feishu, QQ, Discord, Telegram, iMessage, etc.).
  Configure each in [Channels](./channels).
- **Heartbeat** — On a fixed interval, ask ProwlrBot a block of text you wrote and
  optionally send the answer to the channel you last used. See
  [Heartbeat](./heartbeat).
- **Cron jobs** — Scheduled tasks (send X at 9am, ask Y every 2h, etc.), managed
  via [CLI](./cli) or API.

Each term is explained in detail in its chapter.

---

## Suggested order

1. **[Quick start](./quickstart)** — Get the server running in three commands.
2. **[Console](./console)** — Once the server is running, **before configuring
   channels**, you can use the Console (open the root URL in your browser) to
   chat with ProwlrBot and configure the agent. This helps you see how ProwlrBot works.
3. **Configure and use as needed**:
   - [Channels](./channels) — Connect DingTalk / Feishu / QQ / Discord / Telegram / iMessage to
     chat with ProwlrBot in those apps;
   - [Heartbeat](./heartbeat) — Set up scheduled check-in or digest (optional);
   - [CLI](./cli) — Init, cron jobs, clean working dir, etc.;
   - [Skills](./skills) — Understand and extend ProwlrBot's capabilities;
   - [Config & working dir](./config) — Working directory and config file.
