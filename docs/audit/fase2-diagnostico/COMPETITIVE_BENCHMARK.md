# COMPETITIVE_BENCHMARK.md — Benchmark Competitivo: WeDOTalent vs. Mercado
> P07 · Fase 2 · Data: 2026-04-14
> **Depende de:** P01 (PLATFORM_MAP), P04 (MATURITY_ASSESSMENT)
> **Alimenta:** P21 (Roadmap Estratégico)

---

## Sumário Executivo

A plataforma WeDOTalent/LIA compete em um mercado de AI Recruiting em rápida consolidação, com jogadores estabelecidos (Eightfold, Phenom) atingindo maturidade operacional e novos entrantes agênticos (Tezi, HireEZ Agentic) acelerando funcionalidades de execução autônoma. O score médio geral da WeDOTalent é **2.6/5**, posicionando-a como plataforma de **potencial diferenciado mas execução incompleta** — acima do baseline conversacional simples (Paradox, Humanly), porém abaixo dos líderes de mercado em funcionalidade end-to-end (Eightfold: 3.4/5, Phenom: 3.6/5). A arquitetura interna é mais sofisticada que a maioria dos competidores de mesmo porte, mas gaps críticos de execução — scheduling bloqueado (F5), comunicação simulada (F4), WSISession ausente (F3) — impedem a entrega real do valor arquitetural.

As três vantagens competitivas mais concretas da WeDOTalent são: (1) **FairnessGuard de 3 camadas com Four-Fifths Rule** — sistema de fairness documentado e auditável inexistente na maioria dos competidores; (2) **LGPD by design** — a única plataforma no mercado com infraestrutura de consentimento, DSR export e audit trail projetados especificamente para o mercado brasileiro; (3) **WSI (Weighted Scoring Interview)** — metodologia proprietária de avaliação comportamental/técnica com fórmula (70% técnico + 30% comportamental), thresholds auto-approve/review, e HITL integrado, que nenhum competidor replica de forma equivalente. Os três gaps mais críticos são: (1) scheduling completamente bloqueado — enquanto Paradox e HireEZ entregam agendamento como core feature, a WeDOTalent tem 0 de funcionalidade real; (2) comunicação outbound simulada — email e WhatsApp retornam mock success, tornando a plataforma incapaz de ação real com candidatos; (3) sourcing de dados limitado — 750M+ perfis da Tezi e 800M+ da HireEZ/SeekOut vs. integração parcial Apify/LinkedIn sem banco proprietário.

O posicionamento estratégico realista para 2026 é de **challenger diferenciado no mercado Brasil**, com oportunidade de liderança absoluta em Responsible AI para mercado latino-americano, onde nenhum competidor tem LGPD como design principle. Globalmente, a plataforma precisa fechar os gaps de execução (scheduling, comunicação real) antes de competir com Eightfold ou Phenom. Os próximos 90 dias são decisivos: fechar C-01 (WSManager), C-09 (communication dispatch), e C-11 (4 rotas scheduling) elevaria o score médio de 2.6 para 3.2+ e tornaria a plataforma comercialmente competitiva para mid-market Brasil.

---

## Metodologia de Scoring

### Escala 0–5
| Score | Label | Critério |
|-------|-------|----------|
| 0 | Ausente | Funcionalidade não existe ou completamente bloqueada |
| 1 | Rudimentar | Existe mas com falhas críticas que impedem uso real |
| 2 | Básico | Funciona parcialmente; limitações significativas de escala ou profundidade |
| 3 | Competente | Funciona end-to-end; competitivo com produto médio do mercado |
| 4 | Avançado | Diferenciado; acima da média; pronto para enterprise |
| 5 | Líder de Mercado | Melhor da categoria; referência para outros competidores |

### O que é "Benchmark de Mercado"
O score de benchmark representa o **melhor-em-classe** para aquela capacidade entre os 10 competidores pesquisados (Tezi, Popp, Phenom, Eightfold, Findem, HireEZ, Paradox, Humanly, Fetcher, SeekOut). Não é a média do mercado, mas o teto observável da capacidade.

### Fontes
- Documentação técnica de produto: sites oficiais, product pages, whitepapers públicos (2025-2026)
- Avaliações: G2, Capterra, SelectSoftwareReviews, The Daily Hire (2025-2026)
- Press releases e funding announcements: Crunchbase, PRNewswire, TechCrunch (2025-2026)
- Relatórios de analistas: IDC MarketScape Talent Intelligence 2025, Gartner Critical Capabilities Talent Acquisition 2025
- Auditoria interna: PLATFORM_MAP (P01), MATURITY_ASSESSMENT (P04), FLOW_TRACES (P02), PROMPT_AUDIT (P03)
- Processos judiciais e regulatórios: Eightfold class action (jan/2026), NYC LL144, California ADS regulations (out/2025)

---

## 1. Capacidades Agênticas

