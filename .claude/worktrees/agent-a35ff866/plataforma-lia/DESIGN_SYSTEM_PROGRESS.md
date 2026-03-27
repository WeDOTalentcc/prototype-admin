# Design System LIA v4.1 - Progresso (React + Tailwind)

## STATUS
- Projeto: WeDO Talent (Replit)
- Stack: React + Next.js + Tailwind CSS
- Data Início: 2026-02-09 (área de Jobs) / 2026-02-10 (projeto completo)
- Fase Atual: 8 - Validação Final
- % Completo: ~95% (490+/514 arquivos)

## ESPECIFICAÇÕES CRÍTICAS
- Tipografia: Open Sans (85%) + Inter (10% APENAS métricas numéricas) + Source Serif 4 (5% sidebar APENAS)
- Espaçamento: Base 4px
- Cores: 90% gray + 10% accent (cyan #60BED1 APENAS para LIA/IA icons: Brain, Sparkles, Bot)
- Cards: rounded-xl (NUNCA rounded-md para cards)
- Botões Primary: bg-gray-900 (preto, NUNCA cyan)
- Focus ring: ring-gray-900/20 (grayscale, NUNCA cyan)
- Dark mode: obrigatório em todos componentes
- Overlay modais: bg-gray-900/50 dark:bg-gray-950/70

## FASES - ESCOPO COMPLETO DO PROJETO
- [x] Fase 0: Preparação (inventário) ← COMPLETA
- [x] Fase 1: Setup Base (fontes, tokens, Tailwind config) ← COMPLETA
- [x] Fase 2: Botões ← COMPLETA (2026-02-10)
- [x] Fase 3: Inputs e Forms ← COMPLETA (2026-02-10)
- [x] Fase 4: Cards e Containers ← COMPLETA (2026-02-10)
- [x] Fase 5: Navegação e Sidebar ← COMPLETA (2026-02-10)
- [x] Fase 6: Cores Cyan/60BED1 ← COMPLETA (2026-02-10)
- [x] Fase 7: Cores wedo-orange/wedo-cyan ← COMPLETA (2026-02-10)
- [ ] Fase 8: Validação Final ← EM PROGRESSO

## PROGRESSO ANTERIOR (Área de Jobs - 88 arquivos)
Completado em 2026-02-09, todas as fases aplicadas na área de Jobs:
- jobs-page.tsx, job-kanban-page.tsx, edit-job-modal.tsx, quick-actions-modals.tsx
- job-compare-modal.tsx, jobs2-page.tsx, expanded-chat-modal.tsx
- + 81 outros componentes relacionados a Jobs
- Resultado: 0 violações na área de Jobs

## INVENTÁRIO COMPLETO DO PROJETO

### Totais
- Componentes React (.jsx/.tsx): 514 arquivos
- Arquivos CSS: 6
- Tailwind config: tailwind.config.ts
- Design tokens: src/lib/design-tokens.ts (v4.0, 635 linhas)
- Design tokens CSS: src/styles/design-tokens.css (790 linhas, PRECISA ATUALIZAR - referencia #C74446 antigo)

### Estrutura de Pastas Principal
```
src/
├── app/                          # Pages (Next.js App Router)
│   ├── admin/                    # Admin pages (80+ files)
│   │   ├── clientes/[clientId]/  # Client management
│   │   ├── compliance/           # Compliance module
│   │   ├── configuracoes/        # Settings
│   │   └── ...
│   ├── api/                      # API routes (proxy)
│   └── ...                       # Other pages
├── components/                   # Shared components
│   ├── ui/                       # UI primitives (67 files)
│   ├── modals/                   # Modal components (32 files)
│   ├── search/                   # Search components (35 files)
│   ├── pages/                    # Page-level components (25 files)
│   ├── settings/                 # Settings components (22 files)
│   ├── wsi/                      # WSI components (9 files)
│   ├── kanban/                   # Kanban components
│   ├── job-wizard/               # Job wizard stages
│   ├── expanded-chat/            # Expanded chat components
│   ├── chat/                     # Chat components
│   ├── notifications/            # Notification components
│   ├── admin/                    # Admin-specific components
│   └── ...
├── contexts/                     # React contexts
├── hooks/                        # Custom hooks
├── lib/                          # Utilities & design tokens
├── services/                     # API services
├── styles/                       # CSS & design tokens
├── types/                        # TypeScript types
└── utils/                        # Utility functions
```

### Fontes Configuradas
- Open Sans: ✅ via next/font/google + @import globals.css
- Inter: ✅ via next/font/google + @import globals.css
- Source Serif 4: ✅ via next/font/google + @import globals.css
- Tailwind aliases: font-brand (Open Sans), font-data (Inter), font-sidebar (Source Serif 4)

### Padrões Atuais Identificados

**Arredondamento (PROBLEMA PRINCIPAL):**
- rounded-lg: 2.559 ocorrências (dominante - muitos deveriam ser rounded-xl)
- rounded-xl: 854 ocorrências (deveria aumentar)
- rounded-md: 336 ocorrências (deveria diminuir)
- rounded-sm: 35 ocorrências

**Uso de Cyan #60BED1 (TOP 10 arquivos com mais violações):**
| Arquivo | Referências Cyan |
|---------|-----------------|
| smart-search-input.tsx | 124 |
| expanded-chat-modal.tsx | 111 |
| candidates-page.tsx | 78 |
| onboarding-wizard.tsx | 77 |
| job-insights-modal.tsx | 50 |
| jobs-page.tsx | 39 (parcialmente corrigido) |
| CompetenciesStage.tsx | 36 |
| candidate-preview.tsx | 36 |
| triagem-details-modal.tsx | 33 |
| dashboards-page.tsx | 31 |

**Uso de Fontes Inline (TOP 10 arquivos):**
| Arquivo | Font Declarations |
|---------|------------------|
| jobs-page.tsx | 145 |
| candidates-page.tsx | 131 |
| expanded-chat-modal.tsx | 99 |
| onboarding-wizard.tsx | 81 |
| triagem-details-modal.tsx | 76 |
| smart-search-input.tsx | 66 |
| job-kanban-page.tsx | 59 |
| rubric-evaluation-modal.tsx | 55 |
| JDEvaluationPanel.tsx | 41 |
| settings-page.tsx | 25 |

**Inter font total references:** 496 (muitas possivelmente indevidas - verificar se são métricas numéricas)

## PRIORIZAÇÃO PARA PADRONIZAÇÃO
### Prioridade Alta (arquivos grandes com muitas violações):
1. smart-search-input.tsx (124 cyan refs, 66 font refs)
2. expanded-chat-modal.tsx (111 cyan refs, 99 font refs)
3. candidates-page.tsx (78 cyan refs, 131 font refs)
4. onboarding-wizard.tsx (77 cyan refs, 81 font refs)
5. job-insights-modal.tsx (50 cyan refs)
6. triagem-details-modal.tsx (33 cyan refs, 76 font refs)

### Prioridade Média:
7-20. Remaining page/modal components with 10+ violations

### Prioridade Baixa:
- UI primitives (may be intentional)
- Admin pages (lower traffic)
- Storybook files

## LOG
- 2026-02-09: Fases 0-8 completas para área de Jobs (88 arquivos)
- 2026-02-10: Padronização do modal "Roteiro WSI de Triagem" (16 seções corrigidas)
- 2026-02-10: Fase 0 refeita com escopo COMPLETO do projeto (514 arquivos inventariados)
- 2026-02-10: Fases 1-3 completas (Setup Base, Botões, Inputs/Forms)
- 2026-02-10: Fase 4 completa - 2.557 rounded-lg → rounded-xl em 350 arquivos
- 2026-02-10: Fase 5 completa - Source Serif removido de 50+ arquivos, nav/sidebar grayscale
- 2026-02-10: Fase 6 completa - bg-[#60BED1]/bg-cyan/text-cyan → grayscale (320+ instâncias em 80+ arquivos). Cyan preservado APENAS em Brain/Sparkles/Bot icons (10 instâncias)
- 2026-02-10: Fase 7 completa - wedo-orange (67 instâncias) e wedo-cyan (92 instâncias) → grayscale em 60+ arquivos. Design tokens CSS atualizados.

## ESTADO ATUAL (pós Fase 7)
### Violações Restantes:
- wedo-orange: 0 (em .tsx)
- wedo-cyan: 0 (em .tsx)
- bg-[#60BED1]: 0
- bg-cyan (não-LIA): 0
- text-cyan: 10 (TODOS em Brain/Bot icons - CORRETO)
- Erros LSP pré-existentes: chat-page.tsx (38 erros de tipagem, não relacionados a cores)
