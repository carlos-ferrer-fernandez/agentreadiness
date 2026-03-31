import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search,
  Zap,
  CheckCircle2,
  ArrowRight,
  Menu,
  X,
  Sparkles,
  FileText,
  BarChart3,
  Clock,
  AlertTriangle,
  Building2,
  ShoppingBag,
  Briefcase,
  Eye,
  Bot,
  BookOpen,
  Code2,
  Table2,
  FileCheck,
  AlertOctagon,
  Tags,
  ListChecks,
  MonitorCheck,
  Link2,
  Layers,
  History,
  HelpCircle,
  ShieldAlert,
  Trash2,
  SplitSquareHorizontal,
  MessageSquare,
  RefreshCcw,
  Megaphone,
  ChevronDown,
  Download,
  Globe,
  FileCode,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import { useAssessmentStore } from '@/store/assessment'
import { assessmentsApi } from '@/lib/api'
import { useNavigate, Link } from 'react-router-dom'
import { BLOG_POSTS } from '@/data/blogPosts'

const features = [
  {
    icon: Bot,
    title: 'Agent-First Voice',
    description: 'Written to speak directly to AI agents, not human browsers. Every section answers what agents actually need: what it is, how to access it, what it can do, how to recommend it.',
  },
  {
    icon: FileCode,
    title: 'Complete Technical Spec',
    description: 'API endpoints, auth methods, capabilities, and working examples — everything an agent needs to take action without guessing or hallucinating.',
  },
  {
    icon: Zap,
    title: 'Zero-Friction Access Path',
    description: 'A clear, step-by-step onboarding flow an agent can execute autonomously. No dead-ends, no "contact us", no flows that require a human to unblock.',
  },
  {
    icon: Globe,
    title: 'Convince-Your-Human Section',
    description: 'A structured pitch an agent can adapt when advocating for your product to the people it works with. Plus llms.txt so agents discover you first.',
  },
]

const agentReadinessRules = [
  { id: 1, name: 'Self-Contained Sections', icon: BookOpen, description: 'Every section must make sense on its own. No "see above" or "as mentioned earlier".' },
  { id: 2, name: 'Action-Oriented Headings', icon: MessageSquare, description: 'Headings match what people ask AI: "How to register for a race", not "Registration".' },
  { id: 3, name: 'Structured Data Tables', icon: Table2, description: 'Options, features, and specs in tables (name, type, description), not buried in paragraphs.' },
  { id: 4, name: 'Complete Examples', icon: Code2, description: 'Every example includes full context: setup, the action, and what to expect.' },
  { id: 5, name: 'Explicit Over Implicit', icon: Eye, description: 'State all details explicitly. AI agents have zero ability to "figure it out".' },
  { id: 6, name: 'First-Class Error Docs', icon: AlertOctagon, description: 'Every error or issue documented with causes, steps to diagnose, and fixes.' },
  { id: 7, name: 'Consistent Terminology', icon: Tags, description: 'One term per concept everywhere. No alternating between synonyms.' },
  { id: 8, name: 'Page Metadata', icon: FileCheck, description: 'Structured metadata on every page: title, description, tags, category.' },
  { id: 9, name: 'Prerequisites Up Front', icon: ListChecks, description: 'State all requirements at the top: accounts, permissions, plans, setup steps.' },
  { id: 10, name: 'Expected Outcomes', icon: MonitorCheck, description: 'Show what success looks like: expected results, confirmations, next steps.' },
  { id: 11, name: 'Contextual Cross-References', icon: Link2, description: 'Never "click here". Always describe what the linked page covers.' },
  { id: 12, name: 'Content Type Separation', icon: Layers, description: 'Separate explanations, step-by-step guides, and reference content clearly.' },
  { id: 13, name: 'Version Clarity', icon: History, description: 'Version or date stated prominently. Outdated content marked with alternatives.' },
  { id: 14, name: 'Comparison Sections', icon: HelpCircle, description: '"When to use X vs Y" sections so agents can answer comparison questions.' },
  { id: 15, name: 'Safety & Limits', icon: ShieldAlert, description: 'Irreversible actions, billing implications, and limits clearly documented.' },
  { id: 16, name: 'No Anti-Patterns', icon: Trash2, description: 'Strip marketing fluff, "contact us" dead-ends, and content hidden behind JS widgets.' },
  { id: 17, name: 'Retrieval-Optimized', icon: SplitSquareHorizontal, description: 'Sections scoped so AI can retrieve them independently with full context.' },
  { id: 18, name: 'Intent Before Mechanics', icon: Megaphone, description: 'Always explain WHY before HOW. Context before instructions.' },
  { id: 19, name: 'Lifecycle & Status', icon: RefreshCcw, description: 'Document processes as flows: pending, active, completed, cancelled.' },
  { id: 20, name: 'Callouts & Warnings', icon: AlertTriangle, description: 'Standard callout format for warnings, tips, and important notes that AI can prioritize.' },
]

const assessmentStages = [
  { name: 'Discovering pages', icon: Search },
  { name: 'Reading your content', icon: FileText },
  { name: 'Checking if sections stand alone', icon: BookOpen },
  { name: 'Evaluating examples and guides', icon: Code2 },
  { name: 'Analyzing heading structure', icon: MessageSquare },
  { name: 'Checking data tables', icon: Table2 },
  { name: 'Scanning for anti-patterns', icon: Trash2 },
  { name: 'Testing AI retrieval quality', icon: SplitSquareHorizontal },
  { name: 'Verifying error documentation', icon: AlertOctagon },
  { name: 'Running 20-rule evaluation', icon: ListChecks },
  { name: 'Calculating your score', icon: BarChart3 },
]

const liveStatusMessages = [
  'Simulating how Claude reads your content...',
  'Checking if GPT can find your key pages...',
  'Testing if AI can understand your sections independently...',
  'Verifying examples are complete and actionable...',
  'Scanning for vague cross-references...',
  'Checking terminology consistency across pages...',
  'Evaluating page metadata and structure...',
  'Testing if headings match what users ask AI...',
  'Looking for missing expected outcomes...',
  'Checking if limits and warnings are documented...',
  'Analyzing content organization...',
  'Almost there, finalizing your score...',
]


// FAQ Accordion Item
function FaqItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="border-b border-border last:border-0">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center justify-between w-full py-5 text-left group"
      >
        <span className="font-medium text-[15px] pr-4 group-hover:text-primary transition-colors">{q}</span>
        <ChevronDown className={cn("w-5 h-5 text-muted-foreground flex-shrink-0 transition-transform", open && "rotate-180")} />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <p className="text-sm text-muted-foreground pb-5 leading-relaxed">{a}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

type CompanyKey = 'algolia' | 'loops' | 'webflow' | 'linear' | 'segment'

