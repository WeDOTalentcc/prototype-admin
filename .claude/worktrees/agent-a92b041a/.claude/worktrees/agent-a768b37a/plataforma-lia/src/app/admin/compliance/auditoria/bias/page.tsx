"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Scale,
  Calendar,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Shield,
  BarChart3,
  AlertCircle,
  Info,
  RefreshCw,
  Loader2,
} from "lucide-react"
import {
  useBiasAuditReport,
  type AuditDimension,
} from "@/hooks/use-bias-audit-report"

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const DIMENSION_LABELS: Record<string, string> = {
  gender: "Gênero",
  age_group: "Faixa Etária",
  disability: "PCD",
  region: "Região",
}

const complianceFrameworks = [
  { id: "nyc-ll144",   name: "NYC LL144",   description: "New York City Local Law 144" },
  { id: "co-sb205",    name: "CO SB205",    description: "Colorado Senate Bill 205" },
  { id: "eu-ai-act",   name: "EU AI Act",   description: "European Union AI Act" },
  { id: "lgpd-brazil", name: "LGPD Brazil", description: "Lei Geral de Proteção de Dados" },
  { id: "iso-27001",   name: "ISO 27001",   description: "Information Security Management" },
]

// ---------------------------------------------------------------------------
// Pure helpers (sem estado — portáveis para Vue)
// ---------------------------------------------------------------------------

const getAlertBadge = (hasAlerts: boolean) =>
  hasAlerts ? (
    <Badge className="bg-amber-100 text-amber-700 dark:bg-amber-900/20 dark:text-amber-400">
      Atenção
    </Badge>
  ) : (
    <Badge variant="success">OK</Badge>
  )

const getDimensionStatusBadge = (alertLevel: AuditDimension["alert_level"]) =>
  alertLevel === "ok" ? (
    <Badge variant="success" className="gap-1">
      <CheckCircle2 className="w-3 h-3" aria-hidden="true" />Clear
    </Badge>
  ) : (
    <Badge className="bg-amber-100 text-amber-700 dark:bg-amber-900/20 dark:text-amber-400 gap-1">
      <AlertTriangle className="w-3 h-3" aria-hidden="true" />Warning
    </Badge>
  )

const getProgressColor = (ratio: number) => {
  if (ratio >= 0.90) return "bg-emerald-500"
  if (ratio >= 0.80) return "bg-amber-500"
  return "bg-red-500"
}

const formatDate = (dateStr: string) =>
  new Date(dateStr).toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  })

// ---------------------------------------------------------------------------
// Component — template + binding apenas (lógica em useBiasAuditReport)
// ---------------------------------------------------------------------------

