"use client"

/**
 * ContratacaoHub — configurações N2/N3 de proposta de oferta.
 *
 * Expõe para o recrutador:
 * - Dias do mês permitidos para início de contrato (AllowedStartDaysPicker)
 * - Aviso prévio mínimo em dias
 * - Habilitar/desabilitar negociação de proposta (N3 gate)
 * - Percentual máximo de flexibilidade salarial
 *
 * Canonical patterns (CLAUDE.md Sprint D 2026-05-26):
 * - REGRA 1: useQuery para server data (não useState + useEffect)
 * - REGRA 3: usa HubHeader / HubLoadingState / HubErrorState de _shared
 * - REGRA 5: dispatchSettingsUpdate após salvar
 * - REGRA 6: AllowedStartDaysPicker é puramente presentacional
 */

import React, { useState } from "react"
import { CalendarDays, Clock, TrendingUp, Lock } from "lucide-react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { AllowedStartDaysPicker } from "@/components/settings/AllowedStartDaysPicker"
import { HubHeader, HubLoadingState, HubErrorState } from "@/components/settings/_shared"
import { SETTINGS_QUERY_KEYS, dispatchSettingsUpdate } from "@/hooks/settings/useSettingsBroadcast"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

interface OfferRules {
  allowed_start_day_of_month: number[]
  min_notice_days: number
  negotiation_enabled: boolean
  salary_flex_pct_max: number
  counter_proposal_max_rounds: number
  negotiation_hitl_threshold_pct: number
}

const DEFAULTS: OfferRules = {
  allowed_start_day_of_month: [1, 15],
  min_notice_days: 30,
  negotiation_enabled: false,
  salary_flex_pct_max: 0,
  counter_proposal_max_rounds: 2,
  negotiation_hitl_threshold_pct: 5,
}

async function fetchOfferRules(): Promise<OfferRules> {
  const res = await fetch("/api/backend-proxy/offer-rules")
  if (!res.ok) throw new Error("Erro ao buscar regras de contratação")
  const data = await res.json()
  return (data?.offer_rules ?? data) as OfferRules
}

async function saveOfferRules(rules: Partial<OfferRules>): Promise<void> {
  const res = await fetch("/api/backend-proxy/offer-rules", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(rules),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error((err as { error?: string }).error ?? "Erro ao salvar")
  }
}

