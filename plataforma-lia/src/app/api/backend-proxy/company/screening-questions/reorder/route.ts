// DEAD CODE P2-W1-05: este proxy existe mas nenhum componente o chama diretamente.
// Manter até confirmar que pode ser removido com segurança (ver audit Wave 1 2026-05-24).
// grep -r 'screening-questions/reorder' src/ --include='*.ts' --include='*.tsx' | grep -v route.ts
import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/company/screening-questions/reorder",
  methods: ["POST"],
  auth: true,
  backendTarget: "fastapi",
})
