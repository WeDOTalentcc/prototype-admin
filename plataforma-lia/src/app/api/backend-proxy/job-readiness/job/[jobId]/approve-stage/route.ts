import { createProxyHandlers } from "@/lib/api/proxy-handler"

// Phase I.1 — proxy for POST /api/v1/job-readiness/job/{id}/approve-stage
// Backend impl: lia-agent-system/app/api/v1/job_readiness.py:389.
// Triggered from VacancyPreview when vaga is in stage 'wsi_config'.
// Sets approval_status='pendente' + approval_requested_at, advancing
// the vaga to 'aguardando_aprovacao'.
export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/job-readiness/job/:jobId/approve-stage",
  methods: ["POST"],
})
