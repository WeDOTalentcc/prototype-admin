import { useState, useRef } from "react"
import type { SubStatus } from "@/components/settings/recruitment-journey.types"

interface UseSubStatusPanelProps {
  stageId: string
  initialSubStatuses: SubStatus[]
  onToggleSubStatus?: (subStatusId: string, updates: { is_active?: boolean; is_default?: boolean }) => Promise<void>
}

export function useSubStatusPanel({ stageId, initialSubStatuses, onToggleSubStatus }: UseSubStatusPanelProps) {
  const [expanded, setExpanded] = useState(false)
  const [allSubStatuses, setAllSubStatuses] = useState<SubStatus[]>([])
  const [loading, setLoading] = useState(false)
  const [togglingId, setTogglingId] = useState<string | null>(null)
  const hasFetched = useRef(false)

  const activeCount = initialSubStatuses.length
  const displayList = hasFetched.current ? allSubStatuses : initialSubStatuses

  const fetchAll = async () => {
    if (hasFetched.current || !stageId || stageId.startsWith('stage-') || stageId.startsWith('catalog-')) return
    setLoading(true)
    try {
      const res = await fetch(
        `/api/backend-proxy/recruitment-stages/stages/${stageId}/sub-statuses?include_inactive=true`
      )
      if (res.ok) {
        const data = await res.json()
        setAllSubStatuses(data.sub_statuses || [])
        hasFetched.current = true
      }
    } finally {
      setLoading(false)
    }
  }

  const handleExpand = () => {
    const next = !expanded
    setExpanded(next)
    if (next) fetchAll()
  }

  const handleToggleActive = async (ss: SubStatus) => {
    if (!onToggleSubStatus) return
    setTogglingId(ss.id)
    try {
      await onToggleSubStatus(ss.id, { is_active: !ss.is_active })
      setAllSubStatuses(prev => prev.map(s => s.id === ss.id ? { ...s, is_active: !s.is_active } : s))
    } finally {
      setTogglingId(null)
    }
  }

  const handleToggleDefault = async (ss: SubStatus) => {
    if (!onToggleSubStatus) return
    setTogglingId(`default-${ss.id}`)
    try {
      await onToggleSubStatus(ss.id, { is_default: !ss.is_default })
      setAllSubStatuses(prev => prev.map(s => s.id === ss.id ? { ...s, is_default: !s.is_default } : s))
    } finally {
      setTogglingId(null)
    }
  }

  return {
    expanded,
    displayList,
    loading,
    togglingId,
    activeCount,
    canFetch: !stageId.startsWith('stage-') && !stageId.startsWith('catalog-'),
    handleExpand,
    handleToggleActive,
    handleToggleDefault,
  }
}
