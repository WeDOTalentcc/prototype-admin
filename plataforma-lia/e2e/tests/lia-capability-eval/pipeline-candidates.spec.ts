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

test.describe('Domain 3: Pipeline & Candidate Management', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToChat(page);
  });

  test('PC-001: Move candidate to next stage', async ({ page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Mova o candidato João para a etapa de Entrevista Técnica',
    );
    assertIsActionResponse(response);
    assertContainsAny(response, ['mover', 'movido', 'etapa', 'entrevista', 'confirmação', 'qual candidato']);
    await takeEvalScreenshot(page, 'PC-001');
  });

  test('PC-002: Reject candidate with reason', async ({ page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Reprove o candidato Pedro por falta de experiência técnica',
    );
    assertIsActionResponse(response);
    assertContainsAny(response, ['reprovar', 'reprovado', 'rejeitar', 'confirmação', 'qual candidato']);
    await takeEvalScreenshot(page, 'PC-002');
  });

  test('PC-003: Approve candidate', async ({ page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Aprove a candidata Ana para a próxima fase',
    );
    assertIsActionResponse(response);
    assertContainsAny(response, ['aprovar', 'aprovado', 'aprovada', 'próxima', 'qual candidato']);
    await takeEvalScreenshot(page, 'PC-003');
  });

  test('PC-004: Update candidate field', async ({ page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Atualize o telefone do candidato Lucas para (11) 99999-1234',
    );
    assertIsActionResponse(response);
    assertContainsAny(response, ['atualizar', 'atualizado', 'telefone', 'campo', 'qual candidato']);
    await takeEvalScreenshot(page, 'PC-004');
  });

  test('PC-005: Start screening', async ({ page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Inicie a triagem dos candidatos da vaga de Data Engineer',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['triagem', 'iniciar', 'iniciada', 'screening', 'candidatos']);
    await takeEvalScreenshot(page, 'PC-005');
  });

  test('PC-006: Analyze candidate profile', async ({ page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Faça uma análise detalhada do perfil da candidata Mariana para a vaga de PM',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['análise', 'perfil', 'score', 'analisar', 'candidat', 'qual candidato']);
    await takeEvalScreenshot(page, 'PC-006');
  });

  test('PC-007: Batch move candidates', async ({ page }) => {
    const { response } = await sendPromptAndWait(
      page,
      'Mova todos os candidatos da etapa Triagem para Entrevista na vaga de Backend',
    );
    assertNoError(response);
    assertMinLength(response);
    assertContainsAny(response, ['mover', 'movido', 'candidatos', 'lote', 'etapa', 'confirmar']);
    await takeEvalScreenshot(page, 'PC-007');
  });
});
