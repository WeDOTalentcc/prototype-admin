"use client"

import { useState } from "react"
import type { OnboardingCandidate } from "./onboarding-page.types"
import { onboardingCandidates } from "./onboarding-page.types"

export type OnboardingView = 'overview' | 'candidates' | 'templates' | 'analytics'

export function useOnboardingPage() {
  const [selectedView, setSelectedView] = useState<OnboardingView>('overview')
  const [selectedCandidate, setSelectedCandidate] = useState<OnboardingCandidate | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')

  const filteredCandidates = onboardingCandidates.filter(candidate => {
    const matchesSearch = candidate.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         candidate.position.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === 'all' || candidate.status === statusFilter
    return matchesSearch && matchesStatus
  })

  return {
    selectedView,
    setSelectedView,
    selectedCandidate,
    setSelectedCandidate,
    searchTerm,
    setSearchTerm,
    statusFilter,
    setStatusFilter,
    filteredCandidates
  }
}
