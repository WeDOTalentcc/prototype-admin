"use client"

import { useTranslations } from "next-intl"
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
  const t = useTranslations('candidates')
  const cf = crossTabFilter as { type?: string; company?: string; companies?: string[]; filter?: string }
  if (!showCrossTabBanner || !crossTabFilter) return null

  return (
    <Card data-testid="cross-tab-filter-banner" className="bg-lia-bg-secondary dark:bg-lia-bg-secondary">
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-lia-btn-primary-bg dark:bg-lia-bg-tertiary rounded-xl flex items-center justify-center">
            {cf.type === 'company' ? (
              <Building className="w-5 h-5 text-white" />
            ) : (
              <Target className="w-5 h-5 text-white" />
            )}
          </div>
          <div className="flex-1">
            <h3 className="font-medium text-lia-text-primary mb-1">
              {t('crossTabBanner.filterApplied')} {cf.type === 'company' ? t('crossTabBanner.company') : t('crossTabBanner.competitiveIntelligence')}
            </h3>
            <p className="text-sm text-lia-text-primary mb-3" aria-live="polite" aria-atomic="true">
              {cf.type === 'company' && cf.company && (
                <span>{t('crossTabBanner.showingCompany', { company: cf.company })}</span>
              )}
              {cf.type === 'company' && cf.companies && (
                <span>{t('crossTabBanner.showingCompanies', { companies: cf.companies.join(', ') })}</span>
              )}
              {cf.filter === 'discontented_talents' && (
                <span>{t('crossTabBanner.discontentedTalents')}</span>
              )}
            </p>
            <div className="flex gap-2">
              <Button
                data-testid="clear-cross-tab-filter-btn"
                variant="outline"
                size="sm"
                onClick={clearCrossTabFilter}
              >
                <X className="w-3 h-3 mr-1" />
                {t('crossTabBanner.clearFilter')}
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
