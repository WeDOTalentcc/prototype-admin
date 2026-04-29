# JIRA Cards — Fairness Guard para Sugestões de Job Description e Perguntas

Cards gerados a partir do plano em `fairness_job_description_and_questions.md`.

---

## Card 1 — Criar JobFairnessGuard (Core)

**Prioridade:** Alta  
**Tipo:** Story  
**Labels:** fairness, job-suggestions, guard  
**Épico:** Fairness Guard

**Descrição:**  
Criar o módulo `JobFairnessGuard` em Ruby como port do `fairness.py` em Python. Responsabilidades: constantes de filtros bloqueados, validação de filtros, seções de fairness para prompts e disclaimers.

**Acceptance Criteria:**
- [ ] Criar `app/lib/job_fairness_guard.rb` (ou `app/services/fairness/job_fairness_guard.rb`)
- [ ] Definir constantes `BLOCKED_FILTERS` e `PCD_CONTEXT_REQUIRED` (paridade com Python)
- [ ] Implementar `check_filters(params, job_context)` retornando `[allowed, error_message]`
- [ ] Implementar `get_matching_disclaimer` e `get_bulk_action_disclaimer`
- [ ] Criar spec unitário em `spec/lib/job_fairness_guard_spec.rb`

**Contexto técnico:** Referência `fairness.py` em Python; filtros bloqueados: gender, age, race, religion, marital, etc.

---

## Card 2 — prompt_fairness_section para Job Description e Skills

**Prioridade:** Alta  
**Tipo:** Story  
**Labels:** fairness, job-suggestions, prompts  
**Épico:** Fairness Guard  
**Dependência:** Card 1

**Descrição:**  
Implementar método `prompt_fairness_section(job_context:)` que retorna texto a ser injetado em prompts de LLM para job description e skills. Instrui o modelo a não gerar conteúdo discriminatório (gênero, idade, raça, religião, estado civil).

**Acceptance Criteria:**
- [ ] Implementar `prompt_fairness_section(job_context: {})` em `JobFairnessGuard`
- [ ] Incluir instruções claras para evitar conteúdo discriminatório
- [ ] Aceitar `job_context` vazio ou com `disabilities` para extensibilidade
- [ ] Cobrir com testes unitários

**Contexto técnico:** Usado em prompts de `description`, `skills`, `behavioral_skills`, `title` (opcional).

---

## Card 3 — prompt_fairness_section_for_questions com Regra PCD

**Prioridade:** Alta  
**Tipo:** Story  
**Labels:** fairness, screening-questions, pcd  
**Épico:** Fairness Guard  
**Dependência:** Card 1

**Descrição:**  
Implementar método `prompt_fairness_section_for_questions(job_context:)` específico para perguntas de triagem. Deve incluir regra PCD: se `job_context[:disabilities] == true`, permitir perguntas de elegibilidade PCD; caso contrário, instruir "Não inclua perguntas sobre deficiência ou PCD".

**Acceptance Criteria:**
- [ ] Implementar `prompt_fairness_section_for_questions(job_context: {})` em `JobFairnessGuard`
- [ ] Quando `disabilities == true`: incluir instrução permitindo perguntas de elegibilidade PCD
- [ ] Quando `disabilities == false` ou ausente: incluir instrução proibindo perguntas sobre deficiência ou PCD
- [ ] Incluir instruções gerais de fairness (gênero, idade, raça, etc.)
- [ ] Cobrir com testes unitários

**Contexto técnico:** Usado em prompts de `questions` e `evaluation_questions`; paridade com `PCD_CONTEXT_REQUIRED` em Python.

---

## Card 4 — Garantir disabilities em build_job_data e @data

**Prioridade:** Alta  
**Tipo:** Tech Task  
**Labels:** fairness, job-suggestions, data  
**Épico:** Fairness Guard

