// Sensor RRP — state-aware (AD7) + contrato i18n do ResponseBlockRenderer.
// AD16: testa a FUNCAO de resolucao (layout × mode), nao screenshot.
//   - fullscreen: comparison_table renderiza como <table> (wide)
//   - sidebar/floating: transpoe (sem <table>) — degradacao sem scroll-h
//   - i18n: zero MISSING_MESSAGE nas chaves rrp.* (usa messages/pt-BR.json real)
import { describe, expect, it } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"
import React from "react"

import { ResponseBlockRenderer } from "../ResponseBlockRenderer"
import ptBR from "../../../../messages/pt-BR.json"
import type { ResponseBlock } from "@/types/rrp-blocks"

const TABLE: ResponseBlock = {
  kind: "comparison_table",
  block_id: "comparison_table:rank:job1",
  role: "support",
  layout: "wide",
  state: "ready",
  title: "Ranking de candidatos",
  entity_type: "candidate",
  columns: [
    { key: "name", label: "Candidato", type: "text", sortable: true },
    { key: "score", label: "Score LIA", type: "score", sortable: true },
  ],
  rows: [
    {
      entity_id: "1",
      cells: { name: "Ana", score: 92 },
      score_block_id: null,
      highlight: "top",
    },
    {
      entity_id: "2",
      cells: { name: "Bruno", score: 64 },
      score_block_id: null,
      highlight: null,
    },
  ],
  default_sort: null,
  total_count: 5,
  shown_count: 2,
}

function renderWith(blocks: ResponseBlock[], mode?: string) {
  const errors: string[] = []
  const utils = render(
    <NextIntlClientProvider
      locale="pt"
      messages={ptBR as unknown as Record<string, unknown>}
      onError={(e) => errors.push(String((e as { code?: string }).code || e.message))}
    >
      <ResponseBlockRenderer blocks={blocks} mode={mode} />
    </NextIntlClientProvider>,
  )
  return { ...utils, errors }
}

describe("ResponseBlockRenderer — state-aware (AD7) + i18n", () => {
  it("fullscreen: comparison_table renderiza como <table>", () => {
    const { container } = renderWith([TABLE], "fullscreen")
    expect(container.querySelector("table")).toBeTruthy()
    expect(screen.getByText("Ana")).toBeTruthy()
  })

  it("sidebar: comparison_table transpoe (sem <table>)", () => {
    const { container } = renderWith([TABLE], "sidebar")
    expect(container.querySelector("table")).toBeNull()
    expect(screen.getByText("Ana")).toBeTruthy()
  })

  it("floating: comparison_table transpoe (sem <table>)", () => {
    const { container } = renderWith([TABLE], "floating")
    expect(container.querySelector("table")).toBeNull()
  })

  it("i18n: zero MISSING_MESSAGE nas chaves rrp.* (showingOf etc)", () => {
    const { errors } = renderWith([TABLE], "sidebar")
    expect(errors.filter((e) => e.includes("MISSING_MESSAGE"))).toEqual([])
  })

  it("blocks vazio/nulo nao quebra", () => {
    const { container } = renderWith([], "fullscreen")
    expect(container.textContent).toBe("")
  })
})


const FUNNEL: ResponseBlock = {
  kind: "funnel",
  block_id: "funnel:pipeline:Diretor",
  role: "support",
  layout: "wide",
  state: "ready",
  title: "Pipeline (Diretor Juridico)",
  stages: [
    { label: "Triagem", count: 12 },
    { label: "Entrevista", count: 5 },
    { label: "Contratado", count: 1 },
  ],
  total: 18,
  conversion_rate: 5.6,
}

describe("ResponseBlockRenderer — funnel (Fase 1)", () => {
  it("renderiza etapas + contagens nos 3 estados", () => {
    for (const mode of ["fullscreen", "sidebar", "floating"]) {
      const { unmount } = renderWith([FUNNEL], mode)
      expect(screen.getByText("Triagem")).toBeTruthy()
      expect(screen.getByText("Entrevista")).toBeTruthy()
      expect(screen.getByText("12")).toBeTruthy()
      unmount()
    }
  })

  it("mostra total, conversao e retencao % por etapa", () => {
    renderWith([FUNNEL], "fullscreen")
    expect(screen.getByText(/Total: 18/)).toBeTruthy()
    expect(screen.getByText(/Convers/)).toBeTruthy()
    // Entrevista 5 / topo 12 = 42% de retencao
    expect(screen.getByText(/42%/)).toBeTruthy()
  })

  it("i18n: zero MISSING_MESSAGE no funnel", () => {
    const { errors } = renderWith([FUNNEL], "sidebar")
    expect(errors.filter((e) => e.includes("MISSING_MESSAGE"))).toEqual([])
  })

  it("localiza codigo de etapa canonico (interview_manager -> label PT)", () => {
    const coded: ResponseBlock = {
      ...FUNNEL,
      stages: [{ label: "interview_manager", count: 7 }],
    }
    renderWith([coded], "fullscreen")
    expect(screen.getByText("Entrevista com Gestor")).toBeTruthy()
    expect(screen.queryByText("interview_manager")).toBeNull()
  })
})


