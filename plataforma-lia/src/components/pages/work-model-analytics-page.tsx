"use client"

import { formatBRL } from "@/lib/pricing"
import { useState, useEffect, useMemo, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useAuthStore } from "@/stores/auth-store"
import {
  BarChart3, PieChart, MapPin, Users, TrendingUp, Download,
  Filter, Calendar, Building, Target, ArrowUp, ArrowDown,
  RotateCcw, Zap, Clock, Globe, Home, Briefcase
} from "lucide-react"

interface WorkModelData {
  modelo: 'remoto' | 'híbrido' | 'presencial'
  candidatos: number
  percentual: number
  crescimento: number
  salarioMedio: number
}

interface CargoWorkModel {
  cargo: string
  remoto: number
  hibrido: number
  presencial: number
  total: number
}

interface RegionalData {
  regiao: string
  estado: string
  remoto: number
  hibrido: number
  presencial: number
  total: number
}

interface SeniorityData {
  nivel: string
  experiencia: string
  remoto: number
  hibrido: number
  presencial: number
  total: number
  salarioMedio: number
}

const FALLBACK_DISTRIBUTION: WorkModelData[] = [
  { modelo: 'remoto', candidatos: 0, percentual: 0, crescimento: 0, salarioMedio: 0 },
  { modelo: 'híbrido', candidatos: 0, percentual: 0, crescimento: 0, salarioMedio: 0 },
  { modelo: 'presencial', candidatos: 0, percentual: 0, crescimento: 0, salarioMedio: 0 },
]

