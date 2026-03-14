# Marketplace Guide

The ProwlrBot Marketplace is a community hub for sharing skills, channel adapters, agent blueprints, and workflow templates. Packages live in a GitHub registry and are indexed locally in `~/.prowlrbot/marketplace.db`.

For **tiers, credits, and payments** (free tier, Stripe, monthly grants), see [Tiers and Payments](tiers-and-payments.md).

---

## Browsing and installing

### Search

```bash
prowlr market search "slack notification"
prowlr market search "pdf tools" -c skills
prowlr market search "automation" --limit 50
prowlr market popular -l 10
prowlr market categories
```

Categories: `skills`, `channels`, `agents`, `workflows`, `prompts`, `integrations`, `blueprints`, `utilities`, `monitoring`, `analytics`.

### View details

```bash
prowlr market detail LISTING_ID
```

Shows title, author, version, license, downloads, rating, and recent reviews.

### Install

```bash
prowlr market install LISTING_ID
```

Free packages install immediately. Paid packages ask for confirmation.

Installed packages are stored in `~/.prowlrbot/marketplace/<listing_id>/manifest.json`.

### List installed packages

```bash
prowlr market list
```

---

## Keeping the registry current

The local registry syncs from [github.com/ProwlrBot/prowlr-marketplace](https://github.com/ProwlrBot/prowlrbot/prowlr-marketplace):

```bash
prowlr market update
prowlr market update --token $GITHUB_TOKEN   # higher rate limit
```

Without a token, GitHub's API allows 60 requests/hour. With a token: 5000/hour.

---

## Bundles

Bundles are curated collections of related packages:

```bash
prowlr market bundles
prowlr market install-bundle BUNDLE_ID
```

Seed the local DB with official launch bundles:

```bash
prowlr market seed
```

---

## Reviews and tips

```bash
# Leave a review
prowlr market review LISTING_ID --rating 5 --comment "Works great, saved me hours"
prowlr market review LISTING_ID -r 4

# Tip a developer
prowlr market tip LISTING_ID 2.50
prowlr market tip LISTING_ID 5.00 -m "Thanks for maintaining this skill!"
```

---

## Publishing a package

### What you can publish

- **Skills**: a directory with `SKILL.md`
- **Channels**: a Python module with a `BaseChannel` subclass
- **Blueprints**: pre-configured agent team setups
- **Workflows**: automation templates
- **Prompts**: system prompt collections

### Step 1: Prepare your package

Skills are the most common package type. Your directory needs at minimum:

```
my-skill/
└── SKILL.md    # frontmatter: name, description
```

Optional: add `manifest.json` with richer metadata:

```json
{
  "name": "my-skill",
  "title": "My Skill",
  "description": "What this skill does in one sentence",
  "version": "1.0.0",
  "author": "your-github-username",
  "license": "MIT",
  "tags": ["automation", "productivity"],
  "homepage": "https://github.com/your-org/my-skill"
}
```

### Step 2: Test locally

```bash
# Install locally first
cp -r my-skill ~/.prowlrbot/active_skills/
prowlr skills config  # enable it
# Test it in the console
prowlr app
# Chat: "use my-skill to..."
```

### Step 3: Publish

```bash
prowlr market publish ./my-skill -c skills --pricing free
```

For paid packages:

```bash
prowlr market publish ./my-skill -c skills \
  --pricing one_time \
  --price 4.99
```

Pricing models:
- `free`
- `one_time` — single purchase
- `subscription` — monthly recurring
- `usage_based` — per-use billing

Revenue split is **70/30** (you/platform) for paid listings. Requires a Pro or Team tier account.

### Step 4: Publish to GitHub (for the registry)

After local publish confirms the format is correct, push to a GitHub repo and submit a PR to [ProwlrBot/prowlr-marketplace](https://github.com/ProwlrBot/prowlr-marketplace):

1. Fork [github.com/ProwlrBot/prowlr-marketplace](https://github.com/ProwlrBot/prowlr-marketplace)
2. Add your package to the `listings/` directory
3. Open a PR — the maintainers review within a few days

---

## Credits and tiers

### Check your balance

```bash
prowlr market credits
```

### View tier comparison

```bash
prowlr market tiers
```

| Tier | Price | Credits/mo | Marketplace publish |
|------|-------|-----------|---------------------|
| Free | $0 | 50 | No |
| Starter | $5/mo | 500 | No |
| Pro | $15/mo | 2,000 | Yes (70/30 revenue split) |
| Team | $29/mo | 10,000 | Yes (priority review) |

### Upgrade

```bash
prowlr market upgrade pro
prowlr market upgrade team
```

### Buy credits

```bash
prowlr market buy-credits
```

Credit packs are available for one-time purchase separately from the subscription.

### Unlock premium content

Premium content (workflow templates, business specs, insight packs, agent blueprints) requires credits:

```bash
prowlr market unlock workflow_advanced_automation
prowlr market unlock blueprint_research_team
```

---

## Ecosystem repositories

```bash
prowlr market repos
```

Lists all official ProwlrBot GitHub repositories (marketplace, studio, doctor, ROAR protocol, etc.).

---

## Marketplace database

The local database lives at `~/.prowlrbot/marketplace.db` (SQLite). It stores:
- Listings cache (from registry sync)
- Install records
- Reviews you've left
- Tips you've sent
- Your credit balance and transaction history
- Bundles

This file is local only — it does not sync back to GitHub. Reviews and tips are stored locally until a proper backend API is available.
