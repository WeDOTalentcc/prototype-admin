# Plano de Correções — Plataforma LIA
**Baseado em:** QA_REPORT_FINAL.md | 03/04/2026

---

## 🔴 CORREÇÃO 1 (P1 — Bloqueante): WSI Event Loop Bloqueado

### Problema
`client.messages.create()` é chamada **síncrona** dentro de um endpoint **async** FastAPI.
Com timeout padrão do Anthropic SDK de 600s, uma única requisição WSI pode travar todo o servidor.

### Arquivo
`/home/runner/workspace/lia-agent-system/app/api/v1/wsi.py` — função `analyze_response` (~linha 970)

### Código Atual (problemático)
```python
try:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    data = parse_json_response(response.content[0].text, {})
except Exception as e:
    logger.error(f"AI analysis failed: {e}")
    data = {}
```

### Código Corrigido
```python
import asyncio

async def _call_claude_sync(client, model, max_tokens, messages):
    """Wraps synchronous Anthropic call in thread pool to avoid blocking event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=messages
        )
    )

# No handler analyze_response, substituir o bloco try:
try:
    response = await asyncio.wait_for(
        _call_claude_sync(
            client,
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        ),
        timeout=30.0  # 30s hard limit — evita travar o servidor
    )
    data = parse_json_response(response.content[0].text, {})
except asyncio.TimeoutError:
    logger.warning("WSI AI analysis timed out (30s), using deterministic fallback")
    data = {}
except Exception as e:
    logger.error(f"AI analysis failed: {e}")
    data = {}
```

### Teste de Verificação
```bash
# Verificar que o endpoint responde em < 35s mesmo com LLM lento
time curl -X POST http://localhost:8000/api/v1/wsi/analyze-response \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test","question_id":"q1","candidate_id":"c1","job_vacancy_id":"j1",
       "question_text":"Descreva um projeto","response_text":"Liderou migração","competency":"lideranca","framework":"STAR"}'
# Esperado: resposta em < 35s (não mais 120s+)
```

---

## 🟡 CORREÇÃO 2 (P2): Chat Vaza Campo `thought` em Inglês

### Problema
Resposta do endpoint de chat inclui campo interno `"thought"` com raciocínio em inglês exposto ao frontend.

### Arquivo
`/home/runner/workspace/lia-agent-system/app/api/v1/lia_assistant.py` — resposta do endpoint chat

### Diagnóstico
```bash
# Reproduzir o bug:
curl -X POST http://localhost:5000/api/backend-proxy/chat/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Qual o status do pipeline da vaga de Engenheiro?"}'
# Observar: resposta contém "thought": "The pipeline health data returned 0 candidates..."
```

### Código Corrigido
Localizar onde a resposta é construída e filtrar o campo `thought` antes de retornar:

```python
# Procurar por algo como:
response_data = {
    "thought": thought_text,   # ← REMOVER esta linha
    "action": action,
    "lia_response": lia_response,
    ...
}

# Corrigir para:
response_data = {
    "action": action,
    "lia_response": lia_response,
    # thought NÃO exposto — manter apenas em logs internos
    ...
}
```

```bash
# Localizar no código:
grep -n "thought" /home/runner/workspace/lia-agent-system/app/api/v1/lia_assistant.py | head -20
```

### Teste de Verificação
```bash
# Confirmar que "thought" não aparece mais na resposta:
curl -s -X POST http://localhost:5000/api/backend-proxy/chat/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"Análise do pipeline"}' | python3 -c "import json,sys; d=json.load(sys.stdin); print('PASS' if 'thought' not in d else 'FAIL: thought presente')"
```

---

## 🟡 CORREÇÃO 3 (P2): LLM Fallback Silencioso no Intent Classifier

### Problema
`enhanced_intent_classifier.py` cai para regex quando o LLM falha, sem alertar a UI ou log suficiente.
Isso causa classificação de intenções de menor qualidade silenciosamente.

### Arquivo
`/home/runner/workspace/lia-agent-system/app/services/enhanced_intent_classifier.py` — linha 460-476

### Código Atual
```python
except Exception as e:
    logger.warning(f"LLM classification failed, using regex fallback: {e}")
    reasoning="Fallback para extração por regex"
    # ... continua com regex
```

### Código Corrigido
```python
except Exception as e:
    logger.error(f"LLM classification failed: {type(e).__name__}: {e}")
    # Incrementar métrica para monitoramento
    # metrics.increment("intent_classifier.llm_fallback")

    # Adicionar header de degradação na resposta (opcional)
    reasoning = "Fallback regex (LLM indisponível)"

    # Tentar reconexão com Gemini como alternativa
    try:
        result = await self._classify_with_gemini(prompt)
        if result:
            return result
    except Exception as gemini_err:
        logger.error(f"Gemini fallback also failed: {gemini_err}")

    # Só usar regex como último recurso
    # ... regex logic
```

### Diagnóstico Rápido
```bash
# Verificar se o modelfarm está respondendo para o intent classifier:
curl -s --max-time 5 http://localhost:1106/modelfarm/anthropic/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: _DUMMY_API_KEY_" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model":"claude-sonnet-4-6","max_tokens":10,"messages":[{"role":"user","content":"OK"}]}'
# Esperado: resposta JSON com "OK"
```

