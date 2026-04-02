"use client"

import React from "react"

export interface TriStateButtonsProps {
  value: boolean | null
  onChange: (value: boolean | null) => void
}

export function TriStateButtons({ value, onChange }: TriStateButtonsProps) {
  const options = [
    { value: null, label: "Todos" },
    { value: true, label: "Sim" },
    { value: false, label: "Não" },
  ]
  return (
    <div className="flex gap-1.5">
      {options.map((opt) => (
        <button
          key={String(opt.value)}
          onClick={() => onChange(opt.value)}
          className="flex-1 px-2 py-1.5 text-micro rounded-md transition-colors motion-reduce:transition-none"
          style={{backgroundColor: value === opt.value ? "var(--lia-btn-primary-bg)" : "var(--lia-bg-secondary)",
            color: value === opt.value ? "white" : "var(--lia-text-secondary)",
            border: value === opt.value ? "none" : "1px solid var(--lia-border-subtle)"}}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}
