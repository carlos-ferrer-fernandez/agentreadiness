"""
Seed Example Documentation Packages

Pre-built multi-page packages for Stripe, Vercel, Notion, and Slack.
Each includes 3 preview pages (overview, agents, getting-started) plus a full page map.
The agents page content is pulled from seed_examples.py.
"""

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import DocPackage
from services.seed_examples import STRIPE_EXAMPLE, VERCEL_EXAMPLE, NOTION_EXAMPLE, SLACK_EXAMPLE
from services.agent_page_generator import render_agent_page_html
from services.package_renderer import render_package_page

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Page maps
# ---------------------------------------------------------------------------

STRIPE_PAGE_MAP = [
    {"page_type": "overview", "title": "Overview", "slug": "overview", "tier": "preview"},
    {"page_type": "agents", "title": "Agent Operating Guide", "slug": "agents", "tier": "preview"},
    {"page_type": "getting-started", "title": "Getting Started", "slug": "getting-started", "tier": "preview"},
    {"page_type": "authentication", "title": "Authentication", "slug": "authentication", "tier": "full"},
    {"page_type": "core-concepts", "title": "Core Concepts", "slug": "core-concepts", "tier": "full"},
    {"page_type": "workflow", "title": "Accept a Payment", "slug": "workflow-accept-payment", "tier": "full"},
    {"page_type": "workflow", "title": "Manage Subscriptions", "slug": "workflow-subscriptions", "tier": "full"},
    {"page_type": "workflow", "title": "Issue Refunds", "slug": "workflow-refunds", "tier": "full"},
    {"page_type": "rules", "title": "Rules & Constraints", "slug": "rules", "tier": "full"},
    {"page_type": "troubleshooting", "title": "Troubleshooting", "slug": "troubleshooting", "tier": "full"},
    {"page_type": "faq", "title": "FAQ", "slug": "faq", "tier": "full"},
    {"page_type": "resources", "title": "Resources", "slug": "resources", "tier": "full"},
]

VERCEL_PAGE_MAP = [
    {"page_type": "overview", "title": "Overview", "slug": "overview", "tier": "preview"},
    {"page_type": "agents", "title": "Agent Operating Guide", "slug": "agents", "tier": "preview"},
    {"page_type": "getting-started", "title": "Getting Started", "slug": "getting-started", "tier": "preview"},
    {"page_type": "authentication", "title": "Authentication", "slug": "authentication", "tier": "full"},
    {"page_type": "workflow", "title": "Deploy a Project", "slug": "workflow-deploy", "tier": "full"},
    {"page_type": "workflow", "title": "Manage Domains", "slug": "workflow-domains", "tier": "full"},
    {"page_type": "workflow", "title": "Configure Environment Variables", "slug": "workflow-env-vars", "tier": "full"},
    {"page_type": "rules", "title": "Rules & Constraints", "slug": "rules", "tier": "full"},
    {"page_type": "troubleshooting", "title": "Troubleshooting", "slug": "troubleshooting", "tier": "full"},
    {"page_type": "resources", "title": "Resources", "slug": "resources", "tier": "full"},
]

NOTION_PAGE_MAP = [
    {"page_type": "overview", "title": "Overview", "slug": "overview", "tier": "preview"},
    {"page_type": "agents", "title": "Agent Operating Guide", "slug": "agents", "tier": "preview"},
    {"page_type": "getting-started", "title": "Getting Started", "slug": "getting-started", "tier": "preview"},
    {"page_type": "core-concepts", "title": "Core Concepts", "slug": "core-concepts", "tier": "full"},
    {"page_type": "workflow", "title": "Manage Pages & Databases", "slug": "workflow-pages-databases", "tier": "full"},
    {"page_type": "workflow", "title": "Search & Query", "slug": "workflow-search", "tier": "full"},
    {"page_type": "rules", "title": "Rules & Constraints", "slug": "rules", "tier": "full"},
    {"page_type": "troubleshooting", "title": "Troubleshooting", "slug": "troubleshooting", "tier": "full"},
    {"page_type": "resources", "title": "Resources", "slug": "resources", "tier": "full"},
]

