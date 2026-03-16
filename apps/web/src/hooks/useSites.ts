import { useState, useEffect, useCallback } from 'react'
import { sitesApi } from '@/lib/api'
import { useSitesStore, useUIStore } from '@/store'
import type { DocumentationSite } from '@/types'

export function useSites() {
  const { sites, setSites, isLoading, setLoading, error, setError } = useSitesStore()
  const { addNotification } = useUIStore()

  const fetchSites = useCallback(async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await sitesApi.list()
      setSites(response.data)
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to fetch sites'
      setError(message)
      addNotification({ type: 'error', message })
    } finally {
      setLoading(false)
    }
  }, [setSites, setLoading, setError, addNotification])

  useEffect(() => {
    fetchSites()
  }, [fetchSites])

  return { sites, isLoading, error, refetch: fetchSites }
}

export function useCreateSite() {
  const { addSite, setLoading } = useSitesStore()
  const { addNotification } = useUIStore()

  const createSite = async (data: { url: string; name: string }) => {
    setLoading(true)
    
    try {
      const response = await sitesApi.create(data)
      addSite(response.data)
      addNotification({ type: 'success', message: 'Site added successfully' })
      return response.data
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to add site'
      addNotification({ type: 'error', message })
      throw err
    } finally {
      setLoading(false)
    }
  }

  return { createSite }
}

export function useDeleteSite() {
  const { removeSite, setLoading } = useSitesStore()
  const { addNotification } = useUIStore()

  const deleteSite = async (id: string) => {
    setLoading(true)
    
    try {
      await sitesApi.delete(id)
      removeSite(id)
      addNotification({ type: 'success', message: 'Site deleted successfully' })
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to delete site'
      addNotification({ type: 'error', message })
      throw err
    } finally {
      setLoading(false)
    }
  }

  return { deleteSite }
}
