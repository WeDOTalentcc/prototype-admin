"use client"

import React, { useState, useEffect, useRef, useCallback, useMemo } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Maximize2, Minimize2, Play, Pause, RefreshCw, Calendar,
  BarChart3, TrendingUp, TrendingDown, Users, Briefcase,
  DollarSign, Clock, Target, Activity, ArrowUp, ArrowDown,
  Zap, CheckCircle, AlertTriangle, Eye, ChevronLeft, ChevronRight,
  Settings, Grid3X3, PresentationIcon as PresentationChart,
  Monitor, Home, X
} from "lucide-react"

interface PresentationModeProps {
  isActive: boolean
  onToggle: () => void
  currentPage: string
  data?: Record<string, unknown>
}

interface DashboardSlide {
  id: string
  title: string
  component: React.ComponentType<{ data: Record<string, unknown> }>
  icon: React.ComponentType<{ className?: string }>
  duration?: number // seconds to auto-advance
}

// Dashboard data mock memoizado
const mockData = {
  kpis: [
    { label: "Vagas Ativas", value: 18, change: +15, trend: "up", color: "blue" },
    { label: "Candidatos", value: 1247, change: +23, trend: "up", color: "green" },
    { label: "Contratações", value: 12, change: -8, trend: "down", color: "purple" },
    { label: "Time to Hire", value: "28d", change: -12, trend: "down", color: "orange" },
    { label: "Taxa Sucesso", value: "87%", change: +5, trend: "up", color: "teal" },
    { label: "NPS Médio", value: 82, change: +7, trend: "up", color: "pink" }
  ],
  departments: [
    { name: "Tecnologia", jobs: 8, hires: 5, efficiency: 87 },
    { name: "Design", jobs: 4, hires: 3, efficiency: 91 },
    { name: "Produto", jobs: 3, hires: 2, efficiency: 79 },
    { name: "Marketing", jobs: 5, hires: 2, efficiency: 85 }
  ],
  alerts: [
    { type: "success", message: "Meta Q1 atingida: 85% das contratações" },
    { type: "warning", message: "5 vagas com prazo vencendo em 7 dias" },
    { type: "error", message: "Orçamento 90% utilizado - Produto" }
  ]
} as const

// Componente de KPI memoizado
const KPICard = React.memo(({ kpi, index }: { kpi: { label: string; value: number; change: number; trend: string; color: string }; index: number }) => (
  <Card key={kpi.label} className="bg-lia-bg-primary dark:bg-lia-bg-secondary border-2 transition-colors motion-reduce:transition-none">
    <CardContent className="p-8 text-center">
      <div className="text-5xl font-bold text-lia-text-primary mb-4">
        {kpi.value}
      </div>
      <div className="text-xl font-medium text-lia-text-primary mb-4">
        {kpi.label}
      </div>
      <div className="flex items-center justify-center gap-2">
        {kpi.trend === "up" ?
          <ArrowUp className="w-6 h-6 text-status-success" /> :
          <ArrowDown className="w-6 h-6 text-status-error" />
        }
        <span className={`text-lg font-medium ${
 kpi.trend === "up" ? "text-status-success" : "text-status-error"
        }`}>
          {Math.abs(kpi.change)}%
        </span>
      </div>
    </CardContent>
  </Card>
))

KPICard.displayName = 'KPICard'

// Slide Components memoizados
const KPISlide = React.memo(({ data }: { data: Record<string, unknown> }) => {
  const currentDate = useMemo(() => new Date().toLocaleDateString('pt-BR'), [])

  return (
    <div className="h-full flex flex-col justify-center p-16">
      <h1 className="text-6xl font-semibold text-lia-text-primary mb-4 text-center">
        Indicadores Principais
      </h1>
      <p className="text-2xl text-lia-text-secondary text-center mb-16">
        Performance de Recrutamento - {currentDate}
      </p>

      <div className="grid grid-cols-3 gap-8">
        {(data.kpis as { label: string; value: number; change: number; trend: string; color: string }[]).map((kpi, index: number) => (
          <KPICard key={`${kpi.label}-${index}`} kpi={kpi} index={index} />
        ))}
      </div>
    </div>
  )
})

KPISlide.displayName = 'KPISlide'

