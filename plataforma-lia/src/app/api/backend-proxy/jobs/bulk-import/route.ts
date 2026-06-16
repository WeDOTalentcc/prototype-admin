import { createProxyHandlers } from "@/lib/api/proxy-handler"

// Phase 4H — backend-proxy for /api/v1/jobs/bulk-import
// Used by BulkImportModal in jobs-page rail filter "ATS".
// POST: { source, jobs: [...] } → returns batch_id + per-item status
// Backend creates JobVacancy rows with source=ats_import (or ats_external)

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/jobs/bulk-import",
  methods: ["POST"],
  auth: true,
  backendTarget: "fastapi",
})
