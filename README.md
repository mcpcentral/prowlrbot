<p align="center">
  <img src="/console/public/logo.png" alt="ProwlrBot Logo" width="400" />
</p>

<h1 align="center">ProwlrBot</h1>

<p align="center">
  <em>Your AI agent. Your machine. Your rules.</em>
</p>

<p align="center">
  <a href="#-quick-start"><b>Get started in 60 seconds</b></a> •
  <a href="docs/README.md"><b>Docs</b></a> •
  <a href="https://github.com/ProwlrBot/prowlrbot/issues"><b>Issues</b></a> •
  <a href="https://github.com/ProwlrBot/prowlr-marketplace"><b>Marketplace</b></a>
</p>

<p align="center">
  <img src="https://img.shields.io/github/stars/ProwlrBot/prowlrbot?style=flat-square&logo=github" alt="Stars">
  <img src="https://img.shields.io/github/license/ProwlrBot/prowlrbot?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/self--hosted-first-brightgreen?style=flat-square" alt="Self-hosted">
  <img src="https://img.shields.io/badge/local%20models-Ollama%20%7C%20llama.cpp%20%7C%20MLX-blue?style=flat-square" alt="Local models">
</p>

---

ProwlrBot is a **self-hosted AI agent** that runs on your machine, connects to every channel you already use, and keeps working while you’re asleep.

It monitors websites for changes. It runs scheduled tasks. It answers your team on Discord and Telegram at the same time. It coordinates multiple AI agents so they don’t step on each other. It does all of this with **your API keys, your models, and your data — nothing leaves your network unless you want it to.**

No subscription required. No vendor lock-in. `pip install prowlrbot` and you own it.

---

## Why ProwlrBot?

There are a lot of AI chatbots. ProwlrBot is not a chatbot.

**It’s an agent that acts.** Left alone, it monitors, schedules, and responds across all your channels simultaneously. You set it up once and it keeps running.

**Your data stays yours.** API keys are stored locally in an encrypted secrets file. Conversation history lives on your machine. You can run entirely on local models with Ollama — no API key, no data leaving your network, no bill.

**It speaks where you already are.** One agent, eight channels. Discord, Telegram, DingTalk, Feishu, iMessage, and more. Your team doesn’t need to learn a new tool — ProwlrBot comes to them.

**It grows with you.** The skill marketplace means you can add capabilities without writing code. The ROAR Protocol means your agents can talk to other agents, on other machines, at other companies.

| The old way | With ProwlrBot |
|-------------|----------------|
| Check 10 tabs manually every morning | One agent monitors all of them, pings you only when something changes |
| Forget to follow up on something | Schedule it once — the agent handles it at 9am every day |
| Three Claude terminals stepping on each other | War Room coordinates them — file locks, shared task board, no conflicts |
| Paying $50/mo for a tool that phones home | Self-hosted, model-agnostic, free forever |

---

## ✨ Key Features

- 🧠 **Smart Model Router** – Automatically picks the best AI provider (OpenAI, Anthropic, Groq, local Ollama, etc.) based on cost, speed, and availability.
- 🛰️ **Multi‑Agent War Room** – Coordinate dozens of agents with file locking, task claiming, and shared context.
- 🔌 **MCP Integration** – Connect any Model Context Protocol server; tools appear instantly.
- 🌐 **Multi‑Channel Support** – Discord, Telegram, Console, and 5 more channels (custom ones too).
- 🔍 **Web Monitoring** – Watch websites/APIs for changes and trigger actions.
- ⏱️ **Cron Jobs** – Schedule autonomous agent tasks.
- 🖥️ **Web Console** – Full dashboard at `localhost:8088`.
- 🧩 **Skills Marketplace** – Extend agents with plug‑in capabilities (PDF, spreadsheets, email, browser, etc.).
- 💻 **Local First** – Run entirely on your machine with Ollama, llama.cpp, or MLX – no API keys required.

---

## 🚀 Quick Start

```bash
# 0. Set up venv
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 1. Install the package
pip install prowlrbot

# 2. Initialize with default settings
prowlr init --defaults

# 3. Set your API key (optional, for cloud models)
prowlr env set OPENAI_API_KEY sk-your-key

# 4. Start the web console
prowlr app
```

