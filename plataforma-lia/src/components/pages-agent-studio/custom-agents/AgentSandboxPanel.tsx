// Q4.2 Sandbox "Testar antes de ativar" (2026-05-29) — fecha gap C1 do AUDIT 7.
//
// Fase 3 Sprint 3 (2026-05-30): promovido de modal-sobre-modal pra painel
// INLINE. O corpo do sandbox vive agora em <AgentSandboxInline>, renderizado
// lado-a-lado com a config no AgentDetailsPanel (test-as-you-build estilo
// ElevenLabs — preview sempre visível). <AgentSandboxPanel> permanece como
// wrapper Dialog fino pra retrocompatibilidade (callers standalone + testes).
//
// Diferente do TestDebugPanel (debug pós-execução): este painel deixa o
// recrutador SIMULAR a 1ª execução do agente ANTES de ativá-lo. Roda o
// raciocínio REAL (LLM/BYOK + tools de leitura) mas o backend INTERCEPTA write
// tools (send_*/move_*/update_*) — nenhuma ação real acontece. Mostra:
//   - banner AMBER "MODO SIMULAÇÃO" (cor distinta do cyan da IA, sinaliza que
//     nada real ocorreu)
//   - chips de mensagens-exemplo de RH (1 clique dispara o dry-run)
//   - lista das ações que o agente FARIA ("Enviaria…", "Moveria…")
//   - reasoning trace canonical reusando DecisionTreeBody (sem viewer paralelo)
//   - CTA "Ativar agente" depois que o recrutador valida o comportamento
"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import React, { useState } from "react"
import { useTranslations } from "next-intl"
import { Send, Loader2, FlaskConical, Mail, ArrowRightLeft, Pencil, Zap, ShieldCheck } from "lucide-react"
import { cn } from "@/lib/utils"
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { useAiPersona } from "@/hooks/company/use-ai-persona"
import { TabSectionHeader } from "@/components/pages-agent-studio/TabSectionHeader"
import { DecisionTreeBody } from "../decision-tree/DecisionTreeDrawer"
import type {
  AgentReasoningStep,
  ExecutionReasoningResponse,
} from "../decision-tree/types"
import { safeCategoryKey } from "./types"
import type { AgentCategory, CustomAgent } from "./types"

interface WouldDoAction {
  tool: string
  args: Record<string, unknown>
}

interface DryRunResult {
  agent_id: string
  agent_name: string
  response: string
  confidence: number
  would_do_actions: WouldDoAction[]
  reasoning_trace: AgentReasoningStep[] | null
  tool_calls: string[]
  execution_time_ms: number
  tokens_input: number
  tokens_output: number
  model_used: string
  dry_run: boolean
}

interface AgentSandboxInlineProps {
  agent: CustomAgent
  // Chamado quando o recrutador valida o comportamento e quer ativar/vincular.
  onActivate: (agent: CustomAgent) => void
}

interface AgentSandboxPanelProps {
  agent: CustomAgent | null
  open: boolean
  onClose: () => void
  onActivate: (agent: CustomAgent) => void
}

// Heurística canonical: tool name → ícone + verbo "faria". Reusa as keys de
// would-do do namespace agents.studio.sandbox. Fallback genérico se a tool não
// estiver mapeada (custom tool).
const TOOL_ICON: Record<string, React.ReactNode> = {
  send_email: <Mail className="h-4 w-4" aria-hidden="true" />,
  move_candidate: <ArrowRightLeft className="h-4 w-4" aria-hidden="true" />,
  update_candidate_field: <Pencil className="h-4 w-4" aria-hidden="true" />,
  schedule_interview: <Zap className="h-4 w-4" aria-hidden="true" />,
}

// Fase 3 Sprint 3: mensagens-exemplo de RH por categoria de agente. Reduzem a
// fricção do "o que eu escrevo?" + ensinam o recrutador o que vale testar.
// Cada chave resolve em agents.studio.sandbox.examples.<categoria>.<id> (pt-BR + en).
const EXAMPLE_KEYS_BY_CATEGORY: Record<AgentCategory, string[]> = {
  screening: ["seniorPython", "weakProfile", "midGeneralist"],
  sourcing: ["activeSearch", "passiveCandidate", "nicheRole"],
  communication: ["interviewInvite", "rejectionFeedback", "statusUpdate"],
  analytics: ["funnelHealth", "stageBottleneck", "sourceQuality"],
  job_management: ["draftReview", "publishCheck", "requirementsGap"],
  automation: ["newCandidateFlow", "stageChangeFlow", "scheduledDigest"],
  general: ["seniorPython", "weakProfile", "midGeneralist"],
}

function summarizeArgs(args: Record<string, unknown>): string {
  const parts: string[] = []
  for (const [k, v] of Object.entries(args ?? {})) {
    if (v === null || v === undefined) continue
    const val = typeof v === "string" ? v : JSON.stringify(v)
    parts.push(`${k}: ${val.length > 60 ? `${val.slice(0, 60)}…` : val}`)
  }
  return parts.join(" · ")
}

