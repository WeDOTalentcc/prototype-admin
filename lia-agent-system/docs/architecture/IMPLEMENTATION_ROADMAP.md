# Plano de Implementação - Roadmap Consolidado

**Última Atualização:** 30 Janeiro 2026

## Visão Geral

Este documento consolida os planos de implementação para a Plataforma LIA, organizando as tarefas em fases progressivas com base na auditoria técnica e no roadmap de produto.

**Estimativa total:** 8-12 semanas para implementação completa

---

## 1. Visão Geral e Cronograma

### Cronograma Visual

```
Semana  1  2  3  4  5  6  7  8  9  10  11  12
        ├──────┤
        FASE 1: Qualidade & Admin Foundation
              ├──────┤
              FASE 2: Custos & Integrações Core
                    ├──────┤
                    FASE 3: Robustez & Avaliação
                          ├──────┤
                          FASE 4: ATS & Monitoramento
                                ├──────┤
                                FASE 5: Orquestração & Melhoria Contínua
```

### Resumo das Fases

| Fase | Semanas | Foco | Esforço |
|------|---------|------|---------|
| 1 | 1-2 | Qualidade de Respostas & Admin Foundation | 5 dias |
| 2 | 3-4 | Otimização de Custos & Integrações Core | 6 dias |
| 3 | 5-6 | Robustez, Estabilidade & Avaliação | 5 dias |
| 4 | 7-8 | ATS & Monitoramento | 6 dias |
| 5 | 9-10 | Orquestração & Melhoria Contínua | 5 dias |
| **Total** | **10 semanas** | - | **27 dias** |

---

## 2. Fase 1: Qualidade e Admin Foundation (Semanas 1-2)

### Sprint 1.1: Enriquecimento de Prompts
**Prioridade:** Alta | **Esforço:** 3 dias | **Impacto:** Alto

#### Tarefas
1. **Revisar prompts de sistema** (2 dias)
   - [ ] Auditar todos os prompts em `app/agents/prompts/agent_prompts.py`
   - [ ] Adicionar vocabulário técnico de RH brasileiro
   - [ ] Incluir termos esperados nas respostas (funil, etapa, conversão, etc.)
   - [ ] Documentar personas de cada agente

2. **Adicionar few-shot examples** (1 dia)
   - [ ] Criar banco de exemplos em `app/agents/prompts/examples/`
   - [ ] 5-10 exemplos por intent principal
   - [ ] Exemplos bilíngues (PT-BR e EN)

#### Arquivos a Modificar
```
lia-agent-system/app/agents/prompts/agent_prompts.py
lia-agent-system/app/agents/prompts/examples/
lia-agent-system/app/orchestrator/orchestrator.py
```

#### Métricas de Sucesso
- [ ] Quality score médio >= 60% (atualmente 25-50%)
- [ ] Keywords encontradas >= 2/4 em cada cenário

### Sprint 1.2: Tom de Voz Consistente
**Prioridade:** Alta | **Esforço:** 2 dias | **Impacto:** Médio

#### Tarefas
1. **Definir persona LIA** (0.5 dia)
   - [ ] Criar guia de tom de voz
   - [ ] Definir vocabulário formal padrão
   - [ ] Listar termos proibidos (gírias, abreviações)

2. **Implementar validação de tom** (1 dia)
   - [ ] Adicionar pós-processamento de respostas
   - [ ] Criar filter para linguagem informal
   - [ ] Implementar fallback para tom neutro

3. **Testes de consistência** (0.5 dia)
   - [ ] Criar suite de testes de tom
   - [ ] Validar com 50+ cenários

#### Arquivos a Modificar
```
lia-agent-system/app/agents/robustness/response_filter.py (novo)
lia-agent-system/app/agents/base_agent.py
lia-agent-system/tests/test_tone_consistency.py (novo)
```

### Sprint 1.3: Admin Foundation
**Prioridade:** Alta | **Esforço:** 4 dias | **Impacto:** Alto

#### Reestruturação da Navegação do Admin
```
/admin
├── /dashboard (existente)
├── /configuracoes → renomear para /integracoes
├── /clientes (existente)
├── /planos (existente)
├── /metricas (existente)
├── /setup-empresa (NOVO)
├── /testes-tecnicos (NOVO)
├── /big-five (NOVO)
└── /configuracoes-globais (NOVO)
```

#### Área de Integrações (`/admin/integracoes`)

| Categoria | Integrações | Status |
|-----------|-------------|--------|
| **Comunicação** | Microsoft Teams, WhatsApp Business, Email | 🔴 |
| **Calendário** | Microsoft Graph Calendar | 🔴 |
| **Sourcing** | Pearch AI | 🟡 |
| **ATS** | Gupy, Pandapé, Merge.dev | 🔴 |
| **IAs** | Claude, ChatGPT, Gemini | 🟡 |
| **Voice** | OpenMic.ai, Deepgram | 🟡 |
| **Database** | PostgreSQL (Replit) | ✅ |

