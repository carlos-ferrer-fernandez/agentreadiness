import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  ArrowLeft, 
  ExternalLink, 
  Play, 
  Settings, 
  Trash2,
  CheckCircle2,
  AlertCircle,
  FileText,
  BarChart3
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { ScoreCard } from '@/components/score/ScoreCard'
import { ScoreTrend } from '@/components/score/ScoreTrend'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

const mockSite = {
  id: '1',
  url: 'https://docs.resend.com',
  name: 'Resend Documentation',
  status: 'READY',
  pageCount: 156,
  lastCrawledAt: '2025-03-01T10:00:00Z',
  createdAt: '2025-01-15T00:00:00Z',
}

const mockScore = {
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
}

const mockTrendData = [
  { date: '2025-01-15', score: 78, grade: 'C+' },
  { date: '2025-01-30', score: 82, grade: 'B-' },
  { date: '2025-02-15', score: 85, grade: 'B' },
  { date: '2025-03-01', score: 87, grade: 'B+' },
  { date: '2025-03-15', score: 92, grade: 'A-' },
]

const mockRecommendations = [
  {
    id: '1',
    category: 'content_gap',
    title: 'Add more async/await examples',
    description: 'Developers frequently ask about error handling with async operations. Adding comprehensive examples would improve accuracy.',
    impact: 'high',
    effort: 'medium',
    affectedPages: 3,
    estimatedImprovement: 3,
  },
  {
    id: '2',
    category: 'structure',
    title: 'Improve API reference organization',
    description: 'The API reference pages could benefit from better cross-linking and clearer hierarchical structure.',
    impact: 'medium',
    effort: 'low',
    affectedPages: 12,
    estimatedImprovement: 2,
  },
  {
    id: '3',
    category: 'code_quality',
    title: 'Fix syntax errors in Python examples',
    description: 'Several Python code examples have syntax errors that prevent them from running correctly.',
    impact: 'high',
    effort: 'low',
    affectedPages: 5,
    estimatedImprovement: 4,
  },
]

const mockQueryResults = [
  {
    id: '1',
    query: 'How do I send an email with attachments?',
    category: 'how_to',
    difficulty: 'intermediate',
    passed: true,
    confidence: 0.94,
  },
  {
    id: '2',
    query: 'What are the rate limits for the API?',
    category: 'reference',
    difficulty: 'beginner',
    passed: true,
    confidence: 0.98,
  },
  {
    id: '3',
    query: 'How do I handle webhook retries?',
    category: 'troubleshooting',
    difficulty: 'advanced',
    passed: false,
    confidence: 0.45,
  },
  {
    id: '4',
    query: 'Explain the difference between batch and single send',
    category: 'conceptual',
    difficulty: 'intermediate',
    passed: true,
    confidence: 0.87,
  },
]

