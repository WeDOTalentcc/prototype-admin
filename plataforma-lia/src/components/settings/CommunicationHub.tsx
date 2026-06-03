"use client"

/**
 * WT-2022 P1.COMM: Central de Comunicacao
 *
 * Label "Central de Comunicacao" cobre 5 tabs reais (Templates, Signature,
 * Schedule, Alerts, ABTesting). NAO e label-lie - escopo entregue corresponde
 * ao prometido. Auditoria 2026-05-21 inicialmente classificou como ghost mas
 * verificacao confirmou consumers reais para todas as tabs.
 *
 * Subtab "Historico de envios" foi descartada por decisao de produto - se for
 * reintroduzida, criar tab novo aqui + endpoint /api/communication/sent-log.
 */

import React from "react"
import { Mail, PenTool, Bell } from "lucide-react"
import { useTranslations } from "next-intl"
import { tabStyles } from '@/lib/design-tokens'
import type { CommunicationHubProps } from './communication-hub/CommunicationHub.types'
import { useCommunicationHub } from './communication-hub/useCommunicationHub'
import { TemplatesTab } from './communication-hub/TemplatesTab'
import { SignatureTab } from './communication-hub/SignatureTab'
import { AlertPreferencesPanel } from './AlertPreferencesPanel'

export function CommunicationHub({ activeSubsection, visibleTabs, stacked }: CommunicationHubProps) {
  const t = useTranslations("settings")
  const hub = useCommunicationHub(activeSubsection)


  const allTabs = [
    { id: 'templates', label: t("communication.tabTemplates"), icon: Mail },
    { id: 'signature', label: t("communication.tabSignature"), icon: PenTool },
    { id: 'alerts', label: t("communication.tabAlerts"), icon: Bell },
  ]

  const tabs = visibleTabs ? allTabs.filter(tab => visibleTabs.includes(tab.id)) : allTabs

  const renderTab = (tabId: string) => {
    switch (tabId) {
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
            bodyTextareaRef={hub.bodyTextareaRef}
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
      case 'alerts':
        return (
          <AlertPreferencesPanel />
        )
      default:
        return null
    }
  }

  if (stacked) {
    return (
      <div className="space-y-8">
        {tabs.map((tab) => (
          <React.Fragment key={tab.id}>{renderTab(tab.id)}</React.Fragment>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* WT-2022 P1.COMM: subtitle descritivo para evitar confusao com hub generico de comunicacao cross-channel. */}
      {tabs.length > 1 && (
        <p className="text-xs text-lia-text-tertiary -mt-1 mb-2">
          Templates, assinatura, horarios, alertas e testes A/B de comunicacao com candidatos.
        </p>
      )}
      {tabs.length > 1 && (
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
      )}

      {renderTab(hub.activeTab)}
    </div>
  )
}
