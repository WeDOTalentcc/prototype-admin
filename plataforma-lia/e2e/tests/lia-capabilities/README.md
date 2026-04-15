# LIA Capabilities Test Suite

Suíte de testes exaustivos da LIA — uso pré-lançamento ou em CI.

Derivada de `lia-agent-system/app/tools/tool_registry_metadata.yaml` (76 tools)
+ `docs/architecture/ARCHITECTURE.md` §7.5 (Cascaded Router / 8 tiers).

## Estrutura

```
lia-capabilities/
├── README.md                    (este arquivo)
├── helpers.ts                   utilidades (ensureChatOpen, sendPromptAndCapture, expectCapabilitySuccess)
├── catalog.ts                   catálogo de 70 capabilities (tool + prompt + expectativas)
├── capabilities-suite.spec.ts   Camada 1 — 1 teste por capability
└── journeys.spec.ts             Camada 3 — 5 jornadas E2E multi-turn
```

Relacionado (Camada 2 — qualidade LLM-judge):
- `lia-agent-system/tests/eval/datasets/lia_capabilities/scenarios.yaml`
- `lia-agent-system/tests/eval/datasets/lia_capabilities/run_eval.py`

## Rodar

### Pré-requisito — proxy local para Replit

O `.claude/replit-proxy.js` já existe e expõe a instância Replit em `http://localhost:3333`.

```bash
# Em terminal separado
node .claude/replit-proxy.js
```

### Camada 1 — todas as capabilities

```bash
cd plataforma-lia
PLAYWRIGHT_BASE_URL=http://localhost:3333 \
  npx playwright test lia-capabilities/capabilities-suite
```

### Camada 1 — filtrar por severidade

```bash
# Só críticos (release gate)
PLAYWRIGHT_BASE_URL=http://localhost:3333 \
  npx playwright test lia-capabilities/capabilities-suite --grep @critical

# Só bugs conhecidos (regressão)
npx playwright test lia-capabilities/capabilities-suite --grep "@BUG-"
```

### Camada 1 — filtrar por domínio

```bash
# Só jobs
npx playwright test lia-capabilities/capabilities-suite --grep "@domain:jobs-mgmt"

# Só pipeline
npx playwright test lia-capabilities/capabilities-suite --grep "@domain:pipeline"
```

### Camada 3 — jornadas

```bash
PLAYWRIGHT_BASE_URL=http://localhost:3333 \
  npx playwright test lia-capabilities/journeys
```

### Camada 2 — quality eval (LLM-judge)

Requer `ANTHROPIC_API_KEY` + `JWT_TOKEN` válido do backend.

```bash
cd lia-agent-system
ANTHROPIC_API_KEY=sk-ant-... \
JWT_TOKEN=eyJ... \
BACKEND_URL=http://localhost:8000 \
  python -m tests.eval.datasets.lia_capabilities.run_eval \
  --output results/lia_capabilities_$(date +%Y%m%d).json

# Filtrar só críticos
python -m tests.eval.datasets.lia_capabilities.run_eval \
  --filter critical --output results/lia_crit.json
```

## Interpretando resultados

### Relatório HTML do Playwright

```bash
npx playwright show-report
```

Cada teste tem tags (`@critical`, `@domain:X`, `@BUG-N`) — use o filtro da UI.

### JSON da Camada 2

```jsonc
{
  "total": 18,
  "passed": 15,
  "pass_rate": 0.833,
  "by_severity": {
    "critical": { "total": 8, "passed": 7 },
    "high": { "total": 6, "passed": 5 }
  },
  "results": [
    {
      "id": "jobs-mgmt-001",
      "name": "Lista vagas abertas (BUG-17)",
      "score": 2.4,
      "threshold": 2.0,
      "passed": true,
      "judge": {
        "understanding": 3,
        "helpfulness": 2,
        "proactivity": 2,
        "accuracy": 3,
        "tone": 2
      }
    }
  ]
}
```

## Release Gate sugerido

| Camada | Métrica | Mínimo |
|---|---|---|
| 1 — Funcional | % PASS geral | ≥ 90% |
| 1 — Funcional (críticos) | % PASS @critical | 100% |
| 3 — Jornadas | Todos PASS | 100% |
| 2 — Qualidade (críticos) | score médio `@critical` | ≥ 2.3 |
| 2 — Qualidade (geral) | pass_rate | ≥ 70% |
| Regressão | BUG-01..BUG-18 | 0 falhas |

## Manutenção

- Novo tool no `tool_registry_metadata.yaml` → adicionar entrada em `catalog.ts` + `scenarios.yaml`
- Novo bug crítico → adicionar teste `@BUG-N` + marcar no `relatedBug` da capability
- Mudança em `domain_routing.yaml` → re-rodar Camada 1 completa pra pegar regressões de roteamento

## ARCHITECTURE.md — decisões respeitadas

- `catalog.ts` não hardcodes tool dispatch — lista só o que o registry expõe
- Prompts em PT-BR refletem o tom do `rubrics/chat.yaml`
- `allowLenientFail` reservado para capabilities que dependem de dados (não-determinísticas)