const CANDIDATE_CARD: ResponseBlock = {
  kind: "candidate_card",
  block_id: "candidate_card:abc",
  role: "answer",
  layout: "inline",
  state: "ready",
  candidate_id: "abc",
  name: "Felipe Almeida",
  title: "CFO",
  seniority: "Pleno",
  location: "São Paulo/SP",
  experience_years: 6,
  top_skills: ["Oracle", "Power BI", "SAP FI"],
  score: 92,
  score_label: "Score LIA",
  recommendation: "Altamente Recomendado",
  summary: "Forte em financeiro.",
  unverified: false,
}

describe("ResponseBlockRenderer — candidate_card (Fase 1)", () => {
  it("renderiza nome, meta, skills, score e recomendacao", () => {
    renderWith([CANDIDATE_CARD], "fullscreen")
    expect(screen.getByText("Felipe Almeida")).toBeTruthy()
    expect(screen.getByText("Oracle")).toBeTruthy()
    expect(screen.getByText(/92%/)).toBeTruthy()
    expect(screen.getByText("Altamente Recomendado")).toBeTruthy()
  })

  it("sem parecer: mostra nota de nao-verificado e sem score", () => {
    const unv: ResponseBlock = {
      ...CANDIDATE_CARD,
      score: null,
      score_label: null,
      recommendation: null,
      summary: null,
      unverified: true,
    }
    renderWith([unv], "sidebar")
    expect(screen.getByText("Felipe Almeida")).toBeTruthy()
    expect(screen.queryByText(/92%/)).toBeNull()
    expect(screen.getByText("Sem parecer LIA ainda")).toBeTruthy()
  })

  it("i18n: zero MISSING_MESSAGE no candidate_card", () => {
    const { errors } = renderWith([CANDIDATE_CARD], "floating")
    expect(errors.filter((e) => e.includes("MISSING_MESSAGE"))).toEqual([])
  })
})


describe("ResponseBlockRenderer — expand chevron (AD8 suggest_chat_mode)", () => {
  it("bloco wide em sidebar mostra CTA e dispara lia:request-chat-mode", () => {
    const events: (string | undefined)[] = []
    const handler = (e: Event) =>
      events.push((e as CustomEvent).detail?.mode as string | undefined)
    window.addEventListener("lia:request-chat-mode", handler)
    renderWith([TABLE], "sidebar")
    const btn = screen.getByText(/Expandir em tela cheia/)
    expect(btn).toBeTruthy()
    fireEvent.click(btn)
    window.removeEventListener("lia:request-chat-mode", handler)
    expect(events).toContain("fullscreen")
  })

  it("bloco wide em fullscreen NAO mostra CTA", () => {
    renderWith([TABLE], "fullscreen")
    expect(screen.queryByText(/Expandir em tela cheia/)).toBeNull()
  })

  it("bloco inline (candidate_card) em sidebar NAO mostra CTA", () => {
    renderWith([CANDIDATE_CARD], "sidebar")
    expect(screen.queryByText(/Expandir em tela cheia/)).toBeNull()
  })
})


const SCORE_EXPLAINER: ResponseBlock = {
  kind: "score_explainer",
  block_id: "score_explainer:rank:1",
  role: "support",
  layout: "inline",
  state: "ready",
  subject_id: "1",
  subject_label: "Ana",
  score: 92,
  score_label: "Score LIA",
  confidence: "high",
  confidence_basis: "Parecer LIA consolidado",
  factors: [
    {
      label: "Experiencia solida",
      weight: 0.4,
      contribution: "+",
      detail: "8 anos",
      evidence_refs: [],
    },
    { label: "Gap de ingles", weight: 0.2, contribution: "-", evidence_refs: [] },
  ],
  summary: "",
  unverified: false,
}

describe("ResponseBlockRenderer — score_explainer (Fase 2: factor bars)", () => {
  it("colapsado mostra subject + por que; expande mostra fatores com peso", () => {
    renderWith([SCORE_EXPLAINER], "fullscreen")
    expect(screen.getByText("Ana")).toBeTruthy()
    fireEvent.click(screen.getByText(/por qu/i))
    expect(screen.getByText("Experiencia solida")).toBeTruthy()
    // peso renderizado como %
    expect(screen.getByText("40%")).toBeTruthy()
  })

  it("score baixo nao usa vermelho (fairness) — tom neutro", () => {
    const low: ResponseBlock = { ...SCORE_EXPLAINER, score: 55 }
    const { container } = renderWith([low], "fullscreen")
    // nenhuma classe de erro/vermelho aplicada ao score
    expect(container.querySelector(".text-status-error")).toBeNull()
  })
})
