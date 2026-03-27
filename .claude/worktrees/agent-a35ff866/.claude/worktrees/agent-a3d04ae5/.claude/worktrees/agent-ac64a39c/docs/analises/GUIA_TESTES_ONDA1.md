# Guia de Testes — Camada de Inteligência LIA
**Data:** 07/03/2026
**Sprints:**
- **Onda 1:** 1A (stage_entered_at) · 1B (Pipeline Velocity) · 1C (Zero-Touch Scheduling) · 1E (Silver Medalists)
- **Onda 2:** 2A (Recruiter Intelligence) · 2B (Early Warning Score) · 2C (Journey Intelligence) · 2D (Recruiter Benchmark)
- **Onda 3:** 3A (Pipeline Prediction)

> **Nota:** Sprint 1D (Interview Kit + Reliability) reservado para evolução futura do módulo de entrevistas.

---

## Sprint 1A — `stage_entered_at`

### O que faz
Registra o momento exato em que um candidato entrou na etapa atual do pipeline.
Antes só existia `updated_at`, que mudava em qualquer alteração (ex: editar uma nota).
Agora `stage_entered_at` muda **somente** quando o candidato troca de etapa.

### Arquivos modificados
- `app/models/candidate.py` — nova coluna no modelo `VacancyCandidate`
- `app/domains/recruiter_assistant/services/pipeline_stage_service.py` — hook na linha 183
- `alembic/versions/023_add_stage_entered_at.py` — migration com backfill e index

### Como testar

**1. Verificar que a coluna existe no banco:**
```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'vacancy_candidates'
  AND column_name = 'stage_entered_at';
```
Esperado: retorna 1 linha com `timestamp without time zone`.

**2. Verificar que o index existe:**
```sql
SELECT indexname FROM pg_indexes
WHERE tablename = 'vacancy_candidates'
  AND indexname = 'ix_vacancy_candidates_stage_entered_at';
```

**3. Testar a regra de negócio — troca de etapa:**
```sql
-- Antes: anotar stage_entered_at atual
SELECT id, stage, stage_entered_at, updated_at
FROM vacancy_candidates
WHERE candidate_id = '<uuid_candidato>';
```
Mova o candidato de etapa (via Kanban drag-drop ou chat com LIA).
```sql
-- Depois: confirmar que stage_entered_at mudou
SELECT id, stage, stage_entered_at, updated_at
FROM vacancy_candidates
WHERE candidate_id = '<uuid_candidato>';
```
✅ `stage_entered_at` deve ter um novo valor (agora).
✅ `updated_at` também deve ter mudado.

**4. Testar que sub-status NÃO muda o stage_entered_at:**
Altere apenas o sub-status de um candidato (sem trocar de etapa).
```sql
SELECT stage, stage_entered_at, updated_at, status
FROM vacancy_candidates
WHERE candidate_id = '<uuid_candidato>';
```
✅ `stage_entered_at` deve permanecer igual.
✅ `updated_at` deve ter mudado.

---

## Sprint 1B — Pipeline Velocity Engine

### O que faz
Calcula quanto tempo cada candidato está em cada etapa, compara com benchmarks
razoáveis para o mercado brasileiro, e detecta gargalos. Gera alertas automáticos
a cada 30 minutos via ProactiveAgentWorker.

### Benchmarks configurados
| Etapa | Limite recomendado |
|-------|-------------------|
| applied / initial / novo | 2 dias |
| screening / triagem | 3 dias |
| interview_hr / entrevista_rh | 5 dias |
| interview_technical / entrevista_tecnica | 7 dias |
| proposal / offer / proposta | 3 dias |
| Qualquer outra etapa | 5 dias |

### Arquivos criados
- `app/services/pipeline_velocity_service.py` — serviço central
- `app/api/v1/pipeline_velocity.py` — endpoints REST
- `app/shared/agents/proactive_worker.py` — novo check `check_velocity_bottleneck`
- `app/domains/recruiter_assistant/agents/kanban_tool_registry.py` — tool `get_pipeline_velocity`
- `plataforma-lia/src/app/api/backend-proxy/pipeline-velocity/route.ts` — proxy FE
- `plataforma-lia/src/app/api/backend-proxy/pipeline-velocity/bottlenecks/route.ts` — proxy FE

### Como testar — endpoints REST

**Métricas de velocidade por vaga:**
```
GET /api/v1/pipeline/velocity?vacancy_id=<uuid>
```
Resposta esperada:
```json
{
  "success": true,
  "data": {
    "vacancy_id": "...",
    "per_stage": {
      "triagem": {
        "avg_days": 4.2,
        "median_days": 3.8,
        "max_days": 9.0,
        "candidate_count": 12,
        "threshold_days": 3,
        "is_bottleneck": true
      }
    },
    "bottleneck_stages": ["triagem"],
    "overall_health": "warning"
  }
}
```

**Candidatos acima do limite agora:**
```
GET /api/v1/pipeline/velocity/bottlenecks?company_id=<uuid>
```
Resposta esperada:
```json
{
  "success": true,
  "total": 3,
  "data": [
    {
      "candidate_name": "João Silva",
      "vacancy_title": "Analista de RH",
      "stage": "triagem",
      "days_in_stage": 7.5,
      "threshold_days": 3,
      "overdue_days": 4.5
    }
  ]
}
```

**Via proxies frontend:**
```
GET /api/backend-proxy/pipeline-velocity?vacancy_id=<uuid>
GET /api/backend-proxy/pipeline-velocity/bottlenecks?company_id=<uuid>
```

### Como testar — via chat com LIA
Abra o chat e pergunte (com uma vaga em contexto):
- "Onde o pipeline está travando?"
- "Quais etapas estão com gargalo?"
- "Quanto tempo os candidatos estão em cada etapa?"

O agente Kanban vai usar a tool `get_pipeline_velocity` automaticamente.

### Como testar — alertas automáticos
O ProactiveAgentWorker roda a cada 30 minutos. Para forçar sem esperar:
```python
import asyncio
from app.shared.agents.proactive_worker import ProactiveAgentWorker

async def test():
    worker = ProactiveAgentWorker()
    alerts = await worker.check_velocity_bottleneck("sua_company_id")
    for a in alerts:
        print(a["title"], "—", a["severity"])

asyncio.run(test())
```

Verificar alertas gerados via API:
```
GET /api/v1/proactive-actions?company_id=<uuid>
```
Procurar por `action_type = "velocity_bottleneck"`.

---

## Sprint 1C — Zero-Touch Scheduling (Auto-agendamento)

### O que faz
Permite ao recrutador (ou à LIA) enviar ao candidato um link com horários disponíveis.
O candidato escolhe o horário diretamente pelo link (sem precisar responder ou ligar),
e a entrevista é criada automaticamente no sistema.

**Canal preferido:** WhatsApp. Fallback automático para email se não houver telefone
ou se o WhatsApp falhar.

### Fluxo completo
```
Recrutador cria link → candidato recebe WhatsApp/email com link
    → candidato acessa /agendar/{token}
    → candidato vê horários disponíveis
    → candidato clica em um horário
    → entrevista criada automaticamente
    → link marcado como "used"
```

