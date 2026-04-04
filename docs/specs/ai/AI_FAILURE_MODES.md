# AI Failure Modes — WeDOTalent / Plataforma LIA

> Última atualização: 2026-03-26
> Fonte: leitura direta de `circuit_breaker.py`, `react_loop.py`, `llm.py`, `defensive_prompts.py`, `cascaded_router.py`, config settings
> **SPEC-DRIVEN DEVELOPMENT** — catálogo de modos de falha, circuit breakers, fallbacks e mensagens ao usuário.

---

## 1. Arquitetura de Resiliência — 6 Camadas

```
┌──────────────────────────────────────────────────────────────────┐
│  CAMADA 1 — TOKEN BUDGET GUARD (pré-loop)                        │
│  Verifica limites de token/custo ANTES de iniciar o ReAct loop   │
│  Se estourado → resposta imediata sem chamar LLM                 │
│  Configurável: REACT_TOKEN_BUDGET_ENABLED, company_id            │
└────────────────────────┬─────────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────────┐
│  CAMADA 2 — CIRCUIT BREAKER (por serviço externo)                │
│  14 circuits pré-configurados: LLM (3), ATS (4), Auth (1),      │
│  Sourcing (1), Calendar (1), Email (2), Payments (2)             │
│  Estados: CLOSED → OPEN → HALF_OPEN → CLOSED                    │
│  Notificação: Bell + Teams (Redis dedup 1 alerta/hora)           │
└────────────────────────┬─────────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────────┐
│  CAMADA 3 — REACT LOOP ERROR HANDLING                            │
│  Max iterations guard, duplicate tool call detection,            │
│  failed tool call tracking, parse error recovery                 │
└────────────────────────┬─────────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────────┐
│  CAMADA 4 — LLM CASCADE (confidence-based)                       │
│  Haiku(0.80) → Sonnet(0.70) → Opus(0.60) → requires_human       │
│  Cada tier com threshold de confiança independente                │
└────────────────────────┬─────────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────────┐
│  CAMADA 5 — DEFENSIVE PROMPTS (nível de prompt)                  │
│  Clarification triggers, ambiguity detection, error recovery     │
│  prompts, out-of-scope responses                                 │
└────────────────────────┬─────────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────────┐
│  CAMADA 6 — AGENT HEALTH ALERTS (monitoramento contínuo)         │
│  record_failure() / record_success() por agent_id + company_id   │
│  Alerta após N falhas consecutivas                               │
└──────────────────────────────────────────────────────────────────┘
```

### 1.1 Fontes de Verdade por Componente

| Mecanismo | Fonte Canônica | Arquivo |
|-----------|---------------|---------|
| Circuit breaker (14 circuits) | Circuit instances + utilities | `app/shared/resilience/circuit_breaker.py` |
| ReAct loop error handling | `ReActLoop.run()` | `libs/agents-core/lia_agents_core/react_loop.py` |
| LLM cascade (confidence) | `LLMService.generate_with_cascade()` | `app/services/llm.py` L827-909 |
| Cascaded router (6 tiers) | `CascadedRouter.route()` | `app/orchestrator/cascaded_router.py` |
| Defensive prompts | `get_defensive_prompt_section()` | `app/shared/robustness/defensive_prompts.py` + `shared/defensive.yaml` |
| Guardrails (3-source cascade) | `_resolve_guardrails()` | `libs/agents-core/lia_agents_core/enhanced_agent_mixin.py` L108-163 |
| Autonomy engine (per-company) | `AutonomyEngine.resolve_guardrails()` | `libs/agents-core/lia_agents_core/autonomy_engine.py` |
| Token budget guard | `token_tracking_service.check_limits()` | `react_loop.py` pré-loop check |
| Agent health alerts | `agent_health_alert_service.record_failure()` | Chamado no `except` do ReAct loop |
| Degraded mode responses | `DEGRADED_MODE_RESPONSES` dict | `circuit_breaker.py` (inline dict) |
| Scope validation (fail-open) | `is_tool_allowed_in_scope()` | `app/tools/scope_config.py` via `react_loop.py` L494-510 |

