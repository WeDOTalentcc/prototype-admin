"use client"

/**
 * HiringPoliciesHub — 18 perguntas conversacionais de Políticas de Recrutamento
 *
 * Sprint P0-1 (2026-05-27): substitui labels + enum/toggle por form-based interview
 * com Textarea livre, mantendo storage backend inalterado (HiringPolicyData).
 *
 * Arquitetura:
 * - Fetch: React Query via SETTINGS_QUERY_KEYS.hiringPolicy()
 * - Save:  PATCH /api/backend-proxy/hiring-policy/block (savePolicyField canônico)
 * - Cada campo salva on-blur (sem botão Submit)
 * - Strings PT-BR hardcodadas (sem useTranslations — alinhado com padrão deste hub)
 *
 * Grupos:
 * A. Triagem (3 perguntas)
 * B. Aprovação e Governança (3 perguntas)
 * C. Comunicação com o candidato (3 perguntas)
 * D. Entrevistas e agenda (3 perguntas)
 * E. Compatibilidade e filtros (3 perguntas)
 * F. Dados e LGPD (3 perguntas)
 */

import React, { useCallback, useState, useMemo } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Textarea } from "@/components/ui/textarea"
import { SETTINGS_QUERY_KEYS, dispatchSettingsUpdate } from "@/hooks/settings/useSettingsBroadcast"
import { POLICY_FIELD_TO_BLOCK } from "@/hooks/settings/useCompanyBlocks"
import { HubHeader, HubLoadingState, HubErrorState } from "./_shared"
import { CheckCircle2 } from "lucide-react"

// ─── Types ─────────────────────────────────────────────────────────────────

interface HiringPolicyRaw {
  pipeline_rules?: Record<string, unknown>
  scheduling_rules?: Record<string, unknown>
  communication_rules?: Record<string, unknown>
  screening_rules?: Record<string, unknown>
  automation_rules?: Record<string, unknown>
  [key: string]: unknown
}

interface QuestionDef {
  field: string
  group: string
  label: string
  hint: string
  placeholder: string
  crossRef?: string
}

// ─── Question definitions ─────────────────────────────────────────────────

