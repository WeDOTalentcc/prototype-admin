# Threat Model

## Project Overview

Plataforma LIA is a multi-tenant B2B recruitment and candidate assessment platform. The production backend is primarily `lia-agent-system`, a Python FastAPI service using SQLAlchemy/AsyncPG, PostgreSQL, Redis/RabbitMQ/Celery, LangGraph/LangChain AI agents, WorkOS SSO/JWT authentication, and many external integrations. The legacy/system-of-record backend is `ats_api`, a Ruby on Rails 7 API using JWT authentication, Apartment schema-based tenancy, Sidekiq, Redis, and Elasticsearch. The platform processes recruiter accounts, tenant configuration, job requisitions, candidate profiles, WSI assessments, interview transcripts, messaging events, external ATS data, and LLM provider credentials.

Production assumptions for scans: mockup sandboxes and copied backups are not deployed; production uses TLS provided by the platform; production has `NODE_ENV=production`; the current deployment is private, so findings should prioritize authenticated users, invited users, public-link holders, and integration/webhook callers rather than broad anonymous internet access.
In `lia-agent-system`, dependencies named `get_current_user_or_demo` only fall back to the demo user in development. In production they require real authentication and should be analyzed as authenticated-user surfaces, not anonymous ones.

## Assets

- **User accounts and sessions** -- WorkOS/Rails JWTs, refresh tokens, password reset and invitation tokens, MFA codes, and service-to-service tokens. Compromise enables account takeover or cross-service impersonation.
- **Tenant data** -- company settings, hiring policies, jobs, pipelines, candidates, applications, WSI scores, interview notes, audit logs, and billing/usage records. Tenant isolation failures expose one customer's hiring data to another.
- **Candidate personal and sensitive data** -- names, emails, phone numbers, resumes/CVs, employment history, compensation, interview transcripts, assessment answers, bias/fairness metadata, consent and LGPD data-subject request records.
- **AI and integration secrets** -- LLM provider keys, WorkOS secrets, Rails shared JWT secret, database URLs, Redis/RabbitMQ credentials, Microsoft/Google/Twilio/Mailgun/Stripe/Gupy/Pandapé/Merge/Apify keys, and webhook signing secrets.
- **Business-critical automation** -- AI tool execution, candidate stage transitions, sourcing/enrichment flows, billing/credits, webhooks, and communication dispatch. Tampering here can cause unauthorized candidate movement, messages, charges, or data export.

## Trust Boundaries

- **Browser/client to FastAPI and Rails APIs** -- every request from the frontend or external client is untrusted. Protected endpoints must authenticate and authorize server-side, not trust client-provided company IDs, roles, prices, or workflow decisions.
- **Unauthenticated/public routes to internal services** -- health checks, auth flows, password resets, setup tokens, candidate/public job endpoints, tracking pixels, OAuth callbacks, and webhooks cross from the public internet into production systems. They need signed tokens, scoped identifiers, replay protection, rate limits, and minimal responses.
- **FastAPI to PostgreSQL/Redis/RabbitMQ/Celery** -- SQL, cache, queue, and background jobs carry tenant-scoped data. Queries must be parameterized and filtered by company/tenant; queued jobs must preserve tenant context.
- **Rails to PostgreSQL/Apartment tenants** -- Rails controllers switch tenant schemas based on authenticated account context. Any route that skips or misuses `authorize_request` risks cross-tenant data exposure.
- **FastAPI to Rails cross-service trust** -- `lia-agent-system` accepts locally signed JWTs and Rails JWTs. Shared-secret configuration, token claims, and `/v1/me` lookups must prevent forged roles or company IDs.
- **AI agent/tool boundary** -- recruiter/candidate text and LLM output can trigger tool calls. Tool execution must enforce authentication, tenant context, allowlisted tools, prompt-injection defenses, bounded iterations, audit logging, and server-side authorization for state-changing actions.
- **Server to external services** -- WorkOS, Microsoft Graph/Teams, Google Calendar, Twilio, Mailgun, Stripe, Gupy, Pandapé, Merge.dev, Apify/Pearch, Sentry, and LLM providers receive data or callbacks. Outbound requests must avoid SSRF, protect secrets, validate webhook signatures, and avoid unnecessary PII disclosure.
- **File/upload and document-processing boundary** -- resumes, job descriptions, transcripts, and attachments are attacker-controlled files/text. They require size/type validation, safe storage paths, malware/content checks where applicable, and PII-conscious logging.

