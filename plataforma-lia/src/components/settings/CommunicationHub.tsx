"use client"

import React, { useEffect } from "react"
import { Mail, Clock, PenTool, Bell } from "lucide-react"
import { tabStyles } from '@/lib/design-tokens'
import type { CommunicationHubProps } from './communication-hub/CommunicationHub.types'
import { useCommunicationHub } from './communication-hub/useCommunicationHub'
import { TemplatesTab } from './communication-hub/TemplatesTab'
import { SignatureTab } from './communication-hub/SignatureTab'
import { ScheduleTab } from './communication-hub/ScheduleTab'
import { AlertsTab } from './communication-hub/AlertsTab'

export function CommunicationHub({ activeSubsection }: CommunicationHubProps) {
  const hub = useCommunicationHub(activeSubsection)

  useEffect(() => {
    hub.fetchData()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const tabs = [
    { id: 'templates', label: 'Templates', icon: Mail },
    { id: 'signature', label: 'Assinatura', icon: PenTool },
    { id: 'schedule', label: 'Horários LGPD', icon: Clock },
    { id: 'alerts', label: 'Alertas', icon: Bell }
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
      case 'schedule':
        return (
          <ScheduleTab
            successMessage={hub.successMessage}
            error={hub.error}
            sendingHours={hub.sendingHours}
            setSendingHours={hub.setSendingHours}
            respectHolidays={hub.respectHolidays}
            setRespectHolidays={hub.setRespectHolidays}
            respectWeekends={hub.respectWeekends}
            setRespectWeekends={hub.setRespectWeekends}
            maxMessagesPerDay={hub.maxMessagesPerDay}
            setMaxMessagesPerDay={hub.setMaxMessagesPerDay}
            isEditingSchedule={hub.isEditingSchedule}
            setIsEditingSchedule={hub.setIsEditingSchedule}
            savingSettings={hub.savingSettings}
            saveCommunicationSettings={hub.saveCommunicationSettings}
          />
        )
      case 'alerts':
        return (
          <AlertsTab
            successMessage={hub.successMessage}
            error={hub.error}
            alerts={hub.alerts}
            briefingFrequency={hub.briefingFrequency}
            setBriefingFrequency={hub.setBriefingFrequency}
            isEditingAlerts={hub.isEditingAlerts}
            setIsEditingAlerts={hub.setIsEditingAlerts}
            savingAlerts={hub.savingAlerts}
            saveAlertsConfig={hub.saveAlertsConfig}
            handleToggleAlert={hub.handleToggleAlert}
            handleChangeChannel={hub.handleChangeChannel}
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
