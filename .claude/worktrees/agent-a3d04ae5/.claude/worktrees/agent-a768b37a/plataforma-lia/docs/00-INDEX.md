# Documentação Técnica - Plataforma LIA

**Última Atualização:** 30 Janeiro 2026  
**Versão da documentação:** 1.2

Bem-vindo à documentação técnica da **Plataforma LIA** - Sistema de Recrutamento e Seleção com IA.

---

## 📂 Estrutura de Pastas

```
plataforma-lia/docs/
├── 00-INDEX.md              # Este arquivo (índice técnico)
├── 01-arquitetura-sistema.md
├── 02-design-system.md
├── 03-features-implementadas.md
├── 04-guia-desenvolvimento.md
├── 05-changelog.md
├── 06-lia-backend-integration.md
├── README.md                 # Overview
├── design-system/            # Design e UI
│   ├── LIA-DESIGN-SYSTEM.md
│   ├── design-system-v3-pendencias.md
│   └── modal-design-standards.md
├── comercial/                # Materiais de vendas
│   ├── Guia_Apresentacoes_LIA.md
│   ├── LIA_Apresentacao_Comercial_Completa.md
│   ├── LIA_Apresentacao_Institucional_Completa.md
│   ├── LIA_Executive_Summary.md
│   ├── LIA_Pitch_Vendas.md
│   ├── LIA_Revoluciona_Recrutamento_Moderno.pptx.md
│   └── onboarding-roteiro.md
├── auditorias/               # QA e diagnósticos
│   ├── auditoria-gestao-vagas.md
│   ├── auditoria-talent-funnel.md
│   ├── DIAGNOSTICO_KANBAN_VS_TABELA.md
│   └── FEATURES_REMOVIDAS_FILTROS_AVANCADOS.md
├── planejamento/             # Roadmaps e planos
│   ├── 06-plano-lia-agent-system-opcao-b.md
│   ├── 07-plano-ajustes-ux-lia.md
│   └── 08-roadmap-pearch-integration.md
└── lia/                      # Prompts e fluxos LIA
    ├── ANALISE_MELHORES_PRATICAS_IA.md
    ├── FLUXO_BUSCA_CANDIDATOS.md
    └── lia-prompt-design-specs.md
```

---

## 📚 Índice de Documentos Técnicos

### 1. [Arquitetura do Sistema](./01-arquitetura-sistema.md)
- Stack técnico (Next.js 15.5.6, React, TypeScript)
- Estrutura de diretórios
- Padrões arquiteturais
- Configurações de build e deployment
- Performance e segurança

### 2. [Design System](./02-design-system.md)
- Filosofia de design ElevenLabs
- Sistema de cores (Paleta WeDo + Cores pastel)
- Tipografia (3 níveis: Source Serif 4, Open Sans, Inter)
- Componentes padrão
- Responsividade e acessibilidade
- Tokens CSS e dark mode

### 3. [Features Implementadas](./03-features-implementadas.md)
- Módulos principais (Vagas, Candidatos, LIA Assistant)
- Dashboards e indicadores (7 categorias)
- Testes e avaliações
- Configurações e administração
- Features técnicas e convenções

### 4. [Guia de Desenvolvimento](./04-guia-desenvolvimento.md)
- Setup inicial e instalação
- Como adicionar páginas e dashboards
- Padrões de UI e componentes
- Helpers e utilities
- Boas práticas (Performance, Acessibilidade, TypeScript)
- Debugging e troubleshooting

### 5. [Changelog](./05-changelog.md)
- Histórico de mudanças
- Features adicionadas
- Bugs corrigidos
- Melhorias implementadas
- Backlog e próximas features

### 6. [Backend LIA Agent System](./06-lia-backend-integration.md)
- Arquitetura dual (Frontend + Backend)
- Como integrar frontend com backend Python
- Configuração de API keys
- Chat conversacional real-time
- Roadmap de desenvolvimento

---

## 📁 Documentos por Pasta

### design-system/
| Documento | Descrição |
|-----------|-----------|
| [LIA-DESIGN-SYSTEM.md](./design-system/LIA-DESIGN-SYSTEM.md) | Design system completo |
| [design-system-v3-pendencias.md](./design-system/design-system-v3-pendencias.md) | Pendências v3 |
| [modal-design-standards.md](./design-system/modal-design-standards.md) | Padrões de modais |

### comercial/
| Documento | Descrição |
|-----------|-----------|
| [Guia_Apresentacoes_LIA.md](./comercial/Guia_Apresentacoes_LIA.md) | Guia para apresentações |
| [LIA_Apresentacao_Comercial_Completa.md](./comercial/LIA_Apresentacao_Comercial_Completa.md) | Apresentação comercial |
| [LIA_Apresentacao_Institucional_Completa.md](./comercial/LIA_Apresentacao_Institucional_Completa.md) | Apresentação institucional |
| [LIA_Executive_Summary.md](./comercial/LIA_Executive_Summary.md) | Sumário executivo |
| [LIA_Pitch_Vendas.md](./comercial/LIA_Pitch_Vendas.md) | Pitch de vendas |
| [onboarding-roteiro.md](./comercial/onboarding-roteiro.md) | Roteiro de onboarding |

