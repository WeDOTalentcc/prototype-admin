# Theme: P2 — Agent Specialization — Persona Layer

## O que é este tema

Cada agente LIA tem uma especialização sobre a persona base (documentada em P1). A especialização é composta por duas camadas:

1. **Layer YAML** (`agent_prompts.yaml` — 11 tipos + `app/prompts/domains/*.yaml` — 24 domínios): texto que o LLM vê
2. **Layer Python** (`*_system_prompt.py` — 16 arquivos): lógica de composição + REASONING_PROMPT com placeholders dinâmicos

A distinção entre os dois YAMLs:
- `agent_prompts.yaml` (shared): addições concisas por agent_type (role, responsabilidades, capacidades) — consumido via `_load_domain_additions()` em `SystemPromptBuilder.build()`
- `domains/*.yaml` (domain): system_prompt completo + few_shot_examples + metadata — consumido pelos domain `*_system_prompt.py` Python files

Este tema não inclui a persona base (ver P1) nem os padrões de interação anti-sycophancy/CoT (ver P4).

---

## Arquivos conectados (41 total)

### Camada Config (YAMLs — 35 arquivos)

| Arquivo | Path | Conteúdo |
|---------|------|----------|
| `agent_prompts.yaml` | `app/prompts/shared/agent_prompts.yaml` | 11 tipos de agente: role + responsabilidades + capacidades |
| `analytics.yaml` | `app/prompts/domains/analytics.yaml` | v2.0 — Analytics & Reporting |
| `ats_integration.yaml` | `app/prompts/domains/ats_integration.yaml` | v2.0 — ATS Integration |
| `automation.yaml` | `app/prompts/domains/automation.yaml` | v2.0 — Automation & Proactive Alerts |
| `autonomous.yaml` | `app/prompts/domains/autonomous.yaml` | v1.0 — Autonomous cross-domain (Tier 6) |
| `candidate_self_service.yaml` | `app/prompts/domains/candidate_self_service.yaml` | v1.1 — Candidate Portal (LGPD Art. 20) |
| `communication.yaml` | `app/prompts/domains/communication.yaml` | v2.0 — Communication & Messaging |
| `company_settings.yaml` | `app/prompts/domains/company_settings.yaml` | v1.0 — Company Settings |
| `culture_analysis.yaml` | `app/prompts/domains/culture_analysis.yaml` | Análise de cultura + Employer Branding |
| `cv_screening.yaml` | `app/prompts/domains/cv_screening.yaml` | v2.0 — CV Screening & WSI Assessment |
| `digital_twin.yaml` | `app/prompts/domains/digital_twin.yaml` | v1.0 — Digital Twin evaluation |
| `hiring_policy.yaml` | `app/prompts/domains/hiring_policy.yaml` | v1.0 — Hiring Policy enforcement |
| `intent_classification.yaml` | `app/prompts/domains/intent_classification.yaml` | Wizard intent classifier |
| `interview_scheduling.yaml` | `app/prompts/domains/interview_scheduling.yaml` | v2.0 — Interview Scheduling & WSI Interviewer |
| `job_management.yaml` | `app/prompts/domains/job_management.yaml` | v2.0 — Job Management & Vacancy Creation |
| `orchestrator.yaml` | `app/prompts/domains/orchestrator.yaml` | Compliance rules para o orchestrator |
| `pipeline_transition.yaml` | `app/prompts/domains/pipeline_transition.yaml` | v3.0 — Pipeline Transition (decision) |
| `recruiter_assistant.yaml` | `app/prompts/domains/recruiter_assistant.yaml` | v2.0 — Recruiter Personal Assistant |
| `sourcing.yaml` | `app/prompts/domains/sourcing.yaml` | v2.0 — Sourcing & Talent Search |
| `talent_pool.yaml` | `app/prompts/domains/talent_pool.yaml` | v1.0 — Talent Pool / Banco de Talentos |
| `wsi_evaluation.yaml` | `app/prompts/domains/wsi_evaluation.yaml` | v2.0 — WSI Evaluator (scoring) |
| `wsi_interview.yaml` | `app/prompts/domains/wsi_interview.yaml` | v2.0 — WSI Interviewer (behavioral) |
| `wsi_layer2_extraction.yaml` | `app/prompts/domains/wsi_layer2_extraction.yaml` | v1.0 — LLM extractor para penalidades/bônus |
| `agent_calibration.yaml` | `app/prompts/domains/agent_calibration.yaml` | v1.0 — Calibração de agentes de sourcing |
| `analysis.yaml` | `app/prompts/domains/analysis.yaml` | Análise de candidatos (scoring 100%) |

