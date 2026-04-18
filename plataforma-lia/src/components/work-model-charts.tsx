"use client"

import { useState, useMemo } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  PieChart, BarChart3, TrendingUp, Calendar, Filter,
  Home, Globe, Building, Users, MapPin, Star
} from "lucide-react"

interface ChartData {
  label: string
  value: number
  percentage: number
  color: string
  icon?: React.ReactNode
}

interface TrendData {
  period: string
  remoto: number
  hibrido: number
  presencial: number
}

interface WorkModelChartsProps {
  className?: string
}

export function WorkModelCharts({ className }: WorkModelChartsProps) {
  const [selectedChart, setSelectedChart] = useState<'donut' | 'bar' | 'trend' | 'heatmap'>('donut')
  const [selectedPeriod, setSelectedPeriod] = useState<'week' | 'month' | 'quarter' | 'year'>('month')

  // Mock data para gráfico de pizza/donut
  const donutData: ChartData[] = [
    {
      label: 'Híbrido',
      value: 489,
      percentage: 48.9,
      color: 'bg-lia-bg-inverse',
      icon: <Globe className="w-4 h-4" />
    },
    {
      label: 'Remoto',
      value: 342,
      percentage: 34.2,
      color: 'bg-status-success',
      icon: <Home className="w-4 h-4" />
    },
    {
      label: 'Presencial',
      value: 169,
      percentage: 16.9,
      color: 'bg-lia-bg-secondary',
      icon: <Building className="w-4 h-4" />
    }
  ]

  // Mock data para tendências temporais
  const trendData: TrendData[] = [
    { period: 'Jan', remoto: 280, hibrido: 420, presencial: 200 },
    { period: 'Fev', remoto: 295, hibrido: 435, presencial: 190 },
    { period: 'Mar', remoto: 310, hibrido: 450, presencial: 180 },
    { period: 'Abr', remoto: 325, hibrido: 465, presencial: 175 },
    { period: 'Mai', remoto: 342, hibrido: 489, presencial: 169 }
  ]

  // Gráfico de barras por cargo
  const cargoData = [
    { cargo: 'Full Stack', remoto: 52, hibrido: 41, presencial: 15 },
    { cargo: 'Frontend', remoto: 45, hibrido: 32, presencial: 8 },
    { cargo: 'Backend', remoto: 38, hibrido: 28, presencial: 12 },
    { cargo: 'UX Designer', remoto: 28, hibrido: 35, presencial: 18 },
    { cargo: 'DevOps', remoto: 41, hibrido: 22, presencial: 8 }
  ]

  const maxValue = Math.max(...cargoData.flatMap(item => [item.remoto, item.hibrido, item.presencial]))

  // Componente do gráfico donut/pizza
  const DonutChart = () => {
    const total = donutData.reduce((sum, item) => sum + item.value, 0)
    let cumulativePercentage = 0

    return (
      <div className="flex items-center justify-center">
        <div className="relative">
          {/* SVG Donut Chart */}
          <svg width="200" height="200" className="transform -rotate-90">
            <circle
              cx="100"
              cy="100"
              r="80"
              fill="none"
              stroke="var(--lia-border-subtle)"
              strokeWidth="20"
            />
            {donutData.map((item, index) => {
              const percentage = item.percentage
              const strokeDasharray = `${percentage * 5.03} 502.3`
              const strokeDashoffset = -cumulativePercentage * 5.03
              cumulativePercentage += percentage

              return (
                <circle
                  key={`donut-${index}`}
                  cx="100"
                  cy="100"
                  r="80"
                  fill="none"
                  stroke={item.color.replace('bg-', '#').replace('500', 'var(--wedo-blue)').replace('green', 'var(--status-success)').replace('gray', 'var(--lia-text-tertiary)')}
                  strokeWidth="20"
                  strokeDasharray={strokeDasharray}
                  strokeDashoffset={strokeDashoffset}
                  className="transition-colors motion-reduce:transition-none duration-300"
                />
              )
            })}
          </svg>

          {/* Centro do donut */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="text-2xl font-semibold text-lia-text-primary">
                {total}
              </div>
              <div className="text-xs text-lia-text-primary">
                Total
              </div>
            </div>
          </div>
        </div>

        {/* Legenda */}
        <div className="ml-8 space-y-3">
          {donutData.map((item) => (
            <div key={item.label || (item as unknown as Record<string, unknown>).name as string} className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <div className={`w-4 h-4 rounded-full ${item.color}`}></div>
                {item.icon}
              </div>
              <div>
                <div className="font-medium text-lia-text-primary">
                  {item.label}
                </div>
                <div className="text-sm text-lia-text-primary">
                  {item.value} ({item.percentage}%)
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // Componente de gráfico de barras
  const BarChart = () => (
    <div className="space-y-6">
      {cargoData.map((item) => (
        <div key={(item as unknown as Record<string, unknown>).label as string || item.cargo || (item as unknown as Record<string, unknown>).name as string} className="space-y-2">
          <div className="flex items-center justify-between">
            <h4 className="font-medium text-lia-text-primary">
              {item.cargo}
            </h4>
            <span className="text-sm text-lia-text-primary">
              {item.remoto + item.hibrido + item.presencial} candidatos
            </span>
          </div>

          <div className="space-y-1">
            {/* Remoto */}
            <div className="flex items-center gap-3">
              <div className="w-16 text-xs text-lia-text-secondary flex items-center gap-1">
                <Home className="w-3 h-3 text-status-success" />
                Remoto
              </div>
              <div className="flex-1 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full h-2">
                <div
                  className="bg-status-success h-2 rounded-full transition-[width,height] duration-300"
                  style={{width: `${(item.remoto / maxValue) * 100}%`}}
                ></div>
              </div>
              <div className="w-8 text-xs text-lia-text-secondary text-right">
                {item.remoto}
              </div>
            </div>

            {/* Híbrido */}
            <div className="flex items-center gap-3">
              <div className="w-16 text-xs text-lia-text-secondary flex items-center gap-1">
                <Globe className="w-3 h-3 text-lia-text-secondary" />
                Híbrido
              </div>
              <div className="flex-1 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full h-2">
                <div
                  className="bg-lia-bg-inverse h-2 rounded-full transition-[width,height] duration-300"
                  style={{width: `${(item.hibrido / maxValue) * 100}%`}}
                ></div>
              </div>
              <div className="w-8 text-xs text-lia-text-secondary text-right">
                {item.hibrido}
              </div>
            </div>

            {/* Presencial */}
            <div className="flex items-center gap-3">
              <div className="w-16 text-xs text-lia-text-secondary flex items-center gap-1">
                <Building className="w-3 h-3 text-lia-text-secondary" />
                Presencial
              </div>
              <div className="flex-1 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full h-2">
                <div
                  className="bg-lia-bg-secondary h-2 rounded-full transition-[width,height] duration-300"
                  style={{width: `${(item.presencial / maxValue) * 100}%`}}
                ></div>
              </div>
              <div className="w-8 text-xs text-lia-text-secondary text-right">
                {item.presencial}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )

  // Componente de gráfico de tendências
  const TrendChart = () => {
    const maxTrendValue = Math.max(...trendData.flatMap(item => [item.remoto, item.hibrido, item.presencial]))

    return (
      <div className="space-y-4">
        <div className="grid grid-cols-5 gap-4">
          {trendData.map((item) => (
            <div key={(item as unknown as Record<string, unknown>).month as string || (item as unknown as Record<string, unknown>).label as string || (item as unknown as Record<string, unknown>).name as string} className="text-center">
              <div className="mb-2 text-xs font-medium text-lia-text-secondary">
                {item.period}
              </div>

              <div className="relative h-32 flex items-end justify-center gap-1">
                {/* Remoto */}
                <div className="w-3 bg-status-success rounded-t" style={{height: `${(item.remoto / maxTrendValue) * 100}%`,
                  minHeight: '4px'}} title={`Remoto: ${item.remoto}`}></div>

                {/* Híbrido */}
                <div className="w-3 bg-lia-bg-inverse rounded-t" style={{height: `${(item.hibrido / maxTrendValue) * 100}%`,
                  minHeight: '4px'}} title={`Híbrido: ${item.hibrido}`}></div>

                {/* Presencial */}
                <div className="w-3 bg-lia-bg-secondary rounded-t" style={{height: `${(item.presencial / maxTrendValue) * 100}%`,
                  minHeight: '4px'}} title={`Presencial: ${item.presencial}`}></div>
              </div>

              <div className="mt-2 text-xs text-lia-text-primary">
                {item.remoto + item.hibrido + item.presencial}
              </div>
            </div>
          ))}
        </div>

        {/* Legenda */}
        <div className="flex items-center justify-center gap-6 pt-4 border-t border-lia-border-subtle dark:border-lia-border-subtle">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-status-success rounded-md"></div>
            <span className="text-xs text-lia-text-secondary">Remoto</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-lia-bg-inverse rounded-xl"></div>
            <span className="text-xs text-lia-text-secondary">Híbrido</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-lia-bg-secondary rounded-xl"></div>
            <span className="text-xs text-lia-text-secondary">Presencial</span>
          </div>
        </div>
      </div>
    )
  }

  // Heatmap simples de regiões
  const HeatmapChart = () => {
    const regionData = [
      { regiao: 'SP', total: 479, densidade: 'alta' },
      { regiao: 'RJ', total: 235, densidade: 'alta' },
      { regiao: 'MG', total: 97, densidade: 'media' },
      { regiao: 'RS', total: 81, densidade: 'media' },
      { regiao: 'SC', total: 55, densidade: 'baixa' },
      { regiao: 'PR', total: 43, densidade: 'baixa' },
      { regiao: 'DF', total: 54, densidade: 'baixa' },
      { regiao: 'PE', total: 39, densidade: 'baixa' },
      { regiao: 'BA', total: 30, densidade: 'baixa' }
    ]

    const getDensityColor = (densidade: string) => {
      switch (densidade) {
        case 'alta': return 'bg-status-error'
        case 'media': return 'bg-status-warning'
        case 'baixa': return 'bg-status-success'
        default: return 'bg-lia-border-default'
      }
    }

    return (
      <div className="space-y-4">
        <div className="grid grid-cols-3 gap-4">
          {regionData.map((region) => (
            <div
              key={(region as Record<string, unknown>).name as string || (region as Record<string, unknown>).region as string}
              className={`p-4 rounded-md text-white text-center transition-transform motion-reduce:transition-none duration-300 hover:scale-105 ${getDensityColor(region.densidade)}`}
            >
              <div className="font-semibold text-lg">{region.regiao}</div>
              <div className="text-sm opacity-90">{region.total} candidatos</div>
              <div className="text-xs opacity-75 capitalize">{region.densidade} densidade</div>
            </div>
          ))}
        </div>

        {/* Legenda do heatmap */}
        <div className="flex items-center justify-center gap-6 pt-4 border-t border-lia-border-subtle dark:border-lia-border-subtle">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-status-success rounded-md"></div>
            <span className="text-xs text-lia-text-secondary">Baixa densidade (&lt;60)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-status-warning rounded-md"></div>
            <span className="text-xs text-lia-text-secondary">Média densidade (60-100)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-status-error rounded-md"></div>
            <span className="text-xs text-lia-text-secondary">Alta densidade (&gt;200)</span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={className}>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-lia-text-secondary" />
              Visualizações Interativas
            </CardTitle>

            {/* Seletor de tipo de gráfico */}
            <div className="flex bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl p-1">
              <button
                onClick={() => setSelectedChart('donut')}
                className={`px-3 py-1 text-xs rounded-md transition-colors motion-reduce:transition-none flex items-center gap-1 ${
 selectedChart === 'donut'
                    ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text'
                    : 'text-lia-text-secondary hover:text-lia-text-primary'
                }`}
              >
                <PieChart className="w-3 h-3" />
                Distribuição
              </button>
              <button
                onClick={() => setSelectedChart('bar')}
                className={`px-3 py-1 text-xs rounded-md transition-colors motion-reduce:transition-none flex items-center gap-1 ${
 selectedChart === 'bar'
                    ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text'
                    : 'text-lia-text-secondary hover:text-lia-text-primary'
                }`}
              >
                <BarChart3 className="w-3 h-3" />
                Por Cargo
              </button>
              <button
                onClick={() => setSelectedChart('trend')}
                className={`px-3 py-1 text-xs rounded-md transition-colors motion-reduce:transition-none flex items-center gap-1 ${
 selectedChart === 'trend'
                    ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text'
                    : 'text-lia-text-secondary hover:text-lia-text-primary'
                }`}
              >
                <TrendingUp className="w-3 h-3" />
                Tendências
              </button>
              <button
                onClick={() => setSelectedChart('heatmap')}
                className={`px-3 py-1 text-xs rounded-md transition-colors motion-reduce:transition-none flex items-center gap-1 ${
 selectedChart === 'heatmap'
                    ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text'
                    : 'text-lia-text-secondary hover:text-lia-text-primary'
                }`}
              >
                <MapPin className="w-3 h-3" />
                Mapa
              </button>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          <div className="min-h-content-md">
            {selectedChart === 'donut' && <DonutChart />}
            {selectedChart === 'bar' && <BarChart />}
            {selectedChart === 'trend' && <TrendChart />}
            {selectedChart === 'heatmap' && <HeatmapChart />}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
