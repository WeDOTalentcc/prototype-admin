/**
 * dynamic-greeting — núcleo PURO (sem React/next-intl) que DECIDE qual frase de
 * abertura usar nas superfícies "chat" e "funnel".
 *
 * A decisão (contextual vs curada, qual chave i18n, quais contagens) vive aqui e
 * é testável sem React. A RENDERIZAÇÃO/i18n fica no hook `useDynamicGreeting`.
 *
 * Direção (Task #1315 / Opção B): contextual com dados reais do briefing diário,
 * caindo para uma rotação de frases curadas quando não houver dados.
 */

export type GreetingSurface = "chat" | "funnel"

export type TimeOfDayKey = "morning" | "afternoon" | "evening"

/** Subconjunto do briefing diário relevante para as frases de abertura. */
export interface GreetingBriefingInput {
  activeJobs: number
  candidatesToContact: number
  awaitingFeedback: number
  offersPending: number
  interviewsToday: number
}

export type GreetingPlan =
  | {
      kind: "context"
      /** chave sob `dynamicGreetings.<surface>.context.<key>` */
      key: string
      timeKey: TimeOfDayKey
      name: string
      counts: Record<string, number>
    }
  | {
      kind: "curated"
      /** índice bruto; o hook aplica `% pool.length` */
      index: number
      named: boolean
      timeKey: TimeOfDayKey
      name?: string
    }

export interface SelectGreetingArgs {
  surface: GreetingSurface
  now: Date
  briefing: GreetingBriefingInput | null
  name?: string | null
  /** semente de variedade (fixada uma vez por montagem no hook) */
  seed: number
}

export function getTimeOfDay(now: Date): TimeOfDayKey {
  const hour = now.getHours()
  if (hour < 12) return "morning"
  if (hour < 18) return "afternoon"
  return "evening"
}

/**
 * Decide o plano de saudação. Nunca lança — sempre retorna um plano renderizável
 * (contextual quando há dados+nome; senão, curada com fallback garantido).
 */
export function selectGreeting(args: SelectGreetingArgs): GreetingPlan {
  const { surface, now, briefing, name, seed } = args
  const timeKey = getTimeOfDay(now)
  const trimmedName = name?.trim() ? name.trim() : undefined
  const index = Math.abs(Math.trunc(seed))

  if (briefing) {
    if (surface === "chat") {
      // Templates contextuais do chat: usa {name} quando disponível; quando ausente,
      // usa a variante "*Anon" (mesmo key sem {name}) — contexto prevalece sobre curado.
      const { interviewsToday, awaitingFeedback, candidatesToContact, offersPending } = briefing
      const anon = trimmedName ? "" : "Anon"
      const name = trimmedName ?? ""
      if (interviewsToday > 0 && awaitingFeedback > 0) {
        return {
          kind: "context",
          key: `interviewsAndFeedback${anon}`,
          timeKey,
          name,
          counts: { interviews: interviewsToday, feedback: awaitingFeedback },
        }
      }
      if (interviewsToday > 0) {
        return { kind: "context", key: `interviewsToday${anon}`, timeKey, name, counts: { count: interviewsToday } }
      }
      if (candidatesToContact > 0) {
        return { kind: "context", key: `candidatesToContact${anon}`, timeKey, name, counts: { count: candidatesToContact } }
      }
      if (offersPending > 0) {
        return { kind: "context", key: `offersPending${anon}`, timeKey, name, counts: { count: offersPending } }
      }
      if (awaitingFeedback > 0) {
        return { kind: "context", key: `awaitingFeedback${anon}`, timeKey, name, counts: { count: awaitingFeedback } }
      }
      // Briefing presente mas sem sinal relevante → allClear.
      return { kind: "context", key: `allClear${anon}`, timeKey, name, counts: {} }
    } else {
      // funnel — templates não usam nome.
      const { activeJobs, candidatesToContact } = briefing
      if (activeJobs > 0 && candidatesToContact > 0) {
        return { kind: "context", key: "openJobsAndContacts", timeKey, name: "", counts: { jobs: activeJobs, contacts: candidatesToContact } }
      }
      if (activeJobs > 0) {
        return { kind: "context", key: "openJobs", timeKey, name: "", counts: { count: activeJobs } }
      }
      if (candidatesToContact > 0) {
        return { kind: "context", key: "candidatesToContact", timeKey, name: "", counts: { count: candidatesToContact } }
      }
    }
  }

  // Fallback curado (sem briefing, sem nome no chat, ou briefing sem sinal).
  const named = surface === "chat" && !!trimmedName
  return { kind: "curated", index, named, timeKey, name: trimmedName }
}
