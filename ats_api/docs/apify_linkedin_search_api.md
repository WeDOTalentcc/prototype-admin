# Apify LinkedIn Search — Referência Técnica Completa

## Visão Geral

O sistema usa o actor **`harvestapi~linkedin-profile-search`** da Apify para buscar perfis no LinkedIn. A comunicação é feita via REST API da Apify (`https://api.apify.com/v2`), autenticada com `APIFY_KEY` (env var).

---

## Arquitetura dos Services

```
Apify::LinkedinSearchExecutorService          ← Entry point (chamado pelo Sidekiq job)
  └── Apify::LinkedinSearchService            ← Orquestra a busca
        ├── Query                             ← Valida e converte params → actor input
        ├── QueryBuilder                      ← Fluent API para montar queries
        ├── HttpClient                        ← Faraday client (POST/GET + token auth)
        ├── ResultSet                         ← Coleção de profiles + metadata
        ├── Profile                           ← Wrapper dos dados de perfil
        │     ├── Location
        │     ├── Experience
        │     ├── Education
        │     ├── Certification
        │     ├── Project
        │     ├── Volunteering
        │     └── Publication
        └── CostCalculator                    ← Estimativa de custo
```

---

## Autenticação

```
ENV["APIFY_KEY"] → passada como query param `?token=<key>` em todas as requests
```

Arquivo: `app/services/apify/linkedin_search_service/http_client.rb`

```ruby
Faraday.new(url: "https://api.apify.com/v2") do |f|
  f.params["token"] = @api_key   # ENV.fetch("APIFY_KEY")
  f.options.timeout = 300        # 5 min timeout
end
```

---

## Fluxo de Execução

```
1. POST acts/harvestapi~linkedin-profile-search/runs   → inicia o actor run
2. GET  actor-runs/{run_id}                            → polling a cada 5s (max 120x = 10 min)
3. GET  actor-runs/{run_id}/dataset/items              → busca os resultados quando status = SUCCEEDED
```

### Status terminais

| Status | Significado |
|---|---|
| `SUCCEEDED` | Busca concluída com sucesso |
| `FAILED` | Erro na execução |
| `TIMED-OUT` | Actor excedeu tempo limite |
| `ABORTED` | Execução cancelada |

### Tratamento de Erros

| Erro | Classe Ruby | Comportamento |
|---|---|---|
| Rate limit | `RateLimitError` | Retorna `retry_after` (próxima hora cheia) |
| Timeout (polling) | `TimeoutError` | Após 10 min de polling sem resultado |
| Run falhou | `RunFailedError` | Actor retornou `FAILED` |
| Run abortado | `AbortedError` | Actor retornou `ABORTED` |
| HTTP error | `ApiError` | Status code != 2xx |

---

## Parâmetros de Busca (Input do Actor)

### Como usar — Chamada direta

```ruby
Apify::LinkedinSearchService.search(
  search_query: "software engineer",
  locations: ["São Paulo, Brazil"],
  current_job_titles: ["Senior Engineer", "Staff Engineer"],
  mode: :full,
  take_pages: 3,
  max_items: 50
)
```

### Como usar — Fluent Builder

```ruby
Apify::LinkedinSearchService.builder
  .with_query("data scientist")
  .with_titles("Senior Data Scientist", "Lead Data Scientist")
  .in_locations("São Paulo, Brazil", "Rio de Janeiro, Brazil")
  .with_seniority_levels(130, 200)
  .with_experience("5-10")
  .mode(:full_with_email)
  .pages(3)
  .max_results(75)
  .execute
```

### Como usar — Via LinkedinSearchExecutorService (produção)

```ruby
Apify::LinkedinSearchExecutorService.new(
  user: current_user,
  sourcing: sourcing,
  params: {
    query: "product manager",
    locations: ["Brazil"],
    current_job_titles: ["Product Manager"],
    seniority_levels: [130, 200],
    mode: :full_with_email,
    take_pages: 2,
    max_items: 50
  }
).call
```

---

### Tabela Completa de Parâmetros

#### Parâmetros Principais

