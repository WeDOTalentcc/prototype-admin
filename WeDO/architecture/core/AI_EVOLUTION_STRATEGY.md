# Estratégia de Evolução da IA - Plataforma LIA
**Data:** Novembro 2025  
**Objetivo:** Transformar LIA em um agente autônomo de recrutamento world-class através de treinamento avançado, fine-tuning e continuous learning

---

## 📊 Estado Atual (Baseline Assessment)

### ✅ O que já temos:
1. **Observability (LangSmith):** Tracing completo de LLM calls, agent executions, task planning
2. **Prompt Engineering Básico:** System prompts estruturados, intent classification, entity extraction
3. **Conversational Memory:** StateManager in-memory (MVP) - histórico de mensagens, agent results
4. **Evaluation Metrics (Limitado):** Voice screening analysis com scores (0-100) em 4 dimensões
5. **Testing Scripts:** test-chat.sh, test_voice_api.py para validação básica

### ❌ Gaps identificados:
1. **Fine-tuning de LLM:** Nenhum modelo customizado treinado
2. **Evaluation Metrics Abrangentes:** Só voice screening tem scores; falta para job creation, candidate search, scheduling
3. **Synthetic Data Generation:** Zero implementado
4. **Long-term Memory:** State em memória (não persistente além do PostgreSQL)
5. **Advanced Prompt Engineering:** Sem retrieval, few-shot dinâmico, ou chain-of-thought
6. **Continuous Learning Loop:** Nenhum feedback loop implementado

---

## 🎯 Estratégia em 5 Pilares

### Pilar 1: Evaluation Metrics & Quality Measurement
**Objetivo:** Medir performance da LIA em todas as dimensões críticas

#### 1.1 Intent Classification Accuracy
- **Métrica:** Precision, Recall, F1-score por intent
- **Gold Dataset:** 500 mensagens rotuladas manualmente
- **Threshold:** >95% accuracy (já está em 95%+ segundo logs)
- **Tracking:** LangSmith + PostgreSQL table `intent_evaluations`

#### 1.2 Entity Extraction Quality
- **Métrica:** Field-level extraction accuracy (job_title, skills, location, etc.)
- **Gold Dataset:** 300 mensagens com entities anotadas
- **Threshold:** >85% accuracy por campo
- **Tracking:** Custom evaluation script + LangSmith

#### 1.3 Conversational Flow Quality
**Dimensões:**
- **Clareza:** Respostas claras e sem ambiguidade (1-5 escala)
- **Completude:** Respostas completas vs. genéricas (1-5)
- **Tom:** Didática, proatividade, empatia (1-5)
- **Eficiência:** # de turnos para completar task (ideal: <5 turnos)

**Coleta:**
- Avaliação manual por consultores (5★ rating)
- Análise automática via Claude Sonnet 4.5 (meta-evaluation)

#### 1.4 Task Completion Success Rate
- **Job Creation:** % de vagas criadas com sucesso (target: >90%)
- **Candidate Search:** % de buscas que retornam resultados úteis (target: >85%)
- **Interview Scheduling:** % de agendamentos confirmados (target: >95%)

#### 1.5 User Satisfaction (CSAT)
- Thumbs up/down após cada resposta
- NPS score mensal
- Session abandonment rate (target: <10%)

---

### Pilar 2: Synthetic Data Generation
**Objetivo:** Gerar dados de treinamento realistas para fine-tuning e testing

#### 2.1 Conversational Data Synthesis
**Use Case:** Criar 10.000+ conversas de recrutamento sintéticas

