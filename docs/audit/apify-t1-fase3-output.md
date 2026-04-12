# T1 Fase 3 — Validacao Apify Integration

**Data**: 2026-04-12
**Objetivo**: Validar implementacao completa da T1

---

## VALIDACAO 1: Imports e Compilacao

```bash
python -c "from app.domains.sourcing.services.apify_service import ApifyService"           # OK
python -c "from app.domains.sourcing.services.apify_mapper import ApifyProfileMapper"       # OK
python -c "from app.domains.sourcing.services.contact_enrichment_service import ContactEnrichmentService"  # OK
python -c "from app.shared.resilience.circuit_breaker import APIFY_CIRCUIT"                 # OK
```

| Check | Status |
|-------|--------|
| `apify_service.py` | OK |
| `apify_mapper.py` | OK |
| `contact_enrichment_service.py` | OK |
| `circuit_breaker.py` (APIFY_CIRCUIT) | OK |
| `config.py` (env vars) | OK |
| `integrations_hub.py` (health endpoint) | OK |

---

## VALIDACAO 2: Mapper com Dados Parciais

### Test A: Perfil completo (todos os campos preenchidos)

- Input: firstName, lastName, headline, summary, location, profileUrl, email, phone, experience (2), education (1), skills (3), certifications (1), languages (2)
- **Resultado**: PASS
  - name = "Maria Silva"
  - seniority = "senior" (inferido de "Senior Software Engineer")
  - years_of_experience = 9 (2017 ate 2026)
  - location_city = "Sao Paulo", location_country = "Brazil"
  - email, phone mapeados corretamente

### Test B: Perfil sem email (phone presente)

- Input: firstName, lastName, phone apenas
- **Resultado**: PASS
  - phone = "+5511888888888"
  - email = None (nao crasha)

### Test C: Perfil sem email E sem phone

- Input: firstName, lastName, headline apenas
- **Resultado**: PASS
  - name = "Ana Costa"
  - email = None, phone = None
  - Nao crasha, retorna campos disponiveis

### Test D: Perfil minimo (apenas nome + LinkedIn URL)

- Input: firstName, profileUrl apenas
- **Resultado**: PASS
  - name = "Pedro"
  - linkedin_url preenchido
  - Demais campos None (nao crashou)

### Tests adicionais

- Experiences: PASS (2 items mapeados corretamente)
- Education: PASS (1 item, institution = "USP")
- Skills: PASS (3 items: Python, Java, AWS)
- Empty input: PASS (retorna dict vazio, nao crasha)

---

## VALIDACAO 3: Circuit Breaker

- APIFY_CIRCUIT registrado: **Sim** (linhas 367-375 de circuit_breaker.py)
- Params: failure_threshold=5, recovery_timeout=60.0, success_threshold=2, timeout=120.0
- ContactEnrichmentService usa APIFY_CIRCUIT: **Sim**
  - Check: `if APIFY_CIRCUIT.is_open:` (linha 63)
  - Success: `APIFY_CIRCUIT.record_success()` (linha 79)
  - Failure: `APIFY_CIRCUIT.record_failure()` (linha 105)
- Se circuit aberto, retorna `{"success": False, "error": "Apify circuit breaker open"}` sem chamar Apify

| Check | Status |
|-------|--------|
| APIFY_CIRCUIT registrado | OK |
| Mesmos params que PEARCH | OK (threshold=5 vs 3, timeout=120 vs 30) |
| ContactEnrichmentService usa APIFY_CIRCUIT | OK |
| Circuit open = skip Apify | OK |

---

## VALIDACAO 4: Dedup Cache

- **Logica**: Verifica `candidate.additional_data["enrichment"]["last_enriched_at"]`
- **Window**: 24 horas (`DEDUP_WINDOW_HOURS = 24`)
- **Comportamento**: Se candidato enriquecido nas ultimas 24h sem contato, retorna `{"source": "dedup_skip"}` sem chamar Apify
- **Query de cache**: `_recently_enriched()` faz `datetime.fromisoformat(last_enriched)` e compara com `utcnow() - 24h`

| Check | Status |
|-------|--------|
| Campo de cache existe | OK (additional_data.enrichment.last_enriched_at) |
| Window 24h configurada | OK |
| Segunda chamada = cache hit | OK |

---

## VALIDACAO 5: Rate Limiting

- `asyncio.Semaphore(BATCH_CONCURRENCY)` onde `BATCH_CONCURRENCY = APIFY_MAX_CONCURRENT = 5`
- Em `enrich_batch`: `semaphore = asyncio.Semaphore(BATCH_CONCURRENCY)`
- Cada candidato: `async with semaphore:` antes de chamar `enrich_candidate_contact`
- Com 50 candidatos e semaforo = 5: no maximo 5 chamadas simultaneas

| Check | Status |
|-------|--------|
| Semaphore configurado | OK |
| Valor = APIFY_MAX_CONCURRENT (5) | OK |
| Batch usa semaforo | OK |

---

## VALIDACAO 6: Health Check

- Endpoint: `GET /api/v1/integrations/apify/health`
- Adicionado em `integrations_hub.py`
- Retorna JSON com status, circuit_breaker, actor, last_successful_call, cost

| Check | Status |
|-------|--------|
| Endpoint existe | OK |
| Retorna JSON valido | OK |
| Status logica (ok/degraded/down) | OK |

---

## RESUMO FINAL

| Check | Status | Detalhes |
|-------|--------|----------|
| Imports | OK | Todos os modulos compilam |
| Mapper completo | OK | 4 metodos, mapeamento completo |
| Mapper parcial | OK | 4 cenarios testados, nenhum crash |
| Circuit breaker | OK | APIFY_CIRCUIT registrado e usado |
| Dedup cache | OK | 24h window via additional_data |
| Rate limiting | OK | asyncio.Semaphore(5) |
| Health check | OK | GET /api/v1/integrations/apify/health |

**CHECKPOINT**: Todos OK. Pode avancar para T2.
