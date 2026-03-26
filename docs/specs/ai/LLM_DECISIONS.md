# LLM Decisions — WeDOTalent / Plataforma LIA

> Última atualização: 2026-03-26
> Fonte: leitura direta do código — `recruiter_agent_v5` + `lia-agent-system`
> **SPEC-DRIVEN DEVELOPMENT** — decisões de modelo, configuração e critérios de seleção.

---

## 1. Modelo Primário

| Campo | Valor |
|-------|-------|
| **Provider** | Google Gemini |
| **Modelo Default** | `gemini-2.5-flash` |
| **Fallback** | `gemini-1.5-flash-latest` (em gemini_config.py) |
| **Biblioteca** | `langchain-google-genai` (`ChatGoogleGenerativeAI`) |
| **API Key** | `GEMINI_API_KEY` (env var obrigatória) |

### 1.1 Por que Gemini

- **Custo**: Gemini Flash tem custo significativamente menor que GPT-4 e Claude
- **Velocidade**: Flash models otimizados para latência baixa
- **Português**: Bom suporte a português brasileiro
- **LangChain**: Integração nativa via `langchain-google-genai`
- **Context window**: 1M tokens (permite contextos longos sem chunking)

---

## 2. Configurações por Domínio/Agente

| Agente/Domínio | Temperature | Modelo | Motivo |
|----------------|-------------|--------|--------|
| `IntentAnalyzerAgent` | 0.0 | default (gemini-2.5-flash) | Determinismo na classificação de intent |
| `APIPlannerAgent` | 0.0 | default | Planos de execução devem ser reproduzíveis |
| `PlanValidatorAgent` | 0.0 | default | Validação determinística |
| `AnswerFormatterAgent` | 0.0 | default | Formatação consistente |
| `AppliesDomain` | 0.0 | default | Ações sobre candidaturas devem ser precisas |
| `JobsDomain` | 0.0 | default | CRUD e analytics precisos |
| `InsightsDomain` | 0.0 | default | Análises baseadas em dados concretos |
| `MessagingDomain` | 0.0 | default | Comunicação precisa, sem criatividade indesejada |
| `EvaluationDomain` (nodes) | **0.2** | default | Leve variação para avaliação mais natural |
| `AutonomousDomain` | 0.0 | default | Agente universal precisa de determinismo |

### 2.1 Regra Geral

**Temperature 0.0 é o padrão.** Apenas o `EvaluationDomain` usa 0.2 porque avaliação de candidatos se beneficia de leve variação para respostas mais naturais ao candidato.

---

## 3. Factory Centralizada

Toda criação de LLM passa pelo `create_tracked_llm()` em `src/utils/llm_factory.py`:

```python
create_tracked_llm(
    temperature=0.0,
    service_name="NomeDoDominio",
    operation="chat|intent",
    model_override=None,      # para usar modelo diferente do default
    max_output_tokens=None,    # limite de tokens de saída
    extra_callbacks=None,      # callbacks adicionais
)
```

### 3.1 Tracking

Cada chamada LLM é rastreada via `LLMUsageCallbackHandler`:
- `service_name` — identifica qual domínio/agente fez a chamada
- `operation` — tipo de operação (chat, intent, evaluation)
- Métricas: tokens de entrada/saída, latência, custo estimado

Configuração via `LLMTrackingConfig.from_env()` (ativável por env var).

---

## 4. RAG (Retrieval-Augmented Generation)

| Campo | Valor |
|-------|-------|
| **Serviço** | `RAGService` (`src/services/rag_service.py`) |
| **Uso** | IntentAnalyzer e APIPlanner consultam documentação de APIs |
| **Fonte** | Documentação YAML em `documentation/*.yml` (~50 arquivos) |
| **Embedding** | Embeddings locais ou via API |

### 4.1 Documentação de Tools (YAML)

Cada ferramenta disponível tem um arquivo YAML em `documentation/`:
- `candidates_search.yml`, `jobs_create.yml`, `applies_update.yml`, etc.
- Define: endpoint, parâmetros, formato de resposta, exemplos
- Total: ~50 ferramentas documentadas

---

## 5. Critérios de Troca de Modelo

