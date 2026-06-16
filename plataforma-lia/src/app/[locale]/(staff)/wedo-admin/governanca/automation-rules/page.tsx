import { AutomationRulesPanel } from "@/components/_wedo_internal/governanca/AutomationRulesPanel"

/**
 * /wedo-admin/governanca/automation-rules/ — staff WeDOTalent only.
 *
 * Regras de automação por gatilho (pipeline, comunicação, alertas).
 * Backend (kanban_action_tool_registry, pipeline tools) é consumido por LIA —
 * intocado nesta migração.
 *
 * Gate: enforce em (staff)/layout.tsx → StaffLayoutClient.tsx.
 */
export default function WedoAdminAutomationRulesPage() {
  return <AutomationRulesPanel />
}