const DEMO_COMPANIES: Record<CompanyKey, {
  name: string
  domain: string
  url: string
  page: string
  scoreBefore: number
  scoreAfter: number
  before: React.ReactNode
  after: React.ReactNode
}> = {
  algolia: {
    name: 'Algolia',
    domain: 'algolia.com',
    url: 'algolia.com/doc/api-reference/api-methods/save-objects',
    page: 'Add Records to Index',
    scoreBefore: 41,
    scoreAfter: 93,
    before: (
      <div className="space-y-3">
        <h2 className="text-slate-200 text-base font-semibold font-serif">Add or Update Records</h2>
        <p className="text-slate-400 text-xs leading-relaxed">
          To add records to your Algolia index you can use the <code className="text-slate-300">saveObjects</code> method which takes an array of objects. Each object in the array can optionally have an objectID field. If an objectID is provided, Algolia will use it as the unique identifier for that record. If no objectID is provided, Algolia will automatically generate one for you. Note that if a record with the same objectID already exists, it will be completely replaced with the new data. The method returns a task object that contains a taskID which you can use to check if the operation has been completed using the waitTask method before querying the newly indexed data.
        </p>
        <p className="text-slate-400 text-xs leading-relaxed">
          You can also use <code className="text-slate-300">partialUpdateObjects</code> if you only want to update specific fields without replacing the whole record. This is useful when your records are large and you only need to change one or two attributes. There are also batch methods available.
        </p>
      </div>
    ),
    after: (
      <div className="space-y-2.5">
        <div className="flex items-center gap-2">
          <h2 className="text-slate-200 text-base font-semibold font-serif">Add Records to Index</h2>
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-forest/20 border border-forest/30 text-forest">POST</span>
        </div>
        <p className="text-slate-400 text-[11px] leading-relaxed">
          <span className="text-amber-400 font-medium">Agent context:</span> Indexes new records or replaces existing ones by <code className="text-slate-300">objectID</code>. Use <code className="text-slate-300">partialUpdateObjects</code> to update specific fields only. Indexed records appear in search within ~1 second.
        </p>
        <div className="border border-white/10 rounded overflow-hidden text-[11px]">
          <div className="grid grid-cols-3 bg-slate-900 px-3 py-1.5 gap-2">
            <span className="text-slate-400 font-medium">Parameter</span>
            <span className="text-slate-400 font-medium">Type</span>
            <span className="text-slate-400 font-medium">Description</span>
          </div>
          {[
            ['objectID', 'string', 'Optional. Auto-generated if omitted. Existing record with same ID is replaced.'],
            ['[your fields]', 'any', 'Attributes to index. All fields are searchable by default.'],
          ].map(([p, t, d], i) => (
            <div key={i} className="grid grid-cols-3 px-3 py-1.5 gap-2 border-t border-white/10">
              <span className="text-blue-400 font-mono">{p}</span>
              <span className="text-slate-400">{t}</span>
              <span className="text-slate-500">{d}</span>
            </div>
          ))}
        </div>
        <div className="bg-slate-900 border border-white/10 rounded p-2">
          <pre className="text-[11px] text-slate-300 font-mono">{`client.save_objects("products", [
  {"objectID": "p1", "name": "Widget", "price": 9.99}
])`}</pre>
        </div>
      </div>
    ),
  },
  loops: {
    name: 'Loops',
    domain: 'loops.so',
    url: 'loops.so/docs/api-reference/send-event',
    page: 'Send a Transactional Email',
    scoreBefore: 48,
    scoreAfter: 94,
    before: (
      <div className="space-y-3">
        <h2 className="text-slate-200 text-base font-semibold font-serif">Sending Transactional Emails</h2>
        <p className="text-slate-400 text-xs leading-relaxed">
          Loops lets you send transactional emails to your users. You can use the transactional endpoint to do this. You need to create a transactional email in the Loops dashboard first, then you can send it via the API. You'll need the transactional email ID from the dashboard. You also need to provide the email address you want to send to. You can optionally provide data variables that will be used to fill in any dynamic content in the email template.
        </p>
        <p className="text-slate-400 text-xs leading-relaxed">
          Make sure you've set up your sending domain before using this. If the email address you're sending to has unsubscribed, the email won't be delivered. The API will return a success response either way.
        </p>
      </div>
    ),
    after: (
      <div className="space-y-2.5">
        <div className="flex items-center gap-2">
          <h2 className="text-slate-200 text-base font-semibold font-serif">Send a Transactional Email</h2>
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-forest/20 border border-forest/30 text-forest">POST</span>
        </div>
        <p className="text-slate-400 text-[11px] leading-relaxed">
          <span className="text-amber-400 font-medium">Agent context:</span> Sends a single email to one recipient using a pre-built template. Bypasses unsubscribes only if <code className="text-slate-300">addToAudience: false</code>. Requires a verified sending domain.
        </p>
        <div className="border border-white/10 rounded overflow-hidden text-[11px]">
          <div className="grid grid-cols-3 bg-slate-900 px-3 py-1.5 gap-2">
            <span className="text-slate-400 font-medium">Parameter</span>
            <span className="text-slate-400 font-medium">Req.</span>
            <span className="text-slate-400 font-medium">Description</span>
          </div>
          {[
            ['transactionalId', '✓', 'ID of the email template from Loops dashboard'],
            ['email', '✓', "Recipient's email address"],
            ['dataVariables', '–', 'Object of template variables, e.g. { name: "Sarah" }'],
            ['addToAudience', '–', 'Default true. Set false to skip unsubscribe check'],
          ].map(([p, r, d], i) => (
            <div key={i} className="grid grid-cols-3 px-3 py-1.5 gap-2 border-t border-white/10">
              <span className="text-blue-400 font-mono">{p}</span>
              <span className={r === '✓' ? 'text-green-400' : 'text-slate-500'}>{r}</span>
              <span className="text-slate-500">{d}</span>
            </div>
          ))}
        </div>
      </div>
    ),
  },
  webflow: {
    name: 'Webflow',
    domain: 'webflow.com',
    url: 'developers.webflow.com/reference/create-item',
    page: 'Create a CMS Collection Item',
    scoreBefore: 44,
    scoreAfter: 91,
    before: (
      <div className="space-y-3">
        <h2 className="text-slate-200 text-base font-semibold font-serif">Create Item</h2>
        <p className="text-slate-400 text-xs leading-relaxed">
          You can create new items in a CMS Collection using the API. To do this, you'll need to make a POST request to the collections endpoint with the collection ID. In the request body, you need to provide the fields for the item. The fields you need to provide depend on the Collection's schema which you can get from the collection endpoint. Items are created as drafts by default, so you'll need to publish them separately if you want them to appear on the site. Some fields are required depending on how the collection was set up. The response will include the newly created item's ID.
        </p>
        <p className="text-slate-400 text-xs leading-relaxed">
          There's also a bulk create endpoint if you need to create multiple items at once. Rate limits apply — check the headers in the response.
        </p>
      </div>
    ),
    after: (
      <div className="space-y-2.5">
        <div className="flex items-center gap-2">
          <h2 className="text-slate-200 text-base font-semibold font-serif">Create a CMS Item</h2>
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-forest/20 border border-forest/30 text-forest">POST</span>
        </div>
        <p className="text-slate-400 text-[11px] leading-relaxed">
          <span className="text-amber-400 font-medium">Agent context:</span> Creates a draft CMS item in the given collection. <strong className="text-slate-300">Items do not appear on the live site until published.</strong> Get the field schema first: <code className="text-slate-300">GET /collections/{"{collectionId}"}</code>.
        </p>
        <div className="border border-white/10 rounded overflow-hidden text-[11px]">
          <div className="grid grid-cols-3 bg-slate-900 px-3 py-1.5 gap-2">
            <span className="text-slate-400 font-medium">Parameter</span>
            <span className="text-slate-400 font-medium">Req.</span>
            <span className="text-slate-400 font-medium">Description</span>
          </div>
          {[
            ['collectionId', '✓', 'CMS Collection ID from the Webflow dashboard'],
            ['fieldData.name', '✓', 'Item name (slug auto-generated from this)'],
            ['fieldData.slug', '–', 'URL slug. Auto-generated if omitted. Must be unique.'],
            ['isDraft', '–', 'Default true. Set false to publish immediately.'],
          ].map(([p, r, d], i) => (
            <div key={i} className="grid grid-cols-3 px-3 py-1.5 gap-2 border-t border-white/10">
              <span className="text-blue-400 font-mono">{p}</span>
              <span className={r === '✓' ? 'text-green-400' : 'text-slate-500'}>{r}</span>
              <span className="text-slate-500">{d}</span>
            </div>
          ))}
        </div>
      </div>
    ),
  },
  linear: {
    name: 'Linear',
    domain: 'linear.app',
    url: 'developers.linear.app/reference/create-issue',
    page: 'Create an Issue',
    scoreBefore: 45,
    scoreAfter: 92,
    before: (
      <div className="space-y-3">
        <h2 className="text-slate-200 text-base font-semibold font-serif">Creating Issues</h2>
        <p className="text-slate-400 text-xs leading-relaxed">
          To create an issue in Linear, you use the GraphQL API. You need to provide the team ID which you can get by querying the teams endpoint. Issues need a title. You can optionally provide a description in markdown format. Priority is represented as a number from 0 to 4 where 0 means no priority, 1 is urgent, 2 is high, 3 is medium, and 4 is low. You can assign the issue to a user by providing their user ID. If you want to set the status, you need to provide the state ID, which you can get by querying available workflow states for that team.
        </p>
      </div>
    ),
    after: (
      <div className="space-y-2.5">
        <div className="flex items-center gap-2">
          <h2 className="text-slate-200 text-base font-semibold font-serif">Create an Issue</h2>
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-violet-500/20 border border-violet-500/30 text-violet-400">MUTATION</span>
        </div>
        <p className="text-slate-400 text-[11px] leading-relaxed">
          <span className="text-amber-400 font-medium">Agent context:</span> Creates an issue in the specified team. Priority: 0=none, 1=urgent, 2=high, 3=medium, 4=low. Get <code className="text-slate-300">teamId</code> via <code className="text-slate-300">teams {"{ id name }"}</code> query first.
        </p>
        <div className="border border-white/10 rounded overflow-hidden text-[11px]">
          <div className="grid grid-cols-3 bg-slate-900 px-3 py-1.5 gap-2">
            <span className="text-slate-400 font-medium">Parameter</span>
            <span className="text-slate-400 font-medium">Req.</span>
            <span className="text-slate-400 font-medium">Description</span>
          </div>
          {[
            ['teamId', '✓', 'Team to create the issue in'],
            ['title', '✓', 'Issue title (markdown supported)'],
            ['description', '–', 'Issue body in markdown'],
            ['priority', '–', '0–4. Default: 0 (none)'],
            ['stateId', '–', 'Workflow state. Defaults to first "Todo" state'],
          ].map(([p, r, d], i) => (
            <div key={i} className="grid grid-cols-3 px-3 py-1.5 gap-2 border-t border-white/10">
              <span className="text-blue-400 font-mono">{p}</span>
              <span className={r === '✓' ? 'text-green-400' : 'text-slate-500'}>{r}</span>
              <span className="text-slate-500">{d}</span>
            </div>
          ))}
        </div>
      </div>
    ),
  },
  segment: {
    name: 'Segment',
    domain: 'segment.com',
    url: 'segment.com/docs/connections/spec/track',
    page: 'Track a User Event',
    scoreBefore: 39,
    scoreAfter: 91,
    before: (
      <div className="space-y-3">
        <h2 className="text-slate-200 text-base font-semibold font-serif">Track</h2>
        <p className="text-slate-400 text-xs leading-relaxed">
          The track call lets you record any actions your users perform, along with any properties that describe the action. Each action is known as an event, and each event has a name. You need to either pass a userId or an anonymousId. The anonymousId is useful for tracking before a user logs in. You can pass a properties object with any data you want to capture about the event. You can also pass a context object and a timestamp if you want to record when the event happened.
        </p>
      </div>
    ),
    after: (
      <div className="space-y-2.5">
        <div className="flex items-center gap-2">
          <h2 className="text-slate-200 text-base font-semibold font-serif">Track a User Event</h2>
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-forest/20 border border-forest/30 text-forest">POST</span>
        </div>
        <p className="text-slate-400 text-[11px] leading-relaxed">
          <span className="text-amber-400 font-medium">Agent context:</span> Records a user action. Requires <code className="text-slate-300">userId</code> (identified) or <code className="text-slate-300">anonymousId</code> (pre-login). Event names should be past-tense: "Order Completed", "Item Added".
        </p>
        <div className="border border-white/10 rounded overflow-hidden text-[11px]">
          <div className="grid grid-cols-3 bg-slate-900 px-3 py-1.5 gap-2">
            <span className="text-slate-400 font-medium">Parameter</span>
            <span className="text-slate-400 font-medium">Req.</span>
            <span className="text-slate-400 font-medium">Description</span>
          </div>
          {[
            ['event', '✓', 'Event name. Past-tense verb: "Order Completed"'],
            ['userId', '✓*', 'Identified user. Required unless anonymousId set'],
            ['anonymousId', '✓*', 'Pre-login visitor. Required unless userId set'],
            ['properties', '–', 'Event data: { revenue: 9.99, sku: "abc" }'],
          ].map(([p, r, d], i) => (
            <div key={i} className="grid grid-cols-3 px-3 py-1.5 gap-2 border-t border-white/10">
              <span className="text-blue-400 font-mono">{p}</span>
              <span className={r.startsWith('✓') ? 'text-green-400' : 'text-slate-500'}>{r}</span>
              <span className="text-slate-500">{d}</span>
            </div>
          ))}
        </div>
      </div>
    ),
  },
}

