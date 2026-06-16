# Teams LIA em Produção — Passo a Passo

## Pré-requisitos

- GCP Project: `infinite-rider-465217-i1`
- Cloud Run service: `ats-api` (já rodando)
- Redis acessível (REDIS_URL no Secret Manager)
- RabbitMQ acessível (RABBITMQ_URL configurado)
- Azure App Registration configurado

---

## 1. Verificar Secrets no GCP

```bash
# Confirmar que os secrets existem e têm valor real (não "PLACEHOLDER")
gcloud secrets versions access latest --secret=APP_HOST
gcloud secrets versions access latest --secret=AZURE_APP_ID
gcloud secrets versions access latest --secret=AZURE_APP_SECRET
gcloud secrets versions access latest --secret=AZURE_SCOPES
gcloud secrets versions access latest --secret=REDIS_URL
```

**APP_HOST** deve ser o domínio público da API (ex: `api.wedotalent.cc`), SEM `https://`.

Se algum secret precisar ser atualizado:
```bash
echo -n "valor_correto" | gcloud secrets versions add NOME_DO_SECRET --data-file=-
```

---

## 2. Configurar Azure App Registration

Portal: https://portal.azure.com → Azure Active Directory → App Registrations

### Redirect URI de produção
Adicionar:
```
https://api.wedotalent.cc/v1/auth/microsoft_graph_auth/callback
```

### API Permissions (Delegated)
Confirmar que existem:
- `openid`
- `profile`
- `email`
- `offline_access`
- `User.Read`
- `Mail.Read`
- `Mail.Send`
- `MailboxSettings.Read`
- `Calendars.ReadWrite`
- `Chat.ReadWrite`
- `Chat.Create`
- `OnlineMeetings.ReadWrite`

### Certificados/Secrets
Verificar que o `AZURE_APP_SECRET` no GCP não expirou. Se expirou, gerar novo no Azure e atualizar:
```bash
echo -n "novo_secret" | gcloud secrets versions add AZURE_APP_SECRET --data-file=-
```

---

## 3. Deploy do Sidekiq (CRÍTICO)

O Cloud Run atual (`ats-api`) roda só o Puma (web). Sidekiq precisa de um serviço separado para:
- Processar jobs (ingestion, response, token refresh, subscription renewal)
- Rodar os crons do `config/schedule.yml`

### Opção A: Cloud Run com always-on

```bash
export REGION="us-central1"
export PROJECT_ID="infinite-rider-465217-i1"
export CONN_NAME="infinite-rider-465217-i1:us-central1:ats-db"
export VPC_CONNECTOR_NAME="ats-connector"

# Usar a mesma imagem do último deploy
IMAGE=$(gcloud run services describe ats-api --region=$REGION --format='value(spec.template.spec.containers[0].image)')

# Pegar os mesmos secrets
SECRETS=$(gcloud run services describe ats-api --region=$REGION --format='value(spec.template.metadata.annotations."run.googleapis.com/secrets")')

gcloud run deploy ats-sidekiq \
  --project="$PROJECT_ID" \
  --image "$IMAGE" \
  --region "$REGION" \
  --command "bundle","exec","sidekiq","-C","config/sidekiq.yml" \
  --set-cloudsql-instances "$CONN_NAME" \
  --vpc-connector "$VPC_CONNECTOR_NAME" \
  --cpu=1 --memory=1Gi \
  --min-instances=1 --max-instances=1 \
  --no-cpu-throttling \
  --no-allow-unauthenticated \
  --set-env-vars="RAILS_ENV=production,RAILS_LOG_TO_STDOUT=true,RABBITMQ_URL=amqps://jdrmulpn:pvtLMN2jP8tyzZkz9ThBepoZlC6q8p8V@horse.lmq.cloudamqp.com/jdrmulpn,EMBEDDING_RELEVANCE_THRESHOLD=0.70,EMBEDDING_KEYWORD_GATE=true,DATA_COLLECTOR_URL=https://data-collector-api-305702006814.us-central1.run.app,ATS_SYNC_ENABLED=true,GEMINI_FAST_MODEL=gemini-2.5-flash,FRONT_URL=https://app.wedotalent.cc,INTERVIEW_AI_BASE_URL=https://interview.wedotalent.cc" \
  --quiet
```