---

## 🔵 CORREÇÃO 4 (P3): WSI — Escala de Score e Campo `star_completeness`

### Problema
- API retorna score em escala 0-5 mas sem documentar; UIs e benchmarks assumem 0-10
- Campo `star_completeness` esperado pela UI não é calculado

### Arquivo
`/home/runner/workspace/lia-agent-system/app/api/v1/wsi.py` — `AnalyzeResponseOutput` model e handler

### Código Corrigido
```python
# 1. No modelo de resposta, adicionar score_max e star_completeness:
class AnalyzeResponseOutput(BaseModel):
    question_id: str
    bloom_score: int
    bloom_level_name: str
    dreyfus_level: int
    dreyfus_level_name: str
    big_five_indicators: BigFiveIndicators
    score: float           # 0.0 a 5.0
    score_max: float = 5.0 # ← NOVO: documentar escala
    score_normalized: float = 0.0  # ← NOVO: score/5 * 10 para compatibilidade
    feedback: str
    evidences: List[str]
    red_flags: List[str]
    star_completeness: Optional[float] = None  # ← NOVO: 0.0 a 1.0

# 2. No handler, calcular star_completeness a partir do prompt/resposta:
star_elements = ["situação", "situation", "tarefa", "task", "ação", "action", "resultado", "result"]
response_lower = request.response_text.lower()
found = sum(1 for el in star_elements if el in response_lower) / 4  # normalizado 0-1
star_completeness = min(1.0, found)

return AnalyzeResponseOutput(
    ...
    score=data.get("score", 3.0),
    score_max=5.0,
    score_normalized=round(data.get("score", 3.0) / 5.0 * 10, 1),
    star_completeness=star_completeness,
    ...
)
```

---

## 🔵 CORREÇÃO 5 (P3): CV Match — Campos Estruturados Ausentes

### Problema
CV Match retorna resposta em texto livre sem `match_score` numérico nem `matched_skills` estruturados.

### Arquivo
Endpoint CV match (via orchestrator `POST /api/backend-proxy/orchestrator/process/`)

### Diagnóstico
```bash
# Ver estrutura atual da resposta:
curl -s -X POST http://localhost:5000/api/backend-proxy/orchestrator/process/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Faça match do CV de João com a vaga de Engenheiro Python"}' | python3 -m json.tool
```

### Correção no Prompt do Agente CV Match
Adicionar instrução no system prompt do agente para sempre retornar JSON estruturado:
```
Sempre inclua no final da sua análise um bloco JSON estruturado:
```json
{
  "match_score": 85,
  "matched_skills": ["Python", "FastAPI", "PostgreSQL"],
  "missing_skills": ["Kubernetes"],
  "recommendation": "APROVADO"
}
```
```

---

## 🔵 CORREÇÃO 6 (P3): Salary Benchmark — Valores BRL Ausentes

### Problema
Resposta do agente Salary não contém valores monetários parseáveis (ex: `R$ 12.000`).

### Correção no Prompt do Agente Salary
```
Sempre inclua faixas salariais no formato: R$ XX.XXX - R$ XX.XXX mensais (CLT).
Estruture a resposta com:
- Faixa mínima: R$ X.XXX
- Faixa máxima: R$ X.XXX
- Mediana: R$ X.XXX
```

---

## 📋 Ordem de Execução Sugerida

```
Semana 1 (sprint atual):
  [ ] CORREÇÃO 1 — WSI event loop (P1) — ~2h de desenvolvimento
  [ ] CORREÇÃO 2 — thought leak (P2) — ~30min
  [ ] Rodar benchmark_agents.py para verificar WSI corrigido

Semana 2:
  [ ] CORREÇÃO 3 — intent classifier fallback (P2) — ~1h
  [ ] CORREÇÃO 4 — WSI escala/star_completeness (P3) — ~2h
  [ ] CORREÇÃO 5 — CV match campos estruturados (P3) — ~1h
  [ ] CORREÇÃO 6 — Salary valores BRL (P3) — ~30min

Verificação Final:
  [ ] Rodar run_all_benchmarks.sh
  [ ] Score médio esperado após correções: ≥ 85/100
```

---

## 🔁 Como Re-executar os Benchmarks após Correções

```bash
# No Replit (SSH):
cd /home/runner/workspace/docs/specs/qa

# Token
export LIA_TOKEN=$(curl -sL -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@wedotalent.com","password":"demo123"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Benchmark completo
python3 benchmark_prompts.py --base-url http://localhost:5000 --token "$LIA_TOKEN"
python3 benchmark_agents.py  --base-url http://localhost:5000 --token "$LIA_TOKEN" --timeout 60
python3 test_agent_fairness.py --base-url http://localhost:5000 --token "$LIA_TOKEN" --timeout 90

# Score esperado após correções: prompts ≥ 85/100 | agentes ≥ 80/100
```

---

*Plano gerado em 03/04/2026 — Plataforma LIA QA Suite v1.0*
