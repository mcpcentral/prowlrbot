# Marketplace Repo Upgrade: Tiers, Credits & Console Plugins

This guide helps you upgrade the **prowlr-marketplace** repo (or any marketplace registry that syncs into ProwlrBot) to support **tiers**, **credits**, and **console plugins** (listings that add tabs/pages in the console).

---

## 1. Tiers (subscription plans)

Tiers are defined in the **main ProwlrBot app** (`prowlrbot`), not in the marketplace repo. The app exposes:

- **`GET /api/marketplace/tiers`** — returns free / pro / team (and any custom tiers you add).
- **`POST /api/marketplace/subscribe/{tier_id}`** — creates a Stripe Checkout session for that tier.

**Current tiers (in prowlrbot):**

| Tier  | Price   | Credits/mo | Features (summary) |
|-------|---------|------------|--------------------|
| free  | $0      | 1,000      | 1 agent, basic monitoring, **14-day Pro trial** |
| pro   | $19/mo  | 10,000     | 5 agents, advanced monitoring, API, **Console plugins** |
| team  | $49/mo  | 50,000     | Unlimited agents, **War Room**, **Console plugins**, team, SLA |

New Pro/Team subscriptions get a 14-day free trial (no charge until trial ends).

**What you can do in the marketplace repo:**

- In your **marketing or README**, describe which tier is required for paid installs or for “Console plugins” (add tabs). The app already shows “Console plugins (add tabs & pages)” under the Team tier.
- If you run a **fork** of the app, you can add more tiers or change feature lists in `src/prowlrbot/app/routers/marketplace.py` (`get_tiers()` and `_TIER_CONFIG`).

---

## 2. Credits

Credits are stored and managed in the **main app** (marketplace store + Stripe webhook).

- **Earning:** Monthly grant (by tier), publish bonus, download milestone, review bonus, tips, etc.
- **Spending:** `listing_purchase` (paid installs), `unlock/{content_key}` (premium content).

**API (all under `/api/marketplace/`):**

- `GET /credits/{user_id}` — balance
- `GET /credits/{user_id}/transactions` — history
- `POST /credits/{user_id}/add` — admin/add credits
- `POST /credits/{user_id}/spend` — spend (e.g. on install)
- `POST /credits/{user_id}/unlock/{content_key}` — unlock premium content by key

**Implementing paid installs (credits):**

1. In the **app**, when a user installs a **paid** listing, call `spend_credits(user_id, listing.price, transaction_type="listing_purchase", reference_id=listing_id)` (and only complete install if spend succeeds).
2. In the **marketplace repo**, set `pricing_model` and `price` on listings that cost credits (see below).

**What you can do in the marketplace repo:**

- Set `pricing_model` and `price` on listings so the app knows which installs cost credits.
- Optionally document “Paid listings cost X credits” in your README or listing copy.

---

## 3. Console plugins (add tabs/pages)

A listing can declare a **console plugin** so that when it’s installed, the ProwlrBot console gets a new tab and route.

### In the marketplace repo (index.json or manifest.json)

Add a `console_plugin` object to the listing. It can live in:

- **index.json** — per-listing entry, or
- **manifest.json** inside the listing directory (e.g. `skills/warroom-official/manifest.json`).

**Shape:**

```json
{
  "console_plugin": {
    "path": "/warroom",
    "label": "War Room",
    "icon": "Radio",
    "entry": "warroom"
  }
}
```

- **path** — URL path in the console (e.g. `/warroom`, `/my-dashboard`). Must be unique.
- **label** — Sidebar text.
- **icon** — Lucide icon name (e.g. `Radio`, `BarChart3`, `Plug`).
- **entry** — How to render:
  - **Built-in key** (e.g. `"warroom"`) — maps to a component the app already bundles.
  - **URL** — full URL; the console will show it in an iframe.

### Example: listing that adds a tab

**index.json** (one entry in the `listings` array):

```json
{
  "id": "warroom-official",
  "title": "War Room",
  "description": "Multi-agent mission board and live feed.",
  "category": "integrations",
  "version": "1.0.0",
  "author": "ProwlrBot",
  "tags": ["war-room", "agents", "collaboration"],
  "pricing_model": "free",
  "console_plugin": {
    "path": "/warroom",
    "label": "War Room",
    "icon": "Radio",
    "entry": "warroom"
  }
}
```

**Or in a per-listing manifest.json** (e.g. `integrations/warroom-official/manifest.json`):

