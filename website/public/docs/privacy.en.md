# Privacy Policy

**Last updated:** March 11, 2026

---

## The Short Version

ProwlrBot runs on **your machine**. Your data stays with you. We don't collect it, we don't sell it, we don't even see it.

---

## What ProwlrBot Does Not Collect

- No telemetry
- No usage analytics
- No crash reports
- No personal information
- No conversation logs
- No API keys or secrets

ProwlrBot is a self-hosted application. Everything runs locally. There is no "phone home" behavior.

## What Stays on Your Machine

| Data | Location | Who Can Access |
|:-----|:---------|:---------------|
| Configuration | `~/.prowlrbot/config.json` | You |
| Chat history | `~/.prowlrbot/chats/` | You |
| API keys | `~/.prowlrbot.secret/envs.json` | You (mode 0o600) |
| War Room data | `~/.prowlrbot/hub.db` | You + connected agents |
| Installed skills | `~/.prowlrbot/active_skills/` | You |

## Third-Party Services

When you configure AI providers (OpenAI, Anthropic, Groq, etc.), your messages are sent to those providers according to **their** privacy policies. ProwlrBot does not add any additional data to these requests beyond what is needed to generate a response.

| Provider | Privacy Policy |
|:---------|:--------------|
| OpenAI | openai.com/policies/privacy-policy |
| Anthropic | anthropic.com/privacy |
| Groq | groq.com/privacy-policy |
| Ollama (local) | No data leaves your machine |
| llama.cpp (local) | No data leaves your machine |
| MLX (local) | No data leaves your machine |

## Marketplace

The ProwlrBot marketplace (`prowlr market update`) fetches listing metadata from GitHub. This is a public API call — no authentication or personal data is required unless you provide a GitHub token for higher rate limits.

## War Room / Cross-Machine

If you enable cross-machine coordination (ProwlrHub bridge), data travels between your machines over the network you configure (Tailscale VPN recommended). ProwlrBot does not route any data through our servers.

## Changes to This Policy

If we ever change this policy, we will update this page and the `Last updated` date above. Since ProwlrBot is open source, you can always audit exactly what the software does.

## Contact

Questions? Open an issue on [GitHub](https://github.com/ProwlrBot/prowlrbot/issues).

---

*Your data. Your machine. Your rules.*
