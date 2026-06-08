import { describe, it, expect } from "vitest"
import {
  getTimeOfDay,
  selectGreeting,
  type GreetingBriefingInput,
} from "./dynamic-greeting"

const emptyBriefing: GreetingBriefingInput = {
  activeJobs: 0,
  candidatesToContact: 0,
  awaitingFeedback: 0,
  offersPending: 0,
  interviewsToday: 0,
}

const at = (h: number) => new Date(2026, 5, 5, h, 0, 0)

describe("getTimeOfDay", () => {
  it("mapeia faixas horárias", () => {
    expect(getTimeOfDay(at(8))).toBe("morning")
    expect(getTimeOfDay(at(11))).toBe("morning")
    expect(getTimeOfDay(at(12))).toBe("afternoon")
    expect(getTimeOfDay(at(17))).toBe("afternoon")
    expect(getTimeOfDay(at(18))).toBe("evening")
    expect(getTimeOfDay(at(23))).toBe("evening")
  })
})

describe("selectGreeting — fallback curado", () => {
  it("chat sem briefing e sem nome → curada plain (não named)", () => {
    const plan = selectGreeting({ surface: "chat", now: at(9), briefing: null, name: null, seed: 3 })
    expect(plan.kind).toBe("curated")
    if (plan.kind === "curated") {
      expect(plan.named).toBe(false)
      expect(plan.index).toBe(3)
    }
  })

  it("chat sem briefing COM nome → curada named com timeKey", () => {
    const plan = selectGreeting({ surface: "chat", now: at(9), briefing: null, name: "Ana", seed: 1 })
    expect(plan.kind).toBe("curated")
    if (plan.kind === "curated") {
      expect(plan.named).toBe(true)
      expect(plan.name).toBe("Ana")
      expect(plan.timeKey).toBe("morning")
    }
  })

  it("funnel nunca usa nome no curado", () => {
    const plan = selectGreeting({ surface: "funnel", now: at(14), briefing: null, name: "Ana", seed: 2 })
    expect(plan.kind).toBe("curated")
    if (plan.kind === "curated") expect(plan.named).toBe(false)
  })

  it("variedade: seeds diferentes → índices diferentes", () => {
    const a = selectGreeting({ surface: "chat", now: at(9), briefing: null, name: null, seed: 10 })
    const b = selectGreeting({ surface: "chat", now: at(9), briefing: null, name: null, seed: 27 })
    if (a.kind === "curated" && b.kind === "curated") {
      expect(a.index).not.toBe(b.index)
    }
  })

  it("nome só de espaços é tratado como ausente", () => {
    const plan = selectGreeting({ surface: "chat", now: at(9), briefing: null, name: "   ", seed: 0 })
    if (plan.kind === "curated") expect(plan.named).toBe(false)
  })

  it("briefing presente mas sem sinal → curada", () => {
    const plan = selectGreeting({ surface: "chat", now: at(9), briefing: emptyBriefing, name: "Ana", seed: 0 })
    // chat com nome + briefing zerado → allClear (contextual)
    expect(plan.kind).toBe("context")
    if (plan.kind === "context") expect(plan.key).toBe("allClear")
  })

  it("funnel briefing zerado → curada (sem allClear)", () => {
    const plan = selectGreeting({ surface: "funnel", now: at(9), briefing: emptyBriefing, name: "Ana", seed: 5 })
    expect(plan.kind).toBe("curated")
  })
})

describe("selectGreeting — contextual chat (prioridade)", () => {
  it("entrevistas + feedback ganham prioridade máxima", () => {
    const plan = selectGreeting({
      surface: "chat",
      now: at(9),
      briefing: { ...emptyBriefing, interviewsToday: 2, awaitingFeedback: 5, candidatesToContact: 9 },
      name: "Ana",
      seed: 0,
    })
    expect(plan.kind).toBe("context")
    if (plan.kind === "context") {
      expect(plan.key).toBe("interviewsAndFeedback")
      expect(plan.counts).toEqual({ interviews: 2, feedback: 5 })
      expect(plan.name).toBe("Ana")
      expect(plan.timeKey).toBe("morning")
    }
  })

  it("só entrevistas", () => {
    const plan = selectGreeting({ surface: "chat", now: at(9), briefing: { ...emptyBriefing, interviewsToday: 1 }, name: "Ana", seed: 0 })
    if (plan.kind === "context") {
      expect(plan.key).toBe("interviewsToday")
      expect(plan.counts).toEqual({ count: 1 })
    }
  })

  it("candidatos a contatar", () => {
    const plan = selectGreeting({ surface: "chat", now: at(9), briefing: { ...emptyBriefing, candidatesToContact: 4 }, name: "Ana", seed: 0 })
    if (plan.kind === "context") expect(plan.key).toBe("candidatesToContact")
  })

  it("propostas pendentes", () => {
    const plan = selectGreeting({ surface: "chat", now: at(9), briefing: { ...emptyBriefing, offersPending: 3 }, name: "Ana", seed: 0 })
    if (plan.kind === "context") expect(plan.key).toBe("offersPending")
  })

  it("chat com briefing+sinal mas SEM nome → contextual anon (não curada)", () => {
    const plan = selectGreeting({ surface: "chat", now: at(9), briefing: { ...emptyBriefing, interviewsToday: 2 }, name: null, seed: 7 })
    expect(plan.kind).toBe("context")
    if (plan.kind === "context") {
      expect(plan.key).toBe("interviewsTodayAnon")
      expect(plan.name).toBe("")
    }
  })

  it("chat briefing+sinal SEM nome: todas as variantes retornam contextual anon", () => {
    const cases: Array<[Partial<GreetingBriefingInput>, string]> = [
      [{ interviewsToday: 1, awaitingFeedback: 2 }, "interviewsAndFeedbackAnon"],
      [{ interviewsToday: 1 }, "interviewsTodayAnon"],
      [{ candidatesToContact: 3 }, "candidatesToContactAnon"],
      [{ offersPending: 1 }, "offersPendingAnon"],
      [{}, "allClearAnon"],
    ]
    for (const [partial, expectedKey] of cases) {
      const plan = selectGreeting({
        surface: "chat",
        now: at(9),
        briefing: { ...emptyBriefing, ...partial },
        name: null,
        seed: 0,
      })
      expect(plan.kind).toBe("context")
      if (plan.kind === "context") expect(plan.key).toBe(expectedKey)
    }
  })
})

describe("selectGreeting — contextual funnel", () => {
  it("vagas abertas + candidatos a contatar", () => {
    const plan = selectGreeting({ surface: "funnel", now: at(9), briefing: { ...emptyBriefing, activeJobs: 3, candidatesToContact: 6 }, name: null, seed: 0 })
    if (plan.kind === "context") {
      expect(plan.key).toBe("openJobsAndContacts")
      expect(plan.counts).toEqual({ jobs: 3, contacts: 6 })
    }
  })

  it("só vagas abertas", () => {
    const plan = selectGreeting({ surface: "funnel", now: at(9), briefing: { ...emptyBriefing, activeJobs: 2 }, name: null, seed: 0 })
    if (plan.kind === "context") {
      expect(plan.key).toBe("openJobs")
      expect(plan.counts).toEqual({ count: 2 })
    }
  })

  it("só candidatos a contatar", () => {
    const plan = selectGreeting({ surface: "funnel", now: at(9), briefing: { ...emptyBriefing, candidatesToContact: 8 }, name: null, seed: 0 })
    if (plan.kind === "context") expect(plan.key).toBe("candidatesToContact")
  })
})
