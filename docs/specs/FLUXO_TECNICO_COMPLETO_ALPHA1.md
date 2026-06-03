# Fluxo Técnico Completo — Plataforma LIA Alpha 1

**Data:** 03/06/2026 (auditoria de código vs. documentação)  
**Versão:** 1.1  
**Escopo:** Fluxo end-to-end Alpha 1 — desde Login até Scheduling/Feedback  
**Formato:** Diagrama passo-a-passo por macro-etapa (estilo "11 STEPS" do WSI)  
**Referência:** `ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md` v6.3 (complementar)

> ⚠ **Nota de auditoria (v1.1):** este documento foi auditado contra o código real do `lia-agent-system` em 03/06/2026. Correções de nomes de classe, caminhos de arquivo e contagens foram aplicadas ao longo do texto. Divergências que requerem decisão de produto/engenharia (não corrigíveis só no doc) estão consolidadas no apêndice **[Divergências & Gaps (auditoria 03/06/2026)](#divergências--gaps-auditoria-03062026)** no final do documento, e servem de base para tarefas futuras de correção. **Atualização (03/06/2026 — "resolver tudo"):** os 4 gaps que estavam abertos no apêndice foram resolvidos. O D-10 (mascaramento de nome via Presidio) exigiu alteração de código em `lia-agent-system` (`app/shared/pii_masking.py` + `requirements.txt` + teste); D-06/D-08/D-11 foram resolvidos no doc. Ver apêndice para detalhes.**

> 📋 **Checklists do time no final do documento:** [MVP — Roadmap Alpha 1](#checklist-pragmático-mvp--roadmap-alpha-1) (devs, PO, QA) · [Product Readiness — Go-Live](#checklist-product-readiness--go-live) (Ops, PM, Suporte, Legal, Billing).

---

## COMO LER ESTE DOCUMENTO

Cada macro-etapa do Alpha 1 (E1–E9B) é apresentada como um diagrama técnico passo-a-passo, seguindo o formato visual dos "11 STEPS" do fluxo de triagem WSI (ver imagem de referência). Cada step mostra:

1. **O request HTTP real** — endpoint, método, payload
2. **O roteamento** — DomainOrchestrator, CascadedRouter (6 tiers), domínio destino
3. **Os mixins/capabilities injetados** — EnhancedAgentMixin, AuditTrail, WorkingMemory, etc.
4. **FairnessGuard** — quais camadas (L1 explicit, L2 implicit, L3 semantic) atuam ANTES e DEPOIS do LLM
5. **PII Masking** — regex (CPF/email/telefone/RG/CNPJ) + quasi-identificadores + NER Presidio que mascara **nome (PERSON)**, ligado por padrão (modelo PT `pt_core_news_sm`)
6. **Processamento** — qual agente/serviço, qual LLM, qual graph/loop
7. **FactChecker** — 4 tipos de verificação pós-LLM
8. **ConfidenceNode + BiasAuditSnapshot** — calibração, Four-Fifths Rule
9. **AuditTrail** — o que é registrado, append-only, retenção SOX
10. **Response final** — dados demasked, scores, recomendação

### Legenda de Status

| Símbolo | Significado |
|---------|------------|
| ● | Ativo — funcionando no código |
| ◐ | Disponível — código existe, precisa ativar/configurar |
| ○ | A implementar — código não existe |
| ⚠ | Gap bloqueante — requer ação antes do MVP |
| 🔒 | Camada de proteção/compliance |
| 🧠 | Camada de inteligência/learning |

### Convenção de Agentes

| Rótulo | Classe no código | Domínio | LLM Provider |
|--------|-----------------|---------|--------------|
| Ag.0 | MainOrchestrator | orchestrator | Gemini (produção) |
| Ag.2 | SourcingReActAgent | sourcing | Gemini |
| Ag.3 | CV Screening — `WSIScreeningPipeline` / `PipelineReActAgent` (NÃO existe classe "TriagemCurricular"; ver D-09) | cv_screening | Gemini |
| Ag.4 | WSIInterviewGraph | cv_screening | Gemini |
| Ag.5 | WSIService (scoring) | cv_screening | Determinístico (sem LLM) |
| Ag.6 | InterviewGraph | interview_scheduling | Gemini |
| Ag.7 | CommunicationReActAgent / PersonalizedFeedbackService | communication / cv_screening | Gemini |
| Ag.8 | ATSIntegrationReActAgent ⚠ PÓS-MVP | ats_integration | Gemini |
| — | WSIQuestionGenerator / WSIScreeningQuestionGenerator | cv_screening | Gemini |
| — | WSIScreeningPipeline | cv_screening | Gemini |
| — | WSIVoiceOrchestrator | cv_screening | Gemini + Deepgram |
| — | JobDescriptionGeneratorService (`jd_generator_service.py`) | job_management | Claude (Anthropic) |

> **Nota de auditoria:** esta tabela é um subconjunto curado para o fluxo Alpha 1. O inventário canônico tem **16 ReActAgents** (sentinela `tests/integration/agents/test_tenant_aware_rollout_t_d.py`): 14 em `ALL_REACT_AGENTS_RUNTIME_PATH` + `CandidateSelfServiceAgent` e `PipelineTransitionAgent`. Os rótulos `Ag.x` deste doc são didáticos e não mapeiam 1:1 para os registries reais.

---

## GLOSSÁRIO DE COMPONENTES

Para facilitar a leitura por qualquer pessoa — mesmo sem conhecimento da arquitetura — esta seção explica **o que é cada componente** mencionado ao longo do documento.

### Tipos de Componente

| Tipo | O que é | Exemplo |
|------|---------|---------|
| **Domínio** | Uma área funcional da plataforma. Cada domínio agrupa um conjunto coeso de funcionalidades de negócio. É como um "departamento" da IA. | `sourcing` (busca de candidatos), `cv_screening` (triagem), `communication` (emails/mensagens), `job_management` (vagas), `interview_scheduling` (agendamento) |
| **Agente (Ag.)** | Um "trabalhador IA" autônomo que executa tarefas complexas usando raciocínio passo-a-passo (loop ReAct). Cada agente pertence a um domínio e usa ferramentas (tools) para agir. Pense nele como um especialista que analisa, decide e age. | Ag.2 SourcingReActAgent (busca candidatos), Ag.4 WSIInterviewGraph (conduz entrevista de triagem) |
| **Serviço** | Um componente que executa uma função específica, geralmente sem raciocínio autônomo. Recebe um input, processa e devolve um resultado. | `JobDescriptionGeneratorService` (gera descrição de vaga), `WSIService` (calcula scores de triagem) |
| **Tool (Ferramenta)** | Uma ação atômica que um agente pode executar. É como uma "mão" do agente — ele decide quando e como usar cada tool. | `search_candidates` (buscar), `send_email` (enviar email), `schedule_interview` (agendar) |
| **Capability (Capacidade)** | Um módulo transversal que é injetado automaticamente em agentes e serviços para adicionar comportamentos de proteção ou inteligência. Não age sozinho — é uma camada que enriquece quem o usa. | FairnessGuard (anti-viés), PII Masking (proteção de dados), AuditTrail (registro auditável) |
| **Orquestrador** | O componente central que recebe todas as requisições e decide qual domínio/agente deve processá-las. É o "recepcionista" que direciona cada pedido ao especialista certo. | `MainOrchestrator` + `CascadedRouter` (6 camadas de roteamento). Obs.: "DomainOrchestrator" é um nome conceitual deste doc — NÃO existe classe com esse nome (ver D-01) |
| **Graph (Grafo)** | Um fluxo de trabalho estruturado em etapas (nós) conectadas. Diferente do agente ReAct que raciocina livremente, o graph segue uma sequência definida de passos. | `WSIInterviewGraph` (8 estágios da entrevista WSI), `InterviewGraph` (6 nós do agendamento) |
| **Pipeline** | Uma sequência de processamento onde o output de uma etapa alimenta a próxima. Usado para processar dados em cadeia. | `WSIScreeningPipeline` (triagem curricular em cadeia) |
| **Registry** | O catálogo centralizado de agentes. Quando o orquestrador precisa de um especialista, consulta o registry para encontrá-lo pelo nome. | `"sourcing"` → SourcingReActAgent, `"wizard"` → WizardReActAgent |

### Componentes Transversais (aparecem em várias etapas)

| Componente | Tipo | O que faz | Em linguagem simples |
|------------|------|-----------|----------------------|
| **MainOrchestrator** (doc antigo: "DomainOrchestrator") | Orquestrador | Recebe toda requisição e roteia para o domínio correto usando 6 camadas de cache/análise. NÃO existe classe `DomainOrchestrator` — o orquestrador real é `MainOrchestrator` (`app/orchestrator/execution/main_orchestrator.py`) + `CascadedRouter` (ver D-01) | "Recepcionista inteligente" — entende o que você pediu e direciona ao especialista certo |
| **CascadedRouter** | Serviço (dentro do Orquestrador) | 6 camadas de roteamento: memória → cache local → cache Redis → busca vetorial → regex → LLM | "GPS de requisições" — tenta o caminho mais rápido primeiro, escala para análise mais profunda se necessário |
| **FairnessGuard** | Capability (3 camadas) | L1: bloqueia viés explícito (350+ padrões). L2: alerta viés implícito. L3: análise semântica por LLM | "Guardião de equidade" — impede que a IA discrimine por gênero, idade, etnia ou qualquer categoria protegida |
| **PII Masking** | Capability (multicamadas) | Remove dados pessoais antes de enviar ao LLM: regex direto (CPF, email, telefone, RG, CNPJ), quase-identificadores (idade/ano de formatura/endereço) e NER via Presidio que mascara **nome (PERSON)** — ligado por padrão (modelo PT `pt_core_news_sm`; configurável via `LLM_PROMPT_PRESIDIO_ENABLED` / `LLM_PROMPT_PRESIDIO_ENTITIES`). Ver D-10 | "Protetor de privacidade" — identificadores diretos do candidato (incl. nome) são mascarados antes do LLM |
| **AuditTrail** | Capability | Registra toda decisão de forma imutável (append-only); retenção por tipo de evento, até 7 anos para tipos SOX (ver D-07) | "Cartório digital" — tudo que a IA decide fica registrado e não pode ser alterado |
| **FactChecker** | Capability | Verifica claims do LLM: salário, contagem de candidatos, percentuais e datas (métodos `_check_*`; ver D-04) | "Verificador de fatos" — confere se o que a IA diz é coerente com os dados reais |
| **BiasAuditSnapshot** | Capability | Aplica Four-Fifths Rule: detecta se um grupo demográfico é aprovado <80% em relação a outro | "Auditor estatístico" — detecta discriminação numérica mesmo que ninguém a tenha intencionado |
| **ConfidenceNode** | Capability | Calibra scores para serem comparáveis entre candidatos e vagas diferentes | "Calibrador de notas" — garante que um 8 em uma vaga signifique o mesmo que um 8 em outra |
| **LearningLoop** | Capability | Observa silenciosamente quando o recrutador aceita, modifica ou rejeita sugestões da IA e aprende com isso | "Aprendiz silencioso" — a IA melhora sem pedir feedback explícito |
| **SemanticSearch** | Serviço | Expande termos de busca usando vetores semânticos (embeddings 768-dim via Gemini) | "Tradutor de intenções" — quando você busca "Java", ele entende que "Spring Boot" e "JVM" também são relevantes |
| **CircuitBreaker** | Capability | Protege contra falhas em cascata: se um serviço externo cai, para de chamá-lo temporariamente | "Disjuntor" — evita que a falha de um serviço derrube todo o sistema |
| **PolicyEngine** | Serviço | Define regras por setor: nível de autonomia da IA, quando escalar para humano, limites de uso | "Regulador setorial" — em saúde a IA é mais cautelosa, em RPO tem mais autonomia |
| **AntiSycophancy** | Capability | Impede que a IA concorde com tudo que o recrutador diz — força verificação de premissas | "Advogado do diabo" — a IA discorda quando os dados contradizem o que foi pedido |
| **WorkingMemory** | Capability | Memória de curto prazo do agente durante uma conversa/tarefa | "Bloco de notas" — o agente lembra o que já fez durante a tarefa atual |
| **LongTermMemory** | Capability | Memória de longo prazo com compressão automática após 30 dias | "Memória institucional" — a IA lembra padrões de vagas e candidatos passados |
| **ConversationMemory** | Capability | Tracking de entidades na sessão de chat (última vaga, último candidato, pronomes) | "Contexto de conversa" — quando você diz "ele", a IA sabe de quem está falando |
| **ModelDrift** | Capability | Monitora se os scores e decisões da IA estão mudando ao longo do tempo (janela de 7 dias) | "Detector de desvios" — alerta se a IA começa a aprovar muito mais (ou muito menos) que o normal |

---

## E1 — LOGIN — 4 STEPS

### O que acontece nesta etapa (visão do processo)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PASSO A PASSO — E1 LOGIN                                                     │
│                                                                               │
│  • O consultor/recrutador acessa a plataforma LIA pelo navegador             │
│  • Insere seu email e senha na tela de login                                 │
│  • A plataforma autentica as credenciais e gera um token de acesso           │
│  • O recrutador é redirecionado para o dashboard de vagas                    │
│  • Alternativa: login via SSO corporativo (WorkOS) se configurado            │
│  • Proteções ativas: limite de tentativas por IP, logs sem dados pessoais    │
│                                                                               │
│  Resultado: Recrutador autenticado, com acesso à plataforma                  │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Detalhamento técnico

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Login (auth) — 4 STEPS                                       │
│  AuthService [Serviço, domínio auth] — autentica o recrutador                │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Frontend (Next.js 15) envia POST /api/v1/auth/login
    Body: { "email": "user@company.com", "password": "secret" }
    Request logado automaticamente via middleware (X-Request-ID)

 2  AuthService autentica + gera JWT
    Valida email/password via bcrypt (has_secure_password)
    Gera access_token (JWT, 1800s) + refresh_token
    Valida is_active=True (dependency: get_current_active_user)
    WorkOS SSO disponível como alternativa (rotas /auth/workos)
    CircuitBreaker: circuit "workos" (failure_threshold=5, recovery=30s)

 3  RateLimitMiddleware protege contra brute-force
    Redis-backed sliding window (por IP + email)
    Fallback in-memory se Redis indisponível
    Prometheus: login_attempts_total counter

 4  Resposta ao recrutador
    TokenResponse: { access_token, refresh_token, token_type: "bearer", expires_in: 1800 }
    Frontend armazena token via useCookie('auth_token')
    Redireciona para /user/dashboard

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E1)                                          │
│  1. RateLimitMiddleware — sliding window por IP + email ●                     │
│  2. PII Masking — logs de login mascarados (PIIMaskingFilter global) ●        │
│  3. CircuitBreaker — circuit "workos" para SSO ●                              │
│  4. Audit Trail — login events ● (ativado em auth.py — login success/failure)│
│  5. LGPD — JWT stateless, sem cookies de sessão ●                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E2 — EDITAR/CRIAR VAGA — 8 STEPS

### O que acontece nesta etapa (visão do processo)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PASSO A PASSO — E2 EDITAR/CRIAR VAGA                                        │
│                                                                               │
│  • O recrutador acessa a página de vagas WeDo no dashboard                   │
│  • Opção A — EDITAR VAGA (importada do ATS):                                 │
│    - Seleciona uma vaga já existente (importada do sistema ATS do cliente)   │
│    - NÃO cria a vaga na WeDo — apenas edita os dados que vieram do ATS      │
│    - Define/ajusta requisitos, benefícios, faixa salarial, modelo de         │
│      trabalho (presencial/remoto/híbrido)                                    │
│    - 🤖 Ag.8 ATSIntegrationReActAgent sincroniza dados do ATS ⚠ PÓS-MVP(IMPORTANTE)    │
│  • Opção B — CRIAR VAGA MANUALMENTE na WeDo:                                │
│    - Clica em "Criar Vaga" → seleciona "Criar Manualmente"                  │
│    - Preenche todos os campos da vaga manualmente                           │
│  • GERAR JD (Descrição de Vaga) com IA:                           │
│    - Utiliza o job description da vaga para gerar JD enriquecido 
       Na sessão de Configuracao de triagem clica em "Gerar JD" no formulário da vaga  aproveitando JD já existente                            │
│    - 🤖 JobDescriptionGeneratorService [Serviço, domínio job_management]      │
│      gera/melhora a descrição automaticamente usando LLM (Claude)e seguindo 
orientacoes do prompt desenvolvido (atende diversos pre requisitos, 
inclusive fairness, lgpd etc(camada extra de seguranca para cliente nao publicar
JD com problemas e a LIA não consumir JD com problemas))           │
│    - A IA expande skills sugeridas usando busca semântica                    │         │
│  • O FairnessGuard [Capability anti-viés] analisa a vaga e bloqueia          │
│    requisitos discriminatórios (ex: "somente homens", "até 30 anos")                     │
│  • Tudo é registrado no AuditTrail [Capability de auditoria]                 │
│                                                                               │
│  Resultado: Vaga criada/editada com JD de qualidade, sem viés,               │
│  pronta para configurar o roteiro de triagem (E3)                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Detalhamento técnico

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Edição/Criação de Vaga (job_management) — 8 STEPS            │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Consultor acessa POST /api/v1/job-vacancies (criar) ou
    PUT /api/v1/job-vacancies/{vacancy_id} (editar)
    Body: { title, description, department, seniority_level, employment_type,
            work_model, location_city, salary_min, salary_max, required_skills }
    Authorization: Bearer <jwt_token>
    Se "Gerar JD" acionado: POST /api/v1/briefing/generate-jd

 IMPORTANTE: ITENS 2, 3, 4 5 NÃO IMPLEMENTADOS. SOMENTE PÓS MVP
 2  DomainOrchestrator roteia + GuardrailCheck
    Identifica domínio = job_management
    GuardrailRepository (3 níveis): global → tenant → domain
    HiringPolicy carregado por company_id
    PromptInjectionGuard ativado

 3  EnhancedAgentMixin._setup_enhanced()
    4 capabilities CENTRAIS injetadas pelo mixin: Memory,
    Autonomy/Guardrails, Learning, Compliance (+ 3 categorias
    de tools). Camadas como FairnessGuard, PII Masking, AuditTrail,
    BiasAuditSnapshot, ConfidenceNode, AntiSycophancy, CircuitBreaker,
    SemanticSearch e ConversationMemory atuam no fluxo via serviços
    próprios — NÃO são "16 capabilities" do mixin (ver D-05)

 4  FairnessGuard filtra ANTES do LLM
    🔒 L1 Explicit: Regex ~350 patterns em 13 categorias
       Bloqueia requisitos discriminatórios no JD (gênero, idade, etnia, religião,
       deficiência, estado civil, orientação sexual, gravidez, aparência,
       classe social, política, nacionalidade, saúde)
    🔒 L2 Implicit: Detecta termos proxy enviesados ("dinâmico" → age proxy,
       "boa aparência" → appearance proxy) — alerta (log only)
    Input + Output check via check_fairness em jd_generation.py

 5  PII Masking remove dados sensíveis
    NER Presidio (nome → [PERSON REMOVIDO], default ON) +
    regex (CPF → [CPF REMOVIDO], email, telefone, RG, CNPJ) +
    quasi-identificadores (idade/ano formatura/endereço)
    strip_pii_for_llm_prompt aplicado antes do prompt
    Identificadores diretos do candidato (incl. nome) são mascarados

CONTINUA DAQUI - ENRIQUECIMENTO DO JD COM LLM QUE SEGUE PROMPT DEFINIDO POR NOS
 6  JobDescriptionGeneratorService processa (Claude LLM)
    LLM recebe dados mascarados da vaga
    Gera JD estruturada em markdown:
    → Seções: Sobre, Responsabilidades, Requisitos, Benefícios, Diversidade
    → SEO title + tags
    Anti-sycophancy block (FULL variant) no system prompt
    CircuitBreaker: circuit "anthropic" (failure_threshold=5, recovery=30s)
    LLM expande skills sugeridas (Gemini 768-dim)

 7  AuditTrail registra decisão
    🔒 audit_service.log_decision ativo em jd_generation.py
    Registro: LLM input mascarado, output gerado, FairnessGuard results
    Append-only, retenção 730-1825 dias (SOX)
  
 8  Resposta ao recrutador (PII demasked)
    JD gerada com dados enriquecidos
    FairnessGuard warnings incluídos (se houver L2 alerts)
    Frontend renderiza JD no modal de edição de JD em configuracoes de triagem
    Dados persistidos via save_job_draft

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E2)                                          │
│  1. FairnessGuard L1/L2 — input+output check no JD ●                        │
│  2. PII Masking — 4 camadas pré-LLM ●                                       │
│  3. AntiSycophancy FULL — verificação de premissas ●                         │
│  4. CircuitBreaker — circuit "anthropic" ●                                   │
│  5. AuditTrail — log de geração de JD ● (edições manuais ●)                │
│  6. LearningLoop — captura silenciosa de edições ● NÃO APLICAVEL AINDA                          │
│  7. TemplateLearning — auto-template após 3 vagas similares ●  (NAO APLICAVEL AINDA)             │
│  8. PredictiveAnalytics — predict TTF + salary ●                             │
│  9. SemanticSearch — expansão de skills ●                                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E3 — CONFIGURAR ROTEIRO WSI — 9 STEPS