### Arquivos criados
- `app/services/zero_touch_scheduling_service.py` — serviço central
- `app/api/v1/self_scheduling_public.py` — endpoints REST (público + autenticado)
- `plataforma-lia/src/app/api/backend-proxy/scheduling/link/route.ts`
- `plataforma-lia/src/app/api/backend-proxy/scheduling/link/[token]/route.ts`
- `plataforma-lia/src/app/api/backend-proxy/scheduling/link/[token]/confirm/route.ts`

### Como testar — passo a passo completo

**Passo 1 — Criar o link (recrutador autenticado):**
```
POST /api/v1/scheduling/link
Authorization: Bearer <token_do_recrutador>
Content-Type: application/json
```
```json
{
  "company_id": "sua_company_id",
  "candidate_id": "uuid_do_candidato",
  "candidate_name": "Maria Silva",
  "candidate_email": "maria@email.com",
  "candidate_phone": "+5511999999999",
  "job_vacancy_id": "uuid_da_vaga",
  "job_title": "Analista de RH",
  "available_slots": [
    {"start": "2026-03-10T10:00:00", "end": "2026-03-10T11:00:00"},
    {"start": "2026-03-11T14:00:00", "end": "2026-03-11T15:00:00"},
    {"start": "2026-03-12T09:00:00", "end": "2026-03-12T10:00:00"}
  ],
  "interviewer_emails": ["recrutador@empresa.com"],
  "interview_type": "hr",
  "interview_mode": "video",
  "duration_minutes": 60,
  "preferred_channel": "whatsapp",
  "expires_hours": 72
}
```
Resposta esperada:
```json
{
  "success": true,
  "link_id": "...",
  "token": "abc123...",
  "scheduling_url": "/agendar/abc123...",
  "expires_at": "2026-03-09T20:00:00",
  "slots_offered": 3,
  "send_result": { "success": true }
}
```

**Passo 2 — Simular o candidato acessando o link (sem auth):**
```
GET /api/v1/scheduling/link/<token>
```
Resposta esperada:
```json
{
  "candidate_name": "Maria Silva",
  "job_title": "Analista de RH",
  "interview_type": "hr",
  "duration_minutes": 60,
  "available_slots": [...],
  "expires_at": "...",
  "is_valid": true
}
```

**Passo 3 — Simular o candidato confirmando o horário (sem auth):**
```
POST /api/v1/scheduling/link/<token>/confirm
Content-Type: application/json
```
```json
{
  "start": "2026-03-10T10:00:00",
  "end": "2026-03-10T11:00:00"
}
```
Resposta esperada:
```json
{
  "success": true,
  "message": "Entrevista agendada com sucesso! Você receberá um e-mail de confirmação.",
  "candidate_name": "Maria Silva",
  "job_title": "Analista de RH",
  "selected_slot": { "start": "...", "end": "..." }
}
```

**Passo 4 — Verificar no banco:**
```sql
SELECT token, status, selected_slot, use_count, updated_at
FROM self_scheduling_links
WHERE token = '<token>';
```
✅ `status` deve ser `"used"`
✅ `selected_slot` deve ter o horário escolhido
✅ `use_count` deve ser `1`

**Testar link expirado ou já usado:**
Tente confirmar o mesmo token novamente → deve retornar `410 Gone`.

---

## Sprint 1E — Silver Medalists (Candidatos Prata)

### O que faz
Identifica candidatos que chegaram à etapa de entrevista em processos anteriores
mas não foram contratados. São candidatos já validados pela empresa — "quentes" e
prontos para reaproveitamento em novas vagas similares.

### Critérios para ser "candidato prata"
- Chegou até `interview_hr`, `interview_technical`, `interview_manager`, `interview_final`, `offer` ou equivalentes em PT-BR
- Não foi contratado (`stage` e `status` ≠ `hired/contratado`)
- Processo nos últimos 90 dias (padrão configurável)
- Não está já cadastrado na vaga alvo

### Score de relevância (0 a 1)
| Fator | Peso | Critério |
|-------|------|---------|
| Etapa atingida | 40% | offer=1.0, interview_final=0.9, interview_hr=0.5 |
| Recência | 35% | processo hoje=1.0, 180 dias atrás=0.1 |
| LIA score anterior | 25% | score da última avaliação |

### Arquivos criados
- `app/services/silver_medalist_service.py` — serviço com scoring
- `app/shared/agents/proactive_worker.py` — novo check `check_silver_medalists`
- `app/domains/recruiter_assistant/agents/kanban_tool_registry.py` — tool `find_silver_medalists`

### Como testar — via Python direto
```python
import asyncio
from app.services.silver_medalist_service import silver_medalist_service

# Para uma vaga específica
async def test_vaga():
    medalists = await silver_medalist_service.find_for_vacancy(
        target_vacancy_id="uuid_da_vaga_nova",
        company_id="sua_company_id",
        limit=10
    )
    for m in medalists:
        print(
            f"{m['candidate_name']} | "
            f"Etapa: {m['reached_stage']} | "
            f"Score: {m['relevance_score']} | "
            f"Processo: {m['past_vacancy_title']} ({m['days_since_process']}d atrás)"
        )

asyncio.run(test_vaga())
```

```python
# Para toda a empresa (sem vaga específica)
async def test_empresa():
    medalists = await silver_medalist_service.find_for_company(
        company_id="sua_company_id",
        limit=20,
        max_days_lookback=90
    )
    print(f"Total de candidatos prata: {len(medalists)}")

asyncio.run(test_empresa())
```

### Como testar — via chat com LIA
Abra o chat e pergunte:
- "Temos candidatos de processos anteriores para esta vaga?"
- "Quem pode ser reaproveitado do banco de talentos?"
- "Mostre os candidatos prata dos últimos 3 meses"

O agente Kanban vai usar a tool `find_silver_medalists` automaticamente.

### Como testar — alertas automáticos
O ProactiveAgentWorker emite um alerta consolidado quando encontra medalists.
```
GET /api/v1/proactive-actions?company_id=<uuid>
```
Procurar por `action_type = "silver_medalists_available"`.
O alerta lista os top 5 candidatos e sugere ação ao recrutador.

---

## Endpoints novos — referência rápida (Onda 1)

| Método | URL | Auth | Descrição |
|--------|-----|------|-----------|
| GET | `/api/v1/pipeline/velocity` | ✅ | Métricas de velocidade por etapa |
| GET | `/api/v1/pipeline/velocity/bottlenecks` | ✅ | Candidatos acima do limite de tempo |
| POST | `/api/v1/scheduling/link` | ✅ | Criar link de auto-agendamento |
| GET | `/api/v1/scheduling/link/{token}` | ❌ público | Ver slots disponíveis (candidato) |
| POST | `/api/v1/scheduling/link/{token}/confirm` | ❌ público | Confirmar horário (candidato) |

**Proxies frontend (Next.js) — Onda 1:**

| Proxy | Aponta para |
|-------|------------|
| `GET /api/backend-proxy/pipeline-velocity` | `/api/v1/pipeline/velocity` |
| `GET /api/backend-proxy/pipeline-velocity/bottlenecks` | `/api/v1/pipeline/velocity/bottlenecks` |
| `POST /api/backend-proxy/scheduling/link` | `/api/v1/scheduling/link` |
| `GET /api/backend-proxy/scheduling/link/[token]` | `/api/v1/scheduling/link/{token}` |
| `POST /api/backend-proxy/scheduling/link/[token]/confirm` | `/api/v1/scheduling/link/{token}/confirm` |

---

## Verificação rápida — Onda 1

