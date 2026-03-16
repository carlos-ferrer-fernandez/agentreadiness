import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  Plus, 
  ExternalLink, 
  TrendingUp, 
  TrendingDown,
  MoreVertical,
  Search,
  Bell,
  Settings,
  Loader2,
  Zap,
  Globe,
  FileText,
  BarChart3
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScoreCard } from '@/components/score/ScoreCard'
import { ScoreTrend } from '@/components/score/ScoreTrend'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { DocumentationSite, FriendlinessScore } from '@/types'
import { scoreToGrade } from '@/lib/utils'
import { sitesApi } from '@/lib/api'
import { useSitesStore, useUIStore } from '@/store'

interface DashboardProps {
  isAuthenticated: boolean
  onAuthChange: (value: boolean) => void
}

// Mock data for initial display
const mockSites: DocumentationSite[] = [
  {
    id: '1',
    url: 'https://docs.resend.com',
    name: 'Resend Documentation',
    status: 'READY',
    organizationId: '1',
    pageCount: 156,
    lastCrawledAt: '2025-03-01T10:00:00Z',
    createdAt: '2025-01-15T00:00:00Z',
    updatedAt: '2025-03-01T10:00:00Z',
  },
  {
    id: '2',
    url: 'https://vercel.com/docs',
    name: 'Vercel Docs',
    status: 'READY',
    organizationId: '1',
    pageCount: 423,
    lastCrawledAt: '2025-02-28T15:30:00Z',
    createdAt: '2025-01-20T00:00:00Z',
    updatedAt: '2025-02-28T15:30:00Z',
  },
  {
    id: '3',
    url: 'https://stripe.com/docs',
    name: 'Stripe Documentation',
    status: 'CRAWLING',
    organizationId: '1',
    createdAt: '2025-03-02T00:00:00Z',
    updatedAt: '2025-03-02T00:00:00Z',
  },
]

const mockScores: Record<string, FriendlinessScore> = {
  '1': {
    overall: 92,
    grade: 'A-',
    components: {
      accuracy: 94,
      contextUtilization: 89,
      latency: 91,
      citationQuality: 95,
      codeExecutability: 93,
    },
    queryCount: 150,
    passRate: 0.89,
    avgLatencyMs: 1250,
    percentile: 87,
    trend: 5,
  },
  '2': {
    overall: 87,
    grade: 'B+',
    components: {
      accuracy: 89,
      contextUtilization: 85,
      latency: 88,
      citationQuality: 90,
      codeExecutability: 86,
    },
    queryCount: 200,
    passRate: 0.84,
    avgLatencyMs: 1420,
    percentile: 73,
    trend: -2,
  },
}

const mockTrendData = [
  { date: '2025-01-15', score: 78, grade: 'C+' },
  { date: '2025-01-30', score: 82, grade: 'B-' },
  { date: '2025-02-15', score: 85, grade: 'B' },
  { date: '2025-03-01', score: 87, grade: 'B+' },
  { date: '2025-03-15', score: 92, grade: 'A-' },
]

