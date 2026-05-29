/**
 * Task #1196 — Helper canônico de formatação de localização de vaga.
 *
 * O campo `location` vindo do backend pode chegar como:
 *   - string simples já legível (ex.: "São Paulo, SP")
 *   - string contendo JSON de endereço (ex.: '{"city": null, "state": null, "country": "Brasil"}')
 *   - objeto já parseado ({ city, state, country })
 *
 * Esta função normaliza qualquer um desses formatos para um texto limpo,
 * unindo apenas os campos não-nulos/não-vazios por vírgula, e retornando
 * `undefined` quando não há nada útil para exibir.
 *
 * É defensiva contra JSON malformado: faz try/parse e, em caso de falha,
 * cai de volta para a string original.
 */

type LocationObject = {
  city?: unknown
  state?: unknown
  country?: unknown
  [extra: string]: unknown
}

export type JobLocationInput = string | LocationObject | null | undefined

function cleanPart(value: unknown): string | undefined {
  if (typeof value !== "string") return undefined
  const trimmed = value.trim()
  return trimmed.length > 0 ? trimmed : undefined
}

function formatLocationObject(obj: LocationObject): string | undefined {
  const parts = [cleanPart(obj.city), cleanPart(obj.state), cleanPart(obj.country)].filter(
    (p): p is string => Boolean(p),
  )
  return parts.length > 0 ? parts.join(", ") : undefined
}

export function formatJobLocation(location: JobLocationInput): string | undefined {
  if (location === null || location === undefined) return undefined

  if (typeof location === "object") {
    return formatLocationObject(location)
  }

  if (typeof location === "string") {
    const trimmed = location.trim()
    if (trimmed.length === 0) return undefined

    const looksLikeJson = trimmed.startsWith("{") && trimmed.endsWith("}")
    if (looksLikeJson) {
      try {
        const parsed = JSON.parse(trimmed) as unknown
        if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
          return formatLocationObject(parsed as LocationObject)
        }
      } catch {
        // JSON malformado — cai de volta para a string original.
      }
    }

    return trimmed
  }

  return undefined
}
