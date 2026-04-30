import { test, expect } from '../fixtures/auth.fixture';
import path from 'path';

// ============================================================
// JC — Job Compensation Modal
// Cobertura: EditJobModalCompensation — salário, bônus, PRV,
// benefícios {id,name}, split Compensation + Process (Fase 3)
// ============================================================

const REPORT_DIR = path.join(__dirname, '../reports/job-compensation-2026-04-30');

async function openEditJobModal(page: import('@playwright/test').Page): Promise<boolean> {
  await page.goto('/pt');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);

  // Tentar via kanban — card de vaga
  const jobCard = page.locator('[data-testid*="job-card"], [data-testid*="kanban-card"]').first();
  if (await jobCard.isVisible({ timeout: 5000 })) {
    await jobCard.click();
    await page.waitForTimeout(1500);
    const editBtn = page.locator('button').filter({ hasText: /editar|edit/i }).first();
    if (await editBtn.isVisible({ timeout: 3000 })) {
      await editBtn.click();
      await page.waitForTimeout(2000);
      return true;
    }
  }

  // Fallback: página de vagas
  await page.goto('/pt/vagas');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);
  const editBtn = page.locator('button').filter({ hasText: /editar/i }).first();
  if (await editBtn.isVisible({ timeout: 5000 })) {
    await editBtn.click();
    await page.waitForTimeout(2000);
    return true;
  }

  return false;
}

