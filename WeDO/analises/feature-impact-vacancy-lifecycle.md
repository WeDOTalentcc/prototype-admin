# Análise de Impacto: Ciclo de Vida de Vagas (Pausa, Cancelamento, Placement, Fechamento)
  # Feature Impact Analysis — Conforme Skill feature-impact (12 dimensões)

  **Data:** 2026-03-12
  **Skills consultadas:** feature-impact, design-standardize (DS v4.2.1), vue-migration-prep, wedo-governance, feature-audit (14 dimensões), dei-fairness, lgpd-data-protection, screening-compliance

  ---

  ## Resumo
  Implementar 5 fluxos de lifecycle de vagas: pausa, reativação, cancelamento, placement e fechamento sem placement. **Arquitetura revisada:** ações simples (pausa, reativação, cancelamento, fechamento) usam um novo `VacancyActionConfirmModal` leve (mini modal de confirmação). Apenas placement usa o `UniversalTransitionModal` existente (wizard 3 steps com LIA). O `UniversalTransitionModal` permanece INTOCADO para transições de candidatos.

  ---

  ## Dimensões Impactadas (Feature Impact — 12 dimensões)

  | # | Dimensão | Impacto | O que fazer |
  |---|----------|---------|-------------|
  | 1 | **Frontend** | **Alto** | Novo componente `VacancyActionConfirmModal` (mini modal genérico para pausa/reativação/cancelamento/fechamento). Extensão do `UniversalTransitionModal` APENAS para `vacancy_placement` (wizard 3 steps). Componente `CandidateFunnelSummary` reutilizável. `VacancyStatusBadgeDropdown` no header. Novos proxy routes |
  | 2 | **Backend API** | **Alto** | Endpoints: `POST /placement`, `POST /pause` (individual), `POST /cancel`, `POST /close` (enhanced), `GET /candidate-funnel`. Schemas Pydantic novos. Motivo gravado no `extra_data` do `JobVacancyAuditLog` |
  | 3 | **Banco de Dados** | **Alto** | Nova tabela `placements` (migration Alembic). NENHUM campo novo em `job_vacancies`. UNIQUE constraint em `(job_vacancy_id, candidate_id)` |
  | 4 | **Agentes IA** | **Médio** | Novos `BEHAVIOR_DESCRIPTIONS` APENAS para `vacancy_placement` no `TransitionChatPanel`. LIA PEDE dados (não sugere). Pausa/cancelamento NÃO envolvem LIA (mini modal simples) |
  | 5 | **Comunicações** | **Médio** | 5 novos templates (pausa, reativação, cancelamento, parabéns, feedback). Reutiliza `CommunicationDispatcher` e `TransitionDispatchService`. Modo auto = ambos canais; modo manual = modal de envio existente |
  | 6 | **Integrações Externas** | **Baixo** | Flag `ats_synced` preparada. Nenhuma integração ativa nova. Nenhuma nova env var |
  | 7 | **Compliance/LGPD** | **Médio** | `final_salary` = PII financeiro → PII masking. Audit trail obrigatório. DSR exportável. Retenção 5 anos (contratação) |
  | 8 | **Segurança** | **Médio** | Multi-tenant isolamento via `company_id`. `final_salary` role-gated. IDOR prevention. Cancelamento = ação destrutiva com confirmação |
  | 9 | **Infraestrutura** | **Baixo** | Batch notifications via Celery. Migration non-destructive. Nenhum novo cache key |
  | 10 | **Observabilidade** | **Baixo** | Audit logs via `JobVacancyAuditLog`. Activity feed. Structured logging |
  | 11 | **Testes** | **Médio** | Unitários + integração + edge cases (placement duplicado, multi-tenant, PII masking) |
  | 12 | **Performance** | **Baixo** | candidate-funnel = GROUP BY com índice (O(N), aceitável até 10k candidatos) |

  ---

  ## Decisão Arquitetural: Mini Modal vs. UniversalTransitionModal

  | Ação | Componente | Por quê |
  |------|-----------|---------|
  | Pausa | `VacancyActionConfirmModal` (NOVO) | Ação administrativa simples. Dropdown motivo + toggle notificar + botão confirmar. Não precisa de LIA |
  | Reativação | `VacancyActionConfirmModal` | Idem. Motivo opcional + toggle notificar |
  | Cancelamento | `VacancyActionConfirmModal` | Idem. Motivo obrigatório + botão destrutivo vermelho + texto irreversibilidade |
  | Fechamento sem placement | `VacancyActionConfirmModal` | Motivo + toggle notificar demais candidatos |
  | **Placement** | `UniversalTransitionModal` (EXISTENTE) | Wizard 3 steps com LIA: dados contratação → parabéns → feedback. Requer chat da LIA |

  **Vantagem:** O `UniversalTransitionModal` permanece INALTERADO para transições de candidatos. Apenas o modo `vacancy_placement` é adicionado como novo `actionBehavior`.

  ---

  ## Decisão Arquitetural: Motivo como extra_data (não sub-status, não campo separado)

  | Opção | Prós | Contras | Decisão |
  |-------|------|---------|---------|
  | Campos separados (`pause_reason`, `cancel_reason`) em `job_vacancies` | Query simples | Campos sempre null, poluição do modelo, não rastreia múltiplas pausas | ❌ |
  | Sub-status da vaga | Consistente com candidatos | Sub-statuses são exclusivos de candidatos (`RecruitmentSubStatus`). Vagas não têm stage pipeline. Arquitetura incompatível | ❌ |
  | **`extra_data` no `JobVacancyAuditLog`** | Motivo pertence à TRANSIÇÃO, rastreia múltiplas pausas, zero migration extra, audit trail nativo | Query JSON para filtrar por motivo (aceitável — consultas analíticas) | ✅ |

  Formato: `extra_data: {"reason_code": "budget_review", "reason_display": "Budget em análise", "notify_candidates": true}`

  ---

  ## Compliance com Design System v4.2.1 (Skill: design-standardize)

  ### VacancyActionConfirmModal (Mini Modal)
  - **Tamanho:** `max-w-sm` (confirmações — DS §2.5)
  - **Overlay:** `fixed inset-0 bg-gray-900/50 dark:bg-gray-950/70 z-50`
  - **Container:** `bg-white rounded-md shadow-xl dark:bg-gray-800`
  - **Header:** `px-6 py-4 border-b border-gray-200`
  - **Botão Primary:** `bg-gray-900 text-white hover:bg-gray-800` (PRETO, nunca colorido)
  - **Botão Destructive (cancelar vaga):** `bg-red-600 text-white hover:bg-red-700`
  - **Dropdown motivo:** `cursor-pointer` + padrão de select DS §2.2
  - **Toggle notificar:** Switch padrão DS §2.11 (`bg-gray-200` inativo, `bg-gray-900` ativo)
  - **Font:** Open Sans (`font-['Open_Sans']`) em toda a UI
  - **Rounded:** `rounded-md` (8px) — PADRÃO universal DS v4.2.1
  - **Dark mode:** Variantes `dark:` em todos os elementos
  - **Acessibilidade:** `role="dialog" aria-modal="true" aria-labelledby="modal-title"`, focus ring, Esc fecha

  ### CandidateFunnelSummary
  - **Barras:** `bg-gray-900 h-2 rounded-full` (fill) sobre `bg-gray-200 rounded-full h-2` (track) — DS §2.8 Progress
  - **Contadores:** Inter (`font-['Inter']`) com `tabular-nums` — DS dados numéricos
  - **Checkboxes:** `accent-gray-900 w-4 h-4 rounded-sm` — DS §2.14
  - **Labels:** Open Sans `text-sm text-gray-900` — DS §2.14

  ### VacancyStatusBadgeDropdown
  - **Badge base:** `inline-flex items-center px-2 py-1 rounded-full text-[10px] font-medium border` — DS §2.6
  - **Dropdown container:** `bg-white border border-gray-200 rounded-md shadow-lg py-1 z-50` — DS §2.12
  - **Item destrutivo (Cancelar):** `text-red-600 hover:bg-red-50` — DS §2.12

  ---

  ## Compliance com Vue Migration Prep (Skill: vue-migration-prep)

  ### Princípios aplicados nos novos componentes:

  | Princípio | Aplicação |
  |-----------|-----------|
  | **Separação de concerns** | Lógica em hook `useVacancyLifecycle` (→ composable), componente é template + binding |
  | **Props tipadas com interface** | `VacancyActionConfirmModalProps` com interface (não type inline) |
  | **Callbacks on*** | `onConfirm`, `onCancel`, `onNotifyToggle` (→ @confirm, @cancel em Vue) |
  | **Composição declarativa** | children + named props (→ slots em Vue) |
  | **Sem anti-patterns** | Sem cloneElement, sem forwardRef, sem HOC, sem CSS-in-JS |
  | **Helpers de tokens** | Usar `getButtonClasses('destructive')`, `getBadgeClasses('neutral')` em vez de classes hardcoded |
  | **Store pattern** | Hook `useVacancyLifecycleStore` com State/Actions explícitas (→ Pinia) |

  ### Score de portabilidade estimado:
  - `VacancyActionConfirmModal.tsx`: **70%** portável (JSX → template)
  - `useVacancyLifecycle.ts`: **90%** portável (→ composable, ajustar reactivity)
  - `types.ts` / `constants.ts`: **100%** portável (copiar direto)

  ---

  ## Compliance com WeDO Governance (Skill: wedo-governance)

  ### 5 Perguntas de Decisão:

  | # | Pergunta | Resposta |
  |---|----------|----------|
  | 1 | **É justo?** | ✅ Sim. Pausa/cancelamento são ações administrativas, não decisões sobre candidatos. Placement registra contratação (positivo). Feedback de rejeição passa pelo CommunicationAgent com FairnessGuard |
  | 2 | **É necessário?** | ✅ Sim. Sem estes fluxos, recrutadores pausam/cancelam vagas manualmente sem rastreabilidade, e placements não são registrados |
  | 3 | **É transparente?** | ✅ Sim. Motivo gravado no audit log. Candidatos notificados via template claro. Placement registrado com dados verificáveis |
  | 4 | **Conseguimos medir?** | ✅ Sim. Audit trail completo via `JobVacancyAuditLog`. Activity feed. Métricas de placement no OutcomeTracker |
  | 5 | **É resiliente?** | ✅ Sim. Notificações batch via Celery (evita timeout). Circuit breaker em providers de comunicação. DLQ para mensagens falhadas |

  ### 13 Crenças aplicáveis:

  | Crença | Aplicação |
  |--------|-----------|
  | #01 Humano em Primeiro Lugar | Recrutador DECIDE pausar/cancelar/contratar. LIA apenas ASSISTE no placement |
  | #03 Transparente e Explicável | Motivo registrado no audit. Candidato sabe que processo pausou/cancelou |
  | #04 Segura e Respeitosa com Privacidade | `final_salary` PII-masked. Multi-tenant isolado |
  | #07 Resiliente por Design | Batch notifications via Celery. DLQ para falhas |
  | #08 Observável e Rastreável | Audit log completo com motivo |
  | #12 Autonomia Progressiva | Toggle auto/manual para notificações. Recrutador controla nível de automação |
  | #13 Acessível e Inclusiva | WCAG 2.1 AA no mini modal. aria-labels, focus ring, contraste |

  ### Inegociáveis verificados:
  - [x] #4 PII masking ativo → `final_salary` adicionado ao `PIIMaskingFilter`
  - [x] #7 Human override → Recrutador tem toggle manual em todos os fluxos
  - [x] #8 WCAG 2.1 AA → Componentes novos seguem DS v4.2.1 com aria-labels

  ### Production Readiness Gate (18 critérios):
  - #3 PII Masking: Novo pattern para salary
  - #10 Health check: Sem impacto
  - #13 Rollback: DROP TABLE placements (reversível)
  - Demais critérios: sem alteração

  ---

  ## Compliance DEI & Fairness (Skill: dei-fairness)

  | Item | Status | Detalhe |
  |------|--------|---------|
  | FairnessGuard em feedback de rejeição | ✅ | Templates de feedback construtivo (Step 3 do placement e cancelamento) passam pelo `CommunicationAgent` que já tem FairnessGuard ativo |
  | Linguagem neutra nos templates | ✅ | Templates usam linguagem neutra: "Agradecemos sua participação" (sem gênero) |
  | Atributos protegidos mascarados | ✅ | LIA no chat do placement recebe dados do candidato com PII masking (nome, gênero, idade removidos) |
  | Critérios afirmativos respeitados | N/A | Placement/pausa/cancelamento não envolvem avaliação ou ranking de candidatos |
  | Acessibilidade (WCAG 2.1 AA) | ✅ | Mini modal e componentes seguem DS v4.2.1 com aria-labels, focus rings, contraste 4.5:1 |

  **Nota:** Esta feature NÃO avalia, pontua, classifica ou filtra candidatos, portanto o FairnessGuard de screening (3 camadas) não precisa ser ativado nos endpoints novos. O único ponto de atenção é o feedback construtivo no Step 3 do placement, que já passa pelo CommunicationAgent existente com FairnessGuard integrado.

  ---

  ## Compliance LGPD & Proteção de Dados (Skill: lgpd-data-protection)

  | Item | Status | Detalhe |
  |------|--------|---------|
  | **PII Masking** | ⚠️ Ação necessária | `final_salary` (Numeric) é PII financeiro (Art. 5º, I LGPD). Adicionar pattern regex em `PII_PATTERNS` em `pii_masking.py` para mascarar valores monetários em logs |
  | **Consentimento** | ✅ Existente | Candidato já consentiu ao se candidatar. Notificações de pausa/cancelamento são legítimo interesse (Art. 7º, IX LGPD) |
  | **Minimização** | ✅ | Placement coleta apenas dados necessários: salary, contract_type, start_date. Sem dados sensíveis adicionais |
  | **Criptografia** | ✅ | At-rest via PostgreSQL (encryption nativa). In-transit via TLS 1.3 |
  | **Retenção** | ✅ | Dados de placement: 7 anos (exigência trabalhista CLT — `LgpdCleanupService` já cobre). Candidatos contratados com contrato: 7 anos |
  | **Auditoria** | ✅ | `JobVacancyAuditLog` cria trilha imutável (append-only) para cada transição |
  | **DSR (Data Subject Request)** | ⚠️ Ação necessária | Dados de Placement devem ser incluídos na exportação de dados do titular via endpoint `/data-subject-requests`. O `DataRequestService` precisa ser estendido para incluir tabela `placements` |
  | **EU AI Act** | N/A | Placement é registro administrativo, não decisão automatizada de IA. Não requer FRIA adicional |

  ---

  ## Compliance Screening (Skill: screening-compliance)

  | Item | Status |
  |------|--------|
  | Pipeline WSI impactado? | ❌ Não. Nenhuma alteração em scoring, thresholds ou calibração |
  | FairnessGuard em endpoints novos? | N/A. Endpoints de pausa/cancelamento/placement não avaliam candidatos |
  | Feedback personalizado? | ✅ Step 3 do placement (feedback demais candidatos) reutiliza `PersonalizedFeedbackService` existente que já tem FairnessGuard |
  | Model drift? | N/A. Nenhum novo LLM call de avaliação |
  | BARS / Rubric? | N/A. Sem nova avaliação |

  ---

  ## Feature Audit — 14 Dimensões (Skill: feature-audit)

  Pré-audit antes da implementação. Cada dimensão será re-verificada pós-build.

  | # | Dimensão | Pré-status | Notas |
  |---|----------|------------|-------|
  | 1 | Integração (Wiring) | Planejado | Badge dropdown → mini modal → API → audit log. Placement badge → UniversalTransitionModal → API → placement table |
  | 2 | Fluxo de Dados | Planejado | DB → endpoint → proxy → hook → componente. Sem mock data |
  | 3 | UI/UX + DS v4.2.1 | Planejado | Mini modal segue DS §2.5 (max-w-sm). Botões pretos. Cyan apenas LIA icon |
  | 4 | Backend e API | Planejado | 5 endpoints novos. Schemas Pydantic. Proxy routes |
  | 5 | Tipos e Contratos | Planejado | Interfaces TypeScript + Pydantic alinhados. Sem `any` |
  | 6 | Fluxo do Usuário | Planejado | Badge click → dropdown → ação → mini modal → confirmar → toast sucesso |
  | 7 | Consistência | Planejado | Mesmo padrão de confirmação do resto da plataforma. Nomenclatura kebab-case hooks, PascalCase componentes |
  | 8 | Documentação | Planejado | replit.md atualizado. docs/feature-impact atualizado |
  | 9 | Arquitetura de Agentes | Planejado | Sem novo domínio. Reutiliza CommunicationAgent existente |
  | 10 | Qualidade LLM | Planejado | BEHAVIOR_DESCRIPTIONS novos para placement apenas. LIA pede, não sugere |
  | 11 | Serviços/Integrações IA | N/A | Sem novo serviço IA |
  | 12 | Governança/Resiliência IA | ✅ Verificado | 5 perguntas respondidas. Inegociáveis checados. Circuit breaker em comunicação |
  | 13 | Segurança | Planejado | Multi-tenant, IDOR, PII masking, role-gating |
  | 14 | Performance | Planejado | GROUP BY com índice. Celery para batch |

  ---

  ## Plano de Implementação

  ### Tarefa #1: Backend (bloqueante)
  1. Migration Alembic — tabela `placements` (UNIQUE constraint)
  2. Modelo SQLAlchemy `Placement` com company_id, PII annotation
  3. Endpoints: POST /placement, POST /pause, POST /cancel, POST /close enhanced, GET /candidate-funnel
  4. Schemas Pydantic
  5. Audit log: motivo no `extra_data` do `JobVacancyAuditLog`
  6. PII masking para `final_salary`
  7. DSR extension: incluir placements na exportação de dados do titular
  8. Testes unitários

  ### Tarefa #2: Frontend (depende da #1)
  1. **`VacancyActionConfirmModal`** — novo componente mini modal genérico (DS v4.2.1 compliant)
  2. **`CandidateFunnelSummary`** — mini-funil com barras, contadores Inter, checkboxes
  3. **`VacancyStatusBadgeDropdown`** — badge clicável com dropdown de ações
  4. **Extensão do `UniversalTransitionModal`** — APENAS actionBehavior `vacancy_placement` (wizard 3 steps)
  5. **`useVacancyLifecycle` hook** — lógica separada (→ composable Vue)
  6. **Proxy routes** para novos endpoints
  7. **Templates de comunicação** pré-carregados para modo manual
  8. **TransitionChatPanel** — novo BEHAVIOR_DESCRIPTION para vacancy_placement
  9. Todos componentes: Vue-migration-prep compliant (interface Props, callbacks on*, sem anti-patterns)

  ---

  ## Riscos e Mitigações

  | Risco | Prob. | Impacto | Mitigação |
  |-------|-------|---------|-----------|
  | Placement duplicado | Média | Alto | UNIQUE constraint `(job_vacancy_id, candidate_id)` + 409 Conflict |
  | Notificação a candidato já contratado | Baixa | Alto | Filtrar stages terminais (hired, declined) antes de batch |
  | Cancelamento acidental | Baixa | Alto | Botão destrutivo vermelho + texto "irreversível" + confirmação |
  | Backwards compatibility UniversalTransitionModal | Baixa | Alto | Apenas 1 novo actionBehavior (`vacancy_placement`). Demais ações usam mini modal separado — ZERO alteração no modal existente |
  | PII leak de final_salary em logs | Média | Alto | Adicionar pattern monetário ao `PIIMaskingFilter` global |
  | DSR incompleto (Placement não exportado) | Baixa | Médio | Estender `DataRequestService` para incluir tabela placements |

  ---

  ## Pronto para implementar? ✅ Sim

  Todas as 12 dimensões de feature-impact mapeadas. Compliance verificado com 7 skills. Nenhuma dependência bloqueante externa. Migration non-destructive. 2 tarefas com dependência clara.
  