Open **http://localhost:8088** – your agent is live.

> **From source (dev):** `git clone https://github.com/ProwlrBot/prowlrbot.git && cd prowlrbot && pip install -e ".[dev]"`. See [troubleshooting](docs/troubleshooting.md) if install fails.

> **No API key?** Run locally with Ollama:
> `prowlr init --defaults && prowlr app` – ProwlrBot auto‑detects local models.

---

## 📦 Installation Options

<details>
<summary><strong>Development Install (from source)</strong></summary>

```bash
git clone https://github.com/ProwlrBot/prowlrbot.git
cd prowlrbot
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
prowlr init --defaults
prowlr app
```

</details>

<details>
<summary><strong>WSL Install Notes</strong></summary>

- Use the **Linux filesystem** – clone to `/home/user/prowlrbot`, NOT `/mnt/c/...`
- Create venv inside the project: `python3 -m venv .venv`
- If you hit I/O errors, install step‑by‑step:
  `pip install -e .` then `pip install -e ".[dev]"`
- See [Troubleshooting Guide](docs/troubleshooting.md) for WSL‑specific issues

</details>

<details>
<summary><strong>Docker</strong></summary>

```bash
docker pull ghcr.io/prowlrbot/prowlrbot:latest
docker run -p 8088:8088 -v ~/.prowlrbot:/root/.prowlrbot ghcr.io/prowlrbot/prowlrbot:latest
```

</details>

---

## 🏗️ Architecture

```
                    YOU
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
      Discord    Telegram    Console     ← 8 channels
          │          │          │
          └──────────┼──────────┘
                     ▼
             ChannelManager              ← queue + debounce
                     │
                     ▼
              AgentRunner                ← session management
                     │
                     ▼
           ProwlrBotAgent (ReAct)        ← reasoning loop
            ┌────┬────┬────┐
            ▼    ▼    ▼    ▼
         Tools Skills MCP Memory         ← capabilities
            │    │    │    │
            └────┼────┼────┘
                 ▼    ▼
         ┌───────────────────┐
         │   Smart Router    │           ← picks best model
         ├───────────────────┤
         │ OpenAI │Anthropic │
         │ Groq   │ Z.ai     │
         │ Ollama │ llama    │
         │ MLX    │          │
         └───────────────────┘
```

---

## 🛠️ Core Capabilities

### Multi‑Agent War Room

The killer feature: multiple AI agents coordinate in real‑time without stepping on each other.

```bash
# Tell your Claude Code agent:
# "Set up the war room using https://github.com/prowlrbot/prowlrbot/blob/main/INSTALL.md"
# It handles everything.
```

#### War Room – Quick Recipes

You can either let Claude handle setup, or do it manually.

- **Ask Claude (single machine, all terminals on same OS)**

  In each project where you want coordination, say:

  > "Connect this project to the ProwlrBot War Room using
  > https://github.com/prowlrbot/prowlrbot/blob/main/INSTALL.md.
  > The prowlrbot repo is already cloned at `~/dev/prowlrbot`."

  Claude will:

  - verify `prowlrbot` is installed
  - register the `prowlr-hub` MCP server
  - ask for an **agent name** and **capabilities**
  - restart so War Room tools appear (`check_mission_board`, `claim_task`, …)

- **Manual single‑machine setup (power users)**

  1. Install once per machine:

     ```bash
     git clone https://github.com/ProwlrBot/prowlrbot.git
     cd prowlrbot
     pip install -e .
     ```

  2. In your project root, create/update `.mcp.json`:

     ```jsonc
     {
       "mcpServers": {
         "prowlr-hub": {
           "command": "python3",
           "args": ["-m", "prowlrbot.hub"],
           "cwd": "/home/you/dev/prowlrbot",
           "env": {
             "PYTHONPATH": "/home/you/dev/prowlrbot/src",
             "PROWLR_AGENT_NAME": "frontend",
             "PROWLR_CAPABILITIES": "react,typescript,css"
           }
         }
       }
     }
     ```

  3. Fully restart Claude Code, then say:

     > "Call `check_mission_board` and `get_agents` so I can see the War Room."

