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
  Star
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
    icon: Search,
    title: 'Agent Simulation',
    description: 'Test how AI agents interact with your documentation using realistic developer personas.',
  },
  {
    icon: Zap,
    title: 'Friendliness Score',
    description: 'Get a single composite score (0-100) measuring agent-readiness across 5 key dimensions.',
  },
  {
    icon: TrendingUp,
    title: 'Actionable Insights',
    description: 'Receive prioritized recommendations with estimated impact and implementation effort.',
  },
  {
    icon: Shield,
    title: 'Competitive Benchmark',
    description: 'Compare your documentation against competitors and industry leaders.',
  },
]

const assessmentStages = [
  { name: 'Discovering pages', icon: Search },
  { name: 'Analyzing structure', icon: FileText },
  { name: 'Simulating queries', icon: Zap },
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
              <a href="#features" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Features
              </a>
              <a href="#pricing" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Pricing
              </a>
              <a href="#how-it-works" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                How it Works
              </a>
              <Button variant="outline" size="sm" onClick={() => navigate('/dashboard')}>
                Sign In
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
                <a href="#features" className="block text-sm text-muted-foreground">Features</a>
                <a href="#pricing" className="block text-sm text-muted-foreground">Pricing</a>
                <a href="#how-it-works" className="block text-sm text-muted-foreground">How it Works</a>
                <Button variant="outline" size="sm" className="w-full" onClick={() => navigate('/dashboard')}>
                  Sign In
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
                <Sparkles className="w-4 h-4" />
                Free Assessment — No Credit Card Required
              </span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight mb-6"
            >
              Is your documentation{' '}
              <span className="bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
                AI-ready?
              </span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="text-lg md:text-xl text-muted-foreground mb-8"
            >
              AI agents are becoming the primary way developers discover tools.
              Get your <strong>free Friendliness Score</strong> and see how you compare
              to industry leaders.
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
                        Analyzing...
                      </>
                    ) : (
                      <>
                        Get Free Score
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
                          Crawling and analyzing your documentation...
                        </p>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              <p className="text-xs text-muted-foreground mt-4">
                <CheckCircle2 className="w-3 h-3 inline mr-1" />
                Free assessment - No signup required - Real analysis of your docs
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

      {/* Social Proof */}
      <section className="py-12 border-y bg-muted/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-muted-foreground mb-6">
            Trusted by developer-focused companies
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
            <h2 className="text-3xl font-bold mb-4">Everything you need for agent-ready docs</h2>
            <p className="text-muted-foreground">
              Comprehensive analysis and optimization tools to ensure your documentation
              performs well when consumed by AI agents.
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
              Get your Friendliness Score in minutes, then unlock your action plan.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: '01',
                title: 'Free Assessment',
                description: 'Enter your docs URL and get an instant Friendliness Score with component breakdown.',
                highlight: 'Free',
              },
              {
                step: '02',
                title: 'Unlock Action Plan',
                description: 'Purchase a plan to get detailed recommendations with step-by-step improvement guide.',
                highlight: 'From $49',
              },
              {
                step: '03',
                title: 'Implement & Improve',
                description: 'Follow the playbook to improve your score and attract more developers via AI agents.',
                highlight: 'Track Progress',
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

      {/* Pricing Section */}
      <section id="pricing" className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl font-bold mb-4">Unlock your action plan</h2>
            <p className="text-muted-foreground">
              Get detailed recommendations and step-by-step guidance to improve your score.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {[
              {
                name: 'Free Assessment',
                price: '$0',
                period: '',
                description: 'Get started with your Friendliness Score',
                features: [
                  'Friendliness Score (0-100)',
                  'Letter grade (A+ to F)',
                  'Component breakdown',
                  'Top 3 issues identified',
                  'Industry benchmark comparison',
                ],
                cta: 'Start Free',
                variant: 'outline' as const,
                highlighted: false,
              },
              {
                name: 'Starter Plan',
                price: '$49',
                period: '/one-time',
                description: 'Complete action plan for your docs',
                features: [
                  'Everything in Free',
                  'Detailed recommendations (10+)',
                  'Step-by-step improvement guide',
                  'Code examples & templates',
                  'Priority support (email)',
                  'PDF report download',
                ],
                cta: 'Get Action Plan',
                variant: 'default' as const,
                highlighted: true,
              },
              {
                name: 'Growth Plan',
                price: '$149',
                period: '/one-time',
                description: 'Advanced optimization for teams',
                features: [
                  'Everything in Starter',
                  'Unlimited recommendations',
                  'Competitor deep-dive analysis',
                  'Custom improvement roadmap',
                  '1-on-1 consultation (30 min)',
                  'Slack support (1 week)',
                ],
                cta: 'Get Full Analysis',
                variant: 'outline' as const,
                highlighted: false,
              },
            ].map((plan, index) => (
              <motion.div
                key={plan.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className={cn(
                  "bg-card rounded-xl border p-6 flex flex-col",
                  plan.highlighted && "border-primary ring-1 ring-primary shadow-lg scale-105"
                )}
              >
                {plan.highlighted && (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary text-primary-foreground w-fit mb-4">
                    <Star className="w-3 h-3 mr-1" />
                    Most Popular
                  </span>
                )}
                <h3 className="text-lg font-semibold">{plan.name}</h3>
                <div className="mt-2 flex items-baseline">
                  <span className="text-3xl font-bold">{plan.price}</span>
                  <span className="text-muted-foreground ml-1">{plan.period}</span>
                </div>
                <p className="text-sm text-muted-foreground mt-2">{plan.description}</p>
                <ul className="mt-6 space-y-3 flex-1">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2 text-sm">
                      <CheckCircle2 className="w-5 h-5 text-primary flex-shrink-0" />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
                <Button
                  variant={plan.variant}
                  className="w-full mt-6"
                  onClick={scrollToAssessment}
                >
                  {plan.cta}
                </Button>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-20 bg-muted/30">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center mb-12">Frequently Asked Questions</h2>
          <div className="space-y-6">
            {[
              {
                q: 'What is the Friendliness Score?',
                a: 'The Friendliness Score is a composite metric (0-100) that measures how well your documentation performs when consumed by AI agents. It considers answer accuracy, context utilization, response latency, citation quality, and code executability.',
              },
              {
                q: 'How long does the assessment take?',
                a: 'The free assessment typically takes 30-90 seconds depending on your documentation size. We crawl your docs, analyze the content structure, and calculate your score in real-time.',
              },
              {
                q: 'What do I get with the free assessment?',
                a: 'You get your Friendliness Score, letter grade, component breakdown, top 3 issues identified, and a comparison to industry benchmarks. The detailed action plan with step-by-step recommendations requires a paid plan.',
              },
              {
                q: 'Is my data secure?',
                a: 'Yes. We only analyze publicly available documentation. We do not store any sensitive information, and all analysis data is encrypted in transit and at rest.',
              },
              {
                q: 'Can I get a refund?',
                a: 'Yes, we offer a 7-day money-back guarantee if you are not satisfied with your action plan.',
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

      {/* CTA Section */}
      <section className="py-20">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to optimize your docs for AI agents?</h2>
          <p className="text-muted-foreground mb-8">
            Get your free Friendliness Score in under a minute. No signup required.
          </p>
          <Button size="lg" onClick={scrollToAssessment}>
            Get Free Assessment
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
