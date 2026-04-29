# Microsoft Teams Webhooks - Troubleshooting Guide

## 🚨 Problema Comum: Webhooks Não Chegam

### Causas mais comuns:

1. **URL do ngrok mudou** (ngrok gera URLs temporárias)
2. **Subscription expirou** (dura apenas 55 minutos)
3. **Subscription falhou ao criar** (erro na API da Microsoft)
4. **Token MS expirado** (sem refresh token válido)

---

## 🔍 Diagnóstico Rápido

### **1. Rodar diagnóstico completo**

```bash
docker-compose exec web bundle exec rails teams:diagnose
```

**O que verifica:**
- ✅ URL do webhook configurada
- ✅ Status de todas subscriptions (active/failed/expired)
- ✅ Tokens dos usuários LIA
- ✅ Conectividade com Microsoft Graph API

**Output esperado:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 [TeamsSubscriptionDiagnostic] Running diagnostics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 Webhook URL: https://xxxx.ngrok-free.app/v1/webhooks/teams_chat
⚠️  Using ngrok - URL may change on tunnel restart

📊 Tenant: public
   Total: 1
   ✅ Active: 1
   ❌ Failed: 0
   ⏰ Expired: 0
   ⚠️  Expiring Soon: 0

✅ All LIA users have MS tokens
✅ Microsoft Graph API: Connected
```

---

## 🔧 Soluções

### **Solução 1: Script Bash Rápido** ⚡ (RECOMENDADO para DEV)

Script interativo com verificações e logs bonitos:

```bash
# Executar manualmente
./teams_reset_dev.sh

# OU usar atalho do Makefile
make teams-reset
```

**O que o script faz:**
- ✅ Verifica se Docker está rodando
- ✅ Mostra URL atual do webhook (APP_HOST)
- ✅ Reseta subscriptions rapidamente
- ✅ Fornece próximos passos

### **Solução 2: Adicionar ao Crontab** ⏰ (Automático)

Para **resetar automaticamente** quando o ngrok reiniciar (desenvolvimento):

```bash
# Editar crontab
crontab -e

# Adicionar linha (reseta a cada 30 minutos durante horário de trabalho):
*/30 8-18 * * 1-5 cd /home/victhor/ats_mercado/ats_api && ./teams_reset_dev.sh >> /tmp/teams_reset.log 2>&1

# OU resetar apenas 1x ao dia às 9h:
0 9 * * 1-5 cd /home/victhor/ats_mercado/ats_api && ./teams_reset_dev.sh >> /tmp/teams_reset.log 2>&1
```

**Verificar logs do cron:**
```bash
tail -f /tmp/teams_reset.log
```

**⚠️ Atenção:**
- Substitua `/home/victhor/ats_mercado/ats_api` pelo caminho real do seu projeto
- O crontab usa seu usuário, então o Docker precisa estar acessível sem sudo
- Para produção: NÃO use cron, use a task `teams:renew` via Sidekiq-Cron (já configurado)

### **Solução 3: Reset Rápido (Comando Direto)**

Recria todas subscriptions sem deletar da Microsoft (mais rápido):

```bash
docker compose exec web bundle exec rails teams:reset_fast
# OU
make teams-reset
```

### **Solução 4: Reset Completo**

Deleta subscriptions da Microsoft e recria com nova URL:

```bash
docker compose exec web bundle exec rails teams:reset
# OU
make teams-reset-full
```

**⚠️ Confirmará antes de executar:**
```
⚠️  This will DELETE and RECREATE all Teams subscriptions
Current webhook URL: https://xxxx.ngrok-free.app/v1/webhooks/teams_chat
Continue? (yes/no):
```

### **Solução 5: Renovar Subscriptions Expirando**

Se subscriptions estão ativas mas expirando em breve:

```bash
docker compose exec web bundle exec rails teams:renew
# OU
make teams-renew
```

---

## 🎯 Atalhos do Makefile

Comandos simplificados (adicionados recentemente):

```bash
make teams-reset          # Reset rápido com script bash
make teams-diagnose       # Diagnóstico completo
make teams-status         # Ver status das subscriptions
make teams-renew          # Renovar subscriptions expirando
make teams-reset-full     # Reset completo (deleta da MS)
```

---

## 🛠️ Comandos Úteis

### **Ver status de todas subscriptions**

```bash
docker-compose exec web bundle exec rails teams:status
```

### **Via Ruby Console**

```bash
docker-compose exec web bundle exec rails console

# Ver todas subscriptions
TeamsChatSubscription.all.each do |s|
  puts "#{s.chat_id}: #{s.status}, expires: #{s.subscription_expires_at}"
end

# Resetar uma subscription específica
sub = TeamsChatSubscription.find_by(chat_id: "19:...")
lia = User.find(sub.lia_user_id)
sub.update!(subscription_id: nil, status: "expired")
MicrosoftService::TeamsSubscriptionService.new(lia, sub.chat_id).call

# Diagnosticar
MicrosoftService::TeamsSubscriptionDiagnosticService.run

