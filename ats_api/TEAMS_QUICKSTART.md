# 🚀 Quick Start - Teams Reset Automation

## O Problema
Quando você usa **ngrok** para desenvolvimento, a URL muda toda vez que reinicia. Isso quebra os webhooks do Microsoft Teams e você perde as mensagens da LIA.

## Solução em 2 Passos ⚡

### 1️⃣ Reset Manual (quando precisar)
```bash
make teams-reset
```

Ou diretamente com Rails:
```bash
docker compose exec web bundle exec rails teams:reset_fast
```

Pronto! Em 5 segundos suas subscriptions são resetadas.

### 2️⃣ Setup Automático (recomendado)

Adicione ao crontab (rode uma vez):

```bash
crontab -e
```

Cole esta linha (ajuste o caminho do projeto):

```cron
*/30 8-18 * * 1-5 cd /home/victhor/ats_mercado/ats_api && docker compose exec -T web bundle exec rails teams:auto_reset >> log/teams_cron.log 2>&1
```

Isso reseta automaticamente a cada 30 minutos durante seu horário de trabalho (Seg-Sex, 8h-18h).

**Nunca mais se preocupe com webhooks quebrados!**

### 3️⃣ Verificar se está funcionando

```bash
# Ver logs do cron
tail -f log/teams_cron.log

# Ver logs do Rails
docker logs -f ats_api | grep Teams

# Testar manualmente
make teams-reset
```

---📋 Comandos Disponíveis

```bash
make teams-reset          # Reset rápido (Rails task)
---

## 🛠️ Troubleshooting# Reset silencioso (para cron)
make teams-diagnose       # Diagnóstico completo
make teams-status         # Status atual
make teams-renew          # Renovar subscriptions
make teams-show-cron      # Ver exemplos de crontab
```

**Ou diretamente com Rails:**

```bash
docker compose exec web bundle exec rails teams:reset_fast    # Reset interativo
docker compose exec -T web bundle exec rails teams:auto_reset # Reset silencioso
```

## Troubleshooting

### ❌ Webhooks não chegam?
```bash
make teams-reset
```

### ❌ Mudou a URL do ngrok?
```bash
# 1. Atualizar .env
echo 'APP_HOST="https://nova-url.ngrok-free.app"' >> .env

# 2. Resetar
make teams-reset
```

### ❌ Crontab não está funcionando?
```bash
# Verificar se foi adicionado
crontab -l | grep teams

# Testar manualmente
cd /home/victhor/ats_mercado/ats_api && ./teams_reset_dev.sh

# Verificar se Docker funciona sem sudo
docker ps
# Se não funcionar: sudo usermod -aG docker $USER
# Depois: logout e login
```

---

## Arquivos Criados

- `teams_reset_dev.sh` - Script principal de reset
- `setup_teams_cron.sh` - Setup automático do crontab
- `crontab.example` - Exemplos de configuração cron
- `TEAMS_DEV_SETUP.md` - Documentação completa

---

## Mais Info

📚 Docs completas: [TEAMS_DEV_SETUP.md](TEAMS_DEV_SETUP.md)  
🐛 Troubleshooting: [docs/teams_webhooks_troubleshooting.md](docs/teams_webhooks_troubleshooting.md)

---

**TL;DR:** Execute `./setup_teams_cron.sh` uma vez e esqueça. Webhooks funcionarão sempre! 🎉
