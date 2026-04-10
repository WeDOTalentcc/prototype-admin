import { ReactNode } from "react"
import {
  Mail, Phone, Calendar, ClipboardCheck, Briefcase, Star,
  MessageSquareText, Linkedin, ChevronLeft, ChevronRight,
  Maximize2, X, BrainCircuit, Target, Gauge, Code, Globe, Fingerprint
} from "lucide-react"

const scoreIcon = (Icon: React.ElementType, value: number | null, label: string, color: string) => (
  <div className="flex flex-col items-center gap-0.5" title={label}>
    <div className={`w-7 h-7 rounded-md flex items-center justify-center ${value != null ? `bg-${color}/10` : 'bg-gray-100'}`}>
      <Icon className={`w-3.5 h-3.5 ${value != null ? `text-${color}` : 'text-gray-300'}`} />
    </div>
    <span className={`text-[9px] font-medium ${value != null ? 'text-gray-700' : 'text-gray-300'}`}>
      {value != null ? `${value}%` : '—'}
    </span>
  </div>
)

export function PreviewShell({
  candidateName,
  candidateRole,
  candidateCompany,
  stage,
  stageColor,
  subStatus,
  decisionBar,
  isFavorite = false,
}: {
  candidateName: string
  candidateRole: string
  candidateCompany: string
  stage: string
  stageColor: string
  subStatus?: string
  decisionBar: ReactNode
  isFavorite?: boolean
}) {
  return (
    <div className="w-full min-h-screen bg-[#fafafa] font-['Open_Sans',sans-serif] text-[11px]">
      <div className="border-b border-gray-200 bg-white">
        <div className="flex items-center justify-between px-3 py-2">
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1">
              <button className="p-1 hover:bg-gray-100 rounded"><ChevronLeft className="w-3.5 h-3.5 text-gray-400" /></button>
              <button className="p-1 hover:bg-gray-100 rounded"><ChevronRight className="w-3.5 h-3.5 text-gray-400" /></button>
            </div>
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-400 to-purple-600 flex items-center justify-center text-white text-xs font-semibold">
              {candidateName.split(' ').map(n => n[0]).join('').slice(0, 2)}
            </div>
            <div>
              <h3 className="text-xs font-semibold text-gray-900 leading-tight">{candidateName}</h3>
              <p className="text-[10px] text-gray-500">{candidateRole} · {candidateCompany}</p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <button className="p-1 hover:bg-gray-100 rounded"><Maximize2 className="w-3.5 h-3.5 text-gray-400" /></button>
            <button className="p-1 hover:bg-gray-100 rounded"><X className="w-3.5 h-3.5 text-gray-400" /></button>
          </div>
        </div>

        <div className="flex items-center gap-1.5 px-3 pb-2 flex-wrap">
          <ActionIcon icon={Mail} label="Email" />
          <ActionIcon icon={Phone} label="WhatsApp" />
          <ActionIcon icon={Calendar} label="Agendar" color="text-orange-500" />
          <ActionIcon icon={ClipboardCheck} label="WSI" />
          <ActionIcon icon={Briefcase} label="Vaga" />
          <button className={`p-1 rounded ${isFavorite ? 'bg-amber-50' : 'hover:bg-gray-100'}`}>
            <Star className={`w-3.5 h-3.5 ${isFavorite ? 'text-amber-500 fill-amber-500' : 'text-gray-400'}`} />
          </button>
          <ActionIcon icon={MessageSquareText} label="Feedback" color="text-purple-500" />
          <span className="text-gray-300 mx-0.5">|</span>
          <ActionIcon icon={Linkedin} label="LinkedIn" />
        </div>
      </div>

      <div className={`border-b-2 bg-white px-3 py-2`} style={{ borderBottomColor: stageColor }}>
        {decisionBar}
      </div>

      <div className="px-3 pt-2">
        <div className="flex gap-1 border-b border-gray-200 mb-3">
          {['Perfil', 'Atividades', 'Arquivos', 'Pareceres'].map((tab, i) => (
            <button
              key={tab}
              className={`px-3 py-1.5 text-[11px] font-medium border-b-2 transition-colors ${
                i === 0
                  ? 'border-purple-600 text-purple-700'
                  : 'border-transparent text-gray-400 hover:text-gray-600'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        <div className="space-y-3">
          <div className="flex items-center gap-2 mb-2">
            {scoreIcon(Gauge, 78, "Geral", "purple-600")}
            {scoreIcon(BrainCircuit, 82, "Triagem", "blue-600")}
            {scoreIcon(Target, 75, "CV Match", "emerald-600")}
            {scoreIcon(Code, null, "Técnico", "orange-500")}
            {scoreIcon(Globe, null, "Inglês", "cyan-600")}
            {scoreIcon(Fingerprint, 71, "Big Five", "pink-600")}
          </div>

          <div className="bg-white rounded-md border border-gray-200 p-3">
            <h4 className="text-[11px] font-semibold text-gray-700 mb-2">Destaques da Experiência</h4>
            <div className="space-y-1.5">
              <div className="flex items-start gap-2">
                <div className="w-1 h-1 rounded-full bg-purple-500 mt-1.5 flex-shrink-0" />
                <p className="text-[10px] text-gray-600">8 anos em desenvolvimento mobile (React Native, Flutter)</p>
              </div>
              <div className="flex items-start gap-2">
                <div className="w-1 h-1 rounded-full bg-purple-500 mt-1.5 flex-shrink-0" />
                <p className="text-[10px] text-gray-600">Liderança técnica de equipes de até 12 devs</p>
              </div>
              <div className="flex items-start gap-2">
                <div className="w-1 h-1 rounded-full bg-purple-500 mt-1.5 flex-shrink-0" />
                <p className="text-[10px] text-gray-600">Certificações AWS e GCP, experiência em CI/CD</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-md border border-gray-200 p-3">
            <h4 className="text-[11px] font-semibold text-gray-700 mb-1.5">Parecer da LIA</h4>
            <p className="text-[10px] text-gray-500 leading-relaxed">
              Candidato com perfil técnico sólido e experiência relevante em liderança.
              Boa aderência cultural com base nas competências comportamentais avaliadas.
              Recomendo avançar para a próxima etapa.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

function ActionIcon({ icon: Icon, label, color = "text-gray-400" }: { icon: React.ElementType; label: string; color?: string }) {
  return (
    <button className="p-1 hover:bg-gray-100 rounded" title={label}>
      <Icon className={`w-3.5 h-3.5 ${color}`} />
    </button>
  )
}
