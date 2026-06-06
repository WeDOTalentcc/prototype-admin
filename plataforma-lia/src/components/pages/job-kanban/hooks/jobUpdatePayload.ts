/**
 * Onda 1 / O1.4 — canonical serializer for the job vacancy edit save.
 *
 * Single producer that maps the FE form (job-edit-tab) to the FastAPI
 * `JobVacancyUpdate` contract (extra='forbid'). It:
 *   1. maps camelCase form keys → snake_case schema keys,
 *   2. coerces RemoteCombobox objects {id,name} to the scalar the schema expects,
 *   3. drops any key the backend schema does NOT accept (avoids HTTP 422).
 *
 * Mirror of app/api/v1/job_vacancies/_shared.py::JobVacancyUpdate. If a field is
 * added to that schema, add it here too (and vice-versa). See CLAUDE.md harness note.
 */

// camelCase (form) -> snake_case (schema)
const FIELD_MAP: Record<string, string> = {
  title: "title",
  department: "department",
  location: "location",
  workModel: "work_model",
  type: "employment_type",
  seniority: "seniority_level",
  level: "seniority_level",
  status: "status",
  urgencyLevel: "urgency_level",
  recruiter: "recruiter",
  recruiterEmail: "recruiter_email",
  manager: "manager",
  managerEmail: "manager_email",
  openDate: "open_date",
  deadline: "deadline",
  deadlineScreening: "deadline_screening",
  deadlineShortlist: "deadline_shortlist",
  deadlineClosing: "deadline_closing",
  benefits: "benefits",
  languages: "languages",
  visibility: "visibility",
  accessList: "access_list",
  access_list: "access_list",
  isConfidential: "is_confidential",
  maskedCompanyName: "masked_company_name",
  isAffirmative: "is_affirmative",
  affirmativeCriteriaPrimary: "affirmative_criteria_primary",
  affirmativeCriteriaSecondary: "affirmative_criteria_secondary",
  affirmativeDescription: "affirmative_description",
  affirmativeDocumentRequired: "affirmative_document_required",
  affirmativeDocumentTypes: "affirmative_document_types",
  priority: "priority",
  description: "description",
  interviewStages: "interview_stages",
  variableCompensation: "variable_compensation",
}

// Snake_case keys accepted by JobVacancyUpdate (extra='forbid'). Anything not here
// is dropped before the request so the save is never rejected for a phantom key.
// NOTE: target_sector/segment/audience (Mercado-Alvo) and published_* are intentionally
// absent — Mercado-Alvo will be removed (Onda 2); publication channels are not yet a
// real persistable contract. `city` is absent until the global cities dataset (Onda 2).
const ALLOWED_KEYS = new Set<string>([
  "title", "department", "location", "work_model", "employment_type",
  "seniority_level", "description", "responsibilities", "requirements",
  "technical_requirements", "languages", "behavioral_competencies", "salary",
  "salary_range", "bonus_range", "benefits", "variable_compensation", "manager",
  "manager_email", "recruiter", "recruiter_email", "is_confidential", "visibility",
  "access_list", "masked_company_name", "exclude_from_sync", "status", "stage",
  "source", "wizard_stage", "priority", "screening_questions", "interview_stages",
  "eligibility_questions", "disabled_eligibility_question_ids", "confidentiality_config",
  "is_affirmative", "affirmative_criteria_primary", "affirmative_criteria_secondary",
  "affirmative_description", "affirmative_document_required", "affirmative_document_types",
  "enriched_jd", "urgency_level", "open_date", "deadline", "deadline_screening",
  "deadline_shortlist", "deadline_closing",
])

// Keys whose form value may be a RemoteCombobox object {id,name} and the schema wants a string.
const SCALAR_NAME_KEYS = new Set<string>([
  "department", "priority", "employment_type", "work_model", "seniority_level", "status",
])

function isOption(v: unknown): v is { id?: unknown; name?: unknown } {
  return !!v && typeof v === "object" && ("name" in (v as object) || "id" in (v as object))
}

function toScalarName(v: unknown): unknown {
  if (isOption(v)) return (v as { name?: unknown; id?: unknown }).name ?? (v as { id?: unknown }).id ?? null
  return v
}

function toNumber(v: unknown): number | null {
  if (v === null || v === undefined || v === "") return null
  if (isOption(v)) {
    const raw = (v as { id?: unknown; name?: unknown }).id ?? (v as { name?: unknown }).name
    const n = Number(raw)
    return Number.isFinite(n) ? n : null
  }
  const n = Number(v)
  return Number.isFinite(n) ? n : null
}

/**
 * Build the JobVacancyUpdate payload from the requested section `fields` and the form.
 */
export function buildJobUpdatePayload(
  fields: string[],
  form: Record<string, unknown>,
): Record<string, unknown> {
  const updates: Record<string, unknown> = {}

  for (const f of fields) {
    if (f === "salaryMin" || f === "salaryMax") {
      if (!updates["salary_range"]) {
        updates["salary_range"] = {
          min: form.salaryMin ? Number(form.salaryMin) : null,
          max: form.salaryMax ? Number(form.salaryMax) : null,
          currency: "BRL",
        }
      }
      continue
    }
    if (f === "bonusMin" || f === "bonusMax") {
      if (!updates["bonus_range"]) {
        updates["bonus_range"] = {
          min: form.bonusMin ? Number(form.bonusMin) : null,
          max: form.bonusMax ? Number(form.bonusMax) : null,
          currency: "BRL",
        }
      }
      continue
    }

    const key = FIELD_MAP[f] || f
    if (!ALLOWED_KEYS.has(key)) continue // drop phantom/forbidden keys

    let value = form[f]
    if (key === "urgency_level") {
      value = toNumber(value)
    } else if (SCALAR_NAME_KEYS.has(key)) {
      value = toScalarName(value)
    }
    updates[key] = value
  }

  return updates
}
