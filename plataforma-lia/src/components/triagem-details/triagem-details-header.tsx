"use client"

import { Brain, Download, X } from "lucide-react"
import type { Candidate } from "@/components/pages/candidates/types"
import type { WSIResultDetails, WSICandidateRanking } from "@/services/lia-api"
import { getClassificationLabel } from "./useTriagemDetailsState"
import { WSI_VISUAL_3TIER } from '@/lib/wsi/visual'

interface TriagemDetailsHeaderProps {
  candidate: Candidate
  details: WSIResultDetails
  ranking: WSICandidateRanking | null
  onClose: () => void
}

export function TriagemDetailsHeader({ candidate, details, ranking, onClose }: TriagemDetailsHeaderProps) {
  return (
    <div className="flex items-center justify-between px-4 py-3 bg-lia-bg-secondary">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-md flex items-center justify-center flex-shrink-0 bg-wedo-cyan/[0.12]">
          <Brain className="w-4 h-4 text-wedo-cyan" />
        </div>
        <div>
          <h2 className="text-base-ui font-semibold text-lia-text-primary">
            Detalhes da Triagem WSI - {candidate.name}
          </h2>
          <p className="text-xs text-lia-text-secondary">
            {candidate.role || candidate.current_title} {candidate.location ? `• ${candidate.location}` : ''}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-1.5">
        <button
          onClick={() => {
            if (!details) return
            const printWindow = window.open('', '_blank')
            if (!printWindow) return
            const respHtml = details.responses.map((resp, idx) => `
              <div style="margin-bottom:16px;padding:12px;border:1px solid #D4D4D4;border-radius:8px;">
                <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
                  <strong>${resp.competency}</strong>
                  <span style="font-weight:bold;color:${resp.scores.final_score >= WSI_VISUAL_3TIER.green ? 'var(--status-success)' : resp.scores.final_score >= WSI_VISUAL_3TIER.yellow ? 'var(--status-warning)' : 'var(--status-error)'}">${resp.scores.final_score.toFixed(1)}/10.0</span>
                </div>
                <p style="color:var(--lia-text-secondary);font-size:12px;margin-bottom:4px;"><strong>Pergunta:</strong> ${resp.question.text}</p>
                <p style="font-size:12px;margin-bottom:4px;"><strong>Resposta:</strong> ${resp.response_text}</p>
                <p style="font-size:12px;color:var(--lia-text-secondary);font-style:italic;">${resp.justification || ''}</p>
              </div>
            `).join('')
            printWindow.document.write(`
              <html><head><title>Triagem WSI - ${candidate.name}</title>
              <style>body{font-family:'Open Sans',sans-serif;padding:32px;color:var(--lia-text-primary);max-width:800px;margin:0 auto;}
              h1{font-size:20px;margin-bottom:4px;}h2{font-size:16px;margin-top:24px;margin-bottom:12px;color:var(--lia-text-primary);}
              .scores{display:flex;gap:24px;margin:16px 0;}.score-box{text-align:center;padding:12px 20px;border:1px solid #D4D4D4;border-radius:8px;}
              .score-box .value{font-size:24px;font-weight:bold;}.score-box .label{font-size:12px;color:var(--lia-text-secondary);}
              .meta{font-size:12px;color:var(--lia-text-secondary);margin-bottom:16px;}
              @media print{body{padding:16px;}}</style></head><body>
              <h1>Triagem WSI - ${candidate.name}</h1>
              <p class="meta">${candidate.role || candidate.current_title || ''} ${candidate.location ? '• ' + candidate.location : ''}</p>
              <div class="scores">
                <div class="score-box"><div class="value">${details.scores.overall_wsi.toFixed(1)}</div><div class="label">Score Geral</div></div>
                <div class="score-box"><div class="value">${details.scores.technical_wsi.toFixed(1)}</div><div class="label">Comp. Técnicas</div></div>
                <div class="score-box"><div class="value">${details.scores.behavioral_wsi.toFixed(1)}</div><div class="label">Comp. Comportamentais</div></div>
              </div>
              <p style="font-size:13px;"><strong>Classificação:</strong> ${getClassificationLabel(details.scores.classification)}
              ${ranking?.ranked ? ` | <strong>Ranking:</strong> #${ranking.rank} de ${ranking.total}` : ''}</p>
              <h2>Respostas por Competência</h2>${respHtml}
              ${details.report?.executive_summary ? '<h2>Sumário Executivo</h2><p style="font-size:13px;">' + details.report.executive_summary + '</p>' : ''}
              </body></html>
            `)
            printWindow.document.close()
            printWindow.print()
          }}
          className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium transition-colors motion-reduce:transition-none hover:bg-lia-bg-tertiary text-lia-text-primary border border-lia-border-subtle bg-lia-bg-secondary rounded-xl"
        >
          <Download className="w-3 h-3" />
          Exportar
        </button>
        <button onClick={onClose} className="h-7 w-7 p-0 flex items-center justify-center transition-colors motion-reduce:transition-none hover:bg-lia-interactive-hover rounded-full text-lia-text-secondary">
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}