"""
Seed Example Agent Pages

Pre-built showcase pages for Stripe, Vercel, Notion, and Slack.
Uses the compact agent operating guide schema.
"""

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import AgentPage
from services.agent_page_generator import render_agent_page_html

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Stripe
# ---------------------------------------------------------------------------

STRIPE_EXAMPLE = {
    "meta": {
        "product_name": "Stripe",
        "slug": "stripe",
        "mode": "full",
        "docs_root_url": "https://docs.stripe.com"
    },
    "hero": {
        "summary": "Payment processing APIs for charges, subscriptions, refunds, and financial workflows.",
        "high_risk_notice": "Live-mode API keys process real money. Never use live keys in test workflows."
    },
    "agent_scope": {
        "safe_without_approval": [
            {"action": "Retrieve payment or customer details", "risk_level": "safe_read"},
            {"action": "List invoices or subscriptions", "risk_level": "safe_read"},
            {"action": "Check balance and payout history", "risk_level": "safe_read"},
            {"action": "Create test-mode payment intent", "risk_level": "safe_write"}
        ],
        "requires_confirmation": [
            {"action": "Issue a refund", "risk_level": "requires_confirmation", "confirm_what": ["Charge ID", "Amount", "Full or partial"]},
            {"action": "Cancel a subscription", "risk_level": "requires_confirmation", "confirm_what": ["Subscription ID", "Immediate or at period end"]},
            {"action": "Create live-mode payment", "risk_level": "requires_confirmation", "confirm_what": ["Amount", "Currency", "Customer"]},
            {"action": "Create or modify subscription", "risk_level": "requires_confirmation", "confirm_what": ["Price ID", "Customer ID"]}
        ],
        "requires_escalation": [
            {"action": "Change payout schedule or bank account", "risk_level": "requires_escalation"},
            {"action": "Modify API keys or webhook endpoints", "risk_level": "requires_escalation"},
            {"action": "Delete a customer record", "risk_level": "requires_escalation"}
        ],
        "never_do": [
            "Expose secret keys in client code",
            "Use live keys in test environments",
            "Store or log raw card numbers",
            "Refund without operator confirmation",
            "Retry failed payment without diagnosis"
        ]
    },
    "stop_conditions": {
        "stop_and_ask": [
            "Charge vs subscription intent is ambiguous",
            "No currency specified for payment",
            "Refund reason is unclear",
            "Amount seems unusually large",
            "Test vs live mode is uncertain"
        ],
        "stop_and_escalate": [
            "Customer disputes a charge amount",
            "Failure flagged as fraudulent by Radar",
            "Payout or bank account changes requested",
            "API key creation or revocation needed",
            "Bulk operations affecting many customers"
        ]
    },
    "task_playbooks": [
        {
            "task_name": "Accept a Payment",
            "goal": "Charge a customer using a PaymentIntent",
            "risk_level": "requires_confirmation",
            "ask_for": ["Amount in smallest unit", "Currency code", "Payment method types"],
            "check": ["Correct mode (test vs live)", "Amount is positive integer", "Currency is supported"],
            "do": [
                "Create PaymentIntent with amount and currency",
                "Return client_secret to frontend",
                "Client confirms via stripe.confirmCardPayment()",
                "Listen for payment_intent.succeeded webhook"
            ],
            "verify": ["Status is 'succeeded'", "Webhook received", "No duplicate charges"],
            "confirm_before": ["Creating in live mode"],
            "escalate_if": ["Customer disputes amount", "Unusually large payment"],
            "refs": [
                {"label": "Payment Intents API", "url": "https://docs.stripe.com/api/payment_intents"},
                {"label": "Accept a Payment", "url": "https://docs.stripe.com/payments/accept-a-payment"}
            ]
        },
        {
            "task_name": "Create a Subscription",
            "goal": "Set up recurring billing with a specific price plan",
            "risk_level": "requires_confirmation",
            "ask_for": ["Customer ID with payment method", "Price ID for the plan"],
            "check": ["Customer has valid payment method", "Price ID matches intended plan", "No existing active subscription"],
            "do": [
                "Retrieve or create Customer with payment method",
                "Create Subscription with customer and price",
                "Handle invoice.payment_succeeded webhook",
                "Handle subscription lifecycle webhooks"
            ],
            "verify": ["Status is 'active' or 'trialing'", "First invoice is 'paid'"],
            "confirm_before": ["Creating any live-mode subscription", "Changing subscription price"],
            "escalate_if": ["Customer requests custom plan", "Multi-year commitment"],
            "refs": [
                {"label": "Subscriptions API", "url": "https://docs.stripe.com/api/subscriptions"},
                {"label": "Billing Quickstart", "url": "https://docs.stripe.com/billing/quickstart"}
            ]
        },
        {
            "task_name": "Issue a Refund",
            "goal": "Return funds for a previous charge",
            "risk_level": "requires_confirmation",
            "ask_for": ["Charge or PaymentIntent ID"],
            "check": ["Charge exists and succeeded", "Check previous partial refunds", "Calculate refundable amount"],
            "do": [
                "Retrieve charge to verify amount",
                "Confirm refund details with operator",
                "Create Refund with charge and amount",
                "Handle charge.refunded webhook"
            ],
            "verify": ["Refund status is 'succeeded'", "amount_refunded is correct"],
            "confirm_before": ["Always \u2014 refunds move real money"],
            "escalate_if": ["Refund exceeds business threshold", "Charge has active dispute"],
            "refs": [
                {"label": "Refunds API", "url": "https://docs.stripe.com/api/refunds"},
                {"label": "Refund Guide", "url": "https://docs.stripe.com/refunds"}
            ]
        },
        {
            "task_name": "Investigate Failed Payment",
            "goal": "Diagnose why a payment failed and determine next steps",
            "risk_level": "safe_read",
            "ask_for": ["PaymentIntent or Invoice ID"],
            "check": ["Retrieve status", "Check if failure is latest attempt"],
            "do": [
                "Retrieve PaymentIntent with expanded latest_charge",
                "Examine last_payment_error for decline code",
                "Check outcome.reason and risk_level",
                "Determine recovery action from decline code"
            ],
            "verify": ["Root cause identified", "Recovery action matches failure type"],
            "confirm_before": [],
            "escalate_if": ["Flagged as fraudulent by Radar", "Multiple customers report same failure"],
            "refs": [
                {"label": "Decline Codes", "url": "https://docs.stripe.com/declines/codes"},
                {"label": "Payment Intents API", "url": "https://docs.stripe.com/api/payment_intents"}
            ]
        },
        {
            "task_name": "Handle Webhooks",
            "goal": "Process Stripe webhook events safely and idempotently",
            "risk_level": "safe_write",
            "ask_for": ["HTTPS endpoint URL", "Event types to subscribe"],
            "check": ["Endpoint is HTTPS", "Responds with 2xx promptly", "Signing secret available"],
            "do": [
                "Register endpoint with URL and events",
                "Store signing secret securely",
                "Verify signatures on all events",
                "Respond 200 immediately, process async"
            ],
            "verify": ["Endpoint shows 'enabled'", "Test events received", "Signatures pass"],
            "confirm_before": [],
            "escalate_if": ["Endpoint disabled from repeated failures", "Suspected replay attack"],
            "refs": [
                {"label": "Webhooks Overview", "url": "https://docs.stripe.com/webhooks"},
                {"label": "Webhook Signatures", "url": "https://docs.stripe.com/webhooks/signatures"}
            ]
        }
    ],
    "operating_rules": {
        "always": [
            "Use idempotency keys on POST requests",
            "Verify webhook signatures",
            "Use test-mode keys in development",
            "Store API keys in env vars only",
            "Use smallest currency unit for amounts"
        ],
        "never": [
            "Expose secret keys in client code",
            "Use live keys in test environments",
            "Store or log raw card numbers",
            "Refund without confirming with operator",
            "Retry failed payment without diagnosis"
        ],
        "environment": [
            "Test mode: sk_test_ keys and test cards",
            "Live mode: sk_live_ keys, real money",
            "Webhooks must use HTTPS in production"
        ]
    },
    "setup": {
        "prerequisites": [
            "Stripe account (dashboard.stripe.com)",
            "API keys from Dashboard (test and live)",
            "HTTPS endpoint for production webhooks"
        ],
        "auth_methods": [
            "Secret key in Authorization: Bearer header",
            "Restricted keys with per-resource permissions",
            "Publishable key (pk_) for client-side only"
        ],
        "required_secrets": [
            "STRIPE_SECRET_KEY (sk_test_ or sk_live_)",
            "STRIPE_WEBHOOK_SECRET (whsec_)",
            "STRIPE_PUBLISHABLE_KEY (pk_)"
        ],
        "env_notes": [
            "Test and live keys are completely separate",
            "Webhook secrets are per-endpoint",
            "API version via Stripe-Version header"
        ]
    },
    "decision_guide": [
        {
            "decision": "PaymentIntent vs Checkout Sessions",
            "use_when": ["Need full UI control", "Custom checkout form"],
            "avoid_when": ["Pre-built checkout is faster", "PCI scope is a concern"],
            "escalate_if": ["Unclear regulatory requirements"]
        },
        {
            "decision": "Immediate vs end-of-period cancellation",
            "use_when": ["Customer requests immediate", "Subscription created in error"],
            "avoid_when": ["Customer prepaid for current period"],
            "escalate_if": ["Customer wants cancellation AND full refund"]
        },
        {
            "decision": "Full vs partial refund",
            "use_when": ["Full: entire order returned", "Partial: price adjustment"],
            "avoid_when": ["Credit or coupon is more appropriate", "Charge has active dispute"],
            "escalate_if": ["Refund exceeds business threshold"]
        }
    ],
    "troubleshooting": [
        {
            "issue": "Card declined",
            "likely_cause": "Insufficient funds, lost card, or issuer decline",
            "fix": "Check decline_code, ask customer to try different method",
            "escalate_if": "Multiple customers hit same decline, or flagged fraudulent"
        },
        {
            "issue": "Webhook signature verification fails",
            "likely_cause": "Wrong signing secret (test vs live) or body parsed before verification",
            "fix": "Verify secret matches Dashboard, use raw request body",
            "escalate_if": "Verification fails for all events"
        },
        {
            "issue": "Subscription stuck in incomplete",
            "likely_cause": "Initial payment failed or 3DS not completed",
            "fix": "Check latest_invoice payment_intent for failure details",
            "escalate_if": "Multiple subscriptions stuck across customers"
        }
    ],
    "references": [
        {"label": "Payment Intents API", "url": "https://docs.stripe.com/api/payment_intents", "topic": "Payments"},
        {"label": "Accept a Payment", "url": "https://docs.stripe.com/payments/accept-a-payment", "topic": "Payments"},
        {"label": "Testing", "url": "https://docs.stripe.com/testing", "topic": "Payments"},
        {"label": "Subscriptions API", "url": "https://docs.stripe.com/api/subscriptions", "topic": "Billing"},
        {"label": "Billing Quickstart", "url": "https://docs.stripe.com/billing/quickstart", "topic": "Billing"},
        {"label": "Webhooks Overview", "url": "https://docs.stripe.com/webhooks", "topic": "Webhooks"},
        {"label": "Event Types", "url": "https://docs.stripe.com/api/events/types", "topic": "Webhooks"},
        {"label": "Stripe CLI", "url": "https://docs.stripe.com/stripe-cli", "topic": "Webhooks"}
    ]
}

