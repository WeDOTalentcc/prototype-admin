"use client"
import React, { useState } from "react"
import { Brain, Loader2, Paperclip, Mic } from "lucide-react"
import { type ChatMessage, type SearchResults } from "./lia-sidebar-types"
import { mapApiCandidates } from "./mapCandidates"
import { type ApiCandidate } from "./lia-sidebar-types"

interface TabJobDescriptionProps {
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

export const TabJobDescription = React.memo(function TabJobDescription({
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
}: TabJobDescriptionProps) {
  const [jobDescriptionText, setJobDescriptionText] = useState("")
  const [isSearchingJD, setIsSearchingJD] = useState(false)
  const [extractedJDCriteria, setExtractedJDCriteria] = useState<{
    job_title?: string; seniority?: string; skills: string[]
    experience_years?: number; location?: string; languages: string[]
  } | null>(null)

  const handleSearch = async () => {
    if (!jobDescriptionText.trim() || isSearchingJD) return
    setIsSearchingJD(true)
    setExtractedJDCriteria(null)
    const userMsg: ChatMessage = {
      id: `user-jd-${Date.now()}`, type: 'user', timestamp: new Date(),
      content: `Buscar candidatos pela descri\u00e7\u00e3o da vaga:\n\n"${jobDescriptionText.substring(0, 200)}${jobDescriptionText.length > 200 ? '...' : ''}"`
    }
    setChatMessages(prev => [...prev, userMsg])
    try {
      const response = await fetch('/api/backend-proxy/search/candidates/by-job-description', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_description: jobDescriptionText.trim(), limit: 20,
          search_pearch: searchSource !== 'local', pearch_type: pearchSearchOptions.searchType })
      })
      if (!response.ok) throw new Error('Erro na busca')
      const data = await response.json()
      if (data.extracted_criteria) {
        setExtractedJDCriteria({
          job_title: data.extracted_criteria.job_title, seniority: data.extracted_criteria.seniority,
          skills: data.extracted_criteria.skills || [], experience_years: data.extracted_criteria.experience_years,
          location: data.extracted_criteria.location, languages: data.extracted_criteria.languages || []
        })
      }
      if (data.candidates && data.candidates.length > 0) {
        const mapped = mapApiCandidates(data.candidates as ApiCandidate[], 'jd')
        const local = mapped.filter(c => c.source === 'local')
        const global = mapped.filter(c => c.source === 'pearch')
        const showGlobal = searchSource === 'global' || searchSource === 'hybrid'
        setCandidates(showGlobal ? mapped : local)
        setHasSearchResults(true); setShowSearchResults(true); setDisplayedResultsCount(10)
        setSearchResultsCount(data.total_count || mapped.length)
        setLocalResultsCount(data.local_count || local.length)
        setPearchResultsCount(data.pearch_count || global.length)
        setSearchResults(prev => ({ local, global, localCount: data.local_count || local.length,
          globalCount: data.pearch_count || global.length, query: data.query_generated || jobDescriptionText.substring(0, 50),
          isLoading: false, showGlobalResults: showGlobal, globalDismissed: prev.globalDismissed }))
        const localCount = data.local_count || local.length
        setChatMessages(prev => [...prev, {
          id: `lia-jd-result-${Date.now()}`, type: 'lia', timestamp: new Date(),
          content: `**Busca por Job Description conclu\u00edda!**\n\nQuery gerada: "${data.query_generated}"\n\nEncontrei **${localCount} candidato${localCount > 1 ? 's' : ''}** na sua base local.`,
          searchResults: { localCount, globalCount: 0, query: data.query_generated || '' }
        }])
      } else {
        setChatMessages(prev => [...prev, { id: `lia-jd-noresult-${Date.now()}`, type: 'lia', timestamp: new Date(),
          content: `N\u00e3o encontrei candidatos com os crit\u00e9rios extra\u00eddos da descri\u00e7\u00e3o da vaga.\n\nTente ajustar a descri\u00e7\u00e3o ou usar a busca por IA Natural com termos mais espec\u00edficos.` }])
      }
    } catch {
      setChatMessages(prev => [...prev, { id: `lia-jd-error-${Date.now()}`, type: 'lia', timestamp: new Date(),
        content: `Erro ao buscar candidatos pela descri\u00e7\u00e3o da vaga. Por favor, tente novamente.` }])
    } finally { setIsSearchingJD(false) }
  }

  return (
    <div className="space-y-4 overflow-y-auto flex-1 p-4">
      <p className="text-xs text-lia-text-tertiary" aria-live="polite" aria-atomic="true">
        Cole sua descri\u00e7\u00e3o de vaga e a IA extra\u00edr\u00e1 os crit\u00e9rios automaticamente
      </p>
      <div className="relative">
        <textarea
          placeholder="Cole aqui a descri\u00e7\u00e3o da vaga completa..."
          value={jobDescriptionText}
          onChange={(e) => setJobDescriptionText(e.target.value)}
          className="w-full h-48 p-4 pb-12 text-xs rounded-md border focus:outline-none transition-colors motion-reduce:transition-none resize-none bg-white dark:bg-lia-bg-secondary text-lia-text-primary dark:text-lia-text-primary border border-lia-border-subtle"
          onFocus={(e) => e.target.style.borderColor = 'var(--gray-200)'}
          onBlur={(e) => e.target.style.borderColor = 'var(--gray-50)'}
        />
        <div className="absolute bottom-3 right-3 flex gap-2">
          <button type="button" className="p-2 rounded-md hover:bg-gray-100 transition-colors motion-reduce:transition-none" title="Anexar documento" onClick={() => {}}>
            <Paperclip className="w-4 h-4 text-lia-text-primary" />
          </button>
          <button type="button" className="p-2 rounded-md hover:bg-gray-100 transition-colors motion-reduce:transition-none" title="Gravar \u00e1udio" onClick={() => {}}>
            <Mic className="w-4 h-4 text-lia-text-primary" />
          </button>
        </div>
      </div>
      {extractedJDCriteria && (
        <div className="p-3 rounded-md border bg-wedo-cyan/[0.06] border-wedo-cyan/30">
          <div className="flex items-center gap-2 mb-2">
            <Brain className="w-4 h-4 text-wedo-cyan" />
            <span className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary">Crit\u00e9rios Extra\u00eddos</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {extractedJDCriteria.job_title && <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-lia-text-secondary dark:bg-lia-bg-elevated dark:text-lia-text-secondary">{extractedJDCriteria.job_title}</span>}
            {extractedJDCriteria.seniority && <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-lia-text-secondary dark:bg-lia-bg-elevated dark:text-lia-text-secondary">{extractedJDCriteria.seniority}</span>}
            {extractedJDCriteria.skills.map((skill, idx) => <span key={idx} className="px-2 py-1 text-xs rounded-full bg-gray-100 text-lia-text-secondary dark:bg-lia-bg-elevated dark:text-lia-text-secondary">{skill}</span>)}
            {extractedJDCriteria.experience_years && <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-lia-text-secondary dark:bg-lia-bg-elevated dark:text-lia-text-secondary">{extractedJDCriteria.experience_years}+ anos</span>}
            {extractedJDCriteria.location && <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-lia-text-secondary dark:bg-lia-bg-elevated dark:text-lia-text-secondary">{extractedJDCriteria.location}</span>}
          </div>
        </div>
      )}
      <button
        className="w-full h-11 text-sm font-semibold flex items-center justify-center gap-2 rounded-md disabled:opacity-50"
        style={{backgroundColor: isSearchingJD ? 'var(--gray-400)' : 'var(--gray-950)', color: 'var(--gray-50)'}}
        onClick={handleSearch}
        disabled={!jobDescriptionText.trim() || jobDescriptionText.length < 50 || isSearchingJD}
      >
        {isSearchingJD ? (
          <><Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />Analisando...</>
        ) : (
          <><span className="flex items-center justify-center w-5 h-5 rounded-md bg-gray-900"><Brain className="w-3 h-3 text-white" /></span>Extrair e Buscar</>
        )}
      </button>
      {jobDescriptionText.length > 0 && jobDescriptionText.length < 50 && (
        <p className="text-xs text-status-warning">A descri\u00e7\u00e3o precisa ter pelo menos 50 caracteres para an\u00e1lise adequada.</p>
      )}
    </div>
  )
})

TabJobDescription.displayName = "TabJobDescription"
