# DEVOPS_SECURITY_AUDIT.md — Auditoria de DevOps e Seguranca Web
**Protocolo:** PX06  
**Data:** 2026-04-14  
**Auditor:** Claude Opus 4.6  
**Repositorios auditados:**
- Frontend: `plataforma-lia/` (Next.js 15, Replit)
- IA Layer: `lia-agent-system/` (FastAPI, Replit)
- Backend CRUD: `ats-api-copia/` (Rails 7.1, GitHub wedocc2026/wedotalentcc, deploy GCP)
- Contexto: Frontend + IA no Replit, Backend Rails no GCP. RabbitMQ/Redis sendo configurados no GCP.

**Depende de:** P01 (PLATFORM_MAP), P10 (AI_SECURITY_AUDIT)  
**Alimenta:** P32

---

## SCORE GERAL: 3.2 / 5

| Dimensao | Score | Peso |
|----------|-------|------|
| Secrets em Risco | 2.5/5 | 25% |
| Dependencias Vulneraveis | 3.0/5 | 15% |
| Autenticacao e Sessao | 4.0/5 | 25% |
| Headers de Seguranca | 4.0/5 | 10% |
| CI/CD | 2.5/5 | 15% |
| Logging e Monitoring | 3.5/5 | 10% |

---

## 1. SECRETS EM RISCO

### 1.1 ACHADO CRITICO: API Key Atlassian em Texto Claro

**Arquivo:** `/home/runner/workspace/replit` (linha 1-6)
**Conteudo exposto:**
- Organization ID da Atlassian
- API Key da Atlassian (token completo ATCTT3xFfGN0...)
- Email tech@wedotalent.cc

**Severidade:** CRITICA — este arquivo esta no workspace root, potencialmente acessivel. A API key da Atlassian permite acesso ao Jira/Confluence da organizacao.

**Acao imediata:** Revogar a API key no https://admin.atlassian.com e gerar nova via Replit Secrets.

### 1.2 Inventario de Secrets Referenciados

#### Python (lia-agent-system) — libs/config/lia_config/config.py

| Secret | Default | Seguro? | Risco |
|--------|---------|---------|-------|
| `SECRET_KEY` | "change-this-in-production" | NAO em dev, OK em prod (validator bloqueia) | MEDIO — validator impede deploy prod com default |
| `DATABASE_URL` | postgresql+asyncpg://lia_user:lia_password@localhost/lia_db | NAO | ALTO — credenciais default conhecidas |
| `REDIS_URL` | redis://localhost:6379/0 | OK (sem auth local) | BAIXO |
| `RABBITMQ_URL` | amqp://guest:guest@localhost:5672/ | NAO | MEDIO — credenciais guest/guest |
| `ANTHROPIC_API_KEY` | None (Optional) | OK | OK — None nao expoe |
| `OPENAI_API_KEY` | None (Optional) | OK | OK |
| `AI_INTEGRATIONS_*_API_KEY` | None (Optional) | OK | OK — via Replit AI Integrations |
| `WORKOS_API_KEY` | None (Optional) | OK | OK |
| `WORKOS_CLIENT_ID` | None (Optional) | OK | OK |
| `WORKOS_WEBHOOK_SECRET` | None (Optional) | OK | OK |
| `AZURE_CLIENT_SECRET` | None (Optional) | OK | OK |
| `PEARCH_API_KEY` | None (Optional) | OK | OK |
| `TWILIO_AUTH_TOKEN` | None (Optional) | OK | OK |
| `MAILGUN_API_KEY` | None (Optional) | OK | OK |
| `HUBSPOT_API_KEY` | None (Optional) | OK | OK |
| `STRIPE_SECRET_KEY` | None (Optional) | OK | OK |
| `STRIPE_WEBHOOK_SECRET` | None (Optional) | OK | OK |
| `S3_ACCESS_KEY` | None (Optional) | OK | OK |
| `S3_SECRET_KEY` | None (Optional) | OK | OK |
| `DOPPLER_TOKEN` | None (Optional) | OK | OK |
| `ADMIN_API_KEY` | None (Optional) | OK | OK |
| `LANGCHAIN_API_KEY` | None (Optional) | OK | OK |

**Padrao positivo:** A grande maioria dos secrets usa `Optional[str] = None` — ausencia nao quebra startup, apenas desabilita a feature. Boa pratica.