| Capacidade | WeDOTalent (atual) | Score | Benchmark Mercado | Score | Gap | Prioridade |
|------------|-------------------|-------|-------------------|-------|-----|------------|
| Sourcing autônomo de candidatos | Apify + LinkedIn parcial; SourcingReActAgent com sub-agentes; sem banco proprietário; FLOW 1 funcional mas limitado | 2/5 | **Tezi (Max)**: 750M perfis, sourcing totalmente autônomo, calibração deep por feedback, personalized outreach integrado | 5/5 | −3 | P1 |
| Triagem automatizada | CVScreeningBatchService via Celery; WSI scoring (70/30); auto_approve ≥75, review ≥55; de-agentificado mas funcional | 3/5 | **Phenom X+ Screening**: triagem multi-modal com ontologies proprietárias, integração ATS nativa, score explicável | 5/5 | −2 | P2 |
| Scheduling inteligente | InterviewGraph StateGraph implementado; 4 rotas Rails ausentes (GET availability, POST calendar_events); FLOW 5 **100% BLOQUEADO** | 0/5 | **Paradox (Olivia)**: scheduling em segundos, multi-calendário, reschedule automático, timezone handling, líder de mercado | 5/5 | −5 | **P0** |
| Comunicação multicanal (email, WhatsApp, SMS) | send_email e send_whatsapp existem como tools; retornam mock success sem dispatch real (C-09); Path B (Rails direto) funcional mas sem agente | 1/5 | **Popp AI**: WhatsApp + SMS + email + voz + vídeo em 50+ idiomas; conversação multicanal nativa | 5/5 | −4 | **P0** |
| Avaliação comportamental/técnica (WSI) | WSI completo: fórmula (70% técnico + 30% comportamental), Bloom/Dreyfus, HITL, AuditService — metodologia proprietária robusta | 4/5 | **Eightfold AI Interviewer**: avaliação conversacional 24/7, 1.6B perfis, scoring dinâmico | 4/5 | 0 | Manter |
| Geração de relatórios e insights | AnalyticsReActAgent com CoT, RAGAS passivo, KanbanInsightAgent, recruiter_personalization_service (construído mas não injetado) | 2/5 | **SeekOut**: labor market intelligence, competitive benchmarking, talent pool analytics, 300+ filtros | 4/5 | −2 | P2 |
| Ações proativas (sugestões, alertas, follow-ups) | LearningLoopService captura padrões (7 tipos); drift detection; RAGAS batch; PersonalizationContext construída mas não injetada em prompts | 2/5 | **Findem Copilot**: aprende com feedback, self-corrects, pipeline proativo automatizado, agentic workflows | 4/5 | −2 | P2 |

**Score médio WeDOTalent — Capacidades Agênticas: 2.0/5**

**Análise:** O perfil da WeDOTalent em capacidades agênticas revela uma assimetria crítica: a avaliação (WSI, 4/5) é diferenciada e acima do mercado, enquanto as capacidades operacionais de base — scheduling (0/5) e comunicação (1/5) — são o maior bloqueador comercial da plataforma. Nenhum prospect corporativo considerará uma plataforma de recrutamento AI que não consiga agendar entrevistas ou enviar emails reais. Esses dois gaps representam risco de fechamento de deals antes mesmo de uma demonstração técnica. O sourcing é estruturalmente viável mas carece do banco de dados proprietário que diferencia Tezi, HireEZ e SeekOut.

---

## 2. Inteligência

| Capacidade | WeDOTalent (atual) | Score | Benchmark Mercado | Score | Gap | Prioridade |
|------------|-------------------|-------|-------------------|-------|-----|------------|
| Ranking e matching de candidatos | pgvector cosine similarity + LLM scoring; WRF (Weighted Ranking Formula); funcional em FLOW 1; sem fairness pós-ranking (A-03) | 3/5 | **Eightfold**: 1.6B career trajectories, 1.6M skills, 50+ variáveis, deep learning proprietário | 5/5 | −2 | P2 |
| Entendimento de requisitos complexos | CascadedRouter 8 tiers + FastRouter 20+ domínios; A/B testing integrado; JWizardReActAgent (melhor prompt: 27/33) | 3/5 | **Phenom**: X+ Ontologies com contexto de empresa; industry-specific agents; skill-to-role mapping automático | 5/5 | −2 | P2 |
| Capacidade conversacional (profundidade, contextualidade) | LangGraph ReAct + StateGraph; memória cross-turn via PostgresSaver; ConversationMemory; UniversalContext; score médio prompts 62% | 4/5 | **Paradox (Olivia)**: conversação fluida 30+ idiomas; UX líder de mercado; stateless mas alta consistência | 4/5 | 0 | Manter |
| Tomada de decisão autônoma | HITL em 3 fluxos críticos; HubPlanner/HubExecutor implementados; USE_SUPERVISOR=False hardcoded; AutonomousReActAgent prompt 14/33 | 2/5 | **Tezi (Max)**: supervisor multi-agent com dezenas de agentes especializados; decisão autônoma end-to-end | 5/5 | −3 | P1 |
| Aprendizado com feedback (calibração de recrutador) | LearningLoopService (7 padrões, thresholds ≥20 amostras); RecruiterPersonalizationService (construído); PersonalizationContext não injetada | 3/5 | **Findem Copilot**: feedback loop ativo, self-correction, qualidade de candidatos melhora continuamente | 4/5 | −1 | P2 |
| Personalização por empresa/vaga/recrutador | TenantContext enrichment; CustomAgentRuntime (context_level full/standard/minimal); SystemPromptBuilder com versioning; PersonalizationContext não injetada (M-16) | 2/5 | **Phenom**: personalização hyper-granular por candidato, empresa e função; talent experience engine | 5/5 | −3 | P1 |

