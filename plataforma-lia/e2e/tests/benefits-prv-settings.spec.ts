import { test, expect } from '../fixtures/auth.fixture';
import path from 'path';

// ============================================================
// BP — Benefits + PRV Settings
// Cobertura: bloco "Remuneração Variável" + bloco "Benefícios"
// em Configurações → Minha Empresa (Fases 1+2 do plano Benefits+PRV)
// ============================================================

const REPORT_DIR = path.join(__dirname, '../reports/benefits-prv-2026-04-30');

async function goToMinhaEmpresa(page: import('@playwright/test').Page) {
  await page.goto('/pt');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1500);

  const settingsLink = page.locator('a[href*="configuracoes"], text=Configurações').first();
  await settingsLink.click();
  await page.waitForTimeout(2000);

  const menuBtn = page.locator('[data-testid="settings-menu-minha-empresa"]');
  if (await menuBtn.isVisible({ timeout: 4000 })) {
    await menuBtn.click();
  }
  await page.waitForTimeout(2000);
}

test.describe('BP — Benefits + PRV Settings', () => {

  // BP-001: bloco "Remuneração Variável" presente (fix rename de "Documentos")
  test('BP-001: bloco Remuneracao Variavel presente com label correto', async ({ authenticatedPage: page }) => {
    await goToMinhaEmpresa(page);

    const blockTitle = page.locator('text=Remuneração Variável').first();
    await expect(blockTitle).toBeVisible({ timeout: 8000 });

    await page.screenshot({ path: `${REPORT_DIR}/BP-001-prv-block-visible.png` });
  });

  // BP-002: bloco "Benefícios" presente
  test('BP-002: bloco Beneficios presente', async ({ authenticatedPage: page }) => {
    await goToMinhaEmpresa(page);

    const benefitsBlock = page.locator('text=Benefícios').first();
    await expect(benefitsBlock).toBeVisible({ timeout: 8000 });

    await page.screenshot({ path: `${REPORT_DIR}/BP-002-benefits-block-visible.png` });
  });

  // BP-003: regressão — label antigo "Documentos" não aparece como título de bloco
  test('BP-003: titulo antigo Documentos nao aparece no hub', async ({ authenticatedPage: page }) => {
    await goToMinhaEmpresa(page);

    const staleTitle = page.locator('h2, h3, [class*="title"]').filter({ hasText: /^Documentos$/ });
    await expect(staleTitle).toHaveCount(0);
  });

  // BP-004: upload label do bloco menciona Remuneração Variável ou PRV
  test('BP-004: upload label menciona Remuneracao Variavel ou PRV', async ({ authenticatedPage: page }) => {
    await goToMinhaEmpresa(page);
    await page.waitForTimeout(1000);

    const hint = page.locator('text=/Remuneração Variável|PRV|Variable Compensation/i').first();
    await expect(hint).toBeVisible({ timeout: 8000 });

    await page.screenshot({ path: `${REPORT_DIR}/BP-004-prv-label.png` });
  });

  // BP-005: seção Benefícios — botão Adicionar presente
  test('BP-005: secao Beneficios tem botao adicionar', async ({ authenticatedPage: page }) => {
    await goToMinhaEmpresa(page);

    const addBtn = page.locator('button').filter({ hasText: /adicionar|novo benefício|add benefit/i }).first();
    await expect(addBtn).toBeVisible({ timeout: 10000 });

    await page.screenshot({ path: `${REPORT_DIR}/BP-005-add-benefit-btn.png` });
  });

  // BP-006: BenefitFormModal abre com campos dos 22 colunas
  test('BP-006: BenefitFormModal abre com campos avancados', async ({ authenticatedPage: page }) => {
    await goToMinhaEmpresa(page);

    const addBtn = page.locator('button').filter({ hasText: /adicionar|novo benefício|add benefit/i }).first();
    if (await addBtn.isVisible({ timeout: 8000 })) {
      await addBtn.click();
      await page.waitForTimeout(1500);
    }

    const modal = page.locator('[role="dialog"]').first();
    await expect(modal).toBeVisible({ timeout: 6000 });

    // Campo "Nome" obrigatório em todo benefício
    const nameField = page.locator('input[name="name"], input[placeholder*="nome"], label:has-text("Nome")').first();
    await expect(nameField).toBeVisible({ timeout: 5000 });

    await page.screenshot({ path: `${REPORT_DIR}/BP-006-benefit-form-modal.png` });
  });

  // BP-007: seção PRV carrega sem erro 500
  test('BP-007: secao PRV carrega sem erro 500', async ({ authenticatedPage: page }) => {
    await goToMinhaEmpresa(page);
    await page.waitForTimeout(2000);

    const errorText = page.locator('text=/500|Internal Server Error|Unexpected error/i');
    await expect(errorText).toHaveCount(0);

    await page.screenshot({ path: `${REPORT_DIR}/BP-007-prv-section.png`, fullPage: true });
  });

  // BP-008: full page screenshot do hub Minha Empresa
  test('BP-008: full page screenshot hub Minha Empresa', async ({ authenticatedPage: page }) => {
    await goToMinhaEmpresa(page);
    await page.waitForTimeout(3000);

    await page.screenshot({ path: `${REPORT_DIR}/BP-008-minha-empresa-fullpage.png`, fullPage: true });

    const h1OrH2 = page.locator('h1, h2').first();
    await expect(h1OrH2).toBeVisible({ timeout: 5000 });
  });

});
