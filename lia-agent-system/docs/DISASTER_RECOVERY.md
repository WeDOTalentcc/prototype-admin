# Disaster Recovery Plan — LIA Agent System

**Versão:** 1.0
**Data:** 2026-05-02
**Owner:** Infra + Backend
**Revisão:** Trimestral

---

## 1. Objetivos (RPO / RTO)

| Componente | RPO (perda máx. de dados) | RTO (tempo máx. de recuperação) |
|---|---|---|
| Banco de dados (Neon/Postgres) | 1 hora (PITR contínuo) | 4 horas |
| Redis (sessões + cache) | 24 horas (dump.rdb periódico) | 30 minutos |
| Object storage (CVs, JDs) | 24 horas (versionamento S3) | 2 horas |
| Serviço IA (FastAPI) | N/A (stateless) | 15 minutos |
| Frontend (Next.js) | N/A (stateless) | 10 minutos |
| Filas (RabbitMQ) | 0 (mensagens persistidas em disco) | 30 minutos |

> **Referência:** Neon PITR retém backups por 30 dias com granularidade contínua.
> RPO de 1h para DB é conservador — na prática Neon oferece recovery point a qualquer segundo.

---

## 2. Cenários de Desastre e Decisão

Os 5 cenários críticos mapeados nos playbooks operacionais:

| Cenário | Nível | RTO Alvo | Playbook |
|---|---|---|---|
| LLM primário down (Anthropic) | L3 — Degradação Severa | 15 min (fallback OpenAI automático) | PB-01 |
| Banco de dados indisponível (Neon PostgreSQL) | L4 — Incidente Crítico | 4 horas | PB-02 |
| Redis indisponível | L2-L3 — Degradação Moderada | 30 minutos | PB-03 |
| Circuit Breaker em OPEN (qualquer serviço externo) | L2-L3 | 5-15 min | PB-04 |
| Drift alert URGENT/CRITICAL (2+ triggers) | L2-L3 | 10 min triagem + ação | PB-05 |

### 2.1 Árvore de decisão rápida

```
Plataforma inacessível?
├── HTTP 500/503 em massa → PB-02 (banco) ou app crash → rollback deploy
├── IA não responde → PB-01 (LLM)
├── Logins falhando → PB-04 (WORKOS_CIRCUIT)
├── Emails não enviados → PB-04 (MAILGUN/RESEND_CIRCUIT)
├── Drift alert recebido → PB-05
└── Sessões perdendo estado → PB-03 (Redis)
```

---

## 3. Procedimento de Recuperação de Banco de Dados (Neon PostgreSQL)

### 3.1 Backup manual antes de migrations críticas

```bash
pg_dump \
  --no-owner \
  --no-acl \
  --format=custom \
  --file="backup-$(date +%Y%m%d-%H%M%S).dump" \
  "$DATABASE_URL"

# Verificar integridade
pg_restore --list backup-*.dump | wc -l
```

### 3.2 Restauração via PITR (Point-in-Time Recovery)

```bash
# 1. Criar branch de restauração no Neon Console
# Projects > [projeto] > Branches > "Restore to point in time"
# Selecionar timestamp anterior ao incidente

# 2. Validar dados na branch de restauração
psql "$RESTORE_BRANCH_CONNECTION_STRING" \
  -c "SELECT count(*) FROM candidates; SELECT count(*) FROM job_vacancies;"

# 3. Se OK, atualizar connection string no ambiente
kubectl set env deployment/lia-backend DATABASE_URL="$RESTORE_BRANCH_CONNECTION_STRING"
# Ou via docker-compose: editar .env → docker-compose up -d
```

### 3.3 Verificação de integridade pós-restauração

```bash
python3 -c "
import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def check():
    async with AsyncSessionLocal() as db:
        tables = ['candidates', 'job_vacancies', 'companies', 'audit_decisions',
                  'hitl_requests', 'bias_audit_snapshots']
        for t in tables:
            result = await db.execute(text(f'SELECT count(*) FROM {t}'))
            print(f'  {t}: {result.scalar()} registros')
        print('OK — integridade básica verificada')

asyncio.run(check())
"

# Verificar migrations aplicadas
alembic current
alembic history --verbose | head -10
```

### 3.4 Obrigação LGPD pós-incidente

Se dados pessoais de candidatos foram afetados:
- **< 2 horas:** notificar DPO interno (lgpd@wedotalent.com)
- **< 72 horas:** notificar ANPD (LGPD Art. 48)
- Acionar `IncidentResponseService` em `app/domains/lgpd/services/incident_response_service.py`

---

## 4. Procedimento de Recuperação de Redis

### 4.1 Restart simples (primeiro passo sempre)

```bash
docker-compose restart redis
sleep 10
redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD ping
# Esperado: PONG
```

### 4.2 Restore de snapshot (se restart não resolver)

```bash
docker-compose stop redis
cp backup/redis-TIMESTAMP.rdb /data/redis/dump.rdb
docker-compose start redis
redis-cli ping  # deve retornar PONG

# Verificar chaves críticas restauradas
redis-cli keys "hitl:*" | wc -l
redis-cli keys "session:*" | wc -l
```

