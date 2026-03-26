# LLM Decisions — WeDOTalent / Plataforma LIA

> Última atualização: 2026-03-26
> Fonte: leitura direta do código — `recruiter_agent_v5` + `lia-agent-system`
> **SPEC-DRIVEN DEVELOPMENT** — decisões de modelo, configuração e critérios de seleção.

---

# PARTE I — recruiter_agent_v5 (Gemini)

## 1. Modelo Primário

| Campo | Valor |
|-------|-------|
| **Provider** | Google Gemini |
| **Modelo Default** | `gemini-2.5-flash` |
| **Fallback** | `gemini-1.5-flash-latest` (em gemini_config.py) |
| **Biblioteca** | `langchain-google-genai` (`ChatGoogleGenerativeAI`) |
| **API Key** | `GEMINI_API_KEY` (env var obrigatória) |

### 1.1 Por que Gemini (recruiter_agent_v5)

- **Custo**: ~10x menor que GPT-4
- **Velocidade**: Flash models otimizados para latência baixa
- **Português**: Bom suporte a português brasileiro
- **Context window**: 1M tokens (permite contextos longos sem chunking)
- **LangChain**: Integração nativa via `langchain-google-genai`

## 2. Configurações por Domínio (recruiter_agent_v5)

| Agente/Domínio | Temperature | Modelo | Motivo |
|----------------|-------------|--------|--------|
| `IntentAnalyzerAgent` | 0.0 | gemini-2.5-flash | Determinismo na classificação |
| `APIPlannerAgent` | 0.0 | gemini-2.5-flash | Planos reproduzíveis |
| `PlanValidatorAgent` | 0.0 | gemini-2.5-flash | Validação determinística |
| `AnswerFormatterAgent` | 0.0 | gemini-2.5-flash | Formatação consistente |
| `AppliesDomain` | 0.0 | gemini-2.5-flash | Ações precisas |
| `JobsDomain` | 0.0 | gemini-2.5-flash | CRUD e analytics |
| `InsightsDomain` | 0.0 | gemini-2.5-flash | Dados concretos |
| `MessagingDomain` | 0.0 | gemini-2.5-flash | Sem criatividade indesejada |
| `EvaluationDomain` | **0.2** | gemini-2.5-flash | Avaliação mais natural |
| `AutonomousDomain` | 0.0 | gemini-2.5-flash | Determinismo universal |

## 3. Factory Centralizada (recruiter_agent_v5)

```python
create_tracked_llm(
    temperature=0.0,
    service_name="NomeDoDominio",
    operation="chat|intent",
    model_override=None,
    max_output_tokens=None,
    extra_callbacks=None,
)
```

Tracking via `LLMUsageCallbackHandler`: service_name, operation, tokens in/out, latência, custo.

## 4. RAG (recruiter_agent_v5)

| Campo | Valor |
|-------|-------|
| **Serviço** | `RAGService` (`src/services/rag_service.py`) |
| **Uso** | IntentAnalyzer e APIPlanner consultam docs de APIs |
| **Fonte** | ~50 arquivos YAML em `documentation/` |

## 5. Circuit Breaker (recruiter_agent_v5)

| Parâmetro | Valor |
|-----------|-------|
| Threshold | 3 falhas consecutivas |
| Cooldown | 30 segundos |
| Retry delay | 1 segundo |

## 6. Custos Gemini Flash (referência)

| Métrica | Valor |
|---------|-------|
| Input (até 128K tokens) | $0.075 / 1M tokens |
| Input (> 128K tokens) | $0.15 / 1M tokens |
| Output | $0.30 / 1M tokens |
| Context window | 1M tokens |

**Estimativa por query:** ~15K input + ~2.8K output

---

# PARTE II — lia-agent-system (Claude Primário)

## 7. LLM Service — Cascade Haiku→Sonnet→Opus

Arquivo: `app/services/llm.py`

A plataforma usa uma **cascata de 3 modelos** que otimiza custo vs qualidade automaticamente: começa pelo mais barato (Haiku), e só escala se a confiança não atingir o threshold mínimo.

### 7.1 Modelos Configurados

| Variável | Modelo | Papel |
|----------|--------|-------|
| `LLM_PRIMARY_MODEL` | `claude-sonnet-4-6` | Primário para tudo |
| `LLM_FAST_MODEL` | `claude-haiku-4-5` | Rápido e barato |
| `LLM_POWERFUL_MODEL` | `claude-opus-4-6` | Complexo, caro |
| `LLM_GEMINI_MODEL` | `gemini-2.5-flash` | Fallback final |

### 7.2 Provedores em Ordem

```
1. Claude (Anthropic) — primário para tudo
   → ChatAnthropic (LangChain)
   → ANTHROPIC_API_KEY ou AI_INTEGRATIONS_ANTHROPIC_API_KEY

2. OpenAI (GPT-4o) — fallback
   → ChatOpenAI (LangChain)
   → OPENAI_API_KEY

3. Gemini (Google) — fallback para geração de texto simples
   → google.genai SDK nativo (via Replit AI Integration)
   → AI_INTEGRATIONS_GEMINI_API_KEY
```

