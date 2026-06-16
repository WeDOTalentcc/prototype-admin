# ADR-023 — Subagent vs Tool Decision Criteria

**Status:** Accepted
**Date:** 2026-05-02
**Related:**
- ADR-020 (LangGraph Graph Encapsulation Pattern)
- ADR-022 (Tool Registry Taxonomy)
- ADR-024 (Four-Registry Architecture)
- `app/agents/` (subagents)
- `app/tools/registry.py` (tools)

---

## Context

Auditoria de 2026-05 encontrou inconsistências no uso de subagentes versus tools para operações de domínio. Exemplos:

- `pipeline_stage_tool` — executa múltiplas chamadas LLM para mover candidato no pipeline → modelado como **tool**, mas deveria ser subagente.
- `wsi_interview_agent` — fluxo completo de triagem com estado próprio → modelado como **subagente** (correto).
- `format_cv_tool` — chama LLM uma vez, retorna resultado → modelado como **tool** (correto).
- `calibration_runner` — loop iterativo com memória de rounds anteriores → modelado como **tool**, mas deveria ser subagente.

Sem critérios documentados, cada desenvolvedor tomava a decisão por intuição, resultando em tools com estado implícito (anti-padrão) e subagentes para operações atômicas (overhead desnecessário).

## Decision

### Use Subagente quando:

1. **Múltiplas chamadas LLM**: a operação requer duas ou mais chamadas ao LLM (seja em sequência, em loop, ou com ramificação condicional).
2. **Estado ou memória próprios**: a operação mantém contexto entre steps (histórico de rounds, iterações de calibração, etapas de triagem).
3. **Capacidade standalone de produto**: a operação é uma funcionalidade autônoma da plataforma com ciclo de vida próprio (WSI Interview, Hiring Pipeline Stage, Calibration Session).

### Use Tool quando:

1. **Chamada única e atômica**: a operação é uma função determinística ou uma única chamada LLM → resultado.
2. **API externa ou repositório**: a operação delega para um sistema externo (Rails API, banco de dados, email) sem lógica de decisão adicional.
3. **O caller precisa inspecionar o resultado antes de continuar**: a operação retorna dados que o agente pai usa para decidir o próximo passo — ferramentas são transparentes, subagentes são opacos.

### Regra heurística

> **Se precisa de um system prompt próprio, é um subagente. Se só retorna dados, é uma tool.**

### Tabela de decisão

| Pergunta | Sim → | Não → |
|----------|-------|-------|
| Precisa de system prompt próprio? | Subagente | Continuar |
| Faz mais de uma chamada LLM? | Subagente | Continuar |
| Mantém estado entre steps? | Subagente | Continuar |
| Retorna dado para o caller decidir? | Tool | Subagente |

## Consequences

**Positivo:**
- Elimina tools com estado implícito (anti-padrão que quebra rastreabilidade e HITL).
- Subagentes excessivos são reduzidos → menor overhead de orquestração.
- Critério de revisão de código objetivo: PR que cria tool com loop interno é P1.

**Negativo:**
- Alguns casos são genuinamente ambíguos (ex: uma ferramenta que faz retry com backoff). Nesses casos, a regra heurística do system prompt desempata.
- Migrar tools existentes que deveriam ser subagentes exige refactoring com testes de regressão. Aceito como dívida técnica a ser endereçada por domínio.

## Não-decisões

- Se subagentes devem ser expostos diretamente via API ou sempre intermediados pelo orchestrator principal. Decisão atual: sempre via orchestrator; pode ser revisada para Agent Studio.