---

## 2. Circuit Breaker — Implementação Detalhada

### 2.1 Padrão de 3 Estados

```
       ┌─── 5 falhas ───┐
       │                 ▼
    CLOSED ←───── HALF_OPEN ←───── OPEN
       ▲     2 sucessos  │    recovery_timeout
       │                 │     (30-60s)
       └────── reset ────┘
```

| Estado | Comportamento | Transição |
|--------|--------------|-----------|
| `CLOSED` | Chamadas passam normalmente; cada falha incrementa contador | → `OPEN` quando `failure_count ≥ failure_threshold` |
| `OPEN` | Todas as chamadas rejeitadas com `CircuitBreakerError`; retorna `retry_after` | → `HALF_OPEN` quando `recovery_timeout` expira |
| `HALF_OPEN` | Permite chamadas limitadas para testar recuperação | → `CLOSED` quando `success_count ≥ success_threshold`; → `OPEN` se qualquer falha |

### 2.2 Configuração dos 14 Circuits

```
Arquivo: app/shared/resilience/circuit_breaker.py
```

| Circuit | failure_threshold | recovery_timeout | success_threshold | timeout | Tier |
|---------|------------------|-----------------|------------------|---------|------|
| `anthropic` | 5 | 30s | 2 | 60s | critical |
| `openai` | 5 | 30s | 2 | 60s | critical |
| `gemini` | 5 | 30s | 2 | 60s | high |
| `pearch` | 3 | 60s | 2 | 30s | high |
| `workos` | 5 | 30s | 2 | 15s | critical |
| `merge` | 5 | 45s | 2 | 30s | high |
| `google_calendar` | 5 | 60s | 2 | 30s | medium |
| `gupy` | 5 | 45s | 2 | 30s | high |
| `pandape` | 5 | 45s | 2 | 30s | high |
| `sendgrid` | 5 | 30s | 2 | 30s | critical |
| `resend` | 5 | 30s | 2 | 30s | high |
| `iugu` | 3 | 60s | 2 | 30s | medium |
| `vindi` | 3 | 60s | 2 | 30s | medium |

**Circuit adicional no ReAct loop:**

| Circuit | failure_threshold | recovery_timeout | success_threshold | timeout | Escopo |
|---------|------------------|-----------------|------------------|---------|--------|
| `llm_react_reason` | 3 | 60s | 2 | 30s | Chamadas LLM dentro do `_reason()` |

### 2.3 SLOs por Serviço (F1-03)

| Serviço | Availability Target | Latency P95 | Error Budget | Tier |
|---------|-------------------|-------------|-------------|------|
| Anthropic (LLM primário) | 99.9% (~43min/mês) | 8.000ms | 0.1% | critical |
| OpenAI (LLM alternativo) | 99.9% | 10.000ms | 0.1% | critical |
| Gemini (LLM multimodal) | 99.5% | 15.000ms | 0.5% | high |
| Pearch AI (190M+ perfis) | 99.0% | 5.000ms | 1.0% | high |
| WorkOS (SSO/SCIM) | 99.9% | 3.000ms | 0.1% | critical |
| Merge.dev (multi-ATS) | 99.0% | 5.000ms | 1.0% | high |
| Google Calendar | 99.5% | 3.000ms | 0.5% | medium |
| Gupy (ATS) | 99.0% | 5.000ms | 1.0% | high |
| Pandapé (ATS) | 99.0% | 5.000ms | 1.0% | high |
| SendGrid (email) | 99.9% | 2.000ms | 0.1% | critical |
| Resend (email alt.) | 99.9% | 2.000ms | 0.1% | high |
| Iugu (pagamentos) | 99.5% | 5.000ms | 0.5% | medium |
| Vindi (pagamentos) | 99.5% | 5.000ms | 0.5% | medium |

### 2.4 Notificação de Circuit Open (COMP-3)

