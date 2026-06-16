# WSI Skill Taxonomy — v3 (DRAFT, expanded vertical)

> **Status**: DRAFT v3 — pendente aprovacao final Paulo
> **Data**: 2026-05-03
> **Mudancas vs v2**:
>   - REMOVIDAS 4 skills com fairness flag (executive_communication, executive_presence, bias_interruption, founder_mindset_at_scale)
>   - EXPANDIDA Lideranca Tecnica de 7 para 14 skills
>   - ADICIONADA categoria 16: Saude & Bem-estar Clinico (8 skills)
>   - ADICIONADA categoria 17: Educacao & Pedagogia (7 skills)
>   - ADICIONADAS categorias 18-26: 9 verticais (Varejo/Logistica/Marketing/Eng Tradicional/Industria Pesada/Midia/Telecom/Pharma/AI Specialist)
> **Total**: 26 categorias parent, 196 skills filhos
> **Estrutura**: hierarquica 2 niveis (parent ativa rapido, skill refina)
> **Fontes**: O*NET + BEI + Lominger + frameworks vertical-specific (HCAHPS clinical, CPDLC telecom, ICH-GCP pharma, RICS engenharia, etc)

---

## Hierarquia 2 niveis - como o learning funciona

```
Pergunta gerada -> classificada em 1 skill_probed (filho)
                                        v
   Effectiveness aprende em 2 niveis simultaneos:

PARENT (26 categorias)              FILHO (196 skills)
~10 amostras/mes/parent             ~0.5-1 amostra/mes/skill
threshold em ~2 meses               threshold em ~12-24 meses
"categoria importa pra esta vaga?"  "skill especifica funciona?"
```

Runtime fallback chain:
1. filho >=20 amostras -> usa filho stats (mais especifico)
2. parent >=20 amostras -> fallback parent stats (mais rapido)
3. nenhum -> fallback prior O*NET (sem learning, defaults)

---

## Indice das 26 categorias parent

### Universais (15 categorias, 109 skills)

| # | Parent | # filhos | Foco |
|---|---|---|---|
| 1 | Comunicacao & Colaboracao | 9 | universal |
| 2 | Execucao & Entrega | 11 | universal |
| 3 | Aprendizado & Adaptacao | 7 | universal |
| 4 | Pensamento & Decisao | 9 | universal |
| 5 | Customer & Stakeholder | 7 | universal |
| 6 | Vendas & Influencia | 8 | comercial |
| 7 | Analise & Diagnostico | 8 | finance/legal/data |
| 8 | Operacoes & Processos | 7 | ops/admin/log |
| 9 | Compliance & Regulatorio | 6 | legal/finance/health |
| 10 | Inovacao & Empreendedorismo | 6 | produto/startup |
| 11 | Dominio Tecnico Cross-Tech | 8 | eng/dados |
| 12 | Gestao de Pessoas | 8 | RH + lideres |
| 13 | Lideranca Organizacional | 7 | C-level (sem executive_presence/founder) |
| 14 | Lideranca Tecnica | 14 | staff+ tech (expandida) |
| 15 | Cultura, Etica & Saude Mental | 7 | universal (sem bias_interruption) |

### Verticais (11 categorias, 87 skills)

| # | Parent | # filhos | Vertical |
|---|---|---|---|
| 16 | Saude & Bem-estar Clinico | 8 | medico/enfermagem/psicologia |
| 17 | Educacao & Pedagogia | 7 | professor/coordenador |
| 18 | Varejo & Customer-Facing | 7 | retail/loja/atendimento |
| 19 | Logistica & Supply Chain | 7 | logistica/armazem/transporte |
| 20 | Marketing & Branding | 8 | marketing/branding |
| 21 | Engenharia Tradicional | 7 | civil/mec/eletrica/quimica |
| 22 | Industria Pesada | 7 | oil&gas/manufatura/mineracao |
| 23 | Midia & Comunicacao | 7 | jornalismo/editorial/conteudo |
| 24 | Telecomunicacoes | 6 | telecom/redes/conectividade |
| 25 | Pharma & Life Sciences | 6 | farma/clinica/pesquisa |
| 26 | AI/ML Specialist | 7 | dados/ML/IA |

| **Total** | | **196** | |


---

