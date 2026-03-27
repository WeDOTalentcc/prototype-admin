"use client"

import { useState, useMemo, useRef } from "react"
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler,
  ChartOptions
} from 'chart.js'
import { Line, Bar, Pie, Radar, Chart } from 'react-chartjs-2'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Calendar, TrendingUp, TrendingDown, BarChart3, PieChart as PieIcon,
  Activity, Users, DollarSign, Clock, Target, AlertCircle, CheckCircle,
  ChevronDown, Filter, Download, RefreshCw, Zap, Eye, MousePointer
} from "lucide-react"
import { getElementAtEvent } from 'react-chartjs-2'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
)

// Dados realistas para diferentes visualizações
const generateRealisticData = () => {
  const months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
  const quarters = ['Q1 2023', 'Q2 2023', 'Q3 2023', 'Q4 2023', 'Q1 2024']

  return {
    monthlyTrends: months.map((month, index) => ({
      month,
      applications: Math.round(180 + Math.sin(index * 0.5) * 40 + Math.random() * 30),
      interviews: Math.round(65 + Math.sin(index * 0.5) * 15 + Math.random() * 10),
      hires: Math.round(8 + Math.sin(index * 0.3) * 3 + Math.random() * 4),
      timeToFill: Math.round(28 + Math.sin(index * 0.4) * 8 + Math.random() * 6),
      costPerHire: Math.round(3200 + Math.sin(index * 0.2) * 600 + Math.random() * 400),
      nps: Math.round(82 + Math.sin(index * 0.3) * 8 + Math.random() * 6),
      qualityScore: Number((4.2 + Math.sin(index * 0.2) * 0.5 + Math.random() * 0.3).toFixed(1)),
      conversionRate: Number((2.8 + Math.sin(index * 0.4) * 0.8 + Math.random() * 0.4).toFixed(1))
    })),

    recruiterComparison: [
      { name: 'Ana Silva', hires: 12, interviews: 45, nps: 88, timeToFill: 25, conversionRate: 3.2, score: 92 },
      { name: 'Juliana Oliveira', hires: 8, interviews: 32, nps: 91, timeToFill: 22, conversionRate: 4.1, score: 89 },
      { name: 'Carlos Mendes', hires: 6, interviews: 38, nps: 82, timeToFill: 35, conversionRate: 2.1, score: 78 },
      { name: 'Pedro Costa', hires: 4, interviews: 28, nps: 85, timeToFill: 32, conversionRate: 2.8, score: 82 }
    ],

    departmentMetrics: [
      { department: 'Tech', budget: 85000, spent: 72000, hires: 15, avgSalary: 9500, openPositions: 8 },
      { department: 'Sales', budget: 45000, spent: 38000, hires: 12, avgSalary: 6800, openPositions: 6 },
      { department: 'Design', budget: 35000, spent: 28000, hires: 8, avgSalary: 7200, openPositions: 4 },
      { department: 'Marketing', budget: 40000, spent: 35000, hires: 6, avgSalary: 6200, openPositions: 5 },
      { department: 'Product', budget: 60000, spent: 52000, hires: 9, avgSalary: 8900, openPositions: 7 }
    ],

    funnelDetailed: [
      { stage: 'Aplicações', total: 1247, tech: 456, sales: 298, design: 234, marketing: 187, product: 72 },
      { stage: 'Triagem', total: 623, tech: 228, sales: 149, design: 117, marketing: 94, product: 35 },
      { stage: 'Entrevista', total: 298, tech: 109, sales: 71, design: 56, marketing: 45, product: 17 },
      { stage: 'Final', total: 156, tech: 57, sales: 37, design: 29, marketing: 23, product: 10 },
      { stage: 'Contratação', total: 50, tech: 18, sales: 12, design: 9, marketing: 7, product: 4 }
    ],

    sourceAnalysis: [
      { source: 'LinkedIn', applications: 456, hires: 18, cost: 12500, quality: 4.2 },
      { source: 'Indicações', applications: 234, hires: 15, cost: 8900, quality: 4.6 },
      { source: 'Site Empresa', applications: 312, hires: 12, cost: 5600, quality: 3.8 },
      { source: 'Job Boards', applications: 189, hires: 8, cost: 7800, quality: 3.4 },
      { source: 'Headhunting', applications: 56, hires: 7, cost: 15600, quality: 4.8 }
    ],

    skillsAnalysis: [
      { skill: 'React/TypeScript', demand: 45, supply: 28, gap: 17, avgSalary: 9500 },
      { skill: 'Python/Django', demand: 38, supply: 22, gap: 16, avgSalary: 10200 },
      { skill: 'UX/UI Design', demand: 28, supply: 18, gap: 10, avgSalary: 7800 },
      { skill: 'Data Science', demand: 22, supply: 12, gap: 10, avgSalary: 12000 },
      { skill: 'DevOps/AWS', demand: 35, supply: 15, gap: 20, avgSalary: 11500 },
      { skill: 'Product Management', demand: 18, supply: 9, gap: 9, avgSalary: 9800 }
    ],

    workModelTrends: quarters.map((quarter, index) => ({
      quarter,
      remote: 35 + index * 3 + Math.random() * 5,
      hybrid: 30 + index * 2 + Math.random() * 4,
      office: 35 - index * 5 + Math.random() * 3
    })),

    diversityMetrics: [
      { category: 'Gênero', female: 48, male: 50, nonBinary: 2 },
      { category: 'Etnia', white: 52, brown: 31, black: 14, other: 3 },
      { category: 'Idade', under25: 18, between25and35: 42, between35and50: 32, over50: 8 },
      { category: 'PCD', pcd: 8.5, noPcd: 91.5 }
    ]
  }
}

