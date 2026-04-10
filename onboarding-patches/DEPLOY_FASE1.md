# Deploy — Fase 1: Foundation (Onboarding LIA)

## Rails (ats-api-copia)

### 1. Migrations (executar em ordem)
```bash
cp onboarding-patches/rails/migrations/*.rb db/migrate/
rails db:migrate
```

### 2. Models
```bash
cp onboarding-patches/rails/models/onboarding_session.rb app/models/
cp onboarding-patches/rails/models/magic_link.rb app/models/
cp onboarding-patches/rails/models/onboarding_message.rb app/models/
```

### 3. Patch User model
Adicionar ao `app/models/user.rb` (ver `user_onboarding_extension.rb`):
- Associations: `has_many :magic_links`, `has_many :onboarding_sessions`
- Validations: `activation_state` inclusion
- Methods: `onboarding_lia_enabled?`, `complete_onboarding!`

### 4. Services
```bash
cp onboarding-patches/rails/services/magic_link_service.rb app/services/
cp onboarding-patches/rails/services/onboarding_event_publisher.rb app/services/
```

### 5. Controllers
```bash
mkdir -p app/controllers/v1/auth
cp onboarding-patches/rails/controllers/onboarding_controller.rb app/controllers/v1/users/
cp onboarding-patches/rails/controllers/magic_links_controller.rb app/controllers/v1/auth/
```

### 6. Mailer + Views
```bash
cp onboarding-patches/rails/mailers/onboarding_mailer.rb app/mailers/
mkdir -p app/views/onboarding_mailer
cp onboarding-patches/rails/views/onboarding_mailer/welcome_email.html.erb app/views/onboarding_mailer/
```

### 7. Routes
Adicionar ao `config/routes.rb` (ver `routes_patch.rb`)

### 8. Verificar
```bash
rails db:migrate:status  # todas as migrations rodaram?
rails console
> MagicLink.new  # funciona?
> OnboardingSession.new  # funciona?
> User.new.respond_to?(:onboarding_lia_enabled?)  # true?
```

---

## FastAPI (lia-agent-system no Replit)

### 1. Migration
```bash
cp onboarding-patches/fastapi/migrations/059_create_onboarding_tables.py alembic/versions/
alembic upgrade head
```

### 2. Verificar
```bash
alembic current  # deve mostrar 059
```

---

## Checklist

- [ ] 4 Rails migrations executadas (20250716000010-13)
- [ ] 3 models criados (OnboardingSession, MagicLink, OnboardingMessage)
- [ ] User model patcheado com associations + methods
- [ ] Account model tem `onboarding_lia_enabled`
- [ ] MagicLinkService funciona (generate + verify)
- [ ] OnboardingMailer envia email (verificar delivery method configurado)
- [ ] OnboardingController: invite, status, progress, consent endpoints
- [ ] MagicLinksController: verify endpoint
- [ ] Routes adicionadas
- [ ] OnboardingEventPublisher publica para RabbitMQ
- [ ] FastAPI migration 059 executada
- [ ] Tabelas onboarding_agent_state + whatsapp_sessions criadas