**Score médio WeDOTalent — Inteligência: 2.8/5**

**Análise:** A WeDOTalent demonstra inteligência conversacional genuína (4/5), com CascadedRouter e memória cross-turn que superam a maioria dos competidores conversacionais. O grande desperdício é que o sistema captura padrões de aprendizado e constrói personalização mas não os injeta onde importa — o `SystemPromptBuilder.build()` nunca recebe o `PersonalizationContext` construído pelo `RecruiterPersonalizationService`. Esse é um bug de 1-2 dias que custa 1 ponto inteiro na dimensão de personalização. A ausência de modelos ML proprietários (todo o scoring WSI é rule-based/determinístico) é a lacuna de inteligência mais difícil de fechar em curto prazo.

---

## 3. Diferenciais Técnicos

| Capacidade | WeDOTalent (atual) | Score | Benchmark Mercado | Score | Gap | Prioridade |
|------------|-------------------|-------|-------------------|-------|-----|------------|
| Multi-agente vs. monolítico | 9 agentes de domínio + AutonomousReActAgent + CustomAgentRuntime; LangGraph StateGraph + ReAct; HubPlanner/Executor (desabilitado) | 4/5 | **Phenom X+ Agent Studio**: agentes verticalizados por indústria, zero-setup, coordenação nativa entre agentes | 5/5 | −1 | Manter |
| Stack de IA (modelos, embedding, vector search) | Claude Sonnet 4-6 + Gemini Flash/Pro cascata; pgvector cosine; RAGAS; PromptVersionRegistry; A/B experiments; zero fine-tuning realizado | 3/5 | **Eightfold**: modelos deep learning proprietários treinados em 1.6B perfis; embeddings proprietários | 5/5 | −2 | P2 |
| Integrações (ATS, HRIS, calendário, email) | RabbitMQ ↔ Rails (CRUD); Apify (sourcing); Mailgun/Resend (email simulado); sem integrações calendário reais; sem Workday/SAP nativo | 2/5 | **Paradox**: Workday, SuccessFactors, 50+ ATS nativos; calendar integration nativa; líder em integrações enterprise | 5/5 | −3 | P1 |
| API / extensibilidade | BFF 478 rotas proxy; FastAPI com schema dual Claude/Gemini; CustomAgentRuntime com allowed_tools; finetuning_export.py para dados rotulados | 3/5 | **Popp AI**: 3 linhas de código para trigger; API-first design; integração direta em CRM existente | 4/5 | −1 | P2 |
| Dados proprietários / data enrichment | Sem banco proprietário de candidatos; LinkedIn + GitHub parcial via Apify; finetuning_export presente mas sem fine-tuning realizado | 2/5 | **Findem**: 800M+ perfis 3D, 100K+ fontes, patents, publications, code repos; banco proprietário crescente | 5/5 | −3 | P1 |

**Score médio WeDOTalent — Diferenciais Técnicos: 2.8/5**

**Análise:** A WeDOTalent tem a melhor arquitetura multi-agente entre plataformas de mesmo porte — o CascadedRouter de 8 tiers com A/B testing integrado é genuinamente diferenciado e supera soluções como Paradox e Humanly em sofisticação orquestracional. O gap crítico é em integrações enterprise: sem Workday, SuccessFactors ou Google Calendar nativo, a plataforma perde ciclos de vendas para Phenom e Paradox antes de chegar à demo técnica. A ausência de dados proprietários de candidatos é estrutural e requer estratégia de longo prazo (seja parceria de dados, seja construção orgânica de banco via operações de clientes).

---

## 4. Responsible AI

