"use client"

/**
 * CandidatesFilterPanel — Painel lateral de refinamento de resultados.
 *
 * Extraído de candidates-page.tsx (Sprint I2 — god object reduction).
 * Linhas originais: 8825–10092.
 *
 * Props seguem padrão portável Vue/Nuxt:
 *   - tableFilters / setTableFilters → v-model:tableFilters
 *   - on* callbacks → @event
 */

import React from "react"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import {
  X, ArrowUpDown, Zap, Star, Briefcase, MapPin, DollarSign,
  Crown, Bookmark, CheckCircle, Calendar, FileText, Code, Check,
  Brain, Github, Globe, Building, Layers,
} from "lucide-react"
import { badgeStyles, textStyles } from "@/lib/design-tokens"

// ─── Types ───────────────────────────────────────────────────────────────────

export interface TableFilters {
  statuses: string[]
  tags: string[]
  seniorityLevels: string[]
  workModels: string[]
  contractTypes: string[]
  minExperience?: number
  maxExperience?: number
  minScore?: number
  maxScore?: number
  minSalary?: number
  maxSalary?: number
  locations: string[]
  remoteOnly: boolean
  hasEmail: boolean
  hasPhone: boolean
  hasLinkedin: boolean
  sources: string[]
  jobTitles: string[]
  skills: string[]
  companies: string[]
  industries: string[]
  companySizes: string[]
  universities: string[]
  degrees: string[]
  fieldsOfStudy: string[]
  languages: string[]
  isOpenToWork: boolean
  isDecisionMaker: boolean
  isTopUniversities: boolean
  isStartup: boolean
  hasGithub: boolean
  hasPortfolio: boolean
  softSkills: string[]
  certifications: string[]
  willingToRelocate: boolean | null
  mobility: boolean | null
  updatedAtFrom?: string
  updatedAtTo?: string
  lastContactedFrom?: string
  lastContactedTo?: string
  availabilityWindow?: "immediate" | "15_days" | "30_days" | "60_days"
  shortlistedDateFrom?: string
  shortlistedDateTo?: string
  shortlistedVacancyOrigin?: string
  placementDateFrom?: string
  placementDateTo?: string
  placementVacancyDestination?: string
  placementClientCompany?: string
  specificVacancyId?: string
  registrationDateFrom?: string
  registrationDateTo?: string
}

export interface CandidatesFilterPanelProps {
  tableFilters: TableFilters
  setTableFilters: React.Dispatch<React.SetStateAction<TableFilters>>
  searchSortBy: string
  onSortChange: (value: string) => void
  newSoftSkillFilter: string
  setNewSoftSkillFilter: (value: string) => void
  newCertificationFilter: string
  setNewCertificationFilter: (value: string) => void
  activeFiltersCount: number
  onToggleFilter: (category: keyof TableFilters, value: string) => void
  onClearAll: () => void
  onClose: () => void
}

// ─── Component ───────────────────────────────────────────────────────────────