| Cenário | Ação |
|---------|------|
| Gemini indisponível | Circuit breaker abre após 3 falhas, cooldown 30s |
| Contexto > 1M tokens | Compressão via `autonomous/compression.py` |
| Avaliação precisa mais nuance | `temperature=0.2` (já implementado no EvaluationDomain) |
| Custo excessivo | Monitorar via LLM tracking, considerar Gemini Flash-Lite |
| Qualidade insuficiente em PT-BR | Considerar `model_override` para Gemini Pro |

### 5.1 Circuit Breaker para LLM

Implementado em `src/services/circuit_breaker.py`:

| Parâmetro | Valor |
|-----------|-------|
| Threshold | 3 falhas consecutivas |
| Cooldown | 30 segundos |
| Retry delay | 1 segundo |

---

## 6. Custos e Limites

### 6.1 Gemini Flash Pricing (referência)

| Métrica | Valor |
|---------|-------|
| Input (até 128K tokens) | $0.075 / 1M tokens |
| Input (> 128K tokens) | $0.15 / 1M tokens |
| Output | $0.30 / 1M tokens |
| Context window | 1M tokens |
| RPM (requests/min) | 1000 (tier padrão) |

### 6.2 Estimativa de Uso por Query

| Etapa | Tokens estimados (input) | Tokens estimados (output) |
|-------|-------------------------|--------------------------|
| Intent Analysis | ~2K | ~500 |
| API Planning | ~5K (com RAG docs) | ~1K |
| Plan Validation | ~3K | ~300 |
| Answer Formatting | ~5K (com dados) | ~1K |
| **Total por query** | **~15K** | **~2.8K** |

### 6.3 Monitoramento

- `LLMUsageCallbackHandler` rastreia todas as chamadas
- `LLMTrackingConfig` configurável via env vars
- Logs estruturados com service_name, operation, duração

---

## 7. Modelos no lia-agent-system (Replit)

| Domínio | Modelo | Temperature | Uso |
|---------|--------|-------------|-----|
| WSI Screening | Gemini | 0.0 | Triagem WSI — determinismo obrigatório |
| Chat Geral | Gemini / Claude / OpenAI | 0.0 | Configurable via env |
| Voice Processing | Gemini | 0.0 | Transcrição e análise de voz |

### 7.1 Integrações Disponíveis (Replit)

| Provider | Status | Env Var |
|----------|--------|---------|
| Google Gemini | Ativo | `GEMINI_API_KEY` |
| Anthropic Claude | Configurado | `ANTHROPIC_API_KEY` |
| OpenAI | Configurado | `OPENAI_API_KEY` |

---

## 8. Decisões Arquiteturais (ADR)

### ADR-LLM-001: Gemini como modelo primário

**Contexto:** Precisávamos de um LLM com bom suporte a português, custo baixo, e context window grande.

**Decisão:** Google Gemini Flash como modelo primário para todos os agentes.

**Consequências:**
- (+) Custo ~10x menor que GPT-4
- (+) Context window de 1M tokens
- (+) Bom português
- (-) Pode ser menos preciso que GPT-4 em raciocínio complexo
- (-) Vendor lock-in com Google

### ADR-LLM-002: Temperature 0.0 como default

**Contexto:** Agentes de recrutamento precisam de respostas consistentes e reproduzíveis.

**Decisão:** Temperature 0.0 para todos os agentes, exceto EvaluationDomain (0.2).

**Consequências:**
- (+) Respostas determinísticas
- (+) Facilita debugging e testes
- (-) Respostas podem parecer "secas" (mitigado pelo prompt de formatação)

### ADR-LLM-003: Factory centralizada

**Contexto:** Múltiplos domínios criam instâncias de LLM independentemente.

**Decisão:** `create_tracked_llm()` como factory única com tracking embutido.

**Consequências:**
- (+) Tracking uniforme de custos
- (+) Configuração centralizada
- (+) Fácil trocar modelo globalmente

---

## Referências

| Arquivo | Localização |
|---------|-------------|
| Gemini Config | `recruiter_agent_v5/src/config/gemini_config.py` |
| Settings | `recruiter_agent_v5/src/config/settings.py` |
| LLM Factory | `recruiter_agent_v5/src/utils/llm_factory.py` |
| LLM Tracking | `recruiter_agent_v5/src/config/llm_tracking_config.py` |
| Circuit Breaker | `recruiter_agent_v5/src/services/circuit_breaker.py` |
| RAG Service | `recruiter_agent_v5/src/services/rag_service.py` |
| Evaluation Config | `recruiter_agent_v5/src/config/evaluation_config.py` |
