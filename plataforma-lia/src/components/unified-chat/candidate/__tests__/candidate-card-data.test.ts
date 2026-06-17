import { describe, it, expect } from "vitest"
import {
  buildCandidateProfileCard,
  buildCandidateEvaluationCard,
  evaluationTierClasses,
} from "../candidate-card-data"

describe("buildCandidateProfileCard", () => {
  it("returns null when there is no name", () => {
    expect(buildCandidateProfileCard(null)).toBeNull()
    expect(buildCandidateProfileCard({})).toBeNull()
    expect(buildCandidateProfileCard({ role: "Dev" })).toBeNull()
  })

  it("normalizes a candidate record with mixed field names", () => {
    const data = buildCandidateProfileCard({
      id: "cand-1",
      name: "Ana Souza",
      current_role: "Engenheira de Software",
      current_company: "Acme",
      city: "São Paulo",
      avatar_url: "https://example.com/a.png",
      skills: ["React", "TypeScript", "Node"],
      wsi_score: 8.2,
    })
    expect(data).toEqual({
      candidateId: "cand-1",
      name: "Ana Souza",
      role: "Engenheira de Software",
      company: "Acme",
      location: "São Paulo",
      avatarUrl: "https://example.com/a.png",
      skills: ["React", "TypeScript", "Node"],
      matchScore: 8.2,
      matchClassification: null,
    })
  })

  it("drops empty/invalid skills and missing score", () => {
    const data = buildCandidateProfileCard({
      candidate_name: "Bruno",
      skills: ["Go", "", null, 42],
    })
    expect(data?.skills).toEqual(["Go"])
    expect(data?.matchScore).toBeNull()
  })
})

describe("buildCandidateEvaluationCard", () => {
  const baseSchema = {
    success: true,
    candidate_id: "cand-9",
    candidate_name: "Carla Dias",
    vacancy_id: "vac-3",
    job_title: "Tech Lead",
    rubric_score: 87.5,
    cv_fit: { cv_fit_score: 4.37, classification: "Alto" },
    recommendation: "Recomendado",
    recommendation_label: "Forte candidato",
    sub_status: "cv_approved",
    strengths: ["Liderança", "Arquitetura"],
    concerns: ["Pouca exp. mobile"],
    reasoning: "Bom histórico técnico.",
    evaluations: [
      {
        requirement: "Experiência em sistemas distribuídos",
        level: "Avançado",
        points: 90,
        weighted_points: 27,
        evidence: "Liderou migração para microserviços",
      },
      { requirement: "", level: "X" }, // dropped: no requirement
    ],
    evaluated_at: "2026-06-03T10:00:00",
    persisted: false,
    standalone: true,
  }

  it("returns null when there is neither name nor score", () => {
    expect(buildCandidateEvaluationCard(null)).toBeNull()
    expect(buildCandidateEvaluationCard({})).toBeNull()
  })

  it("normalizes the canonical screening schema", () => {
    const data = buildCandidateEvaluationCard(baseSchema)
    expect(data).not.toBeNull()
    expect(data?.candidateName).toBe("Carla Dias")
    expect(data?.jobTitle).toBe("Tech Lead")
    expect(data?.rubricScore).toBe(87.5)
    expect(data?.cvFitScore).toBe(4.37)
    expect(data?.cvFitClassification).toBe("Alto")
    expect(data?.recommendationLabel).toBe("Forte candidato")
    expect(data?.subStatus).toBe("cv_approved")
    expect(data?.strengths).toEqual(["Liderança", "Arquitetura"])
    expect(data?.concerns).toEqual(["Pouca exp. mobile"])
    expect(data?.persisted).toBe(false)
    expect(data?.standalone).toBe(true)
  })

  it("drops evaluations without a requirement and coerces numbers", () => {
    const data = buildCandidateEvaluationCard(baseSchema)
    expect(data?.evaluations).toHaveLength(1)
    expect(data?.evaluations[0]).toEqual({
      requirement: "Experiência em sistemas distribuídos",
      level: "Avançado",
      points: 90,
      weightedPoints: 27,
      evidence: "Liderou migração para microserviços",
    })
  })

  it("infers standalone from persisted when the flag is absent", () => {
    const data = buildCandidateEvaluationCard({
      candidate_name: "Diego",
      rubric_score: 70,
      persisted: true,
    })
    expect(data?.persisted).toBe(true)
    expect(data?.standalone).toBe(false)
  })
})

describe("evaluationTierClasses", () => {
  it("maps sub_status to the canonical status tokens", () => {
    expect(evaluationTierClasses({ subStatus: "cv_approved", rubricScore: 90 }).tier).toBe("success")
    expect(evaluationTierClasses({ subStatus: "cv_analyzing", rubricScore: 65 }).tier).toBe("warning")
    expect(evaluationTierClasses({ subStatus: "cv_rejected", rubricScore: 30 }).tier).toBe("error")
  })

  it("falls back to WSI visual thresholds when sub_status is missing", () => {
    // 80/10 = 8.0 → excelente → success
    expect(evaluationTierClasses({ subStatus: null, rubricScore: 80 }).tier).toBe("success")
    // 65/10 = 6.5 → medio → warning
    expect(evaluationTierClasses({ subStatus: null, rubricScore: 65 }).tier).toBe("warning")
    // 30/10 = 3.0 → regular → error
    expect(evaluationTierClasses({ subStatus: null, rubricScore: 30 }).tier).toBe("error")
  })

  it("includes DS status classes for the resolved tier", () => {
    const classes = evaluationTierClasses({ subStatus: "cv_approved", rubricScore: 90 })
    expect(classes.text).toContain("text-status-success")
    expect(classes.bg).toContain("bg-status-success")
    expect(classes.border).toContain("border-status-success")
  })
})
