# Plano de Implementação — Gaps de IA & Arquitetura
## WeDOTalent / Plataforma LIA
**Data:** 09/março/2026
**Versão:** 1.0
**Base:** `DIAGNOSTICO_ARQUITETURA_IA_v4.0.md` (04/03/2026) + Auditoria técnica do codebase (09/03/2026)

---

## CONTEXTO

Este documento cruzou cada gap identificado no diagnóstico do especialista André com o estado real do código em 09/03/2026. Dos 30 gaps auditados:

| Status | Qtd | Descrição |
|--------|:---:|-----------|
| ✅ Resolvido | 16 | Não requerem ação |
| ⚠️ Parcial | 9 | Requerem complementação |
| ❌ Pendente | 5 | Não iniciados |

**Este plano foca exclusivamente nos 14 itens não totalmente resolvidos**, organizados por prioridade de negócio e interdependências técnicas.

---

## SCORECARD ATUAL vs. META

| Dimensão | Estado 04/03 | **Estado 09/03** | Meta Produção |
|----------|:-----------:|:---------------:|:------------:|
| Estrutura de código | 7/10 | **8/10** | 9/10 |
| Capacidades agênticas | 7/10 | **8/10** | 9/10 |
| Observabilidade | 6/10 | **7/10** | 9/10 |
| Guardrails e compliance | 7/10 | **9/10** | 10/10 |
| Qualidade de agentes | — | **3/10** | 8/10 |
| Cobertura de testes | 3/10 | **4/10** | 7/10 |
| Prontidão para produção | 6/10 | **7/10** | 9/10 |

---

## SPRINT H — GAPS CRÍTICOS (semana 1)

> **Critério de entrada em produção:** os 2 itens abaixo devem estar resolvidos. Bloqueiam compliance SOX/ISO 27001 e expõem dados em logs.

---

### H1 — Corrigir Truncamento de `reasoning` em Auditoria

**Arquivo:** `lia-agent-system/libs/agents-core/lia_agents_core/react_loop.py`
**Linha:** ~278
**Urgência:** 🔴 CRÍTICO — bloqueia compliance SOX/ISO 27001/BCB 498

**Problema atual:**
```python
# ATUAL — truncado a 500 chars
_audit.on_llm_call(
    prompt_preview=message[:500],
    response_preview=reasoning[:500],  # ← TRUNCA auditoria
    ...
)
```

**Solução:**
```python
# CORRIGIDO — sem truncamento em trace completo
_audit.on_llm_call(
    prompt_preview=message[:500],          # Preview mantido (para dashboards)
    prompt_full=message,                   # Campo novo — conteúdo completo
    response_preview=reasoning[:500],      # Preview mantido
    reasoning_full=reasoning,              # Campo novo — sem truncamento
    decision=decision,
    ...
)
```

**Mudanças necessárias:**
1. `react_loop.py:278` — adicionar `prompt_full` e `reasoning_full` ao `on_llm_call()`
2. `AuditCallback.on_llm_call()` — aceitar e persistir os campos `*_full`
3. Migration de banco se `ExecutionLog` tiver campo `VARCHAR(500)` → `TEXT`
4. Verificar `execution_log_store.py` — coluna `decision_final` pode ter limite no modelo

**Testes:**
- Criar decision com >500 chars e verificar persistência completa
- Verificar que preview e full coexistem (backward compat)

**Esforço:** 0,5 dia | **Risco:** Baixo (adição de campos)

---

### H2 — Remover `print()` de wsi_interview_graph.py

**Arquivo:** `lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py`
**Urgência:** 🔴 CRÍTICO — exposição de dados sensíveis em stdout/containers

**Problema:**
```python
print(state.wsi_final_score, state.recommendation)  # CRÍTICO: log leakage
```

**Solução:**
```python
logger.debug(
    "WSI final score computed",
    extra={
        "wsi_final_score": state.wsi_final_score,
        "recommendation": state.recommendation,
        # PII masking: não logar candidate_id direto em debug
    }
)
```

**Ação:** Buscar todos os `print()` em `app/domains/` e substituir por `logger.*`:
```bash
# Verificar scope completo
grep -rn "print(" lia-agent-system/app/domains/ lia-agent-system/libs/agents-core/
```

**Esforço:** 0,5 dia | **Risco:** Zero

---

## SPRINT I — COMPLETAR OBSERVABILIDADE E GUARDRAILS (semanas 2-3)

---

### I1 — CRUD API para Guardrails Editáveis

