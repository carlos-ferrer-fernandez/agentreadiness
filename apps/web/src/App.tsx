import { useEffect, useRef } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { LandingPage } from '@/sections/LandingPage'
import { Dashboard } from '@/sections/Dashboard'
import { SiteDetail } from '@/sections/SiteDetail'
import { AnalysisResults } from '@/sections/AnalysisResults'
import { AssessmentResults } from '@/sections/AssessmentResults'
import { Support } from '@/sections/Support'
import { Showcase } from '@/sections/Showcase'
import { Viewer } from '@/sections/Viewer'
import { Blog } from '@/sections/Blog'
import { BlogPost } from '@/sections/BlogPost'
import AgentPageView from '@/sections/AgentPageView'
import PackageView from '@/sections/PackageView'
import { ToastContainer } from '@/components/ui/toast'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { useUIStore } from '@/store'

function App() {
  const { notifications, removeNotification } = useUIStore()
  const timersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map())

  // Auto-remove notifications after 5 seconds (with proper cleanup)
  useEffect(() => {
    notifications.forEach((notification) => {
      if (!timersRef.current.has(notification.id)) {
        const timer = setTimeout(() => {
          removeNotification(notification.id)
          timersRef.current.delete(notification.id)
        }, 5000)
        timersRef.current.set(notification.id, timer)
      }
    })

    // Cleanup timers for removed notifications
    const activeIds = new Set(notifications.map((n) => n.id))
    timersRef.current.forEach((timer, id) => {
      if (!activeIds.has(id)) {
        clearTimeout(timer)
        timersRef.current.delete(id)
      }
    })
  }, [notifications, removeNotification])

  // Cleanup all timers on unmount
  useEffect(() => {
    return () => {
      timersRef.current.forEach((timer) => clearTimeout(timer))
    }
  }, [])

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/assessment" element={<AssessmentResults />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/sites/:siteId" element={<SiteDetail />} />
          <Route path="/analyses/:analysisId" element={<AnalysisResults />} />
          <Route path="/support" element={<Support />} />
          <Route path="/showcase" element={<Showcase />} />
          <Route path="/blog" element={<Blog />} />
          <Route path="/blog/:slug" element={<BlogPost />} />
          <Route path="/agent-pages/:slug" element={<AgentPageView />} />
          <Route path="/packages/:slug" element={<PackageView />} />
          <Route path="/packages/:slug/:pageSlug" element={<PackageView />} />
          <Route path="/examples/:slug/:pageSlug" element={<PackageView />} />
          <Route path="/view/:assessmentId" element={<Viewer />} />
          <Route path="/view/:assessmentId/:fileName" element={<Viewer />} />
        </Routes>
        <ToastContainer toasts={notifications} onRemove={removeNotification} />
      </BrowserRouter>
    </ErrorBoundary>
  )
}

export default App
