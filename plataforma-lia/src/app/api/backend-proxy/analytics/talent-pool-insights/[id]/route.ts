import { createProxyHandlers } from "@/lib/api/proxy-handler"

/**
 * Proxy route for Talent Pool Insights API.
 * GET /api/backend-proxy/analytics/talent-pool-insights/[id]
 *   → FastAPI GET /api/v1/analytics/predictions/talent-pool/{id}
 *
 * Created for TalentPoolInsightsModal (Juicybox pattern, 2026-06-17).
 */
export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/analytics/predictions/talent-pool/:id",
  methods: ["GET"],
  auth: true,
  backendTarget: "fastapi",
})
