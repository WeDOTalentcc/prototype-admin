// Q4.2 Sandbox "Testar antes de ativar" (2026-05-29) — fecha gap C1 do AUDIT 7.
//
// Diferente do TestDebugPanel (debug pós-execução): este painel deixa o
// recrutador SIMULAR a 1ª execução do agente ANTES de ativá-lo. Roda o
// raciocínio REAL (LLM/BYOK + tools de leitura) mas o backend INTERCEPTA write
// tools (send_*/move_*/update_*) — nenhuma ação real acontece. Mostra:
//   - banner AMBER "MODO SIMULAÇÃO" (cor distinta do cyan da IA, sinaliza que
//     nada real ocorreu)
//   - lista das ações que o agente FARIA ("Enviaria…", "Moveria…")
//   - reasoning trace canonical reusando DecisionTreeBody (sem viewer paralelo)
//   - CTA "Ativar agente" depois que o recrutador valida o comportamento
"use client"

import React, { useState } from "react"
import { useTranslations } from "next-intl"
import { Send, Loader2, FlaskConical, Mail, ArrowRightLeft, Pencil, Zap, ShieldCheck } from "lucide-react"
import { cn } from "@/lib/utils"
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { useAiPersona } from "@/hooks/company/use-ai-persona"
import { DecisionTreeBody } from "../decision-tree/DecisionTreeDrawer"
import type {
  AgentReasoningStep,
  ExecutionReasoningResponse,
} from "../decision-tree/types"
import type { CustomAgent } from "./types"

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

interface AgentSandboxPanelProps {
  agent: CustomAgent | null
  open: boolean
  onClose: () => void
  // Chamado quando o recrutador valida o comportamento e quer ativar/vincular.
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

function summarizeArgs(args: Record<string, unknown>): string {
  const parts: string[] = []
  for (const [k, v] of Object.entries(args ?? {})) {
    if (v === null || v === undefined) continue
    const val = typeof v === "string" ? v : JSON.stringify(v)
    parts.push(`${k}: ${val.length > 60 ? `${val.slice(0, 60)}…` : val}`)
  }
  return parts.join(" · ")
}

export function AgentSandboxPanel({ agent, open, onClose, onActivate }: AgentSandboxPanelProps) {
  const t = useTranslations("agents.studio.sandbox")
  const { persona: aiPersona } = useAiPersona()
  const agentDisplayName = agent?.name || aiPersona?.name || t("untitledAgent")
  const [message, setMessage] = useState("")
  const [isSimulating, setIsSimulating] = useState(false)
  const [result, setResult] = useState<DryRunResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSimulate = async () => {
    if (!agent || !message.trim()) return
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
        body: JSON.stringify({ message: message.trim() }),
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

  if (!agent) return null

  // Synthesize an ExecutionReasoningResponse so we can reuse the canonical
  // DecisionTreeBody renderer (no parallel viewer). Dry-run não popula
  // criteria/LGPD-not-accessed; o renderer degrada graciosamente (mostra
  // "sem critérios" etc), o foco aqui é o reasoning_trace + meta.
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
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent
        className="sm:max-w-lg max-h-[85vh] overflow-y-auto"
        data-testid="agent-sandbox-panel"
      >
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-base font-semibold text-lia-text-primary">
            <FlaskConical className="h-5 w-5 text-amber-500" aria-hidden="true" />
            {t("title", { agent: agentDisplayName })}
          </DialogTitle>
        </DialogHeader>

        {/* Banner MODO SIMULAÇÃO — amber, distinto do cyan da IA (execução real). */}
        <div
          role="status"
          aria-live="polite"
          className="flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900 dark:border-amber-900/40 dark:bg-amber-950/20 dark:text-amber-200"
          data-testid="sandbox-simulation-banner"
        >
          <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          <span>{t("simulationBanner")}</span>
        </div>

        <div className="space-y-4 pt-1">
          <p className="text-xs text-lia-text-secondary">{t("description")}</p>

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
              className="flex-1 rounded-md border border-lia-border-subtle bg-lia-bg-primary px-3 py-2 text-sm text-lia-text-primary focus:outline-none focus:ring-2 focus:ring-amber-400/40"
              data-testid="sandbox-message-input"
            />
            <Button
              type="button"
              onClick={handleSimulate}
              disabled={isSimulating || !message.trim()}
              className="gap-1.5 bg-amber-500 text-white hover:bg-amber-600"
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
              className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-900 dark:border-rose-900/40 dark:bg-rose-950/20 dark:text-rose-200"
              data-testid="sandbox-error"
            >
              {error}
            </div>
          ) : null}

          {result ? (
            <div className="space-y-4" data-testid="sandbox-result">
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
                <h3
                  id="sandbox-would-do-heading"
                  className="mb-2 text-sm font-semibold text-lia-text-primary"
                >
                  {t("wouldDoTitle")}
                </h3>
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
                        className="flex items-start gap-2 rounded-md border border-amber-200 bg-amber-50/50 px-3 py-2 dark:border-amber-900/40 dark:bg-amber-950/10"
                      >
                        <span className="mt-0.5 shrink-0 text-amber-600 dark:text-amber-400">
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
                  <h3
                    id="sandbox-reasoning-heading"
                    className="mb-2 text-sm font-semibold text-lia-text-primary"
                  >
                    {t("reasoningTitle")}
                  </h3>
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
      </DialogContent>
    </Dialog>
  )
}
