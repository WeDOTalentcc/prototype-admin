"use client"

import React from "react"
import { cn } from "@/lib/utils"
import type { DropdownItem } from "./useInputDropdown"

interface Props {
  items: DropdownItem[]
  selectedIndex: number
  onSelect: (item: DropdownItem) => void
}

export function SlashCommandDropdown({ items, selectedIndex, onSelect }: Props) {
  if (items.length === 0) return null

  return (
    <div className="absolute left-0 bottom-full mb-1 z-50 w-72 max-h-64 overflow-y-auto rounded-xl border border-lia-border-subtle bg-lia-bg-primary py-1 shadow-lg">
      <div className="px-3 py-1.5 text-xs text-lia-text-disabled font-['Open_Sans',sans-serif]">
        Comandos
      </div>
      {items.map((item, idx) => {
        const isSelected = idx === selectedIndex
        const Icon = item.icon
        return (
          <button
            key={item.id}
            type="button"
            onMouseDown={(e) => {
              e.preventDefault()
              onSelect(item)
            }}
            className={cn(
              "w-full flex items-center gap-2.5 px-3 py-2 text-sm font-['Open_Sans',sans-serif]",
              isSelected
                ? "bg-lia-interactive-active text-lia-text-primary"
                : "text-lia-text-secondary hover:bg-lia-bg-secondary"
            )}
          >
            {Icon && <Icon className="w-4 h-4 flex-shrink-0 text-lia-text-disabled" />}
            <div className="flex flex-col items-start min-w-0">
              <span className="truncate w-full text-left">{item.label}</span>
              {item.subtitle && (
                <span className="text-xs text-lia-text-disabled truncate w-full text-left">
                  {item.subtitle}
                </span>
              )}
            </div>
          </button>
        )
      })}
    </div>
  )
}
