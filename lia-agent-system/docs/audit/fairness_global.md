# Fairness Global+Local — Análise de Gap e Proposta de Implementação

**Data**: 2026-04-12
**Versão**: 1.0
**Escopo**: Análise completa do estado atual do FairnessGuard, gaps identificados e proposta arquitetural de fairness global+local com persistência em banco de dados e integração com o sistema de observabilidade `lia_audit`

---

## 1. Estado Atual do Fairness

### 1.1 Arquitetura do FairnessGuard (`app/shared/compliance/fairness_guard.py`)

O `FairnessGuard` (1003 linhas) implementa três camadas de verificação de viés:

#### Camada 1 — Detecção Explícita (regex)

Constante `DISCRIMINATORY_CATEGORIES` com **19 categorias** totais (13 PT-BR + 6 EN) e aproximadamente **80 padrões** compilados via `_ensure_compiled()` no startup:

| Categoria | Exemplos de padrões |
|-----------|---------------------|
| `genero` | `\b(apenas|somente)\s+(\w+\s+)*(homens?|mulheres?)\b` |
| `raca_etnia` | `\borigem\s+(europeia|africana|asiatica)\b` |
| `idade` | `\baté\s+\d+\s+anos\b`, `\bfaixa\s+etária\b` |
| `religiao` | `\b(apenas|somente)\s+(cristãos?|muçulmanos?)\b` |
| `orientacao_sexual` | `\b(orientação|orientacao)\s+sexual\b` |
| `estado_civil` | `\bestado\s+civil\b` |
| `deficiencia` | `\bsem\s+deficiência\b`, `\bsem\s+limita[çc][õo]es\b` |
| `maternidade_paternidade` | `\bgravidez\b`, `\bsem\s+filhos\b` |
| `nacionalidade` | `\bexcluir?\s+(\w+\s+)*(estrangeiros?|imigrantes?)\b` |
| `antecedentes_criminais` | `\bsem\s+antecedentes?\s+criminais?\b` |
| `saude_doenca` | `\bsem\s+(HIV|AIDS|hepatite)\b` |
| `filiacao_sindical` | `\bsem\s+filia[çc][ãa]o\s+sindical\b` |
| `aparencia_fisica` | `\baltura\s+(mínima|máxima)\s*[:\s]*\d+` |
| `gender_en` (e demais `_en`) | `\b(only|just)\s+(men|women|male|female)\b` |

Todos os padrões são compilados com `re.IGNORECASE | re.UNICODE` e normalizados via `_normalize_text()` (remoção de acentos) para capturar variantes ortográficas sem acento.

#### Camada 2 — Detecção Implícita (léxico)

Dois dicionários com termos de viés implícito:

- `IMPLICIT_BIAS_TERMS` — **~30 termos** PT-BR: `"boa aparencia"`, `"energia jovem"`, `"escola particular"`, `"periferia"`, `"disponibilidade total"`, `"mae solo"`, etc.
- `IMPLICIT_BIAS_TERMS_EN` — **~30 termos** EN: `"culture fit"`, `"digital native"`, `"clean-cut"`, `"from a good family"`, `"available at all times"`, etc.

O método `check_implicit_bias()` compara o texto normalizado contra ambos os dicionários e retorna `soft_warnings` (avisos não-bloqueantes) em vez de bloquear.

#### Camada 3 — Detecção Semântica (LLM)

Método `check_with_layer3()` aciona LLM (claude-haiku, ~75% mais barato que Sonnet) apenas para ações de alto impacto definidas em `HIGH_IMPACT_ACTIONS`:

```python
HIGH_IMPACT_ACTIONS = {
    "rejection", "shortlist", "wsi_score", "policy_save", "bulk_rejection",
    "sourcing_search", "jd_import", "pipeline_move", "analytics_query",
    "job_create", "job_edit", "bulk_automation", "policy_check", "diversity_check",
}
```

Layer 3 possui feature flag `FAIRNESS_LAYER3_ENABLED` (default `False`) e cache Redis de 1h para evitar chamadas repetidas.

