# Análise Competitiva — LIA Platform vs. Mercado Global de IA para Recrutamento
**WeDOTalent · Março de 2026 · Versão 2.0**

---

## Sumário Executivo

O mercado de plataformas de recrutamento com IA está em aceleração: Workday adquiriu a Paradox por US$ 1B (out/2025), Eightfold serve 1/3 das Fortune 500, e no Brasil a DigAI venceu o Web Summit 2025 e a Gupy lidera com mais de 4.000 clientes. Neste contexto, a LIA está tecnicamente posicionada como plataforma de ponta — com arquitetura de agentes multi-domínio, compliance enterprise-grade e cobertura end-to-end que nenhum concorrente brasileiro oferece e poucos globais alcançam.

**Veredicto síntese:** A LIA não compete com um produto específico — ela compete com a soma de 3–4 ferramentas que cada empresa usa hoje separadamente. Esse é o argumento central de vendas.

---

## 1. Mapa do Mercado — Posicionamento por Segmento

```
                     ESCALA (Volume de candidatos)
                     ▲
    Enterprise        │  Eightfold ●          ● Paradox/Olivia
    Fortune 500        │                       (pós-Workday)
                      │           ● HireVue
    Mid-Market         │  ● Popp AI    ● hireEZ
                      │      ● LIA ★
    PME/Growth         │  ● Gupy (BR)  ● Beam AI
                      │    ● DigAI    ● Tezi (Max)
                      └────────────────────────────────────▶
                       Triagem         End-to-End       Talent Intelligence
                       (1 etapa)    (ciclo completo)    (workforce strategy)
```

**A LIA ocupa o quadrante mid-market/end-to-end** — o quadrante com maior gap no Brasil e maior potencial de crescimento.

---

## 2. Análise por Concorrente

---

### 2.1 Paradox AI — Olivia *(adquirida pela Workday, out/2025, US$ 1B)*

| Dimensão | Paradox / Olivia | LIA |
|---|---|---|
| **Agente principal** | Olivia — chatbot conversacional 24/7 | 7 agentes ReAct especializados por domínio |
| **Canal** | SMS, WhatsApp, web chat, 100+ idiomas | WhatsApp + Email + Teams + Bell + Chat inline |
| **Triagem** | Knockout questions conversacionais | Triagem curricular + WSI + rubrica de avaliação |
| **Entrevistas** | Parcial (coleta de dados) | WSI estruturado via voz (OpenMic.ai + Deepgram) |
| **Agendamento** | Forte — 32M+ entrevistas/ano agendadas | Calendário Google/Outlook (Microsoft Graph) |
| **Sourcing** | Não possui | Pearch AI (190M+ perfis) |
| **Compliance** | Básico | LGPD + BCB 498 + SOX + ISO 27001 + EU AI Act |
| **Bias/Fairness** | Não documentado publicamente | FairnessGuard 3 camadas + Bias Audit API + snapshots auditáveis |
| **Presença Brasil** | Nenhuma (81,88% US) | 100% focado no Brasil |
| **Preço referência** | US$ 1.000–8.000/mês | — |
| **Multi-tenant** | Sim (enterprise) | Sim (nativo — company_id em todos os modelos) |

**Ponto crítico:** A aquisição pela Workday transforma a Olivia em add-on do maior HCM enterprise. Para empresas que **já usam Workday**, será difícil competir. Para o mercado brasileiro — onde Workday tem penetração mínima — a LIA é superior em cobertura, compliance local e custo.

**Vantagem LIA:** Triagem profunda (WSI), sourcing ativo (Pearch), fairness auditável, compliance regulatório BR. A Olivia não faz sourcing, não conduz entrevistas estruturadas e não tem FairnessGuard.

---

### 2.2 Tezi AI — Max *(Menlo Park, fundada 2024, seed US$ 9M)*

| Dimensão | Tezi / Max | LIA |
|---|---|---|
| **Proposta central** | "Primeiro recrutador IA totalmente autônomo" | Plataforma multi-agente end-to-end |
| **Autonomia** | Alta — sourcing → triagem → agendamento sem humano | Alta — 7 agentes com ReAct loop + guardrails |
| **Vagas suportadas** | Desk workers (tech/finanças), entry a director | Todos os segmentos, incluindo alto volume |
| **Sourcing** | Sim (outbound autônomo) | Sim (Pearch AI 190M+) |
| **Canal candidato** | Email, Slack | WhatsApp + Email + Teams |
| **Entrevistas** | Não | WSI por voz estruturado |
| **Compliance/Bias** | Auditado por terceiros, sem treino em dados cliente | FairnessGuard + Bias Audit + LGPD nativo |
| **ATS nativo** | Integra Greenhouse/Ashby/Lever (não é ATS) | Pipeline nativo + integração Gupy/Pandapé/Merge |
| **Presença Brasil** | Zero | 100% BR |
| **Maturidade** | Produto em estágio inicial (2024) | Plataforma com 8+ sessões de desenvolvimento |

**Ponto crítico:** O Max é conceitualmente o mais parecido com a LIA em filosofia (agente autônomo), mas é um produto nascente focado em tech/EUA. Não atende alto volume, não tem canal WhatsApp e não tem compliance regulatório.

**Vantagem LIA:** WhatsApp (canal dominante no Brasil), alto volume, WSI, compliance BR/financeiro, ATS nativo. O Max é o concorrente mais intrigante para acompanhar — se ganhar tração e expandir internacionalmente, será relevante em 2–3 anos.

---

### 2.3 Beam AI *(Nova York, fundada 2022)*

| Dimensão | Beam AI | LIA |
|---|---|---|
| **Natureza do produto** | Plataforma de automação **agnóstica** (RH é uma vertical) | Plataforma especializada em R&S com IA |
| **Arquitetura IA** | Graph-based agents (98% de precisão autodeclarada) | LangGraph ReAct — 7 domínios especializados |
| **Sourcing** | Sim (agent de sourcing genérico) | Sim (Pearch AI especializado) |
| **Triagem** | Parsing + shortlisting | Triagem WSI + rubrica + FairnessGuard |
| **Entrevistas** | Não | WSI estruturado por voz |
| **Agendamento** | Parcial | Microsoft Graph + Google Calendar |
| **Integrações** | 1.000+ sistemas (SAP, Salesforce, etc.) | ATS nativo + Gupy/Pandapé/Merge + Microsoft |
| **Compliance** | SOC-2 | LGPD + BCB 498 + SOX + ISO 27001 + EU AI Act |
| **Presença Brasil** | Zero | 100% BR |
| **Preço** | A partir de US$ 299/ano | — |

