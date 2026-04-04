import axios, { AxiosInstance, AxiosError } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 2 minutes - assessments can take a while
})

// Request interceptor: attach JWT if available
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor: handle 401
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      // Only redirect if we're on a protected page (not landing/assessment)
      const path = window.location.pathname
      if (path.startsWith('/dashboard') || path.startsWith('/sites')) {
        window.location.href = '/'
      }
    }
    return Promise.reject(error)
  }
)

// --- Public Assessments API (no auth required) ---
export const assessmentsApi = {
  analyze: (data: { url: string; email: string; full_name?: string; role?: string }, signal?: AbortSignal) =>
    apiClient.post<AssessmentResult>('/api/assessments/analyze', data, { signal }),
  get: (id: string) =>
    apiClient.get<AssessmentResult>(`/api/assessments/${id}`),
  verifyPromo: (assessmentId: string, code: string) =>
    apiClient.post(`/api/assessments/${assessmentId}/verify-promo`, {
      assessment_id: assessmentId,
      code,
    }),
  getOptimizationStatus: (assessmentId: string) =>
    apiClient.get(`/api/assessments/${assessmentId}/optimization-status`),
  retryOptimization: (assessmentId: string) =>
    apiClient.post(`/api/assessments/${assessmentId}/retry-optimization`),
  getDownloadUrl: (assessmentId: string) =>
    `${API_BASE_URL}/api/assessments/${assessmentId}/download`,
}

// --- Sites API ---
export const sitesApi = {
  list: () => apiClient.get('/api/sites'),
  get: (id: string) => apiClient.get(`/api/sites/${id}`),
  create: (data: { url: string; name: string }) => apiClient.post('/api/sites', data),
  update: (id: string, data: Partial<{ name: string }>) => apiClient.patch(`/api/sites/${id}`, data),
  delete: (id: string) => apiClient.delete(`/api/sites/${id}`),
  verify: (id: string, data: { method: string; token: string }) =>
    apiClient.post(`/api/sites/${id}/verify`, data),
  getVerificationToken: (id: string) => apiClient.get(`/api/sites/${id}/verification-token`),
  analyze: (id: string) => apiClient.post(`/api/sites/${id}/analyze`),
}

// --- Analyses API ---
export const analysesApi = {
  list: (params?: { site_id?: string; status?: string; limit?: number }) =>
    apiClient.get('/api/analyses', { params }),
  get: (id: string) => apiClient.get(`/api/analyses/${id}`),
  getProgress: (id: string) => apiClient.get(`/api/analyses/${id}/progress`),
  getScore: (id: string) => apiClient.get(`/api/analyses/${id}/score`),
  cancel: (id: string) => apiClient.post(`/api/analyses/${id}/cancel`),
  compare: (id: string, compareTo?: string) =>
    apiClient.get(`/api/analyses/${id}/compare`, { params: { compare_to: compareTo } }),
}

// --- Queries API ---
export const queriesApi = {
  list: (analysisId: string, params?: { category?: string; difficulty?: string; status?: string }) =>
    apiClient.get(`/api/queries/analysis/${analysisId}`, { params }),
  get: (id: string) => apiClient.get(`/api/queries/${id}`),
  export: (analysisId: string, params?: { category?: string; status?: string }) =>
    apiClient.post(`/api/queries/analysis/${analysisId}/export`, null, { params }),
}

// --- Recommendations API ---
export const recommendationsApi = {
  list: (siteId: string, params?: { category?: string; impact?: string; status?: string }) =>
    apiClient.get(`/api/recommendations/site/${siteId}`, { params }),
  get: (id: string) => apiClient.get(`/api/recommendations/${id}`),
  update: (id: string, data: { implementation_status: string }) =>
    apiClient.patch(`/api/recommendations/${id}`, data),
  createTicket: (id: string, integration: string = 'github') =>
    apiClient.post(`/api/recommendations/${id}/create-ticket`, null, { params: { integration } }),
}

// --- Auth API ---
export const authApi = {
  github: (code: string) => apiClient.post('/api/auth/github', { code }),
  me: () => apiClient.get('/api/auth/me'),
  logout: () => apiClient.post('/api/auth/logout'),
}

