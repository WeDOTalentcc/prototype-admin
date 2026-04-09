import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST, DELETE } = createProxyHandlers({
  backendPath: "/api/v1/candidates/:id/hide",
  methods: ["POST", "DELETE"],
  auth: true,
  backendTarget: "fastapi",
})