Adicionalmente, `check_with_sector()` usa `ALPHA1_SECTOR_RULES` para habilitar Layer 3 seletivamente por setor (tech, financeiro, saude, rpo habilitados; varejo, logistica desabilitados), com prompt contextualizado por setor.

#### Compilação e Versioning

Todos os padrões são compilados uma única vez via `_ensure_compiled()` no startup e armazenados em `_COMPILED_PATTERNS` (dict global). A constante `_PATTERNS_VERSION = 5` rastreia versão dos padrões; qualquer adição de regras exige incremento manual e redeploy.

### 1.2 Pontos de Aplicação

#### MainOrchestrator (centralizado)

`MainOrchestrator` (`app/orchestrator/main_orchestrator.py`) aplica FairnessGuard como primeiro passo do pipeline para todas as mensagens recebidas via REST (chat.py). O resultado (`fairness_warnings`) é retornado na `ChatResponse`. Este é o ponto de cobertura mais abrangente.

#### EnhancedAgentMixin (manual, por agente)

`EnhancedAgentMixin._fairness_pre_check()` (`libs/agents-core/lia_agents_core/enhanced_agent_mixin.py:273-324`) verifica Camadas 1 e 2 antes do loop ReAct. É um método opt-in: o agente precisa chamá-lo explicitamente em seu pipeline de entrada.

Dos 14 agentes com `EnhancedAgentMixin`, apenas **4 chamam `_fairness_pre_check`**:

| Agente | Arquivo |
|--------|---------|
| `WizardReActAgent` | `app/domains/job_management/agents/wizard_react_agent.py` |
| `TalentReActAgent` | `app/domains/recruiter_assistant/agents/talent_react_agent.py` |
| `KanbanReActAgent` | `app/domains/recruiter_assistant/agents/kanban_react_agent.py` |
| `JobsManagementReActAgent` | `app/domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py` |

Os demais **10 agentes** com `EnhancedAgentMixin` não chamam `_fairness_pre_check` e dependem exclusivamente da cobertura centralizada do `MainOrchestrator`.

### 1.3 Persistência no Banco de Dados

`FairnessAuditLog` (`libs/models/lia_models/fairness_audit.py`) persiste bloqueios e warnings no PostgreSQL via tabela `fairness_audit_log`:

```python
class FairnessAuditLog(Base):
    __tablename__ = "fairness_audit_log"
    id = Column(UUID, primary_key=True)
    company_id = Column(UUID, nullable=True, index=True)
    recruiter_id = Column(UUID, nullable=True)
    job_id = Column(UUID, nullable=True)
    candidate_id = Column(UUID, nullable=True)
    query_hash = Column(String(64))        # SHA-256, sem PII
    category = Column(String(50), index=True)
    blocked_terms = Column(JSONB)
    confidence = Column(Float)
    is_blocked = Column(Boolean, index=True)
    context = Column(String(100))
    soft_warnings = Column(JSONB)
    created_at = Column(DateTime(timezone=True), index=True)
```

O método `log_check()` é chamado após cada verificação que gerou bloqueio ou warning. **Campos ausentes**: `execution_id` e `session_id`, impedindo correlação com `ExecutionAuditRecord`.

### 1.4 Ausência nos Módulos de Observabilidade

`AuditCallback` (`libs/audit/lia_audit/audit_callback.py`) e `ExecutionAuditRecord` (`libs/audit/lia_audit/audit_models.py`) não possuem nenhum campo relacionado a fairness. Os entries da timeline (`llm_call`, `tool_call`, `node_transition`) não incluem um step `fairness_check`. A timeline de auditoria (`app/api/v1/audit_timeline.py`) não expõe nenhum dado de fairness, e o `GET /api/v1/audit/executions/{id}/timeline` não mostra se um bloqueio de fairness ocorreu durante a execução.

API de reports de fairness já existe em `app/api/v1/fairness_reports.py` (summary, trend, audit/logs, export), mas é um sistema separado e desconectado da timeline de execuções.

