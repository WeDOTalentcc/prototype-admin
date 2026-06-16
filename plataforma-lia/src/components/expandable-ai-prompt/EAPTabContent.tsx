"use client"

import { AdvancedFiltersModal, type SearchFilters } from "@/components/search/advanced-filters-modal"
import { useExpandableAIPromptCore } from "./useExpandableAIPromptCore"
import {
  EAPTabNatural,
  EAPTabSimilar,
  EAPTabJobDescription,
  EAPTabBoolean,
  EAPTabFiltros,
  EAPTabArquetipos,
} from "./tabs"

type EAPTabContentProps = Pick<
  ReturnType<typeof useExpandableAIPromptCore>,
  'activeSearchTab' | 'naturalSearchValue' | 'setNaturalSearchValue' | 'searchTags' |
  'suggestions' | 'advancedFilters' | 'setAdvancedFilters' | 'analyzeProfiles' |
  'archetypeSearchFilter' | 'archetypes' | 'autocompleteEnabled' | 'autocompleteSuggestions' |
  'booleanSearchValue' | 'canSaveAsArchetype' | 'combinedSuggestions' |
  'createArchetypeFromActiveSearch' | 'createArchetypeFromDescription' |
  'cvFileInputRef' | 'executeSearchWithCriteria' | 'extractionTimeoutRef' |
  'fetchAutocomplete' | 'filteredArchetypes' | 'getTagColors' |
  'handleAcceptEnhancement' | 'handleAutocompleteKeyDown' | 'handleCvUpload' |
  'handleDismissEnhancement' | 'handlePremiumAutocompleteSelect' | 'handleSourceChange' |
  'hasMultipleSources' | 'hasParsedEntities' | 'isAnalyzingProfiles' |
  'isCreatingArchetype' | 'isCreatingFromSearch' | 'isDeletingArchetype' |
  'isEnhancingPrompt' | 'isParsingEntities' | 'jobDescriptionText' |
  'newArchetypeDescription' | 'onClose' | 'onCommand' |
  'openDeleteArchetypeDialog' | 'openEditArchetype' | 'parseEntitiesFromQuery' |
  'parsedEntities' | 'promptEnhancement' | 'removeCvFile' | 'removeSimilarUrl' |
  'removeSuggestion' | 'requireEmails' | 'requirePhoneNumbers' | 'searchAnalysis' |
  'searchSource' | 'selectedAutocompleteIndex' | 'setArchetypeSearchFilter' |
  'setAutocompleteEnabled' | 'setBooleanSearchValue' | 'setJobDescriptionText' |
  'setNewArchetypeDescription' | 'setRequireEmails' | 'setRequirePhoneNumbers' |
  'setSearchSource' | 'setSelectedArquetipo' | 'setShowAdvancedFiltersModal' |
  'setShowAutocomplete' | 'setShowPremiumAutocomplete' | 'setShowSaveArchetypeModal' |
  'showAutocomplete' | 'showCombinedSuggestions' | 'showGlobalSearchOptions' |
  'showPremiumAutocomplete' | 'similarCvFiles' | 'similarUrls' | 'updateSimilarUrl' |
  'addSimilarUrl'
>

