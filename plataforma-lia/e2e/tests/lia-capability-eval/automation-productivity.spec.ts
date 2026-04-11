import {
  test,
  expect,
  sendPromptAndWait,
  assertNoError,
  assertContainsAny,
  assertMinLength,
  takeEvalScreenshot,
} from './eval-helpers';

test.describe('Domain 6: Automation & Productivity', () => {
  test('AP-001: Create task', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Crie uma tarefa para revisar os currículos novos até sexta-feira',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['tarefa', 'criar', 'criada', 'revisar', 'currículo']);
    await takeEvalScreenshot(page, 'AP-001');
  });

  test('AP-002: Create reminder', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Me lembre de ligar para o candidato amanhã às 10h',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['lembrete', 'lembrar', 'criado', 'amanhã', 'ligar']);
    await takeEvalScreenshot(page, 'AP-002');
  });

  test('AP-003: Create note', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Anote que o candidato mencionou interesse em trabalho remoto e pretensão de 15k CLT',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['nota', 'anotar', 'anotado', 'salvo', 'registrado']);
    await takeEvalScreenshot(page, 'AP-003');
  });

  test('AP-004: Daily briefing', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Me dê um resumo da minha agenda de hoje',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['agenda', 'resumo', 'hoje', 'entrevista', 'tarefa', 'nenhum', 'nada']);
    await takeEvalScreenshot(page, 'AP-004');
  });

  test('AP-005: Multi-step task creation', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Crie três tarefas: 1) enviar feedback para reprovados, 2) atualizar JD da vaga de Backend, 3) alinhar com hiring manager',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['tarefa', 'criar', 'criada', 'feedback', 'backend', 'alinhar']);
    await takeEvalScreenshot(page, 'AP-005');
  });

  test('AP-006: Create note with candidate context', async ({ evalPage: page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Crie uma nota sobre o candidato: "Excelente comunicação, boa liderança técnica, fit cultural alto"',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['nota', 'criada', 'salva', 'registrada', 'candidato']);
    await takeEvalScreenshot(page, 'AP-006');
  });
});
