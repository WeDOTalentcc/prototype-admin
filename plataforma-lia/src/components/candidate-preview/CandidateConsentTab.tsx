"use client"

import { useState, useMemo, useCallback } from "react"
import { useQuery } from "@tanstack/react-query"
import { textStyles } from "@/lib/design-tokens"
import { Chip } from "@/components/ui/chip"
import { Button } from "@/components/ui/button"
import {
  ShieldCheck, ChevronDown, Download,
} from "lucide-react"

// ── Types ─────────────────────────────────────────────────────────────────────
export interface ConsentRecord {
  id: string
  consent_type: string
  purpose?: string | null
  legal_basis?: string | null
  channel?: string | null
  granted_at?: string | null
  version?: string | null
  is_active: boolean
  revoked_at?: string | null
  expires_at?: string | null
  source?: string | null
}

interface ConsentApiResponse {
  data?: ConsentRecord[]
  records?: ConsentRecord[]
  items?: ConsentRecord[]
}

// ── Label maps ────────────────────────────────────────────────────────────────
const CONSENT_TYPE_LABELS: Record<string, string> = {
  consentimento_audio: "Áudio da triagem",
  consentimento_audio_revoked: "Áudio revogado",
  dados_sensiveis_acao_afirmativa: "Dados de ação afirmativa",
  comunicacao: "Comunicação",
}

const CANAL_LABELS: Record<string, string> = {
  chat_web: "Chat web",
  whatsapp: "WhatsApp",
  chamada_online: "Chamada online",
  chamada_telefonica: "Chamada telefônica",
}

function labelConsentType(raw: string): string {
  return CONSENT_TYPE_LABELS[raw] ?? raw
}

function labelCanal(raw: string | null | undefined): string {
  if (!raw) return "—"
  return CANAL_LABELS[raw] ?? raw
}

function formatDatePt(raw: string | null | undefined): string {
  if (!raw) return "—"
  try {
    return new Date(raw).toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    })
  } catch {
    return raw
  }
}

// ── Status chip ───────────────────────────────────────────────────────────────
function ConsentStatusChip({ record }: { record: ConsentRecord }) {
  const now = new Date()
  const isExpired =
    !!record.expires_at && new Date(record.expires_at) < now && record.is_active
  const isRevoked = !!record.revoked_at

  if (isRevoked) {
    return (
      <Chip
        variant="danger"
        muted
        className="text-micro px-1.5 py-0 h-4 flex items-center gap-0.5"
      >
        Revogado
      </Chip>
    )
  }
  if (isExpired) {
    return (
      <Chip
        variant="neutral"
        muted
        className="text-micro px-1.5 py-0 h-4 flex items-center gap-0.5 bg-lia-bg-tertiary text-lia-text-secondary"
      >
        Expirado
      </Chip>
    )
  }
  if (record.is_active) {
    return (
      <Chip
        variant="success"
        muted
        className="text-micro px-1.5 py-0 h-4 flex items-center gap-0.5 bg-status-success/10 text-status-success"
      >
        Ativo
      </Chip>
    )
  }
  return (
    <Chip
      variant="neutral"
      muted
      className="text-micro px-1.5 py-0 h-4 flex items-center gap-0.5 bg-lia-bg-tertiary text-lia-text-secondary"
    >
      Inativo
    </Chip>
  )
}

