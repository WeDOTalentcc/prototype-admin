import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
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
  Users, TrendingUp, UserCheck, Clock, Trophy, Medal,
  Filter, ChevronDown, ChevronUp, Eye, Settings, AlertTriangle,
  BarChart3, Layout, Target, Edit, Plus, LineChart,
  Calendar as CalendarIcon,
} from "lucide-react"
import type { RecruiterData, ViewMode, TeamMetrics, ActiveTab } from "../indicators.types"

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

function getRankingIcon(ranking: number) {
  switch (ranking) {
    case 1:
      return <Trophy className="w-5 h-5 text-status-warning" />
    case 2:
      return <Medal className="w-5 h-5 text-lia-text-secondary" />
    case 3:
      return <Medal className="w-5 h-5 text-status-warning" />
    default:
      return (
        <div className="w-5 h-5 flex items-center justify-center text-sm font-bold text-lia-text-primary dark:text-lia-text-primary">
          {ranking}
        </div>
      )
  }
}

const VIEW_MODES = [
  { id: "cards" as ViewMode, label: "Cards Individuais", icon: Layout },
  { id: "ranking" as ViewMode, label: "Ranking Geral", icon: Trophy },
  { id: "goals" as ViewMode, label: "Metas e Objetivos", icon: Target },
  { id: "comparison" as ViewMode, label: "Comparação", icon: BarChart3 },
]

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
    <div className="space-y-6">
      {/* Filtros Avançados */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
              Filtros Avançados
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
              className="gap-2"
            >
              {showAdvancedFilters ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
              {showAdvancedFilters ? "Ocultar" : "Expandir"}
            </Button>
          </div>
        </CardHeader>
        {showAdvancedFilters && (
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {/* Período */}
              <div>
                <label className="text-sm font-medium mb-2 block text-lia-text-primary dark:text-lia-text-primary">
                  Período
                </label>
                <select
                  value={selectedPeriod}
                  onChange={(e) => setSelectedPeriod(e.target.value)}
                  className="w-full p-2 rounded-md text-sm bg-gray-50 focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 text-lia-text-primary dark:text-lia-text-primary"
                >
                  <option value="current_month">Este Mês</option>
                  <option value="last_month">Mês Passado</option>
                  <option value="quarter">Este Trimestre</option>
                  <option value="year">Este Ano</option>
                </select>
              </div>

              {/* Departamentos */}
              <div>
                <label className="text-sm font-medium mb-2 block text-lia-text-primary dark:text-lia-text-primary">
                  Departamentos
                </label>
                <div className="space-y-2">
                  {departments.map((dept) => (
                    <label key={dept} className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={selectedDepartments.includes(dept)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedDepartments([...selectedDepartments, dept])
                          } else {
                            setSelectedDepartments(selectedDepartments.filter((d) => d !== dept))
                          }
                        }}
                        className="rounded-md"
                      />
                      {dept}
                    </label>
                  ))}
                </div>
              </div>

              {/* Ordenação */}
              <div>
                <label className="text-sm font-medium mb-2 block text-lia-text-primary dark:text-lia-text-primary">
                  Ordenar por
                </label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="w-full p-2 rounded-md text-sm mb-2 bg-gray-50 focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 text-lia-text-primary dark:text-lia-text-primary"
                >
                  <option value="totalScore">Score Total</option>
                  <option value="npsScore">NPS</option>
                  <option value="conversionRate">Taxa Conversão</option>
                  <option value="avgTimeToFill">Time to Fill</option>
                  <option value="totalHires">Total Contratações</option>
                </select>
                <select
                  value={sortOrder}
                  onChange={(e) => setSortOrder(e.target.value as "asc" | "desc")}
                  className="w-full p-2 rounded-md text-sm bg-gray-50 focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 text-lia-text-primary dark:text-lia-text-primary"
                >
                  <option value="desc">Maior para Menor</option>
                  <option value="asc">Menor para Maior</option>
                </select>
              </div>

              {/* Ações Rápidas */}
              <div>
                <label className="text-sm font-medium mb-2 block text-lia-text-primary dark:text-lia-text-primary">
                  Ações Rápidas
                </label>
                <div className="space-y-2">
                  <Button variant="outline" size="sm" className="w-full gap-2">
                    <Eye className="w-3 h-3" />
                    Ver Top Performers
                  </Button>
                  <Button variant="outline" size="sm" className="w-full gap-2">
                    <AlertTriangle className="w-3 h-3" />
                    Alertas de Performance
                  </Button>
                </div>
              </div>
            </div>

            {/* Badges de Filtros Aplicados */}
            {(selectedDepartments.length > 0 || selectedRecruiters.length > 0) && (
              <div className="flex flex-wrap gap-2 pt-4 border-t">
                {selectedDepartments.map((dept) => (
                  <Badge key={dept} variant="outline" className="gap-1">
                    {dept}
                    <button
                      onClick={() =>
                        setSelectedDepartments(selectedDepartments.filter((d) => d !== dept))
                      }
                      className="ml-1 hover:text-status-error"
                    >
                      ×
                    </button>
                  </Badge>
                ))}
                {selectedRecruiters.map((name) => (
                  <Badge key={name} variant="outline" className="gap-1">
                    {name}
                    <button
                      onClick={() =>
                        setSelectedRecruiters(selectedRecruiters.filter((n) => n !== name))
                      }
                      className="ml-1 hover:text-status-error"
                    >
                      ×
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        )}
      </Card>

      {/* Métricas Consolidadas da Equipe */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-lia-border-default dark:border-lia-border-default">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary font-medium">
                  Total Recrutadores
                </p>
                <p className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">
                  {teamMetrics.totalRecruiters}
                </p>
              </div>
              <Users className="w-8 h-8 text-lia-text-secondary dark:text-lia-text-tertiary" />
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
                <p className="text-2xl font-bold text-status-success">{teamMetrics.totalHires}</p>
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
                <p className="text-sm text-wedo-purple font-medium">NPS Médio</p>
                <p className="text-2xl font-bold text-wedo-purple">{teamMetrics.avgNPS}%</p>
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
                <p className="text-sm text-wedo-orange font-medium">Time to Fill Médio</p>
                <p className="text-2xl font-bold text-wedo-orange">{teamMetrics.avgTimeToFill}d</p>
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

      {/* Modos de Visualização */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Modos de Visualização</CardTitle>
            <div className="flex gap-2">
              {VIEW_MODES.map((mode) => (
                <Button
                  key={mode.id}
                  variant={viewMode === mode.id ? "default" : "outline"}
                  size="sm"
                  onClick={() => setViewMode(mode.id)}
                  className="gap-2"
                >
                  <mode.icon className="w-4 h-4" />
                  {mode.label}
                </Button>
              ))}
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Alertas Rápidos */}
      <Card className="border-l-4 border-l-orange-500">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-wedo-orange" />
            Alertas Rápidos
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-status-error/10 rounded-md">
              <div className="text-2xl font-bold text-status-error">2</div>
              <div className="text-sm text-status-error">Alertas Críticos</div>
              <div className="text-xs text-status-error mt-1">Time to Fill &gt; 45 dias</div>
            </div>
            <div className="text-center p-4 bg-status-warning/10 rounded-md">
              <div className="text-2xl font-bold text-status-warning">5</div>
              <div className="text-sm text-status-warning">Avisos</div>
              <div className="text-xs text-status-warning mt-1">NPS abaixo da meta</div>
            </div>
            <div className="text-center p-4 bg-gray-100 dark:bg-lia-bg-secondary rounded-md">
              <div className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">
                12
              </div>
              <div className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                Monitoramentos
              </div>
              <div className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary mt-1">
                KPIs em observação
              </div>
            </div>
          </div>
          <div className="mt-4">
            <Button
              variant="outline"
              className="w-full gap-2"
              onClick={() => setActiveTab("alerts")}
            >
              <AlertTriangle className="w-4 h-4" />
              Ver Todos os Alertas
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Gráficos Avançados de Performance */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RecruiterPerformanceRadar />
        <RecruitmentTrendsChart />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DetailedFunnelChart />
        <SourceEffectivenessChart />
      </div>

      {/* Cards Individuais */}
      {viewMode === "cards" && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
          {filteredRecruiters.map((recruiter) => (
            <Card key={recruiter.name} className="relative">
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Avatar className="w-12 h-12">
                      <AvatarImage src={recruiter.avatar} alt={recruiter.name} />
                      <AvatarFallback className="bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-secondary font-medium">
                        {recruiter.name
                          .split(" ")
                          .map((n) => n[0])
                          .join("")}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-lia-text-primary dark:text-lia-text-primary">
                          {recruiter.name}
                        </h3>
                        {getRankingIcon(recruiter.ranking)}
                      </div>
                      <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                        {recruiter.role}
                      </p>
                      <Badge variant="outline" className="mt-1 text-xs">
                        {recruiter.department}
                      </Badge>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">
                      {recruiter.totalScore}
                    </div>
                    <div className="text-xs text-lia-text-primary dark:text-lia-text-primary">
                      Score Total
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* KPIs Principais */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md">
                    <div className="text-lg font-bold text-lia-text-primary dark:text-lia-text-primary">
                      {recruiter.totalHires}
                    </div>
                    <div className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                      Contratações
                    </div>
                  </div>
                  <div className="text-center p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md">
                    <div className="text-lg font-bold text-lia-text-primary dark:text-lia-text-primary">
                      {recruiter.avgTimeToFill}d
                    </div>
                    <div className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                      Time to Fill
                    </div>
                  </div>
                  <div className="text-center p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md">
                    <div className="text-lg font-bold text-lia-text-primary dark:text-lia-text-primary">
                      {recruiter.npsScore}%
                    </div>
                    <div className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                      NPS Score
                    </div>
                  </div>
                  <div className="text-center p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md">
                    <div className="text-lg font-bold text-lia-text-primary dark:text-lia-text-primary">
                      {recruiter.conversionRate}%
                    </div>
                    <div className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                      Conversão
                    </div>
                  </div>
                </div>

                {/* Metas Mensais */}
                <div>
                  <h4 className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary mb-2">
                    Metas Mensais
                  </h4>
                  <div className="space-y-2">
                    {Object.entries(recruiter.goals.monthly).map(([key, goal]) => (
                      <div key={key} className="flex items-center justify-between text-sm">
                        <span className="text-lia-text-secondary dark:text-lia-text-tertiary capitalize">
                          {key === "hires"
                            ? "Contratações"
                            : key === "timeToFill"
                            ? "Time to Fill"
                            : key === "nps"
                            ? "NPS"
                            : "Entrevistas"}
                          :
                        </span>
                        <div className="flex items-center gap-2">
                          <span className="text-lia-text-primary dark:text-lia-text-primary">
                            {goal.current}/{goal.target}
                          </span>
                          <Badge className={`text-xs ${getStatusColor(goal.status)}`}>
                            {goal.status === "exceeded"
                              ? "Superou"
                              : goal.status === "achieved"
                              ? "Atingiu"
                              : goal.status === "on_track"
                              ? "No prazo"
                              : "Atrasado"}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Distribuição de Sourcing */}
                <div>
                  <h4 className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary mb-2">
                    Fontes de Candidatos
                  </h4>
                  <div className="grid grid-cols-4 gap-2 text-xs">
                    <div className="text-center">
                      <div className="font-medium text-lia-text-secondary dark:text-lia-text-tertiary">
                        {recruiter.sourcing.linkedin}%
                      </div>
                      <div className="text-lia-text-primary dark:text-lia-text-primary">LinkedIn</div>
                    </div>
                    <div className="text-center">
                      <div className="font-medium text-status-success">
                        {recruiter.sourcing.referrals}%
                      </div>
                      <div className="text-lia-text-primary dark:text-lia-text-primary">Indicações</div>
                    </div>
                    <div className="text-center">
                      <div className="font-medium text-wedo-orange">
                        {recruiter.sourcing.jobBoards}%
                      </div>
                      <div className="text-lia-text-primary dark:text-lia-text-primary">Job Boards</div>
                    </div>
                    <div className="text-center">
                      <div className="font-medium text-wedo-purple">
                        {recruiter.sourcing.headhunting}%
                      </div>
                      <div className="text-lia-text-primary dark:text-lia-text-primary">Headhunt</div>
                    </div>
                  </div>
                </div>

                {/* Ações */}
                <div className="flex gap-2 pt-2 border-t">
                  <Button variant="outline" size="sm" className="flex-1 gap-2">
                    <Eye className="w-3 h-3" />
                    Ver Detalhes
                  </Button>
                  <Button variant="outline" size="sm" className="gap-2">
                    <Settings className="w-3 h-3" />
                    Metas
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Ranking */}
      {viewMode === "ranking" && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Trophy className="w-5 h-5 text-status-warning" />
              Ranking Geral dos Recrutadores
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {filteredRecruiters.map((recruiter, index) => (
                <div
                  key={recruiter.name}
                  className={`flex items-center gap-4 p-4 rounded-md border ${
                    index === 0
                      ? "bg-status-warning/10 border-status-warning/30"
                      : index === 1
                      ? "bg-gray-50 border-lia-border-subtle"
                      : index === 2
                      ? "bg-status-warning/10 border-status-warning/30"
                      : "bg-lia-bg-primary border-lia-border-subtle"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {getRankingIcon(recruiter.ranking)}
                    <Avatar className="w-10 h-10">
                      <AvatarImage src={recruiter.avatar} alt={recruiter.name} />
                      <AvatarFallback className="bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-secondary font-medium">
                        {recruiter.name
                          .split(" ")
                          .map((n) => n[0])
                          .join("")}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <div className="font-semibold text-lia-text-primary dark:text-lia-text-primary">
                        {recruiter.name}
                      </div>
                      <div className="text-sm text-lia-text-secondary">
                        {recruiter.role} • {recruiter.department}
                      </div>
                    </div>
                  </div>

                  <div className="flex-1 grid grid-cols-5 gap-4 text-center">
                    <div>
                      <div className="text-lg font-bold text-lia-text-primary dark:text-lia-text-primary">
                        {recruiter.totalScore}
                      </div>
                      <div className="text-xs text-lia-text-primary dark:text-lia-text-primary">
                        Score Total
                      </div>
                    </div>
                    <div>
                      <div className="text-lg font-bold text-status-success">
                        {recruiter.totalHires}
                      </div>
                      <div className="text-xs text-lia-text-primary dark:text-lia-text-primary">
                        Contratações
                      </div>
                    </div>
                    <div>
                      <div className="text-lg font-bold text-wedo-purple">
                        {recruiter.avgTimeToFill}d
                      </div>
                      <div className="text-xs text-lia-text-primary dark:text-lia-text-primary">
                        Time to Fill
                      </div>
                    </div>
                    <div>
                      <div className="text-lg font-bold text-wedo-orange">{recruiter.npsScore}%</div>
                      <div className="text-xs text-lia-text-primary dark:text-lia-text-primary">NPS</div>
                    </div>
                    <div>
                      <div className="text-lg font-bold text-status-error">
                        {recruiter.conversionRate}%
                      </div>
                      <div className="text-xs text-lia-text-primary dark:text-lia-text-primary">
                        Conversão
                      </div>
                    </div>
                  </div>

                  <div className="text-right">
                    {index < 3 && (
                      <Badge
                        className={
                          index === 0
                            ? "bg-status-warning/15 text-status-warning"
                            : index === 1
                            ? "bg-gray-100 text-lia-text-primary"
                            : "bg-status-warning/15 text-status-warning"
                        }
                      >
                        #{recruiter.ranking}
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Metas e Objetivos */}
      {viewMode === "goals" && (
        <div className="space-y-6">
          {filteredRecruiters.map((recruiter) => (
            <Card key={recruiter.name}>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <Avatar className="w-10 h-10">
                    <AvatarImage src={recruiter.avatar} alt={recruiter.name} />
                    <AvatarFallback className="bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-secondary font-medium">
                      {recruiter.name
                        .split(" ")
                        .map((n) => n[0])
                        .join("")}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <CardTitle>{recruiter.name}</CardTitle>
                    <p className="text-sm text-lia-text-secondary">
                      {recruiter.role} • {recruiter.department}
                    </p>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Metas Mensais */}
                  <div>
                    <h4 className="font-medium text-lia-text-primary dark:text-lia-text-primary mb-4 flex items-center gap-2">
                      <CalendarIcon className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                      Metas Mensais
                    </h4>
                    <div className="space-y-4">
                      {Object.entries(recruiter.goals.monthly).map(([key, goal]) => (
                        <div key={key} className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="font-medium capitalize">
                              {key === "hires"
                                ? "Contratações"
                                : key === "timeToFill"
                                ? "Time to Fill (dias)"
                                : key === "nps"
                                ? "NPS Score"
                                : "Entrevistas"}
                            </span>
                            <div className="flex items-center gap-2">
                              <span className="text-lia-text-primary dark:text-lia-text-primary">
                                {goal.current}/{goal.target}
                              </span>
                              <Badge className={`text-xs ${getStatusColor(goal.status)}`}>
                                {goal.status === "exceeded"
                                  ? "Superou"
                                  : goal.status === "achieved"
                                  ? "Atingiu"
                                  : goal.status === "on_track"
                                  ? "No prazo"
                                  : "Atrasado"}
                              </Badge>
                            </div>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full transition-[width,height] duration-300 ${
                                goal.status === "exceeded"
                                  ? "bg-status-success"
                                  : goal.status === "achieved"
                                  ? "bg-wedo-cyan"
                                  : goal.status === "on_track"
                                  ? "bg-status-warning"
                                  : "bg-status-error"
                              }`}
                              style={{
                                width: `${Math.min((goal.current / goal.target) * 100, 100)}%`,
                              }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Metas Trimestrais */}
                  <div>
                    <h4 className="font-medium text-lia-text-primary dark:text-lia-text-primary mb-4 flex items-center gap-2">
                      <Target className="w-4 h-4 text-wedo-purple" />
                      Metas Trimestrais
                    </h4>
                    <div className="space-y-4">
                      {Object.entries(recruiter.goals.quarterly).map(([key, goal]) => (
                        <div key={key} className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="font-medium capitalize">
                              {key === "qualityScore"
                                ? "Score de Qualidade"
                                : "Taxa de Conversão (%)"}
                            </span>
                            <div className="flex items-center gap-2">
                              <span className="text-lia-text-primary dark:text-lia-text-primary">
                                {goal.current}/{goal.target}
                              </span>
                              <Badge className={`text-xs ${getStatusColor(goal.status)}`}>
                                {goal.status === "exceeded"
                                  ? "Superou"
                                  : goal.status === "achieved"
                                  ? "Atingiu"
                                  : goal.status === "on_track"
                                  ? "No prazo"
                                  : "Atrasado"}
                              </Badge>
                            </div>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full transition-[width,height] duration-300 ${
                                goal.status === "exceeded"
                                  ? "bg-status-success"
                                  : goal.status === "achieved"
                                  ? "bg-wedo-cyan"
                                  : goal.status === "on_track"
                                  ? "bg-status-warning"
                                  : "bg-status-error"
                              }`}
                              style={{
                                width: `${Math.min((goal.current / goal.target) * 100, 100)}%`,
                              }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Ações para Metas */}
                <div className="flex gap-2 mt-6 pt-4 border-t">
                  <Button variant="outline" size="sm" className="gap-2">
                    <Edit className="w-3 h-3" />
                    Editar Metas
                  </Button>
                  <Button variant="outline" size="sm" className="gap-2">
                    <Plus className="w-3 h-3" />
                    Nova Meta
                  </Button>
                  <Button variant="outline" size="sm" className="gap-2">
                    <BarChart3 className="w-3 h-3" />
                    Ver Histórico
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Comparação */}
      {viewMode === "comparison" && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-wedo-purple" />
              Comparação de Performance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium text-lia-text-primary dark:text-lia-text-primary mb-4">
                    Contratações por Recrutador
                  </h4>
                  <div className="space-y-3">
                    {filteredRecruiters.map((recruiter) => (
                      <div key={recruiter.name} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Avatar className="w-6 h-6">
                            <AvatarFallback className="bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-secondary text-xs">
                              {recruiter.name
                                .split(" ")
                                .map((n) => n[0])
                                .join("")}
                            </AvatarFallback>
                          </Avatar>
                          <span className="text-sm">{recruiter.name}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-20 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-gray-700 dark:bg-lia-text-tertiary h-2 rounded-full"
                              style={{
                                width: `${
                                  (recruiter.totalHires /
                                    Math.max(...filteredRecruiters.map((r) => r.totalHires))) *
                                  100
                                }%`,
                              }}
                            />
                          </div>
                          <span className="text-sm font-medium w-8 text-right">
                            {recruiter.totalHires}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-lia-text-primary dark:text-lia-text-primary mb-4">
                    NPS Score por Recrutador
                  </h4>
                  <div className="space-y-3">
                    {filteredRecruiters.map((recruiter) => (
                      <div key={recruiter.name} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Avatar className="w-6 h-6">
                            <AvatarFallback className="bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-secondary text-xs">
                              {recruiter.name
                                .split(" ")
                                .map((n) => n[0])
                                .join("")}
                            </AvatarFallback>
                          </Avatar>
                          <span className="text-sm">{recruiter.name}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-20 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-status-success h-2 rounded-full"
                              style={{ width: `${recruiter.npsScore}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium w-8 text-right">
                            {recruiter.npsScore}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Gráfico de Tendências */}
              <div>
                <h4 className="font-medium text-lia-text-primary dark:text-lia-text-primary mb-4">
                  Tendências de Performance (Últimos 6 Meses)
                </h4>
                <div className="bg-gray-50 p-6 rounded-md text-center">
                  <LineChart className="w-12 h-12 text-lia-text-secondary mx-auto mb-2" />
                  <p className="text-lia-text-secondary text-sm">
                    Gráfico interativo de tendências seria exibido aqui
                  </p>
                  <p className="text-xs text-lia-text-primary dark:text-lia-text-primary mt-1">
                    Mostrando evolução de KPIs, sazonalidades e comparações
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
