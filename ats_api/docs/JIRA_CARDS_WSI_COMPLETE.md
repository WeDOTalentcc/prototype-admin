# JIRA Cards — WSI F1–F11 (Spec-Driven Development)

> **Metodologia:** cada card segue o padrão **Given / When / Then** com arquivo de spec nomeado, dependências e estimativa de implementação em dias de engenharia (**1 dev sênior full-time**).
>
> **Épicos sugeridos:**
>
> - **Epic A — Bloco A: criação da vaga (F1–F6)**
> - **Epic B — Bloco B: triagem do candidato (F7–F9)**
> - **Epic C — Decisão e relatório (F10–F11)**

---

## F1 — JD: criação, revisão e enriquecimento

---

### WSI-F1-01 — JD Quality Score determinístico (F1.B)

**Tipo:** Story | **Epic:** A | **Estimativa:** 3 dias

**Descrição:**  
Criar `Wsi::JdQualityScoreService` que avalia o JD em 9 dimensões (§1.4 da metodologia) e retorna um score 0–100 + breakdown, sem invocar LLM. Persistir em novo campo jsonb `jd_quality_score` na tabela `jobs` (ou tabela `job_wsi_profiles`).

**Critérios de aceite:**

- **Given** um `Job` com `title`, `description`, `responsibilities` e skills preenchidas  
  **When** `Wsi::JdQualityScoreService.call(job: job)` é chamado  
  **Then** retorna `{ score: Integer(0..100), dimensions: Hash, status: :critical|:insufficient|:adequate|:good|:excellent }`
- **Given** job com `description` < 100 palavras  
  **Then** dimension `density` retorna score 0 e score total < 30 (bloqueio)
- **Given** job com todas as 9 dimensões completas  
  **Then** score total >= 85
- Score é persistido em `jobs.jd_quality_score` (jsonb) após cálculo

**Spec:** `spec/services/wsi/jd_quality_score_service_spec.rb`  
**Migration:** `add_jd_quality_score_to_jobs`  
**Dependências:** nenhuma

---

### WSI-F1-02 — JD Enrichment LLM service + campo `lia_job_description` (F1.C)

**Tipo:** Story | **Epic:** A | **Estimativa:** 3 dias

**Descrição:**  
Criar `Wsi::JdEnrichmentService` que recebe o JD atual e invoca LLM (temperatura 0.3) retornando schema canônico: `enriched_jd` (skills, competências com `trait_big_five`, `about_role`) + `context_signals` (4 níveis) + `quality_report`. Persistir o rascunho em `jobs.lia_job_description` (jsonb) com status `pending_review`.

**Critérios de aceite:**

- **Given** um job com `jd_quality_score >= 30`  
  **When** `Wsi::JdEnrichmentService.call(job: job)` é chamado  
  **Then** salva em `jobs.lia_job_description` com chaves `enriched_jd`, `context_signals`, `quality_report`, `status: "pending_review"`, `enriched_at`
- **Given** job com `jd_quality_score < 30`  
  **Then** serviço retorna `{ success: false, error: "jd_quality_below_threshold" }` sem invocar LLM
- `enriched_jd.competencias_comportamentais` contém ao menos 5 itens, cada um com `trait_big_five` preenchido
- `enriched_jd.skills_obrigatorias` contém ao menos 9 skills

**Spec:** `spec/services/wsi/jd_enrichment_service_spec.rb`  
**Migration:** `add_lia_job_description_to_jobs`  
**Dependências:** WSI-F1-01

---

### WSI-F1-03 — Approval workflow F1.E (aprovar / rejeitar enrichment)

**Tipo:** Story | **Epic:** A | **Estimativa:** 2 dias

**Descrição:**  
Adicionar endpoints e lógica para o recrutador aprovar, editar ou rejeitar o `lia_job_description`. Ao aprovar, `status` muda para `approved`; ao rejeitar, volta a `nil` e F1.B é re-executado. Bloquear disparo do Bloco A (geração de perguntas F6) se `status != "approved"`.

**Critérios de aceite:**

- **Given** `lia_job_description.status == "pending_review"`  
  **When** `PATCH /v1/users/jobs/:id/wsi_jd_approval` com `{ action: "approve" }`  
  **Then** `lia_job_description.status` == `"approved"`, `approved_at` preenchido, `approved_by` = user atual
- **Given** `lia_job_description.status == "pending_review"`  
  **When** `{ action: "reject" }`  
  **Then** `lia_job_description` reseta status para `nil`; job continua editável
- **Given** `lia_job_description.status != "approved"`  
  **When** endpoint de geração de perguntas WSI (F6) é chamado  
  **Then** retorna `422` com `error: "wsi_jd_not_approved"`

**Spec:** `spec/requests/v1/users/jobs_wsi_jd_approval_spec.rb`  
**Dependências:** WSI-F1-02

---

### WSI-F1-04 — Endpoint de preview + serialização F1.D

**Tipo:** Task | **Epic:** A | **Estimativa:** 1 dia

**Descrição:**  
Criar endpoint `GET /v1/users/jobs/:id/wsi_jd_preview` que retorna o `lia_job_description` atual + `jd_quality_score` breakdown para exibição lado a lado no front.

**Critérios de aceite:**

- **Given** job com `lia_job_description` preenchido  
  **When** `GET .../wsi_jd_preview`  
  **Then** resposta inclui `{ original_jd: {...}, enriched_jd: {...}, quality_score: {...} }`
- **Given** job sem `lia_job_description`  
  **Then** retorna apenas `{ original_jd: {...}, quality_score: {...} }`

**Spec:** `spec/requests/v1/users/jobs_wsi_jd_preview_spec.rb`  
**Dependências:** WSI-F1-01, WSI-F1-02

---

## F2 — Extração Big Five do JD (Abordagem C / F2.5)

---

### WSI-F2-01 — `Wsi::JdBigFiveExtractionService` (F2.5)

**Tipo:** Story | **Epic:** A | **Estimativa:** 3 dias

