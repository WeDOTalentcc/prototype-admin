"use client"

/**
 * CreateAgentWizard — unified goal-first entry-point for agent creation.
 *
 * UX_AUDIT_ESTUDIO_AGENTES_2026-05-21 — T1 + T3 + T4.
 *
 * T1 (transformacao): substitui os ~9 CTAs "Criar Agente / Criar com IA /
 * Criar do zero / Criar primeiro agente" espalhados em 5 tabs
 * (Captacao, Personalizados, Marketplace, Gemeos, Busca) por UM unico
 * wizard de 4 passos com onboarding goal-first.
 *
 * T3 (transformacao): promove "Criar com IA" — que estava escondido como
 * Beta no fundo da aba Custom — para hero do step 2, com badge
 * "Recomendado" e descricao em linguagem natural. Endpoint backing
 * (POST /api/backend-proxy/custom-agents/generate -> FastAPI
 * /api/v1/custom-agents/generate-from-description) ja existia.
 *
 * T4 (clone-first / HubSpot Breeze pattern): aceita `initialConfig` com
 * `templateId` (vindo do TemplateClonePanel). Quando presente, o wizard
 * pula goal+approach e abre direto no step 3 (Configurar) com nome
 * "(cópia)" e config do template ja populada. Recruiter customiza ANTES
 * de criar — vs o pattern antigo "criou primeiro, customiza depois".
 *
 * Steps:
 *   1. GoalStep        — escolher objetivo (5 opcoes canonical)
 *   2. ApproachStep    — IA (hero) | template (filtrado por goal) | manual
 *   3. ConfigStep      — preview/edit conforme approach
 *   4. PreviewStep     — resumo final + criar
 *
 * Endpoint matrix (chamados via fetch direto, sem hook compartilhado
 * porque a logica de criacao varia bastante por approach):
 *   - approach=ai     -> POST /api/backend-proxy/custom-agents/generate (gera preview)
 *                        -> POST /api/backend-proxy/custom-agents (cria com base no preview)
 *   - approach=template -> POST /api/backend-proxy/agent-templates/sectors/{id} (apply)
 *                          fallback: POST /api/backend-proxy/custom-agents (template stub
 *                          inline quando o sector endpoint nao casa)
 *   - approach=manual -> POST /api/backend-proxy/custom-agents
 *
 * Os modais existentes (CreateAgentModal sourcing, CreateDigitalTwinModal,
 * TemplatePreviewModal, ConversationalCreator) ficam montados como
 * entry-points alternativos / detalhes — nao sao removidos. O wizard
 * eh o ponto unico de entrada para "Criar agente" no header da pagina.
 */

import { useEffect, useState } from "react"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { extractErrorMessage } from "@/lib/api/extract-error-message"
import { buildCreateAgentPayloadFromTemplate } from "@/lib/agents/create-agent-payload"
import { useLegacyAgentTemplates } from "@/hooks/agents/use-legacy-agent-templates"
import { toast } from "@/lib/toast"
import { cn } from "@/lib/utils"

import { ApproachStep } from "./steps/ApproachStep"
import { ConfigStep } from "./steps/ConfigStep"
import { GoalStep } from "./steps/GoalStep"
import { PreviewStep } from "./steps/PreviewStep"
import type {
  AgentApproach,
  AgentGoal,
  CreateAgentInitialConfig,
  CreateAgentWizardProps,
  GeneratedConfigPreview,
  WizardConfig,
} from "./types"

const STEP_TITLES = [
  "Vamos criar seu agente",
  "Como voce quer criar?",
  "Configurar agente",
  "Pronto pra criar?",
] as const

const EMPTY_CONFIG: WizardConfig = {
  name: "",
  description: "",
  templateId: null,
  aiDescription: "",
}

function buildAuthHeaders(): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

/**
 * Channel selection at creation (2026-06-09).
 *
 * Channels do NOT flow through the Create schema — the backend only accepts
 * them via the dedicated PATCH /agents/{id}/{channel}/enabled endpoints (same
 * shape the agent-card toggle hooks use: body `{ "<channel>_enabled": true }`,
 * `triagem_invite` -> URL segment `triagem-invite`). We fire one PATCH per
 * enabled channel AFTER the agent exists, in parallel. Failures are NON-blocking
 * (the agent is already created) but NOT silently swallowed: returns the list of
 * channels that failed so the caller can surface a toast.
 */