SLACK_PAGE_MAP = [
    {"page_type": "overview", "title": "Overview", "slug": "overview", "tier": "preview"},
    {"page_type": "agents", "title": "Agent Operating Guide", "slug": "agents", "tier": "preview"},
    {"page_type": "getting-started", "title": "Getting Started", "slug": "getting-started", "tier": "preview"},
    {"page_type": "authentication", "title": "Authentication", "slug": "authentication", "tier": "full"},
    {"page_type": "workflow", "title": "Send Messages", "slug": "workflow-send-messages", "tier": "full"},
    {"page_type": "workflow", "title": "Manage Channels", "slug": "workflow-channels", "tier": "full"},
    {"page_type": "rules", "title": "Rules & Constraints", "slug": "rules", "tier": "full"},
    {"page_type": "troubleshooting", "title": "Troubleshooting", "slug": "troubleshooting", "tier": "full"},
    {"page_type": "resources", "title": "Resources", "slug": "resources", "tier": "full"},
]


# ---------------------------------------------------------------------------
# Overview page content
# ---------------------------------------------------------------------------

STRIPE_OVERVIEW = {
    "product_name": "Stripe",
    "tagline": "Payment processing platform for internet businesses — charges, subscriptions, payouts, and financial infrastructure.",
    "what_it_does": [
        "Process one-time and recurring payments",
        "Manage customers, invoices, and subscriptions",
        "Handle refunds and disputes",
        "Accept 135+ currencies worldwide",
        "Detect and prevent fraud with Radar",
    ],
    "key_concepts": [
        {"term": "PaymentIntent", "definition": "Represents a payment lifecycle from creation to confirmation"},
        {"term": "Customer", "definition": "Stores payment methods and billing info for repeat use"},
        {"term": "Subscription", "definition": "Recurring billing tied to a Price and Customer"},
        {"term": "Webhook", "definition": "Server-to-server event notification for async state changes"},
        {"term": "Idempotency Key", "definition": "Prevents duplicate operations on retries"},
    ],
    "capabilities": [
        {"name": "Payments", "description": "One-time charges via PaymentIntents or Checkout Sessions"},
        {"name": "Subscriptions", "description": "Recurring billing with trials, proration, and metering"},
        {"name": "Invoicing", "description": "Generate and send invoices with line items"},
        {"name": "Connect", "description": "Multi-party payments and marketplace payouts"},
        {"name": "Radar", "description": "Machine learning fraud detection"},
    ],
    "integrations": ["React", "Node.js", "Python", "Ruby", "Go", "Java", ".NET", "iOS", "Android"],
    "when_to_use": [
        "Building an e-commerce checkout flow",
        "Setting up recurring SaaS billing",
        "Processing marketplace payments",
        "Generating invoices for B2B customers",
    ],
    "when_not_to_use": [
        "Crypto or high-risk industries (restricted by Stripe)",
        "Countries not in Stripe's supported list",
    ],
    "links": [
        {"label": "API Reference", "url": "https://docs.stripe.com/api"},
        {"label": "Stripe Dashboard", "url": "https://dashboard.stripe.com"},
        {"label": "Testing Guide", "url": "https://docs.stripe.com/testing"},
    ],
}

