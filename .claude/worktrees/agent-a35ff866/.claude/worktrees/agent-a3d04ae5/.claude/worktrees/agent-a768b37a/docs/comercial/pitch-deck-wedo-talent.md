# WeDo Talent + LIA - Pitch Deck Final
**Recrutamento Autônomo com Agentes de IA**

---

## Slide 1: Tese Inicial - Parceria Taqtile

**"Automatização de Triagem de Candidatos via WhatsApp com IA"**

- Parceria estratégica com Taqtile (consultoria de inovação)
- Foco inicial: **LIA** - agente de IA para triagem conversacional via WhatsApp
- Metodologia proprietária **WSI** (Work Sample Interview) integrada
- Base científica: Bloom's Taxonomy + Dreyfus Model + Big Five + CBI

---

## Slide 2: Jornada de Recrutamento - Tese Taqtile

| Etapa | Status | Descrição |
|-------|--------|-----------|
| Criação de Vaga | ⬜ | |
| Publicação + Validação | ⬜ | |
| **Sourcing** | ✅ | |
| **Triagem WhatsApp** | ✅ | |
| **Agendamento** | ✅ | |
| Avaliação Pós-Entrevista | ⬜ | |
| Proposta + Contratação | ⬜ | |
| Feedbacks Automatizados | ⬜ | |

**Escopo inicial: 3 etapas do funil**

---

## Slide 3: Findings - Problemas Identificados no Desenvolvimento

### Durante o processo, identificamos desafios críticos:

| Problema | Impacto | Fonte |
|----------|---------|-------|
| **Tese atrasada** | Delay no cronograma de entrega | Interno |
| **Qualidade das perguntas de triagem** | Baixa assertividade, eficácia e qualidade da avaliação | Testes internos |
| **Gargalo de integração ATS** | Duplicação de trabalho e abandono do produto | Cliente Afya (caso DigAí) |
| **Falta de banco de candidatos** | Empresas sem LinkedIn Recruiter nem base própria | Clientes diversos |
| **Concorrentes avançando com IA** | Tezi ($9M), Findem ($51M), HireEZ lançando agentes | Análise de mercado |
| **Experiência fragmentada** | Candidatos perdidos entre canais | Feedback de usuários |

### Conclusão:
> "Precisávamos expandir a tese para resolver problemas sistêmicos do recrutamento"

---

## Slide 4: Jornada de Recrutamento - Tese Atualizada

| Etapa | Status | Descrição |
|-------|--------|-----------|
| **Criação de Vaga** | ✅ | Wizard assistido por **Agentes de IA** com 8 etapas + Feedback da IA sobre a vaga com base em informações de mercado e **metodologia de clusterização** (artigo AI em Skills) |
| Publicação + Validação | ✅ | Sugestões automáticas de melhorias na JD |
| **Sourcing** | ✅ | Busca local + global integrada ao **Pearch (40M+ candidatos)** |
| **Triagem WhatsApp** | ✅ | **LIA** conduz entrevistas conversacionais com **metodologia WSI** para criar perguntas e avaliar candidatos |
| **Agendamento** | ✅ | Integração Microsoft Graph + self-scheduling |
| **LIA Assistente Teams** | ✅ | **LIA como Assistente de Recrutamento** do recrutador via Microsoft Teams (Copilot) |
| Avaliação Pós-Entrevista | 🔜 | Rankings + Pareceres automáticos |
| Proposta + Contratação | 🔜 | Elaboração e apresentação assistidas |
| Feedbacks Automatizados | 🔜 | Em todas as etapas do processo |

**Visão: Agentes de IA em 100% do funil**

---

## Slide 5: Diferenciais + Impacto

| Diferencial | Descrição | Impacto |
|-------------|-----------|---------|
| **Metodologia WSI** | Avaliação estruturada (técnica + comportamental) | Triagem consistente e objetiva |
| **Clusterização de Perfis** | IA sugere melhorias na vaga antes da publicação | Vagas melhor estruturadas |
| **Busca Semântica LLM** | 8 domínios com expansão inteligente | Sourcing muito mais assertivo |
| **LIA Copilot no Teams** | Assistente pessoal do recrutador | Suporte em tempo real |
| **Pearch 40M+** | Banco de talentos integrado | Resolve falta de candidatos |

### ROI Comprovado
- **80%** redução de tempo operacional
- **2,3x** mais vagas gerenciadas por recrutador
- Experiência do candidato drasticamente melhorada

---

## Slide 6: Expansão da Tese - Pivot Estratégico

### Arquitetura de Agentes WeDo Talent

