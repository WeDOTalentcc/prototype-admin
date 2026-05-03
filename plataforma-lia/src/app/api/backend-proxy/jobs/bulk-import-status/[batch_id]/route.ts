import { createProxyHandlers } from "@/lib/api/proxy-handler"

// Phase 4I — poll bulk-import batch status
// GET /api/backend-proxy/jobs/bulk-import-status/{batch_id}
//   → backend GET /api/v1/jobs/bulk-import/{batch_id}/status
//
// Used by BulkImportModal to track long-running imports (1000+ vagas).
// Synchronous POST handles small batches; this proxy supports polling
// when the import duration exceeds the synchronous response window.

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/jobs/bulk-import/:batch_id/status",
  methods: ["GET"],
  auth: true,
  backendTarget: "fastapi",
})