```bash
# No diretório lia-agent-system/

# 1. Migration aplicada?
alembic current
# Deve mostrar: 023_add_stage_entered_at (head)

# 2. Coluna no banco?
python -c "
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as db:
        r = await db.execute(text(\"SELECT column_name FROM information_schema.columns WHERE table_name='vacancy_candidates' AND column_name='stage_entered_at'\"))
        print('stage_entered_at:', 'OK' if r.fetchone() else 'FALTANDO')

asyncio.run(check())
"

# 3. Testes unitários passando?
python -m pytest tests/unit/test_stage_entered_at.py \
                tests/unit/test_pipeline_velocity_service.py \
                tests/unit/test_silver_medalist_service.py -v
# Esperado: 40 passed
```

---

## Sprint 2A — Recruiter Intelligence (Opção C)

### O que faz
Surfaça métricas de produtividade do recrutador sem criar nova tela de UI.
O recrutador recebe a informação em 4 canais:

| Canal | Quando | O que recebe |
|-------|--------|-------------|
| **Daily Briefing** | Toda manhã ao abrir o chat | "Você tem 8 candidatos aguardando. Mais urgente: Ana na etapa 'offer' há 4 dias." |
| **Chat com LIA** | Quando pergunta | Resposta com lista priorizada completa |
| **Bell in-app** | Alerta automático (ProactiveWorker) | Sininho acende com badge quando há backlog crítico |
| **Teams** | Apenas severity=critical | Push com Adaptive Card quando há oferta parada |

### O que define "candidato aguardando ação"
Candidato que está na etapa atual além do threshold recomendado:

| Etapa | Threshold |
|-------|-----------|
| offer / proposta | 2 dias |
| interview_hr / entrevista_rh | 4 dias |
| interview_technical / entrevista_tecnica | 4 dias |
| interview_manager / interview_final | 4 dias |
| screening / triagem | 5 dias |
| applied / novo / initial | 3 dias |
| Qualquer outra | 5 dias |

### Vagas consideradas no backlog do recrutador
A query cobre **dois vínculos**:
1. Vagas onde `job_vacancies.created_by = user_id` (recrutador criou a vaga)
2. Vagas onde `job_vacancies.recruiter_email = email do recrutador` (recrutador foi atribuído)

Isso garante que mesmo vagas criadas por gestores e atribuídas via campo `recruiter_email` aparecem no backlog correto.

### Urgency score — como a lista é ordenada
```
urgency_score = days_in_stage × weight_da_etapa

Pesos:
  offer / proposta       → 4.0  (maior urgência)
  interview_*            → 3.0
  screening / triagem    → 2.0
  applied / novo         → 1.0
```
Exemplo: candidato em offer há 3 dias → score 12.0 vence candidato em triagem há 6 dias → score 12.0 (empate, offer aparece primeiro por `is_critical=True`).

### Alertas direcionados por recrutador
O campo `target_user_id` em `proactive_actions` garante que o alerta aparece **apenas para o recrutador responsável**, não para todos da empresa.
`get_pending_alerts(company_id, user_id=<id>)` filtra: `target_user_id IS NULL OR target_user_id = user_id`.

---

### Como testar — via chat com LIA

Abra o chat e pergunte:
- "Quais candidatos estão me esperando?"
- "Tenho candidatos parados no pipeline?"
- "Meu backlog de hoje"
- "O que preciso fazer hoje?"

A LIA usará a tool `get_recruiter_backlog` automaticamente. Resposta esperada:
```
Você tem 5 candidatos aguardando ação, sendo 1 em situação crítica:

🔴 Ana Silva — offer há 4 dias (limite: 2 dias) — Analista de RH
🟡 Bruno Costa — interview_hr há 6 dias (limite: 4 dias) — Dev Backend
🟡 Carla Mendes — triagem há 7 dias (limite: 5 dias) — UX Designer
...
```

---

### Como testar — Daily Briefing

O Daily Briefing é gerado via `BriefingService.generate_daily_briefing(user_id)`.
Para testar diretamente:

```python
import asyncio
from app.services.briefing_service import briefing_service

async def test():
    briefing = await briefing_service.generate_daily_briefing(user_id="seu_user_id")
    metrics = briefing.get("recruiter_metrics", {})
    print(f"Backlog: {metrics['backlog_count']} candidatos")
    print(f"Críticos: {metrics['critical_count']}")
    print(f"Mais urgente: {metrics.get('most_urgent')}")
    print(f"Tempo médio de resposta: {metrics['avg_response_time_days']} dias")
    print(f"Avançados essa semana: {metrics['candidates_advanced_this_week']}")
    print(f"Ofertas pendentes: {metrics['offers_pending']}")

asyncio.run(test())
```

A seção `recruiter_metrics` no retorno do briefing:
```json
{
  "recruiter_metrics": {
    "backlog_count": 5,
    "critical_count": 1,
    "most_urgent": {
      "candidate_name": "Ana Silva",
      "vacancy_title": "Analista de RH",
      "stage": "offer",
      "days_in_stage": 4.0,
      "threshold_days": 2,
      "overdue_days": 2.0,
      "is_critical": true
    },
    "avg_response_time_days": 2.3,
    "candidates_advanced_this_week": 7,
    "offers_pending": 1
  }
}
```

Os insights do briefing também incluem blocos automáticos:
```json
{
  "type": "critical",
  "icon": "AlertCircle",
  "title": "1 candidato(s) em situação crítica",
  "description": "Mais urgente: Ana Silva está na etapa 'offer' há 4.0 dias (limite: 2 dias).",
  "priority": "critical",
  "action_type": "view_recruiter_backlog"
}
```

---

### Como testar — endpoints REST

**Resumo semanal:**
```
GET /api/v1/recruiter-metrics/<recruiter_id>?company_id=<uuid>&period_days=30
Authorization: Bearer <token>
```
Resposta esperada:
```json
{
  "success": true,
  "recruiter_id": "...",
  "data": {
    "backlog_count": 5,
    "critical_count": 1,
    "most_urgent": { "candidate_name": "Ana Silva", "stage": "offer", "days_in_stage": 4.0 },
    "avg_response_time_days": 2.3,
    "candidates_advanced_this_week": 7,
    "offers_pending": 1
  }
}
```

**Lista priorizada de candidatos:**
```
GET /api/v1/recruiter-metrics/<recruiter_id>/backlog?company_id=<uuid>
Authorization: Bearer <token>
```
Resposta esperada:
```json
{
  "success": true,
  "total": 5,
  "critical": 1,
  "data": [
    {
      "candidate_name": "Ana Silva",
      "vacancy_title": "Analista de RH",
      "stage": "offer",
      "days_in_stage": 4.0,
      "threshold_days": 2,
      "overdue_days": 2.0,
      "is_critical": true,
      "urgency_score": 16.0,
      "last_contact_at": "2026-03-01T14:30:00"
    }
  ]
}
```

**Via proxies frontend:**
```
GET /api/backend-proxy/recruiter-metrics/<recruiter_id>?company_id=<uuid>
GET /api/backend-proxy/recruiter-metrics/<recruiter_id>/backlog?company_id=<uuid>
```

---

### Como testar — alertas automáticos (ProactiveWorker)

