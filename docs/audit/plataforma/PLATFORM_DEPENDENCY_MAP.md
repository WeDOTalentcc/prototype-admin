# PLATFORM_DEPENDENCY_MAP.md — Mapa de Dependencias Plataforma <> IA (Bloqueadores)
**Protocolo:** PX07  
**Data:** 2026-04-14  
**Auditor:** Claude Opus 4.6  
**Fontes cruzadas:** PX01, PX02, PX03, PX04, PX05, PX06, P01, P02, P10, P16-P20  
**Contexto:** Frontend + IA no Replit, Backend Rails no GCP. Integracao Rails<>Python via RabbitMQ em configuracao. Redis/RabbitMQ sendo configurados no GCP.

**Depende de:** PX01-PX06, P01-P20  
**Alimenta:** P32 (MIGRATION_PLAN)

---

## LISTA 1: BLOQUEADORES (Fix plataforma ANTES de refatorar agente)

Sem estes fixes, refatoracao de agentes e inutil — os agentes vao operar em cima de infraestrutura quebrada.

| Fix ID | Fonte | Descricao | Agente(s) Bloqueado(s) | Por Que | Esforco |
|--------|-------|-----------|----------------------|---------|---------|
| **BLK-01** | PX01-M01 | `candidates` sem `account_id` — violacao LGPD | TODOS os agentes que tocam candidatos (SourcingReAct, CVScreening, PipelineTransition, AutonomousReAct, CalibrationService) | Agentes criam/buscam candidatos sem isolamento de tenant. Qualquer operacao de candidato e cross-tenant. | M (migration + backfill) |
| **BLK-02** | PX01-CORS | CORS hardcoded `localhost:3000` no Rails | TODOS os agentes que publicam dados via RabbitMQ para Rails | Rails API inacessivel de producao — respostas de agentes que precisam persistir no Rails sao rejeitadas | S (1 linha ENV) |
| **BLK-03** | PX01-PY01 | `RAILS_API_URL` nao configurado — Python opera em banco separado | TODOS os agentes | Candidatos criados pela IA nao chegam ao Rails. Jobs importados no Rails nao chegam ao Python. Dois universos de dados. | S (config env) |
| **BLK-04** | PX01-PY03 | JWT SECRET_KEY diferente entre Python e Rails | Agentes que recebem requests via BFF (todos) | Token gerado pelo Python invalido no Rails e vice-versa. Autenticacao unificada impossivel. | S (compartilhar secret) |
| **BLK-05** | PX01-R01 | `MagicLinksController` nao roteado — 404 | Onboarding LIA agent (PolicySetupAgent) | Flow de onboarding via magic link quebrado — candidato/recrutador nao consegue acessar | S (1 rota) |
| **BLK-06** | PX01-R02 | `OnboardingController` nao roteado — 404 | Onboarding LIA agent + `onboarding_orchestrator.py` | Python chama `/v1/onboarding/progress` que retorna 404. Invite flow quebrado. | S (rotas) |
| **BLK-07** | PX01-W01 | 6 handlers `LiaEventsWorker` sao stubs (log only) | CVScreeningBatchService, InterviewGraph, CommunicationReAct, PipelineTransition | Screening completo, entrevista agendada, oferta enviada, candidato enriquecido, pipeline movido — TUDO descartado pelo Rails. IA trabalha mas resultado nao persiste. | M (implementar 6 handlers) |
| **BLK-08** | PX03-F01 | Email 100% simulado (MAILGUN_API_KEY ausente) | CommunicationReActAgent, CVScreening (convites WSI), InterviewGraph (confirmacao) | Nenhum email real e enviado. Agente "envia email" mas candidato nunca recebe. | S (config secret) |
| **BLK-09** | PX03-F02 | WhatsApp simulado (TWILIO desabilitado) | CommunicationReActAgent, WSI async invites | Convites de triagem e comunicacao via WhatsApp nao chegam. | S (config secret + flag) |
| **BLK-10** | PX04-DRIFT | schema.rb desatualizado (12 tabelas vs 85 migrations) | Qualquer agente que sincronize dados com Rails via RabbitMQ | Se ambiente Rails usa `db:schema:load` em vez de `db:migrate`, 67 migrations nao aplicadas = ~78 tabelas ausentes | M (rails db:migrate + schema:dump no GCP) |
| **BLK-11** | PX01-M03 | `JobImportWorker` hardcoda `account_id: 1` | WizardReActAgent (publicacao de vagas) | Jobs importados ficam todos no tenant 1 — vaga criada pelo agente para empresa X aparece na empresa 1 | S (fix worker) |
| **BLK-12** | PX01-T01 | `ResourceLoader` sem scope de tenant | TODOS os agentes que leem dados via Rails API | Read de candidato/job pode retornar dados de outro tenant — violacao de dados | S (fix concern) |
| **BLK-13** | PX05-ONBOARD | Proxy onboarding aponta para localhost:3000 | Onboarding LIA agent | Frontend chama `/api/backend-proxy/onboarding/**` que vai para localhost:3000 inexistente — loading infinito | S (check + 503) |
| **BLK-14** | PX06-ATLASSIAN | API Key Atlassian em texto claro no arquivo `replit` | Nao bloqueia agentes diretamente | Risco de seguranca: acesso nao autorizado ao Jira/Confluence | S (revogar + Replit Secret) |
| **BLK-15** | PX01-PY04 | WSManager singleton in-memory | Agentes que emitem via WebSocket (todos os ReAct agents) | Com multiplos workers, WS de um worker e invisivel para outros. Respostas de agente perdidas. | M (Redis pub/sub) |

