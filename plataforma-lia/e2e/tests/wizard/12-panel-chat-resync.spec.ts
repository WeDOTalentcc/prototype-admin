/**
 * E2E sentinel — Task #1097 wizard panel ↔ chat resync after browser reload.
 *
 * Problema B identificado na auditoria do wizard (Task #1096): após o
 * recrutador recarregar a página no meio do wizard, o checkpoint LangGraph é
 * preservado pelo backend (Task #1080) mas o painel direito e o chat dianteiro
 * podiam entrar em estados inconsistentes — o painel mostrava a JD enriquecida
 * enquanto o chat aparecia "vazio" até o próximo turno.
 *
 * Modelo canônico Task #1097:
 *   • Backend (`agent_chat_ws.py`) re-emite `wizard_stage` (com `resumed=true`)
 *     logo após `connected` quando o checkpoint do wizard ainda está aberto,
 *     para o `useWizardFlow` rehidratar painel + stage determinísticamente.
 *   • Frontend (`lia-float-context.tsx`) persiste `chatConversationId` em
 *     `sessionStorage` e dispara `loadChatHistory` automaticamente no mount,
 *     restaurando o último turno do chat sem precisar de interação do usuário.
 *
 * Estratégia: estabelece contexto no wizard, recarrega, e valida que o painel
 * direito + a última mensagem do chat continuam visíveis SEM enviar nada novo.
 */
import { test, expect } from '@playwright/test'
import { authenticateAsRecruiter } from '../../fixtures/auth.fixture'
import {
  openJobWizard,
  sendWizardMessage,
} from '../../fixtures/wizard-conversation.fixture'

const ROLE_TITLE = `Engenheiro de Dados Pleno ${Date.now()}`

test.describe('Wizard — painel + chat re-sincronizam após reload (Task #1097)', () => {
  test('painel e chat permanecem visíveis sem nova interação', async ({ page }) => {
    test.setTimeout(120_000)

    await authenticateAsRecruiter(page)
    await openJobWizard(page)

    // Estabelece contexto: gera uma resposta da LIA + abre o painel do wizard.
    await sendWizardMessage(page, `Quero criar uma vaga de ${ROLE_TITLE}.`)

    const chatRegion = page.locator(
      '[data-testid="lia-chat"], .lia-chat',
    ).first()
    await expect(chatRegion).toBeVisible({ timeout: 15_000 })

    const beforeChatRow = chatRegion.locator(
      `:text-matches("${ROLE_TITLE.split(' ').slice(0, 3).join(' ')}", "i")`,
    ).last()
    await expect(beforeChatRow).toBeVisible({ timeout: 30_000 })

    // Snapshot de quantas mensagens existem antes do reload (sanity).
    const messageSelector = '[data-testid="lia-chat"] [data-message-id], [data-testid^="chat-message-"], .lia-chat-message'
    const messagesBefore = await page.locator(messageSelector).count()
    expect(
      messagesBefore,
      'Pré-condição: o turno inicial precisa estar registrado no chat.',
    ).toBeGreaterThan(0)

    await page.reload({ waitUntil: 'networkidle' })

    // Após o reload, SEM digitar nada novo:
    //   1. O cargo enviado antes do reload deve continuar visível no chat
    //      (history restaurada via sessionStorage + /conversations/{id}).
    //   2. O painel direito do wizard deve continuar montado (rehydrated via
    //      `wizard_stage` com `resumed=true` que o backend reemite no connect).
    const restoredChatRow = page.locator(
      `:text-matches("${ROLE_TITLE.split(' ').slice(0, 3).join(' ')}", "i")`,
    ).last()
    await expect(
      restoredChatRow,
      'Task #1097: a última mensagem do chat deve ser restaurada após reload — ' +
        'sem isso o recrutador acha que perdeu o contexto.',
    ).toBeVisible({ timeout: 30_000 })

    // Painel do wizard: usamos seletores tolerantes (o componente concreto
    // varia por etapa — intake / jd_enrichment / etc — mas todos vivem dentro
    // de um container marcado como wizard/job-creation).
    const wizardPanel = page.locator(
      [
        '[data-testid="wizard-panel"]',
        '[data-testid="job-creation-panel"]',
        '[data-panel-type="job_creation"]',
        '[data-wizard-stage]',
      ].join(', '),
    ).first()
    await expect(
      wizardPanel,
      'Task #1097: o painel direito do wizard precisa ser re-aberto pelo ' +
        'backend (`wizard_stage` com `resumed=true`) logo após o WS connect.',
    ).toBeVisible({ timeout: 20_000 })
  })
})
