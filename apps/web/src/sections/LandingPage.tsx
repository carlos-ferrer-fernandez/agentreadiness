import { useState, useCallback, useEffect } from 'react'
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
  ChevronLeft,
  ChevronRight,
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
import { useNavigate } from 'react-router-dom'

const features = [
  {
    icon: Bot,
    title: 'Multi-Agent Simulation',
    description: 'We test your docs the way Claude, GPT, Gemini, and 5 other agents actually consume them. Not how humans read them.',
    gradient: 'from-blue-500/10 to-cyan-500/10',
    iconColor: 'text-blue-500',
  },
  {
    icon: BarChart3,
    title: 'Agent-Readiness Score',
    description: 'Get a 0-100 score with letter grade, rule-by-rule breakdown, and per-page findings. Know exactly where you stand.',
    gradient: 'from-violet-500/10 to-purple-500/10',
    iconColor: 'text-violet-500',
  },
  {
    icon: FileCode,
    title: 'Rewritten Documentation',
    description: 'Not a report. Not tips. We rewrite your actual docs applying all 20 rules. Download a ZIP and deploy in minutes.',
    gradient: 'from-emerald-500/10 to-green-500/10',
    iconColor: 'text-emerald-500',
  },
  {
    icon: Globe,
    title: 'llms.txt Entry Point',
    description: 'Every package includes an llms.txt file. The agent discovery standard that helps AI find and navigate your docs.',
    gradient: 'from-amber-500/10 to-orange-500/10',
    iconColor: 'text-amber-500',
  },
]

const agentReadinessRules = [
  { id: 1, name: 'Self-Contained Sections', icon: BookOpen, description: 'Every section must make sense if read in isolation. No "see above" or "as mentioned earlier".' },
  { id: 2, name: 'Action-Oriented Headings', icon: MessageSquare, description: 'Headings should read like user intents: "Authenticate with API key", not "Authentication".' },
  { id: 3, name: 'Structured Parameter Tables', icon: Table2, description: 'Parameters in tables (name, type, required, default), never buried in prose.' },
  { id: 4, name: 'Complete Code Examples', icon: Code2, description: 'Every example must include imports, setup, the call, and expected output.' },
  { id: 5, name: 'Explicit Over Implicit', icon: Eye, description: 'State all defaults, constraints, and requirements. Agents have zero intuition.' },
  { id: 6, name: 'First-Class Error Docs', icon: AlertOctagon, description: 'Every error code documented with causes, diagnosis steps, and fixes.' },
  { id: 7, name: 'Consistent Terminology', icon: Tags, description: 'One term per concept everywhere. No alternating between synonyms.' },
  { id: 8, name: 'Frontmatter Metadata', icon: FileCheck, description: 'YAML frontmatter on every page: title, description, version, tags.' },
  { id: 9, name: 'Prerequisites Up Front', icon: ListChecks, description: 'State all requirements at the top: accounts, permissions, API keys, SDK version.' },
  { id: 10, name: 'Expected Outputs', icon: MonitorCheck, description: 'Show what success looks like: expected response body, status code, logs.' },
  { id: 11, name: 'Cross-References with Context', icon: Link2, description: 'Never "click here". Always describe what the linked page covers.' },
  { id: 12, name: 'Content Type Separation', icon: Layers, description: 'Separate conceptual, how-to, and reference content clearly.' },
  { id: 13, name: 'Version Clarity', icon: History, description: 'API/SDK version stated prominently. Deprecated content marked with migration paths.' },
  { id: 14, name: 'Decision Documentation', icon: HelpCircle, description: '"When to use X vs Y" sections for agents answering comparison questions.' },
  { id: 15, name: 'Safety Boundaries', icon: ShieldAlert, description: 'Destructive actions, billing implications, rate limits clearly documented.' },
  { id: 16, name: 'No Anti-Patterns', icon: Trash2, description: 'Strip marketing language, "contact support" placeholders, and JS-dependent content.' },
  { id: 17, name: 'Retrieval-Chunk Optimized', icon: SplitSquareHorizontal, description: 'Sections scoped for RAG: clear heading, clear scope, standalone context.' },
  { id: 18, name: 'Intent Before Mechanics', icon: Megaphone, description: 'Always explain WHY before HOW. Context before code.' },
  { id: 19, name: 'State Transitions', icon: RefreshCcw, description: 'Document systems as state machines: states, transitions, triggers, terminal states.' },
  { id: 20, name: 'Callouts & Admonitions', icon: AlertTriangle, description: 'Standard callout syntax for warnings, tips, and notes. These are prioritization signals for agents.' },
]

