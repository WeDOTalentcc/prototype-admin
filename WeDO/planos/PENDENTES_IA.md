# Pendentes IA - Sistema Multi-Agent WeDOTalent

> Última atualização: 21/12/2024

Este documento lista todas as funcionalidades pendentes, melhorias planejadas e integrações a serem implementadas no sistema de IA multi-agent.

---

## 1. Company Configuration Hydration (Proposta Prioritária)

### Problema Atual
O `JobIntakeAgent` usa heurísticas estáticas (benefícios genéricos, pipeline padrão) porque **não existe serviço centralizado** para consumir as configurações da empresa cadastradas no menu "Configurações".

### Proposta
Criar uma **"Etapa 0" invisível** antes do wizard de criação de vagas que carrega um `JobCreationContext` com dados da empresa.

### Dados a Consumir do Menu Configurações

| Configuração | Uso na Etapa | Fallback se Vazio |
|--------------|--------------|-------------------|
| Dados da Empresa (sobre, missão, valores) | 8 (Resumo) | Texto padrão genérico |
| Departamentos/Áreas | 2 (dropdown área) | Campo livre |
| Estrutura Organizacional | 2 (gestor por área) | Campo livre |
| Lista de Benefícios | 5 (checkboxes pré-selecionados) | Lista padrão CLT |
| Jornada de Recrutamento (Pipeline) | 7 (etapas pré-carregadas) | Etapas padrão sugeridas |
| Perguntas de Screening Padrão | 6 (junto com WSI) | Só WSI geradas por IA |

### Implementação Requerida

1. **Mapear endpoints existentes**: `CompanyProfile`, `Department`, `Benefit`, `RecruitmentJourney`, `ScreeningQuestion`
2. **Criar `CompanyConfigurationService`**: Orquestrar chamadas com cache curto em memória
3. **Integrar no `JobIntakeAgent`**: Hook de pré-carregamento com lógica de fallback
4. **Indicadores de origem**: Frontend mostra se dado veio do setup ou foi inserido manualmente
5. **Telemetria**: Registrar quando setup está incompleto para notificar admin

### Fluxo Proposto

```
Início Wizard → CompanyConfigurationService.load()
                         ↓
               ┌─── Encontrou? ───┐
               │                  │
              SIM                NÃO
               │                  │
        Usa como base       Fluxo padrão
        + permite editar    (atual)
```

---

## 2. Pendências por Agente

### Ag.0 - Orchestrator
| Pendência | Prioridade | Status |
|-----------|------------|--------|
| Refinamento do roteamento para workflows complexos | Média | 🟡 Planejado |
| Gestão de estado para multi-turn conversations | Alta | 🟡 Planejado |
| Retry automático com exponential backoff | Baixa | ⚪ Backlog |

### Ag.1 - Job Planner Agent (JobIntakeAgent)
| Pendência | Prioridade | Status |
|-----------|------------|--------|
| **Company Configuration Hydration** (ver seção 1) | Alta | 🔴 Crítico |
| Wire completo do fluxo step-by-step (dispatch path legado ainda ativo) | Alta | 🟡 Em progresso |
| Geração automática de JD completo | Média | 🟡 Planejado |
| Sugestão de requisitos baseada em vagas similares | Média | 🟡 Planejado |
| Integração com base de vagas anteriores da empresa | Baixa | ⚪ Backlog |

### Ag.2 - Sourcing Agent
| Pendência | Prioridade | Status |
|-----------|------------|--------|
| Integração completa com Pearch AI (800M+ perfis) | Alta | 🟡 Planejado |
| Estratégias de outreach mais complexas | Média | 🟡 Planejado |
| Score de aderência pré-triagem | Média | 🟡 Planejado |
| Deduplicação inteligente (fuzzy matching) | Baixa | ⚪ Backlog |

### Ag.3 - CV Screening Agent (TriagemCurricularAgent)
| Pendência | Prioridade | Status |
|-----------|------------|--------|
| Parsing de CVs em PDF/DOCX com OCR | Alta | 🟡 Planejado |
| Integração completa com sistema de Rubrics | Alta | 🟢 Implementado |
| Detecção de red flags aprimorada | Média | 🟢 Implementado |
| Dynamic cutoff learning (aprende com feedback) | Baixa | ⚪ Backlog |

### Ag.4 - Interviewer Agent (EntrevistadorAgent)
| Pendência | Prioridade | Status |
|-----------|------------|--------|
| Entrevista por voz via WhatsApp | Alta | 🟡 Planejado |
| Integração Deepgram Nova-2 para transcrição | Alta | 🟡 Planejado |
| Análise de tom e confiança na voz | Média | ⚪ Backlog |
| Detecção de respostas evasivas | Média | 🟡 Planejado |
| Interview Q&A (responder perguntas do candidato) | Baixa | ⚪ Backlog |

### Ag.5 - WSI Evaluator Agent (AvaliadorWSIAgent)
| Pendência | Prioridade | Status |
|-----------|------------|--------|
| **Implementação completa do scoring WSI** | Alta | 🔴 Crítico |
| Bloom Taxonomy classification | Alta | 🟡 Planejado |
| Dreyfus Model classification (1-5) | Alta | 🟡 Planejado |
| Big Five behavioral trait mapping | Média | 🟡 Planejado |
| CBI framework validation | Média | 🟡 Planejado |
| Calibration loop (aprende com feedback do recrutador) | Baixa | ⚪ Backlog |
| Geração de Parecer/Relatório final | Média | 🟡 Planejado |

