# ADR 003 — Estratégia de IDs LIA × ATS Rails

- **Status:** Proposed (aguardando review de 1 arquiteto + 1 líder de produto antes de Accepted)
- **Data:** 2026-04-18
- **Autor:** Plataforma LIA / Task #468
- **Decisão:** **Adiar refactor estrutural. Manter coexistência UUID + Rails bigint, formalizar as convenções já existentes em uma `ID Boundary Policy` documentada e adicionar guard‑rails preventivos (testes, lint, naming).**
- **Política operacional derivada deste ADR:** [`docs/architecture/id-boundary-policy.md`](../architecture/id-boundary-policy.md) — leitura obrigatória para novos endpoints, colunas e payloads de evento que cruzem a fronteira LIA × Rails.
- **Critério de revisão:** Reabrir este ADR se *qualquer* dos gatilhos da seção [Critério de revisão](#critério-de-revisão) for atingido.
- **Issue de implementação:** Apenas as ações da seção [Plano imediato (baixo custo)](#plano-imediato-baixo-custo) — nenhum refactor de fronteira é encomendado por este ADR.

---

## Resumo executivo (1 página, não-técnico)

**O problema.** A LIA fala duas “línguas” de identificador. Para vagas, candidatos e candidaturas, recursos criados dentro da LIA recebem um identificador novo (UUID — uma sequência aleatória); recursos importados do ATS antigo, escrito em Ruby on Rails, mantêm o número sequencial original (1, 2, 3 …). Tudo funciona, mas exige código extra em vários lugares para reconhecer “qual dos dois formatos é esse?”.

**Por que importa.** Já causou um bug visível ao usuário (Task #455: a aba “Vagas” da Visão do Pipeline retornou 404). O risco real não é tecnologia — é que esse tipo de bug se repita em pontos diferentes (analytics, eventos entre sistemas, integrações com clientes). Quanto mais endpoints e tabelas tocam IDs Rails, maior a área de superfície sem uma convenção explícita.

**O que avaliamos.** Três caminhos:
1. **Manter como está + escrever a convenção** (formalizar o que já fazemos).
2. **Camada anti-corrupção:** todo recurso Rails ganha um UUID local na chegada, e o número Rails vira um campo separado de referência.
3. **Padronizar tudo para o formato Rails (números).** Avaliada apenas para completude — significaria reverter a evolução técnica da LIA.

**Recomendação.** Caminho 1, com guard‑rails. O custo é pequeno (1 sprint de uma pessoa) e elimina a recorrência do bug do tipo #455. O caminho 2 (UUID-everywhere) é o ideal de longo prazo, mas custa 2–4 sprints de várias áreas e só se paga se a LIA decidir reduzir a dependência do ATS Rails — decisão de produto que ainda não foi tomada. O caminho 3 é descartado.

**O que muda agora.** Documentamos a regra de fronteira, replicamos o padrão de validação de path do `JOB_ID_PATH_PATTERN` para *candidatos* e *candidaturas*, e adicionamos um teste estrutural que falha o build quando alguém adiciona um `{id}` aceitando string livre. Nenhuma migração de banco. Nenhuma quebra de API.

**Risco de não fazer nada.** Bugs do tipo Task #455 voltam em outras rotas; integrações novas (BI, webhooks de cliente) precisam reaprender as convenções por tentativa e erro; a “memória” do problema fica concentrada em poucas pessoas.

**Risco de fazer o caminho 2 agora.** Migração concorrente em vagas, candidatos, candidaturas, eventos Rails (`rails_event_schemas.py`), analytics e dashboards do BI. Custo alto sem ganho funcional para o usuário final.

---

## Contexto

A plataforma LIA convive com dois formatos de identificador para entidades que cruzam a fronteira com o ATS legado (`ats-api-copia/`, Ruby on Rails):

- **UUID v4** — padrão para tudo que nasce dentro da LIA (Postgres + SQLAlchemy moderno).
- **Inteiro sequencial (Rails `bigint`)** — preservado quando o registro foi originalmente criado no Rails e ingerido via `RailsAdapter`.

Essa coexistência é deliberada — a LIA não “possui” o ciclo de vida completo das entidades importadas — mas **nunca foi documentada como decisão arquitetural**. Cada equipe redescobre a convenção na primeira vez que toca um endpoint dual. Isso explica:

- A motivação do `JOB_ID_PATH_PATTERN` (`app/api/v1/job_vacancies/_shared.py`), introduzido na Task #455 para evitar que um `{job_vacancy_id}` tipado como `str` capturasse silenciosamente uma rota irmã estática como `/job-vacancies/lifecycle-overview`.
- A existência do `RailsAdapter` (`app/domains/integrations_hub/services/rails_adapter.py`) como ponto único de tradução: `_to_rails_id`, `_looks_like_uuid`, e o lookup `GET /v1/candidates?fork_uuid=<uuid>` para resolver UUID → bigint quando o LIA precisa falar com o Rails.
- A presença, mas inconsistência, de colunas “external id” pulverizadas no schema (`job_id`, `ats_candidate_id`, `pearch_profile_id`, `external_id`, `source_system`, `ats_external_id` dentro de `additional_data` JSONB).

Esta task **não é de implementação**. É descoberta + decisão registrada.

---

## Inventário 1 — Superfície de fronteira (onde IDs Rails entram na LIA)

| Origem | Arquivo / componente | Destino na LIA | Tipo na fronteira | Tipo armazenado |
|---|---|---|---|---|
| API Rails (HTTP) | `app/domains/integrations_hub/services/rails_adapter.py` | Service layer (jobs, candidates, applies) | `int` (Rails bigint) | UUID local + `rails_id` virtual |
| Path params HTTP | `app/api/v1/job_vacancies/{crud,lifecycle,analytics,…}.py` | Handlers de vaga | `str` regex `JOB_ID_PATH_PATTERN` (UUID \| `\d+`) | UUID (PK) ou `job_id` VARCHAR(50) |
| Path params HTTP | `app/api/v1/candidates/…` | Handlers de candidato | `str` (sem regex hoje) | UUID ou `ats_candidate_id` VARCHAR(255) |
| Webhooks ATS | `app/api/v1/ats.py` (`POST /ats/webhooks/{provider}`) | Sync pipeline (Gupy, Pandape, Merge) | `str`/`int` por provedor | UUID local + `ats_*_id` VARCHAR |
| Sync connection | `POST /ats/connections/{id}/sync` | ConnectionService | `str` | UUID local |
| Eventos Rails (RabbitMQ) | `app/shared/messaging/rails_event_schemas.py` (`ScreeningCompletedEvent`, `InterviewScheduledEvent`, …) | Consumers internos | `int \| None` (`apply_id`, `candidate_id`, `job_id`) | n/a (payload em trânsito) |
| Publisher unificado | `app/shared/messaging/unified_event_publisher.py` (LIA-E04) | Exchange `lia_rails_events` | `int` | n/a |
| Analytics / BI | `app/api/v1/job_vacancies/analytics.py` | Funnel + readiness | UUID na agregação local; `funnel_data` JSONB pode trazer Rails ids | misto |
| Logs de auditoria | `audit_logs.resource_id` VARCHAR(255) | Observabilidade | string “qualquer coisa” | string (UUID *ou* dígitos *ou* outro) |
| Idempotency keys | `app/shared/robustness/context_management.py` | Layer de robustez | hashing inclui `params` (e portanto o ID literal) | n/a |
| Dashboards | `docs/PLATFORM_MAP.md`, queries BI externas | Reports | misto, sem normalização | n/a |

**Inconsistência mais sensível:** `audit_logs.resource_id` e `idempotency_keys` aceitam *qualquer* string, então duas chamadas — uma com UUID, outra com o bigint correspondente — para o **mesmo recurso lógico** geram registros distintos. Isso é tolerável hoje, mas é um foot‑gun a mencionar em onboarding.

---

## Inventário 2 — Por entidade

> Compilado de `lia_models/`, `ats-api-copia/app/models/` e dos handlers em `app/api/v1/`.

| Entidade | PK no LIA (SQLAlchemy) | PK no Rails | Coluna “external” no LIA | Indexada? | API LIA aceita | API Rails aceita |
|---|---|---|---|---|---|---|
| **Job Vacancy** | `UUID` (`lia_models/job_vacancy.py`) | `bigint` (`app/models/job.rb`) | `job_id VARCHAR(50)` + `source_system VARCHAR(50)` + `additional_data.ats_external_id` em JSONB | `job_id` indexado, `source_system` indexado | UUID **ou** `\d+` (regex `JOB_ID_PATH_PATTERN`) | bigint |
| **Candidate** | `UUID` (`lia_models/candidate.py`) | `bigint` (`app/models/candidate.rb`) | `ats_candidate_id VARCHAR(255)`, `pearch_profile_id VARCHAR(255)` | não-único | UUID **ou** bigint (sem regex hoje — risco) | bigint |
| **Application / Candidacy** | `UUID` (`lia_models/candidate.py::VacancyCandidate`) | `bigint` (`app/models/apply.rb`) | nenhuma coluna explícita; resolve via `RailsAdapter.APPLY_FORK_TO_RAILS` | n/a | UUID (path do vacancy) | bigint |
| **Company / Account** | `UUID` (`lia_models/company.py`) | `bigint` (`app/models/account.rb`) | nenhuma | n/a | UUID | bigint |
| **User** | `UUID` (`lia_models/client_user.py`) | `bigint` (`app/models/user.rb`) | nenhuma direta (link via auth `user_id` UUID) | n/a | UUID | bigint |
| **Conversation** | `UUID` | n/a (LIA-only) | `session_id VARCHAR(255)` indexado | sim | UUID | n/a |
| **Message** | `UUID` | `bigint` (sync only, `app/models/message.rb`) | nenhuma | n/a | UUID | n/a |
| **Screening Question** | `UUID` | n/a | nenhuma | n/a | UUID | n/a |
| **Interview Stage** | `UUID` (`lia_models/recruitment_stages.py`) | `bigint` (`app/models/selective_process.rb`) | `ats_stage_id VARCHAR(255)` + `ATSStageMapping.wedotalent_stage_id` | sim | UUID | bigint |
| **ATS Connection (subscriptions/billing)** | UUID | n/a | `external_id VARCHAR(255)` (Vindi/Iugu) indexado | sim | UUID | n/a |

**Inconsistências detectadas:**
1. **Naming não-uniforme:** `job_id`, `ats_candidate_id`, `ats_stage_id`, `external_id`, `pearch_profile_id`, `source_system`, `additional_data.ats_external_id`. Sete convenções para o mesmo conceito (“o ID que o sistema externo usa”).
2. **Cardinalidade da unicidade:** `ats_candidate_id` não é único; `external_id` em billing é único; `job_id` é apenas indexado. Risco moderado de colisão silenciosa entre tenants se a tradução errar.
3. **Path validation não-uniforme:** apenas `/job-vacancies/{job_vacancy_id}` está blindado por `JOB_ID_PATH_PATTERN`. `/candidates/{id}`, `/applications/…/{id}`, `/recruitment-journey/stages/{id}` ainda aceitam `str` puro.
4. **`fork_uuid` lookup só existe para candidatos.** Vagas dependem de `RailsAdapter.JOB_FORK_TO_RAILS` (mapping) ou inferência por shape. Não há simetria entre entidades.

---

## Inventário 3 — Riscos atuais conhecidos

### 3.1 Bugs históricos
- **Task #455** — `/job-vacancies/lifecycle-overview` retornava 404 porque `{job_vacancy_id: str}` capturava o segmento estático e o handler tentava `UUID("lifecycle-overview")`. Corrigido com (a) `JOB_ID_PATH_PATTERN`, (b) reordenação de routers em `__init__.py`, (c) regression test em `tests/api/test_job_vacancies_route_shadowing.py`.
- **Task #459** — `POST /{vacancy_id}/close` montado fora do prefixo `/job-vacancies` — qualquer primeiro segmento era parseado como `vacancy_id`. Mesma família de bug.

### 3.2 Categorias de risco vivo no código

| Categoria | Local concreto | Severidade | Por que é risco |
|---|---|---|---|
| **Logs ambíguos** | `audit_logs.resource_id`, qualquer `logger.info("...id=%s", id)` | Baixa | UUID e bigint do mesmo recurso aparecem como entradas distintas em queries de auditoria. |
| **Idempotency** | `app/shared/robustness/context_management.py` | Média | Chave inclui `params`; cliente que “muda” o formato do ID consegue rodar a operação duas vezes. |
| **Integridade referencial frágil** | `ats_candidates [(connection_id, external_id) UNIQUE]` no Rails vs `ats_candidate_id` não-único na LIA | Média | Sync com lookup invertido pode linkar UUID a registro Rails inexistente. |
| **RLS / tenant isolation** | `scope_to_tenant` não é aplicado uniformemente do lado Rails (nota em `PLATFORM_MAP.md`) | Média | Lookup por ID puro (sem `company_id`) pode vazar dados entre tenants se um sync futuro confiar só no ID. |
| **Analytics** | `app/api/v1/job_vacancies/analytics.py` faz coalesce entre `repo.get_stage_counts_for_vacancy` (UUID) e `job.funnel_data` (pode vir do Rails) | Baixa | Risco de double-counting se um candidato existir em ambos os formatos. Mitigado pelo `fork_uuid` backfill, mas backfill incompleto = drift silencioso. |
| **Roteamento** | `/candidates/{id}`, `/applications/…/{id}` ainda sem regex de path | **Alta** | É o mesmo padrão exato do bug #455. Ainda não estourou porque não foram adicionadas rotas-irmãs estáticas, mas é uma armadilha aberta. |

---

## Estratégias avaliadas

### Estratégia A — Status quo + convenções formalizadas (RECOMENDADA)

**O que muda concretamente.** Nenhuma mudança de schema. Documentamos a regra (este ADR + uma `docs/architecture/id-boundary-policy.md`). Replicamos o `JOB_ID_PATH_PATTERN` para candidatos e candidaturas. Padronizamos o naming das próximas colunas externas (`external_<system>_id`) — sem renomear as existentes. Adicionamos teste estrutural que falha o build se um path param `{*_id}` em rota dual aceitar `str` sem regex.

**Sistemas tocados.** `app/api/v1/candidates/`, `app/api/v1/applications/`, `app/shared/robustness/context_management.py` (normalizar ID na chave de idempotency), novos testes em `tests/api/`.

**Esforço.** **S–M.** ≈ 1 sprint de 1 pessoa.

**Riscos de migração.** Mínimos. Nenhum dado tocado, nenhum endpoint quebrado.

**Reversibilidade.** Total — é só doc + testes + um regex em path params.

**Impacto em integrações externas.** Zero. Frontend, webhooks e BI continuam recebendo o mesmo formato.

**Trade-off honesto.** A dívida continua presente. Onboarding ainda exige explicar “tem dois formatos”. Risco residual de drift em analytics permanece.

---

### Estratégia B — Anti-corruption layer (UUID-everywhere)

**O que muda concretamente.** Toda entidade Rails ganha um UUID local na ingestão. O bigint Rails vira coluna `external_rails_id BIGINT INDEX UNIQUE` separada. Endpoints LIA aceitam **só UUID**. `RailsAdapter` traduz UUID ↔ bigint internamente, sem expor o bigint na API pública. Eventos `rails_event_schemas.py` passam a publicar **ambos** (`uuid` + `external_rails_id`) durante a transição.

**Sistemas tocados.**
- Schema: migrations para `job_vacancies`, `candidates`, `vacancy_candidates`, `recruitment_stages` e qualquer outra entidade com ID dual. Backfill de UUIDs para registros Rails existentes (idempotente, mas pesado).
- Código: `RailsAdapter` (rewrite parcial), todos os repos (`get_by_id` deixa de aceitar bigint), todos os handlers `/api/v1/*` que hoje usam `JOB_ID_PATH_PATTERN`, `rails_event_schemas.py` (campo dual durante deprecação), consumers de eventos.
- Frontend: nenhum cliente que hoje passa bigint pode continuar fazendo isso. Verificar `apps/recruiter/`, `apps/candidate/`, integrações Slack/Teams.
- BI / dashboards: queries que hoje fazem `WHERE id = <bigint>` precisam migrar para usar `external_rails_id`. Risco de quebrar relatórios “de fora”.
- Webhooks de saída: payloads que hoje incluem bigint Rails precisam de campo dual ou versionamento de schema.

**Esforço.** **L–XL.** Estimativa ≈ 2–4 sprints atravessando 3 squads. Backfill + janela de coexistência inflam o calendário real.

**Riscos de migração.**
- Sync ATS→LIA precisa de lock/janela durante backfill, ou de duplo gravar.
- Cliente externo (BI, webhook receiver) que ainda use bigint Rails quebra se a coluna sair da resposta sem versionamento de API.
- Regressão silenciosa em RLS se a feature flag de “aceitar bigint” for removida antes do backfill terminar.

**Reversibilidade.** Parcial. UUIDs adicionados são fáceis de manter; remover a aceitação de bigint na API é uma decisão difícil de reverter sem versionamento explícito.

**Impacto em integrações externas.** **Alto.** Exige API versioning (`v1` mantém dual; `v2` UUID-only) ou um deprecation window publicado. Quebra a expectativa atual do BI.

**Quando vale a pena.** Quando *qualquer* dos gatilhos abaixo for atingido — só aí o ROI compensa.

---

### Estratégia C — Padronizar tudo para IDs Rails

**O que muda concretamente.** PKs UUID viram PKs bigint sequenciais. Toda entidade LIA-nativa (Conversation, Message, Screening, etc.) ganha um bigint próprio gerenciado por sequence Postgres. UUID some das URLs e dos schemas.

**Sistemas tocados.** Praticamente tudo — modelos, migrations, frontend, eventos, mensageria, idempotency, analytics, auth (UUID é parte do contrato com o auth provider), MCPs, integrações Slack/Teams.

**Esforço.** **XL+.** Vários trimestres.

**Riscos de migração.** Catastrófico — destrói propriedade de unicidade global do UUID, quebra qualquer cliente que tenha referenciado um UUID, e a LIA passa a depender mais (não menos) do paradigma Rails.

**Reversibilidade.** Praticamente nula uma vez que o schema é migrado.

**Impacto em integrações externas.** Inviável.

**Avaliada apenas para completude.** **Descartada.**

---

## Decisão

> **Adiar o refactor estrutural (Estratégia B) e adotar a Estratégia A: formalizar a coexistência atual.**

### Por quê

1. **Custo/benefício.** O bug do tipo Task #455 é de roteamento, não de armazenamento. Ele se resolve completamente com (a) regex em path params + (b) ordenação de routers + (c) teste estrutural — tudo já existe para vagas. Replicar para candidatos/candidaturas é trabalho de horas, não semanas.
2. **Decisão de produto pendente.** O movimento natural para Estratégia B é começar a desacoplar a LIA do Rails. Essa é uma decisão de produto que **ainda não foi tomada**. Investir 2–4 sprints em UUID-everywhere antes dessa decisão é prematuro.
3. **Reversibilidade.** Estratégia A é totalmente reversível. Estratégia B é parcialmente reversível e quebra contratos externos.
4. **Risco residual aceitável.** Os riscos vivos (logs ambíguos, idempotency, drift de analytics) são todos baixos a médios e mitigáveis pontualmente.

### Plano imediato (baixo custo)

Tarefas que **devem** acontecer como follow-up direto deste ADR:

1. **Aplicar `JOB_ID_PATH_PATTERN` (renomeando para `DUAL_ID_PATH_PATTERN`) em rotas de candidato e candidatura.** Estende a defesa de #455 a essas famílias antes que um irmão estático apareça.
2. **Teste estrutural global.** Generalizar `test_item_path_parameters_are_uuid_or_int_constrained` para qualquer rota cujo parâmetro termine em `_id` em entidade dual. Falha de build se alguém adicionar `{x_id}: str` cru.
3. **Documento `docs/architecture/id-boundary-policy.md`.** 1 página: convenção de naming (`external_<system>_id`), quando usar UUID-only, quando aceitar dual, como o `RailsAdapter` é o único broker autorizado.
4. **Normalizar idempotency keys** para que UUID e bigint do mesmo recurso colapsem na mesma chave (resolver via `RailsAdapter._to_canonical_id` antes de hashear).
5. *(Opcional, baixa prioridade)* Adicionar comentário em `audit_logs.resource_id` documentando que pode ser UUID ou bigint, com pointer para este ADR.

### Critério de revisão

Reabrir este ADR (e considerar Estratégia B) se **qualquer** ocorrer:

- (G1) Produto decide explicitamente reduzir/eliminar a dependência do ATS Rails legado.
- (G2) Surgem **2 ou mais** bugs reportados em produção da família Task #455 / #459 nos próximos 6 meses, mesmo com os guard‑rails do plano imediato aplicados.
- (G3) Um cliente externo (BI, integração) reporta double-counting ou quebra de relatório atribuível a IDs duais.
- (G4) Um novo verticalı de produto (ex.: marketplace público, API parceira) exige UUID-only por contrato.
- (G5) Auditoria de segurança (LGPD/ISO) flagra a falta de uniformidade de `resource_id` em `audit_logs` como gap de compliance.

### Como sabemos que a decisão deu certo

- 0 novos bugs do tipo #455 nos próximos 6 meses.
- Onboarding novo consegue achar a `id-boundary-policy.md` sem perguntar.
- Toda PR que adiciona endpoint dual é forçada pelo teste estrutural a usar o `DUAL_ID_PATH_PATTERN`.

---

## Consequências

**Positivas**
- Custo baixíssimo, valor imediato (fecha a recorrência da família #455).
- Decisão arquitetural fica registrada — fim do “redescobrir a convenção a cada onboarding”.
- Não compromete nenhuma decisão futura: Estratégia B continua possível com 100% do trabalho atual aproveitado (o `RailsAdapter` já é o broker; o naming `external_<system>_id` já é o caminho).

**Negativas**
- Dívida arquitetural permanece visível.
- Cada nova entidade dual continua exigindo decisão consciente (mitigada pelo doc + teste estrutural).
- Logs e analytics continuam com risco baixo de ambiguidade.

**Neutras**
- Nenhum impacto em frontend, BI ou integrações externas.

---

## Alternativas consideradas

Vide seções [Estratégia A](#estratégia-a--status-quo--convenções-formalizadas-recomendada), [B](#estratégia-b--anti-corruption-layer-uuid-everywhere), [C](#estratégia-c--padronizar-tudo-para-ids-rails). Resumo:

| Estratégia | Esforço | Reversibilidade | Quebra externos? | Recomendação |
|---|---|---|---|---|
| A. Status quo + convenções | S–M (≈1 sprint, 1 pessoa) | Total | Não | **Adotada** |
| B. Anti-corruption (UUID-everywhere) | L–XL (≈2–4 sprints, 3 squads) | Parcial | Sim (sem versionamento) | Adiada — só com gatilho |
| C. Padronizar para Rails | XL+ (vários trimestres) | Quase nula | Sim, catastrófico | Descartada |

---

## Referências

- Task #455 — `JOB_ID_PATH_PATTERN`, route shadowing.
- Task #459 — `POST /{vacancy_id}/close` fora do prefixo correto.
- Task #468 — esta descoberta + ADR.
- `lia-agent-system/app/api/v1/job_vacancies/_shared.py` — contrato vigente.
- `lia-agent-system/app/api/v1/job_vacancies/__init__.py` — invariante de ordenação de routers.
- `lia-agent-system/tests/api/test_job_vacancies_route_shadowing.py` — defesa executável.
- `lia-agent-system/app/domains/integrations_hub/services/rails_adapter.py` — broker UUID ↔ bigint.
- `lia-agent-system/app/shared/messaging/rails_event_schemas.py` — payloads de evento Rails.
- `docs/PLATFORM_MAP.md` — visão geral da fronteira LIA × Rails.
- ADRs anteriores: `001-python-not-ruby.md`, `002-graph-vs-react.md`.