## 1. Comunicacao & Colaboracao (parent: communication_collaboration) - 9 skills

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| active_listening | Captura e reflete antes de responder | Demanda confusa de stakeholder. Como confirmou? | jr+ | O*NET |
| async_communication_clarity | Mensagens auto-suficientes que dispensam follow-up | Documentou decisao complexa pra ler depois? | jr+ | Custom |
| synchronous_meeting_effectiveness | Conduz reuniao com objetivo + decisao + follow-up | Reuniao que voce liderou, produziu decisao? | pl+ | Lominger |
| cross_team_alignment | Constroi consenso entre times com objetivos diferentes | Quando alinhou 2+ times pra entrega comum? | sr+ | Custom |
| feedback_giving | Da feedback duro construtivo com exemplos | Vez que precisou dar feedback negativo. | pl+ | BEI |
| feedback_acceptance | Recebe critica direta sem se desestabilizar | Feedback duro recebido. Reacao? | jr+ | BEI |
| conflict_resolution | Trata desacordo sem escalada | Conflito recente com colega. | jr+ | O*NET |
| documentation_writing | Produz docs que outros usam sem perguntar | Doc que voce fez. Quem usou? | jr+ | Custom |
| internal_communication_strategy | Comunica change pra org grande | Comunicaria reorg pra 200 pessoas? | sr+ | Lominger |

## 2. Execucao & Entrega (parent: execution_delivery) - 11 skills

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| delivery_under_deadline_pressure | Cumpre prazo apertado sem comprometer qualidade | 1 semana pra algo de 1 mes. O que fez? | jr+ | BEI |
| prioritization_with_competing_demands | Escolhe entre demandas concorrentes | 3 tarefas urgentes, tempo pra 2. Como decide? | jr+ | O*NET |
| scope_management | Corta escopo quando necessario | Vez que entregou menos do que pediram. | pl+ | BEI |
| ownership_of_outcome | Assume resultado final, nao so esforco | Projeto que foi responsavel pelo resultado. | jr+ | BEI |
| recovery_from_failure | Reage construtivamente quando da errado | Incident em producao. O que mudou depois? | pl+ | Custom |
| attention_to_detail | Captura erros sutis antes do cliente | Bug que outros deixaram passar. | jr+ | O*NET |
| process_improvement | Identifica ineficiencia e implementa melhoria | Processo que mudou recentemente. | pl+ | O*NET |
| time_management | Organiza proprio tempo entre frentes | Dia tipico de 5+ frentes ativas. | jr+ | O*NET |
| quality_under_speed | Mantem qualidade quando velocidade aperta | Vez que cortou caminho. | pl+ | Custom |
| follow_through | Termina o que comecou, sem pontas soltas | Projeto longo do inicio ao fim sozinho. | jr+ | BEI |
| multi_project_juggling | Mantem 5+ projetos com prioridade variavel | Maior numero paralelo. Como balanceou? | pl+ | Lominger |

## 3. Aprendizado & Adaptacao (parent: learning_adaptation) - 7 skills

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| technical_self_learning | Aprende stack/ferramenta sem treinamento | Ultima vez aprendeu tech nova? | jr+ | Custom |
| domain_curiosity | Vai alem do escopo tecnico pra entender negocio | O que entende do negocio alem da sua area? | jr+ | BEI |
| adapting_to_change | Reage a pivos/reorgs/mudanca de prioridade | Projeto que pivotou no meio. | jr+ | O*NET |
| learning_from_failure | Extrai licao concreta de erro proprio | Maior erro. O que aprendeu? | jr+ | BEI |
| cross_domain_translation | Aplica conceito de uma area em outra | Aplicou algo aprendido fora do trabalho. | pl+ | Custom |
| proactive_skill_building | Identifica gaps e investe em fechar | Skill que precisa desenvolver. O que fez? | pl+ | BEI |
| continuous_learning_habit | Habito de aprendizado regular | Como aprende continuamente? | jr+ | Lominger |

## 4. Pensamento & Decisao (parent: thinking_decision) - 9 skills

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| data_driven_decision_making | Usa evidencia quantitativa | Decisao importante. Que dados consultou? | jr+ | O*NET |
| trade_off_articulation | Explica trade-offs com clareza | Escolheu X ou Y. Trade-offs reais? | pl+ | O*NET |
| root_cause_analysis | Investiga ate causa estrutural | Problema recorrente que resolveu. | pl+ | O*NET |
| ambiguity_tolerance | Avanca sem requisito 100% claro | Comecou projeto sem briefing completo. | jr+ | BEI |
| hypothesis_driven_thinking | Forma hipoteses testaveis | Como abordaria problema desconhecido? | pl+ | Custom |
| systems_thinking | Ve implicacoes de 2a ordem | Decisao com efeito secundario que viu antes. | sr+ | O*NET |
| decision_speed | Decide com 70% info | Decidiu rapido com pouca info. | pl+ | BEI |
| bias_awareness | Reconhece proprios viesses | Decisao em que sabia estar enviesado. | sr+ | O*NET |
| creative_problem_solving | Combina elementos nao-obvios | Solucao criativa fora do padrao. | pl+ | Lominger |

