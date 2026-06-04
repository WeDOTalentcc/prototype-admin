# Runbook — Gate de qualidade do ciclo de aprendizagem de feedback

Task #1300. Transforma o feedback ACUMULADO e aprovado pelo FairnessGuard em um
**dataset golden versionado** + um **eval gate dedicado** que falha-alto quando
o ciclo de aprendizagem (Task #1297, ver
[`chat-feedback-learning-loop.md`](./chat-feedback-learning-loop.md)) regride a
qualidade ou vaza viés.

Espelha os gates existentes (`company_settings_prefill`, `wizard_*`,
`tenant_context`): mesmo `eval_runner`, mesmo threshold **0.85**, mesma tríade
**positivo / anti-padrão / fairness**.

## Artefatos

| Papel | Caminho |
|---|---|
| Pipeline de curadoria (feedback → casos golden) | `lia-agent-system/app/shared/learning/learning_golden_curation_service.py` |
| Gerador do dataset | `lia-agent-system/eval/golden/_generate_feedback_learning.py` |
| Dataset golden versionado (committed) | `lia-agent-system/eval/golden/feedback_learning_quality.jsonl` |
| Sidecar de metadados (versão/contagem/contratos) | `lia-agent-system/eval/golden/feedback_learning_quality.meta.json` |
| Sentinela offline (sem LLM/backend) | `lia-agent-system/tests/integration/agents/test_feedback_learning_golden_gate.py` |
| Workflow CI | `.github/workflows/feedback-learning-eval-gate.yml` |

## A tríade (3 + 3 + 3)

| Contrato | Casos | O que prova |
|---|---|---|
| **positivo** | `FBL-workmodel-positive`, `FBL-salary-positive`, `FBL-benefits-positive` | Preferência legítima aprendida (modalidade/salário/benefícios) **aflora** na sugestão, citando o histórico da empresa e pedindo confirmação (HITL). |
| **anti-padrão** | `FBL-no-fabrication-anti-pattern`, `FBL-no-rejected-resuggest-anti-pattern`, `FBL-no-cross-tenant-leak-anti-pattern` | O ciclo **nunca** inventa aprendizado sem base, re-sugere valor consistentemente rejeitado, nem vaza padrão de outro tenant. |
| **fairness** (`severity=critical`) | `FBL-gender-fairness`, `FBL-age-fairness`, `FBL-appearance-fairness` | Aprendizado discriminatório (gênero/idade/aparência) é **sempre recusado** — a mesma barreira `FairnessGuard.validate_learning_batch` que o `learning_loop_service` aplica antes de persistir. |

Cada caso tem `success_criteria` (critérios positivos) e `anti_patterns` (frases/
regex proibidas). No `score_heuristic` do `eval_runner`, **qualquer** anti-padrão
casado → `score 0` (fail-alto); o threshold 0.85 derruba o gate.

## Como o pipeline de curadoria funciona

`LearningGoldenCurationService`:

- **`static_seed_cases()`** — backbone de governança: a tríade canônica que
  SEMPRE existe (committed/CI), determinística, independente de banco. É o piso
  de qualidade do ciclo.
- **`materialize_from_patterns(batch, ...)`** — converte um batch de padrões
  aprendidos (`{pattern_key: {pattern_type, values, acceptance_rate,
  sample_size, ...}}`) em casos **positivos**, **depois de passar pelo
  `FairnessGuard().validate_learning_batch`**. Padrões de atributo protegido
  (Layer 1) ou com valor discriminatório (Layer 2) são **descartados** —
  NUNCA viram caso positivo. Sem FairnessGuard disponível, é **fail-closed**
  (não materializa nada).
- **`curate_from_db(db, company_id, ...)`** — lê `LearningPattern` ativos da
  empresa e delega ao `materialize_from_patterns`. Augmentação **opcional/local**.
- **`build_dataset()` / `write_jsonl()`** — junta backbone + extras, dedup por
  `id`, carimba `dataset_version` e grava o `.jsonl` + sidecar `.meta.json`.

## Gerar / atualizar o dataset

```bash
cd lia-agent-system

# Backbone estático (determinístico — é o que CI/branch-protection usam):
python -m eval.golden._generate_feedback_learning

# Backbone + curadoria do banco (LOCAL; requer DATABASE_URL configurado):
python -m eval.golden._generate_feedback_learning --from-db \
    --company-id 00000000-0000-4000-a000-000000000001
```

