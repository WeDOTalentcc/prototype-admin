"use client"

import React from "react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { cardStyles } from "@/lib/design-tokens"
import { TOOL_KEYS } from "./types"
const ALL_TOOLS = TOOL_KEYS

interface ToolSelectorProps {
  selectedTools: string[]
  onChange: (tools: string[]) => void
  label?: string
}

export function ToolSelector({ selectedTools, onChange, label }: ToolSelectorProps) {
  const t = useTranslations('agents.customAgents')
  const toggle = (tool: string) => {
    onChange(
      selectedTools.includes(tool)
        ? selectedTools.filter((t) => t !== tool)
        : [...selectedTools, tool]
    )
  }

  return (
    <div>
      <label className="text-xs font-semibold text-lia-text-primary mb-2 block">
        {label || t('toolsLabel')}
        <span className="font-normal text-lia-text-disabled ml-1">
          ({selectedTools.length}/{ALL_TOOLS.length})
        </span>
      </label>
      <div className={cn(cardStyles.flat, "p-3 grid grid-cols-2 gap-1.5 max-h-48 overflow-auto")}>
        {ALL_TOOLS.map((tool) => {
          const checked = selectedTools.includes(tool)
          return (
            <label
              key={tool}
              className={cn(
                "flex items-center gap-2 px-2 py-1.5 rounded-md text-xs cursor-pointer transition-colors",
                checked
                  ? "bg-powder text-graphite"
                  : "text-lia-text-secondary hover:bg-lia-bg-tertiary"
              )}
            >
              <input
                type="checkbox"
                checked={checked}
                onChange={() => toggle(tool)}
                className="w-3.5 h-3.5 rounded border-lia-border-default text-graphite focus:ring-lia-btn-primary-bg/30"
              />
              {t('tools.' + tool) || tool}
            </label>
          )
        })}
      </div>
    </div>
  )
}