**Descrição:**  
Criar serviço dedicado que extrai perfil OCEAN do JD via LLM (temperature 0.1, max_tokens 800, rubric NEO-PI-R). Input preferencial: `lia_job_description.enriched_jd` (texto limpo); fallback: `job.description`. Saída: JSON com `{ trait, score(0-100), evidence: "citação literal", confidence: high|medium|low }` × 5.

**Critérios de aceite:**

- **Given** job com `lia_job_description.status == "approved"`  
  **When** `Wsi::JdBigFiveExtractionService.call(job: job)` é chamado  
  **Then** retorna objeto com exatamente 5 traits (`openness`, `conscientiousness`, `extraversion`, `agreeableness`, `stability`)
- Cada trait tem `score` entre 0 e 100, `evidence` não vazio (citação do JD), `confidence` em `%w[high medium low]`
- Resultado é persistido em `jobs.wsi_jd_big_five_profile` (jsonb) com `extracted_at` e `method_version`
- LLM é chamado com `temperature: 0.1` (stub nos testes)

**Spec:** `spec/services/wsi/jd_big_five_extraction_service_spec.rb`  
**Migration:** `add_wsi_jd_big_five_profile_to_jobs`  
**Dependências:** WSI-F1-03

---

### WSI-F2-02 — Normalização do enum OCEAN (`neuroticism` vs `stability`)

**Tipo:** Task | **Epic:** A | **Estimativa:** 1 dia

**Descrição:**  
Criar mapeamento canônico único entre o enum interno Rails (`neuroticism` em `questions.ocean_trait`) e o nome adotado pela metodologia WSI (`stability`). Documentar o contrato em constante e aplicar em todos os serializers, prompts e serviços.

**Critérios de aceite:**

- Constante `Wsi::OCEAN_TRAIT_CANONICAL` mapeia `neuroticism` ↔ `stability` de forma bidirecional
- `QuestionSerializer` e `AnswerSerializer` usam o mapeamento
- Prompts de geração (F6) e extração (F2.5) usam sempre `stability`
- Specs verificam round-trip do mapeamento

**Spec:** `spec/lib/wsi/ocean_trait_canonical_spec.rb`  
**Dependências:** WSI-F2-01

---

### WSI-F2-03 — Auditabilidade: evidências salvas por trait

**Tipo:** Task | **Epic:** A | **Estimativa:** 1 dia

**Descrição:**  
Garantir que `jobs.wsi_jd_big_five_profile` sempre persiste `evidence` (citação literal do JD) por trait, para rastreabilidade conforme EU AI Act. Adicionar validação no serviço: se qualquer trait vier sem `evidence`, registrar `confidence: low` e flag `_evidence_missing: true`.

**Critérios de aceite:**

- **Given** resposta LLM com trait sem `evidence`  
  **Then** serviço define `confidence: "low"` e `_evidence_missing: true` nesse trait
- Persistência não falha; flag é visível no endpoint preview F1.D

**Spec:** seção em `spec/services/wsi/jd_big_five_extraction_service_spec.rb`  
**Dependências:** WSI-F2-01

---

## F3 — Ranking ponderado de traits

---

### WSI-F3-01 — `Wsi::TraitRankingService`

**Tipo:** Story | **Epic:** A | **Estimativa:** 1 dia

**Descrição:**  
Criar serviço determinístico que consome `jobs.wsi_jd_big_five_profile` e produz `big_five_ranking`: lista de 5 traits ordenados por `score` decrescente com `rank`, `weight_normalized` (score / soma dos scores Top-N) e número de traits a selecionar pelo modo/senioridade.

**Critérios de aceite:**

- **Given** perfil `{ openness: 74, conscientiousness: 76, extraversion: 40, agreeableness: 50, stability: 75 }` e seniority `senior`, mode `compact`  
  **When** `Wsi::TraitRankingService.call(job: job, mode: :compact)`  
  **Then** retorna `big_five_ranking` com rank 1 = `conscientiousness`, Top-N = 3, `weight_normalized` soma 1.0 para os 3 primeiros
- Resultado é persistido em `jobs.wsi_jd_trait_ranking` (jsonb)
- Specs cobrem todos os níveis de senioridade

**Spec:** `spec/services/wsi/trait_ranking_service_spec.rb`  
**Migration:** `add_wsi_jd_trait_ranking_to_jobs`  
**Dependências:** WSI-F2-01, WSI-F4-01

---

### WSI-F3-02 — Constante `SENIORITY_BIGFIVE_TOP_N`

**Tipo:** Task | **Epic:** A | **Estimativa:** 1 dia

**Descrição:**  
Criar constante (ou YAML de config) `Wsi::Constants::SENIORITY_BIGFIVE_TOP_N` mapeando cada nível WSI (estagiario, junior, pleno, senior, lead, principal, diretor, vp_clevel) para N traits em Compact e Full.

**Critérios de aceite:**

- Constante acessível e testada para todos os 8 níveis × 2 modos
- Compact: estagiário–pleno = 2; senior = 3; lead = 4; vp_clevel = 5
- Full: junior = 3; pleno = 4; senior–diretor–vp = 5

**Spec:** `spec/lib/wsi/constants_spec.rb`  
**Dependências:** WSI-F4-01

---

### WSI-F3-03 — `weight_normalized` vinculado às perguntas comportamentais

**Tipo:** Task | **Epic:** A | **Estimativa:** 1 dia

**Descrição:**  
Ao gerar perguntas (F6), preencher `questions.extra_params["trait_weight"]` com o `weight_normalized` do trait correspondente a partir do ranking F3.

**Critérios de aceite:**

- **Given** ranking F3 gerado com trait `conscientiousness` weight_normalized = 0.356  
  **When** pergunta comportamental para `conscientiousness` é criada  
  **Then** `question.extra_params["trait_weight"]` == 0.356
- Fallback: 1.0 (uniforme) se F3 não disponível

**Spec:** seção em `spec/services/wsi/trait_ranking_service_spec.rb`  
**Dependências:** WSI-F3-01, WSI-F6-01

---

## F4 — Senioridade: definição e calibração

---

### WSI-F4-01 — Mapeamento `Job::SENIORITY` → chave WSI canônica

