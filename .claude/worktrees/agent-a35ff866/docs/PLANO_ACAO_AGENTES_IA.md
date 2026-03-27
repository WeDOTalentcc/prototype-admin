# Plano de Ação - Resolução de Gaps dos Agentes de IA
**Data:** Janeiro 2026  
**Objetivo:** Completar implementação do sistema multi-agent LIA para MVP

---

## 📋 Resumo Executivo

| Fase | Duração | Foco Principal |
|------|---------|----------------|
| **Fase 1** | 2 semanas | Correções críticas e estabilização |
| **Fase 2** | 3 semanas | Completar funcionalidades core |
| **Fase 3** | 4 semanas | Integrações externas e polish |
| **Fase 4** | Contínuo | Treinamento e otimização |

**Esforço Total Estimado:** 9-10 semanas para MVP funcional

---

## 🔴 FASE 1: CORREÇÕES CRÍTICAS (Semanas 1-2)

### 1.1 Corrigir Erros LSP do JobIntakeAgent
**Prioridade:** Crítica  
**Esforço:** 2-3 dias  
**Bloqueador:** Impede desenvolvimento estável

**Tarefas:**
- [ ] Executar `get_latest_lsp_diagnostics` e listar todos os 51 erros
- [ ] Corrigir imports faltantes/incorretos
- [ ] Resolver tipos incompatíveis
- [ ] Corrigir referências a métodos inexistentes
- [ ] Validar que o agente inicializa sem erros

**Arquivo Principal:** `lia-agent-system/app/agents/specialized/job_intake_agent.py`

**Critério de Sucesso:** 0 erros LSP, agente inicializa corretamente

---

### 1.2 Corrigir Erro LSP do SourcingAgent
**Prioridade:** Alta  
**Esforço:** 1 dia

**Tarefas:**
- [ ] Verificar e corrigir o erro LSP identificado
- [ ] Validar inicialização do agente

**Arquivo Principal:** `lia-agent-system/app/agents/specialized/sourcing_agent.py`

---

### 1.3 Implementar CompanyConfigurationService
**Prioridade:** Crítica  
**Esforço:** 3-4 dias  
**Bloqueador:** JobIntakeAgent usa heurísticas estáticas

**Tarefas:**
- [ ] Criar `lia-agent-system/app/services/company_configuration_service.py`
- [ ] Mapear endpoints existentes:
  - `CompanyProfile` (nome, missão, valores)
  - `Department` (áreas/departamentos)
  - `Benefit` (lista de benefícios)
  - `RecruitmentJourney` (pipeline padrão)
  - `ScreeningQuestion` (perguntas padrão)
- [ ] Implementar cache em memória (TTL 5 min)
- [ ] Criar método `load_job_creation_context(company_id)`
- [ ] Implementar fallbacks para dados ausentes
- [ ] Integrar no JobIntakeAgent como "Etapa 0" invisível

**Estrutura do Contexto:**
```python
@dataclass
class JobCreationContext:
    company_name: str
    company_mission: Optional[str]
    company_values: Optional[str]
    departments: List[Department]
    benefits: List[Benefit]
    pipeline_template: Optional[RecruitmentJourney]
    default_screening_questions: List[ScreeningQuestion]
    organizational_structure: Optional[Dict]
```

**Critério de Sucesso:** Wizard de criação de vagas pré-carrega dados da empresa

---

### 1.4 Criar Suite de Testes Básica
**Prioridade:** Alta  
**Esforço:** 2-3 dias

**Tarefas:**
- [ ] Criar estrutura de testes: `lia-agent-system/tests/agents/`
- [ ] Criar `test_base_agent.py` - testa BaseAgent
- [ ] Criar `test_job_intake_agent.py` - testa JobIntakeAgent
- [ ] Criar `test_sourcing_agent.py` - testa SourcingAgent
- [ ] Criar `test_wsi_evaluator_agent.py` - testa AvaliadorWSI
- [ ] Criar `test_intent_router.py` - testa roteamento
- [ ] Configurar pytest no `pyproject.toml`
- [ ] Adicionar fixtures compartilhadas

