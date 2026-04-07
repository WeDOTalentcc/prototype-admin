"use client"

import {
  Check, Pencil, Trash2, Loader2,
  ChevronUp, ChevronDown,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import type { ArchetypeVacancy } from "./smart-search-input"

interface ArchetypeFilters {
  skills?: string[]
  languages?: string[]
  experience_years_min?: number
  location?: string
  work_model?: string
  employment_type?: string
  [key: string]: unknown
}

export interface ArchetypeCardExpandedProps {
  arch: ArchetypeVacancy
  isExpanded: boolean
  isSelected: boolean
  isDeletingArchetype: string | null
  onToggleExpand: () => void
  onSelectArchetype: (arch: ArchetypeVacancy) => void
  onArchetypeSearchPromptChange: (v: string) => void
  onExpandedArchetypeIdChange: (id: string | null) => void
  buildArchetypePrompt: (arch: ArchetypeVacancy) => string
  onOpenEditArchetype: (arch: ArchetypeVacancy, e: React.MouseEvent) => void
  onDeleteArchetype: (archId: string, e: React.MouseEvent) => void
}

export function ArchetypeCardExpanded({
  arch,
  isExpanded,
  isSelected,
  isDeletingArchetype,
  onToggleExpand,
  onSelectArchetype,
  onArchetypeSearchPromptChange,
  onExpandedArchetypeIdChange,
  buildArchetypePrompt,
  onOpenEditArchetype,
  onDeleteArchetype,
}: ArchetypeCardExpandedProps) {
  return (
    <div
      className={cn(
        "group relative w-full rounded-md text-left transition-colors cursor-pointer border",
        isExpanded
          ? "bg-lia-bg-secondary ring-1 ring-lia-btn-primary-bg/20 border-lia-border-default"
          : isSelected
          ? "bg-lia-bg-secondary ring-1 ring-lia-btn-primary-bg/20 border-lia-border-default"
          : "bg-lia-bg-primary hover:bg-lia-bg-secondary border-lia-border-subtle"
      )}
    >
      <div
        className="px-3 py-2.5"
        onClick={onToggleExpand}
      >
        <div className="flex items-center gap-2">
          <span className="text-base-ui flex-shrink-0">{arch.emoji || "🎯"}</span>
          <span className="font-semibold text-xs truncate text-lia-text-primary">
            {arch.name || arch.title}
          </span>
          {arch.is_default && (
            <span
              className="text-micro px-1.5 py-0.5 rounded-full flex-shrink-0 font-medium bg-wedo-cyan/15"
            >
              Padrão
            </span>
          )}
          {!isExpanded && arch.tags && arch.tags.length > 0 && (
            <div className="flex items-center gap-1 ml-auto flex-shrink-0 group-hover:hidden">
              {arch.tags.slice(0, 2).map((tag: string) => (
                <span
                  key={tag}
                  className="text-micro px-1.5 py-0.5 rounded-full bg-lia-bg-tertiary"
                >
                  {tag}
                </span>
              ))}
              {arch.tags.length > 2 && (
                <span className="text-micro px-1 py-0.5 text-lia-text-tertiary">
                  +{arch.tags.length - 2}
                </span>
              )}
            </div>
          )}
          <div className="ml-auto flex items-center gap-1 flex-shrink-0">
            {isExpanded ? (
              <ChevronUp className="w-3.5 h-3.5 text-lia-text-primary" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5 text-lia-text-tertiary" />
            )}
          </div>
        </div>
        {!isExpanded && arch.description && (
          <p className="mt-1 pl-5 text-micro line-clamp-1"> {/* [OPT-022] px arbitrário — sem canônico Tailwind */}
            {arch.description}
          </p>
        )}
      </div>

      {isExpanded && (
        <div
          className="px-3 pb-3 space-y-2 border-t border-t-lia-border-subtle pt-2.5"
        >
          {arch.description && (
            <p className="text-micro">{arch.description}</p>
          )}

          <div className="space-y-1">
            <span className="text-micro font-medium text-lia-text-tertiary">Query de Busca</span>
            <p className="text-xs p-2 rounded-md">
              {arch.query || "Sem query definida"}
            </p>
          </div>

          {arch.tags && arch.tags.length > 0 && (
            <div className="space-y-1">
              <span className="text-micro font-medium text-lia-text-tertiary">Tags</span>
              <div className="flex flex-wrap gap-1">
                {arch.tags.map((tag: string) => (
                  <span
                    key={tag}
                    className="text-micro px-1.5 py-0.5 rounded-full bg-lia-bg-tertiary"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {((arch.filters as ArchetypeFilters))?.skills && (((arch.filters as ArchetypeFilters))?.skills?.length ?? 0) > 0 && (
            <div className="space-y-1">
              <span className="text-micro font-medium text-lia-text-tertiary">Skills</span>
              <div className="flex flex-wrap gap-1">
                {((arch.filters as ArchetypeFilters))?.skills?.map((skill: string) => (
                  <span
                    key={skill}
                    className="text-micro px-1.5 py-0.5 rounded-full bg-lia-bg-tertiary"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="flex flex-wrap gap-2 text-micro">
            {arch.seniority && (
              <div className="flex items-center gap-1">
                <span className="text-lia-text-tertiary">Senioridade:</span>
                <span className="font-medium capitalize text-lia-text-primary">
                  {arch.seniority}
                </span>
              </div>
            )}
            {arch.industry && (
              <div className="flex items-center gap-1">
                <span className="text-lia-text-tertiary">Indústria:</span>
                <span className="font-medium capitalize text-lia-text-primary">
                  {arch.industry}
                </span>
              </div>
            )}
            {!!(arch.filters?.experience_years_min) && (
              <div className="flex items-center gap-1">
                <span className="text-lia-text-tertiary">Experiência:</span>
                <span className="font-medium text-lia-text-primary">
                  {((arch.filters as ArchetypeFilters)).experience_years_min}+ anos
                </span>
              </div>
            )}
            {!!(arch.filters?.location) && (
              <div className="flex items-center gap-1">
                <span className="text-lia-text-tertiary">Localização:</span>
                <span className="font-medium text-lia-text-primary">{((arch.filters as ArchetypeFilters)).location}</span>
              </div>
            )}
            {!!(arch.filters?.work_model) && (
              <div className="flex items-center gap-1">
                <span className="text-lia-text-tertiary">Modelo:</span>
                <span className="font-medium text-lia-text-primary">
                  {((arch.filters as ArchetypeFilters)).work_model === "remote"
                    ? "Remoto"
                    : ((arch.filters as ArchetypeFilters)).work_model === "hybrid"
                    ? "Híbrido"
                    : ((arch.filters as ArchetypeFilters)).work_model === "onsite"
                    ? "Presencial"
                    : ((arch.filters as ArchetypeFilters)).work_model}
                </span>
              </div>
            )}
            {!!(arch.filters?.employment_type) && (
              <div className="flex items-center gap-1">
                <span className="text-lia-text-tertiary">Contrato:</span>
                <span className="font-medium text-lia-text-primary">
                  {((arch.filters as ArchetypeFilters)).employment_type === "clt"
                    ? "CLT"
                    : ((arch.filters as ArchetypeFilters)).employment_type === "pj"
                    ? "PJ"
                    : ((arch.filters as ArchetypeFilters)).employment_type === "intern"
                    ? "Estágio"
                    : ((arch.filters as ArchetypeFilters)).employment_type === "temporary"
                    ? "Temporário"
                    : ((arch.filters as ArchetypeFilters)).employment_type === "freelancer"
                    ? "Freelancer"
                    : ((arch.filters as ArchetypeFilters)).employment_type}
                </span>
              </div>
            )}
          </div>

          {((arch.filters as ArchetypeFilters))?.languages && (((arch.filters as ArchetypeFilters))?.languages?.length ?? 0) > 0 && (
            <div className="space-y-1">
              <span className="text-micro font-medium text-lia-text-tertiary">Idiomas</span>
              <div className="flex flex-wrap gap-1">
                {((arch.filters as ArchetypeFilters))?.languages?.map((lang: string) => (
                  <span
                    key={lang}
                    className="px-1.5 py-0.5 rounded-full text-micro bg-lia-bg-tertiary"
                  >
                    {lang}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="flex items-center gap-2 pt-2 mt-1 border-t border-t-lia-border-subtle">
            <Button
              size="sm"
              onClick={(e) => {
                e.stopPropagation()
                onSelectArchetype(arch)
                onArchetypeSearchPromptChange(buildArchetypePrompt(arch))
                onExpandedArchetypeIdChange(null)
              }}
              className="flex-1 text-xs h-8 bg-lia-btn-primary-hover text-white"
            >
              <Check className="w-3 h-3 mr-1" />
              Usar Arquétipo
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={(e) => onOpenEditArchetype(arch, e)}
              className="text-xs h-8"
            >
              <Pencil className="w-3 h-3 mr-1" />
              Editar
            </Button>
            {!arch.is_default && (
              <Button
                size="sm"
                variant="ghost"
                onClick={(e) => onDeleteArchetype(arch.id, e)}
                disabled={isDeletingArchetype === arch.id}
                className="text-xs px-2 text-status-error"
              >
                {isDeletingArchetype === arch.id ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
                ) : (
                  <Trash2 className="w-3.5 h-3.5" />
                )}
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
