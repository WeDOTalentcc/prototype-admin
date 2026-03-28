"use client"

import React from "react"
import { LucideIcon } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export interface QuickAction {
  href: string
  icon: LucideIcon
  iconColor?: string
  title: string
  subtitle: string
}

export interface QuickActionsProps {
  title?: string
  actions: QuickAction[]
  columns?: 1 | 2 | 3 | 4
}

export function QuickActions({
  title = "Ações Rápidas",
  actions,
  columns = 3,
}: QuickActionsProps) {
  const gridCols = {
    1: "grid-cols-1",
    2: "grid-cols-1 md:grid-cols-2",
    3: "grid-cols-1 md:grid-cols-3",
    4: "grid-cols-1 md:grid-cols-2 lg:grid-cols-4",
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className={`grid ${gridCols[columns]} gap-4`}>
          {actions.map((action, index) => {
            const Icon = action.icon
            return (
              <a
                key={index}
                href={action.href}
                className="flex items-center gap-3 p-4 rounded-md border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                <Icon 
                  className="w-5 h-5" 
                  style={{color: action.iconColor}}
                />
                <div>
                  <p className="text-sm font-medium text-gray-800 dark:text-gray-100">
                    {action.title}
                  </p>
                  <p className="text-xs text-gray-400 dark:text-gray-500">
                    {action.subtitle}
                  </p>
                </div>
              </a>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
