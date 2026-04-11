"use client"

/**
 * useSearchEntities — Parsing de entidades, análise de qualidade e melhoria de prompt.
 *
 * Extraído de ExpandableAIPrompt (P1-E).
 * Gerencia: parsedEntities, searchAnalysis, extractedCriteria, promptEnhancement
 * e todos os handlers de critérios, áudio, arquivo e execução de busca.
 *
 * Recebe como parâmetro o estado externo de que depende:
 *   - naturalSearchValue / onNaturalSearchValueChange (para aceitar enhancement e áudio)
 *   - activeSearchTab (para debounce do enhancement)
 *   - onCommand (para executeSearchWithCriteria)
 *   - toast (para feedback de arquivo/áudio)
 *
 * Portabilidade Vue: mapeia para composable useSearchEntities().
 */

import { useState, useRef, useCallback, useEffect } from "react"
import type { SearchTab, BackendEntities, SearchAnalysis, SearchCriterion } from "@/components/search/expandable-ai-prompt.types"
import { ENTITY_LABELS, CRITERIA_TYPE_MAP } from "@/components/search/expandable-ai-prompt.types"
import type { FileAnalysisResult } from "@/components/ui/file-upload-button"
import { toast } from "sonner"

export interface PromptEnhancement {
  enhanced_query: string
  explanation: string
  confidence: number
  suggestions?: Array<{ label: string; value: string; category: string }>
}

export interface UseSearchEntitiesResult {
  parsedEntities: BackendEntities
  searchAnalysis: SearchAnalysis | null
  isParsingEntities: boolean
  extractedCriteria: SearchCriterion[]
  promptEnhancement: PromptEnhancement | null
  isEnhancingPrompt: boolean
  promptEnhancementDismissed: boolean
  showPremiumAutocomplete: boolean
  setShowPremiumAutocomplete: (v: boolean) => void
  parseEntitiesFromQuery: (query: string) => Promise<void>
  extractCriteriaFromQuery: (query: string) => void
  buildSearchQueryFromCriteria: () => string
  executeSearchWithCriteria: () => void
  removeCriterion: (id: string) => void
  toggleCriterion: (id: string) => void
  handleAcceptEnhancement: () => void
  handleDismissEnhancement: () => void
  handleFileAnalyzed: (file: File, analysis: FileAnalysisResult) => void
  handleAudioTranscription: (text: string) => void
  handlePremiumAutocompleteSelect: (suggestion: string) => void
}

interface UseSearchEntitiesOptions {
  naturalSearchValue: string
  activeSearchTab: SearchTab
  onNaturalSearchValueChange: (v: string | ((prev: string) => string)) => void
  onCommand: (command: string, action: string) => void
}

