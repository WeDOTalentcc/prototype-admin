# CONTRIBUTING — LIA Agent System

> Guia de contribuição para o repositório. Leia antes de fazer qualquer commit.  
> Última atualização: 2026-06-16.

---

## Regras de ouro (não-negociáveis)

1. **Commits com pathspec sempre** — `git commit -m "..." -- <path1> <path2>`. Nunca `git add .` nem `git commit` sem pathspec. O índice é compartilhado entre sessões paralelas.
2. **Nunca `git push`** sem autorização textual explícita do responsável do projeto.
3. **Nunca criar branches** sem solicitação explícita.
4. **Sempre verificar branch antes de operar:**
   ```bash
   git branch --show-current   # deve ser feat/benefits-prv-canonical
   git status -s
   ```
5. **Fix no produtor, nunca no consumidor** — se 5 telas exibem dado errado via 1 serviço, o fix é no serviço.

---

## Workflow de contribuição

### 1. Antes de começar

```bash
# Confirmar branch ativa
git branch --show-current

# Verificar status limpo (ou entender o que está sujo)
git status -s

# Verificar commits recentes em arquivos que você vai tocar
git log --since="6 hours ago" -- <arquivo>
```

### 2. Durante o desenvolvimento

- **TDD primeiro**: escreva o teste que falha (Red) antes de escrever o código (Green)
- **Boy Scout Rule**: ao tocar um arquivo, corrigir P2 issues encontrados no mesmo arquivo
- **Reportar P0/P1** encontrados fora do escopo — não corrigir silenciosamente sem documentar

### 3. Antes do commit

```bash
# Rodar sensores de qualidade
make check-pydantic    # ~1s — sem desculpa para pular
make lint              # ruff linting

# Se tocou em endpoints: smoke test
make smoke             # ~34s — requer servidor rodando em :8001

# Se tocou em arquivos Python: pre-commit
pre-commit run --files <arquivos-alterados>
```

### 4. Commit canônico

```bash
# Arquivos já rastreados (tracked):
git commit -m "tipo(escopo): descrição breve

Corpo explicando o porquê (não o quê).

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>" -- path/arquivo1.py path/arquivo2.py

# Arquivo novo (untracked):
git add path/novo_arquivo.py
git commit -m "..." -- path/novo_arquivo.py

# Paths com colchetes (App Router Next.js — não se aplica aqui, mas vale para FE):
GIT_LITERAL_PATHSPECS=1 git commit -m "..." -- "path/[id]/route.ts"
```

> **Verificar após commit:** `git log -1 --stat` — número de arquivos deve bater exatamente com os paths nomeados.

---

## Convenções de commit

Formato: `tipo(escopo): descrição imperativa no presente`

| Tipo | Quando usar |
|---|---|
| `feat` | Nova feature ou endpoint |
| `fix` | Correção de bug |
| `docs` | Documentação |
| `test` | Testes (sem mudança de código de produção) |
| `refactor` | Refatoração sem mudança de comportamento |
| `chore` | Configuração, dependências, CI |
| `perf` | Melhoria de performance |

Exemplos:
```
feat(cv_screening): add eligibility phase before WSI scoring
fix(fairness_guard): wire log_check in SSE chat path (Fix A)
docs(GAP-00-002): add ONBOARDING.md and CONTRIBUTING.md
test(offer): add gate contract tests for approval_required flag
```

---

## Padrões de código

### Python (backend)

#### Schemas Pydantic

- Request bodies herdam de `WeDoBaseModel` (já tem `extra='forbid'`)
- `company_id` nunca aparece em request schema — vem do JWT
- Path params com UUID usam `JobIdParam` / `CandidateIdParam` de `app/shared/types.py`

```python
from app.shared.types import WeDoBaseModel, JobIdParam

class CriarVagaSchema(WeDoBaseModel):  # extra='forbid' incluso
    titulo: str
    departamento: str
    # ❌ NÃO: company_id: str

@router.post("/vagas/{vaga_id}/publicar")
async def publicar(vaga_id: JobIdParam, ...):  # ✅ usa alias canonical
    ...
```

#### Multi-tenancy

```python
# ✅ Canonical — sempre via Depends
from app.shared.tenant_guard import get_verified_company_id

async def handler(company_id: str = Depends(get_verified_company_id)):
    ...

# ❌ Proibido — header overwrite
async def handler(x_company_id: str | None = Header(None, alias="X-Company-ID")):
    ...
```

#### Exception handling

Sem `except Exception: pass` em paths críticos:

```python
# ✅ Falhar alto (preferido em path crítico)
except SpecificException as e:
    logger.error("operation failed: %s", e, exc_info=True)
    raise HTTPException(503, "Service unavailable")

# ✅ Debug log + retorno explícito (path não-crítico)
except Exception as exc:
    logger.debug("[component] operation failed: %s", exc, exc_info=True)
    return None

# ❌ Proibido
except Exception:
    pass
```

#### Repository pattern (ADR-001)

```python
# ✅ Services via repositório
class MeuService:
    async def buscar(self, company_id: str, db: AsyncSession):
        repo = MeuRepositorio(db)
        return await repo.list_by_company(company_id)

# ❌ Proibido: SQL inline em service
result = await db.execute(select(Modelo).where(Modelo.company_id == company_id))
```

Exceção documentada com `# ADR-001-EXEMPT: <razão>`.

#### Fairness e LGPD

```python
# ✅ Todo endpoint com texto livre de recrutador → FairnessGuard antes do LLM
from app.shared.compliance.fairness_guard import FairnessGuard

_fg = FairnessGuard()
result = _fg.check(user_text)
if result.is_blocked:
    raise HTTPException(400, detail={
        "error": "fairness_blocked",
        "fairness_blocked": True,
        "educational_message": result.educational_message,
        "category": result.category,
        "blocked_terms": result.blocked_terms or [],
    })
```