**Descrição:**  
Para injetar a seção de fairness corretamente nas perguntas, é necessário que `disabilities` esteja disponível no contexto. Garantir que `@data` e `build_job_data_for_evaluation` exponham `disabilities` quando houver `job` ou `job_id`.

**Acceptance Criteria:**
- [ ] `build_job_data_for_evaluation` inclui `disabilities: job.disabilities`
- [ ] `@data` inclui `disabilities` quando houver dados parciais (create)
- [ ] Para `create` sem job: usar `@data[:disabilities]` ou `false` se ausente
- [ ] Para `generate_evaluation_questions(job)` e fluxos com `job_id`: passar `disabilities: job.disabilities`

**Contexto técnico:** `JobSuggestionService`; `SuggestionsController`; método `build_job_data_for_evaluation`.

---

## Card 5 — Injetar Fairness em Prompts do JobSuggestionService

**Prioridade:** Alta  
**Tipo:** Story  
**Labels:** fairness, job-suggestions, integration  
**Épico:** Fairness Guard  
**Dependência:** Cards 1, 2, 3, 4

**Descrição:**  
Integrar as seções de fairness nos prompts do `JobSuggestionService`. Em `build_prompt`, após obter o prompt base, concatenar a seção de fairness apropriada conforme o tipo de sugestão.

**Acceptance Criteria:**
- [ ] `prompt_for_description`: adicionar `prompt_fairness_section`
- [ ] `prompt_for_skills`: adicionar `prompt_fairness_section`
- [ ] `prompt_for_behavioral_skills`: adicionar `prompt_fairness_section`
- [ ] `prompt_for_questions`: adicionar `prompt_fairness_section_for_questions`
- [ ] `prompt_for_evaluation_questions`: adicionar `prompt_fairness_section_for_questions`
- [ ] `prompt_for_title`: (opcional) adicionar `prompt_fairness_section` para consistência
- [ ] Construir `job_context` com `disabilities` conforme disponibilidade
- [ ] Adicionar testes em spec do `JobSuggestionService` verificando inclusão das seções

**Contexto técnico:** `app/services/job_suggestion_service.rb`; método `build_prompt`.

---

## Card 6 — Garantir disabilities no SuggestionsController

**Prioridade:** Média  
**Tipo:** Tech Task  
**Labels:** fairness, controller, api  
**Épico:** Fairness Guard

**Descrição:**  
O controller deve passar `disabilities` para o `JobSuggestionService` quando houver `job` associado à requisição. Garantir que o fluxo de sugestões receba o contexto correto.

**Acceptance Criteria:**
- [ ] Quando existir `job` ou `job_id`, extrair `job.disabilities` e incluir em `@data` ou parâmetros do service
- [ ] Documentar no controller ou doc interna como o fairness é aplicado
- [ ] Validar em testes de request ou service

**Contexto técnico:** `app/controllers/v1/users/jobs/suggestions_controller.rb`.

---

## Card 7 — Documentação docs/fairness_guard.md

**Prioridade:** Média  
**Tipo:** Documentation  
**Labels:** fairness, docs  
**Épico:** Fairness Guard

**Descrição:**  
Criar documentação em `docs/fairness_guard.md` descrevendo o uso do Fairness Guard em filtros e prompts, com exemplos para novos serviços que chamem LLM.

**Acceptance Criteria:**
- [ ] Criar `docs/fairness_guard.md`
- [ ] Descrever uso em filtros (`check_filters`)
- [ ] Descrever uso em prompts (`prompt_fairness_section`, `prompt_fairness_section_for_questions`)
- [ ] Incluir exemplo para novos serviços que chamem LLM
- [ ] Documentar constantes e métodos públicos
- [ ] Registrar em `.cursorrules` ou `AGENTS.md` que novos prompts de jobs/triagem devem incluir fairness

**Contexto técnico:** Padrão para extensões futuras; seção 5 do plano.

---

## Card 8 — scan_output_for_blocked_content (Validação Pós-LLM)

