import {
  test,
  expect,
  sendPromptAndWait,
  assertNoError,
  assertContainsAny,
  assertMinLength,
  assertIsActionResponse,
  takeEvalScreenshot,
} from './eval-helpers';

test.describe('Domain 4: Communication', () => {
  test('CM-001: Send email to candidate', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Envie um email para o candidato informando que ele foi aprovado na primeira fase',
    );
    assertIsActionResponse(response);
    assertContainsAny(response, ['email', 'enviar', 'mensagem', 'confirmação', 'qual candidato', 'assunto']);
    await takeEvalScreenshot(page, 'CM-001');
  });

  test('CM-002: Send WhatsApp message', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Envie uma mensagem WhatsApp para a candidata pedindo documentos',
    );
    assertIsActionResponse(response);
    assertContainsAny(response, ['whatsapp', 'mensagem', 'enviar', 'confirmação', 'qual candidato']);
    await takeEvalScreenshot(page, 'CM-002');
  });

  test('CM-003: Send feedback to candidate', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Envie feedback de rejeição gentil para o candidato Marcos',
    );
    assertIsActionResponse(response);
    assertContainsAny(response, ['feedback', 'enviar', 'rejeição', 'confirmação', 'qual candidato']);
    await takeEvalScreenshot(page, 'CM-003');
  });

  test('CM-004: Send screening invite', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Envie convite de triagem para os novos candidatos da vaga de QA',
    );
    assertIsActionResponse(response);
    assertContainsAny(response, ['convite', 'triagem', 'enviar', 'confirmação', 'qual candidato']);
    await takeEvalScreenshot(page, 'CM-004');
  });

  test('CM-005: Draft professional email', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Redija um email profissional convidando o candidato para entrevista presencial na próxima terça',
    );
    assertNoError(response);
    assertMinLength(response, 50);
    assertContainsAny(response, ['email', 'entrevista', 'terça', 'convid', 'mensagem']);
    await takeEvalScreenshot(page, 'CM-005');
  });
});
