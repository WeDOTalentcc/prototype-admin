"use client"

import React, { useEffect, useState, useRef } from "react"
import { X } from "lucide-react"

interface SpotlightProps {
  /** CSS selector of the element to highlight */
  selector: string
  /** Tooltip message from LIA */
  message: string
  /** Position of tooltip relative to element */
  position?: "top" | "bottom" | "left" | "right"
  /** Auto-dismiss after N ms (0 = manual only) */
  autoDismissMs?: number
  /** Called when spotlight is dismissed */
  onDismiss?: () => void
}

/**
 * TourSpotlight — highlights a UI element with a dark overlay and LIA tooltip.
 *
 * Uses: position:fixed overlay with clip-path to "cut out" the target element.
 * Design: lia-bg-primary, wedo-cyan border, Open Sans.
 */
export function TourSpotlight({
  selector,
  message,
  position = "bottom",
  autoDismissMs = 0,
  onDismiss,
}: SpotlightProps) {
  const [rect, setRect] = useState<DOMRect | null>(null)
  const [visible, setVisible] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    // Find target element
    const el = document.querySelector(selector)
    if (!el) {
      onDismiss?.()
      return
    }

    const updateRect = () => {
      const r = el.getBoundingClientRect()
      setRect(r)
      setVisible(true)
    }

    // Initial position + scroll/resize listener
    updateRect()
    window.addEventListener("resize", updateRect)
    window.addEventListener("scroll", updateRect, true)

    // Scroll element into view
    el.scrollIntoView({ behavior: "smooth", block: "center" })

    // Auto-dismiss
    if (autoDismissMs > 0) {
      timerRef.current = setTimeout(() => {
        setVisible(false)
        onDismiss?.()
      }, autoDismissMs)
    }

    return () => {
      window.removeEventListener("resize", updateRect)
      window.removeEventListener("scroll", updateRect, true)
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [selector, autoDismissMs, onDismiss])

  if (!visible || !rect) return null

  const padding = 8
  const r = {
    top: rect.top - padding,
    left: rect.left - padding,
    width: rect.width + padding * 2,
    height: rect.height + padding * 2,
  }

  // Tooltip position
  const tooltipStyle: React.CSSProperties = {
    position: "fixed",
    zIndex: 10002,
    maxWidth: 280,
  }

  if (position === "bottom") {
    tooltipStyle.top = r.top + r.height + 12
    tooltipStyle.left = r.left + r.width / 2
    tooltipStyle.transform = "translateX(-50%)"
  } else if (position === "top") {
    tooltipStyle.bottom = window.innerHeight - r.top + 12
    tooltipStyle.left = r.left + r.width / 2
    tooltipStyle.transform = "translateX(-50%)"
  } else if (position === "right") {
    tooltipStyle.top = r.top + r.height / 2
    tooltipStyle.left = r.left + r.width + 12
    tooltipStyle.transform = "translateY(-50%)"
  } else {
    tooltipStyle.top = r.top + r.height / 2
    tooltipStyle.right = window.innerWidth - r.left + 12
    tooltipStyle.transform = "translateY(-50%)"
  }

  const handleDismiss = () => {
    setVisible(false)
    onDismiss?.()
  }

  return (
    <>
      {/* Dark overlay with cutout */}
      <div
        className="fixed inset-0 z-[10000] transition-opacity duration-300"
        style={{
          background: "rgba(0,0,0,0.6)",
          clipPath: `polygon(
            0% 0%, 0% 100%, ${r.left}px 100%, ${r.left}px ${r.top}px,
            ${r.left + r.width}px ${r.top}px, ${r.left + r.width}px ${r.top + r.height}px,
            ${r.left}px ${r.top + r.height}px, ${r.left}px 100%, 100% 100%, 100% 0%
          )`,
        }}
        onClick={handleDismiss}
      />

      {/* Highlight border around element */}
      <div
        className="fixed z-[10001] border-2 border-wedo-cyan rounded-lg pointer-events-none animate-pulse"
        style={{
          top: r.top,
          left: r.left,
          width: r.width,
          height: r.height,
        }}
      />

      {/* Tooltip */}
      <div style={tooltipStyle}>
        <div className="bg-lia-bg-elevated border border-lia-border-subtle rounded-lg shadow-xl px-4 py-3 relative">
          <button
            onClick={handleDismiss}
            className="absolute top-2 right-2 p-0.5 text-lia-text-disabled hover:text-lia-text-secondary rounded"
          >
            <X className="w-3.5 h-3.5" />
          </button>
          <p className="text-sm text-lia-text-primary leading-relaxed pr-4">
            {message}
          </p>
        </div>
      </div>
    </>
  )
}