### O que acontece nesta etapa (visão do processo)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PASSO A PASSO — E3 CONFIGURAR ROTEIRO WSI                                   │
│                                                                               │
│  • A partir da vaga criada/editada na etapa anterior (E2), o recrutador      │
│    precisa configurar as perguntas que serão usadas na triagem dos            │
│    candidatos (WSI = Work Sample Interview — entrevista por amostra           │
│    de trabalho)                                                               │
│  • O recrutador acessa a TAB CONFIGURAÇÕES da vaga                           │
│    → SEÇÃO PERGUNTAS de Triagem                                              │
│  • Primeiro, se necessário, revisa/ajusta o JD (Descrição de Vaga) QUE JÁ FOI ENRIQUECIDO NA ETAPA ANTERIOR DE EDITAR JD          │
│    na aba de configurações da vaga                                           │
│  • Depois, clica em "Criar Roteiro" (modo completo ou compacto 7 OU 12 PERGUNTAS)              │
│    ou edita um roteiro existente                                             │
│  • 🤖 WSIQuestionGeneratorService [Serviço, domínio cv_screening]             │
│    gera perguntas WSI automaticamente usando o JD como base:                 │
│    - Bloco Técnico (avalia conhecimento em 6 níveis de profundidade - BLOOM E DREYFUS)        │
│    - Bloco Comportamental (avalia 5 traços de personalidade - Big Five)     │
│    - Bloco Situacional (cenários práticos do dia-a-dia da vaga)             │
│    -                │
│  • O recrutador revisa as perguntas geradas, pode editar, remover           │
│    ou adicionar perguntas manualmente                                        │
│  • O FairnessGuard [Capability anti-viés] valida cada pergunta              │
│    individualmente contra 13 categorias protegidas                           │
│  • O FactChecker [Capability verificador de fatos] valida a                  │
│    coerência das perguntas com o JD e requisitos                             │
│                                                                               │
│  Resultado: Roteiro de triagem WSI pronto, com perguntas validadas           │
│  e sem viés, para ser aplicado aos candidatos (E7)         

A TRIAGEM PODE SER ATIVADA NA VAGA ECANDIDATOS QUE SE INSCREVEM AUTOMATICAMENTE RECEBEM CONVITE PARA TRIAGEM
CANDIDATOS ADICIONADOS PELO RECRUTADOR - BUSCA NO FUNIL - OU IMPORTADOS DO ATS DO CLIENTE SAO CONVIDADOS MANUALMENTE.

