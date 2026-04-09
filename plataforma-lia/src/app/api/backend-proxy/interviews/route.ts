import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/scheduling/interviews",
  methods: ["GET"],
  backendTarget: "fastapi",
})
