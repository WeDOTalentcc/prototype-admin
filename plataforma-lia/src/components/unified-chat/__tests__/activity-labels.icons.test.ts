import { describe, it, expect } from "vitest"
import {
  Brain,
  ListChecks,
  Microscope,
  Eye,
  Search,
  PenLine,
  PanelRight,
  PauseCircle,
  PlayCircle,
  ArrowRightLeft,
  Workflow,
  User,
  List,
  Wrench,
} from "lucide-react"
import { phaseIcon, toolIcon } from "../activity-labels"

// Enriquecimento 2026-06-07 (estilo Replit): variedade de icones de
// reasoning/activity. FE puro -> vale federado E supervisor.

describe("phaseIcon — heuristica de raciocinio (variedade vs Brain p/ tudo)", () => {
  it("planejamento -> ListChecks", () => {
    expect(phaseIcon("Planejando a resposta")).toBe(ListChecks)
  })
  it("analise -> Microscope", () => {
    expect(phaseIcon("Analisando candidatos")).toBe(Microscope)
  })
  it("revisao -> Eye", () => {
    expect(phaseIcon("Revisando o pipeline")).toBe(Eye)
  })
  it("busca -> Search", () => {
    expect(phaseIcon("Buscando vagas ativas")).toBe(Search)
  })
  it("preparar resposta -> PenLine", () => {
    expect(phaseIcon("Preparando a resposta")).toBe(PenLine)
  })
  it("texto sem match -> Brain (fallback)", () => {
    expect(phaseIcon("xyz aleatorio sem padrao")).toBe(Brain)
  })
})

describe("toolIcon — tools enriquecidas (antes caiam no Wrench/generico)", () => {
  it("open_ui -> PanelRight", () => expect(toolIcon("open_ui")).toBe(PanelRight))
  it("pause_job -> PauseCircle", () => expect(toolIcon("pause_job")).toBe(PauseCircle))
  it("reopen_job -> PlayCircle", () => expect(toolIcon("reopen_job")).toBe(PlayCircle))
  it("batch_move_candidates -> ArrowRightLeft", () =>
    expect(toolIcon("batch_move_candidates")).toBe(ArrowRightLeft))
  it("get_pipeline_summary -> Workflow", () =>
    expect(toolIcon("get_pipeline_summary")).toBe(Workflow))
  it("view_candidate_profile -> User", () =>
    expect(toolIcon("view_candidate_profile")).toBe(User))
  it("list_jobs -> List (inalterado)", () => expect(toolIcon("list_jobs")).toBe(List))
  it("tool desconhecida -> Wrench (fallback)", () =>
    expect(toolIcon("zzz_tool_inexistente")).toBe(Wrench))
})