- **Mac + WSL (cross‑machine)**

  - On the **host** (e.g. Mac) that owns the DB:

    ```bash
    cd ~/dev/prowlrbot
    PYTHONPATH=src python3 -m prowlrbot.hub.bridge
    # Bridge listens on http://<HOST-IP>:8099
    ```

  - On the **remote** (e.g. WSL) project `.mcp.json`:

    ```jsonc
    {
      "mcpServers": {
        "prowlr-hub": {
          "command": "python3",
          "args": ["-m", "prowlrbot.hub"],
          "cwd": "/home/you/dev/prowlrbot",
          "env": {
            "PYTHONPATH": "/home/you/dev/prowlrbot/src",
            "PROWLR_AGENT_NAME": "wsl-dev",
            "PROWLR_CAPABILITIES": "python,testing",
            "PROWLR_HUB_URL": "http://<HOST-IP>:8099"
          }
        }
      }
    }
    ```

  Restart Claude on both sides and run `check_mission_board` — if you see a single shared board, your terminals are in the same War Room.

## Local War Room Setup

```
cd /home/USER/PATH/prowlrbot && PYTHONPATH=src python3 -m prowlrbot.hub.bridge
```
**Terminal 1 (orchestrator)** — paste this:
```
You are the orchestrator for this session. Repo: /home/anon/dev/prowlrbot. We use the ProwlrHub War Room (MCP prowlr-hub, PROWLR_HUB_URL=http://localhost:8099). The other three terminals are WSL-2 (backend), WSL-3 (frontend), WSL-4 (tests). Your job: use check_mission_board and get_agents to plan work; when you want another terminal to do something, output commands clearly labeled [For WSL-2], [For WSL-3], [For WSL-4]. First call check_mission_board and get_agents and tell me who’s connected.
```

**Terminal 2 (backend)** — paste this:
```
You are WSL-2 (backend). Repo: /home/anon/dev/prowlrbot. War Room at http://localhost:8099. Identity: PROWLR_AGENT_NAME=wsl-backend, PROWLR_CAPABILITIES=python,api,backend. Run backend and long-lived services from the repo; use claim_task/lock_file before editing. First call check_mission_board and get_agents to register.
```

**Terminal 3 (frontend)** — paste this:
```
You are WSL-3 (frontend). Repo: /home/anon/dev/prowlrbot. War Room at http://localhost:8099. Identity: PROWLR_AGENT_NAME=wsl-frontend, PROWLR_CAPABILITIES=react,typescript,css. Run console/frontend and UI work from repo; use War Room tools before touching shared files. First call check_mission_board and get_agents to register.
```


**Terminal 4 (tests/tools)** — paste this:
```
You are WSL-4 (tests/tools). Repo: /home/anon/dev/prowlrbot. War Room at http://localhost:8099. Identity: PROWLR_AGENT_NAME=wsl-tests, PROWLR_CAPABILITIES=testing,linting,devtools. Run tests, linters, and one-off tooling; use War Room when work touches shared code. First call check_mission_board and get_agents to register.
```
#### Multi‑terminal Claude prompts (Mac + WSL)

Drop‑in prompts you can copy‑paste into three shells so Claude understands your setup and keeps them coordinated.

- **Mac terminal (orchestrator)**

  ```text
  You are my **orchestrator shell** on macOS.

  Context:
  - I’m developing ProwlrBot.
  - I have three terminals:
    - This one (Mac): orchestrator / planning.
    - A WSL terminal called **WSL-A**.
    - A second WSL terminal called **WSL-B**.
  - On both WSL terminals, the repo lives at `/home/anon/dev/prowlrbot`.

  Your role in this Mac shell:
  1. Plan the work and keep track of which terminal does what.
  2. Decide which commands should run on WSL-A vs WSL-B.
  3. When you want to use a WSL terminal, give me exact commands (with explanations) that I can copy‑paste into that terminal.
  4. Assume WSL-A is “backend + long‑running services” and WSL-B is “frontend, tests, and tools” unless we explicitly change that.

  Important:
  - Never assume you can run commands directly in WSL; always output commands for me to paste there.
  - When you generate commands for WSL-A or WSL-B, label them clearly like:

    [For WSL-A]
    cd /home/anon/dev/prowlrbot
    ...

    [For WSL-B]
    cd /home/anon/dev/prowlrbot
    ...

  First, confirm you understand the three‑terminal setup and then propose a simple default layout (what runs on Mac, WSL-A, and WSL-B).
  ```

