import {
  test,
  expect,
  sendPromptAndWait,
  navigateToChat,
  evalAndAssert,
  takeEvalScreenshot,
} from './eval-helpers';

test.describe('Domain 5: Interviews & Scheduling', () => {
  test('IS-001: Schedule interview', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Agende uma entrevista com o candidato para amanhã às 14h',
    );
    evalAndAssert(testInfo, response, [/agendar/i, /entrevista/i, /agendada/i, /qual candidato/i, /confirmação/i]);
    await takeEvalScreenshot(page, 'IS-001');
  });

  test('IS-002: Reschedule interview', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Reagende a entrevista do candidato para sexta-feira',
    );
    evalAndAssert(testInfo, response, [/reagendar/i, /reagendada/i, /sexta/i, /qual candidato/i]);
    await takeEvalScreenshot(page, 'IS-002');
  });

  test('IS-003: Cancel interview', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Cancele a entrevista do candidato',
    );
    evalAndAssert(testInfo, response, [/cancelar/i, /cancelada/i, /entrevista/i, /qual candidato/i]);
    await takeEvalScreenshot(page, 'IS-003');
  });

  test('IS-004: List today interviews', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Quais entrevistas temos hoje?',
    );
    evalAndAssert(testInfo, response, [/entrevista/i, /hoje/i, /agenda/i, /nenhuma/i]);
    await takeEvalScreenshot(page, 'IS-004');
  });

  test('IS-005: Generate self-scheduling link', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Gere um link de autoagendamento para o candidato',
    );
    evalAndAssert(testInfo, response, [/link/i, /agendamento/i, /gerar/i, /qual candidato/i]);
    await takeEvalScreenshot(page, 'IS-005');
  });
});
