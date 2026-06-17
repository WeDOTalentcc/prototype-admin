# LLM Decisions — Plataforma LIA

## Hierarquia de Providers (Atualizado: Task #132, Abril 2026)

### Provider Padrão: Gemini 2.5 Flash

**Justificativa:** Gemini 2.5 Flash é o LLM mais custo-efetivo disponível, com performance
comparável ao Claude Haiku em tarefas de roteamento e extração estruturada. A mudança reduz
custos operacionais significativamente enquanto mantém resiliência via fallback chain.

### Fallback Chain

```
Gemini 2.5 Flash → Claude Sonnet → OpenAI GPT-4o
```

| Posição | Provider       | Modelo            | Uso                              |
|---------|---------------|-------------------|----------------------------------|
| 1 (Primary) | Gemini     | gemini-2.5-flash  | Default — todas as chamadas      |
| 2 (Fallback 1) | Claude  | claude-sonnet-4-6 | Fallback se Gemini falhar        |
| 3 (Fallback 2) | OpenAI  | gpt-4o            | Último recurso                   |

### Configuração

```
LLM_DEFAULT_PROVIDER=gemini
FALLBACK_ORDER=["gemini", "claude", "openai"]
```

---

## LLM Cascade — Escada de Custo

O `LLMCascadeRouter` implementa uma escada de custo para roteamento de intenções:

```
Tier 1: Gemini Flash (LLM_FAST_MODEL)    → confiança >= 0.80 → retorna
Tier 2: Claude Sonnet (LLM_PRIMARY_MODEL) → confiança >= 0.70 → retorna
Tier 3: Claude Opus (LLM_POWERFUL_MODEL)  → somente se absolutamente necessário
```

**Mudança (Task #132):** O Tier 1 era `claude-haiku-4-5`, substituído por `gemini-2.5-flash`.
Gemini Flash tem latência e custo similares ao Haiku, com suporte nativo a PT-BR.

---

## Exceções — Providers Fixos Justificados

| Serviço                 | Provider Fixo | Justificativa                                       |
|------------------------|---------------|-----------------------------------------------------|
| OpenMic.ai (screening de voz) | OpenAI   | Integração nativa com OpenAI — tratado em task separada |
| WSI deep analysis       | Claude Sonnet | Análise semântica profunda — mantido para qualidade |
| generate_with_tools (tool loop) | Gemini | Suporte a function_calling nativo                   |

---

## Decisões Anteriores

### Task #125 — ProviderContainer e TenantProviderRegistry
- Introdução de DI por tenant, com configuração via YAML (tool_permissions.yaml)
- `LLM_DEFAULT_PROVIDER` já defaultava para "gemini" em `get_default()` e no container

### Task #132 — Gemini como Padrão (esta task)
- `FALLBACK_ORDER` atualizado: `["gemini", "claude", "openai"]` (era `["claude", "gemini", "openai"]`)
- `LLM_FAST_MODEL` atualizado: `gemini-2.5-flash` (era `claude-haiku-4-5`)
- `LLM_ROUTER_MODEL` atualizado: `gemini-2.5-flash` (era `claude-haiku-4-5-20251001`)
- `LLM_DEFAULT_PROVIDER` explicitado no `.env` e adicionado como campo em `LLMSettings`
- Serviços auditados e chamadas explícitas `provider="claude"` substituídas pelo padrão
- Cascata de roteamento usa Gemini Flash no Tier 1

---

## Qualidade PT-BR

Gemini 2.5 Flash demonstra qualidade equivalente ao Claude Haiku em:
- Classificação de intenções em PT-BR
- Extração estruturada de JSON
- Geração de resposta contextual a recrutadores

Para tarefas que exijam raciocínio profundo (scoring WSI, análise semântica), Claude Sonnet
permanece como fallback confiável.
