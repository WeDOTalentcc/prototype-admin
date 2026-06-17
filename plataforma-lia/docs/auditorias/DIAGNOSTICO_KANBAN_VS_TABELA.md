# Diagnóstico Comparativo: Kanban vs Tabela de Candidatos

**Data:** 22/12/2024  
**Objetivo:** Mapear funcionalidades, modais, botões e ações entre as duas interfaces para planejar paridade funcional.

---

## 1. Exibição de Scores

| Score | Kanban | Tabela | Status |
|-------|--------|--------|--------|
| **Nota Geral LIA** (Gauge) | ✅ Ícone clicável → GeneralScoreModal | ❌ Não exibido | GAP |
| **Triagem** (BrainCircuit) | ✅ Ícone clicável → TriagemDetailsModal | ❌ Não exibido | GAP |
| **CV Match** (Target) | ✅ Ícone clicável → LiaAnalysisModal | 🔶 Coluna `score` genérica (sem modal) | GAP PARCIAL |
| **Técnico** (Code) | ✅ Ícone clicável → TechnicalTestModal | ❌ Não exibido | GAP |
| **Inglês** (Globe) | ✅ Ícone clicável → EnglishTestModal | ❌ Não exibido | GAP |
| **Big Five** (Fingerprint) | ✅ Ícone clicável → BigFiveModal | ❌ Não exibido | GAP |

---

## 2. Modais Disponíveis

| Modal | Kanban | Tabela | Status |
|-------|--------|--------|--------|
| **GeneralScoreModal** (metodologia cálculo) | ✅ Via ícone Gauge | ❌ | GAP |
| **TriagemDetailsModal** (histórico triagem) | ✅ Via ícone Brain + sidebar | ❌ | GAP |
| **LiaAnalysisModal** (CV vs Vaga) | ✅ Via ícone Target + badge | ❌ | GAP |
| **TechnicalTestModal** (teste técnico) | ✅ Via ícone Code | ❌ | GAP |
| **EnglishTestModal** (teste inglês) | ✅ Via ícone Globe | ❌ | GAP |
| **BigFiveModal** (personalidade) | ✅ Via ícone Fingerprint | ❌ | GAP |
| **RubricEvaluationModal** (rubricas) | ✅ Via badge/dropdown | ❌ | GAP |
| **CandidateDecisionFlowModal** (Aprovar/Reprovar) | ✅ Botões na sidebar | ❌ | GAP |
| **JobReportModal** (relatório vaga) | ✅ Header do Kanban | ❌ | GAP |
| **UnifiedCommunicationModal** | ✅ Via dropdown/ações | ✅ Via ações | OK |
| **WSITextScreeningModal** | ✅ Via dropdown | ✅ Via ações | OK |
| **WSITriagemInviteModal** | ✅ Via dropdown | ✅ Via ações | OK |
| **QuickViewModal** | ❌ | ✅ | OK (Tabela tem) |
| **ContactModal/ScheduleModal** | ❌ | ✅ | OK (Tabela tem) |
| **AddToListModal** | ✅ Via dropdown | ✅ Via bulk actions | OK |
| **AddCandidatesToVacancyModal** | ✅ Via dropdown | ✅ Via bulk actions | OK |
| **BatchApprovalModal** | ❌ | ✅ Bulk actions | OK (Tabela tem) |
| **SendEmailModal** | ✅ Via dropdown | ✅ Via bulk | OK |
| **CandidateReviewModal** | ❌ | ✅ | OK (Tabela tem) |

---

## 3. Ações de Candidato (Single)

| Ação | Kanban | Tabela | Status |
|------|--------|--------|--------|
| **Aprovar/Reprovar** | ✅ Botões na sidebar (CandidateDecisionFlowModal) | ❌ | GAP CRÍTICO |
| **Mover etapa (drag & drop)** | ✅ | ❌ N/A (estrutura tabela) | N/A |
| **Ver perfil LinkedIn** | ✅ Botão LinkedIn | ✅ Coluna LinkedIn | OK |
| **Enviar email** | ✅ Via dropdown | ✅ Via ações | OK |
| **Enviar WhatsApp** | ✅ Via dropdown | ❌ | GAP |
| **Agendar entrevista** | ✅ Via dropdown | ✅ Via ações | OK |
| **Adicionar à lista** | ✅ Via dropdown | ✅ Via ações | OK |
| **Pin/Favorito** | ❌ | ✅ ActionButtons | OK (Tabela tem) |
| **Ver CV/Documento** | ✅ Via dropdown | ✅ Via ações | OK |
| **Convidar WSI** | ✅ Via dropdown | ✅ Via ações | OK |
| **Quick View** | ❌ | ✅ QuickViewModal | OK (Tabela tem) |

---

## 4. Bulk Actions (Múltiplos Candidatos)

