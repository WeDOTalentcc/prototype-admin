/**
 * mapVacancyToJob — Phase I.2 helper.
 *
 * Converts the lightweight `JobLifecycleVacancy` shape returned by
 * `/api/v1/job-vacancies/lifecycle-overview` (rail data) plus the richer
 * lazy-fetched detail from `liaApi.getJobVacancy(id)` into the full `Job`
 * shape that `JobScreeningSection` (and other shared preview components)
 * expects.
 *
 * Why this helper exists:
 * - The rail returns ~15 fields per vacancy (summary).
 * - `JobScreeningSection` consumes ~50 fields from `Job`.
 * - We want to compose the rich section inside the lighter rail context
 *   without duplicating data structures or coupling the two pages.
 *
 * Defaults are conservative: missing fields default to undefined or empty
 * arrays so collapsible sections render their empty states cleanly.
 *
 * See `.planning/vacancy-pipeline-plan.md` Phase I.2.
 */
import type { Job, JobStatus, JobStage, JobApprovalStatus, JobWorkModel, JobPriority } from "@/components/jobs/jobsPageTypes"

interface JobLifecycleVacancy {
  id: string
  title: string
  department?: string | null
  location?: string | null
  work_model?: string | null
  seniority_level?: string | null
  status: string
  stage_entered_at?: string | null
  updated_at?: string | null
  created_at?: string | null
  manager?: string | null
  imported_from_ats: boolean
  source_system?: string | null
  ats_source_label?: string | null
  approval_status?: string | null
  candidate_count?: number
}

export interface VacancyDetailFromApi {
  description?: string | null
  enriched_jd?: unknown
  technical_requirements?: unknown[]
  benefits?: unknown[]
  salary_range?: { min?: number; max?: number; currency?: string } | null
  recruiter?: string | null
  manager_email?: string | null
  // Phase I.2 extensions — all optional, only consumed if present:
  job_code?: string | null
  recruiter_email?: string | null
  screening_questions?: unknown[]
  screening_config?: unknown
  screening_status?: string | null
  interview_stages?: unknown[]
  languages?: unknown[]
  behavioral_competencies?: unknown[]
  hiring_process?: string[]
  published_linkedin?: boolean
  published_website?: boolean
  published_indeed?: boolean
  approval_status?: string | null
  is_confidential?: boolean
  visibility?: string | null
  deadline?: string | null
  open_date?: string | null
  priority?: string | null
}

const _STATUS_FALLBACK: JobStatus = "Rascunho" as JobStatus
const _STAGE_FALLBACK: JobStage = "Triagem" as JobStage

function _normalizeStatus(s: string | null | undefined): JobStatus {
  return ((s ?? "Rascunho") as JobStatus)
}

function _normalizeWorkModel(m: string | null | undefined): JobWorkModel {
  const n = (m ?? "").toLowerCase()
  if (n === "remoto") return "remoto"
  if (n === "presencial") return "presencial"
  return "híbrido"
}

function _normalizeApproval(a: string | null | undefined): JobApprovalStatus {
  if (a === "aprovada" || a === "rejeitada") return a
  return "pendente"
}

/**
 * Convert (lifecycle vacancy + lazy detail) → Job.
 * Optional fields are passed through; undefined / nullish defaults to safe empty.
 */
export function mapVacancyToJob(
  vacancy: JobLifecycleVacancy,
  detail: VacancyDetailFromApi | null,
): Job {
  const d = detail ?? ({} as VacancyDetailFromApi)
  // Job.id is a `number` per jobsPageTypes; the backend uses UUIDs.
  // We keep the UUID string in `jobId`/`backendId` (type allows string)
  // and use a hash-like 0 as numeric id since the rail context never
  // joins on numeric id (only on jobId/backendId via API calls).
  return {
    id: 0,
    jobId: vacancy.id,
    backendId: vacancy.id,
    title: vacancy.title,
    department: vacancy.department ?? "",
    location: vacancy.location ?? "",
    workModel: _normalizeWorkModel(vacancy.work_model),
    type: "CLT",
    seniority: vacancy.seniority_level ?? undefined,
    salary: "",
    benefits: ((d.benefits || []) as unknown[]).map((b) =>
      typeof b === "string" ? b : ((b as { name?: string })?.name ?? ""),
    ).filter(Boolean) as string[],
    status: _normalizeStatus(vacancy.status),
    stage: _STAGE_FALLBACK,
    openDate: d.open_date ?? vacancy.created_at ?? "",
    deadline: d.deadline ?? undefined,
    description: typeof d.enriched_jd === "string"
      ? d.enriched_jd
      : (d.description ?? ""),
    requirements: ((d.technical_requirements || []) as unknown[]).map((r) =>
      typeof r === "string" ? r : ((r as { name?: string })?.name ?? String(r)),
    ).filter(Boolean) as string[],
    manager: vacancy.manager ?? "",
    managerEmail: d.manager_email ?? "",
    recruiter: d.recruiter ?? "",
    recruiterEmail: d.recruiter_email ?? "",
    priority: ((d.priority as JobPriority | null) ?? "Média") as JobPriority,
    funnel: {
      total: vacancy.candidate_count ?? 0,
      stages: {},
    } as unknown as Job["funnel"],
    publishedLinkedIn: !!d.published_linkedin,
    publishedWebsite: !!d.published_website,
    publishedIndeed: d.published_indeed,
    isConfidential: !!d.is_confidential,
    nps: 0,
    nextActions: [],
    urgencyLevel: 3,
    approvalStatus: _normalizeApproval(vacancy.approval_status ?? d.approval_status),
    hiringProcess: d.hiring_process ?? [],
    screeningQuestions: (d.screening_questions || []) as Job["screeningQuestions"],
    interviewStages: (d.interview_stages || []) as Job["interviewStages"],
    technicalRequirements: (d.technical_requirements || []) as Job["technicalRequirements"],
    languages: (d.languages || []) as Job["languages"],
    behavioralCompetencies: (d.behavioral_competencies || []) as Job["behavioralCompetencies"],
    salaryRange: d.salary_range ?? undefined,
    screeningConfig: (d.screening_config as Job["screeningConfig"]) ?? undefined,
    screeningStatus: (d.screening_status as Job["screeningStatus"]) ?? "not_configured",
    visibility: (d.visibility as Job["visibility"]) ?? undefined,
  } as Job
}
