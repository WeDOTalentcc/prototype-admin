"use client"

import React from "react"

interface ProactiveChatMessageProps {
  title: string
  message: string
  actionLabel: string
  severity: string
  onAccept: () => void
  onReject: () => void
  processing?: boolean
}

export default function ProactiveChatMessage({
  title,
  message,
  actionLabel,
  severity,
  onAccept,
  onReject,
  processing = false,
}: ProactiveChatMessageProps) {
  const borderColor =
    severity === "urgent"
      ? "border-status-error/30"
      : severity === "warning"
      ? "border-status-warning/30"
      : "border-wedo-cyan"

  return (
    <div className={`rounded-md border-l-4 ${borderColor} bg-wedo-cyan/5 p-3 my-2`}>
      <div className="flex items-center gap-1.5 mb-1">
        <div className="w-1.5 h-1.5 rounded-full bg-wedo-cyan" />
        <span
          className="text-sm font-medium text-lia-text-tertiary"
         
        >
          {title}
        </span>
      </div>
      <p
        className="text-xs text-lia-text-secondary mb-2"
       
      >
        {message}
      </p>
      <div className="flex items-center gap-2">
        <button
          onClick={onAccept}
          disabled={processing}
          className="px-3 py-1 text-xs font-medium rounded-md bg-wedo-cyan/20 text-wedo-cyan-text hover:bg-wedo-cyan/30 transition-colors motion-reduce:transition-none disabled:opacity-50"
         
        >
          {processing ? "Processando..." : actionLabel}
        </button>
        <button
          onClick={onReject}
          disabled={processing}
          className="px-3 py-1 text-xs rounded-xl text-lia-text-secondary hover:text-lia-text-tertiary hover:bg-lia-bg-primary/5 transition-colors motion-reduce:transition-none disabled:opacity-50"
         
        >
          Ignorar
        </button>
      </div>
    </div>
  )
}
