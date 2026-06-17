/**
 * Cenário C — HITL com correção (Task #1057).
 *
 * Recrutador entra no wizard, recebe sugestões da LIA até a etapa de
 * setor/quantidade, pede uma CORREÇÃO em texto livre ANTES de aprovar
 * (ex.: "na verdade são 3 vagas, não 2") e valida que:
 *   1. A LIA responde reconhecendo a correção (nova bubble não-vazia).
 *   2. O wizard continua avançando (sessão NÃO foi resetada — checkpointer
 *      LangGraph + wizard_session_pin Tier 0.5 do CascadedRouter mantêm
 *      contexto).
 *   3. Quando o WizardPipelineTemplateCard aparecer, o tile sugerido
 *      ainda reflete o título original (LIA não esqueceu o cargo após a
 *      correção do número de vagas — sentinela Bug B2 do gate online
 *      eval/golden/wizard_no_tenant_leak.jsonl).
 *
 * Reuso integral dos helpers canônicos `goToChatHome` + `sendMessageAndWait`
 * (sem paralelismo, sem testid novo). Assertos em invariantes estruturais
 * (presença de bubble, atributo data-testid do tile) — não em wording exato
 * da LIA (LLM não-determinístico).
 */

import { test, expect } from '../../fixtures/auth.fixture'
import {
  SEL,
  goToChatHome,
  sendMessageAndWait,
  captureMilestone,
  attachQualitySensors,
  assertNoAiSlop,
} from './01-helpers'

test.describe.configure({ retries: 1 })

test.describe('Cenário C — HITL com correção em texto livre', () => {
  test.setTimeout(12 * 60_000)

  test('C — recrutador corrige número de vagas antes de aprovar', async ({
    authenticatedPage: page,
  }, testInfo) => {
    const sensors = attachQualitySensors(page, testInfo)

    try {
      await goToChatHome(page)
      await captureMilestone(page, testInfo, 'C-00-dashboard')

      // 1. Greeting — vaga técnica (mesmo cargo do Cenário A para reuso de
      //    sinal canônico de tile "technical").
      await sendMessageAndWait(
        page,
        'Quero criar uma vaga de Engenheiro de Software Pleno'
      )
      await captureMilestone(page, testInfo, 'C-01-greeting')

      await sendMessageAndWait(page, 'confirma')

      // 2. Setor inicial — recrutador erra de propósito o número de vagas.
      const beforeCorrection = await page.locator(SEL.liaMarkdown).count()
      await sendMessageAndWait(page, 'Engenharia, 2 vagas, prazo 30 dias')
      await captureMilestone(page, testInfo, 'C-02-pre-correcao')

      // 3. Correção em texto livre ANTES de aprovar template.
      //    Verbo natural — o agente precisa reconhecer "na verdade" como sinal
      //    de update, não como nova vaga.
      await sendMessageAndWait(
        page,
        'na verdade são 3 vagas, não 2 — pode ajustar'
      )
      await captureMilestone(page, testInfo, 'C-03-correcao')

      // 4. Invariante estrutural #1 — sessão sobreviveu à correção:
      //    nova bubble da LIA chegou (count cresceu desde antes da correção).
      const afterCorrection = await page.locator(SEL.liaMarkdown).count()
      expect(
        afterCorrection,
        'LIA deve responder à correção de quantidade (sem reset de sessão)'
      ).toBeGreaterThan(beforeCorrection)

      // 4.b Invariante de CONTEÚDO da correção — a(s) bubble(s) NOVA(s)
      //     pós-correção precisam refletir o número novo (3 / três) em
      //     algum lugar. Sem isso, a LIA poderia ter "respondido" mas
      //     ignorado o ajuste — falso positivo do count puro.
      const newBubblesAfterCorrection = (
        await page.locator(SEL.liaMarkdown).allTextContents()
      )
        .slice(beforeCorrection)
        .join('\n')
        .toLowerCase()
      expect(
        /\b3\b|\btr[eê]s\b/.test(newBubblesAfterCorrection),
        `LIA deve refletir a correção (3 vagas) na resposta nova (got: "${newBubblesAfterCorrection.slice(0, 400)}")`
      ).toBe(true)

      // 5. Invariante estrutural #2 — template card eventualmente aparece
      //    (a correção pode atrasar 1 turno — daí timeout generoso). FAIL-LOUD.
      await expect(
        page.locator(SEL.templateCard),
        'WizardPipelineTemplateCard deve aparecer após correção HITL'
      ).toBeVisible({ timeout: 60_000 })

      // 6. Invariante estrutural #3 — tile "technical" continua sendo o
      //    SUGERIDO (data-suggested="true") após a correção do número de
      //    vagas. Visibilidade sozinha não prova nada (todos os tiles ficam
      //    visíveis); o sinal canônico de classificação preservada é o
      //    atributo `data-suggested` — sentinela Bug B2 / Task #1052
      //    (cargo "Engenheiro de Software" NÃO esquecido após HITL).
      const technical = page.locator(
        '[data-testid="wizard-template-option-technical"]'
      )
      await expect(
        technical,
        'tile "technical" deve permanecer visível pós-correção HITL'
      ).toBeVisible({ timeout: 5_000 })
      await expect(
        technical,
        'tile "technical" deve permanecer SUGERIDO (data-suggested=true) — sentinela Bug B2'
      ).toHaveAttribute('data-suggested', 'true')

      // 7. Sentinela: LIA não regrediu para AI-slop após a correção.
      await assertNoAiSlop(page)
    } finally {
      await sensors.attach()
    }
  })
})
