"use client"

import { useState, useCallback } from "react"
import { MAX_SIMILAR_URLS, MAX_CV_FILES, API_BASE } from "./smartSearchConstants"

export function useSmartSearchSimilar() {
  const [similarUrl, setSimilarUrl] = useState("")
  const [similarUrls, setSimilarUrls] = useState<string[]>([""])
  const [similarCvFiles, setSimilarCvFiles] = useState<File[]>([])
  const [combinedSuggestions, setCombinedSuggestions] = useState<string[]>([])
  const [isAnalyzingProfiles, setIsAnalyzingProfiles] = useState(false)
  const [showCombinedSuggestions, setShowCombinedSuggestions] = useState(false)
  const [similarSearchPrompt, setSimilarSearchPrompt] = useState("")

  const addSimilarUrl = useCallback(() => {
    if (similarUrls.length < MAX_SIMILAR_URLS) {
      setSimilarUrls(prev => [...prev, ""])
    }
  }, [similarUrls.length])

  const removeSimilarUrl = useCallback((index: number) => {
    setSimilarUrls(prev => prev.filter((_, i) => i !== index))
    setCombinedSuggestions([])
    setShowCombinedSuggestions(false)
  }, [])

  const updateSimilarUrl = useCallback((index: number, urlValue: string) => {
    setSimilarUrls(prev => {
      const newUrls = [...prev]
      newUrls[index] = urlValue
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

  const addSuggestion = useCallback((keyword: string) => {
    setCombinedSuggestions(prev => {
      if (prev.includes(keyword)) return prev
      return [...prev, keyword]
    })
  }, [])

  const analyzeProfiles = useCallback(async () => {
    const validUrls = similarUrls.filter(url => url.trim().length > 0)
    if (validUrls.length === 0 && similarCvFiles.length === 0) return

    setIsAnalyzingProfiles(true)
    try {
      const formData = new FormData()
      validUrls.forEach((url, i) => formData.append(`urls[${i}]`, url))
      similarCvFiles.forEach((file, i) => formData.append(`cvs[${i}]`, file))

      const response = await fetch(`${API_BASE}/api/backend-proxy/search/similar/combine-profiles`, {
        method: "POST",
        body: formData
      })

      if (response.ok) {
        const data = await response.json()
        setCombinedSuggestions(data.keywords || [])
        setShowCombinedSuggestions(true)
      }
    } catch (error) {
      const mockKeywords = ["Sênior", "Python", "AWS", "Data Engineer", "Fintech", "SQL", "Spark"]
      setCombinedSuggestions(mockKeywords)
      setShowCombinedSuggestions(true)
    } finally {
      setIsAnalyzingProfiles(false)
    }
  }, [similarUrls, similarCvFiles])

  const hasMultipleSources = useCallback(() => {
    const validUrls = similarUrls.filter(url => url.trim().length > 0)
    return validUrls.length + similarCvFiles.length >= 2
  }, [similarUrls, similarCvFiles])

  return {
    // State
    similarUrl,
    similarUrls,
    similarCvFiles,
    combinedSuggestions,
    isAnalyzingProfiles,
    showCombinedSuggestions,
    similarSearchPrompt,
    // Setters
    setSimilarUrl,
    setSimilarUrls,
    setSimilarCvFiles,
    setCombinedSuggestions,
    setShowCombinedSuggestions,
    setSimilarSearchPrompt,
    // Callbacks
    addSimilarUrl,
    removeSimilarUrl,
    updateSimilarUrl,
    handleCvUpload,
    removeCvFile,
    removeSuggestion,
    addSuggestion,
    analyzeProfiles,
    hasMultipleSources,
  }
}