**Cobertura Mínima:** 
- Inicialização de cada agente
- Registro de ações
- Processamento de intent básico

---

## 🟠 FASE 2: FUNCIONALIDADES CORE (Semanas 3-5)

### 2.1 Completar WSI Evaluator Agent
**Prioridade:** Crítica  
**Esforço:** 5-7 dias  
**Bloqueador:** Core diferenciador da WeDOTalent

**Tarefas:**

#### 2.1.1 Implementar Bloom Taxonomy Classification
- [ ] Criar `apply_bloom_taxonomy()` completo
- [ ] Definir critérios para cada nível:
  - Remember (Lembrar) - Nível 1
  - Understand (Compreender) - Nível 2
  - Apply (Aplicar) - Nível 3
  - Analyze (Analisar) - Nível 4
  - Evaluate (Avaliar) - Nível 5
  - Create (Criar) - Nível 6
- [ ] Criar prompts específicos para classificação
- [ ] Implementar scoring baseado em resposta do LLM

#### 2.1.2 Implementar Dreyfus Model Classification
- [ ] Criar `apply_dreyfus_model()` completo
- [ ] Definir critérios para cada estágio:
  - Novice (Novato) - 1
  - Advanced Beginner (Iniciante Avançado) - 2
  - Competent (Competente) - 3
  - Proficient (Proficiente) - 4
  - Expert (Especialista) - 5
- [ ] Criar prompts para avaliação de proficiência
- [ ] Mapear indicadores comportamentais

#### 2.1.3 Implementar Big Five Mapping
- [ ] Criar `map_big_five()` completo
- [ ] Implementar detecção de traços:
  - Openness (Abertura a experiências)
  - Conscientiousness (Conscienciosidade)
  - Extraversion (Extroversão)
  - Agreeableness (Amabilidade)
  - Neuroticism (Neuroticismo)
- [ ] Criar prompt para análise comportamental
- [ ] Gerar perfil normalizado (0-100 por traço)

#### 2.1.4 Implementar Fórmula WSI Final
- [ ] Criar `calculate_wsi_score()` com pesos:
  ```python
  WSI_SCORE = (
      bloom_score * 0.25 +      # Complexidade cognitiva
      dreyfus_score * 0.35 +    # Nível de expertise
      big_five_fit * 0.15 +     # Adequação comportamental
      rubric_score * 0.25       # Aderência aos requisitos
  )
  ```
- [ ] Normalizar para escala 0-100
- [ ] Adicionar confidence score

#### 2.1.5 Gerar Parecer Automático
- [ ] Criar `generate_parecer()` 
- [ ] Template estruturado:
  - Resumo executivo (2-3 frases)
  - Pontos fortes identificados
  - Áreas de desenvolvimento
  - Adequação à vaga (%)
  - Recomendação (Aprovar/Reprovar/Avaliar mais)
- [ ] Suporte a múltiplos idiomas (PT/EN)

**Arquivo Principal:** `lia-agent-system/app/agents/specialized/avaliador_wsi_agent.py`

**Critério de Sucesso:** 
- WSI score calculado para qualquer candidato
- Parecer gerado automaticamente
- Testes passando

---

### 2.2 Completar Wire do Wizard Step-by-Step
**Prioridade:** Alta  
**Esforço:** 3-4 dias

**Tarefas:**
- [ ] Identificar e remover dispatch path legado
- [ ] Garantir fluxo sequencial das 8 etapas:
  1. Detecção de critérios (LIA analisa input)
  2. Informações básicas (título, área, gestor)
  3. Requisitos técnicos (skills, experiência)
  4. Competências comportamentais
  5. Salário e benefícios (pre-populated)
  6. Perguntas WSI (geradas por IA)
  7. Configuração do pipeline
  8. Resumo e publicação