Quando um circuit abre:
1. Função `_notify_circuit_open(service_name)` é chamada assincronamente
2. **Redis dedup**: chave `cb_alert:{service_name}` com TTL de 1 hora — máximo 1 alerta por circuit por hora
3. **Canais**: Bell (in-app) + Teams (webhook)
4. **Mensagem**: `"⚡ Circuit Breaker ABERTO: {service_name}"` com recovery time estimado
5. **Severity**: `warning`

### 2.5 Métricas Prometheus

```python
circuit_breaker_state.labels(service=name).set(value)
# 0 = closed, 1 = half_open, 2 = open
```

---

## 3. Degraded Mode Responses — Mensagens ao Usuário

Quando o circuit está OPEN e nenhum fallback específico está disponível, o sistema retorna uma mensagem de modo degradado em PT-BR:

| Serviço | Mensagem ao Usuário |
|---------|-------------------|
| `anthropic` | "A assistente LIA está temporariamente indisponível. O serviço de IA principal (Anthropic) está com instabilidades. Tente novamente em alguns minutos ou contate o suporte." |
| `openai` | "O serviço de IA alternativo está temporariamente indisponível. Tente novamente em instantes." |
| `gemini` | "A análise multimodal está temporariamente indisponível. Tente novamente em instantes." |
| `pearch` | "A busca de candidatos externos está temporariamente indisponível. Você pode buscar na base interna de candidatos enquanto isso." |
| `workos` | "O serviço de autenticação está com instabilidades. Tente fazer login novamente ou contate o suporte." |
| `merge` | "A sincronização com ATS externo está temporariamente indisponível. Os dados locais continuam acessíveis." |
| `google_calendar` | "O agendamento via Google Calendar está temporariamente indisponível. Agende manualmente e tente a sincronização mais tarde." |
| `gupy` | "A integração com Gupy está temporariamente indisponível. Os dados locais continuam acessíveis." |
| `pandape` | "A integração com Pandapé está temporariamente indisponível. Os dados locais continuam acessíveis." |
| `sendgrid` | "O envio de emails está temporariamente indisponível. As mensagens serão reenviadas assim que o serviço for restaurado." |
| `resend` | "O serviço de email alternativo está temporariamente indisponível. Tente novamente em instantes." |
| `iugu` | "O serviço de pagamentos está temporariamente indisponível. Tente novamente em alguns minutos ou contate o suporte financeiro." |
| `vindi` | "O serviço de pagamentos recorrentes está temporariamente indisponível. Tente novamente em alguns minutos." |
| **(fallback genérico)** | "Este serviço está temporariamente indisponível. Tente novamente em alguns minutos." |

---

## 4. ReAct Loop — Modos de Falha

### 4.1 Catálogo de Falhas no ReAct Loop

```
Arquivo: libs/agents-core/lia_agents_core/react_loop.py (1.082 linhas)
```

| Modo de Falha | Detecção | Comportamento | Mensagem ao Usuário |
|---------------|----------|---------------|---------------------|
| **Max iterations atingido** | `state.iteration >= config.max_iterations` | Gera resposta com observações parciais | "Desculpe, não consegui concluir o processamento completo. Aqui está o que consegui reunir: [observações]. Por favor, tente reformular." |
| **Token budget estourado** | `state.tokens_used_estimate >= token_budget` | Para o loop, gera resposta final | Resposta gerada pelo LLM com contexto parcial |
| **Parse error no reasoning** | `_parse_reasoning()` lança exception | Trata reasoning raw como resposta direta | Usa o texto do reasoning como resposta (degraded) |
| **Tool desconhecida** | `tool_name not in self._tool_map` | Observação + continua loop | (Não exposta ao usuário — retry interno) |
| **Tool já falhou** | `call_key in state.failed_tool_calls` | Observação "já falhou" + continua | (Não exposta — tenta outra abordagem) |
| **Tool call duplicada** | `consecutive_duplicate_count >= THRESHOLD` | Força geração de resposta | Resposta gerada com dados parciais |
| **Guardrail bloqueio** | `tool_name in config.guardrails` | Para loop + pede confirmação | "I need your confirmation before executing '{tool_name}'. Shall I proceed?" |
| **Circuit breaker OPEN** | `CircuitBreakerError` capturada | Resposta de fallback amigável | "O serviço de IA está temporariamente indisponível devido a instabilidade. Tente novamente em ~{retry_after} segundos." |
| **Exceção genérica** | `except Exception` no loop principal | Log + resposta genérica + health alert | "I encountered an error while processing your request. Please try again." |
| **Budget limit pré-loop** | `check_limits()` retorna `False` | Resposta imediata sem LLM | "Limite de uso atingido: {reason}. Entre em contato com o administrador para aumentar os limites." |
| **Resposta vazia após max iter** | `final_response` é None ou vazio | Constrói fallback com observações | "Desculpe, não consegui concluir... Aqui está o que consegui reunir: [últimas 3 observações]" |

