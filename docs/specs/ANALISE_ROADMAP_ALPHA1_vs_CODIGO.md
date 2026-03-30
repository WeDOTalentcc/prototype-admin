# Análise Profunda: Roadmap Alpha 1 vs. Código Existente

**Data:** 30/03/2026  
**Escopo:** Cruzamento do Fluxo Alpha 1 (v2) com a implementação real no Replit  
**Objetivo:** Identificar gaps, mapear agentes/domínios/serviços/tools/camadas de compliance, e gerar mapa de prioridades de construção

---

## 1. VISÃO GERAL — O QUE EXISTE vs. O QUE FALTA

### 1.1 Resumo Executivo

O backend (`lia-agent-system`) possui uma arquitetura robusta com 10+ domínios, 30+ tools registradas, 6+ agentes ReAct migrados para LangGraph, e camadas de compliance (FairnessGuard, PII Masking, Fact-Checker, Audit Service) implementadas. O frontend (`plataforma-lia`) tem integração real via proxy Next.js → FastAPI.

**Porém, a distância entre "código existente" e "MVP funcional Alpha 1" está em 3 eixos:**

1. **Integração ponta-a-ponta** — Muitos serviços existem isolados mas não estão conectados no fluxo completo
2. **Infraestrutura externa** — ATS real (Gupy/Pandapé), Twilio WhatsApp, Resend/SendGrid, Apify, Microsoft Teams dependem de credenciais e configuração de produção
3. **Camadas de compliance ativas** — Existem no código mas precisam ser "ligadas" (feature flags, environment vars) em cada ponto do fluxo

---

## 2. MAPA COMPLETO: ETAPAS DO ALPHA 1 × AGENTES × DOMÍNIOS × SERVIÇOS × TOOLS × CAMADAS

### ETAPA 1: LOGIN

| Dimensão | Componente | Status | Localização |
|----------|-----------|--------|-------------|
| **Domínio** | Auth | Implementado | `app/api/v1/auth.py` |
| **Serviço** | AuthService (JWT + WorkOS SSO) | Implementado | `app/services/auth_service.py` |
| **Tool** | — (não é agente) | N/A | — |
| **Frontend** | Login page + auth hooks | Implementado | `src/app/(auth)/login/` |
| **Camadas Ativas** | | | |
| ↳ PII Masking | Logs de login mascarados | Ativo | `PIIMaskingFilter` global |
| ↳ Rate Limiting | Tentativas de login | A CONFIGURAR | `rate_limiter.py` |
| ↳ Audit | Login events | A CONFIGURAR | Precisa log de auth events |

**Gap:** Rate limiting de login precisa ser configurado. Audit trail de autenticação precisa ser ativado.

---

### ETAPA 2: EDITAR VAGA (importada do ATS)

| Dimensão | Componente | Status | Localização |
|----------|-----------|--------|-------------|
| **Agente** | Ag.8 IntegradorATS | Implementado | `app/domains/ats_integration/` |
| **Domínio** | `ats_integration` + `job_management` | Implementado | `app/domains/` |
| **Serviços** | ATSSyncService, GupyClient, PandapeClient | Implementado | `app/services/ats_sync_service.py` |
| **Tools** | `sync_candidate_to_ats`, `fetch_candidate_from_ats`, `validate_ats_fields` | Registradas | `ats_integration_tool_registry.py` |
| **Frontend** | Página de vagas + edição | Implementado | `src/app/(dashboard)/jobs/` |
| **Camadas Ativas** | | | |
| ↳ FairnessGuard L1 | Bloquear requisitos discriminatórios no JD | PRECISA ATIVAR | Inserir no pipeline de save do JD |
| ↳ FairnessGuard L2 | Alertar termos implicitamente enviesados | PRECISA ATIVAR | Inserir no pipeline de save do JD |
| ↳ PII Masking | Strip PII antes de enviar ao LLM | Ativo (global) | `strip_pii_for_llm_prompt` |
| ↳ Audit | Log de edições de vaga | PRECISA ATIVAR | `audit_service.py` |
| ↳ LGPD | Dados do ATS com consentimento | PRECISA VERIFICAR | Verificar fluxo de import |

