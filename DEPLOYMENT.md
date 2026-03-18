---
title: "Deploy AgentReadiness to Production"
description: "Step-by-step guide to deploy AgentReadiness on Render with GitHub auto-deploy"
version: "0.3.0"
last_updated: "2026-03-18"
tags: ["deployment", "render", "production", "stripe", "openai"]
prerequisites: ["GitHub account with the repository", "Render account", "OpenAI API key", "Stripe account with API keys"]
---

# Deploy AgentReadiness to Production

> AgentReadiness deploys to Render via GitHub push. Push to `main` → Render auto-deploys both frontend and backend. No manual steps after initial setup.

**Live URL:** https://agentreadiness-web.onrender.com/

## Prerequisites

Before deploying, ensure you have:

- [ ] The code pushed to GitHub at `carlos-ferrer-fernandez/agentreadiness`
- [ ] A Render account ([create one here](https://render.com)) — sign up with GitHub
- [ ] An OpenAI API key ([get one here](https://platform.openai.com/api-keys))
- [ ] A Stripe account ([create one here](https://stripe.com)) with API keys

## Step 1: Set Up Render Services

### Create the API service

1. Go to https://dashboard.render.com/new/web-service
2. Connect the `carlos-ferrer-fernandez/agentreadiness` GitHub repository
3. Configure the service:

| Setting | Value |
|---------|-------|
| Name | `agentreadiness-api` |
| Root Directory | `apps/api` |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

### Create the frontend service

1. Go to https://dashboard.render.com/new/static-site
2. Connect the same repository
3. Configure the service:

| Setting | Value |
|---------|-------|
| Name | `agentreadiness-web` |
| Root Directory | `apps/web` |
| Build Command | `npm install && npm run build` |
| Publish Directory | `dist` |

## Step 2: Set Environment Variables

Add these environment variables to the **API service** on Render:

| Variable | Value | Where to Get It |
|----------|-------|-----------------|
| `OPENAI_API_KEY` | `sk-...` | [OpenAI API Keys](https://platform.openai.com/api-keys) |
| `STRIPE_SECRET_KEY` | `sk_test_...` | [Stripe Dashboard → API Keys](https://dashboard.stripe.com/test/apikeys) |
| `STRIPE_PUBLISHABLE_KEY` | `pk_test_...` | [Stripe Dashboard → API Keys](https://dashboard.stripe.com/test/apikeys) |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` | [Stripe Dashboard → Webhooks](https://dashboard.stripe.com/test/webhooks) |
| `JWT_SECRET` | Any random 32+ character string | Generate with `openssl rand -hex 32` |
| `DATABASE_URL` | Render PostgreSQL URL | Create a Render PostgreSQL instance |
| `ALLOWED_ORIGINS` | `https://agentreadiness-web.onrender.com` | Your frontend URL |

Add this environment variable to the **frontend service** on Render:

| Variable | Value |
|----------|-------|
| `VITE_API_URL` | `https://agentreadiness-api.onrender.com` |

> **ℹ️ Info:** No Stripe products or prices need to be created. Pricing is dynamic — the app calculates the price based on documentation size and uses Stripe's `price_data` at checkout time.

## Step 3: Deploy

Push to the `main` branch:

```bash
git push origin main
```

Expected result: Render automatically builds and deploys both services within 3-5 minutes.

## Step 4: Verify the Deployment

| Check | URL | Expected Result |
|-------|-----|-----------------|
| Frontend loads | https://agentreadiness-web.onrender.com | Landing page with assessment form and 20-rule showcase |
| API health check | https://agentreadiness-api.onrender.com/health | `{"status": "healthy"}` |
| Assessment works | Enter any docs URL (e.g., `docs.stripe.com`) | Score, grade, and 20-rule breakdown returned in ~60 seconds |
| Stripe checkout | Click "Get Optimized Docs" after assessment | Redirects to Stripe checkout page |

## Set Up Stripe Webhooks

To receive payment confirmations, configure a Stripe webhook:

1. Go to [Stripe Dashboard → Webhooks](https://dashboard.stripe.com/test/webhooks)
2. Click "Add endpoint"
3. Set the endpoint URL to: `https://agentreadiness-api.onrender.com/api/payments/webhook`
4. Select events: `checkout.session.completed`
5. Copy the webhook signing secret (`whsec_...`)
6. Add it as `STRIPE_WEBHOOK_SECRET` in Render environment variables

## Switch to Live Payments

When ready to accept real payments:

1. Toggle Stripe Dashboard from "Test mode" to "Live mode"
2. Get live API keys (they start with `sk_live_` and `pk_live_`)
3. Update the `STRIPE_SECRET_KEY` and `STRIPE_PUBLISHABLE_KEY` environment variables on Render
4. Create a new webhook endpoint for the live environment
5. Update `STRIPE_WEBHOOK_SECRET` with the live webhook secret
6. Redeploy

> **⚠️ Warning:** Test a real payment with a small amount before announcing to customers. Verify that the payment appears in your Stripe Dashboard and that the optimized docs are generated and downloadable.

## Troubleshooting

### Build fails on Render

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `tsc` type errors | TypeScript compilation failure | Check CI locally with `cd apps/web && npx tsc --noEmit` |
| `ModuleNotFoundError` | Missing Python dependency | Add the package to `apps/api/requirements.txt` |
| `npm ERR!` | Node dependency issue | Delete `package-lock.json` and rebuild |

### Assessment never finishes

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Spinner runs forever | `OPENAI_API_KEY` not set or invalid | Check Render env vars |
| 500 error on analyze | OpenAI account has no credit | Add credit at https://platform.openai.com/account/billing |
| Timeout | Documentation site blocks crawling | Check if the target URL returns content |

### Payment flow broken

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Checkout page doesn't load | `STRIPE_SECRET_KEY` not set or invalid | Check Render env vars |
| Payment succeeds but no download | `STRIPE_WEBHOOK_SECRET` missing or wrong | Re-create webhook in Stripe Dashboard |
| "Payment failed" error | Using test card in live mode | Use a real card in live mode, or switch to test mode |

## Monthly Cost Estimate

| Service | Cost | Notes |
|---------|------|-------|
| Render (API + Frontend) | $0–25/month | Free tier available for low traffic |
| Render PostgreSQL | $0–7/month | Free tier: 1GB, 90-day retention |
| OpenAI API | $1–50/month | Depends on number of assessments and optimizations |
| Stripe | 2.9% + €0.30 per transaction | Only charged when customers pay |
| Domain (optional) | $10–15/year | Custom domain like agentreadiness.dev |

**Estimated total for a side project:** €20–50/month at low volume.
