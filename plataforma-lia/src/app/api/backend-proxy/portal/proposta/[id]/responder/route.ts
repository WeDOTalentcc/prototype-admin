import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/portal/proposta/:id/responder",
  methods: ["POST"],
  auth: false,
})
