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
  CANONICAL_TONES,
  type AiPersonaTone,
} from "@/hooks/company/use-ai-persona"

interface ToneOption {
  value: AiPersonaTone
  label: string
  short: string
  previewMessage: string
  previewChat: string
}

const TONE_OPTIONS: ToneOption[] = [
  {
    value: "profissional",
    label: "Profissional",
    short: "Cordial, direto, focado em resultados.",
    previewMessage:
      "Olá! Identificamos seu perfil para a vaga de Desenvolvedor. Podemos agendar uma conversa para esta semana?",
    previewChat:
      "Encontrei 12 candidatos compatíveis com a vaga. Quer que eu priorize por experiência ou faixa salarial?",
  },
  {
    value: "amigavel",
    label: "Amigável",
    short: "Caloroso, acessível, com leveza.",
    previewMessage:
      "Oi! Que bom encontrar seu perfil para a vaga de Desenvolvedor. Você teria um tempinho essa semana pra gente conversar?",
    previewChat:
      "Boa! Achei 12 candidatos legais pra essa vaga — quer que eu te mostre os mais alinhados primeiro?",
  },
  {
    value: "formal",
    label: "Formal",
    short: "Rigor protocolar, sem contrações, estrutura completa.",
    previewMessage:
      "Prezado(a) candidato(a), tenho o prazer de convidá-lo(a) para conversarmos sobre a oportunidade de Desenvolvedor. Aguardo seu retorno.",
    previewChat:
      "Foram identificados 12 candidatos compatíveis. Solicito sua orientação quanto ao critério de priorização.",
  },
  {
    value: "casual",
    label: "Casual",
    short: "Descontraído, próximo, como conversa de WhatsApp.",
    previewMessage:
      "Ei! Vi que seu perfil bate com a vaga de Dev. Tem um tempinho pra gente bater um papo essa semana?",
    previewChat:
      "Achei uns 12 candidatos pra essa vaga. Qual ordem você prefere? Por experiência ou por fit cultural?",
  },
  {
    value: "formal_amigavel",
    label: "Formal-amigável",
    short: "Equilibra rigor profissional com calor humano.",
    previewMessage:
      "Olá! Foi um prazer encontrar seu perfil. Gostaria de convidar você para conversarmos sobre a vaga de Desenvolvedor — quando seria um bom momento?",
    previewChat:
      "Encontrei 12 candidatos com boa aderência. Posso te mostrar agrupados por senioridade, se ajudar?",
  },
  {
    value: "empatico",
    label: "Empático",
    short: "Escuta, reconhecimento, acolhimento.",
    previewMessage:
      "Olá! Entendo que processos seletivos podem ser intensos. Adoraria conversar com você sobre a vaga de Desenvolvedor — escolha um horário que funcione bem pra você.",
    previewChat:
      "Sei que escolher entre vários candidatos não é fácil. Encontrei 12 perfis — quer que eu te ajude a pensar critério a critério?",
  },
]

export function AiPersonaPanel() {
  const {
    persona,
    isLoading,
    isSaving,
    error,
    validationErrors,
    update,
  } = useAiPersona()

  const [draftName, setDraftName] = useState<string>("")
  const [draftTone, setDraftTone] = useState<AiPersonaTone>("profissional")
  const [savedFeedback, setSavedFeedback] = useState<string | null>(null)

  // Sync draft com persona carregada (uma vez quando chega do servidor).
  useEffect(() => {
    if (persona && draftName === "") {
      setDraftName(persona.name)
      setDraftTone(persona.tone)
    }
  }, [persona, draftName])

  const previewedTone =
    TONE_OPTIONS.find((opt) => opt.value === draftTone) ?? TONE_OPTIONS[0]

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
      <div className="rounded-2xl border border-lia-border-default bg-lia-bg-tertiary p-4 flex items-start gap-3">
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
        <div className="rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 p-3 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
          <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
        </div>
      )}

      {savedFeedback && (
        <div className="rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 p-3 flex items-start gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
          <p className="text-sm text-emerald-700 dark:text-emerald-300">
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
            <div className="rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 p-2 text-xs text-amber-700 dark:text-amber-300">
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
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {TONE_OPTIONS.map((opt) => {
            const isSelected = draftTone === opt.value
            return (
              <button
                key={opt.value}
                type="button"
                onClick={() => setDraftTone(opt.value)}
                disabled={isLoading || isSaving}
                data-testid={`ai-persona-tone-${opt.value}`}
                className={`text-left rounded-2xl border p-4 transition-all ${
                  isSelected
                    ? "border-lia-accent-default bg-lia-accent-soft ring-2 ring-lia-accent-default"
                    : "border-lia-border-default bg-lia-bg-primary hover:border-lia-border-strong"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-sm">{opt.label}</span>
                  {isSelected && (
                    <CheckCircle2 className="w-4 h-4 text-lia-accent-default" />
                  )}
                </div>
                <p className="text-xs text-lia-text-secondary">{opt.short}</p>
              </button>
            )
          })}
        </div>
        {toneErr && (
          <div className="rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 p-2 text-xs text-amber-700 dark:text-amber-300">
            <strong>{toneErr.message}</strong>
            {toneErr.fix && <span className="block mt-1">{toneErr.fix}</span>}
          </div>
        )}
      </div>

      {/* Preview */}
      <Card>
        <CardContent className="p-5 space-y-3">
          <Label className="text-sm font-medium">Preview</Label>
          <div className="space-y-3 text-sm">
            <div className="p-3 rounded-xl bg-lia-bg-primary border border-lia-border-default">
              <p className="text-xs font-medium text-lia-text-tertiary mb-1">
                {draftName || "LIA"} → candidato (e-mail / WhatsApp)
              </p>
              <p className="text-lia-text-primary">
                {previewedTone.previewMessage.replace(/\bLIA\b/g, draftName || "LIA")}
              </p>
            </div>
            <div className="p-3 rounded-xl bg-lia-bg-primary border border-lia-border-default">
              <p className="text-xs font-medium text-lia-text-tertiary mb-1">
                {draftName || "LIA"} → você (chat lateral)
              </p>
              <p className="text-lia-text-primary">
                {previewedTone.previewChat}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Compliance imutável */}
      <div className="rounded-2xl bg-lia-bg-tertiary border border-lia-border-default p-4 flex items-start gap-3">
        <ShieldCheck className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
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
