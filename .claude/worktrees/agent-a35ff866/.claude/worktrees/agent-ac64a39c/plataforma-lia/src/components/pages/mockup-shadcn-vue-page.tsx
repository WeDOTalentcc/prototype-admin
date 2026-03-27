"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  Brain, 
  TrendingUp, 
  Users, 
  Target, 
  ArrowRight,
  Info,
  CheckCircle2,
  AlertCircle,
  BarChart3
} from "lucide-react"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Legend } from 'recharts'
import { Line as ChartJSLine } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip as ChartJSTooltip,
  Legend as ChartJSLegend,
  Filler
} from 'chart.js'

// Registrar componentes Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  ChartJSTooltip,
  ChartJSLegend,
  Filler
)

// Dados de exemplo para os gráficos
const chartData = [
  { mes: 'Jan', candidatos: 120, contratacoes: 8, notaLIA: 7.2 },
  { mes: 'Fev', candidatos: 145, contratacoes: 10, notaLIA: 7.5 },
  { mes: 'Mar', candidatos: 168, contratacoes: 12, notaLIA: 7.8 },
  { mes: 'Abr', candidatos: 190, contratacoes: 14, notaLIA: 8.1 },
  { mes: 'Mai', candidatos: 210, contratacoes: 15, notaLIA: 8.3 },
  { mes: 'Jun', candidatos: 234, contratacoes: 18, notaLIA: 8.4 },
]

export function MockupShadcnVuePage() {
  const [activeView, setActiveView] = useState<'atual' | 'otimizada'>('atual')

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-950 dark:text-gray-50 font-sans">
            🔬 Mockup shadcn-vue
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Comparação: Versão Atual vs Versão Otimizada para shadcn-vue
          </p>
        </div>
      </div>

      {/* Info Alert */}
      <Card className="border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-800">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
 <Info className="w-5 h-5 text-gray-600 flex-shrink-0 mt-0.5" />
            <div className="space-y-2 text-sm">
 <p className="text-wedo-cyan-dark dark:text-gray-400 font-medium">
                Esta página demonstra as otimizações propostas para facilitar a migração para Vue.js + shadcn-vue
              </p>
 <ul className="space-y-1 text-gray-600/80 text-xs">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3 h-3" />
                  <span><strong>Versão Atual:</strong> React + Recharts + Framer Motion</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3 h-3" />
                  <span><strong>Versão Otimizada:</strong> React + Chart.js + CSS Animations (compatível com Vue)</span>
                </li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Toggle Tabs */}
      <Tabs value={activeView} onValueChange={(v) => setActiveView(v as 'atual' | 'otimizada')} className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="atual" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Versão Atual
          </TabsTrigger>
          <TabsTrigger value="otimizada" className="flex items-center gap-2">
            <Brain className="w-4 h-4 text-wedo-cyan" />
            Versão Otimizada
          </TabsTrigger>
        </TabsList>

        {/* Versão Atual */}
        <TabsContent value="atual" className="mt-6 space-y-6">
          <DashboardVersaoAtual />
        </TabsContent>

        {/* Versão Otimizada */}
        <TabsContent value="otimizada" className="mt-6 space-y-6">
          <DashboardVersaoOtimizada />
        </TabsContent>
      </Tabs>
    </div>
  )
}

