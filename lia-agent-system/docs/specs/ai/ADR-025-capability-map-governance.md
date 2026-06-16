# ADR-025 — Capability Map Governance

**Status:** Accepted
**Date:** 2026-05-02
**Related:**
- ADR-024 (Four-Registry Architecture)
- ADR-022 (Tool Registry Taxonomy)
- `app/config/capability_map.yaml`
- `scripts/check_capability_map.py` (sensor a criar)
- UC-P1-28 (ghost card root cause)

---

## Context

O `capability_map.yaml` é lido em runtime pelo Rail A UI para construir os cards de capability disponíveis ao usuário. A auditoria UC-P1-28 identificou que cards "fantasma" (ghost cards — visíveis na UI mas sem ação ao clicar) surgiam quando:

1. Uma entry em `capability_map.yaml` referenciava um `tool_name` não registrado em `app/tools/registry.py`.
2. Uma entry era adicionada ao YAML antes da implementação da tool correspondente (deploy dessincronizado).
3. Uma capability que abre modal não tinha `modal_id` definido, causando clique sem resposta.

O processo atual de adicionar uma capability era informal: editar o YAML e fazer deploy. Não havia gate de validação.

## Decision

### Processo obrigatório para adicionar uma nova capability

Toda nova entrada em `capability_map.yaml` requer **todos** os seguintes gates antes de chegar a produção:

1. **JIRA issue aberta** com o epicode da capability, descrevendo o caso de uso e as tools que ela invoca.
2. **Implementação das tools** — todos os `tool_name` referenciados na nova capability devem existir registrados em `app/tools/registry.py` com `ToolDefinition` completo (incluindo `output_schema`).
3. **QA em staging** — o card de capability deve ser testado manualmente em staging (`https://staging2.wedotalent.cc`) confirmando: card visível, clique funciona, resultado correto.
4. **`modal_id` obrigatório** para capabilities que não são executáveis via chat (i.e., qualquer capability que abre um modal ou inicia um fluxo com UI dedicada). Capabilities puramente via chat podem omitir `modal_id`.

### Schema canônico de uma entry

```yaml
capabilities:
  - name: "search_candidates"           # slug único, kebab-case
    label: "Buscar Candidatos"           # label PT-BR para UI
    tool_names:                          # lista; min 1
      - "search_candidates_tool"
    permissions:                         # scopes de acesso
      - "TALENT_FUNNEL"
    modal_id: null                       # null = executa via chat
    jira_issue: "LIA-XXX"               # obrigatório

  - name: "invite_candidate"
    label: "Convidar Candidato"
    tool_names:
      - "send_candidate_invite_tool"
    permissions:
      - "IN_JOB"
    modal_id: "invite-candidate-modal"   # abre modal
    jira_issue: "LIA-YYY"
```

### Guard de CI: `scripts/check_capability_map.py`

O sensor `check_capability_map.py` (a criar no Sprint seguinte) executa como pre-commit hook e falha se:

- Qualquer `tool_name` em `capability_map.yaml` não existir como key registrada em `app/tools/registry.py`.
- Uma entry não tiver `jira_issue` definido.
- Uma entry com `modal_id: null` referenciar uma tool marcada como `ui_only: true` no registry.

Mensagem de erro do sensor deve incluir instrução de correção em linguagem natural (otimizado para consumo por LLM e humanos):

```
ERRO capability_map: tool 'invite_candidate_v2' referenciada em capability 'invite_candidate'
não existe em app/tools/registry.py.

Para corrigir: implemente a tool com @tool_handler e registre em initialize_tools(),
ou corrija o tool_name para apontar para uma tool existente (ex: 'send_candidate_invite_tool').
```

## Consequences

**Positivo:**
- Ghost cards eliminados: impossível chegar a produção com `tool_name` inexistente.
- Rastreabilidade: toda capability tem JIRA issue associado.
- Deploy sincronizado: YAML e implementação de tool chegam no mesmo PR.
- Erros do sensor são acionáveis por LLM (instruções de correção em linguagem natural).

**Negativo:**
- Processo de adicionar capability é mais lento (gates obrigatórios). Aceito: o custo de ghost cards em produção é maior.
- `jira_issue` obrigatório pode ser contornado com placeholders (ex: "LIA-TODO"). Mitigação: o sensor pode validar formato `LIA-\d+` — a ser adicionado como evolução do guard.

## Não-decisões

- Se `capability_map.yaml` deve ser movido para DB (configurável por tenant). Candidato natural para evolução futura quando tenants precisarem de capabilities diferentes; fora do escopo deste ADR.
- Se o guard deve também validar que `permissions` batem com os scopes em `tool_permissions.yaml`. Recomendado como evolução do sensor na próxima iteração.
