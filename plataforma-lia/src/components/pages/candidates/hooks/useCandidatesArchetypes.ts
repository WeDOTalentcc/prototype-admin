import { useState } from "react"
import { useTranslations } from "next-intl"
import type { Candidate } from "../types"
import type { ParsedEntities, SearchMode } from "@/components/search/smart-search-input"
import { toast } from "sonner"
import type { ChatMessage } from "./candidates-core"

export type Archetype = {
  id: string
  name: string
  description: string
  emoji: string
  query: string
  filters: {
    job_title?: string
    seniority?: string
    skills?: string[]
    location?: string
    experience_years?: number
  }
  tags?: string[]
  industry?: string
  createdAt: Date
  isDefault?: boolean
  usage_count?: number
}

export type BackendArchetype = {
  id: string
  name: string
  description?: string
  emoji: string
  query: string
  filters: Record<string, unknown>
  tags: string[]
  industry?: string
  seniority?: string
  is_default: boolean
  is_active: boolean
  usage_count: number
  created_at?: string
}

export type AISuggestion = {
  name: string
  description: string
  query: string
  filters: {
    job_title?: string
    seniority?: string
    skills?: string[]
    location?: string
  }
}

export interface UseCandidatesArchetypesParams {
  searchSource: string
  pearchSearchOptions: { searchType: string; limit: number }
  setCandidates: (candidates: Candidate[] | ((prev: Candidate[]) => Candidate[])) => void
  setHasSearchResults: (v: boolean) => void
  setSearchResultsCount: (v: number) => void
  setLocalResultsCount: (v: number) => void
  setPearchResultsCount: (v: number) => void
  setLastSearchQuery: (v: string) => void
  setLastSearchMode: (v: string) => void
  setActiveSearchTab: (v: string) => void
  setLiaPromptValue: (v: string) => void
  setChatMessages: (v: ChatMessage[] | ((prev: ChatMessage[]) => ChatMessage[])) => void
}

