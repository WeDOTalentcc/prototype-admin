import { describe, it, expect, beforeAll, afterAll, vi } from "vitest"
import { jobToKanbanItem } from "../jobs-to-kanban"
import type { Job } from "@/components/jobs"

const labels = {
  deadlineSoon: (d: number) => `Vence em ${d}d`,
  deadlinePast: (d: number) => `Atrasada ${d}d`,
  candidatesCount: (c: number) => `${c} candidatos`,
  ageDays: (d: number) => `Aberta há ${d}d`,
  ribbon: {
    label: () => "Ação Necessária",
    deadlineOverdue: (d: number) => `Deadline vencido há ${d}d`,
    deadlineSoon: (d: number) => `Deadline em ${d}d`,
    urgent: () => "Vaga marcada como urgente",
    pendingApproval: () => "Aguardando aprovação",
    noCandidates: () => "Sem candidatos no funil",
  },
}

function baseJob(overrides: Partial<Job> = {}): Job {
  return {
    id: 1,
    jobId: "JOB-1",
    backendId: "uuid-1",
    title: "Engenheiro de Software",
    department: "Tecnologia",
    location: "São Paulo, BR",
    workModel: "remoto",
    type: "CLT",
    seniority: "Pleno",
    salary: "R$ 12k",
    benefits: [],
    status: "Ativa",
    stage: "Triagem",
    openDate: new Date(Date.now() - 30 * 86400000).toISOString(),
    description: "",
    requirements: [],
    manager: "Ana Souza",
    managerEmail: "ana@x.com",
    recruiter: "Bruno Lima",
    recruiterEmail: "bruno@x.com",
    priority: "média",
    funnel: { total: 10, screening: 5, interview: 3, final: 1, hired: 1 },
    publishedLinkedIn: false,
    publishedWebsite: false,
    isConfidential: false,
    nps: 0,
    nextActions: [],
    urgencyLevel: 2,
    approvalStatus: "aprovada",
    ...overrides,
  } as Job
}

describe("jobToKanbanItem (Task #562)", () => {
  beforeAll(() => {
    // Fixa o relógio para tornar `daysSince`/`daysBetween` determinísticos.
    vi.useFakeTimers()
    vi.setSystemTime(new Date("2026-04-19T12:00:00Z"))
  })
  afterAll(() => {
    vi.useRealTimers()
  })

  it("popula funnel quando há candidatos e omite quando total=0 (canonical-fix: sem default silencioso)", () => {
    const withFunnel = jobToKanbanItem(baseJob(), { labels })
    expect(withFunnel.funnel).toEqual({ total: 10, screening: 5, interview: 3, final: 1, hired: 1 })

    const empty = jobToKanbanItem(
      baseJob({ funnel: { total: 0, screening: 0, interview: 0, final: 0, hired: 0 } }),
      { labels },
    )
    expect(empty.funnel).toBeUndefined()
  })

  it("popula owner com iniciais a partir de manager; omite quando manager é vazio", () => {
    const withOwner = jobToKanbanItem(baseJob(), { labels })
    expect(withOwner.owner).toEqual({ name: "Ana Souza", initials: "AS" })

    const noOwner = jobToKanbanItem(baseJob({ manager: "" }), { labels })
    expect(noOwner.owner).toBeUndefined()
  })

  it("calcula ageDays a partir de openDate; omite quando openDate ausente", () => {
    const withAge = jobToKanbanItem(baseJob(), { labels })
    expect(withAge.ageDays).toBe(30)

    const noAge = jobToKanbanItem(baseJob({ openDate: "" }), { labels })
    expect(noAge.ageDays).toBeUndefined()
  })

  it("dispara ribbon=danger com reason de deadline vencido", () => {
    const overdue = jobToKanbanItem(
      baseJob({ deadline: new Date(Date.now() - 5 * 86400000).toISOString() }),
      { labels },
    )
    expect(overdue.deadlineStatus).toBe("danger")
    expect(overdue.ribbon).toEqual({
      label: "Ação Necessária",
      variant: "danger",
      reason: "Deadline vencido há 5d",
    })
  })

  it("dispara ribbon=warning com reason de deadline próximo (≤ 7d)", () => {
    const soon = jobToKanbanItem(
      baseJob({ deadline: new Date(Date.now() + 3 * 86400000).toISOString() }),
      { labels },
    )
    expect(soon.ribbon).toEqual({
      label: "Ação Necessária",
      variant: "warning",
      reason: "Deadline em 3d",
    })
  })

  it("dispara ribbon=warning com reason de urgência quando urgencyLevel >= 4 e sem deadline próximo", () => {
    const urgent = jobToKanbanItem(
      baseJob({ urgencyLevel: 5, deadline: new Date(Date.now() + 30 * 86400000).toISOString() }),
      { labels },
    )
    expect(urgent.ribbon).toEqual({
      label: "Ação Necessária",
      variant: "warning",
      reason: "Vaga marcada como urgente",
    })
  })

  it("dispara ribbon=info quando vaga está aguardando aprovação", () => {
    const pending = jobToKanbanItem(
      baseJob({ status: "Aguardando aprovação", urgencyLevel: 1, priority: "média" }),
      { labels },
    )
    expect(pending.ribbon).toEqual({
      label: "Ação Necessária",
      variant: "info",
      reason: "Aguardando aprovação",
    })
  })

  it("dispara ribbon=info quando vaga está aberta há mais de 14d sem candidatos", () => {
    const stale = jobToKanbanItem(
      baseJob({
        openDate: new Date(Date.now() - 20 * 86400000).toISOString(),
        urgencyLevel: 1,
        priority: "média",
        funnel: { total: 0, screening: 0, interview: 0, final: 0, hired: 0 },
      }),
      { labels },
    )
    expect(stale.ribbon).toEqual({
      label: "Ação Necessária",
      variant: "info",
      reason: "Sem candidatos no funil",
    })
  })

  it("não emite ribbon quando labels.ribbon não é fornecido (caller controla)", () => {
    const labelsNoRibbon = { ...labels, ribbon: undefined }
    const item = jobToKanbanItem(
      baseJob({ urgencyLevel: 5 }),
      { labels: labelsNoRibbon },
    )
    expect(item.ribbon).toBeUndefined()
  })

  it("não emite ribbon para vaga 'saudável' (sem deadline próximo, urgência baixa, com candidatos)", () => {
    const healthy = jobToKanbanItem(
      baseJob({
        urgencyLevel: 2,
        priority: "média",
        deadline: new Date(Date.now() + 60 * 86400000).toISOString(),
      }),
      { labels },
    )
    expect(healthy.ribbon).toBeUndefined()
  })

  it("classifica deadlineStatus ≤ 7d como warning", () => {
    const soon = jobToKanbanItem(
      baseJob({ deadline: new Date(Date.now() + 3 * 86400000).toISOString() }),
      { labels },
    )
    expect(soon.deadlineStatus).toBe("warning")
    expect(soon.dateLabel).toBe("Vence em 3d")
  })
})
