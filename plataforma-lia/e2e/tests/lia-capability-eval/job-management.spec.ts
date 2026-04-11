import {
  test,
  expect,
  sendPromptAndWait,
  assertNoError,
  assertContainsAny,
  assertMinLength,
  assertIsActionResponse,
  takeEvalScreenshot,
} from './eval-helpers';

test.describe('Domain 1: Job Management', () => {
  test('JM-001: Create job via natural language', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Quero criar uma vaga de Desenvolvedor Full Stack Sênior, remoto, em São Paulo',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['vaga', 'criar', 'wizard', 'full stack', 'formulário', 'preencher']);
    await takeEvalScreenshot(page, 'JM-001');
  });

  test('JM-002: List open jobs', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Quais vagas estão abertas agora?',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['vaga', 'ativa', 'aberta', 'abertas', 'nenhuma']);
    await takeEvalScreenshot(page, 'JM-002');
  });

  test('JM-003: Pause a job', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Pause a vaga de Engenheiro de Dados',
    );
    assertIsActionResponse(response);
    assertContainsAny(response, ['pausar', 'pausada', 'pausa', 'confirmação', 'confirmar', 'qual vaga']);
    await takeEvalScreenshot(page, 'JM-003');
  });

  test('JM-004: Close a job', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Feche a vaga de Product Manager que já foi preenchida',
    );
    assertIsActionResponse(response);
    assertContainsAny(response, ['fechar', 'fechada', 'encerrar', 'confirmação', 'confirmar', 'qual vaga']);
    await takeEvalScreenshot(page, 'JM-004');
  });

  test('JM-005: Duplicate a job', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Duplique a vaga de Analista de Dados para outra região',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['duplicar', 'duplicada', 'cópia', 'nova vaga', 'qual vaga']);
    await takeEvalScreenshot(page, 'JM-005');
  });

  test('JM-006: Reopen a closed job', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Reabra a vaga de UX Designer que foi fechada no mês passado',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['reabrir', 'reaberta', 'reativada', 'qual vaga', 'confirmar']);
    await takeEvalScreenshot(page, 'JM-006');
  });

  test('JM-007: Set job as urgent', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Classifique a vaga de DevOps como urgente, precisamos preencher logo',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['urgente', 'prioridade', 'classificar', 'qual vaga']);
    await takeEvalScreenshot(page, 'JM-007');
  });
});
