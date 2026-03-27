"use client"

import { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  TrendingUp, TrendingDown, Minus, RefreshCw, Users, Briefcase,
  Clock, DollarSign, Target, Award, ThumbsUp, UserCheck,
  Download, FileSpreadsheet, FileText, Calendar, ChevronDown,
  BarChart3, Activity
} from "lucide-react"

interface StrategicIndicator {
  id: string
  name: string
  value: number
  unit: string
  target?: number
  previous_value?: number
  trend: 'up' | 'down' | 'stable'
  trend_percentage: number
  category: string
  description?: string
}

interface FunnelStage {
  stage_name: string
  stage_order: number
  count: number
  conversion_rate: number
  drop_off_rate: number
  avg_time_in_stage_days: number
}

interface RecruiterPerformance {
  recruiter_id: string
  recruiter_name: string
  avatar_url?: string
  positions_filled: number
  positions_target: number
  candidates_screened: number
  interviews_conducted: number
  conversion_rate: number
  avg_time_to_fill_days: number
  quality_score: number
  rank: number
}

interface DateRange {
  start_date: string
  end_date: string
}

interface StrategicDashboardProps {
  dateRange?: DateRange
  onExportPDF?: () => void
  onExportExcel?: () => void
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export function StrategicDashboard({ dateRange, onExportPDF, onExportExcel }: StrategicDashboardProps) {
  const [indicators, setIndicators] = useState<StrategicIndicator[]>([])
  const [funnelStages, setFunnelStages] = useState<FunnelStage[]>([])
  const [recruiters, setRecruiters] = useState<RecruiterPerformance[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    
    const queryParams = dateRange 
      ? `?start_date=${dateRange.start_date}&end_date=${dateRange.end_date}` 
      : ''
    
    try {
      const [indicatorsRes, funnelRes, recruitersRes] = await Promise.all([
        fetch(`${BACKEND_URL}/api/v1/dashboard/strategic-indicators${queryParams}`),
        fetch(`${BACKEND_URL}/api/v1/dashboard/funnel-performance${queryParams}`),
        fetch(`${BACKEND_URL}/api/v1/dashboard/recruiter-ranking${queryParams}`)
      ])

      if (indicatorsRes.ok) {
        const data = await indicatorsRes.json()
        setIndicators(data.indicators || [])
      }

      if (funnelRes.ok) {
        const data = await funnelRes.json()
        setFunnelStages(data.stages || [])
      }

      if (recruitersRes.ok) {
        const data = await recruitersRes.json()
        setRecruiters(data.recruiters || [])
      }
    } catch (err) {
      console.error("Error fetching dashboard data:", err)
      setError("Erro ao carregar dados do dashboard")
    } finally {
      setLoading(false)
    }
  }, [dateRange])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <TrendingUp className="w-4 h-4 text-status-success" />
      case 'down': return <TrendingDown className="w-4 h-4 text-status-error" />
      default: return <Minus className="w-4 h-4 text-gray-400" />
    }
  }

  const getTrendColor = (trend: string, value: number, isPositive: boolean = true) => {
    if (trend === 'stable') return 'text-gray-500'
    const positive = isPositive ? trend === 'up' : trend === 'down'
    return positive ? 'text-status-success' : 'text-status-error'
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'recruitment': return <Briefcase className="w-5 h-5" />
      case 'pipeline': return <Users className="w-5 h-5" />
      case 'efficiency': return <Clock className="w-5 h-5" />
      case 'financial': return <DollarSign className="w-5 h-5" />
      case 'satisfaction': return <ThumbsUp className="w-5 h-5" />
      case 'dei': return <UserCheck className="w-5 h-5" />
      default: return <Target className="w-5 h-5" />
    }
  }

  const formatValue = (value: number, unit: string) => {
    if (unit === 'R$') return `R$ ${value.toLocaleString('pt-BR')}`
    if (unit === '%') return `${value}%`
    if (unit === '/5') return `${value}/5`
    if (unit === ':1') return `${value}:1`
    return `${value} ${unit}`
  }

  const handleExportPDF = () => {
    if (onExportPDF) {
      onExportPDF()
      return
    }
    
    const printContent = document.getElementById('strategic-dashboard-content')
    if (printContent) {
      const printWindow = window.open('', '_blank')
      if (printWindow) {
        printWindow.document.write(`
          <html>
            <head>
              <title>Dashboard Estratégico - WeDo Talent</title>
              <style>
                body { font-family: 'Open Sans', sans-serif; padding: 20px; }
                h1 { color: #374151; }
                table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #111827; color: white; }
                .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
                .kpi-card { border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; }
              </style>
            </head>
            <body>
              <h1>Dashboard Estratégico</h1>
              <p>Gerado em: ${new Date().toLocaleString('pt-BR')}</p>
              ${printContent.innerHTML}
            </body>
          </html>
        `)
        printWindow.document.close()
        printWindow.print()
      }
    }
  }

  const handleExportExcel = () => {
    if (onExportExcel) {
      onExportExcel()
      return
    }
    
    let csvContent = "data:text/csv;charset=utf-8,"
    
    csvContent += "INDICADORES ESTRATÉGICOS\n"
    csvContent += "Nome,Valor,Unidade,Meta,Tendência,Variação %\n"
    indicators.forEach(ind => {
      csvContent += `"${ind.name}",${ind.value},"${ind.unit}",${ind.target || ''},${ind.trend},${ind.trend_percentage}\n`
    })
    
    csvContent += "\n\nFUNIL DE RECRUTAMENTO\n"
    csvContent += "Etapa,Candidatos,Taxa Conversão %,Taxa Drop-off %,Tempo Médio (dias)\n"
    funnelStages.forEach(stage => {
      csvContent += `"${stage.stage_name}",${stage.count},${stage.conversion_rate},${stage.drop_off_rate},${stage.avg_time_in_stage_days}\n`
    })
    
    csvContent += "\n\nRANKING RECRUTADORES\n"
    csvContent += "Rank,Nome,Posições Preenchidas,Meta,Taxa Conversão %,Tempo Médio (dias),Score Qualidade\n"
    recruiters.forEach(rec => {
      csvContent += `${rec.rank},"${rec.recruiter_name}",${rec.positions_filled},${rec.positions_target},${rec.conversion_rate},${rec.avg_time_to_fill_days},${rec.quality_score}\n`
    })
    
    const encodedUri = encodeURI(csvContent)
    const link = document.createElement("a")
    link.setAttribute("href", encodedUri)
    link.setAttribute("download", `dashboard-estrategico-${new Date().toISOString().split('T')[0]}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const primaryIndicators = indicators.filter(ind => 
    ['open_positions', 'active_candidates', 'monthly_hires', 'avg_time_to_hire'].includes(ind.id)
  )

  const secondaryIndicators = indicators.filter(ind => 
    !['open_positions', 'active_candidates', 'monthly_hires', 'avg_time_to_hire'].includes(ind.id)
  )

  const maxFunnelCount = Math.max(...funnelStages.map(s => s.count), 1)

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-28 bg-gray-200 rounded-md" />
          ))}
        </div>
        <div className="h-64 bg-gray-200 rounded-md" />
        <div className="h-48 bg-gray-200 rounded-md" />
      </div>
    )
  }

  if (error) {
    return (
      <Card className="">
        <CardContent className="p-8 text-center">
          <p className="text-status-error mb-4">{error}</p>
          <Button onClick={fetchData} variant="outline" className="gap-2">
            <RefreshCw className="w-4 h-4" />
            Tentar Novamente
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <div id="strategic-dashboard-content" className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          <h2 className="text-xs font-semibold text-gray-950 dark:text-gray-50 font-['Open_Sans']">
            Dashboard Estratégico
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleExportPDF}
            className="gap-2 text-xs"
          >
            <FileText className="w-4 h-4" />
            Exportar PDF
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleExportExcel}
            className="gap-2 text-xs"
          >
            <FileSpreadsheet className="w-4 h-4" />
            Exportar Excel
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={fetchData}
            className="gap-2 text-xs"
          >
            <RefreshCw className="w-4 h-4" />
            Atualizar
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {primaryIndicators.map((indicator, index) => (
          <Card 
            key={indicator.id} 
            className="hover:transition-shadow"
            style={{ animationDelay: `${index * 100}ms` }}
          >
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-xs font-medium text-gray-500 font-['Open_Sans']">
                    {indicator.name}
                  </p>
                  <p className="text-2xl font-bold text-gray-950 dark:text-gray-50 mt-1 font-['Open_Sans'] animate-[fadeIn_0.5s_ease-out]">
                    {formatValue(indicator.value, indicator.unit)}
                  </p>
                  <div className="flex items-center gap-1 mt-1">
                    {getTrendIcon(indicator.trend)}
                    <span className={`text-xs font-['Open_Sans'] ${getTrendColor(indicator.trend, indicator.trend_percentage, indicator.id !== 'avg_time_to_hire')}`}>
                      {indicator.trend_percentage > 0 ? '+' : ''}{indicator.trend_percentage}%
                    </span>
                    {indicator.target && (
                      <span className="text-xs text-gray-400 ml-2">
                        Meta: {formatValue(indicator.target, indicator.unit)}
                      </span>
                    )}
                  </div>
                </div>
                <div className="w-10 h-10 rounded-md bg-gray-100 dark:bg-gray-800 flex items-center justify-center text-gray-600 dark:text-gray-400">
                  {getCategoryIcon(indicator.category)}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
        {secondaryIndicators.map((indicator) => (
          <Card key={indicator.id} className="">
            <CardContent className="p-3">
              <p className="text-xs text-gray-500 font-['Open_Sans'] truncate" title={indicator.name}>
                {indicator.name}
              </p>
              <p className="text-lg font-bold text-gray-950 dark:text-gray-50 font-['Open_Sans']">
                {formatValue(indicator.value, indicator.unit)}
              </p>
              <div className="flex items-center gap-1">
                {getTrendIcon(indicator.trend)}
                <span className={`text-xs font-['Open_Sans'] ${getTrendColor(indicator.trend, indicator.trend_percentage)}`}>
                  {indicator.trend_percentage > 0 ? '+' : ''}{indicator.trend_percentage}%
                </span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-semibold font-['Open_Sans'] flex items-center gap-2">
            <Activity className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            Funil de Recrutamento
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {funnelStages.map((stage, index) => {
              const widthPercent = (stage.count / maxFunnelCount) * 100
              const colors = [
                'bg-gray-900 dark:bg-gray-50',
                'bg-gray-700 dark:bg-gray-300',
                'bg-gray-200 dark:bg-gray-700',
                'bg-gray-200 dark:bg-gray-700',
                'bg-status-success'
              ]
              
              return (
                <div key={stage.stage_name} className="relative">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium text-gray-800 dark:text-gray-200 font-['Open_Sans']">
                      {stage.stage_name}
                    </span>
                    <div className="flex items-center gap-4 text-xs text-gray-500 font-['Open_Sans']">
                      <span>{stage.count} candidatos</span>
                      <span>Conv: {stage.conversion_rate.toFixed(1)}%</span>
                      <span>{stage.avg_time_in_stage_days}d média</span>
                    </div>
                  </div>
                  <div className="h-8 bg-gray-100 rounded-md overflow-hidden">
                    <div 
                      className={`h-full ${colors[index] || 'bg-gray-400'} rounded-md transition-all duration-700 ease-out flex items-center justify-end pr-2`}
                      style={{ 
                        width: `${widthPercent}%`,
                        animation: `slideIn 0.5s ease-out ${index * 100}ms backwards`
                      }}
                    >
                      <span className="text-xs font-bold text-white font-['Open_Sans']">
                        {stage.count}
                      </span>
                    </div>
                  </div>
                  {stage.drop_off_rate > 0 && index > 0 && (
                    <div className="absolute -top-1 right-0">
                      <Badge variant="outline" className="text-xs bg-status-error/10 text-status-error border-status-error/30">
                        -{stage.drop_off_rate.toFixed(0)}%
                      </Badge>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      <Card className="">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-semibold font-['Open_Sans'] flex items-center gap-2">
            <Award className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            Ranking de Recrutadores
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-xs font-['Open_Sans']">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 px-2 text-gray-500 font-medium">Rank</th>
                  <th className="text-left py-2 px-2 text-gray-500 font-medium">Recrutador</th>
                  <th className="text-center py-2 px-2 text-gray-500 font-medium">Posições</th>
                  <th className="text-center py-2 px-2 text-gray-500 font-medium">Triagens</th>
                  <th className="text-center py-2 px-2 text-gray-500 font-medium">Entrevistas</th>
                  <th className="text-center py-2 px-2 text-gray-500 font-medium">Conversão</th>
                  <th className="text-center py-2 px-2 text-gray-500 font-medium">Tempo Médio</th>
                  <th className="text-center py-2 px-2 text-gray-500 font-medium">Qualidade</th>
                </tr>
              </thead>
              <tbody>
                {recruiters.map((recruiter) => {
                  const goalProgress = (recruiter.positions_filled / recruiter.positions_target) * 100
                  const isOnTarget = goalProgress >= 100
                  
                  return (
                    <tr 
                      key={recruiter.recruiter_id} 
                      className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                    >
                      <td className="py-3 px-2">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                          recruiter.rank === 1 ? 'bg-status-warning/10 text-status-warning' :
                          recruiter.rank === 2 ? 'bg-gray-300 text-gray-800 dark:bg-gray-600 dark:text-gray-200' :
                          recruiter.rank === 3 ? 'bg-wedo-orange/10 text-wedo-orange' :
                          'bg-gray-100 text-gray-600'
                        }`}>
                          {recruiter.rank}
                        </div>
                      </td>
                      <td className="py-3 px-2">
                        <div className="flex items-center gap-2">
                          <Avatar className="w-8 h-8">
                            <AvatarImage src={recruiter.avatar_url} alt={recruiter.recruiter_name} />
                            <AvatarFallback className="text-xs bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
                              {recruiter.recruiter_name.split(' ').map(n => n[0]).join('')}
                            </AvatarFallback>
                          </Avatar>
                          <span className="font-medium text-gray-950 dark:text-gray-50">{recruiter.recruiter_name}</span>
                        </div>
                      </td>
                      <td className="py-3 px-2 text-center">
                        <div className="flex items-center justify-center gap-1">
                          <span className={isOnTarget ? 'text-status-success font-bold' : 'text-gray-950 dark:text-gray-50'}>
                            {recruiter.positions_filled}
                          </span>
                          <span className="text-gray-400">/</span>
                          <span className="text-gray-500">{recruiter.positions_target}</span>
                          {isOnTarget && (
                            <Badge className="ml-1 bg-status-success/15 text-status-success text-xs">
                              ✓
                            </Badge>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-2 text-center text-gray-800 dark:text-gray-200">
                        {recruiter.candidates_screened}
                      </td>
                      <td className="py-3 px-2 text-center text-gray-800 dark:text-gray-200">
                        {recruiter.interviews_conducted}
                      </td>
                      <td className="py-3 px-2 text-center">
                        <span className={`font-medium ${
                          recruiter.conversion_rate >= 3 ? 'text-status-success' : 
                          recruiter.conversion_rate >= 2 ? 'text-gray-600 dark:text-gray-400' : 
                          'text-wedo-orange'
                        }`}>
                          {recruiter.conversion_rate.toFixed(1)}%
                        </span>
                      </td>
                      <td className="py-3 px-2 text-center">
                        <span className={`${
                          recruiter.avg_time_to_fill_days <= 25 ? 'text-status-success' : 
                          recruiter.avg_time_to_fill_days <= 30 ? 'text-gray-600 dark:text-gray-400' : 
                          'text-wedo-orange'
                        }`}>
                          {recruiter.avg_time_to_fill_days}d
                        </span>
                      </td>
                      <td className="py-3 px-2 text-center">
                        <div className="flex items-center justify-center gap-1">
                          <div className="w-12 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-gray-900 dark:bg-gray-50 rounded-full transition-all duration-500"
                              style={{ width: `${recruiter.quality_score}%` }}
                            />
                          </div>
                          <span className="text-gray-800 dark:text-gray-200 font-medium">{recruiter.quality_score.toFixed(0)}</span>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes slideIn {
          from { width: 0; }
        }
      `}</style>
    </div>
  )
}