**Gap:** O sync com ATS real depende de credenciais de produção (API keys Gupy/Pandapé). FairnessGuard precisa ser inserido como middleware no endpoint de salvar vaga.

---

### ETAPA 3: CONFIGURAR ROTEIRO WSI

| Dimensão | Componente | Status | Localização |
|----------|-----------|--------|-------------|
| **Agente** | Ag.4 EntrevistadorWSI | Implementado | `app/domains/cv_screening/` |
| **Domínio** | `cv_screening` (WSI) + `wizard` | Implementado | `app/domains/` |
| **Serviços** | WSIService, JDGeneratorService | Implementado | `wsi_service.py`, `jd_generator_service.py` |
| **Tools** | `generate_screening_questions`, `analyze_jd_and_suggest_competencies` | Registradas | WSI domain tools |
| **Frontend** | Modal WSI + Preview Vaga | Implementado | `src/components/modals/` |
| **Camadas Ativas** | | | |
| ↳ FairnessGuard L1-L2 | Perguntas geradas sem viés | PRECISA ATIVAR | Pós-geração de perguntas WSI |
| ↳ Fact-Checker | Validar claims nas perguntas | PRECISA ATIVAR | `fact_checker.py` |
| ↳ Audit | Log de geração de roteiro | PRECISA ATIVAR | `audit_service.py` |
| ↳ PII Masking | Strip antes de enviar JD ao LLM | Ativo | `strip_pii_for_llm_prompt` |

**Gap:** O fluxo funciona end-to-end no backend, mas as camadas de compliance (FairnessGuard nas perguntas geradas) precisam ser ativadas como step pós-geração.

---

### ETAPA 4: BUSCAR CANDIDATOS (Funil de Talentos)

| Dimensão | Componente | Status | Localização |
|----------|-----------|--------|-------------|
| **Agente** | Ag.2 SourcingAgent | Implementado | `app/domains/sourcing/` |
| **Agente** | Ag.3 TriagemCurricular | Implementado | `app/domains/cv_screening/` |
| **Agente** | Ag.5 AvaliadorWSI | Implementado | `app/domains/cv_screening/` (WSI Evaluator) |
| **Domínio** | `sourcing` + `pipeline` | Implementado | `app/domains/` |
| **Serviços** | SourcingPipelineService, CandidateEnrichmentService, CVScoringService | Implementados | `app/services/` |
| **Tools** | `search_candidates`, `analyze_profile`, `score_candidate`, `enrich_profile` | Registradas | `sourcing_tool_registry.py` |
| **Frontend** | Funil de Talentos (tabela + filtros + sidebar LIA) | Implementado | `src/app/(dashboard)/candidates/` |
| **Busca** | Elasticsearch + PGVector + WRF | PARCIAL | ES e PGVector configurados; WRF Dynamic K precisa integração |
| **Camadas Ativas** | | | |
| ↳ FairnessGuard L1 | Bloquear buscas discriminatórias | ATIVO | Integrado no `MainOrchestrator` |
| ↳ FairnessGuard L2 | Alertar proxy terms na busca | ATIVO | Integrado no `MainOrchestrator` |
| ↳ FairnessGuard L3 | Análise semântica nas respostas do LLM | PRECISA ATIVAR | No `RubricEvaluationService` |
| ↳ PII Masking | Strip PII de candidatos antes do LLM | Ativo | `strip_pii_for_llm_prompt` |
| ↳ LGPD Anonymize | Modo anônimo no Toon | Implementado | `ToonService` `anonymize=True` |
| ↳ Bias Detection | Scoring sem variáveis protegidas | PRECISA VERIFICAR | `_LEARNING_PROTECTED_FIELDS` |
| ↳ Audit | Log de buscas + scores | PRECISA ATIVAR | `audit_service.py` |
| ↳ Fact-Checker | Validar claims nas análises LIA | PRECISA ATIVAR | `fact_checker.py` |

**Gap CRÍTICO:** A busca com Elasticsearch + PGVector existe, mas o WRF (Weighted Rank Fusion) com Dynamic K e LLM Job Classification precisa ser validado end-to-end. A integração com Pearch/Apify depende de API keys de produção. FairnessGuard L3 (semântico) precisa ser ativado explicitamente no fluxo de análise.

