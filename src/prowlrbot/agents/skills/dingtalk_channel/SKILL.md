---
name: dingtalk_channel_connect
description: "Use a visible browser to automate DingTalk channel setup for ProwlrBot. Applicable when the user mentions DingTalk, developer console, Client ID, Client Secret, bot, Stream mode, binding or configuring a channel. Supports pausing at login pages for user authentication."
metadata:
  {
    "prowlr":
      {
        "emoji": "🤖",
        "requires": {}
      }
  }
---

# DingTalk Channel Auto-Connect (Visible Browser)

This skill automates the creation of a DingTalk app and binding it to a ProwlrBot channel via a visible browser.

## Mandatory Rules

1. Must launch browser in visible mode:

```json
{"action": "start", "headed": true}
```

2. Must pause at login gates:
   - If a login page appears (scan QR code, phone/password login, etc.), immediately stop automation.
   - Clearly prompt the user to log in manually, then wait for their confirmation ("done" / "continue").
   - Do not proceed until the user confirms.

3. All app configuration changes require creating a new version and publishing:
   - After configuring bot settings, **you must publish the bot**.
   - Whether creating a new app or modifying app info (name, description, icon, bot config, etc.), you **must create a new version and publish**.
   - Do not claim the configuration is active until publishing is complete.

## Pre-Execution Confirmation (Required)

Before starting automation, confirm with the user the customizable fields, image requirements, and defaults:

1. Let the user customize these fields:
   - App name
   - App description
   - Bot icon image (URL or local path)
   - Bot message preview image (URL or local path)

2. Clearly state image requirements:
   - Bot icon: JPG/PNG only, `240x240px` or larger, `1:1` ratio, under `2MB`, no rounded corners.
   - Bot message preview: `png/jpeg/jpg` format, under `2MB`.

