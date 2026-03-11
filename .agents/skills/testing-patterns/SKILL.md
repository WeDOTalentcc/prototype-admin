---
name: testing-patterns
description: "Pirâmide de testes da Plataforma LIA — 5 camadas obrigatórias: Produto (Jam.dev), Unitário (pytest/Vitest), Integração (FastAPI endpoints), E2E (Playwright) e Contrato+Fairness (agent-to-agent e bias tests). Use ao criar novos endpoints, componentes, agentes ou ao planejar cobertura de testes para qualquer feature."
---

# Testing Patterns — Pirâmide de Testes da Plataforma LIA

Skill de referência para a estratégia de testes da Plataforma LIA. Cobre as 5 camadas obrigatórias, ferramentas, padrões de código e integração com o fluxo de desenvolvimento (Jam.dev → CI/CD).

> **Skills relacionadas:** feature-audit (D5 Tipos, D6 Fluxo), wedo-governance (Production Readiness gate), screening-compliance (bias tests)

## 1. Quando Usar

- Ao criar novos endpoints REST (FastAPI)
- Ao criar novos componentes ou hooks de frontend
- Ao criar ou modificar agentes IA (LangGraph)
- Ao planejar cobertura de testes para uma feature nova
- Ao identificar um bug reportado via Jam.dev
- Ao verificar cobertura antes de marcar uma tarefa como concluída

---

## 2. Pirâmide de Testes — 5 Camadas

```
┌──────────────────────────────────┐
│  CAMADA 5: Contrato + Fairness   │  ← agent-to-agent, bias/fairness tests
├──────────────────────────────────┤
│  CAMADA 4: E2E                   │  ← Playwright (fluxos críticos)
├──────────────────────────────────┤
│  CAMADA 3: Integração            │  ← FastAPI endpoints com mocks
├──────────────────────────────────┤
│  CAMADA 2: Unitário              │  ← pytest (BE) / Vitest (FE)
├──────────────────────────────────┤
│  CAMADA 1: Produto               │  ← Jam.dev (captura visual + sessão)
└──────────────────────────────────┘
```

| Camada | Ferramenta | Responsável | Quando |
|--------|-----------|-------------|--------|
| Produto | Jam.dev | PM / QA | Validação visual, regressões visuais, bug reports |
| Unitário | pytest / Vitest | Dev | Todo PR com lógica de negócio |
| Integração | pytest + httpx / Vitest | Dev | Todo PR com endpoints ou integrações |
| E2E | Playwright | Dev / QA | Fluxos críticos, pré-release |
| Contrato + Fairness | pytest + custom | Dev | Agentes IA e decisões sobre candidatos |

---

## 3. Camada 1 — Produto (Jam.dev)

Jam.dev captura bugs visuais com sessão completa gravada (console, network, ações do usuário).

### Fluxo de Bug Report via Jam.dev

```
Bug visual encontrado
    ↓
Jam.dev captura sessão (console + network + vídeo)
    ↓
Link Jam.dev gerado automaticamente
    ↓
Card criado no fluxo de desenvolvimento com:
  - Link da sessão Jam.dev
  - Screenshot do estado com bug
  - Console errors relevantes
  - Reprodução: passos + ambiente
    ↓
Dev reproduz localmente → escreve teste unitário/integração para cobrir o caso
    ↓
Fix + teste → PR
```

### O que incluir em um card gerado via Jam.dev

- Link da sessão Jam.dev (obrigatório)
- Ambiente (prod / staging / local)
- Browser / OS
- Usuário afetado (company_id — nunca PII)
- Reprodução mínima
- Expected vs. Actual behavior
- Severidade (P0/P1/P2/P3)

---

## 4. Camada 2 — Unitário

### Backend (pytest)

**Localização:** `lia-agent-system/tests/unit/`

**Padrão de arquivo:** `test_<module>_<function>.py`

```python
# tests/unit/test_wsi_scorer.py
import pytest
from app.services.wsi_scorer import WSIScorer

class TestWSIScorer:
    def test_score_above_threshold_returns_recommended(self):
        scorer = WSIScorer()
        result = scorer.evaluate(scores={"technical": 8.0, "behavioral": 7.5, ...})
        assert result.category == "recommended"
        assert result.score >= 7.0

    def test_protected_attributes_masked_before_evaluation(self):
        scorer = WSIScorer()
        input_data = {"name": "João Silva", "gender": "M", "technical": 7.0}
        result = scorer.evaluate(input_data)
        # Verifica que atributos protegidos não chegam ao LLM
        assert "name" not in result.llm_input
        assert "gender" not in result.llm_input

    def test_score_below_threshold_triggers_human_review(self):
        scorer = WSIScorer()
        result = scorer.evaluate(scores={"technical": 3.0, "behavioral": 4.5, ...})
        assert result.category == "not_recommended"
        assert result.requires_human_review is True
```

**Coverage mínimo:** 80% por módulo (`pytest --cov=app --cov-fail-under=80`)

