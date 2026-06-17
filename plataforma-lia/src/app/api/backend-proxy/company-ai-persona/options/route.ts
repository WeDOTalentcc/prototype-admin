/**
 * F3.2 (audit 2026-05-24) — Next proxy para /api/v1/company-ai-persona/options
 * em lia-agent-system. Retorna catálogo canonical de tons + constraints de
 * nome para a UI da tab "Personalidade da IA" renderizar.
 *
 * Read-only — só GET. Sem variantes per-tenant (catálogo é WeDOTalent-wide),
 * mas exige JWT (auth: true) para consistência com o resto do recurso.
 */
import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/company-ai-persona/options",
  methods: ["GET"],
  auth: true,
  backendTarget: "fastapi",
})