**Ponto crítico:** A Beam AI é genericamente poderosa mas superficialmente especializada. Não conduz entrevistas, não tem fairness BR, e não entende o contexto de R&S local.

**Vantagem LIA:** Profundidade técnica específica de recrutamento, compliance regulatório, canal WhatsApp, entrevistas estruturadas. Beam AI nunca será rival direto — é mais concorrente indireto para empresas que preferem plataformas de automação generalistas.

---

### 2.4 Eightfold AI *(Santa Clara, desde 2016 — referência Fortune 500)*

| Dimensão | Eightfold AI | LIA |
|---|---|---|
| **Posicionamento** | Talent Intelligence enterprise global | Plataforma R&S mid-market BR com compliance enterprise |
| **IA principal** | Deep learning proprietário + "maior dataset global de talentos" | LangGraph ReAct + Claude Sonnet 4.5 |
| **Talent Intelligence** | Forte — skills gap, career pathing, succession planning | Básico (WSI avalia habilidades, sem career pathing ainda) |
| **Mobilidade interna** | Forte (AI Interviewer para interno + externo) | Não possui |
| **Digital Twin** | Sim — LLM personalizado por colaborador | Não possui |
| **Sourcing** | Sim (interno + externo) | Sim (Pearch — externo) |
| **Triagem** | Sim | Sim + FairnessGuard |
| **Agendamento** | Parcial | Sim (Google + Outlook) |
| **Bias/Fairness** | Documentado (EU AI Act) | FairnessGuard 3 camadas + Bias Audit API + Four-Fifths Rule |
| **Compliance** | Enterprise global | LGPD + BCB 498 + SOX + ISO 27001 + EU AI Act |
| **Presença Brasil** | Parcial (via SAP) | 100% BR |
| **Preço** | US$ 650+/mês (mid), seis dígitos anuais (enterprise) | — |
| **Acesso PME/Mid-market** | Proibitivo | Acessível |

**Ponto crítico:** Eightfold é o player mais avançado tecnicamente no aspecto de "inteligência sobre talentos". O Digital Twin e career pathing são genuinamente diferenciadores. Para Fortune 500 que gerenciam dezenas de milhares de colaboradores, Eightfold faz sentido.

**Vantagem LIA:** Custo, acesso (mid-market), canal WhatsApp, compliance regulatório BR (BCB 498 é exclusivo), agente de sourcing externo com Pearch. O gap da LIA vs. Eightfold está na talent intelligence de longo prazo (mobilidade interna, career pathing, Digital Twin) — esses são os próximos horizontes estratégicos.

---

### 2.5 Popp AI *(Reino Unido, fundada 2023 — TIARA Champion 2025)*

| Dimensão | Popp AI | LIA |
|---|---|---|
| **Canais** | WhatsApp + Email + SMS (50+ idiomas) | WhatsApp + Email + Teams + Bell + Chat |
| **Sourcing** | Sim (centenas de milhões de candidatos) | Sim (Pearch AI 190M+) |
| **Triagem** | Multi-modal: texto + voz + vídeo | WSI por voz + curricular |
| **Agendamento** | Sim (auto-join em chamadas) | Sim (Google + Outlook) |
| **Compliance** | EU AI Act nativo, auditoria de terceiros | LGPD + BCB 498 + SOX + ISO 27001 + EU AI Act |
| **ATS integrado** | 30+ (Lever, Pinpoint, Workable, Ashby) | ATS nativo + Gupy/Pandapé/Merge |
| **Bias/Fairness** | Auditado terceiros | FairnessGuard 3 camadas + Bias Audit API auditável |
| **Entrevistas em vídeo** | Sim (triagem multi-modal) | Voz (sem vídeo ainda) |
| **Presença Brasil** | Zero (UK-centric) | 100% BR |

**Ponto crítico:** A Popp é o concorrente mais completo tecnicamente dentre os não-enterprise. Multi-modal (texto + voz + vídeo) é um diferencial real. O gap da LIA aqui está na **triagem em vídeo** — a Popp se junta automaticamente a chamadas e transcreve entrevistas.

**Vantagem LIA:** Mercado BR, compliance local, ATS nativo, multi-tenant consolidado. A Popp é referência técnica para a roadmap de vídeo da LIA.

---

### 2.6 HireVue *(South Jordan, desde 2004 — líder em video assessment)*

| Dimensão | HireVue | LIA |
|---|---|---|
| **Especialidade** | Video assessment + AI scoring de entrevistas | R&S end-to-end com IA |
| **Entrevistas em vídeo** | Forte — líder de mercado (75,7% do espaço enterprise) | Voz (sem vídeo nativo) |
| **Assessments** | Game-based, técnico, lingüístico, virtual job tryout | WSI por voz + rubrica |
| **Sourcing** | Não | Sim (Pearch AI) |
| **Triagem curricular** | Parcial | Sim + FairnessGuard |
| **Agendamento** | Sim (integrado ao ATS) | Sim (Google + Outlook) |
| **Análise facial** | Removida em 2021 (pressão regulatória) | Não usa análise facial |
| **Controvérsias bias** | ACLU processou em 2025 (caso Intuit — discriminação surdo/não-branco) | FairnessGuard + Bias Audit auditável |
| **Compliance** | NYC Local Law 144 (auditoria anual) | LGPD + BCB 498 + SOX + ISO 27001 + EU AI Act |
| **Presença Brasil** | Zero | 100% BR |
| **Preço** | US$ 35.000+/ano (entry enterprise) | — |

**Ponto crítico:** O HireVue é o player com mais controvérsias de viés algorítmico do mercado. A retirada da análise facial em 2021 e o processo da ACLU em 2025 mostram os riscos de plataformas de avaliação sem compliance robusto. A LIA tem vantagem estrutural aqui.

