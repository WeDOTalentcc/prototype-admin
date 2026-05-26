/**
 * POST /api/backend-proxy/job-vacancies/{id}/apply-pipeline-template
 *
 * Fase 3 (Pipeline Template auto-suggest no wizard chat).
 *
 * Forward para o backend FastAPI:
 *   POST /api/v1/vacancies/{vacancy_id}/apply-pipeline-template
 *
 * Body esperado:
 *   { "template_id": "<uuid>", "source": "wizard_explicit" | "wizard_auto" }
 *
 * Auth: JWT forwarded via `createProxyHandlers` (auth: true). Multi-tenancy
 * canonical — `company_id` é resolvido server-side pelo backend a partir do
 * JWT (vide REGRA 6 Pydantic Conventions: nunca trustar body).
 *
 * Pattern canonical: idêntico aos demais proxies do mesmo nível
 * (e.g. company/pipeline-templates/[id], commit a3af84c45).
 */
import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/vacancies/:id/apply-pipeline-template",
  methods: ["POST"],
  auth: true,
  backendTarget: "fastapi",
})
