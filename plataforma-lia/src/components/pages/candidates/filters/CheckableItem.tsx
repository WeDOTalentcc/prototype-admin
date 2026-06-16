"use client"

import React from "react"
import { cn } from "@/lib/utils"
import { Check } from "lucide-react"

export interface CheckableItemProps {
  label: string
  checked: boolean
  onClick: () => void
}

export function CheckableItem({ label, checked, onClick }: CheckableItemProps) {
  return (
    <div
      data-testid={`checkable-item-${label.toLowerCase().replace(/\s+/g, '-')}`}
      onClick={onClick}
      className={`flex items-center gap-2.5 p-2 rounded-md cursor-pointer transition-colors motion-reduce:transition-none hover:bg-lia-bg-secondary ${checked ? "bg-wedo-cyan/[0.08] border border-wedo-cyan/20" : "bg-transparent border border-transparent"}`}
    >
      <div
        className={`w-4 h-4 rounded-md flex items-center justify-center flex-shrink-0 transition-colors motion-reduce:transition-none ${checked ? 'bg-lia-btn-primary-bg border-none' : 'bg-transparent border-2 border-lia-border-default'}`}
      >
        {checked && <Check className="w-3 h-3 text-white" strokeWidth={3} />}
      </div>
      <span
        className={`text-xs ${checked ? 'text-lia-text-primary' : 'text-lia-text-secondary'}`}
      >
        {label}
      </span>
    </div>
  )
}
