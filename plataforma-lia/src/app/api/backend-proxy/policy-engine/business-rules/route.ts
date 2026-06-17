import { createProxyHandlers } from "@/lib/api/proxy-handler"

// POST creates a business rule; backend reads company_id from JWT (get_verified_company_id).
export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/policy-engine/business-rules",
  methods: ["POST"],
  auth: true,
})
