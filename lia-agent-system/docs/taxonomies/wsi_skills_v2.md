# WSI Skill Taxonomy — v2 (DRAFT, hierarchical)

> **Status**: DRAFT v2 — pendente revisao Paulo
> **Data**: 2026-05-03
> **Estrutura**: 15 competencies parent + 119 skills filhos
> **Fontes**: O*NET + BEI (McClelland) + Lominger + 4 frameworks vertical-specific (vendas, juridico, financeiro, saude)
> **Uso**: skill_probed em GeneratedQuestion aponta filho; learning ocorre em ambos os niveis

---

## Como o learning funciona com hierarquia

```
Pergunta gerada -> classificada em 1 skill_probed (filho)
                                        v
   Effectiveness aprende em 2 niveis simultaneos:

PARENT (15 competencies)            FILHO (~120 skills)
~20 amostras/mes                    ~2-3 amostras/mes
threshold em ~1 mes                 threshold em ~6-9 meses
"categoria importa pra esta vaga?"  "skill especifica funciona?"
```

Runtime: filho >=20 amostras usa filho stats; senao fallback parent stats; senao fallback prior O*NET.

---

## Estrutura geral (15 categorias parent)

| # | Parent | # filhos | Foco | Aplica |
|---|---|---|---|---|
| 1 | Comunicacao & Colaboracao | 10 | universal | jr+ |
| 2 | Execucao & Entrega | 11 | universal | jr+ |
| 3 | Aprendizado & Adaptacao | 7 | universal | jr+ |
| 4 | Pensamento & Decisao | 9 | universal | jr+/pl+ |
| 5 | Customer & Stakeholder | 7 | universal | jr+/pl+ |
| 6 | Vendas & Influencia | 8 | comercial/RC | jr+/pl+ |
| 7 | Analise & Diagnostico | 8 | finance/legal/data | pl+ |
| 8 | Operacoes & Processos | 7 | ops/admin/log | jr+ |
| 9 | Compliance & Regulatorio | 6 | legal/finance/health | pl+ |
| 10 | Inovacao & Empreendedorismo | 6 | produto/startup | pl+/sr+ |
| 11 | Dominio Tecnico Cross-Tech | 8 | eng/dados | pl+/sr+ |
| 12 | Gestao de Pessoas | 8 | RH + qualquer lider | sr+ |
| 13 | Lideranca Organizacional | 9 | C-level/diretoria | sr+/ld+ |
| 14 | Lideranca Tecnica | 7 | staff+ tech | sr+/ld+ |
| 15 | Cultura, Etica & Saude Mental | 8 | universal | jr+/pl+ |
| **Total** | | **119** | | |

---

## 1. Comunicacao & Colaboracao (parent: communication_collaboration)

| Skill | Descricao | Exemplo | Sen. | Fonte | Flag |
|---|---|---|---|---|---|
| active_listening | Captura e reflete antes de responder | "Demanda confusa de stakeholder. Como confirmou que entendeu?" | jr+ | O*NET | - |
| async_communication_clarity | Mensagens auto-suficientes que dispensam follow-up | "Documentou decisao complexa pra alguem ler depois?" | jr+ | Custom | - |
| synchronous_meeting_effectiveness | Conduz reuniao com objetivo + decisao + follow-up | "Reuniao que voce liderou. Como produziu decisao?" | pl+ | Lominger | - |
| cross_team_alignment | Constroi consenso entre times com objetivos diferentes | "Quando alinhou 2+ times pra entrega comum?" | sr+ | Custom | - |
| feedback_giving | Da feedback duro construtivo com exemplos concretos | "Vez que precisou dar feedback negativo." | pl+ | BEI | - |
| feedback_acceptance | Recebe critica direta sem se desestabilizar | "Feedback duro recebido. Reacao e o que mudou?" | jr+ | BEI | - |
| conflict_resolution | Trata desacordo sem escalada, busca win-win | "Conflito recente com colega." | jr+ | O*NET | - |
| executive_communication | Resume contexto tecnico pra audiencia senior em <2min | "Apresentaria [problema] pro CEO em 60s?" | sr+ | O*NET | viés socioeconomico |
| documentation_writing | Produz docs que outros usam sem perguntar | "Doc que voce fez. Quem usou?" | jr+ | Custom | - |
| internal_communication_strategy | Comunica change/iniciativa pra org grande | "Comunicaria reorg pra 200 pessoas?" | sr+ | Lominger | - |

