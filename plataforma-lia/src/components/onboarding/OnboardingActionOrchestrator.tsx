"use client"

import React, { useCallback, useEffect, useMemo, useState } from "react"
import {
  useSettingsConversational,
  type SettingsActionId,
} from "@/hooks/settings/use-settings-conversational"
import { AnalyzeWebsiteModal } from "@/components/settings/AnalyzeWebsiteModal"
import { useLiaChatContext } from "@/contexts/lia-float-context"
import type { ProposedSaves } from "@/lib/website-proposal-mapper"
import { buildWebsiteProposalMessage } from "@/components/unified-chat/website-proposal-injector"
import { useAiPersona } from "@/hooks/company/use-ai-persona"

const DEFAULT_PERSONA_NAME = "LIA"

/**
 * OnboardingActionOrchestrator — Task #712
 *
 * State machine que executa as 7 actions do company_settings em ordem
 * conversacional, com confirmação humana, possibilidade de pular e
 * resumo do que ja foi feito. Persiste progresso em localStorage e
 * sincroniza com /api/backend-proxy/onboarding/progress.
 *
 * Fluxo de cada step:
 *  1. Mostra card com pergunta-mestre + botoes [Comecar] [Pular].
 *  2. "Comecar" -> envia prompt para o chat via lia:prefill-message
 *     e dispara lia:settings-action para abrir a aba certa em paralelo.
 *  3. Aguarda evento `lia:settings-success` (emitido pelo hub apos
 *     gravacao bem-sucedida ou pelo backend ao concluir a action via
 *     chat) e marca o step como concluido.
 *  4. "Pular" registra skip e avanca.
 *  5. Ao final, marca onboarding como completo no backend.
 */

interface StepDef {
  key: string
  actionId: SettingsActionId
  title: string
  question: string
  prompt: string
  cta: string
}

const STEPS: StepDef[] = [
  {
    key: "profile",
    actionId: "configure_profile",
    title: "Perfil da empresa",
    question: "Vamos comecar pelo basico — nome, missao, setor, tamanho.",
    prompt:
      "Quero configurar o perfil da minha empresa. Me ajude a preencher nome, missao, setor e tamanho.",
    cta: "Configurar perfil",
  },
  {
    key: "culture",
    actionId: "configure_culture",
    title: "Cultura e valores",
    question: "Quais valores e diferenciais culturais voce quer destacar?",
    prompt:
      "Quero registrar a cultura da empresa: valores, diferenciais e como gostariamos de ser percebidos por candidatos.",
    cta: "Falar sobre cultura",
  },
  {
    key: "tech_stack",
    actionId: "configure_tech_stack",
    title: "Stack tecnico",
    question: "Quais tecnologias o time usa hoje?",
    prompt:
      "Quero cadastrar nosso stack tecnico: linguagens, frameworks, cloud e ferramentas principais.",
    cta: "Cadastrar stack",
  },
  {
    key: "benefits",
    actionId: "configure_benefits",
    title: "Beneficios",
    question: "Liste os principais beneficios oferecidos.",
    prompt:
      "Quero registrar nossos beneficios. Vou listar: vale-refeicao, plano de saude, gympass, ...",
    cta: "Adicionar beneficios",
  },
  {
    key: "workforce",
    actionId: "configure_workforce",
    title: "Planejamento de contratacoes",
    question: "Quais vagas voce planeja abrir nos proximos meses?",
    prompt:
      "Quero importar nosso planejamento de contratacoes (cargo, quantidade, prazo, senioridade).",
    cta: "Planejar contratacoes",
  },
  {
    key: "policy",
    actionId: "configure_hiring_policy",
    title: "Políticas de recrutamento",
    question: "Como você quer que a IA conduza o processo? Aprovações, triagem automática, horários permitidos.",
    prompt:
      "Quero configurar as políticas de recrutamento: aprovação de oferta, triagem automática, autonomia da IA e horários permitidos para contato.",
    cta: "Configurar políticas",
  },
  {
    key: "persona",
    actionId: "configure_persona",
    title: `Personalidade de ${DEFAULT_PERSONA_NAME}`,
    question: "Quer dar um nome ou escolher um tom de voz para a sua assistente?",
    prompt:
      "Quero personalizar a assistente: escolher um nome customizado e o tom de comunicação que combina com a nossa empresa.",
    cta: "Personalizar assistente",
  },
  {
    key: "website",
    actionId: "analyze_website",
    title: "Analisar nosso site",
    question:
      "Posso ler o site da empresa e sugerir conteudo para o perfil. Qual e a URL?",
    prompt: "Quero que voce analise nosso site institucional e me ajude a preencher o perfil.",
    cta: "Analisar site",
  },
  {
    key: "document",
    actionId: "process_document",
    title: "Processar documento",
    question:
      "Tem um manifesto ou material institucional? Posso extrair informacoes.",
    prompt:
      "Vou enviar um documento institucional para voce processar e sugerir campos do perfil.",
    cta: "Enviar documento",
  },
]