| Agente | Função |
|--------|--------|
| **Job Intake Agent** | Criação de vagas conversacional + clusterização |
| **Screening Agent** | Pipeline CV → Rubrics → Score → Timeline (WSI) |
| **Scheduling Agent** | Agendamento + conflitos + lembretes |
| **Communication Agent** | Omnichannel + templates + LGPD |
| **Task Planner Agent** | Decomposição DAG + priorização |
| **Policy Engine** | Regras de negócio + rate-limiting |

**Stack Tecnológica:** FastAPI + LangGraph + Claude Sonnet + PostgreSQL

### Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR                             │
│              (Coordena todos os agentes)                     │
└─────────────────────────────────────────────────────────────┘
         │           │           │           │           │
         ▼           ▼           ▼           ▼           ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ JOB INTAKE  │ │  SCREENING  │ │ SCHEDULING  │ │COMMUNICATION│ │TASK PLANNER │
│   AGENT     │ │    AGENT    │ │    AGENT    │ │    AGENT    │ │    AGENT    │
├─────────────┤ ├─────────────┤ ├─────────────┤ ├─────────────┤ ├─────────────┤
│• Wizard 8   │ │• CV parsing │ │• MS Graph   │ │• 8 canais   │ │• DAG decomp │
│  etapas     │ │• Rubrics    │ │• Self-sched │ │• 38 templa- │ │• Topological│
│• JD extract │ │• Red flags  │ │• Conflitos  │ │  tes        │ │  sorting    │
│• WSI quest. │ │• Batch proc │ │• Lembretes  │ │• LGPD aware │ │• Priority   │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
                                      │
                                      ▼
                          ┌─────────────────────┐
                          │   POLICY ENGINE     │
                          ├─────────────────────┤
                          │ • Business rules    │
                          │ • Rate-limiting     │
                          │ • Escalation flows  │
                          └─────────────────────┘
