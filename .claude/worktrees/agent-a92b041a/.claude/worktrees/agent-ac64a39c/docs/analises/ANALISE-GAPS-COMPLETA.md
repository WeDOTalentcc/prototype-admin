# Análise Completa de Gaps - WeDOTalent + LIA
## O Que Falta Implementar (Dezembro 2025)

---

# RESUMO EXECUTIVO

| Categoria | Total Itens | Implementados | Faltando | % Completo |
|-----------|-------------|---------------|----------|------------|
| Gestão de Candidatos | 8 | 4 | 4 | 50% |
| Gestão de Vagas | 9 | 1 | 8 | 11% |
| Funil de Talentos | 9 | 4 | 5 | 44% |
| Busca de Candidatos | 6 | 4 | 2 | 67% |
| **Sistema de Testes (Assessments)** | 11 | 2 | 9 | 18% |
| WSI Voice Screening | 8 | 2 | 6 | 25% |
| Agendamento | 4 | 0 | 4 | 0% |
| Comunicação Omnichannel | 5 | 1 | 4 | 20% |
| Dashboards & Analytics | 7 | 2 | 5 | 29% |
| Multi-Agent System | 10 | 4 | 6 | 40% |
| Integrações Externas | 12 | 5 | 7 | 42% |
| WeDo Admin (Compliance) | 15 | 15 | 0 | 100% |
| **Compliance Interface Candidato** | 15 | 3 | 12 | 20% |
| **TOTAL** | **119** | **47** | **72** | **39%** |

---

# DETALHAMENTO POR MÓDULO

---

## 1. GESTÃO DE CANDIDATOS

### ✅ Implementado
| Feature | Descrição |
|---------|-----------|
| CRUD básico | Criar, ler, atualizar, deletar |
| Tags e categorização | Organização flexível |
| Busca avançada | Filtros combinados + AI filters |
| Schema completo | 49 campos no banco |

### 🔴 Falta Implementar
| Feature | Descrição | Prioridade | Complexidade |
|---------|-----------|------------|--------------|
| Importação CSV/Excel | Upload em massa com validação | P1 | Média |
| Parsing de CV automático | Extração de dados de PDFs | P1 | Alta |
| Detecção de duplicados | Merge inteligente de candidatos | P2 | Alta |
| Exportação | PDF, CSV, Excel | P1 | Baixa |

---

## 2. GESTÃO DE VAGAS

### ✅ Implementado
| Feature | Descrição |
|---------|-----------|
| Schema no banco | 55 campos definidos |

### 🔴 Falta Implementar
| Feature | Descrição | Prioridade | Complexidade |
|---------|-----------|------------|--------------|
| Criação via chat | LIA extrai dados de descrição | P0 | Alta |
| Templates de vagas | Modelos reutilizáveis | P1 | Média |
| Pipeline customizável | Drag-and-drop de etapas | P0 | Alta |
| Aprovação workflow | Multi-nível de aprovação | P1 | Média |
| Publicação multi-canal | LinkedIn, Indeed, Glassdoor | P2 | Alta |
| Analytics por vaga | Métricas de performance | P1 | Média |
| Clonagem de vagas | Duplicar configurações | P2 | Baixa |
| **Shortlist Interativa** | Compartilhar candidatos com gestores via URL interativa | P0 | Alta |

### 🆕 NOVA FEATURE: Shortlist Interativa para Gestores

**Descrição:** Recrutador pode compartilhar uma shortlist de candidatos com o gestor da vaga através de uma URL. O gestor pode interagir com a shortlist: ver candidatos, deixar comentários e solicitar agendamento de entrevistas.

**Funcionalidades:**
| Item | Descrição |
|------|-----------|
| Geração de URL única | Link com token seguro para a shortlist |
| Visualização de candidatos | Cards/tabela com informações dos candidatos |
| Preview detalhado | Modal com CV resumido, LIA Score, histórico |
| Comentários por candidato | Gestor pode deixar feedback sobre cada candidato |
| Solicitar entrevista | Botão para pedir agendamento de entrevista |
| Aprovar/Rejeitar | Gestor pode aprovar ou rejeitar candidatos |
| Notificação ao recrutador | Alertas quando gestor interage |
| Histórico de interações | Log de todas as ações do gestor |

**Tela do Gestor (Shortlist Interativa):**
```
┌─────────────────────────────────────────────────────────────────────────┐
│  SHORTLIST - Vaga: Desenvolvedor Python Sênior                          │
│  Enviado por: Ana Recrutadora | 5 candidatos selecionados               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ 👤 João Silva                                    LIA Score: 92    │  │
│  │ Senior Developer @ Tech Corp | 8 anos exp | São Paulo             │  │
│  │ Skills: Python, Django, AWS, PostgreSQL                           │  │
│  │ ─────────────────────────────────────────────────────────────     │  │
│  │ 💬 Comentários (1)                                                │  │
│  │ ┌─────────────────────────────────────────────────────────────┐   │  │
│  │ │ Gestor: "Perfil interessante, gostaria de entrevistar"      │   │  │
│  │ └─────────────────────────────────────────────────────────────┘   │  │
│  │ [Adicionar comentário...]                                         │  │
│  │                                                                   │  │
│  │ [👍 Aprovar] [👎 Rejeitar] [📅 Agendar Entrevista] [📄 Ver CV]   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ 👤 Maria Santos                                   LIA Score: 88   │  │
│  │ Tech Lead @ StartupXYZ | 10 anos exp | Remoto                     │  │
│  │ Skills: Python, FastAPI, Kubernetes, MongoDB                      │  │
│  │ ─────────────────────────────────────────────────────────────     │  │
│  │ 💬 Comentários (0)                                                │  │
│  │ [Adicionar comentário...]                                         │  │
│  │                                                                   │  │
│  │ [👍 Aprovar] [👎 Rejeitar] [📅 Agendar Entrevista] [📄 Ver CV]   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ───────────────────────────────────────────────────────────────────    │
│  Resumo: 1 aprovado | 0 rejeitados | 1 entrevista solicitada           │
└─────────────────────────────────────────────────────────────────────────┘
```

