import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { DocumentationSite, User, FriendlinessScore, AnalysisProgress } from '@/types'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  token: string | null
  setUser: (user: User | null) => void
  setToken: (token: string | null) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      token: null,
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      setToken: (token) => set({ token }),
      logout: () => set({ user: null, isAuthenticated: false, token: null }),
    }),
    {
      name: 'auth-storage',
    }
  )
)

interface SitesState {
  sites: DocumentationSite[]
  selectedSite: DocumentationSite | null
  scores: Record<string, FriendlinessScore>
  isLoading: boolean
  error: string | null
  setSites: (sites: DocumentationSite[]) => void
  addSite: (site: DocumentationSite) => void
  updateSite: (id: string, updates: Partial<DocumentationSite>) => void
  removeSite: (id: string) => void
  setSelectedSite: (site: DocumentationSite | null) => void
  setScore: (siteId: string, score: FriendlinessScore) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useSitesStore = create<SitesState>((set) => ({
  sites: [],
  selectedSite: null,
  scores: {},
  isLoading: false,
  error: null,
  setSites: (sites) => set({ sites }),
  addSite: (site) => set((state) => ({ sites: [...state.sites, site] })),
  updateSite: (id, updates) =>
    set((state) => ({
      sites: state.sites.map((s) => (s.id === id ? { ...s, ...updates } : s)),
    })),
  removeSite: (id) =>
    set((state) => ({
      sites: state.sites.filter((s) => s.id !== id),
    })),
  setSelectedSite: (site) => set({ selectedSite: site }),
  setScore: (siteId, score) =>
    set((state) => ({
      scores: { ...state.scores, [siteId]: score },
    })),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
}))

interface AnalysisState {
  currentAnalysis: {
    id: string | null
    progress: AnalysisProgress | null
    isRunning: boolean
  }
  setCurrentAnalysis: (analysis: { id: string | null; progress: AnalysisProgress | null; isRunning: boolean }) => void
  updateProgress: (progress: AnalysisProgress) => void
  clearAnalysis: () => void
}

export const useAnalysisStore = create<AnalysisState>((set) => ({
  currentAnalysis: {
    id: null,
    progress: null,
    isRunning: false,
  },
  setCurrentAnalysis: (analysis) => set({ currentAnalysis: analysis }),
  updateProgress: (progress) =>
    set((state) => ({
      currentAnalysis: { ...state.currentAnalysis, progress },
    })),
  clearAnalysis: () =>
    set({
      currentAnalysis: {
        id: null,
        progress: null,
        isRunning: false,
      },
    }),
}))

interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  message: string
}

interface UIState {
  sidebarOpen: boolean
  theme: 'light' | 'dark' | 'system'
  notifications: Notification[]
  setSidebarOpen: (open: boolean) => void
  setTheme: (theme: 'light' | 'dark' | 'system') => void
  addNotification: (notification: Omit<Notification, 'id'>) => void
  removeNotification: (id: string) => void
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: false,
  theme: 'system',
  notifications: [],
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setTheme: (theme) => set({ theme }),
  addNotification: (notification) =>
    set((state) => ({
      notifications: [
        ...state.notifications,
        { ...notification, id: Math.random().toString(36).substr(2, 9) },
      ],
    })),
  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
}))

// Re-export assessment store
export { useAssessmentStore } from './assessment'
export type { AssessmentResult } from './assessment'
