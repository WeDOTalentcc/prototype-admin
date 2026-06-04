/**
 * AiPersonaPanel — UI canonical para tab "Personalidade da IA" em
 * Minha Empresa (E2.4 audit 2026-05-21).
 *
 * Recrutador define:
 * - Nome da IA (input livre, 2-20 chars, validação backend canonical)
 * - Tom (6 cards canonical — profissional, amigável, formal, casual,
 *   formal-amigável, empático)
 *
 * Preview ao vivo do que a IA "diria" naquela combinação. Box explícito
 * de compliance imutável (LGPD/fairness/anti-bias) reforça transparência.
 *
 * Persona base lia_persona.yaml permanece INTOCADA — backend só APPENDA
 * seções de override (E2.3).
 */
"use client"

import React, { useEffect, useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { AlertCircle, CheckCircle2, Sparkles, ShieldCheck } from "lucide-react"
import { textStyles } from "@/lib/design-tokens"
import {
  useAiPersona,
  useAiPersonaOptions,
  type AiPersonaTone,
  type ToneOption,
} from "@/hooks/company/use-ai-persona"

export function AiPersonaPanel() {
  const {
    persona,
    isLoading,
    isSaving,
    error,
    validationErrors,
    update,
  } = useAiPersona()
  const {
    options,
    isLoading: optionsLoading,
    error: optionsError,
  } = useAiPersonaOptions()

  const [draftName, setDraftName] = useState<string>("")
  const [draftTone, setDraftTone] = useState<AiPersonaTone>("profissional")
  const [savedFeedback, setSavedFeedback] = useState<string | null>(null)

  // Boy-Scout (audit 2026-05-24 P2-E): ressincroniza draft com server-side
  // sempre que persona muda. Antes, o guard `draftName === ""` evitava
  // sobrescrita só no primeiro mount, mas se outra aba editasse persona o
  // refresh trazia novo valor e o draft local ficava stale (CLAUDE.md
  // Onda 2 lição 6: `useState(propX)` é stale state em rerender async).
  // Dependência granular em campos para evitar disparar quando o objeto
  // muda de referência mas valores são iguais.
  const personaName = persona?.name
  const personaTone = persona?.tone
  useEffect(() => {
    if (personaName != null) setDraftName(personaName)
    if (personaTone != null) setDraftTone(personaTone)
  }, [personaName, personaTone])

  const toneOptions: ToneOption[] = options?.tones ?? []
  const previewedTone =
    toneOptions.find((opt) => opt.value === draftTone) ?? toneOptions[0] ?? null

  const handleSave = async () => {
    setSavedFeedback(null)
    const ok = await update({
      name: draftName !== persona?.name ? draftName : undefined,
      tone: draftTone !== persona?.tone ? draftTone : undefined,
    })
    if (ok) {
      setSavedFeedback("Personalidade da IA atualizada com sucesso.")
      setTimeout(() => setSavedFeedback(null), 3000)
    }
  }

  const hasChanges =
    persona && (draftName !== persona.name || draftTone !== persona.tone)
  const nameErr = validationErrors.find((e) => e.code.startsWith("name_"))
  const toneErr = validationErrors.find((e) => e.code.startsWith("tone_"))
  const noChangeErr = validationErrors.find((e) => e.code === "no_change_requested")

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-lia-border-default bg-lia-bg-tertiary p-4 flex items-start gap-3">
        <Sparkles className="w-5 h-5 text-lia-accent-default shrink-0 mt-0.5" />
        <div className="space-y-1">
          <h3 className={textStyles.h4}>Personalidade da IA</h3>
          <p className="text-sm text-lia-text-secondary">
            Escolha o nome da sua IA e o tom de voz que ela usa em mensagens
            aos candidatos E no chat com você. Compliance, fairness e ética
            permanecem imutáveis independente da configuração escolhida.
          </p>
        </div>
      </div>

      {error && (
        <div className="rounded-xl bg-status-error/10 border border-status-error/30 p-3 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-status-error shrink-0 mt-0.5" />
          <p className="text-sm text-status-error">{error}</p>
        </div>
      )}

      {savedFeedback && (
        <div className="rounded-xl bg-status-success-bg border border-status-success/20 p-3 flex items-start gap-2">
          <CheckCircle2 className="w-4 h-4 text-status-success shrink-0 mt-0.5" />
          <p className="text-sm text-status-success">
            {savedFeedback}
          </p>
        </div>
      )}

      {/* Nome */}
      <Card>
        <CardContent className="p-5 space-y-3">
          <Label htmlFor="ai-name" className="text-sm font-medium">
            Nome da IA
          </Label>
          <Input
            id="ai-name"
            value={draftName}
            onChange={(e) => setDraftName(e.target.value)}
            placeholder="Ex: Sofia, Maya, Atena, Iris"
            maxLength={20}
            disabled={isLoading || isSaving}
            data-testid="ai-persona-name-input"
          />
          <p className="text-xs text-lia-text-tertiary">
            2-20 caracteres. Letras (com acentos), números e espaços. Nomes
            de IAs terceiras (Claude, GPT, Gemini, etc.) são reservados.
          </p>
          {nameErr && (
            <div className="rounded-lg bg-status-warning-bg border border-status-warning-border p-2 text-xs text-status-warning">
              <strong>{nameErr.message}</strong>
              {nameErr.fix && (
                <span className="block mt-1">{nameErr.fix}</span>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Tom */}
      <div className="space-y-2">
        <Label className="text-sm font-medium">Tom de Voz</Label>
        {optionsLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {[0, 1, 2, 3, 4, 5].map((idx) => (
              <div
                key={idx}
                className="rounded-xl border border-lia-border-default bg-lia-bg-primary p-4 h-[78px] animate-pulse"
                aria-hidden="true"
              />
            ))}
          </div>
        ) : optionsError || !options ? (
          <div className="rounded-xl bg-status-error/10 border border-status-error/30 p-3 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-status-error shrink-0 mt-0.5" />
            <p className="text-sm text-status-error">
              Não foi possível carregar as opções de tom. Recarregue a página
              para tentar novamente.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {toneOptions.map((opt) => {
              const isSelected = draftTone === opt.value
              return (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setDraftTone(opt.value as AiPersonaTone)}
                  disabled={isLoading || isSaving}
                  data-testid={`ai-persona-tone-${opt.value}`}
                  className={`text-left rounded-xl border p-4 transition-all ${
                    isSelected
                      ? "border-lia-accent-default bg-lia-accent-soft ring-2 ring-lia-accent-default"
                      : "border-lia-border-default bg-lia-bg-primary hover:border-lia-border-strong"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-sm">{opt.label_pt}</span>
                    {isSelected && (
                      <CheckCircle2 className="w-4 h-4 text-lia-accent-default" />
                    )}
                  </div>
                  <p className="text-xs text-lia-text-secondary">
                    {opt.short_pt}
                  </p>
                </button>
              )
            })}
          </div>
        )}
        {toneErr && (
          <div className="rounded-lg bg-status-warning-bg border border-status-warning-border p-2 text-xs text-status-warning">
            <strong>{toneErr.message}</strong>
            {toneErr.fix && <span className="block mt-1">{toneErr.fix}</span>}
          </div>
        )}
      </div>

      {/* Preview */}
      {previewedTone && (
        <Card>
          <CardContent className="p-5 space-y-3">
            <Label className="text-sm font-medium">Preview</Label>
            <div className="space-y-3 text-sm">
              <div className="p-3 rounded-xl bg-lia-bg-primary border border-lia-border-default">
                <p className="text-xs font-medium text-lia-text-tertiary mb-1">
                  {draftName || "LIA"} → candidato (e-mail / WhatsApp)
                </p>
                <p className="text-lia-text-primary">
                  {previewedTone.preview_message_pt.replace(
                    /\bLIA\b/g,
                    draftName || "LIA",
                  )}
                </p>
              </div>
              <div className="p-3 rounded-xl bg-lia-bg-primary border border-lia-border-default">
                <p className="text-xs font-medium text-lia-text-tertiary mb-1">
                  {draftName || "LIA"} → você (chat lateral)
                </p>
                <p className="text-lia-text-primary">
                  {previewedTone.preview_chat_pt}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Compliance imutável */}
      <div className="rounded-xl bg-lia-bg-tertiary border border-lia-border-default p-4 flex items-start gap-3">
        <ShieldCheck className="w-5 h-5 text-status-success shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="text-sm font-medium">Compliance imutável</p>
          <p className="text-xs text-lia-text-secondary">
            Independente do nome e tom escolhidos, a IA mantém: respeito à
            LGPD, ignorar dados protegidos (idade, gênero, foto), linguagem
            inclusiva, transparência em pareceres e registro de decisões.
            Essas garantias são parte do core técnico e não podem ser
            removidas.
          </p>
        </div>
      </div>

      {noChangeErr && (
        <p className="text-xs text-lia-text-tertiary">{noChangeErr.message}</p>
      )}

      <div className="flex justify-end gap-2 pt-2">
        <Button
          variant="outline"
          onClick={() => {
            if (persona) {
              setDraftName(persona.name)
              setDraftTone(persona.tone)
            }
          }}
          disabled={isLoading || isSaving || !hasChanges}
        >
          Reverter
        </Button>
        <Button
          onClick={handleSave}
          disabled={isLoading || isSaving || !hasChanges}
          data-testid="ai-persona-save"
        >
          {isSaving ? "Salvando..." : "Salvar Personalidade"}
        </Button>
      </div>
    </div>
  )
}