**Contexto:** Tabela `guardrails` existe (migration `020_add_guardrails_table.py`). Modelo existe. **Falta apenas a API.**

**Arquivo a criar:** `lia-agent-system/app/api/v1/admin_guardrails.py`

**Endpoints necessários:**
```python
# Listar guardrails (filtros: domain, level, is_active, company_id)
GET /api/v1/admin/guardrails

# Detalhe de um guardrail
GET /api/v1/admin/guardrails/{id}

# Criar guardrail
POST /api/v1/admin/guardrails
Body: { level, domain?, node?, rule, blocking_message?, company_id? }

# Atualizar (editar rule, toggle is_active)
PUT /api/v1/admin/guardrails/{id}

# Deletar (soft delete: is_active=false)
DELETE /api/v1/admin/guardrails/{id}

# Seed guardrails padrão (primários e secundários)
POST /api/v1/admin/guardrails/seed-defaults
```

**Schemas Pydantic:**
```python
class GuardrailCreate(BaseModel):
    level: Literal["primary", "secondary"] = "secondary"
    domain: str | None = None          # None = aplica a todos
    node: str | None = None            # None = aplica a todos os nós
    rule: str                          # regra em linguagem natural
    blocking_message: str | None = None
    company_id: str | None = None      # None = global

class GuardrailUpdate(BaseModel):
    rule: str | None = None
    blocking_message: str | None = None
    is_active: bool | None = None

class GuardrailResponse(BaseModel):
    id: str
    level: str
    domain: str | None
    node: str | None
    rule: str
    is_active: bool
    company_id: str | None
    updated_by: str | None
    updated_at: datetime
```

**Proxy FE:**
```
src/app/api/backend-proxy/admin/guardrails/route.ts
src/app/api/backend-proxy/admin/guardrails/[id]/route.ts
```

**Guardrails primários (seed obrigatório):**
```python
DEFAULT_PRIMARY_GUARDRAILS = [
    {"level": "primary", "rule": "Nunca revelar dados pessoais não compartilhados explicitamente pelo usuário."},
    {"level": "primary", "rule": "Nunca discriminar por gênero, raça, idade, religião, estado civil, deficiência ou origem."},
    {"level": "primary", "rule": "Sempre identificar interação como gerada por IA quando solicitado."},
    {"level": "primary", "rule": "Nunca criar perguntas que impliquem vida pessoal, familiar ou religiosa."},
    {"level": "primary", "rule": "Nunca confirmar ou negar existência de dados de usuário sem verificação de identidade."},
]

DEFAULT_SECONDARY_GUARDRAILS = [
    {"level": "secondary", "domain": "cv_screening", "rule": "Perguntas WSI exclusivamente sobre competências profissionais relevantes à vaga."},
    {"level": "secondary", "domain": "communication", "rule": "Todo email gerado por IA inclui identificação de IA no rodapé."},
    {"level": "secondary", "domain": "sourcing", "rule": "Nunca inferir atributos protegidos a partir de nome, localização ou foto de perfil."},
    {"level": "secondary", "domain": "job_management", "rule": "Requisitos de vaga não podem incluir características físicas ou atributos protegidos."},
]
```

**Testes:** `tests/unit/test_admin_guardrails_api.py` — CRUD completo (15+ testes)

**Esforço:** 2 dias | **Risco:** Baixo

---

### I2 — Alerta Automático de Falha de Agente (N falhas consecutivas)

**Contexto:** `drift_alert_service.py` alerta sobre model drift. Falta alerta genérico de falha de agente.

**Arquivo a criar:** `lia-agent-system/app/services/agent_health_alert_service.py`

**Lógica:**
```python
class AgentHealthAlertService:
    FAILURE_THRESHOLD = 3          # falhas consecutivas → WARNING
    CRITICAL_THRESHOLD = 5         # falhas → CRITICAL
    WINDOW_MINUTES = 30            # janela de análise
    REDIS_KEY = "agent_failures:{company_id}:{agent_id}"

    async def record_failure(self, company_id: str, agent_id: str, error: str):
        """Incrementa contador Redis. Dispara alerta se threshold atingido."""
        key = f"agent_failures:{company_id}:{agent_id}"
        count = await redis.incr(key)
        await redis.expire(key, self.WINDOW_MINUTES * 60)

        if count >= self.CRITICAL_THRESHOLD:
            await self._alert(company_id, agent_id, "CRITICAL", count)
        elif count >= self.FAILURE_THRESHOLD:
            await self._alert(company_id, agent_id, "WARNING", count)

    async def record_success(self, company_id: str, agent_id: str):
        """Reset contador após sucesso."""
        await redis.delete(f"agent_failures:{company_id}:{agent_id}")

    async def _alert(self, company_id, agent_id, level, count):
        await notification_service.notify(
            company_id=company_id,
            channels=["bell", "teams"],
            title=f"Agente {agent_id} com falhas consecutivas",
            body=f"{count} falhas em {self.WINDOW_MINUTES} min — nível {level}",
            level=level.lower()
        )
```

