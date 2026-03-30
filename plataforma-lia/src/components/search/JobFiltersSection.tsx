"use client"

import { useState, useRef } from "react"
import {
  X, ChevronRight, Check, Clock, RotateCcw, Save,
  Zap, Brain, Loader2, Info, List, TrendingUp
} from "lucide-react"
import { cn } from "@/lib/utils"
import { badgeStyles } from '@/lib/design-tokens'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { useSemanticSearch } from "@/hooks/useSemanticSearch"
import type { SearchFilters } from './hooks/useAdvancedFiltersCore'

const globalJobPresets = [
  { 
    id: "customer_success", 
    name: "Sucesso do Cliente", 
    description: "Funções de sucesso do cliente e suporte",
    titles: ["Customer Success Manager", "Senior Customer Success Manager", "Customer Success Specialist", "Customer Support Specialist", "Customer Success Engineer", "Solutions Engineer", "Technical Account Manager", "Director of Customer Success", "Vice President of Customer Success", "Head of Customer Success"]
  },
  { 
    id: "data_analytics", 
    name: "Dados & Analytics", 
    description: "Ciência de dados, analytics e engenharia de dados",
    titles: ["Data Scientist", "Senior Data Scientist", "Machine Learning Engineer", "Senior Machine Learning Engineer", "Data Analyst", "Senior Data Analyst", "Data Engineer", "Senior Data Engineer", "Analytics Engineer", "Head of Data"]
  },
  { 
    id: "design", 
    name: "Design", 
    description: "Design de produto, UX/UI e liderança de design",
    titles: ["Product Designer", "Senior Product Designer", "UX Designer", "UI Designer", "UX Researcher", "Design Lead", "Head of Design", "Vice President of Design", "Design Director", "Creative Director", "Brand Designer"]
  },
  { 
    id: "devops", 
    name: "DevOps & Infraestrutura", 
    description: "DevOps, SRE e engenharia de infraestrutura",
    titles: ["DevOps Engineer", "Senior DevOps Engineer", "Site Reliability Engineer", "SRE", "Platform Engineer", "Senior Platform Engineer", "Systems Engineer", "Infrastructure Engineer", "Cloud Engineer", "Head of Infrastructure"]
  },
  { 
    id: "engineering", 
    name: "Engenharia de Software", 
    description: "Desenvolvimento de software e liderança técnica",
    titles: ["Software Engineer", "Senior Software Engineer", "Staff Software Engineer", "Principal Software Engineer", "Frontend Developer", "Backend Developer", "Fullstack Developer", "Tech Lead", "Engineering Manager", "Director of Engineering", "VP of Engineering", "CTO"]
  },
  { 
    id: "product", 
    name: "Produto", 
    description: "Gestão de produto e estratégia",
    titles: ["Product Manager", "Senior Product Manager", "Group Product Manager", "Director of Product", "Vice President of Product", "Head of Product", "Chief Product Officer", "Product Owner", "Technical Product Manager"]
  },
  { 
    id: "sales", 
    name: "Comercial & Vendas", 
    description: "Vendas, desenvolvimento de negócios e parcerias",
    titles: ["Sales Representative", "Account Executive", "Senior Account Executive", "Sales Manager", "Sales Director", "Vice President of Sales", "Business Development Representative", "BDR", "SDR", "Head of Sales", "Chief Revenue Officer"]
  },
  { 
    id: "marketing", 
    name: "Marketing", 
    description: "Marketing digital, growth e comunicação",
    titles: ["Marketing Manager", "Senior Marketing Manager", "Marketing Director", "Head of Marketing", "VP of Marketing", "CMO", "Growth Marketing Manager", "Digital Marketing Specialist", "Content Marketing Manager", "Brand Manager"]
  }
]