// ── CSV export ────────────────────────────────────────────────────────────────
function exportToCsv(records: ConsentRecord[], candidateId: string) {
  const headers = [
    "Tipo",
    "Propósito",
    "Base Legal",
    "Canal",
    "Data",
    "Versão",
    "Status",
    "Origem",
  ]
  const rows = records.map((r) => {
    const status = r.revoked_at ? "Revogado" : r.is_active ? "Ativo" : "Inativo"
    return [
      labelConsentType(r.consent_type),
      r.purpose ?? "",
      r.legal_basis ?? "",
      labelCanal(r.channel),
      formatDatePt(r.granted_at),
      r.version ?? "",
      status,
      r.source ?? "",
    ]
  })

  const csvContent = [headers, ...rows]
    .map((row) =>
      row
        .map((cell) => `"${String(cell).replace(/"/g, '""')}"`)
        .join(",")
    )
    .join("\n")

  const blob = new Blob(["﻿" + csvContent], { type: "text/csv;charset=utf-8;" })
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.setAttribute("href", url)
  link.setAttribute("download", `consentimentos-${candidateId}.csv`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

// ── Filter options ────────────────────────────────────────────────────────────
const FILTER_ALL = "all"

// ── Main component ────────────────────────────────────────────────────────────
interface CandidateConsentTabProps {
  candidateId: string
  onShowConsentHistory?: () => void
}

export function CandidateConsentTab({ candidateId }: CandidateConsentTabProps) {
  const [filterType, setFilterType] = useState<string>(FILTER_ALL)
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const { data, isLoading, isError, refetch } = useQuery<ConsentRecord[]>({
    queryKey: ["candidate-consents", candidateId],
    queryFn: async () => {
      const res = await fetch(
        `/api/backend-proxy/observability/consents/${candidateId}`
      )
      if (!res.ok) {
        if (res.status === 404) return []
        throw new Error(`HTTP ${res.status}`)
      }
      const body: ConsentApiResponse = await res.json()
      return body.data ?? body.records ?? body.items ?? (Array.isArray(body) ? body : [])
    },
    staleTime: 30_000,
    enabled: !!candidateId,
  })

  const records = useMemo(() => data ?? [], [data])

  // Unique consent types for filter chips
  const consentTypes = useMemo(() => {
    const seen = new Set<string>()
    for (const r of records) seen.add(r.consent_type)
    return Array.from(seen)
  }, [records])

  const filteredRecords = useMemo(
    () =>
      filterType === FILTER_ALL
        ? records
        : records.filter((r) => r.consent_type === filterType),
    [records, filterType]
  )

  const handleExport = useCallback(() => {
    exportToCsv(filteredRecords, candidateId)
  }, [filteredRecords, candidateId])

  // ── Loading ──────────────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div
        className="flex items-center justify-center py-10"
        role="status"
        aria-live="polite"
      >
        <div className="animate-spin motion-reduce:animate-none rounded-full h-5 w-5 border-2 border-lia-border-medium border-t-transparent mr-2" />
        <span className="text-xs text-lia-text-secondary">
          Carregando registros de consentimento...
        </span>
      </div>
    )
  }

  // ── Error ────────────────────────────────────────────────────────────────────
  if (isError) {
    return (
      <div className="p-4 flex flex-col items-center gap-3">
        <div
          className="flex items-center gap-2 p-3 rounded-lg bg-status-error/10 border border-status-error/20 w-full"
          role="alert"
        >
          <span className="text-xs text-status-error">
            Erro ao carregar consentimentos. Tente novamente.
          </span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => refetch()}
          className="text-xs h-7"
        >
          Tentar novamente
        </Button>
      </div>
    )
  }

  // ── Empty ────────────────────────────────────────────────────────────────────
  if (records.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-4 gap-3">
        <div className="w-10 h-10 rounded-full bg-lia-bg-tertiary flex items-center justify-center">
          <ShieldCheck className="w-5 h-5 text-lia-text-tertiary" />
        </div>
        <p className="text-xs text-lia-text-secondary text-center">
          Nenhum registro de consentimento encontrado para este candidato.
        </p>
      </div>
    )
  }

  // ── Main render ──────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col h-full" data-testid="candidate-consent-tab">
      {/* Header */}
      <div className="p-3 bg-lia-bg-primary border-b border-lia-border-subtle">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-xs font-medium text-lia-text-primary flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-lia-text-primary" />
            Consentimentos LGPD
            <Chip
              variant="neutral"
              muted
              className="text-micro px-1.5 py-0 h-4 flex items-center"
            >
              {filteredRecords.length}
            </Chip>
          </h4>
          <Button
            size="sm"
            variant="ghost"
            className="gap-1 px-2 py-1 text-xs h-6 bg-lia-bg-tertiary hover:bg-lia-interactive-active text-lia-text-secondary border border-lia-border-subtle"
            onClick={handleExport}
            disabled={filteredRecords.length === 0}
          >
            <Download className="w-3 h-3" />
            Exportar CSV
          </Button>
        </div>

        {/* Filter chips */}
        <div className="flex gap-1 flex-wrap">
          <Chip
            variant="neutral"
            className={`text-micro px-1.5 py-0 h-4 flex items-center cursor-pointer hover:bg-lia-interactive-hover ${
              filterType === FILTER_ALL ? "bg-lia-bg-tertiary" : ""
            }`}
            onClick={() => setFilterType(FILTER_ALL)}
          >
            Todos ({records.length})
          </Chip>
          {consentTypes.map((ct) => (
            <Chip
              key={ct}
              variant="neutral"
              className={`text-micro px-1.5 py-0 h-4 flex items-center cursor-pointer hover:bg-lia-interactive-hover ${
                filterType === ct ? "bg-lia-bg-tertiary" : ""
              }`}
              onClick={() => setFilterType(filterType === ct ? FILTER_ALL : ct)}
            >
              {labelConsentType(ct)}
            </Chip>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {filteredRecords.map((record) => {
          const isExpanded = expandedId === record.id
          return (
            <div
              key={record.id}
              className="border border-lia-border-subtle rounded-xl transition-colors motion-reduce:transition-none"
            >
              <div
                className="p-2.5 cursor-pointer hover:bg-lia-bg-primary dark:hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none"
                onClick={() => setExpandedId(isExpanded ? null : record.id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault()
                    setExpandedId(isExpanded ? null : record.id)
                  }
                }}
                aria-expanded={isExpanded}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className={`${textStyles.bodySmall} font-medium`}>
                        {labelConsentType(record.consent_type)}
                      </span>
                      <ConsentStatusChip record={record} />
                    </div>
                    <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                      <span className={textStyles.bodySmall}>
                        {labelCanal(record.channel)}
                      </span>
                      {record.granted_at && (
                        <>
                          <span className="text-lia-text-tertiary text-micro">•</span>
                          <span className={textStyles.bodySmall}>
                            {formatDatePt(record.granted_at)}
                          </span>
                        </>
                      )}
                      {record.version && (
                        <>
                          <span className="text-lia-text-tertiary text-micro">•</span>
                          <span className={`${textStyles.bodySmall} text-lia-text-secondary`}>
                            v{record.version}
                          </span>
                        </>
                      )}
                    </div>
                    {record.legal_basis && (
                      <p className="text-micro text-lia-text-tertiary mt-0.5">
                        {record.legal_basis}
                      </p>
                    )}
                  </div>
                  <ChevronDown
                    className={`w-3.5 h-3.5 text-lia-text-secondary flex-shrink-0 transition-transform motion-reduce:transition-none ${
                      isExpanded ? "rotate-180" : ""
                    }`}
                  />
                </div>
              </div>

              {/* Expanded details */}
              {isExpanded && (
                <div className="px-2.5 pb-2.5 border-t border-lia-border-subtle pt-2 space-y-1">
                  {[
                    {
                      label: "Propósito",
                      value: record.purpose,
                    },
                    {
                      label: "Base legal",
                      value: record.legal_basis,
                    },
                    {
                      label: "Canal",
                      value: labelCanal(record.channel),
                    },
                    {
                      label: "Data de concessão",
                      value: formatDatePt(record.granted_at),
                    },
                    {
                      label: "Expiração",
                      value: formatDatePt(record.expires_at),
                    },
                    {
                      label: "Revogado em",
                      value: formatDatePt(record.revoked_at),
                    },
                    {
                      label: "Versão",
                      value: record.version,
                    },
                    {
                      label: "Origem",
                      value: record.source,
                    },
                  ]
                    .filter(({ value }) => !!value && value !== "—")
                    .map(({ label, value }) => (
                      <div key={label} className="flex items-start justify-between gap-2">
                        <span className="text-micro text-lia-text-tertiary flex-shrink-0">
                          {label}
                        </span>
                        <span className="text-micro text-lia-text-secondary text-right">
                          {value}
                        </span>
                      </div>
                    ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