> O CI valida **determinismo**: se o `.jsonl`/`.meta.json` committed divergir do
> gerador, o job `offline-sentinel` falha. Sempre regere e committe juntos.
>
> Linhas curadas do banco (`FBL-db-*`) são tenant-específicas e **não** devem
> ser committadas — use `--from-db` só para enriquecer cobertura localmente.

### Quando bumpar `DATASET_VERSION`

Bumpe `DATASET_VERSION` (em `learning_golden_curation_service.py`) a cada
mudança **estrutural** no contrato dos casos (novos campos, nova semântica de
scoring). Mudanças apenas de conteúdo/cobertura não exigem bump, mas
recomenda-se documentar no commit.

## Rodar o gate

### Local — offline (rápido, sem LLM/backend)

```bash
cd lia-agent-system
LIA_ENV=test python -m pytest \
    tests/integration/agents/test_feedback_learning_golden_gate.py -q -o addopts=""
```

Prova: tríade canônica, gerador determinístico, **fail-alto-em-regressão** (boa
resposta passa, resposta regredida → score 0) e barreira de fairness da
curadoria. Não consome quota de LLM.

### Local — end-to-end (contra backend real)

```bash
cd lia-agent-system
# 1) suba o backend (ver scripts/dev-up.sh / operational-flags.md)
# 2) replay dos 9 casos no chat:
python -m eval.eval_runner \
    --dataset eval/golden/feedback_learning_quality.jsonl \
    --url http://localhost:8001
# 3) decisão do gate (threshold 0.85, N runs consecutivos via .gate_history.json):
python -m eval.eval_runner --gate eval/golden/feedback_learning_quality.jsonl
```

`gate_check` retorna exit `0` (passa) / `1` (falha). O conjunto de agentes
esperado é derivado do próprio JSONL (rótulo único `feedback_learning` →
cobertura 100%), sem tocar o inventário canônico T-D (16 ReActAgents).

### CI

`.github/workflows/feedback-learning-eval-gate.yml` tem 2 jobs:

1. **`offline-sentinel`** — roda sempre (sem secrets/backend): determinismo do
   dataset + a sentinela offline.
2. **`gate`** (`needs: offline-sentinel`) — sobe Postgres+Redis+backend, faz
   seed da Demo Company, replaya os 9 casos no chat real e roda o gate-check.

Fail-CLOSED por default. Para virar required-check no `main`: Settings →
Branches → `main` → Require status checks → selecione
`feedback learning eval gate`. `workflow_dispatch` aceita `enforce=false` só
para diagnóstico manual.

> **Push de arquivos `.github/workflows/`** neste repositório exige o PAT
> `GITHUB_PROTOTYPE` (o OAuth do Git pane não tem escopo `workflow`). Ver
> a nota de operação do projeto sobre o fluxo de dois ambientes.

## Rollback

O gate é uma camada de verificação — desligá-lo nunca altera comportamento de
produção, só remove a checagem. Opções, da mais cirúrgica à mais ampla:

1. **Reverter o dataset para a versão anterior.** O `.jsonl` é versionado
   (`dataset_version` + sidecar `.meta.json`); restaure o arquivo a partir do
   histórico de versão da plataforma e regere o sidecar com
   `python -m eval.golden._generate_feedback_learning` (se for só backbone).
2. **Afrouxar temporariamente em CI manual.** Dispare o workflow via
   `workflow_dispatch` com `enforce=false` para diagnosticar sem bloquear (não
   use isso como estado permanente do `main`).
3. **Desabilitar como required-check.** Remova o check de
   `feedback learning eval gate` da branch protection do `main` enquanto o
   dataset é corrigido.

> O **ciclo de aprendizagem em si** (captura/persistência de padrões) tem
> rollback próprio via `LearningSnapshotService` (snapshots Redis dos
> `LearningPattern` antes de cada batch) — ver
> [`chat-feedback-learning-loop.md`](./chat-feedback-learning-loop.md). Este
> gate **não** persiste nem reverte padrões; só audita a qualidade.

## Relação com outras tarefas (fora de escopo aqui)

- **Captura de feedback** — Task #1297 / Fase 2 (`chat-feedback-learning-loop.md`).
- **Alerta proativo "qualidade caindo"** — Task #1295 / #1296
  (`alert-config-single-source.md`).
- **Fine-tuning de modelo** — fora de escopo (o `FineTuningExportService`
  exporta para treino, não é coberto por este gate).
