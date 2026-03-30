"use client"

import React from "react"
import { LucideIcon, CheckCircle, TrendingUp, AlertCircle, Database, Info } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export type ActivityType = "success" | "upgrade" | "warning" | "integration" | "info"

export interface Activity {
  type: ActivityType
  title: string
  subtitle: string
  timestamp?: string
  icon?: LucideIcon
}

export interface ActivityFeedProps {
  title?: string
  activities: Activity[]
}

const activityIcons: Record<ActivityType, { icon: LucideIcon; color: string }> = {
  success: { icon: CheckCircle, color: "text-status-success" },
  upgrade: { icon: TrendingUp, color: "text-gray-600 dark:text-lia-text-tertiary" },
  warning: { icon: AlertCircle, color: "text-wedo-orange" },
  integration: { icon: Database, color: "text-wedo-purple" },
  info: { icon: Info, color: "lia-text-base" },
}

export function ActivityFeed({
  title = "Atividades Recentes",
  activities,
}: ActivityFeedProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {activities.map((activity, index) => {
          const activityConfig = activityIcons[activity.type]
          const Icon = activity.icon || activityConfig.icon
          const iconColor = activityConfig.color

          return (
            <div key={index} className="flex items-start gap-3 text-sm">
              <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${iconColor}`} />
              <div>
                <p className="font-medium text-gray-800 dark:text-lia-text-primary">
                  {activity.title}
                </p>
                <p className="text-xs text-gray-400">
                  {activity.subtitle}
                  {activity.timestamp && ` • ${activity.timestamp}`}
                </p>
              </div>
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}