function HeroProductDemo() {
  const [company, setCompany] = useState<CompanyKey>('algolia')
  const [tab, setTab] = useState<'before' | 'after'>('before')

  const data = DEMO_COMPANIES[company]

  const handleCompany = (c: CompanyKey) => {
    setCompany(c)
    setTab('before')
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.6, delay: 0.4 }}
      className="hidden lg:flex flex-col gap-3 pt-2"
    >
      {/* Company selector */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-xs text-slate-500 mr-1">Examples:</span>
        {(Object.keys(DEMO_COMPANIES) as CompanyKey[]).map(key => (
          <button
            key={key}
            onClick={() => handleCompany(key)}
            className={cn(
              "flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-colors border",
              company === key
                ? "bg-white/10 text-white border-white/20"
                : "text-slate-500 border-transparent hover:text-slate-300 hover:border-white/10"
            )}
          >
            <img
              src={`https://logo.clearbit.com/${DEMO_COMPANIES[key].domain}`}
              alt={DEMO_COMPANIES[key].name}
              className="w-3.5 h-3.5 rounded-sm"
              onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
            />
            {DEMO_COMPANIES[key].name}
          </button>
        ))}
      </div>

      {/* Browser chrome */}
      <div className="rounded-xl border border-white/10 overflow-hidden shadow-2xl shadow-black/40">
        {/* URL bar */}
        <div className="bg-slate-900 border-b border-white/10 px-4 py-2.5 flex items-center gap-3">
          <div className="flex gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-slate-700" />
            <div className="w-2.5 h-2.5 rounded-full bg-slate-700" />
            <div className="w-2.5 h-2.5 rounded-full bg-slate-700" />
          </div>
          <AnimatePresence mode="wait">
            <motion.div
              key={company}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
              className="flex-1 bg-slate-800 rounded-md px-3 py-1 text-xs text-slate-500 font-mono truncate"
            >
              {data.url}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Before/After toggle */}
        <div className="bg-slate-900 border-b border-white/10 px-4 py-2 flex items-center justify-between">
          <div className="flex gap-1">
            <button
              onClick={() => setTab('before')}
              className={cn(
                "px-3 py-1 rounded text-xs font-medium transition-colors",
                tab === 'before'
                  ? "bg-red-900/40 text-red-300 border border-red-800/40"
                  : "text-slate-500 hover:text-slate-400"
              )}
            >
              Before
            </button>
            <button
              onClick={() => setTab('after')}
              className={cn(
                "px-3 py-1 rounded text-xs font-medium transition-colors",
                tab === 'after'
                  ? "bg-forest/20 text-forest border border-forest/30"
                  : "text-slate-500 hover:text-slate-400"
              )}
            >
              After GrounDocs
            </button>
          </div>
          <div className="flex items-center gap-2 text-[11px]">
            {tab === 'before' ? (
              <span className="text-red-400 font-medium">{data.scoreBefore}/100</span>
            ) : (
              <span className="text-forest font-medium">{data.scoreAfter}/100</span>
            )}
          </div>
        </div>

        {/* Content area — fixed height */}
        <div className="bg-slate-950 p-4 h-[280px] overflow-hidden">
          <AnimatePresence mode="wait">
            <motion.div
              key={`${company}-${tab}`}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              transition={{ duration: 0.18 }}
            >
              {tab === 'before' ? data.before : data.after}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>

      {/* Score delta + CTA */}
      <div className="flex items-center justify-between text-xs text-slate-500">
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1.5">
            <span className="inline-block w-2 h-2 rounded-full bg-red-500/60" />
            Before: {data.scoreBefore}/100
          </span>
          <ArrowRight className="w-3 h-3 text-slate-600" />
          <span className="flex items-center gap-1.5 text-forest">
            <span className="inline-block w-2 h-2 rounded-full bg-forest" />
            After: {data.scoreAfter}/100
          </span>
        </div>
        <button
          onClick={() => setTab(tab === 'before' ? 'after' : 'before')}
          className="text-slate-500 hover:text-slate-300 transition-colors"
        >
          {tab === 'before' ? 'See optimized →' : '← See original'}
        </button>
      </div>
    </motion.div>
  )
}

