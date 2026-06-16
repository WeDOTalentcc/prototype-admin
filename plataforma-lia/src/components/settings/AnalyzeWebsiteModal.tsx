"use client"

/**
 * Task #1180 — Modal pré-análise (form-only).
 *
 * Captura nome + website + LinkedIn + checkbox "atualizar existentes" e
 * dispara `/company/culture-profile/analyze-direct`. O modal NÃO renderiza
 * o card de proposta: o caller recebe `proposed` via `onProposed` e o
 * injeta DENTRO do chat (`WebsiteProposalCard` em `UnifiedMessageList`).
 *
 * Quando aberto sem `initial.companyId`, o modal busca `/auth/me` +
 * `/company/profile/{id}` para pré-popular os 3 campos — cobre o
 * entrypoint do Onboarding (que não tem o contexto na mão).
 */

import React from "react"
import { Loader2, Globe, AlertCircle, X } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import {
  mapExtractedToProposedSaves,
  type ExistingBasic,
  type ProposedSaves,
} from "@/lib/website-proposal-mapper"

export interface AnalyzeWebsiteInitialValues {
  companyName?: string
  websiteUrl?: string
  linkedinUrl?: string
  companyId?: string
  existingBasic?: ExistingBasic
}

interface AnalyzeWebsiteModalProps {
  open: boolean
  onClose: () => void
  initial: AnalyzeWebsiteInitialValues
  /** Caller injeta o card no chat com este payload + companyId. */
  onProposed: (info: { proposed: ProposedSaves; companyId: string }) => void
}

type Stage = "form" | "analyzing" | "error"

const URL_RX = /^https?:\/\/[^\s]+\.[^\s]+/i

function isValidUrl(u: string): boolean {
  return URL_RX.test(u.trim())
}