export function WorkModelAnalyticsPage() {
  const [selectedPeriod, setSelectedPeriod] = useState<'30d' | '90d' | '6m' | '1y'>('90d')
  const [selectedRegion, setSelectedRegion] = useState<string>('all')
  const [selectedCargo, setSelectedCargo] = useState<string>('all')
  const [selectedSeniority, setSelectedSeniority] = useState<string>('all')
  const [backendData, setBackendData] = useState<any>(null)
  const [dataLoading, setDataLoading] = useState(false)
  const user = useAuthStore((s) => s.user)
  const companyId = (user as any)?.company_id || ""

  const fetchAnalytics = useCallback(async () => {
    setDataLoading(true)
    try {
      const res = await fetch(`/api/backend-proxy/jobs/work-model-analytics?period=${selectedPeriod}`)
      if (res.ok) {
        const data = await res.json()
        setBackendData(data)
      }
    } catch (e) {
      console.error("[WorkModelAnalytics] fetch error:", e)
    } finally {
      setDataLoading(false)
    }
  }, [selectedPeriod])

  useEffect(() => {
    fetchAnalytics()
  }, [fetchAnalytics])

  const workModelDistribution: WorkModelData[] = useMemo(() => {
    if (!backendData?.distribution?.length) return FALLBACK_DISTRIBUTION
    return backendData.distribution.map((d: any) => ({
      modelo: d.modelo as any,
      candidatos: d.candidatos,
      percentual: d.percentual,
      crescimento: 0,
      salarioMedio: d.salarioMedio || 0,
    }))
  }, [backendData])

  const cargoWorkModels: CargoWorkModel[] = useMemo(() => {
    if (!backendData?.by_title?.length) return []
    return backendData.by_title
  }, [backendData])

  const regionalData: RegionalData[] = useMemo(() => {
    if (!backendData?.by_location?.length) return []
    return backendData.by_location.map((d: any) => ({
      regiao: d.regiao,
      estado: d.regiao,
      remoto: d.remoto || 0,
      hibrido: d.hibrido || 0,
      presencial: d.presencial || 0,
      total: d.total || 0,
    }))
  }, [backendData])

  const seniorityData: SeniorityData[] = []

  const totalCandidatos = workModelDistribution.reduce((sum, item) => sum + item.candidatos, 0)
  const salarioMedioGeral = totalCandidatos > 0
    ? workModelDistribution.reduce((sum, item) => sum + (item.salarioMedio * item.candidatos), 0) / totalCandidatos
    : 0

  // Função para gerar cores das barras
  const getWorkModelColor = (modelo: string) => {
    switch (modelo) {
      case 'remoto': return 'bg-status-success'
      case 'híbrido': return 'bg-lia-bg-inverse dark:bg-lia-text-tertiary'
      case 'presencial': return 'bg-lia-bg-secondary0'
      default: return 'bg-lia-border-medium'
    }
  }

  // Função para exportar dados
  const handleExport = (format: 'csv' | 'pdf' | 'excel') => {
    // TODO: Implementar exportação real
    alert(`📊 Relatório de Modelos de Trabalho exportado em ${format.toUpperCase()}!`)
  }

  return (
    <div className="h-screen bg-lia-bg-primary dark:bg-lia-bg-primary overflow-hidden">
      <div className="flex flex-col h-full">

        {/* Header */}
        <div className="p-6 bg-lia-bg-primary dark:bg-lia-bg-primary border-b border-lia-border-subtle dark:border-lia-border-subtle">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-lia-text-primary mb-2 flex items-center gap-3">
                <BarChart3 className="w-6 h-6 text-lia-text-secondary" />
                Analytics: Modelos de Trabalho
              </h1>
              <p className="text-sm text-lia-text-secondary">
                Análise completa da distribuição e preferências de modelos de trabalho
              </p>
            </div>

            <div className="flex items-center gap-3">
              {/* Filtros de período */}
              <div className="flex bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-md p-1">
                {(['30d', '90d', '6m', '1y'] as const).map((period) => (
                  <button
                    key={period}
                    onClick={() => setSelectedPeriod(period)}
                    className={`px-3 py-1 text-xs font-medium rounded-md transition-colors motion-reduce:transition-none ${
                      selectedPeriod === period
                        ? 'bg-lia-btn-primary-bg dark:bg-lia-bg-secondary text-white'
                        : 'text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse'
                    }`}
                  >
                    {period === '30d' ? '30 dias' : period === '90d' ? '90 dias' : period === '6m' ? '6 meses' : '1 ano'}
                  </button>
                ))}
              </div>

              {/* Botões de exportação */}
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleExport('csv')}
                  className="gap-2"
                >
                  <Download className="w-4 h-4" />
                  CSV
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleExport('excel')}
                  className="gap-2"
                >
                  <Download className="w-4 h-4" />
                  Excel
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleExport('pdf')}
                  className="gap-2"
                >
                  <Download className="w-4 h-4" />
                  PDF
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 overflow-auto p-6">
          <div className="max-w-7xl mx-auto space-y-6">

            {/* KPIs principais */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              {workModelDistribution.map((item) => (
                <Card key={item.modelo} className="border-l-4 border-l-lia-border-medium dark:border-l-lia-border-medium">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-sm font-medium text-lia-text-secondary capitalize flex items-center gap-2">
                        {item.modelo === 'remoto' && <Home className="w-4 h-4 text-status-success" />}
                        {item.modelo === 'híbrido' && <Globe className="w-4 h-4 text-lia-text-secondary" />}
                        {item.modelo === 'presencial' && <Building className="w-4 h-4 text-lia-text-secondary" />}
                        {item.modelo}
                      </CardTitle>
                      <div className={`flex items-center gap-1 text-xs ${
                        item.crescimento > 0 ? 'text-status-success' : 'text-status-error'
                      }`}>
                        {item.crescimento > 0 ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />}
                        {Math.abs(item.crescimento)}%
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="text-2xl font-bold text-lia-text-primary">
                        {item.candidatos}
                      </div>
                      <div className="text-sm text-lia-text-secondary">
                        {item.percentual}% do total
                      </div>
                      <div className="text-sm font-medium text-lia-text-primary">
                        {formatBRL(item.salarioMedio)} salário médio
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}

              {/* Card de total */}
              <Card className="border-l-4 border-l-purple-500">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium text-lia-text-secondary flex items-center gap-2">
                    <Users className="w-4 h-4 text-wedo-purple" />
                    Total Geral
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="text-2xl font-bold text-lia-text-primary">
                      {totalCandidatos}
                    </div>
                    <div className="text-sm text-lia-text-secondary">
                      Candidatos analisados
                    </div>
                    <div className="text-sm font-medium text-lia-text-primary">
                      {formatBRL(Math.round(salarioMedioGeral))} salário médio
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Seção de gráficos principais */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

              {/* Distribuição por Cargo */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Briefcase className="w-5 h-5 text-lia-text-secondary" />
                    Distribuição por Cargo
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {cargoWorkModels.slice(0, 8).map((cargo, index) => (
                      <div key={cargo.cargo} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-lia-text-primary">
                            {cargo.cargo}
                          </span>
                          <span className="text-xs text-lia-text-primary">
                            {cargo.total} candidatos
                          </span>
                        </div>
                        <div className="flex rounded-full overflow-hidden h-2 bg-lia-interactive-active dark:bg-lia-bg-elevated">
                          <div
                            className="bg-status-success"
                            style={{width: `${(cargo.remoto / cargo.total) * 100}%`}}
                            title={`Remoto: ${cargo.remoto}`}
                          />
                          <div
                            className="bg-lia-bg-inverse dark:bg-lia-text-tertiary"
                            style={{width: `${(cargo.hibrido / cargo.total) * 100}%`}}
                            title={`Híbrido: ${cargo.hibrido}`}
                          />
                          <div
                            className="bg-lia-bg-secondary0"
                            style={{width: `${(cargo.presencial / cargo.total) * 100}%`}}
                            title={`Presencial: ${cargo.presencial}`}
                          />
                        </div>
                        <div className="flex items-center gap-4 text-xs text-lia-text-secondary">
                          <div className="flex items-center gap-1">
                            <div className="w-2 h-2 bg-status-success rounded-full"></div>
                            Remoto: {cargo.remoto}
                          </div>
                          <div className="flex items-center gap-1">
                            <div className="w-2 h-2 bg-lia-bg-inverse dark:bg-lia-text-tertiary rounded-full"></div>
                            Híbrido: {cargo.hibrido}
                          </div>
                          <div className="flex items-center gap-1">
                            <div className="w-2 h-2 bg-lia-bg-secondary0 rounded-full"></div>
                            Presencial: {cargo.presencial}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Distribuição por Senioridade */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-wedo-purple" />
                    Distribuição por Senioridade
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {seniorityData.map((level, index) => (
                      <div key={level.nivel} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <div>
                            <span className="text-sm font-medium text-lia-text-primary">
                              {level.nivel}
                            </span>
                            <span className="text-xs text-lia-text-primary ml-2">
                              ({level.experiencia})
                            </span>
                          </div>
                          <div className="text-right">
                            <div className="text-xs text-lia-text-primary">
                              {level.total} candidatos
                            </div>
                            <div className="text-xs font-medium text-status-success">
                              {formatBRL(level.salarioMedio)}
                            </div>
                          </div>
                        </div>
                        <div className="flex rounded-full overflow-hidden h-3 bg-lia-interactive-active dark:bg-lia-bg-elevated">
                          <div
                            className="bg-status-success"
                            style={{width: `${(level.remoto / level.total) * 100}%`}}
                            title={`Remoto: ${level.remoto}`}
                          />
                          <div
                            className="bg-lia-bg-inverse dark:bg-lia-text-tertiary"
                            style={{width: `${(level.hibrido / level.total) * 100}%`}}
                            title={`Híbrido: ${level.hibrido}`}
                          />
                          <div
                            className="bg-lia-bg-secondary0"
                            style={{width: `${(level.presencial / level.total) * 100}%`}}
                            title={`Presencial: ${level.presencial}`}
                          />
                        </div>
                        <div className="flex items-center gap-4 text-xs text-lia-text-secondary">
                          <div className="flex items-center gap-1">
                            <div className="w-2 h-2 bg-status-success rounded-full"></div>
                            {level.remoto} ({Math.round((level.remoto / level.total) * 100)}%)
                          </div>
                          <div className="flex items-center gap-1">
                            <div className="w-2 h-2 bg-lia-bg-inverse dark:bg-lia-text-tertiary rounded-full"></div>
                            {level.hibrido} ({Math.round((level.hibrido / level.total) * 100)}%)
                          </div>
                          <div className="flex items-center gap-1">
                            <div className="w-2 h-2 bg-lia-bg-secondary0 rounded-full"></div>
                            {level.presencial} ({Math.round((level.presencial / level.total) * 100)}%)
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Análise Regional */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MapPin className="w-5 h-5 text-wedo-orange" />
                  Distribuição Regional
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {regionalData.map((region, index) => (
                    <div key={region.estado} className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium text-lia-text-primary">
                            {region.estado}
                          </h4>
                          <p className="text-xs text-lia-text-primary">{region.regiao}</p>
                        </div>
                        <Badge variant="outline" className="text-xs">
                          {region.total} candidatos
                        </Badge>
                      </div>

                      <div className="space-y-2">
                        <div className="flex rounded-full overflow-hidden h-2 bg-lia-interactive-active dark:bg-lia-bg-elevated">
                          <div
                            className="bg-status-success"
                            style={{width: `${(region.remoto / region.total) * 100}%`}}
                          />
                          <div
                            className="bg-lia-bg-inverse dark:bg-lia-text-tertiary"
                            style={{width: `${(region.hibrido / region.total) * 100}%`}}
                          />
                          <div
                            className="bg-lia-bg-secondary0"
                            style={{width: `${(region.presencial / region.total) * 100}%`}}
                          />
                        </div>

                        <div className="grid grid-cols-3 gap-2 text-xs">
                          <div className="text-center">
                            <div className="font-medium text-status-success">{region.remoto}</div>
                            <div className="text-lia-text-primary">Remoto</div>
                          </div>
                          <div className="text-center">
                            <div className="font-medium text-lia-text-secondary">{region.hibrido}</div>
                            <div className="text-lia-text-primary">Híbrido</div>
                          </div>
                          <div className="text-center">
                            <div className="font-medium text-lia-text-secondary">{region.presencial}</div>
                            <div className="text-lia-text-primary">Presencial</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Insights e Recomendações */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

              {/* Insights */}
              <Card className="border-l-4 border-l-green-500">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Zap className="w-5 h-5 text-status-success" />
                    Insights Principais
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="p-3 bg-status-success/10 dark:bg-status-success/20 rounded-md">
                      <h4 className="text-sm font-medium text-status-success dark:text-status-success mb-1">
                        🏆 Modelo Híbrido Dominante
                      </h4>
                      <p className="text-xs text-status-success dark:text-status-success">
                        48.9% dos candidatos preferem modelo híbrido, com crescimento de 8.3%
                      </p>
                    </div>

                    <div className="p-3 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-md">
                      <h4 className="text-sm font-medium text-lia-text-secondary mb-1">
                        💰 Salário Remoto vs Híbrido
                      </h4>
                      <p className="text-xs text-lia-text-secondary/80">
                        Trabalho híbrido oferece salário médio 8.2% maior que remoto
                      </p>
                    </div>

                    <div className="p-3 bg-wedo-orange/10 dark:bg-wedo-orange/20 rounded-md">
                      <h4 className="text-sm font-medium text-wedo-orange dark:text-wedo-orange mb-1">
                        📍 Concentração em SP/RJ
                      </h4>
                      <p className="text-xs text-wedo-orange dark:text-wedo-orange">
                        71% dos candidatos estão concentrados em São Paulo e Rio de Janeiro
                      </p>
                    </div>

                    <div className="p-3 bg-wedo-purple/10 dark:bg-wedo-purple/20 rounded-md">
                      <h4 className="text-sm font-medium text-wedo-purple dark:text-wedo-purple mb-1">
                        🚀 Desenvolvedores Preferem Remoto
                      </h4>
                      <p className="text-xs text-wedo-purple dark:text-wedo-purple">
                        Full Stack e Frontend lideram preferência por trabalho remoto
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Recomendações */}
              <Card className="border-l-4 border-l-purple-500">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Target className="w-5 h-5 text-wedo-purple" />
                    Recomendações Estratégicas
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md">
                      <h4 className="text-sm font-medium text-lia-text-primary mb-1">
                        🎯 Focar em Modelo Híbrido
                      </h4>
                      <p className="text-xs text-lia-text-secondary">
                        Priorizar vagas híbridas para atrair 48.9% dos candidatos disponíveis
                      </p>
                    </div>

                    <div className="p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md">
                      <h4 className="text-sm font-medium text-lia-text-primary mb-1">
                        💎 Expandir para Regiões
                      </h4>
                      <p className="text-xs text-lia-text-secondary">
                        Oportunidade de crescimento em Sul e Nordeste com trabalho remoto
                      </p>
                    </div>

                    <div className="p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md">
                      <h4 className="text-sm font-medium text-lia-text-primary mb-1">
                        📈 Ajustar Estratégia Salarial
                      </h4>
                      <p className="text-xs text-lia-text-secondary">
                        Modelo híbrido justifica salários 8% maiores pela produtividade
                      </p>
                    </div>

                    <div className="p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md">
                      <h4 className="text-sm font-medium text-lia-text-primary mb-1">
                        🔄 Revisar Políticas Presenciais
                      </h4>
                      <p className="text-xs text-lia-text-secondary">
                        Apenas 16.9% preferem presencial - considerar flexibilização
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
