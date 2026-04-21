#!/usr/bin/env python3
"""propose_sensor.py — Gera draft de sensor a partir de descricao de erro.

Recebe uma descricao curta do erro observado e imprime um esqueleto de:
  1. Classificacao na matriz 2x2 (guide x sensor, computacional x inferencial).
  2. Draft de sensor computacional (teste / lint / schema).
  3. Draft de sensor inferencial alternativo (LLM-as-judge) com aviso de custo.
  4. Mensagem de erro otimizada para LLM.
  5. Item de debito tecnico para propagar em CLAUDE.md / skill.

Uso:
    python3 .agents/skills/harness-engineering/scripts/propose_sensor.py "<descricao do erro>"
    # ou via stdin:
    echo "endpoint X retornou dados de outro tenant" | python3 ...propose_sensor.py

Sem dependencias externas (apenas stdlib).
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass

# Heuristicas de classificacao por palavras-chave -> categoria sugerida.
HEURISTICS: list[tuple[str, str, str]] = [
    # (regex, categoria, justificativa curta)
    (r"\b(tenant|isolation|cross[- ]tenant|empresa errada)\b",
     "Sensor computacional + Guardrail",
     "violacao de tenant isolation — sempre testavel estruturalmente e bloqueavel via decorator"),
    (r"\b(pii|cpf|email|telefone|lgpd|consent)\b",
     "Sensor computacional + Guardrail",
     "PII — exige regex/lint determinista + bloqueio antes do retorno"),
    (r"\b(bias|vies|fairness|dei|estereoti)\b",
     "Sensor computacional (L1) + Sensor inferencial (L2)",
     "fairness — comeca com regex L1, escala para LLM-as-judge L2 quando regex nao basta"),
    (r"\b(timeout|503|504|rate ?limit|429|connection)\b",
     "Sensor computacional",
     "falha transiente de integracao — metric + retry + circuit breaker"),
    (r"\b(invalid (arg|payload)|schema|pydantic|json malformed|tool call)\b",
     "Sensor computacional",
     "validacao de input — Pydantic / JSON Schema no executor"),
    (r"\b(loop infinito|max_steps|iteracao|nao para)\b",
     "Sensor computacional",
     "planning loop sem condicao de parada — limite duro de iteracoes"),
    (r"\b(import (de|from) legacy|caminho deprecat|forbidden import)\b",
     "Sensor computacional",
     "canonical path — CI guard com lista de imports proibidos"),
    (r"\b(tom|empat|grosseiro|formal|persona)\b",
     "Sensor inferencial",
     "qualidade semantica de tom — exige LLM-as-judge"),
    (r"\b(audit|trace|observabil|log estrutur)\b",
     "Sensor computacional",
     "audit trail estruturado — schema obrigatorio + teste de presenca"),
]

DEFAULT_CLASSIFICATION = (
    "Sensor computacional (default)",
    "sem palavra-chave conhecida — comece pelo check determinista mais barato",
)


@dataclass
class Proposal:
    description: str
    classification: str
    justification: str

    def render(self) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", self.description.lower()).strip("_")[:40] or "observed_error"
        return f"""# Proposta de sensor — gerada por harness-engineering

## 1. Erro observado

> {self.description}

## 2. Classificacao (matriz 2x2)

- **Celula sugerida:** {self.classification}
- **Por que:** {self.justification}

## 3. Sensor computacional (PRIMEIRA LINHA — preferir sempre)

```python
# tests/structural/test_{slug}.py
import pytest


def test_{slug}_does_not_regress():
    \"\"\"Garante que <comportamento esperado>.

    Contexto: <link para PR / postmortem / finding de auditoria>.
    Adicionado apos observar: {self.description!r}
    \"\"\"
    # Arrange: prepare input que reproduzia o bug
    # Act: execute o caminho canonico
    # Assert: verifique invariante quebrada antes do fix
    raise NotImplementedError("preencher com reproducao concreta")
```

Alternativas computacionais possiveis (escolher 1):
- Lint customizado em `tools/lint/` que falha em PR.
- Schema validator (Pydantic / JSON Schema) no proprio handler.
- Pre-commit hook bloqueando padrao no diff staged.
- CI guard via GitHub Action.

## 4. Sensor inferencial (FALLBACK CARO — so se 3 for inviavel)

Use LLM-as-judge somente quando o check determinista for impossivel
(ex: avaliar tom, fairness semantica em texto livre, qualidade de design).

```yaml
# evals/inferential/{slug}.yaml
name: {slug}
trigger: pull_request
judge_model: claude-sonnet
rubric: |
  Avalie se a saida {{candidate_output}} viola o seguinte criterio:
  <criterio em linguagem natural>
  Responda APENAS com PASS ou FAIL e justifique em 1 frase.
fail_on: FAIL
```

**Custo estimado:** ~1 chamada LLM por PR / por exemplo. Considerar amostragem.

## 5. Mensagem de erro otimizada para LLM

```
ERROR HARNESS-<categoria>: <resumo objetivo do que falhou>.

CORRECAO: <instrucao concreta — qual arquivo editar, qual linha, qual padrao usar>.

REFERENCIA: CLAUDE.md secao "<X>" / ADR-<NNN> / skill <Y>.

POR QUE: <consequencia se nao corrigir — incidente passado, risco a usuario, etc>.
```

Exemplo concreto preenchido para o caso reportado:

```
ERROR HARNESS-AUTO: {self.description}

CORRECAO: <preencher com guidance acionavel apos investigar root cause>.

REFERENCIA: <preencher com guide canonico>.

POR QUE: <preencher com risco / postmortem>.
```

## 6. Debito tecnico de harness a propagar

- [ ] Adicionar regra em `CLAUDE.md` (ou `AGENTS.md`) descrevendo a invariante.
- [ ] Atualizar skill correspondente (catalogo de sensors / guides).
- [ ] Se o erro pertencer a finding de auditoria, atualizar `references/audit-template.md`
      preenchido com este finding.
- [ ] Considerar promover o teste estrutural para CI guard se o erro reaparecer.

---
*Gerado por `harness-engineering/scripts/propose_sensor.py`. Revise antes de aplicar.*
"""


def classify(description: str) -> tuple[str, str]:
    lower = description.lower()
    for pattern, categoria, justificativa in HEURISTICS:
        if re.search(pattern, lower):
            return categoria, justificativa
    return DEFAULT_CLASSIFICATION


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        description = " ".join(argv[1:]).strip()
    else:
        description = sys.stdin.read().strip()

    if not description:
        print("uso: propose_sensor.py \"<descricao do erro>\"", file=sys.stderr)
        print("     ou: echo \"<descricao>\" | propose_sensor.py", file=sys.stderr)
        return 2

    categoria, justificativa = classify(description)
    proposal = Proposal(description=description,
                        classification=categoria,
                        justification=justificativa)
    print(proposal.render())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
