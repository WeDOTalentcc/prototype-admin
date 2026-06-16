import {
  test,
  expect,
  sendPromptAndWait,
  navigateToChat,
  evalAndAssert,
  takeEvalScreenshot,
} from './eval-helpers';

test.describe('Domain 11: Digital Twin', () => {
  test('DT-001: Create recruiter digital twin', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Crie meu digital twin de recrutador com base no meu histórico de contratações',
    );
    evalAndAssert(testInfo, response, [/digital twin/i, /recrutador/i, /criar/i, /histórico/i, /contratação/i]);
    await takeEvalScreenshot(page, 'DT-001', testInfo);
  });

  test('DT-002: Ask digital twin for recommendation', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'O que meu digital twin recomendaria para melhorar o tempo de contratação?',
    );
    evalAndAssert(testInfo, response, [/digital twin/i, /recomend/i, /tempo/i, /contratação/i, /melhorar/i]);
    await takeEvalScreenshot(page, 'DT-002', testInfo);
  });

  test('DT-003: Digital twin candidate evaluation', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Peça ao digital twin para avaliar o perfil do candidato com base nos padrões de contratação anteriores',
    );
    evalAndAssert(testInfo, response, [/digital twin/i, /avaliar/i, /perfil/i, /candidato/i, /padrão/i]);
    await takeEvalScreenshot(page, 'DT-003', testInfo);
  });

  test('DT-004: Digital twin insights', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Quais insights o digital twin tem sobre meus padrões de avaliação?',
    );
    evalAndAssert(testInfo, response, [/digital twin/i, /insight/i, /padrão/i, /avaliação/i]);
    await takeEvalScreenshot(page, 'DT-004', testInfo);
  });

  test('DT-005: Digital twin bias check', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'O digital twin identifica algum viés nos meus processos seletivos?',
    );
    evalAndAssert(testInfo, response, [/digital twin/i, /viés/i, /processo/i, /seletivo/i, /identificar/i]);
    await takeEvalScreenshot(page, 'DT-005', testInfo);
  });

  test('DT-006: Update digital twin preferences', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Atualize as preferências do meu digital twin: priorizar candidatos com experiência internacional',
    );
    evalAndAssert(testInfo, response, [/digital twin/i, /preferência/i, /atualiz/i, /internacional/i]);
    await takeEvalScreenshot(page, 'DT-006', testInfo);
  });

  test('DT-007: Digital twin with informal language', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'pergunta pro meu clone digital o que ele acha desse candidato',
    );
    evalAndAssert(testInfo, response, [/digital twin/i, /candidato/i, /avaliar/i, /qual candidato/i]);
    await takeEvalScreenshot(page, 'DT-007', testInfo);
  });
});
