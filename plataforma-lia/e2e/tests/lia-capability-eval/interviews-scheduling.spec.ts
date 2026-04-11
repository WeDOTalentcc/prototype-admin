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
    await takeEvalScreenshot(page, 'IS-001', testInfo);
  });

  test('IS-002: Reschedule interview', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Reagende a entrevista do candidato para sexta-feira',
    );
    evalAndAssert(testInfo, response, [/reagendar/i, /reagendada/i, /sexta/i, /qual candidato/i]);
    await takeEvalScreenshot(page, 'IS-002', testInfo);
  });

  test('IS-003: Cancel interview', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Cancele a entrevista do candidato',
    );
    evalAndAssert(testInfo, response, [/cancelar/i, /cancelada/i, /entrevista/i, /qual candidato/i]);
    await takeEvalScreenshot(page, 'IS-003', testInfo);
  });

  test('IS-004: List today interviews', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Quais entrevistas temos hoje?',
    );
    evalAndAssert(testInfo, response, [/entrevista/i, /hoje/i, /agenda/i, /nenhuma/i]);
    await takeEvalScreenshot(page, 'IS-004', testInfo);
  });

  test('IS-005: Generate self-scheduling link', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Gere um link de autoagendamento para o candidato',
    );
    evalAndAssert(testInfo, response, [/link/i, /agendamento/i, /gerar/i, /qual candidato/i]);
    await takeEvalScreenshot(page, 'IS-005', testInfo);
  });

  test('IS-006: Schedule panel interview', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Agende uma entrevista em painel com 3 entrevistadores para o candidato',
    );
    evalAndAssert(testInfo, response, [/painel/i, /entrevista/i, /entrevistador/i, /agendar/i, /qual candidato/i]);
    await takeEvalScreenshot(page, 'IS-006', testInfo);
  });

  test('IS-007: Check interviewer availability', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Verifique a disponibilidade dos entrevistadores para esta semana',
    );
    evalAndAssert(testInfo, response, [/disponibilidade/i, /entrevistador/i, /semana/i, /horário/i]);
    await takeEvalScreenshot(page, 'IS-007', testInfo);
  });

  test('IS-008: Schedule with informal language', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'marca uma call com o candidato pra 2a feira de manhã',
    );
    evalAndAssert(testInfo, response, [/agendar/i, /entrevista/i, /segunda/i, /manhã/i, /qual candidato/i]);
    await takeEvalScreenshot(page, 'IS-008', testInfo);
  });

  test('IS-009: List overdue interviews', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Quais entrevistas estão atrasadas ou sem feedback registrado?',
    );
    evalAndAssert(testInfo, response, [/entrevista/i, /atrasad/i, /feedback/i, /nenhum/i, /pendente/i]);
    await takeEvalScreenshot(page, 'IS-009', testInfo);
  });

  test('IS-010: Record interview feedback', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Registre feedback da entrevista: candidato demonstrou boa comunicação, mas falta experiência em liderança',
    );
    evalAndAssert(testInfo, response, [/feedback/i, /registr/i, /entrevista/i, /qual candidato/i, /comunicação/i]);
    await takeEvalScreenshot(page, 'IS-010', testInfo);
  });
});
