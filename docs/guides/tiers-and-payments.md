# Tiers, Credits, and Payments

How to get **free tier**, **tiers**, and **payments** working in ProwlrBot.

---

## Free tier (no Stripe)

Free tier works out of the box:

1. **Credits**  
   The first time a user (e.g. `default`) is created, you can give them **welcome credits** so they can try the marketplace.  
   - Set `PROWLR_FREE_TIER_WELCOME_CREDITS=100` (or any positive number) before starting the app; new users will receive that many credits once.  
   - Omit it or set to `0` for no welcome grant (balance starts at 0).  
   - Balance is stored in `~/.prowlrbot/marketplace.db`.

2. **Console**  
   Open **Credits** in the console: balance and transaction history load from the API. No login required for read-only; use user id `default` for single-user.

3. **CLI**  
   ```bash
   prowlr market credits --user default   # show balance and tier
   prowlr market tiers                    # list tier features
   ```

4. **Monthly grants (optional)**  
   Free tier gets **100 credits/month** (see `PRO_TIER_LIMITS` in code). To grant them on a schedule, call the API (e.g. from cron):

   ```bash
   curl -X POST "http://localhost:8088/api/marketplace/credits/default/grant-monthly"
   ```

   Or use a cron job that runs daily; the endpoint is idempotent (grants at most once per 30 days per user).

---

## Paid tiers and Stripe

For **Pro** / **Team** subscriptions and real payments:

1. **Stripe account**  
   Create one at [stripe.com](https://stripe.com) and get:
   - **Secret key** (Dashboard → Developers → API keys): `sk_test_...` or `sk_live_...`
   - **Webhook signing secret** (Dashboard → Developers → Webhooks): `whsec_...`

2. **Environment variables**  
   Set before starting the app:

   ```bash
   export STRIPE_SECRET_KEY=sk_test_...
   export STRIPE_WEBHOOK_SECRET=whsec_...
   ```

   (Or put them in `~/.prowlrbot/.env` if your app loads it.)

3. **Webhook endpoint**  
   In Stripe Dashboard → Webhooks, add an endpoint:
   - **URL**: `https://your-domain.com/api/marketplace/webhook/stripe`  
     (for local dev you can use [Stripe CLI](https://stripe.com/docs/stripe-cli) to forward:  
     `stripe listen --forward-to localhost:8088/api/marketplace/webhook/stripe`)
   - **Events**: `checkout.session.completed`, `customer.subscription.created`, `invoice.payment_succeeded`

4. **Dependency**  
   Install the Stripe SDK:

   ```bash
   pip install stripe
   ```

5. **Console upgrade**  
   When Stripe is configured, **Credits → Upgrade to Pro/Team** opens Stripe Checkout. After payment, Stripe sends events to the webhook; the app awards credits and updates tier.

---

## When Stripe is not configured

- **Subscribe API** returns `200` with `checkout_url: null` and a `message` (e.g. “Stripe not configured. Set STRIPE_SECRET_KEY…” or use CLI).
- **Console** does not redirect; you can still use the CLI to change tier locally (see below).

---

## Local tier changes (no payment)

For development or self-hosted use without Stripe:

```bash
# Tier name is case-insensitive (Starter, starter, STARTER); grants monthly credits, no charge
prowlr market upgrade starter --user default   # $5/mo tier
prowlr market upgrade pro --user default      # $15/mo tier
prowlr market upgrade team --user default     # $29/mo tier
```

This updates the user’s tier and grants that tier’s monthly credits once. It does **not** set up recurring billing; use Stripe for that.

**When Stripe is configured**, the CLI upgrade command is **disabled** by default so only real payments (console → Stripe Checkout) can grant paid tiers. To allow CLI upgrade anyway (e.g. in dev): `prowlr market upgrade starter --allow-local` or `export PROWLR_ALLOW_LOCAL_UPGRADE=1`.

---

## Summary

| Goal                    | What to do |
|-------------------------|------------|
| Free tier working       | Nothing. New users get welcome credits; use console or `prowlr market credits`. |
| Monthly free credits    | Call `POST /api/marketplace/credits/{user_id}/grant-monthly` (e.g. from cron). |
| Paid subscriptions      | Set `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, add webhook, `pip install stripe`. |
| No Stripe, “paid” tier  | Use `prowlr market upgrade <tier> --user default` for local tier + one-time credits. |
