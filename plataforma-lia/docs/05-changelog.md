# Changelog - Plataforma LIA

## Convenções
- **[NEW]**: Nova feature
- **[FIX]**: Correção de bug
- **[ENHANCE]**: Melhoria de feature existente
- **[REFACTOR]**: Refatoração de código
- **[STYLE]**: Mudanças visuais/UI

---

## Novembro 2025

### Sistema de Status de Vagas - 12 Estados
**Data**: 17/11/2025

#### [NEW] Cores Pastel para Status
- Implementado sistema de cores pastel harmonioso para 12 status de vagas
- Paleta ElevenLabs (#A8D5B7 verde menta, #F5E6B3 amarelo suave, etc.)
- Contraste WCAG AA garantido em todos os status
- Função helper `getStatusColor()` centralizada

#### [NEW] 9 Vagas Mockadas
Vagas adicionadas cobrindo novos status:
1. Gerente de Projetos - Aprovada
2. Analista de BI - Aguardando aprovação
3. Desenvolvedor Full Stack - Reaberta
4. Assistente Administrativo - Interna
5. Analista de Marketing Digital - Fechada (preenchida)
6. Coordenador de Logística - Fechada (expirada)
7. Designer Gráfico - Cancelada
8. Especialista em Cibersegurança - Rascunho
9. Coordenador de RH - Arquivada

#### [FIX] Bug Crítico na Renderização
- **Problema**: `organizeJobsByStatus` limitado a 4 status antigos
- **Impacto**: 8 novos status invisíveis na tabela
- **Solução**: Atualizado `statusOrder` e `grouped` para incluir todos os 12 status
- **Resultado**: Todas as 24 vagas agora visíveis

#### [ENHANCE] Ícone de Vaga Confidencial
- Tamanho aumentado para 16px (melhor visibilidade)
- Cor alterada para laranja `#ea580c` (orange-600)
- Stroke weight aumentado para 2.5 (mais destaque)

---

### Ajuste de Typography - Menu Admin
**Data**: 17/11/2025

#### [STYLE] Padronização de Fontes
- **Problema**: Menu administrativo com fontes maiores que sidebar principal
- **Solução**: Ajustado menu admin para igualar hierarquia do sidebar
  - Títulos principais: `text-sm` → `text-[10px]`
  - Descrições: `text-xs` → `text-[8px]`
  - Subsections: `text-sm` → `text-[9px]`
- **Padrão**: Open Sans em tamanhos ultra-compactos

---

### Dashboards People Analytics
**Data**: Anterior

#### [NEW] Big Five Analytics
- Dashboard completo de análise de personalidade
- Métricas de distribuição dos 5 traços
- Visualizações em radar chart
- Insights por departamento

#### [NEW] Diversidade & Inclusão
- KPIs de diversidade (gênero, etnia, idade, PcD)
- Metas vs realizado
- Tendências temporais
- Análise por nível hierárquico

#### [NEW] NPS (eNPS)
- Employee Net Promoter Score
- Segmentação por time/departamento
- Evolução temporal
- Benchmark de mercado

#### [ENHANCE] Navegação por Tabs
- 3 dashboards integrados em People Analytics
- Transição suave entre tabs
- Estado persistente

---

### UI/UX Ultra-Compacto
**Data**: Anterior

#### [NEW] Sidebar Collapsible para Dashboards
- Largura: 256px (w-64) expandida, 64px (w-16) colapsada
- Auto-expand on hover
- Botão lock/unlock opcional
- Typography: text-[11px] labels, text-[10px] descriptions, text-[9px] badges

#### [STYLE] Hierarquia Tipográfica Reduzida
- H1: `text-sm`
- H2/CardTitle: `text-[12px]`
- KPI Values: `text-xl`
- Tertiary text: `text-[9px] tracking-tight`
- **ALL badges**: `text-[9px] tracking-tight` (padronização global)

#### [ENHANCE] Layout Responsivo
- Otimizado para 1366x768px (11" laptops)
- Viewport: `px-3 pt-3 pb-6`
- Cards: `gap-2.5` grids
- Overflow handling: `overflow-hidden min-h-0`

---

### Design System
**Data**: Anterior

#### [NEW] Paleta WeDo Semântica
- Green (#4CAF50): Sucesso, aprovações
- Cyan (#60BED1): LIA Intelligence ⭐
- Orange (#FF9800): Alertas, ações urgentes
- Purple (#9C27B0): Premium features
- Magenta (#E91E63): Destaque, favoritos

#### [STYLE] Identidade Visual LIA
- **Padrão BRAIN ICON**: `text-wedo-cyan` (#60BED1)
- Todos os ícones Brain/BrainCircuit usam ciano
- Botões e cards LIA seguem padrão neutral + cyan accent
- Reforço consistente da marca LIA

#### [NEW] Design Tokens CSS
- Arquivo `design-tokens.css` com variáveis completas
- Paleta WeDo mapeada para light/dark mode
- WCAG contrast compliance (≥4.5:1)
- Sistema de cores pastel integrado

---

### Sistema Tipográfico de 3 Níveis
**Data**: Anterior

#### [NEW] Source Serif 4 - Títulos
- Uso: H1 de páginas principais
- Peso: 600-700 (Semibold/Bold)
- Elegância serif para hierarquia

#### [NEW] Open Sans - UI Elements
- Uso: Labels, botões, menus, subtítulos
- Peso: 400-600 (Regular/Semibold)
- Legibilidade otimizada para UI

#### [NEW] Inter - Dados Tabulares
- Uso: Tabelas, badges numéricos, métricas
- Peso: 400-500 (Regular/Medium)
- Clarity em dados densos

---

### Módulo de Vagas
**Data**: Anterior

#### [NEW] Funcionalidades Core
- Sistema completo de CRUD
- Filtros avançados (status, dias, departamento)
- Busca global multi-campo
- Ações em lote
- Pin de vagas prioritárias
- Vagas confidenciais

#### [NEW] Preview Modal
- Tabs: Overview, Screening Script, Pipeline, LIA Metrics
- Visualização detalhada sem sair da lista
- Ações rápidas integradas

#### [NEW] Pipeline Kanban
- Fluxo visual de candidatos
- Drag & drop (planejado)
- Métricas por etapa

---

### Módulo de Candidatos
**Data**: Anterior

#### [NEW] Gestão Completa
- Perfil detalhado
- Timeline de interações
- Upload de documentos
- Testes integrados (English, Big Five)
- Scoring LIA

#### [NEW] Comparação de Candidatos
- Side-by-side comparison
- Métricas normalizadas
- Recomendações LIA

---

### LIA Assistant
**Data**: Anterior

#### [NEW] Sidebar Modal
- Posição lateral direita
- Modos: Colapsada / Expandida
- Contexto dinâmico por página
- Quick actions

#### [NEW] Automação Inteligente
- Screening automático
- Análise de compatibilidade
- Sugestões contextuais
- Predições de sucesso

---

### Dashboards Estratégicos
**Data**: Anterior

#### [NEW] 7 Categorias de Dashboards
1. Estratégicos
2. Previsões & IA
3. People Analytics
4. Modelos de Trabalho
5. Funil & Performance
6. War Room Operacional
7. Análise de Competências

#### [NEW] Layout Pattern Unificado
- Sidebar hover-collapsible
- Typography ultra-compacta
- Semantic WeDo colors
- 90% monochrome / 10% color accents

---

### Configurações e Admin
**Data**: Anterior

#### [NEW] Menu Administrativo
- Seções: Dados da Empresa, Estrutura, Pessoas, Integrações
- Subsections com breadcrumb
- Status tracking (Configurado/Pendente/Não configurado)
- Typography Open Sans compacta

---

## Backlog / Próximas Features

### Planejadas
- [ ] Sistema de permissões granular
- [ ] Integração com calendário (Google/Outlook)
- [ ] Email templates customizáveis
- [ ] Exportação de relatórios avançados
- [ ] Mobile responsiveness completo
- [ ] PWA support
- [ ] Drag & drop no Kanban
- [ ] Real-time notifications
- [ ] Multi-idioma (i18n)
- [ ] Testes automatizados (Jest, React Testing Library)

### Em Discussão
- [ ] Video interviews integradas
- [ ] Gamification para candidatos
- [ ] API pública para integrações
- [ ] Marketplace de templates
- [ ] White-label solution
