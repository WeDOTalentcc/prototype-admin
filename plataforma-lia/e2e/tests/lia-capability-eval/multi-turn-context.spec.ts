import {
  test,
  expect,
  sendPromptAndWait,
  sendMultiTurnConversation,
  navigateToChat,
  classifyResponse,
  takeEvalScreenshot,
} from './eval-helpers';

test.describe('Cross-Domain: Multi-Turn Context Retention', () => {
  test.setTimeout(120_000);

  test('MT-001: Job creation then candidate search (3 turns)', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const result = await sendMultiTurnConversation(page, [
      'Crie uma vaga de Engenheiro de Dados Sênior em São Paulo',
      'Agora busque candidatos para essa vaga que acabei de criar',
      'Compare os 3 melhores candidatos encontrados',
    ]);
    testInfo.annotations.push({ type: 'eval_classification', description: result.turns[result.turns.length - 1].classification });
    testInfo.annotations.push({ type: 'eval_context_retained', description: result.contextRetained ? 'YES' : 'NO' });
    testInfo.annotations.push({ type: 'eval_response', description: result.turns[result.turns.length - 1].response.substring(0, 500) });
    expect(result.turns.length).toBe(3);
    for (const turn of result.turns) {
      expect(turn.classification).not.toBe('SEM RESPOSTA');
    }
    expect(result.contextRetained).toBe(true);
    await takeEvalScreenshot(page, 'MT-001', testInfo);
  });

  test('MT-002: Candidate screening then pipeline move (3 turns)', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const result = await sendMultiTurnConversation(page, [
      'Mostre os candidatos da vaga de Backend na etapa de Triagem',
      'Avalie o primeiro candidato da lista',
      'Mova esse candidato para a etapa de Entrevista',
    ]);
    testInfo.annotations.push({ type: 'eval_classification', description: result.turns[result.turns.length - 1].classification });
    testInfo.annotations.push({ type: 'eval_context_retained', description: result.contextRetained ? 'YES' : 'NO' });
    testInfo.annotations.push({ type: 'eval_response', description: result.turns[result.turns.length - 1].response.substring(0, 500) });
    for (const turn of result.turns) {
      expect(turn.classification).not.toBe('SEM RESPOSTA');
    }
    expect(result.contextRetained).toBe(true);
    await takeEvalScreenshot(page, 'MT-002', testInfo);
  });

  test('MT-003: Schedule interview then communicate (4 turns)', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const result = await sendMultiTurnConversation(page, [
      'Agende uma entrevista com o candidato para amanhã às 15h',
      'Quem é o entrevistador dessa entrevista?',
      'Envie um email de confirmação para o candidato',
      'Adicione uma nota sobre essa entrevista',
    ]);
    testInfo.annotations.push({ type: 'eval_classification', description: result.turns[result.turns.length - 1].classification });
    testInfo.annotations.push({ type: 'eval_context_retained', description: result.contextRetained ? 'YES' : 'NO' });
    testInfo.annotations.push({ type: 'eval_response', description: result.turns[result.turns.length - 1].response.substring(0, 500) });
    for (const turn of result.turns) {
      expect(turn.classification).not.toBe('SEM RESPOSTA');
    }
    expect(result.contextRetained).toBe(true);
    await takeEvalScreenshot(page, 'MT-003', testInfo);
  });

  test('MT-004: Analytics deep dive (4 turns)', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const result = await sendMultiTurnConversation(page, [
      'Gere um relatório de KPIs de recrutamento deste mês',
      'Detalhe o tempo médio de contratação por vaga',
      'Quais vagas estão com SLA estourado?',
      'Sugira ações para melhorar esses indicadores',
    ]);
    testInfo.annotations.push({ type: 'eval_classification', description: result.turns[result.turns.length - 1].classification });
    testInfo.annotations.push({ type: 'eval_context_retained', description: result.contextRetained ? 'YES' : 'NO' });
    testInfo.annotations.push({ type: 'eval_response', description: result.turns[result.turns.length - 1].response.substring(0, 500) });
    for (const turn of result.turns) {
      expect(turn.classification).not.toBe('SEM RESPOSTA');
    }
    expect(result.contextRetained).toBe(true);
    await takeEvalScreenshot(page, 'MT-004', testInfo);
  });

  test('MT-005: Full hiring workflow (5 turns)', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const result = await sendMultiTurnConversation(page, [
      'Crie uma vaga de Product Manager em Curitiba',
      'Busque candidatos para essa vaga',
      'Agende entrevista com o primeiro candidato para segunda-feira',
      'Envie email de confirmação para ele',
      'Gere um resumo do status dessa vaga',
    ]);
    testInfo.annotations.push({ type: 'eval_classification', description: result.turns[result.turns.length - 1].classification });
    testInfo.annotations.push({ type: 'eval_context_retained', description: result.contextRetained ? 'YES' : 'NO' });
    testInfo.annotations.push({ type: 'eval_response', description: result.turns[result.turns.length - 1].response.substring(0, 500) });
    for (const turn of result.turns) {
      expect(turn.classification).not.toBe('SEM RESPOSTA');
    }
    expect(result.contextRetained).toBe(true);
    await takeEvalScreenshot(page, 'MT-005', testInfo);
  });

  test('MT-006: Pronoun resolution across turns (3 turns)', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const result = await sendMultiTurnConversation(page, [
      'Mostre a vaga de Desenvolvedor Backend',
      'Quantos candidatos ela tem?',
      'Mova os aprovados dela para a próxima etapa',
    ]);
    testInfo.annotations.push({ type: 'eval_classification', description: result.turns[result.turns.length - 1].classification });
    testInfo.annotations.push({ type: 'eval_context_retained', description: result.contextRetained ? 'YES' : 'NO' });
    testInfo.annotations.push({ type: 'eval_response', description: result.turns[result.turns.length - 1].response.substring(0, 500) });
    for (const turn of result.turns) {
      expect(turn.classification).not.toBe('SEM RESPOSTA');
    }
    expect(result.contextRetained).toBe(true);
    await takeEvalScreenshot(page, 'MT-006', testInfo);
  });

  test('MT-007: Context switch between domains (4 turns)', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const result = await sendMultiTurnConversation(page, [
      'Quantas vagas ativas temos?',
      'Gere meu briefing do dia',
      'Voltando às vagas, qual tem mais candidatos?',
      'Mostre o funil dessa vaga',
    ]);
    testInfo.annotations.push({ type: 'eval_classification', description: result.turns[result.turns.length - 1].classification });
    testInfo.annotations.push({ type: 'eval_context_retained', description: result.contextRetained ? 'YES' : 'NO' });
    testInfo.annotations.push({ type: 'eval_response', description: result.turns[result.turns.length - 1].response.substring(0, 500) });
    for (const turn of result.turns) {
      expect(turn.classification).not.toBe('SEM RESPOSTA');
    }
    expect(result.contextRetained).toBe(true);
    await takeEvalScreenshot(page, 'MT-007', testInfo);
  });

  test('MT-008: Correction mid-conversation (3 turns)', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const result = await sendMultiTurnConversation(page, [
      'Crie uma vaga de Desenvolvedor Frontend em Belo Horizonte',
      'Na verdade, quero que seja em São Paulo, não BH',
      'Confirme a criação com a localização corrigida',
    ]);
    testInfo.annotations.push({ type: 'eval_classification', description: result.turns[result.turns.length - 1].classification });
    testInfo.annotations.push({ type: 'eval_context_retained', description: result.contextRetained ? 'YES' : 'NO' });
    testInfo.annotations.push({ type: 'eval_response', description: result.turns[result.turns.length - 1].response.substring(0, 500) });
    const lastResponse = result.turns[result.turns.length - 1].response.toLowerCase();
    const corrected = lastResponse.includes('são paulo') || !lastResponse.includes('belo horizonte');
    testInfo.annotations.push({ type: 'eval_correction_applied', description: corrected ? 'YES' : 'NO' });
    for (const turn of result.turns) {
      expect(turn.classification).not.toBe('SEM RESPOSTA');
    }
    expect(result.contextRetained).toBe(true);
    expect(corrected).toBe(true);
    await takeEvalScreenshot(page, 'MT-008', testInfo);
  });
});
