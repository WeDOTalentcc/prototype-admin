# Runbook — Degradação Controlada (LIA Platform)

**Versão:** 1.0 | **Data:** 2026-03-15 | **ACH-015**

---

## Visão Geral

Este runbook descreve os procedimentos de resposta a incidentes quando componentes críticos da plataforma LIA entram em modo degradado. O objetivo é manter o serviço disponível para os usuários com funcionalidade reduzida enquanto a causa raiz é investigada.

---

## Níveis de Degradação

| Nível | Descrição | SLA Alvo | Ação Imediata |
|-------|-----------|----------|---------------|
| **L1 — Degradação Leve** | Latência P95 > 2s, Circuit Breaker half-open | 99,5% | Monitorar, não intervir |
| **L2 — Degradação Moderada** | 1 serviço externo down, fallback ativo | 99,0% | Notificar eng. de plantão |
| **L3 — Degradação Severa** | LLM primário down, agentes em fallback | 98,0% | Acionar runbook completo |
| **L4 — Incidente Crítico** | DB ou autenticação indisponível | < 98% | P0 — escalamento imediato |

---

## Circuit Breakers — Estado e Recuperação

### Verificar estado atual

```bash
# Via API admin (requer token de admin)
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.lia.wedotalent.com/api/v1/admin/circuit-breakers

# Via Prometheus (Grafana)
# Métrica: lia_circuit_breaker_state{service="anthropic"}
# 0 = fechado (normal) | 1 = half-open | 2 = aberto (falha)
```

### Reset manual de circuit breaker

```bash
# Reset de um circuit específico
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.lia.wedotalent.com/api/v1/admin/circuit-breakers/ANTHROPIC_CIRCUIT/reset

# Reset de todos os circuits (usar com cautela)
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.lia.wedotalent.com/api/v1/admin/circuit-breakers/reset-all
```

### Circuits disponíveis

| Circuit | Serviço | Threshold | Timeout |
|---------|---------|-----------|---------|
| `ANTHROPIC_CIRCUIT` | Claude LLM primário | 5 falhas/60s | 30s |
| `OPENAI_CIRCUIT` | OpenAI fallback | 5 falhas/60s | 30s |
| `GEMINI_CIRCUIT` | Google Gemini | 5 falhas/60s | 30s |
| `GUPY_CIRCUIT` | Gupy ATS | 3 falhas/60s | 60s |
| `PANDAPE_CIRCUIT` | Pandapé ATS | 3 falhas/60s | 60s |
| `MERGE_CIRCUIT` | Merge.dev | 3 falhas/60s | 60s |
| `MAILGUN_CIRCUIT` | Mailgun email | 5 falhas/60s | 60s |
| `RESEND_CIRCUIT` | Resend email | 5 falhas/60s | 60s |
| `WORKOS_CIRCUIT` | WorkOS SSO | 3 falhas/30s | 120s |

---

## Procedimentos por Componente

### 1. LLM Primário Indisponível (Anthropic)

**Sintomas:** Respostas dos agentes falham; `ANTHROPIC_CIRCUIT` estado=2 (aberto).

**Procedimento:**
1. Verificar status oficial: https://status.anthropic.com
2. Confirmar que `OPENAI_CIRCUIT` está fechado (fallback ativo automaticamente)
3. Notificar usuários via Bell notification: `"IA em modo de backup — respostas podem ser mais lentas"`
4. Se OpenAI também falhar, ativar modo "resposta simplificada":
   ```bash
   # Variável de ambiente para modo de fallback máximo
   kubectl set env deployment/lia-backend LLM_FALLBACK_SIMPLIFIED=true
   ```
5. Monitorar logs: `app/services/llm_service.py` — procurar por `[LLMService] fallback`
6. Quando Anthropic recuperar: circuit fecha automaticamente após 5 chamadas bem-sucedidas

### 2. Banco de Dados Lento (Neon PostgreSQL)

**Sintomas:** Endpoints com latência > 5s; queries timeout.

**Procedimento:**
1. Verificar connection pool: `SELECT count(*) FROM pg_stat_activity WHERE state='active';`
2. Identificar queries lentas: `SELECT * FROM pg_stat_activity WHERE wait_event_type='Lock' ORDER BY wait_start;`
3. Matar conexões travadas se necessário: `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE ...;`
4. Redis cache deve absorver leitura — verificar hit rate: `redis-cli INFO stats | grep keyspace_hits`
5. Se crise: ativar read-only mode via feature flag `DB_READ_ONLY_MODE=true`

