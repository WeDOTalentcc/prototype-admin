# LIA Documentation Library

Biblioteca de documentação do sistema LIA (Learning Intelligence Assistant).

---

## Handoff Documents (índice rápido)

Conjunto canônico para qualquer dev que precise pegar a camada de IA da LIA do zero. Ler nesta ordem:

| Arquivo | Para quê serve |
|---------|----------------|
| [LIA_AI_HANDOFF.md](./LIA_AI_HANDOFF.md) | Handoff técnico das 12 melhorias (FIX 1–12) na camada de IA: governance enforcement, observability, HITL, related_tools. |
| [specs/ai/ADR-019-governance-and-observability.md](./specs/ai/ADR-019-governance-and-observability.md) | ADR-019: decisões arquiteturais sobre governance tags, FairnessGuard enforcement e observability. |
| [CANONICAL_SOURCES_SPEC.md](./CANONICAL_SOURCES_SPEC.md) | Fonte da verdade sobre "onde mora cada responsabilidade" (observability, registries) — arbitragem entre módulos similares. |
| [GLOSSARIO_ACTIONS_TOOLS.md](./GLOSSARIO_ACTIONS_TOOLS.md) | Glossário de 103 tools + 270 DomainActions (auto-gerado — não editar à mão). |
| [DEVELOPER_HANDOFF.md](./DEVELOPER_HANDOFF.md) | Handoff operacional consolidado do ciclo 2026-04 (PARTES A→E + LLM Factory BYOK + proatividade + UX). |
| [`../scripts/generate_tool_action_glossary.py`](../scripts/generate_tool_action_glossary.py) | Script que regenera `GLOSSARIO_ACTIONS_TOOLS.md` a partir do YAML e dos `DomainActions`. Rodar após qualquer mudança nas fontes. |

---

## Documento Principal

O documento central que consolida toda a análise arquitetural, inventário de código, gap analysis, portabilidade e roadmap:

| Arquivo | Descrição |
|---------|-----------|
| [architecture-comparison-analysis.md](../../docs/architecture-comparison-analysis.md) | **Documento unificado** (~4.000 linhas, 26 seções): comparação entre protótipo e produção, inventário de ~650 arquivos executáveis (~226K linhas), gap analysis, mapa de portabilidade, cobertura de testes, features V5, estimativas de esforço e roadmap de adoção. |

> **Nota**: Este documento está em `docs/` na raiz do workspace (fora de `lia-agent-system/`) por conter análise que cobre ambas as arquiteturas (protótipo e produção).

---

## Documentação de Referência

Estes documentos descrevem metodologias, integrações e workflows. Não definem comportamento do sistema (o código faz isso), mas são referência importante para entender **por que** o código foi escrito assim.

### Metodologia WSI e IA

| Arquivo | Descrição |
|---------|-----------|
| `attached_assets/WSI_FLOW_PONTA_A_PONTA_(1)_1776425690186.md` | Fluxo WSI ponta-a-ponta (canônico) — fluxo completo F1–F12 |
| `attached_assets/WSI_METHODOLOGY_COMPLETE_v2.bak_1776458966926.md` | Metodologia WSI v2 (canônico, complementar) — princípios, scoring, gates |
| [AI_SOURCING_METHODOLOGY.md](methodology/AI_SOURCING_METHODOLOGY.md) | Sourcing inteligente: 5 camadas (boolean, Pearch, PG Vector, WRF, scoring) |
| [AI_GOVERNANCE.md](methodology/AI_GOVERNANCE.md) | Governança IA: compliance LGPD, SOX, EU AI Act, anti-viés |

### Prompts

| Arquivo | Descrição |
|---------|-----------|
| [AI_PROMPTS_CATALOG.md](ai-prompts/AI_PROMPTS_CATALOG.md) | Catálogo dos 15 prompts do sistema com versões, variáveis e exemplos |
| [AI_PROMPT_CREATION_GUIDE.md](ai-prompts/AI_PROMPT_CREATION_GUIDE.md) | Guia de criação de novos prompts seguindo convenções |

### Integrações Externas

| Arquivo | Descrição |
|---------|-----------|
| [PEARCH_GUIDE.md](integrations/PEARCH_GUIDE.md) | Integração Pearch AI: créditos, endpoints, busca híbrida, deduplicação |
| [MICROSOFT_INTEGRATION_GUIDE.md](integrations/MICROSOFT_INTEGRATION_GUIDE.md) | Integração Microsoft: Azure Bot, Graph API (calendário), Teams Bot |
| [ATS_INTEGRATION_SPEC.md](integrations/ATS_INTEGRATION_SPEC.md) | Especificação de integração ATS (Gupy, Pandapé, Merge) |

### Workflows Operacionais

| Arquivo | Descrição |
|---------|-----------|
| [WORKFLOW_COMPLETO.md](workflows/WORKFLOW_COMPLETO.md) | Fluxo end-to-end de recrutamento (Fase 0 + 27 etapas em 7 fases) |
| [JOB_FREEZE_WORKFLOW.md](workflows/JOB_FREEZE_WORKFLOW.md) | Workflow de congelamento de vagas |
| [communication-workflow.md](workflows/communication-workflow.md) | Fluxos de comunicação multi-canal |

### Arquitetura e Planejamento

| Arquivo | Descrição |
|---------|-----------|
| [AI_AGENT_AUDIT_REPORT.md](architecture/AI_AGENT_AUDIT_REPORT.md) | Relatório de auditoria dos agentes IA |
| [IMPLEMENTATION_ROADMAP.md](architecture/IMPLEMENTATION_ROADMAP.md) | Roadmap de implementação: fases, milestones, dependências |

---

## Estrutura

```
docs/                                  # (raiz do workspace)
└── architecture-comparison-analysis.md  # Documento principal unificado

lia-agent-system/docs/                 # (este diretório)
├── README.md                          # Este arquivo
├── ai-prompts/                        # Prompts (2 arquivos)
├── methodology/                       # Metodologias e governança (2 arquivos)
│   └── wsi/                           # Metodologia WSI (2 arquivos)
├── architecture/                      # Arquitetura e planejamento (2 arquivos)
├── integrations/                      # Integrações externas (3 arquivos)
└── workflows/                         # Fluxos de recrutamento (3 arquivos)
```

**Total**: 15 documentos (1 na raiz do workspace + 14 em subpastas aqui)
