"use client"

import React from 'react'
import { Badge } from "@/components/ui/badge"
import {
  Brain, Building2, Loader2, MapPin, Pencil, Plus, Search, Target, Trash2, Wand2, X
} from "lucide-react"
import { useExpandableAIPromptCore } from "../useExpandableAIPromptCore"

type EAPTabArquetipossProps = Pick<
  ReturnType<typeof useExpandableAIPromptCore>,
  'naturalSearchValue' | 'parsedEntities' | 'hasParsedEntities' |
  'newArchetypeDescription' | 'setNewArchetypeDescription' |
  'createArchetypeFromActiveSearch' | 'createArchetypeFromDescription' |
  'isCreatingArchetype' | 'isCreatingFromSearch' | 'isDeletingArchetype' |
  'archetypes' | 'filteredArchetypes' | 'archetypeSearchFilter' | 'setArchetypeSearchFilter' |
  'openEditArchetype' | 'openDeleteArchetypeDialog' | 'setSelectedArquetipo' |
  'onCommand'
>

export const EAPTabArquetipos = React.memo(function EAPTabArquetipos(props: EAPTabArquetipossProps) {
  const {
    naturalSearchValue, parsedEntities, hasParsedEntities,
    newArchetypeDescription, setNewArchetypeDescription,
    createArchetypeFromActiveSearch, createArchetypeFromDescription,
    isCreatingArchetype, isCreatingFromSearch, isDeletingArchetype,
    archetypes, filteredArchetypes, archetypeSearchFilter, setArchetypeSearchFilter,
    openEditArchetype, openDeleteArchetypeDialog, setSelectedArquetipo,
    onCommand,
  } = props

  return (
    <div className="space-y-4">
      {/* Seção: Criar Arquétipo com contexto de busca */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary">Criar Novo Arquétipo</span>
          {naturalSearchValue && (
            <Badge variant="outline" className="text-micro bg-wedo-cyan/10 text-lia-text-secondary dark:text-lia-text-tertiary border-gray-900">
              Busca ativa detectada
            </Badge>
          )}
        </div>

        {/* Pré-preenchimento com contexto de busca */}
        {naturalSearchValue && (
          <div className="p-3 rounded-md border border-wedo-cyan/30 bg-wedo-cyan/5">
            <div className="flex items-start gap-2 mb-2">
              <Brain className="w-3.5 h-3.5 text-wedo-cyan mt-0.5" />
              <span className="text-xs lia-text-base">Contexto da busca atual:</span>
            </div>
            <p className="text-sm lia-text-strong mb-2">{naturalSearchValue}</p>

            {/* Tags de entidades extraídas */}
            {Object.keys(parsedEntities).length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {parsedEntities.job_title && (
                  <Badge variant="secondary" className="text-micro bg-wedo-cyan/10 text-wedo-cyan-dark border-lia-border-default dark:border-lia-border-default">
                    {parsedEntities.job_title}
                  </Badge>
                )}
                {parsedEntities.location && (
                  <Badge variant="secondary" className="text-micro bg-gray-50 lia-text-base border-lia-border-subtle">
                    <MapPin className="w-2.5 h-2.5 mr-0.5" />
                    {parsedEntities.location}
                  </Badge>
                )}
                {parsedEntities.seniority && (
                  <Badge variant="secondary" className="text-micro bg-gray-50 lia-text-base border-lia-border-subtle">
                    {parsedEntities.seniority}
                  </Badge>
                )}
                {parsedEntities.industry && (
                  <Badge variant="secondary" className="text-micro bg-gray-50 lia-text-base border-lia-border-subtle">
                    <Building2 className="w-2.5 h-2.5 mr-0.5" />
                    {parsedEntities.industry}
                  </Badge>
                )}
                {parsedEntities.skills && parsedEntities.skills.map((skill, idx) => (
                  <Badge key={idx} variant="secondary" className="text-micro bg-gray-50 lia-text-base border-lia-border-subtle">
                    {skill}
                  </Badge>
                ))}
              </div>
            )}

            {/* Botão primário: Salvar busca como arquétipo (quando há entidades) */}
            {hasParsedEntities() ? (
              <button
                onClick={createArchetypeFromActiveSearch}
                disabled={isCreatingFromSearch}
                className="mt-3 w-full px-3 py-2 bg-gray-900 hover:bg-gray-800 text-white dark:hover:bg-gray-200 text-xs rounded-md transition-colors motion-reduce:transition-none flex items-center justify-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
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
                onClick={() => {
                  setNewArchetypeDescription(naturalSearchValue)
                }}
                className="mt-3 w-full px-3 py-1.5 bg-gray-100 text-lia-text-primary dark:text-lia-text-primary text-xs rounded-md hover:bg-gray-200 transition-colors motion-reduce:transition-none flex items-center justify-center gap-1.5"
              >
                <Plus className="w-3 h-3" />
                Usar como base para novo arquétipo
              </button>
            )}
          </div>
        )}

        {/* Divisor quando há busca ativa */}
        {naturalSearchValue && hasParsedEntities() && (
          <div className="flex items-center gap-2">
            <div className="flex-1 h-px bg-gray-200" />
            <span className="text-micro lia-text-secondary">ou crie do zero com LIA</span>
            <div className="flex-1 h-px bg-gray-200" />
          </div>
        )}

        {/* Campo de descrição para criar arquétipo */}
        <div className="relative">
          <textarea
            value={newArchetypeDescription}
            onChange={(e) => setNewArchetypeDescription(e.target.value)}
            placeholder="Descreva o perfil ideal: cargo, habilidades, experiência..."
            className="border border-input bg-background rounded-lg text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring w-full px-3 py-2.5 text-sm resize-none"
            rows={2}
          />
        </div>

        <button
          onClick={() => createArchetypeFromDescription(newArchetypeDescription)}
          disabled={isCreatingArchetype || !newArchetypeDescription.trim()}
          className="w-full px-3 py-2 bg-gray-900 text-white text-xs rounded-md hover:bg-gray-800 transition-colors motion-reduce:transition-none flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isCreatingArchetype ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
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
        <span className="text-xs lia-text-secondary">ou selecione um existente</span>
        <div className="flex-1 h-px bg-gray-200" />
      </div>

      {/* Lista de Arquétipos Existentes */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary">Meus Arquétipos</span>
          <Badge variant="outline" className="text-micro">
            {filteredArchetypes.length} {filteredArchetypes.length === 1 ? 'arquétipo' : 'arquétipos'}
          </Badge>
        </div>

        {/* Campo de busca */}
        {archetypes.length > 3 && (
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 lia-text-secondary" />
            <input
              type="text"
              value={archetypeSearchFilter}
              onChange={(e) => setArchetypeSearchFilter(e.target.value)}
              placeholder="Buscar arquétipos..."
              className="w-full pl-8 pr-3 py-1.5 text-xs rounded-md border border-lia-border-subtle focus:outline-none focus:ring-2 focus:ring-gray-400 focus:border-transparent"
            />
          </div>
        )}

        {/* Cards de Arquétipos */}
        <div className="space-y-2 max-h-[200px] overflow-y-auto">
          {filteredArchetypes.length === 0 ? (
            <div className="text-center py-6 lia-text-secondary">
              <Target className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-xs" aria-live="polite" aria-atomic="true">Nenhum arquétipo encontrado</p>
              <p className="text-micro lia-text-secondary mt-1">Crie um novo acima para começar</p>
            </div>
          ) : (
            filteredArchetypes.map((arch) => (
              <div
                key={arch.id}
                className="group relative p-3 rounded-md border border-lia-border-subtle bg-lia-bg-primary hover:border-gray-400 transition-colors motion-reduce:transition-none cursor-pointer"
                onClick={() => {
                  setSelectedArquetipo(arch.id)
                  const query = arch.query || arch.criteria?.query || arch.description || ""
                  if (query) {
                    onCommand(query, 'archetype_search')
                  }
                }}
              >
                {/* Edit/Delete buttons */}
                <div className="absolute top-2 right-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none">
                  <button
                    onClick={(e) => openEditArchetype(arch, e)}
                    className="p-1 rounded-md hover:bg-gray-100 transition-colors motion-reduce:transition-none"
                    title="Editar arquétipo"
                  >
                    <Pencil className="w-3.5 h-3.5 lia-text-secondary hover:lia-text-base" />
                  </button>
                  <button
                    onClick={(e) => openDeleteArchetypeDialog(arch, e)}
                    disabled={isDeletingArchetype === arch.id}
                    className="p-1 rounded-md hover:bg-status-error/10 transition-colors motion-reduce:transition-none"
                    title="Excluir arquétipo"
                  >
                    {isDeletingArchetype === arch.id ? (
                      <Loader2 className="w-3.5 h-3.5 lia-text-secondary animate-spin motion-reduce:animate-none" />
                    ) : (
                      <Trash2 className="w-3.5 h-3.5 lia-text-secondary hover:text-status-error" />
                    )}
                  </button>
                </div>

                <div className="flex items-start gap-2.5 pr-16">
                  <span className="text-lg flex-shrink-0">
                    {arch.emoji || "🎯"}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium lia-text-strong truncate">
                      {arch.name}
                    </div>
                    {arch.description && (
                      <p className="text-xs lia-text-secondary mt-0.5 line-clamp-2">
                        {arch.description}
                      </p>
                    )}
                    {arch.department && (
                      <Badge variant="outline" className="mt-1.5 text-micro">
                        {arch.department}
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
})
EAPTabArquetipos.displayName = 'EAPTabArquetipos'
