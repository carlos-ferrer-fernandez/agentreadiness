import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search,
  Zap,
  TrendingUp,
  Shield,
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
    title: 'Agent Simulation',
    description: 'We test your docs the way AI agents actually consume them. Not how humans read them.',
  },
  {
    icon: Eye,
    title: 'Visibility Score',
    description: 'Find out if agents can see you, recommend you, and answer questions about your product accurately.',
  },
  {
    icon: TrendingUp,
    title: 'Rewritten Documentation',
    description: 'Not a report. Not tips. We rewrite your actual docs so agents can parse them. Download a ZIP and deploy.',
  },
  {
    icon: Shield,
    title: 'Ready to Deploy',
    description: 'Structured markdown files with proper headings, code blocks, and API tables. Works with any docs platform.',
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

    // Validate email (required)
    if (!email || !email.includes('@') || !email.includes('.')) {
      setError('Please enter a valid work email')
      return
    }

    let validatedUrl = url
    if (!url.startsWith('http')) {
      validatedUrl = `https://${url}`
    }

    // Validate URL format
    try {
      new URL(validatedUrl)
    } catch {
      setError('Please enter a valid URL')
      return
    }

    startAssessment()
    setLiveMessage(0)

    // Animate stages while the API call runs, advance every 4s through 11 stages
    const stageInterval = setInterval(() => {
      useAssessmentStore.setState((state) => ({
        assessmentStage: Math.min(state.assessmentStage + 1, assessmentStages.length - 1),
      }))
    }, 4000)

    // Rotate the live status message every 3s
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

      // Map API response to assessment store format
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
      {/* Navigation */}
      <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-primary to-primary/70 rounded-lg flex items-center justify-center">
                <Zap className="w-5 h-5 text-primary-foreground" />
              </div>
              <span className="text-xl font-bold">AgentReadiness</span>
            </div>

            <div className="hidden md:flex items-center gap-6">
              <a href="#rules" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                The 20 Rules
              </a>
              <a href="#how-it-works" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                How it Works
              </a>
              <a href="#pricing" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Pricing
              </a>
              <a href="#faq" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                FAQ
              </a>
              <Button size="sm" onClick={scrollToAssessment}>
                Get Free Score
              </Button>
            </div>

            <button
              className="md:hidden p-2"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
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
              <div className="px-4 py-4 space-y-3">
                <a href="#rules" className="block text-sm text-muted-foreground">The 20 Rules</a>
                <a href="#how-it-works" className="block text-sm text-muted-foreground">How it Works</a>
                <a href="#pricing" className="block text-sm text-muted-foreground">Pricing</a>
                <a href="#faq" className="block text-sm text-muted-foreground">FAQ</a>
                <Button size="sm" className="w-full" onClick={scrollToAssessment}>
                  Get Free Score
                </Button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden py-20 lg:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-sm font-medium mb-6">
                <Shield className="w-4 h-4" />
                Evaluated against 20 rules from 8 major AI agents
              </span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight mb-6"
            >
              Agents read docs, not websites.{' '}
              <span className="bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
                Are yours ready?
              </span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="text-lg md:text-xl text-muted-foreground mb-8"
            >
              Developers increasingly discover tools through AI agents like Claude, GPT and Gemini.
              These agents form opinions based on your documentation structure, not your marketing site.
              We score your docs against <strong>20 rules that all major agents agree on</strong>, then
              rewrite every page so agents can actually parse, cite, and recommend your product.
            </motion.p>

            {/* Assessment Form */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              id="assessment"
              className="max-w-xl mx-auto"
            >
              <div className="bg-card border rounded-xl p-6 shadow-lg">
                <div className="space-y-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                    <Input
                      type="text"
                      placeholder="Enter your docs URL (e.g., docs.example.com)"
                      value={url}
                      onChange={(e) => { setUrl(e.target.value); setError(null) }}
                      className="pl-10 h-12 text-base"
                      onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
                      disabled={isAssessing}
                    />
                  </div>

                  {/* Lead capture fields — shown after URL is entered */}
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
                            className="h-10 text-sm"
                            onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <Input
                            type="text"
                            placeholder="Full name"
                            value={fullName}
                            onChange={(e) => setFullName(e.target.value)}
                            className="h-10 text-sm"
                          />
                          <Input
                            type="text"
                            placeholder="Role (e.g. CTO, DevRel)"
                            value={role}
                            onChange={(e) => setRole(e.target.value)}
                            className="h-10 text-sm"
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
                    className="w-full"
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
                                isComplete ? "bg-green-100" : isActive ? "bg-primary/10" : "bg-muted"
                              )}>
                                {isComplete ? (
                                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                                ) : (
                                  <StageIcon className={cn(
                                    "w-4 h-4",
                                    isActive ? "text-primary" : "text-muted-foreground"
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
                                  className="ml-auto w-4 h-4 border-2 border-primary border-t-transparent rounded-full"
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

              <div className="flex items-center justify-center gap-4 mt-4 text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" />
                  20 rules, 8 agents
                </span>
                <span className="flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" />
                  Powered by GPT-5.4
                </span>
                <span className="flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" />
                  Used by devtool teams
                </span>
              </div>
            </motion.div>
          </div>
        </div>

        {/* Background decoration */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full overflow-hidden -z-10 pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
        </div>
      </section>

      {/* The 20 Rules — Proof of methodology */}
      <section id="rules" className="py-20 border-y bg-muted/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <Badge variant="outline" className="mb-4">Our Methodology</Badge>
            <h2 className="text-3xl font-bold mb-4">
              The 20 Agent-Readiness Rules
            </h2>
            <p className="text-muted-foreground">
              Based on how LLMs are built and how they actually behave. We benchmarked 8 agents
              (Claude, GPT, Gemini, Grok, Kimi, Deepseek, Manus and others) and distilled the
              consensus into 20 concrete, testable rules. Your docs are scored against every one.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {agentReadinessRules.map((rule, index) => (
              <motion.div
                key={rule.id}
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.03 }}
                className="bg-card p-4 rounded-lg border hover:border-primary/50 transition-colors group"
              >
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-md bg-primary/10 flex items-center justify-center flex-shrink-0 group-hover:bg-primary/20 transition-colors">
                    <rule.icon className="w-4 h-4 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium text-sm leading-tight">
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

          <div className="text-center mt-10">
            <p className="text-sm text-muted-foreground mb-4">
              Your documentation is scored against all 20 rules. Our optimizer fixes every failing rule automatically.
            </p>
            <Button onClick={scrollToAssessment}>
              Test Your Docs Against These Rules
              <ArrowRight className="ml-2 w-4 h-4" />
            </Button>
          </div>
        </div>
      </section>

      {/* YC Social Proof — The real thing */}
      <section className="py-16 lg:py-20 border-b bg-muted/30">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-10 items-center">
            {/* Video */}
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

            {/* Quote + Context */}
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
                <span className="text-primary">&ldquo;</span>
                Documentation will be the front door for all of these agents recommending devtools.
                <span className="text-primary">&rdquo;</span>
              </blockquote>

              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-sm font-bold text-primary">
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

              <Button variant="outline" size="sm" onClick={scrollToAssessment}>
                Check if agents can find you
                <ArrowRight className="ml-2 w-3 h-3" />
              </Button>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl font-bold mb-4">
              Your docs are your storefront in the agent economy
            </h2>
            <p className="text-muted-foreground">
              AI agents don't browse your website. They read your documentation.
              If your docs aren't structured for machine consumption, you're invisible
              to the fastest-growing discovery channel in software.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="bg-card p-6 rounded-xl border hover:border-primary/50 transition-colors"
              >
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-primary" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-sm text-muted-foreground">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-20 bg-muted/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl font-bold mb-4">How it works</h2>
            <p className="text-muted-foreground">
              Enter your docs URL. Get a score. See what's failing. Fix everything in one click.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: '01',
                title: 'Get Your Free Score',
                description: 'Enter your docs URL. We evaluate your documentation against 20 agent-readiness rules derived from benchmarking 8 major AI agents (Claude, GPT, Gemini, and more).',
                highlight: 'Free',
              },
              {
                step: '02',
                title: 'See What\'s Failing',
                description: 'Get a rule-by-rule breakdown: which rules pass, which fail, and exactly what agents struggle with. Concrete findings per page, not vague advice.',
                highlight: 'Instant',
              },
              {
                step: '03',
                title: 'Get the Fixed Docs',
                description: 'We rewrite every page applying all 20 rules. You download a ZIP with optimized markdown files + an llms.txt agent entry point. Deploy in minutes.',
                highlight: 'From $109/€99',
              },
            ].map((item, index) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="relative"
              >
                <div className="flex items-center justify-between mb-4">
                  <span className="text-5xl font-bold text-muted/20">{item.step}</span>
                  <Badge variant="secondary">{item.highlight}</Badge>
                </div>
                <h3 className="text-xl font-semibold mb-3">{item.title}</h3>
                <p className="text-muted-foreground">{item.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section — Single Tier */}
      <section id="pricing" className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl font-bold mb-4">Simple pricing, no surprises</h2>
            <p className="text-muted-foreground">
              Get your free score first. If you want the optimized docs, we'll show you the exact price
              based on your documentation size. Starting at $109/€99. One-time payment, no subscriptions.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {/* Free Column */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="bg-card rounded-xl border p-6 flex flex-col"
            >
              <h3 className="text-lg font-semibold">Free Score</h3>
              <div className="mt-2 flex items-baseline">
                <span className="text-3xl font-bold">$0</span>
              </div>
              <p className="text-sm text-muted-foreground mt-2">See where you stand</p>
              <ul className="mt-6 space-y-3 flex-1">
                {[
                  'Agent-Readiness Score (0-100)',
                  'Letter grade (A+ to F)',
                  '20-rule checklist (pass / warning / fail)',
                  'Per-rule findings with page counts',
                  'Component breakdown (5 dimensions)',
                ].map((feature) => (
                  <li key={feature} className="flex items-start gap-2 text-sm">
                    <CheckCircle2 className="w-5 h-5 text-primary flex-shrink-0" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
              <Button
                variant="outline"
                className="w-full mt-6"
                onClick={scrollToAssessment}
              >
                Get Free Score
              </Button>
            </motion.div>

            {/* Report Column */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 }}
              className="bg-card rounded-xl border border-primary ring-1 ring-primary shadow-lg p-6 flex flex-col relative"
            >
              <span className="absolute -top-3 left-4 inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-primary text-primary-foreground">
                <Sparkles className="w-3 h-3 mr-1" />
                The Final Product
              </span>
              <h3 className="text-lg font-semibold">Optimized Documentation</h3>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-sm text-muted-foreground">starting at</span>
                <span className="text-3xl font-bold">$109</span>
                <span className="text-sm text-muted-foreground">/€99</span>
              </div>
              <p className="text-sm text-muted-foreground mt-2">
                Exact price calculated after your free scan, based on documentation size
              </p>
              <ul className="mt-6 space-y-3 flex-1">
                {[
                  'Everything in Free Score',
                  'All 20 rules applied to every page',
                  'Every page rewritten by GPT-5.4',
                  'Self-contained sections for RAG retrieval',
                  'Complete code examples (imports + expected output)',
                  'Structured parameter tables and error docs',
                  'llms.txt agent entry point included',
                  'Download as ZIP, deploy in minutes',
                ].map((feature) => (
                  <li key={feature} className="flex items-start gap-2 text-sm">
                    <CheckCircle2 className="w-5 h-5 text-primary flex-shrink-0" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
              <Button
                className="w-full mt-6"
                onClick={scrollToAssessment}
              >
                Get Free Score First
                <ArrowRight className="ml-2 w-4 h-4" />
              </Button>
              <p className="text-xs text-center text-muted-foreground mt-3">
                Run the free scan first. We'll calculate the exact price based on your documentation size.
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-primary/5 border-y">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <Bot className="w-12 h-12 text-primary mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-4">
            When someone asks an AI agent about your product, what does it say?
          </h2>
          <p className="text-muted-foreground mb-2">
            If your documentation doesn't follow these 20 rules, agents struggle to answer
            accurately. Worse: they recommend a competitor whose docs are better structured.
          </p>
          <p className="text-sm text-muted-foreground mb-8">
            Check your score. See exactly which rules are failing. Fix them in one click.
          </p>
          <Button size="lg" onClick={scrollToAssessment}>
            Run Free Assessment
            <ArrowRight className="ml-2 w-4 h-4" />
          </Button>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="py-20 bg-muted/30">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center mb-12">Frequently Asked Questions</h2>
          <div className="space-y-6">
            {[
              {
                q: 'What is the Agent-Readiness Score?',
                a: 'We evaluate your documentation against 20 concrete rules derived from benchmarking 8 major AI agents (Claude, GPT, Gemini, Grok, and others). Each rule checks something specific: are your sections self-contained? Do code examples include imports? Are parameters in tables or buried in prose? You get a score per rule, per component, and overall.',
              },
              {
                q: 'Where do these 20 rules come from?',
                a: 'We benchmarked 8 major AI agents (Claude, GPT, Gemini, Grok, Kimi, Deepseek, Manus and others) on what actually makes documentation easy or hard for them to consume. The 20 rules are the consensus: specific patterns that all agents agree matter for accurate answers, good code generation, and reliable recommendations. Grounded in how LLMs are built and how they actually behave.',
              },
              {
                q: 'What do I get for free vs. the paid product?',
                a: 'The free scan gives you your score and a rule-by-rule breakdown showing exactly what\'s passing and failing. The paid product (from $109/€99) gives you the actual optimized documentation files. Every page is individually rewritten by GPT-5.4 applying all 20 rules, plus an llms.txt agent entry point. Download as ZIP and deploy.',
              },
              {
                q: 'How is the price calculated?',
                a: 'After your free scan, we know exactly how many pages need to be rewritten. Pricing starts at $109/€99. Each page is individually analyzed and rewritten by GPT-5.4 applying all 20 rules. Larger documentation sites cost more because there\'s more work per page. You\'ll see your exact price before paying. One-time payment, no subscriptions.',
              },
              {
                q: 'How long does it take?',
                a: 'The free score takes about 60 seconds. After purchase, your optimized documentation is generated in roughly 5 minutes. You\'ll get a ZIP file you can download immediately.',
              },
              {
                q: 'What format are the optimized docs in?',
                a: 'You get a ZIP containing structured Markdown (.md) files, one per page, plus a README overview and implementation guide. These work with any docs platform: GitHub Pages, Netlify, Vercel, ReadMe, GitBook, and others.',
              },
            ].map((faq, index) => (
              <div key={index} className="bg-card rounded-lg p-6 border">
                <h3 className="font-semibold mb-2">{faq.q}</h3>
                <p className="text-sm text-muted-foreground">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA Section */}
      <section className="py-20">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold mb-4">
            Make your docs a first-class citizen for AI agents.
          </h2>
          <p className="text-muted-foreground mb-8">
            The teams that get this right early will own their category in the agent economy.
            The rest will wonder why agents stopped recommending them.
          </p>
          <Button size="lg" onClick={scrollToAssessment}>
            Run Free Assessment
            <ArrowRight className="ml-2 w-4 h-4" />
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <Zap className="w-5 h-5 text-primary-foreground" />
              </div>
              <span className="text-lg font-bold">AgentReadiness</span>
            </div>
            <p className="text-sm text-muted-foreground">
              &copy; {new Date().getFullYear()} AgentReadiness. All rights reserved.
            </p>
            <div className="flex gap-6">
              <a href="#" className="text-sm text-muted-foreground hover:text-foreground">
                Privacy
              </a>
              <a href="#" className="text-sm text-muted-foreground hover:text-foreground">
                Terms
              </a>
              <a href="#" className="text-sm text-muted-foreground hover:text-foreground">
                Contact
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
