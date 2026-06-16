# Plano de Consolidação WSI — conversacional → kernel canônico cv_screening

**Decisão (Paulo 2026-05-31):** eliminar o fork WSI do `job_creation`; o conversacional
passa a usar o kernel canônico `cv_screening.WSIService` (+ `jd_generator_service` /
`/jd-evaluate` para JD+score) via **Anticorruption Layer (adapter)**. Orquestração do
wizard (HITL, painéis, streaming, tools) PERMANECE no `job_creation`/orquestrador.

## Princípio (DDD + DRY + harness)
- WSI = **Shared Kernel** (uma metodologia, um lugar). Bounded contexts (cv_screening =
  triar candidato; job_creation = criar vaga) consomem o kernel via adapter.
- Metodologia (gerar CBI, extrair Big Five, score 9-dim, sugerir competências) = canônico.
- Orquestração (HITL editar/regenerar/remover, painel, modo, streaming) = wizard.
- Drift já provado (scores diferentes, contagem 6/7, gerador gemini quebrado) = risco de
  compliance (fix de fairness num lado não chega ao outro). Consolidar elimina.

## Matriz de paridade (Fase 0 — concluída)
| Capacidade | Canônico cv_screening | Fork job_creation | Ação |
|---|---|---|---|
| Sugestão competências | analyze_jd_and_suggest_competencies → CompetencySuggestion | CompetencyBenchmarkService | repontar (Fase 1) |
| Geração perguntas WSI 7/12 | WSIService.generate_screening_questions / generate_from_simple_inputs | WSIQuestionGenerator | repontar (Fase 2) |
| Big Five | analyze_jd / WSIQuestion.big_five_mapping | extract_bigfive | repontar (Fase 2) |
| JD enriquecido | jd_generator_service (dados empresa+seções) | JdEnrichmentService | Fase 3 |
| Score JD | /jd-evaluate 9 dimensões (classify_wsi_score) | calculate_quality_score | Fase 3 |
| skill_probed (taxonomia) | ❌ gap | ✅ | manter no adapter (analytics) |
| single-question (edit/add HITL) | ❌ gap | ✅ generate_single_question | manter no adapter (wizard-específico) |
| FairnessGuard L1/L3 explícito | provável via c3b boundary | ✅ | verificar; preservar |

## Drift de vocabulário de senioridade (descoberto — corrigir no adapter)
- cv_screening: junior|pleno|senior|lead|executive (5)
- FE cadastro: Estágio|Júnior|Pleno|Sênior|Especialista|Coordenador|Gerente|Diretor (8)
- WSI resolver: estagiario|junior|pleno|senior|lead|principal|diretor (7)
→ adapter normaliza wizard→cv_screening (5 níveis) na entrada; vacancy_vocab já cobre FE na saída.

## Adapter (Anticorruption Layer)
`app/domains/job_creation/orchestrator/wsi_canonical_adapter.py` — funções que chamam o
cv_screening.WSIService e mapeiam schemas canônicos → shapes do wizard:
- Competency(name,type,big_five_mapping) → wizard {skill}/{competencia,trait_big_five}
- WSIQuestion(bloom_level,dreyfus_level,trait_ocean,...) → wizard wsi_questions dict
- Mapeamento de senioridade wizard→cv_screening (5 níveis).
- run_coro_in_threadpool (async→sync nos tools).

## Fases
- **Fase 1 (POC + valor, baixo risco):** suggest_competencies → adapter → cv_screening.
  analyze_jd_and_suggest_competencies. Mantém confirm_competencies. Prova o padrão adapter.
- **Fase 2:** generate_wsi_questions + Big Five → adapter → cv_screening.WSIService.
  generate_from_simple_inputs. HITL (edit/add/remove/regenerate) fica no wizard; single-question
  surgical permanece no fork OU sobe pro canônico (decidir). skill_probed no adapter.
- **Fase 3:** enrich_job_description → jd_generator_service (dados empresa+seções) +
  score 9-dim (extrair classify_wsi_score p/ função compartilhada). Preservar relatório
  fairness/mudanças (Paulo gosta).
- **Fase 4:** deprecar fork job_creation WSI (WSIQuestionGenerator, CompetencyBenchmarkService
  no caminho do wizard, calculate_quality_score) após paridade validada.

## Sensores (harness, cada fase)
- TDD: testes de mapeamento de schema (canônico→wizard) com canônico mockado.
- Sensor anti-regressão: grep que o wizard não importa o fork após deprecação (Fase 4).
- Smoke E2E por fase contra o serviço canônico real.

## Rollback
Cada fase atrás de flag/feature isolada; adapter permite reverter o tool para o fork se needed.
