"use client"

import React, { useState, useEffect, use } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Shield,
  Brain,
  Lock,
  Activity,
} from "lucide-react"
import { ComplianceTab } from "./ComplianceTab"
import { AIGovernanceTab } from "./AIGovernanceTab"
import { LGPDTab } from "./LGPDTab"
import { HealthTab } from "./HealthTab"

export default function ObservabilidadePage({
  params
}: {
  params: Promise<{ clientId: string }>
}) {
  const { clientId } = use(params)
  const [activeTab, setActiveTab] = useState('compliance')
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return (
      <div className="space-y-6">
        <div>
          <div className="h-7 w-64 bg-lia-interactive-active rounded-md animate-pulse motion-reduce:animate-none" />
          <div className="h-5 w-96 bg-lia-bg-tertiary rounded-md animate-pulse motion-reduce:animate-none mt-2" />
        </div>
        <div className="h-12 w-full bg-lia-bg-tertiary rounded-md animate-pulse motion-reduce:animate-none" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-32 bg-lia-bg-tertiary rounded-md animate-pulse motion-reduce:animate-none" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 
          className="text-lg font-semibold text-lia-text-primary dark:text-lia-text-primary"
        >
          Observabilidade & Governança
        </h2>
        <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">
          Monitore compliance, governança de IA, privacidade e saúde do sistema
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="w-full justify-start bg-lia-bg-tertiary dark:bg-lia-bg-secondary p-1 rounded-md">
          <TabsTrigger value="compliance" className="flex items-center gap-2">
            <Shield className="w-4 h-4" />
            Compliance
          </TabsTrigger>
          <TabsTrigger value="ai-governance" className="flex items-center gap-2">
            <Brain className="w-4 h-4 text-wedo-cyan" />
            AI Governance
          </TabsTrigger>
          <TabsTrigger value="lgpd" className="flex items-center gap-2">
            <Lock className="w-4 h-4" />
            LGPD & Privacy
          </TabsTrigger>
          <TabsTrigger value="health" className="flex items-center gap-2">
            <Activity className="w-4 h-4" />
            Health & Incidents
          </TabsTrigger>
        </TabsList>

        <TabsContent value="compliance" className="mt-6">
          <ComplianceTab clientId={clientId} />
        </TabsContent>

        <TabsContent value="ai-governance" className="mt-6">
          <AIGovernanceTab clientId={clientId} />
        </TabsContent>

        <TabsContent value="lgpd" className="mt-6">
          <LGPDTab clientId={clientId} />
        </TabsContent>

        <TabsContent value="health" className="mt-6">
          <HealthTab />
        </TabsContent>
      </Tabs>
    </div>
  )
}
