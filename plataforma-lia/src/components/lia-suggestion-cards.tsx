"use client"

import React from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Loader2, AlertTriangle, Clock, TrendingUp, Users, FileText, Search, Plus, Briefcase, RefreshCw } from "lucide-react"
import type { SuggestionCard } from "@/hooks/use-lia-suggestions"

interface LiaSuggestionCardsProps {
  suggestions: SuggestionCard[]
  loading: boolean
  onAction: (action: string, metadata?: Record<string, unknown>) => void
  onRefresh?: () => void
  className?: string
}

const ICON_MAP: Record<string, React.ReactNode> = {
  AlertTriangle: <AlertTriangle className="w-4 h-4" />,
  Clock: <Clock className="w-4 h-4" />,
  TrendingUp: <TrendingUp className="w-4 h-4" />,
  Users: <Users className="w-4 h-4" />,
  FileText: <FileText className="w-4 h-4" />,
  Search: <Search className="w-4 h-4" />,
  Plus: <Plus className="w-4 h-4" />,
  Briefcase: <Briefcase className="w-4 h-4" />,
}

const PRIORITY_STYLES: Record<string, { bg: string; border: string; iconBg: string }> = {
  high: {
    bg: "bg-red-50",
    border: "border-red-200 hover:border-red-300",
    iconBg: "bg-red-100 text-red-600",
  },
  medium: {
    bg: "bg-amber-50",
    border: "border-amber-200 hover:border-amber-300",
    iconBg: "bg-amber-100 text-amber-600",
  },
  low: {
    bg: "bg-gray-50",
    border: "border-gray-200 hover:border-gray-300",
    iconBg: "bg-gray-100 text-gray-600",
  },
}

const TYPE_BADGES: Record<string, { variant: string; label: string }> = {
  alert: { variant: "destructive", label: "Alerta" },
  warning: { variant: "warning", label: "Atenção" },
  insight: { variant: "secondary", label: "Insight" },
  info: { variant: "default", label: "Info" },
  action: { variant: "outline", label: "Ação" },
  suggestion: { variant: "outline", label: "Sugestão" },
}

export function LiaSuggestionCards({
  suggestions,
  loading,
  onAction,
  onRefresh,
  className = "",
}: LiaSuggestionCardsProps) {
  if (loading) {
    return (
      <div className={`flex items-center justify-center py-8 ${className}`}>
        <Loader2 className="w-5 h-5 animate-spin text-gray-600 dark:text-gray-400" />
        <span className="ml-2 text-xs text-gray-500">Carregando sugestões...</span>
      </div>
    )
  }

  if (suggestions.length === 0) {
    return (
      <div className={`text-center py-6 ${className}`}>
        <p className="text-xs text-gray-500">Nenhuma sugestão disponível no momento.</p>
        {onRefresh && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onRefresh}
            className="mt-2 text-xs text-gray-600 dark:text-gray-400 hover:text-wedo-cyan-dark"
          >
            <RefreshCw className="w-3 h-3 mr-1" />
            Atualizar
          </Button>
        )}
      </div>
    )
  }

  return (
    <div className={`space-y-2 ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wider">
          Sugestões da LIA
        </h4>
        {onRefresh && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onRefresh}
            className="h-6 px-2 text-micro text-gray-400 hover:text-gray-900 dark:hover:text-gray-50"
          >
            <RefreshCw className="w-3 h-3" />
          </Button>
        )}
      </div>
      
      <div className="grid gap-2">
        {suggestions.map((suggestion) => {
          const styles = PRIORITY_STYLES[suggestion.priority] || PRIORITY_STYLES.low
          const typeInfo = TYPE_BADGES[suggestion.type] || TYPE_BADGES.info
          const icon = ICON_MAP[suggestion.icon] || <Briefcase className="w-4 h-4" />

          return (
            <Card
              key={suggestion.id}
              className={`p-3 cursor-pointer transition-all ${styles.bg} border ${styles.border}`}
              onClick={() => onAction(suggestion.action, suggestion.metadata)}
            >
              <div className="flex items-start gap-3">
                <div className={`p-1.5 rounded-md ${styles.iconBg}`}>
                  {icon}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h5 className="text-xs font-medium text-gray-900 truncate">
                      {suggestion.title}
                    </h5>
                    <Badge 
                      variant="outline" 
                      className="text-micro px-1.5 py-0 h-4 shrink-0"
                    >
                      {typeInfo.label}
                    </Badge>
                  </div>
                  <p className="text-xs text-gray-600 line-clamp-2">
                    {suggestion.description}
                  </p>
                  <div className="flex items-center gap-2 mt-2">
                    <Badge 
                      variant="secondary" 
                      className="text-micro px-1.5 py-0 h-4 bg-gray-100 text-gray-600"
                    >
                      {suggestion.category}
                    </Badge>
                    {suggestion.metadata?.count && (
                      <span className="text-micro text-gray-400">
                        {suggestion.metadata.count as number} item(s)
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
