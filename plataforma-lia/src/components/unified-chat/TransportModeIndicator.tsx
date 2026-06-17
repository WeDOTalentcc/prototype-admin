"use client"

import type { TransportMode } from "@/hooks/chat/lia-chat-connection-types"

interface Props {
  transportMode: TransportMode
  isReconnecting?: boolean
}

export function TransportModeIndicator({ transportMode, isReconnecting }: Props) {
  if (process.env.NODE_ENV === "production") return null

  const label =
    transportMode === "ws"
      ? "WS"
      : transportMode === "sse"
        ? "SSE"
        : "OFF"

  const color =
    transportMode === "ws"
      ? "bg-emerald-500"
      : transportMode === "sse"
        ? "bg-amber-500"
        : "bg-lia-text-disabled"

  return (
    <span
      className="inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-mono text-white opacity-60 hover:opacity-100 transition-opacity select-none"
      title={`Transport: ${transportMode.toUpperCase()}${isReconnecting ? " (reconnecting...)" : ""}`}
    >
      <span className={`inline-block h-1.5 w-1.5 rounded-full ${color} ${isReconnecting ? "animate-pulse" : ""}`} />
      {label}
    </span>
  )
}
