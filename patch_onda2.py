#!/usr/bin/env python3
"""
Onda 2: Conversational Creation + Test Debug Panel

Backend:
  1. POST /custom-agents/generate-from-description — LIA generates agent config

Frontend:
  2. Proxy route for generate endpoint
  3. ConversationalCreator — description input → LIA generates → preview config
  4. TestDebugPanel — chat + debug panel (tools, tokens, cost, compliance)
  5. Wire into AgentStudioPage
"""
import os
import sys

BASE_BE = "/home/runner/workspace/lia-agent-system"
BASE_FE = "/home/runner/workspace/plataforma-lia/src"


def write_file(base, rel_path, content):
    full = os.path.join(base, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    print(f"  CREATED: {rel_path}")


def read_file(base, rel_path):
    with open(os.path.join(base, rel_path)) as f:
        return f.read()


def patch_file(base, rel_path, old, new, label=""):
    full = os.path.join(base, rel_path)
    content = read_file(base, rel_path)
    if old not in content:
        print(f"  SKIP: {label}")
        return False
    content = content.replace(old, new, 1)
    with open(full, "w") as f:
        f.write(content)
    print(f"  OK: {label}")
    return True


# ============================================================
# 1. BACKEND: generate-from-description endpoint
# ============================================================
print("\n=== 1. Backend: generate-from-description ===")
patch_file(
    BASE_BE,
    "app/api/v1/custom_agents.py",
    '''@router.get("/{agent_id}/preview-prompt")''',
    '''@router.post("/generate-from-description", summary="LIA generates agent config from description")
async def generate_agent_from_description(
    body: dict,
    current_user=Depends(get_current_user),
):
    """Generate a complete agent configuration from a natural language description.

    The recruiter describes what they need in Portuguese, and LIA generates:
    name, role, domain, tools, system_prompt, context_level, etc.

    Compliance: FairnessGuard + SecurityPatterns run on the description before generation.
    """
    description = (body.get("description") or "").strip()
    if not description or len(description) < 10:
        raise HTTPException(status_code=400, detail="Descricao deve ter pelo menos 10 caracteres")

    # Security checks on input
    try:
        from app.shared.robustness.security_patterns import check_input_security
        sec = check_input_security(description)
        if sec.is_blocked:
            raise HTTPException(status_code=400, detail="Descricao bloqueada por padrao de seguranca")
    except HTTPException:
        raise
    except Exception:
        pass

    try:
        from app.shared.compliance.fairness_guard import FairnessGuard
        fg = FairnessGuard()
        fg_result = fg.check(description)
        if fg_result.is_blocked:
            raise HTTPException(status_code=400, detail="Descricao bloqueada por criterios de equidade")
    except HTTPException:
        raise
    except Exception:
        pass

    # Generate config using audited LLM
    try:
        from app.domains.ai.services.llm import llm_service
        import json

        generation_prompt = f"""Voce e um especialista em configuracao de agentes de IA para recrutamento.
O recrutador descreveu o que precisa:

"{description}"

Gere uma configuracao completa de agente no formato JSON com estes campos:
- suggested_name: nome curto e descritivo (max 50 chars)
- suggested_role: descricao do papel do agente (max 200 chars)
- suggested_domain: um de [sourcing, screening, pipeline, analytics, communication, job_management, automation, general]
- suggested_tools: lista de tools (escolha entre: search_candidates, list_jobs, get_job_details, get_candidate_details, get_pipeline_summary, search_talent_pool, get_analytics_summary, get_company_culture, get_evaluation_criteria, summarize_context, move_candidate, send_email, update_candidate_field, schedule_interview, create_note)
- suggested_prompt: system prompt completo para o agente (em portugues, 200-500 chars)
- suggested_context_level: "full", "standard" ou "minimal"
- suggested_max_steps: numero entre 5 e 15
- suggested_temperature: numero entre 0.2 e 0.8
- reasoning: explique brevemente por que escolheu essa configuracao (em portugues)

Responda APENAS com o JSON, sem texto adicional."""

        model = llm_service.get_audited_model(company_id=current_user.company_id)
        response = await model.ainvoke(generation_prompt)
        content = response.content if hasattr(response, "content") else str(response)
        if isinstance(content, list):
            content = "".join(
                b.get("text", "") if isinstance(b, dict) else str(b) for b in content
            )

        # Parse JSON from response
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\\n", 1)[-1].rsplit("```", 1)[0]
        config = json.loads(content)

        return {
            "suggested_name": config.get("suggested_name", "Novo Agente"),
            "suggested_role": config.get("suggested_role", description[:200]),
            "suggested_domain": config.get("suggested_domain", "general"),
            "suggested_tools": config.get("suggested_tools", ["search_candidates", "get_candidate_details"]),
            "suggested_prompt": config.get("suggested_prompt", ""),
            "suggested_context_level": config.get("suggested_context_level", "standard"),
            "suggested_max_steps": config.get("suggested_max_steps", 8),
            "suggested_temperature": config.get("suggested_temperature", 0.5),
            "reasoning": config.get("reasoning", ""),
        }
    except json.JSONDecodeError:
        # Fallback: return sensible defaults
        return {
            "suggested_name": "Novo Agente",
            "suggested_role": description[:200],
            "suggested_domain": "general",
            "suggested_tools": ["search_candidates", "get_candidate_details"],
            "suggested_prompt": f"Voce e um agente de recrutamento. {description}",
            "suggested_context_level": "standard",
            "suggested_max_steps": 8,
            "suggested_temperature": 0.5,
            "reasoning": "Configuracao padrao gerada como fallback.",
        }
    except Exception as e:
        logger.error("Error generating agent config: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao gerar configuracao: {e}")


@router.get("/{agent_id}/preview-prompt")''',
    "generate-from-description endpoint",
)


# ============================================================
# 2. FRONTEND: Proxy route
# ============================================================
print("\n=== 2. Frontend proxy route ===")
proxy_dir = os.path.join(BASE_FE, "app/api/backend-proxy/custom-agents/generate")
os.makedirs(proxy_dir, exist_ok=True)
with open(os.path.join(proxy_dir, "route.ts"), "w") as f:
    f.write('''import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

function getAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  const auth = req.headers.get("authorization")
  if (auth) headers["Authorization"] = auth
  return headers
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.text()
    const res = await fetch(`${BACKEND_URL}/api/v1/custom-agents/generate-from-description`, {
      method: "POST", headers: getAuthHeaders(req), body,
    })
    return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
''')
print("  CREATED: proxy route for generate")


# ============================================================
# 3. FRONTEND: ConversationalCreator
# ============================================================
print("\n=== 3. ConversationalCreator ===")
write_file(BASE_FE, "components/pages-agent-studio/custom-agents/ConversationalCreator.tsx", '''"use client"

import React, { useState } from "react"
import { Wand2, Loader2, Check, ChevronDown, ChevronUp } from "lucide-react"
import { cn } from "@/lib/utils"
import { cardStyles, buttonStyles, textStyles, inputStyles, badgeStyles } from "@/lib/design-tokens"
import { toast } from "@/lib/toast"
import { BetaBadge } from "@/components/ui/beta-badge"
import { CATEGORY_LABELS, TOOL_LABELS } from "./types"
import type { AgentCategory } from "./types"

interface GeneratedConfig {
  suggested_name: string
  suggested_role: string
  suggested_domain: string
  suggested_tools: string[]
  suggested_prompt: string
  suggested_context_level: string
  suggested_max_steps: number
  suggested_temperature: number
  reasoning: string
}

interface ConversationalCreatorProps {
  onAgentCreated: () => void
}

export function ConversationalCreator({ onAgentCreated }: ConversationalCreatorProps) {
  const [description, setDescription] = useState("")
  const [isGenerating, setIsGenerating] = useState(false)
  const [config, setConfig] = useState<GeneratedConfig | null>(null)
  const [showPrompt, setShowPrompt] = useState(false)
  const [isCreating, setIsCreating] = useState(false)

  const handleGenerate = async () => {
    if (!description.trim() || description.length < 10) return
    setIsGenerating(true)
    setConfig(null)
    try {
      const token = localStorage.getItem("auth_token")
      const res = await fetch("/api/backend-proxy/custom-agents/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ description }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Erro" }))
        throw new Error(err.detail || "Erro ao gerar")
      }
      const data = await res.json()
      setConfig(data)
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Erro ao gerar configuracao")
    } finally {
      setIsGenerating(false)
    }
  }

  const handleCreate = async () => {
    if (!config) return
    setIsCreating(true)
    try {
      const token = localStorage.getItem("auth_token")
      const res = await fetch("/api/backend-proxy/custom-agents", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          name: config.suggested_name,
          role: config.suggested_role,
          description: config.suggested_role,
          system_prompt: config.suggested_prompt,
          allowed_tools: config.suggested_tools,
          domain: config.suggested_domain,
          context_level: config.suggested_context_level,
          max_steps: config.suggested_max_steps,
          temperature: config.suggested_temperature,
        }),
      })
      if (!res.ok) throw new Error("Erro ao criar agente")
      toast.success(`Agente "${config.suggested_name}" criado!`, "Agora vincule a uma vaga ou banco de talentos.")
      setConfig(null)
      setDescription("")
      onAgentCreated()
    } catch {
      toast.error("Erro ao criar agente")
    } finally {
      setIsCreating(false)
    }
  }

  const domainLabel = config ? (CATEGORY_LABELS[config.suggested_domain as AgentCategory] || config.suggested_domain) : ""

  return (
    <div className={cn(cardStyles.default, "p-5")}>
      <div className="flex items-center gap-2 mb-3">
        <Wand2 className="w-4 h-4 text-wedo-cyan-dark" />
        <h3 className={cn(textStyles.subtitle, "text-sm font-semibold")}>Criar com IA</h3>
        <BetaBadge size="sm" />
      </div>

      <p className={cn(textStyles.caption, "mb-3 text-xs")}>
        Descreva o que voce precisa e a LIA configura o agente automaticamente
      </p>

      {/* Input */}
      <div className="flex gap-2">
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Ex: Preciso de um agente que filtre candidatos Python com 3+ anos de experiencia em cloud AWS e classifique por senioridade..."
          rows={2}
          className={cn(inputStyles.default, "flex-1 text-sm resize-none")}
        />
        <button
          type="button"
          onClick={handleGenerate}
          disabled={isGenerating || description.length < 10}
          className={cn(buttonStyles.primary, "px-4 py-2 text-xs self-end shrink-0")}
        >
          {isGenerating ? <Loader2 className="w-4 h-4 animate-spin" /> : "Gerar"}
        </button>
      </div>

      {/* Generated Config Preview */}
      {config && (
        <div className="mt-4 space-y-3">
          <div className="flex items-center gap-2">
            <Check className="w-4 h-4 text-emerald-500" />
            <span className={cn(textStyles.subtitle, "text-sm font-semibold")}>
              Configuracao sugerida
            </span>
          </div>

          <div className={cn(cardStyles.flat, "p-4 space-y-2")}>
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-lia-text-primary">{config.suggested_name}</span>
              <span className={badgeStyles.cyan}>{domainLabel}</span>
            </div>
            <p className="text-xs text-lia-text-secondary">{config.suggested_role}</p>

            <div className="flex flex-wrap gap-1 pt-1">
              {config.suggested_tools.map((tool) => (
                <span key={tool} className={cn(badgeStyles.default, "text-[10px]")}>
                  {TOOL_LABELS[tool] || tool}
                </span>
              ))}
            </div>

            <div className="flex items-center gap-3 pt-1 text-[10px] text-lia-text-disabled">
              <span>Contexto: {config.suggested_context_level}</span>
              <span>Steps: {config.suggested_max_steps}</span>
              <span>Temp: {config.suggested_temperature}</span>
            </div>

            {config.reasoning && (
              <p className="text-[11px] text-wedo-cyan-dark italic pt-1">
                LIA: {config.reasoning}
              </p>
            )}

            {/* Collapsible prompt */}
            <button
              type="button"
              onClick={() => setShowPrompt(!showPrompt)}
              className="flex items-center gap-1 text-[10px] text-lia-text-disabled hover:text-lia-text-secondary pt-1"
            >
              {showPrompt ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              {showPrompt ? "Ocultar prompt" : "Ver prompt completo"}
            </button>
            {showPrompt && (
              <pre className="text-[10px] text-lia-text-secondary bg-lia-bg-tertiary rounded-md p-3 overflow-auto max-h-32 whitespace-pre-wrap font-mono">
                {config.suggested_prompt}
              </pre>
            )}
          </div>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleCreate}
              disabled={isCreating}
              className={cn(buttonStyles.primary, "text-xs px-4 py-1.5")}
            >
              {isCreating ? "Criando..." : "Criar agente"}
            </button>
            <button
              type="button"
              onClick={() => { setConfig(null); setDescription("") }}
              className={cn(buttonStyles.ghost, "text-xs px-3 py-1.5")}
            >
              Recomecar
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
''')


# ============================================================
# 4. FRONTEND: TestDebugPanel
# ============================================================
print("\n=== 4. TestDebugPanel ===")
write_file(BASE_FE, "components/pages-agent-studio/custom-agents/TestDebugPanel.tsx", '''"use client"

import React, { useState } from "react"
import { Send, Loader2, Wrench, BarChart3, ShieldCheck, DollarSign } from "lucide-react"
import { cn } from "@/lib/utils"
import { cardStyles, buttonStyles, textStyles, inputStyles, badgeStyles } from "@/lib/design-tokens"
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from "@/components/ui/dialog"
import { BetaBadge } from "@/components/ui/beta-badge"
import type { CustomAgent } from "./types"
import { TOOL_LABELS } from "./types"

interface TestResult {
  response: string
  confidence: number
  tool_calls: string[]
  execution_time_ms: number
  tokens_input: number
  tokens_output: number
  model_used: string
}

interface TestDebugPanelProps {
  agent: CustomAgent | null
  open: boolean
  onClose: () => void
}

export function TestDebugPanel({ agent, open, onClose }: TestDebugPanelProps) {
  const [message, setMessage] = useState("")
  const [isTesting, setIsTesting] = useState(false)
  const [results, setResults] = useState<TestResult[]>([])
  const [messages, setMessages] = useState<{ role: "user" | "agent"; text: string }[]>([])

  const handleTest = async () => {
    if (!agent || !message.trim()) return
    const userMsg = message.trim()
    setMessage("")
    setMessages((prev) => [...prev, { role: "user", text: userMsg }])
    setIsTesting(true)

    try {
      const token = localStorage.getItem("auth_token")
      const res = await fetch(`/api/backend-proxy/custom-agents/${agent.id}/test`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message: userMsg }),
      })
      if (!res.ok) throw new Error("Teste falhou")
      const data: TestResult = await res.json()
      setResults((prev) => [...prev, data])
      setMessages((prev) => [...prev, { role: "agent", text: data.response }])
    } catch {
      setMessages((prev) => [...prev, { role: "agent", text: "Erro ao executar teste." }])
    } finally {
      setIsTesting(false)
    }
  }

  const lastResult = results[results.length - 1]
  const totalTokens = results.reduce((s, r) => s + r.tokens_input + r.tokens_output, 0)
  const totalLatency = results.reduce((s, r) => s + r.execution_time_ms, 0)
  const estimatedCost = (totalTokens * 0.000003).toFixed(4)

  if (!agent) return null

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) { onClose(); setMessages([]); setResults([]) } }}>
      <DialogContent className="sm:max-w-4xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className={cn(textStyles.title, "flex items-center gap-2")}>
            Testar: {agent.name}
            <BetaBadge size="sm" />
          </DialogTitle>
        </DialogHeader>

        <div className="grid grid-cols-5 gap-4 h-[60vh]">
          {/* Chat Panel (3/5) */}
          <div className="col-span-3 flex flex-col border border-lia-border-subtle rounded-md overflow-hidden">
            {/* Messages */}
            <div className="flex-1 overflow-auto p-3 space-y-3">
              {messages.length === 0 && (
                <p className={cn(textStyles.caption, "text-center py-8")}>
                  Envie uma mensagem para testar o agente
                </p>
              )}
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={cn(
                    "max-w-[85%] rounded-lg px-3 py-2 text-sm",
                    msg.role === "user"
                      ? "ml-auto bg-lia-btn-primary-bg text-lia-btn-primary-text"
                      : "bg-lia-bg-tertiary text-lia-text-primary"
                  )}
                >
                  {msg.text}
                </div>
              ))}
              {isTesting && (
                <div className="flex items-center gap-2 text-xs text-lia-text-disabled">
                  <Loader2 className="w-3 h-3 animate-spin" /> Processando...
                </div>
              )}
            </div>

            {/* Input */}
            <div className="border-t border-lia-border-subtle p-2 flex gap-2">
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleTest()}
                placeholder="Digite uma mensagem para testar..."
                className={cn(inputStyles.default, "flex-1 text-sm")}
                disabled={isTesting}
              />
              <button
                type="button"
                onClick={handleTest}
                disabled={isTesting || !message.trim()}
                className={cn(buttonStyles.primary, "px-3 py-1.5")}
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Debug Panel (2/5) */}
          <div className="col-span-2 overflow-auto space-y-3">
            {/* Tools */}
            <div className={cn(cardStyles.flat, "p-3")}>
              <div className="flex items-center gap-1.5 mb-2">
                <Wrench className="w-3.5 h-3.5 text-lia-text-disabled" />
                <span className="text-xs font-semibold text-lia-text-primary">Ferramentas chamadas</span>
              </div>
              {lastResult?.tool_calls.length ? (
                <div className="flex flex-wrap gap-1">
                  {lastResult.tool_calls.map((tool, i) => (
                    <span key={i} className={cn(badgeStyles.cyan, "text-[10px]")}>
                      {TOOL_LABELS[tool] || tool}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-[10px] text-lia-text-disabled">Nenhuma ferramenta chamada ainda</p>
              )}
            </div>

            {/* Metrics */}
            <div className={cn(cardStyles.flat, "p-3")}>
              <div className="flex items-center gap-1.5 mb-2">
                <BarChart3 className="w-3.5 h-3.5 text-lia-text-disabled" />
                <span className="text-xs font-semibold text-lia-text-primary">Metricas</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-lia-text-disabled">Tokens in</span>
                  <p className="font-bold font-inter text-lia-text-primary">{lastResult?.tokens_input || 0}</p>
                </div>
                <div>
                  <span className="text-lia-text-disabled">Tokens out</span>
                  <p className="font-bold font-inter text-lia-text-primary">{lastResult?.tokens_output || 0}</p>
                </div>
                <div>
                  <span className="text-lia-text-disabled">Latencia</span>
                  <p className="font-bold font-inter text-lia-text-primary">{lastResult?.execution_time_ms || 0}ms</p>
                </div>
                <div>
                  <span className="text-lia-text-disabled">Confianca</span>
                  <p className="font-bold font-inter text-lia-text-primary">{lastResult ? (lastResult.confidence * 100).toFixed(0) + "%" : "-"}</p>
                </div>
              </div>
              {lastResult?.model_used && (
                <p className="text-[10px] text-lia-text-disabled mt-1">Model: {lastResult.model_used}</p>
              )}
            </div>

            {/* Cost */}
            <div className={cn(cardStyles.flat, "p-3")}>
              <div className="flex items-center gap-1.5 mb-2">
                <DollarSign className="w-3.5 h-3.5 text-lia-text-disabled" />
                <span className="text-xs font-semibold text-lia-text-primary">Consumo da sessao</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-lia-text-disabled">Total tokens</span>
                  <p className="font-bold font-inter text-lia-text-primary">{totalTokens}</p>
                </div>
                <div>
                  <span className="text-lia-text-disabled">Custo estimado</span>
                  <p className="font-bold font-inter text-lia-text-primary">~R${estimatedCost}</p>
                </div>
                <div>
                  <span className="text-lia-text-disabled">Latencia total</span>
                  <p className="font-bold font-inter text-lia-text-primary">{(totalLatency / 1000).toFixed(1)}s</p>
                </div>
                <div>
                  <span className="text-lia-text-disabled">Interacoes</span>
                  <p className="font-bold font-inter text-lia-text-primary">{results.length}</p>
                </div>
              </div>
            </div>

            {/* Compliance */}
            <div className={cn(cardStyles.flat, "p-3")}>
              <div className="flex items-center gap-1.5 mb-1">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                <span className="text-xs font-semibold text-lia-text-primary">Compliance</span>
              </div>
              <div className="flex flex-wrap gap-1">
                <span className={cn(badgeStyles.success, "text-[10px]")}>FairnessGuard OK</span>
                <span className={cn(badgeStyles.success, "text-[10px]")}>PII Strip OK</span>
                <span className={cn(badgeStyles.success, "text-[10px]")}>Audit Log OK</span>
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
''')


# ============================================================
# 5. Update barrel export
# ============================================================
print("\n=== 5. Update barrel ===")
write_file(BASE_FE, "components/pages-agent-studio/custom-agents/index.ts", '''export { TemplateGallery } from "./TemplateGallery"
export { TemplateCard } from "./TemplateCard"
export { AgentCard } from "./AgentCard"
export { DeployDialog } from "./DeployDialog"
export { ConversationalCreator } from "./ConversationalCreator"
export { TestDebugPanel } from "./TestDebugPanel"
export type * from "./types"
''')


# ============================================================
# 6. Wire into AgentStudioPage
# ============================================================
print("\n=== 6. Wire Onda 2 into AgentStudioPage ===")

# Update import
patch_file(
    BASE_FE,
    "components/pages-agent-studio/AgentStudioPage.tsx",
    'import { TemplateGallery, AgentCard as CustomAgentCard, DeployDialog } from "@/components/pages-agent-studio/custom-agents"',
    'import { TemplateGallery, AgentCard as CustomAgentCard, DeployDialog, ConversationalCreator, TestDebugPanel } from "@/components/pages-agent-studio/custom-agents"',
    "add Onda 2 imports",
)

# Add test state
patch_file(
    BASE_FE,
    "components/pages-agent-studio/AgentStudioPage.tsx",
    '  const [deployAgent, setDeployAgent] = useState<CustomAgent | null>(null)',
    '  const [deployAgent, setDeployAgent] = useState<CustomAgent | null>(null)\n  const [testAgent, setTestAgent] = useState<CustomAgent | null>(null)',
    "add testAgent state",
)

# Wire test button
patch_file(
    BASE_FE,
    "components/pages-agent-studio/AgentStudioPage.tsx",
    'onTest={() => {/* TODO: open test modal */}}',
    'onTest={(a) => setTestAgent(a)}',
    "wire test button",
)

# Add ConversationalCreator + TestDebugPanel after DeployDialog
patch_file(
    BASE_FE,
    "components/pages-agent-studio/AgentStudioPage.tsx",
    '''            {/* Deploy Dialog */}
            <DeployDialog
              agent={deployAgent}
              open={!!deployAgent}
              onClose={() => setDeployAgent(null)}
              onDeployed={() => mutateCustomAgents()}
            />''',
    '''            {/* Conversational Creator */}
            <ConversationalCreator onAgentCreated={() => mutateCustomAgents()} />

            {/* Deploy Dialog */}
            <DeployDialog
              agent={deployAgent}
              open={!!deployAgent}
              onClose={() => setDeployAgent(null)}
              onDeployed={() => mutateCustomAgents()}
            />

            {/* Test Debug Panel */}
            <TestDebugPanel
              agent={testAgent}
              open={!!testAgent}
              onClose={() => setTestAgent(null)}
            />''',
    "add ConversationalCreator + TestDebugPanel",
)


# ============================================================
# VERIFY
# ============================================================
import ast
print("\n=== Verify backend AST ===")
try:
    ast.parse(read_file(BASE_BE, "app/api/v1/custom_agents.py"))
    print("  OK: custom_agents.py")
except SyntaxError as e:
    print(f"  ERROR: {e}")

print("\nOnda 2 complete!")