## 5. Customer & Stakeholder (parent: customer_stakeholder) - 7 skills

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| customer_empathy | Entende dor alem do que cliente articula | Cliente pediu X mas precisava Y. | jr+ | O*NET |
| stakeholder_management | Gerencia expectativas divergentes | Stakeholders queriam coisas opostas. | pl+ | O*NET |
| customer_advocacy | Defende cliente internamente | Vez que segurou decisao por causa do cliente. | pl+ | Custom |
| difficult_conversation_with_customer | Da bad news sem perder relacao | Bad news pra cliente. Como abordou? | pl+ | BEI |
| expectation_setting | Antecipa friccoes antes que virem problema | Cliente surpreendido neg. Como evitaria hoje? | pl+ | Lominger |
| cross_cultural_communication | Comunica eficaz entre culturas (BR/US/EU) | Trabalhar com cliente cultural diferente. | pl+ | O*NET |
| service_recovery | Recupera relacao apos algo dar errado | Cliente furioso. Como reverteu? | pl+ | BEI |

## 6. Vendas & Influencia (parent: sales_influence) - 8 skills

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| consultative_selling | Vende resolvendo problema, nao empurrando produto | Vez que vendeu algo dificil. | jr+ | O*NET |
| objection_handling | Lida com objecao sem ficar defensivo | Objecao mais dura. Como respondeu? | pl+ | Custom |
| negotiation_value_capture | Negocia valor, nao so preco | Negociacao dificil. Que alavancas usou? | pl+ | BEI |
| pipeline_discipline | Mantem disciplina de funil + forecast | Como organiza seu pipeline? | pl+ | Custom |
| account_expansion | Cresce conta existente | Conta que cresceu sob seu cuidado. | pl+ | Lominger |
| influence_without_authority | Move agenda sem ser chefe formal | Mudou direcao sem poder formal. | pl+ | BEI |
| presentation_skill | Apresenta variando registro/profundidade | Apresentacao que mudou opiniao da sala. | pl+ | O*NET |
| closing_under_resistance | Fecha quando cliente esta hesitante | Deal que quase nao fechou. | sr+ | Custom |

## 7. Analise & Diagnostico (parent: analysis_diagnosis) - 8 skills

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| financial_modeling | Constroi modelo financeiro defensavel | Modelo financeiro que voce construiu. | pl+ | Custom |
| legal_risk_assessment | Identifica risco juridico em situacao ambigua | Risco legal que voce identificou antes. | pl+ | Custom |
| data_storytelling | Transforma dados em narrativa pra acao | Analise sua que mudou decisao executiva. | pl+ | O*NET |
| forecast_accuracy | Faz previsao com erro <X% | Previsao que voce fez. Como ajustou? | pl+ | Custom |
| audit_mindset | Valida pressuposto, nao aceita face value | Numero suspeito que questionou. | pl+ | BEI |
| diagnostic_reasoning | Diagnostica problema complexo (med/tec/fin) | Diagnostico complexo que voce fez. | sr+ | O*NET |
| stakeholder_data_request_management | Atende pedidos de dados sem virar 'data monkey' | Pedido infinito de exec. Como conduziu? | pl+ | Custom |
| benchmark_thinking | Compara com referencia externa | Decisao ancorada em benchmark. | pl+ | Lominger |

## 8. Operacoes & Processos (parent: operations_process) - 7 skills

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| sla_management | Mantem SLA sob volume crescente | Como manteve SLA quando volume cresceu? | pl+ | O*NET |
| inventory_logistics_optimization | Otimiza estoque/logistica/fluxo | Otimizacao operacional implementada. | pl+ | Custom |
| crisis_response | Responde crise operacional sob pressao | Crise que voce gerenciou. | pl+ | BEI |
| sop_creation | Cria SOPs que outros seguem | SOP que escreveu. Adocao? | jr+ | O*NET |
| workflow_automation_thinking | Identifica trabalho repetitivo | Automacao que sugeriu/implementou. | pl+ | Custom |
| vendor_management | Gerencia fornecedor com escopo/prazo | Fornecedor dificil. Como gerenciou? | pl+ | O*NET |
| quality_assurance_process | Garante qualidade sistemicamente | QA process que voce implementou. | pl+ | Lominger |

## 9. Compliance & Regulatorio (parent: compliance_regulatory) - 6 skills

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| regulatory_knowledge | Domina regulacao especifica (LGPD/CVM/ANVISA) | Regulacao que domina. Como atualizado? | pl+ | Custom |
| compliance_gap_identification | Identifica gap antes do auditor | Gap que achou antes de auditoria. | pl+ | BEI |
| privacy_data_handling | Lida com dado pessoal sob LGPD/GDPR | Decisao envolvendo dado pessoal. | pl+ | Custom |
| ethics_dilemma_navigation | Navega dilema etico onde regra nao resolve | Dilema etico real que enfrentou. | pl+ | BEI |
| audit_response | Responde auditoria sem panico | Auditoria que conduziu/respondeu. | sr+ | Custom |
| policy_creation_with_practical_lens | Cria politica que protege sem virar burocracia | Politica que criou. Equilibrio? | sr+ | Lominger |