- [ ] Implementar navegação bidirecional (voltar/avançar)
- [ ] Persistir estado entre etapas
- [ ] Validação por etapa

---

### 2.3 Implementar Few-Shot Examples nos Prompts
**Prioridade:** Média  
**Esforço:** 2-3 dias

**Tarefas:**
- [ ] Coletar 5-10 exemplos reais de cada tipo de interação
- [ ] Adicionar few-shot examples ao JobIntakeAgent:
  - Exemplo de criação de vaga técnica
  - Exemplo de vaga executiva
  - Exemplo de vaga confidencial
- [ ] Adicionar few-shot examples ao SourcingAgent:
  - Exemplo de busca booleana
  - Exemplo de refinamento de critérios
- [ ] Adicionar few-shot examples ao WSI Evaluator:
  - Exemplo de avaliação completa
  - Exemplo de parecer gerado
- [ ] Documentar formato esperado de resposta

**Arquivo Principal:** `lia-agent-system/app/agents/prompts/agent_prompts.py`

---

### 2.4 Implementar Parsing de CV (PDF/DOCX)
**Prioridade:** Alta  
**Esforço:** 3-4 dias

**Tarefas:**
- [ ] Adicionar dependências: `pypdf2`, `python-docx`, `pytesseract`
- [ ] Criar `lia-agent-system/app/services/cv_parser_service.py`
- [ ] Implementar extração de texto de PDF
- [ ] Implementar extração de texto de DOCX
- [ ] Implementar OCR para PDFs escaneados
- [ ] Integrar com TriagemCurricularAgent
- [ ] Estruturar dados extraídos:
  ```python
  @dataclass
  class ParsedCV:
      raw_text: str
      name: Optional[str]
      email: Optional[str]
      phone: Optional[str]
      education: List[Education]
      experience: List[Experience]
      skills: List[str]
      languages: List[str]
  ```

---

## 🟡 FASE 3: INTEGRAÇÕES EXTERNAS (Semanas 6-9)

### 3.1 Integrar Pearch AI
**Prioridade:** Alta  
**Esforço:** 4-5 dias  
**Dependência:** API key já configurada

**Tarefas:**
- [ ] Estudar documentação da API Pearch
- [ ] Criar `lia-agent-system/app/services/pearch_service.py`
- [ ] Implementar endpoints:
  - `search_candidates(query, filters)` - Busca global
  - `enrich_profile(profile_url)` - Enriquecimento
  - `get_contact_info(profile_id)` - Dados de contato
- [ ] Integrar com SourcingAgent
- [ ] Implementar rate limiting e retry
- [ ] Cache de resultados (Redis ou in-memory)
- [ ] Tratamento de erros e fallback para busca local

**Critério de Sucesso:** Busca retorna candidatos do Pearch AI

---

### 3.2 Completar Microsoft Graph API
**Prioridade:** Alta  
**Esforço:** 3-4 dias  
**Dependência:** Azure credentials configurados

**Tarefas:**
- [ ] Verificar `lia-agent-system/app/services/microsoft_graph_service.py`
- [ ] Implementar funcionalidades faltantes:
  - `get_available_slots(user_id, date_range)` - Horários livres
  - `create_event(event_data)` - Criar evento
  - `send_invite(event_id, attendees)` - Enviar convite
  - `get_meeting_link()` - Link do Teams
- [ ] Integrar com SchedulingAgent
- [ ] Resolver conflitos automáticos
- [ ] Implementar retry para token expirado

---

### 3.3 Implementar WhatsApp Business API
**Prioridade:** Alta  
**Esforço:** 5-7 dias

**Tarefas:**
- [ ] Escolher provider: Meta Cloud API ou Twilio
- [ ] Criar `lia-agent-system/app/services/whatsapp_service.py`
- [ ] Implementar:
  - `send_template_message(to, template, params)` - Templates aprovados
  - `send_text_message(to, text)` - Mensagens livres
  - `receive_webhook(payload)` - Receber mensagens
  - `handle_status_update(status)` - Status de entrega