---

## 2. Execucao & Entrega (parent: execution_delivery)

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| delivery_under_deadline_pressure | Cumpre prazo apertado sem comprometer qualidade | "1 semana pra algo que precisaria 1 mes. O que fez?" | jr+ | BEI |
| prioritization_with_competing_demands | Escolhe entre demandas concorrentes com criterio | "3 tarefas urgentes, tempo pra 2. Como decide?" | jr+ | O*NET |
| scope_management | Corta escopo quando necessario | "Vez que entregou menos do que pediram." | pl+ | BEI |
| ownership_of_outcome | Assume resultado final, nao so esforco | "Projeto que voce foi responsavel pelo resultado." | jr+ | BEI |
| recovery_from_failure | Reage construtivamente quando da errado | "Incident em producao. O que mudou depois?" | pl+ | Custom |
| attention_to_detail | Captura erros sutis antes do cliente | "Bug que outros deixaram passar." | jr+ | O*NET |
| process_improvement | Identifica ineficiencia e implementa melhoria | "Processo que mudou recentemente." | pl+ | O*NET |
| time_management | Organiza proprio tempo entre frentes | "Dia tipico de 5+ frentes ativas." | jr+ | O*NET |
| quality_under_speed | Mantem qualidade quando velocidade aperta | "Vez que cortou caminho." | pl+ | Custom |
| follow_through | Termina o que comecou, sem pontas soltas | "Projeto longo do inicio ao fim sozinho." | jr+ | BEI |
| multi_project_juggling | Mantem 5+ projetos com prioridade variavel | "Maior numero paralelo. Como balanceou?" | pl+ | Lominger |

---

## 3. Aprendizado & Adaptacao (parent: learning_adaptation)

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| technical_self_learning | Aprende stack/ferramenta nova sem treinamento | "Ultima vez que aprendeu tech totalmente nova." | jr+ | Custom |
| domain_curiosity | Vai alem do escopo tecnico pra entender negocio | "O que voce entende sobre o negocio alem da sua area?" | jr+ | BEI |
| adapting_to_change | Reage a pivos/reorgs/mudanca de prioridade | "Projeto que pivotou no meio." | jr+ | O*NET |
| learning_from_failure | Extrai licao concreta de erro proprio | "Maior erro que cometeu. O que aprendeu?" | jr+ | BEI |
| cross_domain_translation | Aplica conceito de uma area em outra | "Aplicou algo aprendido fora do trabalho na sua area." | pl+ | Custom |
| proactive_skill_building | Identifica gaps e investe em fechar | "Skill que precisa desenvolver. O que esta fazendo?" | pl+ | BEI |
| continuous_learning_habit | Habito de aprendizado regular (nao so quando precisa) | "Como voce aprende continuamente?" | jr+ | Lominger |

---

## 4. Pensamento & Decisao (parent: thinking_decision)

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| data_driven_decision_making | Usa evidencia quantitativa em decisoes importantes | "Decisao importante. Que dados consultou?" | jr+ | O*NET |
| trade_off_articulation | Explica trade-offs com clareza, nao falsa dicotomia | "Escolheu entre X e Y. Trade-offs reais?" | pl+ | O*NET |
| root_cause_analysis | Investiga ate causa estrutural, nao sintoma | "Problema recorrente que resolveu de uma vez." | pl+ | O*NET |
| ambiguity_tolerance | Avanca sem requisito 100% claro | "Comecou projeto sem briefing completo." | jr+ | BEI |
| hypothesis_driven_thinking | Forma hipoteses testaveis antes de partir pra solucao | "Como abordaria problema que ninguem entende?" | pl+ | Custom |
| systems_thinking | Ve implicacoes de 2a ordem (efeitos colaterais) | "Decisao que parecia obvia mas viu efeito secundario." | sr+ | O*NET |
| decision_speed | Decide com 70% info em vez de esperar 100% | "Decidiu rapido com pouca info. O que pesou?" | pl+ | BEI |
| bias_awareness | Reconhece proprios viesses cognitivos | "Decisao que sabia estar enviesado. O que fez?" | sr+ | O*NET |
| creative_problem_solving | Combina elementos nao-obvios pra resolver | "Solucao criativa fora do padrao." | pl+ | Lominger |