#### Frontend (plataforma-lia) — .env.example

| Secret | Default | Seguro? | Risco |
|--------|---------|---------|-------|
| `SECRET_KEY` | "change-this-in-production" | NAO | MEDIO — usado para JWT |
| `WORKOS_API_KEY` | sk_xxxx (placeholder) | OK | OK |
| `WORKOS_SESSION_SECRET` | "uma-string-aleatoria..." | NAO | ALTO — se usado sem trocar, sessoes previssiveis |
| `INTERNAL_API_SECRET` | "token-interno-seguro-aleatorio" | NAO | MEDIO — se usado sem trocar |

#### Docker-compose (workspace root)

| Secret | Valor | Seguro? | Risco |
|--------|-------|---------|-------|
| `POSTGRES_PASSWORD` | lia_password | NAO | ALTO para prod — OK para dev local |
| `RABBITMQ_DEFAULT_PASS` | guest | NAO | MEDIO |
| `WORKOS_API_KEY` | dev_placeholder_key | OK (placeholder) | BAIXO |
| `DEV_AUTO_LOGIN_EMAIL` | giovanni@wedotalent.com | EXPOSTO | MEDIO — email real em config |
| `DEV_AUTO_LOGIN_PASSWORD` | demo123 | EXPOSTO | ALTO — se acessivel em prod |

### 1.3 Secrets com Fallback Aleatorio

**Nenhum encontrado.** Nenhum secret usa `secrets.token_hex()` ou `uuid4()` como default. Isso e bom — defaults sao fixos ou None, nao invalidam tokens entre restarts.

### 1.4 Validator de Producao

`Settings.validate_secret_key()` bloqueia startup se `APP_ENV=production` e `SECRET_KEY` e o default. **Boa pratica implementada.**

---

## 2. DEPENDENCIAS VULNERAVEIS

### 2.1 Python (lia-agent-system)

**Nao foi possivel rodar `pip audit` remotamente** (requer virtual env ativo). Analise baseada em versoes conhecidas do pyproject.toml:

| Dependencia | Risco | Notas |
|-------------|-------|-------|
| FastAPI | Baixo | Atualizado regularmente |
| LangChain/LangGraph | Medio | Ecossistema rapido, patches frequentes |
| Pydantic | Baixo | v2 estavel |
| SQLAlchemy | Baixo | Asyncpg driver atualizado |
| sentry-sdk | Baixo | Integracao instalada |

**Recomendacao:** Configurar `pip audit` no CI (inexistente para Python atualmente).

### 2.2 Rails (ats-api-copia)

| Dependencia | Versao | Risco | Notas |
|-------------|--------|-------|-------|
| Rails | 7.1.0 | MEDIO | 7.1.0 e a release inicial — patches 7.1.x ja existem (7.1.5+). Atualizar. |
| Puma | >= 5.0 | Verificar | Version range amplo — pode estar em versao vulneravel |
| elasticsearch | sem pin | ALTO | Sem version pinning — pode puxar versao incompativel |
| Brakeman | OK | Dev only | Security scanner incluso |
| Sneakers (RabbitMQ) | sem pin | MEDIO | Sem version pinning |
| bcrypt | ~> 3.1.7 | OK | Seguro |
| JWT | sem pin | MEDIO | Sem version pinning |

**Brakeman** (security scanner) esta no Gemfile e roda no CI. **Ponto positivo.**

**Dependabot** configurado para bundler (daily) + github-actions (daily). **Ponto positivo.**

### 2.3 Frontend (plataforma-lia)

**Nao foi possivel rodar `npm audit` remotamente.** Recomendacao: adicionar ao CI.

---

## 3. AUTENTICACAO E SESSAO

### 3.1 Fluxo de Auth

```
Browser
  |
  |-- (1) Login form -> POST /api/v1/auth/login -> JWT access_token + refresh_token
  |-- (2) SSO -> WorkOS redirect -> callback -> JWT
  |-- (3) Magic link -> POST /api/auth/magic-link -> Rails (se configurado)
  |-- (4) Dev auto-login -> DEV_AUTO_LOGIN_EMAIL/PASSWORD (dev only)
  |
  |-- access_token armazenado em cookie httpOnly (lia_access_token)
  |-- refresh_token armazenado em cookie httpOnly (lia_refresh_token)
```