---

### ETAPA 5: APROVAR MAPEADOS (Gate 1)

| Dimensão | Componente | Status | Localização |
|----------|-----------|--------|-------------|
| **Agente** | Ag.0 Orchestrator | Implementado | `app/orchestrator/main_orchestrator.py` |
| **Agente** | Ag.7 AnalistaFeedback | Implementado | `app/domains/analytics/` |
| **Agente** | Ag.8 IntegradorATS | Implementado | `app/domains/ats_integration/` |
| **Domínio** | `pipeline` + `kanban` | Implementado | `app/domains/` |
| **Serviços** | KanbanService, PipelineTransitionService | Implementados | `app/services/` |
| **Tools** | `suggest_movements`, `check_rejection_fairness`, `identify_bottlenecks` | Registradas | `kanban_tool_registry.py` |
| **Frontend** | Kanban board + SmartTransitionModal | Implementado | `src/app/(dashboard)/job-kanban/` |
| **Camadas Ativas** | | | |
| ↳ FairnessGuard | `check_rejection_fairness` — valida motivo de rejeição | Registrada como tool | Precisa ser chamada automaticamente |
| ↳ Policy Engine | Autonomy levels + HITL thresholds | Implementado | `policy_engine_service.py` |
| ↳ Escalation | Trigger quando AI confidence baixa | Implementado | `trigger_escalation` |
| ↳ Audit | Log de aprovações/rejeições + overrides humanos | PRECISA ATIVAR | `audit_service.py` |
| ↳ LGPD | Consentimento antes de contato | PRECISA VERIFICAR | Fluxo de consentimento |

**Gap:** O `check_rejection_fairness` existe como tool mas precisa ser chamado automaticamente (não só sob demanda do agente). O Audit de overrides humanos (quando consultor muda decisão do AI) precisa ser ativado.

---

### ETAPA 6: CONTATO VIA EMAIL + FOLLOW-UP

| Dimensão | Componente | Status | Localização |
|----------|-----------|--------|-------------|
| **Agente** | Ag.0 Orchestrator | Implementado | `main_orchestrator.py` |
| **Domínio** | `communication` | Implementado | `app/domains/communication/` |
| **Serviços** | EmailService (Resend/SendGrid), WhatsAppService (Twilio) | Implementados | `email_service.py`, `whatsapp_service.py` |
| **Tools** | `send_email`, `send_whatsapp`, `send_bulk_email`, `send_feedback` | Registradas | `communication_tools.py` |
| **Frontend** | Templates de email | Implementado | `src/components/` |
| **Camadas Ativas** | | | |
| ↳ Rate Limiting | Limite de envio por empresa/dia | Implementado | `RateLimitRule` |
| ↳ PII Masking | Emails não logam dados pessoais | Ativo | `PIIMaskingFilter` |
| ↳ LGPD | Opt-out link no email | PRECISA IMPLEMENTAR | Template precisa ter unsubscribe |
| ↳ Audit | Log de envios + opens + clicks | PRECISA ATIVAR | `audit_service.py` |
| ↳ Follow-up 7 dias | Automação de re-envio | PRECISA IMPLEMENTAR | Scheduler/cron job |

**Gap:** O follow-up automático de 7 dias precisa de um scheduler (celery/cron/background task) que NÃO existe no código atual. O template de email precisa de link de opt-out (LGPD). O tracking de opens/clicks precisa ser configurado no provedor (Resend/SendGrid).

---

### ETAPA 7: TRIAGEM WSI (Chat Web / WhatsApp)

