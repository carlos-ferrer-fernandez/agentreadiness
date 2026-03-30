export interface BlogPost {
  slug: string
  title: string
  description: string
  keywords: string[]
  date: string
  readingTime: number
  category: string
  content: string
}

export const BLOG_POSTS: BlogPost[] = [
  {
    slug: 'agent-first-documentation-revolution',
    title: 'The Agent-First Documentation Revolution: Why Traditional Docs Are Failing AI',
    description:
      'Discover why traditional documentation is failing AI agents and learn the 20 essential rules for creating agent-first documentation that drives traffic and conversions.',
    keywords: [
      'agent-first documentation',
      'AI documentation',
      'GEO optimization',
      'generative engine optimization',
      'AI-friendly docs',
      'documentation for AI agents',
    ],
    date: 'March 2025',
    readingTime: 7,
    category: 'Strategy',
    content: `## The Documentation Paradigm Shift You Can't Ignore

Something fundamental is changing in how users discover and consume technical documentation. The rise of AI agents—from ChatGPT and Claude to specialized coding assistants—has created a new consumption pattern that most documentation is failing to serve.

Here's the reality: **AI agents are becoming the primary interface between your product and your users.** When a developer asks "How do I authenticate with this API?" they're increasingly asking an AI, not reading your docs directly. When a product manager needs to understand feature limitations, they query their AI assistant first.

This shift demands a new approach to documentation. Welcome to the era of **agent-first documentation**.

## Why Traditional Documentation Is Failing the AI Economy

Traditional documentation was designed for human readers who browse, scan, and navigate through pages. It assumes:

- Readers will explore your information architecture
- Users will click through multiple pages to gather context
- Humans can infer meaning from partial information
- Visual design and navigation aids comprehension

**AI agents work differently.** They retrieve content in chunks, not pages. They can't "browse" your site structure. They have no visual context. And critically—they have zero ability to "figure it out" when information is implicit or fragmented.

### The Retrieval Problem

Modern AI systems use Retrieval-Augmented Generation (RAG) to answer questions. Here's how it works:

1. A user asks an AI: "How do I handle rate limits in the Stripe API?"
2. The AI searches documentation for relevant chunks
3. It retrieves 3-5 text segments based on semantic similarity
4. It synthesizes an answer from those chunks

**The problem?** Most documentation chunks fail this test. They contain phrases like "as mentioned above" or "see the authentication section"—references that make perfect sense to a human reader but are meaningless to an AI retrieving isolated content.

### The Real Cost of Poor AI Documentation

When your documentation fails AI agents, the consequences cascade:

- **Users get wrong answers** → frustration and churn
- **AI assistants recommend competitors** with better-structured docs
- **Your support burden increases** as users can't self-serve
- **Your product appears less mature** in AI-driven discovery

Companies like Resend have recognized this shift. By creating structured, agent-optimized documentation, they've become the default recommendation when users ask AI assistants about email APIs. The documentation itself has become a competitive moat.

## Introducing the 20 Rules of Agent-First Documentation

Based on insights from leading AI systems—including Claude, GPT-4, Kimi, and specialized agent platforms—we've synthesized **20 essential rules** for creating documentation that serves both human readers and AI agents effectively.

These rules are organized into four layers that mirror how AI agents consume and utilize documentation:

### Layer 1: Discoverability
How easily can AI find the right information?

- **Rule #2: Action-Oriented Headings** — Headings should match what people ask AI: "How to register for a race," not "Registration"
- **Rule #8: Page Metadata** — Structured metadata on every page: title, description, tags, category
- **Rule #17: Retrieval-Optimized** — Sections scoped so AI can retrieve them independently with full context

### Layer 2: Answerability
Once found, does the content actually answer the question?

- **Rule #1: Self-Contained Sections** — Every section must make sense on its own. No "see above" or "as mentioned earlier"
- **Rule #4: Complete Examples** — Every example includes full context: setup, the action, and what to expect
- **Rule #5: Explicit Over Implicit** — State all details explicitly. AI agents have zero ability to "figure it out"
- **Rule #11: Contextual Cross-References** — Never "click here." Always describe what the linked page covers
- **Rule #18: Intent Before Mechanics** — Always explain WHY before HOW. Context before instructions

### Layer 3: Operability
Can the agent turn the answer into action?

- **Rule #3: Structured Data Tables** — Options, features, and specs in tables (name, type, description), not buried in paragraphs
- **Rule #9: Prerequisites Up Front** — State all requirements at the top: accounts, permissions, plans, setup steps
- **Rule #10: Expected Outcomes** — Show what success looks like: expected results, confirmations, next steps
- **Rule #12: Content Type Separation** — Separate explanations, step-by-step guides, and reference content clearly
- **Rule #14: Comparison Sections** — "When to use X vs Y" sections so agents can answer comparison questions
- **Rule #19: Lifecycle & Status** — Document processes as flows: pending, active, completed, cancelled

### Layer 4: Trustability
Can the agent verify and trust the information?

- **Rule #6: First-Class Error Docs** — Every error or issue documented with causes, steps to diagnose, and fixes
- **Rule #7: Consistent Terminology** — One term per concept everywhere. No alternating between synonyms
- **Rule #13: Version Clarity** — Version or date stated prominently. Outdated content marked with alternatives
- **Rule #15: Safety & Limits** — Irreversible actions, billing implications, and limits clearly documented
- **Rule #16: No Anti-Patterns** — Strip marketing fluff, "contact us" dead-ends, and content hidden behind JS widgets
- **Rule #20: Callouts & Warnings** — Standard callout format for warnings, tips, and important notes that AI can prioritize

## SEO vs. GEO: Optimizing for Two Kinds of Search

As you implement these rules, you're simultaneously optimizing for two discovery mechanisms:

**SEO (Search Engine Optimization)** ensures humans can find your documentation through traditional search. It focuses on:
- Keyword-rich titles and headings
- Backlinks and domain authority
- Page load speed and mobile responsiveness
- Structured data markup

**GEO (Generative Engine Optimization)** ensures AI agents can find, understand, and accurately represent your documentation. It focuses on:
- Semantic clarity and explicit context
- Self-contained, retrievable content chunks
- Structured data that machines can parse
- Consistent terminology and comprehensive coverage

The 20 rules address both. Action-oriented headings help humans scan and AI retrieve. Self-contained sections serve fragmented readers and RAG systems. Structured tables help both human comprehension and machine parsing.

## The Business Case for Agent-First Documentation

Investing in agent-first documentation isn't just about keeping up with technology trends—it delivers measurable business outcomes:

### Reduced Support Costs
When AI agents can accurately answer user questions from your documentation, support ticket volume drops. Users self-serve through their preferred interface (AI assistants) rather than opening tickets.

### Increased Product Adoption
Clear, actionable documentation reduces friction in the user journey. When AI assistants can confidently guide users through setup and common tasks, more users reach activation.

### Competitive Differentiation
In AI-driven product discovery, documentation quality directly influences recommendations. Products with well-structured, agent-friendly docs are more likely to be suggested by AI assistants.

### Future-Proofing
The trend toward AI-mediated interaction is accelerating. Documentation optimized for agents today will serve an increasing share of your user base tomorrow.

## Getting Started: Your 30-Day Implementation Roadmap

Transforming your documentation doesn't require a complete rewrite. Here's a pragmatic approach:

**Week 1: Audit**
- Review your top 10 most-visited documentation pages
- Identify violations of the 20 rules
- Prioritize fixes based on user impact

**Week 2: Quick Wins**
- Add page metadata (Rule #8)
- Fix "see above" references (Rule #1)
- Convert parameter descriptions to tables (Rule #3)

**Week 3: Content Improvements**
- Rewrite headings to be action-oriented (Rule #2)
- Add prerequisites to task pages (Rule #9)
- Document common errors (Rule #6)

**Week 4: Structural Changes**
- Implement consistent terminology (Rule #7)
- Add version indicators (Rule #13)
- Create comparison sections for key decisions (Rule #14)

## The Future Is Agent-First

The documentation landscape is undergoing its most significant shift since the move from printed manuals to web-based help. AI agents aren't just a new consumption channel—they're becoming the primary channel for technical information discovery.

Companies that recognize this shift and invest in agent-first documentation will capture disproportionate value. Those that don't will find their products increasingly invisible in an AI-mediated world.

The 20 rules provide a concrete framework for this transformation. They distill insights from the AI systems themselves about what makes documentation truly usable for automated consumption.

In the following articles, we'll dive deep into each layer of the framework, providing practical guidance and before/after examples for implementing these rules in your own documentation.`,
  },
  {
    slug: 'documentation-discoverability-framework',
    title: 'How to Structure Documentation for AI Discovery: The Discoverability Framework',
    description:
      'Master the discoverability layer of agent-first documentation. Learn how action-oriented headings, metadata, and retrieval-optimized sections help AI find your content.',
    keywords: [
      'documentation discoverability',
      'AI search optimization',
      'action-oriented headings',
      'documentation metadata',
      'RAG optimization',
      'retrieval-augmented generation',
    ],
    date: 'March 2025',
    readingTime: 8,
    category: 'Discoverability',
    content: `## The Discovery Problem in AI-First Documentation

Here's a scenario playing out millions of times daily: A developer types into ChatGPT, "How do I implement OAuth2 authentication for the GitHub API?" The AI retrieves chunks from GitHub's documentation, synthesizes an answer, and presents it to the user.

But what if GitHub's documentation uses the heading "Authorization Workflows" instead of "How to authenticate with OAuth2"? What if the relevant section lacks metadata describing its contents? What if the section depends on context from three other pages to make sense?

**The AI might retrieve the wrong content. Or fail to retrieve it at all.**

This is the discoverability problem. Before an AI can answer a user's question, it must first find the right information. And AI systems find information differently than humans do.

## Understanding How AI Discovers Documentation

To optimize for AI discovery, you need to understand how modern retrieval systems work:

### Semantic Search vs. Keyword Search

Traditional search engines rely heavily on keyword matching. AI retrieval uses semantic search—finding content based on meaning, not just word overlap.

When a user asks "How do I send emails with your API?" a semantic search system understands this is equivalent to "Email sending methods," "SMTP integration," or "Message dispatch endpoints." It retrieves based on conceptual similarity, not literal keyword presence.

### The Chunking Problem

AI systems don't read entire documentation pages. They break content into chunks—typically 200-500 tokens—and index those chunks for retrieval.

**This creates a critical constraint:** Each chunk must be discoverable and understandable in isolation. A chunk that starts with "As described above..." is undiscoverable because the AI has no access to what came before.

### The Heading Hierarchy

AI systems use document structure to understand content organization. Headings (H1, H2, H3) serve as semantic signposts, helping the AI:
- Understand what a section covers
- Determine relevance to a query
- Navigate to specific information

## The Three Pillars of Documentation Discoverability

The discoverability layer of agent-first documentation rests on three foundational rules:

1. **Action-Oriented Headings (Rule #2)** — Match how users actually ask questions
2. **Page Metadata (Rule #8)** — Provide structured context for every page
3. **Retrieval-Optimized Sections (Rule #17)** — Design sections to stand alone

Let's explore each in depth.

---

## Rule #2: Action-Oriented Headings

### The Principle

Headings should match what people actually ask AI assistants. Instead of topic labels like "Authentication" or "Rate Limiting," use action-oriented phrases like "How to authenticate with an API key" or "How to handle rate limit errors."

### Why This Matters for AI Discovery

When users ask AI assistants questions, they phrase them as tasks:
- "How do I send an email with attachments?"
- "What's the best way to paginate through results?"
- "How do I handle webhook verification?"

If your headings mirror these question patterns, semantic search systems will retrieve your content with higher confidence. The semantic similarity between a user's query and your heading directly impacts retrieval accuracy.

### Before and After Examples

**Poor (Topic-Based):**
\`\`\`
# Authentication
## API Keys
## OAuth
## JWT Tokens
\`\`\`

**Better (Action-Oriented):**
\`\`\`
# How to authenticate with the API
## How to authenticate using API keys
## How to set up OAuth 2.0 authentication
## How to verify JWT tokens
\`\`\`

**Poor:**
\`\`\`
# Webhooks
## Configuration
## Security
\`\`\`

**Better:**
\`\`\`
# How to receive real-time events with webhooks
## How to configure webhook endpoints
## How to verify webhook signatures for security
\`\`\`

### Implementation Guidelines

1. **Start with verbs:** "How to," "Setting up," "Configuring," "Implementing"
2. **Include the full context:** "How to authenticate" → "How to authenticate with OAuth 2.0"
3. **Match user vocabulary:** Use the terms your users actually use, not internal jargon
4. **Be specific:** "How to handle errors" → "How to handle 429 rate limit errors"

### SEO Benefits

Action-oriented headings also improve traditional SEO:
- They match long-tail search queries ("how to authenticate github api")
- They increase click-through rates from search results
- They improve dwell time by immediately signaling relevance

---

## Rule #8: Page Metadata

### The Principle

Every documentation page should include structured metadata: title, description, tags, category, version, and last-updated date. This metadata helps AI systems understand page scope, relevance, and freshness before processing the content.

### Why This Matters for AI Discovery

Metadata provides a "fast path" for AI systems to assess content:
- **Title and description** enable quick relevance scoring
- **Tags and category** help route queries to appropriate content
- **Version information** ensures the AI uses current documentation
- **Last-updated date** signals freshness (stale docs are deprioritized)

Without metadata, AI systems must parse and analyze the full content to understand what a page covers. With metadata, they can make routing decisions in milliseconds.

### Recommended Metadata Schema

\`\`\`yaml
---
title: "How to Send Your First Email"
description: "Complete guide to sending transactional emails via the API, including authentication, request format, and error handling"
category: "Getting Started"
tags: ["email", "api", "quickstart", "tutorial"]
api_version: "v2"
last_updated: "2025-03-15"
difficulty: "beginner"
estimated_time: "10 minutes"
---
\`\`\`

### Implementation Guidelines

1. **Be descriptive, not clever:** "How to Send Your First Email" beats "Getting Started with Messaging"
2. **Include keywords naturally:** Description should read well while containing relevant terms
3. **Use consistent categories:** "Getting Started," "API Reference," "Tutorials," "Troubleshooting"
4. **Version prominently:** AI systems need to know which API version a page covers
5. **Update dates honestly:** Stale documentation is worse than no documentation

### GEO Benefits

Generative Engine Optimization specifically benefits from metadata:
- AI assistants can cite version numbers in answers
- Freshness signals improve trustworthiness scores
- Category information helps AI route complex queries

---

## Rule #17: Retrieval-Optimized Sections

### The Principle

Design documentation sections so that AI can retrieve them independently with full context. Each section should be self-contained, with enough information to answer a query without requiring content from other sections.

### Why This Matters for AI Discovery

RAG systems retrieve content in chunks. If your sections depend on context from elsewhere in the document, retrieved chunks will be incomplete or confusing.

Consider this problematic structure:

\`\`\`markdown
## Authentication

We support three authentication methods. Let's look at each one.

### API Keys

This is the simplest method. See the example below.

### OAuth 2.0

For production applications, use this instead. It provides better security.

### JWT Tokens

This method is deprecated. Use OAuth 2.0 for new implementations.
\`\`\`

If an AI retrieves just the "OAuth 2.0" section, it sees: "For production applications, use this instead. It provides better security."

**Useless.** The AI has no idea what "this" refers to or what "instead of" means.

### The Solution: Self-Contained Sections

\`\`\`markdown
## How to authenticate with API keys

API key authentication is the simplest method for getting started with our API. It works well for server-to-server integrations and testing.

Use API keys when:
- You're building a server-side integration
- You need quick authentication for testing
- You don't need user-specific permissions

### Making authenticated requests

Include your API key in the Authorization header:

\`\`\`bash
curl -H "Authorization: Bearer YOUR_API_KEY" https://api.example.com/v1/users
\`\`\`

### Security considerations

- Never expose API keys in client-side code
- Rotate keys regularly using the dashboard
- Use environment variables for key storage
\`\`\`

This section stands alone. An AI retrieving it has everything needed to explain API key authentication.

### Implementation Guidelines

1. **Restate context in each section:** Don't assume the reader (or AI) has read what came before
2. **Avoid forward/backward references:** No "see above" or "as described in the next section"
3. **Include prerequisites locally:** If a section requires prior knowledge, state it explicitly
4. **Make examples complete:** Show full context, not abbreviated snippets
5. **Scope sections narrowly:** One topic per section, thoroughly covered

### The Chunking Strategy

Structure your content with retrieval in mind:

- **H2 sections:** Major topics that answer specific questions
- **H3 subsections:** Supporting details that might be retrieved independently
- **Paragraphs:** Keep to 3-5 sentences when possible
- **Lists and tables:** These chunk well and parse easily

---

## Measuring Discoverability Success

How do you know if your discoverability improvements are working?

### Internal Metrics

1. **Retrieval simulation:** Use embedding models to test if your content retrieves correctly for target queries
2. **Heading coverage:** Audit that all H2/H3 headings follow action-oriented patterns
3. **Metadata completeness:** Ensure 100% of pages have complete metadata
4. **Self-containment score:** Review sections for references to external context

### External Signals

1. **Search ranking improvements:** Track position changes for target keywords
2. **AI citation frequency:** Monitor if AI assistants are citing your documentation
3. **Referral traffic:** Watch for increases from AI platform referrals
4. **Support ticket themes:** Note reductions in "how do I..." questions

---

## Common Discoverability Anti-Patterns

Avoid these patterns that destroy AI discoverability:

### The Mystery Heading
\`\`\`markdown
## Advanced Topics
\`\`\`
*What topics? What makes them advanced? An AI has no idea if this is relevant.*

### The Context-Dependent Section
\`\`\`markdown
## Error Handling

As mentioned in the authentication section, always check for 401 errors.
\`\`\`
*The AI retrieving this chunk has no access to the authentication section.*

### The Missing Metadata
\`\`\`markdown
# API Documentation

Welcome to our API docs...
\`\`\`
*No title, no description, no version. The AI must parse everything to understand scope.*

### The Overly Broad Section
\`\`\`markdown
## Everything You Need to Know

This section covers authentication, rate limits, error handling, webhooks, and SDKs...
\`\`\`
*Too broad to retrieve accurately for specific queries.*

---

## Putting It All Together: A Discoverability Checklist

Use this checklist for every documentation page:

- [ ] **Headings are action-oriented** — Start with "How to," "Setting up," etc.
- [ ] **Headings match user queries** — Mirror the language users actually use
- [ ] **Complete metadata present** — Title, description, tags, category, version
- [ ] **Sections are self-contained** — No "see above" or "as mentioned"
- [ ] **Context is restated locally** — Each section includes its own prerequisites
- [ ] **Examples are complete** — Full code, not abbreviated snippets
- [ ] **Scope is narrow** — One specific topic per section

---

## The Discoverability-First Mindset

Optimizing for AI discoverability requires a mindset shift. Instead of asking "How do I organize this information logically?" ask "How would an AI retrieve this to answer a specific question?"

The discoverability layer is just the first of four in the agent-first documentation framework. Once AI can find your content, the next challenge is ensuring that content actually answers the question. That's where the Answerability layer comes in.`,
  },
  {
    slug: 'self-contained-documentation-answerability',
    title: 'Writing Self-Contained Documentation That AI Can Actually Use: The Answerability Framework',
    description:
      'Learn how to write self-contained documentation sections that answer user queries completely. Master explicit examples, cross-references, and intent-driven content.',
    keywords: [
      'self-contained documentation',
      'documentation answerability',
      'explicit documentation',
      'complete code examples',
      'intent-driven docs',
      'contextual cross-references',
    ],
    date: 'March 2025',
    readingTime: 10,
    category: 'Answerability',
    content: `## The Answerability Crisis in Technical Documentation

Picture this: A developer asks ChatGPT, "How do I paginate through all results in the Stripe API?" The AI retrieves a chunk from Stripe's documentation that says:

> "Use the \`starting_after\` parameter to fetch the next page. See the list charges endpoint for an example."

The AI now faces a dilemma. It has partial information but needs to answer a complete question. Does it:
- Make up an example based on the partial information?
- Tell the user to "see the list charges endpoint" (which the user can't access through the AI)?
- Admit it doesn't have enough information?

**This is the answerability crisis.** The documentation chunk contains information, but not enough to actually answer the user's question.

## What Makes Content "Answerable"?

Answerable content provides everything needed to respond to a query without requiring additional context. For AI systems, this means:

1. **Self-contained sections** — No dependencies on external content
2. **Complete examples** — Full context, not abbreviated snippets
3. **Explicit details** — Nothing left to inference or assumption
4. **Contextual cross-references** — Descriptions of what linked content contains
5. **Intent before mechanics** — Understanding WHY before explaining HOW

Let's explore each rule in depth.

---

## Rule #1: Self-Contained Sections

### The Principle

Every section must make sense on its own. No "see above," "as mentioned earlier," or references to content that won't be retrieved with the section.

### Why This Is the #1 Rule

Claude, one of the leading AI systems, explicitly identified self-contained sections as "the #1 thing" that makes documentation great for agents. Here's why:

When a RAG system retrieves a chunk of documentation, that chunk needs to make sense independently. If a section says "as mentioned above, use the same method"—the AI is blind. It has no access to what was "mentioned above."

### The Problem in Practice

**Poor (Context-Dependent):**
\`\`\`markdown
## Pagination

As described in the authentication section, first obtain an API key. Then use the \`starting_after\` parameter to fetch subsequent pages. See the rate limiting section for information about request frequency.
\`\`\`

An AI retrieving this chunk sees references to:
- "the authentication section" (unavailable)
- "the rate limiting section" (unavailable)

The chunk is essentially useless.

**Better (Self-Contained):**
\`\`\`markdown
## How to paginate through API results

To fetch large result sets, the API uses cursor-based pagination with a \`starting_after\` parameter.

### Prerequisites

- A valid API key (obtain one from Dashboard → Settings → API Keys)
- Understanding of basic API requests (see [How to make your first API call](/first-call))

### Paginating through results

When you make a list request, the response includes:
- \`data\`: Array of results (default: 10 items)
- \`has_more\`: Boolean indicating if more results exist
- \`next_cursor\`: Use this value for the next request

To fetch the next page:

\`\`\`bash
curl -G https://api.example.com/v1/charges \\
  -H "Authorization: Bearer sk_live_xxx" \\
  -d starting_after=charge_123456
\`\`\`

### Rate limiting considerations

Paginated requests count toward your rate limit (100 requests/minute). Implement a 100ms delay between requests to stay within limits.
\`\`\`

This section stands completely alone.

### Implementation Strategy

1. **Restate prerequisites in every section** — Don't assume prior knowledge
2. **Replace pronouns with nouns** — "The API key" not "it"
3. **Include brief context reminders** — "The \`starting_after\` parameter (used for pagination)"
4. **Make examples copy-paste ready** — Full working code, not fragments

---

## Rule #4: Complete Examples

### The Principle

Every example includes full context: setup, the action, and what to expect. Show imports, initialization, the call, and expected output.

### Why Partial Examples Fail

Most documentation shows code fragments. This creates problems for AI systems:

**Poor (Fragment):**
\`\`\`python
response = client.send_email(to="user@example.com", subject="Hello")
\`\`\`

An AI seeing this fragment must guess:
- How was \`client\` created?
- What imports are needed?
- What does the response look like?
- How do I handle errors?

**Better (Complete):**
\`\`\`python
import requests
import os

# Initialize with your API key
api_key = os.environ.get("API_KEY")
base_url = "https://api.example.com/v1"

# Send an email
response = requests.post(
    f"{base_url}/emails",
    headers={"Authorization": f"Bearer {api_key}"},
    json={
        "to": "user@example.com",
        "subject": "Welcome to Our Service",
        "body": "Thanks for signing up!"
    }
)

# Check the response
if response.status_code == 200:
    data = response.json()
    print(f"Email sent! ID: {data['id']}")
    print(f"Status: {data['status']}")  # "queued", "sent", or "delivered"
else:
    print(f"Error: {response.status_code} - {response.text}")
\`\`\`

### The Complete Example Formula

Every complete example should include:

1. **Imports/Dependencies** — What libraries or modules are needed
2. **Setup/Initialization** — How to configure the client or connection
3. **The Action** — The actual code that performs the task
4. **Expected Output** — What a successful response looks like
5. **Error Handling** — How to handle common failures

### Before and After: API Documentation

**Poor:**
\`\`\`markdown
### Send an email

POST /v1/emails

Parameters:
- to (required): Email address
- subject (required): Email subject
- body (required): Email body

Example: \`client.send_email(to, subject, body)\`
\`\`\`

**Better:**
\`\`\`markdown
### How to send an email

Send a transactional email to a single recipient.

**Endpoint:** \`POST /v1/emails\`

**When to use this:**
- Sending welcome emails
- Password reset notifications
- One-time transactional messages

**Prerequisites:**
- Valid API key with \`email:send\` scope
- Verified sender domain

**Request parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| to | string | Yes | Recipient email address |
| subject | string | Yes | Email subject line (max 998 chars) |
| body | string | Yes | Plain text body (max 1MB) |
| from | string | No | Sender address (defaults to verified domain) |

**Complete example:**

\`\`\`bash
# Set your API key
export API_KEY="sk_live_xxxxxxxxxxxxx"

# Send the email
curl -X POST https://api.example.com/v1/emails \\
  -H "Authorization: Bearer $API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "to": "user@example.com",
    "subject": "Welcome!",
    "body": "Thanks for signing up for our service."
  }'
\`\`\`

**Expected response (200 OK):**

\`\`\`json
{
  "id": "email_1234567890",
  "status": "queued",
  "to": "user@example.com",
  "subject": "Welcome!",
  "created_at": "2025-03-15T10:30:00Z"
}
\`\`\`

**Status values:**
- \`queued\`: Email is being processed
- \`sent\`: Email has been sent
- \`delivered\`: Email confirmed delivered
- \`bounced\`: Email could not be delivered

**Common errors:**
- \`400\`: Invalid email format
- \`401\`: Invalid or missing API key
- \`403\`: Unverified sender domain
- \`429\`: Rate limit exceeded (max 100/minute)
\`\`\`

---

## Rule #5: Explicit Over Implicit

### The Principle

State all details explicitly. AI agents have zero ability to "figure it out" or infer meaning from context.

### The Implicitness Trap

Humans are excellent at filling in gaps. We read "the usual timeout applies" and understand what that means based on context. AI systems cannot do this.

**Poor (Implicit):**
\`\`\`markdown
## Rate Limits

Standard rate limiting applies to all endpoints. Contact support if you need higher limits.
\`\`\`

**What's missing:**
- What are the actual limits?
- How are they enforced?
- What happens when exceeded?
- How do I check my current usage?

**Better (Explicit):**
\`\`\`markdown
## API Rate Limits

All API endpoints are rate-limited to ensure service stability.

### Current limits

| Plan | Requests/minute | Burst limit | Monthly quota |
|------|-----------------|-------------|---------------|
| Free | 60 | 10 | 10,000 |
| Pro | 600 | 100 | 100,000 |
| Enterprise | 6,000 | 1,000 | Unlimited |

### How rate limiting works

- **Window:** 60-second sliding window
- **Counter:** Per API key
- **Response headers:** Every response includes rate limit status

\`\`\`
X-RateLimit-Limit: 600
X-RateLimit-Remaining: 423
X-RateLimit-Reset: 1647345600
\`\`\`

### What happens when exceeded

- **Response:** \`429 Too Many Requests\`
- **Body:** \`{ "error": "Rate limit exceeded", "retry_after": 30 }\`
- **Retry:** Wait for \`Retry-After\` seconds (or use exponential backoff)
\`\`\`

### The Explicitness Checklist

For every piece of information, ask:
- [ ] Are all values stated explicitly? (no "standard," "typical," "usual")
- [ ] Are all options documented? (no "etc.," "and so on")
- [ ] Are defaults specified? (what happens if I don't provide this?)
- [ ] Are limits stated clearly? (max, min, allowed values)
- [ ] Are error cases covered? (what can go wrong?)

---

## Rule #11: Contextual Cross-References

### The Principle

Never use "click here" or bare links. Always describe what the linked page covers so AI systems (and users) understand the relationship.

### Why Bare Links Fail

**Poor:**
\`\`\`markdown
For more information, see [this page](/auth) and [here](/errors).
\`\`\`

An AI retrieving this has no idea what "this page" or "here" contains. It can't follow links, so these references are meaningless.

**Better:**
\`\`\`markdown
For authentication details, see [How to authenticate with API keys](/auth), which covers:
- Generating API keys
- Including keys in requests
- Rotating compromised keys
- Troubleshooting 401 errors

For error handling, see [Complete guide to API error codes](/errors), including:
- HTTP status code reference
- Error response formats
- Retry strategies for each error type
\`\`\`

### The Contextual Cross-Reference Formula

\`\`\`markdown
For [specific topic], see [descriptive link text](URL), which covers:
- [Specific subtopic 1]
- [Specific subtopic 2]
- [Specific subtopic 3]
\`\`\`

This gives AI systems (and users) enough context to understand whether following the link is worthwhile.

### Implementation Guidelines

1. **Describe the destination:** What will the reader learn?
2. **List key topics:** What specific content is covered?
3. **Explain the relationship:** How does this relate to the current content?
4. **Use descriptive anchor text:** Never "click here" or "this page"

---

## Rule #18: Intent Before Mechanics

### The Principle

Always explain WHY before HOW. Provide context before diving into instructions.

### The Mechanics-First Problem

**Poor:**
\`\`\`markdown
## POST /webhooks

Call this endpoint to create a webhook. Parameters:
- url (required): The webhook URL
- events (required): Array of event types
- secret (optional): Webhook secret
\`\`\`

**What's missing:** Why would someone create a webhook? When should they use this vs. polling?

**Better:**
\`\`\`markdown
## How to receive real-time event notifications

Webhooks allow your application to receive real-time notifications when events occur in your account, eliminating the need to poll for updates.

### When to use webhooks

Use webhooks when you need to:
- Update your database when payments complete
- Send customer notifications on order status changes
- Synchronize data between systems in real-time
- Trigger automated workflows based on events

**Webhook vs. Polling:**
- **Webhooks:** We push events to you (instant, efficient)
- **Polling:** You check for updates (delayed, resource-intensive)

Use webhooks for real-time needs. Use polling only if you can't receive HTTP callbacks.

### Creating a webhook endpoint

To start receiving events, create a webhook endpoint:

\`\`\`bash
curl -X POST https://api.example.com/v1/webhooks \\
  -H "Authorization: Bearer $API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "url": "https://your-app.com/webhooks",
    "events": ["payment.success", "payment.failed"],
    "secret": "whsec_your_secret"
  }'
\`\`\`
\`\`\`

### The Intent-First Structure

1. **What is this?** — Define the concept
2. **Why use it?** — Explain the value proposition
3. **When to use it?** — Provide decision guidance
4. **How to use it?** — Give the implementation details
5. **What next?** — Link to related topics

---

## Measuring Answerability

How do you know if your content is truly answerable?

### The Isolation Test

For each section, ask:
- If an AI retrieved only this section, could it answer a user's question?
- Does it include all necessary context?
- Are examples complete enough to be actionable?

### The Completeness Checklist

- [ ] Sections are self-contained (no external dependencies)
- [ ] Examples include imports, setup, and expected output
- [ ] All values are stated explicitly (no "standard" or "typical")
- [ ] Cross-references describe the linked content
- [ ] Intent is explained before mechanics
- [ ] Error cases are documented
- [ ] Prerequisites are stated up front

---

## The Answerability Mindset

Creating answerable content requires empathy for how AI systems consume information. Every section should be written as if it's the only content the AI will see—because often, it is.

The answerability layer ensures that when AI finds your content, it can actually use it to help users. But finding and answering are just the beginning. The next layer—Operability—focuses on turning answers into actions.`,
  },
  {
    slug: 'operable-documentation-ai-agents',
    title: 'From Theory to Action: Building Operable Documentation for AI Agents',
    description:
      'Transform your documentation into actionable resources. Learn structured data tables, prerequisites, expected outcomes, and lifecycle documentation for AI operability.',
    keywords: [
      'operable documentation',
      'AI agent documentation',
      'structured data tables',
      'documentation prerequisites',
      'lifecycle documentation',
      'expected outcomes',
    ],
    date: 'March 2025',
    readingTime: 10,
    category: 'Operability',
    content: `## The Gap Between Knowing and Doing

A developer asks their AI assistant: "How do I implement user authentication with your API?"

The AI retrieves documentation that explains:
- What authentication is
- Why it's important
- Different authentication methods available

But the developer's actual need is:
- The exact API endpoint to call
- The exact headers to include
- The exact format of the request body
- The exact error responses to handle

**This is the operability gap.** Documentation that explains concepts without enabling action.

## What Is Operable Documentation?

Operable documentation provides everything needed to turn understanding into execution. It bridges the gap between "I know what to do" and "I've done it."

For AI agents, operability means the documentation contains:
- Structured data that can be extracted and used programmatically
- Clear prerequisites so the agent knows what's needed
- Expected outcomes so the agent can verify success
- Separated content types so the agent knows what kind of answer to provide
- Comparison sections for decision-making
- Lifecycle documentation for state management

Let's explore each rule in depth.

---

## Rule #3: Structured Data Tables

### The Principle

Options, features, and specifications should be in tables (name, type, description), not buried in paragraphs.

### Why Tables Win

AI systems parse structured data far more effectively than prose. A table with \`name | type | required | default | description\` is instantly machine-readable. A paragraph describing the same information requires complex natural language processing.

### The Paragraph Problem

**Poor (Buried in Prose):**
\`\`\`markdown
The create user endpoint accepts several parameters. The email parameter is required and should be a valid email address string. The name parameter is optional and accepts a string up to 50 characters. The role parameter defaults to 'user' but can be set to 'admin' if you need elevated permissions. The metadata parameter accepts an object with custom key-value pairs.
\`\`\`

An AI parsing this must:
1. Identify that these are parameters
2. Extract each parameter name
3. Determine type information
4. Figure out which are required
5. Find default values

**Better (Structured Table):**
\`\`\`markdown
### Request parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| email | string | Yes | — | Valid email address |
| name | string | No | — | Display name (max 50 chars) |
| role | enum | No | \`user\` | Either \`user\` or \`admin\` |
| metadata | object | No | \`{}\` | Custom key-value pairs |
\`\`\`

### Table Best Practices

1. **Consistent column order:** Name, Type, Required, Default, Description
2. **Explicit defaults:** Use "—" for none, actual value when present
3. **Type specificity:** \`string\` vs \`enum\` vs \`object\` vs \`array\`
4. **Length limits:** Include when applicable (max 50 chars)
5. **Valid values:** List enum options or value ranges

### Advanced Table Patterns

**Response Schema:**
\`\`\`markdown
### Response fields

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| id | string | No | Unique identifier |
| email | string | No | User's email address |
| created_at | ISO 8601 | No | Account creation timestamp |
| last_login | ISO 8601 | Yes | Last successful login |
| metadata | object | No | Custom user data |
\`\`\`

**Error Codes:**
\`\`\`markdown
### Error responses

| Status | Code | Cause | Resolution |
|--------|------|-------|------------|
| 400 | invalid_email | Malformed email | Check email format |
| 409 | email_exists | Email in use | Use different email or reset password |
| 422 | name_too_long | Name > 50 chars | Shorten name |
\`\`\`

**Feature Comparison:**
\`\`\`markdown
### Plan features

| Feature | Free | Pro | Enterprise |
|---------|------|-----|------------|
| API calls/month | 10K | 100K | Unlimited |
| Webhooks | ✗ | ✓ | ✓ |
| Custom domains | ✗ | 1 | Unlimited |
| Priority support | ✗ | ✗ | ✓ |
\`\`\`

---

## Rule #9: Prerequisites Up Front

### The Principle

State all requirements at the top: accounts, permissions, plans, setup steps. Don't bury prerequisites in the middle of instructions.

### The Hidden Prerequisite Problem

**Poor:**
\`\`\`markdown
# How to Send Emails

First, create an email template in the dashboard...

[Three paragraphs later...]

Note: You must have a verified sender domain before emails will be delivered.
\`\`\`

The user has already spent time following instructions that won't work for them.

**Better:**
\`\`\`markdown
# How to send your first email

## Prerequisites

Before you begin, ensure you have:

- [ ] **API key** with \`email:send\` scope ([get one here](/api-keys))
- [ ] **Verified sender domain** ([verify your domain](/domains))
- [ ] **Node.js 16+** installed ([download](https://nodejs.org))
- [ ] **5 minutes** to complete this tutorial

**Estimated time:** 5 minutes
**Difficulty:** Beginner

---

## Step 1: Install the SDK...
\`\`\`

### The Prerequisites Checklist Pattern

\`\`\`markdown
## Prerequisites

Before starting, you need:

**Required:**
- [ ] Valid API key ([how to get one](/api-keys))
- [ ] Account with Pro plan or higher ([upgrade](/billing))
- [ ] \`admin\` role permission ([check your role](/account))

**Recommended:**
- [ ] Basic familiarity with REST APIs
- [ ] curl or HTTP client installed

**Optional:**
- [ ] Webhook endpoint configured (for real-time updates)
\`\`\`

### Why This Matters for AI

When an AI retrieves a "How to" guide, it needs to quickly assess whether the user can actually follow it. Prerequisites up front enable the AI to:
- Warn users about missing requirements
- Suggest prerequisite steps first
- Route users to appropriate content based on their situation

---

## Rule #10: Expected Outcomes

### The Principle

Show what success looks like: expected results, confirmations, next steps.

### The Missing Outcome Problem

**Poor:**
\`\`\`markdown
## How to create a webhook

Call the POST /webhooks endpoint with your URL and events.

\`\`\`bash
curl -X POST https://api.example.com/v1/webhooks \\
  -d '{"url": "https://example.com/webhook", "events": ["payment.success"]}'
\`\`\`

Your webhook is now created.
\`\`\`

**What's missing:**
- What does the response look like?
- How do I know it worked?
- What should I do next?

**Better:**
\`\`\`markdown
## How to create a webhook

### Making the request

\`\`\`bash
curl -X POST https://api.example.com/v1/webhooks \\
  -H "Authorization: Bearer $API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "url": "https://your-app.com/webhooks",
    "events": ["payment.success"]
  }'
\`\`\`

### Expected response (201 Created)

\`\`\`json
{
  "id": "wh_1234567890",
  "url": "https://your-app.com/webhooks",
  "events": ["payment.success"],
  "status": "active",
  "created_at": "2025-03-15T10:30:00Z",
  "secret": "whsec_xxxxxxxxxxxxx"
}
\`\`\`

### How to verify it worked

1. **Check the dashboard:** Go to [Webhooks settings](/dashboard/webhooks) — your webhook should appear in the list
2. **Test with a ping:** Send a test event:
   \`\`\`bash
   curl -X POST https://api.example.com/v1/webhooks/wh_1234567890/ping
   \`\`\`
3. **Check your endpoint:** You should receive a POST request with event type \`webhook.ping\`

### What to do next

- [Secure your webhook endpoint](/webhooks/security) by verifying signatures
- [Handle webhook failures](/webhooks/errors) like timeouts and retries
- [Test with sandbox events](/webhooks/testing) before going live
\`\`\`

### The Expected Outcome Formula

For every task, document:
1. **The expected response** — Status code and body
2. **How to verify success** — Concrete verification steps
3. **What success looks like** — Dashboard changes, notifications, etc.
4. **Next steps** — What to do after completing this task

---

## Rule #12: Content Type Separation

### The Principle

Separate explanations, step-by-step guides, and reference content clearly. Don't mix tutorials with API reference.

### The Mixed Content Problem

**Poor:**
\`\`\`markdown
# Authentication

Authentication is important for securing your API requests. We use API keys for authentication.

To authenticate, include your API key in the Authorization header:

\`\`\`bash
curl -H "Authorization: Bearer YOUR_KEY" https://api.example.com
\`\`\`

The API key should be kept secure. Don't commit it to version control. The header format is \`Authorization: Bearer {key}\`. Keys are 32 characters long and start with \`sk_live_\` or \`sk_test_\`.

Now let's walk through setting up authentication in your application...
\`\`\`

This mixes:
- Conceptual explanation
- Reference information
- Tutorial content

**Better (Separated):**

**Conceptual doc:** [Understanding API Authentication](/concepts/authentication)
- What authentication is
- Why it's important
- Different methods available
- Security best practices

**Tutorial:** [How to authenticate with API keys](/tutorials/first-auth)
- Step-by-step setup
- Complete working example
- Verification steps

**Reference:** [API key authentication reference](/reference/auth)
- Header format
- Key format specifications
- Error responses
- All parameters

### Content Type Definitions

| Type | Purpose | Structure |
|------|---------|-----------|
| **Conceptual** | Explain what and why | Narrative, examples, diagrams |
| **Tutorial** | Guide through first use | Step-by-step, prerequisites, outcomes |
| **How-to Guide** | Solve specific problems | Task-focused, assumes basic knowledge |
| **Reference** | Lookup exact details | Tables, specifications, exhaustive |

### Why This Matters for AI

When AI systems understand content type, they can:
- Route conceptual questions to explanation docs
- Provide step-by-step guidance from tutorials
- Look up precise details from reference
- Not mix explanation with implementation

---

## Rule #14: Comparison Sections

### The Principle

Include "When to use X vs Y" sections so agents can answer comparison questions.

### The Comparison Problem

Users frequently ask AI assistants to compare options:
- "Should I use webhooks or polling?"
- "When should I use batch endpoints?"
- "OAuth vs API keys—which should I choose?"

If your documentation doesn't explicitly compare options, the AI must infer or guess.

### The Comparison Section Template

\`\`\`markdown
## When to use webhooks vs polling

Use **webhooks** when:
- You need real-time updates
- You can receive HTTP callbacks
- You want to minimize API calls
- Events are time-sensitive

Use **polling** when:
- You can't expose a public endpoint
- You need full control over timing
- You're behind a firewall
- Webhook delivery isn't guaranteed

### Quick comparison

| Factor | Webhooks | Polling |
|--------|----------|---------|
| Latency | Instant | Depends on frequency |
| API calls | Fewer | More frequent |
| Complexity | Higher | Lower |
| Reliability | Depends on your endpoint | Fully controlled |

### Decision flowchart

\`\`\`
Can you receive HTTP callbacks?
├── Yes → Use webhooks
└── No → Use polling
\`\`\`

### Migration path

If you're currently using polling and want to switch to webhooks:
1. Set up your webhook endpoint
2. Configure webhook subscriptions
3. Run both in parallel during testing
4. Remove polling after verification
\`\`\`

### Common Comparison Topics

Document comparisons for:
- Authentication methods (API keys vs OAuth vs JWT)
- Integration patterns (webhooks vs polling vs streaming)
- Plan tiers (Free vs Pro vs Enterprise)
- API versions (v1 vs v2 migration)
- SDK options (official vs community)

---

## Rule #19: Lifecycle & Status

### The Principle

Document processes as flows: pending, active, completed, cancelled. Show state transitions, not just end states.

### Why Lifecycle Documentation Matters

Many API operations involve asynchronous processes:
- Payment processing
- File uploads
- Report generation
- Batch operations

Users (and AI agents) need to understand:
- What states exist
- How to check current state
- What transitions are possible
- How long each state typically lasts

### The Lifecycle Documentation Template

\`\`\`markdown
## Payment lifecycle

Payments move through several states from creation to completion.

### State diagram

\`\`\`
[pending] → [processing] → [succeeded]
    ↓            ↓
[cancelled]  [failed]
\`\`\`

### State descriptions

| State | Description | Typical Duration |
|-------|-------------|------------------|
| \`pending\` | Payment initiated, awaiting processing | < 1 second |
| \`processing\` | Payment being processed by provider | 2-5 seconds |
| \`succeeded\` | Payment completed successfully | Final state |
| \`failed\` | Payment could not be completed | Final state |
| \`cancelled\` | Payment cancelled before completion | Final state |

### State transitions

- \`pending\` → \`processing\`: Automatic
- \`processing\` → \`succeeded\`: On successful charge
- \`processing\` → \`failed\`: On error (see error codes)
- \`pending\` → \`cancelled\`: If you cancel within 5 seconds

### Webhook events

You'll receive webhook events for state changes:
- \`payment.processing_started\`
- \`payment.succeeded\`
- \`payment.failed\`
- \`payment.cancelled\`
\`\`\`

### Lifecycle Documentation Checklist

- [ ] All states documented
- [ ] State transitions explained
- [ ] Typical durations specified
- [ ] How to check current state
- [ ] Webhook events for state changes
- [ ] Retry and error behavior

---

## Measuring Operability

### The Actionability Test

For each piece of documentation, ask:
- Can an AI extract structured data from this?
- Are prerequisites stated before instructions?
- Is success clearly defined?
- Can a user go from reading to doing?

### The Operability Scorecard

| Criterion | Weight | Score |
|-----------|--------|-------|
| Structured data present | 20% | /10 |
| Prerequisites clear | 20% | /10 |
| Expected outcomes documented | 20% | /10 |
| Content types separated | 15% | /10 |
| Comparisons included | 15% | /10 |
| Lifecycle documented | 10% | /10 |

---

## The Operability Mindset

Operable documentation treats every page as a potential starting point for action. It doesn't assume the reader will explore—it assumes they need to accomplish something specific, right now.

The operability layer ensures that when AI finds your content and understands it, the user can actually act on it. But action requires trust. The next layer—Trustability—focuses on building confidence in your documentation.`,
  },
  {
    slug: 'trustability-layer-agent-documentation',
    title: 'Building Trust with AI: The Trustability Layer of Agent-First Documentation',
    description:
      'Build trust with AI agents through consistent terminology, comprehensive error documentation, version clarity, and safety warnings. The complete trustability framework.',
    keywords: [
      'documentation trustability',
      'error documentation',
      'consistent terminology',
      'version clarity',
      'AI safety documentation',
      'documentation warnings',
    ],
    date: 'March 2025',
    readingTime: 10,
    category: 'Trustability',
    content: `## The Trust Problem in AI-Mediated Documentation

A developer asks their AI assistant: "What's the best way to delete a user account?"

The AI retrieves documentation and responds: "Call DELETE /users/{id} to remove the user."

What the AI doesn't know—because the documentation doesn't state it explicitly—is that this action:
- Is irreversible
- Deletes all associated data
- Cannot be undone even by support
- Should be confirmed with the user first

**This is the trust problem.** AI agents need documentation they can trust to give safe, accurate advice. When documentation omits critical safety information, version details, or error context, AI systems can give harmful recommendations.

## Why Trustability Matters More for AI

Humans have judgment. When documentation says "delete the user," a human might think "wait, is this reversible?" and look for more information. AI systems don't have this safety mechanism—they work with what they're given.

For AI agents to be trustworthy intermediaries, they need documentation that:
- Documents errors comprehensively (so they can help users recover)
- Uses consistent terminology (so they don't confuse similar concepts)
- States versions clearly (so they don't use outdated information)
- Warns about safety issues (so they don't enable harmful actions)
- Avoids anti-patterns (so they don't learn bad habits)
- Highlights important information (so they can prioritize warnings)

Let's explore each rule in depth.

---

## Rule #6: First-Class Error Docs

### The Principle

Every error or issue should be documented with causes, steps to diagnose, and fixes. Error documentation should be as comprehensive as success documentation.

### The Error Documentation Gap

Most documentation focuses on happy paths. When errors occur, users (and AI agents) are left guessing. This is especially problematic because:
- Users often consult AI assistants specifically when something goes wrong
- Error states are when users need the most help
- Incomplete error docs lead to support tickets

### The Comprehensive Error Documentation Template

\`\`\`markdown
## Error: 429 Rate Limit Exceeded

### What this error means

You've exceeded the rate limit for API requests. The API has temporarily blocked additional requests from your API key.

### When this happens

- Making more than 600 requests per minute (Pro plan)
- Bursting more than 100 requests in a single second
- Not implementing request throttling

### How to diagnose

1. **Check response headers:**
   \`\`\`
   X-RateLimit-Limit: 600
   X-RateLimit-Remaining: 0
   X-RateLimit-Reset: 1647345600
   \`\`\`

2. **Check your usage in the dashboard:**
   Go to [Dashboard → API Usage](/dashboard/usage) to see your request patterns

3. **Identify the pattern:**
   - Is it a sustained high rate? → Implement throttling
   - Is it a burst during startup? → Add exponential backoff
   - Is it across multiple services? → Check for shared API keys

### How to fix

**Immediate fix:** Wait for the rate limit window to reset (check \`X-RateLimit-Reset\` timestamp)

**Long-term solutions:**

1. **Implement request throttling:**
   \`\`\`python
   import time

   def make_request_with_throttle():
       # Max 10 requests per second
       time.sleep(0.1)
       return make_api_request()
   \`\`\`

2. **Add exponential backoff:**
   \`\`\`python
   def request_with_backoff(max_retries=3):
       for attempt in range(max_retries):
           response = make_request()
           if response.status_code == 429:
               wait_time = 2 ** attempt  # 1s, 2s, 4s
               time.sleep(wait_time)
           else:
               return response
       raise Exception("Rate limit exceeded after retries")
   \`\`\`

3. **Cache responses:** Store frequently accessed data locally

4. **Request a limit increase:** Pro and Enterprise customers can [request higher limits](/billing/limits)

### Is retrying safe?

**Yes** — Rate limit errors are always safe to retry. The request was not processed.

### Related errors

- [401 Unauthorized](/errors/401) — Authentication issues
- [403 Forbidden](/errors/403) — Permission issues
- [500 Server Error](/errors/500) — Temporary server issues
\`\`\`

### Error Documentation Checklist

Every error should document:
- [ ] **What it means** — Clear explanation
- [ ] **When it happens** — Trigger conditions
- [ ] **How to diagnose** — Debugging steps
- [ ] **How to fix** — Resolution steps
- [ ] **Is retrying safe?** — Critical for automation
- [ ] **Related errors** — For error classification

### Common Errors to Document

- Authentication errors (401, 403)
- Rate limiting (429)
- Validation errors (400, 422)
- Not found errors (404)
- Server errors (500, 502, 503)
- Timeout errors
- Webhook delivery failures

---

## Rule #7: Consistent Terminology

### The Principle

Use one term per concept everywhere. No alternating between synonyms.

### The Terminology Trap

**Poor (Inconsistent):**
\`\`\`markdown
# User Management

To create a new user, call the create account endpoint. The customer ID will be returned in the response. You can then add the account to a workspace. Each team can have multiple members.
\`\`\`

Terms used interchangeably:
- User / Account / Customer
- Workspace / Team

An AI will treat these as distinct concepts, leading to confused answers.

**Better (Consistent):**
\`\`\`markdown
# User Management

To create a new user, call the create user endpoint. The user ID will be returned in the response. You can then add the user to an organization. Each organization can have multiple users.
\`\`\`

### The Terminology Registry

Maintain a canonical term list:

| Concept | Canonical Term | Incorrect Alternatives |
|---------|---------------|----------------------|
| End user | user | customer, account, client |
| Company account | organization | workspace, team, account |
| API credential | API key | token, secret, credential |
| Permission scope | scope | permission, access level |
| Unique identifier | ID | identifier, key, uuid |

### Implementation Guidelines

1. **Create a glossary** — Document canonical terms
2. **Audit for consistency** — Search for alternative terms
3. **Enforce in reviews** — Check terminology in doc reviews
4. **Update everywhere** — When changing terms, update all occurrences

### Why This Matters for AI

AI systems build semantic models of your product. Inconsistent terminology:
- Creates multiple representations of the same concept
- Leads to fragmented understanding
- Causes confused or contradictory answers

---

## Rule #13: Version Clarity

### The Principle

Version or date stated prominently. Outdated content marked with alternatives.

### The Version Confusion Problem

**Poor:**
\`\`\`markdown
# API Reference

## Authentication

Include your API key in the Authorization header...
\`\`\`

What version of the API? Is this current? Will this code work today?

**Better:**
\`\`\`markdown
---
title: API Authentication
api_version: v2.3
last_updated: 2025-03-15
deprecation_status: stable
---

# API Authentication (v2.3)

**Last updated:** March 15, 2025
**API version:** v2.3
**Status:** Stable

> **Looking for v1 docs?** [API v1 Authentication](/v1/auth) (deprecated, sunset date: 2025-12-31)

## Authentication

Include your API key in the Authorization header...
\`\`\`

### Version Documentation Best Practices

1. **Version in URL:** \`/v2/authentication\` not \`/authentication\`
2. **Version banner:** Prominent display on every page
3. **Last updated date:** Shows freshness
4. **Deprecation notices:** Clear warnings for outdated content
5. **Migration guides:** Path from old to new versions

### The Version Banner Template

\`\`\`markdown
> **API Version:** v2.3
> **Last Updated:** March 15, 2025
> **Status:** Stable
> **Previous Version:** [v2.2](/v2.2/auth) | **Next Version:** [v2.4 (beta)](/v2.4/auth)
\`\`\`

### Deprecation Documentation

\`\`\`markdown
> ⚠️ **Deprecated**
> This endpoint is deprecated and will be removed on December 31, 2025.
> **Migration:** Use [the new endpoint](/v2/users) instead.
> **Timeline:**
> - March 2025: Deprecation announced
> - June 2025: Warning emails sent
> - December 2025: Endpoint removed
\`\`\`

### Why Version Clarity Matters for AI

AI systems need to know:
- Is this information current?
- Will this code work with the latest API?
- Are there newer alternatives?

Without version clarity, AI may give outdated advice.

---

## Rule #15: Safety & Limits

### The Principle

Irreversible actions, billing implications, and limits clearly documented.

### The Safety Documentation Gap

**Poor:**
\`\`\`markdown
## Delete User

DELETE /users/{id}

Removes a user from the system.
\`\`\`

**What's missing:** This is irreversible. All user data will be lost.

**Better:**
\`\`\`markdown
## Delete a user

\`DELETE /users/{id}\`

Permanently removes a user and all associated data from the system.

⚠️ **Warning: This action is irreversible**

- User data cannot be recovered after deletion
- Associated records (orders, payments) will be anonymized
- This action cannot be undone by support
- Consider [deactivating](/users/deactivate) instead if you may need the data later

### Before deleting

1. **Export user data:** [Download user record](/users/{id}/export)
2. **Check for active subscriptions:** Cancel to avoid billing issues
3. **Notify the user:** Required by GDPR for EU users

### Billing implications

- User's subscription will be cancelled immediately
- No prorated refunds are issued
- Outstanding invoices remain due

### Alternative: Deactivate

If you might need the user data later, consider [deactivating the user](/users/deactivate) instead:
- User cannot log in
- Data is preserved
- Can be reactivated later
\`\`\`

### Safety Documentation Checklist

For any destructive or impactful action, document:
- [ ] **Warning callout** — Prominent warning at the top
- [ ] **What's irreversible** — Specific consequences
- [ ] **Billing implications** — Cost impacts
- [ ] **Prerequisites before action** — Safety checks
- [ ] **Alternatives** — Safer options if available
- [ ] **Limits** — Rate limits or quotas

### Common Safety-Critical Operations

- Data deletion (users, accounts, records)
- Billing changes (upgrades, cancellations)
- Permission changes (granting admin access)
- API key rotation (revoking old keys)
- Webhook endpoint changes (affecting live systems)

---

## Rule #16: No Anti-Patterns

### The Principle

Strip marketing fluff, "contact us" dead-ends, and content hidden behind JavaScript widgets.

### Common Anti-Patterns

**Marketing Fluff:**
\`\`\`markdown
Our world-class API leverages cutting-edge technology to seamlessly unlock next-generation workflows for your business.
\`\`\`

**Why it's bad:** No actionable information. Pure noise.

**Contact Us Dead-Ends:**
\`\`\`markdown
For more information about enterprise features, contact our sales team.
\`\`\`

**Why it's bad:** AI can't follow up. The information trail ends.

**JavaScript-Only Content:**
\`\`\`markdown
<div id="api-docs"></div>
<script>loadDocs();</script>
\`\`\`

**Why it's bad:** AI crawlers see empty content. Nothing to retrieve.

### The Anti-Pattern Elimination Checklist

- [ ] **Remove marketing language** — Replace with concrete facts
- [ ] **Expand "contact us" sections** — Provide self-service information
- [ ] **Ensure server-side rendering** — Content in HTML, not JS
- [ ] **Add text alternatives** — Describe images in prose
- [ ] **Avoid tab-only content** — All content visible by default

### Before and After: Anti-Pattern Fixes

**Marketing fluff → Concrete facts:**
\`\`\`markdown
❌ "Our world-class API leverages cutting-edge technology..."
✅ "The API supports 10,000 requests per second with 99.99% uptime."
\`\`\`

**Contact us → Self-service:**
\`\`\`markdown
❌ "Contact sales for enterprise pricing."
✅ "Enterprise pricing starts at $500/month for 1M API calls. [View full pricing](/enterprise/pricing) or [contact sales](/contact) for custom quotes."
\`\`\`

---

## Rule #20: Callouts & Warnings

### The Principle

Use standard callout format for warnings, tips, and important notes that AI can prioritize.

### The Callout Format

Use consistent, semantic callout syntax:

\`\`\`markdown
> **Note:** Additional context or helpful information.

> **Tip:** Best practices and optimization suggestions.

> **Warning:** Potential issues that won't break things but should be considered.

> **Danger:** Critical warnings about irreversible actions or data loss.
\`\`\`

### Why Standard Callouts Matter

AI systems can:
- Recognize callout patterns
- Prioritize danger warnings
- Include tips as supplementary information
- Structure responses with appropriate emphasis

### Callout Examples

**Note:**
\`\`\`markdown
> **Note:** The default rate limit is 100 requests per minute. You can check your current limit in the dashboard.
\`\`\`

**Tip:**
\`\`\`markdown
> **Tip:** Use the \`expand\` parameter to include related objects in a single request, reducing API calls.
\`\`\`

**Warning:**
\`\`\`markdown
> **Warning:** Changing your webhook URL will immediately start sending events to the new endpoint. Ensure it's ready to receive traffic.
\`\`\`

**Danger:**
\`\`\`markdown
> **Danger:** Deleting an organization permanently removes all data, including users, projects, and billing history. This cannot be undone.
\`\`\`

### Callout Best Practices

1. **Use consistently** — Same format across all docs
2. **Place prominently** — Warnings before the relevant content
3. **Be specific** — Explain the risk, not just "be careful"
4. **Provide alternatives** — Suggest safer approaches when possible

---

## Measuring Trustability

### The Trustworthiness Test

Ask these questions about your documentation:
- Can an AI help users recover from errors?
- Will terminology be consistent across all answers?
- Is version information clear and current?
- Are safety warnings prominent and specific?
- Is there any content AI can't access?

### The Trustability Scorecard

| Criterion | Weight | Score |
|-----------|--------|-------|
| Error docs comprehensive | 25% | /10 |
| Terminology consistent | 20% | /10 |
| Version clarity | 20% | /10 |
| Safety warnings present | 20% | /10 |
| No anti-patterns | 15% | /10 |

---

## The Trustability Mindset

Trustable documentation assumes the reader (or AI) needs to make decisions with consequences. It doesn't hide risks, bury version information, or use vague language that could be misinterpreted.

The trustability layer ensures that when AI finds, understands, and can act on your content, it does so safely and accurately. Together, the four layers—Discoverability, Answerability, Operability, and Trustability—create documentation that serves the AI economy.`,
  },
  {
    slug: 'agent-first-documentation-checklist',
    title: 'The Complete Agent-First Documentation Checklist: 20 Rules to Transform Your Docs',
    description:
      'The complete 20-rule checklist for agent-first documentation. Transform your docs for the AI economy with this actionable implementation guide and scoring framework.',
    keywords: [
      'documentation checklist',
      'agent-first docs checklist',
      'AI documentation guide',
      'documentation transformation',
      'GEO checklist',
      'implementation guide',
    ],
    date: 'March 2025',
    readingTime: 12,
    category: 'Strategy',
    content: `## Your Roadmap to Agent-First Documentation

You've learned about the four layers of agent-first documentation: Discoverability, Answerability, Operability, and Trustability. Now it's time to put it into practice.

This article provides a complete implementation roadmap, including:
- A printable checklist of all 20 rules
- Priority-based implementation phases
- Before/after examples for each rule
- Measurement strategies to track progress
- Tools and automation to accelerate the transformation

Let's transform your documentation for the AI economy.

---

## The Complete 20-Rule Checklist

### Layer 1: Discoverability
How easily can AI find the right information?

#### Rule #2: Action-Oriented Headings
- [ ] Headings start with action verbs ("How to," "Setting up")
- [ ] Headings match user query patterns
- [ ] Headings are specific, not generic ("How to authenticate with OAuth" not "Authentication")
- [ ] All H2/H3 headings follow this pattern

**Quick test:** Can you imagine a user asking an AI the exact text of your heading?

#### Rule #8: Page Metadata
- [ ] Every page has a descriptive title
- [ ] Every page has a meta description
- [ ] Category is specified for each page
- [ ] Tags are included for discoverability
- [ ] API version is stated (for API docs)
- [ ] Last updated date is present
- [ ] Difficulty/estimated time included (for tutorials)

**Quick test:** Can an AI understand what a page covers from its metadata alone?

#### Rule #17: Retrieval-Optimized
- [ ] Sections are scoped to single topics
- [ ] Each section can stand alone
- [ ] No section depends on prior context
- [ ] Content chunks are appropriately sized (200-500 tokens)
- [ ] Key information isn't buried in long paragraphs

**Quick test:** If an AI retrieved only this section, would it make sense?

---

### Layer 2: Answerability
Once found, does the content actually answer the question?

#### Rule #1: Self-Contained Sections
- [ ] No "see above" or "as mentioned earlier" references
- [ ] Context is restated in each section
- [ ] Pronouns are replaced with specific nouns
- [ ] Prerequisites are included locally
- [ ] Examples don't depend on external content

**Quick test:** Can someone understand this section without reading anything else?

#### Rule #4: Complete Examples
- [ ] Examples include imports/dependencies
- [ ] Examples include setup/initialization
- [ ] Examples show the complete action
- [ ] Examples include expected output
- [ ] Examples include error handling
- [ ] Examples are copy-paste ready

**Quick test:** Can a developer copy, paste, and run your example successfully?

#### Rule #5: Explicit Over Implicit
- [ ] All values stated explicitly (no "standard" or "typical")
- [ ] All options documented (no "etc.")
- [ ] Defaults specified for all optional parameters
- [ ] Limits stated clearly (max, min, allowed values)
- [ ] Error cases covered

**Quick test:** Is there anything an AI would need to infer or guess?

#### Rule #11: Contextual Cross-References
- [ ] No bare "click here" links
- [ ] Link text describes the destination
- [ ] Cross-references explain what the linked content covers
- [ ] Related topics are linked with context

**Quick test:** Does the link text alone tell you what you'll find?

#### Rule #18: Intent Before Mechanics
- [ ] Purpose is explained before instructions
- [ ] "Why" comes before "how"
- [ ] Use cases are described
- [ ] Alternatives are mentioned when relevant
- [ ] Decision guidance is provided

**Quick test:** Does the reader understand why they're doing this before learning how?

---

### Layer 3: Operability
Can the agent turn the answer into action?

#### Rule #3: Structured Data Tables
- [ ] Parameters are in tables (name, type, required, default, description)
- [ ] Response fields are in tables
- [ ] Error codes are in tables
- [ ] Feature comparisons are in tables
- [ ] No parameter descriptions buried in prose

**Quick test:** Can an AI extract structured data without parsing paragraphs?

#### Rule #9: Prerequisites Up Front
- [ ] All requirements stated at the top
- [ ] Prerequisites include accounts needed
- [ ] Prerequisites include permissions required
- [ ] Prerequisites include plan/tier restrictions
- [ ] Prerequisites include setup steps
- [ ] Prerequisites are in checklist format

**Quick test:** Can a user verify they have everything needed before starting?

#### Rule #10: Expected Outcomes
- [ ] Success is clearly defined
- [ ] Expected responses are documented
- [ ] Verification steps are provided
- [ ] Next steps are listed
- [ ] Common outcomes are described

**Quick test:** Does the user know exactly what success looks like?

#### Rule #12: Content Type Separation
- [ ] Concepts are separated from tutorials
- [ ] Tutorials are separated from reference
- [ ] How-to guides are task-focused
- [ ] Reference docs are comprehensive
- [ ] Content types are clearly labeled

**Quick test:** Can a user quickly identify what type of content they're reading?

#### Rule #14: Comparison Sections
- [ ] "When to use X vs Y" sections exist
- [ ] Common decision points are documented
- [ ] Trade-offs are explained
- [ ] Decision flowcharts or tables are included
- [ ] Migration paths are documented

**Quick test:** Can an AI answer "should I use X or Y?" from your docs?

#### Rule #19: Lifecycle & Status
- [ ] Process states are documented
- [ ] State transitions are explained
- [ ] How to check current state is documented
- [ ] Webhook events for state changes are listed
- [ ] Typical durations are specified
- [ ] Retry behavior is documented

**Quick test:** Can a user understand where they are in a multi-step process?

---

### Layer 4: Trustability
Can the agent verify and trust the information?

#### Rule #6: First-Class Error Docs
- [ ] Every error code is documented
- [ ] Error triggers are explained
- [ ] Diagnosis steps are provided
- [ ] Resolution steps are detailed
- [ ] Retry safety is stated
- [ ] Related errors are linked

**Quick test:** Can a user recover from any error using only your docs?

#### Rule #7: Consistent Terminology
- [ ] One term per concept
- [ ] No synonyms used interchangeably
- [ ] Terminology is documented in a glossary
- [ ] New terms are defined on first use
- [ ] Terminology is consistent across all pages

**Quick test:** Would an AI be confused about whether two terms mean the same thing?

#### Rule #13: Version Clarity
- [ ] Version is stated on every page
- [ ] Last updated date is present
- [ ] Deprecation status is clear
- [ ] Migration paths are documented
- [ ] Outdated content has warnings
- [ ] Version history is available

**Quick test:** Can an AI determine if this information is current?

#### Rule #15: Safety & Limits
- [ ] Irreversible actions have warnings
- [ ] Billing implications are documented
- [ ] Rate limits are stated
- [ ] Quotas are documented
- [ ] Prerequisites before dangerous actions are listed
- [ ] Alternatives to dangerous actions are suggested

**Quick test:** Would an AI give safe advice based on this documentation?

#### Rule #16: No Anti-Patterns
- [ ] Marketing fluff is removed
- [ ] "Contact us" dead-ends are expanded
- [ ] Content is server-side rendered
- [ ] Images have text alternatives
- [ ] No critical content in JS-only widgets

**Quick test:** Can an AI crawler access all important content?

#### Rule #20: Callouts & Warnings
- [ ] Standard callout format is used
- [ ] Warnings are prominent
- [ ] Danger warnings are specific
- [ ] Tips provide actionable advice
- [ ] Notes add helpful context

**Quick test:** Are important warnings impossible to miss?

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
**Focus:** Quick wins that require minimal content changes

**Tasks:**
1. Add page metadata to all pages (Rule #8)
2. Fix obvious "see above" references (Rule #1)
3. Add version banners to all pages (Rule #13)
4. Remove marketing fluff (Rule #16)
5. Standardize callout formatting (Rule #20)

**Expected impact:** 20-30% improvement in agent-friendliness

### Phase 2: Structure (Week 3-4)
**Focus:** Structural improvements to content organization

**Tasks:**
1. Rewrite headings to be action-oriented (Rule #2)
2. Convert parameter descriptions to tables (Rule #3)
3. Add prerequisites to task pages (Rule #9)
4. Separate content types (Rule #12)
5. Add expected outcomes to tutorials (Rule #10)

**Expected impact:** 40-50% improvement in agent-friendliness

### Phase 3: Content (Week 5-6)
**Focus:** Content improvements requiring more extensive writing

**Tasks:**
1. Expand incomplete examples (Rule #4)
2. Document common errors (Rule #6)
3. Add comparison sections (Rule #14)
4. Document lifecycle states (Rule #19)
5. Add safety warnings (Rule #15)

**Expected impact:** 60-70% improvement in agent-friendliness

### Phase 4: Polish (Week 7-8)
**Focus:** Consistency and completeness

**Tasks:**
1. Implement consistent terminology (Rule #7)
2. Make all sections self-contained (Rule #1)
3. Add contextual cross-references (Rule #11)
4. Ensure explicit over implicit (Rule #5)
5. Add intent explanations (Rule #18)

**Expected impact:** 80-90% improvement in agent-friendliness

---

## Measuring Your Progress

### The Agent-Friendliness Score

Score your documentation on each rule (0-10), then calculate:

\`\`\`
Total Score = Σ(Rule Score × Weight)

Weights:
- Tier 1 (Rules 1, 2, 4, 5, 6, 7, 13): 6% each = 42%
- Tier 2 (Rules 3, 8, 9, 10, 11, 12, 17): 5% each = 35%
- Tier 3 (Rules 14, 15, 16, 18, 19, 20): 4% each = 23%
\`\`\`

**Score Interpretation:**
- 90-100: Excellent — AI agents will love your docs
- 70-89: Good — Solid foundation with room for improvement
- 50-69: Fair — Significant issues affecting AI usability
- Below 50: Poor — Major overhaul needed

### Automated Measurement Tools

**Retrieval Simulation:**
\`\`\`python
# Test if your content retrieves correctly for target queries
queries = [
    "How to authenticate with the API",
    "What are the rate limits",
    "How to handle 429 errors"
]

for query in queries:
    chunks = retrieve_chunks(query, your_docs)
    score = evaluate_answerability(query, chunks)
    print(f"{query}: {score}")
\`\`\`

**Self-Containment Check:**
\`\`\`python
# Check for context-dependent phrases
problematic_phrases = [
    "as mentioned above",
    "see the previous section",
    "as described earlier",
    "click here"
]

for doc in your_docs:
    for phrase in problematic_phrases:
        if phrase in doc.content:
            flag_for_review(doc, phrase)
\`\`\`

---

## Before and After: Complete Example

### Before: Traditional Documentation

\`\`\`markdown
# Authentication

Our API uses standard authentication methods. See the dashboard for your API key.

## API Keys

Include your key in the Authorization header.

\`\`\`bash
curl -H "Authorization: Bearer YOUR_KEY" https://api.example.com
\`\`\`

## OAuth

For production apps, use OAuth instead. Contact us for setup help.

## Errors

If authentication fails, you'll get a 401 error. Check your key and try again.
\`\`\`

**Problems:**
- Heading is topic-based, not action-oriented
- No metadata
- "See the dashboard" is vague
- "YOUR_KEY" is not explained
- "Contact us" is a dead-end
- Error documentation is minimal

### After: Agent-First Documentation

\`\`\`markdown
---
title: "How to Authenticate with the API"
description: "Complete guide to API authentication using API keys and OAuth 2.0, with examples and troubleshooting"
category: "Getting Started"
tags: ["authentication", "api keys", "oauth", "security"]
api_version: "v2"
last_updated: "2025-03-15"
---

# How to authenticate with the API

This guide covers authentication methods for the API. Choose the method that fits your use case:

- **API keys** — Best for server-to-server integrations and quick starts
- **OAuth 2.0** — Best for production applications acting on behalf of users

## Prerequisites

Before you begin, ensure you have:
- [ ] A valid API key ([get one here](/dashboard/api-keys))
- [ ] For OAuth: A registered application ([register here](/oauth/apps))

---

## How to authenticate with API keys

API key authentication is the simplest method. Use it when:
- You're building a server-side integration
- You need to get started quickly
- You don't need user-specific permissions

### Making authenticated requests

\`\`\`bash
export API_KEY="sk_live_xxxxxxxxxxxxx"

curl https://api.example.com/v1/users \\
  -H "Authorization: Bearer $API_KEY"
\`\`\`

### Authentication errors

#### 401 Unauthorized

**What it means:** Your API key is missing, invalid, or expired.

**How to fix:**
1. Check that you're including the \`Authorization\` header
2. Verify your API key is correct
3. Ensure you're using the correct key format (\`Bearer {key}\`)

#### 403 Forbidden

**What it means:** Your API key is valid but doesn't have permission for this action.

**How to fix:**
1. Check your key's permissions in the dashboard
2. Request additional scopes if needed
\`\`\`

**Improvements:**
- Action-oriented heading
- Complete metadata
- Clear prerequisites
- Self-contained sections
- Complete examples
- Comparison section
- Comprehensive error docs
- Security warnings
- Next steps

---

## Getting Started Today

1. **Audit your top pages** against this checklist
2. **Start with Phase 1** quick wins for immediate impact
3. **Measure your progress** using the scoring framework
4. **Iterate and improve** over the 8-week implementation plan

The AI economy is here. Documentation optimized for agents isn't just a nice-to-have—it's becoming essential for product discovery, adoption, and success.

**Ready to see how your documentation scores?** [Get your free agent-readiness score](/) and discover exactly which rules your documentation is violating.`,
  },
]

export function getPost(slug: string): BlogPost | undefined {
  return BLOG_POSTS.find((p) => p.slug === slug)
}