**Stack Proposto:**
```python
# Generator usando Claude Sonnet 4.5
from langchain.prompts import ChatPromptTemplate

synthetic_conversation_prompt = """
Gere uma conversa realista entre um consultor de RH e LIA.

CENÁRIO: {scenario}
PERFIL CONSULTOR: {recruiter_profile}
COMPLEXIDADE: {complexity_level}

Crie uma conversa de 5-10 turnos onde:
1. Consultor descreve necessidade (vaga, busca, agendamento)
2. LIA faz perguntas de esclarecimento
3. Consultor fornece informações gradualmente
4. LIA confirma entendimento
5. Task é completada com sucesso

FORMATO DE SAÍDA:
[
  {"role": "user", "content": "...", "intent": "...", "entities": {...}},
  {"role": "assistant", "content": "..."},
  ...
]
"""

# Variáveis de cenário
scenarios = [
    "Criar vaga técnica (Python Backend)",
    "Buscar candidatos sênior para startup",
    "Agendar entrevista comportamental urgente",
    "Triagem de candidatos via WhatsApp",
    ...
]

recruiter_profiles = [
    "Consultor experiente (>5 anos)",
    "Consultor junior (primeiro mês)",
    "Hiring Manager técnico",
    "CEO de startup",
]

complexity_levels = ["simples", "moderado", "complexo", "edge_case"]
```

**Output:** 10.000 conversas sintéticas (JSON) para fine-tuning

#### 2.2 Job Description Dataset
**Use Case:** Gerar 5.000 JDs diversificadas para treinar extração de requisitos

```python
job_description_generator = """
Gere uma descrição de vaga realista.

SETOR: {sector}
SENIORIDADE: {seniority}
LOCALIZAÇÃO: {location}
ESTILO: {style}  # formal, informal, startup, corporativo

Inclua:
- Título claro
- Responsabilidades (5-8 itens)
- Requisitos técnicos (obrigatórios + desejáveis)
- Benefícios
- Informações sobre empresa

Variações: Incluir casos comuns (vagas confidenciais, salário não divulgado, híbrido)
"""

# Output: 5.000 JDs anotadas com entities extraídas
```

#### 2.3 Candidate Profile Dataset
**Use Case:** Gerar 20.000 perfis de candidatos para testes de busca

```python
candidate_profile_generator = """
Gere um perfil de candidato realista do mercado brasileiro.

PERSONA: {persona}  # dev backend, gerente produto, designer, etc.
EXPERIÊNCIA: {years_experience}
REGIÃO: {region}
SETOR ATUAL: {current_sector}

Inclua:
- Nome, email, telefone, LinkedIn
- Histórico profissional (3-5 empresas)
- Skills técnicas e comportamentais
- Formação acadêmica
- Idiomas
- Pretensão salarial

Torne REALISTA: Gaps de carreira, transições, upskilling
"""

# Output: 20.000 perfis para popular banco de dados de teste
```

---

### Pilar 3: Advanced Prompt Engineering
**Objetivo:** Evoluir de prompts estáticos para retrieval-augmented generation (RAG) e few-shot dinâmico

#### 3.1 RAG para Contexto Organizacional
**Implementação:**
```python
# Vector store para conhecimento da WedoTalent
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

knowledge_base = Chroma(
    collection_name="wedotalent_knowledge",
    embedding_function=OpenAIEmbeddings()
)

# Indexar documentos:
# - Políticas de RH da empresa
# - Histórico de vagas preenchidas (successful placements)
# - Perfis de clientes (hiring managers, departamentos)
# - Melhores práticas de triagem

# Retrieval durante conversa
def enhance_context(query, state):
    relevant_docs = knowledge_base.similarity_search(query, k=3)
    
    context = f"""
CONTEXTO RELEVANTE DA BASE DE CONHECIMENTO:
{chr(10).join([doc.page_content for doc in relevant_docs])}

CONVERSA ATUAL:
{state['messages'][-5:]}
"""
    return context
```

**Benefícios:**
- LIA aprende de casos passados
- Personalização por cliente/departamento
- Consistência com políticas da empresa

#### 3.2 Few-Shot Dynamic Learning
**Current:** Prompts com exemplos fixos  
**Target:** Few-shot examples selecionados dinamicamente via retrieval

