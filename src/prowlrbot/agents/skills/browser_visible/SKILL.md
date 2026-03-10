---
name: browser_visible
description: "When the user wants to open a real, visible browser window (not headless mode), use the browser_use headed parameter to launch the browser, then proceed with open/snapshot/click etc. Useful for demos, debugging, or when the user wants to see the page."
metadata:
  {
    "prowlr":
      {
        "emoji": "🖥️",
        "requires": {}
      }
  }
---

# Visible Browser (Real Window) Reference

By default, **browser_use** runs in headless mode in the background without showing a browser window. When the user explicitly wants to **open a real browser window**, **see the browser UI**, or have a **visible browser**, use this skill: first launch the browser in **headed** mode, then open pages and interact as needed.

## When to Use

- User says: "open a real browser", "open a visible browser", "I want to see the browser", "don't run in the background, I want to see the window"
- User wants to watch the page load, click, fill forms, etc. (demos, debugging, teaching)
- User needs to interact with a visible page (e.g. login, CAPTCHA, or other human-in-the-loop scenarios)

## Usage (browser_use)

1. **Launch browser in visible mode**
   Call **browser_use** with `action` set to `start` and pass **headed=true**:
   ```json
   {"action": "start", "headed": true}
   ```
   A real Chromium browser window will appear.

2. **Open pages and interact as needed**
   Same as headless mode, for example:
   - Open URL: `{"action": "open", "url": "https://example.com"}`
   - Get page structure: `{"action": "snapshot"}`
   - Click, type, etc.: use `ref` or `selector` for click, type actions

3. **Close the visible browser**
   When done: `{"action": "stop"}` to close the browser.

## Difference from Default (Headless) Mode

| Mode     | Launch Method                         | Shows Window |
|----------|---------------------------------------|--------------|
| Headless | `{"action": "start"}`                 | No (background) |
| Visible  | `{"action": "start", "headed": true}` | Yes (real window) |

## Notes

- If a browser is already running, you need to `stop` it first, then `start` again with `headed: true` to switch to visible mode.
- Visible mode requires a desktop/graphical environment. It may not work on servers without a display.
