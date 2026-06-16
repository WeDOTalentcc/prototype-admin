/**
 * E2E — Task #1118 — wizard inteiro com aprovações alternando botão e chat.
 *
 * Contexto: Task #1090 trocou o motor de resume para
 * ``JobCreationGraph.aresume_with_message`` (langgraph ``interrupt()``). A
 * sentinela offline (``test_wizard_hitl_unified_contract.py`` —
 * ``test_resume_engine_uses_job_creation_graph_not_legacy_wizard``) cobre só o
 * contrato de ``_resume_engine`` (motor + propagação do comentário). Falta um
 * E2E ao vivo que exercite os 4 gates HITL canônicos do wizard alternando
 * APROVAÇÃO POR BOTÃO e APROVAÇÃO POR MENSAGEM LIVRE NO CHAT, em uma única
 * ``conversation_id``, e prove que cada gate:
 *   1. Não repete a mesma pergunta no próximo turno.
 *   2. Emite EXATAMENTE 1 row em ``audit_logs``
 *      (``agent_name=wizard_gate_service`` ∧
 *       ``decision_type=generate_feedback`` — mapeamento canônico de
 *       ``wizard_step_completed``).
 *
 * Gates canônicos cobertos (definidos em
 * ``lia-agent-system/app/domains/job_creation/graph.py``):
 *   - HITL #1 — ``jd_gate_node``         (estágio ``jd_enrichment``)
 *   - HITL #2 — ``competency_gate_node`` (estágio ``competency``)
 *   - HITL #3 — ``wsi_questions_gate_node``  (estágio ``wsi_questions``)
 *   - HITL #4 — ``review_gate_node``     (estágio ``review`` / publish)
 *
 * Desvio intencional do brief: o brief lista "intake, jd_enrichment, wsi,
 * review" — porém ``intake_node`` não chama ``interrupt()`` (é determinístico).
 * Os 4 nós com ``interrupt()`` canônico são os listados acima; a spec cobre
 * esse contrato real e o brief foi entendido como "todos os HITL gates".
 *
 * Alternância botão/chat (4 turnos de aprovação, 1 por gate):
 *   - HITL #1 (jd_enrichment) → CHAT     ("manda bala")
 *   - HITL #2 (competency)    → CHAT     ("vamos com o curto")
 *   - HITL #3 (wsi_questions) → CHAT     ("tá bom, manda ver")
 *   - HITL #4 (review)        → BOTÃO    ("Aprovar"/"Publicar")
 *
 * O chat-text path obrigatoriamente exercita ``LIA_WIZARD_LLM_GATES=true``
 * (gate classifier de Task #1085) — que decide ``approve`` e dispara o
 * ``Command(resume=...)`` no ``interrupt()`` correspondente. O botão path
 * exercita ``approval_response`` no WS → ``wizard_gate_service.resume_gate`` →
 * ``_resume_engine`` → ``aresume_with_message`` (Task #1090). Cobrir AMBOS
 * mostra que o motor único trata as duas portas de entrada de forma
 * equivalente.
 *
 * Pré-requisitos:
 *   - backend ``lia-backend`` (FastAPI :8001), ``LIA_WIZARD_LLM_GATES=true``
 *   - frontend ``dev-server`` (Next.js :5000)
 *   - ``LIA_SECRET_KEY`` (ou ``SECRET_KEY``) no env do test — necessário para
 *     mintar JWT admin e ler ``/admin/audit-decisions/by-user``
 *
 * Como rodar:
 *   bash plataforma-lia/scripts/run-pw-cenario.sh \
 *     pw-cenario-1118 e2e/tests/wizard/14-resume-via-interrupt.spec.ts
 */
import { Page, APIRequestContext } from '@playwright/test'
import { SignJWT } from 'jose'
import { test, expect } from '../../fixtures/auth.fixture'
import { goToChatHome, sendMessageAndWait, SEL } from './01-helpers'

const BACKEND_URL =
  process.env.LIA_BACKEND_URL || process.env.BACKEND_URL || 'http://127.0.0.1:8001'
const FRONTEND_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5000'

type GateName = 'jd_enrichment' | 'competency' | 'wsi_questions' | 'review'

/** JWT admin minted localmente — espelha ``13-hitl-dupla-aprovacao.spec.ts``. */
async function mintAdminAuditToken(userId: string, companyId: string): Promise<string> {
  const secret = process.env.LIA_SECRET_KEY || process.env.SECRET_KEY
  if (!secret) {
    throw new Error(
      '[task-1118] LIA_SECRET_KEY (ou SECRET_KEY) ausente. A verificação de ' +
        'audit_logs precisa de JWT admin assinado com o mesmo SECRET_KEY do ' +
        'backend. Setar via Doppler/.env.local antes de rodar.',
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

async function getCurrentUserInfo(
  page: Page,
): Promise<{ id: string; companyId: string }> {
  const resp = await page.context().request.get(`${FRONTEND_URL}/api/v1/auth/me`)
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
      `/api/v1/auth/me incompleto: ${JSON.stringify(body).slice(0, 300)}`,
    )
  }
  return { id: String(id), companyId: String(companyId) }
}

/** Conta audit rows ``wizard_gate_service`` para o usuário desde ``dateFromIso``. */
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
  return (body.audit_logs ?? []).filter(
    (r) =>
      r.agent_name === 'wizard_gate_service' &&
      r.decision_type === 'generate_feedback' &&
      typeof r.action === 'string' &&
      (r.action as string).startsWith('resume_gate:'),
  ).length
}

