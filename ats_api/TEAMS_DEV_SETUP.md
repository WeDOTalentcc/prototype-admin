# Teams Development Setup - Automated Reset

## 🎯 Problema

Durante desenvolvimento com **ngrok**, a URL muda frequentemente, quebrando os webhooks do Microsoft Teams. Este guide automatiza o reset das subscriptions.

---

## ⚡ Setup Rápido (5 minutos)

### 1. Reset Manual

Sempre que o ngrok reiniciar ou webhooks pararem de funcionar:

```bash
make teams-reset
```

Ou diretamente com Rails:

```bash
docker compose exec web bundle exec rails teams:reset_fast
```

---

### 2. Setup Automático com Crontab (Recomendado)

Para **resetar automaticamente** durante o trabalho:

#### Passo 1: Abrir crontab

```bash
crontab -e
```

#### Passo 2: Escolher uma estratégia

**Opção A: Reset a cada 30 minutos (segunda a sexta, 8h às 18h)**

```cron
*/30 8-18 * * 1-5 cd /home/victhor/ats_mercado/ats_api && docker compose exec -T web bundle exec rails teams:auto_reset >> log/teams_cron.log 2>&1
```

**Opção B: Reset 1x ao dia (segunda a sexta, 9h da manhã)**

```cron
0 9 * * 1-5 cd /home/victhor/ats_mercado/ats_api && docker compose exec -T web bundle exec rails teams:auto_reset >> log/teams_cron.log 2>&1
```

**Opção C: Reset apenas quando você inicia o trabalho (segunda a sexta, 8h30)**

```cron
30 8 * * 1-5 cd /home/victhor/ats_mercado/ats_api && docker compose exec -T web bundle exec rails teams:auto_reset >> log/teams_cron.log 2>&1
```

**⚠️ IMPORTANTE:**
- Substitua `/home/victhor/ats_mercado/ats_api` pelo **caminho real do seu projeto**
- Verifique que Docker funciona sem `sudo` (adicione seu user ao grupo docker: `sudo usermod -aG docker $USER`)

#### Passo 3: Salvar e sair

- **vim/vi:** Pressione `ESC`, depois digite `:wq` e Enter
- **nano:** Pressione `CTRL+O`, Enter, depois `CTRL+X`

#### Passo 4: Verificar que funcionou

```bash
# Listar crontab
crontab -l

# Ver logs do cron
tail -f log/teams_cron.log

# Ver logs completos do Rails
docker logs -f ats_api | grep Teams
```

---

## 📋 Comandos Disponíveis

### Make Commands (Simplificados)

```bash
make teams-reset          # Reset rápido (Rails task)
make teams-auto-reset     # Reset silencioso (ideal para cron)
make teams-diagnose       # Diagnóstico completo
make teams-status         # Ver status atual
make teams-renew          # Renovar subscriptions expirando
make teams-reset-full     # Reset completo (deleta da Microsoft)
make teams-show-cron      # Ver exemplos de crontab
```

### Rails Tasks (Internos)

```bash
docker compose exec web bundle exec rails teams:reset_fast   # Reset sem deletar da MS
docker compose exec web bundle exec rails teams:auto_reset   # Reset silencioso (para cron)
docker compose exec web bundle exec rails teams:reset        # Reset completo (pede confirmação)
docker compose exec web bundle exec rails teams:diagnose     # Diagnóstico
docker compose exec web bundle exec rails teams:status       # Status
docker compose exec web bundle exec rails teams:renew        # Renovar
```

---

## 🔍 Verificar se Está Funcionando

### 1. Enviar mensagem para LIA no Teams

Após o reset, envie qualquer mensagem:

```
oi
```

### 2. Verificar logs do container

```bash
docker logs -f ats_api | grep Teams
```

**Deve aparecer:**

```
[TeamsWebhook] Notification received: chat_id=19:...
[TeamsMessageIngestionService] Processing message...
```

### 3. Se não funcionar

