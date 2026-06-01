/**
 * settings-rbac.ts — P2-3 (audit 2026-05-26):
 *
 * Matriz canonical de permissões por (hub × role) pro menu Configurações.
 * Roles canonical: admin, manager, recruiter, viewer (ClientUserRole enum).
 *
 * Audit ref: ~/Documents/wedotalent_audit_2026-05-26/CONFIGURACOES_MENU_COHERENCE_AUDIT.md
 * P2-3 + memory project_rbac_sprint_6_7_8_2026-05-26 (RBAC Sprint 7+8 infra).
 *
 * Reuso da infraestrutura Sprint 7+8 RBAC:
 * - compute_visible_scope (backend) — filtragem multi-tenant per role
 * - assert_mutation_allowed (backend) — fail-secure mutation gate
 * - sensitive PII gate (mig 207) — CPF+DoB+endereço per role
 *
 * Este arquivo é o "front-end mirror" — define quais hubs cada role VÊ
 * (hidden), quais pode LER (view), quais pode EDITAR (edit).
 *
 * Backend enforcement permanece autoritativo (defense in depth).
 * Frontend apenas esconde/desabilita UI; mutation real é validada no backend.
 */

import type { SettingsSectionId } from "./resolve-settings-target"

/** Roles canonical da plataforma WeDOTalent (ClientUserRole enum). */
export type SettingsRole = "admin" | "manager" | "recruiter" | "viewer"

/** Nível de acesso por hub. */
export type SettingsPermission = "edit" | "view" | "hidden"

/**
 * Matriz: hubId × role → permission.
 *
 * Princípios:
 * - admin: edita tudo (default canonical)
 * - manager: edita operacional (Recrutamento, Comunicação); vê config; não toca usuários/integrações/billing
 * - recruiter: edita operacional (Recrutamento, Comunicação); vê dados empresa; sem acesso a integrações/billing/governança
 * - viewer: só vê hubs que são read-only de natureza (Minha Empresa, Compliance); zero edit
 *
 * Cada decisão tem rationale documentado em audit §P2-3.
 */
// Tipo relaxado para string (em vez de SettingsSectionId strict) porque
// 'ai-credits' e' hub no settings-page-enhanced.tsx mas NAO esta em
// SETTINGS_SECTION_IDS do resolver (drift historico pre-existente — follow-up).
export const SETTINGS_HUB_PERMISSIONS: Record<
  string,
  Record<SettingsRole, SettingsPermission>
> = {
  "minha-empresa": {
    admin: "edit",
    manager: "view",
    recruiter: "view",
    viewer: "view",
  },
  "lia-personalizacao": {
    admin: "edit",
    manager: "view",
    recruiter: "view",
    viewer: "hidden",
  },
  "recrutamento-lia": {
    admin: "edit",
    manager: "edit",
    recruiter: "edit",
    viewer: "view",
  },
  // P2 (2026-06-01): hub standalone "Políticas de Recrutamento" — mesma
  // natureza operacional de recrutamento-lia (admin/manager/recruiter editam).
  "politicas-recrutamento": {
    admin: "edit",
    manager: "edit",
    recruiter: "edit",
    viewer: "view",
  },
  "comunicacao-alertas": {
    admin: "edit",
    manager: "edit",
    recruiter: "edit",
    viewer: "hidden",
  },
  "usuarios-departamentos": {
    admin: "edit",
    manager: "view",
    recruiter: "hidden",
    viewer: "hidden",
  },
  integrations: {
    admin: "edit",
    manager: "hidden",
    recruiter: "hidden",
    viewer: "hidden",
  },
  // ai-credits: billing/quota monitoring. Admin edita (top-ups, alerts); manager/recruiter veem
  // consumo (transparencia); viewer nao tem acesso a billing info.
  "ai-credits": {
    admin: "edit",
    manager: "view",
    recruiter: "view",
    viewer: "hidden",
  },
  "fairness-compliance": {
    admin: "edit",
    manager: "view",
    recruiter: "view",
    viewer: "view",
  },
}

/**
 * Resolve permissão de um hub pra role atual.
 * Defaults canonical:
 * - role null/undefined (não logado ou sem role) → "hidden" (fail-secure)
 * - role desconhecido → "hidden"
 * - hub desconhecido → "hidden"
 */
export function getHubPermission(
  hubId: string,
  role: string | null | undefined,
): SettingsPermission {
  if (!role) return "hidden"
  // wedotalent_admin (staff WeDOTalent, vem do JWT — ver auth-service.ts) é
  // superset de admin em toda a plataforma. O idioma canônico no resto do código
  // é `role === "admin" || role === "wedotalent_admin"` (CatalogsManagementSection,
  // AuditLogsDrillDown, LiaFieldsConfigPanel). Esta matriz era a ÚNICA exceção que
  // esquecia esse role — fazendo getHubPermission cair em "hidden" → canEditHub=false
  // → SettingsEditModeToggle some → read-only forçado em TODOS os hubs (bug 2026-06-01).
  // Normaliza para admin antes do lookup (fail-secure preservado: role desconhecida
  // continua "hidden").
  const normalizedRole = role === "wedotalent_admin" ? "admin" : role
  const validRole = normalizedRole as SettingsRole
  const hubPermissions = SETTINGS_HUB_PERMISSIONS[hubId as SettingsSectionId]
  if (!hubPermissions) return "hidden"
  return hubPermissions[validRole] ?? "hidden"
}

/**
 * Helper: hub é visível pra essa role? (any permission except "hidden")
 */
export function isHubVisible(
  hubId: string,
  role: string | null | undefined,
): boolean {
  return getHubPermission(hubId, role) !== "hidden"
}

/**
 * Helper: role pode editar esse hub?
 */
export function canEditHub(
  hubId: string,
  role: string | null | undefined,
): boolean {
  return getHubPermission(hubId, role) === "edit"
}