**Tipo:** Task | **Epic:** A | **Estimativa:** 1 dia

**Descrição:**  
Criar constante `Wsi::Constants::SENIORITY_KEY_MAP` que traduz índice `jobs.seniority` (0–7) para chave semântica WSI (`"junior"`, `"pleno"`, `"senior"`, `"lead"`, `"diretor"`, etc.) e corrigir `EvaluationAggregateService#seniority_multiplier` para usar chave semântica em vez de `seniority.to_s.downcase` numérico.

**Critérios de aceite:**

- **Given** `job.seniority == 2` (Sênior)  
  **When** `Wsi::Constants.seniority_key(job)` é chamado  
  **Then** retorna `"senior"`
- `EvaluationAggregateService` nunca mais usa o fallback `pleno` por causa de string numérica
- Specs cobrem todos os índices 0–7

**Spec:** `spec/lib/wsi/constants_spec.rb`, `spec/services/evaluations/evaluation_aggregate_service_spec.rb`  
**Dependências:** nenhuma (foundation)

---

### WSI-F4-02 — Tabela canônica Bloom/Dreyfus por senioridade (§4.1)

**Tipo:** Task | **Epic:** A | **Estimativa:** 1 dia

**Descrição:**  
Criar constante `Wsi::Constants::SENIORITY_CALIBRATION` com Dreyfus técnico, Bloom esperado e Dreyfus comportamental por nível (tabela §4.1 da metodologia). Usar esta tabela como source-of-truth ao passar parâmetros ao gerador de perguntas e à avaliação.

**Critérios de aceite:**

- Constante inclui todos os 8 níveis
- Specs verificam valores exatos da tabela §4.1
- `JobSuggestionService` e prompt de geração consomem a constante (não inferem via LLM)

**Spec:** `spec/lib/wsi/constants_spec.rb`  
**Dependências:** WSI-F4-01

---

### WSI-F4-03 — `Wsi::SeniorityResolverService` multi-sinal

**Tipo:** Story | **Epic:** A | **Estimativa:** 3 dias

**Descrição:**  
Criar serviço determinístico (sem LLM) que infere senioridade a partir de 5 sinais: `explicit` (0.50), `title_keywords` (0.25), `jd_analysis` (0.25), `salary_range` (0.15), `skills_complexity` (0.10). Retorna `suggested_seniority`, `confidence` e `seniority_source`.

**Critérios de aceite:**

- **Given** job com `title: "Senior Software Engineer"` e sem seniority preenchida  
  **When** `Wsi::SeniorityResolverService.call(job: job)`  
  **Then** `suggested_seniority` == `"senior"`, `confidence` == `"high"`, `seniority_source` inclui `"title_keywords"`
- **Given** título `"Analista"` sem qualificador  
  **Then** `suggested_seniority` == `"pleno"`, `confidence` == `"low"`
- Keywords mapeadas conforme tabela §4.2 da metodologia

**Spec:** `spec/services/wsi/seniority_resolver_service_spec.rb`  
**Dependências:** WSI-F4-01

---

### WSI-F4-04 — Auditoria de override de senioridade

**Tipo:** Task | **Epic:** A | **Estimativa:** 1 dia

**Descrição:**  
Ao recrutador alterar `seniority` no job após o resolver ter sugerido um valor, registrar `seniority_overridden_by`, `seniority_overridden_at` e valor anterior.

**Critérios de aceite:**

- **Given** resolver sugeriu `"senior"`, recrutador salva `"lead"`  
  **Then** `job.seniority_override_log` contém `{ from: "senior", to: "lead", user_id: ..., at: ... }`
- Campos não quebram fluxo se resolver não foi chamado

**Spec:** `spec/models/job_spec.rb`  
**Migration:** `add_seniority_override_log_to_jobs`  
**Dependências:** WSI-F4-03

---

## F5 — Distribuição de perguntas por senioridade e modo

---

### WSI-F5-01 — `Wsi::QuestionDistributionService` (T, B, Top-N)

**Tipo:** Story | **Epic:** A | **Estimativa:** 2 dias

**Descrição:**  
Criar serviço que, dado `seniority_key` e `mode` (`:compact` | `:full`), devolve o plano de distribuição: `{ technical: N, behavioral: M, top_n_traits: K }` conforme tabelas §5.4–5.5 da metodologia.

**Critérios de aceite:**

- **Given** `seniority: "junior"`, `mode: :compact`  
  **Then** `{ technical: 5, behavioral: 2, top_n_traits: 2 }`
- **Given** `seniority: "lead"`, `mode: :compact`  
  **Then** `{ technical: 3, behavioral: 4, top_n_traits: 4 }`
- **Given** `seniority: "senior"`, `mode: :full`  
  **Then** `{ technical: 7, behavioral: 5, top_n_traits: 5 }`
- Specs cobrem todos os níveis × 2 modos com table-driven examples

**Spec:** `spec/services/wsi/question_distribution_service_spec.rb`  
**Dependências:** WSI-F4-01, WSI-F3-02

---

### WSI-F5-02 — Alocação intra-framework §5.8

**Tipo:** Story | **Epic:** A | **Estimativa:** 2 dias

**Descrição:**  
Estender `QuestionDistributionService` com a decomposição §5.8: dado T e B, calcular `{ dreyfus: N, bloom: N, cbi_technical: N, cbi_behavioral: N, big_five: N }` com fórmulas distintas por modo.

**Critérios de aceite:**

- **Given** `seniority: "junior"`, `mode: :compact` (T=5, B=2)  
  **Then** `{ cbi_technical: 3, dreyfus: 1, bloom: 1, cbi_behavioral: 1, big_five: 1 }` soma 7 ✓
- **Given** `seniority: "senior"`, `mode: :full` (T=7, B=5)  
  **Then** `{ cbi_technical: 3, dreyfus: 2, bloom: 2, cbi_behavioral: 3, big_five: 2 }` soma 12 ✓
- Todos os exemplos da tabela §5.8 passam como testes

**Spec:** `spec/services/wsi/question_distribution_service_spec.rb` (contexto `#framework_allocation`)  
**Dependências:** WSI-F5-01

