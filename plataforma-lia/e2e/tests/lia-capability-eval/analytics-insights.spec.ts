import {
  test,
  expect,
  sendPromptAndWait,
  assertNoError,
  assertContainsAny,
  assertMinLength,
  takeEvalScreenshot,
} from './eval-helpers';

test.describe('Domain 7: Analytics & Insights', () => {
  test('AI-001: Pipeline performance report', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Gere um relatório de performance do pipeline da última semana',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['relatório', 'pipeline', 'performance', 'semana', 'métricas', 'dados']);
    await takeEvalScreenshot(page, 'AI-001');
  });

  test('AI-002: Recruitment velocity metrics', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Quais são as métricas de velocidade do meu recrutamento?',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['velocidade', 'métricas', 'tempo', 'dias', 'recrutamento', 'dados']);
    await takeEvalScreenshot(page, 'AI-002');
  });

  test('AI-003: Conversion funnel analysis', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Analise o funil de conversão das minhas vagas ativas',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['funil', 'conversão', 'etapa', 'candidatos', 'taxa', 'vagas']);
    await takeEvalScreenshot(page, 'AI-003');
  });

  test('AI-004: Source effectiveness', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'De onde vêm os melhores candidatos? Qual fonte traz mais contratados?',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['fonte', 'origem', 'candidatos', 'contratados', 'melhor', 'dados']);
    await takeEvalScreenshot(page, 'AI-004');
  });

  test('AI-005: Time-to-hire analysis', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Qual o tempo médio de contratação das vagas fechadas nos últimos 3 meses?',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['tempo', 'contratação', 'médio', 'dias', 'meses', 'vagas']);
    await takeEvalScreenshot(page, 'AI-005');
  });

  test('AI-006: Diversity metrics', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Me mostre as métricas de diversidade do nosso pipeline de recrutamento',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['diversidade', 'métricas', 'pipeline', 'candidatos', 'dados']);
    await takeEvalScreenshot(page, 'AI-006');
  });
});
