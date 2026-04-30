"use client"

import React, { useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { Upload, X, Loader2, CheckCircle2, AlertTriangle, FileText } from "lucide-react"

interface ImportJobsDrawerProps {
  open: boolean
  onClose: () => void
  onImportComplete: () => void
}

type ImportStep = "select" | "uploading" | "done" | "error"

interface BatchStatus {
  batch_id: string
  total: number
  successful: number
  failed: number
  status: string
}

export function ImportJobsDrawer({ open, onClose, onImportComplete }: ImportJobsDrawerProps) {
  const [step, setStep] = useState<ImportStep>("select")
  const [batchStatus, setBatchStatus] = useState<BatchStatus | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  if (!open) return null

  async function handleAtsConnect(source: "gupy" | "pandape") {
    setStep("uploading")
    setErrorMsg(null)
    try {
      const res = await fetch(`/api/backend-proxy/ats/connections/sync`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider: source }),
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setBatchStatus({
        batch_id: data.batch_id || "",
        total: data.total || 0,
        successful: data.successful || data.total || 0,
        failed: data.failed || 0,
        status: "completed",
      })
      setStep("done")
      onImportComplete()
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Erro ao conectar com ATS")
      setStep("error")
    }
  }

  async function handleFileUpload(file: File) {
    setStep("uploading")
    setErrorMsg(null)
    try {
      // Parse CSV/XLSX into JSON rows — basic CSV parse for MVP
      const text = await file.text()
      const lines = text.split("\n").filter(Boolean)
      const headers = lines[0].split(",").map((h) => h.trim().toLowerCase().replace(/"/g, ""))
      const jobs = lines.slice(1).map((line) => {
        const cols = line.split(",").map((c) => c.trim().replace(/"/g, ""))
        const obj: Record<string, string> = {}
        headers.forEach((h, i) => { if (cols[i]) obj[h] = cols[i] })
        return {
          title: obj["title"] || obj["titulo"] || obj["job_title"] || "",
          department: obj["department"] || obj["departamento"] || undefined,
          seniority: obj["seniority"] || obj["senioridade"] || undefined,
          salary_min: obj["salary_min"] || obj["salario_min"] ? Number(obj["salary_min"] || obj["salario_min"]) : undefined,
          salary_max: obj["salary_max"] || obj["salario_max"] ? Number(obj["salary_max"] || obj["salario_max"]) : undefined,
        }
      }).filter((j) => j.title)

      if (jobs.length === 0) {
        throw new Error("Nenhuma vaga encontrada. Verifique se o CSV tem coluna 'title' ou 'titulo'.")
      }

      const res = await fetch("/api/backend-proxy/jobs/bulk-import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: "spreadsheet", jobs }),
      })

      const data = await res.json()
      setBatchStatus({
        batch_id: data.batch_id,
        total: data.total,
        successful: data.successful,
        failed: data.failed,
        status: data.status,
      })
      setStep(data.failed > 0 ? "error" : "done")
      if (data.failed === 0) onImportComplete()
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Erro ao importar arquivo")
      setStep("error")
    }
  }

  function handleReset() {
    setStep("select")
    setBatchStatus(null)
    setErrorMsg(null)
  }

  return (
    <div className="fixed inset-0 z-50 flex" role="dialog" aria-modal="true" aria-label="Importar vagas históricas">
      <div className="flex-1 bg-black/30" onClick={onClose} />
      <aside className="w-[400px] max-w-full bg-lia-bg-primary border-l border-lia-border-default shadow-xl flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-lia-border-default flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Upload className="w-4 h-4 text-wedo-cyan" />
            <h2 className="text-sm font-semibold text-lia-text-primary">Importar vagas históricas</h2>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose} aria-label="Fechar">
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 text-sm">
          {step === "select" && (
            <>
              <p className="text-xs text-lia-text-secondary mb-4">
                Importe vagas anteriores para que a LIA tenha contexto desde o dia 1.
                Vagas com faixa salarial alimentam o benchmark de mercado automaticamente.
              </p>

              {/* ATS options */}
              <button
                className="w-full flex items-center gap-3 p-3 rounded-lg border border-lia-border-default hover:border-wedo-cyan hover:bg-lia-bg-elevated transition-colors text-left"
                onClick={() => handleAtsConnect("gupy")}
              >
                <span className="w-8 h-8 rounded-md bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-xs">G</span>
                <div>
                  <div className="font-medium text-lia-text-primary">Conectar Gupy</div>
                  <div className="text-[11px] text-lia-text-secondary">Sincroniza vagas fechadas automaticamente</div>
                </div>
              </button>

              <button
                className="w-full flex items-center gap-3 p-3 rounded-lg border border-lia-border-default hover:border-wedo-cyan hover:bg-lia-bg-elevated transition-colors text-left"
                onClick={() => handleAtsConnect("pandape")}
              >
                <span className="w-8 h-8 rounded-md bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-xs">P</span>
                <div>
                  <div className="font-medium text-lia-text-primary">Conectar Pandapé</div>
                  <div className="text-[11px] text-lia-text-secondary">Sincroniza vagas fechadas automaticamente</div>
                </div>
              </button>

              {/* CSV upload */}
              <div
                className="w-full flex flex-col items-center gap-2 p-4 rounded-lg border-2 border-dashed border-lia-border-default hover:border-wedo-cyan transition-colors cursor-pointer"
                onClick={() => fileRef.current?.click()}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault()
                  const file = e.dataTransfer.files[0]
                  if (file) handleFileUpload(file)
                }}
              >
                <FileText className="w-6 h-6 text-lia-text-tertiary" />
                <span className="text-xs font-medium text-lia-text-primary">Upload planilha CSV</span>
                <span className="text-[11px] text-lia-text-secondary">Colunas: title, department, seniority, salary_min, salary_max</span>
                <input
                  ref={fileRef}
                  type="file"
                  accept=".csv"
                  className="hidden"
                  onChange={(e) => { if (e.target.files?.[0]) handleFileUpload(e.target.files[0]) }}
                />
              </div>
            </>
          )}

          {step === "uploading" && (
            <div className="flex flex-col items-center gap-3 py-8">
              <Loader2 className="w-8 h-8 animate-spin text-wedo-cyan" />
              <span className="text-sm text-lia-text-secondary">Importando vagas…</span>
            </div>
          )}

          {step === "done" && batchStatus && (
            <div className="flex flex-col items-center gap-3 py-6">
              <CheckCircle2 className="w-10 h-10 text-status-success" />
              <h3 className="text-base font-semibold text-lia-text-primary">Importação concluída!</h3>
              <div className="text-center text-xs text-lia-text-secondary space-y-1">
                <p><strong className="text-lia-text-primary">{batchStatus.total}</strong> vagas processadas</p>
                <p><strong className="text-status-success">{batchStatus.successful}</strong> importadas com sucesso</p>
                {batchStatus.failed > 0 && (
                  <p><strong className="text-status-error">{batchStatus.failed}</strong> com erro (ignoradas)</p>
                )}
              </div>
              <p className="text-[11px] text-lia-text-tertiary text-center mt-2">
                Vagas com faixa salarial já estão disponíveis no benchmark. 
                Acompanhe o progresso no Hub de Prontidão abaixo.
              </p>
              <Button size="sm" onClick={onClose} className="mt-2">Fechar</Button>
            </div>
          )}

          {step === "error" && (
            <div className="flex flex-col items-center gap-3 py-6">
              <AlertTriangle className="w-8 h-8 text-status-warning" />
              {batchStatus && batchStatus.failed > 0 ? (
                <>
                  <h3 className="text-sm font-semibold text-lia-text-primary">Importação parcial</h3>
                  <p className="text-xs text-lia-text-secondary text-center">
                    <strong>{batchStatus.successful}</strong> de <strong>{batchStatus.total}</strong> vagas importadas.
                    {batchStatus.failed} com erro.
                  </p>
                  <Button size="sm" onClick={onClose} className="mt-2">Ver Hub de Prontidão</Button>
                </>
              ) : (
                <>
                  <h3 className="text-sm font-semibold text-lia-text-primary">Erro na importação</h3>
                  <p className="text-xs text-lia-text-secondary text-center">{errorMsg}</p>
                  <Button size="sm" variant="outline" onClick={handleReset} className="mt-2">Tentar novamente</Button>
                </>
              )}
            </div>
          )}
        </div>
      </aside>
    </div>
  )
}
