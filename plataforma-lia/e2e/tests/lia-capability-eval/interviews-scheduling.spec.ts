import { test, expect } from '@playwright/test';
import {
  navigateToChat,
  sendPromptAndWait,
  assertNoError,
  assertContainsAny,
  assertMinLength,
  assertIsActionResponse,
  takeEvalScreenshot,
} from './eval-helpers';

test.describe('Domain 5: Interviews & Scheduling', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToChat(page);
  });

  test('IS-001: Schedule interview', async ({ page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Agende uma entrevista técnica com o candidato para terça às 14h',
    );
    assertIsActionResponse(response);
    assertContainsAny(response, ['agendar', 'entrevista', 'agendada', 'data', 'confirmação', 'qual candidato']);
    await takeEvalScreenshot(page, 'IS-001');
  });

  test('IS-002: Reschedule interview', async ({ page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Reagende a entrevista do candidato para quinta-feira às 10h',
    );
    assertIsActionResponse(response);
    assertContainsAny(response, ['reagendar', 'reagendada', 'nova data', 'confirmação', 'qual candidato']);
    await takeEvalScreenshot(page, 'IS-002');
  });

  test('IS-003: Cancel interview', async ({ page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Cancele a entrevista do candidato Roberto prevista para amanhã',
    );
    assertIsActionResponse(response);
    assertContainsAny(response, ['cancelar', 'cancelada', 'entrevista', 'confirmação', 'qual candidato']);
    await takeEvalScreenshot(page, 'IS-003');
  });

  test('IS-004: List today interviews', async ({ page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Quais entrevistas tenho agendadas para hoje?',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['entrevista', 'hoje', 'agenda', 'agendada', 'nenhuma']);
    await takeEvalScreenshot(page, 'IS-004');
  });

  test('IS-005: Send interview reminder', async ({ page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Envie um lembrete de entrevista para a candidata Clara',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['lembrete', 'entrevista', 'enviar', 'enviado', 'qual candidato']);
    await takeEvalScreenshot(page, 'IS-005');
  });

  test('IS-006: Generate self-scheduling link', async ({ page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Gere um link de autoagendamento para o candidato Felipe',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['link', 'agendamento', 'gerar', 'gerado', 'qual candidato']);
    await takeEvalScreenshot(page, 'IS-006');
  });

  test('IS-007: Create generic event', async ({ page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Crie um compromisso de reunião de alinhamento com o time de recrutamento para sexta às 15h',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['compromisso', 'reunião', 'criar', 'criado', 'agendado', 'confirmação']);
    await takeEvalScreenshot(page, 'IS-007');
  });
});