async function enableSelectedChannels(
  agentId: string,
  channels: WizardConfig["channels"],
): Promise<string[]> {
  if (!agentId || !channels) return []
  const enabled = (Object.keys(channels) as Array<keyof NonNullable<WizardConfig["channels"]>>).filter(
    (k) => channels[k],
  )
  if (enabled.length === 0) return []
  const results = await Promise.allSettled(
    enabled.map((channel) => {
      const urlSegment = channel === "triagem_invite" ? "triagem-invite" : channel
      const bodyKey = `${channel}_enabled`
      return fetch(
        `/api/backend-proxy/agent-studio/agents/${encodeURIComponent(agentId)}/${urlSegment}/enabled`,
        {
          method: "PATCH",
          headers: buildAuthHeaders(),
          body: JSON.stringify({ [bodyKey]: true }),
        },
      ).then((res) => {
        if (!res.ok) throw new Error(`channel ${channel} HTTP ${res.status}`)
        return channel
      })
    }),
  )
  const failed: string[] = []
  results.forEach((r, i) => {
    if (r.status === "rejected") {
      failed.push(enabled[i])
      console.warn(`[CreateAgentWizard] failed to enable channel "${enabled[i]}":`, r.reason)
    }
  })
  return failed
}

function canProceed(
  step: number,
  goal: AgentGoal | null,
  approach: AgentApproach | null,
  config: WizardConfig,
  aiPreview: GeneratedConfigPreview | null,
): boolean {
  if (step === 1) return goal !== null
  if (step === 2) {
    if (approach === "ai") return config.aiDescription.trim().length >= 10
    if (approach === "template") return config.templateId !== null
    if (approach === "manual") return true
    return false
  }
  if (step === 3) {
    if (approach === "ai") return aiPreview !== null && config.name.trim().length > 0
    if (approach === "template") return config.name.trim().length > 0
    if (approach === "manual") return config.name.trim().length > 0
    return false
  }
  return true
}

/**
 * T4 — derive starting step + state from optional `initialConfig`.
 *
 * When TemplateClonePanel passes a templateId (clone-first flow), we jump
 * the wizard straight to step 3 (Configurar) with the template's config
 * pre-populated. Otherwise the wizard starts at step 1 (goal selection)
 * just like before.
 */
function deriveInitialState(
  initialGoal: AgentGoal | undefined,
  initialConfig: CreateAgentInitialConfig | undefined,
): {
  step: number
  goal: AgentGoal | null
  approach: AgentApproach | null
  config: WizardConfig
} {
  if (initialConfig?.templateId) {
    // Clone-first: skip goal + approach, open at Configurar
    const goal = initialConfig.goal ?? initialGoal ?? "outro"
    return {
      step: 3,
      goal,
      approach: initialConfig.approach ?? "template",
      config: {
        name: initialConfig.name ?? "",
        description: initialConfig.description ?? "",
        templateId: initialConfig.templateId,
        aiDescription: initialConfig.aiDescription ?? "",
      },
    }
  }

  return {
    step: 1,
    goal: initialGoal ?? null,
    approach: null,
    config: EMPTY_CONFIG,
  }
}