---

## 2. Gaps Identificados

### Gap 1 — Aplicação Fragmentada e Dependente de Chamada Manual

O ponto de cobertura mais robusto é o `MainOrchestrator`, que cobre o fluxo REST. Porém, os seguintes caminhos ficam sem verificação garantida ou duplicam verificação sem coordenação:

- **APIs internas** que chamam diretamente domínios sem passar pelo `MainOrchestrator`
- **Jobs Celery** (bulk operations, automations) que processam textos de JD ou mensagens sem passar pelo pipeline central
- **Webhooks** que recebem payloads de sistemas externos (ATS integration, sourcing providers)
- **10 agentes** com `EnhancedAgentMixin` que não chamam `_fairness_pre_check` — se o `MainOrchestrator` falhar ou for bypassado, ficam sem cobertura

A checagem no `MainOrchestrator` acontece no nível da mensagem do usuário, mas não no nível de parâmetros internos que um agente pode receber via tool calls (por exemplo, critérios de filtro passados como argumentos estruturados JSON a uma tool).

### Gap 2 — Regras Estáticas sem Contexto de Domínio

Todas as regras são globais e aplicadas uniformemente a todos os agentes e domínios. Isso gera dois problemas concretos:

**Falsos positivos por ausência de contexto**:

- O domínio `analytics` frequentemente recebe consultas legítimas com termos demográficos para relatórios de diversidade: *"mostre distribuição por faixa etária dos contratados"* — bloqueado pelo padrão `\bfaixa\s+etária\b` mesmo sendo uma análise interna de diversidade
- O domínio `communication` (employer branding) pode usar "energia jovem" em cópia de marketing para descrever cultura organizacional, não como filtro de candidatos
- O domínio `sourcing` pode precisar de critérios de localização geográfica que disparam `periferia` ou `zona rural` em contexto legítimo de análise de mercado de trabalho

**Ausência de regras mais rígidas onde necessário**:

- O domínio `screening` (avaliação de candidatos) deveria ter regras adicionais sobre peso de critérios subjetivos
- O domínio `job_management` (criação de vagas) deveria ter verificação automática integrada no save de JD, não apenas no chat

### Gap 3 — Alteração Requer Deploy

A alteração de qualquer regra — adicionar uma categoria, ajustar um padrão regex, modificar uma mensagem educacional, adicionar um termo implícito — exige:

1. Editar `fairness_guard.py` (código Python)
2. Incrementar `_PATTERNS_VERSION`
3. Executar pipeline CI/CD completo
4. Deploy do backend

Não há interface de administração para gerenciar regras em runtime. Não há como ativar uma regra apenas para certos tenants ou desativá-la temporariamente para investigação sem deploy.

### Gap 4 — Desconexão com Observabilidade

O sistema de observabilidade (`lia_audit`) e o sistema de fairness (`fairness_audit_log`) são completamente desconectados:

- `ExecutionAuditRecord` não tem campo `fairness_result`
- `FairnessAuditLog` não tem `execution_id` nem `session_id`
- A timeline de auditoria (`GET /api/v1/audit/executions/{id}/timeline`) não mostra bloqueios
- Quando um bloqueio de fairness ocorre, não é possível reconstruir o contexto completo da execução (quais tools foram chamadas, qual domínio, qual foi o resultado final) olhando para um único registro

---

## 3. Proposta: Regras Globais vs. Locais (por Domínio)

### 3.1 Modelo de Escopo

Introduzir o conceito de **escopo** de regra com dois valores:

| Escopo | Descrição |
|--------|-----------|
| `global` | Aplicada a todos os agentes e domínios sem exceção. Editável apenas por super-admin do sistema. |
| `domain` | Associada a um domínio específico. Pode ser mais restritiva (override) ou uma isenção (allowlist) com justificativa auditável. |

### 3.2 Exemplos Concretos de Regras por Domínio

#### Domínio `analytics` — Isenção com Contexto