// Componente de departamento memoizado
const DepartmentCard = React.memo(({ dept, index }: { dept: { name: string; efficiency: number; openPositions: number; avgDays: number }; index: number }) => (
  <Card key={dept.name} className="bg-lia-bg-primary dark:bg-lia-bg-secondary border">
    <CardContent className="p-8">
      <div className="text-center mb-6">
        <h3 className="text-3xl font-semibold text-lia-text-primary mb-2">
          {dept.name}
        </h3>
        <div className="text-6xl font-bold text-lia-text-primary mb-4">
          {dept.efficiency}%
        </div>
        <div className="text-lg text-lia-text-secondary">
          Eficiência
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4 text-center">
        <div>
          <div className="text-2xl font-semibold text-lia-text-primary">
            {((dept as any).jobs as React.ReactNode)}
          </div>
          <div className="text-sm text-lia-text-secondary">
            Vagas
          </div>
        </div>
        <div>
          <div className="text-2xl font-semibold text-lia-text-primary">
            {((dept as any).hires as React.ReactNode)}
          </div>
          <div className="text-sm text-lia-text-secondary">
            Contratações
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
))

DepartmentCard.displayName = 'DepartmentCard'

const DepartmentSlide = React.memo(({ data }: { data: Record<string, unknown> }) => (
  <div className="h-full flex flex-col justify-center p-16">
    <h1 className="text-6xl font-semibold text-lia-text-primary mb-4 text-center">
      Performance por Departamento
    </h1>
    <p className="text-2xl text-lia-text-secondary text-center mb-16">
      Eficiência de Recrutamento por Área
    </p>

    <div className="grid grid-cols-2 gap-8">
      {(data.departments as { name: string; efficiency: number; openPositions: number; avgDays: number }[]).map((dept, index: number) => (
        <DepartmentCard key={`${dept.name}-${index}`} dept={dept} index={index} />
      ))}
    </div>
  </div>
))

DepartmentSlide.displayName = 'DepartmentSlide'

// Componente de alerta memoizado
const AlertItem = React.memo(({ alert, index }: { alert: { type: string; message: string }; index: number }) => {
  const getIcon = useMemo(() => {
    switch (alert.type) {
      case "success": return <CheckCircle className="w-8 h-8 text-status-success" />
      case "warning": return <AlertTriangle className="w-8 h-8 text-status-warning" />
      case "error": return <AlertTriangle className="w-8 h-8 text-status-error" />
      default: return <Activity className="w-8 h-8 text-lia-text-secondary" />
    }
  }, [alert.type])

  const getBgColor = useMemo(() => {
    switch (alert.type) {
      case "success": return "bg-status-success/10 border-status-success/30"
      case "warning": return "bg-status-warning/10 border-status-warning/30"
      case "error": return "bg-status-error/10 border-status-error/30"
      default: return "bg-lia-bg-tertiary dark:bg-lia-bg-secondary border-lia-border-default dark:border-lia-border-default"
    }
  }, [alert.type])

  return (
    <Card key={alert.message} className={`border ${getBgColor}`}>
      <CardContent className="p-6 flex items-center gap-4">
        {getIcon}
        <div className="text-xl font-medium text-lia-text-primary">
          {alert.message}
        </div>
      </CardContent>
    </Card>
  )
})

AlertItem.displayName = 'AlertItem'

const AlertsSlide = React.memo(({ data }: { data: Record<string, unknown> }) => (
  <div className="h-full flex flex-col justify-center p-16">
    <h1 className="text-6xl font-semibold text-lia-text-primary mb-4 text-center">
      Alertas e Status
    </h1>
    <p className="text-2xl text-lia-text-secondary text-center mb-16">
      Monitoramento em Tempo Real
    </p>

    <div className="space-y-6">
      {(data.alerts as { type: string; message: string }[]).map((alert, index: number) => (
        <AlertItem key={`${alert.type}-${index}`} alert={alert} index={index} />
      ))}
    </div>
  </div>
))

AlertsSlide.displayName = 'AlertsSlide'