O ProactiveWorker roda a cada 30 minutos. Para forçar sem esperar:
```python
import asyncio
from app.shared.agents.proactive_worker import ProactiveAgentWorker

async def test():
    worker = ProactiveAgentWorker()
    alerts = await worker.check_recruiter_backlog("sua_company_id")
    for a in alerts:
        print(f"[{a['severity'].upper()}] {a['title']}")
        print(f"  Recrutador: {a['data']['recruiter_id']}")
        print(f"  target_user_id: {a.get('target_user_id')}")

asyncio.run(test())
```

Verificar alertas gerados no banco:
```
GET /api/v1/proactive-actions?company_id=<uuid>
```
Procurar por `action_type = "recruiter_backlog"`.

Verificar que o campo `target_user_id` está preenchido:
```sql
SELECT action_type, severity, title, target_user_id, created_at
FROM proactive_actions
WHERE action_type = 'recruiter_backlog'
ORDER BY created_at DESC
LIMIT 10;
```
✅ `target_user_id` deve conter o user_id do recrutador responsável (não nulo).

---

### Como testar — notificação Teams (severity=critical)

Quando há oferta parada (offer/proposta além de 2 dias), o `check_recruiter_backlog` envia automaticamente via Teams além do Bell.

Para confirmar que o canal Teams foi ativado:
```python
import asyncio
from app.services.notification_service import notification_service

async def test():
    # Verifica notificações recentes do tipo recruiter_backlog
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import text
    async with AsyncSessionLocal() as db:
        r = await db.execute(text("""
            SELECT user_id, title, channels, created_at
            FROM notifications
            WHERE category = 'recruiter_backlog'
            ORDER BY created_at DESC
            LIMIT 5
        """))
        for row in r.fetchall():
            print(row.user_id, row.title, row.channels)

asyncio.run(test())
```
✅ `channels` deve conter `["in_app", "teams"]` para alertas críticos.
✅ `channels` deve conter `["in_app"]` para alertas de warning.

---

### Como testar — vagas atribuídas via recruiter_email

Criar uma vaga onde o recrutador está no campo `recruiter_email` mas NÃO é o `created_by`:
```sql
-- Verificar se vaga está sendo considerada no backlog do recrutador correto
SELECT jv.id, jv.title, jv.created_by, jv.recruiter_email,
       u.id AS recruiter_user_id
FROM job_vacancies jv
LEFT JOIN users u ON u.email = jv.recruiter_email
WHERE jv.company_id::text = '<uuid>';
```
Em seguida chamar o backlog com o `user_id` do recrutador atribuído:
```
GET /api/v1/recruiter-metrics/<recruiter_user_id>/backlog?company_id=<uuid>
```
✅ A vaga deve aparecer no backlog mesmo que `created_by` seja outro usuário.

---

## Sprint 2B — Early Warning Score (EWS)

### O que faz
Detecta candidatos em risco de ghosting **antes** do dano acontecer, usando thresholds calibrados
por etapa (warning + critical) e pondera a urgência pelo LIA score do candidato.

Substitui o `check_engagement_gaps` (threshold fixo de 10 dias) por lógica inteligente com
EWS score de 0.0 a 1.0.

| Canal | Quando | O que recebe |
|-------|--------|-------------|
| **ProactiveWorker → Bell** | Alertas automáticos a cada 30min | Por candidato, direcionado ao recrutador |
| **ProactiveWorker → Teams** | Apenas severity=critical | Push quando candidato crítico sem contato |
| **Chat com LIA** | Quando pergunta | Lista de candidatos em risco com score e ação sugerida |
| **REST** | Qualquer consumidor | `GET /api/v1/early-warning?company_id=&min_risk_level=` |

### Thresholds por etapa

| Etapa | Warning (dias) | Critical (dias) |
|-------|---------------|----------------|
| offer / proposta | 2 | 4 |
| interview_hr / entrevista_rh | 3 | 5 |
| interview_technical / entrevista_tecnica | 3 | 5 |
| interview_manager / interview_final | 3 | 5 |
| screening / triagem | 5 | 8 |
| applied / novo / initial | 7 | 12 |
| Qualquer outra | 5 | 10 |

### Fórmula EWS score (0.0 a 1.0)
```
base_score  = min(1.0, days_since_contact / critical_threshold)
lia_weight  = 1.0 + (lia_score ou 0.5) × 0.5
ews_score   = min(1.0, base_score × lia_weight)
```
- Candidato com LIA score 1.0 tem peso 1.5 (50% mais urgente)
- Candidato sem score usa 0.5 como padrão (peso neutro 1.25)

### Classificação de risco
| EWS score | Risk level |
|-----------|-----------|
| ≥ 1.0 | critical |
| ≥ 0.6 | high |
| ≥ 0.3 | medium |
| < 0.3 | low |

### Alertas direcionados por recrutador
Igual ao Sprint 2A: campo `target_user_id` garante que cada alerta aparece **somente para o
recrutador responsável pela vaga** do candidato em risco.

---

### Como testar — via chat com LIA
Abra o chat e pergunte:
- "Quais candidatos podem sumir?"
- "Temos risco de ghosting?"
- "Candidatos sem contato há dias?"
- "Quem devo contatar urgente hoje?"

O agente Kanban usa a tool `get_at_risk_candidates` automaticamente. Resposta esperada:
```
3 candidatos em risco de desengajamento:

🔴 Ana Silva [CRITICAL] — offer há 5 dias (EWS: 1.00) — Analista de RH
   → Sem contato há 5 dias, limite crítico: 4 dias
🟠 Bruno Costa [HIGH] — interview_hr há 4 dias (EWS: 0.75) — Dev Backend
🟡 Carla Mendes [HIGH] — screening há 6 dias (EWS: 0.69) — UX Designer
```

---

### Como testar — endpoint REST

```
GET /api/v1/early-warning?company_id=<uuid>&min_risk_level=medium
Authorization: Bearer <token>
```
Resposta esperada:
```json
{
  "success": true,
  "company_id": "...",
  "min_risk_level": "medium",
  "summary": {
    "total": 5,
    "by_risk_level": { "critical": 1, "high": 2, "medium": 2 },
    "top_critical": [
      {
        "candidate_name": "Ana Silva",
        "vacancy_title": "Analista de RH",
        "stage": "offer",
        "days_since_contact": 5.0,
        "ews_score": 1.0,
        "risk_level": "critical",
        "warning_threshold": 2,
        "critical_threshold": 4
      }
    ],
    "top_high": [...]
  },
  "data": [...]
}
```

**Via proxy frontend:**
```
GET /api/backend-proxy/early-warning?company_id=<uuid>&min_risk_level=medium
```

---

### Como testar — via Python direto

```python
import asyncio
from app.services.early_warning_service import early_warning_service

async def test():
    candidates = await early_warning_service.get_at_risk_candidates(
        company_id="sua_company_id",
        min_risk_level="medium",
    )
    for c in candidates:
        print(
            f"[{c['risk_level'].upper()}] {c['candidate_name']} | "
            f"{c['stage']} | {c['days_since_contact']:.0f}d sem contato | "
            f"EWS: {c['ews_score']:.2f}"
        )

    summary = await early_warning_service.get_summary_by_risk_level("sua_company_id")
    print(f"\nResumo: {summary['by_risk_level']}")

asyncio.run(test())
```

---

### Como testar — alertas automáticos (ProactiveWorker)

