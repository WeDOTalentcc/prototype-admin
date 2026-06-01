"use client"

/**
 * HiringPoliciesHub — Políticas de Recrutamento (estruturada + instruções LIA)
 *
 * P1 dedup: superfície ESTRUTURADA canônica (bloco "policy" via MinhaEmpresaCard).
 * P3b: seção "Instruções para a LIA" — 11 conceitos narrativos (texto livre) em
 *   CompanyHiringPolicy.policy_instructions (separado dos gates). Consumidos por
 *   build_company_agent_context. Endpoint PATCH /hiring-policy/instructions.
 * P3c: instruções renderizadas pelo card unificado ConfigurableFieldCard.
 */

import React from "react"
import { FileText, RefreshCw, Sparkles } from "lucide-react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useCompanySettingsCards } from "@/hooks/settings/use-company-settings-cards"
import { MinhaEmpresaCard } from "@/components/settings/MinhaEmpresaCard"
import { HubHeader, HubLoadingState, HubErrorState, ConfigurableFieldCard } from "./_shared"
import { SettingsEditModeToggle } from "@/components/settings/SettingsEditModeToggle"
import { useSettingsEditMode } from "@/hooks/settings/useSettingsEditMode"
import { SETTINGS_QUERY_KEYS, dispatchSettingsUpdate } from "@/hooks/settings/useSettingsBroadcast"

// ── 11 conceitos narrativos de política (instruções para a LIA) ──────────────
interface InstructionDef { key: string; label: string; hint: string; placeholder: string }
const POLICY_INSTRUCTIONS: InstructionDef[] = [
  { key: "screening_criteria", label: "Critérios mínimos de triagem", hint: "Requisitos de formação, experiência ou comportamento que a LIA usa como filtro.", placeholder: "Ex: Mínimo 3 anos em gestão de projetos, inglês avançado..." },
  { key: "candidate_feedback_policy", label: "Feedback a candidatos reprovados", hint: "Nível de transparência com candidatos não avançados.", placeholder: "Ex: Reprovados recebem e-mail genérico; quem chegou à entrevista recebe feedback personalizado..." },
  { key: "communication_window", label: "Janela de envio de comunicações (LGPD)", hint: "Dias/horários em que a LIA pode enviar mensagens automáticas.", placeholder: "Ex: Seg a sex, 8h–18h. Sábados até 12h para urgências..." },
  { key: "interview_scheduling_policy", label: "Regras de agendamento de entrevistas", hint: "Como a LIA propõe e confirma horários.", placeholder: "Ex: LIA envia 3 opções; confirmação automática; cancelamento com 12h..." },
  { key: "interview_reminder_policy", label: "Lembretes de entrevista", hint: "Antecedência e canais dos lembretes.", placeholder: "Ex: 24h antes por e-mail e 2h antes por WhatsApp..." },
  { key: "no_show_policy", label: "Política de no-show", hint: "Fluxo de recontato e quando reprovar.", placeholder: "Ex: Recontato por e-mail e WhatsApp; sem resposta em 48h → Reprovado..." },
  { key: "salary_negotiation_policy", label: "Flexibilidade / negociação salarial", hint: "Limites para a LIA orientar expectativas.", placeholder: "Ex: Até 10% acima do base; benefícios fixos..." },
  { key: "remote_work_policy", label: "Política de trabalho remoto", hint: "Modelo de trabalho que a LIA informa aos candidatos.", placeholder: "Ex: Híbrido 3x presencial em SP; TI pode ser 100% remoto..." },
  { key: "data_retention_candidate_policy", label: "Retenção de dados de candidatos (LGPD)", hint: "Prazo de retenção (LGPD Art. 7).", placeholder: "Ex: 12 meses para quem foi à entrevista; 6 meses para triagem; depois anonimizar..." },
  { key: "talent_pool_opt_in_policy", label: "Convite ao banco de talentos (opt-in)", hint: "Quando a LIA convida reprovados para o pool.", placeholder: "Ex: Quem chegou à entrevista recebe convite com clareza sobre como sair..." },
  { key: "diversity_inclusion_guidelines", label: "Diretrizes de diversidade e inclusão", hint: "Políticas afirmativas e grupos prioritários.", placeholder: "Ex: Priorizar PcD, mulheres em tech e pessoas negras; sinalizar se o funil não reflete..." },
]

interface RawPolicy { policy_instructions?: Record<string, string>; [k: string]: unknown }

async function fetchRawPolicy(): Promise<RawPolicy | null> {
  const res = await fetch("/api/backend-proxy/hiring-policy")
  if (res.ok) return res.json()
  return null
}

