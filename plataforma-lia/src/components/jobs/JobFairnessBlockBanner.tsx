"use client"

import { useEffect, useState } from "react"
import { AlertTriangle, ShieldAlert, ChevronDown, ChevronUp } from "lucide-react"

interface FairnessBlockEntry {
  id: string
  category: string | null
  educational_message: string | null
  blocked_terms: string[]
  soft_warnings: string[]
  is_blocked: boolean
  context: string | null
  created_at: string
}

interface FairnessBlocksResponse {
  job_id: string
  total: number
  limit: number
  offset: number
  latest_block: FairnessBlockEntry | null
  items: FairnessBlockEntry[]
}

const CATEGORY_LABELS: Record<string, string> = {
  genero: "Gênero",
  raca_etnia: "Raça/Etnia",
  idade: "Idade",
  religiao: "Religião",
  orientacao_sexual: "Orientação sexual",
  estado_civil: "Estado civil",
  deficiencia: "Deficiência",
  maternidade_paternidade: "Maternidade/Paternidade",
  nacionalidade: "Nacionalidade",
  antecedentes_criminais: "Antecedentes criminais",
  saude_doenca: "Saúde/Doença",
  filiacao_sindical: "Filiação sindical",
  aparencia_fisica: "Aparência física",
}

function formatCategory(category: string | null): string {
  if (!category) return "Critério restrito"
  return CATEGORY_LABELS[category] || category.replace(/_/g, " ")
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  } catch {
    return iso
  }
}

export function JobFairnessBlockBanner({ jobId }: { jobId: string }) {
  const [data, setData] = useState<FairnessBlocksResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [showHistory, setShowHistory] = useState(false)

  useEffect(() => {
    if (!jobId) {
      setLoading(false)
      return
    }
    let aborted = false
    setLoading(true)
    fetch(`/api/backend-proxy/fairness/jobs/${encodeURIComponent(jobId)}/blocks?limit=20`)
      .then(async (res) => (res.ok ? ((await res.json()) as FairnessBlocksResponse) : null))
      .then((json) => {
        if (!aborted) setData(json)
      })
      .catch(() => {
        if (!aborted) setData(null)
      })
      .finally(() => {
        if (!aborted) setLoading(false)
      })
    return () => {
      aborted = true
    }
  }, [jobId])

  if (loading || !data || !data.latest_block) {
    return null
  }

  const block = data.latest_block
  const history = data.items.filter((it) => it.id !== block.id)

  return (
    <div
      role="alert"
      aria-live="polite"
      data-testid="job-fairness-block-banner"
      className="mx-3 my-3 rounded-xl border border-status-error/30 bg-status-error/10 p-4"
    >
      <div className="flex items-start gap-3">
        <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-status-error" aria-hidden />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-status-error">
            Busca bloqueada por critério discriminatório:{" "}
            <span className="underline underline-offset-2">{formatCategory(block.category)}</span>
          </p>
          {block.educational_message ? (
            <p className="mt-1 text-xs text-status-error/90 leading-relaxed">
              {block.educational_message}
            </p>
          ) : null}
          {block.blocked_terms.length > 0 ? (
            <p className="mt-2 text-[11px] text-status-error/80">
              Termos identificados: {block.blocked_terms.slice(0, 5).join(", ")}
            </p>
          ) : null}
          <p className="mt-2 text-[11px] text-status-error/70">
            Bloqueado em {formatDate(block.created_at)}.
            {data.total > 1 ? ` ${data.total} bloqueios registrados nesta vaga.` : ""}
          </p>

          {history.length > 0 ? (
            <div className="mt-3">
              <button
                type="button"
                onClick={() => setShowHistory((v) => !v)}
                aria-expanded={showHistory}
                className="inline-flex items-center gap-1 text-[11px] font-medium text-status-error hover:underline focus:outline-none focus:ring-2 focus:ring-status-error/40 rounded"
              >
                {showHistory ? (
                  <>
                    <ChevronUp className="h-3 w-3" /> Ocultar histórico
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-3 w-3" /> Ver histórico ({history.length})
                  </>
                )}
              </button>

              {showHistory ? (
                <ul className="mt-2 space-y-1.5" data-testid="job-fairness-block-history">
                  {history.map((it) => (
                    <li
                      key={it.id}
                      className="flex items-start gap-2 rounded-md bg-status-error/5 px-2 py-1.5 text-[11px] text-status-error/90"
                    >
                      <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" aria-hidden />
                      <div className="min-w-0">
                        <span className="font-medium">{formatCategory(it.category)}</span>
                        <span className="ml-1 text-status-error/70">
                          · {formatDate(it.created_at)}
                        </span>
                        {it.blocked_terms.length > 0 ? (
                          <div className="text-status-error/70">
                            Termos: {it.blocked_terms.slice(0, 4).join(", ")}
                          </div>
                        ) : null}
                      </div>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}
