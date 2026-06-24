# WeDOTalent Pattern Library — Receitas de Replicação
**Versão:** 2026-06-17
**Objetivo:** 10 receitas passo-a-passo para implementar patterns canônicos da plataforma. Cada receita inclui código minimal, checklist de validação e sensores obrigatórios.

---

## PATTERN-01: Novo Domínio com `@register_domain`

### Quando usar
Criar um novo agente de domínio (ex: `workforce`, `benefits`, `onboarding`) que o MainOrchestrator e CascadedRouter podem rotear automaticamente.

### Pré-requisitos
- Entender qual é a responsabilidade do domínio (1 frase clara)
- Listar 3-10 tools que o domínio vai expor
- Confirmar que não há sobreposição com domínio existente

### Receita

**Passo 1: Criar estrutura de diretórios**
```bash
mkdir -p app/domains/<nome>/services
mkdir -p app/domains/<nome>/repositories
mkdir -p app/domains/<nome>/tools
touch app/domains/<nome>/__init__.py
touch app/domains/<nome>/tools/__init__.py
```

**Passo 2: Criar o prompt de domínio**
```python
# app/domains/<nome>/domain_prompt.py
from app.shared.base_domain_prompt import ComplianceDomainPrompt

@register_domain(
    name="<nome>",
    description="<1 frase descrevendo o domínio>",
    version="1.0.0",
    compliance_tags=["multi_tenancy"],  # + "lgpd" se toca PII, "fairness" se toca candidatos
)
class <Nome>DomainPrompt(ComplianceDomainPrompt):
    DOMAIN_CONTEXT = """
    Você é especialista em <domínio>. Suas responsabilidades incluem:
    - <responsabilidade 1>
    - <responsabilidade 2>
    """
    
    TOOL_DESCRIPTIONS = {
        "<tool_name>": "<descrição da tool>",
    }
```

**Passo 3: Criar tools com wrapper canônico**
```python
# app/domains/<nome>/tools/<tool_name>.py
from app.shared.tool_handler import tool_handler
from app.shared.runtime_context import with_runtime_context

@with_runtime_context("company_id")   # opcional — declara dependência
@tool_handler("<nome>")               # OBRIGATÓRIO — fail-closed multi-tenancy
async def _wrap_<tool_name>(**kwargs) -> dict:
    company_id = kwargs["company_id"]  # garantido pelo tool_handler
    # ... lógica da tool
    return {"success": True, "data": {...}}
```

**Passo 4: Criar repositório com `_require_company_id`**
```python
# app/domains/<nome>/repositories/<nome>_repository.py
from app.shared.base_repository import BaseRepository

class <Nome>Repository(BaseRepository):
    
    def _require_company_id(self, company_id: str) -> None:
        if not company_id:
            raise ValueError("company_id required — multi-tenancy violation")
    
    async def get_by_company(self, company_id: str, ...) -> list:
        self._require_company_id(company_id)
        # ... query
```

**Passo 5: Registrar no capability catalog**
```yaml
# docs/action-surface-registry/_REGISTRY.yaml (adicionar entrada)
- domain: <nome>
  tools:
    - name: <tool_name>
      handler: app.domains.<nome>.tools.<tool_name>._wrap_<tool_name>
      description: <descrição>
      hitl_required: false  # ou true se ação sensível
```

### Checklist de Validação
- [ ] `@register_domain` presente com `name`, `description`, `version`
- [ ] `@tool_handler("<nome>")` em TODA tool (fail-closed)
- [ ] `_require_company_id()` em todo método público de repositório
- [ ] `company_id` NUNCA no request payload (vem do JWT)
- [ ] FairnessGuard.check() em tools que recebem texto livre sobre candidatos
- [ ] Entrada no `_REGISTRY.yaml` (anti-ghost sensor)
- [ ] Testes em `tests/domains/<nome>/`

### Sensor
```bash
# Anti-ghost: verifica que toda tool declarada tem handler real
python scripts/check_capability_catalog_sync.py
```

---

## PATTERN-02: Tool com HITL Gate

### Quando usar
Tool que executa ação irreversível ou de alto impacto: enviar email, rejeitar candidato, publicar vaga, fechar vaga.

### Receita

