"use client"

import { useEffect, useState } from "react"
import { useSearchParams, useRouter, usePathname } from "next/navigation"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { HubHeader } from "@/components/settings/_shared"
import { PlanoTab } from "./consumo/PlanoTab"
import { ConsumoUnificadoTab } from "./consumo/ConsumoUnificadoTab"
import { FaturasTab } from "./consumo/FaturasTab"
import { CobrancaTab } from "./consumo/CobrancaTab"
import { ConsumptionDrilldownModal } from "./consumo/ConsumptionDrilldownModal"

/**
 * Estado canonical compartilhado do drilldown de consumo (Onda 5.2).
 * Elevado ao hub para que CreditosIaTab e AgentesTab usem o mesmo modal.
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
  const [activeTab, setActiveTab] = useState("plano")
  const [drilldown, setDrilldown] = useState<DrilldownState>(EMPTY_DRILLDOWN)

  // Onda 5.3 — leitura do query param ?filter={studioAgentId}.
  // Vindo da página KPIs do Studio. Após processar, limpa o param.
  const searchParams = useSearchParams()
  const router = useRouter()
  const pathname = usePathname()
  const filterParam = searchParams?.get("filter") ?? null

  useEffect(() => {
    if (!filterParam) return
    // Auto-seleciona sub-tab Consumo + abre drilldown filtrado por studio_agent_id.
    setActiveTab("consumo")
    setDrilldown({ agentType: null, studioAgentId: filterParam })
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
        title="Plano e Cobrança"
        description="Plano contratado, consumo de créditos, faturas e dados de cobrança."
      />
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4 max-w-lg">
          <TabsTrigger value="plano">Plano</TabsTrigger>
          <TabsTrigger value="consumo">Consumo</TabsTrigger>
          <TabsTrigger value="faturas">Faturas</TabsTrigger>
          <TabsTrigger value="cobranca">Cobrança</TabsTrigger>
        </TabsList>

        <TabsContent value="plano" className="mt-6">
          <PlanoTab />
        </TabsContent>

        <TabsContent value="consumo" className="mt-6">
          <ConsumoUnificadoTab onOpenDrilldown={openDrilldown} />
        </TabsContent>

        <TabsContent value="faturas" className="mt-6">
          <FaturasTab />
        </TabsContent>

        <TabsContent value="cobranca" className="mt-6">
          <CobrancaTab />
        </TabsContent>
      </Tabs>

      {/* Onda 5.2 — modal canonical único, owned pelo Hub. */}
      <ConsumptionDrilldownModal
        agentType={drilldown.agentType}
        studioAgentId={drilldown.studioAgentId}
        open={drilldownOpen}
        onOpenChange={handleOpenChange}
      />
    </div>
  )
}