export function SiteDetail() {
  const _params = useParams()
  const [activeTab, setActiveTab] = useState('overview')

  const getImpactColor = (impact: string) => {
    const colors: Record<string, string> = {
      high: 'bg-red-100 text-red-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-green-100 text-green-800',
    }
    return colors[impact] || 'bg-gray-100 text-gray-800'
  }

  const getEffortColor = (effort: string) => {
    const colors: Record<string, string> = {
      high: 'bg-red-100 text-red-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-green-100 text-green-800',
    }
    return colors[effort] || 'bg-gray-100 text-gray-800'
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center gap-4">
              <Link to="/dashboard">
                <Button variant="ghost" size="sm">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Dashboard
                </Button>
              </Link>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm">
                <ExternalLink className="w-4 h-4 mr-2" />
                View Site
              </Button>
              <Button variant="outline" size="sm">
                <Settings className="w-4 h-4 mr-2" />
                Settings
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Site Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-3xl font-bold">{mockSite.name}</h1>
            <Badge variant="success">{mockSite.status}</Badge>
          </div>
          <a 
            href={mockSite.url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-muted-foreground hover:text-primary transition-colors flex items-center gap-1"
          >
            {mockSite.url}
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 lg:w-[400px]">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="queries">Queries</TabsTrigger>
            <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid lg:grid-cols-3 gap-6">
              {/* Score Card */}
              <Card>
                <CardHeader>
                  <CardTitle>Friendliness Score</CardTitle>
                  <CardDescription>Overall agent-readiness rating</CardDescription>
                </CardHeader>
                <CardContent className="flex justify-center pb-6">
                  <ScoreCard
                    score={mockScore.overall}
                    grade={mockScore.grade}
                    trend={mockScore.trend}
                    percentile={mockScore.percentile}
                    components={mockScore.components}
                    size="lg"
                  />
                </CardContent>
              </Card>

              {/* Component Breakdown */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle>Component Breakdown</CardTitle>
                  <CardDescription>Detailed scoring by dimension</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid sm:grid-cols-2 gap-6">
                    {Object.entries(mockScore.components).map(([key, value]) => (
                      <div key={key} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium capitalize">
                            {key.replace(/_/g, ' ')}
                          </span>
                          <span className="text-sm font-bold">{value}%</span>
                        </div>
                        <Progress value={value} className="h-2" />
                        <p className="text-xs text-muted-foreground">
                          {getComponentDescription(key)}
                        </p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Stats & Trend */}
            <div className="grid lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <ScoreTrend data={mockTrendData} />
              </div>
              <Card>
                <CardHeader>
                  <CardTitle>Analysis Stats</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Total Queries</span>
                      <span className="font-medium">{mockScore.queryCount}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Pass Rate</span>
                      <span className="font-medium">{Math.round(mockScore.passRate * 100)}%</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Avg Latency</span>
                      <span className="font-medium">{(mockScore.avgLatencyMs / 1000).toFixed(2)}s</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Pages Analyzed</span>
                      <span className="font-medium">{mockSite.pageCount}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Last Analyzed</span>
                      <span className="font-medium">
                        {new Date(mockSite.lastCrawledAt).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  <Button className="w-full mt-6">
                    <Play className="w-4 h-4 mr-2" />
                    Run New Analysis
                  </Button>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="queries" className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Query Results</CardTitle>
                    <CardDescription>
                      Detailed breakdown of simulated agent queries
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-green-600" />
                      <span className="text-sm">{mockQueryResults.filter(q => q.passed).length} passed</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 text-red-600" />
                      <span className="text-sm">{mockQueryResults.filter(q => !q.passed).length} failed</span>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {mockQueryResults.map((query) => (
                    <div
                      key={query.id}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex-1">
                        <p className="font-medium">{query.query}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="secondary" className="text-xs">
                            {query.category}
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            {query.difficulty}
                          </Badge>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <div className="flex items-center gap-2">
                            {query.passed ? (
                              <CheckCircle2 className="w-5 h-5 text-green-600" />
                            ) : (
                              <AlertCircle className="w-5 h-5 text-red-600" />
                            )}
                            <span className={query.passed ? 'text-green-600' : 'text-red-600'}>
                              {query.passed ? 'Pass' : 'Fail'}
                            </span>
                          </div>
                          <p className="text-xs text-muted-foreground">
                            {Math.round(query.confidence * 100)}% confidence
                          </p>
                        </div>
                        <Button variant="ghost" size="sm">
                          View Details
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="recommendations" className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Recommendations</CardTitle>
                    <CardDescription>
                      Prioritized suggestions to improve your score
                    </CardDescription>
                  </div>
                  <Button variant="outline" size="sm">
                    <BarChart3 className="w-4 h-4 mr-2" />
                    Export All
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {mockRecommendations.map((rec, index) => (
                    <motion.div
                      key={rec.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="p-4 border rounded-lg hover:border-primary/50 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-sm font-medium text-muted-foreground">
                              #{index + 1}
                            </span>
                            <h3 className="font-medium">{rec.title}</h3>
                          </div>
                          <p className="text-sm text-muted-foreground mb-3">
                            {rec.description}
                          </p>
                          <div className="flex items-center gap-4">
                            <Badge className={getImpactColor(rec.impact)}>
                              {rec.impact} impact
                            </Badge>
                            <Badge className={getEffortColor(rec.effort)}>
                              {rec.effort} effort
                            </Badge>
                            <span className="text-sm text-muted-foreground">
                              <FileText className="w-4 h-4 inline mr-1" />
                              {rec.affectedPages} pages
                            </span>
                            <span className="text-sm text-green-600">
                              +{rec.estimatedImprovement} pts
                            </span>
                          </div>
                        </div>
                        <Button variant="outline" size="sm">
                          View Details
                        </Button>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="settings" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Site Settings</CardTitle>
                <CardDescription>
                  Configure analysis settings for this documentation site
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Site Name</label>
                  <input
                    type="text"
                    defaultValue={mockSite.name}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Documentation URL</label>
                  <input
                    type="url"
                    defaultValue={mockSite.url}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Analysis Schedule</label>
                  <select className="w-full px-3 py-2 border rounded-md">
                    <option>Weekly</option>
                    <option>Bi-weekly</option>
                    <option>Monthly</option>
                    <option>Manual only</option>
                  </select>
                </div>
                <div className="pt-4 border-t">
                  <Button variant="destructive">
                    <Trash2 className="w-4 h-4 mr-2" />
                    Delete Site
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}

function getComponentDescription(key: string): string {
  const descriptions: Record<string, string> = {
    accuracy: 'Correctness of answers generated from documentation',
    contextUtilization: 'Efficiency of information retrieval',
    latency: 'Response time for query processing',
    citationQuality: 'Accuracy and completeness of source attribution',
    codeExecutability: 'Validity and functionality of code examples',
  }
  return descriptions[key] || ''
}