```yaml
scope: domain
domain: analytics
type: allowlist
pattern: "faixa etária"
justification: >
  No domínio analytics, a consulta de distribuição por faixa etária é legítima
  para relatórios de diversidade e análise de workforce. A isenção aplica-se
  apenas a queries que não usem o critério como filtro eliminatório de candidatos.
approved_by: compliance_team
valid_until: 2026-12-31
```

#### Domínio `communication` — Isenção com Contexto

```yaml
scope: domain
domain: communication
type: allowlist
pattern: "energia jovem"
justification: >
  Em employer branding, "energia jovem" descreve cultura organizacional, não
  filtra candidatos por idade. A isenção aplica-se apenas a conteúdo de branding,
  não a filtros de busca ou critérios de seleção.
approved_by: compliance_team
```

#### Domínio `screening` — Regra mais Restritiva

```yaml
scope: domain
domain: screening
type: override
additional_category: "subjective_appearance_screening"
action: block
message: >
  No contexto de avaliação de candidatos, qualquer referência a critérios de
  aparência é vedada pela Lei 9.029/95 e pela política WeDO de zero-bias.
  Use exclusivamente critérios baseados em competências mensuráveis.
```

#### Domínio `job_management` — Verificação Automática no Save

```yaml
scope: domain
domain: job_management
type: trigger
trigger_event: job_description_save
check_layers: [1, 2, 3]  # all layers including LLM semantic
action: warn_and_require_confirmation
message: >
  Esta descrição de vaga contém termos que podem configurar discriminação.
  Revise antes de publicar. Itens detectados: {blocked_terms}
```

### 3.3 Política de Merge

A aplicação de regras segue a hierarquia:

```
Regras Globais (baseline)
    +
Regras de Domínio tipo override (mais restritivas)
    -
Regras de Domínio tipo allowlist (isenções com justificativa)
    =
Conjunto efetivo de regras para o domínio
```

**Invariantes**:
- Regras `global` nunca podem ser desativadas por regras de domínio
- Isenções (`allowlist`) exigem `justification` não-nula e `approved_by` auditável
- Toda alteração de regra é registrada no `AuditService` existente (`app/shared/compliance/audit_service.py`)

### 3.4 Mapeamento de Domínios LIA

| Domínio | Política Sugerida |
|---------|-------------------|
| `sourcing` | Global + isenção para análise geográfica de mercado de trabalho |
| `screening` | Global + override mais restritivo para aparência e subjetividade |
| `analytics` | Global + isenção para métricas de diversidade |
| `communication` | Global + isenção para employer branding com termos de cultura |
| `job_management` | Global + verificação automática Layer 1+2+3 no save de JD |
| `kanban` | Global (sem customização — fluxo operacional) |
| `talent_intelligence` | Global + isenção para análise comparativa de diversidade de talent pool |

---

## 4. Proposta: Persistência em Banco com Cache

### 4.1 Tabela `fairness_rules`

```sql
CREATE TABLE fairness_rules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category        VARCHAR(100) NOT NULL,
    pattern         TEXT NOT NULL,          -- regex (Layer 1) ou termo literal (Layer 2)
    type            VARCHAR(20) NOT NULL,   -- 'explicit' | 'implicit'
    scope           VARCHAR(20) NOT NULL,   -- 'global' | 'domain'
    domain          VARCHAR(100) NULL,      -- NULL quando scope='global'
    action          VARCHAR(20) NOT NULL,   -- 'block' | 'warn' | 'allowlist'
    educational_message TEXT NULL,
    justification   TEXT NULL,             -- obrigatório para action='allowlist'
    language        VARCHAR(10) NOT NULL DEFAULT 'pt-br',  -- 'pt-br' | 'en'
    version         INTEGER NOT NULL DEFAULT 1,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_by      VARCHAR(255) NOT NULL,
    updated_by      VARCHAR(255) NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NULL,
    company_id      UUID NULL,             -- NULL = regra do sistema; UUID = regra do tenant

    CONSTRAINT fk_domain_required
        CHECK (scope = 'global' OR domain IS NOT NULL),
    CONSTRAINT fk_justification_allowlist
        CHECK (action != 'allowlist' OR justification IS NOT NULL)
);

CREATE INDEX idx_fairness_rules_scope ON fairness_rules (scope, domain);
CREATE INDEX idx_fairness_rules_category ON fairness_rules (category);
CREATE INDEX idx_fairness_rules_active ON fairness_rules (is_active, scope);
CREATE INDEX idx_fairness_rules_company ON fairness_rules (company_id);
CREATE INDEX idx_fairness_rules_action ON fairness_rules (action, scope);
```

