"use client"

import React, { useState, useRef, useEffect } from"react"
import { Button } from"@/components/ui/button"
import { Input } from"@/components/ui/input"
import { Label } from"@/components/ui/label"
import { Checkbox } from"@/components/ui/checkbox"
import { Chip } from "@/components/ui/chip"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from"@/components/ui/tabs"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from"@/components/ui/select"
import { Loader2, Plus, X, Search } from"lucide-react"
import { TECHNOLOGY_CATALOG, TechRequirement, TechnicalRequirementsData } from"../types"

interface PanelProps {
  initialData?: Record<string, unknown>
  onSubmit: (data: unknown) => Promise<void>
  isLoading?: boolean
}

type TechCategory = keyof typeof TECHNOLOGY_CATALOG
type TechLevel ="Básico" |"Intermediário" |"Avançado" |"Expert"

const LEVEL_OPTIONS: TechLevel[] = ["Básico","Intermediário","Avançado","Expert"]

const CATEGORY_LABELS: Record<TechCategory, { label: string; icon: string }> = {
  languages: { label:"Linguagens", icon:"💻" },
  frameworks: { label:"Frameworks", icon:"🔧" },
  databases: { label:"Bancos de Dados", icon:"🗄️" },
  cloud_devops: { label:"Cloud/DevOps", icon:"☁️" },
  tools: { label:"Ferramentas", icon:"🛠️" }
}