**Fluxo de Interação:**
```
Recrutador                          Sistema                           Gestor
    │                                  │                                 │
    │── Seleciona candidatos ─────────▶│                                 │
    │── Clica "Compartilhar Shortlist"▶│                                 │
    │                                  │── Gera URL única ──────────────▶│
    │                                  │                                 │
    │                                  │◀── Acessa URL ──────────────────│
    │                                  │◀── Visualiza candidatos ────────│
    │                                  │◀── Adiciona comentário ─────────│
    │◀── Notificação de comentário ────│                                 │
    │                                  │◀── Solicita entrevista ─────────│
    │◀── Notificação de agendamento ───│                                 │
    │                                  │                                 │
    │── Agenda entrevista ────────────▶│── Confirma com gestor ─────────▶│
```

**NOTA:** Este módulo está quase zerado. Apenas schema existe.

---

## 3. FUNIL DE TALENTOS (TALENT FUNNEL)

### ✅ Implementado
| Feature | Descrição |
|---------|-----------|
| Kanban visual | Arrastar candidatos entre etapas |
| Filtros avançados | 15+ critérios combináveis |
| Preview rápido | Modal de visualização |
| Comparação lado-a-lado | Até 4 candidatos |

### 🔴 Falta Implementar
| Feature | Descrição | Prioridade | Complexidade |
|---------|-----------|------------|--------------|
| Bulk actions | Ações em lote (50+ candidatos) | P0 | Média |
| Exportação de shortlist | PDF executivo | P1 | Média |
| Notificações real-time | Alertas de mudança | P1 | Alta |
| Dados reais no backend | Conectar frontend ao backend | P0 | Alta |
| **Compartilhar Resultado de Busca** | Gerar URL com tabela de candidatos + preview para gestores | P0 | Média |

### 🆕 NOVA FEATURE: Compartilhar Resultado de Busca

**Descrição:** Após realizar uma pesquisa no funil de talentos, o recrutador pode compartilhar o resultado com gestores internos da empresa através de uma URL gerada automaticamente.

**Funcionalidades:**
| Item | Descrição |
|------|-----------|
| Botão "Compartilhar" | Disponível em Actions após fazer uma busca |
| Geração de URL única | Link público/privado com token de acesso |
| Visualização da tabela | Gestor vê a mesma tabela de candidatos |
| Preview de candidatos | Modal com informações resumidas de cada candidato |
| Expiração configurável | Link válido por X dias (padrão: 7 dias) |
| Controle de acesso | Opcional: exigir login ou acesso livre |

**Tela do Gestor (Viewer):**
```
┌─────────────────────────────────────────────────────────────┐
│  RESULTADO DA BUSCA - Compartilhado por [Recrutador]        │
│  "Desenvolvedores Python Sênior - SP" | 12 candidatos       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────┬───────────────┬──────────┬─────────┬────────────┐  │
│  │ Sel │ Nome          │ Título   │ Score   │ Ações      │  │
│  ├─────┼───────────────┼──────────┼─────────┼────────────┤  │
│  │ ☐   │ João Silva    │ Sr Dev   │ 92/100  │ [Preview]  │  │
│  │ ☐   │ Maria Santos  │ Tech Ld  │ 88/100  │ [Preview]  │  │
│  │ ☐   │ Pedro Oliveira│ Sr Dev   │ 85/100  │ [Preview]  │  │
│  └─────┴───────────────┴──────────┴─────────┴────────────┘  │
│                                                             │
│  [Visualização apenas - Sem ações disponíveis]              │
└─────────────────────────────────────────────────────────────┘
```

**NOTA:** Frontend visual existe, mas opera com dados mock em algumas áreas.

---

## 4. BUSCA DE CANDIDATOS (TWO-TIER SEARCH)

### ✅ Implementado
| Feature | Descrição |
|---------|-----------|
| Busca local | PostgreSQL full-text |
| Pearch AI | 800M+ perfis externos |
| AI-powered filters | Ask AI + Find Similar |
| Result merger | Combinação local + externo |

### 🔴 Falta Implementar
| Feature | Descrição | Prioridade | Complexidade |
|---------|-----------|------------|--------------|
| Controle de créditos | Limites por plano | P1 | Média |
| Enriquecimento de perfil | LinkedIn, GitHub, email lookup | P2 | Alta |

---

