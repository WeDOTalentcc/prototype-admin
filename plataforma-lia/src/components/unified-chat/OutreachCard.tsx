"use client"

import React, { useState } from "react"
import { cn } from "@/lib/utils"
import {
  Mail, MessageSquare, Phone, Globe, Mic2,
  Pencil, Send, CheckCircle, ChevronDown, ChevronUp,
} from "lucide-react"

type OutreachChannel = "email" | "whatsapp" | "phone" | "webchat" | "voip"

export interface OutreachData {
  channel: OutreachChannel
  candidate_name: string
  candidate_id?: string
  // email
  subject?: string
  body?: string
  // whatsapp
  phone?: string
  template?: string
  // phone/voip
  script?: string[]
  estimated_duration?: string
  // webchat
  initial_message?: string
  // voip
  extension?: string
  recording?: boolean
}

interface Props {
  data: OutreachData
}

const CHANNEL_META: Record<OutreachChannel, { icon: React.ElementType; label: string; color: string }> = {
  email: { icon: Mail, label: "Email", color: "text-lia-text-secondary" },
  whatsapp: { icon: MessageSquare, label: "WhatsApp", color: "text-status-success" },
  phone: { icon: Phone, label: "Ligação", color: "text-lia-text-secondary" },
  webchat: { icon: Globe, label: "Chat Web", color: "text-lia-text-secondary" },
  voip: { icon: Mic2, label: "VoIP", color: "text-lia-text-secondary" },
}

/**
 * OutreachCard — inline outreach preview for all channels.
 * Renders in the chat message list when message metadata.type === "outreach_message".
 * Recruiter reviews content before sending; Edit button opens the right panel for edits.
 */
export function OutreachCard({ data }: Props) {
  const [sent, setSent] = useState(false)
  const [expanded, setExpanded] = useState(false)

  const meta = CHANNEL_META[data.channel]
  const Icon = meta.icon

  const handleSend = () => {
    window.dispatchEvent(new CustomEvent("lia:outreach-send", {
      detail: { channel: data.channel, candidateId: data.candidate_id, data },
    }))
    setSent(true)
  }

  const handleEdit = () => {
    window.dispatchEvent(new CustomEvent("lia:outreach-edit", {
      detail: { channel: data.channel, candidateId: data.candidate_id, data },
    }))
  }

  if (sent) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 rounded-md border border-lia-border-subtle bg-lia-bg-secondary max-w-[85%]">
        <CheckCircle className="w-4 h-4 text-status-success flex-shrink-0" aria-hidden="true" />
        <span className="text-xs text-lia-text-secondary">
          {meta.label} enviado para {data.candidate_name}
        </span>
      </div>
    )
  }

  return (
    <div className="rounded-md border border-lia-border-subtle bg-lia-bg-secondary max-w-[85%] overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-2.5 border-b border-lia-border-subtle">
        <Icon className={cn("w-4 h-4 flex-shrink-0", meta.color)} aria-hidden="true" />
        <span className="text-xs font-semibold text-lia-text-primary">
          {meta.label} · {data.candidate_name}
        </span>
      </div>

      {/* Channel-specific content */}
      <div className="px-3 py-2">
        {data.channel === "email" && (
          <EmailContent
            subject={data.subject}
            body={data.body}
            expanded={expanded}
            onToggle={() => setExpanded((v) => !v)}
          />
        )}
        {data.channel === "whatsapp" && (
          <WhatsAppContent message={data.initial_message ?? data.body} phone={data.phone} template={data.template} />
        )}
        {(data.channel === "phone" || data.channel === "voip") && (
          <ScriptContent script={data.script} duration={data.estimated_duration} />
        )}
        {data.channel === "webchat" && (
          <ChatContent message={data.initial_message ?? data.body} />
        )}
      </div>

      {/* VoIP extra info */}
      {/*
        A-09 / WCAG 2.1 AA 1.4.3: previously `text-[10px] text-lia-text-muted`
        (~9 px after Tailwind base, ~2.85:1 contrast). Promoted to `text-xs`
        (12 px) and `text-lia-text-secondary` (#6B7280, ≥4.5:1 on white).
      */}
      {data.channel === "voip" && data.extension && (
        <div className="px-3 pb-2 text-xs text-lia-text-secondary">
          Ramal: {data.extension} · Gravação: {data.recording ? "Ativada" : "Desativada"}
        </div>
      )}

      {/* Action buttons */}
      <div className="flex items-center gap-2 px-3 py-2.5 border-t border-lia-border-subtle">
        <button
          onClick={handleEdit}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border border-lia-border-subtle text-xs text-lia-text-secondary hover:text-lia-text-primary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
        >
          <Pencil className="w-3.5 h-3.5" aria-hidden="true" />
          Editar
        </button>
        <ActionButton channel={data.channel} onAction={handleSend} />
      </div>
    </div>
  )
}

