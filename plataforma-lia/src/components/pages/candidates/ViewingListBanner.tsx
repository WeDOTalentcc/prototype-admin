"use client"

import { useTranslations } from "next-intl"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { List, X, ArrowLeft } from "lucide-react"

interface ViewingListBannerProps {
  viewingList: { id: string; name: string; color?: string } | null
  candidates: Array<{ id: string }>
  setViewingList: (value: null) => void
  setShowSearchResults: (value: boolean) => void
  setSearchTerm: (value: string) => void
  setLastSearchQuery: (value: string) => void
  setActiveTab: (tab: string) => void
}

export function ViewingListBanner({
  viewingList,
  candidates,
  setViewingList,
  setShowSearchResults,
  setSearchTerm,
  setLastSearchQuery,
  setActiveTab,
}: ViewingListBannerProps) {
  const t = useTranslations('candidates')
  if (!viewingList) return null

  return (
    <Card data-testid="viewing-list-banner" className="bg-lia-bg-secondary dark:bg-lia-bg-secondary border-l-4" style={{borderLeftColor: viewingList.color || 'var(--lia-text-secondary)'}}>
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-md flex items-center justify-center"
            style={{backgroundColor: viewingList.color || 'var(--lia-text-secondary)'}}
          >
            <List className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1">
            <h3 className="font-medium text-lia-text-primary mb-1">
              {t('viewingListBanner.viewingList', { name: viewingList.name })}
            </h3>
            <p className="text-sm text-lia-text-primary" aria-live="polite" aria-atomic="true">
              {candidates.length === 1
                ? t('viewingListBanner.candidateInList', { count: candidates.length })
                : t('viewingListBanner.candidatesInList', { count: candidates.length })}
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setViewingList(null)
                setShowSearchResults(false)
                setSearchTerm('')
                setLastSearchQuery('')
              }}
            >
              <X className="w-3 h-3 mr-1" />
              {t('viewingListBanner.closeList')}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setActiveTab('lists')}
            >
              <ArrowLeft className="w-3 h-3 mr-1" />
              {t('viewingListBanner.backToLists')}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