### 3. Redis Indisponível

**Sintomas:** Sessões de agentes perdidas; HITL approvals não persistem; rate limiting desativado.

**Procedimento:**
1. Verificar Redis: `redis-cli ping`
2. HITL usa DB como fallback automático (`hitl_service.py` — fallback para PostgreSQL)
3. Sessões WSI serão perdidas — aceitar degradação, não há outro fallback
4. Celery Beat pode falhar — tasks agendadas não serão disparadas. Verificar:
   ```bash
   celery -A app.core.celery_app inspect active
   ```
5. Restaurar Redis da snapshot mais recente se tempo de inatividade > 30min

### 4. Celery Workers Indisponíveis

**Sintomas:** Jobs de drift não rodam; follow-up WSI parado; briefings não enviados.

**Procedimento:**
1. Verificar workers: `celery -A app.core.celery_app inspect ping`
2. Verificar fila RabbitMQ:
   ```bash
   rabbitmqctl list_queues name messages consumers
   ```
3. Restart workers:
   ```bash
   docker-compose restart celery-worker
   docker-compose restart celery-beat
   ```
4. Processar manualmente tarefas críticas via endpoints admin:
   ```bash
   # Rodar drift check manualmente
   curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
     https://api.lia.wedotalent.com/api/v1/drift/run-batch
   ```

### 5. WorkOS SSO Indisponível

**Sintomas:** Usuários não conseguem fazer login; `WORKOS_CIRCUIT` aberto.

**Procedimento:**
1. Verificar: https://status.workos.com
2. Usuários com sessão ativa (JWT válido < 24h) continuam com acesso
3. **Não há fallback de auth** — nova autenticação bloqueada até WorkOS recuperar
4. Notificar usuários via status page
5. Se SLA crítico: contatar WorkOS support imediatamente

---

## Métricas de Monitoramento

### Grafana Dashboards

| Dashboard | URL | Alertas |
|-----------|-----|---------|
| Agent Latency | `/d/agents-overview` | P95 > 5s |
| LLM Costs | `/d/llm-costs` | Custo/hora > $10 |
| Circuit Breakers | `/d/circuit-breakers` | Qualquer estado=2 |
| Drift Detection | `/d/drift-monitoring` | Drift score > 0.3 |

### Alertas Prometheus Críticos

```yaml
# P95 latência agentes
- alert: AgentHighLatency
  expr: histogram_quantile(0.95, lia_agent_request_duration_seconds_bucket) > 10
  for: 5m

# Circuit breaker aberto
- alert: CircuitBreakerOpen
  expr: lia_circuit_breaker_state > 1
  for: 2m

# Taxa de erros alta
- alert: AgentHighErrorRate
  expr: rate(lia_agent_errors_total[5m]) > 0.1
  for: 3m
```

---

## Escalonamento

| Situação | Contato | Canal |
|----------|---------|-------|
| L1-L2 | Eng. de plantão | #alerts-lia (Slack) |
| L3 | Tech Lead | @oncall (PagerDuty) |
| L4 | CTO + Data DPO | Ligação direta |
| Breach LGPD | DPO | lgpd@wedotalent.com (SLA: 2h) |

---

## Circuit Breakers — Operação Detalhada (Sprints AUD-2)

### Diagnóstico rápido

```bash
# Verificar quantos circuits estão abertos
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.lia.wedotalent.com/api/v1/admin/circuit-breakers \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Abertos: {d[\"open_count\"]}/{d[\"total\"]}')"
```

### Interpretação dos estados

| Estado | Código | Significado | Ação |
|--------|--------|-------------|------|
| `closed` | 0 | Normal — chamadas passando | Nenhuma |
| `half_open` | 1 | Testando recuperação | Monitorar logs por 5 min |
| `open` | 2 | Serviço isolado — falhas acumuladas | Verificar serviço externo e resetar quando saudável |

### Reset via API (passo a passo)

```bash
# 1. Verificar estado atual de todos os circuits
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.lia.wedotalent.com/api/v1/admin/circuit-breakers

# 2. Reset de circuit específico (somente após confirmar serviço externo operacional)
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.lia.wedotalent.com/api/v1/admin/circuit-breakers/{NOME_CIRCUIT}/reset
# Exemplo: .../ANTHROPIC_CIRCUIT/reset

# 3. Reset de emergência — todos os circuits
# ATENÇÃO: usar apenas se tiver certeza de que todos os serviços externos estão OK
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.lia.wedotalent.com/api/v1/admin/circuit-breakers/reset-all
```

