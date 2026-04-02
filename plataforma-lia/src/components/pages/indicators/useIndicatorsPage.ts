"use client"

import { useState, useMemo, useCallback } from "react"
import type { ActiveTab, ViewMode, TeamMetrics, RecruiterData } from "./indicators.types"
import { recruitersData } from "./indicators.constants"

export function useIndicatorsPage() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("recruiters")
  const [selectedPeriod, setSelectedPeriod] = useState("current_month")
  const [selectedDepartments, setSelectedDepartments] = useState<string[]>([])
  const [selectedRecruiters, setSelectedRecruiters] = useState<string[]>([])
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false)
  const [viewMode, setViewMode] = useState<ViewMode>("cards")
  const [sortBy, setSortBy] = useState("totalScore")
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc")
  const [selectedCandidates, setSelectedCandidates] = useState<any[]>([])
  const [showExportModal, setShowExportModal] = useState(false)

  const recruiters = Object.values(recruitersData) as RecruiterData[]
  const departments = [...new Set(recruiters.map((r) => r.department))]

  const filteredRecruiters = useMemo(() => {
    const filtered = recruiters
      .filter((r) => selectedDepartments.length === 0 || selectedDepartments.includes(r.department))
      .filter((r) => selectedRecruiters.length === 0 || selectedRecruiters.includes(r.name))

    return [...filtered].sort((a, b) => {
      const aVal = a[sortBy as keyof typeof a] as number
      const bVal = b[sortBy as keyof typeof b] as number
      return sortOrder === "desc" ? bVal - aVal : aVal - bVal
    })
  }, [selectedDepartments, selectedRecruiters, sortBy, sortOrder, recruiters])

  const teamMetrics = useMemo((): TeamMetrics => {
    const total = recruiters.reduce(
      (acc, r) => ({
        activeJobs: acc.activeJobs + r.activeJobs,
        totalCandidates: acc.totalCandidates + r.totalCandidates,
        totalHires: acc.totalHires + r.totalHires,
        completedInterviews: acc.completedInterviews + r.completedInterviews,
      }),
      { activeJobs: 0, totalCandidates: 0, totalHires: 0, completedInterviews: 0 }
    )

    const avgConversionRate = (
      recruiters.reduce((acc, r) => acc + r.conversionRate, 0) / recruiters.length
    ).toFixed(1)
    const avgTimeToFill = Math.round(
      recruiters.reduce((acc, r) => acc + r.avgTimeToFill, 0) / recruiters.length
    )
    const avgNPS = Math.round(
      recruiters.reduce((acc, r) => acc + r.npsScore, 0) / recruiters.length
    )
    const avgQualityScore = (
      recruiters.reduce((acc, r) => acc + r.qualityOfHireScore, 0) / recruiters.length
    ).toFixed(1)

    return {
      ...total,
      avgConversionRate,
      avgTimeToFill,
      avgNPS,
      avgQualityScore,
      totalRecruiters: recruiters.length,
    }
  }, [recruiters])

  const getStatusColor = useCallback((status: string) => {
    switch (status) {
      case "exceeded":
        return "text-status-success bg-status-success/15"
      case "achieved":
        return "text-lia-text-secondary bg-gray-100 dark:bg-lia-bg-secondary"
      case "on_track":
        return "text-status-warning bg-status-warning/15"
      case "behind":
        return "text-status-error bg-status-error/15"
      default:
        return "text-lia-text-secondary bg-gray-100"
    }
  }, [])

  const handleCommandAction = useCallback((_command: string, _action: string) => {
    // Implementar acoes da LIA aqui
  }, [])

  const handleAlertAction = useCallback((_alertId: string, action: string) => {
    switch (action) {
      case "mark_read":
        break
      case "archive":
        break
      case "delete":
        break
      case "send_notification":
        break
    }
  }, [])

  return {
    activeTab,
    setActiveTab,
    selectedPeriod,
    setSelectedPeriod,
    selectedDepartments,
    setSelectedDepartments,
    selectedRecruiters,
    setSelectedRecruiters,
    showAdvancedFilters,
    setShowAdvancedFilters,
    viewMode,
    setViewMode,
    sortBy,
    setSortBy,
    sortOrder,
    setSortOrder,
    selectedCandidates,
    setSelectedCandidates,
    showExportModal,
    setShowExportModal,
    recruiters,
    departments,
    filteredRecruiters,
    teamMetrics,
    getStatusColor,
    handleCommandAction,
    handleAlertAction,
  }
}
