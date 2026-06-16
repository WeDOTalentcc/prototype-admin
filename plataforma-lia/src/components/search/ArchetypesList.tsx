"use client"

/**
 * ArchetypesList — Aba de arquétipos: criar, listar, editar e deletar arquétipos de busca.
 *
 * Extraído de ExpandableAIPrompt (P1-E).
 * Portabilidade Vue: mapeia para componente ArchetypesList.vue.
 */

import React from"react"
import {
  Brain, Wand2, Loader2, Target, Search, MapPin, Building2, Plus, Pencil, Trash2,
} from"lucide-react"
import { Chip } from "@/components/ui/chip"
import type { ArchetypeData, BackendEntities } from"@/components/search/expandable-ai-prompt.types"

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
          <span className="text-xs font-medium text-lia-text-primary">Criar Novo Arquétipo</span>
          {naturalSearchValue && (
            <Chip variant="neutral" className="text-micro bg-wedo-cyan/10 text-lia-text-secondary border-lia-btn-primary-bg dark:border-lia-border-subtle">
              Busca ativa detectada
            </Chip>
          )}
        </div>

        {/* Contexto de busca atual */}
        {naturalSearchValue && (
          <div className="p-3 rounded-xl border border-wedo-cyan/30 bg-wedo-cyan/5">
            <div className="flex items-start gap-2 mb-2">
              <Brain className="w-3.5 h-3.5 text-wedo-cyan mt-0.5" />
              <span className="text-xs text-lia-text-secondary">Contexto da busca atual:</span>
            </div>
            <p className="text-sm text-lia-text-primary mb-2">{naturalSearchValue}</p>

            {/* Tags de entidades extraídas */}
            {Object.keys(parsedEntities).length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {parsedEntities.job_title && (
                  <Chip variant="neutral" muted className="text-micro -dark border-lia-border-default dark:border-lia-border-default">
                    {parsedEntities.job_title}
                  </Chip>
                )}
                {parsedEntities.location && (
                  <Chip variant="neutral" muted className="text-micro bg-lia-bg-secondary text-lia-text-primary border-lia-border-subtle">
                    <MapPin className="w-2.5 h-2.5 mr-0.5" />
                    {parsedEntities.location}
                  </Chip>
                )}
                {parsedEntities.seniority && (
                  <Chip variant="neutral" muted className="text-micro bg-lia-bg-secondary text-lia-text-primary border-lia-border-subtle">
                    {parsedEntities.seniority}
                  </Chip>
                )}
                {parsedEntities.industry && (
                  <Chip variant="neutral" muted className="text-micro bg-lia-bg-secondary text-lia-text-primary border-lia-border-subtle">
                    <Building2 className="w-2.5 h-2.5 mr-0.5" />
                    {parsedEntities.industry}
                  </Chip>
                )}
                {parsedEntities.skills && parsedEntities.skills.map((skill, idx) => (
                  <Chip key={idx} variant="neutral" muted className="text-micro bg-lia-bg-secondary text-lia-text-primary border-lia-border-subtle">
                    {skill}
                  </Chip>
                ))}
              </div>
            )}

            {/* Salvar como arquétipo (quando há entidades) vs usar como base */}
            {hasParsedEntities() ? (
              <button
                onClick={onCreateFromActiveSearch}
                disabled={isCreatingFromSearch}
                className="mt-3 w-full px-3 py-2 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active text-xs rounded-md transition-colors motion-reduce:transition-none flex items-center justify-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isCreatingFromSearch ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
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
                className="mt-3 w-full px-3 py-1.5 bg-lia-bg-tertiary text-lia-text-primary text-xs rounded-xl hover:bg-lia-interactive-active transition-colors motion-reduce:transition-none flex items-center justify-center gap-1.5"
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
            <div className="flex-1 h-px bg-lia-interactive-active" />
            <span className="text-micro text-lia-text-tertiary">ou crie do zero com IA</span>
            <div className="flex-1 h-px bg-lia-interactive-active" />
          </div>
        )}

        {/* Campo de descrição */}
        <div className="relative">
          <textarea
            value={newArchetypeDescription}
            onChange={(e) => onNewArchetypeDescriptionChange(e.target.value)}
            placeholder="Descreva o perfil ideal: cargo, habilidades, experiência..."
            className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-lg text-lia-text-primary focus:outline-none focus:border-red-400 focus:ring-2 focus:ring-red-400/20 w-full px-3 py-2.5 text-sm resize-none"
            rows={2}
          />
        </div>

        <button
          onClick={() => onCreateFromDescription(newArchetypeDescription)}
          disabled={isCreatingArchetype || !newArchetypeDescription.trim()}
          className="w-full px-3 py-2 bg-lia-btn-primary-bg text-lia-btn-primary-text text-xs rounded-md hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isCreatingArchetype ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
              Criando arquétipo...
            </>
          ) : (
            <>
              <Wand2 className="w-3.5 h-3.5" />
              Criar Arquétipo com IA
            </>
          )}
        </button>
      </div>

      {/* Divisor */}
      <div className="flex items-center gap-2">
        <div className="flex-1 h-px bg-lia-interactive-active" />
        <span className="text-xs text-lia-text-secondary">ou selecione um existente</span>
        <div className="flex-1 h-px bg-lia-interactive-active" />
      </div>

      {/* Lista de Arquétipos Existentes */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-lia-text-primary">Meus Arquétipos</span>
          <Chip variant="neutral" className="text-micro">
            {filteredArchetypes.length} {filteredArchetypes.length === 1 ? 'arquétipo' : 'arquétipos'}
          </Chip>
        </div>

        {/* Campo de busca */}
        {archetypes.length > 3 && (
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-lia-text-tertiary" />
            <input
              type="text"
              value={archetypeSearchFilter}
              onChange={(e) => onArchetypeSearchFilterChange(e.target.value)}
              placeholder="Buscar arquétipos..."
              className="w-full pl-8 pr-3 py-1.5 text-xs rounded-xl border border-lia-border-subtle focus:outline-none focus:ring-2 focus:ring-lia-border-medium focus:border-transparent"
            />
          </div>
        )}

        {/* Cards */}
        <div className="space-y-2 max-h-chart-sm overflow-y-auto">
          {filteredArchetypes.length === 0 ? (
            <div className="text-center py-6 text-lia-text-secondary">
              <Target className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-xs" aria-live="polite" aria-atomic="true">Nenhum arquétipo encontrado</p>
              <p className="text-micro text-lia-text-tertiary mt-1">Crie um novo acima para começar</p>
            </div>
          ) : (
            filteredArchetypes.map((arch) => {
              const archExtended = arch as ArchetypeData & { query?: string; emoji?: string }
              const query = archExtended.query || (arch.criteria as Record<string, unknown> | undefined)?.query as string || arch.description ||""
              return (
                <div
                  key={arch.id}
                  className="group relative p-3 rounded-xl border border-lia-border-subtle bg-lia-bg-primary hover:border-lia-border-medium transition-colors motion-reduce:transition-none cursor-pointer"
                  onClick={() => onSelectArchetype(arch.id, query)}
                >
                  {/* Edit/Delete */}
                  <div className="absolute top-2 right-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none">
                    <button
                      onClick={(e) => onEditArchetype(arch, e)}
                      className="p-1 rounded-xl hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none"
                      title="Editar arquétipo"
                    >
                      <Pencil className="w-3.5 h-3.5 text-lia-text-tertiary hover:text-lia-text-secondary" />
                    </button>
                    <button
                      onClick={(e) => onDeleteArchetype(arch, e)}
                      disabled={isDeletingArchetype === arch.id}
                      className="p-1 rounded-md hover:bg-status-error/10 transition-colors motion-reduce:transition-none"
                      title="Excluir arquétipo"
                    >
                      {isDeletingArchetype === arch.id ? (
                        <Loader2 className="w-3.5 h-3.5 text-lia-text-tertiary animate-spin motion-reduce:animate-none" />
                      ) : (
                        <Trash2 className="w-3.5 h-3.5 text-lia-text-tertiary hover:text-status-error" />
                      )}
                    </button>
                  </div>

                  <div className="flex items-start gap-2.5 pr-16">
                    <span className="text-lg flex-shrink-0">{archExtended.emoji ||"🎯"}</span>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-lia-text-primary truncate">{arch.name}</div>
                      {arch.description && (
                        <p className="text-xs text-lia-text-secondary mt-0.5 line-clamp-2">{arch.description}</p>
                      )}
                      {arch.department && (
                        <Chip variant="neutral" className="mt-1.5 text-micro">{arch.department}</Chip>
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