### 4.2 Duplicate Tool Call Detection

```python
REACT_DUPLICATE_THRESHOLD = settings.REACT_DUPLICATE_THRESHOLD  # default: 3

if call_key == state.last_tool_call_key:
    state.consecutive_duplicate_count += 1
    if consecutive_duplicate_count >= THRESHOLD:
        # Força resposta com dados parciais
        state.final_response = await self._generate_response(state, context)
        break
```

### 4.3 Failed Tool Call Tracking

```python
state.failed_tool_calls: List[str] = []  # Serialised keys

if not tool_success:
    state.failed_tool_calls.append(call_key)
    # Na próxima iteração:
    if call_key in state.failed_tool_calls:
        observation = "Tool '{name}' already failed with these parameters. 
                       Try different parameters or a different approach."
```

### 4.4 Confidence Calibration (D2)

```python
# Após o loop:
tool_success_ratio = (total - failed) / total  if total > 0  else 1.0
completion_ratio   = 0.3 if state.error else 1.0
state.confidence_score = tool_success_ratio * 0.7 + completion_ratio * 0.3
```

---

## 5. LLM Cascade — Escalação por Confiança

### 5.1 Fluxo

```
┌────────────┐   confidence < 0.80   ┌────────────┐   confidence < 0.70   ┌────────────┐
│   Haiku    │ ──────────────────── ▶ │   Sonnet   │ ──────────────────── ▶ │    Opus    │
│ (barato)   │                        │ (principal) │                        │  (caro)    │
└────┬───────┘                        └────┬───────┘                        └────┬───────┘
     │ ≥ 0.80                              │ ≥ 0.70                              │ ≥ 0.60
     ▼                                     ▼                                     ▼
  Resultado                             Resultado                             Resultado
  aceito                                aceito                                aceito
                                                                                 │
                                                                                 │ < 0.60
                                                                                 ▼
                                                                          requires_human=True
                                                                          reason="all_models_low_confidence"
```

### 5.2 Tratamento de Erro por Tier

```python
for model_name, threshold in cascade:
    try:
        response = await llm.ainvoke(messages)
        confidence = parsed.get("confidence", 0.5)  # default neutro
        if confidence >= threshold:
            return LLMCascadeResult(content=raw, model_used=model_name, confidence=confidence)
        # Escala para próximo tier
    except Exception as exc:
        logger.warning(f"[cascade] Falha no modelo {model_name}: {exc}")
        continue  # Tenta próximo modelo

# Se todos falharem:
return LLMCascadeResult(content=None, model_used="none", confidence=0.0, 
                        requires_human=True, reason="all_models_low_confidence")
```

---

## 6. Cascaded Router — Fallback de Classificação

### 6.1 Tiers de Routing com Fallback

```
Tier 0: MemoryResolver     → resolução de pronomes/referências
Tier 1: LRU in-process     → cache MD5 em memória local
Tier 2: Redis hash cache   → cache distribuído exato
Tier 3: VectorSemanticCache → pgvector cosine ≥ 0.92
Tier 4: FastRouter          → regex/keyword patterns
Tier 5: LLM Cascade        → Haiku→Sonnet→Opus
Fallback: clarification_needed → pergunta ao usuário
```

