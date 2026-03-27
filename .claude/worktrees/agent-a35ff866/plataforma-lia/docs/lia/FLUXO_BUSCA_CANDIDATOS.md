# Fluxo Completo de Busca de Candidatos

## Arquitetura do Sistema

### Backend (lia-agent-system)
```
app/
├── api/v1/candidate_search.py    # Endpoints REST
├── services/pearch_service.py     # Integração Pearch AI
└── models/pearch.py               # Modelos de dados
```

### Frontend (plataforma-lia)
```
src/
├── components/
│   ├── search/
│   │   ├── smart-search-input.tsx     # Input inteligente com parsing
│   │   ├── search-results-card.tsx    # Exibição de resultados
│   │   ├── credit-cost-display.tsx    # Calculadora de custos
│   │   └── advanced-filters-modal.tsx # Filtros avançados
│   └── pages/chat-page.tsx            # Chat com LIA
└── lib/api/candidate-search.ts        # Cliente API
```

---

## Fluxo de Busca Passo a Passo

### 1. Iniciando a Busca (Chat)

O usuário inicia digitando "buscar candidatos" no chat com a LIA:

```
Usuário: "buscar candidatos"
LIA: "Vou te ajudar a encontrar os melhores candidatos! 
      Para uma busca mais precisa, me conte sobre o perfil..."
```

### 2. Coleta do Perfil

A LIA ativa o `SmartSearchInput` que:
- Aceita linguagem natural: "Desenvolvedor Python em São Paulo com 5 anos"
- Extrai entidades automaticamente:
  - `job_title`: "Desenvolvedor Python"
  - `location`: "São Paulo"
  - `years_experience`: "5 anos"
  - `skills`: ["Python"]

### 3. Busca Híbrida (2 etapas)

#### Etapa 1: Banco Local (GRATUITO)
```
POST /api/v1/search/candidates/local
Query: "Desenvolvedor Python"
Resultado: Candidatos do banco proprietário
Custo: 0 créditos
```

#### Etapa 2: Pearch AI (USA CRÉDITOS)
```
POST /api/v1/search/candidates
{
  "query": "Desenvolvedor Python em São Paulo",
  "search_local": true,
  "search_pearch": true,
  "pearch_type": "pro",
  "pearch_limit": 15
}
```

---

## Cálculo de Créditos Pearch

### Fórmula por Candidato

| Componente | Custo |
|------------|-------|
| **Base Fast** | 1 crédito |
| **Base Pro** | 5 créditos |
| **Insights** | +1 crédito |
| **Scoring** | +1 crédito |
| **Dados Frescos** | +2 créditos |
| **Requerer Email** | +1 crédito |
| **Exibir Email** | +2 créditos |
| **Requerer Telefone** | +1 crédito |
| **Exibir Telefone** | +14 créditos |
| **Email OU Telefone** | +1 crédito |

### Exemplo de Cálculo

Busca PRO com insights + scoring para 15 candidatos:
```
Base (PRO):     5 créditos
Insights:      +1 crédito
Scoring:       +1 crédito
─────────────────────────
Por candidato:  7 créditos
Total (15x):  105 créditos
```

---

## Endpoints da API

### 1. Busca Local (Gratuita)
```
GET /api/v1/search/candidates/local?query=AWS&limit=5

Response:
{
  "query": "AWS",
  "candidates": [...],
  "local_count": 1,
  "total_count": 1
}
```

### 2. Busca Híbrida
```
POST /api/v1/search/candidates
{
  "query": "string",
  "search_local": true,
  "search_pearch": true,
  "pearch_type": "pro",
  "local_limit": 20,
  "pearch_limit": 15
}
```

### 3. Estimativa de Créditos
```
POST /api/v1/search/candidates/estimate
{
  "query": "string",
  "pearch_type": "pro",
  "limit": 15,
  "insights": true,
  "high_freshness": false,
  "show_emails": false,
  "show_phone_numbers": false
}
```

---

## Exibição de Resultados

### SearchResultsCard
Exibe candidatos com:
- Avatar e nome
- Cargo atual e empresa
- Localização
- Score LIA (%)
- Indicadores de contato (email, telefone, LinkedIn)
- Fonte (Local ou Pearch)

### Ações Disponíveis
- **Selecionar múltiplos**: Checkbox para ações em lote
- **Ver perfil**: Abre CandidateDetailSidebar
- **Adicionar à vaga**: Vincula candidato a processo
- **Comparar**: Análise lado a lado
- **Agendar entrevista**: Integração com calendário

---

## Componentes da Calculadora de Custos

### CreditCostDisplay
Exibe breakdown visual em tempo real:
```
┌─────────────────────────────────────┐
│ Calculadora de Custos Pearch        │
├─────────────────────────────────────┤
│ Base (Profissional)          5      │
│ Insights + Scoring          +2      │
│ ─────────────────────────────────── │
│ Por Candidato                7      │
│ Total (15 candidatos)      105      │
└─────────────────────────────────────┘
```

### useCreditEstimator Hook
```typescript
const { 
  creditEstimate,
  calculateLocal,
  calculateFromServer,
  canAfford 
} = useCreditEstimator()
```

---

## Fluxo Visual no Chat

```
┌──────────────────────────────────────┐
│ Chat com LIA                         │
├──────────────────────────────────────┤
│                                      │
│ Usuário: buscar candidatos           │
│                                      │
│ LIA: Vou te ajudar! Descreva o       │
│      perfil ideal...                 │
│                                      │
│ ┌──────────────────────────────────┐ │
│ │ SmartSearchInput                 │ │
│ │ "Desenvolvedor Python em SP"     │ │
│ │                                  │ │
│ │ Tags: [Python] [São Paulo]       │ │
│ └──────────────────────────────────┘ │
│                                      │
│ LIA: Encontrei 5 candidatos no       │
│      banco local e 15 via Pearch!    │
│                                      │
│ ┌──────────────────────────────────┐ │
│ │ SearchResultsCard                │ │
│ │ ☑ Danilo Ramos - AWS  [96%]     │ │
│ │ ☐ Maria Silva - Google [88%]    │ │
│ │ ☐ João Costa - Meta   [85%]     │ │
│ │                                  │ │
│ │ [Adicionar à Vaga] [Comparar]   │ │
│ └──────────────────────────────────┘ │
│                                      │
└──────────────────────────────────────┘
```

---

## Testes Realizados

### Busca Local ✅
```bash
curl "http://localhost:8000/api/v1/search/candidates/local?query=AWS&limit=5"

# Resultado: 1 candidato encontrado
# - Danilo Henrique Ramos (Solutions Architect @ AWS)
# - Score: 96%
# - Skills: AWS, Architecture, Serverless
```

### Lista de Candidatos ✅
```bash
curl "http://localhost:8000/api/v1/candidates?skip=0&limit=5"

# 55 candidatos no banco
```

### Frontend ✅
- Chat com LIA funcionando
- Sugestões de tarefas visíveis
- Badge de créditos (50 créditos)
- Campo de input ativo

---

## Status do Sistema

| Componente | Status |
|------------|--------|
| Backend (FastAPI) | ✅ Rodando |
| Frontend (Next.js) | ✅ Rodando |
| Banco de Dados | ✅ 55 candidatos |
| Busca Local | ✅ Funcionando |
| Calculadora de Créditos | ✅ Implementada |
| Chat com LIA | ✅ Ativo |
