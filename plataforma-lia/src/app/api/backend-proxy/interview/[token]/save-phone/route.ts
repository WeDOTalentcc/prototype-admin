import { createProxyHandlers } from "@/lib/api/proxy-handler"

/**
 * POST /api/backend-proxy/interview/[token]/save-phone
 * → POST /api/v1/triagem/{token}/start-whatsapp  (lia-agent-system)
 *
 * PUBLIC endpoint — no JWT required (token acts as auth credential).
 * Saves candidate phone number to session metadata AND sends the WhatsApp
 * screening consent message.
 *
 * Body: { candidate_phone: string }  — required (E.164 or BR format)
 *
 * Alias of start-whatsapp that makes the intent clear: save phone + kick off WA.
 * Phase 1a LGPD Consent (2026-06-11).
 */
export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/triagem/:token/start-whatsapp",
  methods: ["POST"],
  auth: false,
})