export function Dashboard({ isAuthenticated, onAuthChange }: DashboardProps) {
  const [sites, setSites] = useState<DocumentationSite[]>(mockSites)
  const [searchQuery, setSearchQuery] = useState('')
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)
  const [newSiteUrl, setNewSiteUrl] = useState('')
  const [newSiteName, setNewSiteName] = useState('')
  const [isAdding, setIsAdding] = useState(false)
  const { addNotification } = useUIStore()

  const filteredSites = sites.filter(site => 
    site.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    site.url.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'success' | 'warning' | 'destructive'> = {
      PENDING: 'secondary',
      VERIFIED: 'default',
      CRAWLING: 'warning',
      READY: 'success',
      ERROR: 'destructive',
    }
    return <Badge variant={variants[status] || 'default'}>{status}</Badge>
  }

  const handleAddSite = async () => {
    if (!newSiteUrl || !newSiteName) return
    
    setIsAdding(true)
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      const newSite: DocumentationSite = {
        id: Math.random().toString(36).substr(2, 9),
        url: newSiteUrl,
        name: newSiteName,
        status: 'PENDING',
        organizationId: '1',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      }
      
      setSites([...sites, newSite])
      setIsAddDialogOpen(false)
      setNewSiteUrl('')
      setNewSiteName('')
      
      addNotification({
        type: 'success',
        message: `Added ${newSiteName} successfully`,
      })
    } catch (error) {
      addNotification({
        type: 'error',
        message: 'Failed to add site',
      })
    } finally {
      setIsAdding(false)
    }
  }

  // Calculate stats
  const avgScore = Object.values(mockScores).reduce((acc, s) => acc + s.overall, 0) / Object.keys(mockScores).length
  const totalPages = sites.reduce((acc, s) => acc + (s.pageCount || 0), 0)

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center gap-8">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                  <Zap className="w-5 h-5 text-primary-foreground" />
                </div>
                <span className="text-xl font-bold">AgentReadiness</span>
              </div>
              <nav className="hidden md:flex items-center gap-6">
                <a href="/dashboard" className="text-sm font-medium text-foreground">
                  Dashboard
                </a>
                <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Sites
                </a>
                <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Analyses
                </a>
                <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Reports
                </a>
              </nav>
            </div>
            
            <div className="flex items-center gap-4">
              <button className="p-2 text-muted-foreground hover:text-foreground transition-colors">
                <Search className="w-5 h-5" />
              </button>
              <button className="p-2 text-muted-foreground hover:text-foreground transition-colors relative">
                <Bell className="w-5 h-5" />
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
              </button>
              <div className="flex items-center gap-3 pl-4 border-l">
                <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium">JD</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold">Dashboard</h1>
            <p className="text-muted-foreground">
              Monitor and optimize your documentation for AI agent consumption.
            </p>
          </div>
          
          <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                Add Documentation Site
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add Documentation Site</DialogTitle>
                <DialogDescription>
                  Enter your documentation site details to start analyzing.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Site Name</label>
                  <Input
                    placeholder="e.g., My API Docs"
                    value={newSiteName}
                    onChange={(e) => setNewSiteName(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Documentation URL</label>
                  <Input
                    placeholder="https://docs.example.com"
                    value={newSiteUrl}
                    onChange={(e) => setNewSiteUrl(e.target.value)}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
                  Cancel
                </Button>
                <Button 
                  onClick={handleAddSite} 
                  disabled={!newSiteUrl || !newSiteName || isAdding}
                >
                  {isAdding && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                  Add Site
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        {/* Stats Overview */}
        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total Sites</p>
                  <p className="text-2xl font-bold">{sites.length}</p>
                </div>
                <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                  <Globe className="w-5 h-5 text-primary" />
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Avg Score</p>
                  <p className="text-2xl font-bold">{avgScore.toFixed(1)}</p>
                </div>
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total Pages</p>
                  <p className="text-2xl font-bold">{totalPages}</p>
                </div>
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <FileText className="w-5 h-5 text-blue-600" />
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Analyses</p>
                  <p className="text-2xl font-bold">12</p>
                </div>
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                  <BarChart3 className="w-5 h-5 text-purple-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Sites List */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle>Documentation Sites</CardTitle>
                  <div className="relative w-64">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      placeholder="Search sites..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-9 h-9"
                    />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {filteredSites.map((site) => {
                    const score = mockScores[site.id]
                    return (
                      <motion.div
                        key={site.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex items-center justify-between p-4 border rounded-lg hover:border-primary/50 transition-colors cursor-pointer group"
                      >
                        <div className="flex items-center gap-4">
                          <div className="w-12 h-12 bg-primary/5 rounded-lg flex items-center justify-center">
                            <span className="text-lg font-bold text-primary">
                              {site.name.charAt(0)}
                            </span>
                          </div>
                          <div>
                            <h3 className="font-medium group-hover:text-primary transition-colors">
                              {site.name}
                            </h3>
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                              <span>{site.url}</span>
                              <span>•</span>
                              {getStatusBadge(site.status)}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-6">
                          {score ? (
                            <div className="text-right">
                              <div className="flex items-center gap-2">
                                <span 
                                  className="text-2xl font-bold"
                                  style={{ color: getGradeColor(score.grade) }}
                                >
                                  {score.overall}
                                </span>
                                <span 
                                  className="text-sm font-medium"
                                  style={{ color: getGradeColor(score.grade) }}
                                >
                                  {score.grade}
                                </span>
                              </div>
                              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                {score.trend && score.trend > 0 ? (
                                  <>
                                    <TrendingUp className="w-3 h-3 text-green-600" />
                                    <span className="text-green-600">+{score.trend}</span>
                                  </>
                                ) : score.trend && score.trend < 0 ? (
                                  <>
                                    <TrendingDown className="w-3 h-3 text-red-600" />
                                    <span className="text-red-600">{score.trend}</span>
                                  </>
                                ) : (
                                  <span>No change</span>
                                )}
                              </div>
                            </div>
                          ) : (
                            <div className="text-right text-muted-foreground">
                              <span className="text-sm">Analyzing...</span>
                            </div>
                          )}
                          <button className="p-2 hover:bg-muted rounded-lg transition-colors">
                            <MoreVertical className="w-4 h-4" />
                          </button>
                        </div>
                      </motion.div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Overall Score */}
            <Card>
              <CardHeader>
                <CardTitle>Overall Score</CardTitle>
              </CardHeader>
              <CardContent className="flex justify-center">
                <ScoreCard
                  score={Math.round(avgScore)}
                  grade={scoreToGrade(Math.round(avgScore))}
                  trend={3}
                  percentile={82}
                  size="lg"
                />
              </CardContent>
            </Card>

            {/* Score Trend */}
            <ScoreTrend data={mockTrendData} />

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    { action: 'Analysis completed', target: 'Resend Documentation', time: '2 hours ago' },
                    { action: 'Score improved', target: 'Vercel Docs', time: '1 day ago' },
                    { action: 'New site added', target: 'Stripe Documentation', time: '2 days ago' },
                    { action: 'Recommendation applied', target: 'Resend Documentation', time: '3 days ago' },
                  ].map((activity, index) => (
                    <div key={index} className="flex items-start gap-3">
                      <div className="w-2 h-2 bg-primary rounded-full mt-2"></div>
                      <div>
                        <p className="text-sm font-medium">{activity.action}</p>
                        <p className="text-sm text-muted-foreground">{activity.target}</p>
                        <p className="text-xs text-muted-foreground">{activity.time}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  )
}

function getGradeColor(grade: string): string {
  const colors: Record<string, string> = {
    'A+': '#15803d',
    'A': '#16a34a',
    'A-': '#22c55e',
    'B+': '#65a30d',
    'B': '#84cc16',
    'B-': '#a3e635',
    'C+': '#ca8a04',
    'C': '#eab308',
    'C-': '#facc15',
    'D': '#f97316',
    'F': '#ef4444',
  }
  return colors[grade] || '#6b7280'
}
