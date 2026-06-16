// Onda 1 F5 (2026-05-27) — LGPD CSV export canonical.
//
// Gera client-side CSV da trilha de raciocínio com os campos canonical:
//   step_index, step_type, label, data_fields_accessed, score, matched, timestamp.
//
// Defense-in-depth: campos LGPD-proibidos (cpf, raca, religiao, genero,
// estado_civil) NUNCA podem aparecer no CSV. Strip-only no consumer; o
// backend já garante invariante via sensor B5.2.
import type { AgentReasoningStep, ExecutionReasoningResponse } from "./types"

const LGPD_NEVER_ACCESSED = new Set([
  "cpf",
  "raca",
  "religiao",
  "genero",
  "estado_civil",
])

function csvEscape(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return ""
  const s = String(value)
  if (s.includes('"') || s.includes(",") || s.includes("\n") || s.includes("\r")) {
    return `"${s.replace(/"/g, '""')}"`
  }
  return s
}

function sanitizeFields(fields: string[]): string[] {
  return fields.filter((f) => !LGPD_NEVER_ACCESSED.has(f.toLowerCase()))
}

export interface LgpdCsvOptions {
  /** Override for tests — defaults to new Date(). */
  now?: () => Date
}

export function buildLgpdTrailCsv(
  reasoning: ExecutionReasoningResponse,
  _options: LgpdCsvOptions = {},
): string {
  const header = [
    "step_index",
    "step_type",
    "label",
    "data_fields_accessed",
    "score",
    "matched",
    "timestamp",
  ].join(",")

  const rows = reasoning.reasoning_trace.map((step: AgentReasoningStep, idx: number) => {
    const fields = sanitizeFields(step.data_fields_accessed || []).join(";")
    return [
      idx + 1,
      step.step_type,
      csvEscape(step.label),
      csvEscape(fields),
      step.score ?? "",
      step.matched === null || step.matched === undefined ? "" : step.matched ? "true" : "false",
      csvEscape(step.timestamp ?? ""),
    ].join(",")
  })

  // Trailer canonical com metadata da execução + lista de campos NUNCA acessados (LGPD).
  const trailer = [
    "",
    `# execution_id,${csvEscape(reasoning.execution_id)}`,
    `# agent_name,${csvEscape(reasoning.agent_name)}`,
    `# model_used,${csvEscape(reasoning.model_used)}`,
    `# data_fields_NOT_accessed,${csvEscape(
      reasoning.data_fields_NOT_accessed.join(";"),
    )}`,
  ].join("\n")

  return `${header}\n${rows.join("\n")}\n${trailer}\n`
}

export function downloadLgpdTrailCsv(
  reasoning: ExecutionReasoningResponse,
  options: LgpdCsvOptions = {},
): void {
  if (typeof window === "undefined") return
  const csv = buildLgpdTrailCsv(reasoning, options)
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  const now = options.now ? options.now() : new Date()
  const ymd = now.toISOString().slice(0, 10)
  a.download = `lgpd-trail-${reasoning.execution_id}-${ymd}.csv`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  // Defer revoke pra browsers que precisam do URL ativo durante o click.
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
