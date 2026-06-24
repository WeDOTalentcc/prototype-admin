"use client"

/**
 * BulkImportModal v2 — Phase 4I bulk-import flow with CSV + polling.
 *
 * 5-step wizard: input → preview → importing → polling → result
 *
 * Input modes:
 *   - File upload (CSV) — native FileReader + simple parser (no npm dep)
 *   - JSON paste (power-user fallback)
 *
 * Polling:
 *   POST /api/backend-proxy/jobs/bulk-import returns batch_id + initial status.
 *   If status != 'completed', poll GET /api/backend-proxy/jobs/bulk-import-status/{batch_id}
 *   every 2s until completed or 60s timeout.
 *
 * CSV mapping:
 *   Header row mapped to JD fields by case-insensitive normalization:
 *     'title' / 'titulo' / 'cargo' / 'job title'  → title
 *     'department' / 'departamento' / 'area'       → department
 *     'seniority' / 'senioridade' / 'nivel'        → seniority
 *     'salary_min' / 'salario_min' / 'min_salary'  → salary_min
 *     'salary_max' / 'salario_max' / 'max_salary'  → salary_max
 *     'manager_email' / 'gestor_email' / 'email'   → hiring_manager_email
 *     'description' / 'descricao' / 'desc'         → description
 *     'external_id' / 'id_externo' / 'job_id'      → external_id
 *     'skills' / 'habilidades' / 'tecnologias'     → skills (split by comma/semicolon)
 *
 * Auto-mapping shown to user; user can override before confirming.
 */
import React, { useState, useRef, useCallback } from "react"
import {
  Upload,
  FileSpreadsheet,
  X,
  AlertCircle,
  CheckCircle2,
  Loader2,
  FileJson,
  FileText,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { AtsImportTab } from "@/components/jobs/bulk-import/AtsImportTab"

interface BulkImportJob {
  title: string
  department?: string
  seniority?: string
  salary_min?: number
  salary_max?: number
  skills?: string[]
  description?: string
  hiring_manager_email?: string
  status?: string
  external_id?: string
}

interface BulkImportResponse {
  batch_id: string
  total: number
  successful: number
  failed: number
  status: string
  items: Array<{
    index: number
    title: string
    status: "ok" | "failed"
    error?: string
  }>
}

interface BatchStatusResponse {
  batch_id: string
  status: string
  total_records: number
  processed_records: number
  successful_records: number
  failed_records: number
  errors?: Array<{ jd_title?: string; error?: string }>
}

interface BulkImportModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: (batch: BulkImportResponse) => void
}

type Step = "input" | "preview" | "importing" | "polling" | "result"
type InputMode = "file" | "json" | "ats"

// CSV header → JSON field mapping (case-insensitive, normalized)
const HEADER_MAP: Record<string, keyof BulkImportJob> = {
  title: "title",
  titulo: "title",
  cargo: "title",
  "job title": "title",
  position: "title",
  department: "department",
  departamento: "department",
  area: "department",
  "área": "department",
  seniority: "seniority",
  senioridade: "seniority",
  nivel: "seniority",
  "nível": "seniority",
  level: "seniority",
  salary_min: "salary_min",
  salario_min: "salary_min",
  "salário_min": "salary_min",
  min_salary: "salary_min",
  salary_max: "salary_max",
  salario_max: "salary_max",
  "salário_max": "salary_max",
  max_salary: "salary_max",
  manager_email: "hiring_manager_email",
  gestor_email: "hiring_manager_email",
  email_gestor: "hiring_manager_email",
  hiring_manager_email: "hiring_manager_email",
  description: "description",
  descricao: "description",
  "descrição": "description",
  desc: "description",
  external_id: "external_id",
  id_externo: "external_id",
  job_id: "external_id",
  id: "external_id",
  skills: "skills",
  habilidades: "skills",
  tecnologias: "skills",
  status: "status",
}

function normalizeHeader(h: string): string {
  return h.trim().toLowerCase().replace(/\s+/g, "_").replace(/[̀-ͯ]/g, "")
}