| Param Ruby | Actor Input (JSON) | Tipo | Descrição |
|---|---|---|---|
| `search_query` | `searchQuery` | `String` | Texto livre de busca (keywords, boolean) |
| `current_job_titles` | `currentJobTitles` | `Array<String>` | Cargos atuais do perfil |
| `past_job_titles` | `pastJobTitles` | `Array<String>` | Cargos anteriores |
| `locations` | `locations` | `Array<String>` | Localidades (ex: `"São Paulo, Brazil"`) |
| `current_companies` | `currentCompanies` | `Array<String>` | URLs de empresas atuais no LinkedIn |
| `past_companies` | `pastCompanies` | `Array<String>` | URLs de empresas anteriores |
| `schools` | `schools` | `Array<String>` | URLs de escolas/universidades no LinkedIn |
| `industries` | `industries` | `Array<String>` | IDs de indústrias |
| `years_of_experience` | `yearsOfExperience` | `Array<String>` | Faixas de experiência (ex: `"5-10"`) |
| `years_at_current_company` | `yearsAtCurrentCompany` | `Array<String>` | Tempo na empresa atual |

#### Filtros Avançados

| Param Ruby | Actor Input (JSON) | Tipo | Descrição |
|---|---|---|---|
| `seniority_levels` | `seniorityLevelIds` | `Array<Integer>` | Nível de senioridade (ver tabela abaixo) |
| `functions` | `functionIds` | `Array<Integer>` | Área funcional (ver tabela abaixo) |
| `company_headcount` | `companyHeadcount` | `Array<String>` | Tamanho da empresa (ver tabela abaixo) |
| `profile_languages` | `profileLanguages` | `Array<String>` | Idioma do perfil (ex: `"pt"`, `"en"`) |
| `first_names` | `firstNames` | `Array<String>` | Filtrar por primeiro nome |
| `last_names` | `lastNames` | `Array<String>` | Filtrar por sobrenome |
| `recently_changed_jobs` | `recentlyChangedJobs` | `Boolean` | Pessoas que mudaram de emprego recentemente |
| `company_headquarter_locations` | `companyHeadquarterLocations` | `Array<String>` | Localização da sede da empresa |

#### Filtros de Exclusão

| Param Ruby | Actor Input (JSON) | Tipo | Descrição |
|---|---|---|---|
| `exclude_locations` | `excludeLocations` | `Array<String>` | Excluir localidades |
| `exclude_current_companies` | `excludeCurrentCompanies` | `Array<String>` | Excluir empresas atuais |
| `exclude_past_companies` | `excludePastCompanies` | `Array<String>` | Excluir empresas anteriores |
| `exclude_schools` | `excludeSchools` | `Array<String>` | Excluir escolas |
| `exclude_current_job_titles` | `excludeCurrentJobTitles` | `Array<String>` | Excluir cargos atuais |
| `exclude_past_job_titles` | `excludePastJobTitles` | `Array<String>` | Excluir cargos anteriores |
| `exclude_industry_ids` | `excludeIndustryIds` | `Array<String>` | Excluir indústrias |
| `exclude_seniority_levels` | `excludeSeniorityLevelIds` | `Array<String>` | Excluir níveis de senioridade |
| `exclude_function_ids` | `excludeFunctionIds` | `Array<String>` | Excluir áreas funcionais |
| `exclude_company_headquarter_locations` | `excludeCompanyHeadquarterLocations` | `Array<String>` | Excluir localização de sede |

#### Paginação e Modo

| Param Ruby | Actor Input (JSON) | Tipo | Default | Descrição |
|---|---|---|---|---|
| `mode` | `profileScraperMode` | `Symbol` | `:short` | Nível de detalhe (ver tabela abaixo) |
| `start_page` | `startPage` | `Integer` | `1` | Página inicial |
| `take_pages` | `takePages` | `Integer` | `1` | Quantidade de páginas (max 100, executor limita a 10) |
| `max_items` | `maxItems` | `Integer` | `0` (sem limite) | Máximo de perfis retornados |

#### Segmentação e Deduplicação

| Param Ruby | Actor Input (JSON) | Tipo | Descrição |
|---|---|---|---|
| `auto_query_segmentation` | `autoQuerySegmentation` | `Boolean` | Segmentação automática da query |
| `auto_query_segmentation_levels` | `autoQuerySegmentationLevels` | `String` | Níveis de segmentação |
| `auto_query_segmentation_target_countries` | `autoQuerySegmentationTargetCountries` | `Array<String>` | Países-alvo para segmentação |
| `deduplication_mode` | `profileDeduplicationMode` | `String` | Modo: `none`, `disabled`, `duplicates_only`, `unique_only` |
| `mongodb_connection_string` | `mongoDbConnectionString` | `String` | MongoDB URL para deduplicação persistente |
| `post_filter_query` | `postFilteringMongoDbQuery` | `String` | Query MongoDB para pós-filtragem |
| `post_filter_aggregation` | `postFilteringMongoDbAggregation` | `String` | Aggregation MongoDB para pós-filtragem |

