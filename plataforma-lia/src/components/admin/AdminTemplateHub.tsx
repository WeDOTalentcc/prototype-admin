"use client"

import React from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  Mail, Brain, FileText, MessageSquare, Bell,
  CheckCircle, AlertCircle, Search, Filter,
} from "lucide-react"
import { ChannelFilter } from "./AdminTemplateHub.types"
import { useAdminTemplateHub } from "./useAdminTemplateHub"
import { TemplateListPanel } from "./TemplateListPanel"
import { TemplateDetailPanel } from "./TemplateDetailPanel"

export function AdminTemplateHub() {
  const {
    selectedTemplate,
    setSelectedTemplate,
    editingTemplate,
    setEditingTemplate,
    bodyTextareaRef,
    loading,
    saving,
    error,
    successMessage,
    aiPrompt,
    setAiPrompt,
    isGenerating,
    aiResultModal,
    channelFilter,
    triggerTypeFilter,
    setTriggerTypeFilter,
    searchQuery,
    setSearchQuery,
    expandedGroups,
    setExpandedGroups,
    filteredTemplates,
    groupedTemplates,
    insertVariableAtCursor,
    handleChannelFilterChange,
    handleSaveTemplate,
    handleAdjustWithAI,
    handleConfirmAIAdjustment,
    handleCancelAIAdjustment,
  } = useAdminTemplateHub()

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h2 className="text-xl font-semibold text-lia-text-primary">
          Templates de Sistema
        </h2>
        <p className="text-sm text-lia-text-disabled">
          Gerencie templates automáticos, alertas e notificações internas
        </p>
      </div>

      {successMessage && (
        <div className="px-3 py-2 rounded-md flex items-center gap-2 border border-wedo-cyan/30 text-wedo-cyan-dark bg-lia-interactive-active/30">
          <CheckCircle className="w-4 h-4 text-lia-text-secondary" />
          <span>{successMessage}</span>
        </div>
      )}
      {error && (
        <div className="bg-status-error/10 border border-status-error/30 text-status-error px-3 py-2 rounded-md flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}

      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary" />
            <Input
              placeholder="Buscar templates..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 text-sm h-9 rounded-md"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            {[
              { key: 'all', label: 'Todos', icon: null },
              { key: 'email', label: 'Email', icon: Mail },
              { key: 'bell', label: 'Bell', icon: Bell },
              { key: 'teams', label: 'Teams', icon: MessageSquare },
              { key: 'briefing', label: 'Briefing', icon: FileText },
              { key: 'parecer', label: 'Parecer', icon: Brain },
              { key: 'report', label: 'Report', icon: FileText }
            ].map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => handleChannelFilterChange(key as ChannelFilter)}
                className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors motion-reduce:transition-none ${
                  channelFilter === key
                    ? 'text-white'
                    : 'bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active dark:bg-lia-bg-elevated'
                }`}
                style={channelFilter === key ? { backgroundColor: 'var(--lia-btn-primary-bg)' } : {}}
              >
                {Icon && <Icon className="w-3.5 h-3.5" />}
                {label}
              </button>
            ))}
          </div>

          <div className="flex gap-2">
            <select
              value={triggerTypeFilter}
              onChange={(e) => setTriggerTypeFilter(e.target.value as 'all' | 'automatic' | 'manual' | 'both')}
              className="px-2.5 py-1.5 rounded-md text-xs font-medium border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-secondary"
            >
              <option value="all">Todos Tipos</option>
              <option value="automatic">Automático</option>
              <option value="manual">Manual</option>
              <option value="both">Ambos</option>
            </select>
          </div>
        </div>

        <div className="text-xs text-lia-text-secondary flex items-center gap-2">
          <Filter className="w-3.5 h-3.5" />
          {filteredTemplates.length} template{filteredTemplates.length !== 1 ? 's' : ''} encontrado{filteredTemplates.length !== 1 ? 's' : ''}
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="rounded-md animate-pulse motion-reduce:animate-none">
                <CardContent className="p-3">
                  <div className="flex items-start gap-2">
                    <div className="w-8 h-8 rounded-md bg-wedo-cyan/20"></div>
                    <div className="flex-1">
                      <div className="h-4 w-32 rounded-md mb-2 bg-wedo-cyan/20"></div>
                      <div className="h-3 w-24 rounded-md bg-wedo-cyan/15"></div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          <Card className="border-dashed border-2 border-lia-border-subtle rounded-md h-64 flex items-center justify-center animate-pulse motion-reduce:animate-none">
            <CardContent className="text-center">
              <div className="w-10 h-10 rounded-full mx-auto mb-3 bg-wedo-cyan/20"></div>
              <div className="h-4 w-40 rounded-md mx-auto bg-wedo-cyan/20"></div>
            </CardContent>
          </Card>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 min-h-[500px]">
          <div className="space-y-3 overflow-y-auto pr-2 pb-8" style={{maxHeight: 'calc(100vh - 320px)'}}>
            <TemplateListPanel
              filteredTemplates={filteredTemplates}
              groupedTemplates={groupedTemplates}
              selectedTemplate={selectedTemplate}
              expandedGroups={expandedGroups}
              setExpandedGroups={setExpandedGroups}
              onSelectTemplate={setSelectedTemplate}
            />
          </div>

          <div className="space-y-3 lg:sticky lg:top-0 overflow-y-auto pb-20" style={{maxHeight: 'calc(100vh - 260px)'}}>
            <TemplateDetailPanel
              selectedTemplate={selectedTemplate}
              editingTemplate={editingTemplate}
              setEditingTemplate={setEditingTemplate}
              bodyTextareaRef={bodyTextareaRef}
              saving={saving}
              aiPrompt={aiPrompt}
              setAiPrompt={setAiPrompt}
              isGenerating={isGenerating}
              aiResultModal={aiResultModal}
              insertVariableAtCursor={insertVariableAtCursor}
              handleSaveTemplate={handleSaveTemplate}
              handleAdjustWithAI={handleAdjustWithAI}
              handleConfirmAIAdjustment={handleConfirmAIAdjustment}
              handleCancelAIAdjustment={handleCancelAIAdjustment}
            />
          </div>
        </div>
      )}
    </div>
  )
}