**Vantagem LIA:** FairnessGuard 3 camadas + Bias Audit com Four-Fifths Rule + snapshots SOX — tecnicamente mais robusto que o HireVue em fairness auditável. Gap: vídeo assíncrono (HireVue é excelente nisso). Oportunidade: posicionar a LIA como alternativa compliance-safe ao HireVue para empresas expostas a regulação brasileira.

---

### 2.7 DigAI *(Brasil, fundada 2023 — vencedora Web Summit 2025)*

| Dimensão | DigAI | LIA |
|---|---|---|
| **Especialidade** | Entrevistas automatizadas via WhatsApp (texto + voz) | R&S end-to-end multi-agente |
| **Canal principal** | WhatsApp (áudio + texto) | WhatsApp + Email + Teams + voz + chat |
| **Triagem** | Sim — 300.000+ triagens realizadas | Sim + FairnessGuard |
| **Entrevistas** | 100.000+ via WhatsApp — validadas por pesquisa MIT | WSI estruturado + rubrica |
| **Agendamento** | Parcial | Google Calendar + Outlook completo |
| **Sourcing** | Não | Sim (Pearch AI) |
| **ATS nativo** | Não (integra ATS existentes) | Sim (pipeline nativo + Gupy/Pandapé/Merge) |
| **Análise comportamental** | Sim — sinais comportamentais (parceria MIT) | Não possui (gap) |
| **Clientes** | Nubank, Deloitte, Carrefour, Companhia de Estágios | — |
| **Compliance** | Não documentado publicamente | LGPD + BCB 498 + SOX + ISO 27001 |
| **Presença Brasil** | Total (empresa brasileira) | Total |
| **Maturidade de mercado** | 100+ clientes, 400K+ interações | Em estágio comercial inicial |

**Ponto crítico:** A DigAI é o concorrente mais direto e mais relevante no Brasil. Mesma proposta de WhatsApp + IA, mas focada em **uma etapa** (entrevista inicial). Seu grande diferencial é a análise de **sinais comportamentais** (79,4% de acerto validado pelo MIT) — uma capacidade que a LIA ainda não tem.

**Vantagem LIA:** End-to-end (sourcing → triagem → entrevista → pipeline → kanban → política de contratação). A DigAI não tem sourcing, não tem ATS, não tem agendamento robusto, não tem compliance regulatório documentado. A LIA cobre o ciclo completo; a DigAI cobre uma etapa muito bem.

**Gap crítico da LIA vs. DigAI:** Análise de sinais comportamentais em áudio/voz. A parceria DigAI+MIT é uma vantagem científica real que vale investigar para o módulo WSI.

---

### 2.8 Gupy *(Brasil, desde 2015 — líder nacional)*

| Dimensão | Gupy | LIA |
|---|---|---|
| **Posicionamento** | ATS líder no Brasil com IA adicionada | Plataforma nativa de IA com ATS integrado |
| **Clientes** | 4.000+ (Itaú, Ambev, GPA, Vivo) | Em crescimento |
| **Escala** | 3,5M+ contratações | — |
| **Triagem IA** | 100 currículos/segundo, score automático | WSI + rubrica + FairnessGuard |
| **WhatsApp (Smart Vagas)** | Sim — pré-entrevistas conversacionais 2025 | Sim — triagem + voz |
| **Agendamento** | Sim | Sim (Google + Outlook) |
| **Sourcing ativo** | Parcial (base própria, não outbound proativo) | Sim (Pearch AI outbound proativo) |
| **Entrevistas estruturadas** | Parcial | WSI completo por voz |
| **Compliance** | LGPD básico | LGPD + BCB 498 + SOX + ISO 27001 + EU AI Act |
| **Agentes autônomos** | Roadmap (mencionado) | Implementado — 7 agentes ReAct ativos |
| **Multi-tenant RPO** | Não (ATS por empresa) | Sim — nativo (company_id em todos os modelos) |
| **Presença Brasil** | Total — líder absoluta | Total |
| **Foco** | Grandes empresas + mid-market BR | Mid-market + RPO white-label + financeiro |

**Ponto crítico:** A Gupy é a principal referência de mercado no Brasil e o concorrente mais perigoso pelo volume de clientes e marca consolidada. Porém, é fundamentalmente um **ATS com IA adicionada** — não foi construída com agentes autônomos como arquitetura base. Seu roadmap de IA agentic ainda é promessa, não entrega.

**Vantagem LIA:** Agentes autônomos já implementados (vs. roadmap da Gupy), compliance regulatório financeiro (BCB 498 — diferencial único no Brasil), RPO multi-tenant nativo, sourcing proativo com Pearch AI. A Gupy não atende instituições financeiras reguladas e não tem multi-tenancy para RPO.

**Diferencial defensável da LIA contra Gupy:** Segmento RPO e segmento financeiro regulado — dois mercados que a Gupy não serve adequadamente.

---

## 3. Matriz Comparativa Global

| Capacidade | LIA | Paradox | Tezi | Beam | Eightfold | Popp | HireVue | DigAI | Gupy |
|---|---|---|---|---|---|---|---|---|---|
| **Sourcing proativo** | ✅ Pearch AI | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ⚠️ |
| **Triagem curricular IA** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ |
| **Entrevista estruturada** | ✅ Voz (WSI) | ⚠️ | ❌ | ❌ | ✅ | ✅ Multi-modal | ✅ Vídeo | ✅ Voz WA | ⚠️ |
| **Entrevista em vídeo** | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Agendamento autônomo** | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ |
| **Pipeline/Kanban** | ✅ | ❌ | ❌ | ❌ | ⚠️ | ❌ | ❌ | ❌ | ✅ |
| **ATS nativo** | ✅ | ❌ | ❌ | ❌ | ⚠️ | ❌ | ❌ | ❌ | ✅ |
| **WhatsApp canal** | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ |
| **Multi-tenant RPO** | ✅ | ⚠️ | ❌ | ❌ | ✅ | ⚠️ | ⚠️ | ❌ | ❌ |
| **FairnessGuard/Bias Audit** | ✅ 3 camadas | ❌ | ✅ Parcial | ❌ | ✅ | ✅ Terceiros | ⚠️ Controvérsias | ❌ | ⚠️ |
| **LGPD nativo** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ |
| **BCB 498 / SOX** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Agentes ReAct autônomos** | ✅ 7 domínios | ⚠️ | ✅ 1 agente | ✅ | ✅ | ✅ | ❌ | ⚠️ | ❌ Roadmap |
| **Observabilidade agentes** | ✅ LangSmith + dashboard | ❌ | ❌ | ❌ | ⚠️ | ❌ | ❌ | ❌ | ❌ |
| **Drift detection** | ✅ 4 triggers | ❌ | ❌ | ❌ | ⚠️ | ❌ | ❌ | ❌ | ❌ |
| **Guardrails no banco** | ✅ CRUD + seed | ❌ | ❌ | ❌ | ⚠️ | ❌ | ❌ | ❌ | ❌ |
| **Cascade LLM (Haiku→Opus)** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Análise sinais comportamentais** | ❌ **GAP** | ❌ | ❌ | ❌ | ✅ | ⚠️ | ⚠️ | ✅ MIT | ❌ |
| **Talent Intelligence (career path)** | ❌ **GAP** | ❌ | ❌ | ❌ | ✅✅ | ❌ | ❌ | ❌ | ❌ |
| **Brasil nativo** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Mercado financeiro regulado** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

