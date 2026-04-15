"use client"

import React, { useEffect } from "react"
import { Mail, PenTool } from "lucide-react"
import { useTranslations } from "next-intl"
import { tabStyles } from '@/lib/design-tokens'
import { useCommunicationHub } from './communication-hub/useCommunicationHub'
import { TemplatesTab } from './communication-hub/TemplatesTab'
import { SignatureTab } from './communication-hub/SignatureTab'

export function TemplatesAssinaturaHub() {
  const t = useTranslations("settings")
  const hub = useCommunicationHub()

  useEffect(() => {
    hub.fetchData()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const tabs = [
    { id: 'templates', label: t("communication.tabTemplates"), icon: Mail },
    { id: 'signature', label: t("communication.tabSignature"), icon: PenTool },
  ]

  const renderContent = () => {
    switch (hub.activeTab) {
      case 'templates':
        return (
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
            bodyTextareaRef={hub.bodyTextareaRef as any}
            isGenerating={hub.isGenerating}
            handleChannelFilterChange={hub.handleChannelFilterChange}
            insertVariableAtCursor={hub.insertVariableAtCursor}
            handleAdjustWithAI={hub.handleAdjustWithAI}
            handleConfirmAIAdjustment={hub.handleConfirmAIAdjustment}
            handleCancelAIAdjustment={hub.handleCancelAIAdjustment}
            handleSaveTemplate={hub.handleSaveTemplate}
          />
        )
      case 'signature':
        return (
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
        )
      default:
        return null
    }
  }

  return (
    <div className="space-y-4">
      <div className={tabStyles.pillContainer}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => hub.setActiveTab(tab.id)}
            className={hub.activeTab === tab.id ? tabStyles.pillActive : tabStyles.pill}
          >
            <tab.icon className={tabStyles.pillIcon} />
            {tab.label}
          </button>
        ))}
      </div>

      {renderContent()}
    </div>
  )
}

export default TemplatesAssinaturaHub
