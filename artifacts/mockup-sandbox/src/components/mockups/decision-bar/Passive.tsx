import { PreviewShell } from "./_shared"
import { ChevronDown, ArrowRight, UserPlus, Star } from "lucide-react"

function DecisionBar() {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-cyan-500" />
            <span className="text-[11px] font-semibold text-gray-800">Short List</span>
          </div>
          <span className="text-[9px] text-gray-400">·</span>
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-gray-100 border border-gray-200 rounded text-[9px] text-gray-600 font-medium">
            Aguardando ação do recrutador
          </span>
        </div>
        <div className="flex items-center gap-1">
          <button className="flex items-center gap-1 px-2 py-1 text-[10px] text-gray-500 hover:bg-gray-100 rounded border border-gray-200">
            <ChevronDown className="w-3 h-3" />
            Mover para
          </button>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button className="flex items-center justify-center gap-1.5 px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white text-[11px] font-medium rounded-md transition-colors">
          <ArrowRight className="w-3.5 h-3.5" />
          Avançar p/ Entrevista
        </button>
        <button className="flex items-center justify-center gap-1 px-2.5 py-1.5 bg-white hover:bg-gray-50 text-gray-700 text-[11px] font-medium rounded-md border border-gray-200 transition-colors">
          <UserPlus className="w-3 h-3" />
          Adicionar à Lista
        </button>
        <button className="flex items-center justify-center gap-1 px-2.5 py-1.5 bg-white hover:bg-amber-50 text-amber-600 text-[11px] font-medium rounded-md border border-amber-200 transition-colors">
          <Star className="w-3 h-3" />
          Destacar
        </button>
      </div>

      <p className="text-[9px] text-gray-400 italic">
        Na short list há 5 dias · Score geral: 78% · 3 de 6 avaliações completas
      </p>
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
      stageColor="#06b6d4"
      subStatus="Aguardando"
      decisionBar={<DecisionBar />}
    />
  )
}
