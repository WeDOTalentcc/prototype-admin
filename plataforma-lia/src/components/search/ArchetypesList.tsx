"use client"

/**
 * ArchetypesList — Aba de arquétipos: criar, listar, editar e deletar arquétipos de busca.
 *
 * Extraído de ExpandableAIPrompt (P1-E).
 * Portabilidade Vue: mapeia para componente ArchetypesList.vue.
 */

import React from "react"
import {
  Brain, Wand2, Loader2, Target, Search, MapPin, Building2, Plus, Pencil, Trash2,
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
import type { ArchetypeData, BackendEntities } from "@/components/search/expandable-ai-prompt.types"

interface ArchetypesListProps {
  archetypes: ArchetypeData[]
  filteredArchetypes: ArchetypeData[]
  archetypeSearchFilter: string
  onArchetypeSearchFilterChange: (v: string) => void
  naturalSearchValue: string
  parsedEntities: BackendEntities
  newArchetypeDescription: string
  onNewArchetypeDescriptionChange: (v: string) => void
  isCreatingArchetype: boolean
  isCreatingFromSearch: boolean
  isDeletingArchetype: string | null
  hasParsedEntities: () => boolean
  onCreateFromActiveSearch: () => void
  onCreateFromDescription: (desc: string) => void
  onSelectArchetype: (archetypeId: string, query: string) => void
  onEditArchetype: (arch: ArchetypeData, e: React.MouseEvent) => void
  onDeleteArchetype: (arch: ArchetypeData, e: React.MouseEvent) => void
  onUseAsBase: (value: string) => void
}

export function ArchetypesList({
  archetypes,
  filteredArchetypes,
  archetypeSearchFilter,
  onArchetypeSearchFilterChange,
  naturalSearchValue,
  parsedEntities,
  newArchetypeDescription,
  onNewArchetypeDescriptionChange,
  isCreatingArchetype,
  isCreatingFromSearch,
  isDeletingArchetype,
  hasParsedEntities,
  onCreateFromActiveSearch,
  onCreateFromDescription,
  onSelectArchetype,
  onEditArchetype,
  onDeleteArchetype,
  onUseAsBase,
}: ArchetypesListProps) {
  return (
    <div className="space-y-4">
      {/* Criar Arquétipo */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Criar Novo Arquétipo</span>
          {naturalSearchValue && (
            <Badge variant="outline" className="text-micro bg-wedo-cyan/10 text-gray-600 dark:text-gray-400 border-gray-900 dark:border-gray-50">
              Busca ativa detectada
            </Badge>
          )}
        </div>

        {/* Contexto de busca atual */}
        {naturalSearchValue && (
          <div className="p-3 rounded-md border border-wedo-cyan/30 bg-wedo-cyan/5">
            <div className="flex items-start gap-2 mb-2">
              <Brain className="w-3.5 h-3.5 text-wedo-cyan mt-0.5" />
              <span className="text-xs text-gray-600">Contexto da busca atual:</span>
            </div>
            <p className="text-sm text-gray-800 mb-2">{naturalSearchValue}</p>

            {/* Tags de entidades extraídas */}
            {Object.keys(parsedEntities).length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {parsedEntities.job_title && (
                  <Badge variant="secondary" className="text-micro bg-wedo-cyan/10 text-wedo-cyan-dark border-gray-300 dark:border-gray-600">
                    {parsedEntities.job_title}
                  </Badge>
                )}
                {parsedEntities.location && (
                  <Badge variant="secondary" className="text-micro bg-gray-50 text-gray-700 border-gray-200">
                    <MapPin className="w-2.5 h-2.5 mr-0.5" />
                    {parsedEntities.location}
                  </Badge>
                )}
                {parsedEntities.seniority && (
                  <Badge variant="secondary" className="text-micro bg-gray-50 text-gray-700 border-gray-200">
                    {parsedEntities.seniority}
                  </Badge>
                )}
                {parsedEntities.industry && (
                  <Badge variant="secondary" className="text-micro bg-gray-50 text-gray-700 border-gray-200">
                    <Building2 className="w-2.5 h-2.5 mr-0.5" />
                    {parsedEntities.industry}
                  </Badge>
                )}
                {parsedEntities.skills && parsedEntities.skills.map((skill, idx) => (
                  <Badge key={idx} variant="secondary" className="text-micro bg-gray-50 text-gray-700 border-gray-200">
                    {skill}
                  </Badge>
                ))}
              </div>
            )}

            {/* Salvar como arquétipo (quando há entidades) vs usar como base */}
            {hasParsedEntities() ? (
              <button
                onClick={onCreateFromActiveSearch}
                disabled={isCreatingFromSearch}
                className="mt-3 w-full px-3 py-2 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 text-xs rounded-md transition-colors flex items-center justify-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isCreatingFromSearch ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    Salvando arquétipo...
                  </>
                ) : (
                  <>
                    <Target className="w-3.5 h-3.5" />
                    Salvar Busca como Arquétipo
                  </>
                )}
              </button>
            ) : (
              <button
                onClick={() => onUseAsBase(naturalSearchValue)}
                className="mt-3 w-full px-3 py-1.5 bg-gray-100 text-gray-800 dark:text-gray-200 text-xs rounded-md hover:bg-gray-200 transition-colors flex items-center justify-center gap-1.5"
              >
                <Plus className="w-3 h-3" />
                Usar como base para novo arquétipo
              </button>
            )}
          </div>
        )}

        {/* Divisor condicional */}
        {naturalSearchValue && hasParsedEntities() && (
          <div className="flex items-center gap-2">
            <div className="flex-1 h-px bg-gray-200" />
            <span className="text-micro text-gray-400">ou crie do zero com LIA</span>
            <div className="flex-1 h-px bg-gray-200" />
          </div>
        )}

        {/* Campo de descrição */}
        <div className="relative">
          <textarea
            value={newArchetypeDescription}
            onChange={(e) => onNewArchetypeDescriptionChange(e.target.value)}
            placeholder="Descreva o perfil ideal: cargo, habilidades, experiência..."
            className="lia-input w-full px-3 py-2.5 text-sm resize-none"
            rows={2}
          />
        </div>

        <button
          onClick={() => onCreateFromDescription(newArchetypeDescription)}
          disabled={isCreatingArchetype || !newArchetypeDescription.trim()}
          className="w-full px-3 py-2 bg-gray-900 text-white text-xs rounded-md hover:bg-gray-800 transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isCreatingArchetype ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              Criando arquétipo...
            </>
          ) : (
            <>
              <Wand2 className="w-3.5 h-3.5" />
              Criar Arquétipo com LIA
            </>
          )}
        </button>
      </div>

      {/* Divisor */}
      <div className="flex items-center gap-2">
        <div className="flex-1 h-px bg-gray-200" />
        <span className="text-xs text-gray-500">ou selecione um existente</span>
        <div className="flex-1 h-px bg-gray-200" />
      </div>

      {/* Lista de Arquétipos Existentes */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Meus Arquétipos</span>
          <Badge variant="outline" className="text-micro">
            {filteredArchetypes.length} {filteredArchetypes.length === 1 ? 'arquétipo' : 'arquétipos'}
          </Badge>
        </div>

        {/* Campo de busca */}
        {archetypes.length > 3 && (
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
            <input
              type="text"
              value={archetypeSearchFilter}
              onChange={(e) => onArchetypeSearchFilterChange(e.target.value)}
              placeholder="Buscar arquétipos..."
              className="w-full pl-8 pr-3 py-1.5 text-xs rounded-md border border-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:border-transparent"
            />
          </div>
        )}

        {/* Cards */}
        <div className="space-y-2 max-h-[200px] overflow-y-auto">
          {filteredArchetypes.length === 0 ? (
            <div className="text-center py-6 text-gray-500">
              <Target className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-xs">Nenhum arquétipo encontrado</p>
              <p className="text-micro text-gray-400 mt-1">Crie um novo acima para começar</p>
            </div>
          ) : (
            filteredArchetypes.map((arch) => {
              const archExtended = arch as ArchetypeData & { query?: string; emoji?: string }
              const query = archExtended.query || (arch.criteria as Record<string, unknown> | undefined)?.query as string || arch.description || ""
              return (
                <div
                  key={arch.id}
                  className="group relative p-3 rounded-md border border-gray-100 bg-white hover:border-gray-400 hover:transition-all cursor-pointer"
                  onClick={() => onSelectArchetype(arch.id, query)}
                >
                  {/* Edit/Delete */}
                  <div className="absolute top-2 right-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={(e) => onEditArchetype(arch, e)}
                      className="p-1 rounded hover:bg-gray-100 transition-colors"
                      title="Editar arquétipo"
                    >
                      <Pencil className="w-3.5 h-3.5 text-gray-400 hover:text-gray-600" />
                    </button>
                    <button
                      onClick={(e) => onDeleteArchetype(arch, e)}
                      disabled={isDeletingArchetype === arch.id}
                      className="p-1 rounded hover:bg-status-error/10 transition-colors"
                      title="Excluir arquétipo"
                    >
                      {isDeletingArchetype === arch.id ? (
                        <Loader2 className="w-3.5 h-3.5 text-gray-400 animate-spin" />
                      ) : (
                        <Trash2 className="w-3.5 h-3.5 text-gray-400 hover:text-status-error" />
                      )}
                    </button>
                  </div>

                  <div className="flex items-start gap-2.5 pr-16">
                    <span className="text-lg flex-shrink-0">{archExtended.emoji || "🎯"}</span>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-gray-800 truncate">{arch.name}</div>
                      {arch.description && (
                        <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{arch.description}</p>
                      )}
                      {arch.department && (
                        <Badge variant="outline" className="mt-1.5 text-micro">{arch.department}</Badge>
                      )}
                    </div>
                  </div>
                </div>
              )
            })
          )}
        </div>
      </div>
    </div>
  )
}
