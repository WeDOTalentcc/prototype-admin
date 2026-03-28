"use client"

/**
 * useSimilarProfiles — Gerência de perfis similares (LinkedIn URLs + CVs) para busca por semelhança.
 *
 * Extraído de ExpandableAIPrompt (P1-E).
 * Gerencia: similarUrls, similarCvFiles, similarProfiles, combinedSuggestions e todos os handlers.
 *
 * Recebe `onNaturalSearchValueChange` pois `analyzeProfiles` auto-popula o campo de busca.
 *
 * Portabilidade Vue: mapeia para composable useSimilarProfiles().
 */

import { useState, useCallback } from "react"
import type { SimilarProfile } from "@/components/search/expandable-ai-prompt.types"
import { MAX_SIMILAR_URLS, MAX_CV_FILES } from "@/components/search/expandable-ai-prompt.types"

export interface UseSimilarProfilesResult {
  similarUrls: string[]
  setSimilarUrls: React.Dispatch<React.SetStateAction<string[]>>
  similarCvFiles: File[]
  isAnalyzingProfiles: boolean
  similarProfiles: SimilarProfile[]
  combinedProfileKeywords: string[]
  combinedSuggestions: string[]
  showCombinedSuggestions: boolean
  similarProfileUrl: string
  setSimilarProfileUrl: (v: string) => void
  addSimilarProfile: (url: string, type?: 'linkedin' | 'cv', filename?: string) => void
  removeSimilarProfile: (url: string) => void
  addSimilarUrl: () => void
  removeSimilarUrl: (index: number) => void
  updateSimilarUrl: (index: number, value: string) => void
  handleCvUpload: (e: React.ChangeEvent<HTMLInputElement>) => void
  removeCvFile: (index: number) => void
  removeSuggestion: (keyword: string) => void
  hasMultipleSources: () => boolean
  analyzeProfiles: () => Promise<void>
}

interface UseSimilarProfilesOptions {
  onNaturalSearchValueChange: (v: string) => void
}

export function useSimilarProfiles({ onNaturalSearchValueChange }: UseSimilarProfilesOptions): UseSimilarProfilesResult {
  const [similarUrls, setSimilarUrls] = useState<string[]>([""])
  const [similarCvFiles, setSimilarCvFiles] = useState<File[]>([])
  const [isAnalyzingProfiles, setIsAnalyzingProfiles] = useState(false)
  const [similarProfiles, setSimilarProfiles] = useState<SimilarProfile[]>([])
  const [combinedProfileKeywords, setCombinedProfileKeywords] = useState<string[]>([])
  const [combinedSuggestions, setCombinedSuggestions] = useState<string[]>([])
  const [showCombinedSuggestions, setShowCombinedSuggestions] = useState(false)
  const [similarProfileUrl, setSimilarProfileUrl] = useState("")

  const addSimilarProfile = useCallback((url: string, type: 'linkedin' | 'cv' = 'linkedin', filename?: string) => {
    setSimilarProfiles(prev => {
      if (prev.length >= 3 || prev.some(p => p.url === url)) return prev
      return [...prev, { url, type, filename }]
    })
  }, [])

  const removeSimilarProfile = useCallback((url: string) => {
    setSimilarProfiles(prev => prev.filter(p => p.url !== url))
  }, [])

  const addSimilarUrl = useCallback(() => {
    setSimilarUrls(prev => {
      if (prev.length >= MAX_SIMILAR_URLS) return prev
      return [...prev, ""]
    })
  }, [])

  const removeSimilarUrl = useCallback((index: number) => {
    setSimilarUrls(prev => prev.filter((_, i) => i !== index))
    setCombinedSuggestions([])
    setShowCombinedSuggestions(false)
  }, [])

  const updateSimilarUrl = useCallback((index: number, value: string) => {
    setSimilarUrls(prev => {
      const newUrls = [...prev]
      newUrls[index] = value
      return newUrls
    })
  }, [])

  const handleCvUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files) return
    setSimilarCvFiles(prev => {
      const newFiles = Array.from(files).slice(0, MAX_CV_FILES - prev.length)
      return [...prev, ...newFiles].slice(0, MAX_CV_FILES)
    })
  }, [])

  const removeCvFile = useCallback((index: number) => {
    setSimilarCvFiles(prev => prev.filter((_, i) => i !== index))
    setCombinedSuggestions([])
    setShowCombinedSuggestions(false)
  }, [])

  const removeSuggestion = useCallback((keyword: string) => {
    setCombinedSuggestions(prev => prev.filter(k => k !== keyword))
  }, [])

  const hasMultipleSources = useCallback(() => {
    const validUrls = similarUrls.filter(url => url.trim().length > 0)
    return validUrls.length + similarCvFiles.length >= 1
  }, [similarUrls, similarCvFiles])

  const analyzeProfiles = useCallback(async () => {
    const validUrls = similarUrls.filter(url => url.trim().length > 0)
    if (validUrls.length === 0 && similarCvFiles.length === 0) return

    setIsAnalyzingProfiles(true)
    try {
      const formData = new FormData()
      validUrls.forEach(url => formData.append('urls', url))
      similarCvFiles.forEach(file => formData.append('cvs', file))

      const response = await fetch('/api/backend-proxy/search/similar/combine-profiles', {
        method: 'POST',
        body: formData,
      })

      if (response.ok) {
        const data = await response.json()
        const keywords: string[] = data.keywords || []
        setCombinedSuggestions(keywords)
        setShowCombinedSuggestions(true)

        if (data.title) {
          setCombinedProfileKeywords(() => {
            const combined = [...keywords]
            if (data.title && !combined.includes(data.title)) combined.push(data.title)
            if (data.location && !combined.includes(data.location)) combined.push(data.location)
            return combined
          })
        }

        if (keywords.length > 0) {
          onNaturalSearchValueChange(keywords.slice(0, 6).join(', '))
        }
      } else {
      }
    } catch (error) {
    } finally {
      setIsAnalyzingProfiles(false)
    }
  }, [similarUrls, similarCvFiles, onNaturalSearchValueChange])

  return {
    similarUrls,
    setSimilarUrls,
    similarCvFiles,
    isAnalyzingProfiles,
    similarProfiles,
    combinedProfileKeywords,
    combinedSuggestions,
    showCombinedSuggestions,
    similarProfileUrl,
    setSimilarProfileUrl,
    addSimilarProfile,
    removeSimilarProfile,
    addSimilarUrl,
    removeSimilarUrl,
    updateSimilarUrl,
    handleCvUpload,
    removeCvFile,
    removeSuggestion,
    hasMultipleSources,
    analyzeProfiles,
  }
}