---

## LISTA 2: PARALELOS (Fix plataforma EM PARALELO com refatoracao de agente)

Podem ser feitos ao mesmo tempo que se refatora agentes. Nao bloqueiam, mas melhoram qualidade.

| Fix ID | Fonte | Descricao | Impacto se Nao Fixar | Pode Esperar? |
|--------|-------|-----------|---------------------|---------------|
| **PAR-01** | PX01-T02 | Apartment elevators comentados — schema switching nunca ocorre | Multi-tenancy Rails incompleto. Row-level funciona via account_id, mas sem schema isolation | Sim — row-level e suficiente enquanto integracao nao esta completa |
| **PAR-02** | PX01-T03 | Elasticsearch search sem tenant scope | Busca retorna candidatos de todos os tenants | Sim se SEARCH_BACKEND=postgres (padrao) — Elasticsearch desabilitado |
| **PAR-03** | PX01-A01 | RBAC implementado mas zero controllers usam `authorize` | Sem controle de permissao granular | Sim — auth basica funciona |
| **PAR-04** | PX01-P01 | Bunny (RabbitMQ) abre conexao TCP nova por request | Performance degradada, conexoes TCP esgotam | Sim para dev, NAO para prod com volume |
| **PAR-05** | PX03-F03 | Stripe em simulation mode | Cobranca nao funciona | Sim — nao e MVP |
| **PAR-06** | PX03-F05 | Sneakers (RabbitMQ consumer Rails) COMENTADO no docker-compose | Canal Rails->Python pode estar inativo | Verificar se esta rodando no GCP |
| **PAR-07** | P19-P0 | CalibrationWeight nao consumido por agentes | Loop de calibracao nao fecha — dashboard informativo apenas | Sim, mas alto ROI |
| **PAR-08** | P19-P0 | SearchFeedback nao alimenta re-ranking | Likes/dislikes coletados sem uso | Sim, mas alto ROI |
| **PAR-09** | P19-P1 | ModelRegistry in-memory (perde estado no restart) | Versoes de modelos perdidas | Sim para dev |
| **PAR-10** | P20-P1 | ML Predictions sem dashboard frontend | Predicoes invisiveis ao recrutador | Sim — feature nova, nao fix |
| **PAR-11** | P20-P1 | Calibration analytics sem dashboard frontend | Divergencias LIA<>recrutador invisiveis | Sim — feature nova |
| **PAR-12** | PX05-STALE | Kanban nao atualiza em real-time apos acao do agente | Recrutador precisa refresh manual | Sim, mas UX ruim |
| **PAR-13** | PX06-CI-PY | Zero CI/CD para Python | Regressoes e vulnerabilidades nao detectadas | Sim para dev, NAO para prod |
| **PAR-14** | PX06-CI-FE | Zero CI/CD para Frontend | Mesma razao | Sim para dev |
| **PAR-15** | PX06-RAILS-VER | Rails 7.1.0 desatualizado (patches pendentes) | CVEs nao corrigidos | NAO — atualizar assim que possivel |
| **PAR-16** | P19-P1 | Candidate lifecycle model inexistente | Sem distincao lead/active/hired/alumni | Sim — feature nova |

---

## LISTA 3: INDEPENDENTES (Fix plataforma sem relacao com agentes)

Nao impactam agentes. Podem ser feitos a qualquer momento.

