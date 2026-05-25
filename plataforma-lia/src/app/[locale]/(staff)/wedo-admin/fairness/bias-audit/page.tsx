import { BiasAuditPanel } from "@/components/_wedo_internal/fairness/BiasAuditPanel"

/**
 * /wedo-admin/fairness/bias-audit/ — staff WeDOTalent only.
 *
 * Renderiza BiasAuditPanel (Feature 2 do plan canonical):
 * - Logs em tempo real
 * - Drill-down por Job ID (Four-Fifths Rule, Adverse Impact Ratio)
 * - Tabela paginada de audits recentes
 *
 * Gate: enforce em `(staff)/layout.tsx` → `StaffLayoutClient.tsx`.
 */
export default function WedoAdminBiasAuditPage() {
  return <BiasAuditPanel />
}
