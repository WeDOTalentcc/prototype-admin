# Estratégia de Módulos Monetizáveis — Plataforma LIA WeDOTalent

**Versão**: 1.0
**Data**: 2026-04-11
**Status**: Aprovado para implementação MVP
**Contexto**: Derivado da Task #146 (Talent Intelligence Tools)

---

## 1. Visão Geral

A Plataforma LIA evolui de um ATS com IA para uma **plataforma de serviços inteligentes de recrutamento** com módulos ativáveis. O modelo combina software (funcionalidade) + serviço (dados/insights contínuos) em módulos que o cliente pode adquirir dentro da própria plataforma.

### Princípio Central

> **Vender serviços, não apenas software.** O cliente compra inteligência, estratégia e decisões melhores — a plataforma é o veículo de entrega.

### Modelo de Monetização

- **Plano Base (gratuito/incluído)**: Recrutamento + Triagem WSI + Pipeline + ATS básico
- **Módulos Premium (pagos)**: Inteligência avançada, analytics estratégico, automação
- **Degustação**: Insights limitados no chat da LIA para demonstrar valor (com badge BETA)

---

## 2. Linha Divisória de Inteligência

A distinção entre gratuito e pago segue uma regra clara:

| Etapa do Processo | Inteligência Incluída | Inteligência Paga |
|---|---|---|
| **Triagem (screening)** | WSI completo, gap analysis básico, fit cultural | — |
| **Entrevista** | Gravação, transcrição, armazenamento | Análise WSI, viés, parecer, feedback, comparativo |
| **Decisão** | Pipeline visual, kanban | Analytics preditivo, benchmarks, recomendações |
| **Pós-contratação** | Placement, email de parabéns | Onboarding suite (produto futuro) |

> **Até a triagem → inteligência gratuita.**
> **A partir da entrevista → inteligência paga.**

---

## 3. Inventário de Módulos

### 3.1 Talent Intelligence Pro

**O que entrega**: Mapeamento inteligente de competências e mercado.

| Feature | Degustação (BETA) | Módulo Pago |
|---|---|---|
| Skills Ontology | 1 análise por vaga, resumida | Análise completa, adjacências, mapeamento canônico |
| Gap Analysis | "Candidato tem gap em 2 skills" | Detalhamento, skills adjacentes transferíveis, plano |
| Market Intelligence | "Sua faixa está 15% abaixo do mercado" | Benchmarks completos, fontes, tendências, skills em alta |

