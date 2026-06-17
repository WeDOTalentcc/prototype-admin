import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'

// Task #1177 (addendum Task #1175) — sentinela ratchet para os 4 proxies
// irmãos `backend-proxy/wsi/*` que o commit do #1175 documentou como tendo
// o mesmo anti-padrão (fetch direto sem Authorization) e ficaram pendentes
// para o follow-up. Cada um precisa importar `getAuthHeaders` e NÃO usar
// `headers: { 'Content-Type': 'application/json' }` como literal isolado
// no fetch ao backend (esse literal joga fora os headers de auth).
//
// Quando outro proxy backend-proxy/wsi/* for adicionado, deve seguir o
// mesmo padrão canônico de auth-forward (Authorization / cookies /
// x-company-id) — adicionar nova entrada aqui mantém o ratchet.

const ROUTES = [
  'src/app/api/backend-proxy/wsi/jd-evaluate/route.ts',
  'src/app/api/backend-proxy/wsi/generate-questions/route.ts',
  'src/app/api/backend-proxy/wsi/regenerate-questions/route.ts',
  'src/app/api/backend-proxy/wsi/suggest-question/route.ts',
  'src/app/api/backend-proxy/wsi/questions/save/route.ts',
  'src/app/api/backend-proxy/wsi/questions/adjust/route.ts',
] as const

describe('Task #1177 sentinel — WSI proxy routes forward auth', () => {
  for (const rel of ROUTES) {
    describe(rel, () => {
      const source = readFileSync(join(process.cwd(), rel), 'utf8')

      it('imports getAuthHeaders (canonical auth-forward helper)', () => {
        expect(source).toMatch(/from\s+['"]@\/lib\/api\/auth-headers['"]/)
        expect(source).toMatch(/getAuthHeaders\s*\(\s*request\s*\)/)
      })

      it('does not pass a headers literal containing ONLY Content-Type to fetch', () => {
        // The anti-pattern that drops auth: `headers: { 'Content-Type': 'application/json' }`
        // (with no other keys). Spreading authHeaders alongside Content-Type is fine.
        const offenders = source.match(
          /headers:\s*\{\s*['"]Content-Type['"]\s*:\s*['"]application\/json['"]\s*,?\s*\}/g,
        )
        expect(
          offenders,
          'fetch must not use a bare { "Content-Type": ... } literal — auth headers must be spread in',
        ).toBeNull()
      })

      it('forwards cookie and x-company-id explicitly', () => {
        expect(source).toMatch(/x-company-id/i)
        expect(source).toMatch(/cookie/i)
      })
    })
  }
})
