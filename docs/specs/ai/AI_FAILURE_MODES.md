# AI Failure Modes — WeDOTalent / Plataforma LIA

> Última atualização: 2026-03-26
> Fonte: leitura direta do código — `recruiter_agent_v5` (handlers de erro, circuit breaker, fallbacks)
> **SPEC-DRIVEN DEVELOPMENT** — catálogo de modos de falha e comportamentos de recuperação.

---

## 1. Visão Geral

O sistema possui 4 camadas de proteção contra falhas:

```
Camada 1: Circuit Breaker (previne cascata de falhas)
Camada 2: Error handling por nó do graph (cada agente trata seus erros)
Camada 3: Conditional edges (graph redireciona fluxo em caso de erro)
Camada 4: Answer Formatter (formata erros amigáveis para o usuário)
```

---

## 2. Modos de Falha por Componente

### 2.1 LLM (Google Gemini)

| Falha | Detecção | Comportamento | Mensagem ao Usuário |
|-------|----------|---------------|---------------------|
| API timeout | Exception timeout | Circuit breaker conta falha; retry após delay | "Estou com dificuldade para processar. Tente novamente em alguns segundos." |
| Rate limit (429) | HTTP 429 | Exponential backoff; circuit breaker após 3 falhas | "Sistema temporariamente sobrecarregado. Aguarde um momento." |
| Resposta malformada | JSON parse error | Retry 1x; se falhar, retorna erro ao formatter | "Não consegui processar a resposta. Tente reformular a pergunta." |
| Context too large | Token limit exceeded | Compressão via `compression.py` (AutonomousDomain) | Transparente — comprime e re-tenta |
| API key inválida | 401/403 | Falha imediata, log critical | "Erro de configuração do sistema. Contate o administrador." |
| Modelo indisponível | 503 | Circuit breaker abre por 30s | "Serviço de IA temporariamente indisponível." |

### 2.2 ATS API (Rails)

| Falha | Detecção | Comportamento | Mensagem ao Usuário |
|-------|----------|---------------|---------------------|
| API indisponível | Connection refused | Circuit breaker; retry | "Não consigo acessar os dados no momento. Tente novamente." |
| JWT expirado | 401 | Re-login automático via ATSAPIClient | Transparente — obtém novo token |
| Recurso não encontrado | 404 | Retorna NOT_FOUND via formatter | "Não encontrei [recurso] com esses critérios." |
| Validação falhou | 422 | Extrai mensagens de erro, retorna ao usuário | "Não foi possível: [detalhes da validação]" |
| Permissão negada | 403 | Retorna erro de permissão | "Você não tem permissão para esta ação." |
| Timeout | Request timeout | Retry com backoff | "A busca demorou mais que o esperado. Tente com filtros mais específicos." |

### 2.3 RabbitMQ

| Falha | Detecção | Comportamento |
|-------|----------|---------------|
| Connection lost | `pika.exceptions.ConnectionClosed` | Reconnect automático no `BaseDispatcher` |
| Queue full | Queue length exceeded | Mensagem rejeitada; retry com delay |
| Consumer crash | Worker exception | Message nacked; requeue automático |

### 2.4 Intent Analysis

| Falha | Detecção | Comportamento |
|-------|----------|---------------|
| Intent não identificado | Confidence < threshold | Pede esclarecimento ao usuário |
| Query incompreensível | Parse error | Retorna `needs_clarification: true` |
| Entidade ambígua | Múltiplas entidades possíveis | Retorna `DISAMBIGUATION` response |

### 2.5 API Planning

| Falha | Detecção | Comportamento |
|-------|----------|---------------|
| API não encontrada | API name não existe | Aborta plan; formata erro |
| Plano inválido | PlanStep incompleto | Retry planejamento 1x |
| Dependência circular | Step references loop | Detecta e aborta |

### 2.6 Plan Validation

| Falha | Detecção | Comportamento |
|-------|----------|---------------|
| Dados insuficientes | Resultado vazio ou incompleto | **Replan** — volta ao api_planner (máx 1x) |
| Dados incorretos | Validação falha | **Abort** — vai ao answer_formatter com erro |
| Loop de replanejamento | Re-plan count > 1 | Força abort |

---

## 3. Circuit Breaker

Implementado em `src/services/circuit_breaker.py`:

### 3.1 Estados

```
CLOSED ──── falha ──── OPEN ──── cooldown expira ──── HALF-OPEN
   ▲                                                      │
   │                                                      │
   └──────────── sucesso ─────────────────────────────────┘
```

### 3.2 Configuração

| Parâmetro | Default | Descrição |
|-----------|---------|-----------|
| `failure_threshold` | 3 | Falhas consecutivas para abrir |
| `cooldown_seconds` | 30 | Tempo em estado aberto |
| `retry_delay` | 1.0s | Delay entre retries |

### 3.3 Exceção

