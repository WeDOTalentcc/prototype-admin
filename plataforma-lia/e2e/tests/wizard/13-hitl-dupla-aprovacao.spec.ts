/**
 * E2E — Task #1092 — Validação do contrato HITL canônico contra o backend rodando.
 *
 * A sentinela offline (`tests/integration/agents/test_wizard_hitl_unified_contract.py`,
 * S6) prova que `WizardGateService.resume_gate(...)` é idempotente sob
 * concorrência via CAS Redis (acquire-or-wait + Lua finalize_if_owned). Esta
 * spec prova o MESMO invariante na fronteira real: WS ↔ FastAPI ↔ Redis ↔
 * LangGraph checkpointer ↔ banco PostgreSQL.
 *
 * Cenários (3) — todos usam `auth.fixture` para token JWT real do demo user:
 *   D1 — Botão "Aprovar" + chat "sim" enviados quasi-simultaneamente.
 *   D2 — Rejeição via chat ("rejeita") + clique em "Rejeitar".
 *   D3 — Duas abas do mesmo recrutador clicando "Aprovar" em paralelo.
 *
 * INVARIANTES (forte → fraco; todos COM EQUALIDADE EXATA, nunca `<=`):
 *   1. **Backend state** — `delta GET /job-vacancies?source=wizard == EXPECTED`
 *      (D1=1, D2=0, D3=1). É a prova canônica de "criação única": uma vaga
 *      duplicada é violação real do contrato; um audit row duplicado seria
 *      apenas bug de logging.
 *   2. **Audit count** — `GET /admin/audit-decisions/by-user/{userId}`
 *      filtrado por `agent_name == "wizard_gate_service"` E
 *      `decision_type == "generate_feedback"` (canonical mapping de
 *      `wizard_step_completed` via `DECISION_TYPE_MAPPING`). Quando o
 *      usuário não é admin (default em dev = recruiter), endpoint retorna
 *      403 e a verificação é pulada com `console.warn` documentado.
 *      O backend foi atualizado nesta task para propagar `actor_user_id`
 *      do WS handler → wizard_gate_service → audit_service.log_decision.
 *   3. **WS frame counts** — proxy adicional, EXATAS mensagens com
 *      `source: hitl_resume`/`hitl_rejected`. Cada `approval_response` =
 *      1 frame; cached re-broadcast = +1.
 *
 * Pré-requisito: backend `lia-backend` (FastAPI :8001) + frontend
 * `dev-server` (Next.js :5000) rodando, REDIS_URL configurado.
 */
import { Page, BrowserContext, APIRequestContext, Browser } from '@playwright/test'
import { SignJWT } from 'jose'
import { test, expect } from '../../fixtures/auth.fixture'
import { goToChatHome, sendMessageAndWait, SEL } from './01-helpers'

type WsFrame = {
  type?: string
  source?: string
  content?: string
  domain?: string
}
type VacancySnapshot = {
  ids: Set<string>
  total: number
}

const BACKEND_URL =
  process.env.LIA_BACKEND_URL || process.env.BACKEND_URL || 'http://127.0.0.1:8001'
const FRONTEND_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5000'
const DEMO_EMAIL = process.env.DEV_AUTO_LOGIN_EMAIL || 'demo@wedotalent.com'
const DEMO_PASSWORD = process.env.DEV_AUTO_LOGIN_PASSWORD || 'demo123'

/**
 * Mintage canônico de JWT admin para verificação de audit_logs.
 *
 * Usa o mesmo padrão de `eval/eval_runner.py::_make_eval_token` (HS256 sobre
 * SECRET_KEY do backend), com `is_admin=true` claim — o backend
 * (`get_current_user` em `app/auth/dependencies.py:108`) reconhece a claim e
 * promove o user a `UserRole.admin` na primeira chamada, desbloqueando
 * `require_admin` no `/admin/audit-decisions/by-user/{userId}`.
 *
 * Operadores devem fornecer `LIA_SECRET_KEY` (ou `SECRET_KEY`) com o mesmo
 * valor do backend. Sem isso, o teste FALHA fail-LOUD com instruções claras
 * — a verificação de audit é requisito da Task #1092 e não pode ser pulada
 * silenciosamente. CI: ambos `lia-backend` e a suíte Playwright leem o
 * mesmo Doppler/secret store.
 */
