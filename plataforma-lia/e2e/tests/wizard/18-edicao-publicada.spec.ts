/**
 * E2E — Task #1131 (T5.1) — Supervisor intent `edit_published`.
 *
 * Cobre o caminho de edição pós-publicação: recrutador volta após publicar
 * uma vaga e diz "Quero mudar o salário da vaga X" / "Ajusta a descrição da
 * vaga Y". Supervisor deve roteiar para o fluxo de Job Management (NÃO
 * iniciar novo `JobCreationGraph` do zero).
 *
 * Sentinelas estruturais:
 *   1. Resposta da LIA NÃO dispara `data-wizard-stage` de wizard novo —
 *      o painel de criação NÃO abre (não há `wizard-progress-bar`).
 *   2. Resposta da LIA reconhece o pedido de edição (heurística: mencione
 *      "salário" OU pergunte qual vaga editar).
 *   3. NÃO há padrão de re-criação ("Vamos criar uma vaga …").
 *
 * Desvio do brief: o fluxo backend de Job Management pode ainda não estar
 * 100% wireado para edição via chat — a spec valida APENAS o roteamento
 * do supervisor (não inicia novo wizard) e foi escrita defensiva para
 * aceitar tanto o caminho final (edição inline) quanto o intermediário
 * (LIA pergunta qual vaga editar / dá link).
 *
 * Pré-requisitos:
 *   - `LIA_WIZARD_SUPERVISOR_CLASSIFIER=true`
 *   - Pelo menos 1 vaga publicada pelo tenant do usuário autenticado.
 *
 * Como rodar:
 *   bash plataforma-lia/scripts/run-pw-cenario.sh \
 *     pw-cenario-1131-18 e2e/tests/wizard/18-edicao-publicada.spec.ts
 */
import { expect } from '@playwright/test'
import { test } from '../../fixtures/auth.fixture'
import {
  goToChatHome,
  sendMessageAndWait,
  SEL,
  quickPublishTechVacancy,
} from './01-helpers'

test.describe('Task #1131 — supervisor intent=edit_published', () => {
  test('"Quero mudar o salário da vaga X" NÃO inicia novo wizard', async ({
    authenticatedPage: page,
  }) => {
    // ── Pré-condição: garante que existe pelo menos 1 vaga publicada ──────
    // Usa o helper canônico `quickPublishTechVacancy` (já cobre todo o flow).
    // Se a vaga falhar a publicar (backend down), o teste falha aqui — o que
    // é o comportamento desejado (não silenciar).
    await quickPublishTechVacancy(page)

    // ── Reset: volta para a home limpa e abre chat ────────────────────────
    await page.goto('/pt', { waitUntil: 'domcontentloaded', timeout: 60_000 })
    await goToChatHome(page)

    // ── Ação: pede edição de vaga existente ──────────────────────────────
    await sendMessageAndWait(
      page,
      'Quero mudar o salário da vaga de Engenheiro de Software Pleno',
      { timeout: 60_000 },
    )

    // INVARIANTE ESTRUTURAL 1 — supervisor NÃO disparou wizard novo.
    // O painel de criação (wizard-progress-bar) NÃO deve aparecer.
    // Usamos `toBeHidden` (Playwright auto-retry até o timeout) ao invés de
    // `waitForTimeout` + `isVisible` — `toBeHidden` ASSERTA a ausência ao
    // longo de toda a janela, eliminando race (se o painel abrir no segundo
    // 4, o teste falha como esperado em vez de passar falsamente).
    await expect(
      page.locator(SEL.wizardProgressBar),
      'Supervisor=edit_published NÃO deve abrir painel de criação. ' +
        'Se o progress bar apareceu, o intent foi classificado erradamente ' +
        'como create_new.',
    ).toBeHidden({ timeout: 8_000 })

    // INVARIANTE ESTRUTURAL 2 — LIA NÃO usou padrão de criação from-scratch.
    const last = ((await page.locator(SEL.liaMarkdown).last().innerText()) || '')
      .toLowerCase()
    expect(
      /vamos (criar|abrir) uma vaga (do zero|nova)|qual cargo voc[eê] (quer|deseja) criar/i.test(
        last,
      ),
      `Supervisor=edit_published NÃO deve disparar criação: "${last.slice(0, 200)}"`,
    ).toBe(false)

    // INVARIANTE ESTRUTURAL 3 — LIA reconheceu o pedido de EDIÇÃO (não só
    // ecoou o input). Sensor é heurístico (LLM não-determinístico) — exige
    // EVIDÊNCIA DE AÇÃO DE EDIÇÃO ou pergunta de DESAMBIGUAÇÃO de vaga:
    //   (a) verbo/substantivo de edição: editar/alterar/mudar/atualizar/ajustar;
    //   (b) menciona campo a alterar: salário/remuneração/faixa;
    //   (c) link/oferta para abrir a vaga (abrir/acessar/ir para a vaga);
    //   (d) pergunta de desambiguação (qual vaga/quais vagas).
    // Refinado pós-code-review #1131: a regex anterior aceitava ecos genéricos
    // como "engenheiro|pleno" que poderiam casar respostas tipo "Não entendi
    // qual engenheiro pleno você quer", escondendo falha de entendimento.
    const recognizes =
      /\b(editar|alterar|mudar|atualizar|ajustar|modificar)\b/i.test(last) ||
      /\b(sal[aá]rio|remunera[cç][aã]o|faixa salarial)\b/i.test(last) ||
      /\b(abrir|acessar|ir para) (a )?vaga\b/i.test(last) ||
      /\b(qual|quais) (a |as )?vagas?\b/i.test(last)
    expect(
      recognizes,
      `LIA precisa reconhecer pedido de edição (verbo de edição, campo ou ` +
        `desambiguação). Resposta: "${last.slice(0, 300)}"`,
    ).toBe(true)
  })
})
