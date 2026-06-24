"use client"

/**
 * DataChannelSettings — Canal padrão de coleta de dados do candidato.
 *
 * Reads/writes `communication_rules.preferred_data_channel` from the
 * CompanyHiringPolicy via the canonical hiring-policy proxy route.
 *
 * Follows Settings canonical patterns (CLAUDE.md):
 * - useQuery for server data (REGRA 1)
 * - SETTINGS_QUERY_KEYS.hiringPolicy() (canonical keys)
 * - useMutation + dispatchSettingsUpdate on success (REGRA 5)
 * - HubHeader from _shared (REGRA 3)
 * - No company_id in payload (Pydantic REGRA 2)
 */

import React from "react"
import { useTranslations } from "next-intl"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Mail, Globe, MessageSquare, Phone } from "lucide-react"
import { SETTINGS_QUERY_KEYS, dispatchSettingsUpdate } from "@/hooks/settings/useSettingsBroadcast"
import { HubHeader } from "@/components/settings/_shared"

type DataChannel = "email" | "web" | "whatsapp" | "voice"

const CHANNELS: { id: DataChannel; iconKey: string }[] = [
  { id: "email", iconKey: "channelEmail" },
  { id: "web", iconKey: "channelWeb" },
  { id: "whatsapp", iconKey: "channelWhatsapp" },
  { id: "voice", iconKey: "channelVoice" },
]

const CHANNEL_ICONS: Record<DataChannel, React.ElementType> = {
  email: Mail,
  web: Globe,
  whatsapp: MessageSquare,
  voice: Phone,
}

async function fetchHiringPolicy() {
  const r = await fetch("/api/backend-proxy/hiring-policy")
  if (!r.ok) throw new Error(`hiring-policy fetch failed: ${r.status}`)
  return r.json()
}

async function patchDataChannel(channel: DataChannel) {
  const r = await fetch("/api/backend-proxy/hiring-policy/block", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      block: "communication_rules",
      data: { preferred_data_channel: channel },
    }),
  })
  if (!r.ok) throw new Error(`patch failed: ${r.status}`)
  return r.json()
}

export function DataChannelSettings() {
  const t = useTranslations("settings.communication.dataChannel")
  const queryClient = useQueryClient()

  const { data: policy, isLoading } = useQuery({
    queryKey: SETTINGS_QUERY_KEYS.hiringPolicy(),
    queryFn: fetchHiringPolicy,
    staleTime: 30_000,
  })

  const currentChannel: DataChannel =
    policy?.communication_rules?.preferred_data_channel ?? "email"

  const mutation = useMutation({
    mutationFn: patchDataChannel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEYS.hiringPolicy() })
      dispatchSettingsUpdate({
        actionId: crypto.randomUUID(),
        section: "communication",
        field: "preferred_data_channel",
        source: "ui",
        ts: Date.now(),
      })
    },
  })

  const handleSelect = (channel: DataChannel) => {
    if (channel !== currentChannel && !mutation.isPending) {
      mutation.mutate(channel)
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-3" data-testid="data-channel-loading">
        <div className="h-6 w-48 bg-lia-surface-secondary rounded animate-pulse" />
        <div className="h-20 w-full bg-lia-surface-secondary rounded animate-pulse" />
      </div>
    )
  }

  return (
    <div className="space-y-4" data-testid="data-channel-settings">
      <HubHeader title={t("title")} description={t("description")} />

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3" role="radiogroup" aria-label={t("title")}>
        {CHANNELS.map(({ id, iconKey }) => {
          const Icon = CHANNEL_ICONS[id]
          const isSelected = currentChannel === id
          return (
            <button
              key={id}
              type="button"
              role="radio"
              aria-checked={isSelected}
              onClick={() => handleSelect(id)}
              disabled={mutation.isPending}
              className={`
                flex items-start gap-3 p-4 rounded-lg border text-left transition-colors
                ${isSelected
                  ? "border-lia-primary bg-lia-primary/5 ring-1 ring-lia-primary"
                  : "border-lia-border hover:border-lia-primary/40 bg-lia-surface"
                }
                disabled:opacity-50 disabled:cursor-not-allowed
              `}
              data-testid={`data-channel-${id}`}
            >
              <div className={`
                w-8 h-8 rounded-md flex items-center justify-center shrink-0
                ${isSelected ? "bg-lia-primary/15 text-lia-primary" : "bg-lia-surface-secondary text-lia-text-secondary"}
              `}>
                <Icon className="w-4 h-4" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-lia-text-primary">
                  {t(iconKey)}
                </p>
                <p className="text-xs text-lia-text-secondary mt-0.5">
                  {t(`${iconKey}Desc`)}
                </p>
              </div>
              {isSelected && (
                <div className="w-4 h-4 rounded-full border-4 border-lia-primary shrink-0 mt-1" aria-hidden="true" />
              )}
            </button>
          )
        })}
      </div>

      {mutation.isError && (
        <p className="text-sm text-status-error" role="alert">{t("saveError")}</p>
      )}
      {mutation.isSuccess && (
        <p className="text-sm text-status-success" role="status">{t("saveSuccess")}</p>
      )}
    </div>
  )
}