export function TechnicalRequirementsPanel({
  initialData = {},
  onSubmit,
  isLoading = false
}: PanelProps) {
  const [requirements, setRequirements] = useState<TechRequirement[]>(() => {
    const initial = initialData.requirements as TechRequirement[] | undefined
    return initial || []
  })
  const [activeTab, setActiveTab] = useState<TechCategory>("languages")

  const handleAddRequirement = (name: string, category: TechCategory) => {
    const newRequirement: TechRequirement = {
      id: `${category}_${name.toLowerCase().replace(/[^a-z0-9]/g,"_")}_${Date.now()}`,
      name,
      level:"Intermediário",
      required: false,
      category
    }
    setRequirements((prev) => [...prev, newRequirement])
  }

  const handleRemoveRequirement = (id: string) => {
    setRequirements((prev) => prev.filter((r) => r.id !== id))
  }

  const handleUpdateLevel = (id: string, level: TechLevel) => {
    setRequirements((prev) =>
      prev.map((r) => (r.id === id ? { ...r, level } : r))
    )
  }

  const handleToggleRequired = (id: string) => {
    setRequirements((prev) =>
      prev.map((r) => (r.id === id ? { ...r, required: !r.required } : r))
    )
  }

  const handleSubmit = async () => {
    const data: TechnicalRequirementsData = {
      requirements
    }
    await onSubmit(data)
  }

  const getRequirementsByCategory = (category: TechCategory) => {
    return requirements.filter((r) => r.category === category)
  }

  return (
    <div className="space-y-6">
      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TechCategory)}>
        <TabsList className="grid w-full grid-cols-5 h-auto">
          {(Object.keys(CATEGORY_LABELS) as TechCategory[]).map((category) => (
            <TabsTrigger
              key={category}
              value={category}
              className="text-xs flex flex-col gap-1 py-2"
            >
              <span>{CATEGORY_LABELS[category].icon}</span>
              <span className="hidden sm:inline">{CATEGORY_LABELS[category].label}</span>
            </TabsTrigger>
          ))}
        </TabsList>

        {(Object.keys(CATEGORY_LABELS) as TechCategory[]).map((category) => (
          <TabsContent key={category} value={category} className="mt-4">
            <Card className="rounded-xl dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
              <CardHeader className="pb-3 dark:border-lia-border-subtle">
                <CardTitle className="text-sm flex items-center gap-2 font-sans">
                  {CATEGORY_LABELS[category].icon} {CATEGORY_LABELS[category].label}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <TechAutocomplete
                  category={category}
                  existingTechs={getRequirementsByCategory(category).map((r) => r.name)}
                  onAdd={(name) => handleAddRequirement(name, category)}
                />

                {getRequirementsByCategory(category).length === 0 ? (
                  <div className="text-center py-8 text-lia-text-tertiary text-sm">
                    Nenhuma tecnologia adicionada.
                    <br />
                    Use o campo acima para adicionar.
                  </div>
                ) : (
                  <div className="border rounded-xl overflow-hidden dark:border-lia-border-subtle">
                    <table className="w-full">
                      <thead className="bg-lia-bg-tertiary/50 dark:bg-lia-bg-primary/50">
                        <tr>
                          <th className="text-left px-3 py-2 text-xs font-medium">
                            Tecnologia
                          </th>
                          <th className="text-left px-3 py-2 text-xs font-medium w-36">
                            Nível
                          </th>
                          <th className="text-center px-3 py-2 text-xs font-medium w-24">
                            Obrigatória?
                          </th>
                          <th className="w-10"></th>
                        </tr>
                      </thead>
                      <tbody className="divide-y dark:divide-lia-border-strong">
                        {getRequirementsByCategory(category).map((req) => (
                          <tr key={req.id} className="hover:bg-lia-bg-tertiary/30 dark:hover:bg-lia-bg-inverse/30">
                            <td className="px-3 py-2">
                              <div className="flex items-center gap-2">
                                <span className="text-sm font-medium">{req.name}</span>
                                {req.required && (
                                  <Chip density="relaxed" variant="neutral" muted >
                                    Obrigatória
                                  </Chip>
                                )}
                              </div>
                            </td>
                            <td className="px-3 py-2">
                              <Select
                                value={req.level}
                                onValueChange={(value) =>
                                  handleUpdateLevel(req.id, value as TechLevel)
                                }
                              >
                                <SelectTrigger className="h-8 text-xs dark:bg-lia-bg-primary dark:border-lia-border-subtle">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  {LEVEL_OPTIONS.map((level) => (
                                    <SelectItem key={level} value={level}>
                                      {level}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            </td>
                            <td className="px-3 py-2 text-center">
                              <Checkbox
                                checked={req.required}
                                onCheckedChange={() => handleToggleRequired(req.id)}
                              />
                            </td>
                            <td className="px-3 py-2">
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-7 w-7 dark:hover:bg-lia-bg-inverse"
                                onClick={() => handleRemoveRequirement(req.id)}
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
          </TabsContent>
        ))}
      </Tabs>

      <Card className="rounded-xl dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
        <CardHeader className="pb-3 dark:border-lia-border-subtle">
          <CardTitle className="text-sm font-sans">📊 Resumo</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {requirements.length === 0 ? (
              <span className="text-sm text-lia-text-tertiary">
                Nenhum requisito técnico adicionado ainda.
              </span>
            ) : (
              requirements.map((req) => (
                <Chip
                  key={req.id}
                  variant="neutral"
                  muted={req.required}
                  className="text-xs dark:border-lia-border-default"
                >
                  {req.name} ({req.level.charAt(0)})
                </Chip>
              ))
            )}
          </div>
          <div className="mt-3 text-xs text-lia-text-tertiary">
            {requirements.filter((r) => r.required).length} obrigatórias,{""}
            {requirements.filter((r) => !r.required).length} desejáveis
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

function TechAutocomplete({
  category,
  existingTechs,
  onAdd
}: {
  category: TechCategory
  existingTechs: string[]
  onAdd: (name: string) => void
}) {
  const [search, setSearch] = useState("")
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const suggestionsRef = useRef<HTMLDivElement>(null)

  const catalogTechs = TECHNOLOGY_CATALOG[category]
  const availableTechs = catalogTechs.filter(
    (tech) =>
      !existingTechs.some((e) => e.toLowerCase() === tech.toLowerCase()) &&
      tech.toLowerCase().includes(search.toLowerCase())
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
        prev < availableTechs.length - 1 ? prev + 1 : prev
      )
    } else if (e.key ==="ArrowUp") {
      e.preventDefault()
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : 0))
    } else if (e.key ==="Enter") {
      e.preventDefault()
      if (availableTechs[selectedIndex]) {
        handleAdd(availableTechs[selectedIndex])
      } else if (search.trim()) {
        handleAdd(search.trim())
      }
    } else if (e.key ==="Escape") {
      setShowSuggestions(false)
    }
  }

  const handleAdd = (name: string) => {
    onAdd(name)
    setSearch("")
    setShowSuggestions(false)
    setSelectedIndex(0)
    inputRef.current?.focus()
  }

  return (
    <div className="relative">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-lia-text-tertiary" />
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
            placeholder={`Buscar ou adicionar ${CATEGORY_LABELS[category].label.toLowerCase()}...`}
            className="pl-9 dark:bg-lia-bg-primary dark:border-lia-border-subtle"
          />
        </div>
        <Button
          type="button"
          variant="outline"
          size="icon"
          className="dark:border-lia-border-default dark:hover:bg-lia-bg-inverse"
          onClick={() => {
            if (search.trim()) {
              handleAdd(search.trim())
            }
          }}
          disabled={!search.trim()}
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      {showSuggestions && (search || availableTechs.length > 0) && (
        <div
          ref={suggestionsRef}
          className="absolute z-50 top-full left-0 right-0 mt-1 border rounded-xl max-h-48 overflow-auto dark:bg-lia-bg-secondary dark:border-lia-border-subtle bg-lia-bg-primary border-lia-border-default"
        >
          {availableTechs.length > 0 ? (
            availableTechs.slice(0, 10).map((tech, index) => (
              <button
                key={tech}
                type="button"
                className={`w-full text-left px-3 py-2 text-sm hover:bg-lia-bg-tertiary/50 dark:hover:bg-lia-bg-inverse ${
 index === selectedIndex ?"bg-lia-bg-tertiary dark:bg-lia-bg-elevated" :""
                }`}
                onClick={() => handleAdd(tech)}
                onMouseEnter={() => setSelectedIndex(index)}
              >
                {tech}
              </button>
            ))
          ) : search.trim() ? (
            <button
              type="button"
              className="w-full text-left px-3 py-2 text-sm hover:bg-lia-bg-tertiary/50 bg-lia-bg-tertiary dark:bg-lia-bg-elevated dark:hover:bg-lia-border-medium"
              onClick={() => handleAdd(search.trim())}
            >
              Adicionar"{search.trim()}"
            </button>
          ) : null}
        </div>
      )}
    </div>
  )
}
