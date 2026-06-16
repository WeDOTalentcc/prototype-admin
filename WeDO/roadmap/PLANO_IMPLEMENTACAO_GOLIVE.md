# Plano de Implementação Go-Live - Plataforma WeDoTalent

**Data de Criação:** 19 de Janeiro de 2026  
**Versão:** 1.0  
**Baseado em:** DIAGNOSTICO_GESTAO_VAGAS_GOLIVE.md v5.0  
**Responsável:** WeDo Talent Engineering Team

---

## 1. Sumário Executivo

Este plano detalha as ações necessárias para levar a Plataforma WeDoTalent ao estado de produção (Go-Live). O plano está organizado em **4 fases**, com critérios claros de conclusão e dependências mapeadas.

### Score Atual vs. Meta

| Área | Score Atual | Meta Go-Live | Gap |
|------|-------------|--------------|-----|
| Carregamento Backend | 90% | 95% | 5% |
| Sistema de Filtros | 100% | 100% | ✅ |
| Preview de Vaga | 80% | 90% | 10% |
| **Edição de Vaga** | **10%** | **90%** | **80% CRÍTICO** |
| **Agentes IA/Chat LIA** | **15%** | **70%** | **55% CRÍTICO** |
| Tab Roteiro Triagem | 90% | 95% | 5% |
| Tab Métricas LIA | 35% | 80% | 45% |
| **Notificações Automáticas** | **25%** | **80%** | **55% CRÍTICO** |
| Integrações Voz | 55% | 80% | 25% |
| **Botões/Ações Funcionais** | **30%** | **85%** | **55% CRÍTICO** |
| Templates Email | 85% | 90% | 5% |
| Job Creation Wizard | 95% | 95% | ✅ |
| Notas de Entrevista | 75% | 90% | 15% |

**Tempo Total Estimado: 120-160 horas (3-4 semanas)**

---

## 2. Fases de Implementação

### Visão Geral das Fases

