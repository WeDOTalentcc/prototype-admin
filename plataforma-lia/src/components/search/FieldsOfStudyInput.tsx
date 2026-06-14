"use client"

import { useState, useRef, useEffect, useCallback } from"react"
import { X, Brain, Loader2, Search, ChevronDown, Info, Zap } from"lucide-react"
import { cn } from"@/lib/utils"
import { useTagInputState } from"@/hooks/ui/useTagInputState"
import { Chip } from "@/components/ui/chip"
import { Input } from"@/components/ui/input"
import { Popover, PopoverContent, PopoverTrigger } from"@/components/ui/popover"
import { useSemanticSearch } from"@/hooks/search/useSemanticSearch"

interface FieldsOfStudyInputProps {
  mode: 'regular' | 'nested'
  onModeChange: (mode: 'regular' | 'nested') => void
  value: string[]
  onChange: (fields: string[]) => void
  placeholder?: string
}

const FIELDS_OF_STUDY = ["3D Modelling","3D Modelling and Animation","Accountancy","Accounting","Acting","Actuarial Science","Addiction Counseling","Administration","Administration of Justice","Advertising","Aerospace Engineering","African Studies","Agricultural Engineering","Agriculture","Agronomy","American Studies","Anatomy","Animation","Anthropology","Applied Mathematics","Applied Physics","Arabic","Archaeology","Architecture","Art History","Artificial Intelligence","Asian Studies","Astronomy","Astrophysics","Athletic Training","Biochemistry","Bioengineering","Bioinformatics","Biology","Biomedical Engineering","Biomedical Sciences","Biophysics","Biotechnology","Business","Business Administration","Business Analytics","Business Management","Chemical Engineering","Chemistry","Chinese","Civil Engineering","Classics","Clinical Psychology","Cognitive Science","Communication","Communications","Computer Engineering","Computer Graphics","Computer Science","Construction Management","Creative Writing","Criminal Justice","Criminology","Culinary Arts","Cybersecurity","Dance","Data Analytics","Data Science","Dentistry","Design","Digital Marketing","Digital Media","Drama","Earth Sciences","Ecology","Economics","Education","Electrical Engineering","Electronics","Elementary Education","Engineering","English","English Literature","Entrepreneurship","Environmental Engineering","Environmental Science","Environmental Studies","Epidemiology","European Studies","Fashion Design","Film","Film Production","Film Studies","Finance","Financial Engineering","Fine Arts","Food Science","Foreign Languages","Forensic Science","Forestry","French","Game Design","Gender Studies","Genetics","Geography","Geology","German","Graphic Design","Health Administration","Health Sciences","Healthcare Management","History","Hospitality Management","Hotel Management","Human Resources","Humanities","Illustration","Industrial Design","Industrial Engineering","Information Systems","Information Technology","Interior Design","International Business","International Relations","Italian","Japanese","Journalism","Korean","Landscape Architecture","Latin American Studies","Law","Leadership","Liberal Arts","Library Science","Linguistics","Literature","Logistics","Machine Learning","Management","Management Information Systems","Manufacturing Engineering","Marine Biology","Marketing","Materials Science","Mathematics","Mechanical Engineering","Media Studies","Medicine","Microbiology","Middle Eastern Studies","Military Science","Mining Engineering","Molecular Biology","Music","Music Production","Nanotechnology","Natural Sciences","Neuroscience","Nuclear Engineering","Nursing","Nutrition","Occupational Therapy","Operations Management","Optometry","Organizational Psychology","Paralegal Studies","Petroleum Engineering","Pharmacology","Pharmacy","Philosophy","Photography","Physical Education","Physical Therapy","Physics","Physiology","Political Science","Portuguese","Pre-Law","Pre-Med","Product Design","Project Management","Psychology","Public Administration","Public Health","Public Policy","Public Relations","Quantitative Finance","Real Estate","Religious Studies","Robotics","Russian","Sales","Social Sciences","Social Work","Sociology","Software Engineering","Spanish","Speech Pathology","Sports Management","Sports Medicine","Statistics","Strategic Management","Studio Art","Supply Chain Management","Sustainable Development","Systems Engineering","Teaching","Technical Writing","Technology Management","Telecommunications","Theater","Theology","Tourism","Translation","Transportation","Urban Planning","User Experience Design","Veterinary Medicine","Video Game Development","Visual Arts","Web Development","Women's Studies","Zoology"
]