---

## 5. Customer & Stakeholder (parent: customer_stakeholder)

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| customer_empathy | Entende dor do cliente alem do que ele articula | "Cliente pediu X mas precisava Y. Como descobriu?" | jr+ | O*NET |
| stakeholder_management | Gerencia expectativas de partes com interesses diferentes | "Stakeholders queriam coisas opostas. Como navegou?" | pl+ | O*NET |
| customer_advocacy | Defende cliente internamente em decisoes | "Vez que segurou ou alterou decisao por causa do cliente." | pl+ | Custom |
| difficult_conversation_with_customer | Da bad news pra cliente sem perder relacao | "Bad news pra cliente. Como abordou?" | pl+ | BEI |
| expectation_setting | Antecipa friccoes antes que virem problema | "Cliente surpreendido negativamente. Como evitaria hoje?" | pl+ | Lominger |
| cross_cultural_communication | Comunica eficaz entre culturas diferentes (BR/US/EU) | "Trabalhar com time/cliente cultural diferente." | pl+ | O*NET |
| service_recovery | Recupera relacao apos algo dar errado | "Cliente furioso. Como reverteu?" | pl+ | BEI |

---

## 6. Vendas & Influencia (parent: sales_influence)

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| consultative_selling | Vende resolvendo problema do cliente, nao empurrando produto | "Vez que vendeu algo dificil. Como conduziu?" | jr+ | O*NET |
| objection_handling | Lida com objecao sem ficar defensivo | "Objecao mais dura que recebeu. Como respondeu?" | pl+ | Custom |
| negotiation_value_capture | Negocia em torno de valor, nao so preco | "Negociacao dificil. Que alavancas usou?" | pl+ | BEI |
| pipeline_discipline | Mantem disciplina de funil + forecast accuracy | "Como organiza seu pipeline?" | pl+ | Custom |
| account_expansion | Cresce conta existente (upsell/cross-sell) | "Conta que cresceu sob seu cuidado." | pl+ | Lominger |
| influence_without_authority | Move agenda sem ser chefe formal | "Mudou direcao sem poder formal." | pl+ | BEI |
| presentation_skill | Apresenta pra audiencia variando registro/profundidade | "Apresentacao que mudou a opiniao da sala." | pl+ | O*NET |
| closing_under_resistance | Fecha venda quando cliente esta hesitante | "Deal que quase nao fechou. O que destravou?" | sr+ | Custom |

---

## 7. Analise & Diagnostico (parent: analysis_diagnosis)

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| financial_modeling | Constroi modelo financeiro defensavel | "Modelo financeiro que voce construiu." | pl+ | Custom |
| legal_risk_assessment | Identifica risco juridico em situacao ambigua | "Risco legal que voce identificou antes de outros." | pl+ | Custom |
| data_storytelling | Transforma dados em narrativa pra acao | "Analise sua que mudou decisao executiva." | pl+ | O*NET |
| forecast_accuracy | Faz previsao com erro <X%, ajusta com aprendizado | "Previsao que voce fez. Como acompanhou e ajustou?" | pl+ | Custom |
| audit_mindset | Valida pressuposto, nao aceita numero face value | "Numero suspeito que voce questionou. O que descobriu?" | pl+ | BEI |
| diagnostic_reasoning | Diagnostica problema medico/tecnico/financeiro complexo | "Diagnostico complexo que voce fez (medico/tecnico/etc)." | sr+ | O*NET |
| stakeholder_data_request_management | Atende demanda de dados de exec sem virar 'data monkey' | "Pedido infinito de dados de exec. Como conduziu?" | pl+ | Custom |
| benchmark_thinking | Compara com referencia externa (mercado/peer/historic) | "Decisao que voce ancorou em benchmark." | pl+ | Lominger |

---

## 8. Operacoes & Processos (parent: operations_process)

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| sla_management | Mantem SLA sob volume crescente | "Como manteve SLA quando volume cresceu?" | pl+ | O*NET |
| inventory_logistics_optimization | Otimiza estoque/logistica/fluxo | "Otimizacao operacional que voce implementou." | pl+ | Custom |
| crisis_response | Responde a crise operacional sob pressao | "Crise que voce gerenciou. Sequencia de acoes?" | pl+ | BEI |
| sop_creation | Cria SOPs (Standard Operating Procedures) que outros seguem | "SOP que voce escreveu. Adocao?" | jr+ | O*NET |
| workflow_automation_thinking | Identifica trabalho repetitivo pra automacao | "Automacao que voce sugeriu/implementou." | pl+ | Custom |
| vendor_management | Gerencia fornecedor com escopo/prazo/qualidade | "Fornecedor dificil. Como gerenciou?" | pl+ | O*NET |
| quality_assurance_process | Garante qualidade sistemicamente, nao por revisao manual | "QA process que voce implementou." | pl+ | Lominger |