---

### WSI-F5-03 — `JobSuggestionService` consome plano F5

**Tipo:** Story | **Epic:** A | **Estimativa:** 2 dias

**Descrição:**  
Alterar `JobSuggestionService#generate_evaluation_questions` para consultar `QuestionDistributionService` e passar o plano (T, B, Top-N, framework slots) ao prompt, em vez da heurística 70/30 fixa.

**Critérios de aceite:**

- **Given** job com seniority `"lead"` e modo `compact`  
  **When** endpoint de geração é chamado  
  **Then** prompt recebe `technical: 3, behavioral: 4, top_n_traits: [trait1, trait2, trait3, trait4]`
- Score 70/30 fixo no prompt é removido
- Specs de integração verificam o plano no prompt gerado (mock do LLM)

**Spec:** `spec/services/job_suggestion_service_spec.rb`  
**Dependências:** WSI-F5-01, WSI-F5-02, WSI-F3-01

---

### WSI-F5-04 — Unificação das constantes de pesos (F5 ↔ F9)

**Tipo:** Task | **Epic:** A | **Estimativa:** 1 dia

**Descrição:**  
Criar `Wsi::Constants::SENIORITY_WEIGHTS` com os valores canônicos §5.6 / §9.2 (technical, behavioral — 8 níveis). Apontar `EvaluationAggregateService` e `QuestionDistributionService` para a mesma fonte.

**Critérios de aceite:**

- `senior` → `{ technical: 0.5625, behavioral: 0.4375 }`
- `lead` → `{ technical: 0.4375, behavioral: 0.5625 }`
- Ambos os serviços importam a mesma constante (sem duplicação)

**Spec:** `spec/lib/wsi/constants_spec.rb`  
**Dependências:** WSI-F4-01

---

## F6 — Geração de perguntas por LLM

---

### WSI-F6-01 — Trait-affinity: `_select_comp_by_trait` (F6.6)

**Tipo:** Story | **Epic:** A | **Estimativa:** 2 dias

**Descrição:**  
Antes da chamada LLM para pergunta comportamental, selecionar deterministicamente a competência comportamental cujo `trait_big_five` (do `enriched_jd`) corresponde ao trait alvo do Top-N F3. Fallback posicional se match não encontrado.

**Critérios de aceite:**

- **Given** ranking trait `conscientiousness` e competências `[{name: "Organização", trait_big_five: "conscientiousness"}, ...]`  
  **Then** competência `"Organização"` é selecionada
- **Given** nenhuma competência com o trait alvo  
  **Then** usa próxima competência não utilizada (fallback posicional)
- Specs cobrem match exato, fallback e último recurso

**Spec:** `spec/services/wsi/trait_affinity_selector_spec.rb`  
**Dependências:** WSI-F3-01, WSI-F1-03

---

### WSI-F6-02 — Prompts dedicados F6.5 (técnico) e F6.6 (comportamental)

**Tipo:** Story | **Epic:** A | **Estimativa:** 3 dias

**Descrição:**  
Separar os prompts de geração em dois métodos/arquivos distintos alinhados às specs §6.5 (técnico: CBI, fairness, skill rara, proibições de rubric) e §6.6 (comportamental: cenários ativadores por trait, regras DEI especiais para Amabilidade/Estabilidade/Extraversão).

**Critérios de aceite:**

- Pergunta técnica gerada não contém palavras "trade-off", "com critérios", "com resultados mensuráveis" (proibição de rubric)
- Pergunta com skill rara retorna prefix `[SKILL_APPROXIMATED:]` e flag `_skill_approximated: true` nos metadados
- Pergunta comportamental não usa pronomes de gênero ("ele/ela", "o funcionário")
- Cenário Amabilidade é conflito profissional; Estabilidade é pressão de trabalho; Extraversão é liderança/stakeholders
- Temperatura técnica = 0.7; comportamental = 0.75 (verificado no stub)

**Spec:** `spec/services/wsi/question_prompt_builder_spec.rb`  
**Dependências:** WSI-F6-01, WSI-F4-02, WSI-F5-03

---

### WSI-F6-03 — Módulo de validação F6.8 + retries

**Tipo:** Story | **Epic:** A | **Estimativa:** 2 dias

**Descrição:**  
Criar `Wsi::QuestionValidator` com cheques determinísticos pós-geração: comprimento 15–80 palavras, verbo no passado como primeiro verbo principal, ausência de "imagine que" / "como você faria se", pergunta aberta (sem A/B/C). Integrar ao gerador com retry até 3×; se falhar, setar `needs_manual_review: true`.

**Critérios de aceite:**

- **Given** pergunta com 10 palavras  
  **Then** validação falha com `error: :too_short`
- **Given** pergunta hipotética ("Como você faria se...")  
  **Then** falha com `error: :hypothetical_format`
- **Given** 3 tentativas consecutivas falhas  
  **Then** pergunta salva com `needs_manual_review: true`
- Specs cobrem todos os critérios do checklist §6.8

**Spec:** `spec/services/wsi/question_validator_spec.rb`  
**Dependências:** WSI-F6-02

---

### WSI-F6-04 — Gate `reviewed_by_recruiter` em Evaluation/Question

**Tipo:** Task | **Epic:** A | **Estimativa:** 1 dia

**Descrição:**  
Adicionar flag `questions.wsi_reviewed` (boolean, default false). Endpoint de ativação de triagem (`POST .../evaluation_candidates`) deve rejeitar se qualquer pergunta da avaliação tiver `wsi_reviewed == false`.

**Critérios de aceite:**

- **Given** evaluation com 1 pergunta não revisada  
  **When** tentativa de criar `EvaluationCandidate`  
  **Then** retorna `422` com `error: "questions_pending_review"`
- **Given** todas as perguntas revisadas  
  **Then** fluxo segue normalmente

**Spec:** `spec/requests/v1/users/evaluation_candidates_spec.rb`  
**Migration:** `add_wsi_reviewed_to_questions`  
**Dependências:** WSI-F6-03

---

