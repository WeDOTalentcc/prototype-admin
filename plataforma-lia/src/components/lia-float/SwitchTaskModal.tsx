"use client"

import React, { useState, useEffect, useRef, useCallback, useMemo } from "react"
import { Search, MessageSquare, Clock, ArrowRight, Command } from "lucide-react"
import { cn } from "@/lib/utils"
import { useUIPreferencesStore, type LiaRecentItem } from "@/stores/ui-preferences-store"

export interface SwitchTaskModalProps {
  isOpen: boolean
  onClose: () => void
  onSelectSession: (sessionId: string) => void
  currentSessionId?: string | null
}

export function SwitchTaskModal({
  isOpen,
  onClose,
  onSelectSession,
  currentSessionId,
}: SwitchTaskModalProps) {
  const [query, setQuery] = useState("")
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [activeSessions, setActiveSessions] = useState<Set<string>>(new Set())
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)

  const recentItems = useUIPreferencesStore((s) => s.liaRecentItems)

  useEffect(() => {
    if (!isOpen) return
    const fetchActive = async () => {
      try {
        const res = await fetch("/api/backend-proxy/agent-chat/sessions/active")
        if (res.ok) {
          const data = await res.json()
          const ids = (data.sessions || []).map((s: { id: string }) => s.id)
          setActiveSessions(new Set(ids))
        }
      } catch {}
    }
    fetchActive()
  }, [isOpen])

  const chatItems = useMemo(() => {
    const items = recentItems
      .filter((item) => item.type === "chat")
      .sort((a, b) => {
        const aActive = activeSessions.has(a.id) ? 1 : 0
        const bActive = activeSessions.has(b.id) ? 1 : 0
        if (bActive !== aActive) return bActive - aActive
        return b.timestamp - a.timestamp
      })
      .slice(0, 15)
    return items
  }, [recentItems, activeSessions])

  const filtered = useMemo(() => {
    if (!query.trim()) return chatItems
    const q = query.toLowerCase()
    return chatItems.filter((item) =>
      item.title.toLowerCase().includes(q) || item.id.toLowerCase().includes(q)
    )
  }, [chatItems, query])

  useEffect(() => {
    if (isOpen) {
      setQuery("")
      setSelectedIndex(0)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [isOpen])

  useEffect(() => {
    setSelectedIndex(0)
  }, [query])

  useEffect(() => {
    if (selectedIndex >= 0 && listRef.current) {
      const el = listRef.current.children[selectedIndex] as HTMLElement
      el?.scrollIntoView({ block: "nearest" })
    }
  }, [selectedIndex])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "ArrowDown") {
        e.preventDefault()
        setSelectedIndex((prev) => Math.min(prev + 1, filtered.length - 1))
      } else if (e.key === "ArrowUp") {
        e.preventDefault()
        setSelectedIndex((prev) => Math.max(prev - 1, 0))
      } else if (e.key === "Enter" && filtered[selectedIndex]) {
        e.preventDefault()
        onSelectSession(filtered[selectedIndex].id)
        onClose()
      } else if (e.key === "Escape") {
        e.preventDefault()
        onClose()
      }
    },
    [filtered, selectedIndex, onSelectSession, onClose]
  )

  const formatTime = useCallback((timestamp: number) => {
    const diff = Date.now() - timestamp
    const minutes = Math.floor(diff / 60000)
    if (minutes < 1) return "agora"
    if (minutes < 60) return `${minutes}min`
    const hours = Math.floor(minutes / 60)
    if (hours < 24) return `${hours}h`
    const days = Math.floor(hours / 24)
    return `${days}d`
  }, [])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-[60] flex items-start justify-center pt-[20vh]" onClick={onClose}>
      <div className="fixed inset-0 bg-black/40 backdrop-blur-sm" />
      <div
        className="relative w-full max-w-md bg-lia-bg-primary border border-lia-border-subtle rounded-xl shadow-lia-lg overflow-hidden animate-in fade-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-2 px-4 py-3">
          <Search className="w-4 h-4 text-lia-text-tertiary flex-shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Buscar conversas..."
            className="flex-1 bg-transparent text-sm text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none"
          />
          <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-lia-bg-tertiary border border-lia-border-subtle text-[10px] text-lia-text-muted font-mono">
            ESC
          </kbd>
        </div>

        <div ref={listRef} className="max-h-[300px] overflow-y-auto py-1">
          {filtered.length === 0 ? (
            <div className="px-4 py-8 text-center">
              <MessageSquare className="w-8 h-8 mx-auto text-lia-text-muted mb-2" />
              <p className="text-sm text-lia-text-tertiary">
                {query ? "Nenhuma conversa encontrada" : "Nenhuma conversa recente"}
              </p>
            </div>
          ) : (
            filtered.map((item, index) => {
              const isCurrent = item.id === currentSessionId
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    onSelectSession(item.id)
                    onClose()
                  }}
                  className={cn(
                    "w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors",
                    index === selectedIndex
                      ? "bg-lia-interactive-active"
                      : "hover:bg-lia-interactive-hover",
                    isCurrent && "opacity-50"
                  )}
                >
                  <div className="relative flex-shrink-0">
                    <MessageSquare className="w-4 h-4 text-lia-text-tertiary" />
                    {activeSessions.has(item.id) && (
                      <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-green-500" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-lia-text-primary truncate">
                      {item.title}
                    </p>
                    {item.lastMessage && (
                      <p className="text-xs text-lia-text-muted truncate mt-0.5 italic">
                        {item.lastMessage}
                      </p>
                    )}
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <Clock className="w-3 h-3 text-lia-text-muted" />
                      <span className="text-xs text-lia-text-muted">
                        {formatTime(item.timestamp)}
                      </span>
                      {activeSessions.has(item.id) && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-green-500/10 border border-green-500/30 text-green-400 ml-1">
                          ativa
                        </span>
                      )}
                      {item.mode && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-lia-bg-tertiary border border-lia-border-subtle text-lia-text-tertiary ml-1">
                          {item.mode}
                        </span>
                      )}
                      {isCurrent && (
                        <span className="text-xs text-lia-text-secondary font-medium ml-1">
                          atual
                        </span>
                      )}
                    </div>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-lia-text-muted flex-shrink-0" />
                </button>
              )
            })
          )}
        </div>

        <div className="px-4 py-2 border-t border-lia-border-subtle flex items-center justify-between">
          <div className="flex items-center gap-3 text-[10px] text-lia-text-muted">
            <span className="flex items-center gap-1">
              <kbd className="px-1 py-0.5 rounded bg-lia-bg-tertiary border border-lia-border-subtle font-mono">↑↓</kbd>
              navegar
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1 py-0.5 rounded bg-lia-bg-tertiary border border-lia-border-subtle font-mono">↵</kbd>
              selecionar
            </span>
          </div>
          <div className="flex items-center gap-1 text-[10px] text-lia-text-muted">
            <Command className="w-3 h-3" />
            <span>K</span>
          </div>
        </div>
      </div>
    </div>
  )
}
