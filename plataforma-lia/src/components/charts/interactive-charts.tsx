"use client"

import { useState, useRef } from "react"
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ChartOptions,
  InteractionItem
} from 'chart.js'
import { Line, Bar, Pie, Chart } from 'react-chartjs-2'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Calendar, TrendingUp, TrendingDown, BarChart3, PieChart as PieIcon,
  Activity, Users, DollarSign, Clock, Target, AlertCircle, CheckCircle,
  ChevronDown, Filter, Download, RefreshCw
} from "lucide-react"
import { getElementAtEvent } from 'react-chartjs-2'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

// Dados mock para os gráficos
const generateTimeSeriesData = (months: number, baseTrend: 'up' | 'down' | 'stable' = 'up') => {
  const data = []
  const baseValue = 100

  for (let i = 0; i < months; i++) {
    const month = new Date(2024, i, 1).toLocaleDateString('pt-BR', { month: 'short' })
    let value = baseValue

    if (baseTrend === 'up') {
      value = baseValue + (i * 10) + Math.random() * 20
    } else if (baseTrend === 'down') {
      value = baseValue - (i * 5) + Math.random() * 15
    } else {
      value = baseValue + Math.random() * 30 - 15
    }

    data.push({
      month,
      value: Math.round(value),
      hires: Math.round(value * 0.8),
      interviews: Math.round(value * 1.5),
      applications: Math.round(value * 3),
      timeToFill: Math.round(25 + Math.random() * 15),
      nps: Math.round(80 + Math.random() * 15),
      conversion: Math.round(2 + Math.random() * 3)
    })
  }

  return data
}

// Paleta monocromática — alinhada com design-tokens.css (--chart-1..4)
// Série primária = mais escura, séries adicionais = opacidade decrescente
const COLORS = [
  'rgba(3,7,18,1.00)',   // --chart-1: série principal
  'rgba(3,7,18,0.60)',   // --chart-2
  'rgba(3,7,18,0.35)',   // --chart-3
  'rgba(3,7,18,0.15)',   // --chart-4
  'rgba(3,7,18,0.50)',   // extra (fallback)
  'rgba(3,7,18,0.25)',   // extra (fallback)
]

interface InteractiveChartProps {
  title: string
  data: any[]
  type: 'line' | 'area' | 'bar' | 'pie' | 'composed'
  dataKeys: string[]
  period: 'monthly' | 'quarterly' | 'yearly'
  onPeriodChange?: (period: 'monthly' | 'quarterly' | 'yearly') => void
  onDrillDown?: (dataPoint: any) => void
  showControls?: boolean
  height?: number
}