function EmailContent({
  subject,
  body,
  expanded,
  onToggle,
}: {
  subject?: string
  body?: string
  expanded: boolean
  onToggle: () => void
}) {
  const preview = body ? body.slice(0, 120) : ""
  const hasMore = body ? body.length > 120 : false

  return (
    <div className="space-y-1">
      {subject && (
        <p className="text-xs font-medium text-lia-text-primary truncate">
          {subject}
        </p>
      )}
      <p className="text-xs text-lia-text-secondary leading-relaxed">
        {expanded ? body : preview}
        {hasMore && !expanded && "..."}
      </p>
      {hasMore && (
        <button
          onClick={onToggle}
          className="flex items-center gap-0.5 text-[10px] text-lia-text-muted hover:underline"
        >
          {expanded ? (
            <><ChevronUp className="w-3 h-3" aria-hidden="true" /> ver menos</>
          ) : (
            <><ChevronDown className="w-3 h-3" aria-hidden="true" /> ver mais</>
          )}
        </button>
      )}
    </div>
  )
}

function WhatsAppContent({
  message,
  phone,
  template,
}: {
  message?: string
  phone?: string
  template?: string
}) {
  return (
    <div className="space-y-1">
      {/* A-09 / WCAG 2.1 AA 1.4.3: phone & template promoted from
          `text-[10px] text-lia-text-muted` to `text-xs text-lia-text-secondary`. */}
      {phone && (
        <p className="text-xs text-lia-text-secondary">{phone}</p>
      )}
      {message && (
        <p className="text-xs text-lia-text-secondary leading-relaxed">
          "{message.slice(0, 140)}{message.length > 140 ? "..." : ""}"
        </p>
      )}
      {template && (
        <p className="text-xs text-lia-text-secondary">
          Template: {template}
        </p>
      )}
    </div>
  )
}

function ScriptContent({ script, duration }: { script?: string[]; duration?: string }) {
  return (
    <div className="space-y-1">
      {/* A-09 / WCAG 2.1 AA 1.4.3: duration & step counters promoted from
          `text-[10px] text-lia-text-muted` to `text-xs text-lia-text-secondary`. */}
      {duration && (
        <p className="text-xs text-lia-text-secondary">
          Duração estimada: {duration}
        </p>
      )}
      {script && script.length > 0 && (
        <ol className="space-y-0.5 pl-0">
          {script.slice(0, 4).map((step, i) => (
            <li key={i} className="flex items-start gap-1.5 text-xs text-lia-text-secondary">
              <span className="text-lia-text-secondary flex-shrink-0 mt-0.5">{i + 1}.</span>
              {step}
            </li>
          ))}
          {script.length > 4 && (
            <li className="text-xs text-lia-text-secondary pl-4">
              +{script.length - 4} pontos...
            </li>
          )}
        </ol>
      )}
    </div>
  )
}

function ChatContent({ message }: { message?: string }) {
  return (
    <p className="text-xs text-lia-text-secondary leading-relaxed">
      "{message?.slice(0, 140)}{message && message.length > 140 ? "..." : ""}"
    </p>
  )
}

function ActionButton({ channel, onAction }: { channel: OutreachChannel; onAction: () => void }) {
  const labels: Record<OutreachChannel, { label: string; icon: React.ElementType }> = {
    email: { label: "Aprovar e enviar", icon: Send },
    whatsapp: { label: "Enviar via WhatsApp", icon: Send },
    phone: { label: "Iniciar ligação", icon: Phone },
    webchat: { label: "Abrir chat", icon: Globe },
    voip: { label: "Iniciar VoIP", icon: Mic2 },
  }
  const { label, icon: Icon } = labels[channel]

  return (
    <button
      onClick={onAction}
      className="flex-1 flex items-center justify-center gap-1.5 px-2.5 py-1.5 rounded-md bg-gray-900 text-white text-xs font-medium hover:bg-gray-800 transition-colors motion-reduce:transition-none"
    >
      <Icon className="w-3.5 h-3.5" aria-hidden="true" />
      {label}
    </button>
  )
}