#### Setup da Empresa (`/admin/setup-empresa`)

**Seções:**
1. **Informações Gerais** - Nome, Setor, Porte, Logo, Website
2. **Áreas e Departamentos** - CRUD, Hierarquia, Gestores
3. **Benefícios** - Gerais, por área, por nível
4. **Cultura e Valores** - Visão, Missão, EVP, Tom de comunicação
5. **Perfil Ideal (DNA)** - Critérios obrigatórios/desejáveis, Red flags
6. **Integrações da Empresa** - ATS, Calendário, Workforce

#### Critérios de Sucesso Fase 1
- [ ] Todas as páginas do Admin acessíveis
- [ ] Integrações com status visual
- [ ] Setup da empresa funcional com persistência
- [ ] Quality score de prompts >= 60%

---

## 3. Fase 2: Custos e Integrações Core (Semanas 3-4)

### Sprint 2.1: Sistema de Caching
**Prioridade:** Média | **Esforço:** 4 dias | **Impacto:** Alto

#### Tarefas
1. **Cache de respostas frequentes** (2 dias)
   - [ ] Identificar top 20 queries mais frequentes
   - [ ] Implementar cache Redis com TTL de 5 min
   - [ ] Criar invalidação por contexto

2. **Cache de embeddings** (1 dia)
   - [ ] Cachear embeddings de vagas ativas
   - [ ] Implementar warm-up no startup

3. **Compressão de contexto** (1 dia)
   - [ ] Implementar summarização de histórico longo
   - [ ] Limitar contexto a últimas 5 mensagens + resumo

#### Métricas de Sucesso
- [ ] Redução de 30% no uso de tokens
- [ ] Cache hit rate >= 40%
- [ ] Custo mensal < $150 (atual ~$157)

### Sprint 2.2: Monitoramento de Tokens
**Prioridade:** Média | **Esforço:** 2 dias | **Impacto:** Médio

#### Tarefas
1. **Dashboard de consumo** (1 dia)
   - [ ] Criar endpoint `/api/v1/admin/token-usage`
   - [ ] Agregar por usuário, agente, intent
   - [ ] Alertas para uso excessivo

2. **Métricas em tempo real** (1 dia)
   - [ ] Adicionar logging estruturado de tokens
   - [ ] Integrar com observabilidade existente

### Sprint 2.3: Microsoft Teams Integration
**Prioridade:** Alta | **Esforço:** 3 dias | **Impacto:** Alto

**Funcionalidades:**
- Envio de notificações proativas
- Mensagens com Adaptive Cards
- Botões de ação (Aprovar/Rejeitar)
- Recebimento de respostas

**Implementação:**
```python
class TeamsService:
    def send_notification(self, user_id: str, message: dict) -> bool
    def send_adaptive_card(self, user_id: str, card: dict) -> bool
    def handle_action_response(self, action_data: dict) -> dict
```

### Sprint 2.4: Microsoft Graph Calendar Integration
**Prioridade:** Alta | **Esforço:** 2 dias | **Impacto:** Alto

**Funcionalidades:**
- Verificar disponibilidade
- Criar eventos
- Gerar links de self-scheduling
- Sincronizar com calendário do recrutador

**Implementação:**
```python
class CalendarService:
    def get_availability(self, user_id: str, date_range: tuple) -> list
    def create_event(self, event_data: dict) -> dict
    def generate_scheduling_link(self, slots: list) -> str
```

### Sprint 2.5: WhatsApp Business Integration
**Prioridade:** Média | **Esforço:** 2 dias | **Impacto:** Médio

**Funcionalidades:**
- Envio de mensagens templated
- Recebimento de respostas
- Triagem assíncrona via chat
- Timer de 24h

#### Critérios de Sucesso Fase 2
- [ ] Notificação Teams funcionando
- [ ] Agendamento de eventos no calendário
- [ ] Envio de WhatsApp funcionando
- [ ] Custo mensal < $150

---

## 4. Fase 3: Robustez e Avaliação (Semanas 5-6)

### Sprint 3.1: Rate Limiting
**Prioridade:** Média | **Esforço:** 2 dias | **Impacto:** Alto

#### Tarefas
1. **Rate limiting por usuário** (1 dia)
   - [ ] 100 requests/minuto por usuário
   - [ ] 1000 requests/hora por empresa
   - [ ] Resposta 429 com Retry-After

2. **Proteção contra abuse** (1 dia)
   - [ ] Detectar padrões de abuse
   - [ ] Blacklist temporário automático