### 4.2 Cache em Memória com TTL

```python
@dataclass
class FairnessRulesCache:
    rules: dict[str, list[CompiledRule]]  # keyed by category
    allowlist: dict[str, list[str]]       # domain → padrões isentos
    overrides: dict[str, list[CompiledRule]]  # domain → regras adicionais
    version: int
    loaded_at: datetime
    ttl_seconds: int = 300  # 5 minutos (configurável)

    @property
    def is_stale(self) -> bool:
        age = (datetime.now(timezone.utc) - self.loaded_at).total_seconds()
        return age > self.ttl_seconds
```

Invalidação: evento via Redis pub/sub (`fairness_rules:invalidate`) quando qualquer regra for alterada via CRUD. O warm-up no startup carrega todas as regras ativas e compila os padrões regex.

### 4.3 Validação Rigorosa no CRUD

Antes de persistir qualquer regra com `type='explicit'` (regex):

1. Compilar o padrão em sandbox: `re.compile(pattern, re.IGNORECASE | re.UNICODE)`
2. Executar contra strings de teste de baixo risco para detectar ReDoS: timeout de 100ms
3. Rejeitar padrões com backtracking excessivo ou estrutura de catastrophic backtracking
4. Rejeitar padrões que correspondam a zero strings (lookaheads inválidos)

```python
async def validate_regex_pattern(pattern: str) -> tuple[bool, str]:
    """
    Retorna (is_valid, error_message).
    Testa compilação, execução e ReDoS antes de persistir.
    """
    try:
        compiled = re.compile(pattern, re.IGNORECASE | re.UNICODE)
    except re.error as e:
        return False, f"Padrão regex inválido: {e}"

    test_strings = ["a" * 50, "x" * 100, "test string for timing"]
    for s in test_strings:
        start = time.monotonic()
        compiled.search(s)
        elapsed_ms = (time.monotonic() - start) * 1000
        if elapsed_ms > 100:
            return False, f"Padrão potencialmente ReDoS: {elapsed_ms:.0f}ms em string de teste"

    return True, ""
```

### 4.4 Seed Migration

Migração inicial para popular `fairness_rules` com todas as regras existentes:

- Todas as entradas de `DISCRIMINATORY_CATEGORIES` → `scope='global'`, `type='explicit'`, `action='block'`
- Todas as entradas de `IMPLICIT_BIAS_TERMS` → `scope='global'`, `type='implicit'`, `action='warn'`
- Todas as entradas de `IMPLICIT_BIAS_TERMS_EN` → `scope='global'`, `type='implicit'`, `action='warn'`, `language='en'`
- Migração deve ser idempotente (verificar existência antes de inserir)

---

## 5. Proposta: CRUD com Controle de Acesso

### 5.1 Endpoints REST

```
POST   /api/v1/admin/fairness/rules
  → Criar nova regra (global ou de domínio)
  → Roles: super-admin (global) | company-admin (domain, apenas seu company_id)

GET    /api/v1/admin/fairness/rules?scope=&domain=&category=&active=
  → Listar regras com filtros

GET    /api/v1/admin/fairness/rules/{rule_id}
  → Detalhe de uma regra

PUT    /api/v1/admin/fairness/rules/{rule_id}
  → Atualizar regra (incrementa version, registra updated_by)

DELETE /api/v1/admin/fairness/rules/{rule_id}
  → Soft delete (is_active=False, nunca hard delete)

POST   /api/v1/admin/fairness/rules/validate
  → Validar padrão regex sem persistir (dry-run)

POST   /api/v1/admin/fairness/rules/reload
  → Forçar invalidação do cache e reload (super-admin)
```

