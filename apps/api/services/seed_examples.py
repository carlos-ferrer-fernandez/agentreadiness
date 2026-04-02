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
        "summary": "Stripe is a payments infrastructure platform providing APIs for accepting payments, managing subscriptions, issuing refunds, and handling financial workflows programmatically.",
        "agent_fit_summary": "Agents can safely read payment data, create payment intents, and manage subscriptions. Refunds and cancellations require human confirmation. Account-level configuration changes require escalation.",
        "high_risk_notice": "Live-mode API keys process real money. Never use live keys in test workflows. Refunds, subscription cancellations, and payout schedule changes are irreversible or have delayed reversal windows.",
        "primary_cta_label": "View Full Operating Guide"
    },
    "agent_scope": {
        "safe_without_approval": [
            {"action": "Retrieve payment intent, charge, or customer details", "reason": "Read-only, no side effects", "risk_level": "safe_read"},
            {"action": "List invoices, subscriptions, or transactions", "reason": "Read-only enumeration with pagination", "risk_level": "safe_read"},
            {"action": "Retrieve account balance and payout history", "reason": "Read-only financial summary", "risk_level": "safe_read"},
            {"action": "Create a payment intent in test mode", "reason": "Test mode processes no real money", "risk_level": "safe_write"}
        ],
        "requires_confirmation": [
            {"action": "Issue a refund (full or partial)", "reason": "Moves money back to the customer; cannot be undone once processed", "risk_level": "requires_confirmation", "confirmation_needed_for": ["Refund amount and currency", "Charge ID being refunded", "Whether full or partial refund"]},
            {"action": "Cancel a subscription", "reason": "Ends recurring billing; customer loses access", "risk_level": "requires_confirmation", "confirmation_needed_for": ["Subscription ID", "Whether to cancel immediately or at period end", "Whether to issue a prorated refund"]},
            {"action": "Create a payment intent in live mode", "reason": "Will charge a real payment method", "risk_level": "requires_confirmation", "confirmation_needed_for": ["Amount and currency", "Customer identity", "Payment method to charge"]},
            {"action": "Create or modify a subscription", "reason": "Commits to recurring charges on a real payment method", "risk_level": "requires_confirmation", "confirmation_needed_for": ["Price ID and billing interval", "Customer ID", "Trial period configuration"]}
        ],
        "requires_escalation": [
            {"action": "Change payout schedule or bank account", "reason": "Affects how and when funds reach the business bank account", "risk_level": "requires_escalation", "escalate_when": ["Any modification to payout settings", "Adding or removing bank accounts"]},
            {"action": "Modify account-level settings or API key permissions", "reason": "Affects the entire Stripe account security posture", "risk_level": "requires_escalation", "escalate_when": ["Changing webhook endpoints", "Creating or revoking restricted API keys", "Modifying account business details"]},
            {"action": "Delete a customer record", "reason": "Permanently removes all associated payment methods, subscriptions, and history", "risk_level": "requires_escalation", "escalate_when": ["Any customer deletion request", "Bulk data operations"]}
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
            "Custom fraud rule authoring (Radar rules are Dashboard-only)",
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
            "Live mode API keys for production (sk_live_..., requires account activation)"
        ],
        "authentication": {
            "methods": [
                "Secret API key in Authorization: Bearer header",
                "Restricted API keys with granular per-resource permissions",
                "Publishable key (pk_...) for client-side Stripe.js only"
            ],
            "required_secrets_or_tokens": [
                "STRIPE_SECRET_KEY (sk_test_... or sk_live_...)",
                "STRIPE_WEBHOOK_SECRET (whsec_...) for webhook signature verification",
                "STRIPE_PUBLISHABLE_KEY (pk_...) if using client-side Elements"
            ],
            "permission_notes": [
                "Secret key has full account access by default",
                "Restricted keys can limit to specific resources (e.g., charges:write, customers:read)",
                "Connect OAuth tokens provide access to connected accounts"
            ],
            "environment_notes": [
                "Test mode and live mode keys are completely separate; data does not overlap",
                "Webhook signing secrets are per-endpoint; use the correct one for each URL",
                "API versioning is controlled via the Stripe-Version header or Dashboard settings"
            ]
        },
        "initial_setup_steps": [
            "Install the Stripe SDK: pip install stripe (Python) or npm install stripe (Node.js)",
            "Set STRIPE_SECRET_KEY as an environment variable",
            "Verify connectivity: call stripe.Account.retrieve() or GET /v1/account",
            "Register a webhook endpoint in the Dashboard and store the signing secret",
            "Run a test payment using card number 4242424242424242 in test mode"
        ]
    },
    "task_playbooks": [
        {
            "id": "stripe-accept-payment",
            "task_name": "Accept a Payment",
            "goal": "Charge a customer for a one-time purchase using a PaymentIntent",
            "when_to_use": [
                "Customer is making a one-time purchase",
                "Checkout flow requires server-side payment creation",
                "Payment amount and currency are known"
            ],
            "when_not_to_use": [
                "Recurring billing (use subscriptions instead)",
                "Pre-built checkout UI is preferred (use Stripe Checkout Sessions)",
                "Amount is not yet determined (use SetupIntents to save a card first)"
            ],
            "risk_level": "requires_confirmation",
            "required_inputs": [
                {"name": "amount", "description": "Payment amount in smallest currency unit (e.g., 2500 for $25.00 USD)", "required": True},
                {"name": "currency", "description": "Three-letter ISO currency code, lowercase (e.g., usd, eur)", "required": True},
                {"name": "payment_method_types", "description": "Accepted payment methods (e.g., ['card'])", "required": True}
            ],
            "optional_inputs": [
                {"name": "customer", "description": "Stripe customer ID (cus_...) to associate the payment"},
                {"name": "metadata", "description": "Key-value pairs for internal tracking (e.g., order_id)"},
                {"name": "idempotency_key", "description": "Unique key to prevent duplicate charges on retry"}
            ],
            "pre_checks": [
                "Confirm you are using the correct mode (test vs live) API key",
                "Validate that the amount is a positive integer in the smallest currency unit",
                "Verify the currency is supported in the Stripe account's country"
            ],
            "steps": [
                "Create a PaymentIntent: POST /v1/payment_intents with amount, currency, and payment_method_types",
                "Return the client_secret to the frontend for Stripe.js confirmation",
                "Client confirms the PaymentIntent using stripe.confirmCardPayment(clientSecret)",
                "Stripe handles 3D Secure authentication if required",
                "Listen for the payment_intent.succeeded webhook to fulfill the order"
            ],
            "verification_checks": [
                "PaymentIntent status is 'succeeded'",
                "Webhook payment_intent.succeeded is received and processed",
                "Charge object shows amount_captured equals the intended amount",
                "No duplicate charges exist for the same idempotency key"
            ],
            "common_failure_modes": [
                {"issue": "Card declined", "why_it_happens": ["Insufficient funds", "Incorrect card number", "Card reported lost or stolen", "Issuer decline for suspicious activity"], "safe_recovery": ["Check the decline_code in the error response", "Prompt customer to try a different payment method", "Do not retry the same card without customer action"]},
                {"issue": "3D Secure authentication fails", "why_it_happens": ["Customer abandons the authentication flow", "Bank authentication service is unavailable"], "safe_recovery": ["PaymentIntent moves to requires_payment_method status", "Prompt the customer to retry or use a different card"]},
                {"issue": "Network timeout during creation", "why_it_happens": ["Connectivity issue between server and Stripe"], "safe_recovery": ["Retry with the same idempotency key to prevent duplicate charges", "Check the PaymentIntent list to see if it was created"]}
            ],
            "missing_information_behavior": [
                "If amount is missing, do not proceed; ask the user for the charge amount",
                "If currency is missing, default to the account's default currency if known, otherwise ask"
            ],
            "confirmation_required_when": [
                "Creating a PaymentIntent in live mode (real money)",
                "Amount exceeds a threshold set by the business"
            ],
            "escalate_when": [
                "Customer disputes the charge amount",
                "Payment is for an unusually large amount with no prior history"
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
                "Customer is signing up for a recurring plan",
                "Billing should happen automatically on a schedule",
                "A Price object already exists in Stripe for the plan"
            ],
            "when_not_to_use": [
                "One-time purchase (use PaymentIntent instead)",
                "Metered billing where usage hasn't been reported yet (set up the subscription but configure metered pricing)",
                "Customer only wants to save a card for later (use SetupIntent)"
            ],
            "risk_level": "requires_confirmation",
            "required_inputs": [
                {"name": "customer", "description": "Stripe customer ID (cus_...) with an attached payment method", "required": True},
                {"name": "price", "description": "Stripe price ID (price_...) for the recurring plan", "required": True}
            ],
            "optional_inputs": [
                {"name": "trial_period_days", "description": "Number of free trial days before first charge"},
                {"name": "coupon", "description": "Coupon ID to apply a discount"},
                {"name": "proration_behavior", "description": "How to handle mid-cycle plan changes (create_prorations, none, always_invoice)"}
            ],
            "pre_checks": [
                "Verify the customer exists and has a valid default payment method",
                "Confirm the price ID exists and matches the intended plan",
                "Check whether the customer already has an active subscription for this price"
            ],
            "steps": [
                "Retrieve or create the Customer object with a default payment method",
                "Create the Subscription: POST /v1/subscriptions with customer and items[0][price]",
                "If trial_period_days is set, Stripe delays the first invoice",
                "Handle the invoice.payment_succeeded webhook to confirm activation",
                "Handle customer.subscription.updated for lifecycle changes"
            ],
            "verification_checks": [
                "Subscription status is 'active' (or 'trialing' if trial is set)",
                "First invoice status is 'paid'",
                "Customer's default payment method was charged correctly"
            ],
            "common_failure_modes": [
                {"issue": "Payment method fails on first invoice", "why_it_happens": ["Card expired or insufficient funds", "No default payment method on customer"], "safe_recovery": ["Subscription enters 'incomplete' status", "Use the latest_invoice.payment_intent to retry payment", "Prompt customer to update their payment method"]},
                {"issue": "Duplicate subscription created", "why_it_happens": ["Retry without checking for existing subscription"], "safe_recovery": ["Cancel the duplicate immediately", "Use metadata or idempotency keys to prevent duplicates"]}
            ],
            "missing_information_behavior": [
                "If customer ID is missing, search by email or ask for customer identification",
                "If price ID is unknown, list available prices and ask which plan to use"
            ],
            "confirmation_required_when": [
                "Creating any subscription in live mode",
                "Changing a subscription's price (upgrade or downgrade)",
                "Cancelling a subscription"
            ],
            "escalate_when": [
                "Customer requests a custom plan not available as a standard Price",
                "Subscription involves a multi-year commitment"
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
                "Customer requests a refund for a completed charge",
                "Order was cancelled after payment was captured",
                "Partial refund is needed for a price adjustment"
            ],
            "when_not_to_use": [
                "Payment is still in requires_confirmation or processing state (cancel the PaymentIntent instead)",
                "Charge is older than 180 days (Stripe refund window has closed)",
                "Dispute or chargeback is already filed (respond to the dispute instead)"
            ],
            "risk_level": "requires_confirmation",
            "required_inputs": [
                {"name": "charge_or_payment_intent", "description": "The charge ID (ch_...) or PaymentIntent ID (pi_...) to refund", "required": True}
            ],
            "optional_inputs": [
                {"name": "amount", "description": "Amount to refund in smallest currency unit; omit for full refund"},
                {"name": "reason", "description": "Reason code: duplicate, fraudulent, or requested_by_customer"}
            ],
            "pre_checks": [
                "Verify the charge exists and its status is 'succeeded'",
                "Confirm the charge is within the 180-day refund window",
                "Check if any previous refunds have been issued against this charge",
                "Calculate the remaining refundable amount if partial refunds exist"
            ],
            "steps": [
                "Retrieve the charge to verify status and refundable amount",
                "Confirm the refund details with the human operator (amount, reason)",
                "Create the Refund: POST /v1/refunds with charge and optional amount",
                "Monitor the refund status (may take 5-10 business days to appear on statement)",
                "Handle the charge.refunded webhook for internal bookkeeping"
            ],
            "verification_checks": [
                "Refund object status is 'succeeded'",
                "Charge object amount_refunded reflects the correct total",
                "Webhook charge.refunded is received",
                "Internal order system is updated to reflect the refund"
            ],
            "common_failure_modes": [
                {"issue": "Refund exceeds available amount", "why_it_happens": ["Previous partial refunds already consumed the charge amount", "Attempting to refund more than the original charge"], "safe_recovery": ["Check the charge's amount_refunded field before creating the refund", "Reduce refund amount to the remaining balance"]},
                {"issue": "Charge is too old to refund", "why_it_happens": ["Charge is older than 180 days"], "safe_recovery": ["Issue a credit or manual bank transfer instead", "Escalate to finance team"]}
            ],
            "missing_information_behavior": [
                "If charge ID is missing, ask for the order ID or customer email to look up the charge",
                "If amount is not specified, confirm whether full or partial refund is intended"
            ],
            "confirmation_required_when": [
                "Always; refunds move real money and cannot be cancelled once processing"
            ],
            "escalate_when": [
                "Refund amount exceeds a business-defined threshold",
                "Multiple refunds requested for the same customer in a short period",
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
            "goal": "Diagnose why a payment attempt failed and determine the appropriate next step",
            "when_to_use": [
                "A payment_intent.payment_failed webhook is received",
                "Customer reports that their payment did not go through",
                "Invoice shows status 'open' or 'past_due'"
            ],
            "when_not_to_use": [
                "Payment succeeded but customer claims it did not (check for webhooks first)",
                "Dispute or fraud investigation (use the Disputes workflow)"
            ],
            "risk_level": "safe_read",
            "required_inputs": [
                {"name": "payment_intent_id_or_invoice_id", "description": "The PaymentIntent (pi_...) or Invoice (in_...) ID to investigate", "required": True}
            ],
            "optional_inputs": [
                {"name": "customer_email", "description": "Customer email for looking up related charges and payment methods"}
            ],
            "pre_checks": [
                "Retrieve the PaymentIntent or Invoice to get the current status",
                "Check if the failure is on the latest attempt or a previous one"
            ],
            "steps": [
                "Retrieve the PaymentIntent: GET /v1/payment_intents/{id}?expand[]=latest_charge",
                "Examine last_payment_error for the decline code and message",
                "Check the Charge object's outcome.reason and outcome.risk_level",
                "If the issue is card_declined, note the specific decline_code (e.g., insufficient_funds, lost_card)",
                "Determine the appropriate recovery action based on the decline code",
                "Document findings and recommended next steps"
            ],
            "verification_checks": [
                "Root cause is identified from the decline code or error message",
                "Recommended action is appropriate for the failure type",
                "No additional failed attempts are queued without addressing the root cause"
            ],
            "common_failure_modes": [
                {"issue": "Generic decline with no specific code", "why_it_happens": ["Issuing bank does not provide a detailed reason"], "safe_recovery": ["Ask customer to contact their bank", "Try a different payment method"]},
                {"issue": "Authentication required but not completed", "why_it_happens": ["3D Secure challenge was not presented to the customer", "Customer abandoned the authentication"], "safe_recovery": ["Ensure the frontend handles requires_action status", "Re-attempt with proper 3DS flow"]}
            ],
            "missing_information_behavior": [
                "If no PaymentIntent ID is available, search by customer email or metadata",
                "If the decline code is unfamiliar, reference Stripe's decline code documentation"
            ],
            "confirmation_required_when": [],
            "escalate_when": [
                "Failure is flagged as fraudulent by Stripe Radar",
                "Multiple customers report the same failure simultaneously (possible system issue)",
                "Decline code suggests account-level issues (e.g., account_closed)"
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
                "Setting up a new webhook endpoint to receive Stripe events",
                "Debugging why a webhook event is not being processed",
                "Adding a handler for a new event type"
            ],
            "when_not_to_use": [
                "Polling for status instead of using webhooks (webhooks are the recommended approach)",
                "Event types that are not relevant to the integration"
            ],
            "risk_level": "safe_write",
            "required_inputs": [
                {"name": "endpoint_url", "description": "The HTTPS URL that will receive webhook POST requests", "required": True},
                {"name": "events", "description": "List of event types to subscribe to (e.g., payment_intent.succeeded, invoice.paid)", "required": True}
            ],
            "optional_inputs": [
                {"name": "api_version", "description": "Pin the webhook to a specific API version for consistent payload shape"}
            ],
            "pre_checks": [
                "Endpoint URL must be HTTPS (Stripe rejects HTTP in production)",
                "Endpoint must respond with 2xx status within 20 seconds",
                "Webhook signing secret is available for signature verification"
            ],
            "steps": [
                "Register the webhook endpoint: POST /v1/webhook_endpoints with url and enabled_events",
                "Store the returned webhook signing secret (whsec_...) securely",
                "In the handler, verify the webhook signature using stripe.Webhook.construct_event()",
                "Parse the event type and dispatch to the appropriate handler",
                "Respond with 200 immediately; process the event asynchronously if needed",
                "Implement idempotency: check event.id to avoid duplicate processing"
            ],
            "verification_checks": [
                "Webhook endpoint shows 'enabled' status in the Stripe Dashboard",
                "Test events (sent via Dashboard or CLI) are received and processed",
                "Signature verification passes for all incoming events",
                "Handler returns 2xx within 20 seconds for all event types"
            ],
            "common_failure_modes": [
                {"issue": "Signature verification fails", "why_it_happens": ["Using the wrong webhook signing secret (test vs live)", "Request body was parsed or modified before verification", "Clock skew between servers"], "safe_recovery": ["Use the raw request body for signature verification", "Double-check the endpoint secret in the Dashboard", "Ensure server clock is synchronized via NTP"]},
                {"issue": "Events delivered out of order", "why_it_happens": ["Stripe does not guarantee event ordering", "Retry deliveries can arrive after newer events"], "safe_recovery": ["Design handlers to be idempotent", "Use the event object's created timestamp or resource state to determine action", "Do not assume sequential delivery"]},
                {"issue": "Endpoint returns 5xx causing retries", "why_it_happens": ["Handler throws an unhandled exception", "Downstream service is unavailable"], "safe_recovery": ["Add error handling around the handler logic", "Return 200 and queue the event for async retry internally", "Stripe retries failed deliveries for up to 3 days"]}
            ],
            "missing_information_behavior": [
                "If the webhook signing secret is not available, retrieve it from the Dashboard or re-create the endpoint",
                "If the event type is unrecognized, log it and return 200 to prevent retries"
            ],
            "confirmation_required_when": [],
            "escalate_when": [
                "Webhook endpoint has been disabled due to repeated failures",
                "Suspected replay attack (signature verification consistently fails from unknown sources)"
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
            "Use idempotency keys for all POST requests to prevent duplicate charges",
            "Verify webhook signatures before processing any event",
            "Use test mode API keys during development and testing",
            "Store API keys in environment variables, never in code or version control",
            "Include amount in the smallest currency unit (e.g., cents for USD)",
            "Expand related objects in API calls when you need nested data (e.g., ?expand[]=latest_charge)"
        ],
        "never_do": [
            "Never expose secret API keys in client-side code, logs, or error messages",
            "Never use live mode keys in test or staging environments",
            "Never store or log raw card numbers, CVVs, or full card details",
            "Never process a refund without confirming the amount and charge with the operator",
            "Never assume a payment succeeded without checking the PaymentIntent status or receiving a webhook",
            "Never retry a failed payment without addressing the root cause of the decline"
        ],
        "verify_before_write_actions": [
            "Confirm you are operating in the correct mode (test vs live)",
            "Verify the customer ID and payment method are correct before charging",
            "Check for existing subscriptions before creating a new one to avoid duplicates",
            "Validate refund amount does not exceed the remaining refundable balance"
        ],
        "verify_after_write_actions": [
            "Check the returned object's status field for success confirmation",
            "Verify the amount_captured or amount_refunded matches expectations",
            "Confirm webhook delivery for asynchronous operations (payments, invoices)"
        ],
        "ambiguity_rules": [
            "If the user says 'charge' without specifying one-time vs recurring, ask to clarify",
            "If no currency is specified, confirm before defaulting to the account's default currency",
            "If a refund reason is unclear, ask whether it is duplicate, fraudulent, or customer-requested"
        ],
        "environment_rules": [
            "Test mode: use sk_test_ keys, test card numbers (4242...), and test webhook endpoints",
            "Live mode: use sk_live_ keys only after account activation and human confirmation",
            "Webhook endpoints must use HTTPS in production; HTTP is allowed only in local development with the Stripe CLI"
        ],
        "retry_idempotency_rules": [
            "Always include an Idempotency-Key header on POST requests",
            "Use the same idempotency key when retrying a failed request to prevent duplicates",
            "Idempotency keys expire after 24 hours; generate a new one for genuinely new requests",
            "GET and DELETE requests are inherently idempotent and do not need idempotency keys"
        ]
    },
    "decision_guide": [
        {
            "decision": "PaymentIntent API vs Stripe Checkout Sessions",
            "choose_when": ["You need full control over the payment UI", "The application already has a custom checkout form", "You need to support complex payment flows (split payments, delayed capture)"],
            "avoid_when": ["A pre-built, hosted checkout page would be faster to implement", "PCI compliance scope is a concern (Checkout minimizes it)"],
            "prefer_instead": ["Stripe Checkout Sessions for standard e-commerce flows", "Stripe Elements for embedded UI components with less backend work"],
            "escalate_when": ["The payment flow involves regulatory requirements you are unsure about"]
        },
        {
            "decision": "Immediate cancellation vs end-of-period cancellation for subscriptions",
            "choose_when": ["Customer explicitly requests immediate cancellation and refund", "Subscription was created in error"],
            "avoid_when": ["Customer has prepaid for the current period and expects access until it ends", "Business policy requires end-of-period cancellation by default"],
            "prefer_instead": ["cancel_at_period_end: true to let the subscription run through the paid period"],
            "escalate_when": ["Customer is requesting both immediate cancellation and a full refund", "Cancellation involves a contractual commitment"]
        },
        {
            "decision": "Full refund vs partial refund",
            "choose_when": ["Full: the entire order is being returned or was never fulfilled", "Partial: only part of the order is being returned or a price adjustment is needed"],
            "avoid_when": ["A credit or coupon would better serve the customer's needs", "The charge has an active dispute"],
            "prefer_instead": ["Credit notes or coupons for goodwill adjustments", "Dispute response for chargeback situations"],
            "escalate_when": ["Refund amount exceeds business-defined thresholds", "Customer is requesting refund for a charge older than 90 days"]
        }
    ],
    "troubleshooting": [
        {
            "issue": "Card declined errors",
            "signals": ["PaymentIntent status is requires_payment_method", "Error type is card_error with a decline_code"],
            "likely_causes": ["Insufficient funds on the card", "Card number is incorrect", "Card has been reported lost or stolen", "Issuing bank declined for suspected fraud"],
            "recommended_actions": ["Check the specific decline_code in the error response", "Ask the customer to try a different payment method", "For testing, use Stripe's test card numbers (4000000000000002 for generic decline)"],
            "do_not_do": ["Do not retry the same card immediately without customer action", "Do not expose the full decline reason to the customer (use a generic message)"],
            "escalate_when": ["Multiple customers experience the same decline code simultaneously", "The decline code is 'fraudulent' and the customer claims otherwise"],
            "source_refs": [{"label": "Decline Codes Reference", "url": "https://docs.stripe.com/declines/codes"}]
        },
        {
            "issue": "Webhook signature verification failure",
            "signals": ["stripe.Webhook.construct_event raises SignatureVerificationError", "HTTP 400 responses from webhook handler"],
            "likely_causes": ["Using the wrong webhook signing secret (test endpoint secret vs live)", "Request body was parsed or modified before signature check", "Significant clock skew on the server"],
            "recommended_actions": ["Verify the signing secret matches the endpoint in the Dashboard", "Use the raw request body (not parsed JSON) for verification", "Synchronize server clock via NTP"],
            "do_not_do": ["Do not disable signature verification to work around the error", "Do not parse the request body before verifying the signature"],
            "escalate_when": ["Verification fails for all events, suggesting a configuration issue", "Unexpected events arrive that do not correspond to any known Stripe activity"],
            "source_refs": [{"label": "Webhook Signatures", "url": "https://docs.stripe.com/webhooks/signatures"}]
        },
        {
            "issue": "Subscription stuck in incomplete status",
            "signals": ["Subscription status is 'incomplete' instead of 'active'", "First invoice shows as 'open' or 'draft'"],
            "likely_causes": ["Initial payment failed (card declined, authentication required)", "Payment method was not attached to the customer before subscription creation", "3D Secure authentication was not completed by the customer"],
            "recommended_actions": ["Check the subscription's latest_invoice and its payment_intent for the specific failure", "Have the customer complete authentication or update their payment method", "If the subscription is abandoned, cancel it to avoid retries"],
            "do_not_do": ["Do not create a new subscription without cancelling the incomplete one", "Do not assume the subscription will self-resolve without action"],
            "escalate_when": ["Multiple subscriptions are stuck in incomplete state across different customers"],
            "source_refs": [{"label": "Subscription Statuses", "url": "https://docs.stripe.com/billing/subscriptions/overview#subscription-statuses"}]
        }
    ],
    "references_by_topic": [
        {
            "topic": "Payments",
            "references": [
                {"label": "Payment Intents API", "url": "https://docs.stripe.com/api/payment_intents", "reason": "Core API for creating and managing payments"},
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
                {"label": "Stripe CLI", "url": "https://docs.stripe.com/stripe-cli", "reason": "Local webhook testing and event forwarding"}
            ]
        }
    ],
    "implementation_notes": {
        "customer_page_must_include": [
            "API key management and test vs live mode distinction",
            "PaymentIntent creation and confirmation flow",
            "Subscription lifecycle management including upgrades, downgrades, and cancellations",
            "Webhook setup, signature verification, and idempotent event handling",
            "Refund workflow with pre-checks and operator confirmation",
            "Error handling patterns for decline codes and authentication failures"
        ],
        "doc_gaps_or_unclear_areas": [
            "Country-specific payment method availability is spread across multiple documentation pages",
            "Connect fee calculation and payout timing examples could be more detailed",
            "Radar fraud rule configuration is Dashboard-only; no API documentation for custom rules"
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
        "summary": "Vercel is a cloud platform for frontend frameworks that provides instant deployments, serverless functions, edge computing, and a global CDN. It is the company behind Next.js.",
        "agent_fit_summary": "Agents can safely check deployment statuses and read logs. Deployments and environment variable changes require confirmation. Domain configuration and team settings require escalation.",
        "high_risk_notice": "Production deployments are immediately live to end users. Incorrect environment variables or premature deployments can cause downtime. Rollbacks replace the current production deployment.",
        "primary_cta_label": "View Full Operating Guide"
    },
    "agent_scope": {
        "safe_without_approval": [
            {"action": "Check deployment status and build logs", "reason": "Read-only inspection of existing deployments", "risk_level": "safe_read"},
            {"action": "List projects, deployments, and environment variables", "reason": "Read-only enumeration", "risk_level": "safe_read"},
            {"action": "View domain configuration", "reason": "Read-only DNS and domain inspection", "risk_level": "safe_read"},
            {"action": "Read serverless function invocation logs", "reason": "Read-only observability data", "risk_level": "safe_read"}
        ],
        "requires_confirmation": [
            {"action": "Deploy a project to production", "reason": "Immediately serves traffic to end users", "risk_level": "requires_confirmation", "confirmation_needed_for": ["Target environment (production vs preview)", "Git ref or branch to deploy", "Project name"]},
            {"action": "Rollback to a previous deployment", "reason": "Replaces the current production build; may cause feature regression", "risk_level": "requires_confirmation", "confirmation_needed_for": ["Deployment ID to roll back to", "Confirmation that the target deployment is known-good"]},
            {"action": "Create or update environment variables", "reason": "Incorrect values can break the application at runtime", "risk_level": "requires_confirmation", "confirmation_needed_for": ["Variable name and value", "Target environments (production, preview, development)", "Whether it replaces an existing value"]},
            {"action": "Trigger a redeployment", "reason": "Creates a new build and deployment using current configuration", "risk_level": "requires_confirmation", "confirmation_needed_for": ["Project and target environment", "Reason for redeployment"]}
        ],
        "requires_escalation": [
            {"action": "Configure or remove custom domains", "reason": "DNS changes affect site accessibility and SSL certificates", "risk_level": "requires_escalation", "escalate_when": ["Adding or removing a production domain", "Changing DNS records"]},
            {"action": "Modify team membership or roles", "reason": "Affects access control across all projects", "risk_level": "requires_escalation", "escalate_when": ["Adding or removing team members", "Changing member roles"]},
            {"action": "Delete a project", "reason": "Permanently removes all deployments, environment variables, and configuration", "risk_level": "requires_escalation", "escalate_when": ["Any project deletion request"]}
        ]
    },
    "suitability": {
        "best_for": [
            "Next.js, Nuxt, SvelteKit, and Astro applications",
            "Static sites and JAMstack architectures",
            "Preview deployments for pull request review workflows",
            "Serverless API routes and edge functions",
            "Global content delivery with automatic HTTPS and caching"
        ],
        "less_suitable_for": [
            "Long-running backend processes (serverless timeout limits: 10s-300s)",
            "Applications requiring persistent server state or WebSocket connections",
            "Heavy database workloads (use a dedicated database provider)",
            "Monolithic backend applications not built on supported frameworks"
        ],
        "not_clearly_supported": [
            "Custom Docker container deployments",
            "Non-JavaScript/TypeScript backend runtimes beyond Python, Go, Ruby",
            "Persistent cron jobs running longer than function timeout limits"
        ]
    },
    "setup_access": {
        "prerequisites": [
            "A Vercel account (vercel.com/signup)",
            "A Git repository on GitHub, GitLab, or Bitbucket",
            "Node.js 18+ installed locally for Vercel CLI usage"
        ],
        "accounts_and_access": [
            "Vercel Dashboard access",
            "Git provider connected to Vercel for automatic deployments",
            "API token from Settings > Tokens for programmatic access"
        ],
        "authentication": {
            "methods": [
                "Bearer token in Authorization header for REST API",
                "Vercel CLI authentication via 'vercel login'",
                "OAuth integration for Git provider connection"
            ],
            "required_secrets_or_tokens": [
                "VERCEL_TOKEN (Bearer token for API access)",
                "VERCEL_ORG_ID (team/org identifier for team-scoped requests)",
                "VERCEL_PROJECT_ID (project identifier for project-scoped requests)"
            ],
            "permission_notes": [
                "API tokens are scoped to a user or team",
                "Team roles: Owner, Member, Viewer, Developer",
                "Project-level access controls apply to environment variables"
            ],
            "environment_notes": [
                "API tokens do not expire by default but can be revoked from the Dashboard",
                "Team tokens inherit the team's permissions, not the creating user's",
                "Environment variables can be scoped to production, preview, or development"
            ]
        },
        "initial_setup_steps": [
            "Install the Vercel CLI: npm i -g vercel",
            "Authenticate: run 'vercel login'",
            "Link a project: run 'vercel' in the project directory and follow prompts",
            "Connect the Git repository in the Vercel Dashboard for automatic deployments",
            "Set required environment variables in Project Settings > Environment Variables"
        ]
    },
    "task_playbooks": [
        {
            "id": "vercel-deploy-project",
            "task_name": "Deploy a Project",
            "goal": "Deploy a project to production or create a preview deployment",
            "when_to_use": [
                "Shipping a new version of the application",
                "Triggering a deployment from CI/CD or a script",
                "Creating a preview deployment for a specific branch or commit"
            ],
            "when_not_to_use": [
                "Git-connected repo already auto-deploys on push (deployment is automatic)",
                "You only need to check the status of an existing deployment"
            ],
            "risk_level": "requires_confirmation",
            "required_inputs": [
                {"name": "project_name_or_id", "description": "Vercel project name or ID to deploy", "required": True},
                {"name": "target", "description": "Target environment: 'production' or 'preview'", "required": True}
            ],
            "optional_inputs": [
                {"name": "git_ref", "description": "Git branch, tag, or commit SHA to deploy from"},
                {"name": "environment_variables", "description": "Override environment variables for this deployment"}
            ],
            "pre_checks": [
                "Verify the project exists and the API token has deploy permissions",
                "Confirm the target environment (production deploys are immediately live)",
                "Check that required environment variables are set for the target environment",
                "Review recent deployment history for any ongoing builds"
            ],
            "steps": [
                "POST to https://api.vercel.com/v13/deployments with project name and target",
                "Include the Authorization: Bearer <token> header",
                "If deploying from a specific Git ref, include gitSource with ref and repoId",
                "Monitor the deployment: poll GET /v13/deployments/{id} until state is READY or ERROR",
                "Verify the deployment URL returns the expected content"
            ],
            "verification_checks": [
                "Deployment state is 'READY' in the API response",
                "Production URL returns expected content with HTTP 200",
                "Build logs show no errors or warnings",
                "Serverless functions in /api respond correctly"
            ],
            "common_failure_modes": [
                {"issue": "Build fails with dependency errors", "why_it_happens": ["Missing dependency in package.json", "Node.js version mismatch between local and Vercel build", "Case-sensitive file path issues (macOS vs Linux)"], "safe_recovery": ["Check build logs for the specific error", "Verify package.json has all required dependencies", "Ensure file name casing matches import statements"]},
                {"issue": "Environment variable missing at runtime", "why_it_happens": ["Variable not set for the target environment (production vs preview)", "Variable scoped to a different environment"], "safe_recovery": ["Check environment variable configuration in Project Settings", "Ensure the variable is set for the correct environment scope"]}
            ],
            "missing_information_behavior": [
                "If target is not specified, ask whether this is a production or preview deployment",
                "If git ref is not specified, deploy from the default branch"
            ],
            "confirmation_required_when": [
                "Deploying to production (immediately live to users)",
                "Deploying a branch that is not the default/main branch to production"
            ],
            "escalate_when": [
                "Deployment requires changes to build settings or framework configuration",
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
                "Current production deployment has a critical bug",
                "A deployment introduced a regression that needs immediate resolution",
                "Need to restore a previous version while fixing the issue"
            ],
            "when_not_to_use": [
                "The issue is in environment variables, not the code (fix the env vars instead)",
                "You want to undo a preview deployment (just deploy a new one)",
                "The previous deployment also had issues"
            ],
            "risk_level": "requires_confirmation",
            "required_inputs": [
                {"name": "deployment_id", "description": "The deployment ID (dpl_...) to promote back to production", "required": True},
                {"name": "project_name_or_id", "description": "Vercel project name or ID", "required": True}
            ],
            "optional_inputs": [
                {"name": "reason", "description": "Why the rollback is needed (for audit logging)"}
            ],
            "pre_checks": [
                "Verify the target deployment ID exists and was previously successful",
                "Confirm the deployment was built with the current environment variables (or acceptable ones)",
                "Check that the deployment is not too old (dependencies or external APIs may have changed)"
            ],
            "steps": [
                "Identify the target deployment: list recent deployments and find the last known-good one",
                "Confirm the deployment ID and its creation date with the operator",
                "Promote the deployment: POST to /v13/deployments with the target deployment's Git ref or use the Vercel Dashboard instant rollback",
                "Verify production URL serves the rolled-back version",
                "Document the rollback reason and notify the team"
            ],
            "verification_checks": [
                "Production URL returns the expected content from the rolled-back deployment",
                "No 5xx errors on the production domain",
                "Serverless functions respond correctly",
                "Team is notified of the rollback"
            ],
            "common_failure_modes": [
                {"issue": "Rolled-back deployment relies on environment variables that have since changed", "why_it_happens": ["Environment variables were updated between the original deployment and the rollback"], "safe_recovery": ["Compare current env vars with those at the time of the target deployment", "Restore previous env var values if needed"]},
                {"issue": "Rolled-back deployment has incompatible API contracts", "why_it_happens": ["Backend APIs have changed since the target deployment was live"], "safe_recovery": ["Verify API compatibility before completing the rollback", "May need to rollback backend changes as well"]}
            ],
            "missing_information_behavior": [
                "If no deployment ID is provided, list the 10 most recent successful deployments and ask which one to rollback to"
            ],
            "confirmation_required_when": [
                "Always; rollbacks replace the current production deployment"
            ],
            "escalate_when": [
                "The target deployment is more than 7 days old",
                "The rollback is needed due to a security incident"
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
                "Setting up a new project that requires API keys or configuration",
                "Rotating a secret or updating a connection string",
                "Adding a variable for a new feature deployment"
            ],
            "when_not_to_use": [
                "Variable contains a secret that should be in a dedicated secrets manager",
                "Changing build-time configuration that requires a framework config file change"
            ],
            "risk_level": "requires_confirmation",
            "required_inputs": [
                {"name": "project_id", "description": "Vercel project ID or name", "required": True},
                {"name": "key", "description": "Environment variable name", "required": True},
                {"name": "value", "description": "Environment variable value", "required": True},
                {"name": "target", "description": "Environments to apply to: production, preview, development (array)", "required": True}
            ],
            "optional_inputs": [
                {"name": "type", "description": "Variable type: plain, secret, encrypted (default: encrypted)"}
            ],
            "pre_checks": [
                "Check if the variable already exists to determine create vs update",
                "Verify the value format is correct for its purpose (e.g., valid URL, valid API key format)",
                "Confirm which environments should receive the variable"
            ],
            "steps": [
                "Check existing env vars: GET /v10/projects/{projectId}/env",
                "If creating: POST /v10/projects/{projectId}/env with key, value, target, and type",
                "If updating: PATCH /v10/projects/{projectId}/env/{envId} with the new value",
                "Trigger a redeployment if the variable is needed by the current deployment",
                "Verify the deployed application uses the new value correctly"
            ],
            "verification_checks": [
                "API returns the created/updated environment variable object",
                "Variable appears in the project settings with correct target environments",
                "Application functions correctly after redeployment with the new value"
            ],
            "common_failure_modes": [
                {"issue": "Variable set for wrong environment scope", "why_it_happens": ["Target array did not include 'production' or only included 'development'", "Confusion between preview and production targets"], "safe_recovery": ["Update the variable's target to include the correct environments", "Redeploy after correcting the scope"]},
                {"issue": "Value contains special characters that are not escaped", "why_it_happens": ["Connection strings or JSON values with quotes, newlines, or backslashes"], "safe_recovery": ["URL-encode or base64-encode complex values", "Use the Vercel Dashboard for values with special characters"]}
            ],
            "missing_information_behavior": [
                "If target environments are not specified, ask which environments need the variable",
                "If the value looks like a placeholder, confirm it is the actual value before setting it"
            ],
            "confirmation_required_when": [
                "Setting or changing any production environment variable",
                "Deleting an environment variable"
            ],
            "escalate_when": [
                "The variable contains a production database connection string",
                "The change affects authentication or payment processing credentials"
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
                "Diagnosing why a deployment failed",
                "Verifying production is healthy after a deploy"
            ],
            "when_not_to_use": [
                "You need to create or modify a deployment (use the Deploy playbook)"
            ],
            "risk_level": "safe_read",
            "required_inputs": [
                {"name": "deployment_id_or_url", "description": "Deployment ID (dpl_...) or deployment URL to inspect", "required": True}
            ],
            "optional_inputs": [
                {"name": "project_id", "description": "Project ID to list recent deployments if deployment ID is unknown"}
            ],
            "pre_checks": [
                "Verify the API token has read access to the project"
            ],
            "steps": [
                "Retrieve the deployment: GET /v13/deployments/{id}",
                "Check the 'readyState' field: QUEUED, BUILDING, READY, ERROR, CANCELED",
                "If BUILDING: check build logs at GET /v13/deployments/{id}/events",
                "If ERROR: examine the error details and build output",
                "If READY: verify the deployment URL returns expected content"
            ],
            "verification_checks": [
                "Deployment state is clearly identified",
                "Build logs are accessible and reviewed if issues are present",
                "Production URL returns HTTP 200 for READY deployments"
            ],
            "common_failure_modes": [
                {"issue": "Deployment stuck in QUEUED state", "why_it_happens": ["Concurrent build limit reached for the plan", "Another deployment is currently building"], "safe_recovery": ["Wait for the current build to complete", "Check concurrent build limits for the plan (Hobby: 1, Pro: 12)"]},
                {"issue": "Deployment in ERROR state with no clear message", "why_it_happens": ["Build exceeded memory or time limits", "Internal Vercel infrastructure issue"], "safe_recovery": ["Check build logs for the last output before failure", "Retry the deployment", "Contact Vercel support if the issue persists"]}
            ],
            "missing_information_behavior": [
                "If no deployment ID is provided, list the most recent deployments for the project and ask which one to inspect"
            ],
            "confirmation_required_when": [],
            "escalate_when": [
                "Deployment has been in ERROR state for multiple consecutive attempts",
                "Suspected Vercel platform issue affecting multiple projects"
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
            "Confirm the target environment (production vs preview) before deploying",
            "Check build logs when a deployment fails before retrying",
            "Verify environment variables are set for the correct scope before deploying",
            "Use preview deployments to test changes before promoting to production",
            "Include the team ID in API requests when working with team-scoped projects"
        ],
        "never_do": [
            "Never deploy to production without operator confirmation",
            "Never delete environment variables in production without understanding their dependencies",
            "Never expose API tokens in client-side code or build logs",
            "Never assume a preview deployment URL is private (they are publicly accessible by default)",
            "Never delete a project without explicit escalation and approval"
        ],
        "verify_before_write_actions": [
            "Confirm the target environment before any deployment or env var change",
            "Verify the project name and team are correct (avoid deploying to the wrong project)",
            "Check that the git ref or branch being deployed contains the intended changes"
        ],
        "verify_after_write_actions": [
            "Verify the deployment reaches READY state",
            "Check that the production URL returns expected content after deployment",
            "Confirm serverless functions respond correctly after env var changes"
        ],
        "ambiguity_rules": [
            "If the user says 'deploy' without specifying production or preview, ask to clarify",
            "If an environment variable target is not specified, do not default to production",
            "If rollback target is unclear, list recent deployments and ask the user to choose"
        ],
        "environment_rules": [
            "Production: deployments are immediately live; always require confirmation",
            "Preview: one URL per deployment; safe for testing but publicly accessible",
            "Development: environment variables available in local 'vercel dev' only"
        ],
        "retry_idempotency_rules": [
            "Deployment creation is not idempotent; duplicate POSTs create duplicate deployments",
            "Check for in-progress deployments before triggering a new one",
            "Failed deployments do not auto-retry; a new deployment must be triggered explicitly"
        ]
    },
    "decision_guide": [
        {
            "decision": "Git push deployment vs API deployment",
            "choose_when": ["Git integration is set up and the code change is committed", "Standard CI/CD workflow is in place"],
            "avoid_when": ["You need to deploy a specific commit that is not on the main branch", "The deployment needs custom environment variable overrides"],
            "prefer_instead": ["Git push for routine deployments", "API deployment for CI/CD pipelines and automated workflows"],
            "escalate_when": ["Neither approach works due to infrastructure constraints"]
        },
        {
            "decision": "Rollback vs fix-forward",
            "choose_when": ["Rollback: production is broken and the fix will take longer than acceptable downtime", "Fix-forward: the issue is minor and can be patched quickly"],
            "avoid_when": ["Rollback: the previous deployment also has issues", "Fix-forward: the bug affects data integrity or security"],
            "prefer_instead": ["Rollback for critical production issues", "Fix-forward for minor issues that can be resolved in minutes"],
            "escalate_when": ["Both the current and previous deployments have critical issues", "The rollback involves data migration changes that cannot be reverted"]
        }
    ],
    "troubleshooting": [
        {
            "issue": "Build fails with 'Module not found' error",
            "signals": ["Build log shows 'Module not found: Can't resolve ...'", "Deployment state is ERROR"],
            "likely_causes": ["Missing dependency in package.json", "Case-sensitive file path mismatch (macOS local vs Linux build)", "Incorrect import path"],
            "recommended_actions": ["Check that the module is listed in package.json dependencies", "Verify file name casing matches import statements exactly", "Run the build locally in a case-sensitive environment"],
            "do_not_do": ["Do not add the module as a devDependency if it is needed at build time", "Do not ignore the error and force a redeployment"],
            "escalate_when": ["The error appears intermittently across different builds"],
            "source_refs": [{"label": "Build Troubleshooting", "url": "https://vercel.com/docs/deployments/troubleshoot-a-build"}]
        },
        {
            "issue": "Serverless function returns 504 Gateway Timeout",
            "signals": ["HTTP 504 responses from /api/* routes", "Function invocation logs show timeout"],
            "likely_causes": ["Function execution exceeds the plan's timeout limit", "External API or database call is slow", "Database connection pool exhaustion"],
            "recommended_actions": ["Optimize the function to complete within the timeout (Hobby: 10s, Pro: 60s)", "Use connection pooling for database access", "Add timeout handling for external API calls", "Consider upgrading to Pro or Enterprise for longer timeout limits"],
            "do_not_do": ["Do not work around the timeout by chaining multiple function calls", "Do not remove error handling to speed up the function"],
            "escalate_when": ["The function requires more than 300 seconds (Enterprise limit)", "Timeout issues affect multiple functions simultaneously"],
            "source_refs": [{"label": "Serverless Functions", "url": "https://vercel.com/docs/functions/serverless-functions"}]
        }
    ],
    "references_by_topic": [
        {
            "topic": "Deployments",
            "references": [
                {"label": "Deployments Overview", "url": "https://vercel.com/docs/deployments/overview", "reason": "Core deployment concepts and lifecycle"},
                {"label": "Deployments API", "url": "https://vercel.com/docs/rest-api/endpoints/deployments", "reason": "Programmatic deployment management"},
                {"label": "Vercel CLI", "url": "https://vercel.com/docs/cli", "reason": "CLI commands for local development and deployment"}
            ]
        },
        {
            "topic": "Configuration",
            "references": [
                {"label": "Environment Variables", "url": "https://vercel.com/docs/projects/environment-variables", "reason": "Environment variable management and scoping"},
                {"label": "Project Configuration", "url": "https://vercel.com/docs/projects/project-configuration", "reason": "vercel.json configuration reference"},
                {"label": "Frameworks", "url": "https://vercel.com/docs/frameworks", "reason": "Framework-specific build and deployment settings"}
            ]
        },
        {
            "topic": "Serverless & Edge Functions",
            "references": [
                {"label": "Serverless Functions", "url": "https://vercel.com/docs/functions/serverless-functions", "reason": "Serverless function development and constraints"},
                {"label": "Edge Functions", "url": "https://vercel.com/docs/functions/edge-functions", "reason": "Edge runtime capabilities and limitations"},
                {"label": "Function Logs", "url": "https://vercel.com/docs/observability/runtime-logs", "reason": "Debugging function invocations"}
            ]
        }
    ],
    "implementation_notes": {
        "customer_page_must_include": [
            "Deployment workflow via Git integration and API",
            "Environment variable configuration and scoping",
            "Rollback procedure for production incidents",
            "Serverless function constraints and timeout limits",
            "Common build failure troubleshooting patterns"
        ],
        "doc_gaps_or_unclear_areas": [
            "Detailed API rate limits are not published in a single reference page",
            "Edge Function npm package compatibility list could be more comprehensive",
            "Concurrent build limits per plan are not prominently documented"
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
        "summary": "Notion is an all-in-one workspace for notes, documents, wikis, and databases. Its API provides programmatic access to create, read, update, and search Notion content.",
        "agent_fit_summary": "Agents can safely query databases and read pages. Creating or updating content in shared workspaces requires confirmation. Deleting pages, modifying workspace settings, and bulk operations require escalation.",
        "high_risk_notice": "The Notion API cannot undo page deletions or block modifications. Content changes in shared workspaces are immediately visible to all members. Rate limits are strict at 3 requests per second.",
        "primary_cta_label": "View Full Operating Guide"
    },
    "agent_scope": {
        "safe_without_approval": [
            {"action": "Query a database with filters and sorts", "reason": "Read-only data retrieval", "risk_level": "safe_read"},
            {"action": "Retrieve a page and its properties", "reason": "Read-only page inspection", "risk_level": "safe_read"},
            {"action": "Search the workspace by title", "reason": "Read-only search across shared content", "risk_level": "safe_read"},
            {"action": "List users and workspace members", "reason": "Read-only user enumeration", "risk_level": "safe_read"}
        ],
        "requires_confirmation": [
            {"action": "Create a page in a shared database or workspace", "reason": "New content is immediately visible to all workspace members", "risk_level": "requires_confirmation", "confirmation_needed_for": ["Parent page or database", "Page title and initial content", "Whether the page should be in a shared space"]},
            {"action": "Update page properties", "reason": "Changes are immediately visible and may affect workflows", "risk_level": "requires_confirmation", "confirmation_needed_for": ["Page ID and which properties are changing", "New property values", "Impact on related database views or filters"]},
            {"action": "Append blocks to an existing page", "reason": "Adds content to a page that may be shared with others", "risk_level": "requires_confirmation", "confirmation_needed_for": ["Target page", "Content being appended"]}
        ],
        "requires_escalation": [
            {"action": "Delete or archive a page", "reason": "Cannot be undone via API; content may be lost permanently", "risk_level": "requires_escalation", "escalate_when": ["Any page deletion or archival request", "Page is in a shared workspace"]},
            {"action": "Bulk update multiple pages or database entries", "reason": "High blast radius; errors affect many records simultaneously", "risk_level": "requires_escalation", "escalate_when": ["Operation affects more than 10 pages", "Operation modifies properties used by automations or integrations"]},
            {"action": "Change integration permissions or capabilities", "reason": "Affects the integration's access scope across the workspace", "risk_level": "requires_escalation", "escalate_when": ["Modifying integration capabilities", "Sharing or unsharing pages with the integration"]}
        ]
    },
    "suitability": {
        "best_for": [
            "Knowledge base and documentation management",
            "CRM and project tracking via structured databases",
            "Automated content creation from external data sources",
            "Cross-tool integrations (syncing data from Slack, GitHub, etc.)",
            "Meeting notes and task management automation"
        ],
        "less_suitable_for": [
            "High-frequency real-time data updates (3 req/s rate limit)",
            "Large file storage (Notion is not a file system)",
            "Complex relational queries with joins or aggregations",
            "Public-facing websites with heavy traffic"
        ],
        "not_clearly_supported": [
            "Full-text search of page body content (API only searches titles)",
            "Editing existing block content (must delete and recreate)",
            "Exporting pages to PDF or other formats via API"
        ]
    },
    "setup_access": {
        "prerequisites": [
            "A Notion account with a workspace",
            "An internal integration created at notion.so/my-integrations",
            "Target pages or databases shared with the integration"
        ],
        "accounts_and_access": [
            "Notion workspace member or admin role",
            "Integration token (secret_...)",
            "Pages must be explicitly shared with the integration via the Share menu"
        ],
        "authentication": {
            "methods": [
                "Internal integration token (secret_...) in Authorization: Bearer header",
                "Public OAuth 2.0 integration for third-party apps",
                "Notion-Version header required on all requests (e.g., 2022-06-28)"
            ],
            "required_secrets_or_tokens": [
                "NOTION_API_KEY (internal integration token: secret_...)",
                "NOTION_VERSION (API version header value, e.g., 2022-06-28)"
            ],
            "permission_notes": [
                "Integrations can only access pages and databases explicitly shared with them",
                "Capabilities are configured at integration creation: read, update, insert content",
                "Child pages inherit sharing from parent pages"
            ],
            "environment_notes": [
                "There is no test mode; all API calls affect the real workspace",
                "The Notion-Version header controls API response format and behavior",
                "Rate limit: 3 requests per second per integration token"
            ]
        },
        "initial_setup_steps": [
            "Create an internal integration at notion.so/my-integrations",
            "Copy the integration token (starts with secret_)",
            "Open the target page or database in Notion and click Share > Invite the integration",
            "Test connectivity: GET /v1/users/me with the integration token",
            "Query a shared database to verify access: POST /v1/databases/{id}/query"
        ]
    },
    "task_playbooks": [
        {
            "id": "notion-query-database",
            "task_name": "Query a Database",
            "goal": "Retrieve filtered and sorted entries from a Notion database",
            "when_to_use": [
                "Looking up records matching specific criteria",
                "Generating reports from structured data",
                "Checking the current state of a project tracker or CRM"
            ],
            "when_not_to_use": [
                "Searching across the entire workspace (use Search instead)",
                "Retrieving a single page by ID (use Retrieve Page)"
            ],
            "risk_level": "safe_read",
            "required_inputs": [
                {"name": "database_id", "description": "The Notion database ID (32-character UUID)", "required": True}
            ],
            "optional_inputs": [
                {"name": "filter", "description": "Filter object to narrow results (e.g., {property: 'Status', select: {equals: 'In Progress'}})"},
                {"name": "sorts", "description": "Sort order array (e.g., [{property: 'Due Date', direction: 'ascending'}])"},
                {"name": "page_size", "description": "Number of results per page (max 100, default 100)"}
            ],
            "pre_checks": [
                "Verify the database is shared with the integration",
                "Confirm the filter property names match the actual database schema",
                "Check that property types in filters match (e.g., select vs multi_select)"
            ],
            "steps": [
                "POST /v1/databases/{database_id}/query with filter and sorts in the request body",
                "Include Authorization: Bearer secret_... and Notion-Version headers",
                "Process the results array from the response",
                "If has_more is true, use the next_cursor to fetch additional pages",
                "Continue paginating until has_more is false or desired results are found"
            ],
            "verification_checks": [
                "Response contains a 'results' array with page objects",
                "Result count matches expectations for the filter criteria",
                "Property values in results are in the expected format"
            ],
            "common_failure_modes": [
                {"issue": "404 Not Found for a database that exists", "why_it_happens": ["Database is not shared with the integration", "Using the workspace URL ID format instead of the API ID"], "safe_recovery": ["Share the database with the integration via the Share menu", "Extract the 32-character ID from the database URL"]},
                {"issue": "Filter returns no results unexpectedly", "why_it_happens": ["Property name in filter does not exactly match the database schema", "Property type mismatch (e.g., using select filter on a multi_select property)"], "safe_recovery": ["Retrieve the database schema first: GET /v1/databases/{id}", "Match property names and types exactly"]}
            ],
            "missing_information_behavior": [
                "If database ID is unknown, search the workspace by title to find the database",
                "If filter criteria are vague, ask for specific property names and values"
            ],
            "confirmation_required_when": [],
            "escalate_when": [
                "Query returns an unexpectedly large number of results suggesting a filter issue"
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
                "Adding a new record to a database (e.g., task, contact, note)",
                "Creating a document under an existing page",
                "Programmatically generating content from external data"
            ],
            "when_not_to_use": [
                "Updating an existing page (use Update Page Properties)",
                "Appending content to an existing page (use Append Blocks)"
            ],
            "risk_level": "requires_confirmation",
            "required_inputs": [
                {"name": "parent", "description": "Parent database_id or page_id where the new page will be created", "required": True},
                {"name": "properties", "description": "Page properties matching the parent database schema (must include title)", "required": True}
            ],
            "optional_inputs": [
                {"name": "children", "description": "Array of block objects for initial page content (headings, paragraphs, lists, etc.)"},
                {"name": "icon", "description": "Page icon (emoji or external URL)"},
                {"name": "cover", "description": "Page cover image URL"}
            ],
            "pre_checks": [
                "Verify the parent page or database is shared with the integration",
                "Confirm the property schema matches the target database",
                "Check for duplicate entries if uniqueness is expected"
            ],
            "steps": [
                "Construct the properties object matching the parent database schema",
                "Optionally construct children blocks for page content",
                "POST /v1/pages with parent, properties, and optional children",
                "Capture the returned page ID and URL from the response",
                "Verify the page appears in the database or parent page"
            ],
            "verification_checks": [
                "Response contains a page object with id and url",
                "Page appears in the target database with correct property values",
                "Content blocks render correctly in Notion"
            ],
            "common_failure_modes": [
                {"issue": "Validation error on properties", "why_it_happens": ["Property name does not match the database schema exactly", "Property value type does not match (e.g., sending string for a number property)", "Title property is missing or malformed"], "safe_recovery": ["Retrieve the database schema first to confirm property names and types", "Ensure title is provided as a rich_text array"]},
                {"issue": "Block limit exceeded", "why_it_happens": ["More than 100 children blocks in a single request"], "safe_recovery": ["Create the page first, then append additional blocks in batches of 100"]}
            ],
            "missing_information_behavior": [
                "If parent is unknown, search for the target database by title and confirm with the user",
                "If required properties are missing, retrieve the database schema and ask for values"
            ],
            "confirmation_required_when": [
                "Creating a page in a shared workspace (visible to all members)",
                "Creating a page with content generated from external data"
            ],
            "escalate_when": [
                "Bulk page creation (more than 10 pages at once)",
                "Creating pages that will trigger Notion automations or integrations"
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
            "goal": "Modify the properties of an existing page or database entry",
            "when_to_use": [
                "Changing the status, assignee, or due date of a task",
                "Updating a record with new information from an external source",
                "Correcting incorrect property values"
            ],
            "when_not_to_use": [
                "Adding content blocks to the page body (use Append Blocks)",
                "Changing the page's parent location (not supported via API)"
            ],
            "risk_level": "requires_confirmation",
            "required_inputs": [
                {"name": "page_id", "description": "The Notion page ID (32-character UUID)", "required": True},
                {"name": "properties", "description": "Object containing only the properties to update", "required": True}
            ],
            "optional_inputs": [
                {"name": "archived", "description": "Set to true to archive (soft-delete) the page"}
            ],
            "pre_checks": [
                "Retrieve the current page to verify it exists and check current property values",
                "Confirm the property names and types match the database schema",
                "Verify the integration has update capabilities"
            ],
            "steps": [
                "Retrieve the current page state: GET /v1/pages/{page_id}",
                "Construct the properties update object with only the fields being changed",
                "PATCH /v1/pages/{page_id} with the properties object",
                "Verify the response shows the updated property values",
                "Confirm the change is reflected in the database view"
            ],
            "verification_checks": [
                "Response shows updated property values matching the intended changes",
                "Page properties are correct when retrieved again",
                "Database views reflect the updated data"
            ],
            "common_failure_modes": [
                {"issue": "Cannot update a formula or rollup property", "why_it_happens": ["Formula and rollup properties are computed, not directly editable"], "safe_recovery": ["Update the source properties that the formula or rollup depends on"]},
                {"issue": "Stale data conflict", "why_it_happens": ["Another user or integration modified the page between read and update"], "safe_recovery": ["Re-read the page, verify the current state, and retry the update"]}
            ],
            "missing_information_behavior": [
                "If page ID is unknown, search for the page by title and confirm with the user",
                "If the property to update is ambiguous, list the page's current properties and ask"
            ],
            "confirmation_required_when": [
                "Updating properties on a page in a shared workspace",
                "Archiving a page (soft-delete)"
            ],
            "escalate_when": [
                "Bulk updates affecting more than 10 pages",
                "Modifying properties that trigger workflow automations"
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
            "goal": "Find pages and databases across the workspace by title",
            "when_to_use": [
                "Looking up a page or database when the ID is not known",
                "Finding content related to a specific topic or project",
                "Discovering which databases exist in the workspace"
            ],
            "when_not_to_use": [
                "Querying a specific database with filters (use Query Database)",
                "Searching for content within page bodies (API only searches titles)"
            ],
            "risk_level": "safe_read",
            "required_inputs": [
                {"name": "query", "description": "Search text to match against page and database titles", "required": True}
            ],
            "optional_inputs": [
                {"name": "filter", "description": "Filter by object type: 'page' or 'database'"},
                {"name": "sort", "description": "Sort by last_edited_time ascending or descending"}
            ],
            "pre_checks": [
                "Ensure the search query is specific enough to return relevant results",
                "Remember that search only returns content shared with the integration"
            ],
            "steps": [
                "POST /v1/search with query string and optional filter and sort",
                "Process the results array containing page and database objects",
                "If has_more is true, paginate using next_cursor",
                "Extract page IDs and titles from the results for further operations"
            ],
            "verification_checks": [
                "Results contain relevant pages matching the search query",
                "Result objects include id, title, and parent information",
                "Pagination is handled correctly if results span multiple pages"
            ],
            "common_failure_modes": [
                {"issue": "Search returns no results for known content", "why_it_happens": ["The page is not shared with the integration", "Search only matches titles, not body content", "Content was recently created and not yet indexed"], "safe_recovery": ["Verify the page is shared with the integration", "Try searching with a shorter or different query", "If recently created, wait a few seconds and retry"]},
                {"issue": "Too many irrelevant results", "why_it_happens": ["Search query is too broad", "Many pages have similar titles"], "safe_recovery": ["Use a more specific query", "Filter by object type (page or database)", "Sort by last_edited_time to find the most recent match"]}
            ],
            "missing_information_behavior": [
                "If the search query is empty, ask what the user is looking for",
                "If results are ambiguous, present the top matches and ask the user to select"
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
            "Include the Notion-Version header on every API request",
            "Share target pages and databases with the integration before attempting access",
            "Respect the 3 requests/second rate limit with delays between calls",
            "Retrieve the database schema before creating or updating pages to ensure property compatibility",
            "Handle pagination for all list and query operations (max 100 results per page)"
        ],
        "never_do": [
            "Never delete or archive pages without explicit escalation and approval",
            "Never perform bulk updates on more than 10 pages without escalation",
            "Never assume a page is accessible without verifying it is shared with the integration",
            "Never store the integration token in client-side code or public repositories",
            "Never ignore rate limit (429) responses; always implement backoff"
        ],
        "verify_before_write_actions": [
            "Confirm the target page or database is shared with the integration",
            "Validate property names and types against the database schema",
            "Check for duplicate entries before creating new pages"
        ],
        "verify_after_write_actions": [
            "Retrieve the created or updated page to confirm changes were applied",
            "Verify the content renders correctly in the Notion interface",
            "Check that database views reflect the changes as expected"
        ],
        "ambiguity_rules": [
            "If a page title matches multiple results, present options and ask the user to select",
            "If a property name is ambiguous, retrieve the schema and confirm the correct property",
            "If the user asks to 'update a page' without specifics, ask what to change"
        ],
        "environment_rules": [
            "There is no sandbox or test mode; all API calls affect the live workspace",
            "Use a dedicated test workspace or test database for development and testing",
            "Temporary S3 URLs for file blocks expire after 1 hour; do not cache them long-term"
        ],
        "retry_idempotency_rules": [
            "Implement exponential backoff with jitter for 429 rate limit responses",
            "Page creation is not idempotent; duplicate POSTs create duplicate pages",
            "Use a unique identifier property to detect and prevent duplicate entries",
            "Check for existing records before creating to avoid duplicates"
        ]
    },
    "decision_guide": [
        {
            "decision": "Database query vs workspace search",
            "choose_when": ["Query: you know the target database and need filtered/sorted results", "Search: you need to find a page or database by title across the workspace"],
            "avoid_when": ["Query: you do not know which database contains the data", "Search: you need complex filters, sorts, or property-level matching"],
            "prefer_instead": ["Query for structured data retrieval from a known database", "Search for discovery and lookup by title"],
            "escalate_when": ["The user needs full-text search of page body content (not supported by the API)"]
        },
        {
            "decision": "Create page vs append blocks",
            "choose_when": ["Create: adding a new record or document", "Append: adding content to an existing page"],
            "avoid_when": ["Create: the page already exists (update it instead)", "Append: you need to modify existing blocks (must delete and recreate)"],
            "prefer_instead": ["Create for new records", "Append for adding content sections to existing pages"],
            "escalate_when": ["The operation requires modifying existing block content (not supported; requires delete and recreate)"]
        }
    ],
    "troubleshooting": [
        {
            "issue": "API returns 404 for a page or database that exists in Notion",
            "signals": ["404 Not Found response", "object_not_found error code"],
            "likely_causes": ["Page is not shared with the integration", "Using the wrong ID format (workspace URL vs API format)", "Integration lacks the required capability (read, update, insert)"],
            "recommended_actions": ["Open the page in Notion, click Share, and invite the integration", "Extract the 32-character UUID from the page URL", "Check integration capabilities at notion.so/my-integrations"],
            "do_not_do": ["Do not retry without fixing the sharing or ID issue", "Do not assume the page was deleted without checking"],
            "escalate_when": ["Sharing is correctly configured but 404 persists"],
            "source_refs": [{"label": "Authorization", "url": "https://developers.notion.com/docs/authorization"}]
        },
        {
            "issue": "Rate limit errors (429 Too Many Requests)",
            "signals": ["HTTP 429 response", "Retry-After header in response"],
            "likely_causes": ["Exceeding 3 requests per second", "Batch operations without throttling between calls"],
            "recommended_actions": ["Implement exponential backoff with jitter", "Add a minimum 350ms delay between consecutive requests", "Batch operations and process sequentially with delays"],
            "do_not_do": ["Do not immediately retry without waiting", "Do not parallelize requests beyond the rate limit"],
            "escalate_when": ["Rate limit is consistently hit despite proper throttling, suggesting the integration needs restructuring"],
            "source_refs": [{"label": "Rate Limits", "url": "https://developers.notion.com/reference/request-limits"}]
        }
    ],
    "references_by_topic": [
        {
            "topic": "Getting Started",
            "references": [
                {"label": "Notion API Getting Started", "url": "https://developers.notion.com/docs/getting-started", "reason": "Integration setup and first API call"},
                {"label": "Authorization", "url": "https://developers.notion.com/docs/authorization", "reason": "Authentication methods and sharing requirements"}
            ]
        },
        {
            "topic": "Databases & Pages",
            "references": [
                {"label": "Working with Databases", "url": "https://developers.notion.com/docs/working-with-databases", "reason": "Database query, filter, and sort patterns"},
                {"label": "Pages API", "url": "https://developers.notion.com/reference/page", "reason": "Create, retrieve, and update pages"},
                {"label": "Block Types", "url": "https://developers.notion.com/reference/block", "reason": "Supported block types and their schemas"}
            ]
        },
        {
            "topic": "Search & Discovery",
            "references": [
                {"label": "Search API", "url": "https://developers.notion.com/reference/post-search", "reason": "Workspace-wide title search"},
                {"label": "Pagination", "url": "https://developers.notion.com/reference/intro#pagination", "reason": "Cursor-based pagination for all list endpoints"}
            ]
        }
    ],
    "implementation_notes": {
        "customer_page_must_include": [
            "Integration setup and page sharing requirements",
            "Database query patterns with filters and sorts",
            "Page creation and property management",
            "Block manipulation and content formatting",
            "Rate limiting and backoff strategy implementation",
            "Common gotchas: sharing requirements, block editing limitations, search scope"
        ],
        "doc_gaps_or_unclear_areas": [
            "Complete list of supported block types is not aggregated in one place",
            "OAuth flow error handling examples are minimal",
            "Block content editing limitations are not prominently documented (delete + recreate pattern)"
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
        "summary": "Slack is a business communication platform with APIs for sending messages, managing channels, building interactive bots, and integrating workflows across teams and tools.",
        "agent_fit_summary": "Agents can safely read messages and search content. Sending messages to public channels requires confirmation. Channel management, user administration, and workspace-wide changes require escalation.",
        "high_risk_notice": "Messages sent to public channels are visible to the entire workspace. The bot must be invited to channels before it can read or post. Admin-scoped actions can affect all workspace members.",
        "primary_cta_label": "View Full Operating Guide"
    },
    "agent_scope": {
        "safe_without_approval": [
            {"action": "Search messages and files across the workspace", "reason": "Read-only search within the bot's accessible channels", "risk_level": "safe_read"},
            {"action": "List channels and channel members", "reason": "Read-only enumeration of workspace structure", "risk_level": "safe_read"},
            {"action": "Read message history in channels the bot is in", "reason": "Read-only access to conversation content", "risk_level": "safe_read"},
            {"action": "Retrieve user profiles and presence", "reason": "Read-only user information", "risk_level": "safe_read"}
        ],
        "requires_confirmation": [
            {"action": "Send a message to a public channel", "reason": "Visible to all workspace members; cannot be unsent (only deleted)", "risk_level": "requires_confirmation", "confirmation_needed_for": ["Target channel name and ID", "Message content (text and blocks)", "Whether the message should be threaded"]},
            {"action": "Send a direct message", "reason": "Arrives as a notification to the recipient; may be unexpected", "risk_level": "requires_confirmation", "confirmation_needed_for": ["Recipient user ID", "Message content"]},
            {"action": "Upload a file to a channel", "reason": "Files are shared with all channel members and count against storage", "risk_level": "requires_confirmation", "confirmation_needed_for": ["Target channel", "File content and name"]}
        ],
        "requires_escalation": [
            {"action": "Create or archive a channel", "reason": "Affects workspace organization; archived channels hide content from members", "risk_level": "requires_escalation", "escalate_when": ["Creating any new channel", "Archiving a channel with active members"]},
            {"action": "Manage channel membership (invite/kick)", "reason": "Affects who can see channel content; kicking members may disrupt workflows", "risk_level": "requires_escalation", "escalate_when": ["Removing a member from a channel", "Inviting members to a private channel"]},
            {"action": "Modify workspace settings or user roles", "reason": "Admin-level actions affecting the entire workspace", "risk_level": "requires_escalation", "escalate_when": ["Any admin-scoped API call", "Changing user roles or permissions"]}
        ]
    },
    "suitability": {
        "best_for": [
            "Automated notifications and alerts (deploy, monitoring, CI/CD)",
            "Interactive bots for help desk, on-call rotation, and DevOps workflows",
            "Cross-tool integrations (GitHub, Jira, PagerDuty, etc.)",
            "Workflow automation triggered by Slack events",
            "Team communication search and archival"
        ],
        "less_suitable_for": [
            "High-volume data streaming (use a message queue)",
            "Long-term data storage (Slack has retention policies)",
            "Customer-facing live chat (use a dedicated support platform)",
            "Real-time audio/video (Huddles are not API-accessible)"
        ],
        "not_clearly_supported": [
            "Editing messages sent by other users (only your own messages)",
            "Accessing Slack Huddle or Clip content via API",
            "Full workspace analytics beyond what the admin APIs provide"
        ]
    },
    "setup_access": {
        "prerequisites": [
            "A Slack workspace where you have permission to install apps",
            "A Slack App created at api.slack.com/apps",
            "Bot token scopes configured for the intended use case"
        ],
        "accounts_and_access": [
            "Slack workspace admin approval for app installation",
            "Bot User OAuth Token (xoxb-...)",
            "App-level token (xapp-...) for Socket Mode (optional)"
        ],
        "authentication": {
            "methods": [
                "Bot User OAuth Token (xoxb-...) for bot actions",
                "User OAuth Token (xoxp-...) for user-scoped actions",
                "App-Level Token (xapp-...) for Socket Mode connections",
                "Incoming Webhooks for simple message posting without token management"
            ],
            "required_secrets_or_tokens": [
                "SLACK_BOT_TOKEN (xoxb-... Bot User OAuth Token)",
                "SLACK_SIGNING_SECRET (for verifying incoming requests from Slack)",
                "SLACK_APP_TOKEN (xapp-... for Socket Mode, if used)"
            ],
            "permission_notes": [
                "Scopes are granular: chat:write, channels:read, users:read, files:write, etc.",
                "Bot tokens can only access channels the bot is a member of",
                "User tokens act on behalf of the installing user with their permissions",
                "Admin scopes require workspace admin approval during installation"
            ],
            "environment_notes": [
                "There is no sandbox mode; all API calls affect the real workspace",
                "Use a dedicated test workspace for development and testing",
                "Token rotation is available for enhanced security",
                "Rate limits vary by API method tier (Tier 1-4)"
            ]
        },
        "initial_setup_steps": [
            "Create a new app at api.slack.com/apps (from scratch or app manifest)",
            "Configure OAuth scopes under OAuth & Permissions (e.g., chat:write, channels:read)",
            "Install the app to the workspace and copy the Bot User OAuth Token",
            "Invite the bot to target channels: /invite @botname in each channel",
            "Test connectivity: call auth.test with the bot token to verify"
        ]
    },
    "task_playbooks": [
        {
            "id": "slack-send-message",
            "task_name": "Send a Message",
            "goal": "Post a message to a Slack channel, DM, or thread",
            "when_to_use": [
                "Sending automated notifications (deploy alerts, monitoring, CI/CD results)",
                "Posting structured information using Block Kit formatting",
                "Replying to a thread for follow-up or context"
            ],
            "when_not_to_use": [
                "Simple webhook-based posting (use Incoming Webhooks instead)",
                "Updating an existing message (use chat.update)",
                "Scheduling a message for later (use chat.scheduleMessage)"
            ],
            "risk_level": "requires_confirmation",
            "required_inputs": [
                {"name": "channel", "description": "Channel ID (C0123456789) to post to", "required": True},
                {"name": "text", "description": "Plain text fallback message (always required, even with blocks)", "required": True}
            ],
            "optional_inputs": [
                {"name": "blocks", "description": "Array of Block Kit layout blocks for rich formatting"},
                {"name": "thread_ts", "description": "Timestamp of parent message to reply in a thread"},
                {"name": "unfurl_links", "description": "Whether to unfurl URLs in the message (default true)"}
            ],
            "pre_checks": [
                "Verify the bot is a member of the target channel",
                "Confirm the bot has chat:write scope",
                "Validate Block Kit JSON using the Block Kit Builder if using blocks",
                "Review message content for accuracy and appropriate tone"
            ],
            "steps": [
                "Resolve the channel name to a channel ID if needed: use conversations.list",
                "Construct the message payload with channel, text, and optional blocks",
                "Call chat.postMessage with the bot token",
                "Check the response: ok should be true",
                "Capture the ts (timestamp) from the response for threading or updates"
            ],
            "verification_checks": [
                "API response has ok: true",
                "Response includes ts and channel fields",
                "Message appears in the target channel with correct formatting",
                "Block Kit elements render as expected"
            ],
            "common_failure_modes": [
                {"issue": "channel_not_found error", "why_it_happens": ["Bot is not a member of the channel", "Using channel name instead of channel ID", "Channel has been archived"], "safe_recovery": ["Invite the bot to the channel: /invite @botname", "Use conversations.list to resolve the channel name to an ID", "Check if the channel is archived"]},
                {"issue": "not_authed error", "why_it_happens": ["Bot token is invalid, expired, or revoked", "Token does not have the required scopes"], "safe_recovery": ["Verify the token with auth.test", "Check OAuth scopes in the app settings", "Reinstall the app if the token was revoked"]},
                {"issue": "rate_limited response", "why_it_happens": ["Exceeded the method's rate limit tier"], "safe_recovery": ["Respect the Retry-After header value", "Implement exponential backoff", "Queue messages and send them with delays"]}
            ],
            "missing_information_behavior": [
                "If channel is specified by name, look up the channel ID via conversations.list",
                "If message content is empty, ask the user what to send"
            ],
            "confirmation_required_when": [
                "Sending to a public channel (visible to all workspace members)",
                "Sending a DM to a user who has not interacted with the bot",
                "Message contains mentions (@here, @channel, @user)"
            ],
            "escalate_when": [
                "Message is going to a channel with 100+ members",
                "Message content includes @here or @channel mentions",
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
            "goal": "Find messages across the workspace matching a search query",
            "when_to_use": [
                "Looking for specific conversations or decisions",
                "Finding messages related to an incident or topic",
                "Retrieving information shared in Slack for reference"
            ],
            "when_not_to_use": [
                "Reading the full history of a specific channel (use conversations.history)",
                "Real-time monitoring of new messages (use Events API)"
            ],
            "risk_level": "safe_read",
            "required_inputs": [
                {"name": "query", "description": "Search query string (supports Slack search modifiers like from:, in:, after:)", "required": True}
            ],
            "optional_inputs": [
                {"name": "sort", "description": "Sort by 'score' (relevance) or 'timestamp'"},
                {"name": "sort_dir", "description": "Sort direction: 'asc' or 'desc'"},
                {"name": "count", "description": "Number of results per page (max 100)"}
            ],
            "pre_checks": [
                "Verify the bot has search:read scope",
                "Note that search results are limited to channels the bot can access"
            ],
            "steps": [
                "Call search.messages with the query parameter",
                "Process the messages.matches array from the response",
                "Extract relevant fields: text, channel, user, ts, permalink",
                "If pagination is needed, use the paging object from the response"
            ],
            "verification_checks": [
                "Response ok is true",
                "Results are relevant to the search query",
                "Permalink URLs are valid and point to the correct messages"
            ],
            "common_failure_modes": [
                {"issue": "No results for a known message", "why_it_happens": ["Bot does not have access to the channel containing the message", "Message is in a private channel the bot has not been invited to", "Search index has not yet updated for very recent messages"], "safe_recovery": ["Ensure the bot is a member of relevant channels", "Wait a few seconds for recent messages to be indexed", "Try broader search terms"]},
                {"issue": "Missing search:read scope", "why_it_happens": ["Scope was not added during app configuration"], "safe_recovery": ["Add search:read scope in the app's OAuth & Permissions settings", "Reinstall the app to apply the new scope"]}
            ],
            "missing_information_behavior": [
                "If the query is too broad, suggest adding modifiers (in:channel, from:user, after:date)",
                "If no results are found, suggest broadening the query or checking channel access"
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
                "Setting up a dedicated channel for a project, incident, or team",
                "Automating channel creation as part of a workflow"
            ],
            "when_not_to_use": [
                "A channel with the same purpose already exists",
                "A DM or group DM would be more appropriate",
                "The workspace has channel creation restrictions for bots"
            ],
            "risk_level": "requires_escalation",
            "required_inputs": [
                {"name": "name", "description": "Channel name (lowercase, no spaces, max 80 chars; use hyphens)", "required": True}
            ],
            "optional_inputs": [
                {"name": "is_private", "description": "Whether to create a private channel (default false)"},
                {"name": "team_id", "description": "Team ID for Enterprise Grid workspaces"},
                {"name": "description", "description": "Channel purpose or description"}
            ],
            "pre_checks": [
                "Verify the bot has channels:manage (public) or groups:write (private) scope",
                "Check if a channel with the same name already exists",
                "Confirm the channel naming convention with the user (e.g., project-name, incident-123)"
            ],
            "steps": [
                "Verify no channel exists with the same name: search conversations.list",
                "Confirm the channel name and type (public/private) with the human operator",
                "Call conversations.create with the channel name and is_private flag",
                "Set the channel topic and purpose using conversations.setTopic and conversations.setPurpose",
                "Invite initial members using conversations.invite if needed"
            ],
            "verification_checks": [
                "API response ok is true and includes the new channel ID",
                "Channel appears in the workspace with the correct name",
                "Channel topic and purpose are set correctly",
                "Initial members have been invited if specified"
            ],
            "common_failure_modes": [
                {"issue": "name_taken error", "why_it_happens": ["A channel (including archived channels) already has this name"], "safe_recovery": ["Search for the existing channel and check if it is archived", "If archived, unarchive it instead of creating a new one", "Choose a different name"]},
                {"issue": "restricted_action error", "why_it_happens": ["Workspace admin has restricted channel creation for bots or non-admins"], "safe_recovery": ["Escalate to a workspace admin to create the channel", "Request that the admin grant the bot channel creation permissions"]}
            ],
            "missing_information_behavior": [
                "If channel name is not provided, ask for the name following workspace naming conventions",
                "If public vs private is not specified, ask the user to clarify"
            ],
            "confirmation_required_when": [
                "Always; channel creation affects workspace organization"
            ],
            "escalate_when": [
                "Always; this is an escalation-level action",
                "Creating a private channel (limits visibility)",
                "Creating channels in bulk as part of automation"
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
                "Onboarding a new team member to project channels",
                "Setting up channel membership as part of a workflow",
                "Removing a member from a channel (e.g., off-boarding)"
            ],
            "when_not_to_use": [
                "The user can join the channel themselves via the Slack UI",
                "The channel is public and the user can self-join"
            ],
            "risk_level": "requires_escalation",
            "required_inputs": [
                {"name": "channel", "description": "Channel ID to modify membership for", "required": True},
                {"name": "users", "description": "User ID(s) to invite or remove", "required": True}
            ],
            "optional_inputs": [
                {"name": "action", "description": "'invite' or 'kick' (default: invite)"}
            ],
            "pre_checks": [
                "Verify the bot has channels:manage scope",
                "Confirm the target channel exists and the bot is a member",
                "Check that the target users are valid workspace members",
                "For removal: verify the action is approved by an appropriate authority"
            ],
            "steps": [
                "Confirm the action (invite or remove), channel, and user(s) with the human operator",
                "For invite: call conversations.invite with channel and users (comma-separated IDs)",
                "For removal: call conversations.kick with channel and user",
                "Verify the membership change in the API response",
                "Optionally notify the channel about the membership change"
            ],
            "verification_checks": [
                "API response ok is true",
                "conversations.members confirms the user was added or removed",
                "No error responses indicating permission issues"
            ],
            "common_failure_modes": [
                {"issue": "already_in_channel error on invite", "why_it_happens": ["User is already a member of the channel"], "safe_recovery": ["This is not a real error; the desired state is already achieved", "Log the info and continue"]},
                {"issue": "cant_invite_self error", "why_it_happens": ["Attempting to invite the bot to a channel it is already in"], "safe_recovery": ["The bot is already a member; no action needed"]},
                {"issue": "not_in_channel error on kick", "why_it_happens": ["User is not a member of the channel"], "safe_recovery": ["The desired state is already achieved; no action needed"]}
            ],
            "missing_information_behavior": [
                "If user is specified by name, look up the user ID via users.list or users.lookupByEmail",
                "If the action is not specified, ask whether to invite or remove"
            ],
            "confirmation_required_when": [
                "Always; membership changes affect access to channel content"
            ],
            "escalate_when": [
                "Always; membership management is an escalation-level action",
                "Removing members from channels (potential access revocation)",
                "Bulk membership changes affecting more than 5 users"
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
            "Verify the bot is a member of the target channel before posting or reading",
            "Include a plain text fallback in the 'text' field even when using Block Kit blocks",
            "Respect rate limit tiers and implement backoff using the Retry-After header",
            "Verify webhook request signatures using the signing secret before processing",
            "Respond to Events API requests within 3 seconds (acknowledge first, process async)"
        ],
        "never_do": [
            "Never send messages to public channels without operator confirmation",
            "Never use @here or @channel mentions without explicit approval (notifies everyone)",
            "Never store bot tokens in client-side code or public repositories",
            "Never kick members from channels without escalation and approval",
            "Never ignore 429 rate limit responses; always wait the specified Retry-After duration"
        ],
        "verify_before_write_actions": [
            "Confirm the target channel is correct (name and ID match)",
            "Review message content for accuracy, tone, and unintended mentions",
            "Verify the bot has the required scopes for the action"
        ],
        "verify_after_write_actions": [
            "Check the API response ok field is true",
            "Verify the message appears in the channel (for critical notifications)",
            "Confirm membership changes took effect via conversations.members"
        ],
        "ambiguity_rules": [
            "If a channel is specified by name, resolve to ID and confirm before acting",
            "If the user says 'send a message' without specifying the channel, ask where to send it",
            "If message content includes potential mentions (@user, @here), highlight this and confirm"
        ],
        "environment_rules": [
            "There is no sandbox; all API calls affect the real workspace",
            "Use a dedicated test workspace for development and bot testing",
            "Bot tokens are workspace-specific; they cannot cross workspace boundaries",
            "Message retention depends on the workspace plan (Free: 90 days)"
        ],
        "retry_idempotency_rules": [
            "chat.postMessage is not idempotent; duplicate calls send duplicate messages",
            "Use event_id for deduplication when processing Events API callbacks",
            "Rate limits are per-method and per-workspace; track them separately",
            "For retries on rate-limited calls, wait the full Retry-After duration before retrying"
        ]
    },
    "decision_guide": [
        {
            "decision": "Bot token (xoxb) vs User token (xoxp)",
            "choose_when": ["Bot: posting automated messages, responding to events, managing channels as the bot", "User: performing actions on behalf of a specific user, accessing DMs the bot cannot see"],
            "avoid_when": ["Bot: user-specific actions that should appear as coming from the user", "User: automated workflows where the action should come from the bot"],
            "prefer_instead": ["Bot tokens for most automation use cases", "User tokens only when the action must be attributed to a specific person"],
            "escalate_when": ["Unsure whether the action should come from the bot or a user"]
        },
        {
            "decision": "Events API vs Socket Mode",
            "choose_when": ["Events API: production deployments with a public HTTPS endpoint", "Socket Mode: local development, internal tools, or environments without a public URL"],
            "avoid_when": ["Events API: no public endpoint is available", "Socket Mode: high-volume production workloads"],
            "prefer_instead": ["Events API for production; Socket Mode for development and internal tools"],
            "escalate_when": ["Event processing requirements exceed what either approach can handle"]
        }
    ],
    "troubleshooting": [
        {
            "issue": "Bot cannot post to a channel",
            "signals": ["channel_not_found or not_in_channel error", "Message does not appear in the channel"],
            "likely_causes": ["Bot has not been invited to the channel", "Missing chat:write scope", "Using channel name instead of channel ID", "Channel is archived"],
            "recommended_actions": ["Invite the bot: type /invite @botname in the channel", "Add chat:write scope and reinstall the app", "Use conversations.list to resolve channel name to ID", "Check if the channel is archived"],
            "do_not_do": ["Do not attempt to post repeatedly without fixing the root cause", "Do not use a user token as a workaround without understanding the implications"],
            "escalate_when": ["The bot is invited to the channel but still cannot post (possible workspace restriction)"],
            "source_refs": [{"label": "chat.postMessage", "url": "https://api.slack.com/methods/chat.postMessage"}]
        },
        {
            "issue": "Events are not being received",
            "signals": ["No events arrive at the endpoint or Socket Mode connection", "Slack shows the app as not responding"],
            "likely_causes": ["URL verification challenge was not handled correctly", "Event subscriptions are not configured in the app settings", "Endpoint does not respond within 3 seconds", "Socket Mode connection dropped without reconnection"],
            "recommended_actions": ["Ensure the endpoint handles the url_verification challenge event", "Check Event Subscriptions in the app settings at api.slack.com/apps", "Acknowledge events with HTTP 200 immediately; process asynchronously", "Implement automatic reconnection for Socket Mode"],
            "do_not_do": ["Do not increase the endpoint response time; acknowledge immediately and process later", "Do not disable event subscriptions to troubleshoot; check logs instead"],
            "escalate_when": ["Events are not received despite correct configuration (possible Slack platform issue)"],
            "source_refs": [{"label": "Events API Guide", "url": "https://api.slack.com/events-api"}, {"label": "Socket Mode", "url": "https://api.slack.com/apis/connections/socket"}]
        },
        {
            "issue": "Rate limiting across multiple API methods",
            "signals": ["HTTP 429 responses with Retry-After header", "Multiple methods returning rate_limited error"],
            "likely_causes": ["Burst of API calls exceeding the per-method tier limit", "Missing backoff logic between sequential calls", "High-frequency polling instead of using events"],
            "recommended_actions": ["Implement per-method rate tracking and backoff", "Switch from polling to Events API for real-time data", "Queue outbound messages and send with delays between calls", "Use bulk endpoints where available (e.g., conversations.members for batch membership checks)"],
            "do_not_do": ["Do not ignore Retry-After headers", "Do not distribute calls across multiple tokens to circumvent limits (violates Slack ToS)"],
            "escalate_when": ["Rate limits are consistently hit despite proper throttling, suggesting the integration design needs restructuring"],
            "source_refs": [{"label": "Rate Limiting", "url": "https://api.slack.com/docs/rate-limits"}]
        }
    ],
    "references_by_topic": [
        {
            "topic": "Messaging",
            "references": [
                {"label": "chat.postMessage", "url": "https://api.slack.com/methods/chat.postMessage", "reason": "Primary method for sending messages"},
                {"label": "Block Kit Builder", "url": "https://app.slack.com/block-kit-builder", "reason": "Visual tool for designing rich message layouts"},
                {"label": "Message Formatting", "url": "https://api.slack.com/reference/surfaces/formatting", "reason": "Text formatting syntax for Slack messages"}
            ]
        },
        {
            "topic": "Channels & Conversations",
            "references": [
                {"label": "Conversations API", "url": "https://api.slack.com/docs/conversations-api", "reason": "Channel management and conversation operations"},
                {"label": "conversations.list", "url": "https://api.slack.com/methods/conversations.list", "reason": "List and discover workspace channels"},
                {"label": "conversations.history", "url": "https://api.slack.com/methods/conversations.history", "reason": "Read message history for a channel"}
            ]
        },
        {
            "topic": "Events & Interactivity",
            "references": [
                {"label": "Events API", "url": "https://api.slack.com/events-api", "reason": "Real-time event subscriptions"},
                {"label": "Socket Mode", "url": "https://api.slack.com/apis/connections/socket", "reason": "WebSocket-based event delivery without a public endpoint"},
                {"label": "App Manifest", "url": "https://api.slack.com/reference/manifests", "reason": "Declarative app configuration for reproducible setup"}
            ]
        }
    ],
    "implementation_notes": {
        "customer_page_must_include": [
            "App creation and OAuth scope configuration",
            "Message posting with Block Kit formatting",
            "Channel membership requirements for bot access",
            "Event handling patterns for both Events API and Socket Mode",
            "Rate limit tier awareness and backoff implementation",
            "Message search capabilities and limitations"
        ],
        "doc_gaps_or_unclear_areas": [
            "Rate limit tiers per individual method are not aggregated in a single reference page",
            "Socket Mode reconnection and error handling best practices are minimally documented",
            "Enterprise Grid multi-workspace token scoping is complex and not clearly summarized"
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
        if existing:
            continue

        content_json = example["content_json"]
        html = render_agent_page_html(
            content_json=content_json,
            product_name=example["product_name"],
            slug=slug,
            mode="full",
        )

        agent_page = AgentPage(
            product_name=example["product_name"],
            company_slug=slug,
            docs_url=example["docs_url"],
            email=example["email"],
            status="full_ready",
            payment_status="paid",
            crawl_scope="full",
            full_content_json=content_json,
            full_html=html,
            draft_content_json=content_json,
            draft_html=render_agent_page_html(
                content_json=content_json,
                product_name=example["product_name"],
                slug=slug,
                mode="draft",
            ),
        )
        db.add(agent_page)
        logger.info(f"Seeded example agent page: {slug}")
