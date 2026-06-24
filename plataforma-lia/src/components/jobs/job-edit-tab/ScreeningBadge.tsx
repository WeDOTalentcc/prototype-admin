"use client"

import React from "react"
import { Filter } from "lucide-react"

export function ScreeningBadge() {
  return (
    <span
      className="inline-flex items-center gap-0.5 ml-1.5 group/screening relative"
      title="Usado na triagem automática"
    >
      <Filter className="w-3 h-3 text-wedo-cyan" />
      <span className="absolute left-1/2 -translate-x-1/2 bottom-full mb-1 px-2 py-1 text-micro text-white bg-lia-btn-primary-bg rounded-lg whitespace-nowrap opacity-0 group-hover/screening:opacity-100 transition-opacity pointer-events-none z-50">
        Usado na triagem automática
      </span>
    </span>
  )
}
