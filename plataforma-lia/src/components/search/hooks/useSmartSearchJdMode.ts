"use client"

import { useState, useCallback, useRef, useEffect } from "react"
import type { SearchMode } from "./smartSearchConstants"

interface UseSmartSearchJdModeParams {
  value: string
  mode: SearchMode
}

export function useSmartSearchJdMode(params: UseSmartSearchJdModeParams) {
  const { value, mode } = params

  const [jdContent, setJdContent] = useState("")
  const [jdVacancySearch, setJdVacancySearch] = useState("")
  const [jdVacancyResults, setJdVacancyResults] = useState<Array<{
    id: string
    job_id: string | null
    title: string
    status: string
    created_at: string
    description_preview: string | null
  }>>([])
  const [isSearchingVacancies, setIsSearchingVacancies] = useState(false)
  const [selectedVacancy, setSelectedVacancy] = useState<{
    id: string
    title: string
    job_id: string | null
  } | null>(null)
  const [showVacancyResults, setShowVacancyResults] = useState(false)
  const [jdSearchPrompt, setJdSearchPrompt] = useState("")
  const [booleanFinalPrompt, setBooleanFinalPrompt] = useState("")
  const jdVacancySearchTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const searchJobVacancies = useCallback(async (searchTerm: string) => {
    if (searchTerm.length < 2) {
      setJdVacancyResults([])
      setShowVacancyResults(false)
      return
    }
    setIsSearchingVacancies(true)
    try {
      const response = await fetch(`/api/backend-proxy/job-vacancies/search?query=${encodeURIComponent(searchTerm)}&page_size=5`)
      if (response.ok) {
        const data = await response.json()
        setJdVacancyResults(data.items || [])
        setShowVacancyResults(true)
      }
    } catch (error) {
      setJdVacancyResults([])
    } finally {
      setIsSearchingVacancies(false)
    }
  }, [])

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    try {
      const text = await file.text()
      setJdContent(text)
      setSelectedVacancy(null)
    } catch (error) {
    }
  }

  const handleSelectVacancy = async (vacancy: typeof jdVacancyResults[0]) => {
    setSelectedVacancy({
      id: vacancy.id,
      title: vacancy.title,
      job_id: vacancy.job_id
    })
    setShowVacancyResults(false)
    setJdVacancySearch("")
    try {
      const response = await fetch(`/api/backend-proxy/job-vacancies/${vacancy.id}`)
      if (response.ok) {
        const fullVacancy = await response.json()
        if (fullVacancy.description) {
          setJdContent(fullVacancy.description)
        } else {
          const parts: string[] = []
          if (fullVacancy.title) parts.push(`Cargo: ${fullVacancy.title}`)
          if (fullVacancy.department) parts.push(`Departamento: ${fullVacancy.department}`)
          if (fullVacancy.location) parts.push(`Localização: ${fullVacancy.location}`)
          if (fullVacancy.seniority_level) parts.push(`Senioridade: ${fullVacancy.seniority_level}`)
          if (fullVacancy.requirements?.length) parts.push(`Requisitos: ${fullVacancy.requirements.join(', ')}`)
          setJdContent(parts.join('\n\n'))
        }
      }
    } catch (error) {
      if (vacancy.description_preview) {
        setJdContent(vacancy.description_preview.replace('...', ''))
      }
    }
  }

  const clearSelectedVacancy = () => {
    setSelectedVacancy(null)
    setJdContent("")
    setJdVacancySearch("")
  }

  const formatDate = (dateStr: string) => {
    if (!dateStr) return ""
    try {
      return new Date(dateStr).toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
      })
    } catch {
      return dateStr
    }
  }

  useEffect(() => {
    if (jdVacancySearchTimeoutRef.current) {
      clearTimeout(jdVacancySearchTimeoutRef.current)
    }
    if (jdVacancySearch.length >= 2) {
      jdVacancySearchTimeoutRef.current = setTimeout(() => {
        searchJobVacancies(jdVacancySearch)
      }, 300)
    } else {
      setJdVacancyResults([])
      setShowVacancyResults(false)
    }
    return () => {
      if (jdVacancySearchTimeoutRef.current) {
        clearTimeout(jdVacancySearchTimeoutRef.current)
      }
    }
  }, [jdVacancySearch, searchJobVacancies])

  useEffect(() => {
    if (jdContent.trim().length > 0) {
      const preview = jdContent.length > 200
        ? `Analisar descrição da vaga e encontrar candidatos compatíveis:\n\n${jdContent.slice(0, 200)}...`
        : `Analisar descrição da vaga e encontrar candidatos compatíveis:\n\n${jdContent}`
      setJdSearchPrompt(preview)
    } else {
      setJdSearchPrompt("")
    }
  }, [jdContent])

  useEffect(() => {
    if (value.trim() && mode === "boolean") {
      setBooleanFinalPrompt(`Busca booleana: ${value.trim()}`)
    } else {
      setBooleanFinalPrompt("")
    }
  }, [value, mode])

  return {
    jdContent, setJdContent, jdVacancySearch, setJdVacancySearch,
    jdVacancyResults, isSearchingVacancies, selectedVacancy, setSelectedVacancy,
    showVacancyResults, jdSearchPrompt, setJdSearchPrompt,
    booleanFinalPrompt, setBooleanFinalPrompt,
    handleFileUpload, handleSelectVacancy, clearSelectedVacancy, formatDate,
  }
}
