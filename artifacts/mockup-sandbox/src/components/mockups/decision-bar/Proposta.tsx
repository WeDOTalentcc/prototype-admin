import { PreviewShell } from "./_shared"
import { Send, XCircle, ChevronDown, FileText, DollarSign, Clock } from "lucide-react"

function DecisionBar() {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-[var(--wedo-cyan,#60BED1)]" />
            <span className="text-[11px] font-semibold text-[var(--lia-text-primary,#000)]">Proposta</span>
          </div>
          <span className="text-[9px] text-[var(--lia-text-tertiary,#9CA3AF)]">·</span>
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-[var(--wedo-cyan-light,rgba(96,190,209,0.1))] border border-[var(--wedo-cyan,#60BED1)]/30 rounded text-[9px] text-[var(--wedo-cyan-dark,#4DA8BB)] font-medium">
            <Clock className="w-2.5 h-2.5" />
            Aguardando resposta
          </span>
        </div>
        <button className="flex items-center gap-1 px-2 py-1 text-[10px] text-[var(--lia-btn-secondary-text,#6B7280)] hover:bg-[var(--lia-btn-secondary-hover,#F3F4F6)] rounded border border-[var(--lia-btn-secondary-border,#E5E7EB)]">
          <ChevronDown className="w-3 h-3" />
          Mover para
        </button>
      </div>

      <div className="flex items-center gap-2">
        <button className="flex items-center justify-center gap-1.5 px-3 py-1.5 bg-[var(--lia-btn-primary-bg,#111827)] hover:bg-[var(--lia-btn-primary-hover,#000)] text-[var(--lia-btn-primary-text,#fff)] text-[11px] font-medium rounded-md transition-colors">
          <Send className="w-3.5 h-3.5" />
          Enviar Proposta
        </button>
        <button className="flex items-center justify-center gap-1 px-2.5 py-1.5 bg-[var(--lia-bg-primary,#fff)] hover:bg-[var(--lia-btn-secondary-hover,#F3F4F6)] text-[var(--lia-text-primary,#000)] text-[11px] font-medium rounded-md border border-[var(--lia-btn-secondary-border,#E5E7EB)] transition-colors">
          <FileText className="w-3 h-3" />
          Ver Proposta
        </button>
        <button className="flex items-center justify-center gap-1 px-2.5 py-1.5 bg-[var(--lia-bg-primary,#fff)] hover:bg-[var(--lia-btn-secondary-hover,#F3F4F6)] text-[var(--lia-text-primary,#000)] text-[11px] font-medium rounded-md border border-[var(--lia-btn-secondary-border,#E5E7EB)] transition-colors">
          <DollarSign className="w-3 h-3" />
          Negociar
        </button>
        <button className="flex items-center justify-center gap-1 px-2.5 py-1.5 bg-[var(--lia-bg-primary,#fff)] hover:bg-[var(--lia-brand-primary-light,#FEF2F2)] text-[var(--lia-destructive-bg,#C74446)] text-[11px] font-medium rounded-md border border-[var(--lia-destructive-border,#C74446)]/30 transition-colors">
          <XCircle className="w-3.5 h-3.5" />
          Recusar
        </button>
      </div>

      <div className="flex items-center gap-3 text-[9px] text-[var(--lia-text-tertiary,#9CA3AF)]">
        <span>CLT · R$ 18.000/mês</span>
        <span>·</span>
        <span>Enviada há 3 dias</span>
        <span>·</span>
        <span className="text-[var(--wedo-orange,#D19960)] font-medium">Prazo: 5 dias</span>
      </div>
    </div>
  )
}

export function Proposta() {
  return (
    <PreviewShell
      candidateName="Amanda Silveira"
      candidateRole="Product Manager"
      candidateCompany="iFood"
      stage="Proposta"
      stageColor="var(--wedo-cyan, #60BED1)"
      subStatus="Aguardando resposta"
      decisionBar={<DecisionBar />}
      highlight={
        <span>
          <strong>Product Manager</strong> com 5 anos no iFood, liderou squad de 8 pessoas responsável por crescimento de 30% em GMV.
          MBA em Gestão de Produto pela USP, experiência com OKRs e discovery contínuo.
        </span>
      }
    />
  )
}
