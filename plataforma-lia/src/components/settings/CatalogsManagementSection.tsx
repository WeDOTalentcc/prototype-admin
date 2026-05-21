"use client"

/**
 * CatalogsManagementSection — P0.G entrypoint (audit 2026-05-21).
 *
 * Aggregates the 4 catalog Managers do Sprint 2-5:
 *   1. Pipeline stage templates
 *   2. Alert rule templates
 *   3. Integration catalog
 *   4. Webhook event types
 *
 * Renderizado em Configurações > Catálogos Dinâmicos (categoria Admin).
 * Pattern canonical: stack vertical de 4 Card-wrapped Managers, cada um
 * autônomo com seu próprio CRUD form.
 *
 * Decisão Paulo (canonical 2026-05-20):
 *   - A1: customize cria copia total
 *   - B1: snapshot canonical (custom nao sync com master)
 *   - C: admin full CRUD; recrutador create-novos + edita propios; NAO delete
 *
 * isAdmin/currentUserId vem do contexto auth do caller (settings-page-enhanced).
 */

import React from "react"
import { useAuth } from "@/contexts/auth-context"
import { PipelineStageTemplatesManager } from "@/components/settings/PipelineStageTemplatesManager"
import { AlertRuleTemplatesManager } from "@/components/settings/AlertRuleTemplatesManager"
import { IntegrationCatalogManager } from "@/components/settings/IntegrationCatalogManager"
import { WebhookEventTypesManager } from "@/components/settings/WebhookEventTypesManager"

export function CatalogsManagementSection() {
  const { user } = useAuth()
  // C24: User.role enum (auth-service.ts) inclui "wedotalent_admin" como
  // canonical do backend (C1). Catálogos dinâmicos liberam acesso tanto
  // para org-admin do cliente quanto para staff WeDOTalent.
  const isAdmin = user?.role === "admin" || user?.role === "wedotalent_admin"
  // User identifier canonical no frontend é email (User type não tem id).
  const currentUserId = user?.email ?? null

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-h3 font-semibold text-lia-text-primary mb-1">
          Catálogos Dinâmicos
        </h2>
        <p className="text-xs text-lia-text-secondary">
          Gerencie templates per-tenant para pipeline stages, alertas,
          integrações e webhook events. Master canonical fornecidos pela
          WeDOTalent; customs criados pela sua empresa.
          {isAdmin
            ? " Você tem permissões de admin (full CRUD)."
            : " Como recrutador, você pode criar novos e editar os seus; admin gerencia deletes."}
        </p>
      </div>
      <PipelineStageTemplatesManager isAdmin={isAdmin} currentUserId={currentUserId} />
      <AlertRuleTemplatesManager isAdmin={isAdmin} currentUserId={currentUserId} />
      <IntegrationCatalogManager isAdmin={isAdmin} currentUserId={currentUserId} />
      <WebhookEventTypesManager isAdmin={isAdmin} currentUserId={currentUserId} />
    </div>
  )
}
