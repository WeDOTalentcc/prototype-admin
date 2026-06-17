import {
  test,
  expect,
  sendPromptAndWait,
  navigateToChat,
  evalAndAssert,
  takeEvalScreenshot,
} from './eval-helpers';

test.describe('Domain 13: Recruitment Campaign', () => {
  test('RC-001: Create recruitment campaign', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Crie uma campanha de recrutamento para desenvolvedores Python na região Sul',
    );
    evalAndAssert(testInfo, response, [/campanha/i, /recrutamento/i, /python/i, /criar/i, /região/i]);
    await takeEvalScreenshot(page, 'RC-001', testInfo);
  });

  test('RC-002: List active campaigns', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Quais campanhas de recrutamento estão ativas?',
    );
    evalAndAssert(testInfo, response, [/campanha/i, /ativa/i, /recrutamento/i, /nenhuma/i, /lista/i]);
    await takeEvalScreenshot(page, 'RC-002', testInfo);
  });

  test('RC-003: Campaign performance metrics', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Mostre as métricas de performance da campanha de recrutamento',
    );
    evalAndAssert(testInfo, response, [/métrica/i, /campanha/i, /performance/i, /resultado/i, /qual campanha/i]);
    await takeEvalScreenshot(page, 'RC-003', testInfo);
  });

  test('RC-004: Pause campaign', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Pause a campanha de recrutamento de desenvolvedores',
    );
    evalAndAssert(testInfo, response, [/pausar/i, /campanha/i, /desenvolvedor/i, /confirmação/i]);
    await takeEvalScreenshot(page, 'RC-004', testInfo);
  });

  test('RC-005: Generate job ad text', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Gere um texto de anúncio de vaga para LinkedIn: Analista de Dados Pleno',
    );
    evalAndAssert(testInfo, response, [/anúncio/i, /vaga/i, /linkedin/i, /analista/i, /dados/i]);
    await takeEvalScreenshot(page, 'RC-005', testInfo);
  });

  test('RC-006: Campaign budget tracking', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Qual o orçamento restante da campanha de recrutamento?',
    );
    evalAndAssert(testInfo, response, [/orçamento/i, /campanha/i, /recrutamento/i, /valor/i, /restante/i]);
    await takeEvalScreenshot(page, 'RC-006', testInfo);
  });

  test('RC-007: Campaign A/B test', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Configure um teste A/B para o anúncio da vaga de Backend: versão técnica vs versão cultural',
    );
    evalAndAssert(testInfo, response, [/teste/i, /anúncio/i, /vaga/i, /configur/i, /versão/i]);
    await takeEvalScreenshot(page, 'RC-007', testInfo);
  });

  test('RC-008: Campaign with informal language', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'lança uma campanha pra achar designer UX, pode ser remoto',
    );
    evalAndAssert(testInfo, response, [/campanha/i, /designer/i, /ux/i, /criar/i, /remoto/i]);
    await takeEvalScreenshot(page, 'RC-008', testInfo);
  });
});
