"use client"

import { useState, useEffect, useCallback, useRef } from "react"
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
  const isMountedRef = useRef(true)

  const fetchMetrics = useCallback(async () => {
    if (!clientId) {
      if (isMountedRef.current) setIsLoading(false)
      return
    }

    if (isMountedRef.current) setIsLoading(true)
    if (isMountedRef.current) setError(null)

    try {
      const data = await saasMetricsClientService.getClientMetrics(clientId)
      if (isMountedRef.current) setMetrics(data)
    } catch (err) {
      if (!isMountedRef.current) return
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else {
        setError("Erro ao carregar métricas do cliente")
      }
    } finally {
      if (isMountedRef.current) setIsLoading(false)
    }
  }, [clientId])

  useEffect(() => {
    isMountedRef.current = true
    fetchMetrics()
    return () => { isMountedRef.current = false }
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
  const isMountedRef = useRef(true)

  const fetchRevenue = useCallback(async () => {
    if (!clientId) {
      if (isMountedRef.current) setIsLoading(false)
      return
    }

    if (isMountedRef.current) setIsLoading(true)
    if (isMountedRef.current) setError(null)

    try {
      const data = await saasMetricsClientService.getClientRevenue(clientId)
      if (isMountedRef.current) setRevenue(data)
    } catch (err) {
      if (!isMountedRef.current) return
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else {
        setError("Erro ao carregar receita do cliente")
      }
    } finally {
      if (isMountedRef.current) setIsLoading(false)
    }
  }, [clientId])

  useEffect(() => {
    isMountedRef.current = true
    fetchRevenue()
    return () => { isMountedRef.current = false }
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
  const isMountedRef = useRef(true)

  const fetchUsage = useCallback(async () => {
    if (!clientId) {
      if (isMountedRef.current) setIsLoading(false)
      return
    }

    if (isMountedRef.current) setIsLoading(true)
    if (isMountedRef.current) setError(null)

    try {
      const data = await saasMetricsClientService.getClientUsage(clientId)
      if (isMountedRef.current) setUsage(data)
    } catch (err) {
      if (!isMountedRef.current) return
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else {
        setError("Erro ao carregar uso do cliente")
      }
    } finally {
      if (isMountedRef.current) setIsLoading(false)
    }
  }, [clientId])

  useEffect(() => {
    isMountedRef.current = true
    fetchUsage()
    return () => { isMountedRef.current = false }
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
  const isMountedRef = useRef(true)

  const fetchHealth = useCallback(async () => {
    if (!clientId) {
      if (isMountedRef.current) setIsLoading(false)
      return
    }

    if (isMountedRef.current) setIsLoading(true)
    if (isMountedRef.current) setError(null)

    try {
      const data = await saasMetricsClientService.getClientHealth(clientId)
      if (isMountedRef.current) setHealth(data)
    } catch (err) {
      if (!isMountedRef.current) return
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else {
        setError("Erro ao carregar saúde do cliente")
      }
    } finally {
      if (isMountedRef.current) setIsLoading(false)
    }
  }, [clientId])

  useEffect(() => {
    isMountedRef.current = true
    fetchHealth()
    return () => { isMountedRef.current = false }
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
  const isMountedRef = useRef(true)

  const fetchPayments = useCallback(async () => {
    if (!clientId) {
      if (isMountedRef.current) setIsLoading(false)
      return
    }

    if (isMountedRef.current) setIsLoading(true)
    if (isMountedRef.current) setError(null)

    try {
      const data = await saasMetricsClientService.getClientPayments(clientId)
      if (isMountedRef.current) setPayments(data)
    } catch (err) {
      if (!isMountedRef.current) return
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else {
        setError("Erro ao carregar pagamentos do cliente")
      }
    } finally {
      if (isMountedRef.current) setIsLoading(false)
    }
  }, [clientId])

  useEffect(() => {
    isMountedRef.current = true
    fetchPayments()
    return () => { isMountedRef.current = false }
  }, [fetchPayments])

  return {
    payments,
    isLoading,
    error,
    refetch: fetchPayments,
  }
}
