import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import {
  Unlock,
  CheckCircle2,
  Zap,
  ChevronDown,
  ChevronUp,
  CreditCard,
  Shield,
  Clock,
  Gift,
  AlertTriangle,
  ArrowRight,
  Download,
  FileArchive,
  Loader2,
  Package,
  Rocket,
  FileCode,
  XCircle,
  AlertCircle,
  Check,
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

const componentLabels: Record<string, string> = {
  accuracy: 'Answer Accuracy',
  context_utilization: 'Context Retrieval',
  citation_quality: 'Citation & Trust',
  code_executability: 'Code Quality',
  structure: 'Doc Structure',
}

const componentDescriptions: Record<string, string> = {
  accuracy: 'Can AI agents answer correctly from your documentation?',
  context_utilization: 'Can agents find the right information quickly?',
  citation_quality: 'Can agents cite and trust your documentation?',
  code_executability: 'Do your code examples actually work?',
  structure: 'Is your documentation well-structured for machine parsing?',
}

const deliverableFeatures = [
  'Every page individually rewritten applying all 20 rules',
  'Structured markdown files, ready to deploy',
  'Self-contained sections for RAG retrieval',
  'Complete code examples with imports and expected outputs',
  'Structured parameter tables (not prose)',
  'Error documentation with codes, causes, and fixes',
  'llms.txt file generated as agent entry point',
  'Download as ZIP, deploy in minutes',
]

function RuleStatusIcon({ status }: { status: string }) {
  if (status === 'pass') return <Check className="w-4 h-4 text-green-600" />
  if (status === 'warning') return <AlertCircle className="w-4 h-4 text-yellow-600" />
  return <XCircle className="w-4 h-4 text-red-500" />
}

function RuleStatusBadge({ status }: { status: string }) {
  if (status === 'pass') return <Badge className="bg-green-100 text-green-800 border-green-200">Pass</Badge>
  if (status === 'warning') return <Badge className="bg-yellow-100 text-yellow-800 border-yellow-200">Needs Work</Badge>
  return <Badge variant="destructive">Fail</Badge>
}

export function AssessmentResults() {
  const navigate = useNavigate()
  const { addNotification } = useUIStore()
  const {
    currentAssessment,
    showPaywall,
    markAsPaid,
    hidePaywallModal,
    setOptimizationStatus,
    setOptimizationComplete,
  } = useAssessmentStore()

  const [expandedRule, setExpandedRule] = useState<number | null>(null)
  const [isProcessingPayment, setIsProcessingPayment] = useState(false)
  const [promoCode, setPromoCode] = useState('')
  const [promoError, setPromoError] = useState<string | null>(null)
  const [showPromoInput, setShowPromoInput] = useState(false)
  const [isApplyingPromo, setIsApplyingPromo] = useState(false)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Poll optimization status when paid + not complete
  useEffect(() => {
    if (!currentAssessment?.hasPaid) return
    if (!currentAssessment.optimizationStatus) return
    if (currentAssessment.optimizationStatus === 'complete') return
    if (currentAssessment.optimizationStatus === 'failed') return

    const poll = async () => {
      try {
        const res = await assessmentsApi.getOptimizationStatus(currentAssessment.id)
        const data = res.data
        if (data.status === 'complete') {
          setOptimizationComplete(data.metadata || {})
          if (pollingRef.current) clearInterval(pollingRef.current)
        } else if (data.status === 'failed') {
          setOptimizationStatus('failed')
          if (pollingRef.current) clearInterval(pollingRef.current)
        } else {
          setOptimizationStatus(data.status, data.progress, data.stage)
        }
      } catch {
        // Silently retry
      }
    }

    poll()
    pollingRef.current = setInterval(poll, 3000)

    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current)
    }
  }, [currentAssessment?.hasPaid, currentAssessment?.optimizationStatus, currentAssessment?.id])

  // Check for payment return (Stripe redirect)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const sessionId = params.get('session_id')
    if (!sessionId || !currentAssessment || currentAssessment.hasPaid) return

    const verify = async () => {
      try {
        const res = await paymentsApi.verify(sessionId)
        if (res.data.paid) {
          markAsPaid()
          addNotification({
            type: 'success',
            message: 'Payment successful! Your optimized docs are being generated...',
          })
          window.history.replaceState({}, '', window.location.pathname)
        }
      } catch {
        addNotification({
          type: 'error',
          message: 'Could not verify payment. Please contact support.',
        })
      }
    }

    verify()
  }, [currentAssessment?.id])

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
      if (response.data.url) {
        window.location.href = response.data.url
      }
    } catch (err: any) {
      console.error('Payment error:', err.response?.data || err.message || err)
      const detail = err.response?.data?.detail
      const message = detail
        ? `Payment error: ${detail}`
        : err.message?.includes('Network')
          ? 'Cannot reach payment server. Please try again.'
          : 'Payment failed. Please try again.'
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
        message: 'Promo code applied! Your optimized docs are being generated...',
      })
    } catch (err: any) {
      setPromoError(err.response?.data?.detail || 'Invalid promo code')
    } finally {
      setIsApplyingPromo(false)
    }
  }

  const handleDownload = () => {
    if (!currentAssessment) return
    window.open(assessmentsApi.getDownloadUrl(currentAssessment.id), '_blank')
  }

  const {
    score,
    grade,
    components,
    ruleResults,
    siteName,
    url,
    pageCount,
    estimatedPriceEur,
    hasPaid,
    optimizationStatus,
    optimizationProgress,
    optimizationMetadata,
  } = currentAssessment

  const rules = ruleResults || []
  const isOptimizing = hasPaid && optimizationStatus && !['complete', 'failed'].includes(optimizationStatus)
  const isOptimizationDone = hasPaid && optimizationStatus === 'complete'
  const isOptimizationFailed = hasPaid && optimizationStatus === 'failed'

  const passingRules = rules.filter(r => r.status === 'pass').length
  const warningRules = rules.filter(r => r.status === 'warning').length
  const failingRules = rules.filter(r => r.status === 'fail').length

  const getFOMOMessage = (score: number): string => {
    if (score >= 90) return 'Good position, but your competitors are catching up. Stay ahead.'
    if (score >= 80) return 'Solid foundation, but gaps are costing you agent recommendations.'
    if (score >= 70) return 'Below average. AI agents are likely recommending your competitors instead.'
    if (score >= 60) return 'Concerning. You\'re effectively invisible to most AI agents right now.'
    return 'Critical. AI agents cannot meaningfully interact with your documentation.'
  }

  const getOptimizationStageLabel = () => {
    const stage = currentAssessment.optimizationStage
    if (stage === 'crawling') return 'Crawling your documentation...'
    if (stage === 'analyzing') return 'Analyzing against 20 agent-readiness rules...'
    if (stage === 'optimizing') return 'Rewriting pages for AI agents...'
    if (stage === 'generating_llms_txt') return 'Generating llms.txt entry point...'
    if (stage === 'finalizing') return 'Packaging your optimized docs...'
    return 'Generating your optimized documentation...'
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
            <Badge variant="outline" className="text-xs">20 Rules Evaluated</Badge>
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

        {/* Optimization Progress Banner */}
        {isOptimizing && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8 p-6 rounded-lg border border-primary/30 bg-primary/5"
          >
            <div className="flex items-center gap-3 mb-4">
              <Loader2 className="w-5 h-5 text-primary animate-spin" />
              <div>
                <p className="font-medium">{getOptimizationStageLabel()}</p>
                <p className="text-xs text-muted-foreground">
                  Applying all 20 rules to every page. This usually takes 2-5 minutes.
                </p>
              </div>
            </div>
            <Progress value={(optimizationProgress || 0) * 100} className="h-2" />
          </motion.div>
        )}

        {/* Download Ready Banner */}
        {isOptimizationDone && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8 p-6 rounded-lg border border-green-500/30 bg-green-500/5"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                  <Package className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <p className="font-medium text-green-900">Your optimized documentation is ready!</p>
                  <p className="text-sm text-muted-foreground">
                    {optimizationMetadata?.pages_optimized || pageCount} pages rewritten with all 20 rules applied.
                    Includes llms.txt agent entry point.
                  </p>
                </div>
              </div>
              <Button onClick={handleDownload} className="bg-green-600 hover:bg-green-700">
                <Download className="w-4 h-4 mr-2" />
                Download ZIP
              </Button>
            </div>
          </motion.div>
        )}

        {/* Optimization Failed Banner */}
        {isOptimizationFailed && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8 p-4 rounded-lg border border-destructive/30 bg-destructive/5"
          >
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-sm">Optimization failed. Please contact support.</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Your payment is safe. We'll either fix this or issue a full refund.
                </p>
              </div>
            </div>
          </motion.div>
        )}

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
                  {failingRules} rule(s) failing, {warningRules} need work.
                  Get your docs rewritten & optimized.
                </p>
              </div>
              <Button
                size="sm"
                onClick={() => useAssessmentStore.getState().showPaywallModal()}
              >
                Get Optimized Docs · $199
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

            {/* Rule Summary */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium">20-Rule Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-green-500" />
                    <span className="text-sm">Passing</span>
                  </div>
                  <span className="font-bold text-green-600">{passingRules}</span>
                </div>
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-yellow-500" />
                    <span className="text-sm">Needs Work</span>
                  </div>
                  <span className="font-bold text-yellow-600">{warningRules}</span>
                </div>
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-500" />
                    <span className="text-sm">Failing</span>
                  </div>
                  <span className="font-bold text-red-600">{failingRules}</span>
                </div>
                <div className="pt-3 border-t">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Pages Analyzed</span>
                    <span className="font-medium">{pageCount}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Component Scores */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium">Component Scores</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(components).map(([key, value]) => (
                    <div key={key} className="space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">
                          {componentLabels[key] || key}
                        </span>
                        <span className={cn(
                          "text-sm font-bold",
                          value >= 70 ? "text-green-600" :
                          value >= 40 ? "text-yellow-600" : "text-red-600"
                        )}>
                          {value}%
                        </span>
                      </div>
                      <Progress value={value} className="h-1.5" />
                      <p className="text-xs text-muted-foreground">
                        {componentDescriptions[key]}
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Middle + Right Column - Rule-by-Rule Breakdown */}
          <div className="lg:col-span-2 space-y-6">
            {/* 20-Rule Checklist — THE MAIN THING */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Agent-Readiness Rules (20)</CardTitle>
                  <Badge variant="outline" className="text-xs">
                    Based on multi-agent benchmark
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground">
                  Each rule is evaluated across all {pageCount} pages of your documentation.
                  {!hasPaid && ' Our optimizer fixes all failing rules automatically.'}
                </p>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {rules.map((rule) => (
                    <div
                      key={rule.rule_id}
                      className="border rounded-lg overflow-hidden"
                    >
                      <button
                        onClick={() => setExpandedRule(expandedRule === rule.rule_id ? null : rule.rule_id)}
                        className="w-full flex items-center justify-between p-3 hover:bg-muted/50 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <RuleStatusIcon status={rule.status} />
                          <div className="text-left">
                            <span className="font-medium text-sm">
                              {rule.rule_id}. {rule.name}
                            </span>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className={cn(
                            "text-sm font-bold tabular-nums",
                            rule.score >= 70 ? "text-green-600" :
                            rule.score >= 40 ? "text-yellow-600" : "text-red-600"
                          )}>
                            {rule.score}
                          </span>
                          <RuleStatusBadge status={rule.status} />
                          {expandedRule === rule.rule_id ? (
                            <ChevronUp className="w-4 h-4 text-muted-foreground" />
                          ) : (
                            <ChevronDown className="w-4 h-4 text-muted-foreground" />
                          )}
                        </div>
                      </button>

                      <AnimatePresence>
                        {expandedRule === rule.rule_id && (
                          <motion.div
                            initial={{ height: 0 }}
                            animate={{ height: 'auto' }}
                            exit={{ height: 0 }}
                            className="overflow-hidden"
                          >
                            <div className="p-4 pt-0 border-t bg-muted/30">
                              <p className="text-sm text-muted-foreground mb-3">
                                {rule.finding}
                              </p>
                              {rule.pages_checked > 0 && (
                                <div className="flex items-center gap-4 mb-3">
                                  <div className="text-xs text-muted-foreground">
                                    <span className="font-medium">{rule.pages_passing}</span> / {rule.pages_checked} pages passing
                                  </div>
                                  <Progress
                                    value={rule.pages_checked > 0 ? (rule.pages_passing / rule.pages_checked) * 100 : 0}
                                    className="h-1.5 flex-1"
                                  />
                                </div>
                              )}
                              {hasPaid ? (
                                <p className="text-sm text-green-700 bg-green-50 p-2 rounded">
                                  <CheckCircle2 className="w-3.5 h-3.5 inline mr-1" />
                                  This rule has been <strong>automatically applied</strong> in your optimized documentation.
                                  {isOptimizationDone && ' Download the ZIP to see the improvements.'}
                                </p>
                              ) : rule.status !== 'pass' ? (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => useAssessmentStore.getState().showPaywallModal()}
                                >
                                  <FileCode className="w-3 h-3 mr-2" />
                                  Fix This · Get Optimized Docs
                                </Button>
                              ) : null}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* The Deliverable Preview / CTA */}
            <Card className={cn(!hasPaid && "relative")}>
              {!hasPaid && (
                <div className="absolute inset-0 bg-background/80 backdrop-blur-sm z-10 flex flex-col items-center justify-center rounded-lg">
                  <div className="text-center p-6">
                    <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                      <FileArchive className="w-8 h-8 text-primary" />
                    </div>
                    <h3 className="text-xl font-bold mb-2">Your Optimized Docs Are One Click Away</h3>
                    <p className="text-muted-foreground mb-2 max-w-sm">
                      We apply all 20 rules to every page. You download the optimized files.
                      Deploy in minutes.
                    </p>
                    <p className="text-xs text-muted-foreground mb-6">
                      Not a report. Not recommendations. The actual optimized files.
                    </p>
                    <Button onClick={() => useAssessmentStore.getState().showPaywallModal()}>
                      <Unlock className="w-4 h-4 mr-2" />
                      Get Optimized Docs · $199 One-Time
                    </Button>
                  </div>
                </div>
              )}

              <CardHeader>
                <CardTitle>What You Get</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-3 gap-4">
                  <div className="border rounded-lg p-4 text-center">
                    <FileCode className="w-8 h-8 mx-auto mb-2 text-primary" />
                    <h4 className="font-medium text-sm">Optimized Markdown Files</h4>
                    <p className="text-xs text-muted-foreground mt-1">
                      Every page rewritten with all 20 rules applied
                    </p>
                  </div>
                  <div className="border rounded-lg p-4 text-center">
                    <Rocket className="w-8 h-8 mx-auto mb-2 text-primary" />
                    <h4 className="font-medium text-sm">llms.txt Entry Point</h4>
                    <p className="text-xs text-muted-foreground mt-1">
                      The agent-equivalent of robots.txt. Helps AI agents find your docs
                    </p>
                  </div>
                  <div className="border rounded-lg p-4 text-center">
                    <Package className="w-8 h-8 mx-auto mb-2 text-primary" />
                    <h4 className="font-medium text-sm">Ready-to-Deploy ZIP</h4>
                    <p className="text-xs text-muted-foreground mt-1">
                      One download. Unzip. Deploy. Your docs are now agent-ready.
                    </p>
                  </div>
                </div>

                {isOptimizationDone && optimizationMetadata && (
                  <div className="mt-6 p-4 bg-green-50 rounded-lg border border-green-200">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium text-green-900">Optimization Summary</h4>
                      <Button size="sm" onClick={handleDownload} className="bg-green-600 hover:bg-green-700">
                        <Download className="w-4 h-4 mr-2" />
                        Download ZIP
                      </Button>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Pages Optimized</span>
                        <p className="font-medium">{optimizationMetadata.pages_optimized}</p>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Improvements</span>
                        <p className="font-medium">{optimizationMetadata.total_improvements}</p>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Rules Applied</span>
                        <p className="font-medium">20 / 20</p>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </main>

      {/* Paywall Modal */}
      <Dialog open={showPaywall} onOpenChange={hidePaywallModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-2xl">Unlock Your Optimized Documentation</DialogTitle>
            <DialogDescription>
              We rewrite every page applying all 20 rules. You download and deploy. One-shot — no engagement, no recurring fees.
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
              <div className="text-xs text-muted-foreground">Current</div>
            </div>
            <ArrowRight className="w-4 h-4 text-muted-foreground" />
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">90+</div>
              <div className="text-xs text-muted-foreground">After</div>
            </div>
            <div className="flex-1 text-sm text-muted-foreground ml-2">
              <p className="font-medium">{failingRules + warningRules} rules will be fixed</p>
              <p className="text-xs">{getFOMOMessage(score)}</p>
            </div>
          </div>

          {/* What's included */}
          <div className="space-y-3">
            <h4 className="font-medium text-sm">What you'll download:</h4>
            <ul className="space-y-2">
              {deliverableFeatures.map(f => (
                <li key={f} className="flex items-center gap-2 text-sm">
                  <CheckCircle2 className="w-4 h-4 text-green-600 flex-shrink-0" />
                  {f}
                </li>
              ))}
            </ul>
          </div>

          <div className="mt-4 space-y-4">
            <div className="text-center">
              <div className="flex items-baseline justify-center gap-2">
                <span className="text-3xl font-bold">$199</span>
                <span className="text-lg text-muted-foreground">(€172)</span>
              </div>
              <p className="text-sm font-medium text-emerald-600 mt-2">
                One-time payment · No subscription · No monthly fees
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                {pageCount} pages optimized. Pay once, download, deploy. That's it.
              </p>
            </div>

            <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
              <Shield className="w-4 h-4" />
              Secure payment via Stripe
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
                  Pay $199 — One-Time, No Subscription
                </>
              )}
            </Button>

            <p className="text-xs text-center text-muted-foreground">
              Ready in ~5 minutes. Download as ZIP. Deploy anywhere.
            </p>
          </div>

          {/* Promo Code */}
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
    </div>
  )
}
