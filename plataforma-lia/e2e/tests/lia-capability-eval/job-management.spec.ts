import {
  test,
  expect,
  sendPromptAndWait,
  navigateToChat,
  evalAndAssert,
  takeEvalScreenshot,
} from './eval-helpers';

test.describe('Domain 1: Job Management', () => {
  test('JM-001: Create job via natural language', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Crie uma vaga de Desenvolvedor Backend Sênior em São Paulo, regime híbrido',
    );
    evalAndAssert(testInfo, response, [/vaga/i, /criar/i, /backend/i, /wizard/i, /formulário/i]);
    await takeEvalScreenshot(page, 'JM-001');
  });

  test('JM-002: List active jobs', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Liste as vagas ativas',
    );
    evalAndAssert(testInfo, response, [/vaga/i, /ativa/i, /aberta/i, /nenhuma/i]);
    await takeEvalScreenshot(page, 'JM-002');
  });

  test('JM-003: Pause a job', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Pause a vaga de Desenvolvedor Backend',
    );
    evalAndAssert(testInfo, response, [/pausar/i, /pausada/i, /confirmar/i, /qual vaga/i]);
    await takeEvalScreenshot(page, 'JM-003');
  });

  test('JM-004: Reopen paused job', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Reabra a vaga que acabamos de pausar',
    );
    evalAndAssert(testInfo, response, [/reabrir/i, /reaberta/i, /qual vaga/i, /confirmar/i]);
    await takeEvalScreenshot(page, 'JM-004');
  });

  test('JM-005: Duplicate a job with new title', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Duplique a vaga de Desenvolvedor Backend com o título Desenvolvedor Fullstack',
    );
    evalAndAssert(testInfo, response, [/duplicar/i, /duplicada/i, /fullstack/i, /qual vaga/i]);
    await takeEvalScreenshot(page, 'JM-005');
  });
});