**Legenda:** ✅ Presente e robusto · ⚠️ Parcial ou superficial · ❌ Ausente

---

## 4. Análise SWOT — LIA Platform

### Forças (Strengths)

1. **Única plataforma end-to-end com agentes autônomos no Brasil** — sourcing → triagem → WSI → pipeline → kanban → política
2. **Compliance regulatório financeiro exclusivo** — BCB 498 + SOX + ISO 27001 + LGPD + EU AI Act. Nenhum concorrente brasileiro possui isso.
3. **FairnessGuard 3 camadas + Bias Audit auditável** — tecnicamente superior ao HireVue (que foi processado pela ACLU em 2025) e à maioria dos concorrentes
4. **Arquitetura de agentes ReAct madura** — 7 domínios implementados, LangGraph, observabilidade, drift detection, guardrails no banco
5. **Cascade LLM (Haiku→Sonnet→Opus)** — otimização de custo automática, única no mercado
6. **Multi-tenant RPO nativo** — atende consultorias de RH white-label, mercado crescendo 6,62% a.a.
7. **WhatsApp como canal primário** — validado pela DigAI (100K+ entrevistas) e Gupy como canal dominante no Brasil
8. **Integração Pearch AI (190M+ candidatos)** — sourcing ativo que poucos concorrentes possuem

### Fraquezas (Weaknesses)

1. **Sem entrevista em vídeo** — HireVue e Popp têm vantagem em avaliação visual
2. **Sem análise de sinais comportamentais em áudio** — DigAI tem parceria MIT com 79,4% de acerto comprovado
3. **Sem talent intelligence de longo prazo** — career pathing, mobilidade interna, Digital Twin (vantagem Eightfold)
4. **Histórico de escala ainda sendo construído** — Gupy tem 4.000+ clientes e 3,5M contratações
5. **Sem reconhecimento de marca** — DigAI venceu Web Summit 2025; Gupy é referência nacional
6. **Capacidade de vídeo ausente** — uma etapa que cada vez mais clientes exigem

### Oportunidades (Opportunities)

1. **Mercado financeiro regulado** — bancos, fintechs, seguradoras precisam de BCB 498. Zero concorrentes nesse nicho
2. **RPO white-label** — crescimento de 6,62% a.a., sem player que serve consultoras multi-tenant adequadamente
3. **Alto volume BR (varejo, logística, call center)** — nenhum player nacional resolve completamente
4. **Lacuna pós-Workday/Paradox** — mid-market que usava Paradox não vai para Workday enterprise; precisa de alternativa
5. **Controvérsia HireVue** — processo ACLU em 2025 abre oportunidade para plataformas com fairness auditável
6. **DigAI é parceira potencial** — a análise comportamental deles + o ciclo completo da LIA seria mais forte do que os dois separados

### Ameaças (Threats)

1. **Gupy lançando Smart Vagas e roadmap agentic** — se entregarem agentes reais, competição se intensifica
2. **Tezi/Max expandindo para Brasil** — produto tecnicamente semelhante com fundadores tier-1 e US$ 9M
3. **Consolidação do mercado** — Workday comprou Paradox; SAP/Oracle podem adquirir Eightfold ou Gupy
4. **DigAI escalando para end-to-end** — se adicionarem sourcing, agendamento e ATS, tornam-se concorrente direto
5. **Custo de LLMs** — plataformas que não têm cascade/otimização pagarão mais; a LIA tem vantagem aqui mas precisa escalar

---

## 5. Posicionamento Competitivo Recomendado

### Mensagem Central
> **"A LIA é a única plataforma que integra sourcing, triagem com fairness auditável, entrevistas estruturadas por voz, pipeline e analytics em uma única plataforma — com compliance para instituições financeiras reguladas. Sem precisar de 4 ferramentas diferentes."**

### Segmentos Prioritários por Diferencial Competitivo

| Segmento | Por que a LIA ganha | Concorrente deslocado |
|---|---|---|
| **Instituições financeiras** (bancos, fintechs, seguradoras) | BCB 498 + SOX + ISO 27001 — nenhum concorrente tem | Gupy (sem BCB 498), qualquer ferramenta global (sem LGPD nativo) |
| **RPO / Consultorias de RH** | Multi-tenant nativo + white-label + agentes por cliente | Gupy (sem multi-tenant), Paradox (sem RPO) |
| **Alto volume** (varejo, logística, call center) | WhatsApp + triagem em escala + WSI por voz + agendamento autônomo | DigAI (sem ciclo completo), Gupy (sem agentes autônomos) |
| **Tech/Scale-ups** | Agentes autônomos + sourcing Pearch + integração ATS | Tezi/Max (sem BR), hireEZ (sem entrevista), Beam (sem especialização) |

---

## 6. Gaps Técnicos a Considerar na Roadmap

| Gap | Referência de Mercado | Prioridade | Complexidade |
|---|---|---|---|
| **Entrevista em vídeo assíncrono** | HireVue, Popp AI | Alta | Média (Deepgram + câmera web) |
| **Análise de sinais comportamentais em voz** | DigAI (MIT), Eightfold | Alta | Alta (modelo ML dedicado) |
| **Triagem multi-modal (texto + voz + vídeo)** | Popp AI | Média | Alta |
| **Talent Intelligence — career pathing** | Eightfold (Digital Twin) | Média | Alta |
| **Mobilidade interna de talentos** | Eightfold | Baixa | Alta |
| **Analytics preditivos de sucesso** | HireVue, Eightfold | Média | Média |
| **Game-based assessments** | HireVue | Baixa | Média |

