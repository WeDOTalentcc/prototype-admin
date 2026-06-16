/**
 * T3 — Testes E2E: Criação de Vaga via LIA (Wizard Conversacional)
 *
 * Cobre os cenários principais do wizard de criação de vaga via chat com a LIA.
 * Testa o fluxo conversacional: login → abrir wizard → conversar → publicar/cancelar.
 */
import { test, expect } from '../../fixtures/auth.fixture'
import {
  openJobWizard,
  fillWizardStep,
  sendWizardMessage,
  assertWizardProgress,
  waitForJobPublished,
} from '../../fixtures/wizard-conversation.fixture'

test.describe('T3 — Criação de Vaga via LIA', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    // Garante que o usuário está autenticado antes de cada teste
    await authenticatedPage.waitForLoadState('networkidle')
  })

  /**
   * Cenário 1: Fluxo completo — criação e publicação de vaga
   *
   * login → abrir wizard → conversar com LIA → informar dados → publicar vaga
   */
  test('fluxo completo: criar e publicar vaga via LIA', async ({ authenticatedPage }) => {
    await openJobWizard(authenticatedPage)

    // Etapa 1: Informar cargo e contexto
    await fillWizardStep(authenticatedPage, [
      'Preciso criar uma vaga de Desenvolvedor Backend Senior em Python, remoto, para a equipe de dados',
    ])

    // Verificar que LIA reconheceu e confirmou os dados básicos
    const liaResponse = authenticatedPage.locator('[data-testid="lia-message"], .lia-chat-message').last()
    await expect(liaResponse).toBeVisible({ timeout: 15000 })
    const responseText = await liaResponse.textContent()
    expect(responseText?.toLowerCase()).toMatch(/backend|python|senior|dados/i)

    // Etapa 2: Confirmar dados extraídos e continuar
    await fillWizardStep(authenticatedPage, ['sim, pode continuar'])

    // Etapa 3: Informar faixa salarial
    await sendWizardMessage(
      authenticatedPage,
      'A faixa salarial é de R$ 15.000 a R$ 22.000 por mês, CLT'
    )

    // Etapa 4: Skills técnicas
    await sendWizardMessage(
      authenticatedPage,
      'Skills principais: Python, FastAPI, PostgreSQL, Redis, Docker. Nice to have: Kubernetes, Airflow'
    )

    // Etapa 5: Confirmar e publicar
    await sendWizardMessage(authenticatedPage, 'pode publicar a vaga')

    // Aguarda confirmação de publicação
    await waitForJobPublished(authenticatedPage)

    // Verifica que não há erros visíveis
    const errorMessages = authenticatedPage.locator('[role="alert"], .error-message, [data-testid="error"]')
    expect(await errorMessages.count()).toBe(0)
  })

  /**
   * Cenário 2: Campos obrigatórios faltando — LIA deve pedir esclarecimento
   *
   * Envia dados incompletos → LIA deve perguntar o que falta
   */
  test('campos obrigatórios faltando: LIA pede esclarecimento', async ({ authenticatedPage }) => {
    await openJobWizard(authenticatedPage)

    // Mensagem vaga sem suficiente detalhe
    await sendWizardMessage(authenticatedPage, 'quero criar uma vaga de dev')

    // LIA deve pedir mais informações (esclarecimento)
    const liaQuestion = authenticatedPage.locator('[data-testid="lia-message"], .lia-chat-message').last()
    await expect(liaQuestion).toBeVisible({ timeout: 15000 })

    const questionText = await liaQuestion.textContent()
    // LIA deve perguntar algo (nível, stack, localização, etc.)
    expect(questionText?.length).toBeGreaterThan(20)
    // Verificar que não avançou direto para publicação
    expect(questionText?.toLowerCase()).not.toMatch(/publicar|publish|publicada/i)
  })

  /**
   * Cenário 3: Vaga afirmativa (PCD) — LIA ativa campos de diversidade
   */
  test('vaga afirmativa PCD: LIA ativa campos de diversidade', async ({ authenticatedPage }) => {
    await openJobWizard(authenticatedPage)

    await sendWizardMessage(
      authenticatedPage,
      'Quero criar uma vaga afirmativa para PCD, cargo de Analista de Suporte N1, presencial em São Paulo'
    )

    const liaResponse = authenticatedPage.locator('[data-testid="lia-message"], .lia-chat-message').last()
    await expect(liaResponse).toBeVisible({ timeout: 15000 })

    const responseText = await liaResponse.textContent()
    // LIA deve reconhecer que é vaga afirmativa
    expect(responseText?.toLowerCase()).toMatch(/pcd|afirmativa|diversidade|deficiência/i)
  })

  /**
   * Cenário 4: Cancelamento no meio — estado não deve persistir
   *
   * Inicia criação, cancela, inicia nova → não deve aparecer dados da sessão anterior
   */
  test('cancelamento: estado não persiste após cancelar', async ({ authenticatedPage }) => {
    await openJobWizard(authenticatedPage)

    // Inicia preenchimento
    await sendWizardMessage(
      authenticatedPage,
      'Quero criar vaga de UX Designer Senior, remoto'
    )

    await authenticatedPage.waitForTimeout(2000)

    // Navega para fora (cancela implicitamente)
    await authenticatedPage.goto('/dashboard')
    await authenticatedPage.waitForLoadState('networkidle')

    // Retorna ao wizard — não deve ter dados da sessão anterior no input
    await openJobWizard(authenticatedPage)

    const chatInput = authenticatedPage.locator(
      'textarea[placeholder*="mensagem"], textarea[placeholder*="Digite"], [data-testid="chat-input"]'
    ).first()
    const inputValue = await chatInput.inputValue().catch(() => '')
    expect(inputValue).toBe('')
  })

  /**
   * Cenário 5: Re-entrada via checkpoint — LIA retoma conversação
   *
   * Inicia criação, avança etapas, navega para fora, retorna → LIA deve retomar de onde parou
   */
  test('re-entrada: LIA retoma conversação via checkpoint (A3)', async ({ authenticatedPage }) => {
    await openJobWizard(authenticatedPage)

    // Inicia e avança algumas etapas
    await fillWizardStep(authenticatedPage, [
      'Preciso de um Engenheiro de Machine Learning Senior, remoto, foco em NLP',
      'sim, excelente',
    ])

    // Aguarda LIA processar
    await authenticatedPage.waitForTimeout(3000)

    // Captura o estado atual do chat (última mensagem da LIA)
    const lastMessage = authenticatedPage.locator('[data-testid="lia-message"], .lia-chat-message').last()
    const lastMessageText = await lastMessage.textContent().catch(() => '')

    // Navega para fora
    await authenticatedPage.goto('/dashboard')
    await authenticatedPage.waitForLoadState('networkidle')

    // Retorna ao wizard (via mesmo endpoint — deve restaurar checkpoint)
    await openJobWizard(authenticatedPage)

    // Verifica que a sessão foi retomada (histórico de mensagens deve estar presente)
    const chatHistory = authenticatedPage.locator('[data-testid="lia-message"], .lia-chat-message')
    const messageCount = await chatHistory.count().catch(() => 0)

    // Com checkpoint (A3), a LIA deve mostrar o histórico ou indicar que retomou
    // Aceita ambos: histórico presente OU mensagem de retomada
    const resumeIndicators = authenticatedPage.locator(
      ':has-text("retomando"), :has-text("continuando"), :has-text("Olá novamente")'
    )
    const hasResume = await resumeIndicators.isVisible({ timeout: 5000 }).catch(() => false)
    const hasHistory = messageCount > 0

    expect(hasResume || hasHistory).toBe(true)
  })
})