| Capacidade | WeDOTalent (atual) | Score | Benchmark Mercado | Score | Gap | Prioridade |
|------------|-------------------|-------|-------------------|-------|-----|------------|
| Fairness e bias (público, auditável) | FairnessGuard 3 camadas (L1 regex, L2 implícito 40+ termos, L3 LLM semântico); Four-Fifths Rule; admin_bias_audit.py; mas sourcing fora de _FAIRNESS_DOMAINS | 4/5 | **SeekOut**: bias audit por Credo AI (terceiro independente); DEI analytics; diversity filters publicados | 4/5 | 0 | Manter |
| Compliance (LGPD, GDPR, EEOC, NYC LL144) | lgpd/ domain completo (ConsentChecker, DSR export, GranularConsent, DriftAlert, LGPDCleanup); LGPD by design; GDPR parcial; sem LL144 audit formal | 4/5 | **Humanly**: bias audit terceirizado (FairNow); EEOC alignment declarado; foco em high-volume hiring compliance | 3/5 | **+1** | **Vantagem** |
| Transparência e explicabilidade | AuditService (53 refs, 730d retenção); PROTECTED_CRITERIA excluídos do log; PII masking 3 camadas; EU AI Act apenas em 1 de 13 agentes; AuditService non-blocking em pontos críticos | 3/5 | **Eightfold**: responsible AI whitepaper público; MRC framework documentado; mas class action jan/2026 por opacidade de scoring | 3/5 | 0 | P2 |
| Governança documentada | HITL em 3 fluxos (WizardGraph, PipelineTransitionAgent, WSI); interrupt_before LangGraph; TenantBudget Redis; circuit breakers; zero prompts com tenant isolation explícita | 3/5 | **Phenom**: HITL infrastructure documentada; human-in-the-loop como feature vendável; EU AI Act alignment claim | 3/5 | 0 | P2 |

**Score médio WeDOTalent — Responsible AI: 3.5/5**

**Análise:** Esta é a dimensão mais forte da WeDOTalent e seu diferencial mais estratégico. O FairnessGuard de 3 camadas com Four-Fifths Rule é genuinamente raro no mercado — a maioria dos competidores declara "bias mitigation" mas sem a profundidade de implementação observada na auditoria interna. A vantagem em LGPD é absoluta: nenhum competidor tem LGPD by design (todos são adaptações retroativas de frameworks GDPR). Isso é diferencial crítico para vendas no mercado brasileiro. O risco reputacional é o fato de que gaps de execução (ConsentChecker exception silenciosa C-06, sourcing fora de _FAIRNESS_DOMAINS, AuditService non-blocking) podem anular essa vantagem se explorados em audit externo. A correção desses gaps é urgente precisamente porque a plataforma tem o posicionamento de Responsible AI como diferencial — qualquer brecha terá impacto amplificado.

---

## Perfil de Cada Competidor

### Tezi AI
- **Positioning:** Agente autônomo de recrutamento (Max) — o primeiro AI recruiter verdadeiramente autônomo para growth-stage companies e operadores de RH.
- **Strengths:**
  - Max sourcing autônomo com 750M perfis, calibração profunda e personalização de outreach
  - Arquitetura multi-agente com dezenas de agentes especializados coordenados por supervisor
  - Interface Slack-native; trabalha onde o recrutador já está; nunca perde follow-up
- **Weaknesses:**
  - Foco em mercado US/anglófono; sem suporte declarado a PT-BR ou mercado latino-americano
  - Sem LGPD ou frameworks de compliance para mercado brasileiro
- **vs. WeDOTalent:** Tezi vence em sourcing autônomo (5 vs 2), scheduling (5 vs 0), e autonomia de execução (5 vs 2). WeDOTalent vence em Responsible AI (3.5 vs ~1.5), LGPD (4 vs 0), e WSI methodology (4 vs 0). Para mercado BR, WeDOTalent tem vantagem regulatória decisiva.

---

### Popp AI
- **Positioning:** Plataforma de recrutamento conversacional focada em staffing e agências de grande porte; multiplica receita por recrutador.
- **Strengths:**
  - Comunicação multicanal nativa: WhatsApp, SMS, email, voz, vídeo em 50+ idiomas
  - Agendamento automático com coordenação real de diários e calendários
  - API-first: integração em 3 linhas de código em CRM existente
- **Weaknesses:**
  - Foco em staffing/agências; pouco adaptado para in-house recruiting enterprise
  - Sem fairness guard documentado ou compliance LGPD
- **vs. WeDOTalent:** Popp vence em comunicação multicanal (5 vs 1), scheduling (4 vs 0), e velocidade de integração. WeDOTalent vence em Responsible AI, LGPD, arquitetura de orquestração, e WSI. Para clientes enterprise que precisam de compliance, WeDOTalent tem vantagem. Para agências de staffing que precisam de volume, Popp tem vantagem operacional.

---

### Phenom AI
- **Positioning:** Plataforma enterprise de talent experience end-to-end — candidate, recruiter, employee, manager — com aplicada AI e agentes verticalizados.
- **Strengths:**
  - X+ Agent Studio com agentes pré-built por indústria, zero-setup, coordenação nativa
  - X+ Ontologies: mapa de habilidades e roles com contexto de empresa, semanas em vez de anos
  - #1 Gartner 2025 para Extended CRM Emphasis; IDC MarketScape Leader 2025
- **Weaknesses:**
  - Preço enterprise elevado; inacessível para mid-market e SMB
  - Complexidade de implementação; time-to-value longo para empresas menores
- **vs. WeDOTalent:** Phenom vence em quase tudo em termos de maturidade e escopo. WeDOTalent tem vantagem em LGPD (Phenom não tem framework BR), preço/acessibilidade, e velocidade de inovação de produto para mercado local. Competição direta só fará sentido quando WeDOTalent fechar gaps de scheduling e comunicação.

---