## 5. SISTEMA DE TESTES (ASSESSMENTS)

### ✅ Implementado
| Feature | Descrição |
|---------|-----------|
| Schema no banco | Tabelas de testes técnicos criadas |
| Configuração por cliente | Testes customizáveis por tenant |

### 🔴 Falta Implementar
| Feature | Descrição | Prioridade | Complexidade |
|---------|-----------|------------|--------------|
| **Geração automática com IA** | LIA gera testes baseados em requisitos da vaga | P0 | Alta |
| **Banco de testes por perfil** | Templates de testes por cargo/função | P1 | Média |
| **Banco de testes por arquétipo** | Testes agrupados por arquétipo comportamental | P1 | Média |
| **Teste Técnico** | Avaliação de conhecimentos específicos da área | P0 | Alta |
| **Teste de Inglês** | Avaliação de proficiência em inglês (leitura, escrita, áudio) | P1 | Alta |
| **Teste de Lógica/Raciocínio** | Avaliação de raciocínio lógico e analítico | P1 | Média |
| **Correção automática** | IA corrige e pontua respostas | P1 | Alta |
| **Relatório de resultados** | Dashboard com performance do candidato | P1 | Média |
| **🆕 Teste Big Five (Personalidade)** | Avaliação de traços de personalidade com 50/100/120+ perguntas | P0 | Média |

### 🆕 NOVA FEATURE: Teste Big Five para Recrutamento

**Descrição:** Implementação de teste de personalidade baseado no modelo Big Five (OCEAN) para uso em processos seletivos. Utiliza bibliotecas open source validadas cientificamente.

**Modelo Big Five (OCEAN):**
| Dimensão | Sigla | Descrição | Traços Altos | Traços Baixos |
|----------|-------|-----------|--------------|---------------|
| **Openness** | O | Abertura a experiências | Criativo, curioso, inovador | Prático, convencional |
| **Conscientiousness** | C | Conscienciosidade | Organizado, disciplinado | Flexível, espontâneo |
| **Extraversion** | E | Extroversão | Sociável, assertivo, energético | Reservado, introspectivo |
| **Agreeableness** | A | Amabilidade | Cooperativo, empático | Competitivo, direto |
| **Neuroticism** | N | Neuroticismo | Sensível, reativo | Estável, calmo |

**Versões do Teste:**
| Versão | Perguntas | Tempo | Precisão | Uso Recomendado |
|--------|-----------|-------|----------|-----------------|
| **Mini** | 50 | 10 min | Boa | Triagem inicial rápida |
| **Standard** | 100 | 20 min | Alta | Processo seletivo padrão |
| **Full** | 120+ | 30 min | Muito Alta | Posições de liderança/críticas |

**Bibliotecas Open Source (GitHub):**
| Biblioteca | Linguagem | Perguntas | Licença | URL |
|------------|-----------|-----------|---------|-----|
| **IPIP-NEO** | Multi | 120/300 | Public Domain | ipip.ori.org |
| **Big Five Inventory (BFI)** | Multi | 44 | Academic | berkeley.edu |
| **Big Five Aspect Scales** | Multi | 100 | Open | deYoung & Peterson |
| **python-bigfive** | Python | 50-120 | MIT | GitHub |
| **personality-insights** | JS | 100 | Apache 2.0 | GitHub |

**Mapeamento para Arquétipos:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│  MAPEAMENTO BIG FIVE → ARQUÉTIPOS DE TRABALHO                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  🎯 EXECUTOR (Alto desempenho, resultados)                             │
│  └── Alto C (Conscienciosidade) + Baixo N (Estabilidade)               │
│                                                                         │
│  🧠 ESTRATÉGICO (Visão, planejamento)                                  │
│  └── Alto O (Abertura) + Alto C (Conscienciosidade)                    │
│                                                                         │
│  🤝 COLABORADOR (Trabalho em equipe)                                   │
│  └── Alto A (Amabilidade) + Alto E (Extroversão)                       │
│                                                                         │
│  💡 INOVADOR (Criatividade, disrupção)                                 │
│  └── Alto O (Abertura) + Baixo C (Flexibilidade)                       │
│                                                                         │
│  👔 LÍDER (Gestão de pessoas)                                          │
│  └── Alto E (Extroversão) + Alto C + Baixo N                           │
│                                                                         │
│  🔬 ANALÍTICO (Dados, precisão)                                        │
│  └── Alto C (Conscienciosidade) + Baixo E (Introversão)                │
└─────────────────────────────────────────────────────────────────────────┘
```

**Fluxo de Aplicação:**
```
┌────────────────┐    ┌────────────────┐    ┌────────────────┐
│ Candidato      │───▶│ Responde       │───▶│ Sistema        │
│ Recebe Link    │    │ 50-120 questões│    │ Calcula Scores │
└────────────────┘    └────────────────┘    └────────────────┘
                                                    │
                                                    ▼