### Sprint 3.2: Circuit Breaker
**Prioridade:** Média | **Esforço:** 3 dias | **Impacto:** Alto

#### Tarefas
1. **Circuit breaker para APIs externas** (2 dias)
   - [ ] Implementar para OpenAI, Anthropic, Gemini
   - [ ] Fallback automático entre providers
   - [ ] Backoff exponencial

2. **Health checks automatizados** (1 dia)
   - [ ] Verificar APIs externas a cada 30s
   - [ ] Alertas para degradação

### Sprint 3.3: Módulo Big Five
**Prioridade:** Alta | **Esforço:** 4 dias | **Impacto:** Alto

**Conceito:** Avalia 5 traços de personalidade (OCEAN):
- **O**penness (Abertura a experiências)
- **C**onscientiousness (Conscienciosidade)
- **E**xtraversion (Extroversão)
- **A**greeableness (Amabilidade)
- **N**euroticism (Neuroticismo)

**Implementação:**
```python
class BigFiveService:
    def generate_test(self, job_id: str) -> dict
    def evaluate_responses(self, responses: list) -> dict
    def compare_with_profile(self, scores: dict, job_id: str) -> dict
    def generate_report(self, candidate_id: str) -> dict
```

**Admin UI - Configuração:**
1. Banco de Perguntas (50 itens standard + customizáveis)
2. Perfis por Cargo (templates por função)
3. Configurações do Teste (tempo, questões, escala)
4. Relatórios (radar chart, comparação com ideal)

### Sprint 3.4: Módulo Testes Técnicos
**Prioridade:** Alta | **Esforço:** 4 dias | **Impacto:** Alto

**Implementação:**
```python
class TechnicalTestService:
    def generate_test_with_ai(self, area: str, skills: list, level: str) -> dict
    def evaluate_multiple_choice(self, answers: dict) -> dict
    def evaluate_code(self, code: str, expected: str) -> dict
    def evaluate_essay(self, answer: str, rubric: str) -> dict
    def calculate_final_score(self, results: dict) -> float
```

**Tipos de Questões:**
- Múltipla escolha (correção automática)
- Código (análise de corretude + qualidade)
- Dissertativa (avaliação semântica com IA)

#### Critérios de Sucesso Fase 3
- [ ] Rate limiting ativo
- [ ] Circuit breaker funcionando
- [ ] Teste Big Five funcional
- [ ] Testes técnicos com correção IA

---

## 5. Fase 4: ATS e Monitoramento (Semanas 7-8)

### Sprint 4.1: Dashboard de Agentes
**Prioridade:** Baixa | **Esforço:** 4 dias | **Impacto:** Médio

#### Tarefas
1. **Dashboard de status** (2 dias)
   - [ ] Status de cada agente
   - [ ] Latência média por agente
   - [ ] Taxa de sucesso por intent

2. **Histórico de performance** (2 dias)
   - [ ] Gráficos de tendência
   - [ ] Comparação semanal
   - [ ] Alertas de degradação

### Sprint 4.2: Documentação de Prompts
**Prioridade:** Baixa | **Esforço:** 2 dias | **Impacto:** Baixo

#### Tarefas
- [ ] Criar catálogo de prompts
- [ ] Versionamento de prompts
- [ ] Histórico de alterações

### Sprint 4.3: Integração ATS (Gupy)
**Prioridade:** Alta | **Esforço:** 4 dias | **Impacto:** Alto

**Funcionalidades:**
- Importar histórico de contratações
- Sincronizar vagas (bidirecional)
- Importar candidatos
- Atualizar status de candidatos

**Admin UI:**
- OAuth para conectar conta Gupy
- Mapeamento de campos
- Frequência de sync
- Log de sincronização

### Sprint 4.4: Integração Merge.dev (Unified ATS)
**Prioridade:** Média | **Esforço:** 2 dias | **Impacto:** Médio

**Funcionalidades:**
- API única para 40+ ATS
- Fallback quando Gupy/Pandapé não disponíveis
- Mapeamento unificado

### Sprint 4.5: Historical Analysis Service
**Prioridade:** Média | **Esforço:** 3 dias | **Impacto:** Alto

```python
class HistoricalAnalysisService:
    def import_from_ats(self, ats_type: str, credentials: dict) -> dict
    def analyze_patterns(self, data: list) -> dict
    def generate_ideal_profile(self, patterns: dict) -> dict
    def validate_with_recruiter(self, profile: dict) -> dict
```

#### Critérios de Sucesso Fase 4
- [ ] Conexão com pelo menos 1 ATS
- [ ] Importação de histórico
- [ ] Análise de padrões funcionando
- [ ] Dashboard de agentes operacional

---

## 6. Fase 5: Orquestração e Melhoria Contínua (Semanas 9-10)