### 7.3 Cascade de Confiança (`generate_with_cascade`)

```python
LLM_CASCADE_FAST_THRESHOLD    = 0.80  # Haiku aceito se confiança >= 80%
LLM_CASCADE_MID_THRESHOLD     = 0.70  # Sonnet aceito se confiança >= 70%
LLM_CASCADE_FALLBACK_THRESHOLD = 0.60 # Opus aceito se confiança >= 60%

@dataclass
class LLMCascadeResult:
    content: Optional[str]
    model_used: str       # qual modelo foi suficiente
    confidence: float
    requires_human: bool  # True se todos abaixo do threshold
    reason: str

result = await llm_service.generate_with_cascade(
    prompt=prompt,
    cascade=["haiku", "sonnet", "opus"],
    confidence_threshold=settings.LLM_CASCADE_FAST_THRESHOLD
)
```

### 7.4 Tool Use / Function Calling

```python
response = await llm_service.generate_with_tools(
    messages=history,
    tools=tool_definitions,          # lista de ToolDefinition (Pydantic)
    provider="claude",
    system_prompt=system_prompt,
    max_tokens=4096
)
# Retorna: ToolCallResponse
#   .is_tool_call: bool
#   .tool_calls: List[ToolCallRequest] (id, name, parameters)
#   .text_response: Optional[str]
```

### 7.5 Parâmetros de Geração (sem magic numbers)

| Parâmetro | Valor | Arquivo |
|-----------|-------|---------|
| `LLM_DEFAULT_TEMPERATURE` | 0.7 | `app/core/config.py` |
| `LLM_AGENT_TEMPERATURE` | 0.3 | `app/core/config.py` |
| `LLM_MAX_TOKENS` | 4096 | `app/core/config.py` |
| `LLM_TIMEOUT_SECONDS` | 120.0 | `app/core/config.py` |

---

## 8. Configurações por Uso (lia-agent-system)

| Uso | Temperature | Modelo | Motivo |
|-----|-------------|--------|--------|
| T3 IntentRouter (classificação) | 0.0 | Haiku→Sonnet→Opus (cascade) | Determinismo forçado no roteamento |
| ReAct Loop (reasoning) | 0.3 | Claude Sonnet | Raciocínio controlado |
| Perguntas de triagem WSI | 0.1 | Claude Sonnet | Quase-determinístico |
| Geração de JD, emails | 0.5–0.7 | Claude Sonnet | Criatividade desejada |
| FairnessGuard L3 (LLM) | 0.0 | Claude Sonnet | Compliance determinístico |
| Avaliação WSI (rubrica) | — | Claude Sonnet | Score qualitativo |
| WSI Deterministic Scorer | — | Sem LLM | Funções puras, zero custo |

### 8.1 Regra Geral de Temperatura

| Temperatura | Caso de uso | Tipo |
|-------------|-------------|------|
| 0.0 | Classificação de intent, compliance | Determinístico forçado |
| 0.1 | Perguntas de triagem WSI | Quase-determinístico |
| 0.3 | Reasoning do loop ReAct | Não-determinístico controlado |
| 0.5–0.7 | Geração de JD, emails personalizados | Não-determinístico desejado |

---

## 9. ReAct Loop — Configuração LLM

**O que é:** Parâmetros de controle do loop de raciocínio dos agentes ReAct. Definidos em `app/core/config.py` (settings).

| Variável (settings) | Valor | Descrição |
|----------|:-----:|-----------|
| `REACT_MAX_ITERATIONS_DEFAULT` | 5 | Máximo de iterações reason→act→observe |
| `REACT_MAX_TOOL_CALLS` | 10 | Máximo de tool calls por request |
| `REACT_DUPLICATE_THRESHOLD` | 3 | Mesma ação N vezes → para |
| `REACT_OBSERVATION_MAX_CHARS` | 5000 | Trunca resultado de tool |

**Limites:** Cada iteração é rastreada via LangSmith `@traceable`. ReActObserver registra company_id, user_id, domain, tool timing.

---

## 10. Orchestrator — Routing LLM

### 10.1 T1: Hash Cache (sem LLM)

```
cache_max_size = 1000
Hash MD5 da mensagem → lookup O(1)
```

### 10.2 T2: FastRouter (sem LLM)

```
ROUTER_FAST_CONFIDENCE_THRESHOLD = 0.7
Regex/keyword patterns → domínio
```

### 10.3 T3: IntentRouter (com LLM)

```
generate_with_cascade(): Haiku → Sonnet → Opus
Few-shot examples: app/shared/prompts/examples/orchestrator_examples.py
```

### 10.4 Conversation Summary

A cada `ROUTER_SUMMARY_EVERY_N_MESSAGES` (padrão: 10) mensagens, gera resumo via LLM para manter contexto compacto.

---

## 11. Observabilidade de LLM

### 11.1 LangSmith

```python
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__...
LANGCHAIN_PROJECT=lia-agent-system
```

