"use client"

import React, { useState, useRef, useCallback, useEffect } from "react"
import { Brain } from "lucide-react"
import { cn } from "@/lib/utils"
import { useLiaChatContext } from "@/contexts/lia-float-context"
import { useAuthStore } from "@/stores/auth-store"
import { useTranslations } from 'next-intl'
import {
  BUBBLE_POSITION_STORAGE_KEY,
  BUBBLE_RESET_EVENT,
  getUserScopedKey,
} from "./floating-position"
import { getPersisted, setPersisted, removePersisted } from "@/lib/lia-persistence"

const RESET_EVENT = BUBBLE_RESET_EVENT
const DRAG_THRESHOLD = 4
const BUTTON_SIZE = 56
const ARROW_STEP = 8
const ARROW_STEP_LARGE = 32

interface Props {
  onOpen: () => void
}

function clampPosition(p: { x: number; y: number }) {
  const x = Math.max(0, Math.min(window.innerWidth - BUTTON_SIZE, p.x))
  const y = Math.max(0, Math.min(window.innerHeight - BUTTON_SIZE, p.y))
  return { x, y }
}

// Onda 4-P2-6 (2026-05-24): readBubblePosition migrado pra canonical
// liaPersistence helper (TTL long = 90 dias). Backwards-compat: legacy raw
// {x,y} é auto-removido pelo getPersisted; user vê posição default no
// primeiro load pós-migration (equivalente a "reset").
function readBubblePosition(key: string): { x: number; y: number } | null {
  if (typeof window === "undefined") return null
  const parsed = getPersisted<{ x?: number; y?: number } | null>(key, null)
  if (parsed && typeof parsed.x === "number" && typeof parsed.y === "number") {
    return clampPosition({ x: parsed.x, y: parsed.y })
  }
  return null
}

function getStoredBubblePositionFor(userId: string | null | undefined): { x: number; y: number } | null {
  if (typeof window === "undefined") return null
  // Try the per-user key first, then migrate from the legacy unscoped key.
  const scoped = readBubblePosition(getUserScopedKey(BUBBLE_POSITION_STORAGE_KEY, userId))
  if (scoped) return scoped
  return readBubblePosition(BUBBLE_POSITION_STORAGE_KEY)
}

function getDefaultPosition(): { x: number; y: number } {
  if (typeof window === "undefined") return { x: 0, y: 0 }
  return { x: window.innerWidth - BUTTON_SIZE - 24, y: window.innerHeight - BUTTON_SIZE - 24 }
}

