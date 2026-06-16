"use client"

import React from "react"
import { cn } from "@/lib/utils"
import type { DropdownItem } from "./useInputDropdown"

interface Props {
  items: DropdownItem[]
  selectedIndex: number
  onSelect: (item: DropdownItem) => void
}

/**
 * Slash-command dropdown — Claude-Code-style single-line list.
 *
 * Each row is a two-column row: command token on the left (medium weight,
 * primary color) and description on the right (secondary color, ellipsis
 * on overflow). No icons, no two-line layout — the goal is a dense,
 * scannable command palette that follows the lia-* design tokens.
 *
 * The `label` field carries the canonical command token (e.g. `/criar
 * vaga`). `useSlashCommands` maps `SlashCommand.primary` → `label`
 * specifically for this surface.
 */
export function SlashCommandDropdown({ items, selectedIndex, onSelect }: Props) {
  if (items.length === 0) return null

  return (
    <div
      className={cn(
        "absolute left-0 bottom-full mb-1 z-50",
        "w-[460px] max-w-[calc(100vw-2rem)] max-h-72 overflow-y-auto",
        "rounded-md border border-lia-border-subtle bg-lia-bg-primary py-1 shadow-lg",
      )}
      role="listbox"
      aria-label="Comandos disponiveis"
    >
      <div
        className={cn(
          "px-2.5 py-1 text-[10px] font-medium uppercase tracking-wide",
          "text-lia-text-tertiary",
        )}
      >
        Comandos
      </div>
      {items.map((item, idx) => {
        const isSelected = idx === selectedIndex
        return (
          <button
            key={item.id}
            type="button"
            role="option"
            aria-selected={isSelected}
            onMouseDown={(e) => {
              e.preventDefault()
              onSelect(item)
            }}
            className={cn(
              "w-full flex items-baseline gap-3 px-2.5 py-1 text-[13px] leading-5",
              "transition-colors motion-reduce:transition-none text-left",
              isSelected
                ? "bg-lia-interactive-active"
                : "hover:bg-lia-bg-secondary",
            )}
          >
            <span
              className={cn(
                "font-medium text-lia-text-primary whitespace-nowrap shrink-0",
              )}
            >
              {item.label}
            </span>
            {item.subtitle && (
              <span className="text-lia-text-secondary truncate">
                {item.subtitle}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}
