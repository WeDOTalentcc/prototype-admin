/**
 * Wave 2 Agent B / T-13 — Admin Prompts list endpoint (canonical proxy).
 *
 * GET /api/backend-proxy/admin/prompts/tenant-overrides
 *   → Lista todos os overrides YAML do tenant (company_id do JWT backend).
 */
import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/admin/prompts/tenant-overrides",
  methods: ["GET"],
  auth: true,
  backendTarget: "fastapi",
})
