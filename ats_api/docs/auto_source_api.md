# Auto Source — Busca e Adição Automática de Candidatos a uma Vaga

## Visão Geral

Esta feature permite buscar candidatos da base local que se encaixam em uma vaga e adicioná-los automaticamente ao processo seletivo. O fluxo é assíncrono: a requisição retorna imediatamente com um `sourcing_id`, e os resultados chegam via **ActionCable (WebSocket)**.

### Fluxo completo

```
POST /v1/users/jobs/:id/auto_source
        |
        v
Cria um Sourcing com auto_add_job_id nos parameters
        |
        v
Sourcings::JobEnqueuerService enfileira busca na base local
        |
        v
Para cada perfil encontrado: AiAnalysisJob analisa e pontua
        |
        v
Se score >= min_score_threshold:
  AutoAddCandidateService cria o Apply no primeiro SelectiveProcess (status: web_submission = 0)
        |
        v
Broadcast via ActionCable -> canal: sourcing_<sourcing_id>
```

---

## Endpoint

```
POST /v1/users/jobs/:id/auto_source
```

**Autenticação:** Bearer token (padrão do sistema)

### Parâmetros

| Parâmetro   | Tipo    | Obrigatório | Padrão | Range   | Descrição                                         |
|-------------|---------|-------------|--------|---------|---------------------------------------------------|
| `id`        | integer | sim         | —      | —       | ID da vaga (job)                                  |
| `limit`     | integer | não         | 30     | 1–100   | Quantidade máxima de candidatos a buscar          |
| `min_score` | float   | não         | 70.0   | 0–100   | Score mínimo para adicionar o candidato à vaga    |

### Resposta (202 Accepted)

```json
{
  "sourcing_id": 123,
  "uid": "uuid-aqui",
  "status": "processing",
  "job_id": 456,
  "min_score_threshold": 70.0,
  "limit": 30,
  "message": "Subscribe to channel: sourcing_123"
}
```

### Erros possíveis

| Status | Situação                                      |
|--------|-----------------------------------------------|
| 404    | Job não encontrado                            |
| 403    | Job pertence a outra conta                    |

---

## WebSocket — ActionCable

Após receber o `202`, assine o canal indicado no campo `message`.

### Assinar o canal

```js
consumer.subscriptions.create(
  { channel: "SourcingChannel", id: sourcing_id },
  { received(data) { /* handle events */ } }
)
```

### Eventos recebidos

#### `profile_analyzed` — perfil analisado (com ou sem score suficiente)

```json
{
  "type": "profile_analyzed",
  "sourcing_id": 123,
  "sourced_profile": { ... }
}
```

#### `candidate_added_to_job` — candidato adicionado à vaga

Emitido apenas quando `score >= min_score_threshold`.

```json
{
  "type": "candidate_added_to_job",
  "sourcing_id": 123,
  "job_id": 456,
  "candidate_id": 789,
  "apply_id": 101,
  "sourced_profile_sourcing_id": 202,
  "score": 85.3
}
```

#### `sourcing_completed` — busca finalizada

```json
{
  "type": "sourcing_completed",
  "sourcing_id": 123
}
```

---

## Observacao importante: SelectiveProcess de status `web_submission` (0)

O `AutoAddCandidateService` adiciona o candidato no **primeiro** selective process da vaga (`order(:position).first`).

Para que o Apply seja criado corretamente, a vaga **deve ter um SelectiveProcess com `status: 0` (`web_submission`) na primeira posicao (position: 0)**. Esse e o "Funil" — etapa de entrada do pipeline.

Se a vaga nao tiver esse selective process configurado, o candidato nao sera adicionado (retorno silencioso via `return unless selective_process`).

> Ao criar ou exibir vagas no front, valide se o primeiro selective process existe. Se nao existir, o auto source nao vai adicionar candidatos mesmo que encontre perfis com boa pontuacao.

---

## Sugestoes de implementacao para Vue/Nuxt

> **Importante:** estas sao apenas sugestoes. O mais relevante e analisar como o sistema ja lida com sourcing, candidatos e ActionCable e **reutilizar os componentes, composables e padroes existentes**. Priorize DRY, SOLID e clean code antes de criar qualquer coisa nova.

### 1. Composable para gerenciar o fluxo

Um composable `useAutoSource` concentra a chamada HTTP e a conexao WebSocket. Evita duplicar logica de subscription em multiplos componentes.

```js
// composables/useAutoSource.js
export function useAutoSource(jobId) {
  const sourcing = ref(null)
  const addedCandidates = ref([])
  const isRunning = ref(false)
  let subscription = null

  async function start(options = {}) {
    isRunning.value = true
    addedCandidates.value = []

    const { data } = await useApi(`/v1/users/jobs/${jobId}/auto_source`, {
      method: 'POST',
      body: options
    })

    sourcing.value = data
    subscribeToChannel(data.sourcing_id)
  }

  function subscribeToChannel(sourcingId) {
    subscription = consumer.subscriptions.create(
      { channel: 'SourcingChannel', id: sourcingId },
      {
        received(event) {
          if (event.type === 'candidate_added_to_job') {
            addedCandidates.value.push(event)
          }
          if (event.type === 'sourcing_completed') {
            isRunning.value = false
            subscription?.unsubscribe()
          }
        }
      }
    )
  }

  onUnmounted(() => subscription?.unsubscribe())

  return { start, sourcing, addedCandidates, isRunning }
}
```

### 2. Feedback de progresso

Enquanto `isRunning` for `true`, exiba um indicador. A cada evento `candidate_added_to_job`, incremente um contador visivel ao usuario. Verifique se ja existe um componente de loading/progress no sistema antes de criar um novo.

### 3. Exibicao dos candidatos adicionados

Os eventos `candidate_added_to_job` retornam `candidate_id` e `apply_id`. Verifique se o sistema ja tem um componente de card de candidato que aceita esses dados. Se sim, reutilize-o.

### 4. Configuracao de parametros

Os parametros `limit` e `min_score` podem ser expostos ao usuario ou fixados em valores padrao. Se ja existe algum componente de configuracao de sourcing na interface, analise se faz sentido reaproveita-lo aqui.

### 5. Tratamento de erros

Trate os casos de 404 (vaga nao encontrada) e 403 (sem permissao) com os mecanismos de erro ja existentes no projeto.

### 6. Desconexao do WebSocket

Sempre cancele a subscription quando o componente for desmontado (`onUnmounted`) ou quando o evento `sourcing_completed` chegar, para evitar memory leaks e conexoes orfas.
