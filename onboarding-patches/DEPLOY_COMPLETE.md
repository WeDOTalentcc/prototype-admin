# Deploy Guide — Onboarding LIA Conversacional (Completo)

## Estrutura de arquivos

```
onboarding-patches/
├── DEPLOY_FASE1.md                                  ← Guia Fase 1
├── DEPLOY_COMPLETE.md                               ← Este guia (tudo)
│
├── rails/
│   ├── migrations/
│   │   ├── 20250716000010_add_onboarding_to_users_and_accounts.rb
│   │   ├── 20250716000011_create_onboarding_sessions.rb
│   │   ├── 20250716000012_create_magic_links.rb
│   │   └── 20250716000013_create_onboarding_messages.rb
│   ├── models/
│   │   ├── onboarding_session.rb
│   │   ├── magic_link.rb
│   │   ├── onboarding_message.rb
│   │   └── user_onboarding_extension.rb            ← Patch para User model
│   ├── controllers/
│   │   ├── onboarding_controller.rb                ← v1/users/onboarding
│   │   └── magic_links_controller.rb               ← v1/auth/magic_links
│   ├── services/
│   │   ├── magic_link_service.rb
│   │   └── onboarding_event_publisher.rb
│   ├── mailers/
│   │   └── onboarding_mailer.rb
│   ├── views/onboarding_mailer/
│   │   └── welcome_email.html.erb
│   └── routes_patch.rb
│
├── fastapi/
│   ├── migrations/
│   │   └── 059_create_onboarding_tables.py
│   ├── services/
│   │   ├── onboarding_orchestrator.py              ← FSM principal (10 states)
│   │   ├── onboarding_prompts.py                   ← Prompts LIA (WA + Web)
│   │   ├── onboarding_consumer.py                  ← RabbitMQ consumer
│   │   ├── whatsapp_client.py                      ← Twilio WhatsApp API
│   │   └── whatsapp_flows/
│   │       └── onboarding_flow_v1.json             ← 4-tela Flow definition
│   └── api/
│       ├── onboarding_api.py                       ← FastAPI endpoints
│       └── whatsapp_webhook.py                     ← Twilio webhooks
│
└── frontend/
    ├── OnboardingChatPage.tsx                       ← Fullscreen onboarding wrapper
    ├── useOnboardingFlow.ts                         ← First-login detection hook
    ├── ChatImageMessage.tsx                         ← Screenshot inline no chat
    ├── OnboardingSettingsToggle.tsx                 ← Toggle on/off em Settings
    ├── tour/
    │   ├── TourSpotlight.tsx                        ← Overlay highlight
    │   ├── TourAutoFill.tsx                         ← Typing animation hook
    │   ├── TourController.tsx                       ← Orchestrador de steps
    │   ├── useTourMode.ts                           ← Tour state + persistence
    │   └── tour-steps.ts                            ← Step definitions
    └── proxy-routes/
        ├── onboarding/route.ts                      ← Proxy Rails + FastAPI
        └── auth/magic-link/route.ts                 ← Magic link verify + redirect
```

**Total: 31 arquivos**

---

## Ordem de deploy

### 1. Rails (ats-api-copia)

```bash
# Migrations
cp onboarding-patches/rails/migrations/*.rb db/migrate/
rails db:migrate

# Models
cp onboarding-patches/rails/models/onboarding_session.rb app/models/
cp onboarding-patches/rails/models/magic_link.rb app/models/
cp onboarding-patches/rails/models/onboarding_message.rb app/models/
# Patch User model (ver user_onboarding_extension.rb)

# Services
cp onboarding-patches/rails/services/*.rb app/services/

# Controllers
cp onboarding-patches/rails/controllers/onboarding_controller.rb app/controllers/v1/users/
mkdir -p app/controllers/v1/auth
cp onboarding-patches/rails/controllers/magic_links_controller.rb app/controllers/v1/auth/

# Mailer + Views
cp onboarding-patches/rails/mailers/onboarding_mailer.rb app/mailers/
mkdir -p app/views/onboarding_mailer
cp onboarding-patches/rails/views/onboarding_mailer/*.erb app/views/onboarding_mailer/

# Routes (manual — ver routes_patch.rb)
```

### 2. FastAPI (Replit: lia-agent-system)

