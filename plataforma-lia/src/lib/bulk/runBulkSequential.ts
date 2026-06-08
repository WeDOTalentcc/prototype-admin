export interface BulkItemResult<T = unknown> {
  id: string
  name: string
  ok: boolean
  data?: T
  reason?: string
}

export type BulkTickCallback<T = unknown> = (
  done: number,
  total: number,
  latest: BulkItemResult<T>
) => void

/**
 * Executa uma ação assíncrona sequencialmente sobre uma lista de itens.
 * Nunca lança — captura erros por item e os reflete em ok=false + reason.
 * Produtor único para todas as superfícies de bulk da plataforma.
 */
export async function runBulkSequential<T = unknown>(
  items: Array<{ id: string; name: string }>,
  action: (item: { id: string; name: string }) => Promise<T>,
  onTick?: BulkTickCallback<T>
): Promise<BulkItemResult<T>[]> {
  const results: BulkItemResult<T>[] = []
  for (let i = 0; i < items.length; i++) {
    const item = items[i]
    try {
      const data = await action(item)
      const r: BulkItemResult<T> = { id: item.id, name: item.name, ok: true, data }
      results.push(r)
      onTick?.(i + 1, items.length, r)
    } catch (err) {
      const reason =
        err instanceof Error
          ? err.message
          : typeof err === 'object' && err !== null
            ? JSON.stringify(err)
            : String(err)
      const r: BulkItemResult<T> = { id: item.id, name: item.name, ok: false, reason }
      results.push(r)
      onTick?.(i + 1, items.length, r)
    }
  }
  return results
}