VERCEL_OVERVIEW = {
    "product_name": "Vercel",
    "tagline": "Frontend cloud platform for deploying web applications with zero-config CI/CD and edge infrastructure.",
    "what_it_does": [
        "Deploy frontend apps from Git push",
        "Preview deployments per pull request",
        "Edge functions and serverless compute",
        "Custom domain management with auto-SSL",
        "Environment variable management per branch",
    ],
    "key_concepts": [
        {"term": "Deployment", "definition": "An immutable snapshot of your project at a specific commit"},
        {"term": "Project", "definition": "A Git-connected application with its own settings and domains"},
        {"term": "Preview", "definition": "Auto-deployed version for each branch or PR"},
        {"term": "Edge Function", "definition": "Code running at the CDN edge, low-latency"},
        {"term": "Team", "definition": "Organization-level container for projects and members"},
    ],
    "capabilities": [
        {"name": "Git Integration", "description": "Auto-deploy on push to GitHub, GitLab, or Bitbucket"},
        {"name": "Serverless Functions", "description": "Backend logic co-deployed with your frontend"},
        {"name": "Edge Network", "description": "Global CDN with edge caching and routing"},
        {"name": "Analytics", "description": "Web Vitals and audience insights"},
    ],
    "integrations": ["Next.js", "React", "Svelte", "Nuxt", "Astro", "GitHub", "GitLab", "Bitbucket"],
    "when_to_use": [
        "Deploying a Next.js or React application",
        "Need preview deployments for every PR",
        "Want zero-config CI/CD from Git",
    ],
    "when_not_to_use": [
        "Backend-heavy applications needing persistent servers",
        "Applications requiring Docker containers",
    ],
    "links": [
        {"label": "API Reference", "url": "https://vercel.com/docs/rest-api"},
        {"label": "Dashboard", "url": "https://vercel.com/dashboard"},
        {"label": "CLI Docs", "url": "https://vercel.com/docs/cli"},
    ],
}

NOTION_OVERVIEW = {
    "product_name": "Notion",
    "tagline": "All-in-one workspace for notes, docs, databases, and project management with a structured API.",
    "what_it_does": [
        "Create and organize pages and databases",
        "Query databases with filters and sorts",
        "Manage blocks (paragraphs, lists, etc.)",
        "Search across an entire workspace",
        "Share and permission content",
    ],
    "key_concepts": [
        {"term": "Page", "definition": "A document that can contain blocks and child pages"},
        {"term": "Database", "definition": "A structured collection of pages with typed properties"},
        {"term": "Block", "definition": "The atomic content unit — paragraph, heading, to-do, etc."},
        {"term": "Property", "definition": "A typed field on a database entry (text, date, select, etc.)"},
        {"term": "Integration", "definition": "An API connection with specific workspace permissions"},
    ],
    "capabilities": [
        {"name": "Pages API", "description": "Create, read, update, archive pages"},
        {"name": "Databases API", "description": "Query with filters, create entries, update properties"},
        {"name": "Blocks API", "description": "Append, update, delete content blocks within pages"},
        {"name": "Search API", "description": "Full-text search across shared workspace content"},
    ],
    "integrations": ["Slack", "Google Drive", "GitHub", "Jira", "Figma", "Zapier"],
    "when_to_use": [
        "Building automations that read/write workspace content",
        "Syncing external data into Notion databases",
        "Creating dashboards from Notion data",
    ],
    "when_not_to_use": [
        "Real-time collaboration features (API is async)",
        "Bulk data operations on very large databases",
    ],
    "links": [
        {"label": "API Reference", "url": "https://developers.notion.com/reference"},
        {"label": "Getting Started", "url": "https://developers.notion.com/docs/getting-started"},
    ],
}

SLACK_OVERVIEW = {
    "product_name": "Slack",
    "tagline": "Business messaging platform with channels, threads, apps, and workflow automation APIs.",
    "what_it_does": [
        "Send messages to channels and users",
        "Create and manage channels",
        "Build interactive workflows and bots",
        "Search message history",
        "Manage user and team info",
    ],
    "key_concepts": [
        {"term": "Channel", "definition": "A conversation space — public, private, or DM"},
        {"term": "Bot Token", "definition": "OAuth token for app-level API access"},
        {"term": "User Token", "definition": "OAuth token acting on behalf of a specific user"},
        {"term": "Block Kit", "definition": "UI framework for rich, interactive messages"},
        {"term": "Event", "definition": "Real-time notification of workspace activity via Events API"},
    ],
    "capabilities": [
        {"name": "Web API", "description": "RESTful methods for messages, channels, users, files"},
        {"name": "Events API", "description": "Subscribe to workspace events via webhooks"},
        {"name": "Block Kit", "description": "Rich message layouts with buttons, selects, inputs"},
        {"name": "Workflows", "description": "Multi-step automated processes triggered by events"},
    ],
    "integrations": ["Google Workspace", "Salesforce", "Jira", "GitHub", "Zoom", "Notion"],
    "when_to_use": [
        "Automating notifications to team channels",
        "Building interactive bots for team workflows",
        "Integrating external tools with Slack messages",
    ],
    "when_not_to_use": [
        "Consumer messaging (Slack is enterprise-focused)",
        "Storing structured data (use a database instead)",
    ],
    "links": [
        {"label": "API Reference", "url": "https://api.slack.com/methods"},
        {"label": "Block Kit Builder", "url": "https://app.slack.com/block-kit-builder"},
    ],
}