**Integração:** Chamar em `react_loop.py` no handler de exceção:
```python
except Exception as e:
    await agent_health_alert_service.record_failure(
        company_id=config.company_id,
        agent_id=config.domain,
        error=str(e)
    )
    raise
```

**Testes:** `tests/unit/test_agent_health_alert_service.py` (10+ testes)

**Esforço:** 1 dia | **Risco:** Baixo

---

### I3 — Consolidação de Legacy: `app/agents/` e `app/prompts/`

**Contexto:** ~96K linhas de código legacy ainda em uso ativo. Precisa de plano de deprecação controlado.

**Inventário de impacto:**

| Arquivo Legacy | Linhas | Importado por | Ação |
|----------------|:------:|---------------|------|
| `app/agents/base_agent.py` | 13.030 | orchestrator.py, intent_router.py, task_planner.py (5+) | Manter como shim temporário → migrar referências |
| `app/agents/policy_setup_agent.py` | 713 | hiring_policy.py | Mover para `app/domains/hiring_policy/agents/` |
| `app/prompts/kanban_assistant_prompts.py` | 45.272 | orchestrated_job_chat.py | Migrar conteúdo para `kanban_system_prompt.py` |
| `app/prompts/talent_assistant_prompts.py` | 21.147 | orchestrated_talent_chat.py | Migrar para `talent_system_prompt.py` |
| `app/prompts/job_wizard.py` | 15.454 | múltiplos | Migrar para `wizard_system_prompt.py` |

**Plano de migração em 3 etapas:**

**Etapa 1 (Sprint I3a) — Inventário e análise de dependências:**
- Mapear cada import ativo de `app/agents/` e `app/prompts/`
- Identificar o que é usado vs. dead code
- Criar lista de refatorações necessárias

**Etapa 2 (Sprint I3b) — Migração de prompts:**
- Mover conteúdo de `kanban_assistant_prompts.py` → `app/domains/recruiter_assistant/agents/kanban_system_prompt.py`
- Mover `talent_assistant_prompts.py` → `talent_system_prompt.py`
- Mover `job_wizard.py` → complementar `wizard_system_prompt.py`
- Executar testes de regressão por agente

**Etapa 3 (Sprint I3c) — Deprecação de base_agent.py:**
- Converter `base_agent.py` em shim que re-exporta de `lia_agents_core`
- Atualizar imports nos 5+ callers
- Arquivar `app/agents/` e `app/prompts/` como `_legacy_deprecated/`

**Critério de sucesso:** Todos os agentes passando nos testes após migração. Zero imports de `app/agents/` ou `app/prompts/` no código ativo.

**Esforço:** 5 dias | **Risco:** Médio (regressão possível) — exige testes de integração antes e depois

---

## SPRINT J-EXTRA — QUALIDADE DE AGENTES E AVALIAÇÃO (semanas 4-5)

> Sprint dedicado ao que estava na "Fase 3" do diagnóstico original e ainda não foi implementado.

---

### J1 — Framework de Avaliação Automática de Respostas de Agentes

**Contexto:** Sem avaliação automática, só é possível detectar degradação via drift (score agregado). Não há avaliação de qualidade de resposta individual.

**Abordagem:** Implementar avaliador leve baseado em LLM-as-judge (sem Ragas por ora — evitar dependência externa pesada). Integrar com LangSmith evaluators para staging.

**Arquivo a criar:** `lia-agent-system/app/services/agent_quality_evaluator.py`

