"use client"

import React from "react"
import { LucideIcon } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export interface ServiceItem {
  icon: LucideIcon
  iconColor?: string
  title: string
  subtitle: string
  value?: string
  badge?: string
  trend?: string
  trendDirection?: "up" | "down" | "neutral"
}

export interface ServiceConsumptionProps {
  title?: string
  items: ServiceItem[]
}

export function ServiceConsumption({
  title = "Consumo de Serviços",
  items,
}: ServiceConsumptionProps) {
  const getTrendColor = (direction?: "up" | "down" | "neutral") => {
    switch (direction) {
      case "up":
        return "text-status-error"
      case "down":
        return "text-status-success"
      default:
        return "lia-text-secondary"
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {items.map((item, index) => {
          const Icon = item.icon
          return (
            <div key={item.title} className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Icon className="w-5 h-5" style={{color: item.iconColor}} />
                <div>
                  <p className="text-sm font-medium text-lia-text-primary">
                    {item.title}
                  </p>
                  <p className="text-xs text-lia-text-disabled">
                    {item.subtitle}
                  </p>
                </div>
              </div>
              <div className="text-right">
                {item.value && (
                  <p className="text-sm font-semibold text-lia-text-primary">
                    {item.value}
                  </p>
                )}
                {item.trend && (
                  <p className={`text-xs ${getTrendColor(item.trendDirection)}`}>
                    {item.trend}
                  </p>
                )}
                {item.badge && (
                  <Badge variant="outline" className="text-xs">
                    {item.badge}
                  </Badge>
                )}
              </div>
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}
