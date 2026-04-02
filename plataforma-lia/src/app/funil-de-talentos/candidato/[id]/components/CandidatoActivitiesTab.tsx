"use client"

import React from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Activity, FileText, GitBranch, List, PlusCircle, Plus, Loader2
} from "lucide-react"
import { TabsContent } from "@/components/ui/tabs"
import { NOTE_CATEGORY_OPTIONS, NOTE_CATEGORY_LABELS, ACTIVITY_FILTER_LABELS, PERIOD_FILTER_OPTIONS } from "../candidato-page.constants"
import type { ActivityFilter, PeriodFilter, ActivityView, NoteCategory, ActivityItem } from "../candidato-page.types"
import type { CandidateLocal } from "@/services/lia-api"
import { toast } from "sonner"

interface CandidatoActivitiesTabProps {
  activities: Record<string, unknown>[]
  activityFilter: ActivityFilter
  activityView: ActivityView
  periodFilter: PeriodFilter
  newNoteContent: string
  newNoteCategory: NoteCategory
  isLoadingActivities: boolean
  candidate: CandidateLocal
  setActivityFilter: (v: ActivityFilter) => void
  setActivityView: (v: ActivityView) => void
  setPeriodFilter: (v: PeriodFilter) => void
  setNewNoteContent: (v: string) => void
  setNewNoteCategory: (v: NoteCategory) => void
  setActivities: React.Dispatch<React.SetStateAction<Record<string, unknown>[]>>
  formatRelativeTime: (dateStr: string) => string
}

function getCategoryLabelLocal(cat: unknown): string {
  return NOTE_CATEGORY_LABELS[String(cat)] || "Geral"
}

function parseNotes(candidate: CandidateLocal): Record<string, unknown>[] {
  if (!candidate?.notes) return []
  if (typeof candidate.notes === "string") {
    return [{
      id: "note-legacy",
      type: "note",
      category: "general",
      content: candidate.notes,
      created_at: candidate.updated_at || new Date().toISOString(),
    }]
  }
  if (Array.isArray(candidate.notes)) {
    return (candidate.notes as Record<string, unknown>[]).map((note, idx) => ({
      id: (note.id as string) || `note-${idx}`,
      type: "note",
      category: String(note.category || "general"),
      content: String(note.content || (note.text as string) || ""),
      created_at: (note.created_at || note.date || candidate.updated_at) as string,
    }))
  }
  return []
}