---

## Valores de Referência

### Modos de Scraping

| Modo Ruby | Actor Value | Dados retornados | Custo/perfil |
|---|---|---|---|
| `:short` | `"Short"` | Nome, headline, empresa, localização, URL | $0.00 |
| `:full` | `"Full"` | Tudo acima + experiências, educação, skills, about | $0.004 |
| `:full_with_email` | `"Full + email search"` | Tudo acima + email (quando disponível) | $0.01 |

**O executor usa `:full_with_email` como default.**

### Seniority Levels

| Chave | ID | Descrição |
|---|---|---|
| `unpaid` | 100 | Não remunerado / Estágio voluntário |
| `training` | 110 | Treinamento / Trainee |
| `entry` | 120 | Júnior / Entry-level |
| `senior` | 130 | Sênior / Pleno |
| `manager` | 200 | Gerente |
| `director` | 210 | Diretor |
| `vp` | 220 | Vice-Presidente |
| `cxo` | 300 | C-Level (CEO, CTO, CFO...) |
| `partner` | 310 | Sócio / Partner |
| `owner` | 320 | Proprietário / Fundador |

### Áreas Funcionais (Functions)

| ID | Área |
|---|---|
| 1 | Accounting |
| 2 | Administrative |
| 3 | Arts and Design |
| 4 | Business Development |
| 5 | Community and Social Services |
| 6 | Consulting |
| 7 | Education |
| 8 | Engineering |
| 9 | Entrepreneurship |
| 10 | Finance |
| 11 | Healthcare Services |
| 12 | Human Resources |
| 13 | Information Technology |
| 14 | Legal |
| 15 | Marketing |
| 16 | Media and Communication |
| 17 | Military and Protective Services |
| 18 | Operations |
| 19 | Product Management |
| 20 | Program and Project Management |
| 21 | Purchasing |
| 22 | Quality Assurance |
| 23 | Real Estate |
| 24 | Research |
| 25 | Sales |
| 26 | Support |

### Company Headcount

| Chave | Código | Faixa |
|---|---|---|
| `self_employed` | A | 1 pessoa |
| `tiny` | B | 2-10 |
| `small` | C | 11-50 |
| `medium_small` | D | 51-200 |
| `medium` | E | 201-500 |
| `medium_large` | F | 501-1000 |
| `large` | G | 1001-5000 |
| `very_large` | H | 5001-10000 |
| `enterprise` | I | 10001+ |

---

## Estrutura do Retorno (ResultSet)

O `LinkedinSearchService.search(...)` retorna um `ResultSet` que é `Enumerable`:

```ruby
result_set = Apify::LinkedinSearchService.search(search_query: "CTO", locations: ["Brazil"])

result_set.size               # quantidade de perfis retornados
result_set.total_count        # total estimado pelo LinkedIn
result_set.has_more?          # true se há mais páginas
result_set.pages_scraped      # páginas processadas
result_set.run_id             # ID do actor run na Apify
result_set.run_status         # "SUCCEEDED"
result_set.rate_limited?      # true se foi rate limited

# Filtros no ResultSet
result_set.with_email         # somente perfis com email
result_set.in_location("São Paulo")  # filtrar por localização
result_set.at_company("Google")      # filtrar por empresa
```

### Campos do Profile

Cada item no `ResultSet` é um `Profile`:

