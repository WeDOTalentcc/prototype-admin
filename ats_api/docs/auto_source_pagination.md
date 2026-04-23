# Auto Source - Paginação Inteligente

## 🎯 Problema Resolvido

**Antes:** Quando usuário pedia "20 candidatos", o sistema buscava os top 20 por score e **sempre retornava os mesmos** em buscas subsequentes.

**Depois:** O sistema agora **pagina até encontrar 20 candidatos qualificados**, guardando histórico de páginas visitadas e continuando de onde parou em próximas buscas.

---

## 🔄 Como Funciona

### 1. Primeira Busca

```
User: "Quero 20 candidatos para Desenvolvedor Python"
│
├─ Sistema verifica metadata da vaga (job.auto_source_metadata)
│  └─ Vazio? Inicia da página 1
│
├─ Busca páginas 1-3 (MAX_PAGES_PER_RUN = 3)
│  ├─ Página 1: 30 resultados → 8 qualificados (score >= 70)
│  ├─ Página 2: 30 resultados → 6 qualificados
│  └─ Página 3: 30 resultados → 5 qualificados
│
├─ Total adicionado: 19 candidatos
│
└─ Salva metadata:
   {
     last_page: 3,
     total_added: 19,
     total_searched: 90,
     last_title: "Desenvolvedor Python Sênior",
     last_description: "...",
     last_sourcing_min_score: 70.0
   }
```

### 2. Continuação Automática

Quando o sourcing completa, o sistema verifica se atingiu a meta:

```
19 < 20 (target) → Dispara AutoSourceContinuationJob
│
├─ Busca páginas 4-6
│  ├─ Página 4: 30 resultados → 4 qualificados
│  └─ Total agora: 23 candidatos
│
├─ 23 >= 20 → Meta atingida! ✅
│
└─ Atualiza metadata:
   {
     last_page: 6,
     total_added: 23,
     total_searched: 180
   }
```

### 3. Busca Subsequente (dias depois)

```
User: "Quero mais 10 candidatos"
│
├─ Sistema verifica metadata
│  ├─ Título mudou? NÃO
│  ├─ Description mudou? NÃO
│  └─ Continua da página 7
│
├─ Busca páginas 7-9
│  └─ Adiciona 10 candidatos
│
└─ Total acumulado: 33 candidatos
```

### 4. Reset ao Mudar Vaga

```
User: Edita título de "Dev Python" → "Engenheiro Python Sênior"
│
├─ Sistema detecta mudança
│
├─ ⚠️  RESET metadata:
│  {
│    last_page: 0,
│    total_added: 0,
│    total_searched: 0,
│    last_title: "Engenheiro Python Sênior",
│    reset_at: "2026-03-06T18:30:00Z"
│  }
│
└─ Próxima busca inicia da página 1 novamente
```

---

## 📦 Estrutura de Metadata

### Campo: `job.auto_source_metadata` (JSONB)

```json
{
  "last_title": "Desenvolvedor Python Sênior",
  "last_description": "Buscamos desenvolvedor com experiência em...",
  "last_page": 6,
  "total_searched": 180,
  "total_added": 23,
  "last_sourcing_id": 456,
  "last_sourcing_min_score": 70.0,
  "updated_at": "2026-03-06T18:45:12Z",
  "reset_at": "2026-03-05T10:00:00Z"
}
```

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `last_title` | String | Último título usado na busca |
| `last_description` | String | Última descrição usada |
| `last_page` | Integer | Última página visitada (0-based após reset) |
| `total_searched` | Integer | Total de perfis analisados (todas buscas) |
| `total_added` | Integer | Total de candidatos adicionados à vaga |
| `last_sourcing_id` | Integer | ID do último sourcing executado |
| `last_sourcing_min_score` | Float | Threshold de score usado |
| `updated_at` | ISO8601 | Última atualização |
| `reset_at` | ISO8601 | Quando metadata foi resetada |

---

## 🏗️ Componentes Criados

### 1. Migration

**Arquivo:** `db/migrate/20260306164318_add_auto_source_metadata_to_jobs.rb`

```ruby
add_column :jobs, :auto_source_metadata, :jsonb, default: {}, null: false
add_index :jobs, :auto_source_metadata, using: :gin
```

### 2. AutoSourcePaginationService

**Arquivo:** `app/services/jobs/auto_source_pagination_service.rb`

**Responsabilidades:**
- ✅ Verifica se título/description mudou → reset metadata
- ✅ Calcula quantas páginas buscar baseado em meta e histórico
- ✅ Limita a `MAX_PAGES_PER_RUN = 3` por execução
- ✅ Cria sourcing com informações de paginação
- ✅ Enfileira LocalSearchJob

**Uso:**
```ruby
result = Jobs::AutoSourcePaginationService.call(
  job: @job,
  user: @current_user,
  target_count: 20,
  min_score_threshold: 70.0
)

# result = {
#   success: true,
#   sourcing_id: 789,
#   uid: "abc-123",
#   status: "processing",
#   pagination: {
#     current_page: 7,
#     pages_to_search: 3,
#     max_page: 9
#   }
# }
```

### 3. AutoSourceMetadataUpdateService

**Arquivo:** `app/services/jobs/auto_source_metadata_update_service.rb`

**Responsabilidades:**
- ✅ Atualiza metadata após sourcing completar
- ✅ Incrementa contadores
- ✅ Verifica se atingiu meta
- ✅ Dispara continuação se necessário

**Chamado por:** `AiAnalysisJob` quando todos perfis forem analisados

### 4. AutoSourceContinuationJob

**Arquivo:** `app/jobs/jobs/auto_source_continuation_job.rb`

