"use client"

import { useState } from "react"
import { textStyles, previewChipVariants } from '@/lib/design-tokens'
import { formatDate as formatDateUtil } from '@/lib/format-utils'
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { CandidateAvatar } from"@/components/candidate-profile/CandidateAvatar"
import {
  X, Calendar, MessageSquare, Clock, Brain, CheckCircle, AlertCircle, Expand,
  Mail, Phone, Pencil, Loader2,
} from"lucide-react"
import { Tooltip, TooltipContent, TooltipTrigger } from"@/components/ui/tooltip"
import { toast } from "sonner"
import dynamic from"next/dynamic"
import type { CandidateData } from"./ProfileTabTypes"


type ContactFieldKind = "email" | "phone"

interface ContactFieldProps {
  kind: ContactFieldKind
  value: string | undefined
  candidateId: string | undefined
  onSaved: (next: string) => void
}

/**
 * Inline contact field exibido no header do preview.
 * - Empty: chip "Adicionar email/telefone" + lápis
 * - Filled: ícone + valor + lápis on hover/focus
 * - Edit: Popover ancorado no lápis, com input pré-preenchido e Salvar/Cancelar
 *
 * PUT canonical: /api/backend-proxy/rh/candidates/:id (Rails). Field name segue
 * o schema Rails (`email`, `phone`). Optimistic update local; rollback no erro.
 */
function ContactField({ kind, value, candidateId, onSaved }: ContactFieldProps) {
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState(value ?? "")
  const [saving, setSaving] = useState(false)

  const Icon = kind === "email" ? Mail : Phone
  const label = kind === "email" ? "Email" : "Telefone"
  const inputType = kind === "email" ? "email" : "tel"
  const placeholder = kind === "email" ? "exemplo@empresa.com" : "+55 11 9XXXX-XXXX"
  const fieldName = kind === "email" ? "email" : "phone"
  const linkAction = kind === "email"
    ? (v: string) => `mailto:${v}`
    : (v: string) => `https://wa.me/${v.replace(/\D/g, "")}`

  const handleOpenChange = (next: boolean) => {
    if (next) setDraft(value ?? "")
    setOpen(next)
  }

  const handleSave = async () => {
    if (!candidateId) {
      toast.error("ID do candidato indisponível")
      return
    }
    const trimmed = draft.trim()
    if (trimmed === (value ?? "")) {
      setOpen(false)
      return
    }
    if (kind === "email" && trimmed && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) {
      toast.error("Email inválido")
      return
    }
    setSaving(true)
    try {
      // F11 fix (2026-05-24): previous code hit Rails proxy
      // `/api/backend-proxy/candidates/{id}` which is offline in Replit dev
      // (Rails not running). Route via the canonical FastAPI chat-action
      // endpoint other inline edits use (header pencil, profile cards).
      // Backend honors ALLOWED_DIRECT_FIELDS allow-list (email + phone are in).
      const res = await fetch("/api/backend-proxy/chat/actions/candidate-field-update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_id: candidateId,
          fields: { [fieldName]: trimmed || null },
        }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        const msg = body?.errors?.[0]?.detail || body?.error || `Falha ao salvar (${res.status})`
        toast.error(msg)
        return
      }
      const data = await res.json().catch(() => ({})) as {
        data?: { results?: Array<{ status?: string; error?: string | null; message?: string }> }
      }
      const result = data?.data?.results?.[0]
      if (result && result.status !== "executed") {
        toast.error(result.message || result.error || `Falha ao salvar ${label.toLowerCase()}`)
        return
      }
      onSaved(trimmed)
      toast.success(`${label} atualizado`)
      setOpen(false)
    } catch {
      toast.error("Erro de rede ao salvar")
    } finally {
      setSaving(false)
    }
  }

  const hasValue = !!value && value.length > 0

  return (
    <div className="flex items-center gap-1 min-w-0 group">
      <Icon className="w-3 h-3 text-lia-text-tertiary flex-shrink-0" aria-hidden="true" />
      {hasValue ? (
        <a
          href={linkAction(value!)}
          target={kind === "phone" ? "_blank" : undefined}
          rel={kind === "phone" ? "noopener noreferrer" : undefined}
          className="text-micro text-lia-text-secondary hover:text-lia-text-primary hover:underline truncate"
          onClick={(e) => e.stopPropagation()}
          title={value}
        >
          {value}
        </a>
      ) : (
        <span className="text-micro text-lia-text-tertiary italic">
          Adicionar {label.toLowerCase()}
        </span>
      )}
      <Popover open={open} onOpenChange={handleOpenChange}>
        <PopoverTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className="h-4 w-4 p-0 opacity-60 hover:opacity-100 flex-shrink-0"
            aria-label={`Editar ${label.toLowerCase()}`}
          >
            <Pencil className="w-2.5 h-2.5 text-lia-text-tertiary" />
          </Button>
        </PopoverTrigger>
        <PopoverContent side="bottom" align="start" className="w-72 p-3 space-y-2">
          <label className="text-xs font-medium text-lia-text-primary block">
            {label}
          </label>
          <Input
            type={inputType}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder={placeholder}
            autoFocus
            disabled={saving}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault()
                handleSave()
              } else if (e.key === "Escape") {
                e.preventDefault()
                setOpen(false)
              }
            }}
          />
          <div className="flex items-center justify-end gap-2 pt-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setOpen(false)}
              disabled={saving}
              className="h-7 text-xs"
            >
              Cancelar
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleSave}
              disabled={saving}
              className="h-7 text-xs"
            >
              {saving ? <Loader2 className="w-3 h-3 animate-spin" /> : "Salvar"}
            </Button>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  )
}