export function useCandidatesArchetypes(params: UseCandidatesArchetypesParams) {
  const {
    searchSource, pearchSearchOptions,
    setCandidates, setHasSearchResults, setSearchResultsCount,
    setLocalResultsCount, setPearchResultsCount,
    setLastSearchQuery, setLastSearchMode, setActiveSearchTab,
    setLiaPromptValue, setChatMessages,
  } = params

  const t = useTranslations('candidates.archetypes')
  const [backendArchetypes, setBackendArchetypes] = useState<BackendArchetype[]>([])
  const [isLoadingArchetypes, setIsLoadingArchetypes] = useState(false)
  const [archetypesLoadError, setArchetypesLoadError] = useState<string | null>(null)
  const [isSearchingByArchetype, setIsSearchingByArchetype] = useState(false)
  const [userArchetypes, setUserArchetypes] = useState<Archetype[]>([])
  const [isCreatingArchetype, setIsCreatingArchetype] = useState(false)
  const [archetypeCreationStep, setArchetypeCreationStep] = useState<'initial' | 'input' | 'extracting' | 'review' | 'saving'>('initial')
  const [newArchetypeData, setNewArchetypeData] = useState<Partial<Archetype>>({})
  const [archetypeJobDescription, setArchetypeJobDescription] = useState("")
  const [archetypeLibraryTab, setArchetypeLibraryTab] = useState<'meus' | 'sugestoes' | 'templates'>('meus')
  const [showSaveAsArchetypeModal, setShowSaveAsArchetypeModal] = useState(false)
  const [lastSuccessfulQuery, setLastSuccessfulQuery] = useState("")
  const [previewSuggestion, setPreviewSuggestion] = useState<AISuggestion | null>(null)
  const [previewingUserArchetype, setPreviewingUserArchetype] = useState<Archetype | null>(null)
  const [archetypeToDelete, setArchetypeToDelete] = useState<Archetype | null>(null)
  const [isDeletingArchetype, setIsDeletingArchetype] = useState(false)

  const buildFiltersFromTags = (tags: string[]): Record<string, string[]> => {
    const seniorityKeywords = ['júnior', 'junior', 'pleno', 'sênior', 'senior', 'especialista', 'lead', 'principal', 'staff', 'estagiário', 'trainee']
    const locationKeywords = ['são paulo', 'rio de janeiro', 'belo horizonte', 'curitiba', 'porto alegre', 'brasília', 'salvador', 'fortaleza', 'recife', 'remoto', 'híbrido', 'presencial']
    
    const skills: string[] = []
    const locations: string[] = []
    const seniority: string[] = []
    
    tags.forEach(tag => {
      const lowerTag = tag.toLowerCase().trim()
      
      if (seniorityKeywords.some(kw => lowerTag.includes(kw))) {
        seniority.push(tag)
      } else if (locationKeywords.some(kw => lowerTag.includes(kw))) {
        locations.push(tag)
      } else {
        skills.push(tag)
      }
    })
    
    return {
      skills,
      locations,
      seniority,
      keywords: tags
    }
  }

  const loadArchetypesFromBackend = async () => {
    setIsLoadingArchetypes(true)
    setArchetypesLoadError(null)
    try {
      const response = await fetch('/api/backend-proxy/search/archetypes')
      if (!response.ok) {
        throw new Error(`Erro ao carregar arquétipos: ${response.status}`)
      }
      const data = await response.json()
      setBackendArchetypes(data.archetypes || [])
    } catch (error) {
      setArchetypesLoadError(error instanceof Error ? error.message : 'Erro ao carregar arquétipos')
    } finally {
      setIsLoadingArchetypes(false)
    }
  }

  const executeArchetypeSearch = async (archetype: BackendArchetype) => {
    setIsSearchingByArchetype(true)
    try {
      const response = await fetch(`/api/backend-proxy/search/archetypes/${archetype.id}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          search_local: true,
          search_pearch: searchSource === 'global' || searchSource === 'hybrid',
          pearch_type: pearchSearchOptions.searchType,
          local_limit: 50,
          pearch_limit: pearchSearchOptions.limit,
          calculate_lia_score: true
        })
      })
      
      if (!response.ok) {
        throw new Error(`Erro na busca: ${response.status}`)
      }
      
      const data = await response.json()
      
      setLiaPromptValue(archetype.query)
      setActiveSearchTab('ia-natural')
      
      if (data.candidates && data.candidates.length > 0) {
        const mappedCandidates: Candidate[] = data.candidates.map((c: {
          id?: string; first_name?: string; last_name?: string; name?: string;
          current_title?: string; headline?: string; current_company?: string;
          linkedin_url?: string; skills?: string[]; location?: string;
          picture_url?: string; total_experience_years?: number; source?: string;
          lia_score?: number; score?: number; lia_reasoning?: string; match_summary?: string;
          is_open_to_work?: boolean; lia_breakdown?: unknown; lia_strengths?: string[]; lia_concerns?: string[]
        }) => ({
          id: c.id || `arch-${Date.now()}-${Math.random()}`,
          candidateId: c.id || '',
          name: c.name || `${c.first_name || ''} ${c.last_name || ''}`.trim(),
          email: '',
          phone: '',
          current_title: c.current_title || c.headline,
          current_company: c.current_company,
          linkedin_url: c.linkedin_url,
          seniority_level: archetype.seniority,
          technical_skills: c.skills || [],
          location_city: c.location?.split(',')[0]?.trim(),
          location_state: c.location?.split(',')[1]?.trim(),
          avatar_url: c.picture_url,
          years_of_experience: c.total_experience_years,
          status: 'new',
          source: c.source || 'pearch',
          matching_score: c.lia_score || c.score || 0,
          match_summary: c.lia_reasoning || c.match_summary,
          is_opentowork: c.is_open_to_work,
          lia_score: c.lia_score,
          lia_breakdown: c.lia_breakdown,
          lia_strengths: c.lia_strengths || [],
          lia_concerns: c.lia_concerns || []
        }))
        
        setCandidates(mappedCandidates)
        setHasSearchResults(true)
        setSearchResultsCount(mappedCandidates.length)
        setLocalResultsCount(data.local_count || 0)
        setPearchResultsCount(data.pearch_count || 0)
        setLastSearchQuery(archetype.query)
        setLastSearchMode('archetype')
        
        const localCount = data.local_count || mappedCandidates.length
        const liaMessage = {
          id: `lia-arch-${Date.now()}`,
          type: 'lia' as const,
          content: `🎯 ${t('searchComplete', { name: archetype.name })}\n\n${t('foundCandidates', { count: localCount })}${data.credits_remaining !== undefined ? `\n\n💳 ${t('creditsRemaining', { count: data.credits_remaining })}` : ''}`,
          timestamp: new Date(),
          searchResults: {
            localCount: localCount,
            globalCount: 0,
            query: archetype.query
          }
        }
        setChatMessages(prev => [...prev, liaMessage])
        
        toast.success(t('toastSearchComplete'), { description: t('toastFoundCount', { count: mappedCandidates.length, name: archetype.name }) })
      } else {
        toast.error(t('toastNoneFound'), { description: t('toastNoneFoundDesc', { name: archetype.name }) })
      }
    } catch (error) {
      toast.error(t('toastSearchError'), { description: error instanceof Error ? error.message : t('toastSearchErrorDesc') })
    } finally {
      setIsSearchingByArchetype(false)
    }
  }

  return {
    state: {
      backendArchetypes, isLoadingArchetypes, archetypesLoadError,
      isSearchingByArchetype, userArchetypes, isCreatingArchetype,
      archetypeCreationStep, newArchetypeData, archetypeJobDescription,
      archetypeLibraryTab, showSaveAsArchetypeModal, lastSuccessfulQuery,
      previewSuggestion, previewingUserArchetype,
      archetypeToDelete, isDeletingArchetype,
    },
    actions: {
      setBackendArchetypes, setIsLoadingArchetypes, setArchetypesLoadError,
      setIsSearchingByArchetype, setUserArchetypes, setIsCreatingArchetype,
      setArchetypeCreationStep, setNewArchetypeData, setArchetypeJobDescription,
      setArchetypeLibraryTab, setShowSaveAsArchetypeModal, setLastSuccessfulQuery,
      setPreviewSuggestion, setPreviewingUserArchetype,
      setArchetypeToDelete, setIsDeletingArchetype,
      buildFiltersFromTags, loadArchetypesFromBackend, executeArchetypeSearch,
    },
  }
}