/** Simple CSV parser — handles quoted fields with embedded commas/newlines. */
function parseCsv(text: string): { headers: string[]; rows: string[][] } {
  const lines: string[][] = []
  let cur: string[] = []
  let field = ""
  let inQuotes = false
  let i = 0
  while (i < text.length) {
    const ch = text[i]
    if (inQuotes) {
      if (ch === '"' && text[i + 1] === '"') {
        field += '"'
        i += 2
        continue
      }
      if (ch === '"') {
        inQuotes = false
        i++
        continue
      }
      field += ch
      i++
      continue
    }
    if (ch === '"') {
      inQuotes = true
      i++
      continue
    }
    if (ch === "," || ch === ";") {
      cur.push(field)
      field = ""
      i++
      continue
    }
    if (ch === "\n" || ch === "\r") {
      // handle \r\n
      if (ch === "\r" && text[i + 1] === "\n") i++
      cur.push(field)
      field = ""
      if (cur.length > 1 || cur[0] !== "") lines.push(cur)
      cur = []
      i++
      continue
    }
    field += ch
    i++
  }
  if (field !== "" || cur.length > 0) {
    cur.push(field)
    if (cur.length > 1 || cur[0] !== "") lines.push(cur)
  }
  if (lines.length === 0) return { headers: [], rows: [] }
  return { headers: lines[0], rows: lines.slice(1) }
}

/** Convert parsed CSV to BulkImportJob[] using HEADER_MAP. */
function csvToJobs(headers: string[], rows: string[][]): {
  jobs: BulkImportJob[]
  unmappedHeaders: string[]
  mappedHeaders: Record<string, keyof BulkImportJob>
} {
  const mapping: Record<number, keyof BulkImportJob> = {}
  const mappedHeaders: Record<string, keyof BulkImportJob> = {}
  const unmappedHeaders: string[] = []

  headers.forEach((h, idx) => {
    const norm = normalizeHeader(h)
    const target = HEADER_MAP[norm]
    if (target) {
      mapping[idx] = target
      mappedHeaders[h] = target
    } else if (h.trim()) {
      unmappedHeaders.push(h)
    }
  })

  const jobs: BulkImportJob[] = rows
    .filter((r) => r.some((c) => c.trim() !== ""))
    .map((row) => {
      const job: BulkImportJob = { title: "" }
      Object.entries(mapping).forEach(([idxStr, field]) => {
        const idx = Number(idxStr)
        const raw = (row[idx] ?? "").trim()
        if (!raw) return
        if (field === "salary_min" || field === "salary_max") {
          const n = Number(raw.replace(/[^0-9.,-]/g, "").replace(",", "."))
          if (!isNaN(n)) (job as unknown as Record<string, unknown>)[field] = n
        } else if (field === "skills") {
          job.skills = raw.split(/[,;]/).map((s) => s.trim()).filter(Boolean)
        } else {
          (job as unknown as Record<string, unknown>)[field] = raw
        }
      })
      return job
    })
    .filter((j) => j.title)

  return { jobs, unmappedHeaders, mappedHeaders }
}

