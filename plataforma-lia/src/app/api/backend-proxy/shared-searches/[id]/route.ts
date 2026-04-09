import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, DELETE, PATCH } = createProxyHandlers({
  backendPath: "/api/v1/shared-searches/:id",
  methods: ["GET", "DELETE", "PATCH"],
  backendTarget: "fastapi",
})
