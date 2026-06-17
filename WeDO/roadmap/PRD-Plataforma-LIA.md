# PRD - WeDOTalent + LIA (Learning Intelligence Assistant)
## Product Requirements Document v3.3

**Data:** Dezembro 2025  
**Status:** MVP Avançado  
**Versão:** 3.3  
**Maturidade Real:** ~55% implementado  
**Marca:** WeDOTalent (plataforma + marca mãe)

---

# 📋 Índice

## Parte I: Visão do Produto
1. [Visão Executiva](#1-visão-executiva)
    - 1.5 Contexto Empresarial (Grupo Talenses)
    - 1.6 Posicionamento de Produto (Service as Software)
2. [Problema e Oportunidade](#2-problema-e-oportunidade)
3. [Personas e Usuários](#3-personas-e-usuários)
    - 3.4 Founder/CEO de Startup
    - 3.5 Líder de TA (Alto Volume)
    - 3.6 Segmentos de Mercado
    - 3.7 Perfis Tech Suportados
4. [Proposta de Valor](#4-proposta-de-valor)

## Parte II: Especificação Técnica
5. [Funcionalidades Core](#5-funcionalidades-core)
6. [Arquitetura Multi-Agent](#6-arquitetura-multi-agent)
7. [Modelo de Dados](#7-modelo-de-dados)
8. [Integrações](#8-integrações)
9. [Requisitos Técnicos](#9-requisitos-técnicos)

## Parte III: Métricas e Planejamento
10. [Métricas de Sucesso](#10-métricas-de-sucesso)
11. [Roadmap](#11-roadmap)
12. [Riscos e Mitigações](#12-riscos-e-mitigações)
13. [Estado Atual vs Planejado](#13-estado-atual-vs-planejado)
14. [Estratégia de Migração](#14-estratégia-de-migração)
    - 14.1 Contexto e Situação Atual
    - 14.2 Estratégia Híbrida (Recomendada)
    - 14.3 O Que Aproveitar do Replit
    - 14.4 O Que NÃO Migrar
    - 14.5 Integração Backend: Rails ↔ FastAPI
    - 14.6 Plano de Execução em 3 Ondas
    - 14.7 Uso Contínuo do Replit
    - 14.8 Métricas de Sucesso
    - 14.9 Cronograma Consolidado
    - 14.10 Riscos e Mitigações
    - 14.11 Design Tokens Exportáveis
    - 14.12 Contrato OpenAPI Rails ↔ FastAPI

## Parte IV: Arquitetura e Estratégia
15. [Arquitetura Multi-Agentes Detalhada](#15-arquitetura-multi-agentes-detalhada)
    - 15.1 Visão Geral do Sistema Multi-Agente
    - 15.2 Os 6 Agentes Especializados
    - 15.3 Orquestração e Fluxo de Trabalho
    - 15.4 Loops de Autoaprendizagem
    - 15.5 Arquitetura de IA Técnica (LLMs, RAG, Prompts)
16. [Modelo de Monetização e Pricing](#16-modelo-de-monetização-e-pricing)
17. [Análise Build vs Buy](#17-análise-build-vs-buy)
18. [Metodologia WSI](#18-metodologia-wsi-wedo-screening-interview)
19. [Roadmap de Features](#19-roadmap-de-features)
20. [Estratégia de Crescimento](#20-estratégia-de-crescimento)
    - 20.5 Estratégia de Comunidade e Geração de Leads

## Parte V: Inteligência Competitiva e Benchmarking
21. [Panorama de Concorrentes Agentic AI](#21-panorama-de-concorrentes-agentic-ai)
    - 21.1 Matriz Comparativa (9 Plataformas)
    - 21.2 Análise Detalhada por Concorrente
    - 21.3 Insights Estratégicos
22. [Stacks Voice AI e Benchmark de Custos](#22-stacks-voice-ai-e-benchmark-de-custos)
    - 22.1 Stack Best-of-Breed (Build)
    - 22.2 Plataformas Voice AI Prontas (Buy)
    - 22.3 Comparativo de Custos
23. [Infraestrutura Agentic e Orquestração](#23-infraestrutura-agentic-e-orquestração)
    - 23.1 Plataformas de Infraestrutura
    - 23.2 Matriz de Decisão
    - 23.3 Custos Projetados (36 meses)
24. [Decisão Estratégica Build vs Buy (36m)](#24-decisão-estratégica-build-vs-buy-36m)
    - 24.1 Análise TCO Detalhada
    - 24.2 Critérios de Decisão
    - 24.3 Roadmap Híbrido Recomendado
25. [Guia Agentic vs Conversacional](#25-guia-agentic-vs-conversacional)
    - 25.1 Quando Usar Cada Abordagem
    - 25.2 Arquiteturas de Referência
    - 25.3 Critérios de Migração
    - 25.4 Stack Recomendada WeDOTalent

---

# ⚠️ IMPORTANTE: Estado do Projeto

> **Este PRD descreve a VISÃO COMPLETA do produto. O estado atual de implementação é de aproximadamente 55%.** 
>
> Consulte a [Seção 13](#13-estado-atual-vs-planejado) para entender o que está implementado vs planejado.
>
> **Principais conquistas recentes (Dezembro 2025):**
> - ✅ 80+ tabelas no banco de dados
> - ✅ 200+ endpoints de API
> - ✅ WeDo Talent Admin com arquitetura de 3 pilares
> - ✅ Compliance Health Check (242 itens, 7 frameworks)
> - ✅ LGPD Portal do Titular completo
> - ✅ BCB 498/2025 Cyber Insurance
> - ✅ AI-powered search filters (Ask AI, Find Similar)

---

# 1. Visão Executiva

## 1.1 Resumo do Produto

**WeDOTalent** é uma plataforma de recrutamento AI-first brasileira que combina a **LIA** (Learning Intelligence Assistant) - agente de IA conversacional - com um ATS completo. O produto oferece interface baseada em chat via WhatsApp e Microsoft Teams, onde recrutadores executam tarefas complexas através de linguagem natural, substituindo fluxos manuais por workflows inteligentes orquestrados por agentes especializados.

## 1.2 Missão

> Transformar o recrutamento corporativo através de IA conversacional, reduzindo o tempo de contratação em 60% e aumentando a qualidade das contratações através de análise preditiva e triagem inteligente.

## 1.3 Visão de Produto (3 anos)

Ser a plataforma líder em recrutamento AI-first na América Latina, processando mais de 1 milhão de candidatos/mês e integrando-se nativamente com os principais ATSs do mercado brasileiro.

## 1.4 Diferenciais Competitivos (Implementados)

| Diferencial | Descrição | Status |
|-------------|-----------|--------|
| **AI-First** | Interface conversacional como modo primário | ✅ Funcional |
| **Multi-Agent** | 11 agentes especializados (1 orchestrator + 10 especializados) | ✅ Implementado |
| **WSI Methodology** | Triagem por voz com Deepgram + análise comportamental | 🟡 Voice tests implementados |
| **Two-Tier Search** | Busca local + Pearch AI para cobertura completa | ✅ Funcional |
| **ATS Agnóstico** | Integração bidirecional com Gupy, Pandapé, StackOne (40+ ATSs) | 🟡 3 clientes funcionais |

## 1.5 Contexto Empresarial

### Grupo Talenses (Empresa Mãe)

| Métrica | Valor |
|---------|-------|
| **Anos no mercado** | 10+ anos |
| **Clientes ativos** | 300+ |
| **Profissionais contratados** | 4.000+ |
| **Fundador** | Paulo Moraes |

### Filosofia WeDOTalent

1. **Tecnologia a serviço da humanidade** - IA que amplifica, não substitui
2. **Respeito pela experiência do candidato** - 99% recebem resposta
3. **Conexão omnichannel** - WhatsApp, Teams, ATSs integrados
4. **IA responsável e transparente** - Explicabilidade nas decisões
5. **Melhoria contínua** - Feedback loops de aprendizado
6. **Resultados mensuráveis** - ROI comprovado

## 1.6 Posicionamento de Produto

### "Service as Software"

Modelo diferenciado que combina tecnologia + suporte dedicado:

```
┌─────────────────────────────────────────────────────────────────┐
│               SERVICE AS SOFTWARE                                │
│                                                                  │
│   SaaS Tradicional          WeDOTalent                          │
│   ────────────────          ──────────                          │
│   • Self-service            • Success Manager dedicado          │
│   • Setup semanas           • Setup em 1 dia                    │
│   • Suporte por email       • Suporte via WhatsApp direto       │
│   • Pricing fixo            • Modelo consultivo                 │
│   • Ferramenta genérica     • Português nativo, BR-first        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Diferenciais Únicos

| Diferencial | Descrição |
|-------------|-----------|
| **AI-First, não AI-Added** | IA nativa desde a concepção, não add-on |
| **Choose Your AI** | Cliente escolhe motor de IA (Claude, GPT, Gemini) |
| **WhatsApp-First** | Conversa natural no canal preferido do brasileiro |
| **Plugin ou Standalone** | Flexibilidade: complementa ATS existente ou substitui |
| **Dados para Decisões** | Analytics preditivo para estratégia de RH |

### Métricas de Produto (Targets)

> ⚠️ **Nota:** Estas são metas aspiracionais baseadas em benchmarks de mercado e expectativas do produto. O status atual de implementação é ~5%. As métricas serão validadas após implementação dos módulos core.

| Métrica | Target | Benchmark Mercado | Milestone |
|---------|--------|-------------------|-----------|
| Precisão no match CV-vaga | 92% | 70-75% | Após Screening Agent |
| Conversão agendamento | 95% | 60-70% | Após Scheduling Agent |
| Candidatos respondidos | 99% | 25-30% | Após Communication Agent |
| Satisfação candidatos | 4.8/5 | 3.5/5 | Após WSI implementado |
| Redução time-to-hire | 70% | 20-30% | Após orquestrador completo |
| Redução trabalho manual | 80% | 40-50% | Após 6 agentes ativos |
| ROI comprovado | 5x | 2-3x | Após 6 meses operação |

### Capacidade Operacional

| Métrica | Capacidade |
|---------|------------|
| Vagas simultâneas | 80+ |
| Candidatos processados/mês | 15.000+ |
| Setup time | 1 dia |
| Entrevistas WSI/dia | 1.000+ |

---

# 2. Problema e Oportunidade

## 2.1 Problemas do Mercado

### Para Recrutadores
- **Sobrecarga operacional**: 70% do tempo gasto em tarefas repetitivas
- **Triagem manual ineficiente**: Análise superficial de currículos por volume
- **Comunicação fragmentada**: Múltiplas ferramentas sem integração
- **Falta de insights**: Decisões baseadas em intuição, não dados

### Para Empresas
- **Time-to-hire elevado**: Média de 45 dias no Brasil
- **Custo por contratação alto**: R$ 3.000-8.000 por posição
- **Alta rotatividade**: 40% de turnover no primeiro ano por má seleção
- **Viés inconsciente**: Processos manuais perpetuam discriminação

### Para Candidatos
- **Black hole de candidaturas**: 75% nunca recebem resposta
- **Processo desumanizado**: Formulários longos, falta de feedback
- **Experiência inconsistente**: Cada empresa com processo diferente

## 2.2 Tamanho do Mercado

| Métrica | Valor |
|---------|-------|
| TAM (Global HR Tech) | $35B (2025) |
| SAM (LATAM Recruitment) | $2.8B |
| SOM (Brasil Enterprise) | $400M |
| Crescimento Anual | 12% CAGR |

## 2.3 Oportunidade

Com a adoção acelerada de IA generativa (ChatGPT, Claude), empresas estão prontas para interfaces conversacionais. A LIA capitaliza esta mudança cultural oferecendo uma experiência familiar (chat) para tarefas complexas (recrutamento).

---

# 3. Personas e Usuários

## 3.1 Persona Primária: Recrutador(a) Tech

**Nome:** Ana, 28 anos  
**Cargo:** Tech Recruiter Sênior  
**Empresa:** Startup de tecnologia (200-500 funcionários)  

### Perfil
- Gerencia 15-25 vagas simultâneas
- Usa 5+ ferramentas diariamente (ATS, LinkedIn, WhatsApp, Email, Planilhas)
- Pressão por métricas (time-to-fill, cost-per-hire)
- Trabalho híbrido, precisa de mobilidade

### Dores
- "Perco 3h/dia só respondendo candidatos"
- "Não consigo comparar candidatos de forma objetiva"
- "O ATS é burocrático demais"
- "Não tenho tempo de dar feedback personalizado"

### Objetivos
- Reduzir tempo em tarefas operacionais
- Melhorar qualidade dos candidatos apresentados
- Ter dados para justificar decisões
- Oferecer experiência melhor aos candidatos

### Comportamento Esperado com LIA
```
Ana: "LIA, busque desenvolvedores Python sênior em São Paulo, 
      remoto ok, pretensão até 25k"

LIA: "Encontrei 47 candidatos no banco interno e 23 via Pearch.
      Dos 70, 12 têm match acima de 85%. Quer que eu inicie 
      triagem por voz com os top 5?"
```

---

## 3.2 Persona Secundária: Gestor de RH

**Nome:** Carlos, 42 anos  
**Cargo:** Head de People  
**Empresa:** Empresa média (500-2000 funcionários)  

### Perfil
- Reporta para C-Level
- Responsável por budget de R&S
- Foco em métricas e compliance
- Precisa de visão estratégica

### Dores
- "Não tenho visibilidade do funil de contratação"
- "Gastamos muito com consultorias externas"
- "Não consigo provar ROI das iniciativas"
- "Processos inconsistentes entre áreas"

### Objetivos
- Dashboard executivo em tempo real
- Padronização de processos
- Redução de custos
- Compliance trabalhista

---

## 3.3 Persona Terciária: Hiring Manager

**Nome:** Roberto, 35 anos  
**Cargo:** Engineering Manager  
**Empresa:** Qualquer segmento  

### Perfil
- Não é de RH, mas participa do processo
- Tempo limitado para entrevistas
- Quer candidatos já filtrados
- Precisa de contexto rápido

### Dores
- "Recebo candidatos que não têm fit técnico"
- "Não tenho tempo de ler 50 currículos"
- "Quero saber a opinião do RH antes da entrevista"
- "Feedback do processo demora muito"

---

## 3.4 Persona: Founder/CEO de Startup

**Nome:** Marina, 32 anos  
**Cargo:** CEO e Co-founder  
**Empresa:** Startup early-stage (10-50 funcionários)  

### Perfil
- Sem time de RH dedicado
- Precisa contratar rápido para crescer
- Orçamento limitado
- Faz tudo: produto, vendas, RH

### Dores
- "Não tenho tempo nem expertise para recrutar"
- "Perco candidatos bons por demora no processo"
- "Não sei avaliar fit cultural"
- "Consultorias são caras demais"

### Objetivos
- Contratar sem ter time de RH
- Setup rápido (1 dia)
- Preço fixo e previsível
- Processo profissional desde o início

### Solução WeDOTalent
> "Contrate sem ter time de RH" - Setup 1 dia, preço fixo, LIA faz a triagem

---

## 3.5 Persona: Líder de TA (Alto Volume)

**Nome:** Fernanda, 38 anos  
**Cargo:** Head of Talent Acquisition  
**Empresa:** Varejo/Logística (5000+ funcionários)  

### Perfil
- 50+ vagas abertas simultaneamente
- Equipe de 10+ recrutadores
- Pressão por velocidade e volume
- Processos padronizados

### Dores
- "Minha equipe não escala com a demanda"
- "Qualidade cai quando volume sobe"
- "Candidatos desistem por demora"
- "Processos inconsistentes entre recrutadores"

### Objetivos
- Escalabilidade infinita
- Consistência no processo
- 80+ vagas simultâneas
- Métricas unificadas

### Solução WeDOTalent
> "50+ vagas abertas? LIA dá conta" - Escalabilidade infinita, consistência garantida

---

## 3.6 Segmentos de Mercado

| Segmento | Headline | Público-alvo | Benefícios |
|----------|----------|--------------|------------|
| **Startups & Scale-ups** | "Contrate sem ter time de RH" | Founders, CEOs early-stage | Setup 1 dia, preço fixo, zero overhead |
| **Alto Volume** | "50+ vagas? LIA dá conta" | Varejo, Logística, Call Center | Escalabilidade, consistência, 80+ vagas |
| **Tecnologia** | "Especializada em perfis tech" | Empresas de TI | Avalia stacks, senioridade, red flags |
| **Enterprise** | "Integração total" | Grandes corporações | Plugin ATS, API, customização, SSO |

## 3.7 Perfis Tech Suportados

A LIA possui conhecimento especializado para avaliar:

| Categoria | Perfis |
|-----------|--------|
| **Desenvolvimento** | Full Stack, Frontend, Backend, Mobile (iOS/Android) |
| **Infraestrutura** | DevOps, SRE, Cloud Engineer |
| **Dados** | Data Engineer, Data Scientist, Data Analyst, ML Engineer |
| **Produto** | Product Manager, Product Owner, Product Designer |
| **Design** | UI Designer, UX Designer, UX Researcher |
| **Qualidade** | QA Engineer, Test Engineer, SDET |
| **Segurança** | Security Engineer, InfoSec, Pentester |
| **Arquitetura** | Solutions Architect, Tech Lead, Staff Engineer |

---

# 4. Proposta de Valor

## 4.1 Value Proposition Canvas

### Para Recrutadores
| Dor | Solução LIA | Ganho Esperado |
|-----|-------------|----------------|
| Triagem manual | Triagem por voz automatizada (WSI) | -80% tempo triagem |
| Busca fragmentada | Two-tier search (local + Pearch) | +3x candidatos qualificados |
| Comunicação dispersa | Omnichannel integrado | -60% tempo comunicação |
| Falta de dados | LIA Score + Analytics | Decisões data-driven |

### Para Empresas
| Dor | Solução LIA | Ganho Esperado |
|-----|-------------|----------------|
| Time-to-hire alto | Automação de 70% do processo | -45% tempo contratação |
| Custo elevado | Eficiência operacional | -35% custo por hire |
| Rotatividade | Análise preditiva Big Five | -25% turnover 1º ano |
| Compliance | Audit trail completo | 100% rastreabilidade |

## 4.2 Unique Selling Proposition (USP)

> **"Contrate em dias, não meses. A LIA é sua recrutadora AI que nunca dorme, nunca esquece e sempre aprende."**

## 4.3 Modelo de Monetização (Planejado)

| Plano | Preço | Inclui |
|-------|-------|--------|
| **Starter** | R$ 990/mês | 3 usuários, 10 vagas, 50 triagens/mês |
| **Professional** | R$ 2.990/mês | 10 usuários, vagas ilimitadas, 200 triagens |
| **Enterprise** | Sob consulta | Customizado, SLA, integrações dedicadas |

---

# 5. Funcionalidades Core

## Legenda de Status
- ✅ Implementado
- 🟡 Parcialmente implementado
- 🔴 Não implementado (planejado)

---

## 5.1 Módulo 1: Gestão de Candidatos

**Status Geral:** 🟡 Parcialmente implementado

### 5.1.1 Cadastro de Candidatos

**Campos do Candidato (49 campos definidos no banco):**

#### Identificação
| Campo | Tipo | Status |
|-------|------|--------|
| id | UUID | ✅ |
| name | varchar | ✅ |
| email | varchar | ✅ |
| phone | varchar | ✅ |

#### Links Profissionais
| Campo | Tipo | Status |
|-------|------|--------|
| linkedin_url | varchar | ✅ Schema |
| github_url | varchar | ✅ Schema |
| portfolio_url | varchar | ✅ Schema |

#### Dados Profissionais
| Campo | Tipo | Status |
|-------|------|--------|
| current_title | varchar | ✅ Schema |
| current_company | varchar | ✅ Schema |
| seniority_level | varchar | ✅ Schema |
| years_of_experience | integer | ✅ Schema |

#### Skills e Competências
| Campo | Tipo | Status |
|-------|------|--------|
| technical_skills | ARRAY | ✅ Schema |
| soft_skills | ARRAY | ✅ Schema |
| languages | JSON | ✅ Schema |
| certifications | ARRAY | ✅ Schema |

#### Localização
| Campo | Tipo | Status |
|-------|------|--------|
| location_city | varchar | ✅ Schema |
| location_state | varchar | ✅ Schema |
| location_country | varchar | ✅ Schema |
| is_remote | boolean | ✅ Schema |
| willing_to_relocate | boolean | ✅ Schema |

#### Pretensão Salarial
| Campo | Tipo | Status |
|-------|------|--------|
| desired_salary_min | double | ✅ Schema |
| desired_salary_max | double | ✅ Schema |
| salary_currency | varchar | ✅ Schema |
| work_model_preference | varchar | ✅ Schema |
| contract_type_preference | varchar | ✅ Schema |

#### Currículo
| Campo | Tipo | Status |
|-------|------|--------|
| resume_url | varchar | ✅ Schema |
| resume_text | text | ✅ Schema |
| cover_letter | text | ✅ Schema |

#### Integrações
| Campo | Tipo | Status |
|-------|------|--------|
| source | varchar | ✅ |
| ats_source_name | varchar | ✅ Schema |
| ats_candidate_id | varchar | ✅ Schema |
| pearch_profile_id | varchar | ✅ Schema |

#### Análise LIA
| Campo | Tipo | Status |
|-------|------|--------|
| lia_score | double | ✅ Schema |
| lia_insights | JSON | ✅ Schema |
| skills_match_percentage | double | ✅ Schema |

#### Status e Controle
| Campo | Tipo | Status |
|-------|------|--------|
| status | varchar | ✅ |
| is_active | boolean | ✅ |
| is_blacklisted | boolean | ✅ Schema |
| blacklist_reason | text | ✅ Schema |

#### Preferências de Contato
| Campo | Tipo | Status |
|-------|------|--------|
| preferred_contact_method | varchar | ✅ Schema |
| best_time_to_contact | varchar | ✅ Schema |
| communication_consent | boolean | ✅ Schema |

#### Metadados
| Campo | Tipo | Status |
|-------|------|--------|
| tags | ARRAY | ✅ Schema |
| notes | text | ✅ Schema |
| additional_data | JSON | ✅ Schema |
| created_at | timestamp | ✅ |
| updated_at | timestamp | ✅ |
| last_contacted_at | timestamp | ✅ Schema |
| last_activity_at | timestamp | ✅ Schema |

### 5.1.2 Funcionalidades de Gestão

| Feature | Descrição | Prioridade | Status |
|---------|-----------|------------|--------|
| CRUD completo | Criar, ler, atualizar, deletar | P0 | 🟡 Básico |
| Importação CSV/Excel | Upload em massa com validação | P1 | 🔴 |
| Parsing de CV | Extração automática de dados | P1 | 🔴 |
| Detecção de duplicados | Merge inteligente | P2 | 🔴 |
| Histórico de alterações | Audit log completo | P1 | 🔴 |
| Tags e categorização | Organização flexível | P0 | 🟡 |
| Busca avançada | Filtros combinados | P0 | 🟡 |
| Exportação | PDF, CSV, Excel | P1 | 🔴 |

**Dados Reais no Banco:** 3 candidatos cadastrados

---

## 5.2 Módulo 2: Gestão de Vagas

**Status Geral:** 🔴 Não implementado

### 5.2.1 Estrutura de Vagas (55 campos planejados)

#### Informações Básicas
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | UUID | Identificador único |
| title | varchar | Título da vaga |
| department | varchar | Departamento |
| hiring_manager_id | UUID | Gestor responsável |
| recruiter_id | UUID | Recrutador responsável |
| status | enum | draft, open, paused, closed, filled |

#### Requisitos Técnicos
| Campo | Tipo | Descrição |
|-------|------|-----------|
| required_skills | ARRAY | Skills obrigatórias |
| preferred_skills | ARRAY | Skills desejáveis |
| min_experience | integer | Experiência mínima (anos) |
| max_experience | integer | Experiência máxima |
| education_level | varchar | Formação requerida |
| certifications | ARRAY | Certificações necessárias |
| languages | JSON | Idiomas e níveis |

#### Compensação
| Campo | Tipo | Descrição |
|-------|------|-----------|
| salary_min | double | Salário mínimo |
| salary_max | double | Salário máximo |
| salary_currency | varchar | Moeda |
| bonus_percentage | double | % de bônus |
| benefits | JSON | Benefícios oferecidos |
| equity | boolean | Oferece equity |

#### Modelo de Trabalho
| Campo | Tipo | Descrição |
|-------|------|-----------|
| work_model | enum | remote, hybrid, onsite |
| location | varchar | Localização |
| travel_requirement | varchar | Viagens necessárias |
| contract_type | enum | CLT, PJ, Freelancer |

### 5.2.2 Funcionalidades de Vagas

| Feature | Descrição | Prioridade | Status |
|---------|-----------|------------|--------|
| Criação via chat | LIA extrai dados de descrição | P0 | 🔴 |
| Templates de vagas | Modelos reutilizáveis | P1 | 🔴 |
| Pipeline customizável | Drag-and-drop de etapas | P0 | 🔴 |
| Aprovação workflow | Multi-nível de aprovação | P1 | 🔴 |
| Publicação multi-canal | LinkedIn, Indeed, etc | P2 | 🔴 |
| Analytics por vaga | Métricas de performance | P1 | 🔴 |
| Clonagem de vagas | Duplicar configurações | P2 | 🔴 |
| Arquivamento | Soft delete com histórico | P1 | 🔴 |

**Dados Reais no Banco:** 0 vagas cadastradas

---

## 5.3 Módulo 3: Funil de Talentos (Talent Funnel)

**Status Geral:** 🟡 Frontend visual apenas (dados mock)

### 5.3.1 Abas do Funil

| Aba | Funcionalidade | Status |
|-----|----------------|--------|
| **Candidatos** | Lista principal | 🟡 Visual |
| **Favoritos** | Shortlist | 🟡 Visual |
| **Histórico** | Activity feed | 🟡 Visual |
| **Buscas Salvas** | Queries persistentes | 🟡 Visual |
| **Pipelines** | Kanban visual | 🟡 Visual |

### 5.3.2 Funcionalidades do Funil

| Feature | Descrição | Prioridade | Status |
|---------|-----------|------------|--------|
| Kanban drag-and-drop | Mover candidatos entre etapas | P0 | 🟡 Visual |
| Bulk actions | Ações em lote (50+ candidatos) | P0 | 🔴 |
| Filtros avançados | 15+ critérios combináveis | P0 | 🟡 Visual |
| Ordenação customizada | Por score, data, nome, etc | P0 | 🟡 Visual |
| Preview rápido | Modal de visualização | P0 | 🟡 Visual |
| Comparação lado-a-lado | Até 4 candidatos | P1 | 🟡 Visual |
| Exportação de shortlist | PDF executivo | P1 | 🔴 |
| Notificações de mudança | Alertas real-time | P1 | 🔴 |

**Observação:** O frontend existe visualmente mas opera com dados hardcoded/mock. Não conecta com backend real.

---

## 5.4 Módulo 4: Busca de Candidatos (Two-Tier Search)

**Status Geral:** 🟡 Busca local funciona, Pearch não integrado

### 5.4.1 Arquitetura de Busca (Planejada)

```
┌─────────────────────────────────────────────────┐
│                 USER QUERY                       │
│  "Desenvolvedores Python sênior em São Paulo"    │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│              QUERY PROCESSOR                     │
│  • NLP extraction (skills, location, seniority)  │
│  • Query normalization                           │
│  • Filter construction                           │
└────────────────────┬────────────────────────────┘
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
┌─────────────────┐   ┌─────────────────┐
│   TIER 1        │   │   TIER 2        │
│   LOCAL DB      │   │   PEARCH AI     │
│   PostgreSQL    │   │   External API  │
│   ✅ Funciona   │   │   🔴 Não integr │
└────────┬────────┘   └────────┬────────┘
         │                     │
         └──────────┬──────────┘
                    ▼
┌─────────────────────────────────────────────────┐
│              RESULT MERGER                       │
│  🔴 Não implementado                             │
└─────────────────────────────────────────────────┘
```

### 5.4.2 Filtros de Busca Disponíveis

| Filtro | Tipo | Status |
|--------|------|--------|
| query | text | ✅ |
| required_skills | ARRAY | ✅ |
| preferred_skills | ARRAY | ✅ Schema |
| seniority_levels | ARRAY | ✅ Schema |
| min_years_experience | integer | ✅ Schema |
| max_years_experience | integer | ✅ Schema |
| locations | ARRAY | ✅ Schema |
| remote_only | boolean | ✅ Schema |
| min_salary | double | ✅ Schema |
| max_salary | double | ✅ Schema |
| statuses | ARRAY | ✅ Schema |
| sources | ARRAY | ✅ Schema |
| is_active | boolean | ✅ |
| tags | ARRAY | ✅ Schema |

### 5.4.3 Controle de Créditos (Planejado)

| Recurso | Custo | Limite Diário | Status |
|---------|-------|---------------|--------|
| Busca local | 0 créditos | Ilimitado | ✅ |
| Pearch AI | 2 créditos | 10 buscas/dia | 🔴 |
| Enriquecimento | 1 crédito | 50/dia | 🔴 |

**Dados Reais no Banco:** 31 buscas realizadas, todas locais (0 Pearch)

---

## 5.5 Módulo 5: Triagem por Voz (WSI - Voice Screening)

**Status Geral:** 🔴 Não implementado (schema existe)

### 5.5.1 Metodologia WSI (Planejada)

O **WSI (Wedo Screening Interview)** é uma metodologia proprietária de triagem que combina:

1. **Entrevista por voz automatizada** - Ligação com IA conversacional
2. **Speech-to-Text** - Transcrição em tempo real
3. **Análise comportamental** - Big Five, red flags, padrões de fala
4. **Scoring preditivo** - Probabilidade de sucesso na vaga

### 5.5.2 Tabelas WSI no Banco (Vazias)

| Tabela | Colunas | Registros | Status |
|--------|---------|-----------|--------|
| voice_screening_calls | 28 | 0 | ✅ Schema |
| voice_screening_analyses | 37 | 0 | ✅ Schema |
| wsi_sessions | 10 | 0 | ✅ Schema |
| wsi_questions | 11 | 0 | ✅ Schema |
| wsi_results | 10 | 0 | ✅ Schema |
| wsi_reports | 9 | 0 | ✅ Schema |
| wsi_feedbacks | 13 | 0 | ✅ Schema |
| wsi_response_analyses | 18 | 0 | ✅ Schema |
| wsi_scores_overview | 12 | 0 | ✅ Schema |
| wsi_red_flags_summary | 7 | 0 | ✅ Schema |

### 5.5.3 Integrações de Voz (Planejadas)

| Serviço | Função | Status |
|---------|--------|--------|
| OpenMic.ai | Plataforma de chamadas | 🔴 |
| Deepgram | Speech-to-Text | 🔴 |
| Google TTS | Text-to-Speech | 🔴 |
| Claude Sonnet | Análise profunda | 🔴 |

---

## 5.6 Módulo 6: Agendamento de Entrevistas

**Status Geral:** 🔴 Não implementado (schema existe)

### 5.6.1 Funcionalidades (Planejadas)

| Feature | Descrição | Status |
|---------|-----------|--------|
| Microsoft Graph | Integração calendário | 🔴 |
| Disponibilidade | Verificação automática | 🔴 |
| Criação de eventos | Google Meet / Teams | 🔴 |
| Lembretes | Email + WhatsApp | 🔴 |

### 5.6.2 Tabelas no Banco (Vazias)

| Tabela | Colunas | Registros |
|--------|---------|-----------|
| interviews | 44 | 0 |
| interview_feedbacks | 16 | 0 |
| calendar_availability | 12 | 0 |

---

## 5.7 Módulo 7: Comunicação Omnichannel

**Status Geral:** 🔴 Não implementado

### 5.7.1 Canais (Planejados)

| Canal | Status | Integração |
|-------|--------|------------|
| Email | 🔴 | SMTP/SendGrid |
| WhatsApp | 🔴 | Twilio |
| Teams | 🔴 | Microsoft Graph |
| SMS | 🔴 | Twilio |
| In-app | 🟡 Chat existe | Interno |

### 5.7.2 Tabelas no Banco

| Tabela | Colunas | Registros | Status |
|--------|---------|-----------|--------|
| conversations | 13 | 63 | ✅ |
| messages | 6 | 126 | ✅ |
| teams_conversations | 14 | 0 | ✅ Schema |
| teams_messages | 10 | 0 | ✅ Schema |
| teams_notifications | 15 | 0 | ✅ Schema |
| activity_feed | 21 | 32 | ✅ |

---

## 5.8 Módulo 8: Dashboards e Analytics

**Status Geral:** 🟡 Visual existe (dados mock)

### 5.8.1 Categorias de Indicadores (Planejadas)

| Categoria | Métricas | Status |
|-----------|----------|--------|
| **Funil** | Candidatos por etapa, conversão | 🟡 Mock |
| **Tempo** | Time-to-fill, tempo por etapa | 🔴 |
| **Qualidade** | LIA Score médio, turnover | 🔴 |
| **Produtividade** | Candidatos/recrutador | 🔴 |
| **Custo** | Cost-per-hire, ROI | 🔴 |
| **Diversidade** | D&I metrics, PCD | 🔴 |
| **Previsão** | Pipeline forecast | 🔴 |

---

# 6. Arquitetura Multi-Agent

**Status Geral:** 🔴 Não implementado (documentado apenas)

## 6.1 Decisão Arquitetural

**Escolha:** Multi-Agent > Super-Agent

**Justificativa:**
- Especialização: Cada agente domina seu contexto
- Observabilidade: Trace individual por agente
- Extensibilidade: Adicionar agentes sem refatorar
- Manutenção: Debug isolado

## 6.2 Agentes Especializados (6) - PLANEJADOS

| Agente | Responsabilidade | Status |
|--------|------------------|--------|
| Job Intake Agent | Criação e gestão de vagas | 🔴 |
| Sourcing Agent | Busca e enriquecimento | 🟡 Básico |
| Screening Agent | Triagem automatizada (WSI) | 🔴 |
| Evaluation Agent | Scoring e avaliação | 🔴 |
| Scheduling Agent | Agendamento de entrevistas | 🔴 |
| Communication Agent | Omnichannel | 🔴 |

## 6.3 Componentes do Orquestrador - PLANEJADOS

| Componente | Descrição | Status |
|------------|-----------|--------|
| Intent Router | Classificação de intenção | 🟡 if/else básico |
| Task Planner | Decomposição de tarefas | 🔴 |
| Policy Engine | Regras de negócio | 🔴 |
| State Manager | Gerenciamento de estado | 🟡 In-memory |

---

# 7. Modelo de Dados

## 7.1 Resumo das Tabelas

| Domínio | Tabelas | Com Dados | Status |
|---------|---------|-----------|--------|
| Core | 6 | 4 | 🟡 |
| Chat | 5 | 4 | ✅ |
| ATS | 11 | 1 | 🟡 Schema |
| WSI | 10 | 0 | 🟡 Schema |
| Calendar | 4 | 0 | 🟡 Schema |
| Templates | 2 | 0 | 🟡 Schema |

## 7.2 Estatísticas Reais

```
Total de tabelas:     37
Total de colunas:     617
Tabelas com dados:    6 (16%)
Tabelas vazias:       31 (84%)
Total de registros:   261

Registros por área:
- Chat/Conversas:     221 (85%)
- Buscas:             31 (12%)
- Candidatos:         3 (1%)
- ATS Systems:        6 (2%)
```

## 7.3 Sistemas ATS Configurados

| ATS | Região | Status |
|-----|--------|--------|
| Greenhouse | Global | ✅ Cadastrado |
| Lever | Global | ✅ Cadastrado |
| Workable | Global | ✅ Cadastrado |
| Gupy | Brasil | ✅ Cadastrado |
| Pandapé | LATAM | ✅ Cadastrado |
| BambooHR | Global | ✅ Cadastrado |

**Nota:** Os sistemas estão cadastrados na tabela `ats_systems`, mas nenhuma integração real está funcionando.

---

# 8. Integrações

## 8.1 Status das Integrações

> **✅ ATUALIZADO (Dezembro 2025):** Várias integrações estão funcionais com clientes HTTP reais e auto-inicialização a partir de variáveis de ambiente.

### IA/LLM
| Serviço | Uso | Status Real |
|---------|-----|-------------|
| Anthropic Claude | Orquestrador + Agentes | ✅ Funcional (Sonnet 4) |
| Google Gemini | Voice service, fallback | ✅ Integração configurada |
| OpenAI GPT-4 | Fallback LLM | 🟡 Configurado |
| Deepgram | Speech-to-Text (Nova-2) | ✅ $0.0043/min |

### Comunicação
| Serviço | Canal | Status Real |
|---------|-------|-------------|
| Microsoft Graph | Calendar, Teams | 🟡 Secrets configurados |
| Twilio | WhatsApp, SMS | 🔴 Não configurado |
| SendGrid | Email | 🔴 Não configurado |
| OpenMic.ai | Chamadas automatizadas | 🟡 API integrada (dry_run mode) |

### Busca
| Serviço | Uso | Status Real |
|---------|-----|-------------|
| Pearch AI | Two-tier search (190M+ perfis) | ✅ Funcional |
| LinkedIn | Enriquecimento | 🔴 Não configurado |

### ATS (Bidirecionais - Push + Pull)
| Sistema | Mercado | Status Real | Implementação |
|---------|---------|-------------|---------------|
| **Gupy** | Brasil | ✅ Código implementado | Real HTTP client (httpx), sync_candidate, push_to_ats |
| **Pandapé** | LATAM | ✅ Código implementado | Real HTTP client (httpx), full CRUD |
| **StackOne** | Global (40+ ATSs) | ✅ Código implementado | Unified API client, 40+ conectores |
| Solides | Brasil | 🔴 Não integrado |
| Greenhouse | USA/Global | 🔴 Apenas schema |
| Lever | USA/Global | 🔴 Apenas schema |

**Características das Integrações ATS:**
- Real HTTP clients implementados com `httpx` async
- Auto-inicialização a partir de env vars (`GUPY_API_KEY`, `PANDAPE_API_KEY`, `STACKONE_API_KEY`)
- Mock fallback quando API key não configurada (permite dev/test sem credenciais)
- Retry logic com exponential backoff
- Logging de sync status
- **Nota:** Clientes funcionais em ambiente de desenvolvimento; requer credenciais reais para produção

### Comunicação (Prioridade WhatsApp-First)
| Canal | Serviço | Status Real |
|-------|---------|-------------|
| WhatsApp | Deepgram (transcrição áudio) | ✅ Funcional |
| Teams | Microsoft Graph | 🟡 Configurado |
| SMS | Twilio | 🔴 Não configurado |
| Email | SendGrid | 🔴 Não configurado |

### Voice Screening
| Serviço | Uso | Status Real | Custo |
|---------|-----|-------------|-------|
| **Deepgram** | Transcrição WhatsApp | ✅ Nova-2 | $0.0043/min (12k min/ano free) |
| **OpenMic.ai** | Chamadas automatizadas | 🟡 API integrada | $0.08-0.15/min |

### Compliance e Analytics
| Categoria | Item | Status |
|-----------|------|--------|
| LGPD | Portal do Titular, Consent Management, Data Subject Requests | ✅ Implementado |
| Multi-tenancy | company_id isolation | ✅ Implementado |
| Audit Trail | SOX-Compliant, 7-year retention | ✅ Implementado |
| SOC 2 | Type II controls, Trust Center | ✅ Implementado |
| SOX | SoD Matrix, Risk Register | ✅ Implementado |
| BCB 498 | Cyber Insurance, Business Continuity | ✅ Implementado |
| EU AI Act | Bias Audits, Transparency | ✅ Implementado |
| NYC LL144 | Automated Employment Decision Tools | ✅ Implementado |
| ISO 27001 | 96 controls | ✅ Implementado |
| Health Check | 242 items, 7 frameworks | ✅ Implementado |
| Analytics | LangSmith | ✅ Tracing ativo |

### Secrets Configurados e Utilizados
| Secret | Status | Uso |
|--------|--------|-----|
| `ANTHROPIC_API_KEY` | ✅ Ativo | LLM principal |
| `GEMINI_API_KEY` | ✅ Ativo | Voice + fallback |
| `DEEPGRAM_API_KEY` | ✅ Ativo | STT WhatsApp |
| `PEARCH_API_KEY` | ✅ Ativo | Candidate search |
| `LANGSMITH_API_KEY` | ✅ Ativo | Tracing |
| `OPENMIC_API_KEY` | 🟡 Configurado | Voice calls (dry_run) |
| `AZURE_CLIENT_ID/SECRET` | 🟡 Configurado | MS Graph |

---

# 9. Requisitos Técnicos

## 9.1 Stack Atual

### Frontend
| Tecnologia | Versão | Status |
|------------|--------|--------|
| Next.js | 15.5.6 | ✅ |
| React | 19 | ✅ |
| TypeScript | 5.x | ✅ |
| Tailwind CSS | 3.x | ✅ |
| shadcn/ui | latest | 🟡 Parcial |
| Chart.js | 4.x | ✅ |

### Backend
| Tecnologia | Versão | Status |
|------------|--------|--------|
| FastAPI | 0.115.x | ✅ |
| Python | 3.11 | ✅ |
| LangGraph | latest | 🟡 Básico |
| Pydantic | 2.x | ✅ |
| SQLAlchemy | 2.x | ✅ |

### Database
| Tecnologia | Versão | Status |
|------------|--------|--------|
| PostgreSQL | 15 | ✅ |
| Redis | 7.x | 🔴 Não configurado |

### Observabilidade
| Ferramenta | Status |
|------------|--------|
| LangSmith | 🟡 Parcial |
| Sentry | 🔴 |
| Prometheus | 🔴 |
| Grafana | 🔴 |

## 9.2 Endpoints Backend - Status Real

> **✅ ATUALIZADO (Dezembro 2025):** O backend possui **55+ routers funcionais** com **200+ endpoints** cobrindo todas as funcionalidades do sistema.

### Routers Registrados no FastAPI (38 total)

#### Core & Chat
| Router | Prefixo | Status |
|--------|---------|--------|
| health | `/health` | ✅ |
| chat | `/api/v1/chat` | ✅ LLM real (Claude) |
| auth | `/api/v1/auth` | ✅ JWT |
| candidates | `/api/v1/candidates` | ✅ Full CRUD |
| job_vacancies | `/api/v1/job-vacancies` | ✅ |

#### Agentes & Orquestração
| Router | Prefixo | Status |
|--------|---------|--------|
| orchestrator | `/api/orchestrator` | ✅ Multi-agent |
| wsi_endpoints | `/api/wsi` | ✅ |
| agent_monitoring | `/api/v1/agent-monitoring` | ✅ |

#### ATS & Integrações
| Router | Prefixo | Status |
|--------|---------|--------|
| ats | `/api/v1/ats` | ✅ Gupy, Pandapé, StackOne |
| applications | `/api/v1/applications` | ✅ |
| recruitment_stages | `/api/v1/recruitment-stages` | ✅ |
| pipeline | `/api/v1/pipeline` | ✅ |
| sourcing_pipeline | `/api/v1/sourcing-pipeline` | ✅ |

#### Voice & Screening
| Router | Prefixo | Status |
|--------|---------|--------|
| voice | `/api/v1/voice` | ✅ Gemini |
| openmic | `/api/v1/openmic` | ✅ |
| voice_screening_test | `/api/v1/voice-test` | ✅ Deepgram |

#### Busca & Análise
| Router | Prefixo | Status |
|--------|---------|--------|
| candidate_search | `/api/v1/search` | ✅ Two-tier |
| calibration | `/api/v1/calibration` | ✅ |
| predictive_analytics | `/api/v1/predictive` | ✅ |
| cv_parser | `/api/v1/cv` | ✅ |

#### Comunicação & Workflow
| Router | Prefixo | Status |
|--------|---------|--------|
| teams | `/api/v1/teams` | 🟡 Schema |
| calendar | `/api/v1/calendar` | ✅ |
| email_templates | `/api/v1/email-templates` | ✅ |
| notifications | `/api/v1/notifications` | ✅ |
| automation | `/api/v1/automation` | ✅ |
| bulk_actions | `/api/v1/bulk` | ✅ |

#### Gestão & Admin
| Router | Prefixo | Status |
|--------|---------|--------|
| admin | `/api/v1/admin` | ✅ |
| company | `/api/v1/company` | ✅ |
| workforce | `/api/v1/workforce` | ✅ |
| briefing | `/api/v1/briefing` | ✅ |
| credits | `/api/v1/credits` | ✅ |
| interviews | `/api/v1/interviews` | ✅ |

#### Tasks & Atividades
| Router | Prefixo | Status |
|--------|---------|--------|
| tasks | `/api/v1/tasks` | ✅ |
| task_lifecycle | `/api/v1/task-lifecycle` | ✅ |
| activities | `/api/v1/activities` | ✅ |
| test_activities | `/api/v1/test-activities` | ✅ |
| alerts | `/api/v1/alerts` | ✅ |
| reports | `/api/v1/reports` | ✅ |

### Resumo de Implementação

**Total de routers:** 55+  
**Total de endpoints:** 200+  
**Funcionais (✅):** 50+ (92%)  
**Parciais (🟡):** 5 (8%)  
**Não implementados (🔴):** 0

### Novos Routers de Compliance (Dezembro 2025)

| Router | Prefixo | Endpoints | Status |
|--------|---------|-----------|--------|
| data_subject_requests | `/api/v1/data-subject-requests` | 10 | ✅ LGPD Art. 18 |
| consent | `/api/v1/consent` | 9 | ✅ Consent Management |
| insurance | `/api/v1/insurance` | 19 | ✅ BCB 498/2025 |
| risks | `/api/v1/risks` | 8 | ✅ Risk Register |
| sod | `/api/v1/sod` | 10 | ✅ SoD Matrix |
| continuity | `/api/v1/continuity` | 12 | ✅ BIA/DR |
| health_check | `/api/v1/health-check` | 5 | ✅ Compliance Health |
| controls | `/api/v1/controls` | 8 | ✅ Control Library |
| bias_audit | `/api/v1/bias-audit` | 6 | ✅ AI Fairness |
| trust_center | `/api/v1/trust-center` | 4 | ✅ Public Trust Center |

---

# 10. Métricas de Sucesso

## 10.1 KPIs de Produto (Metas Futuras)

| Métrica | Baseline | Meta 6m | Meta 12m |
|---------|----------|---------|----------|
| Time-to-Fill | 45 dias | 30 dias | 20 dias |
| Cost-per-Hire | R$ 5.000 | R$ 3.500 | R$ 2.500 |
| Candidatos/Recrutador | 50/mês | 100/mês | 150/mês |
| NPS Candidato | 20 | 40 | 60 |

## 10.2 KPIs Técnicos (SLAs Planejados)

| Métrica | SLA |
|---------|-----|
| Uptime | 99.9% |
| Latência API (p95) | < 500ms |
| Latência LLM (p95) | < 3s |
| Error Rate | < 0.1% |

---

# 11. Roadmap

## 11.1 Estado Atual (Dezembro 2025)

- ✅ Frontend completo com WeDo Admin (3 pilares)
- ✅ Backend com 55+ routers e 200+ endpoints
- ✅ PostgreSQL com 80+ tabelas
- ✅ Chat LIA com Claude 3.5 Sonnet
- ✅ Multi-agent orchestrator com LangGraph
- ✅ Integrações ATS funcionais (Gupy, Pandapé, StackOne)
- ✅ Compliance completo (7 frameworks, 242 health checks)
- 🟡 Testes automatizados em expansão (~15% cobertura)

## 11.2 Fases Completadas

### Fase 1: Core ✅ (Concluída)
- [x] CRUD candidatos completo
- [x] CRUD vagas completo
- [x] Busca avançada two-tier
- [x] Autenticação JWT

### Fase 2: Integrações ✅ (Concluída)
- [x] Pearch AI (800M+ perfis)
- [x] ATS bidirecionais
- [x] AI-powered filters

### Fase 3: IA ✅ (Concluída)
- [x] Orquestrador multi-agent
- [x] Voice screening Deepgram
- [x] LIA Score funcional

### Fase 4: Compliance ✅ (Concluída - Dezembro 2025)
- [x] Health Check 242 itens
- [x] LGPD Portal do Titular
- [x] BCB 498/2025 Cyber Insurance
- [x] SOX SoD Matrix
- [x] Trust Center público

## 11.3 Próximas Fases

### Fase 5: Enterprise (Q1 2026)
- [ ] WhatsApp Business API
- [ ] WSI Full Interview
- [ ] Microsoft Graph Calendar
- [ ] Expansão de testes (50% cobertura)

---

# 12. Riscos e Mitigações

## 12.1 Riscos Críticos

| Risco | Probabilidade | Impacto | Mitigação | Status |
|-------|---------------|---------|-----------|--------|
| Custo de APIs LLM | Média | Alto | Rate limiting, cache | ✅ Implementado |
| Integrações ATS instáveis | Média | Médio | Circuit breakers, fallbacks | ✅ Implementado |
| Compliance regulatório | Baixa | Alto | Health Check 242 itens, 7 frameworks | ✅ Implementado |
| Vazamento de dados | Baixa | Crítico | Criptografia, LGPD compliance | ✅ Implementado |

## 12.2 Segurança - Status Atual

| Camada | Status | Implementação |
|--------|--------|---------------|
| **Autenticação** | ✅ Implementado | JWT tokens, refresh tokens |
| **Autorização** | ✅ Implementado | RBAC com roles e permissões |
| **Multi-tenancy** | ✅ Implementado | company_id isolation em todas tabelas |
| **Rate Limiting** | ✅ Implementado | Por usuário/empresa |
| **CORS** | ✅ Implementado | Configurado e validado |
| **Input Validation** | ✅ Implementado | Pydantic v2 strict mode |
| **SQL Injection** | ✅ Protegido | SQLAlchemy ORM |
| **Audit Trail** | ✅ Implementado | SOX-compliant, 7 anos retenção |
| **LGPD** | ✅ Implementado | Portal do Titular, Consent Management |

## 12.3 Dívida Técnica Restante

| Item | Severidade | Descrição | Prioridade |
|------|------------|-----------|------------|
| Testes automatizados | Média | Cobertura atual ~15% | P1 |
| Documentação API | Baixa | OpenAPI parcial | P2 |
| Performance optimization | Baixa | Queries N+1 em alguns endpoints | P2 |

---

# 13. Estado Atual vs Planejado

## 13.1 Resumo Atualizado (Dezembro 2025)

| Área | Planejado | Implementado | % Real |
|------|-----------|--------------|--------|
| Frontend | 100+ componentes | WeDo Admin + Chat + Dashboard + Busca | 65% |
| Backend | 200+ endpoints | 55+ routers, 200+ endpoints | 60% |
| IA/Agentes | 11 agentes | 1 Orchestrator + 10 especializados | 50% |
| Compliance | 7 frameworks | Health Check 242 itens, LGPD, BCB, SOX | 70% |
| Integrações | 8 sistemas | 3 ATS + Pearch + AI filters | 40% |
| Testes | Cobertura 80% | Multi-tenancy + compliance tests | 20% |
| **TOTAL** | **100%** | **~55%** | **55%** |

## 13.2 O Que Funciona

### Frontend
1. ✅ WeDo Talent Admin com arquitetura 3 pilares (Overview, Operations, Compliance)
2. ✅ Chat LIA com side panels dinâmicos
3. ✅ Dashboard com KPIs reais e métricas SaaS
4. ✅ Funil de talentos com pipeline visual
5. ✅ Gestão de candidatos com CV parser
6. ✅ Busca avançada two-tier (local + Pearch)
7. ✅ Filtros com IA: "Ask AI" (autocomplete) + "Find Similar" (sugestões)
8. ✅ Compliance Health Check (242 itens, 7 frameworks)
9. ✅ Trust Center público

### Backend
1. ✅ 55+ routers funcionais (200+ endpoints)
2. ✅ Multi-agent orchestrator com LangGraph
3. ✅ 11 agentes especializados ativos
4. ✅ Integrações ATS bidirecionais (Gupy, Pandapé, StackOne)
5. ✅ Voice screening com Deepgram
6. ✅ Multi-tenancy com company_id isolation
7. ✅ 80+ tabelas no banco de dados

### Compliance & Governance
1. ✅ LGPD Portal do Titular (7 tipos de requisição, SLA 15 dias)
2. ✅ Consent Management com versionamento e hash SHA256
3. ✅ BCB 498/2025 Cyber Insurance (19 endpoints)
4. ✅ Risk Register com matriz 5x5
5. ✅ SoD Matrix para SOX 404
6. ✅ Business Continuity (BIA, DR Plans, Testing)
7. ✅ Bias Audit System (11 categorias)
8. ✅ Control Library (177 controles pré-cadastrados)
9. ✅ Audit Trail SOX-compliant (retenção 7 anos)

### IA & Integrações
1. ✅ Claude 3.5 Sonnet como LLM principal
2. ✅ Pearch AI two-tier search (800M+ perfis)
3. ✅ Deepgram STT ($0.0043/min)
4. ✅ LangSmith tracing ativo
5. ✅ Universal WSI scoring
6. ✅ AI-powered filter suggestions

## 13.3 Em Progresso

1. 🟡 WSI Full Interview Mode
2. 🟡 OpenMic.ai chamadas automatizadas
3. 🟡 Microsoft Graph Calendar
4. 🟡 WhatsApp Business API
5. 🟡 Expansão de testes automatizados

## 13.4 Próximas Prioridades

1. 📋 WhatsApp integração completa
2. 📋 WSI Full Interview com análise Big Five
3. 📋 Expansão de testes (meta: 50% cobertura)
4. 📋 Onboarding interativo
5. 📋 Analytics preditivo avançado

---

# 14. Estratégia de Migração

## 14.1 Contexto e Situação Atual

### Ambientes Existentes

| Ambiente | Stack | Status | Propósito |
|----------|-------|--------|-----------|
| **Produção** | Ruby on Rails + Vue/Nuxt | Funcional | Sistema completo ATS |
| **Replit** | Next.js + React + FastAPI/LangGraph | Protótipo | Design system + Agentes LIA |

### Decisões Estratégicas Confirmadas

- ✅ **Preservar backend Rails** - Core de negócio, auth, billing, integrações ATS
- ✅ **Preservar frontend Vue/Nuxt** - Time já domina, produção estável
- ✅ **Aproveitar Replit** - Design tokens, especificações, agentes LIA
- ✅ **FastAPI como microserviço** - Isolar agentes AI do monólito Rails

## 14.2 Estratégia Híbrida (Recomendada)

```
┌─────────────────────────────────────────────────────────────────┐
│                    ESTRATÉGIA HÍBRIDA                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   REPLIT (Fábrica de Protótipos)                                │
│   ┌─────────────────────────────────┐                           │
│   │ • Prototipagem rápida React     │                           │
│   │ • Geração de design tokens      │                           │
│   │ • Especificações de componentes │                           │
│   │ • Validação de fluxos UX        │                           │
│   │ • Desenvolvimento agentes LIA   │                           │
│   └────────────────┬────────────────┘                           │
│                    │                                             │
│                    ▼ (exporta)                                   │
│                                                                  │
│   ARTEFATOS TRANSFERÍVEIS                                       │
│   ┌─────────────────────────────────┐                           │
│   │ • Design tokens (JSON/CSS)      │                           │
│   │ • Specs componentes (MDX)       │                           │
│   │ • Storyboards (vídeos/imagens)  │                           │
│   │ • Contratos API (OpenAPI)       │                           │
│   │ • Agentes LIA (FastAPI bundle)  │                           │
│   └────────────────┬────────────────┘                           │
│                    │                                             │
│                    ▼ (implementa)                                │
│                                                                  │
│   PRODUÇÃO (Rails + Vue + FastAPI)                              │
│   ┌─────────────────────────────────┐                           │
│   │ Rails: Auth, ATS core, billing  │                           │
│   │ Vue: UI com shadcn-vue/Tailwind │                           │
│   │ FastAPI: Microserviço AI agents │                           │
│   └─────────────────────────────────┘                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 14.3 O Que Aproveitar do Replit

### Alta Prioridade (Transferir Imediatamente)

| Artefato | Formato | Uso em Produção |
|----------|---------|-----------------|
| **Design tokens** | JSON/CSS variables | Tailwind config Vue |
| **Paleta de cores** | HEX/HSL | Theme shadcn-vue |
| **Tipografia** | Font families + sizes | CSS globals |
| **Espaçamentos** | Spacing scale | Tailwind config |
| **Componentes spec** | Screenshots + behavior | Guia implementação Vue |

### Média Prioridade (Adaptar)

| Artefato | Adaptação Necessária |
|----------|---------------------|
| **Layouts de página** | Estrutura → Vue components |
| **Fluxos de tela** | Lógica → Vue router + stores |
| **Componentes React** | Comportamento → Vue composables |
| **APIs mock** | Contratos → Rails endpoints |

### Alta Prioridade (Migrar Direto)

| Artefato | Formato | Ação |
|----------|---------|------|
| **Agentes LangGraph** | Python | Deploy como microserviço |
| **Prompts otimizados** | Texto | Transferir para produção |
| **Lógica de orquestração** | Python | Manter em FastAPI |
| **Contratos de API** | OpenAPI | Documentar para Rails |

## 14.4 O Que NÃO Migrar

| Item | Razão |
|------|-------|
| Código React/TypeScript | Vue é o target, conversão manual muito custosa |
| Next.js SSR logic | Nuxt já resolve SSR no Vue |
| Estado Zustand | Pinia já existe no Vue |
| Hooks React | Composables Vue são diferentes |
| Componentes shadcn/ui | Usar shadcn-vue (compatível) |

## 14.5 Integração Backend: Rails ↔ FastAPI

### Arquitetura de Integração

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│   FRONTEND VUE/NUXT                                             │
│   ┌─────────────────────────────────────────────────────┐       │
│   │  Chat LIA │ Funil │ Dashboard │ Vagas │ Candidatos  │       │
│   └────────────────────────┬────────────────────────────┘       │
│                            │                                     │
│                            ▼                                     │
│   ┌────────────────────────────────────────────────────┐        │
│   │              API GATEWAY (Rails)                    │        │
│   │  • Auth/Session                                     │        │
│   │  • Rate limiting                                    │        │
│   │  • Request routing                                  │        │
│   └────────────────────────┬───────────────────────────┘        │
│                            │                                     │
│            ┌───────────────┴───────────────┐                    │
│            ▼                               ▼                    │
│   ┌─────────────────┐             ┌─────────────────┐           │
│   │  RAILS CORE     │             │  FASTAPI LIA    │           │
│   │                 │   JWT +     │                 │           │
│   │  • ATS/CRUD     │◄───────────►│  • Agentes      │           │
│   │  • Billing      │   Redis     │  • LangGraph    │           │
│   │  • Integrações  │             │  • Claude API   │           │
│   │  • Users/Orgs   │             │  • Pearch       │           │
│   └─────────────────┘             └─────────────────┘           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Mecanismos de Integração

| Mecanismo | Uso | Implementação |
|-----------|-----|---------------|
| **JWT assinado** | Auth entre Rails ↔ FastAPI | Rails gera, FastAPI valida |
| **Redis/Sidekiq** | Jobs assíncronos longos | Screening, análises |
| **Webhooks** | Notificações de eventos | FastAPI → Rails |
| **HTTP sync** | Requests instantâneos | Chat, busca rápida |

### Endpoints de Integração

```yaml
# FastAPI endpoints consumidos pelo Rails
POST /api/v1/chat/message          # Mensagem para LIA
POST /api/v1/jobs/extract          # Extração de JD
POST /api/v1/candidates/search     # Busca two-tier
POST /api/v1/screening/analyze     # Análise pós-screening
GET  /api/v1/conversation/{id}     # Histórico conversa

# Rails endpoints consumidos pelo FastAPI
GET  /api/v1/candidates/{id}       # Dados candidato
GET  /api/v1/jobs/{id}             # Dados vaga
POST /api/v1/candidates            # Criar candidato
POST /api/v1/interviews/schedule   # Agendar entrevista
```

## 14.6 Plano de Execução em 3 Ondas

### Onda 1: Fundação (2-3 semanas)

| Tarefa | Responsável | Entrega |
|--------|-------------|---------|
| Extrair design tokens do Replit | Design/Frontend | JSON + CSS vars |
| Documentar componentes prioritários | Design | Specs MDX |
| Setup shadcn-vue no projeto Vue | Frontend | Biblioteca base |
| Definir contrato Rails ↔ FastAPI | Backend | OpenAPI spec |
| Setup ambiente FastAPI produção | DevOps | Docker + deploy |

### Onda 2: Migração Frontend (4-6 semanas)

| Módulo | Prioridade | Complexidade |
|--------|------------|--------------|
| **Chat LIA** | P0 | Alta |
| **Funil de Talentos** | P0 | Alta |
| **Dashboard KPIs** | P1 | Média |
| **Gestão de Vagas** | P1 | Média |
| **Perfil Candidato** | P2 | Baixa |

### Onda 3: Integração Agentes (4-6 semanas)

| Agente | Integração Rails | Dependências |
|--------|-----------------|--------------|
| **Job Intake** | Webhook → criar vaga | Modelo Job |
| **Sourcing** | API → buscar candidatos | Pearch, DB |
| **Scheduling** | Callback → criar evento | Google Calendar |
| **Communication** | Queue → enviar mensagem | WhatsApp API |

## 14.7 Uso Contínuo do Replit

### Workflow de Prototipagem

```
1. DESIGN
   Designer cria conceito → Figma
   
2. PROTOTIPAGEM REPLIT
   Dev protótipa em React → Replit
   Valida interações, estados, fluxos
   
3. DOCUMENTAÇÃO
   Exporta tokens → JSON/CSS
   Grava comportamentos → Vídeo/GIF
   Escreve specs → MDX
   
4. IMPLEMENTAÇÃO VUE
   Time Vue implementa → Produção
   Usa specs como referência
   
5. VALIDAÇÃO
   Compara Replit vs Produção
   Ajusta se necessário
```

### Ferramentas de Sincronização

| Ferramenta | Função |
|------------|--------|
| **Style Dictionary** | Exportar tokens JSON → CSS/Tailwind |
| **Storybook** | Documentar componentes |
| **Chromatic** | Visual regression testing |
| **Figma Tokens** | Sync design ↔ código |

## 14.8 Métricas de Sucesso da Migração

| Métrica | Target | Como Medir |
|---------|--------|------------|
| **Tempo prototipagem** | -50% | Dias para validar conceito |
| **Fidelidade visual** | 95% | Comparação pixel Replit vs Prod |
| **Reuso de specs** | 80% | Specs usadas sem retrabalho |
| **Velocidade frontend** | +40% | Story points/sprint |
| **Bugs de integração** | <5% | Tickets pós-deploy |

## 14.9 Cronograma Consolidado

```
Semana 1-2:  Onda 1 - Setup tokens, specs, contratos
Semana 3-4:  Onda 1 - Ambiente FastAPI, shadcn-vue
Semana 5-6:  Onda 2 - Chat LIA + Funil (frontend Vue)
Semana 7-8:  Onda 2 - Dashboard + Vagas (frontend Vue)
Semana 9-10: Onda 3 - Job Intake + Sourcing agents
Semana 11-12: Onda 3 - Scheduling + Communication agents
Semana 13+:  Refinamentos, testes, otimizações
```

**Timeline total: 12-14 semanas para MVP completo integrado**

## 14.10 Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Tokens incompatíveis | Média | Baixo | Validar em POC antes |
| Latência Rails↔FastAPI | Baixa | Alto | Cache Redis, async |
| Comportamentos diferentes Vue vs React | Alta | Médio | Specs detalhadas, testes |
| Scope creep na migração | Alta | Alto | Priorização rigorosa P0/P1/P2 |
| Dependências externas (Pearch, OpenMic) | Média | Alto | Fallbacks, mocks |

## 14.11 Design Tokens Exportáveis

### Formato de Exportação (Style Dictionary)

Os design tokens do Replit devem ser exportados em formato JSON para uso com Style Dictionary, permitindo geração automática para múltiplas plataformas.

```json
{
  "color": {
    "brand": {
      "primary": { "value": "#C74446", "type": "color", "description": "Vermelho coral LIA" },
      "primary-hover": { "value": "#B23B3D", "type": "color" },
      "primary-light": { "value": "#FEF2F2", "type": "color" }
    },
    "wedo": {
      "cyan": { "value": "#60BED1", "type": "color", "description": "Automação LIA" },
      "green": { "value": "#60D186", "type": "color", "description": "Sucesso, aprovação" },
      "orange": { "value": "#D19960", "type": "color", "description": "Tempo, custos" },
      "purple": { "value": "#9860D1", "type": "color", "description": "Insights premium" },
      "magenta": { "value": "#D160AB", "type": "color", "description": "Urgência crítica" }
    },
    "background": {
      "primary": { "value": "#FFFFFF", "type": "color" },
      "secondary": { "value": "#F9FAFB", "type": "color" },
      "tertiary": { "value": "#F3F4F6", "type": "color" }
    },
    "text": {
      "primary": { "value": "#111827", "type": "color" },
      "secondary": { "value": "#6B7280", "type": "color" },
      "tertiary": { "value": "#9CA3AF", "type": "color" }
    },
    "border": {
      "subtle": { "value": "#E5E7EB", "type": "color" },
      "default": { "value": "#D1D5DB", "type": "color" }
    }
  },
  "typography": {
    "fontFamily": {
      "inter": { "value": "'Inter', sans-serif", "type": "fontFamily" },
      "open-sans": { "value": "'Open Sans', sans-serif", "type": "fontFamily" },
      "source-serif": { "value": "'Source Serif 4', serif", "type": "fontFamily" }
    },
    "fontSize": {
      "display": { "value": "1.5rem", "type": "dimension" },
      "heading-1": { "value": "1.25rem", "type": "dimension" },
      "heading-2": { "value": "1.125rem", "type": "dimension" },
      "body": { "value": "0.75rem", "type": "dimension" },
      "caption": { "value": "0.6875rem", "type": "dimension" }
    }
  },
  "spacing": {
    "xs": { "value": "0.25rem", "type": "dimension" },
    "sm": { "value": "0.5rem", "type": "dimension" },
    "md": { "value": "1rem", "type": "dimension" },
    "lg": { "value": "1.5rem", "type": "dimension" },
    "xl": { "value": "2rem", "type": "dimension" }
  },
  "borderRadius": {
    "sm": { "value": "0.375rem", "type": "dimension" },
    "md": { "value": "0.5rem", "type": "dimension" },
    "lg": { "value": "0.75rem", "type": "dimension" }
  },
  "shadow": {
    "sm": { "value": "0 1px 2px 0 rgb(0 0 0 / 0.02)", "type": "shadow" },
    "default": { "value": "0 1px 3px 0 rgb(0 0 0 / 0.05)", "type": "shadow" },
    "md": { "value": "0 4px 6px -1px rgb(0 0 0 / 0.05)", "type": "shadow" },
    "lg": { "value": "0 10px 15px -3px rgb(0 0 0 / 0.05)", "type": "shadow" }
  }
}
```

### Conversão para Vue/Tailwind

```javascript
// tailwind.config.js (Vue)
module.exports = {
  theme: {
    extend: {
      colors: {
        'lia-brand': '#C74446',
        'wedo-cyan': '#60BED1',
        'wedo-green': '#60D186',
        'wedo-orange': '#D19960',
        'wedo-purple': '#9860D1',
        'wedo-magenta': '#D160AB',
      },
      fontFamily: {
        'inter': ['Inter', 'sans-serif'],
        'open-sans': ['Open Sans', 'sans-serif'],
        'source-serif': ['Source Serif 4', 'serif'],
      }
    }
  }
}
```

### Arquivos a Exportar do Replit

| Arquivo | Formato | Destino Vue |
|---------|---------|-------------|
| `design-tokens.css` | CSS Variables | `assets/css/tokens.css` |
| `design-tokens.json` | Style Dictionary | Build pipeline |
| `tailwind.config.ts` | Tailwind Config | `tailwind.config.js` |
| `globals.css` | CSS Utilities | Adaptar para Vue |

## 14.12 Contrato OpenAPI Rails ↔ FastAPI

### Especificação OpenAPI 3.0

```yaml
openapi: 3.0.3
info:
  title: WeDOTalent LIA Agent API
  version: 1.0.0
  description: API de integração entre Rails (core ATS) e FastAPI (agentes LIA)

servers:
  - url: https://lia-api.wedotalent.com/api/v1
    description: Produção
  - url: http://localhost:8000/api/v1
    description: Desenvolvimento

security:
  - BearerAuth: []

paths:
  /chat/message:
    post:
      summary: Enviar mensagem para LIA
      operationId: sendChatMessage
      tags: [Chat]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ChatMessageRequest'
      responses:
        '200':
          description: Resposta da LIA
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ChatMessageResponse'
        '401':
          $ref: '#/components/responses/Unauthorized'

  /jobs/extract:
    post:
      summary: Extrair estrutura de Job Description
      operationId: extractJobDescription
      tags: [Jobs]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/JobExtractionRequest'
      responses:
        '200':
          description: Vaga estruturada
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/JobExtractionResponse'

  /candidates/search:
    post:
      summary: Busca two-tier de candidatos
      operationId: searchCandidates
      tags: [Candidates]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CandidateSearchRequest'
      responses:
        '200':
          description: Candidatos encontrados
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CandidateSearchResponse'

  /screening/analyze:
    post:
      summary: Análise pós-screening por voz
      operationId: analyzeScreening
      tags: [Screening]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ScreeningAnalysisRequest'
      responses:
        '200':
          description: Análise completa
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ScreeningAnalysisResponse'

  /conversation/{conversationId}:
    get:
      summary: Obter histórico de conversa
      operationId: getConversation
      tags: [Chat]
      parameters:
        - name: conversationId
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Histórico da conversa
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ConversationHistory'

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: JWT assinado pelo Rails

  schemas:
    ChatMessageRequest:
      type: object
      required: [message, user_id, organization_id]
      properties:
        message:
          type: string
          example: "Preciso encontrar desenvolvedores Python com 5+ anos"
        user_id:
          type: string
          format: uuid
        organization_id:
          type: string
          format: uuid
        conversation_id:
          type: string
          format: uuid
        context:
          type: object
          properties:
            current_job_id:
              type: string
            selected_candidates:
              type: array
              items:
                type: string

    ChatMessageResponse:
      type: object
      properties:
        response:
          type: string
        intent:
          type: string
          enum: [job_intake, candidate_search, scheduling, screening, general]
        confidence:
          type: number
          format: float
        context_data:
          type: object
        suggested_actions:
          type: array
          items:
            $ref: '#/components/schemas/SuggestedAction'

    JobExtractionRequest:
      type: object
      required: [job_description]
      properties:
        job_description:
          type: string
        source:
          type: string
          enum: [text, pdf, url]

    JobExtractionResponse:
      type: object
      properties:
        title:
          type: string
        seniority:
          type: string
        skills:
          type: array
          items:
            type: string
        requirements:
          type: array
          items:
            type: string
        salary_range:
          type: object
        location:
          type: string
        work_model:
          type: string
          enum: [remote, hybrid, onsite]

    CandidateSearchRequest:
      type: object
      required: [query]
      properties:
        query:
          type: string
        job_id:
          type: string
        filters:
          type: object
          properties:
            seniority:
              type: array
              items:
                type: string
            skills:
              type: array
              items:
                type: string
            location:
              type: string
            salary_max:
              type: number
        limit:
          type: integer
          default: 20
        use_external:
          type: boolean
          default: true
          description: Se true, usa Pearch AI após busca local

    CandidateSearchResponse:
      type: object
      properties:
        candidates:
          type: array
          items:
            $ref: '#/components/schemas/CandidateMatch'
        total_found:
          type: integer
        source:
          type: string
          enum: [local, pearch, mixed]
        credits_used:
          type: integer

    CandidateMatch:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        title:
          type: string
        match_score:
          type: number
        skills_match:
          type: array
          items:
            type: string
        source:
          type: string

    ScreeningAnalysisRequest:
      type: object
      required: [screening_id]
      properties:
        screening_id:
          type: string
        transcript:
          type: string
        audio_url:
          type: string

    ScreeningAnalysisResponse:
      type: object
      properties:
        overall_score:
          type: number
        communication_score:
          type: number
        technical_score:
          type: number
        cultural_fit_score:
          type: number
        big_five:
          type: object
        recommendation:
          type: string
          enum: [advance, hold, reject]
        summary:
          type: string

    ConversationHistory:
      type: object
      properties:
        id:
          type: string
        messages:
          type: array
          items:
            type: object
            properties:
              role:
                type: string
                enum: [user, assistant]
              content:
                type: string
              timestamp:
                type: string
                format: date-time
        created_at:
          type: string
          format: date-time

    SuggestedAction:
      type: object
      properties:
        type:
          type: string
        label:
          type: string
        payload:
          type: object

  responses:
    Unauthorized:
      description: Token JWT inválido ou expirado
      content:
        application/json:
          schema:
            type: object
            properties:
              error:
                type: string
              code:
                type: string
```

### Autenticação JWT

```ruby
# Rails: Geração do JWT para FastAPI
class LiaTokenService
  def self.generate(user)
    payload = {
      user_id: user.id,
      organization_id: user.organization_id,
      exp: 1.hour.from_now.to_i,
      iat: Time.now.to_i
    }
    JWT.encode(payload, Rails.application.credentials.lia_jwt_secret, 'HS256')
  end
end
```

```python
# FastAPI: Validação do JWT
from jose import jwt, JWTError

def verify_rails_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, 
            settings.RAILS_JWT_SECRET, 
            algorithms=["HS256"]
        )
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

---

# 15. Arquitetura Multi-Agentes Detalhada

## 15.1 Visão Geral do Sistema Multi-Agente

> **✅ ATUALIZADO (Dezembro 2025):** A plataforma LIA implementa **11 agentes especializados** (1 Orchestrator + 10 especializados) operando com LangGraph.

A plataforma LIA utiliza uma arquitetura de **11 agentes especializados** que trabalham de forma autônoma e colaborativa, orquestrados por um **Orchestrator Agent** central. Cada agente é especialista em um domínio específico do recrutamento.

### Inventário de Agentes (11 total)

| # | Agente | Tipo | Status |
|---|--------|------|--------|
| 1 | **Orchestrator Agent** | Orquestrador | ✅ Funcional |
| 2 | **Job Planner Agent** | Especializado | ✅ Funcional |
| 3 | **Sourcing Agent** | Especializado | ✅ Funcional |
| 4 | **CV Screening Agent** | Especializado | ✅ Funcional |
| 5 | **Entrevistador Agent** | Especializado | ✅ Funcional |
| 6 | **WSI Evaluator Agent** | Especializado | 🟡 Em desenvolvimento |
| 7 | **Scheduler Agent** | Especializado | ✅ Funcional |
| 8 | **Analytics/Feedback Agent** | Especializado | ✅ Funcional |
| 9 | **ATS Integration Agent** | Especializado | ✅ Funcional |
| 10 | **Recruiter Assistant Agent** | Especializado | ✅ 6 handlers conversacionais |
| 11 | **Communication Agent** | Especializado | ✅ Approval workflows |

### Princípios Arquiteturais

| Princípio | Descrição | Benefício |
|-----------|-----------|-----------|
| **Single Responsibility** | Cada agente faz uma coisa bem | Manutenção simplificada |
| **Loose Coupling** | Agentes comunicam via mensagens | Escalabilidade |
| **Self-Healing** | Fallbacks automáticos | Resiliência |
| **Observable** | LangSmith traces por agente | Debugging facilitado |

## 15.2 Os 11 Agentes Especializados

### Orchestrator Agent (Central)

**Objetivo:** Orquestrar o fluxo entre agentes e gerenciar estado da conversa.

| Aspecto | Detalhe |
|---------|---------|
| **Input** | Mensagem do usuário, contexto, histórico |
| **Output** | Delegação para agentes, resposta final |
| **Framework** | LangGraph StateGraph |
| **LLM** | Claude Sonnet 4 |
| **Status** | ✅ Funcional |

---

### Agent 1: Job Intake Agent (Criação de Vagas)

**Objetivo:** Transformar descrições de vagas em linguagem natural em estruturas normalizadas.

| Aspecto | Detalhe |
|---------|---------|
| **Input** | Texto livre, JD, conversa |
| **Output** | Vaga estruturada (JSON) |
| **Metodologia** | Entity Extraction + Slot Filling |
| **LLM** | Claude Sonnet 4 |
| **Contexto** | Vagas anteriores, templates, mercado |

**Workflow:**
```
User Input → Intent Detection → Entity Extraction → 
Validation → Approval Request → Persistence → Notification
```

**Loop de Autoaprendizagem:**
1. Coleta feedback de vagas preenchidas
2. Identifica padrões de sucesso (vagas que geraram boas contratações)
3. Ajusta templates e sugestões
4. A/B test de diferentes formatos de JD

---

### Agent 2: Sourcing Agent (Busca de Candidatos)

**Objetivo:** Encontrar candidatos qualificados usando busca two-tier (local + Pearch AI).

| Aspecto | Detalhe |
|---------|---------|
| **Input** | Query natural, vaga, perfil ideal |
| **Output** | Lista rankeada de candidatos |
| **Metodologia** | Semantic Search + Scoring |
| **Integração** | PostgreSQL + Pearch AI API |
| **Contexto** | Histórico de buscas, contratações passadas |

**Algoritmo Two-Tier:**
```
1. TIER 1 - Busca Local (Custo: 0)
   └─ PostgreSQL full-text + similarity
   └─ Se resultados >= 10 com score > 0.7 → STOP
   
2. TIER 2 - Pearch AI (Custo: 2 créditos)
   └─ Ativado SE: resultados locais < 10 OU score < 0.7
   └─ Semantic search em 340M+ perfis
   └─ Merge + dedupe com resultados locais
```

**Loop de Autoaprendizagem:**
1. Trackeia quais candidatos avançaram no processo
2. Aprende características de candidatos bem-sucedidos
3. Ajusta scoring weights dinamicamente
4. Melhora queries baseado em feedback do recrutador

---

### Agent 3: Screening Agent (Triagem WSI)

**Objetivo:** Realizar triagem automatizada por voz usando metodologia WSI.

| Aspecto | Detalhe |
|---------|---------|
| **Input** | Lista de candidatos, script de perguntas |
| **Output** | Scores, transcrições, análise comportamental |
| **Metodologia** | WSI (Wedo Screening Interview) |
| **Integração** | OpenMic.ai + Deepgram + Claude |
| **Contexto** | Vaga, perfil ideal, red flags históricos |

**Workflow WSI:**
```
Candidato selecionado → Agendamento automático → 
Ligação OpenMic → STT Deepgram → Análise Claude → 
Big Five Score → Red Flags Detection → Report
```

**Métricas Coletadas:**
- Tempo de resposta (hesitação)
- Consistência narrativa
- Alinhamento com CV
- Padrões de linguagem (confiança, evasão)
- Soft skills demonstradas

---

### Agent 4: Evaluation Agent (Avaliação por Rubricas Estruturadas)

**Objetivo:** Avaliar match CV vs Vaga usando metodologia de Rubricas Estruturadas baseada em Schmidt & Hunter (1998) e BARS.

| Aspecto | Detalhe |
|---------|---------|
| **Input** | CV do candidato, requisitos da vaga com prioridades |
| **Output** | Rubric Score (0-100), avaliações por requisito, evidências |
| **Metodologia** | Rubricas Estruturadas + Análise Semântica LLM |
| **LLM** | Claude para extração de evidências e avaliação contextual |
| **Contexto** | Requisitos da vaga, histórico de contratações |

**Metodologia de Rubricas Estruturadas:**

*Escala de 4 Níveis:*
| Nível | Pontos | Descrição |
|-------|--------|-----------|
| Exceeds | 100 | Excede expectativas |
| Meets | 75 | Atende plenamente |
| Partial | 40 | Atende parcialmente |
| Missing | 0 | Não demonstrado |

*Prioridades (Multiplicadores):*
| Prioridade | Multiplicador |
|------------|---------------|
| Essential | 3x |
| Important | 2x |
| Nice to Have | 1x |

**Fórmula do Rubric Score:**
```
Rubric Score = Σ(Pontos × Multiplicador) / Σ(100 × Multiplicador) × 100

Cada avaliação inclui:
- Nível atribuído (Exceeds/Meets/Partial/Missing)
- Evidência: citação específica do CV
- Reasoning: justificativa da avaliação
```

**Importante - Separação de Assessments:**
> O Rubric Score avalia APENAS match CV vs Vaga. As seguintes dimensões requerem assessments SEPARADOS e não fazem parte deste score:
> - **Big Five / OCEAN**: Requer questionário psicométrico
> - **WSI Score**: Requer entrevista estruturada por voz
> - **Cultural Fit**: Requer assessment + análise organizacional

**Loop de Autoaprendizagem:**
1. Correlaciona Rubric Scores com conversão em contratação
2. Ajusta calibração dos níveis (Exceeds/Meets/Partial)
3. Identifica requisitos preditivos de sucesso
4. Reporta accuracy trimestral por tipo de vaga

---

### Agent 5: Scheduling Agent (Agendamento)

**Objetivo:** Coordenar agendas e marcar entrevistas automaticamente.

| Aspecto | Detalhe |
|---------|---------|
| **Input** | Candidato, entrevistadores, preferências |
| **Output** | Evento criado, confirmações enviadas |
| **Metodologia** | Constraint Satisfaction + Optimization |
| **Integração** | Microsoft Graph Calendar |
| **Contexto** | Fuso horário, preferências, histórico |

**Workflow:**
```
Solicitação → Check disponibilidade (Graph API) → 
Sugestão de horários → Confirmação candidato → 
Criação evento → Lembretes → Follow-up
```

---

### Agent 6: Communication Agent (Comunicação Omnichannel)

**Objetivo:** Gerenciar toda comunicação com candidatos de forma personalizada.

| Aspecto | Detalhe |
|---------|---------|
| **Input** | Evento trigger, template, contexto |
| **Output** | Mensagem enviada, resposta processada |
| **Metodologia** | Contextual Generation + A/B Testing |
| **Integração** | Email, WhatsApp, Teams, SMS |
| **Contexto** | Histórico do candidato, tom da empresa |

**Canais Suportados:**
| Canal | Provider | Custo | Use Case |
|-------|----------|-------|----------|
| Email | SendGrid | $0.001/email | Formal, documentação |
| WhatsApp | Twilio | $0.05/msg | Rápido, informal |
| SMS | Twilio | $0.01/msg | Urgente, fallback |
| Teams | Graph API | Incluído | Interno |

## 15.3 Orquestração e Fluxo de Trabalho

### Intent Router (Classificador Central)

```
┌─────────────────────────────────────────────────────────┐
│                    USER MESSAGE                          │
│  "Preciso de 3 devs Python sênior para começar em jan"  │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   INTENT ROUTER                          │
│  Claude Sonnet → Classifica intenção (95%+ confidence)  │
│                                                          │
│  Detected: [JOB_CREATION, CANDIDATE_SEARCH, SCHEDULING] │
└────────────────────────┬────────────────────────────────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
         ┌────────┐ ┌────────┐ ┌────────┐
         │ Job    │ │Sourcing│ │Schedule│
         │ Intake │ │ Agent  │ │ Agent  │
         └────┬───┘ └────┬───┘ └────┬───┘
              │          │          │
              └──────────┼──────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   TASK PLANNER                           │
│  Ordena execução baseado em dependências:               │
│  1. Job Intake (criar vaga) → 2. Sourcing (buscar) →    │
│  3. Screening (triagem) → 4. Scheduling (agendar)       │
└─────────────────────────────────────────────────────────┘
```

### Policy Engine (Regras de Negócio)

| Regra | Limite | Ação |
|-------|--------|------|
| Pearch searches/dia | 10 | Block + upgrade prompt |
| Voice screenings/dia | 20 | Queue para próximo dia |
| Bulk email > 10 | Approval | Pausa + solicita aprovação |
| Candidato blacklisted | Block | Notifica + registra |
| LIA Score < 30 | Alert | Sugere descarte |

## 15.4 Loops de Autoaprendizagem

### Feedback Loop Geral

```
┌──────────────────────────────────────────────────────────┐
│                    FEEDBACK LOOP                          │
│                                                           │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌────────┐│
│  │ Action  │───▶│ Outcome │───▶│ Analysis│───▶│ Update ││
│  │ (Agent) │    │ (Track) │    │ (ML)    │    │(Weights││
│  └─────────┘    └─────────┘    └─────────┘    └────────┘│
│       ▲                                            │     │
│       └────────────────────────────────────────────┘     │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### Métricas de Aprendizado por Agente

| Agente | Métrica de Sucesso | Frequência |
|--------|-------------------|------------|
| Job Intake | Vagas preenchidas / Vagas criadas | Mensal |
| Sourcing | Candidatos contratados / Candidatos apresentados | Semanal |
| Screening | Accuracy WSI vs Performance 6m | Trimestral |
| Evaluation | Correlação LIA Score vs Retenção | Trimestral |
| Scheduling | Taxa de no-show | Semanal |
| Communication | Open rate, Response rate | Diário |

## 15.5 Arquitetura de IA Técnica

### Stack de Modelos de Linguagem (LLMs)

| Modelo | Provider | Uso | Custo/1M tokens | Latência |
|--------|----------|-----|-----------------|----------|
| **Claude Sonnet 4** | Anthropic | Intent Router, Análise WSI | $3.00 input / $15.00 output | ~2s |
| **Claude Haiku 3.5** | Anthropic | Classificação rápida, validação | $0.25 input / $1.25 output | ~0.5s |
| **GPT-4o** | OpenAI | Fallback, comparação | $2.50 input / $10.00 output | ~1.5s |
| **Gemini 2.0 Flash** | Google | Tarefas leves, fallback | $0.075 input / $0.30 output | ~0.3s |

**Para Speech-to-Text (STT):**
| Provider | Modelo | Custo | Uso |
|----------|--------|-------|-----|
| **Deepgram** | Nova-2 | $0.0043/min | WSI principal |
| **Google Cloud** | Speech-to-Text | $0.006/15s (~$0.024/min) | Fallback |
| **OpenAI** | Whisper | $0.006/min | Alternativa |

**Estratégia de Fallback:**
```
Claude Sonnet (primary) → GPT-4o (backup) → Gemini Flash (light tasks)
STT: Deepgram (primary) → Google Cloud (backup) → Whisper (fallback)
```

### Embeddings e Busca Semântica

| Modelo | Dimensões | Uso | Custo/1K tokens* |
|--------|-----------|-----|------------------|
| **text-embedding-3-large** | 3072 | Candidatos, vagas | $0.00013 |
| **text-embedding-3-small** | 1536 | Busca rápida | $0.00002 |
| **Voyage-3** | 1024 | Alternativa | $0.00006 |

*Nota: Custos por 1K tokens (não 1M). Exemplo: 10M tokens = ~$1.30 com text-embedding-3-large.

**Estimativa de Custo Embeddings (mensal):**
| Volume | Tokens | Custo (3-large) | Custo (3-small) |
|--------|--------|-----------------|-----------------|
| 1k CVs | ~5M tokens | ~$0.65 | ~$0.10 |
| 10k CVs | ~50M tokens | ~$6.50 | ~$1.00 |
| 100k CVs | ~500M tokens | ~$65.00 | ~$10.00 |

**Armazenamento de Vetores:**
- **PostgreSQL + pgvector** (MVP) - Integrado, sem custo adicional
- **Pinecone** (Scale) - Serverless, $0.00001/query

### Framework Principal: LangGraph

```
┌─────────────────────────────────────────────────────────────┐
│                      LANGGRAPH ARCHITECTURE                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐   │
│  │   STATE     │────▶│    NODES    │────▶│   EDGES     │   │
│  │  (Context)  │     │  (Actions)  │     │(Transitions)│   │
│  └─────────────┘     └─────────────┘     └─────────────┘   │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    GRAPH EXECUTOR                    │   │
│  │  • Gerencia estado entre nodes                       │   │
│  │  • Controla fluxo condicional                        │   │
│  │  • Persiste checkpoints                              │   │
│  │  • Suporta human-in-the-loop                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Por que LangGraph?**
| Aspecto | LangGraph | LangChain | CrewAI |
|---------|-----------|-----------|--------|
| **Controle de fluxo** | Total (grafos) | Limitado (chains) | Médio |
| **Estado persistente** | Nativo | Manual | Limitado |
| **Human-in-the-loop** | Nativo | Manual | Básico |
| **Debugging** | Excelente | Bom | Médio |
| **Custo** | OSS gratuito | OSS gratuito | $60k+/ano |

### Componentes LangGraph Implementados

```python
# Estrutura do Grafo Principal
from langgraph.graph import StateGraph

class LIAState(TypedDict):
    messages: list[BaseMessage]      # Histórico de conversa
    intent: str                       # Intenção detectada
    entities: dict                    # Entidades extraídas
    agent_results: dict               # Resultados dos agentes
    pending_approvals: list           # Aprovações pendentes
    context: dict                     # Contexto adicional

# Grafo de Orquestração
orchestrator = StateGraph(LIAState)
orchestrator.add_node("intent_router", route_intent)
orchestrator.add_node("job_intake", job_intake_agent)
orchestrator.add_node("sourcing", sourcing_agent)
orchestrator.add_node("screening", screening_agent)
orchestrator.add_node("evaluation", evaluation_agent)
orchestrator.add_node("scheduling", scheduling_agent)
orchestrator.add_node("communication", communication_agent)
orchestrator.add_node("response_planner", plan_response)

# Edges condicionais
orchestrator.add_conditional_edges(
    "intent_router",
    route_to_agents,
    {
        "job_creation": "job_intake",
        "candidate_search": "sourcing",
        "schedule_interview": "scheduling",
        "send_message": "communication",
        "evaluate_candidate": "evaluation",
        "voice_screening": "screening"
    }
)
```

### Arquitetura de Prompts

**System Prompts por Agente:**

| Agente | Prompt Strategy | Técnicas |
|--------|-----------------|----------|
| **Intent Router** | Few-shot + JSON mode | Exemplos de cada intenção |
| **Job Intake** | Slot filling + validation | Chain-of-thought |
| **Sourcing** | Query expansion | Self-consistency |
| **Screening** | STAR method | Structured output |
| **Evaluation** | Rubric-based | Multi-criteria |
| **Communication** | Tone matching | Personalization |

**Exemplo de Prompt (Intent Router):**
```markdown
Você é um classificador de intenções para um sistema de recrutamento.

Classifique a mensagem do usuário em uma das categorias:
- JOB_CREATION: Criar ou editar vaga
- CANDIDATE_SEARCH: Buscar candidatos
- SCHEDULE_INTERVIEW: Agendar entrevista
- EVALUATE_CANDIDATE: Avaliar candidato
- VOICE_SCREENING: Triagem por voz
- SEND_MESSAGE: Enviar comunicação
- GENERAL_QUESTION: Pergunta geral
- UNKNOWN: Não classificável

Responda em JSON:
{
  "intent": "CATEGORIA",
  "confidence": 0.0-1.0,
  "entities": {...}
}

Exemplos:
User: "Preciso contratar 3 devs Python"
{"intent": "JOB_CREATION", "confidence": 0.95, "entities": {"role": "dev Python", "quantity": 3}}

User: "Encontre candidatos com experiência em AWS"
{"intent": "CANDIDATE_SEARCH", "confidence": 0.92, "entities": {"skills": ["AWS"]}}
```

### RAG (Retrieval-Augmented Generation)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         RAG PIPELINE COMPLETO                             │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  INDEXAÇÃO (Offline):                                                     │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   │
│  │Documents│──▶│   PII   │──▶│Chunking │──▶│Embedding│──▶│  Store  │   │
│  │(CVs,JDs)│   │ Redact  │   │(500 tok)│   │(OpenAI) │   │(pgvector│   │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘   │
│                     │                                                     │
│                     ▼                                                     │
│              ┌─────────────┐                                              │
│              │ PII Vault   │ ← Dados sensíveis separados (LGPD)          │
│              │(encrypted)  │                                              │
│              └─────────────┘                                              │
│                                                                           │
│  RETRIEVAL (Online):                                                      │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   │
│  │  Query  │──▶│Embedding│──▶│ Search  │──▶│ Rerank  │──▶│Validate │   │
│  │         │   │         │   │(cosine) │   │(cross)  │   │ Output  │   │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘   │
│                                                                │          │
│                                                                ▼          │
│                                                   ┌─────────────────┐    │
│                                                   │   TOP K CHUNKS  │    │
│                                                   │  + Confidence   │    │
│                                                   │    Scores       │    │
│                                                   └─────────────────┘    │
│                                                                           │
│  MONITORAMENTO (Contínuo):                                                │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐                                 │
│  │Freshness│   │Relevance│   │ Drift   │                                 │
│  │ Check   │   │ Metrics │   │Detection│                                 │
│  └─────────┘   └─────────┘   └─────────┘                                 │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

**Tratamento de PII (LGPD Compliance):**

| Campo Sensível | Tratamento | Onde Armazena |
|----------------|------------|---------------|
| CPF | Hash + tokenização | PII Vault |
| Email pessoal | Pseudonimização | PII Vault |
| Telefone | Mascaramento parcial | PII Vault |
| Endereço | Omitido do embedding | PII Vault |
| Foto | Não indexada | Object Storage |
| Salário atual | Criptografado | PII Vault |

**Nota:** Embeddings contêm apenas skills, experiência, formação - nunca dados pessoais identificáveis.

**Validação e Qualidade do RAG:**

| Métrica | Target | Frequência | Alerta |
|---------|--------|------------|--------|
| **Recall@10** | > 0.85 | Semanal | < 0.75 |
| **Precision@5** | > 0.70 | Semanal | < 0.55 |
| **MRR (Mean Reciprocal Rank)** | > 0.80 | Semanal | < 0.65 |
| **Latência P95** | < 500ms | Contínuo | > 1s |
| **Freshness (docs > 30 dias)** | < 10% | Diário | > 25% |
| **Drift score** | < 0.15 | Mensal | > 0.25 |

**Processo de Validação Offline:**
1. **Dataset de teste** - 500 queries com relevância anotada
2. **Avaliação semanal** - Recall, Precision, MRR automatizado
3. **Drift detection** - Comparar distribuição de embeddings novos vs baseline
4. **Re-indexação** - Trigger automático se freshness > 25%

**Fontes de Conhecimento:**
| Fonte | Volume Est. | Atualização | Uso | PII? |
|-------|-------------|-------------|-----|------|
| CVs de candidatos | 10k-100k docs | Contínua | Sourcing | Sim (redacted) |
| Job descriptions | 1k-10k docs | Diária | Matching | Não |
| Histórico de contratações | 100-1k docs | Semanal | Learning | Sim (redacted) |
| Templates de comunicação | 50-100 docs | Mensal | Communication | Não |
| Políticas da empresa | 10-50 docs | Raro | Compliance | Não |

### Memória e Contexto

**Tipos de Memória:**

| Tipo | Escopo | Storage | TTL |
|------|--------|---------|-----|
| **Working Memory** | Conversa atual | In-memory (Redis) | 24h |
| **Session Memory** | Sessão do usuário | PostgreSQL | 7 dias |
| **Long-term Memory** | Histórico completo | PostgreSQL | Permanente |
| **Semantic Memory** | Conhecimento geral | pgvector | Permanente |

**Estrutura de Contexto por Conversa:**
```json
{
  "conversation_id": "uuid",
  "user_id": "uuid",
  "company_id": "uuid",
  "started_at": "2025-11-26T10:00:00Z",
  "context": {
    "active_job_ids": ["uuid1", "uuid2"],
    "recent_candidates": ["uuid3", "uuid4"],
    "pending_actions": ["approval_required"],
    "preferences": {
      "communication_style": "formal",
      "language": "pt-BR"
    }
  },
  "messages": [
    {"role": "user", "content": "...", "timestamp": "..."},
    {"role": "assistant", "content": "...", "timestamp": "..."}
  ],
  "agent_results": {
    "sourcing": {"candidates_found": 15, "timestamp": "..."},
    "screening": {"completed": 3, "pending": 5}
  }
}
```

### Observabilidade e Monitoramento

**Stack de Observabilidade:**

| Ferramenta | Função | Custo | Prioridade |
|------------|--------|-------|------------|
| **LangSmith** | Traces LLM, debugging | $39/user/mês | P0 (MVP) |
| **Sentry** | Erros, exceptions | $26/mês | P1 |
| **Prometheus** | Métricas custom | OSS | P1 |
| **Grafana** | Dashboards | OSS | P1 |
| **PostHog** | Product analytics | Free tier | P2 |

**Métricas Monitoradas:**

| Métrica | Target | Alerta |
|---------|--------|--------|
| **Latência P50** | < 2s | > 5s |
| **Latência P99** | < 10s | > 20s |
| **Error rate** | < 1% | > 5% |
| **Intent accuracy** | > 95% | < 90% |
| **Fallback rate** | < 5% | > 15% |
| **Token usage/request** | < 4k | > 10k |

### Segurança e Compliance

| Aspecto | Implementação | Status |
|---------|---------------|--------|
| **Dados sensíveis** | Não enviar PII para LLMs externos | Planejado |
| **Prompt injection** | Input sanitization + guardrails | Planejado |
| **Rate limiting** | Por usuário/empresa | Implementado |
| **Audit logging** | Todas as ações LLM registradas | Planejado |
| **LGPD** | Consentimento, exclusão, portabilidade | Planejado |
| **Encryption** | TLS em trânsito, AES-256 em repouso | Parcial |

### Plano de Coleta de Dados para Autoaprendizagem

Para viabilizar os loops de feedback mencionados na seção 15.4:

| Dado | Fonte | Frequência | Uso |
|------|-------|------------|-----|
| **Candidato contratado** | ATS/Manual | Evento | Ajustar scoring weights |
| **Performance 6m** | Integração HRIS | Trimestral | Validar WSI accuracy |
| **Feedback recrutador** | Thumbs up/down | Tempo real | Melhorar respostas |
| **Tempo no pipeline** | Sistema | Contínuo | Otimizar fluxo |
| **Taxa de resposta** | Email/WhatsApp | Diário | A/B test mensagens |
| **No-show rate** | Calendar | Semanal | Ajustar lembretes |

**Pipeline de Retraining:**
```
┌─────────────────────────────────────────────────────────────┐
│                   RETRAINING PIPELINE                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. COLETA (Contínua)                                        │
│     └─ Eventos de sucesso/falha → Data Lake                  │
│                                                              │
│  2. AGREGAÇÃO (Semanal)                                      │
│     └─ Métricas por agente → Dashboard                       │
│                                                              │
│  3. ANÁLISE (Mensal)                                         │
│     └─ Identificar padrões → Report                          │
│                                                              │
│  4. AJUSTE (Trimestral)                                      │
│     └─ Atualizar prompts, weights → Deploy                   │
│                                                              │
│  5. VALIDAÇÃO (Pós-deploy)                                   │
│     └─ A/B test 10% tráfego → Confirmar melhoria             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

# 16. Modelo de Monetização e Pricing

## 16.1 Modelo de Créditos Pearch AI

### Custo Base Pearch

| Tipo de Query | Créditos Pearch | Custo Estimado* |
|---------------|-----------------|-----------------|
| Busca simples (10 perfis) | 10 | $0.10 |
| Busca expandida (50 perfis) | 50 | $0.50 |
| Busca premium (100 perfis) | 100 | $1.00 |
| Enriquecimento (email/phone) | 5/perfil | $0.05/perfil |

*Estimativa baseada em volume médio. Descontos de até 10x para enterprise.

### Markup WeDOTalent

| Estratégia | Markup | Margem | Justificativa |
|------------|--------|--------|---------------|
| **Conservative** | +30% | 23% | Competitivo, volume |
| **Standard** | +50% | 33% | Mercado padrão |
| **Premium** | +100% | 50% | Valor agregado (LIA Score) |

**Recomendação:** Iniciar com **+50% markup** e ajustar baseado em:
- Percepção de valor do cliente
- Elasticidade de demanda
- Custo de suporte

### Modelo de Receita Pearch

```
Receita Pearch = (Créditos Consumidos × Custo Unitário) × (1 + Markup%)

Exemplo:
- Cliente usa 1.000 créditos/mês
- Custo Pearch: $100
- Markup 50%: $50
- Receita bruta: $150
- Margem: $50 (33%)
```

## 16.2 Planos de Assinatura

### Plugin LIA (Integração Teams/Slack)

| Plano | Preço | Usuários | Buscas/mês | WSI/mês | Suporte |
|-------|-------|----------|------------|---------|---------|
| **Starter** | R$ 499/mês | 3 | 50 | 10 | Email |
| **Professional** | R$ 1.499/mês | 10 | 200 | 50 | Chat |
| **Enterprise** | Sob consulta | Ilimitado | Custom | Custom | Dedicado |

### ATS Completo WeDOTalent

| Plano | Preço | Vagas | Candidatos | Storage |
|-------|-------|-------|------------|---------|
| **Essencial** | R$ 2.999/mês | 20 | 5.000 | 10GB |
| **Business** | R$ 5.999/mês | 50 | 20.000 | 50GB |
| **Enterprise** | R$ 12.000+/mês | Ilimitado | Ilimitado | Ilimitado |

## 16.3 Custos Operacionais Estimados

### Por Transação

| Operação | Custo Direto | Custo Nosso* |
|----------|--------------|--------------|
| Busca Pearch (50 perfis) | $0.50 | $0.75 |
| WSI Call (10 min) | $0.10 | $0.30 |
| Email SendGrid | $0.001 | $0.003 |
| WhatsApp Twilio | $0.05 | $0.08 |
| Claude API call | $0.015 | $0.025 |

*Inclui overhead de infra, logs, suporte.

### Margem por Plano (Estimativa)

| Plano | Receita | Custo Variável | Custo Fixo* | Margem |
|-------|---------|----------------|-------------|--------|
| Starter | R$ 499 | R$ 100 | R$ 50 | **70%** |
| Professional | R$ 1.499 | R$ 300 | R$ 100 | **73%** |
| Enterprise | R$ 5.000+ | R$ 800 | R$ 500 | **74%** |

*Custo fixo proporcional: infra, suporte, desenvolvimento.

---

# 17. Análise Build vs Buy

## 17.1 Voice Screening: OpenMic AI vs Desenvolvimento Interno

### Opção A: OpenMic AI (Contratar)

| Aspecto | Detalhe |
|---------|---------|
| **Custo** | $0.01/minuto |
| **Setup** | 1-2 semanas |
| **Manutenção** | Zero (SaaS) |
| **Escalabilidade** | Infinita |
| **Customização** | Média (templates) |

**Custo Mensal (1.000 chamadas × 10 min):**
- OpenMic: 10.000 min × $0.01 = **$100/mês**

### Opção B: Desenvolvimento Interno

| Aspecto | Detalhe |
|---------|---------|
| **Desenvolvimento** | 3-6 meses (2 devs) |
| **Custo Inicial** | R$ 150.000 - 300.000 |
| **Manutenção** | 1 dev part-time |
| **Infraestrutura** | Twilio + Deepgram + GPU |
| **Custo Mensal Infra** | $500 - 2.000 |

**Break-even:**
```
Custo Desenvolvimento: R$ 200.000
Economia Mensal: R$ 400 (OpenMic vs interno)
Break-even: 500 meses (41 anos) ❌
```

### Recomendação Voice Screening

| Fase | Recomendação | Justificativa |
|------|--------------|---------------|
| **0-50 clientes** | OpenMic AI | Custo baixo, zero dev |
| **50-200 clientes** | OpenMic AI | Ainda econômico |
| **200+ clientes** | Avaliar híbrido | Negociar volume |

**Veredicto:** ✅ **OpenMic AI** (pelo menos até 200 clientes)

---

## 17.2 Plataforma Multi-Agentes: Build vs Buy

### Opções Comparadas (Valores em USD)

| Plataforma | Custo Anual (USD) | Custo Anual (BRL)* | Setup | Customização | Lock-in |
|------------|-------------------|-------------------|-------|--------------|---------|
| **LangGraph (OSS)** | $0 + engenharia | R$ 300k-500k | Alto | Total | Baixo |
| **CrewAI Cloud** | $60k-120k | R$ 300k-600k | Médio | Alta | Médio |
| **Relevance AI** | $10k-50k | R$ 50k-250k | Baixo | Média | Alto |
| **Beam AI** | $50k-100k | R$ 250k-500k | Baixo | Baixa | Alto |

*Conversão: USD 1 = BRL 5.0 (ajustar conforme câmbio)

### Custos de Engenharia LangGraph (Detalhado)

| Componente | Ano 1 | Ano 2 | Ano 3 |
|------------|-------|-------|-------|
| **2 Devs Sênior Python/IA** (CLT) | R$ 240k | R$ 260k | R$ 280k |
| **DevOps/Infra** (part-time) | R$ 60k | R$ 80k | R$ 100k |
| **Infraestrutura Cloud** | R$ 24k | R$ 48k | R$ 96k |
| **Licenças e Ferramentas** | R$ 12k | R$ 18k | R$ 24k |
| **Contingência (15%)** | R$ 50k | R$ 61k | R$ 75k |
| **TOTAL** | **R$ 386k** | **R$ 467k** | **R$ 575k** |

### Análise TCO (3 anos)

| Solução | Ano 1 | Ano 2 | Ano 3 | Total | Observação |
|---------|-------|-------|-------|-------|------------|
| **LangGraph (interno)** | R$ 386k | R$ 467k | R$ 575k | **R$ 1.428k** | Controle total, risco técnico |
| **CrewAI Enterprise** | R$ 350k | R$ 350k | R$ 350k | **R$ 1.050k** | Menor risco, menos flex |
| **Relevance AI** | R$ 150k | R$ 150k | R$ 150k | **R$ 450k** | Mais barato, alto lock-in |

**Nota:** LangGraph requer time de engenharia dedicado. Relevance AI é mais barato mas limita customização.

### Recomendação Multi-Agentes

| Fase | Recomendação | Justificativa |
|------|--------------|---------------|
| **MVP (0-20 clientes)** | LangGraph OSS | Já implementado, custo zero |
| **Growth (20-100)** | LangGraph + LangSmith | Observabilidade |
| **Scale (100+)** | Avaliar CrewAI/Relevance | Volume justifica custo |

**Veredicto:** ✅ **LangGraph** no curto prazo (2 anos)

---

## 17.3 Infraestrutura IA: Cloud Comparison

### Opções Analisadas

| Provider | Foco | Custo Base | Vantagens |
|----------|------|------------|-----------|
| **Google Cloud AI** | Full-stack | $$$$ | Ecossistema, Gemini |
| **AWS Bedrock** | Enterprise | $$$$ | Segurança, compliance |
| **Beam.cloud** | AI Serverless | $$ | Simples, GPU on-demand |
| **Modal.com** | Dev-friendly | $$ | Python-native, rápido |
| **Replicate** | Model hosting | $ | Pay-per-inference |

### Custo Comparativo (1M inference/mês)

| Provider | Custo Mensal | Latência | Complexidade |
|----------|--------------|----------|--------------|
| Google Cloud | $2.000-5.000 | Baixa | Alta |
| AWS Bedrock | $2.500-6.000 | Baixa | Alta |
| Beam.cloud | $500-1.500 | Média | Baixa |
| Modal.com | $400-1.200 | Média | Baixa |
| Replicate | $300-800 | Alta | Muito baixa |

### Recomendação Infraestrutura

| Fase | Recomendação | Custo Est. |
|------|--------------|------------|
| **MVP** | Replit + Replicate | R$ 500/mês |
| **Growth** | Modal.com | R$ 2.000/mês |
| **Scale** | Google Cloud AI | R$ 10.000/mês |

---

## 17.4 Viabilidade por Fase de Crescimento

### Cenários de Receita Projetada

| Fase | Clientes | MRR | ARR | Margem Est. |
|------|----------|-----|-----|-------------|
| **Seed (6m)** | 10 | R$ 15k | R$ 180k | 60% |
| **Series A (12m)** | 50 | R$ 75k | R$ 900k | 65% |
| **Growth (24m)** | 200 | R$ 300k | R$ 3.6M | 70% |
| **Scale (36m)** | 500 | R$ 750k | R$ 9M | 75% |

### Decisões por Fase

```
┌─────────────────────────────────────────────────────────┐
│                DECISION MATRIX BY PHASE                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  SEED (0-10 clientes, 0-6 meses):                       │
│  ├─ Voice: OpenMic AI ✅                                │
│  ├─ Agentes: LangGraph OSS ✅                           │
│  ├─ Infra: Replit + Replicate ✅                        │
│  └─ Pearch: Pay-as-you-go ✅                            │
│                                                          │
│  SERIES A (10-50 clientes, 6-18 meses):                 │
│  ├─ Voice: OpenMic AI (negociar volume) ✅              │
│  ├─ Agentes: LangGraph + LangSmith ✅                   │
│  ├─ Infra: Modal.com 🔄                                 │
│  └─ Pearch: Contrato anual (desconto) 🔄                │
│                                                          │
│  GROWTH (50-200 clientes, 18-36 meses):                 │
│  ├─ Voice: Avaliar híbrido (OpenMic + interno) 🔄       │
│  ├─ Agentes: Avaliar CrewAI Enterprise 🔄               │
│  ├─ Infra: GCP ou AWS 🔄                                │
│  └─ Pearch: Partnership/equity deal 🔄                  │
│                                                          │
│  SCALE (200+ clientes, 36+ meses):                      │
│  ├─ Voice: Desenvolvimento interno viável ⏳            │
│  ├─ Agentes: Multi-cloud híbrido ⏳                     │
│  ├─ Infra: Multi-cloud + edge ⏳                        │
│  └─ Pearch: White-label ou aquisição ⏳                 │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

# 18. Metodologia WSI (Wedo Screening Interview)

## 18.1 Visão Geral

O **WSI (Wedo Screening Interview)** é uma metodologia proprietária de triagem por voz que combina:

1. **Entrevista por voz automatizada** - IA conversacional via telefone
2. **Speech-to-Text em tempo real** - Transcrição instantânea
3. **Análise comportamental** - Big Five, padrões de fala, red flags
4. **Scoring preditivo** - Probabilidade de sucesso na vaga

## 18.2 Framework de Avaliação

### Dimensões Avaliadas

| Dimensão | Peso | Como Mede | Indicadores |
|----------|------|-----------|-------------|
| **Competência Técnica** | 30% | Perguntas situacionais | Vocabulário, exemplos concretos |
| **Comunicação** | 20% | Análise de fala | Clareza, estrutura, hesitação |
| **Motivação** | 15% | Perguntas abertas | Entusiasmo, razões, metas |
| **Cultural Fit** | 15% | Valores/cenários | Alinhamento com empresa |
| **Red Flags** | 20% | Pattern matching | Inconsistências, evasão |

### Big Five Mapping

| Traço | O que Detecta | Método |
|-------|---------------|--------|
| **Openness** | Criatividade, curiosidade | Respostas a cenários novos |
| **Conscientiousness** | Organização, disciplina | Estrutura das respostas |
| **Extraversion** | Energia, sociabilidade | Tom de voz, elaboração |
| **Agreeableness** | Cooperação, empatia | Linguagem colaborativa |
| **Neuroticism** | Estabilidade emocional | Reação a pressão |

## 18.3 Fluxo da Entrevista WSI

### Script Padrão (15 minutos)

```
┌─────────────────────────────────────────────────────────┐
│ FASE 1: ABERTURA (2 min)                                │
├─────────────────────────────────────────────────────────┤
│ • Apresentação da LIA                                    │
│ • Explicação do processo                                 │
│ • Confirmação de disponibilidade                         │
│ • Quebra-gelo: "Como está seu dia?"                     │
└─────────────────────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│ FASE 2: QUALIFICAÇÃO (4 min)                            │
├─────────────────────────────────────────────────────────┤
│ • Confirmação dados do CV                                │
│ • "Qual sua experiência com [skill principal]?"         │
│ • "Me conte sobre seu projeto mais relevante"           │
│ • Knockout questions (visa, disponibilidade, salário)   │
└─────────────────────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│ FASE 3: COMPORTAMENTAL (6 min)                          │
├─────────────────────────────────────────────────────────┤
│ • STAR Questions (2-3 perguntas)                         │
│ • "Conte sobre um desafio técnico que enfrentou..."     │
│ • "Como você lida com pressão de prazo?"                │
│ • "Descreva uma situação de conflito no trabalho"       │
│ • Follow-ups baseados em respostas                       │
└─────────────────────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│ FASE 4: MOTIVAÇÃO (2 min)                               │
├─────────────────────────────────────────────────────────┤
│ • "Por que está buscando nova oportunidade?"            │
│ • "O que te atrai nesta vaga?"                          │
│ • "Onde você se vê em 2-3 anos?"                        │
└─────────────────────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│ FASE 5: FECHAMENTO (1 min)                              │
├─────────────────────────────────────────────────────────┤
│ • "Tem alguma pergunta sobre a empresa/vaga?"           │
│ • Explicação dos próximos passos                         │
│ • Agradecimento e despedida                              │
└─────────────────────────────────────────────────────────┘
```

## 18.4 Red Flags Automáticos

| Red Flag | Indicador | Peso |
|----------|-----------|------|
| **Inconsistência CV** | Dados divergem da fala | -30 pts |
| **Fala negativa de empregadores** | Críticas excessivas | -20 pts |
| **Evasão de perguntas** | Respostas vagas repetidas | -25 pts |
| **Hesitação excessiva** | Pausas longas em perguntas simples | -15 pts |
| **Overqualification** | Experiência muito acima | -10 pts |
| **Jumpy career** | Muitas trocas curtas | -15 pts |

## 18.5 Modos de Triagem (NOVO - Dezembro 2025)

> **✅ IMPLEMENTADO:** Dois modos de triagem operacionais com diferentes níveis de profundidade.

### Quick Screening Mode (10-15 min)

| Aspecto | Detalhe |
|---------|---------|
| **Canal** | WhatsApp (áudio ou texto) |
| **Duração** | 10-15 minutos |
| **Perguntas** | 6 perguntas padrão |
| **Transcrição** | Deepgram Nova-2 ($0.0043/min) |
| **Análise** | Claude Sonnet (básica) |
| **Output** | Score 0-100 + Recomendação (Advance/Hold/Reject) |

**6 Perguntas Padrão:**
1. Apresentação profissional breve
2. Experiência relevante para a vaga
3. Expectativa salarial
4. Disponibilidade para início
5. Motivação para a vaga
6. Pergunta knockout (ex: trabalho remoto, viagens)

**Custos por Candidato:**
- Deepgram STT: ~R$ 0.10 (2-3 min de áudio)
- Claude análise: ~R$ 0.05
- **Total: ~R$ 0.15/candidato**

### WSI Full Interview Mode (40-60 min)

| Aspecto | Detalhe |
|---------|---------|
| **Canal** | Chamada telefônica (OpenMic.ai) |
| **Duração** | 40-60 minutos |
| **Perguntas** | Adaptativas (STAR method) |
| **Análise** | Claude Sonnet (completa) + Big Five |
| **Output** | Score detalhado + Transcrição + Red Flags |

**Fases da Entrevista:**
1. **Abertura** (2 min): Apresentação, quebra-gelo
2. **Qualificação** (10 min): Confirmação CV, experiência técnica
3. **Comportamental** (25 min): STAR questions, cenários situacionais
4. **Motivação** (8 min): Expectativas, fit cultural
5. **Fechamento** (5 min): Dúvidas, próximos passos

**Custos por Candidato:**
- OpenMic.ai: ~R$ 3.50 (35 min × $0.10/min)
- Claude análise completa: ~R$ 0.30
- **Total: ~R$ 4.00/candidato**

### Quando Usar Cada Modo

| Critério | Quick Screening | WSI Full |
|----------|-----------------|----------|
| **Volume** | Alto (100+ candidatos) | Baixo (10-30 candidatos) |
| **Senioridade** | Entry/Junior | Pleno/Sênior |
| **Custo** | R$ 0.15 | R$ 4.00 |
| **Profundidade** | Triagem básica | Avaliação completa |
| **Big Five** | ❌ | ✅ |
| **Transcrição** | Resumida | Completa |

---

## 18.6 Output do WSI

### Relatório Gerado

```json
{
  "candidate_id": "uuid",
  "wsi_session_id": "uuid",
  "duration_minutes": 14.5,
  "overall_score": 78,
  "recommendation": "PROCEED",
  
  "scores": {
    "technical_competence": 82,
    "communication": 75,
    "motivation": 85,
    "cultural_fit": 72,
    "red_flags_deduction": -5
  },
  
  "big_five": {
    "openness": 0.72,
    "conscientiousness": 0.81,
    "extraversion": 0.65,
    "agreeableness": 0.78,
    "neuroticism": 0.23
  },
  
  "red_flags": [
    {
      "type": "hesitation",
      "timestamp": "05:23",
      "context": "Pergunta sobre saída do último emprego",
      "severity": "low"
    }
  ],
  
  "highlights": [
    "Experiência sólida com Python e AWS",
    "Boa capacidade de storytelling",
    "Motivação clara para crescimento"
  ],
  
  "concerns": [
    "Hesitação ao falar sobre último emprego",
    "Expectativa salarial no limite superior"
  ],
  
  "transcript_url": "s3://wsi-transcripts/...",
  "audio_url": "s3://wsi-audio/..."
}
```

---

# 19. Roadmap de Features

## 19.1 Definição de Produtos

### Plugin LIA (Integração Teams/Slack)

**Propósito:** Assistente IA para recrutadores dentro das ferramentas que já usam.

| Categoria | Features | Prioridade |
|-----------|----------|------------|
| **Core** | Chat com LIA, busca candidatos, notificações | P0 |
| **Produtividade** | Lembretes, follow-ups, briefing diário | P1 |
| **Inteligência** | Sugestões proativas, insights, alertas | P1 |
| **Integração** | Sync com ATS existente do cliente | P2 |

### ATS Completo WeDOTalent

**Propósito:** Sistema completo para empresas sem ATS ou querendo migrar.

| Categoria | Features | Prioridade |
|-----------|----------|------------|
| **Gestão Vagas** | CRUD, workflows, aprovações, publicação | P0 |
| **Gestão Candidatos** | Pipeline, histórico, documentos | P0 |
| **Recrutamento** | Sourcing, screening, avaliação | P0 |
| **Contratação** | Carta oferta, placement, onboarding | P1 |
| **Analytics** | Dashboards, relatórios, previsões | P1 |
| **Compliance** | LGPD, audit trail, permissões | P0 |

## 19.2 Roadmap por Trimestre

### Q1 2026: Foundation

| Feature | Produto | Esforço | Impacto |
|---------|---------|---------|---------|
| Pipeline visual (Kanban) | Plugin + ATS | 3 semanas | Alto |
| Busca avançada funcional | Plugin + ATS | 2 semanas | Alto |
| Integração Teams básica | Plugin | 4 semanas | Alto |
| Autenticação/RBAC | ATS | 3 semanas | Crítico |
| WSI MVP (5 perguntas) | ATS | 6 semanas | Alto |

### Q2 2026: Growth

| Feature | Produto | Esforço | Impacto |
|---------|---------|---------|---------|
| Email automation com IA | Plugin + ATS | 4 semanas | Alto |
| Integração Pearch AI completa | ATS | 3 semanas | Alto |
| Video interviews + transcrição | ATS | 5 semanas | Médio |
| LIA proativa (sugestões) | Plugin | 4 semanas | Alto |
| Dashboard analytics v1 | Plugin + ATS | 3 semanas | Médio |

### Q3 2026: Intelligence

| Feature | Produto | Esforço | Impacto |
|---------|---------|---------|---------|
| WSI completo (Big Five) | ATS | 6 semanas | Alto |
| Predictive analytics | ATS | 8 semanas | Alto |
| Workforce planning | ATS | 6 semanas | Médio |
| Multi-agent orchestrator v2 | ATS | 8 semanas | Alto |
| Integração Gupy/Pandapé | ATS | 4 semanas | Médio |

### Q4 2026: Enterprise

| Feature | Produto | Esforço | Impacto |
|---------|---------|---------|---------|
| Carta oferta digital | ATS | 3 semanas | Médio |
| Placement tracking | ATS | 4 semanas | Médio |
| Onboarding module | ATS | 8 semanas | Médio |
| White-label option | ATS | 6 semanas | Baixo |
| API pública | Plugin + ATS | 4 semanas | Médio |

## 19.3 Feature Matrix: Plugin vs ATS

| Feature | Plugin | ATS | Justificativa |
|---------|--------|-----|---------------|
| Chat com LIA | ✅ | ✅ | Core de ambos |
| Busca candidatos | ✅ | ✅ | Core de ambos |
| Notificações Teams | ✅ | ❌ | Plugin-specific |
| Pipeline Kanban | ✅ (visual) | ✅ (completo) | Plugin simplificado |
| CRUD vagas | ❌ | ✅ | ATS-only |
| WSI Voice | ❌ | ✅ | Requer infra |
| Video interviews | ❌ | ✅ | Requer storage |
| Carta oferta | ❌ | ✅ | ATS workflow |
| Onboarding | ❌ | ✅ | Pós-contratação |
| Analytics básico | ✅ | ✅ | Diferente scope |
| Analytics preditivo | ❌ | ✅ | Requer dados |
| Workforce planning | ❌ | ✅ | Enterprise |
| Integração ATS externo | ✅ | ❌ | Plugin sync |
| Multi-tenant | ❌ | ✅ | ATS enterprise |

---

# 20. Estratégia de Crescimento

## 20.1 Modelo de Expansão

### Fase 1: Plugin First (0-18 meses)

**Estratégia:** Land-and-expand via Teams/Slack.

```
┌─────────────────────────────────────────────────────────┐
│                    PLUGIN FIRST                          │
│                                                          │
│  1. Cliente instala plugin Teams (grátis/freemium)      │
│  2. Recrutadores usam LIA diariamente                    │
│  3. Valor demonstrado → Upgrade para Pro                │
│  4. Crescimento orgânico no departamento                │
│  5. Upsell para ATS completo                            │
│                                                          │
│  Métricas:                                               │
│  • CAC Plugin: R$ 200 (self-serve)                      │
│  • LTV Plugin: R$ 15.000 (2 anos × Pro)                 │
│  • Conversão Free→Pro: 15%                              │
│  • Upsell Plugin→ATS: 10%                               │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Fase 2: ATS Completo (12-36 meses)

**Estratégia:** Oferecer migração para empresas sem ATS ou insatisfeitas.

```
┌─────────────────────────────────────────────────────────┐
│                   ATS COMPLETO                           │
│                                                          │
│  Target:                                                 │
│  • PMEs sem ATS (planilhas/email)                       │
│  • Empresas insatisfeitas com Gupy/Pandapé              │
│  • Scale-ups precisando de IA                            │
│                                                          │
│  Diferencial:                                            │
│  • AI-first (não bolted-on)                             │
│  • LIA como assistente, não ferramenta                  │
│  • WSI + Analytics preditivo                            │
│  • Preço competitivo                                     │
│                                                          │
│  Métricas:                                               │
│  • CAC ATS: R$ 5.000 (sales-assisted)                   │
│  • LTV ATS: R$ 100.000 (3 anos × Business)              │
│  • Churn: <5% anual                                     │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## 20.2 Crescimento Vertical vs Horizontal

### Vertical (Profundidade no RH)

| Módulo | Descrição | Timeline |
|--------|-----------|----------|
| **Recrutamento** | Core atual | ✅ |
| **Onboarding** | Integração novos funcionários | 2027 |
| **Performance** | Avaliação e feedback | 2027 |
| **Learning** | Treinamento e desenvolvimento | 2028 |
| **Offboarding** | Desligamento estruturado | 2028 |

### Horizontal (Novos Mercados)

| Mercado | Potencial | Barreira | Timeline |
|---------|-----------|----------|----------|
| **Brasil Tech** | Alto | Baixa | ✅ Atual |
| **Brasil Geral** | Alto | Média | 2026 |
| **LATAM (ES)** | Médio | Média | 2027 |
| **Portugal** | Médio | Baixa | 2027 |
| **EUA** | Alto | Alta | 2028+ |

## 20.3 Produtos Futuros

### Curto Prazo (2026)

| Produto | Descrição | Receita Est. |
|---------|-----------|--------------|
| **LIA Plugin Pro** | Versão paga do plugin | R$ 1.500/mês |
| **ATS Essencial** | ATS básico para PMEs | R$ 3.000/mês |
| **WSI Add-on** | Voice screening para ATS externos | R$ 500/mês |

### Médio Prazo (2027)

| Produto | Descrição | Receita Est. |
|---------|-----------|--------------|
| **WeDOTalent Onboarding** | Módulo de integração | R$ 2.000/mês |
| **LIA Enterprise** | Para grandes empresas | R$ 10.000/mês |
| **Talent Insights** | Analytics standalone | R$ 1.000/mês |

### Longo Prazo (2028+)

| Produto | Descrição | Receita Est. |
|---------|-----------|--------------|
| **WeDOTalent HCM** | Suite completa de RH | R$ 20.000/mês |
| **LIA for Staffing** | Para agências | Custom |
| **WeDOTalent Marketplace** | Integrações third-party | % transações |

## 20.4 Unit Economics Target

### Por Produto

| Produto | MRR Target | CAC | LTV | LTV:CAC |
|---------|------------|-----|-----|---------|
| Plugin Free | R$ 0 | R$ 50 | R$ 500* | 10:1 |
| Plugin Pro | R$ 1.500 | R$ 500 | R$ 30.000 | 60:1 |
| ATS Essencial | R$ 3.000 | R$ 3.000 | R$ 72.000 | 24:1 |
| ATS Business | R$ 6.000 | R$ 8.000 | R$ 180.000 | 22:1 |
| ATS Enterprise | R$ 15.000 | R$ 20.000 | R$ 540.000 | 27:1 |

*Valor via conversão para Pro ou upsell para ATS.

### Meta de Crescimento

| Métrica | Ano 1 | Ano 2 | Ano 3 |
|---------|-------|-------|-------|
| **ARR** | R$ 500k | R$ 2M | R$ 6M |
| **Clientes Pagantes** | 30 | 100 | 250 |
| **NRR** | 110% | 120% | 125% |
| **Gross Margin** | 70% | 75% | 80% |
| **CAC Payback** | 12m | 9m | 6m |

## 20.5 Estratégia de Comunidade e Geração de Leads

### "Terapia de Grupo para Recrutadores"

Sistema de geração de leads e nurturing através de comunidade exclusiva para recrutadores.

```
┌─────────────────────────────────────────────────────────────────┐
│           TERAPIA DE GRUPO PARA RECRUTADORES                    │
│                                                                  │
│  Conceito: Comunidade exclusiva e gratuita onde recrutadores    │
│  compartilham experiências, dores, vitórias e aprendizados.     │
│                                                                  │
│  Posicionamento: "Recrutar não precisa ser uma luta solitária"  │
│                                                                  │
│  Modelo:                                                        │
│  • 100% gratuito                                                │
│  • Vagas limitadas (exclusividade)                              │
│  • Comunidade fechada (WhatsApp/Discord)                        │
│  • Eventos mensais (online)                                     │
│  • Conteúdo exclusivo                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Funil de Conversão da Comunidade

```
┌─────────────────────────────────────────────────────────────────┐
│  AWARENESS                                                       │
│  • Blog posts sobre dores de recrutadores                       │
│  • Podcast "Recrutar é..."                                       │
│  • Conteúdo em LinkedIn/Instagram                               │
│                    ↓                                             │
│  INTERESSE                                                       │
│  • Landing page "Terapia de Grupo"                              │
│  • Formulário de inscrição (dados de lead)                      │
│  • Curadoria: perfil profissional validado                      │
│                    ↓                                             │
│  COMUNIDADE (NURTURING)                                          │
│  • Grupo WhatsApp/Discord exclusivo                             │
│  • Eventos mensais (webinars, AMAs)                             │
│  • Conteúdo exclusivo (templates, checklists)                   │
│  • Networking entre recrutadores                                 │
│                    ↓                                             │
│  QUALIFICAÇÃO                                                    │
│  • Identificar dores específicas (alto volume, tech, etc.)      │
│  • Engajamento com conteúdo sobre LIA                           │
│  • Interesse declarado em demo                                   │
│                    ↓                                             │
│  CONVERSÃO                                                       │
│  • Demo personalizada da LIA                                    │
│  • Oferta especial para membros da comunidade                   │
│  • Onboarding prioritário                                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Métricas da Comunidade

| Métrica | Target Ano 1 | Target Ano 2 |
|---------|--------------|--------------|
| **Membros da comunidade** | 500 | 2.000 |
| **Taxa de engajamento** | 30% | 40% |
| **Leads qualificados/mês** | 20 | 80 |
| **Conversão comunidade→demo** | 15% | 20% |
| **Conversão demo→cliente** | 30% | 40% |

### Conteúdo e Eventos

| Tipo | Frequência | Objetivo |
|------|------------|----------|
| **Posts blog** | 2x/semana | SEO, awareness |
| **Podcast** | 1x/semana | Autoridade, engagement |
| **Webinar temático** | 1x/mês | Nurturing, leads |
| **AMA com especialistas** | 1x/mês | Comunidade, engagement |
| **Templates/ferramentas** | 2x/mês | Valor, leads |
| **Meetup presencial** | 1x/trimestre | Networking, brand |

### Gestão da Comunidade

| Papel | Responsabilidade |
|-------|-----------------|
| **Community Manager** | Moderação, engajamento diário, métricas |
| **Content Lead** | Produção de conteúdo, calendário editorial |
| **Sales Rep** | Identificação de leads, transição para comercial |

### ROI da Comunidade

```
Investimento mensal: R$ 15.000
  • Community Manager (1/2 FTE): R$ 5.000
  • Conteúdo (produção): R$ 5.000
  • Eventos/ferramentas: R$ 3.000
  • Ads (promoção): R$ 2.000

Retorno esperado (Ano 2):
  • 80 leads/mês × 20% conversão demo × 30% conversão cliente = 4.8 clientes/mês
  • Ticket médio: R$ 3.000/mês
  • Receita nova: R$ 14.400/mês
  • LTV médio (24 meses): R$ 72.000
  • Valor gerado: R$ 345.600/mês (LTV × novos clientes)

ROI: 2.300% (considerando LTV)
```

### Integração com Stack de Marketing

| Ferramenta | Função | Integração |
|------------|--------|------------|
| **HubSpot** | CRM e automação de marketing | Leads da comunidade → Pipeline |
| **Typeform** | Formulário de inscrição | Qualificação inicial |
| **WhatsApp Business** | Grupo da comunidade | Engajamento diário |
| **Calendly** | Agendamento de demos | Conversão de leads |
| **Loom** | Vídeos de conteúdo | Nurturing assíncrono |

### Dependências e Pré-requisitos

| Item | Status | Responsável |
|------|--------|-------------|
| Conta HubSpot configurada | 🔴 Pendente | Marketing |
| Formulário de inscrição | 🔴 Pendente | Marketing |
| Grupo WhatsApp/Discord | 🔴 Pendente | Community Manager |
| Calendário editorial (3 meses) | 🔴 Pendente | Content Lead |
| Templates de email/WhatsApp | 🔴 Pendente | Marketing |
| Dashboard de métricas | 🔴 Pendente | Ops |

### Cadência Operacional

| Atividade | Frequência | Volume/Evento |
|-----------|------------|---------------|
| Posts no grupo | Diário | 2-3 posts |
| Respostas/moderação | Contínuo | ~20 interações/dia |
| Webinars | Mensal | 50-100 participantes |
| AMAs com especialistas | Mensal | 30-50 participantes |
| Onboarding novos membros | Semanal | 10-20 novos |
| Relatório de métricas | Semanal | - |
| Review de leads qualificados | Semanal | 5-10 leads |

> ⚠️ **Nota:** Esta estratégia será implementada em paralelo com o desenvolvimento do produto. O início está previsto para quando houver MVP funcional para demonstrar aos leads gerados.

---

# Parte V: Inteligência Competitiva e Benchmarking

> **Fontes:** Esta seção é baseada em pesquisas de mercado realizadas em Novembro 2025:
> - Matriz Comparativa de Frameworks e Ferramentas (9 plataformas analisadas)
> - Análise de Stacks para Voice AI Própria
> - Análise de Custo-Benefício de Plataformas Voice AI
> - Análise de Infraestrutura Agentic (Beam vs Relevance vs Alternativas)
>
> Os dados refletem o estado do mercado na data da pesquisa e devem ser revisados periodicamente.

# 21. Panorama de Concorrentes Agentic AI

## 21.1 Matriz Comparativa (9 Plataformas)

Análise de 9 plataformas líderes de agentes de IA de recrutamento, identificando frameworks, ferramentas e arquiteturas.

| Plataforma | Framework | LLM | Especialização | Diferencial | CrewAI/LangGraph? |
|------------|-----------|-----|----------------|-------------|-------------------|
| **Tezi AI** | Custom (Calibration Loop) | GPT-4 | Sourcing | Autonomous learning | ❌ Custom |
| **DigaAI** | Custom (Conversational) | GPT-4/Claude | Interviewing | WhatsApp voice | ❌ Custom |
| **Gupy** | ML tradicional + LLM | GPT-4 | Screening | Semantic matching | ❌ ML tradicional |
| **InHire** | Custom (Automation) | GPT-4 | Full suite | Transcrição + Q&A | ❌ Custom |
| **SeekOut** | Provavelmente LangGraph | GPT-4 | Sourcing | Unified Intelligence | ✅ Provável |
| **Juicebox** | N/A (Search) | Embeddings | Search | BM25 + k-NN | ❌ Search engine |
| **Loxo** | Custom Fleet | GPT-4 | All-in-one | Self-Updating CRM | ⚠️ Possível CrewAI |
| **Beam AI** | LangGraph | GPT-4 | Automation | Agentic architecture | ✅ LangGraph |
| **Popp AI** | Custom (Integration) | GPT-4 | ATS integration | StackOne API | ❌ Custom |

## 21.2 Análise Detalhada por Concorrente

### Tezi AI (USA)

| Aspecto | Detalhe |
|---------|---------|
| **Framework** | Custom Calibration Loop |
| **LLM** | GPT-4 |
| **Arquitetura** | Single autonomous agent |
| **Stack** | Python, OpenAI API, Email/LinkedIn/ATS APIs |
| **Compliance** | SOC2, CCPA, NYC Local Law 144 |
| **Replicabilidade** | 12-16 semanas, $500-1,000/mês |

**Diferencial único:** Aprende com feedback do recruiter, melhora ao longo do tempo.

### DigaAI (Brasil)

| Aspecto | Detalhe |
|---------|---------|
| **Framework** | Custom Conversational AI |
| **LLM** | GPT-4 ou Claude |
| **Arquitetura** | WhatsApp-based interviewing |
| **Stack** | Python + Node.js, Twilio WhatsApp, Google STT/Whisper |
| **Capacidade** | 1,000 entrevistas/dia simultâneas |
| **Assertividade** | 94% |
| **Replicabilidade** | 2-3 meses, $450-11,500/mês |

**Diferencial único:** Entrevistas por áudio no WhatsApp.

### Gupy (Brasil)

| Aspecto | Detalhe |
|---------|---------|
| **Framework** | ML Tradicional + LLM (recente) |
| **LLM** | GPT-4 (adicionado recentemente) |
| **Arquitetura** | ATS com múltiplos AI agents |
| **Stack** | Python (ML) + Java/Node, Scikit-learn, TensorFlow, Elasticsearch |
| **Histórico** | 10 anos de dados |
| **Replicabilidade** | 12-18 meses, $270k dev, $7,000/mês infra |

**Diferencial único:** Semantic matching com histórico massivo de dados.

### InHire (Brasil)

| Aspecto | Detalhe |
|---------|---------|
| **Framework** | Custom Automation Suite |
| **LLM** | GPT-4 |
| **Arquitetura** | ATS + AI automation agents |
| **Stack** | Python + Node.js, Twilio WhatsApp, Google STT, Google Vision OCR |
| **Replicabilidade** | 8-10 meses, $230k dev, $7,000/mês infra |

**Diferencial único:** Transcrição + Q&A sobre entrevista (ninguém mais tem!).

### SeekOut (USA)

| Aspecto | Detalhe |
|---------|---------|
| **Framework** | Provavelmente LangGraph |
| **LLM** | GPT-4 |
| **Arquitetura** | Multi-agent + human-in-loop |
| **Stack** | Python, LangGraph (inferido), Temporal |
| **Replicabilidade** | 12-18 meses, $470k dev, $34,000/mês infra |

**Diferencial único:** Hybrid model (AI + human recruiters), Service (não só software).

### Loxo (USA)

| Aspecto | Detalhe |
|---------|---------|
| **Framework** | Custom Fleet (possível CrewAI) |
| **LLM** | GPT-4 |
| **Arquitetura** | All-in-one com múltiplos agents |
| **Database** | 800M+ profiles |
| **Replicabilidade** | 18-24 meses, $765k dev |

**Diferencial único:** Self-Updating CRM (ninguém mais tem).

### Beam AI (USA)

| Aspecto | Detalhe |
|---------|---------|
| **Framework** | LangGraph (confirmado) |
| **LLM** | GPT-4 |
| **Arquitetura** | Agentic architecture (pre-trained) |
| **Integrações** | 100+ pre-built |
| **Compliance** | ISO 27001, SOC II |
| **Replicabilidade** | 6 meses, $1,500-2,000/mês |

**Diferencial único:** Agents act (não apenas assist), enterprise-ready.

## 21.3 Insights Estratégicos

### Quem Usa o Quê?

| Categoria | Plataformas |
|-----------|-------------|
| ✅ **Confirmado LangGraph** | Beam AI |
| ⚠️ **Provavelmente LangGraph** | SeekOut |
| ⚠️ **Possivelmente CrewAI** | Loxo |
| ❌ **Custom/Outro** | Tezi, DigaAI, Gupy, InHire, Juicebox, Popp |

### Padrões Identificados

1. **Maioria NÃO usa CrewAI/LangGraph** - Desenvolvidos antes de 2023 ou workflows simples
2. **Todos usam GPT-4** - Estabilidade e qualidade superiores
3. **WhatsApp é diferencial no Brasil** - DigaAI e InHire lideram
4. **Transcrição + Q&A é único** - InHire, oportunidade de diferenciação
5. **Hybrid Model é futuro** - AI + Human (SeekOut)

### Ferramentas Mais Usadas

| Categoria | Ferramenta | Quem Usa |
|-----------|------------|----------|
| **LLM** | GPT-4 | Todos (exceto Juicebox) |
| **Agent Framework** | LangGraph | Beam AI, SeekOut |
| **Speech-to-Text** | Google STT/Whisper | DigaAI, InHire |
| **Search** | Elasticsearch/OpenSearch | Gupy, Juicebox |
| **WhatsApp** | Twilio API | DigaAI, InHire |
| **Integrations** | StackOne | Popp AI ($500/mês) |

---

# 22. Stacks Voice AI e Benchmark de Custos

## 22.1 Stack Best-of-Breed (Build)

Componentes para construir Voice AI própria:

```
┌─────────────────────────────────────────────────────────────────┐
│                    STACK VOICE AI BUILD                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  SPEECH-TO-TEXT (STT)                                           │
│  ├─ Deepgram Nova-2 ($0.0043/min) - Melhor accuracy             │
│  ├─ Google Speech-to-Text ($0.006/min) - Português BR           │
│  └─ Whisper (OpenAI) ($0.006/min) - Alternativa                 │
│                                                                  │
│  LLM (Conversação)                                              │
│  ├─ GPT-4 Turbo ($0.01/1K tokens) - Qualidade                   │
│  ├─ Claude 3.5 Sonnet ($0.003/1K) - Cost-effective              │
│  └─ Gemini 2.0 Flash ($0.00015/1K) - Ultra-low cost             │
│                                                                  │
│  TEXT-TO-SPEECH (TTS)                                           │
│  ├─ ElevenLabs ($0.30/1K chars) - Mais natural                  │
│  ├─ Google Cloud TTS ($0.016/1K) - Português BR                 │
│  └─ OpenAI TTS ($0.015/1K) - Qualidade alta                     │
│                                                                  │
│  TELEPHONY                                                       │
│  ├─ Twilio Voice ($0.0085/min) - Global                         │
│  └─ Vonage ($0.0070/min) - Alternativa                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 22.2 Plataformas Voice AI Prontas (Buy)

| Plataforma | Modelo | Preço | Latência | Vozes PT-BR |
|------------|--------|-------|----------|-------------|
| **Synthflow** | No-code | $29-450/mês | 800ms | ✅ 30+ |
| **Vapi** | API-first | $0.05/min | 500ms | ✅ ElevenLabs |
| **Bland AI** | Enterprise | $0.09/min | 400ms | ⚠️ Limited |
| **Retell AI** | Developer | $0.10-0.22/min | 650ms | ✅ Multi |
| **HeyMilo** | Recruiting-specific | Custom | 600ms | ✅ Native |

## 22.3 Comparativo de Custos (1.000 chamadas/mês, 10min cada)

| Abordagem | Custo Mensal | Setup | Manutenção |
|-----------|-------------|-------|------------|
| **Build (Best-of-Breed)** | $800-1,500 | 8-12 semanas | Alto |
| **Synthflow** | $99-450 | 1-2 dias | Baixo |
| **Vapi** | $500 | 1 semana | Médio |
| **HeyMilo** | Custom | 2 semanas | Baixo |

### Recomendação WeDOTalent

```
FASE 1 (MVP): Synthflow ou Vapi
  • Custo: $99-500/mês
  • Time to market: 1-2 semanas
  • Validar product-market fit

FASE 2 (Scale): Build own stack
  • Custo: $800-1,500/mês (mais controle)
  • Time: 8-12 semanas
  • Maior personalização
```

---

# 23. Infraestrutura Agentic e Orquestração

## 23.1 Plataformas de Infraestrutura

| Plataforma | Tipo | Preço Base | Ideal Para |
|------------|------|------------|------------|
| **LangGraph Cloud** | Managed | $0.01/step | Multi-agent complexo |
| **Relevance AI** | Low-code | $19-599/mês | Não-devs |
| **Beam AI** | Pre-built | Custom | Enterprise |
| **n8n** | Workflow | $20-220/mês | Automações simples |
| **CrewAI** | Framework | Open source | Hierárquico |

## 23.2 Matriz de Decisão

| Critério | LangGraph | CrewAI | Custom |
|----------|-----------|--------|--------|
| **Complexidade** | Alta | Média | Variável |
| **Controle** | Máximo | Alto | Total |
| **Observabilidade** | Excelente | Boa | Depende |
| **Curva aprendizado** | Íngreme | Moderada | Variável |
| **Custo inicial** | Baixo | Zero | Médio |
| **Custo escala** | Alto | Médio | Variável |

## 23.3 Custos Operacionais Projetados (36 meses)

> **Nota:** Esta seção mostra apenas custos operacionais (OPEX). Custos de desenvolvimento (CAPEX) são detalhados na Seção 24.

### Cenário: 1.000 conversas/mês

| Componente | Ano 1 | Ano 2 | Ano 3 | Total 36m |
|------------|-------|-------|-------|-----------|
| **LLM (GPT-4)** | $12,000 | $15,000 | $18,000 | $45,000 |
| **Infra (hosting)** | $6,000 | $8,000 | $10,000 | $24,000 |
| **Voice AI** | $6,000 | $8,000 | $12,000 | $26,000 |
| **Integrações** | $3,600 | $4,800 | $6,000 | $14,400 |
| **Total OPEX** | $27,600 | $35,800 | $46,000 | **$109,400** |

### Resumo OPEX vs CAPEX

| Categoria | 36 meses | Descrição |
|-----------|----------|-----------|
| **OPEX (operacional)** | $109,400 | LLM, hosting, voice, integrações |
| **CAPEX (desenvolvimento)** | Variável | Ver Seção 24 para cenários Build/Buy/Hybrid |

---

# 24. Decisão Estratégica Build vs Buy (36m)

> **Fonte:** Análise baseada em pesquisa de mercado (Nov 2025) comparando Tezi AI, DigaAI, Gupy, InHire, SeekOut, Juicebox, Loxo, Beam AI e Popp AI.

## 24.1 Análise TCO Detalhada

> **Nota:** Custos incluem CAPEX (desenvolvimento) + OPEX (operacional) para 36 meses. Base: dev sênior $5k/mês.

### Opção A: Full Build

| Item | Tipo | Cálculo | Custo |
|------|------|---------|-------|
| Desenvolvimento | CAPEX | 6 devs × $5k × 12m | $360,000 |
| Infraestrutura | OPEX | $2k/mês × 36m | $72,000 |
| LLM costs | OPEX | (da Seção 23.3) | $45,000 |
| Manutenção | OPEX | $2.5k/mês × 36m | $90,000 |
| **Total 36m** | | | **$567,000** |

### Opção B: Buy + Customize

| Item | Tipo | Cálculo | Custo |
|------|------|---------|-------|
| Plataforma (Relevance + Synthflow) | OPEX | ~$1k/mês × 36m | $36,000 |
| Customização | CAPEX | 2 devs × $5k × 6m | $60,000 |
| Integrações + Ajustes | CAPEX | 2 devs × 1m | $10,000 |
| LLM costs (adicional) | OPEX | Embutido na plataforma | $20,000 |
| Infraestrutura | OPEX | $1.5k/mês × 36m | $54,000 |
| **Total 36m** | | | **$180,000** |

### Opção C: Hybrid (Recomendado)

| Item | Tipo | Cálculo | Custo |
|------|------|---------|-------|
| Core agents (LangGraph) | CAPEX | 4 devs × $5k × 8m | $160,000 |
| Voice AI (Synthflow/Vapi) | OPEX | $500/mês × 36m | $18,000 |
| Integrações (StackOne) | OPEX | $500/mês × 36m | $18,000 |
| LLM costs | OPEX | (da Seção 23.3) | $45,000 |
| Infraestrutura | OPEX | $1k/mês × 36m | $36,000 |
| Manutenção | OPEX | $1k/mês × 24m (pós-build) | $24,000 |
| **Total 36m** | | | **$301,000** |

### Comparativo Resumido

| Cenário | CAPEX | OPEX (36m) | Total | Break-even |
|---------|-------|------------|-------|------------|
| **Full Build** | $360,000 | $207,000 | $567,000 | 24+ meses |
| **Buy + Customize** | $70,000 | $110,000 | $180,000 | 6 meses |
| **Hybrid** | $160,000 | $141,000 | $301,000 | 12 meses |

## 24.2 Critérios de Decisão

| Critério | Build | Buy | Hybrid |
|----------|-------|-----|--------|
| **Time to market** | 12-18 meses | 2-4 meses | 6-8 meses |
| **Controle** | Total | Limitado | Alto |
| **Diferenciação** | Máxima | Baixa | Alta |
| **Custo inicial** | Alto | Baixo | Médio |
| **Custo longo prazo** | Médio | Alto | Médio |
| **Risco técnico** | Alto | Baixo | Médio |

## 24.3 Roadmap Híbrido Recomendado

```
┌─────────────────────────────────────────────────────────────────┐
│                    ROADMAP HÍBRIDO (24 MESES)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Q1-Q2: FUNDAÇÃO                                                │
│  ├─ Voice AI: Synthflow (buy)                                   │
│  ├─ Integrações: StackOne (buy)                                 │
│  └─ Core: Intent Router + Job Intake (build)                    │
│                                                                  │
│  Q3-Q4: EXPANSÃO                                                │
│  ├─ Sourcing Agent (build, LangGraph)                           │
│  ├─ Screening Agent (build, LangGraph)                          │
│  └─ Voice AI: Migrar para stack própria                         │
│                                                                  │
│  Q5-Q6: MATURIDADE                                              │
│  ├─ Scheduling Agent (build)                                    │
│  ├─ Communication Agent (build)                                 │
│  └─ Orquestrador completo (build)                               │
│                                                                  │
│  Q7-Q8: OTIMIZAÇÃO                                              │
│  ├─ Substituir StackOne por integrações próprias               │
│  ├─ Self-Updating CRM (diferencial Loxo)                        │
│  └─ Calibration Loop (diferencial Tezi)                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

# 25. Guia Agentic vs Conversacional

## 25.1 Quando Usar Cada Abordagem

| Caso de Uso | Abordagem | Razão |
|-------------|-----------|-------|
| Chat simples | Conversacional | Baixa complexidade |
| FAQ/Suporte | Conversacional + RAG | Conhecimento estático |
| Criação de vagas | Agentic (1 agent) | Workflow estruturado |
| Busca candidatos | Agentic (1 agent) | Múltiplas fontes |
| Agendamento | Agentic (1 agent) | Integrações calendar |
| Pipeline completo | Multi-agent | Orquestração complexa |
| Screening + Análise | Multi-agent | Especialização |

## 25.2 Arquiteturas de Referência

### Conversacional Simples

```
User → LLM → Response
         ↓
       Memory
```

### Conversacional + RAG

```
User → Retriever → Context → LLM → Response
                      ↑
                  Vector DB
```

### Single Agent

```
User → Intent Router → Agent → Tools → Response
                          ↓
                       LLM + Memory
```

### Multi-Agent Orquestrado

```
User → Orchestrator → [Agent 1, Agent 2, Agent 3] → Aggregator → Response
            ↓                    ↓
      Policy Engine        Shared State
```

## 25.3 Critérios de Migração

### De Conversacional para Agentic

| Sinal | Ação |
|-------|------|
| Usuário pede ações (não só informação) | Adicionar tools |
| Múltiplos passos necessários | Criar workflow |
| Integrações externas | Adicionar connectors |
| Decisões complexas | Adicionar policy engine |

### De Single Agent para Multi-Agent

| Sinal | Ação |
|-------|------|
| Agent > 15 tools | Dividir em especialistas |
| Prompts > 4000 tokens | Separar contextos |
| Latência > 10s | Paralelizar agents |
| Erros frequentes | Isolar responsabilidades |

## 25.4 Stack Recomendada WeDOTalent

```
┌─────────────────────────────────────────────────────────────────┐
│                    STACK RECOMENDADA                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  FRAMEWORK: LangGraph                                           │
│  ├─ Multi-agent orchestration                                  │
│  ├─ State management                                            │
│  ├─ Human-in-loop                                               │
│  └─ Observability (LangSmith)                                   │
│                                                                  │
│  LLM: Claude Sonnet 4 (primary) + GPT-4 Turbo (fallback)       │
│  ├─ Anthropic: Melhor para português BR                        │
│  └─ OpenAI: Fallback e compatibilidade                          │
│                                                                  │
│  VOICE: Synthflow (MVP) → Build (Scale)                         │
│  ├─ Synthflow: $99/mês, setup 1 dia                             │
│  └─ Build: Deepgram + ElevenLabs + Twilio                       │
│                                                                  │
│  INTEGRAÇÕES: StackOne ($500/mês)                               │
│  ├─ 40+ ATSs (Gupy, Pandapé, Greenhouse)                        │
│  └─ Unified API                                                  │
│                                                                  │
│  OBSERVABILITY: LangSmith + Sentry                              │
│  ├─ LangSmith: LLM traces                                       │
│  └─ Sentry: Application errors                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

# Parte VI: Governança, Riscos e Compliance

# 26. Gestão de Riscos

## 26.1 Matriz de Riscos

### Riscos Técnicos

| Risco | Probabilidade | Impacto | Score | Mitigação |
|-------|---------------|---------|-------|-----------|
| **API OpenAI/Anthropic indisponível** | Média | Alto | 🔴 | Fallback multi-provider (Claude → GPT → Gemini) |
| **Pearch AI descontinuado/preços sobem** | Baixa | Alto | 🟡 | Manter banco local robusto, avaliar alternativas (SeekOut API) |
| **Latência alta em horários de pico** | Média | Médio | 🟡 | Auto-scaling, cache de respostas comuns, rate limiting |
| **Falha de transcrição voice** | Média | Alto | 🔴 | Fallback Deepgram → Google STT → Whisper |
| **Dados corrompidos em migração** | Baixa | Crítico | 🔴 | Backups incrementais, dry-run obrigatório, rollback automatizado |
| **Integração ATS quebra após update** | Alta | Médio | 🟡 | Versionamento de API, testes de regressão, StackOne como abstração |
| **LangGraph breaking changes** | Média | Médio | 🟡 | Pinning de versões, testes automatizados, equipe acompanha releases |

### Riscos de Negócio

| Risco | Probabilidade | Impacto | Score | Mitigação |
|-------|---------------|---------|-------|-----------|
| **Concorrente lança feature similar** | Alta | Médio | 🟡 | Diferenciação por WSI proprietário + contexto Brasil |
| **Adoção lenta por recrutadores** | Média | Alto | 🔴 | Onboarding guiado, "Terapia de Recrutadores", casos de uso prontos |
| **Churn alto nos primeiros 3 meses** | Média | Alto | 🔴 | CSM dedicado, health checks semanais, quick wins visíveis |
| **Custo LLM maior que projetado** | Média | Médio | 🟡 | Monitoramento diário, cache agressivo, modelos menores para tarefas simples |
| **Dependência de único cliente grande** | Baixa | Alto | 🟡 | Diversificação de base, pricing SMB atrativo |

### Riscos Regulatórios

| Risco | Probabilidade | Impacto | Score | Mitigação |
|-------|---------------|---------|-------|-----------|
| **Violação LGPD** | Baixa | Crítico | 🔴 | DPO designado, consentimento explícito, anonimização, auditoria |
| **Discriminação algorítmica** | Média | Crítico | 🔴 | Auditoria de viés trimestral, explicabilidade de scores, human-in-loop |
| **Gravação de voz sem consentimento** | Baixa | Crítico | 🔴 | Opt-in obrigatório com gravação, termo lido pela IA |
| **Vazamento de dados de candidatos** | Baixa | Crítico | 🔴 | Criptografia em repouso/trânsito, SOC2 roadmap, pentest anual |

## 26.2 Plano de Contingência

### Cenário: API LLM Principal Indisponível

```
┌─────────────────────────────────────────────────────────────────┐
│                    FALLBACK CHAIN (< 30s)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Claude Sonnet 4 (primary)                                   │
│     ↓ timeout 10s ou erro 5xx                                   │
│  2. GPT-4 Turbo (secondary)                                     │
│     ↓ timeout 10s ou erro 5xx                                   │
│  3. Gemini Pro (tertiary)                                       │
│     ↓ timeout 10s ou erro 5xx                                   │
│  4. Resposta degradada: "Estou com dificuldades técnicas..."    │
│     + Notificação Slack/PagerDuty                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Cenário: Pico de Uso (>10x normal)

| Ação | Trigger | Resultado |
|------|---------|-----------|
| Auto-scale horizontal | CPU > 70% | +2 pods a cada 30s |
| Rate limiting | >100 req/s por cliente | 429 com retry-after |
| Fila de processamento | Voice screening | Jobs processados assíncronos |
| Modo degradado | Todos LLMs lentos | Respostas em cache + "refinando..." |

### Cenário: Breach de Dados

| Etapa | Tempo | Responsável | Ação |
|-------|-------|-------------|------|
| Detecção | T+0 | Sistema | Alerta automatizado |
| Contenção | T+1h | DevOps | Isolar sistemas afetados |
| Avaliação | T+4h | DPO + Jurídico | Escopo do vazamento |
| Notificação | T+24h | DPO | ANPD + afetados (se aplicável LGPD) |
| Remediação | T+48h | Equipe | Patch + post-mortem |
| Comunicação | T+72h | Marketing | Transparência com clientes |

---

# 27. SLA e Compliance

## 27.1 Service Level Agreements

### Disponibilidade

| Componente | SLA | Medição | Penalidade |
|------------|-----|---------|------------|
| **Plataforma Web** | 99.5% uptime | Mensal | 10% crédito se < 99% |
| **API LIA Chat** | 99.0% uptime | Mensal | 15% crédito se < 98% |
| **Voice Screening** | 98.0% uptime | Mensal | 20% crédito se < 95% |
| **Integrações ATS** | 97.0% uptime | Mensal | Melhor esforço |

### Performance

| Métrica | Target | P95 | P99 |
|---------|--------|-----|-----|
| **Chat response time** | < 3s | < 5s | < 10s |
| **Busca candidatos** | < 5s | < 8s | < 15s |
| **Voice call setup** | < 2s | < 3s | < 5s |
| **Transcrição** | < 30s | < 60s | < 120s |
| **Geração de relatório** | < 10s | < 20s | < 45s |

### Suporte

| Plano | Canais | Tempo Resposta | Horário |
|-------|--------|----------------|---------|
| **Starter** | Email, Chat | 24h úteis | Seg-Sex 9-18h |
| **Professional** | Email, Chat, WhatsApp | 4h úteis | Seg-Sex 8-20h |
| **Enterprise** | Todos + Telefone + Slack | 1h (crítico) | 24/7 |

## 27.2 Compliance LGPD

### Bases Legais Utilizadas

| Dado | Base Legal | Justificativa |
|------|------------|---------------|
| **Nome, email, telefone** | Consentimento | Candidato aceita termos ao se cadastrar |
| **CV, experiências** | Execução contratual | Necessário para processo seletivo |
| **Gravação de voz** | Consentimento explícito | Opt-in específico antes da chamada |
| **Scores e análises** | Legítimo interesse | Otimização do processo (com opt-out) |
| **Dados sensíveis (PCD, gênero)** | Consentimento específico | Apenas se candidato informar voluntariamente |

### Direitos do Titular (Candidato)

| Direito | Implementação | SLA |
|---------|---------------|-----|
| **Acesso** | Portal de privacidade + export JSON/PDF | 5 dias úteis |
| **Correção** | Edição in-app ou via suporte | 2 dias úteis |
| **Exclusão** | "Esqueça-me" no portal ou via DPO | 10 dias úteis |
| **Portabilidade** | Export estruturado (JSON + CSV) | 5 dias úteis |
| **Oposição** | Opt-out de scoring automatizado | Imediato |
| **Revogação** | Retirar consentimentos específicos | Imediato |

### Medidas Técnicas

| Medida | Status | Detalhes |
|--------|--------|----------|
| **Criptografia em trânsito** | ✅ Implementado | TLS 1.3 obrigatório |
| **Criptografia em repouso** | ✅ Implementado | AES-256 (PostgreSQL + S3) |
| **Pseudonimização** | 🔄 Em implementação | IDs hasheados para analytics |
| **Minimização** | ✅ Implementado | Coleta apenas dados necessários |
| **Retenção definida** | ✅ Implementado | 24 meses + política de expurgo |
| **Logs de acesso** | ✅ Implementado | Auditoria completa de quem acessou |
| **Backup criptografado** | ✅ Implementado | Daily, 30 dias retenção |

### Roadmap Certificações

| Certificação | Timeline | Investimento | Prioridade |
|--------------|----------|--------------|------------|
| **SOC 2 Type I** | Q3 2026 | $30-50k | Alta |
| **SOC 2 Type II** | Q1 2027 | $50-80k | Alta |
| **ISO 27001** | Q3 2027 | $40-60k | Média |
| **GDPR Ready** | Q4 2026 | Interno | Média (expansão EU) |

## 27.3 Governança de IA

### Princípios Éticos

1. **Transparência**: Candidatos sabem que interagem com IA
2. **Explicabilidade**: Scores justificados com evidências textuais
3. **Não-discriminação**: Auditoria trimestral de viés por gênero, idade, etnia
4. **Human-in-the-loop**: Decisões finais sempre por humanos
5. **Opt-out**: Candidato pode recusar triagem automatizada

### Auditoria de Viés

| Métrica | Frequência | Threshold | Ação se Exceder |
|---------|------------|-----------|-----------------|
| **Demographic parity** | Trimestral | ±10% | Revisão de prompts + dados |
| **Equal opportunity** | Trimestral | ±10% | Rebalanceamento de exemplos |
| **Calibration** | Mensal | ±5% | Ajuste de thresholds |

### Documentação Obrigatória

- Relatório de Impacto (RIPD) - LGPD Art. 38
- Registro de Operações de Tratamento (ROT)
- Política de Privacidade pública
- Termos de Uso com cláusulas de IA
- Contrato de Processamento de Dados (DPA) para clientes

---

# 28. Dependências Externas e Contingências

## 28.1 Mapa de Dependências Críticas

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEPENDÊNCIAS EXTERNAS                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CRÍTICAS (sistema para sem elas):                              │
│  ├─ Anthropic API (Claude) ────────── LLM principal             │
│  ├─ PostgreSQL (Neon) ─────────────── Persistência              │
│  └─ Vercel/Railway ────────────────── Hosting                   │
│                                                                  │
│  ALTAS (degradação significativa):                              │
│  ├─ OpenAI API (fallback) ─────────── LLM secundário            │
│  ├─ Pearch AI ─────────────────────── Sourcing externo          │
│  ├─ OpenMic.ai ────────────────────── Chamadas de voz           │
│  └─ Microsoft Graph ───────────────── Calendário                │
│                                                                  │
│  MÉDIAS (funcionalidade reduzida):                              │
│  ├─ Deepgram ──────────────────────── STT                       │
│  ├─ Google Cloud (TTS, Gemini) ────── Voz + fallback LLM        │
│  ├─ StackOne ──────────────────────── Integrações ATS           │
│  └─ LangSmith ─────────────────────── Observabilidade           │
│                                                                  │
│  BAIXAS (substituíveis rapidamente):                            │
│  ├─ Resend/SendGrid ───────────────── Email                     │
│  ├─ Twilio ────────────────────────── WhatsApp                  │
│  └─ Unsplash ──────────────────────── Imagens                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 28.2 Análise de Dependências

### APIs de LLM

| Provider | Uso | Custo/1M tokens | Risco | Alternativa |
|----------|-----|-----------------|-------|-------------|
| **Anthropic (Claude)** | Primary | $3-15 | Médio | OpenAI |
| **OpenAI (GPT)** | Fallback | $2.50-10 | Baixo | Anthropic |
| **Google (Gemini)** | Tertiary | $0.50-2 | Baixo | Groq |
| **Groq** | Speed-critical | $0.05-0.27 | Médio | OpenAI |

**Mitigação**: Multi-provider configurado, switch automático em < 30s.

### APIs de Voz

| Provider | Uso | Custo | Risco | Alternativa |
|----------|-----|-------|-------|-------------|
| **OpenMic.ai** | Chamadas | $0.12/min | Alto | Vapi, Bland |
| **Deepgram** | STT | $0.0043/min | Baixo | Google STT |
| **ElevenLabs** | TTS (futuro) | $0.18/1k chars | Médio | Google TTS |

**Mitigação**: Deepgram tem 99.9% uptime. OpenMic é risco por ser startup - manter Vapi como backup contratado.

### Sourcing

| Provider | Uso | Custo | Risco | Alternativa |
|----------|-----|-------|-------|-------------|
| **Pearch AI** | Busca externa | ~$0.50/search | Alto | SeekOut API, Apollo |
| **LinkedIn (futuro)** | Enriquecimento | Premium | Médio | Clearbit |

**Mitigação**: Two-Tier Search prioriza banco local. Se Pearch sair, degradação graceful para busca interna only.

### Infraestrutura

| Provider | Uso | Custo/mês | Risco | Alternativa |
|----------|-----|-----------|-------|-------------|
| **Neon (PostgreSQL)** | Database | $19-69 | Baixo | Supabase, PlanetScale |
| **Vercel** | Frontend | $20-150 | Baixo | Railway, Render |
| **Railway** | Backend | $5-50 | Baixo | Render, Fly.io |
| **AWS S3** | Storage | ~$5 | Muito baixo | Cloudflare R2 |

**Mitigação**: Infra é comoditizada, migração em < 1 semana para qualquer alternativa.

## 28.3 Matriz de Contingência

| Dependência | Downtime Tolerável | Ação Automática | Ação Manual |
|-------------|-------------------|-----------------|-------------|
| **Claude API** | 0 | Switch para GPT-4 | - |
| **GPT-4 API** | 30s | Switch para Gemini | - |
| **PostgreSQL** | 0 | Failover Neon automático | Restore backup |
| **Pearch AI** | 5min | Modo "banco local only" | Ativar SeekOut |
| **OpenMic.ai** | 1h | Fila de retry | Ativar Vapi |
| **Deepgram** | 30s | Switch Google STT | - |
| **Microsoft Graph** | 1h | Fila de agendamentos | Email manual |
| **LangSmith** | 24h | Logs locais | - |

## 28.4 Custos de Contingência Reservados

| Categoria | Reserva Mensal | Uso |
|-----------|----------------|-----|
| **LLM burst** | $500 | Picos inesperados |
| **Backup providers** | $200 | Manter contas ativas |
| **Incident response** | $300 | Overtime, ferramentas |
| **Total** | **$1,000/mês** | ~10% do OPEX |

---

# 29. Validação Comparativa: Arquitetura de Agentes WeDOTalent vs Mercado

> **Objetivo:** Comparar nossa arquitetura de 6 agentes especializados com as 9 plataformas analisadas e validar se a estrutura está adequada.

## 29.1 Nossa Arquitetura (6 Agentes)

```
┌─────────────────────────────────────────────────────────────────┐
│                    WEDOTALENT - 6 AGENTES                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │ JOB INTAKE  │───▶│  SOURCING   │───▶│  SCREENING  │         │
│  │   Agent     │    │   Agent     │    │   Agent     │         │
│  │             │    │             │    │    (WSI)    │         │
│  │ Parse JD    │    │ Two-Tier    │    │ Voice calls │         │
│  │ Rubric gen  │    │ Local+Pearch│    │ STAR method │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│         │                                     │                 │
│         ▼                                     ▼                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │ EVALUATION  │◀───│ SCHEDULING  │◀───│COMMUNICATION│         │
│  │   Agent     │    │   Agent     │    │   Agent     │         │
│  │             │    │             │    │             │         │
│  │ LIA Score   │    │ MS Graph    │    │ Omnichannel │         │
│  │ Big Five    │    │ Calendar    │    │ WhatsApp    │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              ORCHESTRATOR (Intent Router)                  │ │
│  │  Claude Sonnet 4 + Policy Engine + State Manager          │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 29.2 Comparação com Concorrentes

### Matriz de Agentes por Plataforma

| Plataforma | Nº Agentes | Arquitetura | Framework | Foco Principal |
|------------|------------|-------------|-----------|----------------|
| **WeDOTalent** | 6 | Multi-agent orquestrado | LangGraph | Full-funnel + WSI |
| **Tezi AI** | 1 | Single agent | Custom | Sourcing autônomo |
| **DigaAI** | 1-2 | Conversational | Custom | Voice interviewing |
| **Gupy** | 3-4 | ML tradicional | Custom | ATS + screening |
| **InHire** | 2-3 | Automation | Custom | Transcrição + Q&A |
| **SeekOut** | 4-5 | Multi-agent | LangGraph? | Sourcing + AI service |
| **Juicebox** | 0 | Search engine | N/A | Apenas busca |
| **Loxo** | 5-6 | Fleet of agents | CrewAI? | All-in-one ATS |
| **Beam AI** | 3-4 | Agentic | LangGraph | Pre-built templates |
| **Popp AI** | 2-3 | Integration | Custom | ATS sync |

### Mapeamento Funcional

| Função | WeDOTalent | Tezi | DigaAI | Gupy | SeekOut | Loxo | Beam |
|--------|------------|------|--------|------|---------|------|------|
| **Job Creation** | ✅ Job Intake | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Sourcing** | ✅ Sourcing | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ |
| **Voice Screening** | ✅ Screening (WSI) | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Evaluation/Scoring** | ✅ Evaluation | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Scheduling** | ✅ Scheduling | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Communication** | ✅ Communication | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Transcrição + Q&A** | ✅ (via WSI) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

## 29.3 Análise de Gaps e Diferenciais

### ✅ O que WeDOTalent TEM que poucos têm

| Diferencial | WeDOTalent | Concorrentes | Vantagem Competitiva |
|-------------|------------|--------------|----------------------|
| **WSI (Wedo Screening Interview)** | ✅ Único | Apenas DigaAI (Brasil) | Metodologia proprietária STAR+Big Five |
| **Two-Tier Search** | ✅ Local + Pearch | Apenas Loxo (800M) | Economia de créditos + fallback |
| **LangGraph Orquestrador** | ✅ Planejado | Beam, SeekOut (provável) | State management + human-in-loop |
| **WhatsApp-first** | ✅ Brazil | DigaAI, InHire | Mercado brasileiro |
| **Transcrição + Q&A** | ✅ Embutido | Apenas InHire | Diferencial único expandido |

### ⚠️ O que WeDOTalent NÃO TEM (gaps a considerar)

| Gap | Concorrente | Prioridade | Recomendação |
|-----|-------------|------------|--------------|
| **Calibration Loop autônomo** | Tezi AI | Média | Implementar feedback loop em fase 2 |
| **800M+ profiles database** | Loxo, Juicebox | Baixa | Pearch AI cobre isso |
| **Self-updating CRM** | Loxo (único) | Baixa | Não essencial para MVP |
| **100+ integrações prontas** | Beam AI | Média | StackOne cobre 40+ ATSs |
| **AI + Human service** | SeekOut | Alta | Considerar modelo híbrido |

### 🔴 Riscos Identificados

| Risco | Análise | Mitigação |
|-------|---------|-----------|
| **Over-engineering** | 6 agentes pode ser complexo demais para MVP | Começar com 3-4 core agents |
| **Custo de orquestração** | LangGraph Cloud = $0.01/step | Monitorar e otimizar workflows |
| **Dependência de Pearch** | Startup pequena, pode pivotar/fechar | Two-Tier garante fallback para DB local |

## 29.4 Validação: Nossa Estrutura está Adequada?

### Critérios de Avaliação

| Critério | Nota | Justificativa |
|----------|------|---------------|
| **Cobertura funcional** | 9/10 | Cobre todo o funil de recrutamento |
| **Alinhamento com mercado** | 8/10 | Similar a SeekOut/Loxo (líderes) |
| **Diferenciação** | 9/10 | WSI + Two-Tier + WhatsApp = único |
| **Complexidade vs Valor** | 7/10 | 6 agentes pode ser excessivo para MVP |
| **Replicabilidade** | 8/10 | Stack conhecida (LangGraph, GPT-4) |
| **Custo-benefício** | 8/10 | Híbrido balanceia build vs buy |

**Score Médio: 8.2/10** ✅

### Conclusão

| Aspecto | Status | Recomendação |
|---------|--------|--------------|
| **Arquitetura geral** | ✅ Adequada | Manter 6 agentes como visão final |
| **MVP inicial** | ⚠️ Simplificar | Começar com 4 agentes core |
| **Framework** | ✅ Correto | LangGraph é escolha validada pelo mercado |
| **LLM** | ✅ Correto | Claude primary + GPT-4 fallback |
| **Diferenciação** | ✅ Forte | WSI é único no mercado |

## 29.5 Roadmap de Implementação Ajustado

### Fase 1: Core Agents (Semanas 1-8)

| Agente | Prioridade | Justificativa |
|--------|------------|---------------|
| **Intent Router** | P0 | Base do orquestrador |
| **Job Intake Agent** | P0 | Entrada do funil |
| **Sourcing Agent** | P0 | Core do produto |
| **Screening Agent (WSI)** | P0 | Diferencial único |

### Fase 2: Expansion (Semanas 9-14)

| Agente | Prioridade | Justificativa |
|--------|------------|---------------|
| **Evaluation Agent** | P1 | LIA Score completo |
| **Scheduling Agent** | P1 | Automação calendário |

### Fase 3: Full Suite (Semanas 15-20)

| Agente | Prioridade | Justificativa |
|--------|------------|---------------|
| **Communication Agent** | P2 | Omnichannel |
| **Calibration Loop** | P2 | Aprendizado contínuo (inspirado em Tezi) |

## 29.6 Comparativo de Stacks Técnicas

### LLM Primary

| Plataforma | LLM Primary | LLM Secondary | Justificativa |
|------------|-------------|---------------|---------------|
| **WeDOTalent** | Claude Sonnet 4 | GPT-4 Turbo | Melhor para português BR |
| **Tezi** | GPT-4 | - | Estabilidade |
| **DigaAI** | GPT-4/Claude | - | Flexibilidade |
| **SeekOut** | GPT-4 | - | Enterprise |
| **Beam AI** | GPT-4 | - | Padrão LangChain |

**Validação:** ✅ Nossa escolha de Claude como primary é diferenciada e alinhada com qualidade para português.

### Framework de Orquestração

| Plataforma | Framework | Maturidade | Observabilidade |
|------------|-----------|------------|-----------------|
| **WeDOTalent** | LangGraph | Alta | LangSmith |
| **SeekOut** | LangGraph (provável) | Alta | Custom |
| **Beam AI** | LangGraph | Alta | Built-in |
| **Loxo** | CrewAI (possível) | Média | Custom |
| **Outros** | Custom | Variável | Ad-hoc |

**Validação:** ✅ LangGraph é a escolha certa para multi-agent complexo.

### Voice AI

| Plataforma | Voice Stack | Diferencial |
|------------|-------------|-------------|
| **WeDOTalent** | OpenMic + Deepgram + Claude | WSI metodologia |
| **DigaAI** | Custom + WhatsApp | Volume (1000/dia) |
| **InHire** | Google STT + GPT-4 | Transcrição + Q&A |
| **Outros** | N/A | Sem voice |

**Validação:** ✅ Nossa stack de voice é competitiva e a WSI adiciona diferenciação metodológica.

## 29.7 Decisão Final

```
┌─────────────────────────────────────────────────────────────────┐
│                    DECISÃO: ARQUITETURA VALIDADA ✅             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PONTOS FORTES:                                                 │
│  ✅ 6 agentes cobre todo o funil (igual SeekOut/Loxo)           │
│  ✅ LangGraph = escolha validada pelo mercado                   │
│  ✅ WSI = diferencial único no mercado                          │
│  ✅ Two-Tier Search = economia + resiliência                    │
│  ✅ Claude primary = qualidade português BR                     │
│                                                                  │
│  AJUSTES RECOMENDADOS:                                          │
│  ⚠️ MVP com 4 agentes (não 6) para reduzir complexidade        │
│  ⚠️ Adicionar Calibration Loop (inspirado em Tezi)             │
│  ⚠️ Considerar modelo híbrido AI+Human (inspirado em SeekOut)  │
│                                                                  │
│  RISCOS MITIGADOS:                                              │
│  🛡️ Fallback multi-LLM (Claude → GPT-4 → Gemini)               │
│  🛡️ Two-Tier Search (local → Pearch)                           │
│  🛡️ StackOne para integrações (não reinventar)                 │
│                                                                  │
│  VEREDICTO: Estrutura está ADEQUADA para o mercado              │
│             Executar com ajustes de priorização MVP             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 29.8 Análise Técnica Detalhada por Plataforma

> **Fonte:** Matriz Comparativa de Frameworks e Ferramentas - Análise de 9 plataformas líderes.

### 29.8.1 Matriz Comparativa de Frameworks

| Plataforma | Framework de Agentes | LLM | Especialização | Diferencial Técnico | Usa CrewAI/LangGraph? |
|------------|---------------------|-----|----------------|--------------------|-----------------------|
| **Tezi AI** | Custom (Calibration Loop) | GPT-4 | Sourcing | Autonomous learning | ❌ Custom |
| **DigaAI** | Custom (Conversational) | GPT-4/Claude | Interviewing | WhatsApp voice | ❌ Custom |
| **Gupy** | Custom (ML tradicional) | GPT-4 (recente) | Screening | Semantic matching | ❌ ML tradicional |
| **InHire** | Custom (Automation) | GPT-4 | Full suite | Transcrição + Q&A | ❌ Custom |
| **SeekOut** | Provavelmente LangGraph | GPT-4 | Sourcing | Unified Intelligence | ✅ Provável LangGraph |
| **Juicebox** | N/A (Search, não agents) | Embeddings | Search | Hybrid BM25 + k-NN | ❌ Search engine |
| **Loxo** | Custom (Fleet) | GPT-4 | All-in-one | Self-Updating CRM | ⚠️ Possível CrewAI |
| **Beam AI** | LangGraph | GPT-4 | Automation | Agentic architecture | ✅ LangGraph |
| **Popp AI** | Custom (Integration) | GPT-4 | ATS integration | StackOne API | ❌ Custom |

### 29.8.2 Análise Individual das Plataformas

#### Tezi AI (USA)
```
Framework: Custom Calibration Loop
LLM: GPT-4
Arquitetura: Single autonomous agent
```

| Componente | Tecnologia |
|------------|------------|
| Backend | Python |
| LLM | OpenAI GPT-4 API |
| Calibration | Feedback loop (recruiter validates) |
| Integrations | Email, LinkedIn, ATS APIs |
| Compliance | SOC2, CCPA, NYC Local Law 144 |

**Por que NÃO usa CrewAI/LangGraph:**
- Desenvolvido antes de 2023 (frameworks são de 2023)
- Single agent (não multi-agent)
- Focus em calibration (não orchestration)

**Replicabilidade:** ✅ 12-16 semanas, $500-1,000/mês

---

#### DigaAI (Brasil)
```
Framework: Custom Conversational AI
LLM: GPT-4 ou Claude
Arquitetura: WhatsApp-based interviewing agent
```

| Componente | Tecnologia |
|------------|------------|
| Backend | Python + Node.js |
| WhatsApp | Twilio WhatsApp API |
| Speech-to-Text | Google Speech-to-Text ou Whisper |
| LLM | GPT-4 para análise |
| Conversational | State machine (custom) |

**Por que NÃO usa CrewAI/LangGraph:**
- Conversational AI (não agentic workflow)
- Real-time (não batch)
- WhatsApp-specific (não web-based)

**Diferencial:** 1.000 entrevistas/dia simultâneas, 94% assertividade

**Replicabilidade:** ✅ 2-3 meses, $450-11,500/mês (depende da escala)

---

#### Gupy (Brasil)
```
Framework: ML Tradicional + LLM (recente)
LLM: GPT-4 (adicionado recentemente)
Arquitetura: ATS com múltiplos AI agents
```

| Componente | Tecnologia |
|------------|------------|
| Backend | Python (ML) + Java/Node (ATS) |
| ML | Scikit-learn, TensorFlow/PyTorch |
| LLM | GPT-4 API (recente) |
| Search | Elasticsearch |
| NLP | Transformers (Hugging Face) |

**Por que NÃO usa CrewAI/LangGraph:**
- Desenvolvido desde 2015 (muito antes dos frameworks)
- ATS tradicional (não agentic)
- Screening/ranking (não workflow)

**Diferencial:** 10 anos de dados históricos, semantic matching

**Replicabilidade:** ⚠️ 12-18 meses, $270k dev, $7,000/mês infra

---

#### InHire (Brasil)
```
Framework: Custom Automation Suite
LLM: GPT-4
Arquitetura: ATS + AI automation agents
```

| Componente | Tecnologia |
|------------|------------|
| Backend | Python + Node.js |
| WhatsApp | Twilio WhatsApp API |
| Speech-to-Text | Google Speech-to-Text ou Whisper |
| LLM | GPT-4 para Q&A e pareceres |
| OCR | Google Vision API |

**Por que NÃO usa CrewAI/LangGraph:**
- Automações simples (não workflow complexo)
- Focus em APIs (não orchestration)

**Diferencial ÚNICO:** Transcrição + Q&A sobre entrevista (ninguém mais tem!)

**Replicabilidade:** ✅ 8-10 meses, $230k dev, $7,000/mês infra

---

#### SeekOut (USA)
```
Framework: Provavelmente LangGraph ⭐
LLM: GPT-4
Arquitetura: Multi-agent system + human-in-loop
```

| Componente | Tecnologia |
|------------|------------|
| Backend | Python |
| Agent Framework | LangGraph (inferido) |
| LLM | OpenAI GPT-4 |
| Data | Unified Intelligence Layer (custom) |
| Orchestration | Workflow engine (Temporal ou custom) |

**Por que PROVAVELMENTE usa LangGraph:**
- Usa termo "Agentic AI" (LangChain terminology)
- Múltiplos agents especializados (Rubric, Finder, Outreach)
- Workflow complexo (sequencial + paralelo)
- Human-in-loop (checkpoints)
- Desenvolvido recentemente (2024-2025)

**Diferencial:** Hybrid model (AI + human recruiters), Service (não só software)

**Replicabilidade:** ⚠️ Complexo, 12-18 meses, $470k dev, $34,000/mês infra

---

#### Juicebox (USA)
```
Framework: N/A (Search engine, não agents)
LLM: Embeddings (não GPT-4)
Arquitetura: Hybrid search (BM25 + k-NN)
```

| Componente | Tecnologia |
|------------|------------|
| Backend | Python |
| Search | AWS OpenSearch |
| Hybrid Search | BM25 (keyword) + k-NN (semantic) |
| Embeddings | Custom ou OpenAI |
| RAG | Retrieval-Augmented Generation |

**Por que NÃO usa CrewAI/LangGraph:**
- Não é agentic (é search)
- Focus em retrieval (não workflow)

**Diferencial:** 800M+ profiles, 250ms latency, 0.9+ recall

**Replicabilidade:** ✅ 8-12 semanas, $1,100-2,600/mês

---

#### Loxo (USA)
```
Framework: Custom Fleet of Agents (possível CrewAI)
LLM: GPT-4
Arquitetura: All-in-one platform com múltiplos agents
```

| Componente | Tecnologia |
|------------|------------|
| Backend | Python + Node.js |
| Agent Framework | Possível CrewAI ou custom |
| LLM | GPT-4 |
| Database | 800M+ profiles (custom) |
| CRM | Self-Updating (único) |

**Por que POSSIVELMENTE usa CrewAI:**
- "Fleet of agents" (CrewAI terminology)
- Múltiplos agents especializados
- Workflow hierárquico (Manager → Specialists)

**Diferencial ÚNICO:** Self-Updating CRM (ninguém mais tem)

**Replicabilidade:** ⚠️ Muito complexo, 18-24 meses, $765k dev

---

#### Beam AI (USA)
```
Framework: LangGraph ⭐ (CONFIRMADO)
LLM: GPT-4
Arquitetura: Agentic architecture (pre-trained agents)
```

| Componente | Tecnologia |
|------------|------------|
| Backend | Python |
| Agent Framework | LangGraph (confirmado) |
| LLM | OpenAI GPT-4 |
| Integrations | 100+ pre-built |
| Security | ISO 27001, SOC II |

**Por que USA LangGraph:**
- Documentação menciona "agentic architecture"
- LangChain ecosystem
- Pre-trained agents (LangGraph feature)

**Diferencial:** Agents act (não apenas assist), 100+ integrations prontas

**Replicabilidade:** ✅ 6 meses, $1,500-2,000/mês

---

#### Popp AI (USA/Europa)
```
Framework: Custom (Integration-focused)
LLM: GPT-4
Arquitetura: ATS integration via StackOne
```

| Componente | Tecnologia |
|------------|------------|
| Backend | Python + Node.js |
| Integration | StackOne Unified API ($500/mês) |
| LLM | GPT-4 |
| Compliance | Warden AI (independent review) |

**Por que NÃO usa CrewAI/LangGraph:**
- Focus em integração (não orchestration)
- Simples (não precisa de framework complexo)

**Diferencial:** StackOne = 2-4 weeks vs months de integração

**Replicabilidade:** ✅ 8 semanas, $1,000/mês

### 29.8.3 Ferramentas e Plataformas Identificadas

#### LLMs Utilizados
| LLM | Plataformas | Observação |
|-----|-------------|------------|
| **OpenAI GPT-4** | Todos (exceto Juicebox) | Mais estável, melhor qualidade |
| **Anthropic Claude** | DigaAI (backup) | Alternativa para português BR |
| **Gemini** | Ninguém ainda | **Oportunidade!** |

#### Agent Frameworks
| Framework | Plataformas | Status |
|-----------|-------------|--------|
| **LangGraph** | Beam AI (confirmado), SeekOut (provável) | ✅ Validado pelo mercado |
| **CrewAI** | Loxo (possível) | ⚠️ Inferido |
| **Custom** | Tezi, DigaAI, Gupy, InHire, Popp | Maioria |

#### Speech-to-Text
| Tecnologia | Plataformas |
|------------|-------------|
| **Google Speech-to-Text** | DigaAI, InHire |
| **Whisper (OpenAI)** | Alternativa popular |

#### Search Engines
| Tecnologia | Plataformas |
|------------|-------------|
| **Elasticsearch** | Gupy, outros |
| **AWS OpenSearch** | Juicebox |
| **Vector DBs** | Pinecone, Weaviate (embeddings) |

#### WhatsApp Integration
| Tecnologia | Plataformas |
|------------|-------------|
| **Twilio WhatsApp API** | DigaAI, InHire |
| **WhatsApp Business API** | Oficial |

#### ATS Integrations
| Tecnologia | Plataformas | Custo |
|------------|-------------|-------|
| **StackOne** | Popp AI | $500/mês (40+ ATSs) |
| **Composio** | Alternativa | 150+ tools |

#### Prompt Engineering
| Tecnologia | Uso Atual |
|------------|-----------|
| **Maxim AI** | Ninguém usa ainda (**oportunidade!**) |
| **Bifrost** | Alternativa |

### 29.8.4 Insights Estratégicos

#### 1. Maioria NÃO usa CrewAI/LangGraph

**Por quê:**
- Desenvolvidos antes de 2023 (frameworks são recentes)
- Workflows simples (não precisam de orchestration complexa)
- Custom = mais controle

**Implicação para WeDOTalent:**
- Não precisa usar CrewAI/LangGraph para MVP
- Custom pode ser mais rápido para começar
- Adicione frameworks depois se precisar de escala

#### 2. Todos usam GPT-4

**Por quê:**
- Mais estável
- Melhor qualidade
- Documentação extensa

**Implicação para WeDOTalent:**
- Comece com Claude (melhor português BR)
- GPT-4 como fallback
- Adicione Gemini depois (cost optimization)

#### 3. WhatsApp é diferencial no Brasil

**Quem usa:** DigaAI (interviewing), InHire (inscrição + pré-entrevista)

**Implicação para WeDOTalent:**
- WhatsApp = must-have no Brasil
- 90% dos brasileiros usam
- Baixa fricção

#### 4. Transcrição + Q&A é ÚNICO (InHire)

**Ninguém mais tem:** Tezi, Loxo, Beam, Gupy, DigaAI = não transcrevem

**Implicação para WeDOTalent:**
- Oportunidade de diferenciação
- Fácil de implementar (Google Speech-to-Text + GPT-4)
- WSI já captura isso parcialmente

#### 5. Hybrid Model (AI + Human) é futuro

**SeekOut:** AI faz volume, Human garante qualidade, Service (não só software)

**Implicação para WeDOTalent:**
- Considere modelo híbrido
- Não precisa ser 100% automático
- Qualidade > volume

### 29.8.5 Custos de Replicação por Plataforma

| Plataforma | Dev Cost | Infra/Mês | Timeline |
|------------|----------|-----------|----------|
| **Tezi AI** | - | $500-1,000 | 12-16 sem |
| **DigaAI** | - | $450-11,500 | 8-12 sem |
| **Gupy** | $270k | $7,000 | 12-18 meses |
| **InHire** | $230k | $7,000 | 8-10 meses |
| **SeekOut** | $470k | $34,000 | 12-18 meses |
| **Juicebox** | - | $1,100-2,600 | 8-12 sem |
| **Loxo** | $765k | - | 18-24 meses |
| **Beam AI** | - | $1,500-2,000 | 6 meses |
| **Popp AI** | - | $1,000 | 8 sem |

### 29.8.6 Arquitetura Recomendada (Baseada na Análise)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     ARQUITETURA WEDOTALENT RECOMENDADA                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Recruiter (Microsoft Teams / Web)                                         │
│      ↓                                                                      │
│  ┌─────────────────────────────┐                                           │
│  │  Vaga Creation Agent        │ ← WSI Scorecard auto-gerado               │
│  │  - Parse JD                 │                                           │
│  │  - Generate rubric          │                                           │
│  │  - Define workflow          │                                           │
│  └─────────────────────────────┘                                           │
│      ↓                                                                      │
│  ┌─────────────────────────────┐                                           │
│  │  Sourcing Agent             │ ← Two-Tier Search                         │
│  │  - Local DB (PostgreSQL)    │                                           │
│  │  - Pearch AI (external)     │                                           │
│  │  - Enrichment               │                                           │
│  └─────────────────────────────┘                                           │
│      ↓                                                                      │
│  ┌─────────────────────────────┐                                           │
│  │  Screening Agent (WSI)      │ ← Metodologia científica                  │
│  │  - Resume parsing           │                                           │
│  │  - WSI scoring              │                                           │
│  │  - Ranking                  │                                           │
│  └─────────────────────────────┘                                           │
│      ↓                                                                      │
│  ┌─────────────────────────────┐                                           │
│  │  Outreach Agent             │                                           │
│  │  - Personalized emails      │                                           │
│  │  - WhatsApp messages        │                                           │
│  │  - Multi-step campaigns     │                                           │
│  └─────────────────────────────┘                                           │
│      ↓                                                                      │
│  Candidate (WhatsApp/Email)                                                │
│      ↓                                                                      │
│  ┌─────────────────────────────┐                                           │
│  │  Pre-Interview Agent (WSI)  │ ← Voice Screening                         │
│  │  - WhatsApp conversational  │                                           │
│  │  - WSI Compact triagem      │                                           │
│  │  - Scheduling               │                                           │
│  └─────────────────────────────┘                                           │
│      ↓                                                                      │
│  Recruiter (Interview via Teams)                                           │
│      ↓                                                                      │
│  ┌─────────────────────────────┐                                           │
│  │  Transcription Agent ⭐      │ ← Diferencial único                       │
│  │  - Real-time transcription  │                                           │
│  │  - Keyword search           │                                           │
│  │  - Q&A sobre entrevista     │                                           │
│  └─────────────────────────────┘                                           │
│      ↓                                                                      │
│  ┌─────────────────────────────┐                                           │
│  │  Assessment Agent           │                                           │
│  │  - Generate parecer         │                                           │
│  │  - Recommendation           │                                           │
│  │  - Next steps               │                                           │
│  └─────────────────────────────┘                                           │
│      ↓                                                                      │
│  Hiring Decision                                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 29.8.7 Fontes da Análise

| Plataforma | Fonte |
|------------|-------|
| Tezi AI | https://help.tezi.ai/ |
| DigaAI | https://www.digai.ai/ |
| Gupy | https://www.gupy.io/inteligencia-artificial |
| InHire | https://www.inhire.com.br/produto/ia |
| SeekOut | https://www.seekout.com/platform/agentic-ai-recruiting |
| Juicebox | https://aws.amazon.com/blogs/big-data/juicebox-recruits-amazon-opensearch-service/ |
| Loxo | https://www.loxo.co/ai-agents-for-recruiters |
| Beam AI | https://beam.ai/platform |
| Popp AI | https://www.stackone.com/case-studies/popp |

---

# 30. Inteligência de Preços e Monetização dos Concorrentes

> **Fonte:** Pesquisa de mercado Novembro 2025 com dados de pricing de 12 plataformas concorrentes.

## 30.1 Modelos de Monetização

### Visão Geral por Tipo de Cobrança

| Modelo | Plataformas | Características |
|--------|-------------|-----------------|
| **Per Seat/User** | SeekOut, HireEZ, Gem, Loxo | Cobrança por usuário/mês |
| **Per Hire/Volume** | Tezi AI | Baseado em volume de contratações |
| **Custom Enterprise** | Popp AI, DigaAI, Gupy | Pricing customizado por empresa |
| **Tiered Plans** | Beam AI, Loxo | Planos escalonados por features |
| **Freemium + Paid** | Loxo, Gem | Free tier + upgrades pagos |

## 30.2 Tabela de Preços Detalhada (2024-2025)

### Plataformas Internacionais

| Plataforma | Preço Inicial | Preço Médio | Preço Enterprise | Modelo |
|------------|---------------|-------------|------------------|--------|
| **Tezi AI** | $83/mês (~$1k/ano) | $416/mês (~$5k/ano) | $833/mês (~$10k/ano) | Per hire volume |
| **SeekOut** | $125/user/mês | $225/user/mês | $400+/user/mês | Per seat + credits |
| **HireEZ** | $169/user/mês | $199-240/user/mês | $250+/user/mês | Per seat + credits |
| **Gem** | $270/mês (startups) | Custom | Custom | Tiered + custom |
| **Loxo** | $0 (free tier) | ~$500/user/mês | Custom | Freemium + tiered |
| **Beam AI** | $990/mês | $1,990/mês | $3,990+/mês | Tiered by features |
| **Popp AI** | Custom | Custom | Custom | Enterprise only |
| **Juicebox** | ~$200/mês | ~$500/mês | Custom | Search credits |

### Plataformas Brasil

| Plataforma | Preço Inicial | Preço Médio | Preço Enterprise | Modelo |
|------------|---------------|-------------|------------------|--------|
| **Gupy** | R$ 730/mês | R$ 1.500-3.000/mês | Custom | Tiered + volume |
| **DigaAI** | Custom | Custom | Custom | Enterprise only |
| **InHire** | Não divulgado | Não divulgado | Não divulgado | Custom |

### Custo Anual Estimado (Time de 5 Recrutadores)

| Plataforma | Custo Anual (5 users) | Observações |
|------------|----------------------|-------------|
| **Tezi AI** | $5,000 - $10,000 | Volume-based |
| **SeekOut** | $15,000 - $27,000 | Per seat |
| **HireEZ** | $10,000 - $14,400 | Per seat |
| **Gem** | $16,200+ | Startups discount |
| **Loxo** | $30,000+ | ~$6k/user |
| **Beam AI** | $23,880 - $47,880 | Platform fee |
| **Gupy** | R$ 43,800+ (~$8,700) | Entry tier |

## 30.3 Stacks Técnicas Detalhadas

### Matriz Completa de Tecnologias

| Plataforma | Backend | LLM Primary | LLM Secondary | Framework Agentes | Database | Voice AI |
|------------|---------|-------------|---------------|-------------------|----------|----------|
| **Tezi AI** | Python | GPT-4 | - | Custom (Calibration) | PostgreSQL | - |
| **DigaAI** | Python + Node.js | GPT-4 | Claude | Custom (State Machine) | PostgreSQL | Twilio + Google STT |
| **Gupy** | Python + Java | GPT-4 | - | ML tradicional | Elasticsearch | - |
| **InHire** | Python + Node.js | GPT-4 | - | Custom (Automation) | PostgreSQL | Google STT + Whisper |
| **SeekOut** | Python | GPT-4 | - | LangGraph (provável) | Custom + Vector DB | - |
| **Juicebox** | Python | Embeddings | - | N/A (Search) | AWS OpenSearch | - |
| **Loxo** | Python + Node.js | GPT-4 | - | CrewAI (possível) | Custom (800M profiles) | - |
| **Beam AI** | Python | GPT-4 | - | LangGraph | Cloud + Vector DB | Integrations |
| **Popp AI** | Python + Node.js | GPT-4 | - | Custom | PostgreSQL | Multi-channel |
| **HireEZ** | Python + Node.js | GPT-4 | - | Custom | Elasticsearch | - |
| **Gem** | Ruby + Python | GPT-4 | - | Custom | PostgreSQL | - |

### Sistema de Aprendizagem (Learning Systems)

| Plataforma | Tipo de Aprendizado | Mecanismo | Diferencial |
|------------|---------------------|-----------|-------------|
| **Tezi AI** | Calibration Loop | Feedback do recrutador → ajusta modelo | Autonomo, melhora com uso |
| **DigaAI** | Behavioral Analysis | Análise de padrões de resposta | 94% assertividade |
| **Gupy** | ML Tradicional | 10 anos de dados históricos | Semantic matching |
| **SeekOut** | Hybrid AI+Human | Human-in-loop valida outputs | Quality assurance |
| **Loxo** | Self-Updating CRM | CRM atualiza automaticamente | Único no mercado |
| **Beam AI** | Pre-trained Agents | Agents pré-treinados + fine-tuning | 100+ templates |
| **InHire** | Q&A sobre entrevistas | Transcrição + perguntas sobre histórico | Único no mercado |

### Integrações e Ecossistema

| Plataforma | ATSs Suportados | Canais de Comunicação | APIs Externas |
|------------|-----------------|----------------------|---------------|
| **Tezi AI** | Principais ATSs | Email, LinkedIn | SOC2 compliant |
| **DigaAI** | Principais ATSs BR | WhatsApp (principal) | Twilio |
| **Gupy** | Nativo (é ATS) | Email, SMS | TOTVS, Senior, ADP |
| **SeekOut** | Greenhouse, Lever, etc | Email, LinkedIn | LinkedIn Recruiter |
| **Loxo** | Nativo (é ATS) | Email, SMS, Social | 800M profiles DB |
| **Beam AI** | 100+ integrações | Multi-channel | StackOne, Composio |
| **Popp AI** | 30+ via StackOne | WhatsApp, SMS, Email, Video | StackOne ($500/mês) |
| **HireEZ** | Principais ATSs | Email | Boolean search |

## 30.4 Comparativo de Infraestrutura de IA

### Uso de Frameworks de Agentes

| Status | Plataformas | Framework |
|--------|-------------|-----------|
| **✅ Confirmado LangGraph** | Beam AI | LangGraph (documentado) |
| **⚠️ Provável LangGraph** | SeekOut | Usa terminologia "Agentic AI" |
| **⚠️ Possível CrewAI** | Loxo | "Fleet of agents" (terminologia CrewAI) |
| **❌ Custom/ML Tradicional** | Tezi, DigaAI, Gupy, InHire, Popp, HireEZ, Gem | Desenvolvidos antes de 2023 ou workflows simples |

### Por que a Maioria NÃO usa CrewAI/LangGraph?

| Razão | Explicação |
|-------|------------|
| **Timeline** | Desenvolvidos antes de 2023 (CrewAI/LangGraph são recentes) |
| **Complexidade** | Workflows simples não justificam framework complexo |
| **Controle** | Custom = mais controle sobre comportamento |
| **Legacy** | Migrar sistema existente é caro/arriscado |

### Implicações para WeDOTalent

| Insight | Recomendação |
|---------|--------------|
| **LangGraph é diferencial** | Poucos concorrentes usam → vantagem técnica |
| **Custom é viável para MVP** | Se LangGraph for complexo demais, começar custom |
| **Calibration Loop é valioso** | Tezi AI prova que aprendizado contínuo diferencia |
| **WhatsApp é obrigatório no BR** | DigaAI e InHire dominam por isso |

## 30.5 Benchmarking de Preços WeDOTalent

### Posicionamento Proposto

| Tier | Preço Sugerido | Público | Comparativo |
|------|----------------|---------|-------------|
| **Starter** | R$ 500-800/mês | PMEs, 1-2 recrutadores | Abaixo do Gupy (R$ 730) |
| **Professional** | R$ 1.500-2.500/mês | Médias empresas | Par com Gupy mid-tier |
| **Enterprise** | Custom (R$ 5.000+) | Grandes empresas | Custom como SeekOut |

### Modelo de Cobrança Recomendado

| Componente | Modelo | Justificativa |
|------------|--------|---------------|
| **Base** | Per seat (recrutador) | Previsibilidade para cliente |
| **Volume** | Créditos de busca Pearch | Controla custo variável |
| **Voice** | Per minute de screening | Alinha custo com uso |
| **Enterprise** | Custom all-inclusive | Grandes clientes preferem |

### Projeção de Revenue (Cenário Hybrid $301k)

| Métrica | Ano 1 | Ano 2 | Ano 3 |
|---------|-------|-------|-------|
| **Clientes** | 10 | 30 | 80 |
| **ARPU** | R$ 2.000/mês | R$ 2.500/mês | R$ 3.000/mês |
| **MRR** | R$ 20.000 | R$ 75.000 | R$ 240.000 |
| **ARR** | R$ 240.000 | R$ 900.000 | R$ 2.880.000 |

---

# 31. Metodologia WSI - WeDoTalent Skill Index

> **Fonte:** Documentação técnica oficial da metodologia de avaliação e triagens WSI Compact & Compact+.

## 31.1 Visão Geral e Propósito

A metodologia **WSI (WeDoTalent Skill Index)** foi desenvolvida pela WeDOTalent para padronizar e automatizar a validação técnica, comportamental e cultural em processos de recrutamento digital, utilizando **IA generativa e fluxos conversacionais** (via WhatsApp ou WebApp).

### Objetivo Principal
Traduzir respostas humanas em **sinais mensuráveis de competência**, produzindo um índice comparável entre candidatos, funções e empresas, sem abrir mão da experiência natural e humanizada.

### Versões da Metodologia

| Modelo | Nº de Perguntas | Tempo Médio | Indicado Para | Precisão |
|--------|-----------------|-------------|---------------|----------|
| **WSI Compact** | 6–8 | 5–7 minutos | Triagens rápidas, alto volume, vagas júnior | ~90% |
| **WSI Compact+** | 8–10 | 6:30–9 minutos | Vagas críticas, tech leads, liderança, especializadas | ~95% |

## 31.2 Fundamentação Teórica e Científica

O modelo WSI integra princípios clássicos de psicometria, aprendizagem e avaliação cognitiva, alinhando-se a frameworks reconhecidos globalmente.

### 31.2.1 Competency-Based Interviewing (CBI)

**Base:** McClelland, 1973 – Harvard University

As perguntas situacionais ("conte sobre uma vez em que...") permitem inferir competências a partir de comportamentos passados, correlacionando experiência real e tomada de decisão.

| Aplicação na LIA | Descrição |
|------------------|-----------|
| Perguntas contextuais | Base para análise semântica de respostas abertas |
| Microhistórias profissionais | Coletadas via WhatsApp para validação |

### 31.2.2 Taxonomia de Bloom (Revisada, Anderson et al., 2001)

Classificação de níveis cognitivos de domínio técnico:

| Nível Cognitivo | Descrição | Equivalência na Triagem |
|-----------------|-----------|-------------------------|
| **Lembrar** | Recordar fatos e conceitos | Autodeclaração simples |
| **Compreender** | Explicar ideias | Perguntas teóricas |
| **Aplicar** | Usar o conhecimento em prática | Microcases |
| **Analisar** | Diferenciar e relacionar conceitos | Contexto real |
| **Criar** | Gerar soluções novas | Respostas de inovação / liderança técnica |

### 31.2.3 Modelo Dreyfus de Aquisição de Habilidades (1980)

Modelo que descreve a progressão de domínio de uma habilidade:

| Nível | Dreyfus | Interpretação na WSI |
|-------|---------|---------------------|
| 1 | **Novice** | Conhecimento básico, teórico |
| 2 | **Advanced Beginner** | Aplicação parcial e guiada |
| 3 | **Competent** | Execução estável e consistente |
| 4 | **Proficient** | Aplicação autônoma e adaptativa |
| 5 | **Expert** | Domínio intuitivo e contextual |

> O score 1–5 da WSI é diretamente inspirado neste modelo.

### 31.2.4 Big Five (OCEAN Model) – Goldberg, 1992

Modelo de traços comportamentais preditores de performance:

| Fator | Significado | Validação na Triagem |
|-------|-------------|---------------------|
| **Abertura** (Openness) | Curiosidade, inovação | Inovação e aprendizado |
| **Conscienciosidade** | Organização, foco em resultado | Entregabilidade e rigor técnico |
| **Extroversão** | Energia e assertividade | Comunicação e liderança |
| **Amabilidade** | Empatia e colaboração | Trabalho em equipe |
| **Estabilidade Emocional** | Controle sob pressão | Tomada de decisão e resiliência |

### 31.2.5 Síntese Teórica

O modelo WSI combina **Dreyfus + Bloom + CBI + Big Five** sob uma abordagem de IA generativa, permitindo que a LIA:

```
┌─────────────────────────────────────────────────────────────────┐
│                    INTEGRAÇÃO TEÓRICA WSI                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │   Dreyfus   │    │    Bloom    │    │     CBI     │          │
│  │ (Maturidade)│    │ (Cognição)  │    │ (Comportam.)│          │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘          │
│         │                   │                   │                │
│         └─────────────┬─────┴─────────────┬─────┘                │
│                       │                   │                      │
│                       ▼                   ▼                      │
│              ┌─────────────────────────────────┐                │
│              │        MODELO WSI               │                │
│              │ Score 1-5 (Técnico + Cultural)  │                │
│              └─────────────┬───────────────────┘                │
│                            │                                     │
│                            ▼                                     │
│              ┌─────────────────────────────────┐                │
│              │         Big Five                │                │
│              │   (Traços Comportamentais)      │                │
│              └─────────────────────────────────┘                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Referências:**
- Competency Framework Design (CFA Institute, 2018)
- Conversational AI in Recruiting (Paradox, 2024)

## 31.3 Estrutura Operacional da LIA

### Fluxo Completo de Avaliação

| Etapa | Descrição | Resultado |
|-------|-----------|-----------|
| 1 | Análise do Job Description | Extração de skills e cultura |
| 2 | Sugestão automática de competências | Lista técnica e comportamental |
| 3 | Distribuição de pesos automáticos | Peso proporcional à senioridade |
| 4 | Triagem conversacional | Coleta e classificação de respostas |
| 5 | Cálculo de score e ranking | WSI técnico e comportamental |
| 6 | Governança humana | Recrutador valida resultados |

### Detalhamento por Etapa

| Etapa | Responsabilidade da LIA | Output |
|-------|------------------------|--------|
| **Leitura do JD** | Extrai palavras-chave, hard skills, soft skills e verbos de ação | Lista inicial de competências |
| **Mapeamento Cultural** | Conecta o JD aos valores e competências corporativas | Pilares de cultura e fit |
| **Sugestão de Skills** | Propõe até 7 competências (5 técnicas + 2 comportamentais) | Painel de pré-seleção |
| **Distribuição de Pesos** | Define pesos automáticos conforme senioridade | Scorecard técnico pré-preenchido |
| **Condução da Triagem** | Realiza conversa de validação com candidato | Respostas estruturadas (texto/áudio) |
| **Cálculo e Ranking** | Aplica metodologia WSI | Score individual e ranking de fit |

## 31.4 Estrutura Conversacional da Triagem

### Blocos do Fluxo Conversacional

| Etapa | Objetivo | Exemplo | Duração |
|-------|----------|---------|---------|
| **1. Abertura** | Apresentar propósito e tempo | "Leva uns 7 min e no final te mostro seu score técnico." | 0:30 min |
| **2. Validação Técnica** | 3–6 perguntas sobre competências | "De 1 a 5, como avalia seu domínio em Figma? Cite um exemplo de uso recente." | 3–4 min |
| **3. Fit Comportamental** | 2–4 perguntas situacionais | "Conte uma situação em que precisou resolver um problema em equipe." | 2–3 min |
| **4. Fechamento e Score** | Apresenta resultado e próximos passos | "Seu WSI foi 4.1 – nível alto. Envio ao recrutador!" | 0:30 min |

### Tipos de Perguntas

| Tipo de Pergunta | Objetivo | Exemplo |
|------------------|----------|---------|
| **Autodeclaração** | Quantificar domínio | "De 1 a 5, quanto domina Figma?" |
| **Contextual** | Validar aplicação real | "Cite um projeto onde aplicou Figma." |
| **Microcase** | Testar lógica técnica | "O que muda se trocar AND por OR neste SQL?" |
| **Situacional** | Avaliar comportamento | "Como você reage a feedbacks de design?" |

## 31.5 Sistema de Validação e Pontuação

### Formato de Validação (1 Pergunta = 2 Sinais)

Cada competência é avaliada com uma **única pergunta mista**, que combina autodeclaração e contexto real. A resposta é processada por IA generativa, que extrai dois indicadores:

- **Score de Autodeclaração** (0–5)
- **Score de Contexto** (0–5)

### Fórmula de Cálculo por Skill

```
Score_médio = (0.6 × Autodeclaração) + (0.4 × Contexto)
```

> Esse método mantém o rigor técnico com menos perguntas, sem perda de qualidade.

### Tipos de Validação Aplicados (Automáticos)

| Tipo de Validação | Critério de Avaliação | Peso Médio | Aplicação |
|-------------------|----------------------|------------|-----------|
| **Autodeclaração + Contexto** | Domínio técnico e aplicação real | 60% | Padrão para skills técnicas |
| **Microcase Prático** | Lógica, correção e performance | 20% | Vagas seniores e especializadas |
| **Situação Contextual** | Profundidade, clareza e postura | 15% | Soft skills e fit cultural |
| **Pergunta Teórica** | Clareza conceitual e consistência | 5% | Competências analíticas/metodológicas |

> A LIA aplica automaticamente o tipo mais adequado conforme a natureza da skill e o nível da vaga.

## 31.6 Cálculo do Índice WSI

### Fórmula Matemática

```
         Σ (Peso_i × Score_i)
WSI = ─────────────────────────
              100
```

### Distribuição de Pesos Recomendada

| Componente | Peso |
|------------|------|
| **Competências Técnicas** | 70% |
| **Competências Comportamentais/Culturais** | 30% |

### Classificações WSI

| Faixa | Interpretação | Nível Dreyfus |
|-------|---------------|---------------|
| **4,5 – 5,0** | Excelente | Expert |
| **4,0 – 4,4** | Alto | Proficient |
| **3,0 – 3,9** | Médio | Competent |
| **2,0 – 2,9** | Regular | Advanced Beginner |
| **< 2,0** | Baixo | Novice |

### Exemplo de Cálculo Real (UX Designer)

| Skill | Peso (%) | Tipo de Validação | Score Médio (0–5) | Contribuição |
|-------|----------|-------------------|-------------------|--------------|
| Design System | 25% | Microcase | 4.0 | 1.00 |
| Figma | 25% | Autodeclaração + Contexto | 4.5 | 1.12 |
| User Research | 20% | Contextual | 3.8 | 0.76 |
| Cultura: Colaboração | 15% | Situacional | 4.2 | 0.63 |
| Cultura: Inovação | 15% | Contextual | 3.8 | 0.57 |
| **Total WSI** | **100%** | — | — | **4.08 (Nível Alto)** |

## 31.7 Sistema de Score, Ranking e Saturação

### 31.7.1 Corte Inicial (Sem Histórico)

| Faixa WSI | Decisão |
|-----------|---------|
| **≥ 4,2** | Aprovado automático |
| **3,8 – 4,1** | Revisão manual |
| **3,0 – 3,7** | Aguardando comparação |
| **< 3,0** | Não aprovado |

### 31.7.2 Corte Dinâmico (Com Histórico)

Após 30–50 triagens por função:

| Percentil | Decisão |
|-----------|---------|
| **Top 25%** | Aprovado automático |
| **25% – 60%** | Revisão manual |
| **Abaixo de 60%** | Reprovado |

> A LIA recalibra automaticamente os percentis a cada nova triagem.

### 31.7.3 Saturação Inteligente

Quando o número de aprovados atinge o limite da vaga, o sistema:
- Aumenta automaticamente o threshold de aprovação
- Notifica o recrutador sobre saturação
- Sugere abertura de nova vaga ou expansão

## 31.8 Integração Cultural e Fit Comportamental

Além das habilidades técnicas, a LIA valida comportamentos e alinhamento cultural com base nos valores da empresa.

### Pilares de Cultura Avaliados

| Pilar de Cultura | Tipo de Pergunta | Exemplo |
|------------------|------------------|---------|
| **Colaboração** | Situação contextual | "Fale sobre um projeto em que precisou conciliar opiniões diferentes." |
| **Inovação** | Contexto real | "Conte uma vez em que propôs uma solução fora do padrão." |
| **Ética e Integridade** | Reflexiva | "Como você lida com prazos apertados e possíveis conflitos éticos?" |

> Esses pilares correspondem a **30% do WSI total**.

## 31.9 Governança Humana

### Regras de Revisão Manual

| Gatilho | Ação Requerida |
|---------|----------------|
| Score entre 3.8 – 4.1 | Revisão manual obrigatória |
| Inconsistência autodeclaração vs contexto | Flag para análise |
| Candidato reporta problema | Escalação para RH |
| Vaga crítica (C-level, tech lead) | Validação dupla obrigatória |

### Penalização Automática

O sistema aplica penalização automática para inconsistências:
- **Autodeclara 5, mas contexto pobre** → Redução -0,5 a -1
- **Respostas genéricas sem exemplos** → Redução -0,3
- **Contradições entre respostas** → Flag + redução -0,5

## 31.10 Benchmarks de Mercado

### Comparativo com Plataformas Líderes

| Plataforma | Metodologia | Tempo Médio | Precisão Reportada |
|------------|-------------|-------------|-------------------|
| **Paradox (Olivia)** | Conversacional + ML | 5-8 min | ~85% |
| **SHL** | Psicometria tradicional | 30-45 min | ~90% |
| **Gupy (GAIA)** | Semantic matching | 10-15 min | ~80% |
| **IBM Watson Talent** | NLP + ML | 15-20 min | ~85% |
| **WeDOTalent (WSI)** | CBI + Dreyfus + Big Five | 5-9 min | ~90-95% |

### Diferenciais WSI

| Aspecto | WSI | Concorrentes |
|---------|-----|--------------|
| **Fundamentação Teórica** | 4 frameworks integrados | 1-2 frameworks |
| **Tempo de Triagem** | 5-9 minutos | 10-45 minutos |
| **Canal Nativo** | WhatsApp-first | Web/Email |
| **Feedback ao Candidato** | Imediato com score | Dias/semanas |
| **Calibração Dinâmica** | Automática por função | Manual |

## 31.11 Boas Práticas de Aplicação

| Regra | Descrição |
|-------|-----------|
| **1** | Defina até 7 competências totais (5 técnicas + 2 comportamentais) |
| **2** | Prefira perguntas curtas e diretas (respostas de até 40 segundos em áudio) |
| **3** | Reaproveite scores de triagens anteriores para ranqueamento preditivo |
| **4** | Utilize Compact+ apenas em vagas com maior complexidade técnica |
| **5** | Monitore taxa de conclusão (ideal: >85%) |
| **6** | Revise manualmente os primeiros 10 candidatos de cada nova vaga |

## 31.12 Exibição no Painel

### Exemplo de Scorecard Exibido

```
┌─────────────────────────────────────────────────────────────────┐
│ ✅ Triagem concluída – LIA                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ 🧠 Figma: 4.5/5                                                 │
│ 🎨 Design System: 4.0/5                                         │
│ 📊 User Research: 3.8/5                                         │
│ 🤝 Cultura e Fit: 4.0/5                                         │
│                                                                  │
│ 🔹 WSI Final: 4.1 — Nível Alto                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Visualizações Disponíveis no Painel

- Ranking geral da vaga
- Distribuição de scores por competência
- Histórico de triagens do candidato
- Análise de consistência (autodeclaração vs. contexto)
- Sugestões automáticas de follow-up
- Gráficos comparativos entre candidatos

## 31.13 Resumo Executivo

### Para Recrutadores (Versão Profissional)

> O WSI é um índice ponderado de 0 a 5 que combina validações técnicas (70%) e comportamentais (30%). Cada competência é avaliada via pergunta mista (autodeclaração + contexto) e processada por IA semântica. Scores acima de 4.2 são aprovados automaticamente; entre 3.8 e 4.1 passam por revisão manual.

### Para Candidatos (Versão Leiga)

> Você respondeu algumas perguntas sobre suas habilidades e experiências. A LIA analisou suas respostas considerando tanto o que você disse saber, quanto os exemplos que você deu. Seu score reflete o quanto suas competências combinam com o que a vaga precisa.

## 31.14 Conclusão

O modelo **WSI Compact & Compact+** combina:
- ✅ Inteligência de IA generativa
- ✅ Metodologia de avaliação padronizada (4 frameworks científicos)
- ✅ Experiência fluida e humanizada

Ele transforma a triagem em um processo **curto, natural e altamente preditivo**, com métricas consistentes e transparência total.

> 💬 **"A LIA não faz perguntas. Ela entende o que o candidato revela."**
> 
> Cada interação gera um sinal técnico, comportamental e cultural processado em tempo real, resultando em um índice objetivo: o **WSI – WeDoTalent Skill Index**.

---

# 32. Roadmap de Produto - WeDOTalent v1 e v2

> **Objetivo:** Definir o caminho de evolução do produto desde MVP até plataforma ATS completa, com priorização baseada em valor de negócio, complexidade técnica e dependências.

## 32.1 Visão Geral das Versões

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EVOLUÇÃO WEDOTALENT                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │   v1.0 MVP   │────▶│   v1.5 GA    │────▶│   v2.0 ATS   │                │
│  │  (3 meses)   │     │  (3 meses)   │     │  (6 meses)   │                │
│  └──────────────┘     └──────────────┘     └──────────────┘                │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ v1.0 MVP: LIA Conversacional + Triagem WSI + Busca Two-Tier         │   │
│  │ v1.5 GA:  Multi-agentes + Integrações ATS + Voice Screening         │   │
│  │ v2.0 ATS: ATS Nativo + Analytics + White-label + Enterprise         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Definição das Versões

| Versão | Nome | Duração | Objetivo Principal |
|--------|------|---------|-------------------|
| **v1.0** | MVP | 3 meses | Validar proposta de valor com clientes piloto |
| **v1.5** | General Availability | 3 meses | Escalar para mercado com integrações |
| **v2.0** | ATS Completo | 6 meses | Plataforma end-to-end com analytics avançado |

## 32.2 Inventário de Features

### Legenda de Status

| Símbolo | Status | Descrição |
|---------|--------|-----------|
| ✅ | Existente | Implementado e funcional |
| 🔄 | Em Progresso | Desenvolvimento iniciado |
| 📋 | Planejado | Especificado, aguardando desenvolvimento |
| 💡 | Ideação | Conceito inicial, requer validação |

### Módulo 1: LIA - Agente Conversacional

| Feature | Status | v1.0 | v1.5 | v2.0 | Complexidade | Valor |
|---------|--------|------|------|------|--------------|-------|
| Chat interface básica | ✅ | ✓ | ✓ | ✓ | Baixa | Alto |
| Intent classification | ✅ | ✓ | ✓ | ✓ | Média | Alto |
| Entity extraction | ✅ | ✓ | ✓ | ✓ | Média | Alto |
| Conversational memory | ✅ | ✓ | ✓ | ✓ | Média | Alto |
| Context side panel | ✅ | ✓ | ✓ | ✓ | Média | Médio |
| Multi-modal input (texto/voz) | 📋 | - | ✓ | ✓ | Alta | Alto |
| Proactive suggestions | 📋 | - | ✓ | ✓ | Média | Médio |
| LIA Personality customization | 💡 | - | - | ✓ | Média | Baixo |
| Multi-language support | 💡 | - | - | ✓ | Alta | Médio |

### Módulo 2: Gestão de Vagas

| Feature | Status | v1.0 | v1.5 | v2.0 | Complexidade | Valor |
|---------|--------|------|------|------|--------------|-------|
| CRUD de vagas | ✅ | ✓ | ✓ | ✓ | Baixa | Alto |
| Job Description parser | ✅ | ✓ | ✓ | ✓ | Média | Alto |
| Criação conversacional | ✅ | ✓ | ✓ | ✓ | Alta | Alto |
| Frames visuais (matrix, timeline) | ✅ | ✓ | ✓ | ✓ | Média | Médio |
| Templates de vaga | 📋 | ✓ | ✓ | ✓ | Baixa | Médio |
| Aprovação workflow | 📋 | - | ✓ | ✓ | Média | Alto |
| Publicação multi-canal | 📋 | - | ✓ | ✓ | Alta | Alto |
| Job boards integration | 📋 | - | - | ✓ | Alta | Alto |
| Vaga confidencial | 💡 | - | - | ✓ | Baixa | Baixo |

### Módulo 3: Sourcing e Busca

| Feature | Status | v1.0 | v1.5 | v2.0 | Complexidade | Valor |
|---------|--------|------|------|------|--------------|-------|
| Busca local (PostgreSQL) | ✅ | ✓ | ✓ | ✓ | Média | Alto |
| Busca externa (Pearch AI) | ✅ | ✓ | ✓ | ✓ | Média | Alto |
| Two-Tier Search orchestration | ✅ | ✓ | ✓ | ✓ | Alta | Alto |
| Busca por linguagem natural | ✅ | ✓ | ✓ | ✓ | Alta | Alto |
| Arquétipos pré-configurados | ✅ | ✓ | ✓ | ✓ | Baixa | Médio |
| Boolean search avançado | 📋 | - | ✓ | ✓ | Média | Médio |
| Semantic search (embeddings) | 📋 | - | ✓ | ✓ | Alta | Alto |
| Enrichment automático | 📋 | - | - | ✓ | Alta | Médio |
| LinkedIn integration | 💡 | - | - | ✓ | Alta | Alto |
| Chrome extension | 💡 | - | - | ✓ | Alta | Médio |

### Módulo 4: Triagem e Avaliação (WSI)

| Feature | Status | v1.0 | v1.5 | v2.0 | Complexidade | Valor |
|---------|--------|------|------|------|--------------|-------|
| WSI Compact (texto) | 🔄 | ✓ | ✓ | ✓ | Alta | Alto |
| WSI Compact+ (texto) | 🔄 | ✓ | ✓ | ✓ | Alta | Alto |
| Score calculation engine | 🔄 | ✓ | ✓ | ✓ | Alta | Alto |
| Scorecard visualization | 📋 | ✓ | ✓ | ✓ | Média | Alto |
| Voice screening (OpenMic) | 📋 | - | ✓ | ✓ | Alta | Alto |
| WhatsApp integration | 📋 | - | ✓ | ✓ | Alta | Alto |
| Calibration loop | 📋 | - | ✓ | ✓ | Alta | Alto |
| Big Five assessment | 📋 | - | - | ✓ | Alta | Médio |
| Technical tests | 📋 | - | - | ✓ | Alta | Médio |
| Video interviews | 💡 | - | - | ✓ | Alta | Médio |

### Módulo 5: Pipeline e Kanban

| Feature | Status | v1.0 | v1.5 | v2.0 | Complexidade | Valor |
|---------|--------|------|------|------|--------------|-------|
| Kanban board | ✅ | ✓ | ✓ | ✓ | Média | Alto |
| Drag & drop | ✅ | ✓ | ✓ | ✓ | Média | Alto |
| Filtros avançados | ✅ | ✓ | ✓ | ✓ | Média | Médio |
| Bulk actions | 📋 | ✓ | ✓ | ✓ | Média | Alto |
| Custom stages | 📋 | - | ✓ | ✓ | Média | Médio |
| Stage automations | 📋 | - | ✓ | ✓ | Alta | Alto |
| SLA tracking | 📋 | - | - | ✓ | Média | Alto |
| Pipeline analytics | 📋 | - | - | ✓ | Média | Alto |

### Módulo 6: Agendamento

| Feature | Status | v1.0 | v1.5 | v2.0 | Complexidade | Valor |
|---------|--------|------|------|------|--------------|-------|
| Agenda básica | ✅ | ✓ | ✓ | ✓ | Média | Alto |
| Microsoft Graph integration | 🔄 | ✓ | ✓ | ✓ | Alta | Alto |
| Google Calendar integration | 📋 | - | ✓ | ✓ | Alta | Alto |
| AI-first scheduling modal | 📋 | ✓ | ✓ | ✓ | Alta | Alto |
| Availability checking | 📋 | ✓ | ✓ | ✓ | Média | Alto |
| Email templates AI | 📋 | ✓ | ✓ | ✓ | Média | Médio |
| Interview panel coordination | 📋 | - | - | ✓ | Alta | Médio |
| Room/resource booking | 💡 | - | - | ✓ | Média | Baixo |

### Módulo 7: Comunicação

| Feature | Status | v1.0 | v1.5 | v2.0 | Complexidade | Valor |
|---------|--------|------|------|------|--------------|-------|
| Notificações in-app | ✅ | ✓ | ✓ | ✓ | Baixa | Médio |
| Email templates | 📋 | ✓ | ✓ | ✓ | Baixa | Alto |
| WhatsApp outreach | 📋 | - | ✓ | ✓ | Alta | Alto |
| SMS integration | 📋 | - | - | ✓ | Média | Médio |
| Cadence automation | 📋 | - | ✓ | ✓ | Alta | Alto |
| Bulk messaging | 📋 | - | ✓ | ✓ | Média | Alto |
| Response tracking | 📋 | - | - | ✓ | Média | Médio |
| NPS candidato | 💡 | - | - | ✓ | Baixa | Médio |

### Módulo 8: Integrações ATS

| Feature | Status | v1.0 | v1.5 | v2.0 | Complexidade | Valor |
|---------|--------|------|------|------|--------------|-------|
| Gupy connector | 🔄 | - | ✓ | ✓ | Alta | Alto |
| Pandapé connector | 🔄 | - | ✓ | ✓ | Alta | Alto |
| StackOne middleware | 📋 | - | ✓ | ✓ | Alta | Alto |
| Greenhouse connector | 📋 | - | - | ✓ | Alta | Médio |
| Lever connector | 📋 | - | - | ✓ | Alta | Médio |
| Workday connector | 💡 | - | - | ✓ | Alta | Médio |
| SAP SuccessFactors | 💡 | - | - | ✓ | Alta | Médio |
| API pública | 📋 | - | - | ✓ | Alta | Alto |
| Webhooks | 📋 | - | ✓ | ✓ | Média | Alto |

### Módulo 9: Analytics e Dashboards

| Feature | Status | v1.0 | v1.5 | v2.0 | Complexidade | Valor |
|---------|--------|------|------|------|--------------|-------|
| Dashboard básico | ✅ | ✓ | ✓ | ✓ | Média | Alto |
| 7 dashboards estratégicos | ✅ | ✓ | ✓ | ✓ | Alta | Alto |
| KPIs de recrutamento | 📋 | ✓ | ✓ | ✓ | Média | Alto |
| Time-to-hire tracking | 📋 | - | ✓ | ✓ | Média | Alto |
| Cost-per-hire | 📋 | - | ✓ | ✓ | Média | Alto |
| Source effectiveness | 📋 | - | ✓ | ✓ | Média | Alto |
| Predictive analytics | 📋 | - | - | ✓ | Alta | Alto |
| Custom reports | 📋 | - | - | ✓ | Alta | Médio |
| Export (PDF, Excel) | 📋 | - | ✓ | ✓ | Baixa | Médio |
| Real-time dashboards | 💡 | - | - | ✓ | Alta | Médio |

### Módulo 10: Gestão de Candidatos

| Feature | Status | v1.0 | v1.5 | v2.0 | Complexidade | Valor |
|---------|--------|------|------|------|--------------|-------|
| Perfil do candidato | ✅ | ✓ | ✓ | ✓ | Média | Alto |
| CV parsing | 📋 | ✓ | ✓ | ✓ | Alta | Alto |
| Duplicate detection | 📋 | ✓ | ✓ | ✓ | Alta | Alto |
| Candidate comparison | ✅ | ✓ | ✓ | ✓ | Média | Alto |
| Talent pool | 📋 | - | ✓ | ✓ | Média | Alto |
| Tags e categorias | 📋 | ✓ | ✓ | ✓ | Baixa | Médio |
| Activity timeline | 📋 | - | ✓ | ✓ | Média | Médio |
| LGPD compliance (consentimento) | 📋 | ✓ | ✓ | ✓ | Média | Alto |
| Candidate portal | 💡 | - | - | ✓ | Alta | Médio |
| Referral tracking | 💡 | - | - | ✓ | Média | Médio |

### Módulo 11: Administração

| Feature | Status | v1.0 | v1.5 | v2.0 | Complexidade | Valor |
|---------|--------|------|------|------|--------------|-------|
| User management | ✅ | ✓ | ✓ | ✓ | Média | Alto |
| Role-based access (RBAC) | 📋 | ✓ | ✓ | ✓ | Alta | Alto |
| Company settings | ✅ | ✓ | ✓ | ✓ | Baixa | Alto |
| Branding customization | 📋 | - | ✓ | ✓ | Média | Médio |
| Audit logs | 📋 | - | ✓ | ✓ | Média | Alto |
| SSO (SAML, OAuth) | 📋 | - | - | ✓ | Alta | Alto |
| Multi-tenant | 📋 | - | - | ✓ | Alta | Alto |
| White-label | 💡 | - | - | ✓ | Alta | Médio |

## 32.3 Matriz de Priorização (RICE)

### Metodologia RICE

| Fator | Descrição | Peso |
|-------|-----------|------|
| **R**each | Quantos usuários impactados | 1-10 |
| **I**mpact | Quanto impacta cada usuário | 0.25-3 |
| **C**onfidence | Confiança na estimativa | 0.5-1 |
| **E**ffort | Esforço em person-months | 0.5-9 |

**Fórmula:** `RICE Score = (Reach × Impact × Confidence) / Effort`

### Top 20 Features Priorizadas

| Rank | Feature | Reach | Impact | Confidence | Effort | RICE | Versão |
|------|---------|-------|--------|------------|--------|------|--------|
| 1 | WSI Compact completo | 10 | 3 | 0.9 | 2 | 13.5 | v1.0 |
| 2 | WhatsApp integration | 10 | 3 | 0.8 | 3 | 8.0 | v1.5 |
| 3 | CV parsing | 10 | 2 | 0.9 | 2 | 9.0 | v1.0 |
| 4 | Gupy connector | 8 | 3 | 0.8 | 3 | 6.4 | v1.5 |
| 5 | Voice screening | 8 | 3 | 0.7 | 4 | 4.2 | v1.5 |
| 6 | Calibration loop | 7 | 3 | 0.8 | 3 | 5.6 | v1.5 |
| 7 | Email templates | 10 | 2 | 0.9 | 1 | 18.0 | v1.0 |
| 8 | Bulk actions | 8 | 2 | 0.9 | 1 | 14.4 | v1.0 |
| 9 | RBAC | 8 | 2 | 0.9 | 2 | 7.2 | v1.0 |
| 10 | Duplicate detection | 8 | 2 | 0.8 | 2 | 6.4 | v1.0 |
| 11 | Semantic search | 7 | 3 | 0.7 | 4 | 3.7 | v1.5 |
| 12 | Stage automations | 7 | 2 | 0.8 | 3 | 3.7 | v1.5 |
| 13 | Cadence automation | 6 | 3 | 0.7 | 4 | 3.2 | v1.5 |
| 14 | Google Calendar | 8 | 2 | 0.9 | 2 | 7.2 | v1.5 |
| 15 | Pandapé connector | 6 | 3 | 0.8 | 3 | 4.8 | v1.5 |
| 16 | Predictive analytics | 5 | 3 | 0.6 | 5 | 1.8 | v2.0 |
| 17 | Big Five assessment | 5 | 2 | 0.7 | 4 | 1.8 | v2.0 |
| 18 | API pública | 4 | 3 | 0.8 | 4 | 2.4 | v2.0 |
| 19 | SSO | 4 | 2 | 0.9 | 3 | 2.4 | v2.0 |
| 20 | White-label | 3 | 2 | 0.7 | 5 | 0.8 | v2.0 |

## 32.4 Cronograma Detalhado

### v1.0 MVP (Q1 2026 - 12 semanas)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          v1.0 MVP - 12 SEMANAS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SPRINT 1-2 (Semana 1-4): FUNDAÇÃO                                         │
│  ├── FastAPI backend setup (existente, ajustes)                            │
│  ├── PostgreSQL schema final                                               │
│  ├── WSI engine core (cálculo de score)                                    │
│  ├── CV parsing (básico)                                                   │
│  └── LGPD compliance (consentimento)                                       │
│                                                                             │
│  SPRINT 3-4 (Semana 5-8): CORE FEATURES                                    │
│  ├── WSI Compact completo (texto)                                          │
│  ├── Scorecard visualization                                               │
│  ├── Email templates + envio                                               │
│  ├── Bulk actions (aprovar, rejeitar, mover)                               │
│  └── Templates de vaga                                                     │
│                                                                             │
│  SPRINT 5-6 (Semana 9-12): ESTABILIZAÇÃO                                   │
│  ├── RBAC (Admin, Recrutador, Viewer)                                      │
│  ├── Duplicate detection                                                   │
│  ├── AI-first scheduling modal                                             │
│  ├── Testing & QA                                                          │
│  └── Soft launch (3-5 clientes piloto)                                     │
│                                                                             │
│  MILESTONE: 5 clientes piloto ativos, 100 triagens WSI                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### v1.5 General Availability (Q2 2026 - 12 semanas)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      v1.5 GA - 12 SEMANAS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SPRINT 7-8 (Semana 13-16): INTEGRAÇÕES                                    │
│  ├── WhatsApp Business API integration                                     │
│  ├── Gupy connector (StackOne)                                             │
│  ├── Google Calendar integration                                           │
│  └── Webhooks básicos                                                      │
│                                                                             │
│  SPRINT 9-10 (Semana 17-20): VOICE + INTELLIGENCE                          │
│  ├── Voice screening (OpenMic.ai)                                          │
│  ├── Calibration loop                                                      │
│  ├── Semantic search (pgvector)                                            │
│  └── Stage automations                                                     │
│                                                                             │
│  SPRINT 11-12 (Semana 21-24): ESCALA                                       │
│  ├── Pandapé connector                                                     │
│  ├── Cadence automation                                                    │
│  ├── Branding customization                                                │
│  ├── Audit logs                                                            │
│  └── GA launch                                                             │
│                                                                             │
│  MILESTONE: 30 clientes, 1.000 triagens/mês, 2 ATSs integrados             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### v2.0 ATS Completo (Q3-Q4 2026 - 24 semanas)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      v2.0 ATS - 24 SEMANAS                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SPRINT 13-16 (Semana 25-32): ATS NATIVO                                   │
│  ├── Job boards integration (Indeed, LinkedIn, Catho)                      │
│  ├── Talent pool management                                                │
│  ├── Candidate portal                                                      │
│  ├── Activity timeline                                                     │
│  └── Custom reports                                                        │
│                                                                             │
│  SPRINT 17-20 (Semana 33-40): ANALYTICS + ENTERPRISE                       │
│  ├── Predictive analytics                                                  │
│  ├── Big Five assessment                                                   │
│  ├── Technical tests                                                       │
│  ├── SSO (SAML, OAuth)                                                     │
│  └── Multi-tenant                                                          │
│                                                                             │
│  SPRINT 21-24 (Semana 41-48): ENTERPRISE+                                  │
│  ├── API pública + documentação                                            │
│  ├── Greenhouse + Lever connectors                                         │
│  ├── White-label                                                           │
│  ├── Interview panel coordination                                          │
│  └── Enterprise launch                                                     │
│                                                                             │
│  MILESTONE: 80 clientes, 10.000 triagens/mês, ATS próprio funcional        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 32.5 Dependências Críticas

### Diagrama de Dependências

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DEPENDÊNCIAS DE FEATURES                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WSI Engine ─────────┬──▶ Voice Screening                                  │
│       │              │                                                      │
│       │              └──▶ Calibration Loop                                 │
│       │                                                                     │
│       └──▶ Scorecard ──▶ Predictive Analytics                              │
│                                                                             │
│  WhatsApp Integration ──▶ Cadence Automation                               │
│                                                                             │
│  Semantic Search ─────┬──▶ Boolean Search Avançado                         │
│       (pgvector)      │                                                     │
│                       └──▶ Enrichment Automático                           │
│                                                                             │
│  StackOne Middleware ─┬──▶ Gupy Connector                                  │
│                       ├──▶ Pandapé Connector                               │
│                       └──▶ Greenhouse/Lever Connectors                     │
│                                                                             │
│  RBAC ────────────────┬──▶ Audit Logs                                      │
│                       ├──▶ SSO                                             │
│                       └──▶ Multi-tenant                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Bloqueadores Externos

| Dependência | Tipo | Impacto | Mitigação |
|-------------|------|---------|-----------|
| **WhatsApp Business API** | Aprovação Meta | Alto | Iniciar processo 4 semanas antes |
| **OpenMic.ai** | Contrato SLA | Alto | Negociar durante v1.0 |
| **StackOne** | Onboarding técnico | Médio | POC paralelo em v1.0 |
| **Pearch AI** | Créditos/pricing | Médio | Fallback para busca local |
| **LangSmith** | Workspace org | Baixo | Configuração em v1.0 |

## 32.6 Métricas de Sucesso por Versão

### v1.0 MVP - Validação

| Métrica | Target | Método de Medição |
|---------|--------|-------------------|
| **Clientes piloto** | 5 | Contrato assinado |
| **Triagens WSI** | 100 | Logs do sistema |
| **NPS candidato** | > 40 | Survey pós-triagem |
| **Acurácia WSI** | > 85% | Validação com recrutador |
| **Time-to-screen** | < 7 min | Timestamp início/fim |
| **Taxa de conclusão** | > 80% | Triagens completas / iniciadas |

### v1.5 GA - Tração

| Métrica | Target | Método de Medição |
|---------|--------|-------------------|
| **Clientes pagantes** | 30 | MRR > 0 |
| **Triagens/mês** | 1.000 | Logs agregados |
| **Taxa de retenção** | > 90% | Cohort mensal |
| **Voice adoption** | > 40% | Triagens com voz / total |
| **Integração ativa** | 50% | Clientes com ATS conectado |
| **CSAT recrutador** | > 4.2/5 | Survey in-app |

### v2.0 ATS - Escala

| Métrica | Target | Método de Medição |
|---------|--------|-------------------|
| **Clientes totais** | 80 | Contratos ativos |
| **ARR** | R$ 2.8M | Faturamento anualizado |
| **Triagens/mês** | 10.000 | Logs agregados |
| **Uso ATS nativo** | 30% | Clientes sem integração externa |
| **Enterprise clients** | 5 | Contratos > R$ 10k/mês |
| **Churn mensal** | < 5% | Cancelamentos / base |

## 32.7 Equipe Necessária por Fase

### v1.0 MVP (Time Mínimo)

| Papel | FTEs | Responsabilidades |
|-------|------|-------------------|
| **Tech Lead** | 1 | Arquitetura, código crítico, code review |
| **Backend Developer** | 2 | FastAPI, LangGraph, integrações |
| **Frontend Developer** | 1 | Vue.js, UI/UX |
| **Product Manager** | 0.5 | Especificação, priorização, stakeholders |
| **QA** | 0.5 | Testes manuais, automação básica |
| **Total** | **5 FTEs** | |

### v1.5 GA (Time Expandido)

| Papel | FTEs | Delta |
|-------|------|-------|
| **Tech Lead** | 1 | - |
| **Backend Developer** | 3 | +1 |
| **Frontend Developer** | 2 | +1 |
| **DevOps/SRE** | 1 | +1 |
| **Product Manager** | 1 | +0.5 |
| **QA** | 1 | +0.5 |
| **Customer Success** | 1 | +1 |
| **Total** | **10 FTEs** | +5 |

### v2.0 ATS (Time Completo)

| Papel | FTEs | Delta |
|-------|------|-------|
| **Engineering Manager** | 1 | +1 |
| **Tech Lead** | 1 | - |
| **Backend Developer** | 4 | +1 |
| **Frontend Developer** | 3 | +1 |
| **Data Engineer** | 1 | +1 |
| **DevOps/SRE** | 2 | +1 |
| **Product Manager** | 2 | +1 |
| **UX Designer** | 1 | +1 |
| **QA** | 2 | +1 |
| **Customer Success** | 2 | +1 |
| **Sales** | 2 | +2 |
| **Total** | **21 FTEs** | +11 |

## 32.8 Riscos e Mitigações do Roadmap

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| **Atraso em integrações ATS** | Alta | Alto | Começar POC StackOne em v1.0 |
| **Aprovação WhatsApp Business** | Média | Alto | Aplicar 4 semanas antes; ter SMS como fallback |
| **Acurácia WSI abaixo do esperado** | Média | Alto | Calibration loop contínuo; human-in-loop |
| **Escassez de devs Python/LangGraph** | Alta | Médio | Contratar antecipadamente; treinar time |
| **Competidor lança feature similar** | Média | Médio | Foco em diferenciais (WSI, Voice, BR market) |
| **Custo de LLM escala** | Baixa | Médio | Fallback multi-LLM; cache agressivo |
| **LGPD enforcement** | Baixa | Alto | Compliance desde v1.0; DPO externo |

## 32.9 Resumo Executivo do Roadmap

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ROADMAP WEDOTALENT - RESUMO                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  📅 TIMELINE:                                                               │
│  ├── v1.0 MVP: Q1 2026 (12 semanas) → 5 clientes piloto                    │
│  ├── v1.5 GA:  Q2 2026 (12 semanas) → 30 clientes, 1k triagens/mês         │
│  └── v2.0 ATS: Q3-Q4 2026 (24 semanas) → 80 clientes, R$ 2.8M ARR          │
│                                                                             │
│  🎯 PRIORIDADES v1.0:                                                       │
│  ├── WSI Compact completo (triagem via texto)                              │
│  ├── CV parsing + duplicate detection                                      │
│  ├── Email templates + bulk actions                                        │
│  └── RBAC + LGPD compliance                                                │
│                                                                             │
│  🚀 FEATURES DIFERENCIADORES:                                               │
│  ├── WSI (metodologia científica única)                                    │
│  ├── Voice Screening (WhatsApp-first)                                      │
│  ├── Two-Tier Search (custo + resiliência)                                 │
│  └── Calibration Loop (melhora com uso)                                    │
│                                                                             │
│  👥 EQUIPE:                                                                 │
│  ├── v1.0: 5 FTEs                                                          │
│  ├── v1.5: 10 FTEs                                                         │
│  └── v2.0: 21 FTEs                                                         │
│                                                                             │
│  💰 INVESTIMENTO:                                                           │
│  ├── Build: $567k (36 meses)                                               │
│  ├── Buy: $171k (36 meses)                                                 │
│  └── Hybrid: $301k (36 meses) ← RECOMENDADO                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 33. Produtos Avançados: Pipeline Intelligence e Analytics Premium

> **Posicionamento:** Após consolidação do Plugin (v1.0-v1.5), estes módulos representam a evolução para "Talent Intelligence Platform" - expandindo de ferramenta operacional para plataforma estratégica de decisão.

## 33.1 Visão Geral dos Produtos Avançados

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EVOLUÇÃO DE PRODUTO WEDOTALENT                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FASE 1: PLUGIN (v1.0-v1.5)                                                │
│  └── Automação de tarefas operacionais                                     │
│      • WSI Screening                                                        │
│      • CV Parsing                                                           │
│      • Agendamento AI                                                       │
│      • Comunicação automatizada                                             │
│                                                                             │
│  FASE 2: PIPELINE INTELLIGENCE (v2.0)                                      │
│  └── Automação proativa de pipeline e mapeamento                           │
│      • Pipeline Automation                                                  │
│      • Talent Database Diagnostics                                          │
│      • Proactive Shortlists                                                 │
│      • Talent Nurturing Campaigns                                           │
│      • Market Mapping                                                       │
│                                                                             │
│  FASE 3: ANALYTICS PREMIUM (v2.5)                                          │
│  └── Inteligência preditiva e decisória (dados já coletados)               │
│      • Dashboards avançados                                                 │
│      • Predictive Analytics                                                 │
│      • Workforce Planning Intelligence                                      │
│      • Risk & Turnover Analysis                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Lógica da sequência:**
1. **Plugin** → Coleta dados operacionais (triagens, contratações, interações)
2. **Pipeline Intelligence** → Constrói pipelines e mapeamentos, gerando mais dados
3. **Analytics Premium** → Analisa todos os dados coletados para insights preditivos

## 33.2 Pipeline Intelligence - Automação Proativa de Talentos (FASE 2 - v2.0)

### 33.2.1 Visão do Produto

O **Pipeline Intelligence** transforma o recrutamento de reativo para proativo. Em vez de buscar candidatos quando a vaga abre, o sistema mantém pipelines aquecidos e prontos para shortlists instantâneos. Integra diagnóstico do banco de dados com workforce planning para antecipar demandas.

### 33.2.2 Componentes do Módulo

#### A. Pipeline Automation Engine

| Feature | Descrição | Automação |
|---------|-----------|-----------|
| **Smart Pipeline Builder** | Criação automática de pipelines baseada em diagnóstico do banco de dados | AI analisa gaps e sugere pipelines |
| **Demand-Driven Pipelines** | Pipelines vinculados a workforce planning e forecast de demanda | Antecipação de 3-6 meses |
| **Turnover-Triggered Pipelines** | Ativação automática quando risco de turnover detectado | Posições críticas cobertas |
| **Stage Automation** | Regras para movimentação automática entre stages | Redução de 60% em tarefas manuais |
| **SLA Enforcement** | Alertas e escalation automático baseado em SLA por stage | Compliance 95%+ |

#### B. Talent Database Diagnostics

| Análise | Output | Ação Recomendada |
|---------|--------|------------------|
| **Coverage Analysis** | % de cobertura por skill/seniority/localidade | Identificar gaps de sourcing |
| **Freshness Score** | Idade média dos perfis, última interação | Priorizar nurturing |
| **Quality Distribution** | Distribuição de WSI scores no banco | Identificar segmentos premium |
| **Engagement Decay** | Taxa de resposta ao longo do tempo | Reativação de talentos frios |
| **Competitor Overlap** | Candidatos que também estão em processos concorrentes | Priorização de approach |

```
┌─────────────────────────────────────────────────────────────────┐
│              DIAGNÓSTICO DE BANCO DE DADOS                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  EXEMPLO: Cliente "TechCorp" - 15.000 perfis                    │
│                                                                  │
│  COVERAGE GAPS:                                                  │
│  ⚠️ Data Engineers Senior: 23 perfis (gap: 40+)                 │
│  ⚠️ Product Managers: 45 perfis (gap: 30+)                      │
│  ✅ Frontend Devs: 320 perfis (adequado)                         │
│  ✅ Backend Devs: 280 perfis (adequado)                          │
│                                                                  │
│  FRESHNESS:                                                      │
│  🔴 8.200 perfis > 12 meses sem contato                          │
│  🟡 4.500 perfis 6-12 meses sem contato                          │
│  🟢 2.300 perfis < 6 meses (warm)                                │
│                                                                  │
│  RECOMENDAÇÃO AI:                                                │
│  1. Lançar sourcing intensivo: Data Engineers                    │
│  2. Campanha de nurturing: 8.200 perfis frios                   │
│  3. Priorizar pipeline: Product Managers (demanda Q2)            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### C. Integração com Workforce Planning

| Input do Planning | Análise Pipeline | Output |
|-------------------|------------------|--------|
| **Headcount plan 2026** | Cobertura atual vs demanda | Pipelines priorizados por gap |
| **Turnover projetado** | Risco por área/posição | Pipelines preventivos ativados |
| **Áreas críticas** | Talent pool disponível | Sourcing intensivo automático |
| **Timeline** | Capacidade de delivery | Alertas de capacity |

#### D. Proactive Search & Nurturing

| Feature | Descrição | Frequência |
|---------|-----------|------------|
| **Continuous Sourcing** | Busca automática Two-Tier (local + Pearch) para pipelines ativos | Diária |
| **Smart Nurturing Campaigns** | Cadências personalizadas por persona/seniority/engajamento | Ongoing |
| **Content Triggers** | Envio de conteúdo relevante baseado em interesses/skills | Event-driven |
| **Re-engagement Sequences** | Sequências específicas para reativar talentos frios | Mensal |
| **Warm Pool Maintenance** | Interações periódicas para manter candidatos engajados | Trimestral |

#### E. Proactive Shortlists

| Trigger | Ação Automática | SLA |
|---------|-----------------|-----|
| **Nova vaga aberta** | Shortlist de 5-10 candidatos do pipeline | < 1 hora |
| **Turnover risk alto** | Shortlist preventivo para posição de risco | < 24 horas |
| **Workforce plan demand** | Shortlist antecipado 30 dias antes da demanda | 30 dias antes |
| **Hiring manager request** | Shortlist sob demanda via chat LIA | < 2 horas |

```
FLUXO: PROACTIVE SHORTLIST

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Demanda    │     │   Pipeline   │     │  Shortlist   │
│  Detectada   │────▶│   Ativado    │────▶│  Automático  │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
  • Workforce Plan    • Two-Tier Search    • 5-10 candidatos
  • Turnover Risk     • Nurturing ativo    • WSI Score ≥4.0
  • Nova vaga         • Engagement track   • Match score
  • HM request        • Quality filter     • Disponibilidade
```

#### F. Market Mapping (Talent Intelligence)

| Feature | Descrição | Output |
|---------|-----------|--------|
| **Company Intelligence** | Mapeamento de estruturas organizacionais de empresas-alvo | Org charts, headcounts, key people |
| **Talent Pool Mapping** | Identificação de talentos em empresas específicas | Listas priorizadas por fit |
| **Competitive Intelligence** | Análise de movimentações, contratações e saídas de concorrentes | Alertas de oportunidade |
| **Salary Benchmarking** | Faixas salariais por empresa/cargo/localidade | Posicionamento competitivo |
| **Skills Heatmap** | Concentração de skills por empresa/região | Estratégia de sourcing |

```
┌─────────────────────────────────────────────────────────────────┐
│              MARKET MAPPING - EXEMPLO                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  EMPRESA-ALVO: "FinTech XYZ"                                    │
│                                                                  │
│  ESTRUTURA IDENTIFICADA:                                         │
│  ├── Technology (180 pessoas)                                   │
│  │   ├── Engineering (120)                                      │
│  │   │   ├── Backend: 45 (3 seniors, 12 plenos)                │
│  │   │   ├── Frontend: 35 (2 seniors, 10 plenos)               │
│  │   │   ├── Mobile: 25 (2 seniors, 8 plenos)                  │
│  │   │   └── DevOps: 15 (1 senior, 5 plenos)                   │
│  │   ├── Data (30)                                              │
│  │   └── Product (30)                                           │
│  ├── Operations (80)                                            │
│  └── Commercial (60)                                            │
│                                                                  │
│  INSIGHTS:                                                       │
│  🔥 3 Seniors Backend em risco (detectado via LinkedIn)         │
│  📈 Crescimento 40% YoY em Data team                            │
│  💰 Salários 15% acima do mercado                               │
│                                                                  │
│  CANDIDATOS MAPEADOS: 12 perfis high-priority                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 33.2.3 Ciclo Integrado: Planning → Pipeline → Hiring

```
┌─────────────────────────────────────────────────────────────────┐
│         CICLO INTEGRADO: PLANNING → PIPELINE → HIRING            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. WORKFORCE PLANNING INPUT                                     │
│     ├── Headcount plan 2026: +50 contratações                   │
│     ├── Turnover projetado: 15% (12 posições)                   │
│     ├── Áreas críticas: Engineering, Data                       │
│     └── Timeline: Q1-Q2 2026                                    │
│                           ▼                                      │
│  2. PIPELINE INTELLIGENCE ANALYSIS                               │
│     ├── Cobertura atual: 60% (gaps identificados)               │
│     ├── Diagnóstico banco: 2.300 perfis warm                    │
│     ├── Demanda vs capacidade: OK até +30/quarter               │
│     └── Risco: Data Engineers (cobertura 30%)                   │
│                           ▼                                      │
│  3. AUTOMAÇÃO ATIVADA                                            │
│     ├── Pipeline "Data Engineers Q1": criado automaticamente    │
│     ├── Sourcing intensivo: 20 novos perfis/semana              │
│     ├── Nurturing: 45 perfis existentes reativados              │
│     └── Shortlist ready: 15 candidatos warm                     │
│                           ▼                                      │
│  4. EXECUÇÃO                                                     │
│     ├── Vaga abre: shortlist instantâneo (< 1h)                 │
│     ├── Time-to-fill: -40% vs processo tradicional              │
│     └── Quality of hire: +25% (pipeline qualificado)            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 33.2.4 Diferenciadores vs Concorrência

| Feature | WeDOTalent | Gupy | SeekOut | Beamery |
|---------|------------|------|---------|---------|
| Smart Pipeline Builder | ✅ | ❌ | ⚠️ Manual | ✅ |
| Database Diagnostics | ✅ | ❌ | ❌ | ⚠️ |
| Workforce Planning Integration | ✅ | ❌ | ⚠️ | ✅ |
| Proactive Shortlists (< 1h) | ✅ | ❌ | ⚠️ | ✅ |
| Market Mapping | ✅ | ❌ | ✅ | ✅ |
| Turnover-Triggered Pipelines | ✅ | ❌ | ❌ | ⚠️ |

---

## 33.3 Workforce Planning - Do Básico ao Enterprise (FASE 2.5 - 2026/2029)

### 33.3.1 Visão Estratégica do Workforce Planning

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WORKFORCE PLANNING: ESTRATÉGIA DE PRODUTO                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MODELO DE EVOLUÇÃO:                                                        │
│  ├── WFP Básico (2026): Gratuito, insumos para pipeline e dashboards        │
│  ├── WFP Professional (2027): Pago, features intermediárias                 │
│  └── WFP Enterprise (2028-2029): Plataforma completa de mercado             │
│                                                                             │
│  OBJETIVO ESTRATÉGICO:                                                      │
│  ├── Fase 1: WFP Básico gera dados → alimenta Pipeline Intelligence        │
│  ├── Fase 2: WFP dados → alimenta Analytics Premium (indicadores)          │
│  └── Fase 3: WFP Enterprise → nova linha de receita premium                 │
│                                                                             │
│  POSICIONAMENTO DE MERCADO:                                                 │
│  ├── Concorrentes WFP: Workday, SAP SuccessFactors, Visier, ChartHop       │
│  ├── Preço mercado: $15-50/employee/mês (enterprise)                        │
│  ├── Nossa entrada: Freemium → upsell para enterprise                      │
│  └── Diferencial: Integração nativa com recrutamento + IA                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 33.3.2 WFP Básico - Gratuito (2026)

O **Workforce Planning Básico** é um módulo gratuito que coleta dados organizacionais para alimentar as funcionalidades de Pipeline Intelligence e dashboards. Serve como "porta de entrada" para o WFP completo.

#### Features do WFP Básico (Incluso no Plano)

| Feature | Descrição | Dados Gerados |
|---------|-----------|---------------|
| **Org Chart Simplificado** | Estrutura hierárquica básica (até 3 níveis) | Headcount por área, gestores |
| **Headcount Tracker** | Registro de FTEs por departamento | Histórico de crescimento |
| **Turnover Input** | Registro manual de saídas voluntárias/involuntárias | Taxa de turnover por área |
| **Hiring Plan Input** | Plano de contratações por trimestre (manual) | Demanda projetada |
| **Skills Inventory Básico** | Tags de skills por colaborador (manual) | Mapa de competências |
| **Budget Placeholder** | Orçamento de headcount por área (opcional) | Custo de pessoal |

#### Uso dos Dados do WFP Básico

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                FLUXO DE DADOS: WFP BÁSICO → OUTRAS FEATURES                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WFP BÁSICO (INPUT)                                                         │
│       │                                                                     │
│       ├────────────────────────────────────────────────────────────────┐    │
│       │                                                                │    │
│       ▼                                                                ▼    │
│  ┌─────────────────────┐                           ┌─────────────────────┐  │
│  │ PIPELINE            │                           │ DASHBOARDS          │  │
│  │ INTELLIGENCE        │                           │ (Gratuitos + Pagos) │  │
│  ├─────────────────────┤                           ├─────────────────────┤  │
│  │ • Turnover data     │                           │ • Headcount trends  │  │
│  │   → Pipelines       │                           │ • Turnover rate     │  │
│  │     preventivos     │                           │ • Hiring velocity   │  │
│  │ • Hiring plan       │                           │ • Dept growth       │  │
│  │   → Pipelines       │                           │ • Budget vs actual  │  │
│  │     proativos       │                           │ • Skills gaps       │  │
│  │ • Skills gaps       │                           │                     │  │
│  │   → Sourcing        │                           │                     │  │
│  │     direcionado     │                           │                     │  │
│  └─────────────────────┘                           └─────────────────────┘  │
│                                                                             │
│  DASHBOARDS GRATUITOS (usando dados WFP):                                  │
│  ├── Headcount Overview: Total FTEs, crescimento MoM, distribuição        │
│  ├── Turnover Summary: Taxa geral, por área, tendência                    │
│  └── Hiring Progress: Plan vs Actual, vagas abertas vs fechadas           │
│                                                                             │
│  DASHBOARDS PAGOS (Analytics Premium):                                     │
│  ├── Turnover Prediction: Risco de saída por área/pessoa                  │
│  ├── Demand Forecasting: Projeção de necessidade de contratação           │
│  └── Capacity Planning: Time de recrutamento vs demanda                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 33.3.3 WFP Professional - Pago (2027)

Evolução do WFP Básico com features de análise e automação. Primeiro tier pago.

| Feature | Descrição | Preço Sugerido |
|---------|-----------|----------------|
| **Org Chart Avançado** | Estrutura ilimitada, visualização interativa, exportação | +R$ 500/mês |
| **Succession Planning Básico** | Identificação de posições críticas, backup suggestions | Incluso |
| **Scenario Modeling (3 cenários)** | "What-if" para crescimento, contração, reorganização | Incluso |
| **Skills Gap Analysis** | Comparação skills atuais vs necessários por área | Incluso |
| **Attrition Alerts** | Alertas de risco de saída baseado em padrões | Incluso |
| **Headcount Forecast (6 meses)** | Projeção baseada em histórico e tendências | Incluso |
| **Integration API** | Conexão com HRIS (manual sync) | Incluso |

**Preço WFP Professional:** R$ 500-1.500/mês (baseado em headcount)

### 33.3.4 WFP Enterprise - Plataforma Completa (2028-2029)

Plataforma de Workforce Planning de mercado, competindo com soluções enterprise.

| Feature | Descrição | Diferencial |
|---------|-----------|-------------|
| **Strategic Workforce Planning** | Planejamento de 1-5 anos com múltiplos cenários | Integração com recrutamento |
| **AI-Powered Demand Forecasting** | ML para prever demanda baseado em growth plans, mercado | Dados de recrutamento |
| **Real-time Headcount Sync** | Integração bidirecional com HRIS (Workday, SAP, etc) | Automação completa |
| **Compensation Planning** | Análise salarial, budget allocation, equity planning | Mercado + interno |
| **Skills Taxonomy Management** | Taxonomia de skills, career paths, desenvolvimento | Ligado ao recrutamento |
| **Org Design Studio** | Redesenho organizacional, simulações, aprovações | Visual + analytics |
| **Contingent Workforce** | Gestão de contractors, temps, gig workers | Custo total de workforce |
| **M&A Workforce Planning** | Planejamento para fusões e aquisições | Cenários complexos |
| **Board-Ready Reports** | Relatórios executivos, presentations automáticas | Storytelling com dados |
| **Compliance & Audit** | LGPD, SOC2, auditoria de dados de pessoas | Enterprise-grade |

**Preço WFP Enterprise:** R$ 3.000-15.000/mês (baseado em headcount + módulos)

### 33.3.5 Roadmap de Desenvolvimento WFP

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ROADMAP WORKFORCE PLANNING                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  2026 - WFP BÁSICO (GRATUITO)                                              │
│  ├── Q2 2026: Org chart simplificado + headcount tracker                   │
│  ├── Q3 2026: Turnover input + hiring plan input                           │
│  └── Q4 2026: Skills inventory básico + dashboards gratuitos               │
│      Esforço: ~4 sprints (2 meses) | 1 AI Engineer + 1 Backend             │
│                                                                             │
│  2027 - WFP PROFESSIONAL (PAGO)                                            │
│  ├── Q1 2027: Org chart avançado + succession planning                     │
│  ├── Q2 2027: Scenario modeling + skills gap analysis                      │
│  ├── Q3 2027: Attrition alerts + headcount forecast                        │
│  └── Q4 2027: Integration API + HRIS connectors                            │
│      Esforço: ~8 sprints (4 meses) | 1 AI Engineer + 1 Backend + 1 Front   │
│                                                                             │
│  2028-2029 - WFP ENTERPRISE (PREMIUM)                                      │
│  ├── 2028 H1: Strategic WFP + AI demand forecasting                        │
│  ├── 2028 H2: Real-time HRIS sync + compensation planning                  │
│  ├── 2029 H1: Skills taxonomy + org design studio                          │
│  └── 2029 H2: Contingent workforce + M&A planning + compliance             │
│      Esforço: ~20 sprints (10 meses) | Time dedicado de 3-4 pessoas        │
│                                                                             │
│  DEPENDÊNCIAS:                                                              │
│  ├── WFP Básico: Requer v1.5 (GA) estável                                  │
│  ├── WFP Professional: Requer Pipeline Intelligence + 30+ clientes         │
│  └── WFP Enterprise: Requer 80+ clientes + funding adicional               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 33.3.6 Projeção de Revenue WFP

| Produto | 2026 | 2027 | 2028 | 2029 |
|---------|------|------|------|------|
| **WFP Básico** | R$ 0 (gratuito) | R$ 0 | R$ 0 | R$ 0 |
| **WFP Professional** | — | R$ 120k | R$ 360k | R$ 600k |
| **WFP Enterprise** | — | — | R$ 180k | R$ 720k |
| **Total WFP** | R$ 0 | R$ 120k | R$ 540k | R$ 1.32M |

**Nota:** WFP Básico não gera receita direta, mas:
- Aumenta retenção (stickiness) → reduz churn
- Gera dados para Pipeline Intelligence → upsell
- Qualifica leads para WFP Professional → conversão

---

## 33.4 Analytics Premium - Módulo de Inteligência Decisória (FASE 3 - v2.5)

### 33.4.1 Visão do Produto

O **Analytics Premium** transforma dados de recrutamento em insights acionáveis para tomada de decisão estratégica. Diferente de dashboards básicos, oferece análise preditiva e prescritiva. Depende dos dados coletados nas fases anteriores (Plugin + Pipeline Intelligence + WFP Básico) para modelos mais precisos.

### 33.3.2 Componentes do Módulo

#### A. Dashboards Estratégicos (7 Categorias Expandidas)

| Dashboard | Descrição | Métricas Principais |
|-----------|-----------|---------------------|
| **Efficiency Hub** | Performance operacional | Time-to-fill, SLA compliance, recruiter productivity |
| **Quality Analytics** | Qualidade das contratações | Quality of hire (90d, 180d, 1yr), WSI accuracy, hiring manager satisfaction |
| **Cost Intelligence** | Análise financeira | Cost-per-hire, source ROI, channel efficiency |
| **Pipeline Health** | Saúde do funil | Conversion rates, bottleneck detection, stage velocity |
| **Diversity & Inclusion** | Métricas DE&I | Demographic pipeline, offer acceptance by group, bias detection |
| **Candidate Experience** | NPS e satisfação | Candidate NPS, dropout analysis, feedback themes |
| **Predictive Insights** | Análise preditiva | Hiring probability, time-to-fill forecast, risk alerts |

#### B. Predictive Analytics Engine

| Modelo Preditivo | Input | Output | Accuracy Target |
|------------------|-------|--------|-----------------|
| **Time-to-Fill Forecast** | Job specs, market data, histórico | Dias estimados para contratação | ±3 dias (85%) |
| **Hiring Probability** | Candidato profile, stage, engagement | % chance de contratação | 80%+ |
| **Turnover Risk** | Employee data, market signals | Probabilidade de saída em 6m | 75%+ |
| **Offer Acceptance** | Candidate engagement, market rate | % aceitação de oferta | 80%+ |
| **Source Quality** | Historical hires, performance data | Score de qualidade por fonte | 85%+ |
| **Bottleneck Prediction** | Pipeline velocity, capacity | Gargalos em 2-4 semanas | 70%+ |

#### C. Workforce Planning Intelligence

| Feature | Descrição | Benefício |
|---------|-----------|-----------|
| **Demand Forecasting** | Projeção de demanda de contratação baseada em growth plans, turnover, sazonalidade | Antecipação de 3-6 meses |
| **Capacity Planning** | Análise de capacidade do time de recrutamento vs demanda projetada | Dimensionamento correto |
| **Gap Analysis** | Identificação de skills gaps entre workforce atual e futuro | Priorização de hiring |
| **Succession Risk** | Análise de risco de sucessão por área/posição crítica | Planos de contingência |
| **Scenario Modeling** | Simulações "what-if" para diferentes cenários de crescimento | Planejamento estratégico |

#### D. Risk & Turnover Analytics

| Análise | Dados Utilizados | Insight Gerado |
|---------|------------------|----------------|
| **Early Warning System** | Engagement scores, 1:1 feedback, performance trends | Alertas de risco de saída |
| **Turnover Pattern Analysis** | Histórico de saídas, timing, departamento | Padrões sazonais/departamentais |
| **Exit Interview Intelligence** | Transcrições, feedback, exit surveys | Temas recorrentes e root causes |
| **Market Pressure Index** | Salários mercado, demanda skills, concorrência | Pressão externa por área |
| **Retention ROI** | Custo de turnover vs investimento em retenção | Priorização de ações |

### 33.3.3 Tecnologia do Analytics Premium

```
┌─────────────────────────────────────────────────────────────────┐
│                  STACK ANALYTICS PREMIUM                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  DATA LAYER                                                      │
│  ├── PostgreSQL (operational data)                               │
│  ├── Data Warehouse (historical aggregations)                    │
│  └── Real-time streaming (Kafka/Redis)                           │
│                                                                  │
│  ANALYTICS ENGINE                                                │
│  ├── Python (pandas, scikit-learn, prophet)                      │
│  ├── ML Models (regression, classification, time-series)         │
│  └── Claude/GPT-4 (natural language insights)                    │
│                                                                  │
│  VISUALIZATION                                                   │
│  ├── Chart.js / Recharts (React)                                 │
│  ├── Export: PDF, Excel, PowerPoint                              │
│  └── Scheduled reports (email digest)                            │
│                                                                  │
│  AI INSIGHTS                                                     │
│  ├── Natural language summaries                                  │
│  ├── Anomaly detection alerts                                    │
│  └── Actionable recommendations                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 33.3.4 Diferenciadores vs Concorrência

| Feature | WeDOTalent | Gupy | Greenhouse | SeekOut |
|---------|------------|------|------------|---------|
| Predictive time-to-fill | ✅ | ❌ | ⚠️ Basic | ✅ |
| AI-generated insights | ✅ | ❌ | ❌ | ✅ |
| Workforce planning | ✅ | ❌ | ⚠️ Add-on | ✅ |
| Turnover risk prediction | ✅ | ❌ | ❌ | ⚠️ |
| Natural language queries | ✅ | ❌ | ❌ | ❌ |
| WSI correlation analysis | ✅ | ❌ | ❌ | ❌ |

---

## 33.5 Modelo de Monetização dos Produtos Avançados

### 33.5.1 Estratégia de Pricing

| Produto | Modelo | Justificativa |
|---------|--------|---------------|
| **Analytics Premium** | Add-on mensal (% do plano base) | Valor incremental claro, fácil upsell |
| **Pipeline Intelligence** | Créditos + subscription | Combina uso variável com receita recorrente |
| **Market Mapping** | Por projeto ou subscription | Alto valor percebido, serviço consultivo |
| **WFP Básico** | Gratuito (incluso) | Gera dados, aumenta stickiness, porta de entrada |
| **WFP Professional** | Subscription mensal | Primeiro tier pago de WFP |
| **WFP Enterprise** | Subscription + módulos | Plataforma completa de mercado |

### 33.5.2 Tabela de Preços Proposta

#### Analytics Premium

| Tier | Preço Mensal | Incluso | Target |
|------|--------------|---------|--------|
| **Starter** | +R$ 300/mês | 3 dashboards básicos, export PDF | SMB (até 10 vagas/mês) |
| **Professional** | +R$ 800/mês | 7 dashboards, predictive analytics | Mid-Market (10-50 vagas/mês) |
| **Enterprise** | +R$ 2.000/mês | Todos os dashboards, custom reports, API, dedicated support | Enterprise (50+ vagas/mês) |

#### Pipeline Intelligence

| Tier | Preço Mensal | Créditos | Features |
|------|--------------|----------|----------|
| **Essentials** | +R$ 500/mês | 5 pipelines ativos, 100 nurturing contacts/mês | Automação básica, shortlists |
| **Growth** | +R$ 1.500/mês | 15 pipelines ativos, 500 nurturing contacts/mês | + Diagnóstico banco, proactive search |
| **Enterprise** | +R$ 4.000/mês | Ilimitado pipelines, 2.000 nurturing contacts/mês | + Market mapping, competitive intelligence |

#### Workforce Planning

| Tier | Preço Mensal | Incluso | Disponibilidade |
|------|--------------|---------|-----------------|
| **WFP Básico** | R$ 0 (gratuito) | Org chart, headcount, turnover input, hiring plan | 2026 (Q2-Q4) |
| **WFP Professional** | +R$ 500-1.500/mês | + Succession, scenarios, skills gap, HRIS sync | 2027 |
| **WFP Enterprise** | +R$ 3.000-15.000/mês | Plataforma completa: strategic WFP, AI forecasting, org design | 2028-2029 |

#### Market Mapping (Add-on)

| Modelo | Preço | Entrega |
|--------|-------|---------|
| **Por Empresa** | R$ 500-2.000 | Mapeamento completo de 1 empresa-alvo |
| **Por Setor** | R$ 3.000-8.000 | Mapeamento de setor/região específica |
| **Subscription** | +R$ 2.000/mês | Acesso contínuo + atualizações trimestrais |

### 33.5.3 Projeção de Revenue (Atualizada com WFP)

| Produto | 2026 | 2027 | 2028 | 2029 |
|---------|------|------|------|------|
| **Analytics Premium** | R$ 180k | R$ 540k | R$ 900k | R$ 1.2M |
| **Pipeline Intelligence** | R$ 120k | R$ 480k | R$ 750k | R$ 1.0M |
| **Market Mapping** | R$ 60k | R$ 180k | R$ 300k | R$ 400k |
| **WFP Básico** | R$ 0 | R$ 0 | R$ 0 | R$ 0 |
| **WFP Professional** | — | R$ 120k | R$ 360k | R$ 600k |
| **WFP Enterprise** | — | — | R$ 180k | R$ 720k |
| **Total Add-ons** | **R$ 360k** | **R$ 1.32M** | **R$ 2.49M** | **R$ 3.92M** |

**Premissas:**
- 2026: 40 clientes, 20% adopt analytics, 15% adopt pipeline, 10% adopt mapping
- 2027: 80 clientes, 30% adopt analytics, 25% adopt pipeline, 15% adopt mapping, 10% adopt WFP Pro
- 2028: 120 clientes, 35% adopt analytics, 30% adopt pipeline, 20% adopt mapping, 20% WFP Pro, 5% WFP Enterprise
- 2029: 180 clientes, 40% adopt analytics, 35% adopt pipeline, 25% adopt mapping, 25% WFP Pro, 10% WFP Enterprise

### 33.5.4 Valor Estratégico do WFP Básico (Gratuito)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  POR QUE WFP BÁSICO É GRATUITO?                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  BENEFÍCIO 1: GERA DADOS                                                   │
│  ├── Dados de org → alimentam Pipeline Intelligence                       │
│  ├── Dados de turnover → alimentam Analytics Premium                      │
│  ├── Dados de hiring plan → alimentam previsões                           │
│  └── Quanto mais dados, melhor o produto = mais valor                     │
│                                                                             │
│  BENEFÍCIO 2: AUMENTA STICKINESS                                           │
│  ├── Cliente cadastra estrutura organizacional                            │
│  ├── Custo de troca aumenta (dados no sistema)                            │
│  ├── Engajamento diário aumenta                                           │
│  └── Churn reduz significativamente (-20-30%)                             │
│                                                                             │
│  BENEFÍCIO 3: PORTA DE ENTRADA                                            │
│  ├── Cliente experimenta valor de WFP                                     │
│  ├── Percebe limitações → deseja features avançadas                       │
│  ├── Upsell natural para WFP Professional                                 │
│  └── Conversão esperada: 15-25% em 12 meses                               │
│                                                                             │
│  BENEFÍCIO 4: DIFERENCIAL COMPETITIVO                                     │
│  ├── Gupy não tem WFP                                                     │
│  ├── ATSs tradicionais não integram WFP                                   │
│  ├── Somos ATS + Agentes IA + WFP integrado                               │
│  └── Narrativa: "Plataforma completa de gestão de talentos"               │
│                                                                             │
│  ROI ESTIMADO DO WFP GRATUITO:                                             │
│  ├── Retenção: +R$ 200k/ano (churn evitado)                               │
│  ├── Upsell WFP Pro: +R$ 120k/ano (conversões)                            │
│  ├── Cross-sell Analytics: +R$ 80k/ano (dados melhores)                   │
│  └── Total: +R$ 400k/ano de valor indireto                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 33.5.5 Comparativo de Mercado

| Produto | WeDOTalent | Gupy | SeekOut | Beamery | Workday |
|---------|------------|------|---------|---------|---------|
| **Analytics Premium** | R$ 300-2.000/mês | Incluso (básico) | $200-500/user | $300+/user | Custom |
| **Pipeline Intelligence** | R$ 500-4.000/mês | N/A | $150-300/user | $200+/user | N/A |
| **Market Mapping** | R$ 500-8.000/projeto | N/A | $100-200/user | Custom | N/A |
| **WFP Básico** | **Gratuito** | N/A | N/A | N/A | N/A |
| **WFP Professional** | R$ 500-1.500/mês | N/A | N/A | N/A | $15-30/employee |
| **WFP Enterprise** | R$ 3.000-15.000/mês | N/A | N/A | Add-on | $30-50/employee |

**Posicionamento:** WeDOTalent oferece WFP integrado ao ATS - concorrentes tratam como produtos separados ou não oferecem.

---

## 33.6 Roadmap de Implementação

### 33.6.1 Timeline

```
┌─────────────────────────────────────────────────────────────────┐
│          ROADMAP PRODUTOS AVANÇADOS (ATUALIZADO COM WFP)         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Q2 2026 (v2.0)                                                  │
│  └── Pipeline Intelligence MVP + WFP Básico (início)             │
│      • Smart Pipeline Builder                                    │
│      • Talent Database Diagnostics                               │
│      • Basic Nurturing Automation                                │
│      • Proactive Shortlists                                      │
│      • Market Mapping (básico)                                   │
│      • WFP: Org chart simplificado + headcount tracker           │
│                                                                  │
│  Q3 2026 (v2.5)                                                  │
│  └── Analytics Premium MVP + WFP Básico (continuação)            │
│      • 5 dashboards estratégicos                                 │
│      • Predictive time-to-fill                                   │
│      • Export PDF/Excel                                          │
│      • Natural language insights (básico)                        │
│      • WFP: Turnover input + hiring plan input                   │
│                                                                  │
│  Q4 2026 (v3.0)                                                  │
│  └── Pipeline + Analytics GA + WFP Básico (completo)             │
│      • Full Nurturing Campaigns                                  │
│      • Market Mapping (completo)                                 │
│      • 7 dashboards completos                                    │
│      • WFP: Skills inventory + dashboards gratuitos              │
│                                                                  │
│  2027                                                            │
│  └── WFP Professional (Pago)                                     │
│      • Q1: Org chart avançado + succession planning              │
│      • Q2: Scenario modeling + skills gap analysis               │
│      • Q3: Attrition alerts + headcount forecast                 │
│      • Q4: Integration API + HRIS connectors                     │
│                                                                  │
│  2028-2029                                                       │
│  └── WFP Enterprise (Premium)                                    │
│      • Strategic WFP + AI demand forecasting                     │
│      • Real-time HRIS sync + compensation planning               │
│      • Skills taxonomy + org design studio                       │
│      • Contingent workforce + M&A planning                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Lógica da sequência:**
1. **Pipeline Intelligence + WFP Básico (Q2 2026)** → Coleta dados de pipelines + estrutura organizacional
2. **Analytics Premium + WFP dados (Q3 2026)** → Analisa dados já coletados com modelos preditivos
3. **GA + WFP Completo (Q4 2026)** → Todos produtos básicos maduros e integrados
4. **WFP Professional (2027)** → Primeiro tier pago de Workforce Planning
5. **WFP Enterprise (2028-2029)** → Plataforma completa competindo com Workday/Visier

### 33.6.2 Dependências Técnicas

| Produto | Dependência | Prioridade |
|---------|-------------|------------|
| **Pipeline Intelligence** | Nurturing engine, Two-Tier Search | Alta |
| **WFP Básico** | v1.5 (GA) estável, módulo de cadastro | Média |
| **Market Mapping** | Pearch AI integration, data enrichment | Alta |
| **Analytics Premium** | Data warehouse setup, ML pipeline, 6+ meses de dados do Pipeline | Alta |
| **WFP Professional** | WFP Básico adotado por 30%+ clientes | Média |
| **WFP Enterprise** | 80+ clientes, funding adicional, time dedicado | Baixa (2028+) |

### 33.6.3 Equipe Adicional Necessária

| Fase | Adições | Total FTEs |
|------|---------|------------|
| v2.0 (Q2 2026) | +1 Backend (nurturing), +0.5 Frontend | 12.5 |
| v2.5 (Q3 2026) | +1 Data Engineer, +0.5 ML Engineer | 14 |
| v3.0 (Q4 2026) | +1 ML Engineer (full), +1 CS | 16 |
| v3.5 (Q1 2027) | +2 Backend, +1 Data Analyst (WFP Pro) | 19 |
| v4.0 (2028) | +3 dedicados WFP Enterprise | 22 |

---

## 33.7 Resumo Executivo - Produtos Avançados

```
┌─────────────────────────────────────────────────────────────────────────────┐
│   RESUMO: PIPELINE + ANALYTICS + WFP (Evolução Completa 2026-2029)         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  2026 - ANO DOS DADOS                                                      │
│  ════════════════════════════════════════════════════════════════════════  │
│                                                                             │
│  Q2 2026 (v2.0)                                                            │
│  🔄 PIPELINE INTELLIGENCE + 🏢 WFP BÁSICO (início)                          │
│  ├── Pipeline: Automação proativa + nurturing + shortlists                 │
│  ├── WFP: Org chart + headcount (gratuito, coleta dados)                  │
│  └── Pricing: Pipeline R$ 500-4.000/mês | WFP gratuito                     │
│                                                                             │
│  Q3-Q4 2026 (v2.5-v3.0)                                                    │
│  📊 ANALYTICS PREMIUM + 🏢 WFP BÁSICO (completo)                           │
│  ├── Analytics: Dashboards + predictions + insights                        │
│  ├── WFP: + Turnover + hiring plan + skills inventory                     │
│  └── Pricing: Analytics R$ 300-2.000/mês | WFP continua gratuito           │
│                                                                             │
│  2027 - ANO DO UPSELL                                                      │
│  ════════════════════════════════════════════════════════════════════════  │
│                                                                             │
│  📈 WFP PROFESSIONAL (Primeiro tier pago)                                  │
│  ├── Features: Succession, scenarios, skills gap, HRIS sync               │
│  ├── Target: Clientes que já usam WFP Básico e querem mais                │
│  └── Pricing: R$ 500-1.500/mês                                             │
│                                                                             │
│  2028-2029 - ANO DA EXPANSÃO                                               │
│  ════════════════════════════════════════════════════════════════════════  │
│                                                                             │
│  🏆 WFP ENTERPRISE (Plataforma de mercado)                                 │
│  ├── Features: Strategic WFP, AI forecasting, org design, M&A             │
│  ├── Compete com: Workday, SAP SuccessFactors, Visier, ChartHop           │
│  └── Pricing: R$ 3.000-15.000/mês                                          │
│                                                                             │
│  💰 PROJEÇÃO DE REVENUE (add-ons + WFP)                                    │
│  ├── 2026: R$ 360k (Pipeline + Analytics + Mapping)                       │
│  ├── 2027: R$ 1.32M (+ WFP Professional)                                  │
│  ├── 2028: R$ 2.49M (+ WFP Enterprise início)                             │
│  └── 2029: R$ 3.92M (WFP Enterprise escala)                               │
│                                                                             │
│  🎯 VALOR ESTRATÉGICO DO WFP                                               │
│  ├── Básico (gratuito): Gera dados, aumenta stickiness, reduz churn       │
│  ├── Professional: Nova linha de receita, diferencial vs Gupy             │
│  └── Enterprise: Compete em novo mercado (WFP), ARR adicional R$1M+       │
│                                                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# Seção 34: Dimensionamento de Time e Estratégia de Desenvolvimento

## 34.1 Situação Atual do Time

### 34.1.1 Composição Atual (Q4 2025)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TIME ATUAL - 5 PESSOAS (4.5 FTE)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         FOUNDER/CEO                                  │   │
│  │                                                                      │   │
│  │  ESTRATÉGIA & NEGÓCIO           PRODUTO & TECNOLOGIA                │   │
│  │  ├── Comercial/Vendas           ├── Product Management (PM)         │   │
│  │  ├── Marketing                  ├── Design/UX                       │   │
│  │  ├── Planejamento               ├── Prototipagem (Vibe Coding)      │   │
│  │  └── Novos Negócios             ├── Novas Tecnologias               │   │
│  │                                 └── Novos Produtos                  │   │
│  │                                                                      │   │
│  │  QUALIDADE (quando necessário)                                      │   │
│  │  └── QA (validação de protótipos e releases)                        │   │
│  │                                                                      │   │
│  │                      (~1 FTE distribuído em múltiplas funções)       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                         │
│          ┌────────────────────────┼────────────────────────┐               │
│          ▼                        ▼                        ▼               │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐         │
│  │   TECH LEAD      │  │   FRONTEND       │  │   BACKEND        │         │
│  │                  │  │                  │  │                  │         │
│  │  • Arquitetura   │  │  • Vue.js/React  │  │  • Rails/FastAPI │         │
│  │  • Code Review   │  │  • UI/UX impl    │  │  • LangGraph     │         │
│  │  • DevOps        │  │  • Integrações   │  │  • PostgreSQL    │         │
│  │  • Mentoring     │  │  • Performance   │  │  • APIs          │         │
│  │                  │  │                  │  │                  │         │
│  │      1 FTE       │  │      1 FTE       │  │      1 FTE       │         │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘         │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │              HEAD DE CUSTOMER SUCCESS & IMPLEMENTAÇÃO                │   │
│  │              (Gerente Sênior / Head)                                 │   │
│  │                                                                      │   │
│  │  IMPLEMENTAÇÃO                  RELACIONAMENTO                       │   │
│  │  ├── Onboarding de clientes     ├── Suporte ao cliente              │   │
│  │  ├── Setup e configuração       ├── Gestão de relacionamento        │   │
│  │  ├── Treinamento de usuários    ├── Coleta de feedback              │   │
│  │  └── Acompanhamento go-live     ├── Upsell/Cross-sell               │   │
│  │                                 └── Renovações e churn prevention    │   │
│  │                                                                      │   │
│  │  SUCESSO DO CLIENTE                                                  │   │
│  │  ├── Health score monitoring    ├── QBRs (Quarterly Business Review)│   │
│  │  ├── Adoção de features         └── Advocacy e referências          │   │
│  │  └── Métricas de valor entregue                                     │   │
│  │                                                                      │   │
│  │                              1 FTE                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TOTAL EFETIVO: 5 pessoas (4.5 FTEs)                                       │
│  ├── 1 Founder/CEO (múltiplas funções)                                     │
│  ├── 3 Técnicos (Tech Lead, Frontend, Backend)                             │
│  └── 1 Head de CS & Implementação                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 34.1.2 Detalhamento das Funções do Founder/CEO

| Área | Atividades | % Tempo | Foco |
|------|------------|---------|------|
| **Comercial/Vendas** | Prospecção, demos, negociação, fechamento | 15% | Receita |
| **Marketing** | Posicionamento, conteúdo, eventos, comunidade | 10% | Awareness |
| **Planejamento** | OKRs, roadmap, budget, métricas | 10% | Direção |
| **Product Management** | Backlog, priorização, specs, validação | 15% | Produto |
| **Design/UX** | Wireframes, protótipos, design system | 15% | Experiência |
| **Prototipagem** | Vibe coding, Replit, validação técnica | 15% | Velocidade |
| **Novas Tecnologias** | Pesquisa AI, ferramentas, benchmarks | 10% | Inovação |
| **Novos Produtos** | Pipeline Intelligence, Analytics Premium | 5% | Expansão |
| **QA (ad-hoc)** | Validação de releases, smoke tests | 5% | Qualidade |

### 34.1.3 Detalhamento do Head de CS & Implementação

| Área | Atividades | Métricas |
|------|------------|----------|
| **Onboarding** | Setup técnico, migração de dados, configuração | Time-to-value < 2 semanas |
| **Treinamento** | Workshops, tutoriais, documentação | Adoption rate > 80% |
| **Suporte** | Tickets, chat, calls de suporte | Response time < 4h, CSAT > 4.5 |
| **Relacionamento** | Check-ins mensais, QBRs trimestrais | NPS > 50 |
| **Retenção** | Churn prevention, renovações, health monitoring | Churn < 5% anual |
| **Expansão** | Identificar upsell, cross-sell, referências | NRR > 110% |

### 34.1.4 Gaps Identificados

| Área | Responsável Atual | Gap | Impacto |
|------|-------------------|-----|---------|
| **Design dedicado** | Founder (parcial) | Sem designer full-time | Velocidade de iteração UI |
| **QA/Testes** | Founder + Todos (ad-hoc) | Sem QA dedicado | Bugs em produção |
| **DevOps/SRE** | Tech Lead (parcial) | Automação limitada | Deploy manual, downtime |
| **Data/Analytics** | Ninguém | Sem especialista ML | Analytics atrasado |
| **PM dedicado** | Founder (parcial) | Founder sobrecarregado | Backlog crescente |
| **Vendas dedicadas** | Founder (parcial) | Comercial dividido | Pipeline de vendas limitado |

### 34.1.5 Capacidade de Delivery Atual

| Métrica | Valor Atual | Benchmark Ideal |
|---------|-------------|-----------------|
| Story points/sprint | ~20-25 | 40-50 |
| Features/mês | 2-3 | 5-6 |
| Bug fix turnaround | 48-72h | < 24h |
| Time-to-prototype | 2-3 semanas | 3-5 dias |
| Code review backlog | 5-8 PRs | < 3 PRs |

---

## 34.2 Estratégia Dual: Tradicional vs Vibe Coding

### 34.2.1 Definição de Vibe Coding

**Vibe Coding** é uma metodologia de desenvolvimento assistido por IA onde:
- Ferramentas como Cursor, Replit Agent, Claude e GPT-4 aceleram prototipagem
- O desenvolvedor guia a IA com prompts de alto nível ("vibe")
- Código é gerado, iterado e refinado em ciclos rápidos
- Conversão para produção requer validação humana

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUXO TRADICIONAL vs VIBE CODING                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TRADICIONAL (4-6 semanas por feature)                                     │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐               │
│  │Spec  │→ │Design│→ │Dev   │→ │Review│→ │QA    │→ │Deploy│               │
│  │1 sem │  │1 sem │  │2 sem │  │1 sem │  │0.5sem│  │0.5sem│               │
│  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘               │
│                                                                             │
│  VIBE CODING (1-2 semanas por feature)                                     │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────┐  │
│  │ Prompt + Prototype   │→ │ Iterate + Validate   │→ │ Convert + Deploy │  │
│  │ 2-3 dias (AI-assist) │  │ 3-5 dias (AI + Human)│  │ 3-5 dias (Human) │  │
│  └──────────────────────┘  └──────────────────────┘  └──────────────────┘  │
│                                                                             │
│  REDUÇÃO: 60-70% no tempo de prototipagem                                  │
│  TRADE-OFF: Requer conversão cuidadosa para produção                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 34.2.2 Quando Usar Cada Abordagem

| Cenário | Abordagem | Justificativa |
|---------|-----------|---------------|
| **Novo componente UI** | Vibe Coding | Iteração rápida visual |
| **Lógica de negócio crítica** | Tradicional | Requer testes rigorosos |
| **Prototipagem de features** | Vibe Coding | Validação rápida com stakeholders |
| **Integração com APIs externas** | Híbrido | AI gera boilerplate, humano valida |
| **Arquitetura de agentes** | Tradicional | Complexidade alta, debug difícil |
| **Landing pages/marketing** | Vibe Coding | Rápido e descartável |
| **Sistema de pagamentos** | Tradicional | Segurança crítica |
| **Dashboard de métricas** | Vibe Coding | Muita visualização, lógica simples |

### 34.2.3 Stack de Vibe Coding Recomendado

| Ferramenta | Uso | Custo Mensal |
|------------|-----|--------------|
| **Replit Agent** | Prototipagem full-stack, design system | $25-50/usuário |
| **Cursor Pro** | Dev local com AI, refactoring | $20/usuário |
| **Claude Pro** | Prompts complexos, arquitetura | $20/usuário |
| **v0 by Vercel** | Componentes React/shadcn | $20/usuário |
| **Figma + Anima** | Design to code | $15/usuário |
| **GitHub Copilot** | Autocomplete, boilerplate | $19/usuário |

**Custo total/dev:** ~$120/mês (vs $0 tradicional) = **R$ 720/mês**

**ROI esperado:** 3-4x velocidade em tarefas de prototipagem = **break-even com 1-2 features/mês**

---

## 34.3 Modelo Híbrido: Design System Factory

### 34.3.1 Conceito

O **Design System Factory** é a estratégia atual da WeDOTalent:
- **Replit** = Fábrica de protótipos e design tokens (Next.js + React)
- **Rails + Vue** = Sistema de produção (validado, escalável)
- **Export** = Tokens CSS, especificações, componentes convertidos

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     DESIGN SYSTEM FACTORY WORKFLOW                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                    REPLIT (FÁBRICA)                                 │    │
│  │                                                                     │    │
│  │  Founder + AI Agents (Cursor, Replit Agent, Claude)                │    │
│  │                          │                                          │    │
│  │                          ▼                                          │    │
│  │  ┌──────────────────────────────────────────────────────────────┐  │    │
│  │  │  Protótipos Rápidos (Next.js + shadcn + Tailwind)           │  │    │
│  │  │  • Telas completas em 2-3 dias                               │  │    │
│  │  │  • Componentes interativos                                   │  │    │
│  │  │  • Validação visual com stakeholders                         │  │    │
│  │  └──────────────────────────────────────────────────────────────┘  │    │
│  │                          │                                          │    │
│  │                          ▼ EXPORT                                   │    │
│  │  ┌──────────────────────────────────────────────────────────────┐  │    │
│  │  │  Artefatos Exportáveis:                                      │  │    │
│  │  │  • design-tokens.css (cores, espaçamentos, tipografia)       │  │    │
│  │  │  • tailwind.config.ts (configuração extendida)               │  │    │
│  │  │  • Especificações de componentes (props, states, variantes)  │  │    │
│  │  │  • Screenshots de referência (pixel-perfect)                 │  │    │
│  │  │  • Documentação de padrões UI/UX                             │  │    │
│  │  └──────────────────────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                   │                                         │
│                                   ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                   RAILS + VUE (PRODUÇÃO)                           │    │
│  │                                                                     │    │
│  │  Frontend Dev implementa baseado nos artefatos exportados          │    │
│  │                          │                                          │    │
│  │                          ▼                                          │    │
│  │  ┌──────────────────────────────────────────────────────────────┐  │    │
│  │  │  Implementação Production-Ready                              │  │    │
│  │  │  • Componentes Vue.js + shadcn-vue                           │  │    │
│  │  │  • Integração com backend Rails                              │  │    │
│  │  │  • Testes E2E                                                │  │    │
│  │  │  • Performance otimizada                                     │  │    │
│  │  └──────────────────────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  VELOCIDADE: Prototipagem 3-4x mais rápida                                 │
│  QUALIDADE: Produção mantém padrões enterprise                             │
│  SEPARAÇÃO: Founder foca em visão, dev foca em execução                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 34.3.2 Divisão de Responsabilidades

| Papel | Replit (Factory) | Rails/Vue (Produção) |
|-------|------------------|----------------------|
| **Founder** | 80% tempo: prototipagem, design, PRD | 20% tempo: validação, feedback |
| **Frontend** | 10% tempo: review de specs | 90% tempo: implementação Vue |
| **Backend** | 0% tempo | 100% tempo: APIs, agentes, banco |
| **Tech Lead** | 20% tempo: arquitetura, review | 80% tempo: mentoring, DevOps |

### 34.3.3 Métricas de Eficiência

| Métrica | Antes (Tradicional) | Depois (Factory) | Melhoria |
|---------|---------------------|------------------|----------|
| Tempo para protótipo | 2-3 semanas | 3-5 dias | **3-4x** |
| Iterações de design | 5-8 ciclos | 2-3 ciclos | **2-3x** |
| Comunicação design→dev | Figma + reuniões | Código + tokens | **-50% overhead** |
| Features/mês (time atual) | 2-3 | 4-6 | **2x** |

---

## 34.4 Roadmap de Crescimento do Time

### 34.4.1 Timeline de Contratações

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ROADMAP DE CRESCIMENTO DO TIME                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  HOJE (Q4 2025) - 5 pessoas                                                │
│  ├── Founder/CEO (múltiplas funções: Comercial, Marketing, PM, Design,    │
│  │               Prototipagem, Planejamento, Novas Tecnologias, QA)        │
│  ├── Tech Lead                                                             │
│  ├── Frontend Dev                                                          │
│  ├── Backend Dev                                                           │
│  └── Head de CS & Implementação (suporte, onboarding, relacionamento)     │
│                                                                             │
│  v1.0 MVP (Q1 2026) - 6 pessoas (+1)                                       │
│  └── +1 Backend (LangGraph specialist)                                     │
│      Justificativa: Agentes são core do produto                            │
│                                                                             │
│  v1.5 GA (Q2 2026) - 8 pessoas (+2)                                        │
│  ├── +1 QA Engineer (automação de testes)                                  │
│  └── +1 DevOps/SRE (CI/CD, observabilidade)                                │
│      Justificativa: Qualidade e estabilidade para GA                       │
│                                                                             │
│  v2.0 Pipeline Intelligence (Q3 2026) - 10 pessoas (+2)                    │
│  ├── +1 Data Engineer (nurturing, analytics base)                          │
│  └── +1 Product Manager (Founder libera tempo para estratégia)             │
│      Justificativa: Escala produto + dados                                 │
│                                                                             │
│  v2.5 Analytics Premium (Q4 2026) - 12 pessoas (+2)                        │
│  ├── +1 ML Engineer (modelos preditivos)                                   │
│  └── +1 Frontend (dashboards analytics)                                    │
│      Justificativa: ML para analytics + capacidade de entrega              │
│                                                                             │
│  v3.0 Enterprise (Q1 2027) - 15 pessoas (+3)                               │
│  ├── +1 Backend (integrações ATS)                                          │
│  ├── +1 CS adicional (escala de clientes enterprise)                       │
│  └── +1 Sales/Account Executive (vendas dedicadas)                         │
│      Justificativa: Enterprise requer integrações + vendas + suporte       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 34.4.2 Estrutura Organizacional Projetada

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                ESTRUTURA ORGANIZACIONAL - v3.0 (Q1 2027)                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                           ┌──────────────┐                                 │
│                           │   FOUNDER    │                                 │
│                           │   CEO/CPO    │                                 │
│                           └──────┬───────┘                                 │
│                                  │                                          │
│       ┌──────────────────────────┼──────────────────────────┐              │
│       │                          │                          │              │
│       ▼                          ▼                          ▼              │
│  ┌─────────────┐        ┌───────────────┐        ┌─────────────────┐       │
│  │  PRODUTO    │        │  ENGENHARIA   │        │ COMERCIAL & CS  │       │
│  └──────┬──────┘        └───────┬───────┘        └────────┬────────┘       │
│         │                       │                         │                │
│         ▼                       ▼                         ▼                │
│  ┌─────────────┐        ┌─────────────┐        ┌─────────────────────┐     │
│  │ PM          │        │ Tech Lead   │        │ Head CS & Implement │     │
│  │ 1 pessoa    │        │ 1 pessoa    │        │ 1 pessoa            │     │
│  └─────────────┘        └──────┬──────┘        └──────────┬──────────┘     │
│                                │                          │                │
│                 ┌──────────────┼──────────────┐           │                │
│                 │              │              │           │                │
│                 ▼              ▼              ▼           ▼                │
│         ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐         │
│         │ FRONTEND   │ │ BACKEND    │ │ DATA/ML    │ │ CS Jr    │         │
│         │ 2 pessoas  │ │ 3 pessoas  │ │ 2 pessoas  │ │ 1 pessoa │         │
│         └────────────┘ └────────────┘ └────────────┘ └──────────┘         │
│                                │                                           │
│                         ┌──────┴──────┐                                    │
│                         ▼             ▼                                    │
│                  ┌────────────┐ ┌────────────┐                             │
│                  │ QA         │ │ DevOps/SRE │                             │
│                  │ 1 pessoa   │ │ 1 pessoa   │                             │
│                  └────────────┘ └────────────┘                             │
│                                                                             │
│  VENDAS:                                                                   │
│  ┌────────────────┐                                                        │
│  │ AE (Account    │                                                        │
│  │ Executive)     │                                                        │
│  │ 1 pessoa       │                                                        │
│  └────────────────┘                                                        │
│                                                                             │
│  TOTAL: 15 pessoas                                                         │
│  ├── 11 Técnicos (Tech Lead, 2 Frontend, 3 Backend, 2 Data/ML, QA, DevOps)│
│  ├── 1 PM                                                                  │
│  ├── 2 CS (Head + Jr)                                                      │
│  └── 1 AE                                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 34.4.3 Ranges Salariais por Cargo

#### Estrutura Compacta: AI Engineer Híbrido

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              MODELO COMPACTO: 2 AI ENGINEERS COM ESCOPO AMPLIADO            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FILOSOFIA: Mais devs de plataforma + menos especialistas de IA            │
│  ├── Foco: Construir produto sólido (Rails/Vue) + IA como diferencial      │
│  ├── 2 AI Engineers cobrem: Agentes + Data + ML (escopo full-stack AI)     │
│  └── Sem Account Executive: Founder faz vendas até escalar                 │
│                                                                             │
│  AI ENGINEER (ESCOPO HÍBRIDO) - 2 profissionais                            │
│  ├── Fase 1 (v1.0-v1.5): Agentes LangGraph, Claude API, prompts            │
│  ├── Fase 2 (v2.0): Pipelines de dados, ETL, métricas                      │
│  ├── Fase 3 (v2.5): Modelos preditivos básicos, embeddings                 │
│  ├── Skills: LangGraph + SQL + Python + básico de ML                       │
│  └── Perfil: Generalista de IA, não especialista                           │
│                                                                             │
│  DIVISÃO RECOMENDADA DOS 2 AI ENGINEERS:                                   │
│  ├── AI Engineer 1: Foco em agentes conversacionais (LIA core)             │
│  │   └── Job Intake, Sourcing, Screening, Scheduling agents                │
│  └── AI Engineer 2: Foco em dados e analytics                              │
│      └── Pipeline Intelligence, dashboards, modelos simples                │
│                                                                             │
│  QUANDO ESPECIALIZAR (contratar Data/ML dedicado):                         │
│  ├── Volume: > 50 clientes ativos OU                                       │
│  ├── Dados: > 100k candidatos processados OU                               │
│  ├── Revenue: MRR > R$ 300k OU                                             │
│  └── Tempo: 18+ meses de operação com dados                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Cargos Técnicos

| Cargo | Escopo de Atuação | Nível | Salário Base | Custo Total* |
|-------|-------------------|-------|--------------|--------------|
| **Tech Lead** | Arquitetura geral, code review, mentoria, decisões técnicas, DevOps básico | Sênior | R$ 15.000 - 25.000 | R$ 27.000 - 45.000 |
| **Backend Developer** | APIs Rails/FastAPI, integrações ATS (Gupy, Pandapé), CRUD, autenticação | Pleno | R$ 10.000 - 15.000 | R$ 18.500 - 28.000 |
| **Backend Developer** | Arquitetura de serviços, performance, cache, filas, microsserviços | Sênior | R$ 15.000 - 22.000 | R$ 27.000 - 40.000 |
| **AI Engineer (Híbrido)** | Agentes LangGraph, prompts, Claude API, pipelines de dados, analytics, modelos básicos ML | Sênior | R$ 15.000 - 25.000 | R$ 27.000 - 45.000 |
| **Frontend Developer** | Componentes Vue/React, UI responsiva, integração APIs, shadcn/Tailwind | Pleno | R$ 8.000 - 12.000 | R$ 15.000 - 22.000 |
| **Frontend Developer** | Arquitetura frontend, state management, performance, design system | Sênior | R$ 12.000 - 18.000 | R$ 22.000 - 33.000 |
| **DevOps/SRE** | CI/CD, infraestrutura cloud, monitoramento, segurança, escalabilidade | Pleno/Sênior | R$ 12.000 - 20.000 | R$ 22.000 - 36.000 |
| **QA Engineer** | Testes automatizados, QA de agentes IA, validação de fluxos conversacionais | Pleno | R$ 8.000 - 12.000 | R$ 15.000 - 22.000 |

#### Cargos Especializados (Futuro - Após Trigger de Escala)

| Cargo | Escopo de Atuação | Trigger de Contratação | Salário Base | Custo Total* |
|-------|-------------------|------------------------|--------------|--------------|
| **Data Engineer** | Pipelines ETL, data warehouse, dbt, dashboards BI | > 50 clientes OU MRR > R$ 300k | R$ 12.000 - 20.000 | R$ 22.000 - 36.000 |
| **ML Engineer** | Modelos preditivos, feature engineering, MLOps | > 100k candidatos + 18 meses de dados | R$ 18.000 - 30.000 | R$ 32.000 - 53.000 |
| **Product Manager** | Discovery, roadmap, backlog, métricas de produto | > 30 clientes OU time > 8 pessoas | R$ 12.000 - 22.000 | R$ 22.000 - 40.000 |

#### Cargos de Customer Success

| Cargo | Escopo de Atuação | Nível | Salário Base | Custo Total* |
|-------|-------------------|-------|--------------|--------------|
| **Customer Success Manager** | Onboarding, implementação, suporte, treinamentos, health score, retenção, upsell, QBRs | Pleno/Sênior | R$ 11.000 - 17.000 | R$ 20.000 - 30.000 |
| **CS Junior** | Suporte nível 1, tickets, documentação, onboarding básico | Júnior | R$ 4.000 - 7.000 | R$ 8.000 - 14.000 |

*Custo Total = Salário + Encargos (~70%) + Benefícios (~R$ 1.500/mês) + Ferramentas (~R$ 500/mês)

**Nota:** Sem Account Executive - Founder mantém função comercial até MRR > R$ 200k

---

### 34.4.4 Critérios de Escala: Quando Expandir o Time (Conservador)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              TRIGGERS CONSERVADORES PARA EXPANSÃO DO TIME                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FILOSOFIA: Crescer devagar, validar produto, escalar com segurança        │
│  ├── Foco técnico nas fases 1-3 (construir produto sólido)                 │
│  ├── Foco comercial/operacional nas fases 4-6 (escalar receita)            │
│  └── Estrutura compacta sustentável por 18-24 meses                        │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  FASE 1-3: FOCO EM PRODUTO (0-50 clientes)                          │   │
│  │  ├── Prioridade: Estabilidade técnica, features core                │   │
│  │  ├── Founder: 60% produto, 30% vendas, 10% operações               │   │
│  │  └── CSM: Cobre todo relacionamento com clientes                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  FASE 4-6: FOCO EM ESCALA (50-150+ clientes)                        │   │
│  │  ├── Prioridade: Vendas, CS, operações financeiras                  │   │
│  │  ├── Founder: 20% produto, 50% vendas, 30% estratégia              │   │
│  │  └── Time de suporte: Comercial + CS + Financeiro                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SINAIS DE SOBRECARGA (ACELERAR CONTRATAÇÃO):                              │
│  ├── Cycle time > 4 semanas: +1 dev                                       │
│  ├── Bugs críticos > 5/mês: +1 QA                                         │
│  ├── Downtime > 4h/mês: +1 DevOps                                         │
│  ├── Churn > 8%: +1 CS                                                    │
│  ├── Pipeline > 30 leads/mês sem conversão: +1 Comercial                  │
│  └── Founder > 60% operacional: Urgente estruturar                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Roadmap de Contratação Conservador

| Fase | Trigger (Clientes) | Trigger (MRR) | Contratação | Time Total | Custo/mês |
|------|-------------------|---------------|-------------|------------|-----------|
| **Atual** | Baseline | — | Founder, Tech Lead, Frontend, Backend, CSM | 5 | ~R$ 85k |
| **Fase 1** | 25 clientes | R$ 75k | +1 AI Engineer | 6 | ~R$ 110k |
| **Fase 2** | 40 clientes | R$ 120k | +1 QA | 7 | ~R$ 125k |
| **Fase 3** | 60 clientes | R$ 180k | +1 DevOps + 1 Backend | 9 | ~R$ 170k |
| **Fase 4** | 80 clientes | R$ 250k | +1 CS Jr + 1 SDR/BDR + 1 Financeiro Jr | 12 | ~R$ 210k |
| **Fase 5** | 100 clientes | R$ 350k | +1 AE + 1 AI Engineer + 1 PM | 15 | ~R$ 280k |
| **Fase 6** | 150 clientes | R$ 500k | +1 CS Sênior + 1 Data Engineer + 1 Frontend | 18 | ~R$ 350k |

#### Detalhamento por Fase

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DETALHAMENTO DAS FASES DE CRESCIMENTO                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FASE ATUAL (5 pessoas) - ATÉ 25 CLIENTES                                  │
│  ├── Founder/CEO: Produto, Vendas, Design, Prototipagem                    │
│  ├── Tech Lead: Arquitetura, DevOps básico, Code Review                    │
│  ├── Frontend Dev: Vue/React, UI                                           │
│  ├── Backend Dev: Rails/FastAPI, APIs                                      │
│  └── CSM: Onboarding, Suporte, Retenção                                    │
│      Custo: ~R$ 85k/mês | Duração estimada: 6-12 meses                     │
│                                                                             │
│  FASE 1 (6 pessoas) - 25 A 40 CLIENTES                                     │
│  └── +1 AI Engineer: Agentes LangGraph, orquestrador, prompts              │
│      Custo: ~R$ 110k/mês | Duração estimada: 6-9 meses                     │
│                                                                             │
│  FASE 2 (7 pessoas) - 40 A 60 CLIENTES                                     │
│  └── +1 QA Engineer: Testes, qualidade de agentes IA                       │
│      Custo: ~R$ 125k/mês | Duração estimada: 6-9 meses                     │
│                                                                             │
│  FASE 3 (9 pessoas) - 60 A 80 CLIENTES                                     │
│  ├── +1 DevOps/SRE: CI/CD, infra, monitoramento                            │
│  └── +1 Backend Dev: Integrações ATS, APIs, performance                    │
│      Custo: ~R$ 170k/mês | Duração estimada: 6-12 meses                    │
│                                                                             │
│  ════════════════════════════════════════════════════════════════════════  │
│  A PARTIR DAQUI: FOCO EM ESCALA COMERCIAL E OPERACIONAL                    │
│  ════════════════════════════════════════════════════════════════════════  │
│                                                                             │
│  FASE 4 (12 pessoas) - 80 A 100 CLIENTES                                   │
│  ├── +1 CS Junior: Suporte N1, tickets, onboarding básico                  │
│  ├── +1 SDR/BDR: Prospecção, qualificação de leads, agendamento           │
│  └── +1 Financeiro Jr: Faturamento, cobrança, conciliação, NFs            │
│      Custo: ~R$ 210k/mês | Duração estimada: 6-12 meses                    │
│                                                                             │
│  FASE 5 (15 pessoas) - 100 A 150 CLIENTES                                  │
│  ├── +1 Account Executive: Fechamento, negociação enterprise              │
│  ├── +1 AI Engineer: 2º AI para analytics/modelos                         │
│  └── +1 Product Manager: Roadmap, discovery, stakeholders                 │
│      Custo: ~R$ 280k/mês | Duração estimada: 12+ meses                     │
│                                                                             │
│  FASE 6 (18 pessoas) - 150+ CLIENTES                                       │
│  ├── +1 CS Sênior: Contas enterprise, expansão, renovações                │
│  ├── +1 Data Engineer: Pipelines, BI, dashboards avançados                │
│  └── +1 Frontend Dev: Novas features, design system                       │
│      Custo: ~R$ 350k/mês | Escala contínua                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Cargos Comerciais e Operacionais (Fases 4-6)

| Cargo | Escopo de Atuação | Nível | Salário Base | Custo Total* |
|-------|-------------------|-------|--------------|--------------|
| **SDR/BDR** | Prospecção outbound, qualificação de leads, agendamento de demos | Júnior/Pleno | R$ 4.000 - 8.000 | R$ 8.000 - 15.000 |
| **Account Executive** | Fechamento de vendas, negociação, propostas, contratos | Pleno/Sênior | R$ 10.000 - 18.000 | R$ 18.000 - 32.000 |
| **Financeiro Jr** | Faturamento, cobrança, conciliação bancária, NFs, contas a pagar/receber | Júnior | R$ 3.500 - 6.000 | R$ 7.000 - 12.000 |
| **Analista Financeiro** | Controladoria, budget, forecast, relatórios gerenciais | Pleno | R$ 6.000 - 10.000 | R$ 12.000 - 18.000 |

*Nota: AE geralmente tem variável de 20-40% sobre salário base em comissões*

#### Observações sobre Remuneração

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    NOTAS SOBRE POLÍTICA SALARIAL                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FATORES QUE INFLUENCIAM O RANGE:                                          │
│  ├── Localização: SP capital (+20%), remoto nacional (base), remoto        │
│  │                internacional (USD/EUR)                                   │
│  ├── Senioridade: Anos de experiência + complexidade de projetos           │
│  ├── Skills específicos: LangGraph, Claude API, LLM (+15-25%)              │
│  └── Mercado aquecido: IA/ML e DevOps com prêmio de 20-30%                 │
│                                                                             │
│  COMPOSIÇÃO DO CUSTO TOTAL (~70% encargos + benefícios):                   │
│  ├── INSS patronal: 20%                                                    │
│  ├── FGTS: 8%                                                              │
│  ├── 13º salário: 8.33%                                                    │
│  ├── Férias + 1/3: 11.11%                                                  │
│  ├── Provisão rescisão: 4-8%                                               │
│  ├── Benefícios (VR, VT, saúde): R$ 1.000-2.000/mês                        │
│  └── Ferramentas (licenças, equipamento): R$ 300-800/mês                   │
│                                                                             │
│  MODELO DE CONTRATAÇÃO RECOMENDADO:                                        │
│  ├── CLT: Tech Lead, PM, Head CS (estabilidade, cultura)                   │
│  ├── PJ: Devs seniores, ML Engineers (flexibilidade, custo)                │
│  └── Híbrido: Começar PJ, migrar CLT após 6 meses                          │
│                                                                             │
│  VARIÁVEL/BÔNUS:                                                           │
│  ├── AE: Comissão 10-20% sobre vendas fechadas                             │
│  ├── CS: Bônus 5-10% por NRR e retenção                                    │
│  └── Tech: PLR anual de 1-2 salários por metas                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 34.4.4 Custo de Time por Fase

| Fase | Headcount | Custo Médio/Pessoa | Custo Mensal | Custo Anual |
|------|-----------|-------------------|--------------|-------------|
| **Atual (Q4 2025)** | 5 | R$ 18.000 | R$ 90.000 | R$ 1.080.000 |
| **v1.0 (Q1 2026)** | 6 | R$ 18.000 | R$ 108.000 | R$ 1.296.000 |
| **v1.5 (Q2 2026)** | 8 | R$ 17.500 | R$ 140.000 | R$ 1.680.000 |
| **v2.0 (Q3 2026)** | 10 | R$ 17.000 | R$ 170.000 | R$ 2.040.000 |
| **v2.5 (Q4 2026)** | 12 | R$ 16.500 | R$ 198.000 | R$ 2.376.000 |
| **v3.0 (Q1 2027)** | 15 | R$ 16.000 | R$ 240.000 | R$ 2.880.000 |

### 34.4.5 Detalhamento do Custo Atual (5 pessoas)

| Cargo | Salário Base | Custo Total | % do Total |
|-------|--------------|-------------|------------|
| **Founder/CEO** | Pro-labore R$ 15.000 | R$ 18.000 | 20% |
| **Tech Lead** | R$ 20.000 | R$ 35.000 | 39% |
| **Frontend Dev (Pleno)** | R$ 10.000 | R$ 18.000 | 20% |
| **Backend Dev (Pleno)** | R$ 10.000 | R$ 18.000 | 20% |
| **Head CS (Ger. Sênior)** | - | - | - |
| **TOTAL** | - | **R$ 89.000** | 100% |

*Nota: Ajustar valores conforme contratação real do Head CS*

---

## 34.5 Cenários Comparativos: Tradicional vs Vibe Coding

### 34.5.1 Cenário A: Desenvolvimento 100% Tradicional

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              CENÁRIO A: DESENVOLVIMENTO TRADICIONAL                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PREMISSAS:                                                                 │
│  • Sem ferramentas AI de prototipagem                                      │
│  • Ciclo completo: spec → design → dev → review → QA → deploy              │
│  • Founder precisa de designer dedicado                                    │
│                                                                             │
│  TIMELINE PARA v1.5 (GA):                                                  │
│  ├── Q4 2025: MVP parcial (40% features)                                   │
│  ├── Q1 2026: MVP completo + beta                                          │
│  ├── Q2 2026: Iterações + bugs                                             │
│  ├── Q3 2026: GA release                                                   │
│  └── Total: 12 meses até GA                                                │
│                                                                             │
│  HEADCOUNT NECESSÁRIO PARA MESMA VELOCIDADE:                               │
│  • +1 UI/UX Designer (R$ 12k/mês) = R$ 144k/ano                           │
│  • +1 Frontend adicional (R$ 15k/mês) = R$ 180k/ano                        │
│  • +0.5 QA adicional (R$ 6k/mês) = R$ 72k/ano                              │
│  • Total adicional: R$ 396k/ano                                            │
│                                                                             │
│  VELOCIDADE: 3-4 features/mês                                              │
│  CUSTO TIME (Q2 2026): ~R$ 170k/mês (10 pessoas)                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 34.5.2 Cenário B: Vibe Coding Intensivo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              CENÁRIO B: VIBE CODING INTENSIVO                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PREMISSAS:                                                                 │
│  • Founder + AI = Design System Factory                                    │
│  • Head CS já cuida de clientes (liberando Founder)                        │
│  • Prototipagem 3-4x mais rápida                                           │
│  • Conversão para produção requer 30-40% do tempo tradicional              │
│                                                                             │
│  TIMELINE PARA v1.5 (GA):                                                  │
│  ├── Q4 2025: Protótipos completos + MVP 60%                               │
│  ├── Q1 2026: MVP completo + conversão prod                                │
│  ├── Q2 2026: GA release                                                   │
│  └── Total: 8-9 meses até GA (25% mais rápido)                             │
│                                                                             │
│  HEADCOUNT NECESSÁRIO:                                                     │
│  • Time atual (5 pessoas incluindo Head CS) é suficiente até v1.0          │
│  • +1 Backend para v1.0 (agentes complexos)                                │
│  • +2 (QA + DevOps) para v1.5 (qualidade)                                  │
│  • Total: 8 pessoas para GA (vs 11 tradicional)                            │
│                                                                             │
│  CUSTO FERRAMENTAS AI:                                                     │
│  • Replit Pro: R$ 300/mês (Founder)                                        │
│  • Cursor Pro: R$ 120/mês/dev × 3 = R$ 360/mês                             │
│  • Claude Pro: R$ 120/mês × 2 = R$ 240/mês                                 │
│  • GitHub Copilot: R$ 115/mês/dev × 4 = R$ 460/mês                         │
│  • Total ferramentas: R$ 1.460/mês = R$ 17.520/ano                         │
│                                                                             │
│  VELOCIDADE: 5-7 features/mês                                              │
│  CUSTO TIME (Q2 2026): ~R$ 140k/mês (8 pessoas)                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 34.5.3 Comparativo de ROI

| Métrica | Tradicional | Vibe Coding | Diferença |
|---------|-------------|-------------|-----------|
| **Time-to-GA** | 12 meses | 8-9 meses | **-25%** |
| **Headcount para GA** | 11 pessoas | 8 pessoas | **-27%** |
| **Custo mensal (GA)** | R$ 190k | R$ 140k | **-26%** |
| **Custo anual time** | R$ 2.28M | R$ 1.68M | **-R$ 600k** |
| **Custo ferramentas AI** | R$ 0 | R$ 17.5k | +R$ 17.5k |
| **Features/mês** | 3-4 | 5-7 | **+75%** |
| **ROI líquido** | Baseline | +R$ 582k/ano | **+34%** |

### 34.5.4 Cenário Recomendado: Híbrido Otimizado

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              CENÁRIO RECOMENDADO: HÍBRIDO OTIMIZADO                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ESTRATÉGIA:                                                               │
│  ├── Vibe Coding para: UI/UX, protótipos, componentes, dashboards          │
│  ├── Tradicional para: agentes AI, integrações críticas, segurança         │
│  └── Factory Model: Replit exporta → Vue implementa                        │
│                                                                             │
│  DISTRIBUIÇÃO DE ESFORÇO:                                                  │
│  ├── 40% do código = Vibe Coding (UI, prototipagem)                        │
│  ├── 60% do código = Tradicional (backend, agentes, core)                  │
│  └── Conversão = 20% overhead (validação, testes)                          │
│                                                                             │
│  BENEFÍCIOS COMBINADOS:                                                    │
│  ├── Velocidade de prototipagem: 3-4x                                      │
│  ├── Qualidade de produção: mantida                                        │
│  ├── Custo de time: -20-25%                                                │
│  └── Time-to-market: -25%                                                  │
│                                                                             │
│  RISCOS MITIGADOS:                                                         │
│  ├── Código AI sem testes → QA automatizado                                │
│  ├── Dependência de ferramentas → Skills híbridos no time                  │
│  ├── Inconsistência design → Design tokens centralizados                   │
│  └── Dívida técnica → Code review rigoroso na conversão                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 34.6 Configuração de Ferramentas por Fase

### 34.6.1 Stack de Desenvolvimento

| Ferramenta | Atual | v1.5 | v2.5 | Custo/mês |
|------------|-------|------|------|-----------|
| **Replit Pro** | Founder | Founder + 1 dev | 2 devs | R$ 150-300/usuário |
| **Cursor Pro** | 1 dev | 4 devs | 6 devs | R$ 120/usuário |
| **Claude Pro** | Founder | 3 pessoas | 5 pessoas | R$ 120/usuário |
| **GitHub Copilot** | 4 devs | 7 devs | 11 devs | R$ 115/usuário |
| **v0 by Vercel** | Founder | 2 pessoas | 2 pessoas | R$ 120/usuário |
| **Figma** | Founder | 2 pessoas | 3 pessoas | R$ 90/usuário |
| **Linear** | Todo time | Todo time | Todo time | R$ 48/usuário |
| **Notion** | Todo time | Todo time | Todo time | R$ 48/usuário |
| **Slack/Discord** | Todo time | Todo time | Todo time | R$ 45/usuário |

### 34.6.2 Stack de Infraestrutura

| Ferramenta | Atual | v1.5 | v2.5 | Custo/mês |
|------------|-------|------|------|-----------|
| **Railway/Render** | Dev | Dev + Staging | Dev + Staging + Prod | R$ 100-500 |
| **Vercel** | — | Frontend | Frontend | R$ 100-300 |
| **PostgreSQL (Neon)** | 1 instância | 2 instâncias | 3 instâncias | R$ 100-400 |
| **Redis** | — | 1 instância | 2 instâncias | R$ 50-200 |
| **Sentry** | — | Starter | Team | R$ 130-500 |
| **LangSmith** | Free | Free | Team | R$ 0-2.000 |
| **Anthropic API** | Pay-as-you-go | $500/mês | $2.000/mês | R$ 2.500-10.000 |
| **AWS/GCP** | — | Mínimo | Standard | R$ 500-2.000 |

### 34.6.3 Custo Total de Ferramentas por Fase

| Fase | Ferramentas Dev | Infraestrutura | AI APIs | Total/mês | Total/ano |
|------|-----------------|----------------|---------|-----------|-----------|
| **Atual** | R$ 1.800 | R$ 500 | R$ 1.500 | R$ 3.800 | R$ 45.600 |
| **v1.0** | R$ 2.800 | R$ 1.200 | R$ 3.000 | R$ 7.000 | R$ 84.000 |
| **v1.5** | R$ 4.500 | R$ 2.500 | R$ 5.000 | R$ 12.000 | R$ 144.000 |
| **v2.0** | R$ 6.000 | R$ 4.000 | R$ 8.000 | R$ 18.000 | R$ 216.000 |
| **v2.5** | R$ 8.000 | R$ 6.000 | R$ 12.000 | R$ 26.000 | R$ 312.000 |

---

## 34.7 Práticas de Produtividade Máxima

### 34.7.1 Rituais de Time Enxuto

| Ritual | Frequência | Duração | Participantes |
|--------|------------|---------|---------------|
| **Daily standup** | Diário | 15 min | Todo time |
| **Sprint planning** | Quinzenal | 1h | Todo time |
| **Demo/Review** | Quinzenal | 30 min | Todo time + stakeholders |
| **1:1 Tech Lead** | Semanal | 30 min | Cada dev |
| **Design review** | 2x/semana | 30 min | Founder + Frontend |
| **Retro** | Mensal | 1h | Todo time |

### 34.7.2 Práticas de Código

| Prática | Implementação | Impacto |
|---------|---------------|---------|
| **Trunk-based development** | PRs pequenos, merge rápido | -50% tempo de review |
| **Feature flags** | LaunchDarkly/PostHog | Deploy sem risco |
| **Pair programming** | 2h/dia em tarefas complexas | +30% qualidade |
| **AI-assisted review** | Claude analisa PRs | -40% tempo de review |
| **Automated testing** | Jest + Playwright | -60% bugs em produção |
| **Continuous deployment** | GitHub Actions | Deploy em < 10 min |

### 34.7.3 Práticas de Vibe Coding

| Prática | Descrição | Resultado |
|---------|-----------|-----------|
| **Prompt library** | Biblioteca de prompts testados por contexto | Consistência |
| **Component catalog** | Catálogo de componentes AI-gerados aprovados | Reutilização |
| **Conversion checklist** | Checklist para converter código AI → produção | Qualidade |
| **AI pair sessions** | Sessões de 2h Founder + AI para protótipos | 3-4x velocidade |
| **Spec-to-prototype** | Specs escritos como prompts executáveis | Zero ambiguidade |
| **Screenshot validation** | Comparação pixel-perfect React vs Vue | Fidelidade |

---

## 34.8 Métricas de Sucesso do Time

### 34.8.1 KPIs de Produtividade

| Métrica | Atual | v1.0 Target | v1.5 Target | v2.0 Target |
|---------|-------|-------------|-------------|-------------|
| **Velocity (SP/sprint)** | 20-25 | 35-40 | 50-60 | 70-80 |
| **Cycle time (feature)** | 3-4 sem | 2 sem | 1.5 sem | 1 sem |
| **Lead time (idea→prod)** | 6-8 sem | 4 sem | 3 sem | 2 sem |
| **Deployment frequency** | 1x/semana | 2x/semana | Diário | Múltiplo/dia |
| **Change failure rate** | 20% | 15% | 10% | < 5% |
| **MTTR** | 24-48h | 12h | 4h | < 1h |

### 34.8.2 KPIs de Qualidade

| Métrica | Atual | v1.0 Target | v1.5 Target | v2.0 Target |
|---------|-------|-------------|-------------|-------------|
| **Test coverage** | 40% | 60% | 75% | 85% |
| **Bugs/sprint** | 8-10 | 5-6 | 3-4 | < 2 |
| **Tech debt ratio** | 25% | 20% | 15% | 10% |
| **Code review time** | 48h | 24h | 12h | < 6h |
| **AI code acceptance** | — | 60% | 70% | 80% |
| **NPS interno (devs)** | — | 7.0 | 8.0 | 8.5 |

### 34.8.3 KPIs de Vibe Coding

| Métrica | Descrição | Target |
|---------|-----------|--------|
| **Prototype-to-prod ratio** | % código do protótipo que vai para produção | 40-50% |
| **Prompt success rate** | % prompts que geram código utilizável | > 70% |
| **Conversion time** | Tempo para converter componente AI → prod | < 4h |
| **Reuse rate** | % componentes AI reutilizados em outras features | > 60% |
| **Design token compliance** | % código usando tokens vs hardcoded | > 95% |

---

## 34.9 Resumo Executivo - Dimensionamento de Time

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 RESUMO: ESTRATÉGIA DE TIME ENXUTO                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SITUAÇÃO ATUAL (5 PESSOAS)                                                │
│  ├── Founder/CEO: Comercial, Marketing, PM, Design, Prototipagem,          │
│  │               Planejamento, Novas Tecnologias, QA                       │
│  ├── Tech Lead: Arquitetura, Code Review, DevOps, Mentoring                │
│  ├── Frontend Dev: Vue.js/React, UI implementation                         │
│  ├── Backend Dev: Rails/FastAPI, LangGraph, APIs                           │
│  ├── Head CS & Implementação: Onboarding, Suporte, Relacionamento          │
│  ├── Velocidade: 2-3 features/mês                                          │
│  └── Custo: ~R$ 90k/mês                                                    │
│                                                                             │
│  ESTRATÉGIA: DESIGN SYSTEM FACTORY + VIBE CODING                           │
│  ├── Replit = Fábrica de protótipos (Founder + AI)                         │
│  ├── Rails/Vue = Produção enterprise (Time de devs)                        │
│  ├── Head CS = Libera Founder de suporte/clientes                          │
│  ├── Export = Design tokens, specs, componentes                            │
│  └── Resultado: 3-4x velocidade em prototipagem                            │
│                                                                             │
│  CRESCIMENTO PLANEJADO                                                     │
│  ├── v1.0 (Q1 2026): 6 pessoas (+1 Backend LangGraph)                      │
│  ├── v1.5 (Q2 2026): 8 pessoas (+1 QA, +1 DevOps)                          │
│  ├── v2.0 (Q3 2026): 10 pessoas (+1 Data, +1 PM)                           │
│  ├── v2.5 (Q4 2026): 12 pessoas (+1 ML, +1 Frontend)                       │
│  └── v3.0 (Q1 2027): 15 pessoas (+1 Backend, +1 CS Jr, +1 AE)              │
│                                                                             │
│  ROI DO VIBE CODING                                                        │
│  ├── Economia de headcount: -27% (8 vs 11 para GA)                         │
│  ├── Time-to-market: -25% (8-9 vs 12 meses)                                │
│  ├── Custo ferramentas AI: +R$ 17.5k/ano                                   │
│  ├── Economia líquida: ~R$ 582k/ano                                        │
│  └── ROI: 33x sobre investimento em ferramentas                            │
│                                                                             │
│  CONTRATAÇÕES PRIORITÁRIAS                                                 │
│  ├── 1º: Backend LangGraph (core product - agentes)                        │
│  ├── 2º: QA Engineer (qualidade para GA)                                   │
│  ├── 3º: DevOps/SRE (estabilidade e CI/CD)                                 │
│  ├── 4º: Data Engineer (Pipeline Intelligence)                             │
│  └── 5º: Product Manager (liberar Founder para estratégia)                 │
│                                                                             │
│  MÉTRICAS-CHAVE                                                            │
│  ├── Velocity: 20-25 → 70-80 SP/sprint (4x)                                │
│  ├── Features/mês: 2-3 → 8-10 (3-4x)                                       │
│  ├── Cycle time: 3-4 sem → 1 sem (-75%)                                    │
│  ├── Prototype-to-prod: 40-50% código reutilizado                          │
│  └── Churn: < 5% (Head CS garante sucesso do cliente)                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 35. AI Governance & Ethics (NOVO - Dezembro 2025)

> **✅ IMPLEMENTADO:** Framework de governança de IA seguindo princípios de responsabilidade e conformidade LGPD.

## 35.1 Critérios Protegidos (PROTECTED_CRITERIA)

A LIA é **proibida** de usar os seguintes critérios em qualquer decisão de recrutamento:

| # | Critério | Descrição | Risco Legal |
|---|----------|-----------|-------------|
| 1 | **Gênero** | Masculino, feminino, não-binário | Discriminação |
| 2 | **Raça/Etnia** | Qualquer origem racial ou étnica | Discriminação |
| 3 | **Idade** | Acima/abaixo de X anos | Discriminação etária |
| 4 | **Estado Civil** | Casado, solteiro, divorciado | Discriminação |
| 5 | **Orientação Sexual** | LGBTQIA+ | Discriminação |
| 6 | **Religião** | Qualquer crença religiosa | Discriminação |
| 7 | **Deficiência** | PCD | Discriminação (Lei 8.213) |
| 8 | **Nacionalidade** | País de origem | Discriminação |
| 9 | **Gravidez** | Estado de gestação | Discriminação |
| 10 | **Filiação Partidária** | Partido político | Discriminação |

**Implementação:**
```python
PROTECTED_CRITERIA = [
    "gênero", "raça", "idade", "estado_civil", 
    "orientação_sexual", "religião", "deficiência",
    "nacionalidade", "gravidez", "filiação_partidária"
]
```

## 35.2 Regras Anti-Bias em Prompts

Todos os prompts do sistema incluem instruções explícitas:

```markdown
## REGRAS DE GOVERNANÇA (OBRIGATÓRIO)

1. NUNCA mencione ou considere: gênero, raça, idade, estado civil, 
   orientação sexual, religião, deficiência, nacionalidade.

2. AVALIE APENAS: skills técnicas, experiência profissional, 
   competências comportamentais, cultural fit baseado em valores.

3. Se detectar viés na entrada do recrutador, ALERTE e RECUSE.

4. DOCUMENTE a razão de cada decisão de forma explicável.
```

## 35.3 Limites de Autonomia da LIA

### O que a LIA pode fazer automaticamente:
| Ação | Autonomia | Condição |
|------|-----------|----------|
| Responder perguntas sobre vagas | ✅ 100% | — |
| Agendar triagem por voz | ✅ 100% | Dentro do horário permitido |
| Enviar lembretes de entrevista | ✅ 100% | Máximo 3 mensagens/dia |
| Atualizar status do candidato | ✅ 100% | Baseado em regras definidas |
| Gerar relatórios | ✅ 100% | — |

### O que requer aprovação humana:
| Ação | Autonomia | Requer |
|------|-----------|--------|
| Rejeitar candidato | 🔴 0% | Aprovação do recrutador |
| Enviar proposta | 🔴 0% | Aprovação do gestor |
| Bulk email > 10 destinatários | 🟡 Parcial | Aprovação do recrutador |
| Alterar salário da vaga | 🔴 0% | Aprovação do gestor |
| Integrar com novo ATS | 🔴 0% | Aprovação do admin |

## 35.4 Conformidade LGPD

### Horários de Comunicação
| Parâmetro | Valor | Razão |
|-----------|-------|-------|
| **Horário início** | 08:00 | Respeito ao candidato |
| **Horário fim** | 20:00 | Respeito ao candidato |
| **Mensagens/dia** | Máximo 3 | Evitar spam |
| **Quarentena** | 90 dias | Candidato rejeitado |

### Direitos do Candidato (LGPD)
| Direito | Implementação | Status |
|---------|---------------|--------|
| Acesso aos dados | Portal do candidato | ✅ |
| Retificação | Formulário de correção | ✅ |
| Exclusão | Botão "Excluir meus dados" | ✅ |
| Portabilidade | Export JSON/CSV | 🟡 |
| Consentimento | Checkbox explícito | ✅ |

## 35.5 Audit Trail e Explicabilidade

### Logs Obrigatórios
Todo decision ponto gera log com:

```json
{
  "decision_id": "uuid",
  "timestamp": "2025-12-01T10:30:00Z",
  "decision_type": "candidate_screening",
  "input": {
    "candidate_id": "uuid",
    "job_id": "uuid",
    "criteria_used": ["skills", "experience", "cultural_fit"]
  },
  "output": {
    "score": 78,
    "recommendation": "ADVANCE",
    "reasoning": "Candidato possui 4/5 skills requeridas, 
                  5 anos de experiência compatível, 
                  valores alinhados com cultura da empresa"
  },
  "protected_criteria_check": "PASSED",
  "model_used": "claude-sonnet-4",
  "tokens_used": 1234,
  "latency_ms": 850
}
```

---

# 36. Interface Administrativa (NOVO - Dezembro 2025)

> **✅ IMPLEMENTADO:** Sistema administrativo completo com 4 áreas principais.

## 36.1 Setup Empresa (1316 linhas)

### Funcionalidades
| Funcionalidade | Descrição | Status |
|----------------|-----------|--------|
| **Informações da Empresa** | Nome, CNPJ, logo, descrição | ✅ |
| **Departamentos** | CRUD de departamentos com hierarquia | ✅ |
| **Benefícios** | Catálogo de benefícios oferecidos | ✅ |
| **Análise Cultural** | Questionário de cultura organizacional | ✅ |
| **Perfil Ideal** | Definição do candidato ideal por vaga | ✅ |

### Campos de Configuração
- Dados básicos da empresa (nome, setor, tamanho)
- Localização e endereços
- Política de trabalho (remoto, híbrido, presencial)
- Faixa salarial por nível
- Pilares de cultura (5 dimensões)
- EVP (Employee Value Proposition)

## 36.2 Integrações (616 linhas)

### Categorias de Integração (7)

| Categoria | Integrações | Status |
|-----------|-------------|--------|
| **ATS** | Gupy, Pandapé, StackOne | ✅ 3/7 |
| **Calendário** | Microsoft Graph, Google | 🟡 1/2 |
| **Comunicação** | WhatsApp, Email, SMS | 🟡 1/3 |
| **IA/LLM** | Claude, Gemini, OpenAI | ✅ 3/3 |
| **Voice** | Deepgram, OpenMic | ✅ 2/2 |
| **Busca** | Pearch AI, LinkedIn | ✅ 1/2 |
| **Analytics** | LangSmith, Sentry | ✅ 1/2 |

### Funcionalidades
- Status em tempo real de cada integração
- Teste de conexão
- Configuração de credenciais
- Logs de sincronização
- Retry automático com fallback

## 36.3 Big Five (561 linhas)

### Funcionalidades
| Funcionalidade | Descrição | Status |
|----------------|-----------|--------|
| **Banco de Perguntas** | 50+ perguntas por traço OCEAN | ✅ |
| **Perfis por Vaga** | Configuração de pesos por cargo | ✅ |
| **Configuração de Teste** | Duração, número de perguntas | ✅ |
| **Benchmark** | Comparação com candidatos anteriores | 🟡 |

### Traços Avaliados
- **O**penness: Criatividade, curiosidade
- **C**onscientiousness: Organização, responsabilidade
- **E**xtraversion: Sociabilidade, energia
- **A**greeableness: Cooperação, empatia
- **N**euroticism: Estabilidade emocional

## 36.4 Testes Técnicos (788 linhas)

### Funcionalidades
| Funcionalidade | Descrição | Status |
|----------------|-----------|--------|
| **Banco de Questões** | 100+ questões por área técnica | ✅ |
| **Geração por IA** | Claude gera questões sob demanda | ✅ |
| **Auto-correção** | Correção automática de respostas | ✅ |
| **Relatório Detalhado** | Análise por competência | ✅ |

### Áreas Técnicas Suportadas
- Programação (Python, JavaScript, Java, etc.)
- Dados (SQL, Python para dados, estatística)
- DevOps (Docker, Kubernetes, CI/CD)
- Cloud (AWS, GCP, Azure)
- Finanças (Excel, análise financeira)
- Marketing (Google Ads, SEO, analytics)

---

# 37. Voice Screening Infrastructure (NOVO - Dezembro 2025)

> **✅ IMPLEMENTADO:** Infraestrutura de triagem por voz com 5 endpoints de teste.

## 37.1 Endpoints de Teste

### GET /api/v1/voice-test/status
Verifica status dos serviços de voz.

```json
{
  "deepgram": {
    "status": "active",
    "api_key_configured": true,
    "free_tier_remaining": "10,234 min"
  },
  "openmic": {
    "status": "configured",
    "api_key_configured": true,
    "dry_run_mode": true
  }
}
```

### POST /api/v1/voice-test/transcribe-url
Transcreve áudio de URL (ex: WhatsApp).

```json
{
  "audio_url": "https://...",
  "language": "pt-BR",
  "provider": "deepgram"
}
```

### POST /api/v1/voice-test/transcribe-file
Transcreve arquivo de áudio enviado.

```json
{
  "file": "<binary>",
  "language": "pt-BR",
  "provider": "deepgram"
}
```

### POST /api/v1/voice-test/create-screening-agent
Cria agente de triagem para OpenMic.

```json
{
  "job_id": "uuid",
  "questions": ["...", "..."],
  "language": "pt-BR",
  "voice": "brazilian_female_1"
}
```

### POST /api/v1/voice-test/simulate-call
Simula chamada de triagem (dry_run mode).

```json
{
  "candidate_id": "uuid",
  "job_id": "uuid",
  "dry_run": true
}
```

## 37.2 Deepgram vs OpenMic

### Deepgram (Speech-to-Text)

| Aspecto | Detalhe |
|---------|---------|
| **Uso** | Transcrição de áudio WhatsApp |
| **Modelo** | Nova-2 |
| **Custo** | $0.0043/min |
| **Free Tier** | 12.000 min/ano |
| **Latência** | ~2s para áudios curtos |
| **Precisão pt-BR** | 95%+ |

**Quando usar:**
- Áudios de WhatsApp
- Transcrição assíncrona
- Triagem Quick Screening

### OpenMic.ai (Voice AI Agent)

| Aspecto | Detalhe |
|---------|---------|
| **Uso** | Chamadas telefônicas automatizadas |
| **Custo** | $0.08-0.15/min |
| **Inclui** | TTS + STT + AI Agent |
| **Latência** | Real-time |
| **Idiomas** | pt-BR, en-US, es-ES |

**Quando usar:**
- Entrevistas WSI Full
- Chamadas de agendamento
- Follow-up automatizado

## 37.3 Fluxo de Triagem por Voz

```
┌─────────────────────────────────────────────────────────┐
│                 VOICE SCREENING FLOW                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. QUICK SCREENING (WhatsApp)                          │
│  ├── Candidato envia áudio WhatsApp                     │
│  ├── Webhook captura mensagem                            │
│  ├── Deepgram transcreve ($0.0043/min)                  │
│  ├── Claude analisa resposta                             │
│  └── Score + Recomendação → Pipeline                    │
│                                                          │
│  2. WSI FULL INTERVIEW (Telefone)                       │
│  ├── Sistema agenda chamada                              │
│  ├── OpenMic.ai realiza chamada ($0.10/min)             │
│  ├── IA conduz entrevista adaptativa                    │
│  ├── Transcrição em tempo real                          │
│  ├── Claude analisa + Big Five                          │
│  └── Relatório detalhado → Recrutador                   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## 37.4 Custos Operacionais

| Modo | Volume/mês | Custo Deepgram | Custo OpenMic | Total |
|------|------------|----------------|---------------|-------|
| **Quick Screening** | 1.000 candidatos | R$ 100 | — | R$ 100 |
| **WSI Full** | 100 candidatos | — | R$ 350 | R$ 350 |
| **Híbrido** | 1.000 quick + 100 full | R$ 100 | R$ 350 | R$ 450 |

---

# Apêndices

## A. Glossário

### Termos de Negócio

| Termo | Definição |
|-------|-----------|
| **ATS** | Applicant Tracking System - Sistema de gestão de candidatos |
| **LIA** | Learning Intelligence Assistant - Agente de IA conversacional da WeDOTalent |
| **WSI** | Wedo Screening Interview - Metodologia de triagem por voz |
| **Two-Tier Search** | Busca em duas camadas: local (PostgreSQL) + externa (Pearch AI) |
| **LIA Score** | Pontuação composta (0-100) de adequação do candidato |
| **Big Five** | Modelo de personalidade OCEAN (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism) |
| **STAR Method** | Situation, Task, Action, Result - Framework para entrevistas comportamentais |
| **Pearch AI** | API de sourcing com 340M+ perfis globais |
| **OpenMic AI** | Plataforma de chamadas automatizadas com IA |

### Termos de Arquitetura IA

| Termo | Definição |
|-------|-----------|
| **LangGraph** | Framework open-source para construção de agentes com grafos de estado |
| **Intent Router** | Classificador central que direciona mensagens aos agentes corretos |
| **Policy Engine** | Motor de regras de negócio (limites, aprovações, bloqueios) |
| **Feedback Loop** | Ciclo de aprendizado: ação → resultado → análise → atualização |
| **LLM** | Large Language Model - Modelo de linguagem grande (ex: Claude, GPT) |
| **RAG** | Retrieval-Augmented Generation - Geração aumentada por recuperação de contexto |
| **Embeddings** | Representações vetoriais de texto para busca semântica |
| **pgvector** | Extensão PostgreSQL para armazenamento e busca de vetores |
| **Semantic Search** | Busca por significado, não apenas palavras-chave |
| **Slot Filling** | Técnica de NLP para extrair entidades estruturadas de texto |
| **Few-shot Prompting** | Técnica de prompt com exemplos para guiar o LLM |
| **Chain-of-Thought** | Técnica de prompt que incentiva raciocínio passo a passo |
| **Human-in-the-Loop** | Padrão onde humanos validam/aprovam ações do agente |
| **StateGraph** | Estrutura LangGraph para gerenciar estado entre nodes |
| **Checkpoints** | Pontos de salvamento de estado para recuperação/debugging |

### Métricas de Negócio

| Termo | Definição |
|-------|-----------|
| **MRR** | Monthly Recurring Revenue - Receita recorrente mensal |
| **ARR** | Annual Recurring Revenue - Receita recorrente anual |
| **NRR** | Net Revenue Retention - Retenção líquida de receita |
| **CAC** | Customer Acquisition Cost - Custo de aquisição de cliente |
| **LTV** | Lifetime Value - Valor do cliente ao longo do tempo |
| **TCO** | Total Cost of Ownership - Custo total de propriedade |
| **Break-even** | Ponto de equilíbrio entre custo e receita |

## B. Referências

### Documentação Técnica
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangSmith](https://www.langchain.com/langsmith) - Observabilidade LLM
- [Microsoft Graph API](https://docs.microsoft.com/graph/)
- [Pearch AI API](https://pearch.ai)
- [OpenMic.ai](https://openmic.ai)
- [CrewAI](https://www.crewai.com)
- [Relevance AI](https://relevanceai.com)
- [pgvector](https://github.com/pgvector/pgvector) - Vector similarity search for PostgreSQL
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)

### Pesquisa e Metodologia
- [STAR Method - MIT CAPD](https://capd.mit.edu/resources/the-star-method-for-behavioral-interviews/)
- [Big Five Personality Model](https://en.wikipedia.org/wiki/Big_Five_personality_traits)
- [Behavioral Event Interview](https://www.interviewedge.com/articles/Conducting-the-Behavioral-Event-Interview-BEI.htm)
- [RAG Pattern](https://www.pinecone.io/learn/retrieval-augmented-generation/)

### Mercado e Pricing
- [Pearch AI - PitchBook](https://pitchbook.com/profiles/company/542346-04)
- [CrewAI Pricing Guide](https://www.zenml.io/blog/crewai-pricing)
- [LangGraph Pricing](https://www.langchain.com/pricing)
- [Anthropic API Pricing](https://www.anthropic.com/pricing)
- [OpenAI API Pricing](https://openai.com/pricing)

## C. Referência Visual (Protótipo Replit)

> **Nota:** O protótipo Replit serve como "design system factory" - gerando especificações visuais e tokens para implementação Vue.

### Telas Principais Prototipadas

| Tela | Arquivo | Status | Descrição |
|------|---------|--------|-----------|
| **Dashboard Principal** | `src/app/page.tsx` | ✅ Completo | Visão geral com KPIs, atividades recentes |
| **LIA Chat** | `src/components/lia-chat/` | ✅ Completo | Interface conversacional com side panel |
| **Funil de Talentos** | `src/app/funil-talentos/` | ✅ Completo | Pipeline Kanban + busca avançada |
| **Gestão de Vagas** | `src/app/vagas/` | ✅ Completo | CRUD de vagas + criação conversacional |
| **Indicadores** | `src/app/indicadores/` | ✅ Completo | 7 dashboards estratégicos |
| **Candidatos** | `src/app/candidatos/` | ✅ Completo | Perfis + comparação + testes |
| **Agenda** | `src/app/agenda/` | ✅ Completo | Calendário + agendamento AI |
| **Configurações** | `src/app/configuracoes/` | ✅ Completo | Perfil, empresa, integrações |

### Componentes Reutilizáveis

| Componente | Caminho | Uso |
|------------|---------|-----|
| **LIA Score Badge** | `src/components/ui/lia-score.tsx` | Indicador visual de score 0-100 |
| **Candidate Card** | `src/components/candidate-card.tsx` | Card com foto, skills, score |
| **Pipeline Stage** | `src/components/pipeline/` | Coluna Kanban arrastável |
| **Chat Message** | `src/components/lia-chat/message.tsx` | Bolha de chat com avatar |
| **Context Panel** | `src/components/lia-chat/context-panel.tsx` | Side panel dinâmico |
| **Metric Card** | `src/components/ui/metric-card.tsx` | KPI com ícone e tendência |
| **Data Table** | `src/components/ui/data-table.tsx` | Tabela com sort, filter, paginate |

### Arquivos de Design Tokens

| Arquivo | Formato | Conteúdo |
|---------|---------|----------|
| `src/styles/design-tokens.css` | CSS Variables | Cores, espaçamentos, tipografia |
| `tailwind.config.ts` | TypeScript | Configuração Tailwind extendida |
| `src/app/globals.css` | CSS | Reset + utilities globais |

### Como Usar para Migração Vue

1. **Exportar tokens**: Converter CSS variables para formato Vue/Tailwind
2. **Mapear componentes**: Cada componente React → equivalente Vue + shadcn-vue
3. **Manter estrutura**: Diretórios e nomenclatura padronizados
4. **Validar visualmente**: Screenshot lado-a-lado React vs Vue

### Screenshots de Referência

> Capturas de tela podem ser geradas via `screenshot` tool para documentação visual detalhada.

| Tela | Viewport | URL Interna |
|------|----------|-------------|
| Dashboard | Desktop 1440px | `/` |
| LIA Chat expandido | Desktop 1440px | `/funil-talentos` (com chat aberto) |
| Pipeline mobile | Mobile 375px | `/funil-talentos` |
| Criação de vaga | Desktop 1440px | `/vagas/nova` |

## D. Histórico de Versões

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | Nov 2025 | LIA Team | Versão inicial - estado real vs planejado |
| 2.0 | Nov 2025 | LIA Team | Expansão: multi-agentes, pricing, WSI, roadmap, estratégia |
| 2.1 | Nov 2025 | LIA Team | Arquitetura de IA técnica: LLMs, RAG, prompts, observabilidade |
| 2.2 | Nov 2025 | LIA Team | Alinhamento website WeDOTalent: branding unificado, contexto empresarial (Grupo Talenses), posicionamento "Service as Software", personas expandidas (5 tipos), perfis tech (10 categorias), estratégia de comunidade "Terapia de Recrutadores", integrações ATS atualizadas (7 sistemas) |
| 2.3 | Nov 2025 | LIA Team | Estratégia de Migração completa (12 subseções): design tokens exportáveis (JSON/CSS), contrato OpenAPI Rails↔FastAPI, arquitetura híbrida Rails+Vue+FastAPI, plano 3 ondas (14 semanas). Parte V Inteligência Competitiva: análise 9 concorrentes, stacks Voice AI, infraestrutura agentic, decisão Build vs Buy ($301k hybrid), guia Agentic vs Conversacional |
| 2.4 | Nov 2025 | LIA Team | Parte VI Governança: Riscos (26), SLA/Compliance LGPD (27), Dependências Externas (28). Seção 29: Validação Comparativa da Arquitetura - análise detalhada WeDOTalent vs 9 concorrentes, score 8.2/10, decisão "Arquitetura Validada", roadmap ajustado MVP 4 agentes. Apêndice C: Referência Visual do protótipo Replit |
| 2.5 | Nov 2025 | LIA Team | Seção 30: Inteligência de Preços e Monetização - pricing detalhado de 12 concorrentes (Tezi, SeekOut, HireEZ, Gem, Loxo, Beam, Popp, Gupy, DigaAI, InHire, Juicebox, Beamery), stacks técnicas completas (backend, LLM, frameworks, databases, voice AI), sistemas de aprendizagem, integrações, benchmarking de preços WeDOTalent, projeção de revenue |
| 2.6 | Nov 2025 | LIA Team | Seção 31: Metodologia WSI - WeDoTalent Skill Index completa (14 subseções): fundamentação teórica (CBI, Bloom, Dreyfus, Big Five), estrutura operacional, fluxo conversacional (4 blocos), sistema de validação e pontuação (fórmula dual 0.6×auto + 0.4×contexto), cálculo do índice WSI, corte dinâmico e saturação inteligente, integração cultural, governança humana, benchmarks de mercado vs Paradox/SHL/Gupy/IBM, boas práticas de aplicação |
| 2.7 | Nov 2025 | LIA Team | Seção 32: Roadmap de Produto v1→v2 (9 subseções): inventário completo de features (11 módulos, 100+ features), matriz RICE de priorização (top 20), cronograma detalhado (v1.0 MVP 12sem, v1.5 GA 12sem, v2.0 ATS 24sem), dependências críticas, métricas de sucesso por versão, sizing de equipe (5→10→21 FTEs), riscos e mitigações, resumo executivo visual |
| 2.8 | Nov 2025 | LIA Team | Seção 29.8: Análise Técnica Detalhada por Plataforma (7 subseções) - matriz comparativa de frameworks (9 plataformas), análise individual com stacks técnicas completas (Tezi AI, DigaAI, Gupy, InHire, SeekOut, Juicebox, Loxo, Beam AI, Popp AI), ferramentas identificadas (LLMs, Agent Frameworks, STT, Search, WhatsApp, ATS, Prompt Engineering), 5 insights estratégicos, custos de replicação, arquitetura recomendada visual, fontes verificadas |
| 2.9 | Nov 2025 | LIA Team | Seção 33: Produtos Avançados - Pipeline Intelligence e Analytics Premium (6 subseções): evolução de produto em 3 fases (Plugin→Pipeline Intelligence→Analytics Premium), Pipeline Intelligence v2.0, Analytics Premium v2.5, lógica de sequenciamento, modelo de monetização, projeção revenue add-ons (R$360k→R$2.6M), roadmap Q2-Q4 2026 |
| 3.0 | Nov 2025 | LIA Team | **Versão Final PRD.** Seção 34: Dimensionamento de Time e Estratégia de Desenvolvimento (9 subseções): composição atual atualizada (**5 pessoas**: Founder/CEO com 9 funções [Comercial, Marketing, PM, Design, Prototipagem, Planejamento, Novas Tecnologias, Novos Produtos, QA], Tech Lead, Frontend, Backend, **Head CS & Implementação** [Onboarding, Suporte, Relacionamento, Retenção]), detalhamento das funções do Founder com % tempo por área, detalhamento do Head CS com métricas (Time-to-value < 2sem, CSAT > 4.5, Churn < 5%), gaps identificados (Design, QA, DevOps, Data, PM, Vendas), **estratégia dual Tradicional vs Vibe Coding**, **Design System Factory**, **roadmap de crescimento** (5→6→8→10→12→15 pessoas até Q1 2027), estrutura organizacional com áreas Produto/Engenharia/Comercial+CS, custo de time por fase (R$90k→R$240k/mês), **cenários comparativos** (Tradicional vs Vibe Coding: -25% time-to-market, -27% headcount, economia R$582k/ano, ROI 33x), configuração de ferramentas, práticas de produtividade, métricas de sucesso, resumo executivo |
| 3.1 | Dez 2025 | LIA Team | **Atualização de Maturidade (5% → 30%).** Atualizações: Header v3.1 Dezembro 2025, Seção 1.4 (status diferenciais competitivos), Seção 8 (integrações: 3 ATS bidirecionais + Pearch + Deepgram + LangSmith), Seção 9.2 (38 routers funcionais), Seção 13 (estado atual 30%), Seção 15 (11 agentes: 1 orchestrator + 10 especializados), Seção 18.5 (Modos de Triagem: Quick Screening WhatsApp + WSI Full Interview). **Novas seções:** 35 (AI Governance & Ethics: PROTECTED_CRITERIA, anti-bias, LGPD, audit trail), 36 (Interface Administrativa: 4 áreas, 3.281 linhas), 37 (Voice Screening Infrastructure: 5 endpoints Deepgram/OpenMic) |
| 3.2 | Dez 2025 | LIA Team | **Remoção de Industry Weights.** Removida Seção 36 (Industry Weight Calibration) - pesos por indústria eliminados para prevenir vieses. Adotado modelo universal de scoring para avaliação consistente de candidatos. Renumeração das seções subsequentes (37→36, 38→37). |

---

**Documento gerado em:** Novembro 2025  
**Última atualização:** Dezembro 2025  
**Próxima revisão:** Sob demanda  
**Estado do projeto:** MVP em Desenvolvimento (30% implementado, 100% documentado)  
**Marca oficial:** WeDOTalent  
**Linhas do documento:** ~8.150  
**Versão:** 3.1
