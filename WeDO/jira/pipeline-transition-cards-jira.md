# Cards Jira — Pipeline, Transições e Comunicação

**Versão:** 1.0  
**Data:** 19/fev/2026  
**Referências:**
- `docs/pipeline-transition-system.md` v1.2 (18/fev/2026) — especificação funcional completa
- `docs/lia-ai-architecture-cards-jira.md` v2.5 (19/fev/2026) — cards de IA (6 cards com overlap)
- `docs/mvp-alpha-scenarios.md` v2.3 (19/fev/2026) — cenário Alpha 1

---

## Sumário

1. [Contexto e Motivação](#1-contexto-e-motivação)
2. [Relação com Cards de IA Existentes](#2-relação-com-cards-de-ia-existentes)
3. [Épicos](#3-épicos)
4. [Cards Alpha 1](#4-cards-alpha-1)
5. [Cards Alpha 2+](#5-cards-alpha-2)
6. [Tabela Resumo](#6-tabela-resumo)
7. [Mapa de Dependências](#7-mapa-de-dependências)

---

## 1. Contexto e Motivação

O documento `pipeline-transition-system.md` especifica todo o sistema de movimentação de candidatos: arquitetura de colunas, modais de transição, disparos automáticos, badges, herança de pipeline, criação de colunas customizadas e ações em massa.

Os cards de IA (`lia-ai-architecture-cards-jira.md`) cobrem a **camada AI/LLM** do pipeline (predição de sub-status, message generation, webhooks, feature flags). Porém, a **camada de produto** — modelo de dados de colunas, motor de transição, modais frontend, configuração de pipeline, badges — não possui cards dedicados.

Este documento preenche esse gap com cards focados na **infraestrutura de produto** do pipeline.

### Convenção de Prefixo

Todos os cards usam prefixo `PIP-` (Pipeline) para distingui-los dos cards de IA (`AGT-`, `SRV-`, `INF-`, `AUT-`).

---

## 2. Relação com Cards de IA Existentes

Os cards abaixo já existem em `lia-ai-architecture-cards-jira.md` e cobrem aspectos AI/LLM do pipeline. Os cards `PIP-*` deste documento **complementam** (não duplicam) esses cards.

| Card IA | Título | O que cobre | Como PIP-* complementa |
|---------|--------|-------------|------------------------|
| SRV-016 | Stage Automation Engine + Pipeline L2 | SubStatusPredictor, CandidateContextAggregator, bulk predict (backend AI) | PIP-002 define o modelo de `action_behavior` que SRV-016 consome. PIP-003/PIP-004 são a **camada React/UI** que invoca SRV-016 via API — SRV-016 é backend Python, PIP-003/004 são componentes frontend |
| AUT-005 | Cascata screening→feedback + ReturnEventService | 11 tipos de evento, auto-move | PIP-007 define o dispatch Layer 1 (determinístico) que precede o Layer 2 |
| AUT-006 | Cascata stage→interview/rejection + Pipeline L2 | Bulk reject com AI | PIP-010 define a barra de ações em massa (UI) que invoca AUT-006 |
| AGT-011 | CommunicationAgent | Multi-canal, bulk messages | PIP-007 dispara via CommunicationAgent; PIP-003 delega ao UnifiedCommunicationModal |
| INF-005 | EventDispatcher + WebhookAdapters | 3 adapters, idempotência | PIP-018 define timeouts/escalações que geram eventos para INF-005 |
| INF-012 | Feature Flags | ENABLE_LLM_*, ENABLE_WEBHOOK_* | PIP-013 usa flag para habilitar infer-behavior LLM |

---

## 3. Épicos

| Épico | Nome | Descrição |
|-------|------|-----------|
| **É24** | Pipeline & Transições — Modelo de Dados | Arquitetura de colunas, action_behavior, catálogo, CRUD de pipeline |
| **É25** | Pipeline & Transições — Frontend | UniversalTransitionModal, hooks, badges, drag-drop, ações em massa |
| **É26** | Pipeline & Transições — Configuração | Pipeline empresa, herança empresa→vaga, colunas customizadas, modais especializados |

---

## 4. Cards Alpha 1

> Cards essenciais para o MVP Alpha 1. Sem eles, o Kanban não funciona como pipeline de recrutamento.

---

### PIP-001: Arquitetura de 3 Camadas de Colunas + Catálogo

```yaml
Titulo: "[Pipeline] Arquitetura de 3 Camadas de Colunas + Catálogo de Etapas"
Tipo: Feature
Area: Backend + Frontend
Sprint: S1
Pontos: 8
Prioridade: Crítica
Epic: É24
Status: 📋 Pendente Jira
Fase: MVP Alpha 1
Referências IA: SRV-016 (consome action_behavior), INF-005 (cascatas usam stage_id)

Descricao: |
  Modelo de dados para colunas do pipeline com 3 camadas:
  
  1. **System** (3 colunas obrigatórias): Funil, Contratado, Reprovado
     - Presentes em toda vaga, não removíveis
  2. **Catalog** (13 colunas pré-configuradas): Triagem WSI, Entrevista RH,
     Teste Técnico, Avaliação Gestor, Proposta, etc.
     - Disponíveis para adicionar via catálogo
  3. **Custom** (ilimitadas): Criadas pelo recrutador via botão "+"
     - Com sugestão de action_behavior pela LIA (Alpha 2+)
  
  Cada coluna possui: id, name, slug, layer (system|catalog|custom),
  action_behavior, icon, order, sub_statuses[], is_removable, is_reorderable.
  
  Endpoint GET /api/v1/stage-catalog retorna catálogo completo.

Historia de Usuario: |
  Como recrutador, eu quero que o pipeline da minha vaga tenha etapas
  padrão (triagem, entrevista, teste) para organizar o processo seletivo.

Regras de Negocio:
  1. Colunas System NUNCA podem ser removidas ou reordenadas
  2. Colunas Catalog podem ser adicionadas/removidas livremente
  3. Cada coluna TEM um action_behavior que define seu comportamento nativo
  4. Sub-statuses são derivados do action_behavior (ver PIP-002)
  5. Ordem das colunas define o fluxo visual (esquerda→direita)
  6. Slug é único por vaga (snake_case do name)

Requisitos Tecnicos:
  Backend:
    - Tabela pipeline_stages (id, job_id, name, slug, layer, action_behavior,
      icon, order, sub_statuses JSONB, is_removable, is_reorderable)
    - Endpoint GET /api/v1/stage-catalog (catálogo estático ou DB)
    - Seed com 13 colunas catalog + 3 system
  Frontend:
    - Tipo PipelineStage com layer, action_behavior, sub_statuses
    - Hook usePipelineStages(jobId) com CRUD

DoD:
  - [ ] Modelo de dados pipeline_stages criado com 3 camadas
  - [ ] Catálogo de 13 colunas + 3 system populado
  - [ ] Endpoint GET /stage-catalog funcional
  - [ ] Tipo TypeScript PipelineStage definido
  - [ ] Testes unitários para CRUD de pipeline

Criterios de Aceitacao:
  - [ ] Vaga nova tem 3 colunas System (Funil, Contratado, Reprovado)
  - [ ] Recrutador pode adicionar colunas do catálogo ao pipeline
  - [ ] Colunas System não podem ser removidas (botão desabilitado)
  - [ ] Catálogo retorna 13 colunas com action_behavior e ícones

Arquivos de Referencia (Prototipo Replit):
  - spec: docs/pipeline-transition-system.md §2 (3 Camadas)
  - spec: docs/pipeline-transition-system.md §3 (Catálogo Completo)
  - spec: docs/pipeline-transition-system.md Apêndice B (Endpoints)
```

---

### PIP-002: Motor de action_behavior (10 Tipos + Sub-statuses)

```yaml
Titulo: "[Pipeline] Motor de action_behavior — 10 Tipos de Ação Nativa"
Tipo: Feature
Area: Backend + Frontend
Sprint: S1
Pontos: 8
Prioridade: Crítica
Epic: É24
Status: 📋 Pendente Jira
Fase: MVP Alpha 1
Referências IA: SRV-016 (SubStatusPredictor usa action_behavior para predição)

Descricao: |
  Engine que define o comportamento nativo de cada coluna do pipeline.
  Quando um candidato é movido para uma coluna, o sistema consulta o
  action_behavior para determinar: qual modal abrir, quais sub-statuses
  oferecer, qual ação automática disparar.
  
  10 tipos de action_behavior:
  1. intake — Análise inicial (Like/Dislike, Gate 1)
  2. screening — Triagem WSI (convite + acompanhamento)
  3. scheduling — Agendamento de entrevista
  4. evaluation — Avaliação técnica (teste, case study)
  5. verification — Verificação de dados/documentos
  6. offer — Proposta formal ao candidato
  7. passive — Sem ação (aguardando, banco de talentos)
  8. conclusion_hired — Contratação finalizada
  9. conclusion_rejected — Rejeição com feedback
  10. conclusion_declined — Candidato desistiu
  
  Cada tipo define: sub_statuses[], modal_type, channels[], auto_dispatch_eligible.

Historia de Usuario: |
  Como recrutador, eu quero que ao mover um candidato para "Entrevista RH"
  o sistema me ofereça automaticamente opções de agendamento, para que eu
  não precise lembrar qual ação tomar em cada etapa.

Regras de Negocio:
  1. Toda coluna TEM exatamente 1 action_behavior
  2. Sub-statuses são DERIVADOS do action_behavior (não configuráveis pelo usuário)
  3. A matriz action→modal→canal é determinística (ver pipeline-transition-system.md §5)
  4. Tipos conclusion_* são terminais (candidato SAI do pipeline ativo)
  5. intake é o único tipo com ação Like/Dislike (sem comunicação)

Requisitos Tecnicos:
  Backend:
    - Enum ActionBehavior com 10 valores
    - Mapeamento ACTION_BEHAVIOR_CONFIG: Dict[ActionBehavior, ActionConfig]
      onde ActionConfig = {sub_statuses, modal_type, channels, auto_dispatch}
    - Validação: action_behavior é obrigatório em toda coluna
  Frontend:
    - Map de action_behavior→configuração para rendering condicional
    - useActionBehavior(stageId) hook que retorna config completa

DoD:
  - [ ] Enum ActionBehavior com 10 tipos
  - [ ] Mapeamento completo de sub-statuses por tipo
  - [ ] Matriz ação→modal→canal implementada
  - [ ] Hook frontend useActionBehavior funcional
  - [ ] Testes para todos os 10 tipos

Criterios de Aceitacao:
  - [ ] Coluna "Triagem WSI" retorna action_behavior=screening com sub-statuses corretos
  - [ ] Coluna "Proposta" retorna action_behavior=offer com sub-statuses de proposta
  - [ ] Tentativa de criar coluna sem action_behavior retorna erro 400

Arquivos de Referencia (Prototipo Replit):
  - spec: docs/pipeline-transition-system.md §4 (action_behavior)
  - spec: docs/pipeline-transition-system.md §5 (Matriz Ação→Modal→Canal)
```

---

### PIP-003: UniversalTransitionModal (Hub Frontend de Transições)

> **⚠️ Escopo vs SRV-016:** Este card cobre o **componente React** (UI, estado, rendering, delegação a modais). SRV-016 cobre o **backend Python** (SubStatusPredictor, CandidateContextAggregator). PIP-003 *invoca* SRV-016 via API — não duplica sua lógica.

```yaml
Titulo: "[Pipeline] UniversalTransitionModal — Hub de Transições (Frontend)"
Tipo: Feature
Area: Frontend
Sprint: S2
Pontos: 8
Prioridade: Crítica
Epic: É25
Status: 📋 Pendente Jira
Fase: MVP Alpha 1
Referências IA: SRV-016 (SubStatusPredictor — chamado via API), AGT-011 (CommunicationAgent via dispatch)

Descricao: |
  Componente React (~527L) que é o ponto de entrada de TODA movimentação
  de candidato no pipeline. Aparece ao mover candidato via drag-drop ou dropdown.
  
  Estrutura do modal:
  ┌────────────────────────────────────────┐
  │ Header: "Candidato → Etapa Destino"    │
  │ 🧠 Brain icon (#60BED1) se AI ativo    │
  ├────────────────────────────────────────┤
  │ Sub-status: dropdown com opções        │
  │ derivadas do action_behavior           │
  ├────────────────────────────────────────┤
  │ Mini-prompt: campo texto livre         │
  │ (contexto para LIA ou modal manual)    │
  ├────────────────────────────────────────┤
  │ Ação:                                  │
  │ ● LIA auto (dispara automaticamente)   │
  │ ○ Manual (abre modal especializado)    │
  ├────────────────────────────────────────┤
  │ [Confirmar]  [Cancelar]                │
  └────────────────────────────────────────┘
  
  Princípio: NUNCA duplica lógica de modais existentes — DELEGA via
  handleOpenSpecializedModal que abre o modal correto por action_behavior.

Historia de Usuario: |
  Como recrutador, eu quero que ao arrastar um candidato para outra coluna
  um modal me pergunte o sub-status e me ofereça a opção de deixar a LIA
  executar a ação automaticamente ou abrir o modal completo.

Regras de Negocio:
  1. Modal aparece em TODA movimentação (exceto passive → move direto)
  2. Sub-status dropdown mostra opções do action_behavior destino
  3. Mini-prompt é OPCIONAL (personalização em linguagem natural)
  4. Modo LIA auto: dispara ação sem abrir modal especializado
  5. Modo Manual: abre modal especializado correspondente
  6. Brain icon (#60BED1) indica que IA está disponível para a ação
  7. Modal é COMPACTO (~250px largura) — delegação, não duplicação

Requisitos Tecnicos:
  Frontend:
    - Componente UniversalTransitionModal com props:
      candidateId, sourceStage, targetStage, onConfirm, onCancel
    - Integração com useTransitionContext hook (PIP-004)
    - Mapeamento handleOpenSpecializedModal por action_behavior:
      intake → CandidateDecisionFlowModal
      screening → WSITriagemInviteModal
      scheduling → UnifiedCommunicationModal (agendamento)
      evaluation → UnifiedCommunicationModal (avaliação)
      verification → DataRequestModal
      offer → UnifiedCommunicationModal (proposta)
      conclusion_rejected → CandidateDecisionFlowModal + feedback
      conclusion_declined → inline radio (motivo)

DoD:
  - [ ] Modal renderiza com header, sub-status, mini-prompt, ação
  - [ ] Delegação para 7+ modais especializados funcional
  - [ ] Brain icon aparece quando AI está disponível
  - [ ] Modo LIA auto dispara TransitionDispatchService (PIP-007)
  - [ ] Testes para cada action_behavior

Criterios de Aceitacao:
  - [ ] Drag-drop de candidato abre UniversalTransitionModal
  - [ ] Sub-status mostra opções corretas por coluna destino
  - [ ] Botão "Manual" abre WSITriagemInviteModal ao mover para Triagem
  - [ ] Botão "LIA auto" dispara email+WhatsApp sem abrir modal

Arquivos de Referencia (Prototipo Replit):
  - file: plataforma-lia/src/components/kanban/components/UniversalTransitionModal.tsx (527L)
  - spec: docs/pipeline-transition-system.md §7 (Design Compacto)
  - spec: docs/pipeline-transition-system.md §10 (Integração com Modais)
```

---

### PIP-004: use-transition-context Hook (Estado de Transição)

> **⚠️ Escopo vs SRV-016:** Este card cobre o **hook React** (estado local, context provider). SRV-016 cobre os **endpoints backend** que este hook consome. Sem sobreposição — camadas diferentes (frontend vs backend).

```yaml
Titulo: "[Pipeline] use-transition-context — Hook de Estado de Transição"
Tipo: Feature
Area: Frontend
Sprint: S2
Pontos: 5
Prioridade: Alta
Epic: É25
Status: 📋 Pendente Jira
Fase: MVP Alpha 1
Referências IA: SRV-016 (predict-substatus chamado pelo hook)

Descricao: |
  Hook React (~694L) que gerencia todo o estado de uma transição de candidato.
  Centraliza: candidato selecionado, etapa origem/destino, sub-status escolhido,
  mini-prompt, modo (LIA auto vs manual), loading, erros.
  
  Responsabilidades:
  - Carregar config do action_behavior da etapa destino
  - Gerenciar sub-status selecionado
  - Chamar API de transição (POST /candidates/{id}/transition)
  - Chamar predict-substatus (SRV-016) quando AI está habilitado
  - Gerenciar estado de loading/error/success
  - Resetar estado ao fechar modal

Historia de Usuario: |
  Como desenvolvedor, eu quero um hook centralizado para o estado de
  transição, para que o UniversalTransitionModal e os modais especializados
  compartilhem o mesmo estado sem prop drilling.

Requisitos Tecnicos:
  Frontend:
    - Hook useTransitionContext(candidateId, targetStageId)
    - Retorna: { subStatus, setSubStatus, miniPrompt, setMiniPrompt,
      mode, setMode, actionConfig, isAiAvailable, execute, isLoading, error }
    - Context provider TransitionContextProvider para compartilhar entre modais
    - Chamada ao backend: POST /api/v1/candidates/{id}/transition
    - Chamada AI: POST /api/v1/stage-transition/predict-substatus (opcional)

DoD:
  - [ ] Hook funcional com estado completo de transição
  - [ ] Context provider para compartilhamento entre componentes
  - [ ] Integração com API de transição
  - [ ] Integração com predict-substatus (quando AI disponível)
  - [ ] Testes unitários

Criterios de Aceitacao:
  - [ ] Modal e modais especializados compartilham mesmo estado via context
  - [ ] Transição executada via hook atualiza Kanban em tempo real
  - [ ] Erro na API exibe mensagem de erro no modal

Arquivos de Referencia (Prototipo Replit):
  - file: plataforma-lia/src/hooks/use-transition-context.ts (694L)
  - spec: docs/pipeline-transition-system.md §7 (Modal + Estado)
```

---

### PIP-005: Movimentação Livre (Drag-Drop + Dropdown)

```yaml
Titulo: "[Pipeline] Movimentação Livre — Drag-Drop e Dropdown"
Tipo: Feature
Area: Frontend
Sprint: S2
Pontos: 5
Prioridade: Crítica
Epic: É25
Status: 📋 Pendente Jira
Fase: MVP Alpha 1
Referências IA: Nenhuma (feature puramente frontend)

Descricao: |
  O candidato pode ser movido para QUALQUER coluna do pipeline a qualquer
  momento, sem restrições de transição. Duas interfaces de movimentação:
  
  1. **Drag-and-drop no Kanban**: arrastar card do candidato entre colunas
  2. **Dropdown na Tabela**: selecionar etapa destino via dropdown na linha
  
  Ambos disparam o UniversalTransitionModal (PIP-003) antes de confirmar.

Historia de Usuario: |
  Como recrutador, eu quero arrastar candidatos livremente entre colunas
  do Kanban, sem bloqueios de ordem, para ter flexibilidade no processo.

Regras de Negocio:
  1. QUALQUER coluna → QUALQUER coluna (sem rotas restritas)
  2. Movimentação para mesma coluna é ignorada (no-op)
  3. Ao soltar na coluna, abre UniversalTransitionModal
  4. Se coluna destino é passive → move direto SEM modal
  5. Movimentação em massa: selecionar múltiplos → mesma coluna destino
  6. Candidato mantém histórico de movimentações (stage_history)

Requisitos Tecnicos:
  Frontend:
    - Hook useDragDrop com @dnd-kit ou react-beautiful-dnd
    - Integração com UniversalTransitionModal ao drop
    - Dropdown de etapas na view Tabela com onChange → modal
    - Optimistic update no Kanban (mover card antes da confirmação API)
  Backend:
    - Registro de stage_history: {from_stage, to_stage, timestamp, user_id, sub_status}

DoD:
  - [ ] Drag-drop funcional entre colunas do Kanban
  - [ ] Dropdown de etapas na Tabela funcional
  - [ ] Ambos abrem UniversalTransitionModal
  - [ ] Passive columns movem sem modal
  - [ ] stage_history registrado a cada movimentação

Criterios de Aceitacao:
  - [ ] Candidato pode ser arrastado de "Funil" para "Proposta" diretamente
  - [ ] Dropdown na tabela mostra todas as colunas do pipeline
  - [ ] Coluna "Aguardando Documentos" (passive) move sem modal

Arquivos de Referencia (Prototipo Replit):
  - spec: docs/pipeline-transition-system.md §6 (Movimentação Livre)
```

---

### PIP-006: Sistema de Badges nos Cards do Kanban

```yaml
Titulo: "[Pipeline] Sistema de Badges nos Cards do Kanban"
Tipo: Feature
Area: Frontend
Sprint: S2
Pontos: 5
Prioridade: Alta
Epic: É25
Status: 📋 Pendente Jira
Fase: MVP Alpha 1
Referências IA: SRV-016 (sub-status usado nos badges), AUT-005 (return events atualizam badges)

Descricao: |
  Sistema de indicadores visuais nos cards de candidatos no Kanban.
  5 tipos de badge, derivados de f(action_behavior, sub_status, timestamps, activity):
  
  1. **Sub-status**: Estado atual dentro da coluna (ex: "Agendada", "Em análise")
     - Cores por categoria: info (azul), warning (amarelo), success (verde), error (vermelho)
  2. **Ação pendente candidato**: Candidato precisa responder/agir
     - Ex: "Aguardando resposta", "Teste pendente", "Documentos pendentes"
  3. **Ação pendente recrutador**: Recrutador precisa tomar decisão
     - Ex: "Avaliar resultado", "Revisar proposta", "Confirmar entrevista"
  4. **Alerta temporal**: Timeout se aproximando ou expirado
     - Ex: "3 dias sem resposta", "Prazo vencido"
  5. **Conclusão**: Status terminal do candidato
     - Ex: "Contratado", "Reprovado", "Desistiu"

Historia de Usuario: |
  Como recrutador, eu quero ver badges nos cards dos candidatos indicando
  o status detalhado e ações pendentes, para priorizar meu trabalho.

Regras de Negocio:
  1. Badge é CALCULADO automaticamente (não definido manualmente)
  2. Prioridade de exibição: alerta temporal > ação pendente > sub-status
  3. Máximo 2 badges visíveis por card (mais → tooltip)
  4. Badges se atualizam em tempo real (WebSocket ou polling)
  5. Cores seguem paleta: info=#3B82F6, warning=#F59E0B, success=#10B981, error=#EF4444

Requisitos Tecnicos:
  Frontend:
    - Componente CandidateBadge com variant (sub_status|pending_candidate|pending_recruiter|alert|conclusion)
    - Função computeBadges(candidate, stage) → Badge[]
    - Integração com Kanban card (max 2 visíveis + overflow)
  Backend:
    - Endpoint ou campo calculado que retorna badges por candidato
    - Lógica de timeout baseada em timestamps de última atividade

DoD:
  - [ ] 5 tipos de badge implementados
  - [ ] computeBadges funcional para todos os action_behaviors
  - [ ] Badges visíveis nos cards do Kanban
  - [ ] Prioridade de exibição correta
  - [ ] Testes para cálculo de badges

Criterios de Aceitacao:
  - [ ] Candidato em "Triagem WSI" com resposta pendente mostra badge amarelo "Aguardando resposta"
  - [ ] Candidato sem resposta há 3 dias mostra badge vermelho "3 dias sem resposta"
  - [ ] Candidato contratado mostra badge verde "Contratado"

Arquivos de Referencia (Prototipo Replit):
  - spec: docs/pipeline-transition-system.md §11 (Badges)
```

---

### PIP-007: TransitionDispatchService (Layer 1 — Determinístico)

```yaml
Titulo: "[Pipeline] TransitionDispatchService — Disparos Automáticos Layer 1"
Tipo: Feature
Area: Backend
Sprint: S2
Pontos: 8
Prioridade: Alta
Epic: É24
Status: 📋 Pendente Jira
Fase: MVP Alpha 1
Referências IA: AGT-011 (CommunicationAgent executa envio), SRV-016 (Layer 2 estende este serviço)

Descricao: |
  Serviço backend que executa disparos automáticos quando o recrutador
  escolhe modo "LIA auto" no UniversalTransitionModal.
  
  Layer 1 = Determinístico (sem LLM):
  1. Consulta action_behavior da coluna destino
  2. Seleciona template de mensagem por (action_behavior + sub_status)
  3. Renderiza template com dados do candidato e da vaga
  4. Envia via canais configurados (Email + WhatsApp)
  
  Fluxo: action_behavior → template_selector → template_renderer → channel_dispatcher
  
  Layer 2 (LLM, coberto por SRV-016 + AUT-006):
  - Interpretação do mini-prompt por LLM
  - Personalização de mensagem por IA
  - Predição de sub-status

Historia de Usuario: |
  Como recrutador, eu quero que ao escolher "LIA auto" no modal de transição,
  a LIA envie automaticamente a mensagem correta por email e WhatsApp,
  sem que eu precise configurar nada manualmente.

Regras de Negocio:
  1. Layer 1 é DETERMINÍSTICO (sem chamada LLM)
  2. Template selecionado por (action_behavior, sub_status, canal)
  3. Canais: Email + WhatsApp (exceto offer/hired → apenas Email)
  4. Renderização: {{candidato_nome}}, {{vaga_titulo}}, {{empresa_nome}}, etc.
  5. Disparo registrado em activity_log com {channel, template_id, timestamp}
  6. Se template não encontrado → log warning, não bloqueia transição

Requisitos Tecnicos:
  Backend:
    - TransitionDispatchService com dispatch(candidate_id, stage_id, sub_status, mini_prompt)
    - TemplateSelector: busca template por (action_behavior, sub_status, canal)
    - TemplateRenderer: Jinja2/Mustache com variáveis de candidato+vaga
    - ChannelDispatcher: envia via Email (Mailgun) + WhatsApp
    - Tabela dispatch_log (candidate_id, stage_id, channel, template_id, status, timestamp)

DoD:
  - [ ] TransitionDispatchService funcional
  - [ ] Templates para os 6 action_behaviors com comunicação
  - [ ] Envio por Email funcional
  - [ ] Envio por WhatsApp funcional
  - [ ] Registro em dispatch_log
  - [ ] Testes end-to-end de disparo

Criterios de Aceitacao:
  - [ ] "LIA auto" em Triagem WSI → candidato recebe email com link de triagem
  - [ ] "LIA auto" em Entrevista → candidato recebe email+WhatsApp com detalhes
  - [ ] "LIA auto" em Proposta → candidato recebe APENAS email com proposta
  - [ ] Dispatch sem template não bloqueia a movimentação

Arquivos de Referencia (Prototipo Replit):
  - spec: docs/pipeline-transition-system.md §12 (Disparos Automáticos)
```

---

### PIP-008: Endpoints de Transição (API)

```yaml
Titulo: "[Pipeline] Endpoints de Transição — API REST"
Tipo: Feature
Area: Backend
Sprint: S1
Pontos: 5
Prioridade: Crítica
Epic: É24
Status: 📋 Pendente Jira
Fase: MVP Alpha 1
Referências IA: SRV-016 (endpoint predict-substatus), INF-005 (event dispatch pós-transição)

Descricao: |
  Endpoints REST para movimentação de candidatos no pipeline.
  
  Endpoints:
  1. POST /api/v1/candidates/{id}/transition
     Body: { target_stage_id, sub_status?, mini_prompt?, mode: "auto"|"manual" }
     - Executa transição, registra stage_history, dispara eventos
  
  2. POST /api/v1/transition/interpret-context (Alpha 2+)
     Body: { mini_prompt, candidate_id, target_stage_id }
     - LLM interpreta mini-prompt e retorna ação sugerida
  
  3. GET /api/v1/jobs/{id}/pipeline
     - Retorna pipeline completo da vaga com colunas e candidatos por coluna
  
  4. PUT /api/v1/jobs/{id}/pipeline
     - Reordena/adiciona/remove colunas do pipeline da vaga

Historia de Usuario: |
  Como sistema, eu preciso de endpoints para executar transições de
  candidatos e gerenciar o pipeline de vagas.

Requisitos Tecnicos:
  Backend:
    - POST /candidates/{id}/transition com validação de stage existente
    - Registro em candidate_stage_history (from_stage, to_stage, timestamp, user_id, sub_status, mini_prompt)
    - Disparo de evento stage_changed para EventDispatcher (INF-005)
    - GET/PUT /jobs/{id}/pipeline com CRUD de colunas
    - Autenticação e autorização por tenant_id

DoD:
  - [ ] POST /candidates/{id}/transition funcional
  - [ ] GET /jobs/{id}/pipeline retorna pipeline completo
  - [ ] PUT /jobs/{id}/pipeline atualiza colunas
  - [ ] stage_history registrado
  - [ ] Evento stage_changed disparado após transição

Criterios de Aceitacao:
  - [ ] Transição retorna 200 com novo estado do candidato
  - [ ] Transição para stage inexistente retorna 404
  - [ ] stage_history contém registro de toda movimentação
  - [ ] Evento stage_changed recebido pelo EventDispatcher

Arquivos de Referencia (Prototipo Replit):
  - file: lia-agent-system/app/api/v1/stage_transition_automation.py (547L)
  - spec: docs/pipeline-transition-system.md Apêndice B (Endpoints)
```

---

### PIP-009: Pipeline CRUD por Vaga

```yaml
Titulo: "[Pipeline] Pipeline CRUD — Gestão de Colunas por Vaga"
Tipo: Feature
Area: Backend + Frontend
Sprint: S1
Pontos: 5
Prioridade: Alta
Epic: É24
Status: 📋 Pendente Jira
Fase: MVP Alpha 1
Referências IA: Nenhuma (CRUD puro sem IA)

Descricao: |
  Interface e API para o recrutador gerenciar as colunas do pipeline de uma vaga.
  
  Operações:
  - Adicionar coluna do catálogo ao pipeline
  - Remover coluna do pipeline (exceto System)
  - Reordenar colunas (drag-drop horizontal)
  - Renomear coluna (exceto System)
  
  No Alpha 1, o pipeline é definido por vaga (sem herança empresa).
  Herança empresa→vaga é Alpha 2+ (PIP-012).

Historia de Usuario: |
  Como recrutador, eu quero customizar as etapas do pipeline da minha vaga
  adicionando ou removendo colunas, para adaptar o processo seletivo.

Regras de Negocio:
  1. Colunas System NÃO podem ser removidas nem renomeadas
  2. Colunas podem ser reordenadas livremente (exceto System fixas)
  3. Mínimo: 3 colunas System sempre presentes
  4. Máximo: 20 colunas por pipeline (System + Catalog + Custom)
  5. Candidatos em coluna removida são movidos para "Funil"

Requisitos Tecnicos:
  Frontend:
    - Pipeline editor no header do Kanban
    - Botão "+" para adicionar coluna → modal com catálogo
    - Drag-drop horizontal para reordenação
    - Botão "x" para remover (com confirmação se há candidatos)
  Backend:
    - PUT /api/v1/jobs/{id}/pipeline para bulk update de order
    - POST /api/v1/jobs/{id}/pipeline/stages para adicionar
    - DELETE /api/v1/jobs/{id}/pipeline/stages/{stageId} para remover

DoD:
  - [ ] Adicionar coluna do catálogo funcional
  - [ ] Remover coluna com migração de candidatos
  - [ ] Reordenação drag-drop funcional
  - [ ] Validações de limite e proteção System

Criterios de Aceitacao:
  - [ ] Recrutador adiciona "Teste Técnico" do catálogo ao pipeline
  - [ ] Tentar remover "Funil" mostra erro (coluna System)
  - [ ] Remover coluna com 3 candidatos move todos para Funil
  - [ ] Reordenação persiste após reload

Arquivos de Referencia (Prototipo Replit):
  - spec: docs/pipeline-transition-system.md §2, §3 (Colunas)
  - spec: docs/pipeline-transition-system.md Apêndice B (Endpoints)
```

---

### PIP-010: Barra de Ações em Massa

```yaml
Titulo: "[Pipeline] Barra de Ações em Massa — Seleção Múltipla"
Tipo: Feature
Area: Frontend
Sprint: S2
Pontos: 5
Prioridade: Alta
Epic: É25
Status: 📋 Pendente Jira
Fase: MVP Alpha 1
Referências IA: AUT-006 (bulk reject com AI), AGT-011 (bulk messages)

Descricao: |
  Barra de ações que aparece ao selecionar múltiplos candidatos no Kanban
  ou na Tabela. Cada botão abre o modal correspondente em modo bulk.
  
  Ações disponíveis:
  - → Mover Etapa → UniversalTransitionModal (bulk)
  - 📋 Triagem WSI → WSITriagemInviteModal (bulk)
  - 📅 Agendar → UnifiedCommunicationModal (type=agendamento, bulk)
  - 📄 Solicitar Dados → DataRequestModal (bulk)
  - ✉️ Email → UnifiedCommunicationModal (type=email, bulk)
  - 💬 WhatsApp → UnifiedCommunicationModal (type=whatsapp, bulk)
  - 📝 Feedback → UnifiedCommunicationModal (type=feedback, bulk)
  - 🤖 Análise LIA → Análise comparativa em lote
  - 🔴 Reprovar → CandidateDecisionFlowModal (reject, bulk)

Historia de Usuario: |
  Como recrutador, eu quero selecionar vários candidatos e aplicar
  a mesma ação a todos de uma vez, para economizar tempo.

Regras de Negocio:
  1. Barra aparece ao selecionar ≥2 candidatos
  2. Máximo de seleção: 100 candidatos por vez
  3. "× Limpar" reseta seleção
  4. "○ Selecionar todos" seleciona todos da coluna ou filtro
  5. Contador mostra "N candidatos selecionados de M"
  6. Ações abrem modais em modo bulk (lista de candidate_ids)
  7. Bulk reject pode usar SubStatusPredictor (SRV-016) para individualizar

Requisitos Tecnicos:
  Frontend:
    - Componente BulkActionsBar com selectedCandidateIds[]
    - Checkbox de seleção em cada card/row
    - Botões por ação com ícone + label
    - Passagem de candidateIds[] para modais em modo bulk
  Backend:
    - Endpoints de transição aceitam candidate_ids[] (bulk)
    - POST /api/v1/candidates/bulk-transition

DoD:
  - [ ] Barra de ações aparece ao selecionar ≥2 candidatos
  - [ ] 9 ações funcionais em modo bulk
  - [ ] Selecionar todos / limpar seleção
  - [ ] Modais recebem lista de candidatos
  - [ ] Endpoint bulk-transition funcional

Criterios de Aceitacao:
  - [ ] Selecionar 5 candidatos → barra mostra "5 candidatos selecionados"
  - [ ] "Reprovar" em massa → CandidateDecisionFlowModal com 5 candidatos
  - [ ] "Mover Etapa" → UniversalTransitionModal aplica a todos
  - [ ] Máximo 100: tentativa de selecionar 101 mostra aviso

Arquivos de Referencia (Prototipo Replit):
  - spec: docs/pipeline-transition-system.md Apêndice A (Barra de Ações em Massa)
```

---

## 5. Cards Alpha 2+

> Cards de refinamento e features avançadas. Não bloqueiam o Alpha 1 mas enriquecem significativamente a experiência.

---

### PIP-011: Pipeline Padrão da Empresa (Menu Configurações)

```yaml
Titulo: "[Pipeline] Pipeline Padrão da Empresa — Menu Configurações"
Tipo: Feature
Area: Backend + Frontend
Sprint: S3
Pontos: 5
Prioridade: Média
Epic: É26
Status: 📋 Pendente Jira
Fase: Alpha 2
Referências IA: Nenhuma (CRUD puro sem IA)

Descricao: |
  Tela no Menu Configurações para o admin da empresa definir o pipeline
  padrão que será herdado por todas as novas vagas.
  
  Funcionalidades:
  - Listar colunas do pipeline padrão da empresa
  - Adicionar/remover colunas do catálogo
  - Reordenar colunas
  - Definir configurações de comunicação por coluna
  - Salvar como template da empresa

Historia de Usuario: |
  Como administrador da empresa, eu quero definir um pipeline padrão
  para que todas as novas vagas comecem com as mesmas etapas.

Requisitos Tecnicos:
  Backend:
    - Tabela company_pipeline_template (company_id, stages JSONB)
    - GET/PUT /api/v1/company/{id}/pipeline
    - POST /api/v1/company/{id}/pipeline/stages
  Frontend:
    - Tela em Configurações → Pipeline → Editor visual
    - Reutiliza componentes de PIP-009

DoD:
  - [ ] Tela de configuração de pipeline da empresa
  - [ ] CRUD de colunas no pipeline template
  - [ ] Template persiste e é consultável

Criterios de Aceitacao:
  - [ ] Admin define pipeline com 8 colunas → salva com sucesso
  - [ ] Template aparece ao criar nova vaga (PIP-012)

Arquivos de Referencia (Prototipo Replit):
  - spec: docs/pipeline-transition-system.md §15 (Menu Configurações)
```

---

### PIP-012: Herança de Pipeline — Empresa → Vaga

```yaml
Titulo: "[Pipeline] Herança de Pipeline — Empresa → Vaga (Copy-on-Write)"
Tipo: Feature
Area: Backend
Sprint: S3
Pontos: 5
Prioridade: Média
Epic: É26
Status: 📋 Pendente Jira
Fase: Alpha 2
Referências IA: Nenhuma (lógica de herança pura)

Descricao: |
  Ao criar nova vaga, o pipeline é COPIADO do template da empresa.
  A vaga pode customizar seu pipeline sem afetar o template.
  
  Regras de herança:
  1. Nova vaga → copia pipeline da empresa (snapshot)
  2. Alteração na vaga → desvincula do template (copy-on-write)
  3. Alteração no template empresa → NÃO afeta vagas existentes
  4. Vaga pode "resetar" pipeline para o template atual da empresa

Historia de Usuario: |
  Como recrutador, eu quero que novas vagas comecem com o pipeline
  padrão da empresa, e que eu possa customizar sem afetar outras vagas.

Requisitos Tecnicos:
  Backend:
    - Lógica de copy-on-write ao criar vaga
    - Campo is_customized em job_pipeline para indicar desvio
    - Endpoint POST /api/v1/jobs/{id}/pipeline/reset-to-company

DoD:
  - [ ] Nova vaga herda pipeline da empresa
  - [ ] Customização na vaga não afeta template
  - [ ] Reset para template funcional

Criterios de Aceitacao:
  - [ ] Criar vaga → pipeline igual ao template empresa
  - [ ] Adicionar coluna na vaga → is_customized=true
  - [ ] Alterar template empresa → vagas existentes não mudam

Arquivos de Referencia (Prototipo Replit):
  - spec: docs/pipeline-transition-system.md §14 (Herança)
```

---

### PIP-013: Criação de Colunas Customizadas com LIA (Infer-Behavior)

```yaml
Titulo: "[Pipeline] Criação de Colunas Customizadas — LIA sugere action_behavior"
Tipo: Feature
Area: Backend + Frontend
Sprint: S3
Pontos: 5
Prioridade: Média
Epic: É26
Status: 📋 Pendente Jira
Fase: Alpha 2
Referências IA: SRV-016 (LLM inference), INF-012 (feature flag ENABLE_INFER_BEHAVIOR)

Descricao: |
  Recrutador clica "+" no Kanban → digita nome da coluna → LIA sugere
  action_behavior automaticamente via LLM.
  
  Fluxo:
  1. Recrutador clica "+" entre colunas
  2. Input: nome da coluna (ex: "Dinâmica de Grupo")
  3. POST /api/v1/stages/infer-behavior { name: "Dinâmica de Grupo" }
  4. LIA retorna: { action_behavior: "evaluation", confidence: 0.92, reasoning: "..." }
  5. Recrutador confirma ou altera o action_behavior sugerido
  6. Coluna criada com layer=custom

Historia de Usuario: |
  Como recrutador, eu quero criar etapas personalizadas no meu pipeline
  e ter a LIA sugerindo o tipo de ação, para não precisar configurar manualmente.

Requisitos Tecnicos:
  Backend:
    - Endpoint POST /api/v1/stages/infer-behavior
    - LLM prompt: "Dado o nome da coluna '{name}', classifique em um dos 10 action_behaviors..."
    - Feature flag ENABLE_INFER_BEHAVIOR (default: true)
    - Fallback: se LLM falha → retorna action_behavior=passive
  Frontend:
    - Botão "+" entre colunas no Kanban
    - Modal: input nome + dropdown action_behavior (com sugestão AI highlighted)

DoD:
  - [ ] Botão "+" funcional no Kanban
  - [ ] Endpoint infer-behavior com LLM
  - [ ] Modal com sugestão AI e override manual
  - [ ] Coluna custom criada no pipeline

Criterios de Aceitacao:
  - [ ] "Dinâmica de Grupo" → LIA sugere evaluation com 90%+ confiança
  - [ ] "Aguardando Retorno" → LIA sugere passive
  - [ ] Recrutador pode mudar sugestão via dropdown

Arquivos de Referencia (Prototipo Replit):
  - spec: docs/pipeline-transition-system.md §16 (Colunas Customizadas)
```

---

### PIP-014: TestSendModal (Envio de Testes)

```yaml
Titulo: "[Pipeline] TestSendModal — Modal de Envio de Testes Técnicos"
Tipo: Feature
Area: Frontend
Sprint: S3
Pontos: 5
Prioridade: Alta
Epic: É26
Status: 📋 Pendente Jira
Fase: Alpha 2
Referências IA: AGT-011 (envio via CommunicationAgent)

Descricao: |
  Modal dedicado (~300L) para envio de testes técnicos ao candidato.
  Substitui o uso genérico do UnifiedCommunicationModal para action_behavior=evaluation.
  
  Campos:
  - Tipo de teste: Técnico / Case Prático / Inglês / Personalizado
  - Link do teste OU upload de arquivo
  - Prazo para entrega (dias)
  - Instruções adicionais (campo texto)
  - Canal (Email / WhatsApp)
  - Template de envio (filtrado por situation=avaliacao_tecnica)
  - Preview da mensagem
  - Envio com confirmação

Historia de Usuario: |
  Como recrutador, eu quero enviar testes técnicos aos candidatos com
  prazo e instruções claras, em vez de usar um email genérico.

DoD:
  - [ ] Modal com campos de tipo, link/upload, prazo, instruções
  - [ ] Preview da mensagem antes de enviar
  - [ ] Envio via Email ou WhatsApp
  - [ ] Registro de teste enviado no candidate_activity

Criterios de Aceitacao:
  - [ ] Mover candidato para "Teste Técnico" → botão Manual abre TestSendModal
  - [ ] Teste enviado com prazo de 3 dias → badge "Teste pendente" aparece

Arquivos de Referencia (Prototipo Replit):
  - spec: docs/pipeline-transition-system.md §19 Gap 1 (TestSendModal)
```

---

### PIP-015: ProposalModal (Proposta Formal)

```yaml
Titulo: "[Pipeline] ProposalModal — Modal de Proposta Formal ao Candidato"
Tipo: Feature
Area: Frontend
Sprint: S3
Pontos: 5
Prioridade: Alta
Epic: É26
Status: 📋 Pendente Jira
Fase: Alpha 2
Referências IA: AGT-011 (envio via CommunicationAgent)

Descricao: |
  Modal dedicado (~200L+) para envio de proposta formal ao candidato.
  Substitui o uso genérico do UnifiedCommunicationModal para action_behavior=offer.
  
  Campos adicionais:
  - Salário (valor + moeda + periodicidade)
  - Modelo de contratação (CLT / PJ / Cooperativa / Estágio)
  - Benefícios (seleção múltipla do catálogo da empresa)
  - Data de início prevista
  - Prazo para resposta (dias)
  - Bônus / variável (opcional)
  - Template de proposta específico
  - Geração de PDF formal (futuro)

Historia de Usuario: |
  Como recrutador, eu quero enviar uma proposta formal estruturada
  com salário, benefícios e modelo de contratação, não apenas um email.

DoD:
  - [ ] Modal com campos estruturados de proposta
  - [ ] Benefícios carregados do catálogo da empresa
  - [ ] Envio via Email
  - [ ] Registro de proposta no candidate_activity

Criterios de Aceitacao:
  - [ ] Mover para "Proposta" → botão Manual abre ProposalModal
  - [ ] Proposta com salário R$ 15.000 CLT + 5 benefícios → enviada com sucesso
  - [ ] Badge "Proposta enviada" aparece no card

Arquivos de Referencia (Prototipo Replit):
  - spec: docs/pipeline-transition-system.md §19 Gap 2 (ProposalModal)
```

---

### PIP-016: SchedulingModal Dedicado (Integração Calendário)

```yaml
Titulo: "[Pipeline] SchedulingModal — Agendamento com Calendário Integrado"
Tipo: Feature
Area: Frontend + Backend
Sprint: S4
Pontos: 8
Prioridade: Média
Epic: É26
Status: 📋 Pendente Jira
Fase: Alpha 2+
Referências IA: AGT-003 (SchedulingAgent), SRV-010 (Calendar Service), INT-AI-005 (MS Graph)

Descricao: |
  Modal dedicado para agendamento de entrevistas com integração de calendário.
  Substitui o uso do UnifiedCommunicationModal para action_behavior=scheduling.
  
  Funcionalidade:
  - Tipo de entrevista (RH / Técnica / Gestor / Final)
  - Plataforma (Zoom / Meet / Teams / Presencial)
  - Duração (30min / 1h / 1h30 / 2h)
  - Seleção de entrevistador (lista da empresa)
  - Calendário visual com disponibilidade
  - Data e horário selecionados
  - Link automático da plataforma
  - Template pré-preenchido
  - Integração com Google Calendar / Outlook

Historia de Usuario: |
  Como recrutador, eu quero agendar entrevistas vendo a disponibilidade
  do entrevistador e do candidato, e gerando link automaticamente.

DoD:
  - [ ] Modal com seleção de tipo, plataforma, duração
  - [ ] Calendário visual com slots disponíveis
  - [ ] Link da reunião gerado automaticamente
  - [ ] Email de convite enviado ao candidato

Criterios de Aceitacao:
  - [ ] Mover para "Entrevista RH" → Manual abre SchedulingModal
  - [ ] Selecionar slot → email enviado com link Teams
  - [ ] Badge "Entrevista agendada 22/02 14h" aparece

Arquivos de Referencia (Prototipo Replit):
  - spec: docs/pipeline-transition-system.md §19 Gap 3 (SchedulingModal)
```

---

### PIP-017: Mini-Prompt LLM Interpretation (Layer 2 Dispatch)

```yaml
Titulo: "[Pipeline] Mini-Prompt LLM — Interpretação Layer 2 do Dispatch"
Tipo: Feature
Area: Backend
Sprint: S3
Pontos: 5
Prioridade: Média
Epic: É24
Status: 📋 Pendente Jira
Fase: Alpha 2
Referências IA: SRV-016 (LLM inference), AGT-011 (personalização de mensagem)

Descricao: |
  Interpretação por LLM do mini-prompt escrito pelo recrutador no
  UniversalTransitionModal. Estende o Layer 1 (determinístico) com
  personalização inteligente.
  
  Endpoint: POST /api/v1/transition/interpret-context
  Body: { mini_prompt, candidate_id, target_stage_id }
  Response: { suggested_action, personalized_message, confidence }
  
  Exemplos:
  - "Agendar entrevista técnica com o João para semana que vem"
    → { action: "schedule", params: { type: "tecnica", week: "next" } }
  - "Enviar teste de Python com prazo de 5 dias"
    → { action: "send_test", params: { type: "python", deadline_days: 5 } }

Historia de Usuario: |
  Como recrutador, eu quero escrever instruções em linguagem natural
  no mini-prompt e ter a LIA interpretando e executando a ação correta.

DoD:
  - [ ] Endpoint interpret-context funcional
  - [ ] LLM interpreta pelo menos 5 tipos de instrução
  - [ ] Personalização de mensagem com contexto do mini-prompt

Criterios de Aceitacao:
  - [ ] Mini-prompt "agendar para terça às 14h" → ação de agendamento
  - [ ] Mini-prompt "dar feedback positivo" → mensagem personalizada
  - [ ] Mini-prompt vazio → Layer 1 determinístico (fallback)

Arquivos de Referencia (Prototipo Replit):
  - spec: docs/pipeline-transition-system.md §7.3 (Mini-Prompt)
  - spec: docs/pipeline-transition-system.md §12 (Layer 2)
```

---

### PIP-018: Sistema de Timeout e Escalação

```yaml
Titulo: "[Pipeline] Sistema de Timeout e Escalação por Pipeline"
Tipo: Feature
Area: Backend
Sprint: S4
Pontos: 5
Prioridade: Média
Epic: É24
Status: 📋 Pendente Jira
Fase: Alpha 2+
Referências IA: INF-005 (dispara eventos de timeout), AUT-002 (timeout de triagem)

Descricao: |
  Sistema de prazos configuráveis por empresa para cada etapa do pipeline.
  Quando um candidato ultrapassa o timeout de uma coluna:
  
  1. Badge de alerta temporal aparece no card (PIP-006)
  2. Notificação ao recrutador responsável
  3. Se continua sem ação → escalação ao gestor
  4. NUNCA move candidato automaticamente (exceto offer_accepted/declined)
  
  Configuração por empresa:
  - Timeout padrão por action_behavior (ex: screening=5d, scheduling=3d)
  - Escalação: recrutador → gestor → admin
  - Canais: Teams + Email + Bell (in-app)

Historia de Usuario: |
  Como gestor, eu quero ser notificado quando candidatos ficam
  parados em uma etapa por mais tempo que o esperado.

DoD:
  - [ ] Configuração de timeout por etapa por empresa
  - [ ] Badge de alerta temporal funcional
  - [ ] Notificação ao recrutador no timeout
  - [ ] Escalação ao gestor se sem ação

Criterios de Aceitacao:
  - [ ] Candidato 5 dias em "Triagem" → badge "5 dias sem resposta"
  - [ ] Recrutador notificado via Teams
  - [ ] +2 dias → gestor notificado

Arquivos de Referencia (Prototipo Replit):
  - spec: docs/pipeline-transition-system.md §13.5 (Timeout/Escalação)
```

---

## 6. Tabela Resumo

### 6.1 Todos os Cards

| Card | Título | Épico | Sprint | Pts | Prioridade | Fase | Deps |
|------|--------|-------|:------:|:---:|:----------:|:----:|------|
| PIP-001 | Arquitetura 3 Camadas + Catálogo | É24 | S1 | 8 | Crítica | Alpha 1 | — |
| PIP-002 | Motor action_behavior (10 tipos) | É24 | S1 | 8 | Crítica | Alpha 1 | PIP-001 |
| PIP-008 | Endpoints de Transição (API) | É24 | S1 | 5 | Crítica | Alpha 1 | PIP-001, PIP-002 |
| PIP-009 | Pipeline CRUD por Vaga | É24 | S1 | 5 | Alta | Alpha 1 | PIP-001 |
| PIP-003 | UniversalTransitionModal | É25 | S2 | 8 | Crítica | Alpha 1 | PIP-002, PIP-008 |
| PIP-004 | use-transition-context Hook | É25 | S2 | 5 | Alta | Alpha 1 | PIP-003 |
| PIP-005 | Movimentação Livre (Drag-Drop) | É25 | S2 | 5 | Crítica | Alpha 1 | PIP-003 |
| PIP-006 | Badges nos Cards | É25 | S2 | 5 | Alta | Alpha 1 | PIP-002 |
| PIP-007 | TransitionDispatchService (L1) | É24 | S2 | 8 | Alta | Alpha 1 | PIP-008, AGT-011 |
| PIP-010 | Barra de Ações em Massa | É25 | S2 | 5 | Alta | Alpha 1 | PIP-003 |
| PIP-011 | Pipeline Padrão Empresa | É26 | S3 | 5 | Média | Alpha 2 | PIP-009 |
| PIP-012 | Herança Empresa → Vaga | É26 | S3 | 5 | Média | Alpha 2 | PIP-011 |
| PIP-013 | Colunas Customizadas + LIA | É26 | S3 | 5 | Média | Alpha 2 | PIP-009, SRV-016 |
| PIP-014 | TestSendModal | É26 | S3 | 5 | Alta | Alpha 2 | PIP-003 |
| PIP-015 | ProposalModal | É26 | S3 | 5 | Alta | Alpha 2 | PIP-003 |
| PIP-016 | SchedulingModal Dedicado | É26 | S4 | 8 | Média | Alpha 2+ | PIP-003, AGT-003 |
| PIP-017 | Mini-Prompt LLM (L2) | É24 | S3 | 5 | Média | Alpha 2 | PIP-007, SRV-016 |
| PIP-018 | Timeout e Escalação | É24 | S4 | 5 | Média | Alpha 2+ | PIP-006, INF-005 |

### 6.2 Totais

| Fase | Cards | Pontos | Sprints |
|------|:-----:|:------:|:-------:|
| Alpha 1 | 10 | 62 | S1–S2 |
| Alpha 2 | 6 | 30 | S3 |
| Alpha 2+ | 2 | 13 | S4 |
| **Total** | **18** | **105** | S1–S4 |

### 6.3 Por Épico

| Épico | Cards | Pontos |
|-------|:-----:|:------:|
| É24 — Modelo de Dados | 7 | 44 |
| É25 — Frontend | 5 | 28 |
| É26 — Configuração | 6 | 33 |
| **Total** | **18** | **105** |

### 6.4 Por Sprint

| Sprint | Cards | Pontos | Foco |
|--------|:-----:|:------:|------|
| S1 | 4 | 26 | Modelo de dados, catálogo, API, CRUD |
| S2 | 6 | 36 | Modal, drag-drop, badges, dispatch, ações massa |
| S3 | 6 | 30 | Config empresa, herança, colunas custom, modais especializados, L2 |
| S4 | 2 | 13 | Scheduling modal, timeout/escalação |

---

## 7. Mapa de Dependências

```
S1: Fundação
─────────────────────────────────────────────────────
PIP-001 (3 Camadas + Catálogo)
    ├── PIP-002 (action_behavior) ──────────┐
    ├── PIP-009 (Pipeline CRUD) ───────┐    │
    └── PIP-008 (API Transição) ──┐    │    │
                                  │    │    │
S2: Motor + Frontend              │    │    │
─────────────────────────────────────────────────────
    PIP-003 (UniversalTransitionModal) ◄────┤
        ├── PIP-004 (use-transition-context) │
        ├── PIP-005 (Drag-Drop)              │
        └── PIP-010 (Bulk Actions)           │
    PIP-006 (Badges) ◄──────────────────────┘
    PIP-007 (DispatchService L1) ◄── AGT-011 (IA)
                                  │
S3: Refinamentos                  │
─────────────────────────────────────────────────────
    PIP-011 (Pipeline Empresa) ◄── PIP-009
        └── PIP-012 (Herança)
    PIP-013 (Custom + LIA) ◄── SRV-016 (IA)
    PIP-014 (TestSendModal)
    PIP-015 (ProposalModal)
    PIP-017 (Mini-Prompt L2) ◄── SRV-016 (IA)

S4: Avançado
─────────────────────────────────────────────────────
    PIP-016 (SchedulingModal) ◄── AGT-003, INT-AI-005 (IA)
    PIP-018 (Timeout) ◄── INF-005, AUT-002 (IA)
```

### Integração com Cards de IA (Cross-Reference)

```
Cards PIP-* (Produto)              Cards IA (lia-ai-architecture)
─────────────────────              ──────────────────────────────
PIP-002 (action_behavior) ──────► SRV-016 (SubStatusPredictor)
PIP-007 (Dispatch L1) ──────────► AGT-011 (CommunicationAgent)
PIP-010 (Bulk Actions) ─────────► AUT-006 (Bulk Reject AI)
PIP-013 (Infer-behavior) ───────► SRV-016 (LLM inference)
PIP-017 (Mini-Prompt L2) ───────► SRV-016 + AGT-011
PIP-006 (Badges) ───────────────► AUT-005 (Return Events)
PIP-018 (Timeout) ──────────────► INF-005 (EventDispatcher)
```
