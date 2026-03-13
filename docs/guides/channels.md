# Channel Setup Guide

ProwlrBot supports 7 built-in channels and unlimited custom channels. Channels receive user messages and deliver agent replies.

---

## Overview

| Channel | Status | Credentials needed |
|---------|--------|-------------------|
| Console | Built-in, enabled by default | None |
| Discord | Built-in | Bot token |
| Telegram | Built-in | Bot token from BotFather |
| DingTalk | Built-in | Client ID + Client Secret |
| Feishu / Lark | Built-in | App ID + App Secret |
| QQ | Built-in | App ID + Client Secret |
| iMessage | Built-in (macOS only) | None (reads Messages DB directly) |

All channel config lives in `~/.prowlrbot/config.json` under the `channels` key.

---

## Configuring channels

### Interactive (recommended)

```bash
prowlr channels config
```

Use arrow keys to select a channel, Enter to configure it, "Save and exit" when done.

### Per-channel quickstart

```bash
prowlr channels add discord       # install + prompt for bot token
prowlr channels add telegram
prowlr channels add dingtalk
prowlr channels add feishu
prowlr channels add qq
prowlr channels add imessage
```

Pass `--no-configure` to add without the interactive prompt:

```bash
prowlr channels add discord --no-configure
```

Then edit `~/.prowlrbot/config.json` directly or re-run `prowlr channels config`.

---

## Discord

### Create the bot

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications) → **New Application**
2. Under **Bot** tab → **Add Bot** → copy the token
3. Under **OAuth2 > URL Generator**: select `bot` scope, then `Send Messages` + `Read Message History` permissions
4. Use the generated URL to invite the bot to your server

### Configure ProwlrBot

```bash
prowlr channels add discord
# Enter bot token when prompted
```

Or directly in `~/.prowlrbot/config.json`:

```json
{
  "channels": {
    "discord": {
      "enabled": true,
      "bot_token": "YOUR_BOT_TOKEN",
      "bot_prefix": "[BOT]",
      "http_proxy": "",
      "http_proxy_auth": ""
    }
  }
}
```

**Proxy support:** Discord is blocked in some regions. Use `http_proxy` (e.g., `http://127.0.0.1:7890`) and `http_proxy_auth` (`user:pass`) if needed.

### Enable required intents

In the Discord Developer Portal → Bot tab, enable:
- Server Members Intent
- Message Content Intent (required to read message text)

---

## Telegram

### Create the bot

1. Open Telegram, search for `@BotFather`
2. Send `/newbot`, follow prompts, copy the token (format: `1234567890:ABCdef...`)

### Configure ProwlrBot

```bash
prowlr channels add telegram
# Enter bot token when prompted
```

Config file:

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "bot_token": "1234567890:ABCdef...",
      "bot_prefix": "",
      "show_typing": true,
      "http_proxy": "",
      "http_proxy_auth": ""
    }
  }
}
```

`show_typing: true` sends a typing indicator while the agent processes.

**Proxy:** Same as Discord — set `http_proxy` if Telegram is blocked.

---

## DingTalk

### Create the application

1. Go to [open.dingtalk.com](https://open.dingtalk.com) → Developer Console
2. Create an application → **H5 Micro App** or **Enterprise Internal App**
3. In **Permissions**, add: message reading, message sending
4. Copy **Client ID** (AppKey) and **Client Secret** (AppSecret)
5. In **Event Subscription**, set the message receive URL:
   `http://your-server:8088/api/channels/dingtalk/callback`

### Configure ProwlrBot

```bash
prowlr channels add dingtalk
```

Config:

```json
{
  "channels": {
    "dingtalk": {
      "enabled": true,
      "client_id": "ding...",
      "client_secret": "your_secret",
      "bot_prefix": "",
      "media_dir": "~/.prowlrbot/media"
    }
  }
}
```

---

## Feishu / Lark

### Create the application