└──────────────────────────────────────────────────────────────────────────────┘
```

### Detalhamento técnico

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Configuração de Roteiro WSI (cv_screening) — 9 STEPS         │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Consultor acessa TAB CONFIGURAÇÕES → SEÇÃO PERGUNTAS Triagem
    POST /api/v1/wsi/generate-questions
    Body: { job_id, mode: "complete"|"compact", job_description, requirements }
    Authorization: Bearer <jwt_token>

 2  DomainOrchestrator roteia + GuardrailCheck
    Identifica domínio = cv_screening
    GuardrailRepository (3 níveis): global → tenant → domain
    HiringPolicy (per-tenant) carregado
    PromptInjectionGuard ativado

 3  EnhancedAgentMixin._setup_enhanced()
    Capabilities injetadas:
    FairnessGuard (3 layers) | PII Masking (4 layers)
    AuditTrail | ConfidenceNode
    AntiSycophancy | WorkingMemory | CircuitBreaker
    LearningLoop | ConversationMemory | SemanticSearch

 4  JobDescriptionGeneratorService (se JD ausente)
    Se o JD não existe ou precisa ajuste, gera/melhora antes
    Mesmo fluxo da E2 (Claude LLM, FG L1/L2, PII Masking)
    Resultado: JD completa como base para perguntas WSI

 5  FairnessGuard filtra ANTES do LLM
    🔒 L1 Explicit: Valida cada pergunta candidata contra ~350 patterns
    🔒 L2 Implicit: Detecta perguntas com proxy bias
    check_fairness per-question em wsi_questions.py
    Bloqueia perguntas que violem 13 categorias protegidas

 6  PII Masking + strip do JD
    strip_pii_for_llm_prompt aplica 4 camadas
    JD enviado ao LLM sem dados identificáveis

 7  WSIQuestionGenerator processa (Gemini LLM)
    Recebe JD mascarada + requisitos da vaga
    Gera perguntas WSI em blocos estruturados:
    → Bloco 2: Técnico (Bloom 1-6, Dreyfus 1-5)
    → Bloco 3: Comportamental (Big Five traits)
    → Bloco 4: Situacional (cenários práticos)
    → Bloco 5: Cultural Fit
    Cada WSIQuestionBlock: block_id, block_type, question, competency,
    bloom_level, dreyfus_level, big_five_trait, max_score, trait_weight
    🧠 SemanticSearch expande competências sugeridas

 8  FactChecker verifica APÓS o LLM
    🔒 4 tipos de verificação:
    → Experiência declarada: claims vs dados de contexto
    → Certificações: validade técnica
    → Período na empresa: coerência temporal
    → Habilidades técnicas: relevância para a vaga
    Claim inconsistente → flag para revisão
    enable_fact_checker=True por default em DomainWorkflow._post_check

 9  AuditTrail registra + Resposta ao consultor
    🔒 audit_service.log_decision ativo em wsi_questions.py
    Registro: perguntas geradas, FG results, fact-check flags
    Append-only, retenção SOX
    🧠 LearningLoop captura edições nas perguntas
    Resposta: lista de perguntas WSI para revisão/ajuste no modal

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E3)                                          │
│  1. FairnessGuard L1/L2 — per-question check ●                              │
│  2. PII Masking — 4 camadas pré-LLM ●                                       │
│  3. FactChecker — 4 tipos de verificação pós-LLM ●                          │
│  4. AuditTrail — log de geração de roteiro WSI ●                             │
│  5. LearningLoop — captura edições de perguntas ●                            │
│  6. SemanticSearch — expansão de competências ●                              │
│  7. ConversationMemory — tracking da vaga ativa ●                            │
│  STATUS: Compliance completo para esta etapa ✓                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E4 — BUSCAR CANDIDATOS (Funil de Talentos) — 10 STEPS

### O que acontece nesta etapa (visão do processo)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PASSO A PASSO — E4 BUSCAR CANDIDATOS (Funil de Talentos)                    │
│                                                                               │
│  • O recrutador acessa o Funil de Talentos na plataforma                     │
│  • Pode buscar candidatos de 5 formas diferentes:                            │
│    - IA Natural: descreve o que precisa em linguagem livre                  │
│      (ex: "desenvolvedor Python com 5 anos, remoto, São Paulo")             │
│    - Boolean: busca avançada com operadores AND/OR/NOT                      │
│    - Perfil Similar: encontra candidatos parecidos com um existente         │
│    - Job Description: busca baseada no JD da vaga                           │
│    - Archetypes: busca por perfis-tipo pré-definidos                        │
│  • 🤖 Ag.2 SourcingReActAgent [Agente, domínio sourcing]                     │
│    executa a busca em 2 camadas:                                             │
│    - Local: banco de dados próprio (PostgreSQL, gratuito)                   │
│    - Global: base Pearch AI com 190M+ perfis (pago)                         │
│  • SemanticSearch [Serviço de busca semântica] expande os termos             │
│    da busca: "Java" → encontra também "Spring Boot", "JVM", "Maven"          │
│  • O FairnessGuard [Capability anti-viés] bloqueia buscas                    │
│    discriminatórias (ex: "somente candidatos homens") e detecta              │
│    termos com viés implícito (ex: "dinâmico" como proxy para idade)          │
│  • Dados pessoais dos candidatos são mascarados antes de                     │
│    qualquer análise pela IA                                                  │
│  • Resultados aparecem em tabela com 10 candidatos por vez,                  │
│    com preview inline (Perfil, Atividades, Arquivos, Pareceres)             │
│  • O recrutador pode dar Like/Dislike em cada candidato,                     │
│    e a IA aprende silenciosamente com essas preferências                     │
│                                                                               │
│  Resultado: Lista de candidatos ranqueados por aderência à vaga,             │
│  prontos para avaliação E PARA SEREM ADICIONADOS NA VAGA
NA VAGA RECRUTADOR PODE DISPARAR TRIAGEM APÓS aprovação DO PERFIL NA COLUNA FUNI DE TALENTOS                                     │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Detalhamento técnico

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Busca de Candidatos (sourcing) — 10 STEPS                    │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Consultor acessa Funil de Talentos
    GET /api/v1/candidates/search?query=...&skills=...&location=...
    Modos de busca: IA Natural | Boolean | Perfil Similar |
                    Job Description | Archetypes
    Authorization: Bearer <jwt_token>

 2  DomainOrchestrator roteia via CascadedRouter (6 tiers)
    Tier 0: MemoryResolver — resolve pronomes ("ele", "essa vaga")
    Tier 1: LRU in-process — hash MD5, O(1)
    Tier 2: Redis hash cache — distribuído
    Tier 3: VectorSemanticCache — pgvector, cosine ≥ 0.92
    Tier 4: FastRouter — regex/keyword, confiança ≥ 0.7
    Tier 5: LLM Cascade — Gemini (produção)
    Domínio destino = sourcing
    GuardrailRepository (3 níveis) + HiringPolicy carregado

 3  EnhancedAgentMixin._setup_enhanced()
    Capabilities completas injetadas:
    FairnessGuard (3 layers) | PII Masking (4 layers)
    AuditTrail | BiasAuditSnapshot | ConfidenceNode
    AntiSycophancy OPERATIONAL | WorkingMemory | LongTermMemory
    CircuitBreaker | LearningLoop | Calibration
    ScoreNormalization | RoutingAdaptativo | ModelDrift
    PredictiveAnalytics | ConversationMemory | SemanticSearch

 4  FairnessGuard filtra ANTES do LLM
    🔒 L1 Explicit: Bloqueia buscas discriminatórias (MainOrchestrator L35-47)
    🔒 L2 Implicit: Alerta proxy terms na busca (MainOrchestrator L48-62)
    🔒 L3 Semantic (setor-condicionada): Análise semântica profunda
       Setores com L3 ativo: tech, financeiro, saude, rpo
       check_with_sector() ativo em sourcing_agent, RAG pipeline
    _LEARNING_PROTECTED_FIELDS bloqueia learning de: gender, age, ethnicity,
    marital_status, photo, institution, address, religion, disability, cv_gaps

 5  PII Masking + anonimização
    4 camadas pré-LLM para candidatos
    strip_pii_for_llm_prompt em todos os perfis
    ToonService anonymize=True para modo anônimo (LGPD)

 6  Motor de Busca multi-tier
    Busca 2-tier: Local (PostgreSQL, gratuito) → Global (Pearch AI 190M+, pago)
    Elasticsearch + PGVector + WRF (Weighted Rank Fusion):
    → ES Score Drop Analyzer + PGV Gap Analyzer (pré-WRF)
    → WRF Dynamic K (ajuste por nível de qualificação)
    → LLM Job Classification para otimização de K values
    🧠 SemanticSearch: expansão semântica de skills/títulos/indústrias
       (Gemini text-embedding-004, 768-dim, Redis cache)
    CircuitBreaker: circuit "pearch" (failure_threshold=3, recovery=60s)

 7  Ag.2 SourcingReActAgent processa
    ReAct loop: max_iterations=5, max_tool_calls=3
    Tools: search_candidates, analyze_profile, score_candidate,
           compare_candidates, rank_candidates, generate_message
    WorkingMemory + LongTermMemory ativos
    🧠 RoutingAdaptativo: confidence multipliers 0.8x-1.2x por domínio

 8  FactChecker + ConfidenceNode + BiasAuditSnapshot
    🔒 FactChecker: valida claims nas análises LIA
       enable_fact_checker=True por default em DomainWorkflow._post_check
    🔒 ConfidenceNode: score calibrado para comparabilidade real
       confidence_score = tool_success_ratio × 0.7 + completion_ratio × 0.3
    🔒 BiasAuditSnapshot: Four-Fifths Rule
       Detecta se taxa de aprovação de grupo demográfico < 80% de outro
    🧠 ScoreNormalization: ajusta por difficulty_coefficient
    🧠 Calibration: feedback explícito/implícito sobre scores

 9  AuditTrail + Learning
    🔒 Audit: log de buscas + scores ● (ativado via sourcing_react_agent.py)
    🧠 LearningLoop: captura accept/modify/reject de candidatos
    🧠 ModelDrift: monitora score_drift + approval_drift (7-day window)
    🧠 PredictiveAnalytics: predict_skill_success integrado

 10 Resposta ao recrutador (PII demasked)
    Tabela de candidatos: 10 por vez + "Carregar +10"
    Preview inline com 4 tabs: Perfil | Atividades | Arquivos | Pareceres
    Like/Dislike feedback por candidato (otimiza busca)
    Prompt expandido da LIA (análise, comparação, ranking)
    Dados PII restaurados na response final

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E4)                                          │
│  1. FairnessGuard L1/L2/L3 — busca + análise + response ●                   │
│  2. PII Masking — 4 camadas + ToonService anonymize ●                        │
│  3. FactChecker — valida claims pós-LLM ●                                    │
│  4. BiasAuditSnapshot — Four-Fifths Rule ●                                   │
│  5. ConfidenceNode — calibração de score ●                                   │
│  6. ScoreNormalization — difficulty_coefficient ●                             │
│  7. AuditTrail — buscas + scores ● (ativado)                                │
│  8. LearningLoop — captura silenciosa ●                                      │
│  9. Calibration — feedback dual (explícito + implícito) ●                    │
│ 10. ModelDrift — 4 dimensões monitoradas ●                                   │
│ 11. SemanticSearch — expansão 768-dim ●                                      │
│ 12. RoutingAdaptativo — confidence multipliers ●                             │
│ 13. PredictiveAnalytics — predict_skill_success ●                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E5 — APROVAR MAPEADOS (Gate 1) — 9 STEPS

### O que acontece nesta etapa (visão do processo)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PASSO A PASSO — E5 APROVAR MAPEADOS (Gate 1)                                │
│                                                                               │
│  • O recrutador visualiza os candidatos mapeados no Kanban board             │
│    (painel visual com colunas representando cada etapa do processo)           │
│  • Para cada candidato, decide: APROVAR ou REPROVAR                          │
│    - Aprovação individual: arrasta o card do candidato para a                │
│      próxima coluna                                                          │
│    - Aprovação em massa: seleciona vários candidatos e aprova               │
│      todos de uma vez (máx. 100)                                             │
│    - Drag-and-drop: pode mover manualmente para qualquer coluna             │
│  • Se REPROVAR: precisa informar o motivo da rejeição                       │
│    - 🤖 FairnessGuard [Capability anti-viés] analisa o motivo               │
│      da rejeição contra 13 categorias protegidas                             │
│    - Se o motivo for discriminatório → BLOQUEADO OU AVISO automaticamente             │
│  • 🤖 PolicyEngine [Serviço de políticas por setor] define:                  │
│    - Se a IA pode aprovar sozinha ou precisa de confirmação humana           │
│    - Exemplo: no setor financeiro, quase tudo precisa HITL (Human           │
│      In The Loop); em RPO, a IA tem mais autonomia                           │
│  • Antes de contatar candidato aprovado, verifica consentimento LGPD        │
│    - Sem consentimento registrado → triagem não iniciada ou candidato bloqueado                        │
│  • Aprovados seguem para contato via email ou whatsapp(E6)                              │
│  • Reprovados recebem feedback personalizado elaborado pelos agentes de IA (LIA) (E9B)                           │
│  • ⚡ Candidatos que se inscreveram pelo site PULAM esta etapa               │
│    e vão direto para triagem automática                                      │
│                                                                               │
│  Resultado: Candidatos aprovados prontos para contato,                       │
│  reprovados com feedback respeitoso com base em perfil e performance (template construido para utilizacao da LLM)                                       │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Detalhamento técnico

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Aprovação Gate 1 (pipeline + kanban) — 9 STEPS               │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Consultor no Kanban board move candidato(s)
    POST /api/v1/pipeline/transition
    Body: { candidate_ids, from_stage, to_stage, action: "approve"|"reject",
            reason, job_id }
    Aprovação INDIVIDUAL ou EM MASSA (max 100)
    Drag-and-drop manual para qualquer coluna
    Authorization: Bearer <jwt_token>

 2  DomainOrchestrator + PolicyEngine
    Domínio = pipeline + kanban
    🔒 PolicyEngine: ALPHA1_SECTOR_RULES por setor
       Autonomy levels + HITL thresholds
       Determina se ação precisa confirmação humana
    SmartTransitionModal: etapas críticas pedem confirmação
    GuardrailRepository (3 níveis) carregado

 3  EnhancedAgentMixin._setup_enhanced()
    Capabilities injetadas:
    FairnessGuard (3 layers) | PII Masking (4 layers)
    AuditTrail | ConfidenceNode | BiasAuditSnapshot
    AntiSycophancy OPERATIONAL | WorkingMemory
    CircuitBreaker | LearningLoop | Calibration
    RoutingAdaptativo | ModelDrift | ConversationMemory

 4  FairnessGuard valida rejeições
    🔒 Auto-check em reject_candidate (candidate_tools.py)
    🔒 FG L3 pré-check no PipelineTransitionAgent
    check_rejection_fairness: motivo de rejeição analisado contra
    13 categorias protegidas
    Se motivo discriminatório → BLOCK + alerta ao consultor

 5  PipelineTransitionAgent interpreta contexto
    LangGraph ReAct (invocação direta, não via registry)
    POST /api/v1/pipeline/interpret-context
    Tools: validate_transition, get_candidate_profile,
           get_candidate_wsi_scores, suggest_sub_status,
           check_rejection_fairness, extract_preferences
    20 tools disponíveis no registry

 6  LGPD: Consentimento antes de contato
    🔒 CandidateChannelSelector.select_channels verifica:
       → LGPDConsent (consentimento registrado)
       → CandidateOptOut (opt-out por canal)
    WhatsApp: estado AWAITING_CONSENT com mensagem explícita
    Sem consentimento → contato bloqueado

 7  PolicyEngine: Escalation + HITL
    🔒 trigger_escalation quando AI confidence < threshold
    Threshold configurável por setor (ALPHA1_SECTOR_RULES)
    Se HITL necessário → pausa para decisão humana
    Notification: Bell + Teams

 8  AuditTrail + Learning
    🔒 Audit: log de aprovações/rejeições + overrides ● (ativado em pipeline.py + approvals.py)
    🧠 LearningLoop: captura decisões aceitar/rejeitar/modificar suggestion
    🧠 Calibration: implicit feedback (avançar low-score = sinal)
    🧠 ModelDrift: trigger se approval_drift > 10 p.p.
    🧠 RoutingAdaptativo: correções de rota alimentam ajustes

 9  Resposta + Disparo de próxima etapa
    Aprovados → LIA dispara contato (E6)
    Reprovados → LIA envia feedback (E9B)
    ⚡ Inscritos via web BYPASS Gate 1 → triagem automática
    Kanban board atualizado em real-time (ActionCable/WebSocket)

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E5)                                          │
│  1. FairnessGuard — auto-check em rejeções + FG L3 pré-check ●              │
│  2. PolicyEngine — HITL thresholds por setor ●                               │
│  3. LGPD — consent check antes de contato ●                                  │
│  4. PII Masking — ativo globalmente ●                                        │
│  5. Escalation — trigger quando AI confidence < threshold ●                  │
│  6. AuditTrail — aprovações/rejeições ● (ativado)                           │
│  7. LearningLoop — captura decisões ●                                        │
│  8. Calibration — implicit feedback ●                                        │
│  9. ModelDrift — approval_drift monitoring ●                                 │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E6 — CONTATO VIA EMAIL + FOLLOW-UP — 8 STEPS

### O que acontece nesta etapa (visão do processo)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PASSO A PASSO — E6 CONTATO VIA EMAIL + FOLLOW-UP                           │
│                                                                               │
│  • Após aprovação no Gate 1 (E5), a LIA envia automaticamente               │
│    um email para o candidato aprovado                                        │
│  • O email contém:                                                            │
│    - Apresentação da vaga e da empresa                                      │
│    - Link para a triagem via CHAT WEB (canal principal)                     │
│    - Opção de informar número de celular para triagem via WhatsApp          │
│    - Link obrigatório de opt-out (LGPD) para cancelar comunicações          │
│  • 🤖 Ag.7 CommunicationReActAgent [Agente, domínio communication]          │
│    personaliza e envia o email                                               │
│  • A IA testa variantes do template de email automaticamente                 │
│    (A/B Testing) para descobrir qual versão gera mais respostas  (NAO PRIORITARIO - POS MVP)            │
│  • Se o candidato NÃO abre/clica o email:                                    │
│    - Re-envio automático a cada 24h durante A CADA 2 dias              │
│    - Após 7 dias sem resposta → status "sem_resposta"                       │
│    - O recrutador é notificado via Teams                                     │
│  • Se o candidato clicou no opt-out → canal de email bloqueado              │
│    para futuras comunicações                                                 │
│                                                                               │
│  Resultado: Candidato contatado por email com link para triagem,             │
│  com follow-up automático de 7 dias                                          │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Detalhamento técnico

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Contato Email + Follow-up (communication) — 8 STEPS          │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Ag.0 MainOrchestrator dispara contato após Gate 1
    POST /api/v1/communications/send
    Body: { candidate_id, job_id, channel: "email", template_id,
            personalization: { candidate_name, job_title, screening_link } }
    Contato primário: SEMPRE email

 2  DomainOrchestrator roteia
    Domínio = communication
    GuardrailRepository carregado
    Rate limiting verificado: RateLimitRule sliding window por empresa/dia
    CircuitBreaker: circuits "sendgrid" + "resend" (critical tier)

 3  CommunicationReActAgent (Ag.7) processa
    ReAct loop: max_iterations=5
    Tools registradas (communication_tool_registry.py):
    → send_email, send_whatsapp, get_communication_history,
      schedule_message, check_rate_limit
    Legacy tools (communication_tools.py): send_feedback, send_bulk_email

 4  PII Masking em logs
    🔒 PIIMaskingFilter: emails não logam dados pessoais
    Conteúdo do email NÃO mascarado (é para o candidato)
    Logs de envio: PII stripped

 5  LGPD: Opt-out + Consent
    🔒 Opt-out link incluído no email (obrigatório)
    communication_optout.py: HMAC-signed tokens
    ConsentEvent auditável: registro de consentimento/revogação
    Se opt-out registrado → canal bloqueado para futuro

 6  Email enviado com 2 opções
    A) Link para triagem via CHAT WEB (canal principal)
    B) Solicita nº celular → WhatsApp (canal secundário)
    🧠 A/B Testing: variantes de template de email
       seed_email_ab_tests cria 3 experimentos no startup
    🧠 TemplateLearning: templates de email aprendidos

 7  Follow-up automático (7 dias)
    Se candidato NÃO abre/clica email:
    → Re-envio automático a cada 24h por 7 dias consecutivos
    → Após 7 dias sem resposta → status "sem_resposta"
    → Consultor notificado (Teams)
    Celery Beat schedule para verificação periódica

 8  AuditTrail + Response
    🔒 Audit: log de envios + opens + clicks ● (ativado em communication.py)
    🧠 ConversationMemory: tracking de candidatos contatados
    Resposta ao consultor: confirmação de envio + tracking status

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E6)                                          │
│  1. LGPD — opt-out link obrigatório + HMAC-signed tokens ●                  │
│  2. PII Masking — logs mascarados ●                                          │
│  3. RateLimiting — sliding window por empresa/dia ●                          │
│  4. CircuitBreaker — circuits "sendgrid" + "resend" ●                        │
│  5. A/B Testing — variantes de template ●                                    │
│  6. TemplateLearning — templates aprendidos ●                                │
│  7. AuditTrail — envios/opens/clicks ● (ativado)                            │
│  8. Follow-up automático — 7 dias, Celery Beat ●                             │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E7 — TRIAGEM WSI (cv_screening + WSI) — 11 STEPS

### O que acontece nesta etapa (visão do processo)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PASSO A PASSO — E7 TRIAGEM WSI                                              │
│                                                                               │
│  • O candidato recebeu o email (E6) e clica no link de triagem               │
│  • Acessa a página de triagem pelo navegador (chat web)                      │
│    ou pelo WhatsApp (se informou o número)                                   │
│    ou por voz (Twilio/OpenMic.ai — canal terciário)                          │
│  • Antes de começar, o candidato DEVE aceitar o termo LGPD                   │
│    (checkbox obrigatório no WelcomeCard — sem aceitar, não avança)           │
│  • 🤖 Ag.4 WSIInterviewGraph [Agente tipo Graph, domínio cv_screening]       │
│    conduz a entrevista de triagem automaticamente:                            │
│    - Faz perguntas técnicas (nível de profundidade progressivo,              │
│      de básico a avançado — Bloom 1 a 6)                                     │
│    - Faz perguntas comportamentais (avalia 5 traços de                       │
│      personalidade — Big Five: OCEAN)                                        │
│    - Faz perguntas situacionais (cenários práticos da vaga)                 │
│  • A sessão pode durar de 5-10 minutos (modo quick) a 10-15M minutos             │
│    (modo full), com salvamento automático do progresso                       │
│  • O candidato pode pausar e retomar a qualquer momento se não for modo ligacao - se for whatsapp                    │
│  • 🤖 Ag.5 WSIService [Serviço determinístico, domínio cv_screening]         │
│    calcula o score final SEM usar LLM (zero custo, zero latência)            │
│    com normalização por dificuldade do roteiro                               │
│  • O FactChecker [Capability verificador de fatos] valida as                 │
│    respostas: salário, contagem de candidatos, percentuais, datas (ver D-04) │
│  • O BiasAuditSnapshot [Capability auditor estatístico] aplica               │
│    Four-Fifths Rule para detectar discriminação numérica                     │
│  • Ao final, a LIA gera um parecer com recomendação:                         │
│    "aprovado" | "aguardando" | "reprovado"                                    │
│                                                                               │
│  Resultado: Candidato triado com score WSI, parecer da IA e                  │
│  recomendação, aguardando decisão do recrutador (Gate 2 — E8)                │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Detalhamento técnico

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Triagem (cv_screening + WSI) — 11 STEPS                      │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Frontend (Next.js 15) envia POST /api/chat
    Request logado via middleware (X-Request-ID auto-gerado)
    Canais: Chat web (link do email) | WhatsApp | Voz (Twilio/OpenMic.ai)
    Candidato clica link do email → página /triagem/[token]

 2  DomainOrchestrator roteia + GuardrailCheck
    Identifica domínio = cv_screening
    GuardrailRepository (3 níveis): global → tenant → domain
    HiringPolicy (per-tenant) carregado
    PromptInjectionGuard ativado

 3  EnhancedAgentMixin._setup_enhanced()
    4 capabilities CENTRAIS injetadas automaticamente pelo mixin
    (libs/agents-core/lia_agents_core/enhanced_agent_mixin.py):
    (1) Memory — working + long-term (_get_memory_context)
    (2) Autonomy/Guardrails — AutonomyEngine (_resolve_guardrails)
    (3) Learning — LearningExtractor (_post_loop_learning)
    (4) Compliance — FairnessGuard pre-check (_fairness_pre_check)
    + 3 categorias de tools compartilhadas (Insight/Proactive/Predictive)
    PII Masking, AuditTrail, BiasAuditSnapshot, ConfidenceNode,
    CircuitBreaker e ScoreNormalization atuam no fluxo, mas via
    camadas/serviços próprios — NÃO são "16 capabilities" do mixin
    (ver apêndice Divergências & Gaps, item D-05)

 4  FairnessGuard filtra ANTES do LLM
    3 camadas: (1) Regex → bloqueia "rejeitar por idade"
    (2) Implícito → detecta vieses indiretos ("bairro nobre")
    (3) LLM → análise semântica de fairness
    check_with_sector() ativo em rubric_evaluation.py
    Setores com L3: tech, financeiro, saude, rpo

 5  PII Masking remove dados sensíveis
    4 camadas pré-LLM: CPF → [CPF_MASKED]
    nome → [NAME_1] | endereço → [ADDR_MASKED]
    O LLM NUNCA vê dados pessoais reais

 6  WSI Interview Graph processa (1.141L)
    8 stages: INIT → LOAD → GENERATE → AWAIT →
    VALIDATE → SCORE → ADVANCE → COMPLETE
    Bloom (1-6) + Dreyfus (1-5) + Big Five (OCEAN)
    PostgresSaver checkpoint — sessões de 30-120 min via WebSocket
    interview_level: "quick" | "standard" | "full"
    HITL: interrupt_before=["lg_generate_feedback"]

 7  Gemini/Claude processa (dados mascarados)
    LLM recebe [CPF_MASKED], [NAME_1], etc.
    Anti-sycophancy block no system prompt
    CircuitBreaker protege contra falha
    Temperature: 0.3 (LLM_AGENT_TEMPERATURE)

 8  FactChecker verifica APÓS o LLM
    🔒 4 verificações reais (métodos _check_* em fact_checker.py):
    salário, contagem de candidatos, percentuais, datas
    Claim inconsistente → flag para revisão
    enable_fact_checker=True por default
    (tipos "experiência/certificações/período/habilidades" de
     versões anteriores NÃO batem com o código — ver D-04)

 9  ConfidenceNode calibra + BiasAuditSnapshot
    Score calibrado para comparabilidade real
    confidence_score = tool_success_ratio × 0.7 + completion_ratio × 0.3
    🔒 Four-Fifths Rule — detecta se taxa de aprovação
    de grupo demográfico < 80% de outro
    🧠 ScoreNormalization: ajusta por difficulty_coefficient
    🧠 Calibration: feedback dual sobre scores WSI

 10 AuditTrail registra TUDO (append-only)
    Registro imutável: request, fairness check, PII masks,
    LLM response, fact-check, scores, bias audit
    Retenção: 7 anos (SOX). Não pode ser alterado
    🧠 LearningLoop: captura padrões de resposta por competência
    🧠 ModelDrift: monitora drift em scores WSI (7-day window)

 11 Resposta ao recrutador (PII demasked)
    WSIFinalReport com recomendação + 3 scores
    (tech/behavioral) + wsi_final_score
    Dados PII restaurados na resposta (nunca no audit)
    Recomendação: "aprovado" | "aguardando" | "reprovado"

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E7)                                          │
│  1. PII nunca chega ao LLM — 4 camadas de mascaramento pré-LLM ●            │
│  2. FairnessGuard 3 layers — bloqueia vieses explícitos e implícitos ●       │
│  3. BiasAuditSnapshot — Four-Fifths Rule detecta discriminação estatística ● │
│  4. ConfidenceNode — calibra scores para serem comparáveis e significativos ●│
│  5. FactChecker pós-LLM — verifica claims factuais do candidato ●            │
│  6. Audit Trail SOX — registro imutável, 7 anos, append-only ●              │
│  7. WSI com Bloom+Dreyfus — progressão de dificuldade + cobertura ●          │
│  8. LGPD consent — WelcomeCard com checkbox explícito obrigatório ●          │
│  9. Anti-sycophancy — bloqueia concordância automática ●                     │
│ 10. ScoreNormalization — difficulty_coefficient por versão de roteiro ●       │
│ 11. Voice Analysis — STT Deepgram/Whisper + TTS OpenAI ●                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E7A — TRIAGEM ABANDONADA — 5 STEPS

### O que acontece nesta etapa (visão do processo)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PASSO A PASSO — E7A TRIAGEM ABANDONADA                                      │
│                                                                               │
│  • O candidato iniciou a triagem WSI (E7) mas parou de responder             │
│  • A plataforma detecta automaticamente a inatividade:                       │
│    - Verificação automática a cada 4 horas (Celery Beat)                    │
│  • Após 48h sem atividade → 1º lembrete automático                           │
│    - Mensagem personalizada pelo mesmo canal da triagem                     │
│    - Informa o progresso parcial ("você completou 60% da triagem")          │
│  • Após mais 48h (96h total) → 2º lembrete automático                        │
│    - Tom mais urgente, informa prazo limite                                  │
│  • Se ainda não retorna → alerta ao recrutador via Teams                     │
│    - Candidato marcado como "triagem_abandonada"                            │
│    - O recrutador decide: tentar re-engajar ou descartar                    │
│  • O progresso parcial NUNCA é perdido — fica salvo                          │
│    - Se o recrutador re-enviar o link, o candidato retoma de onde parou     │
│    - Scores parciais ficam visíveis para o recrutador                       │
│                                                                               │
│  Resultado: Candidato lembrado 2x; se não retorna, recrutador               │
│  é notificado para decisão manual                                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Detalhamento técnico

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Triagem Abandonada (cv_screening) — 5 STEPS                  │
└──────────────────────────────────────────────────────────────────────────────┘

 1  Detecção de abandono
    Candidato inicia WSI mas para de responder
    Celery Beat: task "wsi-abandoned-check" roda a cada 4h
    Verifica WSIInterviewState: last_activity_at vs now()
    Progresso parcial SALVO via PostgresSaver checkpoint

 2  1º Lembrete (48h sem atividade)
    Timeout: 48h sem atividade detectado
    Ag.7 CommunicationReActAgent envia lembrete
    Canal: mesmo da triagem (chat web, WhatsApp ou voz)
    Mensagem personalizada com progresso parcial

 3  2º Lembrete (+48h sem retorno)
    96h total sem atividade
    Segundo lembrete automático enviado
    Tom mais urgente, informa deadline

 4  Alerta ao consultor
    Após 2º lembrete sem retorno
    Alerta via Teams ao consultor responsável
    Candidato marcado como "triagem_abandonada"
    Consultor decide: re-engajar ou descartar

 5  Estado final
    Progresso parcial permanece salvo
    Scores parciais disponíveis para consultor
    Candidato pode retomar se consultor re-enviar link
    Audit: abandono registrado com timestamps

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E7A)                                         │
│  1. Checkpoint — progresso parcial salvo (PostgresSaver) ●                   │
│  2. Celery Beat — verificação automática a cada 4h ●                         │
│  3. Notification — alerta ao consultor via Teams ●                            │
│  4. LGPD — dados parciais com consentimento original ●                       │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E7B — FEEDBACK PÓS-TRIAGEM — 4 STEPS

### O que acontece nesta etapa (visão do processo)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PASSO A PASSO — E7B FEEDBACK PÓS-TRIAGEM                                   │
│                                                                               │
│  • O candidato completou toda a triagem WSI (E7)                             │
│  • 🤖 Ag.4 WSIInterviewGraph [Agente tipo Graph] gera o feedback:            │
│    - Agradece a participação do candidato                                   │
│    - Dá feedback construtivo sobre o desempenho CONFORME TEMPLATE - PROMPT PARA LLM                             │
│    - Informa os próximos passos do processo seletivo                        │
│  • O feedback é enviado pelo mesmo canal da triagem (chat, WhatsApp          │
│    ou voz)                                                                   │
│  • IMPORTANTE: o feedback NUNCA mostra scores numéricos ao candidato         │
│    (scores são removidos automaticamente antes do envio)                      │
│  • O FairnessGuard [Capability anti-viés] valida o texto do                  │
│    feedback para garantir que não contém viés ou discriminação               │
│  • O recrutador recebe alerta via Teams:                                     │
│    "Triagem WSI concluída para [candidato]"                                  │
│  • Score WSI + parecer da IA ficam disponíveis na plataforma                 │
│    para o recrutador revisar antes da decisão Gate 2 (E8)       
PARECER DA LIA - WSI TEM TEMPLATE DETERMINISTICO ONDE VARIAVEIS SAO SUBSTITUIDAS PARA EVITAR RISCOS│
│                                                                               │
│  Resultado: Candidato recebe feedback respeitoso PERSONALIZADO CONFORME TEMPLATE/PROMPT DEFINIDO
; recrutador é notificado e tem dados para decidir no Gate 2                             │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Detalhamento técnico

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Feedback Pós-Triagem (cv_screening) — 4 STEPS                │
└──────────────────────────────────────────────────────────────────────────────┘

 1  Triagem WSI completa
    Ag.4 WSIInterviewGraph atinge stage GENERATE_FEEDBACK
    HITL: interrupt_before=["lg_generate_feedback"]
    Score WSI calculado + recomendação gerada

 2  Feedback gerado ao candidato
    Ag.4 agradece participação
    Dá feedback construtivo sobre performance
    Informa próximos passos do processo
    Canal: mesmo da triagem (chat web, WhatsApp ou voz)

 3  FairnessGuard valida feedback
    🔒 FG L1/L2 em rubric_evaluation.py
    Feedback não pode conter viés ou dados discriminatórios
    PipelineFeedbackTool._remove_score_references: strip scores numéricos
    FairnessGuard sanitiza texto do feedback

 4  Notificação ao consultor
    Alerta via Teams: "Triagem WSI concluída para [candidato]"
    Score WSI + parecer LIA disponíveis na plataforma
    Candidato aguarda decisão Gate 2

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E7B)                                         │
│  1. FairnessGuard — feedback sem viés ●                                      │
│  2. Score stripping — remove scores numéricos do feedback ●                  │
│  3. HITL — interrupt_before para review humano ●                             │
│  4. Notification — alerta ao consultor ●                                     │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E8 — APROVAR/REPROVAR TRIADOS (Gate 2) — 8 STEPS

### O que acontece nesta etapa (visão do processo)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PASSO A PASSO — E8 APROVAR/REPROVAR TRIADOS (Gate 2)                        │
│                                                                               │
│  • O recrutador recebeu o alerta de triagem concluída (E7B)                  │
│  • Acessa o Kanban board e revisa os resultados:                             │
│    - Score WSI do candidato (técnico + comportamental + final)               │
│    - Parecer/recomendação da IA ("aprovado"/"aguardando"/"reprovado")        │
│  • Para cada candidato triado, decide: APROVAR ou REPROVAR                   │
│  • Se REPROVAR:                                                               │
│    - Informa o motivo da rejeição                                           │
│    - FairnessGuard [Capability anti-viés] valida o motivo contra             │
│      13 categorias protegidas — se discriminatório → BLOQUEADO              │
│    - 🤖 Ag.7 PersonalizedFeedbackService [Serviço, domínio cv_screening]     │
│      gera feedback personalizado e construtivo para o candidato CONFORME PROMPT DEFINIDO PARA LLM CONSUMIR E EVITAR RISCOS              │
│    - Um embedding do perfil é gerado para permitir                           │
│      "re-discovery" — se uma vaga futura for compatível,                     │
│      este candidato pode ser encontrado novamente                            │
│  • Se APROVAR:                                                                │
│    - Candidato vai para SHORT LIST (lista finalista)                        │
│    - Segue para agendamento de entrevista (E9A)                              │
│  • PolicyEngine [Serviço de políticas por setor] define se a IA              │
│    pode decidir sozinha ou precisa de aprovação humana                        │
│  • BiasAuditSnapshot [Capability auditor estatístico] verifica               │
│    equidade estatística nas decisões do Gate 2                               │
│                                                                               │
│  Resultado: Candidatos finalistas na Short List para entrevista;             │
│  reprovados com feedback personalizado e perfil salvo                        │
│  para re-discovery futuro                                                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Detalhamento técnico

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Aprovação Gate 2 (pipeline + kanban + analytics) — 8 STEPS    │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Consultor recebeu alerta Teams (E7B)
    Acessa Kanban board: POST /api/v1/pipeline/transition
    Body: { candidate_ids, from_stage: "triagem", to_stage: "shortlist"|"rejected",
            action, reason, wsi_reviewed: true }
    Revisa score WSI + parecer LIA antes de decidir

 2  DomainOrchestrator + PolicyEngine
    Domínio = pipeline + kanban + analytics
    🔒 PolicyEngine: HITL thresholds por setor (ALPHA1_SECTOR_RULES)
    Determina autonomia: AI pode decidir sozinha vs precisa HITL

 3  FairnessGuard valida rejeições
    🔒 Auto-check em reject_candidate (candidate_tools.py)
    🔒 FG L3 pré-check no PipelineTransitionAgent
    Motivo de rejeição analisado contra 13 categorias
    Se discriminatório → BLOCK + alerta

 4  LGPD: Sanitização de dados para próxima etapa
    🔒 PipelineFeedbackTool._remove_score_references: strip scores numéricos
    🔒 FairnessGuard sanitiza feedback
    🔒 ats_integration_stage_context.py: define campos internos vs ATS
    Dados compartilhados com próxima etapa minimizados

 5  PersonalizedFeedbackService (Ag.7) gera parecer
    Se REPROVADO: gera feedback personalizado para candidato
    FairnessGuard valida feedback antes de enviar
    Embedding do perfil gerado para re-discovery futuro
    _generate_rediscovery_embedding via embedding_service.py

 6  ConfidenceNode + BiasAuditSnapshot
    🔒 Score calibrado para comparabilidade
    🔒 Four-Fifths Rule: verifica equidade estatística Gate 2
    Se anomalia → alerta ao consultor

 7  AuditTrail + Learning
    🔒 Audit: log de aprovação/rejeição Gate 2 ● (ativado em pipeline.py + approvals.py)
    🧠 LearningLoop: feedback sobre decisões Gate 2
    🧠 Calibration: implicit feedback (avançar low-WSI = sinal)
    🧠 ModelDrift: monitora approval_drift Gate 2
    🧠 RoutingAdaptativo: correções entre domínios

 8  Resultado + Disparo
    Aprovados → SHORT LIST → E9A (agendar entrevista)
    Reprovados → E9B (enviar feedback)
    Kanban atualizado em real-time
    🧠 LongTermMemory: episódio salvo para referência futura

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E8)                                          │
│  1. FairnessGuard — auto-check rejeções + FG L3 ●                           │
│  2. PolicyEngine — HITL thresholds por setor ●                               │
│  3. LGPD — data minimization + score stripping ●                             │
│  4. BiasAuditSnapshot — Four-Fifths Rule Gate 2 ●                            │
│  5. AuditTrail — aprovações Gate 2 ● (ativado)                              │
│  6. LearningLoop + Calibration + ModelDrift ●                                │
│  7. Embedding — rediscovery de candidatos reprovados ●                       │
│  8. LongTermMemory — episódios salvos ●                                      │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E9A — AGENDAR ENTREVISTA — 7 STEPS

### O que acontece nesta etapa (visão do processo)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PASSO A PASSO — E9A AGENDAR ENTREVISTA                                      │
│                                                                               │
│  • O candidato foi APROVADO no Gate 2 (E8) e está na Short List              │
│  • A LIA dispara automaticamente o agendamento de entrevista                 │
│  • 🤖 Ag.6 InterviewGraph [Agente tipo Graph, domínio                        │
│    interview_scheduling] busca horários disponíveis:                          │
│    - Consulta o Google Calendar do entrevistador                            │
│    - Encontra os melhores horários disponíveis                              │
│    - Se não encontra horário → alerta ao recrutador via Teams               │
│  • O candidato recebe comunicação com data/hora + link da reunião            │
│    por email E WhatsApp (duplo canal)                                        │
│  • O convite de calendário (ICS) enviado contém SOMENTE                      │
│    dados mínimos: data, hora, local e participantes                         │
│    (LGPD: nenhum dado sensível do candidato no arquivo)                      │
│  • Calendar invite é enviado a todos os participantes                        │
│  • Status atualizado no Kanban board                                         │
│                                                                               │
│  Resultado: Entrevista agendada, todos os participantes notificados,         │
│  Kanban atualizado                                                           │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Detalhamento técnico

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Agendamento de Entrevista (interview_scheduling) — 7 STEPS    │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Candidato APROVADO no Gate 2 → trigger automático
    POST /api/v1/scheduling/create
    Body: { candidate_id, job_id, interview_type, preferred_dates }
    Authorization: Bearer <jwt_token>

 2  DomainOrchestrator roteia
    Domínio = interview_scheduling
    Ag.6 InterviewGraph ativado
    GuardrailRepository carregado
    CircuitBreaker: circuit "google_calendar" (recovery=60s)

 3  Ag.6 InterviewGraph processa
    LangGraph StateGraph: 6 nós
    Tools: schedule_interview, check_availability,
           reschedule_interview, cancel_interview
    Busca horários disponíveis no Google Calendar
    Se NÃO encontra horário → alerta ao consultor via Teams

 4  LGPD: Data Minimization no ICS
    🔒 SchedulingService.generate_ics_content:
    Apenas dtstart/dtend/summary/location/attendee
    SEM dados sensíveis do candidato no arquivo ICS
    Mínimo necessário para o agendamento funcionar

 5  Comunicação multi-canal
    Email + WhatsApp ao candidato (data/hora + link reunião)
    Ag.7 CommunicationReActAgent envia por ambos canais
    Template personalizado com dados da vaga e entrevistador

 6  AuditTrail + Learning
    🔒 Audit: log de agendamento ● (ativado em scheduling.py)
    🧠 LearningLoop: feedback sobre qualidade da sugestão
    🧠 LongTermMemory: episódio salvo (EnhancedAgentMixin._post_loop_learning)

 7  Resposta ao consultor
    Confirmação de agendamento + detalhes
    Calendar invite enviado a todos os participantes
    Status atualizado no Kanban

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E9A)                                         │
│  1. LGPD — data minimization no ICS ●                                        │
│  2. CircuitBreaker — circuit "google_calendar" ●                             │
│  3. PII Masking — ativo globalmente ●                                        │
│  4. AuditTrail — agendamento ● (ativado)                                    │
│  5. LongTermMemory — episódios salvos ●                                      │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E9B — ENVIAR FEEDBACK (Reprovado) — 6 STEPS

### O que acontece nesta etapa (visão do processo)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PASSO A PASSO — E9B ENVIAR FEEDBACK (Reprovado)                             │
│                                                                               │
│  • O candidato foi REPROVADO no Gate 2 (E8)                                  │
│  • 🤖 Ag.7 PersonalizedFeedbackService [Serviço, domínio cv_screening]       │
│    gera feedback personalizado e construtivo COM BASE EM PROMPT DEFINIDO PARA EVITAR PROBLEMAS:                                 │
│    - Analisa o perfil completo + scores WSI + motivo da rejeição            │
│    - Gera texto respeitoso e útil para o candidato                          │
│    - NUNCA inclui scores numéricos (removidos automaticamente)              │
│  • O FairnessGuard [Capability anti-viés] valida o feedback:                 │
│    - Verifica que não contém viés ou discriminação                          │
│    - Sanitiza o texto antes do envio                                         │
│  • O feedback é enviado ao candidato por:                                     │
│    - Email (canal primário, sempre)                                          │
│    - WhatsApp (se o número está disponível)                                  │
│  • A IA testa variantes do template de feedback (A/B Testing)                │
│    para descobrir qual formato gera melhor experiência                       │
│  • Um embedding do perfil do candidato é gerado e salvo:                     │
│    - Permite "re-discovery" futuro: se uma vaga compatível                  │
│      aparecer no futuro, este candidato pode ser encontrado                 │
│      automaticamente pela busca semântica                                    │
│  • Status final do candidato atualizado no Kanban board                      │
│  • Episódio completo salvo na memória de longo prazo da IA                   │
│                                                                               │
│  Resultado: Candidato recebe feedback respeitoso e construtivo;              │
│  perfil salvo para oportunidades futuras; processo encerrado                 │
│  com dignidade                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Detalhamento técnico

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Feedback para Reprovado (communication) — 6 STEPS             │
└──────────────────────────────────────────────────────────────────────────────┘

 1  Trigger: Candidato REPROVADO no Gate 2
    Ag.0 MainOrchestrator dispara feedback
    Domínio = communication + cv_screening

 2  PersonalizedFeedbackService (Ag.7) gera feedback
    Analisa perfil + scores WSI + motivo de rejeição
    Gera feedback construtivo e personalizado
    🔒 FairnessGuard L1/L2: valida feedback antes de envio
    PipelineFeedbackTool._remove_score_references: strip scores

 3  PII Masking + FairnessGuard
    🔒 PII: dados pessoais protegidos em logs
    🔒 FG: feedback não contém viés ou discriminação
    Texto sanitizado por FairnessGuard

 4  CommunicationReActAgent envia
    Email (primário) + WhatsApp (se número disponível)
    Template personalizado com feedback construtivo
    🧠 A/B Testing: variantes de template de feedback
    🧠 TemplateLearning: templates aprendidos

 5  Embedding para rediscovery
    🧠 _generate_rediscovery_embedding:
    Gera embedding do perfil (Gemini text-embedding-004, 768-dim)
    Salvo via embedding_cache_service.py
    Permite re-discovery em vagas futuras similares

 6  AuditTrail + Response
    🔒 Audit: log de feedback enviado ● (ativado em communication.py)
    🧠 LearningLoop: feedback sobre qualidade do feedback gerado
    Status final do candidato atualizado no Kanban
    🧠 LongTermMemory: episódio completo salvo

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E9B)                                         │
│  1. FairnessGuard L1/L2 — feedback sem viés ●                                │
│  2. Score stripping — remove scores numéricos ●                              │
│  3. PII Masking — dados protegidos ●                                         │
│  4. A/B Testing — variantes de feedback ●                                    │
│  5. TemplateLearning — templates aprendidos ●                                │
│  6. Embedding — rediscovery futuro ●                                         │
│  7. AuditTrail — feedback ● (ativado)                                       │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## SEÇÃO TRANSVERSAL: GOVERNANÇA TÉCNICA

### Policy Engine — Motor de Políticas por Setor

```
Arquivo: app/domains/policy/services/policy_engine_service.py
Classe: PolicyEngineService (constante ALPHA1_SECTOR_RULES no mesmo módulo)

