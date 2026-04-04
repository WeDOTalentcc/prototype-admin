"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Settings, Activity, Plus } from "lucide-react"
import { useIntegrationsPage } from "./useIntegrationsPage"
import { IntegrationsStatsCards } from "./IntegrationsStatsCards"
import { IntegrationsList } from "./IntegrationsList"
import { IntegrationsTemplates } from "./IntegrationsTemplates"
import { IntegrationsSidebar } from "./IntegrationsSidebar"
import { NewIntegrationModal } from "./NewIntegrationModal"

export function IntegrationsPage() {
  const {
    integrations,
    templates,
    webhookEvents,
    filteredEvents,
    showNewIntegration,
    setShowNewIntegration,
    showTemplateEditor,
    setShowTemplateEditor,
    selectedTemplate,
    setSelectedTemplate,
    selectedIntegration,
    setSelectedIntegration,
    showWebhookLogs,
    setShowWebhookLogs,
    filterStatus,
    setFilterStatus,
    testingIntegration,
    newIntegration,
    setNewIntegration,
    testIntegration,
    toggleIntegrationStatus,
    deleteIntegration,
    createIntegration,
  } = useIntegrationsPage()

  return (
    <div className="min-h-screen bg-lia-bg-primary dark:bg-lia-bg-primary p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-lia-text-primary mb-2 flex items-center gap-3 font-sans">
                <Settings className="w-8 h-8 text-lia-text-secondary" />
                Integrações Externas
              </h1>
              <p className="text-lia-text-secondary">
                Configure notificações automáticas para Slack, Teams e outras ferramentas
              </p>
            </div>
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => setShowWebhookLogs(!showWebhookLogs)}
                className="gap-2"
              >
                <Activity className="w-4 h-4" />
                Logs de Webhook
              </Button>
              <Button
                onClick={() => setShowNewIntegration(true)}
                className="gap-2 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:hover:bg-lia-interactive-active"
              >
                <Plus className="w-4 h-4" />
                Nova Integração
              </Button>
            </div>
          </div>
        </div>

        <IntegrationsStatsCards
          integrations={integrations}
          templates={templates}
          webhookEvents={webhookEvents}
        />

        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-8">
            <IntegrationsList
              integrations={integrations}
              testingIntegration={testingIntegration}
              onTest={testIntegration}
              onEdit={setSelectedIntegration}
              onToggleStatus={toggleIntegrationStatus}
              onDelete={deleteIntegration}
            />

            <IntegrationsTemplates
              templates={templates}
              onNewTemplate={() => {
                setSelectedTemplate(null)
                setShowTemplateEditor(true)
              }}
              onEditTemplate={(template) => {
                setSelectedTemplate(template)
                setShowTemplateEditor(true)
              }}
            />
          </div>

          <IntegrationsSidebar
            showWebhookLogs={showWebhookLogs}
            filteredEvents={filteredEvents}
            filterStatus={filterStatus}
            onFilterChange={setFilterStatus}
          />
        </div>

        {showNewIntegration && (
          <NewIntegrationModal
            newIntegration={newIntegration}
            onChange={setNewIntegration}
            onCreate={createIntegration}
            onCancel={() => setShowNewIntegration(false)}
          />
        )}
      </div>
    </div>
  )
}
