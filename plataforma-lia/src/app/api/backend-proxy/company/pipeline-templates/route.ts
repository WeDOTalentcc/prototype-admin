import { createProxyHandlers } from "@/lib/api/proxy-handler"

// Criar/listar templates pode incluir cold-start do backend (reload em dev) +
// audit logging em sessao separada. O default de 10s do proxy corta cedo demais
// e gera 504 espurio; 30s da folga sem mascarar uma indisponibilidade real.
export const { dynamic, GET, POST } = createProxyHandlers({
  backendPath: "/api/v1/company/pipeline-templates/",
  methods: ["GET", "POST"],
  auth: true,
  backendTarget: "fastapi",
  timeoutMs: 30000,
})
