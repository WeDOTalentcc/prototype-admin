import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/wsi/questions/:jobId",
  methods: ["GET"],
  auth: true,
})
