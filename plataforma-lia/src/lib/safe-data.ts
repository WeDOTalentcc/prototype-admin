export function safeData(data: Record<string, unknown>) {
  return {
    str(key: string, fallback = ''): string {
      const v = data[key]
      return typeof v === 'string' ? v : (v != null ? String(v) : fallback)
    },
    num(key: string, fallback = 0): number {
      const v = data[key]
      return typeof v === 'number' ? v : (Number(v) || fallback)
    },
    bool(key: string, fallback = false): boolean {
      const v = data[key]
      return typeof v === 'boolean' ? v : fallback
    },
    arr<T = unknown>(key: string): T[] {
      const v = data[key]
      return Array.isArray(v) ? v as T[] : []
    },
    rec(key: string): Record<string, unknown> {
      const v = data[key]
      return (typeof v === 'object' && v !== null && !Array.isArray(v))
        ? v as Record<string, unknown>
        : {}
    },
    raw(key: string): unknown {
      return data[key]
    },
  }
}
