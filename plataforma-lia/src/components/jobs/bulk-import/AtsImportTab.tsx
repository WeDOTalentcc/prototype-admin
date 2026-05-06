"use client"

/**
 * AtsImportTab — Phase D.2.
 *
 * Inside BulkImportModal, this tab lets the recruiter pull vagas directly
 * from a connected ATS (Gupy / Pandapé) instead of uploading CSV/JSON.
 *
 * Three steps:
 *   1. List of company ATS connections (GET /ats/connections)
 *   2. List of remote jobs for the picked connection
 *      (GET /ats/connections/{id}/jobs — Phase C.3)
 *   3. Confirm & dispatch sync filtered by selected job_ids
 *      (POST /ats/connections/{id}/sync — already existed)
 *
 * Merge connections render disabled with a tooltip; the backend returns 501
 * and we want the user to know up front rather than fail on click.
 *
 * Hooks ALWAYS above any early return (Rules of Hooks discipline).
 *
 * See .planning/vacancy-pipeline-plan.md > Phase D.
 */
import { useEffect, useMemo, useState, useCallback } from "react"
import Link from "next/link"
import { Loader2, Check, AlertCircle, Building2, Lock } from "lucide-react"

interface AtsConnection {
  id: string
  provider: string
  name?: string
  is_active?: boolean
  last_sync_at?: string | null
  status?: string
}

interface RemoteJob {
  external_id: string
  title: string
  department?: string | null
  location?: string | null
  status?: string | null
  posted_at?: string | null
}

interface AtsImportTabProps {
  /** Called when import succeeds; parent typically refreshes lifecycle list. */
  onImportSuccess?: (count: number) => void
}

const SUPPORTED_PROVIDERS = new Set(["gupy", "pandape"])

