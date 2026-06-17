"use client"

import type { JobDataSnapshot } from "@/types/offer"

interface JobDataPanelProps {
  job: JobDataSnapshot
}

export function JobDataPanel({ job }: JobDataPanelProps) {
  const range = job.salary_range
  const salaryText = range?.min && range?.max
    ? `${range.currency ?? "R$"} ${Number(range.min).toLocaleString("pt-BR")} – ${Number(range.max).toLocaleString("pt-BR")}`
    : null

  return (
    <div className="flex flex-col gap-4 p-4 bg-muted/30 rounded-lg h-full">
      <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        Dados da Vaga
      </p>

      <div className="flex flex-col gap-3 text-sm">
        {job.title && (
          <Row label="Cargo" value={job.title} />
        )}
        {job.department && (
          <Row label="Departamento" value={job.department} />
        )}
        {job.contract_type && (
          <Row label="Contrato" value={job.contract_type} />
        )}
        {job.work_model && (
          <Row label="Modelo" value={job.work_model} />
        )}
        {salaryText && (
          <Row label="Faixa salarial" value={salaryText} highlight />
        )}
        {job.manager && (
          <Row label="Gestor" value={job.manager} />
        )}
        {job.benefits && job.benefits.length > 0 && (
          <div>
            <p className="text-xs text-muted-foreground mb-1">Benefícios</p>
            <ul className="flex flex-wrap gap-1">
              {job.benefits.slice(0, 8).map((b, i) => (
                <li
                  key={i}
                  className="text-micro bg-background border border-border rounded px-2 py-0.5"
                >
                  {typeof b === "string" ? b : b.name}
                </li>
              ))}
              {job.benefits.length > 8 && (
                <li className="text-xs text-muted-foreground px-1">
                  +{job.benefits.length - 8} mais
                </li>
              )}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}

function Row({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={highlight ? "font-semibold text-foreground" : "text-foreground"}>
        {value}
      </p>
    </div>
  )
}
