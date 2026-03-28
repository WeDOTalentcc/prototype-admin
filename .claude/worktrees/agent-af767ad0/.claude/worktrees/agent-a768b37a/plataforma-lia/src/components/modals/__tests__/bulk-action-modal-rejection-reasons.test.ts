/**
 * Testes Unitários — BulkActionModal: rejectionReasonOptions
 * Camada 2 (Unitário FE — Vitest, sem DOM)
 *
 * Testa a lógica de derivação das opções de motivo de reprovação:
 * - DB-first: quando company pipeline tem sub_statuses no estágio 'rejected',
 *   os motivos vêm do DB
 * - Fallback: quando pipeline não tem sub_statuses, usa REJECTION_REASONS estático
 * - Mapping correto: { code, displayName } a partir dos sub_statuses do DB
 */
import { describe, it, expect } from "vitest"
import { REJECTION_REASONS } from "@/lib/recruitment-stages"

// A lógica de rejectionReasonOptions está no useMemo do BulkActionModal.
// Extraímos e testamos a função de derivação isoladamente.

interface SubStatus {
  name: string
  display_name: string
  is_default?: boolean
}

interface PipelineStage {
  name: string
  sub_statuses?: SubStatus[]
}

/** Replica o useMemo de BulkActionModal — fonte da verdade para este teste */
function deriveRejectionReasonOptions(
  companyPipelineStages: PipelineStage[]
): Array<{ code: string; displayName: string }> {
  const rejectedStage = companyPipelineStages.find(s => s.name === "rejected")
  if (rejectedStage?.sub_statuses?.length) {
    return rejectedStage.sub_statuses.map(ss => ({
      code: ss.name,
      displayName: ss.display_name,
    }))
  }
  return REJECTION_REASONS.map(r => ({ code: r.code, displayName: r.displayName }))
}

// ── Fixtures ─────────────────────────────────────────────────────────────────

const DB_REJECTED_SUB_STATUSES: SubStatus[] = [
  { name: "another_candidate_selected", display_name: "Outro Candidato Selecionado", is_default: true },
  { name: "cultural_mismatch",          display_name: "Não Aprovado Culturalmente" },
  { name: "under_qualified",            display_name: "Subqualificado" },
  { name: "org_restructuring",          display_name: "Reestruturação Organizacional" },
]

// ── Testes ────────────────────────────────────────────────────────────────────

describe("deriveRejectionReasonOptions — DB-first", () => {
  it("retorna sub-statuses do DB quando estágio rejected tem sub_statuses", () => {
    const pipeline: PipelineStage[] = [
      { name: "screening", sub_statuses: [] },
      { name: "rejected", sub_statuses: DB_REJECTED_SUB_STATUSES },
    ]
    const result = deriveRejectionReasonOptions(pipeline)
    expect(result).toHaveLength(DB_REJECTED_SUB_STATUSES.length)
    expect(result[0].code).toBe("another_candidate_selected")
    expect(result[0].displayName).toBe("Outro Candidato Selecionado")
  })

  it("mapeia corretamente: ss.name → code, ss.display_name → displayName", () => {
    const pipeline: PipelineStage[] = [
      {
        name: "rejected",
        sub_statuses: [
          { name: "visa_required", display_name: "Necessita Visto/Patrocínio" },
        ],
      },
    ]
    const result = deriveRejectionReasonOptions(pipeline)
    expect(result[0].code).toBe("visa_required")
    expect(result[0].displayName).toBe("Necessita Visto/Patrocínio")
  })

  it("DB tem prioridade mesmo quando REJECTION_REASONS seria diferente", () => {
    const pipeline: PipelineStage[] = [
      {
        name: "rejected",
        sub_statuses: [
          { name: "custom_reason", display_name: "Motivo Customizado da Empresa" },
        ],
      },
    ]
    const result = deriveRejectionReasonOptions(pipeline)
    expect(result).toHaveLength(1)
    expect(result[0].code).toBe("custom_reason")
  })
})

describe("deriveRejectionReasonOptions — Fallback estático", () => {
  it("usa REJECTION_REASONS quando pipeline está vazio", () => {
    const result = deriveRejectionReasonOptions([])
    expect(result.length).toBe(REJECTION_REASONS.length)
    expect(result[0].code).toBe(REJECTION_REASONS[0].code)
    expect(result[0].displayName).toBe(REJECTION_REASONS[0].displayName)
  })

  it("usa REJECTION_REASONS quando estágio rejected não está no pipeline", () => {
    const pipeline: PipelineStage[] = [
      { name: "screening", sub_statuses: [{ name: "cv_received", display_name: "CV Recebido" }] },
    ]
    const result = deriveRejectionReasonOptions(pipeline)
    expect(result.length).toBe(REJECTION_REASONS.length)
  })

  it("usa REJECTION_REASONS quando rejected tem sub_statuses array vazio", () => {
    const pipeline: PipelineStage[] = [
      { name: "rejected", sub_statuses: [] },
    ]
    const result = deriveRejectionReasonOptions(pipeline)
    expect(result.length).toBe(REJECTION_REASONS.length)
  })

  it("usa REJECTION_REASONS quando rejected.sub_statuses é undefined", () => {
    const pipeline: PipelineStage[] = [
      { name: "rejected" }, // sem sub_statuses
    ]
    const result = deriveRejectionReasonOptions(pipeline)
    expect(result.length).toBe(REJECTION_REASONS.length)
  })
})

describe("REJECTION_REASONS canônico — integridade do fallback", () => {
  it("fallback tem pelo menos 30 motivos", () => {
    expect(REJECTION_REASONS.length).toBeGreaterThanOrEqual(30)
  })

  it("fallback contém 'another_candidate_selected'", () => {
    const codes = REJECTION_REASONS.map(r => r.code)
    expect(codes).toContain("another_candidate_selected")
  })

  it("todos os itens do fallback têm code e displayName não-vazios", () => {
    for (const reason of REJECTION_REASONS) {
      expect(reason.code).toBeTruthy()
      expect(reason.displayName).toBeTruthy()
    }
  })
})
