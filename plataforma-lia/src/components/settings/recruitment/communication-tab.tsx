"use client"

import { useState } from "react"
import { useTranslations, useLocale } from "next-intl"
import { useQuery } from "@tanstack/react-query"
import { Chip } from "@/components/ui/chip"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  Mail, Bell, MessageSquare, Phone, Zap, Plus, Edit,
  MoreVertical, CheckCircle,
} from "lucide-react"

interface EmailTemplate {
  id: string
  name: string
  subject: string
  type: string
  status: "active" | "paused"
  trigger: string
  lastModified: string
}

export function CommunicationTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const t = useTranslations("settings.recruitment.communicationTab")
  const locale = useLocale()
  const [activeSubTab, setActiveSubTab] = useState<'templates' | 'notifications' | 'whatsapp' | 'sms' | 'automation'>('templates')

  const { data: templates = [], isLoading: isLoadingTemplates } = useQuery<EmailTemplate[]>({
    queryKey: ["communication-templates-recruitment"],
    queryFn: async () => {
      const resp = await fetch("/api/backend-proxy/communication/templates")
      if (!resp.ok) return []
      const data = await resp.json()
      // backend may return { templates: [...] } or plain array
      if (Array.isArray(data)) return data
      if (Array.isArray(data?.templates)) return data.templates
      return []
    },
    staleTime: 300_000, // 5 min — templates rarely change
  })

  const subTabs = [
    { id: 'templates', name: t('emailTemplates'), icon: Mail },
    { id: 'notifications', name: t('notifications'), icon: Bell },
    { id: 'whatsapp', name: t('whatsappBusiness'), icon: MessageSquare },
    { id: 'sms', name: t('sms'), icon: Phone },
    { id: 'automation', name: t('automation'), icon: Zap },
  ]

  const notificationItems = [
    { key: 'newCandidate' },
    { key: 'interviewScheduled' },
    { key: 'interviewReminder' },
    { key: 'feedbackDue' },
    { key: 'candidateReply' },
    { key: 'processDeadline' },
  ] as const

  const messageTemplates = [
    { id: 'invite', name: t('msgTemplate_inviteName'), message: t('msgTemplate_inviteText', { vaga: '{vaga}' }) },
    { id: 'reminder', name: t('msgTemplate_reminderName'), message: t('msgTemplate_reminderText', { horario: '{horario}' }) },
    { id: 'docs', name: t('msgTemplate_docsName'), message: t('msgTemplate_docsText', { documentos: '{documentos}' }) },
  ]

  const automations = [
    { id: 'response', name: t('auto_responseName'), description: t('auto_responseDesc'), status: 'active' as const, trigger: t('auto_responseTrigger') },
    { id: 'followup', name: t('auto_followupName'), description: t('auto_followupDesc'), status: 'active' as const, trigger: t('auto_followupTrigger') },
    { id: 'deadline', name: t('auto_deadlineName'), description: t('auto_deadlineDesc'), status: 'paused' as const, trigger: t('auto_deadlineTrigger') },
    { id: 'reengage', name: t('auto_reengageName'), description: t('auto_reengageDesc'), status: 'active' as const, trigger: t('auto_reengageTrigger') },
  ]

  const renderTemplates = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Mail className="w-4 h-4" />
              {t('emailTemplates')}
            </div>
            <Button className="gap-2">
              <Plus className="w-4 h-4" />
              {t('newTemplate')}
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoadingTemplates ? (
            <div className="space-y-4">
              {[1, 2, 3].map((n) => (
                <div key={n} className="h-20 rounded-xl bg-lia-bg-secondary animate-pulse" />
              ))}
            </div>
          ) : templates.length === 0 ? (
            <div className="text-center py-8 text-lia-text-primary text-sm">
              {t('noTemplatesYet')}
            </div>
          ) : (
            <div className="space-y-4">
              {templates.map((template) => (
                <div key={template.id} className="flex items-center justify-between p-4 border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-wedo-cyan/15 dark:bg-wedo-cyan/20 rounded-md flex items-center justify-center">
                      <Mail className="w-5 h-5 text-lia-text-secondary" />
                    </div>
                    <div>
                      <h4 className="font-medium text-lia-text-primary">{template.name}</h4>
                      <p className="text-sm text-lia-text-primary">{template.subject}</p>
                      <div className="flex items-center gap-3 mt-1 text-xs text-lia-text-primary">
                        <span>{t('triggerLabel', { value: template.trigger })}</span>
                        <span>•</span>
                        <span>{t('modifiedOn', { date: new Date(template.lastModified).toLocaleDateString(locale) })}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Chip variant="neutral" muted={template.status !== 'active'}>
                      {template.status === 'active' ? t('statusActive') : t('statusPaused')}
                    </Chip>
                    <Button variant="outline" size="sm">
                      <Edit className="w-4 h-4 mr-2" />
                      {t('edit')}
                    </Button>
                    <Button variant="ghost" size="sm">
                      <MoreVertical className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t('generalEmailSettings')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-2 block">
                {t('senderName')}
              </label>
              <input
                key={t('senderDefault')}
                type="text"
                defaultValue={t('senderDefault')}
                onChange={() => onSettingsChange(true)}
                className="w-full p-2 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary text-sm"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-2 block">
                {t('replyEmail')}
              </label>
              <input
                key={t('replyEmailDefault')}
                type="email"
                defaultValue={t('replyEmailDefault')}
                onChange={() => onSettingsChange(true)}
                className="w-full p-2 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary text-sm"
              />
            </div>
          </div>
          <div>
            <label className="text-sm font-medium text-lia-text-primary mb-2 block">
              {t('defaultSignature')}
            </label>
            <textarea
              key={t('signatureDefault')}
              rows={4}
              defaultValue={t('signatureDefault')}
              onChange={() => onSettingsChange(true)}
              className="w-full p-2 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary text-sm"
            />
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderNotifications = () => (
    <div className="space-y-6">
      {/* P0-W1-13: Ghost-setting banner — notification channel config is pure local state, not persisted */}
      <div className="rounded-lg border border-status-warning-border bg-status-warning-bg px-4 py-3">
        <div className="flex items-start gap-3">
          <span className="inline-flex items-center rounded-full bg-status-warning/10 px-2.5 py-0.5 text-micro font-semibold text-status-warning flex-shrink-0 mt-0.5">
            {t('comingSoon')}
          </span>
          <p className="text-sm text-status-warning">
            {t('notificationsComingSoonText')}
          </p>
        </div>
      </div>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="w-4 h-4" />
            {t('notificationSettings')}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {notificationItems.map((notification) => (
            <div key={notification.key} className="flex items-center justify-between p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl opacity-60 pointer-events-none select-none">
              <div>
                <div className="text-sm font-medium text-lia-text-primary">{t(`notif_${notification.key}_label` as never)}</div>
                <div className="text-xs text-lia-text-primary">{t(`notif_${notification.key}_desc` as never)}</div>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <input type="checkbox" defaultChecked disabled className="text-lia-text-secondary cursor-not-allowed" />
                  <span className="text-xs text-lia-text-primary">{t('email')}</span>
                </div>
                <div className="flex items-center gap-2">
                  <input type="checkbox" disabled className="text-lia-text-secondary cursor-not-allowed" />
                  <span className="text-xs text-lia-text-primary">{t('push')}</span>
                </div>
                <div className="flex items-center gap-2">
                  <input type="checkbox" disabled className="text-lia-text-secondary cursor-not-allowed" />
                  <span className="text-xs text-lia-text-primary">{t('whatsappBusiness')}</span>
                </div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )

  const renderWhatsApp = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="w-4 h-4" />
            {t('whatsappBusiness')}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-4 bg-status-success/10 dark:bg-status-success/20 border border-status-success/30 dark:border-status-success/30 rounded-xl">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="w-5 h-5 text-status-success" />
              <span className="font-medium text-status-success dark:text-status-success">{t('whatsappConnected')}</span>
            </div>
            <p className="text-sm text-status-success dark:text-status-success">
              {t('whatsappNumber')}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-2 block">
                {t('welcomeMessage')}
              </label>
              <textarea
                key={t('welcomeMessageDefault')}
                rows={3}
                defaultValue={t('welcomeMessageDefault')}
                onChange={() => onSettingsChange(true)}
                className="w-full p-2 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary text-sm"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-2 block">
                {t('serviceHours')}
              </label>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm w-16">{t('monday')}</span>
                  <input type="time" defaultValue="08:00" className="text-xs" onChange={() => onSettingsChange(true)} />
                  <span className="text-xs">{t('to')}</span>
                  <input type="time" defaultValue="18:00" className="text-xs" onChange={() => onSettingsChange(true)} />
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm w-16">{t('friday')}</span>
                  <input type="time" defaultValue="08:00" className="text-xs" onChange={() => onSettingsChange(true)} />
                  <span className="text-xs">{t('to')}</span>
                  <input type="time" defaultValue="17:00" className="text-xs" onChange={() => onSettingsChange(true)} />
                </div>
              </div>
            </div>
          </div>

          <div>
            <h4 className="font-medium text-lia-text-primary mb-3">{t('messageTemplates')}</h4>
            <div className="space-y-2">
              {messageTemplates.map((template) => (
                <div key={template.id} className="p-3 border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-sm">{template.name}</span>
                    <Button variant="outline" size="sm">{t('edit')}</Button>
                  </div>
                  <p className="text-xs text-lia-text-primary">{template.message}</p>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderSMS = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Phone className="w-4 h-4" />
            {t('sms')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Phone className="w-12 h-12 text-lia-text-primary mx-auto mb-4" />
            <h3 className="text-lg font-medium text-lia-text-primary mb-2">{t('smsInDevelopment')}</h3>
            <p className="text-lia-text-primary mb-4">
              {t('smsComingSoon')}
            </p>
            <Button variant="outline">
              {t('requestEarlyAccess')}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderAutomation = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="w-4 h-4" />
            {t('communicationAutomation')}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-4">
            {automations.map((automation) => (
              <div key={automation.id} className="flex items-center justify-between p-4 border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-md flex items-center justify-center ${
                    automation.status === 'active' ? 'bg-status-success/15 dark:bg-status-success/20' : 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary'
                  }`}>
                    <Zap className={`w-5 h-5 ${
                      automation.status === 'active' ? 'text-status-success' : 'text-lia-text-primary'
                    }`} />
                  </div>
                  <div>
                    <h4 className="font-medium text-lia-text-primary">{automation.name}</h4>
                    <p className="text-sm text-lia-text-primary">{automation.description}</p>
                    <p className="text-xs text-lia-text-primary">{t('triggerLabel', { value: automation.trigger })}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Chip variant="neutral" muted={automation.status !== 'active'}>
                    {automation.status === 'active' ? t('automationStatusActive') : t('automationStatusPaused')}
                  </Chip>
                  <Button variant="outline" size="sm">
                    {t('configure')}
                  </Button>
                </div>
              </div>
            ))}
          </div>

          <Button className="w-full gap-2" variant="outline">
            <Plus className="w-4 h-4" />
            {t('newAutomation')}
          </Button>
        </CardContent>
      </Card>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Sub Navigation */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-1 overflow-x-auto">
            {subTabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveSubTab(tab.id as Parameters<typeof setActiveSubTab>[0])}
                className={`flex items-center gap-2 px-4 py-3 rounded-md text-sm font-medium whitespace-nowrap transition-colors motion-reduce:transition-none ${
                  activeSubTab === tab.id
                    ? 'bg-lia-bg-secondary dark:bg-lia-bg-secondary text-lia-text-primary'
                    : 'hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover text-lia-text-primary'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.name}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Sub Tab Content */}
      {activeSubTab === 'templates' && renderTemplates()}
      {activeSubTab === 'notifications' && renderNotifications()}
      {activeSubTab === 'whatsapp' && renderWhatsApp()}
      {activeSubTab === 'sms' && renderSMS()}
      {activeSubTab === 'automation' && renderAutomation()}
    </div>
  )
}