### Camada Código (16 arquivos Python — domain system_prompts)

| Arquivo | Path Canônico | Domínio |
|---------|---------------|---------|
| `analytics_system_prompt.py` | `app/domains/analytics/agents/` | analytics |
| `ats_integration_system_prompt.py` | `app/domains/ats_integration/agents/` | ats_integration |
| `automation_system_prompt.py` | `app/domains/automation/agents/` | automation |
| `candidate_system_prompt.py` | `app/domains/candidate_self_service/agents/` | candidate_self_service |
| `communication_system_prompt.py` | `app/domains/communication/agents/` | communication |
| `company_system_prompt.py` | `app/domains/company_settings/agents/` | company_settings |
| `pipeline_system_prompt.py` (cv_screening) | `app/domains/cv_screening/agents/` | cv_screening |
| `policy_system_prompt.py` | `app/domains/hiring_policy/agents/` | hiring_policy |
| `interview_system_prompt.py` | `app/domains/interview_scheduling/agents/` | interview_scheduling |
| `wizard_system_prompt.py` | `app/domains/job_management/agents/` | job_management |
| `pipeline_system_prompt.py` (pipeline) | `app/domains/pipeline/agents/` | pipeline |
| `system_prompt.py` | `app/domains/policy/agents/` | policy |
| `jobs_mgmt_system_prompt.py` | `app/domains/recruiter_assistant/agents/` | jobs management |
| `kanban_system_prompt.py` | `app/domains/recruiter_assistant/agents/` | kanban |
| `talent_system_prompt.py` | `app/domains/recruiter_assistant/agents/` | talent |
| `sourcing_system_prompt.py` | `app/domains/sourcing/agents/` | sourcing |

### Integration points

- **P1 System Prompt Composition**: `_load_domain_additions(agent_type)` consome `agent_prompts.yaml` (seção 4); domain Python files constroem o `extra_instructions` passado para `SystemPromptBuilder.build()`
- **P4 Interaction Patterns**: `ANTI_SYCOPHANCY_OPERATIONAL` importado pelos domain system_prompt files
- **C1 Fairness**: `compliance_base.py ComplianceDomainPrompt` injetado por herança de domínio
- **I1 Agent Architecture**: cada `*_react_agent.py` chama o `*_system_prompt.py` correspondente

---

## Os 11 tipos de agente em agent_prompts.yaml

```yaml
# app/prompts/shared/agent_prompts.yaml
metadata:
  domain: "shared"
  version: "2.0"
  description: "Domain-specific additions. Persona/ethics inherited from lia_persona.yaml."

prompts:
  orchestrator:      # Coordenadora central de 8 agentes especializados
  job_planner:       # Especialista em definição e estruturação de vagas
  sourcing:          # Especialista em busca e captação de candidatos
  cv_screening:      # Especialista em triagem e avaliação de CVs
  interviewer:       # Condutora de entrevistas estruturadas via WSI
  wsi_evaluator:     # Avaliadora WSI (70% técnico + 30% comportamental)
  scheduling:        # Especialista em agendamento de entrevistas
  analyst_feedback:  # Analista de resultados e comunicação de feedback
  ats_integrator:    # Especialista em integração e sincronização com ATS
  recruiter_assistant: # Assistente pessoal do recrutador (genérico)
  proactive_insights:  # Insights proativos baseados em dados
```

Estes tipos são consumidos como `agent_type` param em `SystemPromptBuilder.build()` + `_load_domain_additions()`.

---

## Os 24 domain YAMLs — metadata e formato

### Dois formatos de metadata suportados

