import { PolicyEnginePanel } from "@/components/_wedo_internal/governanca/PolicyEnginePanel"

/**
 * /wedo-admin/governanca/policy-engine/ — staff WeDOTalent only.
 *
 * Configuração de políticas de compliance por setor.
 * Backend (policy_tools) é consumido por LIA — intocado nesta migração.
 *
 * Gate: enforce em (staff)/layout.tsx → StaffLayoutClient.tsx.
 */
export default function WedoAdminPolicyEnginePage() {
  return <PolicyEnginePanel />
}