## 10. Inovacao & Empreendedorismo (parent: innovation_entrepreneurship) - 6 skills

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| zero_to_one_thinking | Cria algo do zero | Iniciativa que comecou do nada. | pl+ | Custom |
| customer_discovery | Descobre necessidade real via entrevista | Insight que extraiu de entrevista cliente. | pl+ | BEI |
| mvp_scoping | Define MVP que valida hipotese | MVP que escopou. O que cortou? | pl+ | Custom |
| failed_experiment_lesson_extraction | Extrai aprendizado de experimento falho | Experimento que falhou. O que aprendeu? | pl+ | BEI |
| scaling_proof_of_concept | Transforma POC em produto escalavel | POC que escalou. O que mudou? | sr+ | Custom |
| resource_constraint_creativity | Faz mais com menos | Restricao severa que tirou seu melhor. | pl+ | Lominger |

## 11. Dominio Tecnico Cross-Tech (parent: technical_cross_tech) - 8 skills

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| code_review_quality | Da feedback tecnico construtivo | Code review onde viu padrao problematico. | pl+ | Custom |
| production_incident_response | Mantem calma em downtime | Incident que voce atuou. Sequencia? | pl+ | Custom |
| technical_debt_management | Equilibra refactor vs feature | Como decide refactor vs feature? | sr+ | Custom |
| remote_first_collaboration | Opera bem em time distribuido async | Time em 4 fusos. Coordenou entrega? | pl+ | Custom |
| ml_ai_critical_thinking | Sabe quando IA/ML resolve | Time queria IA em X. Como avaliou? | sr+ | Custom |
| security_first_mindset | Pensa seguranca desde design | Decisao tecnica com seguranca cedo. | sr+ | Custom |
| performance_engineering | Otimiza performance sob restricao real | Otimizacao de performance que conduziu. | sr+ | Custom |
| api_design_thinking | Projeta API que dura (versionamento/contrato) | API que desenhou. O que durou? | sr+ | Custom |

## 12. Gestao de Pessoas (parent: people_management) - 8 skills

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| hiring_judgment | Avalia candidatos consistentemente | Contratacao que deu errado. Sinais ignorou? | sr+ | BEI |
| performance_feedback_cycle | Conduz 1:1, review, PIP com rigor | Como estrutura 1:1 com seu time? | sr+ | Lominger |
| career_development_coaching | Investe no plano de carreira | Promocao que orquestrou. | sr+ | BEI |
| difficult_termination | Conduz desligamento com dignidade | Desligamento que conduziu. Como? | sr+ | Custom |
| team_health_diagnosis | Identifica problema antes da crise | Sintoma que viu antes de virar problema. | sr+ | Lominger |
| compensation_calibration | Calibra comp com fairness + budget | Como decide aumentos no time? | sr+ | Custom |
| dei_practical_action | Implementa acao concreta DEI | Acao concreta de DEI que conduziu. | sr+ | Custom |
| team_size_scaling | Cresce time sem perder eficiencia | Time que escalou. O que mudou? | sr+ | Lominger |

## 13. Lideranca Organizacional (parent: organizational_leadership) - 7 skills

> NOTA: removidas executive_presence + founder_mindset_at_scale (fairness flag - decisao Paulo).

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| strategic_vision_setting | Define visao de medio prazo (2-5 anos) | Visao de 3 anos que voce definiu. | sr+ | Lominger |
| organizational_design | Estrutura org pra suportar estrategia | Reorg que conduziu. Por que aquela estrutura? | ld+ | Custom |
| board_communication | Comunica progresso/risco pra board | Reuniao de board que preparou. | ld+ | Lominger |
| capital_allocation | Decide onde investir orcamento | Decisao de capital allocation. | sr+ | Custom |
| crisis_leadership | Lidera org em crise | Crise organizacional que liderou. | sr+ | BEI |
| culture_definition_evolution | Define/evolui cultura deliberadamente | Mudanca cultural que conduziu. | sr+ | Lominger |
| public_communication | Comunica externamente (imprensa, palco) | Comunicacao externa significativa. | sr+ | Custom |

## 14. Lideranca Tecnica (parent: technical_leadership) - 14 skills (EXPANDIDA)

