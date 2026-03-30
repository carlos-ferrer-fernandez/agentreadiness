import { useParams, Link, Navigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { getPost, BLOG_POSTS } from '@/data/blogPosts'
import type { Components } from 'react-markdown'

const CATEGORY_COLORS: Record<string, string> = {
  Strategy: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
  Discoverability: 'bg-blue-500/10 text-blue-400 border border-blue-500/20',
  Answerability: 'bg-violet-500/10 text-violet-400 border border-violet-500/20',
  Operability: 'bg-amber-500/10 text-amber-400 border border-amber-500/20',
  Trustability: 'bg-rose-500/10 text-rose-400 border border-rose-500/20',
}

// Intercept internal /blog/ links to use React Router
const markdownComponents: Components = {
  a({ href, children, ...props }) {
    if (href && href.startsWith('/blog/')) {
      return (
        <Link to={href} className="text-emerald-400 hover:text-emerald-300 underline underline-offset-2">
          {children}
        </Link>
      )
    }
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" className="text-emerald-400 hover:text-emerald-300 underline underline-offset-2" {...props}>
        {children}
      </a>
    )
  },
  h1({ children, ...props }) {
    return <h1 className="text-3xl font-bold tracking-tight mt-10 mb-4 first:mt-0" {...props}>{children}</h1>
  },
  h2({ children, ...props }) {
    return <h2 className="text-2xl font-semibold tracking-tight mt-10 mb-4 border-b border-border pb-2" {...props}>{children}</h2>
  },
  h3({ children, ...props }) {
    return <h3 className="text-xl font-semibold mt-8 mb-3" {...props}>{children}</h3>
  },
  h4({ children, ...props }) {
    return <h4 className="text-base font-semibold mt-6 mb-2" {...props}>{children}</h4>
  },
  p({ children, ...props }) {
    return <p className="leading-7 text-muted-foreground mb-4" {...props}>{children}</p>
  },
  ul({ children, ...props }) {
    return <ul className="my-4 ml-6 list-disc [&>li]:mt-2 text-muted-foreground" {...props}>{children}</ul>
  },
  ol({ children, ...props }) {
    return <ol className="my-4 ml-6 list-decimal [&>li]:mt-2 text-muted-foreground" {...props}>{children}</ol>
  },
  li({ children, ...props }) {
    return <li className="leading-7" {...props}>{children}</li>
  },
  blockquote({ children, ...props }) {
    return (
      <blockquote className="mt-6 border-l-4 border-emerald-500 pl-6 italic text-muted-foreground" {...props}>
        {children}
      </blockquote>
    )
  },
  code({ children, className, ...props }) {
    const isInline = !className
    if (isInline) {
      return (
        <code className="relative rounded bg-muted px-[0.3rem] py-[0.2rem] font-mono text-sm text-emerald-400" {...props}>
          {children}
        </code>
      )
    }
    return (
      <code className="font-mono text-sm" {...props}>
        {children}
      </code>
    )
  },
  pre({ children, ...props }) {
    return (
      <pre className="my-6 overflow-x-auto rounded-xl border bg-muted p-4 text-sm font-mono leading-relaxed" {...props}>
        {children}
      </pre>
    )
  },
  table({ children, ...props }) {
    return (
      <div className="my-6 overflow-x-auto rounded-xl border">
        <table className="w-full text-sm" {...props}>{children}</table>
      </div>
    )
  },
  thead({ children, ...props }) {
    return <thead className="bg-muted/50" {...props}>{children}</thead>
  },
  th({ children, ...props }) {
    return <th className="px-4 py-3 text-left font-semibold text-foreground border-b" {...props}>{children}</th>
  },
  td({ children, ...props }) {
    return <td className="px-4 py-3 text-muted-foreground border-b border-border/50" {...props}>{children}</td>
  },
  hr() {
    return <hr className="my-8 border-border" />
  },
  strong({ children, ...props }) {
    return <strong className="font-semibold text-foreground" {...props}>{children}</strong>
  },
}

