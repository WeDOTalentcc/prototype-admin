"use client"

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react"

export interface Client {
  id: string
  name: string
  tradeName?: string
  cnpj?: string
  status: string
  planId?: string
  logoUrl?: string
}

interface ClientContextType {
  selectedClient: Client | null
  setSelectedClient: (client: Client | null) => void
  clearSelectedClient: () => void
  clients: Client[]
  isLoading: boolean
  refreshClients: () => Promise<void>
}

const STORAGE_KEY = "wedo_admin_selected_client"

const ClientContext = createContext<ClientContextType | undefined>(undefined)

export function ClientProvider({ children }: { children: ReactNode }) {
  const [clients, setClients] = useState<Client[]>([])
  const [selectedClient, setSelectedClientState] = useState<Client | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [mounted, setMounted] = useState(false)

  const fetchClients = useCallback(async () => {
    try {
      setIsLoading(true)
      const response = await fetch("/api/backend-proxy/clients?limit=100")
      
      if (!response.ok) {
        throw new Error("Failed to fetch clients")
      }
      
      const data = await response.json()
      const clientsList = Array.isArray(data) ? data : (data.items || data.clients || [])
      setClients(clientsList)
      return clientsList
    } catch (error) {
      setClients([])
      return []
    } finally {
      setIsLoading(false)
    }
  }, [])

  const setSelectedClient = useCallback((client: Client | null) => {
    setSelectedClientState(client)
    if (typeof window !== "undefined") {
      if (client) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(client))
      } else {
        localStorage.removeItem(STORAGE_KEY)
      }
    }
  }, [])

  const clearSelectedClient = useCallback(() => {
    setSelectedClientState(null)
    if (typeof window !== "undefined") {
      localStorage.removeItem(STORAGE_KEY)
    }
  }, [])

  useEffect(() => {
    setMounted(true)
    
    const initContext = async () => {
      const clientsList = await fetchClients()
      
      if (typeof window !== "undefined") {
        const stored = localStorage.getItem(STORAGE_KEY)
        if (stored) {
          try {
            const storedClient = JSON.parse(stored) as Client
            const stillExists = clientsList.find((c: Client) => c.id === storedClient.id)
            if (stillExists) {
              setSelectedClientState(stillExists)
            } else {
              localStorage.removeItem(STORAGE_KEY)
            }
          } catch (e) {
            localStorage.removeItem(STORAGE_KEY)
          }
        }
      }
    }

    initContext()
  }, [fetchClients])

  const value: ClientContextType = {
    selectedClient,
    setSelectedClient,
    clearSelectedClient,
    clients,
    isLoading,
    refreshClients: fetchClients,
  }

  return (
    <ClientContext.Provider value={value}>
      {children}
    </ClientContext.Provider>
  )
}

export function useClient() {
  const context = useContext(ClientContext)
  if (context === undefined) {
    throw new Error("useClient must be used within a ClientProvider")
  }
  return context
}
