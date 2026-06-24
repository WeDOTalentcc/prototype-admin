import { createProxyHandlers } from "@/lib/api/proxy-handler"

/**
 * POST /api/backend-proxy/interview/[token]/start-whatsapp
 * → POST /api/v1/triagem/{token}/start-whatsapp  (lia-agent-system)
 *
 * PUBLIC endpoint — no JWT required (token acts as auth credential).
 * Sends a WhatsApp consent/screening message to the candidate.
 *
 * Body: { candidate_phone?: string }
 *   candidate_phone is optional if already stored in session metadata.
 *
 * Phase 1a LGPD Consent (2026-06-11).
 */
export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/triagem/:token/start-whatsapp",
  methods: ["POST"],
  auth: false,
})
