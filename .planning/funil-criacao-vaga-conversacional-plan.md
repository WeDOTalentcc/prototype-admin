# Plano Estrutural — Funil Conversacional de Criação de Vaga (reestruturação)

> Origem: auditoria E2E 2026-05-29 (commit-base feat/benefits-prv-canonical no Replit) +
> decisão de produto de Paulo. Objetivo: o intake conversacional coleta/confirma TUDO
> que a vaga precisa, com sugestões assistidas por benchmark, dimensionadas pela
> metodologia WSI escolhida no início. Inverte a derivação atual (JD→competências)
> para **competências confirmadas → JD consistente**.

## Princípio arquitetural (a espinha)

- **Hoje:** `jd_enrichment` (WSI F1) gera competências como *subproduto* de um JD auto-gerado;
  o modo de triagem (7/12) só é decidido no estágio 7 (competency_gate) — tarde demais.
- **Alvo:** o recrutador é **dono das competências**. A IA **sugere** (benchmark) cedo,
  ele confirma/edita, e o JD é gerado *consistente com elas*. O modo de triagem é a
  **primeira decisão** e dimensiona quantas competências/perguntas existem.

## Reality check do modelo de dados (VERIFICADO — zero migration)

Todas as colunas já existem em `libs/models/lia_models/job_vacancy.py`:
- `employment_type` (CLT/PJ/Temporary) ✅ — contrato
- `salary_range` JSON {min,max,currency} ✅ — remuneração
- `technical_requirements` JSON ✅ / `behavioral_competencies` JSON ✅
- `work_model`, `seniority_level`, `department`/`department_id` ✅
- `manager`, `manager_email`, `recruiter_email`, `organizational_structure` JSON ✅

**Nenhuma migration necessária.** Os 2 P0 (contrato + salário) são wire de fluxo, não schema.

---

## FASE 0 — Pré-requisitos P0 (desbloqueiam o resto; pequenos e independentes)

### P0-A — Persistir contrato (employment_type)
- **Produtor:** `intake_node._val` (não lê `contract_type` do schema) + `state.py` (sem campo) + `publish.job_data` (sem employment_type).
- **Fix:** adicionar `parsed_employment_type` ao state; mapear `payload.contract_type` no intake; coletar via chips no painel (CLT/PJ/Temporário); incluir `employment_type` no `publish.job_data`.
- **Sensor:** teste de contrato `publish.job_data` inclui employment_type quando setado; teste do intake mapeia contract_type.
- **Tamanho:** S. Sem migration.

### P0-B — Persistir faixa salarial (salary_range)
- **Produtor:** nenhum nó GRAVA `salary_min/max` (só `review_gate` reseta pra None); `salary_node` só faz benchmark; sliders do painel mandam texto que nenhum gate ingere.
- **Fix:** gate de ingestão da faixa (parse "Salário entre R$ X e R$ Y" + aceitar sugestão do benchmark); gravar `salary_min/max/currency` no state; mapear pra `salary_range` JSON no `publish.job_data` (hoje manda salary_min/max soltos — confirmar contrato do endpoint Rails create_job).
- **Sensor:** teste end-to-state: aceitar sugestão de benchmark → salary_range chega não-None no job_data.
- **Tamanho:** M.

---

## ÉPICO — Reestruturação do intake (inversão competências→JD)

### FASE 1 — Modo de triagem como primeira decisão
- Mover a escolha `screening_mode` (compact 7 / complete 12 + tempo estimado) do `competency_gate` (estágio 7) para o **intake** (estágio 1).
- Mensagem orientadora: "Compacto = 7 perguntas (~X min) / Completo = 12 (~Y min)" — seta expectativa.
- **Regra explícita competências↔perguntas (NOVA):** definir o mapeamento canônico
  (ex: compact = top N competências → 7 perguntas; complete → 12). Vive em um único
  lugar (constante/serviço), consumido por jd_enrichment, competency e wsi_questions.
- State: `screening_mode` já existe; garantir que é setado no intake e respeitado downstream.
- **Risco:** competency_gate hoje seta screening_mode via LLM — manter compat (se já setado no intake, gate vira confirmação, não decisão).
- **Tamanho:** M.

