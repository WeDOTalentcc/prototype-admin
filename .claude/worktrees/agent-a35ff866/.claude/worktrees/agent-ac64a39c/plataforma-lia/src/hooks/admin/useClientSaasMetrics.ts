"use client"

import { useState, useEffect, useCallback } from "react"
import {
  saasMetricsClientService,
  ClientSaasMetrics,
  ClientRevenueMetrics,
  ClientUsageMetrics,
  ClientHealthMetrics,
  ClientPayment,
  ApiClientError,
} from "@/services/admin/saas-metrics-service"

export interface UseClientSaasMetricsResult {
  metrics: ClientSaasMetrics | null
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
}

export interface UseClientRevenueResult {
  revenue: ClientRevenueMetrics | null
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
}

export interface UseClientUsageResult {
  usage: ClientUsageMetrics | null
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
}

export interface UseClientHealthResult {
  health: ClientHealthMetrics | null
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
}

export interface UseClientPaymentsResult {
  payments: ClientPayment[]
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
}

export function useClientSaasMetrics(clientId: string): UseClientSaasMetricsResult {
  const [metrics, setMetrics] = useState<ClientSaasMetrics | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchMetrics = useCallback(async () => {
    if (!clientId) {
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const data = await saasMetricsClientService.getClientMetrics(clientId)
      setMetrics(data)
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else {
        setError("Erro ao carregar métricas do cliente")
      }
    } finally {
      setIsLoading(false)
    }
  }, [clientId])

  useEffect(() => {
    fetchMetrics()
  }, [fetchMetrics])

  return {
    metrics,
    isLoading,
    error,
    refetch: fetchMetrics,
  }
}

export function useClientRevenue(clientId: string): UseClientRevenueResult {
  const [revenue, setRevenue] = useState<ClientRevenueMetrics | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchRevenue = useCallback(async () => {
    if (!clientId) {
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const data = await saasMetricsClientService.getClientRevenue(clientId)
      setRevenue(data)
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else {
        setError("Erro ao carregar receita do cliente")
      }
    } finally {
      setIsLoading(false)
    }
  }, [clientId])

  useEffect(() => {
    fetchRevenue()
  }, [fetchRevenue])

  return {
    revenue,
    isLoading,
    error,
    refetch: fetchRevenue,
  }
}

export function useClientUsage(clientId: string): UseClientUsageResult {
  const [usage, setUsage] = useState<ClientUsageMetrics | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchUsage = useCallback(async () => {
    if (!clientId) {
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const data = await saasMetricsClientService.getClientUsage(clientId)
      setUsage(data)
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else {
        setError("Erro ao carregar uso do cliente")
      }
    } finally {
      setIsLoading(false)
    }
  }, [clientId])

  useEffect(() => {
    fetchUsage()
  }, [fetchUsage])

  return {
    usage,
    isLoading,
    error,
    refetch: fetchUsage,
  }
}

export function useClientHealth(clientId: string): UseClientHealthResult {
  const [health, setHealth] = useState<ClientHealthMetrics | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchHealth = useCallback(async () => {
    if (!clientId) {
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const data = await saasMetricsClientService.getClientHealth(clientId)
      setHealth(data)
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else {
        setError("Erro ao carregar saúde do cliente")
      }
    } finally {
      setIsLoading(false)
    }
  }, [clientId])

  useEffect(() => {
    fetchHealth()
  }, [fetchHealth])

  return {
    health,
    isLoading,
    error,
    refetch: fetchHealth,
  }
}

export function useClientPayments(clientId: string): UseClientPaymentsResult {
  const [payments, setPayments] = useState<ClientPayment[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchPayments = useCallback(async () => {
    if (!clientId) {
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const data = await saasMetricsClientService.getClientPayments(clientId)
      setPayments(data)
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else {
        setError("Erro ao carregar pagamentos do cliente")
      }
    } finally {
      setIsLoading(false)
    }
  }, [clientId])

  useEffect(() => {
    fetchPayments()
  }, [fetchPayments])

  return {
    payments,
    isLoading,
    error,
    refetch: fetchPayments,
  }
}
