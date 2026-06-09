"use client"

import { useEffect, useRef, useState } from "react"
import { useLiaChatContext } from "@/contexts/lia-float-context"
import { BackgroundTaskNotification } from "@/components/lia-float/BackgroundTaskNotification"
import type { BackgroundTask } from "@/components/lia-float/BackgroundAgentsStatus"
import { useCandidatesStore } from "@/stores/candidates-store"
import { BulkResultReport } from "@/components/bulk/BulkResultReport"
import type { BulkItemResult } from "@/lib/bulk"

/**
 * LiaTableStateBridge — ponte in-page (Fase 2 slice 1) + feedback de bulk (F3 Gap 1).
 *
 * Aplica filtro/busca/ordenação vindos do chat à tabela JÁ ABERTA, sem
 * navegar nem mutar dados. Escuta `lia:apply_table_state` (despachado pelo
 * `useUIAction` quando a action global `apply_table_state` chega do backend)
 * e dirige o store da superfície.
 *
 * Slice 1: só a superfície "candidates" (funil) via `useCandidatesStore`.
 * Superfícies futuras (jobs, etc.) entram aqui em slices seguintes.
 *
 * Fase 2 funil tabs: `patch.tab` troca a aba do Funil via `setActiveTab`
 * (search/favorites/lists/history/saved-searches/agents).
 *
 * F3 Gap 1: escuta `lia:bulk_execute` e abre `BulkResultReport` com o
 * resumo de sucesso/falha por item da ação em lote executada via chat.
 *
 * Montado globalmente em LIAGlobalModals — funciona de qualquer página.
 */
type ActiveTab =
  | "search"
  | "favorites"
  | "lists"
  | "history"
  | "saved-searches"
  | "agents"

const VALID_TABS: ReadonlySet<string> = new Set<ActiveTab>([
  "search",
  "favorites",
  "lists",
  "history",
  "saved-searches",
  "agents",
])

interface BulkReportState {
  title: string
  results: BulkItemResult[]
}

export function LiaTableStateBridge() {
  const [bulkReport, setBulkReport] = useState<BulkReportState | null>(null)
  const [notification, setNotification] = useState<BackgroundTask | null>(null)

  // Wire BackgroundTaskNotification: watch chatBackgroundTasks for terminal transitions.
  const { chatBackgroundTasks } = useLiaChatContext()
  const prevTasksRef = useRef<Map<string, string>>(new Map())
  useEffect(() => {
    const prev = prevTasksRef.current
    for (const task of chatBackgroundTasks) {
      const prevStatus = prev.get(task.task_id)
      if (
        (task.status === "completed" || task.status === "failed") &&
        prevStatus !== "completed" &&
        prevStatus !== "failed"
      ) {
        // Task just reached terminal state → show notification
        setNotification({
          id: task.task_id,
          type: task.task_type,
          label: task.label,
          status: task.status,
          progress: task.progress,
          message: task.message,
          result: task.result,
        } as BackgroundTask)
      }
    }
    prevTasksRef.current = new Map(chatBackgroundTasks.map((t) => [t.task_id, t.status]))
  }, [chatBackgroundTasks])

  useEffect(() => {
    function handle(e: Event) {
      const { surface, patch } =
        (e as CustomEvent<{ surface: string; patch: Record<string, unknown> }>)
          .detail ?? {}
      if (surface !== "candidates" || !patch) return
      const s = useCandidatesStore.getState()
      if (typeof patch.search === "string") s.setSearchTerm(patch.search)
      if (typeof patch.sortBy === "string") s.setSortBy(patch.sortBy)
      if (patch.sortOrder === "asc" || patch.sortOrder === "desc")
        s.setSortOrder(patch.sortOrder)
      if (Array.isArray(patch.quickFilters))
        s.setQuickFilters(new Set(patch.quickFilters as string[]))
      if (typeof patch.tab === "string" && VALID_TABS.has(patch.tab))
        s.setActiveTab(patch.tab as ActiveTab)
    }
    function handleSelectRows(e: Event) {
      const { surface, mode, ids } = (
        e as CustomEvent<{
          surface: string
          mode: string
          ids?: string[]
        }>
      ).detail ?? {}
      if (surface !== "candidates") return
      const s = useCandidatesStore.getState()
      if (mode === "clear") {
        s.clearSelection()
      } else if (mode === "set" && Array.isArray(ids)) {
        s.setSelectedCandidates(new Set(ids as string[]))
      } else if (mode === "add" && Array.isArray(ids)) {
        const current = s.selectedCandidates
        s.setSelectedCandidates(new Set([...current, ...(ids as string[])]))
      }
    }
    function handleBulkExecute(e: Event) {
      // F3 Gap 1: recebe resultado de acao em lote disparada via chat.
      const { action, title, results } = (
        e as CustomEvent<{
          action: string
          title: string
          results: { id: string; name: string; ok: boolean; reason?: string }[]
        }>
      ).detail ?? {}
      if (!Array.isArray(results)) return
      setBulkReport({
        title: title ?? action ?? "Resultado da ação em lote",
        results: results as BulkItemResult[],
      })
    }

    window.addEventListener("lia:apply_table_state", handle)
    window.addEventListener("lia:select_rows", handleSelectRows)
    window.addEventListener("lia:bulk_execute", handleBulkExecute)
    return () => {
      window.removeEventListener("lia:apply_table_state", handle)
      window.removeEventListener("lia:select_rows", handleSelectRows)
      window.removeEventListener("lia:bulk_execute", handleBulkExecute)
    }
  }, [])

  return (
    <>
      {/* F5: BackgroundTaskNotification — pop-up quando task de background completa */}
      {notification && (
        <div className="fixed bottom-4 right-4 z-[9999] w-80 animate-in fade-in slide-in-from-bottom-4 duration-300">
          <BackgroundTaskNotification
            task={notification}
            onViewResult={() => setNotification(null)}
            onDismiss={() => setNotification(null)}
          />
        </div>
      )}
      {bulkReport && (
        <BulkResultReport
          isOpen={true}
          onClose={() => setBulkReport(null)}
          results={bulkReport.results}
          actionLabel={bulkReport.title}
        />
      )}
    </>
  )
}