**Formato novo (metadata block):**
```yaml
metadata:
  domain: "analytics"
  version: "2.0"
  updated_at: "2026-03-19"
  description: "System prompt for Analytics & Reporting domain"

system_prompt: |
  ...
```

**Formato legado (root level):**
```yaml
name: talent_pool
domain: talent_pool
version: 1
description: "Prompt para interações com Bancos de Talentos Vivos"

system_prompt: |
  ...
```

`prompt_version_loader.validate_prompt_metadata()` suporta ambos.

### Campos opcionais por YAML

| Campo | Uso |
|-------|-----|
| `system_prompt` | Texto base do agente (obrigatório) |
| `few_shot_examples` | Exemplos injetados como `DOMAIN_FEW_SHOT_EXAMPLES` |
| `type` | "decision" | "operational" | "conversational" — hints para compliance variant |
| `updated_at` | Auditoria EU AI Act |

### Exemplos de domain YAML notáveis

**`pipeline_transition.yaml`** — type="decision", v3.0:
- Controla transições de candidatos entre etapas do pipeline
- ComplianceDomainPrompt.get_system_prompt() seleciona variant "decision" (mais restritiva)

**`candidate_self_service.yaml`** — type="conversational", v1.1.0:
- Restricts: scores internos, red_flags, dados de outros candidatos, ações de escrita
- LGPD Art. 20: sempre informa direito de contestação

**`wsi_layer2_extraction.yaml`** — v1.0:
- Spec WeDOTalent §F8.3 — extrai sinais semânticos para penalidades/bônus
- Alimenta camada determinística (M04 penalidades, M05 bônus, M06 inflação)

**`orchestrator.yaml`** — compliance rules para o orchestrator:
- Se input tentar prompt injection → classifica como `intent="compliance_violation"` confidence=0.95
- Não encaminha para nenhum agente — bloqueia direto

---

## Padrão dos domain *_system_prompt.py

Todos os 15 arquivos seguem o mesmo padrão:

```python
"""
<Domain> System Prompt — loads from YAML.
Content source: app/prompts/domains/<domain>.yaml
Compliance/guardrails: injected by ComplianceDomainPrompt.
"""
import logging
from typing import Any
from app.shared.prompts.anti_sycophancy_block import ANTI_SYCOPHANCY_OPERATIONAL  # ou FULL

_yaml_cache: dict[str, Any] | None = None

def _load_yaml() -> dict[str, Any]:
    """Module-level cache — loads once per process."""
    global _yaml_cache
    if _yaml_cache is not None:
        return _yaml_cache
    try:
        from app.shared.prompts.loader import PromptLoader
        _yaml_cache = PromptLoader.load("domains/<domain>")
        return _yaml_cache
    except Exception as exc:
        logger.warning("[<domain>_prompt] YAML load failed: %s", exc)
        _yaml_cache = {}
        return _yaml_cache

def _get(key: str, fallback: str = "") -> str:
    data = _load_yaml()
    val = data.get(key, fallback)
    return val if isinstance(val, str) else fallback

# Exported constants
<DOMAIN>_DOMAIN_SPECIFIC = _get("system_prompt", "Especialista em <Domain>.")
<DOMAIN>_SYSTEM_PROMPT = <DOMAIN>_DOMAIN_SPECIFIC      # legacy alias
<DOMAIN>_FEW_SHOT_EXAMPLES = _get("few_shot_examples", "")

<DOMAIN>_REASONING_PROMPT = """PROTOCOLO REACT — <DOMAIN>:
Contexto: {stage_context}
Memória: {memory_summary}
...
FORMATO DE SAIDA: JSON puro.
"""

def get_<domain>_system_prompt(stage: str, context: dict) -> str:
    """Compõe o prompt completo para o agente <domain>."""
    reasoning = <DOMAIN>_REASONING_PROMPT.format(
        stage_context=context.get("stage_context", ""),
        memory_summary=context.get("memory_summary", "Nenhuma memória."),
    )
    return f"{<DOMAIN>_SYSTEM_PROMPT}\n\n{<DOMAIN>_FEW_SHOT_EXAMPLES}\n\n{reasoning}\n\n{ANTI_SYCOPHANCY_OPERATIONAL}"
```

### Variantes de ANTI_SYCOPHANCY importadas

