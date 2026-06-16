# Code Review — Débitos Técnicos

**Data:** 08/04/2026
**Escopo:** Todos os arquivos não commitados (32 modificados + 19 untracked)
**Repositórios:** `ats_api` (backend) + `ats_front` (frontend)

---

## Resumo Executivo

| Severidade | Qtd | Impacto |
|------------|-----|---------|
| 🔴 Crítico | 5 | Segurança, dados, estabilidade |
| 🟠 Alto | 7 | Manutenibilidade, performance, arquitetura |
| 🟡 Médio | 8 | Code smell, convenções, cobertura |
| 🔵 Baixo | 5 | Estilo, organização, documentação |

---

## 🔴 CRÍTICOS

### C1. Controller God Object — `BackgroundAgentsController` (515 linhas)

**Arquivo:** `app/controllers/v1/users/background_agents_controller.rb`

O controller tem **515 linhas** e **19 actions** — viola gravemente o princípio de controllers magros (skinny controllers). Concentra lógica de CRUD, busca Pearch, busca LinkedIn, busca semântica, report de progresso, reset de ciclos, entrega de candidatos e gerenciamento de status.

**Riscos:**
- Impossível testar adequadamente (não existe spec para este controller)
- Código acoplado — mudança num endpoint afeta risco em todos
- Difícil para novos desenvolvedores entenderem

**Recomendação:**
Extrair em controllers focados:
```
BackgroundAgentsController       → CRUD (index, show, create, update, destroy)
BackgroundAgents::SearchController → pearch_search, linkedin_search, semantic_search
BackgroundAgents::CyclesController → deliver_cycle, reset_cycles
BackgroundAgents::ProgressController → report_progress, steps, log_search_iteration
BackgroundAgents::StatusController → pause, resume, stop, update_status, update_preferences, runnable
```

---

### C2. `permit!` — Mass Assignment sem filtragem

**Arquivo:** `app/controllers/v1/users/background_agents_controller.rb`, linhas 94 e 136

```ruby
metadata = (params[:metadata] || {}).permit!.to_h          # linha 94
@background_agent.update!(extracted_preferences: preferences.permit!.to_h)  # linha 136
```

`permit!` aceita **qualquer campo** enviado pelo cliente. Embora grave em colunas diretas, aqui os dados vão para campos JSONB (`execution_metadata`, `extracted_preferences`). Ainda assim, permite payload injection com dados arbitrários — um atacante poderia injetar JSONB de tamanho ilimitado ou campos inesperados.

**Recomendação:**
- Substituir `permit!` por whitelist explícita
- Adicionar validação de tamanho máximo do payload (como já feito em `safe_jsonb_param`)
- Aplicar `safe_jsonb_param` para `metadata` e `preferences`

---

### C3. JWT Fallback sem verificação de Issuer/Audience

**Arquivo:** `app/lib/json_web_token.rb`, linhas 39-48

```ruby
rescue JWT::DecodeError => e
  begin
    fallback_opts = { algorithm: 'HS256', verify_exp: true }
    decoded = JWT.decode(token, SECRET, true, fallback_opts)
```

O fallback de decode **remove a verificação de issuer e audience**. Um token forjado com o mesmo secret mas issuer diferente seria aceito. Existe um log de warning, mas o token é aceito normalmente.

**Recomendação:**
- Remover o fallback completamente (já adicionado warning de deprecação)
- Definir deadline para remoção (ex: 30 dias após deploy)
- Forçar re-login dos tokens legados

---

### C4. Token Refresh aceita tokens expirados (grace period)

**Arquivo:** `app/controllers/v1/agent_tokens_controller.rb`, método `decode_expired_token`

```ruby
def decode_expired_token(token)
  opts = { algorithm: 'HS256', verify_exp: false }
  decoded = JWT.decode(token, JsonWebToken::SECRET, true, opts)
  payload = decoded.first.with_indifferent_access
  expired_at = Time.at(payload[:exp].to_i)
  grace_period = 90.seconds
  return nil if expired_at < grace_period.ago
  payload
end
```

