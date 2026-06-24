import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/approvals/resolve-by-token",
  methods: ["POST"],
  backendTarget: "fastapi",
})