### 5.2 Controle de Acesso

| Operação | Role necessária | Restrição adicional |
|----------|-----------------|---------------------|
| CRUD de regras `scope='global'` | `super-admin` do sistema | Apenas regras sem `company_id` |
| CRUD de regras `scope='domain'` globais | `super-admin` do sistema | — |
| CRUD de regras `scope='domain'` do tenant | `company-admin` com permissão `fairness:manage` | Apenas regras com seu `company_id` |
| Leitura de regras | `company-admin` | Apenas regras globais + regras do seu `company_id` |
| Invalidação de cache | `super-admin` | — |

### 5.3 Audit de Alterações

Toda operação de escrita em `fairness_rules` gera um registro no `AuditService` existente (`app/shared/compliance/audit_service.py`) com:

```json
{
  "action": "fairness_rule_created|updated|deactivated",
  "actor": "user_id",
  "target": "rule_id",
  "before": { "pattern": "...", "action": "block", "is_active": true },
  "after": { "pattern": "...", "action": "warn", "is_active": true },
  "company_id": "...",
  "timestamp": "2026-04-12T..."
}
```

---

## 6. Proposta: Integração com Observabilidade

### 6.1 Adicionar `fairness_result` no `AuditCallback`

Estender `AuditCallback` (`libs/audit/lia_audit/audit_callback.py`) com um método para registrar o resultado de fairness como um entry na timeline:

```python
def on_fairness_check(
    self,
    result: FairnessCheckResult,
    domain: str,
    latency_ms: float = 0.0,
) -> None:
    """Registra resultado de FairnessGuard como step da timeline."""
    self.entries.append({
        "type": "fairness_check",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "domain": domain,
        "is_blocked": result.is_blocked,
        "category": result.category,
        "blocked_terms": result.blocked_terms or [],
        "soft_warnings_count": len(result.soft_warnings or []),
        "confidence": result.confidence,
        "latency_ms": latency_ms,
    })
```

Na timeline (`app/api/v1/audit_timeline.py`), o `TimelineStep` seria estendido para incluir `fairness_check` como tipo, exibindo:
- `step N: FairnessGuard → blocked (category=genero)` ou
- `step N: FairnessGuard → passed (0 warnings)` ou
- `step N: FairnessGuard → warned (3 soft warnings)`

### 6.2 Adicionar `execution_id` e `session_id` ao `FairnessAuditLog`

Alterar o modelo `FairnessAuditLog` (`libs/models/lia_models/fairness_audit.py`) para incluir os campos de correlação:

```python
# Correlação com ExecutionAuditRecord
execution_id = Column(String(36), nullable=True, index=True)  # UUID da execução
session_id = Column(String(255), nullable=True, index=True)    # session da conversa
```

Com esses campos, a query de correlação fica possível:

```sql
SELECT f.*, a.domain, a.agent_type, a.total_duration_ms
FROM fairness_audit_log f
JOIN audit_execution_metadata a ON f.execution_id = a.execution_id
WHERE f.is_blocked = true
  AND f.created_at > NOW() - INTERVAL '7 days'
ORDER BY f.created_at DESC;
```

### 6.3 Centralizar Checagem no `LangGraphReActBase`

Atualmente, `_fairness_pre_check` é chamado manualmente por cada agente. A proposta é centralizar no `LangGraphReActBase._process_langgraph()` (`libs/agents-core/lia_agents_core/`), seguindo o mesmo padrão já adotado para `_sanitize_messages_pii`:

