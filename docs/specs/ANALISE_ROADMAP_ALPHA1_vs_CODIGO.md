# Análise Profunda: Roadmap Alpha 1 vs. Código Existente

**Data:** 30/03/2026  
**Versão:** 3.0 — Diagrama Vertical com Todas as Dimensões Laterais  
**Escopo:** Cruzamento do Fluxo Alpha 1 (v2) com a implementação real no Replit  
**Objetivo:** Mapear TODAS as dimensões — agentes, domínios, serviços, tools, 6 camadas de compliance, 11 camadas de inteligência — por etapa do fluxo Alpha 1

---

## 0. DIAGRAMA DE JORNADA VISUAL — FLUXO ALPHA 1 (VERTICAL)

### Legenda de Status

```
● = ATIVO (funcionando)    ◐ = DISPONÍVEL (código existe, precisa ativar/integrar)
○ = A IMPLEMENTAR (gap)    ⚠ = GAP BLOQUEANTE    · = N/A nesta etapa
```

### Diagrama Completo — Leitura: Etapa ↓ | Envolvidos → | Compliance → | Inteligência → | Comunicação →

```
╔═══════════════════════╦═══════════════════════════════╦══════════════════════════════════╦══════════════════════════════════════════╦═════════════════════════════╗
║       ETAPA           ║     ENVOLVIDOS                ║     COMPLIANCE (6 camadas)       ║     INTELIGÊNCIA (11 camadas)            ║     COMUNICAÇÃO             ║
╠═══════════════════════╬═══════════════════════════════╬══════════════════════════════════╬══════════════════════════════════════════╬═════════════════════════════╣
║                       ║ Agentes:  —                   ║ FG L1: ·   FG L2: ·   FG L3: ·  ║ Learning Loop: ·    A/B Testing: ·       ║ Email: ·                    ║
║  1. LOGIN             ║ Domínio:  auth                ║ PII:   ●   Fact-Check: ·         ║ Routing Adapt: ·    Template Lrn: ·      ║ WhatsApp: ·                 ║
║     Autenticação      ║ Serviço:  AuthService         ║ Audit: ◐   Policy Eng: ◐         ║ Calibration: ·      Score Norm: ·        ║ Chat Web: ·                 ║
║     JWT + WorkOS SSO  ║ LangGraph: Não                ║ LGPD:  ◐   Rate Limit: ◐         ║ Predictive: ·       Model Drift: ·       ║ Teams: ·                    ║
║                       ║ Metodologia: —                ║                                  ║ Conv Memory: ·      Semantic: ·          ║ Telefone/VoIP: ·            ║
║                       ║                               ║                                  ║ Voice Analysis: ·   Embedding: ·        ║ Feedback Auto: ·            ║
║                       ║                               ║                                  ║                                        ║ Notificação: ·              ║
║  GAP: Rate limiting de login + Audit trail de autenticação precisam ser ativados                                                                               ║
╠═══════════════════════╬═══════════════════════════════╬══════════════════════════════════╬══════════════════════════════════════════╬═════════════════════════════╣
║          │            ║                               ║                                  ║                                        ║                             ║
║          ▼            ║                               ║                                  ║                                        ║                             ║
╠═══════════════════════╬═══════════════════════════════╬══════════════════════════════════╬══════════════════════════════════════════╬═════════════════════════════╣
║                       ║ Agentes:  Ag.8 IntegradorATS  ║ FG L1: ◐   FG L2: ◐   FG L3: ·  ║ Learning Loop: ●    A/B Testing: ◐       ║ Email: ·                    ║
║  2. EDITAR VAGA       ║ Domínio:  ats_integration,    ║ PII:   ●   Fact-Check: ·         ║ Routing Adapt: ·    Template Lrn: ●      ║ WhatsApp: ·                 ║
║     Importar do ATS   ║           job_management      ║ Audit: ◐   Policy Eng: ·         ║ Calibration: ·      Score Norm: ·        ║ Chat Web: ·                 ║
║     Editar wizard     ║ Serviço:  ATSSyncService,     ║ LGPD:  ◐   Rate Limit: ·         ║ Predictive: ◐      Model Drift: ·       ║ Teams: ·                    ║
║                       ║           GupyClient,         ║                                  ║ Conv Memory: ●      Semantic: ◐         ║ Telefone/VoIP: ·            ║
║                       ║           PandapeClient       ║                                  ║ Voice Analysis: ·   Embedding: ·        ║ Feedback Auto: ·            ║
║                       ║ LangGraph: Sim (Ag.8)         ║                                  ║                                        ║ Notificação: ·              ║
║                       ║ Metodologia: —                ║                                  ║                                        ║                             ║
║                       ║ Tools: sync_candidate_to_ats, ║                                  ║                                        ║                             ║
║                       ║   fetch_candidate_from_ats,   ║                                  ║                                        ║                             ║
║                       ║   validate_ats_fields         ║                                  ║                                        ║                             ║
║  GAP: ATS real depende de credenciais (API keys Gupy/Pandapé). FG precisa virar middleware no save JD                                                          ║
╠═══════════════════════╬═══════════════════════════════╬══════════════════════════════════╬══════════════════════════════════════════╬═════════════════════════════╣
║          │            ║                               ║                                  ║                                        ║                             ║
║          ▼            ║                               ║                                  ║                                        ║                             ║
╠═══════════════════════╬═══════════════════════════════╬══════════════════════════════════╬══════════════════════════════════════════╬═════════════════════════════╣
║                       ║ Agentes:  Ag.4 Entrev.WSI     ║ FG L1: ◐   FG L2: ◐   FG L3: ·  ║ Learning Loop: ●    A/B Testing: ◐       ║ Email: ·                    ║
║  3. ROTEIRO WSI       ║ Domínio:  cv_screening,       ║ PII:   ●   Fact-Check: ◐         ║ Routing Adapt: ·    Template Lrn: ·      ║ WhatsApp: ·                 ║
║     Configurar        ║           wizard              ║ Audit: ◐   Policy Eng: ·         ║ Calibration: ·      Score Norm: ·        ║ Chat Web: ·                 ║
║     perguntas de      ║ Serviço:  WSIService,         ║ LGPD:  ·   Rate Limit: ·         ║ Predictive: ·       Model Drift: ·       ║ Teams: ·                    ║
║     triagem           ║           JDGeneratorService  ║                                  ║ Conv Memory: ●      Semantic: ◐         ║ Telefone/VoIP: ·            ║
║     (CBI/Bloom/       ║ LangGraph: Sim (Ag.4)         ║                                  ║ Voice Analysis: ·   Embedding: ·        ║ Feedback Auto: ·            ║
║      Dreyfus/Big5)    ║ Metodologia: WSI              ║                                  ║                                        ║ Notificação: ·              ║
║                       ║ Tools: generate_screening_    ║                                  ║                                        ║                             ║
║                       ║   questions, analyze_jd_and_  ║                                  ║                                        ║                             ║
║                       ║   suggest_competencies        ║                                  ║                                        ║                             ║
║  GAP: FG e Fact-Checker precisam ser ativados como step pós-geração nas perguntas WSI                                                                          ║
╠═══════════════════════╬═══════════════════════════════╬══════════════════════════════════╬══════════════════════════════════════════╬═════════════════════════════╣
║          │            ║                               ║                                  ║                                        ║                             ║
║          ▼            ║                               ║                                  ║                                        ║                             ║
╠═══════════════════════╬═══════════════════════════════╬══════════════════════════════════╬══════════════════════════════════════════╬═════════════════════════════╣
║                       ║ Agentes:  Ag.2 Sourcing,      ║ FG L1: ●   FG L2: ●   FG L3: ◐  ║ Learning Loop: ●    A/B Testing: ◐       ║ Email: ·                    ║
║  4. BUSCAR            ║           Ag.3 TriagemCurr,   ║ PII:   ●   Fact-Check: ◐         ║ Routing Adapt: ●    Template Lrn: ·      ║ WhatsApp: ·                 ║
║     CANDIDATOS        ║           Ag.5 AvaliadorWSI   ║ Audit: ◐   Policy Eng: ·         ║ Calibration: ●      Score Norm: ●        ║ Chat Web: ·                 ║
║     Funil de          ║ Domínio:  sourcing, pipeline  ║ LGPD:  ●   Rate Limit: ·         ║ Predictive: ◐      Model Drift: ●       ║ Teams: ·                    ║
║     Talentos          ║ Serviço:  SourcingPipeline,   ║ Bias Det: ◐                      ║ Conv Memory: ●      Semantic: ●          ║ Telefone/VoIP: ·            ║
║     SmartSearch       ║           CandidateEnrich,    ║   (LGPD: Anonymize=True no Toon) ║ Voice Analysis: ·   Embedding: ◐        ║ Feedback Auto: ·            ║
║     WRF + ES +        ║           CVScoringService    ║                                  ║                                        ║ Notificação: ·              ║
║     PGVector          ║ LangGraph: Sim (Ag.2,3,5)     ║                                  ║                                        ║                             ║
║                       ║ Metodologia: WSI (scoring)    ║                                  ║                                        ║                             ║
║                       ║ Tools: search_candidates,     ║                                  ║                                        ║                             ║
║                       ║   analyze_profile, score_     ║                                  ║                                        ║                             ║
║                       ║   candidate, enrich_profile   ║                                  ║                                        ║                             ║
║  GAP CRÍTICO: WRF Dynamic K + LLM Job Classification precisa validação e2e. FG L3 depende de sector rules. Apify API keys.                                    ║
╠═══════════════════════╬═══════════════════════════════╬══════════════════════════════════╬══════════════════════════════════════════╬═════════════════════════════╣
║          │            ║                               ║                                  ║                                        ║                             ║
║          ▼            ║                               ║                                  ║                                        ║                             ║
╠═══════════════════════╬═══════════════════════════════╬══════════════════════════════════╬══════════════════════════════════════════╬═════════════════════════════╣
║                       ║ Agentes:  Ag.0 Orchestrator,  ║ FG L1: ●   FG L2: ●   FG L3: ·  ║ Learning Loop: ●    A/B Testing: ·       ║ Email: ·                    ║
║  5. APROVAR           ║           Ag.7 Feedback,      ║ PII:   ●   Fact-Check: ·         ║ Routing Adapt: ●    Template Lrn: ·      ║ WhatsApp: ·                 ║
║     MAPEADOS          ║           Ag.8 IntegradorATS  ║ Audit: ◐   Policy Eng: ●         ║ Calibration: ●      Score Norm: ·        ║ Chat Web: ·                 ║
║     (Gate 1)          ║ Domínio:  pipeline, kanban    ║ LGPD:  ◐   Rate Limit: ·         ║ Predictive: ·       Model Drift: ●       ║ Teams: ·                    ║
║     Decisão humana    ║ Serviço:  KanbanService,      ║ Escalation: ●                    ║ Conv Memory: ●      Semantic: ·          ║ Telefone/VoIP: ·            ║
║     assistida por IA  ║           PipelineTransition  ║   (trigger AI conf < threshold)  ║ Voice Analysis: ·   Embedding: ·        ║ Feedback Auto: ·            ║
║                       ║ LangGraph: Sim (Ag.0,7,8)     ║                                  ║                                        ║ Notificação: ○              ║
║                       ║ Metodologia: HITL, BARS       ║                                  ║                                        ║                             ║
║                       ║ Tools: suggest_movements,     ║                                  ║                                        ║                             ║
║                       ║   check_rejection_fairness,   ║                                  ║                                        ║                             ║
║                       ║   identify_bottlenecks        ║                                  ║                                        ║                             ║
║  GAP: check_rejection_fairness precisa ser automática (não sob demanda). Audit de overrides humanos.                                                           ║
╠═══════════════════════╬═══════════════════════════════╬══════════════════════════════════╬══════════════════════════════════════════╬═════════════════════════════╣
║          │            ║                               ║                                  ║                                        ║                             ║
║          ▼            ║                               ║                                  ║                                        ║                             ║
╠═══════════════════════╬═══════════════════════════════╬══════════════════════════════════╬══════════════════════════════════════════╬═════════════════════════════╣
║                       ║ Agentes:  Ag.0 Orchestrator   ║ FG L1: ·   FG L2: ·   FG L3: ·  ║ Learning Loop: ·    A/B Testing: ◐       ║ Email: ● (Resend/SendGrid)  ║
║  6. CONTATO           ║ Domínio:  communication       ║ PII:   ●   Fact-Check: ·         ║ Routing Adapt: ·    Template Lrn: ◐      ║ WhatsApp: ● (Twilio)        ║
║     EMAIL +           ║ Serviço:  EmailService,       ║ Audit: ◐   Policy Eng: ·         ║ Calibration: ·      Score Norm: ·        ║ Chat Web: ·                 ║
║     FOLLOW-UP         ║           WhatsAppService     ║ LGPD:  ○   Rate Limit: ●         ║ Predictive: ·       Model Drift: ·       ║ Teams: ○                    ║
║     Primeiro contato  ║ LangGraph: Sim (Ag.0)         ║   (LGPD: falta opt-out link)     ║ Conv Memory: ●      Semantic: ·          ║ Telefone/VoIP: ·            ║
║     com candidatos    ║ Metodologia: —                ║                                  ║ Voice Analysis: ·   Embedding: ·        ║ Feedback Auto: ·            ║
║     aprovados         ║ Tools: send_email,            ║                                  ║                                        ║ Notificação: ○              ║
║                       ║   send_whatsapp,              ║                                  ║                                        ║                             ║
║                       ║   send_bulk_email,            ║                                  ║                                        ║                             ║
║                       ║   send_feedback               ║                                  ║                                        ║                             ║
║  GAP ⚠: Follow-up 7d precisa SCHEDULER (não existe). Opt-out link LGPD. Webhook de tracking opens/clicks.                                                     ║
╠═══════════════════════╬═══════════════════════════════╬══════════════════════════════════╬══════════════════════════════════════════╬═════════════════════════════╣
║          │            ║                               ║                                  ║                                        ║                             ║
║          ▼            ║                               ║                                  ║                                        ║                             ║
╠═══════════════════════╬═══════════════════════════════╬══════════════════════════════════╬══════════════════════════════════════════╬═════════════════════════════╣
║                       ║ Agentes:  Ag.0 Orchestrator,  ║ FG L1: ◐   FG L2: ◐   FG L3: ◐  ║ Learning Loop: ●    A/B Testing: ◐       ║ Email: ◐ (notificar result) ║
║  7. TRIAGEM WSI       ║           Ag.4 Entrev.WSI,    ║ PII:   ●   Fact-Check: ◐         ║ Routing Adapt: ·    Template Lrn: ·      ║ WhatsApp: ● (Twilio)        ║
║     Chat/WhatsApp     ║           Ag.5 AvaliadorWSI   ║ Audit: ◐   Policy Eng: ●         ║ Calibration: ●      Score Norm: ●        ║ Chat Web: ⚠ NÃO EXISTE     ║
║     Candidato         ║ Domínio:  cv_screening,       ║ LGPD:  ○   Rate Limit: ·         ║ Predictive: ·       Model Drift: ●       ║ Teams: ·                    ║
║     responde          ║           communication       ║ Timeout: ○                       ║ Conv Memory: ●      Semantic: ·          ║ Telefone/VoIP: ◐ (VoiceS)  ║
║     perguntas WSI     ║ Serviço:  WSIService,         ║   (LGPD: falta tela de aceite)   ║ Voice Analysis: ●   Embedding: ·        ║ Feedback Auto: ·            ║
║     (CBI/Bloom/       ║           WhatsAppService,    ║   (Timeout: falta scheduler      ║                                        ║ Notificação: ○              ║
║      Dreyfus/Big5)    ║           VoiceService        ║    48h+48h lembretes)            ║                                        ║                             ║
║                       ║ LangGraph: Sim (Ag.0,4,5)     ║                                  ║                                        ║                             ║
║                       ║ Metodologia: WSI completa     ║                                  ║                                        ║                             ║
║                       ║ Tools: generate_screening_    ║                                  ║                                        ║                             ║
║                       ║   questions, analyze_response,║                                  ║                                        ║                             ║
║                       ║   calculate_wsi               ║                                  ║                                        ║                             ║
║  GAP CRÍTICO ⚠: Chat web público NÃO EXISTE. Timeouts 48h+48h precisam scheduler. Consentimento LGPD precisa tela frontend.                                   ║
╠═══════════════════════╬═══════════════════════════════╬══════════════════════════════════╬══════════════════════════════════════════╬═════════════════════════════╣
║          │            ║                               ║                                  ║                                        ║                             ║
║          ▼            ║                               ║                                  ║                                        ║                             ║
╠═══════════════════════╬═══════════════════════════════╬══════════════════════════════════╬══════════════════════════════════════════╬═════════════════════════════╣
║                       ║ Agentes:  Ag.7 Feedback,      ║ FG L1: ●   FG L2: ●   FG L3: ·  ║ Learning Loop: ●    A/B Testing: ·       ║ Email: ·                    ║
║  8. APROVAR           ║           Ag.8 IntegradorATS  ║ PII:   ●   Fact-Check: ·         ║ Routing Adapt: ●    Template Lrn: ·      ║ WhatsApp: ·                 ║
║     TRIADOS           ║ Domínio:  pipeline, kanban,   ║ Audit: ◐   Policy Eng: ●         ║ Calibration: ●      Score Norm: ·        ║ Chat Web: ·                 ║
║     (Gate 2)          ║           analytics           ║ LGPD:  ◐   Rate Limit: ·         ║ Predictive: ·       Model Drift: ●       ║ Teams: ·                    ║
║     Decisão humana    ║ Serviço:  KanbanService,      ║                                  ║ Conv Memory: ·      Semantic: ·          ║ Telefone/VoIP: ·            ║
║     pós-triagem WSI   ║           PipelineTransition  ║                                  ║ Voice Analysis: ·   Embedding: ·        ║ Feedback Auto: ◐            ║
║                       ║ LangGraph: Sim (Ag.7,8)       ║                                  ║                                        ║ Notificação: ○              ║
║                       ║ Metodologia: HITL, BARS       ║                                  ║                                        ║                             ║
║                       ║ Tools: suggest_movements,     ║                                  ║                                        ║                             ║
║                       ║   check_rejection_fairness    ║                                  ║                                        ║                             ║
║  GAP: Mesmo que Gate 1 — check_rejection_fairness precisa ser automática. Feedback automático para reprovados.                                                 ║
╠═══════════════════════╬═══════════════════════════════╬══════════════════════════════════╬══════════════════════════════════════════╬═════════════════════════════╣
║          │            ║                               ║                                  ║                                        ║                             ║
║          ▼            ║                               ║                                  ║                                        ║                             ║
╠═══════════════════════╬═══════════════════════════════╬══════════════════════════════════╬══════════════════════════════════════════╬═════════════════════════════╣
║                       ║ Agentes:  Ag.6 Scheduling,    ║ FG L1: ◐   FG L2: ◐   FG L3: ·  ║ Learning Loop: ◐    A/B Testing: ◐       ║ Email: ● (convite + ICS)    ║
║  9. AGENDAR           ║           Ag.7 Feedback       ║ PII:   ●   Fact-Check: ·         ║ Routing Adapt: ·    Template Lrn: ◐      ║ WhatsApp: ● (lembrete)      ║
║     ENTREVISTA +      ║ Domínio:  scheduling,         ║ Audit: ◐   Policy Eng: ·         ║ Calibration: ·      Score Norm: ·        ║ Chat Web: ·                 ║
║     FEEDBACK          ║           analytics,          ║ LGPD:  ◐   Rate Limit: ·         ║ Predictive: ·       Model Drift: ·       ║ Teams: ◐ (Graph API)        ║
║     Agendar c/ gestor ║           communication       ║   (LGPD: minimizar dados no ICS) ║ Conv Memory: ·      Semantic: ·          ║ Telefone/VoIP: ·            ║
║     + feedback auto   ║ Serviço:  SchedulingService,  ║                                  ║ Voice Analysis: ·   Embedding: ◐        ║ Feedback Auto: ◐            ║
║     p/ reprovados     ║           EmailService,       ║                                  ║ Long-Term Memory: ◐                     ║ Notificação: ○              ║
║                       ║           WhatsAppService     ║                                  ║                                        ║                             ║
║                       ║ LangGraph: Sim (Ag.6,7)       ║                                  ║                                        ║                             ║
║                       ║ Metodologia: —                ║                                  ║                                        ║                             ║
║                       ║ Tools: schedule_interview,    ║                                  ║                                        ║                             ║
║                       ║   send_feedback               ║                                  ║                                        ║                             ║
║  GAP: Teams depende de configuração Graph API (tenant). ICS funciona standalone. Feedback auto precisa integração.                                              ║
╚═══════════════════════╩═══════════════════════════════╩══════════════════════════════════╩══════════════════════════════════════════╩═════════════════════════════╝
```