| Dimensão | Componente | Status | Localização |
|----------|-----------|--------|-------------|
| **Agente** | Ag.0 Orchestrator | Implementado | `main_orchestrator.py` |
| **Agente** | Ag.4 EntrevistadorWSI | Implementado | `app/domains/cv_screening/` |
| **Agente** | Ag.5 AvaliadorWSI | Implementado | `app/domains/cv_screening/` |
| **Domínio** | `cv_screening` + `communication` | Implementado | `app/domains/` |
| **Serviços** | WSIService, WhatsAppService, VoiceService | Implementados | `app/services/` |
| **Tools** | `generate_screening_questions`, `analyze_response`, `calculate_wsi` | Registradas | WSI tools |
| **Frontend Chat Web** | Chat page para candidato | PRECISA IMPLEMENTAR | Página pública de triagem |
| **Camadas Ativas** | | | |
| ↳ FairnessGuard L1-L3 | Perguntas e análises sem viés | PRECISA ATIVAR | Em cada step da triagem |
| ↳ PII Masking | Strip PII nas respostas antes do LLM | Ativo | `strip_pii_for_llm_prompt` |
| ↳ Fact-Checker | Validar scores e claims | PRECISA ATIVAR | Pós-cálculo WSI |
| ↳ Audit | Log completo da triagem | PRECISA ATIVAR | Cada pergunta/resposta |
| ↳ LGPD | Consentimento antes da triagem | PRECISA IMPLEMENTAR | Tela de aceite |
| ↳ Timeout/Abandono | Lembretes 48h + 48h | PRECISA IMPLEMENTAR | Scheduler |

**Gap CRÍTICO:** O chat web público para candidato (onde ele acessa pelo link do email) NÃO existe como página no frontend. Existe a infraestrutura de chat no backend, mas a página pública de triagem precisa ser construída. Os timeouts de abandono (48h+48h) precisam de scheduler.

---

### ETAPAS 8-9: APROVAR TRIADOS (Gate 2) + AGENDAR ENTREVISTA + FEEDBACK

| Dimensão | Componente | Status | Localização |
|----------|-----------|--------|-------------|
| **Agente** | Ag.6 SchedulingAgent | Implementado | `app/domains/interview_scheduling/` |
| **Agente** | Ag.7 AnalistaFeedback | Implementado | `app/domains/analytics/` |
| **Domínio** | `scheduling` + `analytics` + `communication` | Implementados | `app/domains/` |
| **Serviços** | SchedulingService (ICS + Teams), EmailService, WhatsAppService | Implementados | `app/services/` |
| **Tools** | `schedule_interview`, `send_feedback` | Registradas | `communication_tools.py` |
| **Camadas Ativas** | | | |
| ↳ FairnessGuard | Feedback sem viés | PRECISA ATIVAR | Análise do texto de feedback |
| ↳ Audit | Log de aprovação/rejeição Gate 2 | PRECISA ATIVAR | `audit_service.py` |
| ↳ LGPD | Dados compartilhados com calendário | PRECISA VERIFICAR | Minimização de dados |

**Gap:** O agendamento com Microsoft Teams está implementado mas depende de configuração de tenant (Graph API). O ICS funciona standalone.

---

## 3. MAPA DE CAMADAS DE COMPLIANCE POR AGENTE/DOMÍNIO

| Agente | Domínio | FairnessGuard | PII Masking | LGPD | Fact-Check | Audit | Policy Engine | Bias Detection |
|--------|---------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Ag.0 Orchestrator | orchestration | L1-L2 ativo | Ativo | — | — | Parcial | Ativo | Via FG |
| Ag.2 SourcingAgent | sourcing | L1-L2 ativo | Ativo | Anonymize | A ativar | A ativar | — | A ativar L3 |
| Ag.3 TriagemCurricular | cv_screening | A ativar | Ativo | A verificar | A ativar | A ativar | — | A ativar |
| Ag.4 EntrevistadorWSI | cv_screening | A ativar | Ativo | A implementar | A ativar | A ativar | — | A ativar |
| Ag.5 AvaliadorWSI | cv_screening | A ativar L3 | Ativo | A verificar | A ativar | A ativar | — | A ativar |
| Ag.6 SchedulingAgent | scheduling | — | Ativo | A verificar | — | A ativar | — | — |
| Ag.7 AnalistaFeedback | analytics | A ativar | Ativo | — | A ativar | A ativar | — | A ativar |
| Ag.8 IntegradorATS | ats_integration | — | Ativo | A verificar | — | A ativar | — | — |