| Ação | Kanban | Tabela | Status |
|------|--------|--------|--------|
| **Seleção múltipla (checkboxes)** | 🔶 Limitado | ✅ | OK |
| **Aprovar em lote** | ❌ | ✅ BatchApprovalModal | GAP no Kanban |
| **Enviar email em lote** | 🔶 Via ContextualActionsBanner | ✅ | OK |
| **Adicionar a lista em lote** | 🔶 Via banner | ✅ | OK |
| **Exportar selecionados** | ❌ | ✅ | GAP no Kanban |
| **Comparar candidatos** | ❌ | ✅ showComparisonModal | GAP no Kanban |

---

## 5. Filtros e Ordenação

| Funcionalidade | Kanban | Tabela | Status |
|----------------|--------|--------|--------|
| **Busca por nome** | ✅ | ✅ | OK |
| **Filtro por etapa** | ✅ (visual por coluna) | ❌ (não aplica) | N/A |
| **Ordenação por coluna** | ❌ | ✅ Multi-coluna | GAP no Kanban |
| **Filtros avançados (Pearch)** | ❌ | ✅ AdvancedFiltersModal | GAP no Kanban |
| **Presets de filtros** | ❌ | ✅ | GAP no Kanban |

---

## 6. Visualização de Dados por Candidato

| Dado | Kanban | Tabela | Status |
|------|--------|--------|--------|
| **Avatar** | ✅ | ✅ | OK |
| **Nome** | ✅ | ✅ | OK |
| **Email** | ❌ Card | ✅ CandidateCell | GAP no Kanban |
| **Cargo atual** | ✅ | ✅ | OK |
| **Empresa atual** | ✅ | ✅ | OK |
| **Localização** | ✅ | ✅ | OK |
| **6 Scores (ícones interativos)** | ✅ | ❌ | GAP CRÍTICO |
| **Tags de origem** | ✅ | 🔶 SourceCell | OK |
| **Sub-status detalhado** | ✅ | ❌ | GAP |
| **Skills** | ❌ | ✅ SkillsCell | GAP no Kanban |
| **Salário** | ❌ | ✅ SalaryCell | GAP no Kanban |
| **Work Model** | ❌ | ✅ WorkModelCell | GAP no Kanban |
| **Badge "visualizado"** | ✅ | ❌ | GAP na Tabela |

---

## 7. Integrações

| Integração | Kanban | Tabela | Status |
|------------|--------|--------|--------|
| **WSI (Work Sample Interview)** | ✅ Invites/Text/Voice | ✅ | OK |
| **Calendar (agendamento)** | ✅ | ✅ | OK |
| **Pearch AI (busca global)** | ❌ (não aplica) | ✅ | OK |
| **ATS Export** | ❌ | ✅ | OK |

---

## Resumo de Gaps Prioritários

### CRÍTICOS (Alta prioridade - UX inconsistente)

| # | Gap | Onde falta | Impacto |
|---|-----|------------|---------|
| 1 | **Barra de 6 scores com ícones clicáveis** | Tabela | Usuário não consegue ver/acessar análises detalhadas |
| 2 | **Aprovar/Reprovar candidato** | Tabela | Decisão de contratação indisponível |
| 3 | **Modais de scores** (General, Técnico, Inglês, B5) | Tabela | Análises completas inacessíveis |
| 4 | **TriagemDetailsModal** | Tabela | Histórico de triagem invisível |
| 5 | **LiaAnalysisModal** (CV vs Vaga) | Tabela | Análise de fit inacessível |

### MÉDIOS (Paridade funcional)

| # | Gap | Onde falta |
|---|-----|------------|
| 6 | **Sub-status detalhados** | Tabela |
| 7 | **Badge "visualizado"** | Tabela |
| 8 | **WhatsApp direto** | Tabela |
| 9 | **JobReportModal** | Tabela (contexto de vaga) |
| 10 | **RubricEvaluationModal** | Tabela |

### NICE-TO-HAVE (Kanban catching up)

| # | Gap | Onde falta |
|---|-----|------------|
| 11 | Ordenação multi-coluna | Kanban |
| 12 | Filtros avançados | Kanban |
| 13 | Comparação de candidatos | Kanban |
| 14 | Export em lote | Kanban |
| 15 | Pin/Favorito | Kanban |

---

## Plano de Implementação

### Fase 1 - Paridade Crítica na Tabela
**Estimativa:** 2-3 dias  
**Objetivo:** Trazer funcionalidades core do Kanban para a Tabela

#### 1.1 Barra de Scores com Ícones Clicáveis
- [ ] Criar nova coluna `scores` ou cell renderer `ScoresCell`
- [ ] Reutilizar componente `ScoreIconButton` do Kanban
- [ ] Integrar os 6 ícones: Gauge, BrainCircuit, Target, Code, Globe, Fingerprint
- [ ] Passar props: `formattedValue`, `alwaysClickable` (para CV/Triagem)