**Passo 1: Marcar tool como HITL-required no catalog**
```yaml
# _REGISTRY.yaml
- name: <tool_name>
  hitl_required: true
  hitl_category: "sensitive_action"  # email | rejection | publication | financial
```

**Passo 2: Adicionar `hitl_preflight` na tool**
```python
from app.shared.hitl_service import hitl_preflight, HITLGateError

@tool_handler("<domínio>")
async def _wrap_<tool_name>(**kwargs) -> dict:
    company_id = kwargs["company_id"]
    
    # Gate HITL (dormant se LIA_HITL_GATE=off)
    try:
        await hitl_preflight(
            tool_name="<tool_name>",
            context={"target": kwargs.get("target_id"), "company_id": company_id},
        )
    except HITLGateError as e:
        # Retorna approval_required ao SSE — NÃO executa a ação
        return {"hitl_pending": True, "approval_id": str(e.approval_id), "message": e.user_message}
    
    # ... executa a ação somente após aprovação
```

**Passo 3: FE — tratar `approval_required` no SSE**
```typescript
// useChatSocket.ts
case "approval_required":
  setHITLPending({
    approvalId: frame.approval_id,
    toolName: frame.tool_name,
    message: frame.message,
  });
  break;

// Após usuário aprovar:
const sendApproval = async (approvalId: string) => {
  await fetch("/api/v1/agent-chat/sse", {
    method: "POST",
    body: JSON.stringify({
      message: `__approve__:${approvalId}`,
      session_id: currentSessionId,
    }),
  });
};
```

### Nota Importante
- `LIA_HITL_GATE=off` (default): `hitl_preflight()` é no-op → zero regressão em produção
- `LIA_HITL_GATE=on`: ativa o gate → aprovação obrigatória
- Supervisor (MainOrchestrator path): tem HITL próprio via `intents_config` — NÃO há double-gate

---

## PATTERN-03: Novo Learning Loop

### Quando usar
Adicionar um mecanismo onde outcomes reais (contratações, recusas, conversões) melhoram decisões futuras de IA.

### Receita

**Passo 1: Criar tabela de outcomes**
```sql
-- alembic/versions/<NNN>_add_<nome>_outcomes.py
CREATE TABLE <nome>_outcomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id),
    candidate_id UUID REFERENCES candidates(id),
    vacancy_id UUID REFERENCES job_vacancies(id),
    feature_vector JSONB NOT NULL,  -- scores/features do momento
    outcome VARCHAR(50) NOT NULL,   -- 'hired', 'rejected', 'converted'
    outcome_date TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX ON <nome>_outcomes (company_id, outcome_date);
```

**Passo 2: Criar repositório**
```python
class <Nome>OutcomesRepository(BaseRepository):
    async def record_outcome(
        self, company_id: str, candidate_id: str, 
        feature_vector: dict, outcome: str
    ) -> None:
        self._require_company_id(company_id)
        # INSERT INTO <nome>_outcomes ...
    
    async def get_outcomes_for_training(
        self, company_id: str, min_samples: int = 10
    ) -> list[dict]:
        self._require_company_id(company_id)
        # Retorna outcomes apenas se sample_count >= min_samples (ADR-LGPD-001)
```

**Passo 3: Criar serviço com Welford (se agregado)**
```python
# Se o loop produz um agregado (como BigFive dept profile):
class <Nome>LearningService:
    MIN_SAMPLES = 10  # ADR-LGPD-001: anonimização threshold
    
    async def update_aggregate(self, company_id: str, group_key: str, new_value: float):
        profile = await self.repo.get_or_create(company_id, group_key)
        n = profile.sample_count + 1
        delta = new_value - profile.mean
        new_mean = profile.mean + delta / n
        # Welford M2 para variance (sem armazenar valores individuais)
        profile.mean = new_mean
        profile.sample_count = n
        await self.repo.save(profile)
    
    async def get_aggregate(self, company_id: str, group_key: str) -> float | None:
        profile = await self.repo.get(company_id, group_key)
        if not profile or profile.sample_count < self.MIN_SAMPLES:
            return None  # Não usa até ter anonimização válida
        return profile.mean
```

