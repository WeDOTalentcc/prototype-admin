import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST, PUT, DELETE } = createProxyHandlers({
  backendPath: "/api/v1/candidates/:id/favorite",
  methods: ["POST", "PUT", "DELETE"],
  auth: true,
  backendTarget: "fastapi",
})