ALPHA1_SECTOR_RULES — Regras por setor:
┌──────────────────────────────────────────────────────────────────────────────┐
│  Setor        │ Autonomy  │ HITL Threshold │ FG L3  │ Rate Limit │ Escalation│
│──────────────┼───────────┼────────────────┼────────┼────────────┼───────────│
│  tech         │ medium    │ medium         │ ativo  │ standard   │ ativo     │
│  financeiro   │ low       │ high           │ ativo  │ strict     │ ativo     │
│  saude        │ low       │ high           │ ativo  │ strict     │ ativo     │
│  rpo          │ high      │ low            │ ativo  │ relaxed    │ ativo     │
│  varejo       │ medium    │ medium         │ inativo│ standard   │ ativo     │
│  logistica    │ medium    │ medium         │ inativo│ standard   │ ativo     │
└──────────────────────────────────────────────────────────────────────────────┘

Funcionalidades:
- Autonomy Levels: low (tudo precisa HITL) | medium (ações críticas) | high (auto)
- HITL Thresholds: % de confiança abaixo do qual AI escala para humano
- trigger_escalation: quando AI confidence < threshold por setor
- Rate Limiter: sliding window por empresa/dia/endpoint
- Planos: Starter / Pro / Enterprise (tokens mensais, agentes, automações)
  PLAN_LIMITS_ENFORCE=true
