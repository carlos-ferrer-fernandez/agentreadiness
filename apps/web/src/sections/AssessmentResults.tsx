import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import {
  Lock,
  Unlock,
  CheckCircle2,
  Zap,
  ChevronDown,
  ChevronUp,
  Sparkles,
  CreditCard,
  Shield,
  Clock,
  Gift,
  AlertTriangle,
  ArrowRight,
  EyeOff,
  FileText
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { ScoreCard } from '@/components/score/ScoreCard'
import { cn, getScoreInterpretation } from '@/lib/utils'
import { useAssessmentStore } from '@/store/assessment'
import { useUIStore } from '@/store'
import { assessmentsApi, paymentsApi } from '@/lib/api'

const componentDescriptions: Record<string, string> = {
  accuracy: 'How correct are the answers generated from your documentation?',
  contextUtilization: 'How efficiently can agents find relevant information?',
  latency: 'How quickly can agents retrieve and process information?',
  citationQuality: 'How accurate are the source citations in responses?',
  codeExecutability: 'How many code examples run without errors?',
}

const reportFeatures = [
  'Deep-dive analysis across all 5 dimensions',
  '10+ prioritised recommendations',
  'Before/after code examples for every fix',
  'Competitor benchmarking deep-dive',
  'Implementation templates & snippets',
  'Downloadable PDF report',
  '30-day email support',
]

const recommendationsPreview = [
  {
    category: 'Structure',
    title: 'Improve documentation hierarchy',
    impact: 'high',
    effort: 'medium',
    description: 'Your documentation lacks clear hierarchical structure, making it difficult for AI agents to understand relationships between topics.',
    preview: 'Add a clear table of contents with nested sections...',
  },
  {
    category: 'Content',
    title: 'Add more code examples',
    impact: 'high',
    effort: 'low',
    description: 'AI agents struggle to provide complete answers without sufficient code examples.',
    preview: 'Include at least 3 code examples for each major feature...',
  },
  {
    category: 'Search',
    title: 'Enhance search functionality',
    impact: 'medium',
    effort: 'medium',
    description: 'The current search implementation returns irrelevant results for common queries.',
    preview: 'Implement semantic search with vector embeddings...',
  },
]

export function AssessmentResults() {
  const navigate = useNavigate()
  const { addNotification } = useUIStore()
  const {
    currentAssessment,
    showPaywall,
    markAsPaid,
    hidePaywallModal,
  } = useAssessmentStore()

  const [expandedIssue, setExpandedIssue] = useState<number | null>(null)
  const [isProcessingPayment, setIsProcessingPayment] = useState(false)
  const [showPaymentSuccess, setShowPaymentSuccess] = useState(false)
  const [promoCode, setPromoCode] = useState('')
  const [promoError, setPromoError] = useState<string | null>(null)
  const [showPromoInput, setShowPromoInput] = useState(false)
  const [isApplyingPromo, setIsApplyingPromo] = useState(false)

  if (!currentAssessment) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">No Assessment Found</h1>
          <p className="text-muted-foreground mb-6">Start a new assessment to see your results.</p>
          <Button onClick={() => navigate('/')}>Start Assessment</Button>
        </div>
      </div>
    )
  }

  const handlePayment = async () => {
    if (!currentAssessment) return

    setIsProcessingPayment(true)

    try {
      const response = await paymentsApi.createCheckout({
        assessment_id: currentAssessment.id,
        success_url: `${window.location.origin}/assessment`,
        cancel_url: `${window.location.origin}/assessment`,
      })

      // Redirect to Stripe checkout
      if (response.data.url) {
        window.location.href = response.data.url
      }
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Payment failed. Please try again.'
      addNotification({ type: 'error', message })
    } finally {
      setIsProcessingPayment(false)
    }
  }

  const handlePromoCode = async () => {
    if (!promoCode || !currentAssessment) return

    setIsApplyingPromo(true)
    setPromoError(null)

    try {
      await assessmentsApi.verifyPromo(currentAssessment.id, promoCode)
      markAsPaid()
      hidePaywallModal()
      setPromoCode('')
      setShowPromoInput(false)
      addNotification({
        type: 'success',
        message: 'Promo code applied! Your report is now unlocked.',
      })
    } catch (err: any) {
      setPromoError(err.response?.data?.detail || 'Invalid promo code')
    } finally {
      setIsApplyingPromo(false)
    }
  }

  const {
    score,
    grade,
    components,
    siteName,
    url,
    queryCount,
    passRate,
    avgLatencyMs,
    pageCount,
    topIssues,
    estimatedPriceEur,
    hasPaid
  } = currentAssessment

  const price = estimatedPriceEur || 49

  // Dynamic FOMO message based on score
  const getFOMOMessage = (score: number): string => {
    if (score >= 90) return 'Strong position — but your competitors are catching up. Stay ahead.'
    if (score >= 80) return 'Good foundation, but significant gaps are costing you agent recommendations.'
    if (score >= 70) return 'Below average. AI agents are likely recommending your competitors instead.'
    if (score >= 60) return 'Concerning. You\'re effectively invisible to most AI agents right now.'
    return 'Critical. AI agents cannot meaningfully interact with your documentation.'
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigate('/')}>
              <div className="w-8 h-8 bg-gradient-to-br from-primary to-primary/70 rounded-lg flex items-center justify-center">
                <Zap className="w-5 h-5 text-primary-foreground" />
              </div>
              <span className="text-xl font-bold">AgentReadiness</span>
            </div>
            <Button variant="outline" size="sm" onClick={() => navigate('/')}>
              New Assessment
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Results Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-2">
            <Badge variant="outline" className="text-xs">Assessment Complete</Badge>
            <span className="text-sm text-muted-foreground">
              {new Date(currentAssessment.createdAt).toLocaleDateString()}
            </span>
          </div>
          <h1 className="text-3xl font-bold">{siteName}</h1>
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-muted-foreground hover:text-primary transition-colors"
          >
            {url}
          </a>
        </div>

        {/* FOMO Banner (only if not paid) */}
        {!hasPaid && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8 p-4 rounded-lg border border-destructive/30 bg-destructive/5"
          >
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-medium text-sm">{getFOMOMessage(score)}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Get your complete Agent-Readiness Report to fix this.
                </p>
              </div>
              <Button
                size="sm"
                onClick={() => useAssessmentStore.getState().showPaywallModal()}
              >
                Get Report — €{price}
              </Button>
            </div>
          </motion.div>
        )}

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Left Column - Score & Stats */}
          <div className="space-y-6">
            <Card>
              <CardContent className="pt-6">
                <div className="flex justify-center">
                  <ScoreCard
                    score={score}
                    grade={grade}
                    components={components}
                    size="lg"
                  />
                </div>
                <div className="mt-6 p-4 bg-muted rounded-lg">
                  <p className="text-sm text-muted-foreground text-center">
                    {getScoreInterpretation(grade)}
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium">Quick Stats</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Pages Analyzed</span>
                  <span className="font-medium">{pageCount}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Queries Tested</span>
                  <span className="font-medium">{queryCount}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Pass Rate</span>
                  <span className="font-medium">{Math.round(passRate * 100)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Avg Response Time</span>
                  <span className="font-medium">{(avgLatencyMs / 1000).toFixed(2)}s</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium">Industry Comparison</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {[
                    { name: 'Your Score', score, highlight: true },
                    { name: 'Top 10%', score: 92, highlight: false },
                    { name: 'Industry Avg', score: 68, highlight: false },
                    { name: 'Bottom 10%', score: 45, highlight: false },
                  ].map((item) => (
                    <div key={item.name} className="flex items-center gap-3">
                      <span className={cn(
                        "text-sm w-24",
                        item.highlight && "font-medium"
                      )}>
                        {item.name}
                      </span>
                      <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className={cn(
                            "h-full rounded-full transition-all duration-500",
                            item.highlight ? "bg-primary" : "bg-muted-foreground/30"
                          )}
                          style={{ width: `${item.score}%` }}
                        />
                      </div>
                      <span className={cn(
                        "text-sm w-10 text-right",
                        item.highlight && "font-bold"
                      )}>
                        {item.score}
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Middle Column - Component Breakdown */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Component Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {Object.entries(components).map(([key, value]) => (
                    <div key={key} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="font-medium capitalize">
                            {key.replace(/([A-Z])/g, ' $1').trim()}
                          </span>
                          <p className="text-xs text-muted-foreground">
                            {componentDescriptions[key]}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={cn(
                            "text-lg font-bold",
                            value >= 80 ? "text-green-600" :
                            value >= 60 ? "text-yellow-600" : "text-red-600"
                          )}>
                            {value}%
                          </span>
                        </div>
                      </div>
                      <Progress value={value} className="h-2" />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Top Issues Identified</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {topIssues.map((issue, index) => (
                    <div
                      key={index}
                      className="border rounded-lg overflow-hidden"
                    >
                      <button
                        onClick={() => setExpandedIssue(expandedIssue === index ? null : index)}
                        className="w-full flex items-center justify-between p-4 hover:bg-muted/50 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <Badge variant={
                            issue.severity === 'high' ? 'destructive' :
                            issue.severity === 'medium' ? 'warning' : 'secondary'
                          }>
                            {issue.severity}
                          </Badge>
                          <span className="font-medium text-left">{issue.title}</span>
                        </div>
                        {expandedIssue === index ? (
                          <ChevronUp className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                        )}
                      </button>
                      <AnimatePresence>
                        {expandedIssue === index && (
                          <motion.div
                            initial={{ height: 0 }}
                            animate={{ height: 'auto' }}
                            exit={{ height: 0 }}
                            className="overflow-hidden"
                          >
                            <div className="p-4 pt-0 border-t bg-muted/30">
                              <p className="text-sm text-muted-foreground mb-3">
                                Full analysis, root cause, and step-by-step fix included
                                in your Agent-Readiness Report.
                              </p>
                              {!hasPaid && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => useAssessmentStore.getState().showPaywallModal()}
                                >
                                  <Lock className="w-3 h-3 mr-2" />
                                  Unlock in Report
                                </Button>
                              )}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Recommendations Preview */}
            <Card className={cn(!hasPaid && "relative")}>
              {!hasPaid && (
                <div className="absolute inset-0 bg-background/80 backdrop-blur-sm z-10 flex flex-col items-center justify-center rounded-lg">
                  <div className="text-center p-6">
                    <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                      <Lock className="w-8 h-8 text-primary" />
                    </div>
                    <h3 className="text-xl font-bold mb-2">Your Playbook Is Ready</h3>
                    <p className="text-muted-foreground mb-2 max-w-sm">
                      {recommendationsPreview.length}+ prioritised recommendations with
                      code examples and before/after previews.
                    </p>
                    <p className="text-xs text-muted-foreground mb-6">
                      Less than 1 hour of a developer's time.
                    </p>
                    <Button onClick={() => useAssessmentStore.getState().showPaywallModal()}>
                      <Unlock className="w-4 h-4 mr-2" />
                      Get Report — €{price}
                    </Button>
                  </div>
                </div>
              )}

              <CardHeader>
                <CardTitle>Detailed Recommendations</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recommendationsPreview.map((rec, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <Badge variant="outline" className="mb-2">{rec.category}</Badge>
                          <h4 className="font-medium">{rec.title}</h4>
                        </div>
                        <div className="flex gap-2">
                          <Badge variant={rec.impact === 'high' ? 'destructive' : 'secondary'}>
                            {rec.impact} impact
                          </Badge>
                          <Badge variant="outline">{rec.effort} effort</Badge>
                        </div>
                      </div>
                      <p className="text-sm text-muted-foreground mb-3">{rec.description}</p>
                      <div className="bg-muted rounded-lg p-3">
                        <p className="text-sm font-medium mb-1">Recommended Action:</p>
                        <p className="text-sm text-muted-foreground">{rec.preview}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>

      {/* Paywall Modal — Single Tier, No Selection */}
      <Dialog open={showPaywall} onOpenChange={hidePaywallModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-2xl">Get Your Agent-Readiness Report</DialogTitle>
            <DialogDescription>
              Your complete playbook to dominate the agent economy. One price. No subscriptions.
            </DialogDescription>
          </DialogHeader>

          {/* Score reminder */}
          <div className="flex items-center gap-4 p-4 rounded-lg bg-muted">
            <div className="text-center">
              <div className={cn(
                "text-2xl font-bold",
                score >= 80 ? "text-green-600" :
                score >= 60 ? "text-yellow-600" : "text-red-600"
              )}>
                {score}
              </div>
              <div className="text-xs text-muted-foreground">Your Score</div>
            </div>
            <div className="flex-1 text-sm text-muted-foreground">
              {getFOMOMessage(score)}
            </div>
          </div>

          {/* What's included */}
          <div className="space-y-3">
            <h4 className="font-medium text-sm">What's included:</h4>
            <ul className="space-y-2">
              {reportFeatures.map(f => (
                <li key={f} className="flex items-center gap-2 text-sm">
                  <CheckCircle2 className="w-4 h-4 text-green-600 flex-shrink-0" />
                  {f}
                </li>
              ))}
            </ul>
          </div>

          <div className="mt-4 space-y-4">
            {/* Price */}
            <div className="text-center">
              <div className="flex items-baseline justify-center gap-2">
                <span className="text-3xl font-bold">€{price}</span>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Based on {pageCount} pages analysed. One-time payment. No subscription.
              </p>
            </div>

            <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
              <Shield className="w-4 h-4" />
              7-day money-back guarantee
            </div>

            <Button
              className="w-full"
              size="lg"
              onClick={handlePayment}
              disabled={isProcessingPayment}
            >
              {isProcessingPayment ? (
                <>
                  <Clock className="w-4 h-4 mr-2 animate-spin" />
                  Redirecting to checkout...
                </>
              ) : (
                <>
                  <CreditCard className="w-4 h-4 mr-2" />
                  Get My Report — €{price}
                </>
              )}
            </Button>

            <p className="text-xs text-center text-muted-foreground">
              Instant delivery. Less than 1 hour of a developer's time.
            </p>
          </div>

          {/* Promo Code Section */}
          <div className="mt-4 pt-4 border-t">
            {!showPromoInput ? (
              <button
                onClick={() => setShowPromoInput(true)}
                className="text-sm text-muted-foreground hover:text-primary transition-colors flex items-center gap-2"
              >
                <Gift className="w-4 h-4" />
                Have a promo code?
              </button>
            ) : (
              <div className="space-y-3">
                <p className="text-sm font-medium">Enter promo code:</p>
                <div className="flex gap-2">
                  <Input
                    placeholder="Enter code..."
                    value={promoCode}
                    onChange={(e) => { setPromoCode(e.target.value); setPromoError(null) }}
                    onKeyDown={(e) => e.key === 'Enter' && handlePromoCode()}
                    disabled={isApplyingPromo}
                  />
                  <Button onClick={handlePromoCode} variant="outline" disabled={isApplyingPromo}>
                    {isApplyingPromo ? 'Applying...' : 'Apply'}
                  </Button>
                </div>
                {promoError && <p className="text-sm text-red-600">{promoError}</p>}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Payment Success Modal */}
      <Dialog open={showPaymentSuccess} onOpenChange={setShowPaymentSuccess}>
        <DialogContent className="text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Sparkles className="w-8 h-8 text-green-600" />
          </div>
          <DialogTitle className="text-2xl">Your Report Is Ready!</DialogTitle>
          <DialogDescription className="text-lg">
            Your Agent-Readiness Report is unlocked. You now have your complete
            playbook to dominate the agent economy.
          </DialogDescription>
          <div className="mt-6 space-y-3">
            <Button className="w-full" onClick={() => setShowPaymentSuccess(false)}>
              <FileText className="w-4 h-4 mr-2" />
              View My Report
            </Button>
            <Button variant="outline" className="w-full" onClick={() => navigate('/dashboard')}>
              Go to Dashboard
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