### auditorias/
| Documento | Descrição |
|-----------|-----------|
| [AUDITORIAS_SISTEMA_2025.md](./auditorias/AUDITORIAS_SISTEMA_2025.md) | Auditorias consolidadas 2025 (Vagas + Funil) |
| [DIAGNOSTICO_KANBAN_VS_TABELA.md](./auditorias/DIAGNOSTICO_KANBAN_VS_TABELA.md) | Comparação Kanban vs Tabela |
| [FEATURES_REMOVIDAS_FILTROS_AVANCADOS.md](./auditorias/FEATURES_REMOVIDAS_FILTROS_AVANCADOS.md) | Features removidas |

### planejamento/
| Documento | Descrição |
|-----------|-----------|
| [06-plano-lia-agent-system-opcao-b.md](./planejamento/06-plano-lia-agent-system-opcao-b.md) | Plano completo LIA Agent System |
| [07-plano-ajustes-ux-lia.md](./planejamento/07-plano-ajustes-ux-lia.md) | Plano ajustes UX |
| [08-roadmap-pearch-integration.md](./planejamento/08-roadmap-pearch-integration.md) | Roadmap Pearch AI |

### lia/
| Documento | Descrição |
|-----------|-----------|
| [ANALISE_MELHORES_PRATICAS_IA.md](./lia/ANALISE_MELHORES_PRATICAS_IA.md) | Melhores práticas IA |
| [FLUXO_BUSCA_CANDIDATOS.md](./lia/FLUXO_BUSCA_CANDIDATOS.md) | Fluxo de busca |
| [lia-prompt-design-specs.md](./lia/lia-prompt-design-specs.md) | Specs de prompts |

---

## 🎯 Quick Start

### Executar o Projeto

```bash
cd plataforma-lia
npm install
npm run dev
```

Acesse: `http://localhost:5000`

### Build para Produção

```bash
npm run build
```

Saída estática: `out/`

---

## 🎨 Design Principles

### Paleta de Cores
- **90% Monocromático**: Gray scale (white, black, shades of gray)
- **10% Color Accents**: Cores WeDo dessaturadas em pontos estratégicos

### Typography Hierarchy
1. **Source Serif 4**: Títulos de página
2. **Open Sans**: UI elements (labels, botões, menus)
3. **Inter**: Dados tabulares (tabelas, badges numéricos)

### Identidade LIA
- **Ícone**: Brain / BrainCircuit (Lucide React)
- **Cor**: `text-wedo-cyan` (#60BED1) ⭐
- **Padrão**: Todos os elementos LIA usam ciano

---

## 🏗️ Estrutura de Código

```
plataforma-lia/
├── docs/                       # 📚 Documentação
├── src/
│   ├── app/
│   │   ├── globals.css        # Estilos globais + tokens
│   │   └── page.tsx           # Página principal
│   ├── components/
│   │   ├── pages/             # Páginas completas
│   │   ├── sidebar.tsx        # Menu lateral
│   │   └── ui/                # shadcn/ui components
│   └── lib/                   # Utilities
├── public/                     # Assets estáticos
├── tailwind.config.ts         # Config Tailwind
├── next.config.ts             # Config Next.js
└── package.json
```

---

## 🔑 Conceitos-Chave

### Status de Vagas (12 estados)
1. Ativa, 2. Aprovada, 3. Aguardando aprovação, 4. Reaberta
5. Paralisada, 6. Interna, 7. Rascunho, 8. Fechada (preenchida)
9. Fechada (expirada), 10. Cancelada, 11. Concluída, 12. Arquivada

### Dashboards Estratégicos (7 categorias)
1. Estratégicos, 2. Previsões & IA, 3. People Analytics
4. Modelos de Trabalho, 5. Funil & Performance
6. War Room Operacional, 7. Análise de Competências

### LIA Assistant
- Sidebar modal customizável (direita)
- Contexto dinâmico por página
- Automação com IA (screening, predições, insights)
- Ícone Brain em ciano (#60BED1)

---

## 📦 Dependencies

### Core
- Next.js 15.5.6
- React 18+
- TypeScript 5+

### UI
- Tailwind CSS v3
- Radix UI
- shadcn/ui
- Lucide React

### Visualização
- Chart.js
- Recharts
- Framer Motion

---

## 🤝 Contribuindo

### Code Style
- **Idioma**: Português (código e comentários)
- **Formatting**: Prettier (2 spaces, single quotes)
- **Linting**: ESLint (configuração Next.js)
- **TypeScript**: Strict mode habilitado

### Commits
```bash
# Formato: Verbo + Descrição
git commit -m "Adiciona filtro de candidatos por skills"
git commit -m "Corrige bug na paginação do dashboard"
git commit -m "Atualiza design do card de vaga"
```

---

## 📞 Suporte

### Recursos
- Documentação técnica: Esta pasta (`docs/`)
- Replit.md: Sumário do projeto na raiz
- Code comments: Inline no código fonte

### Troubleshooting
Consulte: [Guia de Desenvolvimento - Troubleshooting](./04-guia-desenvolvimento.md#troubleshooting)
