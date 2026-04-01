"use client"

import { useState, useEffect, useCallback } from "react"

// Interface para histórico de comandos
interface CommandHistory {
  command: string
  timestamp: Date
  filters?: Record<string, unknown>
  actions?: string[]
  complexity: number
  sessionId: string
}

// Interface para configurações do usuário
interface TemplateSettings {
  enabled: boolean
  minComplexity: number
  minRepetitions: number
  frequency: 'never' | 'weekly' | 'daily' | 'smart'
  showEndOfSession: boolean
}

// Interface para sugestão de template
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

  // Carregar dados do localStorage
  useEffect(() => {
    const savedHistory = localStorage.getItem('lia-command-history')
    if (savedHistory) {
      try {
        const parsed = JSON.parse(savedHistory).map((item: Record<string, unknown>) => ({
          ...item,          // @ts-ignore // TODO: fix type
          timestamp: new Date(item.timestamp)
        }))
        setCommandHistory(parsed)
      } catch (error) {
      }
    }

    const savedSettings = localStorage.getItem('lia-template-settings')
    if (savedSettings) {
      try {
        setSettings(JSON.parse(savedSettings))
      } catch (error) {
      }
    }

    // Detectar fim de sessão
    const handleBeforeUnload = () => {
      setIsEndOfSession(true)
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [])

  // Salvar dados no localStorage
  const saveToLocalStorage = useCallback((history: CommandHistory[]) => {
    // Manter apenas últimos 100 comandos
    const trimmedHistory = history.slice(-100)
    localStorage.setItem('lia-command-history', JSON.stringify(trimmedHistory))
    setCommandHistory(trimmedHistory)
  }, [])

  // Calcular complexidade do comando
  const calculateComplexity = useCallback((command: string, filters?: Record<string, unknown>, actions?: string[]): number => {
    let complexity = 0

    // Complexidade baseada no tamanho do comando
    complexity += Math.min(command.length / 20, 5)

    // Complexidade baseada nos filtros
    if (filters) {
      const filterCount = Object.values(filters).flat().length
      complexity += filterCount * 0.5
    }

    // Complexidade baseada nas ações
    if (actions) {
      complexity += actions.length * 2
    }

    // Comandos com operadores booleanos
    if (command.includes('AND') || command.includes('OR') || command.includes('NOT')) {
      complexity += 3
    }

    // Comandos multi-etapa
    if (command.includes('→') || command.includes('depois') || command.includes('então')) {
      complexity += 4
    }

    return Math.round(complexity)
  }, [])

  // Registrar novo comando
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
    saveToLocalStorage(updatedHistory)

    // Analisar padrões em tempo real
    analyzePatterns(updatedHistory, newCommand)
  }, [commandHistory, settings, sessionId, calculateComplexity, saveToLocalStorage])

  // Analisar padrões e sugerir templates
  const analyzePatterns = useCallback((history: CommandHistory[], newCommand: CommandHistory) => {
    if (!settings.enabled) return

    // Encontrar comandos similares
    const similarCommands = history.filter(cmd =>
      cmd.command === newCommand.command &&
      cmd.sessionId !== newCommand.sessionId // Diferentes sessões
    )

    // Comando repetido suficientes vezes?
    if (similarCommands.length >= settings.minRepetitions - 1) {
      const existingSuggestion = templateSuggestions.find(s => s.command === newCommand.command)

      if (!existingSuggestion && newCommand.complexity >= settings.minComplexity) {
        const suggestion: TemplateSuggestion = {
          id: `suggestion-${Date.now()}`,
          command: newCommand.command,
          reason: `Comando usado ${similarCommands.length + 1} vezes`,
          complexity: newCommand.complexity,
          repetitions: similarCommands.length + 1,
          estimatedTime: Math.round(newCommand.complexity * 30), // segundos
          suggested: false
        }

        setTemplateSuggestions(prev => [...prev, suggestion])
      }
    }

    // Comando complexo usado pela primeira vez (mas muito complexo)
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

  // Obter sugestões pendentes
  const getPendingSuggestions = useCallback((): TemplateSuggestion[] => {
    return templateSuggestions.filter(s => !s.suggested)
  }, [templateSuggestions])

  // Marcar sugestão como mostrada
  const markSuggestionAsShown = useCallback((suggestionId: string) => {
    setTemplateSuggestions(prev =>
      prev.map(s => s.id === suggestionId ? { ...s, suggested: true } : s)
    )
  }, [])

  // Descartar sugestão
  const dismissSuggestion = useCallback((suggestionId: string) => {
    setTemplateSuggestions(prev => prev.filter(s => s.id !== suggestionId))
  }, [])

  // Verificar se deve mostrar sugestão
  const shouldShowSuggestion = useCallback((suggestion: TemplateSuggestion): boolean => {
    if (!settings.enabled || suggestion.suggested) return false

    // Sugestão baseada em repetições
    if (suggestion.repetitions >= settings.minRepetitions) return true

    // Sugestão baseada em complexidade
    if (suggestion.complexity >= 8) return true

    // Fim de sessão com comandos múltiplos
    if (isEndOfSession && settings.showEndOfSession && suggestion.repetitions >= 2) return true

    return false
  }, [settings, isEndOfSession])

  // Atualizar configurações
  const updateSettings = useCallback((newSettings: Partial<TemplateSettings>) => {
    const updatedSettings = { ...settings, ...newSettings }
    setSettings(updatedSettings)
    localStorage.setItem('lia-template-settings', JSON.stringify(updatedSettings))
  }, [settings])

  // Obter estatísticas
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
    commandHistory: commandHistory.slice(-20), // Últimos 20 para UI
    isEndOfSession
  }
}