export function CandidatesFilterPanel({
  tableFilters,
  setTableFilters,
  searchSortBy,
  onSortChange,
  newSoftSkillFilter,
  setNewSoftSkillFilter,
  newCertificationFilter,
  setNewCertificationFilter,
  activeFiltersCount,
  onToggleFilter,
  onClearAll,
  onClose,
}: CandidatesFilterPanelProps) {
  return (
    <div className="flex-shrink-0 w-80 transition-all duration-300">
      <div className="bg-white rounded-md h-[calc(100vh-9rem)] overflow-hidden">
        {/* Header */}
        <div className="p-4 flex items-center justify-between border-b border-gray-100">
          <div>
            <h3 className="text-sm font-semibold text-gray-950 dark:text-gray-50">
              Refinar Resultados
            </h3>
            <p className="text-xs mt-0.5 text-gray-800" style={{ fontFamily: "Open Sans, sans-serif" }}>
              {activeFiltersCount > 0
                ? `${activeFiltersCount} filtro${activeFiltersCount > 1 ? "s" : ""} ativo${activeFiltersCount > 1 ? "s" : ""}`
                : "Filtre os resultados exibidos"}
            </p>
          </div>
          <button
            onClick={onClose}
            className="h-8 w-8 rounded-md flex items-center justify-center transition-all text-gray-800 hover:text-gray-950 hover:bg-gray-100"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-4 overflow-y-auto max-h-[calc(100vh-14rem)]">
          {/* Ordenação */}
          <div className="mb-5">
            <h4
              className="text-xs font-semibold uppercase tracking-wider text-gray-800 mb-3 flex items-center gap-1.5"
              style={{ fontFamily: "Open Sans, sans-serif" }}
            >
              <ArrowUpDown className="w-3 h-3" />
              Ordenação
            </h4>
            <RadioGroup value={searchSortBy} onValueChange={onSortChange} className="space-y-1.5">
              {[
                { value: "relevance", label: "Relevância" },
                { value: "score_desc", label: "Maior Score" },
                { value: "score_asc", label: "Menor Score" },
                { value: "name_asc", label: "Nome (A-Z)" },
                { value: "name_desc", label: "Nome (Z-A)" },
                { value: "experience_desc", label: "Maior Experiência" },
              ].map((option) => (
                <label
                  key={option.value}
                  className={cn(
                    "flex items-center gap-2.5 px-3 py-2 rounded-md border cursor-pointer transition-all text-xs",
                    searchSortBy === option.value
                      ? "border-gray-900 bg-gray-50 font-medium text-gray-900"
                      : "border-gray-200 hover:border-gray-300 text-gray-700"
                  )}
                  style={{ fontFamily: "Open Sans, sans-serif" }}
                >
                  <RadioGroupItem
                    value={option.value}
                    className="w-3.5 h-3.5 border-gray-400 data-[state=checked]:border-gray-900 data-[state=checked]:text-gray-900"
                  />
                  {option.label}
                </label>
              ))}
            </RadioGroup>
          </div>

          {/* Filtros Rápidos */}
          <div className="mb-5">
            <h4
              className="text-xs font-semibold uppercase tracking-wider text-gray-800 mb-3 flex items-center gap-1.5"
              style={{ fontFamily: "Open Sans, sans-serif" }}
            >
              <Zap className="w-3 h-3" />
              Filtros Rápidos
            </h4>
            <div className="space-y-2">
              {[
                { key: "hasEmail" as const, label: "Apenas com E-mail" },
                { key: "hasPhone" as const, label: "Apenas com Telefone" },
                { key: "hasLinkedin" as const, label: "Apenas com LinkedIn" },
                { key: "remoteOnly" as const, label: "Apenas Remoto" },
              ].map(({ key, label }) => (
                <div key={key} className="flex items-center justify-between py-1.5">
                  <span className="text-xs text-gray-800" style={{ fontFamily: "Open Sans, sans-serif" }}>
                    {label}
                  </span>
                  <Switch
                    checked={tableFilters[key] as boolean}
                    onCheckedChange={(checked: boolean) =>
                      setTableFilters((prev) => ({ ...prev, [key]: checked }))
                    }
                    className="scale-75"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Experiência */}
          <div className="mb-5">
            <h4
              className="text-xs font-semibold uppercase tracking-wider text-gray-800 mb-3 flex items-center gap-1.5"
              style={{ fontFamily: "Open Sans, sans-serif" }}
            >
              <Briefcase className="w-3 h-3" />
              Experiência
            </h4>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-xs text-gray-800 mb-1 block">Mín. Anos</label>
                <Input
                  type="number"
                  min={0}
                  max={30}
                  value={tableFilters.minExperience ?? ""}
                  onChange={(e) =>
                    setTableFilters((prev) => ({
                      ...prev,
                      minExperience: e.target.value ? Number(e.target.value) : undefined,
                    }))
                  }
                  className="h-8 text-xs"
                  placeholder="0"
                />
              </div>
              <div>
                <label className="text-xs text-gray-800 mb-1 block">Máx. Anos</label>
                <Input
                  type="number"
                  min={0}
                  max={30}
                  value={tableFilters.maxExperience ?? ""}
                  onChange={(e) =>
                    setTableFilters((prev) => ({
                      ...prev,
                      maxExperience: e.target.value ? Number(e.target.value) : undefined,
                    }))
                  }
                  className="h-8 text-xs"
                  placeholder="30"
                />
              </div>
            </div>
          </div>

          {/* Score LIA */}
          <div className="mb-5">
            <h4
              className="text-xs font-semibold uppercase tracking-wider text-gray-800 mb-3 flex items-center gap-1.5"
              style={{ fontFamily: "Open Sans, sans-serif" }}
            >
              <Star className="w-3 h-3" />
              Score LIA
            </h4>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-xs text-gray-800 mb-1 block">Mín. Score</label>
                <Input
                  type="number"
                  min={0}
                  max={100}
                  value={tableFilters.minScore ?? ""}
                  onChange={(e) =>
                    setTableFilters((prev) => ({
                      ...prev,
                      minScore: e.target.value ? Number(e.target.value) : undefined,
                    }))
                  }
                  className="h-8 text-xs"
                  placeholder="0"
                />
              </div>
              <div>
                <label className="text-xs text-gray-800 mb-1 block">Máx. Score</label>
                <Input
                  type="number"
                  min={0}
                  max={100}
                  value={tableFilters.maxScore ?? ""}
                  onChange={(e) =>
                    setTableFilters((prev) => ({
                      ...prev,
                      maxScore: e.target.value ? Number(e.target.value) : undefined,
                    }))
                  }
                  className="h-8 text-xs"
                  placeholder="100"
                />
              </div>
            </div>
          </div>

          {/* Senioridade */}
          <div className="mb-5">
            <h4
              className="text-xs font-semibold uppercase tracking-wider text-gray-800 mb-3 flex items-center gap-1.5"
              style={{ fontFamily: "Open Sans, sans-serif" }}
            >
              <Crown className="w-3 h-3" />
              Senioridade
            </h4>
            <div className="space-y-1.5">
              {[
                { value: "junior", label: "Júnior" },
                { value: "pleno", label: "Pleno" },
                { value: "senior", label: "Sênior" },
                { value: "especialista", label: "Especialista" },
                { value: "lideranca", label: "Liderança" },
              ].map((level) => {
                const isChecked = tableFilters.seniorityLevels.includes(level.value)
                return (
                  <CheckableItem
                    key={level.value}
                    label={level.label}
                    checked={isChecked}
                    onClick={() => onToggleFilter("seniorityLevels", level.value)}
                  />
                )
              })}
            </div>
          </div>

          {/* Modelo de Trabalho */}
          <div className="mb-5">
            <h4
              className="text-xs font-semibold uppercase tracking-wider text-gray-800 mb-3 flex items-center gap-1.5"
              style={{ fontFamily: "Open Sans, sans-serif" }}
            >
              <MapPin className="w-3 h-3" />
              Modelo de Trabalho
            </h4>
            <div className="space-y-1.5">
              {[
                { value: "remote", label: "Remoto" },
                { value: "hybrid", label: "Híbrido" },
                { value: "onsite", label: "Presencial" },
              ].map((model) => {
                const isChecked = tableFilters.workModels.includes(model.value)
                return (
                  <CheckableItem
                    key={model.value}
                    label={model.label}
                    checked={isChecked}
                    onClick={() => onToggleFilter("workModels", model.value)}
                  />
                )
              })}
            </div>
          </div>

          {/* Tipo de Contrato */}
          <div className="mb-5">
            <h4
              className="text-xs font-semibold uppercase tracking-wider text-gray-800 mb-3 flex items-center gap-1.5"
              style={{ fontFamily: "Open Sans, sans-serif" }}
            >
              <FileText className="w-3 h-3" />
              Tipo de Contrato
            </h4>
            <div className="space-y-1.5">
              {["CLT", "PJ", "Freelancer"].map((contract) => {
                const isChecked = tableFilters.contractTypes.includes(contract)
                return (
                  <CheckableItem
                    key={contract}
                    label={contract}
                    checked={isChecked}
                    onClick={() => onToggleFilter("contractTypes", contract)}
                  />
                )
              })}
            </div>
          </div>

          {/* Localização */}
          <div className="mb-5">
            <h4
              className="text-xs font-semibold uppercase tracking-wider text-gray-800 mb-3 flex items-center gap-1.5"
              style={{ fontFamily: "Open Sans, sans-serif" }}
            >
              <MapPin className="w-3 h-3" />
              Localização
            </h4>
            <TagInput
              placeholder="Digite cidade ou estado..."
              tags={tableFilters.locations}
              onAdd={(v) => setTableFilters((prev) => ({ ...prev, locations: [...prev.locations, v] }))}
              onRemove={(v) =>
                setTableFilters((prev) => ({ ...prev, locations: prev.locations.filter((l) => l !== v) }))
              }
            />
          </div>

          {/* Salário */}
          <div className="mb-5">
            <h4
              className="text-xs font-semibold uppercase tracking-wider text-gray-800 mb-3 flex items-center gap-1.5"
              style={{ fontFamily: "Open Sans, sans-serif" }}
            >
              <DollarSign className="w-3 h-3" />
              Faixa Salarial
            </h4>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className={`${textStyles.label} mb-1 block`}>Mín. (R$)</label>
                <Input
                  type="number"
                  min={0}
                  value={tableFilters.minSalary ?? ""}
                  onChange={(e) =>
                    setTableFilters((prev) => ({
                      ...prev,
                      minSalary: e.target.value ? Number(e.target.value) : undefined,
                    }))
                  }
                  className="h-8 text-xs"
                  placeholder="0"
                />
              </div>
              <div>
                <label className={`${textStyles.label} mb-1 block`}>Máx. (R$)</label>
                <Input
                  type="number"
                  min={0}
                  value={tableFilters.maxSalary ?? ""}
                  onChange={(e) =>
                    setTableFilters((prev) => ({
                      ...prev,
                      maxSalary: e.target.value ? Number(e.target.value) : undefined,
                    }))
                  }
                  className="h-8 text-xs"
                  placeholder="50000"
                />
              </div>
            </div>
          </div>

          {/* Indicadores de Perfil */}
          <div className="mb-5">
            <h4
              className="text-xs font-semibold uppercase tracking-wider text-gray-800 mb-3 flex items-center gap-1.5"
              style={{ fontFamily: "Open Sans, sans-serif" }}
            >
              <Crown className="w-3 h-3" />
              Indicadores de Perfil
            </h4>
            <div className="space-y-2">
              {[
                { key: "isOpenToWork" as const, label: "Open to Work" },
                { key: "isDecisionMaker" as const, label: "Decision Maker" },
                { key: "isTopUniversities" as const, label: "Top Universidades" },
                { key: "isStartup" as const, label: "Trabalha em Startup" },
              ].map(({ key, label }) => (
                <div key={key} className="flex items-center justify-between py-1.5">
                  <span className="text-xs text-gray-800" style={{ fontFamily: "Open Sans, sans-serif" }}>
                    {label}
                  </span>
                  <Switch
                    checked={tableFilters[key] as boolean}
                    onCheckedChange={(checked: boolean) =>
                      setTableFilters((prev) => ({ ...prev, [key]: checked }))
                    }
                    className="scale-75"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Fonte */}
          <div className="mb-5">
            <h4
              className="text-xs font-semibold uppercase tracking-wider text-gray-800 mb-3 flex items-center gap-1.5"
              style={{ fontFamily: "Open Sans, sans-serif" }}
            >
              <Globe className="w-3 h-3" />
              Fonte do Candidato
            </h4>
            <div className="space-y-1.5">
              {[
                "Base Global",
                "Base Local",
                "LinkedIn",
                "Indicação",
                "Site Carreiras",
              ].map((source) => {
                const isChecked = tableFilters.sources.includes(source)
                return (
                  <CheckableItem
                    key={source}
                    label={source}
                    checked={isChecked}
                    onClick={() => onToggleFilter("sources", source)}
                  />
                )
              })}
            </div>
          </div>

          {/* Tags */}
          <div className="mb-5">
            <h4
              className="text-xs font-semibold uppercase tracking-wider text-gray-800 mb-3 flex items-center gap-1.5"
              style={{ fontFamily: "Open Sans, sans-serif" }}
            >
              <Bookmark className="w-3 h-3" />
              Tags
            </h4>
            <TagInput
              placeholder="Digite uma tag..."
              tags={tableFilters.tags}
              onAdd={(v) => setTableFilters((prev) => ({ ...prev, tags: [...prev.tags, v] }))}
              onRemove={(v) =>
                setTableFilters((prev) => ({ ...prev, tags: prev.tags.filter((t) => t !== v) }))
              }
            />
          </div>

          {/* Empresa */}
          <div className="mb-5">
            <h4
              className="text-xs font-semibold uppercase tracking-wider text-gray-800 mb-3 flex items-center gap-1.5"
              style={{ fontFamily: "Open Sans, sans-serif" }}
            >
              <Building className="w-3 h-3" />
              Empresa
            </h4>
            <TagInput
              placeholder="Digite nome da empresa..."
              tags={tableFilters.companies}
              onAdd={(v) => setTableFilters((prev) => ({ ...prev, companies: [...prev.companies, v] }))}
              onRemove={(v) =>
                setTableFilters((prev) => ({ ...prev, companies: prev.companies.filter((c) => c !== v) }))
              }
            />
          </div>

          {/* Setor/Indústria */}
          <div className="mb-5">
            <h4
              className="text-xs font-semibold uppercase tracking-wider text-gray-800 mb-3 flex items-center gap-1.5"
              style={{ fontFamily: "Open Sans, sans-serif" }}
            >
              <Layers className="w-3 h-3" />
              Setor/Indústria
            </h4>
            <TagInput
              placeholder="Digite o setor..."
              tags={tableFilters.industries}
              onAdd={(v) => setTableFilters((prev) => ({ ...prev, industries: [...prev.industries, v] }))}
              onRemove={(v) =>
                setTableFilters((prev) => ({
                  ...prev,
                  industries: prev.industries.filter((i) => i !== v),
                }))
              }
            />
          </div>

          {/* Idiomas */}
          <div className="mb-5">
            <h4
              className="text-xs font-semibold uppercase tracking-wider text-gray-800 mb-3 flex items-center gap-1.5"
              style={{ fontFamily: "Open Sans, sans-serif" }}
            >
              <Globe className="w-3 h-3" />
              Idiomas
            </h4>
            <TagInput
              placeholder="Digite um idioma..."
              tags={tableFilters.languages}
              onAdd={(v) => setTableFilters((prev) => ({ ...prev, languages: [...prev.languages, v] }))}
              onRemove={(v) =>
                setTableFilters((prev) => ({
                  ...prev,
                  languages: prev.languages.filter((l) => l !== v),
                }))
              }
            />
          </div>

          {/* Status */}
          <div className="mb-5">
            <h4
              className="text-xs font-semibold uppercase tracking-wider text-gray-800 mb-3 flex items-center gap-1.5"
              style={{ fontFamily: "Open Sans, sans-serif" }}
            >
              <CheckCircle className="w-3 h-3" />
              Status
            </h4>
            <div className="space-y-1.5">
              {[
                { value: "novo", label: "Novo" },
                { value: "em_analise", label: "Em Análise" },
                { value: "entrevista", label: "Entrevista" },
                { value: "aprovado", label: "Aprovado" },
                { value: "reprovado", label: "Reprovado" },
                { value: "contratado", label: "Contratado" },
              ].map((status) => {
                const isChecked = tableFilters.statuses.includes(status.value)
                return (
                  <CheckableItem
                    key={status.value}
                    label={status.label}
                    checked={isChecked}
                    onClick={() => onToggleFilter("statuses", status.value)}
                  />
                )
              })}
            </div>
          </div>

          {/* Presença Online */}
          <div className="mb-5">
            <h4
              className="text-xs font-semibold uppercase tracking-wider text-gray-800 mb-3 flex items-center gap-1.5"
              style={{ fontFamily: "Open Sans, sans-serif" }}
            >
              <Github className="w-3 h-3" />
              Presença Online
            </h4>
            <div className="space-y-2">
              {[
                { key: "hasGithub" as const, label: "Com Github" },
                { key: "hasPortfolio" as const, label: "Com Portfólio" },
              ].map(({ key, label }) => (
                <div key={key} className="flex items-center justify-between py-1.5">
                  <span className="text-xs text-gray-800" style={{ fontFamily: "Open Sans, sans-serif" }}>
                    {label}
                  </span>
                  <Switch
                    checked={tableFilters[key] as boolean}
                    onCheckedChange={(checked: boolean) =>
                      setTableFilters((prev) => ({ ...prev, [key]: checked }))
                    }
                    className="scale-75"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Soft Skills */}
          <div className="mb-5">
            <h4
              className="text-xs font-semibold uppercase tracking-wider text-gray-800 mb-3 flex items-center gap-1.5"
              style={{ fontFamily: "Open Sans, sans-serif" }}
            >
              <Brain className="w-3 h-3 text-wedo-cyan" />
              Soft Skills
            </h4>
            <div className="space-y-2">
              <div className="flex gap-2">
                <Input
                  value={newSoftSkillFilter}
                  onChange={(e) => setNewSoftSkillFilter(e.target.value)}
                  placeholder="Ex: comunicação, liderança..."
                  className="h-8 text-xs"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && newSoftSkillFilter.trim()) {
                      if (!tableFilters.softSkills.includes(newSoftSkillFilter.trim())) {
                        setTableFilters((prev) => ({
                          ...prev,
                          softSkills: [...prev.softSkills, newSoftSkillFilter.trim()],
                        }))
                      }
                      setNewSoftSkillFilter("")
                    }
                  }}
                />
              </div>
              {tableFilters.softSkills.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {tableFilters.softSkills.map((skill) => (
                    <Badge key={skill} variant="secondary" className={`${badgeStyles.default} px-2 py-0.5 flex items-center gap-1`}>
                      {skill}
                      <button
                        onClick={() =>
                          setTableFilters((prev) => ({
                            ...prev,
                            softSkills: prev.softSkills.filter((s) => s !== skill),
                          }))
                        }
                      >
                        <X className="w-2.5 h-2.5" />
                      </button>
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Certificações */}
          <div className="mb-5">
            <h4
              className="text-xs font-semibold uppercase tracking-wider text-gray-800 mb-3 flex items-center gap-1.5"
              style={{ fontFamily: "Open Sans, sans-serif" }}
            >
              <Code className="w-3 h-3" />
              Certificações
            </h4>
            <div className="space-y-2">
              <div className="flex gap-2">
                <Input
                  value={newCertificationFilter}
                  onChange={(e) => setNewCertificationFilter(e.target.value)}
                  placeholder="Ex: AWS, PMP, Scrum..."
                  className="h-8 text-xs"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && newCertificationFilter.trim()) {
                      if (!tableFilters.certifications.includes(newCertificationFilter.trim())) {
                        setTableFilters((prev) => ({
                          ...prev,
                          certifications: [...prev.certifications, newCertificationFilter.trim()],
                        }))
                      }
                      setNewCertificationFilter("")
                    }
                  }}
                />
              </div>
              {tableFilters.certifications.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {tableFilters.certifications.map((cert) => (
                    <Badge key={cert} variant="secondary" className={`${badgeStyles.default} px-2 py-0.5 flex items-center gap-1`}>
                      {cert}
                      <button
                        onClick={() =>
                          setTableFilters((prev) => ({
                            ...prev,
                            certifications: prev.certifications.filter((c) => c !== cert),
                          }))
                        }
                      >
                        <X className="w-2.5 h-2.5" />
                      </button>
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Disponibilidade */}
          <div className="mb-5">
            <h4
              className="text-xs font-semibold uppercase tracking-wider text-gray-800 mb-3 flex items-center gap-1.5"
              style={{ fontFamily: "Open Sans, sans-serif" }}
            >
              <MapPin className="w-3 h-3" />
              Disponibilidade
            </h4>
            <div className="space-y-3">
              <div>
                <label className={`${textStyles.label} mb-1.5 block`}>Aberto a mudar</label>
                <TriStateButtons
                  value={tableFilters.willingToRelocate}
                  onChange={(v) => setTableFilters((prev) => ({ ...prev, willingToRelocate: v }))}
                />
              </div>
              <div>
                <label className={`${textStyles.label} mb-1.5 block`}>Mobilidade</label>
                <TriStateButtons
                  value={tableFilters.mobility}
                  onChange={(v) => setTableFilters((prev) => ({ ...prev, mobility: v }))}
                />
              </div>
              <div>
                <label className={`${textStyles.label} mb-1.5 block`}>Disponibilidade</label>
                <div className="grid grid-cols-2 gap-1.5">
                  {[
                    { value: "immediate", label: "Imediato" },
                    { value: "15_days", label: "15 dias" },
                    { value: "30_days", label: "30 dias" },
                    { value: "60_days", label: "60 dias" },
                  ].map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() =>
                        setTableFilters((prev) => ({
                          ...prev,
                          availabilityWindow:
                            prev.availabilityWindow === opt.value
                              ? undefined
                              : (opt.value as TableFilters["availabilityWindow"]),
                        }))
                      }
                      className="px-2 py-1.5 text-micro rounded-md transition-all"
                      style={{
                        backgroundColor:
                          tableFilters.availabilityWindow === opt.value ? "#111827" : "#f9fafb",
                        color: tableFilters.availabilityWindow === opt.value ? "white" : "#6b7280",
                        border:
                          tableFilters.availabilityWindow === opt.value
                            ? "none"
                            : "1px solid #e5e7eb",
                        fontFamily: "Open Sans, sans-serif",
                      }}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Shortlisted */}
          <div className="mb-5">
            <h4
              className="text-xs font-semibold uppercase tracking-wider text-gray-800 mb-3 flex items-center gap-1.5"
              style={{ fontFamily: "Open Sans, sans-serif" }}
            >
              <Bookmark className="w-3 h-3" />
              Shortlisted
            </h4>
            <div className="space-y-3">
              <div>
                <label className={`${textStyles.label} mb-1.5 block`}>Data Inclusão</label>
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    type="date"
                    value={tableFilters.shortlistedDateFrom ?? ""}
                    onChange={(e) =>
                      setTableFilters((prev) => ({
                        ...prev,
                        shortlistedDateFrom: e.target.value || undefined,
                      }))
                    }
                    className="h-8 text-xs"
                  />
                  <Input
                    type="date"
                    value={tableFilters.shortlistedDateTo ?? ""}
                    onChange={(e) =>
                      setTableFilters((prev) => ({
                        ...prev,
                        shortlistedDateTo: e.target.value || undefined,
                      }))
                    }
                    className="h-8 text-xs"
                  />
                </div>
              </div>
              <div>
                <label className={`${textStyles.label} mb-1.5 block`}>Vaga Origem</label>
                <Input
                  type="text"
                  value={tableFilters.shortlistedVacancyOrigin ?? ""}
                  onChange={(e) =>
                    setTableFilters((prev) => ({
                      ...prev,
                      shortlistedVacancyOrigin: e.target.value || undefined,
                    }))
                  }
                  className="h-8 text-xs"
                  placeholder="Nome ou ID da vaga de origem"
                />
              </div>
            </div>
          </div>

          {/* Placement */}
          <div className="mb-5">
            <h4
              className="text-xs font-semibold uppercase tracking-wider text-gray-800 mb-3 flex items-center gap-1.5"
              style={{ fontFamily: "Open Sans, sans-serif" }}
            >
              <CheckCircle className="w-3 h-3" />
              Placement
            </h4>
            <div className="space-y-3">
              <div>
                <label className={`${textStyles.label} mb-1.5 block`}>Data Colocação</label>
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    type="date"
                    value={tableFilters.placementDateFrom ?? ""}
                    onChange={(e) =>
                      setTableFilters((prev) => ({
                        ...prev,
                        placementDateFrom: e.target.value || undefined,
                      }))
                    }
                    className="h-8 text-xs"
                  />
                  <Input
                    type="date"
                    value={tableFilters.placementDateTo ?? ""}
                    onChange={(e) =>
                      setTableFilters((prev) => ({
                        ...prev,
                        placementDateTo: e.target.value || undefined,
                      }))
                    }
                    className="h-8 text-xs"
                  />
                </div>
              </div>
              <div>
                <label className={`${textStyles.label} mb-1.5 block`}>Vaga Destino</label>
                <Input
                  type="text"
                  value={tableFilters.placementVacancyDestination ?? ""}
                  onChange={(e) =>
                    setTableFilters((prev) => ({
                      ...prev,
                      placementVacancyDestination: e.target.value || undefined,
                    }))
                  }
                  className="h-8 text-xs"
                  placeholder="Nome ou ID da vaga"
                />
              </div>
              <div>
                <label className={`${textStyles.label} mb-1.5 block`}>Empresa Cliente</label>
                <Input
                  type="text"
                  value={tableFilters.placementClientCompany ?? ""}
                  onChange={(e) =>
                    setTableFilters((prev) => ({
                      ...prev,
                      placementClientCompany: e.target.value || undefined,
                    }))
                  }
                  className="h-8 text-xs"
                  placeholder="Nome da empresa"
                />
              </div>
            </div>
          </div>

          {/* Vaga Específica */}
          <div className="mb-5">
            <h4
              className="text-xs font-semibold uppercase tracking-wider text-gray-800 mb-3 flex items-center gap-1.5"
              style={{ fontFamily: "Open Sans, sans-serif" }}
            >
              <Bookmark className="w-3 h-3" />
              Vaga Específica
            </h4>
            <Input
              type="text"
              value={tableFilters.specificVacancyId ?? ""}
              onChange={(e) =>
                setTableFilters((prev) => ({
                  ...prev,
                  specificVacancyId: e.target.value || undefined,
                }))
              }
              className="h-8 text-xs"
              placeholder="Buscar vaga por ID ou nome..."
            />
          </div>

          {/* Data de Cadastro */}
          <div className="mb-5">
            <h4
              className="text-xs font-semibold uppercase tracking-wider text-gray-800 mb-3 flex items-center gap-1.5"
              style={{ fontFamily: "Open Sans, sans-serif" }}
            >
              <Calendar className="w-3 h-3" />
              Data de Cadastro
            </h4>
            <div className="grid grid-cols-2 gap-2">
              <Input
                type="date"
                value={tableFilters.registrationDateFrom ?? ""}
                onChange={(e) =>
                  setTableFilters((prev) => ({
                    ...prev,
                    registrationDateFrom: e.target.value || undefined,
                  }))
                }
                className="h-8 text-xs"
                placeholder="De"
              />
              <Input
                type="date"
                value={tableFilters.registrationDateTo ?? ""}
                onChange={(e) =>
                  setTableFilters((prev) => ({
                    ...prev,
                    registrationDateTo: e.target.value || undefined,
                  }))
                }
                className="h-8 text-xs"
                placeholder="Até"
              />
            </div>
          </div>

          {/* Botões de ação */}
          <div className="pt-4 border-t border-gray-100 space-y-2">
            <button
              className="w-full h-9 text-xs rounded-md transition-all border border-gray-200"
              style={{ fontFamily: "Open Sans, sans-serif" }}
              onClick={onClearAll}
            >
              Limpar Todos os Filtros
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Internal helpers (não exportados — uso exclusivo deste componente) ───────

interface CheckableItemProps {
  label: string
  checked: boolean
  onClick: () => void
}

function CheckableItem({ label, checked, onClick }: CheckableItemProps) {
  return (
    <div
      onClick={onClick}
      className="flex items-center gap-2.5 p-2 rounded-md cursor-pointer transition-all hover:bg-gray-50"
      style={{
        backgroundColor: checked ? "rgba(96,190,209,0.08)" : "transparent",
        border: checked ? "1px solid rgba(96,190,209,0.2)" : "1px solid transparent",
      }}
    >
      <div
        className="w-4 h-4 rounded flex items-center justify-center flex-shrink-0 transition-all"
        style={{
          backgroundColor: checked ? "#111827" : "transparent",
          border: checked ? "none" : "2px solid #d1d5db",
        }}
      >
        {checked && <Check className="w-3 h-3 text-white" strokeWidth={3} />}
      </div>
      <span
        className="text-xs"
        style={{ color: checked ? "#1f2937" : "#6b7280", fontFamily: "Open Sans, sans-serif" }}
      >
        {label}
      </span>
    </div>
  )
}

interface TagInputProps {
  placeholder: string
  tags: string[]
  onAdd: (value: string) => void
  onRemove: (value: string) => void
}

function TagInput({ placeholder, tags, onAdd, onRemove }: TagInputProps) {
  return (
    <div className="space-y-2">
      <Input
        placeholder={placeholder}
        className="h-8 text-xs"
        onKeyDown={(e) => {
          const value = (e.target as HTMLInputElement).value.trim()
          if (e.key === "Enter" && value && !tags.includes(value)) {
            onAdd(value)
            ;(e.target as HTMLInputElement).value = ""
          }
        }}
      />
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {tags.map((tag) => (
            <Badge key={tag} variant="secondary" className="text-micro px-2 py-0.5 flex items-center gap-1">
              {tag}
              <button onClick={() => onRemove(tag)}>
                <X className="w-2.5 h-2.5" />
              </button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  )
}

interface TriStateButtonsProps {
  value: boolean | null
  onChange: (value: boolean | null) => void
}

function TriStateButtons({ value, onChange }: TriStateButtonsProps) {
  const options = [
    { value: null, label: "Todos" },
    { value: true, label: "Sim" },
    { value: false, label: "Não" },
  ]
  return (
    <div className="flex gap-1.5">
      {options.map((opt) => (
        <button
          key={String(opt.value)}
          onClick={() => onChange(opt.value)}
          className="flex-1 px-2 py-1.5 text-micro rounded-md transition-all"
          style={{
            backgroundColor: value === opt.value ? "#111827" : "#f9fafb",
            color: value === opt.value ? "white" : "#6b7280",
            border: value === opt.value ? "none" : "1px solid #e5e7eb",
            fontFamily: "Open Sans, sans-serif",
          }}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}