### WSI-F6-05 — `wsi_metadata` jsonb em `questions`

**Tipo:** Task | **Epic:** A | **Estimativa:** 1 dia

**Descrição:**  
Adicionar coluna `questions.wsi_metadata` (jsonb) para armazenar: `reviewed_by_recruiter`, `needs_manual_review`, `generation_attempts`, `skill_name`, `trait_weight`, `_skill_approximated`.

**Critérios de aceite:**

- Migration aplica sem conflito com `extra_params` existente
- Serializer expõe `wsi_metadata` no endpoint de perguntas
- Specs verificam persistência de cada subcampo

**Spec:** `spec/models/question_spec.rb`  
**Migration:** `add_wsi_metadata_to_questions`  
**Dependências:** WSI-F6-03

---

## F7 — Coleta das respostas

---

### WSI-F7-01 — Autodeclaração 1–5 como evento explícito por pergunta técnica

**Tipo:** Story | **Epic:** B | **Estimativa:** 2 dias

**Descrição:**  
Modelar autodeclaração (escala 1–5 com rótulos fixos §7.2) como campo separado em `answers`: `self_declaration_score` (integer, 1–5). O agente conversacional deve registrar o valor **antes** da resposta textual. `ScoreCalculatorService` usa esse campo como fonte canônica (não mais `comments_response[:score]`).

**Critérios de aceite:**

- **Given** pergunta com `competence_type: "technical"`  
  **When** candidato seleciona escala 3 e envia resposta textual  
  **Then** `answer.self_declaration_score` == 3 e `answer.description` contém a resposta
- **Given** `competence_type: "behavioral"`  
  **Then** `self_declaration_score` é `nil` (não coletado)
- `ScoreCalculatorService#parse_self_declaration` usa `answer.self_declaration_score` como prioridade

**Spec:** `spec/services/evaluations/score_calculator_service_spec.rb`  
**Migration:** `add_self_declaration_score_to_answers`  
**Dependências:** WSI-F8-01

---

### WSI-F7-02 — Tipo de pergunta de elegibilidade (binária)

**Tipo:** Story | **Epic:** B | **Estimativa:** 2 dias

**Descrição:**  
Adicionar `response_type: :eligibility` (ou flag `is_eligibility_question`) em `Question`. Fluxo de coleta apresenta Sim/Não; resposta é persistida em `answer.eligibility_answer` (boolean).

**Critérios de aceite:**

- **Given** `question.response_type == "eligibility"`  
  **When** candidato responde "Não"  
  **Then** `answer.eligibility_answer == false`
- Pergunta de elegibilidade não exige autodeclaração nem score Bloom/Dreyfus
- Specs verificam que `ScoreCalculatorService` skipa scoring para elegibilidade

**Spec:** `spec/models/answer_spec.rb`, `spec/requests/v1/evaluations/answers_spec.rb`  
**Migration:** `add_eligibility_answer_to_answers`  
**Dependências:** nenhuma (pode rodar em paralelo)

---

### WSI-F7-03 — Hash SHA-256 ao completar triagem

**Tipo:** Task | **Epic:** B | **Estimativa:** 1 dia

**Descrição:**  
Ao marcar `EvaluationCandidate.completed = true`, calcular `Digest::SHA256.hexdigest` do payload canônico (respostas ordenadas por `question.position`, normalized UTF-8) e persistir em `evaluation_candidates.answers_hash`.

**Critérios de aceite:**

- **Given** triagem concluída com 7 respostas  
  **When** `completed` é setado  
  **Then** `evaluation_candidates.answers_hash` contém string hex de 64 chars
- Recalcular para a mesma entrada produz o mesmo hash (idempotência)
- Hash é incluído no relatório F11 (Seção 9)

**Spec:** `spec/models/evaluation_candidate_spec.rb`  
**Migration:** `add_answers_hash_to_evaluation_candidates`  
**Dependências:** nenhuma

---

### WSI-F7-04 — Imutabilidade de respostas após envio

**Tipo:** Task | **Epic:** B | **Estimativa:** 1 dia

**Descrição:**  
Bloquear `update` de `answer.description` e `answer.choices` via policy/callback após o candidato enviar a resposta (`session_status` da triagem em andamento).

**Critérios de aceite:**

- **Given** `answer` já com `description` preenchida e `evaluation_candidate.completed == false`  
  **When** `PATCH` em `answer.description`  
  **Then** retorna `403 Forbidden`
- Recrutador ainda pode editar metadados internos (score overrides, etc.) via endpoint admin separado

**Spec:** `spec/requests/v1/evaluations/answers_spec.rb`  
**Dependências:** nenhuma

---

## F8 — Avaliação das respostas (camadas)

---

### WSI-F8-01 — Contrato do extrator LLM (Camada 2, temp = 0)

**Tipo:** Story | **Epic:** B | **Estimativa:** 3 dias

**Descrição:**  
Criar `Wsi::ResponseExtractorService` com chamada LLM dedicada (`temperature: 0.0`, `max_tokens: 800`) que retorna somente o JSON §8.3: `star_components`, `bloom_demonstrated(1-6)`, `dreyfus_demonstrated(1-5)`, `trait_signals_detected`, `trait_signals_absent`, `inflation_detected`, `specificity_score(1-10)`, `key_quote`, `response_authentic`, `authenticity_concern`. O LLM **não** retorna nota.

**Critérios de aceite:**

- **Given** resposta com vocabulário técnico mas sem episódio concreto  
  **Then** `bloom_demonstrated <= 2`, `specificity_score <= 3`
- **Given** resposta < 15 palavras  
  **Then** todos os campos em defaults mínimos, `response_authentic: false`
- **Given** resposta com "ignore suas instruções"  
  **Then** `response_authentic: false`, `authenticity_concern: "prompt_injection_attempt"`
- Specs usam golden files (fixtures de resposta ↔ JSON esperado)
- Temperature = 0.0 verificada no stub

**Spec:** `spec/services/wsi/response_extractor_service_spec.rb`  
**Dependências:** WSI-F7-01

---