**Fixtures padrão:**
```python
@pytest.fixture
def mock_company():
    return {"company_id": "test-company-uuid", "name": "Test Corp"}

@pytest.fixture
def mock_candidate():
    return {"id": "cand-uuid", "company_id": "test-company-uuid"}
```

### Frontend (Vitest)

**Localização:** `plataforma-lia/src/__tests__/` ou co-localizado (`*.test.ts`)

**Padrão de arquivo:** `<component>.test.tsx` ou `use-<hook>.test.ts`

```typescript
// src/__tests__/hooks/use-candidate-filter.test.ts
import { renderHook, act } from '@testing-library/react'
import { useCandidateFilter } from '@/hooks/use-candidate-filter'

describe('useCandidateFilter', () => {
  it('initializes with default filters', () => {
    const { result } = renderHook(() => useCandidateFilter('job-123'))
    expect(result.current.filters.status).toBe('all')
  })

  it('updates filter and triggers re-fetch', async () => {
    const { result } = renderHook(() => useCandidateFilter('job-123'))
    act(() => result.current.applyFilter({ status: 'recommended' }))
    expect(result.current.filters.status).toBe('recommended')
  })
})
```

**Regras:**
- Testar lógica do hook, não implementação interna
- Mock de APIs com `vi.mock` ou `msw`
- Sem `any` nos tipos dos testes
- Testar edge cases: empty state, erro, loading

---

## 5. Camada 3 — Integração (FastAPI)

**Localização:** `lia-agent-system/tests/integration/`

```python
# tests/integration/test_candidates_api.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_list_candidates_isolated_by_company(auth_headers_company_a, auth_headers_company_b):
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Company A só vê seus candidatos
        response_a = await client.get("/api/v1/candidates", headers=auth_headers_company_a)
        assert response_a.status_code == 200
        candidates_a = response_a.json()["items"]
        assert all(c["company_id"] == "company-a-uuid" for c in candidates_a)

        # Company B não vê candidatos da Company A
        response_b = await client.get("/api/v1/candidates", headers=auth_headers_company_b)
        candidates_b = response_b.json()["items"]
        company_a_ids = [c["id"] for c in candidates_a]
        assert not any(c["id"] in company_a_ids for c in candidates_b)

@pytest.mark.asyncio
async def test_endpoint_requires_authentication():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/candidates")
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_paginacao_padrao(auth_headers):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/candidates", headers=auth_headers)
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert len(data["items"]) <= 20  # página padrão
```

**Padrões obrigatórios para testes de integração:**
- Testar isolamento por `company_id` em TODOS os endpoints que retornam dados
- Testar autenticação (401 sem token, 403 sem permissão)
- Testar paginação (não carregar tudo)
- Testar schemas Pydantic (422 para input inválido)
- Usar banco de dados de teste (SQLite in-memory ou PostgreSQL de teste)

---

## 6. Camada 4 — E2E (Playwright)

**Localização:** `plataforma-lia/e2e/`

**Fluxos críticos obrigatórios:**
1. Login SSO (WorkOS)
2. Criar vaga → publicar
3. Candidato se inscreve → recebe confirmação
4. Recrutador acessa pipeline → move candidato entre etapas
5. Triagem WSI executada → resultado visível com explicação
6. Recrutador aprova/rejeita → candidato recebe feedback

```typescript
// e2e/pipeline/move-candidate.spec.ts
import { test, expect } from '@playwright/test'

test('recrutador consegue mover candidato de etapa', async ({ page }) => {
  await page.goto('/pipeline/job-123')

  // Verificar que candidato está na etapa inicial
  const candidate = page.locator('[data-testid="candidate-joao-silva"]')
  await expect(candidate).toBeVisible()
  await expect(candidate.locator('[data-testid="stage"]')).toHaveText('Triagem')

  // Mover para próxima etapa
  await candidate.dragTo(page.locator('[data-testid="stage-entrevista"]'))

  // Verificar confirmação
  await expect(page.locator('[data-testid="toast-success"]')).toBeVisible()
  await expect(candidate.locator('[data-testid="stage"]')).toHaveText('Entrevista')
})

test('candidato recebe notificação após movimentação', async ({ page }) => {
  // ... testa fluxo de notificação
})
```

**Regras:**
- Usar `data-testid` em vez de seletores CSS frágeis
- Testar em dark mode e light mode
- Testar navegação por teclado nos fluxos críticos
- Não depender de ordem de execução entre testes
- Screenshot em falha automático (configurado no `playwright.config.ts`)

---

## 7. Camada 5 — Contrato + Fairness

### Contract Tests (Agent-to-Agent)

```python
# tests/contract/test_wizard_to_pipeline_contract.py
import pytest
from app.domains.wizard.agents.agent import WizardAgent
from app.domains.pipeline.agents.agent import PipelineTransitionAgent

def test_wizard_output_matches_pipeline_input_contract():
    """
    Verifica que o output do WizardAgent é compatível
    com o schema esperado pelo PipelineTransitionAgent.
    """
    wizard_output = WizardAgent.output_schema()
    pipeline_input = PipelineTransitionAgent.input_schema()

    # Campos obrigatórios do pipeline devem existir no output do wizard
    for required_field in pipeline_input.required:
        assert required_field in wizard_output.fields, (
            f"Campo '{required_field}' esperado pelo PipelineAgent "
            f"não está no output do WizardAgent"
        )
```