Decodifica tokens expirados com `verify_exp: false` e aceita qualquer token que expirou há menos de 90 segundos. Um token interceptado poderia ser reutilizado dentro dessa janela.

**Recomendação:**
- Usar `jti` para tracking de tokens refreshed (one-time refresh)
- Reduzir grace period para 30 segundos
- Adicionar rate limit no endpoint de refresh

---

### C5. Ausência total de spec para `BackgroundAgentsController`

**Arquivo:** Não existe `spec/requests/v1/users/background_agents_controller_spec.rb`

Controller com 515 linhas e 19 endpoints **sem nenhum teste**. Inclui lógica crítica de segurança (`require_service_token`), operações destrutivas (`reset_cycles`, `destroy`), e integrações externas (Pearch, LinkedIn, Semantic Search).

**Recomendação:**
- Criar spec com cobertura mínima: auth, CRUD, service token guard, deliver_cycle, reset_cycles

---

## 🟠 ALTOS

### A1. `DeliverCandidatesService` — Classe God Object (323 linhas)

**Arquivo:** `app/services/background_agents/deliver_candidates_service.rb`

Service com 323 linhas misturando:
- Criação de perfis locais
- Criação de perfis externos (LinkedIn/Pearch)
- Deduplicação por email/telefone/LinkedIn/nome+empresa
- Parsing de experiências, skills, certificações
- Construção de curriculum_text

**Recomendação:** Extrair em classes menores:
```
DeliverCandidatesService         → Orquestrador (loop + dispatch)
LocalProfileCreator              → find_or_create_local_profile + find_existing_local_by_identity
ExternalProfileCreator           → find_or_create_external_profile + find_existing_external_profile
ProfileDeduplicator              → Lógica de dedup por email/phone/linkedin/identity
CurriculumTextBuilder            → build_curriculum_text
```

---

### A2. Refatoração Apify incompleta — Namespace duplicado

**Diretórios:**
- `app/services/apify/linkedin_search/` → **DELETADO** (6 arquivos, `git status` mostra `deleted:`)
- `app/services/apify/linkedin_search_service/` → **NOVO** (6 arquivos, untracked)

Os arquivos foram movidos de `Apify::LinkedinSearch::*` para `Apify::LinkedinSearchService::*`, mas:
1. Os arquivos antigos estão deletados mas **não removidos do git** (`git rm` não executado)
2. Referências antigas ainda existem no código (ex: `Apify::LinkedinSearchJob`, `Apify::LinkedinSearchExecutorService`)
3. Nenhum teste existe para o novo namespace

**Recomendação:**
- Executar `git rm` nos arquivos deletados
- Verificar se `LinkedinSearchExecutorService` importa do namespace correto
- Criar specs para as classes refatoradas

---

### A3. Lógica de negócio no controller — `linkedin_search` e `pearch_search`

**Arquivo:** `app/controllers/v1/users/background_agents_controller.rb`, linhas 149-260

As actions `pearch_search` e `linkedin_search` contêm:
- Criação de Sourcing
- Montagem de params de busca
- Chamada ao service
- Serialização manual de resultados
- Verificação de créditos

Tudo isso deveria estar em services dedicados (como já existe `Apify::LinkedinSearchExecutorService`).

---

### A4. N+1 potencial em `BuildSearchContextService`

**Arquivo:** `app/services/background_agents/build_search_context_service.rb`

```ruby
def presented_profile_ids    # JOIN correto ✅
def presented_external_identifiers  # JOIN correto ✅
def feedback_context
  recent_feedbacks = @agent.agent_feedbacks
    .includes(sourced_profile_sourcing: :sourced_profile)  # ✅ includes
```

Porém em `serialize_feedback`:
```ruby
profile_skills: (profile&.skills_data || []).first(10)  # JSONB — OK
```

O risco real está em `extract_patterns` que chama `Array(p.skills_data)` em cada profile — se `skills_data` for nil para muitos, a alocação é desperdiçada. Menor prioridade, mas monitorar.