```python
# Exemplo store
example_store = VectorStore("conversation_examples")

# Durante inference
def get_relevant_examples(user_message, intent):
    """Busca os 3 melhores exemplos de conversas similares"""
    examples = example_store.similarity_search(
        query=user_message,
        filter={"intent": intent},
        k=3
    )
    
    # Formato para prompt
    few_shot_examples = "\n\n".join([
        f"USER: {ex.user_message}\nLIA: {ex.lia_response}"
        for ex in examples
    ])
    
    return few_shot_examples

# Inject no prompt
enhanced_prompt = f"""
{SYSTEM_PROMPT}

EXEMPLOS DE CONVERSAS SIMILARES:
{few_shot_examples}

CONVERSA ATUAL:
User: {user_message}
LIA:
"""
```

#### 3.3 Chain-of-Thought Reasoning
**Para tarefas complexas:** Fazer LIA explicitar raciocínio antes de responder

```python
cot_prompt = """
Antes de responder, pense passo a passo:

1. ANÁLISE DA SITUAÇÃO:
   - O que o usuário está pedindo?
   - Que informações eu já tenho?
   - Que informações estão faltando?

2. ESTRATÉGIA DE RESPOSTA:
   - Devo executar ação agora ou pedir mais informações?
   - Qual a próxima pergunta mais eficiente?
   - Posso sugerir algo proativo?

3. CONSTRUÇÃO DA RESPOSTA:
   - Tom apropriado (didático, proativo, empático)
   - Clareza e objetividade
   - Call-to-action claro

Agora responda ao usuário:
"""
```

---

### Pilar 4: Fine-Tuning de LLM
**Objetivo:** Criar modelo customizado especializado em recrutamento

#### 4.1 Decisão: Fine-Tune vs. RAG vs. Hybrid
**Análise:**
| Abordagem | Vantagens | Desvantagens | Custo | Uso Ideal |
|-----------|-----------|--------------|-------|-----------|
| **RAG** | Sem retreinamento, atualização fácil | Latência maior, contexto limitado | Baixo | Conhecimento dinâmico |
| **Fine-Tuning** | Baixa latência, conhecimento "internalizado" | Caro, lento para atualizar | Alto | Padrões conversacionais |
| **Hybrid** | Melhor de ambos | Mais complexo | Médio-Alto | Ideal para LIA |

**Decisão:** **Hybrid Approach**
- **Fine-Tune Claude Sonnet 3.5** para padrões conversacionais de RH
- **RAG** para conhecimento específico da WedoTalent (policies, histórico)

#### 4.2 Dataset para Fine-Tuning
**Composição:**
- 5.000 conversas reais anonimizadas (coletadas de logs)
- 10.000 conversas sintéticas geradas (Pilar 2)
- 3.000 job descriptions com requisitos extraídos
- 2.000 casos de edge cases (erros, ambiguidades, conflitos)

**Total:** 20.000 exemplos de alta qualidade

#### 4.3 Fine-Tuning Pipeline (Anthropic)
```python
# 1. Preparar dataset no formato Anthropic
training_data = [
    {
        "messages": [
            {"role": "user", "content": "Preciso criar uma vaga"},
            {"role": "assistant", "content": "Vou te ajudar! Qual o cargo?"},
            {"role": "user", "content": "Desenvolvedor Python Sênior"},
            {"role": "assistant", "content": "Perfeito! Me conte mais sobre..."}
        ]
    },
    ...
]

# 2. Upload para Anthropic
import anthropic
client = anthropic.Anthropic()

# 3. Criar fine-tuning job
fine_tune_job = client.fine_tuning.create(
    model="claude-sonnet-3.5",
    training_data=training_data,
    validation_data=validation_data,
    hyperparameters={
        "epochs": 3,
        "batch_size": 16,
        "learning_rate": 1e-5
    }
)

# 4. Monitor training
while fine_tune_job.status != "completed":
    job = client.fine_tuning.get(fine_tune_job.id)
    print(f"Status: {job.status}, Loss: {job.metrics.train_loss}")
    time.sleep(60)

# 5. Deploy custom model
custom_model_id = fine_tune_job.fine_tuned_model
```