function BeforeAfterSlideshow() {
  const [company, setCompany] = useState<CompanyKey>('algolia')
  const data = DEMO_COMPANIES[company]

  return (
    <div>
      {/* Company logo selector */}
      <div className="flex flex-wrap items-center justify-center gap-2 mb-8">
        {(Object.keys(DEMO_COMPANIES) as CompanyKey[]).map(key => (
          <button
            key={key}
            onClick={() => setCompany(key)}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-colors border',
              company === key
                ? 'bg-white/10 text-white border-white/20'
                : 'text-slate-400 border-white/10 hover:text-slate-300 hover:border-white/20'
            )}
          >
            <img
              src={`https://logo.clearbit.com/${DEMO_COMPANIES[key].domain}`}
              alt={DEMO_COMPANIES[key].name}
              className="w-4 h-4 rounded-sm"
              onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
            />
            {DEMO_COMPANIES[key].name}
          </button>
        ))}
      </div>

      {/* Side-by-side before / after */}
      <AnimatePresence mode="wait">
        <motion.div
          key={company}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.25 }}
        >
          <div className="grid md:grid-cols-2 gap-4">
            {/* Before */}
            <div className="rounded-xl border border-red-500/20 bg-slate-900/60 overflow-hidden">
              <div className="flex items-center justify-between px-4 py-2.5 bg-red-500/10 border-b border-red-500/20">
                <span className="text-xs text-red-400 font-medium tracking-wide">BEFORE</span>
                <span className="text-xs text-slate-500">Score: {data.scoreBefore}/100</span>
              </div>
              <div className="p-4 min-h-[220px]">{data.before}</div>
            </div>

            {/* After */}
            <div className="rounded-xl border border-emerald-500/20 bg-slate-900/60 overflow-hidden">
              <div className="flex items-center justify-between px-4 py-2.5 bg-emerald-500/10 border-b border-emerald-500/20">
                <span className="text-xs text-emerald-400 font-medium tracking-wide">AFTER GROUNDOCS</span>
                <span className="text-xs text-forest font-medium">Score: {data.scoreAfter}/100</span>
              </div>
              <div className="p-4 min-h-[220px]">{data.after}</div>
            </div>
          </div>

          <div className="flex items-center justify-between mt-4 text-xs text-slate-500">
            <span>
              <span className="text-slate-300 font-medium">{data.name}</span>
              {' — '}{data.page}
            </span>
            <a
              href={`https://${data.url}`}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-slate-300 transition-colors"
            >
              View original ↗
            </a>
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  )
}

