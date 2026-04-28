"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Bell, Mail, MessageSquare } from "lucide-react"

export interface SettingsNotificationsTabProps {
  onSettingsChange: (changed: boolean) => void
}

export function SettingsNotificationsTab({ onSettingsChange }: SettingsNotificationsTabProps) {
  const t = useTranslations("settings.notifications")
  const [notifications, setNotifications] = useState({
    email: true,
    push: true,
    whatsapp: false,
    newCandidates: true,
    interviews: true,
    deadlines: true,
    liaInsights: true
  })

  const channels = [
    { key: "email", label: t("channelEmail"), icon: Mail, desc: t("channelEmailDesc") },
    { key: "push", label: t("channelPush"), icon: Bell, desc: t("channelPushDesc") },
    { key: "whatsapp", label: t("channelWhatsapp"), icon: MessageSquare, desc: t("channelWhatsappDesc") }
  ]

  const types = [
    { key: "newCandidates", label: t("newCandidates"), desc: t("newCandidatesDesc") },
    { key: "interviews", label: t("interviews"), desc: t("interviewsDesc") },
    { key: "deadlines", label: t("deadlines"), desc: t("deadlinesDesc") },
    { key: "liaInsights", label: t("liaInsights"), desc: t("liaInsightsDesc") }
  ]

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm font-semibold">
            <Bell className="w-4 h-4" />
            {t("channelsTitle")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {channels.map((channel) => (
            <div key={channel.key} className="flex items-center justify-between p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
              <div className="flex items-center gap-3">
                <channel.icon className="w-4 h-4 text-lia-text-primary" />
                <div>
                  <div className="text-sm font-medium text-lia-text-primary">{channel.label}</div>
                  <div className="text-xs text-lia-text-primary">{channel.desc}</div>
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
          <CardTitle>{t("typesTitle")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {types.map((type) => (
            <div key={type.key} className="flex items-center justify-between p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
              <div>
                <div className="text-sm font-medium text-lia-text-primary">{type.label}</div>
                <div className="text-xs text-lia-text-primary">{type.desc}</div>
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
