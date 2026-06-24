export type ContactChannel = 'email' | 'whatsapp' | 'both'

export interface Contactable {
  id: string
  name: string
  email?: string
  phone?: string
}

export interface ContactPartition<T extends Contactable> {
  sendable: T[]
  skipped: Array<{ item: T; reason: string }>
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

/**
 * Pré-validação de contactabilidade. Puro — sem efeitos colaterais.
 * Separa candidatos em sendable (têm contato válido) e skipped (sem contato ou inválido).
 */
export function partitionByContactability<T extends Contactable>(
  candidates: T[],
  channel: ContactChannel
): ContactPartition<T> {
  const sendable: T[] = []
  const skipped: Array<{ item: T; reason: string }> = []

  for (const c of candidates) {
    const needsEmail = channel === 'email' || channel === 'both'
    const needsPhone = channel === 'whatsapp' || channel === 'both'

    if (needsEmail) {
      if (!c.email) { skipped.push({ item: c, reason: 'e-mail ausente' }); continue }
      if (!EMAIL_RE.test(c.email)) { skipped.push({ item: c, reason: 'e-mail inválido' }); continue }
    }
    if (needsPhone) {
      if (!c.phone) { skipped.push({ item: c, reason: 'telefone ausente' }); continue }
    }
    sendable.push(c)
  }

  return { sendable, skipped }
}