// --- Payments API ---
export const paymentsApi = {
  getConfig: () => apiClient.get('/api/payments/config'),
  createCheckout: (data: {
    assessment_id: string
    success_url: string
    cancel_url: string
  }) => apiClient.post('/api/payments/create-checkout', data),
  verify: (sessionId: string) =>
    apiClient.get('/api/payments/verify', { params: { session_id: sessionId } }),
}

// --- Contact ---
export const contactApi = {
  send: (data: { name: string; email: string; subject: string; message: string }) =>
    apiClient.post('/api/contact', data),
}

// --- Agent Pages API ---
export const agentPagesApi = {
  generate: (data: { product_name: string; docs_url: string; email: string }) =>
    apiClient.post('/api/agent-pages/generate', data),
  getFeatured: () =>
    apiClient.get('/api/agent-pages/featured/list'),
  getBySlug: (slug: string) =>
    apiClient.get(`/api/agent-pages/${slug}`),
  getStatus: (slug: string) =>
    apiClient.get(`/api/agent-pages/${slug}/status`),
  getViewHtml: (slug: string) =>
    apiClient.get(`/api/agent-pages/${slug}/view`, { responseType: 'text' }),
  getViewUrl: (slug: string) => {
    const base = apiClient.defaults.baseURL || ''
    return `${base}/api/agent-pages/${slug}/view`
  },
  unlock: (slug: string, data: { success_url: string; cancel_url: string }) =>
    apiClient.post(`/api/agent-pages/${slug}/unlock`, data),
  verifyPayment: (slug: string, sessionId: string) =>
    apiClient.post(`/api/agent-pages/${slug}/verify-payment`, { session_id: sessionId }),
  applyPromo: (slug: string, code: string) =>
    apiClient.post(`/api/agent-pages/${slug}/apply-promo`, { code }),
}

// --- Packages API ---
export const packagesApi = {
  generate: (data: { product_name: string; docs_url: string; email: string }) =>
    apiClient.post('/api/packages/generate', data),
  getExamples: () =>
    apiClient.get('/api/packages/examples'),
  getBySlug: (slug: string) =>
    apiClient.get(`/api/packages/${slug}`),
  getStatus: (slug: string) =>
    apiClient.get(`/api/packages/${slug}/status`),
  getPageHtml: (slug: string, pageSlug: string) =>
    apiClient.get(`/api/packages/${slug}/${pageSlug}`, { responseType: 'text' }),
  getPageUrl: (slug: string, pageSlug: string) => {
    const base = apiClient.defaults.baseURL || ''
    return `${base}/api/packages/${slug}/${pageSlug}`
  },
  unlock: (slug: string, data: { success_url: string; cancel_url: string }) =>
    apiClient.post(`/api/packages/${slug}/unlock`, data),
  verifyPayment: (slug: string, sessionId: string) =>
    apiClient.post(`/api/packages/${slug}/verify-payment`, { session_id: sessionId }),
  applyPromo: (slug: string, code: string) =>
    apiClient.post(`/api/packages/${slug}/apply-promo`, { code }),
  getDownloadUrl: (slug: string) => {
    const base = apiClient.defaults.baseURL || ''
    return `${base}/api/packages/${slug}/download`
  },
}

// --- Health ---
export const healthApi = {
  check: () => apiClient.get('/api/health'),
}

// --- Types ---
export interface RuleResult {
  rule_id: number
  name: string
  short_name: string
  category: string
  score: number
  status: 'pass' | 'warning' | 'fail'
  finding: string
  pages_checked: number
  pages_passing: number
}

export interface AssessmentResult {
  id: string
  url: string
  site_name: string
  score: number
  grade: string
  components: Record<string, number>
  rule_results: RuleResult[]
  query_count: number
  pass_rate: number
  avg_latency_ms: number
  page_count: number
  top_issues: Array<{ category: string; title: string; severity: string; rule_id?: number; score?: number }>
  estimated_price_eur: number
  has_paid: boolean
  optimization_status: string | null
  optimization_progress: number
  optimization_stage: string | null
  optimization_metadata: Record<string, any> | null
  created_at: string
}

export default apiClient
