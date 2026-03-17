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
  EyeOff,
  Bot
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
    description: 'We test your docs the way AI agents actually consume them — not how humans read them.',
  },
  {
    icon: Eye,
    title: 'Visibility Score',
    description: 'Find out if AI agents can see you, recommend you, and answer questions about your product.',
  },
  {
    icon: TrendingUp,
    title: 'Actionable Playbook',
    description: 'Get a complete, prioritised action plan — not vague tips. Before/after examples included.',
  },
  {
    icon: Shield,
    title: 'Competitor Intel',
    description: 'See exactly how your docs stack up against competitors in the eyes of AI agents.',
  },
]

const assessmentStages = [
  { name: 'Discovering pages', icon: Search },
  { name: 'Analyzing structure', icon: FileText },
  { name: 'Simulating AI agents', icon: Bot },
  { name: 'Calculating score', icon: BarChart3 },
]

export function LandingPage() {
  const navigate = useNavigate()
  const [url, setUrl] = useState('')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)

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

    // Animate stages while the API call runs
    const stageInterval = setInterval(() => {
      useAssessmentStore.setState((state) => ({
        assessmentStage: Math.min(state.assessmentStage + 1, assessmentStages.length - 1),
      }))
    }, 3000)

    try {
      const response = await assessmentsApi.analyze({ url: validatedUrl })
      clearInterval(stageInterval)

      // Map API response to assessment store format
      const data = response.data
      setAssessmentResult({
        id: data.id,
        url: data.url,
        siteName: data.site_name,
        score: data.score,
        grade: data.grade,
        components: {
          accuracy: data.components.accuracy || 0,
          contextUtilization: data.components.context_utilization || 0,
          latency: data.components.latency || 0,
          citationQuality: data.components.citation_quality || 0,
          codeExecutability: data.components.code_executability || 0,
        },
        queryCount: data.query_count,
        passRate: data.pass_rate,
        avgLatencyMs: data.avg_latency_ms,
        pageCount: data.page_count,
        topIssues: data.top_issues.map((issue: any) => ({
          category: issue.category,
          title: issue.title,
          severity: issue.severity as 'high' | 'medium' | 'low',
        })),
        estimatedPriceEur: data.estimated_price_eur,
        hasPaid: data.has_paid,
        createdAt: data.created_at,
      })

      navigate('/assessment')
    } catch (err: any) {
      clearInterval(stageInterval)
      const message = err.response?.data?.detail || 'Analysis failed. Please check the URL and try again.'
      setAssessmentError(message)
      setError(message)
    }
  }, [url, isAssessing, startAssessment, setAssessmentResult, setAssessmentError, navigate])

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
              <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-destructive/10 text-destructive text-sm font-medium mb-6">
                <AlertTriangle className="w-4 h-4" />
                68% of documentation is invisible to AI agents
              </span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight mb-6"
            >
              AI agents are the new buyers.{' '}
              <span className="bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
                Can they find you?
              </span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="text-lg md:text-xl text-muted-foreground mb-8"
            >
              For every $1 spent on software, $6 is spent on services — and AI agents
              are deciding where that money goes. Get your <strong>free Visibility Score</strong> and
              find out if you're winning or losing in the agent economy.
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

                  {error && (
                    <p className="text-sm text-red-600">{error}</p>
                  )}

                  <Button
                    size="lg"
                    onClick={handleAnalyze}
                    disabled={isAssessing || !url}
                    className="w-full"
                  >
                    {isAssessing ? (
                      <>
                        <Clock className="mr-2 w-4 h-4 animate-spin" />
                        Scanning...
                      </>
                    ) : (
                      <>
                        Check My Visibility — Free
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
                        <p className="text-xs text-muted-foreground text-center mt-2">
                          Simulating how AI agents see your documentation...
                        </p>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              <p className="text-xs text-muted-foreground mt-4">
                <CheckCircle2 className="w-3 h-3 inline mr-1" />
                Free score in 60 seconds — No signup — No credit card
              </p>
            </motion.div>
          </div>
        </div>

        {/* Background decoration */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full overflow-hidden -z-10 pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
        </div>
      </section>

      {/* Urgency Banner */}
      <section className="py-8 border-y bg-destructive/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-3 gap-6 text-center">
            <div>
              <div className="text-3xl font-bold text-destructive mb-1">6x</div>
              <p className="text-sm text-muted-foreground">
                Services budget vs software budget — agents decide where it goes
              </p>
            </div>
            <div>
              <div className="text-3xl font-bold text-destructive mb-1">68%</div>
              <p className="text-sm text-muted-foreground">
                of docs score below C — effectively invisible to AI agents
              </p>
            </div>
            <div>
              <div className="text-3xl font-bold text-destructive mb-1">2025</div>
              <p className="text-sm text-muted-foreground">
                The year AI agents become the primary discovery channel
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Social Proof */}
      <section className="py-12 border-b bg-muted/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-muted-foreground mb-6">
            Companies already optimising for the agent economy
          </p>
          <div className="flex flex-wrap justify-center items-center gap-8 md:gap-12 opacity-50">
            {['Resend', 'Stripe', 'Vercel', 'Supabase', 'Linear'].map((company) => (
              <span key={company} className="text-lg font-semibold text-muted-foreground">
                {company}
              </span>
            ))}
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
              AI agents don't browse your website — they read your documentation.
              If your docs aren't optimised, you're invisible to the fastest-growing buyer channel.
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
              60 seconds to your score. One click to your complete playbook.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: '01',
                title: 'Get Your Free Score',
                description: 'Enter your docs URL. We simulate real AI agents consuming your documentation and grade you across 5 dimensions.',
                highlight: 'Free',
              },
              {
                step: '02',
                title: 'See Where You Stand',
                description: 'See how you compare against industry leaders and competitors. Find out what\'s costing you agent visibility.',
                highlight: 'Instant',
              },
              {
                step: '03',
                title: 'Get Your Playbook',
                description: 'Unlock your complete Agent-Readiness Report with prioritised fixes, code examples, and before/after previews. Price based on your docs size.',
                highlight: 'From €49',
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
            <h2 className="text-3xl font-bold mb-4">One report. Priced to your docs.</h2>
            <p className="text-muted-foreground">
              No tiers. No subscriptions. No upsells. Price scales with your documentation
              size — starting at just €49 for small docs.
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
                  'Friendliness Score (0-100)',
                  'Letter grade (A+ to F)',
                  'Component breakdown (5 dimensions)',
                  'Top 3 issues identified',
                  'Industry benchmark comparison',
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
                Complete Playbook
              </span>
              <h3 className="text-lg font-semibold">Agent-Readiness Report</h3>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-sm text-muted-foreground">from</span>
                <span className="text-3xl font-bold">€49</span>
              </div>
              <p className="text-sm text-muted-foreground mt-2">
                Price scales with your docs size — 3x our AI analysis cost
              </p>
              <ul className="mt-6 space-y-3 flex-1">
                {[
                  'Everything in Free Score',
                  'Deep-dive analysis across all 5 dimensions',
                  '10+ prioritised recommendations',
                  'Before/after code examples',
                  'Competitor benchmarking deep-dive',
                  'Implementation templates',
                  'Downloadable PDF report',
                  '30-day email support',
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
                Exact price shown after free scan. 7-day money-back guarantee.
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* FOMO Section */}
      <section className="py-16 bg-primary/5 border-y">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <EyeOff className="w-12 h-12 text-destructive mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-4">
            If AI agents can't parse your docs, they can't recommend you.
          </h2>
          <p className="text-muted-foreground mb-2">
            Every day you wait, your competitors are getting optimised. AI agents
            are already choosing who to recommend for development tools, APIs, and services.
          </p>
          <p className="text-sm text-muted-foreground mb-8">
            The companies that move first will own the agent economy. The rest will wonder where their traffic went.
          </p>
          <Button size="lg" onClick={scrollToAssessment}>
            Check My Visibility Now
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
                q: 'What is the Friendliness Score?',
                a: 'It\'s a composite metric (0-100) that measures how well your documentation performs when consumed by AI agents. We simulate real agent interactions and grade you on answer accuracy, context utilisation, response speed, citation quality, and code executability.',
              },
              {
                q: 'Why should I care about AI agent visibility?',
                a: 'AI agents are rapidly becoming the primary way developers discover and evaluate tools. Sequoia estimates that for every $1 spent on software, $6 is spent on services — and AI agents are increasingly deciding where that budget goes. If they can\'t read your docs, they can\'t recommend you.',
              },
              {
                q: 'What do I get for free vs. the paid report?',
                a: 'The free scan gives you your score, letter grade, component breakdown, top 3 issues, and industry benchmarks. The Agent-Readiness Report (from €49) gives you the complete playbook: deep-dive analysis, 10+ prioritised recommendations with before/after examples, competitor analysis, implementation templates, and a downloadable PDF.',
              },
              {
                q: 'How is the price calculated?',
                a: 'The price scales with your documentation size — it\'s 3x our actual AI analysis cost. Small docs (under 25 pages) start at €49. Larger documentation sites cost more because they require more AI processing. You\'ll see your exact price after the free scan. No subscriptions, no hidden fees.',
              },
              {
                q: 'How long does it take?',
                a: 'The free score takes about 60 seconds. The full report is generated instantly after purchase — no waiting, no scheduling calls.',
              },
              {
                q: 'Can I get a refund?',
                a: 'Yes. 7-day money-back guarantee, no questions asked.',
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
            Don't let AI agents forget you exist.
          </h2>
          <p className="text-muted-foreground mb-8">
            Get your free Visibility Score in 60 seconds. No signup. No credit card.
          </p>
          <Button size="lg" onClick={scrollToAssessment}>
            Check My Visibility — Free
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
