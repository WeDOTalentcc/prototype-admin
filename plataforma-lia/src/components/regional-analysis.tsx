"use client"

import { useState, useMemo } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  MapPin, TrendingUp, Users, Building, Home, Globe,
  ChevronDown, ChevronUp, Filter, BarChart3, Target,
  DollarSign, Clock, ArrowUp, ArrowDown
} from "lucide-react"

interface RegionData {
  regiao: string
  estado: string
  cidade?: string
  remoto: number
  hibrido: number
  presencial: number
  total: number
  salarioMedio: number
  crescimento: number
  densidade: 'baixa' | 'media' | 'alta'
  principaisEmpresas: string[]
  cargosPopulares: string[]
}

interface RegionSummary {
  regiao: string
  estados: RegionData[]
  totalCandidatos: number
  remoto: number
  hibrido: number
  presencial: number
  salarioMedio: number
  crescimentoMedio: number
}

interface RegionalAnalysisProps {
  className?: string
}

export function RegionalAnalysis({ className }: RegionalAnalysisProps) {
  const [selectedRegion, setSelectedRegion] = useState<string>('all')
  const [sortBy, setSortBy] = useState<'total' | 'salario' | 'crescimento'>('total')
  const [viewMode, setViewMode] = useState<'regioes' | 'estados' | 'cidades'>('estados')
  const [expandedRegions, setExpandedRegions] = useState<Set<string>>(new Set())

  // Mock data com dados mais detalhados
  const regionData: RegionData[] = [
    {
      regiao: 'Sudeste',
      estado: 'SP',
      cidade: 'São Paulo',
      remoto: 156,
      hibrido: 234,
      presencial: 89,
      total: 479,
      salarioMedio: 9200,
      crescimento: 12.5,
      densidade: 'alta',
      principaisEmpresas: ['Nubank', 'iFood', 'Stone', 'Mercado Livre'],
      cargosPopulares: ['Full Stack', 'Frontend', 'Product Manager']
    },
    {
      regiao: 'Sudeste',
      estado: 'RJ',
      cidade: 'Rio de Janeiro',
      remoto: 89,
      hibrido: 112,
      presencial: 34,
      total: 235,
      salarioMedio: 8500,
      crescimento: 8.3,
      densidade: 'alta',
      principaisEmpresas: ['Globo', 'Vale', 'Petrobras', 'IR'],
      cargosPopulares: ['Backend', 'DevOps', 'Data Scientist']
    },
    {
      regiao: 'Sudeste',
      estado: 'MG',
      cidade: 'Belo Horizonte',
      remoto: 34,
      hibrido: 45,
      presencial: 18,
      total: 97,
      salarioMedio: 7200,
      crescimento: 15.2,
      densidade: 'media',
      principaisEmpresas: ['Localiza', 'Soluções Usiminas', 'Take'],
      cargosPopulares: ['Backend', 'Frontend', 'QA']
    },
    {
      regiao: 'Sul',
      estado: 'RS',
      cidade: 'Porto Alegre',
      remoto: 28,
      hibrido: 41,
      presencial: 12,
      total: 81,
      salarioMedio: 7800,
      crescimento: 18.7,
      densidade: 'media',
      principaisEmpresas: ['Banrisul', 'CWI', 'DBServer', 'ADP'],
      cargosPopulares: ['Full Stack', 'Mobile', 'UX Designer']
    },
    {
      regiao: 'Sul',
      estado: 'SC',
      cidade: 'Florianópolis',
      remoto: 19,
      hibrido: 28,
      presencial: 8,
      total: 55,
      salarioMedio: 7500,
      crescimento: 22.1,
      densidade: 'media',
      principaisEmpresas: ['Softplan', 'Nelogica', 'Involves', 'TOTVS'],
      cargosPopulares: ['Frontend', 'Mobile', 'Product Manager']
    },
    {
      regiao: 'Sul',
      estado: 'PR',
      cidade: 'Curitiba',
      remoto: 15,
      hibrido: 22,
      presencial: 6,
      total: 43,
      salarioMedio: 7300,
      crescimento: 16.8,
      densidade: 'baixa',
      principaisEmpresas: ['Ebanx', 'Madeira Madeira', 'Linx', 'Volvo'],
      cargosPopulares: ['Backend', 'DevOps', 'QA']
    },
    {
      regiao: 'Nordeste',
      estado: 'PE',
      cidade: 'Recife',
      remoto: 12,
      hibrido: 18,
      presencial: 9,
      total: 39,
      salarioMedio: 6800,
      crescimento: 25.3,
      densidade: 'baixa',
      principaisEmpresas: ['Accenture', 'In Loco', 'Porto Digital'],
      cargosPopulares: ['Backend', 'Mobile', 'Data Scientist']
    },
    {
      regiao: 'Nordeste',
      estado: 'BA',
      cidade: 'Salvador',
      remoto: 8,
      hibrido: 15,
      presencial: 7,
      total: 30,
      salarioMedio: 6500,
      crescimento: 20.5,
      densidade: 'baixa',
      principaisEmpresas: ['Tivit', 'Salvador Arena', 'Stefanini'],
      cargosPopulares: ['Frontend', 'Backend', 'QA']
    },
    {
      regiao: 'Centro-Oeste',
      estado: 'DF',
      cidade: 'Brasília',
      remoto: 18,
      hibrido: 25,
      presencial: 11,
      total: 54,
      salarioMedio: 8200,
      crescimento: 14.2,
      densidade: 'baixa',
      principaisEmpresas: ['Serpro', 'Dataprev', 'BB Tecnologia'],
      cargosPopulares: ['Backend', 'DevOps', 'Security Engineer']
    }
  ]

  // Agrupar dados por região
  const regionSummary = useMemo(() => {
    const summary: { [key: string]: RegionSummary } = {}

    regionData.forEach(item => {
      if (!summary[item.regiao]) {
        summary[item.regiao] = {
          regiao: item.regiao,
          estados: [],
          totalCandidatos: 0,
          remoto: 0,
          hibrido: 0,
          presencial: 0,
          salarioMedio: 0,
          crescimentoMedio: 0
        }
      }

      summary[item.regiao].estados.push(item)
      summary[item.regiao].totalCandidatos += item.total
      summary[item.regiao].remoto += item.remoto
      summary[item.regiao].hibrido += item.hibrido
      summary[item.regiao].presencial += item.presencial
    })

    // Calcular médias
    Object.values(summary).forEach((region) => {
      const totalSalario = region.estados.reduce((sum: number, estado: RegionData) =>
        sum + (estado.salarioMedio * estado.total), 0)
      region.salarioMedio = Math.round(totalSalario / region.totalCandidatos)

      region.crescimentoMedio = region.estados.reduce((sum: number, estado: RegionData) =>
        sum + estado.crescimento, 0) / region.estados.length
    })

    return Object.values(summary)
  }, [])

  // Função para ordenar dados
  const sortedData = useMemo(() => {
    const dataToSort = viewMode === 'regioes' ? regionSummary : regionData

    return [...dataToSort].sort((a, b) => {
      switch (sortBy) {
        case 'total':
          return (b.totalCandidatos || b.total) - (a.totalCandidatos || a.total)
        case 'salario':
          return b.salarioMedio - a.salarioMedio
        case 'crescimento':
          return (b.crescimentoMedio || b.crescimento) - (a.crescimentoMedio || a.crescimento)
        default:
          return 0
      }
    })
  }, [regionSummary, regionData, sortBy, viewMode])

  const toggleRegionExpansion = (regionId: string) => {
    setExpandedRegions(prev => {
      const newSet = new Set(prev)
      if (newSet.has(regionId)) {
        newSet.delete(regionId)
      } else {
        newSet.add(regionId)
      }
      return newSet
    })
  }

  const getDensityColor = (densidade: string) => {
    switch (densidade) {
      case 'alta': return 'bg-status-error/15 text-status-error border-status-error/30'
      case 'media': return 'bg-status-warning/15 text-status-warning border-status-warning/30'
      case 'baixa': return 'bg-status-success/15 text-status-success border-status-success/30'
      default: return 'bg-gray-100 lia-text-strong border-lia-border-subtle'
    }
  }

  const getWorkModelPercentage = (remoto: number, hibrido: number, presencial: number) => {
    const total = remoto + hibrido + presencial
    return {
      remoto: (remoto / total) * 100,
      hibrido: (hibrido / total) * 100,
      presencial: (presencial / total) * 100
    }
  }

  return (
    <div className={className}>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <MapPin className="w-5 h-5 text-wedo-orange" />
              Análise Regional Detalhada
            </CardTitle>

            <div className="flex items-center gap-3">
              {/* Seletor de visualização */}
              <div className="flex bg-gray-100 dark:bg-lia-bg-secondary rounded-md p-1">
                {(['regioes', 'estados'] as const).map((mode) => (
                  <button
                    key={mode}
                    onClick={() => setViewMode(mode)}
                    className={`px-3 py-1 text-xs rounded-md transition-colors motion-reduce:transition-none ${
 viewMode === mode
                        ? 'bg-wedo-orange/10 text-white'
                        : 'lia-text-base hover:lia-text-strong'
                    }`}
                  >
                    {mode === 'regioes' ? 'Por Região' : 'Por Estado'}
                  </button>
                ))}
              </div>

              {/* Seletor de ordenação */}
              <div className="flex bg-gray-100 dark:bg-lia-bg-secondary rounded-md p-1">
                {(['total', 'salario', 'crescimento'] as const).map((sort) => (
                  <button
                    key={sort}
                    onClick={() => setSortBy(sort)}
                    className={`px-3 py-1 text-xs rounded-md transition-colors motion-reduce:transition-none ${
 sortBy === sort
                        ? 'bg-gray-900 text-white'
                        : 'lia-text-base hover:lia-text-strong'
                    }`}
                  >
                    {sort === 'total' ? 'Total' :
                     sort === 'salario' ? 'Salário' : 'Crescimento'}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          <div className="space-y-4">
            {sortedData.map((item, index) => {
              const isRegion = 'estados' in item
              const isExpanded = expandedRegions.has(item.regiao || item.estado)
              const percentages = getWorkModelPercentage(
                item.remoto,
                item.hibrido,
                item.presencial
              )

              return (
                <div key={item.regiao || index} className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md overflow-hidden">

                  {/* Header da região/estado */}
                  <div
                    className="p-4 bg-gray-50 dark:bg-lia-bg-secondary cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors motion-reduce:transition-none"
                    onClick={() => isRegion && toggleRegionExpansion(item.regiao)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {isRegion && (
                          <button className="lia-text-base hover:lia-text-strong">
                            {isExpanded ?
                              <ChevronUp className="w-4 h-4" /> :
                              <ChevronDown className="w-4 h-4" />
                            }
                          </button>
                        )}

                        <div>
                          <h3 className="font-medium text-lia-text-primary">
                            {isRegion ? item.regiao : `${item.estado} - ${item.cidade}`}
                          </h3>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge variant="outline" className="text-xs">
                              {isRegion ? item.totalCandidatos : item.total} candidatos
                            </Badge>
                            {!isRegion && (
                              <Badge variant="outline" className={getDensityColor(item.densidade)}>
                                {item.densidade} densidade
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-6 text-sm">
                        <div className="text-center">
                          <div className="text-lg font-bold text-lia-text-primary">
                            R$ {item.salarioMedio.toLocaleString()}
                          </div>
                          <div className="text-xs text-lia-text-primary dark:text-lia-text-primary">Salário médio</div>
                        </div>

                        <div className="text-center">
                          <div className={`text-lg font-bold flex items-center gap-1 ${
 (item.crescimentoMedio || item.crescimento) > 0 ? 'text-status-success' : 'text-status-error'
                          }`}>
                            {(item.crescimentoMedio || item.crescimento) > 0 ?
                              <ArrowUp className="w-4 h-4" /> :
                              <ArrowDown className="w-4 h-4" />
                            }
                            {Math.abs(item.crescimentoMedio || item.crescimento).toFixed(1)}%
                          </div>
                          <div className="text-xs text-lia-text-primary dark:text-lia-text-primary">Crescimento</div>
                        </div>
                      </div>
                    </div>

                    {/* Barra de distribuição de modelos de trabalho */}
                    <div className="mt-4">
                      <div className="flex rounded-full overflow-hidden h-3 bg-gray-200 dark:bg-lia-bg-elevated">
                        <div
                          // @ts-ignore TODO: fix type
                          className="bg-status-success"
                          style={{width: `${percentages.remoto}%`}}
                          title={`Remoto: ${item.remoto} (${percentages.remoto.toFixed(1)}%)`}
                        />
                        <div
                          className="bg-gray-700"
                          style={{width: `${percentages.hibrido}%`}}
                          title={`Híbrido: ${item.hibrido} (${percentages.hibrido.toFixed(1)}%)`}
                        />
                        <div
                          // @ts-ignore TODO: fix type
                          className="bg-gray-500"
                          style={{width: `${percentages.presencial}%`}}
                          title={`Presencial: ${item.presencial} (${percentages.presencial.toFixed(1)}%)`}
                        />
                      </div>

                      <div className="flex items-center justify-between mt-2 text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                        <div className="flex items-center gap-4">
                          <div className="flex items-center gap-1">
                            <Home className="w-3 h-3 text-status-success" />
                            <span>Remoto: {item.remoto}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Globe className="w-3 h-3 text-lia-text-secondary dark:text-lia-text-tertiary" />
                            <span>Híbrido: {item.hibrido}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Building className="w-3 h-3 lia-text-base" />
                            <span>Presencial: {item.presencial}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Detalhes expandidos para regiões */}
                  {isRegion && isExpanded && (
                    <div className="p-4 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {item.estados.map((estado: RegionData, estadoIndex: number) => (
                          <div key={estadoIndex} className="p-3 bg-white dark:bg-lia-bg-primary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle">
                            <div className="flex items-center justify-between mb-2">
                              <h4 className="font-medium text-lia-text-primary">
                                {estado.estado} - {estado.cidade}
                              </h4>
                              <Badge variant="outline" className="text-xs">
                                {estado.total}
                              </Badge>
                            </div>

                            <div className="space-y-2">
                              <div className="flex rounded-full overflow-hidden h-2 bg-gray-200 dark:bg-lia-bg-elevated">
                                <div
                                  className="bg-status-success"
                                  style={{width: `${(estado.remoto / estado.total) * 100}%`}}
                                />
                                <div
                                  className="bg-gray-700"
                                  style={{width: `${(estado.hibrido / estado.total) * 100}%`}}
                                />
                                <div
                                  className="bg-gray-500"
                                  style={{width: `${(estado.presencial / estado.total) * 100}%`}}
                                />
                              </div>

                              <div className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                                <div>R$ {estado.salarioMedio.toLocaleString()} salário médio</div>
                                <div className={estado.crescimento > 0 ? 'text-status-success' : 'text-status-error'}>
                                  {estado.crescimento > 0 ? '+' : ''}{estado.crescimento}% crescimento
                                </div>
                              </div>

                              {/* Principais empresas */}
                              <div>
                                <div className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary mb-1">
                                  Principais Empresas:
                                </div>
                                <div className="flex flex-wrap gap-1">
                                  {estado.principaisEmpresas.slice(0, 3).map((empresa: string) => (
                                    <Badge key={empresa} variant="outline" className="text-xs">
                                      {empresa}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Detalhes para estados individuais */}
                  {!isRegion && (
                    <div className="p-4 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                        {/* Principais empresas */}
                        <div>
                          <h4 className="text-sm font-medium text-lia-text-primary mb-2">
                            Principais Empresas
                          </h4>
                          <div className="space-y-2">
                            {item.principaisEmpresas.map((empresa: string) => (
                              <div key={empresa} className="flex items-center gap-2">
                                <Building className="w-3 h-3 lia-text-base" />
                                <span className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">{empresa}</span>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Cargos populares */}
                        <div>
                          <h4 className="text-sm font-medium text-lia-text-primary mb-2">
                            Cargos Mais Populares
                          </h4>
                          <div className="flex flex-wrap gap-2">
                            {item.cargosPopulares.map((cargo: string) => (
                              <Badge key={cargo} variant="outline" className="text-xs">
                                {cargo}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