O ProactiveWorker gera alertas para candidatos `high` e `critical`. Para forçar sem esperar:
```python
import asyncio
from app.shared.agents.proactive_worker import ProactiveAgentWorker

async def test():
    worker = ProactiveAgentWorker()
    alerts = await worker.check_early_warning("sua_company_id")
    for a in alerts:
        print(f"[{a['severity'].upper()}] {a['title']}")
        print(f"  EWS: {a['data']['ews_score']} | Risco: {a['data']['risk_level']}")
        print(f"  target_user_id: {a.get('target_user_id')}")

asyncio.run(test())
```

Verificar alertas gerados no banco:
```
GET /api/v1/proactive-actions?company_id=<uuid>
```
Procurar por `action_type = "early_warning"`.

```sql
SELECT action_type, severity, title, target_user_id, created_at,
       data->>'ews_score' AS ews_score,
       data->>'risk_level' AS risk_level
FROM proactive_actions
WHERE action_type = 'early_warning'
ORDER BY created_at DESC
LIMIT 10;
```
✅ `severity = 'critical'` → `channels = ["in_app", "teams"]`
✅ `severity = 'warning'` → `channels = ["in_app"]`
✅ `target_user_id` preenchido com o ID do recrutador da vaga

---

## Sprint 2C — Candidate Journey Intelligence

### O que faz
Analisa o funil real de cada vaga em tempo real: conversão por etapa, drop-off, health score
(0–100) e detecção de **padrões preditivos de risco** — não apenas "candidato parado hoje" mas
"este pipeline vai travar se não agir agora".

| Canal | Quando | O que recebe |
|-------|--------|-------------|
| **Bell in-app** | ProactiveWorker a cada 30min | Por recrutador: alerta consolidado por vaga com health < 50 |
| **Teams** | Apenas severity=critical | Push quando health_label=critical (score < 45) |
| **Email** | Sextas-feiras | Digest semanal do recrutador com saúde de cada vaga ativa |
| **Chat com LIA** | Reativo (pergunta) + Proativo (contexto) | Tool `get_journey_metrics` + injeção automática quando health < 50 |

### Health score (0–100)

| Componente | Pontos | Critério |
|-----------|--------|---------|
| Volume | 20 | ≥5 candidatos ativos |
| Conversão geral | 25 | ≥20% chegaram a etapas avançadas |
| Candidatos avançados | 25 | ≥2 em entrevista/offer |
| Drop-off | 15 | taxa de saída ≤ 30% |
| EWS / engajamento | 15 | sem EWS crítico e movimento recente |

| Score | Label |
|-------|-------|
| ≥ 70 | healthy |
| 45–69 | warning |
| < 45 | critical |

### Padrões preditivos detectados

| Padrão | Severidade | Condição |
|--------|-----------|---------|
| `zero_pipeline` | critical | 0 candidatos ativos |
| `empty_advanced_funnel` | critical | Ativos existem mas nenhum em entrevista/offer |
| `high_offer_rejection` | critical | >40% recusaram na etapa offer/proposta |
| `top_heavy_funnel` | warning | >70% dos candidatos ainda nas etapas iniciais (com >3 candidatos) |
| `critical_health` | critical | health_score < 30 |

### LIA proativa dentro da vaga (Kanban/Tabela)
Quando o recrutador abre o chat com uma vaga em contexto (`vacancy_id` presente) e o
`health_score < 50`, o `KanbanReActAgent` injeta automaticamente um bloco de alerta no
system prompt via `get_journey_insight_block()`. A LIA começa a resposta com o contexto
de risco **sem precisar ser perguntada**.

Exemplo de abertura automática:
```
Notei que o pipeline desta vaga está em estado crítico (38/100).
Candidatos ativos: 2 | Em etapas avançadas: 0 | Funil zerado em etapas avançadas.
Recomendo verificar o pipeline antes de continuar. Quer que eu analise as etapas?
```

---

### Como testar — via chat com LIA

Perguntas que acionam a tool `get_journey_metrics`:
- "Como está o funil desta vaga?"
- "O pipeline está saudável?"
- "Onde os candidatos estão saindo?"
- "Temos risco de não fechar esta vaga?"
- "Qual o health score aqui?"

Resposta esperada (com vaga em contexto):
```
Health score: 62/100 (warning)

Funil atual:
  screening     → 8 candidatos ativos | drop-off: 22%
  interview_hr  → 3 candidatos ativos | drop-off: 0%
  offer         → 1 candidato ativo   | drop-off: 50% ⚠️

Padrões de risco:
  [WARNING] Taxa de recusa na etapa 'offer': 50%. Acima de 40% — pode indicar
  problema com proposta ou processo.

Conversão geral: 15% | Últimas movimentações: há 2 dias
```

---

### Como testar — endpoints REST

**Métricas detalhadas por vaga:**
```
GET /api/v1/journey/metrics?vacancy_id=<uuid>&company_id=<uuid>
Authorization: Bearer <token>
```
Resposta esperada:
```json
{
  "success": true,
  "vacancy_id": "...",
  "vacancy_title": "Dev Backend",
  "health_score": 62,
  "health_label": "warning",
  "summary": {
    "total_active": 12,
    "candidates_in_advanced_stages": 4,
    "conversion_rate_overall": 0.22,
    "avg_drop_off_rate": 0.18,
    "at_risk_candidates": 2
  },
  "funnel": [
    { "stage": "screening", "active_count": 8, "drop_off_rate": 0.22, "avg_days_in_stage": 4.1 },
    { "stage": "interview_hr", "active_count": 3, "drop_off_rate": 0.0, "avg_days_in_stage": 3.5 },
    { "stage": "offer", "active_count": 1, "drop_off_rate": 0.50, "avg_days_in_stage": 2.0 }
  ],
  "risk_patterns": [
    { "pattern": "high_offer_rejection", "severity": "critical", "message": "..." }
  ]
}
```

**Visão geral da empresa (todas as vagas ativas):**
```
GET /api/v1/journey/company-overview?company_id=<uuid>
Authorization: Bearer <token>
```
Resposta esperada:
```json
{
  "success": true,
  "total_open_vacancies": 5,
  "summary": { "critical": 1, "warning": 2, "healthy": 2 },
  "vacancies": [
    { "vacancy_title": "Dev Backend", "health_score": 28, "health_label": "critical", ... },
    { "vacancy_title": "Analista RH", "health_score": 55, "health_label": "warning",  ... }
  ]
}
```

**Via proxies frontend (rota unificada):**
```
GET /api/backend-proxy/journey?vacancy_id=<uuid>&company_id=<uuid>   → metrics
GET /api/backend-proxy/journey?company_id=<uuid>                     → company-overview
```

---

### Como testar — via Python direto

```python
import asyncio
from app.services.journey_intelligence_service import journey_intelligence_service

async def test_vaga():
    result = await journey_intelligence_service.get_vacancy_metrics(
        vacancy_id="uuid_da_vaga",
        company_id="sua_company_id",
    )
    print(f"Health: {result['health_score']}/100 ({result['health_label']})")
    print(f"Candidatos ativos: {result['summary']['total_active']}")
    print(f"Em etapas avançadas: {result['summary']['candidates_in_advanced_stages']}")
    for p in result['risk_patterns']:
        print(f"  [{p['severity'].upper()}] {p['message']}")

async def test_empresa():
    result = await journey_intelligence_service.get_company_overview("sua_company_id")
    print(f"Vagas: {result['total_open_vacancies']} | "
          f"Críticas: {result['summary']['critical']} | "
          f"Alerta: {result['summary']['warning']}")
    for v in result['vacancies'][:3]:
        print(f"  {v['vacancy_title']}: {v['health_score']}/100 ({v['health_label']})")

asyncio.run(test_vaga())
asyncio.run(test_empresa())
```

