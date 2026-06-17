# ADR 001 — Manter Python/FastAPI (não migrar para Ruby on Rails)

**Data:** 04/março/2026
**Status:** Aceito
**Decisores:** André (arquiteto sênior), Victor (lead dev)

---

## Contexto

O roadmap original previa migração do backend para Ruby on Rails. Análise arquitetural aprofundada (março/2026) reavaliou essa decisão.

## Decisão

**Manter Python/FastAPI como stack de backend.** Cancelar migração para Ruby on Rails.

## Justificativas

1. **Ecossistema de IA**: LangGraph, LangChain, Anthropic SDK, Deepgram — todos têm suporte nativo e maduro em Python. Ruby não tem equivalentes de qualidade comparável.
2. **Custo de migração vs. benefício**: O codebase tem 230+ services, 95 models, 362 endpoints e 28 agentes. Migrar para Rails exigiria reescrever toda a camada de IA sem ganho funcional.
3. **pgvector e SQLAlchemy async**: A stack atual com PostgreSQL + pgvector + SQLAlchemy 2.0 async é performática e bem integrada. ActiveRecord não tem suporte nativo a pgvector com a mesma maturidade.
4. **Time**: A equipe tem expertise consolidada em Python/FastAPI. Migração criaria risco operacional significativo.
5. **Compliance**: Implementações de FairnessGuard, Bias Audit, LGPD, BCB 498 são Python-native e auditadas.

## Consequências

- Remover todas as referências a "migração para Rails" de CLAUDE.md e documentação
- Focar melhorias na arquitetura Python existente (ver plano de fases 0-7)
- Padrão de portabilidade de código muda de "preparar para Rails" para "manter camadas separadas e services stateless" (boas práticas independentes de linguagem)

## Alternativas Consideradas

- **Migração gradual (strangler fig)**: descartado — complexidade de dois sistemas em paralelo com dados de candidatos e compliance
- **Novo serviço em Rails para parte do sistema**: descartado — aumenta complexidade operacional sem resolver nenhum problema atual