export function ContratacaoHub() {
  // ─── HOOKS TODOS ANTES DE QUALQUER EARLY RETURN (rules-of-hooks) ──────────
  const queryClient = useQueryClient()

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: SETTINGS_QUERY_KEYS.offerRules(),
    queryFn: fetchOfferRules,
    staleTime: 30_000,
  })

  const rules: OfferRules = { ...DEFAULTS, ...(data ?? {}) }

  const [localDays, setLocalDays] = useState<number[] | null>(null)
  const [localNotice, setLocalNotice] = useState<string | null>(null)
  const [localFlex, setLocalFlex] = useState<string | null>(null)
  const [localNegotiation, setLocalNegotiation] = useState<boolean | null>(null)
  const [localRounds, setLocalRounds] = useState<string | null>(null)

  // Merge local overrides sobre server state
  const effective: OfferRules = {
    ...rules,
    allowed_start_day_of_month: localDays ?? rules.allowed_start_day_of_month,
    min_notice_days: localNotice !== null ? parseInt(localNotice) || 0 : rules.min_notice_days,
    salary_flex_pct_max: localFlex !== null ? parseInt(localFlex) || 0 : rules.salary_flex_pct_max,
    negotiation_enabled: localNegotiation ?? rules.negotiation_enabled,
    counter_proposal_max_rounds: localRounds !== null ? parseInt(localRounds) || 0 : rules.counter_proposal_max_rounds,
  }

  const isDirty =
    localDays !== null ||
    localNotice !== null ||
    localFlex !== null ||
    localNegotiation !== null ||
    localRounds !== null

  const mutation = useMutation({
    mutationFn: saveOfferRules,
    onSuccess: () => {
      setLocalDays(null)
      setLocalNotice(null)
      setLocalFlex(null)
      setLocalNegotiation(null)
      setLocalRounds(null)
      queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEYS.offerRules() })
      dispatchSettingsUpdate({ actionId: "configure_contratacao", section: "contratacao", source: "ui", ts: Date.now() })
      toast.success("Configurações de contratação salvas")
    },
    onError: (err: Error) => {
      toast.error(err.message)
    },
  })

  function handleSave() {
    mutation.mutate({
      allowed_start_day_of_month: effective.allowed_start_day_of_month,
      min_notice_days: effective.min_notice_days,
      salary_flex_pct_max: effective.salary_flex_pct_max,
      negotiation_enabled: effective.negotiation_enabled,
      counter_proposal_max_rounds: effective.counter_proposal_max_rounds,
    })
  }

  // ─── EARLY RETURNS APÓS TODOS OS HOOKS ────────────────────────────────────
  if (isLoading) return <HubLoadingState />
  if (error) return <HubErrorState onRetry={refetch} />

  return (
    <div className="space-y-6" data-testid="contratacao-hub">
      <HubHeader
        title="Configurações de Contratação"
        description="Define regras de proposta de oferta, datas de início e negociação."
      />

      {/* Dias de início */}
      <section className="space-y-3">
        <div className="flex items-center gap-2">
          <CalendarDays className="w-4 h-4 text-lia-text-secondary" />
          <h3 className="text-sm font-medium text-lia-text-primary">Dias de início permitidos</h3>
        </div>
        <p className="text-xs text-lia-text-secondary">
          Propostas geradas pela IA sugerirem somente datas nesses dias. Dias 29–31 excluídos
          para cobrir fevereiro.
        </p>
        <AllowedStartDaysPicker
          value={effective.allowed_start_day_of_month}
          onChange={(days) => setLocalDays(days)}
          disabled={mutation.isPending}
        />
      </section>

      {/* Aviso prévio */}
      <section className="space-y-2">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-lia-text-secondary" />
          <Label htmlFor="notice-days" className="text-sm font-medium text-lia-text-primary">
            Aviso prévio mínimo (dias)
          </Label>
        </div>
        <Input
          id="notice-days"
          type="number"
          min={0}
          max={365}
          value={localNotice ?? effective.min_notice_days}
          onChange={(e) => setLocalNotice(e.target.value)}
          disabled={mutation.isPending}
          className="w-32"
        />
      </section>

      {/* Negociação N3 */}
      <section className="space-y-3 p-4 rounded-lg bg-lia-surface-secondary border border-lia-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-lia-text-secondary" />
            <div>
              <p className="text-sm font-medium text-lia-text-primary">Habilitar negociação de proposta</p>
              <p className="text-xs text-lia-text-secondary mt-0.5">
                Permite ao candidato fazer contrapropostas via concierge IA (N3).
              </p>
            </div>
          </div>
          <Switch
            checked={effective.negotiation_enabled}
            onCheckedChange={(checked) => setLocalNegotiation(checked)}
            disabled={mutation.isPending}
            aria-label="Habilitar negociação"
          />
        </div>

        {effective.negotiation_enabled && (
          <div className="pt-2 space-y-3 border-t border-lia-border">
            <div className="flex items-center gap-4">
              <div className="space-y-1">
                <Label htmlFor="flex-pct" className="text-xs text-lia-text-secondary">
                  Flexibilidade salarial máxima (%)
                </Label>
                <Input
                  id="flex-pct"
                  type="number"
                  min={0}
                  max={50}
                  value={localFlex ?? effective.salary_flex_pct_max}
                  onChange={(e) => setLocalFlex(e.target.value)}
                  disabled={mutation.isPending}
                  className="w-24"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="max-rounds" className="text-xs text-lia-text-secondary">
                  Rodadas máximas
                </Label>
                <Input
                  id="max-rounds"
                  type="number"
                  min={0}
                  max={10}
                  value={localRounds ?? effective.counter_proposal_max_rounds}
                  onChange={(e) => setLocalRounds(e.target.value)}
                  disabled={mutation.isPending}
                  className="w-24"
                />
              </div>
            </div>
            <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
              <Lock className="w-3 h-3" />
              <span>
                Negociações acima de {effective.negotiation_hitl_threshold_pct}% de flexibilidade
                passarão por aprovação do recrutador.
              </span>
            </div>
          </div>
        )}
      </section>

      {/* Ações */}
      {isDirty && (
        <div className="flex items-center gap-3 pt-2">
          <Button
            onClick={handleSave}
            disabled={mutation.isPending}
            size="sm"
          >
            {mutation.isPending ? "Salvando…" : "Salvar configurações"}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setLocalDays(null)
              setLocalNotice(null)
              setLocalFlex(null)
              setLocalNegotiation(null)
              setLocalRounds(null)
            }}
            disabled={mutation.isPending}
          >
            Descartar
          </Button>
        </div>
      )}
    </div>
  )
}
