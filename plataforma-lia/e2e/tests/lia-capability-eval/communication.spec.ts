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

  test('CM-006: Send rejection email with empathy', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Envie um email de reprovação empático para o candidato, mantendo a porta aberta para futuras vagas',
    );
    evalAndAssert(testInfo, response, [/email/i, /reprovação/i, /candidato/i, /enviar/i, /futuras/i]);
    await takeEvalScreenshot(page, 'CM-006', testInfo);
  });

  test('CM-007: Send WhatsApp message', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Manda um WhatsApp pro candidato confirmando a entrevista de amanhã',
    );
    evalAndAssert(testInfo, response, [/whatsapp/i, /enviar/i, /entrevista/i, /candidato/i, /confirmação/i]);
    await takeEvalScreenshot(page, 'CM-007', testInfo);
  });

  test('CM-008: Bulk communication', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Envie uma mensagem para todos os candidatos da vaga informando sobre atraso no processo',
    );
    evalAndAssert(testInfo, response, [/mensagem/i, /candidato/i, /enviar/i, /todos/i, /qual vaga/i]);
    await takeEvalScreenshot(page, 'CM-008', testInfo);
  });

  test('CM-009: Draft offer letter', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Prepare uma carta proposta para o candidato aprovado',
    );
    evalAndAssert(testInfo, response, [/proposta/i, /carta/i, /candidato/i, /oferta/i, /qual candidato/i]);
    await takeEvalScreenshot(page, 'CM-009', testInfo);
  });

  test('CM-010: Communication with implicit context', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'avisa ele que mudou o horário',
    );
    evalAndAssert(testInfo, response, [/qual/i, /candidato/i, /horário/i, /especificar/i, /informar/i]);
    await takeEvalScreenshot(page, 'CM-010', testInfo);
  });
});
