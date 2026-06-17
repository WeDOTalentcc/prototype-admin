"use client"

import { useEffect, useState } from "react"
import { useSearchParams, useRouter, usePathname } from "next/navigation"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { HubHeader } from "@/components/settings/_shared"
import { CreditosIaTab } from "./consumo/CreditosIaTab"
import { PearchTab } from "./consumo/PearchTab"
import { AgentesTab } from "./consumo/AgentesTab"
import { BillingTab } from "./consumo/BillingTab"
import { ConsumptionDrilldownModal } from "./consumo/ConsumptionDrilldownModal"

/**
 * Estado canonical compartilhado do drilldown de consumo (Onda 5.2).
 *
 * Backend aceita filtrar por agent_type OU studio_agent_id. O state aqui
 * carrega ambos para que callers (CreditosIaTab via BudgetAlertsList,
 * AgentesTab via BarChart) usem o mesmo modal sem reimplementar logica.
 */
export interface DrilldownState {
  agentType: string | null
  studioAgentId: string | null
}

const EMPTY_DRILLDOWN: DrilldownState = {
  agentType: null,
  studioAgentId: null,
}

export function ConsumoHub() {
  const [activeTab, setActiveTab] = useState("ia")
  // Onda 5.2 — state elevado: ConsumoHub e o owner unico do drilldown modal.
  const [drilldown, setDrilldown] = useState<DrilldownState>(EMPTY_DRILLDOWN)

  // Onda 5.3 — leitura do query param ?filter={studioAgentId}.
  // Vindo da pagina KPIs do Studio. Apos processar, limpa o param para evitar
  // re-trigger em refresh manual.
  const searchParams = useSearchParams()
  const router = useRouter()
  const pathname = usePathname()
  const filterParam = searchParams?.get("filter") ?? null

  useEffect(() => {
    if (!filterParam) return
    // Auto-seleciona aba Agentes + abre o drilldown filtrado por studio_agent_id.
    setActiveTab("agentes")
    setDrilldown({ agentType: null, studioAgentId: filterParam })
    // Limpa o param da URL (mantem section=consumo).
    if (searchParams && pathname) {
      const params = new URLSearchParams(searchParams.toString())
      params.delete("filter")
      const qs = params.toString()
      router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterParam])

  function openDrilldown(next: DrilldownState) {
    setDrilldown(next)
  }

  function handleOpenChange(open: boolean) {
    if (!open) setDrilldown(EMPTY_DRILLDOWN)
  }

  const drilldownOpen =
    drilldown.agentType !== null || drilldown.studioAgentId !== null

  return (
    <div className="space-y-6">
      <HubHeader
        title="Consumo"
        description="Créditos de IA, buscas Pearch, atividade dos agentes e faturamento."
      />
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4 max-w-lg">
          <TabsTrigger value="ia">Créditos IA</TabsTrigger>
          <TabsTrigger value="pearch">Pearch</TabsTrigger>
          <TabsTrigger value="agentes">Agentes</TabsTrigger>
          <TabsTrigger value="billing">Plano e Cobrança</TabsTrigger>
        </TabsList>
        <TabsContent value="ia" className="mt-6">
          <CreditosIaTab onOpenDrilldown={openDrilldown} />
        </TabsContent>
        <TabsContent value="pearch" className="mt-6">
          <PearchTab />
        </TabsContent>
        <TabsContent value="agentes" className="mt-6">
          <AgentesTab onOpenDrilldown={openDrilldown} />
        </TabsContent>
        <TabsContent value="billing" className="mt-6">
          <BillingTab />
        </TabsContent>
      </Tabs>

      {/* Onda 5.2 — modal canonical unico, owned pelo Hub.
          Callers em qualquer tab abrem via openDrilldown(). */}
      <ConsumptionDrilldownModal
        agentType={drilldown.agentType}
        studioAgentId={drilldown.studioAgentId}
        open={drilldownOpen}
        onOpenChange={handleOpenChange}
      />
    </div>
  )
}
