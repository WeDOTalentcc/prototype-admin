import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, POST } = createProxyHandlers({
  backendPath: "/api/v1/candidate-lists",
  methods: ["GET", "POST"],
  backendTarget: "fastapi",
})