const HIRING_POLICY_QUESTIONS: QuestionDef[] = [
  // A. Triagem
  {
    field: "screening_criteria",
    group: "A. Triagem",
    label: "Quais são os critérios mínimos obrigatórios para um candidato avançar na triagem?",
    hint: "Descreva requisitos de formação, experiência, habilidades técnicas ou comportamentais que a LIA deve usar como filtro.",
    placeholder: "Ex: Mínimo 3 anos de experiência em gestão de projetos, inglês avançado, ensino superior completo...",
  },
  {
    field: "auto_screening",
    group: "A. Triagem",
    label: "A triagem inicial deve ser feita automaticamente pela LIA ou requer revisão humana?",
    hint: "Define se a LIA avança candidatos automaticamente ou aguarda aprovação do recrutador.",
    placeholder: "Ex: A LIA pode triar automaticamente candidatos que atendem todos os critérios. Candidatos borderline devem ser revisados por mim...",
  },
  {
    field: "auto_stage_advance",
    group: "A. Triagem",
    label: "Em quais etapas a LIA pode avançar candidatos automaticamente?",
    hint: "Liste as etapas do funil onde o avanço automático é permitido.",
    placeholder: "Ex: Pode avançar da triagem para entrevista técnica. Da entrevista técnica em diante, precisa de aprovação do gestor...",
  },
  // B. Aprovação e Governança
  {
    field: "manager_approval_for_offer",
    group: "B. Aprovação e Governança",
    label: "A oferta de emprego precisa de aprovação do gestor antes de ser enviada ao candidato?",
    hint: "Define quem autoriza a proposta formal antes de ir para o candidato.",
    placeholder: "Ex: Sim, toda oferta precisa de aprovação do gestor direto da área. Para vagas sênior, o diretor também precisa aprovar...",
  },
  {
    field: "manager_approval_sla_hours",
    group: "B. Aprovação e Governança",
    label: "Qual o prazo máximo (em horas) para o gestor aprovar uma oferta antes de escalar?",
    hint: "Após esse prazo, a LIA pode alertar o recrutador para agir.",
    placeholder: "Ex: 24 horas. Se não houver resposta, notificar o recrutador para acionar o gestor diretamente...",
  },
  {
    field: "vacancy_approval_required",
    group: "B. Aprovação e Governança",
    label: "Abertura de nova vaga precisa de aprovação? Se sim, quem aprova?",
    hint: "Governa o fluxo de requisição de vagas internamente.",
    placeholder: "Ex: Toda vaga precisa de aprovação do gestor da área + RH. Vagas de reposição têm aprovação simplificada...",
  },
  // C. Comunicação com o candidato
  {
    field: "communication_window",
    group: "C. Comunicação com o candidato",
    label: "Janela de Envio de Comunicações — dias e horários permitidos para contato automatizado",
    hint: "Dias e horários em que a LIA pode enviar mensagens automáticas ao candidato (LGPD). Diferente do agendamento de entrevistas — consulte 'Janela de Agendamento de Entrevistas' no grupo D abaixo.",
    crossRef: "ⓘ Veja também: Janela de Agendamento de Entrevistas (grupo D — Entrevistas e agenda)",
    placeholder: "Ex: Segunda a sexta, das 8h às 18h. Sábados até 12h para posições urgentes...",
  },
  {
    field: "preferred_channel",
    group: "C. Comunicação com o candidato",
    label: "Quais canais de comunicação são permitidos para contato com candidatos?",
    hint: "WhatsApp, e-mail, SMS — defina quais a LIA pode usar e em qual ordem.",
    placeholder: "Ex: E-mail como principal. WhatsApp apenas se o candidato autorizar. Nunca SMS...",
  },
  {
    field: "candidate_feedback_policy",
    group: "C. Comunicação com o candidato",
    label: "Candidatos reprovados devem receber feedback? Se sim, em qual nível de detalhe?",
    hint: "Define a política de transparência com candidatos não avançados.",
    placeholder: "Ex: Todo candidato reprovado recebe e-mail de feedback genérico. Candidatos que chegaram à entrevista recebem feedback personalizado...",
  },
  // D. Entrevistas e agenda
  {
    field: "interview_scheduling_policy",
    group: "D. Entrevistas e agenda",
    label: "Janela de Agendamento de Entrevistas — dias, horários e regras para marcar entrevistas",
    hint: "Dias e horários em que candidatos podem ser convidados para entrevistas. Diferente do envio de mensagens automáticas — consulte 'Janela de Envio de Comunicações' no grupo C acima.",
    crossRef: "ⓘ Veja também: Janela de Envio de Comunicações (grupo C — Comunicação com o candidato)",
    placeholder: "Ex: LIA pode enviar 3 opções de horário ao candidato. Confirmação é automática se o candidato escolher. Cancelamentos precisam de aviso de 12h...",
  },
  {
    field: "interview_reminder_policy",
    group: "D. Entrevistas e agenda",
    label: "Com quanto tempo de antecedência enviar lembretes de entrevista?",
    hint: "Frequência e canais para lembretes automáticos.",
    placeholder: "Ex: Lembrete 24h antes por e-mail e 2h antes por WhatsApp...",
  },
  {
    field: "no_show_policy",
    group: "D. Entrevistas e agenda",
    label: "O que fazer quando um candidato não comparece à entrevista (no-show)?",
    hint: "Define o fluxo de tentativas de recontato e quando reprovar automaticamente.",
    placeholder: "Ex: Tentar recontato por e-mail e WhatsApp. Se sem resposta em 48h, mover para Reprovado com motivo 'Sem Contato'...",
  },
  // E. Compatibilidade e filtros
  {
    field: "minimum_compatibility_score",
    group: "E. Compatibilidade e filtros",
    label: "Qual a pontuação mínima de compatibilidade para um candidato avançar?",
    hint: "Score mínimo que a LIA deve considerar aceitável para encaminhar ao recrutador.",
    placeholder: "Ex: Mínimo 65% de compatibilidade. Candidatos acima de 85% têm prioridade no funil...",
  },
  {
    field: "salary_negotiation_policy",
    group: "E. Compatibilidade e filtros",
    label: "Existe flexibilidade salarial na oferta? Qual a faixa de negociação permitida?",
    hint: "Define os limites para a LIA orientar expectativas salariais.",
    placeholder: "Ex: Faixa de 10% acima do valor base para negociação. Benefícios são fixos...",
  },
  {
    field: "remote_work_policy",
    group: "E. Compatibilidade e filtros",
    label: "Qual a política de trabalho remoto para as vagas abertas?",
    hint: "Modelo de trabalho que a LIA deve informar aos candidatos.",
    placeholder: "Ex: Modelo híbrido (3x presencial), escritório em São Paulo. Vagas de TI podem ser 100% remoto...",
  },
  // F. Dados e LGPD
  {
    field: "data_retention_candidate_policy",
    group: "F. Dados e LGPD",
    label: "Por quanto tempo manter dados de candidatos não contratados após o encerramento de uma vaga?",
    hint: "Respeitar LGPD Art. 7 — prazo de retenção definido pelo controlador.",
    placeholder: "Ex: 12 meses para candidatos que chegaram à entrevista. 6 meses para triagem apenas. Após isso, anonimizar...",
  },
  {
    field: "talent_pool_opt_in_policy",
    group: "F. Dados e LGPD",
    label: "Candidatos não aprovados devem ser convidados para o banco de talentos?",
    hint: "Define se a LIA envia convite de opt-in para manter o candidato no pool.",
    placeholder: "Ex: Sim, todo candidato que chegou à entrevista recebe convite. Incluir clareza sobre como sair do banco...",
  },
  {
    field: "diversity_inclusion_guidelines",
    group: "F. Dados e LGPD",
    label: "Há diretrizes específicas de diversidade e inclusão que a LIA deve considerar no processo seletivo?",
    hint: "Políticas afirmativas, grupos prioritários ou critérios de D&I da empresa.",
    placeholder: "Ex: Priorizamos candidaturas de PcD, mulheres em tech e pessoas negras para vagas técnicas. A LIA deve sinalizar se o funil não reflete essa diversidade...",
  },
]

