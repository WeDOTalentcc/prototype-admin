# Load Tests — Plataforma LIA (Sprint K3)

Testes de carga usando [Locust](https://locust.io/) para validar SLAs da plataforma LIA.

## Cenários

| Tarefa | Endpoint | Peso | SLA P95 |
|--------|----------|------|---------|
| `candidate_search` | `GET /api/v1/candidates/rag-search` | 40% | 2 000 ms |
| `toon_card` | `GET /api/v1/candidates/{id}/toon` | 30% | 3 000 ms |
| `wizard_interaction` | `POST /api/v1/chat` | 20% | 4 000 ms |
| `wsi_screening_batch` | `POST /api/v1/wsi/sessions` | 10% | 5 000 ms |

## Instalação

```bash
pip install locust
```

## Uso

### Modo interativo (UI web em localhost:8089)
```bash
cd lia-agent-system
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

### Modo headless (CI/CD)
```bash
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --users=50 --spawn-rate=5 \
  --run-time=5m --headless \
  --csv=results/load_test
```

## Perfis de Carga

| Perfil | Usuários | Spawn Rate | Duração | Propósito |
|--------|----------|-----------|---------|-----------|
| `smoke` | 5 | 1/s | 1 min | Verificar funcionamento básico |
| `load` | 50 | 5/s | 5 min | Carga normal de produção |
| `stress` | 200 | 10/s | 10 min | 4× a carga esperada |
| `soak` | 30 | 2/s | 60 min | Detectar vazamentos de memória |

## Variáveis de Ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `LIA_AUTH_TOKEN` | `test-token` | Bearer token de autenticação |
| `LIA_COMPANY_ID` | `c-load-001` | company_id de testes |

## Validação de SLA

Ao final de cada execução, o script valida automaticamente os SLAs definidos em `load_test_config.py`.
O processo retorna código 1 se qualquer SLA for violado — integrável com CI/CD.

## Arquivos

```
tests/load/
├── locustfile.py        ← Definição dos cenários de teste
├── load_test_config.py  ← Configuração de SLAs, perfis e dados de teste
└── README.md            ← Este arquivo
```
