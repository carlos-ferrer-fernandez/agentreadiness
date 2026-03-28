import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Sparkles, ArrowLeft, ExternalLink, CheckCircle, FileText } from 'lucide-react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'https://agentreadiness-api.onrender.com'

const GRADE_COLORS: Record<string, string> = {
  'A+': 'text-green-700 bg-green-50 border-green-200',
  'A':  'text-green-700 bg-green-50 border-green-200',
  'A-': 'text-green-600 bg-green-50 border-green-200',
  'B+': 'text-lime-700 bg-lime-50 border-lime-200',
  'B':  'text-lime-700 bg-lime-50 border-lime-200',
  'B-': 'text-lime-600 bg-lime-50 border-lime-200',
  'C+': 'text-amber-700 bg-amber-50 border-amber-200',
  'C':  'text-amber-700 bg-amber-50 border-amber-200',
  'C-': 'text-amber-600 bg-amber-50 border-amber-200',
  'D':  'text-orange-700 bg-orange-50 border-orange-200',
  'F':  'text-red-700 bg-red-50 border-red-200',
}

interface PageMeta {
  file_name: string
  title: string
  original_url: string
  improvements: string[]
}

interface ViewerIndex {
  id: string
  site_name: string
  url: string
  score: number
  grade: string
  pages: PageMeta[]
  created_at: string
  is_seed?: boolean
}

interface PageContent {
  title: string
  original_url: string
  optimized_content: string
  improvements: string[]
  site_name: string
}

export function Viewer() {
  const { assessmentId, fileName } = useParams<{ assessmentId: string; fileName?: string }>()
  const [index, setIndex] = useState<ViewerIndex | null>(null)
  const [page, setPage] = useState<PageContent | null>(null)
  const [loading, setLoading] = useState(true)
  const [pageLoading, setPageLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!assessmentId) return
    axios.get(`${API_BASE}/api/v/${assessmentId}`)
      .then(r => {
        setIndex(r.data)
        // Auto-load first page
        if (!fileName && r.data.pages.length > 0) {
          loadPage(r.data.pages[0].file_name)
        }
      })
      .catch(e => setError(e.response?.status === 403 ? 'This optimization is private.' : 'Optimization not found.'))
      .finally(() => setLoading(false))
  }, [assessmentId])

  useEffect(() => {
    if (fileName) loadPage(fileName)
  }, [fileName])

  function loadPage(file: string) {
    if (!assessmentId) return
    setPageLoading(true)
    axios.get(`${API_BASE}/api/v/${assessmentId}/${file}`)
      .then(r => setPage(r.data))
      .finally(() => setPageLoading(false))
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <div className="w-8 h-8 border-2 border-forest border-t-transparent rounded-full animate-spin" />
          <p className="text-sm">Loading optimization…</p>
        </div>
      </div>
    )
  }

  if (error || !index) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <p className="text-lg font-medium text-foreground mb-2">{error || 'Not found'}</p>
          <Link to="/showcase" className="text-forest hover:underline text-sm">← Browse showcase</Link>
        </div>
      </div>
    )
  }

  const activePage = fileName || index.pages[0]?.file_name

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Nav */}
      <nav className="border-b bg-background/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-7 h-7 bg-forest rounded-lg flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="font-semibold text-foreground">GrounDocs</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link to="/showcase" className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1">
              <ArrowLeft className="w-3.5 h-3.5" /> Showcase
            </Link>
            <a href={index.url} target="_blank" rel="noopener noreferrer"
               className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1">
              Original docs <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>
      </nav>

      {/* Header */}
      <div className="border-b bg-muted/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="font-serif text-2xl md:text-3xl tracking-[-0.01em]">
                  {index.site_name}
                </h1>
                {index.is_seed && (
                  <span className="text-xs font-medium px-2 py-0.5 rounded bg-muted text-muted-foreground border">
                    Sample
                  </span>
                )}
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                {index.pages.length} pages optimized for AI agents
                {index.is_seed && ' · demonstration optimization'}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="text-right">
                <p className="text-xs text-muted-foreground">Original score</p>
                <p className="text-2xl font-bold text-foreground">{index.score}</p>
              </div>
              <span className={`inline-flex items-center px-3 py-1.5 rounded-lg text-lg font-bold border ${GRADE_COLORS[index.grade] || 'text-muted-foreground bg-muted border-border'}`}>
                {index.grade}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6 gap-6">
        {/* Sidebar */}
        <aside className="w-64 flex-shrink-0">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
            Pages
          </p>
          <nav className="space-y-1">
            {index.pages.map(p => (
              <button
                key={p.file_name}
                onClick={() => loadPage(p.file_name)}
                className={`w-full text-left flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  activePage === p.file_name
                    ? 'bg-forest text-white'
                    : 'text-foreground hover:bg-muted'
                }`}
              >
                <FileText className="w-3.5 h-3.5 flex-shrink-0" />
                <span className="truncate">{p.title}</span>
              </button>
            ))}
          </nav>

          <div className="mt-8 p-4 bg-forest-light/40 border border-forest/20 rounded-xl">
            <p className="text-xs font-medium text-forest mb-1">Want yours?</p>
            <p className="text-xs text-muted-foreground mb-3">
              Get your docs optimized for AI agents.
            </p>
            <Link
              to="/"
              className="block text-center text-xs font-medium text-white bg-forest hover:bg-forest-hover px-3 py-2 rounded-lg transition-colors"
            >
              Score my docs →
            </Link>
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 min-w-0">
          {pageLoading && (
            <div className="flex items-center justify-center h-64 text-muted-foreground">
              <div className="w-6 h-6 border-2 border-forest border-t-transparent rounded-full animate-spin" />
            </div>
          )}

          {!pageLoading && page && (
            <motion.div
              key={page.title}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
            >
              {/* Page header */}
              <div className="mb-6 pb-4 border-b">
                <div className="flex items-start justify-between gap-4">
                  <h2 className="font-serif text-2xl tracking-[-0.01em]">{page.title}</h2>
                  <a
                    href={page.original_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-shrink-0 text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 mt-1"
                  >
                    Original <ExternalLink className="w-3 h-3" />
                  </a>
                </div>

                {page.improvements.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {page.improvements.slice(0, 5).map((imp, i) => (
                      <span key={i} className="inline-flex items-center gap-1 px-2 py-1 bg-forest-light/60 border border-forest/20 rounded-md text-xs text-forest font-medium">
                        <CheckCircle className="w-3 h-3" />
                        {imp}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Optimized content rendered as markdown */}
              <div className="prose prose-sm max-w-none
                prose-headings:font-serif prose-headings:tracking-tight
                prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg
                prose-code:bg-muted prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm prose-code:font-mono
                prose-pre:bg-slate-950 prose-pre:text-slate-100
                prose-a:text-forest prose-a:no-underline hover:prose-a:underline
                prose-blockquote:border-forest/30
              ">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {page.optimized_content}
                </ReactMarkdown>
              </div>
            </motion.div>
          )}

          {!pageLoading && !page && (
            <div className="flex items-center justify-center h-64 text-muted-foreground text-sm">
              Select a page from the sidebar
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