### 3.2 JWT

| Aspecto | Status | Detalhes |
|---------|--------|----------|
| **Algorithm** | HS256 | OK para single-service. RS256 recomendado quando Rails + Python compartilham tokens |
| **Expiracao** | 30 min (access), 7 dias (refresh) | OK |
| **Refresh** | Implementado | `proxyFetchWithRetry` auto-refresh no 401 |
| **Cookie httpOnly** | SIM | Previne XSS token theft |
| **Cookie secure** | SIM em prod | `secure: process.env.NODE_ENV === 'production'` |
| **Cookie sameSite** | lax | OK |
| **Token invalidacao** | PARCIAL | Logout limpa cookies, mas token ainda valido ate expirar (sem blacklist) |
| **Rails JWT secret** | `RAILS_JWT_SECRET_KEY` | Compartilhado para validar tokens cruzados |

### 3.3 AuthEnforcementMiddleware (Python)

| Aspecto | Status | Detalhes |
|---------|--------|----------|
| **Escopo** | Global | Middleware aplica a TODAS as rotas nao-publicas |
| **Tenant isolation** | SIM | Extrai company_id do JWT, injeta em ContextVar |
| **X-Company-ID forgery** | CORRIGIDO | Middleware NAO confia em header X-Company-ID — usa JWT |
| **Prompt injection guard** | SIM | Checa bodies de texto contra patterns de injecao |
| **PUBLIC_PATHS** | 25+ rotas | Auth, health, webhooks — adequado |

### 3.4 Rate Limiting

| Aspecto | Status | Detalhes |
|---------|--------|----------|
| **Middleware** | SIM | `RateLimitMiddleware` (rate_limiter.py) |
| **Login rate limit** | SIM | PolicyEngine com limites por tenant |
| **Per-tenant** | SIM | Usa company_id do JWT |
| **Storage** | Redis | Contadores em Redis com TTL |
| **Bypass** | Nenhum | Rate limiter aplica globalmente |

### 3.5 Brute Force Protection

| Cenario | Protegido? | Detalhes |
|---------|-----------|----------|
| Login JWT | PARCIAL | Rate limiting global, mas sem lockout apos N tentativas |
| Login SSO | SIM | WorkOS gerencia |
| API calls | SIM | Rate limiter per-tenant |
| WS connections | SIM | `WS_MAX_CONNECTIONS_PER_TENANT = 100` |

---

## 4. HEADERS DE SEGURANCA

(Documentado em detalhes no PX05. Resumo aqui.)

| Header | Frontend (Next.js) | Python (FastAPI) | Rails |
|--------|-------------------|------------------|-------|
| **CSP** | SIM (completo) | N/A (API only) | A verificar no GCP |
| **X-Frame-Options** | DENY (prod) | N/A | A verificar |
| **HSTS** | SIM (prod) | N/A | A verificar |
| **X-Content-Type-Options** | nosniff | N/A | A verificar |
| **Referrer-Policy** | strict-origin-when-cross-origin | N/A | A verificar |
| **Permissions-Policy** | camera=(), microphone=(self) | N/A | A verificar |
| **CORS** | Same-origin (BFF) | Configurado (3 origins) | A verificar |

**CORS no Python:** `CORS_ORIGINS: ["http://localhost:5000", "http://localhost:3000", "http://127.0.0.1:5000"]` — OK para dev. Em producao GCP, precisa incluir dominio real.

---

## 5. CI/CD

### 5.1 Rails (ats-api-copia) — GitHub Actions

| Job | O que faz | Status |
|-----|-----------|--------|
| `scan_ruby` | Brakeman security scan | OK |
| `scan_js` | importmap audit (JS deps) | OK |
| `lint` | RuboCop style enforcement | OK |

**FALTANDO no Rails CI:**
- Testes (RSpec esta no Gemfile mas NAO roda no CI)
- `bundle audit` (dependency vulnerability scan)
- Deploy automatico (manual)
- Database migration check

### 5.2 Python (lia-agent-system) — SEM CI/CD

**Nenhum GitHub Actions, nenhum CI configurado.** Deploy e via Replit (manual).

**FALTANDO:**
- Qualquer pipeline de CI
- Testes automatizados pre-deploy
- pip audit
- Linting (ruff/flake8)
- Security scan (bandit)
- Type check (mypy)