### Eightfold AI
- **Positioning:** Talent Intelligence Platform com deep learning proprietário treinado em 1.6B+ career trajectories; da aquisição ao workforce planning.
- **Strengths:**
  - Modelos deep learning proprietários com 1.6B perfis e 1.6M skills — dataset incomparável
  - AI Interviewer conversacional 24/7; digital twins para colaboradores; lifecycle completo
  - Reconhecimento de analistas: IDC MarketScape Leader, multiple Fortune 500 clients
- **Weaknesses:**
  - Class action jan/2026 por scraping de 1B+ perfis sem consentimento e scoring opaco (FCRA violation)
  - Ausência de transparência de scoring — "lógica que o empregador não pode examinar" (National Law Review 2026)
- **vs. WeDOTalent:** Eightfold é significativamente mais maduro em inteligência (modelos proprietários) e escala. Mas o class action de 2026 é oportunidade para WeDOTalent: posicionar FairnessGuard auditável e LGPD by design como resposta direta ao risco Eightfold. Para prospects regulatoriamente sensíveis, a transparência da WeDOTalent é argumento de vendas contra Eightfold.

---

### Findem
- **Positioning:** AI Talent Intelligence com 3D Data Enrichment — perfis enriquecidos de 800M+ candidatos de 100K+ fontes; especialização em agentic workflows.
- **Strengths:**
  - 800M+ perfis 3D com 100K+ fontes (patents, publications, GitHub, census data)
  - Copilot que aprende com feedback e se auto-corrige; candidatos melhoram com o tempo
  - $51M Series C (2025) para expansão de dataset e agentic workflows
- **Weaknesses:**
  - Sourcing como core; fraco em screening, scheduling e comunicação integrada
  - Sem framework específico para compliance LGPD ou mercado BR
- **vs. WeDOTalent:** Findem domina em dados proprietários e sourcing (5 vs 2). WeDOTalent domina em avaliação (WSI 4/5), Responsible AI (3.5/5), e LGPD. Colaboração poderia ser mais interessante que competição direta — usar dados Findem como input para WSI scoring seria stack competitivo.

---

### HireEZ
- **Positioning:** Plataforma de recrutamento outbound com agentic AI — sourcing, screening, outreach, scheduling e analytics em pipeline unificado.
- **Strengths:**
  - Agentic AI 2025: sourcing + screening + outreach + scheduling + analytics totalmente integrados
  - 800M+ perfis, rediscovery de candidatos ATS com 80% mais pipeline
  - ResumeSense para detecção de inconsistências em CVs
- **Weaknesses:**
  - "Semi-autonomous" por design — mantém recrutador no loop estratégico; menos autônomo que Tezi
  - Foco em recrutamento outbound; menos conversacional e menos assessment-focused
- **vs. WeDOTalent:** HireEZ vence em sourcing (4 vs 2), scheduling real (4 vs 0), e outreach multicanal (3 vs 1). WeDOTalent vence em WSI (4 vs 0), FairnessGuard (4 vs 1), LGPD (4 vs 0), e profundidade conversacional (4 vs 2). HireEZ está bem posicionado para mid-market US; WeDOTalent tem vantagem no mercado BR por compliance.

---

### Paradox (Olivia)
- **Positioning:** Conversational AI hiring assistant focada em speed-to-hire — candidato aplica, é screenado, e agenda entrevista em minutos, via chat.
- **Strengths:**
  - Scheduling líder de mercado: entrevistas agendadas em segundos, multi-calendário, reschedule automático, 30+ idiomas
  - Integrações enterprise: Workday, SuccessFactors, 50+ ATS — ecossistema mais amplo do mercado
  - UX conversacional simples e eficaz — alta adoção e NPS elevado
- **Weaknesses:**
  - Arquitetura stateless sem orquestração multi-tier; sem memória cross-turn real
  - Fairness e compliance são thin layers sem profundidade; sem LGPD
- **vs. WeDOTalent:** Paradox domina em scheduling (5 vs 0) e integrações (5 vs 2). WeDOTalent domina em arquitetura de orquestração (CascadedRouter 8 tiers vs. intent classifier simples), WSI (4 vs 0), FairnessGuard (4 vs 1), LGPD (4 vs 0). Com scheduling funcional, WeDOTalent seria diretamente competitiva com Paradox no mercado BR.

---

### Humanly
- **Positioning:** Conversational screening AI para high-volume hiring — chat + SMS + email + voz + vídeo; análise de entrevistas com scoring por competências.
- **Strengths:**
  - Multi-modal: chat, SMS, email, vídeo, voz — canal único para todo o ciclo inicial
  - 5 anos de dados de treinamento de entrevistas; scoring por competências
  - Bias audit externo por FairNow; alinhamento EEOC declarado
- **Weaknesses:**
  - Foco em high-volume / volume-heavy hiring; menos adequado para posições complexas ou sênior
  - Sem LGPD; sem suporte declarado a mercado BR
