/**
 * Normaliza um item de `technicalRequirements` em string utilizável (audit P1-2).
 *
 * Problema histórico: a chamada `r.technology || r.skill || r || r.name` aparecia
 * em 3 arquivos diferentes (job-preview, screening-config, SCMSectionContent),
 * cada uma com ordem ligeiramente diferente. A cadeia silenciosa retornava o
 * objeto cru quando nenhuma chave existia — produzindo `[object Object]` no UI
 * em vez de erro explícito.
 *
 * Este helper centraliza a regra com prioridade DETERMINÍSTICA
 * (`technology` > `skill` > `name`), valida tipos, e loga warning quando o
 * shape é inválido para o item ser filtrado pelo chamador.
 *
 * Uso: `(reqs as unknown[]).map(normalizeTechnicalRequirement).filter(Boolean)`
 */
export function normalizeTechnicalRequirement(input: unknown): string | null {
  if (typeof input === 'string') {
    const trimmed = input.trim()
    return trimmed.length > 0 ? trimmed : null
  }

  if (input && typeof input === 'object') {
    const obj = input as Record<string, unknown>
    const candidates: Array<unknown> = [obj.technology, obj.skill, obj.name]
    for (const candidate of candidates) {
      if (typeof candidate === 'string') {
        const trimmed = candidate.trim()
        if (trimmed.length > 0) return trimmed
      }
    }
  }

  if (typeof console !== 'undefined' && process.env.NODE_ENV !== 'production') {
    // eslint-disable-next-line no-console
    console.warn(
      '[normalizeTechnicalRequirement] Item ignorado — shape inesperado:',
      input,
    )
  }
  return null
}
