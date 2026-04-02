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
      onClick={onClick}
      className={`flex items-center gap-2.5 p-2 rounded-md cursor-pointer transition-colors motion-reduce:transition-none hover:bg-lia-bg-secondary ${checked ? "bg-wedo-cyan/[0.08] border border-wedo-cyan/20" : "bg-transparent border border-transparent"}`}
    >
      <div
        className="w-4 h-4 rounded-md flex items-center justify-center flex-shrink-0 transition-colors motion-reduce:transition-none"
        style={{backgroundColor: checked ? "var(--lia-btn-primary-bg)" : "transparent",
          border: checked ? "none" : "2px solid var(--lia-border-default)"}}
      >
        {checked && <Check className="w-3 h-3 text-white" strokeWidth={3} />}
      </div>
      <span
        className="text-xs"
        style={{color: checked ? "var(--lia-text-primary)" : "var(--lia-text-secondary)"}}
      >
        {label}
      </span>
    </div>
  )
}