| Variante | Usada em |
|----------|----------|
| `ANTI_SYCOPHANCY_OPERATIONAL` | cv_screening, sourcing, analytics, ats_integration, communication, kanban, talent, jobs_mgmt |
| `ANTI_SYCOPHANCY_FULL` | wizard (job_management), hiring_policy |
| `ANTI_SYCOPHANCY_ORCHESTRATOR` | orchestrator (inline em `agent_prompts.yaml`) |

---

## Fluxo de composição completo de um agente especializado

```
1. ReAct agent precisa do system prompt
2. Chama: get_sourcing_system_prompt(stage="SOURCING", context={...})
3. sourcing_system_prompt.py:
   a. _load_yaml() → PromptLoader.load("domains/sourcing") → SOURCING_DOMAIN_SPECIFIC
   b. SOURCING_REASONING_PROMPT.format(stage_context, memory_summary)
   c. Concatena: DOMAIN_SPECIFIC + FEW_SHOT + REASONING + ANTI_SYCOPHANCY
   d. Retorna string → passa como extra_instructions para SystemPromptBuilder.build()
4. SystemPromptBuilder.build(agent_type="sourcing", extra_instructions=sourcing_prompt):
   a. Seção 1-3: IDENTITY + persona_base + platform_knowledge
   b. Seção 4: _load_domain_additions("sourcing") → agent_prompts.yaml sourcing section
   c. Seção 5-8: contexto dinâmico
   d. Seção 9: REACT_INSTRUCTIONS (porque agent_type != "orchestrator")
            + extra_instructions (o sourcing_prompt completo)
5. ComplianceDomainPrompt.get_system_prompt() (se domínio herda dela):
   + lgpd_block + fairness_block + bias_block + audit_block + guardrails
```

**Nota:** Em domínios que usam `ComplianceDomainPrompt`, o fluxo tem mais um passo: `get_system_prompt(base_prompt=sourcing_prompt)` adiciona compliance blocks.

---

## Exemplo concreto: SourcingAgent

### `sourcing_system_prompt.py` — o que a função `get_sourcing_system_prompt()` retorna

```
[SOURCING_DOMAIN_SPECIFIC]     ← from sourcing.yaml system_prompt
[SOURCING_FEW_SHOT_EXAMPLES]   ← from sourcing.yaml few_shot_examples (se existir)
[SOURCING_REASONING_PROMPT]    ← formatted with stage_context + memory_summary
  - Inclui: regra USO CORRETO DO PEARCH (condicional, só se < 5 resultados)
  - Inclui: DISCLAIMER DE DADOS DE MERCADO (números = benchmark estimado)
  - Inclui: TRATAMENTO DE FALHAS DE FERRAMENTA (nunca invente candidatos)
  - Inclui: FORMATO DE SAIDA: JSON puro
[ANTI_SYCOPHANCY_OPERATIONAL]  ← previne concordar com filtros discriminatórios
[NEGATION_DETECTION_BLOCK]     ← detecta negações antes de executar ações
```

### `CandidateSelfServiceAgent` — CSS_DOMAIN_SPECIFIC (leitura direta do YAML)

```python
# candidate_system_prompt.py — não usa _load_yaml(), lê YAML diretamente via pathlib
_yaml_path = Path(__file__).parent.parent.parent.parent / "prompts" / "domains" / "candidate_self_service.yaml"
_config = yaml.safe_load(_yaml_path.read_text()) if _yaml_path.exists() else {}

CSS_DOMAIN_SPECIFIC = (
    "DOMÍNIO: candidate_self_service\n"
    "ESCOPO: Apenas status do processo seletivo do candidato autenticado.\n"
    "PROIBIDO: scores internos, red_flags, dados de outros candidatos, ações de escrita.\n"
    "LGPD: Ao responder sobre rejeição/feedback, sempre informe o direito de explicação (Art. 20)."
)
```

---

## Instruções para Claude Code / Cursor

### "Cria novo agente especializado no v5"