### Resumo Visual de Conexões por Coluna

```
COMPLIANCE — Quem precisa do quê:
┌────────────────────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
│                    │ E1 │ E2 │ E3 │ E4 │ E5 │ E6 │ E7 │ E8 │ E9 │
├────────────────────┼────┼────┼────┼────┼────┼────┼────┼────┼────┤
│ FairnessGuard L1   │ ·  │ ◐  │ ◐  │ ●  │ ●  │ ·  │ ◐  │ ●  │ ◐  │
│ FairnessGuard L2   │ ·  │ ◐  │ ◐  │ ●  │ ●  │ ·  │ ◐  │ ●  │ ◐  │
│ FairnessGuard L3   │ ·  │ ·  │ ·  │ ◐  │ ·  │ ·  │ ◐  │ ·  │ ·  │
│ PII Masking        │ ●  │ ●  │ ●  │ ●  │ ●  │ ●  │ ●  │ ●  │ ●  │
│ Fact-Checker       │ ·  │ ·  │ ◐  │ ◐  │ ·  │ ·  │ ◐  │ ·  │ ·  │
│ Audit Trail        │ ◐  │ ◐  │ ◐  │ ◐  │ ◐  │ ◐  │ ◐  │ ◐  │ ◐  │
│ Policy Engine      │ ◐  │ ·  │ ·  │ ·  │ ●  │ ·  │ ●  │ ●  │ ·  │
│ Rate Limiting      │ ◐  │ ·  │ ·  │ ·  │ ·  │ ●  │ ·  │ ·  │ ·  │
│ LGPD               │ ◐  │ ◐  │ ·  │ ●  │ ◐  │ ○  │ ○  │ ◐  │ ◐  │
└────────────────────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘

INTELIGÊNCIA — Quem precisa do quê:
┌────────────────────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
│                    │ E1 │ E2 │ E3 │ E4 │ E5 │ E6 │ E7 │ E8 │ E9 │
├────────────────────┼────┼────┼────┼────┼────┼────┼────┼────┼────┤
│ Learning Loop      │ ·  │ ●  │ ●  │ ●  │ ●  │ ·  │ ●  │ ●  │ ◐  │
│ A/B Testing        │ ·  │ ◐  │ ◐  │ ◐  │ ·  │ ◐  │ ◐  │ ·  │ ◐  │
│ Routing Adaptativo │ ·  │ ·  │ ·  │ ●  │ ●  │ ·  │ ·  │ ●  │ ·  │
│ Template Learning  │ ·  │ ●  │ ·  │ ·  │ ·  │ ◐  │ ·  │ ·  │ ◐  │
│ Calibration        │ ·  │ ·  │ ·  │ ●  │ ●  │ ·  │ ●  │ ●  │ ·  │
│ Score Normalization│ ·  │ ·  │ ·  │ ●  │ ·  │ ·  │ ●  │ ·  │ ·  │
│ Predictive Analyt. │ ·  │ ◐  │ ·  │ ◐  │ ·  │ ·  │ ·  │ ·  │ ·  │
│ Model Drift        │ ·  │ ·  │ ·  │ ●  │ ●  │ ·  │ ●  │ ●  │ ·  │
│ Conv. Memory       │ ·  │ ●  │ ●  │ ●  │ ●  │ ●  │ ●  │ ·  │ ·  │
│ Semantic Search    │ ·  │ ◐  │ ◐  │ ●  │ ·  │ ·  │ ·  │ ·  │ ·  │
│ Voice Analysis     │ ·  │ ·  │ ·  │ ·  │ ·  │ ·  │ ●  │ ·  │ ·  │
│ Embedding Service  │ ·  │ ·  │ ·  │ ◐  │ ·  │ ·  │ ·  │ ·  │ ◐  │
│ Long-Term Memory   │ ·  │ ·  │ ·  │ ·  │ ·  │ ·  │ ·  │ ·  │ ◐  │
└────────────────────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘

COMUNICAÇÃO — Canais por etapa:
┌────────────────────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
│                    │ E1 │ E2 │ E3 │ E4 │ E5 │ E6 │ E7 │ E8 │ E9 │
├────────────────────┼────┼────┼────┼────┼────┼────┼────┼────┼────┤
│ Email (Resend/SG)  │ ·  │ ·  │ ·  │ ·  │ ·  │ ●  │ ◐  │ ·  │ ●  │
│ WhatsApp (Twilio)  │ ·  │ ·  │ ·  │ ·  │ ·  │ ●  │ ●  │ ·  │ ●  │
│ Chat Web (candidat)│ ·  │ ·  │ ·  │ ·  │ ·  │ ·  │ ⚠  │ ·  │ ·  │
│ Teams (Graph API)  │ ·  │ ·  │ ·  │ ·  │ ·  │ ○  │ ·  │ ·  │ ◐  │
│ Telefone/VoIP      │ ·  │ ·  │ ·  │ ·  │ ·  │ ·  │ ◐  │ ·  │ ·  │
│ Feedback Automático│ ·  │ ·  │ ·  │ ·  │ ·  │ ·  │ ·  │ ◐  │ ◐  │
│ Notificação (Bell) │ ·  │ ·  │ ·  │ ·  │ ○  │ ○  │ ○  │ ○  │ ○  │
└────────────────────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘

● = ATIVO     ◐ = DISPONÍVEL (precisa ativar)     ○ = A IMPLEMENTAR     ⚠ = GAP BLOQUEANTE     · = N/A
```

