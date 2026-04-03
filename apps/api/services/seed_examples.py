"""
Seed Example Agent Pages

Pre-built showcase pages for Stripe, Vercel, Notion, and Slack.
These are realistic, hand-crafted JSON objects matching the agent operating guide schema.
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
        "summary": "Stripe provides APIs for accepting payments, managing subscriptions, issuing refunds, and handling financial workflows.",
        "agent_fit_summary": [
            "Read payment data and account balances safely",
            "Create payment intents and subscriptions with confirmation",
            "Refunds and cancellations require human approval",
            "Account-level config changes require escalation"
        ],
        "high_risk_notice": "Live-mode API keys process real money — never use live keys in test workflows.",
        "primary_cta_label": "View Full Operating Guide"
    },
    "agent_scope": {
        "safe_without_approval": [
            {"action": "Retrieve payment or customer details", "reason": "Read-only, no side effects", "risk_level": "safe_read"},
            {"action": "List invoices or subscriptions", "reason": "Read-only enumeration", "risk_level": "safe_read"},
            {"action": "Retrieve balance and payout history", "reason": "Read-only financial summary", "risk_level": "safe_read"},
            {"action": "Create a test-mode payment intent", "reason": "No real money processed", "risk_level": "safe_write"}
        ],
        "requires_confirmation": [
            {"action": "Issue a refund", "reason": "Moves money back; cannot be undone once processed", "risk_level": "requires_confirmation", "confirmation_needed_for": ["Refund amount", "Charge ID", "Full or partial"]},
            {"action": "Cancel a subscription", "reason": "Ends recurring billing", "risk_level": "requires_confirmation", "confirmation_needed_for": ["Subscription ID", "Immediate or at period end", "Prorated refund needed"]},
            {"action": "Create a live-mode payment intent", "reason": "Charges a real payment method", "risk_level": "requires_confirmation", "confirmation_needed_for": ["Amount and currency", "Customer identity", "Payment method"]},
            {"action": "Create or modify a subscription", "reason": "Commits to recurring charges", "risk_level": "requires_confirmation", "confirmation_needed_for": ["Price ID", "Customer ID", "Trial period"]}
        ],
        "requires_escalation": [
            {"action": "Change payout schedule or bank account", "reason": "Affects how funds reach the business", "risk_level": "requires_escalation", "escalate_when": ["Any payout setting change", "Bank account add/remove"]},
            {"action": "Modify account settings or API keys", "reason": "Affects account security posture", "risk_level": "requires_escalation", "escalate_when": ["Webhook endpoint changes", "API key creation or revocation"]},
            {"action": "Delete a customer record", "reason": "Permanently removes all associated data", "risk_level": "requires_escalation", "escalate_when": ["Any customer deletion", "Bulk data operations"]}
        ]
    },
    "suitability": {
        "best_for": [
            "SaaS billing and subscription management",
            "E-commerce one-time payment processing",
            "Marketplace payment splitting via Connect",
            "Invoice generation and accounts receivable automation",
            "Usage-based metering and billing"
        ],
        "less_suitable_for": [
            "In-person POS without Stripe Terminal hardware",
            "Countries outside Stripe's supported regions",
            "Cryptocurrency or non-fiat payment processing"
        ],
        "not_clearly_supported": [
            "Multi-party escrow workflows beyond Connect",
            "Custom fraud rule authoring (Radar is Dashboard-only)",
            "Batch refund processing via a single API call"
        ]
    },
    "setup_access": {
        "prerequisites": [
            "A Stripe account (sign up at dashboard.stripe.com)",
            "API keys from the Stripe Dashboard (test and live)",
            "HTTPS endpoint for production webhooks"
        ],
        "accounts_and_access": [
            "Stripe Dashboard access with owner or admin role",
            "Test mode API keys for development (sk_test_...)",
            "Live mode API keys for production (sk_live_...)"
        ],
        "authentication": {
            "methods": [
                "Secret API key in Authorization: Bearer header",
                "Restricted keys with per-resource permissions",
                "Publishable key (pk_...) for client-side only"
            ],
            "required_secrets_or_tokens": [
                "STRIPE_SECRET_KEY (sk_test_... or sk_live_...)",
                "STRIPE_WEBHOOK_SECRET (whsec_...) for signature verification",
                "STRIPE_PUBLISHABLE_KEY (pk_...) if using Elements"
            ],
            "permission_notes": [
                "Secret key has full account access by default",
                "Restricted keys limit to specific resources",
                "Connect OAuth tokens access connected accounts"
            ],
            "environment_notes": [
                "Test and live keys are completely separate",
                "Webhook secrets are per-endpoint",
                "API version controlled via Stripe-Version header"
            ]
        },
        "initial_setup_steps": [
            "Install the Stripe SDK for your language",
            "Set STRIPE_SECRET_KEY as an environment variable",
            "Verify connectivity by retrieving your account",
            "Register a webhook endpoint and store the signing secret",
            "Run a test payment using card 4242424242424242"
        ]
    },
    "task_playbooks": [
        {
            "id": "stripe-accept-payment",
            "task_name": "Accept a Payment",
            "goal": "Charge a customer for a one-time purchase using a PaymentIntent",
            "when_to_use": [
                "Customer is making a one-time purchase",
                "Payment amount and currency are known"
            ],
            "when_not_to_use": [
                "Recurring billing (use subscriptions)",
                "Pre-built checkout preferred (use Checkout Sessions)"
            ],
            "risk_level": "requires_confirmation",
            "required_inputs": [
                {"name": "amount", "description": "Payment amount in smallest currency unit (e.g., 2500 for $25.00)", "required": True},
                {"name": "currency", "description": "Three-letter ISO currency code (e.g., usd)", "required": True},
                {"name": "payment_method_types", "description": "Accepted payment methods (e.g., ['card'])", "required": True}
            ],
            "optional_inputs": [
                {"name": "customer", "description": "Stripe customer ID (cus_...)"},
                {"name": "metadata", "description": "Key-value pairs for internal tracking"},
                {"name": "idempotency_key", "description": "Unique key to prevent duplicate charges"}
            ],
            "pre_checks": [
                "Confirm correct mode (test vs live) API key",
                "Validate amount is positive integer in smallest unit",
                "Verify currency is supported in account's country"
            ],
            "steps": [
                "Create PaymentIntent with amount and currency",
                "Return client_secret to frontend for confirmation",
                "Client confirms via stripe.confirmCardPayment()",
                "Listen for payment_intent.succeeded webhook"
            ],
            "verification_checks": [
                "PaymentIntent status is 'succeeded'",
                "Webhook payment_intent.succeeded received",
                "No duplicate charges for same idempotency key"
            ],
            "common_failure_modes": [
                {"issue": "Card declined", "why_it_happens": ["Insufficient funds", "Card reported lost or stolen"], "safe_recovery": ["Check decline_code in error response", "Prompt customer to try different method"]},
                {"issue": "3D Secure authentication fails", "why_it_happens": ["Customer abandons authentication flow"], "safe_recovery": ["Prompt customer to retry or use different card"]},
                {"issue": "Network timeout during creation", "why_it_happens": ["Connectivity issue between server and Stripe"], "safe_recovery": ["Retry with same idempotency key"]}
            ],
            "missing_information_behavior": [
                "If amount missing, ask the user for it",
                "If currency missing, confirm before defaulting"
            ],
            "confirmation_required_when": [
                "Creating a PaymentIntent in live mode"
            ],
            "escalate_when": [
                "Customer disputes the charge amount",
                "Payment is for an unusually large amount"
            ],
            "source_refs": [
                {"label": "Payment Intents API", "url": "https://docs.stripe.com/api/payment_intents"},
                {"label": "Accept a Payment Guide", "url": "https://docs.stripe.com/payments/accept-a-payment"}
            ],
            "confidence": "high"
        },
        {
            "id": "stripe-create-subscription",
            "task_name": "Create a Subscription",
            "goal": "Set up recurring billing for a customer with a specific price plan",
            "when_to_use": [
                "Customer signing up for a recurring plan",
                "A Price object already exists in Stripe"
            ],
            "when_not_to_use": [
                "One-time purchase (use PaymentIntent)",
                "Customer only wants to save a card (use SetupIntent)"
            ],
            "risk_level": "requires_confirmation",
            "required_inputs": [
                {"name": "customer", "description": "Stripe customer ID (cus_...) with payment method", "required": True},
                {"name": "price", "description": "Stripe price ID (price_...) for the plan", "required": True}
            ],
            "optional_inputs": [
                {"name": "trial_period_days", "description": "Number of free trial days"},
                {"name": "coupon", "description": "Coupon ID to apply a discount"},
                {"name": "proration_behavior", "description": "How to handle mid-cycle changes"}
            ],
            "pre_checks": [
                "Verify customer has a valid payment method",
                "Confirm price ID matches intended plan",
                "Check for existing active subscription"
            ],
            "steps": [
                "Retrieve or create Customer with payment method",
                "Create Subscription with customer and price",
                "Handle invoice.payment_succeeded webhook",
                "Handle subscription lifecycle webhooks"
            ],
            "verification_checks": [
                "Subscription status is 'active' or 'trialing'",
                "First invoice status is 'paid'",
                "Payment method was charged correctly"
            ],
            "common_failure_modes": [
                {"issue": "Payment method fails on first invoice", "why_it_happens": ["Card expired or insufficient funds"], "safe_recovery": ["Use latest_invoice.payment_intent to retry", "Prompt customer to update payment method"]},
                {"issue": "Duplicate subscription created", "why_it_happens": ["Retry without checking existing subscriptions"], "safe_recovery": ["Cancel the duplicate immediately"]}
            ],
            "missing_information_behavior": [
                "If customer ID missing, search by email or ask",
                "If price ID unknown, list available prices and ask"
            ],
            "confirmation_required_when": [
                "Creating any live-mode subscription",
                "Changing a subscription's price"
            ],
            "escalate_when": [
                "Customer requests a custom plan",
                "Multi-year commitment involved"
            ],
            "source_refs": [
                {"label": "Subscriptions API", "url": "https://docs.stripe.com/api/subscriptions"},
                {"label": "Billing Quickstart", "url": "https://docs.stripe.com/billing/quickstart"}
            ],
            "confidence": "high"
        },
        {
            "id": "stripe-issue-refund",
            "task_name": "Issue a Refund",
            "goal": "Return funds to a customer for a previous charge",
            "when_to_use": [
                "Customer requests a refund",
                "Order cancelled after payment captured"
            ],
            "when_not_to_use": [
                "Payment still processing (cancel PaymentIntent instead)",
                "Dispute already filed (respond to dispute instead)"
            ],
            "risk_level": "requires_confirmation",
            "required_inputs": [
                {"name": "charge_or_payment_intent", "description": "The charge ID (ch_...) or PaymentIntent ID (pi_...)", "required": True}
            ],
            "optional_inputs": [
                {"name": "amount", "description": "Amount to refund; omit for full refund"},
                {"name": "reason", "description": "Reason: duplicate, fraudulent, or requested_by_customer"}
            ],
            "pre_checks": [
                "Verify charge exists and status is 'succeeded'",
                "Check for previous partial refunds",
                "Calculate remaining refundable amount"
            ],
            "steps": [
                "Retrieve charge to verify refundable amount",
                "Confirm refund details with operator",
                "Create Refund with charge and optional amount",
                "Handle charge.refunded webhook"
            ],
            "verification_checks": [
                "Refund status is 'succeeded'",
                "Charge amount_refunded reflects correct total",
                "Internal order system updated"
            ],
            "common_failure_modes": [
                {"issue": "Refund exceeds available amount", "why_it_happens": ["Previous partial refunds consumed balance"], "safe_recovery": ["Check amount_refunded before creating refund"]},
                {"issue": "Charge is too old to refund", "why_it_happens": ["Charge outside refund window"], "safe_recovery": ["Issue credit or escalate to finance"]}
            ],
            "missing_information_behavior": [
                "If charge ID missing, ask for order ID or email",
                "If amount unspecified, confirm full or partial"
            ],
            "confirmation_required_when": [
                "Always — refunds move real money"
            ],
            "escalate_when": [
                "Refund exceeds business-defined threshold",
                "Charge has an active dispute"
            ],
            "source_refs": [
                {"label": "Refunds API", "url": "https://docs.stripe.com/api/refunds"},
                {"label": "Refund and Cancel Payments", "url": "https://docs.stripe.com/refunds"}
            ],
            "confidence": "high"
        },
        {
            "id": "stripe-investigate-failed-payment",
            "task_name": "Investigate a Failed Payment",
            "goal": "Diagnose why a payment attempt failed and determine next steps",
            "when_to_use": [
                "payment_intent.payment_failed webhook received",
                "Customer reports payment did not go through"
            ],
            "when_not_to_use": [
                "Payment succeeded but customer claims otherwise",
                "Dispute or fraud investigation needed"
            ],
            "risk_level": "safe_read",
            "required_inputs": [
                {"name": "payment_intent_id_or_invoice_id", "description": "The PaymentIntent (pi_...) or Invoice (in_...) ID", "required": True}
            ],
            "optional_inputs": [
                {"name": "customer_email", "description": "Customer email for looking up related charges"}
            ],
            "pre_checks": [
                "Retrieve PaymentIntent or Invoice status",
                "Check if failure is on latest or previous attempt"
            ],
            "steps": [
                "Retrieve PaymentIntent with expanded latest_charge",
                "Examine last_payment_error for decline code",
                "Check Charge outcome.reason and risk_level",
                "Determine recovery action based on decline code"
            ],
            "verification_checks": [
                "Root cause identified from decline code",
                "Recommended action matches failure type",
                "No queued retries without addressing root cause"
            ],
            "common_failure_modes": [
                {"issue": "Generic decline with no code", "why_it_happens": ["Issuing bank withheld reason"], "safe_recovery": ["Ask customer to contact their bank"]},
                {"issue": "Authentication not completed", "why_it_happens": ["3DS challenge not presented or abandoned"], "safe_recovery": ["Ensure frontend handles requires_action status"]}
            ],
            "missing_information_behavior": [
                "If no ID available, search by customer email",
                "If decline code unfamiliar, reference Stripe docs"
            ],
            "confirmation_required_when": [],
            "escalate_when": [
                "Failure flagged as fraudulent by Radar",
                "Multiple customers report same failure"
            ],
            "source_refs": [
                {"label": "Decline Codes", "url": "https://docs.stripe.com/declines/codes"},
                {"label": "Payment Intents API", "url": "https://docs.stripe.com/api/payment_intents"}
            ],
            "confidence": "high"
        },
        {
            "id": "stripe-handle-webhooks",
            "task_name": "Handle Webhooks",
            "goal": "Process incoming Stripe webhook events safely and idempotently",
            "when_to_use": [
                "Setting up a new webhook endpoint",
                "Debugging missed or failed webhook events"
            ],
            "when_not_to_use": [
                "Polling for status (use webhooks instead)",
                "Event types not relevant to your integration"
            ],
            "risk_level": "safe_write",
            "required_inputs": [
                {"name": "endpoint_url", "description": "HTTPS URL to receive webhook POSTs", "required": True},
                {"name": "events", "description": "Event types to subscribe to", "required": True}
            ],
            "optional_inputs": [
                {"name": "api_version", "description": "Pin webhook to a specific API version"}
            ],
            "pre_checks": [
                "Endpoint URL must be HTTPS",
                "Endpoint must respond with 2xx promptly",
                "Webhook signing secret is available"
            ],
            "steps": [
                "Register webhook endpoint with URL and events",
                "Store the returned signing secret securely",
                "Verify signatures on all incoming events",
                "Dispatch events to handlers; respond 200 immediately",
                "Deduplicate using event.id"
            ],
            "verification_checks": [
                "Webhook endpoint shows 'enabled' in Dashboard",
                "Test events are received and processed",
                "Signature verification passes"
            ],
            "common_failure_modes": [
                {"issue": "Signature verification fails", "why_it_happens": ["Wrong signing secret (test vs live)", "Body parsed before verification"], "safe_recovery": ["Use raw request body for verification", "Check endpoint secret in Dashboard"]},
                {"issue": "Events delivered out of order", "why_it_happens": ["Stripe does not guarantee ordering"], "safe_recovery": ["Design handlers to be idempotent"]},
                {"issue": "Endpoint returns 5xx causing retries", "why_it_happens": ["Unhandled exception in handler"], "safe_recovery": ["Return 200 and queue for async processing"]}
            ],
            "missing_information_behavior": [
                "If signing secret unavailable, retrieve from Dashboard",
                "If event type unrecognized, log and return 200"
            ],
            "confirmation_required_when": [],
            "escalate_when": [
                "Endpoint disabled due to repeated failures",
                "Suspected replay attack"
            ],
            "source_refs": [
                {"label": "Webhooks Overview", "url": "https://docs.stripe.com/webhooks"},
                {"label": "Webhook Signatures", "url": "https://docs.stripe.com/webhooks/signatures"}
            ],
            "confidence": "high"
        }
    ],
    "operating_rules": {
        "always_do": [
            "Use idempotency keys for all POST requests",
            "Verify webhook signatures before processing",
            "Use test-mode keys during development",
            "Store API keys in environment variables only",
            "Use smallest currency unit for amounts",
            "Expand related objects when needed"
        ],
        "never_do": [
            "Never expose secret keys in client code",
            "Never use live keys in test environments",
            "Never store or log raw card numbers",
            "Never refund without confirming with operator",
            "Never assume payment succeeded without checking",
            "Never retry failed payment without diagnosis"
        ],
        "verify_before_write_actions": [
            "Confirm correct mode (test vs live)",
            "Verify customer and payment method before charging",
            "Check for existing subscriptions to avoid duplicates",
            "Validate refund amount against refundable balance"
        ],
        "verify_after_write_actions": [
            "Check returned object's status field",
            "Verify amount_captured or amount_refunded matches",
            "Confirm webhook delivery for async operations"
        ],
        "ambiguity_rules": [
            "If 'charge' is ambiguous, ask one-time vs recurring",
            "If no currency specified, confirm before defaulting",
            "If refund reason unclear, ask for clarification"
        ],
        "environment_rules": [
            "Test mode: use sk_test_ keys and test cards",
            "Live mode: use sk_live_ keys after activation",
            "Webhooks must use HTTPS in production"
        ],
        "retry_idempotency_rules": [
            "Always include Idempotency-Key on POST requests",
            "Reuse same key when retrying a failed request",
            "GET and DELETE are inherently idempotent"
        ]
    },
    "decision_guide": [
        {
            "decision": "PaymentIntent API vs Stripe Checkout Sessions",
            "choose_when": ["Need full control over the payment UI", "Application has a custom checkout form"],
            "avoid_when": ["A pre-built checkout page would be faster", "PCI compliance scope is a concern"],
            "prefer_instead": ["Checkout Sessions for standard e-commerce", "Elements for embedded UI components"],
            "escalate_when": ["Payment flow involves unclear regulatory requirements"]
        },
        {
            "decision": "Immediate vs end-of-period subscription cancellation",
            "choose_when": ["Customer explicitly requests immediate cancellation", "Subscription was created in error"],
            "avoid_when": ["Customer prepaid and expects access until period end"],
            "prefer_instead": ["cancel_at_period_end: true by default"],
            "escalate_when": ["Customer wants both cancellation and full refund"]
        },
        {
            "decision": "Full refund vs partial refund",
            "choose_when": ["Full: entire order returned or never fulfilled", "Partial: price adjustment or partial return"],
            "avoid_when": ["Credit or coupon would better serve the need", "Charge has an active dispute"],
            "prefer_instead": ["Credit notes for goodwill adjustments"],
            "escalate_when": ["Refund exceeds business-defined threshold"]
        }
    ],
    "troubleshooting": [
        {
            "issue": "Card declined errors",
            "signals": ["PaymentIntent status is requires_payment_method", "Error type is card_error"],
            "likely_causes": ["Insufficient funds", "Card reported lost or stolen", "Issuing bank declined"],
            "recommended_actions": ["Check decline_code in error response", "Ask customer to try different payment method"],
            "do_not_do": ["Do not retry same card without customer action", "Do not expose full decline reason to customer"],
            "escalate_when": ["Multiple customers experience same decline", "Decline code is 'fraudulent'"],
            "source_refs": [{"label": "Decline Codes Reference", "url": "https://docs.stripe.com/declines/codes"}]
        },
        {
            "issue": "Webhook signature verification failure",
            "signals": ["SignatureVerificationError raised", "HTTP 400 from webhook handler"],
            "likely_causes": ["Wrong signing secret (test vs live)", "Body parsed before signature check"],
            "recommended_actions": ["Verify secret matches endpoint in Dashboard", "Use raw request body for verification"],
            "do_not_do": ["Do not disable signature verification", "Do not parse body before verifying"],
            "escalate_when": ["Verification fails for all events"],
            "source_refs": [{"label": "Webhook Signatures", "url": "https://docs.stripe.com/webhooks/signatures"}]
        },
        {
            "issue": "Subscription stuck in incomplete status",
            "signals": ["Status is 'incomplete' instead of 'active'", "First invoice shows 'open'"],
            "likely_causes": ["Initial payment failed", "Payment method not attached", "3DS not completed"],
            "recommended_actions": ["Check latest_invoice payment_intent for failure", "Have customer update payment method"],
            "do_not_do": ["Do not create new subscription without cancelling incomplete one"],
            "escalate_when": ["Multiple subscriptions stuck across customers"],
            "source_refs": [{"label": "Subscription Statuses", "url": "https://docs.stripe.com/billing/subscriptions/overview#subscription-statuses"}]
        }
    ],
    "references_by_topic": [
        {
            "topic": "Payments",
            "references": [
                {"label": "Payment Intents API", "url": "https://docs.stripe.com/api/payment_intents", "reason": "Core API for managing payments"},
                {"label": "Accept a Payment Guide", "url": "https://docs.stripe.com/payments/accept-a-payment", "reason": "End-to-end integration walkthrough"},
                {"label": "Stripe Testing", "url": "https://docs.stripe.com/testing", "reason": "Test card numbers and sandbox usage"}
            ]
        },
        {
            "topic": "Billing & Subscriptions",
            "references": [
                {"label": "Subscriptions API", "url": "https://docs.stripe.com/api/subscriptions", "reason": "CRUD operations on subscriptions"},
                {"label": "Billing Quickstart", "url": "https://docs.stripe.com/billing/quickstart", "reason": "Step-by-step subscription setup"},
                {"label": "Invoices API", "url": "https://docs.stripe.com/api/invoices", "reason": "Invoice management and lifecycle"}
            ]
        },
        {
            "topic": "Webhooks & Events",
            "references": [
                {"label": "Webhooks Overview", "url": "https://docs.stripe.com/webhooks", "reason": "Webhook concepts and best practices"},
                {"label": "Event Types", "url": "https://docs.stripe.com/api/events/types", "reason": "Complete list of event types"},
                {"label": "Stripe CLI", "url": "https://docs.stripe.com/stripe-cli", "reason": "Local webhook testing"}
            ]
        }
    ],
    "implementation_notes": {
        "customer_page_must_include": [
            "API key management and test vs live mode",
            "PaymentIntent creation and confirmation flow",
            "Subscription lifecycle management",
            "Webhook setup and signature verification",
            "Refund workflow with operator confirmation",
            "Error handling for decline codes"
        ],
        "doc_gaps_or_unclear_areas": [
            "Country-specific payment method availability is spread across pages",
            "Connect fee calculation examples could be more detailed",
            "Radar fraud rule configuration is Dashboard-only"
        ]
    }
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
        "summary": "Vercel is a cloud platform for frontend frameworks providing instant deployments, serverless functions, edge computing, and a global CDN.",
        "agent_fit_summary": [
            "Check deployment status and read logs safely",
            "Deployments and env var changes need confirmation",
            "Domain config and team settings require escalation",
            "Rollbacks replace current production immediately"
        ],
        "high_risk_notice": "Production deployments are immediately live to end users — incorrect config can cause downtime.",
        "primary_cta_label": "View Full Operating Guide"
    },
    "agent_scope": {
        "safe_without_approval": [
            {"action": "Check deployment status and build logs", "reason": "Read-only inspection", "risk_level": "safe_read"},
            {"action": "List projects and deployments", "reason": "Read-only enumeration", "risk_level": "safe_read"},
            {"action": "View domain configuration", "reason": "Read-only DNS inspection", "risk_level": "safe_read"},
            {"action": "Read serverless function logs", "reason": "Read-only observability", "risk_level": "safe_read"}
        ],
        "requires_confirmation": [
            {"action": "Deploy to production", "reason": "Immediately serves traffic to users", "risk_level": "requires_confirmation", "confirmation_needed_for": ["Target environment", "Git ref to deploy", "Project name"]},
            {"action": "Rollback to previous deployment", "reason": "Replaces current production build", "risk_level": "requires_confirmation", "confirmation_needed_for": ["Deployment ID to restore", "Confirmation target is known-good"]},
            {"action": "Create or update environment variables", "reason": "Incorrect values can break the app", "risk_level": "requires_confirmation", "confirmation_needed_for": ["Variable name and value", "Target environments"]},
            {"action": "Trigger a redeployment", "reason": "Creates a new build from current config", "risk_level": "requires_confirmation", "confirmation_needed_for": ["Project and environment", "Reason for redeployment"]}
        ],
        "requires_escalation": [
            {"action": "Configure or remove custom domains", "reason": "DNS changes affect accessibility and SSL", "risk_level": "requires_escalation", "escalate_when": ["Production domain changes", "DNS record modifications"]},
            {"action": "Modify team membership or roles", "reason": "Affects access control across projects", "risk_level": "requires_escalation", "escalate_when": ["Adding or removing members", "Changing roles"]},
            {"action": "Delete a project", "reason": "Permanently removes all deployments and config", "risk_level": "requires_escalation", "escalate_when": ["Any project deletion"]}
        ]
    },
    "suitability": {
        "best_for": [
            "Next.js, Nuxt, SvelteKit, and Astro apps",
            "Static sites and JAMstack architectures",
            "Preview deployments for PR review workflows",
            "Serverless API routes and edge functions",
            "Global content delivery with automatic HTTPS"
        ],
        "less_suitable_for": [
            "Long-running backend processes",
            "Apps requiring persistent server state",
            "Heavy database workloads",
            "Monolithic backends not on supported frameworks"
        ],
        "not_clearly_supported": [
            "Custom Docker container deployments",
            "Non-JS/TS backend runtimes beyond Python, Go, Ruby",
            "Persistent cron jobs exceeding function timeouts"
        ]
    },
    "setup_access": {
        "prerequisites": [
            "A Vercel account (vercel.com/signup)",
            "A Git repository on GitHub, GitLab, or Bitbucket",
            "Node.js 18+ for Vercel CLI usage"
        ],
        "accounts_and_access": [
            "Vercel Dashboard access",
            "Git provider connected for automatic deployments",
            "API token from Settings > Tokens"
        ],
        "authentication": {
            "methods": [
                "Bearer token in Authorization header",
                "Vercel CLI via 'vercel login'",
                "OAuth for Git provider connection"
            ],
            "required_secrets_or_tokens": [
                "VERCEL_TOKEN (Bearer token for API access)",
                "VERCEL_ORG_ID (team/org identifier)",
                "VERCEL_PROJECT_ID (project identifier)"
            ],
            "permission_notes": [
                "Tokens scoped to user or team",
                "Team roles: Owner, Member, Viewer, Developer",
                "Project-level controls on env variables"
            ],
            "environment_notes": [
                "Tokens do not expire unless revoked",
                "Team tokens inherit team permissions",
                "Env vars scoped to production, preview, or dev"
            ]
        },
        "initial_setup_steps": [
            "Install Vercel CLI: npm i -g vercel",
            "Authenticate: run 'vercel login'",
            "Link project: run 'vercel' in project directory",
            "Connect Git repo in Dashboard for auto-deploys",
            "Set required env vars in Project Settings"
        ]
    },
    "task_playbooks": [
        {
            "id": "vercel-deploy-project",
            "task_name": "Deploy a Project",
            "goal": "Deploy a project to production or create a preview deployment",
            "when_to_use": [
                "Shipping a new version of the app",
                "Creating a preview for a specific branch"
            ],
            "when_not_to_use": [
                "Git-connected repo already auto-deploys on push",
                "Only need to check an existing deployment"
            ],
            "risk_level": "requires_confirmation",
            "required_inputs": [
                {"name": "project_name_or_id", "description": "Vercel project name or ID", "required": True},
                {"name": "target", "description": "'production' or 'preview'", "required": True}
            ],
            "optional_inputs": [
                {"name": "git_ref", "description": "Git branch, tag, or commit SHA"},
                {"name": "environment_variables", "description": "Override env vars for this deployment"}
            ],
            "pre_checks": [
                "Verify project exists and token has permissions",
                "Confirm target environment",
                "Check required env vars are set"
            ],
            "steps": [
                "POST to deployments API with project and target",
                "Include git source if deploying specific ref",
                "Poll deployment status until READY or ERROR",
                "Verify deployment URL returns expected content"
            ],
            "verification_checks": [
                "Deployment state is 'READY'",
                "Production URL returns HTTP 200",
                "Build logs show no errors"
            ],
            "common_failure_modes": [
                {"issue": "Build fails with dependency errors", "why_it_happens": ["Missing dependency in package.json", "File path casing mismatch"], "safe_recovery": ["Check build logs for specific error", "Verify all dependencies listed"]},
                {"issue": "Env var missing at runtime", "why_it_happens": ["Variable not set for target environment"], "safe_recovery": ["Check env var scoping in Project Settings"]}
            ],
            "missing_information_behavior": [
                "If target unspecified, ask production or preview",
                "If git ref unspecified, deploy default branch"
            ],
            "confirmation_required_when": [
                "Deploying to production"
            ],
            "escalate_when": [
                "Build settings or framework config changes needed",
                "Multiple consecutive deployments have failed"
            ],
            "source_refs": [
                {"label": "Deployments API", "url": "https://vercel.com/docs/rest-api/endpoints/deployments"},
                {"label": "Vercel CLI Deploy", "url": "https://vercel.com/docs/cli/deploy"}
            ],
            "confidence": "high"
        },
        {
            "id": "vercel-rollback-deployment",
            "task_name": "Rollback a Deployment",
            "goal": "Revert production to a previous known-good deployment",
            "when_to_use": [
                "Current production has a critical bug",
                "Need to restore previous version quickly"
            ],
            "when_not_to_use": [
                "Issue is in env vars, not code",
                "Previous deployment also had issues"
            ],
            "risk_level": "requires_confirmation",
            "required_inputs": [
                {"name": "deployment_id", "description": "Deployment ID (dpl_...) to restore", "required": True},
                {"name": "project_name_or_id", "description": "Vercel project name or ID", "required": True}
            ],
            "optional_inputs": [
                {"name": "reason", "description": "Why the rollback is needed"}
            ],
            "pre_checks": [
                "Verify target deployment was previously successful",
                "Confirm env vars are still compatible",
                "Check deployment is not too old"
            ],
            "steps": [
                "Identify last known-good deployment",
                "Confirm deployment ID with operator",
                "Promote deployment via API or Dashboard",
                "Verify production serves rolled-back version"
            ],
            "verification_checks": [
                "Production URL returns expected content",
                "No 5xx errors on production domain",
                "Serverless functions respond correctly"
            ],
            "common_failure_modes": [
                {"issue": "Env vars changed since target deployment", "why_it_happens": ["Variables updated between deploys"], "safe_recovery": ["Compare current env vars with target deployment era"]},
                {"issue": "Incompatible API contracts", "why_it_happens": ["Backend APIs changed since target was live"], "safe_recovery": ["Verify API compatibility before completing"]}
            ],
            "missing_information_behavior": [
                "If no deployment ID, list recent successes and ask"
            ],
            "confirmation_required_when": [
                "Always — rollbacks replace production"
            ],
            "escalate_when": [
                "Target deployment is significantly old",
                "Rollback needed due to security incident"
            ],
            "source_refs": [
                {"label": "Rollbacks", "url": "https://vercel.com/docs/deployments/rollbacks"},
                {"label": "Deployments API", "url": "https://vercel.com/docs/rest-api/endpoints/deployments"}
            ],
            "confidence": "high"
        },
        {
            "id": "vercel-configure-env-vars",
            "task_name": "Configure Environment Variables",
            "goal": "Add, update, or remove environment variables for a project",
            "when_to_use": [
                "Setting up a new project's API keys",
                "Rotating a secret or connection string"
            ],
            "when_not_to_use": [
                "Secret belongs in a dedicated secrets manager",
                "Change requires a framework config file update"
            ],
            "risk_level": "requires_confirmation",
            "required_inputs": [
                {"name": "project_id", "description": "Vercel project ID or name", "required": True},
                {"name": "key", "description": "Environment variable name", "required": True},
                {"name": "value", "description": "Environment variable value", "required": True},
                {"name": "target", "description": "Environments: production, preview, development", "required": True}
            ],
            "optional_inputs": [
                {"name": "type", "description": "Variable type: plain, secret, encrypted"}
            ],
            "pre_checks": [
                "Check if variable already exists",
                "Verify value format is correct",
                "Confirm target environments"
            ],
            "steps": [
                "Check existing env vars via API",
                "Create or update the variable",
                "Trigger redeployment if needed",
                "Verify app uses new value correctly"
            ],
            "verification_checks": [
                "API returns created/updated variable",
                "Variable appears with correct targets",
                "App functions after redeployment"
            ],
            "common_failure_modes": [
                {"issue": "Variable set for wrong scope", "why_it_happens": ["Target array missing 'production'"], "safe_recovery": ["Update target to include correct environments"]},
                {"issue": "Special characters in value", "why_it_happens": ["Quotes or newlines in connection strings"], "safe_recovery": ["Base64-encode complex values"]}
            ],
            "missing_information_behavior": [
                "If target unspecified, ask which environments",
                "If value looks like a placeholder, confirm"
            ],
            "confirmation_required_when": [
                "Setting any production env var",
                "Deleting an env var"
            ],
            "escalate_when": [
                "Variable is a production database string",
                "Change affects auth or payment credentials"
            ],
            "source_refs": [
                {"label": "Environment Variables", "url": "https://vercel.com/docs/projects/environment-variables"},
                {"label": "Environment Variables API", "url": "https://vercel.com/docs/rest-api/endpoints/projects#get-project-environment-variables"}
            ],
            "confidence": "high"
        },
        {
            "id": "vercel-check-deployment-status",
            "task_name": "Check Deployment Status",
            "goal": "Inspect the state, build logs, and health of a deployment",
            "when_to_use": [
                "Monitoring an in-progress deployment",
                "Diagnosing a failed deployment"
            ],
            "when_not_to_use": [
                "Need to create or modify a deployment"
            ],
            "risk_level": "safe_read",
            "required_inputs": [
                {"name": "deployment_id_or_url", "description": "Deployment ID (dpl_...) or URL", "required": True}
            ],
            "optional_inputs": [
                {"name": "project_id", "description": "Project ID to list recent deployments"}
            ],
            "pre_checks": [
                "Verify API token has read access"
            ],
            "steps": [
                "Retrieve deployment by ID",
                "Check readyState: QUEUED, BUILDING, READY, ERROR",
                "If ERROR, examine build output",
                "If READY, verify URL returns expected content"
            ],
            "verification_checks": [
                "Deployment state clearly identified",
                "Build logs reviewed if issues present",
                "URL returns HTTP 200 for READY deployments"
            ],
            "common_failure_modes": [
                {"issue": "Deployment stuck in QUEUED", "why_it_happens": ["Concurrent build limit reached"], "safe_recovery": ["Wait for current build to complete"]},
                {"issue": "ERROR with no clear message", "why_it_happens": ["Build exceeded memory or time limits"], "safe_recovery": ["Check last build output, then retry"]}
            ],
            "missing_information_behavior": [
                "If no deployment ID, list recent and ask which to inspect"
            ],
            "confirmation_required_when": [],
            "escalate_when": [
                "Multiple consecutive ERROR deployments",
                "Suspected platform issue"
            ],
            "source_refs": [
                {"label": "Deployments API", "url": "https://vercel.com/docs/rest-api/endpoints/deployments"},
                {"label": "Build Logs", "url": "https://vercel.com/docs/deployments/logs"}
            ],
            "confidence": "high"
        }
    ],
    "operating_rules": {
        "always_do": [
            "Confirm target environment before deploying",
            "Check build logs before retrying failures",
            "Verify env vars are set for correct scope",
            "Use preview deployments before production",
            "Include team ID for team-scoped requests"
        ],
        "never_do": [
            "Never deploy to production without confirmation",
            "Never delete production env vars blindly",
            "Never expose API tokens in client code",
            "Never assume preview URLs are private",
            "Never delete a project without escalation"
        ],
        "verify_before_write_actions": [
            "Confirm target environment before changes",
            "Verify project name and team are correct",
            "Check git ref contains intended changes"
        ],
        "verify_after_write_actions": [
            "Verify deployment reaches READY state",
            "Check production URL returns expected content",
            "Confirm functions respond after env changes"
        ],
        "ambiguity_rules": [
            "If 'deploy' is ambiguous, ask production or preview",
            "If env var target unspecified, do not default",
            "If rollback target unclear, list and ask"
        ],
        "environment_rules": [
            "Production: immediately live, always confirm",
            "Preview: one URL per deployment, publicly accessible",
            "Development: available in local 'vercel dev' only"
        ],
        "retry_idempotency_rules": [
            "Deployment creation is not idempotent",
            "Check for in-progress builds before triggering",
            "Failed deploys do not auto-retry"
        ]
    },
    "decision_guide": [
        {
            "decision": "Git push deployment vs API deployment",
            "choose_when": ["Git integration is set up and code is committed", "Standard CI/CD workflow in place"],
            "avoid_when": ["Need to deploy a specific non-main commit", "Need custom env var overrides"],
            "prefer_instead": ["Git push for routine deployments", "API for CI/CD pipelines"],
            "escalate_when": ["Neither approach works for your setup"]
        },
        {
            "decision": "Rollback vs fix-forward",
            "choose_when": ["Rollback: production broken, fix will take too long", "Fix-forward: issue is minor and quick to patch"],
            "avoid_when": ["Rollback: previous deployment also has issues", "Fix-forward: bug affects data integrity"],
            "prefer_instead": ["Rollback for critical issues", "Fix-forward for minor issues"],
            "escalate_when": ["Both current and previous deployments broken"]
        }
    ],
    "troubleshooting": [
        {
            "issue": "Build fails with 'Module not found'",
            "signals": ["'Module not found: Can't resolve ...' in build log"],
            "likely_causes": ["Missing dependency in package.json", "File path casing mismatch", "Incorrect import path"],
            "recommended_actions": ["Check module is in dependencies", "Verify file name casing matches imports"],
            "do_not_do": ["Do not add as devDependency if needed at build time"],
            "escalate_when": ["Error appears intermittently"],
            "source_refs": [{"label": "Build Troubleshooting", "url": "https://vercel.com/docs/deployments/troubleshoot-a-build"}]
        },
        {
            "issue": "Serverless function returns 504 timeout",
            "signals": ["HTTP 504 from /api/* routes", "Timeout in function logs"],
            "likely_causes": ["Function exceeds timeout limit", "Slow external API or database call"],
            "recommended_actions": ["Optimize function to complete within limit", "Use connection pooling for databases"],
            "do_not_do": ["Do not chain function calls as workaround"],
            "escalate_when": ["Function needs more than plan allows"],
            "source_refs": [{"label": "Serverless Functions", "url": "https://vercel.com/docs/functions/serverless-functions"}]
        }
    ],
    "references_by_topic": [
        {
            "topic": "Deployments",
            "references": [
                {"label": "Deployments Overview", "url": "https://vercel.com/docs/deployments/overview", "reason": "Core deployment concepts"},
                {"label": "Deployments API", "url": "https://vercel.com/docs/rest-api/endpoints/deployments", "reason": "Programmatic deployment management"},
                {"label": "Vercel CLI", "url": "https://vercel.com/docs/cli", "reason": "CLI for local dev and deployment"}
            ]
        },
        {
            "topic": "Configuration",
            "references": [
                {"label": "Environment Variables", "url": "https://vercel.com/docs/projects/environment-variables", "reason": "Env var management and scoping"},
                {"label": "Project Configuration", "url": "https://vercel.com/docs/projects/project-configuration", "reason": "vercel.json reference"},
                {"label": "Frameworks", "url": "https://vercel.com/docs/frameworks", "reason": "Framework-specific settings"}
            ]
        },
        {
            "topic": "Serverless & Edge Functions",
            "references": [
                {"label": "Serverless Functions", "url": "https://vercel.com/docs/functions/serverless-functions", "reason": "Serverless function constraints"},
                {"label": "Edge Functions", "url": "https://vercel.com/docs/functions/edge-functions", "reason": "Edge runtime capabilities"},
                {"label": "Function Logs", "url": "https://vercel.com/docs/observability/runtime-logs", "reason": "Debugging function invocations"}
            ]
        }
    ],
    "implementation_notes": {
        "customer_page_must_include": [
            "Deployment workflow via Git and API",
            "Environment variable configuration",
            "Rollback procedure for incidents",
            "Serverless function constraints",
            "Common build failure troubleshooting"
        ],
        "doc_gaps_or_unclear_areas": [
            "API rate limits not published in one page",
            "Edge Function package compatibility incomplete",
            "Concurrent build limits per plan not prominent"
        ]
    }
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
        "summary": "Notion provides an API for programmatic access to create, read, update, and search workspace content including pages and databases.",
        "agent_fit_summary": [
            "Query databases and read pages safely",
            "Creating or updating shared content needs confirmation",
            "Deleting pages and bulk operations require escalation",
            "No test mode — all calls affect the live workspace"
        ],
        "high_risk_notice": "Page deletions and block modifications cannot be undone via API — changes are immediately visible to all members.",
        "primary_cta_label": "View Full Operating Guide"
    },
    "agent_scope": {
        "safe_without_approval": [
            {"action": "Query a database with filters", "reason": "Read-only data retrieval", "risk_level": "safe_read"},
            {"action": "Retrieve a page and its properties", "reason": "Read-only page inspection", "risk_level": "safe_read"},
            {"action": "Search workspace by title", "reason": "Read-only search", "risk_level": "safe_read"},
            {"action": "List users and workspace members", "reason": "Read-only enumeration", "risk_level": "safe_read"}
        ],
        "requires_confirmation": [
            {"action": "Create a page in shared space", "reason": "Immediately visible to all members", "risk_level": "requires_confirmation", "confirmation_needed_for": ["Parent page or database", "Page title and content"]},
            {"action": "Update page properties", "reason": "Changes visible immediately", "risk_level": "requires_confirmation", "confirmation_needed_for": ["Page ID", "Properties being changed"]},
            {"action": "Append blocks to a page", "reason": "Adds content to a shared page", "risk_level": "requires_confirmation", "confirmation_needed_for": ["Target page", "Content being appended"]}
        ],
        "requires_escalation": [
            {"action": "Delete or archive a page", "reason": "Cannot be undone via API", "risk_level": "requires_escalation", "escalate_when": ["Any page deletion or archival"]},
            {"action": "Bulk update multiple pages", "reason": "High blast radius across many records", "risk_level": "requires_escalation", "escalate_when": ["Operation affects many pages", "Modifies properties used by automations"]},
            {"action": "Change integration permissions", "reason": "Affects access scope across workspace", "risk_level": "requires_escalation", "escalate_when": ["Modifying integration capabilities"]}
        ]
    },
    "suitability": {
        "best_for": [
            "Knowledge base and documentation management",
            "CRM and project tracking via databases",
            "Automated content creation from external data",
            "Cross-tool integrations (Slack, GitHub, etc.)",
            "Meeting notes and task automation"
        ],
        "less_suitable_for": [
            "High-frequency real-time updates",
            "Large file storage",
            "Complex relational queries with joins",
            "Public-facing sites with heavy traffic"
        ],
        "not_clearly_supported": [
            "Full-text search of page body content",
            "Editing existing block content in place",
            "Exporting pages to PDF via API"
        ]
    },
    "setup_access": {
        "prerequisites": [
            "A Notion account with a workspace",
            "Internal integration at notion.so/my-integrations",
            "Target pages shared with the integration"
        ],
        "accounts_and_access": [
            "Workspace member or admin role",
            "Integration token (secret_...)",
            "Pages explicitly shared via Share menu"
        ],
        "authentication": {
            "methods": [
                "Internal integration token in Bearer header",
                "Public OAuth 2.0 for third-party apps",
                "Notion-Version header required on all requests"
            ],
            "required_secrets_or_tokens": [
                "NOTION_API_KEY (secret_...)",
                "NOTION_VERSION (e.g., 2022-06-28)"
            ],
            "permission_notes": [
                "Only access pages explicitly shared with integration",
                "Capabilities set at integration creation",
                "Child pages inherit parent sharing"
            ],
            "environment_notes": [
                "No test mode — all calls affect real workspace",
                "Notion-Version header controls response format",
                "Rate limited per integration token"
            ]
        },
        "initial_setup_steps": [
            "Create internal integration at notion.so/my-integrations",
            "Copy the integration token",
            "Share target pages with the integration",
            "Test connectivity: GET /v1/users/me",
            "Query a shared database to verify access"
        ]
    },
    "task_playbooks": [
        {
            "id": "notion-query-database",
            "task_name": "Query a Database",
            "goal": "Retrieve filtered and sorted entries from a Notion database",
            "when_to_use": [
                "Looking up records matching specific criteria",
                "Generating reports from structured data"
            ],
            "when_not_to_use": [
                "Searching across entire workspace (use Search)",
                "Retrieving a single page by ID"
            ],
            "risk_level": "safe_read",
            "required_inputs": [
                {"name": "database_id", "description": "Notion database ID (32-char UUID)", "required": True}
            ],
            "optional_inputs": [
                {"name": "filter", "description": "Filter object to narrow results"},
                {"name": "sorts", "description": "Sort order array"},
                {"name": "page_size", "description": "Results per page (max 100)"}
            ],
            "pre_checks": [
                "Verify database is shared with integration",
                "Confirm filter property names match schema",
                "Check property types in filters match"
            ],
            "steps": [
                "POST /v1/databases/{id}/query with filter and sorts",
                "Process results array from response",
                "Paginate using next_cursor if has_more is true"
            ],
            "verification_checks": [
                "Response contains results array",
                "Result count matches filter expectations",
                "Property values in expected format"
            ],
            "common_failure_modes": [
                {"issue": "404 for existing database", "why_it_happens": ["Not shared with integration", "Wrong ID format"], "safe_recovery": ["Share via Share menu", "Use 32-char ID from URL"]},
                {"issue": "Filter returns no results", "why_it_happens": ["Property name mismatch", "Type mismatch in filter"], "safe_recovery": ["Retrieve schema first with GET /v1/databases/{id}"]}
            ],
            "missing_information_behavior": [
                "If database ID unknown, search workspace by title",
                "If filter criteria vague, ask for specifics"
            ],
            "confirmation_required_when": [],
            "escalate_when": [
                "Query returns unexpectedly large result set"
            ],
            "source_refs": [
                {"label": "Query a Database", "url": "https://developers.notion.com/reference/post-database-query"},
                {"label": "Filter Database Entries", "url": "https://developers.notion.com/reference/post-database-query-filter"}
            ],
            "confidence": "high"
        },
        {
            "id": "notion-create-page",
            "task_name": "Create a Page",
            "goal": "Create a new page in a database or as a child of another page",
            "when_to_use": [
                "Adding a new record to a database",
                "Creating a document under an existing page"
            ],
            "when_not_to_use": [
                "Updating an existing page",
                "Appending content to an existing page"
            ],
            "risk_level": "requires_confirmation",
            "required_inputs": [
                {"name": "parent", "description": "Parent database_id or page_id", "required": True},
                {"name": "properties", "description": "Properties matching parent schema (must include title)", "required": True}
            ],
            "optional_inputs": [
                {"name": "children", "description": "Block objects for initial page content"},
                {"name": "icon", "description": "Page icon (emoji or URL)"},
                {"name": "cover", "description": "Page cover image URL"}
            ],
            "pre_checks": [
                "Verify parent is shared with integration",
                "Confirm property schema matches target",
                "Check for duplicate entries"
            ],
            "steps": [
                "Construct properties matching parent schema",
                "POST /v1/pages with parent and properties",
                "Capture returned page ID and URL",
                "Verify page appears in target location"
            ],
            "verification_checks": [
                "Response contains page object with id",
                "Page appears with correct properties",
                "Content blocks render correctly"
            ],
            "common_failure_modes": [
                {"issue": "Validation error on properties", "why_it_happens": ["Property name/type mismatch", "Title property missing"], "safe_recovery": ["Retrieve schema first to confirm names and types"]},
                {"issue": "Block limit exceeded", "why_it_happens": ["More than 100 children in one request"], "safe_recovery": ["Create page first, append blocks in batches"]}
            ],
            "missing_information_behavior": [
                "If parent unknown, search by title and confirm",
                "If required properties missing, retrieve schema"
            ],
            "confirmation_required_when": [
                "Creating in a shared workspace",
                "Content generated from external data"
            ],
            "escalate_when": [
                "Bulk creation of many pages",
                "Pages that trigger automations"
            ],
            "source_refs": [
                {"label": "Create a Page", "url": "https://developers.notion.com/reference/post-page"},
                {"label": "Block Types", "url": "https://developers.notion.com/reference/block"}
            ],
            "confidence": "high"
        },
        {
            "id": "notion-update-page-properties",
            "task_name": "Update Page Properties",
            "goal": "Modify properties of an existing page or database entry",
            "when_to_use": [
                "Changing status, assignee, or due date",
                "Updating a record with new information"
            ],
            "when_not_to_use": [
                "Adding content blocks (use Append Blocks)",
                "Moving the page (not supported via API)"
            ],
            "risk_level": "requires_confirmation",
            "required_inputs": [
                {"name": "page_id", "description": "Notion page ID (32-char UUID)", "required": True},
                {"name": "properties", "description": "Properties to update", "required": True}
            ],
            "optional_inputs": [
                {"name": "archived", "description": "Set true to archive (soft-delete)"}
            ],
            "pre_checks": [
                "Retrieve page to verify it exists",
                "Confirm property names and types match",
                "Verify integration has update capabilities"
            ],
            "steps": [
                "Retrieve current page state",
                "Construct update with only changed fields",
                "PATCH /v1/pages/{page_id} with properties",
                "Verify response shows updated values"
            ],
            "verification_checks": [
                "Response shows updated property values",
                "Page correct on re-retrieval",
                "Database views reflect changes"
            ],
            "common_failure_modes": [
                {"issue": "Cannot update formula or rollup", "why_it_happens": ["These are computed, not editable"], "safe_recovery": ["Update the source properties instead"]},
                {"issue": "Stale data conflict", "why_it_happens": ["Page modified between read and update"], "safe_recovery": ["Re-read page and retry update"]}
            ],
            "missing_information_behavior": [
                "If page ID unknown, search by title and confirm",
                "If property ambiguous, list current values and ask"
            ],
            "confirmation_required_when": [
                "Updating properties in shared workspace",
                "Archiving a page"
            ],
            "escalate_when": [
                "Bulk updates affecting many pages",
                "Modifying properties tied to automations"
            ],
            "source_refs": [
                {"label": "Update Page Properties", "url": "https://developers.notion.com/reference/patch-page"},
                {"label": "Property Values", "url": "https://developers.notion.com/reference/property-value-object"}
            ],
            "confidence": "high"
        },
        {
            "id": "notion-search-workspace",
            "task_name": "Search Workspace",
            "goal": "Find pages and databases by title across the workspace",
            "when_to_use": [
                "Looking up a page when the ID is unknown",
                "Discovering which databases exist"
            ],
            "when_not_to_use": [
                "Querying a specific database with filters",
                "Searching page body content (not supported)"
            ],
            "risk_level": "safe_read",
            "required_inputs": [
                {"name": "query", "description": "Search text to match against titles", "required": True}
            ],
            "optional_inputs": [
                {"name": "filter", "description": "Filter by 'page' or 'database'"},
                {"name": "sort", "description": "Sort by last_edited_time"}
            ],
            "pre_checks": [
                "Ensure query is specific enough",
                "Search only returns content shared with integration"
            ],
            "steps": [
                "POST /v1/search with query and optional filter",
                "Process results array",
                "Paginate using next_cursor if needed"
            ],
            "verification_checks": [
                "Results contain relevant matches",
                "Objects include id, title, and parent",
                "Pagination handled correctly"
            ],
            "common_failure_modes": [
                {"issue": "No results for known content", "why_it_happens": ["Page not shared with integration", "Search only matches titles"], "safe_recovery": ["Verify sharing", "Try shorter query"]},
                {"issue": "Too many irrelevant results", "why_it_happens": ["Query too broad"], "safe_recovery": ["Use more specific query or filter by type"]}
            ],
            "missing_information_behavior": [
                "If query empty, ask what to search for",
                "If results ambiguous, present top matches"
            ],
            "confirmation_required_when": [],
            "escalate_when": [],
            "source_refs": [
                {"label": "Search API", "url": "https://developers.notion.com/reference/post-search"}
            ],
            "confidence": "high"
        }
    ],
    "operating_rules": {
        "always_do": [
            "Include Notion-Version header on every request",
            "Share pages with integration before access",
            "Respect rate limits with delays between calls",
            "Retrieve schema before creating or updating pages",
            "Handle pagination for all list operations"
        ],
        "never_do": [
            "Never delete pages without escalation",
            "Never bulk update many pages without approval",
            "Never assume pages are accessible without checking",
            "Never store integration token in client code",
            "Never ignore 429 responses"
        ],
        "verify_before_write_actions": [
            "Confirm target is shared with integration",
            "Validate property names against schema",
            "Check for duplicates before creating"
        ],
        "verify_after_write_actions": [
            "Retrieve page to confirm changes applied",
            "Verify content renders correctly in Notion",
            "Check database views reflect changes"
        ],
        "ambiguity_rules": [
            "If title matches multiple, present options",
            "If property name ambiguous, retrieve schema",
            "If 'update' without specifics, ask what to change"
        ],
        "environment_rules": [
            "No sandbox — all calls affect live workspace",
            "Use a test workspace for development",
            "File block URLs expire — do not cache"
        ],
        "retry_idempotency_rules": [
            "Use exponential backoff for 429 responses",
            "Page creation is not idempotent",
            "Use unique identifiers to prevent duplicates"
        ]
    },
    "decision_guide": [
        {
            "decision": "Database query vs workspace search",
            "choose_when": ["Query: know the database, need filtered results", "Search: need to find something by title"],
            "avoid_when": ["Query: don't know which database", "Search: need complex filters"],
            "prefer_instead": ["Query for structured data", "Search for discovery by title"],
            "escalate_when": ["Need full-text search of page body (not supported)"]
        },
        {
            "decision": "Create page vs append blocks",
            "choose_when": ["Create: adding a new record", "Append: adding content to existing page"],
            "avoid_when": ["Create: page already exists", "Append: need to modify existing blocks"],
            "prefer_instead": ["Create for new records", "Append for adding sections"],
            "escalate_when": ["Need to modify existing block content (delete and recreate required)"]
        }
    ],
    "troubleshooting": [
        {
            "issue": "404 for a page that exists in Notion",
            "signals": ["404 Not Found", "object_not_found error code"],
            "likely_causes": ["Not shared with integration", "Wrong ID format", "Missing capability"],
            "recommended_actions": ["Share page with integration via Share menu", "Use 32-char UUID from URL"],
            "do_not_do": ["Do not retry without fixing sharing"],
            "escalate_when": ["Sharing correct but 404 persists"],
            "source_refs": [{"label": "Authorization", "url": "https://developers.notion.com/docs/authorization"}]
        },
        {
            "issue": "Rate limit errors (429)",
            "signals": ["HTTP 429 response", "Retry-After header"],
            "likely_causes": ["Exceeding rate limit", "Batch operations without throttling"],
            "recommended_actions": ["Implement exponential backoff with jitter", "Add delays between consecutive requests"],
            "do_not_do": ["Do not retry immediately without waiting"],
            "escalate_when": ["Rate limit hit despite proper throttling"],
            "source_refs": [{"label": "Rate Limits", "url": "https://developers.notion.com/reference/request-limits"}]
        }
    ],
    "references_by_topic": [
        {
            "topic": "Getting Started",
            "references": [
                {"label": "Notion API Getting Started", "url": "https://developers.notion.com/docs/getting-started", "reason": "Integration setup and first API call"},
                {"label": "Authorization", "url": "https://developers.notion.com/docs/authorization", "reason": "Authentication and sharing requirements"}
            ]
        },
        {
            "topic": "Databases & Pages",
            "references": [
                {"label": "Working with Databases", "url": "https://developers.notion.com/docs/working-with-databases", "reason": "Query, filter, and sort patterns"},
                {"label": "Pages API", "url": "https://developers.notion.com/reference/page", "reason": "Create, retrieve, and update pages"},
                {"label": "Block Types", "url": "https://developers.notion.com/reference/block", "reason": "Supported block types and schemas"}
            ]
        },
        {
            "topic": "Search & Discovery",
            "references": [
                {"label": "Search API", "url": "https://developers.notion.com/reference/post-search", "reason": "Workspace-wide title search"},
                {"label": "Pagination", "url": "https://developers.notion.com/reference/intro#pagination", "reason": "Cursor-based pagination"}
            ]
        }
    ],
    "implementation_notes": {
        "customer_page_must_include": [
            "Integration setup and sharing requirements",
            "Database query patterns with filters",
            "Page creation and property management",
            "Rate limiting and backoff strategy",
            "Common gotchas: sharing, block editing, search scope"
        ],
        "doc_gaps_or_unclear_areas": [
            "Supported block types not aggregated in one place",
            "OAuth error handling examples are minimal",
            "Block editing limitations not prominently documented"
        ]
    }
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
        "summary": "Slack provides APIs for sending messages, managing channels, building bots, and integrating workflows across teams.",
        "agent_fit_summary": [
            "Read messages and search content safely",
            "Sending messages to channels needs confirmation",
            "Channel management requires escalation",
            "No sandbox — all calls affect the real workspace"
        ],
        "high_risk_notice": "Messages sent to public channels are visible to the entire workspace and cannot be unsent.",
        "primary_cta_label": "View Full Operating Guide"
    },
    "agent_scope": {
        "safe_without_approval": [
            {"action": "Search messages and files", "reason": "Read-only search in accessible channels", "risk_level": "safe_read"},
            {"action": "List channels and members", "reason": "Read-only enumeration", "risk_level": "safe_read"},
            {"action": "Read message history", "reason": "Read-only conversation content", "risk_level": "safe_read"},
            {"action": "Retrieve user profiles", "reason": "Read-only user information", "risk_level": "safe_read"}
        ],
        "requires_confirmation": [
            {"action": "Send a message to a public channel", "reason": "Visible to all workspace members", "risk_level": "requires_confirmation", "confirmation_needed_for": ["Target channel", "Message content", "Whether threaded"]},
            {"action": "Send a direct message", "reason": "Arrives as notification to recipient", "risk_level": "requires_confirmation", "confirmation_needed_for": ["Recipient", "Message content"]},
            {"action": "Upload a file to a channel", "reason": "Shared with all channel members", "risk_level": "requires_confirmation", "confirmation_needed_for": ["Target channel", "File content"]}
        ],
        "requires_escalation": [
            {"action": "Create or archive a channel", "reason": "Affects workspace organization", "risk_level": "requires_escalation", "escalate_when": ["Any channel creation", "Archiving active channels"]},
            {"action": "Manage channel membership", "reason": "Affects who can see channel content", "risk_level": "requires_escalation", "escalate_when": ["Removing members", "Inviting to private channels"]},
            {"action": "Modify workspace settings or roles", "reason": "Admin-level workspace-wide impact", "risk_level": "requires_escalation", "escalate_when": ["Any admin-scoped API call"]}
        ]
    },
    "suitability": {
        "best_for": [
            "Automated notifications and alerts",
            "Interactive bots for help desk and DevOps",
            "Cross-tool integrations (GitHub, Jira, etc.)",
            "Workflow automation triggered by events",
            "Team communication search and archival"
        ],
        "less_suitable_for": [
            "High-volume data streaming",
            "Long-term data storage",
            "Customer-facing live chat",
            "Real-time audio/video (Huddles not API-accessible)"
        ],
        "not_clearly_supported": [
            "Editing messages sent by other users",
            "Accessing Huddle or Clip content via API",
            "Full workspace analytics beyond admin APIs"
        ]
    },
    "setup_access": {
        "prerequisites": [
            "A Slack workspace with app install permission",
            "A Slack App at api.slack.com/apps",
            "Bot token scopes configured for use case"
        ],
        "accounts_and_access": [
            "Workspace admin approval for installation",
            "Bot User OAuth Token (xoxb-...)",
            "App-level token (xapp-...) for Socket Mode"
        ],
        "authentication": {
            "methods": [
                "Bot token (xoxb-...) for bot actions",
                "User token (xoxp-...) for user-scoped actions",
                "App token (xapp-...) for Socket Mode",
                "Incoming Webhooks for simple posting"
            ],
            "required_secrets_or_tokens": [
                "SLACK_BOT_TOKEN (xoxb-...)",
                "SLACK_SIGNING_SECRET (for request verification)",
                "SLACK_APP_TOKEN (xapp-... for Socket Mode)"
            ],
            "permission_notes": [
                "Scopes are granular: chat:write, channels:read, etc.",
                "Bot can only access channels it is a member of",
                "Admin scopes require workspace admin approval"
            ],
            "environment_notes": [
                "No sandbox — all calls affect real workspace",
                "Use a dedicated test workspace for development",
                "Rate limits vary by API method tier"
            ]
        },
        "initial_setup_steps": [
            "Create app at api.slack.com/apps",
            "Configure OAuth scopes for your use case",
            "Install app and copy Bot User OAuth Token",
            "Invite bot to target channels: /invite @botname",
            "Test connectivity: call auth.test"
        ]
    },
    "task_playbooks": [
        {
            "id": "slack-send-message",
            "task_name": "Send a Message",
            "goal": "Post a message to a Slack channel, DM, or thread",
            "when_to_use": [
                "Sending automated notifications",
                "Posting structured info using Block Kit"
            ],
            "when_not_to_use": [
                "Simple webhook posting (use Incoming Webhooks)",
                "Updating an existing message (use chat.update)"
            ],
            "risk_level": "requires_confirmation",
            "required_inputs": [
                {"name": "channel", "description": "Channel ID (C0123456789)", "required": True},
                {"name": "text", "description": "Plain text fallback (always required)", "required": True}
            ],
            "optional_inputs": [
                {"name": "blocks", "description": "Block Kit layout blocks for rich formatting"},
                {"name": "thread_ts", "description": "Parent message timestamp for threading"},
                {"name": "unfurl_links", "description": "Whether to unfurl URLs"}
            ],
            "pre_checks": [
                "Verify bot is a member of target channel",
                "Confirm bot has chat:write scope",
                "Review message content for accuracy"
            ],
            "steps": [
                "Resolve channel name to ID if needed",
                "Construct payload with channel and text",
                "Call chat.postMessage with bot token",
                "Capture ts from response for threading"
            ],
            "verification_checks": [
                "Response has ok: true",
                "Response includes ts and channel",
                "Message appears with correct formatting"
            ],
            "common_failure_modes": [
                {"issue": "channel_not_found error", "why_it_happens": ["Bot not in channel", "Using name instead of ID"], "safe_recovery": ["Invite bot: /invite @botname", "Use conversations.list to resolve ID"]},
                {"issue": "not_authed error", "why_it_happens": ["Token invalid or missing scopes"], "safe_recovery": ["Verify token with auth.test"]},
                {"issue": "rate_limited response", "why_it_happens": ["Exceeded method rate limit"], "safe_recovery": ["Respect Retry-After header"]}
            ],
            "missing_information_behavior": [
                "If channel given by name, look up ID first",
                "If message content empty, ask what to send"
            ],
            "confirmation_required_when": [
                "Sending to a public channel",
                "Message contains @here or @channel"
            ],
            "escalate_when": [
                "Channel has many members",
                "Sending automated messages at high frequency"
            ],
            "source_refs": [
                {"label": "chat.postMessage", "url": "https://api.slack.com/methods/chat.postMessage"},
                {"label": "Block Kit Builder", "url": "https://app.slack.com/block-kit-builder"}
            ],
            "confidence": "high"
        },
        {
            "id": "slack-search-messages",
            "task_name": "Search Messages",
            "goal": "Find messages across the workspace matching a query",
            "when_to_use": [
                "Finding specific conversations or decisions",
                "Retrieving info shared in Slack for reference"
            ],
            "when_not_to_use": [
                "Reading full channel history (use conversations.history)",
                "Real-time monitoring (use Events API)"
            ],
            "risk_level": "safe_read",
            "required_inputs": [
                {"name": "query", "description": "Search string (supports from:, in:, after: modifiers)", "required": True}
            ],
            "optional_inputs": [
                {"name": "sort", "description": "Sort by 'score' or 'timestamp'"},
                {"name": "sort_dir", "description": "'asc' or 'desc'"},
                {"name": "count", "description": "Results per page (max 100)"}
            ],
            "pre_checks": [
                "Verify bot has search:read scope",
                "Results limited to bot-accessible channels"
            ],
            "steps": [
                "Call search.messages with query",
                "Process messages.matches array",
                "Extract text, channel, user, permalink",
                "Paginate if needed"
            ],
            "verification_checks": [
                "Response ok is true",
                "Results are relevant to query",
                "Permalinks are valid"
            ],
            "common_failure_modes": [
                {"issue": "No results for known message", "why_it_happens": ["Bot lacks channel access", "Search only covers bot-accessible channels"], "safe_recovery": ["Ensure bot is in relevant channels"]},
                {"issue": "Missing search:read scope", "why_it_happens": ["Scope not added during setup"], "safe_recovery": ["Add scope and reinstall app"]}
            ],
            "missing_information_behavior": [
                "If query too broad, suggest adding modifiers",
                "If no results, suggest broadening query"
            ],
            "confirmation_required_when": [],
            "escalate_when": [],
            "source_refs": [
                {"label": "search.messages", "url": "https://api.slack.com/methods/search.messages"}
            ],
            "confidence": "high"
        },
        {
            "id": "slack-create-channel",
            "task_name": "Create a Channel",
            "goal": "Create a new public or private Slack channel",
            "when_to_use": [
                "Setting up a channel for a project or incident",
                "Automating channel creation in a workflow"
            ],
            "when_not_to_use": [
                "Channel with same purpose already exists",
                "A DM or group DM would suffice"
            ],
            "risk_level": "requires_escalation",
            "required_inputs": [
                {"name": "name", "description": "Channel name (lowercase, hyphens, max 80 chars)", "required": True}
            ],
            "optional_inputs": [
                {"name": "is_private", "description": "Create private channel (default false)"},
                {"name": "team_id", "description": "Team ID for Enterprise Grid"},
                {"name": "description", "description": "Channel purpose"}
            ],
            "pre_checks": [
                "Verify bot has channels:manage scope",
                "Check if channel name already exists",
                "Confirm naming convention"
            ],
            "steps": [
                "Check no existing channel with same name",
                "Confirm name and type with operator",
                "Call conversations.create",
                "Set topic and purpose",
                "Invite initial members if needed"
            ],
            "verification_checks": [
                "Response ok with new channel ID",
                "Channel appears in workspace",
                "Topic and purpose set correctly"
            ],
            "common_failure_modes": [
                {"issue": "name_taken error", "why_it_happens": ["Channel name already in use (including archived)"], "safe_recovery": ["Check if existing is archived; unarchive or rename"]},
                {"issue": "restricted_action error", "why_it_happens": ["Admin restricted bot channel creation"], "safe_recovery": ["Escalate to workspace admin"]}
            ],
            "missing_information_behavior": [
                "If name not provided, ask for it",
                "If public vs private unspecified, ask"
            ],
            "confirmation_required_when": [
                "Always — affects workspace organization"
            ],
            "escalate_when": [
                "Always — escalation-level action",
                "Creating private channels",
                "Bulk channel creation"
            ],
            "source_refs": [
                {"label": "conversations.create", "url": "https://api.slack.com/methods/conversations.create"},
                {"label": "Channel Management", "url": "https://api.slack.com/docs/conversations-api"}
            ],
            "confidence": "high"
        },
        {
            "id": "slack-manage-channel-membership",
            "task_name": "Manage Channel Membership",
            "goal": "Invite or remove members from a Slack channel",
            "when_to_use": [
                "Onboarding a member to project channels",
                "Removing a member during off-boarding"
            ],
            "when_not_to_use": [
                "User can self-join a public channel",
                "Channel is public and user can join via UI"
            ],
            "risk_level": "requires_escalation",
            "required_inputs": [
                {"name": "channel", "description": "Channel ID", "required": True},
                {"name": "users", "description": "User ID(s) to invite or remove", "required": True}
            ],
            "optional_inputs": [
                {"name": "action", "description": "'invite' or 'kick' (default: invite)"}
            ],
            "pre_checks": [
                "Verify bot has channels:manage scope",
                "Confirm channel exists and bot is member",
                "Validate target users are workspace members"
            ],
            "steps": [
                "Confirm action, channel, and users with operator",
                "Call conversations.invite or conversations.kick",
                "Verify membership change in response",
                "Optionally notify channel"
            ],
            "verification_checks": [
                "Response ok is true",
                "conversations.members confirms change",
                "No permission errors"
            ],
            "common_failure_modes": [
                {"issue": "already_in_channel on invite", "why_it_happens": ["User already a member"], "safe_recovery": ["Desired state achieved; continue"]},
                {"issue": "not_in_channel on kick", "why_it_happens": ["User not a member"], "safe_recovery": ["Desired state achieved; continue"]}
            ],
            "missing_information_behavior": [
                "If user given by name, look up ID",
                "If action unspecified, ask invite or remove"
            ],
            "confirmation_required_when": [
                "Always — affects channel access"
            ],
            "escalate_when": [
                "Always — escalation-level action",
                "Removing members from channels",
                "Bulk membership changes"
            ],
            "source_refs": [
                {"label": "conversations.invite", "url": "https://api.slack.com/methods/conversations.invite"},
                {"label": "conversations.kick", "url": "https://api.slack.com/methods/conversations.kick"}
            ],
            "confidence": "high"
        }
    ],
    "operating_rules": {
        "always_do": [
            "Verify bot is in target channel before posting",
            "Include plain text fallback with Block Kit",
            "Respect rate limits with Retry-After backoff",
            "Verify webhook signatures before processing",
            "Acknowledge Events API within 3 seconds"
        ],
        "never_do": [
            "Never post to public channels without confirmation",
            "Never use @here/@channel without approval",
            "Never store bot tokens in client code",
            "Never kick members without escalation",
            "Never ignore 429 rate limit responses"
        ],
        "verify_before_write_actions": [
            "Confirm target channel name and ID match",
            "Review message content and tone",
            "Verify bot has required scopes"
        ],
        "verify_after_write_actions": [
            "Check response ok field is true",
            "Verify message appears in channel",
            "Confirm membership changes took effect"
        ],
        "ambiguity_rules": [
            "If channel given by name, resolve to ID first",
            "If no channel specified, ask where to send",
            "If message has mentions, highlight and confirm"
        ],
        "environment_rules": [
            "No sandbox — all calls affect real workspace",
            "Use a test workspace for development",
            "Bot tokens are workspace-specific"
        ],
        "retry_idempotency_rules": [
            "chat.postMessage is not idempotent",
            "Use event_id for Events API deduplication",
            "Track rate limits per-method separately"
        ]
    },
    "decision_guide": [
        {
            "decision": "Bot token (xoxb) vs User token (xoxp)",
            "choose_when": ["Bot: automated messages and bot actions", "User: actions attributed to a specific person"],
            "avoid_when": ["Bot: action should appear from a user", "User: automated workflows from the bot"],
            "prefer_instead": ["Bot tokens for most automation", "User tokens only when attribution matters"],
            "escalate_when": ["Unsure whether action should come from bot or user"]
        },
        {
            "decision": "Events API vs Socket Mode",
            "choose_when": ["Events API: public HTTPS endpoint available", "Socket Mode: local dev or no public URL"],
            "avoid_when": ["Events API: no public endpoint", "Socket Mode: high-volume production"],
            "prefer_instead": ["Events API for production", "Socket Mode for development"],
            "escalate_when": ["Event processing needs exceed both approaches"]
        }
    ],
    "troubleshooting": [
        {
            "issue": "Bot cannot post to a channel",
            "signals": ["channel_not_found or not_in_channel error"],
            "likely_causes": ["Bot not invited to channel", "Missing chat:write scope", "Channel is archived"],
            "recommended_actions": ["Invite bot: /invite @botname", "Add chat:write scope and reinstall"],
            "do_not_do": ["Do not retry without fixing root cause"],
            "escalate_when": ["Bot invited but still cannot post"],
            "source_refs": [{"label": "chat.postMessage", "url": "https://api.slack.com/methods/chat.postMessage"}]
        },
        {
            "issue": "Events are not being received",
            "signals": ["No events at endpoint or Socket Mode connection"],
            "likely_causes": ["URL verification not handled", "Event subscriptions not configured", "Endpoint too slow"],
            "recommended_actions": ["Handle url_verification challenge", "Check Event Subscriptions in app settings"],
            "do_not_do": ["Do not increase response time — acknowledge immediately"],
            "escalate_when": ["Events missing despite correct configuration"],
            "source_refs": [{"label": "Events API Guide", "url": "https://api.slack.com/events-api"}]
        },
        {
            "issue": "Rate limiting across API methods",
            "signals": ["HTTP 429 with Retry-After header"],
            "likely_causes": ["Burst of calls exceeding tier limit", "Polling instead of using events"],
            "recommended_actions": ["Implement per-method backoff", "Switch from polling to Events API"],
            "do_not_do": ["Do not distribute calls across tokens to circumvent limits"],
            "escalate_when": ["Limits hit despite proper throttling"],
            "source_refs": [{"label": "Rate Limiting", "url": "https://api.slack.com/docs/rate-limits"}]
        }
    ],
    "references_by_topic": [
        {
            "topic": "Messaging",
            "references": [
                {"label": "chat.postMessage", "url": "https://api.slack.com/methods/chat.postMessage", "reason": "Primary method for sending messages"},
                {"label": "Block Kit Builder", "url": "https://app.slack.com/block-kit-builder", "reason": "Visual tool for rich message layouts"},
                {"label": "Message Formatting", "url": "https://api.slack.com/reference/surfaces/formatting", "reason": "Text formatting syntax"}
            ]
        },
        {
            "topic": "Channels & Conversations",
            "references": [
                {"label": "Conversations API", "url": "https://api.slack.com/docs/conversations-api", "reason": "Channel management operations"},
                {"label": "conversations.list", "url": "https://api.slack.com/methods/conversations.list", "reason": "List workspace channels"},
                {"label": "conversations.history", "url": "https://api.slack.com/methods/conversations.history", "reason": "Read channel message history"}
            ]
        },
        {
            "topic": "Events & Interactivity",
            "references": [
                {"label": "Events API", "url": "https://api.slack.com/events-api", "reason": "Real-time event subscriptions"},
                {"label": "Socket Mode", "url": "https://api.slack.com/apis/connections/socket", "reason": "WebSocket event delivery"},
                {"label": "App Manifest", "url": "https://api.slack.com/reference/manifests", "reason": "Declarative app configuration"}
            ]
        }
    ],
    "implementation_notes": {
        "customer_page_must_include": [
            "App creation and OAuth scope setup",
            "Message posting with Block Kit formatting",
            "Channel membership requirements for bot access",
            "Event handling for Events API and Socket Mode",
            "Rate limit awareness and backoff",
            "Message search capabilities and limitations"
        ],
        "doc_gaps_or_unclear_areas": [
            "Per-method rate limit tiers not aggregated",
            "Socket Mode reconnection best practices minimal",
            "Enterprise Grid token scoping is complex"
        ]
    }
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
