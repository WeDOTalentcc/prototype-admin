/**
 * @deprecated Use UnifiedChat (sidebar mode) via InlineChatBridge instead.
 * This component is replaced by the unified chat architecture (Phase 6).
 * Migration: import { InlineChatBridge } from "@/components/unified-chat"
 */
"use client"

import React, { useState, useRef, useCallback } from "react"
import { Brain } from "lucide-react"
import { cn } from "@/lib/utils"
import { useLiaFloat } from "@/contexts/lia-float-context"

interface LiaChatButtonProps {
  className?: string
}

export function LiaChatButton({ className }: LiaChatButtonProps) {
  const { isOpen, toggle } = useLiaFloat()
  const [position, setPosition] = useState<{ x: number; y: number } | null>(null)
  const isDragging = useRef(false)
  const dragStart = useRef<{ x: number; y: number; bx: number; by: number } | null>(null)
  const hasMoved = useRef(false)
  const buttonRef = useRef<HTMLButtonElement>(null)

  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    isDragging.current = true
    hasMoved.current = false
    const rect = buttonRef.current?.getBoundingClientRect()
    if (!rect) return
    dragStart.current = { x: e.clientX, y: e.clientY, bx: rect.left, by: rect.top }
    ;(e.target as HTMLElement).setPointerCapture(e.pointerId)
  }, [])

  const handlePointerMove = useCallback((e: React.PointerEvent) => {
    if (!isDragging.current || !dragStart.current) return
    const dx = e.clientX - dragStart.current.x
    const dy = e.clientY - dragStart.current.y
    if (Math.abs(dx) > 4 || Math.abs(dy) > 4) hasMoved.current = true
    if (!hasMoved.current) return
    const newX = Math.max(0, Math.min(window.innerWidth - 64, dragStart.current.bx + dx))
    const newY = Math.max(0, Math.min(window.innerHeight - 64, dragStart.current.by + dy))
    setPosition({ x: newX, y: newY })
  }, [])

  const handlePointerUp = useCallback(() => {
    isDragging.current = false
    dragStart.current = null
    if (hasMoved.current) {
      hasMoved.current = false
      return
    }
    toggle()
  }, [toggle])

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
      toggle()
    }
  }, [toggle])

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
      aria-label={isOpen ? "Fechar LIA" : "Abrir LIA"}
      title={isOpen ? "Fechar LIA" : "Conversar com LIA"}
      className={cn(
        "fixed z-50 touch-none select-none",
        !position && "bottom-6 left-6",
        "w-16 h-16",
        "flex items-center justify-center",
        "bg-transparent",
        "transition-shadow duration-200",
        "hover:scale-110",
        "focus-visible:outline-none",
        className
      )}
      style={style}
    >
      <Brain
        className={cn(
          "w-10 h-10 transition-colors duration-200 drop-shadow-lia-md",
          isOpen
            ? "text-wedo-cyan-text scale-95"
            : "text-wedo-cyan-text hover:drop-shadow-lia-lg"
        )}
        strokeWidth={2}
      />
    </button>
  )
}
