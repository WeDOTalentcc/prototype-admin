import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'

const ROUTE_PATH = join(
  process.cwd(),
  'src/app/api/backend-proxy/jd/generate/route.ts',
)

describe('Task #1175 sentinel — JD generate proxy forwards auth', () => {
  const source = readFileSync(ROUTE_PATH, 'utf8')

  it('imports getAuthHeaders (canonical auth-forward helper)', () => {
    expect(source).toMatch(/from\s+['"]@\/lib\/api\/auth-headers['"]/)
    expect(source).toMatch(/getAuthHeaders\s*\(\s*request\s*\)/)
  })

  it('passes a headers object (not a bare Content-Type literal) to fetch', () => {
    const fetchCall = source.match(
      /fetch\s*\(\s*`\$\{BACKEND_URL\}\/api\/v1\/jd\/generate`\s*,\s*\{[\s\S]*?\}\s*\)/,
    )
    expect(fetchCall, 'fetch(`${BACKEND_URL}/api/v1/jd/generate`, {...}) not found').toBeTruthy()
    const block = fetchCall![0]
    expect(
      /headers:\s*\{\s*['"]Content-Type['"]\s*:\s*['"]application\/json['"]\s*\}/.test(block),
      'fetch must not use a hard-coded { "Content-Type": ... } literal (auth headers are dropped)',
    ).toBe(false)
    expect(/headers\s*[:,]/.test(block), 'fetch must pass a headers field').toBe(true)
  })
})
