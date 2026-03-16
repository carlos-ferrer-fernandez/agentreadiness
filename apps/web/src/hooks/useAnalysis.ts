import { useState, useCallback, useEffect, useRef } from 'react'
import { analysesApi } from '@/lib/api'
import { useAnalysisStore, useUIStore } from '@/store'
import type { FriendlinessScore, AnalysisProgress } from '@/types'

export function useAnalysis(analysisId: string | null) {
  const [score, setScore] = useState<FriendlinessScore | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { addNotification } = useUIStore()
  const { updateProgress, setCurrentAnalysis } = useAnalysisStore()
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null)

  const fetchScore = useCallback(async () => {
    if (!analysisId) return
    
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await analysesApi.getScore(analysisId)
      setScore(response.data)
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to fetch score'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }, [analysisId])

  const pollProgress = useCallback(async () => {
    if (!analysisId) return
    
    try {
      const response = await analysesApi.getProgress(analysisId)
      const progress: AnalysisProgress = response.data
      
      updateProgress(progress)
      
      if (progress.status === 'COMPLETED') {
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current)
        }
        fetchScore()
        addNotification({ type: 'success', message: 'Analysis completed!' })
      } else if (progress.status === 'FAILED' || progress.status === 'CANCELLED') {
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current)
        }
        addNotification({ 
          type: 'error', 
          message: `Analysis ${progress.status.toLowerCase()}` 
        })
      }
    } catch (err: any) {
      console.error('Failed to fetch progress:', err)
    }
  }, [analysisId, updateProgress, fetchScore, addNotification])

  const startAnalysis = useCallback(async (siteId: string) => {
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await sitesApi.analyze(siteId)
      const newAnalysisId = response.data.analysis_id
      
      setCurrentAnalysis({
        id: newAnalysisId,
        progress: null,
        isRunning: true,
      })
      
      // Start polling
      pollIntervalRef.current = setInterval(pollProgress, 2000)
      
      addNotification({ type: 'info', message: 'Analysis started' })
      return newAnalysisId
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to start analysis'
      setError(message)
      addNotification({ type: 'error', message })
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [setCurrentAnalysis, pollProgress, addNotification])

  const cancelAnalysis = useCallback(async () => {
    if (!analysisId) return
    
    try {
      await analysesApi.cancel(analysisId)
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
      }
      addNotification({ type: 'info', message: 'Analysis cancelled' })
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to cancel analysis'
      addNotification({ type: 'error', message })
    }
  }, [analysisId, addNotification])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
      }
    }
  }, [])

  return {
    score,
    isLoading,
    error,
    fetchScore,
    startAnalysis,
    cancelAnalysis,
  }
}

// Import sitesApi for startAnalysis
import { sitesApi } from '@/lib/api'