### Fairness/Bias Tests

```python
# tests/fairness/test_wsi_bias.py
import pytest
from app.services.wsi_scorer import WSIScorer
from tests.fixtures.golden_dataset import GOLDEN_DATASET

class TestWSIFairness:
    def test_four_fifths_rule_by_gender(self):
        """
        Regra dos 4/5: taxa de aprovação entre grupos deve ter ratio >= 0.80
        """
        scorer = WSIScorer()
        results_by_gender = {"M": [], "F": [], "NB": []}

        for candidate in GOLDEN_DATASET:
            result = scorer.evaluate(candidate)
            gender = candidate["gender_reference"]  # não enviado ao LLM
            results_by_gender[gender].append(result.approved)

        approval_rates = {
            g: sum(r) / len(r) for g, r in results_by_gender.items()
        }
        max_rate = max(approval_rates.values())

        for gender, rate in approval_rates.items():
            ratio = rate / max_rate
            assert ratio >= 0.80, (
                f"Four-Fifths Rule violada para gênero '{gender}': "
                f"ratio={ratio:.2f} (mínimo: 0.80)"
            )

    def test_protected_attributes_not_in_llm_input(self):
        """
        Nenhum atributo protegido deve chegar ao LLM.
        """
        scorer = WSIScorer()
        protected_attrs = ["name", "gender", "age", "ethnicity", "photo_url",
                          "birth_date", "cpf", "address"]

        for candidate in GOLDEN_DATASET[:20]:
            result = scorer.evaluate(candidate)
            for attr in protected_attrs:
                assert attr not in result.llm_input_log, (
                    f"Atributo protegido '{attr}' encontrado no input do LLM"
                )
```

**Golden Dataset:** Mínimo 200 candidatos fictícios com distribuição balanceada entre grupos demográficos. Localização: `tests/fixtures/golden_dataset.py`

---

## 8. Cobertura Mínima e Gates de CI

```yaml
# .github/workflows/tests.yml (referência)
jobs:
  test:
    steps:
      - name: Backend Unit Tests
        run: pytest tests/unit/ --cov=app --cov-fail-under=80

      - name: Backend Integration Tests
        run: pytest tests/integration/ -v

      - name: Frontend Unit Tests
        run: cd plataforma-lia && npx vitest run --coverage

      - name: Fairness Tests
        run: pytest tests/fairness/ -v

      - name: E2E Tests (staging only)
        run: cd plataforma-lia && npx playwright test
        if: github.ref == 'refs/heads/main'
```

**Gates obrigatórios (bloqueiam merge/deploy):**
- Coverage < 80% em qualquer módulo de negócio
- Qualquer teste de fairness falhando (Four-Fifths Rule)
- Atributo protegido detectado no input do LLM
- Qualquer teste E2E de fluxo crítico falhando
- Latência P95 acima do threshold (> 5s)

---

## 9. Geração de Testes com IA

Prompt para gerar testes a partir de um endpoint ou componente existente:

```
Gere testes para [endpoint/componente] seguindo os padrões da Plataforma LIA:

1. Testes unitários com pytest/Vitest
2. Testes de integração cobrindo:
   - Isolamento por company_id
   - Autenticação (401/403)
   - Paginação
   - Schemas Pydantic (422 para input inválido)
3. Edge cases: empty state, erro de rede, timeout, multi-tenant
4. Um teste de fairness se o componente toma decisões sobre candidatos

Referência de padrões: .agents/skills/testing-patterns/SKILL.md
```

---

## 10. Checklist de Cobertura por Feature

- [ ] Camada 1 (Produto): fluxo testado manualmente + Jam.dev configurado para capturar bugs
- [ ] Camada 2 (Unitário): toda lógica de negócio com coverage >= 80%
- [ ] Camada 3 (Integração): todos os endpoints novos com testes de isolamento por company_id
- [ ] Camada 4 (E2E): fluxo completo do usuário coberto (se for feature crítica)
- [ ] Camada 5 (Contrato): contract tests se a feature cria ou modifica agentes IA
- [ ] Camada 5 (Fairness): bias tests se a feature toma decisões sobre candidatos
- [ ] CI verde em todas as camadas antes de merge

---

## Uso em Outros Ambientes

| Ambiente | Como Usar |
|----------|-----------|
| **Claude Code / Replit Agent** | Digite `/testing-patterns` no chat para ativar a skill completa |
| **Cursor IDE** | Mencione `@.cursor/rules/testing-patterns.mdc` no contexto ou ative a regra para o projeto |
| **GitHub / Outros** | Referencie diretamente: `.agents/skills/testing-patterns/SKILL.md` |

**Quando ativar:**
- Ao criar qualquer endpoint, componente ou agente novo
- Ao investigar um bug reportado via Jam.dev
- Ao verificar cobertura antes de `/feature-audit`
- Ao configurar ou atualizar o pipeline de CI/CD