| Fix ID | Fonte | Descricao | Severidade | Quando Fixar |
|--------|-------|-----------|-----------|-------------|
| **IND-01** | PX05-LEGACY | Pagina legacy `/funil` duplicada | Baixo | Cleanup |
| **IND-02** | PX05-CSP | CSP com `unsafe-eval` | Medio | Quando Next.js suportar nonce |
| **IND-03** | PX06-TOKEN-BL | JWT sem blacklist apos logout | Medio | Sprint 2-3 |
| **IND-04** | PX06-LOCKOUT | Sem account lockout apos N tentativas | Medio | Sprint 2-3 |
| **IND-05** | PX06-OTEL | OpenTelemetry configurado mas endpoint vazio | Medio | Deploy GCP |
| **IND-06** | PX06-SENTRY-RAILS | Sentry nao configurado no Rails | Alto | Sprint 1 |
| **IND-07** | PX06-DEV-LOGIN | DEV_AUTO_LOGIN em docker-compose | Medio | Mover para .env |
| **IND-08** | PX06-GEMFILE-PIN | elasticsearch, sneakers, jwt sem version pin | Medio | Sprint 1 |
| **IND-09** | PX04-IDX-EMAIL | `users.email` sem indice | Alto | Imediato (performance) |
| **IND-10** | PX01-M06 | 100+ models .rb sem tabela no schema | Baixo | Cleanup apos migrations |
| **IND-11** | PX03-REDIS-SPOF | Redis e SPOF (cache + broker + DLQ + rate limit) | Alto | Arquitetura (Redis Sentinel/Cluster) |
| **IND-12** | PX03-REDIS-AUTH | Redis sem autenticacao | Alto | Config (requirepass) |
| **IND-13** | PX03-PII-REDIS | PII em plaintext no Redis (TOONCards, semantic cache) | Alto | Encriptar ou TTL curto |

---

## DIAGRAMA DE SEQUENCIA DE EXECUCAO

```
FASE A: DESBLOQUEADORES CRITICOS (Semana 1-2)
══════════════════════════════════════════════
Sprint 0 — Config imediata (< 1 dia total)
  ├── BLK-14: Revogar API Key Atlassian (10 min)
  ├── BLK-02: Fix CORS Rails → ENV.fetch('ALLOWED_ORIGINS') (30 min)
  ├── BLK-03: Configurar RAILS_API_URL no Replit (15 min)
  ├── BLK-04: Compartilhar JWT SECRET_KEY Python = Rails (15 min)
  ├── BLK-05: Rotear MagicLinksController (15 min)
  ├── BLK-06: Rotear OnboardingController (15 min)
  ├── BLK-08: Configurar MAILGUN_API_KEY nos Secrets (10 min)
  ├── BLK-09: Configurar TWILIO + ENVIRONMENT=production (10 min)
  ├── BLK-11: Fix JobImportWorker account_id do payload (30 min)
  ├── BLK-13: Fix proxy onboarding fallback localhost (30 min)
  └── Total Sprint 0: ~3-4 horas de trabalho

Sprint 1 — Tenant Isolation + Schema (3-5 dias)
  ├── BLK-01: Migration add_column candidates.account_id + backfill
  ├── BLK-10: rails db:migrate && rails db:schema:dump no GCP
  ├── BLK-12: Fix ResourceLoader com tenant scope
  ├── IND-09: Add index on users.email
  └── IND-06: Configurar Sentry no Rails

Sprint 2 — Workers + WebSocket (3-5 dias)
  ├── BLK-07: Implementar 6 handlers LiaEventsWorker (screening, interview, offer, enrichment, pipeline, onboarding)
  ├── BLK-15: WSManager -> Redis pub/sub para multi-worker
  └── PAR-04: Bunny connection pool

════════════════════════════════════════════════
CHECKPOINT: Integracao basica Rails <> Python funcional
  - Candidatos com tenant isolation
  - JWT unificado
  - Email/WhatsApp reais
  - Workers processando eventos de IA
  - WebSocket multi-worker
════════════════════════════════════════════════

FASE B: REFATORACAO DE AGENTES + FIXES PARALELOS (Semana 3-6)
══════════════════════════════════════════════════════════════
Sprint 3-4 — Agentes (requerem Fase A completa)
  ├── P35: Consolidacao de fontes canonicas (CRUD -> Rails, IA -> Python)
  ├── P36: Refatoracao agente por agente (cada agente usa Rails para CRUD)
  ├── PAR-07: Fechar loop CalibrationWeight -> scoring
  ├── PAR-08: SearchFeedback -> re-ranking
  └── PAR-12: Kanban real-time via WS event

Sprint 5-6 — Features de IA avancada
  ├── P38-P40: Certificacao de inteligencia por agente
  ├── PAR-10: ML Predictions dashboard frontend
  ├── PAR-11: Calibration analytics dashboard
  ├── PAR-16: Candidate lifecycle model
  └── PAR-09: Persistir ModelRegistry em DB

Em paralelo durante toda Fase B:
  ├── PAR-13: CI/CD para Python
  ├── PAR-14: CI/CD para Frontend
  ├── PAR-15: Atualizar Rails 7.1.0 -> 7.1.5+
  └── PAR-06: Verificar Sneakers no GCP

FASE C: OTIMIZACAO E CLEANUP (Semana 7+)
═════════════════════════════════════════
  ├── IND-01: Remover pagina /funil legacy
  ├── IND-02: CSP com nonce
  ├── IND-03: JWT blacklist no logout
  ├── IND-04: Account lockout
  ├── IND-05: Ativar OpenTelemetry
  ├── IND-07: Mover DEV_AUTO_LOGIN para .env
  ├── IND-08: Pin versions no Gemfile
  ├── IND-10: Cleanup models sem tabela
  ├── IND-11: Redis Sentinel/Cluster
  ├── IND-12: Redis auth (requirepass)
  ├── IND-13: Encriptar PII no Redis
  ├── PAR-01: Apartment elevators
  ├── PAR-02: Elasticsearch tenant scope
  ├── PAR-03: RBAC enforcement
  └── PAR-05: Stripe real
```

