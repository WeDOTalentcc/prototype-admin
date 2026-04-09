import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, POST } = createProxyHandlers({
  backendPath: "/api/v1/shared-searches",
  methods: ["GET", "POST"],
  backendTarget: "fastapi",
})