`CircuitBreakerOpenError` — lançada quando o circuito está aberto. Cada domínio captura e retorna mensagem amigável.

---

## 4. Evaluation Domain — Segurança

### 4.1 Prompt Injection Protection

`src/domains/evaluation/security.py`:

| Proteção | Descrição |
|----------|-----------|
| `safe_process_input()` | Sanitiza input do candidato, detecta padrões de injeção |
| `create_safe_context()` | Cria contexto sanitizado para o LLM |
| Pattern detection | Detecta tentativas de override do system prompt |

### 4.2 Comportamento em Caso de Injeção

```python
if is_injection:
    return {
        "classification": InputClassification(
            intent="off_topic",
            confidence=1.0,
            summary="Conteúdo inválido detectado",
        ),
        "errors": ["security_block:{pattern}"],
    }
```

---

## 5. Fairness Guard — Falhas Éticas

### 5.1 Filtros Bloqueados

Se o recrutador tenta filtrar por critérios discriminatórios:

```
Input: "Busque apenas candidatas mulheres"
→ 🚫 O filtro 'gender' não é permitido por políticas de diversidade e inclusão.
```

### 5.2 Filtros Condicionais

```
Input: "Busque candidatos PCD" (vaga sem disabilities=true)
→ 🚫 Filtro PCD só é permitido quando a vaga tem o campo 'disabilities=true'.
```

---

## 6. Fluxo de Erro no Graph

```
[Qualquer Nó] ──── error ──── state.error = "mensagem"
                                    │
                                    ▼
                          [_should_continue()]
                                    │
                              returns "end"
                                    │
                                    ▼
                                   END
                          (se final_answer vazio,
                           formatter gera erro genérico)
```

### 6.1 Error State Propagation

Cada nó verifica `state.get("error")` no início:
- Se existir erro e já houver `final_answer`, retorna END
- Se existir erro sem `final_answer`, propaga para o próximo nó tratar

---

## 7. Modos de Falha do Autonomous Agent

| Falha | Comportamento |
|-------|---------------|
| Tool retorna erro | ReAct loop tenta tool alternativa |
| Contexto muito grande | `compression.py` comprime conversa antiga |
| Playbook YAML inválido | Pula playbook, executa ad-hoc |
| Tool não encontrada | Informa ao recrutador que a ação não está disponível |
| Loop infinito de ReAct | Limite de iterações (configurable), aborta com resumo parcial |

---

## 8. Logging e Observabilidade

### 8.1 Log Levels

| Level | Uso |
|-------|-----|
| `DEBUG` | Detalhes de execução, params de API |
| `INFO` | Fluxo normal, resultados de ações |
| `WARNING` | Fallbacks ativados, circuit breaker, retries |
| `ERROR` | Falhas de API, LLM, parse |
| `CRITICAL` | API key inválida, configuração quebrada |

### 8.2 LangSmith Integration

Quando `LANGCHAIN_TRACING_V2=true`:
- Todas as chamadas LLM são rastreadas
- Traces com: input, output, tokens, latência
- Projeto: `recruiter-agent-v5`

### 8.3 LLM Usage Tracking

`LLMUsageCallbackHandler` registra:
- `service_name` — qual domínio/agente
- `operation` — tipo de operação
- Tokens de entrada/saída
- Latência

---

## 9. Checklist de Resiliência

| Item | Status |
|------|--------|
| Circuit breaker para LLM | Implementado |
| Circuit breaker para ATS API | Implementado |
| Retry com backoff | Implementado (via circuit breaker) |
| Re-planejamento automático | Implementado (PlanValidator) |
| Sanitização de input | Implementado (EvaluationDomain) |
| Fairness guard | Implementado (JobsDomain) |
| Compressão de contexto | Implementado (AutonomousDomain) |
| JWT auto-renewal | Implementado (ATSAPIClient) |
| RabbitMQ reconnect | Implementado (BaseDispatcher) |
| Error formatting amigável | Implementado (AnswerFormatter) |
| Fallback de modelo LLM | Não implementado (single model) |
| Dead letter queue | Não verificado |
| Health check do agente | Não implementado |

---

## Referências

| Arquivo | Localização |
|---------|-------------|
| Circuit Breaker | `recruiter_agent_v5/src/services/circuit_breaker.py` |
| Evaluation Security | `recruiter_agent_v5/src/domains/evaluation/security.py` |
| Fairness Guard | `recruiter_agent_v5/src/domains/jobs/fairness.py` |
| Workflow Graph | `recruiter_agent_v5/src/workflow/graph.py` |
| Autonomous Compression | `recruiter_agent_v5/src/domains/autonomous/compression.py` |
| Base Dispatcher | `recruiter_agent_v5/src/domains/base_dispatcher.py` |
| LLM Tracking | `recruiter_agent_v5/src/services/llm_tracking_service.py` |
