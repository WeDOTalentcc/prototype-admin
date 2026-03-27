"use client"

import { useState, useEffect, useCallback } from 'react'
import { 
  clientsService, 
  Client, 
  ClientsListParams,
  CreateClientData,
  UpdateClientData
} from '@/services/admin/clients'

export type { Client, ClientsListParams, CreateClientData, UpdateClientData }

interface UseClientsOptions {
  autoFetch?: boolean
  initialPage?: number
  initialLimit?: number
  initialSearch?: string
  initialStatus?: string
}

interface UseClientsResult {
  clients: Client[]
  total: number
  page: number
  limit: number
  totalPages: number
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
  setPage: (page: number) => void
  setLimit: (limit: number) => void
  setSearch: (search: string) => void
  setStatus: (status: string) => void
  createClient: (data: CreateClientData) => Promise<Client>
  updateClient: (id: string, data: UpdateClientData) => Promise<Client>
  deleteClient: (id: string) => Promise<void>
  getClient: (id: string) => Promise<Client | null>
}

export function useClients(options: UseClientsOptions = {}): UseClientsResult {
  const { 
    autoFetch = true, 
    initialPage = 1, 
    initialLimit = 20, 
    initialSearch = '',
    initialStatus = ''
  } = options

  const [clients, setClients] = useState<Client[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPageState] = useState(initialPage)
  const [limit, setLimitState] = useState(initialLimit)
  const [totalPages, setTotalPages] = useState(0)
  const [search, setSearchState] = useState(initialSearch)
  const [status, setStatusState] = useState(initialStatus)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchClients = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const params: ClientsListParams = {
        page,
        limit,
      }
      
      if (search) params.search = search
      if (status) params.status = status

      const result = await clientsService.getClients(params)
      
      setClients(result.items)
      setTotal(result.total)
      setTotalPages(result.totalPages)
    } catch (err) {
      console.error('Error fetching clients:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch clients')
      setClients([])
      setTotal(0)
      setTotalPages(0)
    } finally {
      setIsLoading(false)
    }
  }, [page, limit, search, status])

  useEffect(() => {
    if (autoFetch) {
      fetchClients()
    }
  }, [autoFetch, fetchClients])

  const setPage = useCallback((newPage: number) => {
    setPageState(newPage)
  }, [])

  const setLimit = useCallback((newLimit: number) => {
    setLimitState(newLimit)
    setPageState(1)
  }, [])

  const setSearch = useCallback((newSearch: string) => {
    setSearchState(newSearch)
    setPageState(1)
  }, [])

  const setStatus = useCallback((newStatus: string) => {
    setStatusState(newStatus)
    setPageState(1)
  }, [])

  const createClient = useCallback(async (data: CreateClientData): Promise<Client> => {
    setError(null)
    
    try {
      const newClient = await clientsService.createClient(data)
      await fetchClients()
      return newClient
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create client'
      setError(errorMessage)
      throw new Error(errorMessage)
    }
  }, [fetchClients])

  const updateClient = useCallback(async (id: string, data: UpdateClientData): Promise<Client> => {
    setError(null)
    
    try {
      const updatedClient = await clientsService.updateClient(id, data)
      setClients(prev => prev.map(c => c.id === id ? updatedClient : c))
      return updatedClient
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update client'
      setError(errorMessage)
      throw new Error(errorMessage)
    }
  }, [])

  const deleteClient = useCallback(async (id: string): Promise<void> => {
    setError(null)
    
    try {
      await clientsService.deleteClient(id)
      setClients(prev => prev.filter(c => c.id !== id))
      setTotal(prev => prev - 1)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete client'
      setError(errorMessage)
      throw new Error(errorMessage)
    }
  }, [])

  const getClient = useCallback(async (id: string): Promise<Client | null> => {
    try {
      return await clientsService.getClient(id)
    } catch (err) {
      console.error('Error fetching client:', err)
      return null
    }
  }, [])

  return {
    clients,
    total,
    page,
    limit,
    totalPages,
    isLoading,
    error,
    refetch: fetchClients,
    setPage,
    setLimit,
    setSearch,
    setStatus,
    createClient,
    updateClient,
    deleteClient,
    getClient
  }
}

export default useClients