---

## 1. VISÃO GERAL — O QUE EXISTE vs. O QUE FALTA

### 1.1 Resumo Executivo

O backend (`lia-agent-system`) possui uma arquitetura robusta com 10+ domínios, 30+ tools registradas, 6+ agentes ReAct migrados para LangGraph, 6 camadas de compliance (FairnessGuard, PII Masking, Fact-Checker, Audit, Policy Engine, LGPD) e **11 camadas de inteligência** (Learning Loop, A/B Testing, Routing Adaptativo, Template Learning, Calibration, Score Normalization, Predictive Analytics, Model Drift, Conversation Memory, Semantic Search, Voice Analysis) implementadas. O frontend (`plataforma-lia`) tem integração real via proxy Next.js → FastAPI.

**A distância entre "código existente" e "MVP funcional Alpha 1" está em 3 eixos:**

1. **Integração ponta-a-ponta** — Muitos serviços existem isolados mas não estão conectados no fluxo completo
2. **Infraestrutura externa** — ATS real (Gupy/Pandapé), Twilio WhatsApp, Resend/SendGrid, Apify, Microsoft Teams dependem de credenciais e configuração de produção
3. **Camadas de compliance ativas** — Existem no código mas precisam ser "ligadas" (feature flags, environment vars) em cada ponto do fluxo

---

## 2. TABELA MESTRE: ETAPAS × AGENTES × COMPLIANCE × INTELIGÊNCIA

### ETAPA 1: LOGIN