# ---------------------------------------------------------------------------
# Vercel
# ---------------------------------------------------------------------------

VERCEL_EXAMPLE = {
    "meta": {
        "product_name": "Vercel",
        "slug": "vercel",
        "mode": "full",
        "docs_root_url": "https://vercel.com/docs"
    },
    "hero": {
        "summary": "Cloud platform for frontend frameworks with instant deployments, serverless functions, and global CDN.",
        "high_risk_notice": "Production deployments are immediately live. Incorrect config causes user-facing downtime."
    },
    "agent_scope": {
        "safe_without_approval": [
            {"action": "Check deployment status and logs", "risk_level": "safe_read"},
            {"action": "List projects and deployments", "risk_level": "safe_read"},
            {"action": "View domain configuration", "risk_level": "safe_read"},
            {"action": "Read serverless function logs", "risk_level": "safe_read"}
        ],
        "requires_confirmation": [
            {"action": "Deploy to production", "risk_level": "requires_confirmation", "confirm_what": ["Target environment", "Git ref", "Project"]},
            {"action": "Rollback to previous deployment", "risk_level": "requires_confirmation", "confirm_what": ["Deployment ID", "Reason"]},
            {"action": "Create or update env variables", "risk_level": "requires_confirmation", "confirm_what": ["Variable name/value", "Target environments"]},
            {"action": "Trigger a redeployment", "risk_level": "requires_confirmation", "confirm_what": ["Project", "Environment"]}
        ],
        "requires_escalation": [
            {"action": "Configure or remove custom domains", "risk_level": "requires_escalation"},
            {"action": "Modify team membership or roles", "risk_level": "requires_escalation"},
            {"action": "Delete a project", "risk_level": "requires_escalation"}
        ],
        "never_do": [
            "Deploy to production without confirmation",
            "Delete production env vars blindly",
            "Expose API tokens in client code",
            "Assume preview URLs are private",
            "Delete a project without escalation"
        ]
    },
    "stop_conditions": {
        "stop_and_ask": [
            "Production vs preview target is unclear",
            "Env var target environments unspecified",
            "Rollback target is ambiguous",
            "Build settings or framework changes needed"
        ],
        "stop_and_escalate": [
            "Multiple consecutive deployments fail",
            "Domain or DNS changes requested",
            "Team membership changes needed",
            "Project deletion requested",
            "Security incident requires rollback"
        ]
    },
    "task_playbooks": [
        {
            "task_name": "Deploy a Project",
            "goal": "Deploy to production or create a preview deployment",
            "risk_level": "requires_confirmation",
            "ask_for": ["Project name or ID", "Target: production or preview"],
            "check": ["Project exists and token has access", "Required env vars are set"],
            "do": [
                "POST to deployments API with project and target",
                "Include git source if deploying specific ref",
                "Poll status until READY or ERROR",
                "Verify deployment URL returns expected content"
            ],
            "verify": ["State is 'READY'", "URL returns HTTP 200", "Build logs clean"],
            "confirm_before": ["Deploying to production"],
            "escalate_if": ["Multiple consecutive failures", "Build config changes needed"],
            "refs": [
                {"label": "Deployments API", "url": "https://vercel.com/docs/rest-api/endpoints/deployments"},
                {"label": "Vercel CLI", "url": "https://vercel.com/docs/cli/deploy"}
            ]
        },
        {
            "task_name": "Rollback a Deployment",
            "goal": "Revert production to a previous known-good deployment",
            "risk_level": "requires_confirmation",
            "ask_for": ["Deployment ID to restore", "Project name"],
            "check": ["Target deployment was previously successful", "Env vars still compatible"],
            "do": [
                "Identify last known-good deployment",
                "Confirm deployment ID with operator",
                "Promote deployment via API",
                "Verify production serves rolled-back version"
            ],
            "verify": ["Production URL returns expected content", "No 5xx errors"],
            "confirm_before": ["Always \u2014 rollbacks replace production"],
            "escalate_if": ["Target deployment is significantly old", "Rollback due to security incident"],
            "refs": [
                {"label": "Rollbacks", "url": "https://vercel.com/docs/deployments/rollbacks"}
            ]
        },
        {
            "task_name": "Configure Environment Variables",
            "goal": "Add, update, or remove env variables for a project",
            "risk_level": "requires_confirmation",
            "ask_for": ["Project ID", "Variable name", "Value", "Target environments"],
            "check": ["Variable already exists?", "Value format is correct"],
            "do": [
                "Check existing env vars via API",
                "Create or update the variable",
                "Trigger redeployment if needed",
                "Verify app uses new value"
            ],
            "verify": ["API returns created/updated variable", "App functions after redeployment"],
            "confirm_before": ["Setting any production env var", "Deleting an env var"],
            "escalate_if": ["Production database credentials", "Auth or payment credential changes"],
            "refs": [
                {"label": "Environment Variables", "url": "https://vercel.com/docs/projects/environment-variables"}
            ]
        },
        {
            "task_name": "Check Deployment Status",
            "goal": "Inspect state, build logs, and health of a deployment",
            "risk_level": "safe_read",
            "ask_for": ["Deployment ID or URL"],
            "check": ["API token has read access"],
            "do": [
                "Retrieve deployment by ID",
                "Check readyState: QUEUED, BUILDING, READY, ERROR",
                "If ERROR, examine build output",
                "If READY, verify URL returns expected content"
            ],
            "verify": ["State clearly identified", "Build logs reviewed if issues"],
            "confirm_before": [],
            "escalate_if": ["Multiple consecutive ERROR deployments", "Suspected platform issue"],
            "refs": [
                {"label": "Deployments API", "url": "https://vercel.com/docs/rest-api/endpoints/deployments"}
            ]
        }
    ],
    "operating_rules": {
        "always": [
            "Confirm target environment before deploying",
            "Check build logs before retrying failures",
            "Verify env vars for correct scope",
            "Use preview deployments before production",
            "Include team ID for team-scoped requests"
        ],
        "never": [
            "Deploy to production without confirmation",
            "Delete production env vars blindly",
            "Expose API tokens in client code",
            "Assume preview URLs are private",
            "Delete a project without escalation"
        ],
        "environment": [
            "Production: immediately live, always confirm",
            "Preview: one URL per deployment, publicly accessible",
            "Development: available in local 'vercel dev' only"
        ]
    },
    "setup": {
        "prerequisites": [
            "Vercel account (vercel.com/signup)",
            "Git repo on GitHub, GitLab, or Bitbucket",
            "Node.js 18+ for Vercel CLI"
        ],
        "auth_methods": [
            "Bearer token in Authorization header",
            "Vercel CLI via 'vercel login'",
            "OAuth for Git provider connection"
        ],
        "required_secrets": [
            "VERCEL_TOKEN (Bearer token)",
            "VERCEL_ORG_ID (team identifier)",
            "VERCEL_PROJECT_ID (project identifier)"
        ],
        "env_notes": [
            "Tokens do not expire unless revoked",
            "Env vars scoped to production, preview, or dev"
        ]
    },
    "decision_guide": [
        {
            "decision": "Git push deploy vs API deploy",
            "use_when": ["Git integration set up", "Standard CI/CD workflow"],
            "avoid_when": ["Need specific non-main commit", "Need custom env overrides"],
            "escalate_if": ["Neither approach works for setup"]
        },
        {
            "decision": "Rollback vs fix-forward",
            "use_when": ["Rollback: production broken, fix takes too long", "Fix-forward: issue is minor"],
            "avoid_when": ["Rollback: previous deploy also broken", "Fix-forward: data integrity risk"],
            "escalate_if": ["Both current and previous deployments broken"]
        }
    ],
    "troubleshooting": [
        {
            "issue": "Build fails with 'Module not found'",
            "likely_cause": "Missing dependency in package.json or file path casing mismatch",
            "fix": "Check module is in dependencies, verify file name casing",
            "escalate_if": "Error appears intermittently"
        },
        {
            "issue": "Serverless function 504 timeout",
            "likely_cause": "Function exceeds timeout limit or slow external call",
            "fix": "Optimize to complete within limit, use connection pooling",
            "escalate_if": "Function needs more time than plan allows"
        }
    ],
    "references": [
        {"label": "Deployments Overview", "url": "https://vercel.com/docs/deployments/overview", "topic": "Deployments"},
        {"label": "Deployments API", "url": "https://vercel.com/docs/rest-api/endpoints/deployments", "topic": "Deployments"},
        {"label": "Vercel CLI", "url": "https://vercel.com/docs/cli", "topic": "Deployments"},
        {"label": "Environment Variables", "url": "https://vercel.com/docs/projects/environment-variables", "topic": "Configuration"},
        {"label": "Serverless Functions", "url": "https://vercel.com/docs/functions/serverless-functions", "topic": "Functions"},
        {"label": "Edge Functions", "url": "https://vercel.com/docs/functions/edge-functions", "topic": "Functions"}
    ]
}

