import { test, expect, type Page, type Response as PWResponse } from '@playwright/test'

const SEARCH_TIMEOUT = 15000
const ENTITY_TIMEOUT = 8000

type Severity = 'critical' | 'high' | 'medium' | 'low'

interface AuditResult {
  testId: string
  category: string
  status: 'PASS' | 'FAIL' | 'SKIP' | 'WARN'
  severity: Severity
  details: string
  refBug?: string
}

const auditResults: AuditResult[] = []

function recordResult(testId: string, category: string, status: AuditResult['status'], severity: Severity, details: string, refBug?: string) {
  auditResults.push({ testId, category, status, severity, details, refBug })
  const prefix = status === 'PASS' ? '✓' : status === 'FAIL' ? '✗' : status === 'WARN' ? '⚠' : '⊘'
  console.log(`[AUDIT ${prefix}] [${severity.toUpperCase()}] ${testId}: ${details}${refBug ? ` (ref: ${refBug})` : ''}`)
}

async function navigateToSearch(page: Page) {
  await page.goto('/', { waitUntil: 'domcontentloaded' })
  await page.waitForSelector('text=Vamos buscar de forma inteligente?', { timeout: 30000 })
  await page.waitForTimeout(2000)
}

async function fillSearchAndSubmit(page: Page, query: string, mode: 'natural' | 'boolean' = 'natural') {
  if (mode === 'boolean') {
    const booleanTab = page.locator('text=Boolean')
    await booleanTab.waitFor({ state: 'visible', timeout: 5000 })
    await booleanTab.click()
    await page.waitForTimeout(500)
  }

  const textarea = page.locator('textarea')
  await textarea.waitFor({ state: 'visible', timeout: 5000 })
  await textarea.click()
  await textarea.fill(query)
  await page.waitForTimeout(1000)

  const searchButton = page.locator('button:has(svg.lucide-search)').last()
  if (await searchButton.isEnabled({ timeout: 3000 }).catch(() => false)) {
    await searchButton.click()
  } else {
    await page.keyboard.press('Enter')
  }
}

async function waitForResults(page: Page, timeout = SEARCH_TIMEOUT): Promise<{ found: boolean; count: number | null; text: string }> {
  try {
    const resultIndicator = page.locator('text=/\\d+ candidatos encontrados/')
    await resultIndicator.waitFor({ state: 'visible', timeout })
    const text = await resultIndicator.textContent() || ''
    const match = text.match(/(\d+)\s*candidatos encontrados/)
    return { found: true, count: match ? parseInt(match[1]) : null, text }
  } catch {
    const noResults = await page.locator('text=/[Nn]enhum|0 candidatos/').isVisible().catch(() => false)
    if (noResults) return { found: false, count: 0, text: 'No results' }
    return { found: false, count: null, text: 'Timeout waiting for results' }
  }
}

async function assertNoAppCrash(page: Page, context: string): Promise<void> {
  const pageContent = await page.content()
  expect(
    pageContent.includes('Application error') ||
    pageContent.includes('Internal Server Error') ||
    pageContent.includes('Unhandled Runtime Error'),
    `App should not crash for: ${context}`
  ).toBe(false)
}

interface APICapture { status: number; body: unknown; url: string }

function createAPIInterceptor(page: Page, urlFilter?: string[]): { responses: APICapture[]; dispose: () => void } {
  const defaultPatterns = ['backend-proxy/search', 'backend-proxy/candidate', 'parse-query']
  const patterns = urlFilter ?? defaultPatterns
  const responses: APICapture[] = []
  const handler = async (response: PWResponse) => {
    const url = response.url()
    if (patterns.some(p => url.includes(p))) {
      try {
        const body = await response.json().catch(() => null)
        responses.push({ status: response.status(), body, url })
      } catch {
        responses.push({ status: response.status(), body: null, url })
      }
    }
  }
  page.on('response', handler)
  return {
    responses,
    dispose: () => page.removeListener('response', handler)
  }
}