**Legenda:** Ativo = funcionando em produção | A ativar = código existe, precisa ser ligado | A implementar = código não existe | A verificar = precisa checagem

---

## 4. O QUE FALTA NO ROADMAP (GAPS IDENTIFICADOS)

### 4.1 Gaps Estruturais (faltam no fluxo descrito)

| # | Gap | Impacto | Prioridade |
|---|-----|---------|-----------|
| G1 | **Scheduler/Background Jobs** — Follow-up 7 dias, timeout triagem 48h+48h, lembretes | Sem isso, etapas 6B e 7A não funcionam | BLOQUEANTE |
| G2 | **Chat Web Público (Candidato)** — Página onde candidato faz triagem WSI | Sem isso, etapa 7 inteira não funciona | BLOQUEANTE |
| G3 | **Webhook de Email** — Tracking de opens/clicks para follow-up inteligente | Follow-up fica "cego" sem saber se candidato leu | ALTO |
| G4 | **Consentimento LGPD (Tela de Aceite)** — Antes da triagem WSI | Obrigatório legalmente | BLOQUEANTE |
| G5 | **Unsubscribe Link** — Nos templates de email | LGPD/CAN-SPAM compliance | ALTO |
| G6 | **Notificações (Teams/Email/Bell)** — Sistema de alertas ao consultor | Mencionado no roadmap mas não implementado como sistema | ALTO |
| G7 | **Configuração de Infra Externa** — API keys: Twilio, Resend/SendGrid, Apify, ATS | Sem credenciais, tudo roda em "dev mode" | BLOQUEANTE para Alpha 1 |

### 4.2 Gaps de Camadas de Compliance

| # | Gap | O que existe | O que falta |
|---|-----|-------------|-------------|
| C1 | **FairnessGuard ativo em todos os pontos** | L1-L2 no Orchestrator | Ativar em: save JD, geração WSI, análise de resposta, feedback, scoring |
| C2 | **FairnessGuard L3 (Semântico) em produção** | Código existe no RubricEvaluationService | Ativar como step obrigatório pós-LLM em todos os domínios |
| C3 | **Audit Trail completo** | AuditService existe | Ativar em: login, edição vaga, geração roteiro, busca, aprovação, contato, triagem, feedback |
| C4 | **LGPD Consent Flow** | Endpoints de consentimento existem | Falta fluxo frontend + enforcement antes de processar candidato |
| C5 | **Fact-Checker em todos os outputs** | Código existe | Ativar como middleware pós-resposta em todos os agentes |
| C6 | **Bias Audit Report** | FairnessGuard coleta dados | Falta dashboard/relatório periódico de Four-Fifths Rule |
| C7 | **EU AI Act Compliance** | Mencionado nos docs | Falta classificação de risco por agente e disclosure obrigatório |

---

## 5. MAPA DE PRIORIDADES DE CONSTRUÇÃO

### Fase 0: INFRAESTRUTURA (Semana 1-2) — Sem isso nada funciona

| # | Item | Tipo | Esforço |
|---|------|------|---------|
| P0.1 | Configurar credenciais de produção (Twilio, Resend, Apify, ATS) | Config | 1-2 dias |
| P0.2 | Implementar Scheduler/Background Jobs (Celery ou similar) | Infra | 3-5 dias |
| P0.3 | Configurar Elasticsearch + PGVector em produção | Infra | 2-3 dias |
| P0.4 | Ativar Audit Trail em todos os endpoints | Backend | 2-3 dias |

### Fase 1: FLUXO CORE (Semana 2-4) — Caminho feliz funcional

| # | Item | Agentes Envolvidos | Camadas a Ativar | Esforço |
|---|------|-------------------|------------------|---------|
| P1.1 | Login funcional + rate limiting | — | Rate Limiting, Audit | 1 dia |
| P1.2 | Import/Edição de Vaga do ATS | Ag.8 | FairnessGuard L1-L2, Audit | 2-3 dias |
| P1.3 | Configurar Roteiro WSI (JD → Perguntas) | Ag.4 | FairnessGuard L1-L2, Fact-Checker | 2-3 dias |
| P1.4 | Busca de Candidatos (ES+PGVector+WRF) | Ag.2, Ag.3 | FairnessGuard L1-L3, PII, Audit | 5-7 dias |
| P1.5 | Aprovação no Kanban (Gate 1) | Ag.0, Ag.7, Ag.8 | check_rejection_fairness, Policy Engine, Audit | 3-4 dias |
| P1.6 | Envio de Email de Contato | Ag.0 | Rate Limiting, LGPD (opt-out), Audit | 2-3 dias |