**Backend**: Implementado (Task #146)
**Frontend**: Degustação via chat da LIA

### 3.2 Internal Mobility Suite

**O que entrega**: Matching de colaboradores internos para vagas abertas.

| Feature | Degustação (BETA) | Módulo Pago |
|---|---|---|
| Matching interno | "3 colaboradores compatíveis encontrados" | Lista completa com readiness score, gap detalhado |
| Economia estimada | — | Comparativo custo interno vs. contratação externa |
| Plano de desenvolvimento | — | Sugestões de upskilling por colaborador |

**Backend**: Implementado (Task #146)
**Frontend**: Degustação via chat da LIA

### 3.3 Interview Intelligence Pro

**O que entrega**: Inteligência sobre entrevistas realizadas.

**Camada gratuita (ATS básico):**
- Gravação da entrevista por vídeo
- Transcrição automática
- Armazenamento e acesso ao registro

**Camada paga:**

| Feature | Descrição |
|---|---|
| WSI na entrevista | Mesma metodologia da triagem aplicada à transcrição (7 blocos, Bloom, Dreyfus) |
| Detecção de viés | Identificação de perguntas tendenciosas, padrões de favoritismo |
| Análise comparativa | Candidato vs. top performers contratados, vs. triados com alta pontuação |
| Parecer estratégico | Recomendação fundamentada com evidências da transcrição |
| Feedback estruturado | Gerado automaticamente para devolver ao candidato |
| Scoring de competências | Competências demonstradas (não só declaradas no CV) |

**Backend**: Completo (Task #162 — 5 serviços: WSI, Bias Detection, Comparative Analysis, Strategic Opinion, Feedback Generator)
**Frontend**: Não existe ainda

### 3.4 Workforce Planning

**O que entrega**: Previsão e planejamento de contratações.

| Feature | Degustação (BETA) | Módulo Pago |
|---|---|---|
| Previsão básica | — | Forecast por período/departamento |
| Modelagem de cenários | — | Crescimento, corte, sazonalidade |
| Dashboard de gestores | — | Visualização completa para RH estratégico |

**Backend**: Parcial (Task #146 — forecast básico)
**Frontend**: Não existe

### 3.5 Candidate Nurture / CRM

**O que entrega**: Engajamento automatizado de candidatos passivos.

| Feature | Descrição |
|---|---|
| Sequências de nurture | Campanhas automatizadas de email/mensagem |
| Métricas de engajamento | Taxas de abertura, resposta, conversão |
| Reengajamento inteligente | Identificação de candidatos inativos para recontato |

**Backend**: Estrutura criada (Task #146), falta infraestrutura de envio de email
**Frontend**: Não existe

### 3.6 Onboarding Intelligence (Produto Futuro)

**O que entrega**: Workflow pós-contratação completo.

| Feature | Descrição |
|---|---|
| Checklist configurável | Documentos, exames, acessos |
| Portal do novo colaborador | Interface dedicada |
| Buddy matching | Sugestão de mentor/buddy por perfil |
| Integração HRIS | Sincronização com folha de pagamento |

**Backend**: Não implementado — produto novo
**Frontend**: Não existe
**Modelo**: Software + serviço, cobrança separada

### 3.7 Predictive Attrition (Futuro)

**O que entrega**: Previsão de risco de turnover precoce.

**Backend**: Não implementado — requer dados históricos e modelo de ML
**Viabilidade**: Quando houver volume de dados suficiente

---

## 4. Interface na Plataforma

### 4.1 Página de Módulos

- **Localização**: Item no menu lateral principal ("Módulos" ou "Soluções")
- **Layout**: Cards por módulo com:
  - Nome e descrição
  - Status: BETA (gratuito por tempo limitado) / Disponível / Ativo / Em Breve
  - Badge visual para cada status
  - Botão de ativação ou "Saiba mais"

### 4.2 Degustação no Chat da LIA

- Insights contextuais inseridos proativamente durante uso normal
- Limite de profundidade: insight resumido com CTA "para análise completa, ative o módulo X"
- Badge BETA visível na mensagem

### 4.3 Badge BETA

Aplicar badge BETA em:
- Agentes do Agent Suite (todos em degustação)
- Insights de Skills Ontology no chat
- Alertas de Market Intelligence
- Sugestões de Internal Mobility
- Qualquer funcionalidade nova de módulos

**Objetivo do BETA**:
1. Gerenciar expectativa do cliente
2. Permitir imperfeições em features novas
3. Criar senso de oportunidade ("gratuito enquanto BETA")
4. Coletar feedback para melhorar o produto

**Transição**: Quando módulo amadurecer → remover BETA → aplicar badge "Pro" ou "Premium"

---

## 5. Arquitetura Técnica (MVP)

### 5.1 Tabela company_modules

```sql
CREATE TABLE company_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id),
    module_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'beta',
    tier VARCHAR(20) DEFAULT 'free',
    activated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(company_id, module_name)
);
```

**Status possíveis**: `beta`, `trial`, `active`, `expired`, `disabled`
**Tier possíveis**: `free`, `basic`, `pro`, `enterprise`

### 5.2 Middleware de Verificação

- Antes de executar tools premium, consultar `company_modules`
- Se módulo não ativo: retornar insight parcial + mensagem de ativação
- Se módulo em BETA: permitir acesso completo com badge
- Se módulo ativo (pago): acesso completo sem restrições

### 5.3 Resposta Degradada

```
Módulo ativo → resposta completa
Módulo BETA  → resposta completa + badge BETA
Módulo trial → resposta completa + "X dias restantes"
Sem módulo   → insight parcial + CTA de ativação
```

### 5.4 Módulos Registrados

| module_name | Descrição |
|---|---|
| `talent_intelligence_pro` | Skills Ontology + Gap Analysis + Market Intelligence |
| `internal_mobility` | Matching interno + Readiness scoring |
| `interview_intelligence` | Análise WSI de entrevista + viés + parecer |
| `workforce_planning` | Previsão + cenários + dashboard |
| `candidate_nurture` | Sequências + engajamento + CRM |
| `onboarding_suite` | Workflow pós-contratação (futuro) |
| `predictive_analytics` | Attrition prediction (futuro) |

---

## 6. Plano de Implementação por Fases

### Fase 1 — Infraestrutura + Degustação (Agora)

| # | Item | Esforço | Resultado |
|---|------|---------|-----------|
| 1 | Documento estratégico | Baixo | Este documento |
| 2 | Tabela `company_modules` + middleware | Baixo | Base técnica para tudo |
| 3 | Degustação no chat da LIA (3 insights) | Médio | Cliente "sente" o valor |
| 4 | Badge BETA nos agentes e insights | Baixo | Gerenciamento de expectativa |

### Fase 2 — Primeiros Módulos Pagos (Próximo Sprint)

| # | Item | Esforço | Resultado |
|---|------|---------|-----------|
| 5 | Página "Módulos" no menu lateral | Médio | Visibilidade do catálogo |
| 6 | Talent Intelligence Pro como primeiro módulo | Baixo (backend pronto) | Primeira receita |
| 7 | Ativação manual por admin | Baixo | Fluxo de venda básico |

### Fase 3 — Expansão (2-3 meses)

| # | Item | Esforço | Resultado |
|---|------|---------|-----------|
| 8 | Internal Mobility com dashboard | Médio | Módulo visual para empresas grandes |
| 9 | Workforce Planning com dashboard | Alto | Valor para gestores/RH estratégico |
| 10 | Infraestrutura de vídeo-entrevista | Alto | Base para Interview Intelligence |

### Fase 4 — Produtos Novos (6+ meses)

| # | Item | Esforço | Resultado |
|---|------|---------|-----------|
| 11 | Interview Intelligence Pro | Alto | Módulo premium de alto valor |
| 12 | Candidate Nurture com email | Alto | CRM de candidatos |
| 13 | Onboarding Suite | Muito alto | Produto novo, receita nova |
| 14 | Predictive Attrition | Alto | Premium analytics com ML |

---

## 7. Métricas de Sucesso

| Métrica | Meta Fase 1 | Meta Fase 2 |
|---|---|---|
| Clientes que veem degustação | 80% dos ativos | 90% |
| Cliques em "saiba mais" do módulo | — | 20% dos que veem |
| Módulos ativados (pagos) | — | 5+ empresas |
| Receita incremental por módulo | — | A definir pricing |
| Feedback coletado (BETA) | 10+ feedbacks | 30+ |

---

## 8. Referências

- Task #146: Implementação dos backends de Talent Intelligence
- WeDO Talent Guide v3.3: Metodologia WSI e critérios de avaliação
- Análise competitiva: Eightfold AI, HireVue, Phenom