### Checklist antes de resetar um circuit

- [ ] Verificar status page do serviço externo (Anthropic, Mailgun, etc.)
- [ ] Confirmar que o problema de infraestrutura foi resolvido
- [ ] Ter alguém monitorando logs por 5 min após o reset
- [ ] Registrar a ação no canal #incidents (hora, circuit, responsável)

### Resposta esperada após reset bem-sucedido

```json
{
  "circuit": "ANTHROPIC_CIRCUIT",
  "action": "reset",
  "new_state": "closed"
}
```

---

## Drift Detection — Interpretação e Resposta

### Níveis de alerta

| `alert_level` | Triggers disparados | Ação |
|--------------|---------------------|------|
| `ok` | 0 | Nenhuma — sistema saudável |
| `warning` | 1 | Investigar o trigger específico; notificação Bell automática |
| `critical` | 2 ou mais | Escalonamento imediato; notificação Bell+Teams automática |

**Nota:** Na CLAUDE.md o campo é descrito como `"warning"` (1 trigger) e `"urgent"` (2+ triggers). A API retorna `"critical"` para 2+ triggers. Ambos os termos são usados na documentação de forma intercambiável para o mesmo nível de severidade máxima.

### Os 4 triggers de drift

| Trigger | Métrica | Threshold | Interpretação |
|---------|---------|-----------|---------------|
| `score_drift` | Variação do score médio WSI | > 0,5 pts | LLM calibrando diferente — revisar prompt de avaliação |
| `approval_drift` | Variação da taxa de aprovação | > 10 p.p. | Mudança de perfil de candidatos ou critério de vaga |
| `cost_drift` | Variação do custo médio por avaliação | > 20% | Possível loop de LLM ou mudança de modelo |
| `latency_drift` | Variação do P95 de latência | > 50% | Degradação de infraestrutura ou prompts mais longos |

### Resposta a alerta WARNING (1 trigger)

```bash
# 1. Verificar qual trigger disparou
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  "https://api.lia.wedotalent.com/api/v1/drift/status?company_id=<UUID>"

# 2. Ver campos baseline_value, recent_value, delta no trigger ativo
# 3. Se for score_drift: comparar últimas avaliações com a baseline
# 4. Monitorar nas próximas 24h — se resolver sozinho, apenas documentar
```

### Resposta a alerta URGENT/CRITICAL (2+ triggers)

```bash
# 1. Executar diagnóstico completo
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  "https://api.lia.wedotalent.com/api/v1/drift/status?company_id=<UUID>"

# 2. Pausar avaliações automáticas via feature flag (se disponível)
# 3. Notificar Tech Lead e DPO (dados afetados = compliance)
# 4. Rodar drift check em batch para verificar se é isolado ou sistêmico
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  "https://api.lia.wedotalent.com/api/v1/drift/run-batch?notify_user_id=<USER_ID>"

# 5. Verificar LangSmith por outputs anômalos de LLM
```

### Drift provocado por incidente

Se houve incidente de infraestrutura (LLM down, Redis down, etc.) e o drift foi detectado nesse período, o drift pode ser espúrio:

1. Verificar se `recent_window_start` coincide com o período do incidente
2. Se sim: aguardar nova janela de 7 dias — drift deve se resolver
3. Documentar correlação no post-mortem

---

## Bias Audit — Falha de Snapshot

### Quando um snapshot falha

O snapshot de bias audit (`BiasAuditSnapshot`) é gravado após cada avaliação de adverse impact. Uma falha não impede a resposta da API — é best-effort.

**Sintomas de falha de snapshot:**

```
ERROR [bias_audit_service] save_snapshot error: <mensagem>
```

### Diagnóstico

```bash
# Verificar histórico de snapshots de uma vaga
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
     -H "X-Company-ID: <UUID>" \
  "https://api.lia.wedotalent.com/api/v1/bias-audit/job/<JOB_ID>/history"

# Resposta esperada: { "job_id": "...", "history": [...], "count": N }
# Se count=0 e a vaga tem candidatos avaliados: snapshots não foram gravados
```

### Causas comuns e resolução