---

### Como testar — alertas automáticos (ProactiveWorker)

```python
import asyncio
from app.shared.agents.proactive_worker import ProactiveAgentWorker

async def test():
    worker = ProactiveAgentWorker()
    alerts = await worker.check_journey_intelligence("sua_company_id")
    for a in alerts:
        print(f"[{a['severity'].upper()}] {a['title']}")
        print(f"  target_user_id: {a.get('target_user_id')}")
        print(f"  Vagas: {[v['vacancy_title'] for v in a['data']['at_risk_vacancies']]}")

asyncio.run(test())
```

Verificar alertas no banco:
```
GET /api/v1/proactive-actions?company_id=<uuid>
```
Procurar por `action_type = "journey_intelligence"`.

```sql
SELECT action_type, severity, title, target_user_id, created_at,
       data->>'critical_count' AS critical_count,
       data->>'worst_vacancy' AS worst_vacancy
FROM proactive_actions
WHERE action_type = 'journey_intelligence'
ORDER BY created_at DESC LIMIT 5;
```
✅ `severity = 'critical'` → Bell + Teams
✅ `severity = 'warning'` → Bell apenas
✅ Em sextas-feiras → Bell + Teams (se critical) + Email
✅ `target_user_id` preenchido — alerta apenas para o recrutador da vaga

---

### Como testar — injeção contextual da LIA (comportamento proativo)

Para confirmar que a LIA injeta o insight automaticamente:

1. Abra o chat da LIA em uma vaga com `health_score < 50` (verifique via `GET /api/v1/journey/metrics`)
2. Envie qualquer mensagem (ex: "oi" ou "o que está acontecendo?")
3. A LIA deve **começar a resposta mencionando o estado crítico do pipeline** sem precisar ser perguntada

Para verificar o bloco de injeção diretamente:
```python
from app.domains.recruiter_assistant.agents.kanban_stage_context import get_journey_insight_block

# Simular dados de vaga crítica
journey_data = {
    "health_score": 32,
    "health_label": "critical",
    "vacancy_title": "Dev Backend",
    "summary": {
        "total_active": 2,
        "candidates_in_advanced_stages": 0,
        "at_risk_candidates": 2,
    },
    "risk_patterns": [
        {"severity": "critical", "message": "Funil zerado em etapas avançadas."},
    ],
}
block = get_journey_insight_block(journey_data)
print(block)
# Esperado: bloco de alerta com ≥5 linhas incluindo health score e padrões de risco

# Vaga saudável NÃO deve gerar bloco
journey_healthy = {"health_score": 75, "health_label": "healthy", "risk_patterns": []}
assert get_journey_insight_block(journey_healthy) == ""
```

---

## Sprint 2D — Recruiter Performance Benchmarking

### O que faz
Compara as métricas individuais do recrutador com a **mediana anônima da empresa** — sem
identificar peers individualmente. Fecha o ciclo de inteligência: "sei o que tenho, sei onde
estou em relação ao time."

| Canal | Quando | O que recebe |
|-------|--------|-------------|
| **Daily Briefing** | Toda manhã | Bloco `recruiter_benchmark` com comparação + insights de performance |
| **Chat com LIA** | Quando pergunta | Tool `get_recruiter_benchmark` com interpretação automática |
| **REST** | Qualquer consumidor | `GET /api/v1/recruiter-metrics/{id}/benchmark` |

> **Privacidade:** requer ≥ 2 recrutadores ativos na empresa. Com menos de 2, retorna
> `benchmark_available: false` — sem expor dados de recrutadores isolados.

### Métricas comparadas

| Métrica | Direção | O que mede |
|---------|---------|-----------|
| `response_time` | lower is better | Dias entre candidato entrar na etapa e primeiro contato |
| `advanced_per_week` | higher is better | Candidatos que avançaram de etapa nos últimos 7 dias |
| `backlog_count` | lower is better | Candidatos aguardando ação além do threshold |
| `offers_pending` | lower is better | Ofertas em aberto além do threshold |

### Labels de performance

Para cada métrica:

| Label | Critério | Performance |
|-------|---------|------------|
| `above` | Melhor que mediana em >15% | `better` |
| `at_par` | Dentro de ±15% da mediana | `at_par` |
| `below` | Pior que mediana em >15% | `worse` |

**Performance geral** (`overall_performance`):
- `above_average`: ≥ 3 métricas com `performance=better`
- `average`: ≥ 3 métricas com `better` + `at_par`
- `below_average`: demais casos

---

### Como testar — via chat com LIA

Perguntas que acionam a tool `get_recruiter_benchmark`:
- "Como estou comparado à empresa?"
- "Minha performance está boa?"
- "Quanto tempo outros recrutadores levam para responder?"
- "Estou acima ou abaixo da média do time?"

Resposta esperada:
```
Performance geral: acima da média ✅

  Tempo de resposta: 1.8d (mediana: 3.2d) ✅ melhor
  Candidatos avançados/semana: 9 (mediana: 5.0) ✅ melhor
  Backlog: 2 (mediana: 4.0) ✅ melhor
  Ofertas pendentes: 0 (mediana: 1.0) ✅ melhor
```

---

### Como testar — Daily Briefing

```python
import asyncio
from app.services.briefing_service import briefing_service

async def test():
    briefing = await briefing_service.generate_daily_briefing(user_id="seu_user_id")

    benchmark = briefing.get("recruiter_benchmark", {})
    print(f"Benchmark disponível: {benchmark.get('benchmark_available')}")
    print(f"Performance geral: {benchmark.get('overall_performance')}")

    if benchmark.get("benchmark_available"):
        cmp = benchmark["comparison"]
        rt = cmp["response_time"]
        print(f"Tempo resposta: {rt['personal']}d vs mediana {rt['benchmark']}d → {rt['performance']}")

    # Insights de benchmark nos insights[]
    for insight in briefing.get("insights", []):
        if insight.get("action_type") == "view_benchmark":
            print(f"Insight: [{insight['type']}] {insight['title']}")

asyncio.run(test())
```

Exemplo de insight no briefing quando `overall_performance=above_average`:
```json
{
  "type": "success",
  "icon": "TrendingUp",
  "title": "Performance acima da média da empresa",
  "description": "Você está acima da mediana em 3 de 4 métricas acompanhadas.",
  "priority": "low",
  "action_type": "view_benchmark"
}
```

---

### Como testar — endpoint REST

```
GET /api/v1/recruiter-metrics/<recruiter_id>/benchmark?company_id=<uuid>
Authorization: Bearer <token>
```
Resposta esperada:
```json
{
  "success": true,
  "recruiter_id": "...",
  "company_id": "...",
  "benchmark_available": true,
  "recruiter_count_in_benchmark": 4,
  "overall_performance": "above_average",
  "personal": {
    "backlog_count": 2,
    "avg_response_time_days": 1.8,
    "candidates_advanced_this_week": 9,
    "offers_pending": 0
  },
  "comparison": {
    "response_time":    { "personal": 1.8, "benchmark": 3.2, "delta": -1.4, "percentile_label": "above", "performance": "better" },
    "advanced_per_week":{ "personal": 9.0, "benchmark": 5.0, "delta": 4.0,  "percentile_label": "above", "performance": "better" },
    "backlog_count":    { "personal": 2.0, "benchmark": 4.0, "delta": -2.0, "percentile_label": "above", "performance": "better" },
    "offers_pending":   { "personal": 0.0, "benchmark": 1.0, "delta": -1.0, "percentile_label": "above", "performance": "better" }
  }
}
```

