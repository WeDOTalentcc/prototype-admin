let serverReady = false

export async function waitForServer(maxWaitMs = 20_000): Promise<boolean> {
  const start = Date.now()
  while (Date.now() - start < maxWaitMs) {
    try {
      const r = await fetch('/api/backend-proxy/health', { signal: AbortSignal.timeout(5000) })
      if (r.ok) {
        serverReady = true
        return true
      }
    } catch {}
    await new Promise(r => setTimeout(r, 3000))
  }
  return false
}

export async function ensureServerReady(): Promise<void> {
  if (!serverReady) {
    serverReady = await waitForServer(20_000)
  }
}

export async function fetchWithRetry<T>(
  fn: () => Promise<T>,
  retries = 3,
  baseDelayMs = 2000,
): Promise<T> {
  await ensureServerReady()

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      return await fn()
    } catch (err) {
      if (attempt === retries) throw err
      const delay = Math.min(baseDelayMs * Math.pow(1.5, attempt), 15000)
      await new Promise(r => setTimeout(r, delay))
    }
  }
  throw new Error("unreachable")
}
