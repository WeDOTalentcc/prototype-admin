"use client"
import { useEffect } from"react"
import { formatBRL, CURRENCY_SYMBOL } from"@/lib/pricing"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { useMLPredictions } from"@/hooks/ai/use-ml-predictions"
import { useAuthStore } from"@/stores/auth-store"
import type { RecruiterData } from"../indicators.types"
import {
  TrendingUp, Clock, AlertTriangle, DollarSign, Brain, Target,
} from"lucide-react"

interface PredictionsTabProps {
  recruiters: RecruiterData[]
}

export function PredictionsTab({ recruiters }: PredictionsTabProps) {
  const user = useAuthStore((s) => s.user)
  const { insights, timeToFill, salary, loading, fetchInsights, fetchTimeToFill, fetchSalary } = useMLPredictions()
  const companyId = (user &&"company_id" in user ? user.company_id : undefined) ||"default"

  useEffect(() => {
    fetchInsights(companyId)
    fetchTimeToFill(companyId, {})
    fetchSalary(companyId, {})
  }, [companyId, fetchInsights, fetchTimeToFill, fetchSalary])

  const ttfDays = timeToFill?.predicted_days ?? 0
  const ttfConfidence = timeToFill ? Math.round(timeToFill.confidence * 100) : 0
  const salaryMin = salary?.suggested_min ?? 0
  const salaryMax = salary?.suggested_max ?? 0
  const totalHires = insights?.summary?.total_hires ?? 0
  const successRate = insights?.summary?.success_rate ? Math.round(insights.summary.success_rate * 100) : 0

  return (
    <div className="space-y-6" data-testid="predictions-tab">
      {/* KPIs Preditivos — dados reais do backend ML */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-status-success/30">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-status-success font-medium">Contratações</p>
                <p className="text-2xl font-semibold text-status-success">{loading ?"..." : totalHires}</p>
                <p className="text-xs text-lia-text-primary">Históricas</p>
              </div>
              <TrendingUp className="w-8 h-8 text-status-success" />
            </div>
            <div className="mt-2 text-xs text-status-success">
              {insights ? `Taxa de sucesso: ${successRate}%` :"Carregando..."}
            </div>
          </CardContent>
        </Card>

        <Card className="border-lia-border-default dark:border-lia-border-default">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-lia-text-secondary font-medium">
                  Tempo de Preenchimento
                </p>
                <p className="text-2xl font-semibold text-lia-text-primary">
                  {loading ?"..." : `${ttfDays} dias`}
                </p>
                <p className="text-xs text-lia-text-primary">
                  {timeToFill ? `${timeToFill.range_min}-${timeToFill.range_max} dias` :"Previsão média"}
                </p>
              </div>
              <Clock className="w-8 h-8 text-lia-text-secondary" />
            </div>
            <div className="mt-2 text-xs text-lia-text-secondary">
              {timeToFill ? `${timeToFill.comparison_to_market} (IA: ${ttfConfidence}%)` :"Carregando..."}
            </div>
          </CardContent>
        </Card>

        <Card className="border-wedo-purple/30">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-wedo-purple-text font-medium">Faixa Salarial</p>
                <p className="text-2xl font-semibold text-wedo-purple-text">
                  {loading ?"..." : salary ? `P${salary.market_percentile}` :"--"}
                </p>
                <p className="text-xs text-lia-text-primary">
                  Percentil de mercado
                </p>
              </div>
              <AlertTriangle className="w-8 h-8 text-wedo-purple" />
            </div>
            <div className="mt-2 text-xs text-wedo-purple-text">
              {salary ? salary.competitive_analysis :"Carregando..."}
            </div>
          </CardContent>
        </Card>

        <Card className="border-wedo-orange/30">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-wedo-orange-text font-medium">Salário Sugerido</p>
                <p className="text-2xl font-semibold text-wedo-orange-text">
                  {loading ?"..." : salary ? formatBRL(salaryMin) : `${CURRENCY_SYMBOL} --`}
                </p>
                <p className="text-xs text-lia-text-primary">
                  {salary ? `até ${formatBRL(salaryMax)}` :"Faixa ótima"}
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-wedo-orange" />
            </div>
            <div className="mt-2 text-xs text-wedo-orange-text">
              {salary ? `${Math.round(salary.confidence * 100)}% confiança` :"Calculando..."}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Insights de ML e Fatores de Impacto */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-wedo-purple" />
              Fatores de Impacto — Tempo de Preenchimento
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {(timeToFill?.factors || []).length > 0 ? (
                timeToFill!.factors.map((factor, index) => (
                  <div key={factor.name} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-lia-text-primary">
                        {factor.name}
                      </span>
                      <div className="flex items-center gap-2 text-sm">
                        <span className="text-lia-text-secondary">{factor.value}</span>
                        <Chip variant="neutral" muted className={
                          factor.impact ==="high" ?" text-xs" :
                          factor.impact ==="medium" ?" text-xs" :" text-xs"
                        }>
                          {factor.impact ==="high" ?"Alto" : factor.impact ==="medium" ?"Médio" :"Baixo"}
                        </Chip>
                      </div>
                    </div>
                    <div className="flex-1 bg-lia-interactive-active rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${factor.impact ==="high" ?"bg-status-error" : factor.impact ==="medium" ?"bg-status-warning" :"bg-status-success"}`}
                        style={{ width: `${factor.impact ==="high" ? 90 : factor.impact ==="medium" ? 60 : 30}%` }}
                      />
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-lia-text-secondary">
                  {loading ?"Carregando fatores..." :"Nenhum fator disponível. Execute uma previsão para ver os fatores de impacto."}
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="w-5 h-5 text-status-success" />
              Skills de Sucesso
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(insights?.top_successful_skills || []).length > 0 ? (
                insights!.top_successful_skills.map((item) => (
                  <div
                    key={item.skill}
                    className="flex items-center justify-between p-3 bg-lia-bg-secondary rounded-xl"
                  >
                    <div>
                      <div className="font-medium text-lia-text-primary">
                        {item.skill}
                      </div>
                      <div className="text-sm text-status-success">{Math.round(item.success_rate * 100)}% taxa de sucesso</div>
                    </div>
                    <Chip variant="neutral" muted className={
                      item.success_rate >= 0.8 ?"" :
                      item.success_rate >= 0.5 ?"" :""
                    }>
                      {item.count} contratações
                    </Chip>
                  </div>
                ))
              ) : (
                <p className="text-sm text-lia-text-secondary">
                  {loading ?"Carregando skills..." :"Sem dados históricos de skills disponíveis."}
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recomendações de IA — dados reais do backend */}
      <Card className="border-l-4 border-l-wedo-purple">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-wedo-purple" />
            Recomendações Inteligentes
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {(insights?.recommendations || []).length > 0 ? (
              insights!.recommendations.map((rec, index) => (
                <div
                  key={`rec-${index}`}
                  className={`p-4 rounded-md border-l-4 ${
                    rec.priority ==="high"
                      ?"bg-status-error/10 border-l-red-500"
                      : rec.priority ==="medium"
                      ?"bg-status-warning/10 border-l-yellow-500"
                      :"bg-status-success/10 border-l-green-500"
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className={`font-medium mb-1 ${
                        rec.priority ==="high" ?"text-status-error" :
                        rec.priority ==="medium" ?"text-status-warning" :"text-status-success"
                      }`}>
                        {rec.action}
                      </h4>
                      <p className="text-sm text-lia-text-secondary">{rec.impact}</p>
                    </div>
                    <Chip variant="neutral" muted className={
                      rec.priority ==="high" ?"ml-4" :
                      rec.priority ==="medium" ?"ml-4" :"ml-4"
                    }>
                      {rec.priority ==="high" ?"Alta" : rec.priority ==="medium" ?"Média" :"Baixa"}
                    </Chip>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-lia-text-secondary">
                {loading ?"Carregando recomendações..." :"Sem recomendações disponíveis. Execute análises para gerar insights."}
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
