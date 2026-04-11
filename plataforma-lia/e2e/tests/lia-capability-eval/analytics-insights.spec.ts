import {
  test,
  expect,
  sendPromptAndWait,
  navigateToChat,
  evalAndAssert,
  takeEvalScreenshot,
} from './eval-helpers';

test.describe('Domain 7: Analytics & Insights', () => {
  test('AI-001: Generate KPI report', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Gere um relatório de KPIs de recrutamento',
    );
    evalAndAssert(testInfo, response, [/relatório/i, /kpi/i, /recrutamento/i, /métricas/i]);
    await takeEvalScreenshot(page, 'AI-001', testInfo);
  });

  test('AI-002: Job health check', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Faça um health check da vaga',
    );
    evalAndAssert(testInfo, response, [/health/i, /check/i, /vaga/i, /saúde/i, /qual vaga/i]);
    await takeEvalScreenshot(page, 'AI-002', testInfo);
  });

  test('AI-003: General recruitment funnel analysis', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Analise o funil de recrutamento geral',
    );
    evalAndAssert(testInfo, response, [/funil/i, /recrutamento/i, /análise/i, /etapa/i, /conversão/i]);
    await takeEvalScreenshot(page, 'AI-003', testInfo);
  });

  test('AI-004: Average time-to-hire', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Qual o tempo médio de contratação?',
    );
    evalAndAssert(testInfo, response, [/tempo/i, /médio/i, /contratação/i, /dias/i]);
    await takeEvalScreenshot(page, 'AI-004', testInfo);
  });

  test('AI-005: Jobs closed this month', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Quantas vagas fechamos este mês?',
    );
    evalAndAssert(testInfo, response, [/vaga/i, /fechada/i, /mês/i, /nenhuma/i]);
    await takeEvalScreenshot(page, 'AI-005', testInfo);
  });
});
