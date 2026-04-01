import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useParams, useNavigate, useSearchParams, Link } from 'react-router-dom'
import {
  ArrowLeft,
  Loader2,
  Lock,
  CheckCircle2,
  AlertTriangle,
  Gift,
  Zap,
  FileText,
  Search,
  Sparkles,
  Bot,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { agentPagesApi } from '@/lib/api'
import type { AgentPageStatus } from '@/types'

const generatingMessages = [
  'Crawling your documentation...',
  'Analyzing your product structure...',
  'Identifying API endpoints and capabilities...',
  'Mapping authentication and access flows...',
  'Extracting code examples and parameters...',
  'Building the agent-ready page...',
  'Structuring content for machine consumption...',
  'Generating your /agents page...',
]

export default function AgentPageView() {
  const { slug } = useParams<{ slug: string }>()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const [status, setStatus] = useState<string | null>(null)
  const [paymentStatus, setPaymentStatus] = useState<string>('')
  const [_hasDraft, setHasDraft] = useState(false)
  const [_hasFull, setHasFull] = useState(false)
  const [productName, setProductName] = useState<string>('')
  const [error, setError] = useState<string | null>(null)
  const [isUnlocking, setIsUnlocking] = useState(false)
  const [promoCode, setPromoCode] = useState('')
  const [showPromoInput, setShowPromoInput] = useState(false)
  const [promoError, setPromoError] = useState<string | null>(null)
  const [promoSuccess, setPromoSuccess] = useState(false)
  const [isApplyingPromo, setIsApplyingPromo] = useState(false)
  const [messageIndex, setMessageIndex] = useState(0)
  const [iframeKey, setIframeKey] = useState(0)

  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const messageRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const isGenerating = status === 'submitted' || status === 'crawling' || status === 'generating'
  const isReady = status === 'draft_ready' || status === 'full_ready'
  const isFailed = status === 'failed'
  const isPaid = paymentStatus === 'paid'
  const showDraft = isReady && !isPaid

  const updateStatus = useCallback((s: AgentPageStatus) => {
    setStatus(s.status)
    setPaymentStatus(s.payment_status)
    setHasDraft(s.has_draft)
    setHasFull(s.has_full)
  }, [])

  // Fetch status on mount
  const fetchStatus = useCallback(async () => {
    if (!slug) return
    try {
      const [statusRes, metaRes] = await Promise.all([
        agentPagesApi.getStatus(slug),
        agentPagesApi.getBySlug(slug),
      ])
      updateStatus(statusRes.data)
      if (metaRes.data.product_name) {
        setProductName(metaRes.data.product_name)
      }
    } catch (err: any) {
      if (err.response?.status === 404) {
        setError('Agent page not found.')
      } else {
        setError('Failed to load agent page status.')
      }
    }
  }, [slug, updateStatus])

  // Check for payment callback
  useEffect(() => {
    const sessionId = searchParams.get('session_id')
    if (sessionId && slug) {
      agentPagesApi.verifyPayment(slug, sessionId).then((res) => {
        if (res.data.paid) {
          setStatus('full_ready')
          setPaymentStatus('paid')
          setHasDraft(true)
          setHasFull(true)
          setIframeKey(prev => prev + 1)
          navigate(`/agent-pages/${slug}`, { replace: true })
        }
      }).catch(() => {
        // Payment verification failed, continue normally
      })
    }
  }, [searchParams, slug, navigate])

  useEffect(() => {
    fetchStatus()
  }, [fetchStatus])

  // Poll while generating
  useEffect(() => {
    if (isGenerating && slug) {
      pollingRef.current = setInterval(async () => {
        try {
          const res = await agentPagesApi.getStatus(slug)
          updateStatus(res.data)
        } catch {
          // ignore polling errors
        }
      }, 3000)

      messageRef.current = setInterval(() => {
        setMessageIndex((prev) => (prev + 1) % generatingMessages.length)
      }, 3500)
    }

    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current)
      if (messageRef.current) clearInterval(messageRef.current)
    }
  }, [isGenerating, slug, updateStatus])

  const handleUnlock = async () => {
    if (!slug) return
    setIsUnlocking(true)
    try {
      const res = await agentPagesApi.unlock(slug, {
        success_url: `${window.location.origin}/agent-pages/${slug}?session_id={CHECKOUT_SESSION_ID}`,
        cancel_url: `${window.location.origin}/agent-pages/${slug}`,
      })
      if (res.data.url) {
        window.location.href = res.data.url
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start checkout.')
    } finally {
      setIsUnlocking(false)
    }
  }

  const handleApplyPromo = async () => {
    if (!slug || !promoCode.trim()) return
    setIsApplyingPromo(true)
    setPromoError(null)
    setPromoSuccess(false)
    try {
      const res = await agentPagesApi.applyPromo(slug, promoCode.trim())
      if (res.data.success) {
        setPromoSuccess(true)
        if (res.data.free) {
          setStatus('full_ready')
          setPaymentStatus('paid')
          setHasDraft(true)
          setHasFull(true)
          setIframeKey(prev => prev + 1)
        }
      }
    } catch (err: any) {
      setPromoError(err.response?.data?.detail || 'Invalid promo code.')
    } finally {
      setIsApplyingPromo(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#FAFAF8]">
      {/* Sticky header bar */}
      <header className="sticky top-0 z-50 border-b border-[#E2E2DC] bg-white/80 backdrop-blur-xl">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-14">
            {/* Left: back + logo + product name */}
            <div className="flex items-center gap-3 min-w-0">
              <Link
                to="/"
                className="flex items-center gap-1.5 text-sm text-[#71717A] hover:text-[#18181B] transition-colors flex-shrink-0"
              >
                <ArrowLeft className="w-4 h-4" />
                <span className="hidden sm:inline">Back to GrounDocs</span>
              </Link>
              <div className="w-px h-5 bg-[#E2E2DC] hidden sm:block" />
              <div className="flex items-center gap-2 flex-shrink-0">
                <div className="w-6 h-6 bg-[#1A7A4C] rounded-md flex items-center justify-center">
                  <Zap className="w-3.5 h-3.5 text-white" />
                </div>
                <span className="text-sm font-semibold tracking-tight text-[#18181B]">GrounDocs</span>
              </div>
              {productName && (
                <>
                  <div className="w-px h-5 bg-[#E2E2DC] hidden sm:block" />
                  <span className="text-sm font-medium truncate max-w-[200px] text-[#18181B]">{productName}</span>
                </>
              )}
            </div>

            {/* Right: status + actions */}
            <div className="flex items-center gap-3">
              {isGenerating && (
                <Badge variant="outline" className="text-xs gap-1.5">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  Generating...
                </Badge>
              )}
              {isReady && isPaid && (
                <Badge variant="success" className="text-xs gap-1.5">
                  <CheckCircle2 className="w-3 h-3" />
                  Full Page
                </Badge>
              )}
              {showDraft && (
                <>
                  <Badge variant="warning" className="text-xs gap-1.5">
                    <FileText className="w-3 h-3" />
                    Draft Preview
                  </Badge>

                  {/* Promo code toggle */}
                  <button
                    onClick={() => setShowPromoInput(!showPromoInput)}
                    className="text-xs text-[#71717A] hover:text-[#18181B] transition-colors hidden sm:flex items-center gap-1"
                  >
                    <Gift className="w-3 h-3" />
                    {showPromoInput ? 'Cancel' : 'Have a promo code?'}
                  </button>

                  <Button
                    size="sm"
                    onClick={handleUnlock}
                    disabled={isUnlocking}
                    className="bg-[#1A7A4C] hover:bg-[#145E3A] text-white text-xs"
                  >
                    {isUnlocking ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" />
                    ) : (
                      <Lock className="w-3.5 h-3.5 mr-1.5" />
                    )}
                    Unlock Full Page — $99
                  </Button>
                </>
              )}
              {isFailed && (
                <Badge variant="destructive" className="text-xs gap-1.5">
                  <AlertTriangle className="w-3 h-3" />
                  Failed
                </Badge>
              )}
            </div>
          </div>

          {/* Promo code input row */}
          <AnimatePresence>
            {showPromoInput && showDraft && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <div className="flex items-center gap-2 pb-3">
                  <Input
                    type="text"
                    placeholder="Enter promo code"
                    value={promoCode}
                    onChange={(e) => { setPromoCode(e.target.value); setPromoError(null) }}
                    onKeyDown={(e) => e.key === 'Enter' && handleApplyPromo()}
                    className="h-8 text-sm max-w-[200px] rounded-lg bg-[#FAFAF8] border-[#E2E2DC]"
                  />
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleApplyPromo}
                    disabled={isApplyingPromo || !promoCode.trim()}
                    className="h-8 text-xs"
                  >
                    {isApplyingPromo ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Apply'}
                  </Button>
                  {promoError && (
                    <span className="text-xs text-red-500">{promoError}</span>
                  )}
                  {promoSuccess && (
                    <span className="text-xs text-[#1A7A4C] flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" />
                      Unlocked!
                    </span>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </header>

      {/* Main content area */}
      <main>
        {/* Error state */}
        {error && !isGenerating && (
          <div className="max-w-2xl mx-auto px-4 py-20 text-center">
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <div className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center mx-auto mb-6">
                <AlertTriangle className="w-8 h-8 text-red-500" />
              </div>
              <h2 className="font-serif text-2xl mb-3 text-[#18181B]">Something went wrong</h2>
              <p className="text-[#71717A] mb-6">{error}</p>
              <Button
                variant="outline"
                onClick={() => navigate('/')}
                className="border-[#E2E2DC]"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Try Again
              </Button>
            </motion.div>
          </div>
        )}

        {/* Generating state */}
        {isGenerating && (
          <div className="max-w-2xl mx-auto px-4 py-20 text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <div className="w-20 h-20 rounded-full bg-[#D1F0E1] flex items-center justify-center mx-auto mb-8">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                >
                  <Bot className="w-10 h-10 text-[#1A7A4C]" />
                </motion.div>
              </div>

              <h2 className="font-serif text-3xl mb-3 text-[#18181B]">Building your agent page</h2>
              <p className="text-[#71717A] text-lg mb-8">
                This usually takes 30-60 seconds. We're analyzing your docs and generating a structured page AI agents can use.
              </p>

              {/* Progress steps */}
              <div className="max-w-md mx-auto">
                <div className="space-y-3 mb-6">
                  {[
                    { icon: Search, label: 'Crawling documentation' },
                    { icon: FileText, label: 'Analyzing content structure' },
                    { icon: Sparkles, label: 'Generating agent page' },
                  ].map((step, i) => {
                    const isActive = (status === 'submitted' && i === 0) ||
                      (status === 'crawling' && i <= 1) ||
                      (status === 'generating' && i <= 2)
                    const isCurrentStep = (status === 'submitted' && i === 0) ||
                      (status === 'crawling' && i === 1) ||
                      (status === 'generating' && i === 2)

                    return (
                      <div
                        key={step.label}
                        className={cn(
                          'flex items-center gap-3 px-4 py-3 rounded-lg transition-all',
                          isActive ? 'bg-[#D1F0E1]/50' : 'bg-[#F3F3F0]',
                          isCurrentStep && 'ring-1 ring-[#1A7A4C]/20'
                        )}
                      >
                        <div className={cn(
                          'w-8 h-8 rounded-full flex items-center justify-center',
                          isActive ? 'bg-[#D1F0E1]' : 'bg-[#EAEAE6]'
                        )}>
                          {isActive && !isCurrentStep ? (
                            <CheckCircle2 className="w-4 h-4 text-[#1A7A4C]" />
                          ) : (
                            <step.icon className={cn('w-4 h-4', isActive ? 'text-[#1A7A4C]' : 'text-[#71717A]')} />
                          )}
                        </div>
                        <span className={cn('text-sm', isActive ? 'font-medium text-[#18181B]' : 'text-[#71717A]')}>
                          {step.label}
                        </span>
                        {isCurrentStep && (
                          <motion.div
                            className="ml-auto w-4 h-4 border-2 border-[#1A7A4C] border-t-transparent rounded-full"
                            animate={{ rotate: 360 }}
                            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                          />
                        )}
                      </div>
                    )
                  })}
                </div>

                <AnimatePresence mode="wait">
                  <motion.p
                    key={messageIndex}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }}
                    transition={{ duration: 0.3 }}
                    className="text-xs text-[#A1A1AA]"
                  >
                    {generatingMessages[messageIndex]}
                  </motion.p>
                </AnimatePresence>
              </div>
            </motion.div>
          </div>
        )}

        {/* Content: iframe with agent page HTML */}
        {isReady && !error && slug && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4, delay: 0.1 }}
          >
            {/* Draft overlay banner */}
            {showDraft && (
              <div className="bg-amber-50 border-b border-amber-200 px-4 py-3">
                <div className="max-w-[1400px] mx-auto flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Lock className="w-4 h-4 text-amber-600" />
                    <span className="text-sm text-amber-800">
                      You're viewing a draft preview. Some sections are truncated.
                    </span>
                  </div>
                  <Button
                    size="sm"
                    onClick={handleUnlock}
                    disabled={isUnlocking}
                    className="bg-[#1A7A4C] hover:bg-[#145E3A] text-white text-xs"
                  >
                    Unlock Full Page — $99
                  </Button>
                </div>
              </div>
            )}

            {/* The iframe */}
            <iframe
              key={iframeKey}
              src={agentPagesApi.getViewUrl(slug)}
              className="w-full border-0"
              style={{ height: showDraft ? 'calc(100vh - 56px - 52px)' : 'calc(100vh - 56px)' }}
              title={`${productName} Agent Page`}
            />
          </motion.div>
        )}

        {/* Failed state */}
        {isFailed && !error && (
          <div className="max-w-2xl mx-auto px-4 py-20 text-center">
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <div className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center mx-auto mb-6">
                <AlertTriangle className="w-8 h-8 text-red-500" />
              </div>
              <h2 className="font-serif text-2xl mb-3 text-[#18181B]">Generation failed</h2>
              <p className="text-[#71717A] mb-6">
                We couldn't generate an agent page for this documentation. This usually happens when the docs URL isn't publicly accessible or doesn't contain enough content.
              </p>
              <Button
                variant="outline"
                onClick={() => navigate('/')}
                className="border-[#E2E2DC]"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Try Again
              </Button>
            </motion.div>
          </div>
        )}

        {/* Initial loading state (no status yet) */}
        {!status && !error && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-6 h-6 animate-spin text-[#1A7A4C] mr-3" />
            <span className="text-[#71717A]">Loading...</span>
          </div>
        )}
      </main>
    </div>
  )
}