```

### CircuitBreaker — 14+1 Circuits

```
Arquivo: app/shared/resilience/circuit_breaker.py

Padrão de 3 Estados: CLOSED → OPEN → HALF_OPEN → CLOSED
  CLOSED: chamadas passam; cada falha incrementa contador
  OPEN: todas rejeitadas com CircuitBreakerError + retry_after
  HALF_OPEN: permite chamadas limitadas para testar recuperação

Circuits pré-configurados — ATENÇÃO (auditoria 03/06/2026): o código
define ~22 circuits, NÃO 14. Nomes reais em circuit_breaker.py:
  anthropic, openai, deepseek, gemini, pearch, apify, apify_search,
  workos, merge, google_calendar, gupy, pandape, mailgun, resend,
  iugu, vindi, twilio_voice, gemini_live, deepgram, openmic, rails_api
NÃO existe circuit "sendgrid" (substituído por "mailgun"; ver replit.md
"Mailgun primary / Resend fallback"). "llm_react_reason" é criado
por-ReAct em runtime, não no config default. A tabela legada abaixo
está DESATUALIZADA nos valores e na lista (ver D-06):

┌──────────────────────────────────────────────────────────────────────────────┐
│  Circuit         │ Failures │ Recovery │ Success │ Timeout │ Tier      │
│─────────────────┼──────────┼──────────┼─────────┼─────────┼───────────│
│  anthropic       │ 5        │ 30s      │ 2       │ 60s     │ critical  │
│  openai          │ 5        │ 30s      │ 2       │ 60s     │ critical  │
│  gemini          │ 5        │ 30s      │ 2       │ 60s     │ high      │
│  pearch          │ 3        │ 60s      │ 2       │ 30s     │ high      │
│  workos          │ 5        │ 30s      │ 2       │ 15s     │ critical  │
│  merge           │ 5        │ 45s      │ 2       │ 30s     │ high      │
│  google_calendar │ 5        │ 60s      │ 2       │ 30s     │ medium    │
│  gupy            │ 5        │ 45s      │ 2       │ 30s     │ high      │
│  pandape         │ 5        │ 45s      │ 2       │ 30s     │ high      │
│  sendgrid        │ 5        │ 30s      │ 2       │ 30s     │ critical  │
│  resend          │ 5        │ 30s      │ 2       │ 30s     │ high      │
│  iugu            │ 3        │ 60s      │ 2       │ 30s     │ medium    │
│  vindi           │ 3        │ 60s      │ 2       │ 30s     │ medium    │
│  llm_react_reason│ 3        │ 60s      │ 2       │ 30s     │ (ReAct)   │
└──────────────────────────────────────────────────────────────────────────────┘

Notificação de Circuit Open (COMP-3):
  Redis dedup: máximo 1 alerta por circuit por hora
  Canais: Bell (in-app) + Teams (webhook)
  Mensagem: "⚡ Circuit Breaker ABERTO: {service_name}"
  Prometheus: circuit_breaker_state (0=closed, 1=half_open, 2=open)

Degraded Mode Responses (14 mensagens PT-BR):
  Cada serviço tem mensagem amigável quando circuit OPEN
  Fallback genérico: "Este serviço está temporariamente indisponível."
```

### PromptInjectionGuard

```
Ativado em todo request que chega ao DomainOrchestrator
Detecta tentativas de prompt injection no input do usuário
Bloqueia execução se injeção detectada
Registra tentativa no audit log
```

### Anti-Sycophancy — 3 Variantes

```
Arquivo: app/shared/prompts/anti_sycophancy_block.py

ANTI_SYCOPHANCY_OPERATIONAL → Talent, Kanban, Jobs Management
  5 regras: não concordar com filtros discriminatórios,
  verificar antes de confirmar, discordância com dados

ANTI_SYCOPHANCY_FULL → Wizard, Policy
  5 regras + VERIFICAÇÃO DE PREMISSAS (5 sub-regras)
  Mais restritivo: verificar histórico, nunca mudar silenciosamente

ANTI_SYCOPHANCY_ORCHESTRATOR → Orchestrator
  Versão compacta (1 frase) — ponto de entrada global

Crença #11 do Manifesto WeDOTalent:
"Anti-sycophancy em 100% das interações IA."
```

---

## SEÇÃO TRANSVERSAL: COMPLIANCE TÉCNICO

### FairnessGuard — 3 Camadas

```
Arquivo: app/shared/compliance/fairness_guard.py

Layer 1: Explicit Bias Block
  ~350+ patterns em 13 categorias:
  gender, age, ethnicity, religion, disability, marital_status,
  sexual_orientation, pregnancy, appearance, social_class,
  political, nationality, health
  Ação: BLOCK — impede processamento
  Integração: MainOrchestrator (pré-roteamento)

Layer 2: Implicit Bias Soft Warning
  Proxy terms detectados:
  "dinâmico" → age proxy | "boa aparência" → appearance proxy
  Ação: WARN — permite com alerta (log only)
  Integração: MainOrchestrator (pré-roteamento)

Layer 3: Semantic Analysis (LLM-based)
  Provider: Gemini (análise semântica profunda)
  Ação: WARN ou BLOCK dependendo da severidade
  Condicionada por setor: ALPHA1_SECTOR_RULES[sector].fairness_layer3_enabled
  Ativo em: tech, financeiro, saude, rpo
  Inativo em: varejo, logistica

Protected Fields (Learning Loop):
  _LEARNING_PROTECTED_FIELDS = {gender, age, ethnicity, marital_status,
  photo, institution, address, religion, disability, cv_gaps}
  validate_learning_batch() bloqueia patterns discriminatórios ANTES de persistir

Pontos de integração:
  - MainOrchestrator L35-62 (L1/L2 pré-roteamento)
  - jd_generation.py (L1/L2 input+output)
  - wsi_questions.py (per-question check)
  - rubric_evaluation.py (reasoning check)
  - candidate_tools.py (reject_candidate auto-check)
  - PipelineTransitionAgent (L3 pré-check)
  - sourcing_agent (L3 via check_with_sector)
  - communication_tools (L3)
  - RAG pipeline (L3)
```

### PII Masking — 4 Camadas

```
Arquivo: app/shared/pii_masking.py

Camada 1: CPF → [CPF_MASKED]
Camada 2: nome → [NAME_1], [NAME_2], etc.
Camada 3: endereço → [ADDR_MASKED]
Camada 4: campos sensíveis → [FIELD_MASKED]

Função: strip_pii_for_llm_prompt (global)
PIIMaskingFilter: filtro global de logs
Presidio: NER (PERSON/EMAIL/PHONE/NRP) LIGADO POR PADRÃO
  (LLM_PROMPT_PRESIDIO_ENABLED=true; modelo pt_core_news_sm)

Objetivo: minimizar PII real enviada ao LLM — best-effort por regex +
  NER (não é garantia absoluta; ver trade-off no apêndice D-10)
Demasking: dados restaurados na response final ao recrutador
Audit: dados mascarados no registro (nunca reais)
```

### FactChecker — 4 Tipos de Verificação

```
Arquivo: app/shared/compliance/fact_checker.py

4 verificações IMPLEMENTADAS (métodos _check_* em fact_checker.py):
Tipo 1: Salário — faixas salariais plausíveis (_check_salary_claims)
Tipo 2: Contagem de candidatos — números coerentes (_check_candidate_counts)
Tipo 3: Percentuais — valores no range 0-100 (_check_percentage_claims)
Tipo 4: Datas — janelas temporais de recrutamento (_check_date_claims)

Integração: DomainWorkflow._post_check (app/domains/workflow.py;
  enable_fact_checker=True por default)
Claim inconsistente → flag para revisão
Métodos verify_* granulares + registry de validadores por domínio
NOTA: os tipos "experiência declarada / certificações / período /
  habilidades técnicas" de versões anteriores deste doc NÃO
  correspondem aos métodos do código (ver D-04)

Pontos de integração:
  - wsi_questions.py (valida claims nas perguntas)
  - sourcing (valida claims nas análises)
  - rubric_evaluation.py (valida scores e claims WSI)
```

### BiasAuditSnapshot — Four-Fifths Rule

```
ConfidenceNode + BiasAuditSnapshot integrados

ConfidenceNode:
  confidence_score = tool_success_ratio × 0.7 + completion_ratio × 0.3
  Score calibrado para comparabilidade real

BiasAuditSnapshot:
  Four-Fifths Rule: se taxa de aprovação de grupo demográfico < 80% de outro
  → alerta automático
  Dados coletados em cada Gate (1 e 2)
  Dashboard de Bias Audit: ○ (pendente — backend coleta dados)
```

### AuditTrail — SOX-Compliant

```
Arquivo: app/shared/compliance/audit_service.py

Classe: AuditService | Métodos: log_decision, log_output, log_decision_in_session
8 decision types registráveis
Append-only: registros NUNCA podem ser alterados
Retenção: RETENTION_PERIODS por tipo de evento — até 2555 dias (7 anos)
  para SOX (ex.: company_settings_change=2555); demais tipos variam
  (≈730-1825 dias). A faixa "2-5 anos" de versões anteriores
  subestima os tipos SOX de 7 anos (ver D-07)
record_human_review: registra overrides humanos

O que é registrado:
  - Request original (mascarado)
  - FairnessGuard results (L1/L2/L3)
  - PII masks aplicados
  - LLM response completa
  - FactChecker flags
  - Scores + bias audit
  - Decisão final + motivo

Status de ativação por etapa:
  ● Ativo em TODAS as etapas: auth.py, jd_generation.py,
    wsi_questions.py, sourcing_react_agent.py, pipeline.py,
    approvals.py, communication.py, rubric_evaluation.py,
    scheduling.py
```

---

## SEÇÃO TRANSVERSAL: INTELIGÊNCIA

### 1. Learning Loop (Captura Silenciosa)

```
Arquivo: app/shared/learning/learning_loop_service.py (1137 linhas)
Mecanismo: Observa accept/modify/reject do recrutador sem pedir feedback
Outcomes: accepted | modified | rejected | ignored
Pattern Types: salary_preference, skill_preference, benefit_preference,
               work_model_preference, screening_preference,
               jd_style_preference, source_trust