### 6.2 RouteResult — Clarificação

```python
@dataclass
class RouteResult:
    domain_id: str
    confidence: float
    source: str                       # qual tier resolveu
    needs_clarification: bool = False  # se nenhum tier resolveu
    clarification_question: Optional[str] = None
    clarification_options: Optional[List[str]] = None
```

---

## 7. Defensive Prompts — Tratamento de Erros no Nível do Prompt

### 7.1 Error Recovery Prompt

O sistema usa um prompt LLM para decidir como recuperar de erros:

```
ERRO: {error}
OPERAÇÃO: {operation}
CONTEXTO: {context}

RESPONDA EM JSON:
{
    "recoverable": true/false,
    "partial_data_available": true/false,
    "user_message": "mensagem amigável para o usuário",
    "suggested_action": "ação alternativa se aplicável",
    "retry_possible": true/false
}
```

### 7.2 Ambiguity Detection Prompt

Antes de executar ações, o sistema pode detectar ambiguidade:

```
RESPONDA EM JSON:
{
    "is_ambiguous": true/false,
    "ambiguity_type": "intent|target|parameters|conflict|none",
    "missing_info": ["lista do que falta"],
    "clarification_needed": "pergunta a fazer se ambíguo",
    "confidence": 0.0-1.0
}
```

### 7.3 Clarification Triggers

| Trigger | Quando ativado | Mensagem |
|---------|---------------|----------|
| `missing_job` | Contexto de vaga ausente | "Qual vaga você está trabalhando? Por favor, me diga o nome ou ID da vaga." |
| `missing_candidate` | Contexto de candidato ausente | "Qual candidato você está avaliando? Me informe o nome ou ID do candidato." |
| `ambiguous_action` | Intenção não clara | "Não tenho certeza do que você quer fazer. Você poderia reformular?" |
| `missing_date` | Data/horário faltante | "Para quando você gostaria de agendar? Por favor, informe a data e horário." |
| `missing_criteria` | Critérios de busca ausentes | "Quais critérios você gostaria de usar? Skills, experiência, localização?" |
| `confirm_action` | Confirmação de ação | "Só para confirmar: você quer {action}? Responda 'sim' para confirmar." |
| `partial_match` | Resultados parciais | "Não encontrei resultados exatos, mas encontrei resultados similares. Deseja ver?" |
| `empty_result` | Busca sem resultados | "Não encontrei resultados com esses critérios. Gostaria de expandir a busca?" |

---

## 8. Matriz Domínio × Tipo de Falha × Comportamento

### 8.1 Falhas de LLM (Todos os Domínios)

| Tipo de Falha | Detecção | Comportamento | Impacto no Usuário |
|---------------|----------|---------------|-------------------|
| LLM timeout (>30s) | `asyncio.TimeoutError` no circuit breaker | Incrementa failure count; se threshold atingido → circuit OPEN | Retry automático ou mensagem de indisponibilidade |
| LLM resposta malformada | `_parse_reasoning()` exception | Trata como `action="respond"` com texto raw | Resposta pode ser menos estruturada mas funcional |
| LLM rate limit (429) | Exception capturada pelo circuit | Incrementa failure count | Após 3-5 falhas: circuit OPEN + mensagem degradada |
| LLM resposta vazia | `not response_text` | Chama `_generate_response()` como fallback | Gera resposta com dados parciais das observações |
| Todos os LLMs falharam | Cascade exaure 3 tiers | `requires_human=True` | Escalonamento para humano |

### 8.2 Falhas de Tool Call — Comportamento Genérico do ReAct Loop

Quando qualquer tool falha, o comportamento é determinado pelo ReAct loop (código em `react_loop.py` linhas 520-580):

```
1. Tool retorna success=False ou lança exceção
2. call_key é adicionado a state.failed_tool_calls
3. Observação de erro é adicionada ao state para o LLM raciocinar
4. Na próxima iteração, se mesma tool/args → skip automático com mensagem:
   "Tool '{name}' already failed with these parameters."
5. LLM decide: tentar outra abordagem, outro tool, ou responder ao usuário
```

