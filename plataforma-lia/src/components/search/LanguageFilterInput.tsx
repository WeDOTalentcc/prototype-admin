"use client"

import { useState, useRef, useEffect, useMemo } from "react"
import { Search, X, RotateCcw, Save, List, Brain } from "lucide-react"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"

const LANGUAGES = [
  "Afrikaans",
  "Akan",
  "Albanian",
  "Amazigh",
  "Amharic",
  "Arabic",
  "Aramaic",
  "Armenian",
  "Assamese",
  "Azerbaijani",
  "Basque",
  "Belarusian",
  "Bengali",
  "Bosnian",
  "Bulgarian",
  "Burmese",
  "Catalan",
  "Cebuano",
  "Chichewa",
  "Chinese (Cantonese)",
  "Chinese (Mandarin)",
  "Chinese (Simplified)",
  "Chinese (Traditional)",
  "Corsican",
  "Croatian",
  "Czech",
  "Danish",
  "Dutch",
  "English",
  "Esperanto",
  "Estonian",
  "Filipino",
  "Finnish",
  "French",
  "Frisian",
  "Galician",
  "Georgian",
  "German",
  "Greek",
  "Gujarati",
  "Haitian Creole",
  "Hausa",
  "Hawaiian",
  "Hebrew",
  "Hindi",
  "Hmong",
  "Hungarian",
  "Icelandic",
  "Igbo",
  "Indonesian",
  "Irish",
  "Italian",
  "Japanese",
  "Javanese",
  "Kannada",
  "Kazakh",
  "Khmer",
  "Kinyarwanda",
  "Korean",
  "Kurdish",
  "Kyrgyz",
  "Lao",
  "Latin",
  "Latvian",
  "Lithuanian",
  "Luxembourgish",
  "Macedonian",
  "Malagasy",
  "Malay",
  "Malayalam",
  "Maltese",
  "Maori",
  "Marathi",
  "Mongolian",
  "Nepali",
  "Norwegian",
  "Odia",
  "Pashto",
  "Persian",
  "Polish",
  "Portuguese",
  "Punjabi",
  "Romanian",
  "Russian",
  "Samoan",
  "Scots Gaelic",
  "Serbian",
  "Sesotho",
  "Shona",
  "Sindhi",
  "Sinhala",
  "Slovak",
  "Slovenian",
  "Somali",
  "Spanish",
  "Sundanese",
  "Swahili",
  "Swedish",
  "Tajik",
  "Tamil",
  "Tatar",
  "Telugu",
  "Thai",
  "Tigrinya",
  "Turkish",
  "Turkmen",
  "Ukrainian",
  "Urdu",
  "Uyghur",
  "Uzbek",
  "Vietnamese",
  "Welsh",
  "Wolof",
  "Xhosa",
  "Yiddish",
  "Yoruba",
  "Zulu"
]

interface LanguageFilterInputProps {
  value: string[]
  onAdd: (language: string) => void
  onRemove: (language: string) => void
  placeholder?: string
  showPresets?: boolean
}

