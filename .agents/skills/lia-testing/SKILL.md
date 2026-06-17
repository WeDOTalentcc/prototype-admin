---
name: lia-testing
description: "Estrategia de testes unificada para Plataforma LIA — TDD (Red/Green/Refactor), piramide 5 camadas, e evals para agentes IA. Use ao implementar features, refatorar codigo, criar agentes IA, escrever testes ou verificar cobertura. Cobre React/Next.js (Vitest), Python/FastAPI (pytest), agentes LangGraph, golden datasets e LLM-as-judge."
---

# LIA Testing — Estrategia Unificada de Testes

Combina TDD workflow, piramide de 5 camadas e evals para agentes IA num unico ponto de referencia.

## Quando ativar

- Ao implementar feature nova — escrever teste ANTES (TDD Red/Green/Refactor)
- Ao corrigir bug — escrever teste que reproduz o bug, depois corrigir
- Ao refatorar codigo — rede de testes garante zero regressao antes de mexer
- Quando o usuario disser "escreve teste", "cobre com teste", "TDD nisso", "valida com teste" ou "garante que nao quebra"
- Ao criar agente IA (LangGraph) — escrever golden dataset e LLM-as-judge antes do prompt final
- Ao revisar cobertura de teste em codigo existente (auditoria de cobertura)
- Antes de marcar feature complexa como pronta (rodar piramide de 5 camadas)
- Ao introduzir nova integracao externa (API, banco, fila) — testes de contrato e mock

## Quando NAO ativar

- Mudanca de copy/texto sem logica
- Mockup ou prototipo no sandbox sem intencao de producao
- Configuracao de ambiente (dotfiles, env vars) sem mudanca de codigo
- Quando o usuario pediu fix urgente com prazo apertado e prometeu teste em task separada
- Script descartavel de uso unico (migracao manual, exploracao)

---

## PARTE 1: TDD — Red / Green / Refactor

### Principio

Sem instrucao explicita, o agente escreve implementacao primeiro, depois testes. TDD requer o inverso: **testes dirigem o design**.

```
Red -> Green -> Refactor -> Validate
```

### Para codigo deterministico

```
RED   -> Escreva o teste. Rode. Confirme que FALHA pela razao certa.
GREEN -> Codigo minimo para passar. Nada alem.
REFACTOR -> Clareza e simplicidade. Rode novamente.
COMMIT -> So apos refactor + testes verdes.
```

### Para codigo probabilistico (saidas LLM)

```
EVAL-FIRST -> Defina criterios de avaliacao ANTES de escrever o prompt.
GOLDEN     -> Crie/atualize golden dataset com casos representativos.
IMPLEMENT  -> Escreva o prompt ou no.
JUDGE      -> Rode LLM-as-judge sobre os casos do golden dataset.
THRESHOLD  -> Score minimo aceitavel (>= 0.85).
COMMIT     -> So apos score >= threshold.
```

### Quick Reference

```
NEW FEATURE:     Red -> Green -> Refactor -> Validate
BUG FIX:         Teste que reproduz bug -> Fix -> Verify green
REFACTOR:        Testes de caracterizacao -> Refactor -> Verify green
HOOK EXTRACTION: Teste interface -> Extract -> Simplify -> Validate dims 5,6
UI EXTRACTION:   Teste componente -> Extract -> Apply tokens -> Validate dims 1-5
```

---

## PARTE 2: Piramide de Testes — 5 Camadas

```
+---------------------------------+
|  CAMADA 5: Contrato + Fairness  |  <- agent-to-agent, bias tests
+---------------------------------+
|  CAMADA 4: E2E                  |  <- Playwright (fluxos criticos)
+---------------------------------+
|  CAMADA 3: Integracao           |  <- FastAPI endpoints com mocks
+---------------------------------+
|  CAMADA 2: Unitario             |  <- pytest (BE) / Vitest (FE)
+---------------------------------+
|  CAMADA 1: Produto              |  <- Jam.dev (captura visual)
+---------------------------------+
```

### Stack de Testes

| Camada | Frontend | Backend |
|--------|----------|---------|
| Unitario | Vitest + @testing-library/react | pytest + unittest.mock |
| Integracao | Vitest + msw | pytest + httpx (TestClient) |
| E2E | Playwright | pytest + httpx (full server) |
| Contrato | - | pytest (agent-to-agent schemas) |
| Fairness | - | pytest (Four-Fifths Rule, bias) |