### 5.3 Frontend (plataforma-lia) — SEM CI/CD

**Nenhum GitHub Actions.** Build e via Replit.

**FALTANDO:**
- Pipeline de CI
- npm audit
- Lint check (ESLint ja esta configurado no projeto)
- Type check (TypeScript ja configurado)
- E2E tests

### 5.4 Resumo CI/CD

| Repo | CI | Tests | Security Scan | Auto-Deploy | Rollback |
|------|-----|-------|--------------|-------------|----------|
| ats-api-copia (Rails) | SIM (GitHub Actions) | NAO no CI | SIM (Brakeman) | NAO | NAO automatico |
| lia-agent-system (Python) | NAO | NAO | NAO | Manual (Replit) | NAO |
| plataforma-lia (Frontend) | NAO | NAO | NAO | Manual (Replit) | NAO |

---

## 6. LOGGING E MONITORING

### 6.1 Structured Logging (Python)

| Aspecto | Status | Detalhes |
|---------|--------|----------|
| **JSON formatter** | SIM | `JSONFormatter` em producao (logging_config.py) |
| **Request ID** | SIM | `RequestIdMiddleware` gera UUID por request |
| **User ID in logs** | SIM | Injetado via structured logging |
| **PII masking** | SIM | `PIIMaskingFilter` no handler — CPF, email, telefone |
| **Audit trail** | SIM | `AUDIT_TRAIL` structured log com JSON |
| **Dev vs Prod** | SIM | JSON em prod, human-readable em dev |

### 6.2 Error Tracking (Sentry)

| Aspecto | Status | Detalhes |
|---------|--------|----------|
| **Python** | SIM | `init_sentry()` com FastAPI + Starlette integrations |
| **Frontend** | SIM | `@sentry/nextjs` na error boundary |
| **PII scrubbing** | SIM | `_before_send` hook remove CPF, email, telefone antes de enviar |
| **DSN configurado?** | DEPENDE | `SENTRY_DSN` env var — se vazio, Sentry desativado graciosamente |
| **Degradacao graciosa** | SIM | Sem DSN ou sem SDK = warning no log, app continua |

### 6.3 Uptime Monitoring

| Aspecto | Status | Detalhes |
|---------|--------|----------|
| **Health endpoints** | SIM | `/health`, `/api/v1/health`, `/api/v1/health/performance`, `/api/v1/health/langgraph` |
| **Uptime monitor externo** | NAO CONFIRMADO | Sem evidencia de UptimeRobot, Pingdom, etc. |
| **Prometheus/Grafana** | NAO | Removidos (nenhum arquivo encontrado) |
| **OpenTelemetry** | CONFIGURADO | `OTEL_EXPORTER_OTLP_ENDPOINT` em settings, mas vazio por default |
| **Flower (Celery)** | SIM | Docker-compose inclui Flower em :5555 |
| **LangSmith** | CONFIGURADO | `LANGCHAIN_TRACING_V2` flag + API key — desabilitado por default |

### 6.4 Substituicao de Prometheus/Grafana

**Prometheus/Grafana NAO foram substituidos.** Foram removidos e nada tomou o lugar. OpenTelemetry esta configurado como settings mas `OTEL_EXPORTER_OTLP_ENDPOINT` esta vazio. Em producao GCP, precisa de:
- Cloud Monitoring (GCP native) ou
- OpenTelemetry -> Jaeger/Tempo ou
- Datadog/New Relic

---

## RECOMENDACOES PRIORIZADAS

### P0 URGENTE — Revogar API Key Atlassian
**O que:** Arquivo `/workspace/replit` contem API key da Atlassian em texto claro. Revogar IMEDIATAMENTE em admin.atlassian.com e recriar como Replit Secret.
**Impacto:** Acesso nao autorizado ao Jira/Confluence da organizacao
**Esforco:** S (10 min)

### P0 — Remover DEV_AUTO_LOGIN de Docker-compose
**O que:** `DEV_AUTO_LOGIN_EMAIL` e `DEV_AUTO_LOGIN_PASSWORD` nao devem estar em docker-compose.yml (pode ser commitado). Mover para .env (gitignored).
**Impacto:** Credenciais de dev expostas
**Esforco:** S (5 min)

