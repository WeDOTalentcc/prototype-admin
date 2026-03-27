"use client"

import { useState, useEffect, useCallback } from "react"

export interface RecentItem {
  id: string
  type: 'vaga' | 'chat' | 'candidato'
  title: string
  subtitle?: string
  timestamp: number
  meta?: {
    jobId?: string
    candidateId?: string
    conversationId?: string
    jobTitle?: string
  }
}

const STORAGE_KEY = 'lia-recent-items'
const MAX_ITEMS = 15

function loadItems(): RecentItem[] {
  if (typeof window === 'undefined') return []
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed
  } catch {
    return []
  }
}

function saveItems(items: RecentItem[]) {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
  } catch {
    // storage full or unavailable
  }
}

export function useRecentItems() {
  const [recentItems, setRecentItems] = useState<RecentItem[]>([])
  const [hasMounted, setHasMounted] = useState(false)

  useEffect(() => {
    setHasMounted(true)
    setRecentItems(loadItems())
  }, [])

  const addRecentItem = useCallback((item: Omit<RecentItem, 'timestamp'>) => {
    setRecentItems(prev => {
      const filtered = prev.filter(
        existing => !(existing.id === item.id && existing.type === item.type)
      )
      const newItem: RecentItem = { ...item, timestamp: Date.now() }
      const updated = [newItem, ...filtered].slice(0, MAX_ITEMS)
      saveItems(updated)
      return updated
    })
  }, [])

  const removeRecentItem = useCallback((id: string, type: RecentItem['type']) => {
    setRecentItems(prev => {
      const updated = prev.filter(
        item => !(item.id === id && item.type === type)
      )
      saveItems(updated)
      return updated
    })
  }, [])

  const clearAll = useCallback(() => {
    setRecentItems([])
    saveItems([])
  }, [])

  return {
    recentItems: hasMounted ? recentItems : [],
    addRecentItem,
    removeRecentItem,
    clearAll
  }
}