---

## MATRIZ DE IMPACTO CRUZADO

### Quais agentes sao desbloqueados por qual fix?

| Agente | BLK-01 (account_id) | BLK-03 (RAILS_URL) | BLK-07 (Workers) | BLK-08 (Email) | BLK-09 (WhatsApp) | BLK-15 (WSManager) |
|--------|---------------------|--------------------|--------------------|----------------|--------------------|--------------------|
| **SourcingReAct** | CRITICO | CRITICO | ALTO | - | - | ALTO |
| **CVScreeningBatch** | CRITICO | CRITICO | CRITICO | ALTO | ALTO | - |
| **InterviewGraph** | CRITICO | CRITICO | CRITICO | CRITICO | - | - |
| **CommunicationReAct** | - | ALTO | ALTO | CRITICO | CRITICO | - |
| **PipelineTransition** | CRITICO | CRITICO | CRITICO | - | - | ALTO |
| **WizardReAct** | ALTO | ALTO | - | - | - | - |
| **AutonomousReAct** | CRITICO | CRITICO | ALTO | ALTO | ALTO | ALTO |
| **OnboardingLIA** | - | CRITICO | - | ALTO | ALTO | - |
| **CalibrationService** | ALTO | ALTO | - | - | - | - |
| **CustomAgentRuntime** | ALTO | ALTO | - | - | - | ALTO |
| **DigitalTwin** | ALTO | ALTO | - | - | - | - |
| **AnalyticsReAct** | ALTO | ALTO | - | - | - | - |

### Desbloqueio progressivo

```
Apos Sprint 0 (config):    Email + WhatsApp reais, JWT unificado, rotas existem
Apos Sprint 1 (tenant):    Candidatos isolados, schema atualizado
Apos Sprint 2 (workers):   IA workflows persistem no Rails, WS multi-worker
= TODOS OS AGENTES FUNCIONAIS EM INTEGRACAO REAL
```

---

## CONTAGEM FINAL

| Categoria | Quantidade | % do Total |
|-----------|-----------|-----------|
| **BLOQUEADORES** | 15 | 36% |
| **PARALELOS** | 16 | 38% |
| **INDEPENDENTES** | 13 | 31% |
| **TOTAL de findings classificados** | 44 | 100% |

**Todos os findings de PX01-PX06 + P19-P20 foram classificados.**

---

## RESUMO EXECUTIVO

### A regra de ouro
**NAO refatore agentes antes de completar Sprint 0 + Sprint 1 da Fase A.** Refatorar agentes sobre infraestrutura quebrada (sem tenant isolation, sem email real, sem JWT unificado) e construir sobre areia.

### O caminho critico
```
Sprint 0 (~4h) -> Sprint 1 (3-5d) -> Sprint 2 (3-5d) = FASE A completa
                                                          |
                                                          v
                                              Agentes podem ser refatorados
                                              com confianca de que a infra suporta
```

### Os 3 fixes de maior ROI (desbloqueiam mais agentes por hora de trabalho)
1. **BLK-03 (RAILS_API_URL)** — 15 min, desbloqueia integracao para TODOS os agentes
2. **BLK-08 (MAILGUN_API_KEY)** — 10 min, desbloqueia toda comunicacao real
3. **BLK-01 (candidates.account_id)** — 1-2 dias, desbloqueia LGPD + todas as operacoes de candidato
