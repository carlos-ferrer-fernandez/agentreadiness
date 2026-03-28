"""
Public Viewer Router

Serves hosted optimization results at shareable URLs.
All endpoints are public (no auth) — source docs were already public.

SEED_EXAMPLES contains hand-crafted optimized docs for well-known products,
demonstrating the optimizer's output quality before any paying customers exist.
These are prepended to DB results in the gallery and served by their seed IDs.
"""

import json
import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Assessment

router = APIRouter()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Seed examples — real company docs, hand-optimized to showcase output quality
# ---------------------------------------------------------------------------

SEED_EXAMPLES = {
    "seed-stripe": {
        "id": "seed-stripe",
        "site_name": "Stripe Payments",
        "url": "https://docs.stripe.com",
        "score": 39,
        "grade": "D",
        "created_at": "2026-03-10T09:00:00",
        "is_seed": True,
        "optimization_docs": [
            {
                "file_name": "payment-intents.md",
                "title": "Create a PaymentIntent",
                "original_url": "https://docs.stripe.com/api/payment_intents/create",
                "improvements": ["Added parameter table", "Structured error codes", "Explicit webhook events", "Agent context header"],
                "optimized_content": """# Create a PaymentIntent

**Agent context:** Use this endpoint to start a payment. A PaymentIntent tracks the lifecycle of a customer checkout. You must confirm it (client-side or server-side) before funds move. Most integrations create a PaymentIntent on the server and confirm it in the browser using Stripe.js.

`POST /v1/payment_intents`

## Required parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `amount` | integer | Amount in smallest currency unit. 2000 = $20.00 USD. No decimals. |
| `currency` | string | Three-letter ISO 4217 code. Lowercase. Example: `usd`, `eur`, `gbp`. |

## Common optional parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `customer` | string | Stripe Customer ID (`cus_...`). Attach to save payment method for reuse. |
| `payment_method_types` | array | Defaults to `["card"]`. Also: `"sepa_debit"`, `"bancontact"`, `"ideal"`. |
| `confirm` | boolean | If `true`, attempt to confirm immediately. Skip the separate confirm step. |
| `return_url` | string | Required when `confirm: true`. URL to redirect after authentication. |
| `automatic_payment_methods` | object | `{ enabled: true }` — lets Stripe pick the best method per customer location. |
| `metadata` | object | Up to 50 key-value pairs. Not shown to customers. Use for internal order IDs. |
| `statement_descriptor` | string | Text on customer's bank statement. Max 22 characters. |

## Minimal example

```bash
curl https://api.stripe.com/v1/payment_intents \\
  -u sk_test_...: \\
  -d amount=2000 \\
  -d currency=usd
```

## Response

```json
{
  "id": "pi_3OqE...",
  "object": "payment_intent",
  "amount": 2000,
  "currency": "usd",
  "status": "requires_payment_method",
  "client_secret": "pi_3OqE..._secret_..."
}
```

Pass `client_secret` to Stripe.js on the frontend to complete the payment.

## PaymentIntent status lifecycle

```
requires_payment_method
  → requires_confirmation
  → requires_action        (3D Secure, bank redirect)
  → processing
  → succeeded              ← payment complete
  → canceled               ← terminal, funds not captured
```

## Error codes

| Code | Meaning | Fix |
|------|---------|-----|
| `card_declined` | Bank refused the charge | Ask customer to try a different card |
| `insufficient_funds` | Card has no funds | Ask customer to try a different card |
| `invalid_expiry_year` | Expiry year invalid | Re-collect card details |
| `payment_intent_authentication_failure` | 3DS failed | Retry or use a different payment method |
| `amount_too_small` | Amount below minimum | Minimum varies by currency; USD minimum is $0.50 |

## Webhook events triggered

- `payment_intent.created` — fires immediately on creation
- `payment_intent.payment_failed` — fires after a declined charge attempt
- `payment_intent.succeeded` — fires when funds are captured; **use this to fulfil orders**
- `payment_intent.canceled` — fires when canceled

**Do not fulfil orders on the API response alone** — use the `payment_intent.succeeded` webhook. API calls can time out; the webhook is the authoritative success signal.
""",
            },
            {
                "file_name": "webhooks.md",
                "title": "Handling Stripe Webhooks",
                "original_url": "https://docs.stripe.com/webhooks",
                "improvements": ["Structured event table", "Explicit signature verification steps", "Added retry behavior", "Added idempotency guidance"],
                "optimized_content": """# Handling Stripe Webhooks

**Agent context:** Webhooks are POST requests Stripe sends to your server when events happen in your account. They are the authoritative signal for payment outcomes — more reliable than polling the API or trusting the redirect return URL.

## Setup

1. Create an endpoint in your app at a path like `/webhooks/stripe`. This must be publicly reachable (not localhost in production).
2. In the Stripe Dashboard → Developers → Webhooks, add your endpoint URL and select which events to receive.
3. Copy the **Webhook Signing Secret** (starts with `whsec_`). You need this to verify signatures.

## Verify every webhook (mandatory)

Stripe signs each webhook with your signing secret. **Always verify before processing.** An unverified webhook is an open door for spoofed events.

```python
import stripe
from fastapi import Request, HTTPException

stripe.api_key = "sk_live_..."
WEBHOOK_SECRET = "whsec_..."

async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "payment_intent.succeeded":
        pi = event["data"]["object"]
        fulfil_order(pi["metadata"]["order_id"])

    return {"received": True}
```

Always return **200 OK** immediately — even if your processing fails. Stripe retries on non-200 responses. Process asynchronously (queue the event) to avoid timeouts on long-running fulfilment logic.

## Key events reference

| Event | Trigger | Typical use |
|-------|---------|-------------|
| `payment_intent.succeeded` | Payment captured | Fulfil the order |
| `payment_intent.payment_failed` | Charge declined | Notify customer, prompt retry |
| `customer.subscription.created` | New subscription | Provision access |
| `customer.subscription.updated` | Plan change or renewal | Update access level |
| `customer.subscription.deleted` | Subscription canceled/expired | Revoke access |
| `invoice.payment_succeeded` | Recurring invoice paid | Extend subscription period |
| `invoice.payment_failed` | Recurring payment failed | Send dunning email |
| `checkout.session.completed` | Stripe Checkout completed | Fulfil order (alternative to PI webhook) |

## Retry behavior

Stripe retries failed webhooks up to **18 times over 3 days** with exponential backoff. Design your handlers to be **idempotent** — use the event `id` as a deduplication key. If your database already has a row for `evt_abc123`, skip processing and return 200.

```python
if db.webhook_processed(event["id"]):
    return {"received": True}  # already handled — return 200 silently
```

## Testing locally

```bash
stripe listen --forward-to localhost:8000/webhooks/stripe
stripe trigger payment_intent.succeeded
```
""",
            },
            {
                "file_name": "errors.md",
                "title": "Error Handling",
                "original_url": "https://docs.stripe.com/error-handling",
                "improvements": ["Structured error type table", "Explicit retry logic", "Added HTTP status mapping", "Agent-readable decision tree"],
                "optimized_content": """# Stripe Error Handling

**Agent context:** Stripe errors are structured objects with a `type`, `code`, and `message`. The type tells you the category; the code tells you the specific cause. Always branch on `type` first, then `code` for user-facing messages.

## Error object structure

```json
{
  "error": {
    "type": "card_error",
    "code": "card_declined",
    "decline_code": "insufficient_funds",
    "message": "Your card has insufficient funds.",
    "param": null,
    "charge": "ch_3Oq..."
  }
}
```

## Error types

| Type | Meaning | Retry? | Show to user? |
|------|---------|--------|---------------|
| `card_error` | Card was declined or invalid | No | Yes — use `message` field |
| `invalid_request_error` | Bad API call (wrong params, wrong IDs) | Fix the code first | No |
| `api_error` | Stripe-side error (rare) | Yes, with backoff | Generic "try again" message |
| `authentication_error` | Wrong or missing API key | No | No — fix your config |
| `rate_limit_error` | Too many requests | Yes, with backoff | No — queue and retry |
| `idempotency_error` | Conflicting idempotency key reuse | No | No — change the key |

## Decision tree for handling errors

```
HTTP 402 card_error
  → code: card_declined  → show decline_code message, ask customer to retry
  → code: expired_card   → re-collect card details
  → code: incorrect_cvc  → re-collect CVC

HTTP 400 invalid_request_error
  → Log the full error. This is a code bug. Do not show to users.

HTTP 500 api_error
  → Retry with exponential backoff (3 attempts max).
  → If still failing, surface generic error to user and alert your on-call.

HTTP 429 rate_limit_error
  → Queue the request. Retry after Retry-After header value (or 60s).
```

## Retry with idempotency keys

For `api_error` and `rate_limit_error`, retry safely using idempotency keys:

```python
import stripe
import uuid

idempotency_key = str(uuid.uuid4())  # generate once per attempt series

try:
    intent = stripe.PaymentIntent.create(
        amount=2000,
        currency="usd",
        idempotency_key=idempotency_key,  # same key on retries
    )
except stripe.error.APIError:
    time.sleep(2)
    intent = stripe.PaymentIntent.create(
        amount=2000,
        currency="usd",
        idempotency_key=idempotency_key,  # Stripe deduplicates
    )
```

## Common `decline_code` values

| Code | Cause | Recommended message |
|------|-------|---------------------|
| `insufficient_funds` | No funds | "Your card has insufficient funds. Try a different card." |
| `do_not_honor` | Generic bank decline | "Your card was declined. Contact your bank or try another card." |
| `card_not_supported` | Feature not supported | "This card doesn't support this payment type. Try a different card." |
| `lost_card` / `stolen_card` | Flagged as fraudulent | Do not reveal reason. "Card declined." |
| `fraudulent` | Stripe fraud detection | Do not reveal reason. "Card declined." |
""",
            },
        ],
    },

    "seed-twilio": {
        "id": "seed-twilio",
        "site_name": "Twilio Messaging",
        "url": "https://www.twilio.com/docs/sms",
        "score": 44,
        "grade": "C-",
        "created_at": "2026-03-12T14:00:00",
        "is_seed": True,
        "optimization_docs": [
            {
                "file_name": "send-sms.md",
                "title": "Send an SMS Message",
                "original_url": "https://www.twilio.com/docs/sms/api/message-resource",
                "improvements": ["Added parameter table", "Added character limit guidance", "Structured error codes", "Encoding types explained"],
                "optimized_content": """# Send an SMS Message

**Agent context:** Use the Messages resource to send SMS and MMS. You need a Twilio phone number (from → number) and the recipient's number (to → number). Messages are queued asynchronously — the API returns immediately with a `sid`; delivery status comes via webhook or polling.

`POST https://api.twilio.com/2010-04-01/Accounts/{AccountSid}/Messages.json`

Authenticate with HTTP Basic Auth: `AccountSid` as username, `AuthToken` as password.

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `To` | ✓ | Recipient phone number in E.164 format: `+15551234567` |
| `From` | ✓* | Your Twilio number in E.164 format. *Or use `MessagingServiceSid`. |
| `MessagingServiceSid` | ✓* | Use instead of `From` to use a Messaging Service (sender pool). |
| `Body` | ✓* | SMS text content. Required unless sending MMS with media. |
| `MediaUrl` | ✓* | MMS: publicly accessible URL of image/video. Required for MMS. |
| `StatusCallback` | | Webhook URL for delivery status updates. Highly recommended. |

## Character limits

| Encoding | Characters per segment | Notes |
|----------|----------------------|-------|
| GSM-7 (standard ASCII) | 160 per segment | Most Latin-alphabet messages |
| UCS-2 (Unicode) | 70 per segment | Triggered by any emoji or non-Latin character |

Messages over one segment are split and reassembled. Carriers charge per segment. Check `Body` length before sending — an emoji at the end of a 155-char message turns it into two UCS-2 segments (140 chars total).

## Example

```python
from twilio.rest import Client

client = Client("ACxxx", "auth_token")

message = client.messages.create(
    to="+15551234567",
    from_="+15559876543",
    body="Your verification code is 847291. Expires in 10 minutes.",
    status_callback="https://yourapp.com/webhooks/twilio/status",
)

print(message.sid)  # SM...
```

## Response fields

| Field | Description |
|-------|-------------|
| `sid` | Unique message ID (`SM...`). Use to poll status. |
| `status` | Initial status: `queued`. See status lifecycle below. |
| `direction` | `outbound-api` for messages you send |
| `price` | Cost in USD (populated after delivery) |
| `error_code` | Null unless failed. See error codes below. |

## Message status lifecycle

```
queued → sending → sent → delivered   ← success
                        → undelivered  ← carrier rejected
                  → failed             ← never left Twilio
```

Subscribe to `StatusCallback` to receive POST requests at each transition.

## Error codes

| Code | Meaning | Fix |
|------|---------|-----|
| 21211 | Invalid `To` number | Validate E.164 format before sending |
| 21408 | Permission to send to region not enabled | Enable region in Console |
| 21610 | `To` number is on opt-out list | Do not send; honour unsubscribe |
| 21614 | `To` number is not a mobile number | SMS cannot be delivered to landlines |
| 30003 | Unreachable destination | Number may be disconnected |
| 30008 | Unknown error from carrier | Retry once; if persistent, use different sender |
""",
            },
            {
                "file_name": "messaging-services.md",
                "title": "Messaging Services",
                "original_url": "https://www.twilio.com/docs/messaging/services",
                "improvements": ["Clarified sender pool behavior", "Added throughput table", "Structured use cases", "Sticky sender explained"],
                "optimized_content": """# Twilio Messaging Services

**Agent context:** A Messaging Service is a pool of sender numbers managed by Twilio. Use it instead of a single `From` number to get higher throughput, automatic number selection, and sticky sender behavior. Required for A2P 10DLC compliance in the US.

## When to use a Messaging Service

| Scenario | Use single number | Use Messaging Service |
|----------|------------------|----------------------|
| Low volume (< 1 msg/sec) | ✓ | Optional |
| High volume or campaigns | | ✓ Required |
| Conversational (2-way) messaging | | ✓ Sticky sender keeps same number per user |
| US A2P 10DLC compliance | | ✓ Required |
| Short codes | Possible | ✓ Preferred |

## Throughput by sender type

| Sender type | Max throughput | Best for |
|-------------|---------------|---------|
| Long code (10DLC, registered) | 10 msg/sec per number | Transactional, conversational |
| Toll-free number | 3 msg/sec | Notifications, marketing |
| Short code | 100 msg/sec | High-volume campaigns, OTP |

A Messaging Service pools numbers to multiply throughput. 10 registered long codes = 100 msg/sec.

## Create a Messaging Service

```python
service = client.messaging.v1.services.create(
    friendly_name="Order Notifications",
    inbound_request_url="https://yourapp.com/webhooks/twilio/inbound",
    status_callback="https://yourapp.com/webhooks/twilio/status",
)
print(service.sid)  # MG...
```

Add phone numbers to the service:

```python
client.messaging.v1.services(service.sid).phone_numbers.create(
    phone_number_sid="PNxxx"  # SID of your Twilio number
)
```

## Send using the Messaging Service

```python
message = client.messages.create(
    to="+15551234567",
    messaging_service_sid="MGxxx",  # use instead of from_
    body="Your order has shipped. Track at: https://...",
)
```

## Sticky sender

When enabled, Twilio routes all messages to a given `To` number through the same `From` number. This makes conversations feel coherent — the customer always sees the same number.

Enable in Console: Messaging Service → Settings → Sticky Sender → On.

**Important:** Sticky sender only works if you have enough numbers in the pool. If the sticky number is unavailable, Twilio falls back to a different number.

## Opt-out handling

Twilio automatically handles STOP/UNSTOP/HELP replies on all Messaging Services. When a user replies STOP:
- Twilio adds them to the opt-out list
- Sending to that number returns error code 21610
- Twilio replies automatically with your opt-out confirmation message

Configure the opt-out message in Console: Messaging Service → Compliance.
""",
            },
        ],
    },

    "seed-resend": {
        "id": "seed-resend",
        "site_name": "Resend Email API",
        "url": "https://resend.com/docs",
        "score": 52,
        "grade": "C-",
        "created_at": "2026-03-14T11:00:00",
        "is_seed": True,
        "optimization_docs": [
            {
                "file_name": "send-email.md",
                "title": "Send an Email",
                "original_url": "https://resend.com/docs/api-reference/emails/send-email",
                "improvements": ["Added full parameter table", "Added idempotency guidance", "Rate limit documented", "Batch sending noted"],
                "optimized_content": """# Send an Email

**Agent context:** The `/emails` endpoint sends a transactional email. You need a verified domain (or use the `onboarding@resend.dev` sandbox sender for testing). Emails are delivered asynchronously — the API returns an `id`; actual delivery status comes via webhooks.

`POST https://api.resend.com/emails`

Authentication: `Authorization: Bearer re_...` header.

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `from` | string | ✓ | Sender address. Must be from a verified domain. Format: `Name <email>` or `email`. |
| `to` | string / array | ✓ | Recipient(s). String for one, array for multiple (max 50). |
| `subject` | string | ✓ | Email subject line. |
| `html` | string | ✓* | HTML body. Required unless `text` is provided. |
| `text` | string | ✓* | Plain text fallback. Recommended alongside `html`. |
| `cc` | string / array | | CC recipients. |
| `bcc` | string / array | | BCC recipients. |
| `reply_to` | string / array | | Reply-to address(es). |
| `headers` | object | | Custom headers. Key-value pairs. |
| `attachments` | array | | File attachments. See structure below. |
| `tags` | array | | `[{ "name": "category", "value": "transactional" }]`. For filtering in dashboard. |

## Example

```typescript
import { Resend } from 'resend';

const resend = new Resend('re_...');

const { data, error } = await resend.emails.send({
  from: 'Acme <notifications@acme.com>',
  to: ['user@example.com'],
  subject: 'Your order has shipped',
  html: '<p>Your order <strong>#1234</strong> has shipped. Track it <a href="...">here</a>.</p>',
  text: 'Your order #1234 has shipped.',
  tags: [{ name: 'category', value: 'order-shipped' }],
});

if (error) {
  console.error(error);
  return;
}

console.log(data.id);  // email ID for status lookup
```

## Response

```json
{
  "id": "49a3999c-0ce1-4ea6-ab68-afcd6dc2e794"
}
```

Use the `id` to retrieve delivery status via `GET /emails/{id}` or subscribe to webhook events.

## Attachments structure

```json
{
  "attachments": [
    {
      "filename": "invoice.pdf",
      "content": "<base64-encoded content>"
    }
  ]
}
```

Max total attachment size: 40 MB.

## Rate limits

| Plan | Limit |
|------|-------|
| Free | 100 emails/day, 1 request/sec |
| Pro | 50,000 emails/month, 10 requests/sec |
| Enterprise | Custom |

For bulk sending (newsletters, digests), use the Batch endpoint: `POST /emails/batch` — up to 100 emails per request, processed in parallel.

## Error responses

| HTTP | Code | Meaning |
|------|------|---------|
| 422 | `validation_error` | Invalid parameters. Check `message` for field details. |
| 401 | `missing_api_key` | No `Authorization` header. |
| 403 | `invalid_api_key` | Key is wrong or revoked. |
| 429 | `rate_limit_exceeded` | Slow down. Retry after `Retry-After` header value. |
| 451 | `security_error` | Domain not verified, or sending from unverified address. |
""",
            },
            {
                "file_name": "domains.md",
                "title": "Domain Verification",
                "original_url": "https://resend.com/docs/dashboard/domains/introduction",
                "improvements": ["Step-by-step DNS record table", "Verification timing documented", "SPF/DKIM/DMARC explained concisely", "Troubleshooting table added"],
                "optimized_content": """# Domain Verification

**Agent context:** You must verify ownership of a domain before sending from it. Verification requires adding DNS records to your domain. Once verified, you can send from any address at that domain (e.g., `no-reply@yourdomain.com`, `alerts@yourdomain.com`). Without verification, you can only use the `onboarding@resend.dev` sandbox.

## Step 1: Add the domain in Resend

Dashboard → Domains → Add Domain → enter your domain name (e.g., `yourdomain.com`).

Resend generates three DNS records for you to add at your DNS provider.

## Step 2: Add DNS records

| Record type | Name | Value | Purpose |
|-------------|------|-------|---------|
| TXT | `resend._domainkey` | Provided by Resend | DKIM signing — proves Resend sent the email |
| MX | `send` (subdomain) | `feedback-smtp.us-east-1.amazonses.com` | Bounce/complaint handling |
| TXT | `send` (subdomain) | `v=spf1 include:amazonses.com ~all` | SPF — authorises Resend's servers to send on your behalf |

**Add all three.** Missing DKIM causes emails to land in spam. Missing SPF lowers deliverability. Missing MX breaks bounce handling.

## Step 3: Wait for propagation

DNS changes propagate in **5 minutes to 48 hours**. Resend checks automatically every few minutes. You'll see status change from `Pending` to `Verified` in the Dashboard.

Force a check: Dashboard → Domains → your domain → Verify.

## DMARC (recommended)

DMARC tells receiving mail servers what to do if SPF or DKIM fails. Add this TXT record at `_dmarc.yourdomain.com`:

```
v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.com
```

Start with `p=none` (monitor only), then move to `p=quarantine` after confirming your legitimate email passes. DMARC is not required by Resend but is required by Gmail/Yahoo for bulk senders (> 5,000 msgs/day).

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Stuck on `Pending` after 48 hours | DNS record not added or typo | Check with `dig TXT resend._domainkey.yourdomain.com` |
| Emails landing in spam | DKIM not verified or DMARC missing | Verify all records; add DMARC |
| `security_error` on send | Sending from unverified address | Confirm the domain matches verified domain |
| `invalid_api_key` on send | Wrong API key environment | Check you're using a live key (not test key) for production |

## Subdomains

You can verify a subdomain separately (e.g., `mail.yourdomain.com`). This isolates transactional email reputation from your main domain — recommended for high-volume or bulk sending.
""",
            },
            {
                "file_name": "webhooks.md",
                "title": "Email Webhooks",
                "original_url": "https://resend.com/docs/dashboard/webhooks/introduction",
                "improvements": ["Event table with fields", "Retry behavior documented", "Signature verification added", "Idempotency key guidance"],
                "optimized_content": """# Email Webhooks

**Agent context:** Resend sends webhook events to your endpoint as emails progress through delivery. Subscribe to these to track opens, clicks, bounces, and spam complaints. Essential for suppression list management and delivery monitoring.

## Event types

| Event | When it fires | Key fields |
|-------|--------------|-----------|
| `email.sent` | Email accepted by Resend, handed to provider | `email_id`, `from`, `to` |
| `email.delivered` | Provider confirmed delivery to recipient server | `email_id` |
| `email.delivery_delayed` | Temporary delivery failure; Resend will retry | `email_id` |
| `email.bounced` | Permanent bounce — address doesn't exist | `email_id`, `bounce.type` |
| `email.complained` | Recipient marked as spam | `email_id` |
| `email.opened` | Recipient opened email (tracking pixel) | `email_id` |
| `email.clicked` | Recipient clicked a tracked link | `email_id`, `click.link` |

## Webhook payload shape

```json
{
  "type": "email.bounced",
  "created_at": "2026-03-14T10:12:00Z",
  "data": {
    "email_id": "49a3999c-0ce1-4ea6-ab68-afcd6dc2e794",
    "from": "notifications@acme.com",
    "to": ["user@example.com"],
    "subject": "Your order has shipped",
    "bounce": {
      "type": "hard"
    }
  }
}
```

## Signature verification

Resend signs each webhook with HMAC-SHA256 using your webhook signing secret.

```python
import hmac
import hashlib

def verify_webhook(payload: bytes, signature_header: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)
```

Get the signing secret from Dashboard → Webhooks → your endpoint → Signing Secret.

## Handling bounces and complaints

**Hard bounces** (type `hard`) — permanent failure. Remove the address from your list immediately. Sending to known hard-bounce addresses harms your sender reputation.

**Complaints** (`email.complained`) — the recipient marked your email as spam. Remove from all marketing lists immediately. Required by CAN-SPAM and GDPR.

```python
if event["type"] == "email.bounced":
    if event["data"]["bounce"]["type"] == "hard":
        suppress_address(event["data"]["to"][0])

if event["type"] == "email.complained":
    suppress_address(event["data"]["to"][0])
```

## Retry behavior

Resend retries failed webhooks (non-2xx response or timeout) up to **3 times** over **1 hour**. Make your handler idempotent using `data.email_id` as a deduplication key. Return 200 immediately — process asynchronously to avoid timeouts.
""",
            },
        ],
    },
}


