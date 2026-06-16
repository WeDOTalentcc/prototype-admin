"use client"

/**
 * useJdUploadProgress — wires the wizard JD upload step to the async backend.
 *
 * Audit B-02 / Task #865. Background:
 *
 * The legacy flow synchronously POSTed the file inside the request handler,
 * so a 5 MB DOCX could pin the FastAPI worker for 20 s and the chat would
 * just spin. The endpoint now stages the bytes in Redis and returns
 * `202 + task_id`; the actual extraction runs in a Celery worker
 * (`lia-agent-system/app/jobs/tasks/jd_upload.py`) that publishes
 * `background_task_update` events back to the requesting WS session.
 *
 * Responsibilities of this hook:
 *  1. When `useSmartFileUpload` confirms a JD file, POST the bytes to
 *     `/api/backend-proxy/jd-import/upload` with `?session_id=<chatSessionId>`
 *     so the worker can publish updates to the same socket the chat is on.
 *  2. As soon as the proxy returns 202, **seed** a `queued` row into
 *     `chatBackgroundTasks` so the user sees something other than a frozen
 *     spinner — the worker may take 1-2 s before its first `running` event.
 *  3. Watch `chatBackgroundTasks` for terminal updates on the seeded
 *     `task_id` and:
 *       - on `completed`: dispatch `lia:prefill-message` to start the
 *         wizard intake on the imported JD (and clear the task row);
 *       - on `failed`: append a chat message that **echoes the worker's
 *         message verbatim** so users see `fairness_blocked`,
 *         `empty_text`, `resource_exceeded` or `payload_expired` reasons
 *         instead of a generic "Erro ao subir arquivo".
 *
 * The hook deliberately does NOT swallow the existing `lia:file-upload-confirmed`
 * event — it owns the JD branch end-to-end and `useWizardIntegration` was
 * adjusted to skip its own `sendMessage("Criar vaga…")` when this hook is
 * mounted, so we don't double-fire the wizard.
 */

import { useCallback, useEffect, useRef } from "react"
import type { LiaChatMessage, BackgroundTaskEvent } from "@/hooks/chat/lia-chat-connection-types"

interface Params {
  chatSessionId: string
  chatBackgroundTasks: BackgroundTaskEvent[]
  seedBackgroundTask: (event: BackgroundTaskEvent) => void
  clearBackgroundTask: (taskId: string) => void
  appendChatMessage: (message: LiaChatMessage) => void
  /** Called with the imported JD payload (`result.imported_jd_id` etc.) and
   *  the original filename when the worker reports `completed`. Default
   *  behaviour fires `lia:prefill-message` so the existing wizard flow
   *  picks up the conversation. */
  onJdImported?: (filename: string, result: Record<string, unknown> | undefined) => void
}

interface UploadConfirmDetail {
  file?: File
  type?: string
  consentAcknowledged?: boolean
}

const UPLOAD_PROXY_PATH = "/api/backend-proxy/jd-import/upload"

const TERMINAL_STATUSES: ReadonlySet<BackgroundTaskEvent["status"]> = new Set([
  "completed",
  "failed",
])

function buildUploadUrl(file: File, chatSessionId: string): string {
  // The proxy's `uploadQuerySchema` accepts a `title`, the consent flag, and
  // the WS session id. We derive `title` from the filename (sans extension)
  // so the imported JD has a non-empty default — the wizard can rename it
  // later. `consent_acknowledged=true` is safe because this hook only fires
  // after `useSmartFileUpload` has confirmed (or auto-bypassed) consent.
  const url = new URL(UPLOAD_PROXY_PATH, window.location.origin)
  url.searchParams.set(
    "title",
    file.name.replace(/\.[^.]+$/, "").slice(0, 200) || file.name,
  )
  url.searchParams.set("consent_acknowledged", "true")
  url.searchParams.set("session_id", chatSessionId)
  return url.pathname + url.search
}

