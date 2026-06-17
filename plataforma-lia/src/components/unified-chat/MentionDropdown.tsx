"use client"

import React from "react"
import { Users, Briefcase } from "lucide-react"
import { cn } from "@/lib/utils"
import type { DropdownItem } from "./useInputDropdown"

interface Props {
  items: DropdownItem[]
  selectedIndex: number
  onSelect: (item: DropdownItem) => void
}

export function MentionDropdown({ items, selectedIndex, onSelect }: Props) {
  if (items.length === 0) return null

  // Group items by category
  const grouped = items.reduce<Record<string, DropdownItem[]>>((acc, item) => {
    const cat = item.category || "Outros"
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(item)
    return acc
  }, {})

  let flatIndex = 0

  return (
    <div className="absolute left-0 bottom-full mb-1 z-50 w-72 max-h-64 overflow-y-auto rounded-md border border-lia-border-subtle bg-lia-bg-primary py-1 shadow-lg">
      {Object.entries(grouped).map(([category, categoryItems]) => {
        const CategoryIcon = category === "Candidatos" ? Users : Briefcase
        return (
          <div key={category}>
            <div className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-lia-text-muted">
              <CategoryIcon className="w-3 h-3" />
              {category}
            </div>
            {categoryItems.map((item) => {
              const idx = flatIndex++
              const isSelected = idx === selectedIndex
              const Icon = item.icon
              return (
                <button
                  key={item.category + "-" + item.id}
                  type="button"
                  onMouseDown={(e) => {
                    e.preventDefault()
                    onSelect(item)
                  }}
                  className={cn(
                    "w-full flex items-center gap-2.5 px-3 py-2 text-sm",
                    isSelected
                      ? "bg-lia-interactive-active text-lia-text-primary"
                      : "text-lia-text-secondary hover:bg-lia-bg-secondary"
                  )}
                >
                  {Icon && <Icon className="w-4 h-4 flex-shrink-0" />}
                  <div className="flex flex-col items-start min-w-0">
                    <span className="truncate w-full text-left">{item.label}</span>
                    {item.subtitle && (
                      <span className="text-xs text-lia-text-muted truncate w-full text-left">
                        {item.subtitle}
                      </span>
                    )}
                  </div>
                </button>
              )
            })}
          </div>
        )
      })}
    </div>
  )
}
