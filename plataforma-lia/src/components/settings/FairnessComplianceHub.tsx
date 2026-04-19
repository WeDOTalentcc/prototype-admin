"use client"

import React, { useEffect, useState, useCallback } from"react"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from"@/components/ui/select"
import { Shield, AlertTriangle, TrendingDown, Download, FileText, Clock, CheckCircle } from"lucide-react"
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from"recharts"
import { textStyles, cardStyles } from"@/lib/design-tokens"
import { StudioComplianceView } from"./StudioComplianceView"

interface FairnessSummary {
  total_blocks: number
  total_events: number
  by_category: CategorySummary[]
}

interface CategorySummary {
  category: string
  total_blocks: number
  total_warnings: number
  last_occurrence: string | null
}

interface AuditLogEntry {
  id: string
  category: string
  is_blocked: boolean
  blocked_terms: string[]
  soft_warnings: string[]
  context: string | null
  created_at: string
}

interface LGPDRequestItem {
  id: string
  candidate_id_masked: string
  vacancy_title: string
  vacancy_id: string
  requested_at: string
  deadline: string
  status: "pending" | "responded" | "closed"
}

function LGPDCandidatosView() {
  const [items, setItems] = React.useState<LGPDRequestItem[]>([])
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)
  const [pendingCount, setPendingCount] = React.useState(0)
  const [responding, setResponding] = React.useState<string | null>(null)

  async function fetchData() {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch("/api/backend-proxy/rh/lgpd-requests", { credentials: "include" })
      if (!res.ok) throw new Error("Erro ao carregar pedidos")
      const data = await res.json()
      const payload = data.data || data
      setItems(payload.items || [])
      setPendingCount(payload.pending_count || 0)
    } catch (err: any) {
      setError(err.message || "Erro desconhecido")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [])

  async function handleRespond(id: string) {
    setResponding(id)
    try {
      const res = await fetch(`/api/backend-proxy/rh/lgpd-requests/${id}/respond`, {
        method: "PATCH",
        credentials: "include",
      })
      if (!res.ok) throw new Error("Falha ao atualizar")
      setItems(prev => prev.map(i => i.id === id ? { ...i, status: "responded" } : i))
      setPendingCount(prev => Math.max(0, prev - 1))
    } catch (err: any) {
      alert(err.message)
    } finally {
      setResponding(null)
    }
  }

  const statusConfig: Record<string, { label: string; cls: string }> = {
    pending: { label: "Pendente", cls: "bg-amber-500/15 text-amber-600" },
    responded: { label: "Respondido", cls: "bg-green-500/15 text-green-600" },
    closed: { label: "Encerrado", cls: "bg-lia-bg-tertiary text-lia-text-secondary" },
  }

  const isOverdue = (deadline: string) => new Date(deadline) < new Date()

  if (error) return (
    <div className="text-center py-12">
      <AlertTriangle className="w-10 h-10 text-status-error mx-auto mb-3" />
      <p className="text-lia-text-secondary">{error}</p>
    </div>
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-lia-text-primary">LGPD Art. 20 — Pedidos de Candidatos</h2>
          <p className="text-sm text-lia-text-secondary mt-0.5">Direito à explicação sobre avaliações. Prazo legal: 15 dias úteis.</p>
        </div>
        {pendingCount > 0 && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20">
            <Clock className="w-4 h-4 text-amber-500" />
            <span className="text-sm font-medium text-amber-600">{pendingCount} pendente{pendingCount > 1 ? "s" : ""}</span>
          </div>
        )}
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-14 bg-lia-bg-tertiary rounded-lg animate-pulse" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-12">
          <CheckCircle className="w-10 h-10 text-green-500 mx-auto mb-3" />
          <p className="text-sm font-medium text-lia-text-primary">Nenhum pedido registrado</p>
          <p className="text-sm text-lia-text-secondary">Candidatos ainda não solicitaram explicação sobre suas avaliações.</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-lia-border">
                <th className="text-left py-2 px-3 font-medium text-lia-text-secondary">Candidato</th>
                <th className="text-left py-2 px-3 font-medium text-lia-text-secondary">Vaga</th>
                <th className="text-left py-2 px-3 font-medium text-lia-text-secondary">Solicitado em</th>
                <th className="text-left py-2 px-3 font-medium text-lia-text-secondary">Prazo</th>
                <th className="text-left py-2 px-3 font-medium text-lia-text-secondary">Status</th>
                <th className="text-left py-2 px-3 font-medium text-lia-text-secondary">Ação</th>
              </tr>
            </thead>
            <tbody>
              {items.map(item => {
                const cfg = statusConfig[item.status] || statusConfig.pending
                const overdue = item.status === "pending" && isOverdue(item.deadline)
                return (
                  <tr key={item.id} className={`border-b border-lia-border/30 hover:bg-lia-bg-tertiary/40 ${overdue ? "bg-red-500/5" : ""}`}>
                    <td className="py-2.5 px-3 font-mono text-xs text-lia-text-secondary">{item.candidate_id_masked}</td>
                    <td className="py-2.5 px-3 text-lia-text-primary max-w-[180px] truncate">{item.vacancy_title}</td>
                    <td className="py-2.5 px-3 text-lia-text-secondary whitespace-nowrap">
                      {new Date(item.requested_at).toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" })}
                    </td>
                    <td className={`py-2.5 px-3 whitespace-nowrap ${overdue ? "text-red-500 font-medium" : "text-lia-text-secondary"}`}>
                      {overdue && <AlertTriangle className="inline w-3 h-3 mr-1" />}
                      {new Date(item.deadline).toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" })}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${cfg.cls}`}>{cfg.label}</span>
                    </td>
                    <td className="py-2.5 px-3">
                      {item.status === "pending" && (
                        <button
                          onClick={() => handleRespond(item.id)}
                          disabled={responding === item.id}
                          className="text-xs px-2.5 py-1 rounded-md bg-wedo-cyan/10 text-wedo-cyan hover:bg-wedo-cyan/20 disabled:opacity-50 transition-colors"
                        >
                          {responding === item.id ? "..." : "Marcar respondido"}
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

const categoryLabels: Record<string, string> = {
  gender:"Genero",
  age:"Idade",
  race:"Raca",
  disability:"Deficiencia",
  religion:"Religiao",
  sexual_orientation:"Orient. Sexual",
  nationality:"Nacionalidade",
  marital_status:"Estado Civil",
  appearance:"Aparencia",
}

function translateCategory(cat: string): string {
  return categoryLabels[cat] || cat.charAt(0).toUpperCase() + cat.slice(1)
}

interface FairnessComplianceHubProps {
  activeSubsection: string
}

export function FairnessComplianceHub({ activeSubsection }: FairnessComplianceHubProps) {
  // P2.3: Studio subsection has its own dedicated view
  if (activeSubsection === "studio") {
    return <StudioComplianceView />
  }
  // LGPD Art. 20 candidate requests tab
  if (activeSubsection === "lgpd-candidatos") {
    return <LGPDCandidatosView />
  }

  const [period, setPeriod] = useState("30")
  const [summary, setSummary] = useState<FairnessSummary | null>(null)
  const [logs, setLogs] = useState<AuditLogEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchData() {
      setLoading(true)
      setError(null)
      try {
        const [summaryRes, logsRes] = await Promise.all([
          fetch(`/api/backend-proxy/fairness-report/summary?days=${period}`, { credentials:"include" }),
          fetch(`/api/backend-proxy/fairness-report/summary?days=${period}`, { credentials:"include" }),
        ])
        if (!summaryRes.ok || !logsRes.ok) throw new Error("Erro ao carregar dados")
        const summaryData = await summaryRes.json()
        const logsData = await logsRes.json()
        setSummary(summaryData)
        setLogs(logsData.items || [])
      } catch (err: any) {
        setError(err.message ||"Erro ao carregar dados de fairness")
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [period])

  const handleExport = (format:"csv" |"json") => {
    window.open(`/api/backend-proxy/fairness-report/export?format=${format}&days=${period}`,"_blank")
  }

  const totalWarnings = summary ? summary.total_events - summary.total_blocks : 0

  const chartData = summary?.by_category.map((c) => ({
    name: translateCategory(c.category),
    bloqueios: c.total_blocks,
    alertas: c.total_warnings,
  })) || []

  if (error) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="w-10 h-10 text-status-error mx-auto mb-3" />
        <h3 className={textStyles.subtitle}>Erro ao carregar compliance</h3>
        <p className={textStyles.description}>{error}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className={textStyles.subtitle}>Fairness & Compliance</h2>
          <p className={textStyles.description}>Monitoramento de equidade e conformidade da IA</p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={period} onValueChange={setPeriod}>
            <SelectTrigger className="w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">7 dias</SelectItem>
              <SelectItem value="30">30 dias</SelectItem>
              <SelectItem value="90">90 dias</SelectItem>
              <SelectItem value="365">365 dias</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm" onClick={() => handleExport("csv")}>
            <Download className="w-4 h-4 mr-1.5" /> CSV
          </Button>
          <Button variant="outline" size="sm" onClick={() => handleExport("json")}>
            <Download className="w-4 h-4 mr-1.5" /> JSON
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className={cardStyles.default}>
              <CardContent className="p-5">
                <div className="animate-pulse space-y-3">
                  <div className="h-4 bg-lia-bg-tertiary rounded w-2/3" />
                  <div className="h-8 bg-lia-bg-tertiary rounded w-1/3" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className={cardStyles.default}>
            <CardContent className="p-5">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-9 h-9 rounded-lg bg-blue-500/10 flex items-center justify-center">
                  <Shield className="w-5 h-5 text-blue-500" />
                </div>
                <span className={textStyles.description}>Total de Eventos</span>
              </div>
              <p className="text-2xl font-semibold text-lia-text-primary">{summary?.total_events ?? 0}</p>
            </CardContent>
          </Card>
          <Card className={cardStyles.default}>
            <CardContent className="p-5">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-9 h-9 rounded-lg bg-red-500/10 flex items-center justify-center">
                  <AlertTriangle className="w-5 h-5 text-red-500" />
                </div>
                <span className={textStyles.description}>Bloqueios</span>
              </div>
              <p className="text-2xl font-semibold text-red-500">{summary?.total_blocks ?? 0}</p>
            </CardContent>
          </Card>
          <Card className={cardStyles.default}>
            <CardContent className="p-5">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-9 h-9 rounded-lg bg-yellow-500/10 flex items-center justify-center">
                  <TrendingDown className="w-5 h-5 text-yellow-500" />
                </div>
                <span className={textStyles.description}>Alertas</span>
              </div>
              <p className="text-2xl font-semibold text-yellow-500">{totalWarnings}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Bar Chart */}
      {!loading && chartData.length > 0 && (
        <Card className={cardStyles.default}>
          <CardHeader className="pb-2">
            <CardTitle className={textStyles.subtitle}>Eventos por Categoria</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="bloqueios" fill="#ef4444" radius={[4, 4, 0, 0]} name="Bloqueios" />
                <Bar dataKey="alertas" fill="#eab308" radius={[4, 4, 0, 0]} name="Alertas" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Recent Incidents Table */}
      {!loading && logs.length > 0 && (
        <Card className={cardStyles.default}>
          <CardHeader className="pb-2">
            <CardTitle className={textStyles.subtitle}>Incidentes Recentes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-lia-border">
                    <th className="text-left py-2 px-3 font-medium text-lia-text-secondary">Categoria</th>
                    <th className="text-left py-2 px-3 font-medium text-lia-text-secondary">Tipo</th>
                    <th className="text-left py-2 px-3 font-medium text-lia-text-secondary">Termos</th>
                    <th className="text-left py-2 px-3 font-medium text-lia-text-secondary">Data</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log) => (
                    <tr key={log.id} className="border-lia-border/50 hover:bg-lia-bg-tertiary/50">
                      <td className="py-2.5 px-3">
                        <Chip variant="neutral" className="text-xs">
                          {translateCategory(log.category)}
                        </Chip>
                      </td>
                      <td className="py-2.5 px-3">
                        {log.is_blocked ? (
                          <Chip variant="neutral" muted className="bg-red-500/15 text-red-500 text-xs">Bloqueado</Chip>
                        ) : (
                          <Chip variant="neutral" muted className="bg-yellow-500/15 text-yellow-600 text-xs">Alerta</Chip>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-lia-text-secondary max-w-[200px] truncate">
                        {log.is_blocked
                          ? (log.blocked_terms || []).join(",")
                          : (log.soft_warnings || []).join(",")}
                      </td>
                      <td className="py-2.5 px-3 text-lia-text-secondary whitespace-nowrap">
                        {new Date(log.created_at).toLocaleDateString("pt-BR", {
                          day:"2-digit",
                          month:"short",
                          year:"numeric",
                          hour:"2-digit",
                          minute:"2-digit",
                        })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {!loading && logs.length === 0 && !error && (
        <Card className={cardStyles.default}>
          <CardContent className="py-8 text-center">
            <Shield className="w-10 h-10 text-green-500 mx-auto mb-3" />
            <p className={textStyles.subtitle}>Nenhum incidente registrado</p>
            <p className={textStyles.description}>Nenhum evento de fairness no periodo selecionado.</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