- **WSL-A terminal (backend + long‑running)**

  ```text
  You are my **WSL-A** terminal (Ubuntu in WSL2).

  Context:
  - The ProwlrBot repo is at `/home/anon/dev/prowlrbot`.
  - The Mac “orchestrator” terminal will tell us what to run here.
  - This terminal is primarily for:
    - Running the ProwlrBot backend and long‑lived processes.
    - Running migrations or backend‑focused utilities.

  Your role:
  1. Treat instructions that mention “WSL-A” as coming from the Mac orchestrator.
  2. Turn high‑level goals into concrete commands I can run here, but don’t assume you know my environment until you’ve checked (for example, whether `uv`, `docker`, or `poetry` are installed).
  3. Before giving commands, briefly explain what they do and any prerequisites.

  Conventions:
  - Always start backend commands from `/home/anon/dev/prowlrbot` unless I say otherwise.
  - Prefer safe, idempotent commands over destructive ones.
  - When in doubt, ask one clarifying question, then propose a plan.

  First, verify the repo exists and suggest the standard way to start the backend here.
  ```

- **WSL-B terminal (frontend / tests / tools)**

  ```text
  You are my **WSL-B** terminal (Ubuntu in WSL2).

  Context:
  - The ProwlrBot repo is at `/home/anon/dev/prowlrbot`.
  - The Mac “orchestrator” terminal coordinates work across three shells:
    - Mac: planning/orchestration
    - WSL-A: backend + long‑running processes
    - WSL-B: frontend, tests, and supporting tools
  - This terminal is used for:
    - Running the console frontend (Vite dev server or production build).
    - Running test suites and linters.
    - One‑off scripts that shouldn’t block WSL-A.

  Your role:
  1. Treat instructions that mention “WSL-B” as coming from the orchestrator.
  2. Turn high‑level tasks (“run the frontend”, “run all tests”, “lint the console”) into clear, copy‑pasteable command sequences.
  3. Explain what each command does in one line, then show the commands.

  Conventions:
  - Assume starting point `/home/anon/dev/prowlrbot`.
  - For frontend tasks, work under `console/` by default.
  - Prefer commands that keep logs readable and don’t block the terminal forever unless explicitly told (for example, suggest `npm run dev` with a note that it will stay running).

  First, confirm you understand your role and then propose:
  - One set of commands to run the console in dev mode.
  - One set of commands to run the main test suite.
  ```

**Mission Board (live dashboard):**

```
╔══════════════════════════════════════════════════════════════╗
║                      MISSION BOARD                          ║
╠════╦══════════════════════╦═══════════╦══════════════════════╣
║ ID ║ Task                 ║ Agent     ║ Status               ║
╠════╬══════════════════════╬═══════════╬══════════════════════╣
║  1 ║ Build auth API       ║ backend   ║ In Progress          ║
║  2 ║ Login page           ║ frontend  ║ In Progress          ║
║  3 ║ Write auth tests     ║ tester    ║ Waiting (locked)     ║
║  4 ║ API documentation    ║ --        ║ Available            ║
╚════╩══════════════════════╩═══════════╩══════════════════════╝

Locked Files:
  src/api/auth.py ─── backend (Task #1)
  src/api/models.py ─── backend (Task #1)
  src/components/Login.tsx ─── frontend (Task #2)

Shared Findings:
  backend: "Auth requires JWT — using PyJWT with RS256"
  frontend: "Using shadcn/ui form components for login"
```

**13 Coordination Tools** – `check_mission_board`, `claim_task`, `lock_file`, `share_finding`, and more.
**Cross‑Machine Support** – Agents on different machines can connect via HTTP bridge. Use Tailscale, Cloudflare Tunnel, or SSH for cross‑network setups.
[Full guide →](docs/guides/cross-network-setup.md)