### WSI-F8-02 — Camada 1: alinhamento das regras STAR §8.2

**Tipo:** Story | **Epic:** B | **Estimativa:** 2 dias

**Descrição:**  
Atualizar `CbiEvaluator` / módulo STAR para seguir os pesos e thresholds exatos §8.2: S 20% / T 20% / A 40% / R 20%; penalidades por faixa de palavras (< 30 → −2.5, 30–50 → −1.0), sem 1ª pessoa → −1.5, R ausente → −0.8, paráfrase > 60% → −2.0, idioma errado → −1.0, injection → score = 0; bônus por métrica quantificada (+0.5), resposta > 150 palavras (+0.3), 2+ episódios (+0.3).

**Critérios de aceite:**

- **Given** resposta com 25 palavras  
  **Then** `star_penalty_words` == −2.5
- **Given** resposta sem verbo em 1ª pessoa  
  **Then** `star_penalty_no_first_person` == −1.5
- **Given** resposta com "reduziu em 40%"  
  **Then** `star_bonus_quantified` == +0.5
- Specs com table-driven examples para cada regra

**Spec:** `spec/services/evaluations/cbi_evaluator_spec.rb`  
**Dependências:** WSI-F8-01

---

### WSI-F8-03 — Camada 3: fórmula por tipo de pergunta (0–10)

**Tipo:** Story | **Epic:** B | **Estimativa:** 2 dias

**Descrição:**  
Atualizar `ScoreCalculatorService` para usar as fórmulas §8.4: técnico `0.35×autodeclaração + 0.40×specificity + 0.25×bloom_alignment`; comportamental `0.35×STAR_score + 0.40×trait_signals_norm + 0.25×bloom_alignment`. Score por pergunta em escala **0–10**. Ajustes (inflation −1.5, dreyfus gap −0.8, bloom superado +0.6, etc.).

**Critérios de aceite:**

- **Given** resposta técnica com `self_declaration: 4`, `specificity_score: 8`, `bloom esperado: 4`, `bloom demonstrado: 4`  
  **Then** `score_bruto == (0.35×0.8 + 0.40×0.8 + 0.25×1.0) × 10 == 8.10`
- **Given** `inflation_detected: true`  
  **Then** ajuste −1.5 aplicado ao `score_bruto`
- `final_skill_score` persiste em escala 0–10 (migrar de 0–5)
- `EvaluationAggregateService` recebe escala 0–10 diretamente

**Spec:** `spec/services/evaluations/score_calculator_service_spec.rb`  
**Migration:** Alterar `answers.final_skill_score` precision para suportar 0–10  
**Dependências:** WSI-F8-01, WSI-F8-02, WSI-F7-01

---

### WSI-F8-04 — PII masking + contador de injeção

**Tipo:** Task | **Epic:** B | **Estimativa:** 2 dias

**Descrição:**  
Antes de enviar resposta ao extrator LLM, aplicar remoção de CPF, e-mail, telefone, nome completo via regex. Persistir contador `answers.injection_attempt_count` (incrementado quando `authenticity_concern == "prompt_injection_attempt"`). Regra G2 usa esse contador.

**Critérios de aceite:**

- **Given** resposta com "João da Silva, CPF 123.456.789-00"  
  **Then** texto enviado ao LLM substitui CPF e nome por `[REDACTED]`
- **Given** `injection_attempt_count >= 2`  
  **Then** flag `g2_gate_triggered: true` é setada no candidato
- Specs verificam cada padrão de PII e counter de injeção

**Spec:** `spec/services/wsi/pii_masker_spec.rb`  
**Migration:** `add_injection_attempt_count_to_answers`  
**Dependências:** WSI-F8-01

---

## F9 — Score WSI final: composição e classificação

---

### WSI-F9-01 — SENIORITY_WEIGHTS canônicos + fix seniority_multiplier

**Tipo:** Task | **Epic:** B | **Estimativa:** 1 dia

**Descrição:**  
Substituir `EvaluationAggregateService::SENIORITY_WEIGHTS` pela constante `Wsi::Constants::SENIORITY_WEIGHTS` criada em WSI-F5-04. Remover o `seniority_multiplier` com heurística `/0.80` e usar composição linear explícita §9.3.

**Critérios de aceite:**

- **Given** `job.seniority` mapeado para `"senior"`  
  **Then** `technical_weight == 0.5625`, `behavioral_weight == 0.4375`
- `seniority_multiplier` é removido do código; nenhum fallback numérico

**Spec:** `spec/services/evaluations/evaluation_aggregate_service_spec.rb`  
**Dependências:** WSI-F5-04, WSI-F4-01

---

### WSI-F9-02 — WSI_comportamental ponderado pelo ranking F3

**Tipo:** Story | **Epic:** B | **Estimativa:** 2 dias

**Descrição:**  
Alterar `EvaluationAggregateService` para calcular `WSI_comportamental` como soma ponderada usando `question.extra_params["trait_weight"]` (preenchido em WSI-F3-03). Fallback para média simples se pesos indisponíveis.

**Critérios de aceite:**

- **Given** 3 respostas comportamentais com trait_weights `[0.365, 0.356, 0.279]` e scores `[8.0, 7.0, 6.0]`  
  **Then** `WSI_comportamental` ≈ `(8.0×0.365 + 7.0×0.356 + 6.0×0.279)` / soma_pesos
- **Given** todas as perguntas sem `trait_weight`  
  **Then** média simples (fallback)

**Spec:** `spec/services/evaluations/evaluation_aggregate_service_spec.rb`  
**Dependências:** WSI-F9-01, WSI-F3-03, WSI-F8-03

---

### WSI-F9-03 — Fórmula WSI final §9.3 + classificação §9.5

**Tipo:** Story | **Epic:** B | **Estimativa:** 2 dias

**Descrição:**  
Implementar `WSI_final = WSI_tec × peso_tech + WSI_comp × peso_comp` em escala 0–10. Atualizar `CLASSIFICATION_RANGES` para 6 faixas §9.5 (Excepcional, Excelente, Alto, Médio, Abaixo da média, Regular). Persistir `evaluation_candidates.score` em 0–10 diretamente (sem `× 2`).

