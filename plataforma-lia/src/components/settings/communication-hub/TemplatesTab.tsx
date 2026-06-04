import React from"react"
import { useTranslations } from "next-intl"
import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Input } from"@/components/ui/input"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from"@/components/ui/accordion"
import { VariableSelector } from"@/components/ui/variable-selector"
import {
  Mail, Edit, Save, X, Brain, Check, AlertCircle, MessageSquare,
  Wand2, Loader2, CheckCircle, Search, Filter, Bell
} from"lucide-react"
import { textStyles } from '@/lib/design-tokens'
import type { EmailTemplate, AiResultModal } from './CommunicationHub.types'
import { TEMPLATE_GROUPS, TRIGGER_TYPE_LABELS, PRIORITY_COLORS, CATEGORY_LABELS } from './CommunicationHub.constants'
import { stripHtmlTags } from './CommunicationHub.utils'
import { ThinkingDots } from"@/components/ui/thinking-dots"

interface TemplatesTabProps {
  successMessage: string | null
  error: string | null
  loading: boolean
  channelFilter: 'all' | 'email' | 'whatsapp'
  triggerTypeFilter: 'all' | 'automatic' | 'manual' | 'both'
  setTriggerTypeFilter: (v: 'all' | 'automatic' | 'manual' | 'both') => void
  searchQuery: string
  setSearchQuery: (v: string) => void
  expandedGroups: string[]
  setExpandedGroups: (v: string[]) => void
  filteredTemplates: EmailTemplate[]
  groupedTemplates: Record<string, EmailTemplate[]>
  selectedTemplate: EmailTemplate | null
  setSelectedTemplate: (t: EmailTemplate | null) => void
  editingTemplate: EmailTemplate | null
  setEditingTemplate: (t: EmailTemplate | null | ((prev: EmailTemplate | null) => EmailTemplate | null)) => void
  aiPrompt: string
  setAiPrompt: (v: string) => void
  aiResultModal: AiResultModal | null
  bodyTextareaRef: React.RefObject<HTMLTextAreaElement | null>
  isGenerating: boolean
  handleChannelFilterChange: (channel: 'all' | 'email' | 'whatsapp') => void
  insertVariableAtCursor: (variable: string) => void
  handleAdjustWithAI: () => Promise<void>
  handleConfirmAIAdjustment: () => void
  handleCancelAIAdjustment: () => void
  handleSaveTemplate: () => Promise<void>
}

