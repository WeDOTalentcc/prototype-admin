import { createProxyHandlers } from "@/lib/api/proxy-handler"

// Phase C.2 backend / Phase A.3 frontend — proxy for POST
// /api/v1/job-vacancies/{id}/unpublish. Symmetric to /publish; clears
// published_* flags. Recruiter triggers via JobPublishModal.onUnpublish
// from the vacancy preview side panel.
export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/job-vacancies/:id/unpublish",
  methods: ["POST"],
  backendTarget: "fastapi",
})