### 4.3 Impactos aceitos durante Redis down

| Dado | TTL | Impacto | Fallback |
|---|---|---|---|
| `session:*` | 24h | Usuários refazem login | Nenhum (aceito) |
| `hitl:*` | 24h | Aprovações não persistem | Fallback automático para PostgreSQL |
| `rag_cache:*` | 6h | Respostas mais lentas | Recalculado on-demand |
| Rate limiting | — | Desativado | Monitorar abuso de API LLM |

### 4.4 Reprocessar tasks periódicas perdidas

```bash
# Drift check (se janela 06h Brasília foi perdida):
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  "https://api.lia.wedotalent.com/api/v1/drift/run-batch"

# Verificar aprovações HITL pendentes no PostgreSQL
# (ver RUNBOOK_DEGRADATION.md — seção "HITL Drenagem da Fila")
```

---

## 5. Procedimento de Recuperação de LLM (Anthropic down)

### 5.1 Fallback automático (OpenAI)

O sistema possui fallback automático via `CircuitBreaker`. Se `ANTHROPIC_CIRCUIT` abre:
- OpenAI assume automaticamente como provider secundário
- Monitorar: Grafana `/d/llm-costs` → filtrar `provider=openai`

### 5.2 Se ambos LLMs indisponíveis

```bash
# Ativar modo simplificado (respostas sem LLM)
kubectl set env deployment/lia-backend LLM_FALLBACK_SIMPLIFIED=true
# Ou: editar .env → LLM_FALLBACK_SIMPLIFIED=true → docker-compose up -d
```

### 5.3 Resetar circuit manualmente (se não fechar automaticamente)

```bash
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.lia.wedotalent.com/api/v1/admin/circuit-breakers/ANTHROPIC_CIRCUIT/reset
```

---

## 6. Comunicação Durante Incidente

| Papel | Contato | Quando acionar |
|---|---|---|
| SRE on-call | Slack #incidents | L3+ imediatamente |
| DPO | lgpd@wedotalent.com | Dados pessoais afetados (LGPD Art. 48) |
| BCB/Compliance | compliance@wedotalent.com | Dados financeiros afetados |
| Neon Support | https://neon.tech/support | DB totalmente indisponível |
| WorkOS Support | https://status.workos.com | WORKOS_CIRCUIT aberto |

**Canal principal de incidentes:** Slack `#incidents`

**Comunicação com usuários:**
- L3: notificação Bell interna ("IA em modo de backup")
- L4: status page pública + email para clientes afetados

---

## 7. Checklist Pós-Recuperação

- [ ] Verificar integridade dos dados (contagem comparativa pré/pós incidente)
- [ ] Confirmar que OTEL traces estão chegando ao Grafana
- [ ] Confirmar que todos os jobs Celery Beat estão rodando
- [ ] Verificar logs de auditoria SOX continuam sendo gravados (`audit_decisions` count crescendo)
- [ ] Testar 3 fluxos críticos end-to-end: login, criação de vaga, triagem WSI
- [ ] Verificar drift: `GET /api/v1/drift/status` para empresas ativas
- [ ] Se ativado modo simplificado: remover `LLM_FALLBACK_SIMPLIFIED`
- [ ] Se dados pessoais afetados: confirmar notificação ANPD enviada

---

## 8. Segurança de Backups

- **Todos os backups contêm dados pessoais (LGPD)** — criptografia obrigatória
- Criptografar: `openssl enc -aes-256-cbc -in backup.dump -out backup.dump.enc`
- Chave de criptografia: AWS Secrets Manager (`lia/backup-encryption-key`)
- Acesso a backups: apenas DBA + DPO (acesso auditado)
- Exclusão de candidatos (LGPD Art. 18): `POST /api/v1/admin/lgpd/run-cleanup`

---

## 9. Teste de DR (Schedule)

| Frequência | Escopo | Responsável |
|---|---|---|
| Trimestral | Restore completo de banco em ambiente de staging | Infra |
| Semestral | Simulate Redis down em staging | Infra |
| Anual | Full DR drill (L4 simulado) | Tech Lead + Infra |

**Último teste realizado:** N/A (plano novo — 2026-05-02)
**Próximo teste:** 2026-08-01

---

## 10. Documentos Relacionados

- [RUNBOOK_BACKUP_RECOVERY.md](./RUNBOOK_BACKUP_RECOVERY.md) — Procedimentos detalhados de backup e restore
- [RUNBOOK_INCIDENT_PLAYBOOKS.md](./RUNBOOK_INCIDENT_PLAYBOOKS.md) — Playbooks PB-01 a PB-05 completos
- [RUNBOOK_DEGRADATION.md](./RUNBOOK_DEGRADATION.md) — Níveis de degradação L1-L4, contatos de escalação
- [IncidentResponseService](../app/domains/lgpd/services/incident_response_service.py) — Serviço LGPD para notificação de incidentes

---

*Mantido por: Time de Engenharia + DPO WeDOTalent | Próxima revisão: 2026-08-02*