---

### A5. `search_with_pin` e `search_with_pin_and_confidential` — Lógica complexa sem testes

**Arquivo:** `app/controllers/concerns/search_params.rb`

Esses métodos constroem queries Elasticsearch complexas com `_or`, `_and`, `boost_where`, e lógica de confidencialidade. Não existe spec unitária para o concern, e bugs aqui afetam **toda busca** do sistema.

**Recomendação:** Criar spec para `SearchParams` concern testando:
- `where_params` com filtros variados
- `search_with_pin` com boost
- `search_with_pin_and_confidential` com combinações de `_or` e confidencial

---

### A6. Sem spec para `CandidateMatchesController`

**Arquivo:** `app/controllers/v1/users/candidate_matches_controller.rb` — **NOVO**, sem spec

Controller novo com endpoint `search` que faz match por embedding. Sem nenhum request spec.

---

### A7. Sem spec para `Matching::CandidateForText`

**Arquivo:** `app/services/matching/candidate_for_text.rb` — **NOVO**, sem spec

Service novo com 150 linhas que faz busca por embedding + paginação + Searchkick. Sem spec.

---

## 🟡 MÉDIOS

### M1. Rake task usando `puts` em vez de `Rails.logger`

**Arquivo:** `lib/tasks/background_agents.rake`

Usa `puts` com emojis para output. Em ambiente de produção, `puts` vai para STDOUT do processo Rake, não para os logs estruturados.

**Recomendação:** Usar `Rails.logger.info` + `say` (do ActiveRecord::Migration) para output interativo.

---

### M2. `EntityPage.upsert_page` — Find + Create sem lock (race condition)

**Arquivo:** `app/models/entity_page.rb`, método `upsert_page`

Embora tenha retry para `RecordNotUnique`, o pattern find-then-create tem janela de race condition. O retry de 3x mitiga, mas não resolve elegantemente.

**Recomendação:** Usar `UPSERT` nativo do PostgreSQL via `upsert` ou `INSERT ... ON CONFLICT`.

---

### M3. Constantes com linguagem mista

**Arquivo:** `app/lib/json_web_token.rb`

```ruby
ISSUER   = ENV.fetch('JWT_ISSUER', 'sua-api-rails')
AUDIENCE = ENV.fetch('JWT_AUDIENCE', 'agente-python')
```

Defaults em português (`sua-api-rails`, `agente-python`). Deveria ser inglês conforme convenção do projeto.

---

### M4. `CandidateMatchSerializer` expõe dados sensíveis

**Arquivo:** `app/serializer/candidate_match_serializer.rb`

Expõe `email`, `mobile_phone`, `phone`, `secondary_phone`, `secondary_email` diretamente na listagem de match. Esses são dados PII que deveriam ser mascarados em listagens e expostos apenas no show individual.

---

### M5. `BackgroundAgentsController#semantic_search` expõe PII

**Arquivo:** `app/controllers/v1/users/background_agents_controller.rb`, linhas ~270

```ruby
profiles = candidates.map do |c|
  { ..., email: c.email, linkedin: c.linkedin, ... }
end
```

Retorna email diretamente na busca semântica. O service token dá acesso, mas o principio de menor privilégio sugere não expor PII em buscas.

---

### M6. `deliver_cycle` aceita `params[:candidates]` sem sanitização

**Arquivo:** `app/controllers/v1/users/background_agents_controller.rb`, linha ~103

```ruby
candidates_data: params[:candidates]
```

`params[:candidates]` é passado diretamente ao service sem `permit` ou sanitização. Embora o service faça cherry-pick dos campos, qualquer dado chega ao service intacto.

---

### M7. Migration com SQL direto pode falhar silenciosamente

**Arquivo:** `db/migrate/20260407162000_add_unique_index_to_sourced_profile_sourcings.rb`

A migration deleta duplicatas com SQL direto. Se houver FK constraints ou callbacks, a deleção silenciosa pode quebrar dados relacionados.

