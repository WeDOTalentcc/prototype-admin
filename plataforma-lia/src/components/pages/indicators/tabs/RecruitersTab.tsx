import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  RecruiterPerformanceChart,
} from "@/components/charts/interactive-charts"
import {
  RecruitmentTrendsChart,
  RecruiterPerformanceRadar,
  DetailedFunnelChart,
  SourceEffectivenessChart,
} from "@/components/charts/advanced-interactive-charts"
import {
  Users, TrendingUp, UserCheck, Clock, Trophy, AlertTriangle,
} from "lucide-react"
import type { RecruiterData, ViewMode, TeamMetrics, ActiveTab } from "../indicators.types"
import { VIEW_MODES } from "./recruiters-tab.utils"
import { RecruiterFilters } from "./RecruiterFilters"
import { RecruiterCardView } from "./RecruiterCardView"
import { RecruiterGoalsView } from "./RecruiterGoalsView"
import { RecruiterRankingView, RecruiterComparisonView } from "./RecruiterRankingComparisonView"

interface RecruitersTabProps {
  recruiters: RecruiterData[]
  filteredRecruiters: RecruiterData[]
  departments: string[]
  teamMetrics: TeamMetrics
  selectedPeriod: string
  setSelectedPeriod: (v: string) => void
  selectedDepartments: string[]
  setSelectedDepartments: (v: string[]) => void
  selectedRecruiters: string[]
  setSelectedRecruiters: (v: string[]) => void
  showAdvancedFilters: boolean
  setShowAdvancedFilters: (v: boolean) => void
  viewMode: ViewMode
  setViewMode: (v: ViewMode) => void
  sortBy: string
  setSortBy: (v: string) => void
  sortOrder: "asc" | "desc"
  setSortOrder: (v: "asc" | "desc") => void
  getStatusColor: (status: string) => string
  setActiveTab: (tab: ActiveTab) => void
}

export function RecruitersTab({
  recruiters,
  filteredRecruiters,
  departments,
  teamMetrics,
  selectedPeriod,
  setSelectedPeriod,
  selectedDepartments,
  setSelectedDepartments,
  selectedRecruiters,
  setSelectedRecruiters,
  showAdvancedFilters,
  setShowAdvancedFilters,
  viewMode,
  setViewMode,
  sortBy,
  setSortBy,
  sortOrder,
  setSortOrder,
  getStatusColor,
  setActiveTab,
}: RecruitersTabProps) {
  return (
    <div className="space-y-6" data-testid="recruiters-tab">
      <RecruiterFilters
        departments={departments}
        selectedPeriod={selectedPeriod}
        setSelectedPeriod={setSelectedPeriod}
        selectedDepartments={selectedDepartments}
        setSelectedDepartments={setSelectedDepartments}
        selectedRecruiters={selectedRecruiters}
        setSelectedRecruiters={setSelectedRecruiters}
        showAdvancedFilters={showAdvancedFilters}
        setShowAdvancedFilters={setShowAdvancedFilters}
        sortBy={sortBy}
        setSortBy={setSortBy}
        sortOrder={sortOrder}
        setSortOrder={setSortOrder}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-lia-border-default dark:border-lia-border-default">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-lia-text-secondary font-medium">
                  Total Recrutadores
                </p>
                <p className="text-2xl font-semibold text-lia-text-primary">
                  {teamMetrics.totalRecruiters}
                </p>
              </div>
              <Users className="w-8 h-8 text-lia-text-secondary" />
            </div>
            <div className="mt-2 flex items-center gap-1 text-xs">
              <TrendingUp className="w-3 h-3 text-status-success" />
              <span className="text-status-success">+12% vs mês anterior</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-status-success/30 dark:border-status-success/30">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-status-success font-medium">Contratações Total</p>
                <p className="text-2xl font-semibold text-status-success">{teamMetrics.totalHires}</p>
              </div>
              <UserCheck className="w-8 h-8 text-status-success" />
            </div>
            <div className="mt-2 flex items-center gap-1 text-xs">
              <TrendingUp className="w-3 h-3 text-status-success" />
              <span className="text-status-success">+5% vs trimestre</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-wedo-purple/30">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-wedo-purple-text font-medium">NPS Médio</p>
                <p className="text-2xl font-semibold text-wedo-purple-text">{teamMetrics.avgNPS}%</p>
              </div>
              <Trophy className="w-8 h-8 text-wedo-purple" />
            </div>
            <div className="mt-2 flex items-center gap-1 text-xs">
              <TrendingUp className="w-3 h-3 text-status-success" />
              <span className="text-status-success">+2pt vs mês anterior</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-wedo-orange/30">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-wedo-orange-text font-medium">Tempo de Preenchimento Médio</p>
                <p className="text-2xl font-semibold text-wedo-orange-text">{teamMetrics.avgTimeToFill}d</p>
              </div>
              <Clock className="w-8 h-8 text-wedo-orange" />
            </div>
            <div className="mt-2 flex items-center gap-1 text-xs">
              <TrendingUp className="w-3 h-3 text-status-success" />
              <span className="text-status-success">-3d vs trimestre</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Modos de Visualização</CardTitle>
            <div className="flex gap-2">
              {VIEW_MODES.map((mode) => (
                <Button
                  key={mode.id}
                  variant={viewMode === mode.id ? "primary" : "outline"}
                  size="sm"
                  onClick={() => setViewMode(mode.id)}
                  className="gap-2 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
                >
                  <mode.icon className="w-4 h-4" />
                  {mode.label}
                </Button>
              ))}
            </div>
          </div>
        </CardHeader>
      </Card>

      <Card className="border-l-4 border-l-orange-500">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-wedo-orange" />
            Alertas Rápidos
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-status-error/10 rounded-xl">
              <div className="text-2xl font-semibold text-status-error">2</div>
              <div className="text-sm text-status-error">Alertas Críticos</div>
              <div className="text-xs text-status-error mt-1">Tempo de Preenchimento &gt; 45 dias</div>
            </div>
            <div className="text-center p-4 bg-status-warning/10 rounded-xl">
              <div className="text-2xl font-semibold text-status-warning">5</div>
              <div className="text-sm text-status-warning">Avisos</div>
              <div className="text-xs text-status-warning mt-1">NPS abaixo da meta</div>
            </div>
            <div className="text-center p-4 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl">
              <div className="text-2xl font-semibold text-lia-text-primary">
                12
              </div>
              <div className="text-sm text-lia-text-secondary">
                Monitoramentos
              </div>
              <div className="text-xs text-lia-text-secondary mt-1">
                KPIs em observação
              </div>
            </div>
          </div>
          <div className="mt-4">
            <Button
              variant="outline"
              className="w-full gap-2 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
              onClick={() => setActiveTab("alerts")}
            >
              <AlertTriangle className="w-4 h-4" />
              Ver Todos os Alertas
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RecruiterPerformanceRadar />
        <RecruitmentTrendsChart />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DetailedFunnelChart />
        <SourceEffectivenessChart />
      </div>

      {viewMode === "cards" && (
        <RecruiterCardView
          filteredRecruiters={filteredRecruiters}
          getStatusColor={getStatusColor}
        />
      )}

      {viewMode === "ranking" && (
        <RecruiterRankingView filteredRecruiters={filteredRecruiters} />
      )}

      {viewMode === "goals" && (
        <RecruiterGoalsView
          filteredRecruiters={filteredRecruiters}
          getStatusColor={getStatusColor}
        />
      )}

      {viewMode === "comparison" && (
        <RecruiterComparisonView filteredRecruiters={filteredRecruiters} />
      )}
    </div>
  )
}