# ---------------------------------------------------------------------------
# Notion
# ---------------------------------------------------------------------------

NOTION_EXAMPLE = {
    "meta": {
        "product_name": "Notion",
        "slug": "notion",
        "mode": "full",
        "docs_root_url": "https://developers.notion.com"
    },
    "hero": {
        "summary": "API for creating, reading, updating, and searching workspace content including pages and databases.",
        "high_risk_notice": "No test mode. All API calls affect the live workspace. Page deletions cannot be undone via API."
    },
    "agent_scope": {
        "safe_without_approval": [
            {"action": "Query a database with filters", "risk_level": "safe_read"},
            {"action": "Retrieve a page and its properties", "risk_level": "safe_read"},
            {"action": "Search workspace by title", "risk_level": "safe_read"},
            {"action": "List users and members", "risk_level": "safe_read"}
        ],
        "requires_confirmation": [
            {"action": "Create a page in shared space", "risk_level": "requires_confirmation", "confirm_what": ["Parent page/database", "Title and content"]},
            {"action": "Update page properties", "risk_level": "requires_confirmation", "confirm_what": ["Page ID", "Properties being changed"]},
            {"action": "Append blocks to a page", "risk_level": "requires_confirmation", "confirm_what": ["Target page", "Content"]}
        ],
        "requires_escalation": [
            {"action": "Delete or archive a page", "risk_level": "requires_escalation"},
            {"action": "Bulk update multiple pages", "risk_level": "requires_escalation"},
            {"action": "Change integration permissions", "risk_level": "requires_escalation"}
        ],
        "never_do": [
            "Delete pages without escalation",
            "Bulk update without approval",
            "Assume pages are accessible without checking",
            "Store integration token in client code",
            "Ignore 429 rate limit responses"
        ]
    },
    "stop_conditions": {
        "stop_and_ask": [
            "Title matches multiple pages",
            "Property name is ambiguous",
            "Update request lacks specifics",
            "Database ID is unknown",
            "Filter criteria are vague"
        ],
        "stop_and_escalate": [
            "Page deletion or archival requested",
            "Bulk operation affects many pages",
            "Properties tied to automations",
            "Integration capability changes needed",
            "Query returns unexpectedly large result set"
        ]
    },
    "task_playbooks": [
        {
            "task_name": "Query a Database",
            "goal": "Retrieve filtered entries from a Notion database",
            "risk_level": "safe_read",
            "ask_for": ["Database ID (32-char UUID)"],
            "check": ["Database is shared with integration", "Filter property names match schema"],
            "do": [
                "POST /v1/databases/{id}/query with filter",
                "Process results array",
                "Paginate using next_cursor if has_more"
            ],
            "verify": ["Results array returned", "Count matches expectations"],
            "confirm_before": [],
            "escalate_if": ["Unexpectedly large result set"],
            "refs": [
                {"label": "Query a Database", "url": "https://developers.notion.com/reference/post-database-query"}
            ]
        },
        {
            "task_name": "Create a Page",
            "goal": "Create a new page in a database or under another page",
            "risk_level": "requires_confirmation",
            "ask_for": ["Parent database_id or page_id", "Properties matching schema"],
            "check": ["Parent shared with integration", "Property schema matches", "Check for duplicates"],
            "do": [
                "Construct properties matching parent schema",
                "POST /v1/pages with parent and properties",
                "Capture returned page ID",
                "Verify page appears in target location"
            ],
            "verify": ["Response contains page with id", "Properties are correct"],
            "confirm_before": ["Creating in shared workspace", "Content from external data"],
            "escalate_if": ["Bulk creation of many pages", "Pages trigger automations"],
            "refs": [
                {"label": "Create a Page", "url": "https://developers.notion.com/reference/post-page"}
            ]
        },
        {
            "task_name": "Update Page Properties",
            "goal": "Modify properties of an existing database entry",
            "risk_level": "requires_confirmation",
            "ask_for": ["Page ID (32-char UUID)", "Properties to update"],
            "check": ["Page exists", "Property names and types match", "Integration has update capability"],
            "do": [
                "Retrieve current page state",
                "Construct update with only changed fields",
                "PATCH /v1/pages/{id} with properties",
                "Verify response shows updated values"
            ],
            "verify": ["Updated values in response", "Database views reflect changes"],
            "confirm_before": ["Updating in shared workspace", "Archiving a page"],
            "escalate_if": ["Bulk updates", "Properties tied to automations"],
            "refs": [
                {"label": "Update Page Properties", "url": "https://developers.notion.com/reference/patch-page"}
            ]
        },
        {
            "task_name": "Search Workspace",
            "goal": "Find pages and databases by title",
            "risk_level": "safe_read",
            "ask_for": ["Search query text"],
            "check": ["Query is specific enough", "Only returns shared content"],
            "do": [
                "POST /v1/search with query",
                "Process results array",
                "Paginate if needed"
            ],
            "verify": ["Results contain relevant matches", "Objects include id and title"],
            "confirm_before": [],
            "escalate_if": [],
            "refs": [
                {"label": "Search API", "url": "https://developers.notion.com/reference/post-search"}
            ]
        }
    ],
    "operating_rules": {
        "always": [
            "Include Notion-Version header on every request",
            "Share pages with integration before access",
            "Retrieve schema before creating/updating",
            "Handle pagination for all list operations",
            "Respect rate limits with delays"
        ],
        "never": [
            "Delete pages without escalation",
            "Bulk update without approval",
            "Assume pages are accessible",
            "Store token in client code",
            "Ignore 429 responses"
        ],
        "environment": [
            "No sandbox \u2014 all calls affect live workspace",
            "Use a test workspace for development",
            "File block URLs expire \u2014 do not cache"
        ]
    },
    "setup": {
        "prerequisites": [
            "Notion account with a workspace",
            "Internal integration at notion.so/my-integrations",
            "Target pages shared with the integration"
        ],
        "auth_methods": [
            "Internal integration token in Bearer header",
            "Public OAuth 2.0 for third-party apps",
            "Notion-Version header required on all requests"
        ],
        "required_secrets": [
            "NOTION_API_KEY (secret_)",
            "NOTION_VERSION (e.g., 2022-06-28)"
        ],
        "env_notes": [
            "No test mode \u2014 all calls affect real workspace",
            "Rate limited per integration token",
            "Only access pages shared with integration"
        ]
    },
    "decision_guide": [
        {
            "decision": "Database query vs workspace search",
            "use_when": ["Query: know the database, need filters", "Search: need to find by title"],
            "avoid_when": ["Query: don't know which database", "Search: need complex filters"],
            "escalate_if": ["Need full-text search of page body (not supported)"]
        },
        {
            "decision": "Create page vs append blocks",
            "use_when": ["Create: adding a new record", "Append: adding content to existing page"],
            "avoid_when": ["Create: page already exists", "Append: need to modify existing blocks"],
            "escalate_if": ["Need to modify existing block content"]
        }
    ],
    "troubleshooting": [
        {
            "issue": "404 for a page that exists",
            "likely_cause": "Page not shared with integration or wrong ID format",
            "fix": "Share page via Share menu, use 32-char UUID from URL",
            "escalate_if": "Sharing correct but 404 persists"
        },
        {
            "issue": "Rate limit errors (429)",
            "likely_cause": "Exceeding rate limit or batch operations without throttling",
            "fix": "Implement exponential backoff with jitter",
            "escalate_if": "Rate limit hit despite proper throttling"
        }
    ],
    "references": [
        {"label": "Getting Started", "url": "https://developers.notion.com/docs/getting-started", "topic": "Setup"},
        {"label": "Authorization", "url": "https://developers.notion.com/docs/authorization", "topic": "Setup"},
        {"label": "Working with Databases", "url": "https://developers.notion.com/docs/working-with-databases", "topic": "Databases"},
        {"label": "Pages API", "url": "https://developers.notion.com/reference/page", "topic": "Pages"},
        {"label": "Block Types", "url": "https://developers.notion.com/reference/block", "topic": "Content"},
        {"label": "Search API", "url": "https://developers.notion.com/reference/post-search", "topic": "Search"}
    ]
}

