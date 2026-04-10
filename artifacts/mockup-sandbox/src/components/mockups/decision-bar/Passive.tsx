import { PreviewShell } from "./_shared"
import { ChevronDown, ArrowRight, UserPlus, Star } from "lucide-react"

function DecisionBar() {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-[var(--wedo-cyan,#60BED1)]" />
            <span className="text-[11px] font-semibold text-[var(--lia-text-primary,#000)]">Short List</span>
          </div>
          <span className="text-[9px] text-[var(--lia-text-tertiary,#9CA3AF)]">·</span>
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-[var(--lia-bg-tertiary,#F3F4F6)] border border-[var(--lia-border-subtle,#E5E7EB)] rounded text-[9px] text-[var(--lia-text-secondary,#6B7280)] font-medium">
            Aguardando ação do recrutador
          </span>
        </div>
        <div className="flex items-center gap-1">
          <button className="flex items-center gap-1 px-2 py-1 text-[10px] text-[var(--lia-btn-secondary-text,#6B7280)] hover:bg-[var(--lia-btn-secondary-hover,#F3F4F6)] rounded border border-[var(--lia-btn-secondary-border,#E5E7EB)]">
            <ChevronDown className="w-3 h-3" />
            Mover para
          </button>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button className="flex items-center justify-center gap-1.5 px-3 py-1.5 bg-[var(--lia-btn-primary-bg,#111827)] hover:bg-[var(--lia-btn-primary-hover,#000)] text-[var(--lia-btn-primary-text,#fff)] text-[11px] font-medium rounded-md transition-colors">
          <ArrowRight className="w-3.5 h-3.5" />
          Avançar p/ Entrevista
        </button>
        <button className="flex items-center justify-center gap-1 px-2.5 py-1.5 bg-[var(--lia-bg-primary,#fff)] hover:bg-[var(--lia-btn-secondary-hover,#F3F4F6)] text-[var(--lia-text-primary,#000)] text-[11px] font-medium rounded-md border border-[var(--lia-btn-secondary-border,#E5E7EB)] transition-colors">
          <UserPlus className="w-3 h-3" />
          Adicionar à Lista
        </button>
        <button className="flex items-center justify-center gap-1 px-2.5 py-1.5 bg-[var(--lia-bg-primary,#fff)] hover:bg-[var(--wedo-orange-light,rgba(209,153,96,0.1))] text-[var(--wedo-orange,#D19960)] text-[11px] font-medium rounded-md border border-[var(--wedo-orange,#D19960)]/30 transition-colors">
          <Star className="w-3 h-3" />
          Destacar
        </button>
      </div>
    </div>
  )
}

export function Passive() {
  return (
    <PreviewShell
      candidateName="Isabela Martins"
      candidateRole="UX Designer Senior"
      candidateCompany="Stone"
      stage="Short List"
      stageColor="var(--wedo-cyan, #60BED1)"
      subStatus="Aguardando"
      decisionBar={<DecisionBar />}
      highlight={
        <span>
          <strong>UX Designer Senior</strong> com 7 anos na Stone, especialista em design systems e research.
          Portfólio premiado no Behance, experiência com acessibilidade WCAG 2.1. Score geral: 78%.
        </span>
      }
    />
  )
}
