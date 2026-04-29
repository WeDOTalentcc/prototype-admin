# Auto Source - Integração WebSocket com Kanban

## 🎯 Objetivo

Permitir que o Kanban de Applies mostre candidatos sendo adicionados em **tempo real** quando o **Auto Source** encontra perfis qualificados, sem precisar recarregar a página ou fazer polling.

---

## 🔄 Fluxo Completo

### 1. Usuário Aciona Auto Source

```
Frontend → POST /v1/users/jobs/:id/auto_source
          ↓
Backend cria Sourcing com parameters:
{
  sources: ["local"],
  auto_add_job_id: 123,
  min_score_threshold: 70.0
}
          ↓
Enfileira LocalSearchJob via JobEnqueuerService
          ↓
Retorna sourcing_id para frontend
```

**Response:**
```json
{
  "sourcing_id": 456,
  "uid": "abc-123-def",
  "status": "processing",
  "job_id": 123,
  "min_score_threshold": 70.0,
  "limit": 30,
  "message": "Subscribe to channel: sourcing_456"
}
```

---

### 2. Jobs Processam Candidatos em Background

```
LocalSearchJob busca candidatos na base local
          ↓
Para cada candidato encontrado:
  SourcedProfileSourcingAiAnalysisJob analisa fit com job
          ↓
  Se score >= min_score_threshold (70):
    AutoAddCandidateService.call
          ↓
    Cria Apply na primeira coluna (web_submission)
          ↓
    ✨ BROADCAST via ApplyCollectionChannel ✨
```

---

### 3. Kanban Recebe Notificação em Tempo Real

O Kanban já está **conectado ao ApplyCollectionChannel** quando montado:

```javascript
// kanban.vue - onMounted
subscribe(jobId)  // Conecta ao WebSocket
```

**Quando um candidato é adicionado** via Auto Source, o backend emite:

```json
{
  "type": "item_completed",
  "timestamp": "2026-03-06T14:30:45.123Z",
  "apply_id": 789,
  "candidate_id": 456,
  "selective_process_id": 12,
  "source": "auto_source",
  "score": 85.5,
  "apply": {
    "id": 789,
    "candidate_id": 456,
    "job_id": 123,
    "selective_process_id": 12,
    "selective_process_status": "Triagem",
    "candidate": {
      "id": 456,
      "name": "João Silva",
      "email": "joao@example.com",
      "avatar_url": "...",
      ...
    },
    "created_at": "2026-03-06T14:30:45.120Z",
    ...
  }
}
```

---

## 📡 Canal WebSocket

### Nome do Canal

`ApplyCollectionChannel`

### Stream Identifier

```ruby
"#{user_id}_apply_collection_#{job_id}"
```

**Exemplo:** `42_apply_collection_123`

### Parâmetros de Subscription

```javascript
{
  channel: 'ApplyCollectionChannel',
  job_id: 123
}
```

---

## 📨 Eventos Emitidos

### `item_completed` (candidato adicionado)

Emitido **toda vez** que um candidato é adicionado ao funil via Auto Source.

**Payload:**
```typescript
{
  type: "item_completed"
  timestamp: string           // ISO 8601
  apply_id: number
  candidate_id: number
  selective_process_id: number
  source: "auto_source"       // Identifica que veio do Auto Source
  score: number               // Score de fit calculado pela IA (0-100)
  apply: ApplyObject          // Apply completo serializado
}
```

**Diferenças vs Bulk Operations:**

| Campo | Bulk Operations | Auto Source |
|-------|----------------|-------------|
| `source` | Não existe | `"auto_source"` |
| `score` | Não existe | Score da IA (85.5) |
| `current`, `total`, `percent` | ✅ Presente | ❌ Não existe |

---

## 🖥️ Frontend - Como Funciona Atualmente

O Kanban **já está preparado** para receber esses eventos via `useApplyCollectionChannel`:

### Callback: `onItemCompleted`

```javascript
onItemCompleted.value = (apply, event) => {
  const targetSpId = event.selective_process_id ?? apply.selective_process_id
  const targetColumn = kanbanColumns.value.find(c => c.id === targetSpId)
  
  if (!targetColumn) return
  
  // Remove da coluna antiga (se existia)
  kanbanColumns.value.forEach(col => {
    col.applies = col.applies.filter(a => a.id !== apply.id)
  })
  
  // 🎯 Adiciona na coluna correta
  apply._isNew = true  // Flag para animação
  targetColumn.applies.unshift(apply)
  targetColumn.totalCount = (targetColumn.totalCount || 0) + 1
  
  // Remove flag após 3s
  setTimeout(() => {
    apply._isNew = false
  }, 3000)
}
```

### Comportamento Visual

- ✅ Candidato aparece **no topo da primeira coluna** (web_submission)
- ✅ Classe `.apply-card--new` aplicada por 3s (pode ter animação CSS)
- ✅ Contador da coluna incrementa automaticamente
- ✅ **Sem reload necessário** - atualização incremental

---

## 🆕 Melhorias Sugeridas (Opcionais)

### 1. Badge "Auto Source" no Card

Diferenciar visualmente candidatos que vieram do Auto Source:

```vue
<template>
  <v-chip
    v-if="apply._source === 'auto_source'"
    size="x-small"
    color="purple"
    variant="flat"
  >
    🤖 Auto
  </v-chip>
</template>

<script>
// No onItemCompleted callback:
if (event.source === 'auto_source') {
  apply._source = 'auto_source'
  apply._autoSourceScore = event.score
}
</script>
```