const COLORS = {
  primary: ['#3B82F6', '#1D4ED8', '#1E40AF', '#1E3A8A'],
  secondary: ['#10B981', '#059669', '#047857', '#065F46'],
  tertiary: ['#F59E0B', '#D97706', '#B45309', '#92400E'],
  quaternary: ['#EF4444', '#DC2626', '#B91C1C', '#991B1B'],
  neutral: ['#6B7280', '#4B5563', '#374151', '#1F2937'],
  rainbow: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#84CC16', '#F97316']
}

interface AdvancedChartProps {
  type: 'line' | 'area' | 'bar' | 'pie' | 'scatter' | 'radar' | 'funnel' | 'treemap' | 'composed'
  title: string
  data: any[]
  dataKeys: string[]
  height?: number
  showControls?: boolean
  drillDownEnabled?: boolean
  onDataPointClick?: (data: any) => void
}

export function AdvancedInteractiveChart({
  type,
  title,
  data,
  dataKeys,
  height = 400,
  showControls = true,
  drillDownEnabled = true,
  onDataPointClick
}: AdvancedChartProps) {
  const [selectedDataPoint, setSelectedDataPoint] = useState<any>(null)
  const [chartConfig, setChartConfig] = useState({
    showGrid: true,
    showLegend: true,
    showTooltip: true,
    animationDuration: 1000
  })
  const chartRef = useRef<any>(null)

  const handleClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!chartRef.current || !drillDownEnabled) return
    
    const chart = chartRef.current
    const elements = getElementAtEvent(chart, event)
    
    if (elements.length > 0) {
      const element = elements[0]
      const index = element.index
      const dataPoint = data[index]
      
      setSelectedDataPoint(dataPoint)
      onDataPointClick?.(dataPoint)
    }
  }

  const getChartData = () => {
    const labelKey = dataKeys[0]
    
    if (type === 'pie') {
      // Para pie, se temos 2+ dataKeys, o primeiro é label, segundo é valor
      // Se temos 1 dataKey, é o valor e usamos name/stage como label
      const valueKey = dataKeys.length > 1 ? dataKeys[1] : dataKeys[0]
      const labels = dataKeys.length > 1 
        ? data.map((item: any) => item[labelKey])
        : data.map((item: any) => item.name || item.stage || item.category)
      
      return {
        labels,
        datasets: [{
          data: data.map((item: any) => item[valueKey]),
          backgroundColor: COLORS.rainbow,
          borderColor: '#fff',
          borderWidth: 2,
        }]
      }
    }

    if (type === 'radar') {
      return {
        labels: dataKeys.slice(1),
        datasets: data.map((item: any, index: number) => ({
          label: item[labelKey],
          data: dataKeys.slice(1).map(key => item[key]),
          backgroundColor: COLORS.primary[index % COLORS.primary.length] + '33',
          borderColor: COLORS.primary[index % COLORS.primary.length],
          borderWidth: 2,
          pointBackgroundColor: COLORS.primary[index % COLORS.primary.length],
          pointBorderColor: '#fff',
          pointHoverBackgroundColor: '#fff',
          pointHoverBorderColor: COLORS.primary[index % COLORS.primary.length],
        }))
      }
    }

    if (type === 'funnel') {
      // Funnel como horizontal bar chart
      return {
        labels: data.map((item: any) => item[labelKey]),
        datasets: [{
          label: dataKeys[1],
          data: data.map((item: any) => item[dataKeys[1]]),
          backgroundColor: COLORS.rainbow,
          borderRadius: 4,
        }]
      }
    }

    // Detectar automaticamente o campo de label baseado no que existe nos dados
    const getLabelValue = () => {
      if (!data || data.length === 0) return []
      return data.map((item: any) => item[labelKey] || item.month || item.stage || item.name || item.quarter || '')
    }
    
    const labels = getLabelValue()
    
    // Para composed: primeiro dataset é bar, segundo é line em eixos diferentes
    if (type === 'composed') {
      const valuableKeys = dataKeys.slice(1)
      return {
        labels,
        datasets: [
          {
            type: 'bar' as const,
            label: valuableKeys[0],
            data: data.map((item: any) => item[valuableKeys[0]]),
            backgroundColor: COLORS.tertiary[0] + 'CC',
            borderColor: COLORS.tertiary[0],
            yAxisID: 'y',
            borderRadius: 4,
          },
          {
            type: 'line' as const,
            label: valuableKeys[1],
            data: data.map((item: any) => item[valuableKeys[1]]),
            backgroundColor: COLORS.primary[0],
            borderColor: COLORS.primary[0],
            borderWidth: 3,
            pointRadius: 5,
            pointHoverRadius: 8,
            yAxisID: 'y1',
          }
        ]
      }
    }
    
    const valuableKeys = dataKeys.slice(1)
    
    const datasets = valuableKeys.map((key, index) => {
      const colorArray = type === 'area' ? COLORS.secondary : 
                         type === 'bar' ? COLORS.tertiary : 
                         COLORS.primary

      const baseConfig = {
        label: key,
        data: data.map((item: any) => item[key]),
        backgroundColor: colorArray[index % colorArray.length] + (type === 'area' ? '99' : 'CC'),
        borderColor: colorArray[index % colorArray.length],
        borderWidth: type === 'line' ? 3 : 2,
        pointRadius: type === 'line' ? 5 : 0,
        pointHoverRadius: type === 'line' ? 8 : 0,
        tension: 0.3,
      }

      if (type === 'area') {
        return {
          ...baseConfig,
          fill: true,
        }
      }

      if (type === 'bar') {
        return {
          ...baseConfig,
          borderRadius: 4,
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
          display: chartConfig.showLegend,
          position: 'top' as const,
        },
        tooltip: {
          enabled: chartConfig.showTooltip,
          backgroundColor: '#fff',
          titleColor: '#111',
          bodyColor: '#555',
          borderColor: '#ddd',
          borderWidth: 1,
          padding: 12,
          displayColors: true,
          callbacks: {
            footer: drillDownEnabled ? () => '🔍 Clique para drill-down' : undefined
          }
        },
      },
      onClick: handleClick as any,
      animation: {
        duration: chartConfig.animationDuration,
      },
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

    if (type === 'radar') {
      return {
        ...baseOptions,
        scales: {
          r: {
            beginAtZero: true,
            grid: {
              display: chartConfig.showGrid,
            },
          },
        },
      }
    }

    if (type === 'funnel') {
      return {
        ...baseOptions,
        indexAxis: 'y' as const,
        scales: {
          x: {
            beginAtZero: true,
            grid: {
              display: chartConfig.showGrid,
              color: '#f0f0f0',
            },
          },
          y: {
            grid: {
              display: false,
            },
          },
        },
      }
    }

    if (type === 'composed') {
      return {
        ...baseOptions,
        scales: {
          x: {
            grid: {
              display: chartConfig.showGrid,
              color: '#f0f0f0',
            },
          },
          y: {
            type: 'linear' as const,
            display: true,
            position: 'left' as const,
            beginAtZero: true,
            grid: {
              display: chartConfig.showGrid,
              color: '#f0f0f0',
            },
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
            display: chartConfig.showGrid,
            color: '#f0f0f0',
          },
        },
        y: {
          beginAtZero: true,
          grid: {
            display: chartConfig.showGrid,
            color: '#f0f0f0',
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
      case 'funnel':
        return <Bar ref={chartRef} data={chartData as any} options={options} />
      
      case 'pie':
        return <Pie ref={chartRef} data={chartData as any} options={options} />
      
      case 'radar':
        return <Radar ref={chartRef} data={chartData as any} options={options} />
      
      case 'composed':
        return <Chart ref={chartRef} type='bar' data={chartData as any} options={options} />
      
      case 'treemap':
      case 'scatter':
        return (
          <div className="flex items-center justify-center h-full text-gray-800 dark:text-gray-200">
            Tipo de gráfico não disponível no Chart.js. Considere usar Bar ou Pie como alternativa.
          </div>
        )
      
      default:
        return (
          <div className="flex items-center justify-center h-full text-gray-800 dark:text-gray-200">
            Tipo de gráfico não suportado
          </div>
        )
    }
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              {title}
            </CardTitle>
            {selectedDataPoint && (
              <p className="text-sm text-gray-600 mt-1">
                📊 Selecionado: {selectedDataPoint[dataKeys[0]]}
              </p>
            )}
          </div>

          {showControls && (
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" className="gap-1">
                <Download className="w-3 h-3" />
                PNG
              </Button>
              <Button variant="outline" size="sm" className="gap-1">
                <Download className="w-3 h-3" />
                PDF
              </Button>
              <Button variant="outline" size="sm" className="gap-1">
                <RefreshCw className="w-3 h-3" />
              </Button>
            </div>
          )}
        </div>

        {/* Chart Controls */}
        <div className="flex items-center gap-4 text-sm mt-2">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={chartConfig.showGrid}
              onChange={(e) => setChartConfig(prev => ({ ...prev, showGrid: e.target.checked }))}
              className="rounded"
            />
            Grade
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={chartConfig.showLegend}
              onChange={(e) => setChartConfig(prev => ({ ...prev, showLegend: e.target.checked }))}
              className="rounded"
            />
            Legenda
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={chartConfig.showTooltip}
              onChange={(e) => setChartConfig(prev => ({ ...prev, showTooltip: e.target.checked }))}
              className="rounded"
            />
            Tooltip
          </label>
          {drillDownEnabled && (
            <Badge variant="outline" className="gap-1">
              <MousePointer className="w-3 h-3" />
              Drill-down ativo
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent>
        <div className="w-full" style={{ height }}>
          {renderChart()}
        </div>

        {/* Drill-down Details */}
        {selectedDataPoint && (
          <div className="mt-4 p-4 bg-gray-100 dark:bg-gray-800 rounded-md border border-gray-300 dark:border-gray-600">
            <h4 className="font-medium text-gray-800 dark:text-gray-200 mb-3">
              📊 Detalhes - {selectedDataPoint[dataKeys[0]]}
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(selectedDataPoint).map(([key, value]) => (
                key !== dataKeys[0] && (
                  <div key={key} className="text-center">
                    <div className="text-lg font-bold text-gray-900 dark:text-gray-50">{String(value)}</div>
                    <div className="text-xs text-gray-600 dark:text-gray-400 capitalize">{key}</div>
                  </div>
                )
              ))}
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedDataPoint(null)}
              className="mt-3 text-gray-600 dark:text-gray-400"
            >
              Fechar detalhes
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// Componentes específicos para diferentes métricas
export function RecruitmentTrendsChart() {
  const data = generateRealisticData()

  return (
    <AdvancedInteractiveChart
      type="line"
      title="Tendências de Recrutamento - Últimos 12 Meses"
      data={data.monthlyTrends}
      dataKeys={['month', 'applications', 'interviews', 'hires']}
      height={400}
      drillDownEnabled={true}
    />
  )
}

export function RecruiterPerformanceRadar() {
  const data = generateRealisticData()

  return (
    <AdvancedInteractiveChart
      type="radar"
      title="Comparação de Performance - Recrutadores"
      data={data.recruiterComparison}
      dataKeys={['name', 'nps', 'conversionRate', 'score']}
      height={400}
      drillDownEnabled={true}
    />
  )
}

export function DepartmentBudgetChart() {
  const data = generateRealisticData()

  return (
    <AdvancedInteractiveChart
      type="composed"
      title="Orçamento vs Performance por Departamento"
      data={data.departmentMetrics}
      dataKeys={['department', 'spent', 'hires']}
      height={400}
      drillDownEnabled={true}
    />
  )
}

export function DetailedFunnelChart() {
  const data = generateRealisticData()

  return (
    <AdvancedInteractiveChart
      type="bar"
      title="Funil Detalhado por Departamento"
      data={data.funnelDetailed}
      dataKeys={['stage', 'tech', 'sales', 'design', 'marketing', 'product']}
      height={400}
      drillDownEnabled={true}
    />
  )
}

export function SourceEffectivenessChart() {
  const data = generateRealisticData()

  return (
    <AdvancedInteractiveChart
      type="area"
      title="Efetividade por Fonte de Recrutamento"
      data={data.sourceAnalysis}
      dataKeys={['source', 'applications', 'hires']}
      height={400}
      drillDownEnabled={true}
    />
  )
}

export function SkillsGapChart() {
  const data = generateRealisticData()

  return (
    <AdvancedInteractiveChart
      type="bar"
      title="Análise de Skills Gap"
      data={data.skillsAnalysis}
      dataKeys={['skill', 'demand', 'supply', 'gap']}
      height={400}
      drillDownEnabled={true}
    />
  )
}

export { generateRealisticData }
