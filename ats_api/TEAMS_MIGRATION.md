# Teams Subscriptions - Migração para Rake Tasks

## 🎯 TL;DR

Scripts `.sh` foram **deprecados**. Use **Rake tasks** (padrão Rails):

```bash
# Antes (deprecado):
./teams_reset_dev.sh

# Depois:
make teams-reset
# ou
docker compose exec web bundle exec rails teams:reset_fast
```

---

## 📋 Migration Guide

### Reset Manual

| Antes (Deprecado) | Depois (Padrão Rails) |
|-------------------|----------------------|
| `./teams_reset_dev.sh` | `make teams-reset` |
| - | `docker compose exec web bundle exec rails teams:reset_fast` |

### Crontab

| Antes (Deprecado) | Depois (Padrão Rails) |
|-------------------|----------------------|
| `./teams_reset_dev.sh >> /tmp/teams_reset.log` | `docker compose exec -T web bundle exec rails teams:auto_reset >> log/teams_cron.log` |
| `./setup_teams_cron.sh` | Adicionar manualmente ao crontab (ver `make teams-show-cron`) |

### Exemplo Crontab Atualizado

```cron
# Reset a cada 30 minutos (Seg-Sex, 8h-18h)
*/30 8-18 * * 1-5 cd /home/victhor/ats_mercado/ats_api && docker compose exec -T web bundle exec rails teams:auto_reset >> log/teams_cron.log 2>&1
```

---

## 🆕 Novos Comandos

### Makefile

```bash
make teams-reset          # Reset rápido (interativo)
make teams-auto-reset     # Reset silencioso (para cron)
make teams-diagnose       # Diagnóstico completo
make teams-status         # Ver status
make teams-renew          # Renovar subscriptions
make teams-show-cron      # Ver exemplos de crontab
```

### Rake Tasks

```bash
# Interativo (com logs bonitos no STDOUT)
docker compose exec web bundle exec rails teams:reset_fast

# Silencioso (logs apenas no Rails.logger, ideal para cron)
docker compose exec -T web bundle exec rails teams:auto_reset

# Completo (pede confirmação)
docker compose exec web bundle exec rails teams:reset

# Outros
rails teams:diagnose      # Diagnóstico
rails teams:status        # Status
rails teams:renew         # Renovar
```

---

## 🔍 Por Que Migrar?

### Problemas dos Scripts `.sh`:

❌ Não é padrão Rails  
❌ Logs em `/tmp` (fora do projeto)  
❌ Difícil de debugar  
❌ Não integra com `Rails.logger`  
❌ Precisa de permissões `chmod +x`  
❌ Dependências externas (bash, grep, etc)  

### Vantagens das Rake Tasks:

✅ **Padrão Rails** - idiomático e familiar  
✅ **Logs integrados** - `log/teams_cron.log` e `Rails.logger`  
✅ **Environment carregado** - acesso a models, services, config  
✅ **Testável** - pode escrever specs  
✅ **Documentado** - `rails -T` lista todas as tasks  
✅ **Multiplataforma** - funciona em qualquer OS com Ruby  
✅ **Integração** - usa mesmos services que o resto da app  

---

## 📦 Arquivos do Projeto

### Scripts Deprecados (podem ser removidos)

- ~~`teams_reset_dev.sh`~~ → Use `rails teams:reset_fast`
- ~~`setup_teams_cron.sh`~~ → Adicione ao crontab manualmente

### Ativos

- `lib/tasks/teams.rake` - **Todas as rake tasks**
- `Makefile` - Atalhos convenientes
- `crontab.example` - Exemplos de configuração
- `TEAMS_DEV_SETUP.md` - Documentação completa
- `TEAMS_QUICKSTART.md` - Guia rápido

---

## 🧹 Como Limpar (Opcional)

Se quiser remover os scripts `.sh` deprecados:

```bash
# ATENÇÃO: Certifique-se de não estar usando eles antes!
rm teams_reset_dev.sh setup_teams_cron.sh
```

**Ou deixe-os no projeto** com os avisos de deprecação (já adicionados).

---

## 🚀 Próximos Passos

1. **Atualize seu crontab** (se estiver usando):
   ```bash
   crontab -e
   # Substitua ./teams_reset_dev.sh por:
   docker compose exec -T web bundle exec rails teams:auto_reset >> log/teams_cron.log 2>&1
   ```

2. **Use `make` para tudo**:
   ```bash
   make teams-reset          # Quando ngrok mudar
   make teams-diagnose       # Para debugar
   make teams-status         # Ver estado atual
   ```

3. **Configure logs** (opcional):
   ```bash
   # Ver logs do cron
   tail -f log/teams_cron.log
   
   # Limpar logs antigos
   > log/teams_cron.log
   ```

---

## 📚 Documentação

- **Quick Start:** [TEAMS_QUICKSTART.md](TEAMS_QUICKSTART.md)
- **Setup Completo:** [TEAMS_DEV_SETUP.md](TEAMS_DEV_SETUP.md)
- **Troubleshooting:** [docs/teams_webhooks_troubleshooting.md](docs/teams_webhooks_troubleshooting.md)
- **Código:** [lib/tasks/teams.rake](lib/tasks/teams.rake)

---

**TL;DR:** Scripts `.sh` foram substituídos por Rake tasks. Use `make teams-reset` ou `rails teams:reset_fast`. 🎉