┌────────────────┐    ┌────────────────┐    ┌────────────────┐
│ Relatório      │◀───│ Mapeia para    │◀───│ Identifica     │
│ Final          │    │ Arquétipo      │    │ Traços OCEAN   │
└────────────────┘    └────────────────┘    └────────────────┘
```

**Relatório Big Five:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│  RELATÓRIO DE PERSONALIDADE - João Silva                                │
│  Teste: Big Five Standard (100 questões) | Data: 20/12/2025            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  SCORES OCEAN                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ O - Abertura          ████████████████████░░░░░  78%            │   │
│  │ C - Conscienciosidade ██████████████████████████  92%           │   │
│  │ E - Extroversão       ██████████████░░░░░░░░░░░  55%            │   │
│  │ A - Amabilidade       ███████████████████░░░░░░  72%            │   │
│  │ N - Neuroticismo      ██████░░░░░░░░░░░░░░░░░░░  25%            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ARQUÉTIPO IDENTIFICADO: 🎯 EXECUTOR + 🧠 ESTRATÉGICO                  │
│                                                                         │
│  PONTOS FORTES:                                                        │
│  • Alta capacidade de organização e planejamento                       │
│  • Estabilidade emocional acima da média                               │
│  • Abertura para novas ideias e aprendizado                            │
│                                                                         │
│  PONTOS DE ATENÇÃO:                                                    │
│  • Pode ter dificuldade em ambientes muito caóticos                    │
│  • Extroversão moderada - avaliar fit com posições de alta exposição   │
│                                                                         │
│  FIT COM A VAGA: 87% (Desenvolvedor Sênior)                            │
└─────────────────────────────────────────────────────────────────────────┘
```

**Integração com LIA Score:**
- Resultado Big Five compõe 20% do LIA Score final
- Validação cruzada com análise de entrevista WSI
- Red flags se grande discrepância entre Big Five e comportamento na entrevista

### 🆕 NOVA FEATURE: Sistema de Testes com IA

**Descrição:** Sistema completo de assessments técnicos, comportamentais e de idiomas com geração automática de questões por IA e banco de testes organizados por perfil, função ou arquétipo.

**Tipos de Testes:**
| Tipo | Descrição | Formato |
|------|-----------|---------|
| **Técnico** | Conhecimentos específicos (programação, finanças, vendas, etc) | Múltipla escolha + Código + Dissertativo |
| **Inglês** | Reading, Writing, Listening | Múltipla escolha + Áudio + Escrita |
| **Lógica/Raciocínio** | Sequências, padrões, análise de dados | Múltipla escolha + Problemas |
| **Comportamental** | Big Five, valores, cultura fit | Escala Likert + Situacional |

**Banco de Testes:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│  BANCO DE TESTES                                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  📁 Por Perfil/Cargo                                                   │
│  ├── Desenvolvedor Backend                                             │
│  │   ├── Python Fundamentals (30 questões)                            │
│  │   ├── SQL Avançado (25 questões)                                   │
│  │   └── APIs REST (20 questões)                                      │
│  ├── Analista de Dados                                                 │
│  │   ├── Python para Data Science (30 questões)                       │
│  │   ├── SQL Analytics (25 questões)                                  │
│  │   └── Estatística Básica (20 questões)                             │
│  └── Product Manager                                                   │
│      ├── Métricas de Produto (25 questões)                            │
│      └── Priorização e Discovery (20 questões)                        │
│                                                                         │
│  📁 Por Arquétipo                                                      │
│  ├── Executor (foco em resultados)                                     │
│  ├── Estratégico (visão de longo prazo)                               │
│  ├── Colaborador (trabalho em equipe)                                  │
│  └── Inovador (criatividade)                                           │
│                                                                         │
│  📁 Por Idioma                                                         │
│  ├── Inglês A1-A2 (básico)                                            │
│  ├── Inglês B1-B2 (intermediário)                                     │
│  └── Inglês C1-C2 (avançado/fluente)                                  │
│                                                                         │
│  🤖 Geração com IA                                                     │
│  └── [Gerar novo teste baseado na descrição da vaga]                  │
└─────────────────────────────────────────────────────────────────────────┘
```

**Fluxo de Geração Automática:**
```
┌────────────────┐    ┌────────────────┐    ┌────────────────┐
│ Requisitos     │───▶│ LIA Analisa    │───▶│ Gera Questões  │
│ da Vaga        │    │ Skills/Nível   │    │ Personalizadas │
└────────────────┘    └────────────────┘    └────────────────┘
                                                    │
                                                    ▼