| Dimensão | Componente | Status | Arquivo Replit |
|----------|-----------|--------|----------------|
| **Domínio** | Auth | Implementado | `app/api/v1/auth.py` |
| **Serviço** | AuthService (JWT + WorkOS SSO) | Implementado | `app/services/auth_service.py` |
| **Tool** | — (não é agente) | N/A | — |
| **Frontend** | Login page + auth hooks | Implementado | `src/app/(auth)/login/` |
| **COMPLIANCE** | | | |
| ↳ FairnessGuard | N/A nesta etapa | — | — |
| ↳ PII Masking | Logs de login mascarados | ATIVO | `PIIMaskingFilter` global |
| ↳ Fact-Checker | N/A nesta etapa | — | — |
| ↳ Audit Trail | Login events | A CONFIGURAR | Precisa log de auth events |
| ↳ Policy Engine | Rate limiting de tentativas | A CONFIGURAR | `rate_limiter.py` |
| ↳ LGPD | Cookie consent | A VERIFICAR | — |
| **INTELIGÊNCIA** | | | |
| ↳ Learning Loop | N/A | — | — |
| ↳ A/B Testing | N/A | — | — |
| ↳ Routing Adaptativo | N/A | — | — |
| ↳ Template Learning | N/A | — | — |
| ↳ Calibration | N/A | — | — |
| ↳ Score Normalization | N/A | — | — |
| ↳ Predictive Analytics | N/A | — | — |
| ↳ Model Drift | N/A | — | — |
| ↳ Conv. Memory | N/A | — | — |
| ↳ Semantic Search | N/A | — | — |
| ↳ Voice Analysis | N/A | — | — |

**Gap:** Rate limiting de login + Audit trail de autenticação precisam ser ativados.

---

### ETAPA 2: EDITAR VAGA (importada do ATS)

| Dimensão | Componente | Status | Arquivo Replit |
|----------|-----------|--------|----------------|
| **Agente** | Ag.8 IntegradorATS | Implementado | `app/domains/ats_integration/` |
| **Domínio** | `ats_integration` + `job_management` | Implementado | `app/domains/` |
| **Serviços** | ATSSyncService, GupyClient, PandapeClient | Implementado | `app/services/ats_sync_service.py` |
| **Tools** | `sync_candidate_to_ats`, `fetch_candidate_from_ats`, `validate_ats_fields` | Registradas | `ats_integration_tool_registry.py` |
| **Frontend** | Página de vagas + edição | Implementado | `src/app/(dashboard)/jobs/` |
| **COMPLIANCE** | | | |
| ↳ FairnessGuard L1 | Bloquear requisitos discriminatórios no JD | PRECISA ATIVAR | `fairness_guard.py` → inserir no save JD |
| ↳ FairnessGuard L2 | Alertar termos proxy enviesados | PRECISA ATIVAR | `fairness_guard.py` → inserir no save JD |
| ↳ PII Masking | Strip PII antes de enviar ao LLM | ATIVO (global) | `strip_pii_for_llm_prompt` |
| ↳ Fact-Checker | N/A (não há claims numéricas) | — | — |
| ↳ Audit Trail | Log de edições de vaga | PRECISA ATIVAR | `audit_service.py` |
| ↳ Policy Engine | N/A nesta etapa | — | — |
| ↳ LGPD | Dados do ATS com consentimento | PRECISA VERIFICAR | Verificar fluxo de import |
| **INTELIGÊNCIA** | | | |
| ↳ Learning Loop | Captura edições do wizard (salary, skills, benefits) | ATIVO | `learning_loop_service.py` via `capture_from_wizard_update` |
| ↳ A/B Testing | Variantes de prompt para JD generation | DISPONÍVEL | `ab_testing_service.py` — precisa criar testes |
| ↳ Routing Adaptativo | N/A (domínio fixo: job_management) | — | — |
| ↳ Template Learning | Aprende templates após 3 vagas similares | ATIVO | `template_learning_service.py` |
| ↳ Calibration | N/A (sem scoring nesta etapa) | — | — |
| ↳ Score Normalization | N/A | — | — |
| ↳ Predictive Analytics | `predict_time_to_fill`, `predict_optimal_salary` | DISPONÍVEL | `ml/outcome_predictor.py` |
| ↳ Model Drift | N/A | — | — |
| ↳ Conv. Memory | Entity tracking (vaga mencionada) | ATIVO | `conversation_state.py` |
| ↳ Semantic Search | Expansão de skills para JD | DISPONÍVEL | `semantic_search_service.py` |
| ↳ Voice Analysis | N/A | — | — |

**Gap:** Sync com ATS real depende de credenciais de produção (API keys Gupy/Pandapé). FairnessGuard precisa virar middleware no endpoint de salvar vaga.

---

### ETAPA 3: CONFIGURAR ROTEIRO WSI

| Dimensão | Componente | Status | Arquivo Replit |
|----------|-----------|--------|----------------|
| **Agente** | Ag.4 EntrevistadorWSI | Implementado | `app/domains/cv_screening/` |
| **Domínio** | `cv_screening` (WSI) + `wizard` | Implementado | `app/domains/` |
| **Serviços** | WSIService, JDGeneratorService | Implementado | `wsi_service.py`, `jd_generator_service.py` |
| **Tools** | `generate_screening_questions`, `analyze_jd_and_suggest_competencies` | Registradas | WSI domain tools |
| **Frontend** | Modal WSI + Preview Vaga | Implementado | `src/components/modals/` |
| **COMPLIANCE** | | | |
| ↳ FairnessGuard L1-L2 | Perguntas geradas sem viés | PRECISA ATIVAR | Pós-geração de perguntas WSI |
| ↳ PII Masking | Strip antes de enviar JD ao LLM | ATIVO | `strip_pii_for_llm_prompt` |
| ↳ Fact-Checker | Validar claims nas perguntas | PRECISA ATIVAR | `fact_checker.py` |
| ↳ Audit Trail | Log de geração de roteiro | PRECISA ATIVAR | `audit_service.py` |
| ↳ Policy Engine | N/A | — | — |
| ↳ LGPD | N/A (dados internos) | — | — |
| **INTELIGÊNCIA** | | | |
| ↳ Learning Loop | Captura edições nas perguntas geradas | ATIVO | `learning_loop_service.py` |
| ↳ A/B Testing | Variantes de prompt para geração de perguntas | DISPONÍVEL | `ab_testing_service.py` |
| ↳ Routing Adaptativo | N/A (domínio fixo) | — | — |
| ↳ Template Learning | N/A (roteiro é por vaga) | — | — |
| ↳ Calibration | N/A | — | — |
| ↳ Score Normalization | N/A | — | — |
| ↳ Predictive Analytics | N/A | — | — |
| ↳ Model Drift | N/A | — | — |
| ↳ Conv. Memory | Tracking da vaga ativa na sessão | ATIVO | `conversation_state.py` |
| ↳ Semantic Search | Expansão de competências sugeridas | DISPONÍVEL | `semantic_search_service.py` |
| ↳ Voice Analysis | N/A | — | — |

**Gap:** FairnessGuard e Fact-Checker precisam ser ativados como step pós-geração nas perguntas WSI.

---

### ETAPA 4: BUSCAR CANDIDATOS (Funil de Talentos)

| Dimensão | Componente | Status | Arquivo Replit |
|----------|-----------|--------|----------------|
| **Agente** | Ag.2 SourcingAgent | Implementado | `app/domains/sourcing/` |
| **Agente** | Ag.3 TriagemCurricular | Implementado | `app/domains/cv_screening/` |
| **Agente** | Ag.5 AvaliadorWSI | Implementado | `app/domains/cv_screening/` (WSI Evaluator) |
| **Domínio** | `sourcing` + `pipeline` | Implementado | `app/domains/` |
| **Serviços** | SourcingPipelineService, CandidateEnrichmentService, CVScoringService | Implementados | `app/services/` |
| **Tools** | `search_candidates`, `analyze_profile`, `score_candidate`, `enrich_profile` | Registradas | `sourcing_tool_registry.py` |
| **Frontend** | Funil de Talentos (tabela + filtros + sidebar LIA) | Implementado | `src/app/(dashboard)/candidates/` |
| **Busca** | Elasticsearch + PGVector + WRF | PARCIAL | ES e PGVector configurados; WRF Dynamic K precisa validação |
| **COMPLIANCE** | | | |
| ↳ FairnessGuard L1 | Bloquear buscas discriminatórias | ATIVO | `MainOrchestrator` L35-47 |
| ↳ FairnessGuard L2 | Alertar proxy terms na busca | ATIVO | `MainOrchestrator` L48-62 |
| ↳ FairnessGuard L3 | Análise semântica nas respostas do LLM | PRECISA ATIVAR | `RubricEvaluationService` — sector rules |
| ↳ PII Masking | Strip PII de candidatos antes do LLM | ATIVO | `strip_pii_for_llm_prompt` |
| ↳ Fact-Checker | Validar claims nas análises LIA | PRECISA ATIVAR | `fact_checker.py` |
| ↳ Audit Trail | Log de buscas + scores | PRECISA ATIVAR | `audit_service.py` |
| ↳ Policy Engine | N/A | — | — |
| ↳ LGPD | Modo anônimo no Toon | IMPLEMENTADO | `ToonService` `anonymize=True` |
| ↳ Bias Detection | `_LEARNING_PROTECTED_FIELDS` | ATIVO | Bloqueia learning de campos protegidos |
| **INTELIGÊNCIA** | | | |
| ↳ Learning Loop | Captura accept/modify/reject de candidatos avaliados | ATIVO | `learning_loop_service.py` |
| ↳ A/B Testing | Variantes de prompt para scoring | DISPONÍVEL | `ab_testing_service.py` |
| ↳ Routing Adaptativo | Ajuste de confiança sourcing vs screening | ATIVO | `routing_learning_service.py` (0.8x-1.2x) |
| ↳ Template Learning | N/A (não é criação de vaga) | — | — |
| ↳ Calibration | Feedback explícito/implícito sobre scores | ATIVO | `calibration_service.py` |
| ↳ Score Normalization | Normaliza scores por difficulty_coefficient | ATIVO | `score_normalization_service.py` |
| ↳ Predictive Analytics | `predict_skill_success` | DISPONÍVEL | `ml/outcome_predictor.py` |
| ↳ Model Drift | Monitora score_drift + approval_drift | ATIVO | `model_drift_service.py` — trigger automático |
| ↳ Conv. Memory | Tracking de candidatos mencionados + filtros | ATIVO | `conversation_state.py` |
| ↳ Semantic Search | Expansão semântica de skills/títulos/indústrias | ATIVO | `semantic_search_service.py` (Gemini 768-dim) |
| ↳ Voice Analysis | N/A (busca não é por voz) | — | — |