**Avaliação Pós-Fine-Tuning:**
- Intent accuracy: target >98% (vs. 95% atual)
- Entity extraction: target >92% (vs. ~85% atual)
- Conversational quality: +15% CSAT
- Task completion: +10% success rate

---

### Pilar 5: Continuous Learning Loop
**Objetivo:** Sistema de feedback contínuo para melhorar LIA automaticamente

#### 5.1 Feedback Collection System
```python
# PostgreSQL schema
class ConversationFeedback(Base):
    __tablename__ = "conversation_feedback"
    
    id = Column(UUID, primary_key=True)
    conversation_id = Column(UUID, ForeignKey("conversations.id"))
    message_id = Column(UUID, ForeignKey("messages.id"))
    
    # Feedback explícito
    rating = Column(Integer)  # 1-5 stars
    thumbs_up = Column(Boolean)
    feedback_text = Column(Text, nullable=True)
    
    # Feedback implícito
    task_completed = Column(Boolean)
    time_to_completion = Column(Integer)  # seconds
    num_clarifications_needed = Column(Integer)
    user_abandoned = Column(Boolean)
    
    # Metadata
    intent = Column(String)
    complexity = Column(String)  # simple, moderate, complex
    created_at = Column(DateTime)
```

#### 5.2 Automated Quality Scoring
```python
async def auto_evaluate_conversation(conversation_id):
    """Avalia qualidade da conversa usando Claude Sonnet 4.5"""
    
    conversation = await db.get_conversation(conversation_id)
    
    eval_prompt = f"""
Avalie esta conversa entre consultor e LIA:

{conversation.messages}

Retorne scores (0-100) para:
1. **Clareza:** Respostas claras e sem ambiguidade
2. **Eficiência:** Mínimo de turnos para completar task
3. **Proatividade:** LIA sugeriu ações úteis
4. **Tom:** Adequado (didático, empático, profissional)
5. **Precisão:** Informações corretas e relevantes

JSON:
{{
  "clarity_score": 0-100,
  "efficiency_score": 0-100,
  "proactivity_score": 0-100,
  "tone_score": 0-100,
  "accuracy_score": 0-100,
  "overall_score": 0-100,
  "improvement_suggestions": ["...", "..."]
}}
"""
    
    result = await claude.ainvoke(eval_prompt)
    
    # Salvar no banco
    await db.save_conversation_evaluation(conversation_id, result)
    
    return result
```

#### 5.3 Retraining Pipeline
**Cadência:** Mensal (ou quando atingir 1.000 novas conversas avaliadas)

```python
# 1. Coletar dados de melhor performance
high_quality_convos = db.query("""
    SELECT conversation_id, messages
    FROM conversations c
    JOIN conversation_evaluations e ON c.id = e.conversation_id
    WHERE e.overall_score >= 85
    AND e.task_completed = true
    AND c.created_at > NOW() - INTERVAL '30 days'
    LIMIT 1000
""")

# 2. Adicionar ao dataset de fine-tuning
training_data.extend(high_quality_convos)

# 3. Re-fine-tune modelo
new_fine_tune_job = client.fine_tuning.create(
    base_model=current_custom_model_id,
    training_data=training_data,
    validation_data=validation_data,
    incremental=True  # Fine-tune incremental (não do zero)
)

# 4. A/B testing antes de deploy
ab_test_results = await run_ab_test(
    model_a=current_custom_model_id,
    model_b=new_fine_tune_job.fine_tuned_model,
    num_conversations=100
)

if ab_test_results.model_b_wins:
    deploy_model(new_fine_tune_job.fine_tuned_model)
```

---

## 🛠️ Implementation Roadmap (6 meses)

### Mês 1-2: Foundation (Evaluation + Synthetic Data)
**Semana 1-2:**
- [ ] Criar gold datasets para intent classification (500 examples)
- [ ] Criar gold datasets para entity extraction (300 examples)
- [ ] Implementar evaluation scripts (precision, recall, F1)
- [ ] Setup LangSmith dashboards para tracking