┌────────────────┐    ┌────────────────┐    ┌────────────────┐
│ Relatório      │◀───│ IA Corrige     │◀───│ Candidato      │
│ de Resultados  │    │ e Pontua       │    │ Responde       │
└────────────────┘    └────────────────┘    └────────────────┘
```

**Integração com WSI:**
- Testes podem ser aplicados antes ou depois da triagem por voz
- Resultados combinados no LIA Score final
- Red flags automáticos se discrepância entre entrevista e teste

---

## 6. WSI - VOICE SCREENING

### ✅ Implementado
| Feature | Descrição |
|---------|-----------|
| Schema completo | 10 tabelas WSI no banco |
| Voice tests básicos | Deepgram STT funcional |

### 🔴 Falta Implementar
| Feature | Descrição | Prioridade | Complexidade |
|---------|-----------|------------|--------------|
| Entrevista por voz automatizada | Ligação com IA conversacional | P0 | Muito Alta |
| OpenMic.ai integração real | Chamadas telefônicas | P1 | Alta |
| Análise Big Five | Traços de personalidade | P1 | Alta |
| Red flags automáticos | Detecção de inconsistências | P1 | Alta |
| Scoring preditivo | ML para probabilidade de sucesso | P2 | Muito Alta |
| Relatório WSI completo | PDF com análise detalhada | P1 | Média |

**NOTA:** WSI é diferencial competitivo chave, mas está majoritariamente não implementado.

---

## 6. AGENDAMENTO DE ENTREVISTAS

### ✅ Implementado
| Feature | Descrição |
|---------|-----------|
| Schema no banco | Tabelas criadas |

### 🔴 Falta Implementar
| Feature | Descrição | Prioridade | Complexidade |
|---------|-----------|------------|--------------|
| Microsoft Graph | Integração calendário | P1 | Alta |
| Verificação de disponibilidade | Automática | P1 | Média |
| Criação de eventos | Google Meet / Teams | P1 | Alta |
| Lembretes | Email + WhatsApp | P1 | Média |

**NOTA:** Módulo inteiro não implementado, apenas schema.

---

## 7. COMUNICAÇÃO OMNICHANNEL

### ✅ Implementado
| Feature | Descrição |
|---------|-----------|
| Chat in-app | Conversas com LIA |

### 🔴 Falta Implementar
| Feature | Descrição | Prioridade | Complexidade |
|---------|-----------|------------|--------------|
| Email (SendGrid/Resend) | Envio de emails transacionais | P0 | Média |
| WhatsApp Business API | Mensagens via Twilio | P0 | Alta |
| Microsoft Teams | Notificações e mensagens | P1 | Alta |
| SMS | Via Twilio | P2 | Baixa |

**NOTA:** Omnichannel é crítico para experiência do candidato.

---

## 8. DASHBOARDS & ANALYTICS

### ✅ Implementado
| Feature | Descrição |
|---------|-----------|
| Dashboard visual | KPIs básicos |
| Métricas SaaS Admin | MRR, ARR, churn (WeDo Admin) |

### 🔴 Falta Implementar
| Feature | Descrição | Prioridade | Complexidade |
|---------|-----------|------------|--------------|
| Time-to-fill | Tempo médio para preencher vaga | P1 | Média |
| LIA Score médio | Qualidade dos candidatos | P1 | Média |
| Candidatos/recrutador | Produtividade | P1 | Baixa |
| Cost-per-hire | Custo por contratação | P2 | Média |
| D&I metrics | Diversidade e inclusão | P2 | Média |

---

## 9. ARQUITETURA MULTI-AGENT

### ✅ Implementado
| Feature | Descrição |
|---------|-----------|
| Orchestrator | Roteamento de intents |
| 10 agentes especializados | Base implementada |
| LangGraph | Framework de orquestração |
| LangSmith | Tracing ativo |

### 🔴 Falta Implementar
| Feature | Descrição | Prioridade | Complexidade |
|---------|-----------|------------|--------------|
| Job Intake Agent completo | Criação de vagas via chat | P0 | Alta |
| Screening Agent completo | Triagem automatizada WSI | P0 | Muito Alta |
| Scheduling Agent completo | Agendamento inteligente | P1 | Alta |
| Communication Agent completo | Omnichannel integrado | P1 | Alta |
| Task Planner | Decomposição de tarefas | P2 | Alta |
| Policy Engine | Regras de negócio | P2 | Alta |

---

## 10. INTEGRAÇÕES EXTERNAS

### ✅ Implementado
| Integração | Status |
|------------|--------|
| Anthropic Claude | ✅ Funcional |
| Google Gemini | ✅ Funcional |
| Deepgram STT | ✅ Funcional |
| Pearch AI | ✅ Funcional |
| ATS (Gupy, Pandapé, StackOne) | ✅ Código implementado |

### 🔴 Falta Implementar
| Integração | Descrição | Prioridade | Complexidade |
|------------|-----------|------------|--------------|
| WhatsApp Business API | Twilio integration | P0 | Alta |
| SendGrid/Resend | Email transacional | P0 | Média |
| Microsoft Graph Calendar | Agendamento | P1 | Alta |
| Microsoft Teams | Chat e notificações | P1 | Alta |
| LinkedIn API | Enriquecimento de perfis | P2 | Alta |
| OpenMic.ai (produção) | Chamadas reais | P1 | Alta |
| Billing (Stripe/Pagar.me) | Cobrança real | P1 | Alta |

---

## 11. WEDO ADMIN (COMPLIANCE) ✅ 100% COMPLETO

| Feature | Status |
|---------|--------|
| Health Check 242 itens | ✅ |
| LGPD Portal do Titular | ✅ |
| Consent Management | ✅ |
| BCB 498/2025 Cyber Insurance | ✅ |
| Risk Register | ✅ |
| SoD Matrix | ✅ |
| Business Continuity | ✅ |
| Bias Audit System | ✅ |
| Control Library | ✅ |
| Trust Center | ✅ |
| Audit Trail SOX | ✅ |
| Default Templates | ✅ |
| Global Policies | ✅ |
| Technical Tests | ✅ |
| SaaS Metrics | ✅ |

---

## 12. COMPLIANCE & PRIVACIDADE - INTERFACE DO CANDIDATO 🆕

**Status Geral:** 🔴 Majoritariamente não implementado

### ✅ Implementado (Backend/Admin)
| Feature | Descrição |
|---------|-----------|
| Portal do Titular LGPD (Admin) | Dashboard para gestão de requisições |
| Consent Management API | APIs para gerenciar consentimentos |
| Bias Audit System (Admin) | Relatórios de viés para compliance |

### 🔴 Falta Implementar - Interface do Candidato
| Feature | Descrição | Regulamentação | Prioridade | Complexidade |
|---------|-----------|----------------|------------|--------------|
| **Portal do Candidato** | UI para candidato gerenciar seus dados | LGPD Art. 18 | P0 | Alta |
| **Consentimento via WhatsApp** | Opt-in/out por WhatsApp com log | LGPD Art. 8 | P0 | Média |
| **Consentimento por Email** | Double opt-in com link de confirmação | LGPD Art. 8 | P0 | Média |
| **Controle de Dados (UI)** | Candidato visualiza todos seus dados | LGPD Art. 18-II | P0 | Alta |
| **Solicitação de Exclusão (UI)** | Candidato solicita exclusão de dados | LGPD Art. 18-VI | P0 | Média |
| **Solicitação de Portabilidade (UI)** | Candidato exporta seus dados | LGPD Art. 18-V | P1 | Média |
| **Explicação de Decisão AI (UI)** | Candidato entende como foi avaliado | EU AI Act / LGPD Art. 20 | P0 | Alta |
| **Solicitação de Revisão Humana** | Candidato pede revisão por humano | EU AI Act Art. 14 | P0 | Média |
| **Consentimento Granular** | Aceitar/recusar cada tipo de uso | LGPD Art. 8 | P1 | Média |
| **Histórico de Consentimentos** | Candidato vê todo histórico | LGPD Art. 18-VII | P1 | Baixa |
| **Notificação de Violação** | Alertar candidato em caso de breach | LGPD Art. 48 | P1 | Média |
| **Preferências de Comunicação** | Escolher canais e frequência | LGPD | P1 | Baixa |

### 🆕 Portal do Candidato - Especificação Detalhada

**Descrição:** Interface web/mobile onde o candidato pode gerenciar seus dados pessoais, consentimentos e entender como a IA avaliou seu perfil.

**Acesso:**
- URL pública: `/meus-dados` ou `/candidato/privacidade`
- Autenticação por email (magic link) ou código SMS
- Sem necessidade de criar conta

**Telas do Portal:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│  MEU PORTAL DE PRIVACIDADE - WeDo Talent                                │
│  Olá, João Silva | joao@email.com                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 📋 MEUS DADOS                                                   │   │
│  │                                                                 │   │
│  │ Nome: João Silva                                                │   │
│  │ Email: joao@email.com                                           │   │
│  │ Telefone: (11) 99999-9999                                       │   │
│  │ CV enviado: curriculum_joao.pdf                                 │   │
│  │ Último acesso: 20/12/2025                                       │   │
│  │                                                                 │   │
│  │ [📥 Baixar Todos Meus Dados] [✏️ Corrigir Dados]               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 🤖 DECISÕES AUTOMATIZADAS (EU AI Act / LGPD Art. 20)           │   │
│  │                                                                 │   │
│  │ Vaga: Desenvolvedor Python Sênior                               │   │
│  │ LIA Score: 85/100                                               │   │
│  │                                                                 │   │
│  │ Como você foi avaliado:                                         │   │
│  │ ├── Experiência (8 anos) ..................... +25 pontos       │   │
│  │ ├── Skills (Python, Django) .................. +30 pontos       │   │
│  │ ├── Formação (Ciência da Computação) ......... +15 pontos       │   │
│  │ ├── Entrevista WSI ........................... +10 pontos       │   │
│  │ └── Big Five (perfil executor) ............... +5 pontos        │   │
│  │                                                                 │   │
│  │ [🧑 Solicitar Revisão Humana]                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ ✅ MEUS CONSENTIMENTOS                                          │   │
│  │                                                                 │   │
│  │ ☑️ Receber vagas por email ............. [Ativo desde 01/12/25]│   │
│  │ ☑️ Receber vagas por WhatsApp .......... [Ativo desde 01/12/25]│   │
│  │ ☐ Compartilhar perfil com parceiros .... [Não autorizado]      │   │
│  │ ☑️ Análise por IA ...................... [Ativo desde 01/12/25]│   │
│  │ ☑️ Armazenar CV por 2 anos ............. [Ativo desde 01/12/25]│   │
│  │                                                                 │   │
│  │ [📜 Ver Histórico de Consentimentos]                            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 🗑️ EXCLUSÃO DE DADOS                                           │   │
│  │                                                                 │   │
│  │ Você pode solicitar a exclusão de todos os seus dados.          │   │
│  │ Esta ação é irreversível e será processada em até 15 dias.      │   │
│  │                                                                 │   │
│  │ [🗑️ Solicitar Exclusão de Dados]                               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 🆕 Consentimento via WhatsApp

**Fluxo de Opt-in:**
```
┌────────────────────────────────────────────────────────────────────────┐
│ WhatsApp - WeDo Talent                                                 │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  🤖 WeDo Talent (10:30)                                               │
│  ┌─────────────────────────────────────────────────────────┐          │
│  │ Olá João! Obrigado pelo interesse na vaga de            │          │
│  │ Desenvolvedor Python na TechCorp.                       │          │
│  │                                                         │          │
│  │ Para continuar no processo, precisamos do seu           │          │
│  │ consentimento para:                                     │          │
│  │                                                         │          │
│  │ 1️⃣ Analisar seu currículo com IA                        │          │
│  │ 2️⃣ Enviar atualizações do processo por WhatsApp         │          │
│  │ 3️⃣ Armazenar seus dados por até 2 anos                  │          │
│  │                                                         │          │
│  │ Responda com:                                           │          │
│  │ ✅ ACEITO - para concordar com todos                    │          │
│  │ 📋 DETALHES - para ver a política completa              │          │
│  │ ❌ RECUSO - para não participar                         │          │
│  └─────────────────────────────────────────────────────────┘          │
│                                                                        │
│  👤 João (10:32)                                                      │
│  ┌─────────────────────────────────────────────────────────┐          │
│  │ ACEITO                                                  │          │
│  └─────────────────────────────────────────────────────────┘          │
│                                                                        │
│  🤖 WeDo Talent (10:32)                                               │
│  ┌─────────────────────────────────────────────────────────┐          │
│  │ ✅ Consentimento registrado!                            │          │
│  │ Código: CONS-2025-12345                                 │          │
│  │ Data: 20/12/2025 10:32                                  │          │
│  │                                                         │          │
│  │ Você pode revogar a qualquer momento respondendo        │          │
│  │ REVOGAR ou acessando: wedotalent.com/meus-dados        │          │
│  └─────────────────────────────────────────────────────────┘          │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### 🆕 Explicabilidade de Decisão AI (EU AI Act)