**Tools registradas por domínio** (verificáveis nos `*_tool_registry.py` de cada domínio):

| Domínio | Tools registradas | Arquivo de referência |
|---------|------------------|----------------------|
| Wizard (Job Management) | `get_salary_benchmarks`, `validate_job_requirements`, `save_job_draft` | `app/domains/job_management/agents/wizard_tool_registry.py` |
| Sourcing | `search_candidates` (6 variantes), `send_outreach` | `app/domains/sourcing/tools.py`, `sourcing_engagement_tool_registry.py` |
| CV Screening (Pipeline) | `run_wsi_screening`, `view_screening_results`, `move_candidate`, `finalize_hiring` | `app/domains/cv_screening/agents/pipeline_tool_registry.py` |
| Kanban | `batch_move`, `send_bulk_email`, `start_screening_batch` | `app/domains/recruiter_assistant/agents/kanban_tool_registry.py` |
| Talent | `search_candidates`, `list_candidates`, `view_candidate_profile` | `app/domains/recruiter_assistant/agents/talent_tool_registry.py` |

**Nota**: O LLM decide a mensagem de fallback ao usuário com base no contexto; não há mensagens de fallback hardcoded por tool. As mensagens no `wizard_system_prompt.py` são instruções ao LLM sobre *como* comunicar falhas, não templates fixos.

### 8.3 Falhas de Contexto

O tratamento de contexto ausente é feito via prompts defensivos (definidos em `shared/defensive.yaml`). O LLM usa os clarification triggers para pedir informações ao recrutador:

| Trigger (defensive.yaml) | Quando aplicado | Mensagem ao Recrutador |
|--------------------------|-----------------|----------------------|
| `missing_job` | Contexto de vaga ausente | "Qual vaga você está trabalhando?" |
| `missing_candidate` | Contexto de candidato ausente | "Qual candidato você está avaliando?" |
| `ambiguous_action` | Intenção não clara | "Não tenho certeza do que você quer fazer..." |
| `missing_date` | Data/horário faltante | "Para quando você gostaria de agendar?" |
| `missing_criteria` | Critérios de busca ausentes | "Quais critérios você gostaria de usar?" |

**Nota**: estas mensagens são templates nos prompts defensivos — o LLM pode reformulá-las. Não são respostas fixas do sistema.

---

## 9. Agent Health Alert Service

### 9.1 Mecanismo

```python
# Após exceção no ReAct loop:
await agent_health_alert_service.record_failure(
    company_id=context.get("company_id", ""),
    agent_id=self.config.domain,
    error=str(exc),
    notify_user_id=context.get("user_id"),
)

# Após sucesso:
await agent_health_alert_service.record_success(
    company_id=context.get("company_id", ""),
    agent_id=self.config.domain,
)
```

### 9.2 Comportamento

- `record_failure()`: incrementa contador de falhas consecutivas por (company_id, agent_id)
- `record_success()`: reseta contador para zero
- Após N falhas consecutivas: envia notificação ao admin e/ou `notify_user_id`
- **Best-effort**: se o serviço de health alert falhar, a exceção é logada mas não propaga

---

## 10. Token Budget Guard

### 10.1 Pré-Loop Check

```python
if settings.REACT_TOKEN_BUDGET_ENABLED:
    _within_limits, _limit_reason = await token_tracking_service.check_limits(
        user_id=user_id,
        company_id=company_id,
    )
    if not _within_limits:
        state.final_response = f"Limite de uso atingido: {_limit_reason}. 
                                 Entre em contato com o administrador."
        return state  # Sem chamar LLM
```

### 10.2 In-Loop Check

```python
if token_budget and state.tokens_used_estimate >= token_budget:
    state.observations.append(f"Token budget ({token_budget}) reached.")
    state.final_response = await self._generate_response(state, context)
    break  # Sai do loop
```