### 2. Notificação Toast com Score

```javascript
onItemCompleted.value = (apply, event) => {
  // ... lógica existente ...
  
  if (event.source === 'auto_source') {
    toast.info(
      `Novo candidato encontrado! Fit: ${event.score.toFixed(0)}%`,
      { duration: 3000 }
    )
  }
}
```

### 3. Contador de "Candidatos Auto Source"

Mostrar quantos candidatos foram adicionados automaticamente:

```vue
<template>
  <v-banner v-if="autoSourceCount > 0" color="purple-lighten-5">
    🤖 {{ autoSourceCount }} candidatos encontrados via Auto Source
  </v-banner>
</template>

<script>
const autoSourceCount = ref(0)

onItemCompleted.value = (apply, event) => {
  // ... lógica existente ...
  
  if (event.source === 'auto_source') {
    autoSourceCount.value++
  }
}
</script>
```

---

## 🔍 Como Testar

### 1. Abrir Kanban de uma Vaga

```
/jobs/123/kanban
```

### 2. Acionar Auto Source

```bash
curl -X POST http://localhost:3000/v1/users/jobs/123/auto_source \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "limit": 10,
    "min_score": 70
  }'
```

### 3. Observar Console do Navegador

Você deve ver logs:

```
[ApplyCollectionChannel] 📨 Received event: item_completed { ... }
[ApplyCollectionChannel] handleEvent: item_completed SP: 12
```

### 4. Verificar Kanban

- Candidatos devem aparecer **automaticamente** na primeira coluna
- Cards devem ter classe `.apply-card--new` por 3s
- Contador da coluna deve incrementar

---

## 🐛 Debugging

### Backend

**Ver broadcasts sendo enviados:**
```bash
docker logs -f ats_api

# Procurar por:
📢 [AutoAddCandidateService] Broadcasted to kanban (ApplyCollectionChannel)
✅ [AutoAddCandidateService] Added candidate 456 to job 123 via auto_source
```

### Frontend

**Verificar estado do canal:**
```javascript
// No console do navegador:
const channel = window.$nuxt.$applyCollectionChannel
console.log(channel.status)  // Se houver erro
```

**Verificar se está conectado:**
```javascript
// Deve aparecer no log:
[ApplyCollectionChannel] ✅ Connected!
```

---

## 🔁 Fluxo Comparado: Bulk vs Auto Source

### Bulk Operations (Add from Talent Pool)

```
User Action → Bulk Job → Multiple Broadcasts:
  1. started (total: 100)
  2. item_completed (1 de 100) → Adiciona card
  3. item_completed (2 de 100) → Adiciona card
  ...
  100. completed (created: 95, skipped: 5)
```

**Frontend mostra:**
- Progress bar global (0-100%)
- Spinner na coluna sendo processada
- Toast final com resumo

### Auto Source (Background Search)

```
User Action → Sourcing → Background Jobs:
  → Profile 1 analyzed → Score 85 → AutoAdd → broadcast
  → Profile 2 analyzed → Score 45 → Skip (below threshold)
  → Profile 3 analyzed → Score 92 → AutoAdd → broadcast
  ...
```

**Frontend mostra:**
- Candidatos aparecem **individualmente** conforme são encontrados
- **Sem progress bar** (não tem total conhecido a priori)
- Cada card aparece com animação `_isNew`

---

## ⚙️ Implementação Backend

### Arquivo Modificado

[app/services/jobs/auto_add_candidate_service.rb](../app/services/jobs/auto_add_candidate_service.rb)

### Mudanças

```ruby
def call
  # ... cria apply ...
  
  broadcast_candidate_added(apply)         # SourcingChannel (já existia)
  broadcast_to_kanban(apply, selective_process)  # 🆕 ApplyCollectionChannel
end

private

def broadcast_to_kanban(apply, selective_process)
  ApplyCollectionChannel.broadcast_to(
    apply_collection_stream_id,
    {
      type: "item_completed",
      timestamp: Time.current.iso8601,
      apply_id: apply.id,
      candidate_id: apply.candidate_id,
      selective_process_id: selective_process.id,
      apply: serialize_apply(apply),
      source: "auto_source",
      score: @sps.score
    }
  )
end
```

---

## ✅ Compatibilidade

### Backward Compatible

✅ **Frontend antigo continua funcionando** - ignora campo `source`  
✅ **Bulk operations não afetadas** - continuam emitindo eventos como antes  
✅ **Kanban já preparado** - callback `onItemCompleted` processa ambos os casos

### Breaking Changes

❌ **Nenhum** - apenas adiciona novos campos opcionais

---

## 📚 Docs Relacionados

- [ApplyCollectionChannel - Frontend Integration](./apply_collection_channel.md)
- [Auto Source API](./auto_source_api.md)
- [Hybrid Search Complete Documentation](./hybrid_search_complete_documentation.md)

---

## 🎉 Resultado Final

**Antes:**
- Usuário aciona Auto Source
- Precisa **recarregar página** para ver candidatos adicionados
- Sem feedback visual de progresso

**Depois:**
- Usuário aciona Auto Source
- Candidatos aparecem **automaticamente** no Kanban conforme são encontrados
- Animação visual de entrada
- Contador incrementa em tempo real
- Possibilidade de adicionar badge "Auto Source" e mostrar score