### Camada 2 — Unitario

**Frontend (Vitest):**

```typescript
// src/hooks/__tests__/useJobFilters.test.ts
import { renderHook, act } from '@testing-library/react'
import { useJobFilters } from '../useJobFilters'

describe('useJobFilters', () => {
  it('should initialize with default filters', () => {
    const { result } = renderHook(() => useJobFilters())
    expect(result.current.status).toBe('all')
  })

  it('should update status filter', () => {
    const { result } = renderHook(() => useJobFilters())
    act(() => { result.current.setStatus('active') })
    expect(result.current.status).toBe('active')
  })
})
```

**Backend (pytest):**

```python
# tests/unit/test_wsi_scorer.py
class TestWSIScorer:
    def test_score_above_threshold_returns_recommended(self):
        scorer = WSIScorer()
        result = scorer.evaluate(scores={"technical": 8.0, "behavioral": 7.5})
        assert result.category == "recommended"

    def test_protected_attributes_masked_before_evaluation(self):
        scorer = WSIScorer()
        input_data = {"name": "Joao", "gender": "M", "technical": 7.0}
        result = scorer.evaluate(input_data)
        assert "name" not in result.llm_input
        assert "gender" not in result.llm_input
```

### Camada 3 — Integracao (FastAPI)

```python
@pytest.mark.asyncio
async def test_list_candidates_isolated_by_company(auth_headers_a, auth_headers_b):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response_a = await client.get("/api/v1/candidates", headers=auth_headers_a)
        candidates_a = response_a.json()["items"]
        assert all(c["company_id"] == "company-a" for c in candidates_a)

        response_b = await client.get("/api/v1/candidates", headers=auth_headers_b)
        candidates_b = response_b.json()["items"]
        company_a_ids = [c["id"] for c in candidates_a]
        assert not any(c["id"] in company_a_ids for c in candidates_b)
```

**Padroes obrigatorios:**
- Testar isolamento por `company_id` em TODOS os endpoints
- Testar autenticacao (401 sem token, 403 sem permissao)
- Testar paginacao
- Testar schemas Pydantic (422 para input invalido)

### Camada 4 — E2E (Playwright)

**Fluxos criticos obrigatorios:**
1. Login SSO (WorkOS)
2. Criar vaga -> publicar
3. Candidato se inscreve -> confirmacao
4. Pipeline -> mover candidato entre etapas
5. Triagem WSI -> resultado visivel
6. Aprovar/rejeitar -> feedback ao candidato

**Regras:** `data-testid` (nao seletores CSS), testar dark/light mode, navegacao por teclado.

### Camada 5 — Contrato + Fairness

**Contract tests (agent-to-agent):**
```python
def test_wizard_output_matches_pipeline_input_contract():
    wizard_output = WizardAgent.output_schema()
    pipeline_input = PipelineTransitionAgent.input_schema()
    for field in pipeline_input.required:
        assert field in wizard_output.fields
```

**Fairness/bias tests (Four-Fifths Rule):**
```python
def test_four_fifths_rule_by_gender(self):
    approval_rates = {g: sum(r)/len(r) for g, r in results_by_gender.items()}
    max_rate = max(approval_rates.values())
    for gender, rate in approval_rates.items():
        ratio = rate / max_rate
        assert ratio >= 0.80, f"Four-Fifths Rule violada: {gender} ratio={ratio:.2f}"
```

---

## PARTE 3: Evals para Agentes IA

### Golden Dataset

Arquivo JSON com input + output esperado + criterios. Versionado no repo.

**Estrutura:** `tests/golden/nome_do_agente.json`

```json
{
  "dataset": "wsi_scoring_v1",
  "cases": [
    {
      "id": "wsi_001",
      "description": "Candidato senior com resposta completa",
      "input": {"question": "...", "answer": "..."},
      "expected": {"score_min": 7.5, "feedback_should_not_contain": ["fraco"]}
    },
    {
      "id": "wsi_002",
      "description": "Sem resposta — nao deve gerar feedback positivo",
      "input": {"question": "...", "answer": ""},
      "expected": {"score_max": 1.0, "feedback_should_not_contain": ["excelente"]}
    }
  ]
}
```

### LLM-as-Judge

