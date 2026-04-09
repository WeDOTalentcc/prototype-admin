"use client"

import React, { useState, useRef, useEffect } from "react"
import {
  Brain, X, Maximize2, PanelRight, MessageSquare,
  Plus, MoreHorizontal, ChevronDown, Pencil, Trash2, ArrowRightLeft
} from "lucide-react"
import { cn } from "@/lib/utils"
import type { ChatMode } from "./unified-chat-types"

interface Props {
  mode: ChatMode
  onModeChange: (mode: ChatMode) => void
  onClose: () => void
  onNewChat: () => void
  onSwitchTask?: () => void
  conversationTitle?: string | null
  isConnected: boolean
  onRename?: (newTitle: string) => void
  onDelete?: () => void
}

const MODE_OPTIONS: { mode: ChatMode; icon: React.ElementType; label: string }[] = [
  { mode: "sidebar", icon: PanelRight, label: "Lateral" },
  { mode: "floating", icon: MessageSquare, label: "Flutuante" },
  { mode: "fullscreen", icon: Maximize2, label: "Tela cheia" },
]

export function UnifiedChatHeader({
  mode,
  onModeChange,
  onClose,
  onNewChat,
  onSwitchTask,
  conversationTitle,
  isConnected,
  onRename,
  onDelete,
}: Props) {
  const [showModeMenu, setShowModeMenu] = useState(false)
  const [showOptionsMenu, setShowOptionsMenu] = useState(false)
  const [isRenaming, setIsRenaming] = useState(false)
  const [renameValue, setRenameValue] = useState("")
  const renameInputRef = useRef<HTMLInputElement>(null)

  const title = conversationTitle || "Nova conversa"

  useEffect(() => {
    if (isRenaming && renameInputRef.current) {
      renameInputRef.current.focus()
      renameInputRef.current.select()
    }
  }, [isRenaming])

  const handleStartRename = () => {
    setRenameValue(title)
    setIsRenaming(true)
    setShowOptionsMenu(false)
  }

  const handleFinishRename = () => {
    const trimmed = renameValue.trim()
    if (trimmed && trimmed !== title && onRename) {
      onRename(trimmed)
    }
    setIsRenaming(false)
  }

  const handleRenameKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault()
      handleFinishRename()
    }
    if (e.key === "Escape") {
      setIsRenaming(false)
    }
  }

  const handleDelete = () => {
    setShowOptionsMenu(false)
    if (window.confirm("Tem certeza que deseja excluir esta conversa?")) {
      onDelete?.()
    }
  }

  const renderTitle = () => {
    if (isRenaming) {
      return (
        <input
          ref={renameInputRef}
          value={renameValue}
          onChange={(e) => setRenameValue(e.target.value)}
          onBlur={handleFinishRename}
          onKeyDown={handleRenameKeyDown}
          className="text-sm font-medium text-lia-text-primary bg-lia-bg-secondary border border-lia-border-subtle rounded px-1.5 py-0.5 max-w-[200px] outline-none focus:border-wedo-cyan font-['Open_Sans',sans-serif]"
          aria-label="Renomear conversa"
        />
      )
    }
    return null
  }

  return (
    <div className="flex items-center justify-between px-4 py-2.5 border-b border-lia-border-subtle flex-shrink-0 bg-lia-bg-primary">
      {/* Left: LIA branding + conversation title */}
      <div className="flex items-center gap-2 min-w-0">
        <Brain className="w-4 h-4 text-wedo-cyan flex-shrink-0" strokeWidth={2} />

        {mode === "fullscreen" ? (
          /* Fullscreen: breadcrumb style like Notion */
          <div className="flex items-center gap-1 min-w-0">
            <span className="text-sm text-lia-text-secondary font-['Open_Sans',sans-serif]">
              LIA
            </span>
            <span className="text-sm text-lia-text-disabled">/</span>
            {isRenaming ? (
              renderTitle()
            ) : (
              <button
                onClick={() => setShowOptionsMenu(!showOptionsMenu)}
                className="flex items-center gap-1 min-w-0 group"
              >
                <span className="text-sm text-lia-text-primary font-medium truncate max-w-[200px] font-['Open_Sans',sans-serif]">
                  {title}
                </span>
                <ChevronDown className="w-3 h-3 text-lia-text-disabled group-hover:text-lia-text-secondary flex-shrink-0" />
              </button>
            )}
          </div>
        ) : (
          /* Sidebar/Floating: compact title */
          isRenaming ? (
            renderTitle()
          ) : (
            <button
              onClick={() => setShowOptionsMenu(!showOptionsMenu)}
              className="flex items-center gap-1 min-w-0 group"
            >
              <span className="text-sm font-medium text-lia-text-primary truncate max-w-[160px] font-['Open_Sans',sans-serif]">
                {title}
              </span>
              <ChevronDown className="w-3 h-3 text-lia-text-disabled group-hover:text-lia-text-secondary flex-shrink-0" />
            </button>
          )
        )}

        {/* Connection indicator */}
        {isConnected && (
          <span className="w-1.5 h-1.5 rounded-full bg-status-success flex-shrink-0" title="Conectado" />
        )}
      </div>

      {/* Right: actions */}
      <div className="flex items-center gap-0.5">
        {/* New chat */}
        <button
          onClick={onNewChat}
          className="p-1.5 rounded-md text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
          title="Nova conversa"
          aria-label="Nova conversa"
        >
          <Plus className="w-4 h-4" />
        </button>

        {/* Switch Task */}
        {onSwitchTask && (
          <button
            onClick={onSwitchTask}
            className="p-1.5 rounded-md text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
            title="Trocar conversa (⌘K)"
            aria-label="Trocar conversa"
          >
            <ArrowRightLeft className="w-4 h-4" />
          </button>
        )}

        {/* Mode switcher */}
        <div className="relative">
          <button
            onClick={() => setShowModeMenu(!showModeMenu)}
            className="p-1.5 rounded-md text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
            title="Mudar modo de exibição"
            aria-label="Modo de exibição"
          >
            {mode === "sidebar" && <PanelRight className="w-4 h-4" />}
            {mode === "floating" && <MessageSquare className="w-4 h-4" />}
            {mode === "fullscreen" && <Maximize2 className="w-4 h-4" />}
          </button>

          {showModeMenu && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setShowModeMenu(false)} />
              <div className="absolute right-0 top-full mt-1 z-50 w-40 rounded-md border border-lia-border-subtle bg-lia-bg-primary py-1">
                {MODE_OPTIONS.map((opt) => (
                  <button
                    key={opt.mode}
                    onClick={() => {
                      onModeChange(opt.mode)
                      setShowModeMenu(false)
                    }}
                    className={cn(
                      "w-full flex items-center gap-2.5 px-3 py-2 text-sm font-['Open_Sans',sans-serif]",
                      "hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none",
                      mode === opt.mode
                        ? "text-lia-text-primary"
                        : "text-lia-text-secondary"
                    )}
                  >
                    <opt.icon className="w-4 h-4" />
                    <span>{opt.label}</span>
                    {mode === opt.mode && (
                      <span className="ml-auto text-wedo-cyan text-xs">✓</span>
                    )}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>

        {/* Close (sidebar/floating only) or minimize (fullscreen) */}
        {mode !== "fullscreen" && (
          <button
            onClick={onClose}
            className="p-1.5 rounded-md text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
            title="Fechar"
            aria-label="Fechar chat"
          >
            <X className="w-4 h-4" />
          </button>
        )}

        {/* Options menu (three dots) */}
        <div className="relative">
          <button
            onClick={() => setShowOptionsMenu(!showOptionsMenu)}
            className="p-1.5 rounded-md text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
            title="Opções"
            aria-label="Opções da conversa"
          >
            <MoreHorizontal className="w-4 h-4" />
          </button>

          {showOptionsMenu && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setShowOptionsMenu(false)} />
              <div className="absolute right-0 top-full mt-1 z-50 w-44 rounded-md border border-lia-border-subtle bg-lia-bg-primary py-1">
                <button
                  onClick={handleStartRename}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-lia-text-secondary hover:bg-lia-bg-secondary font-['Open_Sans',sans-serif]"
                >
                  <Pencil className="w-3.5 h-3.5" />
                  Renomear
                </button>
                <div className="my-1 border-t border-lia-border-subtle" />
                <button
                  onClick={handleDelete}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-status-error hover:bg-lia-bg-secondary font-['Open_Sans',sans-serif]"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  Excluir
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