export function BlogPost() {
  const { slug } = useParams<{ slug: string }>()
  const post = slug ? getPost(slug) : undefined

  if (!post) {
    return <Navigate to="/blog" replace />
  }

  // Find adjacent posts
  const currentIndex = BLOG_POSTS.findIndex((p) => p.slug === slug)
  const prevPost = currentIndex > 0 ? BLOG_POSTS[currentIndex - 1] : null
  const nextPost = currentIndex < BLOG_POSTS.length - 1 ? BLOG_POSTS[currentIndex + 1] : null

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
            <Link to="/blog" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              ← All articles
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

      <div className="container mx-auto px-4 py-12 max-w-3xl">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-xs text-muted-foreground mb-8">
          <Link to="/" className="hover:text-foreground transition-colors">Home</Link>
          <span>/</span>
          <Link to="/blog" className="hover:text-foreground transition-colors">Blog</Link>
          <span>/</span>
          <span className="text-foreground truncate max-w-48">{post.title}</span>
        </nav>

        {/* Header */}
        <header className="mb-10">
          <div className="flex items-center gap-3 mb-4">
            <span
              className={`text-xs font-medium px-2.5 py-1 rounded-full ${
                CATEGORY_COLORS[post.category] ?? 'bg-muted text-muted-foreground'
              }`}
            >
              {post.category}
            </span>
            <span className="text-xs text-muted-foreground">{post.readingTime} min read</span>
            <span className="text-xs text-muted-foreground">·</span>
            <span className="text-xs text-muted-foreground">{post.date}</span>
          </div>

          <h1 className="text-3xl md:text-4xl font-bold tracking-tight leading-tight mb-4">
            {post.title}
          </h1>
          <p className="text-lg text-muted-foreground leading-relaxed">
            {post.description}
          </p>
        </header>

        {/* Article content */}
        <article className="prose-sm max-w-none">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={markdownComponents}
          >
            {post.content}
          </ReactMarkdown>
        </article>

        {/* Keywords */}
        <div className="mt-10 pt-8 border-t">
          <div className="flex flex-wrap gap-2">
            {post.keywords.map((kw) => (
              <span key={kw} className="text-xs px-3 py-1 rounded-full bg-muted text-muted-foreground">
                {kw}
              </span>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div className="mt-10 rounded-2xl border bg-emerald-500/5 border-emerald-500/20 p-8 text-center">
          <h2 className="text-lg font-semibold mb-2">See How Your Documentation Scores</h2>
          <p className="text-sm text-muted-foreground mb-5 max-w-md mx-auto">
            Get a free analysis of your docs against all 20 agent-first documentation rules. Know
            exactly what AI agents see when they read your content.
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

        {/* Prev / Next navigation */}
        {(prevPost || nextPost) && (
          <div className="mt-10 grid sm:grid-cols-2 gap-4">
            {prevPost ? (
              <Link
                to={`/blog/${prevPost.slug}`}
                className="group rounded-xl border bg-card p-5 hover:border-emerald-500/40 transition-colors"
              >
                <div className="text-xs text-muted-foreground mb-1">← Previous</div>
                <div className="text-sm font-medium group-hover:text-emerald-400 transition-colors line-clamp-2">
                  {prevPost.title}
                </div>
              </Link>
            ) : (
              <div />
            )}
            {nextPost ? (
              <Link
                to={`/blog/${nextPost.slug}`}
                className="group rounded-xl border bg-card p-5 hover:border-emerald-500/40 transition-colors text-right sm:text-right"
              >
                <div className="text-xs text-muted-foreground mb-1">Next →</div>
                <div className="text-sm font-medium group-hover:text-emerald-400 transition-colors line-clamp-2">
                  {nextPost.title}
                </div>
              </Link>
            ) : (
              <div />
            )}
          </div>
        )}
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
