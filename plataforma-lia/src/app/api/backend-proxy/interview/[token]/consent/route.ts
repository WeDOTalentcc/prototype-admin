import { createProxyHandlers } from "@/lib/api/proxy-handler"

/**
 * POST /api/backend-proxy/interview/[token]/consent
 * → POST /api/v1/interview/{token}/consent  (lia-agent-system)
 *
 * PUBLIC endpoint — no JWT required (token acts as auth credential).
 * Records LGPD consent for a triagem session before the candidate starts.
 * Phase 1a LGPD Consent (2026-06-11).
 */
export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/interview/:token/consent",
  methods: ["POST"],
  auth: false,
})
