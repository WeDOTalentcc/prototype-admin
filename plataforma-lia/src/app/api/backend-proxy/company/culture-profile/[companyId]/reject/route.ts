import { createProxyHandlers } from "@/lib/api/proxy-handler"

// Fase 5.1 — HITL approval gate for auto-generated culture profiles.
export const { dynamic, PATCH } = createProxyHandlers({
  backendPath: "/api/v1/company/culture-profile/:companyId/reject",
  methods: ["PATCH"],
  auth: true,
})