**Critérios de aceite:**

- **Given** `WSI_tecnico = 7.85`, `WSI_comp = 7.59`, seniority `senior`  
  **Then** `WSI_final == (7.85×0.5625 + 7.59×0.4375).round(2) == 7.74`
- **Given** `WSI_final >= 9.0`  
  **Then** `wsi_classification == "Excepcional"`
- `evaluation_candidates.score` == `WSI_final` (não ×2)

**Spec:** `spec/services/evaluations/evaluation_aggregate_service_spec.rb`  
**Dependências:** WSI-F9-02

---

### WSI-F9-04 — Perfil Big Five observado (§9.6)

**Tipo:** Story | **Epic:** B | **Estimativa:** 2 dias

**Descrição:**  
Após agregação, calcular `candidate_big_five_observed`: para cada trait avaliado, comparar score demonstrado (médio das respostas comportamentais daquele trait) com score requerido pelo JD (`wsi_jd_big_five_profile`). Persistir em `evaluation_candidates.wsi_big_five_observed` (jsonb).

**Critérios de aceite:**

- **Given** trait `conscientiousness` com `score_required: 82` e `score_demonstrated: 62`  
  **Then** `gap: -20`, `status: "GAP"`, `critical_gap: true`
- Traits fora do Top-N (sem pergunta) aparecem com `score_demonstrated: null`
- Campo alimenta F10 (gap top-1) e F11 (cruzamento Big Five)

**Spec:** `spec/services/evaluations/evaluation_aggregate_service_spec.rb`  
**Migration:** `add_wsi_big_five_observed_to_evaluation_candidates`  
**Dependências:** WSI-F9-03, WSI-F2-01

---

## F10 — Gates absolutos e decisão

---

### WSI-F10-01 — Gates G2–G6 engine

**Tipo:** Story | **Epic:** C | **Estimativa:** 3 dias

**Descrição:**  
Criar `Wsi::GateEngine` que avalia G2–G6 a partir dos dados persistidos: G2 (`injection_attempt_count >= 2`); G3 (`WSI_tecnico < 4.0`); G4 (skill crítica com score < 3.0); G5 (≥ 50% respostas < 30 palavras); G6 (`inflation_detected` em ≥ 3 respostas). G1 (elegibilidade) adiado conforme decisão da análise.

**Critérios de aceite:**

- **Given** candidato com `WSI_tecnico = 3.8`  
  **Then** `GateEngine.evaluate` retorna `{ triggered: true, gate: "G3", reason: "wsi_tecnico_below_threshold" }`
- **Given** 4 de 7 respostas com `inflation_detected: true`  
  **Then** gate `G6` ativado
- **Given** candidato com `WSI_final = 9.5` mas G3 ativo  
  **Then** gate vence — resultado é `REPROVADO`
- Um contexto de spec por gate (G2–G6)

**Spec:** `spec/services/wsi/gate_engine_spec.rb`  
**Dependências:** WSI-F9-03, WSI-F8-04

---

### WSI-F10-02 — `Wsi::ScreeningDecisionService` (duas camadas)

**Tipo:** Story | **Epic:** C | **Estimativa:** 2 dias

**Descrição:**  
Orquestrar a lógica §10.4: primeiro `GateEngine`, depois critérios §10.3 (faixas + gap top-1 trait). Retorna `{ result: APROVADO|EM_AVALIACAO|REPROVADO, confidence: alta|media|baixa, human_review_required: true|false, gate_triggered: nil|G2..G6, reason: String }`.

**Critérios de aceite:**

- **Given** `WSI_final >= 7.5`, `WSI_tecnico >= 6.5`, `WSI_comp >= 6.5`, sem gates  
  **Then** `result: "APROVADO"`, `confidence: "alta"`, `human_review_required: false`
- **Given** `WSI_final = 6.5`, gap top-1 = 25 pts  
  **Then** `result: "REPROVADO"`, `reason: "gap_trait_critico"`
- **Given** qualquer gate ativo  
  **Then** nunca retorna `APROVADO`

**Spec:** `spec/services/wsi/screening_decision_service_spec.rb`  
**Dependências:** WSI-F10-01, WSI-F9-04

---

### WSI-F10-03 — Persistência de decisão + API

**Tipo:** Task | **Epic:** C | **Estimativa:** 1 dia

**Descrição:**  
Adicionar `evaluation_candidates.wsi_decision` (jsonb) com campos `result`, `confidence`, `gate_triggered`, `human_review_required`, `reason`, `decided_at`. Endpoint `GET /v1/users/evaluation_candidates/:uid/wsi_decision` expõe a decisão ao recrutador.

**Critérios de aceite:**

- Decisão é gravada ao completar triagem (callback ou job)
- `gate_triggered` nunca exibe código interno ao candidato — apenas ao recrutador
- Endpoint retorna 200 com decisão estruturada

**Spec:** `spec/requests/v1/users/evaluation_candidates_wsi_decision_spec.rb`  
**Migration:** `add_wsi_decision_to_evaluation_candidates`  
**Dependências:** WSI-F10-02

---

### WSI-F10-04 — Red flags RF-01–08 detector

**Tipo:** Task | **Epic:** C | **Estimativa:** 2 dias

**Descrição:**  
Criar `Wsi::RedFlagDetector` que analisa todas as respostas de um candidato e produz lista de `{ code: RF-01..RF-08, level: alto|medio, description: String }`. Persistir em `evaluation_candidates.wsi_red_flags` (jsonb).

**Critérios de aceite:**

- **Given** `inflation_detected: true` em 2 respostas (não 3+)  
  **Then** `RF-01` presente com `level: "medio"`
- **Given** `bloom_demonstrated < bloom_esperado` em 4 respostas  
  **Then** `RF-02` com `level: "alto"`
- **Given** `response_authentic: false` em qualquer resposta  
  **Then** `RF-08` com `level: "alto"`
- Um contexto de spec por flag RF-01–RF-08