**Prioridade:** Baixa  
**Tipo:** Story  
**Labels:** fairness, validation, llm-output  
**Épico:** Fairness Guard (Extensão)

**Descrição:**  
Implementar validação opcional pós-LLM: detectar termos de `BLOCKED_FILTERS` no texto retornado. Se houver match, logar, retornar erro ou substituir por placeholder. Evitar falsos positivos (ex.: "idade mínima para dirigir" em contexto profissional).

**Acceptance Criteria:**
- [ ] Implementar `scan_output_for_blocked_content(text)` em `JobFairnessGuard`
- [ ] Detectar termos relacionados a `BLOCKED_FILTERS` no texto
- [ ] Definir ação: logar, retornar erro ou substituir por placeholder
- [ ] Implementar heurísticas para reduzir falsos positivos
- [ ] Documentar como feature opcional e quando usar

**Contexto técnico:** Seção 5.3 do plano; uso após chamadas LLM em `JobSuggestionService`.

---

## Card 9 — Integrar JobFairnessGuard em API de Busca (Filtros)

**Prioridade:** Média  
**Tipo:** Story  
**Labels:** fairness, search, filters  
**Épico:** Fairness Guard (Extensão)

**Descrição:**  
Se existir endpoint de busca com `where` (ex.: `matching_candidates`), integrar `JobFairnessGuard.check_filters(params, job_context)` para bloquear filtros discriminatórios e validar PCD conforme `job.disabilities`.

**Acceptance Criteria:**
- [ ] Identificar endpoints de busca que aceitam `where` ou filtros similares
- [ ] Chamar `JobFairnessGuard.check_filters(params, job_context)` antes de executar busca
- [ ] Retornar erro 422 (ou equivalente) com mensagem clara quando filtros forem bloqueados
- [ ] Passar `job_context` com `disabilities` quando aplicável
- [ ] Testes de request cobrindo cenários bloqueados e permitidos

**Contexto técnico:** Paridade com `fairness.py` em Python; filtros de candidatos.

---

## Card 10 — Estender Fairness a Outros Serviços (Candidates, ProfileAnalyzer, etc.)

**Prioridade:** Baixa  
**Tipo:** Story  
**Labels:** fairness, reuse, candidates  
**Épico:** Fairness Guard (Extensão)

**Descrição:**  
Reutilizar o `JobFairnessGuard` em outros serviços que chamem LLM para sugestões ou descrições: `Candidates::SuggestionService`, `ProfileAnalyzer`, `IntentBasedRefinementService`, `Evaluations::AiFeedbackService`, `SearchArchetypes::CreateFromDescriptionService`.

**Acceptance Criteria:**
- [ ] Mapear serviços que precisam de fairness (queries, descrições, feedbacks)
- [ ] Para `Candidates::SuggestionService`: injetar `prompt_fairness_section` em prompts de busca
- [ ] Para `ProfileAnalyzer`/`IntentBasedRefinementService`: `prompt_fairness_section` em descrições de candidatos ideais
- [ ] Para `Evaluations::AiFeedbackService`: garantir que feedbacks não mencionem atributos protegidos
- [ ] Para `SearchArchetypes::CreateFromDescriptionService`: `prompt_fairness_section` em descrições base
- [ ] Documentar padrão de uso em `docs/fairness_guard.md`

**Contexto técnico:** Seção 5.1 do plano; tabela de serviços e uso de fairness.

---

## Resumo de Priorização

| Prioridade | Cards |
|------------|-------|
| Alta       | 1, 2, 3, 4, 5 |
| Média      | 6, 7, 9 |
| Baixa      | 8, 10 |

### Ordem Sugerida de Implementação

1. **Fase 1 — Core:** Card 1 → Card 2 → Card 3  
2. **Fase 2 — Integração:** Card 4 → Card 5 → Card 6  
3. **Fase 3 — Documentação:** Card 7  
4. **Extensões:** Card 8, 9, 10 (conforme prioridade de produto)
