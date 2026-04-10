import { PreviewShell } from "./_shared"
import { CheckCircle2, XCircle, ChevronDown, Calendar, Video, RotateCcw, XSquare } from "lucide-react"

function DecisionBar() {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-orange-500" />
            <span className="text-[11px] font-semibold text-gray-800">Entrevista RH</span>
          </div>
          <span className="text-[9px] text-gray-400">·</span>
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-emerald-50 border border-emerald-200 rounded text-[9px] text-emerald-700 font-medium">
            <Calendar className="w-2.5 h-2.5" />
            Confirmada · 12/04 às 14h
          </span>
        </div>
        <button className="flex items-center gap-1 px-2 py-1 text-[10px] text-gray-500 hover:bg-gray-100 rounded border border-gray-200">
          <ChevronDown className="w-3 h-3" />
          Mover para
        </button>
      </div>

      <div className="flex items-center gap-2">
        <button className="flex items-center justify-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-[11px] font-medium rounded-md transition-colors">
          <Video className="w-3.5 h-3.5" />
          Entrar na Sala
        </button>
        <button className="flex items-center justify-center gap-1 px-2.5 py-1.5 bg-white hover:bg-gray-50 text-gray-700 text-[11px] font-medium rounded-md border border-gray-200 transition-colors">
          <RotateCcw className="w-3 h-3" />
          Reagendar
        </button>
        <button className="flex items-center justify-center gap-1 px-2.5 py-1.5 bg-white hover:bg-red-50 text-red-500 text-[11px] font-medium rounded-md border border-gray-200 transition-colors">
          <XSquare className="w-3 h-3" />
          Cancelar
        </button>
        <span className="text-gray-300 mx-0.5">|</span>
        <button className="flex items-center justify-center gap-1 px-2.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-[11px] font-medium rounded-md transition-colors">
          <CheckCircle2 className="w-3.5 h-3.5" />
          Passou
        </button>
        <button className="flex items-center justify-center gap-1 px-2.5 py-1.5 bg-white hover:bg-red-50 text-red-600 text-[11px] font-medium rounded-md border border-red-200 transition-colors">
          <XCircle className="w-3.5 h-3.5" />
          Não passou
        </button>
      </div>

      <p className="text-[9px] text-gray-400 italic">
        Via MS Teams · Entrevistador: Maria Santos · Duração: 45 min
      </p>
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
      stageColor="#f97316"
      subStatus="Entrevista confirmada"
      decisionBar={<DecisionBar />}
    />
  )
}