`@traceable` em todos os agentes e grafos — rastreia chamadas LLM com company_id + user_id.

### 11.2 Prometheus (13+ métricas)

Arquivo: `app/observability/metrics.py`

Métricas: `agent_iterations_total`, latência por domínio, tokens consumidos, erros por provider.

### 11.3 Drift Detection (4 triggers)

| Trigger | Threshold | Descrição |
|---------|-----------|-----------|
| Score drift | 0.5 | Variação absoluta no score médio WSI |
| Aprovação drift | 0.10 | 10 p.p. na taxa de aprovação |
| Cost drift | 0.20 | 20% variação no custo |
| Latency drift | 0.50 | 50% variação no P95 |

Batch: `drift.run_batch` — diário 06h Brasília.
Alerta: 1 trigger=WARNING, 2+=URGENT → Bell + Teams.

### 11.4 AgentQualityEvaluator

Sampling: 10% das interações (Sprint J1).

### 11.5 AgentHealthAlertService

3 falhas → WARNING, 5 → CRITICAL. Notifica Bell + Teams automático.

---

## 12. Integrações de LLM Disponíveis (Replit)

| Provider | Status | Variáveis |
|----------|--------|-----------|
| Anthropic (Claude) | Ativo — primário | `ANTHROPIC_API_KEY` ou `AI_INTEGRATIONS_ANTHROPIC_API_KEY` + `AI_INTEGRATIONS_ANTHROPIC_BASE_URL` |
| OpenAI | Configurado — fallback | `OPENAI_API_KEY` |
| Google Gemini | Configurado — fallback | `AI_INTEGRATIONS_GEMINI_API_KEY` + `AI_INTEGRATIONS_GEMINI_BASE_URL` |

---

## 13. Decisões Arquiteturais (ADR)

### ADR-LLM-001: Gemini como modelo primário (recruiter_agent_v5)

**Decisão:** Google Gemini Flash para todos os agentes do recruiter_agent_v5.
- (+) Custo ~10x menor que GPT-4
- (+) Context window de 1M tokens
- (-) Pode ser menos preciso em raciocínio complexo

### ADR-LLM-002: Claude como modelo primário (lia-agent-system)

**Decisão:** Claude Sonnet 4.6 como modelo primário com cascade de confiança.
- (+) Melhor raciocínio e tool calling
- (+) Cascade otimiza custo (Haiku para casos simples)
- (+) Fallbacks para OpenAI e Gemini
- (-) Custo maior que Gemini

### ADR-LLM-003: Temperature 0.0 como default de roteamento

**Decisão:** Temperature 0.0 para classificação de intent e compliance. 0.3 para ReAct reasoning.
- (+) Routing determinístico
- (+) Compliance reproduzível
- (-) Respostas de agentes podem parecer "secas" (mitigado pelo prompt)

### ADR-LLM-004: Factory centralizada

**Decisão:** `create_tracked_llm()` (r_a_v5) e `LLMService` (lia) como factories únicas.
- (+) Tracking uniforme de custos
- (+) Configuração centralizada
- (+) Fácil trocar modelo globalmente

### ADR-LLM-005: Python, não Ruby (decisão de stack)

**Arquivo:** `docs/adr/001-python-not-ruby.md` (raiz do repo lia-agent-system)
**Decisão:** Python é a stack definitiva — sem migração planejada.
- Ecossistema de ML/IA (LangGraph, LangChain, PyTorch)
- Python `multiprocessing` usa todos os cores
- Validado pelo especialista externo André

---

## 14. Critérios de Troca de Modelo

| Cenário | Ação | Repositório |
|---------|------|-------------|
| Gemini indisponível | Circuit breaker 3 falhas, cooldown 30s | recruiter_agent_v5 |
| Claude indisponível | Fallback OpenAI → Gemini | lia-agent-system |
| Confiança < threshold | Escala: Haiku → Sonnet → Opus → humano | lia-agent-system |
| Contexto > 1M tokens | Compressão via `compression.py` | recruiter_agent_v5 |
| Custo excessivo | Monitorar tracking, ajustar thresholds cascade | ambos |
| Qualidade insuficiente | `model_override` ou ajustar cascade | ambos |

---

## Referências

| Arquivo | Localização |
|---------|-------------|
| Gemini Config | `recruiter_agent_v5/src/config/gemini_config.py` |
| LLM Factory | `recruiter_agent_v5/src/utils/llm_factory.py` |
| LLMService | `lia-agent-system/app/services/llm.py` |
| Config (lia) | `lia-agent-system/app/core/config.py` |
| Circuit Breaker | `lia-agent-system/app/shared/resilience/circuit_breaker.py` |
| IntentRouter | `lia-agent-system/app/orchestrator/intent_router.py` |
| Drift Service | `lia-agent-system/app/services/model_drift_service.py` |
| ADR 001 | `docs/adr/001-python-not-ruby.md` (raiz do repo lia-agent-system) |
| ADR 002 | `docs/adr/002-graph-vs-react.md` (raiz do repo lia-agent-system) |
