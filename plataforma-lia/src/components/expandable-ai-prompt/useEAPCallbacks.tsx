"use client"

import { useArchetypeHandlers } from './useArchetypeHandlers'
import { useEAPSearchCallbacks } from './useEAPSearchCallbacks'
import { useEAPCommandCallbacks } from './useEAPCommandCallbacks'
import type { UseEAPCallbacksParams } from './useEAPCallbacksTypes'

export function useEAPCallbacks(params: UseEAPCallbacksParams) {
  const {
    parsedEntities,
    advancedFilters,
    naturalSearchValue,
    editingArchetype,
    editArchetypeName,
    editArchetypeQuery,
    editArchetypeDescription,
    editArchetypeEmoji,
    editArchetypeTags,
    archetypeToDelete,
    setArchetypes,
    setIsCreatingArchetype,
    setSelectedJobForArchetype,
    setIsCreatingFromSearch,
    setNewArchetypeDescription,
    setEditingArchetype,
    setEditArchetypeName,
    setEditArchetypeQuery,
    setEditArchetypeDescription,
    setEditArchetypeEmoji,
    setEditArchetypeTags,
    setNewTagInput,
    setIsSavingArchetype,
    setIsDeletingArchetype,
    setShowDeleteArchetypeDialog,
    setArchetypeToDelete,
  } = params

  const searchCallbacks = useEAPSearchCallbacks(params)
  const commandCallbacks = useEAPCommandCallbacks(params)

  const {
    hasParsedEntities,
    buildSearchSpec,
    generateArchetypeName,
    createArchetypeFromJob,
    createArchetypeFromActiveSearch,
    createArchetypeFromDescription,
    openEditArchetype,
    closeEditArchetype,
    saveArchetype,
    openDeleteArchetypeDialog,
    confirmDeleteArchetype,
  } = useArchetypeHandlers({
    parsedEntities,
    advancedFilters,
    naturalSearchValue,
    editingArchetype,
    editArchetypeName,
    editArchetypeQuery,
    editArchetypeDescription,
    editArchetypeEmoji,
    editArchetypeTags,
    archetypeToDelete,
    setArchetypes,
    setIsCreatingArchetype,
    setSelectedJobForArchetype,
    setIsCreatingFromSearch,
    setNewArchetypeDescription,
    setEditingArchetype,
    setEditArchetypeName,
    setEditArchetypeQuery,
    setEditArchetypeDescription,
    setEditArchetypeEmoji,
    setEditArchetypeTags,
    setNewTagInput,
    setIsSavingArchetype,
    setIsDeletingArchetype,
    setShowDeleteArchetypeDialog,
    setArchetypeToDelete,
  })

  return {
    ...searchCallbacks,
    ...commandCallbacks,
    hasParsedEntities,
    buildSearchSpec,
    generateArchetypeName,
    createArchetypeFromJob,
    createArchetypeFromActiveSearch,
    createArchetypeFromDescription,
    openEditArchetype,
    closeEditArchetype,
    saveArchetype,
    openDeleteArchetypeDialog,
    confirmDeleteArchetype,
  }
}