function DashboardVersaoAtual() {
  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-950 dark:text-gray-50 font-sans flex items-center gap-2">
            <Brain className="w-5 h-5 text-wedo-cyan" />
            Dashboard Previsões & IA
          </h2>
          <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
            Versão Atual: React + Recharts + Framer Motion
          </p>
        </div>
        <div className="flex gap-2">
          <Badge variant="outline" className="text-[11px]">React-only</Badge>
          <Badge variant="outline" className="text-[11px]">Recharts</Badge>
          <Badge variant="outline" className="text-[11px]">Framer Motion</Badge>
        </div>
      </div>

      {/* KPIs Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KPICard 
          icon={<Users className="w-4 h-4" />}
          title="Candidatos Analisados"
          value="1,234"
          change="+12%"
          trend="up"
          description="vs mês anterior"
        />
        <KPICard 
          icon={<Target className="w-4 h-4" />}
          title="Taxa de Sucesso"
          value="87%"
          change="+5%"
          trend="up"
          description="previsão LIA"
        />
        <KPICard 
          icon={<TrendingUp className="w-4 h-4" />}
          title="Contratações"
          value="45"
          change="+18%"
          trend="up"
          description="este mês"
        />
        <KPICard 
          icon={<Brain className="w-4 h-4 text-wedo-cyan" />}
          title="Nota LIA Média"
          value="8.4"
          change="+0.3"
          trend="up"
          description="qualidade geral"
        />
      </div>

      {/* Gráfico Recharts */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              Tendências de Recrutamento (Recharts)
            </CardTitle>
            <div className="flex gap-2">
              <Badge variant="outline" className="text-[11px] bg-orange-50 dark:bg-orange-950 text-orange-700 dark:text-orange-300 border-orange-300 dark:border-orange-700">
                React-only
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
                <XAxis 
                  dataKey="mes" 
                  className="text-xs"
                  tick={{ fontSize: 11 }}
                />
                <YAxis 
                  className="text-xs"
                  tick={{ fontSize: 11 }}
                />
                <RechartsTooltip 
                  contentStyle={{
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    fontSize: '12px'
                  }}
                />
                <Legend 
                  wrapperStyle={{ fontSize: '11px' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="candidatos" 
                  stroke="#374151" 
                  strokeWidth={2}
                  name="Candidatos"
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
                <Line 
                  type="monotone" 
                  dataKey="contratacoes" 
                  stroke="#10b981" 
                  strokeWidth={2}
                  name="Contratações"
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function DashboardVersaoOtimizada() {
  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-950 dark:text-gray-50 font-sans flex items-center gap-2">
            <Brain className="w-5 h-5 text-wedo-cyan" />
            Dashboard Previsões & IA
          </h2>
          <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
            Versão Otimizada: React + Chart.js + CSS Animations (compatível Vue)
          </p>
        </div>
        <div className="flex gap-2">
          <Badge className="text-[11px] bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100">
            ✓ Vue-compatible
          </Badge>
          <Badge className="text-[11px] bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100">
            Chart.js
          </Badge>
          <Badge className="text-[11px] bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100">
            CSS Animations
          </Badge>
        </div>
      </div>

      {/* Animation Explanation Card */}
      <Card className="border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-950/30">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Brain className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
            <div className="space-y-2 text-sm">
              <p className="text-green-900 dark:text-green-100 font-medium">
                Animações CSS @keyframes substituindo Framer Motion
              </p>
              <ul className="space-y-1 text-green-800 dark:text-green-200 text-xs">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-3 h-3 flex-shrink-0 mt-0.5" />
                  <span><strong>slideInUp:</strong> Cards entram com fade-in de baixo para cima (substitui motion.div initial/animate)</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-3 h-3 flex-shrink-0 mt-0.5" />
                  <span><strong>pulse:</strong> Ícones pulsam ao hover (substitui whileHover do Framer)</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-3 h-3 flex-shrink-0 mt-0.5" />
                  <span><strong>fadeIn:</strong> Elementos aparecem gradualmente (substitui AnimatePresence)</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-3 h-3 flex-shrink-0 mt-0.5" />
                  <span><strong>CSS transitions:</strong> Hover effects suaves com cubic-bezier (substitui transition do Framer)</span>
                </li>
              </ul>
              <p className="text-[11px] text-green-700 dark:text-green-300 italic mt-2">
                💡 Passe o mouse sobre os cards KPIs abaixo para ver as animações em ação!
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* KPIs Row - mesmos dados, animações CSS */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KPICardOptimized 
          icon={<Users className="w-4 h-4" />}
          title="Candidatos Analisados"
          value="1,234"
          change="+12%"
          trend="up"
          description="vs mês anterior"
        />
        <KPICardOptimized 
          icon={<Target className="w-4 h-4" />}
          title="Taxa de Sucesso"
          value="87%"
          change="+5%"
          trend="up"
          description="previsão LIA"
        />
        <KPICardOptimized 
          icon={<TrendingUp className="w-4 h-4" />}
          title="Contratações"
          value="45"
          change="+18%"
          trend="up"
          description="este mês"
        />
        <KPICardOptimized 
          icon={<Brain className="w-4 h-4 text-wedo-cyan" />}
          title="Nota LIA Média"
          value="8.4"
          change="+0.3"
          trend="up"
          description="qualidade geral"
        />
      </div>

      {/* Gráfico Chart.js */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm flex items-center gap-2">
              <Brain className="w-4 h-4 text-green-600 dark:text-green-400" />
              Tendências de Recrutamento (Chart.js)
            </CardTitle>
            <div className="flex gap-2">
              <Badge className="text-[11px] bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100 border-green-300 dark:border-green-700">
                ✓ Vue-compatible
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-[300px]">
            <ChartJSLine
              data={{
                labels: chartData.map(d => d.mes),
                datasets: [
                  {
                    label: 'Candidatos',
                    data: chartData.map(d => d.candidatos),
                    backgroundColor: 'rgba(229, 231, 235, 0.3)',
                    borderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    tension: 0.3,
                  },
                  {
                    label: 'Contratações',
                    data: chartData.map(d => d.contratacoes),
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    tension: 0.3,
                  },
                ],
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    display: true,
                    position: 'top' as const,
                    labels: {
                      font: { size: 11 },
                      usePointStyle: true,
                    },
                  },
                  tooltip: {
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    titleColor: '#111827',
                    bodyColor: '#111827',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true,
                    bodyFont: { size: 12 },
                  },
                },
                scales: {
                  x: {
                    grid: {
                      display: true,
                      color: 'rgba(0, 0, 0, 0.05)',
                    },
                    ticks: {
                      font: { size: 11 },
                    },
                  },
                  y: {
                    grid: {
                      display: true,
                      color: 'rgba(0, 0, 0, 0.05)',
                    },
                    ticks: {
                      font: { size: 11 },
                    },
                  },
                },
              }}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// KPI Card - Versão Atual (com placeholder para Framer Motion)
function KPICard({ 
  icon, 
  title, 
  value, 
  change, 
  trend, 
  description 
}: { 
  icon: React.ReactNode
  title: string
  value: string
  change: string
  trend: 'up' | 'down'
  description: string
}) {
  return (
    <Card className="hover:transition-shadow duration-200">
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-2">
          <div className="text-gray-600 dark:text-gray-400">
            {icon}
          </div>
          <Badge 
            variant="outline" 
            className={`text-[11px] ${
              trend === 'up' 
                ? 'text-green-600 dark:text-green-400 border-green-600 dark:border-green-400' 
                : 'text-red-600 dark:text-red-400 border-red-600 dark:border-red-400'
            }`}
          >
            {change}
          </Badge>
        </div>
        <div className="space-y-1">
          <div className="text-2xl font-bold text-gray-950 dark:text-gray-50">
            {value}
          </div>
          <div className="text-xs text-gray-600 dark:text-gray-400 font-medium">
            {title}
          </div>
          <div className="text-[11px] text-gray-500 dark:text-gray-500">
            {description}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// KPI Card - Versão Otimizada (CSS animations com @keyframes)
function KPICardOptimized({ 
  icon, 
  title, 
  value, 
  change, 
  trend, 
  description 
}: { 
  icon: React.ReactNode
  title: string
  value: string
  change: string
  trend: 'up' | 'down'
  description: string
}) {
  return (
    <>
      <style jsx>{`
        @keyframes slideInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        @keyframes pulse {
          0%, 100% {
            transform: scale(1);
          }
          50% {
            transform: scale(1.05);
          }
        }
        
        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }
        
        .kpi-card-optimized {
          animation: slideInUp 0.5s ease-out;
        }
        
        .kpi-card-optimized:hover {
          box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
          transform: translateY(-4px);
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .kpi-icon-optimized {
          animation: fadeIn 0.6s ease-in;
        }
        
        .kpi-icon-optimized:hover {
          animation: pulse 1s ease-in-out;
        }
        
        .kpi-value-optimized {
          animation: fadeIn 0.8s ease-in;
        }
        
        .kpi-badge-optimized {
          animation: slideInUp 0.7s ease-out;
          transition: all 0.3s ease;
        }
        
        .kpi-badge-optimized:hover {
          transform: scale(1.1);
        }
      `}</style>
      <Card className="kpi-card-optimized">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="text-gray-600 dark:text-gray-400 kpi-icon-optimized">
              {icon}
            </div>
            <Badge 
              variant="outline" 
              className={`text-[11px] kpi-badge-optimized ${
                trend === 'up' 
                  ? 'text-green-600 dark:text-green-400 border-green-600 dark:border-green-400 hover:bg-green-50 dark:hover:bg-green-950' 
                  : 'text-red-600 dark:text-red-400 border-red-600 dark:border-red-400 hover:bg-red-50 dark:hover:bg-red-950'
              }`}
            >
              {change}
            </Badge>
          </div>
          <div className="space-y-1">
            <div className="text-2xl font-bold text-gray-950 dark:text-gray-50 kpi-value-optimized">
              {value}
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400 font-medium">
              {title}
            </div>
            <div className="text-[11px] text-gray-500 dark:text-gray-500">
              {description}
            </div>
          </div>
        </CardContent>
      </Card>
    </>
  )
}
