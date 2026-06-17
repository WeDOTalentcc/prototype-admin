import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/shared-searches/:id/add-to-job",
  methods: ["POST"],
  backendTarget: "fastapi",
})
