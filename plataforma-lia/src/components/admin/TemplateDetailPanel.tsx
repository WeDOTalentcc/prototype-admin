"use client"

import React, { RefObject } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { VariableSelector } from "@/components/ui/variable-selector"
import { ThinkingDots } from "@/components/ui/thinking-dots"
import {
  Edit, Save, X, Brain, Check, AlertCircle,
  Wand2, Loader2, Settings
} from "lucide-react"
import {
  EmailTemplate,
  AIResultModal,
  TRIGGER_TYPE_LABELS,
  CHANNEL_LABELS,
} from "./AdminTemplateHub.types"

interface TemplateDetailPanelProps {
  selectedTemplate: EmailTemplate | null
  editingTemplate: EmailTemplate | null
  setEditingTemplate: (template: EmailTemplate | null) => void
  bodyTextareaRef: RefObject<HTMLTextAreaElement | null>
  saving: boolean
  aiPrompt: string
  setAiPrompt: (prompt: string) => void
  isGenerating: boolean
  aiResultModal: AIResultModal | null
  insertVariableAtCursor: (variable: string) => void
  handleSaveTemplate: () => void
  handleAdjustWithAI: () => void
  handleConfirmAIAdjustment: () => void
  handleCancelAIAdjustment: () => void
}

export function TemplateDetailPanel({
  selectedTemplate,
  editingTemplate,
  setEditingTemplate,
  bodyTextareaRef,
  saving,
  aiPrompt,
  setAiPrompt,
  isGenerating,
  aiResultModal,
  insertVariableAtCursor,
  handleSaveTemplate,
  handleAdjustWithAI,
  handleConfirmAIAdjustment,
  handleCancelAIAdjustment,
}: TemplateDetailPanelProps) {
  if (!selectedTemplate) {
    return (
      <Card className="border-dashed border-2 border-lia-border-subtle rounded-md h-96 flex items-center justify-center">
        <CardContent className="text-center">
          <div className="w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3 bg-lia-interactive-active/30">
            <Settings className="w-6 h-6 text-lia-text-secondary" />
          </div>
          <p className="text-sm text-lia-text-secondary mb-1">
            Selecione um template
          </p>
          <p className="text-xs text-lia-text-secondary">
            Clique em um template à esquerda para visualizar e editar
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-lia-text-primary">
          {editingTemplate ? 'Editando Template' : 'Visualização'}
        </h3>
        <div className="flex items-center gap-2">
          {editingTemplate ? (
            <>
              <Button variant="ghost" size="sm" onClick={() => setEditingTemplate(null)}>
                <X className="w-3.5 h-3.5" />
              </Button>
              <Button size="sm" className="py-1.5 px-2 text-xs bg-lia-btn-primary-bg text-lia-btn-primary-text" onClick={handleSaveTemplate}>
                <Save className="w-3.5 h-3.5 mr-1" />
                {saving ? 'Salvando...' : 'Salvar'}
              </Button>
            </>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setEditingTemplate({ ...selectedTemplate })}
              className="rounded-md py-1.5 px-2 text-xs border-lia-border-default"
            >
              <Edit className="w-3.5 h-3.5 mr-1" />
              Editar
            </Button>
          )}
        </div>
      </div>

      <Card className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-lia-bg-primary/80 dark:bg-lia-bg-secondary/80 rounded-md">
        <CardContent className="p-4 space-y-4">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge className={`${CHANNEL_LABELS[selectedTemplate.channel || 'email']?.color || ''}`}>
              {CHANNEL_LABELS[selectedTemplate.channel || 'email']?.label || selectedTemplate.channel}
            </Badge>
            <Badge variant="outline">{selectedTemplate.category}</Badge>
            {selectedTemplate.trigger_type && (
              <Badge className={`${TRIGGER_TYPE_LABELS[selectedTemplate.trigger_type]?.color || ''}`}>
                {TRIGGER_TYPE_LABELS[selectedTemplate.trigger_type]?.label}
              </Badge>
            )}
          </div>

          {selectedTemplate.subject && (
            <div>
              <label className="block text-xs font-medium text-lia-text-secondary mb-1">Assunto</label>
              {editingTemplate ? (
                <input
                  type="text"
                  value={editingTemplate.subject}
                  onChange={(e) => setEditingTemplate({ ...editingTemplate, subject: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:outline-none"
                />
              ) : (
                <p className="text-sm text-lia-text-primary bg-lia-bg-secondary rounded-md px-3 py-2">{selectedTemplate.subject}</p>
              )}
            </div>
          )}

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-medium text-lia-text-secondary">Conteúdo</label>
              {editingTemplate && (
                <VariableSelector
                  onSelect={insertVariableAtCursor}
                  disabled={!editingTemplate}
                />
              )}
            </div>
            {editingTemplate ? (
              <textarea
                ref={bodyTextareaRef}
                value={editingTemplate.body}
                onChange={(e) => setEditingTemplate({ ...editingTemplate, body: e.target.value })}
                rows={12}
                className="w-full px-3 py-2 text-sm border border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:outline-none font-mono"
              />
            ) : (
              <div className="bg-lia-bg-secondary rounded-md p-3">
                <pre className="text-sm text-lia-text-primary whitespace-pre-wrap font-sans">
                  {selectedTemplate.body}
                </pre>
              </div>
            )}
          </div>

          {selectedTemplate.variables && selectedTemplate.variables.length > 0 && (
            <div>
              <label className="block text-xs font-medium text-lia-text-secondary mb-2">Variáveis Disponíveis</label>
              <div className="flex flex-wrap gap-1.5">
                {selectedTemplate.variables.map((variable, idx) => (
                  <Badge key={idx} variant="outline" className="text-xs font-mono">
                    {`{{${variable}}}`}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {selectedTemplate.used_in && selectedTemplate.used_in.length > 0 && (
            <div>
              <label className="block text-xs font-medium text-lia-text-secondary mb-2">Usado em</label>
              <div className="flex flex-wrap gap-1.5">
                {selectedTemplate.used_in.map((usage, idx) => (
                  <Badge key={idx} variant="secondary" className="text-xs">
                    {usage}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {editingTemplate && (
        <Card className="rounded-md border border-lia-border-subtle bg-lia-bg-primary">
          <CardContent className="p-4 space-y-3">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-md flex items-center justify-center bg-lia-interactive-active/30">
                <Brain className="w-4 h-4 text-wedo-cyan" />
              </div>
              <div>
                <span className="text-base-ui font-semibold text-lia-text-primary">Ajustar com a LIA</span>
                <p className="text-xs text-lia-text-secondary">
                  Descreva as alterações desejadas
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={aiPrompt}
                onChange={(e) => setAiPrompt(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !isGenerating && aiPrompt.trim() && handleAdjustWithAI()}
                placeholder="Ex: Torne mais formal e adicione contexto técnico..."
                disabled={isGenerating}
                className="flex-1 px-3 py-2 text-xs border border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-lia-btn-primary-bg/20 focus:border-lia-border-medium focus:outline-none disabled:bg-lia-bg-secondary disabled:lia-text-secondary"
              />
              <Button
                onClick={handleAdjustWithAI}
                disabled={isGenerating || !aiPrompt.trim()}
                className="gap-1.5 rounded-md py-2 px-3 text-xs min-w-[100px]"
                style={{backgroundColor: isGenerating ? 'var(--wedo-cyan)' : 'var(--lia-text-secondary)', color: 'white'}}
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
                    Ajustando...
                  </>
                ) : (
                  <>
                    <Wand2 className="w-3.5 h-3.5" />
                    Ajustar
                  </>
                )}
              </Button>
            </div>
            {isGenerating && (
              <div className="flex items-center gap-2 p-2 rounded-md bg-wedo-cyan/[.08]">
                <div className="flex gap-1">
                  <ThinkingDots dotClassName="bg-lia-btn-primary-bg" size="md" />
                </div>
                <span className="text-xs" style={{color: 'var(--wedo-cyan-dark)'}}>
                  A LIA está analisando e ajustando o template...
                </span>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {aiResultModal?.show && (
        <div className="fixed inset-0 bg-lia-overlay flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-hidden rounded-md bg-lia-bg-primary">
            <div className="border-b border-lia-border-subtle p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-md flex items-center justify-center bg-lia-interactive-active/30">
                    <Brain className="w-5 h-5 text-wedo-cyan" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-lia-text-primary">
                      Ajustes da LIA
                    </h3>
                    <p className="text-xs text-lia-text-secondary">
                      Revise as alterações sugeridas
                    </p>
                  </div>
                </div>
                <Button variant="ghost" size="sm" onClick={handleCancelAIAdjustment} className="rounded-md">
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </div>
            <CardContent className="p-4 space-y-4 overflow-y-auto" style={{maxHeight: 'calc(90vh - 180px)'}}>
              <div>
                <label className="block text-xs font-medium text-lia-text-secondary uppercase tracking-wide mb-2">
                  Alterações Realizadas
                </label>
                <div className="flex flex-wrap gap-1.5">
                  {aiResultModal.changesMade.map((change, idx) => (
                    <Badge key={idx} className="text-xs px-2 py-0.5 rounded-full bg-lia-interactive-active/30 text-wedo-cyan-dark">
                      <Check className="w-3 h-3 mr-1" />
                      {change}
                    </Badge>
                  ))}
                </div>
              </div>

              {aiResultModal.newSubject && (
                <div>
                  <label className="block text-xs font-medium text-lia-text-secondary uppercase tracking-wide mb-2">
                    Novo Assunto
                  </label>
                  <div className="p-3 bg-lia-bg-secondary rounded-md text-xs text-lia-text-primary">
                    {aiResultModal.newSubject}
                  </div>
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-lia-text-secondary uppercase tracking-wide mb-2">
                  Novo Conteúdo
                </label>
                <div className="p-3 bg-lia-bg-secondary rounded-md text-xs text-lia-text-primary whitespace-pre-wrap max-h-content-md overflow-y-auto">
                  {aiResultModal.newBody}
                </div>
              </div>

              <div className="p-3 rounded-md border border-status-warning/30 bg-status-warning/10">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-status-warning mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-status-warning">
                    Ao aplicar os ajustes, o texto será atualizado no editor. Lembre-se de clicar em <strong>"Salvar"</strong> para confirmar as alterações definitivamente.
                  </p>
                </div>
              </div>
            </CardContent>
            <div className="border-t border-lia-border-subtle p-4 flex items-center justify-end gap-3">
              <Button variant="outline" onClick={handleCancelAIAdjustment} className="rounded-md px-4 py-2 text-xs">
                Cancelar
              </Button>
              <Button
                onClick={handleConfirmAIAdjustment}
                className="rounded-md px-4 py-2 text-xs gap-1.5 bg-lia-btn-primary-bg text-lia-btn-primary-text"
              >
                <Check className="w-3.5 h-3.5" />
                Aplicar Ajustes
              </Button>
            </div>
          </Card>
        </div>
      )}
    </>
  )
}
