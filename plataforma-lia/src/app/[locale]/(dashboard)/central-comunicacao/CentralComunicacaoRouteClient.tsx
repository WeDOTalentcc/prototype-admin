"use client"

import { CommunicationHub } from "@/components/settings/CommunicationHub"
import { ModuleUpsell } from "@/components/module-access/module-upsell"
import { hasModuleAccess } from "@/utils/license-manager"

export function CentralComunicacaoRouteClient() {
  if (!hasModuleAccess("communication_center")) {
    return (
      <ModuleUpsell
        moduleId="communication_center"
        title="Central de Comunicação Omnichannel"
        description="Sistema unificado de comunicação multi-canal"
      />
    )
  }
  return <CommunicationHub />
}