export function CreateAgentWizard({
  open,
  onClose,
  onCreated,
  initialGoal,
  initialConfig,
}: CreateAgentWizardProps) {
  const { templates: AGENT_TEMPLATES } = useLegacyAgentTemplates()
  const initial = deriveInitialState(initialGoal, initialConfig)
  const [step, setStep] = useState(initial.step)
  const [goal, setGoal] = useState<AgentGoal | null>(initial.goal)
  const [approach, setApproach] = useState<AgentApproach | null>(initial.approach)
  const [config, setConfig] = useState<WizardConfig>(initial.config)
  const [aiPreview, setAiPreview] = useState<GeneratedConfigPreview | null>(null)
  const [isGeneratingAI, setIsGeneratingAI] = useState(false)
  const [aiError, setAiError] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)

  // Reset when wizard re-opens (UX-Sprint-A QW#11 audit pattern: wizards
  // sempre limpam state ao abrir pra evitar carry-over confuso entre
  // sessoes diferentes de criacao). T4: respeita `initialConfig` para
  // clone-first abrir no step 3.
  useEffect(() => {
    if (open) {
      const next = deriveInitialState(initialGoal, initialConfig)
      setStep(next.step)
      setGoal(next.goal)
      setApproach(next.approach)
      setConfig(next.config)
      setAiPreview(null)
      setAiError(null)
      setIsGeneratingAI(false)
      setIsCreating(false)
    }
  }, [open, initialGoal, initialConfig])

  const handleGenerateAI = async () => {
    if (config.aiDescription.trim().length < 10) return
    setIsGeneratingAI(true)
    setAiError(null)
    setAiPreview(null)
    try {
      const res = await fetch("/api/backend-proxy/custom-agents/generate", {
        method: "POST",
        headers: buildAuthHeaders(),
        body: JSON.stringify({ description: config.aiDescription }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(extractErrorMessage(err, res.status))
      }
      const data = (await res.json()) as GeneratedConfigPreview
      if (!data || typeof data !== "object") {
        throw new Error("Resposta inesperada do backend ao gerar agente")
      }
      setAiPreview(data)
      // Pre-populate name field if backend provided one
      if (data.suggested_name && !config.name) {
        setConfig({ ...config, name: data.suggested_name })
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Erro ao gerar configuração"
      setAiError(msg)
    } finally {
      setIsGeneratingAI(false)
    }
  }

  const handleCreate = async () => {
    if (!approach || !goal) return
    setIsCreating(true)
    try {
      if (approach === "ai") {
        if (!aiPreview) throw new Error("Configuracao IA nao gerada")
        const res = await fetch("/api/backend-proxy/custom-agents", {
          method: "POST",
          headers: buildAuthHeaders(),
          body: JSON.stringify({
            name: config.name || aiPreview.suggested_name || "Novo Agente",
            role: aiPreview.suggested_role ?? config.aiDescription.slice(0, 200),
            description: aiPreview.suggested_role ?? config.aiDescription.slice(0, 200),
            system_prompt: aiPreview.suggested_prompt ?? "",
            allowed_tools: aiPreview.suggested_tools ?? [
              "search_candidates",
              "get_candidate_details",
            ],
            domain: aiPreview.suggested_domain ?? "general",
            context_level: aiPreview.suggested_context_level ?? "standard",
            max_steps: aiPreview.suggested_max_steps ?? 8,
            temperature: aiPreview.suggested_temperature ?? 0.5,
          }),
        })
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(extractErrorMessage(err, res.status))
        }
        const data = await res.json()
        toast.success(`Agente "${config.name || "Novo Agente"}" criado`, "Pronto para uso")
        const newAgentId = data?.id ?? ""
        const failedChannels = await enableSelectedChannels(newAgentId, config.channels)
        if (failedChannels.length > 0) {
          toast.warning(
            "Agente criado; alguns canais nao puderam ser ativados",
            "Voce pode tenta-los novamente no card do agente.",
          )
        }
        onCreated?.(newAgentId)
        onClose()
      } else if (approach === "template") {
        const tmpl = AGENT_TEMPLATES.find((t) => t.id === config.templateId)
        if (!tmpl) throw new Error("Template nao encontrado")
        // Templates are catalog-defined in plataforma-lia (lib/agent-templates-data),
        // not sector templates from the FastAPI sectors endpoint. We create the
        // custom agent directly from the template's pre-baked config.
        const res = await fetch("/api/backend-proxy/custom-agents", {
          method: "POST",
          headers: buildAuthHeaders(),
          body: JSON.stringify(
            buildCreateAgentPayloadFromTemplate(tmpl, config.name || tmpl.name),
          ),
        })
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(extractErrorMessage(err, res.status))
        }
        const data = await res.json()
        toast.success(`Agente "${config.name || tmpl.name}" criado`, "A partir de template")
        const newAgentId = data?.id ?? ""
        const failedChannels = await enableSelectedChannels(newAgentId, config.channels)
        if (failedChannels.length > 0) {
          toast.warning(
            "Agente criado; alguns canais nao puderam ser ativados",
            "Voce pode tenta-los novamente no card do agente.",
          )
        }
        onCreated?.(newAgentId)
        onClose()
      } else {
        // approach === "manual" — create minimal custom agent, user finishes in editor
        const res = await fetch("/api/backend-proxy/custom-agents", {
          method: "POST",
          headers: buildAuthHeaders(),
          body: JSON.stringify({
            name: config.name,
            role: config.description || config.name,
            description: config.description || config.name,
            system_prompt: "",
            allowed_tools: ["search_candidates", "get_candidate_details"],
            domain: "general",
            context_level: "standard",
            max_steps: 8,
            temperature: 0.5,
          }),
        })
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(extractErrorMessage(err, res.status))
        }
        const data = await res.json()
        toast.success(`Agente "${config.name}" criado`, "Configure os detalhes no editor avancado")
        const newAgentId = data?.id ?? ""
        const failedChannels = await enableSelectedChannels(newAgentId, config.channels)
        if (failedChannels.length > 0) {
          toast.warning(
            "Agente criado; alguns canais nao puderam ser ativados",
            "Voce pode tenta-los novamente no card do agente.",
          )
        }
        onCreated?.(newAgentId)
        onClose()
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Erro ao criar agente"
      toast.error(msg, "Tente novamente")
    } finally {
      setIsCreating(false)
    }
  }

  const handleNext = () => setStep((s) => Math.min(s + 1, 4))
  // T4 clone-first: quando o wizard começou no step 3 (initialConfig.templateId),
  // o "Voltar" não deve voltar para steps 1/2 — não há goal/approach selecionável
  // pelo usuário nesse fluxo. Limita o piso ao step inicial.
  const minStep = initialConfig?.templateId ? 3 : 1
  const handleBack = () => setStep((s) => Math.max(s - 1, minStep))

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent
        className="max-w-2xl bg-lia-bg-primary border border-lia-border-medium shadow-lia-lg rounded-xl p-6"
        data-testid="create-agent-wizard"
      >
        <DialogHeader>
          <DialogTitle className="text-base font-semibold text-lia-text-primary">
            {STEP_TITLES[step - 1]}
          </DialogTitle>
          <DialogDescription className="text-xs text-lia-text-disabled" data-testid="wizard-step-indicator">
            Etapa {step} de 4
          </DialogDescription>
        </DialogHeader>

        {/* Progress dots — visual + screen-reader friendly */}
        <div
          className="flex items-center gap-2 pb-2"
          role="progressbar"
          aria-valuenow={step}
          aria-valuemin={1}
          aria-valuemax={4}
          aria-label={`Etapa ${step} de 4`}
        >
          {[1, 2, 3, 4].map((s) => (
            <div
              key={s}
              className={cn(
                "h-1 flex-1 rounded-full transition-colors duration-200",
                s <= step ? "bg-graphite" : "bg-lia-bg-tertiary",
              )}
              aria-hidden="true"
            />
          ))}
        </div>

        <div className="py-4 max-h-[60vh] overflow-y-auto" data-testid="wizard-step-content">
          {step === 1 && <GoalStep goal={goal} onSelect={setGoal} />}
          {step === 2 && goal && (
            <ApproachStep
              goal={goal}
              approach={approach}
              config={config}
              onSelect={setApproach}
              setConfig={setConfig}
            />
          )}
          {step === 3 && goal && approach && (
            <ConfigStep
              approach={approach}
              goal={goal}
              config={config}
              setConfig={setConfig}
              aiPreview={aiPreview}
              isGeneratingAI={isGeneratingAI}
              aiError={aiError}
              onGenerateAI={handleGenerateAI}
            />
          )}
          {step === 4 && goal && approach && (
            <PreviewStep goal={goal} approach={approach} config={config} aiPreview={aiPreview} />
          )}
        </div>

        <DialogFooter className="flex items-center justify-between gap-2">
          <div>
            {step > minStep && (
              <Button
                variant="ghost"
                onClick={handleBack}
                disabled={isCreating || isGeneratingAI}
                data-testid="wizard-back-button"
              >
                Voltar
              </Button>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={onClose}
              disabled={isCreating}
              data-testid="wizard-cancel-button"
            >
              Cancelar
            </Button>
            {step < 4 ? (
              <Button
                onClick={handleNext}
                disabled={!canProceed(step, goal, approach, config, aiPreview) || isGeneratingAI}
                data-testid="wizard-next-button"
                className="bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover"
              >
                Proximo
              </Button>
            ) : (
              <Button
                onClick={handleCreate}
                disabled={isCreating}
                data-testid="wizard-create-button"
                className="bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover"
              >
                {isCreating ? "Criando..." : "Criar agente"}
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
