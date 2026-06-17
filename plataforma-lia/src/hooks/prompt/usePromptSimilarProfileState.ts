"use client"

import { useState, useCallback, useRef } from "react"
import type { SimilarProfile } from "@/hooks/ui/usePromptState"

const MAX_SIMILAR_URLS = 2
const MAX_CV_FILES = 2

export interface UsePromptSimilarProfileStateReturn {
  similarUrls: string[]
  setSimilarUrls: React.Dispatch<React.SetStateAction<string[]>>
  similarCvFiles: File[]
  setSimilarCvFiles: React.Dispatch<React.SetStateAction<File[]>>
  isAnalyzingProfiles: boolean
  combinedSuggestions: string[]
  showCombinedSuggestions: boolean
  cvFileInputRef: React.RefObject<HTMLInputElement | null>
  MAX_SIMILAR_URLS: number
  MAX_CV_FILES: number
  similarProfiles: SimilarProfile[]
  combinedProfileKeywords: string[]
  addSimilarProfile: (url: string, type?: 'linkedin' | 'cv', filename?: string) => void
  removeSimilarProfile: (url: string) => void
  addSimilarUrl: () => void
  removeSimilarUrl: (index: number) => void
  updateSimilarUrl: (index: number, value: string) => void
  handleCvUpload: (e: React.ChangeEvent<HTMLInputElement>) => void
  removeCvFile: (index: number) => void
  removeSuggestion: (keyword: string) => void
  hasMultipleSources: () => boolean
  analyzeProfiles: (setNaturalSearchValue: React.Dispatch<React.SetStateAction<string>>) => Promise<void>
  analyzeCombinedProfiles: () => Promise<void>
}

export function usePromptSimilarProfileState(): UsePromptSimilarProfileStateReturn {
  const [similarUrls, setSimilarUrls] = useState<string[]>([""])
  const [similarCvFiles, setSimilarCvFiles] = useState<File[]>([])
  const [isAnalyzingProfiles, setIsAnalyzingProfiles] = useState(false)
  const [combinedSuggestions, setCombinedSuggestions] = useState<string[]>([])
  const [showCombinedSuggestions, setShowCombinedSuggestions] = useState(false)
  const cvFileInputRef = useRef<HTMLInputElement>(null)

  const [similarProfiles, setSimilarProfiles] = useState<SimilarProfile[]>([])
  const [combinedProfileKeywords, setCombinedProfileKeywords] = useState<string[]>([])

  const addSimilarProfile = useCallback((url: string, type: 'linkedin' | 'cv' = 'linkedin', filename?: string) => {
    if (similarProfiles.length >= 3 || similarProfiles.some(p => p.url === url)) return
    setSimilarProfiles(prev => [...prev, { url, type, filename }])
  }, [similarProfiles])

  const removeSimilarProfile = useCallback((url: string) => {
    setSimilarProfiles(prev => prev.filter(p => p.url !== url))
  }, [])

  const addSimilarUrl = useCallback(() => {
    if (similarUrls.length < MAX_SIMILAR_URLS) setSimilarUrls(prev => [...prev, ""])
  }, [similarUrls.length])

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
    const newFiles = Array.from(files).slice(0, MAX_CV_FILES - similarCvFiles.length)
    setSimilarCvFiles(prev => [...prev, ...newFiles].slice(0, MAX_CV_FILES))
  }, [similarCvFiles.length])

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

  const analyzeProfiles = useCallback(async (
    setNaturalSearchValue: React.Dispatch<React.SetStateAction<string>>
  ) => {
    const validUrls = similarUrls.filter(url => url.trim().length > 0)
    if (validUrls.length === 0 && similarCvFiles.length === 0) return
    setIsAnalyzingProfiles(true)
    try {
      const formData = new FormData()
      validUrls.forEach(url => formData.append('urls', url))
      similarCvFiles.forEach(file => formData.append('cvs', file))
      const response = await fetch('/api/backend-proxy/search/similar/combine-profiles', {
        method: "POST", body: formData
      })
      if (response.ok) {
        const data = await response.json()
        const keywords = data.keywords || []
        setCombinedSuggestions(keywords)
        setShowCombinedSuggestions(true)
        if (data.title) {
          setCombinedProfileKeywords(prev => {
            const combined = [...keywords]
            if (data.title && !combined.includes(data.title)) combined.push(data.title)
            if (data.location && !combined.includes(data.location)) combined.push(data.location)
            return combined
          })
        }
        if (keywords.length > 0) {
          const searchQuery = keywords.slice(0, 6).join(', ')
          setNaturalSearchValue(searchQuery)
        }
      }
    } catch {
    } finally {
      setIsAnalyzingProfiles(false)
    }
  }, [similarUrls, similarCvFiles])

  const analyzeCombinedProfiles = useCallback(async () => {
    if (similarProfiles.length === 0) return
    setIsAnalyzingProfiles(true)
    try {
      const formData = new FormData()
      similarProfiles.forEach(profile => {
        if (profile.type === 'linkedin') {
          formData.append('urls', profile.url)
        }
      })
      const res = await fetch('/api/backend-proxy/search/similar/combine-profiles', {
        method: 'POST',
        body: formData
      })
      if (res.ok) {
        const data = await res.json()
        setCombinedProfileKeywords(data.keywords || [])
      }
    } catch {
    } finally {
      setIsAnalyzingProfiles(false)
    }
  }, [similarProfiles])

  return {
    similarUrls, setSimilarUrls,
    similarCvFiles, setSimilarCvFiles,
    isAnalyzingProfiles,
    combinedSuggestions,
    showCombinedSuggestions,
    cvFileInputRef,
    MAX_SIMILAR_URLS,
    MAX_CV_FILES,
    similarProfiles,
    combinedProfileKeywords,
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
    analyzeCombinedProfiles,
  }
}