export function InteractiveChart({
  title,
  data,
  type,
  dataKeys,
  period,
  onPeriodChange,
  onDrillDown,
  showControls = true,
  height = 300
}: InteractiveChartProps) {
  const [selectedDataPoint, setSelectedDataPoint] = useState<any>(null)
  const [highlightedSeries, setHighlightedSeries] = useState<string | null>(null)
  const chartRef = useRef<any>(null)

  const handleClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!chartRef.current) return
    
    const chart = chartRef.current
    const elements = getElementAtEvent(chart, event)
    
    if (elements.length > 0) {
      const element = elements[0]
      const datasetIndex = element.datasetIndex
      const index = element.index
      const dataPoint = data[index]
      
      setSelectedDataPoint(dataPoint)
      onDrillDown?.(dataPoint)
    }
  }

  const getChartData = () => {
    if (type === 'pie') {
      // Para pie, dataKeys[0] é o campo de dados (ex: 'value', 'count')
      const valueKey = dataKeys[0]
      return {
        labels: data.map((item: any) => item.name || item.stage || item.month),
        datasets: [{
          data: data.map((item: any) => item[valueKey]),
          backgroundColor: data.map((_, index) => COLORS[index % COLORS.length]),
          borderColor: '#fff',
          borderWidth: 2,
        }]
      }
    }

    // Detectar automaticamente o campo de label baseado no que existe nos dados
    const getLabelField = () => {
      if (!data || data.length === 0) return 'month'
      const firstItem = data[0]
      // Tentar campos comuns em ordem de prioridade
      if (firstItem.month) return 'month'
      if (firstItem.stage) return 'stage'
      if (firstItem.name) return 'name'
      if (firstItem.quarter) return 'quarter'
      if (firstItem.category) return 'category'
      if (firstItem.source) return 'source'
      if (firstItem.skill) return 'skill'
      if (firstItem.department) return 'department'
      // Fallback para o primeiro campo não numérico
      for (const key in firstItem) {
        if (typeof firstItem[key] === 'string') return key
      }
      return 'label'
    }
    
    const labelField = getLabelField()
    const labels = data.map((item: any) => item[labelField])
    
    // Para composed: primeiro dataset é bar, segundo é line
    if (type === 'composed') {
      return {
        labels,
        datasets: [
          {
            type: 'bar' as const,
            label: dataKeys[0],
            data: data.map((item: any) => item[dataKeys[0]]),
            backgroundColor: COLORS[0] + 'CC',
            borderColor: COLORS[0],
            yAxisID: 'y',
          },
          {
            type: 'line' as const,
            label: dataKeys[1],
            data: data.map((item: any) => item[dataKeys[1]]),
            backgroundColor: COLORS[1],
            borderColor: COLORS[1],
            borderWidth: 3,
            pointRadius: 5,
            pointHoverRadius: 8,
            yAxisID: 'y1',
          }
        ]
      }
    }
    
    const datasets = dataKeys.map((key, index) => {
      const baseConfig = {
        label: key,
        data: data.map((item: any) => item[key]),
        backgroundColor: COLORS[index % COLORS.length],
        borderColor: COLORS[index % COLORS.length],
        borderWidth: highlightedSeries === key ? 3 : 2,
        pointRadius: highlightedSeries === key ? 6 : 4,
        pointHoverRadius: 8,
      }

      if (type === 'area') {
        return {
          ...baseConfig,
          fill: true,
          backgroundColor: COLORS[index % COLORS.length] + (highlightedSeries === key ? 'CC' : '99'),
        }
      }

      if (type === 'bar') {
        return {
          ...baseConfig,
          backgroundColor: COLORS[index % COLORS.length] + (highlightedSeries === key ? 'FF' : 'CC'),
        }
      }

      return baseConfig
    })

    return { labels, datasets }
  }

  const getChartOptions = (): ChartOptions<any> => {
    const baseOptions: ChartOptions<any> = {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index' as const,
        intersect: false,
      },
      plugins: {
        legend: {
          display: false, // Usando badges customizados
        },
        tooltip: {
          enabled: true,
          backgroundColor: '#F9FAFB',
          titleColor: '#030712',
          bodyColor: '#4B5563',
          borderColor: '#E5E7EB',
          borderWidth: 1,
          padding: 12,
          displayColors: true,
          callbacks: {
            footer: () => 'Clique para drill-down'
          }
        },
      },
      onClick: handleClick as any,
    }

    if (type === 'pie') {
      return {
        ...baseOptions,
        plugins: {
          ...baseOptions.plugins,
          tooltip: {
            ...baseOptions.plugins?.tooltip,
            callbacks: {
              label: (context: any) => {
                const label = context.label || ''
                const value = context.parsed || 0
                const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0)
                const percentage = ((value / total) * 100).toFixed(0)
                return `${label}: ${value} (${percentage}%)`
              }
            }
          }
        }
      }
    }

    if (type === 'composed') {
      return {
        ...baseOptions,
        scales: {
          y: {
            type: 'linear' as const,
            display: true,
            position: 'left' as const,
          },
          y1: {
            type: 'linear' as const,
            display: true,
            position: 'right' as const,
            grid: {
              drawOnChartArea: false,
            },
          },
        },
      }
    }

    return {
      ...baseOptions,
      scales: {
        x: {
          grid: {
            display: true,
            color: '#E5E7EB',
          },
        },
        y: {
          beginAtZero: true,
          grid: {
            display: true,
            color: '#E5E7EB',
          },
        },
      },
    }
  }

  const renderChart = () => {
    const chartData = getChartData()
    const options = getChartOptions()

    switch (type) {
      case 'line':
      case 'area':
        return <Line ref={chartRef} data={chartData as any} options={options} />
      
      case 'bar':
        return <Bar ref={chartRef} data={chartData as any} options={options} />
      
      case 'pie':
        return <Pie ref={chartRef} data={chartData as any} options={options} />
      
      case 'composed':
        return <Chart ref={chartRef} type='bar' data={chartData as any} options={options} />
      
      default:
        return <div>Gráfico não disponível</div>
    }
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            {title}
          </CardTitle>
          {showControls && (
            <div className="flex items-center gap-2">
              {/* Period Selector */}
              <div className="flex bg-gray-100 rounded-md p-1">
                {(['monthly', 'quarterly', 'yearly'] as const).map((p) => (
                  <Button
                    key={p}
                    variant={period === p ? "default" : "ghost"}
                    size="sm"
                    onClick={() => onPeriodChange?.(p)}
                    className="text-xs"
                  >
                    {p === 'monthly' ? 'Mensal' : p === 'quarterly' ? 'Trimestral' : 'Anual'}
                  </Button>
                ))}
              </div>

              {/* Actions */}
              <Button variant="outline" size="sm" className="gap-1">
                <Download className="w-3 h-3" />
                Export
              </Button>
              <Button variant="outline" size="sm" className="gap-1">
                <RefreshCw className="w-3 h-3" />
              </Button>
            </div>
          )}
        </div>

        {/* Legend Controls */}
        <div className="flex flex-wrap gap-2 mt-2">
          {dataKeys.map((key, index) => (
            <Badge
              key={key}
              variant="outline"
              className={`cursor-pointer transition-all ${
                highlightedSeries === key ? 'border-2 bg-gray-100 dark:bg-gray-800' : ''
              }`}
              onClick={() => setHighlightedSeries(highlightedSeries === key ? null : key)}
              style={{ borderColor: COLORS[index % COLORS.length] }}
            >
              <div
                className="w-2 h-2 rounded-full mr-2"
                style={{ backgroundColor: COLORS[index % COLORS.length] }}
              />
              {key}
            </Badge>
          ))}
        </div>
      </CardHeader>

      <CardContent>
        <div className="w-full" style={{ height }}>
          {renderChart()}
        </div>

        {/* Selected Data Point Details */}
        {selectedDataPoint && (
          <div className="mt-4 p-3 bg-gray-100 dark:bg-gray-800 rounded-md border border-gray-300 dark:border-gray-600">
            <h4 className="font-medium text-gray-800 dark:text-gray-200 mb-2">
              Detalhes - {selectedDataPoint.month || selectedDataPoint.stage}
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
              {Object.entries(selectedDataPoint).map(([key, value]) => (
                key !== 'month' && key !== 'stage' && (
                  <div key={key} className="text-gray-600 dark:text-gray-400">
                    <span className="font-medium">{key}:</span> {String(value)}
                  </div>
                )
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// Componente específico para Funil de Conversão
export function ConversionFunnelChart() {
  const [period, setPeriod] = useState<'monthly' | 'quarterly' | 'yearly'>('monthly')

  const funnelData = [
    { stage: 'Pipeline', count: 2847, percentage: 100, color: 'rgba(3,7,18,1.00)' },
    { stage: 'Triagem', count: 1423, percentage: 50, color: 'rgba(3,7,18,0.75)' },
    { stage: 'Entrevistas', count: 512, percentage: 18, color: 'rgba(3,7,18,0.55)' },
    { stage: 'Ofertas', count: 127, percentage: 4.5, color: 'rgba(3,7,18,0.35)' },
    { stage: 'Contratações', count: 89, percentage: 3.1, color: '#16A34A' }  // status-success
  ]

  const handleDrillDown = (dataPoint: any) => {
    console.log('Drill down para:', dataPoint)
    // Implementar navegação para detalhes
  }

  return (
    <InteractiveChart
      title="Funil de Conversão - Drill Down Interativo"
      data={funnelData}
      type="bar"
      dataKeys={['count']}
      period={period}
      onPeriodChange={setPeriod}
      onDrillDown={handleDrillDown}
      height={300}
    />
  )
}

// Componente para Performance dos Recrutadores
export function RecruiterPerformanceChart() {
  const [period, setPeriod] = useState<'monthly' | 'quarterly' | 'yearly'>('monthly')
  const [selectedMetric, setSelectedMetric] = useState('hires')

  const performanceData = generateTimeSeriesData(12, 'up')

  const metrics = [
    { key: 'hires', label: 'Contratações', color: 'rgba(3,7,18,1.00)' },
    { key: 'interviews', label: 'Entrevistas', color: 'rgba(3,7,18,0.60)' },
    { key: 'timeToFill', label: 'Time to Fill', color: 'rgba(3,7,18,0.35)' },
    { key: 'nps', label: 'NPS Score', color: 'rgba(3,7,18,0.15)' }
  ]

  return (
    <div className="space-y-4">
      {/* Metric Selector */}
      <div className="flex gap-2 flex-wrap">
        {metrics.map(metric => (
          <Button
            key={metric.key}
            variant={selectedMetric === metric.key ? "default" : "outline"}
            size="sm"
            onClick={() => setSelectedMetric(metric.key)}
            className="gap-2"
          >
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: metric.color }}
            />
            {metric.label}
          </Button>
        ))}
      </div>

      <InteractiveChart
        title={`Tendência de ${metrics.find(m => m.key === selectedMetric)?.label} - Comparativo por Recrutador`}
        data={performanceData}
        type="line"
        dataKeys={[selectedMetric]}
        period={period}
        onPeriodChange={setPeriod}
        height={350}
      />
    </div>
  )
}

// Componente para Modelos de Trabalho
export function WorkModelDistributionChart() {
  const [period, setPeriod] = useState<'monthly' | 'quarterly' | 'yearly'>('monthly')
  const [viewType, setViewType] = useState<'distribution' | 'trends'>('distribution')

  const distributionData = [
    { name: 'Remoto', value: 42, trend: '+8%' },
    { name: 'Híbrido', value: 35, trend: '+3%' },
    { name: 'Presencial', value: 23, trend: '-11%' }
  ]

  const trendsData = generateTimeSeriesData(12, 'stable').map(item => ({
    ...item,
    remoto: Math.round(40 + Math.random() * 10),
    hibrido: Math.round(30 + Math.random() * 10),
    presencial: Math.round(25 + Math.random() * 10)
  }))

  return (
    <div className="space-y-4">
      {/* View Toggle */}
      <div className="flex gap-2">
        <Button
          variant={viewType === 'distribution' ? "default" : "outline"}
          size="sm"
          onClick={() => setViewType('distribution')}
          className="gap-2"
        >
          <PieIcon className="w-4 h-4" />
          Distribuição
        </Button>
        <Button
          variant={viewType === 'trends' ? "default" : "outline"}
          size="sm"
          onClick={() => setViewType('trends')}
          className="gap-2"
        >
          <TrendingUp className="w-4 h-4" />
          Tendências
        </Button>
      </div>

      {viewType === 'distribution' ? (
        <InteractiveChart
          title="Distribuição por Modelo de Trabalho"
          data={distributionData}
          type="pie"
          dataKeys={['value']}
          period={period}
          onPeriodChange={setPeriod}
          height={300}
        />
      ) : (
        <InteractiveChart
          title="Evolução dos Modelos de Trabalho"
          data={trendsData}
          type="area"
          dataKeys={['remoto', 'hibrido', 'presencial']}
          period={period}
          onPeriodChange={setPeriod}
          height={350}
        />
      )}
    </div>
  )
}

// Componente para Previsões Preditivas
export function PredictiveAnalyticsChart() {
  const [period, setPeriod] = useState<'monthly' | 'quarterly' | 'yearly'>('monthly')
  const [confidenceLevel, setConfidenceLevel] = useState(85)

  const historicalData = generateTimeSeriesData(6, 'up')
  const predictiveData = generateTimeSeriesData(6, 'up').map((item, index) => ({
    ...item,
    month: `Prev ${index + 1}`,
    predicted: true,
    confidence: Math.round(85 + Math.random() * 10),
    upperBound: item.value * 1.2,
    lowerBound: item.value * 0.8
  }))

  const combinedData = [...historicalData, ...predictiveData]

  return (
    <div className="space-y-4">
      {/* Confidence Selector */}
      <div className="flex items-center gap-4">
        <span className="text-sm font-medium">Nível de Confiança:</span>
        <div className="flex gap-2">
          {[80, 85, 90, 95].map(level => (
            <Button
              key={level}
              variant={confidenceLevel === level ? "default" : "outline"}
              size="sm"
              onClick={() => setConfidenceLevel(level)}
            >
              {level}%
            </Button>
          ))}
        </div>
      </div>

      <InteractiveChart
        title="Previsões de Contratação com Intervalos de Confiança"
        data={combinedData}
        type="composed"
        dataKeys={['value', 'upperBound']}
        period={period}
        onPeriodChange={setPeriod}
        height={400}
      />

      {/* Prediction Insights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
        <Card className="border-green-200">
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-600" />
              <div>
                <p className="text-sm font-medium text-green-700">Tendência Positiva</p>
                <p className="text-lg font-bold text-green-800">+24%</p>
                <p className="text-xs text-green-600">Próximos 3 meses</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-gray-300 dark:border-gray-600">
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Target className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Precisão Modelo</p>
                <p className="text-lg font-bold text-gray-900 dark:text-gray-50">92.4%</p>
                <p className="text-xs text-gray-600 dark:text-gray-400">Últimos 6 meses</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-orange-200">
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-orange-600" />
              <div>
                <p className="text-sm font-medium text-orange-700">Atenção Necessária</p>
                <p className="text-lg font-bold text-orange-800">Tech</p>
                <p className="text-xs text-orange-600">Demanda crescente</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