export function useJdUploadProgress({
  chatSessionId,
  chatBackgroundTasks,
  seedBackgroundTask,
  clearBackgroundTask,
  appendChatMessage,
  onJdImported,
}: Params) {
  // Map of `task_id -> { filename, handled }`. We only fire the
  // success/failure handler ONCE per task even though the WS stream may
  // emit several updates after `completed` (e.g. cleanup events).
  const pendingTasksRef = useRef<Map<string, { filename: string; handled: boolean }>>(new Map())

  // Stable ref for `chatSessionId` so the upload effect doesn't tear down
  // and re-attach every render — the session id is stable for the lifetime
  // of the float context anyway.
  const chatSessionIdRef = useRef(chatSessionId)
  useEffect(() => {
    chatSessionIdRef.current = chatSessionId
  }, [chatSessionId])

  // Mirror of `chatBackgroundTasks` so the upload-confirmation handler can
  // synchronously inspect the current task store immediately after seeding
  // — required to handle the WS-arrives-before-seed race (see below).
  const chatBackgroundTasksRef = useRef(chatBackgroundTasks)
  useEffect(() => {
    chatBackgroundTasksRef.current = chatBackgroundTasks
  }, [chatBackgroundTasks])

  const surfaceErrorMessage = useCallback((label: string, message: string) => {
    appendChatMessage({
      id: `jd-upload-err-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      sender: "lia",
      content: `**${label}** — ${message}`,
      timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
      metadata: { source: "jd-upload", level: "error" },
    })
  }, [appendChatMessage])

  // Single canonical handler for a terminal (`completed`/`failed`) WS event
  // on a task we own. Idempotent via `pending.handled` so the WS effect and
  // the post-seed race-recovery path can both call it without dispatching
  // twice.
  const handleTerminalTask = useCallback((task: BackgroundTaskEvent) => {
    const pending = pendingTasksRef.current.get(task.task_id)
    if (!pending || pending.handled) return
    if (!TERMINAL_STATUSES.has(task.status)) return

    pending.handled = true

    if (task.status === "completed") {
      if (onJdImported) {
        onJdImported(pending.filename, task.result)
      } else {
        // Default: trigger wizard via the same prefill event the rest of
        // the app already listens to. Mention the imported_jd_id when the
        // worker provides it so the wizard can hydrate immediately
        // instead of re-fetching by filename.
        const importedId = task.result && typeof task.result === "object"
          ? (task.result as Record<string, unknown>).imported_jd_id
          : undefined
        const message = importedId
          ? `Criar vaga a partir do arquivo importado (id: ${importedId}, origem: ${pending.filename})`
          : `Criar vaga a partir do arquivo: ${pending.filename}`
        window.dispatchEvent(new CustomEvent("lia:prefill-message", { detail: { message } }))
      }
    } else {
      // failed — surface the worker's `message` verbatim so the user can
      // act on it (fairness_blocked → revisar texto, empty_text → outro
      // arquivo, resource_exceeded → menor, payload_expired → reenviar).
      surfaceErrorMessage(
        "Falha ao importar Job Description",
        task.message || "Erro desconhecido durante o processamento.",
      )
    }

    clearBackgroundTask(task.task_id)
    pendingTasksRef.current.delete(task.task_id)
  }, [clearBackgroundTask, onJdImported, surfaceErrorMessage])

  // Listen for confirmed JD uploads and POST them. Side-effects here are
  // intentionally idempotent: the upstream consent dialog dispatches the
  // same event once per user action, so we don't need to debounce.
  useEffect(() => {
    if (typeof window === "undefined") return

    async function handleConfirmed(e: Event) {
      const detail = (e as CustomEvent<UploadConfirmDetail>).detail || {}
      const { file, type } = detail
      if (type !== "jd" || !file) return

      const sessionId = chatSessionIdRef.current
      const formData = new FormData()
      formData.append("file", file)

      let response: Response
      try {
        response = await fetch(buildUploadUrl(file, sessionId), {
          method: "POST",
          body: formData,
          // Auth (workos_session / lia_access_token) lives in cookies, and
          // the proxy returns 401 if `getAuthHeadersForForm` can't resolve
          // a bearer — `credentials: "include"` is required for the cookie
          // path to work across origins (preview vs prod).
          credentials: "include",
        })
      } catch (err) {
        surfaceErrorMessage(
          "Falha ao enviar JD",
          `Não foi possível contatar o servidor (${(err as Error).message || "erro de rede"}).`,
        )
        return
      }

      // Backend now returns 202 on accept; some proxy paths still return 200
      // (legacy/sync mode) — accept both as "queued for processing".
      if (response.status !== 202 && response.status !== 200) {
        let detailMsg = `HTTP ${response.status}`
        try {
          const body = await response.json()
          if (body && typeof body.error === "string") detailMsg = body.error
          else if (body && typeof body.detail === "string") detailMsg = body.detail
        } catch {
          /* non-JSON body — keep status code */
        }
        surfaceErrorMessage("Falha ao enviar JD", detailMsg)
        return
      }

      let body: { task_id?: string; status?: string; success?: boolean } & Record<string, unknown>
      try {
        body = await response.json()
      } catch {
        surfaceErrorMessage(
          "Falha ao enviar JD",
          "Resposta do servidor em formato inesperado.",
        )
        return
      }

      const taskId = typeof body.task_id === "string" ? body.task_id : ""
      if (!taskId) {
        // Sync legacy fallback: backend returned the imported JD inline.
        // Treat this as immediate completion so the wizard still kicks off.
        if (onJdImported) onJdImported(file.name, body as Record<string, unknown>)
        else
          window.dispatchEvent(new CustomEvent("lia:prefill-message", {
            detail: { message: `Criar vaga a partir do arquivo: ${file.name}` },
          }))
        return
      }

      pendingTasksRef.current.set(taskId, { filename: file.name, handled: false })

      // Seed an immediate "queued" row. The worker will overwrite this entry
      // as soon as it emits its first `background_task_update` thanks to the
      // task_id-based dedup in `seedBackgroundTask` and `useChatSocket`.
      // The seeder's race-guard (`mergeSeededBackgroundTask`) refuses to
      // downgrade an already-terminal entry — necessary because the WS
      // terminal update can land BEFORE this seed call (slow `await
      // response.json()` vs instantaneous Celery completion in dev).
      seedBackgroundTask({
        task_id: taskId,
        task_type: "wizard",
        label: "Importação de Job Description",
        status: "queued",
        message: typeof body.message === "string" ? body.message : "Upload aceito. Processando...",
      })

      // Race-recovery: if a terminal update for this task already lives in
      // `chatBackgroundTasks` (arrived between the POST and now), the
      // `chatBackgroundTasks` effect below won't fire again — neither the
      // array reference nor the pending map were observable when that
      // terminal first landed. Process it synchronously here so the wizard
      // still kicks off / the error still surfaces.
      const existing = chatBackgroundTasksRef.current.find(t => t.task_id === taskId)
      if (existing && TERMINAL_STATUSES.has(existing.status)) {
        handleTerminalTask(existing)
      }
    }

    window.addEventListener("lia:file-upload-confirmed", handleConfirmed as EventListener)
    return () => window.removeEventListener("lia:file-upload-confirmed", handleConfirmed as EventListener)
  }, [seedBackgroundTask, surfaceErrorMessage, onJdImported, handleTerminalTask])

  // React to background task updates on tasks WE seeded. The chat socket
  // already drops the same payload into `chatBackgroundTasks`; we simply
  // observe terminal transitions and translate them into wizard
  // intake / chat-error UI. The actual dispatch is in `handleTerminalTask`
  // so this loop and the race-recovery branch above stay in sync.
  useEffect(() => {
    if (!pendingTasksRef.current.size) return
    for (const task of chatBackgroundTasks) {
      handleTerminalTask(task)
    }
  }, [chatBackgroundTasks, handleTerminalTask])
}