export function LanguageFilterInput({
  value,
  onAdd,
  onRemove,
  placeholder = "Ex: English, Spanish, Mandarin, etc.",
  showPresets = true
}: LanguageFilterInputProps) {
  const [inputValue, setInputValue] = useState("")
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [focusedIndex, setFocusedIndex] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const existingLanguages = useMemo(() => 
    value.map(l => l.toLowerCase()), 
    [value]
  )

  const filteredLanguages = useMemo(() => {
    if (!inputValue.trim()) {
      return LANGUAGES.filter(l => !existingLanguages.includes(l.toLowerCase()))
    }
    const search = inputValue.toLowerCase()
    return LANGUAGES.filter(l => 
      l.toLowerCase().includes(search) && 
      !existingLanguages.includes(l.toLowerCase())
    )
  }, [inputValue, existingLanguages])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current && 
        !dropdownRef.current.contains(event.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(event.target as Node)
      ) {
        setIsDropdownOpen(false)
        setFocusedIndex(-1)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const addLanguage = (language: string) => {
    if (!existingLanguages.includes(language.toLowerCase())) {
      onAdd(language)
    }
    setInputValue("")
    setIsDropdownOpen(false)
    setFocusedIndex(-1)
    inputRef.current?.focus()
  }

  const clearAll = () => {
    value.forEach(l => onRemove(l))
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault()
      if (focusedIndex >= 0 && focusedIndex < filteredLanguages.length) {
        addLanguage(filteredLanguages[focusedIndex])
      } else if (inputValue.trim() && filteredLanguages.length > 0) {
        addLanguage(filteredLanguages[0])
      } else if (inputValue.trim()) {
        addLanguage(inputValue.trim())
      }
    } else if (e.key === "ArrowDown") {
      e.preventDefault()
      setFocusedIndex(prev => Math.min(prev + 1, filteredLanguages.length - 1))
    } else if (e.key === "ArrowUp") {
      e.preventDefault()
      setFocusedIndex(prev => Math.max(prev - 1, -1))
    } else if (e.key === "Escape") {
      setIsDropdownOpen(false)
      setFocusedIndex(-1)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value)
    setIsDropdownOpen(true)
    setFocusedIndex(-1)
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-end gap-3">
        {value.length > 0 && (
          <button
            onClick={clearAll}
            className="text-xs text-lia-text-secondary hover:text-status-error flex items-center gap-1 transition-colors motion-reduce:transition-none"
          >
            <RotateCcw className="w-3 h-3" />
            Limpar tudo
          </button>
        )}
        {showPresets && (
          <>
            <button
              onClick={() => {}}
              disabled={value.length === 0}
              className="text-xs text-lia-text-secondary hover:text-lia-text-primary flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save className="w-3.5 h-3.5" />
              Salvar Preset
            </button>
            <button
              onClick={() => {}}
              className="text-xs text-lia-text-secondary hover:text-lia-text-primary flex items-center gap-1"
            >
              <List className="w-3.5 h-3.5" />
              Presets
            </button>
          </>
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
            onFocus={() => setIsDropdownOpen(true)}
            placeholder={placeholder}
            className="pl-9 pr-3 border-lia-border-subtle focus:ring-1 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 focus:border-lia-border-medium"
          />
        </div>

        {isDropdownOpen && filteredLanguages.length > 0 && (
          <div 
            ref={dropdownRef}
            className="absolute z-50 w-full mt-1 bg-lia-bg-primary border border-lia-border-subtle rounded-xl max-h-64 overflow-y-auto"
          >
            {filteredLanguages.slice(0, 20).map((language, index) => (
              <button
                key={language}
                onClick={() => addLanguage(language)}
                className={cn(
                  "w-full text-left px-3 py-2 text-sm transition-colors",
                  focusedIndex === index ? "bg-lia-bg-tertiary" : "hover:bg-lia-bg-secondary"
                )}
              >
                <span className="font-medium text-lia-text-primary">{language}</span>
              </button>
            ))}
            {filteredLanguages.length > 20 && (
              <div className="px-3 py-2 text-xs text-lia-text-secondary border-t border-lia-border-subtle">
                +{filteredLanguages.length - 20} mais resultados...
              </div>
            )}
          </div>
        )}

        {isDropdownOpen && inputValue && filteredLanguages.length === 0 && (
          <div 
            ref={dropdownRef}
            className="absolute z-50 w-full mt-1 bg-lia-bg-primary border border-lia-border-subtle rounded-xl"
          >
            <button
              onClick={() => addLanguage(inputValue.trim())}
              className="w-full text-left px-3 py-2 text-sm hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none"
            >
              <div className="flex items-center gap-2">
                <Brain className="w-4 h-4 text-wedo-cyan" />
                <span className="text-lia-text-primary">Adicionar "{inputValue.trim()}"</span>
              </div>
            </button>
          </div>
        )}
      </div>

      {value.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {value.map(language => (
            <div
              key={language}
              className="flex items-center gap-1.5 px-2.5 py-1 bg-lia-bg-tertiary rounded-xl text-sm"
            >
              <span className="text-lia-text-primary">{language}</span>
              <button
                onClick={() => onRemove(language)}
                className="text-lia-text-tertiary hover:text-lia-text-secondary transition-colors motion-reduce:transition-none"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
