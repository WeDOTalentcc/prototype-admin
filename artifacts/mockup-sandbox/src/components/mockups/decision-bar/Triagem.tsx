import { PreviewShell } from "./_shared"
import { CheckCircle2, XCircle, ChevronDown, BrainCircuit, Zap } from "lucide-react"

function DecisionBar() {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-purple-500" />
            <span className="text-[11px] font-semibold text-gray-800">Triagem</span>
          </div>
          <span className="text-[9px] text-gray-400">·</span>
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-amber-50 border border-amber-200 rounded text-[9px] text-amber-700 font-medium">
            <Zap className="w-2.5 h-2.5" />
            Decisão pendente
          </span>
        </div>
        <button className="flex items-center gap-1 px-2 py-1 text-[10px] text-gray-500 hover:bg-gray-100 rounded border border-gray-200">
          <ChevronDown className="w-3 h-3" />
          Mover para
        </button>
      </div>

      <div className="flex items-center gap-2">
        <button className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-[11px] font-medium rounded-md transition-colors">
          <CheckCircle2 className="w-3.5 h-3.5" />
          Aprovar
        </button>
        <button className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 bg-white hover:bg-red-50 text-red-600 text-[11px] font-medium rounded-md border border-red-200 transition-colors">
          <XCircle className="w-3.5 h-3.5" />
          Reprovar
        </button>
        <button className="flex items-center justify-center gap-1 px-2.5 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 text-[11px] font-medium rounded-md border border-blue-200 transition-colors">
          <BrainCircuit className="w-3.5 h-3.5" />
          WSI
        </button>
      </div>

      <p className="text-[9px] text-gray-400 italic">
        Score WSI: 82% · Triagem concluída há 2 dias · LIA recomenda aprovar
      </p>
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
      stageColor="#a855f7"
      subStatus="Decisão pendente"
      isFavorite
      decisionBar={<DecisionBar />}
    />
  )
}