def _seed_to_gallery_item(seed: dict) -> dict:
    return {
        "id": seed["id"],
        "site_name": seed["site_name"],
        "url": seed["url"],
        "score": seed["score"],
        "grade": seed["grade"],
        "page_count": len(seed["optimization_docs"]),
        "created_at": seed["created_at"],
        "is_seed": True,
    }


def _seed_to_index(seed: dict) -> dict:
    pages = [
        {
            "file_name": d["file_name"],
            "title": d["title"],
            "original_url": d["original_url"],
            "improvements": d.get("improvements", []),
        }
        for d in seed["optimization_docs"]
    ]
    return {
        "id": seed["id"],
        "site_name": seed["site_name"],
        "url": seed["url"],
        "score": seed["score"],
        "grade": seed["grade"],
        "pages": pages,
        "created_at": seed["created_at"],
        "is_seed": True,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/public")
async def list_public_optimizations(db: AsyncSession = Depends(get_db)):
    """List showcase-worthy optimizations. Seed examples always appear first."""
    result = await db.execute(
        select(Assessment)
        .where(and_(
            Assessment.has_paid == True,
            Assessment.optimization_status == "complete",
        ))
        .order_by(Assessment.created_at.desc())
        .limit(24)
    )
    assessments = result.scalars().all()

    db_items = [
        {
            "id": a.id,
            "site_name": a.site_name,
            "url": a.url,
            "score": a.score,
            "grade": a.grade,
            "page_count": len(a.optimization_docs) if a.optimization_docs else 0,
            "created_at": a.created_at.isoformat(),
        }
        for a in assessments
    ]

    seed_items = [_seed_to_gallery_item(s) for s in SEED_EXAMPLES.values()]
    return seed_items + db_items


@router.get("/{assessment_id}")
async def get_viewer_index(assessment_id: str, db: AsyncSession = Depends(get_db)):
    """Return optimization metadata and page list for the viewer."""
    # Check seed examples first
    if assessment_id in SEED_EXAMPLES:
        return _seed_to_index(SEED_EXAMPLES[assessment_id])

    result = await db.execute(
        select(Assessment).where(Assessment.id == assessment_id)
    )
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Not found")
    if not assessment.has_paid or assessment.optimization_status != "complete":
        raise HTTPException(status_code=403, detail="Optimization not available")

    docs = assessment.optimization_docs or []
    if isinstance(docs, str):
        docs = json.loads(docs)

    pages = [
        {
            "file_name": d["file_name"],
            "title": d["title"],
            "original_url": d["original_url"],
            "improvements": d.get("improvements", []),
        }
        for d in docs
    ]

    return {
        "id": assessment.id,
        "site_name": assessment.site_name,
        "url": assessment.url,
        "score": assessment.score,
        "grade": assessment.grade,
        "pages": pages,
        "created_at": assessment.created_at.isoformat(),
    }


@router.get("/{assessment_id}/{file_name}")
async def get_optimized_page(
    assessment_id: str,
    file_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Return a single optimized page's content."""
    # Check seed examples first
    if assessment_id in SEED_EXAMPLES:
        seed = SEED_EXAMPLES[assessment_id]
        page = next((d for d in seed["optimization_docs"] if d["file_name"] == file_name), None)
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        return {
            "title": page["title"],
            "original_url": page["original_url"],
            "optimized_content": page["optimized_content"],
            "improvements": page.get("improvements", []),
            "site_name": seed["site_name"],
            "assessment_id": assessment_id,
        }

    result = await db.execute(
        select(Assessment).where(Assessment.id == assessment_id)
    )
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Not found")
    if not assessment.has_paid or assessment.optimization_status != "complete":
        raise HTTPException(status_code=403, detail="Optimization not available")

    docs = assessment.optimization_docs or []
    if isinstance(docs, str):
        docs = json.loads(docs)

    page = next((d for d in docs if d["file_name"] == file_name), None)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    return {
        "title": page["title"],
        "original_url": page["original_url"],
        "optimized_content": page["optimized_content"],
        "improvements": page.get("improvements", []),
        "site_name": assessment.site_name,
        "assessment_id": assessment_id,
    }