### FASE 2 — Serviço de competency-benchmark (NET-NEW — espelho do salary benchmark)
- Criar `CompetencyBenchmarkService` (espelho do `MarketBenchmarkService`) que sugere
  competências técnicas + comportamentais por (título + senioridade + departamento + modo).
- Fontes possíveis: role-profile interno + agregados (reusar pattern `BigFiveDepartmentProfileRepository`) + LLM com grounding WSI. **Dimensionado pelo modo** (N competências).
- Multi-tenancy: `company_id` do contexto (nunca payload). LGPD: sem dados sensíveis na sugestão.
- Fairness: sugestões passam por FairnessGuard (mesma disciplina do jd_enrichment P7).
- **Risco:** qualidade da sugestão com input magro (só título+senioridade). Mitigação: benchmark + few-shot por família de cargo.
- **Tamanho:** L (é o item mais pesado).

### FASE 3 — intake_gate vira "confirmação assistida"
- Estender o `intake_gate` (Frente 2) para, além de salário, sugerir **competências técnicas + comportamentais** (via Fase 2), dimensionadas pelo modo.
- Recruiter aceita/edita/adiciona via painel (chips) — recognition > recall.
- Gestor + email coletados via **painel (form), não conversacional** + **não-bloqueante**.
- Grava competências confirmadas no state (`confirmed_technical_competencies`, `confirmed_behavioral_competencies` — campos novos).
- **Tamanho:** M.

### FASE 4 — Inverter jd_enrichment (WSI F1): consumir, não produzir
- `jd_enrichment` passa a **consumir** as competências já confirmadas (input) e gerar um JD
  CONSISTENTE com elas, em vez de gerá-las do zero.
- Mantém WSI F1.C (thresholds, P7 fairness, quality_score) — mas agora o F1 conhece o modo
  e as competências confirmadas.
- **Risco alto:** muda o contrato do nó mais central. Precisa de fallback: se não há
  competências confirmadas (fast-path de quem colou JD pronto), jd_enrichment volta ao
  comportamento atual (gera competências). Defesa em profundidade.
- **Tamanho:** L.

### FASE 5 — Painel lateral = ficha de briefing viva (frontend)
- `DynamicContextPanel` do intake/intake_gate vira form acumulativo: preenche conforme o
  chat anda, mostra o que falta (bloqueante vs enriquecedor), recruiter edita direto.
- **Bloqueante p/ avançar:** título, senioridade, modelo trabalho, modo de triagem.
  **Enriquecedor/diferível:** gestor, contrato, salário exato, ajuste de competências.
- **Preservar fast-path:** quem cola JD pronto pula o Q&A (classifier `provides_jd_intent`).
- **Tamanho:** M-L (frontend + i18n + sensores vitest).

### FASE 6 — Reconciliar competency / wsi_questions (consumir o confirmado)
- `competency` (F4/F5): monta `question_distribution` a partir das competências confirmadas
  + modo (não re-deriva do JD).
- `wsi_questions` (F6): gera exatamente N perguntas conforme o modo + competências.
- `salary` (estágio 6): vira confirmação/validação (faixa já confirmada na Fase 0-B/3).
- **Tamanho:** M.

---

## Ordem de execução recomendada

1. **P0-A + P0-B** (pré-req, independentes, entregam valor imediato — vaga deixa de sair sem contrato/salário).
2. **Fase 1** (modo cedo + regra competências↔perguntas — fundação do dimensionamento).
3. **Fase 2** (benchmark de competências — habilita Fase 3).
4. **Fase 3** (confirmação assistida no intake_gate).
5. **Fase 4** (inverter jd_enrichment — com fallback).
6. **Fase 6** (reconciliar consumidores) — pode ir em paralelo com Fase 5.
7. **Fase 5** (painel ficha viva).

## Riscos transversais

- **Inversão do contrato do jd_enrichment (F1)** — nó mais central; exige fallback robusto + sensores de regressão WSI.
- **Fast-path (colar JD)** não pode regredir — classifier `provides_jd_intent` deve continuar pulando o Q&A.
- **Carga cognitiva** — não transformar o intake em interrogatório; bloqueante vs enriquecedor é a régua.
- **Multi-tenancy + LGPD + Fairness** nas sugestões de competências (Fase 2/3) — mesma disciplina canônica.
- **Drift FE↔BE** do `ui_action` (P1 da auditoria) — corrigir no bridge ao mexer no painel (Fase 5).
- **Coordenação com agente paralelo** ativo no workspace Replit (agent-studio + search_feedback) — staging preciso por fase.