```python
class AgentQualityEvaluator:
    """
    Avalia qualidade de respostas de agentes via LLM-as-judge.
    Executa em staging/shadow mode — não bloqueia produção.
    """

    METRICS = {
        "task_completion": "A tarefa solicitada foi completamente executada?",
        "factual_accuracy": "A resposta contém afirmações verificáveis e corretas?",
        "fairness": "A resposta é livre de viés discriminatório?",
        "coherence": "A resposta é coerente com o contexto da conversa?",
        "actionability": "A resposta oferece próximos passos claros?",
    }

    async def evaluate_response(
        self,
        *,
        agent_id: str,
        user_message: str,
        agent_response: str,
        context: dict,
        company_id: str,
    ) -> EvaluationResult:
        """
        Avalia uma resposta de agente.
        Retorna scores por métrica (0-1) + score agregado.
        Persiste em agent_quality_evaluations para trend analysis.
        """
        scores = {}
        for metric, question in self.METRICS.items():
            score = await self._judge(
                question=question,
                user_message=user_message,
                agent_response=agent_response,
                context=context,
            )
            scores[metric] = score

        overall = sum(scores.values()) / len(scores)

        result = EvaluationResult(
            agent_id=agent_id,
            company_id=company_id,
            scores=scores,
            overall_score=overall,
            evaluated_at=datetime.utcnow(),
        )
        await self._persist(result)
        return result

    async def _judge(self, question, user_message, agent_response, context) -> float:
        """LLM-as-judge via Claude Haiku (barato, suficiente para eval)."""
        prompt = f"""
Você é um avaliador de qualidade de sistemas de IA para recrutamento.

Pergunta de avaliação: {question}

Mensagem do usuário: {user_message}
Resposta do agente: {agent_response}

Responda APENAS com um número de 0.0 a 1.0.
0.0 = não satisfaz | 0.5 = parcialmente | 1.0 = totalmente satisfaz
"""
        response = await llm_service.generate(prompt, model="claude-haiku-4-5")
        return float(response.strip())
```

**Modelos de dados:**
```sql
-- Migration: 033_add_agent_quality_evaluations.py
CREATE TABLE agent_quality_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(100) NOT NULL,
    company_id VARCHAR(36) NOT NULL,
    session_id VARCHAR(100),
    overall_score FLOAT NOT NULL,
    scores JSONB NOT NULL,         -- {task_completion: 0.9, fairness: 1.0, ...}
    evaluated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    -- indexes: company_id, agent_id, evaluated_at
);
```

**Endpoint de trend:**
```
GET /api/v1/admin/agent-quality?agent_id=&company_id=&days=30
→ { avg_score, trend, scores_by_metric, samples_count }
```

**Execução:** Shadow mode (não bloqueia resposta ao usuário). Executar em background via Celery para ~10% das interações (sampling configurável via `QUALITY_EVAL_SAMPLING_RATE`).

**Integração com LangSmith:** Enviar resultado como feedback dataset para staging via `langsmith.Client().create_feedback()`.

**Testes:** `tests/unit/test_agent_quality_evaluator.py` (15+ testes)

**Esforço:** 3 dias | **Risco:** Baixo (shadow mode — não afeta produção)

---

### J2 — Few-shot T3 com Exemplos de RH Sênior

**Contexto:** Tier 3 do orchestrator (LLM few-shot) tem exemplos criados por programadores. André destacou que precisam ser co-criados com profissional sênior de RH.

**Arquivo:** `lia-agent-system/app/orchestrator/intent_router.py` ou `app/shared/prompts/v1/orchestrator_few_shot.py`

**Casos que precisam ser cobertos (por domínio):**

| Intenção | Mensagem Clara | Mensagem Ambígua |
|----------|---------------|-----------------|
| Wizard | "preciso criar uma vaga de dev sênior" | "vou contratar alguém novo" |
| Pipeline Triagem | "analisa o CV do João" | "o que você acha desse candidato" |
| Kanban | "quem está parado no pipeline" | "como está o funil" |
| Sourcing | "busca devs fullstack no mercado" | "preciso de candidatos" |
| JobsManagement | "status das vagas abertas" | "como estão as vagas" |
| Communication | "manda email pro candidato" | "avisa o candidato" |
| Policy | "quais são as regras de pipeline" | "como funciona nossa seleção" |

**Ação:**
1. Exportar 20 exemplos reais de conversas de recrutadores (anonymizados, LGPD)
2. Sessão de validação com profissional de RH (1-2h)
3. Atualizar `few_shot_examples` no `intent_router.py`
4. Adicionar métricas de acurácia do T3 ao dashboard de monitoramento