> Skills expandidas conforme decisao Paulo: maxima granularidade.

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| tech_strategy_definition | Define direcao tecnica de medio prazo | Decisao tecnica de 6+ meses que liderou. | sr+ | Custom |
| architecture_decision_making | Toma decisao arquitetural defensavel | ADR mais importante que escreveu. | sr+ | Custom |
| build_vs_buy_decision | Decide build vs buy com criterios | Build vs buy que decidiu. Criterios? | sr+ | Custom |
| technical_evangelism | Convence stakeholders nao-tecnicos | Decisao tecnica vendida pra negocio. | sr+ | Custom |
| platform_thinking | Constroi capability reusavel | Platform que criou. Quem reusou? | ld+ | Custom |
| tech_recruiting_calibration | Calibra bar tecnico em entrevistas | Como calibra bar no time? | sr+ | Custom |
| open_source_engagement | Contribui ou mantem OSS | Contribuicao OSS sua. | sr+ | Custom |
| distributed_systems_design | Projeta sistemas distribuidos resilientes | Decisao de design distribuido (CAP, consistencia) que tomou. | sr+ | Custom |
| data_intensive_application_design | Projeta apps com volume massivo de dados | App data-intensive que projetou. Trade-offs? | sr+ | Custom |
| security_architecture | Arquitetura de seguranca em profundidade | Threat model que conduziu. Mitigacoes? | sr+ | Custom |
| observability_engineering | Constroi observabilidade (logs, metrics, traces) | Sistema observabilidade que implementou. | sr+ | Custom |
| devops_excellence | Excelencia em CI/CD, deploy, rollback | Pipeline CI/CD que voce desenhou. | sr+ | Custom |
| ml_systems_design | Projeta sistemas ML em producao | Sistema ML em prod que projetou. Drift, retraining? | sr+ | Custom |
| frontend_architecture | Arquitetura frontend escalavel | Decisao frontend (SPA vs SSR, micro-frontends) que tomou. | sr+ | Custom |

## 15. Cultura, Etica & Saude Mental (parent: culture_ethics_wellbeing) - 7 skills

> NOTA: removida bias_interruption (fairness flag - decisao Paulo).

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| ethical_concern_raising | Levanta issue mesmo inconveniente | Issue impopular que levantou. | jr+ | BEI |
| confidentiality_handling | Mantem confidencialidade sob pressao | Info que nao podia compartilhar. | jr+ | O*NET |
| inclusive_collaboration | Garante vozes minoritarias ouvidas | Time de 5, 1 nao fala. O que faz? | pl+ | Custom |
| integrity_under_pressure | Nao corta etica sob pressao | Pediram cortar caminho duvidoso. | pl+ | BEI |
| psychological_safety_building | Cria ambiente de discordia segura | O que faz pra time discordar de voce? | sr+ | Custom |
| burnout_awareness | Reconhece sinais em si e no time | Burnout que identificou. | pl+ | Custom |
| work_life_boundary_setting | Estabelece limite saudavel | Como mantem boundary trabalho/vida? | jr+ | Custom |

---
## 16. Saude & Bem-estar Clinico (parent: health_clinical) - 8 skills [NOVA]

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| clinical_diagnostic_reasoning | Raciocinio diagnostico (anamnese, hipoteses, exclusao) | Caso clinico complexo que diagnosticou. Sequencia? | jr+ | O*NET |
| patient_communication | Comunica diagnostico/prognostico com empatia | Bad news pra paciente. Como conduziu? | jr+ | HCAHPS |
| evidence_based_practice | Atualiza pratica com evidencia (meta-analises) | Mudanca de conduta que voce adotou por evidencia. | pl+ | Custom |
| multidisciplinary_team_collaboration | Coordena com outras especialidades | Caso que exigiu time multi (med+enf+psico+ft). | pl+ | O*NET |
| medical_ethics_navigation | Navega dilemas (autonomia vs paternalismo) | Dilema etico clinico que enfrentou. | pl+ | BEI |
| clinical_documentation_rigor | Prontuario completo, defensavel, ressuscitavel | Caso em que prontuario fez diferenca. | jr+ | Custom |
| emergency_response_clinical | Estabiliza emergencia (BLS/ACLS/triagem) | Emergencia clinica que conduziu. | pl+ | O*NET |
| patient_safety_culture | Reporta near-miss, segue checklists, fala up | Near-miss que reportou. O que mudou? | jr+ | Custom |

