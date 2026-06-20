"use client"

import { useState, useMemo, useCallback, useEffect } from "react"
import { useTranslations } from "next-intl"
import {
  Brain, Plus, Pin, PinOff, Edit3, StickyNote, Archive, Trash2,
  X, Search, MessageSquare, ChevronDown, ChevronsLeft,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { useIASessionStore } from "@/stores/ia-session-store"
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
// Context menu
// ---------------------------------------------------------------------------
interface ContextMenuProps {
  session: IASession
  onClose: () => void
  onPin: () => void
  onRename: () => void
  onNote: () => void
  onArchive: () => void
  onDelete: () => void
}

function SessionContextMenu({
  session,
  onClose,
  onPin,
  onRename,
  onNote,
  onArchive,
  onDelete,
}: ContextMenuProps) {
  return (
    <div
      className="absolute right-0 top-6 z-50 bg-lia-bg-primary border border-lia-border-subtle rounded-lg shadow-lg py-1 min-w-[160px]"
      onClick={(e) => e.stopPropagation()}
    >
      <button
        className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-lia-text-secondary hover:bg-lia-interactive-hover"
        onClick={() => { onPin(); onClose() }}
      >
        {session.is_pinned ? (
          <><PinOff className="w-3.5 h-3.5" /> Desafixar <kbd className="ml-auto text-[10px] text-lia-text-muted">P</kbd></>
        ) : (
          <><Pin className="w-3.5 h-3.5" /> Fixar <kbd className="ml-auto text-[10px] text-lia-text-muted">P</kbd></>
        )}
      </button>
      <button
        className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-lia-text-secondary hover:bg-lia-interactive-hover"
        onClick={() => { onRename(); onClose() }}
      >
        <Edit3 className="w-3.5 h-3.5" /> Renomear <kbd className="ml-auto text-[10px] text-lia-text-muted">R</kbd>
      </button>
      <button
        className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-lia-text-secondary hover:bg-lia-interactive-hover"
        onClick={() => { onNote(); onClose() }}
      >
        <StickyNote className="w-3.5 h-3.5" /> Nota <kbd className="ml-auto text-[10px] text-lia-text-muted">N</kbd>
      </button>
      <div className="my-1 border-t border-lia-border-subtle" />
      <button
        className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-lia-text-secondary hover:bg-lia-interactive-hover"
        onClick={() => { onArchive(); onClose() }}
      >
        <Archive className="w-3.5 h-3.5" /> Arquivar <kbd className="ml-auto text-[10px] text-lia-text-muted">A</kbd>
      </button>
      <button
        className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-status-error hover:bg-status-error/10"
        onClick={() => { onDelete(); onClose() }}
      >
        <Trash2 className="w-3.5 h-3.5" /> Excluir <kbd className="ml-auto text-[10px] text-lia-text-muted">Del</kbd>
      </button>
    </div>
  )
}

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
  const [menuOpen, setMenuOpen] = useState(false)
  const [renaming, setRenaming] = useState(false)
  const [renameValue, setRenameValue] = useState(session.title ?? "")
  const [addingNote, setAddingNote] = useState(false)
  const [noteValue, setNoteValue] = useState(session.note ?? "")

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
      : "Conversa")

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
            placeholder="Adicionar nota..."
            rows={3}
            maxLength={500}
            className="w-full text-xs px-2 py-1 rounded border border-lia-border-medium bg-lia-bg-primary text-lia-text-primary focus:outline-none focus:ring-1 focus:ring-wedo-cyan resize-none"
          />
          <div className="flex justify-end gap-1 mt-1">
            <button onClick={() => setAddingNote(false)} className="text-[10px] text-lia-text-muted px-2 py-0.5 hover:text-lia-text-secondary">Cancelar</button>
            <button onClick={handleNoteSubmit} className="text-[10px] text-wedo-cyan px-2 py-0.5 font-medium hover:text-wedo-cyan/80">Salvar (⌘↵)</button>
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
          <div className="flex items-center gap-1.5 min-w-0">
            {session.domain_tag && <DomainTagChip tag={session.domain_tag} />}
            <span className="text-[10px] text-lia-text-muted">
              {session.updated_at
                ? new Date(session.updated_at).toLocaleDateString("pt-BR", { day: "numeric", month: "short" })
                : ""}
            </span>
          </div>
        </button>
      )}

      {/* "..." hover menu trigger */}
      {!renaming && !addingNote && (
        <div className="absolute right-1 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 focus-within:opacity-100">
          <button
            onClick={(e) => { e.stopPropagation(); setMenuOpen((v) => !v) }}
            className="p-1 rounded hover:bg-lia-bg-elevated text-lia-text-muted hover:text-lia-text-secondary"
            aria-label="Opções da conversa"
          >
            <ChevronDown className="w-3 h-3" />
          </button>
          {menuOpen && (
            <SessionContextMenu
              session={session}
              onClose={() => setMenuOpen(false)}
              onPin={() => onUpdate({ id: session.id, is_pinned: !session.is_pinned })}
              onRename={() => { setRenameValue(session.title ?? ""); setRenaming(true) }}
              onNote={() => { setNoteValue(session.note ?? ""); setAddingNote(true) }}
              onArchive={() => onArchive(session.id)}
              onDelete={() => onDelete(session.id)}
            />
          )}
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
  const { isIASidebarOpen, closeIASidebar, activeConversationId, setActiveConversation, localUnreadCounts } =
    useIASessionStore()
  const { open: openLiaChat } = useLiaFloat()
  const [searchQuery, setSearchQuery] = useState("")
  const { data: sessions = [], isLoading } = useIASessions()
  const updateSession = useUpdateSession()
  const markRead = useMarkSessionRead()
  const deleteSession = useDeleteSession()
  const archiveSession = useArchiveSession()

  const handleOpen = useCallback(
    (id: string) => {
      setActiveConversation(id)
      markRead.mutate(id)
      // Open the conversation in LIA chat panel
      openLiaChat(id)
      onOpenConversation?.(id)
      closeIASidebar()
    },
    [setActiveConversation, markRead, openLiaChat, closeIASidebar, onOpenConversation]
  )

  // Keyboard shortcuts: P=pin, N=new, A=archive, Del=delete, Esc=close
  // Scoped to sidebar open + focus NOT in a text field
  useEffect(() => {
    if (!isIASidebarOpen) return
    const handler = (e: KeyboardEvent) => {
      const el = e.target as HTMLElement
      if (el.tagName === "INPUT" || el.tagName === "TEXTAREA" || el.isContentEditable) return
      const target = sessions.find((s) => s.id === activeConversationId)
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
    if (!searchQuery.trim()) return sessions
    const q = searchQuery.toLowerCase()
    return sessions.filter(
      (s) =>
        (s.title ?? "").toLowerCase().includes(q) ||
        (s.domain_tag ?? "").toLowerCase().includes(q)
    )
  }, [sessions, searchQuery])

  const pinned = filteredSessions.filter((s) => s.is_pinned)
  const todaySessions = filteredSessions.filter((s) => !s.is_pinned && isToday(s.updated_at))
  const yesterdaySessions = filteredSessions.filter((s) => !s.is_pinned && isYesterday(s.updated_at))
  const olderSessions = filteredSessions.filter(
    (s) => !s.is_pinned && !isToday(s.updated_at) && !isYesterday(s.updated_at)
  )

  const activeSession = sessions.find((s) => s.id === activeConversationId)
  const activeNote = activeSession?.note ?? null

  if (!isIASidebarOpen) return null

  return (
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
          "fixed top-0 z-40 h-full w-[420px] bg-lia-bg-primary border-r border-lia-border-subtle",
          "flex flex-col shadow-lg",
          "transform transition-transform duration-200 ease-out"
        )}
        style={{ left: sidebarOffset }}
        aria-label="Histórico de conversas com a LIA"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-lia-border-subtle">
          <div className="flex items-center gap-2">
            <Brain className="w-4 h-4 text-wedo-cyan" />
            <span className="text-sm font-semibold text-lia-text-primary">Conversas</span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={closeIASidebar}
            className="h-6 w-6 p-0 text-lia-text-secondary hover:text-lia-text-primary"
            aria-label="Retrair painel"
          >
            <ChevronsLeft className="w-4 h-4" />
          </Button>
        </div>

        {/* Nova conversa CTA */}
        <div className="px-3 py-2 border-b border-lia-border-subtle">
          <button
            onClick={() => { onNewConversation?.(); closeIASidebar() }}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-wedo-cyan/10 hover:bg-wedo-cyan/15 text-wedo-cyan text-sm font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
            Nova conversa
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
              placeholder="Buscar conversas..."
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
              <span className="text-xs">Carregando...</span>
            </div>
          )}

          {!isLoading && filteredSessions.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-center px-4 gap-3">
              <MessageSquare className="w-8 h-8 text-lia-text-muted opacity-40" />
              <div>
                <p className="text-xs font-medium text-lia-text-secondary">
                  {searchQuery ? "Nenhuma conversa encontrada" : "Comece uma conversa com a LIA"}
                </p>
                {!searchQuery && (
                  <p className="text-[11px] text-lia-text-muted mt-1">
                    Clique em &ldquo;Nova conversa&rdquo; para começar
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Pinned */}
          {pinned.length > 0 && (
            <>
              <SectionHeader label="Fixadas" />
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
              <SectionHeader label="Hoje" />
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
              <SectionHeader label="Ontem" />
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
              <SectionHeader label="Anteriores" />
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
      </aside>
    </>
  )
}
