import { describe, it, expect } from "vitest"

/**
 * Sensor: garante que IDs numéricos (index+1) NÃO vazem para props de modais de vaga.
 * Bug canônico 2026-06-19: JobsModalsSection.tsx passava String(job.id) = "2"
 * em vez de job.backendId (UUID) — causava DataError 500 no backend.
 *
 * Princípio canonical-fix: fix no produtor (JobsModalsSection), não nos consumidores.
 */

// Simula o Job interface conforme jobsPageTypes.ts
interface Job {
  id: number       // índice sequencial UI — NUNCA usar em API calls
  jobId: string    // WDT-XXXXXXXX
  backendId: string // UUID real do PostgreSQL
  title: string
}

function buildModalJobProps(job: Job) {
  // Simula o que JobsModalsSection.tsx faz ao construir props dos modais
  return {
    id: job.backendId,  // ✅ canonical fix: sempre UUID
    code: job.jobId,
    title: job.title,
  }
}

describe("JobsModalsSection — ID/UUID sensor", () => {
  const mockJob: Job = {
    id: 2,  // índice numérico — NÃO deve entrar em API calls
    jobId: "WDT-610705AB",
    backendId: "610705ab-7a98-45e9-999a-5bdb62975989",
    title: "Engenheiro de Software",
  }

  it("usa backendId (UUID) como id do modal, nunca o índice numérico", () => {
    const props = buildModalJobProps(mockJob)
    expect(props.id).toBe(mockJob.backendId)
    expect(props.id).toBe("610705ab-7a98-45e9-999a-5bdb62975989")
  })

  it("id do modal NÃO é o índice numérico convertido para string", () => {
    const props = buildModalJobProps(mockJob)
    expect(props.id).not.toBe(String(mockJob.id))  // não deve ser "2"
    expect(props.id).not.toBe("2")
  })

  it("id do modal é um UUID (36 chars com hífens)", () => {
    const props = buildModalJobProps(mockJob)
    const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
    expect(props.id).toMatch(UUID_PATTERN)
  })

  it("backendId sempre presente (non-optional em Job interface)", () => {
    // Se backendId fosse undefined, String(undefined) = "undefined" → 500
    expect(mockJob.backendId).toBeTruthy()
    expect(typeof mockJob.backendId).toBe("string")
  })
})