**Gap CRÍTICO:** WRF Dynamic K + LLM Job Classification precisa validação end-to-end. FairnessGuard L3 precisa ser ativado explicitamente (depende de `ALPHA1_SECTOR_RULES[sector].fairness_layer3_enabled`). Integração com Pearch/Apify depende de API keys.

---

### ETAPA 5: APROVAR MAPEADOS (Gate 1)

| Dimensão | Componente | Status | Arquivo Replit |
|----------|-----------|--------|----------------|
| **Agente** | Ag.0 Orchestrator | Implementado | `main_orchestrator.py` |
| **Agente** | Ag.7 AnalistaFeedback | Implementado | `app/domains/analytics/` |
| **Agente** | Ag.8 IntegradorATS | Implementado | `app/domains/ats_integration/` |
| **Domínio** | `pipeline` + `kanban` | Implementado | `app/domains/` |
| **Serviços** | KanbanService, PipelineTransitionService | Implementados | `app/services/` |
| **Tools** | `suggest_movements`, `check_rejection_fairness`, `identify_bottlenecks` | Registradas | `kanban_tool_registry.py` |
| **Frontend** | Kanban board + SmartTransitionModal | Implementado | `src/app/(dashboard)/job-kanban/` |
| **COMPLIANCE** | | | |
| ↳ FairnessGuard | `check_rejection_fairness` como tool | REGISTRADA | Precisa ser automática, não sob demanda |
| ↳ PII Masking | Ativo globalmente | ATIVO | — |
| ↳ Fact-Checker | N/A (decisão binária) | — | — |
| ↳ Audit Trail | Log de aprovações/rejeições + overrides | PRECISA ATIVAR | `audit_service.py` — `record_human_review` |
| ↳ Policy Engine | Autonomy levels + HITL thresholds por setor | IMPLEMENTADO | `ALPHA1_SECTOR_RULES` em `policy_engine_service.py` |
| ↳ Escalation | Trigger quando AI confidence < threshold | IMPLEMENTADO | `trigger_escalation` |
| ↳ LGPD | Consentimento antes de contato | PRECISA VERIFICAR | Fluxo de consentimento |
| **INTELIGÊNCIA** | | | |
| ↳ Learning Loop | Captura decisões: aceitar/rejeitar/modificar AI suggestion | ATIVO | `learning_loop_service.py` |
| ↳ A/B Testing | N/A (decisão humana) | — | — |
| ↳ Routing Adaptativo | Correções de rota alimentam ajustes | ATIVO | `routing_learning_service.py` |
| ↳ Template Learning | N/A | — | — |
| ↳ Calibration | Implicit feedback: avançar candidato low-score = sinal | ATIVO | `calibration_service.py` → `record_implicit_feedback` |
| ↳ Score Normalization | N/A (scores já normalizados) | — | — |
| ↳ Predictive Analytics | N/A | — | — |
| ↳ Model Drift | Trigger se approval_drift > 10 p.p. | ATIVO | `model_drift_service.py` |
| ↳ Conv. Memory | Tracking de ações no kanban | ATIVO | `conversation_state.py` |
| ↳ Semantic Search | N/A | — | — |
| ↳ Voice Analysis | N/A | — | — |

**Gap:** `check_rejection_fairness` precisa ser chamado automaticamente (não sob demanda). Audit de overrides humanos precisa ativação.

---

### ETAPA 6: CONTATO VIA EMAIL + FOLLOW-UP

| Dimensão | Componente | Status | Arquivo Replit |
|----------|-----------|--------|----------------|
| **Agente** | Ag.0 Orchestrator | Implementado | `main_orchestrator.py` |
| **Domínio** | `communication` | Implementado | `app/domains/communication/` |
| **Serviços** | EmailService (Resend/SendGrid), WhatsAppService (Twilio) | Implementados | `email_service.py`, `whatsapp_service.py` |
| **Tools** | `send_email`, `send_whatsapp`, `send_bulk_email`, `send_feedback` | Registradas | `communication_tools.py` |
| **Frontend** | Templates de email | Implementado | `src/components/` |
| **COMPLIANCE** | | | |
| ↳ FairnessGuard | N/A (email é template) | — | — |
| ↳ PII Masking | Emails não logam dados pessoais | ATIVO | `PIIMaskingFilter` |
| ↳ Fact-Checker | N/A | — | — |
| ↳ Audit Trail | Log de envios + opens + clicks | PRECISA ATIVAR | `audit_service.py` |
| ↳ Policy Engine / Rate Limiting | Limite de envio por empresa/dia | IMPLEMENTADO | `RateLimitRule` sliding window |
| ↳ LGPD | Opt-out link no email | PRECISA IMPLEMENTAR | Template precisa unsubscribe |
| **INTELIGÊNCIA** | | | |
| ↳ Learning Loop | N/A (email é ação, não sugestão) | — | — |
| ↳ A/B Testing | Variantes de template de email | DISPONÍVEL | `ab_testing_service.py` |
| ↳ Routing Adaptativo | N/A | — | — |
| ↳ Template Learning | Templates de email aprendidos | DISPONÍVEL | `template_learning_service.py` |
| ↳ Calibration | N/A | — | — |
| ↳ Score Normalization | N/A | — | — |
| ↳ Predictive Analytics | N/A | — | — |
| ↳ Model Drift | N/A | — | — |
| ↳ Conv. Memory | Tracking de candidatos contatados | ATIVO | `conversation_state.py` |
| ↳ Semantic Search | N/A | — | — |
| ↳ Voice Analysis | N/A | — | — |

**Gap:** Follow-up automático de 7 dias precisa de **scheduler** (Celery/cron/background task) que NÃO existe. Template de email precisa de link de opt-out (LGPD). Tracking de opens/clicks precisa configuração no provedor.

---

### ETAPA 7: TRIAGEM WSI (Chat Web / WhatsApp)

| Dimensão | Componente | Status | Arquivo Replit |
|----------|-----------|--------|----------------|
| **Agente** | Ag.0 Orchestrator | Implementado | `main_orchestrator.py` |
| **Agente** | Ag.4 EntrevistadorWSI | Implementado | `app/domains/cv_screening/` |
| **Agente** | Ag.5 AvaliadorWSI | Implementado | `app/domains/cv_screening/` |
| **Domínio** | `cv_screening` + `communication` | Implementado | `app/domains/` |
| **Serviços** | WSIService, WhatsAppService, VoiceService | Implementados | `app/services/` |
| **Tools** | `generate_screening_questions`, `analyze_response`, `calculate_wsi` | Registradas | WSI tools |
| **Frontend Chat Web** | Chat page para candidato | **NÃO EXISTE** | PRECISA SER CONSTRUÍDO |
| **COMPLIANCE** | | | |
| ↳ FairnessGuard L1-L2 | Perguntas e análises sem viés | PRECISA ATIVAR | Em cada step da triagem |
| ↳ FairnessGuard L3 | Análise semântica das respostas | PRECISA ATIVAR | Sector-dependent: `fairness_layer3_enabled` |
| ↳ PII Masking | Strip PII nas respostas antes do LLM | ATIVO | `strip_pii_for_llm_prompt` |
| ↳ Fact-Checker | Validar scores e claims do WSI | PRECISA ATIVAR | `fact_checker.py` |
| ↳ Audit Trail | Log completo: cada pergunta/resposta/score | PRECISA ATIVAR | `audit_service.py` |
| ↳ Policy Engine | Autonomy level por setor | IMPLEMENTADO | `ALPHA1_SECTOR_RULES` |
| ↳ LGPD | Consentimento antes da triagem | **PRECISA IMPLEMENTAR** | Tela de aceite frontend |
| ↳ Timeout/Abandono | Lembretes 48h + 48h | **PRECISA IMPLEMENTAR** | Scheduler |
| **INTELIGÊNCIA** | | | |
| ↳ Learning Loop | Captura padrões de resposta por competência | ATIVO | `learning_loop_service.py` |
| ↳ A/B Testing | Variantes de prompt para análise de respostas | DISPONÍVEL | `ab_testing_service.py` |
| ↳ Routing Adaptativo | N/A (domínio fixo: cv_screening) | — | — |
| ↳ Template Learning | N/A | — | — |
| ↳ Calibration | Calibração de scores WSI | ATIVO | `calibration_service.py` |
| ↳ Score Normalization | Normalização por versão do roteiro | ATIVO | `score_normalization_service.py` |
| ↳ Predictive Analytics | N/A | — | — |
| ↳ Model Drift | Monitora drift em scores WSI | ATIVO | `model_drift_service.py` |
| ↳ Conv. Memory | Estado da triagem por candidato | ATIVO | `conversation_state.py` |
| ↳ Semantic Search | N/A (perguntas já definidas) | — | — |
| ↳ Voice Analysis | STT/TTS para triagem por voz | IMPLEMENTADO | `voice_service.py` (Deepgram + OpenAI) |