| Causa | Resolução |
|-------|-----------|
| Tabela `bias_audit_snapshots` inexistente | Verificar migration `018_add_bias_audit_snapshot.py`: `alembic history | grep 018` |
| Conexão DB instável | O service usa try/except — reprocessar manualmente quando DB estabilizar |
| `company_id` ausente no header | Endpoint exige `X-Company-ID` — verificar client que chama |

### Reprocessar snapshot manualmente

```bash
# A auditoria ainda funciona (retorna dados em tempo real mesmo sem snapshot)
# Para forçar nova gravação, basta chamar o endpoint novamente:
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
     -H "X-Company-ID: <UUID>" \
  "https://api.lia.wedotalent.com/api/v1/bias-audit/job/<JOB_ID>"
# O save_snapshot() é chamado internamente a cada GET
```

### Impacto regulatório de gaps no histórico

Gaps de snapshot impactam auditabilidade SOX/ISO 27001. Se o gap durou mais de 24h:

1. Registrar o período sem snapshot no log de conformidade
2. Notificar Compliance (`compliance@wedotalent.com`)
3. Verificar se alguma avaliação foi feita no período sem snapshot

---

## HITL — Drenagem da Fila de Aprovações Pendentes

### Verificar aprovações pendentes

```bash
# Verificar aprovação pendente por thread_id específico
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.lia.wedotalent.com/api/v1/hitl/<THREAD_ID>/pending

# Resposta: { "thread_id": "...", "pending": { pending_id, action, domain, ... } }
# Se "pending" == null: não há aprovação pendente para este thread
```

### Quando a fila acumula (Redis ou API lenta)

O HITL usa Redis como fast-path e PostgreSQL como fallback. Em situação de degradação:

1. Agentes parados aguardando aprovação não expiram — ficam bloqueados indefinidamente
2. Se Redis caiu e o fallback para DB estava ativo, as aprovações estão em `hitl_requests` no banco

```sql
-- Verificar aprovações pendentes no DB (conectar via psql)
SELECT id, thread_id, domain, company_id, created_at
FROM hitl_requests
WHERE status = 'pending'
ORDER BY created_at ASC;
```

### Aprovar ou rejeitar via API

```bash
# Aprovar uma ação pendente
curl -X POST \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pending_id": "<PENDING_ID>", "approved": true, "comment": "Aprovado em massa — incidente"}' \
  https://api.lia.wedotalent.com/api/v1/hitl/<THREAD_ID>/approve

# Rejeitar
curl -X POST \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pending_id": "<PENDING_ID>", "approved": false, "comment": "Rejeitado preventivamente durante incidente"}' \
  https://api.lia.wedotalent.com/api/v1/hitl/<THREAD_ID>/approve
```

### Drenagem em massa (procedimento de emergência)

Se houver dezenas de aprovações acumuladas após um incidente:

1. Listar todos os thread_ids pendentes via SQL (acima)
2. Priorizar por `domain`: `pipeline_transition` > `sourcing_outreach` > `communication`
3. Para abordagens de sourcing represadas (baixo risco), aprovar em lote com comentário de rastreabilidade
4. Para transições de pipeline, revisar individualmente
5. Documentar cada aprovação em massa no `audit_decisions` via `audit_service.log_decision()`

---

## PolicyEngine — Revertendo Setor Incorreto

### Quando aplicar template de setor errado

O endpoint `POST /api/v1/policy-engine/apply-sector/{company_id}?sector=` é idempotente — pode ser chamado novamente com o setor correto para sobrescrever.

```bash
# 1. Verificar qual setor está atualmente configurado
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
     -H "X-Company-ID: <COMPANY_UUID>" \
  "https://api.lia.wedotalent.com/api/v1/policy-engine"

# 2. Aplicar o setor correto (sobrescreve o anterior)
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  "https://api.lia.wedotalent.com/api/v1/policy-engine/apply-sector/<COMPANY_UUID>?sector=tech"
# Setores válidos: tech | varejo | logistica | financeiro | saude | rpo
```

### Setores disponíveis e suas características

| Setor | Uso típico | Diferencial |
|-------|-----------|-------------|
| `tech` | Empresas de tecnologia | Critérios técnicos, auto-aprovação de sourcing |
| `varejo` | Varejo e e-commerce | Alto volume, triagem acelerada |
| `logistica` | Logística e supply chain | Critérios físicos/operacionais habilitados |
| `financeiro` | Bancos, fintechs | BCB 498, critérios regulatórios mais rígidos |
| `saude` | Hospitais, clínicas | CRM/CRN verificação habilitada |
| `rpo` | Consultorias de RH (RPO) | Multi-cliente, whitelabel |