export function FieldsOfStudyInput({
  mode,
  onModeChange,
  value,
  onChange,
  placeholder ="All Engineering Majors, Natural Sciences, CS, etc."
}: FieldsOfStudyInputProps) {
  const {
    inputValue, setInputValue,
    isDropdownOpen, setIsDropdownOpen,
    focusedIndex, setFocusedIndex,
    inputRef, dropdownRef,
    closeDropdown,
  } = useTagInputState()
  const [isModeDropdownOpen, setIsModeDropdownOpen] = useState(false)
  const [isLoadingAI, setIsLoadingAI] = useState(false)
  const modeDropdownRef = useRef<HTMLDivElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const requestIdRef = useRef(0)

  const { 
    suggestions: semanticSuggestions, 
    isLoading: isSemanticLoading, 
    search: searchSemantic,
    clearSuggestions
  } = useSemanticSearch({ domain:"fields-of-study", debounceMs: 400 })

  const existingFields = value.map(f => f.toLowerCase())

  const filteredSuggestions = inputValue.trim()
    ? FIELDS_OF_STUDY.filter(field => 
        field.toLowerCase().includes(inputValue.toLowerCase()) &&
        !existingFields.includes(field.toLowerCase())
      ).slice(0, 8)
    : []

  const semanticItems = semanticSuggestions
    .filter(s => !existingFields.includes(s.term.toLowerCase()))
    .map(s => ({ type: 'semantic' as const, label: s.term, field: s.term, confidence: s.confidence }))

  const showAskAI = inputValue.trim().length >= 2
  const dropdownItems = [
    ...semanticItems,
    ...(showAskAI && semanticItems.length === 0 ? [{ type: 'ai' as const, label: `Buscar com IA"${inputValue}"`, field: null, confidence: 0 }] : []),
    ...filteredSuggestions.map(f => ({ type: 'field' as const, label: f, field: f, confidence: 0 }))
  ]

  useEffect(() => {
    const handleModeClickOutside = (event: MouseEvent) => {
      if (modeDropdownRef.current && !modeDropdownRef.current.contains(event.target as Node)) {
        setIsModeDropdownOpen(false)
      }
    }
    document.addEventListener("mousedown", handleModeClickOutside)
    return () => document.removeEventListener("mousedown", handleModeClickOutside)
  }, [])

  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  const addField = useCallback((field: string) => {
    if (!field.trim()) return
    if (existingFields.includes(field.toLowerCase())) return
    onChange([...value, field])
    setInputValue("")
    setIsDropdownOpen(false)
    setFocusedIndex(-1)
  }, [value, onChange, existingFields, setInputValue, setIsDropdownOpen, setFocusedIndex])

  const removeField = useCallback((field: string) => {
    onChange(value.filter(f => f !== field))
  }, [value, onChange])

  const clearAll = useCallback(() => {
    onChange([])
  }, [onChange])

  const askAIForFields = useCallback(async (query: string) => {
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
      const response = await fetch('/api/ai/suggest-fields-of-study', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, existingFields: value }),
        signal: controller.signal
      })
      
      if (currentRequestId !== requestIdRef.current) return
      
      if (response.ok) {
        const data = await response.json()
        if (data.suggestions && data.suggestions.length > 0) {
          const newFields = data.suggestions
            .filter((f: string) => !existingFields.includes(f.toLowerCase()))
            .slice(0, 6)
          
          onChange([...value, ...newFields])
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
  }, [value, onChange, existingFields, setInputValue, setIsDropdownOpen])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      if (focusedIndex >= 0 && dropdownItems[focusedIndex]) {
        const item = dropdownItems[focusedIndex]
        if (item.type === 'ai') {
          askAIForFields(inputValue)
        } else if (item.field) {
          addField(item.field)
        }
      } else if (inputValue.trim()) {
        addField(inputValue.trim())
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
    const newValue = e.target.value
    setInputValue(newValue)
    setIsDropdownOpen(newValue.length > 0)
    setFocusedIndex(-1)
    
    if (newValue.trim().length >= 2) {
      searchSemantic(newValue, value)
    } else {
      clearSuggestions()
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <div className="relative inline-block" ref={modeDropdownRef}>
          <button
            onClick={() => setIsModeDropdownOpen(!isModeDropdownOpen)}
            className={cn("flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-[width,height]",
              mode === 'regular'
                ?"border-lia-border-default bg-lia-bg-primary text-lia-text-primary"
                :"border-lia-btn-primary-bg dark:border-lia-border-subtle bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-primary"
            )}
          >
            {mode === 'regular' ? 'Regular' : 'Nested'}
            <ChevronDown className="w-3 h-3" />
          </button>

          {isModeDropdownOpen && (
            <div className="absolute z-50 mt-1 w-72 bg-lia-bg-primary border border-lia-border-subtle rounded-xl">
              <button
                onClick={() => {
                  onModeChange('regular')
                  setIsModeDropdownOpen(false)
                }}
                className={cn("w-full text-left px-4 py-3 transition-colors motion-reduce:transition-none hover:bg-lia-bg-secondary rounded-t-lg",
                  mode === 'regular' &&"bg-lia-bg-secondary"
                )}
              >
                <div className="flex items-center gap-2">
                  <div className={cn("w-3 h-3 rounded-full border-2",
                    mode === 'regular' 
                      ?"border-lia-border-strong bg-lia-bg-inverse" 
                      :"border-lia-border-default"
                  )}>
                    {mode === 'regular' && (
                      <div className="w-full h-full rounded-full bg-lia-bg-primary scale-50" />
                    )}
                  </div>
                  <span className="font-medium text-sm text-lia-text-primary">Regular</span>
                </div>
                <p className="text-xs text-lia-text-secondary mt-1 ml-5">
                  Find people who studied this field from any university
                </p>
              </button>

              <button
                onClick={() => {
                  onModeChange('nested')
                  setIsModeDropdownOpen(false)
                }}
                className={cn("w-full text-left px-4 py-3 transition-colors motion-reduce:transition-none hover:bg-lia-bg-secondary rounded-b-lg border-t border-lia-border-subtle",
                  mode === 'nested' &&"bg-lia-bg-secondary dark:bg-lia-bg-secondary/50"
                )}
              >
                <div className="flex items-center gap-2">
                  <div className={cn("w-3 h-3 rounded-full border-2",
                    mode === 'nested' 
                      ?"border-lia-btn-primary-bg bg-lia-btn-primary-bg dark:border-lia-border-subtle" 
                      :"border-lia-border-default"
                  )}>
                    {mode === 'nested' && (
                      <div className="w-full h-full rounded-full bg-lia-bg-primary scale-50" />
                    )}
                  </div>
                  <span className="font-medium text-sm text-lia-text-primary">Nested</span>
                </div>
                <p className="text-xs text-lia-text-secondary mt-1 ml-5">
                  Find people who studied this field from selected universities
                </p>
              </button>
            </div>
          )}
        </div>

        <Popover>
          <PopoverTrigger asChild>
            <button className="text-lia-text-tertiary hover:text-lia-text-secondary transition-colors motion-reduce:transition-none">
              <Info className="w-3.5 h-3.5" />
            </button>
          </PopoverTrigger>
          <PopoverContent className="w-64 p-3 text-xs bg-lia-bg-elevated" side="right">
            <p className="text-lia-text-secondary leading-relaxed">
              <strong>Regular:</strong> Matches candidates who studied this field at any university.
            </p>
            <p className="text-lia-text-secondary leading-relaxed mt-2">
              <strong>Nested:</strong> Only matches candidates who studied this field at the universities you've selected above.
            </p>
          </PopoverContent>
        </Popover>

        {value.length > 0 && (
          <button
            onClick={clearAll}
            className="text-xs text-lia-text-primary hover:text-lia-text-primary font-medium ml-auto"
          >
            Clear all
          </button>
        )}
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
                    askAIForFields(inputValue)
                  } else if (item.field) {
                    addField(item.field)
                  }
                }}
                className={cn("w-full text-left px-3 py-2 text-sm transition-colors",
                  focusedIndex === index ?"bg-lia-bg-tertiary" :"hover:bg-lia-bg-secondary",
                  item.type === 'ai' &&""
                )}
              >
                {item.type === 'ai' ? (
                  <div className="flex items-center gap-2 text-wedo-purple-text">
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
        <div className="flex flex-wrap gap-2">
          {value.map(field => (
            <Chip variant="neutral" muted
              key={field}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-lia-bg-tertiary text-lia-text-primary border border-lia-border-subtle"
            >
              <span>{field}</span>
              <button
                onClick={() => removeField(field)}
                className="hover:bg-lia-interactive-active rounded-md p-0.5 transition-colors motion-reduce:transition-none ml-1"
                title="Remove"
              >
                <X className="w-3 h-3" />
              </button>
            </Chip>
          ))}
        </div>
      )}
    </div>
  )
}

export default FieldsOfStudyInput