# ---------------------------------------------------------------------------
# Getting Started page content
# ---------------------------------------------------------------------------

STRIPE_GETTING_STARTED = {
    "product_name": "Stripe",
    "prerequisites": [
        "Stripe account (free to create)",
        "Node.js 14+ or Python 3.7+",
        "Test-mode API keys from Dashboard",
    ],
    "install_steps": [
        {"step_number": 1, "instruction": "Install the Stripe SDK", "code_snippet": "npm install stripe\n# or\npip install stripe"},
        {"step_number": 2, "instruction": "Set your secret key", "code_snippet": "export STRIPE_SECRET_KEY=sk_test_..."},
        {"step_number": 3, "instruction": "Initialize the client", "code_snippet": "const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);"},
    ],
    "first_api_call": {
        "description": "Create a PaymentIntent to accept a $10 payment",
        "code_snippet": "const paymentIntent = await stripe.paymentIntents.create({\n  amount: 1000,\n  currency: 'usd',\n  payment_method_types: ['card'],\n});",
        "expected_response": '{"id": "pi_...", "status": "requires_payment_method", "amount": 1000}',
    },
    "auth_setup": {
        "method": "API Key (Bearer token)",
        "steps": ["Get keys from Dashboard > Developers > API keys", "Use sk_test_... for testing", "Use sk_live_... for production (never in client code)"],
    },
    "common_next_steps": [
        {"action": "Add Stripe Elements", "description": "Embed a secure payment form in your frontend"},
        {"action": "Set up webhooks", "description": "Listen for payment_intent.succeeded and other events"},
        {"action": "Create a Customer", "description": "Store payment methods for returning users"},
    ],
    "gotchas": [
        "Amounts are in smallest currency unit (cents for USD)",
        "Always use test mode keys during development",
        "Webhooks need a publicly accessible URL (use Stripe CLI for local dev)",
    ],
}

VERCEL_GETTING_STARTED = {
    "product_name": "Vercel",
    "prerequisites": [
        "Vercel account (free tier available)",
        "Node.js 18+",
        "A Git repository (GitHub, GitLab, or Bitbucket)",
    ],
    "install_steps": [
        {"step_number": 1, "instruction": "Install the Vercel CLI", "code_snippet": "npm install -g vercel"},
        {"step_number": 2, "instruction": "Log in", "code_snippet": "vercel login"},
        {"step_number": 3, "instruction": "Deploy from your project directory", "code_snippet": "vercel"},
    ],
    "first_api_call": {
        "description": "List your projects via the REST API",
        "code_snippet": "curl -H 'Authorization: Bearer YOUR_TOKEN' \\\n  https://api.vercel.com/v9/projects",
        "expected_response": '{"projects": [{"id": "...", "name": "my-app", ...}]}',
    },
    "auth_setup": {
        "method": "Bearer Token",
        "steps": ["Go to Settings > Tokens", "Create a new token with appropriate scope", "Pass as Authorization: Bearer <token> header"],
    },
    "common_next_steps": [
        {"action": "Connect a Git repo", "description": "Auto-deploy on every push"},
        {"action": "Add a custom domain", "description": "Point your domain to your Vercel deployment"},
        {"action": "Set environment variables", "description": "Configure secrets per environment"},
    ],
    "gotchas": [
        "Serverless functions have a 10s default timeout (configurable to 60s on Pro)",
        "Preview deployments are public by default",
        "Environment variables are not shared across projects",
    ],
}