**Requisito Legal:** Art. 13 e 14 do EU AI Act exigem transparência em sistemas de IA de alto risco (recrutamento é classificado como alto risco).

**O que deve ser explicado:**
| Elemento | Descrição | Status |
|----------|-----------|--------|
| Fatores considerados | Quais dados influenciaram a decisão | 🔴 |
| Peso de cada fator | Quanto cada elemento contribuiu | 🔴 |
| Limites de corte | Score mínimo para aprovação | 🔴 |
| Comparação com outros | Posição relativa (sem identificar) | 🔴 |
| Dados não utilizados | O que NÃO foi considerado | 🔴 |
| Opção de revisão humana | Como solicitar | 🔴 |

### 🆕 Requisitos por Regulamentação

#### LGPD (Brasil)
| Artigo | Requisito | Interface Candidato | Status |
|--------|-----------|---------------------|--------|
| Art. 7 | Base legal para tratamento | Informar base legal usada | 🔴 |
| Art. 8 | Consentimento específico | Checkboxes granulares | 🔴 |
| Art. 9 | Dados sensíveis | Consentimento destacado | 🔴 |
| Art. 18-I | Confirmação de tratamento | Visualizar se tem dados | 🔴 |
| Art. 18-II | Acesso aos dados | Tela "Meus Dados" | 🔴 |
| Art. 18-III | Correção de dados | Formulário de correção | 🔴 |
| Art. 18-IV | Anonimização/bloqueio | Opção de anonimizar | 🔴 |
| Art. 18-V | Portabilidade | Export JSON/PDF | 🔴 |
| Art. 18-VI | Eliminação | Botão "Excluir meus dados" | 🔴 |
| Art. 18-VII | Info sobre compartilhamento | Lista de quem tem acesso | 🔴 |
| Art. 18-VIII | Revogar consentimento | Toggles para cada uso | 🔴 |
| Art. 20 | Revisão de decisão automatizada | Botão "Revisão humana" | 🔴 |

