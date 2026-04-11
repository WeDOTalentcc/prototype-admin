import {
  test,
  expect,
  sendPromptAndWait,
  navigateToChat,
  evalAndAssert,
  takeEvalScreenshot,
} from './eval-helpers';

test.describe('Domain 9: CV Screening & WSI', () => {
  test('CS-001: Start CV screening for a job', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Inicie a triagem de CVs para a vaga de Desenvolvedor Backend',
    );
    evalAndAssert(testInfo, response, [/triagem/i, /cv/i, /vaga/i, /inici/i, /backend/i]);
    await takeEvalScreenshot(page, 'CS-001', testInfo);
  });

  test('CS-002: View screening results', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Mostre os resultados da triagem dos candidatos',
    );
    evalAndAssert(testInfo, response, [/resultado/i, /triagem/i, /candidato/i, /score/i, /nenhum/i]);
    await takeEvalScreenshot(page, 'CS-002', testInfo);
  });

  test('CS-003: Start WSI session', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Inicie uma sessão WSI para o candidato João Silva',
    );
    evalAndAssert(testInfo, response, [/wsi/i, /sessão/i, /candidato/i, /inici/i, /joão/i]);
    await takeEvalScreenshot(page, 'CS-003', testInfo);
  });

  test('CS-004: View WSI score', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Qual o score WSI do candidato?',
    );
    evalAndAssert(testInfo, response, [/wsi/i, /score/i, /candidato/i, /resultado/i, /qual candidato/i]);
    await takeEvalScreenshot(page, 'CS-004', testInfo);
  });

  test('CS-005: Batch screening', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Faça a triagem em lote de todos os candidatos novos da vaga',
    );
    evalAndAssert(testInfo, response, [/triagem/i, /lote/i, /candidato/i, /vaga/i, /inici/i]);
    await takeEvalScreenshot(page, 'CS-005', testInfo);
  });

  test('CS-006: Screening criteria configuration', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Configure os critérios de triagem: Python obrigatório, Docker desejável, 3+ anos de experiência',
    );
    evalAndAssert(testInfo, response, [/critério/i, /triagem/i, /python/i, /configur/i, /obrigatório/i]);
    await takeEvalScreenshot(page, 'CS-006', testInfo);
  });

  test('CS-007: Compare WSI scores', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Compare os scores WSI dos 3 melhores candidatos da vaga',
    );
    evalAndAssert(testInfo, response, [/compar/i, /wsi/i, /score/i, /candidato/i, /qual vaga/i]);
    await takeEvalScreenshot(page, 'CS-007', testInfo);
  });

  test('CS-008: Screening with informal language', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'faz a peneira nos CVs novos aí',
    );
    evalAndAssert(testInfo, response, [/triagem/i, /cv/i, /candidato/i, /qual vaga/i, /inici/i]);
    await takeEvalScreenshot(page, 'CS-008', testInfo);
  });
});
