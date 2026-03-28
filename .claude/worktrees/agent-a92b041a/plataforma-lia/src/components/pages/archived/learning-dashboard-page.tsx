"use client"

import { useState, useEffect, useCallback } from "react"
import { Brain, TrendingUp, FlaskConical, BarChart3, Target, Award, Sparkles, Activity, RefreshCw } from "lucide-react"
import { useAuth } from "@/components/auth-context"

const fetchData = async (endpoint: string) => {
  try {
    const res = await fetch(`/api/backend-proxy/${endpoint}`)
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  }
}

const fetchCompanyId = async (): Promise<string | null> => {
  try {
    const res = await fetch('/api/backend-proxy/company/profile')
    if (!res.ok) return null
    const data = await res.json()
    return data?.id || null
  } catch {
    return null
  }
}

function SkeletonCard() {
  return (
    <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-md p-4 animate-pulse">
      <div className="h-4 bg-zinc-200 dark:bg-zinc-700 rounded w-1/2 mb-3" />
      <div className="h-8 bg-zinc-200 dark:bg-zinc-700 rounded w-1/3 mb-2" />
      <div className="h-3 bg-zinc-200 dark:bg-zinc-700 rounded w-2/3" />
    </div>
  )
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-md p-8 text-center">
      <Brain className="w-8 h-8 text-wedo-cyan mx-auto mb-3" />
      <p className="text-zinc-500 dark:text-zinc-400 text-sm">{message}</p>
    </div>
  )
}

function KPICard({ icon: Icon, label, value, accent }: { icon: any; label: string; value: number | string; accent?: boolean }) {
  return (
    <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-md p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-zinc-500 dark:text-zinc-400 text-sm font-sans">{label}</span>
        <Icon className={`w-4 h-4 ${accent ? "text-cyan-500 dark:text-cyan-400" : "text-zinc-400 dark:text-zinc-500"}`} />
      </div>
      <div className="text-2xl font-bold text-zinc-900 dark:text-zinc-100 font-sans">{value}</div>
    </div>
  )
}

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100)
  const color = pct >= 80 ? "bg-emerald-500" : pct >= 60 ? "bg-amber-500" : "bg-red-500"
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-zinc-200 dark:bg-zinc-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-zinc-500 dark:text-zinc-400 w-10 text-right">{pct}%</span>
    </div>
  )
}

