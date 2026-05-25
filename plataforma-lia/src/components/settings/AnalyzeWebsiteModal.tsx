"use client"

import React from "react"
import { Loader2, Globe, AlertCircle, CheckCircle2, X } from "lucide-react"
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
  type ProposalBlock,
  type ProposalBlockKey,
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
  /** Callback após save bem-sucedido — DashboardApp pode postar msg no chat. */
  onApplied?: (info: { blocksSaved: ProposalBlockKey[]; payloadHash: string }) => void
}

type Stage = "form" | "analyzing" | "review" | "saving" | "done" | "error"

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
  onApplied,
}: AnalyzeWebsiteModalProps) {
  const [stage, setStage] = React.useState<Stage>("form")
  const [companyName, setCompanyName] = React.useState(initial.companyName ?? "")
  const [websiteUrl, setWebsiteUrl] = React.useState(initial.websiteUrl ?? "")
  const [linkedinUrl, setLinkedinUrl] = React.useState(initial.linkedinUrl ?? "")
  const [updateExisting, setUpdateExisting] = React.useState(false)
  const [errorMsg, setErrorMsg] = React.useState<string | null>(null)
  const [proposed, setProposed] = React.useState<ProposedSaves | null>(null)
  const [selectedBlocks, setSelectedBlocks] = React.useState<Set<ProposalBlockKey>>(new Set())
  const [savedCount, setSavedCount] = React.useState(0)

  // Reset interno quando o modal abre.
  React.useEffect(() => {
    if (!open) return
    setStage("form")
    setCompanyName(initial.companyName ?? "")
    setWebsiteUrl(initial.websiteUrl ?? "")
    setLinkedinUrl(initial.linkedinUrl ?? "")
    setUpdateExisting(false)
    setErrorMsg(null)
    setProposed(null)
    setSelectedBlocks(new Set())
    setSavedCount(0)
  }, [open, initial.companyName, initial.websiteUrl, initial.linkedinUrl])

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
    setStage("analyzing")

    // Persistência pré-análise dos campos editados (best-effort).
    if (initial.companyId) {
      try {
        const patch: Record<string, unknown> = {}
        if (companyName && companyName !== initial.companyName) patch.name = companyName.trim()
        if (wsUrl && wsUrl !== initial.websiteUrl) patch.website = wsUrl
        if (linkedinUrl && linkedinUrl !== initial.linkedinUrl) patch.linkedin_url = linkedinUrl.trim()
        if (Object.keys(patch).length > 0) {
          await fetch(`/api/backend-proxy/company/profile/${initial.companyId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(patch),
          })
        }
      } catch {
        // Não bloqueia a análise — só avisa.
      }
    }

    try {
      const res = await fetch("/api/backend-proxy/company/culture-profile/analyze-direct", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          website_url: wsUrl,
          linkedin_url: linkedinUrl.trim() || undefined,
          company_id: initial.companyId,
        }),
      })
      if (!res.ok) {
        const detail = await res.text().catch(() => "")
        throw new Error(`Falha na análise (HTTP ${res.status}). ${detail.slice(0, 160)}`)
      }
      const extracted = (await res.json()) as Record<string, unknown>
      const mapped = mapExtractedToProposedSaves(extracted, {
        existingBasic: initial.existingBasic,
        updateExisting,
      })
      setProposed(mapped)
      setSelectedBlocks(new Set(mapped.blocks.map((b) => b.key)))
      if (mapped.blocks.length === 0) {
        setStage("done")
        setSavedCount(0)
      } else {
        setStage("review")
      }
    } catch (err) {
      setStage("error")
      setErrorMsg(err instanceof Error ? err.message : "Erro desconhecido na análise.")
    }
  }

  const toggleBlock = (key: ProposalBlockKey) => {
    setSelectedBlocks((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const handleSave = async (mode: "all" | "selected") => {
    if (!proposed || !initial.companyId) return
    setErrorMsg(null)
    setStage("saving")
    const toSave: ProposalBlock[] =
      mode === "all"
        ? proposed.blocks
        : proposed.blocks.filter((b) => selectedBlocks.has(b.key))
    let count = 0
    try {
      for (const blk of toSave) {
        if (blk.key === "culture") {
          const body: Record<string, unknown> = {}
          for (const f of blk.fields) body[f.key] = f.value
          const res = await fetch(
            `/api/backend-proxy/company/culture-profile/${encodeURIComponent(initial.companyId)}`,
            {
              method: "PUT",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(body),
            },
          )
          if (!res.ok) throw new Error(`Falha ao salvar Cultura (HTTP ${res.status}).`)
          count += blk.fields.length
        } else if (blk.key === "tech_stack") {
          const techField = blk.fields.find((f) => f.key === "tech_stack")
          if (techField && Array.isArray(techField.value)) {
            const res = await fetch(
              "/api/backend-proxy/skills-catalog/company/skills-catalog/sync",
              {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ tech_stack: techField.value }),
              },
            )
            if (!res.ok) throw new Error(`Falha ao salvar Tech Stack (HTTP ${res.status}).`)
            count += 1
          }
          const engCultureField = blk.fields.find((f) => f.key === "engineering_culture")
          if (engCultureField) {
            const res = await fetch(
              `/api/backend-proxy/company/culture-profile/${encodeURIComponent(initial.companyId)}`,
              {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ engineering_culture: engCultureField.value }),
              },
            )
            if (!res.ok) throw new Error(`Falha ao salvar cultura de engenharia (HTTP ${res.status}).`)
            count += 1
          }
        } else if (blk.key === "benefits") {
          for (const f of blk.fields) {
            const benefit = f.value as Record<string, unknown>
            const res = await fetch(
              `/api/backend-proxy/company/benefits/?company_id=${encodeURIComponent(initial.companyId)}`,
              {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(benefit),
              },
            )
            if (!res.ok) throw new Error(`Falha ao salvar benefício "${f.label}" (HTTP ${res.status}).`)
            count += 1
          }
        } else if (blk.key === "basic_complementary") {
          const body: Record<string, unknown> = {}
          for (const f of blk.fields) {
            if (f.key === "headquarters" && typeof f.value === "string") {
              const lastComma = f.value.lastIndexOf(",")
              if (lastComma === -1) {
                body.headquarters_city = f.value
              } else {
                body.headquarters_city = f.value.slice(0, lastComma).trim()
                body.headquarters_state = f.value.slice(lastComma + 1).trim()
              }
            } else {
              body[f.key] = f.value
            }
          }
          const res = await fetch(`/api/backend-proxy/company/profile/${initial.companyId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
          })
          if (!res.ok) throw new Error(`Falha ao salvar Dados Básicos (HTTP ${res.status}).`)
          count += Object.keys(body).length
        }
      }

      setSavedCount(count)
      setStage("done")
      // Notifica os cards de Minha Empresa para re-fetch.
      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent("lia:settings-updated"))
      }
      onApplied?.({
        blocksSaved: toSave.map((b) => b.key),
        payloadHash: proposed.payload_hash,
      })
    } catch (err) {
      setStage("error")
      setErrorMsg(err instanceof Error ? err.message : "Erro ao salvar.")
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
            A LIA lê o site institucional e sugere campos para o perfil da empresa.
            Você revisa antes de salvar.
          </DialogDescription>
        </DialogHeader>

        <div className="px-5 py-4 max-h-[60vh] overflow-y-auto">
          {(stage === "form" || stage === "analyzing") && (
            <div className="space-y-3">
              <label className="block text-xs text-lia-text-secondary">
                Nome da empresa <span className="text-status-error">*</span>
                <Input
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="Ex.: Acme Corp"
                  className="mt-1"
                  disabled={stage === "analyzing"}
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
                  disabled={stage === "analyzing"}
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
                  disabled={stage === "analyzing"}
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
          )}

          {(stage === "review" || stage === "saving") && proposed && (
            <div className="space-y-3" data-testid="analyze-website-proposal">
              <p className="text-xs text-lia-text-secondary">
                A LIA extraiu {proposed.blocks.reduce((a, b) => a + b.fields.length, 0)} campos
                organizados em {proposed.blocks.length} bloco(s). Desmarque blocos que não
                quiser salvar agora.
              </p>
              {proposed.blocks.map((blk) => {
                const checked = selectedBlocks.has(blk.key)
                return (
                  <div
                    key={blk.key}
                    className="rounded-md border border-lia-border-subtle bg-lia-bg-secondary/40 p-3"
                  >
                    <label className="flex items-center gap-2 cursor-pointer">
                      <Checkbox
                        checked={checked}
                        onCheckedChange={() => toggleBlock(blk.key)}
                        disabled={stage === "saving"}
                        data-testid={`proposal-block-${blk.key}`}
                      />
                      <span className="text-sm font-medium">{blk.label}</span>
                      <span className="ml-auto text-micro text-lia-text-tertiary">
                        {blk.fields.length} campo{blk.fields.length === 1 ? "" : "s"}
                      </span>
                    </label>
                    {checked && (
                      <ul className="mt-2 space-y-1 pl-6">
                        {blk.fields.map((f) => (
                          <li key={f.key} className="text-xs text-lia-text-tertiary flex gap-2">
                            <span className="text-lia-text-secondary min-w-[120px]">{f.label}:</span>
                            <span className="text-lia-text-primary truncate flex-1">
                              {Array.isArray(f.value)
                                ? (f.value as unknown[]).slice(0, 8).join(", ") +
                                  ((f.value as unknown[]).length > 8 ? "…" : "")
                                : typeof f.value === "object"
                                  ? JSON.stringify(f.value).slice(0, 80)
                                  : String(f.value ?? "")}
                            </span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )
              })}
              {errorMsg && (
                <div className="flex items-start gap-2 px-3 py-2 rounded-md bg-status-error/10 text-status-error text-xs border border-status-error/30">
                  <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <span>{errorMsg}</span>
                </div>
              )}
              {stage === "saving" && (
                <div className="flex items-center gap-2 text-xs text-lia-text-tertiary">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Salvando...
                </div>
              )}
            </div>
          )}

          {stage === "done" && (
            <div className="flex flex-col items-center gap-2 py-6 text-center">
              <CheckCircle2 className="w-8 h-8 text-status-success" />
              <p className="text-sm font-medium">
                {savedCount > 0
                  ? `Pronto! ${savedCount} campo(s) salvo(s) a partir do site.`
                  : "Análise concluída — não havia campos novos para salvar."}
              </p>
              <p className="text-xs text-lia-text-tertiary">
                Você pode editar qualquer campo individualmente no hub Minha Empresa.
              </p>
            </div>
          )}

          {stage === "error" && (
            <div className="flex flex-col items-center gap-2 py-6 text-center">
              <X className="w-8 h-8 text-status-error" />
              <p className="text-sm font-medium">Não foi possível concluir</p>
              <p className="text-xs text-lia-text-tertiary">
                {errorMsg ?? "Erro desconhecido."}
              </p>
            </div>
          )}
        </div>

        <div className="flex justify-end gap-2 px-5 py-3 border-t border-lia-border-subtle bg-lia-bg-secondary/30">
          {stage === "form" && (
            <>
              <Button variant="ghost" size="sm" onClick={onClose} data-testid="analyze-website-cancel">
                Cancelar
              </Button>
              <Button
                size="sm"
                onClick={handleAnalyze}
                disabled={!formValid}
                data-testid="analyze-website-submit"
              >
                Analisar
              </Button>
            </>
          )}
          {stage === "analyzing" && (
            <Button size="sm" disabled>
              <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" />
              Analisando...
            </Button>
          )}
          {stage === "review" && (
            <>
              <Button variant="ghost" size="sm" onClick={onClose}>
                Cancelar
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleSave("selected")}
                disabled={selectedBlocks.size === 0 || selectedBlocks.size === proposed?.blocks.length}
                data-testid="analyze-website-save-selected"
              >
                Salvar selecionados
              </Button>
              <Button
                size="sm"
                onClick={() => handleSave("all")}
                data-testid="analyze-website-save-all"
              >
                Salvar tudo
              </Button>
            </>
          )}
          {stage === "saving" && (
            <Button size="sm" disabled>
              <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" />
              Salvando...
            </Button>
          )}
          {(stage === "done" || stage === "error") && (
            <Button size="sm" onClick={onClose} data-testid="analyze-website-close">
              Fechar
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
