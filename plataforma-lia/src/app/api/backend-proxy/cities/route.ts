import { createProxyHandlers } from "@/lib/api/proxy-handler"

// Onda 2B (audit 2026-06-06): autocomplete de cidades (dataset global IBGE no FastAPI).
export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/cities",
  methods: ["GET"],
  auth: true,
  backendTarget: "fastapi",
})
