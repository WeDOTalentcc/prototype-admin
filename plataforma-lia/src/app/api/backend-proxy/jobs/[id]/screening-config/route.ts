import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, PUT } = createProxyHandlers({
  backendPath: "/api/v1/vagas/:id/screening-config",
  methods: ["GET", "PUT"],
  auth: true,
  backendTarget: "fastapi",
})
