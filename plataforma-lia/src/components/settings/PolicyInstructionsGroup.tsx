"use client"

/**
 * PolicyInstructionsGroup — instruções de PROCESSO para a LIA (V2.2, 2026-06-01).
 *
 * 7 conceitos narrativos de processo (texto livre que orienta a LIA), movidos
 * de Políticas de Recrutamento para LIA & Personalização → "Instruções por Campo"
 * (grupo "Processo"), ao lado dos 34 campos da empresa. Unifica a superfície de
 * instruções num só lugar (Políticas fica só com gates tipados).
 *
 * Store: CompanyHiringPolicy.policy_instructions (coluna separada dos gates).
 * Endpoint: PATCH /api/backend-proxy/hiring-policy/instructions.
 * Consumidor: build_company_agent_context (backend) — inalterado.
 *
 * NB: store distinto dos 34 campos da empresa (lia_instructions). Por isso este
 * grupo tem seu próprio fetch+save; não compartilha o handler dos 34.
 */

import React from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { ConfigurableFieldCard } from "./_shared"
import { SETTINGS_QUERY_KEYS, dispatchSettingsUpdate } from "@/hooks/settings/useSettingsBroadcast"

interface InstructionDef { key: string; label: string; hint: string; placeholder: string }

// Os 7 conceitos de PROCESSO (os 4 redundantes — D&I, remoto, salário, janela —
// foram removidos na V2.2: D&I/remoto/salário vivem nos campos da empresa acima;
// janela LGPD saiu junto com a tab ghost).
export const PROCESS_INSTRUCTIONS: InstructionDef[] = [
  { key: "screening_criteria", label: "Critérios mínimos de triagem", hint: "Requisitos de formação, experiência ou comportamento que a LIA usa como filtro.", placeholder: "Ex: Mínimo 3 anos em gestão de projetos, inglês avançado..." },
  { key: "candidate_feedback_policy", label: "Feedback a candidatos reprovados", hint: "Nível de transparência com candidatos não avançados.", placeholder: "Ex: Reprovados recebem e-mail genérico; quem chegou à entrevista recebe feedback personalizado..." },
  { key: "interview_scheduling_policy", label: "Regras de agendamento de entrevistas", hint: "Como a LIA propõe e confirma horários.", placeholder: "Ex: LIA envia 3 opções; confirmação automática; cancelamento com 12h..." },
  { key: "interview_reminder_policy", label: "Lembretes de entrevista", hint: "Antecedência e canais dos lembretes.", placeholder: "Ex: 24h antes por e-mail e 2h antes por WhatsApp..." },
  { key: "no_show_policy", label: "Política de no-show", hint: "Fluxo de recontato e quando reprovar.", placeholder: "Ex: Recontato por e-mail e WhatsApp; sem resposta em 48h → Reprovado..." },
  { key: "data_retention_candidate_policy", label: "Retenção de dados de candidatos (LGPD)", hint: "Prazo de retenção (LGPD Art. 7).", placeholder: "Ex: 12 meses para quem foi à entrevista; 6 meses para triagem; depois anonimizar..." },
  { key: "talent_pool_opt_in_policy", label: "Convite ao banco de talentos (opt-in)", hint: "Quando a LIA convida reprovados para o pool.", placeholder: "Ex: Quem chegou à entrevista recebe convite com clareza sobre como sair..." },
]

interface RawPolicy { policy_instructions?: Record<string, string>; [k: string]: unknown }

async function fetchRawPolicy(): Promise<RawPolicy | null> {
  const res = await fetch("/api/backend-proxy/hiring-policy")
  if (res.ok) return res.json()
  return null
}

export function PolicyInstructionsGroup({ isReadOnly = false }: { isReadOnly?: boolean }) {
  const queryClient = useQueryClient()

  const { data: rawPolicy } = useQuery({
    queryKey: SETTINGS_QUERY_KEYS.hiringPolicy(),
    queryFn: fetchRawPolicy,
    staleTime: 30_000,
  })

  const [savedInstr, setSavedInstr] = React.useState<Record<string, string>>({})
  const [savingInstr, setSavingInstr] = React.useState<Set<string>>(new Set())

  const serverInstr = React.useMemo(
    () => (rawPolicy?.policy_instructions ?? {}) as Record<string, string>,
    [rawPolicy],
  )

  const mutation = useMutation({
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
      dispatchSettingsUpdate({ actionId: "save_policy_instruction", section: "lia_personalizacao", field: key, source: "ui", ts: Date.now() })
    },
    onError: (_e, { key }) => {
      setSavingInstr((p) => { const n = new Set(p); n.delete(key); return n })
    },
  })

  const save = React.useCallback((key: string, value: string) => {
    setSavingInstr((p) => new Set(p).add(key))
    mutation.mutate({ key, value })
  }, [mutation])

  return (
    <section className="space-y-3" data-testid="policy-instructions-group">
      <div>
        <h4 className="text-sm font-semibold text-lia-text-primary">Processo</h4>
        <p className="text-xs text-lia-text-secondary leading-relaxed mt-0.5">
          Orientações de processo (texto livre) que a LIA leva em conta. Não são gates
          automáticos — são contexto que enriquece decisões e comunicação.
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
        {PROCESS_INSTRUCTIONS.map((q) => {
          const value = savedInstr[q.key] !== undefined ? savedInstr[q.key] : (serverInstr[q.key] ?? "")
          return (
            <ConfigurableFieldCard
              key={q.key}
              data-testid={`instruction-block-${q.key}`}
              label={q.label}
              hint={q.hint}
              placeholder={q.placeholder}
              instruction={value}
              isReadOnly={isReadOnly}
              isSaving={savingInstr.has(q.key)}
              onInstructionSave={(text) => save(q.key, text)}
            />
          )
        })}
      </div>
    </section>
  )
}
