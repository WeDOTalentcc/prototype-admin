import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/interview-notes",
  methods: ["POST"],
  backendTarget: "fastapi",
})
