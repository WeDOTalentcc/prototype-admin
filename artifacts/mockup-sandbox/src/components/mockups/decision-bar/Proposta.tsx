import { PreviewShell } from "./_shared"
import { Send, XCircle, ChevronDown, FileText, DollarSign, Clock } from "lucide-react"

function DecisionBar() {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-blue-600" />
            <span className="text-[11px] font-semibold text-gray-800">Proposta</span>
          </div>
          <span className="text-[9px] text-gray-400">·</span>
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-blue-50 border border-blue-200 rounded text-[9px] text-blue-700 font-medium">
            <Clock className="w-2.5 h-2.5" />
            Aguardando resposta
          </span>
        </div>
        <button className="flex items-center gap-1 px-2 py-1 text-[10px] text-gray-500 hover:bg-gray-100 rounded border border-gray-200">
          <ChevronDown className="w-3 h-3" />
          Mover para
        </button>
      </div>

      <div className="flex items-center gap-2">
        <button className="flex items-center justify-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-[11px] font-medium rounded-md transition-colors">
          <Send className="w-3.5 h-3.5" />
          Enviar Proposta
        </button>
        <button className="flex items-center justify-center gap-1 px-2.5 py-1.5 bg-white hover:bg-gray-50 text-gray-700 text-[11px] font-medium rounded-md border border-gray-200 transition-colors">
          <FileText className="w-3 h-3" />
          Ver Proposta
        </button>
        <button className="flex items-center justify-center gap-1 px-2.5 py-1.5 bg-white hover:bg-gray-50 text-gray-700 text-[11px] font-medium rounded-md border border-gray-200 transition-colors">
          <DollarSign className="w-3 h-3" />
          Negociar
        </button>
        <button className="flex items-center justify-center gap-1 px-2.5 py-1.5 bg-white hover:bg-red-50 text-red-600 text-[11px] font-medium rounded-md border border-red-200 transition-colors">
          <XCircle className="w-3.5 h-3.5" />
          Recusar
        </button>
      </div>

      <div className="flex items-center gap-3 text-[9px] text-gray-400">
        <span>CLT · R$ 18.000/mês</span>
        <span>·</span>
        <span>Enviada há 3 dias</span>
        <span>·</span>
        <span className="text-amber-600 font-medium">Prazo: 5 dias</span>
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
      stageColor="#2563eb"
      subStatus="Aguardando resposta"
      decisionBar={<DecisionBar />}
    />
  )
}
