import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface AssessmentResult {
  id: string
  url: string
  siteName: string
  score: number
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
  pageCount: number
  topIssues: Array<{
    category: string
    title: string
    severity: 'high' | 'medium' | 'low'
  }>
  estimatedPriceEur: number
  hasPaid: boolean
  optimizationStatus: string | null  // queued, running, complete, failed
  optimizationProgress: number
  optimizationStage: string | null
  optimizationMetadata: Record<string, any> | null
  createdAt: string
}

interface AssessmentState {
  // Current assessment
  currentAssessment: AssessmentResult | null
  isAssessing: boolean
  assessmentStage: number
  assessmentError: string | null

  // Payment state (single tier — no plan selection needed)
  showPaywall: boolean

  // Actions
  startAssessment: () => void
  setAssessmentStage: (stage: number) => void
  setAssessmentResult: (result: AssessmentResult) => void
  setAssessmentError: (error: string | null) => void
  clearAssessment: () => void

  // Payment actions
  showPaywallModal: () => void
  hidePaywallModal: () => void
  markAsPaid: () => void

  // Optimization actions
  setOptimizationStatus: (status: string, progress?: number, stage?: string) => void
  setOptimizationComplete: (metadata: Record<string, any>) => void
}

export const useAssessmentStore = create<AssessmentState>()(
  persist(
    (set, get) => ({
      currentAssessment: null,
      isAssessing: false,
      assessmentStage: 0,
      assessmentError: null,
      showPaywall: false,

      startAssessment: () => set({
        isAssessing: true,
        assessmentStage: 0,
        assessmentError: null,
        currentAssessment: null,
        showPaywall: false,
      }),

      setAssessmentStage: (stage) => set({ assessmentStage: stage }),

      setAssessmentResult: (result) => set({
        currentAssessment: result,
        isAssessing: false,
        showPaywall: true,
      }),

      setAssessmentError: (error) => set({
        assessmentError: error,
        isAssessing: false,
      }),

      clearAssessment: () => set({
        currentAssessment: null,
        isAssessing: false,
        assessmentStage: 0,
        assessmentError: null,
        showPaywall: false,
      }),

      showPaywallModal: () => set({ showPaywall: true }),
      hidePaywallModal: () => set({ showPaywall: false }),

      markAsPaid: () => {
        const current = get().currentAssessment
        if (current) {
          set({
            currentAssessment: {
              ...current,
              hasPaid: true,
              optimizationStatus: 'queued',
            },
            showPaywall: false,
          })
        }
      },

      setOptimizationStatus: (status, progress = 0, stage = null) => {
        const current = get().currentAssessment
        if (current) {
          set({
            currentAssessment: {
              ...current,
              optimizationStatus: status,
              optimizationProgress: progress,
              optimizationStage: stage,
            },
          })
        }
      },

      setOptimizationComplete: (metadata) => {
        const current = get().currentAssessment
        if (current) {
          set({
            currentAssessment: {
              ...current,
              optimizationStatus: 'complete',
              optimizationProgress: 1,
              optimizationStage: 'complete',
              optimizationMetadata: metadata,
            },
          })
        }
      },
    }),
    {
      name: 'assessment-storage',
      partialize: (state) => ({
        currentAssessment: state.currentAssessment,
      }),
    }
  )
)