**Formato dos exemplos:**
```python
FEW_SHOT_EXAMPLES = [
    # Casos CLAROS (alta confiança esperada)
    FewShotExample(
        message="preciso criar uma nova vaga de desenvolvedor backend sênior para o time de plataforma",
        intent="job_wizard",
        domain="job_management",
        confidence=0.95,
        notes="cargo específico + senioridade + contexto claro"
    ),
    # Casos AMBÍGUOS (confiança esperada moderada → deve escalar)
    FewShotExample(
        message="vou precisar contratar alguém",
        intent="clarification_needed",
        domain=None,
        confidence=0.40,
        notes="sem cargo, sem contexto — deve pedir esclarecimento"
    ),
    # ... 20 casos total (10 claros + 10 ambíguos)
]
```

**Testes:** `tests/unit/test_intent_classification_few_shot.py` — verificar acurácia >85% nos 20 casos

**Esforço:** 2 dias (1 dev + 1 sessão RH) | **Risco:** Baixo

---

### J3 — Flag `auto_confirm` por Usuário/Domínio

**Contexto:** Agentes HITL pedem confirmação em cada ação crítica. Para usuários avançados, isso vira chatbot (feedback explícito do André).

**Abordagem:** Preferência por usuário persistida em banco. HITL pede confirmação na primeira vez e oferece opção de auto-confirmar daqui em diante para aquele tipo de ação.

**Modelo de dados:**
```sql
-- Migration: 034_add_user_agent_preferences.py
CREATE TABLE user_agent_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(36) NOT NULL,
    company_id VARCHAR(36) NOT NULL,
    domain VARCHAR(50) NOT NULL,       -- ex: "pipeline", "job_management"
    action_type VARCHAR(100) NOT NULL, -- ex: "move_candidate", "create_job"
    auto_confirm BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, company_id, domain, action_type)
);
```

**Integração em `hitl_service.py`:**
```python
async def request_approval(
    self, *, thread_id, action, description, data,
    domain, company_id, user_id, agent_input
) -> ApprovalRequest:

    # Verificar preferência de auto-confirm
    pref = await UserAgentPreferenceService.get(
        user_id=user_id, company_id=company_id,
        domain=domain, action_type=action
    )

    if pref and pref.auto_confirm:
        # Auto-aprova — sem interromper o agente
        await self._log_auto_approval(thread_id, action, domain, company_id, user_id)
        return ApprovalRequest(auto_approved=True, pending_id=None)

    # Fluxo normal de HITL
    pending = await self._create_pending_action(...)
    return ApprovalRequest(auto_approved=False, pending_id=pending.id)
```

**Frontend — componente HITLConfirmCard atualizado:**
```tsx
// HITLConfirmCard.tsx — adicionar checkbox "sempre confirmar automaticamente"
<label className="flex items-center gap-2 text-xs text-gray-500 mt-3">
  <input
    type="checkbox"
    checked={rememberChoice}
    onChange={(e) => setRememberChoice(e.target.checked)}
  />
  Confirmar automaticamente esta ação no futuro
</label>

// onConfirm envia { approved: true, auto_confirm: rememberChoice }
```

**Endpoint:**
```
POST /api/v1/user-preferences/agent
Body: { domain, action_type, auto_confirm: bool }
```

**Testes:** `tests/unit/test_user_agent_preferences.py` (10+ testes)

**Esforço:** 2 dias | **Risco:** Baixo

---

## SPRINT K — COMPLIANCE DE CANAL E TESTES (semanas 6-7)

---

### K1 — Cláusula LGPD Específica para Twilio/Email Providers

**Contexto:** Termos de privacidade têm menção genérica a "Política de Privacidade". André e requisito LGPD exigem declaração explícita de compartilhamento com sub-processadores.

**Arquivos a atualizar:**

**1. `app/templates/communication_templates.py`:**
```python
# Adicionar ao template de primeiro contato WSI
DATA_PROCESSING_NOTICE = """
📋 Processamento de Dados:
Sua participação neste processo seletivo envolve o processamento de dados pessoais
pela WeDOTalent. As comunicações via WhatsApp são processadas pela Twilio Inc.
(EUA) sob acordos de proteção de dados adequados. Emails são processados pela
SendGrid/Resend sob condições equivalentes. Você pode solicitar exclusão de seus
dados a qualquer momento em {privacy_portal_url}. Gerado por IA — LIA Assistant.
"""
```

**2. Documentação legal (fora do código):**
- Atualizar DPA (Data Processing Agreement) com Twilio/SendGrid como sub-processadores
- Incluir na Política de Privacidade pública: lista de sub-processadores de dados
- Adicionar mecanismo de opt-out de comunicação WhatsApp no portal LGPD

