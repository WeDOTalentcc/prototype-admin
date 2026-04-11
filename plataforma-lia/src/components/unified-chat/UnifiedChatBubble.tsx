"use client"

import React, { useState, useRef, useCallback, useEffect } from "react"
import { Brain } from "lucide-react"
import { cn } from "@/lib/utils"
import { useLiaChatContext } from "@/contexts/lia-float-context"

const POSITION_STORAGE_KEY = "lia-bubble-position"
const DRAG_THRESHOLD = 4
const BUTTON_SIZE = 56

interface Props {
  onOpen: () => void
}

function getStoredPosition(): { x: number; y: number } | null {
  if (typeof window === "undefined") return null
  try {
    const stored = localStorage.getItem(POSITION_STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      if (typeof parsed.x === "number" && typeof parsed.y === "number") {
        const x = Math.max(0, Math.min(window.innerWidth - BUTTON_SIZE, parsed.x))
        const y = Math.max(0, Math.min(window.innerHeight - BUTTON_SIZE, parsed.y))
        return { x, y }
      }
    }
  } catch {}
  return null
}

export function UnifiedChatBubble({ onOpen }: Props) {
  const { chatIsConnected } = useLiaChatContext()
  const [position, setPosition] = useState<{ x: number; y: number } | null>(getStoredPosition)
  const isDragging = useRef(false)
  const dragStart = useRef<{ x: number; y: number; bx: number; by: number } | null>(null)
  const hasMoved = useRef(false)
  const buttonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (position) {
      localStorage.setItem(POSITION_STORAGE_KEY, JSON.stringify(position))
    }
  }, [position])

  useEffect(() => {
    const handleResize = () => {
      setPosition(prev => {
        if (!prev) return prev
        const x = Math.max(0, Math.min(window.innerWidth - BUTTON_SIZE, prev.x))
        const y = Math.max(0, Math.min(window.innerHeight - BUTTON_SIZE, prev.y))
        if (x === prev.x && y === prev.y) return prev
        return { x, y }
      })
    }
    window.addEventListener("resize", handleResize)
    return () => window.removeEventListener("resize", handleResize)
  }, [])

  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    isDragging.current = true
    hasMoved.current = false
    const rect = buttonRef.current?.getBoundingClientRect()
    if (!rect) return
    dragStart.current = { x: e.clientX, y: e.clientY, bx: rect.left, by: rect.top }
    ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
  }, [])

  const handlePointerMove = useCallback((e: React.PointerEvent) => {
    if (!isDragging.current || !dragStart.current) return
    const dx = e.clientX - dragStart.current.x
    const dy = e.clientY - dragStart.current.y
    if (Math.abs(dx) > DRAG_THRESHOLD || Math.abs(dy) > DRAG_THRESHOLD) hasMoved.current = true
    if (!hasMoved.current) return
    const newX = Math.max(0, Math.min(window.innerWidth - BUTTON_SIZE, dragStart.current.bx + dx))
    const newY = Math.max(0, Math.min(window.innerHeight - BUTTON_SIZE, dragStart.current.by + dy))
    setPosition({ x: newX, y: newY })
  }, [])

  const handlePointerUp = useCallback(() => {
    isDragging.current = false
    dragStart.current = null
    if (hasMoved.current) {
      hasMoved.current = false
      return
    }
    onOpen()
  }, [onOpen])

  const handlePointerCancel = useCallback(() => {
    isDragging.current = false
    dragStart.current = null
    hasMoved.current = false
  }, [])

  const handleClick = useCallback((e: React.MouseEvent) => {
    if (hasMoved.current) {
      e.preventDefault()
      return
    }
  }, [])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault()
      onOpen()
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
      onKeyDown={handleKeyDown}
      className={cn(
        "fixed z-50 touch-none select-none",
        !position && "bottom-6 right-6",
        "w-14 h-14 rounded-full",
        "bg-[#60BED1] shadow-lg shadow-[#60BED1]/30",
        "flex items-center justify-center",
        "transition-transform motion-reduce:transition-none",
        "hover:scale-110 hover:shadow-xl hover:shadow-[#60BED1]/40",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/50 focus-visible:ring-offset-2",
        "group"
      )}
      style={style}
      title="Abrir LIA (⌘⇧K)"
      aria-label="Abrir chat com a LIA"
    >
      <Brain
        className="w-7 h-7 text-white drop-shadow-sm group-hover:drop-shadow-md transition-all motion-reduce:transition-none"
        strokeWidth={2.2}
      />

      {chatIsConnected && (
        <span className="absolute top-0 right-0 w-2.5 h-2.5 rounded-full bg-status-success ring-2 ring-[#60BED1]" />
      )}
    </button>
  )
}
