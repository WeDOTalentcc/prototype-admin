---
name: feature-impact
description: Analisa o impacto sistêmico completo de uma feature ou ajuste na plataforma LIA. Use quando o usuário pedir para criar uma feature nova, ajustar uma existente, ou antes de qualquer implementação significativa. Garante que todas as dimensões da plataforma sejam consideradas.
---

# Feature Impact Analysis — LIA Platform

Antes de qualquer implementação, execute esta análise completa. O objetivo é garantir que nenhuma dimensão da plataforma seja esquecida.

## Processo

1. **Entender o escopo**: Leia a descrição da feature/ajuste
2. **Mapear impactos por dimensão**: Para cada dimensão abaixo, determine se há impacto (Sim/Não/Talvez) e o que precisa ser feito
3. **Priorizar**: Identifique o que é bloqueante vs. opcional para o MVP
4. **Propor plano**: Liste as tarefas em ordem lógica de implementação

---

## Checklist de Dimensões

### 1. FRONTEND
- [ ] Novas páginas ou rotas (`src/app/*/page.tsx`)?
- [ ] Novos componentes ou ajuste em existentes (`src/components/`)?
- [ ] Novos hooks ou ajuste em existentes (`src/hooks/`)?
- [ ] Novas rotas de API proxy (`src/app/api/backend-proxy/`)?
- [ ] Mudanças de layout, design, fluxo UX?
- [ ] Novos estados de loading/error/empty?
- [ ] Impacto em componentes compartilhados (bulk actions, modais, tabelas)?
- [ ] Compatibilidade com Design System v4.2.1 (tokens wedo-*, rounded-md, sem shadows)?

### 2. BACKEND — API
- [ ] Novos endpoints REST (`app/api/v1/`)?
- [ ] Ajustes em endpoints existentes (breaking changes?)?
- [ ] Novos schemas Pydantic (request/response)?
- [ ] Rate limiting adequado?
- [ ] Autenticação/autorização correta (multi-tenant isolamento)?

### 3. BACKEND — SERVICES
- [ ] Novos serviços (`app/services/`)?
- [ ] Ajuste em serviços existentes?
- [ ] Lógica de negócio impactada?
- [ ] Tratamento de erros e fallbacks?

### 4. BANCO DE DADOS
- [ ] Novas tabelas SQLAlchemy (`app/models/`)?
- [ ] Novos campos em tabelas existentes?
- [ ] Migration Alembic necessária?
- [ ] Índices para performance?
- [ ] Isolamento multi-tenant (company_id em todas as queries)?
- [ ] Campos sensíveis (PII) com mascaramento?

### 5. CAMADA DE IA / AGENTES
- [ ] Impacto em agentes ReAct existentes (Wizard, Pipeline, Sourcing, etc.)?
- [ ] Novos tools no tool registry?
- [ ] Ajuste de system prompts?
- [ ] Mudança no state machine (`app/shared/agents/state_machine.py`)?
- [ ] Novos nodes LangGraph (`app/shared/agents/nodes.py`)?
- [ ] Impacto na memória de trabalho ou longa duração do agente?
- [ ] Novos domínios de agente (`app/domains/`)?
- [ ] FairnessGuard ou FactChecker precisam ser ajustados?
- [ ] Custo de tokens estimado (usar `token_tracking_service.py`)?

### 6. COMUNICAÇÕES & NOTIFICAÇÕES
- [ ] Novos tipos de notificação (bell, email, WhatsApp, Teams)?
- [ ] Novos templates de email (`app/api/v1/email_templates.py`)?
- [ ] Mensagens WhatsApp (Meta API ou Twilio)?
- [ ] Mensagens Microsoft Teams (bot ou webhook)?
- [ ] Notificações in-app necessárias?
- [ ] Preferências do usuário respeitadas (communication_matrix)?
- [ ] Serviço de notificação central afetado (`notification_service.py`)?

### 7. INTEGRAÇÕES EXTERNAS
- [ ] Impacto no WorkOS (auth, SCIM)?
- [ ] Impacto no Microsoft Graph (Teams, Outlook, calendário)?
- [ ] Impacto no Pearch AI (busca de candidatos)?
- [ ] Impacto no Deepgram (transcrição)?
- [ ] Impacto no OpenMic.ai (triagem por voz)?
- [ ] Impacto no Gupy/Pandapé ATS (sincronização)?
- [ ] Impacto no HubSpot (CRM)?
- [ ] Impacto no Stripe (billing)?
- [ ] Novos webhooks a configurar?
- [ ] Novas variáveis de ambiente necessárias?