- [ ] Criar templates de mensagem:
  - Abordagem inicial
  - Confirmação de entrevista
  - Feedback pós-processo
- [ ] Integrar com EntrevistadorAgent
- [ ] Implementar rate limiting

---

### 3.4 Implementar Deepgram Nova-2
**Prioridade:** Média  
**Esforço:** 3-4 dias

**Tarefas:**
- [ ] Adicionar SDK Deepgram
- [ ] Criar `lia-agent-system/app/services/transcription_service.py`
- [ ] Implementar:
  - `transcribe_audio(audio_file)` - Transcrição de arquivo
  - `transcribe_stream(audio_stream)` - Transcrição em tempo real
- [ ] Integrar com EntrevistadorAgent
- [ ] Detectar idioma automaticamente
- [ ] Extrair timestamps por fala

---

### 3.5 Integrar ATSs (Gupy, Pandapé)
**Prioridade:** Média  
**Esforço:** 5-7 dias (por ATS)

**Tarefas Gupy:**
- [ ] Estudar documentação API Gupy
- [ ] Criar `lia-agent-system/app/services/gupy_service.py`
- [ ] Implementar sync bidirecional:
  - Candidatos (WeDOTalent ↔ Gupy)
  - Vagas (WeDOTalent → Gupy)
  - Status (WeDOTalent ↔ Gupy)
- [ ] Webhook para eventos do Gupy
- [ ] Mapeamento de campos

**Tarefas Pandapé:**
- [ ] Estudar documentação API Pandapé
- [ ] Criar `lia-agent-system/app/services/pandape_service.py`
- [ ] Implementar sync similar ao Gupy

---

## ⚪ FASE 4: TREINAMENTO E OTIMIZAÇÃO (Contínuo)

### 4.1 Criar Evaluation Metrics por Agente
**Prioridade:** Média  
**Esforço:** 3-4 dias

**Tarefas:**
- [ ] Criar `lia-agent-system/app/evaluation/` module
- [ ] Definir métricas por agente:

| Agente | Métricas |
|--------|----------|
| Job Planner | field_extraction_accuracy, jd_quality_score, conversation_efficiency |
| Sourcing | search_relevance, candidate_match_rate, response_time |
| CV Screening | parsing_accuracy, red_flag_detection, ranking_consistency |
| WSI Evaluator | score_accuracy, parecer_quality, calibration_drift |
| Scheduling | booking_success_rate, conflict_resolution_rate |

- [ ] Implementar coleta automática
- [ ] Dashboard de métricas

---

### 4.2 Implementar Synthetic Data Generation
**Prioridade:** Baixa (pós-MVP)  
**Esforço:** 1 semana

**Tarefas:**
- [ ] Criar gerador de conversas sintéticas
- [ ] Gerar 20K examples para fine-tuning:
  - Job Intake: 5K examples
  - Sourcing: 5K examples
  - Screening: 3K examples
  - Scheduling: 4K examples
  - Evaluation: 2K examples
  - Communication: 1K examples
- [ ] Validar qualidade com sampling manual

---

### 4.3 Implementar RAG per-Agent
**Prioridade:** Baixa (pós-MVP)  
**Esforço:** 1-2 semanas

**Tarefas:**
- [ ] Escolher vector store (Pinecone, Weaviate, ou pgvector)
- [ ] Criar embeddings para:
  - Vagas anteriores (Job Planner)
  - Perfis de candidatos (Sourcing)
  - Avaliações passadas (WSI Evaluator)
- [ ] Implementar retrieval no contexto do prompt
- [ ] A/B test de qualidade

---

### 4.4 Implementar Calibration Loop
**Prioridade:** Baixa (pós-MVP)  
**Esforço:** 1 semana

**Tarefas:**
- [ ] Criar sistema de feedback do recrutador
- [ ] Thumbs up/down após cada resposta
- [ ] Override de scores WSI
- [ ] Coletar dados de calibração
- [ ] Ajustar thresholds baseado em feedback
- [ ] Retrain periódico