```python
class LangGraphReActBase:
    _enable_fairness_check: bool = True  # override para False em agentes especializados

    async def _process_langgraph(self, user_input: str, ...) -> str:
        # Já existente: PII sanitization
        user_input = self._sanitize_messages_pii(user_input)

        # Novo: FairnessGuard centralizado
        if self._enable_fairness_check:
            t0 = time.monotonic()
            fairness_result = await self._run_fairness_check(user_input)
            latency = (time.monotonic() - t0) * 1000
            if self._audit_callback:
                self._audit_callback.on_fairness_check(fairness_result, self.domain, latency)
            if fairness_result.is_blocked:
                return fairness_result.educational_message
        ...
```

Isso garante cobertura automática para todos os agentes que herdam de `LangGraphReActBase`, sem que cada um precise chamar `_fairness_pre_check` individualmente. Os 4 agentes que já chamam `_fairness_pre_check` podem ter suas chamadas removidas ou mantidas como override explícito.

### 6.4 Expor Dados de Fairness na Timeline

Estender o endpoint `GET /api/v1/audit/executions/{id}/timeline` para incluir steps de `fairness_check`:

```python
class TimelineStep(BaseModel):
    step: int
    type: str  # "llm_call" | "tool_call" | "node_transition" | "fairness_check"  # novo
    timestamp: str
    # campos existentes ...

    # Novos campos para fairness_check
    is_blocked: bool | None = None
    fairness_category: str | None = None
    fairness_warnings_count: int | None = None
    fairness_confidence: float | None = None
```

---

## 7. Riscos e Considerações

### 7.1 Performance

- **Compilação de regras dinâmicas**: regras carregadas do banco precisam de cache eficiente com warm-up no startup. A compilação de 80+ regexes leva ~5-10ms — aceitável para warm-up, inaceitável para cada request
- **TTL do cache**: 5 minutos é razoável para produção; em desenvolvimento, considerar TTL menor ou invalidação imediata
- **Overhead de banco**: a query de load de regras deve usar índice em `(is_active, scope)` e ter resultado cacheado — nunca atingir o banco por request

### 7.2 Segurança

- **Validação contra ReDoS**: obrigatória antes de qualquer persistência de padrão regex
- **Padrões inválidos**: devem ser rejeitados no CRUD com erro 422 e mensagem clara
- **Injeção via allowlist**: uma allowlist mal configurada pode criar brechas. Toda isenção deve ser revisada por compliance antes de ativação
- **Tenant isolation**: `company_id` deve ser validado via JWT, seguindo o padrão `_enforce_tenant()` existente em `app/shared/tenant_guard.py`

### 7.3 Granularidade de Isenções

- Isenções de domínio não devem criar brecha para contornar fairness global
- A invariante é: `allowlist` apenas remove a regra do contexto do domínio específico, mas a regra global continua ativa em todos os outros domínios
- Toda isenção deve ter `justification` explícita, `approved_by` e, idealmente, `valid_until` para revisão periódica

### 7.4 Compatibilidade Durante Transição

- `FairnessGuard` deve continuar funcional durante a transição — nunca degradar proteção existente
- Durante a migração, o sistema pode operar em modo híbrido: regras hardcoded do `fairness_guard.py` como fallback, regras do banco como override
- A seed migration deve ser executada antes de qualquer mudança no código que remova as constantes hardcoded

### 7.5 Multi-tenant

- Regras globais do sistema (`company_id IS NULL`) são lidas por todos os tenants
- Regras customizadas do tenant (`company_id = X`) são aplicadas apenas ao tenant X, em adição às globais
- A precedência é: global + tenant-override + domain-tenant. Um tenant não pode desativar regras globais do sistema

---

## 8. Tabela de Viabilidade

