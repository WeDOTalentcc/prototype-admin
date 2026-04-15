"use client"

import React, { useEffect } from "react"
import { useCommunicationHub } from './communication-hub/useCommunicationHub'
import { TemplatesTab } from './communication-hub/TemplatesTab'
import { SignatureTab } from './communication-hub/SignatureTab'

export function TemplatesAssinaturaHub() {
  const hub = useCommunicationHub()

  useEffect(() => {
    hub.fetchData()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="space-y-8">
      <TemplatesTab
        successMessage={hub.successMessage}
        error={hub.error}
        loading={hub.loading}
        channelFilter={hub.channelFilter}
        triggerTypeFilter={hub.triggerTypeFilter}
        setTriggerTypeFilter={hub.setTriggerTypeFilter}
        searchQuery={hub.searchQuery}
        setSearchQuery={hub.setSearchQuery}
        expandedGroups={hub.expandedGroups}
        setExpandedGroups={hub.setExpandedGroups}
        filteredTemplates={hub.filteredTemplates}
        groupedTemplates={hub.groupedTemplates}
        selectedTemplate={hub.selectedTemplate}
        setSelectedTemplate={hub.setSelectedTemplate}
        editingTemplate={hub.editingTemplate}
        setEditingTemplate={hub.setEditingTemplate}
        aiPrompt={hub.aiPrompt}
        setAiPrompt={hub.setAiPrompt}
        aiResultModal={hub.aiResultModal}
        bodyTextareaRef={hub.bodyTextareaRef as React.RefObject<HTMLTextAreaElement>}
        isGenerating={hub.isGenerating}
        handleChannelFilterChange={hub.handleChannelFilterChange}
        insertVariableAtCursor={hub.insertVariableAtCursor}
        handleAdjustWithAI={hub.handleAdjustWithAI}
        handleConfirmAIAdjustment={hub.handleConfirmAIAdjustment}
        handleCancelAIAdjustment={hub.handleCancelAIAdjustment}
        handleSaveTemplate={hub.handleSaveTemplate}
      />

      <SignatureTab
        successMessage={hub.successMessage}
        error={hub.error}
        signature={hub.signature}
        setSignature={hub.setSignature}
        isEditingSignature={hub.isEditingSignature}
        setIsEditingSignature={hub.setIsEditingSignature}
        savingSettings={hub.savingSettings}
        saveCommunicationSettings={hub.saveCommunicationSettings}
      />
    </div>
  )
}

export default TemplatesAssinaturaHub