**Passo 4: Registrar hook em TransitionDispatchService**
```python
# app/domains/communication/services/transition_dispatch_service.py
async def _hook_conclusion_hired(self, ...):
    # ... hooks existentes ...
    
    # Novo hook:
    try:
        await self.<nome>_learning_service.record_outcome(
            company_id=company_id,
            candidate_id=candidate_id,
            feature_vector=current_features,
            outcome="hired",
        )
    except Exception as e:
        # NUNCA falha a transição por erro no hook de aprendizado
        logger.warning(f"Learning hook failed (non-blocking): {e}", exc_info=True)
```

### Invariantes LGPD (ADR-LGPD-001)
- Agregado Welford sem armazenar valores individuais = anonimização válida (Art. 12 §1)
- `MIN_SAMPLES=10` gate na LEITURA (não na escrita)
- Erasure de candidato individual NÃO requer recompute do agregado

---

## PATTERN-04: Nova Configuração de Empresa

### Quando usar
Adicionar um novo toggle, instrução ou campo de configuração que os recrutadores definem em "Configurações" e que os agentes devem respeitar.

### Receita

**Passo 1: Adicionar campo ao modelo**
```python
# libs/models/lia_models/company_profile.py ou hiring_policy.py
class CompanyHiringPolicy(Base):
    # ... campos existentes ...
    nova_config: bool = Column(Boolean, default=False)
    # OU para instrução texto:
    nova_instrucao: str | None = Column(Text, nullable=True)
```

**Passo 2: Criar migration**
```bash
# No Replit:
cd /home/runner/workspace/lia-agent-system
# Verificar último número: ls alembic/versions/ | grep -oE '^[0-9]+' | sort -un | tail -3
alembic revision --autogenerate -m "add nova_config to hiring_policy"
# Editar a migration gerada para ser específica
alembic upgrade head
```

**Passo 3: Adicionar ao `lia_field_toggles` SE for controle de contexto de IA**
```python
# libs/models/lia_models/lia_field_toggles.py
DEFAULT_FIELD_TOGGLES = {
    # ... existentes ...
    "nova_config": {
        "label": "Nova Configuração",
        "description": "Descrição do que controla",
        "default": True,
        "category": "empresa",  # candidato | empresa | vaga
    }
}
```

**Passo 4: Implementar consumer — NÃO criar toggle sem consumer**
```python
# SE for gate hard (fail-closed):
class MeuService:
    async def check_can_fazer_algo(self, company_id: str) -> None:
        policy = await self.policy_repo.get(company_id)
        if not policy.nova_config:
            raise PermissionError("nova_config está desativado para esta empresa")
    
    async def fazer_algo(self, ...):
        await self.check_can_fazer_algo(company_id)  # pre-flight
        # ... ação ...
        # Defense-in-depth: verificar novamente se necessário

# SE for instrução de IA (soft):
# LiaFieldConfigService.get_filtered_context() já carrega automaticamente
# se o campo estiver em DEFAULT_FIELD_TOGGLES e o toggle ON
# Basta chamar build_company_agent_context() no agente
```

**Passo 5: Sincronizar frontend**
```typescript
// plataforma-lia/src/components/settings/ConfigHub.tsx
// Adicionar toggle com label+description espelhando DEFAULT_FIELD_TOGGLES
// Usar SETTINGS_QUERY_KEYS.settingsProgress() para invalidar cache após save

// Sensor de sync:
// python scripts/check_lia_field_definitions_sync.py
// Falha se LIA_FIELD_DEFINITIONS (FE) !== DEFAULT_FIELD_TOGGLES (BE)
```

### Regra Absoluta
**Todo toggle exposto em Configurações DEVE ter consumer real.** Toggle sem consumer = ghost setting = mentira para o usuário. Sensor: revisar `lia_field_toggles` periodicamente com `grep -r "nova_config" app/` para confirmar que existe ao menos 1 ponto de leitura além do UI.

---

## PATTERN-05: Nova Inferência no Wizard

### Quando usar
Adicionar uma etapa ao WizardOrchestrator que infere/sugere dados a partir do input do recrutador.

### Receita

