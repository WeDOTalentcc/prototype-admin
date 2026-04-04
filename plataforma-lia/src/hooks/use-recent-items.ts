"use client"

import { useState, useEffect, useCallback } from "react"
import { useRecentItemsStore } from "@/stores/recent-items-store"
import type { RecentItem } from "@/stores/recent-items-store"

export type { RecentItem }

export function useRecentItems() {
  const store = useRecentItemsStore()
  const [hasMounted, setHasMounted] = useState(false)

  useEffect(() => {
    setHasMounted(true)
  }, [])

  const addRecentItem = useCallback((item: Omit<RecentItem, 'timestamp'>) => {
    store.addItem({ ...item, timestamp: Date.now() })
  }, [store])

  const removeRecentItem = useCallback((id: string, type: RecentItem['type']) => {
    store.removeItem(id, type)
  }, [store])

  const clearAll = useCallback(() => {
    store.clearAll()
  }, [store])

  return {
    recentItems: hasMounted ? store.items : [],
    addRecentItem,
    removeRecentItem,
    clearAll
  }
}