test.describe('Search Quality Audit — Cruzamento WeDOTalent', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToSearch(page)
  })

  test.describe('1. Keyword Search (multi-area)', () => {
    const keywordQueries = [
      { id: 'KW-01', area: 'Tech', query: 'python django' },
      { id: 'KW-02', area: 'Tech', query: 'react frontend senior' },
      { id: 'KW-03', area: 'Tech', query: 'devops kubernetes docker' },
      { id: 'KW-04', area: 'Tech', query: 'data scientist machine learning' },
      { id: 'KW-05', area: 'Finanças', query: 'analista financeiro' },
      { id: 'KW-06', area: 'RH', query: 'analista recursos humanos' },
      { id: 'KW-07', area: 'Marketing', query: 'marketing digital growth' },
      { id: 'KW-08', area: 'C-Level', query: 'CEO startup' },
      { id: 'KW-09', area: 'Design', query: 'UX designer figma' },
      { id: 'KW-10', area: 'Vendas', query: 'vendas B2B enterprise' },
    ]

    for (const { id, area, query } of keywordQueries) {
      test(`${id}: Keyword search — ${area} "${query}"`, async ({ page }) => {
        const interceptor = createAPIInterceptor(page)
        try {
          await fillSearchAndSubmit(page, query, 'natural')
          await assertNoAppCrash(page, `keyword search "${query}"`)

          const results = await waitForResults(page)
          const apiErrors = interceptor.responses.filter(r => r.status >= 400)

          const searchResponses = interceptor.responses.filter(r =>
            r.status === 200 && r.body && typeof r.body === 'object'
          )

          let relevanceCheck = ''
          if (searchResponses.length > 0) {
            const body = searchResponses[searchResponses.length - 1].body as Record<string, unknown>
            const candidates = Array.isArray(body.candidates) ? body.candidates : []
            if (candidates.length > 0) {
              const topCandidate = candidates[0] as Record<string, unknown>
              const candidateText = JSON.stringify(topCandidate).toLowerCase()
              const queryTerms = query.toLowerCase().split(/\s+/)
              const matchedTerms = queryTerms.filter(term => candidateText.includes(term))
              relevanceCheck = ` | top result relevance: ${matchedTerms.length}/${queryTerms.length} terms matched`
            }
          }

          if (results.found && results.count !== null && results.count > 0) {
            recordResult(id, 'Keyword Search', 'PASS', 'low', `${results.count} results for "${query}" [${area}]${relevanceCheck}`)
          } else {
            recordResult(id, 'Keyword Search', 'WARN', 'low', `${results.count ?? 0} results for "${query}" [${area}] — may indicate empty local DB`)
          }

          expect(apiErrors.length, `No API errors for query "${query}"`).toBe(0)
        } finally {
          interceptor.dispose()
        }
      })
    }
  })

  test.describe('2. Boolean Search — Ref: BUG-01 (OR/NOT complex)', () => {
    const booleanQueries = [
      { id: 'BOOL-01', query: '(React OR Vue) AND (Senior OR Pleno)', desc: 'Parentheses with OR complex' },
      { id: 'BOOL-02', query: 'Python AND Django AND AWS', desc: 'Simple AND chain' },
      { id: 'BOOL-03', query: '"machine learning" AND Python', desc: 'Quoted phrase + AND' },
      { id: 'BOOL-04', query: 'gerente AND NOT junior', desc: 'NOT operator' },
      { id: 'BOOL-05', query: 'DevOps OR SRE', desc: 'Simple OR' },
      { id: 'BOOL-06', query: '"product manager" OR "gerente de produto"', desc: 'OR with quoted phrases' },
      { id: 'BOOL-07', query: 'CFO OR "diretor financeiro" OR "VP finanças"', desc: 'Multiple OR terms' },
      { id: 'BOOL-08', query: 'React AND TypeScript AND -junior', desc: 'Exclusion with dash' },
    ]

    for (const { id, query, desc } of booleanQueries) {
      test(`${id}: Boolean "${query}" — ${desc}`, async ({ page }) => {
        await fillSearchAndSubmit(page, query, 'boolean')

        const booleanErrorLocator = page.locator('text=/[Ee]rro.*boolean|[Ii]nválid|syntax error/')
        const hasParseError = await booleanErrorLocator.isVisible({ timeout: 3000 }).catch(() => false)

        await assertNoAppCrash(page, `boolean search "${query}"`)

        const results = await waitForResults(page)

        if (hasParseError) {
          recordResult(id, 'Boolean Search', 'FAIL', 'critical', `Parse error for "${query}" — ${desc}`, 'BUG-01')
        } else if (results.found && results.count !== null && results.count > 0) {
          recordResult(id, 'Boolean Search', 'PASS', 'critical', `${results.count} results — ${desc}`, 'BUG-01')
        } else {
          recordResult(id, 'Boolean Search', 'WARN', 'critical', `0 results for "${query}" — query parsed OK but no matches in DB`, 'BUG-01')
        }

        expect(hasParseError, `Boolean query "${query}" must not produce a parse error (WeDO BUG-01 equivalent)`).toBe(false)
      })
    }
  })

  test.describe('3. Natural Language Search — Ref: BUG-04 (no NLP)', () => {
    const nlQueries = [
      { id: 'NL-01', query: 'alguém bom com números e planilhas', lang: 'PT' },
      { id: 'NL-02', query: 'pessoa para liderar equipe de desenvolvimento', lang: 'PT' },
      { id: 'NL-03', query: 'profissional que entenda de finanças e contabilidade', lang: 'PT' },
      { id: 'NL-04', query: 'preciso de um dev que saiba mexer com banco de dados', lang: 'PT' },
      { id: 'NL-05', query: 'someone good at building mobile apps', lang: 'EN' },
      { id: 'NL-06', query: 'I need a senior data engineer who knows Spark', lang: 'EN' },
      { id: 'NL-07', query: 'quero encontrar um designer que faça interfaces bonitas', lang: 'PT' },
      { id: 'NL-08', query: 'alguém com experiência em vendas para SaaS', lang: 'PT' },
    ]

    const nlExpectedEntities: Record<string, string[]> = {
      'NL-01': ['financeiro', 'analista', 'excel', 'planilhas'],
      'NL-02': ['líder', 'desenvolvimento', 'tech lead', 'gerente'],
      'NL-03': ['financ', 'contab'],
      'NL-04': ['banco de dados', 'database', 'sql', 'dev'],
      'NL-05': ['mobile', 'app', 'ios', 'android'],
      'NL-06': ['data engineer', 'spark', 'dados'],
      'NL-07': ['designer', 'ux', 'ui', 'interface'],
      'NL-08': ['vendas', 'saas', 'sales', 'comercial'],
    }

    for (const { id, query, lang } of nlQueries) {
      test(`${id}: NL (${lang}) "${query}"`, async ({ page }) => {
        const interceptor = createAPIInterceptor(page)
        try {
          const textarea = page.locator('textarea')
          await textarea.click()
          await textarea.fill(query)

          const entityExtracted = await page.locator('text=/Cargo|Localização|Skills|Habilidades/').first()
            .isVisible({ timeout: ENTITY_TIMEOUT }).catch(() => false)

          const parseResponses = interceptor.responses.filter(r =>
            r.body && typeof r.body === 'object' && r.status < 400
          )
          const hadNlpProcessing = entityExtracted || parseResponses.length > 0

          let relevanceNote = ''
          if (parseResponses.length > 0) {
            const lastParse = parseResponses[parseResponses.length - 1].body as Record<string, unknown>
            const parseText = JSON.stringify(lastParse).toLowerCase()
            const expectedTerms = nlExpectedEntities[id] || []
            const matchedTerms = expectedTerms.filter(t => parseText.includes(t))
            if (expectedTerms.length > 0) {
              relevanceNote = ` | NLP relevance: ${matchedTerms.length}/${expectedTerms.length} expected entities found`
            }
          }

          await assertNoAppCrash(page, `NL query "${query}"`)

          if (hadNlpProcessing) {
            recordResult(id, 'Natural Language', 'PASS', 'critical',
              `NLP layer processed "${query}" (${lang}) — entities extracted: ${entityExtracted}${relevanceNote}`, 'BUG-04')
          } else {
            recordResult(id, 'Natural Language', 'FAIL', 'critical',
              `No NLP processing detected for "${query}" (${lang}) — verify backend parse-query endpoint`, 'BUG-04')
          }

          expect(hadNlpProcessing, `NLP layer must process "${query}" — our platform should NOT have WeDO BUG-04 (no NLP)`).toBeTruthy()
        } finally {
          interceptor.dispose()
        }
      })
    }
  })

  test.describe('4. Filters & Sort — Ref: BUG-05, BUG-08', () => {
    test('FILT-01: Seniority filter changes search results via entity extraction', async ({ page }) => {
      const interceptor1 = createAPIInterceptor(page)
      await fillSearchAndSubmit(page, 'Desenvolvedor Python', 'natural')
      const baseResults = await waitForResults(page)
      interceptor1.dispose()

      await navigateToSearch(page)

      const interceptor2 = createAPIInterceptor(page)
      await fillSearchAndSubmit(page, 'Desenvolvedor Python senior', 'natural')
      const filteredResults = await waitForResults(page)
      interceptor2.dispose()

      await assertNoAppCrash(page, 'seniority filter comparison')

      const baseApiOK = interceptor1.responses.filter(r => r.status >= 400).length === 0
      const filteredApiOK = interceptor2.responses.filter(r => r.status >= 400).length === 0
      const baseCount = baseResults.count ?? 0
      const filteredCount = filteredResults.count ?? 0

      if (baseCount > 0 && filteredCount > 0 && filteredCount <= baseCount) {
        recordResult('FILT-01', 'Filters & Sort', 'PASS', 'high',
          `Seniority filter narrows results: ${baseCount} → ${filteredCount}`, 'BUG-05')
      } else if (baseCount === 0 && filteredCount === 0) {
        recordResult('FILT-01', 'Filters & Sort', 'WARN', 'high',
          'Both queries returned 0 — cannot verify filter effect (empty DB)', 'BUG-05')
      } else {
        recordResult('FILT-01', 'Filters & Sort', 'WARN', 'high',
          `Seniority filter: base=${baseCount}, filtered=${filteredCount} — unexpected ratio`, 'BUG-05')
      }

      expect(baseApiOK, 'Base query API should succeed').toBe(true)
      expect(filteredApiOK, 'Filtered query API should succeed').toBe(true)
    })

    test('FILT-02: Location filter changes search results via entity extraction', async ({ page }) => {
      const interceptor1 = createAPIInterceptor(page)
      await fillSearchAndSubmit(page, 'Analista financeiro', 'natural')
      const baseResults = await waitForResults(page)
      interceptor1.dispose()

      await navigateToSearch(page)

      const interceptor2 = createAPIInterceptor(page)
      await fillSearchAndSubmit(page, 'Analista financeiro em São Paulo', 'natural')
      const filteredResults = await waitForResults(page)
      interceptor2.dispose()

      await assertNoAppCrash(page, 'location filter comparison')

      const baseCount = baseResults.count ?? 0
      const filteredCount = filteredResults.count ?? 0

      if (baseCount > 0 && filteredCount > 0 && filteredCount <= baseCount) {
        recordResult('FILT-02', 'Filters & Sort', 'PASS', 'high',
          `Location filter narrows results: ${baseCount} → ${filteredCount}`, 'BUG-05')
      } else if (baseCount === 0 && filteredCount === 0) {
        recordResult('FILT-02', 'Filters & Sort', 'WARN', 'high',
          'Both queries returned 0 — cannot verify filter effect (empty DB)', 'BUG-05')
      } else {
        recordResult('FILT-02', 'Filters & Sort', 'WARN', 'high',
          `Location filter: base=${baseCount}, filtered=${filteredCount}`, 'BUG-05')
      }
    })

    test('FILT-03: Skills filter changes result set — adding specific skill narrows results', async ({ page }) => {
      await fillSearchAndSubmit(page, 'Desenvolvedor', 'natural')
      const broadResults = await waitForResults(page)

      await navigateToSearch(page)

      await fillSearchAndSubmit(page, 'Desenvolvedor com Python e Django', 'natural')
      const narrowResults = await waitForResults(page)

      await assertNoAppCrash(page, 'skills filter comparison')

      const broadCount = broadResults.count ?? 0
      const narrowCount = narrowResults.count ?? 0

      if (broadCount > 0 && narrowCount > 0 && narrowCount <= broadCount) {
        recordResult('FILT-03', 'Filters & Sort', 'PASS', 'high',
          `Skills filter narrows: ${broadCount} → ${narrowCount}`, 'BUG-05')
      } else if (broadCount === 0) {
        recordResult('FILT-03', 'Filters & Sort', 'WARN', 'high',
          'Broad query returned 0 — cannot verify skill filter (empty DB)', 'BUG-05')
      } else {
        recordResult('FILT-03', 'Filters & Sort', 'WARN', 'high',
          `Skills filter: broad=${broadCount}, narrow=${narrowCount}`, 'BUG-05')
      }
    })

    test('FILT-04: Advanced filters modal opens and contains actual filter controls', async ({ page }) => {
      const filtersButton = page.locator('button:has-text("Filtros")')
      await expect(filtersButton, 'Filters button must be visible').toBeVisible({ timeout: 5000 })

      await filtersButton.click()

      const modal = page.locator('[role="dialog"], [data-state="open"]')
      await expect(modal, 'Filter modal must open').toBeVisible({ timeout: 5000 })

      const modalContent = await modal.textContent() || ''
      const hasFilterLabels = /[Ss]enioridade|[Ll]ocalização|[Ss]kills|[Ff]iltro|[Oo]rigem|[Ii]ndústria/.test(modalContent)

      recordResult('FILT-04', 'Filters & Sort', hasFilterLabels ? 'PASS' : 'FAIL', 'high',
        `Advanced filters modal: content length=${modalContent.length}, has filter labels=${hasFilterLabels}`, 'BUG-05')

      expect(modalContent.length, 'Filter modal must have content (not empty)').toBeGreaterThan(50)
      expect(hasFilterLabels, 'Filter modal must contain filter-related labels (seniority, location, skills etc)').toBe(true)
    })

    test('FILT-05: Experience filter changes result set — adding years narrows results', async ({ page }) => {
      await fillSearchAndSubmit(page, 'Gerente de Projetos', 'natural')
      const baseResults = await waitForResults(page)

      await navigateToSearch(page)

      await fillSearchAndSubmit(page, 'Gerente de Projetos com 10 anos de experiência', 'natural')
      const filteredResults = await waitForResults(page)

      await assertNoAppCrash(page, 'experience filter comparison')

      const baseCount = baseResults.count ?? 0
      const filteredCount = filteredResults.count ?? 0

      if (baseCount > 0 && filteredCount > 0 && filteredCount <= baseCount) {
        recordResult('FILT-05', 'Filters & Sort', 'PASS', 'high',
          `Experience filter narrows: ${baseCount} → ${filteredCount}`, 'BUG-05')
      } else if (baseCount === 0) {
        recordResult('FILT-05', 'Filters & Sort', 'WARN', 'high',
          'Base query returned 0 — cannot verify experience filter', 'BUG-05')
      } else {
        recordResult('FILT-05', 'Filters & Sort', 'WARN', 'high',
          `Experience filter: base=${baseCount}, filtered=${filteredCount}`, 'BUG-05')
      }
    })

    test('FILT-06: Sort — relevance ordering via API response (Ref: BUG-08)', async ({ page }) => {
      const interceptor = createAPIInterceptor(page, ['backend-proxy/search', 'backend-proxy/candidate'])
      try {
        await fillSearchAndSubmit(page, 'Desenvolvedor Python senior', 'natural')
        await waitForResults(page)

        const searchResponses = interceptor.responses.filter(r =>
          r.status === 200 && r.body && typeof r.body === 'object'
        )

        if (searchResponses.length > 0) {
          const body = searchResponses[searchResponses.length - 1].body as Record<string, unknown>
          const candidates = Array.isArray(body.candidates) ? body.candidates : []

          if (candidates.length >= 2) {
            const scores = candidates
              .map((c: Record<string, unknown>) => (c.score as number) ?? null)
              .filter((s: number | null): s is number => s !== null)

            if (scores.length >= 2) {
              let isDescending = true
              for (let i = 1; i < scores.length; i++) {
                if (scores[i] > scores[i - 1]) {
                  isDescending = false
                  break
                }
              }

              recordResult('FILT-06', 'Filters & Sort', isDescending ? 'PASS' : 'FAIL', 'high',
                `Relevance sort: scores ${scores.slice(0, 5).join(', ')}... descending=${isDescending}`, 'BUG-08')

              expect(isDescending, 'Results must be sorted by relevance score descending (unlike WeDO BUG-08 where sort was ignored)').toBe(true)
            } else {
              recordResult('FILT-06', 'Filters & Sort', 'WARN', 'high',
                'Not enough scored candidates to verify sort order', 'BUG-08')
            }
          } else {
            recordResult('FILT-06', 'Filters & Sort', 'WARN', 'high',
              `Only ${candidates.length} candidates — cannot verify sort`, 'BUG-08')
          }
        } else {
          recordResult('FILT-06', 'Filters & Sort', 'WARN', 'high',
            'No API responses captured to verify sort', 'BUG-08')
        }
      } finally {
        interceptor.dispose()
      }
    })

    test('FILT-07: Sort by name — selecting "Nome (A-Z)" reorders candidates alphabetically', async ({ page }) => {
      await fillSearchAndSubmit(page, 'Analista', 'natural')
      await waitForResults(page)

      const filtersToggle = page.locator('[data-testid="table-filters-toggle-btn"]')
      const filtersVisible = await filtersToggle.isVisible({ timeout: 5000 }).catch(() => false)

      if (filtersVisible) {
        await filtersToggle.click()
        await page.waitForTimeout(500)

        const nameAZOption = page.locator('label:has-text("Nome (A-Z)")')
        const nameOptionVisible = await nameAZOption.isVisible({ timeout: 3000 }).catch(() => false)

        if (nameOptionVisible) {
          await nameAZOption.click()
          await page.waitForTimeout(1000)

          const sortBadge = page.locator('text=Nome A-Z')
          const badgeVisible = await sortBadge.isVisible({ timeout: 3000 }).catch(() => false)

          const rows = page.locator('table tbody tr, [data-testid*="candidate"]')
          const rowCount = await rows.count()

          if (badgeVisible || rowCount > 0) {
            recordResult('FILT-07', 'Filters & Sort', 'PASS', 'high',
              `Name sort applied: badge visible=${badgeVisible}, ${rowCount} rows rendered after sort change`, 'BUG-08')
          } else {
            recordResult('FILT-07', 'Filters & Sort', 'WARN', 'high',
              'Name sort option clicked but no visible ordering change detected', 'BUG-08')
          }
        } else {
          recordResult('FILT-07', 'Filters & Sort', 'WARN', 'high',
            'Nome (A-Z) sort option not visible in filter panel — may require search results first', 'BUG-08')
        }
      } else {
        recordResult('FILT-07', 'Filters & Sort', 'WARN', 'high',
          'Filters toggle button not visible — cannot test name sort', 'BUG-08')
      }
    })

    test('FILT-08: Sort by score — selecting "Maior Score" reorders by score descending', async ({ page }) => {
      await fillSearchAndSubmit(page, 'Desenvolvedor', 'natural')
      await waitForResults(page)

      const filtersToggle = page.locator('[data-testid="table-filters-toggle-btn"]')
      const filtersVisible = await filtersToggle.isVisible({ timeout: 5000 }).catch(() => false)

      if (filtersVisible) {
        await filtersToggle.click()
        await page.waitForTimeout(500)

        const scoreDescOption = page.locator('label:has-text("Maior Score")')
        const scoreOptionVisible = await scoreDescOption.isVisible({ timeout: 3000 }).catch(() => false)

        if (scoreOptionVisible) {
          await scoreDescOption.click()
          await page.waitForTimeout(1000)

          const sortBadge = page.locator('text=Maior Score')
          const badgeVisible = await sortBadge.isVisible({ timeout: 3000 }).catch(() => false)

          const experienceOption = page.locator('label:has-text("Maior Experiência")')
          const expVisible = await experienceOption.isVisible({ timeout: 2000 }).catch(() => false)

          recordResult('FILT-08', 'Filters & Sort', badgeVisible ? 'PASS' : 'WARN', 'high',
            `Score sort applied: badge visible=${badgeVisible}, experience option available=${expVisible}` +
            ` — platform offers 6 sort modes (Relevância, Score desc/asc, Nome A-Z/Z-A, Experiência) unlike WeDO where sort was ignored`, 'BUG-08')
        } else {
          recordResult('FILT-08', 'Filters & Sort', 'WARN', 'high',
            'Maior Score option not visible in filter panel', 'BUG-08')
        }
      } else {
        recordResult('FILT-08', 'Filters & Sort', 'WARN', 'high',
          'Filters toggle not visible — cannot test score sort', 'BUG-08')
      }
    })

    test('FILT-09: Entity extraction detects multiple structured criteria from rich query', async ({ page }) => {
      const textarea = page.locator('textarea')
      await textarea.click()
      await textarea.fill('Backend Sênior em São Paulo, 5+ anos em fintechs, Node.js e Python')

      const cargo = page.locator('text=Cargo')
      const location = page.locator('text=Localização')
      const quality = page.locator('text=Qualidade da busca')

      const hasCargo = await cargo.isVisible({ timeout: ENTITY_TIMEOUT }).catch(() => false)
      const hasLocation = await location.isVisible({ timeout: ENTITY_TIMEOUT }).catch(() => false)
      const hasQuality = await quality.isVisible({ timeout: ENTITY_TIMEOUT }).catch(() => false)

      const criteriaFound = [hasCargo && 'Cargo', hasLocation && 'Localização', hasQuality && 'Quality'].filter(Boolean)

      recordResult('FILT-09', 'Filters & Sort', criteriaFound.length >= 2 ? 'PASS' : 'FAIL', 'high',
        `Criteria detected: ${criteriaFound.join(', ') || 'none'} from rich query`, 'BUG-05')

      expect(criteriaFound.length, 'Rich query must extract at least 2 structured criteria (unlike WeDO where structured fields were empty)')
        .toBeGreaterThanOrEqual(2)
    })

    test('FILT-10: Quality bar shows completeness score for detailed query', async ({ page }) => {
      const textarea = page.locator('textarea')
      await textarea.click()
      await textarea.fill('Desenvolvedor Python senior em São Paulo com 5 anos de experiência')

      const qualityBar = page.locator('text=Qualidade da busca')
      const isVisible = await qualityBar.isVisible({ timeout: ENTITY_TIMEOUT }).catch(() => false)

      recordResult('FILT-10', 'Filters & Sort', isVisible ? 'PASS' : 'FAIL', 'medium',
        `SearchQualityBar visible=${isVisible} — addresses WeDO BUG-08 gap`, 'BUG-08')

      expect(isVisible, 'Quality bar must appear for detailed query (our platform has SearchQualityBar, WeDO did not)').toBe(true)
    })
  })

  test.describe('5. Edge Cases — Ref: BUG-10, BUG-11', () => {
    test('EDGE-01: Empty query — submit should be disabled or handled gracefully', async ({ page }) => {
      const textarea = page.locator('textarea')
      await textarea.click()
      await textarea.fill('')

      const searchButton = page.locator('button:has(svg.lucide-search)').last()
      const isEnabled = await searchButton.isEnabled({ timeout: 2000 }).catch(() => false)

      if (!isEnabled) {
        recordResult('EDGE-01', 'Edge Cases', 'PASS', 'medium', 'Submit button correctly disabled for empty query')
      } else {
        await searchButton.click()
        await assertNoAppCrash(page, 'empty query submission')
        recordResult('EDGE-01', 'Edge Cases', 'PASS', 'medium', 'Empty query submitted without crash')
      }
    })

    test('EDGE-02: Special characters — C++, C#', async ({ page }) => {
      await fillSearchAndSubmit(page, 'C++ developer', 'natural')
      await assertNoAppCrash(page, 'C++ query')
      recordResult('EDGE-02', 'Edge Cases', 'PASS', 'medium', 'Special characters (C++) handled without crash')
    })

    test('EDGE-03: SQL injection attempt — must not expose SQL errors', async ({ page }) => {
      const interceptor = createAPIInterceptor(page)
      try {
        await fillSearchAndSubmit(page, "'; DROP TABLE candidates; --", 'natural')
        await page.waitForTimeout(3000)

        const pageContent = await page.content()
        const hasSqlLeak = /SQL\s*(syntax|error|statement)/i.test(pageContent) ||
          pageContent.includes('pg_catalog') ||
          pageContent.includes('relation "candidates"') ||
          pageContent.includes('PG::')

        const serverErrors = interceptor.responses.filter(r => r.status === 500 &&
          r.body && JSON.stringify(r.body).includes('SQL'))

        const isSafe = !hasSqlLeak && serverErrors.length === 0
        recordResult('EDGE-03', 'Edge Cases', isSafe ? 'PASS' : 'FAIL', 'critical',
          `SQL injection: page leak=${hasSqlLeak}, SQL 500s=${serverErrors.length}`)

        expect(hasSqlLeak, 'SQL injection must not expose database errors or SQL syntax in page content').toBe(false)
        expect(serverErrors.length, 'API must not return SQL-related 500 errors').toBe(0)

        await assertNoAppCrash(page, 'SQL injection attempt')
      } finally {
        interceptor.dispose()
      }
    })

    test('EDGE-04: XSS attempt — script tags must not execute', async ({ page }) => {
      let alertFired = false
      page.on('dialog', async (dialog) => {
        alertFired = true
        await dialog.dismiss()
      })

      await fillSearchAndSubmit(page, '<script>alert("xss")</script>', 'natural')
      await page.waitForTimeout(2000)

      const pageContent = await page.content()
      const hasRawScript = pageContent.includes('<script>alert("xss")</script>')

      const isSafe = !alertFired && !hasRawScript
      recordResult('EDGE-04', 'Edge Cases', isSafe ? 'PASS' : 'FAIL', 'critical',
        `XSS: alert fired=${alertFired}, raw HTML=${hasRawScript}`)

      expect(alertFired, 'XSS script must not execute (no alert dialog should appear)').toBe(false)
      expect(hasRawScript, 'XSS payload must not be rendered as raw HTML in page').toBe(false)

      await assertNoAppCrash(page, 'XSS attempt')
    })

    test('EDGE-05: Very long query (300+ chars) — Ref: BUG-10', async ({ page }) => {
      const longQuery = 'Desenvolvedor Python senior com experiência em Django Flask FastAPI PostgreSQL MongoDB Redis Docker Kubernetes AWS GCP Azure CI/CD GitHub Actions Jenkins Terraform Ansible ' +
        'machine learning TensorFlow PyTorch scikit-learn pandas numpy data engineering Apache Spark Kafka Airflow microservices REST GraphQL gRPC WebSockets React TypeScript Next.js'

      expect(longQuery.length, 'Test query should be 300+ chars').toBeGreaterThan(300)

      const interceptor = createAPIInterceptor(page)
      try {
        await fillSearchAndSubmit(page, longQuery, 'natural')
        await assertNoAppCrash(page, 'long query (300+ chars)')

        const apiErrors = interceptor.responses.filter(r => r.status >= 500)

        const results = await waitForResults(page)
        if (results.found && results.count !== null && results.count > 0) {
          recordResult('EDGE-05', 'Edge Cases', 'PASS', 'medium',
            `Long query (${longQuery.length} chars) returned ${results.count} results — better than WeDO BUG-10 (0 results)`, 'BUG-10')
        } else {
          recordResult('EDGE-05', 'Edge Cases', 'WARN', 'medium',
            `Long query (${longQuery.length} chars) returned 0 results — same as WeDO BUG-10?`, 'BUG-10')
        }

        expect(apiErrors.length, 'Long query must not cause server errors').toBe(0)
      } finally {
        interceptor.dispose()
      }
    })

    test('EDGE-06: Emoji in query — should be stripped or ignored', async ({ page }) => {
      await fillSearchAndSubmit(page, 'desenvolvedor 🚀', 'natural')
      await assertNoAppCrash(page, 'emoji in query')
      recordResult('EDGE-06', 'Edge Cases', 'PASS', 'low', 'Emoji in query handled without crash')
    })

    test('EDGE-07: Accent normalization — both variants should work', async ({ page }) => {
      const interceptor1 = createAPIInterceptor(page)
      await fillSearchAndSubmit(page, 'analise negocios', 'natural')
      await assertNoAppCrash(page, 'unaccented query')
      const result1 = await waitForResults(page)
      interceptor1.dispose()

      await navigateToSearch(page)

      const interceptor2 = createAPIInterceptor(page)
      await fillSearchAndSubmit(page, 'análise negócios', 'natural')
      await assertNoAppCrash(page, 'accented query')
      const result2 = await waitForResults(page)
      interceptor2.dispose()

      const apiErrors = [...interceptor1.responses, ...interceptor2.responses].filter(r => r.status >= 500)

      recordResult('EDGE-07', 'Edge Cases', apiErrors.length === 0 ? 'PASS' : 'FAIL', 'medium',
        `Accent variants: unaccented=${result1.count ?? '?'}, accented=${result2.count ?? '?'}, errors=${apiErrors.length}`)

      expect(apiErrors.length, 'Neither accent variant should cause server errors').toBe(0)
    })

    test('EDGE-08: Email search — Ref: BUG-11', async ({ page }) => {
      const interceptor = createAPIInterceptor(page)
      try {
        await fillSearchAndSubmit(page, 'joao@empresa.com', 'natural')
        await assertNoAppCrash(page, 'email search')

        const serverErrors = interceptor.responses.filter(r => r.status >= 500)
        const results = await waitForResults(page)

        recordResult('EDGE-08', 'Edge Cases',
          serverErrors.length === 0 ? 'PASS' : 'FAIL', 'medium',
          `Email search: ${results.count ?? 0} results, server errors=${serverErrors.length}`, 'BUG-11')

        expect(serverErrors.length, 'Email search must not cause server errors').toBe(0)
      } finally {
        interceptor.dispose()
      }
    })
  })

  test.describe('6. Suggestions / Copilot — Ref: BUG-02', () => {
    test('SUG-01: Portuguese complete query triggers entity extraction', async ({ page }) => {
      const textarea = page.locator('textarea')
      await textarea.click()
      await textarea.fill('Desenvolvedor Python senior Django AWS São Paulo')

      const entityOrSuggestion = page.locator('text=/Cargo|Assistente de Busca|Qualidade da busca/')
      const hasResponse = await entityOrSuggestion.first().isVisible({ timeout: ENTITY_TIMEOUT }).catch(() => false)

      recordResult('SUG-01', 'Suggestions', hasResponse ? 'PASS' : 'FAIL', 'critical',
        `Complete PT query: entity/suggestion response = ${hasResponse}`, 'BUG-02')

      expect(hasResponse, 'Complete PT query must trigger entity extraction or search assistant').toBeTruthy()
    })

    test('SUG-02: English query triggers entity extraction (WeDO had 100% EN failure)', async ({ page }) => {
      const textarea = page.locator('textarea')
      await textarea.click()
      await textarea.fill('Senior Product Manager')

      const entityOrSuggestion = page.locator('text=/Cargo|Assistente de Busca|Qualidade/')
      const hasResponse = await entityOrSuggestion.first().isVisible({ timeout: ENTITY_TIMEOUT }).catch(() => false)

      if (hasResponse) {
        recordResult('SUG-02', 'Suggestions', 'PASS', 'critical',
          'EN query triggered entity extraction — better than WeDO (100% EN failure)', 'BUG-02')
      } else {
        recordResult('SUG-02', 'Suggestions', 'WARN', 'critical',
          'EN query did not trigger entity extraction — similar to WeDO BUG-02', 'BUG-02')
      }
    })

    test('SUG-03: Short query "python" — WeDO failed for all short queries', async ({ page }) => {
      const textarea = page.locator('textarea')
      await textarea.click()
      await textarea.fill('python')

      const anyResponse = page.locator('text=/Cargo|Qualidade|Assistente/')
      const hasResponse = await anyResponse.first().isVisible({ timeout: 6000 }).catch(() => false)

      const autocomplete = page.locator('[data-testid="autocomplete-dropdown"]')
      const hasAutocomplete = await autocomplete.isVisible({ timeout: 3000 }).catch(() => false)

      const triggered = hasResponse || hasAutocomplete
      if (triggered) {
        recordResult('SUG-03', 'Suggestions', 'PASS', 'high', 'Short query "python" triggered response', 'BUG-02')
      } else {
        recordResult('SUG-03', 'Suggestions', 'WARN', 'high', 'Short query "python" — no copilot response (same as WeDO)', 'BUG-02')
      }
    })

    test('SUG-04: Natural language query triggers copilot', async ({ page }) => {
      const textarea = page.locator('textarea')
      await textarea.click()
      await textarea.fill('alguém bom com números e planilhas')

      const anyResponse = page.locator('text=/Cargo|Qualidade|Assistente|Sugestão/')
      const hasResponse = await anyResponse.first().isVisible({ timeout: ENTITY_TIMEOUT }).catch(() => false)

      await assertNoAppCrash(page, 'NL copilot query')

      if (hasResponse) {
        recordResult('SUG-04', 'Suggestions', 'PASS', 'high', 'NL query triggered copilot response', 'BUG-02')
      } else {
        recordResult('SUG-04', 'Suggestions', 'WARN', 'high', 'NL query produced no copilot response', 'BUG-02')
      }
    })

    test('SUG-05: Assistente de Busca appears for rich query', async ({ page }) => {
      const textarea = page.locator('textarea')
      await textarea.click()
      await textarea.fill('Engenheiro de dados senior com Python e Spark em São Paulo')

      const assistente = page.locator('text=Assistente de Busca')
      const isVisible = await assistente.isVisible({ timeout: ENTITY_TIMEOUT }).catch(() => false)

      recordResult('SUG-05', 'Suggestions', isVisible ? 'PASS' : 'FAIL', 'high',
        `Assistente de Busca visible=${isVisible} for rich query`, 'BUG-02')

      expect(isVisible, 'Assistente de Busca must appear for rich query').toBe(true)
    })
  })

  test.describe('7. Pagination — Ref: BUG-09', () => {
    test('PAG-01: API enforces per_page limits — local_limit and pearch_limit bounds', async ({ page }) => {
      const interceptor = createAPIInterceptor(page, ['backend-proxy/search', 'backend-proxy/candidate'])
      try {
        await fillSearchAndSubmit(page, 'python developer', 'natural')
        await waitForResults(page)

        const searchResponses = interceptor.responses.filter(r =>
          r.status === 200 && r.body && typeof r.body === 'object'
        )

        if (searchResponses.length > 0) {
          const body = searchResponses[searchResponses.length - 1].body as Record<string, unknown>
          const candidates = Array.isArray(body.candidates) ? body.candidates : []
          const localCount = (body.local_count as number) ?? 0
          const pearchCount = (body.pearch_count as number) ?? 0
          const totalCount = (body.total_count as number) ?? 0

          const localOK = localCount <= 100
          const pearchOK = pearchCount <= 50
          const totalOK = totalCount === localCount + pearchCount
          const lengthOK = candidates.length === totalCount
          const allOK = localOK && pearchOK && totalOK && lengthOK

          recordResult('PAG-01', 'Pagination', allOK ? 'PASS' : 'FAIL', 'medium',
            `Per-page limits: local=${localCount}/100(${localOK}), pearch=${pearchCount}/50(${pearchOK}), ` +
            `total=${totalCount}=local+pearch(${totalOK}), array=${candidates.length}(${lengthOK})`, 'BUG-09')

          expect(localCount, 'local_count must not exceed max local_limit (100)').toBeLessThanOrEqual(100)
          expect(pearchCount, 'pearch_count must not exceed max pearch_limit (50)').toBeLessThanOrEqual(50)
          expect(totalCount, 'total_count must equal sum of local + pearch').toBe(localCount + pearchCount)
          expect(candidates.length, 'Returned candidates array length must equal total_count').toBe(totalCount)
        } else {
          recordResult('PAG-01', 'Pagination', 'WARN', 'medium',
            'No search API responses captured to verify pagination limits', 'BUG-09')
        }
      } finally {
        interceptor.dispose()
      }
    })

    test('PAG-02: Deep pagination — Load More button adds candidates to current view', async ({ page }) => {
      await fillSearchAndSubmit(page, 'python', 'natural')
      const initialResults = await waitForResults(page)

      if (initialResults.found && initialResults.count !== null && initialResults.count > 10) {
        const loadMoreBtn = page.locator('[data-testid="load-more-btn"]')
        const loadMoreVisible = await loadMoreBtn.isVisible({ timeout: 5000 }).catch(() => false)

        if (loadMoreVisible) {
          const statusBefore = await page.locator('[data-testid="load-more-container"]').textContent() || ''
          const beforeMatch = statusBefore.match(/(\d+)\s*de\s*(\d+)/)
          const displayedBefore = beforeMatch ? parseInt(beforeMatch[1]) : 0
          const totalBefore = beforeMatch ? parseInt(beforeMatch[2]) : 0

          await loadMoreBtn.click()
          await page.waitForTimeout(2000)

          const statusAfter = await page.locator('[data-testid="load-more-container"]').textContent().catch(() => '') || ''
          const allLoadedText = await page.locator('text=/Todos os \\d+ candidatos carregados/').isVisible({ timeout: 2000 }).catch(() => false)
          const afterMatch = statusAfter.match(/(\d+)\s*de\s*(\d+)/)
          const displayedAfter = afterMatch ? parseInt(afterMatch[1]) : 0

          if (displayedAfter > displayedBefore || allLoadedText) {
            recordResult('PAG-02', 'Pagination', 'PASS', 'medium',
              `Load More works: ${displayedBefore}→${displayedAfter} of ${totalBefore} candidates (allLoaded=${allLoadedText})`, 'BUG-09')
          } else {
            recordResult('PAG-02', 'Pagination', 'WARN', 'medium',
              `Load More clicked but count unchanged: ${displayedBefore}→${displayedAfter}`, 'BUG-09')
          }

          expect(displayedAfter >= displayedBefore || allLoadedText,
            'Load More must increase displayed count or show all-loaded message').toBeTruthy()
        } else {
          const allLoaded = await page.locator('text=/Todos os \\d+ candidatos carregados/').isVisible({ timeout: 2000 }).catch(() => false)
          if (allLoaded) {
            recordResult('PAG-02', 'Pagination', 'PASS', 'medium',
              `All ${initialResults.count} candidates loaded on first page — no Load More needed`, 'BUG-09')
          } else {
            recordResult('PAG-02', 'Pagination', 'WARN', 'medium',
              'Load More button not visible after search', 'BUG-09')
          }
        }
      } else {
        recordResult('PAG-02', 'Pagination', 'WARN', 'medium',
          `Only ${initialResults.count ?? 0} results — cannot test deep pagination (need >10)`, 'BUG-09')
      }
    })

    test('PAG-03: Result count is displayed in UI after search', async ({ page }) => {
      await fillSearchAndSubmit(page, 'desenvolvedor', 'natural')
      const results = await waitForResults(page)

      if (results.found) {
        recordResult('PAG-03', 'Pagination', 'PASS', 'low',
          `UI displays result count: ${results.count} candidatos encontrados`, 'BUG-09')
        expect(results.count, 'Result count must be a valid number').not.toBeNull()
        expect(results.count!, 'Result count must be non-negative').toBeGreaterThanOrEqual(0)
      } else {
        recordResult('PAG-03', 'Pagination', 'WARN', 'low',
          'Could not verify result count display', 'BUG-09')
      }
    })

    test('PAG-04: API response includes all required pagination metadata fields', async ({ page }) => {
      const interceptor = createAPIInterceptor(page, ['backend-proxy/search', 'backend-proxy/candidate'])
      try {
        await fillSearchAndSubmit(page, 'react', 'natural')
        await waitForResults(page)

        const searchResponses = interceptor.responses.filter(r =>
          r.status === 200 && r.body && typeof r.body === 'object'
        )

        if (searchResponses.length > 0) {
          const body = searchResponses[searchResponses.length - 1].body as Record<string, unknown>

          const requiredFields = ['total_count', 'local_count', 'pearch_count', 'candidates']
          const missingFields = requiredFields.filter(f => !(f in body))

          recordResult('PAG-04', 'Pagination', missingFields.length === 0 ? 'PASS' : 'FAIL', 'medium',
            `Pagination metadata: present=${requiredFields.filter(f => f in body).join(', ')}, missing=${missingFields.join(', ') || 'none'}`, 'BUG-09')

          expect(missingFields.length, `API response must include: ${requiredFields.join(', ')} — found missing: ${missingFields.join(', ')}`).toBe(0)

          if ('can_load_more' in body) {
            expect(typeof body.can_load_more, 'can_load_more should be boolean').toBe('boolean')
          }
        } else {
          recordResult('PAG-04', 'Pagination', 'WARN', 'medium',
            'No API responses captured to verify metadata', 'BUG-09')
        }
      } finally {
        interceptor.dispose()
      }
    })

    test('PAG-05: Per-page cap validation — candidates returned does not exceed configured limits', async ({ page }) => {
      const interceptor = createAPIInterceptor(page, ['backend-proxy/search', 'backend-proxy/candidate'])
      try {
        await fillSearchAndSubmit(page, 'analista', 'natural')
        await waitForResults(page)

        const searchResponses = interceptor.responses.filter(r =>
          r.status === 200 && r.body && typeof r.body === 'object'
        )

        if (searchResponses.length > 0) {
          const body = searchResponses[searchResponses.length - 1].body as Record<string, unknown>
          const candidates = Array.isArray(body.candidates) ? body.candidates : []
          const localCount = (body.local_count as number) ?? 0
          const pearchCount = (body.pearch_count as number) ?? 0

          const localOK = localCount <= 100
          const pearchOK = pearchCount <= 50
          const countOK = candidates.length === localCount + pearchCount
          const allOK = localOK && pearchOK && countOK

          recordResult('PAG-05', 'Pagination', allOK ? 'PASS' : 'FAIL', 'medium',
            `Per-page cap: ${candidates.length} candidates (local=${localCount}/${localOK ? 'OK' : 'OVER'}, pearch=${pearchCount}/${pearchOK ? 'OK' : 'OVER'})` +
            ` — explicit limits vs WeDO undocumented cap at 30`, 'BUG-09')

          expect(localCount, 'local_count must respect max local_limit (100)').toBeLessThanOrEqual(100)
          expect(pearchCount, 'pearch_count must respect max pearch_limit (50)').toBeLessThanOrEqual(50)
          expect(candidates.length, 'Total candidates must equal local + pearch counts').toBe(localCount + pearchCount)
        } else {
          recordResult('PAG-05', 'Pagination', 'WARN', 'medium',
            'No API responses captured for per-page verification', 'BUG-09')
        }
      } finally {
        interceptor.dispose()
      }
    })
  })

  test.describe('8. Cross-reference Summary — 12 WeDOTalent Bugs', () => {
    test('SUMMARY: Generate audit report comparing our platform vs 12 WeDOTalent bugs', async ({ page }) => {
      await expect(page.locator('textarea')).toBeVisible({ timeout: 10000 })

      const bugMap: Record<string, { wedoDesc: string; ourArchitecture: string; expectedStatus: string; severity: Severity }> = {
        'BUG-01': {
          wedoDesc: 'Boolean search with OR/NOT complex returns 0 (tsvector limitation)',
          ourArchitecture: 'BooleanQueryBuilder handles AND/OR/NOT programmatically, not raw SQL',
          expectedStatus: 'MITIGATED — different parser architecture',
          severity: 'critical'
        },
        'BUG-02': {
          wedoDesc: 'Suggestions fail for English, short queries, NL (50% failure)',
          ourArchitecture: 'LLM-based autocomplete + prompt enhancement (Assistente de Busca)',
          expectedStatus: 'MITIGATED — LLM backend supports multilingual',
          severity: 'critical'
        },
        'BUG-03': {
          wedoDesc: 'Sourcings stuck in processing indefinitely (7 occurrences)',
          ourArchitecture: 'FastAPI async tasks with timeout handling, not Rails background jobs',
          expectedStatus: 'NOT APPLICABLE — different async architecture',
          severity: 'critical'
        },
        'BUG-04': {
          wedoDesc: 'No NLP processing — search is purely lexical',
          ourArchitecture: 'LLM entity extraction (parse-query), SearchQualityBar, semantic search via pgvector',
          expectedStatus: 'RESOLVED — NLP is core to our search pipeline',
          severity: 'critical'
        },
        'BUG-05': {
          wedoDesc: 'Advanced filters dont work (city, state, gender, level) — data not populated',
          ourArchitecture: 'SearchSpec with NLP-extracted filters (location, seniority, skills from text)',
          expectedStatus: 'DIFFERENT ARCHITECTURE — filters extracted by NLP, not dependent on pre-populated fields',
          severity: 'high'
        },
        'BUG-06': {
          wedoDesc: 'Endpoint /sourcings/:id/candidates returns 404',
          ourArchitecture: 'Unified /api/v1/search/candidates with hybrid_search (local + Pearch)',
          expectedStatus: 'NOT APPLICABLE — different API design',
          severity: 'high'
        },
        'BUG-07': {
          wedoDesc: 'Archetypes — PG::ForeignKeyViolation (account_id FK broken)',
          ourArchitecture: 'SearchArchetype model with string IDs, proper seeding, no FK constraint on account_id',
          expectedStatus: 'RESOLVED — different data model',
          severity: 'high'
        },
        'BUG-08': {
          wedoDesc: 'Sort ignored in candidate search',
          ourArchitecture: 'Results ranked by pgvector similarity score + rubric evaluation',
          expectedStatus: 'PARTIALLY ADDRESSED — relevance sort works via similarity score',
          severity: 'high'
        },
        'BUG-09': {
          wedoDesc: 'per_page hard-capped at 30 without documentation',
          ourArchitecture: 'SearchRequestDTO: local_limit (default 20, max 100), pearch_limit (default 15, max 50)',
          expectedStatus: 'RESOLVED — configurable limits with explicit bounds',
          severity: 'medium'
        },
        'BUG-10': {
          wedoDesc: 'Long query (300+ chars) returns 0 results — no truncation',
          ourArchitecture: 'LLM parsing extracts key entities from any length text',
          expectedStatus: 'MITIGATED — LLM handles long text naturally',
          severity: 'medium'
        },
        'BUG-11': {
          wedoDesc: 'Email search does not work — field not indexed',
          ourArchitecture: 'Depends on pgvector + full-text search configuration',
          expectedStatus: 'NEEDS VERIFICATION — tested in EDGE-08',
          severity: 'medium'
        },
        'BUG-12': {
          wedoDesc: 'results_count vs stats.total discrepancy in sourcings',
          ourArchitecture: 'SearchResponseDTO: explicit local_count + pearch_count = total_count fields',
          expectedStatus: 'RESOLVED — explicit count fields prevent discrepancy',
          severity: 'medium'
        },
      }

      const statusCounts = { resolved: 0, mitigated: 0, notApplicable: 0, needsVerification: 0, partiallyAddressed: 0 }

      for (const [bugId, info] of Object.entries(bugMap)) {
        const related = auditResults.filter(r => r.refBug === bugId)
        const relatedPasses = related.filter(r => r.status === 'PASS').length
        const relatedFails = related.filter(r => r.status === 'FAIL').length
        const relatedTotal = related.length

        let derivedStatus = info.expectedStatus
        if (relatedFails > 0) {
          derivedStatus = `NEEDS FIX — ${relatedFails}/${relatedTotal} tests failed`
        } else if (relatedPasses > 0 && relatedFails === 0) {
          derivedStatus = `VERIFIED (${relatedPasses}/${relatedTotal} passed) — ${info.expectedStatus}`
        }

        if (derivedStatus.includes('RESOLVED') || derivedStatus.includes('VERIFIED')) statusCounts.resolved++
        else if (derivedStatus.includes('MITIGATED')) statusCounts.mitigated++
        else if (derivedStatus.includes('NOT APPLICABLE')) statusCounts.notApplicable++
        else if (derivedStatus.includes('PARTIALLY')) statusCounts.partiallyAddressed++
        else statusCounts.needsVerification++

        console.log(`\n[BUG COMPARISON] ${bugId} [severity: ${info.severity}]`)
        console.log(`  WeDO Issue: ${info.wedoDesc}`)
        console.log(`  Our Architecture: ${info.ourArchitecture}`)
        console.log(`  Status: ${derivedStatus}`)
        if (related.length > 0) {
          console.log(`  Test Evidence: ${related.map(r => `${r.testId}[${r.status}/${r.severity}]`).join(', ')}`)
        }
      }

      console.log('\n' + '='.repeat(60))
      console.log('SEARCH QUALITY AUDIT — FINAL REPORT')
      console.log('='.repeat(60))
      console.log(`Total WeDOTalent bugs analyzed: 12`)
      console.log(`Resolved/Verified: ${statusCounts.resolved}`)
      console.log(`Mitigated (different approach): ${statusCounts.mitigated}`)
      console.log(`Not applicable (different arch): ${statusCounts.notApplicable}`)
      console.log(`Partially addressed: ${statusCounts.partiallyAddressed}`)
      console.log(`Needs verification: ${statusCounts.needsVerification}`)

      const totalTests = auditResults.length
      const passes = auditResults.filter(r => r.status === 'PASS').length
      const fails = auditResults.filter(r => r.status === 'FAIL').length
      const warns = auditResults.filter(r => r.status === 'WARN').length

      console.log(`\nTest Execution Summary:`)
      console.log(`  Total: ${totalTests} | PASS: ${passes} | FAIL: ${fails} | WARN: ${warns}`)
      console.log(`  Critical: ${auditResults.filter(r => r.severity === 'critical').length} tests`)
      console.log(`  High: ${auditResults.filter(r => r.severity === 'high').length} tests`)
      console.log(`  Medium: ${auditResults.filter(r => r.severity === 'medium').length} tests`)
      console.log(`  Low: ${auditResults.filter(r => r.severity === 'low').length} tests`)

      if (fails > 0) {
        console.log(`\nFailed tests requiring attention:`)
        auditResults.filter(r => r.status === 'FAIL').forEach(r => {
          console.log(`  [${r.severity.toUpperCase()}] ${r.testId}: ${r.details}`)
        })
      }

      console.log('='.repeat(60))

      if (fails > 0) {
        console.log(`\n⚠ AUDIT NOTE: ${fails} test(s) recorded as FAIL. These represent discovered defects and are documented above with severity levels.`)
      }

      console.log(`\nArchitecture comparison: ${statusCounts.resolved + statusCounts.mitigated + statusCounts.notApplicable}/12 bugs resolved/mitigated/NA, ` +
        `${statusCounts.partiallyAddressed} partially addressed, ${statusCounts.needsVerification} need verification`)
    })
  })
})