**Passo 1: Registrar a nova tool no WizardOrchestrator**
```python
# app/orchestrators/wizard_orchestrator.py
WIZARD_TOOLS = [
    # ... existentes ...
    "nova_inferencia",
]

async def _wrap_nova_inferencia(**kwargs) -> dict:
    company_id = kwargs["company_id"]  # do JWT via tool_handler
    vacancy_id = kwargs["vacancy_id"]
    
    # Busca dados da vaga
    vacancy = await job_repo.get(vacancy_id, company_id)
    
    # Deriva sugestão de SINAL REAL (nunca inventa)
    suggestion = None
    provenance = None
    
    if vacancy.job_description:
        # Infere de sinal real
        suggestion = extract_from_jd(vacancy.job_description)
        provenance = "derivado_da_jd"
    
    return {
        "suggestion": suggestion,
        "provenance": provenance,
        "confidence": "high" if suggestion else "none",
        "message": f"Sugestão baseada na descrição da vaga" if suggestion else "Nenhum sinal encontrado",
    }
```

**Passo 2: Regra de Proveniência**
```python
# CORRETO: derivar de sinal real com declaração
return {
    "suggestion": "São Paulo",
    "provenance": "email_domain",
    "note": "Deduzi pelo domínio do email de contato — confirme"
}

# INCORRETO: inventar sem sinal
return {
    "suggestion": "São Paulo",  # inventado sem evidência
    "provenance": "market_estimate",  # falso
}
```

**Passo 3: Adicionar ao prompt do wizard**
```yaml
# app/prompts/wizard/wizard_orchestrator_prompt.yaml
tools:
  - name: nova_inferencia
    description: "Infere <dado> a partir de <sinal>. Use quando <condição>."
    when_to_use: "Após intake_job_info, antes de suggest_salary"
    output_handling: "Apresente como sugestão, não como fato definitivo"
```

---

## PATTERN-06: Novo Voice Plugin

### Quando usar
Adicionar um canal de coleta de dados ou triagem via voz (Twilio + Gemini Live).

### Receita

**Passo 1: Herdar de BaseVoicePlugin**
```python
# app/domains/voice/plugins/<nome>_voice_plugin.py
from app.domains.voice.plugins.base_voice_plugin import BaseVoicePlugin
from app.domains.voice.services.voice_rate_limiter import check_voice_budget, increment_voice_calls

class <Nome>VoicePlugin(BaseVoicePlugin):
    
    # OBRIGATÓRIO: CONSENT_QUESTION hardcoded (nunca parametrizar com ai_name)
    CONSENT_QUESTION: str = (
        "Você autoriza a WeDOTalent a coletar e tratar seus dados pessoais para "
        "o seu processo seletivo, conforme a LGPD? Por favor responda sim ou não."
    )
    
    async def on_session_initiated(self, session: VoiceSession) -> str:
        """Saudação personalizada por tenant — ai_name OK aqui (informacional)"""
        ai_name = await self._get_ai_name(session.company_id)
        return self._build_recording_notice(ai_name)
    
    async def start_collection(self, company_id: str, candidate_id: str, ...) -> dict:
        # 1. Validação de dados
        # 2. Consentimento LGPD
        consent = await consent_service.check(candidate_id, purpose=self.CONSENT_PURPOSE)
        if not consent:
            return {"status": "consent_required"}
        
        # 3. Budget gate (REGRA: antes de initiate_call)
        allowed, calls_count = await check_voice_budget(company_id)
        if not allowed:
            return {
                "status": "voice_collection_budget_exceeded",
                "calls_this_month": calls_count,
                "limit": VOICE_CALLS_MONTHLY_DEFAULT_LIMIT,
            }
        
        # 4. Iniciar chamada
        result = await self.voice_orchestrator.initiate_call(...)
        
        # 5. Incrementar SOMENTE em sucesso
        if result.get("orch_status") == "initiated":
            await increment_voice_calls(company_id)
        
        return result
```

