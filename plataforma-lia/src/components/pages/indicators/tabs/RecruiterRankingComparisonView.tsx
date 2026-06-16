import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import { Trophy, BarChart3, LineChart } from"lucide-react"
import type { RecruiterData } from"../indicators.types"
import { getRankingIcon, getInitials } from"./recruiters-tab.utils"

interface RecruiterRankingViewProps {
  filteredRecruiters: RecruiterData[]
}

export function RecruiterRankingView({ filteredRecruiters }: RecruiterRankingViewProps) {
  return (
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
                  ?"bg-status-warning/10 border-status-warning/30"
                  : index === 1
                  ?"bg-lia-bg-secondary border-lia-border-subtle"
                  : index === 2
                  ?"bg-status-warning/10 border-status-warning/30"
                  :"bg-lia-bg-primary border-lia-border-subtle"
              }`}
            >
              <div className="flex items-center gap-3">
                {getRankingIcon(recruiter.ranking)}
                <Avatar className="w-10 h-10">
                  <AvatarImage src={recruiter.avatar} alt={recruiter.name} />
                  <AvatarFallback className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary font-medium">
                    {getInitials(recruiter.name)}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <div className="font-semibold text-lia-text-primary">
                    {recruiter.name}
                  </div>
                  <div className="text-sm text-lia-text-secondary">
                    {recruiter.role} • {recruiter.department}
                  </div>
                </div>
              </div>

              <div className="flex-1 grid grid-cols-5 gap-4 text-center">
                <div>
                  <div className="text-lg font-semibold text-lia-text-primary">
                    {recruiter.totalScore}
                  </div>
                  <div className="text-xs text-lia-text-primary">
                    Score Total
                  </div>
                </div>
                <div>
                  <div className="text-lg font-semibold text-status-success">
                    {recruiter.totalHires}
                  </div>
                  <div className="text-xs text-lia-text-primary">
                    Contratações
                  </div>
                </div>
                <div>
                  <div className="text-lg font-semibold text-lia-text-secondary">
                    {recruiter.avgTimeToFill}d
                  </div>
                  <div className="text-xs text-lia-text-primary">
                    Tempo de Preenchimento
                  </div>
                </div>
                <div>
                  <div className="text-lg font-semibold text-wedo-orange-text">{recruiter.npsScore}%</div>
                  <div className="text-xs text-lia-text-primary">NPS</div>
                </div>
                <div>
                  <div className="text-lg font-semibold text-status-error">
                    {recruiter.conversionRate}%
                  </div>
                  <div className="text-xs text-lia-text-primary">
                    Conversão
                  </div>
                </div>
              </div>

              <div className="text-right">
                {index < 3 && (
                  <Chip variant="neutral" muted
                    className={
                      index === 0
                        ?""
                        : index === 1
                        ?"bg-lia-bg-tertiary text-lia-text-primary"
                        :""
                    }
                  >
                    #{recruiter.ranking}
                  </Chip>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

interface RecruiterComparisonViewProps {
  filteredRecruiters: RecruiterData[]
}

export function RecruiterComparisonView({ filteredRecruiters }: RecruiterComparisonViewProps) {
  return (
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
              <h4 className="font-medium text-lia-text-primary mb-4">
                Contratações por Recrutador
              </h4>
              <div className="space-y-3">
                {filteredRecruiters.map((recruiter) => (
                  <div key={recruiter.name} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Avatar className="w-6 h-6">
                        <AvatarFallback className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary text-xs">
                          {getInitials(recruiter.name)}
                        </AvatarFallback>
                      </Avatar>
                      <span className="text-sm">{recruiter.name}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-20 bg-lia-interactive-active rounded-full h-2">
                        <div
                          className="bg-lia-bg-inverse dark:bg-lia-text-tertiary h-2 rounded-full"
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
              <h4 className="font-medium text-lia-text-primary mb-4">
                NPS Score por Recrutador
              </h4>
              <div className="space-y-3">
                {filteredRecruiters.map((recruiter) => (
                  <div key={recruiter.name} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Avatar className="w-6 h-6">
                        <AvatarFallback className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary text-xs">
                          {getInitials(recruiter.name)}
                        </AvatarFallback>
                      </Avatar>
                      <span className="text-sm">{recruiter.name}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-20 bg-lia-interactive-active rounded-full h-2">
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

          <div>
            <h4 className="font-medium text-lia-text-primary mb-4">
              Tendências de Performance (Últimos 6 Meses)
            </h4>
            <div className="bg-lia-bg-secondary p-6 rounded-xl text-center">
              <LineChart className="w-12 h-12 text-lia-text-secondary mx-auto mb-2" />
              <p className="text-lia-text-secondary text-sm">
                Gráfico interativo de tendências seria exibido aqui
              </p>
              <p className="text-xs text-lia-text-primary mt-1">
                Mostrando evolução de KPIs, sazonalidades e comparações
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