export function PresentationMode({ isActive, onToggle, currentPage, data }: PresentationModeProps) {
  const [currentSlide, setCurrentSlide] = useState(0)
  const [isPlaying, setIsPlaying] = useState(true)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  // Memoizar os dados combinados
  const combinedData = useMemo(() => ({
    ...mockData,
    ...data
  }), [data])

  // Memoizar os slides
  const slides = useMemo<DashboardSlide[]>(() => [
    {
      id: "kpis",
      title: "Indicadores Principais",
      component: KPISlide,
      icon: BarChart3,
      duration: 8
    },
    {
      id: "departments",
      title: "Performance por Departamento",
      component: DepartmentSlide,
      icon: Users,
      duration: 8
    },
    {
      id: "alerts",
      title: "Alertas e Status",
      component: AlertsSlide,
      icon: AlertTriangle,
      duration: 6
    }
  ], [])

  // Funções de navegação memoizadas
  const nextSlide = useCallback(() => {
    setCurrentSlide(prev => (prev + 1) % slides.length)
  }, [slides.length])

  const prevSlide = useCallback(() => {
    setCurrentSlide(prev => (prev - 1 + slides.length) % slides.length)
  }, [slides.length])

  const goToSlide = useCallback((index: number) => {
    setCurrentSlide(index)
  }, [])

  const togglePlayPause = useCallback(() => {
    setIsPlaying(prev => !prev)
  }, [])

  // Auto-advance slides
  useEffect(() => {
    if (!isActive || !isPlaying) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      return
    }

    const currentSlideDuration = slides[currentSlide]?.duration || 5
    intervalRef.current = setInterval(nextSlide, currentSlideDuration * 1000)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [isActive, isPlaying, currentSlide, slides, nextSlide])

  // Keyboard controls
  useEffect(() => {
    if (!isActive) return

    const handleKeyPress = (event: KeyboardEvent) => {
      switch (event.key) {
        case 'ArrowLeft':
          event.preventDefault()
          prevSlide()
          break
        case 'ArrowRight':
        case ' ':
          event.preventDefault()
          nextSlide()
          break
        case 'Escape':
          event.preventDefault()
          onToggle()
          break
        case 'p':
        case 'P':
          event.preventDefault()
          togglePlayPause()
          break
      }
    }

    document.addEventListener('keydown', handleKeyPress)
    return () => document.removeEventListener('keydown', handleKeyPress)
  }, [isActive, nextSlide, prevSlide, onToggle, togglePlayPause])

  // Progress calculation
  const progress = useMemo(() =>
    ((currentSlide + 1) / slides.length) * 100,
    [currentSlide, slides.length]
  )

  if (!isActive) return null

  const CurrentSlideComponent = slides[currentSlide]?.component

  return (
    <div className="fixed inset-0 bg-lia-bg-primary dark:bg-lia-bg-primary z-50 flex flex-col">
      {/* Header Controls */}
      <div className="flex items-center justify-between p-4 bg-lia-bg-tertiary dark:bg-lia-bg-secondary border-b">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggle}
            className="gap-2 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
            Sair do Modo Apresentação
          </Button>

          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={prevSlide}
              disabled={currentSlide === 0}
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>

            <span className="text-sm font-medium text-lia-text-secondary">
              {currentSlide + 1} / {slides.length}
            </span>

            <Button
              variant="ghost"
              size="sm"
              onClick={nextSlide}
              disabled={currentSlide === slides.length - 1}
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-lg font-semibold text-lia-text-primary">
            {slides[currentSlide]?.title}
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={togglePlayPause}
            className="gap-2 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
          >
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            {isPlaying ? "Pausar" : "Play"}
          </Button>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="h-1 bg-lia-interactive-active dark:bg-lia-bg-elevated">
        <div
          className="h-full bg-lia-bg-inverse transition-[width,height] duration-300"
          style={{width: `${progress}%`}}
        />
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {CurrentSlideComponent && (
          <CurrentSlideComponent data={combinedData} />
        )}
      </div>

      {/* Footer Navigation */}
      <div className="p-4 bg-lia-bg-tertiary dark:bg-lia-bg-secondary border-t">
        <div className="flex items-center justify-center gap-2">
          {slides.map((slide, index) => (
            <Button
              key={slide.id}
              variant={currentSlide === index ? "primary" : "ghost"}
              size="sm"
              onClick={() => goToSlide(index)}
              className="gap-2 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
            >
              <slide.icon className="w-4 h-4" />
              {slide.title}
            </Button>
          ))}
        </div>
      </div>
    </div>
  )
}
