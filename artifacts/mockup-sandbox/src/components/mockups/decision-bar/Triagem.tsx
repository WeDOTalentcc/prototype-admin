import { PreviewShell } from "./_shared"
import { CheckCircle2, XCircle, ChevronDown, Zap } from "lucide-react"

function DecisionBar() {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-[var(--wedo-purple,#9860D1)]" />
            <span className="text-[11px] font-semibold text-[var(--lia-text-primary,#000)]">Triagem</span>
          </div>
          <span className="text-[9px] text-[var(--lia-text-tertiary,#9CA3AF)]">·</span>
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-[var(--wedo-orange-light,rgba(209,153,96,0.1))] border border-[var(--wedo-orange,#D19960)]/30 rounded text-[9px] text-[var(--wedo-orange,#D19960)] font-medium">
            <Zap className="w-2.5 h-2.5" />
            Decisão pendente
          </span>
        </div>
        <button className="flex items-center gap-1 px-2 py-1 text-[10px] text-[var(--lia-btn-secondary-text,#6B7280)] hover:bg-[var(--lia-btn-secondary-hover,#F3F4F6)] rounded border border-[var(--lia-btn-secondary-border,#E5E7EB)]">
          <ChevronDown className="w-3 h-3" />
          Mover para
        </button>
      </div>

      <div className="flex items-center gap-2">
        <button className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 bg-[var(--lia-btn-primary-bg,#111827)] hover:bg-[var(--lia-btn-primary-hover,#000)] text-[var(--lia-btn-primary-text,#fff)] text-[11px] font-medium rounded-md transition-colors">
          <CheckCircle2 className="w-3.5 h-3.5" />
          Aprovar
        </button>
        <button className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 bg-[var(--lia-bg-primary,#fff)] hover:bg-[var(--lia-brand-primary-light,#FEF2F2)] text-[var(--lia-destructive-bg,#C74446)] text-[11px] font-medium rounded-md border border-[var(--lia-destructive-border,#C74446)]/30 transition-colors">
          <XCircle className="w-3.5 h-3.5" />
          Reprovar
        </button>
      </div>
    </div>
  )
}

export function Triagem() {
  return (
    <PreviewShell
      candidateName="Gustavo Pereira"
      candidateRole="Tech Lead Mobile"
      candidateCompany="XP Inc."
      stage="Triagem"
      stageColor="var(--wedo-purple, #9860D1)"
      subStatus="Decisão pendente"
      isFavorite
      decisionBar={<DecisionBar />}
      highlight={
        <span>
          <strong>Tech Lead Mobile</strong> com 8 anos de experiência em React Native e Flutter na XP Inc.
          Liderou equipes de até 12 devs, certificações AWS/GCP. Score WSI: 82%.
        </span>
      }
    />
  )
}
