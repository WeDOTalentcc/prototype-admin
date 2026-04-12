# T1 Fase 2 — Implementacao Apify Integration

**Data**: 2026-04-12
**Objetivo**: Registro de implementacao dos 6 passos

---

## PASSO 1: Atualizar Actor e Configs

**Arquivo**: `apify_service.py` + `config.py`

### Mudancas

1. `LINKEDIN_PERSON_ACTOR_ID` = `"dev_fusion/Linkedin-Profile-Scraper"` (ja era)
2. Adicionado `LINKEDIN_LEGACY_ACTOR_ID` = `"anchor/linkedin-person-scraper"` como fallback
3. Adicionadas env vars no `config.py`:
   - `APIFY_COST_PER_ENRICHMENT_USD` = 0.01
   - `APIFY_ENRICHMENT_TIMEOUT_SECONDS` = 30
   - `APIFY_MAX_CONCURRENT_ENRICHMENTS` = 5
   - `APIFY_LEGACY_ACTOR` = "anchor/linkedin-person-scraper"
4. Adicionadas constantes no `apify_service.py`:
   - `APIFY_COST_PER_ENRICHMENT_USD`
   - `APIFY_ENRICHMENT_TIMEOUT`
   - `APIFY_MAX_CONCURRENT`

### Validacao

```bash
python -c "from app.domains.sourcing.services.apify_service import LINKEDIN_LEGACY_ACTOR_ID, APIFY_COST_PER_ENRICHMENT_USD; print('OK')"
# OK Cost=0.01
```

---

## PASSO 2: Criar Mapper Completo

**Arquivo criado**: `app/domains/sourcing/services/apify_mapper.py`

### Classe: `ApifyProfileMapper`

| Metodo | Input | Output |
|--------|-------|--------|
| `map_to_candidate(apify_data)` | dict Apify | dict campos Candidate |
| `map_to_experiences(apify_data)` | dict Apify | list[dict] CandidateExperience |
| `map_to_educations(apify_data)` | dict Apify | list[dict] CandidateEducation |
| `map_to_skills(apify_data)` | dict Apify | list[str] skills |

### Regras implementadas

- Todos os campos sao opcionais (dados parciais nao crasham)
- `source="apify"` e `enrichment_source="apify"` setados
- `years_of_experience`: calculado da experiencia mais antiga ate hoje
- `location_city/state/country`: parsing por virgula
- `email`: primeiro email encontrado, resto em `personal_emails`
- `seniority_level`: inferido por keywords (c_level, vp, director, manager, senior, mid, junior)
- Valores None filtrados do output

### Helpers privados

| Helper | Funcao |
|--------|--------|
| `_extract_emails` | Extrai emails de multiplas keys (email, emailAddress, emails[], etc) |
| `_extract_phones` | Extrai telefones de multiplas keys |
| `_parse_location` | Split por virgula -> city, state, country |
| `_get_current_experience` | Encontra experiencia sem endDate |
| `_calculate_years_of_experience` | Ano mais antigo ate hoje |
| `_infer_seniority` | Keywords lookup no titulo |

### Validacao

```bash
python -c "from app.domains.sourcing.services.apify_mapper import ApifyProfileMapper; print('OK')"
# ApifyProfileMapper OK
```

---

## PASSO 3: Registrar APIFY_CIRCUIT

**Arquivo**: `app/shared/resilience/circuit_breaker.py`

### Registro (ja existia)

```python
APIFY_CIRCUIT = CircuitBreaker(
    "apify",
    CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=60.0,
        success_threshold=2,
        timeout=120.0,
    )
)
```

### Validacao

```bash
python -c "from app.shared.resilience.circuit_breaker import APIFY_CIRCUIT; print(f'state={APIFY_CIRCUIT.state}')"
# APIFY_CIRCUIT state=closed
```

---

## PASSO 4: Criar Contact Enrichment Service

**Arquivo**: `app/domains/sourcing/services/contact_enrichment_service.py`

### Classe: `ContactEnrichmentService`

| Metodo | Descricao |
|--------|-----------|
| `enrich_candidate_contact(db, candidate_id, linkedin_url, force)` | Enriquecimento individual |
| `enrich_batch(db, candidates, force)` | Batch com semaforo |
| `enrich_search_results_and_filter(db, candidates)` | Enriquece + filtra sem contato |

### Fluxo `enrich_candidate_contact`

1. Busca candidato no DB
2. Se ja tem contato e !force -> retorna existing
3. Se sem LinkedIn URL -> retorna erro
4. Se recentemente enriquecido (24h) -> retorna dedup_skip
5. Verifica APIFY_CIRCUIT.is_open -> retorna erro se aberto
6. Chama CandidateEnrichmentService.enrich_candidate
7. APIFY_CIRCUIT.record_success() ou record_failure()
8. Retorna resultado com custo e tempo

### Rate limiting

- `asyncio.Semaphore(BATCH_CONCURRENCY)` = 5 (via APIFY_MAX_CONCURRENT)
- Cada chamada no batch adquire semaforo
- `asyncio.gather` com `return_exceptions=True`

### Dedup cache

- Verifica `additional_data.enrichment.last_enriched_at`
- Window: 24 horas (`DEDUP_WINDOW_HOURS`)
- Se enriquecido recentemente sem resultado -> skip

### Resultado

```python
{
    "success": bool,
    "has_contact": bool,
    "email": str | None,
    "phone": str | None,
    "fields_updated": list[str],
    "source": str,  # "existing", "apify", "dedup_skip", "apify_error"
    "cost_usd": float,  # 0.01
    "elapsed_seconds": float,
}
```

### Validacao

```bash
python -c "from app.domains.sourcing.services.contact_enrichment_service import ContactEnrichmentService; print('OK')"
# ContactEnrichmentService OK
```

---

## PASSO 5: Rails Adapter Mapping

**Arquivo**: `rails_adapter.py`

**Status**: Sem gaps. Todos os campos que o Apify preenche ja estao no mapping CANDIDATE_FORK_TO_RAILS:

- email, secondary_email -> email, secondary_email
- phone, mobile_phone -> phone, mobile_phone
- current_title -> role_name
- current_company -> current_company
- location_city/state/country -> city/state/country
- technical_skills -> technical_skills
- years_of_experience -> years_of_experience
- seniority_level -> seniority_level

Nenhuma mudanca necessaria.

---

## PASSO 6: Health Check Endpoint

**Arquivo**: `app/api/v1/integrations_hub.py`

### Endpoint

`GET /api/v1/integrations/apify/health`

### Response

```json
{
    "status": "ok|degraded|down",
    "circuit_breaker": "closed|open|half_open",
    "actor": "dev_fusion/Linkedin-Profile-Scraper",
    "last_successful_call": "2026-04-12T...",
    "avg_response_time_ms": null,
    "cost_per_enrichment_usd": 0.01
}
```

### Logica de status

- `ok`: circuit fechado E ultima chamada < 5 min
- `degraded`: circuit half-open OU ultima chamada > 5 min
- `down`: circuit aberto
