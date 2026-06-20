"use client"

import React from "react"
import { useState, useMemo, useCallback, useEffect, useLayoutEffect, useRef } from "react"
import { useTranslations } from "next-intl"
import {
  Brain, Plus, Pin, PinOff, Edit3, StickyNote, Archive, Trash2,
  X, Search, MessageSquare, MoreHorizontal, ChevronsLeft,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { useIASessionStore } from "@/stores/ia-session-store"
import { useUIPreferencesStore, type LiaRecentItem } from "@/stores/ui-preferences-store"
import { useLiaFloat } from "@/contexts/lia-float-context"
import {
  useIASessions,
  useUpdateSession,
  useMarkSessionRead,
  useDeleteSession,
  useArchiveSession,
  type IASession,
} from "@/hooks/ia-sessions/useIASessions"

// ---------------------------------------------------------------------------
// Domain tag chip
// ---------------------------------------------------------------------------
const DOMAIN_TAG_COLORS: Record<string, string> = {
  Vagas: "bg-blue-500/15 text-blue-600 dark:text-blue-400",
  Candidatos: "bg-purple-500/15 text-purple-600 dark:text-purple-400",
  "Relatórios": "bg-amber-500/15 text-amber-600 dark:text-amber-400",
  "Configurações": "bg-slate-500/15 text-slate-600 dark:text-slate-400",
  Geral: "bg-lia-bg-tertiary text-lia-text-muted",
}

function DomainTagChip({ tag }: { tag: string }) {
  const color = DOMAIN_TAG_COLORS[tag] ?? DOMAIN_TAG_COLORS["Geral"]
  return (
    <span className={cn("text-[10px] font-medium px-1.5 py-0.5 rounded-full", color)}>
      {tag}
    </span>
  )
}

// ---------------------------------------------------------------------------
// Note callout (D7: persistent until note deleted)
// ---------------------------------------------------------------------------
function NoteCallout({
  note,
  onEdit,
}: {
  note: string
  onEdit: () => void
}) {
  return (
    <button
      onClick={onEdit}
      className="w-full text-left flex items-start gap-2 rounded-md bg-amber-500/10 border border-amber-500/20 px-3 py-2 mx-3 mb-2 hover:bg-amber-500/15 transition-colors"
      style={{ width: "calc(100% - 1.5rem)" }}
    >
      <StickyNote className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
      <span className="text-xs text-amber-700 dark:text-amber-300 line-clamp-2 flex-1">
        {note}
      </span>
    </button>
  )
}

// ---------------------------------------------------------------------------
// Context menu (inline — no portal, position:fixed escapes overflow containers)
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Session item
// ---------------------------------------------------------------------------
interface SessionItemProps {
  session: IASession
  isActive: boolean
  localUnread: number
  onOpen: (id: string) => void
  onUpdate: (payload: { id: string; title?: string | null; is_pinned?: boolean | null; note?: string | null }) => void
  onArchive: (id: string) => void
  onDelete: (id: string) => void
}

function SessionItem({
  session,
  isActive,
  localUnread,
  onOpen,
  onUpdate,
  onArchive,
  onDelete,
}: SessionItemProps) {
  const t = useTranslations("iaSidebar")
  const [menuOpen, setMenuOpen] = useState(false)
  const [renaming, setRenaming] = useState(false)
  const [renameValue, setRenameValue] = useState(session.title ?? "")
  const [addingNote, setAddingNote] = useState(false)
  const [noteValue, setNoteValue] = useState(session.note ?? "")
  const menuButtonRef = useRef<HTMLButtonElement>(null)
  const menuRef = useRef<HTMLDivElement>(null)
  const [menuPos, setMenuPos] = useState({ top: 0, right: 0 })

  // Compute fixed position from trigger button when menu opens
  useLayoutEffect(() => {
    if (menuOpen && menuButtonRef.current) {
      const rect = menuButtonRef.current.getBoundingClientRect()
      setMenuPos({ top: rect.bottom + 4, right: window.innerWidth - rect.right })
    }
  }, [menuOpen])

  useEffect(() => {
    if (!menuOpen) return
    const handler = (e: MouseEvent) => {
      const t = e.target as Node
      if (!menuButtonRef.current?.contains(t) && !menuRef.current?.contains(t)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [menuOpen])

  const totalUnread = (session.unread_count ?? 0) + localUnread

  const handleRenameSubmit = useCallback(() => {
    if (renameValue.trim() && renameValue.trim() !== session.title) {
      onUpdate({ id: session.id, title: renameValue.trim() })
    }
    setRenaming(false)
  }, [renameValue, session.id, session.title, onUpdate])

  const handleNoteSubmit = useCallback(() => {
    onUpdate({ id: session.id, note: noteValue.trim() || null })
    setAddingNote(false)
  }, [noteValue, session.id, onUpdate])

  const displayTitle =
    session.title ||
    (session.created_at
      ? new Date(session.created_at).toLocaleDateString("pt-BR", { day: "numeric", month: "short" })
      : t("fallbackTitle"))

  return (
    <div className="relative group">
      {renaming ? (
        <div className="px-2 py-1.5">
          <input
            autoFocus
            value={renameValue}
            onChange={(e) => setRenameValue(e.target.value)}
            onBlur={handleRenameSubmit}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleRenameSubmit()
              if (e.key === "Escape") setRenaming(false)
            }}
            className="w-full text-xs px-2 py-1 rounded border border-lia-border-medium bg-lia-bg-primary text-lia-text-primary focus:outline-none focus:ring-1 focus:ring-wedo-cyan"
          />
        </div>
      ) : addingNote ? (
        <div className="px-2 py-1.5">
          <textarea
            autoFocus
            value={noteValue}
            onChange={(e) => setNoteValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleNoteSubmit()
              if (e.key === "Escape") setAddingNote(false)
            }}
            placeholder={t("note.placeholder")}
            rows={3}
            maxLength={500}
            className="w-full text-xs px-2 py-1 rounded border border-lia-border-medium bg-lia-bg-primary text-lia-text-primary focus:outline-none focus:ring-1 focus:ring-wedo-cyan resize-none"
          />
          <div className="flex justify-end gap-1 mt-1">
            <button onClick={() => setAddingNote(false)} className="text-[10px] text-lia-text-muted px-2 py-0.5 hover:text-lia-text-secondary">{t("note.cancel")}</button>
            <button onClick={handleNoteSubmit} className="text-[10px] text-wedo-cyan px-2 py-0.5 font-medium hover:text-wedo-cyan/80">{t("note.save")}</button>
          </div>
        </div>
      ) : (
        <button
          onClick={() => onOpen(session.id)}
          className={cn(
            "w-full flex flex-col gap-0.5 px-2 py-1.5 rounded-md text-left transition-colors",
            isActive
              ? "bg-wedo-cyan/10 text-lia-text-primary"
              : "hover:bg-lia-interactive-hover text-lia-text-secondary"
          )}
        >
          <div className="flex items-center gap-1 min-w-0">
            <span className="text-xs font-medium truncate flex-1">{displayTitle}</span>
            {totalUnread > 0 && (
              <span className="flex-shrink-0 text-[10px] font-semibold bg-wedo-cyan text-white rounded-full w-4 h-4 flex items-center justify-center">
                {totalUnread > 9 ? "9+" : totalUnread}
              </span>
            )}
            {session.is_pinned && !totalUnread && (
              <Pin className="w-2.5 h-2.5 flex-shrink-0 text-lia-text-muted" />
            )}
          </div>
          {session.domain_tag && (
            <div className="flex items-center gap-1.5 min-w-0">
              <DomainTagChip tag={session.domain_tag} />
            </div>
          )}
        </button>
      )}

      {/* "..." hover menu trigger — visible on hover OR when menu is open */}
      {!renaming && !addingNote && (
        <div className={cn(
          "absolute right-1 top-1/2 -translate-y-1/2",
          menuOpen ? "opacity-100" : "opacity-0 group-hover:opacity-100 focus-within:opacity-100"
        )}>
          <button
            ref={menuButtonRef}
            onClick={(e) => { e.stopPropagation(); setMenuOpen((v) => !v) }}
            className="p-1 rounded hover:bg-lia-bg-elevated text-lia-text-muted hover:text-lia-text-secondary"
            aria-label={t("aria.sessionOptions")}
          >
            <MoreHorizontal className="w-3 h-3" />
          </button>
        </div>
      )}

      {/* Context menu — inline with position:fixed (escapes overflow:auto, no nested portal) */}
      {menuOpen && !renaming && !addingNote && (
        <div
          ref={menuRef}
          style={{ position: "fixed", top: menuPos.top, right: menuPos.right, zIndex: 9999 }}
          className="bg-lia-bg-primary border border-lia-border-subtle rounded-lg shadow-lg py-1 min-w-[160px]"
          onMouseDown={(e) => e.stopPropagation()}
          onClick={(e) => e.stopPropagation()}
        >
          <button
            className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-lia-text-secondary hover:bg-lia-interactive-hover"
            onMouseDown={(e) => e.stopPropagation()}
            onClick={(e) => {
              e.stopPropagation()
              onUpdate({ id: session.id, is_pinned: !session.is_pinned })
              setMenuOpen(false)
            }}
          >
            {session.is_pinned ? (
              <><PinOff className="w-3.5 h-3.5" /> {t("context.unpin")} <kbd className="ml-auto text-[10px] text-lia-text-muted">P</kbd></>
            ) : (
              <><Pin className="w-3.5 h-3.5" /> {t("context.pin")} <kbd className="ml-auto text-[10px] text-lia-text-muted">P</kbd></>
            )}
          </button>
          <button
            className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-lia-text-secondary hover:bg-lia-interactive-hover"
            onMouseDown={(e) => e.stopPropagation()}
            onClick={(e) => {
              e.stopPropagation()
              setRenameValue(session.title ?? "")
              setRenaming(true)
              setMenuOpen(false)
            }}
          >
            <Edit3 className="w-3.5 h-3.5" /> {t("context.rename")} <kbd className="ml-auto text-[10px] text-lia-text-muted">R</kbd>
          </button>
          <button
            className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-lia-text-secondary hover:bg-lia-interactive-hover"
            onMouseDown={(e) => e.stopPropagation()}
            onClick={(e) => {
              e.stopPropagation()
              setNoteValue(session.note ?? "")
              setAddingNote(true)
              setMenuOpen(false)
            }}
          >
            <StickyNote className="w-3.5 h-3.5" /> {t("context.note")} <kbd className="ml-auto text-[10px] text-lia-text-muted">N</kbd>
          </button>
          <div className="my-1 border-t border-lia-border-subtle" />
          <button
            className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-lia-text-secondary hover:bg-lia-interactive-hover"
            onMouseDown={(e) => e.stopPropagation()}
            onClick={(e) => {
              e.stopPropagation()
              onArchive(session.id)
              setMenuOpen(false)
            }}
          >
            <Archive className="w-3.5 h-3.5" /> {t("context.archive")} <kbd className="ml-auto text-[10px] text-lia-text-muted">A</kbd>
          </button>
          <button
            className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-status-error hover:bg-status-error/10"
            onMouseDown={(e) => e.stopPropagation()}
            onClick={(e) => {
              e.stopPropagation()
              onDelete(session.id)
              setMenuOpen(false)
            }}
          >
            <Trash2 className="w-3.5 h-3.5" /> {t("context.delete")} <kbd className="ml-auto text-[10px] text-lia-text-muted">Del</kbd>
          </button>
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Section header
// ---------------------------------------------------------------------------
function SectionHeader({ label }: { label: string }) {
  return (
    <div className="px-3 pt-3 pb-1">
      <span className="text-[10px] font-semibold text-lia-text-tertiary tracking-[0.15em] uppercase opacity-70">
        {label}
      </span>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main IASidebar component
// ---------------------------------------------------------------------------
function localItemToSession(item: LiaRecentItem): IASession {
  return {
    id: item.id,
    user_id: "",
    context_type: "chat_bubble",
    context_id: null,
    title: item.title || "Conversa",
    summary: item.lastMessage ?? null,
    intent: null,
    status: "active",
    is_active: true,
    is_pinned: false,
    domain_tag: null,
    note: null,
    unread_count: 0,
    message_count: 0,
    created_at: new Date(item.timestamp).toISOString(),
    updated_at: new Date(item.timestamp).toISOString(),
  }
}

function isToday(dateStr: string | null): boolean {
  if (!dateStr) return false
  const d = new Date(dateStr)
  const now = new Date()
  return d.toDateString() === now.toDateString()
}

function isYesterday(dateStr: string | null): boolean {
  if (!dateStr) return false
  const d = new Date(dateStr)
  const yesterday = new Date()
  yesterday.setDate(yesterday.getDate() - 1)
  return d.toDateString() === yesterday.toDateString()
}

interface IASidebarProps {
  onOpenConversation?: (id: string) => void
  onNewConversation?: () => void
  activeNoteConversationId?: string | null
  sidebarOffset?: number  // pixel width of left sidebar (Apollo-style positioning)
}

export function IASidebar({ onOpenConversation, onNewConversation, activeNoteConversationId, sidebarOffset = 64 }: IASidebarProps) {
  const t = useTranslations("iaSidebar")
  const { isIASidebarOpen, closeIASidebar, activeConversationId, setActiveConversation, localUnreadCounts } =
    useIASessionStore()
  const { open: openLiaChat, switchChatContext, loadChatHistory, chatContextType, setChatMessages } = useLiaFloat()
  const [searchQuery, setSearchQuery] = useState("")
  const [panelWidth, setPanelWidth] = useState(340)
  const isDraggingRef = useRef(false)
  const resizeStartRef = useRef({ x: 0, width: 0 })

  // Resize drag handler
  const handleResizeStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    isDraggingRef.current = true
    resizeStartRef.current = { x: e.clientX, width: panelWidth }
    document.body.style.cursor = "col-resize"
    document.body.style.userSelect = "none"
  }, [panelWidth])

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (!isDraggingRef.current) return
      const delta = e.clientX - resizeStartRef.current.x
      const next = Math.min(600, Math.max(280, resizeStartRef.current.width + delta))
      setPanelWidth(next)
    }
    const onUp = () => {
      if (!isDraggingRef.current) return
      isDraggingRef.current = false
      document.body.style.cursor = ""
      document.body.style.userSelect = ""
    }
    document.addEventListener("mousemove", onMove)
    document.addEventListener("mouseup", onUp)
    return () => {
      document.removeEventListener("mousemove", onMove)
      document.removeEventListener("mouseup", onUp)
    }
  }, [])
  const { data: sessions = [], isLoading } = useIASessions()
  const liaRecentItems = useUIPreferencesStore((s) => s.liaRecentItems)
  // Fallback: when backend returns empty (user_id mismatch between accounts),
  // show localStorage recent items so history is never blank to the user.
  const localChatItems = liaRecentItems.filter((i) => i.type === "chat")
  const effectiveSessions: IASession[] = sessions.length > 0
    ? sessions
    : (!isLoading && localChatItems.length > 0 ? localChatItems.map(localItemToSession) : sessions)
  const updateSession = useUpdateSession()
  const markRead = useMarkSessionRead()
  const deleteSession = useDeleteSession()
  const archiveSession = useArchiveSession()

  const handleOpen = useCallback(
    (id: string) => {
      setActiveConversation(id)
      markRead.mutate(id)
      // Clear existing messages and load the selected conversation
      setChatMessages([])
      switchChatContext(chatContextType, { conversationId: id })
      void loadChatHistory(id)
      openLiaChat(id)
      onOpenConversation?.(id)
      closeIASidebar()
    },
    [setActiveConversation, markRead, openLiaChat, switchChatContext, loadChatHistory, chatContextType, setChatMessages, closeIASidebar, onOpenConversation]
  )

  // Keyboard shortcuts: P=pin, N=new, A=archive, Del=delete, Esc=close
  // Scoped to sidebar open + focus NOT in a text field
  useEffect(() => {
    if (!isIASidebarOpen) return
    const handler = (e: KeyboardEvent) => {
      const el = e.target as HTMLElement
      if (el.tagName === "INPUT" || el.tagName === "TEXTAREA" || el.isContentEditable) return
      const target = effectiveSessions.find((s) => s.id === activeConversationId)
      switch (e.key) {
        case "n":
        case "N":
          e.preventDefault()
          onNewConversation?.()
          closeIASidebar()
          break
        case "p":
        case "P":
          if (!target) return
          e.preventDefault()
          updateSession.mutate({ id: target.id, is_pinned: !target.is_pinned })
          break
        case "a":
        case "A":
          if (!target) return
          e.preventDefault()
          archiveSession.mutate(target.id)
          break
        case "Delete":
          if (!target) return
          e.preventDefault()
          if (window.confirm(`Excluir conversa "${target.title ?? "sem título"}"?`)) {
            deleteSession.mutate(target.id)
          }
          break
        case "Escape":
          e.preventDefault()
          closeIASidebar()
          break
      }
    }
    document.addEventListener("keydown", handler)
    return () => document.removeEventListener("keydown", handler)
  }, [isIASidebarOpen, activeConversationId, sessions, updateSession, archiveSession, deleteSession, closeIASidebar, onNewConversation])

  // Client-side search filter
  const filteredSessions = useMemo(() => {
    if (!searchQuery.trim()) return effectiveSessions
    const q = searchQuery.toLowerCase()
    return effectiveSessions.filter(
      (s) =>
        (s.title ?? "").toLowerCase().includes(q) ||
        (s.domain_tag ?? "").toLowerCase().includes(q)
    )
  }, [effectiveSessions, searchQuery])

  const pinned = filteredSessions.filter((s) => s.is_pinned)
  const todaySessions = filteredSessions.filter((s) => !s.is_pinned && isToday(s.updated_at))
  const yesterdaySessions = filteredSessions.filter((s) => !s.is_pinned && isYesterday(s.updated_at))
  const olderSessions = filteredSessions.filter(
    (s) => !s.is_pinned && !isToday(s.updated_at) && !isYesterday(s.updated_at)
  )

  const activeSession = effectiveSessions.find((s) => s.id === activeConversationId)
  const activeNote = activeSession?.note ?? null

  if (!isIASidebarOpen) return null
  if (typeof document === "undefined") return null

  return createPortal(
    <>
      {/* Overlay — covers only content area to the right of sidebar (Apollo-style) */}
      <div
        className="fixed top-0 bottom-0 right-0 z-30"
        style={{ left: sidebarOffset }}
        onClick={closeIASidebar}
        aria-hidden="true"
      />

      {/* Panel — positioned adjacent to sidebar (Apollo-style) */}
      <aside
        className={cn(
          "fixed top-0 z-40 h-full bg-lia-bg-primary border-r border-lia-border-subtle",
          "flex flex-col shadow-lg"
        )}
        style={{ left: sidebarOffset, width: panelWidth }}
        aria-label={t("aria.historyPanel")}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <Brain className="w-4 h-4 text-wedo-cyan" />
            <span className="text-sm font-semibold text-lia-text-primary">{t("header")}</span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={closeIASidebar}
            className="h-6 w-6 p-0 text-lia-text-secondary hover:text-lia-text-primary"
            aria-label={t("aria.collapsePanel")}
          >
            <ChevronsLeft className="w-4 h-4" />
          </Button>
        </div>

        {/* Nova conversa CTA */}
        <div className="px-3 py-2">
          <button
            onClick={() => { openLiaChat(); closeIASidebar() }}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-lia-bg-inverse hover:bg-lia-bg-inverse/90 text-lia-text-on-inverse text-sm font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
            {t("newConversation")}
          </button>
        </div>

        {/* Note callout for active conversation */}
        {activeNote && (
          <div className="pt-2">
            <NoteCallout
              note={activeNote}
              onEdit={() => {
                // The context menu handles editing; open the item's context menu
              }}
            />
          </div>
        )}

        {/* Search */}
        <div className="px-3 py-2">
          <div className="flex items-center gap-2 px-2 py-1.5 rounded-md bg-lia-bg-secondary dark:bg-lia-bg-tertiary">
            <Search className="w-3 h-3 text-lia-text-muted flex-shrink-0" />
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={t("search.placeholder")}
              className="flex-1 text-xs bg-transparent text-lia-text-primary placeholder:text-lia-text-muted focus:outline-none"
            />
            {searchQuery && (
              <button onClick={() => setSearchQuery("")} className="text-lia-text-muted hover:text-lia-text-secondary">
                <X className="w-3 h-3" />
              </button>
            )}
          </div>
        </div>

        {/* Session list */}
        <div className="flex-1 overflow-y-auto px-1">
          {isLoading && (
            <div className="flex items-center justify-center py-8 text-lia-text-muted">
              <span className="text-xs">{t("loading")}</span>
            </div>
          )}

          {!isLoading && filteredSessions.length === 0 && (
            <div className="py-14 px-6 text-center">
              <div className="w-14 h-14 rounded-full bg-lia-bg-tertiary flex items-center justify-center mx-auto mb-4">
                <MessageSquare className="w-6 h-6 text-lia-text-muted" aria-hidden="true" />
              </div>
              <p className="text-xs font-medium text-lia-text-primary">
                {searchQuery ? t("search.noResults") : t("empty.title")}
              </p>
              {!searchQuery && (
                <p className="text-[11px] text-lia-text-tertiary mt-1">
                  {t("empty.hint")}
                </p>
              )}
            </div>
          )}

          {/* Pinned */}
          {pinned.length > 0 && (
            <>
              <SectionHeader label={t("sections.pinned")} />
              {pinned.map((s) => (
                <SessionItem
                  key={s.id}
                  session={s}
                  isActive={s.id === activeConversationId}
                  localUnread={localUnreadCounts[s.id] ?? 0}
                  onOpen={handleOpen}
                  onUpdate={(p) => updateSession.mutate(p)}
                  onArchive={(id) => archiveSession.mutate(id)}
                  onDelete={(id) => deleteSession.mutate(id)}
                />
              ))}
            </>
          )}

          {/* Today */}
          {todaySessions.length > 0 && (
            <>
              <SectionHeader label={t("sections.today")} />
              {todaySessions.map((s) => (
                <SessionItem
                  key={s.id}
                  session={s}
                  isActive={s.id === activeConversationId}
                  localUnread={localUnreadCounts[s.id] ?? 0}
                  onOpen={handleOpen}
                  onUpdate={(p) => updateSession.mutate(p)}
                  onArchive={(id) => archiveSession.mutate(id)}
                  onDelete={(id) => deleteSession.mutate(id)}
                />
              ))}
            </>
          )}

          {/* Yesterday */}
          {yesterdaySessions.length > 0 && (
            <>
              <SectionHeader label={t("sections.yesterday")} />
              {yesterdaySessions.map((s) => (
                <SessionItem
                  key={s.id}
                  session={s}
                  isActive={s.id === activeConversationId}
                  localUnread={localUnreadCounts[s.id] ?? 0}
                  onOpen={handleOpen}
                  onUpdate={(p) => updateSession.mutate(p)}
                  onArchive={(id) => archiveSession.mutate(id)}
                  onDelete={(id) => deleteSession.mutate(id)}
                />
              ))}
            </>
          )}

          {/* Older */}
          {olderSessions.length > 0 && (
            <>
              <SectionHeader label={t("sections.older")} />
              {olderSessions.map((s) => (
                <SessionItem
                  key={s.id}
                  session={s}
                  isActive={s.id === activeConversationId}
                  localUnread={localUnreadCounts[s.id] ?? 0}
                  onOpen={handleOpen}
                  onUpdate={(p) => updateSession.mutate(p)}
                  onArchive={(id) => archiveSession.mutate(id)}
                  onDelete={(id) => deleteSession.mutate(id)}
                />
              ))}
            </>
          )}
        </div>
        {/* Resize handle */}
        <div
          onMouseDown={handleResizeStart}
          className="absolute right-0 top-0 h-full w-1 cursor-col-resize hover:bg-wedo-cyan/30 transition-colors z-10"
          aria-hidden="true"
        />
      </aside>
    </>,
    document.body
  )
}
