import { createProxyHandlers } from "@/lib/api/proxy-handler"

// Phase D.1 — proxy for GET /api/v1/ats/connections/{id}/jobs
// Backend impl: app/api/v1/ats.py::list_remote_jobs (Phase C.3).
// Consumed by BulkImportModal's "ATS Conectado" tab to list available
// vagas before selective import.
export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/ats/connections/:connectionId/jobs",
  methods: ["GET"],
})
