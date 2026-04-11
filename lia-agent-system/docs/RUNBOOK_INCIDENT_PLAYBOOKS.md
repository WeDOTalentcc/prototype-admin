# Runbook — Playbooks de Incidentes (LIA Platform)

**Versão:** 1.0 | **Data:** 2026-03-15 | **C5**

Este documento contém playbooks passo a passo para os 5 cenários de incidente mais críticos da plataforma LIA. Cada playbook segue o formato: **Detecção → Triagem → Contenção → Resolução → Pós-Incidente**.

Para referência de níveis de degradação (L1–L4) e contatos de escalonamento, consulte `docs/RUNBOOK_DEGRADATION.md`.

---

## Índice

1. [PB-01 — LLM Primário Down (Anthropic)](#pb-01--llm-primário-down-anthropic)
2. [PB-02 — Banco de Dados Indisponível (Neon PostgreSQL)](#pb-02--banco-de-dados-indisponível-neon-postgresql)
3. [PB-03 — Redis Indisponível](#pb-03--redis-indisponível)
4. [PB-04 — Circuit Breaker em OPEN](#pb-04--circuit-breaker-em-open)
5. [PB-05 — Drift Alerta URGENT/CRITICAL](#pb-05--drift-alerta-urgentcritical)

---

## PB-01 — LLM Primário Down (Anthropic)

**Nível de degradação:** L3 — Degradação Severa
**SLA alvo:** 98,0% disponibilidade
**Tempo máximo para contenção:** 15 minutos

### 1. Detecção

Alertas que disparam este playbook:

- Prometheus: `CircuitBreakerOpen{circuit="ANTHROPIC_CIRCUIT"}` por > 2 min
- Grafana: Dashboard `/d/circuit-breakers` — estado=2 para `ANTHROPIC_CIRCUIT`
- Usuários reportando: "Agente LIA não responde" ou timeouts em triagem WSI
- Log: `[LLMService] anthropic request failed` repetidamente

### 2. Triagem (< 5 min)

```bash
# Passo 2.1 — Verificar se é problema da Anthropic ou local
curl -s https://status.anthropic.com/api/v2/status.json | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(d['status']['description'])"

# Passo 2.2 — Confirmar estado do circuit
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.lia.wedotalent.com/api/v1/admin/circuit-breakers \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
ac = d['circuits'].get('ANTHROPIC_CIRCUIT', {})
oc = d['circuits'].get('OPENAI_CIRCUIT', {})
print(f'Anthropic: {ac.get(\"state\",\"?\")} | OpenAI fallback: {oc.get(\"state\",\"?\")}')
"

# Passo 2.3 — Verificar se OpenAI está respondendo como fallback
# Se OPENAI_CIRCUIT=closed: fallback ativo automaticamente → L3 gerenciável
# Se OPENAI_CIRCUIT=open também: escalonamento imediato → L4
```

### 3. Contenção

**Cenário A — OpenAI fallback operacional (situação mais comum)**

```bash
# Notificar usuários via notificação Bell (se houver endpoint de broadcast)
# Mensagem: "IA em modo de backup — respostas podem ser mais lentas que o normal"

# Monitorar taxa de erros no fallback:
# Grafana: /d/llm-costs → filtrar por provider=openai
```

**Cenário B — Ambos Anthropic e OpenAI indisponíveis**

```bash
# Ativar modo simplificado (respostas sem LLM)
kubectl set env deployment/lia-backend LLM_FALLBACK_SIMPLIFIED=true

# Ou via variável de ambiente no docker-compose:
# Editar .env → LLM_FALLBACK_SIMPLIFIED=true → docker-compose up -d
```

### 4. Resolução

```bash
# Quando Anthropic recuperar (verificar status.anthropic.com):

# Passo 4.1 — O circuit fecha automaticamente após 5 chamadas bem-sucedidas
# Aguardar 5-10 minutos monitorando logs

# Passo 4.2 — Se não fechar automaticamente, resetar manualmente
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.lia.wedotalent.com/api/v1/admin/circuit-breakers/ANTHROPIC_CIRCUIT/reset

# Passo 4.3 — Confirmar que circuit está CLOSED
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.lia.wedotalent.com/api/v1/admin/circuit-breakers \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d['circuits']['ANTHROPIC_CIRCUIT']['state'])  # deve imprimir 'closed'
"

# Passo 4.4 — Remover modo simplificado se ativado
kubectl set env deployment/lia-backend LLM_FALLBACK_SIMPLIFIED-
```

### 5. Pós-Incidente

- [ ] Verificar se avaliações WSI foram afetadas (resultados no período do incidente)
- [ ] Checar drift: `GET /api/v1/drift/status?company_id=<UUID>` — o incidente pode ter provocado `cost_drift` ou `latency_drift`
- [ ] Calcular custo extra do fallback OpenAI: dashboard `/d/llm-costs`
- [ ] Documentar em post-mortem: duração, número de avaliações afetadas, custo extra

---

## PB-02 — Banco de Dados Indisponível (Neon PostgreSQL)

**Nível de degradação:** L4 — Incidente Crítico
**SLA alvo:** < 98% (P0)
**Tempo máximo para contenção:** 5 minutos | Tempo máximo para resolução: 4 horas

### 1. Detecção

- Prometheus: `up{job="lia-backend"} == 0` ou `http_request_duration_seconds{quantile="0.95"} > 30`
- Endpoints retornando HTTP 500 ou 503 em massa
- Log: `sqlalchemy.exc.OperationalError: could not connect to server`
- Celery Beat: tasks falhando com erro de DB

### 2. Triagem (< 3 min)

```bash
# Passo 2.1 — Testar conexão direta ao Neon
psql "$DATABASE_URL" -c "SELECT 1;" 2>&1

# Passo 2.2 — Verificar painel Neon
# https://console.neon.tech/app/projects → verificar status do projeto

# Passo 2.3 — Verificar se é connection pool esgotado
psql "$DATABASE_URL" -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"
# Se active > 90: pool esgotado (não é down, é sobrecarga)
```

### 3. Contenção

**Cenário A — DB realmente indisponível (Neon side)**

```bash
# Notificar usuários: "Plataforma em manutenção emergencial"
# Acionar Neon Support: https://neon.tech/support

# Verificar se há branch de DR disponível:
curl -H "Authorization: Bearer $NEON_API_KEY" \
  "https://console.neon.tech/api/v2/projects/$NEON_PROJECT_ID/branches"
```

**Cenário B — Pool de conexões esgotado**

```bash
# Reiniciar aplicação para liberar conexões
docker-compose restart lia-backend

# Matar conexões idle no DB
psql "$DATABASE_URL" -c "
  SELECT pg_terminate_backend(pid)
  FROM pg_stat_activity
  WHERE state = 'idle'
    AND state_change < NOW() - INTERVAL '5 minutes'
    AND pid <> pg_backend_pid();
"

# Ativar modo read-only para reduzir carga de escrita
# Editar .env → DB_READ_ONLY_MODE=true → docker-compose up -d
```

**Cenário C — Queries lentas travando o sistema**

```bash
# Identificar queries bloqueadas
psql "$DATABASE_URL" -c "
  SELECT pid, query, wait_event_type, wait_event, state, query_start
  FROM pg_stat_activity
  WHERE wait_event_type = 'Lock'
  ORDER BY query_start;
"

# Matar queries bloqueadas específicas
psql "$DATABASE_URL" -c "SELECT pg_terminate_backend(<PID>);"
```

### 4. Resolução

```bash
# Passo 4.1 — Confirmar que DB responde
psql "$DATABASE_URL" -c "SELECT count(*) FROM candidates LIMIT 1;"

# Passo 4.2 — Verificar integridade básica das tabelas críticas
python3 -c "
import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def check():
    async with AsyncSessionLocal() as db:
        tables = ['candidates', 'job_vacancies', 'companies', 'audit_decisions']
        for t in tables:
            r = await db.execute(text(f'SELECT count(*) FROM {t}'))
            print(f'  {t}: {r.scalar()} registros')

asyncio.run(check())
"

# Passo 4.3 — Verificar migrations aplicadas
alembic current
alembic history --verbose | head -5

# Passo 4.4 — Remover modo read-only se ativado
# .env → DB_READ_ONLY_MODE=false → docker-compose up -d
```

### 5. Pós-Incidente

- [ ] Verificar se dados foram perdidos comparando contagem de registros com último backup
- [ ] Se dados pessoais foram afetados: notificar DPO em < 2h (LGPD Art. 48 — 72h ANPD)
- [ ] Verificar tasks Celery que falharam durante o período — reprocessar se necessário
- [ ] Atualizar `docs/RUNBOOK_BACKUP_RECOVERY.md` com aprendizados

---

## PB-03 — Redis Indisponível

**Nível de degradação:** L2-L3 — Degradação Moderada a Severa
**SLA alvo:** 99,0%
**Tempo máximo para contenção:** 5 minutos | Tempo máximo para resolução: 30 minutos

### 1. Detecção

- Log: `redis.exceptions.ConnectionError: Error connecting to Redis`
- HITL: aprovações não persistindo (warning nos logs)
- Sessões WSI: novas sessões não iniciam
- Celery Beat: tasks periódicas não disparando
- Rate limiting: desativado (maior risco de abuso de API)

### 2. Triagem (< 2 min)

```bash
# Passo 2.1 — Verificar Redis
redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD ping
# Resposta esperada: PONG
# Se "Could not connect": Redis down

# Passo 2.2 — Verificar container Redis
docker-compose ps redis
# Se Status != "Up": container parado

# Passo 2.3 — Verificar memória do host
free -h
df -h /var/lib/docker
```

### 3. Contenção

```bash
# Passo 3.1 — Tentar restart simples do container
docker-compose restart redis

# Aguardar 10 segundos
sleep 10
redis-cli ping

# Passo 3.2 — Se restart não resolver, verificar logs
docker-compose logs --tail=50 redis

# Passo 3.3 — Se Redis continua down, verificar impactos:
#   - HITL: fallback automático para PostgreSQL (verificar hitl_service.py)
#   - Sessões WSI: novas sessões serão perdidas (degradação aceita)
#   - Celery Beat: tasks periódicas não disparam → executar manualmente endpoints admin
#   - Rate limiting: desativado → monitorar logs de abuso
```

### 4. Resolução

```bash
# Opção A — Redis reiniciou normalmente
redis-cli ping  # deve retornar PONG
# Verificar que dados críticos foram restaurados (se dump.rdb era recente)
redis-cli info keyspace

# Opção B — Redis corrompido, restaurar de backup
docker-compose stop redis
cp backup/redis-TIMESTAMP.rdb /data/redis/dump.rdb
docker-compose start redis
redis-cli ping

# Verificar que chaves HITL foram restauradas (se inatividade < 24h)
redis-cli keys "hitl:*" | wc -l

# Passo 4.1 — Reprocessar tasks periódicas que não rodaram
# Drift check (se janela de 06h Brasília foi perdida):
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  "https://api.lia.wedotalent.com/api/v1/drift/run-batch"

# Passo 4.2 — Verificar aprovações HITL que ficaram pendentes
# Ver seção "HITL — Drenagem da Fila" no RUNBOOK_DEGRADATION.md
```

### 5. Pós-Incidente

- [ ] Verificar duração da inatividade do Redis
- [ ] Se > 30 min: revisar aprovações HITL pendentes no PostgreSQL
- [ ] Se sessões WSI foram perdidas: notificar candidatos afetados via email
- [ ] Considerar Redis Sentinel ou Redis Cluster para alta disponibilidade
- [ ] Verificar se rate limiting desativado causou picos de chamada LLM (custo)

---

## PB-04 — Circuit Breaker em OPEN

**Nível de degradação:** L2 (1 circuit) a L3 (múltiplos circuits)
**SLA alvo:** Dependente do serviço afetado

### 1. Detecção

- Grafana: Dashboard `/d/circuit-breakers` — qualquer estado=2
- Prometheus: `lia_circuit_breaker_state > 1` por > 2 min
- Log: `[CircuitBreaker] <NOME> OPEN — chamadas bloqueadas`

### 2. Triagem (< 5 min)

```bash
# Passo 2.1 — Identificar quais circuits estão abertos
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.lia.wedotalent.com/api/v1/admin/circuit-breakers \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
open_circuits = {k: v for k, v in d['circuits'].items() if v.get('state') == 'open'}
print(f'Circuits abertos: {list(open_circuits.keys())}')
for name, info in open_circuits.items():
    print(f'  {name}: failure_count={info.get(\"failure_count\", \"?\")}')
"

# Passo 2.2 — Mapear impacto por circuit
# ANTHROPIC_CIRCUIT aberto → ver PB-01
# MAILGUN_CIRCUIT / RESEND_CIRCUIT aberto → emails não são enviados
# GUPY_CIRCUIT / PANDAPE_CIRCUIT aberto → sincronização ATS parada
# WORKOS_CIRCUIT aberto → novos logins bloqueados (crítico!)
```

### 3. Contenção por tipo de circuit

**Circuits de email (MAILGUN_CIRCUIT / RESEND_CIRCUIT)**

```bash
# Verificar status Mailgun: https://status.mailgun.com
# Verificar status Resend: https://status.resend.com

# Se apenas Mailgun aberto: Resend será usado como fallback automático
# Se ambos abertos: emails não estão sendo enviados — usuários não recebem notificações

# Comunicar internamente sobre impacto em notificações
```

**Circuits de ATS (GUPY_CIRCUIT / PANDAPE_CIRCUIT / MERGE_CIRCUIT)**

```bash
# Verificar status dos sistemas ATS:
# Gupy: https://status.gupy.io
# Pandapé: https://status.pandape.com.br

# Impacto: sincronização de candidatos/vagas pausada
# Não afeta operação interna da plataforma LIA
# Vagas continuam funcionando com dados locais
```

**Circuit de SSO (WORKOS_CIRCUIT) — CRÍTICO**

```bash
# Verificar: https://status.workos.com

# Impacto IMEDIATO: usuários com JWT expirado não conseguem renovar sessão
# Usuários com JWT válido (< 24h) continuam com acesso

# Comunicar via status page
# Contatar WorkOS support imediatamente se SLA crítico
```

### 4. Resolução

```bash
# Passo 4.1 — Confirmar que serviço externo está operacional
# (verificar status page do fornecedor)

# Passo 4.2 — Verificar se circuit já fechou automaticamente (half-open → closed)
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.lia.wedotalent.com/api/v1/admin/circuit-breakers \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'Abertos ainda: {d[\"open_count\"]}')
"

# Passo 4.3 — Se não fechou automaticamente, resetar manualmente
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.lia.wedotalent.com/api/v1/admin/circuit-breakers/<CIRCUIT_NAME>/reset

# Passo 4.4 — Monitorar por 5 min após reset para garantir que não reabre
```

### 5. Pós-Incidente

- [ ] Identificar causa raiz (timeout? mudança de API? rate limiting do fornecedor?)
- [ ] Revisar threshold do circuit se houve muitos falsos positivos
- [ ] Verificar se mensagens em fila (emails, sync ATS) precisam ser reprocessadas
- [ ] Atualizar tabela de circuits no `RUNBOOK_DEGRADATION.md` se thresholds mudaram

---

## PB-05 — Drift Alerta URGENT/CRITICAL

**Nível de degradação:** L2-L3 (dependendo do trigger)
**Responsável principal:** Tech Lead + DPO (dados afetados)

> **Nota:** "URGENT" e "CRITICAL" são termos equivalentes neste contexto. A API retorna `alert_level: "critical"` quando 2+ triggers disparam simultaneamente. A notificação automática usa "URGENT" no título Bell+Teams.

### 1. Detecção

- Bell notification: `"[DRIFT URGENT] 2 triggers em empresa <NOME>"`
- Teams: Card de alerta no canal #alerts-lia com `alert_level=critical`
- Grafana: Dashboard `/d/drift-monitoring` — drift_score > 0.3

### 2. Triagem (< 10 min)

```bash
# Passo 2.1 — Obter detalhes completos do drift
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  "https://api.lia.wedotalent.com/api/v1/drift/status?company_id=<COMPANY_UUID>" \
  | python3 -m json.tool

# Verificar os campos críticos:
# - alert_level: "critical" (2+ triggers)
# - evaluated_at: timestamp da avaliação
# - recent_window_start: início da janela recente (últimos 7 dias)
# - baseline_window_start: início da baseline (7-14 dias atrás)
# - triggers[].triggered: true = aquele trigger específico disparou
# - triggers[].delta: magnitude da variação

# Passo 2.2 — Rodar drift check em batch para verificar se é isolado
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  "https://api.lia.wedotalent.com/api/v1/drift/run-batch" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'Verificadas: {d[\"checked\"]} empresas | Com drift: {d[\"drifted\"]} | Erros: {d[\"errors\"]}')
"
# Se drifted > 1: drift sistêmico — investigar mudança de infraestrutura/modelo
# Se drifted = 1: drift isolado — investigar a empresa específica
```

### 3. Interpretação e Contenção por Trigger

**score_drift (variação score médio > 0,5 pts)**

```
Causas comuns:
  - Mudança de prompt de avaliação sem versionamento
  - Mudança de modelo LLM (ex: nova versão do Claude)
  - Perfil de candidatos da empresa mudou significativamente
  - Viés sendo introduzido ou removido do prompt

Ação imediata:
  1. Verificar logs de avaliação: grep "[rubric_evaluation]" | tail -100
  2. Comparar últimas 10 avaliações com baseline
  3. Se mudança de prompt foi feita: rollback no código se necessário
```

**approval_drift (variação taxa de aprovação > 10 p.p.)**

```
Causas comuns:
  - Critérios da vaga foram alterados
  - Perfil demográfico dos candidatos mudou (anomalia)
  - Bug em critério de filtragem

Ação imediata:
  1. Verificar audit_decisions para a empresa no período
  2. Checar se algum recruiter alterou critérios de vaga recentemente
  3. Rodar bias audit para verificar se aprovação mudou por dimensão demográfica
```

```bash
# Rodar bias audit para a vaga/empresa afetada
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
     -H "X-Company-ID: <COMPANY_UUID>" \
  "https://api.lia.wedotalent.com/api/v1/bias-audit/job/<JOB_ID>"
```

**cost_drift (variação custo > 20%)**

```
Causas comuns:
  - Prompts cresceram em tamanho (tokens extras)
  - Loop de LLM (agente chamando LLM repetidamente sem terminar)
  - Mudança de modelo de pricing (novo contrato Anthropic)
  - Explosão de volume de candidatos

Ação imediata:
  1. Verificar dashboard /d/llm-costs por período
  2. Verificar se há agente em loop: grep "[LLMService]" | wc -l por hora
  3. Se loop detectado: reiniciar worker celery + verificar fila
```

**latency_drift (variação P95 > 50%)**

```
Causas comuns:
  - Degradação de infraestrutura (Neon lento, Redis lento)
  - Prompts maiores aumentando tempo de geração LLM
  - Circuit breaker abrindo e causando timeouts antes do circuit fechar

Ação imediata:
  1. Verificar Grafana: /d/agents-overview → P95 latência
  2. Verificar se DB está lento: pg_stat_activity
  3. Correlacionar com events de circuit breaker no período
```

### 4. Escalonamento por Severidade

| Combinação de triggers | Escalonamento | Prazo |
|------------------------|---------------|-------|
| `score_drift` + `approval_drift` | Tech Lead + DPO | 2h |
| `score_drift` + `cost_drift` | Tech Lead + CTO | 4h |
| `approval_drift` + qualquer outro | Tech Lead + DPO + Compliance | 2h |
| Qualquer combinação em múltiplas empresas | CTO | 1h |

> Mudança em `approval_drift` pode indicar discriminação algorítmica — acionar DPO obrigatório (EU AI Act Art. 9, LGPD Art. 20).

### 5. Resolução

```bash
# Após identificar e corrigir causa raiz:

# Passo 5.1 — Aguardar próxima janela de avaliação (drift é calculado em janelas de 7 dias)
# Não há como forçar reset do drift — aguardar os dados da janela recente normalizarem

# Passo 5.2 — Verificar que nova avaliação não dispara mais:
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  "https://api.lia.wedotalent.com/api/v1/drift/status?company_id=<COMPANY_UUID>" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'alert_level: {d[\"alert_level\"]}')
print(f'drift_detected: {d[\"drift_detected\"]}')
"
```

### 6. Pós-Incidente

- [ ] Documentar qual trigger disparou, causa raiz, e correção aplicada
- [ ] Se `approval_drift` estava envolvido: salvar relatório de bias audit do período
- [ ] Atualizar ou criar regra de CI para prevenir regressão
- [ ] Verificar se snapshots de bias audit foram gravados durante o período de drift
- [ ] Notificar DPO se empresa afetada é do setor financeiro (BCB 498)

---

## Referências Rápidas

### Endpoints de diagnóstico (todos requerem `Authorization: Bearer $ADMIN_TOKEN`)

| Ação | Endpoint |
|------|---------|
| Status todos os circuits | `GET /api/v1/admin/circuit-breakers` |
| Reset circuit específico | `POST /api/v1/admin/circuit-breakers/{name}/reset` |
| Reset todos os circuits | `POST /api/v1/admin/circuit-breakers/reset-all` |
| Status de drift por empresa | `GET /api/v1/drift/status?company_id=<UUID>` |
| Rodar drift batch | `POST /api/v1/drift/run-batch` |
| Auditoria de viés por vaga | `GET /api/v1/bias-audit/job/{job_id}` |
| Histórico de snapshots bias | `GET /api/v1/bias-audit/job/{job_id}/history` |
| Aprovação HITL pendente | `GET /api/v1/hitl/{thread_id}/pending` |
| Aprovar/rejeitar HITL | `POST /api/v1/hitl/{thread_id}/approve` |
| Aplicar setor PolicyEngine | `POST /api/v1/policy-engine/apply-sector/{company_id}` |
| Status LGPD cleanup | `GET /api/v1/admin/lgpd/cleanup-status` |

### Canais de status externos

| Serviço | Status Page |
|---------|------------|
| Anthropic | https://status.anthropic.com |
| WorkOS | https://status.workos.com |
| Mailgun | https://status.mailgun.com |
| Neon | https://neonstatus.com |
| Gupy | https://status.gupy.io |

---

*Mantido por: Time de Engenharia WeDOTalent | Próxima revisão: 2026-06-15*
