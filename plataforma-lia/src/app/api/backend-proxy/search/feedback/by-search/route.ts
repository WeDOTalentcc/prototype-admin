import { createProxyHandlers } from "@/lib/api/proxy-handler"

// Fase 2: re-hidratacao do feedback por fingerprint da busca.
// GET /api/backend-proxy/search/feedback/by-search?fingerprint=...
export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/search/feedback/by-search",
  methods: ["GET"],
  auth: true,
})
