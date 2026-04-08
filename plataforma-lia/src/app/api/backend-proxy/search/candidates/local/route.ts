import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/search/candidates/local",
  methods: ["GET"],
  auth: true,
})
