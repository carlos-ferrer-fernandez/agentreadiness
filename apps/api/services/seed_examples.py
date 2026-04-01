"""
Seed Example Agent Pages

Pre-built showcase pages for Stripe, Vercel, Notion, and Slack.
These are realistic, hand-crafted JSON objects used as demo content.
"""

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import AgentPage
from services.agent_page_generator import render_agent_page_html

logger = logging.getLogger(__name__)


EXAMPLE_PAGES = [
    {
        "product_name": "Stripe",
        "company_slug": "stripe",
        "docs_url": "https://docs.stripe.com",
        "email": "demo@groundocs.com",
        "content_json": {
            "product_name": "Stripe",
            "slug": "stripe",
            "mode": "full",
            "summary": "Stripe is a payments infrastructure platform that provides APIs for accepting payments, managing subscriptions, sending payouts, and building financial workflows programmatically.",
            "overview": {
                "what_it_is": "A full-stack payments platform with APIs for online payments, subscriptions, invoicing, Connect marketplace payouts, and financial reporting. Stripe handles PCI compliance, fraud detection, and global payment method support.",
                "what_agents_can_do": [
                    "Create and manage payment intents for one-time charges",
                    "Set up and modify subscription billing plans",
                    "Generate invoices and send them to customers",
                    "Issue refunds (full or partial)",
                    "Create connected accounts for marketplace payouts",
                    "Retrieve balance, transaction, and payout history",
                    "Manage customers, payment methods, and saved cards",
                    "Configure webhook endpoints to listen for events"
                ],
                "best_for": [
                    "SaaS billing and subscription management",
                    "E-commerce checkout flows",
                    "Marketplace and platform payment routing",
                    "Invoicing and accounts receivable automation",
                    "Recurring billing with usage-based metering"
                ]
            },
            "when_to_use": {
                "ideal_use_cases": [
                    "Accepting credit card payments online",
                    "Managing recurring subscriptions with trials and proration",
                    "Splitting payments between a platform and connected sellers",
                    "Sending programmatic invoices with line items",
                    "Issuing refunds or credits to customers"
                ],
                "non_ideal_use_cases": [
                    "In-person POS without Stripe Terminal hardware",
                    "Cryptocurrency or non-fiat payments (limited support)",
                    "Countries not in Stripe's supported list",
                    "High-risk merchant categories that Stripe prohibits"
                ]
            },
            "getting_started": {
                "prerequisites": [
                    "A Stripe account (sign up at dashboard.stripe.com)",
                    "API keys from the Stripe Dashboard (publishable + secret key)",
                    "HTTPS endpoint for production (required for webhooks and Checkout)"
                ],
                "required_accounts_or_access": [
                    "Stripe Dashboard access (owner or admin role)",
                    "Test mode API keys for development",
                    "Live mode API keys for production (requires account activation)"
                ],
                "setup_steps": [
                    "Install the Stripe SDK: pip install stripe (Python) or npm install stripe (Node)",
                    "Set your secret API key in environment variables: STRIPE_SECRET_KEY",
                    "Create a test payment intent to verify connectivity",
                    "Set up a webhook endpoint to handle asynchronous events",
                    "Switch to live mode keys when ready to accept real payments"
                ]
            },
            "authentication_access": {
                "auth_methods": [
                    "Secret API key (sk_test_... or sk_live_...) passed in Authorization: Bearer header",
                    "Restricted API keys with granular permissions for specific resources",
                    "Publishable key (pk_...) for client-side Stripe.js only"
                ],
                "permissions": [
                    "Secret key has full account access by default",
                    "Restricted keys can limit to specific resources (e.g., charges:write, customers:read)",
                    "Connect OAuth tokens for accessing connected accounts"
                ],
                "important_auth_notes": [
                    "Never expose secret keys in client-side code or version control",
                    "Test mode and live mode keys are separate and do not overlap",
                    "Webhook signatures must be verified using the webhook signing secret",
                    "API versioning is controlled via Stripe-Version header or Dashboard settings"
                ]
            },
            "core_capabilities": [
                {
                    "name": "Payment Intents",
                    "description": "Create, confirm, and capture payments with built-in SCA/3DS support. Supports 135+ currencies and dozens of payment methods.",
                    "requirements": ["Secret API key", "Valid payment method or source"],
                    "limitations": ["Minimum charge amount varies by currency (e.g., $0.50 USD)", "Some payment methods require specific confirmation flows"]
                },
                {
                    "name": "Subscriptions & Billing",
                    "description": "Recurring billing with plans, prices, trials, coupons, proration, and usage-based metering.",
                    "requirements": ["Customer object with payment method", "Price or Plan object configured"],
                    "limitations": ["Invoice finalization is asynchronous", "Proration behavior must be explicitly configured"]
                },
                {
                    "name": "Connect (Marketplaces)",
                    "description": "Split payments between platform and connected accounts. Supports Standard, Express, and Custom account types.",
                    "requirements": ["Platform Connect setup", "Connected account onboarding"],
                    "limitations": ["Payout timing depends on connected account country", "KYC requirements vary by account type"]
                },
                {
                    "name": "Webhooks",
                    "description": "Real-time event notifications for payment lifecycle events. Essential for handling asynchronous payment confirmation.",
                    "requirements": ["HTTPS endpoint", "Webhook signing secret for signature verification"],
                    "limitations": ["Events may be delivered out of order", "Retry logic: Stripe retries failed deliveries for up to 3 days"]
                }
            ],
            "recommended_workflows": [
                {
                    "name": "Accept a One-Time Payment",
                    "goal": "Charge a customer's card for a single purchase",
                    "steps": [
                        "Create a PaymentIntent with amount, currency, and payment_method_types",
                        "On the client, use Stripe.js to collect card details and confirm the PaymentIntent",
                        "Handle the payment_intent.succeeded webhook to fulfill the order",
                        "If 3D Secure is required, Stripe.js handles the redirect automatically"
                    ],
                    "success_checks": [
                        "PaymentIntent status is 'succeeded'",
                        "Webhook payment_intent.succeeded is received",
                        "Charge object shows amount_captured equals intended amount"
                    ],
                    "failure_risks": [
                        "Card declined: check the decline code in the error",
                        "3DS authentication fails: PaymentIntent moves to requires_payment_method",
                        "Network timeout: use idempotency keys to safely retry"
                    ]
                },
                {
                    "name": "Create a Subscription",
                    "goal": "Set up recurring billing for a customer",
                    "steps": [
                        "Create or retrieve a Customer object",
                        "Attach a PaymentMethod to the customer",
                        "Create a Subscription with the customer ID and price ID",
                        "Handle invoice.payment_succeeded and customer.subscription.updated webhooks",
                        "Manage lifecycle: upgrades, downgrades, cancellations, trial periods"
                    ],
                    "success_checks": [
                        "Subscription status is 'active'",
                        "First invoice is paid",
                        "Recurring invoices are generated on schedule"
                    ],
                    "failure_risks": [
                        "Payment method fails on renewal: subscription enters 'past_due' state",
                        "Smart Retries may recover some failed payments automatically",
                        "Missing webhook handler can cause fulfillment gaps"
                    ]
                }
            ],
            "input_output_expectations": {
                "common_inputs": [
                    "amount (integer in smallest currency unit, e.g., cents)",
                    "currency (3-letter ISO code, lowercase)",
                    "customer (Stripe customer ID, cus_...)",
                    "payment_method (pm_... or card token)",
                    "metadata (key-value pairs for your own tracking)"
                ],
                "common_outputs": [
                    "PaymentIntent object with id, status, amount, and client_secret",
                    "Subscription object with id, status, current_period_start/end",
                    "Invoice object with lines, total, status, and hosted_invoice_url",
                    "Event objects delivered to webhooks with type and data"
                ],
                "data_format_notes": [
                    "All amounts are in the smallest currency unit (e.g., 1000 = $10.00 USD)",
                    "Timestamps are Unix epoch seconds",
                    "IDs are prefixed strings (pi_, sub_, cus_, ch_, in_, etc.)",
                    "List endpoints support pagination with starting_after and limit"
                ]
            },
            "rules_constraints_caveats": [
                "API rate limit: 100 read requests/second, 100 write requests/second in live mode",
                "Idempotency keys are recommended for all POST requests to prevent duplicate charges",
                "Refunds must be issued within 180 days of the original charge",
                "PCI compliance: never log or store raw card numbers; use Stripe.js or Elements",
                "Webhook endpoints must respond with 2xx within 20 seconds or Stripe will retry",
                "Test mode data is completely separate from live mode data"
            ],
            "examples": [
                {
                    "title": "Create a Payment Intent",
                    "scenario": "Charge a customer $25.00 USD",
                    "example_instruction": "POST /v1/payment_intents with amount=2500, currency=usd, payment_method_types=['card']",
                    "expected_result": "Returns a PaymentIntent object with status 'requires_payment_method' and a client_secret for frontend confirmation"
                },
                {
                    "title": "Issue a Partial Refund",
                    "scenario": "Refund $10 of a $50 charge",
                    "example_instruction": "POST /v1/refunds with charge=ch_xxx, amount=1000",
                    "expected_result": "Returns a Refund object with status 'succeeded' and amount=1000"
                }
            ],
            "troubleshooting": [
                {
                    "issue": "Card declined errors",
                    "likely_causes": ["Insufficient funds", "Incorrect card number", "Card reported lost/stolen", "Issuer decline for suspicious activity"],
                    "recommended_fix": ["Check the decline_code in the error response", "Ask the customer to try another payment method", "For testing, use Stripe's test card numbers (e.g., 4000000000000002 for generic decline)"]
                },
                {
                    "issue": "Webhook signature verification fails",
                    "likely_causes": ["Wrong webhook signing secret (test vs live)", "Request body was parsed/modified before verification", "Clock skew between servers"],
                    "recommended_fix": ["Use the raw request body for signature verification", "Ensure you are using the correct endpoint secret from the Dashboard", "Check that your server clock is synchronized"]
                }
            ],
            "implementation_notes": {
                "what_should_appear_on_customer_agents_page": [
                    "API authentication setup and key management",
                    "Payment Intent creation and confirmation flow",
                    "Subscription lifecycle management",
                    "Webhook event handling patterns",
                    "Error handling and idempotency best practices"
                ],
                "missing_info_or_doc_gaps": [
                    "Country-specific payment method availability is spread across multiple pages",
                    "Connect fee calculation examples could be more detailed"
                ]
            },
            "canonical_references": [
                {"label": "Stripe API Reference", "url": "https://docs.stripe.com/api", "reason": "Complete API endpoint documentation with request/response examples"},
                {"label": "Stripe Payments Guide", "url": "https://docs.stripe.com/payments", "reason": "Step-by-step guides for payment integration patterns"},
                {"label": "Stripe Billing Guide", "url": "https://docs.stripe.com/billing", "reason": "Subscription and invoicing documentation"},
                {"label": "Stripe Testing", "url": "https://docs.stripe.com/testing", "reason": "Test card numbers, webhook testing, and sandbox usage"}
            ]
        },
    },
    {
        "product_name": "Vercel",
        "company_slug": "vercel",
        "docs_url": "https://vercel.com/docs",
        "email": "demo@groundocs.com",
        "content_json": {
            "product_name": "Vercel",
            "slug": "vercel",
            "mode": "full",
            "summary": "Vercel is a cloud platform for frontend frameworks and static sites that provides instant deployments, serverless functions, edge computing, and a global CDN. It is the company behind Next.js.",
            "overview": {
                "what_it_is": "A deployment and hosting platform optimized for frontend applications. Vercel builds your project from a Git repository, deploys it to a global edge network, provisions HTTPS, and provides serverless/edge function runtimes.",
                "what_agents_can_do": [
                    "Deploy projects from Git repositories with zero configuration",
                    "Create and manage environment variables",
                    "Trigger redeployments programmatically via API",
                    "Configure custom domains and DNS settings",
                    "Manage team members and access controls",
                    "Monitor deployment logs and serverless function invocations",
                    "Set up preview deployments for pull requests"
                ],
                "best_for": [
                    "Next.js, Nuxt, SvelteKit, and Astro applications",
                    "Static sites and JAMstack architectures",
                    "Preview deployments for code review workflows",
                    "Serverless API routes and edge functions",
                    "Global content delivery with automatic caching"
                ]
            },
            "when_to_use": {
                "ideal_use_cases": [
                    "Deploying frontend frameworks with server-side rendering",
                    "Hosting static marketing sites with instant global delivery",
                    "Creating preview URLs for every pull request",
                    "Running lightweight serverless API endpoints",
                    "Projects that benefit from edge computing (low-latency responses)"
                ],
                "non_ideal_use_cases": [
                    "Long-running backend processes (serverless has 10s-300s timeout limits)",
                    "Applications requiring persistent server state or WebSocket connections",
                    "Heavy database workloads (use a dedicated database provider)",
                    "Monolithic backend applications not built on supported frameworks"
                ]
            },
            "getting_started": {
                "prerequisites": [
                    "A Vercel account (vercel.com/signup)",
                    "A Git repository on GitHub, GitLab, or Bitbucket",
                    "Node.js 18+ installed locally for CLI usage"
                ],
                "required_accounts_or_access": [
                    "Vercel Dashboard access",
                    "Git provider connected to Vercel for automatic deployments",
                    "API token from Settings > Tokens for programmatic access"
                ],
                "setup_steps": [
                    "Install the Vercel CLI: npm i -g vercel",
                    "Run 'vercel' in your project directory to link and deploy",
                    "Connect your Git repository in the Vercel Dashboard for automatic deployments",
                    "Configure environment variables in Project Settings > Environment Variables",
                    "Set up a custom domain in Project Settings > Domains"
                ]
            },
            "authentication_access": {
                "auth_methods": [
                    "Bearer token in Authorization header for REST API",
                    "Vercel CLI authentication via 'vercel login'",
                    "OAuth integration for Git providers"
                ],
                "permissions": [
                    "API tokens are scoped to a user or team",
                    "Team roles: Owner, Member, Viewer, Developer",
                    "Project-level access controls for environment variables"
                ],
                "important_auth_notes": [
                    "API tokens do not expire by default but can be revoked",
                    "Team tokens have the permissions of the team, not the creating user",
                    "Environment variables can be scoped to production, preview, or development"
                ]
            },
            "core_capabilities": [
                {
                    "name": "Git-Based Deployments",
                    "description": "Every push to a connected Git repository triggers a new deployment. Main branch deploys to production; other branches create preview URLs.",
                    "requirements": ["Git repository connected via Dashboard"],
                    "limitations": ["Build time limit: 45 minutes on Pro, 10 minutes on Hobby", "Deployment size limit: 100MB compressed"]
                },
                {
                    "name": "Serverless Functions",
                    "description": "Deploy backend logic as serverless functions in the /api directory. Supports Node.js, Python, Go, and Ruby runtimes.",
                    "requirements": ["Functions placed in /api directory or defined via framework conventions"],
                    "limitations": ["Execution timeout: 10s (Hobby), 60s (Pro), 300s (Enterprise)", "Payload size limit: 4.5MB", "No persistent file system between invocations"]
                },
                {
                    "name": "Edge Functions",
                    "description": "Run code at the edge (closest to the user) with sub-millisecond cold starts. Uses the V8 runtime (Web APIs).",
                    "requirements": ["Export config with runtime: 'edge' in your function"],
                    "limitations": ["Limited to Web APIs (no Node.js built-in modules)", "1MB code size limit", "No native npm packages that require Node.js APIs"]
                },
                {
                    "name": "Preview Deployments",
                    "description": "Every pull request gets a unique preview URL with the full deployment. Teams can comment and review directly on the preview.",
                    "requirements": ["Git integration enabled"],
                    "limitations": ["Preview URLs are publicly accessible by default (can be restricted on Enterprise)"]
                }
            ],
            "recommended_workflows": [
                {
                    "name": "Deploy a Next.js Application",
                    "goal": "Ship a Next.js app to production with automatic deployments",
                    "steps": [
                        "Push your Next.js project to a GitHub repository",
                        "Import the repository in the Vercel Dashboard",
                        "Vercel auto-detects Next.js and configures the build",
                        "Set any required environment variables",
                        "First deployment happens automatically; subsequent pushes trigger new deployments"
                    ],
                    "success_checks": [
                        "Deployment status shows 'Ready' in Dashboard",
                        "Production URL returns expected content",
                        "Serverless functions in /api respond correctly"
                    ],
                    "failure_risks": [
                        "Build fails: check build logs for dependency or configuration errors",
                        "Environment variables missing: functions return 500 errors",
                        "Framework version mismatch: ensure package.json matches expected Node version"
                    ]
                },
                {
                    "name": "Programmatic Redeployment via API",
                    "goal": "Trigger a redeployment from a CI/CD pipeline or external system",
                    "steps": [
                        "Generate an API token in Vercel Dashboard > Settings > Tokens",
                        "POST to https://api.vercel.com/v13/deployments with project and target",
                        "Include Authorization: Bearer <token> header",
                        "Poll the deployment status endpoint until state is 'READY'"
                    ],
                    "success_checks": [
                        "API returns 200 with deployment ID",
                        "Deployment state transitions to READY",
                        "New deployment URL is accessible"
                    ],
                    "failure_risks": [
                        "Invalid token: 401 Unauthorized",
                        "Rate limiting: 100 deployments per hour per project",
                        "Build failure: check deployment events for error details"
                    ]
                }
            ],
            "input_output_expectations": {
                "common_inputs": [
                    "Git repository URL or project name",
                    "Environment variables (key-value pairs)",
                    "Custom domain names",
                    "Build command and output directory overrides",
                    "Framework preset selection"
                ],
                "common_outputs": [
                    "Deployment URL (unique per deployment)",
                    "Production URL (custom domain or .vercel.app)",
                    "Build logs and function invocation logs",
                    "Deployment metadata (git SHA, branch, timestamp)"
                ],
                "data_format_notes": [
                    "API responses are JSON",
                    "Timestamps are ISO 8601 or Unix milliseconds",
                    "Deployment IDs are alphanumeric strings (dpl_...)",
                    "Pagination uses 'next' cursor in response headers"
                ]
            },
            "rules_constraints_caveats": [
                "Hobby plan: 1 concurrent build, 100GB bandwidth/month, 10s function timeout",
                "Pro plan: 12 concurrent builds, 1TB bandwidth/month, 60s function timeout",
                "Serverless functions are stateless: use external databases for persistence",
                "Environment variables have a 64KB total size limit per deployment",
                "Custom domains require DNS configuration (CNAME or A record)",
                "Monorepo support requires turbo.json or explicit root directory configuration"
            ],
            "examples": [
                {
                    "title": "Deploy via CLI",
                    "scenario": "Deploy the current directory to Vercel",
                    "example_instruction": "Run 'vercel --prod' in the project root",
                    "expected_result": "Returns a production deployment URL (e.g., https://my-app.vercel.app)"
                },
                {
                    "title": "Set an Environment Variable via API",
                    "scenario": "Add a DATABASE_URL variable for production",
                    "example_instruction": "POST /v10/projects/{projectId}/env with body {key: 'DATABASE_URL', value: '...', target: ['production']}",
                    "expected_result": "Returns the created env variable object with id and encrypted value"
                }
            ],
            "troubleshooting": [
                {
                    "issue": "Build fails with 'Module not found'",
                    "likely_causes": ["Missing dependency in package.json", "Case-sensitive file path on Linux build servers vs local macOS", "Incorrect import path"],
                    "recommended_fix": ["Run 'npm install' locally and verify", "Check file name casing matches import statements exactly", "Review build logs for the specific missing module"]
                },
                {
                    "issue": "Serverless function returns 504 Gateway Timeout",
                    "likely_causes": ["Function exceeds execution time limit", "External API call is slow", "Database connection timeout"],
                    "recommended_fix": ["Optimize function to complete within timeout", "Use connection pooling for database access", "Consider upgrading plan for longer timeout limits"]
                }
            ],
            "implementation_notes": {
                "what_should_appear_on_customer_agents_page": [
                    "Deployment workflow and Git integration setup",
                    "API authentication and token management",
                    "Environment variable configuration",
                    "Serverless function constraints and best practices",
                    "Common troubleshooting patterns"
                ],
                "missing_info_or_doc_gaps": [
                    "Detailed API rate limits are not published in a single page",
                    "Edge Function compatibility list for npm packages could be more comprehensive"
                ]
            },
            "canonical_references": [
                {"label": "Vercel Documentation", "url": "https://vercel.com/docs", "reason": "Official documentation hub"},
                {"label": "Vercel REST API", "url": "https://vercel.com/docs/rest-api", "reason": "Complete API reference for programmatic access"},
                {"label": "Next.js on Vercel", "url": "https://vercel.com/docs/frameworks/nextjs", "reason": "Framework-specific deployment guide"},
                {"label": "Vercel CLI Reference", "url": "https://vercel.com/docs/cli", "reason": "CLI commands and configuration options"}
            ]
        },
    },
    {
        "product_name": "Notion",
        "company_slug": "notion",
        "docs_url": "https://developers.notion.com",
        "email": "demo@groundocs.com",
        "content_json": {
            "product_name": "Notion",
            "slug": "notion",
            "mode": "full",
            "summary": "Notion is an all-in-one workspace for notes, docs, wikis, databases, and project management. Its API allows programmatic access to create, read, update, and search Notion content.",
            "overview": {
                "what_it_is": "A collaborative workspace platform combining documents, databases, kanban boards, and wikis. The Notion API exposes CRUD operations on pages, databases, blocks, users, and comments.",
                "what_agents_can_do": [
                    "Create new pages and database entries",
                    "Query databases with filters and sorts",
                    "Update page properties and content blocks",
                    "Search across the workspace by title or content",
                    "Retrieve user information and workspace members",
                    "Add comments to pages and discussions",
                    "Append content blocks to existing pages"
                ],
                "best_for": [
                    "Knowledge base and documentation management",
                    "CRM and project tracking via databases",
                    "Automated content creation and updates",
                    "Cross-tool integrations (Slack, GitHub, Zapier)",
                    "Meeting notes and task management automation"
                ]
            },
            "when_to_use": {
                "ideal_use_cases": [
                    "Programmatically creating structured content in a team wiki",
                    "Syncing external data into Notion databases",
                    "Building dashboards that pull from Notion as a data source",
                    "Automating repetitive content updates",
                    "Search and retrieval of organizational knowledge"
                ],
                "non_ideal_use_cases": [
                    "High-frequency real-time data (API rate limits apply)",
                    "Large file storage (Notion is not a file system)",
                    "Complex relational database queries (limited join/aggregation support)",
                    "Public-facing websites with heavy traffic (use a proper CMS)"
                ]
            },
            "getting_started": {
                "prerequisites": [
                    "A Notion account with a workspace",
                    "An internal integration created at notion.so/my-integrations",
                    "Pages or databases shared with the integration"
                ],
                "required_accounts_or_access": [
                    "Notion workspace admin or member role",
                    "Integration token (secret_...)",
                    "Explicit page/database sharing with the integration (click Share > Invite)"
                ],
                "setup_steps": [
                    "Create an integration at notion.so/my-integrations",
                    "Copy the integration token (starts with secret_)",
                    "Share target pages/databases with the integration via the Share menu",
                    "Make API calls with Authorization: Bearer secret_... and Notion-Version header",
                    "Start with GET /v1/users/me to verify authentication"
                ]
            },
            "authentication_access": {
                "auth_methods": [
                    "Internal integration token (secret_...) for private workspace access",
                    "Public OAuth integration for third-party apps (OAuth 2.0 flow)",
                    "Notion-Version header required on all requests (e.g., 2022-06-28)"
                ],
                "permissions": [
                    "Integrations can only access pages/databases explicitly shared with them",
                    "Capabilities configured at integration creation: read content, update content, insert content",
                    "OAuth scopes limit access for public integrations"
                ],
                "important_auth_notes": [
                    "Pages must be manually shared with the integration before API access works",
                    "Child pages inherit sharing from parent pages",
                    "The Notion-Version header controls API behavior and response format",
                    "Rate limit: 3 requests/second per integration"
                ]
            },
            "core_capabilities": [
                {
                    "name": "Database Queries",
                    "description": "Query a Notion database with filters, sorts, and pagination. Returns matching pages with their properties.",
                    "requirements": ["Database shared with integration", "Database ID"],
                    "limitations": ["100 results per page (pagination required)", "Filter complexity has limits", "Rollup and formula properties are read-only"]
                },
                {
                    "name": "Page & Block Management",
                    "description": "Create pages, append blocks (paragraphs, headings, lists, code, etc.), and update existing content.",
                    "requirements": ["Parent page or database ID", "Content formatted as block objects"],
                    "limitations": ["Cannot modify block content after creation (must delete and recreate)", "Max 100 blocks per append request", "Some block types are not yet supported via API"]
                },
                {
                    "name": "Search",
                    "description": "Full-text search across page titles and database titles in the workspace.",
                    "requirements": ["Integration token with read access"],
                    "limitations": ["Searches titles only, not page body content", "Results limited to pages shared with the integration", "No advanced query syntax"]
                },
                {
                    "name": "Comments",
                    "description": "Add and retrieve comments on pages and discussions.",
                    "requirements": ["Page shared with integration", "Comment capability enabled"],
                    "limitations": ["Cannot edit or delete comments via API", "Comments are append-only"]
                }
            ],
            "recommended_workflows": [
                {
                    "name": "Sync External Data into a Notion Database",
                    "goal": "Keep a Notion database in sync with an external data source",
                    "steps": [
                        "Query the Notion database to get existing entries",
                        "Fetch data from the external source",
                        "Compare records by a unique key property",
                        "Create new pages for records that don't exist in Notion",
                        "Update properties of existing pages that have changed",
                        "Optionally archive pages for records removed from the source"
                    ],
                    "success_checks": [
                        "Database entry count matches source count",
                        "Properties are up-to-date with latest source data",
                        "No duplicate entries exist"
                    ],
                    "failure_risks": [
                        "Rate limiting (3 req/s): implement exponential backoff",
                        "Page not shared with integration: sync silently skips items",
                        "Property type mismatch: ensure source data matches Notion property types"
                    ]
                },
                {
                    "name": "Create a Formatted Report Page",
                    "goal": "Programmatically generate a report page with structured content",
                    "steps": [
                        "Create a new page under a parent page or database",
                        "Append heading blocks for each report section",
                        "Append paragraph, list, and table blocks with data",
                        "Add a callout block for key findings or alerts",
                        "Share the page URL with stakeholders"
                    ],
                    "success_checks": [
                        "Page is created and visible in the workspace",
                        "All content blocks render correctly in Notion",
                        "Links and formatting are preserved"
                    ],
                    "failure_risks": [
                        "Block limit exceeded (100 per request): batch appends",
                        "Unsupported block types silently ignored",
                        "Rich text formatting requires correct annotation objects"
                    ]
                }
            ],
            "input_output_expectations": {
                "common_inputs": [
                    "page_id or database_id (32-char hex string, with or without hyphens)",
                    "Block objects (type, content, children)",
                    "Property values (title, rich_text, number, select, date, etc.)",
                    "Filter objects for database queries"
                ],
                "common_outputs": [
                    "Page objects with id, properties, parent, and URL",
                    "Block objects with id, type, content, and children flag",
                    "Database objects with id, title, and property schema",
                    "Paginated results with has_more flag and next_cursor"
                ],
                "data_format_notes": [
                    "IDs are UUIDs (32 hex chars, hyphens optional in requests)",
                    "Rich text is an array of text objects with annotations",
                    "Dates use ISO 8601 format",
                    "All endpoints require Notion-Version header"
                ]
            },
            "rules_constraints_caveats": [
                "Rate limit: 3 requests per second per integration token",
                "Integrations can only access content explicitly shared with them",
                "Block content cannot be edited after creation (delete + recreate pattern)",
                "Maximum 100 blocks per PATCH /blocks/{id}/children request",
                "Search only indexes page and database titles, not body content",
                "File and media blocks use temporary S3 URLs that expire after 1 hour"
            ],
            "examples": [
                {
                    "title": "Query a Database",
                    "scenario": "Get all tasks with status 'In Progress' sorted by due date",
                    "example_instruction": "POST /v1/databases/{db_id}/query with filter: {property: 'Status', select: {equals: 'In Progress'}}, sorts: [{property: 'Due Date', direction: 'ascending'}]",
                    "expected_result": "Returns paginated list of page objects matching the filter, each with full properties"
                },
                {
                    "title": "Create a Page with Content",
                    "scenario": "Add a meeting notes page to a database",
                    "example_instruction": "POST /v1/pages with parent: {database_id: '...'}, properties: {Name: {title: [{text: {content: 'Q1 Review'}}]}}, children: [heading_2, paragraph blocks]",
                    "expected_result": "Returns the created page object with id and URL"
                }
            ],
            "troubleshooting": [
                {
                    "issue": "API returns 404 for a page/database that exists",
                    "likely_causes": ["Page not shared with the integration", "Using workspace URL ID instead of API ID", "Integration lacks required capabilities"],
                    "recommended_fix": ["Open the page in Notion > Share > Invite the integration", "Use the 32-char ID from the URL (remove hyphens or keep them)", "Check integration capabilities in notion.so/my-integrations"]
                },
                {
                    "issue": "Rate limit errors (429 Too Many Requests)",
                    "likely_causes": ["Exceeding 3 requests/second", "Batch operations without throttling"],
                    "recommended_fix": ["Implement exponential backoff with jitter", "Batch operations and add delays between requests", "Use pagination cursors instead of re-fetching entire databases"]
                }
            ],
            "implementation_notes": {
                "what_should_appear_on_customer_agents_page": [
                    "Integration setup and sharing requirements",
                    "Database query patterns with filters",
                    "Page creation and block manipulation",
                    "Rate limiting and backoff strategies",
                    "Common gotchas (sharing, block editing, search limitations)"
                ],
                "missing_info_or_doc_gaps": [
                    "Notion API does not clearly document all supported block types in one place",
                    "OAuth flow documentation could include more error handling examples"
                ]
            },
            "canonical_references": [
                {"label": "Notion API Reference", "url": "https://developers.notion.com/reference", "reason": "Complete endpoint documentation"},
                {"label": "Notion API Getting Started", "url": "https://developers.notion.com/docs/getting-started", "reason": "Integration setup guide"},
                {"label": "Working with Databases", "url": "https://developers.notion.com/docs/working-with-databases", "reason": "Database query and filter patterns"},
                {"label": "Block Types Reference", "url": "https://developers.notion.com/reference/block", "reason": "Supported block types and their schemas"}
            ]
        },
    },
    {
        "product_name": "Slack",
        "company_slug": "slack",
        "docs_url": "https://api.slack.com/docs",
        "email": "demo@groundocs.com",
        "content_json": {
            "product_name": "Slack",
            "slug": "slack",
            "mode": "full",
            "summary": "Slack is a business communication platform with APIs for sending messages, managing channels, building interactive bots, and integrating workflows across teams and tools.",
            "overview": {
                "what_it_is": "A messaging platform for teams with channels, direct messages, threads, and file sharing. The Slack API provides Web API methods, Events API for real-time events, and Block Kit for rich interactive messages.",
                "what_agents_can_do": [
                    "Send messages to channels, DMs, and threads",
                    "Create, archive, and manage channels",
                    "React to messages and pin important content",
                    "Upload and share files",
                    "Search messages and files across the workspace",
                    "Manage users and user groups",
                    "Build interactive workflows with modals and buttons",
                    "Listen for real-time events via Events API or Socket Mode"
                ],
                "best_for": [
                    "Automated notifications and alerts to team channels",
                    "Interactive bots for help desk, on-call, or DevOps",
                    "Workflow automation triggered by Slack events",
                    "Cross-tool integrations (GitHub, Jira, PagerDuty, etc.)",
                    "Team communication analytics and reporting"
                ]
            },
            "when_to_use": {
                "ideal_use_cases": [
                    "Sending automated notifications (deploy alerts, monitoring, CI/CD)",
                    "Building conversational bots with interactive buttons and modals",
                    "Creating custom Slack workflows for team processes",
                    "Integrating external tools with Slack channels",
                    "Searching and retrieving conversation history"
                ],
                "non_ideal_use_cases": [
                    "High-volume data streaming (use a message queue instead)",
                    "Long-term data storage (Slack has retention policies)",
                    "Customer-facing chat (use a dedicated support tool)",
                    "Real-time audio/video manipulation (Slack Huddles are not API-accessible)"
                ]
            },
            "getting_started": {
                "prerequisites": [
                    "A Slack workspace where you have permission to install apps",
                    "A Slack App created at api.slack.com/apps",
                    "Bot token scopes configured for your use case"
                ],
                "required_accounts_or_access": [
                    "Slack workspace admin approval (for app installation)",
                    "Bot User OAuth Token (xoxb-...)",
                    "App-level token (xapp-...) for Socket Mode (optional)"
                ],
                "setup_steps": [
                    "Create a new app at api.slack.com/apps (from scratch or manifest)",
                    "Configure OAuth scopes under OAuth & Permissions (e.g., chat:write, channels:read)",
                    "Install the app to your workspace and copy the Bot User OAuth Token",
                    "Invite the bot to target channels (/invite @botname)",
                    "Test with a simple chat.postMessage API call"
                ]
            },
            "authentication_access": {
                "auth_methods": [
                    "Bot User OAuth Token (xoxb-...) for bot actions",
                    "User OAuth Token (xoxp-...) for user-scoped actions",
                    "App-Level Token (xapp-...) for Socket Mode and org-wide events",
                    "Incoming Webhooks for simple message posting (no token needed)"
                ],
                "permissions": [
                    "Scopes are granular: chat:write, channels:read, users:read, files:write, etc.",
                    "Bot tokens can only access channels the bot is a member of",
                    "User tokens act on behalf of the installing user",
                    "Admin scopes require workspace admin approval"
                ],
                "important_auth_notes": [
                    "The bot must be invited to a channel before it can post or read messages",
                    "Token rotation: Slack supports automatic token rotation for enhanced security",
                    "Rate limits vary by method (see Slack API rate limit tiers)",
                    "Signing secrets verify that incoming requests are from Slack (for Events API)"
                ]
            },
            "core_capabilities": [
                {
                    "name": "Web API (chat.postMessage, etc.)",
                    "description": "Over 200 HTTP methods for reading and writing Slack data: messages, channels, users, files, reactions, pins, and more.",
                    "requirements": ["Bot or user OAuth token", "Appropriate scopes for each method"],
                    "limitations": ["Rate limits per method (Tier 1-4, from 1/min to 100+/min)", "Message text limit: 40,000 characters", "File upload limit: 1GB"]
                },
                {
                    "name": "Events API",
                    "description": "Subscribe to workspace events (messages, reactions, channel changes) delivered to your HTTP endpoint in real-time.",
                    "requirements": ["Public HTTPS endpoint or Socket Mode", "Event subscriptions configured in app settings"],
                    "limitations": ["Must respond to URL verification challenge", "Must respond within 3 seconds (acknowledge quickly, process async)", "Duplicate events may be delivered"]
                },
                {
                    "name": "Block Kit",
                    "description": "Rich message layouts with sections, buttons, select menus, date pickers, modals, and interactive components.",
                    "requirements": ["blocks parameter in message payload", "Interactivity URL configured for interactive components"],
                    "limitations": ["Max 50 blocks per message", "Some elements only available in modals vs messages", "File blocks and video blocks have specific formatting requirements"]
                },
                {
                    "name": "Socket Mode",
                    "description": "WebSocket-based connection for receiving events without a public HTTP endpoint. Ideal for development and internal tools.",
                    "requirements": ["App-level token (xapp-...)", "Socket Mode enabled in app settings"],
                    "limitations": ["Not recommended for high-volume production apps", "Requires persistent WebSocket connection", "Limited to apps that don't need public distribution"]
                }
            ],
            "recommended_workflows": [
                {
                    "name": "Send an Automated Alert",
                    "goal": "Post a formatted notification to a Slack channel",
                    "steps": [
                        "Obtain the channel ID (use conversations.list to find it by name)",
                        "Ensure the bot is a member of the channel",
                        "Call chat.postMessage with channel, text (fallback), and blocks (rich layout)",
                        "Handle the response to confirm delivery (check 'ok' field)",
                        "Optionally thread replies using thread_ts from the response"
                    ],
                    "success_checks": [
                        "API response has ok: true",
                        "Message appears in the target channel",
                        "Block Kit renders correctly (test in Block Kit Builder)"
                    ],
                    "failure_risks": [
                        "channel_not_found: bot not in channel or wrong channel ID",
                        "not_authed: invalid or expired token",
                        "rate_limited: back off using Retry-After header"
                    ]
                },
                {
                    "name": "Build an Interactive Bot",
                    "goal": "Create a bot that responds to messages and button clicks",
                    "steps": [
                        "Subscribe to message.im and message.channels events",
                        "Set up an HTTP endpoint or Socket Mode to receive events",
                        "Parse incoming events and route by type (message, block_action, view_submission)",
                        "Respond with chat.postMessage or open a modal with views.open",
                        "Handle interactive component callbacks at your Interactivity URL"
                    ],
                    "success_checks": [
                        "Bot receives and responds to direct messages",
                        "Interactive buttons trigger expected actions",
                        "Modal submissions are processed correctly"
                    ],
                    "failure_risks": [
                        "Event acknowledgment timeout (must respond within 3 seconds)",
                        "Duplicate event processing: use event_id for deduplication",
                        "Missing scopes: bot cannot perform actions without correct permissions"
                    ]
                }
            ],
            "input_output_expectations": {
                "common_inputs": [
                    "channel (channel ID, e.g., C0123456789)",
                    "text (plain text fallback for notifications)",
                    "blocks (array of Block Kit layout blocks)",
                    "thread_ts (timestamp of parent message for threading)",
                    "user (user ID for DMs and user-specific actions)"
                ],
                "common_outputs": [
                    "ok: true/false indicating success",
                    "ts: message timestamp (unique identifier for the message)",
                    "channel: channel ID where message was posted",
                    "error: error code string when ok is false",
                    "response_metadata: pagination cursors and warnings"
                ],
                "data_format_notes": [
                    "Message timestamps (ts) are unique string identifiers, not parseable times",
                    "Channel and user IDs are alphanumeric strings starting with C/U/D/G",
                    "Pagination uses cursor-based approach with next_cursor",
                    "All API methods accept application/x-www-form-urlencoded or application/json"
                ]
            },
            "rules_constraints_caveats": [
                "Rate limits are per-method and per-workspace (Tier 1: ~1/min, Tier 4: ~100/min)",
                "The bot must be explicitly invited to channels to read/write messages",
                "Events API requires 200 OK response within 3 seconds (process async)",
                "Message history retention depends on workspace plan (free: 90 days)",
                "File uploads count against workspace storage limits",
                "Unfurling URLs requires links:write scope and unfurl domain configuration"
            ],
            "examples": [
                {
                    "title": "Post a Message with Block Kit",
                    "scenario": "Send a deploy notification with a button to view logs",
                    "example_instruction": "POST chat.postMessage with channel, text: 'Deploy succeeded', blocks: [{type: 'section', text: {...}}, {type: 'actions', elements: [{type: 'button', text: 'View Logs', url: '...'}]}]",
                    "expected_result": "Returns ok: true with ts and channel. Message appears with formatted blocks and clickable button."
                },
                {
                    "title": "Search Messages",
                    "scenario": "Find all messages mentioning 'outage' in the last week",
                    "example_instruction": "GET search.messages with query: 'outage after:2024-01-01', sort: 'timestamp', sort_dir: 'desc'",
                    "expected_result": "Returns paginated list of matching messages with channel context and permalink"
                }
            ],
            "troubleshooting": [
                {
                    "issue": "Bot cannot post to a channel",
                    "likely_causes": ["Bot not invited to the channel", "Missing chat:write scope", "Using channel name instead of channel ID"],
                    "recommended_fix": ["Invite the bot: /invite @botname in the channel", "Add chat:write scope and reinstall the app", "Use conversations.list to resolve channel name to ID"]
                },
                {
                    "issue": "Events not being received",
                    "likely_causes": ["URL verification failed", "Event subscription not configured", "Endpoint not responding within 3 seconds"],
                    "recommended_fix": ["Ensure endpoint handles the url_verification challenge event", "Check Event Subscriptions in app settings", "Acknowledge events immediately, process asynchronously"]
                }
            ],
            "implementation_notes": {
                "what_should_appear_on_customer_agents_page": [
                    "App creation and OAuth scope configuration",
                    "Message posting with Block Kit formatting",
                    "Event handling patterns (Events API and Socket Mode)",
                    "Rate limit tiers and backoff strategies",
                    "Channel membership requirements"
                ],
                "missing_info_or_doc_gaps": [
                    "Rate limit tiers per method are not aggregated in a single reference page",
                    "Socket Mode reconnection and error handling best practices could be more detailed"
                ]
            },
            "canonical_references": [
                {"label": "Slack Web API Methods", "url": "https://api.slack.com/methods", "reason": "Complete list of all API methods with parameters and examples"},
                {"label": "Block Kit Builder", "url": "https://app.slack.com/block-kit-builder", "reason": "Visual tool for designing Block Kit layouts"},
                {"label": "Events API Guide", "url": "https://api.slack.com/events-api", "reason": "Setup and usage of real-time event subscriptions"},
                {"label": "Slack App Manifest", "url": "https://api.slack.com/reference/manifests", "reason": "YAML/JSON app configuration for reproducible setup"}
            ]
        },
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
