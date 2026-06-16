"use client"

import { useState, useRef, useEffect, useCallback } from"react"
import { X, Brain, Loader2, Search, RotateCcw, Save, List } from"lucide-react"
import { cn } from"@/lib/utils"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { Input } from"@/components/ui/input"
import { UniversityPresetsModal } from"./UniversityPresetsModal"
import { useUIPreferencesStore } from"@/stores/ui-preferences-store"

interface UniversitiesFilterInputProps {
  value: string[]
  onChange: (universities: string[]) => void
  placeholder?: string
  showPresets?: boolean
}

const POPULAR_UNIVERSITIES = ["Harvard University","Stanford University","MIT (Massachusetts Institute of Technology)","Yale University","Princeton University","Columbia University","University of Pennsylvania","Brown University","Cornell University","Dartmouth College","UC Berkeley","UCLA","University of Michigan","University of Chicago","Northwestern University","Duke University","Caltech","Carnegie Mellon University","NYU (New York University)","University of Texas at Austin","Oxford University","Cambridge University","Imperial College London","London School of Economics","University College London","ETH Zurich","EPFL","USP (Universidade de São Paulo)","Unicamp","UFRJ","PUC-Rio","FGV","Insper","ITA","Mackenzie","UFMG","UFRGS","UFPR","UnB","Tsinghua University","Peking University","National University of Singapore","University of Melbourne","University of Sydney","University of Toronto","McGill University","KAIST","Seoul National University","University of Tokyo","Kyoto University",
]