# ---------------------------------------------------------------------------
# Slack
# ---------------------------------------------------------------------------

SLACK_EXAMPLE = {
    "meta": {
        "product_name": "Slack",
        "slug": "slack",
        "mode": "full",
        "docs_root_url": "https://api.slack.com"
    },
    "hero": {
        "summary": "APIs for sending messages, managing channels, building bots, and integrating workflows across teams.",
        "high_risk_notice": "No sandbox. Messages to public channels are visible to the entire workspace and cannot be unsent."
    },
    "agent_scope": {
        "safe_without_approval": [
            {"action": "Search messages and files", "risk_level": "safe_read"},
            {"action": "List channels and members", "risk_level": "safe_read"},
            {"action": "Read message history", "risk_level": "safe_read"},
            {"action": "Retrieve user profiles", "risk_level": "safe_read"}
        ],
        "requires_confirmation": [
            {"action": "Send message to public channel", "risk_level": "requires_confirmation", "confirm_what": ["Channel", "Content", "Threaded?"]},
            {"action": "Send a direct message", "risk_level": "requires_confirmation", "confirm_what": ["Recipient", "Content"]},
            {"action": "Upload a file to a channel", "risk_level": "requires_confirmation", "confirm_what": ["Channel", "File content"]}
        ],
        "requires_escalation": [
            {"action": "Create or archive a channel", "risk_level": "requires_escalation"},
            {"action": "Manage channel membership", "risk_level": "requires_escalation"},
            {"action": "Modify workspace settings", "risk_level": "requires_escalation"}
        ],
        "never_do": [
            "Post to public channels without confirmation",
            "Use @here/@channel without approval",
            "Store bot tokens in client code",
            "Kick members without escalation",
            "Ignore 429 rate limit responses"
        ]
    },
    "stop_conditions": {
        "stop_and_ask": [
            "Channel given by name, not ID",
            "No channel specified for message",
            "Message contains @here or @channel",
            "Message content is empty or unclear",
            "Invite vs remove action unspecified"
        ],
        "stop_and_escalate": [
            "Channel has many members and message is broad",
            "Automated high-frequency messaging requested",
            "Channel creation or archival requested",
            "Member removal from channels",
            "Admin-scoped API call needed"
        ]
    },
    "task_playbooks": [
        {
            "task_name": "Send a Message",
            "goal": "Post a message to a channel, DM, or thread",
            "risk_level": "requires_confirmation",
            "ask_for": ["Channel ID", "Message text"],
            "check": ["Bot is in target channel", "Bot has chat:write scope", "Content is accurate"],
            "do": [
                "Resolve channel name to ID if needed",
                "Construct payload with channel and text",
                "Call chat.postMessage with bot token",
                "Capture ts for threading"
            ],
            "verify": ["Response has ok: true", "Message appears correctly"],
            "confirm_before": ["Sending to public channel", "Message has @here/@channel"],
            "escalate_if": ["Channel has many members", "High-frequency automated posting"],
            "refs": [
                {"label": "chat.postMessage", "url": "https://api.slack.com/methods/chat.postMessage"},
                {"label": "Block Kit Builder", "url": "https://app.slack.com/block-kit-builder"}
            ]
        },
        {
            "task_name": "Search Messages",
            "goal": "Find messages matching a query across the workspace",
            "risk_level": "safe_read",
            "ask_for": ["Search query (supports from:, in:, after:)"],
            "check": ["Bot has search:read scope", "Results limited to accessible channels"],
            "do": [
                "Call search.messages with query",
                "Process messages.matches array",
                "Extract text, channel, user, permalink",
                "Paginate if needed"
            ],
            "verify": ["Response ok is true", "Results are relevant"],
            "confirm_before": [],
            "escalate_if": [],
            "refs": [
                {"label": "search.messages", "url": "https://api.slack.com/methods/search.messages"}
            ]
        },
        {
            "task_name": "Create a Channel",
            "goal": "Create a new public or private channel",
            "risk_level": "requires_escalation",
            "ask_for": ["Channel name (lowercase, hyphens, max 80 chars)"],
            "check": ["Bot has channels:manage scope", "Name doesn't already exist", "Naming convention confirmed"],
            "do": [
                "Verify no existing channel with same name",
                "Confirm name and type with operator",
                "Call conversations.create",
                "Set topic and purpose"
            ],
            "verify": ["Response ok with new channel ID", "Channel appears in workspace"],
            "confirm_before": ["Always \u2014 affects workspace organization"],
            "escalate_if": ["Always \u2014 escalation-level action", "Private channel creation", "Bulk creation"],
            "refs": [
                {"label": "conversations.create", "url": "https://api.slack.com/methods/conversations.create"}
            ]
        },
        {
            "task_name": "Manage Channel Membership",
            "goal": "Invite or remove members from a channel",
            "risk_level": "requires_escalation",
            "ask_for": ["Channel ID", "User ID(s)"],
            "check": ["Bot has channels:manage scope", "Channel exists and bot is member", "Users are workspace members"],
            "do": [
                "Confirm action, channel, and users with operator",
                "Call conversations.invite or conversations.kick",
                "Verify membership change",
                "Optionally notify channel"
            ],
            "verify": ["Response ok is true", "conversations.members confirms change"],
            "confirm_before": ["Always \u2014 affects channel access"],
            "escalate_if": ["Always \u2014 escalation-level action", "Member removal", "Bulk changes"],
            "refs": [
                {"label": "conversations.invite", "url": "https://api.slack.com/methods/conversations.invite"}
            ]
        }
    ],
    "operating_rules": {
        "always": [
            "Verify bot is in channel before posting",
            "Include plain text fallback with Block Kit",
            "Respect rate limits with Retry-After",
            "Verify webhook signatures",
            "Acknowledge Events API within 3 seconds"
        ],
        "never": [
            "Post to public channels without confirmation",
            "Use @here/@channel without approval",
            "Store bot tokens in client code",
            "Kick members without escalation",
            "Ignore 429 rate limit responses"
        ],
        "environment": [
            "No sandbox \u2014 all calls affect real workspace",
            "Use test workspace for development",
            "Bot tokens are workspace-specific"
        ]
    },
    "setup": {
        "prerequisites": [
            "Slack workspace with app install permission",
            "Slack App at api.slack.com/apps",
            "Bot token scopes configured"
        ],
        "auth_methods": [
            "Bot token (xoxb-) for bot actions",
            "User token (xoxp-) for user-scoped actions",
            "App token (xapp-) for Socket Mode"
        ],
        "required_secrets": [
            "SLACK_BOT_TOKEN (xoxb-)",
            "SLACK_SIGNING_SECRET",
            "SLACK_APP_TOKEN (xapp-) for Socket Mode"
        ],
        "env_notes": [
            "No sandbox \u2014 all calls affect real workspace",
            "Use dedicated test workspace",
            "Rate limits vary by API method tier"
        ]
    },
    "decision_guide": [
        {
            "decision": "Bot token (xoxb) vs User token (xoxp)",
            "use_when": ["Bot: automated messages", "User: actions attributed to a person"],
            "avoid_when": ["Bot: should appear from a user", "User: automated workflows"],
            "escalate_if": ["Unsure about bot vs user attribution"]
        },
        {
            "decision": "Events API vs Socket Mode",
            "use_when": ["Events API: public HTTPS endpoint", "Socket Mode: local dev or no public URL"],
            "avoid_when": ["Events API: no public endpoint", "Socket Mode: high-volume production"],
            "escalate_if": ["Processing needs exceed both approaches"]
        }
    ],
    "troubleshooting": [
        {
            "issue": "Bot cannot post to channel",
            "likely_cause": "Bot not invited or missing chat:write scope",
            "fix": "Invite bot with /invite @botname, add scope and reinstall",
            "escalate_if": "Bot invited but still cannot post"
        },
        {
            "issue": "Events not being received",
            "likely_cause": "URL verification not handled or event subscriptions not configured",
            "fix": "Handle url_verification challenge, check Event Subscriptions",
            "escalate_if": "Events missing despite correct configuration"
        },
        {
            "issue": "Rate limiting (429)",
            "likely_cause": "Burst of calls exceeding tier limit or polling instead of events",
            "fix": "Implement per-method backoff, switch to Events API",
            "escalate_if": "Limits hit despite proper throttling"
        }
    ],
    "references": [
        {"label": "chat.postMessage", "url": "https://api.slack.com/methods/chat.postMessage", "topic": "Messaging"},
        {"label": "Block Kit Builder", "url": "https://app.slack.com/block-kit-builder", "topic": "Messaging"},
        {"label": "Conversations API", "url": "https://api.slack.com/docs/conversations-api", "topic": "Channels"},
        {"label": "Events API", "url": "https://api.slack.com/events-api", "topic": "Events"},
        {"label": "Socket Mode", "url": "https://api.slack.com/apis/connections/socket", "topic": "Events"},
        {"label": "Rate Limiting", "url": "https://api.slack.com/docs/rate-limits", "topic": "Operations"}
    ]
}


