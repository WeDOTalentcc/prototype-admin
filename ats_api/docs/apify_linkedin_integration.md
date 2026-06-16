# Integração Apify + LinkedIn — WeDO Talent ATS

> Documentação da integração com Apify para scraping de perfis e busca no LinkedIn.

---

## Visão Geral

O sistema usa dois actors do Apify para interagir com o LinkedIn:

| Service | Actor Apify | Função |
|---------|-------------|--------|
| `Apify::LinkedinProfileParserService` | `apimaestro~linkedin-profile-detail` | Extrai dados de perfis específicos (por URL/username) |
| `Apify::LinkedinSearchService` | `harvestapi~linkedin-profile-search` | Busca perfis no LinkedIn por critérios (keywords, cargo, etc.) |

---

## 1. LinkedinProfileParserService — Extração de Perfis

### Aceita coleção de URLs? **SIM**

O service aceita um **array de URLs/usernames** nativamente:

```ruby
Apify::LinkedinProfileParserService.parse(
  linkedin_profile_urls: [
    "https://linkedin.com/in/joao-silva",
    "https://linkedin.com/in/maria-santos",
    "john-doe-123"
  ],
  include_email: true
)
```

### Porém: processamento é SEQUENCIAL (1 a 1)

Apesar de aceitar um array, internamente o service **itera um por um**:

```ruby
# app/services/apify/linkedin_profile_parser_service.rb (linhas 97-119)
urls.each_with_index do |url, index|
  result = parse_single(url, include_email)  # ← 1 chamada Apify por URL
  results << result
end
```

Cada URL dispara:
1. `POST acts/apimaestro~linkedin-profile-detail/runs` — inicia um actor run
2. Polling a cada 5s até completar (máximo 120 tentativas = ~10 min timeout)
3. `GET actor-runs/{id}/dataset/items` — busca o resultado

### Impacto de Performance

| URLs | Tempo estimado (por URL) | Tempo total estimado |
|------|--------------------------|---------------------|
| 1 | ~10-30s | ~10-30s |
| 5 | ~10-30s cada | ~50s-2.5min |
| 20 | ~10-30s cada | ~3-10min |
| 50+ | ~10-30s cada | ~8-25min |

O processamento é **sequencial** — não há paralelismo. Se uma URL falha, o erro é capturado e o service continua para a próxima.

### Progress Broadcasting

Quando chamado com um objeto `Sourcing`, o service faz broadcast do progresso via WebSocket (`SourcingChannel`):

```ruby
Apify::LinkedinProfileParserService.parse(
  linkedin_profile_urls: urls,
  sourcing: sourcing  # ← opcional, habilita broadcast
)
```

Evento enviado por WebSocket:
```json
{
  "type": "sourcing_linkedin_progress",
  "percentage": 40.0,
  "current_profile": 2,
  "total_profiles": 5,
  "sourcing_id": 123
}
```

---

## 2. Onde é usado

### ProcessLinkedinProfilesJob (Batch — Sourcing)

O principal consumidor de múltiplas URLs. Recebe um array de LinkedIn profile URLs do Sourcing:

```ruby
# app/jobs/candidates/process_linkedin_profiles_job.rb
Candidates::ProcessLinkedinProfilesJob.perform_async(
  account_id,
  sourcing_id,
  ["https://linkedin.com/in/user1", "https://linkedin.com/in/user2"],
  true  # include_email
)
```

Fluxo:
1. Recebe array de URLs do Sourcing
2. Chama `Apify::LinkedinProfileParserService.parse` com o array completo
3. Concatena os textos extraídos dos perfis
4. Gera uma query de busca a partir dos textos (`Candidates::SuggestionService`)
5. Atualiza o sourcing com a query gerada
6. Enfileira jobs de busca por cada source configurado

### LinkedinEnrichmentJob (1 a 1 — Candidato)

Enriquece um candidato específico a partir da URL LinkedIn dele:

```ruby
# app/jobs/candidates/linkedin_enrichment_job.rb
Candidates::LinkedinEnrichmentJob.perform_later(candidate_id, account_id)
```

- Processa **1 candidato por vez**
- Retry com backoff exponencial em caso de rate limit
- Descarta em caso de erro de validação
- Cooldown de 7 dias (não re-enriquece se feito recentemente)

### LinkedinEnricher (Lib — Helper)

Utilitário simples para enriquecer candidatos ou buscar payload:

```ruby
LinkedinEnricher.enrich(candidate)
LinkedinEnricher.fetch_payload("https://linkedin.com/in/joao-silva")
```

---

## 3. LinkedinSearchService — Busca no LinkedIn

Busca perfis no LinkedIn por critérios (não por URL). Usa o actor `harvestapi~linkedin-profile-search`:

```ruby
Apify::LinkedinSearchService.search(
  keywords: "Ruby Developer",
  location: "São Paulo",
  # ... outros critérios via QueryBuilder
)
```

Retorna um `ResultSet` com perfis encontrados. Não aceita URLs — é para **descoberta** de perfis.

---

## 4. Limitações e Pontos de Atenção

### Rate Limiting do LinkedIn
- O Apify respeita os limites do LinkedIn
- Se rate limited, o service levanta `RateLimitError`
- Retry automático no job com backoff exponencial
- `retry_after` indica quando tentar novamente (próximo início de hora)

### Não há paralelismo
- Cada URL é processada sequencialmente (um actor run por URL)
- Para melhorar performance com muitas URLs, seria necessário:
  - Paralelizar os runs (múltiplos actor runs simultâneos)
  - Ou usar um actor que aceite batch nativo (ex: Apify actors com input de lista)

### Actor Utilizado
- **Parser de perfil:** `apimaestro~linkedin-profile-detail`
  - Input: `{ username: "joao-silva", includeEmail: true }`
  - Aceita apenas **1 username por run**
  - Cada run custa ~ 1 compute unit do Apify

### Dados Extraídos por Perfil
- `basic_info`: headline, about, location, top_skills
- `concatenated_text`: texto concatenado para uso em queries de busca
- Email (se `include_email: true` — depende do actor encontrar)

---

## 5. Possibilidades de Otimização (Batch)

O service atual processa **1 a 1**, mas a interface já aceita array. Para otimização futura:

| Abordagem | Descrição | Complexidade |
|-----------|-----------|--------------|
| **Runs paralelos** | Disparar N actor runs simultâneos e aguardar todos | Média |
| **Actor de lista** | Trocar por um actor Apify que aceita lista de URLs como input | Baixa (se o actor existir) |
| **Job splitting** | Criar 1 job Sidekiq por URL e processar em paralelo no Sidekiq | Baixa |

---

## 6. Variáveis de Ambiente

| Variável | Descrição |
|----------|-----------|
| `APIFY_KEY` | API key do Apify (obrigatória) |

---

## Resumo

- **Sim**, o service aceita uma coleção de URLs
- **Não**, o processamento não é paralelizado — cada URL dispara um actor run separado e espera a conclusão antes de processar a próxima
- O gargalo é o actor Apify (`apimaestro~linkedin-profile-detail`) que aceita **1 username por run**
- Para grandes volumes, o processamento é feito via Sidekiq job (`ProcessLinkedinProfilesJob`) com progress broadcasting