### 10.3 Pós-Loop Recording

```python
await token_tracking_service.record_usage(
    user_id=user_id,
    company_id=company_id,
    agent_type=self.config.domain,
    intent="react_loop",
    input_tokens=tokens_estimate // 2,
    output_tokens=tokens_estimate // 2,
    model=model_name,
    latency_ms=total_duration,
)
```

---

## 11. Scope Validation (E8) — Fail-Open

```python
if self.config.active_scope:
    _scope_allowed = is_tool_allowed_in_scope(
        tool_name, PromptScope(self.config.active_scope)
    )
    if not _scope_allowed:
        logger.warning(
            "[SCOPE-VIOLATION] agent=%s tool=%s scope=%s — "
            "tool fora do escopo ativo, prosseguindo (fail-open)"
        )
```

**Escopos possíveis**: `TALENT_FUNNEL`, `JOB_TABLE`, `IN_JOB`, `GLOBAL`

Violações são **logadas** mas **não bloqueiam** a execução (fail-open). O objetivo é auditoria, não enforcement.

---

## 12. Streaming Callback (E7) — Fail-Silent

```python
if state.streaming_callback:
    try:
        await state.streaming_callback({
            "type": "thinking",
            "step": state.iteration,
            "thought": f"Chamando tool: {tool_name}",
        })
    except Exception:
        pass  # fail-silent — não bloqueia o loop
```

Eventos de streaming NUNCA bloqueiam o loop principal. Se o WebSocket falhar, o processamento continua normalmente.

---

## 13. Guardrails — Ações que Requerem Confirmação

Certas tool calls são bloqueadas pelo ReAct loop até o recrutador confirmar. A lista é determinada por 3 fontes em cascata (código em `enhanced_agent_mixin.py` linhas 108-163):

### 13.1 Fonte Primária: AutonomyEngine (por empresa)

```
Arquivo: libs/agents-core/lia_agents_core/autonomy_engine.py

GUARDRAILS_BY_LEVEL:
  low:    move_candidate, batch_move, reject_candidate, schedule_interview,
          generate_offer, finalize_hiring, create_job, update_job, delete_job,
          send_message, bulk_send
  medium: batch_move, reject_candidate, generate_offer, finalize_hiring,
          delete_job, bulk_send
  high:   finalize_hiring, delete_job
```

O nível é determinado pela `CompanyHiringPolicy` da empresa (cache 5min, TTL 300s).

### 13.2 Fonte Secundária: GuardrailRepository (banco de dados)

Se a AutonomyEngine falhar → consulta `GuardrailRepository.get_blocked_tools(db, domain, company_id)`.

### 13.3 Fallback Estático (_DEFAULT_GUARDRAIL_TOOLS)

Se ambas as fontes falharem → lista estática:

```python
_DEFAULT_GUARDRAIL_TOOLS = [
    "move_candidate",
    "batch_move",
    "finalize_hiring",
    "delete_job",
    "reject_candidate",
    "send_bulk_email",
    "update_candidate_field",
]
```

### 13.4 Guardrails por Domínio (Registros Específicos)

| Domínio | Guardrail Tools | Fonte |
|---------|----------------|-------|
| Sourcing | `send_outreach` | `sourcing_engagement_tool_registry.py` L14 |

### 13.5 Comportamento quando guardrail ativa

```
Arquivo: react_loop.py linhas 471-485

if tool_name in self.config.guardrails:
    state.final_response = (
        f"I need your confirmation before executing '{tool_name}'. "
        f"Shall I proceed?"
    )
    state.should_respond = True
    break  # Sai do loop, espera confirmação
```

---

## 14. Wizard — Tratamento de Erros Específico

O `wizard_system_prompt.py` inclui instruções específicas de error handling inline:

```
=== TRATAMENTO DE ERROS ===
- Se uma ferramenta falhar, informe o usuário de forma amigável
- Nunca mostre detalhes técnicos, stack traces ou códigos de erro
- Ofereça alternativas quando possível
- Exemplo: "Não consegui buscar os benchmarks salariais agora, 
  mas posso sugerir uma faixa com base na minha experiência. 
  Quer que eu faça isso?"
```