```bash
# Migration
cp onboarding-patches/fastapi/migrations/059_create_onboarding_tables.py alembic/versions/
alembic upgrade head

# Services
cp onboarding-patches/fastapi/services/onboarding_orchestrator.py app/services/
cp onboarding-patches/fastapi/services/onboarding_prompts.py app/services/
cp onboarding-patches/fastapi/services/onboarding_consumer.py app/services/
cp onboarding-patches/fastapi/services/whatsapp_client.py app/services/
mkdir -p app/services/whatsapp_flows
cp onboarding-patches/fastapi/services/whatsapp_flows/*.json app/services/whatsapp_flows/

# API endpoints
cp onboarding-patches/fastapi/api/onboarding_api.py app/api/v1/onboarding.py
cp onboarding-patches/fastapi/api/whatsapp_webhook.py app/api/v1/whatsapp_webhook.py

# Register routers in main.py:
#   from app.api.v1.onboarding import router as onboarding_router
#   from app.api.v1.whatsapp_webhook import router as whatsapp_router
#   app.include_router(onboarding_router)
#   app.include_router(whatsapp_router)

# Start consumer (add to startup):
#   from app.services.onboarding_consumer import start_onboarding_consumer
#   asyncio.create_task(start_onboarding_consumer())
```

### 3. Frontend (Replit: plataforma-lia)

```bash
# Tour Engine
mkdir -p src/components/onboarding/tour
cp onboarding-patches/frontend/tour/*.tsx src/components/onboarding/tour/
cp onboarding-patches/frontend/tour/*.ts src/components/onboarding/tour/

# Onboarding page + hooks
cp onboarding-patches/frontend/OnboardingChatPage.tsx src/components/onboarding/
cp onboarding-patches/frontend/useOnboardingFlow.ts src/components/onboarding/
cp onboarding-patches/frontend/ChatImageMessage.tsx src/components/unified-chat/
cp onboarding-patches/frontend/OnboardingSettingsToggle.tsx src/components/settings/

# Proxy routes
mkdir -p src/app/api/backend-proxy/onboarding
cp onboarding-patches/frontend/proxy-routes/onboarding/route.ts src/app/api/backend-proxy/onboarding/[...path]/route.ts
mkdir -p src/app/api/auth/magic-link
cp onboarding-patches/frontend/proxy-routes/auth/magic-link/route.ts src/app/api/auth/magic-link/route.ts

# Onboarding page (create)
mkdir -p src/app/\(dashboard\)/onboarding
# Create page.tsx that imports OnboardingChatPage
```

### 4. Env vars

```bash
# FastAPI
TWILIO_ACCOUNT_SID=xxx
TWILIO_AUTH_TOKEN=xxx
LIA_WHATSAPP_NUMBER=+5511xxxxxxxxx
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
FRONTEND_URL=https://app.wedotalent.com

# Rails
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# Frontend
RAILS_BACKEND_URL=http://rails-api:3000
BACKEND_URL=http://localhost:8000
```

---

## Checklist final

### Rails
- [ ] 4 migrations executadas
- [ ] 3 models criados
- [ ] User model patcheado (associations + methods + scopes)
- [ ] Account model tem onboarding_lia_enabled
- [ ] MagicLinkService funciona (generate + verify)
- [ ] OnboardingMailer envia email
- [ ] Controllers respondem (invite, verify, status, progress, consent)
- [ ] Routes adicionadas
- [ ] RabbitMQ publisher funciona

### FastAPI
- [ ] Migration 059 executada
- [ ] OnboardingOrchestrator funciona (start, handle_whatsapp, handle_web)
- [ ] WhatsApp client envia mensagens (Twilio)
- [ ] Webhooks recebem mensagens
- [ ] RabbitMQ consumer escuta eventos
- [ ] Routers registrados no main.py

### Frontend
- [ ] Tour Engine funciona (Spotlight + AutoFill + Controller)
- [ ] OnboardingChatPage renderiza fullscreen
- [ ] useOnboardingFlow detecta first-login
- [ ] ChatImageMessage renderiza screenshots no chat
- [ ] Settings toggle funciona
- [ ] Proxy routes encaminham para Rails + FastAPI
- [ ] Magic link redirect funciona (/auth/magic-link → /onboarding)

### E2E
- [ ] Admin convida recrutador → email + WhatsApp enviados
- [ ] WhatsApp: LIA se apresenta → user responde → Flow → dados coletados
- [ ] Magic link → browser abre logado → redirect /onboarding
- [ ] Tour: Pipeline spotlight → Campaigns → Agent Studio → LIA
- [ ] Action choice: criar vaga → Wizard WSI
- [ ] Complete: onboarding_completed_at set, activation_state = "active"
