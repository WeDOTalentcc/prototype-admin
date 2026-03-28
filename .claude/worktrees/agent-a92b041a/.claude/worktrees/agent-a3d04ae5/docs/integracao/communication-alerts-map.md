# Mapa Completo do Sistema de Comunicação e Alertas da Plataforma LIA

**Versão:** 2.0  
**Data:** 17 Dezembro 2025  
**Objetivo:** Mapear todos os pontos de comunicação, alertas e notificações para garantir uma experiência completa e eficiente para recrutadores e candidatos.

---

## 📋 Índice

1. [Resumo Executivo](#1-resumo-executivo)
2. [Estrutura de Navegação](#2-estrutura-de-navegação)
3. [Canais de Comunicação](#3-canais-de-comunicação)
4. [Matriz de Comunicações por Módulo](#4-matriz-de-comunicações-por-módulo)
5. [Catálogo Completo de Templates](#5-catálogo-completo-de-templates)
   - 5.1 Templates de Email (Candidatos)
   - 5.2 Templates de WhatsApp
   - 5.3 Templates de Notificação (Recrutador)
   - 5.4 Templates de Briefing da LIA
   - 5.5 Templates de Parecer da LIA
6. [Modelos de Relatórios e Dashboards](#6-modelos-de-relatórios-e-dashboards)
7. [Sistema de Alertas Proativos](#7-sistema-de-alertas-proativos)
8. [Análise do Painel de Controle](#8-análise-do-painel-de-controle)
9. [Templates Necessários (Gap)](#9-templates-necessários-gap)
10. [Configurações de UI Necessárias](#10-configurações-de-ui-necessárias)
11. [Plano de Implementação](#11-plano-de-implementação)
12. [Status da Implementação (v2.0)](#12-status-da-implementação-v20)

---

## 1. Resumo Executivo

### Status Atual (Atualizado em 17/12/2025)
| Componente | Backend | Frontend | Templates | Integração |
|------------|---------|----------|-----------|------------|
| Alertas Proativos | ✅ Completo | ✅ Integrado | ✅ 18 tipos | ✅ OK |
| Briefing LIA | ✅ Completo | ✅ Integrado | ✅ Completo | ✅ OK |
| Parecer LIA | ✅ Completo | ✅ Funcional | ✅ 2 formatos | ✅ OK |
| Email Candidatos | ✅ Completo | ✅ Central Comunicações | ✅ 24 templates | ⚠️ SendGrid (dev mode) |
| WhatsApp | ✅ Completo | ✅ Central Comunicações | ✅ 10 templates | ⚠️ Twilio (dev mode) |
| Notificações In-App | ✅ Completo | ✅ Funcional | N/A | ✅ OK |
| Teams | ✅ Completo | ✅ Endpoints | ✅ Adaptive Cards | ⚠️ Webhook config |
| Webhooks | ✅ Completo | ✅ CRUD | ✅ 10 eventos | ✅ OK |
| Automações | ✅ Completo | ✅ UI | ✅ 8 triggers | ✅ OK |
| Dashboards | ✅ 5 APIs | ✅ Strategic Dashboard | N/A | ✅ Dados fictícios |
| Relatórios | ✅ 3 tipos | ✅ Preview/Envio | ✅ HTML templates | ⚠️ Scheduler disabled |

### Legenda
- ✅ Implementado e funcional
- ⚠️ Parcialmente implementado
- ❌ Não implementado

---

## 2. Estrutura de Navegação

### Localização no Menu de Configurações

```
⚙️ Configurações
├── 🏢 Empresa
├── 👥 Equipe
├── 🎯 Metas & Planejamento
│   └── 🔔 Alertas ← (AJUSTAR - tela existente)
├── 📧 Central de Comunicações ← (NOVA TELA)
│   ├── Templates
│   ├── Automações
│   ├── Políticas
│   └── Histórico
├── 🤖 Automações de Comunicação ← (NOVA TELA ou aba)
├── 🔗 Integrações
└── 🔐 Segurança
```

### Confirmação de Estrutura

| Tela | Localização | Propósito | Status |
|------|-------------|-----------|--------|
| **Alertas** | Configurações > Metas & Planejamento > Alertas | Configurar thresholds e canais de alertas | ⚠️ Ajustar |
| **Central de Comunicações** | Configurações > Central de Comunicações | Gerenciar templates de email/WhatsApp | ❌ Nova |
| **Automações de Comunicação** | Configurações > Central de Comunicações > Automações | Configurar triggers e fluxos automáticos | ❌ Nova |

---

## 3. Canais de Comunicação

### 3.1 Para Recrutadores (Interno)

| Canal | Descrição | Status | Configurável |
|-------|-----------|--------|--------------|
| **In-App (Bell)** | Notificações no sino | ✅ OK | ✅ Sim |
| **Chat LIA** | Mensagens conversacionais | ✅ OK | ❌ Não |
| **Email** | Alertas e resumos | ⚠️ Estrutura | ✅ Sim |
| **Teams** | Alertas em canais | ⚠️ Estrutura | ✅ Sim |
| **WhatsApp** | Alertas urgentes | ❌ Falta | ✅ Sim |

### 3.2 Para Candidatos (Externo)

| Canal | Descrição | Status | Aprovação |
|-------|-----------|--------|-----------|
| **Email** | Todas comunicações | ✅ Templates | Por tipo |
| **WhatsApp** | Urgentes/Lembretes | ✅ Templates | Por tipo |
| **SMS** | Fallback | ❌ Falta | Automático |

---

## 4. Matriz de Comunicações por Módulo

### 4.1 🎯 JORNADA DO CANDIDATO

#### Sourcing e Primeiro Contato

| Trigger | Onde Acontece | Destinatário | Canais | Auto? | Template | Aprovação |
|---------|---------------|--------------|--------|-------|----------|-----------|
| Candidato sourced | **Busca Avançada** → Recrutador clica "Revelar" ou arrasta para vaga | Recrutador | Bell, Chat | ✅ | N/A | Não |
| Novo candidato com match alto | **Sistema** → LIA detecta match >80% ao processar CV ou sync ATS | Recrutador | Bell, Email | ✅ | `high_match_found` | Não |
| Convite para triagem | **Kanban/Card do Candidato** → Recrutador clica "Convidar para Triagem" no card ou bulk action | Candidato | Email, WhatsApp | ❌ | `initial_contact` | ✅ Obrigatória |
| Candidato visualizou vaga | **Sistema** → Tracking quando candidato abre link da vaga | Recrutador | Bell | ✅ | N/A | Não |

#### Triagem (Screening)

| Trigger | Onde Acontece | Destinatário | Canais | Auto? | Template | Aprovação |
|---------|---------------|--------------|--------|-------|----------|-----------|
| Triagem iniciada | **Sistema** → Candidato clica no link e inicia triagem (WhatsApp/Web) | Recrutador | Bell | ✅ | N/A | Não |
| Triagem abandonada (>24h) | **Sistema/Cron** → Job automático detecta triagens não finalizadas | Candidato | Email | ✅ | `screening_reminder` | Não |
| Triagem concluída | **Sistema** → Candidato finaliza última pergunta da triagem | Recrutador | Bell, Chat | ✅ | N/A | Não |
| Aprovado na triagem | **Kanban** → Recrutador avalia resultado da triagem e clica "Aprovar" no card | Candidato | Email | ⚠️ | `screening_passed` | Não |
| Reprovado na triagem | **Kanban** → Recrutador avalia resultado da triagem e clica "Reprovar" no card ou arrasta para coluna "Reprovado" | Candidato | Email | ❌ | `screening_failed` | ✅ Obrigatória |

#### Entrevistas

| Trigger | Onde Acontece | Destinatário | Canais | Auto? | Template | Aprovação |
|---------|---------------|--------------|--------|-------|----------|-----------|
| Entrevista agendada | **Card do Candidato** → Recrutador clica "Agendar Entrevista" e seleciona data/hora via modal de agendamento | Candidato | Email, WhatsApp | ✅ | `interview_scheduled` | Não |
| Lembrete 24h antes | **Sistema/Cron** → Job automático verifica entrevistas do próximo dia | Candidato | Email, WhatsApp | ✅ | `interview_reminder` | Não |
| Lembrete 1h antes | **Sistema/Cron** → Job automático verifica entrevistas da próxima hora | Candidato | WhatsApp | ✅ | `interview_reminder_urgent` | Não |
| Confirmação de presença | **Sistema** → Candidato clica "Confirmar" no email/WhatsApp | Candidato | Email | ✅ | `interview_confirmation` | Não |
| Entrevista não confirmada | **Sistema/Cron** → Job verifica 6h antes se candidato confirmou | Recrutador | Bell, Teams | ✅ | N/A | Não |
| Candidato não compareceu | **Card do Candidato** → Entrevistador/Recrutador marca "Não compareceu" após horário da entrevista | Recrutador | Bell, Email | ✅ | `no_show_alert` | Não |
| Feedback pendente (>48h) | **Sistema/Cron** → Job verifica entrevistas sem feedback após 48h | Entrevistador | Email, Bell | ✅ | `feedback_pending` | Não |

#### Oferta e Contratação

| Trigger | Onde Acontece | Destinatário | Canais | Auto? | Template | Aprovação |
|---------|---------------|--------------|--------|-------|----------|-----------|
| Proposta gerada | **Card do Candidato** → Recrutador clica "Gerar Proposta" e preenche modal com salário/benefícios | Candidato | Email | ❌ | `offer_letter` | ✅ Obrigatória |
| Proposta aceita | **Sistema** → Candidato clica "Aceitar" no link da proposta ou recrutador registra aceite verbal | Recrutador, Gestor | Bell, Email, Teams | ✅ | `offer_accepted` | Não |
| Proposta recusada | **Sistema** → Candidato clica "Recusar" no link da proposta ou recrutador registra recusa | Recrutador, Gestor | Bell, Email | ✅ | `offer_rejected` | Não |
| Prazo de resposta próximo | **Sistema/Cron** → Job verifica propostas com deadline em 48h | Candidato | WhatsApp | ✅ | `offer_deadline_reminder` | Não |
| Contratação efetivada | **Kanban** → Recrutador arrasta candidato para coluna "Contratado" ou clica "Confirmar Contratação" | RH, Gestor | Email, Teams | ✅ | `hiring_completed` | Não |

#### Rejeição e Encerramento

| Trigger | Onde Acontece | Destinatário | Canais | Auto? | Template | Aprovação |
|---------|---------------|--------------|--------|-------|----------|-----------|
| Processo fechado (vaga) | **Página da Vaga** → Recrutador/Gestor clica "Fechar Vaga" no header da vaga | Candidatos em pipeline | Email | ❌ | `process_closed` | ✅ Obrigatória |
| Feedback de rejeição | **Card do Candidato** → Recrutador clica "Reprovar e Enviar Feedback" e preenche motivo no modal | Candidato | Email | ❌ | `rejection_feedback` | ✅ Obrigatória |
| Candidato em quarentena | **Sistema** → Automático após 3ª rejeição ou flag manual do recrutador | Sistema | Log | ✅ | N/A | N/A |

---

### 4.2 📊 VAGAS E PIPELINE

| Trigger | Onde Acontece | Destinatário | Canais | Auto? | Template | Status |
|---------|---------------|--------------|--------|-------|----------|--------|
| Nova vaga criada | **Wizard de Criação de Vaga** → Recrutador finaliza wizard e clica "Publicar Vaga" | Recrutadores designados | Bell, Email | ✅ | N/A | ⚠️ Falta email |
| Vaga pausada | **Página da Vaga** → Recrutador clica "Pausar Vaga" no menu de ações | Candidatos ativos | Email | ❌ | `job_paused` | ❌ Falta |
| Vaga reativada | **Página da Vaga** → Recrutador clica "Reativar Vaga" em vaga pausada | Candidatos ativos | Email | ❌ | `job_reactivated` | ❌ Falta |
| SLA em risco (80%) | **Sistema/Cron** → Job monitora tempo médio de cada etapa vs SLA configurado | Recrutador | Bell, Teams | ✅ | N/A | ✅ OK |
| SLA violado | **Sistema/Cron** → Job detecta etapa que ultrapassou SLA definido | Recrutador, Gestor | Bell, Email, Teams | ✅ | `sla_violated` | ⚠️ Falta email |
| Pipeline vazio há X dias | **Sistema/Cron** → Job verifica vagas sem candidatos novos por X dias | Recrutador | Bell, Chat | ✅ | N/A | ✅ OK |
| Candidato parado há X dias | **Sistema/Cron** → Job verifica candidatos sem movimentação por X dias | Recrutador | Bell | ✅ | N/A | ✅ OK |

---

### 4.3 🎯 METAS E PERFORMANCE

| Trigger | Onde Acontece | Destinatário | Canais | Auto? | Template | Status |
|---------|---------------|--------------|--------|-------|----------|--------|
| Meta mensal em risco | **Sistema/Cron** → Job calcula progresso vs meta quando faltam 20% do período | Recrutador | Bell, Email | ✅ | `goal_at_risk` | ⚠️ Falta email |
| Meta atingida | **Sistema** → Automático ao registrar ação que completa a meta (ex: contratação) | Recrutador | Bell, Chat | ✅ | N/A | ✅ OK |
| Meta não atingida | **Sistema/Cron** → Job verifica metas ao final do período (mês/trimestre) | Recrutador, Gestor | Email | ❌ | `goal_missed` | ❌ Falta |
| Resumo semanal | **Sistema/Cron** → Job toda segunda-feira 8h gera relatório da semana anterior | Recrutador | Email | ❌ | `weekly_performance` | ❌ Falta |
| Ranking atualizado | **Sistema/Cron** → Job diário recalcula ranking após todas metas serem atualizadas | Todos recrutadores | Bell | ❌ | N/A | ❌ Falta |

---

### 4.4 📅 BRIEFING DA LIA

| Frequência | Onde Acontece | Destinatário | Canais | Conteúdo | Status |
|------------|---------------|--------------|--------|----------|--------|
| 2x ao dia (8h, 14h) | **Sistema/Cron** → Job às 8h e 14h gera briefing personalizado | Recrutador | Chat, Email | Urgências, agenda, tarefas | ⚠️ Só Chat |
| Diário (8h) | **Sistema/Cron** → Job às 8h com resumo completo do dia | Recrutador | Chat, Email | Resumo completo | ⚠️ Só Chat |
| Semanal (Segunda) | **Sistema/Cron** → Job toda segunda 8h com análise da semana | Recrutador | Email | Performance, próximos passos | ❌ Falta |
| Mensal (1º dia útil) | **Sistema/Cron** → Job no 1º dia útil do mês com relatório mensal | Recrutador, Gestor | Email | Relatório mensal | ❌ Falta |

---

### 4.5 ⚙️ SISTEMA E INTEGRAÇÕES

| Trigger | Onde Acontece | Destinatário | Canais | Auto? | Template | Status |
|---------|---------------|--------------|--------|-------|----------|--------|
| Sync ATS falhou | **Sistema/Cron** → Job de sync com ATS (Gupy/Pandapé) retorna erro | Admin, Recrutador | Bell, Email | ✅ | `ats_sync_failed` | ⚠️ Falta email |
| Créditos Pearch baixos | **Sistema** → Ao consumir crédito, verifica se saldo < threshold configurado | Admin | Bell, Email | ✅ | `credits_low` | ⚠️ Falta email |
| Erro de IA | **Sistema** → Chamada à API Claude/Gemini falha ou retorna erro | Admin | Bell | ✅ | N/A | ✅ OK |
| Novo usuário adicionado | **Admin > Equipe** → Admin clica "Adicionar Usuário" e confirma | Admin, Usuário | Email | ❌ | `welcome_user` | ❌ Falta |
| Senha alterada | **Perfil do Usuário** → Usuário altera senha em "Minha Conta" | Usuário | Email | ❌ | `password_changed` | ❌ Falta |

---

### 4.6 👥 GESTORES E APROVAÇÕES

| Trigger | Onde Acontece | Destinatário | Canais | Auto? | Template | Status |
|---------|---------------|--------------|--------|-------|----------|--------|
| Aprovação pendente | **Sistema** → Recrutador submete ação que requer aprovação (proposta, comunicação inicial, etc) | Gestor | Bell, Email, Teams | ✅ | `approval_pending` | ⚠️ Parcial |
| Aprovação concedida | **Admin > Aprovações** → Gestor clica "Aprovar" na lista de pendências | Recrutador | Bell | ✅ | N/A | ✅ OK |
| Aprovação negada | **Admin > Aprovações** → Gestor clica "Rejeitar" e preenche motivo | Recrutador | Bell, Chat | ✅ | N/A | ✅ OK |
| Aprovação expirada | **Sistema/Cron** → Job verifica aprovações pendentes há mais de X dias | Gestor, Recrutador | Bell, Email | ✅ | `approval_expired` | ⚠️ Falta email |
| Feedback solicitado | **Card do Candidato** → Recrutador clica "Solicitar Feedback" e seleciona gestor | Gestor | Bell, Email | ✅ | `feedback_request` | ⚠️ Falta email |

---

### 4.7 📈 WORKFORCE PLANNING

| Trigger | Onde Acontece | Destinatário | Canais | Auto? | Template | Status |
|---------|---------------|--------------|--------|-------|----------|--------|
| Variância >20% plano vs real | **Sistema/Cron** → Job mensal compara headcount planejado vs contratações realizadas | Gestor, RH | Email | ❌ | `workforce_variance` | ❌ Falta |
| Próximo mês com vagas planejadas | **Sistema/Cron** → Job 15 dias antes do mês verifica planejamento | Recrutadores | Email | ❌ | `upcoming_hires` | ❌ Falta |
| Forecast atualizado | **Workforce Planning** → Gestor atualiza previsões no módulo de planejamento | Stakeholders | Email | ❌ | `forecast_update` | ❌ Falta |

---

## 5. Catálogo Completo de Templates

### 5.1 📧 TEMPLATES DE EMAIL (CANDIDATOS)

---

#### `initial_contact` - Primeiro Contato com Candidato

| Atributo | Valor |
|----------|-------|
| **ID** | `initial_contact` |
| **Tipo** | Email |
| **Destinatário** | Candidato |
| **Trigger** | Recrutador clica "Convidar para Triagem" no card do candidato |
| **Onde Acontece** | Kanban da Vaga → Card do Candidato → Botão "Convidar" |
| **Aprovação** | ✅ Obrigatória (gestor deve aprovar antes do envio) |
| **Status** | ✅ Implementado |

**Variáveis:**
| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `candidate_name` | Nome do candidato | "Maria Silva" |
| `job_title` | Título da vaga | "Desenvolvedor Senior" |
| `company_name` | Nome da empresa (ou oculto se confidencial) | "TechCorp" |
| `is_confidential` | Vaga confidencial? | true/false |
| `job_challenge` | Descrição do desafio da vaga | "Liderar equipe de 5 devs..." |
| `recruiter_name` | Nome do recrutador | "Ana Recrutadora" |

**Preview Visual:**
```
┌─────────────────────────────────────────────────────────────┐
│ 📧 Email                                                     │
├─────────────────────────────────────────────────────────────┤
│ De: recrutamento@empresa.com                                 │
│ Para: maria.silva@email.com                                  │
│ Assunto: Oportunidade: Desenvolvedor Senior - TechCorp       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Olá Maria Silva,                                            │
│                                                             │
│ A TechCorp está em busca de um(a) Desenvolvedor Senior      │
│ para integrar nosso time.                                   │
│                                                             │
│ Seu perfil chamou nossa atenção e acreditamos que você      │
│ pode ser um excelente fit para esta posição.                │
│                                                             │
│ O DESAFIO:                                                  │
│ Liderar equipe de 5 devs...                                 │
│                                                             │
│ PRÓXIMOS PASSOS:                                            │
│ Se tiver interesse, convidamos você a participar de uma     │
│ triagem inicial com a LIA, nossa assistente de              │
│ recrutamento com inteligência artificial.                   │
│                                                             │
│ A LIA conduz entrevistas de forma:                          │
│ ✅ Profissional e isenta (sem viés)                         │
│ ✅ Humanizada e respeitosa                                  │
│ ✅ Com feedback construtivo ao final                        │
│                                                             │
│           ┌─────────────────────────────┐                   │
│           │ 👉 CLIQUE AQUI PARA INICIAR │                   │
│           └─────────────────────────────┘                   │
│                                                             │
│ Atenciosamente,                                             │
│ Ana Recrutadora                                             │
│ TechCorp                                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

#### `screening_reminder` - Lembrete de Triagem Pendente

| Atributo | Valor |
|----------|-------|
| **ID** | `screening_reminder` |
| **Tipo** | Email |
| **Destinatário** | Candidato |
| **Trigger** | Candidato não completou triagem após 24h |
| **Onde Acontece** | Sistema/Cron → Job automático às 8h verifica triagens pendentes |
| **Aprovação** | ❌ Automático |
| **Status** | ✅ Implementado |

**Variáveis:**
| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `candidate_name` | Nome do candidato | "João Santos" |
| `job_title` | Título da vaga | "Product Manager" |
| `hours_remaining` | Horas restantes | 12 |

**Preview Visual:**
```
┌─────────────────────────────────────────────────────────────┐
│ 📧 Email                                                     │
├─────────────────────────────────────────────────────────────┤
│ De: lia@empresa.com                                          │
│ Para: joao.santos@email.com                                  │
│ Assunto: Lembrete: Triagem pendente - Product Manager        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Olá João Santos,                                            │
│                                                             │
│ Notei que você ainda não completou a triagem para a         │
│ posição de Product Manager.                                  │
│                                                             │
│ Você tem mais 12 horas para finalizar a conversa.           │
│                                                             │
│           ┌─────────────────────────────┐                   │
│           │ 👉 CLIQUE AQUI PARA CONTINUAR│                   │
│           └─────────────────────────────┘                   │
│                                                             │
│ Se tiver qualquer dificuldade ou dúvida, é só responder     │
│ este email.                                                 │
│                                                             │
│ Atenciosamente,                                             │
│ LIA - Assistente de Recrutamento                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

#### `screening_passed` - Aprovação na Triagem

| Atributo | Valor |
|----------|-------|
| **ID** | `screening_passed` |
| **Tipo** | Email |
| **Destinatário** | Candidato |
| **Trigger** | Recrutador clica "Aprovar" após avaliar resultado da triagem |
| **Onde Acontece** | Kanban → Card do candidato na coluna "Triagem Concluída" → Botão "Aprovar" |
| **Aprovação** | ❌ Automático após ação do recrutador |
| **Status** | ✅ Implementado |

---

#### `screening_failed` - Rejeição na Triagem

| Atributo | Valor |
|----------|-------|
| **ID** | `screening_failed` |
| **Tipo** | Email |
| **Destinatário** | Candidato |
| **Trigger** | Recrutador clica "Reprovar" após avaliar resultado da triagem |
| **Onde Acontece** | Kanban → Card do candidato → Botão "Reprovar" |
| **Aprovação** | ✅ Obrigatória |
| **Status** | ✅ Implementado |

---

#### `interview_scheduled` - Entrevista Agendada

| Atributo | Valor |
|----------|-------|
| **ID** | `interview_scheduled` |
| **Tipo** | Email |
| **Destinatário** | Candidato |
| **Trigger** | Recrutador agenda entrevista via modal |
| **Onde Acontece** | Card do Candidato → Botão "Agendar Entrevista" → Modal |
| **Aprovação** | ❌ Automático |
| **Status** | ✅ Implementado |

---

#### `rejection_post_interview` - Rejeição Pós-Entrevista

| Atributo | Valor |
|----------|-------|
| **ID** | `rejection_post_interview` |
| **Tipo** | Email |
| **Destinatário** | Candidato |
| **Trigger** | Recrutador clica "Reprovar e Enviar Feedback" |
| **Onde Acontece** | Card do Candidato → Após entrevista → Botão "Reprovar" |
| **Aprovação** | ✅ Obrigatória |
| **Status** | ✅ Implementado |

---

#### `process_closed` - Processo Encerrado

| Atributo | Valor |
|----------|-------|
| **ID** | `process_closed` |
| **Tipo** | Email |
| **Destinatário** | Todos os candidatos ativos na vaga |
| **Trigger** | Recrutador/Gestor fecha a vaga |
| **Onde Acontece** | Página da Vaga → Menu "Fechar Vaga" |
| **Aprovação** | ✅ Obrigatória |
| **Status** | ✅ Implementado |

---

### 5.2 💬 TEMPLATES DE WHATSAPP

#### `initial_contact_wa` - Primeiro Contato via WhatsApp

| Atributo | Valor |
|----------|-------|
| **ID** | `initial_contact_wa` |
| **Tipo** | WhatsApp |
| **Destinatário** | Candidato |
| **Trigger** | Recrutador clica "Convidar via WhatsApp" |
| **Onde Acontece** | Card do Candidato → Dropdown "Convidar" → "Via WhatsApp" |
| **Aprovação** | ✅ Obrigatória |
| **HSM Status** | ⏳ Pendente aprovação Meta |

**Preview Visual (Celular):**
```
┌─────────────────────────────────────┐
│ 💬 WhatsApp                   📱     │
├─────────────────────────────────────┤
│                                     │
│   ┌───────────────────────────┐    │
│   │ Olá Roberto! 👋            │    │
│   │                           │    │
│   │ Sou a LIA, assistente de  │    │
│   │ recrutamento da StartupXYZ│    │
│   │                           │    │
│   │ Seu perfil foi            │    │
│   │ identificado para a       │    │
│   │ posição de *Backend       │    │
│   │ Developer* e gostaríamos  │    │
│   │ de convidá-lo(a) para uma │    │
│   │ conversa inicial.         │    │
│   │                           │    │
│   │ A triagem é:              │    │
│   │ ✅ Por texto ou voz       │    │
│   │ ✅ No seu tempo (24h)     │    │
│   │ ✅ Com feedback ao final  │    │
│   │                           │    │
│   │ O que acha? 😊            │    │
│   └───────────────────────────┘    │
│                          14:32 ✓✓  │
│                                     │
└─────────────────────────────────────┘
```

---

#### `screening_reminder_wa` - Lembrete de Triagem (WhatsApp)

| Atributo | Valor |
|----------|-------|
| **ID** | `screening_reminder_wa` |
| **Tipo** | WhatsApp |
| **Trigger** | Triagem pausada há mais de 12h |
| **Onde Acontece** | Sistema/Cron → Job automático |
| **Aprovação** | ❌ Automático |

---

#### `interview_reminder_wa` - Lembrete de Entrevista (WhatsApp)

| Atributo | Valor |
|----------|-------|
| **ID** | `interview_reminder_wa` |
| **Tipo** | WhatsApp |
| **Trigger** | 2h antes da entrevista agendada |
| **Onde Acontece** | Sistema/Cron → Job automático |
| **Aprovação** | ❌ Automático |

---

### 5.3 🔔 TEMPLATES DE NOTIFICAÇÃO (RECRUTADOR)

#### `screening_completed` - Triagem Concluída

| Atributo | Valor |
|----------|-------|
| **ID** | `screening_completed` |
| **Tipo** | Bell / Chat LIA |
| **Destinatário** | Recrutador |
| **Trigger** | Candidato finaliza triagem |
| **Onde Acontece** | Sistema → Candidato responde última pergunta |
| **Status** | ✅ Implementado |

**Preview Visual (Chat LIA):**
```
┌─────────────────────────────────────────────────────────────┐
│ 🤖 LIA                                           14:35      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 🎯 *Triagem Concluída*                                      │
│                                                             │
│ *Candidato:* Maria Silva                                    │
│ *Vaga:* UX Designer                                         │
│ *Score WSI:* 78%                                            │
│ *Status:* ✅ APROVADO                                       │
│                                                             │
│ *Pontos Fortes:*                                            │
│ • Excelente comunicação                                     │
│ • Experiência com Design Systems                            │
│ • Portfolio consistente                                     │
│                                                             │
│ *Áreas de Desenvolvimento:*                                 │
│ • Experiência com pesquisa de usuário                       │
│                                                             │
│ Deseja agendar entrevista?                                  │
│                                                             │
│ [ Agendar ] [ Rejeitar ] [ Ver parecer completo ]           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

#### `critical_alert` - Alerta Crítico

| Atributo | Valor |
|----------|-------|
| **ID** | `critical_alert` |
| **Tipo** | Bell / Teams / Email |
| **Destinatário** | Recrutador / Admin |
| **Trigger** | Diversos (SLA violado, sync falhou, etc.) |
| **Onde Acontece** | Sistema detecta condição crítica |
| **Status** | ⚠️ Parcial |

---

### 5.4 📋 TEMPLATES DE BRIEFING DA LIA

#### `daily_briefing` - Briefing Diário

| Atributo | Valor |
|----------|-------|
| **ID** | `daily_briefing` |
| **Tipo** | Chat LIA / Email |
| **Destinatário** | Recrutador |
| **Trigger** | Automático às 8h e 14h |
| **Onde Acontece** | Sistema/Cron → Job agendado |
| **Status** | ✅ Implementado (Chat) / ❌ Falta (Email) |

**Estrutura de Dados (Backend):**
```python
briefing = {
    "id": "briefing_{user_id}_{date}",
    "generated_at": "2025-01-15T08:00:00",
    "user_id": "uuid",
    "greeting": "Bom dia",
    "summary": {
        "urgent_count": 3,
        "tasks_today": 8,
        "interviews_today": 2,
        "alerts_active": 1
    },
    "urgent_actions": [...],    # Top 5 ações urgentes
    "pipeline": {...},          # Resumo do funil
    "schedule": [...],          # Agenda do dia
    "tasks": [...],             # Top 10 tarefas
    "alerts": [...],            # Top 5 alertas
    "insights": {...},          # Insights de IA
    "next_refresh": "2025-01-15T09:00:00"
}
```

**Preview Visual (Chat LIA - Manhã):**
```
┌─────────────────────────────────────────────────────────────┐
│ 🤖 LIA                                           08:00      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ☀️ Bom dia, Ana!                                            │
│                                                             │
│ Aqui está seu resumo do dia:                                │
│                                                             │
│ ┌─────────────────────────────────────────────────────┐    │
│ │ 📊 VISÃO GERAL                                       │    │
│ ├─────────────────────────────────────────────────────┤    │
│ │  🔴 3  Ações urgentes                                │    │
│ │  📅 2  Entrevistas hoje                              │    │
│ │  ✅ 8  Tarefas do dia                                │    │
│ │  ⚠️ 1  Alerta ativo                                  │    │
│ └─────────────────────────────────────────────────────┘    │
│                                                             │
│ 🚨 *AÇÕES URGENTES:*                                        │
│                                                             │
│ 1. ⏰ *Feedback pendente há 72h*                            │
│    Candidato: João Silva (vaga DevOps)                      │
│    [ Dar Feedback ]                                         │
│                                                             │
│ 2. 📋 *Triagem concluída - aguardando decisão*              │
│    Candidata: Maria Costa (vaga PM)                         │
│    Score WSI: 85% | Recomendação: Aprovada                  │
│    [ Ver Parecer ] [ Aprovar ] [ Rejeitar ]                 │
│                                                             │
│ 3. ⚠️ *SLA em risco*                                        │
│    Vaga "Tech Lead" - Etapa Entrevista há 8 dias            │
│    [ Ver Pipeline ]                                         │
│                                                             │
│ ───────────────────────────────────────────────────────    │
│                                                             │
│ 📅 *AGENDA DE HOJE:*                                        │
│                                                             │
│ • 10:00 - Entrevista com Carlos Mendes (UX Designer)        │
│ • 14:30 - Entrevista com Ana Paula (Backend Dev)            │
│                                                             │
│ ───────────────────────────────────────────────────────    │
│                                                             │
│ 💡 *INSIGHT DA LIA:*                                        │
│                                                             │
│ "Sua taxa de conversão Triagem → Entrevista está em 65%,    │
│ acima da média do time (52%). Continue assim! 🎉"           │
│                                                             │
│ Posso ajudar com algo específico?                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

#### `end_of_day_summary` - Resumo de Fim de Dia

| Atributo | Valor |
|----------|-------|
| **ID** | `end_of_day_summary` |
| **Tipo** | Chat LIA / Email |
| **Destinatário** | Recrutador |
| **Trigger** | Automático às 18h |
| **Onde Acontece** | Sistema/Cron → Job agendado |
| **Status** | ✅ Implementado (Chat) |

**Preview Visual (Chat LIA - Fim do Dia):**
```
┌─────────────────────────────────────────────────────────────┐
│ 🤖 LIA                                           18:00      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 🌙 Boa noite, Ana!                                          │
│                                                             │
│ Resumo do seu dia:                                          │
│                                                             │
│ ┌─────────────────────────────────────────────────────┐    │
│ │ ✅ REALIZADOS HOJE                                   │    │
│ ├─────────────────────────────────────────────────────┤    │
│ │  ✅ 2  Entrevistas concluídas                        │    │
│ │  ✅ 5  Candidatos triados                            │    │
│ │  ✅ 3  Aprovações processadas                        │    │
│ │  ✅ 8  Tarefas completadas                           │    │
│ └─────────────────────────────────────────────────────┘    │
│                                                             │
│ ⏳ *PENDENTES PARA AMANHÃ:*                                 │
│ • Dar feedback para João Silva (DevOps)                     │
│ • Revisar 3 triagens concluídas                             │
│ • Agendar entrevista com 2 candidatos (vaga UX)             │
│                                                             │
│ 📊 *PROGRESSO DAS METAS:*                                   │
│ • Contratações: 3/5 (60%) - Meta mensal                     │
│ • Triagens: 28/40 (70%) - Meta mensal                       │
│                                                             │
│ Descanse bem! Até amanhã! 😊                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### 5.5 📝 TEMPLATES DE PARECER DA LIA

#### `lia_opinion_compact` - Parecer Resumido

| Atributo | Valor |
|----------|-------|
| **ID** | `lia_opinion_compact` |
| **Tipo** | Card / Preview |
| **Destinatário** | Recrutador |
| **Trigger** | Exibido no card do candidato ou lista de triagens |
| **Onde Acontece** | Kanban → Card do Candidato (hover ou click) |
| **Status** | ✅ Implementado |

**Estrutura de Dados (Schema):**
```python
class LiaOpinionCompact(BaseModel):
    id: UUID
    opinion_type: str          # "general" | "wsi"
    source: str                # "cv_analysis" | "text_screening" | "voice_screening"
    score: Optional[float]     # 0-100
    wsi_score: Optional[float] # 0-5
    recommendation: str        # "approved" | "pending_review" | "not_approved"
    summary: Optional[str]     # Resumo de 2-3 frases
    archetype: Optional[str]   # Arquétipo Big Five
    job_vacancy_id: Optional[UUID]
    job_vacancy_title: Optional[str]
    created_at: datetime
    is_current: bool
```

**Preview Visual (Card Resumido):**
```
┌─────────────────────────────────────────────────────────────┐
│ 📝 Parecer LIA - Resumido                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─────────────────────────────────────────────────────┐    │
│ │                                                     │    │
│ │  👤 Maria Silva                                     │    │
│ │  📋 Vaga: UX Designer Senior                        │    │
│ │                                                     │    │
│ │  ┌─────────┐  ┌─────────┐  ┌──────────────┐       │    │
│ │  │ Score   │  │ WSI     │  │ Arquétipo    │       │    │
│ │  │  85%    │  │  4.2    │  │ Criativo     │       │    │
│ │  │ █████░░ │  │ ★★★★☆  │  │ Inovador     │       │    │
│ │  └─────────┘  └─────────┘  └──────────────┘       │    │
│ │                                                     │    │
│ │  🏷️ Recomendação: ✅ APROVADO                      │    │
│ │                                                     │    │
│ │  📄 Resumo:                                         │    │
│ │  "Candidata com forte experiência em Design        │    │
│ │  Systems e excelente comunicação. Demonstrou       │    │
│ │  conhecimento sólido em Figma e pesquisa de        │    │
│ │  usuário. Recomendada para próxima etapa."         │    │
│ │                                                     │    │
│ │  [ Ver Parecer Completo ]                          │    │
│ │                                                     │    │
│ └─────────────────────────────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

#### `lia_opinion_full` - Parecer Completo

| Atributo | Valor |
|----------|-------|
| **ID** | `lia_opinion_full` |
| **Tipo** | Modal / Página |
| **Destinatário** | Recrutador |
| **Trigger** | Recrutador clica "Ver Parecer Completo" |
| **Onde Acontece** | Card do Candidato → Botão "Parecer LIA" → Modal expandido |
| **Status** | ✅ Implementado |

**Estrutura de Dados (Schema):**
```python
class LiaOpinionFull(BaseModel):
    # Identificação
    id: UUID
    candidate_id: UUID
    opinion_type: str           # "general" | "wsi"
    source: str                 # Origem da análise
    job_vacancy_id: Optional[UUID]
    job_vacancy_title: Optional[str]
    wsi_screening_id: Optional[UUID]
    
    # Scores
    score: Optional[float]      # Score geral 0-100
    wsi_score: Optional[float]  # Score WSI 0-5
    recommendation: str         # Recomendação final
    
    # Análise Resumida
    summary: Optional[str]
    archetype: Optional[str]
    archetype_match_score: Optional[float]
    
    # Análise Detalhada
    score_breakdown: {
        "skills_match": float,      # Match de competências
        "experience_match": float,  # Match de experiência
        "seniority_match": float,   # Match de senioridade
        "location_match": float,    # Match de localização
        "title_match": float,       # Match de cargo
        "cultural_fit": float,      # Fit cultural
        "personality_fit": float    # Fit de personalidade
    }
    
    technical_analysis: {
        "strengths": [...],         # Lista de pontos fortes
        "gaps": [...],              # Gaps identificados
        "evidence": [...]           # Evidências da análise
    }
    
    behavioral_analysis: {
        "collaboration_score": float,
        "innovation_score": float,
        "organization_score": float,
        "resilience_score": float,
        "observations": [...]
    }
    
    cultural_fit: {
        "score": float,
        "aligned_values": [...],
        "attention_points": [...]
    }
    
    # Listas
    strengths: List[str]        # Pontos fortes gerais
    concerns: List[str]         # Preocupações
    gaps: List[str]             # Gaps
    matched_skills: List[str]   # Skills que batem
    missing_skills: List[str]   # Skills faltantes
    
    # Próximos passos
    next_steps: Optional[str]
    
    # Override do recrutador
    recruiter_notes: Optional[str]
    recruiter_override: Optional[str]
    recruiter_override_reason: Optional[str]
    recruiter_override_by: Optional[str]
    recruiter_override_at: Optional[datetime]
    
    # Metadata
    is_current: bool
    version: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
```

**Preview Visual (Modal Parecer Completo):**
```
┌─────────────────────────────────────────────────────────────────────────┐
│ 📝 Parecer LIA - Completo                                    [X]        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ ┌─────────────────────────────────────────────────────────────────┐    │
│ │ 👤 Maria Silva                                                   │    │
│ │ 📋 Vaga: UX Designer Senior                                      │    │
│ │ 📅 Gerado: 15/01/2025 às 14:30                                   │    │
│ │ 🔄 Fonte: Triagem por Texto (WSI)                                │    │
│ └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│ ═══════════════════════════════════════════════════════════════════    │
│                                                                         │
│ 📊 SCORES                                                               │
│ ┌──────────────┬──────────────┬──────────────┬──────────────┐         │
│ │ Score Geral  │ Score WSI    │ Arquétipo    │ Match Vaga   │         │
│ │    85%       │    4.2/5     │  Criativo    │    78%       │         │
│ │  ████████░░  │   ★★★★☆     │  Inovador    │  ███████░░░  │         │
│ └──────────────┴──────────────┴──────────────┴──────────────┘         │
│                                                                         │
│ 🏷️ RECOMENDAÇÃO: ✅ APROVADO para próxima etapa                        │
│                                                                         │
│ ═══════════════════════════════════════════════════════════════════    │
│                                                                         │
│ 📄 RESUMO EXECUTIVO                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐    │
│ │ Maria demonstrou forte experiência em Design Systems com        │    │
│ │ conhecimento sólido em Figma, Sketch e ferramentas de           │    │
│ │ prototipagem. Sua comunicação foi clara e estruturada durante   │    │
│ │ toda a triagem. Apresentou cases relevantes de projetos         │    │
│ │ anteriores com métricas de impacto. Recomendamos avançar para   │    │
│ │ entrevista técnica com foco em pesquisa de usuário.             │    │
│ └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│ ═══════════════════════════════════════════════════════════════════    │
│                                                                         │
│ 📊 BREAKDOWN DE SCORES                                                  │
│                                                                         │
│ Competências Técnicas  ████████░░ 82%                                   │
│ Experiência            ███████░░░ 75%                                   │
│ Senioridade            ████████░░ 85%                                   │
│ Localização            ██████████ 100%                                  │
│ Fit Cultural           ███████░░░ 72%                                   │
│ Fit Personalidade      ████████░░ 80%                                   │
│                                                                         │
│ ═══════════════════════════════════════════════════════════════════    │
│                                                                         │
│ ✅ PONTOS FORTES                                                        │
│ ┌─────────────────────────────────────────────────────────────────┐    │
│ │ • Experiência sólida com Design Systems (4+ anos)               │    │
│ │ • Domínio avançado de Figma e ferramentas de prototipagem       │    │
│ │ • Excelente comunicação e articulação de ideias                 │    │
│ │ • Cases com métricas de impacto quantificadas                   │    │
│ │ • Proatividade em propor soluções durante a triagem             │    │
│ └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│ ⚠️ ÁREAS DE DESENVOLVIMENTO                                            │
│ ┌─────────────────────────────────────────────────────────────────┐    │
│ │ • Experiência limitada com pesquisa de usuário quantitativa     │    │
│ │ • Não demonstrou familiaridade com ferramentas de analytics     │    │
│ └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│ ═══════════════════════════════════════════════════════════════════    │
│                                                                         │
│ 🧠 ANÁLISE COMPORTAMENTAL (Big Five)                                    │
│ ┌─────────────────────────────────────────────────────────────────┐    │
│ │ Colaboração   ████████░░ 78%  "Trabalha bem em equipe"          │    │
│ │ Inovação      █████████░ 88%  "Alta criatividade"               │    │
│ │ Organização   ██████░░░░ 62%  "Pode melhorar processos"         │    │
│ │ Resiliência   ███████░░░ 72%  "Lida bem com pressão"            │    │
│ └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│ ═══════════════════════════════════════════════════════════════════    │
│                                                                         │
│ 🎯 PRÓXIMOS PASSOS RECOMENDADOS                                         │
│ ┌─────────────────────────────────────────────────────────────────┐    │
│ │ 1. Agendar entrevista técnica com Tech Lead de Design           │    │
│ │ 2. Solicitar portfolio expandido com cases de pesquisa          │    │
│ │ 3. Aplicar teste prático de Design Challenge                    │    │
│ └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│ ═══════════════════════════════════════════════════════════════════    │
│                                                                         │
│ 📝 NOTAS DO RECRUTADOR                                                  │
│ ┌─────────────────────────────────────────────────────────────────┐    │
│ │ [                                                               ] │    │
│ │ [  Digite suas observações aqui...                              ] │    │
│ │ [                                                               ] │    │
│ └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│ ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│ │  ✅ Aprovar    │  │  ❌ Reprovar   │  │  ⏸️ Pendente   │            │
│ └────────────────┘  └────────────────┘  └────────────────┘            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Modelos de Relatórios e Dashboards

### 6.1 Dashboards Disponíveis

| Dashboard | Descrição | Indicadores | Status Backend | Status Frontend |
|-----------|-----------|-------------|----------------|-----------------|
| **Indicadores Estratégicos** | KPIs de negócio, performance de recrutadores e ROI | 12 | ⚠️ Parcial | ⚠️ Mock |
| **Previsões & IA** | Machine Learning, previsões de demanda e alertas inteligentes | 8 | ⚠️ Parcial | ⚠️ Mock |
| **People Analytics** | Big Five, Diversidade & Inclusão, NPS e Satisfação | 344 candidatos | ✅ OK | ⚠️ Mock |
| **Modelos de Trabalho** | Remoto, Híbrido, Presencial - análises por região | 102 | ⚠️ Parcial | ⚠️ Mock |
| **Funil & Performance** | Conversão do pipeline, efetividade por canal | 67 | ✅ OK | ⚠️ Mock |
| **War Room Operacional** | Alertas críticos, ações urgentes, pipelines em risco | 8 | ✅ OK | ⚠️ Mock |
| **Análise de Competências** | Skills gap, competências emergentes | 14 | ⚠️ Parcial | ⚠️ Mock |
| **Voice Screening** | Análise de triagem por voz (OpenMic.ai + LIA) | 0 | ✅ OK | ⚠️ Mock |
| **Atividade dos Agentes** | Monitoramento e métricas dos agentes IA | 7 | ✅ OK | ⚠️ Mock |

### 6.2 Relatórios por Email

| Relatório | Frequência | Destinatário | Conteúdo | Status |
|-----------|------------|--------------|----------|--------|
| **Briefing Diário** | 2x/dia (8h, 14h) | Recrutador | Urgências, agenda, insights | ⚠️ Só Chat |
| **Resumo Semanal** | Segunda 8h | Recrutador | Performance, conversões, metas | ❌ Falta |
| **Relatório Mensal** | 1º dia útil | Gestor, RH | KPIs consolidados, ROI | ❌ Falta |
| **Relatório Executivo da Vaga** | Sob demanda | Gestor, Recrutador | Funil, candidatos, custos, timeline | ✅ Implementado |
| **Relatório de Equipe** | Sob demanda | Gestor | Performance do time | ❌ Falta |

---

### 6.3 Relatório Executivo da Vaga (Template Completo)

| Atributo | Valor |
|----------|-------|
| **ID** | `job_executive_report` |
| **Tipo** | Modal / PDF Export |
| **Destinatário** | Recrutador, Gestor |
| **Trigger** | Recrutador clica botão "Relatório" na página da vaga |
| **Onde Acontece** | Página da Vaga → Header → Botão "Relatório" |
| **Ações Disponíveis** | Compartilhar, Imprimir, Exportar PDF |
| **Status** | ✅ Implementado (Frontend) |

**Seções do Relatório:**

| Seção | Descrição | Dados |
|-------|-----------|-------|
| **Resumo Executivo** | Visão geral da vaga | Total candidatos, contratados, tempo médio, custo por contratação |
| **Análise do Funil** | Funil de conversão | Candidatos → Triagem → Entrevista → Final → Contratados (%) |
| **Performance por Canal** | Efetividade dos canais | LinkedIn, Website, LIA Database, Referral com ROI |
| **Top 5 Candidatos** | Melhores candidatos | Nome, score LIA, status, fit |
| **Linha do Tempo** | Histórico do processo | Eventos com status (concluído/em andamento/pendente) |
| **Análise de Custos** | Orçamento | Total, gasto, restante, breakdown por categoria |
| **Recomendações LIA** | Insights de IA | Sugestões para otimizar o processo |

**Estrutura de Dados:**
```typescript
reportData = {
  generatedDate: "17 de dezembro de 2025",
  generatedTime: "14:30",
  
  // Métricas do Funil
  funnelMetrics: {
    totalCandidates: 156,
    screening: 89,
    interview: 34,
    final: 12,
    hired: 3,
    conversionRate: 1.9,         // %
    averageTimeToHire: 23,       // dias
    costPerHire: 4500            // R$
  },
  
  // Performance por Canal
  channelPerformance: [
    { channel: "LinkedIn", candidates: 67, quality: 89, hired: 2, cost: 2800 },
    { channel: "Website", candidates: 45, quality: 76, hired: 1, cost: 0 },
    { channel: "LIA Database", candidates: 28, quality: 92, hired: 0, cost: 500 },
    { channel: "Referral", candidates: 16, quality: 94, hired: 0, cost: 0 }
  ],
  
  // Top Candidatos
  topCandidates: [
    { name: "Ana Silva", score: 94, status: "Final", fit: 96 },
    { name: "Carlos Mendes", score: 91, status: "Entrevista", fit: 89 },
    // ...
  ],
  
  // Orçamento
  budget: {
    total: 50000,
    spent: 18500,
    remaining: 31500,
    breakdown: [
      { category: "Divulgação", amount: 5200 },
      { category: "Plataformas", amount: 3800 },
      { category: "Testes", amount: 2400 },
      { category: "Equipe", amount: 4600 },
      { category: "LIA/Automação", amount: 2500 }
    ]
  },
  
  // Qualidade
  qualityMetrics: {
    nps: 87,
    candidateSatisfaction: 4.6,
    hiringManagerSatisfaction: 4.8,
    timeToFillBenchmark: "Abaixo da média do mercado",
    qualityOfHireBenchmark: "Acima da média do mercado"
  }
}
```

**Preview Visual (Modal):**
```
┌─────────────────────────────────────────────────────────────────────────┐
│ 📄 Relatório Executivo da Vaga                                          │
│ ═══════════════════════════════════════════════════════════════════════ │
│                                                                         │
│ ┌─────────────────────────────────────────────────────────────────┐    │
│ │ 📋 Desenvolvedor Senior                                          │    │
│ │ 🏢 Tecnologia | 📍 São Paulo | 📅 Aberta há 23 dias              │    │
│ │                                          Gerado: 17/12/2025 14:30│    │
│ └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│ ═══════════════════════════════════════════════════════════════════    │
│                                                                         │
│ 📊 RESUMO EXECUTIVO                                                     │
│ ┌──────────────┬──────────────┬──────────────┬──────────────┐         │
│ │ 👥 Total     │ ✅ Contrat.  │ ⏱️ Tempo     │ 💰 Custo     │         │
│ │    156       │     3        │   23 dias    │  R$ 4.500    │         │
│ │ candidatos   │ contratados  │ p/ contratar │ por contrat. │         │
│ └──────────────┴──────────────┴──────────────┴──────────────┘         │
│                                                                         │
│ ⚠️ Status: Processo em fase de testes técnicos com 34 candidatos       │
│    em entrevista e 12 finalistas. Taxa de conversão: 1.9% (mercado 2.3%)│
│                                                                         │
│ ═══════════════════════════════════════════════════════════════════    │
│                                                                         │
│ 🔄 ANÁLISE DO FUNIL                                                     │
│                                                                         │
│ 1️⃣ Candidatos    156  ████████████████████ 100%                        │
│ 2️⃣ Triagem        89  ████████████░░░░░░░░  57%  ↓-43%                 │
│ 3️⃣ Entrevista     34  ████████░░░░░░░░░░░░  22%  ↓-35%                 │
│ 4️⃣ Final          12  ███░░░░░░░░░░░░░░░░░   8%  ↓-14%                 │
│ 5️⃣ Contratados     3  █░░░░░░░░░░░░░░░░░░░   2%  ↓-6%                  │
│                                                                         │
│ ═══════════════════════════════════════════════════════════════════    │
│                                                                         │
│ 🌐 PERFORMANCE POR CANAL                                                │
│ ┌────────────────┬───────────┬───────────┬───────────┬─────────────┐  │
│ │ Canal          │ Candidatos│ Qualidade │ Contrat.  │ Custo       │  │
│ ├────────────────┼───────────┼───────────┼───────────┼─────────────┤  │
│ │ 💼 LinkedIn    │    67     │   89%     │    2      │ R$ 2.800    │  │
│ │ 🌐 Website     │    45     │   76%     │    1      │    -        │  │
│ │ 🧠 LIA Database│    28     │   92%     │    0      │ R$ 500      │  │
│ │ 👥 Referral    │    16     │   94%     │    0      │    -        │  │
│ └────────────────┴───────────┴───────────┴───────────┴─────────────┘  │
│                                                                         │
│ ═══════════════════════════════════════════════════════════════════    │
│                                                                         │
│ 🏆 TOP 5 CANDIDATOS                                                     │
│ ┌────┬────────────────┬──────────┬────────────┬───────────┐           │
│ │ #  │ Nome           │ Score LIA│ Status     │ Fit       │           │
│ ├────┼────────────────┼──────────┼────────────┼───────────┤           │
│ │ 🥇 │ Ana Silva      │   94%    │ Final      │   96%     │           │
│ │ 🥈 │ Carlos Mendes  │   91%    │ Entrevista │   89%     │           │
│ │ 🥉 │ Maria Santos   │   89%    │ Entrevista │   87%     │           │
│ │ 4  │ João Paulo     │   87%    │ Triagem    │   85%     │           │
│ │ 5  │ Fernanda Lima  │   85%    │ Triagem    │   82%     │           │
│ └────┴────────────────┴──────────┴────────────┴───────────┘           │
│                                                                         │
│ ═══════════════════════════════════════════════════════════════════    │
│                                                                         │
│ 📅 LINHA DO TEMPO                                                       │
│                                                                         │
│ ✅ 01/03 ─── Vaga publicada                                             │
│ ✅ 05/03 ─── Primeira triagem LIA                                       │
│ ✅ 10/03 ─── Início das entrevistas                                     │
│ 🔄 15/03 ─── Testes técnicos (em andamento)                             │
│ ⏳ 20/03 ─── Decisão final (pendente)                                   │
│ ⏳ 25/03 ─── Contratação prevista (pendente)                            │
│                                                                         │
│ ═══════════════════════════════════════════════════════════════════    │
│                                                                         │
│ 💰 ANÁLISE DE CUSTOS                                                    │
│                                                                         │
│ Orçamento Total: R$ 50.000                                              │
│ ├── Gasto: R$ 18.500 (37%)  ████████░░░░░░░░░░░░                       │
│ └── Disponível: R$ 31.500 (63%)                                        │
│                                                                         │
│ Breakdown:                                                              │
│ • Divulgação    R$ 5.200  ████░░░░░░ 28%                               │
│ • Plataformas   R$ 3.800  ███░░░░░░░ 21%                               │
│ • Equipe        R$ 4.600  ████░░░░░░ 25%                               │
│ • Testes        R$ 2.400  ██░░░░░░░░ 13%                               │
│ • LIA/Automação R$ 2.500  ██░░░░░░░░ 14%                               │
│                                                                         │
│ ═══════════════════════════════════════════════════════════════════    │
│                                                                         │
│ 💡 RECOMENDAÇÕES DA LIA                                                 │
│ ┌─────────────────────────────────────────────────────────────────┐    │
│ │ 1. Considere aumentar investimento em Referral - melhor         │    │
│ │    qualidade (94%) e custo zero                                 │    │
│ │                                                                 │    │
│ │ 2. Taxa de conversão (1.9%) abaixo do mercado (2.3%) -          │    │
│ │    sugerimos revisar critérios de triagem                       │    │
│ │                                                                 │    │
│ │ 3. Ana Silva (score 94%) está há 5 dias em "Final" -            │    │
│ │    recomendamos decisão rápida para evitar dropout              │    │
│ └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│ ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│ │ 📤 Compartilhar│  │ 🖨️ Imprimir   │  │ 📥 Exportar PDF│            │
│ └────────────────┘  └────────────────┘  └────────────────┘            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Sistema de Alertas Proativos

### 7.1 Categorias de Alertas

| Categoria | Descrição | Alertas | Status |
|-----------|-----------|---------|--------|
| **PIPELINE** | Saúde do pipeline de candidatos | 4 | ✅ Implementado |
| **PRODUCTIVITY** | Produtividade do recrutador | 4 | ✅ Implementado |
| **COMMUNICATION** | Taxas de entrega e resposta | 3 | ✅ Implementado |
| **PREDICTIVE** | Previsões de IA | 4 | ✅ Implementado |
| **SYSTEM** | Saúde do sistema e integrações | 3 | ✅ Implementado |

### 7.2 Alertas Implementados (18 tipos)

#### PIPELINE

| Alerta | Threshold | Severidade | Cooldown |
|--------|-----------|------------|----------|
| `CONVERSION_RATE_LOW` | <5% conversão | ⚠️ Warning | 24h |
| `CANDIDATES_STAGNANT` | >10 dias parado, mín 5 candidatos | ⚠️ Warning | 48h |
| `OFFERS_PENDING_LONG` | >72h sem resposta | 🔴 Urgent | 24h |
| `PIPELINE_EMPTY` | <3 candidatos na vaga | 🔴 Urgent | 12h |

#### PRODUCTIVITY

| Alerta | Threshold | Severidade | Cooldown |
|--------|-----------|------------|----------|
| `TASKS_OVERDUE` | >5 tarefas atrasadas | 🔴 Urgent | 8h |
| `NO_ACTIVITY` | >2h sem atividade | ℹ️ Info | 4h |
| `DAILY_GOAL_RISK` | <50% da meta às 16h | ⚠️ Warning | 24h |
| `SCORECARDS_PENDING` | >24h sem avaliar, mín 3 | 🔴 Urgent | 12h |

#### COMMUNICATION

| Alerta | Threshold | Severidade | Cooldown |
|--------|-----------|------------|----------|
| `EMAIL_DELIVERY_LOW` | <80% entrega | ⚠️ Warning | 24h |
| `CANDIDATES_NO_RESPONSE` | >48h sem resposta, mín 5 | 🟠 Action Required | 24h |
| `HIGH_OPT_OUT` | >10 opt-outs em 7 dias | ⚠️ Warning | 72h |

#### PREDICTIVE

| Alerta | Threshold | Severidade | Cooldown |
|--------|-----------|------------|----------|
| `DROPOUT_RISK_HIGH` | >70% risco de desistência | 🔴 Urgent | 24h |
| `TIME_TO_FILL_RISK` | >120% do tempo esperado | ⚠️ Warning | 48h |
| `IDEAL_CANDIDATE_FOUND` | >90% match | ✅ Success | 0h |
| `REJECTION_PATTERN` | >60% rejeições por mesmo motivo | ℹ️ Info | 168h |

#### SYSTEM

| Alerta | Threshold | Severidade | Cooldown |
|--------|-----------|------------|----------|
| `ATS_SYNC_FAILED` | 3 falhas consecutivas | 🔴 Urgent | 2h |
| `AGENT_HEALTH_LOW` | <70% saúde do agente | ⚠️ Warning | 24h |
| `CREDITS_LOW` | <20% créditos restantes | ⚠️ Warning | 48h |
| `AI_DECISION_ERROR` | 1 erro em 24h | ℹ️ Info | 24h |

### 7.3 Onde os Alertas Aparecem

| Local | Tipos de Alerta | Ação Disponível |
|-------|-----------------|-----------------|
| **Bell (Sino)** | Todos | Ver detalhes, Marcar como lido |
| **Chat LIA** | Urgentes, Success | Ação direta via chat |
| **Email** | Warning, Urgent (⚠️ Pendente) | Link para ação |
| **Teams** | Urgent, Action Required (⚠️ Pendente) | Link para ação |
| **War Room Dashboard** | Todos os ativos | Ação em lote |

---

## 8. Análise do Painel de Controle

### 8.1 Visão Geral dos Dashboards

O Painel de Controle (Dashboards) é a central de monitoramento da plataforma, composto por **9 dashboards especializados**:

```
┌─────────────────────────────────────────────────────────────┐
│ 📊 Painel de Controle                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐│
│  │ 🎯 Indicadores  │  │ 🧠 Previsões    │  │ 👥 People    ││
│  │    Estratégicos │  │    & IA         │  │    Analytics ││
│  │    12 KPIs      │  │    8 modelos    │  │    344 items ││
│  └─────────────────┘  └─────────────────┘  └──────────────┘│
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐│
│  │ 🏢 Modelos de   │  │ 📈 Funil &      │  │ ⚠️ War Room  ││
│  │    Trabalho     │  │    Performance  │  │    Operacional│
│  │    102 análises │  │    67 métricas  │  │    8 alertas ││
│  └─────────────────┘  └─────────────────┘  └──────────────┘│
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐│
│  │ 🏆 Análise de   │  │ 🎤 Voice        │  │ 🤖 Atividade ││
│  │    Competências │  │    Screening    │  │    Agentes   ││
│  │    14 skills    │  │    0 triagens   │  │    7 agentes ││
│  └─────────────────┘  └─────────────────┘  └──────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Conexão com Sistema de Alertas

| Dashboard | Alertas Relacionados | Integração |
|-----------|---------------------|------------|
| **Indicadores Estratégicos** | `DAILY_GOAL_RISK`, `CONVERSION_RATE_LOW` | ⚠️ Dados mock |
| **Previsões & IA** | `DROPOUT_RISK_HIGH`, `TIME_TO_FILL_RISK`, `IDEAL_CANDIDATE_FOUND` | ⚠️ Dados mock |
| **People Analytics** | N/A | ⚠️ Dados mock |
| **Modelos de Trabalho** | N/A | ⚠️ Dados mock |
| **Funil & Performance** | `CONVERSION_RATE_LOW`, `PIPELINE_EMPTY` | ⚠️ Dados mock |
| **War Room** | **TODOS os 18 alertas** | ✅ Conectado (mock) |
| **Competências** | `REJECTION_PATTERN` | ⚠️ Dados mock |
| **Voice Screening** | N/A | ⚠️ Dados mock |
| **Atividade Agentes** | `AGENT_HEALTH_LOW`, `AI_DECISION_ERROR` | ⚠️ Dados mock |

### 8.3 Gap Analysis - Painel de Controle

#### O que funciona ✅

| Item | Descrição |
|------|-----------|
| Estrutura de navegação | 9 dashboards organizados com menu lateral |
| Big Five Dashboard | Componente completo com análises de personalidade |
| Layout responsivo | Cards e gráficos adaptáveis |
| Design tokens | Cores e estilos WeDo Talent aplicados |

#### O que falta ❌

| Item | Descrição | Prioridade |
|------|-----------|------------|
| **Conexão com APIs reais** | Todos dashboards usam dados mock | Alta |
| **Briefing integrado** | Briefing da LIA não aparece no dashboard | Alta |
| **Alertas em tempo real** | War Room não atualiza automaticamente | Alta |
| **Filtros por período** | Não há seletor de data funcional | Média |
| **Export de relatórios** | Não há botão de exportar PDF/Excel | Média |
| **Drill-down** | Clicar em métrica não mostra detalhes | Média |
| **Comparativos** | Não há comparação período anterior | Baixa |

### 8.4 Roadmap para Painel 100% Funcional

#### Fase 1: Conexão Backend (2 semanas)

| Tarefa | Endpoints Necessários | Esforço |
|--------|----------------------|---------|
| Indicadores Estratégicos | `GET /api/v1/analytics/kpis` | 3d |
| Funil & Performance | `GET /api/v1/analytics/funnel` | 2d |
| War Room | `GET /api/v1/alerts/active` (existe) | 1d |
| People Analytics | `GET /api/v1/analytics/candidates` | 2d |
| Atividade Agentes | `GET /api/v1/agents/monitoring` (existe) | 1d |

#### Fase 2: Funcionalidades (1 semana)

| Tarefa | Descrição | Esforço |
|--------|-----------|---------|
| Briefing no Dashboard | Widget de briefing na home | 2d |
| Filtro de período | DatePicker funcional | 1d |
| Atualização automática | WebSocket ou polling | 2d |

#### Fase 3: Relatórios (1 semana)

| Tarefa | Descrição | Esforço |
|--------|-----------|---------|
| Export PDF | Gerar PDF de qualquer dashboard | 2d |
| Export Excel | Gerar Excel com dados | 1d |
| Agendamento | Enviar relatório por email | 2d |

---

## 9. Templates Necessários (Gap) ❌

| Template | Prioridade | Tipo | Destinatário | Trigger |
|----------|------------|------|--------------|---------|
| `goal_at_risk` | Alta | Email | Recrutador | Meta com progresso <50% quando faltam 20% do período |
| `goal_missed` | Alta | Email | Recrutador, Gestor | Meta não atingida ao final do período |
| `weekly_performance` | Alta | Email | Recrutador | Toda segunda-feira às 8h |
| `monthly_report` | Média | Email | Gestor | 1º dia útil do mês |
| `sla_violated` | Alta | Email | Recrutador, Gestor | Etapa do pipeline ultrapassa SLA |
| `welcome_user` | Média | Email | Novo usuário | Admin adiciona novo usuário |
| `approval_pending` | Alta | Email | Gestor | Recrutador submete ação que requer aprovação |
| `approval_expired` | Média | Email | Gestor, Recrutador | Aprovação pendente há mais de X dias |
| `ats_sync_failed` | Média | Email | Admin | Sync com ATS retorna erro |
| `credits_low` | Média | Email | Admin | Créditos Pearch abaixo do threshold |
| `workforce_variance` | Baixa | Email | Gestor, RH | Variância >20% entre planejado e realizado |
| `no_show_alert` | Média | Email | Recrutador | Candidato não compareceu à entrevista |
| `offer_accepted` | Alta | Email | Recrutador, Gestor | Candidato aceita proposta |
| `offer_rejected` | Alta | Email | Recrutador, Gestor | Candidato recusa proposta |
| `job_paused` | Média | Email | Candidatos ativos | Recrutador pausa vaga |
| `job_reactivated` | Média | Email | Candidatos ativos | Recrutador reativa vaga |

---

## 10. Configurações de UI Necessárias

### 10.1 Tela de Alertas (Existente - Ajustar)

**Localização:** Configurações > Metas & Planejamento > Alertas

```
┌─────────────────────────────────────────────────────────────┐
│ Configuração de Alertas                    [Salvar]         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ALERTAS DE PIPELINE                                        │
│  ├─ SLA Próximo do Vencimento    [Email ▼] [Teams ▼] [●]   │
│  │   └─ Threshold: [80] % do SLA                            │
│  ├─ Candidato Sem Interação      [Teams ▼] [●]              │
│  │   └─ Dias sem contato: [5] dias                          │
│  └─ Pipeline Vazio               [Email ▼] [Bell ▼] [●]    │
│      └─ Mínimo candidatos: [3]                              │
│                                                             │
│  ALERTAS DE METAS                                           │
│  ├─ Meta Mensal em Risco         [Email ▼] [●]              │
│  │   └─ % restante do mês: [20] %                           │
│  └─ Meta Atingida                [Bell ▼] [●]               │
│                                                             │
│  ALERTAS DE ENTREVISTA                                      │
│  ├─ Entrevista Não Confirmada    [Bell ▼] [Teams ▼] [●]    │
│  │   └─ Horas antes: [24] h                                 │
│  ├─ Feedback Pendente            [Email ▼] [●]              │
│  │   └─ Horas após entrevista: [48] h                       │
│  └─ No-Show                      [Bell ▼] [Email ▼] [●]    │
│                                                             │
│  ALERTAS DE SISTEMA                                         │
│  ├─ Sync ATS Falhou              [Email ▼] [●]              │
│  └─ Créditos Baixos              [Email ▼] [●]              │
│      └─ Limite: [100] créditos                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 10.2 Central de Comunicações (Nova Tela)

**Localização:** Configurações > Central de Comunicações

```
┌─────────────────────────────────────────────────────────────┐
│ Central de Comunicações                                      │
├─────────────────────────────────────────────────────────────┤
│ [Templates] [Automações] [Políticas] [Histórico]            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  TEMPLATES DE EMAIL                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 📧 Primeiro Contato           [Editar] [Prévia]     │   │
│  │ 📧 Lembrete de Triagem        [Editar] [Prévia]     │   │
│  │ 📧 Aprovação na Triagem       [Editar] [Prévia]     │   │
│  │ 📧 Feedback de Rejeição       [Editar] [Prévia]     │   │
│  │ 📧 Entrevista Agendada        [Editar] [Prévia]     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  TEMPLATES DE WHATSAPP                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 💬 Convite para Triagem       [Editar] [HSM: ✅]    │   │
│  │ 💬 Lembrete de Entrevista     [Editar] [HSM: ⏳]    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 10.3 Automações de Comunicação (Nova Aba)

**Localização:** Configurações > Central de Comunicações > Automações

```
┌─────────────────────────────────────────────────────────────┐
│ Automações de Comunicação                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  JORNADA DO CANDIDATO                                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Quando: Candidato sourced com match > 80%            │   │
│  │ Ação: Enviar email "Primeiro Contato"                │   │
│  │ Canal: [Email ▼]  Aprovação: [Obrigatória ▼]  [●]   │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Quando: Triagem não concluída há 24h                 │   │
│  │ Ação: Enviar lembrete                                │   │
│  │ Canal: [Email ▼]  Aprovação: [Automático ▼]  [●]    │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Quando: 24h antes da entrevista                      │   │
│  │ Ação: Enviar lembrete                                │   │
│  │ Canal: [WhatsApp ▼]  Aprovação: [Automático ▼]  [●] │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [+ Adicionar Automação]                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 11. Plano de Implementação

### Fase 1: Fundação (1-2 semanas)

| Tarefa | Prioridade | Esforço | Status |
|--------|------------|---------|--------|
| Integrar frontend de Alertas com API backend | Alta | 2d | ✅ Completo |
| Integrar frontend de Briefing com API backend | Alta | 1d | ✅ Completo |
| Criar endpoint para salvar preferências de alertas | Alta | 1d | ✅ Completo |
| Configurar SendGrid para envio real de emails | Alta | 1d | ✅ Dev mode |
| Configurar Twilio para WhatsApp | Média | 2d | ✅ Dev mode |

### Fase 2: Templates (1 semana)

| Tarefa | Prioridade | Esforço | Status |
|--------|------------|---------|--------|
| Criar templates de email faltantes (16) | Alta | 3d | ✅ Completo |
| Criar templates WhatsApp e submeter HSM | Média | 2d | ✅ Completo |
| UI Central de Comunicações | Média | 2d | ✅ Completo |

### Fase 3: Automações (2 semanas)

| Tarefa | Prioridade | Esforço | Status |
|--------|------------|---------|--------|
| Sistema de triggers e automações | Alta | 5d | ✅ Completo |
| UI para configurar automações | Alta | 3d | ✅ Completo |
| Fluxo de aprovações para mensagens | Alta | 2d | ✅ Completo |
| Histórico de comunicações por candidato | Média | 2d | ✅ Completo |

### Fase 4: Dashboards (2 semanas)

| Tarefa | Prioridade | Esforço | Status |
|--------|------------|---------|--------|
| Conectar Indicadores Estratégicos ao backend | Alta | 3d | ✅ Completo |
| Conectar Funil & Performance ao backend | Alta | 2d | ✅ Completo |
| Conectar War Room aos alertas reais | Alta | 1d | ✅ Completo |
| Implementar filtros de período | Média | 1d | ✅ Completo |
| Implementar export PDF/Excel | Média | 2d | ✅ Completo |

### Fase 5: Relatórios e Briefings (1 semana)

| Tarefa | Prioridade | Esforço | Status |
|--------|------------|---------|--------|
| Geração automática de briefing diário por email | Alta | 2d | ✅ Completo |
| Relatório semanal de performance | Média | 2d | ✅ Completo |
| Relatório mensal para gestores | Baixa | 1d | ✅ Completo |

### Fase 6: Integrações (1 semana)

| Tarefa | Prioridade | Esforço | Status |
|--------|------------|---------|--------|
| Integração Microsoft Teams | Média | 3d | ✅ Completo |
| Integração Slack (opcional) | Baixa | 2d | ⏳ Pendente |
| Webhooks para sistemas externos | Baixa | 2d | ✅ Completo |

---

## 12. Status da Implementação (v2.0)

**Data:** 17 de Dezembro de 2025

### Arquivos Criados/Modificados

#### Backend (lia-agent-system)
| Arquivo | Descrição |
|---------|-----------|
| `app/models/alert.py` | AlertPreference com company_id e 18 tipos |
| `app/models/automation.py` | CommunicationAutomation com triggers e actions |
| `app/models/webhook.py` | Webhook e WebhookLog com 10 eventos |
| `app/api/v1/alerts.py` | Endpoints de preferências com multi-tenant |
| `app/api/v1/automations.py` | 9 endpoints REST para automações |
| `app/api/v1/dashboard_data.py` | 5 APIs com dados fictícios |
| `app/api/v1/webhooks.py` | CRUD de webhooks com logs |
| `app/api/v1/reports.py` | Endpoints de relatórios e preview |
| `app/services/email_service.py` | SendGridEmailService em dev mode |
| `app/services/whatsapp_service.py` | WhatsAppService com Twilio |
| `app/services/automation_service.py` | Execute actions com validação |
| `app/services/teams_service.py` | Adaptive Cards e alertas |
| `app/services/webhook_service.py` | Trigger com HMAC signature |
| `app/services/report_service.py` | Geração de briefings e relatórios |
| `app/templates/communication_templates.py` | 24 templates de email + 10 WhatsApp |
| `app/templates/report_templates.py` | HTML templates para relatórios |
| `app/jobs/scheduled_reports.py` | Jobs com feature flag de segurança |

#### Frontend (plataforma-lia)
| Arquivo | Descrição |
|---------|-----------|
| `src/components/alerts/kpi-alert-system.tsx` | Integrado com backend |
| `src/components/alerts/alert-settings-modal.tsx` | Salva preferências via API |
| `src/components/pages/communication-center-page.tsx` | 4 abas funcionais |
| `src/components/dashboard/strategic-dashboard.tsx` | KPIs, funil, ranking |
| `src/components/ui/date-range-picker.tsx` | Filtros de período |

### Segurança Multi-Tenant

Todos os endpoints protegidos com:
- Header `X-Company-ID` obrigatório
- Validação de company_id em queries
- Índices para performance

### Variáveis de Ambiente Necessárias

| Variável | Descrição | Obrigatório |
|----------|-----------|-------------|
| `SENDGRID_API_KEY` | Chave API SendGrid | Não (dev mode) |
| `SENDGRID_FROM_EMAIL` | Email remetente | Não (dev mode) |
| `TWILIO_ACCOUNT_SID` | Conta Twilio | Não (dev mode) |
| `TWILIO_AUTH_TOKEN` | Token Twilio | Não (dev mode) |
| `TWILIO_WHATSAPP_FROM` | Número WhatsApp | Não (dev mode) |
| `TEAMS_WEBHOOK_URL` | URL Incoming Webhook | Não (dev mode) |
| `ENABLE_SCHEDULED_REPORTS` | Ativar jobs de relatório | Não (default: false) |

### Próximos Passos

1. **Configurar SendGrid** com API key real para produção
2. **Configurar Twilio** para envio de WhatsApp
3. **Configurar Teams Webhook** para notificações
4. **Ativar scheduler** com `ENABLE_SCHEDULED_REPORTS=true` em produção
5. **Implementar Slack** (opcional)
6. **Conectar dashboards a dados reais** quando backend de métricas estiver pronto

---

*Documento atualizado em 17 Dezembro 2025 - Plataforma LIA v2.0*