export function LandingPage() {
  const navigate = useNavigate()
  const [url, setUrl] = useState('')
  const [email, setEmail] = useState('')
  const [fullName, setFullName] = useState('')
  const [role, setRole] = useState('')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [liveMessage, setLiveMessage] = useState(0)

  const {
    isAssessing,
    assessmentStage,
    startAssessment,
    setAssessmentResult,
    setAssessmentError,
  } = useAssessmentStore()

  const handleAnalyze = useCallback(async () => {
    if (!url || isAssessing) return
    setError(null)

    if (!email || !email.includes('@') || !email.includes('.')) {
      setError('Please enter a valid work email')
      return
    }

    let validatedUrl = url
    if (!url.startsWith('http')) {
      validatedUrl = `https://${url}`
    }

    try {
      new URL(validatedUrl)
    } catch {
      setError('Please enter a valid URL')
      return
    }

    startAssessment()
    setLiveMessage(0)

    const stageInterval = setInterval(() => {
      useAssessmentStore.setState((state) => ({
        assessmentStage: Math.min(state.assessmentStage + 1, assessmentStages.length - 1),
      }))
    }, 4000)

    const messageInterval = setInterval(() => {
      setLiveMessage((prev) => (prev + 1) % liveStatusMessages.length)
    }, 3000)

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 120000)

    try {
      const response = await assessmentsApi.analyze({
        url: validatedUrl,
        email,
        full_name: fullName || undefined,
        role: role || undefined,
      }, controller.signal)

      const data = response.data
      setAssessmentResult({
        id: data.id,
        url: data.url,
        siteName: data.site_name,
        score: data.score,
        grade: data.grade,
        components: data.components || {},
        ruleResults: (data.rule_results || []).map((r: any) => ({
          rule_id: r.rule_id,
          name: r.name,
          short_name: r.short_name,
          category: r.category,
          score: r.score,
          status: r.status,
          finding: r.finding,
          pages_checked: r.pages_checked,
          pages_passing: r.pages_passing,
        })),
        queryCount: data.query_count,
        passRate: data.pass_rate,
        avgLatencyMs: data.avg_latency_ms,
        pageCount: data.page_count,
        topIssues: data.top_issues.map((issue: any) => ({
          category: issue.category,
          title: issue.title,
          severity: issue.severity as 'high' | 'medium' | 'low',
          rule_id: issue.rule_id,
          score: issue.score,
        })),
        estimatedPriceEur: data.estimated_price_eur,
        hasPaid: data.has_paid,
        optimizationStatus: data.optimization_status || null,
        optimizationProgress: data.optimization_progress || 0,
        optimizationStage: data.optimization_stage || null,
        optimizationMetadata: data.optimization_metadata || null,
        createdAt: data.created_at,
      })

      navigate('/assessment')
    } catch (err: any) {
      let message: string
      if (err.name === 'AbortError' || err.code === 'ERR_CANCELED') {
        message = 'Scan is taking longer than expected. Try a more specific URL — for example, https://docs.stripe.com/payments instead of https://docs.stripe.com/.'
      } else if (err.response?.status === 408) {
        message = err.response?.data?.detail || 'Scan timed out. Try a more specific section URL rather than the top-level docs root.'
      } else if (err.response?.status === 400) {
        message = err.response?.data?.detail || 'We couldn\'t reach this URL. Please check it\'s publicly accessible and try again.'
      } else {
        message = err.response?.data?.detail || 'Analysis failed. Please check the URL and try again.'
      }
      setAssessmentError(message)
      setError(message)
    } finally {
      clearTimeout(timeoutId)
      clearInterval(stageInterval)
      clearInterval(messageInterval)
    }
  }, [url, email, fullName, role, isAssessing, startAssessment, setAssessmentResult, setAssessmentError, navigate, setLiveMessage])

  const scrollToAssessment = () => {
    document.getElementById('assessment')?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation - Mintlify-inspired clean nav */}
      <nav className="border-b bg-background/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-14 items-center">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 bg-forest rounded-lg flex items-center justify-center">
                <Zap className="w-4 h-4 text-white" />
              </div>
              <span className="text-lg font-semibold tracking-tight">GrounDocs</span>
            </div>

            <div className="hidden md:flex items-center gap-1">
              <a href="#how-it-works" className="text-sm text-muted-foreground hover:text-foreground transition-colors px-3 py-2 rounded-md hover:bg-muted">
                How it Works
              </a>
              <a href="#rules" className="text-sm text-muted-foreground hover:text-foreground transition-colors px-3 py-2 rounded-md hover:bg-muted">
                20 Rules
              </a>
              <a href="#pricing" className="text-sm text-muted-foreground hover:text-foreground transition-colors px-3 py-2 rounded-md hover:bg-muted">
                Pricing
              </a>
              <a href="#faq" className="text-sm text-muted-foreground hover:text-foreground transition-colors px-3 py-2 rounded-md hover:bg-muted">
                FAQ
              </a>
              <Link to="/blog" className="text-sm text-muted-foreground hover:text-foreground transition-colors px-3 py-2 rounded-md hover:bg-muted">
                Blog
              </Link>
              <a href="/support" className="text-sm text-muted-foreground hover:text-foreground transition-colors px-3 py-2 rounded-md hover:bg-muted">
                Support
              </a>
              <div className="w-px h-5 bg-border mx-2" />
              <Button size="sm" className="bg-forest hover:bg-forest-hover text-white" onClick={scrollToAssessment}>
                Get Free Scan
              </Button>
            </div>

            <button
              className="md:hidden p-2"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="md:hidden border-t bg-background"
            >
              <div className="px-4 py-4 space-y-1">
                <a href="#how-it-works" className="block text-sm text-muted-foreground px-3 py-2 rounded-md hover:bg-muted">How it Works</a>
                <a href="#rules" className="block text-sm text-muted-foreground px-3 py-2 rounded-md hover:bg-muted">20 Rules</a>
                <a href="#pricing" className="block text-sm text-muted-foreground px-3 py-2 rounded-md hover:bg-muted">Pricing</a>
                <a href="#faq" className="block text-sm text-muted-foreground px-3 py-2 rounded-md hover:bg-muted">FAQ</a>
                <Link to="/blog" className="block text-sm text-muted-foreground px-3 py-2 rounded-md hover:bg-muted">Blog</Link>
                <a href="/support" className="block text-sm text-muted-foreground px-3 py-2 rounded-md hover:bg-muted">Support</a>
                <Button size="sm" className="w-full mt-2 bg-forest hover:bg-forest-hover text-white" onClick={scrollToAssessment}>
                  Get Free Scan
                </Button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden border-b border-border/40 bg-slate-950">
        {/* Subtle depth gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-slate-950 to-black -z-10" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(47,79,47,0.15),_transparent_60%)] -z-10" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16 lg:pt-24 lg:pb-20">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-start">

            {/* Left column — headline + form */}
            <div>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
              >
                <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-forest/10 border border-forest/20 text-forest text-sm font-medium mb-8">
                  <Sparkles className="w-3.5 h-3.5" />
                  One page. Agent-optimized by default.
                </span>
              </motion.div>

              <motion.h1
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.1 }}
                className="font-serif text-4xl md:text-5xl lg:text-[3.25rem] tracking-[-0.01em] leading-[1.1] mb-6 text-white"
              >
                Give AI agents a{' '}
                <span className="text-forest">
                  dedicated front door to your product
                </span>
              </motion.h1>

              <motion.p
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.2 }}
                className="text-lg text-slate-400 mb-8 leading-relaxed"
              >
                Most products send AI agents to a marketing site built for humans.
                We build your <code className="text-forest font-mono text-base">/agents</code> page — one dedicated, machine-readable page that tells agents
                exactly what your product is, how to access it, and how to recommend it.
              </motion.p>

              {/* Browse examples link */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.25 }}
                className="mb-6"
              >
                <Link
                  to="/showcase"
                  className="inline-flex items-center gap-1.5 text-sm text-slate-400 hover:text-forest transition-colors"
                >
                  <Eye className="w-3.5 h-3.5" />
                  See example /agents pages →
                </Link>
              </motion.div>

              {/* Assessment Form */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.3 }}
                id="assessment"
                className="max-w-xl"
              >
              <div className="bg-card border rounded-2xl p-6 shadow-xl shadow-black/5">
                <div className="space-y-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                    <Input
                      type="text"
                      placeholder="Enter your product URL (e.g., example.com, docs.example.com)"
                      value={url}
                      onChange={(e) => { setUrl(e.target.value); setError(null) }}
                      className="pl-10 h-12 text-base rounded-xl border-border/60 focus:border-forest focus:ring-forest/20"
                      onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
                      disabled={isAssessing}
                    />
                  </div>

                  <AnimatePresence>
                    {url.length > 3 && !isAssessing && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="space-y-3"
                      >
                        <div className="pt-2 border-t">
                          <p className="text-xs text-muted-foreground mb-3">
                            We'll send your free agent readiness report to this email
                          </p>
                          <Input
                            type="email"
                            placeholder="Work email *"
                            value={email}
                            onChange={(e) => { setEmail(e.target.value); setError(null) }}
                            className="h-10 text-sm rounded-lg"
                            onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <Input
                            type="text"
                            placeholder="Full name"
                            value={fullName}
                            onChange={(e) => setFullName(e.target.value)}
                            className="h-10 text-sm rounded-lg"
                          />
                          <Input
                            type="text"
                            placeholder="Role (e.g. CEO, Product, Marketing)"
                            value={role}
                            onChange={(e) => setRole(e.target.value)}
                            className="h-10 text-sm rounded-lg"
                          />
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {error && (
                    <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700">
                      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                      <span>{error}</span>
                    </div>
                  )}

                  <Button
                    size="lg"
                    onClick={handleAnalyze}
                    disabled={isAssessing || !url || !email || !email.includes('@') || !email.includes('.')}
                    className="w-full rounded-xl bg-forest hover:bg-forest-hover text-white h-12"
                  >
                    {isAssessing ? (
                      <>
                        <Clock className="mr-2 w-4 h-4 animate-spin" />
                        Scanning...
                      </>
                    ) : (
                      <>
                        Check Agent Readiness — Free
                        <ArrowRight className="ml-2 w-4 h-4" />
                      </>
                    )}
                  </Button>
                </div>

                {/* Assessment Progress */}
                <AnimatePresence>
                  {isAssessing && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="mt-6 pt-6 border-t"
                    >
                      <div className="space-y-4">
                        {assessmentStages.map((stage, index) => {
                          const StageIcon = stage.icon
                          const isActive = index === assessmentStage
                          const isComplete = index < assessmentStage

                          return (
                            <div
                              key={stage.name}
                              className={cn(
                                "flex items-center gap-3 transition-opacity",
                                isActive ? "opacity-100" : isComplete ? "opacity-60" : "opacity-30"
                              )}
                            >
                              <div className={cn(
                                "w-8 h-8 rounded-full flex items-center justify-center",
                                isComplete ? "bg-forest-light" : isActive ? "bg-forest-light/50" : "bg-muted"
                              )}>
                                {isComplete ? (
                                  <CheckCircle2 className="w-4 h-4 text-forest" />
                                ) : (
                                  <StageIcon className={cn(
                                    "w-4 h-4",
                                    isActive ? "text-forest" : "text-muted-foreground"
                                  )} />
                                )}
                              </div>
                              <span className={cn(
                                "text-sm",
                                isActive ? "font-medium" : ""
                              )}>
                                {stage.name}
                              </span>
                              {isActive && (
                                <motion.div
                                  className="ml-auto w-4 h-4 border-2 border-forest border-t-transparent rounded-full"
                                  animate={{ rotate: 360 }}
                                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                                />
                              )}
                            </div>
                          )
                        })}
                      </div>

                      <div className="mt-4">
                        <Progress
                          value={((assessmentStage + 1) / assessmentStages.length) * 100}
                          className="h-2"
                        />
                        <AnimatePresence mode="wait">
                          <motion.p
                            key={liveMessage}
                            initial={{ opacity: 0, y: 6 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -6 }}
                            transition={{ duration: 0.3 }}
                            className="text-xs text-muted-foreground text-center mt-2"
                          >
                            {liveStatusMessages[liveMessage]}
                          </motion.p>
                        </AnimatePresence>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              <div className="flex items-center gap-6 mt-5 text-xs text-slate-500">
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-forest" />
                  Free analysis
                </span>
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-forest" />
                  60-second scan
                </span>
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-forest" />
                  One deployable page
                </span>
              </div>
            </motion.div>
            </div>

            {/* Right column — before/after product demo */}
            <HeroProductDemo />

          </div>
        </div>
      </section>

      {/* Social Proof / Logo Bar - Mintlify-inspired */}
      <section className="py-12 border-y bg-muted/30">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-xs font-medium text-muted-foreground uppercase tracking-wider mb-6">
            Built on research from 8 major AI agents
          </p>
          <div className="flex flex-wrap items-center justify-center gap-x-10 gap-y-4">
            {['Claude', 'GPT', 'Gemini', 'Grok', 'Kimi', 'Deepseek', 'Manus', 'Perplexity'].map((name) => (
              <span key={name} className="text-sm font-medium text-muted-foreground/60 hover:text-muted-foreground transition-colors">
                {name}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* The Problem - Context setter */}
      <section className="py-20 lg:py-24">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
            >
              <Badge variant="outline" className="mb-6 text-xs">The missing piece</Badge>
              <h2 className="font-serif text-3xl md:text-4xl tracking-[-0.01em] mb-6">
                Most products don't have a front door for AI agents
              </h2>
              <p className="text-lg text-muted-foreground leading-relaxed mb-4">
                When an AI agent needs to understand your product — to recommend it, help a user set it up, or integrate it —
                it has nowhere to go. There's no dedicated page that speaks its language, explains your access model,
                or tells it what your product can actually do.
              </p>
              <p className="text-lg text-muted-foreground leading-relaxed">
                So agents improvise from your marketing copy, your FAQs, and your docs. They hallucinate API details.
                They hit human-only flows and give up. Or they recommend a competitor whose product they can actually understand.
                The companies that fix this first win. The rest become invisible to the fastest-growing discovery channel.
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Who it's for */}
      <section className="py-16 lg:py-20 border-y bg-muted/20">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-2xl mb-12">
            <Badge variant="outline" className="mb-4 text-xs">Who needs an /agents page</Badge>
            <h2 className="font-serif text-3xl md:text-4xl tracking-[-0.01em] mb-4">
              Any product AI agents encounter
            </h2>
            <p className="text-muted-foreground text-lg">
              If an AI agent might recommend, integrate, or help a user set up your product — you need an /agents page.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {[
              {
                icon: Code2,
                title: 'Developer Tools & APIs',
                example: 'Your API, SDK, or integration is how agents do the work',
                ask: '"What\'s the best email API for Node.js?"',
              },
              {
                icon: Building2,
                title: 'B2B SaaS',
                example: 'Agents recommend tools to users. Yours needs to be discoverable.',
                ask: '"What CRM integrates with Slack?"',
              },
              {
                icon: ShoppingBag,
                title: 'Marketplaces & Platforms',
                example: 'Agents book, search, and transact on behalf of users',
                ask: '"What platform handles event registrations?"',
              },
              {
                icon: Briefcase,
                title: 'Any Product with a Signup',
                example: 'If agents can reach it, they need to understand it',
                ask: '"Which accounting software handles VAT?"',
              },
            ].map((useCase, index) => (
              <motion.div
                key={useCase.title}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.08 }}
                className="bg-card rounded-xl border p-6 hover:border-forest/30 transition-all"
              >
                <div className="w-10 h-10 rounded-lg bg-forest-light flex items-center justify-center mb-4">
                  <useCase.icon className="w-5 h-5 text-forest" />
                </div>
                <h3 className="font-semibold mb-1">{useCase.title}</h3>
                <p className="text-sm text-muted-foreground mb-3">{useCase.example}</p>
                <p className="text-xs text-forest font-medium italic">
                  {useCase.ask}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* YC Social Proof */}
      <section className="py-16 lg:py-20 border-y bg-muted/20">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-10 items-center">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="relative aspect-video rounded-xl overflow-hidden shadow-2xl border"
            >
              <iframe
                src="https://www.youtube.com/embed/Q8wVMdwhlh4?start=576"
                title="Diana Hu (YC) on Agent Documentation"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
                className="absolute inset-0 w-full h-full"
              />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="space-y-6"
            >
              <Badge variant="outline" className="text-xs">
                Y Combinator AI Startup School 2025
              </Badge>

              <blockquote className="text-xl lg:text-2xl font-medium leading-relaxed">
                <span className="text-forest">&ldquo;</span>
                Documentation will be the front door for all of these agents recommending tools and services.
                <span className="text-forest">&rdquo;</span>
              </blockquote>

              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-forest-light flex items-center justify-center text-sm font-bold text-forest">
                  DH
                </div>
                <div>
                  <p className="font-semibold text-sm">Diana Hu</p>
                  <p className="text-xs text-muted-foreground">General Partner, Y Combinator</p>
                </div>
              </div>

              <p className="text-sm text-muted-foreground leading-relaxed">
                In this talk, Diana explains how AI agents are rapidly becoming the primary way
                people discover and evaluate products. The companies that optimise their
                content for agent consumption will win. The rest become invisible.
              </p>

              <Button variant="outline" size="sm" onClick={scrollToAssessment} className="rounded-lg">
                Does your product have an /agents page?
                <ArrowRight className="ml-2 w-3 h-3" />
              </Button>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features Section - Mintlify card grid */}
      <section id="how-it-works" className="py-20 lg:py-24">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-2xl mb-16">
            <Badge variant="outline" className="mb-4 text-xs">How it works</Badge>
            <h2 className="font-serif text-3xl md:text-4xl tracking-[-0.01em] mb-4">
              From scan to deployed /agents page in minutes
            </h2>
            <p className="text-muted-foreground text-lg">
              Enter your URL. We analyze your product. You get one page agents can actually use.
            </p>
          </div>

          {/* 3-step flow */}
          <div className="grid md:grid-cols-3 gap-6 mb-20">
            {[
              {
                step: '1',
                icon: Search,
                title: 'Scan Your Product',
                description: 'Enter your URL. We crawl your site to understand what your product does, who it\'s for, and how agents can access it.',
                highlight: 'Free',
              },
              {
                step: '2',
                icon: BarChart3,
                title: 'See What Agents Can\'t Find',
                description: 'We identify the gaps: missing API context, unclear access paths, human-only onboarding, content agents can\'t parse.',
                highlight: 'Instant',
              },
              {
                step: '3',
                icon: Download,
                title: 'Get Your /agents Page',
                description: 'One complete, deployable page built from your product content, structured against all 20 agent-readiness rules. Download and host at /agents.',
                highlight: '$99 one-time',
              },
            ].map((item, index) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="relative bg-card rounded-xl border p-6 hover:border-forest/30 hover:shadow-md transition-all"
              >
                <div className="flex items-center justify-between mb-5">
                  <div className="w-10 h-10 rounded-lg bg-forest-light flex items-center justify-center">
                    <item.icon className="w-5 h-5 text-forest" />
                  </div>
                  <Badge variant="secondary" className="text-xs">{item.highlight}</Badge>
                </div>
                <h3 className="text-lg font-semibold mb-2">{item.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{item.description}</p>
              </motion.div>
            ))}
          </div>

          {/* Feature cards - Mintlify-style 2x2 */}
          <div className="grid md:grid-cols-2 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="bg-card rounded-xl border p-8 hover:border-forest/30 hover:shadow-md transition-all"
              >
                <div className="w-12 h-12 bg-forest-light rounded-xl flex items-center justify-center mb-5">
                  <feature.icon className="w-6 h-6 text-forest" />
                </div>
                <h3 className="text-xl font-semibold mb-3">{feature.title}</h3>
                <p className="text-muted-foreground leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Before/After Slideshow - Dark section */}
      <section className="py-20 lg:py-24 bg-slate-950 text-white border-y">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-2xl mb-12">
            <Badge className="mb-4 bg-white/10 text-white border-white/20 hover:bg-white/20 text-xs">
              Before and after
            </Badge>
            <h2 className="font-serif text-3xl md:text-4xl tracking-[-0.01em] mb-4 text-white">
              The quality standard behind every /agents page
            </h2>
            <p className="text-slate-400 text-lg">
              Each /agents page we build applies all 20 rules. Here's the difference it makes —
              the same content, before and after agent-first structuring.
            </p>
          </div>

          <BeforeAfterSlideshow />
        </div>
      </section>

      {/* The 20 Rules */}
      <section id="rules" className="py-20 lg:py-24">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-2xl mb-12">
            <Badge variant="outline" className="mb-4 text-xs">Our methodology</Badge>
            <h2 className="font-serif text-3xl md:text-4xl tracking-[-0.01em] mb-4">
              The 20 Agent-Readiness Rules
            </h2>
            <p className="text-muted-foreground text-lg">
              Derived from benchmarking 8 agents on what makes content easy or hard for them to consume.
              Every /agents page we build passes all 20. Every rule is concrete and verifiable.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {agentReadinessRules.map((rule, index) => (
              <motion.div
                key={rule.id}
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.02 }}
                className="bg-card p-4 rounded-xl border hover:border-forest/30 hover:bg-forest-light/30 transition-all group"
              >
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center flex-shrink-0 group-hover:bg-forest-light transition-colors">
                    <rule.icon className="w-4 h-4 text-muted-foreground group-hover:text-forest transition-colors" />
                  </div>
                  <div>
                    <p className="font-mono text-xs leading-tight text-foreground">
                      <span className="text-muted-foreground mr-1">#{rule.id}</span>
                      {rule.name}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                      {rule.description}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          <div className="text-center mt-12">
            <p className="text-sm text-muted-foreground mb-5">
              We scan your product against all 20 rules and build your /agents page so it passes every one.
            </p>
            <Button onClick={scrollToAssessment} className="rounded-xl bg-forest hover:bg-forest-hover text-white">
              Check If Your Product Is Agent-Ready
              <ArrowRight className="ml-2 w-4 h-4" />
            </Button>
          </div>
        </div>
      </section>

      {/* Pricing Section - Mintlify-inspired clean pricing */}
      <section id="pricing" className="py-20 lg:py-24 bg-muted/30 border-y">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-2xl mb-16">
            <Badge variant="outline" className="mb-4 text-xs">Pricing</Badge>
            <h2 className="font-serif text-3xl md:text-4xl tracking-[-0.01em] mb-4">Simple, transparent pricing</h2>
            <p className="text-muted-foreground text-lg">
              Free scan first. Pay only if you want your /agents page built. $99 one-time — no subscription, no monthly fees, no engagement.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {/* Free Column */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="bg-card rounded-xl border p-8 flex flex-col"
            >
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-1">Agent Readiness Scan</h3>
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-bold">$0</span>
                </div>
                <p className="text-sm text-muted-foreground mt-2">See what agents can and can't find</p>
              </div>

              <ul className="space-y-3 flex-1">
                {[
                  'Agent-Readiness Score (0-100)',
                  'Letter grade (A+ to F)',
                  '20-rule pass/warning/fail checklist',
                  'Exactly what agents struggle to find',
                  'What\'s blocking autonomous access',
                ].map((feature) => (
                  <li key={feature} className="flex items-start gap-2.5 text-sm">
                    <CheckCircle2 className="w-4 h-4 text-forest flex-shrink-0 mt-0.5" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>

              <Button
                variant="outline"
                className="w-full mt-8 rounded-xl h-11"
                onClick={scrollToAssessment}
              >
                Scan My Product — Free
              </Button>
            </motion.div>

            {/* Paid Column */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 }}
              className="bg-card rounded-xl border-2 border-forest shadow-xl shadow-forest/10 p-8 flex flex-col relative"
            >
              <span className="absolute -top-3.5 left-6 inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-forest text-white">
                <Sparkles className="w-3 h-3 mr-1" />
                Most popular
              </span>

              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-1">Your /agents Page</h3>
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-bold">$99</span>
                  <span className="text-sm text-muted-foreground">(€84)</span>
                </div>
                <p className="text-sm font-medium text-forest mt-2">
                  One-time payment · No subscription · No monthly fees
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  Pay once, download, deploy at /agents. No engagement. No recurring charges.
                </p>
              </div>

              <ul className="space-y-3 flex-1">
                {[
                  'Everything in the free scan',
                  'One complete /agents page, ready to deploy',
                  'Agent-first voice — written for machine readers',
                  'Full product description an agent can act on',
                  'Access path: API, auth, signup — zero friction',
                  'Structured examples an agent can execute',
                  'Convince-your-human pitch section included',
                  'llms.txt entry point + deploy in minutes',
                ].map((feature) => (
                  <li key={feature} className="flex items-start gap-2.5 text-sm">
                    <CheckCircle2 className="w-4 h-4 text-forest flex-shrink-0 mt-0.5" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>

              <Button
                className="w-full mt-8 rounded-xl h-11 bg-forest hover:bg-forest-hover text-white"
                onClick={scrollToAssessment}
              >
                Scan First, Then Decide
                <ArrowRight className="ml-2 w-4 h-4" />
              </Button>
              <p className="text-xs text-center text-muted-foreground mt-3">
                Free scan first. One-shot purchase if you want the page built.
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* CTA Banner */}
      <section className="py-20 lg:py-24 relative overflow-hidden bg-forest">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="font-serif text-3xl md:text-4xl text-white mb-4 tracking-[-0.01em]">
            Does your product have a front door for AI agents?
          </h2>
          <p className="text-white/80 text-lg mb-8 max-w-2xl mx-auto">
            When an AI agent encounters your product, it should have a dedicated page that speaks its language.
            Without one, agents make their best guess — or skip you entirely.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button
              size="lg"
              onClick={scrollToAssessment}
              className="rounded-xl bg-white text-forest hover:bg-forest-light h-12 px-8 font-semibold"
            >
              Check Agent Readiness — Free
              <ArrowRight className="ml-2 w-4 h-4" />
            </Button>
            <a href="#rules" className="text-white/90 hover:text-white text-sm font-medium flex items-center gap-1.5">
              See the 20 rules
              <ArrowRight className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>
      </section>

      {/* FAQ Section - Mintlify-style accordion */}
      <section id="faq" className="py-20 lg:py-24">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-12">
            <Badge variant="outline" className="mb-4 text-xs">FAQ</Badge>
            <h2 className="font-serif text-3xl md:text-4xl tracking-[-0.01em]">Frequently asked questions</h2>
          </div>

          <div className="border rounded-xl bg-card divide-y">
            <div className="px-6">
              <FaqItem
                q="What is an /agents page?"
                a="An /agents page is a dedicated page on your site — typically at yourproduct.com/agents — written specifically for AI agents, not humans. It tells agents what your product is, how to access it, what it can do, and how to onboard autonomously. Monday.com pioneered this format. We build yours, applying all 20 agent-readiness rules so it's complete, machine-readable, and actually useful."
              />
              <FaqItem
                q="Do I need an API or developer product?"
                a="Not necessarily. Any product an agent might recommend, help a user set up, or interact with on their behalf benefits from an /agents page. If you have a signup flow, a free tier, or any kind of programmatic access — you need one. Even if you don't, agents still encounter your product and need a structured way to understand it."
              />
              <FaqItem
                q="Where do these 20 rules come from?"
                a="We benchmarked 8 major AI agents (Claude, GPT, Gemini, Grok, Kimi, Deepseek, Manus, and others) on what actually makes content easy or hard for them to consume. The 20 rules are the consensus: specific patterns that all agents agree matter for accurate answers and reliable recommendations."
              />
              <FaqItem
                q="What do I get for free vs. the paid product?"
                a="The free scan analyzes your site and shows you what agents can't find: missing API context, unclear access paths, content that blocks autonomous use. The paid product ($99 one-time) is your complete /agents page — one deployable HTML and Markdown file that covers everything an agent needs, built from your product's content and structured against all 20 rules."
              />
              <FaqItem
                q="How is the price calculated?"
                a="It's a flat $99 (€84) for everyone — one complete /agents page, no matter how complex your product. No per-page pricing, no tiers, no recurring fees. You pay once, download your page, and deploy it at /agents on your domain."
              />
              <FaqItem
                q="How long does it take?"
                a="The free scan takes about 60 seconds. After purchase, your /agents page is generated in roughly 5 minutes. You'll get the HTML and Markdown files immediately."
              />
              <FaqItem
                q="What format are the files in?"
                a="You get your /agents page as an HTML file ready to deploy at /agents on your domain, a Markdown version, and an llms.txt entry point. Works with any platform: static sites, Webflow, Framer, Vercel, Netlify, or any CMS that accepts HTML."
              />
            </div>
          </div>
        </div>
      </section>

      {/* Blog Section */}
      <section className="py-20 lg:py-24 border-t">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-end justify-between mb-10 gap-4">
            <div>
              <Badge variant="outline" className="mb-4 text-xs">From the blog</Badge>
              <h2 className="font-serif text-3xl md:text-4xl tracking-[-0.01em]">
                The agent-first documentation playbook
              </h2>
              <p className="text-muted-foreground mt-3 max-w-xl">
                Deep guides on what AI agents actually need — from entry points to answerability.
                Learn how the best products are building for the agent economy.
              </p>
            </div>
            <Link
              to="/blog"
              className="hidden md:flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors whitespace-nowrap"
            >
              View all articles
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {BLOG_POSTS.slice(0, 3).map((post) => (
              <Link
                key={post.slug}
                to={`/blog/${post.slug}`}
                className="group block rounded-xl border bg-card p-6 hover:border-emerald-500/40 hover:shadow-lg hover:shadow-emerald-500/5 transition-all duration-200"
              >
                <div className="flex items-center justify-between mb-4">
                  <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    {post.category}
                  </span>
                  <span className="text-xs text-muted-foreground">{post.readingTime} min read</span>
                </div>
                <h3 className="text-sm font-semibold leading-snug mb-2 group-hover:text-emerald-400 transition-colors line-clamp-2">
                  {post.title}
                </h3>
                <p className="text-xs text-muted-foreground line-clamp-2 mb-4">
                  {post.description}
                </p>
                <span className="text-xs text-emerald-400 group-hover:translate-x-0.5 transition-transform inline-block">
                  Read article →
                </span>
              </Link>
            ))}
          </div>

          <div className="mt-6 text-center md:hidden">
            <Link
              to="/blog"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors inline-flex items-center gap-1.5"
            >
              View all 6 articles <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-20 lg:py-24 border-t bg-muted/20">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="font-serif text-3xl md:text-4xl tracking-[-0.01em] mb-4">
            Give AI agents a front door to your product
          </h2>
          <p className="text-muted-foreground text-lg mb-8">
            The products that build for agents first will own the agent economy.
            The rest will wonder why AI stopped recommending them.
          </p>
          <Button size="lg" onClick={scrollToAssessment} className="rounded-xl bg-forest hover:bg-forest-hover text-white h-12 px-8">
            Check Agent Readiness — Free
            <ArrowRight className="ml-2 w-4 h-4" />
          </Button>
        </div>
      </section>

      {/* Footer - Mintlify-style clean footer */}
      <footer className="border-t py-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 bg-forest rounded-lg flex items-center justify-center">
                <Zap className="w-4 h-4 text-white" />
              </div>
              <span className="text-lg font-semibold">GrounDocs</span>
            </div>

            <div className="flex items-center gap-6">
              <a href="#how-it-works" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                How it Works
              </a>
              <a href="#rules" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                20 Rules
              </a>
              <a href="#pricing" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Pricing
              </a>
              <a href="#faq" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                FAQ
              </a>
              <Link to="/blog" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Blog
              </Link>
              <a href="/support" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Support
              </a>
            </div>

            <p className="text-sm text-muted-foreground">
              &copy; {new Date().getFullYear()} GrounDocs
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
