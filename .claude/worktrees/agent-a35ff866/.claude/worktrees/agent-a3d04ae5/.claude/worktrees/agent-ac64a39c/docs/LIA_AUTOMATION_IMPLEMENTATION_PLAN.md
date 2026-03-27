# Plano de Implementação - Sistema de Automação LIA

## Visão Geral

Este documento detalha o plano de implementação faseado do Sistema de Automação LIA para transições de etapa no processo de recrutamento.

---

## Fases de Implementação

### Fase 1: MVP - Modal de Transição Inteligente (Individual)
**Duração estimada: 8-12 horas**
**Prioridade: Alta**

### Fase 2: Ações em Lote (Bulk)
**Duração estimada: 6-8 horas**
**Prioridade: Média**

### Fase 3: Integrações e Analytics
**Duração estimada: 8-10 horas**
**Prioridade: Baixa**

---

## Fase 1: MVP - Detalhamento

### 1.1 Backend: API de Predição de Sub-Status
**Arquivo:** `lia-agent-system/app/api/automation/predict_substatus.py`

**Tarefas:**
- [ ] Criar endpoint POST `/api/automation/predict-substatus`
- [ ] Implementar lógica de análise de contexto do candidato
- [ ] Integrar com Claude para predição inteligente
- [ ] Retornar sub-status sugerido + confidence + reasoning

**Estimativa:** 2 horas

### 1.2 Backend: API de Geração de Mensagem Personalizada
**Arquivo:** `lia-agent-system/app/api/automation/generate_message.py`

**Tarefas:**
- [ ] Criar endpoint POST `/api/automation/generate-message`
- [ ] Implementar coleta de contexto completo do candidato
- [ ] Criar prompts otimizados para cada tipo de mensagem
- [ ] Integrar regras de Do's and Don'ts
- [ ] Suportar diferentes canais (email/whatsapp)

**Estimativa:** 2.5 horas

### 1.3 Backend: API de Regeneração por Sub-Status
**Arquivo:** `lia-agent-system/app/api/automation/regenerate_message.py`

**Tarefas:**
- [ ] Criar endpoint POST `/api/automation/regenerate-for-substatus`
- [ ] Implementar lógica de ajuste mantendo estrutura
- [ ] Preservar edições manuais quando possível
- [ ] Retornar changelog de alterações

**Estimativa:** 1.5 horas

### 1.4 Frontend: Hook useTransitionContext
**Arquivo:** `plataforma-lia/src/hooks/use-transition-context.ts`

**Tarefas:**
- [ ] Criar hook para gerenciar contexto de transição
- [ ] Implementar coleta de dados do candidato
- [ ] Gerenciar estado de sub-status e mensagens
- [ ] Implementar chamadas às APIs de automação
- [ ] Gerenciar regeneração ao mudar sub-status

**Estimativa:** 2 horas

### 1.5 Frontend: SmartTransitionModal
**Arquivo:** `plataforma-lia/src/components/modals/smart-transition-modal.tsx`

**Tarefas:**
- [ ] Criar componente modal completo
- [ ] Header com info da transição (De → Para)
- [ ] Seletor de ação (email, whatsapp, wsi, agendar, apenas mover)
- [ ] Dropdown de sub-status (editável, com sugestão LIA)
- [ ] Preview da mensagem com indicador "Sugerido pela LIA"
- [ ] Botão de editar mensagem
- [ ] Seletor de canal (email/whatsapp)
- [ ] Estados de loading durante geração
- [ ] Ajuste dinâmico ao mudar sub-status

**Estimativa:** 3 horas

### 1.6 Frontend: Integração no Kanban
**Arquivo:** `plataforma-lia/src/components/pages/job-kanban-page.tsx`

**Tarefas:**
- [ ] Modificar handleDrop para abrir SmartTransitionModal
- [ ] Passar contexto do candidato para o modal
- [ ] Tratar confirmação do modal (mover + executar ação)
- [ ] Remover modal de seleção de sub-status atual (substituir)

**Estimativa:** 1.5 horas

### 1.7 Frontend: Integração na Tabela
**Arquivo:** `plataforma-lia/src/components/tables/cell-renderers.tsx`

**Tarefas:**
- [ ] Modificar InteractiveStageCell para usar SmartTransitionModal
- [ ] Substituir StageTransitionActionsModal atual
- [ ] Manter consistência de experiência com Kanban

**Estimativa:** 1 hora

### 1.8 Testes e Ajustes
**Tarefas:**
- [ ] Testar todas as combinações de transição
- [ ] Validar qualidade das mensagens geradas
- [ ] Ajustar prompts conforme necessário
- [ ] Testar ajuste dinâmico de sub-status
- [ ] Testar com dados reais

**Estimativa:** 2 horas

---

## Fase 2: Bulk Actions - Detalhamento

### 2.1 Backend: API de Geração em Lote
**Arquivo:** `lia-agent-system/app/api/automation/generate_bulk.py`

