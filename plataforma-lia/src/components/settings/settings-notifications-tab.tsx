"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Bell, Mail, MessageSquare } from "lucide-react"

export interface SettingsNotificationsTabProps {
  onSettingsChange: (changed: boolean) => void
}

export function SettingsNotificationsTab({ onSettingsChange }: SettingsNotificationsTabProps) {
  const [notifications, setNotifications] = useState({
    email: true,
    push: true,
    whatsapp: false,
    slack: true,
    newCandidates: true,
    interviews: true,
    deadlines: true,
    liaInsights: true
  })

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <Bell className="w-4 h-4" />
            Canais de Notificação
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {[
            { key: "email", label: "Email", icon: Mail, desc: "Notificações por email" },
            { key: "push", label: "Push", icon: Bell, desc: "Notificações do navegador" },
            { key: "whatsapp", label: "WhatsApp", icon: MessageSquare, desc: "Mensagens WhatsApp" },
            { key: "slack", label: "Slack", icon: MessageSquare, desc: "Mensagens Slack" }
          ].map((channel) => (
            <div key={channel.key} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
              <div className="flex items-center gap-3">
                <channel.icon className="w-4 h-4 text-gray-800 dark:text-gray-200" />
                <div>
                  <div className="text-sm font-medium text-gray-950 dark:text-gray-50">{channel.label}</div>
                  <div className="text-xs text-gray-800 dark:text-gray-400">{channel.desc}</div>
                </div>
              </div>
              <input
                type="checkbox"
                checked={notifications[channel.key as keyof typeof notifications] as boolean}
                onChange={(e) => {
                  setNotifications(prev => ({ ...prev, [channel.key]: e.target.checked }))
                  onSettingsChange(true)
                }}
              />
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Tipos de Notificação</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {[
            { key: "newCandidates", label: "Novos Candidatos", desc: "Quando novos candidatos se inscrevem" },
            { key: "interviews", label: "Entrevistas", desc: "Lembretes e confirmações de entrevistas" },
            { key: "deadlines", label: "Prazos", desc: "Deadlines de feedback e processos" },
            { key: "liaInsights", label: "Insights da LIA", desc: "Análises e sugestões da IA" }
          ].map((type) => (
            <div key={type.key} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
              <div>
                <div className="text-sm font-medium text-gray-950 dark:text-gray-50">{type.label}</div>
                <div className="text-xs text-gray-800 dark:text-gray-400">{type.desc}</div>
              </div>
              <input
                type="checkbox"
                checked={notifications[type.key as keyof typeof notifications] as boolean}
                onChange={(e) => {
                  setNotifications(prev => ({ ...prev, [type.key]: e.target.checked }))
                  onSettingsChange(true)
                }}
              />
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
