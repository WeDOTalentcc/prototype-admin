"use client"

import useSWR from swr
import {
  saasMetricsClientService,
  ClientSaasMetrics,
  ClientRevenueMetrics,
  ClientUsageMetrics,
  ClientHealthMetrics,
  ClientPayment,
  ApiClientError,
} from @/services/admin/saas-metrics-service

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
  const { data, error, isLoading, mutate } = useSWR(
    clientId ? [adminClientSaasMetrics, clientId] : null,
    ([, id]) => saasMetricsClientService.getClientMetrics(id)
  )

  return {
    metrics: data ?? null,
    isLoading,
    error: error instanceof ApiClientError ? error.message
      : error instanceof Error ? error.message
      : error ? String(error) : null,
    refetch: () => mutate(),
  }
}

export function useClientRevenue(clientId: string): UseClientRevenueResult {
  const { data, error, isLoading, mutate } = useSWR(
    clientId ? [adminClientRevenue, clientId] : null,
    ([, id]) => saasMetricsClientService.getClientRevenue(id)
  )

  return {
    revenue: data ?? null,
    isLoading,
    error: error instanceof ApiClientError ? error.message
      : error instanceof Error ? error.message
      : error ? String(error) : null,
    refetch: () => mutate(),
  }
}

export function useClientUsage(clientId: string): UseClientUsageResult {
  const { data, error, isLoading, mutate } = useSWR(
    clientId ? [adminClientUsage, clientId] : null,
    ([, id]) => saasMetricsClientService.getClientUsage(id)
  )

  return {
    usage: data ?? null,
    isLoading,
    error: error instanceof ApiClientError ? error.message
      : error instanceof Error ? error.message
      : error ? String(error) : null,
    refetch: () => mutate(),
  }
}

export function useClientHealth(clientId: string): UseClientHealthResult {
  const { data, error, isLoading, mutate } = useSWR(
    clientId ? [adminClientHealth, clientId] : null,
    ([, id]) => saasMetricsClientService.getClientHealth(id)
  )

  return {
    health: data ?? null,
    isLoading,
    error: error instanceof ApiClientError ? error.message
      : error instanceof Error ? error.message
      : error ? String(error) : null,
    refetch: () => mutate(),
  }
}

export function useClientPayments(clientId: string): UseClientPaymentsResult {
  const { data, error, isLoading, mutate } = useSWR(
    clientId ? [adminClientPayments, clientId] : null,
    ([, id]) => saasMetricsClientService.getClientPayments(id)
  )

  return {
    payments: data ?? [],
    isLoading,
    error: error instanceof ApiClientError ? error.message
      : error instanceof Error ? error.message
      : error ? String(error) : null,
    refetch: () => mutate(),
  }
}