export function UnifiedChatBubble({ onOpen }: Props) {
  const { chatIsConnected } = useLiaChatContext()
  const t = useTranslations('chat.bubble')
  const userId = useAuthStore(s => s.user?.id ?? null)
  const [position, setPosition] = useState<{ x: number; y: number } | null>(
    () => getStoredBubblePositionFor(userId),
  )
  const isDragging = useRef(false)
  const dragStart = useRef<{ x: number; y: number; bx: number; by: number } | null>(null)
  const dragOriginPosition = useRef<{ x: number; y: number } | null>(null)
  const hasMoved = useRef(false)
  const buttonRef = useRef<HTMLButtonElement>(null)

  // Reload bubble position when the active user changes (login/logout)
  const lastUserIdRef = useRef<string | null>(userId)
  useEffect(() => {
    if (lastUserIdRef.current === userId) return
    lastUserIdRef.current = userId
    setPosition(getStoredBubblePositionFor(userId))
  }, [userId])

  useEffect(() => {
    // Onda 4-P2-6: canonical persistence com TTL long (90 dias)
    const key = getUserScopedKey(BUBBLE_POSITION_STORAGE_KEY, userId)
    if (position) {
      setPersisted(key, position)
    } else {
      removePersisted(key)
    }
    // Always drop the legacy unscoped key so resets are durable for users
    // who had been migrated from the old global key.
    removePersisted(BUBBLE_POSITION_STORAGE_KEY)
  }, [position, userId])

  // Robust Esc cancel during pointer drag (works even if focus has moved)
  useEffect(() => {
    const handleKey = (ev: KeyboardEvent) => {
      if (ev.key !== "Escape" || !isDragging.current) return
      ev.preventDefault()
      const origin = dragOriginPosition.current
      isDragging.current = false
      dragStart.current = null
      hasMoved.current = false
      dragOriginPosition.current = null
      setPosition(origin)
    }
    window.addEventListener("keydown", handleKey)
    return () => window.removeEventListener("keydown", handleKey)
  }, [])

  useEffect(() => {
    const handleResize = () => {
      setPosition(prev => {
        if (!prev) return prev
        const next = clampPosition(prev)
        if (next.x === prev.x && next.y === prev.y) return prev
        return next
      })
    }
    window.addEventListener("resize", handleResize)
    return () => window.removeEventListener("resize", handleResize)
  }, [])

  useEffect(() => {
    const handleReset = () => setPosition(null)
    window.addEventListener(RESET_EVENT, handleReset)
    return () => window.removeEventListener(RESET_EVENT, handleReset)
  }, [])

  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    isDragging.current = true
    hasMoved.current = false
    const rect = buttonRef.current?.getBoundingClientRect()
    if (!rect) return
    dragStart.current = { x: e.clientX, y: e.clientY, bx: rect.left, by: rect.top }
    dragOriginPosition.current = position
    ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
  }, [position])

  const handlePointerMove = useCallback((e: React.PointerEvent) => {
    if (!isDragging.current || !dragStart.current) return
    const dx = e.clientX - dragStart.current.x
    const dy = e.clientY - dragStart.current.y
    if (Math.abs(dx) > DRAG_THRESHOLD || Math.abs(dy) > DRAG_THRESHOLD) hasMoved.current = true
    if (!hasMoved.current) return
    setPosition(clampPosition({ x: dragStart.current.bx + dx, y: dragStart.current.by + dy }))
  }, [])

  const handlePointerUp = useCallback(() => {
    isDragging.current = false
    dragStart.current = null
    dragOriginPosition.current = null
    if (hasMoved.current) {
      hasMoved.current = false
      return
    }
    onOpen()
  }, [onOpen])

  const handlePointerCancel = useCallback(() => {
    isDragging.current = false
    dragStart.current = null
    dragOriginPosition.current = null
    hasMoved.current = false
  }, [])

  const handleClick = useCallback((e: React.MouseEvent) => {
    if (hasMoved.current) {
      e.preventDefault()
      return
    }
  }, [])

  // Right-click on the bubble offers a quick "reset position" affordance
  const handleContextMenu = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    setPosition(null)
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent(BUBBLE_RESET_EVENT))
    }
  }, [])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault()
      onOpen()
      return
    }
    if (e.key === "Escape" && isDragging.current) {
      e.preventDefault()
      const origin = dragOriginPosition.current
      isDragging.current = false
      dragStart.current = null
      hasMoved.current = false
      dragOriginPosition.current = null
      setPosition(origin)
      return
    }
    const arrowMap: Record<string, [number, number]> = {
      ArrowUp: [0, -1],
      ArrowDown: [0, 1],
      ArrowLeft: [-1, 0],
      ArrowRight: [1, 0],
    }
    const delta = arrowMap[e.key]
    if (delta) {
      e.preventDefault()
      const step = e.shiftKey ? ARROW_STEP_LARGE : ARROW_STEP
      setPosition(prev => {
        const base = prev ?? getDefaultPosition()
        return clampPosition({ x: base.x + delta[0] * step, y: base.y + delta[1] * step })
      })
    }
  }, [onOpen])

  const style: React.CSSProperties = position
    ? { left: position.x, top: position.y, right: "auto", bottom: "auto" }
    : {}

  return (
    <button
      ref={buttonRef}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerCancel}
      onClick={handleClick}
      onContextMenu={handleContextMenu}
      onKeyDown={handleKeyDown}
      data-testid="lia-bubble"
      className={cn(
        "fixed z-50 touch-none select-none",
        !position && "bottom-6 right-6",
        "w-14 h-14 rounded-full",
        "bg-wedo-cyan shadow-lg shadow-wedo-cyan/30",
        "flex items-center justify-center",
        "transition-transform motion-reduce:transition-none",
        "hover:scale-110 hover:shadow-lia-lg hover:shadow-wedo-cyan/40",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/50 focus-visible:ring-offset-2",
        "cursor-grab active:cursor-grabbing",
        "group"
      )}
      style={style}
      title={t('openLia', { shortcut: '\u2318\u21E7K' })}
      aria-label={t('openLiaLabel')}
    >
      <Brain
        className="w-7 h-7 text-white drop-shadow-sm group-hover:drop-shadow-md transition-all motion-reduce:transition-none"
        strokeWidth={2.2}
      />

      {/* Drag affordance — 6 small dots, visible on hover/focus */}
      <span
        aria-hidden="true"
        className={cn(
          "absolute -bottom-1 left-1/2 -translate-x-1/2 flex gap-[3px]",
          "opacity-0 group-hover:opacity-80 group-focus-visible:opacity-80 transition-opacity motion-reduce:transition-none"
        )}
      >
        <span className="w-[3px] h-[3px] rounded-full bg-white/90" />
        <span className="w-[3px] h-[3px] rounded-full bg-white/90" />
        <span className="w-[3px] h-[3px] rounded-full bg-white/90" />
      </span>

      {chatIsConnected && (
        <span className="absolute top-0 right-0 w-2.5 h-2.5 rounded-full bg-status-success ring-2 ring-wedo-cyan" />
      )}
    </button>
  )
}