```bash
# Rodar diagnóstico
make teams-diagnose

# Ver status detalhado
make teams-status

# Ver se APP_HOST está correto
grep APP_HOST .env
```

---

## 🛠️ Troubleshooting

### ❌ "Container 'web' não está rodando"

```bash
docker compose up -d
```

### ❌ Erro ao executar rake task

```bash
# Verificar se containers estão rodando
docker compose ps

# Se não estiverem, iniciar
docker compose up -d
```

### ❌ Crontab não executa

1. **Verificar se cron está rodando:**
   ```bash
   sudo systemctl status cron
   ```

2. **Verificar logs do sistema:**
   ```bash
   grep CRON /var/log/syslog
   ```

3. **Testar comando manualmente:**
   ```bash
   cd /home/victhor/ats_mercado/ats_api && \
     docker compose exec -T web bundle exec rails teams:auto_reset
   ```

4. **Verificar que Docker funciona sem sudo:**
   ```bash
   docker ps
   # Se pedir sudo, adicionar ao grupo docker:
   sudo usermod -aG docker $USER
   # Fazer logout/login para aplicar
   ```

### ❌ "APP_HOST parece ser localhost"

Certifique-se que `.env` tem a URL do ngrok:

```bash
# Ver URL atual
echo $APP_HOST

# Atualizar .env
APP_HOST="https://seu-ngrok-url.ngrok-free.app"

# Resetar após atualizar
make teams-reset
```

### ❌ Webhooks ainda não chegam

1. **Verificar se ngrok está rodando:**
   ```bash
   curl https://seu-ngrok-url.ngrok-free.app/v1/webhooks/teams_chat
   ```

2. **Testar endpoint diretamente:**
   ```bash
   curl -X POST https://seu-ngrok-url.ngrok-free.app/v1/webhooks/teams_chat \
     -H "Content-Type: application/json" \
     -d '{"value": []}'
   ```

3. **Ver subscription na Microsoft:**
   ```bash
   docker compose exec web rails console
   
   # No console:
   sub = TeamsChatSubscription.first
   lia = User.find(sub.lia_user_id)
   MicrosoftService::Api.get("/subscriptions/#{sub.subscription_id}", lia)
   ```

---

## 🎉 Resultado Final

**Antes:**
- ❌ Webhooks quebram quando ngrok reinicia
- ❌ Precisa rodar comandos manualmente
- ❌ Scripts .sh desorganizados

**Depois:**
- ✅ Rake tasks padrão Rails
- ✅ Logs no `log/teams_cron.log` (padrão Rails)
- ✅ Makefile simplifica comandos
- ✅ Crontab chama Rails diretamente
- ✅ Fácil de debugar e manter

---

## 📚 Docs Relacionadas

- [teams_webhooks_troubleshooting.md](./docs/teams_webhooks_troubleshooting.md) - Troubleshooting completo
- [TEAMS_AGENT_INTEGRATION.md](./docs/TEAMS_AGENT_INTEGRATION.md) - Integração com agentes
- Código: [app/services/microsoft_service/teams_subscription_reset_service.rb](./app/services/microsoft_service/teams_subscription_reset_service.rb)

---

## 🚀 Produção

**⚠️ Em produção NÃO use crontab!**

A renovação automática já está configurada via **Sidekiq-Cron**:

```yaml
# config/schedule.yml
teams_subscription_renewal:
  cron: "*/15 * * * *"  # A cada 15 minutos
  class: "Microsoft::TeamsSubscriptionRenewalJob"
```

Subscriptions são renovadas automaticamente antes de expirar (55min TTL).

## 🧹 Limpeza

Os seguintes arquivos foram deprecados (não são mais necessários):
- ~~`teams_reset_dev.sh`~~ - Use `rails teams:reset_fast`
- ~~`setup_teams_cron.sh`~~ - Adicione manualmente ao crontab
- ~~`TEAMS_QUICKSTART.md`~~ - Use este arquivo

Tudo agora é feito através de **Rake tasks** (padrão Rails).
