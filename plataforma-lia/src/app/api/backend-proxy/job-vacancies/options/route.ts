import { createProxyHandlers } from "@/lib/api/proxy-handler"

// Onda 1 (audit 2026-06-06): canonical vocabularies for the vacancy form dropdowns.
// FastAPI is the single source of truth (Rails fora do fluxo).
export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/job-vacancies/options",
  methods: ["GET"],
  auth: true,
  backendTarget: "fastapi",
})