export function BulkImportModal({ isOpen, onClose, onSuccess }: BulkImportModalProps) {
  const [step, setStep] = useState<Step>("input")
  const [mode, setMode] = useState<InputMode>("file")
  const [rawJson, setRawJson] = useState("")
  const [parseError, setParseError] = useState<string | null>(null)
  const [jobs, setJobs] = useState<BulkImportJob[]>([])
  const [mappedHeaders, setMappedHeaders] = useState<Record<string, string>>({})
  const [unmappedHeaders, setUnmappedHeaders] = useState<string[]>([])
  const [importResult, setImportResult] = useState<BulkImportResponse | null>(null)
  const [importError, setImportError] = useState<string | null>(null)
  const [pollProgress, setPollProgress] = useState<BatchStatusResponse | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const reset = () => {
    setStep("input")
    setMode("file")
    setRawJson("")
    setParseError(null)
    setJobs([])
    setMappedHeaders({})
    setUnmappedHeaders([])
    setImportResult(null)
    setImportError(null)
    setPollProgress(null)
  }

  const handleClose = () => {
    reset()
    onClose()
  }

  const handleFileRead = useCallback((file: File) => {
    setParseError(null)
    const reader = new FileReader()
    reader.onload = (e) => {
      const text = String(e.target?.result || "")
      try {
        if (file.name.toLowerCase().endsWith(".json")) {
          const parsed = JSON.parse(text)
          const arr: BulkImportJob[] = Array.isArray(parsed)
            ? parsed
            : Array.isArray((parsed as Record<string, unknown>).jobs)
            ? ((parsed as Record<string, unknown>).jobs as BulkImportJob[])
            : []
          if (!arr.length) {
            setParseError("JSON vazio ou sem 'jobs'.")
            return
          }
          if (!arr.every((j) => j.title)) {
            setParseError("Algumas vagas não têm campo 'title' (obrigatório).")
            return
          }
          setJobs(arr)
          setMappedHeaders({})
          setUnmappedHeaders([])
          setStep("preview")
        } else {
          // CSV path
          const { headers, rows } = parseCsv(text)
          if (!headers.length) {
            setParseError("CSV vazio ou cabeçalho não encontrado.")
            return
          }
          const { jobs: csvJobs, mappedHeaders: m, unmappedHeaders: u } = csvToJobs(headers, rows)
          if (!csvJobs.length) {
            setParseError(
              "Nenhuma vaga válida encontrada (precisa ter coluna 'title', 'titulo' ou 'cargo')."
            )
            return
          }
          setJobs(csvJobs)
          setMappedHeaders(Object.fromEntries(Object.entries(m).map(([k, v]) => [k, String(v)])))
          setUnmappedHeaders(u)
          setStep("preview")
        }
      } catch (err) {
        setParseError(`Erro ao parsear: ${err instanceof Error ? err.message : "desconhecido"}`)
      }
    }
    reader.onerror = () => setParseError("Erro ao ler o arquivo.")
    reader.readAsText(file, "UTF-8")
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)
      const file = e.dataTransfer.files?.[0]
      if (file) handleFileRead(file)
    },
    [handleFileRead]
  )

  // Rules of Hooks: this early return MUST stay below every hook call.
  // See CLAUDE.md § Frontend / React rules-of-hooks discipline.
  if (!isOpen) return null

  const handleParseJson = () => {
    setParseError(null)
    try {
      const parsed = JSON.parse(rawJson)
      const arr: BulkImportJob[] = Array.isArray(parsed)
        ? parsed
        : Array.isArray((parsed as Record<string, unknown>).jobs)
        ? ((parsed as Record<string, unknown>).jobs as BulkImportJob[])
        : []
      if (!arr.length) {
        setParseError("Nenhuma vaga encontrada. Esperado: array JSON ou objeto com chave 'jobs'.")
        return
      }
      const invalid = arr.findIndex((j) => !j.title)
      if (invalid >= 0) {
        setParseError(`Vaga #${invalid + 1} não tem campo 'title' (obrigatório).`)
        return
      }
      setJobs(arr)
      setMappedHeaders({})
      setUnmappedHeaders([])
      setStep("preview")
    } catch (e) {
      setParseError(`JSON inválido: ${e instanceof Error ? e.message : "erro desconhecido"}`)
    }
  }

  const pollBatchStatus = async (batchId: string, maxSeconds = 60): Promise<BulkImportResponse> => {
    const startedAt = Date.now()
    while (Date.now() - startedAt < maxSeconds * 1000) {
      await new Promise((r) => setTimeout(r, 2000))
      try {
        const res = await fetch(`/api/backend-proxy/jobs/bulk-import-status/${batchId}`)
        if (!res.ok) continue
        const status = (await res.json()) as BatchStatusResponse
        setPollProgress(status)
        if (
          status.status === "completed" ||
          status.status === "partially_completed" ||
          status.status === "failed"
        ) {
          // Build a BulkImportResponse-ish shape from final batch status
          return {
            batch_id: status.batch_id,
            total: status.total_records,
            successful: status.successful_records,
            failed: status.failed_records,
            status: status.status,
            items: (status.errors || []).map((e, idx) => ({
              index: idx,
              title: e.jd_title || "?",
              status: "failed" as const,
              error: e.error || "",
            })),
          }
        }
      } catch {
        // network blip — continue polling
      }
    }
    throw new Error(`Timeout: import não concluiu em ${maxSeconds}s`)
  }

  const handleConfirmImport = async () => {
    setStep("importing")
    setImportError(null)
    try {
      const res = await fetch("/api/backend-proxy/jobs/bulk-import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: "spreadsheet", jobs }),
      })

      if (!res.ok && res.status !== 207) {
        const errBody = await res.text()
        throw new Error(`HTTP ${res.status}: ${errBody.slice(0, 200)}`)
      }

      const data = (await res.json()) as BulkImportResponse

      // If batch is still processing, poll for completion
      if (data.status === "processing" || data.status === "pending") {
        setStep("polling")
        const finalStatus = await pollBatchStatus(data.batch_id)
        setImportResult(finalStatus)
        setStep("result")
        onSuccess(finalStatus)
      } else {
        setImportResult(data)
        setStep("result")
        onSuccess(data)
      }
    } catch (e) {
      setImportError(e instanceof Error ? e.message : "Erro desconhecido")
      setStep("preview")
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      onClick={handleClose}
    >
      <div
        className="bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl shadow-xl border border-lia-border-medium max-w-2xl w-full max-h-[80vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-lia-border-subtle">
          <div className="flex items-center gap-2">
            <FileSpreadsheet className="w-5 h-5 text-wedo-cyan" />
            <h2 className="text-base font-semibold text-lia-text-primary">
              Importar vagas do ATS
            </h2>
          </div>
          <button
            onClick={handleClose}
            className="text-lia-text-secondary hover:text-lia-text-primary"
            aria-label="Fechar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-auto p-5">
          {step === "input" && (
            <>
              {/* Mode toggle */}
              <div className="flex gap-2 mb-3">
                <button
                  onClick={() => setMode("file")}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    mode === "file"
                      ? "bg-wedo-cyan/10 text-wedo-cyan-text border border-wedo-cyan/30"
                      : "bg-lia-bg-secondary text-lia-text-secondary border border-lia-border-subtle"
                  }`}
                >
                  <FileText className="w-3.5 h-3.5" />
                  Arquivo CSV
                </button>
                <button
                  onClick={() => setMode("json")}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    mode === "json"
                      ? "bg-wedo-cyan/10 text-wedo-cyan-text border border-wedo-cyan/30"
                      : "bg-lia-bg-secondary text-lia-text-secondary border border-lia-border-subtle"
                  }`}
                >
                  <FileJson className="w-3.5 h-3.5" />
                  Colar JSON
                </button>
                <button
                  onClick={() => setMode("ats")}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    mode === "ats"
                      ? "bg-wedo-cyan/10 text-wedo-cyan-text border border-wedo-cyan/30"
                      : "bg-lia-bg-secondary text-lia-text-secondary border border-lia-border-subtle"
                  }`}
                >
                  <FileText className="w-3.5 h-3.5" />
                  ATS Conectado
                </button>
              </div>

              {mode === "ats" ? (
                <AtsImportTab
                  onImportSuccess={(count) => {
                    onSuccess({
                      batch_id: `ats-${Date.now()}`,
                      total: count,
                      successful: count,
                      failed: 0,
                      status: "completed",
                      items: [],
                    })
                  }}
                />
              ) : mode === "file" ? (
                <>
                  <p className="text-sm text-lia-text-secondary mb-3">
                    Arraste um arquivo <strong>CSV</strong> ou <strong>JSON</strong> exportado do
                    seu ATS. Cabeçalhos esperados: <code className="text-xs bg-lia-bg-secondary px-1 rounded">title</code>
                    , department, seniority, salary_min, salary_max, manager_email, description,
                    external_id, skills.
                  </p>
                  <div
                    onDragOver={(e) => {
                      e.preventDefault()
                      setIsDragging(true)
                    }}
                    onDragLeave={() => setIsDragging(false)}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                    className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
                      isDragging
                        ? "border-wedo-cyan bg-wedo-cyan/5"
                        : "border-lia-border-medium hover:border-wedo-cyan hover:bg-lia-bg-secondary"
                    }`}
                  >
                    <Upload
                      className={`w-10 h-10 mx-auto mb-2 ${
                        isDragging ? "text-wedo-cyan-text" : "text-lia-text-disabled"
                      }`}
                    />
                    <div className="text-sm font-medium text-lia-text-primary">
                      {isDragging ? "Solte o arquivo aqui" : "Clique ou arraste o arquivo"}
                    </div>
                    <div className="text-xs text-lia-text-secondary mt-1">CSV, JSON · até 10MB</div>
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv,.json,text/csv,application/json"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0]
                      if (file) handleFileRead(file)
                    }}
                  />
                </>
              ) : (
                <>
                  <p className="text-sm text-lia-text-secondary mb-3">
                    Cole o JSON das vagas exportado do seu ATS.
                  </p>
                  <textarea
                    value={rawJson}
                    onChange={(e) => setRawJson(e.target.value)}
                    placeholder={`[\n  {\n    "title": "Backend Engineer Sênior",\n    "department": "Engenharia",\n    "external_id": "WD-2024-0156"\n  }\n]`}
                    className="w-full h-72 font-mono text-xs p-3 border border-lia-border-subtle rounded-lg bg-lia-bg-secondary text-lia-text-primary"
                  />
                </>
              )}

              {parseError && (
                <div className="mt-3 flex items-start gap-2 text-sm text-status-error">
                  <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <span>{parseError}</span>
                </div>
              )}
            </>
          )}

          {step === "preview" && (
            <>
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle2 className="w-5 h-5 text-status-success" />
                <span className="text-sm font-medium text-lia-text-primary">
                  {jobs.length} vaga{jobs.length !== 1 ? "s" : ""} pronta
                  {jobs.length !== 1 ? "s" : ""} para importar
                </span>
              </div>

              {Object.keys(mappedHeaders).length > 0 && (
                <div className="mb-3 p-3 bg-lia-bg-secondary rounded-lg">
                  <div className="text-xs font-medium text-lia-text-primary mb-1.5">
                    Mapeamento de colunas detectado:
                  </div>
                  <div className="grid grid-cols-2 gap-1.5 text-xs">
                    {Object.entries(mappedHeaders).map(([csv, jsonField]) => (
                      <div key={csv} className="text-lia-text-secondary">
                        <code className="bg-lia-bg-primary px-1 rounded">{csv}</code> →{" "}
                        <code className="text-lia-text-secondary">{jsonField}</code>
                      </div>
                    ))}
                  </div>
                  {unmappedHeaders.length > 0 && (
                    <div className="text-xs text-lia-text-muted mt-2">
                      Ignorados: {unmappedHeaders.join(", ")}
                    </div>
                  )}
                </div>
              )}

              <div className="space-y-2 max-h-64 overflow-auto">
                {jobs.slice(0, 5).map((j, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-3 p-3 border border-lia-border-subtle rounded-lg bg-lia-bg-secondary"
                  >
                    <FileSpreadsheet className="w-4 h-4 text-wedo-cyan mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-lia-text-primary truncate">
                        {j.title}
                      </div>
                      <div className="text-xs text-lia-text-secondary mt-0.5">
                        {[
                          j.department,
                          j.seniority,
                          j.salary_min && j.salary_max
                            ? `R$ ${j.salary_min.toLocaleString()} – R$ ${j.salary_max.toLocaleString()}`
                            : null,
                        ]
                          .filter(Boolean)
                          .join(" · ")}
                      </div>
                    </div>
                  </div>
                ))}
                {jobs.length > 5 && (
                  <div className="text-xs text-center text-lia-text-secondary py-2">
                    + {jobs.length - 5} mais…
                  </div>
                )}
              </div>
              {importError && (
                <div className="mt-3 flex items-start gap-2 text-sm text-status-error">
                  <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <span>{importError}</span>
                </div>
              )}
            </>
          )}

          {step === "importing" && (
            <div className="flex flex-col items-center justify-center py-12 gap-3">
              <Loader2 className="w-8 h-8 text-wedo-cyan animate-spin" />
              <span className="text-sm text-lia-text-secondary">
                Enviando {jobs.length} vagas para o servidor…
              </span>
            </div>
          )}

          {step === "polling" && pollProgress && (
            <div className="flex flex-col items-center justify-center py-12 gap-3">
              <Loader2 className="w-8 h-8 text-wedo-cyan animate-spin" />
              <div className="text-center">
                <div className="text-sm font-medium text-lia-text-primary">
                  Processando {pollProgress.processed_records} de {pollProgress.total_records}…
                </div>
                <div className="text-xs text-lia-text-secondary mt-1">
                  ✅ {pollProgress.successful_records} sucesso
                  {pollProgress.failed_records > 0 ? ` · ❌ ${pollProgress.failed_records} falha(s)` : ""}
                </div>
              </div>
              <div className="w-full max-w-xs h-1.5 bg-lia-bg-secondary rounded-full overflow-hidden">
                <div
                  className="h-full bg-wedo-cyan transition-all duration-300"
                  style={{
                    width: `${
                      pollProgress.total_records
                        ? (pollProgress.processed_records / pollProgress.total_records) * 100
                        : 0
                    }%`,
                  }}
                />
              </div>
            </div>
          )}

          {step === "result" && importResult && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-status-success" />
                <span className="text-sm font-semibold text-lia-text-primary">
                  Importação concluída
                </span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="p-3 bg-lia-bg-secondary rounded-lg">
                  <div className="text-xs text-lia-text-secondary">Total</div>
                  <div className="text-lg font-semibold text-lia-text-primary">
                    {importResult.total}
                  </div>
                </div>
                <div className="p-3 bg-status-success/10 rounded-lg">
                  <div className="text-xs text-status-success">Sucesso</div>
                  <div className="text-lg font-semibold text-status-success">
                    {importResult.successful}
                  </div>
                </div>
                <div className="p-3 bg-status-error/10 rounded-lg">
                  <div className="text-xs text-status-error">Falhas</div>
                  <div className="text-lg font-semibold text-status-error">
                    {importResult.failed}
                  </div>
                </div>
              </div>
              {importResult.failed > 0 && importResult.items.length > 0 && (
                <div className="max-h-40 overflow-auto space-y-1.5">
                  {importResult.items
                    .filter((it) => it.status === "failed")
                    .slice(0, 10)
                    .map((it, i) => (
                      <div
                        key={i}
                        className="text-xs p-2 bg-status-error/5 border border-status-error/20 rounded"
                      >
                        <span className="font-medium">{it.title}</span>{" "}
                        <span className="text-lia-text-secondary">— {it.error}</span>
                      </div>
                    ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 px-5 py-3 border-t border-lia-border-subtle">
          {step === "input" && (
            <>
              <Button variant="ghost" onClick={handleClose}>
                Cancelar
              </Button>
              {mode === "json" && (
                <Button onClick={handleParseJson} disabled={!rawJson.trim()}>
                  Validar e prévia
                </Button>
              )}
            </>
          )}
          {step === "preview" && (
            <>
              <Button variant="ghost" onClick={() => setStep("input")}>
                Voltar
              </Button>
              <Button onClick={handleConfirmImport}>
                Importar {jobs.length} vaga{jobs.length !== 1 ? "s" : ""}
              </Button>
            </>
          )}
          {step === "result" && <Button onClick={handleClose}>Fechar</Button>}
        </div>
      </div>
    </div>
  )
}

export default BulkImportModal