const assessmentStages = [
  { name: 'Discovering pages', icon: Search },
  { name: 'Crawling documentation', icon: FileText },
  { name: 'Checking self-contained sections', icon: BookOpen },
  { name: 'Evaluating code examples', icon: Code2 },
  { name: 'Analyzing heading structure', icon: MessageSquare },
  { name: 'Checking parameter tables', icon: Table2 },
  { name: 'Scanning for anti-patterns', icon: Trash2 },
  { name: 'Testing retrieval chunks', icon: SplitSquareHorizontal },
  { name: 'Verifying error documentation', icon: AlertOctagon },
  { name: 'Running 20-rule evaluation', icon: ListChecks },
  { name: 'Calculating your score', icon: BarChart3 },
]

const liveStatusMessages = [
  'Simulating how Claude reads your docs...',
  'Checking if GPT can find your API reference...',
  'Testing RAG retrieval on your sections...',
  'Verifying code examples are copy-paste ready...',
  'Scanning for vague cross-references...',
  'Checking terminology consistency...',
  'Evaluating frontmatter metadata...',
  'Testing heading relevance for agent queries...',
  'Looking for missing expected outputs...',
  'Checking safety boundary documentation...',
  'Analyzing content type separation...',
  'Almost there, finalizing scores...',
]