NOTION_GETTING_STARTED = {
    "product_name": "Notion",
    "prerequisites": [
        "Notion account with admin access",
        "An integration created at notion.so/my-integrations",
        "At least one page shared with your integration",
    ],
    "install_steps": [
        {"step_number": 1, "instruction": "Install the Notion SDK", "code_snippet": "npm install @notionhq/client\n# or\npip install notion-client"},
        {"step_number": 2, "instruction": "Set your integration token", "code_snippet": "export NOTION_TOKEN=ntn_..."},
        {"step_number": 3, "instruction": "Initialize the client", "code_snippet": "const { Client } = require('@notionhq/client');\nconst notion = new Client({ auth: process.env.NOTION_TOKEN });"},
    ],
    "first_api_call": {
        "description": "Search for pages shared with your integration",
        "code_snippet": "const response = await notion.search({\n  filter: { property: 'object', value: 'page' }\n});",
        "expected_response": '{"results": [{"object": "page", "id": "...", ...}]}',
    },
    "auth_setup": {
        "method": "Internal Integration Token",
        "steps": ["Create an integration at notion.so/my-integrations", "Copy the Internal Integration Token", "Share target pages/databases with your integration via the Share menu"],
    },
    "common_next_steps": [
        {"action": "Query a database", "description": "Filter and sort entries in a Notion database"},
        {"action": "Create a page", "description": "Add new content programmatically"},
        {"action": "Append blocks", "description": "Add paragraphs, lists, and other content to a page"},
    ],
    "gotchas": [
        "Integration can only access pages explicitly shared with it",
        "Rate limit: 3 requests per second per integration",
        "Page content must be read via the Blocks API, not the Pages API",
    ],
}

SLACK_GETTING_STARTED = {
    "product_name": "Slack",
    "prerequisites": [
        "Slack workspace with admin permissions",
        "A Slack App created at api.slack.com/apps",
        "Bot token with required OAuth scopes",
    ],
    "install_steps": [
        {"step_number": 1, "instruction": "Install the Slack SDK", "code_snippet": "npm install @slack/web-api\n# or\npip install slack_sdk"},
        {"step_number": 2, "instruction": "Set your bot token", "code_snippet": "export SLACK_BOT_TOKEN=xoxb-..."},
        {"step_number": 3, "instruction": "Initialize the client", "code_snippet": "const { WebClient } = require('@slack/web-api');\nconst slack = new WebClient(process.env.SLACK_BOT_TOKEN);"},
    ],
    "first_api_call": {
        "description": "Post a message to a channel",
        "code_snippet": "const result = await slack.chat.postMessage({\n  channel: '#general',\n  text: 'Hello from my bot!'\n});",
        "expected_response": '{"ok": true, "channel": "C...", "ts": "1234567890.123456"}',
    },
    "auth_setup": {
        "method": "OAuth Bot Token",
        "steps": ["Create app at api.slack.com/apps", "Add Bot Token Scopes (e.g. chat:write, channels:read)", "Install to workspace and copy xoxb- token"],
    },
    "common_next_steps": [
        {"action": "Listen for events", "description": "Subscribe to message, reaction, and channel events"},
        {"action": "Use Block Kit", "description": "Build rich interactive messages"},
        {"action": "Add slash commands", "description": "Register custom /commands for your bot"},
    ],
    "gotchas": [
        "Bot must be invited to a channel before it can post",
        "Rate limits vary by method (usually ~1 req/sec for posting)",
        "User tokens (xoxp-) and bot tokens (xoxb-) have different scopes",
    ],
}


# ---------------------------------------------------------------------------
# Package definitions
# ---------------------------------------------------------------------------

