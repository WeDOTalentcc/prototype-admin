"use client"

import { useState, useEffect, useCallback } from "react"
import { useTemplateStore } from "@/stores/template-store"

interface CommandHistory {
  command: string
  timestamp: Date
  filters?: Record<string, unknown>
  actions?: string[]
  complexity: number
  sessionId: string
}

interface TemplateSettings {
  enabled: boolean
  minComplexity: number
  minRepetitions: number
  frequency: 'never' | 'weekly' | 'daily' | 'smart'
  showEndOfSession: boolean
}

interface TemplateSuggestion {
  id: string
  command: string
  reason: string
  complexity: number
  repetitions: number
  estimatedTime: number
  suggested: boolean
}

export const useTemplateSuggestions = () => {
  const templateStore = useTemplateStore()
  const [commandHistory, setCommandHistory] = useState<CommandHistory[]>([])
  const [templateSuggestions, setTemplateSuggestions] = useState<TemplateSuggestion[]>([])
  const [settings, setSettings] = useState<TemplateSettings>({
    enabled: true,
    minComplexity: 5,
    minRepetitions: 3,
    frequency: 'smart',
    showEndOfSession: true
  })
  const [sessionId] = useState(() => `session-${Date.now()}`)
  const [isEndOfSession, setIsEndOfSession] = useState(false)

  useEffect(() => {
    const storedHistory = templateStore.commandHistory
    if (storedHistory.length > 0) {
      try {
        const parsed = storedHistory.map((item) => ({
          ...item,
          timestamp: new Date(item.timestamp)
        }))
        setCommandHistory(parsed)
      } catch (error) {
        console.error("[use-template-suggestions] Error:", error)
      }
    }

    const storedSettings = templateStore.settings
    if (storedSettings) {
      setSettings(storedSettings)
    }

    const handleBeforeUnload = () => {
      setIsEndOfSession(true)
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const saveToStore = useCallback((history: CommandHistory[]) => {
    const trimmedHistory = history.slice(-100)
    templateStore.setCommandHistory(
      trimmedHistory.map(h => ({
        ...h,
        timestamp: h.timestamp.toISOString()
      }))
    )
    setCommandHistory(trimmedHistory)
  }, [templateStore])

  const calculateComplexity = useCallback((command: string, filters?: Record<string, unknown>, actions?: string[]): number => {
    let complexity = 0

    complexity += Math.min(command.length / 20, 5)

    if (filters) {
      const filterCount = Object.values(filters).flat().length
      complexity += filterCount * 0.5
    }

    if (actions) {
      complexity += actions.length * 2
    }

    if (command.includes('AND') || command.includes('OR') || command.includes('NOT')) {
      complexity += 3
    }

    if (command.includes('→') || command.includes('depois') || command.includes('então')) {
      complexity += 4
    }

    return Math.round(complexity)
  }, [])

  const analyzePatterns = useCallback((history: CommandHistory[], newCommand: CommandHistory) => {
    if (!settings.enabled) return

    const similarCommands = history.filter(cmd =>
      cmd.command === newCommand.command &&
      cmd.sessionId !== newCommand.sessionId
    )

    if (similarCommands.length >= settings.minRepetitions - 1) {
      const existingSuggestion = templateSuggestions.find(s => s.command === newCommand.command)

      if (!existingSuggestion && newCommand.complexity >= settings.minComplexity) {
        const suggestion: TemplateSuggestion = {
          id: `suggestion-${Date.now()}`,
          command: newCommand.command,
          reason: `Comando usado ${similarCommands.length + 1} vezes`,
          complexity: newCommand.complexity,
          repetitions: similarCommands.length + 1,
          estimatedTime: Math.round(newCommand.complexity * 30),
          suggested: false
        }

        setTemplateSuggestions(prev => [...prev, suggestion])
      }
    }

    if (newCommand.complexity >= 8 && similarCommands.length === 0) {
      const suggestion: TemplateSuggestion = {
        id: `suggestion-complex-${Date.now()}`,
        command: newCommand.command,
        reason: 'Comando complexo detectado',
        complexity: newCommand.complexity,
        repetitions: 1,
        estimatedTime: Math.round(newCommand.complexity * 30),
        suggested: false
      }

      setTemplateSuggestions(prev => [...prev, suggestion])
    }
  }, [settings, templateSuggestions])

  const addCommand = useCallback((command: string, filters?: Record<string, unknown>, actions?: string[]) => {
    if (!settings.enabled || !command.trim()) return

    const complexity = calculateComplexity(command, filters, actions)

    const newCommand: CommandHistory = {
      command: command.trim(),
      timestamp: new Date(),
      filters,
      actions,
      complexity,
      sessionId
    }

    const updatedHistory = [...commandHistory, newCommand]
    saveToStore(updatedHistory)

    analyzePatterns(updatedHistory, newCommand)
  }, [commandHistory, settings, sessionId, calculateComplexity, saveToStore, analyzePatterns])

  const getPendingSuggestions = useCallback((): TemplateSuggestion[] => {
    return templateSuggestions.filter(s => !s.suggested)
  }, [templateSuggestions])

  const markSuggestionAsShown = useCallback((suggestionId: string) => {
    setTemplateSuggestions(prev =>
      prev.map(s => s.id === suggestionId ? { ...s, suggested: true } : s)
    )
  }, [])

  const dismissSuggestion = useCallback((suggestionId: string) => {
    setTemplateSuggestions(prev => prev.filter(s => s.id !== suggestionId))
  }, [])

  const shouldShowSuggestion = useCallback((suggestion: TemplateSuggestion): boolean => {
    if (!settings.enabled || suggestion.suggested) return false

    if (suggestion.repetitions >= settings.minRepetitions) return true

    if (suggestion.complexity >= 8) return true

    if (isEndOfSession && settings.showEndOfSession && suggestion.repetitions >= 2) return true

    return false
  }, [settings, isEndOfSession])

  const updateSettings = useCallback((newSettings: Partial<TemplateSettings>) => {
    const updatedSettings = { ...settings, ...newSettings }
    setSettings(updatedSettings)
    templateStore.setSettings(updatedSettings)
  }, [settings, templateStore])

  const getStats = useCallback(() => {
    const today = new Date()
    today.setHours(0, 0, 0, 0)

    const todayCommands = commandHistory.filter(cmd => cmd.timestamp >= today)
    const uniqueCommands = new Set(commandHistory.map(cmd => cmd.command)).size
    const avgComplexity = commandHistory.length > 0
      ? commandHistory.reduce((sum, cmd) => sum + cmd.complexity, 0) / commandHistory.length
      : 0

    return {
      totalCommands: commandHistory.length,
      todayCommands: todayCommands.length,
      uniqueCommands,
      avgComplexity: Math.round(avgComplexity * 10) / 10,
      pendingSuggestions: getPendingSuggestions().length
    }
  }, [commandHistory, getPendingSuggestions])

  return {
    addCommand,
    getPendingSuggestions,
    markSuggestionAsShown,
    dismissSuggestion,
    shouldShowSuggestion,
    updateSettings,
    getStats,
    settings,
    commandHistory: commandHistory.slice(-20),
    isEndOfSession
  }
}
