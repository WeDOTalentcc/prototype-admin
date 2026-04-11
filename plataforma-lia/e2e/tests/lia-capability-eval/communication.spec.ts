import {
  test,
  expect,
  sendPromptAndWait,
  navigateToChat,
  evalAndAssert,
  takeEvalScreenshot,
} from './eval-helpers';

test.describe('Domain 4: Communication', () => {
  test('CM-001: Send thank-you email to candidate', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Envie um e-mail para o candidato agradecendo pela entrevista',
    );
    evalAndAssert(testInfo, response, [/email/i, /enviar/i, /agradec/i, /qual candidato/i, /confirmação/i]);
    await takeEvalScreenshot(page, 'CM-001', testInfo);
  });

  test('CM-002: Send approval feedback', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Envie feedback de aprovação para o candidato',
    );
    evalAndAssert(testInfo, response, [/feedback/i, /aprovação/i, /enviar/i, /qual candidato/i]);
    await takeEvalScreenshot(page, 'CM-002', testInfo);
  });

  test('CM-003: Send screening invite', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Envie convite de triagem para os candidatos da etapa Novos',
    );
    evalAndAssert(testInfo, response, [/convite/i, /triagem/i, /enviar/i, /candidato/i, /confirmação/i]);
    await takeEvalScreenshot(page, 'CM-003', testInfo);
  });

  test('CM-004: Share candidate profile with manager', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Compartilhe o perfil do candidato com o gestor',
    );
    evalAndAssert(testInfo, response, [/compartilh/i, /perfil/i, /gestor/i, /qual candidato/i]);
    await takeEvalScreenshot(page, 'CM-004', testInfo);
  });

  test('CM-005: Send job progress report', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Envie um relatório de progresso da vaga',
    );
    evalAndAssert(testInfo, response, [/relatório/i, /progresso/i, /vaga/i, /enviar/i, /qual vaga/i]);
    await takeEvalScreenshot(page, 'CM-005', testInfo);
  });
});