### Reverter para configuração padrão (sem setor)

Não existe endpoint de "limpar setor". Para reverter ao comportamento padrão:

```bash
# Aplicar setor mais genérico como aproximação
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  "https://api.lia.wedotalent.com/api/v1/policy-engine/apply-sector/<COMPANY_UUID>?sector=tech"

# Ou editar diretamente a CompanyHiringPolicy via DB (somente DBA)
# UPDATE company_hiring_policies SET automation_rules='{}', screening_rules='{}'
# WHERE company_id = '<UUID>';
```

### Auditoria de mudança de setor

Cada chamada a `apply-sector` é auditada via `audit_service.log_decision()`. Para ver o histórico:

```bash
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
     -H "X-Company-ID: <COMPANY_UUID>" \
  "https://api.lia.wedotalent.com/api/v1/policy-engine/evaluation-logs?action=apply_sector_defaults"
```

---

## Celery Workers — Diagnóstico de Tasks Presas

### Verificar estado dos workers

```bash
# Ping em todos os workers ativos
celery -A app.core.celery_app inspect ping

# Listar tasks ativas (em execução agora)
celery -A app.core.celery_app inspect active

# Listar tasks reservadas (na fila, aguardando worker)
celery -A app.core.celery_app inspect reserved

# Listar tasks agendadas (Celery Beat)
celery -A app.core.celery_app inspect scheduled
```

### Tasks críticas e seus schedules

| Task Celery | Schedule (Beat) | Timeout esperado |
|-------------|----------------|-----------------|
| `drift.run_batch` | Diário às 06h Brasília (09h UTC) | < 5 min |
| `briefing.send_daily` | Diário às 09h UTC (06h Brasília) | < 3 min |
| `followup.process_pending` | Horário (minuto 0) | < 2 min |
| `wsi.check_abandoned` | A cada 4h (minuto 0) | < 2 min |
| `lgpd-cleanup-daily` | Diário às 05h UTC | < 10 min |

### Diagnosticar task presa

```bash
# Verificar fila no RabbitMQ
rabbitmqctl list_queues name messages consumers

# Se fila `celery` tem mensagens mas consumers=0 → workers mortos
# Restart:
docker-compose restart celery-worker
docker-compose restart celery-beat

# Verificar logs do worker
docker-compose logs --tail=100 celery-worker
```

### Task presa sem resposta (STARTED há mais de 30 min)

```bash
# Listar tasks ativas com detalhes
celery -A app.core.celery_app inspect active --timeout=10

# Revogar task específica (mata a execução)
celery -A app.core.celery_app control revoke <TASK_ID> --terminate

# Se worker não responde — forçar restart
docker-compose kill celery-worker && docker-compose up -d celery-worker
```

### Rodar tasks críticas manualmente (quando Beat está down)

```bash
# Drift check manual
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  "https://api.lia.wedotalent.com/api/v1/drift/run-batch?notify_user_id=<USER_ID>"

# LGPD cleanup manual
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  "https://api.lia.wedotalent.com/api/v1/admin/lgpd/run-cleanup"
```

### Sintomas de task presa vs. worker morto

| Sintoma | Diagnóstico | Ação |
|---------|------------|------|
| Fila RabbitMQ crescendo, workers respondendo ao ping | Task presa em execução | Revogar task + investigar logs |
| Workers não respondem ao ping | Workers mortos | Restart docker-compose |
| Workers respondem, fila vazia, tarefa não executou | Beat parado | Restart celery-beat |
| Workers respondem, Beat ativo, erro no log | Bug na task | Corrigir código + redeploy |

---

## Pós-Incidente

1. Preencher post-mortem em 48h (template: `docs/templates/post-mortem.md`)
2. Atualizar este runbook com novos aprendizados
3. Criar ticket de melhoria no backlog se causa raiz for sistêmica
4. Verificar se drift foi detectado durante incidente: `GET /api/v1/drift/status`
5. Verificar se alguma aprovação HITL ficou pendente durante o incidente
6. Confirmar que todos os circuit breakers voltaram ao estado `closed`
7. Verificar histórico de snapshots de bias audit para gaps no período do incidente

---

*Mantido por: Time de Engenharia WeDOTalent | Versão: 2.0 | Próxima revisão: 2026-06-15*
