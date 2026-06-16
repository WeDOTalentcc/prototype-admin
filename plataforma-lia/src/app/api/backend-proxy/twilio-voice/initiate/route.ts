import { NextRequest, NextResponse } from "next/server"
import { proxyFetchWithRetry } from "@/lib/api/proxy-fetch-with-retry"

/**
 * Task #425 — Recruiter-side Twilio PSTN trigger.
 *
 * Forwards InitiateCallRequest payload to backend `/api/v1/twilio-voice/initiate`,
 * which is wrapped by the TWILIO_VOICE_CIRCUIT and validates LGPD consent.
 * Errors (HTTP 451 consent_revoked, 5xx Twilio failures) are surfaced verbatim
 * so the recruiter UI can show a real reason — never a silent success.
 */
export async function POST(req: NextRequest) {
  try {
    const response = await proxyFetchWithRetry(req, "/api/v1/twilio-voice/initiate", {
      method: "POST",
      body: await req.text(),
    })
    return new NextResponse(await response.text(), {
      status: response.status,
      headers: { "Content-Type": "application/json" },
    })
  } catch (e) {
    const message = e instanceof Error ? e.message : "Proxy error"
    return NextResponse.json(
      { success: false, error: "proxy_error", message },
      { status: 502 },
    )
  }
}