**Recomendação imediata:** entrevista em vídeo assíncrono é o gap com maior impacto comercial e menor complexidade relativa. Deepgram (já integrado para voz) pode ser base para transcrição de vídeo.

---

## 7. Engenharia Reversa — Arquitetura Técnica de IA por Concorrente

> **Metodologia:** Análise inferencial baseada em engineering blogs, job descriptions técnicas (que revelam stack inadvertidamente), investment thesis de VCs, AI explainability documents publicados por obrigação regulatória, declarações de CEOs e papers acadêmicos. A maioria das plataformas mantém deliberada opacidade técnica.

---

### 7.1 Paradox AI / Olivia

**Tipo de agente:** Conversational chatbot com state machine baseada em intent recognition — **não é ReAct, não é grafo dinâmico**. Opera com fluxos pré-definidos (screening, scheduling, FAQ) orquestrados por um motor NLU com branches condicionais.

**LLMs:** Multi-provider selecionado por tarefa — OpenAI, Anthropic, Google e Mistral avaliados e escolhidos por caso de uso. A Paradox **não constrói LLMs do zero**: faz fine-tuning sobre modelos base com dados sintéticos derivados de 189M+ conversas reais. Deliberadamente **não treina em dados reais de candidatos** — usa derivativos sintéticos.

**Framework:** Proprietário. Infra: AWS/Azure + Docker/Kubernetes + Postgres + Nginx. Time de R&D em Tel Aviv, EUA e Vietnam.

**Orquestração:** Single agent com módulos. Olivia é uma entidade única que delega para módulos especializados (screening, scheduling, assessments via Traitify/Big Five). Não é multi-agent.

**State management:** Sessão conversacional + knowledge base privada siloed por tenant. Company X nunca acessa dados de Company Y.

**Memória:** Knowledge base customizada por empresa (não RAG público). Contexto estruturado do candidato (cargo, localização, disponibilidade) injetado na sessão.

**Diferencial técnico declarado:** "Privately hosted — modificamos o código subjacente, não apenas o prompt." Sugere modelos open-source fine-tunados em infra própria.

**Pós-aquisição Workday:** Integra ao **Workday Agent System of Record** — plataforma de governança de agentes IA.

---

### 7.2 Tezi AI / Max

**Tipo de agente:** **Multi-agent hierárquico com dezenas de agentes especializados** — o design agentico mais granular encontrado entre todos os concorrentes. O investidor 8VC descreveu como "army of agents fine-tuned to perform specialized recruiting tasks, seamlessly orchestrated under one unified experience."

**LLMs:** OpenAI + Anthropic (ambos confirmados publicamente). Modelos fine-tuned em parceria direta com as duas empresas, treinados em 250M+ perfis licenciados de data providers. Usa modelos de reasoning (GPT-4o ou Claude com CoT) — CEO citou explicitamente "a combinação de raciocínio e linguagem natural dos novos LLMs."

**Framework:** Não declarado. Dado o background do CEO (ex-Head of Engineering da Covariant, empresa de robótica com pipelines ML avançados) e a escala de agentes, provavelmente framework proprietário ou LangGraph com orquestração customizada — não LangChain vanilla.

**Orquestração:** Unified interface (Max) sobre dezenas de sub-agentes. Usuário interage com uma entidade; a orquestração é invisível. ATS nativo próprio — não depende de ATS externo.

**State management:** ATS nativo Tezi com histórico de candidatos, pipeline, comunicações e A/B testing de mensagens de outreach.

**Memória:** 750M perfis indexados como base de busca. Tool use extensivo: calendários, email, Slack API, banco de candidatos.

---

### 7.3 Beam AI

**Tipo de agente:** **Graph-based self-learning agents** — grafos direcionados onde nós são etapas de decisão e arestas são fluxos condicionais. Diferencial: o grafo pode **auto-modificar-se** quando o agente encontra caminhos desconhecidos (aprendizado via Task Mining sobre interações humanas).

**LLMs — ModelMesh (roteamento multi-LLM proprietário):**
- GPT-4o → raciocínio complexo e tomada de decisão
- GPT-4o-mini → respostas rápidas (latência crítica)
- Claude 3.5 → processamento e extração de dados
- Command R (Cohere) → workflows RAG e retrieval
- LLaMA, DeepSeek, BLOOM, Grok → disponíveis como alternativas

**Framework:** Proprietário. Não usa LangGraph ou CrewAI — se posiciona como alternativa completa a eles. Plataforma no-code + SDK pro-code.

**Orquestração:** Multi-agent com routing por habilidade e SLA. Execução paralela, retries, timeouts e traces auditáveis.

**State management:** O grafo em si codifica o estado e o "conhecimento" do agente. Modificação do grafo como memória de longo prazo.

**Diferencial técnico:** 98% de precisão autodeclarada que melhora a cada execução (self-learning). Processa 5.000+ tarefas/minuto.

---

### 7.4 Eightfold AI

**Tipo de agente:** **Arquitetura em duas camadas** — única entre todos os concorrentes:
- **Camada 1 (base):** Deep learning proprietário treinado em 1,6B+ trajetórias de carreira
- **Camada 2 (interface):** Agentic AI / LLMs generativos adicionados em 2023–2025

**Camada 1 — Deep Learning (Talent Intelligence Engine):**
- Embeddings N-dimensionais para títulos, empresas e skills no mesmo espaço vetorial (ex: vetor "Google" próximo de "Microsoft", distante de "KFC")
- RNNs treinadas em centenas de milhões de trajetórias para prever "próximo título" de um profissional
- Token embedding de título + empresa no mesmo espaço vetorial — similaridade semântica além de keywords
- Modelos de baixa latência para matching em tempo real
- Dataset: 1,6B+ perfis, 1,6M skills catalogadas

