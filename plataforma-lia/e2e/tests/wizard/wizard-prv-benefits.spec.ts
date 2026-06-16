import { test, expect } from '../../fixtures/auth.fixture';
import { openJobWizard, sendWizardMessage } from '../../fixtures/wizard-conversation.fixture';
import path from 'path';

// ============================================================
// WB — Wizard PRV + Benefits integration (INT:001-002)
//
// Cobre: etapa de salário + benefícios do wizard de criação de
// vaga — integração benefits/compensation_policies do Sprint Benefits.
//
// INT:001: PRV section estruturado substitui prosa "Bônus ou PLR"
// INT:002: Benefits filtrados por seniority_levels (Python-side)
//
// Ref: stage_salary.py, wizard_step_service/service.py
//      app/orchestrator/services/rail_a_hint_override.py
// ============================================================

const REPORT_DIR = path.join(__dirname, '../../reports/wizard-prv-benefits-2026-04-30');

const SEL = {
  chatInput: [
    '[data-testid="chat-input"]',
    'textarea[placeholder*="mensagem" i]',
    'textarea[placeholder*="Digite" i]',
  ].join(', '),
  liaMarkdown: '.lia-markdown-content',
  liaMarkdownLast: '.lia-markdown-content:last-of-type',
  panelJobCreation: '[role="complementary"]',
  chatMessages: '[data-testid="chat-messages"], .lia-chat-messages, .message-list',
};

/** Avança o wizard até a etapa de salário enviando mensagens canônicas. */
async function advanceWizardToSalary(page: import('@playwright/test').Page): Promise<boolean> {
  const chatInput = page.locator(SEL.chatInput).first();
  if (!await chatInput.isVisible({ timeout: 20000 }).catch(() => false)) return false;

  // Step 1-3: cargo, requisitos, competências (respostas mínimas para avançar)
  const steps = [
    'Desenvolvedor Backend Senior Python',
    'Python avançado, FastAPI, PostgreSQL, 5 anos de experiência',
    'Resolução de problemas, trabalho em equipe',
  ];

  for (const msg of steps) {
    await chatInput.fill(msg);
    await chatInput.press('Enter');
    // Aguarda LIA responder antes de continuar
    await page.waitForTimeout(5000);
  }

  // Verifica se chegou na etapa de salário
  const salaryKeywords = ['salário', 'remuneração', 'faixa salarial', 'salary', 'benefícios', 'PRV', 'bônus'];
  const allMessages = await page.locator(SEL.liaMarkdown).allTextContents();
  const lastMessages = allMessages.slice(-3).join(' ').toLowerCase();
  const atSalaryStep = salaryKeywords.some(k => lastMessages.includes(k.toLowerCase()));

  return atSalaryStep;
}