export function CandidatoActivitiesTab({
  activities,
  activityFilter,
  activityView,
  periodFilter,
  newNoteContent,
  newNoteCategory,
  isLoadingActivities,
  candidate,
  setActivityFilter,
  setActivityView,
  setPeriodFilter,
  setNewNoteContent,
  setNewNoteCategory,
  setActivities,
  formatRelativeTime,
}: CandidatoActivitiesTabProps) {
  const candidateNotes = parseNotes(candidate)

  const allItems: Array<Record<string, unknown>> = [
    ...activities.map((act) => ({ ...act, itemType: (act.activity_type as string) || (act.type as string) || "activity" })),
    ...candidateNotes.map(n => ({ ...n, itemType: "note" })),
  ]
  allItems.sort((a: Record<string, unknown>, b: Record<string, unknown>) => {
    const dateA = new Date((String(a.created_at || a.timestamp || 0))).getTime()
    const dateB = new Date((String(b.created_at || b.timestamp || 0))).getTime()
    return dateB - dateA
  })
  const filteredItems: Array<Record<string, unknown>> = allItems.filter(item => {
    if (activityFilter === "all") return true
    if (activityFilter === "notes") return item.itemType === "note"
    if (activityFilter === "emails") return item.itemType === "email" || item.type === "email"
    if (activityFilter === "interviews") return item.itemType === "interview" || item.type === "interview"
    if (activityFilter === "lia") return item.itemType === "lia" || item.type === "lia" || item.source === "lia"
    if (activityFilter === "tests") return item.itemType === "test" || item.type === "test"
    if (activityFilter === "offers") return item.itemType === "offer" || item.type === "offer"
    if (activityFilter === "applications") return item.itemType === "application" || item.type === "application"
    return true
  })

  function handleSaveNote() {
    if (!newNoteContent.trim()) return
    const newNote: ActivityItem = {
      id: `note-${Date.now()}`,
      type: "note",
      category: newNoteCategory,
      content: newNoteContent.trim(),
      created_at: new Date().toISOString(),
      author: "Recrutador",
    }
    setActivities(prev => [newNote, ...prev])
    toast.success("Nota adicionada", { description: "A nota foi registrada no histórico do candidato" })
    setNewNoteContent("")
    setNewNoteCategory("general")
  }

  return (
    <TabsContent value="activities" className="mt-4">
      <Card className="border-lia-border-subtle">
        <CardContent className="p-0">
          <div className="flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-semibold text-lia-text-primary flex items-center gap-2">
                  <Activity className="w-4 h-4 text-lia-text-primary" />
                  Feed de Atividades
                  <Badge className="text-xs px-1.5 py-0">{activities.length}</Badge>
                </h4>
                <div className="flex items-center gap-2">
                  <select
                    value={periodFilter}
                    onChange={(e) => setPeriodFilter(e.target.value as PeriodFilter)}
                    className="text-xs px-2 py-1.5 bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-default rounded-md focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 dark:text-lia-text-primary"
                  >
                    {PERIOD_FILTER_OPTIONS.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                  <div className="flex items-center bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-md p-0.5 border border-lia-border-subtle dark:border-lia-border-default">
                    <button
                      onClick={() => setActivityView("timeline")}
                      className={`p-1.5 rounded-md transition-colors motion-reduce:transition-none ${activityView === "timeline" ? "bg-lia-interactive-active text-lia-text-primary" : "text-lia-text-secondary hover:lia-text-700"}`}
                      title="Visualização Timeline"
                    >
                      <GitBranch className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setActivityView("list")}
                      className={`p-1.5 rounded-md transition-colors motion-reduce:transition-none ${activityView === "list" ? "bg-lia-interactive-active text-lia-text-primary" : "text-lia-text-secondary hover:lia-text-700"}`}
                      title="Visualização Lista"
                    >
                      <List className="w-4 h-4" />
                    </button>
                  </div>
                  <Button size="sm" className="gap-1.5 px-3 py-1.5 text-xs h-8 bg-lia-bg-tertiary hover:bg-lia-interactive-active text-lia-text-primary border border-lia-border-subtle">
                    <PlusCircle className="w-3.5 h-3.5" />
                    Nova Atividade
                  </Button>
                </div>
              </div>

              {/* Filtros coloridos */}
              <div className="flex gap-1.5 flex-wrap">
                {(["all","emails","interviews","tests","lia","offers","applications","notes"] as ActivityFilter[]).map(filter => {
                  const isActive = activityFilter === filter
                  const isLia = filter === "lia"
                  const isNote = filter === "notes"
                  let cls = ""
                  if (isLia) cls = isActive ? "bg-status-error text-white" : "bg-status-error/15 text-status-error hover:bg-status-error/20"
                  else if (isNote) cls = isActive ? "bg-status-warning text-white" : "bg-status-warning/15 text-status-warning hover:bg-status-warning/20"
                  else cls = isActive ? "bg-lia-bg-inverse text-white font-semibold" : "bg-lia-bg-tertiary text-lia-text-primary hover:bg-lia-interactive-active"
                  return (
                    <button
                      key={filter}
                      onClick={() => setActivityFilter(filter)}
                      className={`px-2.5 py-1 text-xs rounded-md transition-colors motion-reduce:transition-none ${cls}`}
                    >
                      {ACTIVITY_FILTER_LABELS[filter]}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Add Note section */}
            {(activityFilter === "notes" || activityFilter === "all") && (
              <div className="p-4 border-b border-lia-border-subtle bg-status-warning/5">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-status-warning/15 flex items-center justify-center flex-shrink-0 mt-1">
                    <FileText className="w-4 h-4 text-status-warning" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs font-medium text-lia-text-primary">Categoria:</span>
                      <select
                        value={newNoteCategory}
                        onChange={(e) => setNewNoteCategory(e.target.value as NoteCategory)}
                        className="text-xs px-2 py-1 bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-default rounded-md focus:outline-none focus:ring-1 focus:ring-amber-400 dark:text-lia-text-primary"
                      >
                        {NOTE_CATEGORY_OPTIONS.map(opt => (
                          <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                      </select>
                    </div>
                    <textarea
                      value={newNoteContent}
                      onChange={(e) => setNewNoteContent(e.target.value)}
                      placeholder="Adicione uma nota sobre este candidato..."
                      className="w-full text-sm px-3 py-2 border border-lia-border-subtle dark:border-lia-border-default rounded-md resize-none focus:outline-none focus:ring-1 focus:ring-amber-400 bg-lia-bg-primary dark:bg-lia-bg-secondary dark:text-lia-text-primary"
                      rows={2}
                    />
                  </div>
                  <Button
                    size="sm"
                    className="gap-1.5 mt-6 bg-status-warning hover:bg-status-warning/90 text-white"
                    disabled={!newNoteContent.trim()}
                    onClick={handleSaveNote}
                  >
                    <Plus className="w-3.5 h-3.5" />
                    Salvar
                  </Button>
                </div>
              </div>
            )}

            {/* Feed */}
            <div className="flex-1 p-4" role="status" aria-live="polite">
              {isLoadingActivities ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-6 h-6 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
                </div>
              ) : filteredItems.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 px-4">
                  <div className="w-16 h-16 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-full flex items-center justify-center mb-4">
                    {activityFilter === "notes" ? (
                      <FileText className="w-8 h-8 text-status-warning" />
                    ) : (
                      <Activity className="w-8 h-8 text-lia-text-secondary" />
                    )}
                  </div>
                  <h3 className="text-sm font-semibold text-lia-text-primary mb-2">
                    {activityFilter === "notes" ? "Nenhuma nota registrada ainda" : "Nenhuma atividade registrada ainda"}
                  </h3>
                  <p className="text-xs text-lia-text-secondary text-center max-w-xs">
                    {activityFilter === "notes"
                      ? "Use o formulário acima para adicionar notas sobre este candidato"
                      : "As atividades aparecerão aqui conforme o processo avança"}
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {filteredItems.map((item, index) => {
                    if (item.itemType === "note") {
                      return (
                        <div
                          key={(item.id as string) || index}
                          className="flex items-start gap-3 p-3 bg-status-warning/5 rounded-md border border-status-warning/30 transition-colors motion-reduce:transition-none"
                        >
                          <div className="w-8 h-8 rounded-full bg-status-warning/15 flex items-center justify-center flex-shrink-0">
                            <FileText className="w-4 h-4 text-status-warning" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1 flex-wrap">
                              <span className="text-xs font-medium text-lia-text-primary">Nota Interna</span>
                              <Badge className="text-xs px-1.5 py-0 bg-status-warning/15 text-status-warning border-status-warning/30">
                                {getCategoryLabelLocal(item.category)}
                              </Badge>
                              <span className="text-xs text-lia-text-secondary">{formatRelativeTime(String(item.created_at || ""))}</span>
                            </div>
                            <p className="text-sm text-lia-text-secondary">{String(item.content || "")}</p>
                            {!!item.user_name && (
                              <p className="text-xs text-lia-text-secondary mt-1">Por: {String(item.user_name)}</p>
                            )}
                          </div>
                        </div>
                      )
                    }
                    return (
                      <div
                        key={(item.id as string) || index}
                        className="flex gap-3 p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle transition-colors motion-reduce:transition-none"
                      >
                        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-elevated flex items-center justify-center">
                          <Activity className="w-4 h-4 text-lia-text-secondary" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-semibold text-lia-text-primary">
                              {String(item.activity_type || item.type || item.title || "Atividade")}
                            </span>
                            <span className="text-xs text-lia-text-secondary">
                              {formatRelativeTime(String(item.created_at || item.timestamp || ""))}
                            </span>
                          </div>
                          {!!(item.description || item.content || item.details) && (
                            <p className="text-sm text-lia-text-secondary">
                              {String(item.description || item.content || item.details || "")}
                            </p>
                          )}
                          {!!item.user_name && (
                            <p className="text-xs text-lia-text-secondary mt-1">Por: {String(item.user_name)}</p>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </TabsContent>
  )
}