> **Importante:** `--min-instances=1` + `--no-cpu-throttling` mantém o Sidekiq sempre ativo. Sem isso ele vai dormir e os crons não rodam.

### Opção B: Adicionar Sidekiq no deploy3.sh

Adicionar no final do `deploy3.sh`, antes do bloco de sucesso:

```bash
echo "🔧 Fazendo deploy do Sidekiq..."
gcloud run deploy ats-sidekiq \
  --project="$PROJECT_ID" \
  --image "$IMAGE" \
  --region "$REGION" \
  --command "bundle","exec","sidekiq","-C","config/sidekiq.yml" \
  --set-cloudsql-instances "$CONN_NAME" \
  --vpc-connector "$VPC_CONNECTOR_NAME" \
  --set-secrets="$SECRETS_WEB_STR" \
  --set-env-vars="$ENV_VARS_WEB" \
  --cpu=1 --memory=1Gi \
  --min-instances=1 --max-instances=1 \
  --no-cpu-throttling \
  --no-allow-unauthenticated \
  --quiet
```

---

## 4. Verificar que Migrations Rodaram

A tabela `teams_chat_subscriptions` já deve existir (migration `20260304221140`). Confirmar:

```bash
# Via Cloud Run Job de migrations (já roda no deploy3.sh)
gcloud run jobs execute ats-migrate --region us-central1 --wait
```

Ou via Rails console:
```ruby
ActiveRecord::Base.connection.table_exists?(:teams_chat_subscriptions)
# => true
```

---

## 5. Criar/Configurar o User LIA

Em cada tenant, precisa existir um user com `lia_user: true`.

### Verificar se já existe

```ruby
# Rails console (produção)
Account.pluck(:tenant).each do |t|
  Apartment::Tenant.switch(t) do
    lia = User.find_by(lia_user: true)
    if lia
      puts "#{t}: LIA=#{lia.email} token=#{lia.ms_access_token.present?} expires=#{lia.ms_expires_at}"
    else
      puts "#{t}: ❌ SEM LIA USER"
    end
  end
end
```

### Se não existir, criar

```ruby
Apartment::Tenant.switch("nome_do_tenant") do
  account = Account.find_by(tenant: "nome_do_tenant")
  User.create!(
    name: "Lia",
    email: "lia@wedotalent.cc",
    password: SecureRandom.hex(16),
    lia_user: true,
    account_id: account.id,
    status: 1
  )
end
```

---

## 6. Autenticar LIA no Microsoft (OAuth)

A LIA precisa de `ms_access_token` para enviar mensagens no Teams. Esse token vem do OAuth da Microsoft.

### Gerar URL de auth

```ruby
# Rails console produção
lia = User.find_by(lia_user: true)
redirect_uri = "https://api.wedotalent.cc/v1/auth/microsoft_graph_auth/callback"
scopes = "openid profile email offline_access User.Read Mail.Read Mail.Send MailboxSettings.Read Calendars.ReadWrite Chat.ReadWrite Chat.Create OnlineMeetings.ReadWrite"

url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?" + {
  client_id: ENV["AZURE_APP_ID"],
  response_type: "code",
  redirect_uri: redirect_uri,
  scope: scopes,
  state: JWT.encode({ user_id: lia.id, type: "integration" }, Rails.application.credentials.secret_key_base, "HS256"),
  response_mode: "query"
}.to_query

puts url
```

### Fazer login

1. Abrir o URL gerado no browser
2. Fazer login com a conta Microsoft da LIA (ex: `lia@wedotalent.cc`)
3. Aceitar as permissões
4. O callback salva os tokens automaticamente

### Confirmar que funcionou

```ruby
lia.reload
puts "Token: #{lia.ms_access_token.present?}"
puts "Refresh: #{lia.ms_refresh_token.present?}"
puts "Expires: #{lia.ms_expires_at}"
# Token: true, Refresh: true
```