async function mintAdminAuditToken(userId: string, companyId: string): Promise<string> {
  const secret = process.env.LIA_SECRET_KEY || process.env.SECRET_KEY
  if (!secret) {
    throw new Error(
      '[task-1092] LIA_SECRET_KEY (ou SECRET_KEY) ausente no ambiente do test. ' +
        'A verificação canônica de audit_logs precisa de um JWT admin assinado com ' +
        'o mesmo SECRET_KEY do backend. Setar via Doppler / .env.local antes de ' +
        'rodar a spec. Mesmo padrão do `eval_runner._make_eval_token`.',
    )
  }
  const expSec = Math.floor(Date.now() / 1000) + 60 * 30
  return await new SignJWT({
    sub: userId,
    company_id: companyId,
    is_admin: true,
    type: 'access',
  })
    .setProtectedHeader({ alg: 'HS256', typ: 'JWT' })
    .setExpirationTime(expSec)
    .sign(new TextEncoder().encode(secret))
}

function attachWsFrameRecorder(page: Page): WsFrame[] {
  const frames: WsFrame[] = []
  page.on('websocket', (ws) => {
    if (!/agent-chat|chat\/ws/i.test(ws.url())) return
    ws.on('framereceived', (event) => {
      const payload =
        typeof event.payload === 'string' ? event.payload : event.payload?.toString('utf8')
      if (!payload) return
      try {
        frames.push(JSON.parse(payload) as WsFrame)
      } catch {
        /* binário/ping — ignore */
      }
    })
  })
  return frames
}
function countFrames(frames: WsFrame[], kind: 'hitl_resume' | 'hitl_rejected'): number {
  return frames.filter(
    (f) => f && (f.type === 'message' || f.type === undefined) && f.source === kind,
  ).length
}

/** Login direto contra o backend e seed cookies — replica auth.fixture
 *  para uso em contextos secundários (D3 cross-tab). */
async function loginAndSeedContext(
  ctx: BrowserContext,
  request: APIRequestContext,
): Promise<void> {
  const url = `${BACKEND_URL}/api/v1/auth/login`
  const resp = await request.post(url, {
    data: { email: DEMO_EMAIL, password: DEMO_PASSWORD },
    headers: { 'Content-Type': 'application/json' },
    failOnStatusCode: true,
    timeout: 15_000,
  })
  const body = (await resp.json()) as { access_token?: string; data?: { access_token?: string } }
  const accessToken = body.access_token || body.data?.access_token
  if (!accessToken) throw new Error('login: access_token ausente da resposta')
  let domain = 'localhost'
  try {
    if (process.env.PLAYWRIGHT_BASE_URL) domain = new URL(process.env.PLAYWRIGHT_BASE_URL).hostname
  } catch {
    /* keep localhost */
  }
  await ctx.addCookies([
    { name: 'lia_access_token', value: accessToken, domain, path: '/', httpOnly: true, sameSite: 'Lax' },
    { name: 'lia_auth_method', value: 'jwt', domain, path: '/' },
  ])
}

async function snapshotWizardVacancies(ctx: BrowserContext): Promise<VacancySnapshot> {
  // Absolute URL — `browser.newContext()` (D3) não herda baseURL do config.
  const resp = await ctx.request.get(`${FRONTEND_URL}/api/v1/job-vacancies?source=wizard&limit=500`)
  if (!resp.ok()) {
    throw new Error(
      `GET /api/v1/job-vacancies?source=wizard falhou: ${resp.status()} ${(await resp.text()).slice(0, 300)}`,
    )
  }
  const body = (await resp.json()) as { items?: Array<{ id?: string }>; total?: number }
  const items = body.items ?? []
  return {
    ids: new Set(items.map((it) => String(it.id ?? '')).filter(Boolean)),
    total: typeof body.total === 'number' ? body.total : items.length,
  }
}

/**
 * Aguarda o backend mostrar o delta esperado.
 *
 * - `expectedDelta > 0`: poll até `delta >= expectedDelta` ou timeout, então
 *   retorna (caller asserta exato).
 * - `expectedDelta === 0`: poll a janela INTEIRA (`timeoutMs`); falha cedo
 *   se aparecer qualquer ID novo (delayed async creation cataloga como
 *   violação real do contrato de rejeição). Retorna delta=0 só se nenhum
 *   ID novo apareceu durante a janela toda.
 */
