import { Card, CardContent, CardHeader } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import { Eye, Settings } from"lucide-react"
import type { RecruiterData } from"../indicators.types"
import { getRankingIcon, getGoalLabel, getGoalStatusLabel, getInitials } from"./recruiters-tab.utils"

interface RecruiterCardViewProps {
  filteredRecruiters: RecruiterData[]
  getStatusColor: (status: string) => string
}

export function RecruiterCardView({ filteredRecruiters, getStatusColor }: RecruiterCardViewProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
      {filteredRecruiters.map((recruiter) => (
        <Card key={recruiter.name} className="relative">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Avatar className="w-12 h-12">
                  <AvatarImage src={recruiter.avatar} alt={recruiter.name} />
                  <AvatarFallback className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary font-medium">
                    {getInitials(recruiter.name)}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-lia-text-primary">
                      {recruiter.name}
                    </h3>
                    {getRankingIcon(recruiter.ranking)}
                  </div>
                  <p className="text-sm text-lia-text-secondary">
                    {recruiter.role}
                  </p>
                  <Chip density="relaxed" variant="neutral" className="mt-1">
                    {recruiter.department}
                  </Chip>
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-semibold text-lia-text-primary">
                  {recruiter.totalScore}
                </div>
                <div className="text-xs text-lia-text-primary">
                  Score Total
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
                <div className="text-lg font-semibold text-lia-text-primary">
                  {recruiter.totalHires}
                </div>
                <div className="text-xs text-lia-text-secondary">
                  Contratações
                </div>
              </div>
              <div className="text-center p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
                <div className="text-lg font-semibold text-lia-text-primary">
                  {recruiter.avgTimeToFill}d
                </div>
                <div className="text-xs text-lia-text-secondary">
                  Tempo de Preenchimento
                </div>
              </div>
              <div className="text-center p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
                <div className="text-lg font-semibold text-lia-text-primary">
                  {recruiter.npsScore}%
                </div>
                <div className="text-xs text-lia-text-secondary">
                  NPS Score
                </div>
              </div>
              <div className="text-center p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
                <div className="text-lg font-semibold text-lia-text-primary">
                  {recruiter.conversionRate}%
                </div>
                <div className="text-xs text-lia-text-secondary">
                  Conversão
                </div>
              </div>
            </div>

            <div>
              <h4 className="text-sm font-medium text-lia-text-primary mb-2">
                Metas Mensais
              </h4>
              <div className="space-y-2">
                {Object.entries(recruiter.goals.monthly).map(([key, goal]) => (
                  <div key={key} className="flex items-center justify-between text-sm">
                    <span className="text-lia-text-secondary capitalize">
                      {getGoalLabel(key)}:
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="text-lia-text-primary">
                        {goal.current}/{goal.target}
                      </span>
                      <Chip variant="neutral" muted className={`text-xs ${getStatusColor(goal.status)}`}>
                        {getGoalStatusLabel(goal.status)}
                      </Chip>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h4 className="text-sm font-medium text-lia-text-primary mb-2">
                Fontes de Candidatos
              </h4>
              <div className="grid grid-cols-4 gap-2 text-xs">
                <div className="text-center">
                  <div className="font-medium text-lia-text-secondary">
                    {recruiter.sourcing.linkedin}%
                  </div>
                  <div className="text-lia-text-primary">LinkedIn</div>
                </div>
                <div className="text-center">
                  <div className="font-medium text-status-success">
                    {recruiter.sourcing.referrals}%
                  </div>
                  <div className="text-lia-text-primary">Indicações</div>
                </div>
                <div className="text-center">
                  <div className="font-medium text-wedo-orange-text">
                    {recruiter.sourcing.jobBoards}%
                  </div>
                  <div className="text-lia-text-primary">Job Boards</div>
                </div>
                <div className="text-center">
                  <div className="font-medium text-lia-text-secondary">
                    {recruiter.sourcing.headhunting}%
                  </div>
                  <div className="text-lia-text-primary">Headhunt</div>
                </div>
              </div>
            </div>

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
  )
}