**Passo 2: Sensores obrigatórios**
```python
# tests/unit/test_<nome>_voice_plugin.py
def test_consent_question_is_lgpd_literal():
    """CONSENT_QUESTION não pode ter interpolação de ai_name"""
    from app.domains.voice.plugins.<nome>_voice_plugin import <Nome>VoicePlugin
    q = <Nome>VoicePlugin.CONSENT_QUESTION
    assert "{" not in q and "}" not in q, "CONSENT_QUESTION não pode ter interpolação"
    assert "WeDOTalent" in q, "CONSENT_QUESTION deve citar WeDOTalent como controlador legal"

def test_budget_gate_before_initiate():
    """Budget gate deve impedir chamada quando excedido"""
    # ...

def test_increment_only_on_initiated():
    """Incremento só ocorre quando orch_status == 'initiated'"""
    # ...
```

### Regras Invioláveis
- `CONSENT_QUESTION` sempre hardcoded com "WeDOTalent" (controlador legal LGPD Art. 7/9)
- Budget gate ANTES de `initiate_call`
- Incremento SOMENTE em `orch_status == "initiated"`
- Fail-open no check de budget (Redis down → permite chamada)

---

## PATTERN-07: FairnessGuard em Nova Surface

### Quando usar
Qualquer novo endpoint que recebe texto livre de recrutador para ser processado por LLM ou gravado como critério de seleção.

### Receita

**Passo 1: Adicionar gate no endpoint**
```python
# app/api/v1/<seu_endpoint>.py
from app.shared.compliance.fairness_guard import FairnessGuard
from fastapi import HTTPException

_fg = FairnessGuard()

@router.post("/<rota>")
async def meu_endpoint(
    payload: MeuSchema,
    company_id: str = Depends(require_company_id),
    recruiter_id: str = Depends(require_user_id),
):
    # Gate ANTES de qualquer LLM ou DB write
    if payload.query_text:  # ou qualquer campo texto livre
        result = _fg.check(payload.query_text)
        if result.is_blocked:
            # Logar para audit trail
            result.log_check(
                company_id=company_id,
                recruiter_id=recruiter_id,
                session_id=getattr(payload, "session_id", None),
            )
            raise HTTPException(400, detail={
                "error": "fairness_blocked",
                "fairness_blocked": True,
                "educational_message": result.educational_message,
                "category": result.category,
                "blocked_terms": result.blocked_terms or [],
            })
    
    # ... continua com a lógica normal
```

**Passo 2: FE — tratar a resposta**
```typescript
// Hook de chamada
const { data, error } = await myApiCall(payload);

if (error?.status === 400) {
  const body = await error.json();
  if (body?.error === "fairness_blocked" || body?.fairness_blocked) {
    setFairnessBlocked({
      message: body.educational_message,
      category: body.category,
    });
    return;
  }
}

// JSX — banner âmbar
{fairnessBlocked && (
  <div role="alert" className="bg-amber-50 border border-amber-200 p-3 rounded">
    <ShieldAlertIcon className="inline mr-2 text-amber-600" />
    {fairnessBlocked.message}
    <button onClick={() => setFairnessBlocked(null)}>Entendi</button>
  </div>
)}
```

**Passo 3: Teste TDD obrigatório**
```python
# tests/unit/test_fairness_<surface>.py
@pytest.mark.asyncio
async def test_fairness_blocks_discriminatory_query():
    response = await client.post("/<rota>", json={
        "query_text": "candidatos jovens apenas",  # discriminação por idade
    }, headers={"Authorization": f"Bearer {token}"})
    
    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "fairness_blocked"
    assert body["fairness_blocked"] is True
    assert "educational_message" in body
    assert "categoria" in body or "category" in body

@pytest.mark.asyncio
async def test_fairness_logs_to_audit():
    # Verifica que log_check() foi chamado
    with patch.object(FairnessGuard, "check") as mock_check:
        mock_result = MagicMock(is_blocked=True, educational_message="...", category="age")
        mock_check.return_value = mock_result
        
        await client.post("/<rota>", json={"query_text": "jovens"}, headers=...)
        
        mock_result.log_check.assert_called_once()
```

---

## PATTERN-08: Novo Agente no Agent Studio

### Quando usar
Criar um agente custom que recrutadores podem instalar no Agent Studio via `CustomAgentRuntime`.

### Receita