export const JobFiltersSection = ({
  filters, 
  updateFilter, 
  addToArray, 
  removeFromArray 
}: { 
  filters: SearchFilters
  updateFilter: <T extends keyof SearchFilters>(category: T, key: keyof NonNullable<SearchFilters[T]>, value: string | string[] | number | boolean | null) => void
  addToArray: <T extends keyof SearchFilters>(category: T, key: keyof NonNullable<SearchFilters[T]>, value: string) => void
  removeFromArray: <T extends keyof SearchFilters>(category: T, key: keyof NonNullable<SearchFilters[T]>, value: string) => void
}) => {
  const [titleInput, setTitleInput] = useState("")
  const [pastTitleInput, setPastTitleInput] = useState("")
  const [roleInput, setRoleInput] = useState("")
  const [isLoadingSimilar, setIsLoadingSimilar] = useState(false)
  const [showPresetsModal, setShowPresetsModal] = useState(false)
  const [showSavePresetModal, setShowSavePresetModal] = useState(false)
  const [savePresetName, setSavePresetName] = useState("")
  const [savePresetDescription, setSavePresetDescription] = useState("")
  const [customPresets, setCustomPresets] = useState<Array<{id: string, name: string, description: string, titles: string[]}>>([])
  const [selectedPreset, setSelectedPreset] = useState<typeof globalJobPresets[0] | null>(null)
  const [presetTarget, setPresetTarget] = useState<"titles" | "pastTitles">("titles")
  const [aiSuggestedTitles, setAiSuggestedTitles] = useState<string[]>([])
  const [selectedAiTitles, setSelectedAiTitles] = useState<string[]>([])
  const [isLoadingSimilarPastTitles, setIsLoadingSimilarPastTitles] = useState(false)
  const [aiSuggestedPastTitles, setAiSuggestedPastTitles] = useState<string[]>([])
  const [selectedAiPastTitles, setSelectedAiPastTitles] = useState<string[]>([])
  const [showTitleSuggestions, setShowTitleSuggestions] = useState(false)
  const [showPastTitleSuggestions, setShowPastTitleSuggestions] = useState(false)
  const [showRoleSuggestions, setShowRoleSuggestions] = useState(false)
  const titleInputRef = useRef<HTMLInputElement>(null)
  const pastTitleInputRef = useRef<HTMLInputElement>(null)
  const roleInputRef = useRef<HTMLInputElement>(null)

  const { 
    suggestions: titleSuggestions, 
    isLoading: isLoadingTitles, 
    search: searchTitles,
    clearSuggestions: clearTitleSuggestions
  } = useSemanticSearch({ domain: "job-titles", debounceMs: 400 })

  const { 
    suggestions: roleSuggestions, 
    isLoading: isLoadingRoles, 
    search: searchRoles,
    clearSuggestions: clearRoleSuggestions
  } = useSemanticSearch({ domain: "roles", debounceMs: 400 })

  const handleAddTitle = (title: string) => {
    if (title.trim()) {
      addToArray("job", "titles", title.trim())
      setTitleInput("")
      clearTitleSuggestions()
      setShowTitleSuggestions(false)
    }
  }

  const handleAddPastTitle = (title: string) => {
    if (title.trim()) {
      addToArray("job", "pastTitles", title.trim())
      setPastTitleInput("")
      clearTitleSuggestions()
      setShowPastTitleSuggestions(false)
    }
  }

  const handleAddRole = (role: string) => {
    if (role.trim()) {
      addToArray("job", "roles", role.trim())
      setRoleInput("")
      clearRoleSuggestions()
      setShowRoleSuggestions(false)
    }
  }

  const handleTitleInputChange = (value: string) => {
    setTitleInput(value)
    if (value.trim().length >= 2) {
      searchTitles(value, filters.job?.titles || [])
      setShowTitleSuggestions(true)
    } else {
      clearTitleSuggestions()
      setShowTitleSuggestions(false)
    }
  }

  const handlePastTitleInputChange = (value: string) => {
    setPastTitleInput(value)
    if (value.trim().length >= 2) {
      searchTitles(value, filters.job?.pastTitles || [])
      setShowPastTitleSuggestions(true)
    } else {
      clearTitleSuggestions()
      setShowPastTitleSuggestions(false)
    }
  }

  const handleRoleInputChange = (value: string) => {
    setRoleInput(value)
    if (value.trim().length >= 2) {
      searchRoles(value, filters.job?.roles || [])
      setShowRoleSuggestions(true)
    } else {
      clearRoleSuggestions()
      setShowRoleSuggestions(false)
    }
  }

  const handleFindSimilar = async () => {
    const currentTitles = filters.job?.titles || []
    if (currentTitles.length === 0) return
    
    setIsLoadingSimilar(true)
    try {
      const response = await fetch('/api/ai/suggest-similar-titles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ titles: currentTitles })
      })
      
      if (response.ok) {
        const data = await response.json()
        const suggestions = data.suggestions || []
        setAiSuggestedTitles(suggestions.filter((s: string) => !currentTitles.includes(s)))
      } else {
        const similarTitles = generateLocalSimilarTitles(currentTitles)
        setAiSuggestedTitles(similarTitles.filter(s => !currentTitles.includes(s)))
      }
    } catch (error) {
      const similarTitles = generateLocalSimilarTitles(currentTitles)
      setAiSuggestedTitles(similarTitles.filter(s => !currentTitles.includes(s)))
    }
    setIsLoadingSimilar(false)
  }

  const generateLocalSimilarTitles = (titles: string[]): string[] => {
    const suggestions: string[] = []
    const seniorityPrefixes = ["Junior", "Senior", "Staff", "Principal", "Lead", "Head of"]
    
    titles.forEach(title => {
      const cleanTitle = title.replace(/^(Junior|Senior|Staff|Principal|Lead|Head of)\s*/i, "")
      seniorityPrefixes.forEach(prefix => {
        const newTitle = `${prefix} ${cleanTitle}`
        if (!titles.includes(newTitle) && !suggestions.includes(newTitle)) {
          suggestions.push(newTitle)
        }
      })
    })
    
    return suggestions.slice(0, 8)
  }

  const handleApplyPreset = (preset: typeof globalJobPresets[0], target: "titles" | "pastTitles" = "titles") => {
    const currentArray = target === "titles" ? filters.job?.titles : filters.job?.pastTitles
    preset.titles.forEach(title => {
      if (!currentArray?.includes(title)) {
        addToArray("job", target, title)
      }
    })
    setShowPresetsModal(false)
    setSelectedPreset(null)
    setPresetTarget("titles")
  }

  const handleSavePreset = () => {
    const currentTitles = presetTarget === "titles" 
      ? (filters.job?.titles || []) 
      : (filters.job?.pastTitles || [])
    if (currentTitles.length === 0 || !savePresetName.trim()) return
    
    const newPreset = {
      id: `custom_${Date.now()}`,
      name: savePresetName.trim(),
      description: savePresetDescription.trim() || `Preset com ${currentTitles.length} cargos`,
      titles: [...currentTitles]
    }
    
    setCustomPresets(prev => [...prev, newPreset])
    setSavePresetName("")
    setSavePresetDescription("")
    setShowSavePresetModal(false)
    setPresetTarget("titles")
  }

  const handleClearAllJobFilters = () => {
    updateFilter("job", "titles", [] as string[])
    updateFilter("job", "pastTitles", [] as string[])
    updateFilter("job", "levels", [] as string[])
    updateFilter("job", "roles", [] as string[])
    updateFilter("job", "titleScope", "current_only")
    updateFilter("job", "timeInRoleMin", "no_limit")
    updateFilter("job", "timeInRoleMax", "no_limit")
    updateFilter("job", "minAverageTenure", "no_limit")
    setAiSuggestedTitles([])
    setSelectedAiTitles([])
    setAiSuggestedPastTitles([])
    setSelectedAiPastTitles([])
  }

  const toggleAiTitleSelection = (title: string) => {
    if (selectedAiTitles.includes(title)) {
      setSelectedAiTitles(prev => prev.filter(t => t !== title))
    } else {
      setSelectedAiTitles(prev => [...prev, title])
    }
  }

  const handleAddSelectedAiTitles = () => {
    selectedAiTitles.forEach(title => {
      addToArray("job", "titles", title)
    })
    setAiSuggestedTitles(prev => prev.filter(t => !selectedAiTitles.includes(t)))
    setSelectedAiTitles([])
  }

  const handleFindSimilarPastTitles = async () => {
    const pastTitles = filters.job?.pastTitles || []
    if (pastTitles.length === 0) return
    
    setIsLoadingSimilarPastTitles(true)
    try {
      const response = await fetch('/api/ai/suggest-similar-titles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ titles: pastTitles })
      })
      
      if (response.ok) {
        const data = await response.json()
        const suggestions = data.suggestions || []
        setAiSuggestedPastTitles(suggestions.filter((s: string) => !pastTitles.includes(s)))
      } else {
        const similarTitles = generateLocalSimilarTitles(pastTitles)
        setAiSuggestedPastTitles(similarTitles.filter(s => !pastTitles.includes(s)))
      }
    } catch (error) {
      const similarTitles = generateLocalSimilarTitles(pastTitles)
      setAiSuggestedPastTitles(similarTitles.filter(s => !pastTitles.includes(s)))
    }
    setIsLoadingSimilarPastTitles(false)
  }

  const toggleAiPastTitleSelection = (title: string) => {
    if (selectedAiPastTitles.includes(title)) {
      setSelectedAiPastTitles(prev => prev.filter(t => t !== title))
    } else {
      setSelectedAiPastTitles(prev => [...prev, title])
    }
  }

  const handleAddSelectedAiPastTitles = () => {
    selectedAiPastTitles.forEach(title => {
      addToArray("job", "pastTitles", title)
    })
    setAiSuggestedPastTitles(prev => prev.filter(t => !selectedAiPastTitles.includes(t)))
    setSelectedAiPastTitles([])
  }

  return (
    <div className="space-y-6">
      {/* Job Titles Section */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Label className="text-xs font-medium">Cargos Atuais</Label>
            <Select
              value={filters.job?.titleScope || "current_only"}
              onValueChange={(value) => updateFilter("job", "titleScope", value as "current_only" | "current_recent" | "current_past")}
            >
              <SelectTrigger className="h-7 w-[150px] text-xs border-lia-border-subtle">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-lia-bg-secondary">
                {titleScopeOptions.map(option => (
                  <SelectItem key={option.value} value={option.value} className="text-xs">
                    <div>
                      <div className="font-medium">{option.label}</div>
                      <div className="text-micro lia-text-500">{option.description}</div>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-3">
            <button 
              onClick={handleClearAllJobFilters}
              className="text-xs lia-text-500 hover:text-status-error flex items-center gap-1 transition-colors"
            >
              <RotateCcw className="w-3 h-3" />
              Limpar tudo
            </button>
            <button 
              onClick={() => {
                setSavePresetName(`Novo Preset (${new Date().toLocaleDateString('pt-BR')})`)
                setShowSavePresetModal(true)
              }}
              disabled={(filters.job?.titles?.length || 0) === 0}
              className="text-xs lia-text-600 hover:lia-text-800 flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save className="w-3.5 h-3.5" />
              Salvar Preset
            </button>
            <button 
              onClick={() => setShowPresetsModal(true)}
              className="text-xs lia-text-600 hover:lia-text-800 flex items-center gap-1"
            >
              <List className="w-3.5 h-3.5" />
              Presets
            </button>
          </div>
        </div>

        {/* Title Input */}
        <div className="relative">
          <div className="relative">
            <Input
              ref={titleInputRef}
              value={titleInput}
              onChange={(e) => handleTitleInputChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && titleInput.trim()) {
                  e.preventDefault()
                  handleAddTitle(titleInput)
                } else if (e.key === "Escape") {
                  setShowTitleSuggestions(false)
                }
              }}
              onFocus={() => titleInput.length >= 2 && setShowTitleSuggestions(true)}
              onBlur={() => setTimeout(() => setShowTitleSuggestions(false), 200)}
              placeholder="Digite cargo e pressione Enter (ex: Software Engineer, Product Manager)"
              className="border border-lia-border-subtle focus:ring-1 focus:ring-gray-400 pr-10"
            />
            {isLoadingTitles && (
              <div className="absolute right-3 top-1/2 -translate-y-1/2">
                <Loader2 className="w-4 h-4 lia-text-500 animate-spin" />
              </div>
            )}
          </div>
          
          {/* Semantic Suggestions Dropdown */}
          {showTitleSuggestions && titleSuggestions.length > 0 && (
            <div className="absolute z-50 mt-1 w-full bg-lia-bg-primary border border-lia-border-subtle rounded-md max-h-48 overflow-y-auto">
              <div className="p-1.5 border-b border-lia-border-subtle dark:border-lia-border-subtle">
                <div className="flex items-center gap-1.5 text-micro lia-text-600 dark:text-lia-text-tertiary">
                  <Zap className="w-3 h-3" />
                  <span>Sugestões semânticas</span>
                </div>
              </div>
              {titleSuggestions.map((suggestion) => (
                <button
                  key={suggestion.term}
                  onMouseDown={(e) => {
                    e.preventDefault()
                    handleAddTitle(suggestion.term)
                  }}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 flex items-center justify-between gap-2"
                >
                  <span>{suggestion.term}</span>
                  <span className="text-micro lia-text-400">
                    {Math.round(suggestion.confidence * 100)}%
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Selected Titles */}
        {(filters.job?.titles?.length || 0) > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {filters.job?.titles?.map((title) => {
              const isAiSuggested = aiSuggestedTitles.includes(title)
              return (
                <Badge
                  key={title}
                  variant="secondary"
                  className={cn(
                    "pl-2 pr-1 py-1 flex items-center gap-1",
                    isAiSuggested 
                      ? "bg-wedo-purple/10 border border-wedo-purple/30 text-wedo-purple" 
                      : "bg-gray-100 lia-text-800 dark:text-lia-text-primary"
                  )}
                >
                  {isAiSuggested && <Brain className="w-3 h-3 text-wedo-purple" />}
                  <span className="text-xs">{title}</span>
                  <button
                    onClick={() => removeFromArray("job", "titles", title)}
                    className="ml-1 hover:bg-gray-300 rounded-md p-0.5"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </Badge>
              )
            })}
            
            {/* Find Similar Button */}
            <button
              onClick={handleFindSimilar}
              disabled={isLoadingSimilar || (filters.job?.titles?.length || 0) === 0}
              className={cn(
                "px-3 py-1 rounded-full text-xs border flex items-center gap-1.5 transition-[width,height]",
                "border-wedo-purple/30 bg-wedo-purple/10 text-wedo-purple hover:bg-wedo-purple/15",
                "disabled:opacity-50 disabled:cursor-not-allowed"
              )}
            >
              {isLoadingSimilar ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : (
                <Brain className="w-3 h-3 text-wedo-cyan" />
              )}
              Buscar Similares
            </button>
          </div>
        )}

        {/* AI Suggestions with Multi-Select */}
        {aiSuggestedTitles.length > 0 && (
          <div className="p-3 rounded-md border border-wedo-purple/30 bg-wedo-purple/10/50">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Brain className="w-4 h-4 text-wedo-purple" />
                <span className="text-xs font-medium text-wedo-purple">Sugestões da LIA</span>
                <span className="text-micro text-wedo-purple">
                  (clique para selecionar múltiplos)
                </span>
              </div>
              {selectedAiTitles.length > 0 && (
                <button
                  onClick={handleAddSelectedAiTitles}
                  className="px-2 py-1 rounded-md text-xs bg-gray-900 text-white hover:bg-gray-800 dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200 transition-colors flex items-center gap-1"
                >
                  <Check className="w-3 h-3" />
                  Adicionar {selectedAiTitles.length} selecionado{selectedAiTitles.length > 1 ? 's' : ''}
                </button>
              )}
            </div>
            <div className="flex flex-wrap gap-1.5">
              {aiSuggestedTitles.slice(0, 10).map((title) => {
                const isSelected = selectedAiTitles.includes(title)
                return (
                  <button
                    key={title}
                    onClick={() => toggleAiTitleSelection(title)}
                    className={cn(
                      "px-2 py-1 rounded-md text-xs border transition-colors flex items-center gap-1",
                      isSelected
                        ? "border-wedo-purple/30 bg-wedo-purple/15 text-wedo-purple font-medium"
                        : "border-wedo-purple/30 bg-lia-bg-primary text-wedo-purple hover:bg-wedo-purple/10"
                    )}
                  >
                    {isSelected && <Check className="w-3 h-3" />}
                    {!isSelected && <span className="text-wedo-purple">+</span>}
                    {title}
                  </button>
                )
              })}
            </div>
          </div>
        )}
      </div>

      {/* Time in Role & Average Tenure */}
      <div className="grid grid-cols-2 gap-4">
        <div className="p-3 rounded-md border border-lia-border-subtle dark:border-lia-border-subtle">
          <div className="flex items-center gap-1.5 mb-2">
            <Clock className="w-4 h-4 lia-text-500" />
            <Label className="text-xs font-medium">Tempo na Função Atual</Label>
            <Popover>
              <PopoverTrigger asChild>
                <button className="lia-text-400 hover:lia-text-600">
                  <Info className="w-3 h-3" />
                </button>
              </PopoverTrigger>
              <PopoverContent className="w-64 p-2 bg-lia-bg-elevated text-xs">
                Filtrar candidatos pelo tempo que estão no cargo atual
              </PopoverContent>
            </Popover>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs lia-text-500">Entre</span>
            <Select
              value={filters.job?.timeInRoleMin || "no_limit"}
              onValueChange={(value) => updateFilter("job", "timeInRoleMin", value)}
            >
              <SelectTrigger className="h-7 flex-1 text-xs border-lia-border-subtle">
                <SelectValue placeholder="Sem limite" />
              </SelectTrigger>
              <SelectContent className="bg-lia-bg-secondary">
                {timeInRoleOptions.map(opt => (
                  <SelectItem key={opt.value} value={opt.value} className="text-xs">
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <span className="text-xs lia-text-500">e</span>
            <Select
              value={filters.job?.timeInRoleMax || "no_limit"}
              onValueChange={(value) => updateFilter("job", "timeInRoleMax", value)}
            >
              <SelectTrigger className="h-7 flex-1 text-xs border-lia-border-subtle">
                <SelectValue placeholder="Sem limite" />
              </SelectTrigger>
              <SelectContent className="bg-lia-bg-secondary">
                {timeInRoleOptions.map(opt => (
                  <SelectItem key={opt.value} value={opt.value} className="text-xs">
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="p-3 rounded-md border border-lia-border-subtle dark:border-lia-border-subtle">
          <div className="flex items-center gap-1.5 mb-2">
            <TrendingUp className="w-4 h-4 lia-text-500" />
            <Label className="text-xs font-medium">Tempo Médio nas Empresas</Label>
            <Popover>
              <PopoverTrigger asChild>
                <button className="lia-text-400 hover:lia-text-600">
                  <Info className="w-3 h-3" />
                </button>
              </PopoverTrigger>
              <PopoverContent className="w-64 p-2 bg-lia-bg-elevated text-xs">
                Candidatos com média de permanência mínima em cada empresa
              </PopoverContent>
            </Popover>
          </div>
          <Select
            value={filters.job?.minAverageTenure || "no_limit"}
            onValueChange={(value) => updateFilter("job", "minAverageTenure", value)}
          >
            <SelectTrigger className="h-7 text-xs border-lia-border-subtle">
              <SelectValue placeholder="Selecionar duração" />
            </SelectTrigger>
            <SelectContent className="bg-lia-bg-secondary">
              {tenureOptions.map(opt => (
                <SelectItem key={opt.value} value={opt.value} className="text-xs">
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Past Job Titles */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <Label className="text-xs font-medium">Cargos Anteriores</Label>
            <Popover>
              <PopoverTrigger asChild>
                <button className="lia-text-400 hover:lia-text-600">
                  <Info className="w-3 h-3" />
                </button>
              </PopoverTrigger>
              <PopoverContent className="w-64 p-2 bg-lia-bg-elevated text-xs">
                Buscar candidatos que já tiveram estes cargos em algum momento da carreira
              </PopoverContent>
            </Popover>
          </div>
          <div className="flex items-center gap-3">
            <button 
              onClick={() => updateFilter("job", "pastTitles", [] as string[])}
              disabled={(filters.job?.pastTitles?.length || 0) === 0}
              className="text-xs lia-text-500 hover:text-status-error flex items-center gap-1 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RotateCcw className="w-3 h-3" />
              Limpar tudo
            </button>
            <button 
              onClick={() => {
                setSavePresetName(`Novo Preset (${new Date().toLocaleDateString('pt-BR')})`)
                setPresetTarget("pastTitles")
                setShowSavePresetModal(true)
              }}
              disabled={(filters.job?.pastTitles?.length || 0) === 0}
              className="text-xs lia-text-600 hover:lia-text-800 flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save className="w-3.5 h-3.5" />
              Salvar Preset
            </button>
            <button 
              onClick={() => setShowPresetsModal(true)}
              className="text-xs lia-text-600 hover:lia-text-800 flex items-center gap-1"
            >
              <List className="w-3.5 h-3.5" />
              Presets
            </button>
          </div>
        </div>
        <div className="relative">
          <div className="relative">
            <Input
              ref={pastTitleInputRef}
              value={pastTitleInput}
              onChange={(e) => handlePastTitleInputChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && pastTitleInput.trim()) {
                  e.preventDefault()
                  handleAddPastTitle(pastTitleInput)
                } else if (e.key === "Escape") {
                  setShowPastTitleSuggestions(false)
                }
              }}
              onFocus={() => pastTitleInput.length >= 2 && setShowPastTitleSuggestions(true)}
              onBlur={() => setTimeout(() => setShowPastTitleSuggestions(false), 200)}
              placeholder="Digite cargo anterior e pressione Enter"
              className="border border-lia-border-subtle focus:ring-1 focus:ring-gray-400 pr-10"
            />
            {isLoadingTitles && showPastTitleSuggestions && (
              <div className="absolute right-3 top-1/2 -translate-y-1/2">
                <Loader2 className="w-4 h-4 lia-text-500 animate-spin" />
              </div>
            )}
          </div>
          
          {/* Semantic Suggestions Dropdown for Past Titles */}
          {showPastTitleSuggestions && titleSuggestions.length > 0 && (
            <div className="absolute z-50 mt-1 w-full bg-lia-bg-primary border border-lia-border-subtle rounded-md max-h-48 overflow-y-auto">
              <div className="p-1.5 border-b border-lia-border-subtle dark:border-lia-border-subtle">
                <div className="flex items-center gap-1.5 text-micro lia-text-600 dark:text-lia-text-tertiary">
                  <Zap className="w-3 h-3" />
                  <span>Sugestões semânticas</span>
                </div>
              </div>
              {titleSuggestions.map((suggestion) => (
                <button
                  key={suggestion.term}
                  onMouseDown={(e) => {
                    e.preventDefault()
                    handleAddPastTitle(suggestion.term)
                  }}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 flex items-center justify-between gap-2"
                >
                  <span>{suggestion.term}</span>
                  <span className="text-micro lia-text-400">
                    {Math.round(suggestion.confidence * 100)}%
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
        {(filters.job?.pastTitles?.length || 0) > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {filters.job?.pastTitles?.map((title) => {
              const isAiSuggested = aiSuggestedPastTitles.includes(title)
              return (
                <Badge
                  key={title}
                  variant="secondary"
                  className={cn(
                    "pl-2 pr-1 py-1 flex items-center gap-1",
                    isAiSuggested 
                      ? "bg-wedo-purple/10 border border-wedo-purple/30 text-wedo-purple" 
                      : "bg-gray-100 lia-text-800 dark:text-lia-text-primary"
                  )}
                >
                  {isAiSuggested && <Brain className="w-3 h-3 text-wedo-purple" />}
                  <span className="text-xs">{title}</span>
                  <button
                    onClick={() => removeFromArray("job", "pastTitles", title)}
                    className="ml-1 hover:bg-gray-300 rounded-md p-0.5"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </Badge>
              )
            })}
            
            <button
              onClick={handleFindSimilarPastTitles}
              disabled={isLoadingSimilarPastTitles || (filters.job?.pastTitles?.length || 0) === 0}
              className={cn(
                "px-3 py-1 rounded-full text-xs border flex items-center gap-1.5 transition-[width,height]",
                "border-wedo-purple/30 bg-wedo-purple/10 text-wedo-purple hover:bg-wedo-purple/15",
                "disabled:opacity-50 disabled:cursor-not-allowed"
              )}
            >
              {isLoadingSimilarPastTitles ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : (
                <Brain className="w-3 h-3 text-wedo-cyan" />
              )}
              Buscar Similares
            </button>
          </div>
        )}

        {aiSuggestedPastTitles.length > 0 && (
          <div className="p-3 rounded-md border border-wedo-purple/30 bg-wedo-purple/10/50">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Brain className="w-4 h-4 text-wedo-purple" />
                <span className="text-xs font-medium text-wedo-purple">Sugestões da LIA</span>
                <span className="text-micro text-wedo-purple">
                  (clique para selecionar múltiplos)
                </span>
              </div>
              {selectedAiPastTitles.length > 0 && (
                <button
                  onClick={handleAddSelectedAiPastTitles}
                  className="px-2 py-1 rounded-md text-xs bg-gray-900 text-white hover:bg-gray-800 dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200 transition-colors flex items-center gap-1"
                >
                  <Check className="w-3 h-3" />
                  Adicionar {selectedAiPastTitles.length} selecionado{selectedAiPastTitles.length > 1 ? 's' : ''}
                </button>
              )}
            </div>
            <div className="flex flex-wrap gap-1.5">
              {aiSuggestedPastTitles.slice(0, 10).map((title) => {
                const isSelected = selectedAiPastTitles.includes(title)
                return (
                  <button
                    key={title}
                    onClick={() => toggleAiPastTitleSelection(title)}
                    className={cn(
                      "px-2 py-1 rounded-md text-xs border transition-colors flex items-center gap-1",
                      isSelected
                        ? "border-wedo-purple/30 bg-wedo-purple/15 text-wedo-purple font-medium"
                        : "border-wedo-purple/30 bg-lia-bg-primary text-wedo-purple hover:bg-wedo-purple/10"
                    )}
                  >
                    {isSelected && <Check className="w-3 h-3" />}
                    {!isSelected && <span className="text-wedo-purple">+</span>}
                    {title}
                  </button>
                )
              })}
            </div>
          </div>
        )}
      </div>

      {/* Job Title Levels & Roles */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <div className="flex items-center gap-1.5">
            <Label className="text-xs font-medium">Níveis de Cargo</Label>
            <Popover>
              <PopoverTrigger asChild>
                <button className="lia-text-400 hover:lia-text-600">
                  <Info className="w-3 h-3" />
                </button>
              </PopoverTrigger>
              <PopoverContent className="w-64 p-2 bg-lia-bg-elevated text-xs">
                Filtrar por nível hierárquico do cargo
              </PopoverContent>
            </Popover>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {experienceLevels.map(level => {
              const isSelected = filters.job?.levels?.includes(level.value)
              return (
                <button
                  key={level.value}
                  onClick={() => {
                    if (isSelected) {
                      removeFromArray("job", "levels", level.value)
                    } else {
                      addToArray("job", "levels", level.value)
                    }
                  }}
                  className={cn(
                    "px-2.5 py-1 rounded-md text-xs border transition-colors",
                    isSelected 
                      ? "border-gray-400 bg-gray-100 lia-text-800 dark:text-lia-text-primary font-medium" 
                      : "border-lia-border-subtle hover:border-lia-border-default lia-text-600"
                  )}
                >
                  {level.label}
                </button>
              )
            })}
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center gap-1.5">
            <Label className="text-xs font-medium">Funções/Áreas</Label>
            <Popover>
              <PopoverTrigger asChild>
                <button className="lia-text-400 hover:lia-text-600">
                  <Info className="w-3 h-3" />
                </button>
              </PopoverTrigger>
              <PopoverContent className="w-64 p-2 bg-lia-bg-elevated text-xs">
                Filtrar por área funcional de atuação. Selecione da lista ou digite para adicionar uma área customizada.
              </PopoverContent>
            </Popover>
          </div>
          
          {/* Custom Role Input */}
          <div className="relative">
            <div className="relative">
              <Input
                ref={roleInputRef}
                value={roleInput}
                onChange={(e) => handleRoleInputChange(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && roleInput.trim()) {
                    e.preventDefault()
                    handleAddRole(roleInput)
                  } else if (e.key === "Escape") {
                    setShowRoleSuggestions(false)
                  }
                }}
                onFocus={() => roleInput.length >= 2 && setShowRoleSuggestions(true)}
                onBlur={() => setTimeout(() => setShowRoleSuggestions(false), 200)}
                placeholder="Digite área e pressione Enter"
                className="h-7 text-xs border border-lia-border-subtle focus:ring-1 focus:ring-gray-400"
              />
              {isLoadingRoles && (
                <div className="absolute right-2 top-1/2 -translate-y-1/2">
                  <Loader2 className="w-3 h-3 lia-text-500 animate-spin" />
                </div>
              )}
            </div>
            
            {/* Semantic Suggestions for Roles */}
            {showRoleSuggestions && roleSuggestions.length > 0 && (
              <div className="absolute z-50 mt-1 w-full bg-lia-bg-primary border border-lia-border-subtle rounded-md max-h-40 overflow-y-auto">
                <div className="p-1 border-b border-lia-border-subtle dark:border-lia-border-subtle">
                  <div className="flex items-center gap-1 text-micro lia-text-600 dark:text-lia-text-tertiary">
                    <Zap className="w-2.5 h-2.5" />
                    <span>Sugestões AI</span>
                  </div>
                </div>
                {roleSuggestions.map((suggestion) => (
                  <button
                    key={suggestion.term}
                    onMouseDown={(e) => {
                      e.preventDefault()
                      handleAddRole(suggestion.term)
                    }}
                    className="w-full text-left px-2 py-1.5 text-xs hover:bg-gray-50 flex items-center justify-between gap-2"
                  >
                    <span>{suggestion.term}</span>
                    <span className="text-micro lia-text-400">
                      {Math.round(suggestion.confidence * 100)}%
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Custom Roles (added by user) */}
          {(filters.job?.roles?.filter(r => !jobRoles.find(jr => jr.value === r))?.length || 0) > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {filters.job?.roles?.filter(r => !jobRoles.find(jr => jr.value === r)).map(role => (
                <Badge
                  key={role}
                  variant="secondary"
                  className="bg-wedo-purple/10 border border-wedo-purple/30 text-wedo-purple pl-2 pr-1 py-0.5 flex items-center gap-1"
                >
                  <span className="text-xs">{role}</span>
                  <button
                    onClick={() => removeFromArray("job", "roles", role)}
                    className="ml-1 hover:bg-wedo-purple/20 rounded-md p-0.5"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </Badge>
              ))}
            </div>
          )}

          {/* Predefined Roles */}
          <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto">
            {jobRoles.map(role => {
              const isSelected = filters.job?.roles?.includes(role.value)
              return (
                <button
                  key={role.value}
                  onClick={() => {
                    if (isSelected) {
                      removeFromArray("job", "roles", role.value)
                    } else {
                      addToArray("job", "roles", role.value)
                    }
                  }}
                  className={cn(
                    "px-2.5 py-1 rounded-md text-xs border transition-colors",
                    isSelected 
                      ? "border-gray-400 bg-gray-100 lia-text-800 dark:text-lia-text-primary font-medium" 
                      : "border-lia-border-subtle hover:border-lia-border-default lia-text-600"
                  )}
                >
                  {role.label}
                </button>
              )
            })}
          </div>
        </div>
      </div>

      {/* Presets Modal */}
      {showPresetsModal && (
        <div className="fixed inset-0 z-overlay flex items-center justify-center">
          <div className="absolute inset-0 bg-black/50 backdrop-blur-[1px]" onClick={() => { setShowPresetsModal(false); setSelectedPreset(null) }} />
          <div className="relative bg-white rounded-md w-full max-w-lg max-h-[70vh] overflow-hidden dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
            <div className="flex items-center justify-between p-4 border-b border-lia-border-subtle dark:border-lia-border-subtle">
              <div className="flex items-center gap-2">
                {selectedPreset && (
                  <button 
                    onClick={() => setSelectedPreset(null)} 
                    className="lia-text-500 hover:lia-text-700"
                  >
                    <ChevronRight className="w-4 h-4 rotate-180" />
                  </button>
                )}
                <h3 className="font-medium lia-text-800">
                  {selectedPreset ? `${selectedPreset.name} (${selectedPreset.titles.length})` : "Presets de Cargos"}
                </h3>
              </div>
              <div className="flex items-center gap-2">
                {selectedPreset && (
                  <>
                    <Select
                      value={presetTarget}
                      onValueChange={(value) => setPresetTarget(value as "titles" | "pastTitles")}
                    >
                      <SelectTrigger className="h-8 w-[140px] text-xs border-lia-border-subtle">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-lia-bg-secondary">
                        <SelectItem value="titles" className="text-xs">Cargos Atuais</SelectItem>
                        <SelectItem value="pastTitles" className="text-xs">Cargos Anteriores</SelectItem>
                      </SelectContent>
                    </Select>
                    <Button
                      size="sm"
                      onClick={() => handleApplyPreset(selectedPreset, presetTarget)}
                      className="bg-gray-900 hover:bg-gray-800 text-white dark:lia-bg-100 dark:lia-text-900 dark:hover:bg-gray-200"
                    >
                      Aplicar Preset
                    </Button>
                  </>
                )}
                <button onClick={() => { setShowPresetsModal(false); setSelectedPreset(null); setPresetTarget("titles") }} className="lia-text-400 hover:lia-text-600">
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
            
            <div className="p-4 overflow-y-auto max-h-[calc(70vh-60px)]">
              {!selectedPreset ? (
                <div className="space-y-4">
                  {/* Custom Presets */}
                  {customPresets.length > 0 && (
                    <div>
                      <h4 className="text-xs font-medium lia-text-800 dark:text-lia-text-primary mb-2">Meus Presets</h4>
                      <p className="text-xs lia-text-500 mb-3">Presets criados por você</p>
                      <div className="space-y-2">
                        {customPresets.map(preset => (
                          <button
                            key={preset.id}
                            onClick={() => setSelectedPreset(preset)}
                            className="w-full text-left p-3 rounded-md border border-wedo-purple/30 hover:border-wedo-purple/30 hover:bg-wedo-purple/10/50 transition-colors"
                          >
                            <div className="flex items-center justify-between">
                              <div>
                                <div className="font-medium text-xs lia-text-800 flex items-center gap-1.5">
                                  <Save className="w-3.5 h-3.5 text-wedo-purple" />
                                  {preset.name}
                                </div>
                                <div className="text-xs lia-text-500 mt-0.5">{preset.description}</div>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-wedo-purple">+{preset.titles.length} cargos</span>
                                <ChevronRight className="w-4 h-4 lia-text-400" />
                              </div>
                            </div>
                            <div className="flex flex-wrap gap-1 mt-2">
                              {preset.titles.slice(0, 3).map(title => (
                                <span key={title} className="text-micro px-1.5 py-0.5 bg-wedo-purple/15 rounded-full text-wedo-purple">
                                  {title}
                                </span>
                              ))}
                              {preset.titles.length > 3 && (
                                <span className="text-micro text-wedo-purple">...</span>
                              )}
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Global Presets */}
                  <div>
                    <h4 className="text-xs font-medium lia-text-800 dark:text-lia-text-primary mb-2">Presets Globais</h4>
                    <p className="text-xs lia-text-500 mb-3">Conjuntos pré-definidos de cargos por área</p>
                    <div className="space-y-2">
                      {globalJobPresets.map(preset => (
                        <button
                          key={preset.id}
                          onClick={() => setSelectedPreset(preset)}
                          className="w-full text-left p-3 rounded-md border border-lia-border-subtle dark:border-lia-border-subtle hover:border-lia-border-subtle hover:bg-gray-50 transition-colors"
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="font-medium text-xs lia-text-800">{preset.name}</div>
                              <div className="text-xs lia-text-500 mt-0.5">{preset.description}</div>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-xs lia-text-400">+{preset.titles.length} cargos</span>
                              <ChevronRight className="w-4 h-4 lia-text-400" />
                            </div>
                          </div>
                          <div className="flex flex-wrap gap-1 mt-2">
                            {preset.titles.slice(0, 3).map(title => (
                              <span key={title} className="text-micro px-1.5 py-0.5 bg-gray-100 rounded-full lia-text-600">
                                {title}
                              </span>
                            ))}
                            {preset.titles.length > 3 && (
                              <span className="text-micro lia-text-400">...</span>
                            )}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {selectedPreset.titles.map(title => (
                    <span key={title} className="px-3 py-1.5 bg-gray-100 rounded-md text-xs lia-text-800 dark:text-lia-text-primary">
                      {title}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Save Preset Modal */}
      {showSavePresetModal && (
        <div className="fixed inset-0 z-overlay flex items-center justify-center">
          <div className="absolute inset-0 bg-black/50 backdrop-blur-[1px]" onClick={() => setShowSavePresetModal(false)} />
          <div className="relative bg-white rounded-md w-full max-w-md p-4 dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
            <h3 className="font-medium lia-text-800 mb-4">Salvar como Preset</h3>
            
            <div className="space-y-4">
              <div>
                <Label className="text-xs font-medium lia-text-600 mb-1 block">Nome do Preset</Label>
                <Input
                  value={savePresetName}
                  onChange={(e) => setSavePresetName(e.target.value)}
                  placeholder="Ex: Product Managers"
                  className="border border-lia-border-subtle"
                />
              </div>
              
              <div>
                <Label className="text-xs font-medium lia-text-600 mb-1 block">Descrição</Label>
                <Input
                  value={savePresetDescription}
                  onChange={(e) => setSavePresetDescription(e.target.value)}
                  placeholder="Descrição opcional"
                  className="border border-lia-border-subtle"
                />
              </div>

              <div className="p-3 rounded-md bg-gray-50 border border-lia-border-subtle dark:border-lia-border-subtle">
                <div className="text-xs lia-text-600 mb-2">
                  {(presetTarget === "titles" ? filters.job?.titles?.length : filters.job?.pastTitles?.length) || 0} cargos {presetTarget === "pastTitles" ? "anteriores " : ""}serão salvos:
                </div>
                <div className="flex flex-wrap gap-1 max-h-24 overflow-y-auto">
                  {(presetTarget === "titles" ? filters.job?.titles : filters.job?.pastTitles)?.slice(0, 10).map(title => (
                    <span key={title} className="text-micro px-1.5 py-0.5 bg-gray-200 rounded-full lia-text-800 dark:text-lia-text-primary">
                      {title}
                    </span>
                  ))}
                  {((presetTarget === "titles" ? filters.job?.titles?.length : filters.job?.pastTitles?.length) || 0) > 10 && (
                    <span className="text-micro lia-text-400">+{((presetTarget === "titles" ? filters.job?.titles?.length : filters.job?.pastTitles?.length) || 0) - 10} mais</span>
                  )}
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => { setShowSavePresetModal(false); setPresetTarget("titles") }}
              >
                Cancelar
              </Button>
              <Button
                size="sm"
                onClick={handleSavePreset}
                disabled={!savePresetName.trim() || ((presetTarget === "titles" ? filters.job?.titles?.length : filters.job?.pastTitles?.length) || 0) === 0}
                className="bg-gray-900 hover:bg-gray-800 text-white dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200"
              >
                <Save className="w-3.5 h-3.5 mr-1.5" />
                Salvar Preset
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

const TagInput = ({ 
  value = [], 
  onAdd, 
  onRemove, 
  placeholder 
}: { 
  value: string[]
  onAdd: (val: string) => void
  onRemove: (val: string) => void
  placeholder: string
}) => {
  const [inputValue, setInputValue] = useState("")
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && inputValue.trim()) {
      e.preventDefault()
      onAdd(inputValue)
      setInputValue("")
    }
  }

  return (
    <div className="space-y-2">
      <Input
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className="border border-lia-border-subtle focus:ring-1 focus:ring-gray-400"
      />
      {value.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {value.map((item) => (
            <Badge
              key={item}
              variant="secondary"
              className={`${badgeStyles.default} pl-2 pr-1 py-1 flex items-center gap-1`}
            >
              {item}
              <button
                onClick={() => onRemove(item)}
                className="ml-1 hover:bg-gray-300 rounded-md p-0.5"
              >
                <X className="w-3 h-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  )
}