Confidence: ≥20 samples=high, ≥10=medium, ≥5=low
FairnessGuard: validate_learning_batch() bloqueia discriminação ANTES de persistir
ModelDrift: trigger automático quando feedback rejected/ignored
Snapshot: learning_snapshot_service salva snapshot pré-learning (rollback Z2-01)

Etapas ativas: E2, E3, E4, E5, E7, E8, E9
```

### 2. A/B Testing

```
Arquivo: app/shared/learning/ab_testing_service.py (307 linhas)
Mecanismo: Hash-based traffic splitting (MD5 → bucket 0-9999)
Estatísticas: z-score, p-value (erfc), 95% CI, improvement %
Significância: p < 0.05 AND |improvement| > 5%
Modelo: PromptVariant + ABTestResult
API: GET/POST testes + GET variant via api/v1/ab_testing.py
seed_email_ab_tests: 3 experimentos criados no startup

Etapas ativas: E2, E3, E4, E6, E7, E9
```

### 3. Routing Adaptativo

```
Arquivo: app/domains/analytics/services/routing_learning_service.py
  (também em app/shared/services/routing_learning_service.py)
Mecanismo: Quando recrutador corrige roteamento, ajusta multipliers
Range: 0.8x (muitos erros) a 1.2x (alta precisão) por domínio
Método: compute_domain_confidence_adjustments(company_id, db)

Etapas ativas: E4, E5, E8
```

### 4. Template Learning

```
Arquivo: app/shared/learning/template_learning_service.py
Mecanismo: Após 3 vagas similares (mesmo setor/seniority), gera template
Métodos: learn_from_job_creation(), suggest_templates_for_improvement()
UNION de fontes corrigida (email + JD + feedback)

Etapas ativas: E2, E6, E9
```

### 5. Calibration

```
Arquivo: app/domains/analytics/services/calibration_service.py
Mecanismo: Dual feedback
  Explícito: thumbs up/down do recrutador
  Implícito: avançar candidato low-score = sinal positivo
Output: CalibrationSuggestion (ex: "Reduzir peso de skill técnica em 15%")
Métodos: record_explicit_feedback(), record_implicit_feedback(), generate_suggestions()

Etapas ativas: E4, E5, E7, E8
```

### 6. Score Normalization

```
Arquivo: app/domains/cv_screening/services/score_normalization_service.py
Mecanismo: Ajusta scores baseado no difficulty_coefficient da versão do questionário
Objetivo: Candidatos com versões mais difíceis não penalizados

Etapas ativas: E4, E7
```

### 7. Predictive Analytics

```
Arquivo: app/domains/analytics/services/predictive_analytics_service.py
        + app/services/ml/outcome_predictor.py
API: app/api/v1/predictive_analytics.py
Agent Tools: predictive_tools.py — integrado em agentes

Métodos:
  predict_time_to_fill(db, job_data, company_id) → dias + confidence
  predict_optimal_salary(db, job_data, company_id) → faixa competitiva
  predict_skill_success(db, skill_name, company_id) → probabilidade

Etapas ativas: E2, E4
```

### 8. Model Drift

```
Arquivo: app/shared/observability/model_drift_service.py
  (também em app/domains/ai/services/ e app/shared/services/)
4 dimensões monitoradas (janela de 7 dias):
  Score Drift: variação > 0.5 pts
  Approval Drift: variação > 10 p.p.
  Cost Drift: aumento significativo de custo LLM
  Latency Drift: degradação de tempo de resposta
Trigger: automático pelo Learning Loop quando feedback negativo acumula
Batch: drift.run_batch — diário 06h Brasília (Celery Beat)
Alerta: 1 trigger=WARNING, 2+=URGENT → Bell + Teams

Etapas ativas: E4, E5, E7, E8
```

### 9. Conversation Memory

```
Arquivo: app/shared/memory/conversation_state.py
Mecanismo: Estado efêmero da sessão de chat
Recursos:
  Entity tracking (última vaga, último candidato mencionado)
  Pronoun resolution ("conte mais sobre ele" → resolve)
  Active filters tracking (filtros persistem na sessão)

Etapas ativas: E2, E3, E4, E5, E6, E7
```

### 10. Semantic Search

```
Arquivo: app/shared/intelligence/semantic_search_service.py
Provider: Gemini text-embedding-004 (768 dimensões)
Cache: Redis para evitar re-embedding
Domínios: Skills, Job Titles, Industries, Locations
Métodos: expand_query(domain, query), expand_skills(), expand_job_titles()
Embedding Service: app/shared/intelligence/embedding_service.py

Etapas ativas: E2, E3, E4
```

### 11. Voice Analysis

```
Arquivo: app/domains/cv_screening/services/voice_service.py
  (também em app/domains/voice/services/ e app/shared/services/)
STT Providers: Deepgram (primário), Whisper (fallback)
TTS Provider: OpenAI (voice="nova")
Uso: Triagem WSI por voz — candidato responde por áudio
WSIVoiceOrchestrator: coordena triagem por voz

Etapas ativas: E7
```

### 12. Long-Term Memory

```
Arquivo: libs/agents-core/lia_agents_core/long_term_memory.py
Mecanismo: Episódios + compressão LLM após 30 dias
Integração:
  EnhancedAgentMixin._post_loop_learning: salva learnings após cada ReAct loop
  _get_memory_context: enriquece system prompt com memórias históricas
Background processing via Celery tasks

Etapas ativas: E4, E8, E9A, E9B
```

---

## SEÇÃO TRANSVERSAL: LGPD / DATA PROTECTION

### Consent Flow

```
Arquivo: NÃO existe app/api/v1/lgpd.py. Os fluxos LGPD vivem em:
  app/api/v1/lgpd_compliance.py, app/api/v1/admin_lgpd.py,
  app/api/v1/data_subject_requests.py, app/api/v1/data_request.py,
  app/api/public/candidate_portal.py (portal público)
  + app/api/v1/communication_optout.py (opt-out HMAC)
  + domínio app/domains/lgpd/ (repos + services) (ver D-08)

1. Consentimento para triagem WSI:
   WelcomeCard com checkbox explícito obrigatório
   Botões desabilitados até aceite LGPD
   ConsentEvent auditável registrado

2. Consentimento para contato:
   CandidateChannelSelector.select_channels verifica:
   → LGPDConsent (consentimento registrado por canal)
   → CandidateOptOut (opt-out por canal)
   WhatsApp: estado AWAITING_CONSENT com mensagem explícita
   Sem consentimento → canal bloqueado

3. Opt-out em emails:
   Link obrigatório em todo email
   HMAC-signed tokens (anti-tampering)
   ConsentEvent auditável: revogação registrada
```

### DSR — Data Subject Requests

```
Rotas DSR reais (auditadas 03/06/2026). NÃO existe app/api/v1/lgpd.py —
mas existe o PREFIXO /api/v1/lgpd (em lgpd_compliance.py). Mapa por arquivo:

  data_subject_requests.py — prefixo /api/v1/data-subject-requests
    POST /                        criar pedido — REQUER JWT; company_id vem do
                                  JWT (payload data.company_id IGNORADO,
                                  anti cross-tenant) + rate-limit por IP
    GET  /track/{request_id}      acompanhar status — REQUER JWT; tenant-scoped
                                  via get_by_id_and_company + RLS
    GET  / | GET /{request_id}    listar / detalhar (interno)
    PUT  /{request_id}/assign | /verify-identity | /process |
         /complete | /reject      ciclo de atendimento do DSR
    Tipos (schemas/data_subject_requests.py): ACCESS, CORRECTION,
    DELETION, PORTABILITY, OBJECTION, RESTRICTION, EXPLANATION (Art. 18)

  candidate_portal.py — prefixo /api/public/portal/data-request
    GET /{token} · POST /{token}/request-otp · /verify-otp ·
    /submit · /upload   (portal do titular por token + OTP)

  data_request.py — prefixo /api/v1/data-requests
    Config recrutador-side de COLETA de dados (config/templates/fields/
    triggers por vaga/WhatsApp) — não é o canal DSR do titular.

  lgpd_compliance.py — prefixo /api/v1/lgpd
    /stats · /dpo* · /breaches* (ANPD) · /decisions* (revisão humana
    de decisão automatizada) · /schedule-deletion · /run-cleanup

  communication_optout.py — /api/v1/communication/unsubscribe/{token}
    opt-out de email com token HMAC-assinado

  Portabilidade (Art. 18 V): dsr_export_service.generate_portability_json.

Status: endpoints implementados ●. Integração ponta-a-ponta do portal
público (/portal/data-request/[token]) ainda NÃO verificada E2E — ver checklist.
```

### Data Minimization

```
Princípios aplicados:
  1. ICS Calendar: apenas dtstart/dtend/summary/location/attendee
     Sem dados sensíveis do candidato
  2. ATS Sync: ATSSyncService filtra dados sensíveis (salário)
     "Dado sensível - não sincronizar"
  3. Feedback: PipelineFeedbackTool._remove_score_references
     Strip scores numéricos do feedback ao candidato
  4. PII Masking: regex + NER Presidio pré-LLM
     PII real minimizada antes do LLM (best-effort; nome ligado por padrão)
  5. ToonService: anonymize=True para visualização anônima
```

### Retenção por Tipo de Dado

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  Tipo de Dado              │ Retenção        │ Base Legal                    │
│───────────────────────────┼─────────────────┼───────────────────────────────│
│  Audit Trail (SOX)         │ 730-1825 dias   │ SOX compliance, Art. 12 LGPD │
│  Scores WSI                │ Duração processo│ Legítimo interesse            │
│  Dados de candidato (PII)  │ Até revogação   │ Consentimento                 │
│  Logs de comunicação       │ 365 dias        │ Legítimo interesse            │
│  Embeddings de perfil      │ Indefinido      │ Anonimizados (sem PII)        │
│  Learning patterns         │ Indefinido      │ Agregados (sem PII individual)│
│  LLM prompts/responses     │ 90 dias         │ Auditoria + melhoria          │
│  Conversation memory       │ Sessão          │ Efêmero                       │
│  Long-term memory          │ Compressão 30d  │ Anonimizado                   │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## MAPA CONSOLIDADO DE AGENTES

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  MAPA DE AGENTES — ALPHA 1                                                    │
│                                                                               │
│  Ag.0 MainOrchestrator                                                        │
│    Classe: MainOrchestrator                                                   │
│    Domínio: orchestrator                                                      │
│    LLM: Gemini (CascadedRouter T5)                                           │
│    Tools: CascadedRouter (6-tier), ActionExecutor, PendingAction             │
│    Etapas: E5, E6, E7 (coordenação geral)                                   │
│    FG: L1+L2 (pré-roteamento) | Anti-Sycophancy: ORCHESTRATOR               │
│                                                                               │
│  Ag.2 SourcingReActAgent                                                      │
│    Classe: SourcingReActAgent (LangGraphReActBase + EnhancedAgentMixin)       │
│    Domínio: sourcing                                                          │
│    Registry: "sourcing"                                                       │
│    LLM: Gemini | max_iterations: 5 | max_tool_calls: 3                      │
│    Tools: 15 (search, analyze, compare, rank, outreach, generate_message)    │
│    Etapas: E4 (busca de candidatos)                                          │
│    FG: L1+L2+L3 | PII: ativo | Audit: ●                                    │
│                                                                               │
│  Ag.3 CV Screening — WSIScreeningPipeline / PipelineReActAgent                │
│    (NÃO existe classe "TriagemCurricular"; ver D-09)                          │
│    Domínio: cv_screening                                                      │
│    LLM: Gemini                                                                │
│    Etapas: E4 (triagem curricular na busca)                                  │
│    FG: L1+L2+L3 | PII: ativo | Fact-Check: ativo | Audit: ●                │
│                                                                               │
│  Ag.4 WSIInterviewGraph                                                       │
│    Classe: WSIInterviewGraph (LangGraph StateGraph)                          │
│    Domínio: cv_screening                                                      │
│    LLM: Gemini | 8 stages | Bloom+Dreyfus+BigFive                           │
│    HITL: interrupt_before=["lg_generate_feedback"]                           │
│    Checkpoint: PostgresSaver (sessões 30-120 min)                            │
│    Etapas: E7 (conduz entrevista WSI), E7B (feedback pós-triagem)            │
│    FG: L1+L2+L3 | PII: ativo | Fact-Check: ativo | Audit: ●                │
│                                                                               │
│  Ag.5 WSIService (Scoring)                                                    │
│    Classe: WSIService + WSIDeterministicScorer                                │
│    Domínio: cv_screening                                                      │
│    LLM: SEM LLM (determinístico — zero latência, zero custo)                 │
│    Etapas: E4 (score WSI na busca), E7 (calcula score final)                 │
│    ScoreNormalization: difficulty_coefficient ativo                           │
│                                                                               │
│  Ag.6 InterviewGraph                                                          │
│    Classe: InterviewGraph (LangGraph StateGraph)                             │
│    Domínio: interview_scheduling                                              │
│    LLM: Gemini | 6 nós                                                       │
│    Tools: schedule_interview, check_availability, reschedule, cancel         │
│    Etapas: E9A (agendar entrevista)                                          │
│    CircuitBreaker: "google_calendar"                                         │
│                                                                               │
│  Ag.7 CommunicationReActAgent + PersonalizedFeedbackService                  │
│    Classes: CommunicationReActAgent (ReAct) + PersonalizedFeedbackService    │
│    Domínios: communication + cv_screening                                    │
│    LLM: Gemini | max_iterations: 5                                           │
│    Tools: send_email, send_whatsapp, get_history, schedule_message           │
│    Etapas: E5 (feedback rejeição Gate 1), E6 (contato email),               │
│            E8 (feedback Gate 2), E9B (feedback reprovado)                    │
│    FG: L1+L2 | LGPD: opt-out obrigatório                                    │
│                                                                               │
│  Ag.8 ATSIntegrationReActAgent ⚠ PÓS-MVP                                   │
│    Classe: ATSIntegrationReActAgent                                           │
│    Domínio: ats_integration                                                   │
│    LLM: Gemini                                                                │
│    Tools: sync_candidate_to_ats, fetch_candidate_from_ats, validate_fields   │
│    Etapas: E2 (sync ATS), E5 (sync status), E8 (sync status)                │
│    Status: Código existe, depende de credenciais de produção                 │
│                                                                               │
│  SERVIÇOS AUXILIARES (sem rótulo Ag.):                                        │
│                                                                               │
│  WSIQuestionGenerator / WSIScreeningQuestionGenerator                         │
│    Domínio: cv_screening | LLM: Gemini                                       │
│    Etapas: E3 (gera perguntas WSI)                                           │
│                                                                               │
│  WSIScreeningPipeline                                                         │
│    Domínio: cv_screening | LLM: Gemini                                       │
│    Etapas: E4 (triagem/screening na busca)                                   │
│                                                                               │
│  WSIVoiceOrchestrator                                                         │
│    Domínio: cv_screening | LLM: Gemini + Deepgram + OpenAI TTS              │
│    Etapas: E7 (triagem por voz)                                              │
│                                                                               │
│  JobDescriptionGeneratorService                                              │
│    Domínio: job_management | LLM: Claude (Anthropic)                         │
│    Etapas: E2 (gera JD), E3 (JD como base para WSI)                         │
│                                                                               │
│  PipelineTransitionAgent                                                      │
│    Classe: PipelineTransitionAgent (LangGraphReActBase + EnhancedAgentMixin) │
│    Domínio: pipeline | LLM: Gemini                                           │
│    Invocação: POST /api/v1/pipeline/interpret-context (direta)               │
│    Tools: 20 | Etapas: E5, E8 (transições de pipeline)                       │
│                                                                               │
│  WizardReActAgent                                                             │
│    Registry: "wizard" | Domínio: job_management | LLM: Gemini               │
│    6 stages: input-evaluation → jd-enrichment → salary → competencies →      │
│              wsi-questions → review-publish                                   │
│    Tools: 10 | Etapas: E2, E3 (criação/edição de vagas)                      │
│                                                                               │
│  KanbanReActAgent                                                             │
│    Registry: "kanban" | Domínio: recruiter_assistant | LLM: Gemini           │
│    Tools: 22 (maior número) | Etapas: E5, E8 (Kanban board)                 │
│                                                                               │
│  TalentFunnelReActAgent                                                       │
│    Classe: TalentFunnelReActAgent (talent_funnel_react_agent.py)             │
│    Registry: "talent_funnel" | Domínio: recruiter_assistant | LLM: Gemini    │
│    NÃO existe "TalentReActAgent" nem registry "talent" (ver D-02)            │
│    Tools: 13 | Stages: discovery → analysis → action_planning               │
│    Etapas: E4 (funil de talentos)                                            │
│                                                                               │
│  PolicyReActAgent                                                             │
│    Registry: "policy" | Domínio: hiring_policy | LLM: Gemini                │
│    Tools: 13 | Setup wizard por blocos                                       │
│    Etapas: Transversal (configuração de políticas)                           │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Grafo de Dependências

```
                    ┌──────────────┐
                    │    Ag.0      │
                    │ Orchestrator │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼────┐ ┌────▼─────┐ ┌────▼─────┐
        │  Ag.2    │ │  Ag.4   │ │  Ag.8   │
        │ Sourcing │ │Entrev.  │ │ ATS Int.│
        └─────┬────┘ │  WSI    │ └────┬────┘
              │      └────┬────┘      │
              │           │           │
        ┌─────▼────┐ ┌────▼─────┐    │
        │  Ag.3    │ │  Ag.5   │    │
        │ Triagem  │ │Avaliador│    │
        │Curricular│ │  WSI    │    │
        └──────────┘ └────┬────┘    │
                          │         │
                    ┌─────▼────┐    │
                    │  Ag.7    │◄───┘
                    │Analista  │
                    │Feedback  │
                    └─────┬────┘
                          │
                    ┌─────▼────┐
                    │  Ag.6    │
                    │Scheduling│
                    └──────────┘