function normalizeUrl(u: string): string {
  const t = u.trim()
  if (!t) return ""
  if (/^https?:\/\//i.test(t)) return t
  return `https://${t}`
}

export function AnalyzeWebsiteModal({
  open,
  onClose,
  initial,
  onProposed,
}: AnalyzeWebsiteModalProps) {
  const [stage, setStage] = React.useState<Stage>("form")
  const [companyName, setCompanyName] = React.useState(initial.companyName ?? "")
  const [websiteUrl, setWebsiteUrl] = React.useState(initial.websiteUrl ?? "")
  const [linkedinUrl, setLinkedinUrl] = React.useState(initial.linkedinUrl ?? "")
  const [updateExisting, setUpdateExisting] = React.useState(false)
  const [errorMsg, setErrorMsg] = React.useState<string | null>(null)
  const [companyId, setCompanyId] = React.useState<string | undefined>(initial.companyId)
  const [existingBasic, setExistingBasic] = React.useState<ExistingBasic | undefined>(
    initial.existingBasic,
  )
  const [prefilling, setPrefilling] = React.useState(false)

  // Reset interno quando o modal abre.
  React.useEffect(() => {
    if (!open) return
    setStage("form")
    setCompanyName(initial.companyName ?? "")
    setWebsiteUrl(initial.websiteUrl ?? "")
    setLinkedinUrl(initial.linkedinUrl ?? "")
    setUpdateExisting(false)
    setErrorMsg(null)
    setCompanyId(initial.companyId)
    setExistingBasic(initial.existingBasic)
  }, [open, initial.companyName, initial.websiteUrl, initial.linkedinUrl, initial.companyId, initial.existingBasic])

  // Auto-prefill: quando o caller não passa companyId/companyName (entrypoint
  // do Onboarding), busca /auth/me + /company/profile/{id}.
  React.useEffect(() => {
    if (!open) return
    if (initial.companyName || initial.companyId) return
    let cancelled = false
    ;(async () => {
      try {
        setPrefilling(true)
        const meRes = await fetch("/api/backend-proxy/auth/me")
        if (!meRes.ok) return
        const me = (await meRes.json()) as { company_id?: string }
        const cid = me.company_id
        if (!cid || cancelled) return
        const profRes = await fetch(`/api/backend-proxy/company/profile/${encodeURIComponent(cid)}`)
        if (!profRes.ok) {
          if (!cancelled) setCompanyId(cid)
          return
        }
        const prof = (await profRes.json()) as Record<string, unknown>
        if (cancelled) return
        setCompanyId(cid)
        if (!companyName && typeof prof.name === "string") setCompanyName(prof.name)
        if (!websiteUrl && typeof prof.website === "string") setWebsiteUrl(prof.website)
        if (!linkedinUrl && typeof prof.linkedin_url === "string")
          setLinkedinUrl(prof.linkedin_url)
        setExistingBasic({
          industry: prof.industry as string | undefined,
          employee_count: prof.employee_count as number | string | undefined,
          company_size: prof.company_size as string | undefined,
          headquarters_city: prof.headquarters_city as string | undefined,
          headquarters_state: prof.headquarters_state as string | undefined,
          founded_year: prof.founded_year as number | string | undefined,
          work_model: prof.work_model as string | undefined,
          linkedin_url: prof.linkedin_url as string | undefined,
          logo_url: prof.logo_url as string | undefined,
        })
      } catch {
        // best-effort
      } finally {
        if (!cancelled) setPrefilling(false)
      }
    })()
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  const formValid = React.useMemo(
    () => companyName.trim().length > 1 && isValidUrl(normalizeUrl(websiteUrl)),
    [companyName, websiteUrl],
  )

  const handleAnalyze = async () => {
    setErrorMsg(null)
    const wsUrl = normalizeUrl(websiteUrl)
    if (!formValid) {
      setErrorMsg("Preencha o nome da empresa e uma URL válida.")
      return
    }
    if (!companyId) {
      setErrorMsg("Não foi possível identificar a empresa. Recarregue a página.")
      return
    }
    setStage("analyzing")

    // Persistência pré-análise dos 3 campos editados (best-effort).
    try {
      const patch: Record<string, unknown> = {}
      if (companyName && companyName !== initial.companyName) patch.name = companyName.trim()
      if (wsUrl && wsUrl !== initial.websiteUrl) patch.website = wsUrl
      if (linkedinUrl && linkedinUrl !== initial.linkedinUrl)
        patch.linkedin_url = linkedinUrl.trim()
      if (Object.keys(patch).length > 0) {
        await fetch(`/api/backend-proxy/company/profile/${encodeURIComponent(companyId)}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(patch),
        })
      }
    } catch {
      // Não bloqueia a análise.
    }

    try {
      const res = await fetch("/api/backend-proxy/company/culture-profile/analyze-direct", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          website_url: wsUrl,
          linkedin_url: linkedinUrl.trim() || undefined,
          company_id: companyId,
        }),
      })
      if (!res.ok) {
        const detail = await res.text().catch(() => "")
        throw new Error(`Falha na análise (HTTP ${res.status}). ${detail.slice(0, 160)}`)
      }
      const extracted = (await res.json()) as Record<string, unknown>
      const mapped = mapExtractedToProposedSaves(extracted, {
        existingBasic,
        updateExisting,
      })
      onProposed({ proposed: mapped, companyId })
      onClose()
    } catch (err) {
      setStage("error")
      setErrorMsg(err instanceof Error ? err.message : "Erro desconhecido na análise.")
    }
  }

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent
        className="max-w-[520px] sm:max-w-[560px] rounded-md p-0 overflow-hidden"
        data-testid="analyze-website-modal"
      >
        <DialogHeader className="px-5 pt-5 pb-3 border-b border-lia-border-subtle">
          <DialogTitle className="text-base font-semibold flex items-center gap-2">
            <Globe className="w-4 h-4 text-wedo-cyan" />
            Analisar nosso site
          </DialogTitle>
          <DialogDescription className="text-xs text-lia-text-tertiary">
            A LIA lê o site institucional e devolve uma proposta de campos no
            chat. Você revisa, edita e escolhe o que salvar.
          </DialogDescription>
        </DialogHeader>

        <div className="px-5 py-4 max-h-[60vh] overflow-y-auto">
          <div className="space-y-3">
            <label className="block text-xs text-lia-text-secondary">
              Nome da empresa <span className="text-status-error">*</span>
              <Input
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="Ex.: Acme Corp"
                className="mt-1"
                disabled={stage === "analyzing" || prefilling}
                data-testid="analyze-website-name"
              />
            </label>
            <label className="block text-xs text-lia-text-secondary">
              Website <span className="text-status-error">*</span>
              <Input
                value={websiteUrl}
                onChange={(e) => setWebsiteUrl(e.target.value)}
                placeholder="https://acme.com.br"
                className="mt-1"
                disabled={stage === "analyzing" || prefilling}
                data-testid="analyze-website-url"
              />
            </label>
            <label className="block text-xs text-lia-text-secondary">
              LinkedIn (opcional)
              <Input
                value={linkedinUrl}
                onChange={(e) => setLinkedinUrl(e.target.value)}
                placeholder="https://linkedin.com/company/acme"
                className="mt-1"
                disabled={stage === "analyzing" || prefilling}
                data-testid="analyze-website-linkedin"
              />
            </label>
            <label className="flex items-center gap-2 text-xs text-lia-text-secondary pt-1">
              <Checkbox
                checked={updateExisting}
                onCheckedChange={(v) => setUpdateExisting(v === true)}
                data-testid="analyze-website-update-existing"
              />
              Atualizar campos já preenchidos
            </label>
            {prefilling && (
              <div className="flex items-center gap-2 text-xs text-lia-text-tertiary pt-1">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Carregando dados da empresa...
              </div>
            )}
            {errorMsg && (
              <div className="flex items-start gap-2 px-3 py-2 rounded-md bg-status-error/10 text-status-error text-xs border border-status-error/30">
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>{errorMsg}</span>
              </div>
            )}
            {stage === "analyzing" && (
              <div className="flex items-center gap-2 text-xs text-lia-text-tertiary pt-1">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Lendo o site e o LinkedIn (pode levar 30-60s)...
              </div>
            )}
          </div>
        </div>

        <div className="flex justify-end gap-2 px-5 py-3 border-t border-lia-border-subtle bg-lia-bg-secondary/30">
          {stage !== "analyzing" ? (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                data-testid="analyze-website-cancel"
              >
                <X className="w-3.5 h-3.5 mr-1" />
                Cancelar
              </Button>
              <Button
                size="sm"
                onClick={handleAnalyze}
                disabled={!formValid || prefilling}
                data-testid="analyze-website-submit"
              >
                Analisar
              </Button>
            </>
          ) : (
            <Button size="sm" disabled>
              <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" />
              Analisando...
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