---

## 9. Compliance & Regulatorio (parent: compliance_regulatory)

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| regulatory_knowledge | Domina regulacao especifica (LGPD/CVM/ANVISA/etc) | "Regulacao que voce domina. Como mantém atualizado?" | pl+ | Custom |
| compliance_gap_identification | Identifica gap de compliance antes do auditor | "Gap que voce achou antes de auditoria." | pl+ | BEI |
| privacy_data_handling | Lida com dado pessoal sob LGPD/GDPR | "Decisao envolvendo dado pessoal. Como navegou LGPD?" | pl+ | Custom |
| ethics_dilemma_navigation | Navega dilema etico onde regra nao resolve | "Dilema etico real que enfrentou." | pl+ | BEI |
| audit_response | Responde auditoria sem panico, com evidencia | "Auditoria que voce conduziu/respondeu." | sr+ | Custom |
| policy_creation_with_practical_lens | Cria politica que protege sem virar burocracia | "Politica que voce criou. Equilibrio?" | sr+ | Lominger |

---

## 10. Inovacao & Empreendedorismo (parent: innovation_entrepreneurship)

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| zero_to_one_thinking | Cria algo do zero quando nada existe | "Iniciativa que voce comecou do nada." | pl+ | Custom |
| customer_discovery | Descobre real necessidade via entrevista (nao survey) | "Insight que voce extraiu de entrevista com cliente." | pl+ | BEI |
| mvp_scoping | Define MVP que valida hipotese, nao 'mini produto' | "MVP que voce escopou. O que cortou?" | pl+ | Custom |
| failed_experiment_lesson_extraction | Extrai aprendizado de experimento que nao deu certo | "Experimento que falhou. O que aprendeu?" | pl+ | BEI |
| scaling_proof_of_concept | Transforma POC validado em produto escalavel | "POC que voce escalou. O que mudou no caminho?" | sr+ | Custom |
| resource_constraint_creativity | Faz mais com menos (orcamento/time/tempo) | "Restricao severa que tirou o melhor de voce." | pl+ | Lominger |

---

## 11. Dominio Tecnico Cross-Tech (parent: technical_cross_tech)

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| code_review_quality | Da feedback tecnico construtivo sem ser pedante | "Code review onde viu padrao problematico." | pl+ | Custom |
| production_incident_response | Mantem calma e estrutura na resposta a downtime | "Incident que voce atuou. Sequencia?" | pl+ | Custom |
| technical_debt_management | Equilibra refactor vs entrega de feature | "Como decide refactor vs feature?" | sr+ | Custom |
| remote_first_collaboration | Opera bem em time distribuido async | "Time em 4 fusos. Como coordenou entrega complexa?" | pl+ | Custom |
| ml_ai_critical_thinking | Sabe quando IA/ML resolve e quando nao | "Time queria IA em X. Como avaliou?" | sr+ | Custom |
| security_first_mindset | Pensa em seguranca desde design, nao no final | "Decisao tecnica onde voce trouxe seguranca cedo." | sr+ | Custom |
| performance_engineering | Otimiza performance sob restricao real (latencia/custo) | "Otimizacao de performance que voce conduziu." | sr+ | Custom |
| api_design_thinking | Projeta API que dura (versionamento, contrato) | "API que voce desenhou. O que durou, o que mudaria?" | sr+ | Custom |

---

