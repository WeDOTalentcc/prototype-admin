/**
 * Testes unitários — useActionIntent + actionTypeToDomain (Phase 4c)
 *
 * Camada 2 — Unitária (jsdom)
 * Cobre: wizard keywords, wsi keywords, threshold 0.70, domain mapping,
 *        edge cases (vazio, irrelevante, ambíguo).
 */

import { renderHook } from "@testing-library/react"
import { useActionIntent, actionTypeToDomain } from "../shared/use-action-intent"

describe("useActionIntent — detect()", () => {
  const setup = () => renderHook(() => useActionIntent()).result.current

  it("retorna null para mensagem vazia", () => {
    const { detect } = setup()
    const r = detect("")
    expect(r.actionType).toBeNull()
    expect(r.confidence).toBe(0)
    expect(r.label).toBeNull()
  })

  it("retorna null para mensagem só de espaços", () => {
    const { detect } = setup()
    expect(detect("   ").actionType).toBeNull()
  })

  it("detecta wizard para 'criar vaga'", () => {
    const { detect } = setup()
    const r = detect("quero criar vaga para engenheiro")
    expect(r.actionType).toBe("wizard")
    expect(r.confidence).toBeGreaterThanOrEqual(0.70)
    expect(r.label).toContain("Vaga")
  })

  it("detecta wizard para 'nova vaga'", () => {
    const { detect } = setup()
    expect(detect("preciso abrir nova vaga urgente").actionType).toBe("wizard")
  })

  it("detecta wizard para 'headcount'", () => {
    const { detect } = setup()
    expect(detect("novo headcount aprovado").actionType).toBe("wizard")
  })

  it("detecta wizard para 'preciso contratar'", () => {
    const { detect } = setup()
    expect(detect("preciso contratar um dev").actionType).toBe("wizard")
  })

  it("detecta wsi para 'entrevista'", () => {
    const { detect } = setup()
    const r = detect("iniciar entrevista com o candidato")
    expect(r.actionType).toBe("wsi")
    expect(r.confidence).toBeGreaterThanOrEqual(0.70)
    expect(r.label).toContain("WSI")
  })

  it("detecta wsi para 'avaliar candidato'", () => {
    const { detect } = setup()
    expect(detect("quero avaliar candidato agora").actionType).toBe("wsi")
  })

  it("detecta wsi para 'wsi' literal", () => {
    const { detect } = setup()
    expect(detect("rodar wsi para o João").actionType).toBe("wsi")
  })

  it("retorna null para mensagem irrelevante", () => {
    const { detect } = setup()
    expect(detect("olá, tudo bem?").actionType).toBeNull()
  })

  it("retorna null para perguntas gerais sobre candidatos", () => {
    const { detect } = setup()
    expect(detect("quantos candidatos temos no funil?").actionType).toBeNull()
  })

  it("confidence é bounded entre 0 e 1", () => {
    const { detect } = setup()
    const r = detect("criar vaga headcount abrir vaga nova posição")
    expect(r.confidence).toBeGreaterThanOrEqual(0)
    expect(r.confidence).toBeLessThanOrEqual(1)
  })

  it("wsi tem prioridade sobre wizard em mensagem ambígua", () => {
    const { detect } = setup()
    // Ambas as keywords presentes; wsi deve vencer
    const r = detect("criar vaga e entrevistar candidato")
    expect(r.actionType).toBe("wsi")
  })

  it("case insensitive — CRIAR VAGA", () => {
    const { detect } = setup()
    expect(detect("CRIAR VAGA urgente").actionType).toBe("wizard")
  })

  // ─── Phase 5 — Analytics ──────────────────────────────────────────────────

  it("detecta analytics para 'relatório'", () => {
    const { detect } = setup()
    expect(detect("gerar relatório de vagas").actionType).toBe("analytics")
  })

  it("detecta analytics para 'kpi'", () => {
    const { detect } = setup()
    expect(detect("quais os kpis do processo seletivo?").actionType).toBe("analytics")
  })

  it("detecta analytics para 'métricas'", () => {
    const { detect } = setup()
    expect(detect("ver métricas de contratação").actionType).toBe("analytics")
  })

  it("detecta analytics para 'indicadores'", () => {
    const { detect } = setup()
    expect(detect("mostrar indicadores do funil").actionType).toBe("analytics")
  })

  // ─── Phase 5 — Communication ──────────────────────────────────────────────

  it("detecta communication para 'enviar email'", () => {
    const { detect } = setup()
    expect(detect("enviar email para o candidato").actionType).toBe("communication")
  })

  it("detecta communication para 'notificar candidato'", () => {
    const { detect } = setup()
    // "mensagem para candidato" — sem keywords de WSI (sem "entrevista")
    expect(detect("enviar mensagem para candidato aprovado").actionType).toBe("communication")
  })

  it("detecta communication para 'feedback ao candidato'", () => {
    const { detect } = setup()
    expect(detect("enviar feedback ao candidato reprovado").actionType).toBe("communication")
  })

  // ─── Phase 5 — ATS Integration ────────────────────────────────────────────

  it("detecta ats_integration para 'sincronizar gupy'", () => {
    const { detect } = setup()
    expect(detect("sincronizar gupy agora").actionType).toBe("ats_integration")
  })

  it("detecta ats_integration para 'importar candidatos'", () => {
    const { detect } = setup()
    expect(detect("importar candidatos do ats").actionType).toBe("ats_integration")
  })

  it("detecta ats_integration para 'pandapé'", () => {
    const { detect } = setup()
    expect(detect("atualizar pandapé com os candidatos").actionType).toBe("ats_integration")
  })
})

describe("actionTypeToDomain()", () => {
  it("'wizard' → 'wizard'", () => {
    expect(actionTypeToDomain("wizard")).toBe("wizard")
  })

  it("'wsi' → 'talent'", () => {
    expect(actionTypeToDomain("wsi")).toBe("talent")
  })

  it("'analytics' → 'analytics'", () => {
    expect(actionTypeToDomain("analytics")).toBe("analytics")
  })

  it("'communication' → 'communication'", () => {
    expect(actionTypeToDomain("communication")).toBe("communication")
  })

  it("'ats_integration' → 'ats_integration'", () => {
    expect(actionTypeToDomain("ats_integration")).toBe("ats_integration")
  })

  it("null → 'general'", () => {
    expect(actionTypeToDomain(null)).toBe("general")
  })
})
