# LIA Documentation Library

Biblioteca de documentação do sistema LIA (Learning Intelligence Assistant).

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
| [AI_WSI_EVALUATION_GUIDE.md](methodology/wsi/AI_WSI_EVALUATION_GUIDE.md) | Guia técnico WSI: especificação, schemas, scoring (rubricas 4 níveis), processamento LLM, guardrails |
| [AI_WSI_INTERVIEW_TEMPLATES.md](methodology/wsi/AI_WSI_INTERVIEW_TEMPLATES.md) | Templates de entrevista: CBI/Bloom/Dreyfus/Big Five, calibração, pareceres |
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
