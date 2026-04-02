"use client"
import { Card, CardContent } from "@/components/ui/card"
import { textStyles } from "@/lib/design-tokens"

interface GoalsStatsCardsProps {
  totalTemplates: number
  totalAssigned: number
  achieved: number
  inProgress: number
  overdue: number
}

export function GoalsStatsCards({
  totalTemplates, totalAssigned, achieved, inProgress, overdue
}: GoalsStatsCardsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
      <Card className="border border-lia-border-subtle dark:border-lia-border-strong">
        <CardContent className="p-3 text-center">
          <div className={`${textStyles.metricLarge} !text-lg`}>{totalTemplates}</div>
          <div className={textStyles.caption}>Templates</div>
        </CardContent>
      </Card>
      <Card className="border border-lia-border-subtle dark:border-lia-border-strong">
        <CardContent className="p-3 text-center">
          <div className={`${textStyles.metricLarge} !text-lg`}>{totalAssigned}</div>
          <div className={textStyles.caption}>Atribuídas</div>
        </CardContent>
      </Card>
      <Card className="border border-lia-border-subtle dark:border-lia-border-strong">
        <CardContent className="p-3 text-center">
          <div className={`${textStyles.metricLarge} !text-lg !text-status-success`}>{achieved}</div>
          <div className={textStyles.caption}>Atingidas</div>
        </CardContent>
      </Card>
      <Card className="border border-lia-border-subtle dark:border-lia-border-strong">
        <CardContent className="p-3 text-center">
          <div className={`${textStyles.metricLarge} !text-lg !text-status-warning`}>{inProgress}</div>
          <div className={textStyles.caption}>Em Progresso</div>
        </CardContent>
      </Card>
      <Card className="border border-lia-border-subtle dark:border-lia-border-strong">
        <CardContent className="p-3 text-center">
          <div className={`${textStyles.metricLarge} !text-lg !text-status-error`}>{overdue}</div>
          <div className={textStyles.caption}>Atrasadas</div>
        </CardContent>
      </Card>
    </div>
  )
}

GoalsStatsCards.displayName = "GoalsStatsCards"
