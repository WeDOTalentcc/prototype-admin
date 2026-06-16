export interface FormatRelativeTimeOptions {
  includeTime?: boolean
}

/**
 * Formata uma data como dd/mm/aaaa (pt-BR) de forma resiliente.
 *
 * NUNCA retorna a string "Invalid Date". `new Date(x).toLocaleDateString()`
 * devolve a string literal "Invalid Date" (sem lançar exceção) quando `x` é
 * nulo/vazio/malformado — por isso o guard explícito com `isNaN(getTime())`.
 * Entradas inválidas resultam em string vazia, que o chamador deve tratar
 * (ex.: esconder a linha de data em vez de imprimir "em ").
 */
export function formatDate(
  value: string | number | Date | null | undefined,
  opts?: Intl.DateTimeFormatOptions
): string {
  if (value == null || value === '') return ''
  const date = value instanceof Date ? value : new Date(value)
  if (isNaN(date.getTime())) return ''
  return date.toLocaleDateString(
    'pt-BR',
    opts ?? { day: '2-digit', month: '2-digit', year: 'numeric' }
  )
}

export function formatRelativeTime(
  dateStr: string | null | undefined,
  options?: FormatRelativeTimeOptions
): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  if (isNaN(date.getTime())) return ''
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffMins < 1) return 'Agora'
  if (diffMins < 60) return `Há ${diffMins} min`
  if (diffHours < 24) return `Há ${diffHours}h`
  if (diffDays === 1) return 'Ontem'
  if (diffDays < 7) return `Há ${diffDays} dias`

  const formatOptions: Intl.DateTimeFormatOptions = {
    day: '2-digit',
    month: 'short',
    ...(options?.includeTime && { hour: '2-digit', minute: '2-digit' }),
  }
  return date.toLocaleDateString('pt-BR', formatOptions)
}

export function formatFileSize(bytes: number): string {
  if (!bytes || !Number.isFinite(bytes)) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}
