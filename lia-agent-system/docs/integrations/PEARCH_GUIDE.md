# Pearch AI - Guia Completo de Integração

**Última Atualização:** 13 Abril 2026

## Status: ✅ OPERATIONAL (24/11/2025)

Integração completa com Pearch AI para busca de candidatos em 800M+ perfis profissionais.

---

## 1. Visão Geral e Status

### O que é Pearch AI?

A Pearch AI é uma plataforma de busca de candidatos com 800M+ perfis profissionais. A integração com a Plataforma LIA permite três modos de busca:

| Modo | Descrição | Custo |
|------|-----------|-------|
| **Base Local** | Busca apenas no banco de dados interno | Gratuito |
| **Busca Global Pearch** | Busca na base Pearch (800M+ perfis) | Créditos |
| **Híbrido** | Combina local + Pearch | Parcialmente pago |

### Funcionalidades Implementadas

#### Serviço Pearch AI (`app/services/pearch_service.py`)
- ✅ Autenticação via Bearer token (PEARCH_API_KEY)
- ✅ Busca por linguagem natural (`search_candidates`)
- ✅ Busca por job description completa (`search_by_job_description`)
- ✅ Parsing robusto de respostas JSON (suporta array e dict)
- ✅ Logging detalhado (tempo de busca, quantidade de resultados)
- ✅ Error handling (timeouts, HTTP errors, parsing errors)

#### Modelos de Dados (`app/models/pearch.py`)
- ✅ `CandidateProfile` - Perfil completo do candidato
- ✅ `CandidateContact` - Informações de contato (email, phone, LinkedIn)
- ✅ `CandidateExperience` - Histórico de experiência profissional
- ✅ `CandidateEducation` - Formação acadêmica
- ✅ `PearchSearchRequest` - Request model para busca
- ✅ `PearchSearchResponse` - Response model com candidatos

#### REST API Endpoints (`app/api/v1/candidates.py`)
- ✅ `POST /api/v1/candidates/search` - Busca com body JSON
- ✅ `GET /api/v1/candidates/search` - Busca via query params
- ✅ `POST /api/v1/candidates/search/by-job-description` - Busca com JD completa
- ✅ `GET /api/v1/candidates/health` - Health check da integração

#### Integração LIA Conversational Agent (`app/agents/conversation.py`)
- ✅ Intent detection: `search_candidates`
- ✅ Entity extraction otimizada para busca de candidatos
- ✅ Node `execute_candidate_search` no LangGraph workflow
- ✅ Apresentação conversacional dos resultados
- ✅ Context enrichment com top candidatos

---

## 2. Sistema de Créditos

### Custo Base por Candidato

| Tipo de Busca | Custo Base | Descrição |
|---------------|------------|-----------|
| `fast` | 1 crédito | Busca padrão, dados completos |

> **Nota:** O modo `pro` (5 créditos) foi removido. Todas as buscas utilizam o modo `fast`.

### Enriquecimento de Contato via Apify

Candidatos sem email ou telefone são enriquecidos automaticamente via Apify (`dev_fusion/Linkedin-Profile-Scraper`) ao custo de **$0.01/candidato**. Candidatos que continuam sem contato após enriquecimento são filtrados dos resultados.

| Etapa | Custo | Descrição |
|-------|-------|-----------|
| Busca Pearch | 1 crédito/candidato | Dados de perfil completos |
| Enriquecimento Apify | $0.01/candidato | Fallback quando Pearch não retorna contato |
| Revelação de contato | Apify primeiro, Pearch fallback | Endpoint `/contact/reveal` |

### Dados Incluídos no Custo Base (GRATUITOS após busca)

Quando você paga o custo base, recebe **todos** estes dados:

