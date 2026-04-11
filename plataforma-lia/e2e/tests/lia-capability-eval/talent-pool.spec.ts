import {
  test,
  expect,
  sendPromptAndWait,
  navigateToChat,
  evalAndAssert,
  takeEvalScreenshot,
} from './eval-helpers';

test.describe('Domain 10: Talent Pool', () => {
  test('TP-001: Create talent pool', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Crie um banco de talentos para desenvolvedores fullstack',
    );
    evalAndAssert(testInfo, response, [/banco/i, /talento/i, /criar/i, /fullstack/i, /pool/i]);
    await takeEvalScreenshot(page, 'TP-001', testInfo);
  });

  test('TP-002: Add candidate to talent pool', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Adicione o candidato ao banco de talentos de Backend',
    );
    evalAndAssert(testInfo, response, [/adicion/i, /candidato/i, /banco/i, /talento/i, /qual candidato/i]);
    await takeEvalScreenshot(page, 'TP-002', testInfo);
  });

  test('TP-003: Search talent pool', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Busque no banco de talentos candidatos com experiência em React e TypeScript',
    );
    evalAndAssert(testInfo, response, [/banco/i, /talento/i, /react/i, /typescript/i, /candidato/i, /nenhum/i]);
    await takeEvalScreenshot(page, 'TP-003', testInfo);
  });

  test('TP-004: List talent pools', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Quais bancos de talentos temos cadastrados?',
    );
    evalAndAssert(testInfo, response, [/banco/i, /talento/i, /lista/i, /nenhum/i, /cadastr/i]);
    await takeEvalScreenshot(page, 'TP-004', testInfo);
  });

  test('TP-005: Re-engage talent pool candidates', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Envie uma mensagem de re-engajamento para os candidatos do banco de talentos de Backend',
    );
    evalAndAssert(testInfo, response, [/mensagem/i, /banco/i, /talento/i, /candidato/i, /enviar/i]);
    await takeEvalScreenshot(page, 'TP-005', testInfo);
  });

  test('TP-006: Talent pool statistics', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Quantos candidatos temos no banco de talentos e há quanto tempo estão lá?',
    );
    evalAndAssert(testInfo, response, [/candidato/i, /banco/i, /talento/i, /tempo/i, /total/i]);
    await takeEvalScreenshot(page, 'TP-006', testInfo);
  });

  test('TP-007: Match talent pool to new job', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Encontre candidatos do banco de talentos que sejam compatíveis com a nova vaga de DevOps',
    );
    evalAndAssert(testInfo, response, [/candidato/i, /banco/i, /talento/i, /compatível/i, /devops/i, /vaga/i]);
    await takeEvalScreenshot(page, 'TP-007', testInfo);
  });
});