#### EU AI Act (União Europeia)
| Artigo | Requisito | Interface Candidato | Status |
|--------|-----------|---------------------|--------|
| Art. 13 | Transparência | Explicar que usa IA | 🔴 |
| Art. 14 | Supervisão humana | Acesso a revisor humano | 🔴 |
| Art. 26 | Informar sobre IA | Aviso claro no início | 🔴 |
| Art. 50 | Documentação | Logs de decisão acessíveis | 🔴 |
| Anexo III | Alto risco (recrutamento) | Conformidade total | 🔴 |

#### SOC 2 Type II
| Critério | Requisito | Interface Candidato | Status |
|----------|-----------|---------------------|--------|
| CC6.1 | Acesso lógico | Portal seguro | 🔴 |
| CC7.2 | Monitoramento | Logs de acesso | ✅ Backend |
| PI1.1 | Privacidade | Política acessível | 🔴 |

#### SOX (Sarbanes-Oxley)
| Seção | Requisito | Interface Candidato | Status |
|-------|-----------|---------------------|--------|
| 302 | Controles internos | Audit trail visível | ✅ Backend |
| 404 | Documentação | Histórico de ações | ✅ Backend |

#### NYC LL144 (Local Law 144)
| Requisito | Descrição | Interface Candidato | Status |
|-----------|-----------|---------------------|--------|
| Aviso de AEDT | Informar uso de AI em recrutamento | Banner de aviso | 🔴 |
| Bias Audit Summary | Resumo de auditoria de viés | Link para relatório público | 🔴 |
| Opt-out | Opção de processo sem IA | Checkbox de recusa | 🔴 |

