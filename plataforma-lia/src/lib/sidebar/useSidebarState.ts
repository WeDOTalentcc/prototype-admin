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
 * @version 1.0.1
 * @sprint F2-6
 */

"use client"

import { useState, useEffect, useCallback, useMemo, useRef } from "react"
import {
  type SidebarState,
  type SidebarComputed,
  SIDEBAR_DEFAULTS,
} from "./sidebar.types"
import { useUIPreferencesStore } from "@/stores/ui-preferences-store"
import { useHoverDebounce } from "./useHoverDebounce"

// ─── Return type ──────────────────────────────────────────────────────────────

export interface UseSidebarStateReturn extends SidebarState, SidebarComputed {
  reducedMotion: boolean
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
  const [sidebarWidth, setSidebarWidth] = useState<number>(SIDEBAR_DEFAULTS.WIDTH)
  const [isResizing, setIsResizing] = useState(false)

  // ── Mount guard (SSR safe) ──────────────────────────────────────────────────
  useEffect(() => {
    setIsMounted(true)
  }, [])

  // ── Zustand store — individual selectors to avoid full-store re-renders ─────
  const sidebarCollapsed = useUIPreferencesStore((s) => s.sidebarCollapsed)
  const storedWidth = useUIPreferencesStore((s) => s.sidebarWidth)
  const setSidebarCollapsed = useUIPreferencesStore((s) => s.setSidebarCollapsed)
  const setStoredWidth = useUIPreferencesStore((s) => s.setSidebarWidth)

  useEffect(() => {
    if (!isMounted) return
    setIsCollapsed(sidebarCollapsed)
    setSidebarWidth(storedWidth)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isMounted])

  // ── Sync isCollapsed → Zustand store (one-way, skips initial mount) ─────────
  const isSyncInitialised = useRef(false)
  useEffect(() => {
    if (!isMounted) return
    if (!isSyncInitialised.current) {
      isSyncInitialised.current = true
      return
    }
    setSidebarCollapsed(isCollapsed)
  }, [isCollapsed, isMounted, setSidebarCollapsed])

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
  // Use a ref to always have the latest width available in the mouseup closure.
  // Keep it in sync with sidebarWidth (including the initial store-hydrated value).
  const sidebarWidthRef = useRef(sidebarWidth)
  useEffect(() => {
    sidebarWidthRef.current = sidebarWidth
  }, [sidebarWidth])

  const startResize = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    setIsResizing(true)
    const startX = e.clientX
    const startWidth = sidebarWidthRef.current

    const handleMouseMove = (moveEvent: MouseEvent) => {
      const delta = moveEvent.clientX - startX
      const newWidth = Math.max(
        SIDEBAR_DEFAULTS.MIN_WIDTH,
        Math.min(SIDEBAR_DEFAULTS.MAX_WIDTH, startWidth + delta)
      )
      sidebarWidthRef.current = newWidth
      setSidebarWidth(newWidth)
    }

    const handleMouseUp = () => {
      setIsResizing(false)
      setStoredWidth(sidebarWidthRef.current)
      document.removeEventListener("mousemove", handleMouseMove)
      document.removeEventListener("mouseup", handleMouseUp)
      document.body.style.cursor = ""
      document.body.style.userSelect = ""
    }

    document.addEventListener("mousemove", handleMouseMove)
    document.addEventListener("mouseup", handleMouseUp)
    document.body.style.cursor = "col-resize"
    document.body.style.userSelect = "none"
  }, [setStoredWidth])

  useEffect(() => {
    if (!isCollapsed) {
      setIsTemporaryExpanded(false)
    }
  }, [isCollapsed])

  // ── Actions ────────────────────────────────────────────────────────────────
  const toggleCollapse = useCallback(() => {
    setIsCollapsed((prev) => !prev)
  }, [])

  const expandOnHover = useCallback(() => {
    setIsTemporaryExpanded(true)
  }, [])

  const collapseOnHover = useCallback(() => {
    setIsTemporaryExpanded(false)
  }, [])

  const { handleMouseEnter, handleMouseLeave, reducedMotion } = useHoverDebounce({
    onExpand: expandOnHover,
    onCollapse: collapseOnHover,
    isEnabled: isCollapsed,
  })

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
    reducedMotion,
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
