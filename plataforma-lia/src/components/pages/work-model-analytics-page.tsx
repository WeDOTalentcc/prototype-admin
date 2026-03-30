"use client"

import { useState, useEffect, useMemo } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  BarChart3, PieChart, MapPin, Users, TrendingUp, Download,
  Filter, Calendar, Building, Target, ArrowUp, ArrowDown,
  RotateCcw, Zap, Clock, Globe, Home, Briefcase
} from "lucide-react"

// Interfaces para tipos de dados
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

export function WorkModelAnalyticsPage() {
  // Estados para filtros
  const [selectedPeriod, setSelectedPeriod] = useState<'30d' | '90d' | '6m' | '1y'>('90d')
  const [selectedRegion, setSelectedRegion] = useState<string>('all')
  const [selectedCargo, setSelectedCargo] = useState<string>('all')
  const [selectedSeniority, setSelectedSeniority] = useState<string>('all')

  // Mock data - distribuição geral de modelos de trabalho
  const workModelDistribution: WorkModelData[] = [
    {
      modelo: 'remoto',
      candidatos: 342,
      percentual: 34.2,
      crescimento: 12.5,
      salarioMedio: 8500
    },
    {
      modelo: 'híbrido',
      candidatos: 489,
      percentual: 48.9,
      crescimento: 8.3,
      salarioMedio: 9200
    },
    {
      modelo: 'presencial',
      candidatos: 169,
      percentual: 16.9,
      crescimento: -5.2,
      salarioMedio: 7800
    }
  ]

  // Mock data - distribuição por cargo
  const cargoWorkModels: CargoWorkModel[] = [
    { cargo: 'Desenvolvedor Frontend', remoto: 45, hibrido: 32, presencial: 8, total: 85 },
    { cargo: 'Desenvolvedor Backend', remoto: 38, hibrido: 28, presencial: 12, total: 78 },
    { cargo: 'Full Stack Developer', remoto: 52, hibrido: 41, presencial: 15, total: 108 },
    { cargo: 'UX Designer', remoto: 28, hibrido: 35, presencial: 18, total: 81 },
    { cargo: 'Product Manager', remoto: 22, hibrido: 31, presencial: 9, total: 62 },
    { cargo: 'Data Scientist', remoto: 34, hibrido: 25, presencial: 6, total: 65 },
    { cargo: 'DevOps Engineer', remoto: 41, hibrido: 22, presencial: 8, total: 71 },
    { cargo: 'QA Engineer', remoto: 19, hibrido: 28, presencial: 15, total: 62 },
    { cargo: 'Tech Lead', remoto: 18, hibrido: 24, presencial: 12, total: 54 },
    { cargo: 'Mobile Developer', remoto: 31, hibrido: 19, presencial: 11, total: 61 }
  ]

  // Mock data - distribuição regional
  const regionalData: RegionalData[] = [
    { regiao: 'Sudeste', estado: 'SP', remoto: 156, hibrido: 234, presencial: 89, total: 479 },
    { regiao: 'Sudeste', estado: 'RJ', remoto: 89, hibrido: 112, presencial: 34, total: 235 },
    { regiao: 'Sudeste', estado: 'MG', remoto: 34, hibrido: 45, presencial: 18, total: 97 },
    { regiao: 'Sul', estado: 'RS', remoto: 28, hibrido: 41, presencial: 12, total: 81 },
    { regiao: 'Sul', estado: 'SC', remoto: 19, hibrido: 28, presencial: 8, total: 55 },
    { regiao: 'Sul', estado: 'PR', remoto: 15, hibrido: 22, presencial: 6, total: 43 },
    { regiao: 'Nordeste', estado: 'PE', remoto: 12, hibrido: 18, presencial: 9, total: 39 },
    { regiao: 'Nordeste', estado: 'BA', remoto: 8, hibrido: 15, presencial: 7, total: 30 },
    { regiao: 'Centro-Oeste', estado: 'DF', remoto: 18, hibrido: 25, presencial: 11, total: 54 }
  ]

  // Mock data - distribuição por senioridade
  const seniorityData: SeniorityData[] = [
    { nivel: 'Estagiário', experiencia: '0-1 anos', remoto: 12, hibrido: 28, presencial: 15, total: 55, salarioMedio: 2800 },
    { nivel: 'Júnior', experiencia: '1-3 anos', remoto: 78, hibrido: 95, presencial: 42, total: 215, salarioMedio: 4500 },
    { nivel: 'Pleno', experiencia: '3-6 anos', remoto: 134, hibrido: 189, presencial: 67, total: 390, salarioMedio: 7200 },
    { nivel: 'Sênior', experiencia: '6-10 anos', remoto: 98, hibrido: 142, presencial: 38, total: 278, salarioMedio: 11500 },
    { nivel: 'Especialista', experiencia: '10-15 anos', remoto: 18, hibrido: 31, presencial: 6, total: 55, salarioMedio: 16800 },
    { nivel: 'Líder Técnico', experiencia: '15+ anos', remoto: 2, hibrido: 4, presencial: 1, total: 7, salarioMedio: 22000 }
  ]

  // Cálculos derivados
  const totalCandidatos = workModelDistribution.reduce((sum, item) => sum + item.candidatos, 0)
  const salarioMedioGeral = workModelDistribution.reduce((sum, item) => sum + (item.salarioMedio * item.candidatos), 0) / totalCandidatos

  // Função para gerar cores das barras
  const getWorkModelColor = (modelo: string) => {
    switch (modelo) {
      case 'remoto': return 'bg-status-success'
      case 'híbrido': return 'bg-gray-700 dark:bg-gray-300'
      case 'presencial': return 'bg-gray-500'
      default: return 'bg-gray-400'
    }
  }

  // Função para exportar dados
  const handleExport = (format: 'csv' | 'pdf' | 'excel') => {
    // TODO: Implementar exportação real
    alert(`📊 Relatório de Modelos de Trabalho exportado em ${format.toUpperCase()}!`)
  }

  return (
    <div className="h-screen bg-gray-50 dark:bg-lia-bg-primary overflow-hidden">
      <div className="flex flex-col h-full">

        {/* Header */}
        <div className="p-6 bg-white dark:bg-lia-bg-primary border-b border-lia-border-subtle dark:border-lia-border-subtle">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-lia-text-primary dark:text-lia-text-primary mb-2 flex items-center gap-3">
                <BarChart3 className="w-6 h-6 text-lia-text-secondary dark:text-lia-text-tertiary" />
                Analytics: Modelos de Trabalho
              </h1>
              <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                Análise completa da distribuição e preferências de modelos de trabalho
              </p>
            </div>

            <div className="flex items-center gap-3">
              {/* Filtros de período */}
              <div className="flex bg-gray-100 dark:bg-lia-bg-secondary rounded-md p-1">
                {(['30d', '90d', '6m', '1y'] as const).map((period) => (
                  <button
                    key={period}
                    onClick={() => setSelectedPeriod(period)}
                    className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                      selectedPeriod === period
                        ? 'bg-gray-900 dark:bg-gray-50 text-white dark:text-lia-text-disabled'
                        : 'text-lia-text-secondary dark:text-lia-text-tertiary hover:text-lia-text-primary dark:hover:text-lia-text-inverse'
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
                <Card key={item.modelo} className="border-l-4 border-l-gray-400 dark:border-l-gray-500">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-sm font-medium text-lia-text-secondary dark:text-lia-text-tertiary capitalize flex items-center gap-2">
                        {item.modelo === 'remoto' && <Home className="w-4 h-4 text-status-success" />}
                        {item.modelo === 'híbrido' && <Globe className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />}
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
                      <div className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">
                        {item.candidatos}
                      </div>
                      <div className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                        {item.percentual}% do total
                      </div>
                      <div className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                        R$ {item.salarioMedio.toLocaleString()} salário médio
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}

              {/* Card de total */}
              <Card className="border-l-4 border-l-purple-500">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium text-lia-text-secondary dark:text-lia-text-tertiary flex items-center gap-2">
                    <Users className="w-4 h-4 text-wedo-purple" />
                    Total Geral
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">
                      {totalCandidatos}
                    </div>
                    <div className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                      Candidatos analisados
                    </div>
                    <div className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                      R$ {Math.round(salarioMedioGeral).toLocaleString()} salário médio
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
                      <div key={index} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                            {cargo.cargo}
                          </span>
                          <span className="text-xs text-lia-text-primary dark:text-lia-text-primary">
                            {cargo.total} candidatos
                          </span>
                        </div>
                        <div className="flex rounded-full overflow-hidden h-2 bg-gray-200 dark:bg-lia-bg-elevated">
                          <div
                            className="bg-status-success"
                            style={{width: `${(cargo.remoto / cargo.total) * 100}%`}}
                            title={`Remoto: ${cargo.remoto}`}
                          />
                          <div
                            className="bg-gray-700 dark:bg-gray-300"
                            style={{width: `${(cargo.hibrido / cargo.total) * 100}%`}}
                            title={`Híbrido: ${cargo.hibrido}`}
                          />
                          <div
                            className="bg-gray-500"
                            style={{width: `${(cargo.presencial / cargo.total) * 100}%`}}
                            title={`Presencial: ${cargo.presencial}`}
                          />
                        </div>
                        <div className="flex items-center gap-4 text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                          <div className="flex items-center gap-1">
                            <div className="w-2 h-2 bg-status-success rounded-full"></div>
                            Remoto: {cargo.remoto}
                          </div>
                          <div className="flex items-center gap-1">
                            <div className="w-2 h-2 bg-gray-700 dark:bg-gray-300 rounded-full"></div>
                            Híbrido: {cargo.hibrido}
                          </div>
                          <div className="flex items-center gap-1">
                            <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
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
                      <div key={index} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <div>
                            <span className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                              {level.nivel}
                            </span>
                            <span className="text-xs text-lia-text-primary dark:text-lia-text-primary ml-2">
                              ({level.experiencia})
                            </span>
                          </div>
                          <div className="text-right">
                            <div className="text-xs text-lia-text-primary dark:text-lia-text-primary">
                              {level.total} candidatos
                            </div>
                            <div className="text-xs font-medium text-status-success">
                              R$ {level.salarioMedio.toLocaleString()}
                            </div>
                          </div>
                        </div>
                        <div className="flex rounded-full overflow-hidden h-3 bg-gray-200 dark:bg-lia-bg-elevated">
                          <div
                            className="bg-status-success"
                            style={{width: `${(level.remoto / level.total) * 100}%`}}
                            title={`Remoto: ${level.remoto}`}
                          />
                          <div
                            className="bg-gray-700 dark:bg-gray-300"
                            style={{width: `${(level.hibrido / level.total) * 100}%`}}
                            title={`Híbrido: ${level.hibrido}`}
                          />
                          <div
                            className="bg-gray-500"
                            style={{width: `${(level.presencial / level.total) * 100}%`}}
                            title={`Presencial: ${level.presencial}`}
                          />
                        </div>
                        <div className="flex items-center gap-4 text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                          <div className="flex items-center gap-1">
                            <div className="w-2 h-2 bg-status-success rounded-full"></div>
                            {level.remoto} ({Math.round((level.remoto / level.total) * 100)}%)
                          </div>
                          <div className="flex items-center gap-1">
                            <div className="w-2 h-2 bg-gray-700 dark:bg-gray-300 rounded-full"></div>
                            {level.hibrido} ({Math.round((level.hibrido / level.total) * 100)}%)
                          </div>
                          <div className="flex items-center gap-1">
                            <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
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
                    <div key={index} className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium text-lia-text-primary dark:text-lia-text-primary">
                            {region.estado}
                          </h4>
                          <p className="text-xs text-lia-text-primary dark:text-lia-text-primary">{region.regiao}</p>
                        </div>
                        <Badge variant="outline" className="text-xs">
                          {region.total} candidatos
                        </Badge>
                      </div>

                      <div className="space-y-2">
                        <div className="flex rounded-full overflow-hidden h-2 bg-gray-200 dark:bg-lia-bg-elevated">
                          <div
                            className="bg-status-success"
                            style={{width: `${(region.remoto / region.total) * 100}%`}}
                          />
                          <div
                            className="bg-gray-700 dark:bg-gray-300"
                            style={{width: `${(region.hibrido / region.total) * 100}%`}}
                          />
                          <div
                            className="bg-gray-500"
                            style={{width: `${(region.presencial / region.total) * 100}%`}}
                          />
                        </div>

                        <div className="grid grid-cols-3 gap-2 text-xs">
                          <div className="text-center">
                            <div className="font-medium text-status-success">{region.remoto}</div>
                            <div className="text-lia-text-primary dark:text-lia-text-primary">Remoto</div>
                          </div>
                          <div className="text-center">
                            <div className="font-medium text-lia-text-secondary dark:text-lia-text-tertiary">{region.hibrido}</div>
                            <div className="text-lia-text-primary dark:text-lia-text-primary">Híbrido</div>
                          </div>
                          <div className="text-center">
                            <div className="font-medium text-lia-text-secondary">{region.presencial}</div>
                            <div className="text-lia-text-primary dark:text-lia-text-primary">Presencial</div>
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

                    <div className="p-3 bg-gray-100 dark:bg-lia-bg-secondary rounded-md">
                      <h4 className="text-sm font-medium text-lia-text-secondary dark:text-lia-text-secondary dark:text-lia-text-tertiary mb-1">
                        💰 Salário Remoto vs Híbrido
                      </h4>
                      <p className="text-xs text-lia-text-secondary dark:text-lia-text-secondary dark:text-lia-text-tertiary/80">
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
                    <div className="p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md">
                      <h4 className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary mb-1">
                        🎯 Focar em Modelo Híbrido
                      </h4>
                      <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                        Priorizar vagas híbridas para atrair 48.9% dos candidatos disponíveis
                      </p>
                    </div>

                    <div className="p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md">
                      <h4 className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary mb-1">
                        💎 Expandir para Regiões
                      </h4>
                      <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                        Oportunidade de crescimento em Sul e Nordeste com trabalho remoto
                      </p>
                    </div>

                    <div className="p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md">
                      <h4 className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary mb-1">
                        📈 Ajustar Estratégia Salarial
                      </h4>
                      <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                        Modelo híbrido justifica salários 8% maiores pela produtividade
                      </p>
                    </div>

                    <div className="p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md">
                      <h4 className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary mb-1">
                        🔄 Revisar Políticas Presenciais
                      </h4>
                      <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
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
