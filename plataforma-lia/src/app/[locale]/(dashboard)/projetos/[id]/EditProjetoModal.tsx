"use client"

import React, { useState, useEffect } from "react"
import { Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { type CampaignItem } from "@/hooks/jobs/useCampaignsList"
import { useAiPersona } from "@/hooks/company/use-ai-persona"

interface Props {
  project: CampaignItem
  open: boolean
  onClose: () => void
  onSaved: (updated: CampaignItem) => void
}

const AUTOMATION_OPTIONS = [
  { key: "manual" as const, label: "Sugerir", desc: "__PERSONA__ sugere — você decide" },
  { key: "semi" as const, label: "Rascunhar", desc: "__PERSONA__ prepara para aprovação" },
  { key: "full" as const, label: "Executar", desc: "__PERSONA__ executa automaticamente" },
]

export function EditProjetoModal({ project, open, onClose, onSaved }: Props) {
  const { persona } = useAiPersona()
  const personaName = persona?.name ?? "IA"
  const [name, setName] = useState(project.name)
  const [description, setDescription] = useState(project.description ?? "")
  const [automationLevel, setAutomationLevel] = useState(project.automation_level)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      setName(project.name)
      setDescription(project.description ?? "")
      setAutomationLevel(project.automation_level)
      setError(null)
    }
  }, [open, project])

  async function handleSave() {
    if (!name.trim()) return
    setSubmitting(true)
    setError(null)
    try {
      const res = await fetch(`/api/backend-proxy/recruitment-campaigns/${project.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.trim(),
          description: description.trim() || null,
          automation_level: automationLevel,
        }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body?.detail ?? "Erro ao salvar projeto")
      }
      const json = await res.json()
      const updated: CampaignItem = ("ok" in json ? json.data : json) as CampaignItem
      onSaved(updated)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro inesperado")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-2xl bg-lia-bg-primary border border-lia-border-medium shadow-lia-lg rounded-xl p-6">
        <DialogHeader>
          <DialogTitle className="text-base font-semibold text-lia-text-primary">
            Editar projeto
          </DialogTitle>
          <DialogDescription className="text-xs text-lia-text-muted">
            Altere nome, descrição ou nível de automação.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="space-y-1.5">
            <label className="text-small font-medium text-lia-text-primary">Nome</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2.5 rounded-md border border-lia-border-subtle bg-lia-bg-paper text-body text-lia-text-primary placeholder:text-lia-text-tertiary focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/30"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-small font-medium text-lia-text-primary">
              Descrição <span className="text-lia-text-tertiary font-normal">(opcional)</span>
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              placeholder="Contexto, objetivo, critérios..."
              className="w-full px-3 py-2 rounded-md border border-lia-border-subtle bg-lia-bg-paper text-small text-lia-text-primary placeholder:text-lia-text-tertiary focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/30 resize-none"
            />
          </div>

          <div className="space-y-2">
            <label className="text-small font-medium text-lia-text-primary">Nível de automação</label>
            <div className="grid grid-cols-3 gap-2">
              {AUTOMATION_OPTIONS.map(({ key, label, desc }) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => setAutomationLevel(key)}
                  className={[
                    "flex flex-col items-start gap-0.5 p-3 rounded-md border-2 text-left transition-colors",
                    automationLevel === key
                      ? "border-lia-btn-primary-bg bg-lia-btn-primary-bg/10"
                      : "border-lia-border-subtle bg-lia-bg-paper hover:border-lia-border",
                  ].join(" ")}
                >
                  <span className={[
                    "text-small font-semibold",
                    automationLevel === key ? "text-lia-btn-primary-bg" : "text-lia-text-primary",
                  ].join(" ")}>
                    {label}
                  </span>
                  <span className="text-micro text-lia-text-tertiary leading-snug">{desc.replace("__PERSONA__", personaName)}</span>
                </button>
              ))}
            </div>
          </div>

          {error && <p className="text-small text-lia-text-error">{error}</p>}
        </div>

        <DialogFooter className="flex items-center justify-end gap-2">
          <Button variant="outline" onClick={onClose} disabled={submitting}>
            Cancelar
          </Button>
          <Button
            onClick={handleSave}
            disabled={submitting || !name.trim()}
            className="bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover"
          >
            {submitting && <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />}
            Salvar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
