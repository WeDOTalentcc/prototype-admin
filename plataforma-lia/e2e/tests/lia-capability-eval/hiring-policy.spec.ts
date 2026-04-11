import {
  test,
  expect,
  sendPromptAndWait,
  navigateToChat,
  evalAndAssert,
  takeEvalScreenshot,
} from './eval-helpers';

test.describe('Domain 8: Hiring Policy', () => {
  test('HP-001: Create hiring policy', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Crie uma política de contratação que exija aprovação do gestor para vagas sênior',
    );
    evalAndAssert(testInfo, response, [/política/i, /contratação/i, /aprovação/i, /gestor/i, /criar/i]);
    await takeEvalScreenshot(page, 'HP-001', testInfo);
  });

  test('HP-002: List active policies', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Quais são as políticas de contratação ativas?',
    );
    evalAndAssert(testInfo, response, [/política/i, /ativa/i, /contratação/i, /nenhuma/i, /lista/i]);
    await takeEvalScreenshot(page, 'HP-002', testInfo);
  });

  test('HP-003: Configure SLA for stages', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Configure um SLA de 5 dias úteis para a etapa de triagem',
    );
    evalAndAssert(testInfo, response, [/sla/i, /triagem/i, /dias/i, /configur/i, /etapa/i]);
    await takeEvalScreenshot(page, 'HP-003', testInfo);
  });

  test('HP-004: Set approval workflow', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Defina que toda proposta salarial acima de R$15.000 precisa de aprovação do diretor',
    );
    evalAndAssert(testInfo, response, [/aprovação/i, /proposta/i, /diretor/i, /salari/i, /configur/i]);
    await takeEvalScreenshot(page, 'HP-004', testInfo);
  });

  test('HP-005: Configure diversity targets', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Configure meta de 40% de diversidade de gênero nas contratações',
    );
    evalAndAssert(testInfo, response, [/diversidade/i, /gênero/i, /meta/i, /configur/i, /contratação/i]);
    await takeEvalScreenshot(page, 'HP-005', testInfo);
  });

  test('HP-006: Policy compliance check', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Verifique se a vaga de Backend está em conformidade com as políticas de contratação',
    );
    evalAndAssert(testInfo, response, [/conformidade/i, /política/i, /vaga/i, /compliance/i, /verificar/i]);
    await takeEvalScreenshot(page, 'HP-006', testInfo);
  });

  test('HP-007: Update policy with informal language', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'muda a regra pra não precisar mais de aprovação em vagas jr',
    );
    evalAndAssert(testInfo, response, [/política/i, /aprovação/i, /atualiz/i, /junior/i, /alterar/i]);
    await takeEvalScreenshot(page, 'HP-007', testInfo);
  });

  test('HP-008: Policy exception request', async ({ authenticatedPage: page }, testInfo) => {
    await navigateToChat(page);
    const { response } = await sendPromptAndWait(
      page,
      'Solicite uma exceção à política de SLA para a vaga urgente de DevOps',
    );
    evalAndAssert(testInfo, response, [/exceção/i, /política/i, /sla/i, /devops/i, /solicit/i]);
    await takeEvalScreenshot(page, 'HP-008', testInfo);
  });
});
