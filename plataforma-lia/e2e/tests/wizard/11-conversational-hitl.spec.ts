/**
 * E2E — T2 (Task #1085) — wizard conversational HITL gate (jd_enrichment)
 *
 * Reproduz o bug original: wizard repetia "preciso de aprovação" 4× ignorando
 * variações naturais de aprovação ("manda bala", "tá liberado", "fica bom").
 *
 * Cenários:
 *   C1 — "manda bala" → wizard NÃO repete pedido de aprovação; avança para Big Five.
 *   C2 — "calma, refaz só skills" → wizard reconhece feedback (não trata como aprovação).
 *   C3 — pergunta natural ("o salário tá baixo?") → wizard responde sem avançar erradamente.
 *
 * Pré-requisito: `LIA_WIZARD_LLM_GATES=true` no backend (workflow `lia-backend`)
 * + `ANTHROPIC_API_KEY` configurado. Em CI, o teste é skipped se a flag estiver OFF.
 */
import { test, expect } from '@playwright/test';

const FLAG_ENV = process.env.LIA_WIZARD_LLM_GATES?.toLowerCase();
const FLAG_ON = FLAG_ENV === '1' || FLAG_ENV === 'true' || FLAG_ENV === 'on';

test.describe('Wizard HITL conversacional (T2)', () => {
  test.skip(!FLAG_ON, 'LIA_WIZARD_LLM_GATES OFF — gate LLM não ativo neste ambiente');

  test.beforeEach(async ({ page }) => {
    await page.goto('/pt/chat');
    await page.waitForLoadState('networkidle');
  });

  test('C1 — "manda bala" é reconhecido como aprovação e avança para Big Five', async ({ page }) => {
    const chatInput = page.getByTestId('chat-input').or(page.locator('textarea').first());
    await chatInput.fill('quero criar uma vaga de Engenheiro Backend Pleno em São Paulo, remoto, faixa 12-18k');
    await chatInput.press('Enter');

    // Aguarda o wizard chegar no stage jd_enrichment (até 60s para enrichment Gemini).
    await expect(
      page.locator('[data-testid*="wizard-jd"], [data-wizard-stage="jd_enrichment"]')
        .first(),
    ).toBeVisible({ timeout: 60_000 });

    // Aprova com forma coloquial.
    await chatInput.fill('manda bala');
    await chatInput.press('Enter');

    // Anti-padrão: NÃO pode aparecer 2× "preciso de aprovação" depois do "manda bala".
    await page.waitForTimeout(8_000); // dá tempo do gate LLM responder
    const messages = await page.locator('[data-testid="chat-message"], [role="article"]').allTextContents();
    const lastFew = messages.slice(-4).join(' | ').toLowerCase();
    expect(lastFew).not.toMatch(/preciso de aprova[cç][aã]o.*preciso de aprova[cç][aã]o/);
    expect(lastFew).not.toMatch(/voc[eê] aprovou\?.*voc[eê] aprovou\?/);

    // Avançou: o painel já mostra Big Five OU a LIA confirma o avanço.
    const hasBigFive = await page.locator('[data-wizard-stage="bigfive"], [data-testid*="bigfive"]').count();
    const hasAdvanceMessage = lastFew.includes('big five') || lastFew.includes('próximo bloco') || lastFew.includes('aprovado');
    expect(hasBigFive > 0 || hasAdvanceMessage).toBeTruthy();
  });

  test('C2 — "calma, refaz só skills" NÃO é tratado como aprovação', async ({ page }) => {
    const chatInput = page.getByTestId('chat-input').or(page.locator('textarea').first());
    await chatInput.fill('quero criar uma vaga de Analista Financeiro Pleno');
    await chatInput.press('Enter');
    await expect(
      page.locator('[data-testid*="wizard-jd"], [data-wizard-stage="jd_enrichment"]').first(),
    ).toBeVisible({ timeout: 60_000 });

    await chatInput.fill('calma, refaz só a parte de skills');
    await chatInput.press('Enter');
    await page.waitForTimeout(8_000);

    const messages = await page.locator('[data-testid="chat-message"], [role="article"]').allTextContents();
    const last = (messages[messages.length - 1] || '').toLowerCase();

    // Reconheceu como ajuste, não como aprovação.
    expect(last).not.toContain('big five');
    expect(last).not.toContain('aprovado!');
    // Idealmente menciona "skills" ou "ajustar" ou "revisar".
    expect(last).toMatch(/skills|ajust|revis|mudar|refazer/);
  });

  test('C3 — pergunta sobre salário não é confundida com aprovação', async ({ page }) => {
    const chatInput = page.getByTestId('chat-input').or(page.locator('textarea').first());
    await chatInput.fill('vaga de Coordenador de Marketing remoto');
    await chatInput.press('Enter');
    await expect(
      page.locator('[data-testid*="wizard-jd"], [data-wizard-stage="jd_enrichment"]').first(),
    ).toBeVisible({ timeout: 60_000 });

    await chatInput.fill('o salário tá baixo pra mercado?');
    await chatInput.press('Enter');
    await page.waitForTimeout(8_000);

    const messages = await page.locator('[data-testid="chat-message"], [role="article"]').allTextContents();
    const last = (messages[messages.length - 1] || '').toLowerCase();

    expect(last).not.toContain('big five');
    expect(last).not.toContain('próximo bloco');
    // Deve responder à pergunta sobre salário.
    expect(last).toMatch(/sal[áa]rio|benchmark|faixa|mercado/);
  });
});
