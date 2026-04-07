"use client"

import { SearchModeArchetypes } from "./SearchModeArchetypes"
import { SSISimilarMode } from "./SSISimilarMode"
import { SSIModeNatural } from "./ssi-modes/SSIModeNatural"
import { SSIModeJobDescription } from "./ssi-modes/SSIModeJobDescription"
import { SSIModeBoolean } from "./ssi-modes/SSIModeBoolean"
import type { useSmartSearchCore } from "./hooks/useSmartSearchCore"


type SSIModeContentProps = ReturnType<typeof useSmartSearchCore>

export function SSIModeContent(props: SSIModeContentProps) {
  const {
    addSimilarUrl, analyzeProfiles, archetypeCreateMode, archetypeDescription, archetypeSearch, archetypeSearchPrompt, archetypeTab, archetypeVacancies,
    autocompleteEnabled, autocompleteItems, booleanError, buildArchetypePrompt, canSubmit, clearSelectedVacancy, combinedSuggestions,
    createArchetypeFromDescription, cvFileInputRef, deleteArchetype, expandedArchetypeId, fileInputRef, filteredArchetypes, formatDate, getPlaceholder,
    ghostOverlayRef, ghostTextInfo, ghostTextSuffix, handleAcceptEnhancement, handleAutocompleteSelect, handleCvUpload, handleDismissEnhancement, handleFileUpload,
    handleKeyDown, handleSelectVacancy, handleSourceChange, handleSubmit, hasMultipleSources, isAnalyzingProfiles, isCreatingArchetype, isDeletingArchetype,
    isLoading, isLoadingArchetypes, isParsingEntities, isSearchingJobs, isSearchingVacancies, jdContent, jdSearchPrompt, jdVacancyResults,
    jdVacancySearch, jobSearchQuery, jobSearchResults, mode, onChange, onRequireEmailsChange, onRequirePhoneNumbersChange, onSearchSourceChange,
    onSubmit, openArchetypeFromJob, openEditArchetype, removeCvFile, removeSimilarUrl, removeSuggestion, requireEmails,
    requirePhoneNumbers, searchAnalysis, searchJobsForArchetype, searchSource, selectedArchetype, selectedAutocompleteIndex, selectedVacancy, setArchetypeCreateMode,
    setArchetypeDescription, setArchetypeSearch, setArchetypeSearchPrompt, setArchetypeTab, setAutocompleteEnabled, setAutocompleteItems, setExpandedArchetypeId, setJdContent,
    setJdSearchPrompt, setJdVacancySearch, setJobSearchQuery, setSelectedArchetype, setSelectedAutocompleteIndex, setSelectedVacancy, setShowAutocomplete, setSimilarSearchPrompt,
    showAutocomplete, showCombinedSuggestions, showGlobalSearchOptions, showVacancyResults, similarCvFiles, similarSearchPrompt, similarUrls, tags,
    textareaRef, updateSimilarUrl, value
  } = props

  return (
    <>
      {/* Natural search mode */}
      {mode === "natural" && (
        <SSIModeNatural
          value={value}
          onChange={onChange}
          handleKeyDown={handleKeyDown}
          handleSubmit={handleSubmit}
          canSubmit={canSubmit}
          isLoading={isLoading}
          getPlaceholder={getPlaceholder}
          textareaRef={textareaRef}
          ghostOverlayRef={ghostOverlayRef}
          ghostTextInfo={ghostTextInfo}
          ghostTextSuffix={ghostTextSuffix}
          handleAcceptEnhancement={handleAcceptEnhancement}
          handleDismissEnhancement={handleDismissEnhancement}
          showAutocomplete={showAutocomplete}
          setShowAutocomplete={setShowAutocomplete}
          autocompleteItems={autocompleteItems}
          setAutocompleteItems={setAutocompleteItems}
          autocompleteEnabled={autocompleteEnabled}
          setAutocompleteEnabled={setAutocompleteEnabled}
          selectedAutocompleteIndex={selectedAutocompleteIndex}
          setSelectedAutocompleteIndex={setSelectedAutocompleteIndex}
          handleAutocompleteSelect={handleAutocompleteSelect}
          tags={tags}
          isParsingEntities={isParsingEntities}
          searchAnalysis={searchAnalysis}
          searchSource={searchSource}
          onSearchSourceChange={onSearchSourceChange}
          handleSourceChange={handleSourceChange}
          showGlobalSearchOptions={showGlobalSearchOptions}
          requireEmails={requireEmails}
          onRequireEmailsChange={onRequireEmailsChange}
          requirePhoneNumbers={requirePhoneNumbers}
          onRequirePhoneNumbersChange={onRequirePhoneNumbersChange}
        />
      )}

      {/* Similar profile mode - Combined Profile Feature */}
      {mode === "similar" && (
        <SSISimilarMode
          similarUrls={similarUrls} updateSimilarUrl={updateSimilarUrl} handleKeyDown={handleKeyDown}
          removeSimilarUrl={removeSimilarUrl} addSimilarUrl={addSimilarUrl} cvFileInputRef={cvFileInputRef}
          handleCvUpload={handleCvUpload} similarCvFiles={similarCvFiles} removeCvFile={removeCvFile}
          isLoading={isLoading || false} hasMultipleSources={hasMultipleSources}
          showCombinedSuggestions={showCombinedSuggestions} analyzeProfiles={analyzeProfiles}
          isAnalyzingProfiles={isAnalyzingProfiles || false} combinedSuggestions={combinedSuggestions}
          removeSuggestion={removeSuggestion} similarSearchPrompt={similarSearchPrompt}
          setSimilarSearchPrompt={setSimilarSearchPrompt} onSearchSourceChange={onSearchSourceChange as any}
          searchSource={searchSource || "local"} handleSourceChange={handleSourceChange as any}
          showGlobalSearchOptions={showGlobalSearchOptions} onRequireEmailsChange={onRequireEmailsChange}
          onRequirePhoneNumbersChange={onRequirePhoneNumbersChange} requireEmails={requireEmails || false}
          requirePhoneNumbers={requirePhoneNumbers || false} handleSubmit={handleSubmit}
          canSubmit={canSubmit}
        />
      )}

      {/* Job Description mode */}
      {mode === "jd" && (
        <SSIModeJobDescription
          jdContent={jdContent}
          setJdContent={setJdContent}
          jdVacancySearch={jdVacancySearch}
          setJdVacancySearch={setJdVacancySearch}
          jdVacancyResults={jdVacancyResults}
          showVacancyResults={showVacancyResults}
          isSearchingVacancies={isSearchingVacancies}
          selectedVacancy={selectedVacancy}
          setSelectedVacancy={setSelectedVacancy}
          clearSelectedVacancy={clearSelectedVacancy}
          handleSelectVacancy={handleSelectVacancy}
          formatDate={formatDate}
          jdSearchPrompt={jdSearchPrompt}
          setJdSearchPrompt={setJdSearchPrompt}
          fileInputRef={fileInputRef}
          handleFileUpload={handleFileUpload}
          handleSubmit={handleSubmit}
          canSubmit={canSubmit}
          isLoading={isLoading}
          getPlaceholder={getPlaceholder}
          searchSource={searchSource}
          onSearchSourceChange={onSearchSourceChange}
          handleSourceChange={handleSourceChange}
          showGlobalSearchOptions={showGlobalSearchOptions}
          requireEmails={requireEmails}
          onRequireEmailsChange={onRequireEmailsChange}
          requirePhoneNumbers={requirePhoneNumbers}
          onRequirePhoneNumbersChange={onRequirePhoneNumbersChange}
        />
      )}

      {/* Boolean mode */}
      {mode === "boolean" && (
        <SSIModeBoolean
          value={value}
          onChange={onChange}
          handleKeyDown={handleKeyDown}
          handleSubmit={handleSubmit}
          canSubmit={canSubmit}
          isLoading={isLoading}
          getPlaceholder={getPlaceholder}
          textareaRef={textareaRef}
          booleanError={booleanError}
          searchSource={searchSource}
          onSearchSourceChange={onSearchSourceChange}
          handleSourceChange={handleSourceChange}
          showGlobalSearchOptions={showGlobalSearchOptions}
          requireEmails={requireEmails}
          onRequireEmailsChange={onRequireEmailsChange}
          requirePhoneNumbers={requirePhoneNumbers}
          onRequirePhoneNumbersChange={onRequirePhoneNumbersChange}
        />
      )}

      {/* Archetypes mode */}
      {mode === "archetypes" && (
        <SearchModeArchetypes
          archetypeTab={archetypeTab}
          onArchetypeTabChange={setArchetypeTab}
          archetypeSearch={archetypeSearch}
          onArchetypeSearchChange={setArchetypeSearch}
          isLoadingArchetypes={isLoadingArchetypes}
          filteredArchetypes={filteredArchetypes}
          archetypeVacancies={archetypeVacancies}
          selectedArchetype={selectedArchetype}
          onSelectArchetype={setSelectedArchetype}
          expandedArchetypeId={expandedArchetypeId}
          onExpandedArchetypeIdChange={setExpandedArchetypeId}
          isDeletingArchetype={isDeletingArchetype}
          archetypeSearchPrompt={archetypeSearchPrompt}
          onArchetypeSearchPromptChange={setArchetypeSearchPrompt}
          onOpenEditArchetype={openEditArchetype as any}
          onDeleteArchetype={deleteArchetype}
          buildArchetypePrompt={buildArchetypePrompt as any}
          onSubmit={handleSubmit}
          isLoading={isLoading}
          searchSource={searchSource}
          onSearchSourceChange={onSearchSourceChange}
          onHandleSourceChange={handleSourceChange}
          showGlobalSearchOptions={showGlobalSearchOptions}
          requireEmails={requireEmails}
          onRequireEmailsChange={onRequireEmailsChange}
          requirePhoneNumbers={requirePhoneNumbers}
          onRequirePhoneNumbersChange={onRequirePhoneNumbersChange}
          archetypeCreateMode={archetypeCreateMode}
          onArchetypeCreateModeChange={setArchetypeCreateMode}
          jobSearchQuery={jobSearchQuery}
          onJobSearchQueryChange={setJobSearchQuery}
          isSearchingJobs={isSearchingJobs}
          jobSearchResults={jobSearchResults as any}
          onOpenArchetypeFromJob={openArchetypeFromJob}
          archetypeDescription={archetypeDescription}
          onArchetypeDescriptionChange={setArchetypeDescription}
          isCreatingArchetype={isCreatingArchetype}
          onCreateArchetypeFromDescription={createArchetypeFromDescription}
          onSearchJobsForArchetype={searchJobsForArchetype}
        />
      )}
    </>
  )
}