**Gap CRÍTICO:** Chat web público para candidato NÃO existe. Timeouts 48h+48h precisam de scheduler. Consentimento LGPD precisa de tela frontend.

---

### ETAPA 8: APROVAR TRIADOS (Gate 2)

| Dimensão | Componente | Status | Arquivo Replit |
|----------|-----------|--------|----------------|
| **Agente** | Ag.7 AnalistaFeedback | Implementado | `app/domains/analytics/` |
| **Agente** | Ag.8 IntegradorATS | Implementado | `app/domains/ats_integration/` |
| **Domínio** | `pipeline` + `kanban` + `analytics` | Implementado | `app/domains/` |
| **Tools** | `suggest_movements`, `check_rejection_fairness` | Registradas | `kanban_tool_registry.py` |
| **Frontend** | Kanban board (mesmo de Gate 1) | Implementado | `src/app/(dashboard)/job-kanban/` |
| **COMPLIANCE** | | | |
| ↳ FairnessGuard | Validação de rejeição (motivo) | REGISTRADA | `check_rejection_fairness` tool |
| ↳ PII Masking | Ativo | ATIVO | — |
| ↳ Audit Trail | Log de aprovação/rejeição Gate 2 | PRECISA ATIVAR | `audit_service.py` |
| ↳ Policy Engine | HITL thresholds por setor | IMPLEMENTADO | `ALPHA1_SECTOR_RULES` |
| ↳ LGPD | Dados compartilhados com próxima etapa | PRECISA VERIFICAR | Minimização de dados |
| **INTELIGÊNCIA** | | | |
| ↳ Learning Loop | Feedback sobre decisões Gate 2 | ATIVO | `learning_loop_service.py` |
| ↳ Calibration | Implicit feedback: avançar candidato low-WSI | ATIVO | `calibration_service.py` |
| ↳ Model Drift | Monitora approval_drift Gate 2 | ATIVO | `model_drift_service.py` |
| ↳ Routing Adaptativo | Correções de rota entre domínios | ATIVO | `routing_learning_service.py` |
| ↳ (demais) | N/A nesta etapa | — | — |

**Gap:** Mesmo que Gate 1 — `check_rejection_fairness` precisa ser automática.

---

### ETAPA 9: AGENDAR ENTREVISTA + FEEDBACK

| Dimensão | Componente | Status | Arquivo Replit |
|----------|-----------|--------|----------------|
| **Agente** | Ag.6 SchedulingAgent | Implementado | `app/domains/interview_scheduling/` |
| **Agente** | Ag.7 AnalistaFeedback | Implementado | `app/domains/analytics/` |
| **Domínio** | `scheduling` + `analytics` + `communication` | Implementados | `app/domains/` |
| **Serviços** | SchedulingService (ICS + Teams), EmailService, WhatsAppService | Implementados | `app/services/` |
| **Tools** | `schedule_interview`, `send_feedback` | Registradas | `communication_tools.py` |
| **Frontend** | Scheduling UI | Implementado | `src/app/(dashboard)/` |
| **COMPLIANCE** | | | |
| ↳ FairnessGuard | Feedback sem viés | PRECISA ATIVAR | Análise do texto de feedback |
| ↳ PII Masking | Ativo | ATIVO | — |
| ↳ Fact-Checker | N/A | — | — |
| ↳ Audit Trail | Log de aprovação/rejeição + feedback enviado | PRECISA ATIVAR | `audit_service.py` |
| ↳ Policy Engine | N/A | — | — |
| ↳ LGPD | Dados compartilhados com calendário | PRECISA VERIFICAR | Minimização de dados no ICS |
| **INTELIGÊNCIA** | | | |
| ↳ Learning Loop | Feedback sobre qualidade do feedback gerado | DISPONÍVEL | `learning_loop_service.py` |
| ↳ A/B Testing | Variantes de template de feedback | DISPONÍVEL | `ab_testing_service.py` |
| ↳ Template Learning | Templates de feedback aprendidos | DISPONÍVEL | `template_learning_service.py` |
| ↳ Embedding Service | Embedding do perfil para matching futuro | DISPONÍVEL | `embedding_service.py` (Gemini 768-dim) |
| ↳ Long-Term Memory | Armazena episódios da vaga para referência | DISPONÍVEL | `long_term_memory.py` |
| ↳ (demais) | N/A nesta etapa | — | — |

**Gap:** Agendamento com Microsoft Teams depende de configuração de tenant (Graph API). ICS funciona standalone.

---

## 3. MATRIZ CONSOLIDADA: COMPLIANCE POR AGENTE

| Agente | Domínio | FG L1 | FG L2 | FG L3 | PII | LGPD | Fact-Check | Audit | Policy | Bias Det. |
|--------|---------|:-----:|:-----:|:-----:|:---:|:----:|:----------:|:-----:|:------:|:---------:|
| Ag.0 Orchestrator | orchestration | ATIVO | ATIVO | — | ATIVO | — | — | Parcial | ATIVO | Via FG |
| Ag.2 Sourcing | sourcing | ATIVO | ATIVO | A ativar | ATIVO | Anonymize | A ativar | A ativar | — | A ativar |
| Ag.3 TriagemCurr. | cv_screening | A ativar | A ativar | A ativar | ATIVO | A verificar | A ativar | A ativar | — | A ativar |
| Ag.4 Entrev.WSI | cv_screening | A ativar | A ativar | A ativar | ATIVO | A impl. | A ativar | A ativar | — | A ativar |
| Ag.5 Avaliador WSI | cv_screening | A ativar | A ativar | A ativar | ATIVO | A verificar | A ativar | A ativar | — | A ativar |
| Ag.6 Scheduling | scheduling | — | — | — | ATIVO | A verificar | — | A ativar | — | — |
| Ag.7 Feedback | analytics | A ativar | A ativar | — | ATIVO | — | A ativar | A ativar | — | A ativar |
| Ag.8 ATS Integr. | ats_integration | — | — | — | ATIVO | A verificar | — | A ativar | — | — |

**Legenda:** ATIVO = funcionando | A ativar = código existe, precisa ligar | A impl. = código não existe | A verificar = precisa checagem

---

## 4. MATRIZ CONSOLIDADA: INTELIGÊNCIA POR ETAPA

| Etapa | Learning Loop | A/B Test | Routing | Template | Calibr. | Score Norm. | Predict. | Drift | Conv. Mem. | Semantic | Voice |
|-------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1. Login | — | — | — | — | — | — | — | — | — | — | — |
| 2. Editar Vaga | ATIVO | DISP | — | ATIVO | — | — | DISP | — | ATIVO | DISP | — |
| 3. Roteiro WSI | ATIVO | DISP | — | — | — | — | — | — | ATIVO | DISP | — |
| 4. Buscar Cand. | ATIVO | DISP | ATIVO | — | ATIVO | ATIVO | DISP | ATIVO | ATIVO | ATIVO | — |
| 5. Gate 1 | ATIVO | — | ATIVO | — | ATIVO | — | — | ATIVO | ATIVO | — | — |
| 6. Email/Follow | — | DISP | — | DISP | — | — | — | — | ATIVO | — | — |
| 7. Triagem WSI | ATIVO | DISP | — | — | ATIVO | ATIVO | — | ATIVO | ATIVO | — | IMPL |
| 8. Gate 2 | ATIVO | — | ATIVO | — | ATIVO | — | — | ATIVO | — | — | — |
| 9. Agendar/Feed. | DISP | DISP | — | DISP | — | — | — | — | — | — | — |

**Legenda:** ATIVO = integrado e funcionando | DISP = disponível, precisa wiring | IMPL = implementado mas não integrado no fluxo | — = N/A

---

## 5. DETALHAMENTO DAS 11 CAMADAS DE INTELIGÊNCIA

### 5.1 Learning Loop (Captura Silenciosa)
- **Arquivo:** `app/shared/learning/learning_loop_service.py` (1137 linhas)
- **Mecanismo:** Observa o que o recrutador aceita, modifica ou rejeita sem pedir feedback explícito
- **Outcomes:** `accepted` | `modified` | `rejected` | `ignored`
- **Pattern Types:** salary_preference, skill_preference, benefit_preference, work_model_preference, screening_preference, jd_style_preference, source_trust
- **Confidence:** Baseada em sample size (≥20 = high, ≥10 = medium, ≥5 = low)
- **FairnessGuard Integration:** `validate_learning_batch()` bloqueia padrões discriminatórios ANTES de persistir (F1-02)
- **Model Drift Integration:** Trigger automático via `asyncio.create_task` quando feedback é `rejected` ou `ignored`
- **Snapshot Integration:** `learning_snapshot_service` salva snapshot ANTES de aplicar patterns (rollback Z2-01)