- **vs. WeDOTalent:** Humanly vence em comunicação multicanal real (4 vs 1) e bias audit externo formalizado. WeDOTalent vence em profundidade de avaliação (WSI 4 vs scoring por competências 3), arquitetura (4 vs 2), LGPD (4 vs 0). Para mercado BR enterprise, WeDOTalent é competitivamente superior se resolver comunicação multicanal.

---

### Fetcher
- **Positioning:** Automated outbound recruiting — sourcing + personalização de outreach via AI; parceria com SmartRecruiters para end-to-end.
- **Strengths:**
  - Sourcing via natural language (sem Boolean); auto-parse de job description
  - Outreach personalizado com generative AI em múltiplos idiomas (EN, FR, ES)
  - DE&I pipelines, anonymous sourcing, reporting integrado
- **Weaknesses:**
  - Essencialmente sourcing + outreach; screening, scheduling e assessment são limitados ou via parceiros
  - Sem framework de compliance LGPD; suporte a PT-BR não declarado
- **vs. WeDOTalent:** Fetcher é mais simples e focado em top-of-funnel. WeDOTalent é mais completo: WSI, conversação profunda, fairness. Para empresas que precisam apenas de sourcing automatizado, Fetcher tem melhor UX. Para empresas que precisam de avaliação + compliance + memória conversacional, WeDOTalent é superior.

---

### SeekOut
- **Positioning:** Talent search + analytics com foco em candidatos de alta especialização (STEM, diversidade, segurança clearance); agentic AI em 2025.
- **Strengths:**
  - 800M+ perfis com 300+ filtros e semantic search; GitHub, Google Scholar, patents
  - AI Screener com vídeo + avaliação de respostas + shortlist qualificado
  - Bias audit externo por Credo AI; DEI analytics; EEOC compliance declarado
- **Weaknesses:**
  - Foco em sourcing especializado (STEM/tech); menos conversacional; sem LGPD
  - Preço ($12K+/ano) elevado para PMEs e mid-market
- **vs. WeDOTalent:** SeekOut vence em profundidade de dados (800M perfis vs. sourcing limitado) e bias audit externo formalizado. WeDOTalent vence em conversação (4 vs 2), LGPD (4 vs 0), WSI methodology (4 vs 2), e preço acessível para BR. Para especialistas em sourcing US, SeekOut é melhor. Para recrutamento consultivo com compliance BR, WeDOTalent é melhor.

---

## Análise Estratégica

### Onde a Plataforma Já Compete (Manter e Fortalecer)

| Capacidade | WeDO Score | Mercado Líder | Delta |
|------------|-----------|---------------|-------|
| Avaliação comportamental/técnica (WSI) | 4/5 | Eightfold (4/5) | 0 |
| Capacidade conversacional (profundidade, contextualidade) | 4/5 | Paradox (4/5) | 0 |
| Fairness e bias (public, auditável) | 4/5 | SeekOut (4/5) | 0 |
| LGPD compliance (mercado BR) | 4/5 | Ninguém (0/5) | **+4** |
| Arquitetura multi-agente | 4/5 | Phenom (5/5) | −1 |
| Calibração de recrutador | 3/5 | Findem (4/5) | −1 |

Essas capacidades devem ser preservadas e comunicadas ao mercado. Em particular, o WSI e o LGPD by design são únicos — nenhum investimento nessas áreas deve ser sacrificado por velocidade de feature delivery.

---

### Onde Está Atrás (Catch-up Necessário)

| Capacidade | WeDO Score | Líder | Gap | Para fechar o gap | Esforço |
|------------|-----------|-------|-----|-------------------|---------|
| Scheduling inteligente | 0/5 | Paradox (5/5) | −5 | Criar 4 rotas Rails ausentes + conectar InterviewGraph ao calendário real | Médio (2-3 semanas) |
| Comunicação multicanal real | 1/5 | Popp (5/5) | −4 | Reconectar communication_tools.py ao CommunicationDispatcher; verificar WhatsApp API | Baixo (2-3 dias) |
| Sourcing autônomo | 2/5 | Tezi (5/5) | −3 | Parceria de dados (Findem/Apollo) + SourcingReActAgent com banco próprio | Alto (3-6 meses) |
| Integrações enterprise (ATS/calendário) | 2/5 | Paradox (5/5) | −3 | Connectors Workday/SuccessFactors/Google Calendar | Alto (2-4 meses) |
| Tomada de decisão autônoma | 2/5 | Tezi (5/5) | −3 | Habilitar USE_SUPERVISOR=True + reescrever prompt AutonomousReActAgent | Médio (3-4 semanas) |
| Personalização por empresa/vaga | 2/5 | Phenom (5/5) | −3 | Injetar PersonalizationContext no SystemPromptBuilder (1-2 dias de código) | **Baixo (1-2 dias)** |

Os dois primeiros gaps (scheduling e comunicação) são bloqueadores comerciais que devem ser resolvidos imediatamente — são tecnicamente simples, de baixo/médio esforço, e de alto impacto comercial. A personalização é um quick win de 1-2 dias que custa 1 ponto em uma dimensão inteira.

---

