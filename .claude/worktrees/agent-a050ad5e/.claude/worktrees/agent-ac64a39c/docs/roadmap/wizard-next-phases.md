# Plano de Implementação: Wizard Inteligente de Criação de Vagas

> **Versão**: 1.0  
> **Data**: Fevereiro 2026  
> **Objetivo**: Fazer a 10ª vaga ser criada 80% mais rápida que a 1ª

---

## Status das Fases Implementadas

### Fases Concluídas ✅

| Fase | Descrição | Status | Data |
|------|-----------|--------|------|
| **1** | Smart Start (catálogo pré-configurado) | ✅ Completo | Jan 2026 |
| **2** | Refactored Wizard Architecture (modularização) | ✅ Completo | Jan 2026 |
| **3** | WSI Quality Gates (5+ técnicas, 3+ comportamentais) | ✅ Completo | Jan 2026 |
| **4** | Unified Orchestrator verification | ✅ Verificado | Fev 2026 |
| **5** | useWizardOrchestrator hook + backend integration | ✅ Completo | Fev 2026 |
| **6** | Command Parser (navegação/edição local) | ✅ Completo | Fev 2026 |
| **7** | Bidirectional Chat-Panel Sync (useChatSync) | ✅ Completo | Fev 2026 |
| **8** | Learning System (pgvector + embeddings) | ✅ Completo | Fev 2026 |

### Detalhes da Fase 8 (Learning System)

**Componentes implementados:**
- **Backend:**
  - `JobEmbedding` model com pgvector para busca semântica
  - `JobPattern`, `SalaryBenchmark`, `SkillCluster` models
  - `JobEmbeddingService` para gerar embeddings e buscar similares
  - API `/api/v1/job-embeddings/` com endpoints de busca e Fast Track
  - Seed com 12 vagas de exemplo + padrões de sucesso
  
- **Frontend:**
  - `useLearning` hook - busca sugestões ao mudar título da vaga
  - `useWizardAnalytics` hook - tracking de sessões e métricas
  - Aplicação automática de sugestões (salário, skills, competências)

**Arquivos principais:**
- `lia-agent-system/app/models/job_pattern.py`
- `lia-agent-system/app/services/job_embedding_service.py`
- `lia-agent-system/app/api/v1/job_embeddings.py`
- `plataforma-lia/src/components/expanded-chat/hooks/useLearning.ts`
- `plataforma-lia/src/components/expanded-chat/hooks/useWizardAnalytics.ts`

---

### Detalhes da Fase 7 (Sincronização Bidirecional)

**Componentes implementados:**
- `useChatSync` hook com debounce (800ms) e grouping (1500ms)
- Tracking de mudanças de salário (panel e chat)
- Tracking de mudanças de skills técnicas (panel e chat)
- Tracking de mudanças de competências comportamentais (panel)
- Contexto LLM enriquecido com `generateLLMContext()`
- Mensagens de sistema automáticas para mudanças do painel

**Arquivos modificados:**
- `plataforma-lia/src/components/expanded-chat-modal.tsx`
- `plataforma-lia/src/components/expanded-chat/hooks/useChatSync.ts`

---

## Próximas Etapas (Fase 9-10)

### Fase 9: Fast Track & Biblioteca de Templates (3-4 semanas) 🔄 EM PROGRESSO

**Objetivo**: Biblioteca de 480 templates + Fast Track para criação em 3 minutos

#### 9.1 Biblioteca de Templates (~480 templates)

| Área | Quantidade | Subáreas |
|------|------------|----------|
| Tecnologia/TI | 85 | Desenvolvimento (25), Dados (15), Infra/Cloud (12), Segurança (10), Design (8), Gestão (10), Suporte (5) |
| Finanças/Contabilidade/Tributário | 55 | Contabilidade (10), Fiscal/Tributário (15), Controladoria/FP&A (10), Tesouraria (8), Auditoria (6), Crédito/Risco (6) |
| Recursos Humanos | 35 | R&S (8), Generalista/BP (7), DP (6), Comp&Ben (5), T&D (5), D&I (4) |
| Comercial/Vendas | 45 | Inside Sales (8), Field Sales (10), Vendas Técnicas (5), Canais (5), Sales Ops (8), E-commerce (5), Backoffice (4) |
| Marketing | 40 | Digital (12), Conteúdo/Social (8), Branding (6), Produto/Trade (8), Analytics (4), Liderança (2) |
| Operações/Supply Chain | 35 | Logística (10), Supply Chain (10), Compras (8), Comex (7) |
| Engenharia | 50 | Civil (10), Mecânica (8), Elétrica (8), Produção (8), Química (6), Outras (10) |
| Jurídico/Compliance | 25 | Corporativo (10), Trabalhista (5), Compliance (10) |
| Administrativo | 15 | Secretariado, Facilities, Viagens, Frotas |
| Customer Success | 25 | CS (8), CX (5), Suporte (7), Implementação (5) |
| Saúde | 40 | Medicina (12), Enfermagem (8), Outras (12), Gestão Hospitalar (8) |
| Educação | 15 | Professores, Designers Instrucionais, E-learning |
| Qualidade | 15 | ISO, Lean Six Sigma, Melhoria Contínua |

#### 9.2 Tarefas de Implementação

| Tarefa | Descrição | Status |
|--------|-----------|--------|
| **9.2.1** | Modelo JobTemplate + migrations | ✅ Completo |
| **9.2.2** | Gerar dados completos (skills, competências, responsabilidades, títulos alternativos) | 🔄 Em progresso |
| **9.2.3** | Seed script com 480 templates | Pendente |
| **9.2.4** | API de templates (CRUD, busca, clone) | Pendente |
| **9.2.5** | Serviço de enriquecimento IA | Pendente |
| **9.2.6** | Learning system (evolução por uso) | Pendente |
| **9.2.7** | Integração Fast Track no wizard | Pendente |