SEED_PACKAGES = [
    {
        "product_name": "Stripe",
        "slug": "stripe",
        "docs_url": "https://docs.stripe.com",
        "email": "demo@groundocs.com",
        "page_map": STRIPE_PAGE_MAP,
        "agents_data": STRIPE_EXAMPLE,
        "overview_data": STRIPE_OVERVIEW,
        "getting_started_data": STRIPE_GETTING_STARTED,
    },
    {
        "product_name": "Vercel",
        "slug": "vercel",
        "docs_url": "https://vercel.com/docs",
        "email": "demo@groundocs.com",
        "page_map": VERCEL_PAGE_MAP,
        "agents_data": VERCEL_EXAMPLE,
        "overview_data": VERCEL_OVERVIEW,
        "getting_started_data": VERCEL_GETTING_STARTED,
    },
    {
        "product_name": "Notion",
        "slug": "notion",
        "docs_url": "https://developers.notion.com",
        "email": "demo@groundocs.com",
        "page_map": NOTION_PAGE_MAP,
        "agents_data": NOTION_EXAMPLE,
        "overview_data": NOTION_OVERVIEW,
        "getting_started_data": NOTION_GETTING_STARTED,
    },
    {
        "product_name": "Slack",
        "slug": "slack",
        "docs_url": "https://api.slack.com",
        "email": "demo@groundocs.com",
        "page_map": SLACK_PAGE_MAP,
        "agents_data": SLACK_EXAMPLE,
        "overview_data": SLACK_OVERVIEW,
        "getting_started_data": SLACK_GETTING_STARTED,
    },
]


# ---------------------------------------------------------------------------
# Seed function
# ---------------------------------------------------------------------------

async def seed_example_packages(db: AsyncSession):
    """Create or update seed example packages."""
    for pkg_def in SEED_PACKAGES:
        slug = pkg_def["slug"]
        product_name = pkg_def["product_name"]
        page_map = pkg_def["page_map"]

        result = await db.execute(
            select(DocPackage).where(DocPackage.slug == slug)
        )
        existing = result.scalar_one_or_none()

        # Build preview pages
        preview_pages = {}

        # Overview
        overview_html = render_package_page(
            content_json=pkg_def["overview_data"],
            page_type="overview",
            page_title="Overview",
            product_name=product_name,
            package_slug=slug,
            page_map=page_map,
            current_page_slug="overview",
            is_paid=False,
        )
        preview_pages["overview"] = {
            "title": "Overview",
            "page_type": "overview",
            "html": overview_html,
            "content_json": pkg_def["overview_data"],
        }

        # Agents (reuse existing agent page content)
        agents_html = render_package_page(
            content_json=pkg_def["agents_data"],
            page_type="agents",
            page_title="Agent Operating Guide",
            product_name=product_name,
            package_slug=slug,
            page_map=page_map,
            current_page_slug="agents",
            is_paid=False,
        )
        preview_pages["agents"] = {
            "title": "Agent Operating Guide",
            "page_type": "agents",
            "html": agents_html,
            "content_json": pkg_def["agents_data"],
        }

        # Getting Started
        gs_html = render_package_page(
            content_json=pkg_def["getting_started_data"],
            page_type="getting-started",
            page_title="Getting Started",
            product_name=product_name,
            package_slug=slug,
            page_map=page_map,
            current_page_slug="getting-started",
            is_paid=False,
        )
        preview_pages["getting-started"] = {
            "title": "Getting Started",
            "page_type": "getting-started",
            "html": gs_html,
            "content_json": pkg_def["getting_started_data"],
        }

        if existing:
            existing.page_map_json = page_map
            existing.preview_pages_json = preview_pages
            existing.status = "preview_ready"
            existing.docs_url = pkg_def["docs_url"]
            logger.info(f"Updated seed package: {slug}")
        else:
            package = DocPackage(
                product_name=product_name,
                slug=slug,
                docs_url=pkg_def["docs_url"],
                email=pkg_def["email"],
                status="preview_ready",
                page_map_json=page_map,
                preview_pages_json=preview_pages,
            )
            db.add(package)
            logger.info(f"Created seed package: {slug}")