async function waitForVacancyDelta(
  ctx: BrowserContext,
  before: VacancySnapshot,
  expectedDelta: number,
  timeoutMs: number,
): Promise<{ delta: number; newIds: string[] }> {
  const deadline = Date.now() + timeoutMs
  let last: VacancySnapshot = before
  while (Date.now() < deadline) {
    last = await snapshotWizardVacancies(ctx)
    const newIds = [...last.ids].filter((id) => !before.ids.has(id))
    if (expectedDelta === 0) {
      // Modo strict-zero: qualquer aparição é falha imediata; observa janela
      // inteira para capturar criações async tardias.
      if (newIds.length > 0) return { delta: newIds.length, newIds }
      // continua observando até esgotar timeoutMs
    } else if (newIds.length >= expectedDelta) {
      return { delta: newIds.length, newIds }
    }
    await new Promise((r) => setTimeout(r, 1500))
  }
  const newIds = [...last.ids].filter((id) => !before.ids.has(id))
  return { delta: newIds.length, newIds }
}

/**
 * Conta audit rows do `wizard_gate_service` para o usuário no intervalo,
 * usando JWT admin minted via `mintAdminAuditToken` (não depende do role
 * do user logado). Filtro robusto: agent_name + decision_type canônico
 * (mapped via `DECISION_TYPE_MAPPING["wizard_step_completed"]` →
 * `generate_feedback`, valor PERSISTIDO em `audit_logs.decision_type`)
 * + action começando com `resume_gate:`.
 */
async function countWizardGateAuditRows(
  userId: string,
  companyId: string,
  dateFromIso: string,
  reqCtx: APIRequestContext,
): Promise<number> {
  const adminToken = await mintAdminAuditToken(userId, companyId)
  const resp = await reqCtx.get(
    `${BACKEND_URL}/api/v1/admin/audit-decisions/by-user/${encodeURIComponent(userId)}` +
      `?date_from=${encodeURIComponent(dateFromIso)}&limit=500`,
    { headers: { Authorization: `Bearer ${adminToken}` } },
  )
  if (!resp.ok()) {
    throw new Error(
      `GET /admin/audit-decisions/by-user falhou: ${resp.status()} ${(await resp.text()).slice(0, 300)}`,
    )
  }
  const body = (await resp.json()) as { audit_logs?: Array<Record<string, unknown>> }
  const rows = body.audit_logs ?? []
  return rows.filter(
    (r) =>
      r.agent_name === 'wizard_gate_service' &&
      r.decision_type === 'generate_feedback' &&
      typeof r.action === 'string' &&
      (r.action as string).startsWith('resume_gate:'),
  ).length
}

async function getCurrentUserInfo(
  ctx: BrowserContext,
): Promise<{ id: string; companyId: string }> {
  const resp = await ctx.request.get(`${FRONTEND_URL}/api/v1/auth/me`)
  if (!resp.ok()) {
    throw new Error(
      `GET /api/v1/auth/me falhou: ${resp.status()} ${(await resp.text()).slice(0, 300)}`,
    )
  }
  const body = (await resp.json()) as {
    id?: string
    company_id?: string
    user?: { id?: string; company_id?: string }
  }
  const id = body.id || body.user?.id
  const companyId = body.company_id || body.user?.company_id
  if (!id || !companyId) {
    throw new Error(
      `/api/v1/auth/me retornou payload incompleto: ${JSON.stringify(body).slice(0, 300)}`,
    )
  }
  return { id: String(id), companyId: String(companyId) }
}

/** Manda o wizard até `jd_enrichment` (HITL #1) — fail-LOUD se não chega. */
async function reachJdEnrichmentStage(page: Page, vagaPrompt: string): Promise<void> {
  await goToChatHome(page)
  await sendMessageAndWait(page, vagaPrompt, { timeout: 90_000 })
  const stageLoc = page
    .locator('[data-wizard-stage="jd_enrichment"], [data-testid*="wizard-jd"]')
    .first()
  if (!(await stageLoc.isVisible({ timeout: 30_000 }).catch(() => false))) {
    await sendMessageAndWait(page, 'confirma', { timeout: 60_000 })
  }
  await expect(
    stageLoc,
    'wizard precisa estar em jd_enrichment para o HITL aparecer',
  ).toBeVisible({ timeout: 90_000 })
}