### Fase 2: TRIAGEM + AUTOMAÇÃO (Semana 4-6) — Diferencial do produto

| # | Item | Agentes Envolvidos | Camadas a Ativar | Esforço |
|---|------|-------------------|------------------|---------|
| P2.1 | Chat Web Público para Triagem WSI | Ag.0, Ag.4, Ag.5 | FairnessGuard L1-L3, LGPD Consent, PII, Audit | 7-10 dias |
| P2.2 | Follow-up Automático 7 dias | Ag.0 | Rate Limiting, Audit | 3-4 dias |
| P2.3 | Timeout + Abandono de Triagem | Ag.4 | Scheduler, Audit | 2-3 dias |
| P2.4 | Score WSI + Parecer Textual | Ag.5 | Fact-Checker, Bias Detection, Audit | 3-5 dias |

### Fase 3: GATES + SCHEDULING (Semana 6-8) — Fechamento do loop

| # | Item | Agentes Envolvidos | Camadas a Ativar | Esforço |
|---|------|-------------------|------------------|---------|
| P3.1 | Gate 2 (Aprovar/Reprovar Triados) | Ag.7, Ag.8 | FairnessGuard, Policy Engine, Audit | 3-4 dias |
| P3.2 | Agendamento de Entrevista | Ag.6 | LGPD (dados calendário), Audit | 3-5 dias |
| P3.3 | Feedback Automático (Reprovados) | Ag.7 | FairnessGuard (texto feedback), Audit | 2-3 dias |
| P3.4 | Notificações Teams/Email/Bell | Todos | Audit | 3-5 dias |

### Fase 4: COMPLIANCE PROFUNDO (Semana 8-10) — Produção real

| # | Item | Tipo | Esforço |
|---|------|------|---------|
| P4.1 | Bias Audit Dashboard (Four-Fifths Rule) | Frontend + Backend | 5-7 dias |
| P4.2 | EU AI Act Risk Classification por agente | Docs + Backend | 3-5 dias |
| P4.3 | LGPD DSR (Data Subject Requests) — export/delete | Backend | 3-5 dias |
| P4.4 | Presidio NER Layer 4 ativado em produção | Backend | 2-3 dias |
| P4.5 | SOX Audit Export (para auditoria externa) | Backend | 2-3 dias |

---

## 6. GRAFO DE DEPENDÊNCIAS DOS AGENTES

```
                    ┌──────────────┐
                    │  Ag.0        │
                    │ Orchestrator │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼────┐ ┌────▼─────┐ ┌────▼─────┐
        │  Ag.2    │ │  Ag.4   │ │  Ag.8   │
        │ Sourcing │ │Entrev.  │ │ ATS Int.│
        └─────┬────┘ │  WSI    │ └────┬────┘
              │      └────┬────┘      │
              │           │           │
        ┌─────▼────┐ ┌────▼─────┐    │
        │  Ag.3    │ │  Ag.5   │    │
        │ Triagem  │ │Avaliador│    │
        │Curricular│ │  WSI    │    │
        └──────────┘ └────┬────┘    │
                          │         │
                    ┌─────▼────┐    │
                    │  Ag.7    │◄───┘
                    │Analista  │
                    │Feedback  │
                    └─────┬────┘
                          │
                    ┌─────▼────┐
                    │  Ag.6    │
                    │Scheduling│
                    └──────────┘
```

### Camadas transversais (ativas em TODOS os nós):