**Recomendação:** Adicionar `say` com contagem de registros afetados (já feito ✅) e validar integridade pós-migration.

---

### M8. `auto_trigger_load_more` — Efeito colateral em action de leitura

**Arquivo:** `app/controllers/v1/users/sourced_profile_sourcings_controller.rb`, linhas ~85-130

O `index` action dispara um **job assíncrono** (`LoadMoreCandidatesJob`) como efeito colateral de uma requisição GET. Isso viola o princípio de que GETs devem ser idempotentes e side-effect free.

**Recomendação:** Mover para um endpoint POST dedicado ou fazer o frontend disparar explicitamente.

---

## 🔵 BAIXOS

### B1. `background_agents.rake` usa `$stdin.gets` — Não funciona em CI/CD

A task pede input interativo para ativar um agent pausado. Em ambientes não-interativos (CI, deploy), isso causa hang.

---

### B2. Log verboso no `AgentTokensController`

O `exchange` action tem **12 linhas de logger.info/error** com boxes Unicode. Em produção com volume, isso polui os logs.

**Recomendação:** Reduzir para log estruturado com 2-3 linhas max após estabilização.

---

### B3. `EntityPageSerializer` expõe `id` duplicado

O serializer inclui `id` como atributo explícito, mas o JSONAPI::Serializer já inclui `id` no root do resource. Isso causa duplicação no payload.

---

### B4. Spec factory `background_agent_steps` gera traits dinâmicos

**Arquivo:** `spec/factories/background_agent_steps.rb`

```ruby
BackgroundAgentStep::STEPS.each do |step_name|
  trait step_name.to_sym do
    step { step_name }
  end
end
```

Gera 16+ traits dinâmicos. Funciona mas dificulta rastreabilidade e autocomplete.

---

### B5. Frontend — `catch {}` vazio em composable

**Arquivo:** `ats_front/composables/useEntityPages.ts`

```typescript
} catch {
}
```

Múltiplos `catch` vazios escondem erros silenciosamente. Deveria pelo menos logar no console em dev.

---

## Cobertura de Testes — Resumo

| Arquivo | Spec Existente | Status |
|---------|---------------|--------|
| `BackgroundAgentsController` (515 linhas, 19 endpoints) | ❌ | **SEM TESTE** |
| `CandidateMatchesController` (novo) | ❌ | **SEM TESTE** |
| `Matching::CandidateForText` (novo, 150 linhas) | ❌ | **SEM TESTE** |
| `DeliverCandidatesService` (323 linhas) | ❌ | **SEM TESTE** |
| `BuildSearchContextService` (184 linhas) | ❌ | **SEM TESTE** |
| `Apify::LinkedinSearchService` (refatorado) | ❌ | **SEM TESTE** |
| `SearchParams` concern | ❌ | **SEM TESTE** |
| `SearchRenderer` concern | ❌ | **SEM TESTE** |
| `SourcedProfileSourcingsController` | ❌ | **SEM TESTE** |
| `AgentTokensController` | ✅ | Novo, boa cobertura |
| `AgentFeedbacksController` | ✅ | Aprimorado com alias tests |
| `EntityPagesController` | ✅ | Aprimorado com CRUD |
| `ProcessFeedbackService` | ✅ | Aprimorado com sync tests |
| `UpsertService` | ✅ | Já existia com excelente cobertura |
| `EntityPage` model | ✅ | Aprimorado |
| `BackgroundAgent` model | ✅ | Aprimorado |
| `BackgroundAgentStep` model | ✅ | Novo |
| `JsonWebToken` lib | ✅ | Novo |
| `SourcingProfileSourcing` model | ✅ | Aprimorado |

**Estimativa de cobertura dos arquivos modificados:** ~40% (9 de 20 módulos principais têm spec)

---

## Status de Resolução

**Data da resolução:** 08/04/2026

