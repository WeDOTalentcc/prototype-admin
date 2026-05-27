'use client'

import { useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { CreditosIaTab } from './consumo/CreditosIaTab'
import { PearchTab } from './consumo/PearchTab'
import { AgentesTab } from './consumo/AgentesTab'
import { BillingTab } from './consumo/BillingTab'

export function ConsumoHub() {
  const [activeTab, setActiveTab] = useState('ia')

  return (
    <div className="space-y-6">
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4 max-w-lg">
          <TabsTrigger value="ia">Créditos IA</TabsTrigger>
          <TabsTrigger value="pearch">Pearch</TabsTrigger>
          <TabsTrigger value="agentes">Agentes</TabsTrigger>
          <TabsTrigger value="billing">Billing</TabsTrigger>
        </TabsList>
        <TabsContent value="ia" className="mt-6">
          <CreditosIaTab />
        </TabsContent>
        <TabsContent value="pearch" className="mt-6">
          <PearchTab />
        </TabsContent>
        <TabsContent value="agentes" className="mt-6">
          <AgentesTab />
        </TabsContent>
        <TabsContent value="billing" className="mt-6">
          <BillingTab />
        </TabsContent>
      </Tabs>
    </div>
  )
}
