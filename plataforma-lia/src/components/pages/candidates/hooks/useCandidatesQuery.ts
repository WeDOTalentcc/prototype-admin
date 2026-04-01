"use client"

import { useState, useCallback, useEffect } from "react"
import { liaApi, CandidateLocal } from "@/services/lia-api"
import {
  searchCandidates as searchCandidatesHybrid,
  searchLocalCandidates,
  type SearchRequest,
  type SearchResponse,
} from "@/lib/api/candidate-search"
import type { Candidate, SearchMetadata } from "../types"

interface UseCandidatesQueryOptions {
  initialPageSize?: number
  enableAutoRefresh?: boolean
  refreshInterval?: number
}

interface UseCandidatesQueryResult {
  candidates: Candidate[]
  isLoading: boolean
  error: Error | null
  totalCount: number
  searchMetadata: SearchMetadata | null
  search: (query: string, filters?: Record<string, unknown>) => Promise<void>
  searchLocal: (query: string) => Promise<void>
  searchGlobal: (query: string) => Promise<void>
  loadMore: () => Promise<void>
  refresh: () => Promise<void>
  clearSearch: () => void
}

export function useCandidatesQuery(options: UseCandidatesQueryOptions = {}): UseCandidatesQueryResult {
  const { initialPageSize = 20 } = options
  
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [totalCount, setTotalCount] = useState(0)
  const [searchMetadata, setSearchMetadata] = useState<SearchMetadata | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [lastQuery, setLastQuery] = useState("")

  const transformCandidate = useCallback((raw: CandidateLocal): Candidate => {    // @ts-ignore // TODO: fix type
    return {
      id: raw.id,
      candidateId: raw.id,
      name: raw.name,
      email: raw.email || "",
      phone: raw.phone || "",
      linkedin_url: raw.linkedin_url,
      avatar_url: raw.avatar_url,
      current_title: raw.current_title,
      current_company: raw.current_company,
      seniority_level: raw.seniority_level,
      years_of_experience: raw.years_of_experience,
      technical_skills: raw.technical_skills,
      location_city: raw.location_city,
      location_state: raw.location_state,
      is_remote: raw.is_remote,
      lia_score: raw.lia_score,
      lia_insights: raw.lia_insights,
      source: raw.source,
      tags: raw.tags,
      created_at: raw.created_at,
      updated_at: raw.updated_at,
      position: raw.current_title || "Não informado",
      monthlySalary: raw.current_salary || 0,
      location: [raw.location_city, raw.location_state].filter(Boolean).join(", ") || "Não informado",
      workModel: raw.is_remote ? "remoto" : "híbrido",
      score: raw.lia_score || 0,
      contractType: "CLT",
      linkedin: raw.linkedin_url || "",
    }
  }, [])

  const search = useCallback(async (query: string, filters?: Record<string, unknown>) => {
    setIsLoading(true)
    setError(null)
    setLastQuery(query)
    setCurrentPage(1)
    
    const startTime = Date.now()
    
    try {
      const request: SearchRequest = {
        // @ts-ignore // TODO: fix type
        query,
        // @ts-ignore // TODO: fix type
        limit: initialPageSize,
        offset: 0,
        filters: filters as SearchRequest["filters"],
      }
      
      // @ts-ignore // TODO: fix type
      const response: SearchResponse = await searchCandidatesHybrid(request)
      
      // @ts-ignore // TODO: fix type
      const transformedCandidates = response.candidates.map((c) => transformCandidate(c as CandidateLocal))
      
      setCandidates(transformedCandidates)      // @ts-ignore // TODO: fix type
      setTotalCount(response.total)
      setSearchMetadata({
        query,
        // @ts-ignore // TODO: fix type
        totalResults: response.total,
        // @ts-ignore // TODO: fix type
        source: response.source || "hybrid",
        creditsUsed: response.credits_used,
        searchTime: Date.now() - startTime,
      })
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Search failed"))
      setCandidates([])
    } finally {
      setIsLoading(false)
    }
  }, [initialPageSize, transformCandidate])

  const searchLocal = useCallback(async (query: string) => {
    setIsLoading(true)
    // @ts-ignore // TODO: fix type
    setError(null)
    setLastQuery(query)
    
    const startTime = Date.now()
    
    try {      // @ts-ignore // TODO: fix type
      const response = await searchLocalCandidates({
        query,
        // @ts-ignore // TODO: fix type
        limit: initialPageSize,
        offset: 0,
      })      
      // @ts-ignore // TODO: fix type
      const transformedCandidates = response.candidates.map((c) => transformCandidate(c as CandidateLocal))
      
      setCandidates(transformedCandidates)
      // @ts-ignore // TODO: fix type
      setTotalCount(response.total)
      setSearchMetadata({
        query,
        // @ts-ignore // TODO: fix type
        totalResults: response.total,
        source: "local",
        searchTime: Date.now() - startTime,
      })
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Local search failed"))
    } finally {
      setIsLoading(false)
    }
  }, [initialPageSize, transformCandidate])

  // @ts-ignore // TODO: fix type
  const searchGlobal = useCallback(async (query: string) => {
    setIsLoading(true)
    setError(null)
    setLastQuery(query)
    
    // @ts-ignore // TODO: fix type
    const startTime = Date.now()
    
    try {
      // @ts-ignore // TODO: fix type
      const response = await searchCandidatesHybrid({
        query,
        // @ts-ignore // TODO: fix type
        limit: initialPageSize,
        offset: 0,
        use_global: true,
      })
      
      // @ts-ignore // TODO: fix type
      const transformedCandidates = response.candidates.map((c) => transformCandidate(c as CandidateLocal))
      
      setCandidates(transformedCandidates)
      // @ts-ignore // TODO: fix type
      setTotalCount(response.total)
      setSearchMetadata({
        query,
        // @ts-ignore // TODO: fix type
        totalResults: response.total,
        source: "global",
        creditsUsed: response.credits_used,
        searchTime: Date.now() - startTime,
      })
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Global search failed"))
    } finally {
      setIsLoading(false)
    // @ts-ignore // TODO: fix type
    }
  }, [initialPageSize, transformCandidate])

  const loadMore = useCallback(async () => {
    // @ts-ignore // TODO: fix type
    if (isLoading || !lastQuery) return
    
    setIsLoading(true)
    
    try {
      const nextPage = currentPage + 1
      const offset = (nextPage - 1) * initialPageSize
      
      const response = await searchCandidatesHybrid({
        query: lastQuery,
        // @ts-ignore // TODO: fix type
        limit: initialPageSize,
        offset,
      })
      
      // @ts-ignore // TODO: fix type
      const transformedCandidates = response.candidates.map((c) => transformCandidate(c as CandidateLocal))
      
      setCandidates((prev) => [...prev, ...transformedCandidates])
      setCurrentPage(nextPage)
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Load more failed"))
    } finally {
      setIsLoading(false)
    }
  }, [isLoading, lastQuery, currentPage, initialPageSize, transformCandidate])

  const refresh = useCallback(async () => {
    if (lastQuery) {
      await search(lastQuery)
    }
  }, [lastQuery, search])

  const clearSearch = useCallback(() => {
    setCandidates([])
    setTotalCount(0)
    setSearchMetadata(null)
    setLastQuery("")
    setCurrentPage(1)
    setError(null)
  }, [])

  return {
    candidates,
    isLoading,
    error,
    totalCount,
    searchMetadata,
    search,
    searchLocal,
    searchGlobal,
    loadMore,
    refresh,
    clearSearch,
  }
}