---

### Smart Model Router

Automatically scores providers: `cost × w₁ + speed × w₂ + availability × w₃` and picks the winner.

| Provider | How to enable |
|----------|---------------|
| OpenAI   | `OPENAI_API_KEY` |
| Anthropic| `ANTHROPIC_API_KEY` |
| Groq     | `GROQ_API_KEY` |
| Z.ai     | `ZAI_API_KEY` |
| Ollama   | Local (no key) |
| llama.cpp| Local (no key) |
| MLX      | Local (Apple Silicon) |

---

### Web Monitoring & Cron

**Monitor websites or APIs** for changes and trigger actions:

```bash
prowlr monitor add https://example.com/pricing --interval 1h
prowlr monitor list
```

**Schedule autonomous agent tasks** with cron:

```bash
prowlr cron add "Check email and summarize" --schedule "0 9 * * *"
prowlr cron add "Monitor competitors" --interval 30m
```

---

### REST API & MCP Integration

**REST API** at `http://localhost:8088/api` – manage agents, channels, skills, cron jobs, and more.
[API Reference →](docs/api.md)

**MCP Integration** – Connect any MCP server; tools appear instantly (hot‑reload enabled).

```json
{
  "mcp": {
    "servers": {
      "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"]
      }
    }
  }
}
```

---

### Local Models (No Cloud)

Run everything on your machine – no API keys, no data leaving your computer.

