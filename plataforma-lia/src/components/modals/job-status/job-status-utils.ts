// Utility functions extracted from job-status-modal.tsx

export function formatPausedDuration(pausedSince?: string): string {
  if (!pausedSince) return "—"
  const pausedDate = new Date(pausedSince)
  const now = new Date()
  const diffMs = now.getTime() - pausedDate.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return "Hoje"
  if (diffDays === 1) return "1 dia"
  if (diffDays < 7) return `${diffDays} dias`
  if (diffDays < 30) return `${Math.ceil(diffDays / 7)} semanas`
  return `${Math.ceil(diffDays / 30)} meses`
}

export function replaceTemplateVariables(content: string, jobTitle: string): string {
  return content
    .replace(/\{\{job_title\}\}/g, jobTitle)
    .replace(/\{\{vaga\}\}/g, jobTitle)
    .replace(/\{\{company_name\}\}/g, "WeDO Talent")
    .replace(/\{\{empresa\}\}/g, "WeDO Talent")
}