```
┌─────────────────────────────────────────────────────────────────────────┐
│  FASE 1: FUNDAÇÃO CRÍTICA (Semana 1)                                    │
│  ├── Edição de Vagas (CRÍTICO)                                          │
│  ├── Botões/Ações Funcionais                                            │
│  └── Remoção de Código Morto                                            │
├─────────────────────────────────────────────────────────────────────────┤
│  FASE 2: FUNCIONALIDADES CORE (Semana 2)                                │
│  ├── Quick Actions LIA                                                  │
│  ├── Notificações Automáticas                                           │
│  ├── Notas de Entrevista (Backend)                                      │
│  └── Métricas LIA Reais                                                 │
├─────────────────────────────────────────────────────────────────────────┤
│  FASE 3: INTEGRAÇÕES (Semana 3)                                         │
│  ├── OpenMic.ai (Triagens por Voz)                                      │
│  ├── Deepgram (Transcrição)                                             │
│  └── WhatsApp (Envio Real)                                              │
├─────────────────────────────────────────────────────────────────────────┤
│  FASE 4: POLIMENTO (Semana 4)                                           │
│  ├── Activity Feed nas Vagas                                            │
│  ├── Compartilhamento de Vagas                                          │
│  ├── Refatoração e Testes                                               │
│  └── QA Final                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. FASE 1: Fundação Crítica

**Duração:** 1 semana (40 horas)  
**Prioridade:** CRÍTICA - Bloqueante para Go-Live  
**Objetivo:** Permitir edição de vagas e ter ações funcionais na UI

### 3.1 Edição de Vagas

**Score Atual:** 10% → **Meta:** 90%  
**Esforço:** 16 horas  
**Arquivos Principais:** `jobs-page.tsx`, `job_vacancies.py`

| # | Tarefa | Horas | Prioridade | Entregável |
|---|--------|-------|------------|------------|
| 1.1.1 | Criar componente `EditJobModal.tsx` | 4h | P0 | Modal com formulário completo |
| 1.1.2 | Implementar campos editáveis (título, descrição, requisitos, salário, etc.) | 4h | P0 | 15+ campos editáveis |
| 1.1.3 | Conectar ao endpoint PUT `/api/v1/job-vacancies/{id}` | 2h | P0 | CRUD completo |
| 1.1.4 | Adicionar validação de campos obrigatórios | 2h | P0 | Feedback visual de erros |
| 1.1.5 | Implementar histórico de alterações (audit log) | 2h | P1 | Registro de quem alterou o quê |
| 1.1.6 | Adicionar botão "Editar" na tabela e preview | 2h | P0 | Acesso rápido à edição |

**Critérios de Aceite:**
- [ ] Usuário pode editar todos os campos de uma vaga existente
- [ ] Alterações são salvas no backend com sucesso
- [ ] Validação impede salvar com campos obrigatórios vazios
- [ ] Toast de confirmação após salvar
- [ ] Histórico de alterações registrado

### 3.2 Botões e Ações Funcionais

**Score Atual:** 30% → **Meta:** 85%  
**Esforço:** 12 horas  
**Arquivos Principais:** `jobs-page.tsx`

| # | Tarefa | Horas | Prioridade | Entregável |
|---|--------|-------|------------|------------|
| 1.2.1 | Padronizar dropdown de ações na tabela (Editar, Duplicar, Arquivar, Excluir) | 3h | P0 | Menu consistente |
| 1.2.2 | Implementar "Duplicar Vaga" com endpoint POST clone | 3h | P0 | Clonagem funcional |
| 1.2.3 | Implementar "Arquivar Vaga" com mudança de status | 2h | P0 | Status "Arquivada" |
| 1.2.4 | Implementar confirmação para "Excluir Vaga" | 2h | P1 | Dialog de confirmação |
| 1.2.5 | Conectar botão "Compartilhar" no preview | 2h | P1 | Gera link público |

**Critérios de Aceite:**
- [ ] Dropdown de ações aparece em todas as linhas da tabela
- [ ] Duplicar cria nova vaga com sufixo "(Cópia)"
- [ ] Arquivar muda status e remove da listagem ativa
- [ ] Excluir pede confirmação e remove permanentemente
- [ ] Compartilhar gera link copiável

### 3.3 Limpeza de Código

**Esforço:** 8 horas

| # | Tarefa | Horas | Prioridade | Entregável |
|---|--------|-------|------------|------------|
| 1.3.1 | Remover ~900 linhas de vagas mock hardcoded | 2h | P1 | Código limpo |
| 1.3.2 | Mover componentes inline para arquivos separados | 4h | P2 | Melhor organização |
| 1.3.3 | Resolver erros LSP pendentes (3 em jobs-page) | 2h | P1 | 0 erros LSP |

**Critérios de Aceite:**
- [ ] `jobs-page.tsx` reduzido de 6.500 para ~4.000 linhas
- [ ] 0 erros LSP no arquivo
- [ ] Código morto removido

### Checkpoint Fase 1

**Após completar Fase 1:**
- Edição de vagas 100% funcional
- Todas as ações da tabela funcionando
- Código mais limpo e organizado

---

## 4. FASE 2: Funcionalidades Core

**Duração:** 1 semana (40 horas)  
**Prioridade:** CRÍTICA  
**Objetivo:** Chat LIA funcional, notificações automáticas, métricas reais

### 4.1 Quick Actions LIA

**Score Atual:** 15% → **Meta:** 70%  
**Esforço:** 16 horas  
**Arquivos Principais:** `jobs-page.tsx`, `lia-api.ts`, backend agents

| # | Tarefa | Horas | Prioridade | Comportamento Esperado |
|---|--------|-------|------------|------------------------|
| 2.1.1 | "Comparar Candidatos" - Análise comparativa real | 3h | P0 | Claude analisa 2+ candidatos |
| 2.1.2 | "Analisar Performance" - GET métricas + insights IA | 3h | P0 | Dados reais + análise |
| 2.1.3 | "Gerar Script" - Claude gera roteiro de entrevista | 2h | P0 | Script baseado na vaga |
| 2.1.4 | "Ver Insights" - Análise preditiva real | 3h | P1 | Previsões baseadas em dados |
| 2.1.5 | "Publicar" - POST para canais (mockado inicialmente) | 2h | P1 | Preparado para LinkedIn/Indeed |
| 2.1.6 | "Integração ATS" - Sync status (mockado) | 3h | P2 | Preparado para Gupy/Pandapé |

**Critérios de Aceite:**
- [ ] Cada ação executa chamada real ao backend
- [ ] Resultado aparece no chat LIA
- [ ] Loading state durante processamento
- [ ] Erro tratado com mensagem amigável

### 4.2 Notificações Automáticas

**Score Atual:** 25% → **Meta:** 80%  
**Esforço:** 12 horas  
**Arquivos Principais:** `notification-context.tsx`, `notifications.py`

| # | Tarefa | Horas | Prioridade | Trigger |
|---|--------|-------|------------|---------|
| 2.2.1 | Trigger: Novo candidato aplicou | 2h | P0 | Após application |
| 2.2.2 | Trigger: Triagem completada | 2h | P0 | Após screening WSI |
| 2.2.3 | Trigger: Candidato aprovado/reprovado | 2h | P0 | Após decisão |
| 2.2.4 | Trigger: Prazo de vaga próximo (3 dias) | 2h | P1 | Cron job diário |
| 2.2.5 | Trigger: Vaga sem atividade (7 dias) | 2h | P1 | Cron job diário |
| 2.2.6 | Endpoint POST /notifications/automatic-trigger | 2h | P0 | Backend central |

**Critérios de Aceite:**
- [ ] Notificações aparecem automaticamente no sino
- [ ] Email enviado para eventos críticos
- [ ] Configurável por usuário (quais notificações quer receber)

### 4.3 Notas de Entrevista - Backend

**Score Atual:** 75% → **Meta:** 90%  
**Esforço:** 6 horas  
**Arquivos:** `interview-notes/*.tsx`, backend

| # | Tarefa | Horas | Prioridade | Entregável |
|---|--------|-------|------------|------------|
| 2.3.1 | Endpoint POST /interviews/{id}/notes | 2h | P0 | Salvar notas no banco |
| 2.3.2 | Endpoint GET /candidates/{id}/interview-notes | 2h | P0 | Histórico por candidato |
| 2.3.3 | Conectar saveInterviewNote() ao backend real | 2h | P0 | CRUD completo |

**Critérios de Aceite:**
- [ ] Notas persistem no banco de dados
- [ ] Histórico de notas acessível no perfil do candidato
- [ ] LIA parecer salvo junto com a nota

### 4.4 Métricas LIA Reais

**Score Atual:** 35% → **Meta:** 80%  
**Esforço:** 6 horas  
**Arquivos:** `jobs-page.tsx` (Tab Métricas), backend

| # | Tarefa | Horas | Prioridade | Métrica |
|---|--------|-------|------------|---------|
| 2.4.1 | Endpoint GET /job-vacancies/{id}/metrics | 3h | P0 | Retorna métricas reais |
| 2.4.2 | Calcular tempo médio de triagem real | 1h | P0 | Baseado em timestamps |
| 2.4.3 | Calcular taxa de conclusão real | 1h | P0 | Triagens concluídas / iniciadas |
| 2.4.4 | Substituir valores hardcoded no frontend | 1h | P0 | Hook useJobMetrics |

**Critérios de Aceite:**
- [ ] Todas as métricas vêm do backend
- [ ] Valores atualizados em tempo real
- [ ] 0 valores hardcoded

### Checkpoint Fase 2

**Após completar Fase 2:**
- Chat LIA executa ações reais
- Notificações disparam automaticamente
- Notas de entrevista persistem
- Métricas calculadas com dados reais

---

## 5. FASE 3: Integrações

**Duração:** 1 semana (32 horas)  
**Prioridade:** IMPORTANTE  
**Objetivo:** Integrações de voz e comunicação funcionais

### 5.1 OpenMic.ai (Triagens por Voz)

**Score Atual:** 40% → **Meta:** 80%  
**Esforço:** 14 horas  
**Dependência:** OPENMIC_API_KEY, OPENMIC_WEBHOOK_SECRET

| # | Tarefa | Horas | Prioridade | Entregável |
|---|--------|-------|------------|------------|
| 3.1.1 | Solicitar e configurar API Keys | 1h | P0 | Keys no secrets |
| 3.1.2 | Testar conexão com ambiente sandbox | 2h | P0 | Chamada de teste OK |
| 3.1.3 | Criar botão "Iniciar Triagem por Voz" no preview | 3h | P0 | UI funcional |
| 3.1.4 | Implementar fluxo: selecionar candidatos → iniciar chamadas | 4h | P0 | Batch de chamadas |
| 3.1.5 | Processar webhooks de resultado | 2h | P0 | Transcrição + análise |
| 3.1.6 | Exibir resultado no ScreeningMediaModal | 2h | P0 | Visualização completa |

**Critérios de Aceite:**
- [ ] Chamada telefônica iniciada com sucesso
- [ ] Transcrição recebida via webhook
- [ ] Análise WSI gerada automaticamente
- [ ] Resultado visível no modal de mídia

### 5.2 Deepgram (Transcrição)

**Score Atual:** 50% → **Meta:** 85%  
**Esforço:** 8 horas  
**Dependência:** DEEPGRAM_API_KEY (✅ já configurada)

| # | Tarefa | Horas | Prioridade | Entregável |
|---|--------|-------|------------|------------|
| 3.2.1 | Criar componente de upload de áudio | 3h | P0 | Drag & drop funcional |
| 3.2.2 | Integrar com transcribe_audio_bytes() | 2h | P0 | Transcrição automática |
| 3.2.3 | Exibir transcrição no ScreeningMediaModal | 2h | P0 | Visualização com timestamps |
| 3.2.4 | Integrar transcrição com análise WSI | 1h | P1 | Score automático |

**Critérios de Aceite:**
- [ ] Upload de áudio funciona (MP3, WAV, M4A)
- [ ] Transcrição em português BR correta
- [ ] Timestamps por frase
- [ ] Análise WSI gerada

### 5.3 WhatsApp (Envio Real)

**Score Atual:** 40% → **Meta:** 70%  
**Esforço:** 10 horas  
**Dependência:** TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN

| # | Tarefa | Horas | Prioridade | Entregável |
|---|--------|-------|------------|------------|
| 3.3.1 | Configurar conta Twilio/WhatsApp Business | 2h | P0 | Conta ativa |
| 3.3.2 | Implementar envio via Twilio API | 4h | P0 | Mensagens enviadas |
| 3.3.3 | Criar templates aprovados no WhatsApp Business | 2h | P0 | 3+ templates |
| 3.3.4 | Integrar com fluxo de convite para triagem | 2h | P0 | Botão funcional |

**Critérios de Aceite:**
- [ ] Mensagem WhatsApp enviada com sucesso
- [ ] Templates aprovados pela Meta
- [ ] Log de envios no sistema

### Checkpoint Fase 3

**Após completar Fase 3:**
- Triagens por voz (telefone) funcionais
- Upload e transcrição de áudio
- WhatsApp enviando mensagens reais

---

## 6. FASE 4: Polimento

**Duração:** 1 semana (24-40 horas)  
**Prioridade:** IMPORTANTE  
**Objetivo:** Acabamento, testes, documentação

### 6.1 Activity Feed nas Vagas

**Esforço:** 6 horas

| # | Tarefa | Horas | Prioridade | Entregável |
|---|--------|-------|------------|------------|
| 4.1.1 | Endpoint GET /job-vacancies/{id}/activities | 2h | P0 | Atividades por vaga |
| 4.1.2 | Integrar ActivityFeed no preview de vaga | 2h | P0 | Tab "Atividades" |
| 4.1.3 | Registrar eventos automaticamente | 2h | P1 | Audit trail completo |

### 6.2 Compartilhamento de Vagas

**Esforço:** 6 horas

| # | Tarefa | Horas | Prioridade | Entregável |
|---|--------|-------|------------|------------|
| 4.2.1 | Endpoint POST /job-vacancies/{id}/share | 2h | P0 | Gera link único |
| 4.2.2 | Página pública de vaga (sem login) | 3h | P0 | /vagas/{slug} |
| 4.2.3 | Botão "Copiar Link" funcional | 1h | P0 | Clipboard API |

### 6.3 Testes e QA

**Esforço:** 12 horas

| # | Tarefa | Horas | Prioridade | Entregável |
|---|--------|-------|------------|------------|
| 4.3.1 | Testes E2E: Criar vaga (wizard completo) | 2h | P0 | Cypress/Playwright |
| 4.3.2 | Testes E2E: Editar vaga | 2h | P0 | - |
| 4.3.3 | Testes E2E: Fluxo de triagem | 2h | P0 | - |
| 4.3.4 | Testes E2E: Notas de entrevista | 2h | P1 | - |
| 4.3.5 | Revisão de segurança (OWASP basics) | 2h | P0 | Checklist OK |
| 4.3.6 | Performance audit (Lighthouse) | 2h | P1 | Score > 80 |

### 6.4 Documentação e Deploy

**Esforço:** 8 horas

| # | Tarefa | Horas | Prioridade | Entregável |
|---|--------|-------|------------|------------|
| 4.4.1 | Atualizar replit.md com todas as mudanças | 2h | P0 | Docs atualizados |
| 4.4.2 | Criar guia de uso para equipe de vendas | 3h | P1 | PDF/Notion |
| 4.4.3 | Configurar deploy de produção | 2h | P0 | CI/CD funcional |
| 4.4.4 | Monitoramento de erros (Sentry/similar) | 1h | P1 | Alertas configurados |

### Checkpoint Fase 4 (GO-LIVE)

**Critérios de Go-Live:**
- [ ] Todos os testes E2E passando
- [ ] 0 erros críticos no console
- [ ] Performance Lighthouse > 80
- [ ] Documentação atualizada
- [ ] Deploy de produção configurado
- [ ] Monitoramento ativo

---

## 7. Dependências Externas

### 7.1 API Keys Necessárias

| Serviço | Variável | Status | Responsável | Prazo |
|---------|----------|--------|-------------|-------|
| OpenMic.ai | OPENMIC_API_KEY | ❌ Pendente | Comercial | Fase 3 |
| OpenMic.ai | OPENMIC_WEBHOOK_SECRET | ❌ Pendente | Comercial | Fase 3 |
| Deepgram | DEEPGRAM_API_KEY | ✅ Configurada | - | - |
| Twilio/WhatsApp | TWILIO_ACCOUNT_SID | ❌ Pendente | Comercial | Fase 3 |
| Twilio/WhatsApp | TWILIO_AUTH_TOKEN | ❌ Pendente | Comercial | Fase 3 |
| Microsoft Graph | AZURE_CLIENT_ID | ❌ Pendente | TI | Pós Go-Live |

### 7.2 Ações Comerciais Necessárias

1. **Semana 1:** Solicitar trial/contrato OpenMic.ai
2. **Semana 2:** Criar conta Twilio + aprovar templates WhatsApp
3. **Semana 3:** Validar custos operacionais (estimativa: $500-1000/mês)

---

## 8. Cronograma Resumido

```
Semana 1 (Fase 1): Fundação Crítica
├── Seg-Ter: Edição de Vagas
├── Qua-Qui: Botões/Ações
└── Sex: Limpeza de Código

Semana 2 (Fase 2): Funcionalidades Core
├── Seg-Ter: Quick Actions LIA
├── Qua: Notificações Automáticas
├── Qui: Notas de Entrevista Backend
└── Sex: Métricas LIA Reais

Semana 3 (Fase 3): Integrações
├── Seg-Ter: OpenMic.ai
├── Qua-Qui: Deepgram + WhatsApp
└── Sex: Testes de integração

Semana 4 (Fase 4): Polimento
├── Seg: Activity Feed + Compartilhamento
├── Ter-Qua: Testes E2E
├── Qui: Documentação
└── Sex: Deploy + GO-LIVE
```

---

## 9. Riscos e Mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| API Keys atrasadas | Alto | Média | Solicitar na Semana 1 |
| OpenMic.ai indisponível | Alto | Baixa | Fallback triagem manual |
| Complexidade edição vagas | Médio | Média | Priorizar campos essenciais |
| Bugs em produção | Alto | Média | Testes E2E abrangentes |
| Performance degradada | Médio | Baixa | Lighthouse audit + otimizações |

---

## 10. Métricas de Sucesso

### 10.1 KPIs Técnicos

| Métrica | Atual | Meta Go-Live |
|---------|-------|--------------|
| Score geral do módulo | 78% | 90% |
| Cobertura de testes | 0% | 60% |
| Erros LSP | 55+ | 0 |
| Lighthouse Performance | ? | > 80 |
| Tempo de carregamento | ? | < 3s |

### 10.2 KPIs de Negócio

| Métrica | Meta |
|---------|------|
| Vagas criadas sem erro | 100% |
| Triagens iniciadas com sucesso | > 95% |
| Notificações entregues | > 99% |
| Uptime | > 99.5% |

---

## 11. Próximos Passos Imediatos

### Esta Semana (Semana 1):

1. **HOJE:** Iniciar implementação de `EditJobModal.tsx`
2. **Amanhã:** Conectar edição ao backend
3. **Dia 3:** Implementar dropdown de ações na tabela
4. **Dia 4:** Duplicar e Arquivar vagas
5. **Dia 5:** Limpeza de código + revisão

### Ações Paralelas:

- [ ] Comercial: Solicitar API Key OpenMic.ai
- [ ] Comercial: Criar conta Twilio
- [ ] TI: Revisar configurações de produção

---

## 12. Aprovações

| Papel | Nome | Data | Assinatura |
|-------|------|------|------------|
| Tech Lead | - | - | - |
| Product Owner | - | - | - |
| CTO | - | - | - |

---

**Documento criado em:** 19 de Janeiro de 2026  
**Próxima revisão:** Após Fase 1 (Semana 2)