interface CandidatePreviewHeaderProps {
  c: CandidateData
  candidate: Record<string, unknown>
  generateShortId: (name: string, id?: string) => string
  onOpenFullPage?: (candidate: Record<string, unknown>) => void
  onClose: () => void
  hasAudioConsent?: boolean
}

export function CandidatePreviewHeader({
  c,
  candidate,
  generateShortId,
  onOpenFullPage,
  onClose,
  hasAudioConsent,
}: CandidatePreviewHeaderProps) {
  const formatDate = (dateStr: string | Date | null | undefined): string =>
    formatDateUtil(dateStr, { day: '2-digit', month: 'short', year: 'numeric' })

  const lastContactedAt = c.last_contacted_at || c.lastContactedAt
  const updatedAt = c.updated_at || c.updatedAt
  const createdAt = c.created_at || c.createdAt

  const candidateRailsId =
    (c.id as string | undefined) ||
    (c.candidateId as string | undefined)

  const [emailLocal, setEmailLocal] = useState<string | undefined>(c.email)
  const [phoneLocal, setPhoneLocal] = useState<string | undefined>(c.phone)

  return (
    <>
      <div className="flex items-start gap-3 mb-1.5">
        <CandidateAvatar
          name={c.name as string}
          avatarUrl={(c.avatar_url as string | undefined) || (c.avatar as string | undefined) || (c.photo_url as string | undefined) || (c.photoUrl as string | undefined)}
          size="lg"
          showRing
        />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 mb-0.5 flex-wrap">
            <h3 className={`${textStyles.title} truncate`}>
              {c.name as string}
            </h3>
            {/* F11 Bug 3 (2026-05-24): header chips agora compartilham EXATAMENTE
                a mesma classe do LGPD chip (text-micro px-1.5 py-0 h-4 flex
                items-center). Removido `border border-lia-border-default` do ID
                chip (que adicionava 2px box-sizing) e previewChipVariants
                substituído por classe inline igual ao LGPD pattern. Cores
                preservadas via variant + bg override. */}
            <Chip variant="neutral" muted className="text-micro px-1.5 py-0 h-4 flex items-center flex-shrink-0 bg-lia-bg-tertiary text-lia-text-secondary">
              {generateShortId(c.name as string, (c.id as string | undefined) || (c.candidateId as string | undefined) || (c.pearch_id as string | undefined))}
            </Chip>
            {(c.seniority_level || c.seniorityLevel) && (
              <Chip variant="warning" muted className="text-micro px-1.5 py-0 h-4 flex items-center flex-shrink-0 bg-status-warning/10 text-status-warning">
                {(c.seniority_level as string | undefined) || (c.seniorityLevel as string | undefined)}
              </Chip>
            )}
            {(c.years_of_experience !== undefined && c.years_of_experience !== null) ||
             (c.years_of_experience !== undefined && c.years_of_experience !== null) ? (
              <Chip variant="neutral" muted className="text-micro px-1.5 py-0 h-4 flex items-center flex-shrink-0 bg-lia-bg-tertiary text-lia-text-secondary">
                {typeof (c.years_of_experience || c.yearsOfExperience) === 'number'
                  ? `${((c.years_of_experience as number | undefined) || (c.yearsOfExperience as number | undefined) || 0).toFixed(1)} anos`
                  : `${c.years_of_experience || c.yearsOfExperience} anos`}
              </Chip>
            ) : null}
            {(c.communication_consent !== undefined || c.communicationConsent !== undefined) && (
              <Chip variant="neutral" muted className={`text-micro px-1.5 py-0 h-4 flex items-center gap-0.5 ${(c.communication_consent ?? c.communicationConsent) ? '' : ''}`}>
                {(c.communication_consent ?? c.communicationConsent) ? <CheckCircle className="w-2.5 h-2.5" /> : <AlertCircle className="w-2.5 h-2.5" />}
                Consent. com.
              </Chip>
            )}
            {hasAudioConsent === true && (
              <Chip variant="success" muted className="text-micro px-1.5 py-0 h-4 flex items-center gap-0.5 bg-status-success/10 text-status-success">
                <CheckCircle className="w-2.5 h-2.5" />
                Consent. audio OK
              </Chip>
            )}
            {hasAudioConsent === false && (
              <Chip variant="neutral" muted className="text-micro px-1.5 py-0 h-4 flex items-center gap-0.5 bg-lia-bg-tertiary text-lia-text-secondary">
                <AlertCircle className="w-2.5 h-2.5" />
                Sem consent. audio
              </Chip>
            )}
            {c.is_enriching && (
              <Chip variant="warning" muted className="text-micro px-1.5 py-0 h-4 flex items-center gap-0.5 bg-status-warning/15 animate-pulse">
                Enriquecendo...
              </Chip>
            )}
            {c.enrichment_source && !c.is_enriching && (() => {
              const src = String(c.enrichment_source).toLowerCase()
              const config = src === 'apify'
                ? { label: 'Apify', cls: 'bg-wedo-orange/15 text-wedo-orange-text border-wedo-orange/30' }
                : src === 'pearch'
                  ? { label: 'Pearch', cls: 'bg-wedo-cyan/15 text-wedo-cyan-text border-wedo-cyan/30' }
                  : src === 'local'
                    ? { label: 'Local', cls: 'bg-stone-400/15 text-stone-500 border-stone-400/30' }
                    : { label: String(c.enrichment_source), cls: 'bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-default' }
              return (
                <Chip variant="neutral" muted className={`text-micro px-1.5 py-0 h-4 flex items-center ${config.cls}`}>
                  {config.label}
                </Chip>
              )
            })()}
          </div>

          <div className="flex items-center gap-1.5 flex-wrap">
            <p className={`${textStyles.bodySmall} truncate`}>
              {(c.position || c.title || 'Cargo não informado') as React.ReactNode}
            </p>
            <span className={`${textStyles.bodySmall} text-lia-text-secondary`}>•</span>
            <p className={`${textStyles.bodySmall} truncate`}>
              {(c.work_history as Array<Record<string, unknown>> | undefined)?.[0]?.company as React.ReactNode || c.current_company as React.ReactNode || c.company as React.ReactNode || 'Empresa'}
            </p>
            {((c.work_history as Array<Record<string, unknown>> | undefined)?.[0]?.industry || (c.work_history as Array<Record<string, unknown>> | undefined)?.[0]?.segment || c.company_segment || c.industry) && (
              <>
                <span className={`${textStyles.description} text-lia-text-secondary`}>•</span>
                <p className={`${textStyles.description} truncate`}>
                  {((c.work_history as Array<Record<string, unknown>> | undefined)?.[0]?.industry || (c.work_history as Array<Record<string, unknown>> | undefined)?.[0]?.segment || c.company_segment || c.industry) as React.ReactNode}
                </p>
              </>
            )}
          </div>

          <div className="flex items-center gap-3 mt-0.5 flex-wrap">
            <ContactField
              kind="email"
              value={emailLocal}
              candidateId={candidateRailsId}
              onSaved={setEmailLocal}
            />
            <ContactField
              kind="phone"
              value={phoneLocal}
              candidateId={candidateRailsId}
              onSaved={setPhoneLocal}
            />
          </div>
        </div>

        <div className="flex items-center gap-1 flex-shrink-0">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onOpenFullPage?.(candidate)}
                className="h-7 w-7 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
              >
                <Expand className="w-4 h-4 text-lia-text-tertiary" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="bottom" className="text-xs">Expandir</TooltipContent>
          </Tooltip>

          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="h-7 w-7 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
          >
            <X className="w-4 h-4 text-lia-text-tertiary" />
          </Button>
        </div>
      </div>

      {(() => {
        if (!createdAt && !updatedAt && !lastContactedAt) return null
        
        return (
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            {!!createdAt && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className="text-micro text-lia-text-secondary flex items-center gap-0.5 cursor-help">
                    <Calendar className="w-2.5 h-2.5" />
                    {String(formatDate(createdAt as string | Date | null | undefined) || '')}
                  </span>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Data de cadastro</TooltipContent>
              </Tooltip>
            )}
            {!!updatedAt && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className="text-micro text-lia-text-secondary flex items-center gap-0.5 cursor-help">
                    <Clock className="w-2.5 h-2.5" />
                    {String(formatDate(updatedAt as string | Date | null | undefined) || '')}
                  </span>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Última atualização</TooltipContent>
              </Tooltip>
            )}
            {!!lastContactedAt && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className="text-micro text-lia-text-tertiary flex items-center gap-0.5 cursor-help">
                    <MessageSquare className="w-2.5 h-2.5" />
                    {String(formatDate(lastContactedAt as string | Date | null | undefined) || '')}
                  </span>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Último contato</TooltipContent>
              </Tooltip>
            )}
          </div>
        )
      })()}
    </>
  )
}