export function UniversitiesFilterInput({
  value,
  onChange,
  placeholder ="Type university name and press Enter",
  showPresets = true
}: UniversitiesFilterInputProps) {
  const { getCustomPresets, setCustomPresets: setCustomPresetsInStore } = useUIPreferencesStore()
  const [inputValue, setInputValue] = useState("")
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [isLoadingAI, setIsLoadingAI] = useState(false)
  const [isFindingSimilar, setIsFindingSimilar] = useState(false)
  const [focusedIndex, setFocusedIndex] = useState(-1)
  const [isPresetsModalOpen, setIsPresetsModalOpen] = useState(false)
  const [aiSuggestions, setAiSuggestions] = useState<string[]>([])
  const [showSavePresetModal, setShowSavePresetModal] = useState(false)
  const [savePresetName, setSavePresetName] = useState("")
  const inputRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const requestIdRef = useRef(0)

  const existingUniversities = value.map(u => u.toLowerCase())

  const filteredSuggestions = inputValue.trim()
    ? POPULAR_UNIVERSITIES.filter(university => 
        university.toLowerCase().includes(inputValue.toLowerCase()) &&
        !existingUniversities.includes(university.toLowerCase())
      ).slice(0, 6)
    : []

  const showAskAI = inputValue.trim().length >= 2
  const allSuggestions = [...new Set([...filteredSuggestions, ...aiSuggestions])]
    .filter(s => !existingUniversities.includes(s.toLowerCase()))
    .slice(0, 8)

  const dropdownItems = showAskAI 
    ? [{ type: 'ai' as const, label: `Ask AI for"${inputValue}"`, university: null }, 
       ...allSuggestions.map(u => ({ type: 'university' as const, label: u, university: u }))]
    : allSuggestions.map(u => ({ type: 'university' as const, label: u, university: u }))

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node) &&
          inputRef.current && !inputRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps -- ref cleanup
      const timeout = debounceTimeoutRef.current
      if (timeout) {
        clearTimeout(timeout)
      }
    }
  }, [])

  const addUniversity = useCallback((university: string) => {
    if (!university.trim()) return
    if (existingUniversities.includes(university.toLowerCase())) return
    onChange([...value, university])
    setInputValue("")
    setIsDropdownOpen(false)
    setFocusedIndex(-1)
    setAiSuggestions([])
  }, [value, onChange, existingUniversities])

  const removeUniversity = useCallback((university: string) => {
    onChange(value.filter(u => u !== university))
  }, [value, onChange])

  const clearAll = useCallback(() => {
    onChange([])
  }, [onChange])

  const handleSaveCustomPreset = useCallback(() => {
    if (!savePresetName.trim() || value.length === 0) return
    
    const existingPresets = getCustomPresets('university_custom_presets')
    const newPreset = {
      id: `custom_${Date.now()}`,
      name: savePresetName.trim(),
      universities: value,
      createdAt: new Date().toISOString()
    }
    setCustomPresetsInStore('university_custom_presets', [...existingPresets, newPreset])
    setSavePresetName("")
    setShowSavePresetModal(false)
  }, [savePresetName, value, getCustomPresets, setCustomPresetsInStore])

  const askAIForUniversities = useCallback(async (query: string) => {
    if (!query.trim()) return
    
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    
    const controller = new AbortController()
    abortControllerRef.current = controller
    const currentRequestId = ++requestIdRef.current
    
    setIsLoadingAI(true)
    setIsDropdownOpen(false)
    
    try {
      const response = await fetch('/api/ai/suggest-universities', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, existingUniversities: value }),
        signal: controller.signal
      })
      
      if (currentRequestId !== requestIdRef.current) return
      
      if (response.ok) {
        const data = await response.json()
        if (data.suggestions && data.suggestions.length > 0) {
          const newUniversities = data.suggestions
            .filter((u: string) => !existingUniversities.includes(u.toLowerCase()))
            .slice(0, 6)
          
          onChange([...value, ...newUniversities])
        }
      }
    } catch (error) {
      if ((error as Error).name !== 'AbortError') {
      }
    } finally {
      if (currentRequestId === requestIdRef.current) {
        setIsLoadingAI(false)
        setInputValue("")
      }
    }
  }, [value, onChange, existingUniversities])

  const findSimilarUniversities = useCallback(async () => {
    if (value.length === 0) return
    
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    
    const controller = new AbortController()
    abortControllerRef.current = controller
    const currentRequestId = ++requestIdRef.current
    
    setIsFindingSimilar(true)
    
    try {
      const response = await fetch('/api/ai/suggest-universities', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ universities: value, existingUniversities: value }),
        signal: controller.signal
      })
      
      if (currentRequestId !== requestIdRef.current) return
      
      if (response.ok) {
        const data = await response.json()
        if (data.suggestions && data.suggestions.length > 0) {
          const newUniversities = data.suggestions
            .filter((u: string) => !existingUniversities.includes(u.toLowerCase()))
            .slice(0, 6)
          onChange([...value, ...newUniversities])
        }
      }
    } catch (error) {
      if ((error as Error).name !== 'AbortError') {
      }
    } finally {
      if (currentRequestId === requestIdRef.current) {
        setIsFindingSimilar(false)
      }
    }
  }, [value, onChange, existingUniversities])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      if (focusedIndex >= 0 && dropdownItems[focusedIndex]) {
        const item = dropdownItems[focusedIndex]
        if (item.type === 'ai') {
          askAIForUniversities(inputValue)
        } else if (item.university) {
          addUniversity(item.university)
        }
      } else if (inputValue.trim()) {
        addUniversity(inputValue.trim())
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      setFocusedIndex(prev => Math.min(prev + 1, dropdownItems.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setFocusedIndex(prev => Math.max(prev - 1, -1))
    } else if (e.key === 'Escape') {
      setIsDropdownOpen(false)
      setFocusedIndex(-1)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value)
    setIsDropdownOpen(e.target.value.length > 0)
    setFocusedIndex(-1)
  }

  const handlePresetSelect = (universities: string[]) => {
    const newUniversities = universities.filter(
      u => !existingUniversities.includes(u.toLowerCase())
    )
    onChange([...value, ...newUniversities])
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {value.length > 0 && (
            <span className="text-xs text-lia-text-secondary">
              {value.length} universit{value.length !== 1 ? 'ies' : 'y'} selected
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={clearAll}
            className="text-xs text-lia-text-secondary hover:text-status-error flex items-center gap-1 transition-colors motion-reduce:transition-none"
          >
            <RotateCcw className="w-3 h-3" />
            Limpar tudo
          </button>
          <button 
            onClick={() => setShowSavePresetModal(true)}
            disabled={value.length === 0}
            className="text-xs text-lia-text-secondary hover:text-lia-text-primary flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Save className="w-3.5 h-3.5" />
            Salvar Preset
          </button>
          {showPresets && (
            <button 
              onClick={() => setIsPresetsModalOpen(true)}
              className="text-xs text-lia-text-secondary hover:text-lia-text-primary flex items-center gap-1"
            >
              <List className="w-3.5 h-3.5" />
              Presets
            </button>
          )}
        </div>
      </div>

      <div className="relative">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-lia-text-tertiary" />
          <Input
            ref={inputRef}
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={() => inputValue.length > 0 && setIsDropdownOpen(true)}
            placeholder={placeholder}
            className="pl-9 pr-3 border-lia-border-subtle focus:ring-1 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 focus:border-lia-border-medium"
            disabled={isLoadingAI}
          />
          {isLoadingAI && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
            </div>
          )}
        </div>

        {isDropdownOpen && dropdownItems.length > 0 && (
          <div 
            ref={dropdownRef}
            className="absolute z-50 w-full mt-1 bg-lia-bg-primary border border-lia-border-subtle rounded-xl max-h-64 overflow-y-auto"
          >
            {dropdownItems.map((item, index) => (
              <button
                key={`${item.type}-${item.label}`}
                onClick={() => {
                  if (item.type === 'ai') {
                    askAIForUniversities(inputValue)
                  } else if (item.university) {
                    addUniversity(item.university)
                  }
                }}
                className={cn("w-full text-left px-3 py-2 text-sm transition-colors",
                  focusedIndex === index ?"bg-lia-bg-tertiary" :"hover:bg-lia-bg-secondary",
                  item.type === 'ai' &&""
                )}
              >
                {item.type === 'ai' ? (
                  <div className="flex items-center gap-2 text-lia-text-secondary">
                    <Brain className="w-4 h-4 text-wedo-cyan" />
                    <span>{item.label}</span>
                  </div>
                ) : (
                  <span className="text-lia-text-primary">{item.label}</span>
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {value.length > 0 && (
        <div className="space-y-2">
          <div className="flex flex-wrap gap-2">
            {value.map(university => (
              <Chip variant="neutral" muted
                key={university}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-lia-bg-tertiary text-lia-text-primary border border-lia-border-subtle"
              >
                <span>{university}</span>
                <button
                  onClick={() => removeUniversity(university)}
                  className="hover:bg-lia-interactive-active rounded-md p-0.5 transition-colors motion-reduce:transition-none ml-1"
                  title="Remove"
                >
                  <X className="w-3 h-3" />
                </button>
              </Chip>
            ))}
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={findSimilarUniversities}
            disabled={isFindingSimilar || value.length === 0}
            className="text-xs gap-1.5 border-lia-btn-primary-bg dark:border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-tertiary dark:bg-lia-bg-secondary"
          >
            {isFindingSimilar ? (
              <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none" />
            ) : (
              <Brain className="w-3 h-3 text-wedo-cyan" />
            )}
            Find Similar
          </Button>
        </div>
      )}

      <UniversityPresetsModal
        isOpen={isPresetsModalOpen}
        onClose={() => setIsPresetsModalOpen(false)}
        onSelectPreset={handlePresetSelect}
      />

      {showSavePresetModal && (
        <div className="fixed inset-0 bg-lia-overlay flex items-center justify-center z-50" onClick={() => setShowSavePresetModal(false)}>
          <div className="bg-lia-bg-primary rounded-xl p-4 w-80" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-medium text-sm mb-3">Salvar Preset</h3>
            <Input
              value={savePresetName}
              onChange={(e) => setSavePresetName(e.target.value)}
              placeholder="Nome do preset"
              className="mb-3"
            />
            <div className="flex justify-end gap-2">
              <Button variant="outline" size="sm" onClick={() => setShowSavePresetModal(false)}>
                Cancelar
              </Button>
              <Button 
                size="sm" 
                onClick={handleSaveCustomPreset}
                disabled={!savePresetName.trim()}
                className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
              >
                <Save className="w-3.5 h-3.5 mr-1.5" />
                Salvar
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default UniversitiesFilterInput
