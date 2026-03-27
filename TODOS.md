# TODOS

## P2 — Growth (validate demand before building)

### Subscription / Continuous Re-crawl
**What:** Monthly fee to automatically re-score and re-optimize docs when the
source changes. Customer pays once, gets fresh optimized docs every month (or
on a trigger).

**Why:** Turns the $99 one-time transaction into MRR. Docs change frequently —
Stripe publishes multiple doc updates per week. The value proposition renews
itself.

**Pros:** Recurring revenue, high retention, compound value over time.
**Cons:** Requires a scheduler (APScheduler or Render cron), re-crawl pipeline,
email notifications, Stripe subscription setup.

**Context:** Deferred at CEO review 2026-03-25 pending customer demand signal.
First, observe whether customers return asking "can I get updated docs?" That's
the trigger to build this.

**Effort:** L (human: ~2 weeks / CC: ~1h) | **Priority:** P2
**Depends on:** Optimizer fix landing first (so re-runs produce quality output)

---

### Hosted Optimized Docs Endpoint
**What:** After optimization, serve the docs at a GrounDocs subdomain
(e.g. `docs.groundocs.com/stripe/`) — AI agents can retrieve them directly
via HTTP without the customer needing to download, unzip, and host a ZIP.
Includes a `llms.txt` index at the root.

**Why:** ZIP delivery is friction for the customer. A hosted endpoint is the
10x version — plug the URL into your LLM pipeline and you're done.

**Pros:** Premium tier justification, higher willingness to pay, reduces
customer activation friction.
**Cons:** Storage and CDN costs, subdomain/routing complexity, content
freshness (stale hosted docs if source changes and customer didn't subscribe).

**Context:** Deferred at CEO review 2026-03-25 pending demand signal.
Natural pairing with the subscription feature (host + refresh).

**Effort:** M (human: ~1 week / CC: ~30min) | **Priority:** P2
**Depends on:** Subscription / continuous re-crawl (hosting stale docs is
worse than no hosting)

---

## P3 — Quality / Tech Debt

### Add regression tests for optimizer page selection
After the optimizer fix lands, add unit tests for `_score_page_density`
and the two-queue BFS displacement logic. Current optimizer has no
automated test coverage for page selection behavior.

**Effort:** S | **Priority:** P3
