"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import type { NewIntegrationForm } from "./integrations-page.types"
import { AVAILABLE_EVENTS } from "./useIntegrationsPage"

interface NewIntegrationModalProps {
  newIntegration: NewIntegrationForm
  onChange: (form: NewIntegrationForm) => void
  onCreate: () => void
  onCancel: () => void
}

export function NewIntegrationModal({ newIntegration, onChange, onCreate, onCancel }: NewIntegrationModalProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-md max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-lia-text-primary mb-4">
            Nova Integração
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-lia-text-primary mb-2">
                Plataforma
              </label>
              <select
                value={newIntegration.type}
                onChange={(e) => onChange({...newIntegration, type: e.target.value as 'teams'})}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-lia-bg-primary dark:bg-lia-bg-elevated text-lia-text-primary"
              >
                <option value="teams">Microsoft Teams</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-lia-text-primary mb-2">
                Nome da Integração
              </label>
              <input
                type="text"
                value={newIntegration.name}
                onChange={(e) => onChange({...newIntegration, name: e.target.value})}
                placeholder="Ex: Canal #recrutamento"
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-lia-bg-primary dark:bg-lia-bg-elevated text-lia-text-primary"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-lia-text-primary mb-2">
                Webhook URL
              </label>
              <input
                type="url"
                value={newIntegration.webhookUrl}
                onChange={(e) => onChange({...newIntegration, webhookUrl: e.target.value})}
                placeholder="https://outlook.office.com/webhook/..."
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-lia-bg-primary dark:bg-lia-bg-elevated text-lia-text-primary"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-lia-text-primary mb-2">
                Eventos para Notificar
              </label>
              <div className="grid grid-cols-2 gap-2">
                {AVAILABLE_EVENTS.map((event) => (
                  <label key={event.id} className="flex items-center gap-2 p-2 border border-lia-border-subtle dark:border-lia-border-subtle rounded-md cursor-pointer hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse">
                    <input
                      type="checkbox"
                      checked={newIntegration.events.includes(event.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          onChange({
                            ...newIntegration,
                            events: [...newIntegration.events, event.id]
                          })
                        } else {
                          onChange({
                            ...newIntegration,
                            events: newIntegration.events.filter(ev => ev !== event.id)
                          })
                        }
                      }}
                      className="rounded-md border-lia-border-default"
                    />
                    <event.icon className="w-4 h-4 text-lia-text-secondary" />
                    <span className="text-sm text-lia-text-primary">{event.label}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          <div className="flex gap-3 mt-6">
            <Button
              onClick={onCreate}
              className="flex-1 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:hover:bg-lia-interactive-active"
            >
              Criar Integração
            </Button>
            <Button
              variant="outline"
              onClick={onCancel}
            >
              Cancelar
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