```
✅ Nome completo
✅ Headline / Título atual
✅ Empresa atual
✅ Localização (cidade, estado, país)
✅ Skills técnicas
✅ Experiências profissionais completas
   - Empresa (nome, domínio, LinkedIn)
   - Cargo
   - Período (início/fim)
   - Duração em anos
   - Descrição das atividades
   - Localização
   - Industries da empresa
   - Porte da empresa
   - Stack tecnológico
   - Se é startup
✅ Educação completa
   - Instituição
   - Grau (Graduação, Mestrado, etc.)
   - Área de estudo
   - Período
✅ Anos de experiência total
✅ Resumo/Summary profissional
✅ LinkedIn URL
✅ Foto/Avatar
✅ Idiomas
✅ Se está "Open to Work"
✅ Se é decision maker
```

### Custos Adicionais (Opcionais)

| Recurso | Custo Extra | Quando Cobrado |
|---------|-------------|----------------|
| Insights de IA | +1 crédito/candidato | Se `insights=true` |
| Profile Scoring | +1 crédito/candidato | Se `profile_scoring=true` |
| High Freshness | +2 créditos/candidato | Se `high_freshness=true` |
| Exigir email | +1 crédito/candidato | Se `require_emails=true` |
| **Revelar email** | +2 créditos/candidato | Se `show_emails=true` |
| Exigir telefone | +1 crédito/candidato | Se `require_phone_numbers=true` |
| **Revelar telefone** | +14 créditos/candidato | Se `show_phone_numbers=true` |

### Exemplo de Cálculo

```
Busca: "Senior Python Developer em São Paulo"
Tipo: fast (1 crédito base)
Limite: 20 candidatos
Opções: insights=true, show_emails=true

Cálculo:
- Base: 1 crédito
- Insights: +1 crédito
- Revelar email: +2 créditos
= 4 créditos/candidato

Total: 4 × 20 = 80 créditos
```

---

## 3. Endpoints da API

### Configuração

#### 1. Obter API Key
```
https://platform.pearch.ai/dashboard
```

#### 2. Adicionar Secret no Replit
```
PEARCH_API_KEY=seu-token-aqui
```

#### 3. Verificar Configuração
```bash
curl http://localhost:8000/api/v1/candidates/health
```

### Health Check
```bash
GET /api/v1/candidates/health
```

**Response:**
```json
{
  "service": "Pearch AI Candidate Search",
  "status": "configured",
  "api_key_set": true,
  "message": "Ready to search 190M+ candidate profiles"
}
```

### Busca Simples (Natural Language)
```bash
curl -X GET "http://localhost:8000/api/v1/candidates/search?\
query=Senior%20Python%20engineer%20in%20NYC&\
limit=10"
```

### Busca com JSON Body
```bash
curl -X POST http://localhost:8000/api/v1/candidates/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Full stack developer with React and Node.js, remote",
    "search_type": "fast",
    "limit": 20,
    "timeout": 60
  }'
```

### Busca por Job Description
```bash
curl -X POST http://localhost:8000/api/v1/candidates/search/by-job-description \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "We are looking for a Senior Backend Engineer with 5+ years of experience in Python, Django, and AWS...",
    "location": "San Francisco",
    "limit": 25
  }'
```

### Estimar Créditos (Antes de Buscar)

```http
POST /api/v1/search/candidates/estimate
Content-Type: application/json

{
  "query": "Senior Python Developer",
  "pearch_type": "fast",
  "limit": 20,
  "insights": true,
  "show_emails": false,
  "show_phone_numbers": false
}
```

**Response:**
```json
{
  "query": "Senior Python Developer",
  "pearch_type": "fast",
  "limit": 20,
  "base_cost": 1,
  "insights_cost": 1,
  "cost_per_candidate": 2,
  "total_estimated": 40,
  "confirmation_message": "Busca estimada em 40 créditos (máximo)"
}
```

### Response Schema