```
┌──────────────────────────────────────────────────────────┐
│                    CAMADAS TRANSVERSAIS                   │
├──────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ FairnessGuard│  │ PII Masking │  │ Fact-Checker │     │
│  │  (L1-L2-L3) │  │ (4 layers)  │  │ (Numeric +  │     │
│  │             │  │             │  │  Claims)    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ Audit Trail │  │Policy Engine│  │ LGPD/Consent│     │
│  │ (SOX/EU AI) │  │(Escalation) │  │ (DSR/Anon)  │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│  ┌─────────────┐  ┌─────────────┐                       │
│  │Rate Limiting│  │Bias Audit   │                       │
│  │(Sliding Win)│  │(4/5 Rule)   │                       │
│  └─────────────┘  └─────────────┘                       │
└──────────────────────────────────────────────────────────┘
```

---

## 7. RESPOSTA ÀS PERGUNTAS DO USUÁRIO

### "Isso faz sentido?"
**Sim, o fluxo Alpha 1 faz sentido e está bem estruturado.** A sequência Login → Editar Vaga → Roteiro WSI → Buscar → Aprovar → Contato → Triagem → Gate 2 → Agendar/Feedback é o caminho natural de um processo de recrutamento assistido por IA. O backend suporta esse fluxo.

### "Falta informação?"
**Sim, faltam 7 gaps estruturais e 7 gaps de compliance** detalhados nas seções 4.1 e 4.2. Os mais críticos são:
1. **Scheduler** (sem ele, follow-up e timeouts não funcionam)
2. **Chat Web Público** (sem ele, a triagem WSI não acontece)
3. **Consentimento LGPD** (obrigatório legalmente)
4. **Credenciais de produção** (sem elas, tudo é "dev mode")

### "Faz sentido adicionar camadas de compliance por agente?"
**Absolutamente.** A tabela da seção 3 mostra que a maioria das camadas está "código existe, precisa ser ligada". O mapa de prioridades (seção 5) já incorpora quais camadas precisam ser ativadas em cada fase. A prioridade é:
1. **FairnessGuard em todos os pontos** (já tem código, só precisa de wiring)
2. **Audit Trail completo** (já tem serviço, precisa ativar em cada endpoint)
3. **LGPD Consent Flow** (precisa de implementação frontend + enforcement)
4. **Fact-Checker como middleware** (já tem código, precisa virar middleware)
5. **Bias Audit Dashboard** (precisa ser construído)

---

## 8. ARQUIVOS-CHAVE DO CÓDIGO REFERENCIADOS

| Arquivo | Responsabilidade |
|---------|-----------------|
| `lia-agent-system/app/orchestrator/main_orchestrator.py` | Orquestração central (3 fases) |
| `lia-agent-system/app/orchestrator/intent_router.py` | Roteamento de intents por cascata de modelos |
| `lia-agent-system/libs/agents-core/lia_agents_core/react_agent_registry.py` | Registry de agentes ReAct |
| `lia-agent-system/libs/agents-core/lia_agents_core/langgraph_base.py` | Base LangGraph com checkpointer |
| `lia-agent-system/libs/agents-core/lia_agents_core/langgraph_react_base.py` | Base ReAct LangGraph |
| `lia-agent-system/app/shared/compliance/fairness_guard.py` | FairnessGuard (3 camadas, ~350 patterns) |
| `lia-agent-system/app/shared/pii_masking.py` | PII Masking (4 camadas, Presidio opt-in) |
| `lia-agent-system/app/shared/compliance/audit_service.py` | Audit Trail (SOX-compliant) |
| `lia-agent-system/app/shared/compliance/fact_checker.py` | Fact-Checker (numeric claims) |
| `lia-agent-system/app/services/policy_engine_service.py` | Policy Engine + Rate Limiting + Escalation |
| `lia-agent-system/app/domains/communication/services/email_service.py` | Email (Resend/SendGrid) |
| `lia-agent-system/app/domains/communication/services/whatsapp_service.py` | WhatsApp (Twilio) |
| `lia-agent-system/app/domains/cv_screening/services/wsi_service.py` | WSI (CBI/Bloom/Dreyfus/Big Five) |
| `lia-agent-system/app/domains/ats_integration/` | ATS (Gupy/Pandapé/Merge/StackOne) |
| `lia-agent-system/app/domains/interview_scheduling/services/scheduling_service.py` | Scheduling (ICS + Teams) |
