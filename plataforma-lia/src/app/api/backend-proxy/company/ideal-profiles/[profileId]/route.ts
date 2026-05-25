import { createProxyHandlers } from "@/lib/api/proxy-handler"

// Sprint 4 v3 (2026-05-25): GET adicionado para o SourcingTab do TalentPoolPage
// pré-popular inputs a partir do ideal_profile_id do pool. Backend canonical:
//   GET /api/v1/company/ideal-profiles/:profileId (multi-tenant gated)
export const { dynamic, GET, PUT, DELETE } = createProxyHandlers({
  backendPath: "/api/v1/company/ideal-profiles/:profileId",
  methods: ["GET", "PUT", "DELETE"],
  auth: true,
  backendTarget: "fastapi",
})
