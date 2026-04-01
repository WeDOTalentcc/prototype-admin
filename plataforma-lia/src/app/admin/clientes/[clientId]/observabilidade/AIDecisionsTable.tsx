import React from "react"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { CheckCircle2, XCircle, Brain } from "lucide-react"

interface AIDecision {
  id: string
  timestamp: string
  agent: string
  decisionType: string
  candidateId: string
  candidateName: string
  outcome: string
  overridden: boolean
  explainability: boolean
  confidence: number
}

interface AIDecisionsTableProps {
  decisions: AIDecision[]
  formatDateTime: (dateStr: string | undefined | null) => string
}

const agentLabels: Record<string, string> = {
  screening: 'Triagem',
  scoring: 'Scoring',
  interview: 'Entrevista',
  matching: 'Matching'
}

export function AIDecisionsTable({ decisions, formatDateTime }: AIDecisionsTableProps) {
  if (decisions.length === 0) {
    return (
      <div className="text-center py-6">
        <Brain className="w-8 h-8 text-wedo-cyan mx-auto mb-2" />
        <p className="text-sm lia-text-400 dark:lia-text-500">Nenhuma decisão automatizada registrada</p>
      </div>
    )
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-lia-border-subtle dark:border-lia-border-subtle">
            <th className="text-left py-3 px-2 text-xs font-medium lia-text-400 dark:lia-text-500">Data/Hora</th>
            <th className="text-left py-3 px-2 text-xs font-medium lia-text-400 dark:lia-text-500">Agente</th>
            <th className="text-left py-3 px-2 text-xs font-medium lia-text-400 dark:lia-text-500">Candidato</th>
            <th className="text-left py-3 px-2 text-xs font-medium lia-text-400 dark:lia-text-500">Decisão</th>
            <th className="text-left py-3 px-2 text-xs font-medium lia-text-400 dark:lia-text-500">Confiança</th>
            <th className="text-left py-3 px-2 text-xs font-medium lia-text-400 dark:lia-text-500">Override</th>
            <th className="text-left py-3 px-2 text-xs font-medium lia-text-400 dark:lia-text-500">XAI</th>
          </tr>
        </thead>
        <tbody>
          {decisions.map((decision) => (
            <tr key={decision.id} className="border-b hover:bg-gray-50 dark:hover:bg-gray-800/50 border-lia-border-subtle dark:border-lia-border-subtle">
              <td className="py-3 px-2 text-sm lia-text-400 dark:lia-text-500">{formatDateTime(decision.timestamp)}</td>
              <td className="py-3 px-2">
                <Badge variant="outline" className="text-xs">{agentLabels[decision.agent] || decision.agent}</Badge>
              </td>
              <td className="py-3 px-2 text-sm lia-text-800 dark:text-lia-text-primary">{decision.candidateName}</td>
              <td className="py-3 px-2 text-sm font-medium lia-text-800 dark:text-lia-text-primary">{decision.outcome}</td>
              <td className="py-3 px-2">
                <div className="flex items-center gap-2">
                  <Progress value={decision.confidence * 100} className="h-1.5 w-16" />
                  <span className="text-xs lia-text-400 dark:lia-text-500">{(decision.confidence * 100).toFixed(0)}%</span>
                </div>
              </td>
              <td className="py-3 px-2">
                {decision.overridden ? (
                  <Badge variant="warning" className="text-xs">Sim</Badge>
                ) : (
                  <Badge variant="outline" className="text-xs">Não</Badge>
                )}
              </td>
              <td className="py-3 px-2">
                {decision.explainability ? (
                  <CheckCircle2 className="w-4 h-4 text-status-success" />
                ) : (
                  <XCircle className="w-4 h-4 lia-text-400" />
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