| Aspecto | Viabilidade | Infraestrutura Existente | Esforço Estimado |
|---------|-------------|--------------------------|------------------|
| Persistência de regras em banco | Alta | PostgreSQL com SQLAlchemy; padrão de models em `lia_models` | 1 migration + 1 model |
| Cache em memória com TTL | Alta | Redis já configurado (usado em CascadedRouter); padrão LRU existente | ~150 linhas |
| CRUD com controle de acesso | Média | `_enforce_tenant()` + `AuditService` existentes; padrão REST em `app/api/v1/` | 3-4 endpoints + roles |
| Seed migration das regras existentes | Alta | Migration Alembic existente; regras já em Python dict | 1 migration (~80 entradas) |
| `execution_id`+`session_id` em `FairnessAuditLog` | Alta | Campos UUID; migration simples; `execution_id` disponível em `AuditCallback` | 1 migration + 2 campos |
| `on_fairness_check` em `AuditCallback` | Alta | Padrão `on_tool_call`/`on_llm_call` já implementado; basta adicionar novo tipo | ~30 linhas |
| Centralizar em `LangGraphReActBase` | Média | `_sanitize_messages_pii` já é o padrão; requer teste de regressão nos 4 agentes que já chamam `_fairness_pre_check` | ~50 linhas + testes |
| Fairness na timeline de auditoria | Média | Timeline já consome `entries[]`; basta adicionar tipo `fairness_check` | ~40 linhas frontend + backend |
| Regras por domínio (scope local) | Média | Sem infraestrutura — requer lógica de merge e lookup por domínio | ~200 linhas |
| CRUD de allowlist com aprovação | Baixa-Média | Sem workflow de aprovação; requer estado `pending_approval` | Sprint dedicado |
| Validação anti-ReDoS no CRUD | Média | Sem utilitário existente; requer sandbox de regex com timeout | ~60 linhas |

**Esforço total estimado** (sem allowlist workflow): ~4-6 dias de engineering, distribuídos em 2 sprints.

---

## 9. Arquivos Referenciados

| Arquivo | Papel na Análise |
|---------|-----------------|
| `app/shared/compliance/fairness_guard.py` | Implementação central do FairnessGuard (1003 linhas) — 3 camadas, `DISCRIMINATORY_CATEGORIES`, `IMPLICIT_BIAS_TERMS`, `log_check()` |
| `libs/agents-core/lia_agents_core/enhanced_agent_mixin.py:273-324` | `_fairness_pre_check()` — chamada manual opt-in; apenas 4 dos 14 agentes a usam |
| `libs/models/lia_models/fairness_audit.py` | `FairnessAuditLog` — persistência de bloqueios; sem `execution_id` nem `session_id` |
| `libs/audit/lia_audit/audit_callback.py` | `AuditCallback` — sem qualquer campo de fairness; `entries[]` a ser estendido |
| `libs/audit/lia_audit/audit_models.py` | `ExecutionAuditRecord` — modelo a ser seguido para correlação |
| `libs/audit/lia_audit/audit_writer.py` | `AuditWriter` com `get_audit_writer()` singleton — padrão de persistência dual (PG + Storage) |
| `app/api/v1/audit_timeline.py` | Timeline de auditoria — padrão de endpoint e `TimelineStep` a ser estendido |
| `app/api/v1/fairness_reports.py` | Reports de fairness já existentes (summary, trend, audit/logs) — sistema isolado |
| `app/orchestrator/main_orchestrator.py` | Ponto de aplicação centralizado do FairnessGuard para fluxo REST |
| `app/domains/job_management/agents/wizard_react_agent.py` | Um dos 4 agentes que chamam `_fairness_pre_check` |
| `app/domains/recruiter_assistant/agents/talent_react_agent.py` | Um dos 4 agentes que chamam `_fairness_pre_check` |
| `app/domains/recruiter_assistant/agents/kanban_react_agent.py` | Um dos 4 agentes que chamam `_fairness_pre_check` |
| `app/domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py` | Um dos 4 agentes que chamam `_fairness_pre_check` |
| `app/shared/compliance/audit_service.py` | `AuditService` para audit trail de alterações em regras |
| `app/shared/tenant_guard.py` | `_enforce_tenant()` — padrão de tenant isolation a ser reaproveitado no CRUD |

---

**Autor**: LIA Agent System Audit
**Data**: 2026-04-12
**Próximo passo**: Implementar `execution_id`/`session_id` em `FairnessAuditLog` e `on_fairness_check()` em `AuditCallback` (menor esforço, maior impacto imediato na correlação de dados)