### 🆕 Fluxo Completo de Compliance do Candidato

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    JORNADA DE COMPLIANCE DO CANDIDATO                       │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────┐
    │ Candidato   │
    │ se aplica   │
    └──────┬──────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. AVISO INICIAL (EU AI Act Art. 26 / NYC LL144)                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ⚠️ Este processo utiliza Inteligência Artificial para              │   │
│  │ auxiliar na análise de candidatos. Você tem direito a:             │   │
│  │ • Entender como a IA avalia seu perfil                             │   │
│  │ • Solicitar revisão por um humano                                  │   │
│  │ • Optar por processo sem IA                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  2. CONSENTIMENTO GRANULAR (LGPD Art. 8)                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ☑️ Autorizo análise do meu currículo (obrigatório)                 │   │
│  │ ☑️ Autorizo avaliação por IA                                       │   │
│  │ ☐ Autorizo contato por WhatsApp                                    │   │
│  │ ☐ Autorizo armazenamento por 2 anos para outras vagas              │   │
│  │ ☐ Autorizo compartilhamento com empresas parceiras                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  3. PROCESSO SELETIVO (com transparência)                                  │
│                                                                             │
│  • Cada etapa informa se usa IA                                            │
│  • Candidato pode ver seu progresso                                        │
│  • Notificações por canal escolhido                                        │
└─────────────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  4. RESULTADO COM EXPLICAÇÃO (LGPD Art. 20 / EU AI Act Art. 13)            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Resultado: Não aprovado para esta vaga                             │   │
│  │                                                                     │   │
│  │ Motivo principal: Experiência abaixo do requisito (3 anos vs 5)    │   │
│  │                                                                     │   │
│  │ [🧑 Solicitar Revisão Humana] [📄 Ver Análise Completa]            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  5. PÓS-PROCESSO (Portal do Candidato)                                     │
│                                                                             │
│  • Acessar/baixar dados a qualquer momento                                 │
│  • Atualizar consentimentos                                                │
│  • Solicitar exclusão                                                      │
│  • Ver histórico de processos                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# PRIORIZAÇÃO RECOMENDADA

## P0 - Crítico (Bloqueador de negócio)
1. Email (SendGrid/Resend)
2. WhatsApp Business API
3. Bulk actions no funil
4. Conectar funil ao backend real
5. Criação de vagas via chat
6. **🆕 Shortlist Interativa para Gestores**
7. **🆕 Compartilhar Resultado de Busca**
8. **🆕 Teste Técnico com geração IA**
9. **🆕 Teste Big Five (Personalidade)**
10. **🆕 Portal do Candidato (LGPD/EU AI Act)**
11. **🆕 Consentimento via WhatsApp**
12. **🆕 Explicação de Decisão AI (UI)**
13. **🆕 Solicitação de Revisão Humana**

## P1 - Alta Prioridade
14. Microsoft Graph Calendar
15. Importação CSV/Excel de candidatos
16. Parsing de CV automático
17. Exportação PDF/CSV
18. WSI Full Interview
19. OpenMic.ai produção
20. Relatório WSI
21. **🆕 Teste de Inglês (Reading/Writing/Listening)**
22. **🆕 Teste de Lógica/Raciocínio**
23. **🆕 Banco de testes por perfil/arquétipo**
24. **🆕 Correção automática de testes**
25. **🆕 Consentimento Granular (LGPD)**
26. **🆕 Portabilidade de Dados (UI)**
27. **🆕 Histórico de Consentimentos (UI)**

## P2 - Média Prioridade
28. Detecção de duplicados
29. Publicação multi-canal de vagas
30. LinkedIn enriquecimento
31. D&I metrics
32. SMS via Twilio
33. **🆕 Preferências de Comunicação (UI)**
34. **🆕 Notificação de Violação de Dados**

---

# 🆕 FEATURES DE COLABORAÇÃO (NOVAS)

Duas novas funcionalidades identificadas para melhorar a colaboração entre recrutadores e gestores:

| Feature | Módulo | Descrição | Impacto |
|---------|--------|-----------|---------|
| **Compartilhar Resultado de Busca** | Funil | Gerar URL com tabela + preview para gestores | Alto |
| **Shortlist Interativa** | Vagas | URL interativa com comentários e solicitação de entrevistas | Muito Alto |

**Benefícios:**
- Agiliza decisões de contratação
- Reduz emails e reuniões de alinhamento
- Gestores podem avaliar candidatos de qualquer lugar
- Histórico centralizado de feedback
- Integração direta com agendamento de entrevistas

---

# ESTIMATIVA REVISADA

Com base nesta análise detalhada:

| Métrica | Valor |
|---------|-------|
| Total de features planejadas | 119 |
| Features implementadas | 47 |
| Features faltando | 72 |
| **% Real de Implementação** | **39%** |

**Notas:**
- O compliance WeDo Admin (backend) está 100% completo
- A interface do candidato para compliance está apenas 20% (faltam UI de LGPD, EU AI Act, consentimentos)
- Os módulos core de recrutamento (vagas, agendamento, WSI, comunicação) estão entre 0-25%