### 8. COMPLIANCE, LGPD & GOVERNANÇA
- [ ] Feature processa dados pessoais (PII)? → Verificar LGPD
- [ ] Consentimento do titular necessário?
- [ ] Auditoria de acesso precisa ser registrada (`audit_logs.py`)?
- [ ] Impacto nos controles SOC 2 / ISO 27001?
- [ ] Impacto nos controles BCB 498 (instituições financeiras)?
- [ ] Dados podem ser exportados/deletados via Data Subject Request?
- [ ] Retenção de dados definida?
- [ ] Feature precisa de aprovação antes de executar ações destrutivas?

### 9. SEGURANÇA & MULTI-TENANT
- [ ] Isolamento por `company_id` em todos os dados?
- [ ] Permissões de usuário verificadas (roles/scopes)?
- [ ] Vulnerabilidades: SQL injection, XSS, IDOR, command injection?
- [ ] Rate limiting nas rotas novas?
- [ ] Chaves de API criptografadas (nunca em plaintext no código)?

### 10. INFRAESTRUTURA & ASYNC
- [ ] Tarefas longas precisam ir para Celery (evitar timeout)?
- [ ] RabbitMQ necessário (pub/sub ou filas)?
- [ ] Redis: novo cache key pattern necessário?
- [ ] Migrations precisam rodar sem downtime?
- [ ] Health checks afetados?

### 11. OBSERVABILIDADE & MONITORAMENTO
- [ ] Logs estruturados adicionados nas operações novas?
- [ ] Métricas Prometheus relevantes?
- [ ] LangSmith traces para as chamadas LLM?
- [ ] Alertas de erro configurados?
- [ ] Activity feed registrado (`activity_service.py`)?
- [ ] Agent execution log atualizado (`execution_log_store.py`)?

### 12. TESTES & QUALIDADE
- [ ] Casos de teste unitário identificados?
- [ ] Casos de teste de integração identificados?
- [ ] Casos edge identificados (empty state, erro, timeout, multi-tenant)?
- [ ] Compatibilidade com dados existentes em produção?
- [ ] Rollback plan se algo der errado?

---

## Formato de Saída

Apresentar análise no formato:

```markdown
## Análise de Impacto: [Nome da Feature]

### Resumo
[1-2 frases descrevendo o que será feito]

### Dimensões Impactadas
| Dimensão | Impacto | O que fazer |
|----------|---------|-------------|
| Frontend | Alto/Médio/Baixo/Nenhum | descrição |
| Backend API | ... | ... |
| Banco de Dados | ... | ... |
| Agentes IA | ... | ... |
| Comunicações | ... | ... |
| Integrações | ... | ... |
| Compliance/LGPD | ... | ... |
| Segurança | ... | ... |
| Infraestrutura | ... | ... |
| Observabilidade | ... | ... |

### Plano de Implementação
1. [Tarefa 1 — bloqueante]
2. [Tarefa 2 — depende da 1]
3. [Tarefa 3 — paralela com 2]
...

### Riscos e Atenções
- [Risco 1]: [Mitigação]
- [Risco 2]: [Mitigação]

### Pronto para implementar? [Sim/Precisa de mais informação]
```

---

## Regras de Ouro

1. **Nunca implementar sem mapear o impacto primeiro**
2. **Multi-tenant**: Todo dado novo deve ter `company_id` e isolamento
3. **LGPD**: Qualquer campo novo com dado pessoal precisa de análise de compliance
4. **Design**: Sempre perguntar antes de mudar layout/design
5. **Chat first**: Novas interações devem ser via chat, não via botões
6. **Tokens**: Estimar custo de IA para features com LLM calls frequentes

---

## Uso em Outros Ambientes

| Ambiente | Como Usar |
|----------|-----------|
| **Claude Code / Replit Agent** | Digite `/feature-impact` no chat para ativar a skill completa |
| **Cursor IDE** | Mencione `@.cursor/rules/feature-impact.mdc` no contexto ou ative a regra para o projeto |
| **GitHub / Outros** | Referencie diretamente: `.agents/skills/feature-impact/SKILL.md` |

**Fluxo recomendado:**
1. Antes de escrever qualquer linha de código, execute `/feature-impact`
2. Preencha o checklist de 12 dimensões
3. Aguarde aprovação do plano antes de implementar
