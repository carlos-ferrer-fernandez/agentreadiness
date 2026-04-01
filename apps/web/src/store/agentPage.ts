import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AgentPageState {
  currentSlug: string | null
  status: string | null // submitted, crawling, generating, draft_ready, full_ready, failed
  paymentStatus: string | null
  hasDraft: boolean
  hasFull: boolean
  isGenerating: boolean
  error: string | null

  setSlug: (slug: string) => void
  setStatus: (status: string, paymentStatus: string, hasDraft: boolean, hasFull: boolean) => void
  setGenerating: (generating: boolean) => void
  setError: (error: string | null) => void
  clear: () => void
}

export const useAgentPageStore = create<AgentPageState>()(
  persist(
    (set) => ({
      currentSlug: null,
      status: null,
      paymentStatus: null,
      hasDraft: false,
      hasFull: false,
      isGenerating: false,
      error: null,

      setSlug: (slug) => set({ currentSlug: slug }),

      setStatus: (status, paymentStatus, hasDraft, hasFull) => set({
        status,
        paymentStatus,
        hasDraft,
        hasFull,
      }),

      setGenerating: (generating) => set({ isGenerating: generating }),

      setError: (error) => set({ error }),

      clear: () => set({
        currentSlug: null,
        status: null,
        paymentStatus: null,
        hasDraft: false,
        hasFull: false,
        isGenerating: false,
        error: null,
      }),
    }),
    {
      name: 'agent-page-storage',
      partialize: (state) => ({
        currentSlug: state.currentSlug,
        status: state.status,
        paymentStatus: state.paymentStatus,
        hasDraft: state.hasDraft,
        hasFull: state.hasFull,
      }),
    }
  )
)
