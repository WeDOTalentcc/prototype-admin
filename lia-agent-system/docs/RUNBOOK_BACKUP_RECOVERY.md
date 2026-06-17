# Runbook — Backup e Recuperação (LIA Platform)

**Versão:** 1.0 | **Data:** 2026-03-15 | **ACH-024**

---

## Visão Geral

Este runbook cobre os procedimentos de backup, verificação de integridade e recuperação de dados da plataforma LIA. Segue os requisitos de retenção de dados da LGPD, ISO 27001 e BCB 498.

---

## Arquitetura de Dados

| Componente | Tecnologia | Hospedagem | Backup |
|------------|-----------|-----------|--------|
| Banco principal | PostgreSQL (Neon) | Neon Cloud | Automático (Neon) |
| Cache/Sessões | Redis | Self-hosted | Snapshot periódico |
| Filas | RabbitMQ | Self-hosted | Messages persistent |
| Arquivos (CV, JDs) | Object Storage | S3-compatible | Versionamento S3 |
| Logs de auditoria | PostgreSQL | Neon Cloud | Mesma política |

---

## Política de Retenção de Dados (LGPD)

| Tipo de Dado | Retenção | Base Legal | Exclusão |
|-------------|----------|-----------|---------|
| Dados candidatos (não contratados) | 2 anos | Legítimo interesse | Automática via celery-beat |
| Dados candidatos (contratados) | 5 anos | Obrigação legal | Manual (RH) |
| Logs de auditoria (decisions) | 7 anos | SOX/BCB 498 | Manual (Compliance) |
| Logs de acesso (HTTP) | 6 meses | ISO 27001 | Automática |
| Sessões WSI | 90 dias | Consentimento | Automática |
| Snapshots bias audit | 3 anos | EU AI Act | Manual |

---

## Backups PostgreSQL (Neon)

### Verificar último backup

Neon realiza backups automáticos contínuos (Point-in-Time Recovery por 30 dias).

```bash
# Via Neon Console: https://console.neon.tech/app/projects
# Ou via API Neon:
curl -H "Authorization: Bearer $NEON_API_KEY" \
  "https://console.neon.tech/api/v2/projects/$NEON_PROJECT_ID/branches"
```

### Criar backup manual antes de migrations críticas

```bash
# Export via pg_dump (conectar via Neon connection string)
pg_dump \
  --no-owner \
  --no-acl \
  --format=custom \
  --file="backup-$(date +%Y%m%d-%H%M%S).dump" \
  "$DATABASE_URL"

# Verificar integridade do dump
pg_restore --list backup-*.dump | wc -l
```

### Restaurar a partir de backup Neon (PITR)

```bash
# 1. Criar branch de restauração no Neon Console
# Projects > [projeto] > Branches > "Restore to point in time"

# 2. Conectar à branch de restauração para validar
psql "$RESTORE_BRANCH_CONNECTION_STRING" -c "SELECT count(*) FROM candidates;"

# 3. Se OK, swap connection string no ambiente
kubectl set env deployment/lia-backend DATABASE_URL="$RESTORE_BRANCH_CONNECTION_STRING"
```

---

## Backups Redis

### Snapshot manual

```bash
# Conectar ao Redis
redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD

# Forçar snapshot (blocking BGSAVE)
BGSAVE

# Verificar quando foi o último save
LASTSAVE

# Copiar dump.rdb para storage seguro
cp /data/redis/dump.rdb "backup/redis-$(date +%Y%m%d-%H%M%S).rdb"
```

### Restaurar Redis

```bash
# 1. Parar Redis
docker-compose stop redis

# 2. Substituir dump.rdb
cp backup/redis-TIMESTAMP.rdb /data/redis/dump.rdb

# 3. Reiniciar
docker-compose start redis

# 4. Verificar
redis-cli ping  # deve retornar PONG
```

### Dados críticos em Redis

| Chave | TTL | Criticidade | Pode perder? |
|-------|-----|-------------|-------------|
| `session:*` | 24h | Alta | Sim (usuário refaz login) |
| `hitl:*` | 24h | Alta | Não — fallback para DB |
| `toon:*` | 1h | Baixa | Sim (regenerado) |
| `fairness_l3:*` | 1h | Baixa | Sim (recalculado) |
| `rag_cache:*` | 6h | Média | Sim (recalculado) |

---

## Recuperação de Desastres (DR)

### RTO e RPO

| Cenário | RTO | RPO | Procedimento |
|---------|-----|-----|-------------|
| Falha Redis | 5 min | 0 (fallback DB) | Restart container |
| Falha app server | 5 min | 0 | Rollback deploy |
| Corrupção DB (tabela) | 2h | 1h | Restaurar tabela via PITR |
| Corrupção DB (total) | 4h | 1h | Restaurar projeto Neon |
| Vazamento de dados | 2h notificação | N/A | Acionar DPO + ANPD |

### Checklist de DR

- [ ] Identificar escopo da falha (tabela, schema, projeto inteiro)
- [ ] Criar branch de restauração no Neon
- [ ] Validar contagem de registros críticos (candidates, job_vacancies, audit_decisions)
- [ ] Verificar integridade referencial: `app/alembic/versions/` — rodar migrations do zero
- [ ] Sincronizar Redis com novo DB
- [ ] Testar endpoints críticos: `/api/v1/health`, `/api/v1/drift/status`
- [ ] Notificar DPO se dados pessoais foram afetados (LGPD art. 48 — 72h ANPD)
- [ ] Atualizar audit log de incidente

---

## Validação de Integridade Pós-Restauração

```bash
# Script de verificação de integridade
python -c "
import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def check():
    async with AsyncSessionLocal() as db:
        tables = ['candidates', 'job_vacancies', 'companies', 'audit_decisions',
                  'hitl_requests', 'bias_audit_snapshots']
        for t in tables:
            result = await db.execute(text(f'SELECT count(*) FROM {t}'))
            count = result.scalar()
            print(f'  {t}: {count} registros')
        print('OK — integridade básica verificada')

asyncio.run(check())
"

# Verificar migrations aplicadas
alembic history --verbose | head -20
alembic current
```

---

## Dados Sensíveis — Atenção Especial

### PII em backups

- Todos os backups contêm dados pessoais (LGPD)
- Backups devem ser criptografados: `openssl enc -aes-256-cbc -in backup.dump -out backup.dump.enc`
- Chave de criptografia: armazenada em AWS Secrets Manager (`lia/backup-encryption-key`)
- Acesso a backups: apenas DBA + DPO (auditado)

### Exclusão de candidatos (LGPD Art. 18)

```bash
# Verificar requests pendentes de exclusão
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.lia.wedotalent.com/api/v1/admin/lgpd/cleanup-status

# Executar limpeza manual se celery-beat falhou
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.lia.wedotalent.com/api/v1/admin/lgpd/run-cleanup
```

---

## Contatos e Responsabilidades

| Responsabilidade | Contato |
|----------------|---------|
| Backup PostgreSQL | Neon Support + DBA |
| Redis/RabbitMQ | SRE on-call |
| LGPD / DPO | lgpd@wedotalent.com |
| BCB 498 (financeiras) | compliance@wedotalent.com |
| ISO 27001 | security@wedotalent.com |

---

*Mantido por: Time de Engenharia + DPO WeDOTalent | Próxima revisão: 2026-06-15*
