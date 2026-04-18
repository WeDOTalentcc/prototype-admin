"use client"

import React, { useState, useRef, useEffect } from"react"
import { Button } from"@/components/ui/button"
import { Label } from"@/components/ui/label"
import { Checkbox } from"@/components/ui/checkbox"
import { Chip } from "@/components/ui/chip"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Input } from"@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from"@/components/ui/select"
import { Loader2, Plus, X, Search } from"lucide-react"
import { LANGUAGES_CATALOG, Language, LanguagesData } from"../types"

interface PanelProps {
  initialData?: Record<string, unknown>
  onSubmit: (data: unknown) => Promise<void>
  isLoading?: boolean
}

type LanguageLevel ="Básico" |"Intermediário" |"Avançado" |"Fluente" |"Nativo"

const LEVEL_OPTIONS: LanguageLevel[] = ["Básico","Intermediário","Avançado","Fluente","Nativo"]

const LEVEL_STYLES: Record<LanguageLevel, { bg: string; text: string; opacity: string }> = {"Básico": { bg: 'var(--lia-bg-tertiary)', text: 'var(--lia-text-tertiary)', opacity: '0.7' },"Intermediário": { bg: 'var(--lia-bg-tertiary)', text: 'var(--lia-text-secondary)', opacity: '0.85' },"Avançado": { bg: 'var(--lia-bg-secondary)', text: 'var(--lia-text-primary)', opacity: '1' },"Fluente": { bg: 'var(--lia-btn-primary-bg)', text: 'var(--lia-btn-primary-text)', opacity: '1' },"Nativo": { bg: 'var(--lia-btn-primary-bg)', text: 'var(--lia-btn-primary-text)', opacity: '1' }
}

const DEFAULT_LANGUAGES: Language[] = [
  { id:"en_default", name:"Inglês", code:"en", level:"Intermediário", required: false },
  { id:"es_default", name:"Espanhol", code:"es", level:"Básico", required: false },
  { id:"pt_default", name:"Português", code:"pt", level:"Nativo", required: true }
]