**Passo 1: Criar o agente no format Agent Studio**
```python
# app/domains/agent_studio/agents/<nome>_agent.py
from app.domains.agent_studio.base_custom_agent import BaseCustomAgent

class <Nome>CustomAgent(BaseCustomAgent):
    
    AGENT_MANIFEST = {
        "id": "<nome>_agent",
        "name": "<Nome> Agent",
        "description": "<descrição pública>",
        "version": "1.0.0",
        "author": "WeDOTalent",
        "category": "sourcing",  # sourcing | screening | analytics | communication
        "required_permissions": ["read_candidates", "read_vacancies"],
        "tools": ["<tool_1>", "<tool_2>"],
    }
    
    async def run(self, prompt: str, context: AgentContext) -> AgentResponse:
        company_id = context.company_id  # SEMPRE do contexto, nunca do prompt
        
        # FairnessGuard em texto livre
        fg_result = self._fg.check(prompt)
        if fg_result.is_blocked:
            return AgentResponse(
                success=False,
                educational_message=fg_result.educational_message,
                fairness_blocked=True,
            )
        
        # ... lógica do agente
```

**Passo 2: Registrar no Agent Registry**
```python
# app/domains/agent_studio/registry/agent_registry.py
REGISTERED_AGENTS = {
    # ... existentes ...
    "<nome>_agent": <Nome>CustomAgent,
}
```

**Passo 3: Review gate (P0-2 — evitar install sem review)**
```python
# CustomAgentRuntime.install() já tem gate:
# if not agent_manifest.reviewed_by_wedotalent_admin:
#     raise PermissionError("Agente não revisado pelo admin WeDOTalent")
# Não bypass esse gate
```

**Passo 4: Dry-run obrigatório antes de deploy**
```python
# CustomAgentRuntime.dry_run(agent_id, test_prompt, company_id)
# Executa sem side effects, valida que:
# - company_id é respeitado
# - FairnessGuard está funcionando
# - Todas as tools declaradas existem
```

---

## PATTERN-09: Fiação E2E de Nova Ação FE→BE

### Quando usar
Adicionar uma nova ação que o agente pode disparar no frontend (ex: abrir modal, navegar, aplicar filtro).

### Receita

**Passo 1: Declarar a ação no vocabulário**
```python
# app/shared/ui_action_sink.py
class UIActionType(str, Enum):
    # ... existentes ...
    NOVA_ACAO = "nova_acao"
    # Adição sem caso = RuntimeError em runtime (enum fail-high)
```

**Passo 2: Registrar a tool no catálogo**
```python
# docs/action-surface-registry/_REGISTRY.yaml
- name: nova_acao
  handler: app.shared.ui_action_sink._wrap_nova_acao
  fe_handler: "NovaAcaoHandler"
  description: "<descrição>"
  category: "NAVEGACAO"  # CANDIDATOS | VAGAS | NAVEGACAO | EMPRESA_CONFIG
```

**Passo 3: Implementar a tool BE**
```python
# app/shared/ui_action_sink.py (ou domain específico)
@tool_handler("ui_actions")
async def _wrap_nova_acao(**kwargs) -> dict:
    company_id = kwargs["company_id"]
    target_id = kwargs.get("target_id")
    
    # INVARIANTE: open_ui só abre/navega, NUNCA muta dados
    # Mutação deve ser tool separada com HITL se necessário
    
    return {
        "ui_action": "nova_acao",
        "target_id": target_id,
        "navigate_to": f"/pt/pagina/{target_id}",
    }
```

**Passo 4: Implementar o handler FE**
```typescript
// plataforma-lia/src/hooks/chat/useUIActionHandlers.ts
const handleUIAction = (frame: UIActionFrame) => {
  switch (frame.ui_action) {
    // ... existentes ...
    case "nova_acao":
      // Implementar ação
      if (frame.navigate_to) {
        router.push(frame.navigate_to);
      }
      break;
    default:
      assertNeverAction(frame.ui_action); // TypeScript compile error se não tratado
  }
};
```

**Passo 5: Wire no SSE consumer**
```typescript
// useChatSocket.ts
case "ui_action":
  handleUIAction(frame);
  break;
```

**Passo 6: Teste E2E obrigatório**
```python
# tests/e2e/test_nova_acao_e2e.py
async def test_nova_acao_reaches_frontend():
    """
    Verifica que a ação não morre no caminho
    (aprendizado: testes de peças passam, fio E2E pode ser ghost)
    """
    # 1. Mock do FE consumer
    # 2. Dispara conversa que deve triggerar nova_acao
    # 3. Assert que o frame ui_action chegou ao consumer
    # 4. Assert que o handler FE foi invocado
```

