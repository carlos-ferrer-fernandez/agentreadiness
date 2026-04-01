import { useState, useEffect, useRef } from 'react'
import { motion, useInView } from 'framer-motion'
import { useNavigate, Link } from 'react-router-dom'
import {
  ArrowRight,
  Menu,
  X,
  Zap,
  BookOpen,
  Code2,
  AlertOctagon,
  Table2,
  Layers,
  FileCheck,
  Link2,
  Eye,
  ShieldAlert,
  Loader2,
  Check,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { agentPagesApi } from '@/lib/api'

// ------------------------------------------------------------------
// Fade-in-on-scroll wrapper
// ------------------------------------------------------------------
function FadeIn({ children, className = '', delay = 0 }: {
  children: React.ReactNode
  className?: string
  delay?: number
}) {
  const ref = useRef<HTMLDivElement>(null)
  const isInView = useInView(ref, { once: true, margin: '-60px' })
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 20 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.5, delay, ease: [0, 0, 0.2, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

// ------------------------------------------------------------------
// Shared form component
// ------------------------------------------------------------------
function GenerateForm({ id, buttonLabel = 'Generate Free Preview' }: {
  id?: string
  buttonLabel?: string
}) {
  const navigate = useNavigate()
  const [productName, setProductName] = useState('')
  const [docsUrl, setDocsUrl] = useState('')
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const validate = () => {
    if (!productName.trim()) return 'Product name is required'
    if (!docsUrl.trim() || !docsUrl.startsWith('http')) return 'Enter a valid URL starting with http'
    if (!email.trim() || !email.includes('@') || !email.includes('.')) return 'Enter a valid email'
    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const validationError = validate()
    if (validationError) {
      setError(validationError)
      return
    }
    setError(null)
    setLoading(true)
    try {
      const res = await agentPagesApi.generate({
        product_name: productName.trim(),
        docs_url: docsUrl.trim(),
        email: email.trim(),
      })
      navigate(`/agent-pages/${res.data.slug}`)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Something went wrong. Please try again.')
      setLoading(false)
    }
  }

  return (
    <form id={id} onSubmit={handleSubmit} className="space-y-3">
      <Input
        placeholder="e.g. Stripe, Notion, Vercel"
        value={productName}
        onChange={(e) => setProductName(e.target.value)}
        className="h-11 bg-white border-[#E2E2DC] rounded-lg text-[15px] placeholder:text-[#A1A1AA]"
      />
      <Input
        placeholder="https://docs.example.com"
        value={docsUrl}
        onChange={(e) => setDocsUrl(e.target.value)}
        className="h-11 bg-white border-[#E2E2DC] rounded-lg text-[15px] placeholder:text-[#A1A1AA]"
      />
      <Input
        type="email"
        placeholder="you@company.com"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        className="h-11 bg-white border-[#E2E2DC] rounded-lg text-[15px] placeholder:text-[#A1A1AA]"
      />
      {error && (
        <p className="text-sm text-[#B91C1C]">{error}</p>
      )}
      <Button
        type="submit"
        disabled={loading}
        className="w-full h-12 bg-[#1A7A4C] hover:bg-[#145E3A] text-white rounded-lg text-[15px] font-semibold"
      >
        {loading ? (
          <Loader2 className="w-4 h-4 animate-spin mr-2" />
        ) : null}
        {buttonLabel}
        {!loading && <ArrowRight className="w-4 h-4 ml-2" />}
      </Button>
    </form>
  )
}

// ------------------------------------------------------------------
// Best practices data
// ------------------------------------------------------------------
const BEST_PRACTICES = [
  { icon: Eye, title: 'Write for the machine reader first', desc: 'Agents parse structure, not vibes' },
  { icon: BookOpen, title: 'Make every section self-contained', desc: 'No "see above" or "as mentioned earlier"' },
  { icon: FileCheck, title: 'State prerequisites explicitly', desc: "Agents can't infer what's \"obvious\"" },
  { icon: Code2, title: 'Show complete, runnable code', desc: 'Agents execute literally, not conceptually' },
  { icon: AlertOctagon, title: 'Document every error code', desc: 'Agents need to handle failures without guessing' },
  { icon: Table2, title: 'Use tables for parameters', desc: 'Structured data beats prose for machines' },
  { icon: Layers, title: 'Separate concepts from procedures', desc: 'Clear action paths, not mixed narratives' },
  { icon: Code2, title: 'Include input/output examples', desc: 'Agents learn patterns from concrete data' },
  { icon: ShieldAlert, title: 'Define constraints and limits', desc: 'Rate limits, size caps, permissions — be explicit' },
  { icon: Link2, title: 'Link to canonical references', desc: 'Give agents verifiable source-of-truth URLs' },
]

// ------------------------------------------------------------------
// Hardcoded example pages (fallback)
// ------------------------------------------------------------------
const EXAMPLE_PAGES = [
  { slug: 'stripe', product_name: 'Stripe', desc: 'Payment processing APIs structured for agent consumption' },
  { slug: 'vercel', product_name: 'Vercel', desc: 'Deployment platform with clear agent integration paths' },
  { slug: 'notion', product_name: 'Notion', desc: 'Workspace API capabilities organized for machine readers' },
  { slug: 'slack', product_name: 'Slack', desc: 'Messaging platform with structured bot and API references' },
]

// ------------------------------------------------------------------
// Main component
// ------------------------------------------------------------------
export function LandingPage() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [featuredPages, setFeaturedPages] = useState(EXAMPLE_PAGES)

  useEffect(() => {
    agentPagesApi.getFeatured()
      .then((res) => {
        if (res.data && res.data.length > 0) {
          const mapped = res.data.slice(0, 4).map((p: any) => ({
            slug: p.company_slug || p.slug,
            product_name: p.product_name,
            desc: `Agent-optimized page for ${p.product_name}`,
          }))
          setFeaturedPages(mapped)
        }
      })
      .catch(() => {
        // keep hardcoded fallback
      })
  }, [])

  const scrollToHero = () => {
    document.getElementById('hero-form')?.scrollIntoView({ behavior: 'smooth' })
    setMobileMenuOpen(false)
  }

  return (
    <div className="min-h-screen bg-[#FAFAF8] text-[#18181B]">
      {/* ============================================================ */}
      {/*  NAVIGATION                                                  */}
      {/* ============================================================ */}
      <nav className="sticky top-0 z-50 bg-[#FAFAF8]/80 backdrop-blur-xl border-b border-[#E2E2DC]">
        <div className="max-w-[1100px] mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <div className="w-7 h-7 bg-[#1A7A4C] rounded-lg flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="text-lg font-semibold font-serif">GrounDocs</span>
          </Link>

          {/* Desktop links */}
          <div className="hidden md:flex items-center gap-6">
            <a href="#examples" className="text-sm text-[#71717A] hover:text-[#18181B] transition-colors">
              Examples
            </a>
            <a href="#practices" className="text-sm text-[#71717A] hover:text-[#18181B] transition-colors">
              Best Practices
            </a>
            <a href="#pricing" className="text-sm text-[#71717A] hover:text-[#18181B] transition-colors">
              Pricing
            </a>
            <Link to="/blog" className="text-sm text-[#71717A] hover:text-[#18181B] transition-colors">
              Blog
            </Link>
            <Button
              size="sm"
              onClick={scrollToHero}
              className="bg-[#1A7A4C] hover:bg-[#145E3A] text-white rounded-lg text-sm"
            >
              Get Free Preview
            </Button>
          </div>

          {/* Mobile hamburger */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-[#71717A] hover:text-[#18181B]"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        {/* Mobile slide-out */}
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            className="md:hidden bg-white border-b border-[#E2E2DC] px-4 pb-4 space-y-3"
          >
            <a href="#examples" onClick={() => setMobileMenuOpen(false)} className="block text-sm py-2 text-[#71717A]">Examples</a>
            <a href="#practices" onClick={() => setMobileMenuOpen(false)} className="block text-sm py-2 text-[#71717A]">Best Practices</a>
            <a href="#pricing" onClick={() => setMobileMenuOpen(false)} className="block text-sm py-2 text-[#71717A]">Pricing</a>
            <Link to="/blog" onClick={() => setMobileMenuOpen(false)} className="block text-sm py-2 text-[#71717A]">Blog</Link>
            <Button
              onClick={scrollToHero}
              className="w-full bg-[#1A7A4C] hover:bg-[#145E3A] text-white rounded-lg text-sm"
            >
              Get Free Preview
            </Button>
          </motion.div>
        )}
      </nav>

      {/* ============================================================ */}
      {/*  HERO                                                        */}
      {/* ============================================================ */}
      <section className="py-16 sm:py-20 lg:py-24">
        <div className="max-w-[1100px] mx-auto px-4 sm:px-6">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-start">
            {/* Left: copy */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, ease: [0, 0, 0.2, 1] }}
            >
              <h1 className="font-serif text-[42px] sm:text-[54px] leading-[1.0] tracking-[-0.02em] mb-5">
                Turn your docs into an agent-ready page
              </h1>
              <p className="text-lg text-[#71717A] leading-relaxed max-w-[540px]">
                Most products send AI agents to documentation built for humans.
                GrounDocs generates a dedicated page that tells agents exactly
                how to use your product.
              </p>
            </motion.div>

            {/* Right: form card */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.15, ease: [0, 0, 0.2, 1] }}
            >
              <div className="bg-white rounded-2xl shadow-[0_4px_12px_rgba(24,24,27,0.08),0_2px_4px_rgba(24,24,27,0.04)] p-6 sm:p-8">
                <GenerateForm id="hero-form" />
                <p className="text-xs text-[#A1A1AA] text-center mt-4">
                  Free draft preview. No credit card required.
                </p>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  PROBLEM                                                     */}
      {/* ============================================================ */}
      <section className="py-16 sm:py-20 border-t border-[#E2E2DC]">
        <div className="max-w-[1100px] mx-auto px-4 sm:px-6">
          <FadeIn>
            <h2 className="font-serif text-3xl sm:text-[38px] leading-[1.15] tracking-[-0.01em] text-center mb-12">
              Your docs weren't built for AI agents
            </h2>
          </FadeIn>

          <div className="grid sm:grid-cols-3 gap-6">
            {[
              {
                title: "Agents don't scroll",
                body: 'They need self-contained answers, not breadcrumb trails across dozens of pages.',
              },
              {
                title: 'Agents take instructions literally',
                body: 'Vague language like "simply configure" means nothing to a machine that needs exact steps.',
              },
              {
                title: 'Agents need structure',
                body: 'Marketing copy, scattered links, and ambiguous steps break agent workflows.',
              },
            ].map((card, i) => (
              <FadeIn key={card.title} delay={i * 0.1}>
                <div className="bg-white rounded-xl p-6 shadow-[0_1px_3px_rgba(24,24,27,0.06),0_1px_2px_rgba(24,24,27,0.04)] border border-[#E2E2DC]">
                  <h3 className="font-semibold text-[17px] mb-2">{card.title}</h3>
                  <p className="text-sm text-[#71717A] leading-relaxed">{card.body}</p>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  HOW IT WORKS                                                */}
      {/* ============================================================ */}
      <section className="py-16 sm:py-20 border-t border-[#E2E2DC]">
        <div className="max-w-[1100px] mx-auto px-4 sm:px-6">
          <FadeIn>
            <h2 className="font-serif text-3xl sm:text-[38px] leading-[1.15] tracking-[-0.01em] text-center mb-4">
              Three steps to your /agents page
            </h2>
          </FadeIn>

          <div className="grid sm:grid-cols-3 gap-8 mt-12">
            {[
              {
                step: '1',
                title: 'Submit your docs',
                body: 'We crawl and analyze your documentation, extracting the content AI agents actually need.',
              },
              {
                step: '2',
                title: 'AI generates your page',
                body: 'Our models extract what agents actually need: endpoints, parameters, auth flows, and examples.',
              },
              {
                step: '3',
                title: 'Preview and publish',
                body: 'Get a hosted, agent-optimized page in minutes. Review the draft, unlock the full version.',
              },
            ].map((item, i) => (
              <FadeIn key={item.step} delay={i * 0.1}>
                <div className="text-center sm:text-left">
                  <div className="w-10 h-10 rounded-full bg-[#D1F0E1] text-[#1A7A4C] font-semibold text-sm flex items-center justify-center mx-auto sm:mx-0 mb-4">
                    {item.step}
                  </div>
                  <h3 className="font-semibold text-[17px] mb-2">{item.title}</h3>
                  <p className="text-sm text-[#71717A] leading-relaxed">{item.body}</p>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  EXAMPLE PAGES                                               */}
      {/* ============================================================ */}
      <section id="examples" className="py-16 sm:py-20 border-t border-[#E2E2DC]">
        <div className="max-w-[1100px] mx-auto px-4 sm:px-6">
          <FadeIn>
            <div className="text-center mb-12">
              <h2 className="font-serif text-3xl sm:text-[38px] leading-[1.15] tracking-[-0.01em] mb-3">
                See it in action
              </h2>
              <p className="text-[#71717A] text-lg">
                Agent pages we've built for well-known products
              </p>
            </div>
          </FadeIn>

          <div className="grid sm:grid-cols-2 gap-5">
            {featuredPages.map((page, i) => (
              <FadeIn key={page.slug} delay={i * 0.08}>
                <Link
                  to={`/agent-pages/${page.slug}`}
                  className="group block bg-white rounded-xl p-6 shadow-[0_1px_3px_rgba(24,24,27,0.06),0_1px_2px_rgba(24,24,27,0.04)] border border-[#E2E2DC] hover:shadow-[0_4px_12px_rgba(24,24,27,0.08),0_2px_4px_rgba(24,24,27,0.04)] hover:border-[#1A7A4C]/30 transition-all duration-200"
                >
                  <div className="flex items-center gap-3 mb-3">
                    <img
                      src={`https://logo.clearbit.com/${page.product_name.toLowerCase()}.com`}
                      alt={page.product_name}
                      className="w-8 h-8 rounded-lg"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none'
                      }}
                    />
                    <h3 className="font-semibold text-[17px]">{page.product_name}</h3>
                  </div>
                  <p className="text-sm text-[#71717A] mb-4">{page.desc}</p>
                  <span className="text-sm text-[#1A7A4C] font-medium group-hover:translate-x-0.5 transition-transform inline-flex items-center gap-1">
                    View Agent Page <ArrowRight className="w-3.5 h-3.5" />
                  </span>
                </Link>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  10 BEST PRACTICES                                           */}
      {/* ============================================================ */}
      <section id="practices" className="py-16 sm:py-20 border-t border-[#E2E2DC]">
        <div className="max-w-[1100px] mx-auto px-4 sm:px-6">
          <FadeIn>
            <div className="text-center mb-12">
              <h2 className="font-serif text-3xl sm:text-[38px] leading-[1.15] tracking-[-0.01em] mb-3">
                What makes a great /agents page
              </h2>
              <p className="text-[#71717A] text-lg">
                The principles behind every page we generate
              </p>
            </div>
          </FadeIn>

          <div className="grid sm:grid-cols-2 gap-x-8 gap-y-5 max-w-[900px] mx-auto">
            {BEST_PRACTICES.map((item, i) => (
              <FadeIn key={item.title} delay={i * 0.04}>
                <div className="flex gap-4 items-start">
                  <div className="flex-shrink-0 w-9 h-9 rounded-lg bg-[#F3F3F0] flex items-center justify-center">
                    <span className="text-xs font-mono font-medium text-[#71717A]">{String(i + 1).padStart(2, '0')}</span>
                  </div>
                  <div>
                    <h3 className="font-semibold text-[15px] mb-0.5">{item.title}</h3>
                    <p className="text-sm text-[#71717A]">{item.desc}</p>
                  </div>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  PRICING                                                     */}
      {/* ============================================================ */}
      <section id="pricing" className="py-16 sm:py-20 border-t border-[#E2E2DC]">
        <div className="max-w-[1100px] mx-auto px-4 sm:px-6">
          <FadeIn>
            <h2 className="font-serif text-3xl sm:text-[38px] leading-[1.15] tracking-[-0.01em] text-center mb-12">
              Simple pricing
            </h2>
          </FadeIn>

          <div className="grid sm:grid-cols-2 gap-6 max-w-[700px] mx-auto">
            {/* Free tier */}
            <FadeIn delay={0}>
              <div className="bg-white rounded-xl p-6 sm:p-8 shadow-[0_1px_3px_rgba(24,24,27,0.06),0_1px_2px_rgba(24,24,27,0.04)] border border-[#E2E2DC]">
                <h3 className="font-semibold text-[17px] mb-1">Draft Preview</h3>
                <p className="text-sm text-[#71717A] mb-5">See what your agent page looks like</p>
                <div className="mb-6">
                  <span className="text-3xl font-serif">$0</span>
                </div>
                <ul className="space-y-2.5 text-sm text-[#71717A]">
                  <li className="flex items-start gap-2">
                    <Check className="w-4 h-4 text-[#1A7A4C] mt-0.5 flex-shrink-0" />
                    Limited analysis of your docs
                  </li>
                  <li className="flex items-start gap-2">
                    <Check className="w-4 h-4 text-[#1A7A4C] mt-0.5 flex-shrink-0" />
                    Core sections visible
                  </li>
                  <li className="flex items-start gap-2">
                    <Check className="w-4 h-4 text-[#1A7A4C] mt-0.5 flex-shrink-0" />
                    Some sections locked
                  </li>
                </ul>
              </div>
            </FadeIn>

            {/* Paid tier */}
            <FadeIn delay={0.1}>
              <div className="bg-white rounded-xl p-6 sm:p-8 shadow-[0_4px_12px_rgba(24,24,27,0.08),0_2px_4px_rgba(24,24,27,0.04)] border-2 border-[#1A7A4C] relative">
                <div className="absolute -top-3 left-6 bg-[#1A7A4C] text-white text-xs font-medium px-3 py-1 rounded-full">
                  Recommended
                </div>
                <h3 className="font-semibold text-[17px] mb-1">Full Agent Page</h3>
                <p className="text-sm text-[#71717A] mb-5">Complete, hosted, agent-optimized</p>
                <div className="mb-6">
                  <span className="text-3xl font-serif">$99</span>
                  <span className="text-sm text-[#71717A] ml-1">one-time</span>
                </div>
                <ul className="space-y-2.5 text-sm text-[#71717A]">
                  <li className="flex items-start gap-2">
                    <Check className="w-4 h-4 text-[#1A7A4C] mt-0.5 flex-shrink-0" />
                    Complete documentation analysis
                  </li>
                  <li className="flex items-start gap-2">
                    <Check className="w-4 h-4 text-[#1A7A4C] mt-0.5 flex-shrink-0" />
                    All sections unlocked
                  </li>
                  <li className="flex items-start gap-2">
                    <Check className="w-4 h-4 text-[#1A7A4C] mt-0.5 flex-shrink-0" />
                    Hosted agent page
                  </li>
                </ul>
                <p className="text-xs text-[#A1A1AA] mt-5">
                  Generate your page to get started
                </p>
              </div>
            </FadeIn>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  FINAL CTA                                                   */}
      {/* ============================================================ */}
      <section className="py-16 sm:py-20 border-t border-[#E2E2DC]">
        <div className="max-w-[520px] mx-auto px-4 sm:px-6">
          <FadeIn>
            <h2 className="font-serif text-3xl sm:text-[38px] leading-[1.15] tracking-[-0.01em] text-center mb-8">
              Give AI agents a front door to your product
            </h2>
          </FadeIn>

          <FadeIn delay={0.1}>
            <div className="bg-white rounded-2xl shadow-[0_4px_12px_rgba(24,24,27,0.08),0_2px_4px_rgba(24,24,27,0.04)] p-6 sm:p-8">
              <GenerateForm buttonLabel="Generate Free Preview" />
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  FOOTER                                                      */}
      {/* ============================================================ */}
      <footer className="border-t border-[#E2E2DC] py-10">
        <div className="max-w-[1100px] mx-auto px-4 sm:px-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 bg-[#1A7A4C] rounded-lg flex items-center justify-center">
                <Zap className="w-4 h-4 text-white" />
              </div>
              <span className="text-lg font-semibold font-serif">GrounDocs</span>
            </div>

            <div className="flex items-center gap-6">
              <Link to="/blog" className="text-sm text-[#71717A] hover:text-[#18181B] transition-colors">
                Blog
              </Link>
              <Link to="/support" className="text-sm text-[#71717A] hover:text-[#18181B] transition-colors">
                Support
              </Link>
              <a href="mailto:hello@groundocs.com" className="text-sm text-[#71717A] hover:text-[#18181B] transition-colors">
                Contact
              </a>
            </div>

            <p className="text-sm text-[#A1A1AA]">
              &copy; 2026 GrounDocs
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