// ─── Field extractor: reads leaf value from nested HiringPolicyRaw ──────────

function extractFieldValue(data: HiringPolicyRaw | null | undefined, field: string): string {
  if (!data) return ""
  const subBlock = POLICY_FIELD_TO_BLOCK[field]
  if (!subBlock) {
    // fallback: try top-level
    const v = data[field]
    if (v === null || v === undefined) return ""
    if (typeof v === "boolean") return v ? "Sim" : "Não"
    return String(v)
  }
  const block = data[subBlock] as Record<string, unknown> | undefined
  if (!block) return ""
  const v = block[field]
  if (v === null || v === undefined) return ""
  if (typeof v === "boolean") return v ? "Sim" : "Não"
  if (typeof v === "object") return JSON.stringify(v)
  return String(v)
}

// ─── Fetch ───────────────────────────────────────────────────────────────────

async function fetchHiringPolicy(): Promise<HiringPolicyRaw | null> {
  const res = await fetch("/api/backend-proxy/hiring-policy")
  if (res.ok) return res.json()
  if (res.status !== 404) {
    console.error("[HiringPoliciesHub] fetchHiringPolicy HTTP", res.status)
  }
  return null
}

// ─── Save ────────────────────────────────────────────────────────────────────

async function savePolicyField(field: string, value: string): Promise<void> {
  const subBlock = POLICY_FIELD_TO_BLOCK[field]
  if (!subBlock) throw new Error(`Campo não mapeado para sub-bloco: ${field}`)
  const res = await fetch("/api/backend-proxy/hiring-policy/block", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ block: subBlock, data: { [field]: value } }),
  })
  if (!res.ok) {
    let msg = "Falha ao salvar política"
    try {
      const data = await res.json()
      if (data?.detail) msg = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail)
      else if (data?.message) msg = data.message
    } catch { /* not JSON */ }
    throw new Error(msg)
  }
}

