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
      ? "border-red-500"
      : severity === "warning"
      ? "border-amber-500"
      : "border-wedo-cyan"

  return (
    <div className={`rounded-md border-l-4 ${borderColor} bg-wedo-cyan/5 p-3 my-2`}>
      <div className="flex items-center gap-1.5 mb-1">
        <div className="w-1.5 h-1.5 rounded-full bg-wedo-cyan" />
        <span
          className="text-sm font-medium text-gray-200"
          style={{ fontFamily: "Open Sans, sans-serif" }}
        >
          {title}
        </span>
      </div>
      <p
        className="text-xs text-gray-400 mb-2"
        style={{ fontFamily: "Open Sans, sans-serif" }}
      >
        {message}
      </p>
      <div className="flex items-center gap-2">
        <button
          onClick={onAccept}
          disabled={processing}
          className="px-3 py-1 text-xs font-medium rounded bg-wedo-cyan/20 text-wedo-cyan hover:bg-wedo-cyan/30 transition-colors disabled:opacity-50"
          style={{ fontFamily: "Open Sans, sans-serif" }}
        >
          {processing ? "Processando..." : actionLabel}
        </button>
        <button
          onClick={onReject}
          disabled={processing}
          className="px-3 py-1 text-xs rounded text-gray-500 hover:text-gray-300 hover:bg-white/5 transition-colors disabled:opacity-50"
          style={{ fontFamily: "Open Sans, sans-serif" }}
        >
          Ignorar
        </button>
      </div>
    </div>
  )
}
