import { createProxyHandlers } from "@/lib/api/proxy-handler"

// Onda 2F (audit 2026-06-06): toggle ativar/desativar triagem → PUT screening-status.
export const { dynamic, PUT } = createProxyHandlers({
  backendPath: "/api/v1/vagas/:id/screening-status",
  methods: ["PUT"],
  auth: true,
  backendTarget: "fastapi",
})