// ─── Group header ─────────────────────────────────────────────────────────────

function GroupHeader({ label }: { label: string }) {
  return (
    <div className="pt-4 first:pt-0">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-lia-text-tertiary border-b border-lia-border-subtle pb-2 mb-4">
        {label}
      </h3>
    </div>
  )
}

// ─── Single question block ────────────────────────────────────────────────────

interface QuestionBlockProps {
  question: QuestionDef
  value: string
  savedValue: string
  onChange: (field: string, value: string) => void
  onBlur: (field: string, value: string) => void
  isSaving: boolean
  saveError: string | null
}

function QuestionBlock({
  question,
  value,
  savedValue,
  onChange,
  onBlur,
  isSaving,
  saveError,
}: QuestionBlockProps) {
  const isDirty = value !== savedValue
  const showSaved = !isDirty && savedValue !== "" && !isSaving

  return (
    <div className="space-y-1.5" data-testid={`question-block-${question.field}`}>
      <div className="flex items-start justify-between gap-2">
        <label
          htmlFor={`policy-q-${question.field}`}
          className="text-sm font-medium text-lia-text-primary leading-snug"
        >
          {question.label}
        </label>
        {showSaved && (
          <span className="flex items-center gap-1 text-micro text-status-success shrink-0 mt-0.5" aria-label="Salvo">
            <CheckCircle2 className="w-3 h-3" />
            Salvo
          </span>
        )}
        {isSaving && (
          <span className="text-micro text-lia-text-tertiary shrink-0 mt-0.5">Salvando...</span>
        )}
      </div>
      <p className="text-xs text-lia-text-secondary leading-relaxed">{question.hint}</p>
      {question.crossRef && (
        <p className="text-xs text-lia-text-tertiary italic mt-0.5">{question.crossRef}</p>
      )}
      <Textarea
        id={`policy-q-${question.field}`}
        value={value}
        onChange={(e) => onChange(question.field, e.target.value)}
        onBlur={(e) => onBlur(question.field, e.target.value)}
        placeholder={question.placeholder}
        rows={3}
        className="resize-none text-sm bg-lia-bg-primary border-lia-border-subtle focus:border-lia-border-medium placeholder:text-lia-text-tertiary"
        aria-describedby={saveError ? `policy-q-${question.field}-error` : undefined}
      />
      {saveError && (
        <p
          id={`policy-q-${question.field}-error`}
          className="text-xs text-status-error mt-0.5"
          role="alert"
        >
          {saveError}
        </p>
      )}
    </div>
  )
}

// ─── Main hub ─────────────────────────────────────────────────────────────────

