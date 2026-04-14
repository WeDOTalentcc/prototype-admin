# HANDOFF — Execução Wave 0 (Ajustes)

## CONEXÃO REPLIT
```
ssh -i ~/.ssh/replit -p 22 82791557-0b63-4f8d-baed-bba54c6e1fdf@82791557-0b63-4f8d-baed-bba54c6e1fdf-00-32kinhguzv9ak.picard.replit.dev
```

## ARQUITETURA
- **Backend oficial:** `ats-api-copia` (Rails 7.1) — GitHub org `WeDOTalentcc/ats-api-copia` — deploy GCP
- **IA + Frontend:** `lia-agent-system` + `plataforma-lia` — Replit
- **Integração:** Rails↔Python via RabbitMQ (configurando no GCP). Redis/RabbitMQ no GCP.
- **Dois bancos PostgreSQL independentes** sem sync enquanto RAILS_API_URL não configurado

## GITHUB
- Autenticado como `wedocc2026`, acesso admin ao `WeDOTalentcc/ats-api-copia`
- `gh auth status` confirma: gist, read:org, repo scopes

## AUDITORIA COMPLETA — 39 Protocolos
Todos salvos em `/home/runner/workspace/docs/audit/` no Replit:

```
docs/audit/
  ├── COMPLETENESS_VERIFICATION.md          (P15)
  ├── fase1-reconhecimento/                 (P01-P03: 3 docs)
  ├── fase2-diagnostico/                    (P04-P10: 7 docs)
  ├── fase3-qualitativo/                    (P11-P14: 4 docs)
  ├── fase4-integracao/                     (P16-P20: 5 docs)
  ├── fase5-arquitetura/                    (P21-P26: 6 docs)
  │   ├── TARGET_ARCHITECTURE.md
  │   ├── CANONICAL_SOURCES_SPEC.md
  │   ├── AGENT_CONVERGENCE_PLAN.md
  │   ├── EVAL_FRAMEWORK_SPEC.md
  │   ├── PROMPT_TEMPLATE.md
  │   └── OBSERVABILITY_SPEC.md
  ├── fase6-tdd/                            (P27-P31: 5 docs)
  │   ├── ARCHITECTURE_FITNESS_BASELINE.md   (8/12 pass)
  │   ├── CONTRACT_TEST_BASELINE.md          (11/17 pass)
  │   ├── GOLDEN_BASELINE.md                 (70% estimado)
  │   ├── INVARIANT_BASELINE.md              (12/20 pass)
  │   └── VERTICAL_INTEGRATION_BASELINE.md   (82% conectividade)
  ├── fase7-execucao/                       (P32: 1 doc)
  │   └── MIGRATION_PLAN.md                  (6 Waves, 12 Sprints)
  └── plataforma/                           (PX01-PX07: 7 docs)
      ├── PLATFORM_HEALTH_AUDIT.md           (50/100)
      ├── ROUTES_ENDPOINTS_AUDIT.md
      ├── INTEGRATIONS_INFRASTRUCTURE_AUDIT.md
      ├── DATABASE_SCHEMA_INTEGRITY_AUDIT.md (schema.rb 67 migrations atras)
      ├── FRONTEND_HEALTH_AUDIT.md           (3.6/5)
      ├── DEVOPS_SECURITY_AUDIT.md           (3.2/5)
      └── PLATFORM_DEPENDENCY_MAP.md         (15 bloqueadores)
```

Backup local: `/Users/paulomoraes/Documents/Python/pmoraes/audit/`

## SCORES CHAVE
| Metrica | Score |
|---------|-------|
| Platform Health | 50/100 |
| AI Security | 4.2/10 |
| ML Maturity | 1.4/5 |
| Frontend Health | 3.6/5 |
| DevOps Security | 3.2/5 |
| Agent Convergence | 85% |
| Vertical Connectivity | 82% |
| Fitness Functions | 8/12 (67%) |
| Contract Tests | 11/17 (65%) |
| Invariants | 12/20 (60%) |
| Golden Scenarios | 70% estimado |

