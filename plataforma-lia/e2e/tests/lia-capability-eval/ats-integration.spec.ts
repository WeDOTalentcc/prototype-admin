import {
  test,
  expect,
  sendPromptAndWait,
  navigateToChat,
  evalAndAssert,
  takeEvalScreenshot,
} from './eval-helpers';

test.describe('Domain 12: ATS Integration', () => {
  test('AT-001: Check ATS connection status', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Verifique o status da integração com o ATS',
    );
    evalAndAssert(testInfo, response, [/ats/i, /integração/i, /status/i, /conect/i, /configurar/i]);
    await takeEvalScreenshot(page, 'AT-001', testInfo);
  });

  test('AT-002: Sync jobs from ATS', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Sincronize as vagas do ATS com a plataforma',
    );
    evalAndAssert(testInfo, response, [/sincroniz/i, /vaga/i, /ats/i, /importar/i, /configur/i]);
    await takeEvalScreenshot(page, 'AT-002', testInfo);
  });

  test('AT-003: Import candidates from ATS', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Importe os candidatos da vaga de Backend do Gupy para cá',
    );
    evalAndAssert(testInfo, response, [/importar/i, /candidato/i, /gupy/i, /vaga/i, /backend/i]);
    await takeEvalScreenshot(page, 'AT-003', testInfo);
  });

  test('AT-004: Export candidate to ATS', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Exporte o candidato aprovado para o ATS',
    );
    evalAndAssert(testInfo, response, [/exportar/i, /candidato/i, /ats/i, /qual candidato/i, /aprovad/i]);
    await takeEvalScreenshot(page, 'AT-004', testInfo);
  });

  test('AT-005: ATS sync history', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Mostre o histórico de sincronizações com o ATS',
    );
    evalAndAssert(testInfo, response, [/histórico/i, /sincroniz/i, /ats/i, /log/i, /nenhum/i]);
    await takeEvalScreenshot(page, 'AT-005', testInfo);
  });

  test('AT-006: Configure ATS mapping', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Configure o mapeamento de campos entre a LIA e o Pandapé',
    );
    evalAndAssert(testInfo, response, [/mapeamento/i, /campo/i, /pandapé/i, /configur/i, /integração/i]);
    await takeEvalScreenshot(page, 'AT-006', testInfo);
  });

  test('AT-007: ATS with informal language', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'puxa os candidatos do gupy pra cá',
    );
    evalAndAssert(testInfo, response, [/importar/i, /candidato/i, /gupy/i, /sincroniz/i, /qual vaga/i]);
    await takeEvalScreenshot(page, 'AT-007', testInfo);
  });
});