## 17. Educacao & Pedagogia (parent: education_pedagogy) - 7 skills [NOVA]

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| instructional_design | Desenha aula/curso com objetivo + atividade + avaliacao | Curso/aula que desenhou. Aprendizado real? | pl+ | Custom |
| learning_assessment_design | Cria avaliacao que mede o que diz medir | Avaliacao que criou. Validade? | pl+ | Custom |
| classroom_management | Gerencia disciplina e engajamento em sala | Sala dificil que conduziu. | jr+ | O*NET |
| individualized_learning_adaptation | Adapta pra ritmo/dificuldade individual | Aluno com dificuldade especifica. Como adaptou? | jr+ | Custom |
| pedagogical_content_knowledge | Sabe como ensinar conteudo (nao so o conteudo) | Conceito dificil. Como ensinaria? | pl+ | O*NET |
| parent_caregiver_communication | Comunica com pais/responsaveis construtivamente | Reuniao dificil com pais. Como conduziu? | jr+ | Custom |
| student_motivation_engagement | Motiva aluno desinteressado | Aluno desinteressado que voce engajou. | jr+ | BEI |

## 18. Varejo & Customer-Facing (parent: retail_customer_facing) - 7 skills [NOVA]

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| pos_operation_excellence | Opera POS/caixa com velocidade + acuracia | Pico de movimento. Como manteve fluxo? | jr+ | O*NET |
| store_visual_merchandising | Organiza loja pra conversao + experiencia | Layout que voce mudou. Resultado? | jr+ | Custom |
| customer_complaint_recovery_floor | Recupera cliente furioso na loja | Cliente furioso na loja. Como reverteu? | jr+ | BEI |
| upsell_floor_technique | Sugere produto adicional sem ser invasivo | Upsell bem-sucedido que conduziu. | jr+ | Custom |
| inventory_count_accuracy | Mantem inventario acurado (loss prevention) | Discrepancia de estoque que descobriu. | jr+ | O*NET |
| peak_hour_throughput_management | Mantem throughput em horario de pico | Black Friday/Natal. Como conduziu? | pl+ | Custom |
| brand_ambassadorship_floor | Vive marca no atendimento (nao so script) | Como representa a marca no dia-a-dia? | jr+ | Custom |

## 19. Logistica & Supply Chain (parent: logistics_supply_chain) - 7 skills [NOVA]

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| demand_forecasting | Prever demanda com erro tolerável | Forecast que voce conduziu. Acuracia? | pl+ | Custom |
| supply_planning | Planeja suprimento (lead time + buffer) | Plano de supply que conduziu. | pl+ | Custom |
| last_mile_optimization | Otimiza entrega final (rotas, prazo, custo) | Otimizacao de last-mile que implementou. | pl+ | O*NET |
| warehouse_layout_thinking | Layout de armazem (fluxo, picking, slotting) | Mudanca de layout que conduziu. | pl+ | Custom |
| freight_negotiation | Negocia frete com transportador | Negociacao de frete dificil. | pl+ | Custom |
| customs_compliance_navigation | Navega aduana, INCOTERMS, documentacao | Importacao/exportacao complexa. | pl+ | Custom |
| supplier_audit_capability | Audita fornecedor (qualidade, capacidade, etica) | Auditoria de fornecedor que conduziu. | sr+ | Custom |

## 20. Marketing & Branding (parent: marketing_branding) - 8 skills [NOVA]

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| brand_positioning_thinking | Define posicionamento defensavel | Posicionamento que voce definiu. Por que? | pl+ | Custom |
| content_strategy_design | Planeja conteudo com funnel + persona + canal | Estrategia de conteudo que desenhou. | pl+ | Custom |
| growth_loop_design | Desenha loop de crescimento (referral, viral, content) | Loop de crescimento que implementou. | pl+ | Custom |
| paid_media_optimization | Otimiza ROAS de paid media | Campanha que otimizou. Resultado? | pl+ | Custom |
| marketing_attribution_analysis | Atribui resultado a canal corretamente | Modelo de atribuicao que voce escolheu. | sr+ | Custom |
| customer_segmentation_thinking | Segmenta base com criterio acionavel | Segmentacao que voce desenhou. | pl+ | Custom |
| brand_voice_consistency | Mantem voz consistente em N canais | Voz da marca que voce padronizou. | pl+ | Custom |
| community_building | Constroi comunidade de marca | Comunidade que voce nucleou. | pl+ | Custom |

## 21. Engenharia Tradicional (parent: traditional_engineering) - 7 skills [NOVA]

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| engineering_calculation_rigor | Faz calculo defensavel + verificacao | Calculo critico que voce conduziu. | pl+ | Custom |
| project_management_construction | Gerencia obra/projeto fisico (prazo, custo, qualidade) | Obra/projeto que voce conduziu. | pl+ | O*NET |
| safety_first_engineering | Prioriza seguranca (NR-X, OSHA) sem comprometer | Decisao onde voce priorizou seguranca. | jr+ | Custom |
| materials_specification_judgment | Especifica material com criterios (resistencia, custo, ambiente) | Especificacao critica que voce conduziu. | pl+ | Custom |
| regulatory_engineering_compliance | Navega regulacao tecnica (CREA, codigo de obras) | Aprovacao regulatoria dificil. | pl+ | Custom |
| field_problem_solving | Resolve problema em campo (nao no escritorio) | Problema de campo que resolveu. | pl+ | BEI |
| multidisciplinary_engineering_coordination | Coordena civil+eletrica+hidraulica+arquitetura | Projeto multidisciplinar que coordenou. | pl+ | Custom |

