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
});