function approveButton(page: Page) {
  return page.getByRole('button', { name: /aprovar|aprovo|publicar/i }).first()
}
function rejectButton(page: Page) {
  return page.getByRole('button', { name: /rejeitar|cancelar|recusar/i }).first()
}

/** Espera HITL card — fail-LOUD se não aparecer (em vez de skip silencioso). */
async function waitForHitlCard(page: Page, btn: ReturnType<typeof approveButton>): Promise<void> {
  await expect(
    btn,
    'HITLConfirmCard com botão de ação deve aparecer após reach jd_enrichment ' +
      '(LIA_WIZARD_LLM_GATES=true precisa estar ativo no backend).',
  ).toBeVisible({ timeout: 60_000 })
}

test.describe('Task #1092 — HITL contrato canônico contra backend rodando', () => {
  test('D1 — botão "Aprovar" + chat "sim" simultâneos criam EXATAMENTE 1 vaga', async ({
    authenticatedPage: page,
    context,
  }) => {
    const frames = attachWsFrameRecorder(page)
    const { id: userId, companyId } = await getCurrentUserInfo(context)
    const dateFrom = new Date().toISOString()

    const vacanciesBefore = await snapshotWizardVacancies(context)

    await reachJdEnrichmentStage(
      page,
      'quero criar uma vaga de Engenheiro Backend Pleno em São Paulo, remoto, faixa 12-18k',
    )

    const approve = approveButton(page)
    await waitForHitlCard(page, approve)

    const framesBefore = frames.length

    // Race REAL — sem swallow. Se um lado falhar, o teste falha fail-loud.
    await Promise.all([
      approve.click(),
      sendMessageAndWait(page, 'sim', { timeout: 30_000 }),
    ])

    // INVARIANTE PRIMÁRIO: backend criou EXATAMENTE 1 vaga.
    const { delta, newIds } = await waitForVacancyDelta(context, vacanciesBefore, 1, 60_000)
    expect(
      delta,
      `Backend criou ${delta} vaga(s) (ids: ${JSON.stringify(newIds)}); esperado EXATAMENTE 1. ` +
        `>1 = duplicação real do gate (CAS atômico falhou).`,
    ).toBe(1)

    // INVARIANTE SECUNDÁRIO ENFORCED: 1 audit row via JWT admin minted.
    const auditCount = await countWizardGateAuditRows(userId, companyId, dateFrom, context.request)
    expect(
      auditCount,
      `audit_logs gravou ${auditCount} row(s) wizard_gate_service/resume_gate; esperado EXATAMENTE 1.`,
    ).toBe(1)

    // PROXY: 1 approval_response WS = 1 hitl_resume frame.
    const resumeCount = countFrames(frames.slice(framesBefore), 'hitl_resume')
    expect(
      resumeCount,
      `WS deveria receber EXATAS 1 frame hitl_resume (recebeu ${resumeCount}).`,
    ).toBe(1)
  })

  test('D2 — rejeição via chat + clique em "Rejeitar" criam ZERO vagas e 1 audit', async ({
    authenticatedPage: page,
    context,
  }) => {
    const frames = attachWsFrameRecorder(page)
    const { id: userId, companyId } = await getCurrentUserInfo(context)
    const dateFrom = new Date().toISOString()

    const vacanciesBefore = await snapshotWizardVacancies(context)

    await reachJdEnrichmentStage(
      page,
      'quero criar uma vaga de Analista Financeiro Pleno em SP, presencial, faixa 8-12k',
    )

    const reject = rejectButton(page)
    await waitForHitlCard(page, reject)

    const framesBefore = frames.length

    await Promise.all([
      reject.click(),
      sendMessageAndWait(page, 'rejeita, refaz tudo', { timeout: 30_000 }),
    ])

    // INVARIANTE PRIMÁRIO: rejeição NÃO cria vaga. Janela de observação
    // 30s — strict-zero falha cedo se aparecer ID novo (pega criação async).
    const { delta, newIds } = await waitForVacancyDelta(context, vacanciesBefore, 0, 30_000)
    expect(
      delta,
      `Rejeição NÃO pode criar vagas (criou ${delta}: ${JSON.stringify(newIds)}).`,
    ).toBe(0)

    // INVARIANTE SECUNDÁRIO ENFORCED: 1 audit row de rejeição.
    const auditCount = await countWizardGateAuditRows(userId, companyId, dateFrom, context.request)
    expect(
      auditCount,
      `Esperado EXATAS 1 audit row de rejeição; gravou ${auditCount}.`,
    ).toBe(1)

    // PROXY: 1 hitl_rejected, ZERO hitl_resume (paths não se misturam).
    const rejectedCount = countFrames(frames.slice(framesBefore), 'hitl_rejected')
    const resumeCount = countFrames(frames.slice(framesBefore), 'hitl_resume')
    expect(
      rejectedCount,
      `Esperado EXATAS 1 frame hitl_rejected (got ${rejectedCount}).`,
    ).toBe(1)
    expect(
      resumeCount,
      'Rejeição NÃO pode coexistir com hitl_resume na mesma janela.',
    ).toBe(0)
  })

  test('D3 — duas abas aprovando em paralelo criam 1 ÚNICA vaga (CAS cross-process)', async ({
    browser,
    request,
  }: { browser: Browser; request: APIRequestContext }) => {
    // Contexto autenticado fresh com baseURL explícito (newContext NÃO herda
    // do `use.baseURL` do config) e auth via login + cookies httpOnly.
    const ctx: BrowserContext = await browser.newContext({ baseURL: FRONTEND_URL })
    await loginAndSeedContext(ctx, request)

    const { id: userId, companyId } = await getCurrentUserInfo(ctx)
    const dateFrom = new Date().toISOString()
    const vacanciesBefore = await snapshotWizardVacancies(ctx)

    const tabA = await ctx.newPage()
    const framesA = attachWsFrameRecorder(tabA)

    await reachJdEnrichmentStage(
      tabA,
      'quero criar uma vaga de Coordenador de Produto Pleno remoto, faixa 14-20k',
    )
    const approveA = approveButton(tabA)
    await waitForHitlCard(tabA, approveA)

    // Aba B no mesmo contexto (cookies httpOnly compartilhados → mesmo user).
    const tabB = await ctx.newPage()
    const framesB = attachWsFrameRecorder(tabB)
    await tabB.goto(tabA.url(), { waitUntil: 'domcontentloaded', timeout: 60_000 })
    const approveB = approveButton(tabB)
    await waitForHitlCard(tabB, approveB)

    const framesABefore = framesA.length
    const framesBBefore = framesB.length

    // Clique simultâneo cross-tab — força o CAS Redis a serializar.
    await Promise.all([approveA.click(), approveB.click()])
    await Promise.all([tabA.waitForTimeout(30_000), tabB.waitForTimeout(30_000)])

    // INVARIANTE PRIMÁRIO: 1 ÚNICA vaga, mesmo com 2 cliques cross-tab.
    const { delta, newIds } = await waitForVacancyDelta(ctx, vacanciesBefore, 1, 60_000)
    expect(
      delta,
      `2 abas aprovando em paralelo criaram ${delta} vagas (${JSON.stringify(newIds)}); ` +
        `esperado EXATAMENTE 1. >1 = CAS Redis falhou em serializar entre processos.`,
    ).toBe(1)

    // INVARIANTE SECUNDÁRIO ENFORCED: 1 audit row, não 2.
    const auditCount = await countWizardGateAuditRows(userId, companyId, dateFrom, ctx.request)
    expect(
      auditCount,
      `Esperado EXATAS 1 audit wizard_gate_service/resume_gate; gravou ${auditCount}.`,
    ).toBe(1)

    // PROXY: cada aba recebe 1 frame de resposta (1 real + 1 cached).
    const resumeA = countFrames(framesA.slice(framesABefore), 'hitl_resume')
    const resumeB = countFrames(framesB.slice(framesBBefore), 'hitl_resume')
    expect(
      resumeA + resumeB,
      `Total de frames hitl_resume (A=${resumeA}, B=${resumeB}); esperado EXATAS 2.`,
    ).toBe(2)

    // Anti-padrão: nenhum frame de erro de gate.
    const allFrames = [...framesA.slice(framesABefore), ...framesB.slice(framesBBefore)]
    const erroGate = allFrames.filter((f) =>
      /erro ao processar a aprovação do wizard/i.test(f?.content ?? ''),
    ).length
    expect(erroGate, 'Frame de erro de gate apareceu — investigar lease expiration.').toBe(0)

    await ctx.close()
  })
})