export function EAPTabContent(props: EAPTabContentProps) {
  const { activeSearchTab } = props

  return (
    <>
      {activeSearchTab === 'natural' && (
        <EAPTabNatural
          naturalSearchValue={props.naturalSearchValue}
          setNaturalSearchValue={props.setNaturalSearchValue}
          searchTags={props.searchTags}
          advancedFilters={props.advancedFilters}
          autocompleteEnabled={props.autocompleteEnabled}
          autocompleteSuggestions={props.autocompleteSuggestions}
          canSaveAsArchetype={props.canSaveAsArchetype}
          executeSearchWithCriteria={props.executeSearchWithCriteria}
          extractionTimeoutRef={props.extractionTimeoutRef}
          fetchAutocomplete={props.fetchAutocomplete}
          getTagColors={props.getTagColors}
          handleAcceptEnhancement={props.handleAcceptEnhancement}
          handleAutocompleteKeyDown={props.handleAutocompleteKeyDown}
          handleDismissEnhancement={props.handleDismissEnhancement}
          handlePremiumAutocompleteSelect={props.handlePremiumAutocompleteSelect}
          handleSourceChange={props.handleSourceChange}
          isEnhancingPrompt={props.isEnhancingPrompt}
          isParsingEntities={props.isParsingEntities}
          parseEntitiesFromQuery={props.parseEntitiesFromQuery}
          promptEnhancement={props.promptEnhancement}
          requireEmails={props.requireEmails}
          requirePhoneNumbers={props.requirePhoneNumbers}
          searchAnalysis={props.searchAnalysis}
          searchSource={props.searchSource}
          selectedAutocompleteIndex={props.selectedAutocompleteIndex}
          setAutocompleteEnabled={props.setAutocompleteEnabled}
          setRequireEmails={props.setRequireEmails}
          setRequirePhoneNumbers={props.setRequirePhoneNumbers}
          setSearchSource={props.setSearchSource}
          setShowPremiumAutocomplete={props.setShowPremiumAutocomplete}
          setShowSaveArchetypeModal={props.setShowSaveArchetypeModal}
          setShowAutocomplete={props.setShowAutocomplete}
          showAutocomplete={props.showAutocomplete}
          showGlobalSearchOptions={props.showGlobalSearchOptions}
          showPremiumAutocomplete={props.showPremiumAutocomplete}
        />
      )}

      {activeSearchTab === 'similar' && (
        <EAPTabSimilar
          similarUrls={props.similarUrls}
          similarCvFiles={props.similarCvFiles}
          combinedSuggestions={props.combinedSuggestions}
          showCombinedSuggestions={props.showCombinedSuggestions}
          isAnalyzingProfiles={props.isAnalyzingProfiles}
          analyzeProfiles={props.analyzeProfiles}
          hasMultipleSources={props.hasMultipleSources}
          updateSimilarUrl={props.updateSimilarUrl}
          removeSimilarUrl={props.removeSimilarUrl}
          addSimilarUrl={props.addSimilarUrl}
          cvFileInputRef={props.cvFileInputRef}
          handleCvUpload={props.handleCvUpload}
          removeCvFile={props.removeCvFile}
          removeSuggestion={props.removeSuggestion}
          onCommand={props.onCommand}
        />
      )}

      {activeSearchTab === 'job-description' && (
        <EAPTabJobDescription
          jobDescriptionText={props.jobDescriptionText}
          setJobDescriptionText={props.setJobDescriptionText}
          onCommand={props.onCommand}
        />
      )}

      {activeSearchTab === 'boolean' && (
        <EAPTabBoolean
          booleanSearchValue={props.booleanSearchValue}
          setBooleanSearchValue={props.setBooleanSearchValue}
          searchSource={props.searchSource}
          setSearchSource={props.setSearchSource}
          showGlobalSearchOptions={props.showGlobalSearchOptions}
          handleSourceChange={props.handleSourceChange}
          requireEmails={props.requireEmails}
          setRequireEmails={props.setRequireEmails}
          requirePhoneNumbers={props.requirePhoneNumbers}
          setRequirePhoneNumbers={props.setRequirePhoneNumbers}
          onCommand={props.onCommand}
        />
      )}

      {activeSearchTab === 'filtros' && (
        <EAPTabFiltros
          advancedFilters={props.advancedFilters}
          setAdvancedFilters={props.setAdvancedFilters}
          setShowAdvancedFiltersModal={props.setShowAdvancedFiltersModal}
          onCommand={props.onCommand}
        />
      )}

      {activeSearchTab === 'arquetipos' && (
        <EAPTabArquetipos
          naturalSearchValue={props.naturalSearchValue}
          parsedEntities={props.parsedEntities}
          hasParsedEntities={props.hasParsedEntities}
          newArchetypeDescription={props.newArchetypeDescription}
          setNewArchetypeDescription={props.setNewArchetypeDescription}
          createArchetypeFromActiveSearch={props.createArchetypeFromActiveSearch}
          createArchetypeFromDescription={props.createArchetypeFromDescription}
          isCreatingArchetype={props.isCreatingArchetype}
          isCreatingFromSearch={props.isCreatingFromSearch}
          isDeletingArchetype={props.isDeletingArchetype}
          archetypes={props.archetypes}
          filteredArchetypes={props.filteredArchetypes}
          archetypeSearchFilter={props.archetypeSearchFilter}
          setArchetypeSearchFilter={props.setArchetypeSearchFilter}
          openEditArchetype={props.openEditArchetype}
          openDeleteArchetypeDialog={props.openDeleteArchetypeDialog}
          setSelectedArquetipo={props.setSelectedArquetipo}
          onCommand={props.onCommand}
        />
      )}
    </>
  )
}
