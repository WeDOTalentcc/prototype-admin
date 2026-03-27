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
            className="text-xs text-gray-500 hover:text-status-error flex items-center gap-1 transition-colors"
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
              className="text-xs text-gray-600 hover:text-gray-800 flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save className="w-3.5 h-3.5" />
              Salvar Preset
            </button>
            <button
              onClick={() => {}}
              className="text-xs text-gray-600 hover:text-gray-800 flex items-center gap-1"
            >
              <List className="w-3.5 h-3.5" />
              Presets
            </button>
          </>
        )}
      </div>

      <div className="relative">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            ref={inputRef}
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsDropdownOpen(true)}
            placeholder={placeholder}
            className="pl-9 pr-3 border-gray-200 focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400"
          />
        </div>

        {isDropdownOpen && filteredLanguages.length > 0 && (
          <div 
            ref={dropdownRef}
            className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md max-h-64 overflow-y-auto"
          >
            {filteredLanguages.slice(0, 20).map((language, index) => (
              <button
                key={language}
                onClick={() => addLanguage(language)}
                className={cn(
                  "w-full text-left px-3 py-2 text-sm transition-colors",
                  focusedIndex === index ? "bg-gray-100" : "hover:bg-gray-50"
                )}
              >
                <span className="font-medium text-gray-950 dark:text-gray-50">{language}</span>
              </button>
            ))}
            {filteredLanguages.length > 20 && (
              <div className="px-3 py-2 text-xs text-gray-500 border-t border-gray-100">
                +{filteredLanguages.length - 20} mais resultados...
              </div>
            )}
          </div>
        )}

        {isDropdownOpen && inputValue && filteredLanguages.length === 0 && (
          <div 
            ref={dropdownRef}
            className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md"
          >
            <button
              onClick={() => addLanguage(inputValue.trim())}
              className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-2">
                <Brain className="w-4 h-4 text-wedo-cyan" />
                <span className="text-gray-800 dark:text-gray-200">Adicionar "{inputValue.trim()}"</span>
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
              className="flex items-center gap-1.5 px-2.5 py-1 bg-gray-100 rounded-md text-sm"
            >
              <span className="text-gray-800 dark:text-gray-200">{language}</span>
              <button
                onClick={() => onRemove(language)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
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