## 22. Industria Pesada (parent: heavy_industry) - 7 skills [NOVA]

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| hse_excellence | Health Safety Environment (zero incidente) | Iniciativa HSE que conduziu. | pl+ | Custom |
| shutdown_planning | Planeja parada de manutencao critica | Shutdown que voce conduziu. | sr+ | Custom |
| asset_integrity_management | Gerencia integridade de ativo (corrosao, fadiga) | Programa de integridade que conduziu. | sr+ | Custom |
| root_cause_analysis_industrial | RCA com 5-Why, Ishikawa, FTA | Falha critica que voce diagnosticou. | pl+ | O*NET |
| lean_manufacturing_implementation | Implementa kaizen, 5S, value stream | Lean implementation que conduziu. | pl+ | Custom |
| environmental_compliance_navigation | Navega licenciamento ambiental (CONAMA) | Licenciamento dificil que conduziu. | sr+ | Custom |
| contractor_management_field | Gerencia empreiteira em campo | Empreiteira dificil que gerenciou. | pl+ | Custom |

## 23. Midia & Comunicacao (parent: media_communication) - 7 skills [NOVA]

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| editorial_judgment | Decide o que e noticia/relevante | Decisao editorial dificil que tomou. | pl+ | Custom |
| headline_craft | Escreve headline que captura sem clickbait | Headline que voce considera melhor seu. | jr+ | Custom |
| source_validation | Valida fonte antes de publicar | Pauta que voce parou por fonte fraca. | pl+ | Custom |
| deadline_journalism | Entrega materia sob deadline apertado | Furada que voce cobriu sob pressao. | jr+ | BEI |
| multimedia_storytelling | Conta historia em texto+video+audio integrado | Reportagem multimidia que conduziu. | pl+ | Custom |
| audience_engagement_thinking | Entende metricas de engajamento sem cair em vanity | Decisao editorial baseada em audience data. | pl+ | Custom |
| brand_safety_in_content | Evita risco reputacional em conteudo | Decisao de nao publicar por brand safety. | pl+ | Custom |

## 24. Telecomunicacoes (parent: telecommunications) - 6 skills [NOVA]

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| network_design_thinking | Projeta rede com capacidade + resiliencia | Projeto de rede que conduziu. | sr+ | Custom |
| signal_quality_diagnosis | Diagnostica problema de sinal (RF, fibra, ethernet) | Problema de sinal complexo que resolveu. | pl+ | O*NET |
| regulatory_telecom_navigation | Navega ANATEL, FCC, etc | Compliance telecom dificil. | pl+ | Custom |
| customer_carrier_balance | Equilibra cliente final vs carrier B2B | Conflito cliente vs carrier. | sr+ | Custom |
| capacity_planning_telco | Planeja capacidade pra picos de trafego | Capacity event (BBB, COPA) que voce planejou. | sr+ | Custom |
| field_install_excellence | Excelencia em instalacao de campo | Instalacao critica que conduziu. | jr+ | Custom |

## 25. Pharma & Life Sciences (parent: pharma_life_sciences) - 6 skills [NOVA]

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| clinical_trial_protocol_rigor | Conduz ensaio clinico segundo ICH-GCP | Ensaio que voce conduziu. Desvios? | pl+ | Custom |
| pharmacovigilance_mindset | Reporta adverse events com rigor | AE serio que reportou. | pl+ | Custom |
| regulatory_submission_navigation | Submete dossier (ANVISA, FDA) | Submissao regulatoria dificil. | sr+ | Custom |
| gxp_compliance | Aplica GMP/GLP/GCP no dia-a-dia | Desvio GxP que identificou. | pl+ | Custom |
| scientific_publication_quality | Publica em peer-review com qualidade | Publicacao com peer-review. | sr+ | Custom |
| biostatistics_judgment | Aplica estatistica sem hackear p-value | Analise estatistica que conduziu. | sr+ | Custom |