**Camada 2 — Agentic AI (2025):**
- **Recruiter Agent + AI Interviewer:** Conduz conversas estruturadas por voz 24/7. "This isn't a script or a wrapper on a general-purpose LLM" — fine-tuning confirmado. Arquitetura voice multimodal (STT → LLM → TTS ou end-to-end).
- **Project Andromeda / Digital Twins:** LLM personalizado por colaborador que agrega conhecimento via email, Slack, Teams, CRMs, repositórios de código. Roteamento para agentes especializados baseado em expertise dos Digital Twins.

**Framework:** Proprietário (ex-Google/Facebook engineers). Hierárquico: single entry point → agentes especializados via Domain Knowledge Mapping.

**LLMs:** Não nomeados publicamente. "LLMs pré-treinados comparados e selecionados" — modelos proprietários de domínio que superam LLMs genéricos em acurácia e fairness.

**Modelo estático e determinístico:** Não re-treina on the fly — consistência e auditabilidade.

---

### 7.5 Popp AI

**Tipo de agente:** LLM conversational screening agent com capacidades multimodais (texto + voz + vídeo). Single agent com módulos por etapa.

**LLMs:** Não declarado. Declaração pública confirma uso de LLMs: *"deploying screening tools that rely on LLMs... can intuitively understand if a candidate has experience without needing explicit keyword inclusion."* Inferido: GPT-4o ou Claude dada a cobertura de 50+ idiomas. STT para voz: provavelmente OpenAI Whisper ou similar.

**Framework:** Provavelmente SDK direto de LLM provider com orquestração customizada. Integração ATS com "três linhas de código" — SDK bem abstraído.

**Orquestração:** Wrapper/orchestration layer sobre ATS existentes (Oracle, Workday, Lever, SAP). Módulos: sourcing → scoring de aplicações → screening conversacional → scheduling → transcrição de entrevistas.

**Compliance técnico:** Ciclo completo de gestão de risco EU AI Act + auditorias de bias independentes.

---

### 7.6 HireVue

**Tipo de agente:** **Não é um agente** — é um **pipeline de ML scoring estático e determinístico**. Sem loop de raciocínio, sem LLMs generativos no core do scoring, sem autonomia.

**Pipeline técnico (documentado publicamente no AI Explainability Statement 2024):**
1. **STT:** Rev.ai (testado em 50.000+ horas de áudio)
2. **NLP:** **RoBERTa fine-tuned** em dados de entrevistas → features linguísticas específicas de contexto de entrevista (não usa features de input out-of-the-box)
3. **Deep Neural Network:** Combina features do RoBERTa fine-tuned → scores de competências (orientação a equipe, adaptabilidade, etc.)
4. **Ensemble Learning:** Múltiplos modelos combinados para acurácia preditiva
5. **25.000 data points** por entrevista (antes de descontinuar análise visual)

**Game-Based Assessments:** ML scoring separado, treinado em 11.574 completions. Validade convergente r=0.5, teste-reteste r=0.68. Fairness-optimized ML (fairness incorporado no treinamento, não pós-processamento).

**Mudança arquitetural crítica:** Scoring migrou de análise facial + fala + texto → **text-only** (pressão regulatória Illinois + ACLU). O scoring atual se baseia exclusivamente no texto transcrito.

**Modelo:** Estático, determinístico, não re-treina on the fly. Mesma entrada = mesma saída sempre.

**O mais documentado tecnicamente** entre todos os concorrentes — único com AI Explainability Statement público detalhado.

---

### 7.7 DigAI

**Tipo de agente:** Conversational WhatsApp agent (áudio) para triagem em alto volume. Pipeline linear: candidato → WhatsApp (áudio) → STT → LLM análise comportamental → relatório + integração ATS.

**LLMs:** Total opacidade técnica. Análise inferencial:
- **STT:** OpenAI Whisper (excelente pt-BR, open-source) ou Google Speech-to-Text / AWS Transcribe
- **Análise comportamental:** GPT-4 ou Claude (análise de texto transcrito para mapeamento de competências) — possivelmente modelo fine-tuned dado parceria MIT
- "Algorítmos que interpretam respostas comportamentais" + "NLU para simular tom, empatia e linguagem" são consistentes com LLMs modernos

**Framework:** Provavelmente SDKs diretos de LLM providers (OpenAI API ou Anthropic API) com orquestração customizada simples. Improvável uso de LangGraph em produção neste estágio (startup early-stage, US$ 2,42M).

**Orquestração:** Single agent pipeline linear. Implementação em ~30 dias (sugere arquitetura simples).

**Canal:** Meta Business API (WhatsApp). Integração bidirecional com ATSs do mercado.

**Diferencial técnico real:** Análise de **sinais comportamentais** em áudio além de conteúdo semântico. Validado por pesquisa MIT — 79,4% de acerto na identificação de candidatos adequados. 8,9/10 de satisfação de candidatos.

---

### 7.8 Gupy / GAIA

**Tipo de agente:** Duas gerações convivendo:
- **GAIA (2015–2023):** ML clássico de ranking supervisionado — não é agente ReAct. Modelo treinado em dados de processos seletivos reais para ordenar currículos.
- **Agentes Generativos (2024–2025):** Camada LLM sobre GAIA. Human-in-the-loop obrigatório — agentes recomendam, humanos decidem. Sem autonomia de ação em processos complexos.

**LLMs:** Silêncio técnico completo. Análise inferencial:
- **Job description reveladora (Arquiteto de Soluções de IA):** Exige "experiência em design de state flows e orquestração usando **Google ADK, LangGraph, CrewAI ou orquestradores nativos de nuvem**" — **confirma uso desses frameworks em produção**
- **RAG documentado:** Vagas mencionam "Feature Store + Vector Store para Grounding (RAG) de modelos generativos"
- **Google Cloud:** Parceria altamente provável → **Gemini como LLM provável** para funcionalidades generativas

**Framework:** **LangGraph e/ou Google ADK confirmados** via job descriptions. Em transição — ML clássico (GAIA) + agentes LangGraph (novo).

**Orquestração:** Human-in-the-loop. Módulos: (1) Ordenação de currículos, (2) Criação de vagas, (3) Feedback em massa, (4) Condução de entrevistas, (5) Benchmarking, (6) Mobilidade interna, (7) Metas e Plano de Carreira.

**State management:** RAG sobre dataset proprietário de 35M+ candidatos brasileiros. Currículo + JD como contexto do agente de ordenação.