export function useSearchEntities({
  naturalSearchValue,
  activeSearchTab,
  onNaturalSearchValueChange,
  onCommand,
}: UseSearchEntitiesOptions): UseSearchEntitiesResult {
  const [parsedEntities, setParsedEntities] = useState<BackendEntities>({})
  const [searchAnalysis, setSearchAnalysis] = useState<SearchAnalysis | null>(null)
  const [isParsingEntities, setIsParsingEntities] = useState(false)
  const [extractedCriteria, setExtractedCriteria] = useState<SearchCriterion[]>([])
  const [promptEnhancement, setPromptEnhancement] = useState<PromptEnhancement | null>(null)
  const [isEnhancingPrompt, setIsEnhancingPrompt] = useState(false)
  const [promptEnhancementDismissed, setPromptEnhancementDismissed] = useState(false)
  const [showPremiumAutocomplete, setShowPremiumAutocomplete] = useState(false)

  const dismissedQueryRef = useRef<string>("")
  const enhanceTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const extractionTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const lastQueryRef = useRef<string>('')

  // ── Entity parsing (API) ─────────────────────────────────────────────────

  const parseEntitiesFromQuery = useCallback(async (query: string) => {
    if (!query.trim() || query.length < 5) {
      setSearchAnalysis(null)
      setExtractedCriteria([])
      setParsedEntities({})
      return
    }

    setIsParsingEntities(true)

    try {
      const [parseRes, analysisRes] = await Promise.all([
        fetch('/api/backend-proxy/search/parse-query/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query }),
        }),
        fetch('/api/backend-proxy/search-assistant/analyze/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query }),
        }),
      ])

      if (parseRes.ok) {
        const parseData = await parseRes.json()
        const entities = parseData.entities as BackendEntities
        setParsedEntities(entities || {})

        if (entities) {
          const newCriteria: SearchCriterion[] = []
          let idx = 0

          if (entities.job_title) {
            newCriteria.push({ id: `entity-job_title-${idx++}`, type: 'job_title', label: ENTITY_LABELS.job_title, value: entities.job_title, active: true })
          }
          if (entities.location) {
            newCriteria.push({ id: `entity-location-${idx++}`, type: 'location', label: ENTITY_LABELS.location, value: entities.location, active: true })
          }
          if (entities.years_experience) {
            newCriteria.push({ id: `entity-years_experience-${idx++}`, type: 'years_experience', label: ENTITY_LABELS.years_experience, value: entities.years_experience, active: true })
          }
          if (entities.industry) {
            newCriteria.push({ id: `entity-industry-${idx++}`, type: 'industry', label: ENTITY_LABELS.industry, value: entities.industry, active: true })
          }
          if (entities.skills && entities.skills.length > 0) {
            entities.skills.forEach((skill, skillIdx) => {
              newCriteria.push({ id: `entity-skills-${idx++}-${skillIdx}`, type: 'skills', label: 'Habilidade', value: skill, active: true })
            })
          }
          if (entities.seniority) {
            newCriteria.push({ id: `entity-seniority-${idx++}`, type: 'seniority', label: ENTITY_LABELS.seniority, value: entities.seniority, active: true })
          }
          if (entities.company) {
            newCriteria.push({ id: `entity-company-${idx++}`, type: 'company', label: ENTITY_LABELS.company, value: entities.company, active: true })
          }

          setExtractedCriteria(newCriteria)
        }
      }

      if (analysisRes.ok) {
        const backendAnalysis = await analysisRes.json()

        const criteriaFound = (backendAnalysis.filled_criteria || []).map((label: string) => ({
          type: CRITERIA_TYPE_MAP[label] || label.toLowerCase(),
          label,
          value: label,
        }))

        const criteriaMissing = (backendAnalysis.missing_criteria || []).map((label: string) => ({
          type: CRITERIA_TYPE_MAP[label] || label.toLowerCase(),
          label,
          importance: label === 'Cargo' || label === 'Localização' ? 'high' : 'medium',
        }))

        setSearchAnalysis({
          completeness_score: backendAnalysis.completeness_score || 0,
          criteria_found: criteriaFound,
          criteria_missing: criteriaMissing,
          alerts: backendAnalysis.alerts || [],
          suggestions: [],
          enrichment_suggestions: backendAnalysis.enrichment_suggestions || {},
          next_recommended_action: backendAnalysis.next_recommended_action,
        })
      }
    } catch (error) {
    } finally {
      setIsParsingEntities(false)
    }
  }, [])

  // ── Prompt enhancement (API + debounce) ──────────────────────────────────

  const fetchPromptEnhancement = useCallback(async (query: string) => {
    if (!query || query.length < 10 || promptEnhancementDismissed) {
      setPromptEnhancement(null)
      return
    }

    setIsEnhancingPrompt(true)
    try {
      const response = await fetch('/api/backend-proxy/enhance-prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      })

      if (response.ok) {
        const data = await response.json()
        if (data.enhanced_query && data.enhanced_query !== query) {
          setPromptEnhancement(data)
        }
      }
    } catch (error) {
    } finally {
      setIsEnhancingPrompt(false)
    }
  }, [promptEnhancementDismissed])

  useEffect(() => {
    if (activeSearchTab !== 'natural' || !naturalSearchValue || naturalSearchValue.length < 10) {
      setPromptEnhancement(null)
      return
    }

    if (promptEnhancementDismissed && dismissedQueryRef.current) {
      const dismissedPrefix = dismissedQueryRef.current.toLowerCase().slice(0, 15)
      const currentPrefix = naturalSearchValue.toLowerCase().slice(0, 15)
      if (dismissedPrefix !== currentPrefix) {
        setPromptEnhancementDismissed(false)
        dismissedQueryRef.current = ""
      }
    }

    if (enhanceTimeoutRef.current) clearTimeout(enhanceTimeoutRef.current)

    enhanceTimeoutRef.current = setTimeout(() => {
      if (!promptEnhancementDismissed) {
        fetchPromptEnhancement(naturalSearchValue)
      }
    }, 1500)

    return () => {
      if (enhanceTimeoutRef.current) clearTimeout(enhanceTimeoutRef.current)
    }
  }, [naturalSearchValue, activeSearchTab, promptEnhancementDismissed, fetchPromptEnhancement])

  const handleAcceptEnhancement = useCallback(() => {
    if (promptEnhancement) {
      onNaturalSearchValueChange(promptEnhancement.enhanced_query)
      setPromptEnhancement(null)
    }
  }, [promptEnhancement, onNaturalSearchValueChange])

  const handleDismissEnhancement = useCallback(() => {
    dismissedQueryRef.current = naturalSearchValue
    setPromptEnhancementDismissed(true)
    setPromptEnhancement(null)
  }, [naturalSearchValue])

  // ── Criteria (local extraction + CRUD) ───────────────────────────────────

  const removeCriterion = useCallback((id: string) => {
    setExtractedCriteria(prev => prev.filter(c => c.id !== id))
  }, [])

  const toggleCriterion = useCallback((id: string) => {
    setExtractedCriteria(prev => prev.map(c => c.id === id ? { ...c, active: !c.active } : c))
  }, [])

  const extractCriteriaFromQuery = useCallback((query: string) => {
    if (extractionTimeoutRef.current) clearTimeout(extractionTimeoutRef.current)

    extractionTimeoutRef.current = setTimeout(() => {
      const queryLower = query.toLowerCase().trim()
      if (queryLower === lastQueryRef.current) return
      lastQueryRef.current = queryLower

      setExtractedCriteria(prev => {
        const manuallyModified = prev.filter(c => !c.active)
        const newlyExtracted: SearchCriterion[] = []

        const locations = ['são paulo', 'rio de janeiro', 'belo horizonte', 'curitiba', 'porto alegre', 'brasília', 'sp', 'rj']
        for (const loc of locations) {
          if (queryLower.includes(loc)) {
            const id = `loc-${loc.replace(/\s/g, '-')}`
            if (!prev.find(c => c.id === id)) {
              newlyExtracted.push({ id, type: 'location', label: 'Localização', value: loc.charAt(0).toUpperCase() + loc.slice(1), active: true })
            }
            break
          }
        }

        const expMatch = queryLower.match(/(\d+)\+?\s*anos?|(\d+)\+?\s*years?/)
        if (expMatch) {
          const years = expMatch[1] || expMatch[2]
          const id = `exp-${years}`
          if (!prev.find(c => c.id === id)) {
            newlyExtracted.push({ id, type: 'experience', label: 'Experiência', value: `${years}+ anos`, active: true })
          }
        }

        const skills = ['python', 'react', 'node', 'java', 'typescript', 'javascript', 'aws', 'docker', 'kubernetes', 'sql', 'figma', 'ux', 'ui', 'angular', 'vue', 'spring', 'django', 'flask', 'fastapi']
        for (const skill of skills) {
          if (queryLower.includes(skill)) {
            const id = `skill-${skill}`
            if (!prev.find(c => c.id === id)) {
              newlyExtracted.push({ id, type: 'skills', label: 'Skills', value: skill.charAt(0).toUpperCase() + skill.slice(1), active: true })
            }
          }
        }

        const languages = ['inglês', 'espanhol', 'francês', 'alemão', 'english', 'spanish', 'fluente', 'avançado']
        for (const lang of languages) {
          if (queryLower.includes(lang)) {
            const id = `lang-${lang}`
            if (!prev.find(c => c.id === id)) {
              newlyExtracted.push({ id, type: 'language', label: 'Idioma', value: lang.charAt(0).toUpperCase() + lang.slice(1), active: true })
            }
            break
          }
        }

        const seniorities: Record<string, string> = {
          'sênior': 'Sênior', 'senior': 'Sênior',
          'pleno': 'Pleno',
          'júnior': 'Júnior', 'junior': 'Júnior',
          'lead': 'Tech Lead', 'tech lead': 'Tech Lead',
          'especialista': 'Especialista', 'staff': 'Staff',
        }
        for (const [key, value] of Object.entries(seniorities)) {
          if (queryLower.includes(key)) {
            const id = `seniority-${key.replace(/\s/g, '-')}`
            if (!prev.find(c => c.id === id)) {
              newlyExtracted.push({ id, type: 'job_title', label: 'Senioridade', value, active: true })
            }
            break
          }
        }

        const existingActive = prev.filter(c => c.active)
        const merged = [...existingActive, ...manuallyModified]
        for (const newCrit of newlyExtracted) {
          if (!merged.find(c => c.id === newCrit.id)) merged.push(newCrit)
        }
        return merged
      })
    }, 300)
  }, [])

  useEffect(() => {
    return () => {
      if (extractionTimeoutRef.current) clearTimeout(extractionTimeoutRef.current)
    }
  }, [])

  const buildSearchQueryFromCriteria = useCallback(() => {
    const activeCriteria = extractedCriteria.filter(c => c.active)
    if (activeCriteria.length === 0) return naturalSearchValue

    const parts: string[] = []
    activeCriteria.forEach(c => {
      if (c.type === 'location') parts.push(`em ${c.value}`)
      else if (c.type === 'experience' || c.type === 'years_experience') parts.push(`com ${c.value}`)
      else if (c.type === 'skills') parts.push(c.value)
      else if (c.type === 'language') parts.push(`com ${c.value}`)
      else if (c.type === 'job_title' || c.type === 'seniority') parts.push(c.value)
      else if (c.type === 'industry') parts.push(`em ${c.value}`)
      else if (c.type === 'company') parts.push(`da ${c.value}`)
      else if (c.type === 'education') parts.push(c.value)
    })
    return parts.join(' ')
  }, [extractedCriteria, naturalSearchValue])

  const executeSearchWithCriteria = useCallback(() => {
    const searchQuery = buildSearchQueryFromCriteria()
    if (searchQuery.trim()) {
      onCommand(searchQuery, 'natural_search')
    }
  }, [buildSearchQueryFromCriteria, onCommand])

  // ── File / audio / premium autocomplete ─────────────────────────────────

  const handleFileAnalyzed = useCallback((file: File, analysis: FileAnalysisResult) => {
    if (analysis.success) {
      const keywords: string[] = []
      if (analysis.keywords && analysis.keywords.length > 0) {
        keywords.push(...analysis.keywords.slice(0, 5))
      }
      if (analysis.entities) {
        if (analysis.entities.skills) keywords.push(...analysis.entities.skills.slice(0, 3))
        if (analysis.entities.job_titles) keywords.push(...analysis.entities.job_titles.slice(0, 2))
        if (analysis.entities.locations) keywords.push(...analysis.entities.locations.slice(0, 2))
      }
      const uniqueKeywords = [...new Set(keywords)]
      if (uniqueKeywords.length > 0) {
        const searchText = uniqueKeywords.join(', ')
        onNaturalSearchValueChange(prev => (typeof prev === 'string' && prev) ? `${prev}, ${searchText}` : searchText)
        parseEntitiesFromQuery(searchText)
        toast.info("Arquivo analisado", { description: `Extraídos ${uniqueKeywords.length} critérios de ${file.name}` })
      } else {
        toast.info("Arquivo processado", { description: `${file.name} foi analisado mas não foram encontrados critérios de busca` })
      }
    } else {
      toast.error("Erro na análise", { description: analysis.error || "Não foi possível analisar o arquivo" })
    }
  }, [parseEntitiesFromQuery, onNaturalSearchValueChange])

  const handleAudioTranscription = useCallback((text: string) => {
    if (text && text.trim()) {
      onNaturalSearchValueChange(prev => {
        const newValue = (typeof prev === 'string' && prev) ? `${prev} ${text.trim()}` : text.trim()
        parseEntitiesFromQuery(newValue)
        return newValue
      })
      setShowPremiumAutocomplete(true)
      toast.info("Transcrição concluída", { description: "Texto adicionado à busca" })
    }
  }, [parseEntitiesFromQuery, onNaturalSearchValueChange])

  const handlePremiumAutocompleteSelect = useCallback((suggestion: string) => {
    onNaturalSearchValueChange(suggestion)
    setShowPremiumAutocomplete(false)
    parseEntitiesFromQuery(suggestion)
  }, [parseEntitiesFromQuery, onNaturalSearchValueChange])

  return {
    parsedEntities,
    searchAnalysis,
    isParsingEntities,
    extractedCriteria,
    promptEnhancement,
    isEnhancingPrompt,
    promptEnhancementDismissed,
    showPremiumAutocomplete,
    setShowPremiumAutocomplete,
    parseEntitiesFromQuery,
    extractCriteriaFromQuery,
    buildSearchQueryFromCriteria,
    executeSearchWithCriteria,
    removeCriterion,
    toggleCriterion,
    handleAcceptEnhancement,
    handleDismissEnhancement,
    handleFileAnalyzed,
    handleAudioTranscription,
    handlePremiumAutocompleteSelect,
  }
}