// Sprint 3 BE-6: map section from lia:settings-updated → actionId so the
// general LIA chat (WS) also advances the onboarding orchestrator when the
// agent saves a settings field. Covers both onboarding runner sections
// ("policy") and useChatTransport TOOL_TO_SECTION values ("hiring_policies").
const SECTION_TO_ONBOARDING_ACTION: Partial<Record<string, string>> = {
  profile: "configure_profile",
  culture: "configure_culture",
  tech_stack: "configure_tech_stack",
  benefits: "configure_benefits",
  workforce: "configure_workforce",
  policy: "configure_hiring_policy",
  hiring_policies: "configure_hiring_policy",
  lia_persona: "configure_persona",
}

type StepStatus = "pending" | "in_progress" | "done" | "skipped"

interface ProgressState {
  current: number
  status: Record<string, StepStatus>
}

const LS_KEY = "lia:onboarding-712:v1"

function loadLocal(): ProgressState {
  if (typeof window === "undefined") {
    return { current: 0, status: {} }
  }
  try {
    const raw = localStorage.getItem(LS_KEY)
    if (raw) return JSON.parse(raw) as ProgressState
  } catch {
    // ignore
  }
  return { current: 0, status: {} }
}

function saveLocal(state: ProgressState) {
  try {
    localStorage.setItem(LS_KEY, JSON.stringify(state))
  } catch {
    // ignore
  }
}

async function pushProgress(stepKey: string, status: StepStatus) {
  try {
    await fetch("/api/backend-proxy/onboarding/progress", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({
        task: "company_settings_712",
        step_id: stepKey,
        status,
      }),
    })
  } catch {
    // best-effort, no UX block
  }
}

