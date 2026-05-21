import { z } from "zod"
import { createProxyHandlers } from "@/lib/api/proxy-handler"

// T-21c admin revoke company-level training data consent (LGPD Art. 18 cascade)
const revokeSchema = z.object({
  reason: z.string().min(1),
})

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/admin/consent/company-training-consent/revoke",
  methods: ["POST"],
  backendTarget: "fastapi",
  bodySchema: revokeSchema,
})
