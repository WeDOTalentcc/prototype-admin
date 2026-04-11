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
    await takeEvalScreenshot(page, 'SS-001', testInfo);
  });

  test('SS-002: Suggest candidates for a job', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Sugira candidatos para a vaga de Desenvolvedor Backend Sênior',
    );
    evalAndAssert(testInfo, response, [/sugerir/i, /candidato/i, /vaga/i, /qual vaga/i, /nenhum/i]);
    await takeEvalScreenshot(page, 'SS-002', testInfo);
  });

  test('SS-003: Compare top candidates', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Compare os 3 primeiros candidatos encontrados',
    );
    evalAndAssert(testInfo, response, [/comparar/i, /comparação/i, /candidato/i, /quais/i]);
    await takeEvalScreenshot(page, 'SS-003', testInfo);
  });

  test('SS-004: Rank candidates by score', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Ranqueie os candidatos da vaga por score',
    );
    evalAndAssert(testInfo, response, [/ranking/i, /score/i, /candidato/i, /qual vaga/i]);
    await takeEvalScreenshot(page, 'SS-004', testInfo);
  });

  test('SS-005: Add candidate manually', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Adicione o candidato João Silva, email joao@teste.com, para a vaga de Backend',
    );
    evalAndAssert(testInfo, response, [/cadastr/i, /adicion/i, /candidato/i, /joão/i]);
    await takeEvalScreenshot(page, 'SS-005', testInfo);
  });

  test('SS-006: Search with informal language', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'acha alguém q manja de react e node, pode ser jr',
    );
    evalAndAssert(testInfo, response, [/candidato/i, /react/i, /node/i, /encontr/i, /busca/i]);
    await takeEvalScreenshot(page, 'SS-006', testInfo);
  });

  test('SS-007: Search with location filter', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Busque candidatos de São Paulo com inglês fluente e 5+ anos de experiência',
    );
    evalAndAssert(testInfo, response, [/candidato/i, /são paulo/i, /inglês/i, /experiência/i, /nenhum/i]);
    await takeEvalScreenshot(page, 'SS-007', testInfo);
  });

  test('SS-008: Search with negation', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Busque candidatos que NÃO tenham sido reprovados anteriormente',
    );
    evalAndAssert(testInfo, response, [/candidato/i, /busca/i, /filtro/i, /resultado/i, /nenhum/i]);
    await takeEvalScreenshot(page, 'SS-008', testInfo);
  });

  test('SS-009: Boolean search query', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Busque candidatos com (Python OR Java) AND (AWS OR GCP) e mínimo 3 anos',
    );
    evalAndAssert(testInfo, response, [/candidato/i, /python/i, /java/i, /aws/i, /busca/i]);
    await takeEvalScreenshot(page, 'SS-009', testInfo);
  });

  test('SS-010: Search with implicit context', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Tem alguém bom pra aquela vaga que abri semana passada?',
    );
    evalAndAssert(testInfo, response, [/vaga/i, /candidato/i, /qual vaga/i, /especificar/i]);
    await takeEvalScreenshot(page, 'SS-010', testInfo);
  });
});