3. State the defaults (used when user doesn't specify):
   - App name: `ProwlrBot`
   - App description: `Your personal assistant`
   - Bot icon: `https://img.alicdn.com/imgextra/i4/O1CN01M0iyHF1FVNzM9qjC0_!!6000000000492-2-tps-254-254.png`
   - Bot message preview: `https://img.alicdn.com/imgextra/i4/O1CN01M0iyHF1FVNzM9qjC0_!!6000000000492-2-tps-254-254.png`

4. If the user provides no custom values, confirm:
   - "Using all defaults (ProwlrBot / Your personal assistant / default images). Proceeding."

## Image Upload Strategy (URL and local path supported)

1. If the user provides a local path, use it directly for upload.
2. If the user provides an image URL, download it to a local temp file first, then upload.
3. Upload sequence must be:
   - Click the page upload trigger (triggers file chooser)
   - Call `file_upload` with the local path array (`paths_json`)
4. If upload fails due to image spec violations (size, ratio, dimensions, format):
   - Pause automation immediately
   - Ask the user to manually upload a compliant image
   - After user confirms "uploaded/continue", resume from current step

### Upload Practical Tips

1. `file_upload`'s `paths_json` must be a "JSON string array" — mind the escaping:

```json
{
  "action": "file_upload",
  "paths_json": "[\"xxx.png\"]",
  "frame_selector": "iframe[src*=\"/fe/app?isHideOuterFrame=true\"]"
}
```

2. If the page uses iframes, include `frame_selector` — otherwise the upload control or chooser may not be found.

3. You must click the upload trigger before calling `file_upload`; otherwise you'll get:
   - `No chooser. Click upload then file_upload.`

4. Common structural patterns for locating the bot icon area (examples):
   - `text: "* Bot Icon"`
   - `button: "Use App Icon"`
   - `button: "avatar"` (usually contains `img "avatar"`)

5. When both "Use App Icon" and "avatar" appear in the snapshot, prefer clicking the `avatar` button to trigger upload, then call `file_upload`.

## Automation Flow

### Step 1: Open DingTalk Developer Console

1. Launch browser in visible mode (`headed: true`)
2. Navigate to `https://open-dev.dingtalk.com/`
3. Call `snapshot` to check if login is required

If login is needed, pause with this message:

> Login required for the DingTalk developer console. I've paused automation — please log in using the browser window. Reply "continue" when done, and I'll resume from the current page.

### Step 2: Create an Internal Enterprise App

After user confirms login:

1. Navigate to the creation path:
   - App Development -> Internal Enterprise Apps -> DingTalk App -> Create App
2. Fill in app info (use user's custom values, or defaults):
   - App name: default `ProwlrBot`
   - App description: default `Your personal assistant`
3. Save and create the app

If the page text or structure differs from expected, re-`snapshot` and locate elements by visible text semantics.

### Step 3: Add Bot Capability and Publish

1. Click **Add Capability** under **App Capabilities**, find **Bot** and add it
2. Toggle the **Bot Configuration** switch to enabled
3. Fill in **Bot Name**, **Bot Summary**, and **Bot Description**
4. Upload **Bot Icon** (user-specified or default):
   - Click the image area below "Bot Icon"
   - Default URL: `https://img.alicdn.com/imgextra/i4/O1CN01M0iyHF1FVNzM9qjC0_!!6000000000492-2-tps-254-254.png`
   - If URL, download locally first then upload
   - If image doesn't meet spec, pause and ask user to upload manually
5. Upload **Bot Message Preview Image** (user-specified or default):
   - Click the image area below "Bot Message Preview"
   - Default URL: `https://img.alicdn.com/imgextra/i4/O1CN01M0iyHF1FVNzM9qjC0_!!6000000000492-2-tps-254-254.png`
   - If URL, download locally first then upload
   - If image doesn't meet spec, pause and ask user to upload manually
6. Confirm message receiving mode is set to `Stream Mode`
7. Click **Publish** — a confirmation dialog will appear, confirm to publish. **You must publish the bot** before proceeding.

### Step 4: Create Version and Publish

1. Go to `App Publishing -> Version Management & Publishing`
2. Create a new version (required after every config change)
3. Fill in version description, set app visibility to all employees
4. Follow page prompts to complete publishing — a confirmation dialog will appear, confirm
5. Only after seeing a successful publish status should you proceed or tell the user it's active

### Step 5: Obtain Credentials

1. Go to `Basic Info -> Credentials & Basic Info`
2. Show the user where `Client ID` (AppKey) and `Client Secret` (AppSecret) are on the page. Do not modify them — guide the user to bind them manually.

## ProwlrBot Binding

After obtaining credentials, guide the user to choose one of these methods:

1. Console UI:
   - In ProwlrBot console, go to `Control -> Channels -> DingTalk`
   - Enter `Client ID` and `Client Secret`

2. Config file:

```json
"dingtalk": {
  "enabled": true,
  "bot_prefix": "[BOT]",
  "client_id": "Your Client ID",
  "client_secret": "Your Client Secret"
}
```

Path: `~/.prowlrbot/config.json`, under `channels.dingtalk`.

### Credential Delivery Requirements (Mandatory)

1. The agent only guides the user to the credentials page and displays `Client ID` and `Client Secret`.
2. The agent does NOT modify console config or `~/.prowlrbot/config.json` directly.
3. Must prompt the user to fill in credentials manually via one of:
   - Console UI: `Control -> Channels -> DingTalk`
   - Config file: edit `~/.prowlrbot/config.json` under `channels.dingtalk`

## Browser Tool Call Pattern

Default execution order:

1. `start` with `headed: true`
2. `open`
3. `snapshot`
4. `click` / `type` / `select_option` / `press_key` as needed
5. frequent `snapshot` after page transitions
6. `stop` when done

## Stability & Recovery Strategy

- Prefer using `ref` from the latest `snapshot`; only use `selector` when necessary.
- After each critical click or navigation, use a short `wait_for` and immediately re-`snapshot`.
- If the session expires or re-login is required mid-flow, pause again and wait for user login before continuing.
- If blocked by tenant permissions or admin approval, clearly describe the blocker and ask the user to complete that step manually before resuming.
