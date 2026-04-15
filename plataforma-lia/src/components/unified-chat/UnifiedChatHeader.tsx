"use client"

import React, { useState, useRef, useEffect } from "react"
import {
  Brain, X, Maximize2, PanelRight, MessageSquare, Minimize2,
  Plus, MoreHorizontal, ChevronDown, Pencil, Trash2, ArrowRightLeft
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useTranslations } from 'next-intl'
import type { ChatMode } from "./unified-chat-types"
import type { TransportMode } from "@/hooks/chat/lia-chat-connection-types"
import { TransportModeIndicator } from "./TransportModeIndicator"
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogFooter,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogAction,
  AlertDialogCancel,
} from "@/components/ui/alert-dialog"

interface Props {
  mode: ChatMode
  onModeChange: (mode: ChatMode) => void
  onClose: () => void
  onNewChat: () => void
  onSwitchTask?: () => void
  conversationTitle?: string | null
  isConnected: boolean
  transportMode?: TransportMode
  isReconnecting?: boolean
  onRename?: (newTitle: string) => void
  onDelete?: () => void
  hasMessages?: boolean
}

export function UnifiedChatHeader({
  mode,
  onModeChange,
  onClose,
  onNewChat,
  onSwitchTask,
  conversationTitle,
  isConnected,
  transportMode,
  isReconnecting,
  onRename,
  onDelete,
  hasMessages,
}: Props) {
  const t = useTranslations('chat.header')
  const [showModeMenu, setShowModeMenu] = useState(false)
  const [showOptionsMenu, setShowOptionsMenu] = useState(false)
  const [isRenaming, setIsRenaming] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [renameValue, setRenameValue] = useState("")
  const renameInputRef = useRef<HTMLInputElement>(null)

  const MODE_OPTIONS: { mode: ChatMode; icon: React.ElementType; label: string }[] = [
    { mode: "sidebar", icon: PanelRight, label: t('modeSidebar') },
    { mode: "floating", icon: MessageSquare, label: t('modeFloating') },
    { mode: "fullscreen", icon: Maximize2, label: t('modeFullscreen') },
    { mode: "minimized", icon: Minimize2, label: t('modeMinimize') },
  ]

  const title = conversationTitle || t('newConversation')

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
    setShowDeleteDialog(true)
  }

  const handleConfirmDelete = () => {
    setShowDeleteDialog(false)
    onDelete?.()
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
          className="text-sm font-medium text-lia-text-primary bg-lia-bg-secondary border border-lia-border-subtle rounded px-1.5 py-0.5 max-w-[200px] outline-none focus:border-wedo-cyan"
          aria-label={t('renameLabel')}
        />
      )
    }
    return null
  }

  return (
    <div className="flex items-center justify-between px-4 py-2.5 flex-shrink-0 bg-lia-bg-primary">
      <div className="flex items-center gap-2 min-w-0">
        <Brain className="w-4 h-4 text-wedo-cyan flex-shrink-0" strokeWidth={2} />

        {mode === "fullscreen" ? (
          <div className="flex items-center gap-1 min-w-0">
            <span className="text-sm text-lia-text-secondary">
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
                <span className="text-sm text-lia-text-primary font-medium truncate max-w-[200px]">
                  {title}
                </span>
                <ChevronDown className="w-3 h-3 text-lia-text-disabled group-hover:text-lia-text-secondary flex-shrink-0" />
              </button>
            )}
          </div>
        ) : (
          isRenaming ? (
            renderTitle()
          ) : (
            <button
              onClick={() => setShowOptionsMenu(!showOptionsMenu)}
              className="flex items-center gap-1 min-w-0 group"
            >
              <span className="text-sm font-medium text-lia-text-primary truncate max-w-[160px]">
                {title}
              </span>
              <ChevronDown className="w-3 h-3 text-lia-text-disabled group-hover:text-lia-text-secondary flex-shrink-0" />
            </button>
          )
        )}

        {isConnected && (
          <span className="w-1.5 h-1.5 rounded-full bg-status-success flex-shrink-0" title={t('connected')} />
        )}
        {transportMode && (
          <TransportModeIndicator transportMode={transportMode} isReconnecting={isReconnecting} />
        )}
      </div>

      <div className="flex items-center gap-0.5">
        <button
          onClick={onNewChat}
          className="p-1.5 rounded-md text-lia-border-strong hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
          title={t('newChat')}
          aria-label={t('newChat')}
        >
          <Plus className="w-4 h-4" />
        </button>

        {onSwitchTask && (
          <button
            onClick={onSwitchTask}
            className="p-1.5 rounded-md text-lia-border-strong hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
            title={t('switchChat', { shortcut: '\u2318K' })}
            aria-label={t('switchChatLabel')}
          >
            <ArrowRightLeft className="w-4 h-4" />
          </button>
        )}

        <div className="relative">
          <button
            onClick={() => setShowModeMenu(!showModeMenu)}
            className="p-1.5 rounded-md text-lia-border-strong hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
            title={t('displayMode')}
            aria-label={t('displayModeLabel')}
          >
            {mode === "sidebar" && <PanelRight className="w-4 h-4" />}
            {mode === "floating" && <MessageSquare className="w-4 h-4" />}
            {mode === "fullscreen" && <Maximize2 className="w-4 h-4" />}
          </button>

          {showModeMenu && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setShowModeMenu(false)} />
              <div className="absolute right-0 top-full mt-1 z-50 w-40 rounded-xl border border-lia-border-subtle bg-lia-bg-primary py-1">
                {MODE_OPTIONS.map((opt) => (
                  <button
                    key={opt.mode}
                    onClick={() => {
                      onModeChange(opt.mode)
                      setShowModeMenu(false)
                    }}
                    className={cn(
                      "w-full flex items-center gap-2.5 px-3 py-2 text-sm",
                      "hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none",
                      mode === opt.mode
                        ? "text-lia-text-primary"
                        : "text-lia-text-secondary"
                    )}
                  >
                    <opt.icon className="w-4 h-4" />
                    <span>{opt.label}</span>
                    {mode === opt.mode && (
                      <span className="ml-auto text-wedo-cyan text-xs">{'\u2713'}</span>
                    )}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>

        {mode !== "fullscreen" && (
          <button
            onClick={onClose}
            className="p-1.5 rounded-md text-lia-border-strong hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
            title={t('close')}
            aria-label={t('closeChat')}
          >
            <X className="w-4 h-4" />
          </button>
        )}

        <div className="relative">
          <button
            onClick={() => setShowOptionsMenu(!showOptionsMenu)}
            className="p-1.5 rounded-md text-lia-border-strong hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
            title={t('options')}
            aria-label={t('optionsLabel')}
          >
            <MoreHorizontal className="w-4 h-4" />
          </button>

          {showOptionsMenu && hasMessages && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setShowOptionsMenu(false)} />
              <div className="absolute right-0 top-full mt-1 z-50 w-44 rounded-xl border border-lia-border-subtle bg-lia-bg-primary py-1">
                <button
                  onClick={handleStartRename}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-lia-text-secondary hover:bg-lia-bg-secondary"
                >
                  <Pencil className="w-3.5 h-3.5" />
                  {t('rename')}
                </button>
                <div className="my-1 border-t border-lia-border-subtle" />
                <button
                  onClick={handleDelete}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-status-error hover:bg-lia-bg-secondary"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  {t('delete')}
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent className="sm:max-w-[420px] bg-lia-bg-primary rounded-xl dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-sm font-semibold">
              {t('deleteTitle')}
            </AlertDialogTitle>
            <AlertDialogDescription className="text-sm text-lia-text-secondary">
              {t('deleteDescription')}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="text-xs h-8">
              {t('deleteCancel')}
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDelete}
              className="bg-status-error hover:bg-status-error/90 text-white text-xs h-8"
            >
              {t('deleteAction')}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