```
1. Crie o YAML em app/prompts/domains/<novo_dominio>.yaml
   Campos obrigatórios:
     metadata:
       domain: "<novo_dominio>"
       version: "1.0"
       updated_at: "<data>"
       description: "..."
     system_prompt: |
       Você é especialista em <área>...

2. Crie app/domains/<novo_dominio>/agents/<novo>_system_prompt.py
   Siga o padrão:
   - _yaml_cache global + _load_yaml() + _get()
   - <DOMAIN>_DOMAIN_SPECIFIC = _get("system_prompt", fallback_text)
   - <DOMAIN>_REASONING_PROMPT com {stage_context} e {memory_summary}
   - get_<domain>_system_prompt(stage, context) → string completo
   - Importa ANTI_SYCOPHANCY_OPERATIONAL (ou FULL se consultivo)

3. Se domínio toma decisões sobre candidatos:
   - Adicione ao _DECISION_DOMAINS frozenset em compliance_base.py
   - Herde ComplianceDomainPrompt (não DomainPrompt)

4. Adicione entrada em app/prompts/shared/agent_prompts.yaml
   sob prompts.<novo_dominio>: |
   Role + responsabilidades + capacidades específicas

5. Registre o react agent em I1 (agents_registry.yaml)
```

### "Atualiza prompt de um agente existente"

```
1. Edite app/prompts/domains/<dominio>.yaml
2. Incremente metadata.version (ex: 2.0 → 2.1)
3. Atualize metadata.updated_at
4. NÃO edite o Python file — o YAML é o source of truth
5. Em produção: PromptLoader._cache precisa ser limpo ou worker reiniciado
```

### Setup em CLAUDE.md (snippet pronto)