### Sprint 5.1: A/B Testing de Prompts
**Prioridade:** Baixa | **Esforço:** 3 dias | **Impacto:** Médio

#### Tarefas
1. **Framework de A/B testing** (2 dias)
   - [ ] Suporte a variantes de prompts
   - [ ] Métricas por variante
   - [ ] Rollout gradual

2. **Integração com analytics** (1 dia)
   - [ ] Tracking de performance por variante
   - [ ] Dashboard de resultados

### Sprint 5.2: Testes de Regressão
**Prioridade:** Baixa | **Esforço:** 2 dias | **Impacto:** Alto

#### Tarefas
- [ ] 100+ cenários de teste
- [ ] Execução diária via CI/CD
- [ ] Alertas para regressões

### Sprint 5.3: Orquestração dos Agentes
**Prioridade:** Alta | **Esforço:** 3 dias | **Impacto:** Alto

**Garantir que cada agente acessa os dados corretos:**

| Agente | Dados que Precisa | Fonte |
|--------|-------------------|-------|
| Job Planner | Benefícios, Cultura, Perfil Ideal | Setup Empresa |
| Sourcing | Perfil Ideal, Pesos, ATS | Setup + Integrações |
| CV Screener | Matriz Técnica, Perfil Ideal | Vaga + Setup |
| WSI Evaluator | Competências, Big Five | Vaga + Config |
| Interview Scheduler | Calendário, Regras | Integrações + Vaga |
| Recruiter Assistant | Templates, Teams | Setup + Integrações |
| Analytics | Histórico, Padrões | ATS + Database |

### Sprint 5.4: Sistema de Scoring Composto
**Prioridade:** Alta | **Esforço:** 2 dias | **Impacto:** Alto

```python
class ScoringService:
    def calculate_composite_score(self, candidate_id: str, job_id: str) -> dict:
        """
        Calcula Score LIA composto:
        - Aderência ao Perfil (25%)
        - Score WSI (25%)
        - Critérios Técnicos (20%)
        - Critérios Comportamentais (15%)
        - Teste Técnico (10%) - se disponível
        - Big Five (5%) - se disponível
        """
```

### Sprint 5.5: Proactive Service Completo
**Prioridade:** Média | **Esforço:** 2 dias | **Impacto:** Médio

**Funcionalidades:**
- Morning briefing via Teams
- End-of-day summary
- Alertas de entrevistas
- Notificações de triagem
- Lembretes de follow-up

### Sprint 5.6: Testes End-to-End
**Prioridade:** Alta | **Esforço:** 2 dias | **Impacto:** Alto

**Cenários a testar:**
1. Criação de empresa → Setup completo
2. Abertura de vaga → Uso de benefícios do setup
3. Sourcing → Uso de perfil ideal
4. Triagem → WSI + Big Five
5. Agendamento → Calendar integration
6. Feedback → Teams + Email + WhatsApp

#### Critérios de Sucesso Fase 5
- [ ] Fluxo completo funcionando
- [ ] Score composto calculado
- [ ] Notificações proativas funcionando
- [ ] Dados fluindo entre sistemas

---

## 7. Priorização MVP e Recursos

### MVP Essencial (Semanas 1-4)

Se precisarmos entregar um MVP mais rápido, focar em:

1. ✅ Setup Empresa básico (sem análise automática)
2. ✅ Integrações: Email + Teams
3. ✅ Big Five simplificado
4. ✅ Score composto básico
5. ✅ Fluxo end-to-end funcionando

### V1.1 (Semanas 5-8)
1. WhatsApp Business
2. Calendar Integration
3. Testes Técnicos com IA
4. Integração 1 ATS (Gupy)

### V1.2 (Semanas 9-12)
1. Análise automática de cultura
2. Historical Analysis
3. Workforce Planning
4. Múltiplos ATS

---

## Recursos Necessários

### Backend
- 1 desenvolvedor Python senior (full-time)
- Conhecimento em LangGraph, FastAPI

### Frontend
- 1 desenvolvedor React/Next.js (full-time)
- Conhecimento em Tailwind, shadcn/ui

### Integrações
- Acesso às APIs (Teams, WhatsApp, Gupy, etc.)
- Credenciais de teste

### Infraestrutura
- Replit (já configurado)
- PostgreSQL (já configurado)

---

## Próximos Passos Imediatos

1. ✅ Aprovar plano de implementação
2. 🔴 Iniciar Sprint 1.1 (Enriquecimento de Prompts)
3. 🔴 Definir métricas de baseline antes das mudanças
4. 🔴 Criar ambiente de staging para testes

---

*Documento consolidado em: Janeiro 2026*  
*Baseado em: Auditoria Técnica (Janeiro 2026) + Plano de Fases de Produto (Novembro 2024)*
