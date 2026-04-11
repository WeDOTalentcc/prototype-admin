import {
  test,
  expect,
  sendPromptAndWait,
  navigateToChat,
  evalAndAssert,
  takeEvalScreenshot,
} from './eval-helpers';

test.describe('Domain 6: Automation & Productivity', () => {
  test('AP-001: Create task', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Crie uma tarefa: revisar CVs da vaga até sexta',
    );
    evalAndAssert(testInfo, response, [/tarefa/i, /criar/i, /criada/i, /revisar/i]);
    await takeEvalScreenshot(page, 'AP-001', testInfo);
  });

  test('AP-002: Create note about candidate', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Adicione uma nota sobre o candidato: excelente comunicação',
    );
    evalAndAssert(testInfo, response, [/nota/i, /adicion/i, /comunicação/i, /candidato/i]);
    await takeEvalScreenshot(page, 'AP-002', testInfo);
  });

  test('AP-003: Daily briefing', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Gere meu briefing do dia',
    );
    evalAndAssert(testInfo, response, [/briefing/i, /agenda/i, /hoje/i, /resumo/i]);
    await takeEvalScreenshot(page, 'AP-003', testInfo);
  });

  test('AP-004: Create automation rule', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Crie uma automação: quando candidato entrar em Entrevista, envie WhatsApp',
    );
    evalAndAssert(testInfo, response, [/automação/i, /whatsapp/i, /entrevista/i, /criar/i]);
    await takeEvalScreenshot(page, 'AP-004', testInfo);
  });

  test('AP-005: Check proactive pipeline alerts', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Verifique alertas proativos do pipeline',
    );
    evalAndAssert(testInfo, response, [/alerta/i, /pipeline/i, /proativ/i, /nenhum/i]);
    await takeEvalScreenshot(page, 'AP-005', testInfo);
  });

  test('AP-006: Weekly recap', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Gere um resumo semanal das minhas atividades de recrutamento',
    );
    evalAndAssert(testInfo, response, [/resumo/i, /semanal/i, /atividade/i, /recrutamento/i]);
    await takeEvalScreenshot(page, 'AP-006', testInfo);
  });

  test('AP-007: Create reminder', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Me lembre de dar retorno para o candidato João até amanhã às 17h',
    );
    evalAndAssert(testInfo, response, [/lembrete/i, /candidato/i, /retorno/i, /amanhã/i, /criado/i]);
    await takeEvalScreenshot(page, 'AP-007', testInfo);
  });

  test('AP-008: List pending tasks', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Quais são minhas tarefas pendentes?',
    );
    evalAndAssert(testInfo, response, [/tarefa/i, /pendente/i, /nenhuma/i, /lista/i]);
    await takeEvalScreenshot(page, 'AP-008', testInfo);
  });

  test('AP-009: Create automation with informal language', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'configura pra mandar email automático quando alguém for reprovado',
    );
    evalAndAssert(testInfo, response, [/automação/i, /email/i, /reprov/i, /configurar/i, /criar/i]);
    await takeEvalScreenshot(page, 'AP-009', testInfo);
  });

  test('AP-010: Productivity metrics', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Mostre minhas métricas de produtividade desta semana',
    );
    evalAndAssert(testInfo, response, [/métrica/i, /produtividade/i, /semana/i, /atividade/i]);
    await takeEvalScreenshot(page, 'AP-010', testInfo);
  });
});
