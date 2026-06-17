import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, PATCH } = createProxyHandlers({
  backendPath: "/api/v1/sourcing-agents/:id/:action",
  methods: ["PATCH"],
  auth: true,
  backendTarget: "fastapi",
})