1. Go to [open.feishu.cn](https://open.feishu.cn) (Feishu) or [open.larksuite.com](https://open.larksuite.com) (Lark)
2. Create an application → **Custom App**
3. Add permissions: `im:message` (read and send messages)
4. Under **Event Subscriptions**: add `im.message.receive_v1`
5. Set request URL: `http://your-server:8088/api/channels/feishu/callback`
6. Copy **App ID** and **App Secret** from credentials

### Configure ProwlrBot

```bash
prowlr channels add feishu
```

Config:

```json
{
  "channels": {
    "feishu": {
      "enabled": true,
      "app_id": "cli_...",
      "app_secret": "your_secret",
      "encrypt_key": "",
      "verification_token": "",
      "bot_prefix": "",
      "media_dir": "~/.prowlrbot/media"
    }
  }
}
```

`encrypt_key` and `verification_token` are optional — set them if you enable encryption in Feishu's event subscription settings.

---

## QQ

### Create the bot application

1. Go to [q.qq.com](https://q.qq.com) → Developer Platform
2. Create application → Bot type
3. Copy **App ID** and **Client Secret**
4. Set callback URL: `http://your-server:8088/api/channels/qq/callback`

### Configure ProwlrBot

```bash
prowlr channels add qq
```

Config:

```json
{
  "channels": {
    "qq": {
      "enabled": true,
      "app_id": "your_app_id",
      "client_secret": "your_secret",
      "bot_prefix": ""
    }
  }
}
```

---

## iMessage (macOS only)

iMessage works by polling the local Messages database (`~/Library/Messages/chat.db`). No external credentials needed, but it only works on macOS.

### Requirements

- macOS with Messages app configured
- ProwlrBot process must have **Full Disk Access** (System Preferences → Security & Privacy → Privacy → Full Disk Access)
- The bot must be running on the same Mac where iMessage is signed in

### Configure ProwlrBot

```bash
prowlr channels add imessage
```

Config:

```json
{
  "channels": {
    "imessage": {
      "enabled": true,
      "bot_prefix": "[BOT]",
      "db_path": "~/Library/Messages/chat.db",
      "poll_sec": 1.0
    }
  }
}
```

`poll_sec` controls how often the DB is checked. 1 second is a good default.

---

## Console

The Console channel reads from stdin and writes to stdout. Enabled by default. Useful for testing without a messaging app.

```bash
prowlr app
# Open http://localhost:8088 and use the chat interface

# Or send a message via the REST API:
curl -X POST http://localhost:8088/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "channel": "console"}'
```

Config:

```json
{
  "channels": {
    "console": {
      "enabled": true,
      "bot_prefix": "[BOT] "
    }
  }
}
```

---

## Custom channels

If you need a channel not listed above (Slack, WhatsApp, WeChat, custom webhook, etc.), you can build one.

### Scaffold a stub

```bash
prowlr channels install slack        # creates ~/.prowlrbot/custom_channels/slack.py
```

Or copy an existing module:

```bash
prowlr channels install slack --path ./my_slack_channel.py
```

### Implement the stub

The generated file at `~/.prowlrbot/custom_channels/slack.py` has this structure:

```python
from prowlrbot.app.channels.base import BaseChannel
from prowlrbot.app.channels.schema import ChannelType

class CustomChannel(BaseChannel):
    channel: ChannelType = "slack"

    @classmethod
    def from_config(cls, process, config, on_reply_sent=None, show_tool_details=True):
        return cls(process=process, ...)

    def build_agent_request_from_native(self, native_payload):
        # Convert incoming webhook payload to AgentRequest
        ...

    async def start(self):
        # Start polling / webhook listener
        ...

    async def stop(self):
        # Clean up
        ...

    async def send(self, to_handle: str, text: str, meta=None):
        # Send reply back to the channel (e.g., POST to Slack API)
        ...
```

The key method is `build_agent_request_from_native()` — it converts the channel's native message format into a `TextContent` / `ImageContent` / `FileContent` list, then calls `build_agent_request_from_user_content()`.

### Register in config

After implementing:

```bash
prowlr channels add slack --no-configure
# Then edit config.json to add your channel's config fields
```

Custom channels are loaded from `~/.prowlrbot/custom_channels/` at startup. No restart needed if using hot-reload — the manager picks them up automatically.

---

## Message flow

```
Incoming message (Discord/Telegram/etc.)
    │
    ▼
Channel.build_agent_request_from_native(payload)
    │
    ▼
content_parts = [TextContent, ImageContent, FileContent]
    │
    ▼
AgentRequest { channel_id, sender_id, session_id, content_parts }
    │
    ▼
ChannelManager queue (4 async workers per channel)
    │
    ▼
AgentRunner → ProwlrBotAgent (ReAct loop)
    │
    ▼
Channel.send(to_handle, text) → reply delivered
```

---

## Enabling channels programmatically

To enable a channel via the REST API:

```bash
# PUT the full config via API
curl -X PUT http://localhost:8088/api/config \
  -H "Content-Type: application/json" \
  -d '{"channels": {"discord": {"enabled": true, "bot_token": "..."}}}'

# Then restart the app to pick up changes
prowlr app
```