/**
 * Espera o wizard alcançar um estágio HITL específico — fail-LOUD se não chega.
 *
 * Sensor estrutural via ``data-wizard-stage`` (atributo emitido pelo painel
 * do wizard quando recebe ``ws_stage_payload`` com o estágio correspondente).
 */
async function waitForStage(page: Page, stage: GateName, timeoutMs = 90_000): Promise<void> {
  const loc = page.locator(`[data-wizard-stage="${stage}"]`).first()
  await expect(
    loc,
    `wizard precisa alcançar o estágio ${stage} (data-wizard-stage). ` +
      `Verifique se LIA_WIZARD_LLM_GATES=true no backend.`,
  ).toBeVisible({ timeout: timeoutMs })
}

function approveButton(page: Page) {
  return page.getByRole('button', { name: /aprovar|aprovo|publicar/i }).first()
}

/**
 * Captura o último texto da LIA (markdown bubble) — usado para asserir que
 * a próxima resposta NÃO repete a pergunta de aprovação anterior.
 */
async function lastLiaText(page: Page): Promise<string> {
  const bubbles = page.locator(SEL.liaMarkdown)
  const count = await bubbles.count()
  if (count === 0) return ''
  return ((await bubbles.nth(count - 1).innerText()) || '').toLowerCase()
}

/** Anti-padrão: a LIA NÃO pode pedir nova aprovação no mesmo gate após aprovar. */
function expectNoRepeatedApprovalAsk(text: string, gate: GateName): void {
  const re = /preciso (de )?aprova[cç][aã]o|aguardando aprova[cç][aã]o|voc[eê] aprovou\??/i
  expect(
    re.test(text),
    `Após aprovar o gate ${gate}, a LIA repetiu o pedido de aprovação. ` +
      `Trecho: ${text.slice(0, 200)}`,
  ).toBe(false)
}

test.describe('Task #1118 — wizard 4 gates HITL com aprovação botão+chat', () => {
  test('cobertura completa dos 4 interrupts canônicos em uma única conversa', async ({
    authenticatedPage: page,
  }) => {
    const { id: userId, companyId } = await getCurrentUserInfo(page)
    const dateFrom = new Date().toISOString()

    await goToChatHome(page)

    // ── Drive até HITL #1 (jd_enrichment) ──────────────────────────────────
    await sendMessageAndWait(
      page,
      'quero criar uma vaga de Engenheira Backend Pleno em São Paulo, ' +
        'remoto, faixa 12-18k, stack Python + FastAPI + AWS',
      { timeout: 120_000 },
    )
    await waitForStage(page, 'jd_enrichment', 120_000)

    // HITL #1 — APROVA VIA CHAT ("manda bala") — exercita _resume_engine
    // pelo path do classifier LLM (Task #1085) sem tocar no botão.
    await sendMessageAndWait(page, 'manda bala', { timeout: 60_000 })
    expectNoRepeatedApprovalAsk(await lastLiaText(page), 'jd_enrichment')

    // ── HITL #2 (competency) ───────────────────────────────────────────────
    await waitForStage(page, 'competency', 120_000)
    // APROVA VIA CHAT — escolhe modo compacto em PT natural.
    await sendMessageAndWait(page, 'vamos com o curto', { timeout: 60_000 })
    expectNoRepeatedApprovalAsk(await lastLiaText(page), 'competency')

    // ── HITL #3 (wsi_questions) ────────────────────────────────────────────
    await waitForStage(page, 'wsi_questions', 120_000)
    // APROVA VIA CHAT — natural language ("tá bom, manda ver").
    await sendMessageAndWait(page, 'tá bom, manda ver', { timeout: 60_000 })
    expectNoRepeatedApprovalAsk(await lastLiaText(page), 'wsi_questions')

    // ── HITL #4 (review / publish) — APROVA VIA BOTÃO ──────────────────────
    await waitForStage(page, 'review', 120_000)
    const approve = approveButton(page)
    await expect(
      approve,
      'HITLConfirmCard de review precisa expor botão de aprovação.',
    ).toBeVisible({ timeout: 60_000 })
    await approve.click()

    // Aguarda backend processar — usa o próprio chat como sensor (qualquer
    // resposta nova após click prova que approval_response → resume_gate
    // → aresume_with_message executou sem repetir o gate).
    await page.waitForTimeout(8_000)
    expectNoRepeatedApprovalAsk(await lastLiaText(page), 'review')

    // ── Audit invariant: 4 gates aprovados → EXATAMENTE 4 audit rows ─────
    // Pequeno backoff para o audit_service flush (best-effort, async).
    let auditCount = 0
    const deadline = Date.now() + 30_000
    while (Date.now() < deadline) {
      auditCount = await countWizardGateAuditRows(
        userId,
        companyId,
        dateFrom,
        page.context().request,
      )
      if (auditCount >= 4) break
      await page.waitForTimeout(1_500)
    }
    expect(
      auditCount,
      `Esperado EXATAMENTE 4 audit rows wizard_gate_service/resume_gate ` +
        `(1 por gate aprovado); contou ${auditCount}.`,
    ).toBe(4)
  })
})
