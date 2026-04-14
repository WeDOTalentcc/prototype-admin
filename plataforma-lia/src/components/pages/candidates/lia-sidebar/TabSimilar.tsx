"use client"
import React, { useState } from "react"
import { useTranslations } from "next-intl"
import { Users, Loader2, Lightbulb } from "lucide-react"
import { Button } from "@/components/ui/button"
import { type ChatMessage, type SearchResults } from "./lia-sidebar-types"
import { mapApiCandidates } from "./mapCandidates"
import { type ApiCandidate } from "./lia-sidebar-types"

interface TabSimilarProps {
  searchSource: string
  pearchSearchOptions: { searchType: string }
  setChatMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>
  setSearchResults: React.Dispatch<React.SetStateAction<SearchResults>>
  setCandidates: (v: unknown[]) => void
  setHasSearchResults: (v: boolean) => void
  setSearchResultsCount: (v: number) => void
  setLocalResultsCount: (v: number) => void
  setPearchResultsCount: (v: number) => void
  setShowSearchResults: (v: boolean) => void
  setDisplayedResultsCount: (v: number) => void
}

export const TabSimilar = React.memo(function TabSimilar({
  searchSource,
  pearchSearchOptions,
  setChatMessages,
  setSearchResults,
  setCandidates,
  setHasSearchResults,
  setSearchResultsCount,
  setLocalResultsCount,
  setPearchResultsCount,
  setShowSearchResults,
  setDisplayedResultsCount,
}: TabSimilarProps) {
  const t = useTranslations('candidates.liaSidebar')
  const [similarProfileUrl, setSimilarProfileUrl] = useState("")
  const [isSearchingSimilar, setIsSearchingSimilar] = useState(false)

  const handleSearch = async () => {
    if (!similarProfileUrl.trim() || isSearchingSimilar) return
    setIsSearchingSimilar(true)
    const isLinkedInUrl = similarProfileUrl.includes('linkedin.com/in/')
    const userMsg: ChatMessage = {
      id: `user-similar-${Date.now()}`, type: 'user', timestamp: new Date(),
      content: isLinkedInUrl
        ? t('searchSimilarUrl', { url: similarProfileUrl })
        : t('searchSimilarGeneric', { input: similarProfileUrl })
    }
    setChatMessages(prev => [...prev, userMsg])
    try {
      const requestBody: { linkedin_url?: string; candidate_id?: string; limit: number; search_pearch: boolean; pearch_type: string } = {
        limit: 20, search_pearch: searchSource !== 'local', pearch_type: pearchSearchOptions.searchType
      }
      if (isLinkedInUrl) { requestBody.linkedin_url = similarProfileUrl.trim() }
      else { requestBody.candidate_id = similarProfileUrl.trim() }

      const response = await fetch('/api/backend-proxy/search/candidates/similar', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      })
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || t('searchError'))
      }
      const data = await response.json()
      if (data.candidates && data.candidates.length > 0) {
        const mapped = mapApiCandidates(data.candidates as ApiCandidate[], 'similar')
        const local = mapped.filter(c => c.source === 'local')
        const global = mapped.filter(c => c.source === 'pearch')
        const showGlobal = searchSource === 'global' || searchSource === 'hybrid'
        setCandidates(showGlobal ? mapped : local)
        setHasSearchResults(true); setShowSearchResults(true); setDisplayedResultsCount(10)
        setSearchResultsCount(data.total_count || mapped.length)
        setLocalResultsCount(data.local_count || local.length)
        setPearchResultsCount(data.pearch_count || global.length)
        setSearchResults(prev => ({ local, global, localCount: data.local_count || local.length,
          globalCount: data.pearch_count || global.length, query: data.query_generated || 'Similar Search',
          isLoading: false, showGlobalResults: showGlobal, globalDismissed: prev.globalDismissed,
          isEnrichingContacts: prev.isEnrichingContacts }))
        const refInfo = data.reference_profile
          ? t('referenceProfile', { name: data.reference_profile.name || data.reference_profile.linkedin_url || 'ID: ' + data.reference_profile.id })
          : ''
        const localCount = data.local_count || local.length
        setChatMessages(prev => [...prev, {
          id: `lia-similar-result-${Date.now()}`, type: 'lia', timestamp: new Date(),
          content: t('similarSearchComplete', { refInfo, query: data.query_generated, count: localCount }),
          searchResults: { localCount, globalCount: 0, query: data.query_generated || '' }
        }])
      } else {
        setChatMessages(prev => [...prev, { id: `lia-similar-noresult-${Date.now()}`, type: 'lia', timestamp: new Date(),
          content: t('similarNoResults') }])
      }
    } catch (error: unknown) {
      setChatMessages(prev => [...prev, { id: `lia-similar-error-${Date.now()}`, type: 'lia', timestamp: new Date(),
        content: t('similarError', { error: error instanceof Error ? error.message : t('similarErrorDefault') }) }])
    } finally { setIsSearchingSimilar(false) }
  }

  return (
    <div data-testid="tab-similar" className="space-y-4 overflow-y-auto flex-1 p-4">
      <p className="text-xs text-lia-text-tertiary" aria-live="polite" aria-atomic="true">
        {t('similarDescription')}
      </p>
      <div className="relative">
        <input
          type="text"
          value={similarProfileUrl}
          onChange={(e) => setSimilarProfileUrl(e.target.value)}
          placeholder={t('similarPlaceholder')}
          className="w-full p-3 text-xs rounded-xl border focus:outline-none transition-colors motion-reduce:transition-none bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary border border-lia-border-subtle"
        />
      </div>
      <div className="p-2.5 rounded-xl bg-white border border-lia-border-subtle">
        <div className="flex items-start gap-2">
          <Lightbulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
          <p className="text-xs text-lia-text-secondary">
            <strong>{t('booleanTipLabel')}</strong> {t('similarTip')}
          </p>
        </div>
      </div>
      <Button
        className={`w-full h-11 !text-sm font-semibold text-white font-open-sans ${isSearchingSimilar ? 'bg-lia-border-medium' : 'bg-wedo-cyan-dark'}`}
        onClick={handleSearch}
        disabled={!similarProfileUrl.trim() || isSearchingSimilar}
      >
        {isSearchingSimilar ? (
          <><Loader2 className="w-4 h-4 mr-2 animate-spin motion-reduce:animate-none" />{t('searching')}</>
        ) : (
          <><Users className="w-4 h-4 mr-2" />{t('findSimilar')}</>
        )}
      </Button>
    </div>
  )
})

TabSimilar.displayName = "TabSimilar"