## 12. Gestao de Pessoas (parent: people_management)

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| hiring_judgment | Avalia candidatos consistentemente, reconhece red flags | "Contratacao que deu errado. Que sinais ignorou?" | sr+ | BEI |
| performance_feedback_cycle | Conduz ciclo formal (1:1, review, PIP) com rigor | "Como voce estrutura 1:1 com seu time?" | sr+ | Lominger |
| career_development_coaching | Investe no plano de carreira de cada pessoa | "Promocao no seu time que voce orquestrou." | sr+ | BEI |
| difficult_termination | Conduz desligamento com dignidade e clareza | "Desligamento que voce conduziu. Como?" | sr+ | Custom |
| team_health_diagnosis | Identifica problema de saude no time antes da crise | "Sintoma que voce viu antes de virar problema." | sr+ | Lominger |
| compensation_calibration | Calibra comp da equipe com fairness + budget | "Como voce decide aumentos no seu time?" | sr+ | Custom |
| dei_practical_action | Implementa acao concreta de DEI (nao slogan) | "Acao concreta de DEI que voce conduziu." | sr+ | Custom |
| team_size_scaling | Cresce time de 5 pra 15 (ou shrink) sem perder eficiencia | "Time que voce escalou. O que mudou na gestao?" | sr+ | Lominger |

---

## 13. Lideranca Organizacional (parent: organizational_leadership)

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| strategic_vision_setting | Define visao de medio prazo (2-5 anos) com clareza | "Visao de 3 anos que voce definiu." | sr+ | Lominger |
| organizational_design | Estrutura org pra suportar estrategia (nao copia outras) | "Reorg que voce conduziu. Por que aquela estrutura?" | ld+ | Custom |
| board_communication | Comunica progresso/risco pra board com transparencia | "Reuniao de board que voce preparou. O que destacou?" | ld+ | Lominger |
| capital_allocation | Decide onde investir orcamento entre prioridades | "Decisao de capital allocation que voce tomou." | sr+ | Custom |
| crisis_leadership | Lidera org em crise (PR, financeira, operacional) | "Crise organizacional que voce liderou." | sr+ | BEI |
| culture_definition_evolution | Define/evolui cultura de forma deliberada | "Mudanca cultural que voce conduziu." | sr+ | Lominger |
| executive_presence | Inspira confianca em audiencia senior | "Como prepara reuniao com C-level?" | ld+ | Lominger | viés genero/raca/socio |
| public_communication | Comunica externamente (imprensa, palco, comunidade) | "Comunicacao externa significativa que voce fez." | sr+ | Custom |
| founder_mindset_at_scale | Mantem mindset de founder mesmo em org grande | "Decisao em que voce agiu como founder em vez de gestor." | sr+ | Custom |

---

## 14. Lideranca Tecnica (parent: technical_leadership)

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| tech_strategy_definition | Define direcao tecnica de medio prazo com justificativa | "Decisao tecnica de 6+ meses que liderou." | sr+ | Custom |
| architecture_decision_making | Toma decisao arquitetural defensavel (ADR-style) | "ADR mais importante que voce escreveu." | sr+ | Custom |
| build_vs_buy_decision | Decide build vs buy com criterios estruturados | "Build vs buy que voce decidiu. Criterios?" | sr+ | Custom |
| technical_evangelism | Convence stakeholders nao-tecnicos de decisao tecnica | "Decisao tecnica que voce vendeu pra negocio." | sr+ | Custom |
| platform_thinking | Constroi capability reusavel, nao solucao pontual | "Platform que voce criou. Quem reusou?" | ld+ | Custom |
| tech_recruiting_calibration | Calibra bar tecnico em entrevistas com consistencia | "Como voce calibra bar tecnico no time?" | sr+ | Custom |
| open_source_engagement | Contribui ou mantem OSS de forma significativa | "Contribuicao OSS sua. O que aprendeu?" | sr+ | Custom |

---

## 15. Cultura, Etica & Saude Mental (parent: culture_ethics_wellbeing)

| Skill | Descricao | Exemplo | Sen. | Fonte |
|---|---|---|---|---|
| ethical_concern_raising | Levanta issue mesmo quando inconveniente | "Issue impopular que voce levantou." | jr+ | BEI |
| confidentiality_handling | Mantem confidencialidade sob pressao | "Info que nao podia compartilhar sob pressao." | jr+ | O*NET |
| inclusive_collaboration | Garante vozes minoritarias ouvidas | "Time de 5, 1 nao fala. O que voce faz?" | pl+ | Custom |
| integrity_under_pressure | Nao corta etica sob pressao por resultado | "Pediram pra cortar caminho duvidoso. O que fez?" | pl+ | BEI |
| psychological_safety_building | Cria ambiente onde time fala desconfortos | "O que faz pra alguem se sentir confortavel discordando?" | sr+ | Custom |
| burnout_awareness | Reconhece sinais de burnout em si e no time | "Burnout que voce identificou (em si ou no time)." | pl+ | Custom |
| work_life_boundary_setting | Estabelece limite saudavel sem sair do jogo | "Como voce mantem boundary trabalho/vida?" | jr+ | Custom |
| bias_interruption | Interrompe comportamento enviesado de outros | "Colega fez comentario enviesado. O que fez?" | sr+ | Custom | sensivel |

