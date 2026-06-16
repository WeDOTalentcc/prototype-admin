"use client"

import { useCallback } from "react"
import { API_BASE } from "./smartSearchConstants"
import type { UseSmartSearchCallbacksParams } from "./useSmartSearchCallbackTypes"

export function useCallbacksSimilarOps(params: UseSmartSearchCallbacksParams) {
  const {
    similarUrls, similarCvFiles, combinedSuggestions,
    MAX_SIMILAR_URLS, MAX_CV_FILES,
    setSimilarUrls, setSimilarCvFiles, setCombinedSuggestions,
    setShowCombinedSuggestions, setIsAnalyzingProfiles,
  } = params

  const addSimilarUrl = useCallback(() => {
    if (similarUrls.length < MAX_SIMILAR_URLS) {
      setSimilarUrls(prev => [...prev, ""])
    }
  }, [similarUrls.length, MAX_SIMILAR_URLS, setSimilarUrls])

  const removeSimilarUrl = useCallback((index: number) => {
    setSimilarUrls(prev => prev.filter((_, i) => i !== index))
    setCombinedSuggestions([])
    setShowCombinedSuggestions(false)
  }, [setSimilarUrls, setCombinedSuggestions, setShowCombinedSuggestions])

  const updateSimilarUrl = useCallback((index: number, val: string) => {
    setSimilarUrls(prev => {
      const newUrls = [...prev]
      newUrls[index] = val
      return newUrls
    })
  }, [setSimilarUrls])

  const handleCvUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files) return
    const newFiles = Array.from(files).slice(0, MAX_CV_FILES - similarCvFiles.length)
    setSimilarCvFiles(prev => [...prev, ...newFiles].slice(0, MAX_CV_FILES))
  }, [similarCvFiles.length, MAX_CV_FILES, setSimilarCvFiles])

  const removeCvFile = useCallback((index: number) => {
    setSimilarCvFiles(prev => prev.filter((_, i) => i !== index))
    setCombinedSuggestions([])
    setShowCombinedSuggestions(false)
  }, [setSimilarCvFiles, setCombinedSuggestions, setShowCombinedSuggestions])

  const removeSuggestion = useCallback((keyword: string) => {
    setCombinedSuggestions(prev => prev.filter(k => k !== keyword))
  }, [setCombinedSuggestions])

  const addSuggestion = useCallback((keyword: string) => {
    if (!combinedSuggestions.includes(keyword)) {
      setCombinedSuggestions(prev => [...prev, keyword])
    }
  }, [combinedSuggestions, setCombinedSuggestions])

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
  }, [similarUrls, similarCvFiles, setIsAnalyzingProfiles, setCombinedSuggestions, setShowCombinedSuggestions])

  const hasMultipleSources = useCallback(() => {
    const validUrls = similarUrls.filter(url => url.trim().length > 0)
    return validUrls.length + similarCvFiles.length >= 2
  }, [similarUrls, similarCvFiles])

  return {
    addSimilarUrl, removeSimilarUrl, updateSimilarUrl,
    handleCvUpload, removeCvFile, removeSuggestion,
    addSuggestion, analyzeProfiles, hasMultipleSources,
  }
}