### 5.2 A/B Testing
- **Arquivo:** `app/shared/learning/ab_testing_service.py` (307 linhas)
- **Mecanismo:** Hash-based traffic splitting (MD5 → bucket 0-9999)
- **Estatísticas:** z-score, p-value (erfc), 95% CI, improvement percentage
- **Significância:** p < 0.05 AND |improvement| > 5%
- **Modelo:** `PromptVariant` (test_name, variant_name, traffic_percentage) + `ABTestResult` (metric_name, metric_value)

### 5.3 Routing Adaptativo
- **Arquivo:** `app/services/routing_learning_service.py`
- **Mecanismo:** Quando usuário corrige roteamento (mensagem foi pro domínio errado), ajusta multiplicadores de confiança por domínio
- **Range:** 0.8x (muitos erros) a 1.2x (alta precisão)
- **Método:** `compute_domain_confidence_adjustments(company_id, db)` → Dict[str, float]

### 5.4 Template Learning
- **Arquivo:** `app/shared/learning/template_learning_service.py`
- **Mecanismo:** Após 3 vagas similares (mesmo setor/seniority), gera template automaticamente
- **Métodos:** `learn_from_job_creation()`, `suggest_templates_for_improvement()`

### 5.5 Calibration
- **Arquivo:** `app/services/calibration_service.py`
- **Mecanismo:** Dual feedback — explícito (thumbs up/down) + implícito (avançar candidato low-score)
- **Output:** `CalibrationSuggestion` (ex: "Reduzir peso de skill técnica em 15%")
- **Métodos:** `record_explicit_feedback()`, `record_implicit_feedback()`, `generate_suggestions()`

### 5.6 Score Normalization
- **Arquivo:** `app/domains/cv_screening/services/score_normalization_service.py`
- **Mecanismo:** Ajusta scores baseado no `difficulty_coefficient` da versão do questionário
- **Objetivo:** Candidatos que responderam versões mais difíceis não são penalizados

### 5.7 Predictive Analytics
- **Arquivo:** `app/services/ml/outcome_predictor.py`
- **Métodos:**
  - `predict_time_to_fill(db, job_data, company_id)` → dias estimados + confidence
  - `predict_optimal_salary(db, job_data, company_id)` → faixa salarial competitiva
  - `predict_skill_success(db, skill_name, company_id)` → probabilidade de sucesso

### 5.8 Model Drift
- **Arquivo:** `app/services/model_drift_service.py`
- **4 Dimensões monitoradas:**
  - Score Drift: variação > 0.5 pts na janela de 7 dias
  - Approval Drift: variação > 10 pontos percentuais
  - Cost Drift: aumento significativo de custo LLM
  - Latency Drift: degradação de tempo de resposta
- **Trigger:** Chamado automaticamente pelo Learning Loop quando feedback negativo acumula

### 5.9 Conversation Memory
- **Arquivo:** `app/shared/memory/conversation_state.py`
- **Mecanismo:** Estado efêmero da sessão de chat
- **Recursos:**
  - Entity tracking (última vaga, último candidato mencionado)
  - Pronoun resolution ("conte mais sobre **ele**" → resolve para último candidato)
  - Active filters tracking (filtros de busca persistem na sessão)
- **Long-Term Memory:** `libs/agents-core/lia_agents_core/long_term_memory.py` — episódios + compressão LLM após 30 dias

### 5.10 Semantic Search
- **Arquivo:** `app/shared/intelligence/semantic_search_service.py`
- **Provider:** Gemini `text-embedding-004` (768 dimensões)
- **Cache:** Redis para evitar re-embedding
- **Domínios:** Skills, Job Titles, Industries, Locations
- **Métodos:** `expand_query(domain, query)`, `expand_skills()`, `expand_job_titles()`
- **Embedding Service:** `app/shared/intelligence/embedding_service.py` — wrapper para geração de vetores

### 5.11 Voice Analysis
- **Arquivo:** `app/services/voice_service.py`
- **STT Providers:** Deepgram (primário), Whisper (fallback)
- **TTS Provider:** OpenAI (`voice="nova"`)
- **Uso:** Triagem WSI por voz (candidato pode responder por áudio)

---

## 6. GAPS IDENTIFICADOS

### 6.1 Gaps Estruturais (faltam no fluxo)

| # | Gap | Impacto | Prioridade |
|---|-----|---------|-----------|
| G1 | **Scheduler/Background Jobs** — Follow-up 7 dias, timeout triagem 48h+48h, lembretes | Sem isso, etapas 6B e 7A não funcionam | BLOQUEANTE |
| G2 | **Chat Web Público (Candidato)** — Página onde candidato faz triagem WSI | Sem isso, etapa 7 inteira não funciona | BLOQUEANTE |
| G3 | **Webhook de Email** — Tracking de opens/clicks para follow-up inteligente | Follow-up fica "cego" sem saber se candidato leu | ALTO |
| G4 | **Consentimento LGPD (Tela de Aceite)** — Antes da triagem WSI | Obrigatório legalmente | BLOQUEANTE |
| G5 | **Unsubscribe Link** — Nos templates de email | LGPD/CAN-SPAM compliance | ALTO |
| G6 | **Notificações (Teams/Email/Bell)** — Sistema de alertas ao consultor | Mencionado no roadmap mas não implementado como sistema | ALTO |
| G7 | **Configuração de Infra Externa** — API keys: Twilio, Resend/SendGrid, Apify, ATS | Sem credenciais, tudo roda em "dev mode" | BLOQUEANTE |

### 6.2 Gaps de Compliance

| # | Gap | O que existe | O que falta |
|---|-----|-------------|-------------|
| C1 | **FairnessGuard ativo em todos os pontos** | L1-L2 no Orchestrator | Ativar em: save JD, geração WSI, análise de resposta, feedback, scoring |
| C2 | **FairnessGuard L3 (Semântico)** | Código existe, sector rules definidas | Ativar como step obrigatório pós-LLM (tech/financeiro/saude/rpo) |
| C3 | **Audit Trail completo** | `AuditService` com 8 decision types | Ativar em: login, edição vaga, geração roteiro, busca, aprovação, contato, triagem, feedback |
| C4 | **LGPD Consent Flow** | Endpoints de consentimento existem | Falta fluxo frontend + enforcement antes de processar candidato |
| C5 | **Fact-Checker em todos os outputs** | 4 checkers (salary, count, %, date) + 3 granulares (V5) | Ativar como middleware pós-resposta em todos os agentes |
| C6 | **Bias Audit Report** | FairnessGuard coleta dados | Falta dashboard/relatório periódico de Four-Fifths Rule |
| C7 | **EU AI Act Compliance** | Mencionado nos docs | Falta classificação de risco por agente e disclosure obrigatório |

### 6.3 Gaps de Inteligência

| # | Gap | Status | O que falta |
|---|-----|--------|-------------|
| I1 | **A/B Testing sem testes criados** | Serviço implementado | Precisa definir e criar os primeiros testes (JD prompt, scoring prompt) |
| I2 | **Predictive Analytics não integrado no fluxo** | Serviço implementado | Precisa ser chamado na UI de criação de vaga (predict_time_to_fill, predict_optimal_salary) |
| I3 | **Template Learning sem trigger automático** | Serviço implementado | Precisa hook pós-criação de vaga para chamar `learn_from_job_creation` |
| I4 | **Voice Analysis não integrado na triagem web** | STT/TTS implementado | Precisa UI de gravação de áudio na página de triagem do candidato |
| I5 | **Long-Term Memory sem compressão ativa** | Código de compressão existe | Precisa de cron job para executar `compress_old_episodes` periodicamente |
| I6 | **Semantic Search parcialmente wired** | Expansão funciona | Precisa ser integrado no fluxo de busca de candidatos como step automático |

---

## 7. MAPA DE PRIORIDADES DE CONSTRUÇÃO

### Fase 0: INFRAESTRUTURA (Semana 1-2)

| # | Item | Tipo | Esforço |
|---|------|------|---------|
| P0.1 | Configurar credenciais de produção (Twilio, Resend, Apify, ATS) | Config | 1-2 dias |
| P0.2 | Implementar Scheduler/Background Jobs (Celery ou similar) | Infra | 3-5 dias |
| P0.3 | Configurar Elasticsearch + PGVector em produção | Infra | 2-3 dias |
| P0.4 | Ativar Audit Trail em todos os endpoints | Backend | 2-3 dias |

### Fase 1: FLUXO CORE (Semana 2-4)

| # | Item | Agentes | Compliance | Inteligência | Esforço |
|---|------|---------|------------|-------------|---------|
| P1.1 | Login funcional + rate limiting | — | Rate Limiting, Audit | — | 1 dia |
| P1.2 | Import/Edição de Vaga do ATS | Ag.8 | FG L1-L2, Audit | Template Learning, Predictive | 2-3 dias |
| P1.3 | Configurar Roteiro WSI | Ag.4 | FG L1-L2, Fact-Check | A/B Testing, Learning Loop | 2-3 dias |
| P1.4 | Busca de Candidatos | Ag.2, Ag.3 | FG L1-L3, PII, Audit | Semantic Search, Calibration, Score Norm. | 5-7 dias |
| P1.5 | Aprovação Kanban (Gate 1) | Ag.0, Ag.7, Ag.8 | check_rejection_fairness, Policy, Audit | Calibration, Learning Loop | 3-4 dias |
| P1.6 | Envio de Email de Contato | Ag.0 | Rate Limiting, LGPD (opt-out), Audit | A/B Testing (templates) | 2-3 dias |

