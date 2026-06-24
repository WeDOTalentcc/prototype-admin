# State Machines — WeDOTalent LIA

Documentação visual das máquinas de estado do sistema. Gerada a partir do código-fonte
e validada por sensor automatizado (`tests/contract/test_gap05_002_state_machine_doc.py`).

---

## 1. Job Vacancy Status Transitions

**Fonte:** `app/api/v1/job_vacancies/_shared.py` — `ALLOWED_STATUS_TRANSITIONS`

### Diagrama

```mermaid
stateDiagram-v2
    [*] --> Rascunho : Criação da vaga

    Rascunho --> Ativa : Publicar
    Rascunho --> Cancelada : Cancelar
    Rascunho --> Arquivada : Arquivar

    Ativa --> Pausada : Pausar
    Ativa --> Concluída : Concluir (vaga preenchida)
    Ativa --> Cancelada : Cancelar
    Ativa --> Arquivada : Arquivar

    Pausada --> Ativa : Reativar
    Pausada --> Cancelada : Cancelar
    Pausada --> Arquivada : Arquivar

    Concluída --> Arquivada : Arquivar

    Cancelada --> Arquivada : Arquivar

    Arquivada --> [*] : Estado terminal
```

### Tabela de transições

| Estado atual | Transições permitidas |
|---|---|
| **Rascunho** | Ativa, Cancelada, Arquivada |
| **Ativa** | Pausada, Concluída, Cancelada, Arquivada |
| **Pausada** | Ativa, Cancelada, Arquivada |
| **Concluída** | Arquivada |
| **Cancelada** | Arquivada |
| **Arquivada** | _(nenhuma — estado terminal)_ |

### Descrição dos estados

- **Rascunho**: Vaga criada mas ainda não publicada. Recrutador pode editar livremente.
- **Ativa**: Vaga publicada e recebendo candidatos. Triagem e processos seletivos em andamento.
- **Pausada**: Vaga temporariamente suspensa (ex: orçamento congelado). Pode ser reativada.
- **Concluída**: Vaga preenchida com sucesso. Caminho unidirecional para Arquivada.
- **Cancelada**: Vaga cancelada (ex: posição eliminada). Caminho unidirecional para Arquivada.
- **Arquivada**: Estado terminal. Nenhuma transição permitida. Vaga mantida para histórico.

### Invariantes

1. **Arquivada é absorvente** — todo estado pode transitar para Arquivada, mas Arquivada não transita para nenhum.
2. **Concluída e Cancelada são quase-terminais** — só permitem transição para Arquivada.
3. **Ciclo Ativa ↔ Pausada** — único ciclo permitido no grafo.

---

## 2. Candidate Stage Transitions (Pipeline FSM)

**Fonte:** `app/services/state_machines/candidate_fsm.py` — `TERMINAL_STAGES` + `validate_stage_transition()`

### Diagrama

```mermaid
stateDiagram-v2
    [*] --> any_stage : Entrada no pipeline

    state "Estágios customizáveis" as custom {
        state "Qualquer estágio" as any
        any --> any : Transição livre
    }

    any_stage --> custom
    custom --> hired : Contratar
    custom --> rejected : Rejeitar
    custom --> cancelled : Cancelar
    custom --> not_selected : Não selecionado

    state "Estágios terminais" as terminal {
        hired --> [*]
        rejected --> [*]
        cancelled --> [*]
        not_selected --> [*]
    }

    note right of terminal
        Transições FROM terminal stages
        bloqueadas exceto com force=True
        (correções administrativas).
    end note
```

### Estágios terminais

| Estágio | Significado |
|---|---|
| `hired` | Candidato contratado |
| `rejected` | Candidato rejeitado pelo recrutador |
| `cancelled` | Processo cancelado |
| `not_selected` | Candidato não selecionado (decisão final) |

### Regras

1. **Transição livre entre estágios não-terminais** — colunas do kanban são customizáveis por empresa; qualquer transição entre elas é válida.
2. **Terminal = sem saída** — `validate_stage_transition()` levanta `LIAInvalidStateTransition` (HTTP 409) ao tentar mover candidato FROM um estágio terminal.
3. **Escape hatch: `force=True`** — agentes com autoridade explícita (ex: correções administrativas) podem forçar transição de estágio terminal. Uso auditado.
4. **`from_stage=None` sempre permitido** — colocação inicial do candidato no pipeline.
