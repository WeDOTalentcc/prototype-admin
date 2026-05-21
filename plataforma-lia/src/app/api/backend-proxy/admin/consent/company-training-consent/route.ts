import { createProxyHandlers } from "@/lib/api/proxy-handler"

// T-21c admin company-level training data consent (ADR-RLHF-001)
// GET → /api/v1/admin/consent/company-training-consent
export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/admin/consent/company-training-consent",
  methods: ["GET"],
  backendTarget: "fastapi",
})