**Tarefas:**
- [ ] Criar endpoint POST `/api/automation/generate-bulk`
- [ ] Implementar processamento paralelo (batches de 5)
- [ ] Retornar progresso durante geração
- [ ] Suportar streaming de resultados

**Estimativa:** 2 horas

### 2.2 Frontend: Expandir SmartTransitionModal para Bulk
**Arquivo:** `plataforma-lia/src/components/modals/smart-transition-modal.tsx`

**Tarefas:**
- [ ] Adicionar modo bulk (múltiplos candidatos)
- [ ] Toggle "Template padrão" vs "Personalizado pela LIA"
- [ ] Lista scrollável de candidatos com preview
- [ ] Edição individual de mensagens
- [ ] Loading progressivo durante geração
- [ ] Contador de candidatos processados

**Estimativa:** 3 horas

### 2.3 Frontend: Integração Bulk no Kanban
**Arquivo:** `plataforma-lia/src/components/pages/job-kanban-page.tsx`

**Tarefas:**
- [ ] Suportar seleção múltipla de candidatos
- [ ] Ação de mover selecionados abre SmartTransitionModal em modo bulk
- [ ] UI de seleção (checkboxes nos cards)

**Estimativa:** 2 horas

### 2.4 Testes Bulk
**Tarefas:**
- [ ] Testar com 5, 10, 20 candidatos
- [ ] Validar performance de geração
- [ ] Testar edição individual em bulk

**Estimativa:** 1 hora

---

## Fase 3: Integrações e Analytics - Detalhamento

### 3.1 Backend: Sistema de Alertas
**Arquivo:** `lia-agent-system/app/services/alert_service.py`

**Tarefas:**
- [ ] Criar serviço de alertas unificado
- [ ] Implementar canal Bell (notificação interna)
- [ ] Implementar integração Microsoft Teams
- [ ] Configurar triggers por tipo de transição

**Estimativa:** 4 horas

### 3.2 Frontend: Central de Notificações
**Arquivo:** `plataforma-lia/src/components/notifications/`

**Tarefas:**
- [ ] Criar sino de notificações no header
- [ ] Badge com contagem de não lidas
- [ ] Dropdown com lista de alertas
- [ ] Marcar como lido/não lido
- [ ] Link direto para o candidato/vaga

**Estimativa:** 3 horas

### 3.3 Analytics de Automação
**Arquivo:** `lia-agent-system/app/services/automation_analytics.py`

**Tarefas:**
- [ ] Trackear uso de sugestões LIA
- [ ] Medir taxa de aceitação vs edição
- [ ] Tempo médio por transição
- [ ] Dashboard de métricas

**Estimativa:** 3 horas

---

## Cronograma Sugerido

```
Semana 1:
├── Dia 1-2: Backend APIs (1.1, 1.2, 1.3)
├── Dia 3: Hook useTransitionContext (1.4)
├── Dia 4-5: SmartTransitionModal (1.5)

Semana 2:
├── Dia 1: Integração Kanban (1.6)
├── Dia 2: Integração Tabela (1.7)
├── Dia 3-4: Testes e Ajustes (1.8)
├── Dia 5: Buffer / Deploy MVP

Semana 3:
├── Fase 2: Bulk Actions

Semana 4:
├── Fase 3: Integrações e Analytics
```

---

## Dependências Técnicas

### Backend
- FastAPI (já instalado)
- Anthropic Claude API (já integrado)
- Pydantic para validação

### Frontend
- React + TypeScript (já configurado)
- Radix UI para componentes (já instalado)
- SWR para data fetching (já instalado)

---

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Latência da geração de mensagens | Média | Alto | Implementar loading states e feedback visual |
| Qualidade das mensagens | Média | Alto | Testes extensivos, ajuste de prompts, revisão humana |
| Custo de tokens Claude | Baixa | Médio | Cache de contexto, limitar tamanho de prompts |
| Complexidade do modal | Média | Médio | Implementar incrementalmente, code review |

---

## Critérios de Sucesso

### Fase 1 (MVP)
- [ ] Todas as transições de etapa passam pelo SmartTransitionModal
- [ ] LIA sugere sub-status com >80% de acurácia
- [ ] Mensagens personalizadas são geradas em <3 segundos
- [ ] Ao mudar sub-status, mensagem é reajustada automaticamente
- [ ] Recrutador pode editar qualquer parte da mensagem

### Fase 2 (Bulk)
- [ ] Suporte a até 20 candidatos por vez
- [ ] Geração completa em <30 segundos para 20 candidatos
- [ ] Edição individual mantida

### Fase 3 (Integrações)
- [ ] Alertas Bell funcionando para todas as transições relevantes
- [ ] Integração Teams operacional
- [ ] Dashboard de métricas disponível

---

## Aprovação

| Papel | Nome | Data | Status |
|-------|------|------|--------|
| Product Owner | | | Pendente |
| Tech Lead | | | Pendente |
| UX Designer | | | Pendente |

---

*Documento criado em: Janeiro 2026*
*Versão: 1.0*
