import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/search/contextual-hints",
  methods: ["GET"],
  backendTarget: "fastapi",
})
