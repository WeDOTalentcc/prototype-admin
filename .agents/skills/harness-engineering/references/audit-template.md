# Audit Template — Harness de Agente

Use como esqueleto para auditoria formal de harness de um agente / projeto / repositorio. Produz relatorio em formato consumivel por humano e por LLM.

---

# Auditoria de Harness — `<nome do projeto / agente>`

**Data:** YYYY-MM-DD
**Auditor:** `<nome ou skill>`
**Escopo:** `<repo / subsistema / agente especifico>`
**Versao do guia:** `harness-engineering` SKILL.md vX.Y

## Sumario executivo (3 linhas)

- Maturidade geral: `[Nascente | Em construcao | Solido | Avancado]`
- Componentes criticos descobertos: `<lista>`
- Risco residual mais alto: `<descricao curta>`

## Gap matrix por componente

Status: `OK` | `PARCIAL` | `AUSENTE` | `N/A`

| #  | Componente            | Status   | Evidencia (arquivo/linha/PR) | Risco se nao corrigido          | Acao proposta                     |
|----|-----------------------|----------|------------------------------|---------------------------------|-----------------------------------|
| 1  | Planning loop         |          |                              |                                 |                                   |
| 2  | Tool layer            |          |                              |                                 |                                   |
| 3  | Context management    |          |                              |                                 |                                   |
| 4  | Memoria               |          |                              |                                 |                                   |
| 5  | Sandbox               |          |                              |                                 |                                   |
| 6  | State persistence     |          |                              |                                 |                                   |
| 7  | Guides                |          |                              |                                 |                                   |
| 8  | Sensors               |          |                              |                                 |                                   |
| 9  | Error handling        |          |                              |                                 |                                   |
| 10 | Guardrails            |          |                              |                                 |                                   |
| 11 | Serving layer         |          |                              |                                 |                                   |

## Findings detalhados

Para cada componente com status `PARCIAL` ou `AUSENTE`, abrir secao:

### Finding F-NN: `<titulo curto>`

- **Componente:** `<n>` `<nome>`
- **Severidade:** `[Critico | Alto | Medio | Baixo]`
- **Descricao:** o que esta faltando ou parcial.
- **Como se manifesta:** sintoma observavel hoje (bug recorrente, regressao, risco latente).
- **Classificacao na matriz 2x2:** `[Guide computacional | Guide inferencial | Sensor computacional | Sensor inferencial | Guardrail]`.
- **Tipo de falha relacionada (taxonomia):** `[Transient | LLM-recoverable | User-fixable | Unexpected | Compliance | Tenant breach]`.
- **Acao proposta:**
  - Guide proposto (feedforward): onde vive, conteudo, tipo, justificativa.
  - Sensor proposto (feedback): onde vive, conteudo, tipo, mensagem de erro otimizada para LLM.
- **Esforco estimado:** `[XS | S | M | L]`.
- **Skill LIA relacionada:** `<canonical-fix | feature-audit | lia-compliance | ...>`.

## Mapeamento para o 6-stage remediation plan

| Finding | Stage relacionado (1-6) | Status do Stage |
|---------|------------------------|-----------------|
| F-01    |                        |                 |
| F-02    |                        |                 |

## Debito tecnico de harness a propagar

Lista de itens que precisam virar entrada permanente em `CLAUDE.md`, `AGENTS.md` ou skill — princípio Hashimoto: nunca mais aquele erro especifico.

- [ ] `<item 1>` → propagar para `<arquivo>`
- [ ] `<item 2>` → propagar para `<skill>`

## Proximos passos recomendados

1. Implementar findings de severidade `Critico` antes de qualquer feature nova.
2. Agendar reaudita em `<prazo>` apos implementacao.
3. Considerar promover findings recorrentes para CI guard automatico.

---

## Anexo A — Comandos executados

```bash
python3 .agents/skills/harness-engineering/scripts/scan_claude_md.py .
# saida resumida: ...
```

## Anexo B — Referencias

- `harness-engineering/SKILL.md` (matriz, workflow, anti-patterns)
- `harness-engineering/references/failure-taxonomy.md`
- `harness-engineering/references/guides-catalog.md`
- `harness-engineering/references/sensors-catalog.md`
