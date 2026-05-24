/**
 * lia-persistence.ts — canonical localStorage helper with TTL.
 *
 * Onda 4-P2-6 (2026-05-24): substitui 4 sites de localStorage cru no
 * unified-chat (lia-chat-mode, lia-chat-width, lia-bubble-position-*,
 * lia-recent-items) que persistiam indefinidamente. Pattern alinhado com
 * canonical do codebase (proxy-fetch-with-retry maxAge, session-crypto
 * expiresAt timestamp, resolve-company-id TENANT_CACHE_TTL_MS).
 *
 * Por que TTL importa:
 * - Usuário pode mudar de máquina/perfil — bubble position fica stale
 * - Width pode persistir valor inválido se UI muda layout
 * - Recent items podem virar lixo (conversation IDs deletadas há meses)
 *
 * Backwards-compat: getPersisted retorna fallback para entries em formato
 * legacy (raw value sem wrapper), forçando re-persist no próximo setPersisted.
 * Zero impacto pro usuário existente — UX equivalente a "primeira visita
 * desta feature".
 */

const TTL_PRESETS = {
  short: 24 * 60 * 60 * 1000,         // 1 day
  medium: 30 * 24 * 60 * 60 * 1000,   // 30 days
  long: 90 * 24 * 60 * 60 * 1000,     // 90 days
} as const

type TTLPreset = keyof typeof TTL_PRESETS

interface PersistedWrapper<T> {
  value: T
  expiresAt: number  // ms epoch
}

function isWrapper<T>(raw: unknown): raw is PersistedWrapper<T> {
  return (
    typeof raw === "object" &&
    raw !== null &&
    "value" in raw &&
    "expiresAt" in raw &&
    typeof (raw as PersistedWrapper<T>).expiresAt === "number"
  )
}

/**
 * Persist value under key with TTL. Default TTL = "long" (90 days).
 * No-op if window/localStorage unavailable (SSR).
 */
export function setPersisted<T>(
  key: string,
  value: T,
  ttl: TTLPreset | number = "long",
): void {
  if (typeof window === "undefined") return
  try {
    const ttlMs = typeof ttl === "string" ? TTL_PRESETS[ttl] : ttl
    const wrapper: PersistedWrapper<T> = {
      value,
      expiresAt: Date.now() + ttlMs,
    }
    window.localStorage.setItem(key, JSON.stringify(wrapper))
  } catch {
    // Quota exceeded, security error (private mode), etc. — fail silently
    // per REGRA 4: log but don't crash UX. localStorage failures must not
    // block render of the chat.
  }
}

/**
 * Retrieve persisted value. Returns fallback if:
 * - key missing
 * - TTL expired (key auto-removed)
 * - legacy raw format (auto-removed; UX falls back, next setPersisted
 *   adopts canonical format)
 * - JSON parse error
 */
export function getPersisted<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback
  try {
    const raw = window.localStorage.getItem(key)
    if (raw === null) return fallback

    let parsed: unknown
    try {
      parsed = JSON.parse(raw)
    } catch {
      // Not JSON (legacy raw string) — remove and fallback
      window.localStorage.removeItem(key)
      return fallback
    }

    if (!isWrapper<T>(parsed)) {
      // JSON but not in canonical wrapper format (legacy plain object/value)
      // Remove and fallback so next setPersisted adopts wrapper.
      window.localStorage.removeItem(key)
      return fallback
    }

    if (parsed.expiresAt < Date.now()) {
      // Expired
      window.localStorage.removeItem(key)
      return fallback
    }

    return parsed.value
  } catch {
    return fallback
  }
}

/**
 * Explicitly remove a persisted key.
 */
export function removePersisted(key: string): void {
  if (typeof window === "undefined") return
  try {
    window.localStorage.removeItem(key)
  } catch {
    // ignore
  }
}

export const LIA_TTL = TTL_PRESETS