export function TemplatesTab({
  successMessage, error, loading,
  channelFilter, triggerTypeFilter, setTriggerTypeFilter,
  searchQuery, setSearchQuery,
  expandedGroups, setExpandedGroups,
  filteredTemplates, groupedTemplates,
  selectedTemplate, setSelectedTemplate,
  editingTemplate, setEditingTemplate,
  aiPrompt, setAiPrompt, aiResultModal,
  bodyTextareaRef, isGenerating,
  handleChannelFilterChange, insertVariableAtCursor,
  handleAdjustWithAI, handleConfirmAIAdjustment, handleCancelAIAdjustment,
  handleSaveTemplate,
}: TemplatesTabProps) {
  const t = useTranslations("settings.communication.templates")
  const categoryLabels = CATEGORY_LABELS

  return (
    <div className="space-y-4">
      {successMessage && (
        <div className="px-2 py-1.5 rounded-full flex items-center gap-2 bg-status-success/10 border border-status-success/30 text-status-success dark:bg-status-success/20 dark:border-status-success/30 dark:text-status-success">
          <CheckCircle className="w-4 h-4" />
          <span>{successMessage}</span>
        </div>
      )}
      {error && (
        <div className="bg-status-error/10 border border-status-error/30 text-status-error px-2 py-1.5 rounded-full flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className={textStyles.h2}>{t("title")}</h3>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-tertiary" />
            <Input
              placeholder={t("searchPlaceholder")}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 text-xs h-9 rounded-md"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            {([
              { key: 'all', label: t('all'), icon: null },
              { key: 'email', label: t('filterEmail'), icon: Mail },
              { key: 'whatsapp', label: t('filterWhatsapp'), icon: MessageSquare }
            ] as const).map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => handleChannelFilterChange(key)}
                className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-full text-xs font-medium transition-colors motion-reduce:transition-none ${
                  channelFilter === key
                    ? 'bg-lia-bg-secondary text-lia-text-primary border border-lia-border-default'
                    : 'bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active dark:bg-lia-bg-elevated'
                }`}
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
              className="px-2.5 py-1.5 rounded-full text-xs font-medium border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary"
            >
              <option value="all">{t("allTypes")}</option>
              <option value="automatic">{t("automatic")}</option>
              <option value="manual">{t("manual")}</option>
              <option value="both">{t("both")}</option>
            </select>
          </div>
        </div>

        <div className="text-xs text-lia-text-secondary flex items-center gap-2">
          <Filter className="w-3.5 h-3.5" />
          {t("templatesFoundCount", { count: filteredTemplates.length })}
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          <div className="space-y-3">
            <div className="h-5 w-32 rounded-xl animate-pulse motion-reduce:animate-none bg-lia-interactive-active dark:bg-lia-bg-elevated"></div>
            {[1, 2, 3].map((i) => (
              <Card key={i} className="rounded-md animate-pulse motion-reduce:animate-none backdrop-blur-sm">
                <CardContent className="p-3">
                  <div className="flex items-start gap-2">
                    <div className="w-8 h-8 rounded-xl bg-lia-interactive-active dark:bg-lia-bg-elevated"></div>
                    <div className="flex-1">
                      <div className="h-4 w-32 rounded-xl mb-2 bg-lia-interactive-active dark:bg-lia-bg-elevated"></div>
                      <div className="h-3 w-24 rounded-xl bg-lia-interactive-active dark:bg-lia-bg-elevated"></div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          <Card className="border-dashed border-2 border-lia-border-subtle dark:border-lia-border-subtle rounded-xl h-64 flex items-center justify-center animate-pulse motion-reduce:animate-none backdrop-blur-sm">
            <CardContent className="text-center">
              <div className="w-10 h-10 rounded-full mx-auto mb-3 bg-lia-interactive-active dark:bg-lia-bg-elevated"></div>
              <div className="h-4 w-40 rounded-md mx-auto bg-lia-interactive-active dark:bg-lia-bg-elevated"></div>
            </CardContent>
          </Card>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 h-[calc(100vh-280px)] min-h-content-lg">
          <div className="space-y-3 overflow-y-auto pr-2 pb-8 max-h-[calc(100vh-280px)]">
            {filteredTemplates.length === 0 ? (
              <Card className="border border-dashed border-lia-border-subtle dark:border-lia-border-subtle rounded-xl">
                <CardContent className="p-4 text-center">
                  <div className="w-10 h-10 rounded-full flex items-center justify-center mx-auto mb-2 bg-lia-bg-tertiary dark:bg-lia-bg-secondary">
                    <Search className="w-4 h-4 text-lia-text-secondary" />
                  </div>
                  <p className="text-xs text-lia-text-secondary" role="status" aria-live="polite" aria-atomic="true">{t("noTemplateFound")}</p>
                  <p className="text-xs text-lia-text-tertiary mt-1">{t("tryAdjustFilters")}</p>
                </CardContent>
              </Card>
            ) : (
              <Accordion type="multiple" value={expandedGroups} onValueChange={setExpandedGroups} className="space-y-2">
                {Object.entries(TEMPLATE_GROUPS).map(([groupKey, group]) => {
                  const groupTemplates = groupedTemplates[groupKey] || []
                  if (groupTemplates.length === 0) return null
                  return (
                    <AccordionItem key={groupKey} value={groupKey} className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl overflow-hidden">
                      <AccordionTrigger className="px-3 py-2.5 hover:no-underline hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover/50">
                        <div className="flex items-center gap-2 text-left">
                          <span className="text-lg">{group.icon}</span>
                          <span className={textStyles.subtitle}>{group.label}</span>
                          <Chip variant="neutral" className="text-micro ml-1">{groupTemplates.length}</Chip>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent className="px-2 pb-2">
                        <div className="space-y-2">
                          {groupTemplates.map((template) => (
                            <Card
                              key={template.id}
                              className={`border cursor-pointer transition-colors motion-reduce:transition-none rounded-md backdrop-blur-sm ${
                                selectedTemplate?.id === template.id
                                  ? 'border-lia-btn-primary-bg dark:border-lia-border-subtle'
                                  : 'border-lia-border-subtle dark:border-lia-border-subtle hover:border-lia-border-default hover:'
                              }`}
                              onClick={() => setSelectedTemplate(template)}
                            >
                              <CardContent className="p-2.5">
                                <div className="flex items-start justify-between gap-2">
                                  <div className="flex items-center gap-2 flex-1 min-w-0">
                                    <div className={`w-7 h-7 rounded-md ${categoryLabels[template.category]?.color || 'bg-lia-bg-secondary text-lia-text-secondary'} flex items-center justify-center flex-shrink-0`}>
                                      {template.channel === 'whatsapp' ? <MessageSquare className="w-3.5 h-3.5" /> :
                                       template.channel === 'teams' ? <MessageSquare className="w-3.5 h-3.5" /> :
                                       template.channel === 'bell' ? <Bell className="w-3.5 h-3.5" /> :
                                       <Mail className="w-3.5 h-3.5" />}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                      <div className="flex items-center gap-1.5">
                                        <p className="text-xs font-medium text-lia-text-primary truncate">{template.name}</p>
                                        {template.priority && (
                                          <span className={`w-2 h-2 rounded-full flex-shrink-0 ${PRIORITY_COLORS[template.priority]}`} title={t("priority", { priority: template.priority })} />
                                        )}
                                      </div>
                                      <div className="flex items-center gap-1 mt-0.5 flex-wrap">
                                        {template.trigger_type && (
                                          <Chip variant="neutral" muted className={`text-micro px-1.5 py-0 ${TRIGGER_TYPE_LABELS[template.trigger_type]?.color || ''}`}>
                                            {TRIGGER_TYPE_LABELS[template.trigger_type]?.label || template.trigger_type}
                                          </Chip>
                                        )}
                                        {template.used_in && template.used_in.slice(0, 2).map((usage, idx) => (
                                          <Chip key={idx} variant="neutral" className="text-micro px-1.5 py-0">{usage}</Chip>
                                        ))}
                                        {template.used_in && template.used_in.length > 2 && (
                                          <Chip variant="neutral" className="text-micro px-1.5 py-0">+{template.used_in.length - 2}</Chip>
                                        )}
                                      </div>
                                    </div>
                                  </div>
                                  <Chip variant="neutral" muted={!template.isActive} className="text-micro flex-shrink-0">
                                    {template.isActive ? t("active") : t("inactive")}
                                  </Chip>
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  )
                })}
              </Accordion>
            )}
          </div>

          <div className="space-y-3 lg:sticky lg:top-0 overflow-y-auto pb-20 max-h-[calc(100vh-220px)]">
            {selectedTemplate ? (
              <>
                <div className="flex items-center justify-between">
                  <h3 className={textStyles.h3}>{editingTemplate ? t("editingTemplate") : t("viewing")}</h3>
                  <div className="flex items-center gap-2">
                    {editingTemplate ? (
                      <>
                        <Button variant="ghost" size="sm" onClick={() => setEditingTemplate(null)}>
                          <X className="w-3.5 h-3.5" />
                        </Button>
                        <Button size="sm" className="py-1.5 px-2 text-xs hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active" onClick={handleSaveTemplate}>
                          <Save className="w-3.5 h-3.5 mr-1" />
                          {t("save")}
                        </Button>
                      </>
                    ) : (
                      <Button
                        variant="outline" size="sm"
                        onClick={() => setEditingTemplate({ ...selectedTemplate })}
                        className="rounded-full py-1.5 px-2 text-xs border-lia-btn-primary-bg text-lia-text-primary hover:bg-lia-bg-secondary dark:border-lia-border-subtle dark:hover:bg-lia-btn-primary-bg"
                      >
                        <Edit className="w-3.5 h-3.5 mr-1" />
                        {t("edit")}
                      </Button>
                    )}
                  </div>
                </div>

                <Card className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-lia-bg-primary/80 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-xl">
                  <CardContent className="p-3 space-y-3">
                    {channelFilter === 'email' && (
                      <div>
                        <label className={`block ${textStyles.labelSmall} mb-1`}>{t("subjectLabel")}</label>
                        {editingTemplate ? (
                          <input
                            type="text"
                            value={editingTemplate.subject}
                            onChange={(e) => setEditingTemplate(prev => prev ? { ...prev, subject: e.target.value } : null)}
                            className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary focus:ring-2 focus:outline-none"
                          />
                        ) : (
                          <p className="text-xs text-lia-text-primary bg-lia-bg-secondary rounded-full px-2 py-1.5">{selectedTemplate.subject}</p>
                        )}
                      </div>
                    )}
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <label className={`block ${textStyles.labelSmall}`}>
                          {channelFilter === 'email' ? t("emailBodyLabel") : t("whatsappMessageLabel")}
                        </label>
                        {editingTemplate && (
                          <VariableSelector onSelect={insertVariableAtCursor} disabled={!editingTemplate} />
                        )}
                      </div>
                      {editingTemplate ? (
                        <textarea
                          ref={bodyTextareaRef}
                          value={editingTemplate.body}
                          onChange={(e) => setEditingTemplate(prev => prev ? { ...prev, body: e.target.value } : null)}
                          rows={10}
                          className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary focus:ring-2 focus:outline-none font-mono"
                        />
                      ) : channelFilter === 'whatsapp' ? (
                        <div className="rounded-md p-3 bg-whatsapp-bg">
                          <div className="flex justify-end">
                            <div className="bg-whatsapp-bubble rounded-md p-3 max-w-[85%]">
                              <div className="text-xs text-lia-text-primary whitespace-pre-wrap">
                                {stripHtmlTags(selectedTemplate.body)}
                              </div>
                              <div className="text-micro text-lia-text-secondary text-right mt-1">
                                {new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })} ✓✓
                              </div>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="text-xs text-lia-text-primary bg-lia-bg-secondary rounded-xl px-3 py-2.5 whitespace-pre-wrap max-h-content-md overflow-y-auto">
                          {stripHtmlTags(selectedTemplate.body)}
                        </div>
                      )}
                    </div>
                    <div>
                      <label className={`block ${textStyles.labelSmall} mb-1`}>{t("availableVariables")}</label>
                      <div className="flex flex-wrap gap-1">
                        {selectedTemplate.variables.map((v) => (
                          <Chip key={v} variant="neutral" className="text-micro font-mono rounded-full border-lia-border-default text-lia-text-primary dark:border-lia-border-default">
                            {`{{${v}}}`}
                          </Chip>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {editingTemplate && (
                  <Card className="rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary">
                    <CardContent className="p-4 space-y-3">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-xl flex items-center justify-center bg-lia-bg-tertiary dark:bg-lia-bg-secondary">
                          <Brain className="w-4 h-4 text-wedo-cyan" />
                        </div>
                        <div>
                          <span className={textStyles.h4}>{t("adjustWithLia")}</span>
                          <p className="text-xs text-lia-text-secondary">{t("describeChanges")}</p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={aiPrompt}
                          onChange={(e) => setAiPrompt(e.target.value)}
                          onKeyDown={(e) => e.key === 'Enter' && !isGenerating && aiPrompt.trim() && handleAdjustWithAI()}
                          placeholder={t("aiPlaceholder")}
                          disabled={isGenerating}
                          className="flex-1 px-3 py-2 text-xs border border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-lia-btn-primary-bg/10 focus:border-lia-btn-primary-bg focus:outline-none disabled:bg-lia-bg-secondary disabled:text-lia-text-tertiary dark:bg-lia-bg-secondary dark:border-lia-border-subtle dark:focus:ring-lia-border-subtle/10 dark:focus:border-lia-border-subtle"
                        />
                        <Button
                          onClick={handleAdjustWithAI}
                          disabled={isGenerating || !aiPrompt.trim()}
                          className="gap-1.5 rounded-md py-2 px-3 text-xs min-w-[100px] hover:bg-lia-btn-primary-hover disabled:bg-lia-border-medium dark:hover:bg-lia-interactive-active dark:disabled:bg-lia-border-medium"
                        >
                          {isGenerating ? (
                            <><Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />{t("adjusting")}</>
                          ) : (
                            <><Wand2 className="w-3.5 h-3.5" />{t("adjust")}</>
                          )}
                        </Button>
                      </div>
                      {isGenerating && (
                        <div className="flex items-center gap-2 p-2 rounded-xl bg-lia-bg-tertiary dark:bg-lia-bg-secondary">
                          <div className="flex gap-1">
                            <ThinkingDots dotClassName="bg-lia-btn-primary-bg" size="md" />
                          </div>
                          <span className="text-xs text-lia-text-primary">{t("liaAnalyzing")}</span>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}

                {aiResultModal?.show && (
                  <div className="fixed inset-0 bg-lia-overlay flex items-center justify-center z-[9999] p-4">
                    <Card className="w-full max-w-2xl max-h-[90vh] overflow-hidden rounded-xl bg-lia-bg-primary">
                      <CardHeader className="dark:border-lia-border-subtle pb-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-lia-bg-tertiary dark:bg-lia-bg-secondary">
                              <Brain className="w-5 h-5 text-wedo-cyan" />
                            </div>
                            <div>
                              <CardTitle className={textStyles.h3}>{t("liaAdjustments")}</CardTitle>
                              <p className="text-xs text-lia-text-secondary">{t("reviewChanges")}</p>
                            </div>
                          </div>
                          <Button variant="ghost" size="sm" onClick={handleCancelAIAdjustment} className="rounded-md">
                            <X className="w-4 h-4" />
                          </Button>
                        </div>
                      </CardHeader>
                      <CardContent className="p-4 space-y-4 overflow-y-auto">
                        <div>
                          <label className="block text-xs font-medium text-lia-text-secondary uppercase tracking-wide mb-2">
                            {t("changesMade")}
                          </label>
                          <div className="flex flex-wrap gap-1.5">
                            {aiResultModal.changesMade.map((change, idx) => (
                              <Chip density="relaxed" variant="neutral" muted key={idx} className="px-2 py-0.5 rounded-full dark:bg-status-success dark:text-status-success">
                                <Check className="w-3 h-3 mr-1" />
                                {change}
                              </Chip>
                            ))}
                          </div>
                        </div>
                        {aiResultModal.newSubject && (
                          <div>
                            <label className="block text-xs font-medium text-lia-text-secondary uppercase tracking-wide mb-2">{t("newSubject")}</label>
                            <div className="p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl text-xs text-lia-text-primary">{aiResultModal.newSubject}</div>
                          </div>
                        )}
                        <div>
                          <label className="block text-xs font-medium text-lia-text-secondary uppercase tracking-wide mb-2">{t("newContent")}</label>
                          <div className="p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl text-xs text-lia-text-primary whitespace-pre-wrap max-h-content-md overflow-y-auto font-mono">
                            {aiResultModal.newBody}
                          </div>
                        </div>
                        <div className="p-3 rounded-xl border border-status-warning/30 bg-status-warning/10">
                          <div className="flex items-start gap-2">
                            <AlertCircle className="w-4 h-4 text-status-warning mt-0.5 flex-shrink-0" />
                            <p className="text-xs text-status-warning">
                              {t("applyChangesWarning")} <strong>"{t("applyChangesWarningSave")}"</strong> {t("applyChangesWarningEnd")}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                      <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle p-4 flex items-center justify-end gap-3">
                        <Button variant="outline" onClick={handleCancelAIAdjustment} className="px-4 py-2 text-xs">{t("cancel")}</Button>
                        <Button onClick={handleConfirmAIAdjustment} className="px-4 py-2 text-xs gap-1.5 hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active">
                          <Check className="w-3.5 h-3.5" />
                          {t("applyAdjustments")}
                        </Button>
                      </div>
                    </Card>
                  </div>
                )}
              </>
            ) : (
              <Card className="border-dashed border-2 border-lia-border-subtle dark:border-lia-border-subtle rounded-xl h-full flex items-center justify-center backdrop-blur-sm">
                <CardContent className="text-center py-8">
                  <Mail className="w-10 h-10 text-lia-text-disabled mx-auto mb-3" />
                  <p className="text-xs text-lia-text-secondary">{t("selectTemplate")}</p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
