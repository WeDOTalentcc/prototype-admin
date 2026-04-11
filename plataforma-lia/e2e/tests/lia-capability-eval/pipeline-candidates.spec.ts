import {
  test,
  expect,
  sendPromptAndWait,
  navigateToChat,
  evalAndAssert,
  takeEvalScreenshot,
} from './eval-helpers';

test.describe('Domain 3: Pipeline & Candidate Management', () => {
  test('PC-001: Move candidate to interview stage', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Mova o candidato para a etapa de Entrevista',
    );
    evalAndAssert(testInfo, response, [/mover/i, /movido/i, /etapa/i, /entrevista/i, /qual candidato/i]);
    await takeEvalScreenshot(page, 'PC-001', testInfo);
  });

  test('PC-002: List candidates in screening stage', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Quais candidatos estão na etapa de Triagem?',
    );
    evalAndAssert(testInfo, response, [/candidato/i, /triagem/i, /etapa/i, /nenhum/i]);
    await takeEvalScreenshot(page, 'PC-002', testInfo);
  });

  test('PC-003: Analyze candidate profile', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Analise o perfil do candidato para a vaga de Backend',
    );
    evalAndAssert(testInfo, response, [/análise/i, /perfil/i, /score/i, /qual candidato/i]);
    await takeEvalScreenshot(page, 'PC-003', testInfo);
  });

  test('PC-004: Show conversion funnel', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Mostre o funil de conversão da vaga',
    );
    evalAndAssert(testInfo, response, [/funil/i, /conversão/i, /etapa/i, /candidatos/i, /qual vaga/i]);
    await takeEvalScreenshot(page, 'PC-004', testInfo);
  });

  test('PC-005: Stale candidates check', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Quais candidatos estão parados há mais de 7 dias?',
    );
    evalAndAssert(testInfo, response, [/candidato/i, /dia/i, /parado/i, /nenhum/i]);
    await takeEvalScreenshot(page, 'PC-005', testInfo);
  });

  test('PC-006: Reject candidate with reason', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Reprove o candidato por falta de experiência na stack',
    );
    evalAndAssert(testInfo, response, [/reprov/i, /candidato/i, /motivo/i, /qual candidato/i, /confirmar/i]);
    await takeEvalScreenshot(page, 'PC-006', testInfo);
  });

  test('PC-007: Batch move candidates', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Mova todos os candidatos aprovados na triagem para a etapa de entrevista técnica',
    );
    evalAndAssert(testInfo, response, [/mover/i, /candidato/i, /entrevista/i, /confirmar/i, /etapa/i]);
    await takeEvalScreenshot(page, 'PC-007', testInfo);
  });

  test('PC-008: Move with informal language', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'joga o candidato pra próxima fase aí',
    );
    evalAndAssert(testInfo, response, [/mover/i, /etapa/i, /candidato/i, /qual/i, /próxim/i]);
    await takeEvalScreenshot(page, 'PC-008', testInfo);
  });

  test('PC-009: Pipeline summary by stage', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Quantos candidatos temos em cada etapa do pipeline?',
    );
    evalAndAssert(testInfo, response, [/candidato/i, /etapa/i, /pipeline/i, /total/i, /nenhum/i]);
    await takeEvalScreenshot(page, 'PC-009', testInfo);
  });

  test('PC-010: Add tag to candidate', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Adicione a tag "destaque" ao candidato',
    );
    evalAndAssert(testInfo, response, [/tag/i, /adicion/i, /candidato/i, /destaque/i, /qual candidato/i]);
    await takeEvalScreenshot(page, 'PC-010', testInfo);
  });
});