export function HiringPoliciesHub() {
  // ─── TODOS OS HOOKS PRIMEIRO (rules-of-hooks, CLAUDE.md) ───
  const {
    blocks, benefits, companyId, loading, error,
    recentlyUpdated, editingField, isSavingField,
    startEditing, cancelEditing, saveField, refreshAll, watchdogError,
  } = useCompanySettingsCards()

  const [isExpanded, setIsExpanded] = React.useState(true)
  const { isEditing } = useSettingsEditMode("politicas-recrutamento")
  const queryClient = useQueryClient()

  const { data: rawPolicy } = useQuery({
    queryKey: SETTINGS_QUERY_KEYS.hiringPolicy(),
    queryFn: fetchRawPolicy,
    staleTime: 30_000,
  })

  const [savedInstr, setSavedInstr] = React.useState<Record<string, string>>({})
  const [savingInstr, setSavingInstr] = React.useState<Set<string>>(new Set())

  const policyBlock = React.useMemo(() => blocks.find((b) => b.key === "policy"), [blocks])
  const serverInstr = React.useMemo(
    () => (rawPolicy?.policy_instructions ?? {}) as Record<string, string>,
    [rawPolicy],
  )

  const instrMutation = useMutation({
    mutationFn: async ({ key, value }: { key: string; value: string }) => {
      const res = await fetch("/api/backend-proxy/hiring-policy/instructions", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ instructions: { [key]: value } }),
      })
      if (!res.ok) throw new Error("Falha ao salvar instrução")
    },
    onSuccess: (_d, { key, value }) => {
      setSavedInstr((p) => ({ ...p, [key]: value }))
      setSavingInstr((p) => { const n = new Set(p); n.delete(key); return n })
      queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEYS.hiringPolicy() })
      dispatchSettingsUpdate({ actionId: "save_policy_instruction", section: "hiring_policies", field: key, source: "ui", ts: Date.now() })
    },
    onError: (_e, { key }) => {
      setSavingInstr((p) => { const n = new Set(p); n.delete(key); return n })
    },
  })

  React.useEffect(() => {
    if (typeof window === "undefined") return
    const handler = () => refreshAll()
    window.addEventListener("lia:settings-updated", handler)
    return () => window.removeEventListener("lia:settings-updated", handler)
  }, [refreshAll])

  const saveInstruction = React.useCallback((key: string, value: string) => {
    setSavingInstr((p) => new Set(p).add(key))
    instrMutation.mutate({ key, value })
  }, [instrMutation])

  // ─── EARLY RETURNS — APÓS TODOS OS HOOKS ───
  if (watchdogError) return <HubErrorState message={watchdogError} onRetry={refreshAll} />
  if (loading) return <HubLoadingState message="Carregando políticas de recrutamento..." />
  if (!policyBlock) return <HubErrorState message="Bloco de políticas não encontrado. Tente recarregar." onRetry={refreshAll} />

  return (
    <div className="flex flex-col h-full space-y-4">
      {error && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm bg-status-error/10 text-status-error border border-status-error/30">
          <span>{error}</span>
        </div>
      )}

      <div>
        <HubHeader
          title="Políticas de Recrutamento"
          description="Regras tipadas (triagem, aprovação, agendamento, automação) e instruções de texto livre que a LIA aplica no processo seletivo."
        >
          <div className="flex items-center gap-3">
            <SettingsEditModeToggle hubId="politicas-recrutamento" />
            <button onClick={refreshAll} className="p-1.5 rounded-md hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none" aria-label="Recarregar dados">
              <RefreshCw className="w-4 h-4 text-lia-text-secondary" />
            </button>
          </div>
        </HubHeader>
      </div>

      <div className="grid grid-cols-1 gap-4">
        <MinhaEmpresaCard
          block={policyBlock}
          IconComp={FileText}
          isExpanded={isExpanded}
          recentlyUpdated={recentlyUpdated}
          editingField={editingField}
          isSavingField={isSavingField}
          benefits={benefits}
          companyId={companyId}
          isReadOnly={!isEditing}
          onBenefitsChanged={refreshAll}
          onLogoUploaded={refreshAll}
          onToggle={() => setIsExpanded((v) => !v)}
          onStartEditing={startEditing}
          onCancelEditing={cancelEditing}
          onSaveField={saveField}
        />
      </div>

      {/* P3b/P3c — Instruções narrativas para a LIA (texto livre, fora dos gates) */}
      <div className="rounded-lg border border-lia-border-subtle bg-lia-bg-secondary/40 dark:bg-lia-bg-elevated p-4 space-y-4">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-wedo-cyan" aria-hidden />
          <h3 className="text-sm font-semibold text-lia-text-primary">Instruções para a LIA</h3>
        </div>
        <p className="text-xs text-lia-text-secondary leading-relaxed">
          Orientações em texto livre que a LIA leva em conta no processo. Não são regras
          automáticas (gates) — são contexto que enriquece as decisões e a comunicação da IA.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {POLICY_INSTRUCTIONS.map((q) => {
            const value = savedInstr[q.key] !== undefined ? savedInstr[q.key] : (serverInstr[q.key] ?? "")
            return (
              <ConfigurableFieldCard
                key={q.key}
                data-testid={`instruction-block-${q.key}`}
                label={q.label}
                hint={q.hint}
                placeholder={q.placeholder}
                instruction={value}
                isReadOnly={!isEditing}
                isSaving={savingInstr.has(q.key)}
                onInstructionSave={(text) => saveInstruction(q.key, text)}
              />
            )
          })}
        </div>
      </div>
    </div>
  )
}
