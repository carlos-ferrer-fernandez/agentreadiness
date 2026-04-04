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
  Download,
  BookOpen,
  Rocket,
  Shield,
  Lightbulb,
  Wrench,
  HelpCircle,
  ExternalLink,
  Settings,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
// Badge available if needed for status indicators
import { cn } from '@/lib/utils'
import { packagesApi } from '@/lib/api'
import type { PageMapEntry } from '@/types'

const PAGE_ICONS: Record<string, typeof BookOpen> = {
  overview: BookOpen,
  agents: Bot,
  'getting-started': Rocket,
  authentication: Shield,
  'core-concepts': Lightbulb,
  rules: FileText,
  troubleshooting: Wrench,
  faq: HelpCircle,
  resources: ExternalLink,
  workflow: Settings,
}

function getPageIcon(pageType: string) {
  if (pageType.startsWith('workflow')) return PAGE_ICONS.workflow
  return PAGE_ICONS[pageType] || FileText
}

const generatingMessages = [
  'Crawling your documentation...',
  'Analyzing content structure...',
  'Planning your documentation package...',
  'Generating overview page...',
  'Building agent operating guide...',
  'Creating getting started guide...',
  'Structuring content for AI agents...',
  'Finalizing your package...',
]

export default function PackageView() {
  const { slug, pageSlug } = useParams<{ slug: string; pageSlug?: string }>()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const currentPage = pageSlug || 'overview'

  const [status, setStatus] = useState<string | null>(null)
  const [paymentStatus, setPaymentStatus] = useState<string>('')
  const [pageMap, setPageMap] = useState<PageMapEntry[] | null>(null)
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
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const messageRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const isGenerating = status === 'submitted' || status === 'crawling' || status === 'planning' || status === 'generating' || status === 'full_generating'
  const isReady = status === 'preview_ready' || status === 'full_ready'
  const isFailed = status === 'failed'
  const isPaid = paymentStatus === 'paid'

  const currentPageEntry = pageMap?.find(p => p.slug === currentPage)

  const fetchStatus = useCallback(async () => {
    if (!slug) return
    try {
      const [statusRes, metaRes] = await Promise.all([
        packagesApi.getStatus(slug),
        packagesApi.getBySlug(slug),
      ])
      setStatus(statusRes.data.status)
      setPaymentStatus(statusRes.data.payment_status)
      setPageMap(statusRes.data.page_map)
      if (statusRes.data.error_message) {
        setError(statusRes.data.error_message)
      }
      if (metaRes.data.product_name) {
        setProductName(metaRes.data.product_name)
      }
    } catch (err: any) {
      if (err.response?.status === 404) {
        setError('Documentation package not found.')
      } else {
        setError('Failed to load package status.')
      }
    }
  }, [slug])

  // Check for payment callback
  useEffect(() => {
    const sessionId = searchParams.get('session_id')
    if (sessionId && slug) {
      packagesApi.verifyPayment(slug, sessionId).then((res) => {
        if (res.data.paid) {
          setPaymentStatus('paid')
          setIframeKey(prev => prev + 1)
          navigate(`/packages/${slug}/${currentPage}`, { replace: true })
        }
      }).catch(() => {})
    }
  }, [searchParams, slug, navigate, currentPage])

  useEffect(() => {
    fetchStatus()
  }, [fetchStatus])

  // Poll while generating
  useEffect(() => {
    if (isGenerating && slug) {
      pollingRef.current = setInterval(async () => {
        try {
          const res = await packagesApi.getStatus(slug)
          setStatus(res.data.status)
          setPaymentStatus(res.data.payment_status)
          setPageMap(res.data.page_map)
          if (res.data.error_message) {
            setError(res.data.error_message)
          }
        } catch {}
      }, 3000)

      messageRef.current = setInterval(() => {
        setMessageIndex((prev) => (prev + 1) % generatingMessages.length)
      }, 3500)
    }

    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current)
      if (messageRef.current) clearInterval(messageRef.current)
    }
  }, [isGenerating, slug])

  // Refresh iframe when navigating between pages
  useEffect(() => {
    setIframeKey(prev => prev + 1)
  }, [currentPage])

  const handleUnlock = async () => {
    if (!slug) return
    setIsUnlocking(true)
    try {
      const res = await packagesApi.unlock(slug, {
        success_url: `${window.location.origin}/packages/${slug}/${currentPage}`,
        cancel_url: `${window.location.origin}/packages/${slug}/${currentPage}`,
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
      const res = await packagesApi.applyPromo(slug, promoCode.trim())
      if (res.data.success) {
        setPromoSuccess(true)
        if (res.data.free) {
          setPaymentStatus('paid')
          setIframeKey(prev => prev + 1)
        }
      }
    } catch (err: any) {
      setPromoError(err.response?.data?.detail || 'Invalid promo code.')
    } finally {
      setIsApplyingPromo(false)
    }
  }

  const handleDownload = () => {
    if (!slug) return
    window.open(packagesApi.getDownloadUrl(slug), '_blank')
  }

  return (
    <div className="min-h-screen bg-[#FAFAF8] flex">
      {/* Mobile sidebar toggle */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="fixed top-4 left-4 z-[60] w-10 h-10 rounded-lg bg-white border border-[#E2E2DC] flex items-center justify-center md:hidden shadow-sm"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" />
        </svg>
      </button>

      {/* Sidebar */}
      <aside className={cn(
        'fixed top-0 left-0 bottom-0 w-[260px] bg-white border-r border-[#E2E2DC] z-50 overflow-y-auto transition-transform duration-200',
        sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
      )}>
        {/* Brand */}
        <div className="px-5 py-4 border-b border-[#E2E2DC]">
          <Link to="/" className="flex items-center gap-2 mb-2">
            <div className="w-6 h-6 bg-[#1A7A4C] rounded-md flex items-center justify-center">
              <Zap className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="text-sm font-semibold tracking-tight text-[#18181B]">GrounDocs</span>
          </Link>
          {productName && (
            <h2 className="font-serif text-lg text-[#18181B] leading-tight">{productName}</h2>
          )}
          <p className="text-xs text-[#71717A] mt-0.5">AI-Ready Documentation</p>
        </div>

        {/* Navigation */}
        <nav className="py-2">
          {pageMap?.map((entry) => {
            const Icon = getPageIcon(entry.page_type)
            const isActive = entry.slug === currentPage
            const isLocked = entry.tier === 'full' && !isPaid

            return (
              <Link
                key={entry.slug}
                to={`/packages/${slug}/${entry.slug}`}
                onClick={() => setSidebarOpen(false)}
                className={cn(
                  'flex items-center gap-2.5 px-5 py-2.5 text-sm transition-all border-l-3',
                  isActive
                    ? 'bg-[#1A7A4C]/5 text-[#1A7A4C] font-semibold border-l-[3px] border-[#1A7A4C]'
                    : 'text-[#52525B] hover:bg-[#F4F4F5] border-l-[3px] border-transparent',
                  isLocked && 'opacity-50'
                )}
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span className="truncate">{entry.title}</span>
                {isLocked && <Lock className="w-3 h-3 ml-auto text-[#A1A1AA] flex-shrink-0" />}
              </Link>
            )
          })}
        </nav>

        {/* Sidebar footer actions */}
        <div className="mt-auto px-5 py-4 border-t border-[#E2E2DC]">
          {isPaid && (
            <Button
              size="sm"
              variant="outline"
              onClick={handleDownload}
              className="w-full text-xs border-[#E2E2DC] mb-2"
            >
              <Download className="w-3.5 h-3.5 mr-1.5" />
              Download ZIP
            </Button>
          )}
          {!isPaid && (
            <>
              <Button
                size="sm"
                onClick={handleUnlock}
                disabled={isUnlocking}
                className="w-full bg-[#1A7A4C] hover:bg-[#145E3A] text-white text-xs mb-2"
              >
                {isUnlocking ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" />
                ) : (
                  <Lock className="w-3.5 h-3.5 mr-1.5" />
                )}
                Unlock Full Package — $99
              </Button>
              <button
                onClick={() => setShowPromoInput(!showPromoInput)}
                className="text-xs text-[#71717A] hover:text-[#18181B] transition-colors flex items-center gap-1 mx-auto"
              >
                <Gift className="w-3 h-3" />
                {showPromoInput ? 'Cancel' : 'Promo code?'}
              </button>
              {showPromoInput && (
                <div className="flex items-center gap-1.5 mt-2">
                  <Input
                    type="text"
                    placeholder="Code"
                    value={promoCode}
                    onChange={(e) => { setPromoCode(e.target.value); setPromoError(null) }}
                    onKeyDown={(e) => e.key === 'Enter' && handleApplyPromo()}
                    className="h-7 text-xs rounded-md bg-[#FAFAF8] border-[#E2E2DC]"
                  />
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleApplyPromo}
                    disabled={isApplyingPromo || !promoCode.trim()}
                    className="h-7 text-xs px-2"
                  >
                    {isApplyingPromo ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Apply'}
                  </Button>
                </div>
              )}
              {promoError && <p className="text-xs text-red-500 mt-1">{promoError}</p>}
              {promoSuccess && (
                <p className="text-xs text-[#1A7A4C] mt-1 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Unlocked!
                </p>
              )}
            </>
          )}
        </div>
      </aside>

      {/* Backdrop for mobile sidebar */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/20 z-40 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <main className="flex-1 md:ml-[260px] min-h-screen">
        {/* Error state */}
        {error && !isGenerating && (
          <div className="max-w-2xl mx-auto px-4 py-20 text-center">
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
              <div className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center mx-auto mb-6">
                <AlertTriangle className="w-8 h-8 text-red-500" />
              </div>
              <h2 className="font-serif text-2xl mb-3 text-[#18181B]">Something went wrong</h2>
              <p className="text-[#71717A] mb-6">{error}</p>
              <Button variant="outline" onClick={() => navigate('/')} className="border-[#E2E2DC]">
                <ArrowLeft className="w-4 h-4 mr-2" /> Try Again
              </Button>
            </motion.div>
          </div>
        )}

        {/* Generating state */}
        {isGenerating && (
          <div className="max-w-2xl mx-auto px-4 py-20 text-center">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
              <div className="w-20 h-20 rounded-full bg-[#D1F0E1] flex items-center justify-center mx-auto mb-8">
                <motion.div animate={{ rotate: 360 }} transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}>
                  <Bot className="w-10 h-10 text-[#1A7A4C]" />
                </motion.div>
              </div>
              <h2 className="font-serif text-3xl mb-3 text-[#18181B]">Building your documentation package</h2>
              <p className="text-[#71717A] text-lg mb-8">
                This usually takes 60-90 seconds. We're analyzing your docs and generating multiple AI-ready pages.
              </p>
              <div className="max-w-md mx-auto">
                <div className="space-y-3 mb-6">
                  {[
                    { icon: Search, label: 'Crawling documentation', statuses: ['submitted', 'crawling'] },
                    { icon: Lightbulb, label: 'Planning page structure', statuses: ['planning'] },
                    { icon: Sparkles, label: 'Generating pages', statuses: ['generating', 'full_generating'] },
                  ].map((step) => {
                    const isActive = step.statuses.some(s => {
                      const statusOrder = ['submitted', 'crawling', 'planning', 'generating', 'full_generating']
                      return statusOrder.indexOf(status || '') >= statusOrder.indexOf(s)
                    })
                    const isCurrentStep = step.statuses.includes(status || '')

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

        {/* Content: iframe with page HTML */}
        {isReady && !error && slug && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="h-screen"
          >
            <iframe
              key={iframeKey}
              src={packagesApi.getPageUrl(slug, currentPage)}
              className="w-full h-full border-0"
              title={`${productName} - ${currentPageEntry?.title || currentPage}`}
            />
          </motion.div>
        )}

        {/* Failed state */}
        {isFailed && !error && (
          <div className="max-w-2xl mx-auto px-4 py-20 text-center">
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
              <div className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center mx-auto mb-6">
                <AlertTriangle className="w-8 h-8 text-red-500" />
              </div>
              <h2 className="font-serif text-2xl mb-3 text-[#18181B]">Generation failed</h2>
              <p className="text-[#71717A] mb-6">
                We couldn't generate a documentation package. This usually happens when the docs URL isn't publicly accessible.
              </p>
              <Button variant="outline" onClick={() => navigate('/')} className="border-[#E2E2DC]">
                <ArrowLeft className="w-4 h-4 mr-2" /> Try Again
              </Button>
            </motion.div>
          </div>
        )}

        {/* Loading state */}
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
