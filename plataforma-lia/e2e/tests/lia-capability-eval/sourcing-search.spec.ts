import {
  test,
  expect,
  sendPromptAndWait,
  navigateToChat,
  evalAndAssert,
  takeEvalScreenshot,
} from './eval-helpers';

test.describe('Domain 2: Sourcing & Search', () => {
  test('SS-001: Search candidates by skill', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Busque candidatos com experiência em Python e machine learning',
    );
    evalAndAssert(testInfo, response, [/candidato/i, /python/i, /resultado/i, /encontrado/i, /nenhum/i]);
    await takeEvalScreenshot(page, 'SS-001');
  });

  test('SS-002: Suggest candidates for a job', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Sugira candidatos para a vaga de Desenvolvedor Backend Sênior',
    );
    evalAndAssert(testInfo, response, [/sugerir/i, /candidato/i, /vaga/i, /qual vaga/i, /nenhum/i]);
    await takeEvalScreenshot(page, 'SS-002');
  });

  test('SS-003: Compare top candidates', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Compare os 3 primeiros candidatos encontrados',
    );
    evalAndAssert(testInfo, response, [/comparar/i, /comparação/i, /candidato/i, /quais/i]);
    await takeEvalScreenshot(page, 'SS-003');
  });

  test('SS-004: Rank candidates by score', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Ranqueie os candidatos da vaga por score',
    );
    evalAndAssert(testInfo, response, [/ranking/i, /score/i, /candidato/i, /qual vaga/i]);
    await takeEvalScreenshot(page, 'SS-004');
  });

  test('SS-005: Add candidate manually', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Adicione o candidato João Silva, email joao@teste.com, para a vaga de Backend',
    );
    evalAndAssert(testInfo, response, [/cadastr/i, /adicion/i, /candidato/i, /joão/i]);
    await takeEvalScreenshot(page, 'SS-005');
  });
});
