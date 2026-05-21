import { z } from "zod"
import { createProxyHandlers } from "@/lib/api/proxy-handler"

// T-21c admin grant company-level training data consent (LGPD Art. 7 §I)
const grantSchema = z.object({
  consent_text: z.string().min(1),
  version: z.string().optional(),
  ip_address: z.string().nullable().optional(),
})

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/admin/consent/company-training-consent/grant",
  methods: ["POST"],
  backendTarget: "fastapi",
  bodySchema: grantSchema,
})