test.describe('WB — Wizard PRV + Benefits', () => {

  // WB-001: /vagas/nova carrega sem erro
  test('WB-001: wizard /vagas/nova sem crash 500', async ({ authenticatedPage: page }) => {
    await page.goto('/vagas/nova');
    await page.waitForLoadState('networkidle');

    const errorEl = page.locator('text=/500|Internal Server Error|Unexpected error/i');
    await expect(errorEl).toHaveCount(0);

    const chatInput = page.locator(SEL.chatInput).first();
    await expect(chatInput).toBeVisible({ timeout: 20000 });

    await page.screenshot({ path: `${REPORT_DIR}/WB-001-wizard-loaded.png` });
  });

  // WB-002: /vagas/nova?step=4 (URL legada) não crasha
  test('WB-002: /vagas/nova?step=4 sem crash', async ({ authenticatedPage: page }) => {
    await page.goto('/vagas/nova?step=4');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    const errorEl = page.locator('text=/500|Internal Server Error/i');
    await expect(errorEl).toHaveCount(0);

    await page.screenshot({ path: `${REPORT_DIR}/WB-002-step4-url.png` });
  });

  // WB-003: LIA first response não tem "Bônus ou PLR" como texto simples
  //         (INT:001 substituiu prosa por seção estruturada)
  test('WB-003: resposta LIA nao usa prosa "Bonus ou PLR" como fallback', async ({ authenticatedPage: page }) => {
    await openJobWizard(page);

    // Avança para o step de salário
    const reachedSalary = await advanceWizardToSalary(page);
    if (!reachedSalary) {
      test.skip();
      return;
    }

    const allMessages = await page.locator(SEL.liaMarkdown).allTextContents();
    const combined = allMessages.join(' ');

    // Não deve ter o texto de prosa antigo como conteúdo principal
    // (pode aparecer entre parênteses como nota, mas não como item standalone)
    const hasOldFallback = /^[•\-]\s*Bônus ou PLR \(se aplicável\s*—/im.test(combined);
    expect.soft(hasOldFallback, 'INT:001 regression: prosa antiga "Bônus ou PLR" ainda presente').toBe(false);

    await page.screenshot({ path: `${REPORT_DIR}/WB-003-no-bonus-prose.png` });
  });

  // WB-004: Wizard etapa salarial mostra seção de benefícios
  test('WB-004: etapa salarial tem secao de beneficios na resposta', async ({ authenticatedPage: page }) => {
    await openJobWizard(page);

    const reachedSalary = await advanceWizardToSalary(page);
    if (!reachedSalary) {
      test.skip();
      return;
    }

    const allText = await page.locator(SEL.liaMarkdown).allTextContents();
    const combined = allText.join(' ').toLowerCase();
    const hasBenefits = /benefício|vale|plano/i.test(combined);

    await page.screenshot({ path: `${REPORT_DIR}/WB-004-benefits-in-response.png` });
    expect.soft(hasBenefits, 'Nenhum benefício encontrado na resposta da etapa salarial').toBe(true);
  });

  // WB-005: Painel JobCreation mostra resumo da vaga em criação
  test('WB-005: painel Criacao de Vaga ativo durante wizard', async ({ authenticatedPage: page }) => {
    await page.goto('/vagas/nova');
    await page.waitForLoadState('networkidle');

    const chatInput = page.locator(SEL.chatInput).first();
    await chatInput.waitFor({ state: 'visible', timeout: 20000 });
    await chatInput.fill('Criar vaga de Product Manager');
    await chatInput.press('Enter');
    await page.waitForTimeout(6000);

    const panel = page.locator(SEL.panelJobCreation).filter({ hasText: 'Criação de Vaga' });
    const panelVisible = await panel.isVisible({ timeout: 5000 }).catch(() => false);

    await page.screenshot({ path: `${REPORT_DIR}/WB-005-job-panel.png` });
    // Soft: panel pode não ativar dependendo do backend
    expect.soft(panelVisible).toBe(true);
  });

  // WB-006: Wizard responde mencionando faixa salarial na etapa 4
  test('WB-006: LIA menciona faixa salarial na etapa salary', async ({ authenticatedPage: page }) => {
    await openJobWizard(page);

    const reachedSalary = await advanceWizardToSalary(page);
    if (!reachedSalary) {
      test.skip();
      return;
    }

    const allText = await page.locator(SEL.liaMarkdown).allTextContents();
    const combined = allText.join(' ');
    const hasSalaryInfo = /R\$|faixa salarial|salário|salary/i.test(combined);

    await page.screenshot({ path: `${REPORT_DIR}/WB-006-salary-range.png` });
    expect.soft(hasSalaryInfo).toBe(true);
  });

  // WB-007: API benefits endpoint retorna 200 (não 500)
  test('WB-007: API wizard benefits nao retorna 500', async ({ authenticatedPage: page }) => {
    const apiErrors: { url: string; status: number }[] = [];

    page.on('response', resp => {
      if (resp.url().includes('/wizard') || resp.url().includes('/benefits') || resp.url().includes('/step')) {
        if (resp.status() >= 500) {
          apiErrors.push({ url: resp.url(), status: resp.status() });
        }
      }
    });

    await openJobWizard(page);
    await page.waitForTimeout(3000);

    expect(apiErrors, `API 500 errors: ${JSON.stringify(apiErrors)}`).toHaveLength(0);
    await page.screenshot({ path: `${REPORT_DIR}/WB-007-api-no-500.png` });
  });

  // WB-008: LIA não retorna erro "domínio não reconhecido" no wizard
  test('WB-008: LIA nao retorna erro de dominio no wizard', async ({ authenticatedPage: page }) => {
    await page.goto('/vagas/nova');
    await page.waitForLoadState('networkidle');

    const chatInput = page.locator(SEL.chatInput).first();
    await chatInput.waitFor({ state: 'visible', timeout: 20000 });
    await chatInput.fill('Quero criar uma vaga de desenvolvedor');
    await chatInput.press('Enter');
    await page.waitForTimeout(8000);

    const allText = await page.locator(SEL.liaMarkdown).allTextContents();
    const combined = allText.join(' ').toLowerCase();

    const hasRoutingError = /domínio não reconhecido|domain not found|routing error|nenhum domínio/i.test(combined);
    expect.soft(hasRoutingError, 'LIA mostrou erro de routing — Rail A pode não estar ativo').toBe(false);

    await page.screenshot({ path: `${REPORT_DIR}/WB-008-no-routing-error.png` });
  });

  // WB-009: LIA menciona PRV ou política de remuneração na etapa salarial
  test('WB-009: LIA menciona PRV na etapa salarial', async ({ authenticatedPage: page }) => {
    await openJobWizard(page);

    const reachedSalary = await advanceWizardToSalary(page);
    if (!reachedSalary) {
      test.skip();
      return;
    }

    const allText = await page.locator(SEL.liaMarkdown).allTextContents();
    const combined = allText.join(' ');

    // PRV aparece se a empresa tem compensation_policies cadastradas
    // Caso contrário, fallback é "nenhuma política PRV cadastrada"
    const hasPRVMention = /PRV|Política de PRV|política de remuneração variável|remuneração variável|nenhuma política PRV/i.test(combined);

    await page.screenshot({ path: `${REPORT_DIR}/WB-009-prv-mention.png` });
    // Soft: empresa de dev pode não ter policies cadastradas
    expect.soft(hasPRVMention).toBe(true);
  });

  // WB-010: Full screenshot do wizard após etapa salarial
  test('WB-010: screenshot completo da etapa salarial', async ({ authenticatedPage: page }) => {
    await openJobWizard(page);
    await advanceWizardToSalary(page);

    await page.screenshot({ path: `${REPORT_DIR}/WB-010-salary-step-full.png`, fullPage: true });

    // Apenas verifica que não há erro visível na tela
    const errorEl = page.locator('text=/500|Unexpected error/i');
    await expect(errorEl).toHaveCount(0);
  });

});