| Backend      | Best For                     | Install                             |
|--------------|------------------------------|-------------------------------------|
| **Ollama**   | Cross‑platform, easy         | [ollama.ai](https://ollama.ai)      |
| **llama.cpp**| GGUF models, CPU/GPU         | `pip install 'prowlrbot[llamacpp]'` |
| **MLX**      | Apple Silicon (M1–M4)        | `pip install 'prowlrbot[mlx]'`      |

---

## 📂 Project Structure

```
prowlrbot/
├── src/prowlrbot/
│   ├── agents/            # ReAct agent, tools, skills, memory
│   ├── app/                # FastAPI app, channels, cron, MCP, routers
│   ├── cli/                 # Click CLI (`prowlr` command)
│   ├── config/              # Pydantic models + hot‑reload
│   ├── providers/           # Model registry, detector, smart router
│   ├── monitor/             # Web/API change detection
│   ├── hub/                 # ProwlrHub war room (MCP server)
│   └── envs/                # Encrypted secret store
├── console/                  # React 18 + Vite + Ant Design dashboard
├── swarm/                    # Cross‑machine Redis execution
├── plugins/                  # Claude Code plugins
├── docs/                      # Documentation hub
│   ├── blog/                  # Humanized posts
│   ├── guides/                # Setup + troubleshooting
│   ├── protocols/             # ROAR protocol specs
│   └── README.md              # Documentation index
└── website/                   # GitHub Pages docs site
```

---

## 🌐 Ecosystem

ProwlrBot is part of a family of projects:

| Project | Description |
|---------|-------------|
| [ProwlrBot](https://github.com/ProwlrBot/prowlrbot) | Core agent platform |
| [ROAR Protocol](https://github.com/ProwlrBot/roar-protocol) · [PyPI](https://pypi.org/project/roar-protocol/) | Agent communication standard — `pip install roar-protocol` |
| [Marketplace](https://github.com/ProwlrBot/prowlr-marketplace) | Skills & agents marketplace |
| [Docs](https://github.com/ProwlrBot/prowlr-docs) | Centralized documentation |
| [AgentVerse](https://github.com/ProwlrBot/agentverse) | Virtual agent world for testing |

### 🎬 See ROAR in action

**One protocol. Any agent.** ProwlrBot speaks [ROAR](https://github.com/ProwlrBot/roar-protocol) — the open agent communication protocol. Discover agents, fetch their cards, and send tasks over HTTP or WebSocket. No vendor lock-in; any ROAR-compatible agent can talk to any other.

| Try it | Description |
|--------|-------------|
| **[▶ Live demo](https://prowlrbot.com/demo/roar-demo.html)** | Point at any ROAR endpoint (e.g. `app.prowlrbot.com`), check health, fetch the agent card, send a test message — all in your browser, zero install. |
| **CLI** | One-liners below. |
| **Video** | Record the demo (health → card → send message), upload to YouTube/Loom, and [add the link](docs/guides/roar-usage.md) for a one‑minute showoff. |

```bash
# Quick CLI check (no auth)
curl -s https://app.prowlrbot.com/roar/health
curl -s https://app.prowlrbot.com/roar/card | jq .
```

---

## 🤝 Contributing

We ❤️ contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for commit conventions, skill structure, and PR guidelines.

<a href="https://github.com/ProwlrBot/prowlrbot/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=ProwlrBot/prowlrbot" />
</a>

---

## 💬 Community

Join the community — ask questions, share what you've built, report bugs, suggest features.

<p align="center">
  <a href="https://github.com/ProwlrBot/prowlrbot/discussions">
    <img src="https://img.shields.io/badge/GitHub_Discussions-Join_the_conversation-181717?style=for-the-badge&logo=github" alt="GitHub Discussions" />
  </a>
  &nbsp;
  <a href="https://github.com/ProwlrBot/prowlrbot/issues">
    <img src="https://img.shields.io/badge/GitHub_Issues-Report_a_bug-red?style=for-the-badge&logo=github" alt="GitHub Issues" />
  </a>
</p>

**Good first ways to get involved:**

- ⭐ Star the repo — it helps more people find the project
- 🐛 [Open an issue](https://github.com/ProwlrBot/prowlrbot/issues) — bugs, questions, ideas, all welcome
- 💬 [Start a discussion](https://github.com/ProwlrBot/prowlrbot/discussions) — share your setup, show off a skill you built, ask how something works
- 🔧 [Build a skill](docs/guides/building-skills.md) — add it to the marketplace so others can use it
- 📣 Tell someone — the fastest way to grow this is word of mouth

---

## 💖 Support the Project

ProwlrBot is free, open source, and will stay that way. If it saves you time or solves a real problem, consider sponsoring — it goes toward development time, infrastructure, and keeping the lights on.

<p align="center">
  <a href="https://github.com/sponsors/kdairatchi">
    <img src="https://img.shields.io/badge/GitHub_Sponsors-Sponsor-EA4AAA?style=for-the-badge&logo=github-sponsors&logoColor=white" alt="GitHub Sponsors" />
  </a>
  &nbsp;
  <a href="https://buymeacoffee.com/kdairatchi">
    <img src="https://img.shields.io/badge/Buy_Me_a_Coffee-Support-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black" alt="Buy Me a Coffee" />
  </a>
  &nbsp;
  <a href="https://ko-fi.com/kdairatchi">
    <img src="https://img.shields.io/badge/Ko--fi-Donate-FF5E5B?style=for-the-badge&logo=ko-fi&logoColor=white" alt="Ko-fi" />
  </a>
  &nbsp;
  <a href="https://opencollective.com/prowlrbot">
    <img src="https://img.shields.io/badge/Open_Collective-Contribute-3295A8?style=for-the-badge&logo=opencollective&logoColor=white" alt="Open Collective" />
  </a>
</p>

**Sponsoring is completely optional.** The software is yours either way. But if you want to say thanks and help push development forward, any amount makes a real difference.

---

## 📄 License

ProwlrBot is open source under the [Apache 2.0 License](LICENSE).

---

<p align="center">
  <strong>ProwlrBot</strong> — Always watching. Always ready.<br/><br/>
  <a href="docs/README.md">📚 Docs</a> ·
  <a href="docs/blog/">📰 Blog</a> ·
  <a href="https://github.com/ProwlrBot/prowlrbot/discussions">💬 Discussions</a> ·
  <a href="https://github.com/prowlrbot/prowlrbot/issues">🐛 Issues</a> ·
  <a href="https://github.com/ProwlrBot/prowlr-marketplace">🛒 Marketplace</a> ·
  <a href="CONTRIBUTING.md">🤝 Contribute</a> ·
  <a href="https://github.com/sponsors/kdairatchi">💖 Sponsor</a>
</p>