#### 1.2 Integração dos Modais de Scores
- [ ] Adicionar estados para cada modal na página que usa a tabela
- [ ] Implementar `handleOpenScoreModal` similar ao Kanban
- [ ] Conectar cliques dos ícones aos handlers
- [ ] Modais a integrar:
  - `GeneralScoreModal`
  - `TriagemDetailsModal`
  - `LiaAnalysisModal`
  - `TechnicalTestModal`
  - `EnglishTestModal`
  - `BigFiveModal`

#### 1.3 Aprovar/Reprovar na Tabela
- [ ] Adicionar ação no menu dropdown da linha
- [ ] Integrar `CandidateDecisionFlowModal`
- [ ] Implementar callbacks de decisão

---

### Fase 2 - Completude da Tabela
**Estimativa:** 1-2 dias  
**Objetivo:** Pequenas melhorias de UX

#### 2.1 Sub-status como Badge
- [ ] Criar `SubStatusCell` renderer
- [ ] Mapear sub-status por etapa do pipeline

#### 2.2 Badge de Visualizado
- [ ] Adicionar estado `viewedCandidateIds` na tabela
- [ ] Mostrar indicador visual (ícone Eye) no avatar ou nome

#### 2.3 WhatsApp no Menu de Ações
- [ ] Adicionar item "Enviar WhatsApp" no dropdown
- [ ] Abrir `UnifiedCommunicationModal` com type='whatsapp'

#### 2.4 RubricEvaluationModal
- [ ] Adicionar ação "Ver Rubricas" no dropdown
- [ ] Conectar ao modal existente

---

### Fase 3 - Enriquecimento do Kanban
**Estimativa:** 2-3 dias  
**Objetivo:** Trazer funcionalidades da Tabela para o Kanban

#### 3.1 Ordenação de Cards
- [ ] Adicionar dropdown "Ordenar por" no header de cada coluna
- [ ] Opções: Score, Nome, Data de aplicação
- [ ] Persistir ordenação por coluna

#### 3.2 Atalho para Filtros Avançados
- [ ] Adicionar botão "Filtros" no header do Kanban
- [ ] Abrir `AdvancedFiltersModal` ou modal simplificado
- [ ] Aplicar filtros aos candidatos exibidos

#### 3.3 Comparação Rápida
- [ ] Permitir selecionar 2-3 cards (Cmd/Ctrl+Click)
- [ ] Mostrar botão "Comparar" no banner contextual
- [ ] Abrir modal de comparação lado-a-lado

#### 3.4 Pin/Favorito em Cards
- [ ] Adicionar ícones de Pin/Star no hover do card
- [ ] Persistir estado
- [ ] Opção de filtrar apenas fixados/favoritos

---

## Arquivos Relevantes

### Kanban
- `plataforma-lia/src/components/pages/job-kanban-page.tsx` - Página principal
- `plataforma-lia/src/components/ui/score-icon-button.tsx` - Componente de ícone de score

### Tabela
- `plataforma-lia/src/components/tables/unified-candidate-table.tsx` - Componente de tabela
- `plataforma-lia/src/components/tables/candidate-table-row.tsx` - Linha da tabela
- `plataforma-lia/src/components/tables/cell-renderers.tsx` - Células customizadas
- `plataforma-lia/src/components/tables/types.ts` - Tipos e interfaces

### Modais Compartilhados
- `plataforma-lia/src/components/modals/general-score-modal.tsx`
- `plataforma-lia/src/components/modals/technical-test-modal.tsx`
- `plataforma-lia/src/components/modals/english-test-modal.tsx`
- `plataforma-lia/src/components/big-five-modal.tsx`
- `plataforma-lia/src/components/modals/lia-analysis-modal.tsx`
- `plataforma-lia/src/components/triagem-details-modal.tsx`
- `plataforma-lia/src/components/rubric-evaluation-modal.tsx`
- `plataforma-lia/src/components/candidate-decision-flow-modal.tsx`

---

## Notas Técnicas

### Componente ScoreIconButton
Já criado e testado no Kanban. Props importantes:
- `formattedValue`: string formatada (ex: "85%")
- `alwaysClickable`: boolean para modais sempre acessíveis (CV, Triagem)
- `onClick`: handler para abrir modal específico

### Cálculo da Nota Geral LIA
```typescript
function calculateNotaLiaGeral(candidate) {
  const weights = {
    cv: 0.25,      // 25%
    triagem: 0.30, // 30%
    tecnico: 0.25, // 25%
    ingles: 0.20   // 20%
  }
  // Média ponderada dos scores disponíveis
}
```

### Padrão de Design
- 100% monocromático (escala de cinzas)
- Ícones em ciano (#60BED1) quando ativos
- Ícones em cinza quando inativos/indisponíveis
- Tooltips informativos sempre visíveis