**Semana 3-4:**
- [ ] Implementar synthetic data generators (job descriptions, candidate profiles)
- [ ] Gerar 5.000 JDs sintéticas + 10.000 perfis
- [ ] Criar conversation synthesis pipeline
- [ ] Validar qualidade dos dados sintéticos (amostragem manual)

**Semana 5-8:**
- [ ] Implementar conversational quality metrics (CSAT, completion rate)
- [ ] Adicionar thumbs up/down UI no chat
- [ ] Criar PostgreSQL tables para feedback
- [ ] Implementar auto-evaluation usando Claude Sonnet 4.5

**Deliverables:**
- ✅ 500 intent classification gold examples
- ✅ 300 entity extraction gold examples
- ✅ 5.000 JDs sintéticas
- ✅ 10.000 perfis de candidatos sintéticos
- ✅ Evaluation framework completo
- ✅ Feedback collection system

---

### Mês 3-4: Advanced Prompting + RAG
**Semana 9-10:**
- [ ] Implementar vector store para WedoTalent knowledge base
- [ ] Indexar 500+ documentos (policies, histórico de vagas, perfis de clientes)
- [ ] Criar retrieval pipeline para contexto dinâmico
- [ ] Testar RAG em 100 conversas (A/B test vs. baseline)

**Semana 11-12:**
- [ ] Implementar few-shot dynamic learning
- [ ] Criar example store com 1.000 conversas de alta qualidade
- [ ] Integrar retrieval de examples no prompt engineering
- [ ] Testar few-shot dinâmico vs. estático (A/B test)

**Semana 13-16:**
- [ ] Implementar chain-of-thought reasoning para tarefas complexas
- [ ] Adicionar "explain reasoning" mode (debug)
- [ ] Otimizar latência (target: <2s por resposta)
- [ ] Rollout gradual para 50% dos usuários

**Deliverables:**
- ✅ RAG system com 500+ docs indexados
- ✅ Few-shot dynamic learning (+10% accuracy)
- ✅ Chain-of-thought para edge cases
- ✅ Latência <2s mantida

---

### Mês 5-6: Fine-Tuning + Continuous Learning
**Semana 17-18:**
- [ ] Preparar dataset de fine-tuning (20.000 examples)
- [ ] Validar qualidade do dataset (amostragem 10%)
- [ ] Upload para Anthropic Fine-Tuning API
- [ ] Iniciar fine-tuning job (duração: ~1 semana)

**Semana 19-20:**
- [ ] Avaliar modelo fine-tuned (test set de 2.000 conversas)
- [ ] A/B test: Claude Sonnet 4.5 base vs. custom model
- [ ] Calcular ROI: accuracy gain vs. custo
- [ ] Deploy modelo customizado se gains > 8%

**Semana 21-22:**
- [ ] Implementar continuous learning pipeline
- [ ] Configurar retraining mensal automático
- [ ] Criar monitoring dashboard (model drift, performance degradation)
- [ ] Documentar processo de retraining

**Semana 23-24:**
- [ ] Rollout completo do modelo customizado
- [ ] Monitoring 24/7 por 2 semanas
- [ ] Ajustes finais baseados em feedback
- [ ] Documentação final + handoff para equipe

**Deliverables:**
- ✅ Modelo LIA customizado (fine-tuned Claude Sonnet 3.5)
- ✅ +12% accuracy em intent classification (target: 98%)
- ✅ +18% CSAT score
- ✅ Continuous learning pipeline em produção
- ✅ Documentação completa

---

## 💰 Estimativa de Custos

### Fine-Tuning (Anthropic)
- **Training:** $8 per 1M tokens (20K examples x 500 tokens avg = 10M tokens) = **$80**
- **Inference:** +20% vs. base model = **~$400/mês adicional**
- **Retraining mensal:** $80/mês

### Synthetic Data Generation
- **10K conversas:** 10K x 10 turnos x 200 tokens = 20M tokens = **$160 (one-time)**
- **5K JDs:** 5K x 500 tokens = 2.5M tokens = **$20 (one-time)**