---

### 4.5 Fine-Tuning do Modelo
**Prioridade:** Baixa (pós-MVP)  
**Esforço:** 2-3 semanas

**Tarefas:**
- [ ] Preparar dataset de treinamento (20K examples)
- [ ] Formatar para Claude fine-tuning API
- [ ] Submeter para treinamento
- [ ] Avaliar modelo fine-tuned vs. base
- [ ] Deploy se performance > 10% melhor
- [ ] Monitorar drift

**Custo Estimado:** $80 (one-time) + $400/mês

---

## 📊 Cronograma Visual

```
Semana 1  │ ████ Correção LSP + CompanyConfigService
Semana 2  │ ████ Testes básicos + Estabilização
Semana 3  │ ██████ WSI Evaluator (Bloom + Dreyfus)
Semana 4  │ ██████ WSI Evaluator (Big Five + Parecer)
Semana 5  │ ████ Wizard Wire + Few-shot Prompts + CV Parser
Semana 6  │ ██████ Pearch AI + Microsoft Graph
Semana 7  │ ██████ WhatsApp Business API
Semana 8  │ ████ Deepgram + Polish
Semana 9  │ ████ ATS Integration (Gupy)
Semana 10+│ ░░░░ Treinamento e Otimização (contínuo)
```

---

## ✅ Critérios de Sucesso do MVP

1. **Zero erros LSP** em todos os agentes
2. **JobIntakeAgent** consome configurações da empresa
3. **WSI Evaluator** calcula score científico com Bloom/Dreyfus/Big Five
4. **Parecer** gerado automaticamente para cada candidato
5. **Pearch AI** integrado e retornando candidatos
6. **Agendamento** funciona via Microsoft Graph
7. **WhatsApp** envia mensagens para candidatos
8. **Cobertura de testes** > 50% nos agentes
9. **Todas as intents** mapeadas funcionando

---

## 📁 Arquivos a Criar/Modificar

### Novos Arquivos:
```
lia-agent-system/
├── app/
│   ├── services/
│   │   ├── company_configuration_service.py  # Fase 1
│   │   ├── cv_parser_service.py              # Fase 2
│   │   ├── pearch_service.py                 # Fase 3
│   │   ├── whatsapp_service.py               # Fase 3
│   │   ├── transcription_service.py          # Fase 3
│   │   ├── gupy_service.py                   # Fase 3
│   │   └── pandape_service.py                # Fase 3
│   └── evaluation/
│       ├── __init__.py                       # Fase 4
│       ├── metrics.py                        # Fase 4
│       └── calibration.py                    # Fase 4
└── tests/
    └── agents/
        ├── __init__.py                       # Fase 1
        ├── test_base_agent.py                # Fase 1
        ├── test_job_intake_agent.py          # Fase 1
        ├── test_sourcing_agent.py            # Fase 1
        ├── test_wsi_evaluator_agent.py       # Fase 1
        └── test_intent_router.py             # Fase 1
```

### Arquivos a Modificar:
```
lia-agent-system/app/agents/specialized/job_intake_agent.py     # Fase 1, 2
lia-agent-system/app/agents/specialized/sourcing_agent.py       # Fase 1, 3
lia-agent-system/app/agents/specialized/avaliador_wsi_agent.py  # Fase 2
lia-agent-system/app/agents/prompts/agent_prompts.py            # Fase 2
lia-agent-system/app/orchestrator/intent_router.py              # Fase 2
```

---

## 🚀 Próximos Passos Imediatos

1. **Aprovar este plano** com stakeholders
2. **Iniciar Fase 1** - Correção de erros LSP
3. **Configurar CI/CD** para rodar testes automaticamente
4. **Agendar reviews** semanais de progresso

---

## Histórico de Atualizações

| Data | Versão | Mudança |
|------|--------|---------|
| Jan/2026 | 1.0 | Criação inicial do plano |