---

## Pre-commit hooks

O `.pre-commit-config.yaml` inclui:

| Hook | O que faz | Blocking? |
|---|---|---|
| `ruff` | Linting + auto-fix | Sim |
| `ruff-format` | Formatação | Sim |
| `mypy-warn-only` | Type check | Não (warn-only) |
| `no-sql-in-controllers` | G1: sem SQL raw em `app/api/` | Sim |
| `no-pii-in-logs` | G4: LGPD — sem PII em logs | Sim |
| `response-model-required` | G2: todo endpoint tem `response_model=` | Sim |
| `tenant-db-required` | G-TENANTDB: `get_tenant_db` em domains | Sim |
| `pydantic-conventions-warn` | R1+R2+R3+R4 conventions | Warn-only |

Instalar uma vez:
```bash
pre-commit install
```

Rodar manualmente:
```bash
pre-commit run --files app/api/v1/meu_endpoint.py
pre-commit run --all-files  # roda em tudo (lento)
```

---

## Requisitos de testes

### Filosofia

- **TDD obrigatório para bugs** — escreva o teste Red antes do fix
- **Cobertura mínima em code paths críticos** — compliance, fairness, multi-tenancy, offer gates
- **Testes de contrato** para todo novo contrato de API ou shape de dados

### Estrutura de testes

```
tests/
├── unit/         # Testes unitários puros (sem DB, sem HTTP)
├── contract/     # Testes de contrato de API e shapes de dados
├── integration/  # Testes com banco/redis/serviços reais
├── e2e/          # Fluxos end-to-end
└── fixtures/     # Fixtures compartilhadas
```

### Rodando testes

```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=app tests/

# Arquivo específico
pytest tests/unit/test_fairness_guard.py -v

# Categoria específica
pytest tests/contract/ -v --tb=short

# Testes rápidos (sem IO)
pytest tests/unit/ -v
```

### Padrão de teste para novos endpoints

```python
# tests/contract/test_meu_recurso.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_criar_item_sem_company_id_retorna_401(client: AsyncClient):
    resp = await client.post("/api/v1/itens", json={"nome": "teste"})
    assert resp.status_code == 401

@pytest.mark.asyncio
async def test_criar_item_com_company_id_no_body_retorna_422(
    authed_client: AsyncClient,
):
    resp = await authed_client.post(
        "/api/v1/itens",
        json={"nome": "teste", "company_id": "qualquer"},  # proibido
    )
    assert resp.status_code == 422  # extra='forbid'
```

---

## Checklist de PR / revisão

Antes de considerar uma mudança pronta:

### Qualidade de código
- [ ] `make check-pydantic` — 0 violations (ou baseline mantido)
- [ ] `make lint` — 0 erros ruff
- [ ] `pre-commit run --files <alterados>` — todos hooks passando
- [ ] Sem `except Exception: pass` em paths críticos
- [ ] Sem SQL inline em services (ADR-001)

### Segurança e compliance
- [ ] `company_id` vem do JWT — nunca do payload
- [ ] Sem `x_company_id` header override
- [ ] Sem hardcoded secrets ou API keys
- [ ] Endpoints com texto livre de recrutador têm `FairnessGuard`
- [ ] PII não aparece em log statements
- [ ] Dado sensível (raça/gênero/etc) não é processado em decisões de IA

### Testes
- [ ] Teste Red escrito antes do fix (TDD)
- [ ] Todos os testes verdes (`pytest tests/unit/ tests/contract/`)
- [ ] Teste de contrato para shape de dados novo
- [ ] Teste `_reset_tenant_contextvar` se usar ContextVars de tenant

### Commit e versionamento
- [ ] Commit com pathspec (`git commit -m "..." -- path/arquivo.py`)
- [ ] `git log -1 --stat` confirma exatamente os arquivos esperados
- [ ] Mensagem de commit no formato `tipo(escopo): descrição`
- [ ] Sem `git push` (empurrar para remoto requer autorização explícita)

### Migration de banco
- [ ] Número sequencial verificado antes de criar
- [ ] Migration não destrói dados existentes (add column nullable ou com default)
- [ ] `alembic upgrade head` rodou sem erro localmente
- [ ] `alembic downgrade -1` testado (reversibilidade)

---

## Sensores de qualidade — referência rápida

| Sensor | Comando | Blocking? |
|---|---|---|
| Pydantic R1+R2+R3+R4 | `make check-pydantic` | R3 blocking; R1+R2 warn |
| Import paths canônicos | `make check-imports` | Blocking |
| Smoke test endpoints | `make smoke` | Blocking (baseline) |
| Conformidade de domínio | `make check-domain-conformance` | Blocking |
| SQL inline em services | `python3 scripts/check_no_select_in_services.py` | Blocking |
| FairnessGuard coverage | `python3 scripts/check_agent_hitl_gates.py` | Warn |
| Alembic single head | `python3 scripts/check_alembic_singlehead.py` | Warn |

Rodar tudo: `make check-all` (~35s).

---

## Referências

- `CLAUDE.md` (raiz do repo) — regras de harness para agentes IA
- `app/shared/types.py` — tipos canônicos (`WeDoBaseModel`, `JobIdParam`)
- `app/shared/tenant_guard.py` — multi-tenancy canonical
- `app/shared/compliance/fairness_guard.py` — FairnessGuard
- `Makefile` — `make help` para todos os targets
- `scripts/README.md` — documentação dos sensores
- `docs/` — ADRs e specs técnicas
