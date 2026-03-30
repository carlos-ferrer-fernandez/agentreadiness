import { useState } from 'react'
import { Link } from 'react-router-dom'
import { BLOG_POSTS } from '@/data/blogPosts'

const CATEGORY_COLORS: Record<string, string> = {
  Strategy: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
  Discoverability: 'bg-blue-500/10 text-blue-400 border border-blue-500/20',
  Answerability: 'bg-violet-500/10 text-violet-400 border border-violet-500/20',
  Operability: 'bg-amber-500/10 text-amber-400 border border-amber-500/20',
  Trustability: 'bg-rose-500/10 text-rose-400 border border-rose-500/20',
}

export function Blog() {
  const categories = ['All', ...Array.from(new Set(BLOG_POSTS.map((p) => p.category)))]
  const [activeCategory, setActiveCategory] = useState('All')

  const filtered =
    activeCategory === 'All' ? BLOG_POSTS : BLOG_POSTS.filter((p) => p.category === activeCategory)

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Nav */}
      <nav className="border-b bg-background/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="container mx-auto px-4 h-14 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-lg bg-emerald-500 flex items-center justify-center">
              <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <span className="text-sm font-semibold">GrounDocs</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link to="/" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              ← Back to home
            </Link>
            <Link
              to="/"
              className="text-sm font-medium bg-emerald-500 hover:bg-emerald-600 text-white px-4 py-1.5 rounded-lg transition-colors"
            >
              Get Free Score
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <div className="border-b bg-muted/20">
        <div className="container mx-auto px-4 py-16 max-w-4xl">
          <div className="inline-flex items-center gap-2 text-xs text-emerald-400 font-medium bg-emerald-500/10 border border-emerald-500/20 rounded-full px-3 py-1 mb-6">
            <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" fill="none" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Agent-First Documentation
          </div>
          <h1 className="text-4xl font-bold tracking-tight mb-4">
            Learn to Write Documentation<br />
            <span className="text-emerald-400">That AI Agents Can Actually Use</span>
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl">
            Deep guides on the 20 rules of agent-first documentation — the framework used by
            leading developer tools to become the default recommendation of AI assistants.
          </p>
        </div>
      </div>

      {/* Category filter */}
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="flex flex-wrap gap-2 mb-10">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`text-sm px-4 py-1.5 rounded-full font-medium transition-colors ${
                activeCategory === cat
                  ? 'bg-emerald-500 text-white'
                  : 'bg-muted text-muted-foreground hover:text-foreground hover:bg-muted/80'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Articles grid */}
        <div className="grid gap-6 sm:grid-cols-2">
          {filtered.map((post, i) => (
            <Link
              key={post.slug}
              to={`/blog/${post.slug}`}
              className="group block rounded-xl border bg-card p-6 hover:border-emerald-500/40 hover:shadow-lg hover:shadow-emerald-500/5 transition-all duration-200"
            >
              {/* Category + reading time */}
              <div className="flex items-center justify-between mb-4">
                <span
                  className={`text-xs font-medium px-2.5 py-1 rounded-full ${
                    CATEGORY_COLORS[post.category] ?? 'bg-muted text-muted-foreground'
                  }`}
                >
                  {post.category}
                </span>
                <span className="text-xs text-muted-foreground">{post.readingTime} min read</span>
              </div>

              {/* Number indicator for series */}
              {i < 6 && (
                <div className="text-xs text-muted-foreground/50 font-mono mb-1">
                  {String(i + 1).padStart(2, '0')}
                </div>
              )}

              <h2 className="text-base font-semibold leading-snug mb-2 group-hover:text-emerald-400 transition-colors line-clamp-2">
                {post.title}
              </h2>
              <p className="text-sm text-muted-foreground line-clamp-2 mb-4">
                {post.description}
              </p>

              {/* Footer */}
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>{post.date}</span>
                <span className="text-emerald-400 group-hover:translate-x-0.5 transition-transform">
                  Read article →
                </span>
              </div>
            </Link>
          ))}
        </div>

        {/* Bottom CTA */}
        <div className="mt-16 rounded-2xl border bg-muted/30 p-8 text-center">
          <h2 className="text-xl font-semibold mb-2">See How Your Docs Score</h2>
          <p className="text-sm text-muted-foreground mb-6 max-w-md mx-auto">
            Run a free analysis on your documentation and get a detailed report against all 20
            agent-first rules.
          </p>
          <Link
            to="/"
            className="inline-flex items-center gap-2 bg-emerald-500 hover:bg-emerald-600 text-white font-medium px-6 py-2.5 rounded-lg transition-colors text-sm"
          >
            Get your free documentation score
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </Link>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t mt-12 py-8">
        <div className="container mx-auto px-4 text-center text-xs text-muted-foreground">
          © 2025 GrounDocs. Making documentation AI-ready.
        </div>
      </footer>
    </div>
  )
}