```json
{
  "id": "warroom-official",
  "name": "War Room",
  "version": "1.0.0",
  "description": "Multi-agent mission board and live feed.",
  "category": "integrations",
  "author": "ProwlrBot",
  "tags": ["war-room", "agents", "collaboration"],
  "pricing_model": "free",
  "price": 0,
  "console_plugin": {
    "path": "/warroom",
    "label": "War Room",
    "icon": "Radio",
    "entry": "warroom"
  }
}
```

When the main app **syncs** the registry (`prowlr market update` or sync from GitHub), it will read `console_plugin` and store it. When a user has the listing **installed**, `GET /api/console/plugins` will include it and the console will show the tab and route.

### Paid console plugin (credits)

To make a console plugin **paid** (user spends credits to install):

1. In the marketplace repo, set the listing to a paid model and a price in credits, e.g.:
   ```json
   "pricing_model": "one_time",
   "price": 50
   ```
2. In the main app, the install flow should:
   - Check the user’s credit balance.
   - Call `spend_credits(user_id, listing.price, "listing_purchase", listing_id)`.
   - If success, record the install and then the console will show the plugin.

The marketplace repo only defines **what** the listing is (price, console_plugin); the **prowlrbot** app implements the actual credit spend and install recording.

---

## 4. Tips for developers

### Let users tip you (listing authors)

Users can send **tips** to the author of a listing. The app supports this out of the box:

- **`POST /api/marketplace/listings/{listing_id}/tip`** — body: `{ "amount": 5.00, "message": "Thanks for the skill!" }`.
  - If Stripe is configured: returns a `checkout_url`; after payment, the webhook records the tip and the author’s listing stats reflect it.
  - If Stripe is not configured: the tip is recorded locally and no payment is taken.

Listing detail responses include **`tip_total`** (total tips received by that listing’s author), so you can show “Support this dev” or “Tip the author” in the console or docs and link to the tip flow.

**In the marketplace repo:** no change needed. Tip handling lives in the app. You can mention in your listing description or README that users can tip via the console or API.

### Publishing tips

- **Stable IDs:** Use a fixed, URL-friendly `id` for each listing (e.g. `warroom-official`, `my-skill-name`). Don’t change it after publish or you break installs and console plugin routes.
- **Console plugin paths:** Every `console_plugin.path` must be **unique** across all installed listings. Prefer a short, namespaced path (e.g. `/warroom`, `/mycompany-dashboard`).
- **Price in credits:** For paid listings, `price` is in **credits** (integer). Set `pricing_model` to `one_time` (or `subscription` / `usage_based` if the app supports it) and `price` to the credit cost.
- **Sync after changes:** After editing `index.json` or a listing’s `manifest.json`, run registry sync in the app (`prowlr market update` or your admin sync) so new/updated listings and `console_plugin` appear.

### Testing credits and paid installs

- Use **`POST /api/marketplace/credits/{user_id}/add`** to give a test user credits, then install a paid listing and confirm balance decreases and the install succeeds.
- A **402** response on install means insufficient credits; the body includes `balance`, `required`, and `code: "insufficient_credits"`.

---

## 5. Checklist for upgrading the marketplace repo

- [ ] **Tiers:** No change required in the repo; tiers live in the app. Optionally document “Console plugins” under Team tier in your README.
- [ ] **Credits:** For paid listings, set `pricing_model` and `price` in each listing (in index.json or manifest.json). Ensure the app’s install flow spends credits for paid installs.
- [ ] **Console plugins:** For any listing that should add a tab:
  - Add `console_plugin` with `path`, `label`, `icon`, `entry` (built-in key or URL).
  - Ensure the listing is included in the registry sync (index.json or discovered manifest).
- [ ] **Sync:** After updating the marketplace repo, run registry sync in the app (e.g. `prowlr market update` or your admin sync) so new/updated listings and `console_plugin` appear.

---

## 6. Reference: where things live

| Concern            | Where it lives |
|--------------------|----------------|
| Tier definitions   | prowlrbot: `app/routers/marketplace.py` (`get_tiers`, `_TIER_CONFIG`) |
| Stripe subscribe   | prowlrbot: `POST /api/marketplace/subscribe/{tier_id}` |
| Credits balance    | prowlrbot: marketplace store + `GET/POST /api/marketplace/credits/...` |
| Tips (support devs)| prowlrbot: `POST /api/marketplace/listings/{listing_id}/tip` (Stripe checkout or local); listing response includes `tip_total` |
| Console plugin list| prowlrbot: `GET /api/console/plugins` (built-ins + installed with `console_plugin`) |
| Listing data       | **prowlr-marketplace repo:** index.json + per-listing manifest.json |
| console_plugin     | **prowlr-marketplace repo:** inside each listing object in index or manifest |
| Sync               | prowlrbot: `marketplace/registry.py` `sync_registry()` reads repo and upserts listings (including `console_plugin`) |