/**
 * Corpo INLINE do sandbox — sem Dialog próprio. Renderizado dentro do
 * AgentDetailsPanel (coluna "Testar agente") ou em qualquer surface que queira
 * o test-as-you-build sem nesting de modal.
 */
export function AgentSandboxInline({ agent, onActivate }: AgentSandboxInlineProps) {
  const t = useTranslations("agents.studio.sandbox")
  const { persona: aiPersona } = useAiPersona()
  const agentDisplayName = agent.name || aiPersona?.name || t("untitledAgent")
  const [message, setMessage] = useState("")
  const [isSimulating, setIsSimulating] = useState(false)
  const [result, setResult] = useState<DryRunResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const categoryKey = safeCategoryKey(agent.category ?? agent.domain)
  const exampleKeys = EXAMPLE_KEYS_BY_CATEGORY[categoryKey] ?? EXAMPLE_KEYS_BY_CATEGORY.general

  const runSimulation = async (sampleMessage: string) => {
    const trimmed = sampleMessage.trim()
    if (!trimmed) return
    setIsSimulating(true)
    setError(null)
    try {
      const token = localStorage.getItem("auth_token")
      const res = await fetch(`/api/backend-proxy/custom-agents/${agent.id}/dry-run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message: trimmed }),
      })
      if (!res.ok) throw new Error(await res.text())
      const data: DryRunResult = await res.json()
      setResult(data)
    } catch {
      setError(t("error"))
    } finally {
      setIsSimulating(false)
    }
  }

  const handleSimulate = () => runSimulation(message)

  // Chip de exemplo: preenche o input + dispara o dry-run num clique.
  const handleExampleChip = (label: string) => {
    setMessage(label)
    void runSimulation(label)
  }

  // Synthesize an ExecutionReasoningResponse so we can reuse the canonical
  // DecisionTreeBody renderer (no parallel viewer). Dry-run não popula
  // criteria/LGPD-not-accessed; o renderer degrada graciosamente.
  const reasoning: ExecutionReasoningResponse | null = result
    ? {
        execution_id: "dry-run",
        agent_id: result.agent_id,
        agent_name: result.agent_name,
        started_at: null,
        completed_at: null,
        model_used: result.model_used,
        cost_usd: null,
        latency_ms: result.execution_time_ms,
        input_tokens: result.tokens_input,
        output_tokens: result.tokens_output,
        reasoning_trace: result.reasoning_trace ?? [],
        data_fields_accessed_summary: [],
        data_fields_NOT_accessed: [],
      }
    : null

  return (
    <div className="flex h-full flex-col" data-testid="agent-sandbox-inline">
      <div className="mb-3 flex items-center gap-2">
        <FlaskConical className="h-4 w-4 text-status-warning" aria-hidden="true" />
        <h3 className="text-sm font-semibold text-lia-text-primary">
          {t("inlineTitle", { agent: agentDisplayName })}
        </h3>
      </div>

      {/* Banner MODO SIMULAÇÃO — amber (status-warning), distinto do cyan da IA. */}
      <div
        role="status"
        aria-live="polite"
        className="flex items-start gap-2 rounded-md border border-status-warning/30 bg-status-warning/10 p-3 text-xs text-status-warning"
        data-testid="sandbox-simulation-banner"
      >
        <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
        <span>{t("simulationBanner")}</span>
      </div>

      <div className="mt-3 flex min-h-0 flex-1 flex-col space-y-3">
        <p className="text-xs text-lia-text-secondary">{t("description")}</p>

        {/* Chips de mensagens-exemplo de RH (1 clique → dry-run). */}
        <div data-testid="sandbox-example-chips">
          <p className="mb-1.5 text-[11px] font-medium uppercase tracking-wide text-lia-text-tertiary">
            {t("examplesLabel")}
          </p>
          <div className="flex flex-wrap gap-1.5">
            {exampleKeys.map((key) => {
              const label = t(`examples.${categoryKey}.${key}`)
              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => handleExampleChip(label)}
                  disabled={isSimulating}
                  className="rounded-full border border-lia-border-subtle bg-lia-bg-secondary px-3 py-1 text-xs text-lia-text-secondary transition-colors hover:bg-lia-bg-tertiary hover:text-lia-text-primary disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-status-warning/40"
                  data-testid={`sandbox-example-chip-${key}`}
                >
                  {label}
                </button>
              )
            })}
          </div>
        </div>

        {/* Input de mensagem de amostra */}
        <div className="flex gap-2">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !isSimulating) handleSimulate()
            }}
            placeholder={t("inputPlaceholder")}
            aria-label={t("inputAriaLabel")}
            className="flex-1 rounded-md border border-lia-border-subtle bg-lia-bg-primary px-3 py-2 text-sm text-lia-text-primary focus:outline-none focus:ring-2 focus:ring-status-warning/40"
            data-testid="sandbox-message-input"
          />
          <Button
            type="button"
            onClick={handleSimulate}
            disabled={isSimulating || !message.trim()}
            className="gap-1.5 bg-status-warning text-paper hover:bg-status-warning/90"
            data-testid="sandbox-simulate-button"
          >
            {isSimulating ? (
              <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none" aria-hidden="true" />
            ) : (
              <Send className="h-4 w-4" aria-hidden="true" />
            )}
            {t("simulateButton")}
          </Button>
        </div>

        {error ? (
          <div
            className="rounded-md border border-status-error/30 bg-status-error/10 p-3 text-sm text-status-error"
            data-testid="sandbox-error"
          >
            {error}
          </div>
        ) : null}

        {!result && !error && !isSimulating ? (
          <div
            className="flex flex-1 flex-col items-center justify-center rounded-md border border-dashed border-lia-border-subtle p-6 text-center"
            data-testid="sandbox-empty"
          >
            <FlaskConical className="mb-2 h-6 w-6 text-lia-text-muted" aria-hidden="true" />
            <p className="text-xs text-lia-text-muted">{t("emptyHint")}</p>
          </div>
        ) : null}

        {result ? (
          <div className="space-y-4 overflow-y-auto" data-testid="sandbox-result">
            {/* Resposta textual do agente */}
            <div className="rounded-md border border-lia-border-subtle bg-lia-bg-secondary p-3">
              <div className="mb-1 text-xs font-semibold text-lia-text-secondary">
                {t("agentResponse")}
              </div>
              <p className="text-sm text-lia-text-primary whitespace-pre-wrap break-words">
                {result.response}
              </p>
            </div>

            {/* Ações que o agente FARIA (interceptadas) */}
            <section aria-labelledby="sandbox-would-do-heading">
              <TabSectionHeader
                headingId="sandbox-would-do-heading"
                className="mb-2"
                title={t("wouldDoTitle")}
              />
              {result.would_do_actions.length === 0 ? (
                <p
                  className="text-xs text-lia-text-tertiary italic"
                  data-testid="sandbox-no-actions"
                >
                  {t("noWouldDo")}
                </p>
              ) : (
                <ul className="space-y-1.5" data-testid="sandbox-would-do-list">
                  {result.would_do_actions.map((action, idx) => (
                    <li
                      key={`wd-${idx}`}
                      className="flex items-start gap-2 rounded-md border border-status-warning/30 bg-status-warning/10 px-3 py-2"
                    >
                      <span className="mt-0.5 shrink-0 text-status-warning">
                        {TOOL_ICON[action.tool] ?? <Zap className="h-4 w-4" aria-hidden="true" />}
                      </span>
                      <div className="min-w-0 flex-1">
                        <div className="text-sm font-medium text-lia-text-primary">
                          {t.has(`wouldDoVerb.${action.tool}`)
                            ? t(`wouldDoVerb.${action.tool}`)
                            : t("wouldDoGeneric", { tool: action.tool })}
                        </div>
                        {summarizeArgs(action.args) ? (
                          <div className="mt-0.5 text-xs text-lia-text-secondary break-words">
                            {summarizeArgs(action.args)}
                          </div>
                        ) : null}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            {/* Reasoning trace canonical (reusa DecisionTreeBody) */}
            {reasoning ? (
              <section
                aria-labelledby="sandbox-reasoning-heading"
                className="border-t border-lia-border-subtle pt-3"
              >
                <TabSectionHeader
                  headingId="sandbox-reasoning-heading"
                  className="mb-2"
                  title={t("reasoningTitle")}
                />
                <DecisionTreeBody reasoning={reasoning} agentDisplayName={agentDisplayName} />
              </section>
            ) : null}

            {/* CTA Ativar agente */}
            <div className="flex gap-2 border-t border-lia-border-subtle pt-3">
              <Button
                type="button"
                onClick={() => onActivate(agent)}
                className="flex-1 bg-powder text-graphite hover:bg-mist"
                data-testid="sandbox-activate-button"
              >
                {t("activateButton")}
              </Button>
              <Button
                type="button"
                variant="ghost"
                onClick={() => {
                  setResult(null)
                  setMessage("")
                }}
                className="text-lia-text-secondary"
                data-testid="sandbox-retry-button"
              >
                {t("retryButton")}
              </Button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  )
}

/**
 * Wrapper Dialog fino — retrocompatibilidade pra callers standalone (e testes).
 * Surfaces novas devem preferir <AgentSandboxInline> sem nesting de modal.
 */
export function AgentSandboxPanel({ agent, open, onClose, onActivate }: AgentSandboxPanelProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('agent-sandbox', open)

  const t = useTranslations("agents.studio.sandbox")
  const { persona: aiPersona } = useAiPersona()

  if (!agent) return null
  const agentDisplayName = agent.name || aiPersona?.name || t("untitledAgent")

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent
        className="sm:max-w-lg max-h-[85vh] overflow-y-auto"
        data-testid="agent-sandbox-panel"
      >
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-base font-semibold text-lia-text-primary">
            <FlaskConical className="h-5 w-5 text-status-warning" aria-hidden="true" />
            {t("title", { agent: agentDisplayName })}
          </DialogTitle>
        </DialogHeader>
        <AgentSandboxInline agent={agent} onActivate={onActivate} />
      </DialogContent>
    </Dialog>
  )
}