```python
import anthropic, json, os

client = anthropic.Anthropic(
    api_key=os.environ["AI_INTEGRATIONS_ANTHROPIC_API_KEY"],
    base_url=os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL", "https://api.anthropic.com")
)

JUDGE_PROMPT = """Avalie a resposta do agente IA.
Criterios: {criteria}
Resposta: {response}
Retorne JSON: {{"score": 0.0-1.0, "passed": true/false, "reason": "..."}}"""

def run_eval(case, agent_response):
    msg = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=512,
        messages=[{"role": "user", "content": JUDGE_PROMPT.format(
            criteria=json.dumps(case["expected"]), response=agent_response
        )}]
    )
    return json.loads(msg.content[0].text)
```

### Teste de No LangGraph

```python
class TestAnalyzeIntent:
    def test_retorna_action_id_correto(self):
        state = {"question": "liste vagas", "domain_id": "jobs"}
        with patch("src.domains.jobs.nodes.create_tracked_llm") as mock_llm:
            mock_resp = MagicMock()
            mock_resp.action_id = "list_jobs"
            mock_resp.confidence = 0.92
            mock_llm.return_value.with_structured_output.return_value.invoke.return_value = mock_resp
            result = analyze_intent(state)
        assert result["action_id"] == "list_jobs"
        assert result["confidence"] >= 0.5

class TestRouting:
    def test_alta_confianca_vai_para_execute(self):
        state = {"confidence": 0.85, "action_id": "list_jobs", "retry_count": 0}
        assert route_after_intent(state) == "execute"

    def test_max_retries_vai_para_fallback(self):
        state = {"confidence": 0.2, "action_id": "", "retry_count": 3}
        assert route_after_intent(state) == "fallback"
```

---

## PARTE 4: Anti-Patterns

| Anti-Pattern | Correto |
|-------------|---------|
| Chamar API LLM real no teste | Mockar com unittest.mock |
| Testar apenas happy path | Sempre testar input vazio, extremos, erros |
| "Write tests for this feature" | "Write FAILING tests. Do NOT implement yet." |
| Pular RED porque "sabe que vai passar" | Sempre ver o teste falhar primeiro |
| Arquivo de teste > 300 linhas | Quebrar por feature/dominio |
| Score hardcoded como expected | Usar intervalos: `assert 6.0 <= score <= 9.0` |

---

## PARTE 5: Cobertura e Thresholds

| Tipo | Coverage minimo |
|------|----------------|
| Nos de agente (routing, scoring) | 100% branches |
| Prompts / evals | 85% golden dataset |
| Endpoints FastAPI | 80% status codes |
| Componentes UI | 70% comportamentos criticos |
| Modulos de negocio | 80% (pytest --cov-fail-under=80) |

### Checklist por Tipo de Mudanca

**Agentes IA:**
- [ ] Nos novos com teste unitario (mock LLM)
- [ ] Routing functions com 3+ cenarios
- [ ] Nenhum LLM instanciado direto (usar factory)
- [ ] Caso de teste para score zero e maximo
- [ ] Golden dataset atualizado

**Endpoints FastAPI:**
- [ ] Teste integracao happy path
- [ ] Payload invalido retorna 422
- [ ] Recurso inexistente retorna 404
- [ ] Isolamento por company_id

**Componentes React:**
- [ ] Hook/componente com __tests__/
- [ ] Loading, erro e empty state testados
- [ ] Dados mockados (nunca APIs reais)

**Prompts:**
- [ ] Criterios definidos ANTES de escrever
- [ ] Golden dataset com 3+ casos (feliz, triste, edge)
- [ ] LLM-as-judge score >= 85%

---

## PARTE 6: Comandos

```bash
# Frontend
cd plataforma-lia && npx vitest run
cd plataforma-lia && npx vitest run src/hooks/__tests__/
cd plataforma-lia && npx playwright test

# Backend
cd lia-agent-system && python -m pytest app/tests/ -v
cd lia-agent-system && python -m pytest app/tests/ --cov=app --cov-fail-under=80

# Evals
python tests/eval_runner.py tests/golden/wsi_scoring_v1.json

# E2E via Replit
runTest({ testPlan: "..." })  # via code_execution
```

## Bugs Historicos — Regressoes Obrigatorias

| Bug | Teste |
|-----|-------|
| LIA usava girias ("cool", "legal") em entrevistas | `test_lia_nao_usa_girias_em_entrevista` |
| Feedback "excellent" para score < 3 | `test_candidato_regular_nao_recebe_feedback_otimista` |
| Modal WSI nao abria | `test_modal_abre_para_candidato_com_score_valido` |