**Regras Críticas do Wizard:**
1. NUNCA mostre JSON, erros técnicos ou IDs internos ao usuário
2. NUNCA invente dados — use ferramentas para buscar informações reais
3. Se dados de benchmark indisponíveis → sugira com base em experiência, mas informe que são estimativas

---

## 15. Archived Mock Interfaces

3 tabs do Talent Funnel foram arquivadas em `_archived/` com handlers locais sem backend:

| Tab | Arquivo | Handler | Status |
|-----|---------|---------|--------|
| Pipelines | `_archived/pipelines-tab.tsx` | `handleLIAInsights()` | **ARCHIVED** — não carregada em produção |
| Personas | `_archived/personas-tab.tsx` | `handleLIAInsights()` | **ARCHIVED** — não carregada em produção |
| Mapping | `_archived/mapping-tab.tsx` | `handleLIAInsights()` | **ARCHIVED** — não carregada em produção |

O componente ativo `candidates-page.tsx` usa `handleLIAChatMessage()` e `handleLIAClick()` para interação com o backend LIA via API; `tasks-page.tsx` usa `handleLIAAction()` para ações contextuais por vaga.

---

## 16. Observabilidade e Métricas

### 16.1 Métricas Prometheus Disponíveis

| Métrica | Labels | Significado |
|---------|--------|-------------|
| `circuit_breaker_state` | `service` | Estado do circuit (0=closed, 1=half_open, 2=open) |
| `agent_iterations_total` | `domain`, `action_type` | Contagem de iterações do ReAct (respond/call_tool) |
| `router_tier_hit_total` | `tier` | Qual tier do cascaded router resolveu a intent |
| `router_latency_ms` | — | Latência do routing |
| `router_confidence_histogram` | — | Distribuição de confidence dos routes |

### 16.2 LangSmith Tracing

```python
@_traceable(name="ReAct Loop", run_type="chain")
async def run(self, message, context, session_id, observer=None):
    # Toda execução é traçada no LangSmith
```

### 16.3 Audit Callback

```python
if _audit:
    _audit.on_chain_start_manual()
    _audit.on_llm_call(prompt_preview, response_preview, latency_ms, model, ...)
    _audit.on_tool_call(tool_name, input_preview, output_preview, latency_ms, success, error)
```

---

## 17. Resumo de Fallback Chains

### 17.1 LLM Indisponível

```
1. Circuit breaker detecta falhas (threshold 3-5)
2. Circuit abre → notificação Bell+Teams (Redis dedup)
3. Próxima chamada: CircuitBreakerError capturada pelo ReAct loop
4. Resposta: "O serviço de IA está temporariamente indisponível..."
5. Após recovery_timeout (30-60s): circuit → HALF_OPEN → testa
6. Se 2 sucessos: circuit → CLOSED (operação normal)
```

### 17.2 Tool Call Falha

```
1. Tool retorna success=False
2. call_key adicionado a failed_tool_calls
3. Se mesma tool chamada novamente com mesmos args → skip automático
4. Agent tenta abordagem diferente (outra tool ou args diferentes)
5. Se N iterações sem progresso → força resposta com dados parciais
```

### 17.3 Max Iterations Atingido

```
1. Último observation: "Maximum iterations reached. Summarising..."
2. Tenta _generate_response() com contexto parcial
3. Se _generate_response() falha → fallback estático:
   "Desculpe, não consegui concluir... Aqui está o que consegui reunir:
   - [últimas 3 observações]
   Por favor, tente reformular."
```

### 17.4 Resposta Completamente Indisponível

```
1. Todas as tentativas de gerar resposta falharam
2. final_response é None ou vazio
3. Fallback construído com observações parciais
4. Se nenhuma observação disponível:
   "Desculpe, não consegui concluir o processamento completo da sua solicitação.
   Por favor, tente reformular ou fornecer mais detalhes."
```