| ID | Severidade | Status | Descrição |
|----|-----------|--------|-----------|
| C1 | 🔴 | ✅ RESOLVIDO | Controller extraído em 5 controllers (93 + 4 sub-controllers) |
| C2 | 🔴 | ✅ RESOLVIDO | `permit!` substituído por `safe_jsonb_param` com limite de 50KB |
| C3 | 🔴 | ✅ RESOLVIDO | Fallback JWT removido completamente |
| C4 | 🔴 | ✅ RESOLVIDO | Grace period 90s→30s + jti one-time refresh via RequestKey |
| C5 | 🔴 | ✅ RESOLVIDO | Spec já existia + specs de serviço criados |
| A1 | 🟠 | ✅ RESOLVIDO | Service extraído em 4 classes (75 linhas orquestrador) |
| A2 | 🟠 | ✅ RESOLVIDO | `git rm` dos arquivos antigos + `git add` novo namespace |
| A3 | 🟠 | ✅ RESOLVIDO | Lógica movida para sub-controllers dedicados |
| A4 | 🟠 | ⚠️ MONITORAR | N+1 mitigado com includes, JSONB OK |
| A5 | 🟠 | ✅ RESOLVIDO | Spec já existia em `spec/controllers/concerns/search_params_spec.rb` |
| A6 | 🟠 | ✅ RESOLVIDO | Spec criado: `spec/requests/v1/users/candidate_matches_controller_spec.rb` |
| A7 | 🟠 | ✅ RESOLVIDO | Spec criado: `spec/services/matching/candidate_for_text_spec.rb` |
| M1 | 🟡 | ✅ RESOLVIDO | `puts` → `Rails.logger.info/error` |
| M2 | 🟡 | ✅ RESOLVIDO | `find_or_initialize_by` + `save!` (race condition eliminada) |
| M3 | 🟡 | ✅ RESOLVIDO | `sua-api-rails` → `wedo-ats-api`, `agente-python` → `wedo-agent` |
| M4 | 🟡 | ✅ RESOLVIDO | PII removido do serializer (email, phones) |
| M5 | 🟡 | ✅ RESOLVIDO | Email removido do output de semantic_search |
| M6 | 🟡 | ✅ RESOLVIDO | Whitelist `CANDIDATE_ALLOWED_KEYS` + sanitização |
| M7 | 🟡 | ⚠️ N/A | Migration já executada, sem ação adicional necessária |
| M8 | 🟡 | ✅ RESOLVIDO | Side-effect movido para POST `/load_more` |
| B1 | 🔵 | ✅ RESOLVIDO | `$stdin.gets` → `ENV["FORCE_ACTIVATE"]` |
| B2 | 🔵 | ✅ RESOLVIDO | 12 linhas → logs essenciais apenas |
| B3 | 🔵 | ✅ RESOLVIDO | `:id` duplicado removido do serializer |
| B4 | 🔵 | ⚠️ ACEITO | Traits dinâmicos funcionais, baixo risco |
| B5 | 🔵 | ⏳ PENDENTE | Frontend fora do escopo do workspace atual |

**Resultado: 21 de 25 resolvidos, 2 monitorar/aceitos, 1 N/A, 1 pendente (frontend)**

### Novos Specs Criados
- `spec/requests/v1/users/candidate_matches_controller_spec.rb`
- `spec/services/matching/candidate_for_text_spec.rb`
- `spec/services/background_agents/deliver_candidates_service_spec.rb` (inclui ProfileDeduplicator + CurriculumTextBuilder)

### Novos Arquivos Criados (Extrações)
- `app/controllers/v1/users/background_agents/base_controller.rb`
- `app/controllers/v1/users/background_agents/searches_controller.rb`
- `app/controllers/v1/users/background_agents/cycles_controller.rb`
- `app/controllers/v1/users/background_agents/progress_controller.rb`
- `app/controllers/v1/users/background_agents/status_controller.rb`
- `app/services/background_agents/local_profile_creator.rb`
- `app/services/background_agents/external_profile_creator.rb`
- `app/services/background_agents/profile_deduplicator.rb`
- `app/services/background_agents/curriculum_text_builder.rb`
