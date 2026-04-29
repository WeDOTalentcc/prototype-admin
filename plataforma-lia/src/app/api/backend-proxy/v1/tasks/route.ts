/**
 * Proxy: GET /api/backend-proxy/v1/tasks -> FastAPI /api/v1/tasks/
 *
 * Onda 30 D — used by useActiveTasks() to populate the TaskContextBar
 * dropdown with the current user's in-progress tasks.
 *
 * Auth: forwards JWT via getAuthHeaders. Backend MUST filter by current_user
 * (see separate P0 issue tracking enforcement of company_id from JWT).
 */
import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/tasks/",
  methods: ["GET"],
  backendTarget: "fastapi",
})
