import { AIPerformancePanel } from "@/components/_wedo_internal/governanca/AIPerformancePanel"

/**
 * /wedo-admin/governanca/ai-performance/ — staff WeDOTalent only.
 *
 * A/B testing canonical (Thompson + Bonferroni + Sequential + FairnessGate) — T-19.
 *
 * Gate: enforce em (staff)/layout.tsx → StaffLayoutClient.tsx.
 */
export default function WedoAdminAIPerformancePage() {
  return <AIPerformancePanel />
}
