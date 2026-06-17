// Onda 1 F7 (2026-05-27) — Studio Control Room proxy.
// Backend canonical: GET /api/v1/agent-monitoring/executions/{execution_id}/reasoning
// Retorna decision tree completo + LGPD declarative trail.
// 404 quando reasoning_payload é null (legacy ou agent não-instrumentado).
import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/agent-monitoring/executions/:execution_id/reasoning",
  methods: ["GET"],
  auth: true,
})