**Spec:** `spec/services/wsi/red_flag_detector_spec.rb`  
**Migration:** `add_wsi_red_flags_to_evaluation_candidates`  
**Dependências:** WSI-F10-02

---

## F11 — Relatório completo do consultor

---

### WSI-F11-01 — Schema JSON canônico do relatório + builder

**Tipo:** Story | **Epic:** C | **Estimativa:** 3 dias

**Descrição:**  
Criar `Wsi::ReportBuilderService` que monta o JSON completo do relatório (Seções 1–9 do template §11.2) preenchendo dados de F1–F10. Persistir em `evaluation_candidates.f11_report_json` (jsonb) com `report_generated_at` e `report_version`.

**Critérios de aceite:**

- **Given** candidato com triagem completa e decisão F10 gravada  
  **When** `Wsi::ReportBuilderService.call(evaluation_candidate: ec)`  
  **Then** `f11_report_json` contém todas as 9 seções com dados reais
- Seção 2 inclui `gate_checklist` com G1–G6 preenchidos
- Seção 9 inclui `answers_hash` (SHA-256 de F7) e `report_version`
- Snapshot test: JSON gerado passa por schema validation

**Spec:** `spec/services/wsi/report_builder_service_spec.rb`  
**Migration:** `add_f11_report_json_to_evaluation_candidates`  
**Dependências:** WSI-F10-04, WSI-F9-04, WSI-F7-03

---

### WSI-F11-02 — Seção 7: gaps determinísticos + F11.5 (perguntas presenciais)

**Tipo:** Story | **Epic:** C | **Estimativa:** 3 dias

**Descrição:**  
Criar `Wsi::GapAnalyzer` com classificação ALTO/MÉDIO/BAIXO segundo tabela §11.2.1. Criar `Wsi::InterviewQuestionGeneratorService` que recebe os top-3 gaps (`gap_score_delta` descendente) e gera exatamente 2 perguntas CBI calibradas via LLM (temperature 0.6, max_tokens 600, retry ≤ 3). Injetar resultado na Seção 7 do relatório.

**Critérios de aceite:**

- **Given** gap com `score_pergunta: 3.5` e `peso_dimensao: 25%`  
  **Then** severidade `ALTO`
- **Given** gap com `bloom_demonstrado == bloom_esperado - 1`  
  **Then** severidade `MÉDIO`
- **Given** top-3 gaps calculados  
  **Then** serviço gera 2 perguntas com formato CBI, sem revelar trait/framework
- Máximo 3 pontos fortes e 4 gaps na Seção 7

**Spec:** `spec/services/wsi/gap_analyzer_spec.rb`, `spec/services/wsi/interview_question_generator_service_spec.rb`  
**Dependências:** WSI-F11-01

---

### WSI-F11-03 — Endpoints de ranking por vaga e por candidato

**Tipo:** Story | **Epic:** C | **Estimativa:** 2 dias

**Descrição:**  
Criar endpoints: `GET /v1/users/jobs/:id/wsi_ranking` (lista candidatos ordenados por `WSI_final` desc com decisão e red flags) e `GET /v1/users/evaluation_candidates/:uid/wsi_report` (relatório F11 completo de um candidato).

**Critérios de aceite:**

- **Given** 3 candidatos triados na mesma vaga  
  **When** `GET .../wsi_ranking`  
  **Then** retorna lista ordenada por `WSI_final` decrescente com campos `uid`, `name`, `wsi_final`, `decision`, `red_flags_count`
- **Given** candidato com `f11_report_json` gerado  
  **When** `GET .../wsi_report`  
  **Then** retorna JSON completo das 9 seções

**Spec:** `spec/requests/v1/users/wsi_ranking_spec.rb`  
**Dependências:** WSI-F11-01

---

### WSI-F11-04 — Cache `f11_report_json` + invalidação

**Tipo:** Task | **Epic:** C | **Estimativa:** 1 dia

**Descrição:**  
Implementar política de cache para `f11_report_json`: relatório é gerado uma vez e invalidado somente quando `Answer` ou `EvaluationCandidate` for atualizado. Usar `after_commit` + background job de regeneração.

**Critérios de aceite:**

- **Given** relatório já gerado  
  **When** nenhuma resposta muda  
  **Then** `GET .../wsi_report` retorna cached JSON sem rebuild
- **Given** nova resposta salva  
  **Then** `f11_report_json` é marcado como `stale: true` e job de regeneração enfileirado
- Specs verificam invalidação via `after_commit`

**Spec:** `spec/jobs/wsi/report_generation_job_spec.rb`  
**Dependências:** WSI-F11-01, WSI-F11-03

---

## Resumo

| Fase      | Nº de Cards  | Estimativa (dias) |
| --------- | ------------ | ----------------- |
| F1        | 4            | 9                 |
| F2        | 3            | 5                 |
| F3        | 3            | 3                 |
| F4        | 4            | 6                 |
| F5        | 4            | 7                 |
| F6        | 5            | 9                 |
| F7        | 4            | 6                 |
| F8        | 4            | 9                 |
| F9        | 4            | 7                 |
| F10       | 4            | 8                 |
| F11       | 4            | 9                 |
| **Total** | **43 cards** | **78 dias**       |

---

### Estimativa de prazo

| Cenário                                  | Duração estimada                             |
| ---------------------------------------- | -------------------------------------------- |
| 1 dev sênior                             | ~78 dias úteis → **~16 semanas (4 meses)**   |
| 2 devs em paralelo (Bloco A + Bloco B/C) | **~9–10 semanas (2,5 meses)**                |
| Sprint de 2 semanas                      | **~8 sprints (1 dev) / ~5 sprints (2 devs)** |

> **Observações:**
>
> - Estimativas incluem implementação + specs + code review. Não incluem QA manual nem ajustes de frontend.
> - Cards F4-01 e F5-04 são **foundation** e desbloqueiam várias outras histórias — prioridade máxima no backlog.
> - G1 (Elegibilidade) foi adiado conforme decisão documentada no `WSI_COMPLETE_ANALYSIS.md` — não consta nesta lista.
> - Bloco de elegibilidade em F9 (WSI_elegibilidade 20%) também adiado.