**Transparência:** "Nova Ordenação explicável" — XAI que mostra em linguagem simples por que cada candidato ficou em determinada posição.

---

### 7.9 Tabela Comparativa Técnica — Todos os Concorrentes vs. LIA

| | **LIA** | Paradox | Tezi | Beam AI | Eightfold | Popp | HireVue | DigAI | Gupy |
|---|---|---|---|---|---|---|---|---|---|
| **Tipo de agente** | ReAct Loop multi-domínio | Chatbot + state machine | Multi-agent hierárquico | Graph-based self-learning | Deep Learning + Agentic AI | LLM conversacional | ML scoring pipeline | Conversational WhatsApp | ML ranking + agentes LLM |
| **Framework** | **LangGraph** (explícito) | Proprietário | Proprietário (provável) | Proprietário (grafo) | Proprietário | SDK direto (inferido) | ML clássico próprio | SDK direto (inferido) | **LangGraph / Google ADK** (confirmado via JD) |
| **LLM primário** | **Claude Sonnet 4.5** (Anthropic) | Multi: OpenAI+Anthropic+Google+Mistral | OpenAI + Anthropic (fine-tuned) | GPT-4o + Claude 3.5 + Command R | Proprietário (deep learning) | Não declarado | RoBERTa fine-tuned | Não declarado (Whisper+GPT/Claude inferido) | Gemini/Google (inferido) |
| **Cascade de modelos** | ✅ Haiku→Sonnet→Opus (custo otimizado) | ❌ | ❌ | ✅ ModelMesh (por tipo de tarefa) | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Multi-agent** | ✅ 7 domínios especializados | ❌ Single | ✅ Dezenas de agentes | ✅ Multi-agent + routing | ✅ Hierárquico | ❌ Single | ❌ Pipeline | ❌ Pipeline | ⚠️ Módulos (não autônomos) |
| **ReAct loop** | ✅ (LangGraph nativo) | ❌ | ❌ (hierárquico) | ❌ (grafo) | ❌ (proprietário) | ❌ | ❌ | ❌ | ❌ Roadmap |
| **Tool calling** | ✅ Tool registry por domínio | ✅ Calendar, ATS APIs | ✅ Email, Calendar, Slack, DB | ✅ APIs de negócio genéricas | ✅ Calendar, SMS, ATS | ✅ WhatsApp, ATS APIs | ❌ (scoring only) | ✅ WhatsApp API, ATS | ✅ ATS interno |
| **State management** | ✅ LangGraph state + DB | Sessão + KB por tenant | ATS nativo Tezi | Grafo auto-modificável | Talent Intel Platform (1,6B+ perfis) | Perfil enriquecido progressivamente | Stateless (scoring) | Perfil + histórico por candidato | RAG + 35M candidatos BR |
| **Memória de longo prazo** | ✅ PostgreSQL + pgvector | KB privada por empresa | 750M perfis indexados | Modificação do grafo | 1,6B+ perfis + Digital Twins | Perfis de candidatos | 70M entrevistas (treinamento) | Dataset de processos (treinamento) | 35M candidatos brasileiros |
| **Observabilidade** | ✅ LangSmith + dashboard próprio + drift detection | ❌ | ❌ | ✅ Traces auditáveis | ⚠️ | ❌ | ✅ AI Explainability Statement | ❌ | ❌ |
| **Guardrails dinâmicos** | ✅ Tabela DB + CRUD + seed | ❌ | ❌ | ❌ | ⚠️ | ❌ | ❌ | ❌ | ❌ |
| **Fairness/Bias técnico** | ✅ FairnessGuard 3 camadas + Bias Audit API + Four-Fifths Rule | ❌ | ✅ Auditado terceiros | ❌ | ✅ Modelos bias-aware | ✅ Auditado terceiros | ⚠️ ACLU 2025 | ❌ não documentado | ⚠️ Exclusão de dados sensíveis |
| **Fine-tuning proprietário** | ❌ (prompt engineering + cascade) | ✅ Sintético (189M+ conversas) | ✅ (250M+ perfis + OpenAI/Anthropic) | ❌ | ✅ Deep learning próprio | ❌ | ✅ RoBERTa (entrevistas) | ❌ provável | ❌ (RAG sobre dataset) |
| **Análise de voz/audio** | ✅ OpenMic.ai + Deepgram | ❌ | ❌ | ❌ | ✅ Voice multimodal | ✅ | ✅ (descontinuando fala) | ✅ Core do produto | ❌ |
| **Self-learning** | ❌ | ❌ | ❌ | ✅ Task Mining + grafo | ⚠️ (batch re-training) | ❌ | ❌ | ❌ | ❌ |
| **Geração de código** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Autonomia real** | ✅ Agentes decidem e executam | ⚠️ Fluxos pré-definidos | ✅ Autônomo fim-a-fim | ✅ Autônomo (processos definidos) | ✅ (com oversight) | ✅ | ❌ | ⚠️ Pipeline fixo | ❌ Human-in-the-loop obrigatório |

---

### 7.10 As Três Gerações Técnicas do Mercado

```
Geração 1 — ML Clássico (2004–2020)
├── HireVue: RoBERTa fine-tuned + ensemble → scoring determinístico
└── Gupy GAIA: ML ranking supervisionado em 35M candidatos

Geração 2 — Chatbots LLM com Fluxos Semi-Estruturados (2020–2023)
├── Paradox/Olivia: NLU + state machine + LLM multi-provider
├── DigAI: WhatsApp áudio + STT + LLM análise comportamental
└── Popp AI: LLM conversacional multi-modal

Geração 3 — Agentes Autônomos Multi-Step (2023–atual)
├── Tezi/Max: dezenas de agentes especializados hierárquicos
├── Eightfold: Deep Learning + Agentic AI + Digital Twins
├── Beam AI: graph-based self-learning + ModelMesh
└── LIA ★: 7 domínios ReAct + LangGraph + cascade Haiku→Opus
```

**A LIA está na Geração 3** — junto com Tezi e Eightfold. Gupy e DigAI ainda são Geração 1–2, com roadmap para 3.

---

### 7.11 Onde a LIA é Tecnicamente Superior

