"use client"

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react"
import { useUIPreferencesStore } from "@/stores/ui-preferences-store"

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

const ClientContext = createContext<ClientContextType | undefined>(undefined)

export function ClientProvider({ children }: { children: ReactNode }) {
  const [clients, setClients] = useState<Client[]>([])
  const [selectedClient, setSelectedClientState] = useState<Client | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [mounted, setMounted] = useState(false)
  const { adminSelectedClient, setAdminSelectedClient } = useUIPreferencesStore()

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
    setAdminSelectedClient(client as (Client & { id: string; name: string; status: string }) | null)
  }, [setAdminSelectedClient])

  const clearSelectedClient = useCallback(() => {
    setSelectedClientState(null)
    setAdminSelectedClient(null)
  }, [setAdminSelectedClient])

  useEffect(() => {
    setMounted(true)
    
    const initContext = async () => {
      const clientsList = await fetchClients()
      
      if (adminSelectedClient) {
        const stillExists = clientsList.find((c: Client) => c.id === adminSelectedClient.id)
        if (stillExists) {
          setSelectedClientState(stillExists)
        } else {
          setAdminSelectedClient(null)
        }
      }
    }

    initContext()
  }, [fetchClients, adminSelectedClient, setAdminSelectedClient])

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
