import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import {
  Edit, Plus, BarChart3, Target,
  Calendar as CalendarIcon,
} from"lucide-react"
import type { RecruiterData } from"../indicators.types"
import { getGoalLabel, getGoalStatusLabel, getGoalStatusBarColor, getInitials } from"./recruiters-tab.utils"

interface RecruiterGoalsViewProps {
  filteredRecruiters: RecruiterData[]
  getStatusColor: (status: string) => string
}

export function RecruiterGoalsView({ filteredRecruiters, getStatusColor }: RecruiterGoalsViewProps) {
  return (
    <div className="space-y-6">
      {filteredRecruiters.map((recruiter) => (
        <Card key={recruiter.name}>
          <CardHeader>
            <div className="flex items-center gap-3">
              <Avatar className="w-10 h-10">
                <AvatarImage src={recruiter.avatar} alt={recruiter.name} />
                <AvatarFallback className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary font-medium">
                  {getInitials(recruiter.name)}
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
              <div>
                <h4 className="font-medium text-lia-text-primary mb-4 flex items-center gap-2">
                  <CalendarIcon className="w-4 h-4 text-lia-text-secondary" />
                  Metas Mensais
                </h4>
                <div className="space-y-4">
                  {Object.entries(recruiter.goals.monthly).map(([key, goal]) => (
                    <div key={key} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium capitalize">
                          {getGoalLabel(key,"long")}
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
                      <div className="w-full bg-lia-interactive-active rounded-full h-2">
                        <div
                          className={`h-2 rounded-full transition-[width,height] duration-300 ${getGoalStatusBarColor(goal.status)}`}
                          style={{
                            width: `${Math.min((goal.current / goal.target) * 100, 100)}%`,
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="font-medium text-lia-text-primary mb-4 flex items-center gap-2">
                  <Target className="w-4 h-4 text-wedo-purple" />
                  Metas Trimestrais
                </h4>
                <div className="space-y-4">
                  {Object.entries(recruiter.goals.quarterly).map(([key, goal]) => (
                    <div key={key} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium capitalize">
                          {getGoalLabel(key,"long")}
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
                      <div className="w-full bg-lia-interactive-active rounded-full h-2">
                        <div
                          className={`h-2 rounded-full transition-[width,height] duration-300 ${getGoalStatusBarColor(goal.status)}`}
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
  )
}