## Scan Anchors

- **FastAPI entry point:** `lia-agent-system/app/main.py`; global auth and public route scope in `lia-agent-system/app/middleware/auth_enforcement.py`; config defaults in `lia-agent-system/libs/config/lia_config/config.py`.
- **FastAPI route surfaces:** `lia-agent-system/app/api/v1/`, `lia-agent-system/app/api/public/`, `lia-agent-system/app/api/orchestrator_routes.py`, webhook files (`*webhook*.py`), candidate/job/WSI/calendar/billing/admin routes, `/external-webhooks/*`, WorkOS routes in `lia-agent-system/app/api/v1/workos.py`, and WebSocket/SSE chat routes.
- **Outbound URL and fetch surfaces:** routes and services that accept recruiter-controlled URLs or trigger server-side HTTP fetches, especially `lia-agent-system/app/api/v1/integrations.py`, `lia-agent-system/app/api/v1/company_culture.py`, `lia-agent-system/app/api/v1/job_status_webhooks.py`, webhook schemas, and the canonical validator `lia-agent-system/app/shared/security/url_validator.py`.
- **AI tool surfaces:** `lia-agent-system/app/tools/`, `lia-agent-system/app/domains/*/tools/`, `lia-agent-system/app/domains/*/agents/*tool_registry*.py`, and `lia-agent-system/app/domains/*/agents/*graph*.py`.
- **Rails entry point and routes:** `ats_api/config.ru`, `ats_api/config/routes.rb`, `ats_api/app/controllers/concerns/authenticable.rb`, and controllers under `ats_api/app/controllers/v1/`.
- **High-risk public Rails surfaces:** sessions/MFA, WorkOS, setup tokens, password resets, tracking, public jobs/applies, public interview links, agent token bootstrap/exchange routes, webhooks, Sidekiq mount, and ActionCable mount.
- **Dev-only or normally out of production scope:** `artifacts/mockup-sandbox/`, `ats-api-copia/`, `onboarding-patches/`, `lia-agent-system/eval/`, `lia-agent-system/tests-eval/`, `.local/`, `local/tasks/`, root one-off scripts unless production deployment explicitly runs them, and generated caches/logs.

## Threat Categories

### Spoofing

Attackers may try to forge JWTs, replay setup/password/MFA tokens, spoof webhook providers, or bypass public-route authentication. The platform must reject default or weak signing keys in production, validate JWT type/issuer/expiry where applicable, verify webhook signatures, rate-limit auth flows, and never grant role or tenant context from unsigned client input.

### Tampering

Recruiters, candidates, integrations, and LLM outputs can attempt unauthorized changes to candidate stages, job status, hiring policy, billing state, or tenant settings. The API must enforce server-side authorization and company scoping on every state-changing endpoint and tool, use parameterized SQL, validate request bodies, and record audit trails for sensitive actions.

### Repudiation

The platform makes consequential hiring decisions and automated communications. Sensitive actions such as candidate movement, WSI scoring, fairness overrides, approvals, consent changes, billing changes, and AI tool execution must have durable audit logs with actor, tenant, timestamp, action, and decision context.

### Information Disclosure

The application holds high-volume candidate PII and tenant business data. Endpoints, logs, errors, traces, prompts, LLM calls, exports, and public links must only disclose the minimum necessary data. Cross-tenant query bugs, verbose auth errors, exposed OpenAPI/debug information, PII in logs, and public token enumeration are key risks.

### Denial of Service

Public auth, webhook, upload, chat/LLM, search, enrichment, and export endpoints can consume significant CPU, database, queue, or third-party API budget. The services must enforce request/body/file limits, rate limits that remain effective across instances, bounded LLM/tool loops, external-call timeouts, and queue backpressure.

### Elevation of Privilege

Users may attempt to reach admin endpoints, use AI tools outside their role, inject different `company_id` values, abuse setup/service tokens, or manipulate Rails/FastAPI cross-service trust. Admin and service-only routes must require explicit server-side role/service checks, and all downstream repositories/services must preserve tenant context rather than trusting frontend filters.