Quando empresa tem < 2 recrutadores:
```json
{ "success": true, "benchmark_available": false, "recruiter_count_in_benchmark": 1 }
```

**Via proxy frontend:**
```
GET /api/backend-proxy/recruiter-metrics/<recruiter_id>/benchmark?company_id=<uuid>
```

---

### Como testar — via Python direto

```python
import asyncio
from app.services.recruiter_metrics_service import recruiter_metrics_service

async def test():
    # Benchmark da empresa
    bm = await recruiter_metrics_service.get_company_benchmark("sua_company_id")
    print(f"Benchmark disponível: {bm['benchmark_available']}")
    if bm["benchmark_available"]:
        print(f"  Recrutadores: {bm['recruiter_count']}")
        print(f"  Mediana tempo resposta: {bm['median_response_time_days']}d")
        print(f"  Mediana avançados/semana: {bm['median_advanced_per_week']}")

    # Comparação individual
    result = await recruiter_metrics_service.get_recruiter_benchmark_comparison(
        recruiter_id="seu_user_id",
        company_id="sua_company_id",
    )
    print(f"\nPerformance: {result['overall_performance']}")
    for k, v in result["comparison"].items():
        print(f"  {k}: {v['personal']} vs {v['benchmark']} → {v['performance']}")

asyncio.run(test())
```

---

### Guard de privacidade — verificação SQL

```sql
-- Quantos recrutadores ativos a empresa tem?
SELECT COUNT(DISTINCT COALESCE(u.id::text, jv.created_by)) AS recruiter_count
FROM job_vacancies jv
LEFT JOIN users u ON u.email = jv.recruiter_email AND u.company_id::text = '<company_id>'
WHERE jv.company_id::text = '<company_id>'
  AND jv.status IN ('open', 'Ativa', 'Publicada');
```
✅ Se `recruiter_count < 2` → `benchmark_available: false` (nunca expõe dados de recrutador isolado)

---

## Endpoints novos — referência rápida (Sprint 2A + 2B + 2C)

| Método | URL | Auth | Descrição |
|--------|-----|------|-----------|
| GET | `/api/v1/recruiter-metrics/{id}` | ✅ | Resumo semanal de produtividade (2A) |
| GET | `/api/v1/recruiter-metrics/{id}/backlog` | ✅ | Lista priorizada de candidatos aguardando (2A) |
| GET | `/api/v1/early-warning` | ✅ | Candidatos em risco de ghosting com EWS score (2B) |
| GET | `/api/v1/journey/metrics` | ✅ | Funil detalhado + health score por vaga (2C) |
| GET | `/api/v1/journey/company-overview` | ✅ | Saúde de pipeline de todas as vagas ativas (2C) |
| GET | `/api/v1/recruiter-metrics/{id}/benchmark` | ✅ | Comparação com mediana anônima da empresa (2D) |

**Proxies frontend (Next.js) — Sprint 2A + 2B + 2C + 2D:**

| Proxy | Aponta para |
|-------|------------|
| `GET /api/backend-proxy/recruiter-metrics/[id]` | `/api/v1/recruiter-metrics/{id}` |
| `GET /api/backend-proxy/recruiter-metrics/[id]/backlog` | `/api/v1/recruiter-metrics/{id}/backlog` |
| `GET /api/backend-proxy/recruiter-metrics/[id]/benchmark` | `/api/v1/recruiter-metrics/{id}/benchmark` |
| `GET /api/backend-proxy/early-warning` | `/api/v1/early-warning` |
| `GET /api/backend-proxy/journey?vacancy_id=&company_id=` | `/api/v1/journey/metrics` |
| `GET /api/backend-proxy/journey?company_id=` | `/api/v1/journey/company-overview` |

---

## Verificação rápida — tudo de uma vez (Onda 1 + Sprint 2A + 2B)

```bash
# No diretório lia-agent-system/

# 1. Migration Onda 1 aplicada?
alembic current
# Deve mostrar: 023_add_stage_entered_at (head)

# 2. Colunas no banco?
python -c "
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as db:
        r = await db.execute(text(\"SELECT column_name FROM information_schema.columns WHERE table_name='vacancy_candidates' AND column_name='stage_entered_at'\"))
        print('stage_entered_at:', 'OK' if r.fetchone() else 'FALTANDO')

        r2 = await db.execute(text(\"SELECT column_name FROM information_schema.columns WHERE table_name='proactive_actions' AND column_name='target_user_id'\"))
        print('target_user_id em proactive_actions:', 'OK' if r2.fetchone() else 'SERA ADICIONADO NO STARTUP')

asyncio.run(check())
"

# 3. Testes unitários passando?
python -m pytest tests/unit/ -v
# Esperado: 162 passed

# 4. Verificar EWS score manualmente
python -c "
from app.services.early_warning_service import compute_ews_score, risk_level_for_score
score = compute_ews_score(5, 'offer', lia_score=0.8)
print(f'offer, 5 dias, lia=0.8 → EWS={score}, risco={risk_level_for_score(score)}')
# Esperado: EWS=1.0, risco=critical
score2 = compute_ews_score(6, 'screening', lia_score=0.5)
print(f'screening, 6 dias, lia=0.5 → EWS={score2}, risco={risk_level_for_score(score2)}')
# Esperado: EWS~0.938, risco=high
"
```

> **Nota:** `target_user_id` em `proactive_actions` é adicionado automaticamente pelo
> `ensure_proactive_actions_columns()` no startup da aplicação — não requer migration manual.

---

---

## Sprint 3A — Pipeline Prediction

### O que faz
Prevê probabilidade de fechamento de vagas ativas em X dias usando dados operacionais já existentes — sem ML externo, sem migration.

**Fórmula determinística (5 fatores, total 100 pts):**

| Fator | Peso | Lógica |
|-------|------|--------|
| Velocidade | 30 pts | Média de dias por etapa; < 3d = 30, < 5d = 22, < 8d = 14, < 14d = 6, ≥ 14d = 0 |
| Funil avançado | 25 pts | Stage do candidato mais avançado; offer = 25, interview_final = 20, interview_hr = 10, ... |
| Health score | 20 pts | `health_score / 100 * 20` (calculado inline com mesma fórmula do Journey 2C) |
| EWS risk | 15 pts | Base 15 − (critical_ews × 5) − (high_ews × 2), mínimo 0 |
| Volume | 10 pts | ≥8 candidatos = 10, ≥5 = 8, ≥3 = 5, ≥1 = 2 |

**Pipeline vazio (`total_active = 0`) → retorna `0%` imediatamente.**

**Labels de confiança:**
- `high`: total_active ≥ 5 E health ≥ 60
- `low`: total_active ≤ 1 OU health < 30
- `medium`: demais casos

### Arquivos criados/modificados