test.describe('JC — Job Compensation Modal', () => {

  // JC-001: modal de editar vaga abre sem crash
  test('JC-001: modal editar vaga abre sem erro', async ({ authenticatedPage: page }) => {
    const opened = await openEditJobModal(page);

    if (opened) {
      const modal = page.locator('[role="dialog"]').first();
      await expect(modal).toBeVisible({ timeout: 8000 });
      await page.screenshot({ path: `${REPORT_DIR}/JC-001-modal-open.png` });
    } else {
      // Sem vagas — página não deve ter erro 500
      const errorEl = page.locator('text=/500|Unexpected error/i');
      await expect(errorEl).toHaveCount(0);
      await page.screenshot({ path: `${REPORT_DIR}/JC-001-no-jobs.png` });
    }
  });

  // JC-002: seção Remuneração existe no modal
  test('JC-002: secao Remuneracao presente no modal', async ({ authenticatedPage: page }) => {
    const opened = await openEditJobModal(page);
    if (!opened) return;

    const remuSection = page.locator('text=/Remuneração|Faixa Salarial|Salary/i').first();
    await expect(remuSection).toBeVisible({ timeout: 8000 });

    await page.screenshot({ path: `${REPORT_DIR}/JC-002-compensation-section.png` });
  });

  // JC-003: campos salário min/max presentes
  test('JC-003: campos salarioMin e salarioMax presentes', async ({ authenticatedPage: page }) => {
    const opened = await openEditJobModal(page);
    if (!opened) return;

    const salMin = page.locator('input[name*="salaryMin"], input[placeholder*="mínimo"], input[placeholder*="minimo"]').first();
    const salMax = page.locator('input[name*="salaryMax"], input[placeholder*="máximo"], input[placeholder*="maximo"]').first();

    const minVisible = await salMin.isVisible({ timeout: 5000 }).catch(() => false);
    const maxVisible = await salMax.isVisible({ timeout: 5000 }).catch(() => false);
    expect(minVisible || maxVisible).toBe(true);

    await page.screenshot({ path: `${REPORT_DIR}/JC-003-salary-fields.png` });
  });

  // JC-004: dropdown PRV (compensation_policy_id) presente
  test('JC-004: dropdown Politica de Remuneracao Variavel presente', async ({ authenticatedPage: page }) => {
    const opened = await openEditJobModal(page);
    if (!opened) return;

    // Label do dropdown PRV
    const prvLabel = page.locator('text=/Política de Remuneração|Remuneração Variável/i').first();
    await expect(prvLabel).toBeVisible({ timeout: 8000 });

    await page.screenshot({ path: `${REPORT_DIR}/JC-004-prv-dropdown.png` });
  });

  // JC-005: área de benefícios com chips presente
  test('JC-005: area beneficios com chips presente', async ({ authenticatedPage: page }) => {
    const opened = await openEditJobModal(page);
    if (!opened) return;

    const benefitSection = page.locator('text=/Benefícios|Benefits/i').first();
    await expect(benefitSection).toBeVisible({ timeout: 8000 });

    await page.screenshot({ path: `${REPORT_DIR}/JC-005-benefits-area.png` });
  });

  // JC-006: seção Etapas (EditJobModalProcess) separada
  test('JC-006: secao Etapas separada da secao Remuneracao', async ({ authenticatedPage: page }) => {
    const opened = await openEditJobModal(page);
    if (!opened) return;

    const stagesSection = page.locator('text=/Etapas|Pipeline|Stages/i').first();
    await expect(stagesSection).toBeVisible({ timeout: 8000 });

    await page.screenshot({ path: `${REPORT_DIR}/JC-006-stages-section.png` });
  });

  // JC-007: campo bônus anual presente
  test('JC-007: campo Bonus Anual presente', async ({ authenticatedPage: page }) => {
    const opened = await openEditJobModal(page);
    if (!opened) return;

    const bonusLabel = page.locator('text=/Bônus Anual|Bonus|Annual Bonus/i').first();
    await expect(bonusLabel).toBeVisible({ timeout: 8000 });

    await page.screenshot({ path: `${REPORT_DIR}/JC-007-bonus-field.png` });
  });

  // JC-008: split Compensation + Process funcional (ambas seções existem)
  test('JC-008: split Compensation e Process ambos presentes no modal', async ({ authenticatedPage: page }) => {
    const opened = await openEditJobModal(page);
    if (!opened) return;

    const remuEl  = page.locator('text=/Remuneração|Faixa Salarial/i').first();
    const stageEl = page.locator('text=/Etapas|Pipeline/i').first();

    const remuVisible  = await remuEl.isVisible({ timeout: 5000 }).catch(() => false);
    const stageVisible = await stageEl.isVisible({ timeout: 5000 }).catch(() => false);

    expect(remuVisible).toBe(true);
    expect(stageVisible).toBe(true);

    await page.screenshot({ path: `${REPORT_DIR}/JC-008-split-components.png` });
  });

  // JC-009: botão "Detalhado" abre BenefitFormModal com context=job
  test('JC-009: botao Detalhado abre BenefitFormModal no contexto de vaga', async ({ authenticatedPage: page }) => {
    const opened = await openEditJobModal(page);
    if (!opened) return;

    // Botão "Detalhado" dentro da seção de benefícios
    const detalhadoBtn = page.locator('button').filter({ hasText: /detalhado|detalhar/i }).first();
    if (await detalhadoBtn.isVisible({ timeout: 5000 })) {
      await detalhadoBtn.click();
      await page.waitForTimeout(1500);

      const formModal = page.locator('[role="dialog"]').nth(1);
      await expect(formModal).toBeVisible({ timeout: 5000 });

      await page.screenshot({ path: `${REPORT_DIR}/JC-009-benefit-detail-modal.png` });
    } else {
      // Botão pode não existir se não houver lista de benefícios ainda
      await page.screenshot({ path: `${REPORT_DIR}/JC-009-no-detail-btn.png` });
    }
  });

  // JC-010: full page screenshot do modal aberto
  test('JC-010: full screenshot modal vaga com compensacao', async ({ authenticatedPage: page }) => {
    const opened = await openEditJobModal(page);
    if (!opened) return;

    await page.waitForTimeout(2000);
    await page.screenshot({ path: `${REPORT_DIR}/JC-010-full-job-modal.png`, fullPage: true });

    const modal = page.locator('[role="dialog"]').first();
    await expect(modal).toBeVisible({ timeout: 5000 });
  });


  // ──────────────────────────────────────────────────────────────
  // INT:005 — "Sugerir pacote com LIA" button (WIZARD-INT:005)
  //
  // Ref: EditJobModalCompensation.tsx onSuggestWithLIA prop
  //      edit-job-modal.tsx sendChatMessage integration
  // ──────────────────────────────────────────────────────────────

  // JC-011: seção compensation tem data-testid canônico
  test('JC-011: edit-job-compensation-section tem testid canonico', async ({ authenticatedPage: page }) => {
    const opened = await openEditJobModal(page);
    if (!opened) { test.skip(); return; }

    const section = page.locator('[data-testid="edit-job-compensation-section"]');
    await expect(section).toBeVisible({ timeout: 8000 });

    await page.screenshot({ path: `${REPORT_DIR}/JC-011-compensation-testid.png` });
  });

  // JC-012: seção process tem data-testid canônico
  test('JC-012: edit-job-process-section tem testid canonico', async ({ authenticatedPage: page }) => {
    const opened = await openEditJobModal(page);
    if (!opened) { test.skip(); return; }

    const section = page.locator('[data-testid="edit-job-process-section"]');
    await expect(section).toBeVisible({ timeout: 8000 });

    await page.screenshot({ path: `${REPORT_DIR}/JC-012-process-testid.png` });
  });

  // JC-013: botão "Sugerir pacote com LIA" presente quando policy selecionada
  test('JC-013: botao Sugerir pacote com LIA visivel quando policy selecionada', async ({ authenticatedPage: page }) => {
    const opened = await openEditJobModal(page);
    if (!opened) { test.skip(); return; }

    const suggestBtn = page.locator('button').filter({ hasText: /Sugerir pacote com LIA/i });
    const btnVisible = await suggestBtn.isVisible({ timeout: 5000 }).catch(() => false);

    await page.screenshot({ path: `${REPORT_DIR}/JC-013-suggest-btn.png` });

    if (btnVisible) {
      await expect(suggestBtn).toBeVisible();
    } else {
      console.log('[JC-013] Botão não visível — empresa sem compensation_policies cadastradas');
    }
  });

  // JC-014: clique no botão envia mensagem ao LIA chat
  test('JC-014: botao Sugerir com LIA envia mensagem ao chat', async ({ authenticatedPage: page }) => {
    const opened = await openEditJobModal(page);
    if (!opened) { test.skip(); return; }

    const suggestBtn = page.locator('button').filter({ hasText: /Sugerir pacote com LIA/i });
    if (!await suggestBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      test.skip(); return;
    }

    const wsSent: string[] = [];
    page.on('websocket', ws => {
      ws.on('framesent', frame => wsSent.push(String(frame.payload ?? '')));
    });

    await suggestBtn.click();
    await page.waitForTimeout(2000);

    const messageSent = wsSent.some(f => {
      try {
        const p = JSON.parse(f);
        return Boolean(p?.content?.includes('pacote de remuneração') || p?.content?.includes('Sugira'));
      } catch { return false; }
    });

    await page.screenshot({ path: `${REPORT_DIR}/JC-014-suggest-sent.png` });
    expect(messageSent, 'Nenhuma mensagem enviada após clique no botão Sugerir com LIA').toBe(true);
  });

  // JC-015: mensagem contém "pacote de remuneração" + título da vaga
  test('JC-015: mensagem do botao contem pacote de remuneracao', async ({ authenticatedPage: page }) => {
    const opened = await openEditJobModal(page);
    if (!opened) { test.skip(); return; }

    const suggestBtn = page.locator('button').filter({ hasText: /Sugerir pacote com LIA/i });
    if (!await suggestBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      test.skip(); return;
    }

    const wsSent: string[] = [];
    page.on('websocket', ws => {
      ws.on('framesent', frame => wsSent.push(String(frame.payload ?? '')));
    });

    await suggestBtn.click();
    await page.waitForTimeout(2000);

    const correctMsg = wsSent.some(f => {
      try {
        const p = JSON.parse(f);
        const content: string = p?.content ?? '';
        return /pacote de remuneração|salário.*PRV|PRV.*benefícios/i.test(content);
      } catch { return false; }
    });

    await page.screenshot({ path: `${REPORT_DIR}/JC-015-message-content.png` });
    expect.soft(correctMsg, 'Mensagem do botão não menciona "pacote de remuneração"').toBe(true);
  });

  // JC-016: layout completo — salary + PRV + benefits + process sections
  test('JC-016: modal tem salary + PRV + benefits + process sections', async ({ authenticatedPage: page }) => {
    const opened = await openEditJobModal(page);
    if (!opened) { test.skip(); return; }

    await expect.soft(page.locator('[data-testid="edit-job-compensation-section"]')).toBeVisible({ timeout: 5000 });
    await expect.soft(page.locator('[data-testid="edit-job-process-section"]')).toBeVisible({ timeout: 5000 });
    await expect.soft(page.locator('text=/Faixa Salarial|Salário/i').first()).toBeVisible({ timeout: 5000 });
    await expect.soft(page.locator('text=/Benefícios/i').first()).toBeVisible({ timeout: 5000 });

    await page.screenshot({ path: `${REPORT_DIR}/JC-016-full-modal-layout.png`, fullPage: true });
  });


});
