import { AuditLogsDrillDownPanel } from "@/components/_wedo_internal/governanca/AuditLogsDrillDownPanel"

/**
 * /wedo-admin/governanca/audit-logs/ — staff WeDOTalent only.
 *
 * Drill-down completo de audit logs (LGPD Art. 37 V).
 * Cliente DPO acessa apenas o summary read-only via
 * /configuracoes?section=fairness-compliance&subsection=audit-summary.
 *
 * Gate: enforce em (staff)/layout.tsx → StaffLayoutClient.tsx.
 */
export default function WedoAdminAuditLogsPage() {
  return <AuditLogsDrillDownPanel />
}
