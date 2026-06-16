import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/portal/proposta/:id/visualizado",
  methods: ["POST"],
  auth: false,
})
