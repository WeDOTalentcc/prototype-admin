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

  test('C4 — "ainda não te passei a descrição" + paste invalida cache e re-enriquece', async ({ page }) => {
    // Reproduz o bug exato relatado: recrutador inicia com pedido vago,
    // wizard tenta enriquecer com pouca info, recrutador então cola a JD
    // real. Esperado: provide_new_content → jd_enriched=null → re-enrichment
    // com o conteúdo novo (NÃO repete o prompt de aprovação canned).
    const chatInput = page.getByTestId('chat-input').or(page.locator('textarea').first());
    await chatInput.fill('queria abrir uma vaga nova');
    await chatInput.press('Enter');
    await expect(
      page.locator('[data-testid*="wizard-jd"], [data-wizard-stage="jd_enrichment"]').first(),
    ).toBeVisible({ timeout: 60_000 });

    // Snapshot inicial das mensagens para comparar.
    const initialCount = await page.locator('[data-testid="chat-message"], [role="article"]').count();

    // Recrutador admite que não passou a JD e cola o conteúdo real.
    const realJD = `ainda não te passei a descrição certinha, segue:

Engenheira de Dados Sênior — Stack: Python, Spark, AWS, Snowflake, dbt.
Atuação: squad de produto, mentoria a juniores, OKRs trimestrais.
Modelo: Remoto BR. Faixa: 18-25k CLT.
Diferenciais: experiência com data mesh e dbt cloud.`;
    await chatInput.fill(realJD);
    await chatInput.press('Enter');

    // Aguarda re-enrichment (até 30s — Gemini call real).
    await page.waitForTimeout(15_000);

    const messages = await page.locator('[data-testid="chat-message"], [role="article"]').allTextContents();
    const afterPaste = messages.slice(initialCount).join(' | ').toLowerCase();

    // Anti-padrão #1: NÃO repete o canned "preciso de aprovação" que era
    // o bug original.
    const cannedRepeats = (afterPaste.match(/preciso de aprova[cç][aã]o/g) || []).length;
    expect(cannedRepeats).toBeLessThanOrEqual(1);

    // Anti-padrão #2: NÃO trata como aprovação prematura.
    expect(afterPaste).not.toMatch(/aprovado!.*big five/);

    // Sinal positivo: reconheceu o conteúdo novo (palavras-chave da JD
    // colada devem aparecer no enrichment ou na resposta).
    expect(afterPaste).toMatch(/snowflake|dbt|spark|engenheir[ao] de dados|re-?enriqu/);
  });

  test('C5 — competency: "vamos com o compacto" seleciona modo sem re-perguntar', async ({ page }) => {
    // T4 (Task #1086) — wizard avança rápido até o stage `competency`
    // (escolha do modo de triagem WSI) e o gate LLM-based interpreta
    // "vamos com o compacto" como `select_compact` → screening_mode="compact".
    const chatInput = page.getByTestId('chat-input').or(page.locator('textarea').first());
    // Caminho rápido até competency: JD → approve → bigfive → salary → competency.
    await chatInput.fill('quero criar uma vaga de Analista de Dados Pleno em SP, remoto, faixa 10-15k. Stack: SQL, Python, dbt.');
    await chatInput.press('Enter');
    await expect(
      page.locator('[data-testid*="wizard-jd"], [data-wizard-stage="jd_enrichment"]').first(),
    ).toBeVisible({ timeout: 60_000 });
    await chatInput.fill('manda bala');
    await chatInput.press('Enter');
    // Aguarda chegar em competency (até 60s — passa por bigfive/salary).
    await expect(
      page.locator('[data-wizard-stage="competency"], [data-testid*="competency"], [data-testid*="screening-mode"]').first(),
    ).toBeVisible({ timeout: 60_000 });

    await chatInput.fill('vamos com o compacto');
    await chatInput.press('Enter');
    await page.waitForTimeout(8_000);

    const messages = await page.locator('[data-testid="chat-message"], [role="article"]').allTextContents();
    const lastFew = messages.slice(-4).join(' | ').toLowerCase();
    // Anti-padrão: NÃO repete pergunta do modo após escolha clara.
    expect(lastFew).not.toMatch(/compacto.*ou.*completo.*compacto.*ou.*completo/);
    // Sinal positivo: confirma compact (ou avança para wsi_questions).
    const hasWsi = await page.locator('[data-wizard-stage="wsi_questions"], [data-testid*="wsi-questions"]').count();
    const acked = lastFew.includes('compacto') || lastFew.includes('7 perguntas');
    expect(hasWsi > 0 || acked).toBeTruthy();
  });

  test('C6 — competency: "qual a diferença?" responde sem mutar screening_mode', async ({ page }) => {
    // T4 (Task #1086) — pergunta natural no stage competency é classificada
    // como `ask_question`; gate responde com explicação 7q/12q SEM avançar
    // para wsi_questions.
    const chatInput = page.getByTestId('chat-input').or(page.locator('textarea').first());
    await chatInput.fill('quero criar uma vaga de Engenheiro de Software Pleno remoto, faixa 14-20k. Python, AWS.');
    await chatInput.press('Enter');
    await expect(
      page.locator('[data-testid*="wizard-jd"], [data-wizard-stage="jd_enrichment"]').first(),
    ).toBeVisible({ timeout: 60_000 });
    await chatInput.fill('manda bala');
    await chatInput.press('Enter');
    await expect(
      page.locator('[data-wizard-stage="competency"], [data-testid*="competency"], [data-testid*="screening-mode"]').first(),
    ).toBeVisible({ timeout: 60_000 });

    await chatInput.fill('qual a diferença entre os dois?');
    await chatInput.press('Enter');
    await page.waitForTimeout(8_000);

    const messages = await page.locator('[data-testid="chat-message"], [role="article"]').allTextContents();
    const last = (messages[messages.length - 1] || '').toLowerCase();

    // Anti-padrão #1: NÃO avançou para wsi_questions sem escolha explícita.
    const hasWsi = await page.locator('[data-wizard-stage="wsi_questions"], [data-testid*="wsi-questions"]').count();
    expect(hasWsi).toBe(0);
    // Anti-padrão #2: NÃO confirmou seleção de modo.
    expect(last).not.toMatch(/modo (compacto|completo) selecionado/);
    // Sinal positivo: explicou diferença (cita 7 vs 12 perguntas OU os dois nomes).
    expect(last).toMatch(/7\s*pergunt|12\s*pergunt|compacto|completo/);
  });

  test('C7 — wsi_questions: "tá bom, manda ver" aprova pacote sem repetir canned', async ({ page }) => {
    // T5 (Task #1087) — wizard avança até wsi_questions e o gate LLM-based
    // interpreta "tá bom, manda ver" como `approve_all` → questions_approved=true.
    const chatInput = page.getByTestId('chat-input').or(page.locator('textarea').first());
    await chatInput.fill('quero criar uma vaga de Engenheiro Backend Pleno remoto, faixa 12-18k. Stack: Python, AWS, Postgres.');
    await chatInput.press('Enter');
    await expect(
      page.locator('[data-testid*="wizard-jd"], [data-wizard-stage="jd_enrichment"]').first(),
    ).toBeVisible({ timeout: 60_000 });
    await chatInput.fill('manda bala');
    await chatInput.press('Enter');
    await expect(
      page.locator('[data-wizard-stage="competency"], [data-testid*="competency"], [data-testid*="screening-mode"]').first(),
    ).toBeVisible({ timeout: 60_000 });
    await chatInput.fill('vamos com o compacto');
    await chatInput.press('Enter');
    await expect(
      page.locator('[data-wizard-stage="wsi_questions"], [data-testid*="wsi-questions"]').first(),
    ).toBeVisible({ timeout: 90_000 });

    const initialCount = await page.locator('[data-testid="chat-message"], [role="article"]').count();
    await chatInput.fill('tá bom, manda ver');
    await chatInput.press('Enter');
    await page.waitForTimeout(8_000);

    const messages = await page.locator('[data-testid="chat-message"], [role="article"]').allTextContents();
    const after = messages.slice(initialCount).join(' | ').toLowerCase();

    // Anti-padrão #1: NÃO repete o canned "preciso de aprovação" 4× — bug HITL #2.
    const cannedRepeats = (after.match(/preciso de aprova[cç][aã]o/g) || []).length;
    expect(cannedRepeats).toBeLessThanOrEqual(1);
    // Anti-padrão #2: NÃO regenera (bug seria entender "manda" como regenerate).
    expect(after).not.toMatch(/regenerando|gerando.*novo.*pacote/);
    // Sinal positivo: confirma aprovação OU já avançou para elegibilidade.
    const hasElig = await page.locator('[data-wizard-stage="eligibility"], [data-testid*="eligibility"]').count();
    const acked = after.includes('aprovado') || after.includes('elegibilidade');
    expect(hasElig > 0 || acked).toBeTruthy();
  });

  test('C8 — wsi_questions: "mexe na pergunta 3" identifica edit cirúrgico', async ({ page }) => {
    // T5 (Task #1087) — pedido de edição de pergunta específica é classificado
    // como `edit_specific_question` com question_index=3, sem confundir com
    // aprovação ou regeneração total.
    const chatInput = page.getByTestId('chat-input').or(page.locator('textarea').first());
    await chatInput.fill('quero criar uma vaga de Analista de Dados Pleno remoto, faixa 10-15k. SQL, Python, dbt.');
    await chatInput.press('Enter');
    await expect(
      page.locator('[data-testid*="wizard-jd"], [data-wizard-stage="jd_enrichment"]').first(),
    ).toBeVisible({ timeout: 60_000 });
    await chatInput.fill('manda bala');
    await chatInput.press('Enter');
    await expect(
      page.locator('[data-wizard-stage="competency"], [data-testid*="competency"], [data-testid*="screening-mode"]').first(),
    ).toBeVisible({ timeout: 60_000 });
    await chatInput.fill('vamos com o compacto');
    await chatInput.press('Enter');
    await expect(
      page.locator('[data-wizard-stage="wsi_questions"], [data-testid*="wsi-questions"]').first(),
    ).toBeVisible({ timeout: 90_000 });

    const initialCount = await page.locator('[data-testid="chat-message"], [role="article"]').count();
    await chatInput.fill('mexe na pergunta 3, deixa mais técnica');
    await chatInput.press('Enter');
    await page.waitForTimeout(8_000);

    const messages = await page.locator('[data-testid="chat-message"], [role="article"]').allTextContents();
    const after = messages.slice(initialCount).join(' | ').toLowerCase();

    // Anti-padrão #1: NÃO trata como aprovação.
    const hasElig = await page.locator('[data-wizard-stage="eligibility"], [data-testid*="eligibility"]').count();
    expect(hasElig).toBe(0);
    expect(after).not.toMatch(/aprovado!.*elegibilidade/);
    // Sinal positivo: reconheceu o pedido de edição na pergunta 3.
    expect(after).toMatch(/(pergunta\s*3|ajustar|t[eé]cnica|editar)/);
  });

  test('C4 — review/publish exige dupla confirmação de chat (T6)', async ({ page }) => {
    // Cenário canônico T6 — Task #1088. Após chegar ao stage `review`,
    // o primeiro `publica agora` NÃO deve disparar publicação imediata —
    // a LIA precisa pedir confirmação. O segundo `publica agora` dentro
    // do TTL (5min) destrava `policy_confirmed_publish` e o publish_node.
    const chatInput = page.getByTestId('chat-input').or(page.locator('textarea').first());
    await chatInput.fill('vaga de Analista de Dados Pleno remoto');
    await chatInput.press('Enter');
    await expect(
      page.locator('[data-wizard-stage="jd_enrichment"], [data-testid*="wizard-jd"]').first(),
    ).toBeVisible({ timeout: 60_000 });

    // Avança forçado pelo chat até review (sequência canônica conversacional).
    for (const turn of ['aprova', 'compacto', 'manda ver', 'aprova as elegibilidades']) {
      await chatInput.fill(turn);
      await chatInput.press('Enter');
      await page.waitForTimeout(8_000);
    }

    // Aguarda o painel de review aparecer.
    await expect(
      page.locator('[data-wizard-stage="review"], [data-testid*="wizard-review"]').first(),
    ).toBeVisible({ timeout: 90_000 });

    // 1ª confirmação — deve PEDIR confirmação, NÃO publicar ainda.
    const before1 = await page.locator('[data-testid="chat-message"], [role="article"]').count();
    await chatInput.fill('publica agora');
    await chatInput.press('Enter');
    await page.waitForTimeout(8_000);

    const messages1 = await page.locator('[data-testid="chat-message"], [role="article"]').allTextContents();
    const after1 = messages1.slice(before1).join(' | ').toLowerCase();
    // Sinal positivo: pediu confirmação.
    expect(after1).toMatch(/(confirma|tem certeza|publicar.*\?)/);
    // Anti-padrão: NÃO deve ter ido para publish/calibration sem 2ª confirmação.
    const publishedYet = await page.locator('[data-wizard-stage="publish"], [data-wizard-stage="calibration"]').count();
    expect(publishedYet).toBe(0);

    // 2ª confirmação — destrava publish.
    await chatInput.fill('confirmo, manda');
    await chatInput.press('Enter');
    await page.waitForTimeout(15_000);

    // Sinal positivo: chegou ao publish (ou já avançou para calibration).
    const publishedNow = await page.locator(
      '[data-wizard-stage="publish"], [data-wizard-stage="calibration"], [data-testid*="share-link"]',
    ).count();
    expect(publishedNow).toBeGreaterThan(0);
  });

  test('C5 — request_changes em review volta para a seção indicada (T6)', async ({ page }) => {
    // Verifica que `muda o título` no review NÃO é confundido com publicação
    // e roteia de volta ao jd_enrichment.
    const chatInput = page.getByTestId('chat-input').or(page.locator('textarea').first());
    await chatInput.fill('vaga de Coordenador de Vendas remoto');
    await chatInput.press('Enter');
    await expect(
      page.locator('[data-wizard-stage="jd_enrichment"], [data-testid*="wizard-jd"]').first(),
    ).toBeVisible({ timeout: 60_000 });

    for (const turn of ['aprova', 'compacto', 'manda ver', 'aprova as elegibilidades']) {
      await chatInput.fill(turn);
      await chatInput.press('Enter');
      await page.waitForTimeout(8_000);
    }
    await expect(
      page.locator('[data-wizard-stage="review"], [data-testid*="wizard-review"]').first(),
    ).toBeVisible({ timeout: 90_000 });

    const before = await page.locator('[data-testid="chat-message"], [role="article"]').count();
    await chatInput.fill('muda o título pra Sales Lead Pleno');
    await chatInput.press('Enter');
    await page.waitForTimeout(10_000);

    const messages = await page.locator('[data-testid="chat-message"], [role="article"]').allTextContents();
    const after = messages.slice(before).join(' | ').toLowerCase();
    // Sinal positivo: reconheceu pedido de ajuste no título.
    expect(after).toMatch(/(t[íi]tulo|ajustar|sales lead)/);
    // Anti-padrão: NÃO foi pra publish.
    const publishedYet = await page.locator('[data-wizard-stage="publish"]').count();
    expect(publishedYet).toBe(0);
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