## 26. AI/ML Specialist (parent: ai_ml_specialist) - 7 skills [NOVA]

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| model_evaluation_rigor | Avalia modelo com baseline + holdout + a/b | Avaliacao rigorosa que conduziu. | pl+ | Custom |
| dataset_quality_thinking | Garante qualidade de dataset (label, drift, leakage) | Issue de dataset que descobriu. | pl+ | Custom |
| llm_application_design | Projeta app LLM (RAG, agentes, eval) | App LLM que projetou. Trade-offs? | pl+ | Custom |
| ml_ops_excellence | MLOps (deploy, monitoring, retrain pipeline) | Pipeline ML em prod que voce desenhou. | sr+ | Custom |
| ai_safety_alignment | Avalia risco de IA (jailbreak, hallucination, bias) | Decisao de safety em IA que tomou. | sr+ | Custom |
| prompt_engineering_systematic | Eng. de prompt sistematica (nao trial-error) | Prompt critico que voce desenhou. Iterou como? | pl+ | Custom |
| model_monitoring_drift_detection | Detecta drift de modelo em prod | Drift que detectou. Como reagiu? | sr+ | Custom |

---

## Resumo estatistico v3

| Categoria | # | Tipo |
|---|---|---|
| Universais (15 cats) | 109 skills | Aplicam transversalmente |
| Verticais (11 cats) | 87 skills | Specific por industria |
| **Total** | **196** | |

| Por fonte |
|---|
| O*NET: ~40 |
| BEI: ~20 |
| Lominger: ~15 |
| Custom (incluindo verticais novas): ~121 |

| Verticais cobertas | Cobertura |
|---|---|
| Tech/SaaS | Cross-tech (cat 11) + Tech Leadership (cat 14) + AI/ML (cat 26) = 29 skills |
| Healthcare | Saude clinica (cat 16) + Pharma (cat 25) = 14 skills |
| Educacao | Educacao (cat 17) = 7 skills |
| Comercial/Vendas | Vendas (cat 6) + Marketing (cat 20) = 16 skills |
| Industria/Eng | Eng. tradicional (cat 21) + Industria pesada (cat 22) = 14 skills |
| Servicos/Varejo | Varejo (cat 18) + Logistica (cat 19) = 14 skills |
| Comunicacao | Midia (cat 23) + Telecom (cat 24) = 13 skills |

| Verticais NAO cobertas explicitamente |
|---|
| Direito (Compliance cat 9 cobre parte; advocacia litigancia nao) |
| Servicos financeiros (Analise cat 7 cobre parte; trading/banking detail nao) |
| Construcao civil propriamente dita (Eng. tradicional cobre parte) |
| Agronegocio (nenhuma cobertura) |
| Hospitalidade (atendimento turismo) (Varejo cobre parte) |

**Recomendacao**: deixar essas em v4 se demanda real aparecer. v3 ja cobre 80% das vagas WeDOTalent.

---

## Decisoes de design v3

### Hierarquia 2 niveis funciona como?
- Cada pergunta gerada -> classificada em 1 skill_probed (filho)
- Effectiveness aprende em ambos: parent stats (rapido, ~2 mes) + filho stats (devagar, ~12-24 meses)
- Runtime usa filho se >=20 amostras; senao parent; senao prior O*NET

### Por que 196 (e nao 80 ou 400)?
- 80 era v1 - cobertura tech-heavy, perde verticais
- 400 dilui learning de skill ainda mais
- 196 = sweet spot para cobertura ampla com hierarquia funcionando bem em parent level

### Aplicabilidade por senioridade
- jr+ : ~50 skills (entrada universal + alguns verticais)
- pl+ : ~80 skills (cresce em scope/customer/vertical)
- sr+ : ~55 skills (lideranca + estrategia + tech advanced)
- ld+ : ~10 skills (C-level apenas)

### Skills com fairness flag
v3 NAO TEM fairness flags. Removidas conforme decisao Paulo.

---

## Perguntas remanescentes pra revisar v3

1. **Skills duplicadas/sobrepostas** entre categorias? Ex: `regulatory_knowledge` (cat 9) vs `regulatory_telecom_navigation` (cat 24) vs `regulatory_engineering_compliance` (cat 21). Sao parecidas mas verticais diferentes. Manter ou consolidar em uma generica?
2. **Granularidade por vertical** esta OK ou alguma vertical precisa de mais? (Ex: Saude tem 8, mas medicina tem mil sub-especialidades. Educacao tem 7 mas EAD vs presencial vs corporativa sao diferentes).
3. **Verticais nao cobertas** (advocacia litigancia, agronegocio, hospitalidade, construcao civil pesada) - adicionar v4 ou esperar demanda?
4. **Categorias verticais novas** estao em snake_case ingles. WeDOTalent prefere nomenclatura PT-BR (saude_clinica) ou EN (health_clinical)?
5. **Aprovado pra implementacao tecnica Phase 3** ou tem ajustes na taxonomia?