**3. `app/services/email_providers/base.py`:**
```python
# Garantir que todo email tenha footer com identificação IA + LGPD link
BASE_EMAIL_FOOTER = """
---
Este email foi gerado com assistência de Inteligência Artificial (LIA by WeDOTalent).
Política de Privacidade: {privacy_url} | Opt-out: {optout_url}
WeDOTalent Ltda. — CNPJ XX.XXX.XXX/XXXX-XX
"""
```

**Esforço:** 1 dia (dev) + aprovação jurídica | **Risco:** Baixo

---

### K2 — Testes de Integração de Agentes (Cobertura 29% → 40%)

**Contexto:** Coverage em 29%. Gate está em 25%. Meta produção é 40% com testes de integração de agentes reais.

**Estratégia:** 6 novos arquivos de teste de integração:

**1. `tests/integration/test_wizard_flow.py`** — fluxo completo de criação de vaga:
```python
async def test_create_job_full_flow():
    """Wizard → FairnessGuard → HITL interrupt → aprovação → vaga criada"""
    # Setup: job_id, company_id, user_id
    # Step 1: iniciar wizard
    # Step 2: fornecer dados da vaga
    # Step 3: wizard chega em stage_transition → HITL
    # Step 4: aprovar via hitl_service
    # Step 5: verificar vaga criada no banco
    # Step 6: verificar FairnessGuard foi chamado
```

**2. `tests/integration/test_wsi_interview_flow.py`** — fluxo de entrevista WSI:
```python
async def test_wsi_interview_with_hitl():
    """WSI: 8 estágios → HITL antes de feedback → score persistido"""
```

**3. `tests/integration/test_pipeline_transition_flow.py`** — transição com aprovação:
```python
async def test_pipeline_move_with_approval():
    """PipelineTransition → HITL → aprovação → candidato movido"""
```

**4. `tests/integration/test_sourcing_search_flow.py`** — busca e engajamento:
```python
async def test_sourcing_search_and_engage():
    """Sourcing → RAG search → compose message → FairnessGuard → send"""
```

**5. `tests/integration/test_rag_and_toon.py`** — busca semântica + TOON card:
```python
async def test_rag_hybrid_search_returns_toon():
    """RAG search → top result → TOON generation → Redis cache"""
```

**6. `tests/integration/test_drift_and_bias_audit.py`** — compliance end-to-end:
```python
async def test_drift_detection_triggers_alert():
    """Injetar score drift → drift_job → alert → Bell notification"""

async def test_bias_audit_four_fifths_rule():
    """Criar candidatos sintéticos → rodar bias audit → verificar ratios"""
```

**Configuração de CI:**
```yaml
# .github/workflows/ci.yml — adicionar step de integração
- name: Run integration tests
  run: pytest tests/integration/ -v --timeout=60
  continue-on-error: false
```

**Meta de coverage:** 40% (de 29,05%)

**Esforço:** 4 dias | **Risco:** Médio (dependências de DB/Redis reais em CI)

---

### K3 — Testes de Carga: 50 Candidatos Simultâneos

**Contexto:** Sem testes de carga com cenários reais. Diagnóstico apontou risco de colapso em produção para alto volume (ex: 50 CVs em triagem simultânea).

**Ferramenta:** Locust (Python, sem dependência nova — já Python stack)

**Arquivo a criar:** `tests/load/locustfile.py`

```python
from locust import HttpUser, task, between
import random

class RecruitmentWorkflow(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def candidate_search(self):
        """Simula busca de candidatos (alta frequência)"""
        self.client.get(
            "/api/v1/candidates/rag-search",
            params={"q": "desenvolvedor python", "company_id": TEST_COMPANY, "limit": 20}
        )

    @task(2)
    def toon_card(self):
        """Simula geração de TOON card"""
        candidate_id = random.choice(TEST_CANDIDATE_IDS)
        self.client.get(f"/api/v1/candidates/{candidate_id}/toon",
                       params={"job_id": TEST_JOB_ID, "company_id": TEST_COMPANY})

    @task(1)
    def wsi_screening_batch(self):
        """Simula triagem batch WSI (menor frequência, operação pesada)"""
        self.client.post("/api/v1/async/triagem/run-batch",
                        json={"job_id": TEST_JOB_ID, "company_id": TEST_COMPANY,
                              "candidate_ids": random.sample(TEST_CANDIDATE_IDS, 5)})

    @task(1)
    def wizard_interaction(self):
        """Simula turno de wizard"""
        self.client.post("/api/v1/wizard-smart-orchestrator",
                        json={"message": "quero criar uma vaga de dev sênior",
                              "session_id": f"test-{random.randint(1,100)}",
                              "company_id": TEST_COMPANY})
```