### Fase 2: TRIAGEM + AUTOMAÇÃO (Semana 4-6)

| # | Item | Agentes | Compliance | Inteligência | Esforço |
|---|------|---------|------------|-------------|---------|
| P2.1 | Chat Web Público para Triagem WSI | Ag.0, Ag.4, Ag.5 | FG L1-L3, LGPD Consent, PII, Audit | Voice Analysis, Conv. Memory, Score Norm. | 7-10 dias |
| P2.2 | Follow-up Automático 7 dias | Ag.0 | Rate Limiting, Audit | — | 3-4 dias |
| P2.3 | Timeout + Abandono de Triagem | Ag.4 | Scheduler, Audit | — | 2-3 dias |
| P2.4 | Score WSI + Parecer Textual | Ag.5 | Fact-Check, Bias Detection, Audit | Calibration, Model Drift | 3-5 dias |

### Fase 3: GATES + SCHEDULING (Semana 6-8)

| # | Item | Agentes | Compliance | Inteligência | Esforço |
|---|------|---------|------------|-------------|---------|
| P3.1 | Gate 2 (Aprovar/Reprovar Triados) | Ag.7, Ag.8 | FG, Policy Engine, Audit | Learning Loop, Calibration | 3-4 dias |
| P3.2 | Agendamento de Entrevista | Ag.6 | LGPD (dados calendário), Audit | Embedding Service | 3-5 dias |
| P3.3 | Feedback Automático (Reprovados) | Ag.7 | FG (texto), Audit | A/B Testing, Template Learning | 2-3 dias |
| P3.4 | Notificações Teams/Email/Bell | Todos | Audit | — | 3-5 dias |

### Fase 4: COMPLIANCE + INTELIGÊNCIA PROFUNDA (Semana 8-10)

| # | Item | Tipo | Esforço |
|---|------|------|---------|
| P4.1 | Bias Audit Dashboard (Four-Fifths Rule) | Frontend + Backend | 5-7 dias |
| P4.2 | EU AI Act Risk Classification por agente | Docs + Backend | 3-5 dias |
| P4.3 | LGPD DSR (Data Subject Requests) — export/delete | Backend | 3-5 dias |
| P4.4 | Criar primeiros A/B Tests (JD prompt, scoring prompt) | Backend | 2-3 dias |
| P4.5 | Integrar Predictive Analytics na UI de vagas | Frontend + Backend | 3-4 dias |
| P4.6 | Ativar Long-Term Memory compression (cron) | Infra | 1-2 dias |
| P4.7 | SOX Audit Export (para auditoria externa) | Backend | 2-3 dias |

---

## 8. GRAFO DE DEPENDÊNCIAS DOS AGENTES

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

---

## 9. DETALHAMENTO FairnessGuard — ARQUITETURA 3 CAMADAS

### Layer 1: Explicit Bias Block (350+ patterns, 13 categorias)
- **Categorias:** gender, age, ethnicity, religion, disability, marital_status, sexual_orientation, pregnancy, appearance, social_class, political, nationality, health
- **Ação:** BLOCK — impede processamento
- **Integração ativa:** MainOrchestrator (pré-roteamento)
- **Protected fields:** `_LEARNING_PROTECTED_FIELDS` = {gender, age, ethnicity, marital_status, photo, institution, address, religion, disability, cv_gaps}

### Layer 2: Implicit Bias Soft Warning (proxy terms)
- **Exemplos:** "dinâmico" → proxy para age, "boa aparência" → proxy para appearance
- **Ação:** WARN — permite com alerta
- **Integração ativa:** MainOrchestrator (pré-roteamento)

### Layer 3: Semantic Analysis (LLM-based)
- **Provider:** Gemini (análise semântica profunda)
- **Ação:** WARN ou BLOCK dependendo da severidade
- **Integração:** Condicionada por setor via `ALPHA1_SECTOR_RULES[sector].fairness_layer3_enabled`
- **Setores com L3 ativo:** tech, financeiro, saude, rpo
- **Setores sem L3:** varejo, logistica

### FairnessGuard no Learning Loop (F1-02)
- `validate_learning_batch()` — chamado ANTES de persistir patterns aprendidos
- Bloqueia patterns que correlacionam com campos protegidos
- Audit trail automático quando pattern é bloqueado

---

## 10. ARQUIVOS-CHAVE DO CÓDIGO REFERENCIADOS

### Backend Core
| Arquivo | Responsabilidade |
|---------|-----------------|
| `app/orchestrator/main_orchestrator.py` | Orquestração central (3 fases) + FairnessGuard L1-L2 |
| `app/orchestrator/intent_router.py` | Roteamento de intents por cascata de modelos |
| `libs/agents-core/lia_agents_core/react_agent_registry.py` | Registry de agentes ReAct |
| `libs/agents-core/lia_agents_core/langgraph_base.py` | Base LangGraph com checkpointer |

### Compliance (6 camadas)
| Arquivo | Responsabilidade |
|---------|-----------------|
| `app/shared/compliance/fairness_guard.py` | FairnessGuard (3 camadas, ~350 patterns, 13 categorias) |
| `app/shared/pii_masking.py` | PII Masking (4 camadas, Presidio opt-in) |
| `app/shared/compliance/audit_service.py` | Audit Trail (SOX-compliant, 730-1825d retention, human override) |
| `app/shared/compliance/fact_checker.py` | Fact-Checker (salary, count, %, date + V5 granulares) |
| `app/services/policy_engine_service.py` | Policy Engine + Rate Limiting + Escalation + Sector Rules |
| `app/api/v1/lgpd.py` | LGPD endpoints (consent, DSR, anonymize) |

### Inteligência (11 camadas)
| Arquivo | Responsabilidade |
|---------|-----------------|
| `app/shared/learning/learning_loop_service.py` | Learning Loop (silent capture + FairnessGuard F1-02) |
| `app/shared/learning/ab_testing_service.py` | A/B Testing (z-score, p-value, 95% CI) |
| `app/services/routing_learning_service.py` | Routing Adaptativo (0.8x-1.2x confidence multipliers) |
| `app/shared/learning/template_learning_service.py` | Template Learning (auto after 3 similar jobs) |
| `app/services/calibration_service.py` | Calibration (explicit + implicit feedback → weight suggestions) |
| `app/domains/cv_screening/services/score_normalization_service.py` | Score Normalization (difficulty coefficient) |
| `app/services/ml/outcome_predictor.py` | Predictive Analytics (time-to-fill, optimal salary, skill success) |
| `app/services/model_drift_service.py` | Model Drift (4 dimensions: score, approval, cost, latency) |
| `app/shared/memory/conversation_state.py` | Conversation Memory (entity tracking, pronoun resolution) |
| `app/shared/intelligence/semantic_search_service.py` | Semantic Search (Gemini 768-dim, Redis cache, domain expansion) |
| `app/services/voice_service.py` | Voice Analysis (STT: Deepgram/Whisper, TTS: OpenAI) |
| `app/shared/intelligence/embedding_service.py` | Embedding Service (Gemini text-embedding-004, 768-dim) |
| `libs/agents-core/lia_agents_core/long_term_memory.py` | Long-Term Memory (episodes + LLM compression after 30d) |
| `app/shared/learning/learning_snapshot_service.py` | Learning Snapshot (pre-learning rollback points, Z2-01) |

### Communication
| Arquivo | Responsabilidade |
|---------|-----------------|
| `app/domains/communication/services/email_service.py` | Email (Resend/SendGrid) |
| `app/domains/communication/services/whatsapp_service.py` | WhatsApp (Twilio) |
| `app/domains/cv_screening/services/wsi_service.py` | WSI (CBI/Bloom/Dreyfus/Big Five) |
| `app/domains/ats_integration/` | ATS (Gupy/Pandapé/Merge/StackOne) |
| `app/domains/interview_scheduling/services/scheduling_service.py` | Scheduling (ICS + Teams) |

---

## 11. RESPOSTAS ÀS PERGUNTAS DO USUÁRIO

### "Isso faz sentido?"
**Sim.** A sequência Login → Editar Vaga → Roteiro WSI → Buscar → Aprovar → Contato → Triagem → Gate 2 → Agendar/Feedback é o caminho natural de recrutamento assistido por IA. O backend suporta esse fluxo com 8 agentes, 30+ tools, 6 compliance layers e 11 intelligence layers.

### "Falta informação?"
**Sim, faltam 7 gaps estruturais, 7 gaps de compliance e 6 gaps de inteligência** detalhados na seção 6. Os mais críticos: Scheduler, Chat Web Público, Consentimento LGPD, Credenciais de produção.

### "Faz sentido o mapa por camada?"
**Absolutamente.** A matriz da seção 4 mostra que a maioria das intelligence layers está "implementada mas não integrada". O diferencial competitivo da plataforma está justamente nessas 11 camadas — Learning Loop silencioso, A/B Testing com significância estatística, Routing Adaptativo, Score Normalization, Predictive Analytics, e Voice Analysis são capacidades que concorrentes não têm.

### "Prioridade de ativação?"
1. **Compliance first:** FairnessGuard em todos os pontos + Audit Trail completo (sem isso não vai para produção)
2. **Intelligence core:** Learning Loop já ativo + Calibration + Score Normalization (já funcionam, só precisam de validação)
3. **Intelligence advanced:** A/B Testing (criar primeiros testes) + Predictive Analytics (integrar na UI) + Voice Analysis (integrar na triagem web)