export function LearningDashboardPage() {
  const { user } = useAuth()
  const [companyId, setCompanyId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<"overview" | "patterns" | "wsi" | "abtests">("overview")
  const [loading, setLoading] = useState(true)
  const [patterns, setPatterns] = useState<any[]>([])
  const [promotedSkills, setPromotedSkills] = useState<any[]>([])
  const [successProfiles, setSuccessProfiles] = useState<any[]>([])
  const [abTests, setAbTests] = useState<any[]>([])
  const [wsiCorrelation, setWsiCorrelation] = useState<any>(null)
  const [wsiDistribution, setWsiDistribution] = useState<any>(null)
  const [wsiBlockAccuracy, setWsiBlockAccuracy] = useState<any[]>([])
  const [wsiThreshold, setWsiThreshold] = useState<any>(null)

  useEffect(() => {
    const getCompanyId = async () => {
      const id = await fetchCompanyId()
      setCompanyId(id || "demo-company")
    }
    getCompanyId()
  }, [])

  const loadData = useCallback(async () => {
    if (!companyId) return
    setLoading(true)
    const [p, ps, sp, ab, wc, wd, wb, wt] = await Promise.all([
      fetchData(`v1/patterns/${companyId}/detected`),
      fetchData(`v1/patterns/${companyId}/promoted-skills`),
      fetchData(`v1/patterns/${companyId}/success-profiles`),
      fetchData(`v1/ab-tests`),
      fetchData(`v1/wsi-observability/${companyId}/correlation`),
      fetchData(`v1/wsi-observability/${companyId}/distribution`),
      fetchData(`v1/wsi-observability/${companyId}/block-accuracy`),
      fetchData(`v1/wsi-observability/${companyId}/threshold-analysis`),
    ])
    setPatterns(Array.isArray(p) ? p : p?.patterns ?? [])
    setPromotedSkills(Array.isArray(ps) ? ps : ps?.skills ?? [])
    setSuccessProfiles(Array.isArray(sp) ? sp : sp?.profiles ?? [])
    setAbTests(Array.isArray(ab) ? ab : ab?.tests ?? [])
    setWsiCorrelation(wc)
    setWsiDistribution(wd)
    setWsiBlockAccuracy(Array.isArray(wb) ? wb : wb?.blocks ?? [])
    setWsiThreshold(wt)
    setLoading(false)
  }, [companyId])

  useEffect(() => { loadData() }, [loadData])

  const tabs = [
    { id: "overview" as const, label: "Visão Geral", icon: BarChart3 },
    { id: "patterns" as const, label: "Padrões de Aprendizado", icon: Brain },
    { id: "wsi" as const, label: "WSI Observability", icon: Activity },
    { id: "abtests" as const, label: "A/B Testing", icon: FlaskConical },
  ]

  return (
    <div className="h-full overflow-y-auto bg-gray-50 dark:bg-gray-900 p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-zinc-900 dark:text-zinc-100 font-sans flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-cyan-500 dark:text-cyan-400" />
            Aprendizado & Observabilidade IA
          </h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400 font-sans mt-1">
            Padrões detectados, skills promovidas, WSI e testes A/B
          </p>
        </div>
        <button
          onClick={loadData}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-2 text-sm rounded-md border border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Atualizar
        </button>
      </div>

      <div className="border-b border-zinc-200 dark:border-zinc-800 mb-6">
        <div className="flex gap-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 pb-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? "border-cyan-500 text-cyan-600 dark:text-cyan-400"
                  : "border-transparent text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-300"
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {activeTab === "overview" && (
        <div className="space-y-6">
          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {[...Array(4)].map((_, i) => <SkeletonCard key={i} />)}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <KPICard icon={Brain} label="Padrões Detectados" value={patterns.length} accent />
              <KPICard icon={Award} label="Skills Promovidas" value={promotedSkills.length} />
              <KPICard icon={FlaskConical} label="Testes A/B Ativos" value={abTests.filter((t: any) => t.status === "active" || t.status === "running").length || abTests.length} />
              <KPICard icon={Target} label="Perfis de Sucesso" value={successProfiles.length} />
            </div>
          )}
        </div>
      )}

      {activeTab === "patterns" && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-md overflow-hidden">
            <div className="px-4 py-3 border-b border-zinc-200 dark:border-zinc-800">
              <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">Padrões de Correção Detectados</h2>
            </div>
            {loading ? (
              <div className="p-4 space-y-3">{[...Array(3)].map((_, i) => <div key={i} className="h-10 bg-zinc-100 dark:bg-zinc-800 rounded animate-pulse" />)}</div>
            ) : patterns.length === 0 ? (
              <div className="p-6"><EmptyState message="Nenhum padrão de correção detectado ainda." /></div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/50">
                      <th className="text-left px-4 py-2 text-zinc-500 dark:text-zinc-400 font-medium">Campo</th>
                      <th className="text-left px-4 py-2 text-zinc-500 dark:text-zinc-400 font-medium">Valor Original</th>
                      <th className="text-left px-4 py-2 text-zinc-500 dark:text-zinc-400 font-medium">Valor Corrigido</th>
                      <th className="text-left px-4 py-2 text-zinc-500 dark:text-zinc-400 font-medium w-40">Confiança</th>
                      <th className="text-right px-4 py-2 text-zinc-500 dark:text-zinc-400 font-medium">Frequência</th>
                    </tr>
                  </thead>
                  <tbody>
                    {patterns.map((p: any, i: number) => (
                      <tr key={i} className="border-b border-zinc-100 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800/50">
                        <td className="px-4 py-2.5 text-zinc-900 dark:text-zinc-100 font-medium">{p.field || p.field_name || "—"}</td>
                        <td className="px-4 py-2.5 text-zinc-500 dark:text-zinc-400">{p.original_value || "—"}</td>
                        <td className="px-4 py-2.5 text-cyan-600 dark:text-cyan-400">{p.corrected_value || "—"}</td>
                        <td className="px-4 py-2.5"><ConfidenceBar value={p.confidence ?? 0} /></td>
                        <td className="px-4 py-2.5 text-right text-zinc-900 dark:text-zinc-100 font-medium">{p.frequency ?? p.count ?? 0}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-md overflow-hidden">
            <div className="px-4 py-3 border-b border-zinc-200 dark:border-zinc-800">
              <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                <Award className="w-4 h-4 text-cyan-500 dark:text-cyan-400" />
                Skills Promovidas
              </h2>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">Skills confirmadas ≥ 5 vezes pelo sistema de aprendizado</p>
            </div>
            {loading ? (
              <div className="p-4 space-y-2">{[...Array(3)].map((_, i) => <div key={i} className="h-8 bg-zinc-100 dark:bg-zinc-800 rounded animate-pulse" />)}</div>
            ) : promotedSkills.length === 0 ? (
              <div className="p-6"><EmptyState message="Nenhuma skill promovida ainda." /></div>
            ) : (
              <div className="p-4 flex flex-wrap gap-2">
                {promotedSkills.map((s: any, i: number) => (
                  <span key={i} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm bg-cyan-50 dark:bg-cyan-900/20 text-cyan-700 dark:text-cyan-300 border border-cyan-200 dark:border-cyan-800">
                    <Award className="w-3 h-3" />
                    {s.skill || s.name || s}
                    {(s.confirmations || s.count) && (
                      <span className="text-xs text-cyan-500 dark:text-cyan-400 ml-1">({s.confirmations || s.count}×)</span>
                    )}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === "wsi" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-md p-4">
              <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 mb-3 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-cyan-500 dark:text-cyan-400" />
                Correlação Score vs Resultado
              </h3>
              {loading ? (
                <div className="h-32 bg-zinc-100 dark:bg-zinc-800 rounded animate-pulse" />
              ) : !wsiCorrelation ? (
                <EmptyState message="Dados de correlação indisponíveis." />
              ) : (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-zinc-500 dark:text-zinc-400">Coeficiente de correlação</span>
                    <span className="text-lg font-bold text-zinc-900 dark:text-zinc-100">{wsiCorrelation.correlation_coefficient?.toFixed(3) ?? wsiCorrelation.coefficient?.toFixed(3) ?? "—"}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-zinc-500 dark:text-zinc-400">P-valor</span>
                    <span className="text-sm text-zinc-700 dark:text-zinc-300">{wsiCorrelation.p_value?.toFixed(4) ?? "—"}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-zinc-500 dark:text-zinc-400">Amostras</span>
                    <span className="text-sm text-zinc-700 dark:text-zinc-300">{wsiCorrelation.sample_size ?? wsiCorrelation.n ?? "—"}</span>
                  </div>
                </div>
              )}
            </div>

            <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-md p-4">
              <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 mb-3 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-cyan-500 dark:text-cyan-400" />
                Distribuição de Scores
              </h3>
              {loading ? (
                <div className="h-32 bg-zinc-100 dark:bg-zinc-800 rounded animate-pulse" />
              ) : !wsiDistribution ? (
                <EmptyState message="Dados de distribuição indisponíveis." />
              ) : (
                <div className="space-y-2">
                  {(wsiDistribution.buckets ?? wsiDistribution.ranges ?? Object.entries(wsiDistribution).filter(([k]) => k !== "total")).map((item: any, i: number) => {
                    const label = item.range ?? item.label ?? item[0] ?? `Faixa ${i + 1}`
                    const count = item.count ?? item.value ?? item[1] ?? 0
                    const total = wsiDistribution.total ?? 100
                    const pct = total > 0 ? Math.round((count / total) * 100) : 0
                    return (
                      <div key={i} className="flex items-center gap-3">
                        <span className="text-xs text-zinc-500 dark:text-zinc-400 w-20 shrink-0">{label}</span>
                        <div className="flex-1 h-5 bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden">
                          <div className="h-full bg-cyan-500 dark:bg-cyan-400 rounded-full transition-all" style={{ width: `${pct}%` }} />
                        </div>
                        <span className="text-xs font-medium text-zinc-700 dark:text-zinc-300 w-12 text-right">{count}</span>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </div>

          <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-md overflow-hidden">
            <div className="px-4 py-3 border-b border-zinc-200 dark:border-zinc-800">
              <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">Acurácia por Bloco WSI</h3>
            </div>
            {loading ? (
              <div className="p-4 space-y-2">{[...Array(3)].map((_, i) => <div key={i} className="h-8 bg-zinc-100 dark:bg-zinc-800 rounded animate-pulse" />)}</div>
            ) : wsiBlockAccuracy.length === 0 ? (
              <div className="p-6"><EmptyState message="Dados de acurácia por bloco indisponíveis." /></div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/50">
                      <th className="text-left px-4 py-2 text-zinc-500 dark:text-zinc-400 font-medium">Bloco</th>
                      <th className="text-left px-4 py-2 text-zinc-500 dark:text-zinc-400 font-medium w-40">Acurácia</th>
                      <th className="text-right px-4 py-2 text-zinc-500 dark:text-zinc-400 font-medium">Avaliações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {wsiBlockAccuracy.map((b: any, i: number) => (
                      <tr key={i} className="border-b border-zinc-100 dark:border-zinc-800">
                        <td className="px-4 py-2.5 text-zinc-900 dark:text-zinc-100 font-medium">{b.block_name ?? b.block ?? b.name ?? `Bloco ${i + 1}`}</td>
                        <td className="px-4 py-2.5"><ConfidenceBar value={b.accuracy ?? b.score ?? 0} /></td>
                        <td className="px-4 py-2.5 text-right text-zinc-700 dark:text-zinc-300">{b.evaluations ?? b.total ?? b.count ?? 0}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-md p-4">
            <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 mb-3 flex items-center gap-2">
              <Target className="w-4 h-4 text-cyan-500 dark:text-cyan-400" />
              Análise de Threshold
            </h3>
            {loading ? (
              <div className="h-20 bg-zinc-100 dark:bg-zinc-800 rounded animate-pulse" />
            ) : !wsiThreshold ? (
              <EmptyState message="Dados de threshold indisponíveis." />
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                {Object.entries(wsiThreshold).map(([key, val]: [string, any]) => (
                  <div key={key} className="text-center">
                    <p className="text-xs text-zinc-500 dark:text-zinc-400 mb-1">{key.replace(/_/g, " ")}</p>
                    <p className="text-lg font-bold text-zinc-900 dark:text-zinc-100">{typeof val === "number" ? val.toFixed(2) : String(val)}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === "abtests" && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-md overflow-hidden">
            <div className="px-4 py-3 border-b border-zinc-200 dark:border-zinc-800">
              <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                <FlaskConical className="w-4 h-4 text-cyan-500 dark:text-cyan-400" />
                Testes A/B
              </h2>
            </div>
            {loading ? (
              <div className="p-4 space-y-3">{[...Array(3)].map((_, i) => <div key={i} className="h-12 bg-zinc-100 dark:bg-zinc-800 rounded animate-pulse" />)}</div>
            ) : abTests.length === 0 ? (
              <div className="p-6"><EmptyState message="Nenhum teste A/B configurado." /></div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/50">
                      <th className="text-left px-4 py-2 text-zinc-500 dark:text-zinc-400 font-medium">Teste</th>
                      <th className="text-left px-4 py-2 text-zinc-500 dark:text-zinc-400 font-medium">Variantes</th>
                      <th className="text-left px-4 py-2 text-zinc-500 dark:text-zinc-400 font-medium">Tráfego</th>
                      <th className="text-left px-4 py-2 text-zinc-500 dark:text-zinc-400 font-medium">Status</th>
                      <th className="text-left px-4 py-2 text-zinc-500 dark:text-zinc-400 font-medium">Significância</th>
                    </tr>
                  </thead>
                  <tbody>
                    {abTests.map((test: any, i: number) => (
                      <tr key={i} className="border-b border-zinc-100 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800/50">
                        <td className="px-4 py-2.5 text-zinc-900 dark:text-zinc-100 font-medium">{test.name ?? test.test_name ?? `Teste ${i + 1}`}</td>
                        <td className="px-4 py-2.5 text-zinc-500 dark:text-zinc-400">
                          {(test.variants ?? []).map((v: any, j: number) => (
                            <span key={j} className="inline-block mr-2 px-2 py-0.5 bg-zinc-100 dark:bg-zinc-800 rounded text-xs">
                              {v.name ?? v}
                            </span>
                          )) || "—"}
                        </td>
                        <td className="px-4 py-2.5 text-zinc-700 dark:text-zinc-300">
                          {test.traffic_split ?? test.traffic_percentage ? `${test.traffic_split ?? test.traffic_percentage}%` : "—"}
                        </td>
                        <td className="px-4 py-2.5">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                            (test.status === "active" || test.status === "running")
                              ? "bg-emerald-100 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400"
                              : test.status === "completed"
                              ? "bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400"
                              : "bg-amber-100 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400"
                          }`}>
                            {test.status ?? "—"}
                          </span>
                        </td>
                        <td className="px-4 py-2.5 text-zinc-700 dark:text-zinc-300">
                          {test.significance != null ? `${(test.significance * 100).toFixed(1)}%` : test.p_value != null ? `p=${test.p_value.toFixed(4)}` : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
