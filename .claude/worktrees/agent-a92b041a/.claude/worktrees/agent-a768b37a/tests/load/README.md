# T4 — Testes de Carga com Locust

Testes de carga para os endpoints críticos da LIA Platform:
- Wizard de criação de vaga (LLM-heavy)
- Pipeline de movimentação de candidatos (CRUD-heavy)

## Pré-requisitos

```bash
pip install locust
```

## Executar localmente (modo web)

```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

Acesse `http://localhost:8089` para a interface web do Locust.

## Executar em modo headless

```bash
# Teste rápido: 20 usuários, spawn 2/s, 60 segundos
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --headless \
  --users=20 \
  --spawn-rate=2 \
  --run-time=60s \
  --html=tests/load/reports/report_$(date +%Y%m%d_%H%M%S).html

# Teste de carga completo: 50 usuários, spawn 5/s, 120 segundos
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --headless \
  --users=50 \
  --spawn-rate=5 \
  --run-time=120s \
  --html=tests/load/reports/report_full_$(date +%Y%m%d_%H%M%S).html
```

## Targets de Performance Aceitável

| Métrica | Target |
|---------|--------|
| p50 (mediana) | < 500ms |
| p95 | < 2.000ms (2s) |
| p99 | < 5.000ms (5s) |
| Error rate | < 1% |

Estes targets são para o ambiente de staging com dados de teste.
Em produção, ajustar conforme o perfil real de carga.

## Configuração dos Dados de Teste

Editar `tests/load/load_test_config.py`:

```python
# IDs de teste — usar IDs reais do ambiente de staging
TEST_JOB_IDS = ["uuid-da-vaga-1", "uuid-da-vaga-2", ...]
TEST_VACANCY_CANDIDATE_IDS = ["uuid-vc-1", "uuid-vc-2", ...]
```

## User Classes

| Classe | Descrição | Weight |
|--------|-----------|--------|
| `WizardUser` | Criação de vagas via chat LIA | Alto (default) |
| `PipelineUser` | Movimentação de candidatos | Alto (default) |
| `HealthCheckUser` | Monitoramento de health | Baixo (weight=1) |

## Saída Esperada

Ao finalizar, o Locust exibe um relatório de conformidade com os targets:

```
============================================================
📊 RESUMO DO TESTE DE CARGA — LIA Platform
============================================================

  /wizard/chat
    ✅ p50: 450ms (target: <500ms)
    ✅ p95: 1800ms (target: <2s)
    ✅ p99: 4200ms (target: <5s)
    ✅ error rate: 0.12% (target: <1%)

  /pipeline/transition
    ✅ p50: 120ms (target: <500ms)
    ✅ p95: 380ms (target: <2s)
    ...
```

## CI/CD Integration

Para integrar ao CI (GitHub Actions):

```yaml
- name: Load Tests
  run: |
    pip install locust
    locust -f tests/load/locustfile.py \
      --host=${{ env.STAGING_URL }} \
      --headless \
      --users=20 \
      --spawn-rate=2 \
      --run-time=60s \
      --csv=tests/load/results/ci_$(date +%Y%m%d)
```
