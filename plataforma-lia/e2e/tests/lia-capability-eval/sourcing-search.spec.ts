import {
  test,
  expect,
  sendPromptAndWait,
  assertNoError,
  assertContainsAny,
  assertMinLength,
  takeEvalScreenshot,
} from './eval-helpers';

test.describe('Domain 2: Sourcing & Search', () => {
  test('SS-001: Search candidates by skill', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Busque candidatos com experiência em Python e Machine Learning',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['candidato', 'resultado', 'encontrado', 'busca', 'python', 'nenhum']);
    await takeEvalScreenshot(page, 'SS-001');
  });

  test('SS-002: Search candidates by location', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Buscar candidatos de São Paulo com experiência em React',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['candidato', 'são paulo', 'encontrado', 'resultado', 'nenhum']);
    await takeEvalScreenshot(page, 'SS-002');
  });

  test('SS-003: Rank candidates for a job', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Rankear os candidatos da vaga de Engenheiro de Software',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['ranking', 'score', 'candidato', 'top', 'vaga', 'qual vaga']);
    await takeEvalScreenshot(page, 'SS-003');
  });

  test('SS-004: Compare two candidates', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Compare os candidatos João e Maria para a vaga de Tech Lead',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['comparação', 'comparar', 'candidato', 'perfil', 'quais candidatos']);
    await takeEvalScreenshot(page, 'SS-004');
  });

  test('SS-005: Tag candidates', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Taguear os candidatos da vaga de Backend como "alto potencial"',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['tag', 'taguear', 'etiqueta', 'aplicada', 'quais candidatos']);
    await takeEvalScreenshot(page, 'SS-005');
  });

  test('SS-006: Suggest candidates for a job', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Sugira candidatos do banco de talentos para a vaga de Product Designer',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['sugerir', 'sugerido', 'candidato', 'talento', 'vaga', 'qual vaga']);
    await takeEvalScreenshot(page, 'SS-006');
  });

  test('SS-007: Add candidate manually', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Cadastre o candidato Carlos Silva, email carlos@email.com, para a vaga de Frontend',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['cadastr', 'adicion', 'candidato', 'carlos', 'criado']);
    await takeEvalScreenshot(page, 'SS-007');
  });
});
