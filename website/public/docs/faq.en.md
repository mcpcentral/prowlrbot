# FAQ

This page collects the most frequently asked questions from the community.
Click a question to expand the answer.

---

### ProwlrBot vs OpenClaw: Feature Comparison

Please check the [Comparison](/docs/comparison) page for detailed feature comparison.

### How to install ProwlrBot

ProwlrBot supports multiple installation methods. See
[Quick Start](https://prowlr.agentscope.io/docs/quickstart) for details:

1. One-line installer (sets up Python automatically)

```
# macOS / Linux:
curl -fsSL https://prowlr.agentscope.io/install.sh | bash
# Windows (PowerShell):
irm https://prowlr.agentscope.io/install.ps1 | iex
# For latest instructions, refer to docs and prefer pip if needed.
```

2. Install with pip

Python version requirement: >= 3.10, < 3.14

```
pip install prowlr
```

3. Install with Docker

If Docker is installed, run the following commands and then open
`http://127.0.0.1:8088/` in your browser:

```
docker pull agentscope/prowlr:latest
docker run -p 8088:8088 -v prowlr-data:/app/working agentscope/prowlr:latest
```

### How to update ProwlrBot

To update ProwlrBot, use the method matching your installation type:

1. If installed via one-line script, re-run the installer to upgrade.

2. If installed via pip, run:

```
pip install --upgrade prowlr
```

3. If installed from source, pull the latest code and reinstall:

```
cd ProwlrBot
git pull origin main
pip install -e .
```

4. If using Docker, pull the latest image and restart the container:

```
docker pull agentscope/prowlr:latest
docker run -p 8088:8088 -v prowlr-data:/app/working agentscope/prowlr:latest
```

After upgrading, restart the service with `prowlr app`.

### How to initialize and start ProwlrBot service

Recommended quick initialization:

```bash
prowlr init --defaults
```

Start service:

```bash
prowlr app
```

The default Console URL is `http://127.0.0.1:8088/`. After quick init, you can
open Console and customize settings. See
[Quick Start](https://prowlr.agentscope.io/docs/quickstart).

### Open-source repository

ProwlrBot is open source. Official repository:
`https://github.com/agentscope-ai/ProwlrBot`

### Where to check latest version upgrade details

You can check version changes in ProwlrBot GitHub
[Releases](https://github.com/agentscope-ai/ProwlrBot/releases).

### How to configure models

In Console, go to **Settings -> Models**. See
[Console -> Models](https://prowlr.agentscope.io/docs/console#models) for
details.

- Cloud models: fill provider API key (ModelScope, DashScope, or custom), then
  choose the active model.
- Local models: supports `llama.cpp`, `MLX`, and Ollama. After download, select
  the active model on the same page.

You can also use `prowlr models` CLI commands for configuration, download, and
switching. See
[CLI -> Models and Environment Variables -> prowlr models](https://prowlr.agentscope.io/docs/cli#prowlr-models).

### How to manage Skills

Go to **Agent -> Skills** in Console. You can enable/disable Skills, create
custom Skills, and import Skills from Skills Hub. See
[Skills](https://prowlr.agentscope.io/docs/skills).

### How to configure MCP

Go to **Agent -> MCP** in Console. You can enable/disable/delete/create MCP
clients there. See [MCP](https://prowlr.agentscope.io/docs/mcp).

### Common error

1. Error pattern: `You didn't provide an API key`

Error detail:

```
Error: Unknown agent error: AuthenticationError: Error code: 401 - {'error': {'message': "You didn't provide an API key. You need to provide your API key in an Authorization header using Bearer auth (i.e. Authorization: Bearer YOUR_KEY). ", 'type': 'invalid_request_error', 'param': None, 'code': None}, 'request_id': 'xxx'}
```

Cause 1: model API key is not configured. Get an API key and configure it in
**Console -> Settings -> Models**.

Cause 2: key is configured but still fails. In most cases, one of the
configuration fields is incorrect (for example `base_url`, `api key`, or model
name).

ProwlrBot supports API keys obtained via DashScope Coding Plan. If it still fails,
please check:

- whether `base_url` is correct;
- whether the API key is copied completely (no extra spaces);
- whether the model name exactly matches the provider value (case-sensitive).

Reference for the correct key acquisition flow:
https://help.aliyun.com/zh/model-studio/coding-plan-quickstart#2531c37fd64f9

---

### How to get support when errors occur

To speed up troubleshooting and fixes, please create an issue in the ProwlrBot
GitHub repository and include complete error information:
https://github.com/agentscope-ai/ProwlrBot/issues

In many Console errors, a detailed error file path is included. For example:

Error: Unknown agent error: AuthenticationError: Error code: 401 - {'error': {'message': "You didn't provide an API key. You need to provide your API key in an Authorization header using Bearer auth (i.e. Authorization: Bearer YOUR_KEY). ", 'type': 'invalid_request_error', 'param': None, 'code': None}, 'request_id': 'xxx'}(Details: /var/folders/.../prowlr_query_error_qzbx1mv1.json)

Please upload that file (for example
`/var/folders/.../prowlr_query_error_qzbx1mv1.json`) together with your current
model provider, model name, and exact ProwlrBot version.
