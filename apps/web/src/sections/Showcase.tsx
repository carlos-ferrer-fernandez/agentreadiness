import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { FileText, ArrowRight, Sparkles } from 'lucide-react'
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

interface PublicOptimization {
  id: string
  site_name: string
  url: string
  score: number
  grade: string
  page_count: number
  created_at: string
  is_seed?: boolean
}

export function Showcase() {
  const [optimizations, setOptimizations] = useState<PublicOptimization[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get(`${API_BASE}/api/v/public`)
      .then(r => setOptimizations(r.data))
      .catch(() => setOptimizations([]))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="min-h-screen bg-background">
      {/* Nav */}
      <nav className="border-b bg-background/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-7 h-7 bg-forest rounded-lg flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="font-semibold text-foreground">GrounDocs</span>
          </Link>
          <Link to="/" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            ← Back to home
          </Link>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="mb-12"
        >
          <h1 className="font-serif text-4xl md:text-5xl tracking-[-0.01em] mb-4">
            Optimized documentation
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl">
            Browse real documentation rewrites. See how GrounDocs transforms docs
            so AI agents can parse, cite, and recommend them.
          </p>
          <p className="text-sm text-muted-foreground mt-3">
            Companies marked <span className="font-medium text-foreground">Sample</span> are demonstration optimizations we ran to show output quality.
          </p>
        </motion.div>

        {loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-48 bg-muted animate-pulse rounded-xl" />
            ))}
          </div>
        )}

        {!loading && optimizations.length === 0 && (
          <div className="text-center py-24 text-muted-foreground">
            <FileText className="w-12 h-12 mx-auto mb-4 opacity-30" />
            <p className="text-lg font-medium">No optimizations yet</p>
            <p className="text-sm mt-2">Be the first — run your docs through GrounDocs.</p>
            <Link to="/" className="inline-flex items-center gap-2 mt-6 text-forest font-medium hover:underline">
              Score my docs <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        )}

        {!loading && optimizations.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {optimizations.map((opt, i) => (
              <motion.div
                key={opt.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: i * 0.05 }}
              >
                <Link
                  to={`/view/${opt.id}`}
                  className="block bg-card border rounded-xl p-6 hover:border-forest/40 hover:shadow-md transition-all group"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-foreground truncate group-hover:text-forest transition-colors">
                          {opt.site_name}
                        </h3>
                        {opt.is_seed && (
                          <span className="flex-shrink-0 text-[10px] font-medium px-1.5 py-0.5 rounded bg-muted text-muted-foreground border">
                            Sample
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground mt-1 truncate">
                        {opt.url}
                      </p>
                    </div>
                    <span className={`ml-3 inline-flex items-center px-2.5 py-1 rounded-lg text-sm font-bold border ${GRADE_COLORS[opt.grade] || 'text-muted-foreground bg-muted border-border'}`}>
                      {opt.grade}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <span>{opt.page_count} pages optimized</span>
                    <span className="flex items-center gap-1 text-forest font-medium group-hover:gap-2 transition-all">
                      View <ArrowRight className="w-3.5 h-3.5" />
                    </span>
                  </div>

                  {/* Score bar */}
                  <div className="mt-4 h-1.5 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-forest rounded-full transition-all"
                      style={{ width: `${opt.score}%` }}
                    />
                  </div>
                  <p className="text-xs text-muted-foreground mt-1.5">Score: {opt.score}/100</p>
                </Link>
              </motion.div>
            ))}
          </div>
        )}

        {!loading && optimizations.length > 0 && (
          <div className="mt-16 text-center">
            <p className="text-muted-foreground mb-4">Your docs not here yet?</p>
            <Link
              to="/"
              className="inline-flex items-center gap-2 px-6 py-3 bg-forest text-white rounded-lg font-medium hover:bg-forest-hover transition-colors"
            >
              Score my docs <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}
