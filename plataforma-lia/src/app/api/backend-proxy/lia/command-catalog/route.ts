import { createProxyHandlers } from "@/lib/api/proxy-handler"

// Fase 2 (2026-06-06): catálogo de comandos acionáveis da LIA (Ctrl+/ + Cmd+K),
// derivado do capability_map no backend.
export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/lia/command-catalog",
})
