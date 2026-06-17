import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/chat/actions/candidate-field-update",
  methods: ["POST"],
})