export function OnboardingActionOrchestrator() {
  const { persona } = useAiPersona()
  const personaName = persona?.name ?? "IA"
  const [state, setState] = useState<ProgressState>(() => loadLocal())
  const { triggerAction, sendChatPrompt } = useSettingsConversational()
  // Task #1180 — passo "website" abre o modal pré-análise em vez de
  // disparar prompt para o chat.
  const [analyzeModalOpen, setAnalyzeModalOpen] = useState(false)
  const { setChatMessages } = useLiaChatContext()

  useEffect(() => {
    saveLocal(state)
  }, [state])

  // Listen to success/error events emitted by settings hubs OR backend
  useEffect(() => {
    if (typeof window === "undefined") return
    const onSuccess = (e: Event) => {
      const detail = (e as CustomEvent).detail || {}
      // Sprint 3 BE-6: lia:settings-updated carries section but no actionId.
      // Derive actionId from section so WS-based saves also advance the orchestrator.
      const actionId: string | undefined =
        detail.actionId ||
        (detail.section ? SECTION_TO_ONBOARDING_ACTION[detail.section as string] : undefined)
      if (!actionId) return
      setState((prev) => {
        const idx = STEPS.findIndex((s) => s.actionId === actionId)
        if (idx === -1) return prev
        const stepKey = STEPS[idx].key
        if (prev.status[stepKey] === "done") return prev
        const next = { ...prev.status, [stepKey]: "done" as StepStatus }
        const newCurrent = idx === prev.current ? Math.min(idx + 1, STEPS.length) : prev.current
        pushProgress(stepKey, "done")
        return { current: newCurrent, status: next }
      })
    }
    window.addEventListener("lia:settings-success", onSuccess)
    window.addEventListener("lia:settings-updated", onSuccess)
    return () => {
      window.removeEventListener("lia:settings-success", onSuccess)
      window.removeEventListener("lia:settings-updated", onSuccess)
    }
  }, [])

  const advance = useCallback((reason: "skip" | "back") => {
    setState((prev) => {
      const stepKey = STEPS[prev.current]?.key
      const status = { ...prev.status }
      if (reason === "skip" && stepKey) {
        status[stepKey] = "skipped"
        pushProgress(stepKey, "skipped")
        return {
          current: Math.min(prev.current + 1, STEPS.length),
          status,
        }
      }
      if (reason === "back") {
        return { current: Math.max(prev.current - 1, 0), status }
      }
      return prev
    })
  }, [])

  const startStep = useCallback(
    (step: StepDef, idx: number) => {
      setState((prev) => {
        const status = { ...prev.status, [step.key]: "in_progress" as StepStatus }
        pushProgress(step.key, "in_progress")
        return { current: idx, status }
      })
      // Task #1180 — passo `website` agora abre o modal pré-análise, não
      // dispara prompt no chat. Os demais passos seguem o fluxo conversacional.
      if (step.key === "website") {
        setAnalyzeModalOpen(true)
        return
      }
      // triggerAction ja despacha `lia:prefill-message` quando recebe `prompt`,
      // entao nao chamamos sendChatPrompt aqui — evita prefill duplicado no chat.
      triggerAction(step.actionId, {
        prompt: step.prompt,
        source: "onboarding",
      })
    },
    [triggerAction],
  )

  const completed = useMemo(
    () => STEPS.filter((s) => state.status[s.key] === "done").length,
    [state.status],
  )
  const total = STEPS.length
  const allDone = state.current >= total

  return (
    <aside
      data-testid="onboarding-orchestrator"
      className="w-[340px] flex-shrink-0 border-r border-lia-border-default bg-lia-bg-secondary/40
                 p-4 flex flex-col gap-3 overflow-y-auto"
    >
      <header className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-lia-text-primary">
          {`Configurar empresa com ${personaName}`}
        </h2>
        <span
          aria-label="Progresso"
          className="text-xs text-lia-text-secondary tabular-nums"
        >
          {completed}/{total}
        </span>
      </header>
      <div className="h-1 w-full rounded bg-lia-bg-tertiary overflow-hidden">
        <div
          className="h-full bg-wedo-cyan transition-[width]"
          style={{ width: `${(completed / total) * 100}%` }}
        />
      </div>

      <ol className="flex flex-col gap-2 mt-2">
        {STEPS.map((step, idx) => {
          const status: StepStatus = state.status[step.key] || "pending"
          const isCurrent = idx === state.current && !allDone
          return (
            <li
              key={step.key}
              data-testid={`onb-step-${step.key}`}
              className={`rounded-md border p-3 text-sm transition-colors ${
                isCurrent
                  ? "border-wedo-cyan bg-lia-bg-primary"
                  : status === "done"
                    ? "border-lia-border-default bg-lia-bg-tertiary/40 opacity-80"
                    : status === "skipped"
                      ? "border-lia-border-default bg-lia-bg-tertiary/20 opacity-60"
                      : "border-lia-border-default bg-lia-bg-secondary"
              }`}
            >
              <div className="flex items-center gap-2">
                <span
                  className={`inline-flex w-5 h-5 items-center justify-center rounded-full text-[10px] font-semibold ${
                    status === "done"
                      ? "bg-wedo-cyan text-white"
                      : status === "skipped"
                        ? "bg-lia-bg-tertiary text-lia-text-disabled"
                        : isCurrent
                          ? "border-2 border-wedo-cyan text-wedo-cyan-text"
                          : "bg-lia-bg-tertiary text-lia-text-disabled"
                  }`}
                >
                  {status === "done" ? "✓" : status === "skipped" ? "—" : idx + 1}
                </span>
                <strong className="text-lia-text-primary">{step.title}</strong>
              </div>
              {isCurrent && (
                <>
                  <p className="text-xs text-lia-text-secondary mt-2">
                    {step.question}
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => startStep(step, idx)}
                      data-testid={`onb-step-${step.key}-start`}
                      className="px-3 py-1 text-xs rounded bg-wedo-cyan text-white
                                 hover:bg-wedo-cyan/90"
                    >
                      {step.cta}
                    </button>
                    <button
                      type="button"
                      onClick={() => advance("skip")}
                      data-testid={`onb-step-${step.key}-skip`}
                      className="px-3 py-1 text-xs rounded border border-lia-border-default
                                 text-lia-text-secondary hover:bg-lia-bg-tertiary"
                    >
                      Pular
                    </button>
                    {idx > 0 && (
                      <button
                        type="button"
                        onClick={() => advance("back")}
                        className="px-3 py-1 text-xs rounded text-lia-text-secondary
                                   hover:underline"
                      >
                        Voltar
                      </button>
                    )}
                  </div>
                </>
              )}
            </li>
          )
        })}
      </ol>

      <AnalyzeWebsiteModal
        open={analyzeModalOpen}
        onClose={() => setAnalyzeModalOpen(false)}
        initial={{}}
        onProposed={({ proposed, companyId: cid }: { proposed: ProposedSaves; companyId: string }) => {
          setChatMessages((prev) => [
            ...prev,
            buildWebsiteProposalMessage(proposed, cid),
          ])
        }}
      />

      {allDone && (
        <div
          data-testid="onb-complete"
          className="rounded-md border border-wedo-cyan bg-wedo-cyan/10 p-3 text-sm
                     text-lia-text-primary"
        >
          <strong>Configuracao basica concluida.</strong>
          <p className="text-xs text-lia-text-secondary mt-1">
            Voce pode revisar tudo em Configuracoes &gt; Minha Empresa quando
            quiser.
          </p>
        </div>
      )}
    </aside>
  )
}