### Atenção: Teste de Peças ≠ Fio E2E
O erro clássico é testar cada componente em isolamento e não testar o fio completo. Uma ação pode passar em todos os testes unitários e ainda ser ghost porque o SSE consumer não drena corretamente ou o handler FE não está montado. SEMPRE adicionar um teste que simula o fluxo completo.

---

## PATTERN-10: Migrar Ghost Feature para Funcional

### Quando usar
Uma feature está declarada no código mas nunca é executada em produção (ghost). Exemplos históricos: `lia_field_toggles` (34 toggles sem consumer), `manager_approval_for_offer` (toggle sem gate), `eligibility_questions` (4 shapes divergentes).

### Receita

**Passo 1: Diagnosticar o ghost**
```bash
# Encontrar onde a feature é declarada
grep -r "<nome_da_feature>" app/ --include="*.py" | grep -v "test_" | grep -v "#"

# Encontrar onde deveria ser consumida
grep -r "<nome_da_feature>" app/ --include="*.py" | grep -v "test_" | grep "def \|class \|await \|return "

# Se declaração >> consumo → ghost confirmado
```

**Passo 2: Mapear o produtor canônico**
```bash
# Skill canonical-fix: identificar arquivo canonical (produtor)
# Princípio: fix no produtor, NUNCA no consumidor
# Se 5 telas mostram dado errado por 1 hook → fix no hook (1 lugar)
```

**Passo 3: Escolher a estratégia de consumer**
```
Ghost Toggle (sem gate):
  → Adicionar pre-flight: check_can_<acao>(company_id) que lê o toggle
  → Defense-in-depth: também checar no método de transição
  → Modelo: OfferService.check_can_send() + mark_sent()

Ghost Config de IA (sem injeção no prompt):
  → Adicionar ao DEFAULT_FIELD_TOGGLES em lia_field_toggles.py
  → Chamar build_company_agent_context() em todos os agentes relevantes
  → LiaFieldConfigService.get_filtered_context() injeta automaticamente

Ghost Dados (sem produtor unificado):
  → Criar produtor único (service/repository)
  → Migrar todos os consumidores para usar o produtor
  → Deletar implementações duplicadas
```

**Passo 4: TDD — Red→Green→Refactor**
```python
# RED: escrever teste que falha (prova que o ghost existe)
async def test_toggle_is_respected():
    """Falha porque o toggle é ignorado"""
    company = await create_company_with_toggle_off("nova_config")
    response = await client.post("/api/v1/fazer_algo", headers=company_auth)
    assert response.status_code == 403  # Falha: retorna 200 atualmente

# GREEN: implementar o consumer mínimo
# REFACTOR: limpar e garantir sensores
```

**Passo 5: Sensor anti-ghost**
```python
# Após migrar, adicionar ao check_capability_catalog_sync.py
# ou criar sensor específico:
# scripts/check_<nome>_has_consumer.py

# Regra: se campo X existe em DEFAULT_FIELD_TOGGLES, 
# deve existir referência a X em pelo menos 1 arquivo não-UI
```

**Passo 6: Documentar no FEATURE_CATALOG.md**
```markdown
## F-XX: Nome da Feature
**Status:** 🟢 Live (era 🔴 Ghost)
**Migrado em:** 2026-XX-XX
**Commit:** <hash>
**Consumer canônico:** `app/domains/.../services/...`
```

### Lição Histórica
A saga `lia_field_toggles` (2026-05-21): 34 toggles expostos em UI, recrutador customizava 34 dimensões acreditando influenciar a IA, mas os valores nunca eram lidos por nenhum agente. Fix: `LiaFieldConfigService` + `build_company_agent_context()` como produtor único. 16 campos migrados para funcional em uma sessão. **O padrão se repete** — sempre que você adicionar um toggle em Configurações, confirme o consumer antes de mergear.

---

*Documento gerado em 2026-06-17. Para contribuir com novos patterns, abrir issue no backlog com label `pattern-library`.*