## TOP 15 ACHADOS P0 (BLOQUEADORES)
1. candidates sem account_id (LGPD violation)
2. CORS hardcoded localhost no Rails
3. RAILS_API_URL não configurado (dois bancos divergentes)
4. JWT secrets divergentes Python/Rails
5. MagicLinksController não roteado (404)
6. OnboardingController não roteado (404)
7. 6 LiaEventsWorker handlers são stubs
8. Email 100% simulado (MAILGUN_API_KEY ausente)
9. WhatsApp simulado (TWILIO desabilitado)
10. schema.rb 67 migrations atras
11. API Key Atlassian em texto claro no arquivo `replit`
12. JobImportWorker hardcoda account_id: 1
13. Proxy onboarding aponta para localhost:3000
14. WSManager singleton in-memory (multi-worker)
15. Zero CI/CD para Python e Frontend

## WAVE 0 — Sprint 0 (PRÓXIMO PASSO) — ~4 horas de config

| # | Task | Arquivo | Esforço |
|---|------|---------|---------|
| 0.1 | Revogar API Key Atlassian | `replit` + admin.atlassian.com | 10 min |
| 0.2 | Fix CORS Rails → ENV.fetch | `ats-api-copia/config/initializers/cors.rb` | 30 min |
| 0.3 | Configurar RAILS_API_URL | Replit Secrets | 15 min |
| 0.4 | Compartilhar JWT SECRET_KEY | Replit Secrets + Rails credentials | 15 min |
| 0.5 | Rotear MagicLinksController | `ats-api-copia/config/routes.rb` | 15 min |
| 0.6 | Rotear OnboardingController | `ats-api-copia/config/routes.rb` | 15 min |
| 0.7 | Configurar MAILGUN_API_KEY | Replit Secrets | 10 min |
| 0.8 | Configurar TWILIO + ENVIRONMENT | Replit Secrets | 10 min |
| 0.9 | Fix JobImportWorker account_id | `ats-api-copia/app/workers/job_import_worker.rb:35-36` | 30 min |
| 0.10 | Fix proxy onboarding fallback | `plataforma-lia/src/app/api/backend-proxy/onboarding/[...path]/route.ts` | 30 min |
| 0.11 | Configurar SENTRY_DSN | Replit Secrets + GCP | 15 min |
| 0.12 | Mover DEV_AUTO_LOGIN para .env | `docker-compose.yml` → `.env` | 5 min |

## WAVE 0 — Sprint 1 (APÓS Sprint 0) — 3-5 dias

| # | Task | Esforço |
|---|------|---------|
| 1.1 | Migration candidates.account_id | M |
| 1.2 | Backfill account_id existentes | M |
| 1.3 | rails db:migrate && db:schema:dump no GCP | M |
| 1.4 | Fix ResourceLoader tenant scope | S |
| 1.5 | Fix SearchRenderer tenant scope | S |
| 1.6 | Add index on users.email | S |
| 1.7 | Configurar Sentry no Rails | S |

## WAVE 0 — Sprint 2 (APÓS Sprint 1) — 3-5 dias

| # | Task | Esforço |
|---|------|---------|
| 2.1 | Implementar 6 handlers LiaEventsWorker | M |
| 2.2 | WSManager → Redis Pub/Sub | M |
| 2.3 | Bunny connection pool | S |
| 2.4 | OTEL endpoint configurado | S |

## INSTRUÇÃO PARA PRÓXIMA SESSÃO
Antes de cada fix:
1. Leia o documento de audit relevante no Replit
2. Leia o arquivo a editar
3. Faça a edição
4. Commit atômico com mensagem descritiva
5. Marque como done

Para tasks de Rails (0.2, 0.5, 0.6, 0.9): clonar `WeDOTalentcc/ats-api-copia`, editar, push.
Para tasks de config (0.3, 0.4, 0.7, 0.8, 0.11): configurar Replit Secrets via Replit UI.
Para tasks de frontend (0.10): editar no Replit via SSH.
