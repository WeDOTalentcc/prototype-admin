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
    await takeEvalScreenshot(page, 'JM-001', testInfo);
  });

  test('JM-002: List active jobs', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Liste as vagas ativas',
    );
    evalAndAssert(testInfo, response, [/vaga/i, /ativa/i, /aberta/i, /nenhuma/i]);
    await takeEvalScreenshot(page, 'JM-002', testInfo);
  });

  test('JM-003: Pause a job', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Pause a vaga de Desenvolvedor Backend',
    );
    evalAndAssert(testInfo, response, [/pausar/i, /pausada/i, /confirmar/i, /qual vaga/i]);
    await takeEvalScreenshot(page, 'JM-003', testInfo);
  });

  test('JM-004: Reopen paused job', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Reabra a vaga que acabamos de pausar',
    );
    evalAndAssert(testInfo, response, [/reabrir/i, /reaberta/i, /qual vaga/i, /confirmar/i]);
    await takeEvalScreenshot(page, 'JM-004', testInfo);
  });

  test('JM-005: Duplicate a job with new title', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Duplique a vaga de Desenvolvedor Backend com o título Desenvolvedor Fullstack',
    );
    evalAndAssert(testInfo, response, [/duplicar/i, /duplicada/i, /fullstack/i, /qual vaga/i]);
    await takeEvalScreenshot(page, 'JM-005', testInfo);
  });

  test('JM-006: Create job with informal language', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'abre uma vaga de dev frontend jr, remoto, salário até 5k',
    );
    evalAndAssert(testInfo, response, [/vaga/i, /frontend/i, /criar/i, /formulário/i, /remoto/i]);
    await takeEvalScreenshot(page, 'JM-006', testInfo);
  });

  test('JM-007: Close a job', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Feche a vaga de Desenvolvedor Backend, posição preenchida',
    );
    evalAndAssert(testInfo, response, [/fechar/i, /fechada/i, /vaga/i, /confirmar/i]);
    await takeEvalScreenshot(page, 'JM-007', testInfo);
  });

  test('JM-008: Edit job requirements', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Atualize os requisitos da vaga de Backend adicionando experiência com Docker e Kubernetes',
    );
    evalAndAssert(testInfo, response, [/atualiz/i, /requisito/i, /docker/i, /kubernetes/i, /qual vaga/i]);
    await takeEvalScreenshot(page, 'JM-008', testInfo);
  });

  test('JM-009: Create job with abbreviations', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'cria vaga p/ PM sr, SP, presencial, início ASAP',
    );
    evalAndAssert(testInfo, response, [/vaga/i, /product/i, /manager/i, /criar/i, /são paulo/i]);
    await takeEvalScreenshot(page, 'JM-009', testInfo);
  });

  test('JM-010: List jobs with filter negation', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Mostre as vagas que NÃO são remotas',
    );
    evalAndAssert(testInfo, response, [/vaga/i, /presencial/i, /híbrido/i, /nenhuma/i, /resultado/i]);
    await takeEvalScreenshot(page, 'JM-010', testInfo);
  });
});
