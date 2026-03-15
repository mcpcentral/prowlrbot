# Sign-up, credits, and workspace (website vs app)

How “anybody” can get an account, where credits live, and the difference between **your website**, **your app**, and **local**.

---

## Two different “sites”

| What | URL (example) | Auth | Purpose |
|------|----------------|------|--------|
| **Website** | prowlrbot.com | Clerk (Sign in / Sign up) | Marketing, docs, pricing. When Clerk is also used on the app, the same account works everywhere. |
| **App (console)** | app.prowlrbot.com | Clerk (if configured) or app login (username/password or OAuth) | Dashboard, chat, workspace, credits, War Room. **Credits and workspace live here.** With Clerk on all three, one sign-in covers site + app. |

So: **can anybody go to my site and sign up and gain credits?**  
- If **Clerk is on all three**: signing up on the website or the app gives one account; the backend creates an app user on first sign-in and grants **welcome credits** (if `PROWLR_FREE_TIER_WELCOME_CREDITS` is set).  
- If only **legacy app login** is used: they must sign up on **app.prowlrbot.com** to get an app account and credits.

To let “anybody” sign up and get credits, they need to use the **app** (e.g. “Log in” / “Sign up” on app.prowlrbot.com), not only the website. You can add a clear “Open console” or “Sign in to app” link on the website that points to `https://app.prowlrbot.com` (or your app URL).

---

## One auth across the whole studio (Clerk on all three)

**One auth** is used across the whole product: **website**, **console**, and **backend** all use Clerk when configured.

| Part | Role |
|------|------|
| **Website** | Clerk sign-in/sign-up (marketing, nav). Same Clerk application as console. |
| **Console** | When `VITE_CLERK_PUBLISHABLE_KEY` is set, the console shows Clerk Sign In and sends the Clerk session JWT on API requests. |
| **Backend** | When `CLERK_JWKS_URL` is set, the API verifies Clerk JWTs and maps Clerk user id → app user (created on first sign-in). Credits and workspace use that app user. |

**Setup:** Use the **same Clerk application** for website and console. Set:

- **Website:** `VITE_CLERK_PUBLISHABLE_KEY` (already used).
- **Console:** `VITE_CLERK_PUBLISHABLE_KEY` (same value).
- **Backend:** `CLERK_JWKS_URL` = your Clerk JWKS URL (e.g. Frontend API URL + `/.well-known/jwks.json`). Optionally `CLERK_AUTHORIZED_PARTIES` (comma-separated allowed origins for the `azp` claim).

If you omit Clerk on the console or backend, the console falls back to **legacy app login** (username/password and optional OAuth) and the backend continues to accept legacy JWTs. So you can enable Clerk on all three for one account everywhere, or keep legacy auth on the app only.

---

## Do they get their own workspace?

**No.** The app has **one workspace per deployment** (one server = one `WORKING_DIR`, e.g. `/data/.prowlrbot`). All users who log in to that app instance see and use the **same** workspace (same Core Files, AGENTS.md, etc.). Credits are **per user**; workspace is **shared** for the instance.

So today:
- **Multiple users** → each has their own **account** and **credit balance**.
- **One workspace** → shared by everyone on that app instance.

If you later want one workspace per user, that would require backend changes (e.g. workspace path or API scoped by `user_id`).

---

## Local vs “my site” (hosted app)

| | **Local** | **Your site (app.prowlrbot.com)** |
|--|-----------|------------------------------------|
| **What** | You run `prowlr app` on your machine | One deployed instance (e.g. Fly) |
| **Workspace** | One: your machine’s `.prowlrbot` dir (e.g. `~/.prowlrbot`) | One: server’s `WORKING_DIR` (e.g. `/data/.prowlrbot`) |
| **Users** | You (and anyone with access to that machine). First user from `PROWLRBOT_ADMIN_*`. | Anyone who registers on the app (or you create). |
| **Credits** | Stored in `~/.prowlrbot/marketplace.db` (local). Welcome credits for new users if `PROWLR_FREE_TIER_WELCOME_CREDITS` is set. | Same logic, but DB lives on the server. Stripe for paid tiers if configured. |
| **Auth** | Same app login (username/password or OAuth). | Same. No Clerk on the app; Clerk is only on the website. |

So:
- **Local** = your own ProwlrBot instance on your computer; one workspace, your (or your team’s) users and credits.
- **Your site** = your ProwlrBot instance in the cloud; one workspace, anyone who signs up on the app gets an account and (optionally) welcome credits.

---

## Summary

| Question | Answer |
|----------|--------|
| Can anybody sign up and get credits? | Yes, if they sign up on the **app** (app.prowlrbot.com), not only the website. Set `PROWLR_FREE_TIER_WELCOME_CREDITS` so new app users get welcome credits. |
| Do they get their own workspace? | No. One workspace per app instance; all app users share it. Credits are per user. |
| Website vs app? | Website = marketing + Clerk. App = console, credits, workspace; has its own login/register. **Recommended:** one auth (e.g. Clerk) for both so one account works everywhere. |
| Local vs site? | Local = one instance on your machine. Site = one instance in the cloud; multiple users can register and use the same workspace and their own credits. |
