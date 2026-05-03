"use client"

/**
 * AtsImportSuggestionCard — Phase 4H empty state for the "ATS" rail filter.
 *
 * Visual contract replicates the suggestion card pattern from
 * `chat-workflow-reels.tsx` (lines 393-430): icon block + title + description
 * inside a bordered button. When the user clicks the rail's "ATS" filter and
 * has zero vagas with source='ats_import' / 'ats_external', this card invites
 * them to start importing.
 *
 * Wiring: parent (JobsListContent) renders this when:
 *   activeFilter === 'ats' && filteredJobs.length === 0
 * onClick triggers parent's setShowBulkImportModal(true).
 */
import React from "react"
import { Database, Upload, FileSpreadsheet } from "lucide-react"

interface AtsImportSuggestionCardProps {
  onImport: () => void
  onConnectAts?: () => void  // future: connect live ATS (Gupy, Greenhouse...)
}

const ACCENT = "var(--wedo-cyan, #60BED1)"
const ACCENT_BG = "rgba(96, 190, 209, 0.10)"
const CARD_BORDER = "rgba(96, 190, 209, 0.25)"
const NODE_BORDER = "var(--wedo-cyan, #60BED1)"

export function AtsImportSuggestionCard({
  onImport,
  onConnectAts,
}: AtsImportSuggestionCardProps) {
  return (
    <div className="w-full flex flex-col items-center justify-center py-12 gap-6">
      <div className="flex items-center gap-3">
        <div
          className="rounded-xl p-3"
          style={{ backgroundColor: ACCENT_BG, color: ACCENT }}
        >
          <Database className="w-6 h-6" />
        </div>
        <div className="text-center">
          <h3 className="text-lg font-semibold text-lia-text-primary">
            Não há vagas importadas do ATS
          </h3>
          <p className="text-sm text-lia-text-secondary mt-1">
            Importe vagas em massa do seu ATS atual para começar.
          </p>
        </div>
      </div>

      <div className="flex flex-wrap gap-3 justify-center max-w-2xl">
        {/* Card 1 — Import from spreadsheet (primary CTA) */}
        <button
          onClick={onImport}
          className="flex items-start gap-3 p-4 text-left rounded-xl bg-lia-bg-primary border transition-all duration-150 hover:-translate-y-0.5 group flex-1 min-w-[260px] max-w-[340px]"
          style={{ borderColor: CARD_BORDER }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = NODE_BORDER
            e.currentTarget.style.backgroundColor = ACCENT_BG
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = CARD_BORDER
            e.currentTarget.style.backgroundColor = "var(--lia-bg-primary)"
          }}
        >
          <div
            className="rounded-lg p-2 flex-shrink-0"
            style={{ backgroundColor: ACCENT_BG, color: ACCENT }}
          >
            <FileSpreadsheet className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <span className="text-[14px] font-semibold text-lia-text-primary block mb-0.5">
              Importar vagas do ATS
            </span>
            <span className="text-xs leading-snug text-lia-text-secondary block">
              Faça upload de planilha (CSV/Excel) com suas vagas históricas
              ou ativas. As vagas aparecerão como cards aqui.
            </span>
          </div>
        </button>

        {/* Card 2 — Connect live ATS (placeholder, future feature) */}
        {onConnectAts && (
          <button
            onClick={onConnectAts}
            className="flex items-start gap-3 p-4 text-left rounded-xl bg-lia-bg-primary border transition-all duration-150 hover:-translate-y-0.5 group flex-1 min-w-[260px] max-w-[340px]"
            style={{ borderColor: CARD_BORDER }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = NODE_BORDER
              e.currentTarget.style.backgroundColor = ACCENT_BG
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = CARD_BORDER
              e.currentTarget.style.backgroundColor = "var(--lia-bg-primary)"
            }}
          >
            <div
              className="rounded-lg p-2 flex-shrink-0"
              style={{ backgroundColor: ACCENT_BG, color: ACCENT }}
            >
              <Upload className="w-4 h-4" />
            </div>
            <div className="min-w-0">
              <span className="text-[14px] font-semibold text-lia-text-primary block mb-0.5">
                Conectar ATS ao vivo
              </span>
              <span className="text-xs leading-snug text-lia-text-secondary block">
                Sincronizar com Gupy, Greenhouse, Lever ou outros (em breve).
              </span>
            </div>
          </button>
        )}
      </div>
    </div>
  )
}

export default AtsImportSuggestionCard
