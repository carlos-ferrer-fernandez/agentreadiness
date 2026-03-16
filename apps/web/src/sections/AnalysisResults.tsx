import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  ArrowLeft, 
  Download, 
  Share2,
  Clock,
  CheckCircle2,
  AlertCircle,
  Loader2
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { ScoreCard } from '@/components/score/ScoreCard'

const mockAnalysis = {
  id: '1',
  siteId: '1',
  siteName: 'Resend Documentation',
  status: 'COMPLETED',
  progress: 100,
  startedAt: '2025-03-01T10:00:00Z',
  completedAt: '2025-03-01T10:05:23Z',
  score: {
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
  },
  stages: [
    { name: 'Crawling', status: 'completed', duration: '45s' },
    { name: 'Content Analysis', status: 'completed', duration: '1m 12s' },
    { name: 'Query Generation', status: 'completed', duration: '58s' },
    { name: 'RAG Simulation', status: 'completed', duration: '2m 30s' },
    { name: 'Scoring', status: 'completed', duration: '18s' },
  ],
}

export function AnalysisResults() {
  const { analysisId } = useParams()
  const [isExporting, setIsExporting] = useState(false)

  const handleExport = async () => {
    setIsExporting(true)
    // Simulate export
    await new Promise(resolve => setTimeout(resolve, 1500))
    setIsExporting(false)
  }

  const getStageIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-5 h-5 text-green-600" />
      case 'in_progress':
        return <Loader2 className="w-5 h-5 text-primary animate-spin" />
      case 'pending':
        return <Clock className="w-5 h-5 text-muted-foreground" />
      default:
        return <AlertCircle className="w-5 h-5 text-red-600" />
    }
  }

  const duration = mockAnalysis.completedAt && mockAnalysis.startedAt
    ? Math.round((new Date(mockAnalysis.completedAt).getTime() - new Date(mockAnalysis.startedAt).getTime()) / 1000)
    : 0

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
                  Back
                </Button>
              </Link>
            </div>
            <div className="flex items-center gap-2">
              <Button 
                variant="outline" 
                size="sm"
                onClick={handleExport}
                disabled={isExporting}
              >
                {isExporting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Exporting...
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4 mr-2" />
                    Export PDF
                  </>
                )}
              </Button>
              <Button variant="outline" size="sm">
                <Share2 className="w-4 h-4 mr-2" />
                Share
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Analysis Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-3xl font-bold">Analysis Results</h1>
            <Badge variant="success">{mockAnalysis.status}</Badge>
          </div>
          <p className="text-muted-foreground">
            {mockAnalysis.siteName} • Analysis #{analysisId}
          </p>
        </div>

        {/* Progress Overview */}
        <div className="grid lg:grid-cols-3 gap-6 mb-8">
          {/* Score Card */}
          <Card>
            <CardHeader>
              <CardTitle>Friendliness Score</CardTitle>
              <CardDescription>Overall agent-readiness rating</CardDescription>
            </CardHeader>
            <CardContent className="flex justify-center pb-6">
              <ScoreCard
                score={mockAnalysis.score.overall}
                grade={mockAnalysis.score.grade}
                components={mockAnalysis.score.components}
                size="lg"
              />
            </CardContent>
          </Card>

          {/* Analysis Progress */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Analysis Progress</CardTitle>
              <CardDescription>
                Completed in {Math.floor(duration / 60)}m {duration % 60}s
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {mockAnalysis.stages.map((stage, index) => (
                  <motion.div
                    key={stage.name}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-center justify-between p-3 bg-muted/50 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      {getStageIcon(stage.status)}
                      <span className="font-medium">{stage.name}</span>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-sm text-muted-foreground">{stage.duration}</span>
                      {stage.status === 'completed' && (
                        <CheckCircle2 className="w-4 h-4 text-green-600" />
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>
              <div className="mt-4">
                <Progress value={100} className="h-2" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Component Breakdown */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Component Breakdown</CardTitle>
            <CardDescription>Detailed scoring by dimension</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {Object.entries(mockAnalysis.score.components).map(([key, value]) => (
                <div key={key} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium capitalize">
                      {key.replace(/_/g, ' ')}
                    </span>
                    <span className="text-sm font-bold">{value}%</span>
                  </div>
                  <Progress value={value} className="h-2" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Stats */}
        <div className="grid md:grid-cols-4 gap-6">
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <p className="text-sm text-muted-foreground mb-1">Total Queries</p>
                <p className="text-3xl font-bold">{mockAnalysis.score.queryCount}</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <p className="text-sm text-muted-foreground mb-1">Pass Rate</p>
                <p className="text-3xl font-bold">{Math.round(mockAnalysis.score.passRate * 100)}%</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <p className="text-sm text-muted-foreground mb-1">Avg Latency</p>
                <p className="text-3xl font-bold">{(mockAnalysis.score.avgLatencyMs / 1000).toFixed(2)}s</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <p className="text-sm text-muted-foreground mb-1">Analysis Time</p>
                <p className="text-3xl font-bold">{Math.floor(duration / 60)}m {duration % 60}s</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
}