**Cenários de teste:**
1. **Cenário base:** 10 usuários simultâneos por 5 min → P95 < 2s
2. **Cenário alto volume:** 50 triagens simultâneas → sem timeout, sem 5xx
3. **Cenário pico:** Ramp de 0→100 usuários em 2 min → observar graceful degradation

**Critérios de aprovação:**
- P50 < 500ms (busca), P50 < 2s (wizard)
- P95 < 2s (busca), P95 < 5s (wizard)
- Error rate < 1% em 50 usuários simultâneos
- Zero 5xx em cenário base

**Esforço:** 2 dias (setup + execução + análise) | **Risco:** Baixo para setup, resultado pode revelar problemas

---

## SPRINT L — FRONTEND: ELIMINAR MOCK DATA (semanas 7-8)

---

### L1 — Auditoria e Eliminação de Mock Data

**Contexto:** 35+ arquivos com mock data no frontend. Maioria como fallback defensivo (correto), mas algumas telas com dados hardcoded iniciais (problema).

**Ação 1 — Mapear todos os mocks:**
```bash
grep -rn "mockConsents\|mockDSRs\|mockIntegrations\|hardcoded\|TODO.*real" \
  plataforma-lia/src/ --include="*.tsx" --include="*.ts" > mock_audit.txt
```

**Classificação dos mocks encontrados:**

| Tipo | Ação |
|------|------|
| Fallback defensivo (API indisponível) | ✅ Manter — bom design |
| Dados iniciais (tela carrega com mocks) | ❌ Remover — conectar API real |
| Mock temporário com `// TODO: real data` | ❌ Implementar endpoint |
| Dados de exemplo em formulários | ✅ Manter (UX) |

**Telas prioritárias para auditoria:**
1. `/admin/clientes/[clientId]/observabilidade/page.tsx` — `mockConsents`, `mockDSRs`, `mockIntegrations`
2. `/admin/compliance/auditoria/bias/page.tsx` — verificar se usa dados reais
3. Dashboard principal — verificar KPIs reais vs. mock

**Ação 2 — Para cada mock de dados reais: implementar endpoint ou conectar existente.**

**Ação 3 — Teste ponta a ponta (Alpha 1):**
```
Login → Criar Vaga (Wizard) → Buscar Candidatos (RAG)
→ Triagem WSI → Aprovar HITL → Feedback → Candidato Avançado
```

**Esforço:** 3 dias | **Risco:** Médio (pode revelar endpoints faltando)

---

## RESUMO DO PLANO — CRONOGRAMA

| Sprint | Itens | Duração | Prioridade |
|--------|-------|---------|-----------|
| **H** | H1 (truncamento reasoning), H2 (print statement) | 1 semana | 🔴 Crítico |
| **I** | I1 (API guardrails), I2 (alerta falha agente), I3 (legacy consolidation) | 2-3 semanas | 🟡 Alta |
| **J** | J1 (evaluação qualidade), J2 (few-shot RH), J3 (auto_confirm) | 2-3 semanas | 🟡 Alta |
| **K** | K1 (LGPD Twilio), K2 (testes integração), K3 (carga) | 2-3 semanas | 🟡 Alta |
| **L** | L1 (mock data FE) | 1-2 semanas | 🟡 Média |

**Total estimado:** 8-12 semanas (Sprint H paralelo aos outros onde possível)

---

## CHECKLIST DE PRONTIDÃO PARA PRODUÇÃO

