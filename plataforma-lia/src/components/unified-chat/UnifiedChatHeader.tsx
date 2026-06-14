"use client"

import React, { useState, useRef, useEffect } from "react"
import {
  Brain, X, Maximize2, PanelRight, MessageSquare, Minimize2,
  Plus, MoreHorizontal, ChevronDown, Pencil, Trash2, ArrowRightLeft,
  CheckCircle2, Briefcase, CornerDownRight
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useTranslations } from 'next-intl'
import type { ChatMode } from "./unified-chat-types"
import type { TransportMode } from "@/hooks/chat/lia-chat-connection-types"
import { TransportModeIndicator } from "./TransportModeIndicator"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { buttonVariants } from "@/components/ui/button"

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
  activeTaskLabel?: string | null
  /**
   * Auto-save hint shown next to the active-task pill while the wizard
   * is running (e.g. "Salvo agora", "Salvo há 2 min", "Salvando…"). The
   * UnifiedChat owner derives the label from the latest wizard_stage
   * payload — null hides the indicator.
   */
  autoSaveLabel?: string | null
  /**
   * When true, render a "Ver vaga" shortcut next to the active-task pill
   * so the recruiter can re-open the right-side panel after dismissing
   * it mid-wizard. The owner is responsible for deciding when there is a
   * panel to re-open.
   */
  showOpenJobButton?: boolean
  /** Fired when the user clicks the "Ver vaga" shortcut. */
  onOpenJob?: () => void
  /**
   * Task #1291 — when true (floating mode only, after the window has been
   * dragged away from its dock), render a discreet "back to corner" button
   * that returns the floating window to the bottom-right corner.
   */
  showResetFloatingButton?: boolean
  /** Fired when the user clicks the "back to corner" button. */
  onResetFloatingPosition?: () => void
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
  activeTaskLabel,
  autoSaveLabel,
  showOpenJobButton,
  onOpenJob,
  showResetFloatingButton,
  onResetFloatingPosition,
}: Props) {
  const t = useTranslations('chat.header')
  const [showModeMenu, setShowModeMenu] = useState(false)
  const [optionsAnchor, setOptionsAnchor] = useState<"title" | "more" | null>(null)
  const [isRenaming, setIsRenaming] = useState(false)
  const [renameValue, setRenameValue] = useState("")
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
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
    setOptionsAnchor(null)
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
    setOptionsAnchor(null)
    setShowDeleteDialog(true)
  }

  const handleConfirmDelete = async () => {
    if (!onDelete) {
      setShowDeleteDialog(false)
      return
    }
    try {
      setIsDeleting(true)
      await onDelete()
    } finally {
      setIsDeleting(false)
      setShowDeleteDialog(false)
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
          className="text-sm font-medium text-lia-text-primary bg-lia-bg-secondary border border-lia-border-subtle rounded px-1.5 py-0.5 max-w-[200px] outline-none focus:border-wedo-cyan"
          aria-label={t('renameLabel')}
        />
      )
    }
    return null
  }

  // Conversation options menu (rename + delete). Anchored to whichever
  // trigger opened it: the title button (left) or the kebab (right).
  // Single source of truth for the menu body so both triggers stay in sync.
  const renderConversationMenu = (align: "left" | "right") => (
    <>
      <div className="fixed inset-0 z-40" onClick={() => setOptionsAnchor(null)} />
      <div
        className={cn(
          "absolute top-full mt-1 z-50 w-44 rounded-md border border-lia-border-subtle bg-lia-bg-primary py-1",
          align === "left" ? "left-0" : "right-0",
        )}
      >
        {/* Floating mode (360px) — "Trocar conversa" is tucked into this menu
            instead of a dedicated header icon to declutter the cramped header.
            Sidebar/fullscreen keep the standalone icon. */}
        {mode === "floating" && onSwitchTask && (
          <>
            <button
              onClick={() => {
                onSwitchTask()
                setOptionsAnchor(null)
              }}
              className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-lia-text-secondary hover:bg-lia-bg-secondary"
            >
              <ArrowRightLeft className="w-3.5 h-3.5" />
              {t('switchChatLabel')}
            </button>
            <div className="my-1 border-t border-lia-border-subtle" />
          </>
        )}
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
  )

  // Conversation title acting as the menu trigger. The dropdown opens
  // anchored to the title (left), so it visually belongs to "LIA / <name>"
  // instead of floating to the opposite corner of the header.
  const renderTitleButton = (maxWidthClass: string) => (
    <div className="relative">
      <button
        onClick={() => setOptionsAnchor(optionsAnchor === "title" ? null : "title")}
        className="flex items-center gap-1 min-w-0 group"
      >
        <span className={cn("text-sm font-medium text-lia-text-primary truncate", maxWidthClass)}>
          {title}
        </span>
        <ChevronDown className="w-3 h-3 text-lia-text-disabled group-hover:text-lia-text-secondary flex-shrink-0" />
      </button>
      {optionsAnchor === "title" && renderConversationMenu("left")}
    </div>
  )

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
            {isRenaming ? renderTitle() : renderTitleButton("max-w-[200px]")}
          </div>
        ) : (
          isRenaming ? renderTitle() : renderTitleButton(mode === "floating" ? "max-w-[120px]" : "max-w-[160px]")
        )}

        {isConnected && (
          <span className="w-1.5 h-1.5 rounded-full bg-status-success flex-shrink-0" title={t('connected')} />
        )}
        {transportMode && mode !== "floating" && (
          <TransportModeIndicator transportMode={transportMode} isReconnecting={isReconnecting} />
        )}

        {/* Active task pill (Tezi Task Context Bar pattern) */}
        {activeTaskLabel && (
          <button
            onClick={onSwitchTask}
            className="flex items-center gap-1 px-2 py-0.5 rounded-md border border-lia-border-subtle bg-lia-bg-secondary text-lia-text-secondary hover:text-lia-text-primary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none flex-shrink-0 max-w-[200px]"
            title={`${activeTaskLabel} — trocar conversa (⌘K)`}
            aria-label={`Tarefa ativa: ${activeTaskLabel}. Clique para trocar`}
          >
            <span className="text-xs truncate">{activeTaskLabel}</span>
            <ArrowRightLeft className="w-3 h-3 flex-shrink-0 opacity-60" aria-hidden="true" />
          </button>
        )}

        {/* "Ver vaga" — re-open the right-side wizard panel after the
            recruiter dismissed it mid-wizard. Owner controls visibility
            (only shows when there's a panel to restore). */}
        {showOpenJobButton && onOpenJob && (
          <button
            onClick={onOpenJob}
            className="flex items-center gap-1 px-2 py-0.5 rounded-md border border-wedo-cyan/40 bg-wedo-cyan/10 text-wedo-cyan-text hover:bg-wedo-cyan/20 transition-colors motion-reduce:transition-none flex-shrink-0"
            title="Reabrir o painel da vaga em criação"
            aria-label="Reabrir o painel lateral da vaga em criação"
            data-testid="open-job-panel-button"
          >
            <Briefcase className="w-3 h-3" aria-hidden="true" />
            <span className="text-xs font-medium">Ver vaga</span>
          </button>
        )}

        {/* Auto-save hint — refreshed every minute by the owner. Hidden
            when no wizard is active or the timestamp is unknown. */}
        {autoSaveLabel && (
          <span
            className="hidden sm:flex items-center gap-1 text-[11px] text-lia-text-tertiary flex-shrink-0"
            aria-live="polite"
            aria-atomic="true"
            data-testid="wizard-autosave-indicator"
          >
            <CheckCircle2 className="w-3 h-3 text-status-success" aria-hidden="true" />
            <span className="truncate max-w-[120px]">{autoSaveLabel}</span>
          </span>
        )}
      </div>

      <div className={cn("flex items-center", mode === "floating" ? "gap-1" : "gap-0.5")}>
        <button
          onClick={onNewChat}
          className="p-1.5 rounded-md text-lia-border-strong hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
          title={t('newChat')}
          aria-label={t('newChat')}
        >
          <Plus className="w-4 h-4" />
        </button>

        {onSwitchTask && mode !== "floating" && (
          <button
            onClick={onSwitchTask}
            className="p-1.5 rounded-md text-lia-border-strong hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
            title={t('switchChat', { shortcut: '\u2318K' })}
            aria-label={t('switchChatLabel')}
          >
            <ArrowRightLeft className="w-4 h-4" />
          </button>
        )}

        {/* Task #1291 — "back to corner": only shown in floating mode once the
            window has been dragged away from its dock. Returns it to the
            bottom-right corner (its original position). */}
        {showResetFloatingButton && onResetFloatingPosition && (
          <button
            onClick={onResetFloatingPosition}
            className="p-1.5 rounded-md text-lia-border-strong hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
            title="Voltar ao canto"
            aria-label="Voltar a janela flutuante ao canto inferior direito"
            data-testid="floating-reset-button"
          >
            <CornerDownRight className="w-4 h-4" />
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
              <div className="absolute right-0 top-full mt-1 z-50 w-40 rounded-md border border-lia-border-subtle bg-lia-bg-primary py-1">
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
                      <span className="ml-auto text-wedo-cyan-text text-xs">{'\u2713'}</span>
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
            onClick={() => setOptionsAnchor(optionsAnchor === "more" ? null : "more")}
            className="p-1.5 rounded-md text-lia-border-strong hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
            title={t('options')}
            aria-label={t('optionsLabel')}
          >
            <MoreHorizontal className="w-4 h-4" />
          </button>

          {optionsAnchor === "more" && renderConversationMenu("right")}
        </div>
      </div>

      <AlertDialog
        open={showDeleteDialog}
        onOpenChange={(open) => {
          if (isDeleting) return
          setShowDeleteDialog(open)
        }}
      >
        <AlertDialogContent data-testid="delete-conversation-dialog">
          <AlertDialogHeader>
            <AlertDialogTitle>{t('deleteTitle')}</AlertDialogTitle>
            <AlertDialogDescription>
              {t('deleteDescription')}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>
              {t('deleteCancel')}
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={(e) => {
                e.preventDefault()
                void handleConfirmDelete()
              }}
              disabled={isDeleting}
              data-testid="delete-conversation-confirm"
              className={cn(buttonVariants({ variant: "destructive" }))}
            >
              {t('deleteAction')}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