```json
{
  "query": "Senior Python engineer in San Francisco",
  "total_results": 3,
  "search_time_seconds": 3.64,
  "credits_used": null,
  "candidates": [
    {
      "id": null,
      "name": null,
      "headline": "Senior Staff Software Engineer @ Company",
      "current_title": "Senior Staff Software Engineer",
      "current_company": "Company",
      "location": "San Francisco, California, United States",
      "contact": {
        "email": "email@example.com",
        "phone": "+1234567890",
        "linkedin_url": "https://linkedin.com/in/profile",
        "location": "San Francisco, CA"
      },
      "experience": [...],
      "education": [...],
      "skills": ["Python", "Django", "AWS", "Docker"],
      "summary": "Software engineer with 9 years' experience...",
      "match_score": 95.5,
      "match_reasoning": "Strong Python background with senior-level experience in SF"
    }
  ]
}
```

---

## 4. Fluxo de Dados e Persistência

### Ciclo de Vida dos Dados

```
┌─────────────────────────────────────────────────────────────────┐
│                     FLUXO DE DADOS PEARCH                        │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │   RECRUTADOR │
    │  faz busca   │
    └──────┬───────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. BUSCA EXECUTADA (Créditos Consumidos)                       │
│                                                                  │
│  - Pearch retorna candidatos com dados completos                │
│  - DADOS ESTÃO APENAS NA MEMÓRIA DO FRONTEND                    │
│  - Você JÁ PAGOU pelos dados neste momento                      │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          │                               │
          ▼                               ▼
┌─────────────────────┐     ┌─────────────────────────────────────┐
│  SEM IMPORT         │     │  COM IMPORT                          │
│                     │     │                                      │
│  - Dados temporários│     │  POST /candidates/import             │
│  - Perdidos ao sair │     │                                      │
│  - VOCÊ PERDEU $$$  │     │  ✅ Dados salvos no banco local     │
│                     │     │  ✅ Educação → candidate_education   │
│  ❌ NÃO RECOMENDADO │     │  ✅ Experiência → candidate_experiences│
└─────────────────────┘     │  ✅ Disponível para sempre           │
                            │  ✅ Não paga novamente               │
                            │                                      │
                            │  ✅ RECOMENDADO                      │
                            └─────────────────────────────────────┘
```

### Regra de Ouro

> **Se você fez uma busca e pagou créditos, SEMPRE importe os candidatos para o banco local.**
> 
> Isso evita pagar novamente pelos mesmos dados em buscas futuras.

### Endpoints de Persistência

#### Importação Completa de Candidatos

```http
POST /api/v1/search/candidates/import
Content-Type: application/json

{
  "candidates": [
    {
      "pearch_id": "abc123",
      "name": "João Silva",
      "email": "joao@email.com",
      "phone": "+5511999999999",
      "linkedin_url": "https://linkedin.com/in/joaosilva",
      "current_title": "Senior Developer",
      "current_company": "TechCorp",
      "location": "São Paulo, SP, Brasil",
      "years_of_experience": 8,
      "skills": ["Python", "Django", "AWS"],
      "languages": [{"language": "Português", "level": "Nativo"}],
      "education": [...],
      "experiences": [...]
    }
  ],
  "source_search_query": "Senior Python Developer São Paulo"
}
```

**Response:**
```json
{
  "imported_count": 1,
  "skipped_count": 0,
  "imported_ids": ["uuid-do-candidato"],
  "message": "Importados 1 candidatos. 0 já existiam na base."
}
```

#### Persistir Contato Revelado

```http
POST /api/v1/search/candidates/persist-revealed
Content-Type: application/json

{
  "pearch_id": "abc123",
  "candidate_name": "João Silva",
  "email": "joao@email.com",
  "phone": "+5511999999999",
  "linkedin_url": "https://linkedin.com/in/joaosilva",
  "current_title": "Senior Developer",
  "current_company": "TechCorp"
}
```

### Tabelas do Banco de Dados

#### candidates
```sql
- id (UUID)
- name, email, phone
- linkedin_url, avatar_url
- current_title, current_company
- pearch_profile_id          -- ID único da Pearch
- source                      -- "pearch", "manual", "csv", etc.
- technical_skills, soft_skills
- languages, certifications
- current_salary, salary_expectation_clt
```

