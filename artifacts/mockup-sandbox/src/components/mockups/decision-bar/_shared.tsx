import { ReactNode } from "react"
import {
  Mail, Phone, Calendar, ClipboardCheck, Briefcase, Star,
  MessageSquareText, Linkedin, ChevronLeft, ChevronRight,
  Maximize2, X, Sparkles
} from "lucide-react"

export function PreviewShell({
  candidateName,
  candidateRole,
  candidateCompany,
  stage,
  stageColor,
  subStatus,
  decisionBar,
  highlight,
  isFavorite = false,
}: {
  candidateName: string
  candidateRole: string
  candidateCompany: string
  stage: string
  stageColor: string
  subStatus?: string
  decisionBar: ReactNode
  highlight?: ReactNode
  isFavorite?: boolean
}) {
  return (
    <div className="w-full min-h-screen bg-[var(--lia-bg-secondary,#fafafa)] font-['Open_Sans',sans-serif] text-[11px]">
      <div className="border-b border-[var(--lia-border-subtle,#E5E7EB)] bg-[var(--lia-bg-primary,#fff)]">
        <div className="flex items-center justify-between px-3 py-2">
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1">
              <button className="p-1 hover:bg-[var(--lia-interactive-hover,#F3F4F6)] rounded"><ChevronLeft className="w-3.5 h-3.5 text-[var(--lia-text-tertiary,#9CA3AF)]" /></button>
              <button className="p-1 hover:bg-[var(--lia-interactive-hover,#F3F4F6)] rounded"><ChevronRight className="w-3.5 h-3.5 text-[var(--lia-text-tertiary,#9CA3AF)]" /></button>
            </div>
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-400 to-purple-600 flex items-center justify-center text-white text-xs font-semibold">
              {candidateName.split(' ').map(n => n[0]).join('').slice(0, 2)}
            </div>
            <div>
              <h3 className="text-xs font-semibold text-[var(--lia-text-primary,#000)] leading-tight">{candidateName}</h3>
              <p className="text-[10px] text-[var(--lia-text-secondary,#6B7280)]">{candidateRole} · {candidateCompany}</p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <button className="p-1 hover:bg-[var(--lia-interactive-hover,#F3F4F6)] rounded"><Maximize2 className="w-3.5 h-3.5 text-[var(--lia-text-tertiary,#9CA3AF)]" /></button>
            <button className="p-1 hover:bg-[var(--lia-interactive-hover,#F3F4F6)] rounded"><X className="w-3.5 h-3.5 text-[var(--lia-text-tertiary,#9CA3AF)]" /></button>
          </div>
        </div>

        <div className="flex items-center gap-1.5 px-3 pb-2 flex-wrap">
          <ActionIcon icon={Mail} label="Email" />
          <ActionIcon icon={Phone} label="WhatsApp" />
          <ActionIcon icon={Calendar} label="Agendar" color="text-[var(--wedo-orange,#D19960)]" />
          <ActionIcon icon={ClipboardCheck} label="WSI" />
          <ActionIcon icon={Briefcase} label="Vaga" />
          <button className={`p-1 rounded ${isFavorite ? 'bg-amber-50' : 'hover:bg-[var(--lia-interactive-hover,#F3F4F6)]'}`}>
            <Star className={`w-3.5 h-3.5 ${isFavorite ? 'text-amber-500 fill-amber-500' : 'text-[var(--lia-text-tertiary,#9CA3AF)]'}`} />
          </button>
          <ActionIcon icon={MessageSquareText} label="Feedback" color="text-[var(--wedo-purple,#9860D1)]" />
          <span className="text-[var(--lia-text-disabled,#D1D5DB)] mx-0.5">|</span>
          <ActionIcon icon={Linkedin} label="LinkedIn" />
        </div>
      </div>

      <div className="border-b-2 bg-[var(--lia-bg-primary,#fff)] px-3 py-2" style={{ borderBottomColor: stageColor }}>
        {decisionBar}
        {highlight && (
          <div className="mt-2 flex items-start gap-1.5 px-2 py-1.5 rounded-md bg-[var(--lia-bg-secondary,#F9FAFB)] border border-[var(--lia-border-subtle,#E5E7EB)]">
            <Sparkles className="w-3 h-3 text-[var(--wedo-cyan,#60BED1)] mt-0.5 flex-shrink-0" />
            <div className="text-[10px] text-[var(--lia-text-secondary,#6B7280)] leading-relaxed">
              {highlight}
            </div>
          </div>
        )}
      </div>

      <div className="px-3 pt-2">
        <div className="flex gap-1 border-b border-[var(--lia-border-subtle,#E5E7EB)] mb-3">
          {['Perfil', 'Atividades', 'Arquivos', 'Pareceres'].map((tab, i) => (
            <button
              key={tab}
              className={`px-3 py-1.5 text-[11px] font-medium border-b-2 transition-colors ${
                i === 0
                  ? 'border-[var(--lia-border-strong,#C9CDD4)] text-[var(--lia-text-primary,#000)]'
                  : 'border-transparent text-[var(--lia-text-tertiary,#9CA3AF)] hover:text-[var(--lia-text-secondary,#6B7280)]'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        <div className="space-y-3">
          <div className="bg-[var(--lia-bg-primary,#fff)] rounded-md border border-[var(--lia-border-subtle,#E5E7EB)] p-3">
            <h4 className="text-[11px] font-semibold text-[var(--lia-text-primary,#000)] mb-2">Destaques da Experiência</h4>
            <div className="space-y-1.5">
              <div className="flex items-start gap-2">
                <div className="w-1 h-1 rounded-full bg-[var(--wedo-cyan,#60BED1)] mt-1.5 flex-shrink-0" />
                <p className="text-[10px] text-[var(--lia-text-secondary,#6B7280)]">8 anos em desenvolvimento mobile (React Native, Flutter)</p>
              </div>
              <div className="flex items-start gap-2">
                <div className="w-1 h-1 rounded-full bg-[var(--wedo-cyan,#60BED1)] mt-1.5 flex-shrink-0" />
                <p className="text-[10px] text-[var(--lia-text-secondary,#6B7280)]">Liderança técnica de equipes de até 12 devs</p>
              </div>
              <div className="flex items-start gap-2">
                <div className="w-1 h-1 rounded-full bg-[var(--wedo-cyan,#60BED1)] mt-1.5 flex-shrink-0" />
                <p className="text-[10px] text-[var(--lia-text-secondary,#6B7280)]">Certificações AWS e GCP, experiência em CI/CD</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function ActionIcon({ icon: Icon, label, color = "text-[var(--lia-text-tertiary,#9CA3AF)]" }: { icon: React.ElementType; label: string; color?: string }) {
  return (
    <button className="p-1 hover:bg-[var(--lia-interactive-hover,#F3F4F6)] rounded" title={label}>
      <Icon className={`w-3.5 h-3.5 ${color}`} />
    </button>
  )
}
