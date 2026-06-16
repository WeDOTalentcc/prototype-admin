"use client"

import {
  Brain,
  BarChart3,
  Lightbulb,
  Target,
  TrendingUp,
  TrendingDown,
  Zap,
  Search,
  ArrowRightLeft,
  XCircle,
} from "lucide-react"

interface LiaInsight {
  type: "action_recommended" | "analysis" | "comparative" | "attention"
  title: string
  description: string
}

const INSIGHT_STYLES: Record<LiaInsight["type"], {
  bg: string
  border: string
  iconColor: string
  badgeText: string
  badgeBg: string
  icon: React.ElementType
}> = {
  action_recommended: {
    bg: "bg-status-warning/10",
    border: "border-status-warning/30",
    iconColor: "text-status-warning",
    badgeText: "Ação Recomendada",
    badgeBg: "bg-status-warning/15 text-status-warning",
    icon: Zap,
  },
  analysis: {
    bg: "bg-wedo-purple/10",
    border: "border-wedo-purple/30",
    iconColor: "text-lia-text-secondary",
    badgeText: "Análise",
    badgeBg: "bg-wedo-purple/15 text-wedo-purple-text",
    icon: Search,
  },
  comparative: {
    bg: "bg-wedo-cyan/10",
    border: "border-wedo-cyan/30",
    iconColor: "text-lia-text-secondary",
    badgeText: "Comparativo",
    badgeBg: "bg-wedo-cyan/15 text-wedo-cyan-text",
    icon: ArrowRightLeft,
  },
  attention: {
    bg: "bg-status-error/10",
    border: "border-status-error/30",
    iconColor: "text-status-error",
    badgeText: "Atenção",
    badgeBg: "bg-status-error/15 text-status-error",
    icon: XCircle,
  },
}

interface LiaAnalysisData {
  summary: string
  keyMetrics: {
    label: string
    value: string
    trend?: "up" | "down" | "neutral"
    highlight?: boolean
  }[]
  insights: LiaInsight[]
  recommendations: string[]
}

interface LiaAnalysisPanelProps {
  liaAnalysis: LiaAnalysisData
}

export function LiaAnalysisPanel({ liaAnalysis }: LiaAnalysisPanelProps) {
  return (
    <div data-testid="lia-analysis-panel" className="border border-lia-border-subtle rounded-xl overflow-hidden">
      <div className="bg-lia-bg-secondary px-4 py-2.5">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-lia-bg-tertiary rounded-xl flex items-center justify-center">
            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
          </div>
          <h3 className="text-base-ui font-semibold text-lia-text-primary">Análise LIA</h3>
        </div>
      </div>

      <div className="p-4 space-y-4">
        <p className="text-xs text-lia-text-secondary leading-relaxed">
          {liaAnalysis.summary}
        </p>

        <div>
          <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2 flex items-center gap-1.5">
            <BarChart3 className="w-3 h-3" />
            Indicadores-Chave
          </h4>
          <div className="grid grid-cols-4 gap-3">
            {liaAnalysis.keyMetrics.map((metric, idx) => (
              <div
                key={`metric-${idx}`}
                className={`p-3 rounded-md border ${
                  metric.highlight
                    ? "bg-lia-bg-secondary border-lia-border-default"
                    : "bg-lia-bg-secondary border-lia-border-subtle"
                }`}
              >
                <p className="text-micro text-lia-text-tertiary uppercase tracking-wide mb-1">
                  {metric.label}
                </p>
                <div className="flex items-center gap-1.5">
                  <span className={`text-lg font-semibold ${
                    metric.highlight ? "text-lia-text-secondary" : "text-lia-text-primary"
                  }`}>
                    {metric.value}
                  </span>
                  {metric.trend === "up" && (
                    <TrendingUp className="w-3.5 h-3.5 text-status-success" />
                  )}
                  {metric.trend === "down" && (
                    <TrendingDown className="w-3.5 h-3.5 text-status-warning" />
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {liaAnalysis.insights.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2 flex items-center gap-1.5">
              <Lightbulb className="w-3 h-3" />
              Insights
            </h4>
            <div className="space-y-2">
              {liaAnalysis.insights.map((insight, idx) => {
                const style = INSIGHT_STYLES[insight.type]
                const IconComponent = style.icon
                return (
                  <div
                    key={idx}
                    className={`p-3 rounded-md border flex items-start gap-2.5 ${style.bg} ${style.border}`}
                  >
                    <IconComponent className={`w-4 h-4 ${style.iconColor} flex-shrink-0 mt-0.5`} />
                    <div className="flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="text-xs font-semibold text-lia-text-primary">{insight.title}</p>
                        <span className={`text-micro font-semibold px-1.5 py-0.5 rounded-full ${style.badgeBg}`}>
                          {style.badgeText}
                        </span>
                      </div>
                      <p className="text-xs text-lia-text-secondary mt-0.5 leading-relaxed">
                        {insight.description}
                      </p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {liaAnalysis.recommendations.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2 flex items-center gap-1.5">
              <Target className="w-3 h-3" />
              Recomendações
            </h4>
            <ul className="space-y-1.5">
              {liaAnalysis.recommendations.map((rec, idx) => (
                <li key={`rec-${idx}`} className="flex items-start gap-2 text-xs text-lia-text-secondary">
                  <span className="text-lia-text-disabled mt-0.5">•</span>
                  <span className="leading-relaxed">{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