```

---

## Slide 7: WeDo Talent vs Concorrentes Globais

| Funcionalidade | WeDo Talent | Tezi AI | Findem | Paradox | HireEZ | Juicebox |
|----------------|-------------|---------|--------|---------|--------|----------|
| **Triagem WhatsApp** | ✅ LIA | ❌ Slack | ❌ | ❌ SMS | ❌ | ❌ |
| **Arquitetura Multiagentes** | ✅ 6+ | ✅ Dezenas | ✅ 5+ | ❌ | ⚠️ Semi | ✅ |
| **Banco de Talentos** | ✅ 40M+ | ✅ 750M+ | ✅ 800M+ | ❌ | ✅ 800M+ | ✅ 800M+ |
| **Metodologia Estruturada** | ✅ WSI | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Copilot/Assistente** | ✅ Teams | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Busca Semântica LLM** | ✅ 8 domínios | ✅ | ✅ 3D Data | ❌ | ✅ | ✅ |
| **Foco Mercado** | 🇧🇷 Brasil | 🌎 Global | 🌎 Global | 🌎 Alto volume | 🌎 Global | 🌎 Global |
| **Funding** | - | $9M | $51M | $200M+ | - | $36M |

### Detalhes dos Concorrentes Globais

| Plataforma | País | Diferencial Principal | Arquitetura IA |
|------------|------|----------------------|----------------|
| **Tezi AI** | EUA | Max (agente autônomo full-cycle) | Multiagentes (dezenas) |
| **Findem** | EUA | 3D Talent Data + Success Signals | Multiagentes (5+ especializados) |
| **Paradox AI** | EUA | Olivia chatbot 24/7 (alto volume) | Chatbot único |
| **HireEZ** | EUA | EZ Agent (semi-autônomo) + CRM | Agentic AI (semi) |
| **Juicebox** | EUA | PeopleGPT (linguagem natural) | AI Agents 24/7 |
| **Humanly** | EUA | Video interviewer + DEI focus | LLM único |
| **Hirefly** | EUA | Autopilot mode (outbound) | Automação |

---

## Slide 8: WeDo Talent vs Concorrentes Brasil

| Funcionalidade | WeDo Talent | DigAí | Coploy | Recrut.AI | Gupy | InHire |
|----------------|-------------|-------|--------|-----------|------|--------|
| **Triagem WhatsApp** | ✅ Texto + Voz | ✅ Áudio | ❌ | ❌ | ❌ | ✅ |
| **Arquitetura Multiagentes** | ✅ 6+ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Banco de Talentos Integrado** | ✅ 40M+ Pearch | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Metodologia Estruturada** | ✅ WSI | ⚠️ Fit cultural | ⚠️ Body lang | ❌ | ❌ | ❌ |
| **Copilot/Assistente** | ✅ Teams | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Busca Semântica LLM** | ✅ | ❌ | ❌ | ⚠️ NLP | ⚠️ Gaia | ⚠️ IA |
| **Video Interviews** | 🔜 | ❌ | ✅ | ✅ | ❌ | ❌ |

### Detalhes dos Concorrentes Brasil

| Plataforma | Foco | Diferencial | Funding |
|------------|------|-------------|---------|
| **DigAí** | Triagem WhatsApp áudio | 79% precisão (MIT) | R$1.5M |
| **Coploy** | Video interviews | Análise body language | R$1.5M |
| **Recrut.AI** | Volume hiring (varejo) | +97% precisão ranking | - |
| **Gupy** | ATS full ecosystem | Gaia (Watson-based) | $93M |
| **InHire** | ATS para recrutadores | Suite IA (add-on) | DGF investment |

### Conclusão
> **Nenhum concorrente brasileiro tem banco de talentos integrado + arquitetura multiagentes**

---

## Slide 9: Roadmap 2025

| Fase | Período | Entregas |
|------|---------|----------|
| **Fase 1** ✅ | Concluída | Triagem WhatsApp + Sourcing + Agendamento + LIA Teams |
| **Fase 2** 🔜 | Q1 2025 | Avaliação pós-entrevista + Rankings + Pareceres |
| **Fase 3** 🔜 | Q2 2025 | Feedbacks automatizados em todas as etapas |
| **Fase 4** 🔜 | Q3 2025 | Proposta + Contratação automatizadas |

### Próximos Passos Imediatos
1. Expandir automação de feedbacks para candidatos
2. Assistente IA no Teams para suporte ao recrutador
3. Clusterização de perfis com parecer sobre vagas
4. Ajudar gestores a construir perfis aderentes ao mercado

### Visão de Longo Prazo
> "O recrutador focado apenas em decisões estratégicas - todo o operacional automatizado por agentes de IA"

---

## Anexo A: Funcionalidades do Funil de Talentos

- Busca semântica com 8 domínios LLM
- 5 modos de busca unificados (Linguagem Natural, Similar, Descrição da Vaga, Boolean, Arquétipos)
- Filtros avançados com 53 campos
- Escopo Local/Híbrido/Global
- Integração Pearch (40M+ candidatos)

---

## Anexo B: Funcionalidades de Gestão de Vagas

- Wizard de 8 etapas com IA
- Extração automática de requisitos
- Geração de perguntas de triagem WSI
- Clusterização de perfis
- Publicação multi-canal

---

## Anexo C: Compliance & Segurança

- LGPD completo (Art. 18, Art. 20)
- NYC LL144, EU AI Act, FEHA
- Bias audit system
- SOC 2 Type II, ISO 27001
- BCB 498/2025

---

## Anexo D: Análise Detalhada de Mercado

### Concorrentes com Arquitetura Multiagentes

| Plataforma | Nº Agentes | Funding | Diferenciais |
|------------|------------|---------|--------------|
| **WeDo Talent** | 6+ especializados | - | WhatsApp + WSI + Pearch 40M+ |
| **Tezi AI** | Dezenas | $9M Series A | Max agente autônomo |
| **Findem** | 5+ especializados | $51M Series C | 3D Talent Data |
| **HireEZ** | 1 (semi-autônomo) | - | EZ Agent + CRM |
| **Juicebox** | Múltiplos | $36M | PeopleGPT |

### Concorrentes sem Arquitetura Multiagentes

| Plataforma | Tipo de IA | Limitação |
|------------|------------|-----------|
| **Paradox** | Chatbot único | Sem banco de talentos |
| **Humanly** | LLM único | Foco em DEI/video |
| **DigAí** | IA conversacional | Sem banco de talentos |
| **Coploy** | IA de vídeo | Apenas entrevistas |
| **Gupy** | Neural networks | ATS tradicional |
| **InHire** | Suite IA (add-on) | ATS tradicional |
| **Recrut.AI** | Automated hunting | Foco volume hiring |

### Diferenciais Únicos WeDo Talent

1. **WhatsApp nativo** - Canal preferido no Brasil (90% penetração)
2. **Arquitetura multiagentes** - Único no Brasil com 6+ agentes especializados
3. **Banco Pearch integrado** - 40M+ candidatos (66% LinkedIn Brasil)
4. **Metodologia WSI** - Base científica para avaliação
5. **Copilot Teams** - Assistente pessoal do recrutador
6. **Busca semântica 8 domínios** - Expansão inteligente com LLM

---

*Documento gerado em Dezembro 2024*
*WeDo Talent - Recrutamento Autônomo com Agentes de IA*
