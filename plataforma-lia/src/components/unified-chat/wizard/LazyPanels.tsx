"use client"

/**
 * LazyPanels — DEPRECATED.
 *
 * DynamicContextPanel now handles lazy loading internally.
 * This module re-exports PanelLoader for backward compatibility.
 */

import React from "react"

export function PanelLoader() {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="w-5 h-5 border-2 border-wedo-cyan border-t-transparent rounded-full animate-spin" />
    </div>
  )
}