// Before/After examples using Mailgun docs (mentioned in the YC video as a cautionary tale)
const beforeAfterSlides = [
  {
    rule: '#4 Complete Code Examples',
    ruleShort: 'Rule #4',
    tagline: 'If an agent can\'t copy-paste it, it doesn\'t exist',
    before: {
      label: 'Mailgun docs',
      lines: [
        { text: 'const mg = mailgun.client({', type: 'code' as const },
        { text: '  username: "api",', type: 'code' as const },
        { text: '  key: "MAILGUN_API_KEY"', type: 'code' as const },
        { text: '});', type: 'code' as const },
        { text: '', type: 'gap' as const },
        { text: '// No imports shown. FormData required but', type: 'comment-bad' as const },
        { text: '// not in the example. No expected response.', type: 'comment-bad' as const },
        { text: '// Agent generates broken code every time.', type: 'comment-bad' as const },
      ],
    },
    after: {
      label: 'After AgentReadiness',
      lines: [
        { text: '// 1. Install: npm install mailgun.js', type: 'comment-good' as const },
        { text: 'import Mailgun from "mailgun.js";', type: 'code' as const },
        { text: 'const mailgun = new Mailgun(FormData);', type: 'code' as const },
        { text: 'const mg = mailgun.client({', type: 'code' as const },
        { text: '  username: "api",', type: 'code' as const },
        { text: '  key: process.env.MAILGUN_API_KEY', type: 'code' as const },
        { text: '});', type: 'code' as const },
        { text: '', type: 'gap' as const },
        { text: '// Expected: mg is a configured client', type: 'comment-good' as const },
        { text: '// ready to call mg.messages.create()', type: 'comment-good' as const },
      ],
    },
  },
  {
    rule: '#2 Action-Oriented Headings',
    ruleShort: 'Rule #2',
    tagline: 'Agents search by intent, not by topic',
    before: {
      label: 'Mailgun docs',
      lines: [
        { text: '## Messages', type: 'heading-bad' as const },
        { text: '', type: 'gap' as const },
        { text: '## Domains', type: 'heading-bad' as const },
        { text: '', type: 'gap' as const },
        { text: '## Events', type: 'heading-bad' as const },
        { text: '', type: 'gap' as const },
        { text: '## Webhooks', type: 'heading-bad' as const },
        { text: '', type: 'gap' as const },
        { text: '// Topic headings. An agent searching "how', type: 'comment-bad' as const },
        { text: '// to send email" won\'t match "Messages".', type: 'comment-bad' as const },
      ],
    },
    after: {
      label: 'After AgentReadiness',
      lines: [
        { text: '## Send an Email via the Mailgun API', type: 'heading-good' as const },
        { text: '', type: 'gap' as const },
        { text: '## Verify and Configure a Sending Domain', type: 'heading-good' as const },
        { text: '', type: 'gap' as const },
        { text: '## Track Email Delivery Events', type: 'heading-good' as const },
        { text: '', type: 'gap' as const },
        { text: '## Set Up Webhooks for Bounce Handling', type: 'heading-good' as const },
        { text: '', type: 'gap' as const },
        { text: '// Intent-based headings match how agents', type: 'comment-good' as const },
        { text: '// search: "how to send email with Mailgun"', type: 'comment-good' as const },
      ],
    },
  },
  {
    rule: '#3 Structured Parameter Tables',
    ruleShort: 'Rule #3',
    tagline: 'Tables are machine-parseable. Prose is not.',
    before: {
      label: 'Mailgun docs',
      lines: [
        { text: 'You can pass the following parameters:', type: 'normal' as const },
        { text: 'to, subject, html or text for content,', type: 'prose-bad' as const },
        { text: 'o:tag for tagging, o:campaign for campaign', type: 'prose-bad' as const },
        { text: 'identification, attachment for files', type: 'prose-bad' as const },
        { text: '(multipart/form-data required).', type: 'prose-bad' as const },
        { text: '', type: 'gap' as const },
        { text: '// Parameters buried in prose. No types,', type: 'comment-bad' as const },
        { text: '// no defaults, no required markers.', type: 'comment-bad' as const },
      ],
    },
    after: {
      label: 'After AgentReadiness',
      lines: [
        { text: '| Parameter  | Type     | Required | Description          |', type: 'table-header' as const },
        { text: '|------------|----------|----------|----------------------|', type: 'table-sep' as const },
        { text: '| from       | string   | yes      | Sender address       |', type: 'table-row' as const },
        { text: '| to         | string[] | yes      | Recipients (max 50)  |', type: 'table-row' as const },
        { text: '| subject    | string   | yes      | Email subject line   |', type: 'table-row' as const },
        { text: '| html       | string   | one of*  | HTML email body      |', type: 'table-row' as const },
        { text: '| text       | string   | one of*  | Plain text body      |', type: 'table-row' as const },
        { text: '| o:tag      | string[] | no       | Message tags         |', type: 'table-row' as const },
      ],
    },
  },
  {
    rule: '#6 First-Class Error Docs',
    ruleShort: 'Rule #6',
    tagline: 'Agents need exact error strings to help users debug',
    before: {
      label: 'Mailgun docs',
      lines: [
        { text: 'Mailgun returns standard HTTP response', type: 'normal' as const },
        { text: 'codes. 200 for success. Errors include a', type: 'normal' as const },
        { text: 'message field in the JSON response.', type: 'normal' as const },
        { text: '', type: 'gap' as const },
        { text: '// No error table. No common failure modes.', type: 'comment-bad' as const },
        { text: '// "Domain not verified" kills onboarding', type: 'comment-bad' as const },
        { text: '// but isn\'t documented anywhere.', type: 'comment-bad' as const },
      ],
    },
    after: {
      label: 'After AgentReadiness',
      lines: [
        { text: '| Error              | Cause                | Fix                  |', type: 'table-header' as const },
        { text: '|--------------------|----------------------|----------------------|', type: 'table-sep' as const },
        { text: '| 401 Unauthorized   | Invalid API key      | Check key in env     |', type: 'table-row' as const },
        { text: '| 400 "domain not    | Domain not verified  | Complete DNS setup   |', type: 'table-row' as const },
        { text: '|   verified"        |                      | in Mailgun dashboard |', type: 'table-row' as const },
        { text: '| 400 "to param      | Missing recipients   | Add to: ["email"]    |', type: 'table-row' as const },
        { text: '|   is required"     |                      |                      |', type: 'table-row' as const },
        { text: '| 429 Rate limited   | Too many requests    | Add 1s delay or use  |', type: 'table-row' as const },
        { text: '|                    |                      | batch sending        |', type: 'table-row' as const },
      ],
    },
  },
  {
    rule: '#9 Prerequisites + #10 Expected Output',
    ruleShort: 'Rules #9 & #10',
    tagline: 'Tell agents what\'s needed before and what success looks like after',
    before: {
      label: 'Mailgun docs',
      lines: [
        { text: '# Quickstart', type: 'heading-bad' as const },
        { text: '', type: 'gap' as const },
        { text: 'Mailgun is an email service provider...', type: 'normal' as const },
        { text: '', type: 'gap' as const },
        { text: 'mg.messages.create("sandbox.mailgun.org",', type: 'code' as const },
        { text: '  { from: "...", to: ["..."], subject: "..." }', type: 'code' as const },
        { text: ')', type: 'code' as const },
        { text: '', type: 'gap' as const },
        { text: '// No prerequisites. No expected response.', type: 'comment-bad' as const },
        { text: '// Agent doesn\'t know setup is needed first.', type: 'comment-bad' as const },
      ],
    },
    after: {
      label: 'After AgentReadiness',
      lines: [
        { text: '## Prerequisites', type: 'heading-good' as const },
        { text: '- Mailgun account (free tier: 100 emails/day)', type: 'normal' as const },
        { text: '- Verified sending domain (DNS records)', type: 'normal' as const },
        { text: '- API key from Settings > API Keys', type: 'normal' as const },
        { text: '- Node.js >= 18.x, npm install mailgun.js', type: 'normal' as const },
        { text: '', type: 'gap' as const },
        { text: '## Expected Response', type: 'heading-good' as const },
        { text: '// { id: "<abc123@sandbox.mailgun.org>",', type: 'comment-good' as const },
        { text: '//   message: "Queued. Thank you." }', type: 'comment-good' as const },
      ],
    },
  },
]

