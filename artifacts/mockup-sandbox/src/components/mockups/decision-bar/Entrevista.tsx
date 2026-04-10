import { PreviewShell } from "./_shared"
import { CheckCircle2, XCircle, ChevronDown, Calendar, Video, RotateCcw, XSquare } from "lucide-react"

function DecisionBar() {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-[var(--wedo-orange,#D19960)]" />
            <span className="text-[11px] font-semibold text-[var(--lia-text-primary,#000)]">Entrevista RH</span>
          </div>
          <span className="text-[9px] text-[var(--lia-text-tertiary,#9CA3AF)]">·</span>
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-[var(--wedo-green-light,rgba(93,164,122,0.1))] border border-[var(--wedo-green,#5DA47A)]/30 rounded text-[9px] text-[var(--wedo-green,#5DA47A)] font-medium">
            <Calendar className="w-2.5 h-2.5" />
            Confirmada · 12/04 às 14h
          </span>
        </div>
        <button className="flex items-center gap-1 px-2 py-1 text-[10px] text-[var(--lia-btn-secondary-text,#6B7280)] hover:bg-[var(--lia-btn-secondary-hover,#F3F4F6)] rounded border border-[var(--lia-btn-secondary-border,#E5E7EB)]">
          <ChevronDown className="w-3 h-3" />
          Mover para
        </button>
      </div>

      <div className="flex items-center gap-2">
        <button className="flex items-center justify-center gap-1.5 px-3 py-1.5 bg-[var(--lia-btn-primary-bg,#111827)] hover:bg-[var(--lia-btn-primary-hover,#000)] text-[var(--lia-btn-primary-text,#fff)] text-[11px] font-medium rounded-md transition-colors">
          <Video className="w-3.5 h-3.5" />
          Entrar na Sala
        </button>
        <button className="flex items-center justify-center gap-1 px-2.5 py-1.5 bg-[var(--lia-bg-primary,#fff)] hover:bg-[var(--lia-btn-secondary-hover,#F3F4F6)] text-[var(--lia-text-primary,#000)] text-[11px] font-medium rounded-md border border-[var(--lia-btn-secondary-border,#E5E7EB)] transition-colors">
          <RotateCcw className="w-3 h-3" />
          Reagendar
        </button>
        <button className="flex items-center justify-center gap-1 px-2.5 py-1.5 bg-[var(--lia-bg-primary,#fff)] hover:bg-[var(--lia-brand-primary-light,#FEF2F2)] text-[var(--lia-destructive-bg,#C74446)] text-[11px] font-medium rounded-md border border-[var(--lia-btn-secondary-border,#E5E7EB)] transition-colors">
          <XSquare className="w-3 h-3" />
          Cancelar
        </button>
        <span className="text-[var(--lia-text-disabled,#D1D5DB)] mx-0.5">|</span>
        <button className="flex items-center justify-center gap-1 px-2.5 py-1.5 bg-[var(--lia-btn-primary-bg,#111827)] hover:bg-[var(--lia-btn-primary-hover,#000)] text-[var(--lia-btn-primary-text,#fff)] text-[11px] font-medium rounded-md transition-colors">
          <CheckCircle2 className="w-3.5 h-3.5" />
          Passou
        </button>
        <button className="flex items-center justify-center gap-1 px-2.5 py-1.5 bg-[var(--lia-bg-primary,#fff)] hover:bg-[var(--lia-brand-primary-light,#FEF2F2)] text-[var(--lia-destructive-bg,#C74446)] text-[11px] font-medium rounded-md border border-[var(--lia-destructive-border,#C74446)]/30 transition-colors">
          <XCircle className="w-3.5 h-3.5" />
          Não passou
        </button>
      </div>
    </div>
  )
}

export function Entrevista() {
  return (
    <PreviewShell
      candidateName="Bruno Cavalcanti"
      candidateRole="Senior Backend Engineer"
      candidateCompany="Nubank"
      stage="Entrevista RH"
      stageColor="var(--wedo-orange, #D19960)"
      subStatus="Entrevista confirmada"
      decisionBar={<DecisionBar />}
      highlight={
        <span>
          <strong>Senior Backend Engineer</strong> com 6 anos no Nubank, especialista em microsserviços Java/Kotlin.
          Liderou migração de monolito que reduziu latência em 40%. Inglês fluente, perfil colaborativo.
        </span>
      }
    />
  )
}