### Ag.6 - Scheduling Agent
| Pendência | Prioridade | Status |
|-----------|------------|--------|
| Integração Microsoft Graph API | Alta | 🟡 Parcial |
| Self-scheduling links para candidatos | Média | 🟢 Implementado |
| Resolução automática de conflitos | Média | 🟡 Planejado |
| Lembretes automáticos (24h, 1h antes) | Baixa | 🟢 Implementado |
| Sugestão inteligente de horários | Baixa | ⚪ Backlog |

### Ag.7 - Analyst & Feedback Agent (AnalistaFeedbackAgent)
| Pendência | Prioridade | Status |
|-----------|------------|--------|
| Envio via SMS | Média | 🟡 Planejado |
| Notificações granulares para Teams | Média | 🟡 Planejado |
| Dashboards de performance em tempo real | Média | 🟡 Planejado |
| Relatórios preditivos | Baixa | ⚪ Backlog |
| Detecção de anomalias no funil | Baixa | ⚪ Backlog |

### Ag.8 - ATS Integrator Agent (IntegradorATSAgent)
| Pendência | Prioridade | Status |
|-----------|------------|--------|
| Integração Gupy API | Alta | 🟡 Planejado |
| Integração Pandapé API | Alta | 🟡 Planejado |
| StackOne integration (40+ ATSs) | Média | 🟡 Planejado |
| Sync bidirecional de status | Média | 🟡 Planejado |
| Webhook receivers para eventos do ATS | Baixa | ⚪ Backlog |

### Ag.9 - Recruiter Assistant Agent
| Pendência | Prioridade | Status |
|-----------|------------|--------|
| Briefing diário personalizado | Média | 🟡 Planejado |
| Alertas proativos | Média | 🟢 Implementado |
| Q&A sobre processo seletivo | Baixa | 🟡 Planejado |

---

## 3. Integrações Externas Pendentes

### APIs de Terceiros

| Integração | Descrição | Prioridade | Status |
|------------|-----------|------------|--------|
| **Pearch AI** | Busca global 800M+ perfis | Alta | 🟡 API key configurada, integração pendente |
| **Microsoft Graph** | Calendário e agendamento | Alta | 🟡 Parcial |
| **Deepgram Nova-2** | Transcrição de áudio | Média | ⚪ Backlog |
| **OpenMic.ai** | Voice screening platform | Média | ⚪ Backlog |
| **Gupy ATS** | Integração ATS brasileiro | Alta | 🟡 Planejado |
| **Pandapé ATS** | Integração ATS brasileiro | Alta | 🟡 Planejado |
| **StackOne** | Unified ATS (40+ sistemas) | Média | ⚪ Backlog |
| **WhatsApp Business API** | Comunicação com candidatos | Alta | 🟡 Planejado |
| **Twilio** | SMS e voz | Média | ⚪ Backlog |

---

## 4. Melhorias de Arquitetura

### Orquestrador e Roteamento

| Melhoria | Descrição | Impacto |
|----------|-----------|---------|
| **Policy Engine Service** | Repositório de regras de negócio, rate-limiting, escalation workflows | Alto |
| **Task DAG Validation** | Validação de dependências circulares antes de execução | Médio |
| **Agent Health Monitoring** | Monitoramento de saúde e performance de cada agente | Médio |
| **Graceful Degradation** | Fallback quando agente específico falha | Alto |

### Aprendizado e Calibração

| Melhoria | Descrição | Impacto |
|----------|-----------|---------|
| **Calibration Loop** | Loop de feedback para aprendizado contínuo | Alto |
| **Dynamic Cutoff Learning** | Ajuste automático de thresholds baseado em resultados | Médio |
| **Recruiter Feedback Integration** | Incorporar feedback do recrutador no modelo | Alto |
| **A/B Testing de Prompts** | Testar variações de prompts e medir conversão | Baixo |

---

## 5. Novos Agentes Planejados (Fases Futuras)

| Agente | Descrição | Fase |
|--------|-----------|------|
| **Onboarding Agent** | Automação do processo de onboarding | Fase 3 |
| **Performance Analyst Agent** | Análise de performance pós-contratação | Fase 3 |
| **Culture Fit Agent** | Avaliação de fit cultural | Fase 2 |
| **Offer Agent** | Gestão de propostas e negociação | Fase 2 |
| **Compliance Agent** | Verificação automática de compliance (LGPD, etc) | Fase 2 |

---

## 6. Prioridades Imediatas (Próximo Sprint)

### 🔴 Crítico
1. **Company Configuration Hydration** - JobIntakeAgent consumir configurações da empresa
2. **WSI Evaluator Agent** - Implementação completa do scoring científico
3. **Wire completo do fluxo step-by-step** - Corrigir dispatch path legado

### 🟠 Alta Prioridade
4. Integração Pearch AI para busca global
5. Microsoft Graph API para agendamento
6. Parsing de CVs com suporte a PDF/DOCX

### 🟡 Média Prioridade
7. WhatsApp Business API
8. Integrações ATS (Gupy, Pandapé)
9. Entrevista por voz

---

## Legenda

| Símbolo | Significado |
|---------|-------------|
| 🔴 | Crítico - Bloqueia funcionalidade principal |
| 🟠 | Alta prioridade - Necessário para MVP completo |
| 🟡 | Planejado - Em backlog priorizado |
| 🟢 | Implementado - Funcional |
| ⚪ | Backlog - Futuro, não priorizado |

---

## Arquivos Relacionados

- `lia-agent-system/app/agents/specialized/` - Implementação dos agentes
- `lia-agent-system/app/orchestrator/` - Orquestrador central
- `lia-agent-system/app/services/` - Serviços compartilhados
- `docs/JOB_CREATION_WIZARD_FLOW.md` - Fluxo de criação de vagas
- `docs/AI_TRAINING_PER_AGENT.md` - Treinamento por agente
