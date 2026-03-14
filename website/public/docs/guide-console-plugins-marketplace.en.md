# Console Plugins from the Marketplace

This guide describes how **marketplace plugins can add tabs and new pages** to the ProwlrBot console, so features like War Room can be installable from the marketplace instead of (or in addition to) being built into core.

---

## Why War Room is separate today

Right now the console is **static**: routes and sidebar items are hardcoded in `MainLayout` and `Sidebar`. War Room is a first-class page because it was implemented as part of the core app. The marketplace today supports **skills**, **channels**, **agents**, **workflows**, etc.—packages that extend backend behavior and show up in Skills/MCP/Agents—but there is **no extension point for “add a new console tab/page.”**

To make “War Room as a plugin” (and any future UI feature) work from the marketplace, we need:

1. **A way for a listing to declare:** “I add a console tab” (path, label, icon, how to render).
2. **A backend API** that returns the list of **enabled console plugins** (from installed marketplace packages that have this declaration).
3. **Console wiring** that fetches that list and **dynamically adds** sidebar items and routes.

---

## Console plugin manifest

A marketplace listing can include an optional **console plugin** manifest. When the package is installed, the console will show an extra tab and route.

### In the listing (backend model)

```json
{
  "id": "warroom-official",
  "title": "War Room",
  "category": "integrations",
  "console_plugin": {
    "path": "/warroom",
    "label": "War Room",
    "icon": "Radio",
    "entry": "warroom"
  }
}
```

- **path** – URL path (e.g. `/warroom`). Must be unique.
- **label** – Text in the sidebar.
- **icon** – Lucide icon name (e.g. `Radio`, `LayoutDashboard`).
- **entry** – How to render the page:
  - **Built-in key** (e.g. `"warroom"`) – Maps to a known component the console already bundles (War Room, Monitoring, etc.). Lets “War Room” be installable from the marketplace while reusing the same code.
  - **URL** – Load the page in an iframe (e.g. `https://my-plugin.example.com` or a path the backend serves from the installed package).

### API: list enabled console plugins

- **`GET /api/console/plugins`** – Returns the list of console plugins from **installed** marketplace packages that have a `console_plugin` manifest. Each item includes `path`, `label`, `icon`, `entry`. The console uses this to build the sidebar and routes.

---

## How the console uses it

1. On load, the console calls `GET /api/console/plugins`.
2. **Sidebar** – For each plugin, append an item (path, label, icon). Plugins can be shown in a dedicated “Plugins” group or merged into existing groups.
3. **Routes** – For each plugin:
   - If `entry` is a **known key** (e.g. `warroom`), render the existing component (e.g. `WarRoomPage`).
   - If `entry` is a **URL**, render an iframe with that `src`.

So:

- **War Room as a marketplace plugin:** A listing “War Room” with `console_plugin: { path: "/warroom", label: "War Room", icon: "Radio", entry: "warroom" }`. When the user installs it, the console gets it from the plugins API and adds the tab; the existing War Room page component is used. Core can still ship War Room by default by treating it as a built-in plugin, or only show it when the package is installed.
- **Third-party tab:** A listing “My Dashboard” with `console_plugin: { path: "/my-dashboard", label: "My Dashboard", icon: "BarChart3", entry: "https://my-dashboard.example.com" }`. When installed, the console adds a tab that loads that URL in an iframe.

---

## Implementation status

- **Design and manifest shape** – Implemented: `ConsolePluginManifest` in `marketplace/models.py`; optional `console_plugin` on `MarketplaceListing`.
- **Backend** – `GET /api/console/plugins` in `app/routers/console_plugins.py`; returns built-in plugins (e.g. War Room) plus plugins from installed marketplace listings. Marketplace store has `get_console_plugins(user_id)`, migration for `console_plugin` column, and `console_plugin` in publish/update.
- **Frontend** – Console fetches `GET /api/console/plugins` in `MainLayout`; sidebar merges plugin items (from API) and routes are rendered from the plugin list (built-in `entry` keys map to existing pages; URL `entry` → iframe).
- **Marketplace listing** – Optional `console_plugin` field on listings; publishers can set it when creating/updating a listing so that when users install it, the console gains the new tab/page.

---

## Adding a new tab via the marketplace (publisher)

1. Create your package (skill, integration, or dedicated “console plugin” package) with a `manifest.json` (or backend listing payload) that includes:

   ```json
   "console_plugin": {
     "path": "/my-feature",
     "label": "My Feature",
     "icon": "Sparkles",
     "entry": "https://my-feature.example.com"
   }
   ```

2. Publish the listing to the marketplace (category e.g. `integrations` or a future `console_plugins`).
3. Users install the package from the marketplace (console or `prowlr market install`).
4. After install, the console shows “My Feature” in the sidebar and the route `/my-feature` (iframe to your URL).

To ship a **built-in-style** page (like War Room) as a plugin: use an `entry` that the console knows (e.g. `"warroom"`) and ensure the listing is either pre-installed or installed by default so the tab appears.

---

## Summary

- **Why War Room was separate:** The console had no plugin API for tabs/pages; everything was hardcoded.
- **How to do it from the marketplace:** Listings can declare a `console_plugin` (path, label, icon, entry). The backend exposes `GET /api/console/plugins` from installed packages. The console merges that into the sidebar and routes (built-in component or iframe). That way any marketplace plugin can add tabs and new pages.