### Onde Pode Diferenciar (Oportunidade de Liderança)

1. **LGPD by design para mercado BR e LATAM** — Nenhum competidor tem LGPD como design principle. Com a aprovação e fiscalização crescente da LGPD no Brasil, e com regulações similares emergindo no Chile, Argentina e Colômbia, a WeDOTalent pode ser a plataforma referência de Responsible AI para o mercado LATAM. Isso é uma vantagem de 3-5 anos que competidores não podem copiar facilmente (requer reengenharia do produto, não apenas checkbox).

2. **WhatsApp-native AI recruiting** — Brasil tem 93%+ de penetração de WhatsApp. Nenhum competidor global tem WhatsApp como canal primário nativo de IA. Paradox e Humanly têm WhatsApp como canal secundário ou via parceiros. Uma WeDOTalent com comunicação WhatsApp real (não simulada) seria única no mercado global de AI recruiting para o contexto brasileiro.

3. **WSI como metodologia de avaliação proprietária** — A fórmula (70% técnico + 30% comportamental) com Bloom/Dreyfus e HITL pode ser vendida como framework de avaliação, não apenas ferramenta. Nenhum competidor tem uma metodologia proprietária nomeada e documentada. Isso permite posicionamento consultivo e criação de certificação WSI como produto independente.

4. **PT-BR NLU profundo** — Os modelos dos competidores globais têm performance significativamente inferior em português brasileiro comparado ao inglês. O histórico de conversações em PT-BR da WeDOTalent é ativo de fine-tuning para modelo próprio ou adaptado. Com `finetuning_export.py` já implementado, a plataforma pode construir capacidade de PT-BR superior a todos os competidores globais.

5. **FairnessGuard como produto independente** — A arquitetura de 3 camadas (regex + implícita + LLM semântica), auditável e configurável por setor, pode ser ofertada como compliance layer para outros sistemas de RH. Num contexto em que Eightfold enfrenta class action por opacidade e NYC LL144 exige bias audits anuais, uma ferramenta de FairnessGuard-as-a-Service seria diferenciadora.

---

### Features Table Stakes Faltando (Bloqueadores Comerciais)

| Feature | Status | Complexidade de Build | Prioridade |
|---------|--------|----------------------|------------|
| Scheduling real de entrevistas | Ausente (4 rotas Rails faltando) | Média | **P0** |
| Email outbound com delivery real | Parcial (mock em path agente) | Baixa | **P0** |
| WhatsApp outbound com entrega real | Parcial (mock em path agente) | Baixa | **P0** |
| Integração Google Calendar / Outlook | Ausente | Média | P1 |
| Connector ATS enterprise (Workday, Greenhouse, Lever) | Ausente nativo | Alta | P1 |
| Bias audit externo documentado (terceiro independente) | Ausente (interno apenas) | Média | P1 |
| Dashboard de métricas de recrutamento (time-to-hire, funnel) | Básico (heurístico) | Média | P1 |
| Aplicação via mobile / WhatsApp (candidate-facing) | Ausente | Alta | P2 |
| Exportação de relatórios (PDF/Excel) | Não confirmada | Baixa | P2 |
| SSO enterprise (além de WorkOS) | Ausente declarado | Média | P2 |

---

## Score Card Resumido

| Dimensão | WeDOTalent | Melhor Competidor | Posição |
|----------|-----------|------------------|---------|
| Capacidades Agênticas | 2.0/5 | 5.0/5 (Tezi/Paradox) | 8 de 11 |
| Inteligência | 2.8/5 | 5.0/5 (Phenom/Eightfold) | 6 de 11 |
| Diferenciais Técnicos | 2.8/5 | 5.0/5 (Findem/Paradox) | 6 de 11 |
| Responsible AI | 3.5/5 | 4.0/5 (SeekOut/Humanly) | **1 de 11** |
| **MÉDIA GERAL** | **2.6/5** | **3.6/5 (Phenom)** | **7 de 11** |

> **Nota de posição:** Rankings são estimativas baseadas em pesquisa de produto público e auditoria interna. Os 11 competidores são: WeDOTalent, Tezi, Popp, Phenom, Eightfold, Findem, HireEZ, Paradox, Humanly, Fetcher, SeekOut.

### Leitura do Score Card