> A partir daqui o `Microsoft::TokenRefreshJob` (cron 5min) renova o token automaticamente.

---

## 7. Enviar Mensagens para @wedotalent.cc

### Dry-run primeiro

```ruby
# Rails console
MicrosoftService::TeamsProactiveOutreachService.call(domain: "wedotalent.cc", dry_run: true)
```

Vai listar quem receberia sem enviar nada.

### Enviar de verdade

```ruby
MicrosoftService::TeamsProactiveOutreachService.call(domain: "wedotalent.cc")
```

Ou via rake task:
```bash
# Se tiver shell no container
bundle exec rails "teams:outreach[wedotalent.cc]"
```

Cada recruiter vai receber um DM da LIA no Teams com a mensagem de apresentação.

---

## 8. Verificar que Tudo Está Funcionando

### Status das subscriptions

```ruby
Account.pluck(:tenant).each do |t|
  Apartment::Tenant.switch(t) do
    next unless ActiveRecord::Base.connection.table_exists?(:teams_chat_subscriptions)
    subs = TeamsChatSubscription.all
    next if subs.empty?
    puts "\n=== #{t} (#{subs.count} subs) ==="
    subs.each do |s|
      puts "  [#{s.status}] recruiter=#{s.recruiter_user_id} chat=#{s.chat_id} expires=#{s.subscription_expires_at}"
    end
  end
end
```

### Testar fluxo completo

1. Envie uma mensagem para a LIA no Teams (como recruiter)
2. Verifique nos logs do Sidekiq que o webhook chegou:
   ```
   [TeamsWebhook] Notification received
   [TeamsMessageIngestionJob] Processing...
   ```
3. Verifique que a LIA respondeu no Teams

---

## 9. Crons Automáticos (já configurados)

Com o Sidekiq rodando, estes crons funcionam automaticamente via `sidekiq-cron`:

| Job | Intervalo | O que faz |
|-----|-----------|-----------|
| `Microsoft::TokenRefreshJob` | 5 min | Renova tokens Microsoft antes de expirar |
| `Microsoft::TeamsSubscriptionRenewalJob` | 15 min | Renova webhooks Teams (TTL 55min) |

**Não precisa configurar crontab do sistema.** O `sidekiq-cron` cuida de tudo.

---

## Troubleshooting

| Problema | Causa | Solução |
|----------|-------|---------|
| LIA não responde | Sidekiq não está rodando | Verificar se `ats-sidekiq` está ativo no Cloud Run |
| "Token expired" | Token da LIA expirou e refresh falhou | Re-autenticar LIA (passo 6) |
| Webhook não chega | APP_HOST errado ou subscription expirada | `gcloud secrets versions access latest --secret=APP_HOST` e rodar `teams:recreate` |
| "Subscription failed" | Token expirado ou permissões faltando | Verificar token da LIA + permissões no Azure |
| Mensagens duplicadas | Redis indisponível (dedup falhou) | Verificar REDIS_URL |
| Recruiter não recebe DM | Email não existe no Azure AD | Confirmar que o email do recruiter existe no M365 |

### Logs úteis

```bash
# Logs do web (webhooks)
gcloud run services logs read ats-api --region=us-central1 --limit=50 | grep -i teams

# Logs do Sidekiq (jobs)
gcloud run services logs read ats-sidekiq --region=us-central1 --limit=50 | grep -i teams
```

---

## Resumo da Ordem

1. ✅ Verificar secrets GCP
2. ✅ Configurar Azure App (redirect URI + permissões)
3. ✅ Deploy do Sidekiq (`ats-sidekiq`)
4. ✅ Confirmar migrations
5. ✅ Criar user LIA (se não existir)
6. ✅ Autenticar LIA via OAuth (pegar ms_access_token)
7. ✅ Rodar outreach (`teams:outreach[wedotalent.cc]`)
8. ✅ Verificar fluxo completo
9. ✅ Crons já rodam sozinhos com Sidekiq