export function HiringPoliciesHub() {
  const queryClient = useQueryClient()

  const { data: policyData, isLoading, error, refetch } = useQuery({
    queryKey: SETTINGS_QUERY_KEYS.hiringPolicy(),
    queryFn: fetchHiringPolicy,
    staleTime: 30_000,
  })

  // Local state for in-progress edits (before blur)
  const [localValues, setLocalValues] = useState<Record<string, string>>({})
  // Track last-saved values for "Salvo" indicator
  const [savedValues, setSavedValues] = useState<Record<string, string>>({})
  // Per-field saving state
  const [savingFields, setSavingFields] = useState<Set<string>>(new Set())
  // Per-field save errors
  const [saveErrors, setSaveErrors] = useState<Record<string, string | null>>({})

  // Initialize local state from fetched data (on first load only)
  const initialValues = useMemo(() => {
    const init: Record<string, string> = {}
    for (const q of HIRING_POLICY_QUESTIONS) {
      init[q.field] = extractFieldValue(policyData, q.field)
    }
    return init
  }, [policyData])

  const mutation = useMutation({
    mutationFn: ({ field, value }: { field: string; value: string }) =>
      savePolicyField(field, value),
    onSuccess: (_data, { field, value }) => {
      setSavedValues((prev) => ({ ...prev, [field]: value }))
      setSavingFields((prev) => {
        const next = new Set(prev)
        next.delete(field)
        return next
      })
      setSaveErrors((prev) => ({ ...prev, [field]: null }))
      queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEYS.hiringPolicy() })
      dispatchSettingsUpdate({ actionId: "save_hiring_policy", section: "hiring_policies", field, source: "ui", ts: Date.now() })
    },
    onError: (err: Error, { field }) => {
      setSavingFields((prev) => {
        const next = new Set(prev)
        next.delete(field)
        return next
      })
      setSaveErrors((prev) => ({
        ...prev,
        [field]: err.message || "Falha ao salvar",
      }))
    },
  })

  const handleChange = useCallback((field: string, value: string) => {
    setLocalValues((prev) => ({ ...prev, [field]: value }))
  }, [])

  const handleBlur = useCallback(
    (field: string, value: string) => {
      const currentValue = value
      const serverValue = extractFieldValue(policyData, field)
      const previousLocal = initialValues[field] ?? ""
      const effectivePrev = savedValues[field] !== undefined ? savedValues[field] : previousLocal

      // Only save if value actually changed
      if (currentValue === effectivePrev || currentValue === serverValue) return

      setSavingFields((prev) => new Set(prev).add(field))
      setSaveErrors((prev) => ({ ...prev, [field]: null }))
      mutation.mutate({ field, value: currentValue })
    },
    [policyData, initialValues, savedValues, mutation],
  )

  if (isLoading) {
    return <HubLoadingState message="Carregando políticas de recrutamento..." />
  }

  if (error) {
    return (
      <HubErrorState
        message="Erro ao carregar políticas. Tente novamente."
        onRetry={refetch}
      />
    )
  }

  // Determine display value: local override > saved value > server value
  const getDisplayValue = (field: string): string => {
    if (field in localValues) return localValues[field]
    if (savedValues[field] !== undefined) return savedValues[field]
    return initialValues[field] ?? ""
  }

  // Group questions
  const questionsByGroup: Record<string, QuestionDef[]> = {}
  for (const q of HIRING_POLICY_QUESTIONS) {
    if (!questionsByGroup[q.group]) questionsByGroup[q.group] = []
    questionsByGroup[q.group].push(q)
  }
  const groups = Object.entries(questionsByGroup)

  const filledCount = HIRING_POLICY_QUESTIONS.filter((q) => {
    const v = getDisplayValue(q.field)
    return v.trim() !== ""
  }).length

  return (
    <div className="flex flex-col h-full" data-testid="hiring-policies-hub">
      <HubHeader
        title="Políticas de Recrutamento"
        description="Defina como a LIA deve se comportar no processo seletivo. Responda com suas próprias palavras — quanto mais detalhado, mais preciso o comportamento da IA."
      >
        <span className="text-xs text-lia-text-secondary whitespace-nowrap">
          {filledCount} / {HIRING_POLICY_QUESTIONS.length} respondidas
        </span>
      </HubHeader>

      <div className="flex-1 overflow-y-auto space-y-6 mt-4 pr-1">
        {groups.map(([groupLabel, questions]) => (
          <div key={groupLabel}>
            <GroupHeader label={groupLabel} />
            <div className="space-y-6">
              {questions.map((q) => (
                <QuestionBlock
                  key={q.field}
                  question={q}
                  value={getDisplayValue(q.field)}
                  savedValue={
                    savedValues[q.field] !== undefined
                      ? savedValues[q.field]
                      : (initialValues[q.field] ?? "")
                  }
                  onChange={handleChange}
                  onBlur={handleBlur}
                  isSaving={savingFields.has(q.field)}
                  saveError={saveErrors[q.field] ?? null}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