# Resetar tudo
MicrosoftService::TeamsSubscriptionResetService.reset_all_subscriptions(force_delete_ms: false)
```

---

## 📋 Checklist de Troubleshooting

### ✅ Passo a Passo

**1. Verificar URL do webhook**
```bash
docker-compose exec web bundle exec rails runner "puts ENV['APP_HOST']"
```

Se retornou ngrok, verificar se tunnel está ativo:
```bash
curl https://SEU-NGROK.ngrok-free.app/v1/webhooks/teams_chat
# Deve retornar: Filter chain halted... (OK - endpoint existe)
```

**2. Rodar diagnóstico**
```bash
docker-compose exec web bundle exec rails teams:diagnose
```

**3. Se há subscriptions "failed" ou "expired"**
```bash
docker-compose exec web bundle exec rails teams:reset_fast
```

**4. Testar envio de mensagem**
- Envie mensagem no Teams para a LIA
- Verifique logs do container:
```bash
docker-compose logs -f web | grep "TeamsWebhook|TeamsMessage"
```

**5. Se ainda não funcionar**
```bash
# Reset completo (deleta da MS)
docker-compose exec web bundle exec rails teams:reset
```

---

## 🔬 Logs de Debug

### **Ver logs de webhooks recebidos**

```bash
docker-compose logs -f web | grep TeamsWebhook
```

**Output esperado quando webhook chega:**
```
[TeamsWebhook] Notification received: chat_id=19:...
[TeamsMessageIngestionJob] Processing message_id=...
```

### **Ver logs de subscriptions**

```bash
docker-compose logs -f web | grep TeamsSubscription
```

---

## 🚀 Setup Inicial (primeira vez)

### **1. Criar ngrok tunnel** 

```bash
ngrok http 3000
```

Copiar URL (ex: `https://abc123.ngrok-free.app`)

### **2. Configurar APP_HOST**

```bash
# .env ou docker-compose.yml
APP_HOST=https://abc123.ngrok-free.app
```

### **3. Reiniciar container**

```bash
docker-compose restart web
```

### **4. Resetar subscriptions com nova URL**

```bash
docker-compose exec web bundle exec rails teams:reset_fast
```

---

## 📊 Estrutura do Sistema

### **Fluxo de Subscription**

```
1. Recruiter inicia chat com LIA no Teams
   ↓
2. LIA responde → PerCandidateNotificationJob cria subscription
   ↓
3. Subscription registrada no Microsoft Graph API
   ├─ notificationUrl: https://APP_HOST/v1/webhooks/teams_chat
   ├─ resource: /chats/{chat_id}/messages
   ├─ expirationDateTime: 55 minutos no futuro
   └─ clientState: secret para validação
   ↓
4. Microsoft envia webhooks para APP_HOST quando há novas mensagens
   ↓
5. TeamsWebhookController processa e enfileira TeamsMessageIngestionJob
   ↓
6. Mensagem processada e resposta enviada via TeamsResponseJob
```

### **Renovação Automática**

```
Cron Job (a cada 15 min) → TeamsSubscriptionRenewalJob
   ↓
Busca subscriptions expirando em < 10 min
   ↓
Renova cada subscription (PATCH /subscriptions/{id})
   ↓
Atualiza subscription_expires_at
```

### **Lifecycle Events**

Microsoft envia lifecycle events quando:
- Subscription está prestes a expirar
- Subscription foi deletada
- Subscription encontrou erro

TeamsWebhookController trata esses eventos e renova automaticamente.

---

## 🔐 Segurança

### **Validação de Webhooks**

Todo webhook recebido valida:
1. **clientState**: Compara com `Rails.application.credentials.secret_key_base.first(32)`
2. **subscription_id**: Verifica se existe no banco
3. **tenant**: Resolve tenant pela subscription

### **Tokens MS**

- Armazenados em `User.ms_access_token`
- Expiram em 1h (renovados automaticamente)
- Refresh token armazenado em `User.ms_refresh_token`

---

## ⚠️  Problemas Conhecidos

### **1. Ngrok URL mudou**

**Sintoma:** Webhooks param de chegar após reiniciar ngrok  
**Solução:** `rails teams:reset_fast`

### **2. Subscriptions expiraram durante deploy**

**Sintoma:** Após deploy, webhooks não chegam  
**Solução:** `rails teams:recreate` (force recreate all active)

### **3. Token MS expirado sem refresh**

**Sintoma:** Diagnóstico mostra "No valid token"  
**Solução:** Usuário precisa reconectar conta MS no frontend

### **4. Subscription "failed" mas sem motivo claro**

**Sintoma:** Status = "failed", subscription_id = nil  
**Solução:** `rails teams:reset_fast` (recria do zero)

---

## 📚 Arquivos Relacionados

- **Subscription Service:** `app/services/microsoft_service/teams_subscription_service.rb`
- **Reset Service:** `app/services/microsoft_service/teams_subscription_reset_service.rb`
- **Diagnostic Service:** `app/services/microsoft_service/teams_subscription_diagnostic_service.rb`
- **Webhook Controller:** `app/controllers/v1/webhooks/microsoft_teams/teams_webhook_controller.rb`
- **Renewal Job:** `app/jobs/microsoft/teams_subscription_renewal_job.rb`
- **Model:** `app/models/teams_chat_subscription.rb`
- **Rake Tasks:** `lib/tasks/teams.rake`

---

## 🆘 Suporte

**Se ainda não funcionar após todas soluções:**

1. Rodar diagnóstico e copiar output:
```bash
docker-compose exec web bundle exec rails teams:diagnose > teams_debug.txt
```

2. Verificar logs do webhook:
```bash
docker-compose logs web | grep -E "Teams(Webhook|Subscription|Message)" | tail -100 > teams_logs.txt
```

3. Verificar se ngrok está aceitando requests:
```bash
curl -I https://SEU-NGROK.ngrok-free.app/v1/webhooks/teams_chat
```

4. Testar criação manual de subscription:
```ruby
sub = TeamsChatSubscription.first
lia = User.find(sub.lia_user_id)
result = MicrosoftService::TeamsSubscriptionService.new(lia, sub.chat_id).call
puts sub.reload.inspect
```
