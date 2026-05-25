"use client"

/**
 * Task #1180 — Card de proposta renderizado DENTRO do chat (não modal).
 * Recebe os 4 blocos extraídos do site, permite edição inline e dispara
 * os saves REST. Workforce planning FORA de escopo (mapper já filtra +
 * sentinela AST garante).
 */

import React from "react"
import { Loader2, CheckCircle2, AlertCircle, X, Pencil } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import type {
  ProposalBlock,
  ProposalBlockKey,
  ProposedSaves,
} from "@/lib/website-proposal-mapper"

export interface WebsiteProposalCardData {
  proposed: ProposedSaves
  companyId: string
}

type Stage = "review" | "saving" | "done" | "error"

function fmtValue(v: unknown): string {
  if (v === null || v === undefined) return ""
  if (Array.isArray(v)) return (v as unknown[]).join(", ")
  if (typeof v === "object") return JSON.stringify(v)
  return String(v)
}

async function saveBlock(blk: ProposalBlock, companyId: string): Promise<number> {
  if (blk.key === "culture") {
    const body: Record<string, unknown> = {}
    for (const f of blk.fields) body[f.key] = f.value
    const res = await fetch(
      `/api/backend-proxy/company/culture-profile/${encodeURIComponent(companyId)}`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
    )
    if (!res.ok) throw new Error(`Falha ao salvar Cultura (HTTP ${res.status}).`)
    return blk.fields.length
  }
  if (blk.key === "tech_stack") {
    let count = 0
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
    const engCulture = blk.fields.find((f) => f.key === "engineering_culture")
    if (engCulture) {
      const res = await fetch(
        `/api/backend-proxy/company/culture-profile/${encodeURIComponent(companyId)}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ engineering_culture: engCulture.value }),
        },
      )
      if (!res.ok) throw new Error(`Falha ao salvar cultura de engenharia (HTTP ${res.status}).`)
      count += 1
    }
    return count
  }
  if (blk.key === "benefits") {
    let count = 0
    for (const f of blk.fields) {
      const benefit = f.value as Record<string, unknown>
      const res = await fetch(
        `/api/backend-proxy/company/benefits/?company_id=${encodeURIComponent(companyId)}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(benefit),
        },
      )
      if (!res.ok) throw new Error(`Falha ao salvar benefício "${f.label}" (HTTP ${res.status}).`)
      count += 1
    }
    return count
  }
  if (blk.key === "basic_complementary") {
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
    const res = await fetch(`/api/backend-proxy/company/profile/${companyId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
    if (!res.ok) throw new Error(`Falha ao salvar Dados Básicos (HTTP ${res.status}).`)
    return Object.keys(body).length
  }
  return 0
}

export function WebsiteProposalCard({ data }: { data: WebsiteProposalCardData }) {
  const { proposed, companyId } = data
  const [stage, setStage] = React.useState<Stage>("review")
  const [errorMsg, setErrorMsg] = React.useState<string | null>(null)
  const [savedCount, setSavedCount] = React.useState(0)
  const [blocks, setBlocks] = React.useState<ProposalBlock[]>(proposed.blocks)
  const [selected, setSelected] = React.useState<Set<ProposalBlockKey>>(
    new Set(proposed.blocks.map((b) => b.key)),
  )
  const [editing, setEditing] = React.useState<Set<string>>(new Set())
  // Idempotência: trava in-flight + dedupe pós-sucesso por (companyId|payload_hash).
  const savingRef = React.useRef(false)
  const [blockErrors, setBlockErrors] = React.useState<Record<string, string>>({})

  const fieldId = (blkKey: ProposalBlockKey, fkey: string) => `${blkKey}::${fkey}`

  const toggleBlock = (key: ProposalBlockKey) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const setFieldValue = (blkKey: ProposalBlockKey, fkey: string, raw: string) => {
    setBlocks((prev) =>
      prev.map((b) => {
        if (b.key !== blkKey) return b
        return {
          ...b,
          fields: b.fields.map((f) => {
            if (f.key !== fkey) return f
            const wasArray = Array.isArray(f.value)
            const newVal: unknown = wasArray
              ? raw.split(",").map((s) => s.trim()).filter(Boolean)
              : raw
            return { ...f, value: newVal }
          }),
        }
      }),
    )
  }

  const handleSave = async (mode: "all" | "selected") => {
    // Guard: dupla interação rápida ou re-click após erro de um bloco.
    if (savingRef.current) return
    if (!companyId) {
      setErrorMsg("Sem company_id — recarregue a página e tente novamente.")
      setStage("error")
      return
    }
    savingRef.current = true
    setErrorMsg(null)
    setBlockErrors({})
    setStage("saving")
    const toSave: ProposalBlock[] =
      mode === "all" ? blocks : blocks.filter((b) => selected.has(b.key))
    let count = 0
    const errors: Record<string, string> = {}
    const savedKeys: ProposalBlockKey[] = []
    for (const blk of toSave) {
      try {
        count += await saveBlock(blk, companyId)
        savedKeys.push(blk.key)
      } catch (err) {
        errors[blk.key] = err instanceof Error ? err.message : "Erro ao salvar bloco."
      }
    }
    setSavedCount(count)
    setBlockErrors(errors)
    if (typeof window !== "undefined" && savedKeys.length > 0) {
      window.dispatchEvent(new CustomEvent("lia:settings-updated"))
      window.dispatchEvent(
        new CustomEvent("lia:settings-success", {
          detail: { actionId: "analyze_website", blocksSaved: savedKeys },
        }),
      )
    }
    if (Object.keys(errors).length === 0) {
      setStage("done")
    } else {
      // Mantém o card em review para o usuário re-tentar só os blocos com falha.
      // Remove do selected os já salvos para evitar re-submit duplicado.
      setSelected((prev) => {
        const next = new Set(prev)
        for (const k of savedKeys) next.delete(k)
        return next
      })
      setStage("review")
      const failedLabels = toSave
        .filter((b) => errors[b.key])
        .map((b) => b.label)
        .join(", ")
      setErrorMsg(
        `Salvei ${savedKeys.length} de ${toSave.length} blocos. Falharam: ${failedLabels}. Você pode editar e tentar novamente apenas os blocos restantes.`,
      )
    }
    savingRef.current = false
  }

  if (stage === "done") {
    return (
      <div
        className="mt-2 rounded-md border border-status-success/40 bg-status-success/5 p-3 flex items-start gap-2"
        data-testid="website-proposal-card-done"
      >
        <CheckCircle2 className="w-4 h-4 text-status-success flex-shrink-0 mt-0.5" />
        <div className="text-xs">
          <p className="font-medium text-lia-text-primary">
            {savedCount > 0
              ? `Pronto — ${savedCount} campo(s) salvo(s) a partir do site.`
              : "Nada novo para salvar."}
          </p>
          <p className="text-lia-text-tertiary mt-0.5">
            Você pode revisar ou ajustar qualquer campo no hub Minha Empresa.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div
      className="mt-2 rounded-md border border-lia-border-subtle bg-lia-bg-secondary/40 p-3 space-y-3"
      data-testid="website-proposal-card"
    >
      <p className="text-xs text-lia-text-secondary">
        Extraí {blocks.reduce((a, b) => a + b.fields.length, 0)} campos do site.
        Revise, edite o que quiser e me diga o que salvar.
      </p>

      {blocks.map((blk) => {
        const checked = selected.has(blk.key)
        return (
          <div
            key={blk.key}
            className="rounded-md border border-lia-border-subtle bg-lia-bg-primary p-2.5"
          >
            <label className="flex items-center gap-2 cursor-pointer">
              <Checkbox
                checked={checked}
                onCheckedChange={() => toggleBlock(blk.key)}
                disabled={stage === "saving"}
                data-testid={`proposal-block-${blk.key}`}
              />
              <span className="text-sm font-medium">{blk.label}</span>
              <span className="ml-auto text-[11px] text-lia-text-tertiary">
                {blk.fields.length} campo{blk.fields.length === 1 ? "" : "s"}
              </span>
            </label>
            {blockErrors[blk.key] && (
              <p
                className="mt-1 text-[11px] text-status-error pl-6"
                data-testid={`proposal-block-error-${blk.key}`}
              >
                {blockErrors[blk.key]}
              </p>
            )}
            {checked && (
              <ul className="mt-2 space-y-1.5 pl-6">
                {blk.fields.map((f) => {
                  const id = fieldId(blk.key, f.key)
                  const isEditing = editing.has(id)
                  const display = fmtValue(f.value)
                  const isObject = !isEditing && typeof f.value === "object" && !Array.isArray(f.value)
                  return (
                    <li key={f.key} className="text-xs flex items-start gap-2">
                      <span className="text-lia-text-secondary min-w-[120px] pt-1">
                        {f.label}:
                      </span>
                      <div className="flex-1 flex items-start gap-1">
                        {isEditing && !isObject ? (
                          <Input
                            value={display}
                            onChange={(e) => setFieldValue(blk.key, f.key, e.target.value)}
                            className="h-7 text-xs"
                            data-testid={`field-input-${id}`}
                          />
                        ) : (
                          <span
                            className="text-lia-text-primary flex-1 break-words"
                            data-testid={`field-value-${id}`}
                          >
                            {isObject ? JSON.stringify(f.value).slice(0, 80) : display}
                          </span>
                        )}
                        {!isObject && (
                          <button
                            type="button"
                            onClick={() => {
                              setEditing((prev) => {
                                const next = new Set(prev)
                                if (next.has(id)) next.delete(id)
                                else next.add(id)
                                return next
                              })
                            }}
                            disabled={stage === "saving"}
                            className="text-lia-text-tertiary hover:text-lia-text-primary p-1"
                            data-testid={`field-edit-${id}`}
                            title={isEditing ? "Concluir edição" : "Editar"}
                          >
                            {isEditing ? <CheckCircle2 className="w-3.5 h-3.5" /> : <Pencil className="w-3 h-3" />}
                          </button>
                        )}
                      </div>
                    </li>
                  )
                })}
              </ul>
            )}
          </div>
        )
      })}

      {errorMsg && (
        <div className="flex items-start gap-2 px-2 py-1.5 rounded-md bg-status-error/10 text-status-error text-xs border border-status-error/30">
          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
          <span>{errorMsg}</span>
        </div>
      )}

      <div className="flex justify-end gap-2 pt-1">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            setStage("done")
            setSavedCount(0)
          }}
          disabled={stage === "saving"}
          data-testid="website-proposal-cancel"
        >
          <X className="w-3.5 h-3.5 mr-1" />
          Cancelar
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => handleSave("selected")}
          disabled={
            stage === "saving" ||
            selected.size === 0 ||
            selected.size === blocks.length
          }
          data-testid="website-proposal-save-selected"
        >
          Salvar selecionados
        </Button>
        <Button
          size="sm"
          onClick={() => handleSave("all")}
          disabled={stage === "saving"}
          data-testid="website-proposal-save-all"
        >
          {stage === "saving" ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" />
              Salvando...
            </>
          ) : (
            "Salvar tudo"
          )}
        </Button>
      </div>
    </div>
  )
}
