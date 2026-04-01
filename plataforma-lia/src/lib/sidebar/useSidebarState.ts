/**
 * useSidebarState.ts
 *
 * Extracted state logic from sidebar.tsx.
 * Framework-agnostic by intent: all business logic lives here,
 * rendering stays in sidebar.tsx (React) or Sidebar.vue (Vue 3).
 *
 * Vue 3 migration path:
 *   Replace this hook with a composable:
 *   export function useSidebarState() { ... }  ← same signature, same return
 *   Only swap useState → ref, useEffect → watchEffect/onMounted, useCallback → plain fn
 *
 * @version 1.0.0
 * @sprint F2-6
 */

"use client"

import { useState, useEffect, useCallback, useMemo } from "react"
import {
  type SidebarState,
  type SidebarComputed,
  SIDEBAR_STORAGE_KEYS,
  SIDEBAR_DEFAULTS,
} from "./sidebar.types"

// ─── Return type ──────────────────────────────────────────────────────────────

export interface UseSidebarStateReturn extends SidebarState, SidebarComputed {
  // Actions
  toggleCollapse: () => void
  handleMouseEnter: () => void
  handleMouseLeave: () => void
  handleShowTipsModal: () => void
  handleCloseTipsModal: () => void
  startResize: (e: React.MouseEvent) => void
}

// ─── Hook ────────────────────────────────────────────────────────────────────

export function useSidebarState(): UseSidebarStateReturn {
  // ── State ──────────────────────────────────────────────────────────────────
  const [isMounted, setIsMounted] = useState(false)
  const [showTipsModal, setShowTipsModal] = useState(false)
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [isTemporaryExpanded, setIsTemporaryExpanded] = useState(false)
  const [sidebarWidth, setSidebarWidth] = useState(SIDEBAR_DEFAULTS.WIDTH)
  const [isResizing, setIsResizing] = useState(false)

  // ── Mount guard (SSR safe) ──────────────────────────────────────────────────
  useEffect(() => {
    setIsMounted(true)
  }, [])

  // ── Persist collapsed state ────────────────────────────────────────────────
  useEffect(() => {
    if (!isMounted) return
    const saved = localStorage.getItem(SIDEBAR_STORAGE_KEYS.COLLAPSED)
    if (saved !== null) {
      setIsCollapsed(JSON.parse(saved))
    }
    const savedWidth = localStorage.getItem(SIDEBAR_STORAGE_KEYS.WIDTH)
    if (savedWidth !== null) {
      setSidebarWidth(parseInt(savedWidth))
    }
  }, [isMounted])

  useEffect(() => {
    if (!isMounted) return
    localStorage.setItem(SIDEBAR_STORAGE_KEYS.COLLAPSED, JSON.stringify(isCollapsed))
  }, [isCollapsed, isMounted])

  useEffect(() => {
    if (!isMounted) return
    localStorage.setItem(SIDEBAR_STORAGE_KEYS.WIDTH, sidebarWidth.toString())
  }, [sidebarWidth, isMounted])

  // ── Keyboard shortcut Ctrl+B ───────────────────────────────────────────────
  useEffect(() => {
    const handleKeydown = (event: KeyboardEvent) => {
      if (event.ctrlKey && event.key === "b") {
        event.preventDefault()
        setIsCollapsed((prev) => !prev)
      }
    }
    window.addEventListener("keydown", handleKeydown)
    return () => window.removeEventListener("keydown", handleKeydown)
  }, [])

  // ── Resize logic ───────────────────────────────────────────────────────────
  const startResize = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    setIsResizing(true)
    const startX = e.clientX
    const startWidth = sidebarWidth

    const handleMouseMove = (moveEvent: MouseEvent) => {
      const delta = moveEvent.clientX - startX
      const newWidth = Math.max(
        SIDEBAR_DEFAULTS.MIN_WIDTH,
        Math.min(SIDEBAR_DEFAULTS.MAX_WIDTH, startWidth + delta)
      )
      setSidebarWidth(newWidth)
    }

    const handleMouseUp = () => {
      setIsResizing(false)
      document.removeEventListener("mousemove", handleMouseMove)
      document.removeEventListener("mouseup", handleMouseUp)
      document.body.style.cursor = ""
      document.body.style.userSelect = ""
    }

    document.addEventListener("mousemove", handleMouseMove)
    document.addEventListener("mouseup", handleMouseUp)
    document.body.style.cursor = "col-resize"
    document.body.style.userSelect = "none"
  }, [sidebarWidth])

  // ── Actions ────────────────────────────────────────────────────────────────
  const toggleCollapse = useCallback(() => {
    setIsCollapsed((prev) => !prev)
  }, [])

  const handleMouseEnter = useCallback(() => {
    if (isCollapsed) setIsTemporaryExpanded(true)
  }, [isCollapsed])

  const handleMouseLeave = useCallback(() => {
    setIsTemporaryExpanded(false)
  }, [])

  const handleShowTipsModal = useCallback(() => {
    setShowTipsModal(true)
  }, [])

  const handleCloseTipsModal = useCallback(() => {
    setShowTipsModal(false)
  }, [])

  // ── Computed ───────────────────────────────────────────────────────────────
  const shouldShowContent = useMemo(
    () => !isCollapsed || isTemporaryExpanded,
    [isCollapsed, isTemporaryExpanded]
  )

  const dynamicWidth = useMemo(
    () =>
      isCollapsed && !isTemporaryExpanded
        ? SIDEBAR_DEFAULTS.COLLAPSED_WIDTH
        : `${sidebarWidth}px`,
    [isCollapsed, isTemporaryExpanded, sidebarWidth]
  )

  return {
    // State
    isMounted,
    showTipsModal,
    isCollapsed,
    isTemporaryExpanded,
    sidebarWidth,
    isResizing,
    // Computed
    shouldShowContent,
    dynamicWidth,
    // Actions
    toggleCollapse,
    handleMouseEnter,
    handleMouseLeave,
    handleShowTipsModal,
    handleCloseTipsModal,
    startResize,
  }
}