#### 9.3 Estrutura de Cada Template

Cada template inclui:
- **Título + Títulos alternativos** (3-5 sinônimos)
- **Skills técnicas** (5-10 com níveis e pesos)
- **Competências comportamentais** (3-5 com justificativa)
- **Responsabilidades** (5-8 bullet points)
- **Requisitos mínimos** (formação, experiência, certificações)
- **Diferenciais** (nice-to-have)
- **Faixa salarial** (min/max por senioridade)

#### 9.4 Fluxo de Evolução

1. **Templates do sistema** (is_system=true): Base de 480 templates
2. **Geração IA**: Enriquece campos vazios dinamicamente
3. **Learning por uso**: Empresa cria variação → vira template da empresa
4. **Feedback loop**: Métricas de sucesso atualizam quality_score

**Arquivos principais:**
- `lia-agent-system/app/models/job_template.py`
- `docs/templates/biblioteca-templates-completa.md`

---

### Fase 10: Analytics e Métricas (2 semanas) - ADIADA

**Objetivo**: Dashboard de eficiência do wizard

| Tarefa | Descrição | Prioridade |
|--------|-----------|------------|
| **10.1** | Time-to-Create Tracking - Medir tempo de criação por etapa | Alta |
| **10.2** | Auto-fill Rate - % de campos preenchidos automaticamente | Alta |
| **10.3** | Edit Rate - % de campos editados pelo recrutador | Média |
| **10.4** | Quality Score - Pontuação WSI média das vagas | Média |
| **10.5** | Recruiter Dashboard - Métricas por recrutador | Baixa |

**Dependências técnicas:**
- Event tracking no frontend
- Backend analytics service
- Dashboard UI

---

## Melhorias Contínuas

### Performance (P1)

| Melhoria | Descrição | Esforço |
|----------|-----------|---------|
| Lazy Loading de Stages | Carregar stages sob demanda | 1 dia |
| Otimização de Re-renders | Memoização de componentes pesados | 2 dias |
| Cache de Configurações | Redis cache para companyConfig | 1 dia |
| Debounce de API Calls | Reduzir chamadas desnecessárias | 1 dia |

### UX (P2)

| Melhoria | Descrição | Esforço |
|----------|-----------|---------|
| Keyboard Shortcuts | Atalhos para navegação rápida | 2 dias |
| Undo/Redo | Desfazer alterações no wizard | 3 dias |
| Drag & Drop Skills | Reordenar skills arrastando | 2 dias |
| Inline Editing | Editar campos diretamente nos cards | 2 dias |
| Voice Input | Entrada por voz para chat | 1 semana |

### Robustez (P3)

| Melhoria | Descrição | Esforço |
|----------|-----------|---------|
| Error Boundaries | Recuperação graceful de erros | 1 dia |
| Offline Support | Salvar localmente quando offline | 3 dias |
| Conflict Resolution | Detectar edições simultâneas | 2 dias |
| Validation Improvements | Validação em tempo real mais granular | 2 dias |

### Testes (P4)

| Melhoria | Descrição | Esforço |
|----------|-----------|---------|
| Unit Tests para Hooks | Testar useChatSync, useWizardOrchestrator | 2 dias |
| E2E Tests do Wizard | Testes de fluxo completo | 3 dias |
| Integration Tests | Testes de integração com backend | 2 dias |
| Performance Tests | Benchmarks de tempo de resposta | 1 dia |

---

## Métricas de Sucesso

### KPIs da Fase 7 (Atual)

| Métrica | Baseline | Target | Atual |
|---------|----------|--------|-------|
| Tempo médio de criação de vaga | ~15 min | <8 min | TBD |
| % de campos auto-preenchidos | ~30% | >60% | TBD |
| Satisfação do recrutador | - | >4.5/5 | TBD |
| Erros de validação | - | <5% | TBD |

### KPIs Meta (10ª Vaga 80% Mais Rápida)

| Métrica | 1ª Vaga | 10ª Vaga | Redução |
|---------|---------|----------|---------|
| Tempo de criação | 15 min | 3 min | 80% |
| Campos editados | 20 | 4 | 80% |
| Interações com chat | 10 | 2 | 80% |

---

## Cronograma Sugerido

```
Fev 2026    Mar 2026    Abr 2026    Mai 2026
   |           |           |           |
   v           v           v           v
[Fase 8: Aprendizado] --> [Fase 9: Reutilização] --> [Fase 10: Analytics]
   |                           |                           |
   +-- 8.1 Pattern Recognition +-- 9.1 Fast Track          +-- 10.1 Time Tracking
   +-- 8.2 Salary Learning     +-- 9.2 Templates           +-- 10.2 Auto-fill Rate
   +-- 8.3 Skills Engine       +-- 9.3 Delta Analysis      +-- 10.3 Edit Rate
   +-- 8.4 TTF Prediction      |                           +-- 10.4 Quality Score
   +-- 8.5 Success Profile     |                           +-- 10.5 Dashboard
```

---

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Volume de dados insuficiente para learning | Média | Alto | Aguardar 100+ vagas antes de Phase 8 |
| Performance degradada com tracking | Baixa | Médio | Debounce agressivo, lazy loading |
| Complexidade de manutenção | Média | Médio | Documentação detalhada, code reviews |
| Resistência dos recrutadores | Baixa | Alto | Treinamento, feedback loops |

---

> **Documento mantido por**: Equipe LIA  
> **Última revisão**: 01 de Fevereiro de 2026
