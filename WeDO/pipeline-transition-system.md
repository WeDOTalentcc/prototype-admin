# Sistema de Pipeline, Transições e Comunicação da Plataforma LIA

> **Versão**: 1.4 — 20 de Fevereiro de 2026  
> **Propósito**: Guia de implementação, referência técnica e base para treinamento  
> **Status**: Documento de referência para o sistema de movimentação de candidatos

---

## Índice

1. [Visão Geral](#1-visão-geral)
2. [Arquitetura de 3 Camadas de Colunas](#2-arquitetura-de-3-camadas-de-colunas)
3. [Catálogo Completo de Colunas](#3-catálogo-completo-de-colunas)
4. [Sistema de `action_behavior`](#4-sistema-de-action_behavior)
5. [Matriz Autoritativa: Ação → Modal → Canal](#5-matriz-autoritativa-ação--modal--canal)
6. [Movimentação Livre de Candidatos](#6-movimentação-livre-de-candidatos)
7. [UniversalTransitionModal — Design Compacto](#7-universaltransitionmodal--design-compacto)
8. [Design dos Modais por Tipo de Ação](#8-design-dos-modais-por-tipo-de-ação)
9. [Inventário de Modais Existentes](#9-inventário-de-modais-existentes)
10. [Integração: UniversalTransitionModal → Modais Existentes](#10-integração-universaltransitionmodal--modais-existentes)
11. [Sistema de Badges nos Cards](#11-sistema-de-badges-nos-cards)
12. [Disparos Automáticos (Email + WhatsApp)](#12-disparos-automáticos-email--whatsapp)
13. [Retorno Automático de Candidatos](#13-retorno-automático-de-candidatos)
14. [Herança de Pipeline: Empresa → Vaga](#14-herança-de-pipeline-empresa--vaga)
15. [Menu Configurações — Pipeline da Empresa](#15-menu-configurações--pipeline-da-empresa)
16. [Criação de Colunas Customizadas com LIA](#16-criação-de-colunas-customizadas-com-lia)
17. [Fluxos Completos End-to-End](#17-fluxos-completos-end-to-end)
18. [Plano Faseado de Implementação](#18-plano-faseado-de-implementação)
19. [Gaps e Modais a Criar](#19-gaps-e-modais-a-criar)
20. [Glossário](#20-glossário)
21. [Status de Implementação e Roadmap](#21-status-de-implementação-e-roadmap)
22. [Fase 5 — Retorno Automático de Candidatos](#22-fase-5--retorno-automático-de-candidatos-implementado)
23. [Phase 6: Pipeline Configuration, Add Column & Infer-Behavior](#23-phase-6-pipeline-configuration-add-column--infer-behavior)
24. [Próximos Passos](#24-próximos-passos)
25. [Auditoria de Implementação](#25-auditoria-de-implementação-20022026)

---

## 1. Visão Geral

### O que é o Sistema de Pipeline

O pipeline é a representação visual do processo seletivo de uma vaga. Cada **coluna** representa uma etapa do processo, e os **candidatos** se movem entre colunas conforme avançam (ou são reprovados).

### Filosofia Central

```
┌─────────────────────────────────────────────────────────────┐
│                    PRINCÍPIOS FUNDAMENTAIS                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. MOVIMENTAÇÃO LIVRE                                      │
│     O recrutador pode mover qualquer candidato para         │
│     qualquer coluna. Sem restrições de transição.           │
│                                                             │
│  2. AÇÃO NATIVA DA COLUNA                                   │
│     Cada coluna tem um tipo de ação (action_behavior).      │
│     Ao mover um candidato para uma coluna, o sistema        │
│     oferece automaticamente a ação nativa daquela coluna.   │
│                                                             │
│  3. MODAIS COMPACTOS QUE DELEGAM                            │
│     O modal de transição é enxuto. Mostra o essencial       │
│     e oferece BOTÕES que abrem modais especializados        │
│     já existentes. NUNCA duplica lógica de outros modais.   │
│                                                             │
│  4. LIA COMO FACILITADORA                                   │
│     A LIA pode executar ações automaticamente (agendar,     │
│     enviar feedback, disparar triagem) ou o recrutador      │
│     pode optar pelo modo manual (abre modal completo).      │
│                                                             │
│  5. CANDIDATO MOVE O PROCESSO                               │
│     Quando o candidato responde (completa triagem,          │
│     confirma entrevista, envia documentos), o sistema       │
│     atualiza sub-status e/ou move automaticamente.          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Diagrama Geral do Fluxo

```
                    RECRUTADOR                          CANDIDATO
                        │                                   │
                        ▼                                   │
              ┌───────────────────┐                         │
              │  Move candidato   │                         │
              │  (drag-drop ou    │                         │
              │   dropdown)       │                         │
              └────────┬──────────┘                         │
                       │                                    │
                       ▼                                    │
              ┌───────────────────┐                         │
              │  Universal        │                         │
              │  Transition       │                         │
              │  Modal            │                         │
              │  ┌─────────────┐  │                         │
              │  │ Sub-status  │  │                         │
              │  │ Mini-prompt │  │                         │
              │  │ Ação:       │  │                         │
              │  │ ● LIA auto  │──┼── LIA dispara ──────────┤
              │  │ ○ Manual ───┼──┼── Abre modal ───┐       │
              │  └─────────────┘  │                 │       │
              └───────────────────┘                 │       │
                                                    ▼       │
                                           ┌──────────────┐ │
                                           │ Modal        │ │
                                           │ Especializ.  │ │
                                           │ (Agendamento,│ │
                                           │  Feedback,   │ │
                                           │  Triagem...) │ │
                                           └──────┬───────┘ │
                                                  │         │
                                                  ▼         ▼
                                           ┌──────────────────┐
                                           │   DISPARO        │
                                           │   Email +        │
                                           │   WhatsApp       │
                                           └──────┬───────────┘
                                                  │
                                                  ▼
                                           ┌──────────────────┐
                                           │  CANDIDATO       │
                                           │  RESPONDE        │
                                           │  (completa       │
                                           │   triagem,       │
                                           │   confirma       │
                                           │   entrevista,    │
                                           │   envia docs...) │
                                           └──────┬───────────┘
                                                  │
                                                  ▼
                                           ┌──────────────────┐
                                           │  ATUALIZAÇÃO     │
                                           │  AUTOMÁTICA      │
                                           │  Sub-status e/ou │
                                           │  Movimentação    │
                                           └──────┬───────────┘
                                                  │
                                                  ▼
                                           ┌──────────────────┐
                                           │  NOTIFICAÇÃO     │
                                           │  ao recrutador   │
                                           │  (toast + badge) │
                                           └──────────────────┘
```

---

## 2. Arquitetura de 3 Camadas de Colunas

O pipeline da LIA organiza colunas em **3 camadas hierárquicas**:

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  CAMADA 1: SYSTEM (Fixas)                                   │
│  ─────────────────────────                                  │
│  Colunas obrigatórias, presentes em TODA vaga.              │
│  Não podem ser removidas, reordenadas ou renomeadas.        │
│                                                             │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │
│  │ Funil  │ │Triagem │ │Entrev. │ │Aprovad.│ │Contrat.│    │
│  │        │ │        │ │ RH     │ │        │ │        │    │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘    │
│  + ┌────────┐                                               │
│    │Reprov. │ (coluna lateral/final, sempre disponível)      │
│    └────────┘                                               │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CAMADA 2: CATALOG (Pré-configuradas)                       │
│  ─────────────────────────────────                          │
│  Colunas com ação e sub-statuses já definidos.              │
│  Empresa escolhe quais usar no Menu Configurações.          │
│  Podem ser inseridas entre as colunas System.               │
│                                                             │
│  Exemplos: Entrevista Técnica, Entrevista Gestor,           │
│  Teste Técnico, Teste de Inglês, Referências,               │
│  Entrevista Final, Proposta, etc.                           │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CAMADA 3: CUSTOM (Criadas pelo recrutador)                 │
│  ──────────────────────────────────────────                 │
│  Recrutador digita nome + descrição.                        │
│  LIA sugere o action_behavior adequado.                     │
│  Recrutador confirma ou altera.                             │
│                                                             │
│  Exemplo: "Dinâmica de Grupo" → LIA sugere: evaluation      │
│           "Entrevista com CEO" → LIA sugere: scheduling      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Regras de Organização

| Regra | Descrição |
|-------|-----------|
| Colunas System são fixas | Não podem ser removidas ou renomeadas |
| Colunas System definem a estrutura base | Funil → Triagem → Entrevista RH → Aprovados → Contratado |
| Reprovado é transversal | Candidatos podem ser reprovados de qualquer etapa |
| Catalog e Custom se inserem ENTRE as System | Ex: Funil → Triagem → **Teste Técnico** → Entrevista RH → **Entrevista Gestor** → Aprovados → **Proposta** → Contratado |
| Ordem é configurável | Empresa define a ordem no Menu Configurações |
| Vaga herda da empresa | Mas pode customizar (adicionar/remover colunas Catalog/Custom) |

---

## 3. Catálogo Completo de Colunas

### 3.1 Colunas System (Fixas)

| # | Coluna | `action_behavior` | Sub-statuses Padrão | Descrição |
|---|--------|-------------------|---------------------|-----------|
| 1 | **Funil** | `intake` | Novo, Visualizado, Indicado | Candidatos entram aqui. Recrutador faz like/dislike nos cards. |
| 2 | **Triagem** | `screening` | Convite Enviado, Aguardando Resposta, Em Andamento, Triagem Completa | Triagem WSI automatizada pela LIA. |
| 3 | **Entrevista RH** | `scheduling` | Convite Enviado, Agendada, Confirmada, Realizada, No-show | Entrevista com equipe de recrutamento. |
| 4 | **Aprovados** | `passive` | Aprovado RH, Aprovado Técnico, Aprovado Final | Candidatos aprovados aguardando próxima etapa ou proposta. |
| 5 | **Contratado** | `conclusion_hired` | Proposta Aceita, Em Onboarding, Integrado | Candidato contratado. Fim do processo. |
| 6 | **Reprovado** | `conclusion_rejected` | Perfil Inadequado, Reprovado Triagem, Reprovado Entrevista, Reprovado Teste, Desistência, Sem Resposta | Candidato reprovado em qualquer etapa. |

### 3.2 Colunas Catalog (Pré-configuradas)

| # | Coluna | `action_behavior` | Sub-statuses Padrão | Ícone |
|---|--------|-------------------|---------------------|-------|
| 7 | **Entrevista Técnica** | `scheduling` | Convite Enviado, Agendada, Confirmada, Realizada, No-show | 💻 |
| 8 | **Entrevista Gestor** | `scheduling` | Convite Enviado, Agendada, Confirmada, Realizada, No-show | 👔 |
| 9 | **Entrevista Final** | `scheduling` | Convite Enviado, Agendada, Confirmada, Realizada, No-show | 🏆 |
| 10 | **Teste Técnico** | `evaluation` | Teste Enviado, Em Andamento, Concluído, Expirado | 📝 |
| 11 | **Teste de Inglês** | `evaluation` | Teste Enviado, Em Andamento, Concluído, Expirado | 🌐 |
| 12 | **Case Prático** | `evaluation` | Case Enviado, Em Andamento, Entregue, Avaliado | 📊 |
| 13 | **Referências** | `verification` | Solicitação Enviada, Aguardando, Documentos Recebidos, Verificado | 🔍 |
| 14 | **Proposta** | `offer` | Proposta Elaborada, Proposta Enviada, Em Análise, Aceita, Recusada, Contra-proposta | 📄 |
| 15 | **Proposta Recusada** | `conclusion_declined` | Salário, Benefícios, Modelo de Trabalho, Outra Proposta, Motivo Pessoal, Localização | ↩️ |
| 16 | **Dinâmica de Grupo** | `scheduling` | Convite Enviado, Agendada, Confirmada, Realizada | 👥 |

### 3.3 Exemplo de Pipeline Completo

```
Pipeline padrão de uma empresa de tecnologia:

┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ Funil  │→│Triagem │→│Entrev. │→│ Teste  │→│Entrev. │→│Entrev. │→│Aprovad.│→│Proposta│→│Contrat.│
│        │ │        │ │ RH     │ │Técnico │ │Técnica │ │Gestor  │ │        │ │        │ │        │
│ intake │ │screen. │ │sched.  │ │eval.   │ │sched.  │ │sched.  │ │passive │ │offer   │ │hired   │
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
                                                                                          │
                                                                              ┌───────────┘
                                                                              ▼
                                                                        ┌────────┐
                                                                        │Reprov. │
                                                                        │rejected│
                                                                        └────────┘

Legenda: System ■  Catalog □  A qualquer momento → Reprovado
```

---

## 4. Sistema de `action_behavior`

O campo `action_behavior` define **o que acontece automaticamente** quando um candidato é movido para uma coluna. É o coração do sistema de transições.

### 4.1 Tipos de `action_behavior`

| Tipo | O que acontece | Ação automática (LIA) | Ação manual |
|------|----------------|----------------------|-------------|
| `intake` | Candidato entra no funil | — | Like/Dislike no card |
| `screening` | Triagem WSI | LIA envia convite de triagem por email+WhatsApp | Botão abre WSITriagemInviteModal |
| `scheduling` | Agendamento de entrevista | LIA envia horários por email+WhatsApp, candidato escolhe | Botão abre modal de agendamento completo |
| `evaluation` | Envio de teste/case | LIA envia teste por email+WhatsApp | Botão abre TestSendModal |
| `verification` | Solicitação de dados/documentos | LIA solicita dados por email+WhatsApp | Botão abre DataRequestModal |
| `offer` | Envio de proposta | LIA envia proposta por email | Botão abre modal de proposta |
| `passive` | Sem ação automática | — | — |
| `conclusion_hired` | Confirmação de contratação | LIA envia boas-vindas por email | Botão abre modal de email |
| `conclusion_rejected` | Rejeição | LIA envia feedback por email+WhatsApp | Botão abre modal de feedback |
| `conclusion_declined` | Proposta recusada | — | Formulário de motivo inline |

### 4.2 Diagrama de Decisão: Automático vs Manual

```
Candidato movido para coluna com action_behavior = scheduling
                        │
                        ▼
              ┌───────────────────┐
              │ UniversalTransi-  │
              │ tionModal abre    │
              │                   │
              │ Como agendar?     │
              │                   │
              │ ● LIA auto        │
              │ ○ Manual          │
              └──────┬────────────┘
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
  ┌───────────────┐    ┌───────────────────┐
  │ LIA AUTO      │    │ MANUAL            │
  │               │    │                   │
  │ Recrutador    │    │ Abre modal de     │
  │ pode informar │    │ agendamento       │
  │ preferência   │    │ completo          │
  │ no prompt:    │    │ (screenshot):     │
  │ "terça 14h"   │    │                   │
  │               │    │ - Canal           │
  │ LIA envia     │    │ - Tipo entrevista │
  │ opções ao     │    │ - Plataforma      │
  │ candidato     │    │ - Duração         │
  │ por Email +   │    │ - Data/Hora       │
  │ WhatsApp      │    │ - Entrevistador   │
  │               │    │ - Template        │
  │ Candidato     │    │ - Preview email   │
  │ escolhe       │    │                   │
  │ horário       │    │ Recrutador        │
  │               │    │ controla tudo     │
  └───────────────┘    └───────────────────┘
          │                     │
          └──────────┬──────────┘
                     ▼
              ┌───────────────┐
              │ Disparo       │
              │ Email +       │
              │ WhatsApp      │
              └───────────────┘
```

### 4.3 Importante: o `action_behavior` NÃO é exposto ao recrutador como termo técnico

Na interface, o recrutador vê:
- No Menu Configurações: **"Tipo de Ação"** com opções em português ("Agendamento", "Avaliação/Teste", "Solicitação de Dados", etc.)
- No Kanban: apenas o nome da coluna e os sub-statuses
- No UniversalTransitionModal: a seção de ação é renderizada automaticamente com base no tipo

---

## 5. Matriz Autoritativa: Ação → Modal → Canal

> **Esta é a tabela de referência central.** Todas as outras seções do documento (Design dos Modais, Integração, Fluxos End-to-End) DEVEM ser consistentes com esta matriz. Em caso de dúvida, esta tabela prevalece.

### 5.1 Tabela Completa

| `action_behavior` | Coluna exemplo | Modo LIA Auto | Modo Manual → Modal | Canal Auto | Canal Manual | Modal existente? | Sub-status inicial |
|---|---|---|---|---|---|---|---|
| `intake` | Funil | — | Like/Dislike no card → CandidateDecisionFlowModal | — | — | ✅ Existe | Novo |
| `screening` | Triagem | LIA dispara convite de triagem WSI | [Abrir Triagem] → WSITriagemInviteModal | Email + WhatsApp | Recrutador escolhe | ✅ Existe | Convite Enviado |
| `scheduling` | Entrev. RH, Técnica, Gestor, Final, Dinâmica | LIA envia horários disponíveis, candidato escolhe | [Abrir Agendamento] → UnifiedCommunicationModal (type=agendamento) | Email + WhatsApp | Recrutador escolhe | ✅ Existe | Convite Enviado |
| `evaluation` | Teste Técnico, Inglês, Case | LIA envia teste configurado para a etapa | [Abrir Envio de Teste] → TestSendModal | Email + WhatsApp | Recrutador escolhe | ❌ Criar | Teste Enviado |
| `verification` | Referências | LIA solicita dados/documentos | [Abrir Solicitação] → DataRequestModal | Email + WhatsApp | Recrutador escolhe | ✅ Existe | Solicitação Enviada |
| `offer` | Proposta | LIA envia proposta formal | [Abrir Proposta] → UnifiedCommunicationModal (type=proposta) | **Email apenas** | Recrutador escolhe | ❌ Adaptar | Proposta Enviada |
| `passive` | Aprovados | — | — | — | — | N/A | (sem sub-status obrigatório) |
| `conclusion_hired` | Contratado | LIA envia boas-vindas | [Personalizar] → UnifiedCommunicationModal (type=email) | **Email apenas** | Recrutador escolhe | ✅ Existe | Proposta Aceita |
| `conclusion_rejected` | Reprovado | LIA envia feedback construtivo (pós-triagem) | [Enviar Feedback] → UnifiedCommunicationModal (type=feedback) | Email + WhatsApp | Recrutador escolhe | ✅ Existe | (varia por motivo) |
| `conclusion_declined` | Proposta Recusada | — | Formulário inline (radio motivo) | — | — | N/A (inline) | (motivo selecionado) |

### 5.2 Exceções ao Canal "Email + WhatsApp"

| `action_behavior` | Canal no modo automático | Motivo |
|---|---|---|
| `offer` | **Email apenas** | Proposta formal é documento com peso jurídico, inadequado para WhatsApp |
| `conclusion_hired` | **Email apenas** | Boas-vindas e onboarding contêm documentos e links formais |
| Todos os outros | Email + WhatsApp | Comunicação operacional, ambos canais são adequados |

No modo **manual**, o recrutador sempre pode escolher qualquer canal disponível, independentemente do padrão automático.

### 5.3 Resumo Visual

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MATRIZ AÇÃO → MODAL → CANAL                        │
│                                                                         │
│  intake ─────────→ CandidateDecisionFlowModal ──────→ (sem disparo)    │
│  screening ──────→ WSITriagemInviteModal ───────────→ Email + WhatsApp │
│  scheduling ─────→ UnifiedCommModal(agendamento) ──→ Email + WhatsApp │
│  evaluation ─────→ TestSendModal (CRIAR) ──────────→ Email + WhatsApp │
│  verification ──→ DataRequestModal ────────────────→ Email + WhatsApp │
│  offer ─────────→ UnifiedCommModal(proposta) ──────→ Email APENAS ⚠️  │
│  passive ────────→ (sem ação extra) ───────────────→ (sem disparo)    │
│  conclusion_hired→ UnifiedCommModal(email) ────────→ Email APENAS ⚠️  │
│  conclusion_rej.→ UnifiedCommModal(feedback) ──────→ Email + WhatsApp │
│  conclusion_dec.→ Formulário inline ───────────────→ (sem disparo)    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Movimentação Livre de Candidatos

### 6.1 Antes vs Depois

```
ANTES (sistema antigo — NÃO FUNCIONA):
─────────────────────────────────────
- allowed_transitions definia rotas permitidas
- Candidato só podia ir para certas colunas
- Sub-status modals causavam erros
- Muitas features documentadas mas não implementadas

DEPOIS (novo sistema):
──────────────────────
- Movimentação LIVRE: qualquer coluna → qualquer coluna
- A coluna DESTINO determina a ação (via action_behavior)
- Único modal (UniversalTransitionModal) para toda transição
- Modais especializados abrem sob demanda via botões
```

### 6.2 Como funciona no Kanban

```
┌─────────────────────────────────────────────────────────┐
│                        KANBAN                           │
│                                                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │ Triagem │  │Entrev.RH│  │ Teste   │  │Aprovados│   │
│  │         │  │         │  │ Técnico │  │         │   │
│  │ ┌─────┐ │  │         │  │         │  │         │   │
│  │ │João │─┼──┼────drag────┼─────────┼──▶         │   │
│  │ │Silva│ │  │         │  │         │  │         │   │
│  │ └─────┘ │  │         │  │         │  │         │   │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │
│                                                         │
│  Ao soltar (drop):                                      │
│  → Sistema consulta action_behavior da coluna destino   │
│  → Abre UniversalTransitionModal com seção correta      │
│                                                         │
│  Coluna destino "Aprovados" tem action_behavior=passive │
│  → Modal mostra apenas: candidato, transição, sub-status│
│  → Sem ação extra                                       │
│                                                         │
│  Coluna destino "Entrev.RH" tem action_behavior=sched.  │
│  → Modal mostra: candidato, transição, sub-status       │
│  → + Seção: "LIA auto" ou "Manual → [Abrir Agendamento]│
└─────────────────────────────────────────────────────────┘
```

### 6.3 Como funciona na Tabela

```
┌──────────────────────────────────────────────────────────────────┐
│ [Configurar Etapas]                                              │
│                                                                  │
│ Nome          │ Cargo            │ Etapa          │ Status       │
│───────────────┼──────────────────┼────────────────┼──────────────│
│ João Silva    │ Product Designer │ [Triagem    ▼] │ 🟢 Completa  │
│ Maria Santos  │ Dev Frontend     │ [Entrev. RH ▼] │ 🟡 Agendada  │
│ Carlos Lima   │ DevOps Engineer  │ [Teste Téc. ▼] │ 🔵 Enviado   │
│                                                                  │
│ Ao mudar dropdown de "Etapa":                                    │
│ → Abre UniversalTransitionModal (mesmo comportamento do Kanban)  │
│                                                                  │
│ Coluna "Status" mostra badges equivalentes ao Kanban             │
│ (sub-status + ação pendente + alertas)                           │
└──────────────────────────────────────────────────────────────────┘
```

---

## 7. UniversalTransitionModal — Design Compacto

### 7.1 Estrutura Base (presente em TODA transição)

```
┌─────────────────────────────────────────────────────┐
│ ⚡ Mover Candidato                              [X] │
│─────────────────────────────────────────────────────│
│                                                     │
│ 👤 João Silva                                       │
│    Product Designer • TechCorp                      │
│                                                     │
│ ┌──────────┐           ┌──────────┐                 │
│ │ Triagem  │  ────▶    │ Entrev.  │                 │
│ │          │           │ RH       │                 │
│ └──────────┘           └──────────┘                 │
│                                                     │
│ Sub-status:  [ Agendada                    ▼ ]      │
│              (opções vêm da coluna destino)          │
│                                                     │
│ ┌─────────────────────────────────────────────────┐ │
│ │ 💬 Contexto para a LIA (opcional)               │ │
│ │                                                 │ │
│ │ "aprovado, entrevista terça 14h"                │ │
│ │                                                 │ │
│ │ 🤖 LIA: Sub-status ajustado para "Agendada".   │ │
│ │    Registrei preferência terça 14:00.           │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ ╔═════════════════════════════════════════════════╗ │
│ ║  SEÇÃO DE AÇÃO                                  ║ │
│ ║  (varia por action_behavior — ver Seção 8)      ║ │
│ ╚═════════════════════════════════════════════════╝ │
│                                                     │
│ ─────────────────────────────────────────────────── │
│                     [Cancelar]  [Confirmar Mov.]    │
└─────────────────────────────────────────────────────┘
```

### 7.2 Componentes do Modal

| Componente | Descrição | Sempre presente? |
|------------|-----------|-----------------|
| **Header** | "Mover Candidato" + botão fechar | ✅ Sim |
| **Candidato** | Avatar, nome, cargo atual, empresa | ✅ Sim |
| **Transição visual** | Badge "antes" → seta → Badge "depois" | ✅ Sim |
| **Sub-status** | Dropdown com opções da coluna destino | ✅ Sim (se coluna tem sub-statuses) |
| **Mini-prompt LIA** | Campo de texto livre + resposta inline da LIA | ✅ Sim |
| **Seção de ação** | Varia por `action_behavior` | Depende do tipo |
| **Footer** | Cancelar + Confirmar Movimentação | ✅ Sim |

### 7.3 Comportamento do Mini-prompt LIA

O mini-prompt é um campo de texto onde o recrutador pode escrever contexto em linguagem natural. A LIA interpreta e:

1. **Ajusta o sub-status** — "aprovado na entrevista" → sub-status "Realizada" ou "Aprovado"
2. **Registra informações** — "entrevista terça 14h" → registra preferência de horário
3. **Sugere ações** — "precisa de mais uma entrevista técnica" → sugere mover para coluna diferente
4. **Captura motivos** — "perfil não se encaixa" → registra motivo de rejeição

O endpoint `POST /api/v1/transition/interpret-context` processa o texto e retorna sugestões.

---

## 8. Design dos Modais por Tipo de Ação

### 8.1 `intake` — Funil (Sem modal, usa Like/Dislike)

Candidatos no Funil não usam o UniversalTransitionModal para interação primária. A interação é diretamente no card:

```
┌────────────────────────────────┐
│ 👤 João Silva          85% ★  │
│    Product Designer            │
│    TechCorp                    │
│                                │
│ Skills: React, Node, Figma     │
│                                │
│    [👎 Dislike]  [👍 Like]     │
└────────────────────────────────┘

Like  → Abre CandidateDecisionFlowModal
        (flowType: 'approve_to_triage')
        → Candidato move para Triagem

Dislike → Abre CandidateDecisionFlowModal
          (flowType: 'reject_pre_triage')
          → Candidato move para Reprovado

Drag para outra coluna → Abre UniversalTransitionModal
                         com ação da coluna destino
```

### 8.2 `screening` — Triagem

```
╔═════════════════════════════════════════════════╗
║ 📋 AÇÃO: Triagem WSI                            ║
║                                                 ║
║  ● LIA envia triagem automaticamente            ║
║    Convite por Email + WhatsApp                 ║
║    Perguntas WSI calibradas para a vaga          ║
║                                                 ║
║  ○ Configurar manualmente → [Abrir Triagem]     ║
║    Abre o modal de convite WSI com todas         ║
║    as opções de configuração                     ║
╚═════════════════════════════════════════════════╝

"Abrir Triagem" → abre WSITriagemInviteModal
(componente existente: wsi/wsi-triagem-invite-modal.tsx)
```

### 8.3 `scheduling` — Agendamento (Entrevista RH, Técnica, Gestor, Final, Dinâmica)

```
╔═════════════════════════════════════════════════╗
║ 📅 AÇÃO: Agendamento de Entrevista              ║
║                                                 ║
║  ● LIA agenda automaticamente                   ║
║    LIA envia horários disponíveis por            ║
║    Email + WhatsApp para o candidato             ║
║    escolher.                                     ║
║                                                 ║
║  ○ Agendar manualmente → [Abrir Agendamento]    ║
║    Abre o modal completo de agendamento          ║
║    (canal, tipo, plataforma, data, hora,         ║
║     entrevistador, template, preview)            ║
╚═════════════════════════════════════════════════╝

"Abrir Agendamento" → abre UnifiedCommunicationModal
(componente existente: modals/unified-communication-modal.tsx)
(type = 'agendamento')
```

**Importante**: "LIA auto" com preferência de horário no prompt ("terça 14h comigo") **ainda é automático**. A LIA usa essa informação para sugerir horários ao candidato. O candidato pode aceitar ou pedir outros horários. Tudo via Email + WhatsApp.

"Manual" = o recrutador abre o modal completo e define tudo ele mesmo: canal, plataforma (Zoom/Teams/Meet/Presencial), tipo de entrevista (Funcional/Técnica/Completa/Cultural), data, hora, entrevistador, template de email, preview.

### 8.4 `evaluation` — Envio de Teste

```
╔═════════════════════════════════════════════════╗
║ 📝 AÇÃO: Envio de Teste                         ║
║                                                 ║
║  ● LIA envia teste automaticamente               ║
║    Busca teste configurado para esta etapa       ║
║    Dispara por Email + WhatsApp                  ║
║                                                 ║
║  ○ Configurar envio → [Abrir Envio de Teste]     ║
║    Escolher tipo de teste, link, prazo,           ║
║    canal e mensagem                               ║
╚═════════════════════════════════════════════════╝

"Abrir Envio de Teste" → abre TestSendModal
(componente a criar — ver Seção 19: Gaps)
```

### 8.5 `verification` — Solicitação de Dados

```
╔═════════════════════════════════════════════════╗
║ 🔍 AÇÃO: Solicitação de Dados                   ║
║                                                 ║
║  ● LIA solicita dados automaticamente            ║
║    Usa template padrão da etapa                  ║
║    (Referências / Documentos / Certificações)    ║
║    Dispara por Email + WhatsApp                  ║
║                                                 ║
║  ○ Configurar solicitação → [Abrir Solicitação]  ║
║    Escolher campos, template, prazo e canal       ║
╚═════════════════════════════════════════════════╝

"Abrir Solicitação" → abre DataRequestModal
(componente existente: modals/data-request-modal.tsx)
```

### 8.6 `offer` — Proposta

```
╔═════════════════════════════════════════════════╗
║ 📄 AÇÃO: Envio de Proposta                       ║
║                                                 ║
║  ● LIA envia proposta automaticamente            ║
║    Usa dados de proposta configurados            ║
║    Dispara por Email                             ║
║                                                 ║
║  ○ Elaborar proposta → [Abrir Proposta]           ║
║    Definir salário, modelo, benefícios,           ║
║    data início, prazo de resposta, mensagem       ║
╚═════════════════════════════════════════════════╝

"Abrir Proposta" → abre UnifiedCommunicationModal
(componente existente, adaptado com type = 'proposta')
(ver Seção 19: Gaps — adaptação necessária)
```

### 8.7 `passive` — Sem Ação Extra

```
╔═════════════════════════════════════════════════╗
║  (sem seção de ação extra)                      ║
║                                                 ║
║  O modal mostra apenas os elementos base:       ║
║  - Candidato                                    ║
║  - Transição visual (antes → depois)            ║
║  - Sub-status (se houver opções)                ║
║  - Mini-prompt LIA                              ║
╚═════════════════════════════════════════════════╝
```

### 8.8 `conclusion_hired` — Contratação

```
╔═════════════════════════════════════════════════╗
║ ✅ AÇÃO: Confirmar Contratação                   ║
║                                                 ║
║  ┌───────────────────────────────────────────┐  ║
║  │ 🎉 Candidato será marcado como contratado │  ║
║  │ Próximos passos de onboarding serão       │  ║
║  │ iniciados.                                │  ║
║  └───────────────────────────────────────────┘  ║
║                                                 ║
║  ☑ Enviar email de boas-vindas                   ║
║     → [Personalizar mensagem]                    ║
║       (abre UnifiedCommunicationModal type=email)║
╚═════════════════════════════════════════════════╝
```

### 8.9 `conclusion_rejected` — Rejeição

Dois cenários baseados no histórico do candidato:

**Pré-triagem** (candidato não iniciou processo ativo):

```
╔═════════════════════════════════════════════════╗
║ ✕ AÇÃO: Reprovar Candidato                      ║
║                                                 ║
║  ┌───────────────────────────────────────────┐  ║
║  │ ⓘ Candidato ainda não participou do       │  ║
║  │   processo ativo. Feedback é opcional.     │  ║
║  └───────────────────────────────────────────┘  ║
║                                                 ║
║  ☐ Enviar feedback → [Abrir Feedback]            ║
║    (opcional, não recomendado pré-triagem)        ║
╚═════════════════════════════════════════════════╝

→ Reutiliza flowType 'reject_pre_triage' do
  CandidateDecisionFlowModal (já existe)
```

**Pós-triagem** (candidato já participou do processo):

```
╔═════════════════════════════════════════════════╗
║ ✕ AÇÃO: Reprovar Candidato                      ║
║                                                 ║
║  ┌───────────────────────────────────────────┐  ║
║  │ 💬 Candidato participou do processo.       │  ║
║  │ Recomendamos enviar feedback construtivo.  │  ║
║  └───────────────────────────────────────────┘  ║
║                                                 ║
║  ● Enviar feedback → [Abrir Feedback]   Recomend║
║  ○ Apenas mover (sem comunicação)                ║
╚═════════════════════════════════════════════════╝

"Abrir Feedback" → abre UnifiedCommunicationModal
(componente existente: type = 'feedback')
```

### 8.10 `conclusion_declined` — Proposta Recusada

```
╔═════════════════════════════════════════════════╗
║ ↩️ AÇÃO: Registrar Recusa de Proposta           ║
║                                                 ║
║  Motivo da recusa:                               ║
║  ┌───────────────────────────────────────────┐  ║
║  │ ○ Aceitou outra proposta                   │  ║
║  │ ● Valor abaixo da expectativa              │  ║
║  │ ○ Modelo de trabalho (presencial/remoto)   │  ║
║  │ ○ Benefícios insuficientes                 │  ║
║  │ ○ Localização                              │  ║
║  │ ○ Motivo pessoal                           │  ║
║  │ ○ Outro: [________________]                │  ║
║  └───────────────────────────────────────────┘  ║
║                                                 ║
║  (Motivo registrado no histórico do candidato    ║
║   e alimenta analytics de retenção de propostas) ║
╚═════════════════════════════════════════════════╝

→ Formulário inline, sem modal adicional
→ Mini-prompt LIA pode complementar detalhes
```

---

## 9. Inventário de Modais Existentes

### 9.1 Modais de Comunicação

| Modal | Arquivo | Linhas | O que faz | Funciona? |
|-------|---------|--------|-----------|-----------|
| **UnifiedCommunicationModal** | `modals/unified-communication-modal.tsx` | 957 | 5 tipos: email, whatsapp, triagem, agendamento, feedback. Canal, templates, MessageComposer, config entrevista, preview. Suporta bulk. | ✅ |
| **ContactModal** | `quick-actions-modals.tsx` | ~595 | Email/WhatsApp/Phone, templates LIA, sugestões | ✅ Parcial |
| **SendEmailModal** | `email-templates/send-email-modal.tsx` | ~100 | Email simples com template | ✅ |
| **WSITriagemInviteModal** | `wsi/wsi-triagem-invite-modal.tsx` | 778 | Convite de triagem WSI, perguntas, canal, preview | ✅ |

### 9.2 Modais de Agendamento

| Modal | Arquivo | Linhas | O que faz | Funciona? |
|-------|---------|--------|-----------|-----------|
| **UnifiedCommunicationModal** (type=agendamento) | `modals/unified-communication-modal.tsx` | 957 | Modal completo: tipo entrevista, plataforma, duração, data, hora, entrevistador, templates, preview | ✅ |
| **InterviewSchedulingModal** | `ui/interview-scheduling-modal.tsx` | 277 | Agendamento via prompt natural + email gerado pela LIA | ✅ |
| **ScheduleModal** | `quick-actions-modals.tsx` | ~669 | Tipo, data, hora, duração, plataforma, entrevistador, LIA insights | ✅ Parcial (dados mock) |

### 9.3 Modais de Decisão/Fluxo

| Modal | Arquivo | Linhas | O que faz | Funciona? |
|-------|---------|--------|-----------|-----------|
| **CandidateDecisionFlowModal** | `candidate-decision-flow-modal.tsx` | 493 | 6 flowTypes: approve_to_triage, approve_to_interview, reject_pre/post_triage, request_urgency, reschedule | ✅ |
| **BatchApprovalModal** | `batch-approval-modal.tsx` | 947 | Aprovação/rejeição/movimentação em lote | ✅ Parcial |

### 9.4 Modais de Transição

| Modal | Arquivo | Linhas | O que faz | Funciona? |
|-------|---------|--------|-----------|-----------|
| **StageTransitionActionsModal** | `modals/stage-transition-actions-modal.tsx` | 915 | Ações sugeridas por tipo de etapa, templates, preview | ✅ Parcial |

### 9.5 Modais de Avaliação/Teste

| Modal | Arquivo | Linhas | O que faz | Funciona? |
|-------|---------|--------|-----------|-----------|
| **TechnicalTestModal** | `modals/technical-test-modal.tsx` | 365 | **Visualiza** resultados de teste técnico (score, categorias) | ✅ Só visualização |
| **EnglishTestModal** | `modals/english-test-modal.tsx` | 355 | **Visualiza** resultados de teste de inglês (CEFR) | ✅ Só visualização |
| **RubricEvaluationModal** | `rubric-evaluation-modal.tsx` | 875 | Avaliação por rubrica WSI pós-entrevista | ✅ |

### 9.6 Modais de Solicitação de Dados

| Modal | Arquivo | Linhas | O que faz | Funciona? |
|-------|---------|--------|-----------|-----------|
| **DataRequestModal** | `modals/data-request-modal.tsx` | 332 | Solicita dados/documentos. Templates (Básico, Triagem, Pré-Entrevista, Proposta/Admissão, Custom). Canal, prazo. Bulk. | ✅ |

### 9.7 Outros Modais Relevantes

| Modal | Arquivo | Linhas | O que faz |
|-------|---------|--------|-----------|
| **CandidateModal** | `candidate-modal.tsx` | 125+ | Visualização completa do candidato |
| **QuickViewModal** | `quick-view-modal.tsx` | 56+ | Preview rápido do candidato |
| **ColumnConfigurationModal** | `column-configuration-modal.tsx` | 82+ | Configuração de colunas do pipeline |
| **ExpandedChatModal** | `expanded-chat-modal.tsx` | 11309 | Chat expandido (fullscreen) com LIA |

---

## 10. Integração: UniversalTransitionModal → Modais Existentes

### 10.1 Mapa de Delegação

```
UniversalTransitionModal
│
├── action_behavior = intake
│   └── N/A (like/dislike no card, não usa modal de transição)
│
├── action_behavior = screening
│   ├── LIA auto → confirma → backend dispara triagem
│   └── Manual → [Abrir Triagem] → WSITriagemInviteModal ✅
│
├── action_behavior = scheduling
│   ├── LIA auto → confirma → backend dispara convite
│   └── Manual → [Abrir Agendamento] → UnifiedCommunicationModal(agendamento) ✅
│
├── action_behavior = evaluation
│   ├── LIA auto → confirma → backend dispara teste
│   └── Manual → [Abrir Envio de Teste] → TestSendModal ❌ (criar)
│
├── action_behavior = verification
│   ├── LIA auto → confirma → backend solicita dados
│   └── Manual → [Abrir Solicitação] → DataRequestModal ✅
│
├── action_behavior = offer
│   ├── LIA auto → confirma → backend envia proposta
│   └── Manual → [Abrir Proposta] → UnifiedCommunicationModal(proposta) ❌ (adaptar)
│
├── action_behavior = passive
│   └── Sem ação extra (apenas confirma movimentação)
│
├── action_behavior = conclusion_hired
│   ├── Confirma contratação
│   └── ☑ Enviar boas-vindas → [Personalizar] → UnifiedCommunicationModal(email) ✅
│
├── action_behavior = conclusion_rejected
│   ├── Pré-triagem: CandidateDecisionFlowModal(reject_pre_triage) ✅
│   ├── Pós-triagem: [Enviar Feedback] → UnifiedCommunicationModal(feedback) ✅
│   └── Apenas mover (sem comunicação) → confirma direto
│
└── action_behavior = conclusion_declined
    └── Formulário inline (radio motivo + campo livre) → confirma direto
```

### 10.2 Fluxo de Dados entre Modais

```
┌──────────────────────┐
│ UniversalTransition   │
│ Modal                 │
│                       │
│ Props necessárias:    │
│ - candidate           │
│ - currentStage        │  
│ - targetStage         │──────┐
│ - actionBehavior      │      │
│ - subStatuses[]       │      │ onActionClick(type)
│ - jobTitle            │      │
│ - jobId               │      │
│ - companyId           │      │
└───────────────────────┘      │
                               │
            ┌──────────────────┘
            │
            ▼
┌───────────────────────────────────┐
│  Modal Especializado              │
│                                   │
│  Recebe (via props):              │
│  - candidate (id, name, email...) │
│  - jobTitle                       │
│  - jobId                          │
│  - companyId                      │
│                                   │
│  Retorna (via callback):          │
│  - success: boolean               │
│  - action: string                 │
│  - metadata: any                  │
│                                   │
│  Ao fechar com sucesso:           │
│  → UniversalTransitionModal       │
│    confirma a transição           │
│    com sub-status atualizado      │
└───────────────────────────────────┘
```

---

## 11. Sistema de Badges nos Cards

### 11.1 No Kanban — Badges nos cards dos candidatos

Cada card no Kanban exibe badges que informam visualmente o estado atual do candidato naquela etapa:

```
┌────────────────────────────────────────────┐
│ 👤 João Silva                    85% ★     │
│    Product Designer • TechCorp             │
│                                            │
│ ┌──────────────────┐ ┌──────────────────┐  │
│ │ 🟢 Triagem       │ │ ⏳ Aguardando    │  │
│ │    Completa      │ │    Resposta      │  │
│ └──────────────────┘ └──────────────────┘  │
│                                            │
│ Skills: React, Node, Figma                 │
│                                            │
│ ┌──────────────────────────────────────┐   │
│ │ ⚠️ Sem resposta há 3 dias            │   │
│ └──────────────────────────────────────┘   │
└────────────────────────────────────────────┘
```

### 11.2 Tipos de Badge

| Tipo | Cor | Exemplo | Quando aparece |
|------|-----|---------|----------------|
| **Sub-status** | Varia (verde/amarelo/azul/cinza) | 🟢 Triagem Completa, 🟡 Agendada, 🔵 Teste Enviado | Sempre que tem sub-status definido |
| **Ação pendente do candidato** | Amarelo/âmbar | ⏳ Aguardando Resposta, ⏳ Aguardando Documentos | Quando candidato precisa agir |
| **Ação pendente do recrutador** | Azul/cyan | 📅 Agendar, 💬 Enviar Feedback, 📋 Avaliar Teste | Quando recrutador precisa agir |
| **Alerta** | Vermelho/laranja | ⚠️ Sem resposta há X dias, ⚠️ Prazo expirando, 🔴 Teste expirado | Quando há urgência ou prazo |
| **Conclusão** | Verde/vermelho | ✅ Proposta Aceita, ✕ Reprovado Entrevista | Quando etapa tem conclusão |

### 11.3 Lógica de Derivação das Badges

```
Badge = f(action_behavior, sub_status, timestamps, candidate_activity)
```

**Prioridade de exibição** (quando múltiplas badges se aplicam, exibir na ordem):
1. **Alerta** (prioridade máxima — vermelho/laranja)
2. **Ação pendente** (amarelo para candidato, cyan para recrutador)
3. **Sub-status** (informativo — cor varia)

#### Tabela Completa de Derivação

| `action_behavior` | `sub_status` | Condição temporal | Badge | Cor | Pendente de |
|---|---|---|---|---|---|
| `intake` | `novo` | — | Novo | cinza | Recrutador |
| `intake` | `aprovado` | — | 👍 Aprovado | verde | — |
| `intake` | `rejeitado` | — | 👎 Rejeitado | vermelho | — |
| `screening` | `convite_enviado` | < 7 dias | ⏳ Aguardando Triagem | amarelo | Candidato |
| `screening` | `convite_enviado` | ≥ 7 dias | ⚠️ Sem resposta há X dias | vermelho | Candidato |
| `screening` | `em_andamento` | — | 🔄 Triagem em Andamento | azul | Candidato |
| `screening` | `triagem_completa` | sem próxima ação | 📋 Avaliar Triagem | cyan | Recrutador |
| `scheduling` | `convite_enviado` | < 3 dias | ⏳ Aguardando Confirmação | amarelo | Candidato |
| `scheduling` | `convite_enviado` | ≥ 3 dias | ⚠️ Sem resposta há X dias | vermelho | Candidato |
| `scheduling` | `agendada` | data futura | 📅 Agendada DD/MM | verde | — |
| `scheduling` | `confirmada` | data futura | ✅ Confirmada DD/MM | verde | — |
| `scheduling` | `realizada` | sem avaliação | 📋 Avaliar Entrevista | cyan | Recrutador |
| `scheduling` | `reagendada` | — | 🔄 Reagendada DD/MM | amarelo | — |
| `scheduling` | `no_show` | — | ❌ No-show | vermelho | Recrutador |
| `scheduling` | `cancelada` | — | ✕ Cancelada | cinza | Recrutador |
| `evaluation` | `teste_enviado` | prazo > 24h | ⏳ Teste Pendente | amarelo | Candidato |
| `evaluation` | `teste_enviado` | prazo ≤ 24h | ⚠️ Prazo expirando | laranja | Candidato |
| `evaluation` | `teste_enviado` | prazo expirado | 🔴 Teste expirado | vermelho | Candidato |
| `evaluation` | `em_andamento` | — | 🔄 Teste em Andamento | azul | Candidato |
| `evaluation` | `concluido` | sem avaliação | 📋 Avaliar Teste | cyan | Recrutador |
| `verification` | `solicitacao_enviada` | < 5 dias | ⏳ Aguardando Documentos | amarelo | Candidato |
| `verification` | `solicitacao_enviada` | ≥ 5 dias | ⚠️ Sem resposta há X dias | vermelho | Candidato |
| `verification` | `parcialmente_recebido` | — | 📄 Docs Parciais | amarelo | Candidato |
| `verification` | `documentos_recebidos` | — | 📋 Verificar Docs | cyan | Recrutador |
| `offer` | `proposta_enviada` | < 5 dias | ⏳ Aguardando Resposta | amarelo | Candidato |
| `offer` | `proposta_enviada` | ≥ 5 dias | ⚠️ Sem resposta há X dias | vermelho | Candidato |
| `offer` | `contra_proposta` | — | 💬 Contra-proposta | laranja | Recrutador |
| `offer` | `proposta_aceita` | — | ✅ Proposta Aceita | verde | — |
| `passive` | (qualquer) | — | (sem badge obrigatório) | — | — |
| `conclusion_hired` | — | — | ✅ Contratado | verde | — |
| `conclusion_rejected` | (motivo) | — | ✕ Reprovado: {motivo} | vermelho | — |
| `conclusion_declined` | (motivo) | — | ↩️ Recusou: {motivo} | cinza | — |

#### Regras de Cálculo de Dias

```
dias_sem_resposta = (now - last_action_timestamp).days
prazo_restante = (test_deadline - now)

Limiares configuráveis por empresa (defaults):
- screening: alerta após 7 dias
- scheduling: alerta após 3 dias  
- verification: alerta após 5 dias
- offer: alerta após 5 dias
- evaluation: alerta prazo ≤ 24h, expirado = deadline passado
```

### 11.4 Na Tabela — Coluna "Status"

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Nome          │ Cargo            │ Etapa      │ Status                  │
│───────────────┼──────────────────┼────────────┼─────────────────────────│
│ João Silva    │ Product Designer │ Triagem    │ 🟢 Completa ℹ️          │
│ Maria Santos  │ Dev Frontend     │ Entrev. RH │ 🟡 Agendada 📅 18/02   │
│ Carlos Lima   │ DevOps Engineer  │ Teste Téc. │ 🔵 Enviado ⏳ 2 dias    │
│ Ana Costa     │ UX Researcher    │ Proposta   │ 🟡 Enviada ⏳ Resp.     │
│ Pedro Rocha   │ Backend Dev      │ Referências│ 🟠 Aguardando ⚠️ 5d    │
│                                                                         │
│ ℹ️ = tooltip com detalhes ao hover                                      │
│ 📅 = data agendada                                                      │
│ ⏳ = dias desde envio                                                    │
│ ⚠️ = alerta (hover mostra detalhes)                                     │
└──────────────────────────────────────────────────────────────────────────┘
```

Mesma lógica de derivação do Kanban, mas em formato compacto (tag + ícone + tooltip).

---

## 12. Disparos Automáticos (Email + WhatsApp)

### 12.1 Quando são disparados

Disparos automáticos acontecem quando o recrutador confirma uma transição com a opção **"LIA auto"** selecionada (que é o default).

### 12.2 Canais

| Canal | Quando ativo | Configuração |
|-------|-------------|--------------|
| **Email** | Sempre | Sempre ativo por padrão |
| **WhatsApp** | Se empresa tem integração configurada | Menu Configurações → Canais de Comunicação |

Quando ambos estão ativos, a LIA dispara **nos dois canais simultaneamente**. O candidato responde pelo canal que preferir.

### 12.3 Templates por `action_behavior`

| `action_behavior` | Situação do Template | Conteúdo do Disparo |
|--------------------|--------------------|---------------------|
| `screening` | `triagem` | Convite para responder perguntas de triagem WSI |
| `scheduling` | `agendamento` | Horários disponíveis para entrevista, link para escolher |
| `evaluation` | `avaliacao` | Link do teste, prazo para conclusão, instruções |
| `verification` | `solicitacao_dados` | Lista de documentos necessários, prazo |
| `offer` | `proposta` | Detalhes da proposta (salário, benefícios, modelo), prazo para resposta |
| `conclusion_rejected` | `feedback_construtivo` | Feedback construtivo sobre o processo |
| `conclusion_hired` | `boas_vindas` | Boas-vindas, próximos passos de onboarding |

### 12.4 Fluxo de Disparo

```
Recrutador confirma transição (modo LIA auto)
        │
        ▼
┌──────────────────────────────┐
│ Backend: TransitionService   │
│                              │
│ 1. Move candidato de etapa   │
│ 2. Atualiza sub-status       │
│ 3. Registra no histórico     │
│ 4. Identifica action_behavior│
│    da coluna destino         │
│ 5. Busca template padrão     │
│    (por empresa + situação)  │
│ 6. Gera mensagem             │
│    personalizada (LIA)       │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ CommunicationService         │
│                              │
│ 1. Verifica canais ativos    │
│    da empresa                │
│ 2. Prepara mensagem:         │
│    - Email: HTML formatado   │
│    - WhatsApp: texto limpo   │
│ 3. Dispara nos canais ativos │
│ 4. Registra no histórico     │
│    de comunicação            │
│ 5. Atualiza sub-status       │
│    para "Convite Enviado"    │
└──────────────────────────────┘
```

### 12.5 Personalização no Mini-prompt

O recrutador pode personalizar o disparo automático via mini-prompt:

```
Mini-prompt: "agendar para terça 14h, entrevista técnica com o Carlos"

→ LIA interpreta:
  - Tipo: Entrevista Técnica
  - Preferência: terça-feira 14:00
  - Entrevistador: Carlos (identifica pelo nome no time)
  
→ Email/WhatsApp enviado ao candidato inclui:
  - Sugestão de terça 14h
  - Opções alternativas (se calendário tiver conflito)
  - Nome do entrevistador Carlos
```

---

## 13. Retorno Automático de Candidatos

### 13.1 Conceito

Quando o candidato responde a uma ação (completa triagem, confirma entrevista, envia documentos), o sistema **automaticamente**:
1. Atualiza o sub-status do candidato
2. Em alguns casos, move o candidato para a próxima etapa
3. Notifica o recrutador

### 13.2 Mapa de Retornos

```
AÇÃO ENVIADA                    CANDIDATO RESPONDE           RESULTADO AUTOMÁTICO
─────────────                   ──────────────────           ────────────────────

Convite triagem WSI       →     Inicia triagem          →    Sub-status: "Em Andamento"
                          →     Completa triagem        →    Sub-status: "Triagem Completa"
                          →     Não responde (7 dias)   →    Sub-status: "Sem Resposta"
                                                             Badge alerta: ⚠️

Convite agendamento       →     Escolhe horário         →    Sub-status: "Agendada"
                          →     Confirma presença       →    Sub-status: "Confirmada"
                          →     Cancela/reagenda        →    Sub-status: "Reagendada"
                          →     Não comparece           →    Sub-status: "No-show"
                          →     Não responde (3 dias)   →    Badge alerta: ⚠️

Teste enviado             →     Inicia teste            →    Sub-status: "Em Andamento"
                          →     Conclui teste           →    Sub-status: "Concluído"
                          →     Prazo expira            →    Sub-status: "Expirado"
                                                             Badge alerta: 🔴

Solicitação de dados      →     Envia documentos        →    Sub-status: "Documentos Recebidos"
                          →     Envia parcialmente      →    Sub-status: "Parcialmente Recebido"
                          →     Não responde (5 dias)   →    Badge alerta: ⚠️

Proposta enviada          →     Aceita proposta         →    MOVE para "Contratado" ✅
                                                             Notifica recrutador 🔔
                          →     Recusa proposta         →    MOVE para "Proposta Recusada"
                                                             Notifica recrutador 🔔
                          →     Pede contra-proposta    →    Sub-status: "Contra-proposta"
                                                             Notifica recrutador 🔔
                          →     Não responde (5 dias)   →    Badge alerta: ⚠️
```

### 13.3 Movimentação Automática vs Atualização de Sub-status

| Retorno | Ação automática | Motivo |
|---------|----------------|--------|
| Triagem completa | **Sub-status** apenas | Recrutador precisa avaliar resultado antes de mover |
| Agendamento confirmado | **Sub-status** apenas | Entrevista ainda precisa acontecer |
| Teste concluído | **Sub-status** apenas | Recrutador precisa avaliar resultado |
| Documentos recebidos | **Sub-status** apenas | Recrutador precisa verificar |
| Proposta aceita | **MOVE para Contratado** | Decisão final do candidato, ação imediata |
| Proposta recusada | **MOVE para Proposta Recusada** | Decisão final do candidato, ação imediata |
| No-show | **Sub-status** apenas | Recrutador decide se reagenda ou reprova |

**Regra**: Só há movimentação automática quando a resposta do candidato é **definitiva** (aceitar/recusar proposta). Em todos os outros casos, apenas o sub-status é atualizado e o recrutador é notificado para tomar a decisão.

### 13.4 Cenários Edge-Case de Retorno

| Cenário | Comportamento |
|---------|--------------|
| Candidato completa triagem WSI com score < 50% | Sub-status: "Triagem Completa (Baixa Aderência)". Dispara WSI Post-Screening Feedback automaticamente. Recrutador é notificado para decisão. |
| Candidato cancela entrevista < 2h antes | Sub-status: "Cancelada (Tardio)". Notificação urgente ao recrutador. Slot é liberado no calendário. |
| Candidato pede reagendamento 2+ vezes | Sub-status: "Reagendada (3ª vez)". Badge: ⚠️ "Múltiplos reagendamentos". Recrutador decide se mantém. |
| Candidato envia documentos após prazo | Sub-status: "Documentos Recebidos (Atrasado)". Badge informa atraso. Recrutador decide se aceita. |
| Candidato desiste voluntariamente (qualquer etapa) | MOVE para coluna "Candidato Desistiu" (se existir) ou Sub-status: "Desistência Voluntária". Notifica recrutador. |
| Entrevista realizada mas candidato sai no meio | Sub-status: "Entrevista Incompleta". Badge: ⚠️. Recrutador decide próximo passo. |
| Teste com suspeita de fraude (ex: tab-switch excessivo) | Sub-status: "Concluído (Revisão Necessária)". Badge: ⚠️ "Suspeita de irregularidade". Recrutador avalia. |
| Proposta aceita e depois candidato volta atrás | Sub-status: "Desistência Pós-Aceite". MOVE para "Proposta Recusada". Notificação urgente ao recrutador. |
| Candidato responde via canal diferente do enviado | Sistema unifica: resposta é processada independente do canal de entrada. Sub-status atualizado normalmente. |

### 13.5 Timeouts e Escalação Automática

```
Timeout padrão (configurável por empresa):
─────────────────────────────────────────
screening:    7 dias → Sub-status "Sem Resposta" + Alerta
scheduling:   3 dias → Alerta ⚠️ (sem mudança de sub-status)
evaluation:   Baseado no prazo do teste (deadline do teste)
verification: 5 dias → Alerta ⚠️
offer:        5 dias → Alerta ⚠️

Escalação (configurável):
─────────────────────────
1º nível: Badge alerta no card (automático no timeout)
2º nível: Notificação push/email ao recrutador (timeout + 1 dia)
3º nível: Notificação ao gestor da vaga (timeout + 3 dias, se configurado)

Ação de timeout NUNCA move candidato automaticamente.
Apenas o recrutador decide mover, reprovar ou reenviar.
```

### 13.6 Notificações ao Recrutador

```
┌─────────────────────────────────────────────┐
│ 🔔 Notificação                              │
│                                              │
│ Toast (canto inferior direito):             │
│ ┌─────────────────────────────────────────┐ │
│ │ ✅ João Silva completou a triagem WSI   │ │
│ │    Analista de BI • Score: 82%          │ │
│ │    [Ver resultado]  [Mover candidato]   │ │
│ └─────────────────────────────────────────┘ │
│                                              │
│ Badge no Kanban:                             │
│ A coluna "Triagem" mostra contador:          │
│ ┌──────────┐                                 │
│ │ Triagem  │                                 │
│ │    🔴 3  │ ← 3 candidatos precisam de      │
│ │          │   atenção (triagem completa,     │
│ │          │   sem próxima ação)              │
│ └──────────┘                                 │
│                                              │
│ Badge no card do candidato:                  │
│ Atualiza automaticamente (ver Seção 11)      │
│                                              │
│ Histórico de atividade:                      │
│ Registrado no card do candidato com          │
│ timestamp e detalhes                         │
└─────────────────────────────────────────────┘
```

---

## 14. Herança de Pipeline: Empresa → Vaga

### 14.1 Fluxo de Herança

```
┌──────────────────────────────────────┐
│ EMPRESA (Menu Configurações)         │
│                                      │
│ Pipeline padrão:                     │
│ Funil → Triagem → Entrev.RH →       │
│ Teste Técnico → Entrev.Técnica →     │
│ Aprovados → Proposta → Contratado    │
│ + Reprovado                          │
│                                      │
│ Ações pré-configuradas por coluna:   │
│ - Templates padrão                   │
│ - Canal preferido                    │
│ - Modo (auto/manual)                 │
└──────────────┬───────────────────────┘
               │
               │ herda
               ▼
┌──────────────────────────────────────┐
│ VAGA (ao ser criada)                 │
│                                      │
│ Pipeline herdado:                    │
│ (cópia do pipeline da empresa)       │
│                                      │
│ is_customized = false                │
│                                      │
│ Recrutador pode:                     │
│ - Adicionar colunas (+)              │
│ - Remover colunas Catalog/Custom     │
│ - Reordenar colunas                  │
│ - Criar colunas custom               │
│                                      │
│ Ao customizar: is_customized = true  │
│ (não recebe mais atualizações da     │
│  empresa automaticamente)            │
└──────────────────────────────────────┘
```

### 14.2 Regras de Herança

| Regra | Descrição |
|-------|-----------|
| Vaga nova herda pipeline da empresa | Cópia completa (colunas, ordem, ações) |
| Vaga customizada é independente | Alterações na empresa não afetam vagas customizadas |
| Colunas System sempre presentes | Mesmo se vaga customizar, as 6 System permanecem |
| Colunas Catalog podem ser removidas | Recrutador pode tirar colunas que não se aplicam |
| Colunas Custom são por vaga | Criadas para aquela vaga específica |
| Reset possível | Recrutador pode "resetar para padrão da empresa" |

---

## 15. Menu Configurações — Pipeline da Empresa

### 15.1 Interface

```
┌──────────────────────────────────────────────────────────────────────┐
│ ⚙️ Configurações > Jornada de Recrutamento                          │
│──────────────────────────────────────────────────────────────────────│
│                                                                      │
│ Pipeline Padrão da Empresa                                           │
│ (Novas vagas herdam este pipeline)                                   │
│                                                                      │
│ ┌─ ETAPAS OBRIGATÓRIAS (System) ──────────────────────────────────┐  │
│ │                                                                  │  │
│ │  1. ████ Funil           Tipo: Intake (Entrada)         🔒      │  │
│ │  2. ████ Triagem         Tipo: Triagem WSI              🔒      │  │
│ │  3. ████ Entrevista RH   Tipo: Agendamento              🔒      │  │
│ │  ...                                                             │  │
│ │  N. ████ Aprovados       Tipo: Passiva                  🔒      │  │
│ │  N+1 ███ Contratado      Tipo: Contratação              🔒      │  │
│ │  ─── ███ Reprovado       Tipo: Rejeição                 🔒      │  │
│ │                                                                  │  │
│ └──────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│ ┌─ ETAPAS ADICIONAIS ─────────────────────────────────────────────┐  │
│ │                                                                  │  │
│ │  4. ░░░░ Teste Técnico    Tipo: [Avaliação/Teste  ▼]    [✏️][🗑]│  │
│ │  5. ░░░░ Entrev. Técnica  Tipo: [Agendamento     ▼]    [✏️][🗑]│  │
│ │  6. ░░░░ Referências      Tipo: [Solic. Dados    ▼]    [✏️][🗑]│  │
│ │  7. ░░░░ Proposta         Tipo: [Proposta         ▼]    [✏️][🗑]│  │
│ │                                                                  │  │
│ │  ↕ Arrastar para reordenar                                       │  │
│ │                                                                  │  │
│ └──────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  [+ Adicionar do Catálogo]  [+ Criar Nova Etapa]                     │
│                                                                      │
│ ┌─ PRÉ-CONFIGURAÇÃO DE AÇÕES ─────────────────────────────────────┐  │
│ │                                                                  │  │
│ │ Para cada etapa adicional, configure:                             │  │
│ │                                                                  │  │
│ │ Teste Técnico:                                                   │  │
│ │   Template padrão: [Convite Teste Técnico      ▼]                │  │
│ │   Canal preferido: [Email + WhatsApp           ▼]                │  │
│ │   Modo padrão:     [● LIA automático ○ Manual  ]                 │  │
│ │                                                                  │  │
│ │ Entrev. Técnica:                                                 │  │
│ │   Template padrão: [Convite Entrevista         ▼]                │  │
│ │   Canal preferido: [Email + WhatsApp           ▼]                │  │
│ │   Modo padrão:     [● LIA automático ○ Manual  ]                 │  │
│ │                                                                  │  │
│ └──────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│                                              [Cancelar]  [Salvar]    │
└──────────────────────────────────────────────────────────────────────┘
```

### 15.2 Dropdown "Tipo de Ação" (label amigável para `action_behavior`)

| Label no dropdown | `action_behavior` | Descrição |
|-------------------|-------------------|-----------|
| Entrada (Funil) | `intake` | Candidatos entram, like/dislike |
| Triagem WSI | `screening` | Triagem automatizada pela LIA |
| Agendamento | `scheduling` | Agendamento de entrevista/reunião |
| Avaliação / Teste | `evaluation` | Envio de teste ou case |
| Solicitação de Dados | `verification` | Pedido de documentos/referências |
| Proposta | `offer` | Envio de proposta formal |
| Passiva (sem ação) | `passive` | Apenas organização, sem disparo |
| Contratação | `conclusion_hired` | Confirma contratação |
| Rejeição | `conclusion_rejected` | Reprovação com feedback |
| Proposta Recusada | `conclusion_declined` | Registro de recusa |

---

## 16. Criação de Colunas Customizadas com LIA

### 16.1 Fluxo de Criação

```
Recrutador clica [+ Criar Nova Etapa]
                    │
                    ▼
        ┌───────────────────────┐
        │ Nome: [Dinâmica Grupo]│
        │                       │
        │ Descrição (opcional): │
        │ [Atividade em grupo   │
        │  para avaliar soft    │
        │  skills]              │
        │                       │
        │         [Criar]       │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ 🤖 LIA sugere:        │
        │                       │
        │ Tipo de Ação:         │
        │ ● Agendamento         │
        │                       │
        │ Motivo: "Dinâmica de  │
        │ grupo envolve agendar │
        │ data, horário e local │
        │ com participantes"    │
        │                       │
        │ Sub-statuses sugeridos:│
        │ ☑ Convite Enviado     │
        │ ☑ Agendada            │
        │ ☑ Confirmada          │
        │ ☑ Realizada           │
        │ ☐ (adicionar custom)  │
        │                       │
        │ [Alterar tipo ▼]      │
        │ [Confirmar]           │
        └───────────────────────┘
```

### 16.2 Endpoint de Inferência

```
POST /api/v1/stages/infer-behavior

Request:
{
  "name": "Dinâmica de Grupo",
  "description": "Atividade em grupo para avaliar soft skills"
}

Response:
{
  "suggested_behavior": "scheduling",
  "confidence": 0.85,
  "reasoning": "Dinâmica de grupo envolve agendamento...",
  "suggested_sub_statuses": [
    "Convite Enviado",
    "Agendada", 
    "Confirmada",
    "Realizada"
  ]
}
```

---

## 17. Fluxos Completos End-to-End

### 17.1 Fluxo: Candidato do Funil ao Contratado (Automático)

```
1. Candidato entra no FUNIL
   → Card aparece com like/dislike
   → Recrutador clica 👍 Like

2. Like abre CandidateDecisionFlowModal (approve_to_triage)
   → Recrutador confirma
   → Candidato move para TRIAGEM
   → LIA dispara convite de triagem (Email + WhatsApp)
   → Badge: "⏳ Aguardando Triagem"

3. Candidato responde triagem
   → Sub-status: "Em Andamento" → "Triagem Completa"
   → Badge: "🟢 Triagem Completa"
   → Notificação ao recrutador: "João completou triagem, Score: 82%"

4. Recrutador arrasta candidato para ENTREVISTA RH
   → UniversalTransitionModal abre
   → action_behavior = scheduling
   → Recrutador escolhe "LIA auto" + prompt: "amanhã 14h"
   → Confirma
   → LIA dispara convite com sugestão de horário (Email + WhatsApp)
   → Badge: "⏳ Aguardando Confirmação"

5. Candidato confirma horário
   → Sub-status: "Confirmada"
   → Badge: "🟡 Confirmada 📅 19/02 14h"
   → Notificação ao recrutador

6. Entrevista realizada
   → Recrutador atualiza sub-status para "Realizada"
   → Recrutador arrasta para TESTE TÉCNICO

7. UniversalTransitionModal abre (action_behavior = evaluation)
   → Recrutador escolhe "LIA auto"
   → LIA dispara teste (Email + WhatsApp)
   → Badge: "⏳ Teste Pendente"

8. Candidato completa teste
   → Sub-status: "Concluído"
   → Badge: "🟢 Teste Concluído"
   → Notificação ao recrutador com score

9. Recrutador avalia e arrasta para APROVADOS
   → action_behavior = passive
   → Modal simples, confirma
   → Badge: "🟢 Aprovado"

10. Recrutador arrasta para PROPOSTA
    → action_behavior = offer
    → Recrutador escolhe "Manual → [Abrir Proposta]"
    → Abre UnifiedCommunicationModal(type=proposta)
    → Define salário, benefícios, prazo
    → Envia
    → Badge: "⏳ Proposta Enviada"

11. Candidato aceita proposta
    → MOVIMENTAÇÃO AUTOMÁTICA para CONTRATADO
    → Notificação ao recrutador: "🎉 João aceitou a proposta!"
    → LIA dispara email de boas-vindas
    → Badge: "✅ Proposta Aceita"
```

### 17.2 Fluxo: Rejeição Pós-Triagem

```
1. Candidato está em TRIAGEM com sub-status "Triagem Completa"
   → Recrutador avalia: Score WSI = 35% (abaixo do threshold)

2. Recrutador arrasta para REPROVADO
   → UniversalTransitionModal abre
   → action_behavior = conclusion_rejected
   → Sistema detecta: candidato participou da triagem (pós-triagem)
   → Mostra: "Recomendamos enviar feedback construtivo"
   → Opção: ● Enviar feedback → [Abrir Feedback]  (recomendado)
            ○ Apenas mover

3. Recrutador clica [Abrir Feedback]
   → UnifiedCommunicationModal abre (type = feedback)
   → Template de feedback construtivo pré-carregado
   → Recrutador personaliza se quiser
   → Envia

4. Volta ao UniversalTransitionModal
   → Confirma movimentação
   → Candidato vai para REPROVADO
   → Sub-status: "Reprovado Triagem"
   → Feedback registrado no histórico
```

### 17.3 Fluxo: Agendamento Manual

```
1. Recrutador arrasta candidato para ENTREVISTA TÉCNICA
   → UniversalTransitionModal abre
   → action_behavior = scheduling

2. Recrutador escolhe:
   ○ LIA auto
   ● Manual → [Abrir Agendamento]

3. Clica [Abrir Agendamento]
   → UnifiedCommunicationModal abre (type = agendamento)
   → Canal: Email / WhatsApp
   → Tipo: Técnica
   → Plataforma: Zoom
   → Duração: 1 hora
   → Data: 20/02/2026
   → Hora: 15:00
   → Entrevistador: Carlos Mendes - Tech Lead
   → Template: "Convite Entrevista Técnica"
   → Preview do email
   → Clica [Enviar Email]

4. Volta ao UniversalTransitionModal
   → Sub-status automaticamente: "Agendada"
   → Confirma movimentação

5. Resultado:
   → Candidato em ENTREVISTA TÉCNICA
   → Sub-status: "Agendada"
   → Badge: "🟡 Agendada 📅 20/02 15h"
   → Email enviado ao candidato
   → Evento no calendário do entrevistador
```

---

## 18. Plano Faseado de Implementação

### Fase 1 — Fundação: Modelo de Dados e Catálogo

| # | Tarefa | Tipo | Dependência |
|---|--------|------|-------------|
| F1.1 | Adicionar `action_behavior` ao modelo RecruitmentStage + campos auxiliares | Backend | — |
| F1.2 | Criar STANDARD_STAGE_CATALOG + endpoint GET /api/v1/stage-catalog | Backend | F1.1 |
| F1.3 | Endpoints de pipeline por empresa (GET/PUT/POST) | Backend | F1.1 |
| F1.4 | Herança empresa→vaga (GET/PUT pipeline por vaga) | Backend | F1.3 |
| F1.5 | Refatorar RecruitmentJourneyConfig no Menu Configurações | Frontend | F1.2, F1.3 |

### Fase 2 — Motor de Transição e Modal

| # | Tarefa | Tipo | Dependência |
|---|--------|------|-------------|
| F2.1 | Remover allowed_transitions, movimentação livre | Backend | F1.1 |
| F2.2 | Endpoint interpret-context (mini-prompt LIA) | Backend | F2.1 |
| F2.3 | Criar UniversalTransitionModal compacto | Frontend | F2.1 |
| F2.4 | Seção de ação por action_behavior (botões delegadores) | Frontend | F2.3 |
| F2.5 | Refatorar use-drag-drop.ts para usar UniversalTransitionModal | Frontend | F2.3 |
| F2.6 | Dropdown de etapa na tabela + botão "Configurar Etapas" | Frontend | F2.3 |
| F2.7 | Sistema de badges nos cards do Kanban | Frontend | F2.1 |
| F2.8 | Coluna "Status" com badges na tabela | Frontend | F2.7 |

### Fase 3 — Integração com Modais Existentes

| # | Tarefa | Tipo | Dependência |
|---|--------|------|-------------|
| F3.1 | Integração: screening → WSITriagemInviteModal | Frontend | F2.4 |
| F3.2 | Integração: scheduling → UnifiedCommunicationModal(agendamento) | Frontend | F2.4 |
| F3.3 | Integração: rejection → UnifiedCommunicationModal(feedback) | Frontend | F2.4 |
| F3.4 | Integração: verification → DataRequestModal | Frontend | F2.4 |

### Fase 4 — Disparos Automáticos

| # | Tarefa | Tipo | Dependência |
|---|--------|------|-------------|
| F4.1 | Serviço de disparo automático (Email + WhatsApp) | Backend | F2.1 |
| F4.2 | Configuração de canais por empresa | Backend | F4.1 |

### Fase 5 — Retorno Automático de Candidatos

| # | Tarefa | Tipo | Dependência |
|---|--------|------|-------------|
| F5.1 | Webhooks para retorno: triagem, agendamento, teste, docs | Backend | F4.1 |
| F5.2 | Retorno de proposta: aceitar/recusar → movimentação automática | Backend | F5.1 |
| F5.3 | Notificações em tempo real + histórico de atividade | Frontend | F5.1, F2.7 |

### Fase 6 — Gaps e Customizações

| # | Tarefa | Tipo | Dependência |
|---|--------|------|-------------|
| F6.1 | Criar TestSendModal | Frontend | F3.1 |
| F6.2 | Adaptar UnifiedCommunicationModal para type=proposta | Frontend | F3.2 |
| F6.3 | Botão "+" no Kanban (catálogo + criar nova) | Frontend | F1.2, F1.5 |
| F6.4 | Pré-cadastro de ações por coluna no Menu Configurações | Frontend | F1.5, F4.2 |
| F6.5 | Endpoint infer-behavior (LIA sugere tipo para coluna custom) | Backend | F1.2 |
| F6.6 | Testes end-to-end e documentação | Full-stack | Todas |

### Diagrama de Dependências

```
F1.1 ──→ F1.2 ──→ F1.5
  │        │
  │        └──→ F6.3
  │        └──→ F6.5
  │
  ├──→ F1.3 ──→ F1.4
  │              │
  │              └──→ F1.5
  │
  └──→ F2.1 ──→ F2.2
         │
         ├──→ F2.3 ──→ F2.4 ──→ F3.1
         │     │         │        F3.2
         │     │         │        F3.3
         │     │         │        F3.4
         │     │         │
         │     │         └──→ F6.1
         │     │         └──→ F6.2
         │     │
         │     ├──→ F2.5
         │     └──→ F2.6
         │
         ├──→ F2.7 ──→ F2.8
         │              │
         │              └──→ F5.3
         │
         └──→ F4.1 ──→ F4.2
                │        │
                │        └──→ F6.4
                │
                └──→ F5.1 ──→ F5.2
                       │
                       └──→ F5.3
```

---

## 19. Gaps e Modais a Criar

### 19.1 Gap 1: TestSendModal (Envio de Teste)

**Problema**: Os modais `TechnicalTestModal` e `EnglishTestModal` existentes são de **visualização de resultados**. Não existe modal para **enviar** um teste ao candidato.

**Solução**: Criar `TestSendModal` (~250 linhas)

```
Funcionalidade:
- Tipo de teste (Técnico / Case Prático / Inglês / Personalizado)
- Link ou upload do teste
- Prazo para entrega (dias)
- Canal (Email / WhatsApp)
- Mensagem com template (reutiliza MessageComposer existente)
- Preview da mensagem
```

**Componentes reutilizados**: `MessageComposer`, templates de comunicação, `Dialog/DialogContent` do shadcn.

### 19.2 Gap 2: UnifiedCommunicationModal (type=proposta)

**Problema**: O `UnifiedCommunicationModal` suporta 5 tipos (email, whatsapp, triagem, agendamento, feedback) mas não tem `proposta`.

**Solução**: Adaptar o modal existente (~120 linhas adicionais)

```
Campos adicionais para type=proposta:
- Salário (valor + moeda)
- Modelo de contratação (CLT / PJ / Cooperativa / Estágio)
- Benefícios (seleção múltipla do catálogo da empresa)
- Data de início prevista
- Prazo para resposta (dias)
- Template de proposta específico
```

**Nota**: O `DataRequestModal` já tem template "Proposta/Admissão" para solicitar documentos. O fluxo seria: (1) enviar proposta → (2) candidato aceita → (3) solicitar documentos de admissão.

---

## 20. Glossário

| Termo | Definição | Seção de referência |
|-------|-----------|---------------------|
| **Pipeline** | Sequência de colunas/etapas que representam o processo seletivo de uma vaga | §1 |
| **Coluna / Etapa** | Uma fase do processo seletivo (ex: Triagem, Entrevista RH, Teste Técnico) | §2, §3 |
| **System (coluna)** | Coluna obrigatória presente em toda vaga, não pode ser removida (Funil, Contratado, Reprovado) | §2.1 |
| **Catalog (coluna)** | Coluna pré-configurada disponível para adicionar ao pipeline (13 colunas no catálogo) | §2.2, §3 |
| **Custom (coluna)** | Coluna criada pelo recrutador para uma necessidade específica, com sugestão de LIA | §2.3, §16 |
| **`action_behavior`** | Tipo de ação associada a uma coluna que define o que acontece na movimentação. 10 tipos: intake, screening, scheduling, evaluation, verification, offer, passive, conclusion_hired, conclusion_rejected, conclusion_declined | §4 |
| **Sub-status** | Estado detalhado do candidato dentro de uma coluna (ex: "Agendada", "Confirmada", "No-show"). Derivado do action_behavior | §4, §11 |
| **UniversalTransitionModal** | Modal compacto (~250L) que aparece em toda movimentação de candidato. Contém: header, sub-status, mini-prompt, e BOTÕES para abrir modais especializados | §7 |
| **Modal especializado** | Modal existente com funcionalidade completa, aberto via botão do UniversalTransitionModal. Inclui: UnifiedCommunicationModal, WSITriagemInviteModal, DataRequestModal, InterviewSchedulingModal, TestSendModal, CandidateDecisionFlowModal | §9, §10 |
| **Delegação de modal** | Padrão arquitetural: o UniversalTransitionModal NUNCA duplica lógica de modais existentes — sempre delega via botão que abre o modal especializado | §7, §10 |
| **LIA auto** | Modo em que a LIA executa ações automaticamente (dispara mensagens por Email + WhatsApp, agenda horários). O recrutador pode personalizar via mini-prompt | §5, §12 |
| **Manual** | Modo em que o recrutador clica botão no UniversalTransitionModal → abre modal especializado com todos os controles (canal, template, data/hora, etc.) | §5, §8 |
| **Mini-prompt** | Campo de texto opcional no modal de transição para contexto em linguagem natural. No modo LIA auto, personaliza o disparo. No modo manual, é passado como contexto ao modal especializado | §7.3 |
| **Badge** | Indicador visual no card do candidato. 5 tipos: sub-status, ação pendente candidato, ação pendente recrutador, alerta temporal, conclusão. Derivados de f(action_behavior, sub_status, timestamps, activity) | §11 |
| **Disparo automático** | Envio de mensagem ao candidato por Email + WhatsApp (ou apenas Email para offer/hired) quando modo LIA auto é selecionado | §12 |
| **Retorno automático** | Atualização de sub-status (ou movimentação em casos definitivos) quando candidato responde a uma ação. Movimentação automática apenas em proposta aceita/recusada | §13 |
| **Timeout / Escalação** | Sistema de prazos configuráveis por empresa. Após timeout: badge alerta → notificação recrutador → notificação gestor. Nunca move candidato automaticamente | §13.5 |
| **Herança de pipeline** | Pipeline padrão da empresa (definido em Menu Configurações) é copiado para novas vagas. Vaga pode customizar sem afetar template empresa | §14 |
| **Movimentação livre** | Candidato pode ser movido para QUALQUER coluna a qualquer momento (drag-and-drop no Kanban ou dropdown na tabela). Não existem mais rotas restritas | §6 |
| **WSI** | WeDoTalent Skill Index — metodologia de avaliação de candidatos em 7 blocos (técnico, comportamental, cultural) | §1 |
| **Triagem WSI** | Processo automatizado de perguntas e avaliação do candidato usando a metodologia WSI. Candidato recebe convite, responde, e recebe score de aderência | §8.2 |
| **TestSendModal** | Modal a ser criado (~250L) para envio de testes técnicos, inglês, case study. Gap identificado | §19 |
| **Ações em massa** | Barra de ações que aparece ao selecionar múltiplos candidatos. Cada ação abre modal correspondente em modo bulk | Apêndice A |
| **Catálogo de colunas** | Biblioteca de colunas pré-configuradas com action_behavior, sub-statuses e ícone. Servido pelo endpoint `/api/v1/stage-catalog` | §3, Apêndice B |

---

## Apêndice A: Barra de Ações em Massa

> **Atualizado em 20/02/2026**: Consolidação de ações para reduzir complexidade e aumentar automação.
> Removidos: Agendar (absorvido por Mover Etapa + action_behavior), Email/WhatsApp separados (consolidados em "Mensagem"), Feedback (absorvido por Reprovar/Mensagem).

As barras de ações são **contextuais** — mostram botões diferentes conforme o ambiente:

### A.1 Dentro da Vaga (Kanban/Tabela)

Candidatos já vinculados a uma vaga com posição no pipeline.

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ ○ Selecionar todos   👥 2 candidatos selecionados de 20                         │
│                                                                                  │
│ [→ Mover Etapa] [📋 Lista] [🔗 Compartilhar] [🔬 Triagem WSI]                   │
│ [📄 Solicitar Dados] [✉️ Mensagem] [⭐ Favoritos] [🤖 Análise LIA]              │
│ [🔴 Reprovar]                                                        × Limpar    │
└──────────────────────────────────────────────────────────────────────────────────┘
```

| Botão | Modal/Ação | Notas |
|-------|-----------|-------|
| **Mover Etapa** | UniversalTransitionModal (bulk) | Ação principal — dispara ações automáticas via action_behavior da coluna destino. Absorve "Agendar" (scheduling), "Triagem" ao mover para coluna Triagem, etc. |
| **Lista** | AddToListModal | Adicionar candidatos a uma lista de talentos |
| **Compartilhar** | ShareSearchModal | Compartilhar perfis com gestores/colegas |
| **Triagem WSI** | WSITriagemInviteModal (bulk) | Atalho direto para triagem sem mover etapa |
| **Solicitar Dados** | DataRequestModal (bulk) | Solicitar documentos/dados do candidato |
| **Mensagem** | UnifiedCommunicationModal (escolha de canal Email/WhatsApp) | Consolidou "Email" e "WhatsApp" num único botão com seleção de canal |
| **Favoritos** | Toggle favorito (lista especial pré-criada) | Adiciona/remove da lista única "Favoritos" |
| **Análise LIA** | Análise comparativa em lote | Análise de perfil pela IA |
| **Reprovar** | CandidateDecisionFlowModal (reject, bulk) | Inclui feedback automático pós-triagem |

### A.2 Funil de Talentos (Resultados de Busca)

Candidatos **sem vaga vinculada** — perfis no banco de talentos.

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 👥 3 candidatos selecionados                                                     │
│                                                                                  │
│ [📌 Vaga] [📋 Lista] [🔗 Compartilhar] [✉️ Mensagem] [🔬 Triagem WSI]           │
│ [⭐ Favoritos] [👁 Ocultar] [🤖 Análise LIA]                          × Limpar   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

| Botão | Modal/Ação | Notas |
|-------|-----------|-------|
| **Vaga** | AddCandidatesToVacancyModal | Ação principal — vincular ao pipeline de uma vaga |
| **Lista** | AddToListModal | Organização de talentos por tema |
| **Compartilhar** | ShareSearchModal | Enviar perfis para validação |
| **Mensagem** | UnifiedCommunicationModal (escolha de canal) | Abordagem ativa (convite, networking) |
| **Triagem WSI** | WSITriagemInviteModal | Sourcing ativo — triagem antes de vincular à vaga |
| **Favoritos** | Toggle favorito (lista especial) | Lista única pré-criada pelo sistema |
| **Ocultar** | Oculta candidato dos resultados | Filtro pessoal do recrutador |
| **Análise LIA** | Análise de perfil pela IA | Cruzar perfil vs. vagas abertas |

### A.3 Ações removidas e justificativa

| Ação removida | Motivo | Substituída por |
|---------------|--------|-----------------|
| **Agendar** | Absorvido pelo sistema de transição: ao mover para coluna com `action_behavior=scheduling`, o UniversalTransitionModal já oferece agendamento automático (LIA) ou manual | Mover Etapa + mini-prompt LIA |
| **Email** (separado) | Canal de comunicação, não ação. Consolidado com WhatsApp | Mensagem (com seleção de canal) |
| **WhatsApp** (separado) | Canal de comunicação, não ação. Consolidado com Email | Mensagem (com seleção de canal) |
| **Feedback** | Ação contextual de reprovação, não ação independente. Na vaga: absorvido por Reprovar (que já inclui feedback pós-triagem). No funil: sem contexto de processo para feedback | Reprovar (na vaga) / Mensagem (comunicação geral) |

---

## Apêndice B: Endpoints da API

### Pipeline e Catálogo

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/stage-catalog` | Retorna catálogo de colunas disponíveis |
| GET | `/api/v1/company/{id}/pipeline` | Pipeline padrão da empresa |
| PUT | `/api/v1/company/{id}/pipeline` | Atualiza pipeline padrão |
| POST | `/api/v1/company/{id}/pipeline/stages` | Adiciona coluna ao pipeline |
| GET | `/api/v1/jobs/{id}/pipeline` | Pipeline da vaga (herdado ou customizado) |
| PUT | `/api/v1/jobs/{id}/pipeline` | Customiza pipeline da vaga |

### Transições

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/candidates/{id}/transition` | Move candidato de etapa |
| POST | `/api/v1/transition/interpret-context` | Interpreta mini-prompt LIA |

### Inferência e IA

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/stages/infer-behavior` | LIA sugere action_behavior |

### Comunicação

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/company/{id}/communication-config` | Configuração de canais |
| PUT | `/api/v1/company/{id}/communication-config` | Atualiza configuração |

---

---

## 21. Status de Implementação e Roadmap

> Atualizado em 20/02/2026

### 21.1 Status das Fases

| Fase | Descrição | Status | Notas |
|------|-----------|--------|-------|
| **Fase 1** | Fundação: Modelo de Dados e Catálogo (3-layer, STANDARD_STAGE_CATALOG) | ✅ IMPLEMENTADO | action_behavior no modelo, catálogo de colunas, endpoints de pipeline |
| **Fase 2** | Motor de Transição e Modal (UniversalTransitionModal, action_behavior mapping, sub-status system) | ✅ IMPLEMENTADO | UniversalTransitionModal (527L), badges, use-drag-drop, movimentação livre |
| **Fase 3** | Integração com Modais Existentes (CandidateDecisionFlowModal, Badge system) | ✅ IMPLEMENTADO | 7 tipos de modal wired via handleOpenSpecializedModal |
| **Fase 4** | Disparos Automáticos (Email + WhatsApp, Templates, Communication integration) | ✅ IMPLEMENTADO | TransitionDispatchService: determinístico, template→render→envio |
| **Fase 5** | Retorno Automático de Candidatos (ReturnEventService, 11 event types, auto-move, ActivityFeed) | ✅ IMPLEMENTADO | Webhooks, sub-status updates, movimentação automática, polling |
| **Fase 6** | Pipeline Configuration (Add column, Infer-behavior, stage catalog) | ✅ IMPLEMENTADO | Botão "+", endpoint `/infer-behavior`, UI de configuração |
| **Fase 7** | Pipeline Inheritance (Company→Job, is_pipeline_customized, reset endpoint) | ✅ IMPLEMENTADO | Herança de pipeline, vaga customizável, endpoints de reset |
| **Fase 8** | Inline Column Editing (ColumnContextMenu, PATCH/DELETE/reorder endpoints) | ✅ IMPLEMENTADO | Menu contextual no header, edição inline, reordenação |

### 21.2 Inventário de Modais — Status Atual

| action_behavior | Modal Modo Manual | Status | Como funciona hoje |
|---|---|---|---|
| `intake` | Like/Dislike → CandidateDecisionFlowModal | ✅ Implementado | Abre via decision-flow handler |
| `screening` | WSITriagemInviteModal | ✅ Implementado | Abre modal de convite de triagem WSI |
| `scheduling` | UnifiedCommunicationModal (type=agendamento) | ✅ Implementado | Abre com situation=agendamento, templates filtrados |
| `evaluation` | UnifiedCommunicationModal (type=email, situation=avaliacao_tecnica) | 🔶 Adaptado | Usa modal genérico de email com template de avaliação. Falta TestSendModal dedicado |
| `verification` | DataRequestModal | ✅ Implementado | Modal de solicitação de dados/documentos |
| `offer` | UnifiedCommunicationModal (type=email, situation=proposta) | 🔶 Adaptado | Usa modal genérico de email com template de proposta. Falta campos dedicados (salário, benefícios, modelo contratação) |
| `passive` | — (sem ação) | ✅ N/A | Movimentação direta sem modal de ação |
| `conclusion_hired` | CandidateDecisionFlowModal | ✅ Implementado | Fluxo de decisão de aprovação |
| `conclusion_rejected` | CandidateDecisionFlowModal + UnifiedCommunicationModal (feedback) | ✅ Implementado | Decision flow + botão de feedback construtivo |
| `conclusion_declined` | Formulário inline (radio motivo) | ✅ Implementado | Inline no UniversalTransitionModal |

### 21.3 Modais a Criar ou Refinar

#### Gap 1: TestSendModal (Prioridade: Alta)

**Problema**: `evaluation` usa modal genérico de email. O recrutador não consegue configurar tipo de teste, prazo, link/upload do teste.

**Solução**: Criar `TestSendModal` dedicado (~300 linhas)

```
Funcionalidade necessária:
├── Tipo de teste (Técnico / Case Prático / Inglês / Personalizado)
├── Link do teste ou upload de arquivo
├── Prazo para entrega (dias)
├── Instruções adicionais (campo texto)
├── Canal (Email / WhatsApp)
├── Template de envio (filtrado por situation=avaliacao_tecnica)
├── Preview da mensagem
└── Envio com confirmação
```

**Dependências**: Sistema de upload de arquivos (se permitir upload), templates de avaliação no banco.

#### Gap 2: ProposalModal — Campos Dedicados (Prioridade: Alta)

**Problema**: `offer` usa modal genérico de email. Não tem campos estruturados para proposta formal.

**Solução**: Criar `ProposalModal` ou adaptar UnifiedCommunicationModal com seção de proposta (~200 linhas adicionais)

```
Campos adicionais necessários:
├── Salário (valor + moeda + periodicidade)
├── Modelo de contratação (CLT / PJ / Cooperativa / Estágio)
├── Benefícios (seleção múltipla do catálogo da empresa)
├── Data de início prevista
├── Prazo para resposta (dias)
├── Bônus / variável (opcional)
├── Template de proposta específico
└── Geração de PDF formal (futuro)
```

**Nota**: O fluxo completo seria: (1) enviar proposta → (2) candidato aceita → (3) solicitar documentos de admissão via DataRequestModal.

#### Gap 3: SchedulingModal Dedicado (Prioridade: Média)

**Problema**: `scheduling` usa UnifiedCommunicationModal com template de agendamento. Funciona, mas não integra com calendário, não mostra disponibilidade, não permite seleção de entrevistador.

**Solução futura**: Integrar com InterviewSchedulingModal existente (usado no chat-page) ou criar versão adaptada para o Kanban.

```
Funcionalidade desejada (futuro):
├── Tipo de entrevista (RH / Técnica / Gestor / Final)
├── Plataforma (Zoom / Meet / Teams / Presencial)
├── Duração (30min / 1h / 1h30 / 2h)
├── Seleção de entrevistador (lista da empresa)
├── Calendário visual com disponibilidade
├── Data e horário selecionados
├── Link automático da plataforma
├── Template pré-preenchido com detalhes
└── Integração com calendário (Google / Outlook)
```

### 21.4 Refinamentos Pendentes

#### R1: Bulk Rejection com Sub-Status Individualizado (Prioridade: Alta)

**Problema**: Ao reprovar múltiplos candidatos em bulk, todos recebem o mesmo sub-status e o mesmo template de feedback.

**Impacto**: Em cenários reais, cada candidato pode ter motivo de rejeição diferente (outro candidato selecionado, perfil inadequado, desistência) e merece feedback personalizado.

**Opções de design a explorar**:

```
Opção A: Sub-status por Agrupamento
─────────────────────────────────────
1. Recrutador seleciona 10 candidatos para reprovar
2. Modal apresenta lista dos 10 com dropdown de sub-status individual
3. Recrutador agrupa: 6 "outro candidato", 3 "perfil inadequado", 1 "desistiu"
4. Cada grupo recebe template de feedback adequado
5. Confirma → 10 emails diferentes enviados

Opção B: LIA Sugere Sub-Status Individual
──────────────────────────────────────────
1. Recrutador seleciona 10 candidatos para reprovar
2. LIA analisa histórico de cada um:
   - Quanto avançou no pipeline
   - Scores WSI
   - Notas de entrevista
   - Tempo no processo
3. LIA sugere sub-status mais provável para cada candidato
4. Recrutador revisa/ajusta na lista
5. Confirma → envios individualizados

Opção C: Templates com Condicionais
────────────────────────────────────
1. Template único de rejeição com blocos condicionais:
   {{#if perfil_inadequado}}
     Texto genérico de feedback
   {{/if}}
   {{#if outro_candidato_selecionado}}
     Texto empático sobre outro candidato
   {{/if}}
2. Sub-status determina qual bloco é renderizado
3. Mantém operação bulk com personalização automática
```

**Desafio UX**: Equilibrar velocidade operacional (bulk) com qualidade de personalização (individual).

**Aplica-se a**: conclusion_rejected, conclusion_declined.

**Dependências**: Sistema de templates condicionais, mapeamento refinado sub-status → template situation.

#### R2: Layer 2 — Interpretação LLM do Mini-Prompt (Prioridade: Média)

**Problema**: No modo "LIA auto" atual (Layer 1), o disparo é puramente determinístico: busca template, renderiza variáveis, envia. O campo "mini-prompt" do recrutador não é interpretado.

**Solução futura**: Quando o recrutador escreve no mini-prompt (ex: "agende para terça às 14h", "envie feedback mencionando que ficamos impressionados com o teste"), a LIA deve:
1. Interpretar o prompt via LLM
2. Extrair informações relevantes (data, hora, observações)
3. Personalizar o template com as informações extraídas
4. Enviar a versão personalizada

**Dependências**: Integração com sistema de agentes (LangGraph), endpoint interpret-context.

#### R3: Retorno Automático de Candidatos (Prioridade: Média)

**Problema**: Após disparo automático, o sistema não reage quando o candidato responde (completa triagem, confirma entrevista, entrega teste).

**Solução futura**:
- Webhooks para cada tipo de resposta
- Atualização automática de sub-status (ex: "Convite Enviado" → "Triagem Completa")
- Movimentação automática apenas em casos definitivos (proposta aceita → Contratado, proposta recusada → Proposta Recusada)
- Notificação ao recrutador em tempo real

#### R4: Configuração de Canais por Empresa (Prioridade: Baixa)

**Problema**: Hoje o canal (email/WhatsApp) é escolhido pelo recrutador a cada transição. Não há configuração padrão por empresa.

**Solução futura**: Menu Configurações → Comunicação → Canal padrão por tipo de ação (ex: "Agendamento sempre por Email + WhatsApp", "Proposta sempre por Email apenas").

#### NOTA: F4.2 — Configuração de Canais por Empresa (Adiado)

**Status**: Pendente — adiado para implementar junto com F6.4 (pré-cadastro de ações por coluna).

**Escopo quando implementar**:
- Modelo `CompanyCommunicationConfig` (canais padrão por action_behavior)
- Endpoint GET/PUT `/api/v1/company/{id}/communication-config`
- UI no Menu Configurações → Comunicação → tabela action_behavior × canais habilitados
- TransitionDispatchService consulta config da empresa antes de disparar (fallback: email)
- Exemplos de config: `scheduling → email+whatsapp`, `offer → email_only`, `screening → email+whatsapp`

**Dependências**: Impacta TransitionDispatchService (F4.1), Menu Configurações (F6.4).

### 21.5 Diagrama de Prioridades

```
AGORA (próxima implementação)
└── F5.1-F5.3: Retorno automático de candidatos (webhooks + notificações)

EM BREVE
├── F6.1: TestSendModal (envio de teste dedicado)
├── F6.2: ProposalModal (campos de proposta estruturados)
├── R1: Bulk rejection com sub-status individualizado
└── R2: Layer 2 — Interpretação LLM do mini-prompt

FUTURO
├── F4.2: Configuração de canais por empresa (endpoint + UI)
├── Gap 3: SchedulingModal dedicado com calendário
├── R4: Configuração de canais padrão por empresa
└── F6.6: Testes end-to-end e documentação
```

---

## 22. Fase 5 — Retorno Automático de Candidatos (Implementado)

**Data**: 2026-02-18

### 22.1 Visão Geral

Quando o candidato completa uma ação (triagem WSI, confirmação de entrevista, envio de teste, resposta de proposta, etc.), o sistema:
1. Atualiza o sub-status do candidato no pipeline
2. Move automaticamente o candidato para nova etapa (apenas em casos definitivos)
3. Registra a atividade no ActivityFeed (timeline do candidato)
4. Envia notificação para o recrutador responsável

### 22.2 Arquitetura

```
[Evento de Retorno] → POST /transition/return-event
                          ↓
                  ReturnEventService.process_event()
                  ├── Valida event_type
                  ├── Carrega VacancyCandidate + Candidate
                  ├── Atualiza sub-status (e stage se auto-move)
                  ├── Cria ActivityFeed entry
                  └── Envia Notification ao recrutador
```

### 22.3 Tipos de Evento

| Event Type | Sub-Status | Auto-Move | Categoria | Prioridade |
|---|---|---|---|---|
| screening_complete | triagem_completa | — | screening | normal |
| screening_expired | triagem_expirada | — | screening | normal |
| interview_confirmed | confirmada | — | interview | normal |
| interview_declined | candidato_recusou | — | interview | normal |
| interview_completed | realizada | — | interview | normal |
| interview_no_show | no_show | — | interview | normal |
| test_submitted | concluido | — | evaluation | normal |
| test_expired | expirado | — | evaluation | normal |
| documents_received | documentos_recebidos | — | verification | normal |
| offer_accepted | aceita | → hired | offer | urgent |
| offer_declined | recusada | → offer_declined | offer | normal |

### 22.4 Endpoints

**POST** `/api/v1/recruitment-stages/transition/return-event`
- Processa um evento de retorno individual
- Body: `{ vacancy_candidate_id, event_type, metadata?, triggered_by? }`
- Response: `{ success, event_type, new_sub_status, new_stage, activity_id, notification_sent, auto_moved, error }`

**POST** `/api/v1/recruitment-stages/transition/return-event/bulk`
- Processa múltiplos eventos em lote (para webhooks que reportam vários candidatos)
- Body: `{ events: [{ vacancy_candidate_id, event_type, metadata?, triggered_by? }] }`
- Response: `{ total, success_count, failure_count, results: [...] }`

**GET** `/api/v1/recruitment-stages/transition/return-event/types`
- Lista todos os tipos de evento suportados com suas configurações
- Response: `{ event_types: [...], total: 11 }`

### 22.5 Regras de Auto-Move

Apenas dois eventos provocam movimentação automática de coluna:
- `offer_accepted` → move para etapa "hired" (contratado)
- `offer_declined` → move para etapa "offer_declined" (proposta recusada)

Todos os outros eventos apenas atualizam o sub-status. Movimentações de etapa para outros cenários continuam sendo decisão do recrutador.

### 22.6 Integração com ActivityFeed

Cada evento de retorno gera uma entrada no ActivityFeed com:
- `activity_type`: `return_event_{event_type}` (ex: `return_event_screening_complete`)
- `actor_type`: "candidate" (o candidato é quem completou a ação)
- `target_type`: "vacancy_candidate"
- `category`: screening | interview | evaluation | verification | offer
- Visível na timeline do candidato via `GET /activities?candidate_id=xxx`

### 22.7 Integração com Notificações

Cada evento gera uma notificação para o recrutador responsável (campo `added_by` do VacancyCandidate) via `notification_service.create_notification()`, visível no sino de notificações.

### 22.8 Simulação vs Webhooks Externos

Atualmente os endpoints funcionam como **simulação interna** — qualquer sistema pode chamar o endpoint para simular a resposta do candidato. No futuro, adaptadores de webhook podem mapear eventos externos para o mesmo ReturnEventService:

```
[SendGrid Webhook] → Adapter → ReturnEventService.process_event()
[Calendly Webhook] → Adapter → ReturnEventService.process_event()
[Portal do Candidato] → Adapter → ReturnEventService.process_event()
```

### 22.9 Arquivos

| Arquivo | Descrição |
|---|---|
| `lia-agent-system/app/domains/communication/services/return_event_service.py` | Serviço central (ReturnEventService, ReturnEventType enum, RETURN_EVENT_CONFIG) |
| `lia-agent-system/app/api/v1/recruitment_stages.py` | Endpoints /transition/return-event, /return-event/bulk, /return-event/types |
| `lia-agent-system/app/models/activity_feed.py` | Modelo ActivityFeed (pré-existente, reaproveitado) |

---

## 23. Phase 6: Pipeline Configuration, Add Column & Infer-Behavior

### 23.1 default_channel no RecruitmentStage

Adicionado campo `default_channel` ao modelo `RecruitmentStage`:
- Valores: `email`, `whatsapp`, `email_whatsapp`
- Default: `email` para maioria das etapas
- Etapas de scheduling (entrevistas, dinâmica): `email_whatsapp`
- Incluído no `to_dict()` e no `STANDARD_STAGE_CATALOG`

### 23.2 Stage Config Update Endpoint

**PUT** `/api/v1/recruitment-stages/stages/{stage_id}/config`
- Atualiza `action_behavior`, `default_channel`, `sla_hours` de uma etapa
- Validação: action_behavior deve ser valor válido, channel deve ser email/whatsapp/email_whatsapp

### 23.3 Infer-Behavior Endpoint

**POST** `/api/v1/recruitment-stages/stages/infer-behavior`
- Recebe `stage_name` (nome da etapa customizada)
- Retorna `suggested_behavior`, `confidence` (0-1), `alternatives`, `method`
- Baseado em keyword matching em português (extensível para LLM)
- Exemplo: "Teste Prático" → evaluation (0.95)

### 23.4 UI: Configuração de Pipeline (Jornada de Recrutamento)

No componente `RecruitmentJourneyConfig`:
- Seletor de `action_behavior` (Ação) por etapa com 10 opções
- Seletor de `default_channel` (Canal) por etapa: E-mail, WhatsApp, E-mail+WhatsApp
- Editável apenas para etapas custom/default (sistema = read-only)
- Badge de canal visível no modo leitura quando diferente de email

### 23.5 UI: Botão "Adicionar Coluna" no Kanban

- Botão "+" com borda tracejada após última coluna do Kanban
- Abre modal com:
  1. Input de nome customizado + botão "Sugerir tipo de ação" (chama infer-behavior)
  2. Catálogo de 8 etapas pré-definidas (filtra já existentes)
- Nova coluna inserida antes das etapas finais (contratado/reprovado)

### 23.6 Stage Catalog Endpoint

**GET** `/api/v1/recruitment-stages/catalog`
- Retorna catálogo completo de etapas padrão (17 etapas)
- Usado pelo Settings e pelo Kanban para adicionar novas colunas

### 23.7 E2E Tests

Arquivo: `lia-agent-system/tests/test_pipeline_e2e.py`
- 16 testes cobrindo: catalog, infer-behavior, return events, transitions, stage config
- 13/16 passam (3 requerem auth/DB real — esperado em ambiente de simulação)

### 23.8 Arquivos

| Arquivo | Descrição |
|---|---|
| `lia-agent-system/app/domains/communication/services/infer_behavior_service.py` | Serviço de inferência de behavior por keywords |
| `lia-agent-system/app/api/v1/recruitment_stages.py` | Endpoints: /stages/config, /catalog, /stages/infer-behavior |
| `lia-agent-system/app/models/recruitment_stages.py` | Modelo com default_channel, STANDARD_STAGE_CATALOG atualizado |
| `plataforma-lia/src/components/settings/RecruitmentJourneyConfig.tsx` | UI config com action_behavior + default_channel |
| `plataforma-lia/src/components/pages/job-kanban-page.tsx` | Botão "+" para adicionar colunas ao Kanban |
| `lia-agent-system/tests/test_pipeline_e2e.py` | Suite de testes E2E |

---

## 24. Próximos Passos

### 24.1 Edição Inline de Colunas no Kanban ✅ IMPLEMENTADO

Implementado em 20/02/2026. Componente `ColumnContextMenu.tsx` com menu contextual no header de cada coluna do Kanban. Endpoints `PATCH /stages/{stage_id}/inline-edit`, `DELETE /stages/{stage_id}/remove`, `POST /stages/reorder`.

Funcionalidades: Renomear, Desativar/Ativar, Remover (custom only), Configurar SLA, Mover esquerda/direita, Ver configuração completa.

### 24.2 Modais de Ação Específicos

- **F6.1 — TestSendModal**: Modal para envio de testes técnicos e de inglês ao mover candidato para etapas de teste
- **F6.2 — ProposalModal**: Modal para envio de proposta ao mover candidato para etapa "Proposta"

### 24.3 Refinamentos de Pipeline

- **R1 — Bulk Rejection Individualizado**: Rejeição em lote com sub-status e motivo individual por candidato (não genérico para o grupo todo)

---

## 25. Auditoria de Implementação (20/02/2026)

### 25.1 Features Implementadas vs Especificação

| Feature | Especificação | Status | Arquivos |
|---|---|---|---|
| 3-Layer Architecture | Seção 2 | ✅ Implementado | `recruitment_stages.py` (modelo), `stage-utils.ts` |
| Catálogo de Colunas (16 etapas) | Seção 3 | ✅ Implementado | `STANDARD_STAGE_CATALOG`, `COLUMN_DEFINITIONS` |
| action_behavior (8 tipos) | Seção 4 | ✅ Implementado | `infer_behavior_service.py`, `stage-utils.ts` |
| UniversalTransitionModal | Seção 7 | ✅ Implementado | `UniversalTransitionModal.tsx` |
| CandidateDecisionFlowModal | Seção 8 | ✅ Implementado (7 flow types) | `candidate-decision-flow-modal.tsx` |
| Badge System | Seção 11 | ✅ Implementado | `badge-utils.ts`, `CandidateBadges.tsx` |
| Auto Dispatchers | Seção 12 | ✅ Implementado (email+WhatsApp) | `return_event_service.py` |
| Return Events (11 tipos) | Seção 13/22 | ✅ Backend implementado | `return_event_service.py` |
| Return Events Frontend | Seção 13 | ✅ Implementado | `use-return-events.ts` (polling + toasts) |
| Pipeline Inheritance | Seção 14 | ✅ Implementado | `use-pipeline-inheritance.ts`, endpoints |
| Pipeline Config Settings | Seção 15 | ✅ Implementado | `RecruitmentJourneyConfig.tsx` |
| Add Column + Infer-behavior | Seção 16/23 | ✅ Implementado | Botão "+" no Kanban, endpoint `/infer-behavior` |
| SSE Real-time Events | Seção 13 | ✅ Implementado | `use-return-events.ts` (EventSource + fallback), `recruitment_stages.py` (/stream) |
| Bulk Rejection Individualizado | Seção 7 | ✅ Implementado | `UniversalTransitionModal.tsx` (per-candidate UI), `stage_transition_automation.py` |
| AI Sub-status Prediction | Seção 7/12 | ✅ Implementado | `stage_transition_automation.py` (LLM via Claude), `SubStatusPredictor` |
| Criação de Colunas via Chat LIA | Seção 16 | ✅ Implementado | `pipeline_tools.py` (create_pipeline_stage tool) |
| Matriz Autoritativa action→modal→canal | Seção 5 | ✅ Implementado | `action-matrix.ts` (AUTHORITATIVE_ACTION_MATRIX) |
| Inline Column Editing | Seção 24.1 | ✅ Implementado | `ColumnContextMenu.tsx`, PATCH/DELETE endpoints |

### 25.2 Gaps Conhecidos (Especificação Futura)

| Feature | Status | Prioridade |
|---|---|---|
| TestSendModal dedicado | Especificação (usando UnifiedCommunicationModal fallback) | Média |
| ProposalModal dedicado | Especificação (usando UnifiedCommunicationModal fallback) | Média |

---

## 26. Implementações Complementares (20/02/2026)

### 26.1 SSE (Server-Sent Events) para Eventos de Retorno

Substituído polling por SSE real-time com fallback automático:

- **Backend**: Endpoint `GET /api/v1/recruitment-stages/transition/return-event/stream`
  - StreamingResponse com media_type `text/event-stream`
  - Polling interno a cada 5 segundos via ActivityFeed
  - Keepalive para manter conexão
  - Auth via `get_current_active_user`

- **Frontend**: Hook `useReturnEvents` atualizado
  - Conexão EventSource como transporte primário
  - Fallback automático para polling (30s) em caso de erro SSE
  - Reconexão SSE automática após 10 segundos
  - Interface pública inalterada

### 26.2 Bulk Rejection Individualizado

UI completa para rejeição em lote com sub-status individual:

- Seção colapsável "Motivo por candidato" no UniversalTransitionModal
- Cards por candidato com avatar, nome e dropdown de sub-status individual
- Indicador de IA (ícone Brain em cyan) para candidatos com predição automática
- Reasoning da predição visível abaixo do dropdown
- Sub-status global aplica-se apenas a candidatos não editados manualmente
- Loading spinner durante predição batch

### 26.3 AI-Powered Sub-Status Prediction

Predição real via LLM integrada ao SubStatusPredictor:

- Feature flag: `ENABLE_LLM_SUBSTATUS_PREDICTION` (default: true)
- Modelo: Claude claude-sonnet-4-20250514 via `get_anthropic_client()`
- Prompt em português com contexto completo (WSI scores, notas, parecer, vaga)
- Validação: predicted_substatus deve estar na lista de opções válidas
- Fallback: determinístico (`SubStatusPredictor.predict()`) em caso de erro ou flag desativada

### 26.4 Criação de Colunas via Chat da LIA

Tool `create_pipeline_stage` registrado no ToolRegistry:

- Acionado quando recrutador pede "adiciona coluna de teste prático" via chat
- Usa `infer_behavior_auto()` para determinar action_behavior automaticamente
- Detecta duplicatas (nome já existente)
- Posição automática: insere antes das etapas finais
- Agentes autorizados: orchestrator, recruiter_assistant, job_planner

### 26.5 Matriz Autoritativa action→modal→canal

Constante centralizada `AUTHORITATIVE_ACTION_MATRIX` em `action-matrix.ts`:

- Mapeia cada um dos 10 action_behaviors para configuração completa
- Campos: label, description, modalType, defaultChannel, allowLiaAuto, iconName, specializedModal, defaultSubStatuses
- Helpers: `getActionConfig()`, `getDefaultChannel()`, `isLiaAutoAllowed()`, `getModalType()`
- Substitui lógica espalhada entre stage-utils.ts e UniversalTransitionModal

### 26.6 Arquivos Novos/Modificados

| Arquivo | Descrição |
|---|---|
| `plataforma-lia/src/components/kanban/utils/action-matrix.ts` | Matriz autoritativa action→modal→canal |
| `lia-agent-system/app/domains/recruiter_assistant/tools/pipeline_tools.py` | Tool create_pipeline_stage |