```ruby
result_set.each do |profile|
  # Dados básicos
  profile.full_name              # "João Silva"
  profile.first_name             # "João"
  profile.last_name              # "Silva"
  profile.headline               # "Senior Software Engineer at Google"
  profile.about                  # Bio/summary do perfil
  profile.linkedin_url           # "https://www.linkedin.com/in/joaosilva"
  profile.public_identifier      # "joaosilva"
  profile.object_urn             # URN interno do LinkedIn
  profile.email                  # "joao@email.com" (só no modo full_with_email)
  profile.has_email?             # true/false

  # Foto
  profile.photo_url              # URL da foto
  profile.profile_picture_url(size: "200x200")  # URL em tamanho específico

  # Flags
  profile.open_to_work?          # Disponível para trabalho
  profile.hiring?                # Está contratando
  profile.premium?               # Conta premium
  profile.influencer?            # LinkedIn influencer
  profile.verified?              # Verificado
  profile.memorialized?          # In memoriam

  # Números
  profile.connections_count      # 500+
  profile.follower_count         # 1234
  profile.years_of_experience    # 12

  # Localização
  profile.location.text          # "São Paulo, São Paulo, Brasil"
  profile.location.city          # "São Paulo"
  profile.location.state         # "São Paulo"
  profile.location.country       # "Brazil"
  profile.location.country_code  # "BR"

  # Empresa atual
  profile.current_company        # "Google"
  profile.current_position       # Experience object da posição atual

  # Experiências (Array<Experience>)
  profile.experience.each do |exp|
    exp.title                    # "Senior Engineer"
    exp.company                  # "Google"
    exp.company_url              # "https://linkedin.com/company/google"
    exp.company_id               # 1441
    exp.company_universal_name   # "google"
    exp.company_logo_url         # URL do logo
    exp.location                 # "Mountain View, CA"
    exp.employment_type          # "Full-time"
    exp.workplace_type           # "Remote"
    exp.duration                 # "2 years 3 months"
    exp.description              # Descrição da posição
    exp.current?                 # true se posição atual
    exp.start_date               # { year: 2022, month: 3 }
    exp.end_date                 # { text: "Present" } ou { year: 2024, month: 1 }
    exp.skills                   # ["Ruby", "Python"]
  end

  # Educação (Array<Education>)
  profile.education.each do |edu|
    edu.school                   # "USP"
    edu.school_linkedin_url      # URL da escola
    edu.school_id                # 123
    edu.school_logo_url          # URL do logo
    edu.degree                   # "Bachelor's degree"
    edu.field                    # "Computer Science"
    edu.description              # Descrição
    edu.start_date               # { year: 2010 }
    edu.end_date                 # { year: 2014 }
    edu.period                   # "2010 - 2014"
    edu.skills                   # ["Python", "Algorithms"]
  end

  # Skills
  profile.skills                 # ["Ruby", "Rails", "Python", ...]
  profile.top_skills(5)          # Primeiros 5

  # Idiomas
  profile.languages              # ["Portuguese", "English"]

  # Certificações (Array<Certification>)
  profile.certifications.each do |cert|
    cert.name                    # "AWS Solutions Architect"
    cert.authority               # "Amazon"
    cert.url                     # URL da certificação
    cert.start_date              # Data de emissão
    cert.end_date                # Data de expiração
  end

  # Outros
  profile.projects               # Array<Project> (title, description, url, members)
  profile.volunteering           # Array<Volunteering> (role, organization, cause)
  profile.publications           # Array<Publication>
  profile.courses                # Array de cursos
  profile.patents                # Array de patentes
  profile.honors_and_awards      # Array de prêmios
  profile.causes                 # Array de causas
  profile.received_recommendations # Array de recomendações
  profile.featured               # Array de posts/artigos em destaque
  profile.more_profiles          # Perfis similares sugeridos

  # Metadata
  profile.page_number            # Página em que apareceu
  profile.registered_at          # Data de registro no LinkedIn

  # Serialização
  profile.to_h                   # Hash completo com raw_data
  profile.to_json                # JSON string
  profile.raw_json               # JSON pretty-printed
end
```

---

## Estimativa de Custos

```ruby
cost = Apify::LinkedinSearchService.builder
  .with_query("CTO")
  .in_locations("Brazil")
  .mode(:full_with_email)
  .pages(3)
  .estimated_cost

# => {
#   pages: "$0.30",
#   profiles: "~$0.75",
#   total: "~$1.05",
#   breakdown: {
#     pages: 3,
#     estimated_profiles: 75,
#     cost_per_page: 0.10,
#     cost_per_profile: 0.01
#   }
# }
```

| Item | Custo |
|---|---|
| Por página da busca | $0.10 |
| Por perfil (short) | $0.00 |
| Por perfil (full) | $0.004 |
| Por perfil (full + email) | $0.01 |
| Perfis por página | ~25 |

---

## Validações

Uma query é válida quando:

1. Tem pelo menos um critério de busca: `search_query`, `current_job_titles`, `past_job_titles`, `locations`, `current_companies`, `past_companies`, `schools`, `first_names` ou `last_names`
2. Paginação válida: `start_page > 0`, `take_pages > 0`, `take_pages <= 100`
3. Modo válido: `:short`, `:full` ou `:full_with_email`