### P0 — Atualizar Rails para 7.1.5+
**O que:** Rails 7.1.0 tem patches de seguranca pendentes. Atualizar para latest 7.1.x.
**Impacto:** CVEs conhecidos corrigidos
**Esforco:** S (bundle update rails)

### P1 — CI/CD para Python (lia-agent-system)
**O que:** Criar GitHub Actions com: lint (ruff), type check (mypy), tests (pytest), security (bandit), pip audit
**Impacto:** Previne regressoes e vulnerabilidades
**Esforco:** M (1-2 dias)

### P1 — CI/CD para Frontend (plataforma-lia)
**O que:** Criar GitHub Actions com: lint (ESLint), type check (tsc), npm audit, build check
**Impacto:** Qualidade e seguranca do frontend
**Esforco:** M (1-2 dias)

### P1 — Adicionar Testes ao CI do Rails
**O que:** RSpec esta no Gemfile mas NAO roda no CI. Adicionar job `test` com service containers (postgres, redis).
**Impacto:** Testes reais antes de merge
**Esforco:** M (meio dia)

### P1 — Configurar CORS para Producao
**O que:** `CORS_ORIGINS` inclui apenas localhost. Adicionar dominio real de producao.
**Impacto:** Frontend GCP consegue chamar API
**Esforco:** S (configuracao)

### P2 — Token Blacklist no Logout
**O que:** JWT continua valido apos logout ate expirar (30 min). Implementar blacklist em Redis.
**Impacto:** Seguranca de sessao
**Esforco:** M (1-2 dias)

### P2 — Ativar OpenTelemetry
**O que:** `OTEL_EXPORTER_OTLP_ENDPOINT` esta vazio. Configurar Jaeger ou GCP Cloud Trace.
**Impacto:** Observabilidade de traces distribuidos
**Esforco:** M (1 dia)

### P2 — Pin Versions no Gemfile
**O que:** elasticsearch, sneakers, jwt sem version pinning. Adicionar pins.
**Impacto:** Previne breaking changes inesperados
**Esforco:** S (30 min)

### P2 — Account Lockout apos N Tentativas
**O que:** Rate limiting existe, mas sem lockout temporario apos ex: 5 tentativas de login falhadas.
**Impacto:** Protecao contra brute force direcionado
**Esforco:** M (1 dia)

---

## RESUMO EXECUTIVO

### O que funciona muito bem
1. **Auth chain completa** — JWT + WorkOS SSO + refresh automatico + httpOnly cookies
2. **AuthEnforcementMiddleware global** — tenant isolation via JWT, nao confia em headers forjados
3. **Prompt injection guard** — middleware checa todos os bodies contra patterns de injecao
4. **Rate limiting per-tenant** — Redis-backed, aplicado globalmente
5. **Structured logging + PII masking** — JSON logs em prod, CPF/email/telefone mascarados
6. **Sentry com PII scrubbing** — before_send hook remove PII antes de enviar
7. **Brakeman no CI Rails** — security scan automatico em PRs
8. **Dependabot ativo** — daily updates para Rails deps
9. **SECRET_KEY validator** — bloqueia startup em prod com default inseguro

### O que esta quebrado/faltando
1. **API Key Atlassian em texto claro** no arquivo `replit` (CRITICO)
2. **Zero CI/CD para Python e Frontend** — deploy manual sem checks
3. **Rails 7.1.0 desatualizado** — patches de seguranca pendentes
4. **Prometheus/Grafana removidos sem substituto** — OpenTelemetry configurado mas vazio
5. **Token JWT sem blacklist** — valido ate expirar apos logout
6. **CORS hardcoded para localhost** — precisa dominio real para GCP
7. **DEV_AUTO_LOGIN em docker-compose** — credenciais expostas

### Metafora
A seguranca da plataforma e como um forte medieval: muralhas solidas (auth middleware, rate limiting, Sentry), ponte levadica funcional (JWT + refresh + httpOnly), guardas nas torres (Brakeman, PII masking). Mas alguem deixou a chave do escritorio do rei pendurada na porta da frente (API key no arquivo `replit`), e metade do exercito nao tem uniforme (sem CI/CD para Python/Frontend).

### Score Final: 3.2/5
Boa seguranca de aplicacao, gaps serios em CI/CD e secrets management.
