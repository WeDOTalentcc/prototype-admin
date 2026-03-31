// @ts-nocheck
"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Building, Target, X } from "lucide-react"

interface CrossTabFilterBannerProps {
  showCrossTabBanner: boolean
  crossTabFilter: Record<string, unknown>
  clearCrossTabFilter: () => void
}

export function CrossTabFilterBanner({
  showCrossTabBanner,
  crossTabFilter,
  clearCrossTabFilter,
}: CrossTabFilterBannerProps) {
  if (!showCrossTabBanner || !crossTabFilter) return null

  return (
    <Card className="bg-gray-50 dark:bg-lia-bg-secondary">
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gray-900 dark:bg-gray-100 rounded-md flex items-center justify-center">
            {crossTabFilter.type === company ? (
              <Building className="w-5 h-5 text-white dark:text-lia-text-disabled" />
            ) : (
              <Target className="w-5 h-5 text-white dark:text-lia-text-disabled" />
            )}
          </div>
          <div className="flex-1">
            <h3 className="font-medium text-lia-text-primary dark:text-lia-text-primary mb-1">
              🎯 Filtro Aplicado: {crossTabFilter.type === company ? Empresa : Inteligência Competitiva}
            </h3>
            <p className="text-sm text-lia-text-primary dark:text-lia-text-tertiary mb-3" aria-live="polite" aria-atomic="true">
              {crossTabFilter.type === company && crossTabFilter.company && (
                
              )}
              {crossTabFilter.type === company && crossTabFilter.companies && (
                
              )}
              {crossTabFilter.filter === discontented_talents && (
                
              )}
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={clearCrossTabFilter}
              >
                <X className="w-3 h-3 mr-1" />
                Limpar Filtro
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
