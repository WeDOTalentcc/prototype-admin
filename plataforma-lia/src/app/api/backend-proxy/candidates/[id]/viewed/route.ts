import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST, DELETE } = createProxyHandlers({
  backendPath: "/api/v1/candidates/:id/viewed",
  methods: ["POST", "DELETE"],
  auth: true,
  backendTarget: "fastapi",
})