---

## Fluxo em Produção (LinkedinSearchExecutorService)

```
Controller/Job → LinkedinSearchExecutorService.new(user:, sourcing:, params:).call
  │
  ├── 1. build_search_options         → monta hash com todos os params
  │     └── Default: mode=:full_with_email, pages=2, max_items=50, locations=["Brazil"]
  │
  ├── 2. LinkedinSearchService.search → executa a busca na Apify
  │
  ├── 3. create_sourced_profiles      → para cada perfil retornado:
  │     ├── Verifica duplicatas (email + linkedin_url via ProfileMatchingService)
  │     ├── Se existente → atualiza dados
  │     ├── Se novo → cria SourcedProfile
  │     └── Cria SourcedProfileSourcing (link com o sourcing)
  │
  └── 4. update_sourcing              → atualiza sourcing com metadata:
        ├── status: "done"
        ├── results_count
        ├── global_results_count (total_count do LinkedIn)
        └── response_metadata: { run_id, pages_scraped, has_more, estimated_cost }
```

### Dados salvos no SourcedProfile

| Campo | Origem no Profile |
|---|---|
| `name` | `full_name` |
| `first_name` | `first_name` |
| `last_name` | `last_name` |
| `title` | `headline` |
| `current_company` | `current_company` |
| `email` | `email` |
| `linkedin_url` | `linkedin_url` |
| `linkedin_slug` | `public_identifier` |
| `city` | `location.city` |
| `state` | `location.state` |
| `country` | `location.country` |
| `location` | `location.to_s` |
| `total_experience_years` | `years_of_experience` |
| `skills_data` | `skills` |
| `languages_data` | `languages` |
| `picture_url` | `photo_url` |
| `summary` | `about` |
| `current_title` | `current_position.title` |
| `followers_count` | `follower_count` |
| `connections_count` | `connections_count` |
| `certifications_data` | `certifications` (serializado) |
| `awards_data` | `honors_and_awards` |
| `experiences_data` | `experience` (serializado) |
| `educations_data` | `education` (serializado) |
| `curriculum_text` | Texto concatenado (nome + headline + about + exp + edu + skills + certs) |
| `profile_data` | JSON com flags (open_to_work, hiring, premium, etc.) + projetos, voluntariado, publicações |

---

## Exemplo de Payload Enviado à Apify

```json
{
  "searchQuery": "software engineer",
  "currentJobTitles": ["Senior Software Engineer", "Staff Engineer"],
  "pastJobTitles": [],
  "locations": ["São Paulo, Brazil"],
  "currentCompanies": [],
  "pastCompanies": [],
  "schools": [],
  "industries": [],
  "yearsOfExperience": ["5-10"],
  "yearsAtCurrentCompany": [],
  "profileScraperMode": "Full + email search",
  "startPage": 1,
  "takePages": 2,
  "maxItems": 50,
  "seniorityLevelIds": [130, 200],
  "functionIds": [8, 13],
  "companyHeadcount": ["E", "F", "G"],
  "profileLanguages": ["pt"],
  "recentlyChangedJobs": false,
  "excludeCurrentCompanies": ["https://linkedin.com/company/competitor"],
  "excludeLocations": ["Manaus, Brazil"]
}
```

---

## Arquivos Relevantes

| Arquivo | Responsabilidade |
|---|---|
| `app/services/apify/linkedin_search_service.rb` | Orquestração: start run → poll → fetch results |
| `app/services/apify/linkedin_search_service/http_client.rb` | Faraday client com auth via token |
| `app/services/apify/linkedin_search_service/query.rb` | Validação + conversão dos params para actor input |
| `app/services/apify/linkedin_search_service/query_builder.rb` | Fluent API para montar queries |
| `app/services/apify/linkedin_search_service/profile.rb` | Wrapper OO dos dados de perfil + inner classes |
| `app/services/apify/linkedin_search_service/result_set.rb` | Coleção Enumerable de profiles + filtros |
| `app/services/apify/linkedin_search_service/cost_calculator.rb` | Estimativa de custo por busca |
| `app/services/apify/linkedin_search_executor_service.rb` | Service de produção: busca + cria SourcedProfiles |
| `app/jobs/apify/linkedin_search_job.rb` | Sidekiq job que chama o executor |