export function AtsImportTab({ onImportSuccess }: AtsImportTabProps) {
  // ── Hooks (above any early return) ──
  const [connections, setConnections] = useState<AtsConnection[]>([])
  const [isLoadingConnections, setIsLoadingConnections] = useState(true)
  const [connectionsError, setConnectionsError] = useState<string | null>(null)

  const [selectedConnId, setSelectedConnId] = useState<string | null>(null)
  const [remoteJobs, setRemoteJobs] = useState<RemoteJob[]>([])
  const [isLoadingJobs, setIsLoadingJobs] = useState(false)
  const [jobsError, setJobsError] = useState<string | null>(null)

  const [selectedJobIds, setSelectedJobIds] = useState<Set<string>>(new Set())
  const [searchQuery, setSearchQuery] = useState("")
  const [isImporting, setIsImporting] = useState(false)
  const [importError, setImportError] = useState<string | null>(null)
  const [importedCount, setImportedCount] = useState<number | null>(null)

  // Step 1: load connections on mount.
  useEffect(() => {
    let cancelled = false
    setIsLoadingConnections(true)
    setConnectionsError(null)
    fetch("/api/backend-proxy/ats/connections")
      .then(async (r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return (await r.json()) as AtsConnection[]
      })
      .then((data) => {
        if (cancelled) return
        setConnections(Array.isArray(data) ? data : [])
      })
      .catch((err) => {
        if (cancelled) return
        setConnectionsError(err instanceof Error ? err.message : "Erro desconhecido")
      })
      .finally(() => {
        if (!cancelled) setIsLoadingConnections(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  // Step 2: when user picks a connection, fetch remote jobs.
  useEffect(() => {
    if (!selectedConnId) return
    let cancelled = false
    setIsLoadingJobs(true)
    setJobsError(null)
    setRemoteJobs([])
    setSelectedJobIds(new Set())
    fetch(`/api/backend-proxy/ats/connections/${selectedConnId}/jobs?page=1&size=200`)
      .then(async (r) => {
        if (!r.ok) {
          const body = await r.text()
          throw new Error(`HTTP ${r.status}: ${body.slice(0, 160)}`)
        }
        return (await r.json()) as { items?: RemoteJob[] }
      })
      .then((data) => {
        if (cancelled) return
        setRemoteJobs(Array.isArray(data.items) ? data.items : [])
      })
      .catch((err) => {
        if (cancelled) return
        setJobsError(err instanceof Error ? err.message : "Erro desconhecido")
      })
      .finally(() => {
        if (!cancelled) setIsLoadingJobs(false)
      })
    return () => {
      cancelled = true
    }
  }, [selectedConnId])

  const filteredJobs = useMemo(() => {
    const q = searchQuery.trim().toLowerCase()
    if (!q) return remoteJobs
    return remoteJobs.filter(
      (j) =>
        j.title.toLowerCase().includes(q) ||
        (j.department || "").toLowerCase().includes(q) ||
        (j.location || "").toLowerCase().includes(q),
    )
  }, [remoteJobs, searchQuery])

  const toggleJob = useCallback((id: string) => {
    setSelectedJobIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  const toggleAll = useCallback(() => {
    setSelectedJobIds((prev) => {
      if (prev.size === filteredJobs.length) return new Set()
      return new Set(filteredJobs.map((j) => j.external_id))
    })
  }, [filteredJobs])

  const handleImport = useCallback(async () => {
    if (!selectedConnId || selectedJobIds.size === 0) return
    setIsImporting(true)
    setImportError(null)
    try {
      const res = await fetch(
        `/api/backend-proxy/ats/connections/${selectedConnId}/sync`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            sync_type: "jobs",
            filters: { job_ids: Array.from(selectedJobIds) },
          }),
        },
      )
      if (!res.ok) {
        const body = await res.text()
        throw new Error(`HTTP ${res.status}: ${body.slice(0, 160)}`)
      }
      const count = selectedJobIds.size
      setImportedCount(count)
      onImportSuccess?.(count)
    } catch (err) {
      setImportError(err instanceof Error ? err.message : "Erro desconhecido")
    } finally {
      setIsImporting(false)
    }
  }, [selectedConnId, selectedJobIds, onImportSuccess])

  // ── Render ──
  if (isLoadingConnections) {
    return (
      <div className="flex items-center justify-center py-12 text-lia-text-tertiary">
        <Loader2 className="w-4 h-4 animate-spin mr-2" />
        Carregando integrações…
      </div>
    )
  }

  if (connectionsError) {
    return (
      <div className="flex flex-col items-center py-8 text-status-error">
        <AlertCircle className="w-6 h-6 mb-2" />
        <p className="text-sm">Falha ao carregar integrações: {connectionsError}</p>
      </div>
    )
  }

  if (connections.length === 0) {
    return (
      <div className="flex flex-col items-center py-8 text-lia-text-tertiary">
        <Building2 className="w-8 h-8 mb-2 opacity-40" />
        <p className="text-sm">Nenhuma integração ATS conectada.</p>
        <Link
          href="/configuracoes?section=integrations"
          className="text-xs mt-2 underline hover:text-lia-text-primary"
        >
          Configurar uma agora
        </Link>
      </div>
    )
  }

  // Imported state — show success and reset button.
  if (importedCount !== null) {
    return (
      <div className="flex flex-col items-center py-8 text-lia-text-secondary">
        <Check className="w-8 h-8 mb-2 text-status-success" />
        <p className="text-sm font-medium text-lia-text-primary">
          {importedCount} {importedCount === 1 ? "vaga importada" : "vagas importadas"}
        </p>
        <p className="text-xs mt-1">As vagas aparecerão em &quot;ATS Importada&quot; assim que o sync concluir.</p>
        <button
          className="mt-4 text-xs underline hover:text-lia-text-primary"
          onClick={() => {
            setImportedCount(null)
            setSelectedJobIds(new Set())
          }}
        >
          Importar mais vagas
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4 py-2">
      {/* Step 1: connections list */}
      <section>
        <h3 className="text-xs font-medium text-lia-text-secondary uppercase tracking-wide mb-2">
          1. Escolha a integração
        </h3>
        <div className="grid grid-cols-2 gap-2">
          {connections.map((c) => {
            const isSupported = SUPPORTED_PROVIDERS.has(c.provider.toLowerCase())
            const isSelected = c.id === selectedConnId
            return (
              <button
                key={c.id}
                disabled={!isSupported}
                onClick={() => setSelectedConnId(c.id)}
                className={[
                  "p-3 rounded-lg border text-left transition-colors",
                  isSelected
                    ? "border-wedo-cyan bg-lia-bg-tertiary"
                    : "border-lia-border-subtle hover:border-lia-border-default hover:bg-lia-bg-secondary",
                  !isSupported && "opacity-50 cursor-not-allowed",
                ].filter(Boolean).join(" ")}
                title={
                  !isSupported
                    ? "Importação direta para este provedor — em breve. Use CSV/JSON."
                    : undefined
                }
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-lia-text-primary capitalize">
                    {c.name || c.provider}
                  </span>
                  {!isSupported && <Lock className="w-3 h-3 text-lia-text-tertiary" />}
                </div>
                <div className="text-xs text-lia-text-tertiary">
                  {c.provider}
                  {c.last_sync_at && ` · sync ${new Date(c.last_sync_at).toLocaleDateString("pt-BR")}`}
                </div>
              </button>
            )
          })}
        </div>
      </section>

      {/* Step 2: job list */}
      {selectedConnId && (
        <section>
          <h3 className="text-xs font-medium text-lia-text-secondary uppercase tracking-wide mb-2">
            2. Selecione as vagas
          </h3>

          {isLoadingJobs ? (
            <div className="flex items-center py-6 text-xs text-lia-text-tertiary">
              <Loader2 className="w-3 h-3 animate-spin mr-2" />
              Buscando vagas no ATS…
            </div>
          ) : jobsError ? (
            <div className="flex items-center py-4 text-xs text-status-error">
              <AlertCircle className="w-3 h-3 mr-2" />
              {jobsError}
            </div>
          ) : remoteJobs.length === 0 ? (
            <p className="text-xs text-lia-text-tertiary py-4">Nenhuma vaga encontrada.</p>
          ) : (
            <>
              <div className="flex items-center gap-2 mb-2">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Filtrar por título, departamento, local…"
                  className="flex-1 px-2 py-1 rounded text-xs bg-lia-bg-secondary border border-lia-border-subtle"
                />
                <button
                  onClick={toggleAll}
                  className="text-xs text-lia-text-secondary underline whitespace-nowrap"
                >
                  {selectedJobIds.size === filteredJobs.length && filteredJobs.length > 0
                    ? "Desmarcar todas"
                    : "Selecionar todas"}
                </button>
              </div>

              <div className="max-h-64 overflow-y-auto border border-lia-border-subtle rounded-lg">
                {filteredJobs.map((j) => {
                  const checked = selectedJobIds.has(j.external_id)
                  return (
                    <label
                      key={j.external_id}
                      className="flex items-center gap-2 px-3 py-2 border-b border-lia-border-subtle last:border-b-0 hover:bg-lia-bg-secondary cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => toggleJob(j.external_id)}
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-lia-text-primary truncate">{j.title}</p>
                        <p className="text-[10px] text-lia-text-tertiary truncate">
                          {[j.department, j.location, j.status].filter(Boolean).join(" · ")}
                        </p>
                      </div>
                    </label>
                  )
                })}
              </div>
            </>
          )}
        </section>
      )}

      {/* Step 3: import action */}
      {selectedConnId && remoteJobs.length > 0 && (
        <section className="flex items-center justify-between gap-2 pt-2">
          <span className="text-xs text-lia-text-tertiary">
            {selectedJobIds.size} de {filteredJobs.length} vaga(s) selecionada(s)
          </span>
          <button
            onClick={handleImport}
            disabled={selectedJobIds.size === 0 || isImporting}
            className="px-3 py-2 rounded-lg text-xs font-medium bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors motion-reduce:transition-none"
          >
            {isImporting ? (
              <>
                <Loader2 className="w-3 h-3 animate-spin inline mr-1" />
                Importando…
              </>
            ) : (
              "Importar vagas selecionadas"
            )}
          </button>
        </section>
      )}

      {importError && (
        <div className="flex items-center text-xs text-status-error">
          <AlertCircle className="w-3 h-3 mr-1" />
          {importError}
        </div>
      )}
    </div>
  )
}