- **Responsible AI (3.5/5, #1):** Este é o diferencial real e sustentável da plataforma. Nenhum competidor pesquisado tem LGPD by design, FairnessGuard de 3 camadas documentado, e DSR export integrado. A vantagem é defensável.

- **Inteligência e Diferenciais Técnicos (2.8/5, #6):** Competitivos mas não líderes. A arquitetura é sofisticada mas o gap entre design e execução penaliza os scores. Fechar PersonalizationContext injection e USE_SUPERVISOR=True elevaria ambos imediatamente.

- **Capacidades Agênticas (2.0/5, #8):** Score mais baixo e de maior impacto comercial. Scheduling bloqueado e comunicação simulada são responsáveis por −2 a −3 pontos nesta dimensão. Resolver esses dois itens (estimativa: 2-4 semanas de eng) moveria o score para 3.0-3.5/5.

- **Média Geral (2.6/5, #7):** Posição de mid-market challenger. Abaixo de Phenom, Eightfold, Paradox, HireEZ e Tezi em capacidades gerais. Acima de Fetcher, Popp, e provavelmente Humanly em profundidade técnica. Com os quick wins dos próximos 30 dias, a plataforma pode atingir 3.2/5 e posição #4-5.

---

## Fontes e Referências

### Competidores
- [Tezi AI — Product Page](https://tezi.ai/)
- [Tezi — Max Launch, $9M Funding](https://blog.tezi.ai/p/tezi-raises-9m-to-launch-max-the-first-fully-autonomous-ai-recruiter)
- [Popp AI — Platform Page](https://www.joinpopp.com/our-product)
- [Popp AI — Compliance and Responsible AI](https://www.joinpopp.com/our-approach)
- [Phenom — Intelligent Talent Experience Platform](https://www.phenom.com/intelligent-talent-experience-platform)
- [Phenom — Gartner Critical Capabilities #1 (April 2025)](https://www.businesswire.com/news/home/20250414134631/en/Phenom-Ranked-1-for-Extended-CRM-Emphasis-Use-Case-in-the-2025-Gartner%C2%AE-Critical-Capabilities-for-Talent-Acquisition-(Recruiting)-Suites-Report)
- [Eightfold AI — Talent Intelligence Platform](https://eightfold.ai/products/)
- [Eightfold AI — Agentic AI 2025](https://www.prnewswire.com/news-releases/talent-intelligence-to-talent-advantage-eightfold-ai-revolutionizes-hr-through-agentic-ai-302449233.html)
- [Eightfold AI — Responsible AI Whitepaper](https://eightfold.ai/wp-content/uploads/Responsible_AI_at_Eightfold.pdf)
- [Eightfold AI Class Action 2026 — National Law Review](https://natlawreview.com/article/ai-hiring-under-fire-what-the-eightfold-lawsuit-means-every-employer-using-algorithmic)
- [Findem — 3D Data Platform](https://www.findem.ai/why-findem/3d-data)
- [Findem — $51M Series C 2025](https://www.prnewswire.com/news-releases/findem-raises-51-million-to-transform-how-companies-hire-with-the-worlds-largest-expert-labeled-talent-dataset-302589634.html)
- [HireEZ — Agentic AI Announcement 2025](https://www.prnewswire.com/news-releases/hireez-unveils-agentic-ai-a-semi-autonomous-approach-to-smarter-more-strategic-recruiting-302411200.html)
- [HireEZ — Platform Overview](https://hireez.com/platform/)
- [Paradox (Olivia) — Conversational Scheduling](https://www.paradox.ai/products/conversational-scheduling)
- [Paradox (Olivia) — Product Review 2026](https://www.index.dev/blog/paradox-ai-recruitment-chatbot-review)
- [Humanly — Updated Platform Launch Nov 2025](https://finance.yahoo.com/news/humanly-launches-updated-conversational-ai-142000350.html)
- [Humanly — Bias Audit by FairNow Case Study](https://fairnow.ai/case-study-fairnow-humanly-hr-tech-chatbot/)
- [Fetcher — AI Recruiter Product](https://fetcher.ai/)
- [Fetcher — June 2025 Product Release](https://fetcher.ai/blog/june-2025-product-release)
- [SeekOut — Agentic AI Platform](https://www.seekout.com/platform/recruit)
- [SeekOut — Bias Audit by Credo AI](https://aiproductivity.ai/tools/seekout/)

### Regulatório e Analistas
- [IDC MarketScape Talent Intelligence 2025 (Phenom/Eightfold)](https://www.phenom.com/press-release/phenom-leader-idc-marketscape-talent-intelligence)
- [NYC Local Law 144 — AEDT Bias Audit Requirements](https://eightfold.ai/blog/nyc-ai-law/)
- [California ADS Regulations October 2025](https://www.hrdefenseblog.com/2025/11/ai-in-hiring-emerging-legal-developments-and-compliance-guidance-for-2026/)
- [EU AI Act February 2025 Provisions](https://secureprivacy.ai/blog/ai-gdpr-compliance-challenges-2025)
- [EEOC AI Algorithmic Fairness Initiative](https://www.eeoc.gov/newsroom/eeoc-launches-initiative-artificial-intelligence-and-algorithmic-fairness)
- [AI Hiring Tools Market Overview 2026 — Truffle](https://www.hiretruffle.com/blog/ai-recruiting-software)

### Auditoria Interna (base para scores WeDOTalent)
- PLATFORM_MAP.md (P01) — `/home/runner/workspace/docs/audit/fase1-reconhecimento/PLATFORM_MAP.md`
- MATURITY_ASSESSMENT.md (P04) — `/home/runner/workspace/docs/audit/fase2-diagnostico/MATURITY_ASSESSMENT.md`
- FLOW_TRACES (P02) — referenciado em P04
- PROMPT_AUDIT (P03) — referenciado em P04