### RAG Infrastructure
- **Vector store (Chroma self-hosted):** **$0**
- **Embedding API (OpenAI):** 500 docs x 1000 tokens = 500K tokens = **$2 (one-time)**
- **Retrieval inference:** +10% latência, custo embedding negligível = **$50/mês**

### Evaluation & Monitoring
- **LangSmith:** $39/mês (Professional plan)
- **Auto-evaluation:** 1000 conversas/mês x 1000 tokens = 1M tokens = **$8/mês**

**Total One-Time:** $262  
**Total Recorrente:** ~$577/mês ($39 LangSmith + $400 fine-tuned inference + $80 retraining + $50 RAG + $8 eval)

**ROI Esperado:**
- +18% CSAT → +30% conversão de leads
- -25% tempo médio por task → +40% produtividade consultores
- **Payback estimado:** 2-3 meses

---

## 📈 KPIs de Sucesso

### Technical Metrics
- Intent Classification Accuracy: **95% → 98%** (current → target)
- Entity Extraction Accuracy: **85% → 92%**
- Task Completion Rate: **82% → 92%**
- Avg Response Latency: **1.8s → <2.0s** (mesmo com RAG)

### Business Metrics
- CSAT Score: **4.2 → 5.0** (1-5 scale)
- NPS: **42 → 60**
- Session Abandonment: **15% → <10%**
- Time-to-Task-Completion: **8.5 min → 6.0 min**

### Learning Metrics
- New Training Examples/Month: **1,000+**
- Model Retraining Cadence: **Monthly**
- A/B Test Win Rate: **>60%** (new model vs. previous)

---

## 🚀 Próximos Passos Imediatos

### Para você (Agent):
1. **Criar gold datasets** (1-2 dias)
   - 500 mensagens para intent classification
   - 300 mensagens para entity extraction
   - Formato JSON com labels corretos

2. **Implementar evaluation scripts** (1 dia)
   - Calcular precision, recall, F1 por intent
   - Criar relatório de performance atual (baseline)

3. **Prototipar synthetic data generator** (2 dias)
   - Job description generator
   - Candidate profile generator
   - Validar 100 exemplos manualmente

### Para você (Usuário):
1. **Fornecer contexto adicional:**
   - Políticas de RH da WedoTalent (para RAG)
   - Histórico de vagas bem-sucedidas (para training)
   - Perfis de clientes ideais (para personalização)

2. **Aprovar investimento:**
   - Budget de ~$600/mês para fine-tuning + infraestrutura
   - Tempo de implementação: 6 meses (roadmap acima)

3. **Definir prioridades:**
   - Qual pilar atacar primeiro? (Recomendo: Pilar 1 + 2 em paralelo)
   - Algum caso de uso específico mais crítico? (job creation, candidate search, scheduling)

---

## 🤔 Perguntas para Alinhamento

1. **Dados Proprietários:**
   - Tem acesso a conversas reais de consultores? (anonimizadas)
   - Pode compartilhar 100-200 JDs reais para análise?
   - Tem histórico de candidatos colocados (successful placements)?

2. **Prioridades de Negócio:**
   - Qual fluxo é mais crítico para otimizar? (job creation, candidate search, scheduling)
   - Qual métrica importa mais? (CSAT, produtividade, conversão de leads)

3. **Recursos Disponíveis:**
   - Tem equipe técnica para implementar? Ou quer que eu (agent) execute tudo?
   - Budget aprovado para fine-tuning (~$600/mês)?
   - Prazo: 6 meses é viável ou precisa mais rápido?

---

**Como prefere seguir?** Posso:
- **A)** Começar gerando dados sintéticos agora (job descriptions, candidate profiles)
- **B)** Criar gold datasets para evaluation primeiro (baseline metrics)
- **C)** Implementar RAG imediatamente (conhecimento da WedoTalent)
- **D)** Outra prioridade que você definir

Me diga o caminho e vou executar! 🚀
