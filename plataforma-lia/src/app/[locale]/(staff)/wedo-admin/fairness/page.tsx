import { FairnessDashboard } from "@/components/_wedo_internal/fairness/FairnessDashboard"

/**
 * /wedo-admin/fairness/ — staff WeDOTalent only.
 *
 * Renderiza FairnessDashboard (Features 1 + 4 do plan canonical):
 * - Sumário de eventos/bloqueios/alertas por período
 * - Gráfico por categoria (Recharts)
 * - Export CSV/JSON
 * - Tabela de incidentes recentes
 *
 * Para drill-down de bias audit (Four-Fifths Rule, dimensões),
 * vide `/wedo-admin/fairness/bias-audit/`.
 *
 * Gate: enforce em `(staff)/layout.tsx` → `StaffLayoutClient.tsx`.
 */
export default function WedoAdminFairnessPage() {
  return <FairnessDashboard />
}