```

---

## CHECKLIST PRAGMÁTICO MVP — ROADMAP ALPHA 1

### Para quem é esta seção
Time de feature: devs, PO, QA. Lista o que falta construir, ativar ou integrar para o fluxo E1 → E9B funcionar end-to-end. Para itens de operação/legal/billing, ver a próxima seção (Product Readiness — Go-Live).

### Como usar
Cada item usa `- [ ]` (markdown checkbox) e referencia a etapa (E1, E2, …, E9B) ou camada transversal de origem (Compliance, Inteligência, Governança, LGPD). Itens vindos do corpo do documento mantêm o símbolo original (⚠ bloqueante · ○ a implementar · ◐ a configurar/ativar). Itens identificados nesta consolidação têm tag `(novo)` para o time saber que vieram da auditoria e não estão no corpo do documento.

### Índice
- [1. Pré-MVP — Bloqueantes](#1-pré-mvp--bloqueantes)
- [2. MVP por Etapa (E1 → E9B)](#2-mvp-por-etapa-e1--e9b)
- [3. Camadas Transversais](#3-camadas-transversais)
- [4. Pós-MVP](#4-pós-mvp)
- [5. QA & Testes](#5-qa--testes)

### 1. Pré-MVP — Bloqueantes
Sem isso o MVP não pode subir.

- [ ] **(novo · E0/Pré-Login) Onboarding de tenant + RBAC + isolamento multi-tenant verificável** — fluxo para criar uma empresa nova na plataforma, com papéis (admin, recrutador, operador), separação dos dados de cada cliente comprovada por teste. Sem isso não dá para receber o primeiro cliente real.
- [ ] **(novo · Compliance) Bias Audit Dashboard (UI)** — o backend já coleta o `BiasAuditSnapshot` (Four-Fifths Rule), mas falta a tela onde recrutador/PO veem se algum grupo demográfico está sendo aprovado <80% que outro. (ver também: Product Readiness · Transparência IA)
- [ ] **(novo · LGPD) Portal público DSR ponta-a-ponta** — `/portal/data-request/[token]` precisa funcionar de verdade: candidato consegue pedir cópia, correção ou exclusão dos próprios dados sem depender de email manual. Endpoints existem mas integração está pendente (○ na seção LGPD).
- [ ] **(novo · LGPD) Verificação automática de retenção de dados** — rotina (cron/Celery Beat) que aplica os prazos da tabela "Retenção por Tipo de Dado" (audit 730-1825d, logs 365d, prompts 90d, etc.) e apaga/anonimiza o que vencer. Sem isso a tabela é só intenção.
- [ ] **(E5/E8 · ⚠ FairnessGuard L3 obrigatório por setor)** ALPHA1_SECTOR_RULES exige L3 ativo para tech, financeiro, saúde e RPO — confirmar que o pré-check do `PipelineTransitionAgent` realmente bloqueia (não só alerta) nas rejeições desses setores antes do go-live do MVP.

### 2. MVP por Etapa (E1 → E9B)

#### E1 — Login
- [ ] **(novo) Onboarding self-service básico de tenant** — sem isso, cada cliente novo precisa de provisionamento manual no primeiro login. (ver também: Product Readiness · Cliente & Suporte)
- [ ] **(novo) Mensagem clara de erro quando WorkOS SSO está fora** — circuit "workos" abre (failure_threshold=5) e o usuário precisa entender o que aconteceu. Hoje só temos a degraded message genérica.

#### E2 — Editar/Criar Vaga
- [ ] **(⚠ PÓS-MVP — confirmar fora do MVP) Ag.8 ATSIntegrationReActAgent sincroniza dados do ATS** (linhas 173 e 1862) — está fora do escopo Alpha 1; manter desligado e bloquear UI que dependa disso.
- [ ] **(IMPORTANTE — NÃO IMPLEMENTADO, só PÓS-MVP) Steps 2, 3, 4, 5 do detalhamento técnico de E2** (linha 210) — DomainOrchestrator routing + GuardrailCheck para job_management, EnhancedAgentMixin com 16 capabilities, FairnessGuard pré-LLM no JD, PII Masking pré-LLM. Hoje a geração de JD funciona "à parte" sem passar por essas camadas. Sem isso o JD pode subir com viés ou vazar PII para o LLM.
- [ ] **(◐/●) LearningLoop em E2 — captura silenciosa de edições do recrutador no JD** — listado como ● mas marcado "NÃO APLICAVEL AINDA" (linha 268). Decidir se fica ou se sai do MVP de E2.
- [ ] **(◐/●) TemplateLearning — auto-template após 3 vagas similares** — listado como ● mas marcado "(NAO APLICAVEL AINDA)" (linha 269). Decidir se fica ou se sai do MVP de E2.

#### E3 — Configurar Roteiro WSI
- [ ] **(MVP) Roteiro completo (≈12 perguntas) e compacto (≈7 perguntas) testados ponta-a-ponta** — confirmar que ambos os modos geram blocos Técnico (Bloom 1-6 + Dreyfus 1-5), Comportamental (Big Five), Situacional e Cultural Fit conforme `wsi_constants.py`.
- [ ] **(MVP) FactChecker e FairnessGuard L1/L2 efetivamente bloqueiam perguntas ruins** — não só alertam. Garantir que pergunta com viés ou claim incoerente nunca chega ao candidato.

#### E4 — Buscar Candidatos (Funil de Talentos)
- [ ] **(MVP) Like/Dislike por candidato realmente alimenta LearningLoop e RoutingAdaptativo** — verificar que o sinal chega aos serviços (`learning_loop_service`, `routing_learning_service`) e altera ranking nas próximas buscas.
- [ ] **(MVP) Os 5 modos de busca funcionam (IA Natural, Boolean, Perfil Similar, Job Description, Archetypes)** — cobertura mínima E2E por modo.
- [ ] **(novo) Mensagens claras de fallback quando Pearch (circuit "pearch") está aberto** — usuário precisa entender que está vendo só a base local naquele momento.

#### E5 — Aprovar Mapeados (Gate 1)
- [ ] **(MVP) Aprovação em massa (até 100) respeita PolicyEngine + LGPDConsent + opt-out** — testar com lote real, não só caso unitário.
- [ ] **(MVP) Bypass automático de candidatos inscritos via web (⚡ Inscritos via web BYPASS Gate 1) sem perder consentimento LGPD nem rate limit.**
- [ ] **(⚠ PÓS-MVP) Ag.8 ATSIntegrationReActAgent — sync de status de volta ao ATS** — manter fora do MVP, mas confirmar que UI não tenta acionar.

#### E6 — Contato via Email + Follow-up
- [ ] **(◐) Follow-up automático de 7 dias (re-envio cada 24h, status "sem_resposta")** — confirmar Celery Beat rodando em produção e mensagem para consultor disparando via Teams.
- [ ] **(◐) A/B Testing de templates de email já seedado no startup (3 experimentos)** — verificar que o `seed_email_ab_tests` rodou e que `record_result` está sendo chamado nos eventos de open/click/reply.
- [ ] **(novo · UX) Acessibilidade WCAG e responsividade mobile do email/chat WSI** — candidato pode estar respondendo do celular; testar a régua mínima A/AA.

#### E7 — Triagem WSI
- [ ] **(MVP) Sessão WSI de 30-120 min sobrevive a desconexão via PostgresSaver checkpoint** — testar retomada real (refresh, fechar aba, voltar pelo link).
- [ ] **(novo) Backup do PostgresSaver — política de snapshot dos checkpoints WSI** — sessões longas não podem ser perdidas se o Postgres tiver hiccup.
- [ ] **(MVP) Triagem por voz (WSIVoiceOrchestrator + Deepgram + OpenAI TTS) testada nos 3 canais** (chat web, WhatsApp, voz) com fallback Whisper.
- [ ] **(MVP) FactChecker (4 tipos) e BiasAuditSnapshot (Four-Fifths) ativos pós-LLM em todas as triagens.**
- [ ] **(novo · UX) Acessibilidade WCAG na página `/triagem/[token]` revisada para AA** — `aria-live`, `aria-label`, `motion-reduce` já existem (Audit Fase 6), mas falta passada formal.

#### E7A — Triagem Abandonada
- [ ] **(MVP) 1º lembrete em 48h sem atividade + 2º lembrete em +48h + alerta ao consultor** — confirmar Celery Beat e canal Teams.
- [ ] **(MVP) Progresso parcial salvo de verdade** — candidato volta exatamente do ponto onde parou.

#### E7B — Feedback Pós-Triagem
- [ ] **(MVP) Score numérico nunca aparece no feedback enviado ao candidato** — confirmar `PipelineFeedbackTool._remove_score_references` no caminho real.
- [ ] **(MVP) HITL `interrupt_before=["lg_generate_feedback"]` está ativo e o consultor consegue revisar antes do envio.**

#### E8 — Aprovar/Reprovar Triados (Gate 2)
- [ ] **(MVP) FG L3 + auto-check de `reject_candidate` realmente bloqueiam motivos discriminatórios em rejeição (não só alertam).**
- [ ] **(MVP) Embedding de re-discovery do reprovado é gerado e indexado para futuras vagas.**
- [ ] **(⚠ PÓS-MVP) Ag.8 sync de status Gate 2 → ATS** — fora do MVP.

#### E9A — Agendar Entrevista
- [ ] **(MVP) Ag.6 InterviewGraph: 6 nós funcionando, fallback Teams quando Google Calendar não tem horário.**
- [ ] **(MVP) ICS Calendar invite gerado com data minimization (só dtstart/dtend/summary/location/attendee — sem PII do candidato).**
- [ ] **(MVP) Comunicação multi-canal (email + WhatsApp) com confirmação de entrega.**

#### E9B — Enviar Feedback (Reprovado)
- [ ] **(MVP) PersonalizedFeedbackService gera feedback construtivo seguindo o template determinístico (linhas 1007 e 1072) — sem alucinar dados, sem score numérico.**
- [ ] **(MVP) FairnessGuard sanitiza o texto antes do envio.**
- [ ] **(MVP) Embedding de perfil salvo via `embedding_cache_service.py` para re-discovery futuro.**

### 3. Camadas Transversais

#### Compliance — FairnessGuard, PII, FactChecker, BiasAudit, AuditTrail
- [ ] **(◐ → ●) Ativar FairnessGuard L3 em 100% dos setores listados como `ativo` em `ALPHA1_SECTOR_RULES`** (tech, financeiro, saude, rpo) e confirmar fallback explícito em varejo/logística.
- [ ] **(◐) Cobertura PII Masking — auditar que 100% das chamadas LLM passam por `strip_pii_for_llm_prompt`** — pré-condição para LGPD. (ver também: Product Readiness · Segurança Operacional)
- [ ] **(○) Bias Audit Dashboard — UI de visualização do BiasAuditSnapshot** (linha 1533: "○ pendente — backend coleta dados"). (ver também: Product Readiness · Transparência IA)
- [ ] **(MVP) AuditTrail SOX-compliant ativo nos 9 endpoints já listados** (auth, jd_generation, wsi_questions, sourcing_react_agent, pipeline, approvals, communication, rubric_evaluation, scheduling).
- [ ] **(MVP) PromptInjectionGuard ativo em todo request que chega ao DomainOrchestrator** — confirmar logs de tentativa.

#### Inteligência — Learning, A/B, Calibration, Drift, Memória, Semantic, Voice
- [ ] **(MVP) Learning Loop — `validate_learning_batch()` bloqueia patterns discriminatórios ANTES de persistir** — `_LEARNING_PROTECTED_FIELDS` cobre gender, age, ethnicity, marital_status, photo, institution, address, religion, disability, cv_gaps.
- [ ] **(MVP) Model Drift batch diário (06h Brasília) ativo nas 4 dimensões** (score, approval, cost, latency) com alerta Bell + Teams.
- [ ] **(MVP) Calibration dual feedback (explícito + implícito) gerando `CalibrationSuggestion` legível para o recrutador.**
- [ ] **(MVP) Long-Term Memory — compressão LLM após 30 dias rodando como Celery task.**
- [ ] **(MVP) Semantic Search (Gemini text-embedding-004 768-dim) com cache Redis funcional.**

#### Governança — Policy Engine, CircuitBreaker, PromptInjection, AntiSycophancy
- [ ] **(MVP) Policy Engine — `ALPHA1_SECTOR_RULES` carregado para 6 setores** (tech, financeiro, saude, rpo, varejo, logistica) com autonomia/HITL/L3/rate limit/escalation por setor.
- [ ] **(MVP) Os ~22 circuits do CircuitBreaker (anthropic, openai, deepseek, gemini, pearch, apify, apify_search, workos, merge, google_calendar, gupy, pandape, mailgun, resend, iugu, vindi, twilio_voice, gemini_live, deepgram, openmic, rails_api — NÃO existe "sendgrid"; ver D-06) com mensagem PT-BR de degraded mode.**
- [ ] **(MVP) Anti-Sycophancy — 3 variantes (OPERATIONAL, FULL, ORCHESTRATOR) injetadas nos system prompts dos agentes corretos** (Crença #11 do Manifesto WeDOTalent).
- [ ] **(novo) Feature flags / rollout por setor** — habilitar/desabilitar regras por tech/financeiro/saúde/RPO conforme `ALPHA1_SECTOR_RULES` sem precisar de deploy.

#### LGPD — Consent, DSR técnico, Data Min, Retenção
- [ ] **(MVP) Consentimento WSI obrigatório no WelcomeCard** — botão desabilitado até checkbox marcado, `ConsentEvent` auditável registrado.
- [ ] **(MVP) Opt-out HMAC-signed em 100% dos emails** com `ConsentEvent` registrando revogação.
- [ ] **(○) Portal público DSR (`/api/public/portal/data-request/{token}`) verificado E2E** — rotas DSR reais: `POST /api/v1/data-subject-requests` + `GET /.../track/{id}` (ambas requerem JWT) e o portal do titular por token+OTP (ver seção transversal LGPD/DSR). Atenção: os caminhos `/api/v1/lgpd/data-export|data-delete|consent` **NÃO existem**. (ver também: Product Readiness · Legal & Compliance)
- [ ] **(MVP) Data Minimization aplicada em ICS, ATS sync, feedback, PII Masking, ToonService anonymize.**
- [ ] **(novo) Verificação automática dos prazos da tabela "Retenção por Tipo de Dado"** — sem isso é só promessa.
- [ ] **(novo · Observabilidade básica) Prometheus dashboards por etapa + alertas configurados** — base para qualquer SLA. (ver também: Product Readiness · Confiabilidade & Operação)

### 4. Pós-MVP
Itens explicitamente marcados no documento como pós-MVP — manter visíveis mas FORA do escopo Alpha 1.

- [ ] **(⚠ PÓS-MVP) Ag.8 ATSIntegrationReActAgent** completo (E2 sync de dados, E5 sync de status, E8 sync de status) — linhas 48, 173, 1862.
- [ ] **(NÃO IMPLEMENTADO, só PÓS-MVP) Steps técnicos 2-5 do fluxo E2** com DomainOrchestrator/EnhancedAgentMixin/FairnessGuard/PII Masking integrados ao job_management — linha 210.
- [ ] **(NAO PRIORITARIO — POS MVP) A/B Testing avançado de templates de email em E6** — linha 688. O básico (seed_email_ab_tests) já está in.
- [ ] **(NAO APLICAVEL AINDA) TemplateLearning auto-template após 3 vagas similares em E2** — linha 269.
- [ ] **(NAO APLICAVEL AINDA) LearningLoop captura silenciosa de edições em E2** — linha 268.

### 5. QA & Testes
- [ ] **(novo) Plano consolidado de testes E2E por etapa (E1 a E9B)** — um cenário "happy path" + um cenário "fairness block" + um cenário "circuit breaker open" por etapa, no mínimo.
- [ ] **(MVP) Teste E2E de E7 (Triagem WSI)** — sessão de 30-120 min com PostgresSaver, abandono e retomada, finalização com score.
- [ ] **(MVP) Teste E2E de E5 + E8 (Gates)** — aprovação individual, em massa (≤100), drag-and-drop, rejeição com motivo discriminatório (deve bloquear).
- [ ] **(MVP) Teste E2E de E6** — envio, abertura, clique, opt-out, follow-up de 7 dias.
- [ ] **(MVP) Teste E2E de E4** — busca nos 5 modos com Like/Dislike alimentando LearningLoop.
- [ ] **(MVP) Teste E2E de E9A** — agendamento com Google Calendar, ICS sem PII, comunicação dual canal.
- [ ] **(MVP) Teste de regressão de FairnessGuard L1/L2/L3 + PII Masking + AuditTrail** — qualquer mudança em capability transversal precisa quebrar este conjunto se a cobertura cair.

---

## CHECKLIST PRODUCT READINESS — GO-LIVE

### Para quem é esta seção
Time de operação: SRE/Plataforma, PM, Suporte, Legal, Financeiro, Comercial. Lista o que precisa estar pronto para operar em produção com clientes pagantes — independente das features do fluxo, que estão na seção MVP acima.

### Como usar
Cada item usa `- [ ]` (markdown checkbox). Itens vindos desta consolidação têm tag `(novo)` para o time saber que vieram da auditoria e não estão no corpo do documento. Estes itens são para operar/atender/cobrar/cumprir contrato — não são features do fluxo E1 → E9B.

### Índice
- [1. Confiabilidade & Operação](#1-confiabilidade--operação)
- [2. Cliente & Suporte](#2-cliente--suporte)
- [3. Comercial & Billing](#3-comercial--billing)
- [4. Legal, Compliance & Transparência IA](#4-legal-compliance--transparência-ia)
- [5. Segurança Operacional](#5-segurança-operacional)

### 1. Confiabilidade & Operação

- [ ] **(novo) SLO/SLA por etapa definidos e publicados** — pelo menos: P95 latência E7 (triagem WSI), disponibilidade E1 (login), P95 E4 (busca), P95 E6 (envio de email). Sem isso, suporte e comercial não conseguem prometer nada.
- [ ] **(novo) On-call rotation + escalation policy ativa** — quem é chamado de madrugada, qual a ferramenta de paging (PagerDuty/Opsgenie), qual o tempo de resposta esperado.
- [ ] **(novo) Incident response: template de post-mortem + war-room runbook + comunicação ao cliente** — formato padrão para escrever post-mortem público sem entrar em pânico.
- [ ] **(novo) Runbooks operacionais por circuit breaker** — um runbook curto ("o que fazer quando o circuit X abre") para cada um dos ~22 circuits reais (anthropic, openai, deepseek, gemini, pearch, apify, apify_search, workos, merge, google_calendar, gupy, pandape, mailgun, resend, iugu, vindi, twilio_voice, gemini_live, deepgram, openmic, rails_api; ver D-06 — "sendgrid" não existe).
- [ ] **(novo) Runbook de recuperação WSI** — passo-a-passo para retomar checkpoint WSI interrompido (PostgresSaver) e re-engajar candidato sem perder a sessão.
- [ ] **(novo) Disaster Recovery: RTO/RPO definidos + teste periódico de restore** — não basta ter backup, precisa ter o ensaio. Sem isso o cliente não confia no SLA.
- [ ] **(novo) Logs centralizados — agregador único, retenção definida e busca rápida** — hoje os logs estão por workflow; em produção precisam estar agregados (ex: Loki, ELK, Datadog) com retenção compatível com a tabela LGPD (audit 730-1825d, logs comunicação 365d).
- [ ] **(novo) Capacity planning + load test executado e registrado** — número de tenants suportados, P95 sob carga, throughput de triagens WSI por minuto.
- [ ] **(novo) Status page pública + assinatura por cliente** — clientes precisam ver "estou caindo ou é só eu?" sem ligar para suporte.

### 2. Cliente & Suporte

- [ ] **(novo) Onboarding self-service de novo tenant** — criar empresa, importar primeira vaga, primeiro convite ao recrutador, sem intervenção manual.
- [ ] **(novo) Suporte ao cliente — canais (email/chat/Teams), SLA de primeira resposta, base de conhecimento navegável.**
- [ ] **(novo) Treinamento de recrutadores — materiais escritos + vídeo curto + onboarding do consultor** — quem nunca usou a LIA precisa virar produtivo em 1 sessão.
- [ ] **(novo) Documentação pública — API docs versionada (OpenAPI / Swagger UI hospedado) + help center** com FAQ e troubleshooting.
- [ ] **(novo) Quota e consumo visíveis ao cliente no painel** — quantos tokens, quantos agentes, quantas automações já consumiu vs limite do plano.

### 3. Comercial & Billing

- [ ] **(novo) Billing real por plano Starter / Pro / Enterprise** — `PLAN_LIMITS_ENFORCE=true` já bloqueia consumo, mas falta cobrar de verdade (Iugu/Vindi via circuit breakers já existentes na arquitetura).
- [ ] **(novo) Visibilidade de custo por tenant (interno)** — quanto cada cliente está custando em LLM (Gemini, Claude), Pearch, Deepgram, OpenAI TTS — sem isso a margem é cega.
- [ ] **(novo) Versionamento de API + política de deprecation** — semver na rota (`/api/v1`, `/api/v2`) + janela mínima de descontinuação anunciada com antecedência. Pré-requisito para Ag.8 ATS integrar com clientes pós-MVP.
- [ ] **(novo) Entrega confiável de webhooks — DLQ, retry exponencial, assinatura HMAC, dashboard de falhas** — importante especialmente quando Ag.8 ATSIntegrationReActAgent for ativado pós-MVP.

### 4. Legal, Compliance & Transparência IA

- [ ] **(novo) Termos de Uso + Política de Privacidade aceitos no signup** — necessários antes do primeiro cliente pagante.
- [ ] **(novo) DPA (Data Processing Agreement) disponível para clientes corporativos** — exigência legal para B2B, especialmente em saúde e financeiro.
- [ ] **(novo) Página de Transparência IA — EU AI Act art. 13/14 + LGPD art. 20** — explicar para o candidato que ele está interagindo com IA, qual a lógica das decisões automatizadas e como pedir revisão humana. (ver também: MVP · Compliance · Bias Audit Dashboard)
- [ ] **(novo) Model cards dos LLMs em uso (Gemini, Claude, Deepgram, OpenAI TTS)** — capacidades, limitações, vieses conhecidos. Pré-requisito de transparência para EU AI Act.
- [ ] **(novo) Data residency declarada no contrato (BR / US)** — onde os dados ficam fisicamente armazenados. LGPD exige clareza.
- [ ] **(novo) Pen-test executado e relatório arquivado** antes do go-live.
- [ ] **(novo) Roadmap formal SOC2 / ISO 27001** — não precisa estar certificado no go-live, precisa ter o plano por escrito para responder a RFP de Enterprise.
- [ ] **(novo) DSR público (`/portal/data-request/[token]`) operacional** — interface visível ao titular dos dados, com SLA de resposta. (ver também: MVP · LGPD · DSR técnico)

### 5. Segurança Operacional

- [ ] **(novo) Rotação de secrets — política e calendário** para LLM keys (Gemini, Claude, OpenAI), JWT secret, WorkOS, Pearch, SendGrid, Resend, Twilio.
- [ ] **(novo) Kill-switch e feature flags com auditoria de mudança** — quem ligou/desligou o quê, quando, por quê. Pré-requisito para rollback rápido em produção.
- [ ] **(novo) Auditoria de cobertura de PII Masking em 100% das chamadas LLM** — script periódico que confirma que toda chamada LLM passou por `strip_pii_for_llm_prompt`. Sem isso o "regra absoluta: o LLM NUNCA vê dados pessoais reais" é só intenção. (ver também: MVP · Compliance)

---
---

## Divergências & Gaps (auditoria 03/06/2026)

> Apêndice gerado pela auditoria de código de 03/06/2026 (Task de documentação). Lista as divergências entre o que este documento afirmava e o que o código do `lia-agent-system` realmente faz. **Cada item é base para uma tarefa futura** — algumas exigem correção apenas no doc (já aplicada nesta v1.1, marcada ✅ Doc corrigido), outras exigem decisão de produto/engenharia (marcada ⚠ Requer decisão).
>
> Severidade: **Alta** = induz a erro em entendimento de arquitetura/segurança; **Média** = nome/caminho incorreto que quebra navegação no código; **Baixa** = imprecisão menor.

| ID | Componente | O que o doc dizia | O que o código faz | Severidade | Status |
|----|-----------|-------------------|--------------------|------------|--------|
| **D-01** | Orquestrador | Classe `DomainOrchestrator` | NÃO existe classe `DomainOrchestrator`. O orquestrador real é `MainOrchestrator` (`app/orchestrator/execution/main_orchestrator.py`) + `CascadedRouter`. "DomainOrchestrator" era nome conceitual | Média | ✅ Doc corrigido |
| **D-02** | Funil de Talentos | `TalentReActAgent`, registry `"talent"` | Classe real `TalentFunnelReActAgent` (`talent_funnel_react_agent.py`), registry `"talent_funnel"` | Média | ✅ Doc corrigido |
| **D-03** | Inventário de agentes | Rótulos `Ag.0–Ag.8` como mapa completo | Inventário canônico = **16 ReActAgents** (sentinela `test_tenant_aware_rollout_t_d.py`): 14 em `ALL_REACT_AGENTS_RUNTIME_PATH` + `CandidateSelfServiceAgent` + `PipelineTransitionAgent`. Os `Ag.x` são didáticos | Baixa | ✅ Doc corrigido (nota adicionada) |
| **D-04** | FactChecker | 4 tipos: experiência declarada, certificações, período na empresa, habilidades técnicas | 4 verificações reais (`_check_*` em `app/shared/compliance/fact_checker.py`): **salário, contagem de candidatos, percentuais, datas** + `verify_*` granulares + registry de validadores por domínio | Alta | ✅ Doc corrigido |
| **D-05** | EnhancedAgentMixin | "16 capabilities injetadas automaticamente" | 4 capabilities centrais no mixin (`libs/agents-core/lia_agents_core/enhanced_agent_mixin.py`): **Memory, Autonomy/Guardrails, Learning, Compliance** + 3 categorias de tools. PII Masking/AuditTrail/CircuitBreaker etc. atuam por camadas próprias, não como "16 capabilities" do mixin | Alta | ✅ Doc corrigido |
| **D-06** | CircuitBreaker | "14 circuits pré-configurados", incluindo `sendgrid` | `circuit_breaker.py` define **21 circuits**: anthropic, openai, deepseek, gemini, pearch, apify, apify_search, workos, merge, google_calendar, gupy, pandape, mailgun, resend, iugu, vindi, twilio_voice, gemini_live, deepgram, openmic, rails_api. **Não existe `sendgrid`** (→ `mailgun`); `llm_react_reason` é per-ReAct em runtime. Valores inline reauditados (LLMs 5/30s/60s; pearch+apify 3/60s/30s; apify_search 3/120s/300s; workos 5/30s/15s) — conferem | Alta | ✅ Resolvido (03/06/2026) |
| **D-07** | AuditTrail (retenção) | "730–1825 dias (~2–5 anos)" | `RETENTION_PERIODS` por tipo de evento, até **2555 dias (7 anos)** para tipos SOX (ex.: `company_settings_change`). A faixa antiga subestimava os tipos de 7 anos | Média | ✅ Doc corrigido |
| **D-08** | LGPD / DSR | Endpoints em `app/api/v1/lgpd.py` | **Não existe `app/api/v1/lgpd.py`**. Os fluxos LGPD vivem em `lgpd_compliance.py`, `admin_lgpd.py`, `data_subject_requests.py`, `data_request.py`, `app/api/public/candidate_portal.py`, `communication_optout.py` + domínio `app/domains/lgpd/`. Os caminhos/verbos exatos das rotas DSR estão mapeados na seção transversal LGPD/DSR deste doc | Alta | ✅ Resolvido (03/06/2026) |
| **D-09** | Ag.3 (CV Screening) | Classe `TriagemCurricular` | Não existe classe `TriagemCurricular`. CV screening usa `WSIScreeningPipeline` / `PipelineReActAgent` | Média | ✅ Doc corrigido |
| **D-10** | PII Masking | "4 camadas (CPF, nome, endereço, campos sensíveis)" | Camadas: regex direto (CPF/email/telefone/RG/CNPJ), quase-identificadores (idade/ano de formatura/endereço) e NER via Presidio. Mascaramento de **nome** (PERSON) agora ligado por padrão via Presidio + modelo spaCy PT (`pt_core_news_sm`, declarado em `requirements.txt`). **Bug corrigido:** `AnalyzerEngine()` sem `nlp_engine` tentava o modelo inglês e falhava em silêncio → nome nunca era mascarado mesmo com a flag ON; agora o `NlpEngineProvider` carrega o modelo PT e a falha de carga loga CRITICAL. Entidades configuráveis via `LLM_PROMPT_PRESIDIO_ENTITIES` (LOCATION/DATE_TIME fora do default p/ não mascarar skills). Teste: `tests/unit/test_pii_presidio_name_masking.py` | Média | ✅ Resolvido (03/06/2026) |
| **D-11** | Caminhos de serviços de Intelligence | `app/services/{routing_learning,calibration,model_drift,voice}_service.py` | Os módulos vivem em domínios/shared: `app/domains/analytics/services/` (routing_learning, calibration), `app/shared/observability/` (model_drift, com cópias em `app/domains/ai/services/` e `app/shared/services/`), `app/domains/cv_screening/services/` (voice). Os arquivos em `app/shared/services/*` e `app/shared/observability/*` são **shims de re-export** (2-3 linhas, marcados R-005.2/R-056) apontando para o canônico em `app/domains/*` — backward-compat intencional, NÃO duplicação divergente. `calibration_service` (analytics) e os vários `*voice_service` (cv_screening / voice / communication) são serviços DISTINTOS, não cópias | Média | ✅ Resolvido (doc — shims intencionais) |
| **D-12** | PolicyEngine | `app/services/policy_engine_service.py`, classe `PolicyEngine` | `app/domains/policy/services/policy_engine_service.py`, classe `PolicyEngineService` (com `ALPHA1_SECTOR_RULES` + `fairness_layer3_enabled` por setor) | Média | ✅ Doc corrigido |

**Status de follow-up (atualizado 03/06/2026 — "resolver tudo"):** D-06 ✅ (21 circuits; valores inline reauditados), D-08 ✅ (rotas DSR mapeadas na seção LGPD), D-10 ✅ (mascaramento de nome via Presidio + `pt_core_news_sm` ligado por padrão; deps declaradas; teste em `tests/unit/test_pii_presidio_name_masking.py`), D-11 ✅ doc (os "duplicados" em `app/shared/services/*` são shims de re-export intencionais para o canônico em `app/domains/*`). **Trade-off conhecido do D-10:** o modelo PT pequeno ocasionalmente mascara termos capitalizados (skills/títulos) como PERSON; o nome do candidato é sempre mascarado (prioridade LGPD). `LOCATION`/`DATE_TIME` ficam fora do default para preservar a qualidade da triagem (ativáveis via `LLM_PROMPT_PRESIDIO_ENTITIES` para privacidade máxima).

---
---

*Documento gerado a partir do código real do lia-agent-system (Replit) e documentação specs existente. Complementa o `ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md` com nível de detalhe técnico passo-a-passo por etapa. Última atualização de status: 03/06/2026 (auditoria de código — v1.1).*
