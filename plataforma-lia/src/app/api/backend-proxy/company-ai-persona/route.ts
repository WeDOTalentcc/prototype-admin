/**
 * E2.4 (audit 2026-05-21) — Next proxy para o endpoint canonical
 * /api/v1/company-ai-persona em lia-agent-system.
 *
 * Mantém shape transparente: GET retorna {name, tone}; PUT recebe
 * {name?, tone?} e retorna {name, tone}. Erros 422 do backend
 * (validator) propagam intactos para o UI renderizar inline.
 */
import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, PUT } = createProxyHandlers({
  backendPath: "/api/v1/company-ai-persona",
  methods: ["GET", "PUT"],
  auth: true,
  backendTarget: "fastapi",
})