```markdown
## Agent Specialization
24 domain YAMLs in app/prompts/domains/ — SSoT for agent behavior
11 agent types in app/prompts/shared/agent_prompts.yaml — consumed by SystemPromptBuilder
16 *_system_prompt.py files — compose REASONING_PROMPT + anti-sycophancy

Pattern:
  1. get_<domain>_system_prompt() in *_system_prompt.py
  2. Passes to SystemPromptBuilder.build(agent_type=X, extra_instructions=Y)
  3. ComplianceDomainPrompt.get_system_prompt() adds compliance blocks if domain is decision type
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

| Item | Flexibilidade |
|------|---------------|
| Conteúdo dos YAMLs (role descriptions, responsabilidades) | Adaptar para contexto do v5 |
| `REASONING_PROMPT` texto | Adaptar raciocínio para features do v5 |
| `FEW_SHOT_EXAMPLES` | Substituir por exemplos do v5 |
| Nomes dos arquivos Python | Renomear se necessário |
| Ordem de concatenação no `get_<domain>_system_prompt()` | Ajustar |

### NÃO pode adaptar (base legal ou arquitetural)

| Item | Motivo |
|------|--------|
| `ANTI_SYCOPHANCY_*` presente em domínios de decisão | Crença #11 do Manifesto WeDOTalent; violação cria risco de conformidade com filtros discriminatórios |
| `NEGATION_DETECTION_BLOCK` em domínios com ações irreversíveis | Previne execuções acidentais (rejeição, email, mudança de etapa) após negação |
| `ComplianceDomainPrompt` herdado em decision domains | Audit trail obrigatório (EU AI Act Art. 13) |
| `candidate_self_service` PROIBIDO scores/red_flags internos | LGPD Art. 20 + EU AI Act Art. 86 — candidato não pode ver scores internos |
| `pipeline_transition.yaml` type="decision" | Transições de candidato = decisão de alto impacto → FairnessGuard Layer 3 |

---

## Checklist de completude (P0/P1/P2)

- [ ] (P0) Todos os domain YAMLs têm `metadata.version` e `metadata.domain` (ou root-level equivalents)
- [ ] (P0) `candidate_self_service` PROÍBE scores internos e dados de outros candidatos
- [ ] (P0) Domínios de decisão herdam `ComplianceDomainPrompt` (não `DomainPrompt`)
- [ ] (P1) `_yaml_cache` global por módulo (não recarrega YAML a cada request)
- [ ] (P1) `ANTI_SYCOPHANCY_OPERATIONAL` presente em agentes operacionais (sourcing, cv_screening, etc.)
- [ ] (P1) `REASONING_PROMPT` tem placeholders `{stage_context}` e `{memory_summary}`
- [ ] (P1) `FORMATO DE SAIDA: JSON puro` no REASONING_PROMPT de agentes de decisão
- [ ] (P2) `few_shot_examples` key em YAMLs de domínios que usam exemplos
- [ ] (P2) `updated_at` atualizado em cada edição de YAML (auditoria)

---

## Gotchas e erros comuns

### G1: Editar Python file em vez do YAML

**Problema:** Dev hardcoda texto no `<DOMAIN>_DOMAIN_SPECIFIC` em vez de editar o YAML. Próximo deployment sincroniza YAML mas perde a mudança no Python.

**Solução:** YAML é o SSoT. O Python file é apenas o loader + composer. Nunca hardcode conteúdo de prompt no Python file.

---

### G2: Novo domínio não aparece no REASONING_PROMPT

**Problema:** Dev cria novo YAML mas não cria o Python file correspondente. O REASONING_PROMPT não é gerado com `{stage_context}` e `{memory_summary}` populados.

**Causa:** `_load_domain_additions()` em `SystemPromptBuilder` carrega só os adicionais do `agent_prompts.yaml`, não o REASONING_PROMPT de domínio específico. O REASONING_PROMPT é construído exclusivamente nos Python files.

---

### G3: anti-sycophancy errada por tipo

**Problema:** Agente wizard recebe `ANTI_SYCOPHANCY_OPERATIONAL` (mais simples) em vez de `ANTI_SYCOPHANCY_FULL` (com verificação de premissas). Wizard perde capacidade de questionar afirmações do recrutador.

**Solução:** Domínios consultivos/estratégicos (wizard, policy) usam `ANTI_SYCOPHANCY_FULL`. Domínios operacionais usam `ANTI_SYCOPHANCY_OPERATIONAL`.

---

### G4: yaml_cache não invalida em teste

**Problema:** Testes que precisam testar diferentes conteúdos de YAML não conseguem limpar o `_yaml_cache` global do módulo Python.

**Solução:** Nos testes, usar `monkeypatch` para setar `<module>._yaml_cache = None` antes do teste que modifica o YAML.

---

## Testes obrigatórios

| Teste | Path | Cenário coberto |
|-------|------|-----------------|
| YAML metadata validation | `tests/unit/test_prompt_version_loader.py` | validate_all_prompts() retorna {} (sem erros) |
| candidate_self_service PROIBIDO scores | `tests/unit/test_candidate_system_prompt.py` | Prompt não menciona "wsi_score" ou "red_flags" |
| REASONING_PROMPT format | `tests/unit/test_domain_system_prompts.py` | stage_context + memory_summary substituídos |
| anti-sycophancy em sourcing | `tests/unit/test_domain_system_prompts.py` | ANTI_SYCOPHANCY_OPERATIONAL presente em get_sourcing_system_prompt() |
| anti-sycophancy FULL no wizard | `tests/unit/test_domain_system_prompts.py` | ANTI_SYCOPHANCY_FULL presente em get_wizard_system_prompt() |
| _yaml_cache singleton | `tests/unit/test_domain_system_prompts.py` | Segunda chamada não relê arquivo YAML |
| ComplianceDomainPrompt em decision domains | `tests/integration/test_persona_invariants.py` | pipeline_transition herda ComplianceDomainPrompt |

---

## Referências

- **P1 — System Prompt Composition** — `_load_domain_additions()` consome `agent_prompts.yaml`
- **P4 — Interaction Patterns** — `ANTI_SYCOPHANCY_OPERATIONAL/FULL`, `NEGATION_DETECTION_BLOCK`
- **C1 — Fairness** — `ComplianceDomainPrompt` auto-injeta fairness_block em decision domains
- **I1 — Agent Architecture** — react agents chamam `get_<domain>_system_prompt()`
- **LIA_PERSONA §9.2, §9.6, §9.11** — especialização + compliance por domínio (verbatim)
- **EU AI Act Art. 13** — transparência: base legal para `metadata.version` obrigatório
- **LGPD Art. 20** — direito de contestação: base legal para `candidate_self_service` restrições