**Responsabilidades:**
- ✅ Job background para buscar próximas páginas automaticamente
- ✅ Verifica se ainda precisa de mais candidatos
- ✅ Respeita limite de 10 páginas totais

**Enfileirado por:** `AutoSourceMetadataUpdateService`

### 5. Modificações em AiAnalysisJob

**Arquivo:** `app/jobs/sourced_profiles/ai_analysis_job.rb`

**Adicionado:**
- ✅ Método `update_auto_source_metadata_if_needed`
- ✅ Conta quantos candidatos foram adicionados no sourcing atual
- ✅ Chama `AutoSourceMetadataUpdateService` quando análise completa

---

## 🎮 API - Endpoint Modificado

### POST `/v1/users/jobs/:id/auto_source`

**Request:**
```json
{
  "limit": 20,
  "min_score": 70
}
```

**Response (Success):**
```json
{
  "success": true,
  "sourcing_id": 789,
  "uid": "abc-123-def",
  "status": "processing",
  "job_id": 456,
  "min_score_threshold": 70.0,
  "target_count": 20,
  "pagination": {
    "current_page": 7,
    "pages_to_search": 3,
    "max_page": 9
  },
  "message": "Subscribe to channel: sourcing_789"
}
```

**Response (Max Pages Reached):**
```json
{
  "success": false,
  "error": "Max pages reached",
  "metadata": {
    "last_page": 10,
    "total_added": 45,
    "total_searched": 300
  }
}
```

---

## ⚙️ Configurações

### Constantes no AutoSourcePaginationService

```ruby
MAX_PAGES_PER_RUN = 3      # Páginas por execução
CANDIDATES_PER_PAGE = 30   # Resultados por página
```

### Limites

- **Máximo de páginas por run:** 3
- **Máximo de páginas total:** 10 (após isso, retorna erro)
- **Continuação automática:** Sim, se meta não atingida

---

## 📊 Logs

### Início da Busca Paginada

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 [AutoSourcePagination] Starting paginated search
   Job: 456 - Desenvolvedor Python Sênior
   Pages: 7 to 9
   Target: 20 candidates
   Min Score: 70%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Reset de Metadata

```
🔄 [AutoSourcePagination] Job 456 changed - resetting metadata
   Title changed: true
   Description changed: false
```

### Atualização após Sourcing

```
✅ [AutoSourceMetadataUpdate] Updated job 456 metadata
   Pages searched: 7 to 9
   Added this run: 8
   Total added: 23
   Target: 20
```

### Continuação Automática

```
🔄 [AutoSourceMetadataUpdate] Need 7 more candidates, checking if should continue...
🚀 [AutoSourceMetadataUpdate] Triggering next batch search
```

---

## 🧪 Como Testar

### 1. Primeira busca

```bash
curl -X POST http://localhost:3000/v1/users/jobs/123/auto_source \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "limit": 20,
    "min_score": 70
  }'
```

**Verificar metadata:**
```ruby
Job.find(123).auto_source_metadata
# => { "last_page" => 3, "total_added" => 15, ... }
```

### 2. Busca subsequente (continua de onde parou)

```bash
curl -X POST http://localhost:3000/v1/users/jobs/123/auto_source \
  -H "Authorization: Bearer TOKEN" \
  -d '{ "limit": 30, "min_score": 70 }'
```

**Verificar que começou da página 4:**
```ruby
Job.find(123).auto_source_metadata["last_page"]
# => 6 (buscou páginas 4, 5, 6)
```

### 3. Mudar vaga e verificar reset

```ruby
job = Job.find(123)
job.update!(title: "Engenheiro Python Sênior")

# Próxima busca:
# - Detecta mudança de título
# - Reseta metadata
# - Inicia da página 1
```

---

## 🔮 Melhorias Futuras

### Opcionais (não implementados ainda):

1. **Score dinâmico por página**
   - Relaxar threshold se poucas matches (75 → 70 → 65)

2. **Cache de queries**
   - Evitar regerar query LLM se job não mudou

3. **Analytics**
   - Dashboard mostrando páginas visitadas
   - Taxa de conversão por página

4. **Smart pagination**
   - Pular páginas se score médio muito baixo

5. **Manual override**
   - Botão "Resetar histórico de busca" na UI

---

## 🎯 Resumo Técnico

| Aspecto | Implementação |
|---------|---------------|
| **Persistência** | JSONB no Job (`auto_source_metadata`) |
| **Paginação** | 3 páginas por run, máx 10 total |
| **Reset** | Automático ao mudar título/description |
| **Continuação** | Automática via Sidekiq job |
| **Tracking** | Contador acumulativo de candidatos |
| **Broadcast** | Via ApplyCollectionChannel (tempo real) |
| **Backward Compatible** | ✅ Sim - metadata opcional |

---

## 📚 Arquivos Relacionados

- [app/services/jobs/auto_source_pagination_service.rb](../app/services/jobs/auto_source_pagination_service.rb)
- [app/services/jobs/auto_source_metadata_update_service.rb](../app/services/jobs/auto_source_metadata_update_service.rb)
- [app/jobs/jobs/auto_source_continuation_job.rb](../app/jobs/jobs/auto_source_continuation_job.rb)
- [app/controllers/v1/users/jobs/auto_source_controller.rb](../app/controllers/v1/users/jobs/auto_source_controller.rb)
- [app/jobs/sourced_profiles/ai_analysis_job.rb](../app/jobs/sourced_profiles/ai_analysis_job.rb)
- [docs/auto_source_kanban_websocket_integration.md](./auto_source_kanban_websocket_integration.md)
