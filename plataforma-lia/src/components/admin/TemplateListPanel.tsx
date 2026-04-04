"use client"

import React from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { Search } from "lucide-react"
import {
  EmailTemplate,
  TEMPLATE_GROUPS,
  TRIGGER_TYPE_LABELS,
  PRIORITY_COLORS,
  CHANNEL_LABELS,
  getChannelIcon,
} from "./AdminTemplateHub.types"

interface TemplateListPanelProps {
  filteredTemplates: EmailTemplate[]
  groupedTemplates: Record<string, EmailTemplate[]>
  selectedTemplate: EmailTemplate | null
  expandedGroups: string[]
  setExpandedGroups: (groups: string[]) => void
  onSelectTemplate: (template: EmailTemplate) => void
}

export function TemplateListPanel({
  filteredTemplates,
  groupedTemplates,
  selectedTemplate,
  expandedGroups,
  setExpandedGroups,
  onSelectTemplate,
}: TemplateListPanelProps) {
  if (filteredTemplates.length === 0) {
    return (
      <Card className="border border-dashed border-lia-border-subtle rounded-md">
        <CardContent className="p-4 text-center">
          <div className="w-10 h-10 rounded-full flex items-center justify-center mx-auto mb-2 bg-lia-interactive-active/30">
            <Search className="w-4 h-4 text-lia-text-secondary" />
          </div>
          <p className="text-sm text-lia-text-secondary" aria-live="polite" aria-atomic="true">
            Nenhum template encontrado
          </p>
          <p className="text-xs text-lia-text-secondary mt-1">
            Tente ajustar os filtros de busca
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Accordion
      type="multiple"
      value={expandedGroups}
      onValueChange={setExpandedGroups}
      className="space-y-2"
    >
      {Object.entries(TEMPLATE_GROUPS).map(([groupKey, group]) => {
        const groupTemplates = groupedTemplates[groupKey] || []
        if (groupTemplates.length === 0) return null

        return (
          <AccordionItem key={groupKey} value={groupKey} className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md overflow-hidden">
            <AccordionTrigger className="px-3 py-2.5 hover:no-underline hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover/50">
              <div className="flex items-center gap-2 text-left">
                <span className="text-lg">{group.icon}</span>
                <span className="text-sm font-semibold text-lia-text-primary">
                  {group.label}
                </span>
                <Badge variant="outline" className="text-xs ml-1">
                  {groupTemplates.length}
                </Badge>
              </div>
            </AccordionTrigger>
            <AccordionContent className="px-2 pb-2">
              <div className="space-y-2">
                {groupTemplates.map((template) => {
                  const ChannelIcon = getChannelIcon(template.channel || 'email')
                  return (
                    <Card
                      key={template.id}
                      className={`border cursor-pointer transition-colors motion-reduce:transition-none rounded-md ${
                        selectedTemplate?.id === template.id
                          ? 'border-lia-btn-primary-bg'
                          : 'border-lia-border-subtle dark:border-lia-border-subtle hover:border-lia-border-default'
                      }`}
                      style={selectedTemplate?.id === template.id ? { boxShadow: '0 0 0 2px var(--wedo-cyan-bg-20)' } : {}}
                      onClick={() => onSelectTemplate(template)}
                    >
                      <CardContent className="p-2.5">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex items-center gap-2 flex-1 min-w-0">
                            <div className={`w-7 h-7 rounded-md ${CHANNEL_LABELS[template.channel || 'email']?.color || 'bg-lia-bg-secondary text-lia-text-secondary'} flex items-center justify-center flex-shrink-0`}>
                              <ChannelIcon className="w-3.5 h-3.5" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-1.5">
                                <p className="text-xs font-medium text-lia-text-primary truncate">
                                  {template.name}
                                </p>
                                {template.priority && (
                                  <span className={`w-2 h-2 rounded-full flex-shrink-0 ${PRIORITY_COLORS[template.priority]}`} title={`Prioridade: ${template.priority}`} />
                                )}
                              </div>
                              <div className="flex items-center gap-1 mt-0.5 flex-wrap">
                                <Badge className={`text-micro px-1.5 py-0 ${CHANNEL_LABELS[template.channel || 'email']?.color || ''}`}>
                                  {CHANNEL_LABELS[template.channel || 'email']?.label || template.channel}
                                </Badge>
                                {template.trigger_type && (
                                  <Badge className={`text-micro px-1.5 py-0 ${TRIGGER_TYPE_LABELS[template.trigger_type]?.color || ''}`}>
                                    {TRIGGER_TYPE_LABELS[template.trigger_type]?.label || template.trigger_type}
                                  </Badge>
                                )}
                              </div>
                            </div>
                          </div>
                          <Badge variant={template.isActive ? "default" : "outline"} className="text-micro flex-shrink-0" style={template.isActive ? { backgroundColor: 'var(--lia-btn-primary-bg)' } : {}}>
                            {template.isActive ? 'Ativo' : 'Inativo'}
                          </Badge>
                        </div>
                      </CardContent>
                    </Card>
                  )
                })}
              </div>
            </AccordionContent>
          </AccordionItem>
        )
      })}
    </Accordion>
  )
}