function CodeLine({ line }: { line: { text: string; type: string } }) {
  const styles: Record<string, string> = {
    'heading-bad': 'text-red-400 font-bold',
    'heading-good': 'text-emerald-400 font-bold',
    'normal': 'text-slate-300',
    'gap': '',
    'prose-bad': 'text-red-300/80 bg-red-500/10',
    'code': 'text-sky-300',
    'comment-bad': 'text-red-400/60 italic',
    'comment-good': 'text-emerald-400/60 italic',
    'table-header': 'text-amber-300 font-mono text-xs',
    'table-sep': 'text-slate-600 font-mono text-xs',
    'table-row': 'text-slate-300 font-mono text-xs',
    'frontmatter': 'text-violet-400',
  }
  if (line.type === 'gap') return <div className="h-2" />
  return (
    <div className={cn('px-3 py-0.5 font-mono text-[13px] leading-relaxed whitespace-pre', styles[line.type] || 'text-slate-300')}>
      {line.text}
    </div>
  )
}

function BeforeAfterSlideshow() {
  const [current, setCurrent] = useState(0)
  const slide = beforeAfterSlides[current]

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrent(prev => (prev + 1) % beforeAfterSlides.length)
    }, 6000)
    return () => clearInterval(timer)
  }, [])

  return (
    <div>
      <div className="flex items-center justify-center gap-3 mb-6">
        <button
          onClick={() => setCurrent(prev => (prev - 1 + beforeAfterSlides.length) % beforeAfterSlides.length)}
          className="p-1.5 rounded-full hover:bg-white/10 transition-colors text-slate-400"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
        <div className="flex items-center gap-2">
          {beforeAfterSlides.map((_, i) => (
            <button
              key={i}
              onClick={() => setCurrent(i)}
              className={cn(
                'w-2 h-2 rounded-full transition-all',
                i === current ? 'bg-emerald-400 w-6' : 'bg-slate-600 hover:bg-slate-500'
              )}
            />
          ))}
        </div>
        <button
          onClick={() => setCurrent(prev => (prev + 1) % beforeAfterSlides.length)}
          className="p-1.5 rounded-full hover:bg-white/10 transition-colors text-slate-400"
        >
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={current}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.25 }}
        >
          <div className="text-center mb-6">
            <Badge className="mb-2 bg-emerald-500/20 text-emerald-300 border-emerald-500/30 hover:bg-emerald-500/30">{slide.rule}</Badge>
            <p className="text-sm text-slate-400">{slide.tagline}</p>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            {/* Before */}
            <div className="rounded-xl border border-red-500/20 bg-slate-950 overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-2.5 bg-red-500/10 border-b border-red-500/20">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-red-500/60" />
                  <div className="w-3 h-3 rounded-full bg-slate-700" />
                  <div className="w-3 h-3 rounded-full bg-slate-700" />
                </div>
                <span className="text-xs text-red-400 font-medium ml-2">BEFORE</span>
                <span className="text-xs text-slate-500 ml-auto">{slide.before.label}</span>
              </div>
              <div className="py-3 min-h-[220px]">
                {slide.before.lines.map((line, i) => (
                  <CodeLine key={i} line={line} />
                ))}
              </div>
            </div>

            {/* After */}
            <div className="rounded-xl border border-emerald-500/20 bg-slate-950 overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-2.5 bg-emerald-500/10 border-b border-emerald-500/20">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-emerald-500/60" />
                  <div className="w-3 h-3 rounded-full bg-slate-700" />
                  <div className="w-3 h-3 rounded-full bg-slate-700" />
                </div>
                <span className="text-xs text-emerald-400 font-medium ml-2">AFTER</span>
                <span className="text-xs text-slate-500 ml-auto">{slide.after.label}</span>
              </div>
              <div className="py-3 min-h-[220px]">
                {slide.after.lines.map((line, i) => (
                  <CodeLine key={i} line={line} />
                ))}
              </div>
            </div>
          </div>

          <p className="text-center text-xs text-slate-500 mt-4">
            {current + 1} of {beforeAfterSlides.length} examples
          </p>
        </motion.div>
      </AnimatePresence>
    </div>
  )
}

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

    try {
      const response = await assessmentsApi.analyze({
        url: validatedUrl,
        email,
        full_name: fullName || undefined,
        role: role || undefined,
      })
      clearInterval(stageInterval)
      clearInterval(messageInterval)

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
      clearInterval(stageInterval)
      clearInterval(messageInterval)
      const message = err.response?.data?.detail || 'Analysis failed. Please check the URL and try again.'
      setAssessmentError(message)
      setError(message)
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
              <div className="w-7 h-7 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-lg flex items-center justify-center">
                <Zap className="w-4 h-4 text-white" />
              </div>
              <span className="text-lg font-semibold tracking-tight">AgentReadiness</span>
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
              <div className="w-px h-5 bg-border mx-2" />
              <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700 text-white" onClick={scrollToAssessment}>
                Get Free Score
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
                <Button size="sm" className="w-full mt-2 bg-emerald-600 hover:bg-emerald-700 text-white" onClick={scrollToAssessment}>
                  Get Free Score
                </Button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </nav>

      {/* Hero Section - Mintlify-inspired gradient hero */}
      <section className="relative overflow-hidden">
        {/* Gradient background */}
        <div className="absolute inset-0 bg-gradient-to-b from-emerald-50/50 via-background to-background dark:from-emerald-950/20 -z-10" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-gradient-to-br from-emerald-500/10 via-cyan-500/5 to-transparent rounded-full blur-3xl -z-10" />

        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16 lg:pt-28 lg:pb-24">
          <div className="text-center max-w-3xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-300 text-sm font-medium mb-8">
                <Sparkles className="w-3.5 h-3.5" />
                Benchmarked against Claude, GPT, Gemini, and 5 more agents
              </span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-4xl md:text-5xl lg:text-[3.5rem] font-bold tracking-tight leading-[1.1] mb-6"
            >
              Build documentation that{' '}
              <span className="bg-gradient-to-r from-emerald-600 to-cyan-600 dark:from-emerald-400 dark:to-cyan-400 bg-clip-text text-transparent">
                AI agents can actually use
              </span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="text-lg text-muted-foreground mb-10 max-w-2xl mx-auto leading-relaxed"
            >
              When developers ask AI for tool recommendations, the answer comes from your docs.
              We evaluate yours against 20 rules, then rewrite every page so agents can parse,
              cite, and recommend you.
            </motion.p>

            {/* Assessment Form - Cleaner Mintlify-style */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              id="assessment"
              className="max-w-xl mx-auto"
            >
              <div className="bg-card border rounded-2xl p-6 shadow-xl shadow-black/5">
                <div className="space-y-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                    <Input
                      type="text"
                      placeholder="Enter your docs URL (e.g., docs.example.com)"
                      value={url}
                      onChange={(e) => { setUrl(e.target.value); setError(null) }}
                      className="pl-10 h-12 text-base rounded-xl border-border/60 focus:border-emerald-500 focus:ring-emerald-500/20"
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
                            We'll send your free report to this email
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
                            placeholder="Role (e.g. CTO, DevRel)"
                            value={role}
                            onChange={(e) => setRole(e.target.value)}
                            className="h-10 text-sm rounded-lg"
                          />
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {error && (
                    <p className="text-sm text-red-600">{error}</p>
                  )}

                  <Button
                    size="lg"
                    onClick={handleAnalyze}
                    disabled={isAssessing || !url || !email}
                    className="w-full rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white h-12"
                  >
                    {isAssessing ? (
                      <>
                        <Clock className="mr-2 w-4 h-4 animate-spin" />
                        Scanning...
                      </>
                    ) : (
                      <>
                        Run Free Assessment
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
                                isComplete ? "bg-emerald-100 dark:bg-emerald-900/30" : isActive ? "bg-emerald-500/10" : "bg-muted"
                              )}>
                                {isComplete ? (
                                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                                ) : (
                                  <StageIcon className={cn(
                                    "w-4 h-4",
                                    isActive ? "text-emerald-600" : "text-muted-foreground"
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
                                  className="ml-auto w-4 h-4 border-2 border-emerald-500 border-t-transparent rounded-full"
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

              <div className="flex items-center justify-center gap-6 mt-5 text-xs text-muted-foreground">
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                  Free, no credit card
                </span>
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                  60-second scan
                </span>
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                  20-rule evaluation
                </span>
              </div>
            </motion.div>
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
          <div className="max-w-3xl mx-auto text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
            >
              <Badge variant="outline" className="mb-6 text-xs">The new distribution channel</Badge>
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-6">
                Your docs are your storefront in the agent economy
              </h2>
              <p className="text-lg text-muted-foreground leading-relaxed mb-4">
                AI agents don't browse your marketing site. They read your documentation.
                When a developer asks Claude "what's the best auth library?" or GPT "how do I send emails in Python?",
                the agent pulls from docs to answer.
              </p>
              <p className="text-lg text-muted-foreground leading-relaxed">
                If your docs aren't structured for machine consumption, agents can't parse them, can't cite them,
                and recommend someone else. Your documentation is no longer just for humans.
              </p>
            </motion.div>
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
                <span className="text-emerald-500">&ldquo;</span>
                Documentation will be the front door for all of these agents recommending devtools.
                <span className="text-emerald-500">&rdquo;</span>
              </blockquote>

              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-emerald-500/10 flex items-center justify-center text-sm font-bold text-emerald-600">
                  DH
                </div>
                <div>
                  <p className="font-semibold text-sm">Diana Hu</p>
                  <p className="text-xs text-muted-foreground">General Partner, Y Combinator</p>
                </div>
              </div>

              <p className="text-sm text-muted-foreground leading-relaxed">
                In this talk, Diana explains how AI agents are rapidly becoming the primary way
                developers discover and evaluate tools. The companies that optimise their
                documentation for agent consumption will win. The rest become invisible.
              </p>

              <Button variant="outline" size="sm" onClick={scrollToAssessment} className="rounded-lg">
                Check if agents can find you
                <ArrowRight className="ml-2 w-3 h-3" />
              </Button>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features Section - Mintlify card grid */}
      <section id="how-it-works" className="py-20 lg:py-24">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <Badge variant="outline" className="mb-4 text-xs">How it works</Badge>
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">
              From assessment to deployment in minutes
            </h2>
            <p className="text-muted-foreground text-lg">
              Enter your docs URL. Get a score. See what's failing. Get the fixed docs.
            </p>
          </div>

          {/* 3-step flow */}
          <div className="grid md:grid-cols-3 gap-6 mb-20">
            {[
              {
                step: '1',
                icon: Search,
                title: 'Get Your Free Score',
                description: 'Enter your docs URL. We evaluate against 20 agent-readiness rules derived from benchmarking 8 major AI agents.',
                highlight: 'Free',
              },
              {
                step: '2',
                icon: BarChart3,
                title: 'See What\'s Failing',
                description: 'Rule-by-rule breakdown: which rules pass, which fail, and exactly what agents struggle with. Per-page findings.',
                highlight: 'Instant',
              },
              {
                step: '3',
                icon: Download,
                title: 'Download Fixed Docs',
                description: 'Every page rewritten applying all 20 rules. Download a ZIP with optimized markdown + llms.txt. Deploy in minutes.',
                highlight: 'From $99',
              },
            ].map((item, index) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="relative bg-card rounded-2xl border p-6 hover:border-emerald-500/30 hover:shadow-lg hover:shadow-emerald-500/5 transition-all"
              >
                <div className="flex items-center justify-between mb-5">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                    <item.icon className="w-5 h-5 text-emerald-600" />
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
                className={cn(
                  "bg-gradient-to-br rounded-2xl border p-8 hover:shadow-lg transition-all",
                  feature.gradient
                )}
              >
                <div className="w-12 h-12 bg-background rounded-xl flex items-center justify-center mb-5 shadow-sm border">
                  <feature.icon className={cn("w-6 h-6", feature.iconColor)} />
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
          <div className="text-center max-w-2xl mx-auto mb-12">
            <Badge className="mb-4 bg-emerald-500/20 text-emerald-300 border-emerald-500/30 hover:bg-emerald-500/30 text-xs">
              Real example: Mailgun docs
            </Badge>
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4 text-white">
              See why Resend is winning
            </h2>
            <p className="text-slate-400 text-lg">
              Mailgun's docs are hard for agents to parse. That's why AI recommends Resend instead.
              Here's what we'd fix.
            </p>
          </div>

          <BeforeAfterSlideshow />
        </div>
      </section>

      {/* The 20 Rules */}
      <section id="rules" className="py-20 lg:py-24">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <Badge variant="outline" className="mb-4 text-xs">Our methodology</Badge>
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">
              The 20 Agent-Readiness Rules
            </h2>
            <p className="text-muted-foreground text-lg">
              Derived from benchmarking 8 agents on what makes documentation easy or hard for them to consume.
              Every rule is concrete, testable, and fixable.
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
                className="bg-card p-4 rounded-xl border hover:border-emerald-500/40 hover:bg-emerald-500/5 transition-all group"
              >
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center flex-shrink-0 group-hover:bg-emerald-500/10 transition-colors">
                    <rule.icon className="w-4 h-4 text-muted-foreground group-hover:text-emerald-600 transition-colors" />
                  </div>
                  <div>
                    <p className="font-medium text-sm leading-tight">
                      <span className="text-muted-foreground mr-1 text-xs">#{rule.id}</span>
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
              Your documentation is scored against all 20 rules. Our optimizer fixes every failing rule automatically.
            </p>
            <Button onClick={scrollToAssessment} className="rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white">
              Test Your Docs Against These Rules
              <ArrowRight className="ml-2 w-4 h-4" />
            </Button>
          </div>
        </div>
      </section>

      {/* Pricing Section - Mintlify-inspired clean pricing */}
      <section id="pricing" className="py-20 lg:py-24 bg-muted/30 border-y">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <Badge variant="outline" className="mb-4 text-xs">Pricing</Badge>
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">Simple, transparent pricing</h2>
            <p className="text-muted-foreground text-lg">
              Free score first. Pay only if you want the optimized docs. One-time payment, no subscriptions.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {/* Free Column */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="bg-card rounded-2xl border p-8 flex flex-col"
            >
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-1">Assessment</h3>
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-bold">$0</span>
                </div>
                <p className="text-sm text-muted-foreground mt-2">See where you stand</p>
              </div>

              <ul className="space-y-3 flex-1">
                {[
                  'Agent-Readiness Score (0-100)',
                  'Letter grade (A+ to F)',
                  '20-rule pass/warning/fail checklist',
                  'Per-rule findings with page counts',
                  'Component breakdown (5 dimensions)',
                ].map((feature) => (
                  <li key={feature} className="flex items-start gap-2.5 text-sm">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>

              <Button
                variant="outline"
                className="w-full mt-8 rounded-xl h-11"
                onClick={scrollToAssessment}
              >
                Get Free Score
              </Button>
            </motion.div>

            {/* Paid Column */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 }}
              className="bg-card rounded-2xl border-2 border-emerald-500 shadow-xl shadow-emerald-500/10 p-8 flex flex-col relative"
            >
              <span className="absolute -top-3.5 left-6 inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-emerald-600 text-white">
                <Sparkles className="w-3 h-3 mr-1" />
                Most popular
              </span>

              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-1">Optimized Documentation</h3>
                <div className="flex items-baseline gap-2">
                  <span className="text-sm text-muted-foreground">from</span>
                  <span className="text-4xl font-bold">$99</span>
                  <span className="text-sm text-muted-foreground">one-time</span>
                </div>
                <p className="text-sm text-muted-foreground mt-2">
                  Price based on documentation size, shown after free scan
                </p>
              </div>

              <ul className="space-y-3 flex-1">
                {[
                  'Everything in the free assessment',
                  'All 20 rules applied to every page',
                  'Every page individually rewritten by AI',
                  'Self-contained sections for RAG retrieval',
                  'Complete code examples with expected output',
                  'Structured parameter tables and error docs',
                  'llms.txt agent entry point included',
                  'Download as ZIP, deploy in minutes',
                ].map((feature) => (
                  <li key={feature} className="flex items-start gap-2.5 text-sm">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>

              <Button
                className="w-full mt-8 rounded-xl h-11 bg-emerald-600 hover:bg-emerald-700 text-white"
                onClick={scrollToAssessment}
              >
                Get Free Score First
                <ArrowRight className="ml-2 w-4 h-4" />
              </Button>
              <p className="text-xs text-center text-muted-foreground mt-3">
                Run the free scan first. Exact price shown after.
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* CTA Banner - Mintlify-style gradient */}
      <section className="py-20 lg:py-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-emerald-600 to-cyan-600 -z-10" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_50%,rgba(255,255,255,0.1),transparent)] -z-10" />

        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4 tracking-tight">
            When someone asks an AI about your product, what does it say?
          </h2>
          <p className="text-emerald-100 text-lg mb-8 max-w-2xl mx-auto">
            If your docs don't follow these 20 rules, agents struggle to answer accurately.
            Worse: they recommend a competitor whose docs are better structured.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button
              size="lg"
              onClick={scrollToAssessment}
              className="rounded-xl bg-white text-emerald-700 hover:bg-emerald-50 h-12 px-8 font-semibold"
            >
              Run Free Assessment
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
          <div className="text-center mb-12">
            <Badge variant="outline" className="mb-4 text-xs">FAQ</Badge>
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight">Frequently asked questions</h2>
          </div>

          <div className="border rounded-2xl bg-card divide-y">
            <div className="px-6">
              <FaqItem
                q="What is the Agent-Readiness Score?"
                a="We evaluate your documentation against 20 concrete rules derived from benchmarking 8 major AI agents (Claude, GPT, Gemini, Grok, and others). Each rule checks something specific: are your sections self-contained? Do code examples include imports? Are parameters in tables or buried in prose? You get a score per rule, per component, and overall."
              />
              <FaqItem
                q="Where do these 20 rules come from?"
                a="We benchmarked 8 major AI agents (Claude, GPT, Gemini, Grok, Kimi, Deepseek, Manus and others) on what actually makes documentation easy or hard for them to consume. The 20 rules are the consensus: specific patterns that all agents agree matter for accurate answers, good code generation, and reliable recommendations."
              />
              <FaqItem
                q="What do I get for free vs. the paid product?"
                a="The free scan gives you your score and a rule-by-rule breakdown showing exactly what's passing and failing. The paid product (from $99) gives you the actual optimized documentation files. Every page is individually rewritten applying all 20 rules, plus an llms.txt agent entry point. Download as ZIP and deploy."
              />
              <FaqItem
                q="How is the price calculated?"
                a="After your free scan, we know exactly how many pages need to be rewritten. Pricing starts at $99. Each page is individually analyzed and rewritten applying all 20 rules. Larger documentation sites cost more because there's more work per page. You'll see your exact price before paying. One-time payment, no subscriptions."
              />
              <FaqItem
                q="How long does it take?"
                a="The free score takes about 60 seconds. After purchase, your optimized documentation is generated in roughly 5 minutes. You'll get a ZIP file you can download immediately."
              />
              <FaqItem
                q="What format are the optimized docs in?"
                a="You get a ZIP containing structured Markdown (.md) files, one per page, rendered HTML previews, an llms.txt agent entry point, and deployment instructions. Works with any docs platform: Mintlify, GitBook, ReadMe, Docusaurus, GitHub Pages, and others."
              />
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-20 lg:py-24 border-t bg-muted/20">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">
            Make your docs a first-class citizen for AI agents
          </h2>
          <p className="text-muted-foreground text-lg mb-8">
            The teams that get this right early will own their category in the agent economy.
            The rest will wonder why agents stopped recommending them.
          </p>
          <Button size="lg" onClick={scrollToAssessment} className="rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white h-12 px-8">
            Run Free Assessment
            <ArrowRight className="ml-2 w-4 h-4" />
          </Button>
        </div>
      </section>

      {/* Footer - Mintlify-style clean footer */}
      <footer className="border-t py-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 bg-emerald-600 rounded-lg flex items-center justify-center">
                <Zap className="w-4 h-4 text-white" />
              </div>
              <span className="text-lg font-semibold">AgentReadiness</span>
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
            </div>

            <p className="text-sm text-muted-foreground">
              &copy; {new Date().getFullYear()} AgentReadiness
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
