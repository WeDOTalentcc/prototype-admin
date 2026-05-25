"use client"

import { Brain, Trophy, Award, Clock, MessageSquare, FileText, BarChart3 } from "lucide-react"
import { cn } from "@/lib/utils"
import type { WSIResultDetails, WSICandidateRanking } from "@/services/lia-api"

interface TriagemSummaryBarProps {
  scores: WSIResultDetails["scores"]
  sessionInfo: WSIResultDetails["session"]
  ranking: WSICandidateRanking | null
  classColors: { bg: string; text: string; label: string }
  decisionDisplay: { label: string; icon: React.ElementType; color: string; bg: string }
  activeTab: "triagem" | "parecer" | "comparativo"
  onTabChange: (tab: "triagem" | "parecer" | "comparativo") => void
  getClassificationLabel: (c: string) => string
  getScoreColor: (s: number) => string
}

export function TriagemSummaryBar({
  scores,
  sessionInfo,
  ranking,
  classColors,
  decisionDisplay,
  activeTab,
  onTabChange,
  getClassificationLabel,
  getScoreColor,
}: TriagemSummaryBarProps) {
  const DecisionIcon = decisionDisplay.icon
  return (
    <>
      <div className="px-4 py-2.5 border-b border-b-lia-border-subtle bg-lia-bg-secondary">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-5">
            <div className="flex items-center gap-2">
              <Brain className="w-4 h-4 text-wedo-cyan" />
              <div>
                <p className="text-micro text-lia-text-secondary">Score WSI</p>
                <p className={`text-base font-bold ${getScoreColor(scores.overall_wsi)}`}>{scores.overall_wsi.toFixed(1)}<span className="lia-text-secondary font-normal">/10.0</span></p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Trophy className="w-4 h-4 text-lia-text-secondary" />
              <div>
                <p className="text-micro text-lia-text-secondary">Ranking</p>
                <p className="text-sm font-bold text-lia-text-primary">
                  {ranking?.ranked ? `#${ranking.rank} de ${ranking.total}` : 'N/A'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Award className="w-4 h-4 text-lia-text-secondary" />
              <div>
                <p className="text-micro text-lia-text-secondary">Classificação</p>
                <span className="inline-flex items-center px-1.5 py-0.5 text-micro font-medium rounded-full" style={{backgroundColor: classColors.bg, color: classColors.text}}>
                  {getClassificationLabel(scores.classification)}
                </span>
              </div>
            </div>

            {sessionInfo.duration_minutes && (
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-lia-text-secondary" />
                <div>
                  <p className="text-micro text-lia-text-secondary">Duração</p>
                  <p className="text-xs font-medium text-lia-text-primary">{sessionInfo.duration_minutes} min</p>
                </div>
              </div>
            )}
          </div>

          <div className="text-right">
            <span className="inline-flex items-center gap-1 px-2 py-1 text-micro font-medium rounded-full" style={{backgroundColor: decisionDisplay.bg, color: decisionDisplay.color}}>
              <DecisionIcon className="w-3 h-3" />
              {decisionDisplay.label}
            </span>
          </div>
        </div>
      </div>

      <div className="px-4 py-2 border-b border-b-lia-border-subtle">
        <div className="flex gap-1">
          {[
            { key: 'triagem' as const, icon: MessageSquare, label: 'Respostas e Avaliação' },
            { key: 'parecer' as const, icon: FileText, label: 'Parecer e Feedback' },
            { key: 'comparativo' as const, icon: BarChart3, label: 'Ranking e Comparativo' },
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => onTabChange(tab.key)}
              className={cn("px-3 py-1.5 text-xs font-medium transition-colors motion-reduce:transition-none flex items-center gap-1.5 rounded-full", activeTab === tab.key ? "bg-lia-btn-primary-bg text-lia-btn-primary-text" : "bg-transparent text-lia-text-secondary hover:bg-lia-interactive-hover")}
            >
              <tab.icon className="w-3 h-3" />
              {tab.label}
            </button>
          ))}
        </div>
      </div>
    </>
  )
}
