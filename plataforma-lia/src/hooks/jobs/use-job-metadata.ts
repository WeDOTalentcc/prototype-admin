"use client"

import useSWR from "swr"
import {
  fetchDepartments, fetchCities, fetchJobPriorities, fetchJobUrgencyLevels,
  fetchJobWorkplaceTypes, fetchJobEmploymentTypes, fetchJobSeniorities,
  fetchJobStatuses, searchUsers,
} from "@/services/jobs/job-metadata.service"
import type { RemoteOption, SeniorityOption, UserSearchHit } from "@/services/jobs/job-metadata.types"

const SHARED_CONFIG = {
  revalidateOnFocus: false,
  dedupingInterval: 60_000,
  shouldRetryOnError: false,
} as const

export function useJobStatuses() {
  const { data, error, isLoading } = useSWR<RemoteOption[]>("job-statuses", fetchJobStatuses, SHARED_CONFIG)
  return { options: data ?? [], error, isLoading }
}

export function useJobPriorities() {
  const { data, error, isLoading } = useSWR<RemoteOption[]>("job-priorities", fetchJobPriorities, SHARED_CONFIG)
  return { options: data ?? [], error, isLoading }
}

export function useJobUrgencyLevels() {
  const { data, error, isLoading } = useSWR<RemoteOption[]>("job-urgency-levels", fetchJobUrgencyLevels, SHARED_CONFIG)
  return { options: data ?? [], error, isLoading }
}

export function useJobWorkplaceTypes() {
  const { data, error, isLoading } = useSWR<RemoteOption[]>("job-workplace-types", fetchJobWorkplaceTypes, SHARED_CONFIG)
  return { options: data ?? [], error, isLoading }
}

export function useJobEmploymentTypes() {
  const { data, error, isLoading } = useSWR<RemoteOption[]>("job-employment-types", fetchJobEmploymentTypes, SHARED_CONFIG)
  return { options: data ?? [], error, isLoading }
}

export function useJobSeniorities() {
  const { data, error, isLoading } = useSWR<SeniorityOption[]>("job-seniorities", fetchJobSeniorities, SHARED_CONFIG)
  return { options: data ?? [], error, isLoading }
}

export function useDepartmentsSearch(query: string) {
  const key: [string, string] = ["departments", query]
  const { data, error, isLoading } = useSWR<RemoteOption[]>(
    key,
    ([, q]) => fetchDepartments(q as string),
    SHARED_CONFIG,
  )
  return { options: data ?? [], error, isLoading }
}

export function useCitiesSearch(query: string) {
  const key: [string, string] = ["cities", query]
  const { data, error, isLoading } = useSWR<RemoteOption[]>(
    key,
    ([, q]) => fetchCities(q as string),
    SHARED_CONFIG,
  )
  return { options: data ?? [], error, isLoading }
}

export function useUserSearch(query: string) {
  const key = query.length >= 2 ? (["user-search", query] as const) : null
  const { data, error, isLoading } = useSWR<UserSearchHit[]>(
    key,
    ([, q]) => searchUsers(q as string),
    SHARED_CONFIG,
  )
  return { options: data ?? [], error, isLoading }
}