| Aspecto | Por que a LIA lidera |
|---|---|
| **Cascade LLM por confiança** | Único no mercado — Haiku→Sonnet→Opus com threshold de confiança. Beam AI tem multi-LLM mas por tipo de tarefa, não por confiança/custo dinâmico |
| **Guardrails no banco de dados** | CRUD + seed + toggle em runtime. Nenhum concorrente documenta essa capacidade |
| **Observabilidade de agentes com drift detection** | 4 triggers (score, aprovação, custo, latência P95) + alertas automáticos Bell+Teams. Único entre plataformas de recrutamento |
| **FairnessGuard 3 camadas com auditoria SOX** | Camada 1 (regex 40+ patterns) + Camada 2 (léxico implícito) + Camada 3 LLM opt-in + Four-Fifths Rule + snapshots auditáveis. HireVue foi processado por falhar exatamente nisso |
| **Compliance financeiro** | BCB 498 + SOX + ISO 27001 — zero concorrentes têm isso |
| **ReAct loop com LangGraph explícito** | Única plataforma de recrutamento que declara e implementa LangGraph + ReAct como arquitetura central (Gupy confirma LangGraph em JD mas não entregou) |
| **Cascade async com WebSocket** | Celery 5.4 + WebSocket para jobs longos (WSI, triagem em lote, sourcing). Arquitetura de produção enterprise |

---

### 7.12 Onde a LIA Precisa Evoluir (Gaps Técnicos vs. Concorrentes)

| Gap Técnico | Referência | O que fazem que a LIA não faz |
|---|---|---|
| **Fine-tuning proprietário** | Paradox, Tezi, HireVue, Eightfold | Modelos treinados em dados próprios de domínio superam prompts genéricos em precisão e custo. A LIA depende 100% de APIs sem fine-tuning |
| **Análise de sinais comportamentais em áudio** | DigAI (MIT) | Além do conteúdo semântico, detectam padrões prosódicos e comportamentais que humanos não percebem conscientemente — 79,4% de acerto validado |
| **Self-learning / melhoria contínua** | Beam AI (Task Mining) | Agentes que aprendem com interações e modificam seu comportamento automaticamente. A LIA não tem feedback loop de aprendizado |
| **Digital Twin / knowledge graph por colaborador** | Eightfold (Project Andromeda) | LLM personalizado por colaborador integrando email, Slack, código — memória organizacional distribuída |
| **Entrevista em vídeo** | HireVue, Popp AI | Análise de conteúdo de respostas em vídeo assíncrono. Deepgram já está integrado — é o caminho mais curto |
| **Multi-LLM routing por tipo de tarefa** | Beam AI (ModelMesh) | Usar Claude para extração, GPT-4o para raciocínio, Command R para RAG — cada tarefa com o modelo mais adequado além da cascade de confiança |

---

## 8. Referências Técnicas

**Paradox:**
- [AI 101: The AI Behind Our Assistant](https://www.paradox.ai/blog/ai-101-the-ai-behind-our-assistant)
- [Paradox AI Deep Dive — Gene DAI Substack](https://genedai.substack.com/p/paradox-ai-olivia-deep-dive-the-conversational)

**Tezi AI:**
- [Tezi raises $9M — blog.tezi.ai](https://blog.tezi.ai/p/tezi-raises-9m-to-launch-max-the)
- [8VC Investment Thesis](https://www.8vc.com/resources/ready-ai-hire-announcing-our-investment-in-tezi)
- [TechCrunch — Tezi is building an AI agent](https://techcrunch.com/2024/07/31/tezi-is-building-an-ai-agent-for-hiring-managers/)

**Beam AI:**
- [ModelMesh — Multi-model approach](https://beam.ai/agentic-insights/modelmesh-a-multi-model-approach-by-beam-ai)
- [Self-Learning AI Agents](https://beam.ai/agentic-insights/self-learning-ai-agents-transforming-automation-with-continuous-improvement)

**Eightfold AI:**
- [Engineering Blog — Talent Matching](https://eightfold.ai/engineering-blog/ai-powered-talent-matching-the-tech-behind-smarter-and-fairer-hiring/)
- [Project Andromeda — Digital Twins](https://eightfold.ai/engineering-blog/agentic-operating-system-digital-twins/)
- [Recruiter Agent Launch (GlobeNewsWire)](https://www.globenewswire.com/news-release/2025/08/19/3135928/0/en/Eightfold-AI-Launches-Recruiter-Agent-Built-for-Hyper-Personalized-Always-On-High-Volume-Hiring.html)

**HireVue:**
- [2024 AI Explainability Statement (PDF)](https://www.hirevue.com/wp-content/uploads/2024/09/HV_2024_AI-Explainability-Statement.pdf)
- [CDT Analysis — Explainability gaps](https://cdt.org/insights/hirevue-ai-explainability-statement-mostly-fails-to-explain-what-it-does/)
- [Frontiers in Psychology — Game-based assessments](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2022.942662/full)

**DigAI:**
- [100K entrevistas WhatsApp](https://blog.digai.ai/2025/06/24/como-a-digai-realizou-100-mil-entrevistas-com-ia-via-whatsapp-e-se-tornou-referencia-em-recrutamento-automatizado/)
- [Web Summit Rio 2025](https://rio.websummit.com/blog/news/digais-ai-agent-triumphs-in-web-summit-rio-pitch-competition/)

**Gupy:**
- [Nova Ordenação com Agentes de IA](https://www.gupy.io/en/nova-ordenacao-com-agentes-de-ia)
- [Vaga Arquiteto de Soluções de IA (confirma LangGraph/Google ADK)](https://leega.gupy.io/jobs/10721123)
- [IT Forum — Gupy Agentes IA](https://itforum.com.br/noticias/gupy-agentes-ia/)

**Mercado geral:**
- Paradox: aquisição Workday (out/2025), newsroom.workday.com
- Popp AI: TIARA Champion 2025, joinpopp.com
- HireVue: ACLU complaint (mar/2025), hrdive.com
- Phenom: Gartner Magic Quadrant Visionary 2025, phenom.com
- hireEZ: Agentic AI launch 2025, hireez.com
- Leonar: "13 Best AI Recruiting Tools in 2026", leonar.app

---

*Documento v2.0 — Seções 1–6: análise comercial/funcional. Seção 7: engenharia reversa técnica. Revisão trimestral recomendada.*