| Arquivo | Tipo |
|---------|------|
| `app/services/pipeline_prediction_service.py` | Criado — serviço principal |
| `app/api/v1/pipeline_prediction.py` | Criado — 2 endpoints REST |
| `plataforma-lia/src/app/api/backend-proxy/pipeline-prediction/route.ts` | Criado — proxy FE |
| `tests/unit/test_pipeline_prediction_service.py` | Criado — 29 testes |
| `app/shared/agents/proactive_worker.py` | Modificado — `check_pipeline_prediction` |
| `app/services/briefing_service.py` | Modificado — `_get_pipeline_prediction` + insights |
| `app/domains/recruiter_assistant/agents/kanban_tool_registry.py` | Modificado — tool `get_pipeline_prediction` |
| `app/domains/recruiter_assistant/agents/kanban_stage_context.py` | Modificado — `get_pipeline_prediction_block()` |
| `app/domains/recruiter_assistant/agents/kanban_react_agent.py` | Modificado — injeção no `process()` |
| `app/domains/recruiter_assistant/agents/jobs_mgmt_tool_registry.py` | Modificado — tool `get_pipeline_prediction` |
| `app/domains/recruiter_assistant/agents/jobs_mgmt_stage_context.py` | Modificado — `get_pipeline_prediction_block()` |
| `app/domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py` | Modificado — injeção no `process()` |
| `app/main.py` | Modificado — router registrado |

### Canais de superfície

| Canal | Contexto | Trigger | Conteúdo |
|-------|----------|---------|---------|
| 🔔 **Bell (negativo)** | ProactiveWorker | `closure_probability < 30%` | "Pipeline crítico: vaga X com 18% de chance de fechar" |
| 👥 **Teams** | ProactiveWorker | `prob < 30%` E severity=critical | Mensagem com link para a vaga |
| 📧 **Email** | ProactiveWorker | `prob < 30%` apenas às sextas | Digest semanal de vagas em risco |
| 🔔 **Bell (positivo)** | ProactiveWorker | `prob ≥ 80%`, 1x por vaga | "Vaga X está 80% próxima do fechamento!" |
| 💬 **Chat Kanban** | `kanban_react_agent.py` | Automático quando `vacancy_id` presente | Bloco `=== PREVISAO DE FECHAMENTO ===` no `stage_ctx` |
| 💬 **Chat Gestão de Vagas** | `jobs_mgmt_react_agent.py` | Automático em todo `process()` com `company_id` | Bloco com ranking de vagas em risco + prestes a fechar |
| 📋 **Briefing** | `briefing_service.py` | Diário | Seção `pipeline_prediction` + 2 insights (risco/fechamento) |
| 🔧 **Tool sob demanda** | `get_pipeline_prediction` (kanban + jobs_mgmt) | Pergunta do usuário | Probabilidade + fatores + estimativa |

**Diferença entre os dois agentes:**
- **Kanban** (`vacancy_id` presente): injeção individual por vaga — mesma abordagem do Journey 2C
- **Gestão de Vagas** (sem `vacancy_id`): injeção de visão geral do portfolio completo do recrutador

**Bell positivo — flag de não-repetição:**
O alerta de `prob ≥ 80%` usa `setattr(self, f"_notified_closing_{vac_id}", True)` para disparar 1x por vaga por instância do worker. Não persiste entre restarts — comportamento aceitável para MVP.

### Endpoints REST

```bash
# Previsão individual
GET /api/v1/pipeline-prediction?vacancy_id=<uuid>&company_id=<uuid>

# Visão geral (vagas ordenadas por risco, mais crítica primeiro)
GET /api/v1/pipeline-prediction/company-overview?company_id=<uuid>

# Proxy FE (vacancy_id opcional — sem ele vai para company-overview)
GET /api/backend-proxy/pipeline-prediction?company_id=<uuid>
GET /api/backend-proxy/pipeline-prediction?vacancy_id=<uuid>&company_id=<uuid>
```

**Response individual:**
```json
{
  "vacancy_id": "uuid",
  "vacancy_title": "Dev Backend",
  "closure_probability": 68,
  "estimated_days_to_close": 12,
  "confidence_level": "medium",
  "stage_of_best_candidate": "interview_final",
  "positive_factors": ["candidate_in_final_interview", "velocity_above_avg"],
  "risk_factors": ["ews_critical_count_1"],
  "total_active": 5,
  "advanced_count": 2
}
```

**Response company-overview:**
```json
{
  "company_id": "uuid",
  "vacancies": [...],  // ordenado por closure_probability ASC
  "summary": {
    "total_active_vacancies": 8,
    "at_risk_count": 2,
    "near_closure_count": 1,
    "avg_closure_probability": 54
  }
}
```

### Como testar

**1. REST — previsão individual:**
```bash
curl "http://localhost:8000/api/v1/pipeline-prediction?vacancy_id=<uuid>&company_id=<uuid>"
# Esperado: closure_probability entre 0 e 100
```

**2. REST — visão geral:**
```bash
curl "http://localhost:8000/api/v1/pipeline-prediction/company-overview?company_id=<uuid>"
# Esperado: lista de vagas ordenada por probability ASC
```

**3. Python — funções puras:**
```python
from app.services.pipeline_prediction_service import (
    compute_closure_probability, estimate_days_to_close, get_confidence_level
)

# Vaga saudável com candidato em offer
prob = compute_closure_probability(5, "offer", 2.0, 2, 0, 0, 80)
print(f"Probabilidade: {prob}%")  # Esperado: >= 80

# Estimativa de dias
days = estimate_days_to_close("interview_final", 4.0, 3)
print(f"Estimativa: {days} dias")  # Esperado: ~10-15

# Pipeline vazio
prob_empty = compute_closure_probability(0, "", 0, 0, 0, 0, 0)
print(f"Pipeline vazio: {prob_empty}%")  # Esperado: 0
```

**4. Chat LIA — Kanban (com vacancy_id):**
```
Usuário: "Qual a chance de fechar essa vaga?"
LIA: [contexto já injetado com closure_probability] → resposta direta com % e fatores

Usuário: "Quando vamos fechar?"
LIA: usa tool get_pipeline_prediction → retorna estimated_days_to_close
```

**5. Chat LIA — Gestão de Vagas:**
```
Usuário: [abre a página de gestão de vagas]
LIA: [contexto já contém ranking de vagas com previsão]

Usuário: "Quais vagas estão em risco?"
LIA: responde com lista de vagas < 30% de probability com ações sugeridas

Usuário: "Alguma vaga vai fechar logo?"
LIA: responde com vagas ≥ 80% de probability com prazo estimado
```

**6. ProactiveWorker:**
```python
from app.shared.agents.proactive_worker import ProactiveAgentWorker
worker = ProactiveAgentWorker()
alerts = asyncio.run(worker.check_pipeline_prediction("company-uuid"))
print(f"{len(alerts)} alertas gerados")
# Vagas < 30%: tipo "pipeline_prediction_risk", severity critical/warning
# Vagas >= 80%: tipo "pipeline_prediction_closing", severity info
```

**7. Testes unitários:**
```bash
python -m pytest tests/unit/test_pipeline_prediction_service.py -v
# Esperado: 29 passed

python -m pytest tests/unit/ -q
# Esperado: 191 passed
```

---

*Documento atualizado em 07/03/2026 — Onda 1 (1A · 1B · 1C · 1E) + Onda 2 (2A · 2B · 2C · 2D) + Onda 3 (3A) da Camada de Inteligência LIA.*