## Cascata canonical por fase (REGRA #0)

Cada fase passa por: `canonical-fix` (produtor vs consumidor) → `feature-impact` (surfaces afetados) →
`lia-testing` (TDD Red→Green) → `lia-compliance` (multi-tenant/LGPD/fairness onde tocar) →
`feature-audit` (14 dimensões antes de concluir). Sensores computacionais > inferenciais.

## Critérios de sucesso do épico

- Vaga publicada SEMPRE com: contrato, faixa salarial, competências técnicas + comportamentais
  confirmadas pelo recrutador, dimensionadas ao modo de triagem.
- Modo de triagem escolhido no início, com expectativa de tempo.
- jd_enrichment gera JD consistente com competências confirmadas (não as inventa).
- Fast-path preservado (colar JD pronto continua rápido).
- Zero regressão nos sensores WSI existentes.

---

## Estado de execução (atualizado 2026-05-30)

Branch Replit: .

- ✅ **Fase 0 — P0-A** contrato (employment_type): commit  (+3 testes TDD).
- ✅ **Fase 0 — P0-B** salário (salary_range do benchmark): commit  (+3 testes TDD).
- ✅ **Fase 1** — modo de triagem no intake + SCREENING_MODE_CONFIG canonical: commit `4f2676b79`. (+29 testes TDD)
  Intake gate captura modo do recrutador; competency_gate pula LLM quando modo já setado.
- ✅ **Fase 2** — CompetencyBenchmarkService (net-new, espelho do MarketBenchmarkService): commit `0b1f8a793`. (+16 testes TDD)
  Sugere competências téc+comp por título/senioridade/depto/modo; dimensionado via SCREENING_MODE_CONFIG (compact 5+2, full 8+4); FairnessGuard P7 filtra; fallback por família de cargo; company_id na cache key.
- ✅ **Fase 3** — intake_gate confirmação assistida de competências: commit `8b0c9186b`. (+11 testes TDD)
  Ao aprovar, sugere competências (via Fase 2) dimensionadas pelo modo, seed em confirmed_* (accept-all; right_panel_form tem precedência); campos novos no state; fail-open não bloqueia aprovação; gestor/email já eram não-bloqueantes.
- ✅ **Fase 4** — inverter jd_enrichment (WSI F1): commit `eb82d9b5f`. (+11 testes TDD)
  jd_enrichment consome confirmed_* (Fase 3) e gera JD consistente; override determinístico das competências (sem drift do LLM); quality_score mode-aware (compact 5+2 não penalizado); fallback honra confirmadas; sem confirmed_* → comportamento legado. Stub t1062 atualizado em lockstep.
- ⬜ **PRÓXIMA: Fase 6** — reconciliar competency/wsi_questions: montar question_distribution a partir das confirmed_* + modo (não re-derivar do JD); gerar N perguntas conforme modo. (Fase 5 painel ficha viva fica deferida — frontend.)
- ⬜ Fase 5 (painel ficha viva, frontend) — deferida (FASE 6 FE deferida per repo).

### Como retomar (sessão nova)
1. Abrir Claude Code no projeto.
2. Colar: "Continue o épico do funil de criação de vaga. Leia o plano em
    no Replit (ssh replit-wedo-0405,
   branch feat/benefits-prv-canonical). Fases 0-4 feitas e commitadas
   (+ fix do benchmark salarial no intake_gate, commit 101963773).
   Comece a Fase 6 (reconciliar competency/wsi_questions: question_distribution a partir
   das confirmed_* + modo; gerar N perguntas conforme modo). Fase 5 (painel FE) deferida.
   Cascata canonical-fix + lia-testing (TDD) + harness-engineering."
3. Disciplina: ler código real no Replit antes de editar; TDD Red→Green; commit atômico
   por fase; stage só os arquivos da fase (agente paralelo ativo no workspace).