---

## Resumo estatistico

| Categoria | # Skills | Foco |
|---|---|---|
| Comunicacao | 10 | universal |
| Execucao | 11 | universal |
| Aprendizado | 7 | universal |
| Pensamento | 9 | universal |
| Customer | 7 | universal |
| Vendas | 8 | comercial |
| Analise | 8 | finance/legal/data |
| Operacoes | 7 | ops |
| Compliance | 6 | regulado |
| Inovacao | 6 | startup/produto |
| Tech Cross | 8 | tech |
| People Mgmt | 8 | RH/lideres |
| Org Leadership | 9 | C-level |
| Tech Leadership | 7 | staff+ |
| Culture Ethics | 8 | universal |
| **Total** | **119** | |

| Por fonte |
|---|
| O*NET: 32 |
| BEI: 18 |
| Lominger: 13 |
| Custom: 56 |

| Skills com fairness flag | 4 |
|---|---|
| executive_communication | viés socioeconomico |
| executive_presence | viés genero/raca/socio (alta) |
| bias_interruption | sensivel (recruiter pode discriminar pela resposta) |
| founder_mindset_at_scale | viés socioeconomico (parcial) |

---

## Decisoes de design

### Hierarquia 2 niveis funciona como?
- Cada pergunta gerada -> classificada em 1 skill_probed (filho)
- Effectiveness aprende em ambos: parent stats (rapido, ~1 mes) + filho stats (devagar, ~6-9 meses)
- Runtime usa filho se >=20 amostras; senao parent; senao prior O*NET

### Por que 119 (e nao 200 ou 80)?
- 80 era v1 — cobertura tech-heavy, perde verticais
- 200 dilui learning (cada skill <1 amostra/mes)
- 119 = sweet spot pra cobrir 15 categorias com 5-11 skills cada, threshold de 20 usos atinge em 6-9 meses por skill em escala WeDOTalent

### Skills que podem soar duplicadas mas nao sao
- executive_communication (skill, em Comunicacao) vs executive_presence (skill, em Org Leadership): **comunicacao = clareza/estrutura; presence = postura/inspiracao**. Distinguem.
- influence_without_authority (Vendas) vs influence_without_authority (Org Leadership): **mesma skill** — fica so em Vendas (parent comercial). Em Org Leadership, equivalente e cross_team_alignment.

### Aplicabilidade por senioridade
- jr+ (24 skills): comunicacao basica, execucao, aprendizado
- pl+ (45 skills): + scope, vendas, analise, operacoes
- sr+ (40 skills): + lideranca tecnica, gestao pessoas, estrategia
- ld+ (10 skills): C-level, board, founder mindset

### Fairness flags = 4 skills
Sao skills com risco conhecido de viés (executive_presence é o mais documentado).
**Gate especial em Phase 3 impl**: antes de incluir pergunta dessa skill, rodar fairness audit; se adverse impact > 0.1 vs grupo protegido na empresa-cliente, **bloquear** pra essa empresa + recomendar substituta.

---

## Perguntas abertas para Paulo

1. **WeDOTalent ja tem framework interno** (RH, calibracao, OKRs)? Se sim, devo alinhar nomenclatura.
2. **Cobertura de saude (medico/enfermagem/psicologia)** — adicionar categoria 16? Ou skills atuais sao suficientes?
3. **Cobertura de educacao (professor/coordenador)** — mesma pergunta.
4. **Skills com fairness flag** — manter, remover, ou opt-in apenas?
5. **executive_presence** — sabidamente enviesada. Recomendo remover OU manter so com gate ativado.
6. **Granularidade dentro de Lideranca Tecnica (7 skills)** — esta certo ou faltam coisas tipo distributed_systems, data_intensive_apps, etc?
7. **Vertical missing** — ha alguma vertical que WeDOTalent atende e nao esta coberta aqui?
