import { Trophy, Medal } from "lucide-react"
import type { ViewMode, GoalStatus } from "../indicators.types"
import { Layout, Target, BarChart3 } from "lucide-react"

export function getRankingIcon(ranking: number) {
  switch (ranking) {
    case 1:
      return <Trophy className="w-5 h-5 text-status-warning" />
    case 2:
      return <Medal className="w-5 h-5 text-lia-text-secondary" />
    case 3:
      return <Medal className="w-5 h-5 text-status-warning" />
    default:
      return (
        <div className="w-5 h-5 flex items-center justify-center text-sm font-bold text-lia-text-primary">
          {ranking}
        </div>
      )
  }
}

export const VIEW_MODES = [
  { id: "cards" as ViewMode, label: "Cards Individuais", icon: Layout },
  { id: "ranking" as ViewMode, label: "Classificação Geral", icon: Trophy },
  { id: "goals" as ViewMode, label: "Metas e Objetivos", icon: Target },
  { id: "comparison" as ViewMode, label: "Comparação", icon: BarChart3 },
]

export function getGoalLabel(key: string, variant: "short" | "long" = "short"): string {
  if (variant === "long") {
    switch (key) {
      case "hires": return "Contratações"
      case "timeToFill": return "Tempo de Preenchimento (dias)"
      case "nps": return "NPS"
      case "interviews": return "Entrevistas"
      case "qualityScore": return "Nota de Qualidade"
      case "conversionRate": return "Taxa de Conversão (%)"
      default: return key
    }
  }
  switch (key) {
    case "hires": return "Contratações"
    case "timeToFill": return "Tempo de Preenchimento"
    case "nps": return "NPS"
    case "interviews": return "Entrevistas"
    default: return key
  }
}

export function getGoalStatusLabel(status: GoalStatus): string {
  switch (status) {
    case "exceeded": return "Superou"
    case "achieved": return "Atingiu"
    case "on_track": return "No prazo"
    case "behind": return "Atrasado"
  }
}

export function getGoalStatusBarColor(status: GoalStatus): string {
  switch (status) {
    case "exceeded": return "bg-status-success"
    case "achieved": return "bg-wedo-cyan"
    case "on_track": return "bg-status-warning"
    case "behind": return "bg-status-error"
  }
}

export function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
}