export function LanguagesPanel({
  initialData = {},
  onSubmit,
  isLoading = false
}: PanelProps) {
  const [languages, setLanguages] = useState<Language[]>(() => {
    const initial = initialData.languages as Language[] | undefined
    if (initial && Array.isArray(initial) && initial.length > 0) {
      return initial
    }
    return DEFAULT_LANGUAGES.map((l) => ({ ...l, id: `${l.code}_${Date.now()}_${Math.random()}` }))
  })

  const handleAddLanguage = (langCatalog: typeof LANGUAGES_CATALOG[number]) => {
    const newLanguage: Language = {
      id: `${langCatalog.code}_${Date.now()}`,
      name: langCatalog.name,
      code: langCatalog.code,
      level:"Intermediário",
      required: false
    }
    setLanguages((prev) => [...prev, newLanguage])
  }

  const handleRemoveLanguage = (id: string) => {
    setLanguages((prev) => prev.filter((l) => l.id !== id))
  }

  const handleUpdateLevel = (id: string, level: LanguageLevel) => {
    setLanguages((prev) =>
      prev.map((l) => (l.id === id ? { ...l, level } : l))
    )
  }

  const handleToggleRequired = (id: string) => {
    setLanguages((prev) =>
      prev.map((l) => (l.id === id ? { ...l, required: !l.required } : l))
    )
  }

  const handleSubmit = async () => {
    const data: LanguagesData = {
      languages
    }
    await onSubmit(data)
  }

  const getFlag = (code: string) => {
    const lang = LANGUAGES_CATALOG.find((l) => l.code === code)
    return lang?.flag ||"🌐"
  }

  const existingCodes = languages.map((l) => l.code)

  return (
    <div className="space-y-6">
      <Card className="rounded-xl dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
        <CardHeader className="pb-3 dark:border-lia-border-subtle">
          <CardTitle className="text-sm flex items-center gap-2 font-sans text-lia-text-primary">
            🌍 Idiomas Requeridos
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <LanguageAutocomplete
            existingCodes={existingCodes}
            onAdd={handleAddLanguage}
          />

          {languages.length === 0 ? (
            <div className="text-center py-8 text-sm text-lia-text-tertiary">
              Nenhum idioma adicionado.
              <br />
              Use o campo acima para adicionar.
            </div>
          ) : (
            <div className="rounded-xl overflow-hidden dark:border-lia-border-subtle border border-lia-border-subtle">
              <table className="w-full">
                <thead className="bg-lia-bg-secondary">
                  <tr>
                    <th className="text-left px-3 py-2 text-xs font-medium text-lia-text-secondary">
                      Idioma
                    </th>
                    <th className="text-left px-3 py-2 text-xs font-medium w-36 text-lia-text-secondary">
                      Nível
                    </th>
                    <th className="text-center px-3 py-2 text-xs font-medium w-24 text-lia-text-secondary">
                      Obrigatório?
                    </th>
                    <th className="w-10"></th>
                  </tr>
                </thead>
                <tbody className="divide-y dark:divide-lia-border-strong border-lia-border-subtle">
                  {languages.map((lang) => (
                    <tr
                      key={lang.id}
                      className="transition-colors motion-reduce:transition-none dark:hover:bg-lia-bg-inverse"
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--lia-interactive-hover)'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                    >
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-2">
                          <span className="text-lg">{getFlag(lang.code)}</span>
                          <span className="text-sm font-medium text-lia-text-primary">{lang.name}</span>
                          {lang.required && (
                            <Chip
                              variant="neutral" muted
                              className="text-xs border-0 bg-lia-bg-tertiary text-lia-text-secondary"
                            >
                              Obrigatório
                            </Chip>
                          )}
                        </div>
                      </td>
                      <td className="px-3 py-2">
                        <Select
                          value={lang.level}
                          onValueChange={(value) =>
                            handleUpdateLevel(lang.id, value as LanguageLevel)
                          }
                        >
                          <SelectTrigger className="h-8 text-xs dark:bg-lia-bg-primary dark:border-lia-border-subtle">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {LEVEL_OPTIONS.map((level) => {
                              const styles = LEVEL_STYLES[level]
                              return (
                                <SelectItem key={level} value={level}>
                                  <span
                                    className="inline-block px-1.5 py-0.5 rounded-md text-xs"
                                    style={{backgroundColor: styles.bg,
                                      color: styles.text,
                                      opacity: styles.opacity}}
                                  >
                                    {level}
                                  </span>
                                </SelectItem>
                              )
                            })}
                          </SelectContent>
                        </Select>
                      </td>
                      <td className="px-3 py-2 text-center">
                        <Checkbox
                          checked={lang.required}
                          onCheckedChange={() => handleToggleRequired(lang.id)}
                        />
                      </td>
                      <td className="px-3 py-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 dark:hover:bg-lia-bg-inverse"
                          onClick={() => handleRemoveLanguage(lang.id)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="rounded-xl dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
        <CardHeader className="pb-3 dark:border-lia-border-subtle">
          <CardTitle className="text-sm font-sans text-lia-text-primary">📊 Resumo</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {languages.length === 0 ? (
              <span className="text-sm text-lia-text-tertiary">
                Nenhum idioma adicionado ainda.
              </span>
            ) : (
              languages.map((lang) => (
                <Chip
                  key={lang.id}
                  variant="neutral"
                  className={`text-xs dark:border-lia-border-default text-lia-text-secondary ${lang.required ? 'border-lia-border-default bg-lia-bg-secondary' : 'border-lia-border-subtle bg-transparent'}`}
                >
                  {getFlag(lang.code)} {lang.name} ({lang.level.charAt(0)})
                </Chip>
              ))
            )}
          </div>
          <div className="mt-3 text-xs text-lia-text-tertiary">
            {languages.filter((l) => l.required).length} obrigatórios,{""}
            {languages.filter((l) => !l.required).length} desejáveis
          </div>
        </CardContent>
      </Card>

      <Button
        onClick={handleSubmit}
        disabled={isLoading}
        className="w-full bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
        size="lg"
      >
        {isLoading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none mr-2" />
            Salvando...
          </>
        ) : ("Concluído"
        )}
      </Button>
    </div>
  )
}

function LanguageAutocomplete({
  existingCodes,
  onAdd
}: {
  existingCodes: string[]
  onAdd: (lang: typeof LANGUAGES_CATALOG[number]) => void
}) {
  const [search, setSearch] = useState("")
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const suggestionsRef = useRef<HTMLDivElement>(null)

  const availableLanguages = LANGUAGES_CATALOG.filter(
    (lang) =>
      !existingCodes.includes(lang.code) &&
      (lang.name.toLowerCase().includes(search.toLowerCase()) ||
        lang.code.toLowerCase().includes(search.toLowerCase()))
  )

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(e.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(e.target as Node)
      ) {
        setShowSuggestions(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key ==="ArrowDown") {
      e.preventDefault()
      setSelectedIndex((prev) =>
        prev < availableLanguages.length - 1 ? prev + 1 : prev
      )
    } else if (e.key ==="ArrowUp") {
      e.preventDefault()
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : 0))
    } else if (e.key ==="Enter") {
      e.preventDefault()
      if (availableLanguages[selectedIndex]) {
        handleAdd(availableLanguages[selectedIndex])
      }
    } else if (e.key ==="Escape") {
      setShowSuggestions(false)
    }
  }

  const handleAdd = (lang: typeof LANGUAGES_CATALOG[number]) => {
    onAdd(lang)
    setSearch("")
    setShowSuggestions(false)
    setSelectedIndex(0)
    inputRef.current?.focus()
  }

  return (
    <div className="relative">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-lia-text-tertiary"
          />
          <Input
            ref={inputRef}
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setShowSuggestions(true)
              setSelectedIndex(0)
            }}
            onFocus={() => setShowSuggestions(true)}
            onKeyDown={handleKeyDown}
            placeholder="Buscar idioma..."
            className="pl-9 dark:bg-lia-bg-primary dark:border-lia-border-subtle"
          />
        </div>
        <Button
          type="button"
          variant="outline"
          size="icon"
          className="dark:border-lia-border-default dark:hover:bg-lia-bg-inverse"
          onClick={() => {
            if (availableLanguages[0]) {
              handleAdd(availableLanguages[0])
            }
          }}
          disabled={availableLanguages.length === 0}
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      {showSuggestions && availableLanguages.length > 0 && (
        <div
          ref={suggestionsRef}
          className="absolute z-50 top-full left-0 right-0 mt-1 rounded-xl max-h-48 overflow-auto dark:bg-lia-bg-secondary dark:border-lia-border-subtle bg-lia-bg-primary border border-lia-border-subtle"
        >
          {availableLanguages.slice(0, 10).map((lang, index) => (
            <button
              key={lang.code}
              type="button"
              className={`w-full text-left px-3 py-2 text-sm flex items-center gap-2 transition-colors motion-reduce:transition-none dark:hover:bg-lia-bg-inverse text-lia-text-primary ${index === selectedIndex ? 'bg-lia-interactive-hover' : 'bg-transparent'}`}
              onClick={() => handleAdd(lang)}
              onMouseEnter={() => setSelectedIndex(index)}
            >
              <span className="text-lg">{lang.flag}</span>
              <span className="dark:text-lia-text-primary">{lang.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