# ---------------------------------------------------------------------------
# Assemble the EXAMPLE_PAGES list
# ---------------------------------------------------------------------------

EXAMPLE_PAGES = [
    {
        "product_name": "Stripe",
        "company_slug": "stripe",
        "docs_url": "https://docs.stripe.com",
        "email": "demo@groundocs.com",
        "content_json": STRIPE_EXAMPLE,
    },
    {
        "product_name": "Vercel",
        "company_slug": "vercel",
        "docs_url": "https://vercel.com/docs",
        "email": "demo@groundocs.com",
        "content_json": VERCEL_EXAMPLE,
    },
    {
        "product_name": "Notion",
        "company_slug": "notion",
        "docs_url": "https://developers.notion.com",
        "email": "demo@groundocs.com",
        "content_json": NOTION_EXAMPLE,
    },
    {
        "product_name": "Slack",
        "company_slug": "slack",
        "docs_url": "https://api.slack.com/docs",
        "email": "demo@groundocs.com",
        "content_json": SLACK_EXAMPLE,
    },
]


async def seed_example_pages(db: AsyncSession):
    """Create example AgentPage records if they don't already exist."""
    for example in EXAMPLE_PAGES:
        slug = example["company_slug"]
        result = await db.execute(
            select(AgentPage).where(AgentPage.company_slug == slug)
        )
        existing = result.scalar_one_or_none()

        content_json = example["content_json"]
        full_html = render_agent_page_html(
            content_json=content_json,
            product_name=example["product_name"],
            slug=slug,
            mode="full",
        )
        draft_html = render_agent_page_html(
            content_json=content_json,
            product_name=example["product_name"],
            slug=slug,
            mode="draft",
        )

        if existing:
            # Always re-render HTML to pick up renderer changes
            existing.full_content_json = content_json
            existing.full_html = full_html
            existing.draft_content_json = content_json
            existing.draft_html = draft_html
            logger.info(f"Updated example agent page: {slug}")
        else:
            agent_page = AgentPage(
                product_name=example["product_name"],
                company_slug=slug,
                docs_url=example["docs_url"],
                email=example["email"],
                status="full_ready",
                payment_status="paid",
                crawl_scope="full",
                full_content_json=content_json,
                full_html=full_html,
                draft_content_json=content_json,
                draft_html=draft_html,
            )
            db.add(agent_page)
            logger.info(f"Seeded example agent page: {slug}")