export default function BiasAuditPage() {
  const {
    jobIdInput,
    loading,
    error,
    auditData,
    setJobIdInput,
    handleSearch,
  } = useBiasAuditReport()

  const alertCount = auditData?.dimensions.filter((d) => d.alert_level === "warning").length ?? 0

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-md flex items-center justify-center bg-gray-200/30 dark:bg-gray-700/30">
              <Scale className="w-5 h-5 text-gray-600 dark:text-gray-400" aria-hidden="true" />
            </div>
            <div>
              <h1
                className="text-xl font-semibold"
                style={{ color: "var(--eleven-text-primary)" }}
              >
                Auditorias de Bias
              </h1>
              <p className="text-sm" style={{ color: "var(--eleven-text-tertiary)" }}>
                Análise de viés algorítmico — Four-Fifths Rule (adverse impact ≥ 0.80)
              </p>
            </div>
          </div>
          <Button className="gap-2 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200">
            <FileText className="w-4 h-4" aria-hidden="true" />
            Exportar Relatório
          </Button>
        </div>

        {/* Job ID Search */}
        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="flex items-end gap-3">
              <div className="flex-1">
                <label
                  htmlFor="job-id-input"
                  className="text-xs font-medium text-gray-500 mb-1 block"
                >
                  ID da Vaga (UUID)
                </label>
                <input
                  id="job-id-input"
                  type="text"
                  placeholder="Ex: 123e4567-e89b-12d3-a456-426614174000"
                  value={jobIdInput}
                  onChange={(e) => setJobIdInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  aria-label="ID da vaga para auditoria de viés"
                  className="w-full px-3 py-2 text-sm rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-50 focus:outline-none focus:ring-1 focus:ring-gray-400"
                />
              </div>
              <Button
                onClick={handleSearch}
                disabled={!jobIdInput.trim() || loading}
                aria-label="Analisar auditoria de viés para a vaga"
                className="gap-2 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                ) : (
                  <RefreshCw className="w-4 h-4" aria-hidden="true" />
                )}
                Analisar
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Status dinâmico — aria-live para screen readers */}
        <div aria-live="polite" aria-atomic="true" className="sr-only">
          {loading && "Carregando auditoria de viés…"}
          {error && `Erro: ${error}`}
          {auditData && `Auditoria carregada. ${auditData.total_candidates} candidatos avaliados.`}
        </div>

        {/* Error state */}
        {error && (
          <Card className="mb-6 border-red-200 dark:border-red-800" role="alert">
            <CardContent className="p-4">
              <div className="flex items-center gap-3 text-red-600 dark:text-red-400">
                <AlertCircle className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
                <p className="text-sm">{error}</p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Empty state */}
        {!auditData && !loading && !error && (
          <Card className="mb-6">
            <CardContent className="p-8 text-center">
              <Scale className="w-10 h-10 text-gray-300 dark:text-gray-600 mx-auto mb-3" aria-hidden="true" />
              <p className="text-sm text-gray-500">
                Informe o ID da vaga para calcular a auditoria de viés em tempo real.
              </p>
              <p className="text-xs text-gray-400 mt-1">
                Dimensões analisadas: gênero · faixa etária · PCD · região
              </p>
            </CardContent>
          </Card>
        )}

        {/* Loading skeleton */}
        {loading && (
          <Card className="mb-6" role="status" aria-label="Carregando auditoria">
            <CardContent className="p-8 text-center">
              <Loader2 className="w-8 h-8 text-gray-400 animate-spin mx-auto mb-3" aria-hidden="true" />
              <p className="text-sm text-gray-500">Calculando auditoria de viés…</p>
            </CardContent>
          </Card>
        )}

        {/* Results */}
        {auditData && !loading && (
          <>
            {/* Summary cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-purple-50 dark:bg-purple-900/20 rounded-md">
                      <Calendar className="w-5 h-5 text-purple-600" aria-hidden="true" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Avaliado em</p>
                      <p className="text-sm font-semibold text-gray-950 dark:text-gray-50">
                        {formatDate(auditData.evaluated_at)}
                      </p>
                    </div>
                    {getAlertBadge(auditData.has_alerts)}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-md">
                      <BarChart3 className="w-5 h-5 text-gray-600 dark:text-gray-400" aria-hidden="true" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Candidatos Avaliados</p>
                      <p className="text-lg font-semibold text-gray-950 dark:text-gray-50">
                        {auditData.total_candidates}
                      </p>
                    </div>
                    <Badge variant="outline" className="ml-auto">
                      {auditData.dimensions.length} dimensões
                    </Badge>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-md ${alertCount > 0 ? "bg-amber-50 dark:bg-amber-900/20" : "bg-emerald-50 dark:bg-emerald-900/20"}`}>
                      {alertCount > 0 ? (
                        <AlertTriangle className="w-5 h-5 text-amber-600" aria-hidden="true" />
                      ) : (
                        <CheckCircle2 className="w-5 h-5 text-emerald-600" aria-hidden="true" />
                      )}
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Alertas de Viés</p>
                      <p className="text-lg font-semibold text-gray-950 dark:text-gray-50">
                        {alertCount} {alertCount === 1 ? "alerta" : "alertas"}
                      </p>
                    </div>
                    {getAlertBadge(alertCount > 0)}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Dimensions table */}
            <Card className="mb-6">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base font-medium">
                    Resultados por Dimensão — Four-Fifths Rule
                  </CardTitle>
                  <Badge variant="outline" className="font-mono text-xs">
                    {auditData.job_id.slice(0, 8)}…
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full" role="table" aria-label="Resultados de adverse impact por dimensão">
                    <thead>
                      <tr className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
                        <th scope="col" className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-6 py-3">Dimensão</th>
                        <th scope="col" className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-4 py-3">Status</th>
                        <th scope="col" className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-4 py-3">Adverse Impact Ratio</th>
                        <th scope="col" className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-4 py-3">Grupos</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                      {auditData.dimensions.map((dim) => (
                        <tr key={dim.dimension} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                          <td className="px-6 py-4">
                            <p className="text-sm font-medium text-gray-950 dark:text-gray-50">
                              {DIMENSION_LABELS[dim.dimension] ?? dim.dimension}
                            </p>
                            <p className="text-xs text-gray-500 font-mono">{dim.dimension}</p>
                          </td>
                          <td className="px-4 py-4">
                            {getDimensionStatusBadge(dim.alert_level)}
                          </td>
                          <td className="px-4 py-4">
                            <div className="flex items-center gap-2 min-w-[140px]">
                              <div
                                className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden"
                                role="progressbar"
                                aria-valuenow={Math.round(dim.adverse_impact_ratio * 100)}
                                aria-valuemin={0}
                                aria-valuemax={100}
                                aria-label={`Adverse impact ratio: ${Math.round(dim.adverse_impact_ratio * 100)}%`}
                              >
                                <div
                                  className={`h-full rounded-full ${getProgressColor(dim.adverse_impact_ratio)}`}
                                  style={{ width: `${Math.min(dim.adverse_impact_ratio * 100, 100)}%` }}
                                />
                              </div>
                              <span className="text-sm font-mono text-gray-600 dark:text-gray-400">
                                {(dim.adverse_impact_ratio * 100).toFixed(0)}%
                              </span>
                            </div>
                            {dim.below_threshold && (
                              <p className="text-xs text-amber-600 mt-1">Abaixo do limiar (80%)</p>
                            )}
                          </td>
                          <td className="px-4 py-4">
                            <div className="flex flex-wrap gap-1">
                              {Object.entries(dim.groups).map(([label, stats]) => (
                                <span
                                  key={label}
                                  className="text-xs px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400"
                                  title={`${stats.approved}/${stats.count} aprovados`}
                                >
                                  {label}: {(stats.rate * 100).toFixed(0)}%
                                </span>
                              ))}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </>
        )}

        {/* Compliance frameworks */}
        <Card className="mb-6">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <Shield className="w-4 h-4 text-gray-600 dark:text-gray-400" aria-hidden="true" />
              Frameworks de Compliance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              {complianceFrameworks.map((fw) => (
                <div
                  key={fw.id}
                  className="p-3 rounded-md border border-gray-200 dark:border-gray-700"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-950 dark:text-gray-50">{fw.name}</span>
                    <Badge variant="success" className="text-xs">Ativo</Badge>
                  </div>
                  <p className="text-xs text-gray-500">{fw.description}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Methodology note */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-md">
                <Info className="w-5 h-5 text-gray-600 dark:text-gray-400" aria-hidden="true" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-950 dark:text-gray-50">
                  Metodologia de Análise
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Métricas calculadas conforme Four-Fifths Rule (NYC LL144 / EU AI Act Art. 10).
                  Impact Ratio = taxa_grupo_menor / taxa_grupo_maior. Valores abaixo de 80% (0.80)
                  indicam possível viés adverso. Apenas estatísticas agregadas são retornadas — sem
                  identificação individual de candidatos (LGPD-safe).
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

      </div>
    </div>
  )
}