#### candidate_education
```sql
- id (UUID)
- candidate_id (FK → candidates)
- institution
- degree
- field_of_study
- start_date, end_date
- is_completed
- sequence_order
```

#### candidate_experiences
```sql
- id (UUID)
- candidate_id (FK → candidates)
- company_name
- company_linkedin_url, company_domain
- title
- start_date, end_date, duration_years
- is_current
- description, location
- industries [], technologies []
- company_size, company_size_range
- is_startup, company_founded_year
- sequence_order
```

---

## 5. Busca Híbrida e Deduplicação

### Como Funciona a Busca Híbrida

```
┌─────────────────────────────────────────────────────────────────┐
│                     BUSCA HÍBRIDA                                │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────┐
    │  Query: "Senior Python Developer São Paulo"              │
    └───────────────────────────┬──────────────────────────────┘
                                │
            ┌───────────────────┴───────────────────┐
            │                                       │
            ▼                                       ▼
    ┌───────────────────┐               ┌───────────────────────┐
    │  1. BUSCA LOCAL   │               │  2. BUSCA PEARCH      │
    │                   │               │                       │
    │  - Custo: ZERO    │               │  - Custo: X créditos  │
    │  - Base interna   │               │  - Base 800M+ perfis  │
    │  - Candidatos já  │               │  - Perfis novos       │
    │    importados     │               │                       │
    └─────────┬─────────┘               └───────────┬───────────┘
              │                                     │
              └──────────────┬──────────────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │  RESULTADOS COMBINADOS  │
                │                         │
                │  - Local primeiro       │
                │  - Pearch depois        │
                │  - Duplicatas removidas │
                └─────────────────────────┘
```

### Parâmetros da Busca Híbrida

```http
POST /api/v1/search/candidates/hybrid
Content-Type: application/json

{
  "query": "Senior Python Developer",
  "search_local_first": true,
  "local_limit": 20,
  "include_pearch": true,
  "pearch_type": "fast",
  "pearch_limit": 15,
  "exclude_candidate_ids": []
}
```

### Deduplicação

O sistema detecta automaticamente candidatos já existentes:

#### Por `pearch_profile_id`
Quando você importa um candidato Pearch, o ID único (`pearch_id` / `docid`) é salvo no campo `pearch_profile_id` do banco local.

Em buscas futuras:
1. O sistema verifica se o `pearch_id` já existe no banco
2. Se existir, retorna os dados locais (gratuito)
3. Se não existir, retorna dados Pearch (pago)

#### Por LinkedIn URL
Como fallback, o sistema também pode comparar por LinkedIn URL para evitar duplicatas.

---

## 6. Integração com LIA Agent

O LIA detecta automaticamente intenção de busca de candidatos:

**Usuário:**
> "Preciso de desenvolvedores Python sênior em São Paulo"

**LIA:**
1. Detecta intent: `search_candidates` (confidence > 0.95)
2. Extrai entities:
   ```json
   {
     "job_title": "desenvolvedor Python",
     "seniority": "senior",
     "location": "São Paulo",
     "limit": 10
   }
   ```
3. Executa busca Pearch: `"Senior desenvolvedor Python in São Paulo"`
4. Apresenta top 5 candidatos de forma conversacional
5. Oferece próximos passos (ver mais detalhes, agendar entrevistas)

### Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                      │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│               FastAPI Backend (Port 8000)                    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  /api/v1/candidates/* (candidates.py)              │    │
│  └────────────────────┬───────────────────────────────┘    │
│                       │                                      │
│                       ▼                                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │  PearchService (pearch_service.py)                 │    │
│  │  - search_candidates()                             │    │
│  │  - search_by_job_description()                     │    │
│  └────────────────────┬───────────────────────────────┘    │
│                       │                                      │
│                       ▼                                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │  LIA Agent (conversation.py)                       │    │
│  │  - classify_intent                                 │    │
│  │  - extract_entities                                │    │
│  │  - execute_candidate_search                        │    │
│  │  - generate_response                               │    │
│  └────────────────────────────────────────────────────┘    │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼ HTTPS + Bearer Auth
┌─────────────────────────────────────────────────────────────┐
│              Pearch AI API (api.pearch.ai)                   │
│                 800M+ Professional Profiles                  │
└─────────────────────────────────────────────────────────────┘
```

### Performance

- **Busca fast:** 3-5 segundos (média)
- **Enriquecimento Apify:** 5-15 segundos por candidato
- **Timeout default:** 60 segundos
- **Timeout máximo:** 1800 segundos (30 minutos)

### Segurança

- ✅ API key armazenada em Replit Secrets (encrypted at rest)
- ✅ Bearer token authentication
- ✅ HTTPS apenas (api.pearch.ai usa SSL)
- ✅ Logs não expõem API key
- ✅ Error handling não vaza informações sensíveis

---

## 7. Troubleshooting e Referências

### Erros Comuns

#### Erro: "PEARCH_API_KEY not configured"
**Solução:** Adicione a API key em Replit Secrets e reinicie o backend.

#### Erro: "HTTP 401 Unauthorized"
**Solução:** Verifique se a API key é válida em https://platform.pearch.ai/dashboard

#### Erro: "HTTP 429 Too Many Requests"
**Solução:** Aguarde ou contate Pearch AI para aumentar rate limits.

#### Busca retorna 0 candidatos
**Possíveis causas:**
- Query muito específica (relaxe critérios)
- Location inexistente ou mal formatada
- Skills muito nichadas

### Boas Práticas

#### 1. Sempre Importe Após Buscar
```javascript
const searchResults = await searchCandidates(query);
displayResults(searchResults);
await importCandidates(searchResults.candidates);
```

#### 2. Use Estimativa Antes de Buscar
```javascript
const estimate = await estimateCredits(query, options);
const confirmed = await showConfirmationDialog(estimate);
if (confirmed) {
  const results = await searchCandidates(query, options);
}
```

#### 3. Prefira Busca Híbrida
```javascript
const results = await hybridSearch({
  query: "Senior Developer",
  search_local_first: true,
  include_pearch: true
});
```

#### 4. Revele Contatos Apenas Quando Necessário
```javascript
const candidate = await revealContact(pearchId, { 
  show_emails: true,
  show_phone_numbers: false
});
```

### Checklist de Implementação Frontend

- [ ] Exibir estimativa de créditos antes de busca global/híbrida
- [ ] Chamar `/candidates/import` após exibir resultados
- [ ] Chamar `/candidates/persist-revealed` ao revelar contato
- [ ] Mostrar badge "Salvo" em candidatos já importados
- [ ] Diferenciar visualmente candidatos locais vs Pearch
- [ ] Mostrar badge de source do contato (Apify/Pearch/Local)

### Próximos Passos

#### Melhorias Futuras
- [ ] Cache de resultados (Redis) para queries frequentes
- [ ] Filtros avançados (years_experience, education_level, companies)
- [ ] Bulk search (múltiplas queries em paralelo)
- [ ] Webhook para notificações de novos candidatos
- [ ] Integration com ATS (Greenhouse, Lever via Merge.dev)
- [ ] Export de candidatos (CSV, PDF)

#### Melhorias LIA Agent
- [ ] Multi-step candidate refinement (iterative search)
- [ ] Candidate scoring personalizado
- [ ] Automatic interview scheduling integration
- [ ] Email outreach automation

### Referências

- [Pearch AI Website](https://pearch.ai/)
- [Pearch AI API Docs](https://apidocs.pearch.ai/reference/post_v2-search)
- [Pearch AI Dashboard](https://platform.pearch.ai/dashboard)
- [Pearch AI GitHub](https://github.com/Pearch-ai)
- [Pearch AI MCP](https://github.com/Pearch-ai/mcp_pearch)

---

**Última atualização:** Abril 2026  
**Status:** ✅ Produção-ready  
**Cobertura:** 800M+ perfis profissionais  
**Enrichment:** Apify dev_fusion/Linkedin-Profile-Scraper ($0.01/candidato)
