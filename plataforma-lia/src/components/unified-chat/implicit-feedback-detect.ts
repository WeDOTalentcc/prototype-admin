/**
 * Task #1299 — client-side classifier for two IMPLICIT feedback signals that
 * are observable at send-time, WITHOUT any UI/layout change:
 *
 *   - `correction_delta`: the recruiter's next message strongly REUSES the
 *     prior LIA answer but is not identical → an edited/corrected version.
 *   - `abandonment`: the recruiter IGNORES a substantive LIA answer and sends
 *     an unrelated message → a topic switch (weak negative).
 *
 * This is only a cheap pre-filter so the chat doesn't POST a signal on every
 * mundane turn. The BACKEND (`ImplicitFeedbackService`) is the authoritative
 * gate: it re-applies the FairnessGuard check and the conservative abandonment
 * criterion before anything is persisted. Keep the thresholds here in step with
 * `is_abandonment_candidate` in
 * `lia-agent-system/app/shared/learning/implicit_feedback_service.py`.
 */

// Mirror of the backend thresholds (deliberately conservative).
export const CORRECTION_OVERLAP_MIN = 0.45
export const ABANDON_MIN_RESPONSE_CHARS = 60
export const ABANDON_MIN_NEXT_WORDS = 4
export const ABANDON_MAX_TOKEN_OVERLAP = 0.08

const WORD_RE = /[a-zà-ÿ0-9]+/giu

// PT-BR continuation/confirmation tokens — a next message that IS one of these
// is engagement (answering LIA), never abandonment.
const CONTINUATION_TOKENS = new Set([
  'sim', 'claro', 'ok', 'okay', 'beleza', 'isso', 'pode', 'vamos', 'vai',
  'certo', 'perfeito', 'obrigado', 'obrigada', 'valeu', 'concordo', 'aceito',
  'não', 'nao', 'negativo', 'continua', 'continuar', 'prossiga', 'segue',
])

const STOPWORDS = new Set([
  'a', 'o', 'as', 'os', 'um', 'uma', 'de', 'da', 'do', 'das', 'dos', 'em',
  'no', 'na', 'nos', 'nas', 'e', 'ou', 'que', 'para', 'pra', 'por', 'com',
  'se', 'sua', 'seu', 'the', 'to', 'of', 'and', 'is', 'in', 'you', 'me',
  'eu', 'voce', 'você', 'ao', 'aos', 'à', 'às', 'mais', 'como', 'isso',
])

function tokenize(text: string | null | undefined): Set<string> {
  if (!text) return new Set()
  const out = new Set<string>()
  for (const m of text.matchAll(WORD_RE)) {
    const t = m[0].toLowerCase()
    if (t.length > 1 && !STOPWORDS.has(t)) out.add(t)
  }
  return out
}

export function tokenOverlap(
  a: string | null | undefined,
  b: string | null | undefined,
): number {
  const ta = tokenize(a)
  const tb = tokenize(b)
  if (ta.size === 0 || tb.size === 0) return 0
  let inter = 0
  for (const t of ta) if (tb.has(t)) inter++
  const union = ta.size + tb.size - inter
  return union ? inter / union : 0
}

function wordCount(text: string): number {
  const m = text.match(WORD_RE)
  return m ? m.length : 0
}

/** Conservative abandonment pre-check, mirroring the backend criterion. */
export function isAbandonmentCandidate(
  liaResponse: string | null | undefined,
  nextUserMessage: string | null | undefined,
): boolean {
  const resp = (liaResponse ?? '').trim()
  const nxt = (nextUserMessage ?? '').trim()
  if (resp.length < ABANDON_MIN_RESPONSE_CHARS) return false
  if (resp.endsWith('?')) return false
  if (wordCount(nxt) < ABANDON_MIN_NEXT_WORDS) return false
  if (CONTINUATION_TOKENS.has(nxt.toLowerCase().replace(/[?.! ]+$/, ''))) return false
  return tokenOverlap(resp, nxt) <= ABANDON_MAX_TOKEN_OVERLAP
}

export type ImplicitSignalType = 'correction_delta' | 'abandonment'

/**
 * Classify the relationship between the prior LIA answer and the recruiter's
 * next message. Returns the signal to report, or `null` when the turn is
 * ordinary (verbatim accept, continuation, or ambiguous middle ground).
 */
export function classifyImplicitSignal(
  priorLiaText: string | null | undefined,
  sentText: string | null | undefined,
): ImplicitSignalType | null {
  const prior = (priorLiaText ?? '').trim()
  const sent = (sentText ?? '').trim()
  if (!prior || !sent) return null
  if (prior === sent) return null // verbatim reuse → not a correction

  if (tokenOverlap(prior, sent) >= CORRECTION_OVERLAP_MIN) {
    return 'correction_delta'
  }
  if (isAbandonmentCandidate(prior, sent)) {
    return 'abandonment'
  }
  return null
}
