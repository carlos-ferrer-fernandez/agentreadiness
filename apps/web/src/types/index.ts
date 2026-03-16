export interface Organization {
  id: string
  name: string
  githubId?: string
  createdAt: string
  updatedAt: string
}

export interface User {
  id: string
  email: string
  name?: string
  githubId?: string
  organizationId: string
  organization: Organization
}

export interface DocumentationSite {
  id: string
  url: string
  name: string
  status: 'PENDING' | 'VERIFIED' | 'CRAWLING' | 'READY' | 'ERROR'
  organizationId: string
  pageCount?: number
  lastCrawledAt?: string
  createdAt: string
  updatedAt: string
}

export interface TestRun {
  id: string
  siteId: string
  status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED'
  progress: number
  startedAt?: string
  completedAt?: string
  errorMessage?: string
  createdAt: string
}

export interface FriendlinessScore {
  overall: number
  grade: string
  components: {
    accuracy: number
    contextUtilization: number
    latency: number
    citationQuality: number
    codeExecutability: number
  }
  queryCount: number
  passRate: number
  avgLatencyMs: number
  percentile?: number
  trend?: number
}

export interface QueryResult {
  id: string
  queryText: string
  category: 'how_to' | 'conceptual' | 'troubleshooting' | 'reference'
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  passed: boolean
  confidence: number
  generatedResponse: string
  expectedAnswer?: string
  retrievedChunks: RetrievedChunk[]
}

export interface RetrievedChunk {
  content: string
  sourceUrl: string
  sourceTitle: string
  similarityScore: number
}

export interface Recommendation {
  id: string
  siteId: string
  priority: number
  impact: 'high' | 'medium' | 'low'
  effort: 'high' | 'medium' | 'low'
  category: 'content_gap' | 'structure' | 'clarity' | 'freshness' | 'code_quality'
  title: string
  description: string
  affectedPages: { id: string; url: string; title: string }[]
  beforeExample?: string
  afterExample?: string
  estimatedScoreImprovement?: number
  implementationStatus: 'pending' | 'in_progress' | 'implemented' | 'dismissed'
}

export interface AnalysisProgress {
  status: string
  progress: number
  currentStage?: string
  estimatedCompletion?: string
  pageCount?: number
  processedPages?: number
}