### ✅ JÁ RESOLVIDO (não precisa de ação)
- [x] Loop agêntico ReAct real (`react_loop.py`)
- [x] Multi-provider LLM com CircuitBreaker (Claude→OpenAI→Gemini)
- [x] Cascata de confiança T3 (Haiku→Sonnet→Opus) — `llm_cascade.py`
- [x] FairnessGuard 3 camadas com FAIRNESS_LAYER3_ENABLED
- [x] Tabela `guardrails` no banco (migration 020)
- [x] Padrão 4 arquivos por agente (todos os 9 domínios)
- [x] WebSocket `/ws/chat/{session_id}` para streaming LLM
- [x] WebSocket `/ws/jobs/{job_id}` para progresso async
- [x] AsyncJobResponse padrão para operações agênticas
- [x] EntrevistadorWSI integrado com Celery queue
- [x] Dashboard de saúde de agentes (`agent_monitoring.py`)
- [x] ADR: Graph vs. ReAct (`docs/adr/002-graph-vs-react.md`)
- [x] HITL multi-tenant com `domain` + `company_id` (Sprint G1)
- [x] RAG Híbrido BM25 + pgvector (Sprint G6)
- [x] TOON Service com LGPD anonymize (Sprint G7)
- [x] Token Budget multi-tenant (4 planos)
- [x] Model Drift Detection + Celery Beat diário
- [x] Bias Audit (Four-Fifths Rule) com snapshot SOX
- [x] PromptInjectionGuard (40+ patterns)
- [x] Disclosure de IA em emails (`communication_templates.py`)
- [x] YAML Tool Registry (32 tools declaradas)
- [x] company_id + user_id em todos os traces
- [x] `max_iterations` configurável via env var
- [x] `REACT_MAX_ITERATIONS_DEFAULT` (não hardcoded magic number)

### 🔴 CRÍTICO — RESOLVER ANTES DE QUALQUER DEPLOY
- [ ] **H1** — `reasoning` truncado a 500 chars em `react_loop.py:278`
- [ ] **H2** — `print(state.wsi_final_score)` em `wsi_interview_graph.py`

### 🟡 ALTA PRIORIDADE — RESOLVER ANTES DE PRODUÇÃO
- [ ] **I1** — CRUD API para guardrails editáveis via admin
- [ ] **I2** — Alerta automático de N falhas consecutivas de agente
- [ ] **I3** — Plano de deprecação de `app/agents/` e `app/prompts/` (96K linhas legacy)
- [ ] **J1** — Framework de avaliação automática de qualidade (LLM-as-judge)
- [ ] **J2** — Few-shot T3 co-criado com profissional sênior de RH
- [ ] **J3** — Flag `auto_confirm` por usuário/domínio (UX anti-chatbot)
- [ ] **K1** — Cláusula LGPD específica para Twilio/SendGrid nos Termos
- [ ] **K2** — Testes de integração de agentes (coverage 29% → 40%)
- [ ] **K3** — Teste de carga: 50 candidatos simultâneos com Locust
- [ ] **L1** — Auditoria e eliminação de mock data no frontend

### 📋 COMPLEMENTAR — PÓS-PRODUÇÃO
- [ ] Migração final CLAUDE.md: remover referência Ruby/Rails como backend futuro
- [ ] Ragas/DeepEval para avaliação contínua em staging (após J1 estabilizar)
- [ ] Versionamento formal de prompts (`app/shared/prompts/v1/`)
- [ ] Red team formal de FairnessGuard (<1% jailbreak em 100 testes)
- [ ] Sampling 5% de decisões para revisão humana (LGPD + SOX)

---

## DECISÃO ARQUITETURAL PENDENTE: RUBY/RAILS NO CLAUDE.md

O `CLAUDE.md` atual menciona migração futura para Ruby on Rails como backend. O especialista André foi **explicitamente contrário** por razões técnicas sólidas:

> *"Se a ideia era migrar tudo para Ruby, não façam isso, vai ser uma merda."*

**Razões técnicas:**
- Garbage collector ineficiente para alto volume
- Não libera memória para o SO adequadamente
- Python tem vantagem clara para ML/processamento de IA
- `multiprocessing` Python permite uso eficiente de múltiplos cores

**Ação necessária:** Atualizar `CLAUDE.md` para documentar a decisão de manter Python (FastAPI) como backend permanente, removendo referência a Rails.

---

## REFERÊNCIAS

| Documento | Caminho |
|-----------|---------|
| Diagnóstico v4.0 (base deste plano) | `docs/DIAGNOSTICO_ARQUITETURA_IA_v4.0.md` |
| Mapa de Inteligência (atualizado) | `docs/analises/MAPA_INTELIGENCIA_LIA_COMPLETO.md` |
| ADR: Graph vs ReAct | `docs/adr/002-graph-vs-react.md` |
| ADR: Python vs Ruby | `docs/adr/001-python-not-ruby.md` |
| Design System v4.2.1 | `plataforma-lia/docs/design-system/00-design-system-v4.md` |

---

*Plano criado em 09/03/2026.*
*Revisão: após conclusão de Sprint H (resolução dos 2 itens críticos).*
