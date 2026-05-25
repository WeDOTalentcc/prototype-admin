import { AITransparencyPanel } from "@/components/_wedo_internal/governanca/AITransparencyPanel"

/**
 * /wedo-admin/governanca/ai-transparency/ — staff WeDOTalent only.
 *
 * EU AI Act Art. 13/14 (Explainability + Human Oversight) + Annex III.
 * Override reasons viewer.
 *
 * Gate: enforce em (staff)/layout.tsx → StaffLayoutClient.tsx.
 */
export default function WedoAdminAITransparencyPage() {
  return <AITransparencyPanel />
}
