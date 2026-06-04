# Handoff — Funil de Talentos: Busca & Gestão de Resultados

> **Objetivo deste documento:** permitir que um time de devs **replique do zero**, em outro ambiente, toda a funcionalidade de **busca de candidatos** do Funil de Talentos e as abas de **gestão de resultados** (Histórico, Buscas Salvas, Listas, Favoritos).
>
> **Fora de escopo (por enquanto):** a aba **Banco de Talentos** (ainda em construção) — será documentada quando finalizada.
>
> **Como ler:** a **Parte A** descreve a busca como *fluxos end-to-end* (a espinha dorsal). A **Parte B** cobre as abas de gestão. A **Parte C** é material de *referência* (integrações, contratos de API, config, checklist de replicação). Cada funcionalidade traz um bloco **📋 Regras de negócio** explicando *o que* é imposto e *por quê*; o **§17** consolida tudo num quadro-resumo. A tabela de resultados é documentada **uma única vez** (§5).
>
> **Stack:** Next.js + React + TypeScript (`plataforma-lia`) · FastAPI + PostgreSQL/pgvector (`lia-agent-system`) · Rails (`ats_api`, sistema-de-registro legado) · Elasticsearch · Pearch AI + Apify (fontes externas) · Gemini (transcrição/classificação).

---

## Índice

**Parte A — Busca**
1. [Visão geral & arquitetura](#1-visão-geral--arquitetura)
2. [Conceitos-chave: os 2 eixos](#2-conceitos-chave-os-2-eixos)
3. [Anatomia da UI](#3-anatomia-da-ui)
4. [Os 5 fluxos de busca](#4-os-5-fluxos-de-busca)
   - [4.1 Natural](#41-fluxo-natural) · [4.2 Similar](#42-fluxo-similar) · [4.3 JD](#43-fluxo-jd-job-description) · [4.4 Boolean](#44-fluxo-boolean) · [4.5 Archetypes](#45-fluxo-archetypes)
   - [4.6 📋 Regras de negócio da busca (valem para os 5 fluxos)](#46--regras-de-negócio-da-busca-valem-para-os-5-fluxos)
5. [A tabela de resultados (destino comum)](#5-a-tabela-de-resultados-destino-comum)

**Parte B — Gestão de resultados**
6. [Histórico](#6-histórico) · 7. [Buscas Salvas](#7-buscas-salvas) · 8. [Listas](#8-listas) · 9. [Favoritos](#9-favoritos)

**Parte C — Referência**
10. [Fontes & escopo](#10-fontes--escopo) · 11. [Ranking & scoring](#11-ranking--scoring) · 12. [Integrações externas](#12-integrações-externas-pearch--apify) · 13. [Filtros de contato](#13-filtros-de-contato) · 14. [Contratos de API](#14-contratos-de-api) · 15. [Componentes & estado](#15-componentes--estado-frontend) · 16. [Config & env vars](#16-config--variáveis-de-ambiente) · 17. [📋 Quadro-resumo de regras de negócio](#17--quadro-resumo-de-regras-de-negócio) · 18. [Checklist de replicação](#18-checklist-de-replicação-em-outro-ambiente) · 19. [Gaps & pontos de atenção](#19-gaps--pontos-de-atenção)

---

# PARTE A — BUSCA

## 1. Visão geral & arquitetura

O Funil de Talentos é uma SPA React que conversa com o backend FastAPI **sempre via proxy** (`/api/backend-proxy/*` → `/api/v1/*`). O backend orquestra três fontes de dados e devolve uma lista única, rankeada e normalizada de candidatos.

```mermaid
flowchart TD
    U[Recrutador] -->|digita / fala / cola JD| SB[SmartSearchInput<br/>barra de busca]
    SB -->|assistência em tempo real| AS[Assistentes de busca]
    AS --> AC[autocomplete]
    AS --> PQ[parse-query - tags]
    AS --> EP[enhance-prompt - ghost text]
    AS --> AN[analyze - completude]
    SB -->|submit| GUARD[FairnessGuard<br/>bloqueia termos discriminatórios]
    GUARD --> PROXY[Next.js proxy<br/>/api/backend-proxy/*]
    PROXY --> API[FastAPI<br/>/api/v1/search/candidates]
    API --> CRED[CreditService<br/>checa/debita créditos]
    API --> LOCAL[(Local: PostgreSQL<br/>pgvector + Elasticsearch)]
    API --> PEARCH[Pearch AI v2]
    PEARCH -.circuit OPEN.-> APIFY[Apify fallback<br/>LinkedIn scraping]
    LOCAL --> FUSE[WRF / hybrid score]
    PEARCH --> FUSE
    APIFY --> FUSE
    FUSE --> CLASS[Classificação LLM<br/>+ rubric scoring + corte de relevância]
    CLASS --> RESP[SearchResponse]
    RESP --> TABLE[CandidateSearchResultsView<br/>tabela de resultados]
```

**Princípios para replicação:**
- O frontend nunca chama o backend diretamente — sempre pelo proxy `/api/backend-proxy/...` (resolve CORS/cookies httpOnly).
- A busca externa (Pearch/Apify) **só dispara se explicitamente habilitada** (`search_pearch=true`). O default do lib é `false` (busca local).
- Tudo é **multi-tenant**: os candidatos retornados são sempre filtrados por `company_id` ativo (do JWT). Nunca confie em `company_id` vindo do cliente.

---

## 2. Conceitos-chave: os 2 eixos

> ⚠️ **O erro mais comum** é achar que "local/híbrida/global" são os tipos de busca. **Não são.** Existem **dois eixos ortogonais** que se combinam livremente.

### Eixo 1 — Tipo de busca (*como* você expressa a intenção)

| Tipo | O que é | Entrada |
|---|---|---|
| **Natural** | Linguagem natural, com assistência (autocomplete, tags, ghost text, voz) | Texto livre ou áudio |
| **Similar** | "Ache parecidos com este perfil/CV" via similaridade vetorial | Um candidato/CV de referência |
| **JD** | Cola uma Job Description inteira; o sistema extrai requisitos | Texto longo (a vaga) |
| **Boolean** | Operadores `AND` / `OR` / `NOT` para controle fino | Expressão booleana |
| **Archetypes** | Busca a partir de um arquétipo salvo (template de perfil) | Seleção de arquétipo |

### Eixo 2 — Fonte / escopo (*onde* procura)

| Fonte (UI) | Flags backend | Fonte de dados | Custo |
|---|---|---|---|
| **Local** | `search_local=true`, `search_pearch=false` | PostgreSQL (pgvector) + Elasticsearch internos | Grátis |
| **Híbrida** | `search_local=true`, `search_pearch=true` | Local **+** Pearch, fundidos via WRF | Créditos Pearch + enrich |
| **Global** | `search_local=false`, `search_pearch=true` | Só Pearch (Apify como fallback) | Créditos Pearch + enrich |

### A matriz (qualquer tipo × qualquer fonte)

|  | Local | Híbrida | Global |
|---|---|---|---|
| **Natural** | ✅ | ✅ | ✅ |
| **Similar** | ✅ | ✅ | ✅ |
| **JD** | ✅ | ✅ | ✅ |
| **Boolean** | ✅ | ✅ | ✅ |
| **Archetypes** | ✅ | ✅ | ✅ |

O **tipo** define qual endpoint/preparo de query roda; a **fonte** define quais flags (`search_local`/`search_pearch`) vão no payload. Os dois são escolhidos independentemente na UI antes do submit.

---

## 3. Anatomia da UI

Componente raiz canônico: `plataforma-lia/src/components/pages/candidates-page.tsx` (719 linhas — **única implementação válida**; não criar alternativas). Orquestrado por `useCandidatesPageCore` + `CandidatesPageHeader` + `CandidatesPageModals` + `CandidateSearchResultsView` + a barra de busca (`SmartSearchInput`).

### 3.1 As 6 abas do Funil

| Aba | Componente | Status |
|---|---|---|
| **Busca / Resultados** | `CandidateSearchResultsView` | ✅ documentada (§4, §5) |
| **Histórico** | `talent-funnel-tabs/history-tab.tsx` | ✅ §6 |
| **Buscas Salvas** | `talent-funnel-tabs/saved-searches-tab.tsx` | ✅ §7 |
| **Listas** | `talent-funnel-tabs/lists-tab.tsx` | ✅ §8 |
| **Favoritos** | `talent-funnel-tabs/favorites-tab.tsx` | ✅ §9 |
| **Banco de Talentos** | — | ⛔ fora de escopo (em construção) |

### 3.2 A barra de busca (`SmartSearchInput` / `SSIModeNatural`)

Arquivo: `plataforma-lia/src/components/search/ssi-modes/SSIModeNatural.tsx`.

| Controle | Ação | Localização |
|---|---|---|
| **Abas de tipo** | Natural · Similar · JD · Boolean · Archetypes | seletor de modo |
| **Seletor de fonte** | 🏠 Home (Local) · ⚡ Zap (Híbrida) · 🌐 Globe (Global) | `SSIModeNatural.tsx:115-189` — trocar p/ Híbrida/Global abre modal de confirmação de custo |
| **Filtro Email** | ✉️ exige email (`require_emails`) | `:191-243` |
| **Filtro Telefone** | ☎️ exige telefone (`require_phone_numbers`) | `:191-243` |
| **Microfone** 🎤 | grava áudio e transcreve (Gemini) | `AudioRecordButton` (ver §4.1) |
| **Buscar** 🔍 | dispara a busca | — |

A troca de fonte para Híbrida/Global passa por `confirmSourceChange` (`useCandidatesSearch.ts:193`); ligar filtros de contato passa por `handleContactFilterChange` (`:220`), que abre modal de custo de enriquecimento.

---

## 4. Os 5 fluxos de busca

Todos os 5 tipos seguem o **mesmo template de fluxo** (facilita a replicação). As **regras de negócio comuns** aos cinco (créditos, fairness, revelação de contato, corte de relevância, dedup, tenant) estão consolidadas no **§4.6** — cada fluxo abaixo só anota o que é *específico* dele.

### 4.1 Fluxo Natural

**O que é:** busca por linguagem natural ("devs frontend sênior em SP, remoto, React"), com toda a camada de assistência por IA. É o modo default e o mais usado.

**Gatilho:** aba **Natural** (default) na barra de busca.

**Entrada:** três métodos —
- **Texto** no `textarea`.
- **🎤 Voz** → `AudioRecordButton` (`plataforma-lia/src/components/ui/audio-record-button.tsx`): grava, envia via `transcribeAudio` (`:181`) para o proxy `/api/backend-proxy/transcribe/audio` (`:59`) → backend `POST /api/v1/voice/transcribe` (`lia-agent-system/app/api/v1/voice.py:70`), **provider Google Gemini `gemini-2.5-flash`**. O texto transcrito é inserido no `textarea`.

**Assistência em tempo real** — **4 elementos distintos**:

```mermaid
flowchart LR
    T[usuário digitando] --> AC[1. Autocomplete dropdown]
    T --> PQ[2. Tags de entidade]
    T --> GT[3. Ghost text inline]
    GT --> FC[3b. Card de sugestão fallback]
    T --> CP[4. Score de completude + alertas]
```

| # | Elemento | Componente (linha) | Fonte de dados |
|---|---|---|---|
| 1 | **Autocomplete** (dropdown com categorias: cargo, skill, local…) | `SSIModeNatural.tsx:315-426` | `GET /api/backend-proxy/search/autocomplete` → `get_predictive_suggestions` (`search_assistant.py:494`). Debounce ~400ms, mín. 2 chars na última palavra |
| 2 | **Tags de entidade** (chips: localização, cargo, skills, experiência) | `SSIModeNatural.tsx:429-472` | `POST /api/backend-proxy/search/parse-query` → regex `jd_search.py:304` |
| 3 | **Ghost text** (sufixo cinza inline; **Tab** aceita) | `SSIModeNatural.tsx:79-88` | `POST /api/backend-proxy/search/enhance-prompt` (mostra se confiança > 0.6) |
| 3b | **Card "Sugestão"** (fallback quando o ghost não casa com o prefixo) | `SSIModeNatural.tsx:288-313` | mesmo endpoint `enhance-prompt` |
| 4 | **Score de completude + alertas** | via `analyze` | `POST /api/backend-proxy/search-assistant/analyze` → 5 critérios: cargo, localização, anos de experiência, skills, indústria |

#### 4.1.1 ⚙️ Determinístico vs 🤖 LLM — a verdade da camada de assistência

> ⚠️ **Mito a derrubar:** olhando a UI, parece que "tudo é IA preditiva". **Não é.** Dos 4 elementos de assistência, **apenas o ghost text (enhance-prompt) usa LLM**. Os outros três são **100% determinísticos** (dicionários estáticos + regex + contagem). Replicar isso **não** exige modelo de ML — exige portar as listas e as regras.

| Elemento | Mecanismo | Usa LLM? | Implementação |
|---|---|---|---|
| **1. Autocomplete** | prefixo/containment sobre taxonomias estáticas | ❌ **Determinístico** | `get_predictive_suggestions` (`search_assistant.py:494`) |
| **2. Tags de entidade** (`parse-query`) | regex + listas estáticas + `confidence` incremental | ❌ **Determinístico** | `parse_search_query` (`jd_search.py:304`) |
| **3. Ghost text / Sugestão** (`enhance-prompt`) | LLM (Gemini via `llm_service`), persona de sourcing | ✅ **LLM** | `misc_search.py:291` |
| **4. Completude + alertas** (`analyze`) | 5 critérios booleanos → `score = preenchidos/5×100` | ❌ **Determinístico** | `analyze_search` (`search_assistant.py:345`) |

**1. Autocomplete — determinístico (dicionário + prefixo).** `get_predictive_suggestions` percorre, **nesta ordem**, e retorna **no máx. 8** itens (`search_assistant.py:506-571`):
1. `AUTOCOMPLETE_TEMPLATES` — casa por `template["pattern"] in query_lower` **ou** `last_word.startswith(pattern[:3])`. É daqui que saem expansões como `sap → "Consultor SAP MM/SD/FI-CO"`, `abap → "ABAP OO"`, `dev → "Desenvolvedor Backend/Frontend/Full Stack"`, `data → "Data Scientist/Engineer/Analyst"`.
2. `JOB_TITLES_TAXONOMY` · 3. `SKILLS_TAXONOMY` · 4. `LOCATIONS_TAXONOMY` · 5. `INDUSTRIES_TAXONOMY` — todas por `title.lower().startswith(last_word)` (prefixo da **última palavra**).

> 🔴 **NÃO é predição/ML.** Não há análise de contexto, embedding nem ranking aprendido. "Tech Lead", "SAP S/4HANA" etc. **vêm de listas hardcoded**, não de inferência. Disparo no front com **debounce ~400ms** e **mín. 2 chars** na última palavra. Endpoints irmãos (mesma natureza determinística): `/suggestions` (`BEST_PRACTICES` + taxonomias, ordenado por `popularity_score` fixo) e `/synonyms` (lookup em `SYNONYM_MAP`).

**2. Tags de entidade — determinístico (regex + listas).** `parse-query` extrai 5 grupos de entidades por regex/listas estáticas e soma **`confidence` incremental** (`jd_search.py:304-623`):
- **Cargo** (`job_title`), **Localização** (cidades + UF), **Senioridade/Anos** (aliases + `\d+ anos`), **Skills** (lista de ~centenas de termos; `+0.2`, máx. 8), **Setor/Indústria** (regex por vertical; `+0.15`, primeiro match).
- **Normalização canônica:** `js`→`JavaScript`, `ts`→`TypeScript`, `nodejs`→`Node.js`, `k8s`→`Kubernetes`, `ml`→`Machine Learning`, `inglês fluente`→`Inglês Avançado`. `confidence` é **somatório capado em 1.0** (não é probabilidade de modelo). Se faltar grupo, devolve `suggestions[]` textuais ("Especifique o cargo…").

**3. Ghost text / Sugestão — LLM (o único cérebro de verdade).** `enhance-prompt` (`misc_search.py:291`) chama o **LLM (Gemini via `llm_service`)** com uma **persona de sourcing/recrutamento** e retorna:
- `enhanced_query` — a busca reescrita/completada (**~200 chars máx.**), que vira o **ghost text inline** (sufixo cinza; **Tab** aceita) quando casa com o prefixo, ou o **Card "Sugestão"** (fallback) quando não casa.
- `explanation` (por que melhorou) + `suggestions[]` com `{label, value, category}`.
- **Gating no front:** só aparece se **confiança > 0.6**. É **aqui** — e só aqui — que mora a "inteligência" de inferir o perfil ideal a partir de texto incompleto.

**4. Completude + alertas — determinístico (5 critérios × 20 pts).** `analyze` calcula `calculate_completeness` sobre exatamente **5 chaves** — `job_title`, `location`, `years_experience`, `skills`, `industry` — cada preenchida vale **20 pts** → `score = (preenchidos/5)×100` (`search_assistant.py:146-166`). `analyze_search_quality` (`:169-227`) gera alertas por regra fixa:
- **`broad_search`** (WARNING) se `completeness < 40`.
- **`restrictive_search`** (INFO) se `completeness == 100` **e** `len(query) > 100`.
- **`ambiguous_term`** (INFO) para termos vagos hardcoded (`dev`, `analista`, `gerente`, `engineer`) quando não há especificador.
- **`synonym_suggestion`** (INFO) via `SYNONYM_MAP` (ex.: sugere `node/react/vue` ao ver `javascript`).

**Submit:** monta `SearchRequest` com `query` + `search_spec` (entidades) + flags de fonte/contato (payload completo em §14).

**Backend:** `POST /api/v1/search/candidates` (`search.py:105`). Gera `search_fingerprint` → busca multi-fonte → enriquece → rankeia.

**→ Tabela de resultados (§5).** Específico do Natural: as tags de entidade alimentam o `search_spec` que aparece como filtros aplicados.

**Edge cases:** query < 5 chars não dispara parse; autocomplete só na última palavra; transcrição falha → mantém o texto digitado.

### 4.2 Fluxo Similar

**O que é:** "encontre candidatos parecidos com este" — similaridade vetorial pura a partir de um perfil/CV de referência.

**Gatilho:** aba **Similar** (ou ação "Buscar similares" em um candidato). **Entrada:** um candidato de referência (id) ou um CV.

**Submit/Backend:** `POST /api/backend-proxy/search/candidates/similar` → `similar_search.py`. Usa o embedding do perfil de referência e faz nearest-neighbor por cosine no pgvector.

**Específico:** ranking por distância vetorial (`1 - (embedding <=> :embedding::vector)`); a tabela mostra **similaridade** em vez de match-score de vaga.

### 4.3 Fluxo JD (Job Description)

**O que é:** cola-se uma vaga inteira; o sistema extrai requisitos (essential/important/nice-to-have) e busca/ranqueia contra eles.

**Gatilho:** aba **JD**. **Entrada:** texto longo da JD (ou `job_id` existente).

**Submit/Backend:** `POST /api/backend-proxy/search/candidates/by-job-description`.

**Específico:** quando há `job_id`/JD, aplica **rubric scoring** (§11) com `RubricEvaluationService` (BARS). A tabela ganha coluna **Match Score** (0–99) + `match_summary` por candidato.

### 4.4 Fluxo Boolean

**O que é:** controle fino com `AND`/`OR`/`NOT` (ex.: `(React OR Vue) AND TypeScript NOT estágio`).

**Gatilho:** aba **Boolean**. **Submit/Backend:** mesmo `POST /api/v1/search/candidates`, com a expressão interpretada na camada de query (full-text/Elasticsearch).

**Específico:** combina match textual (BM25/text score) com hybrid score.

### 4.5 Fluxo Archetypes

**O que é:** busca a partir de um **arquétipo** salvo (template de perfil reutilizável).

**Gatilho:** aba **Archetypes** → seleciona um arquétipo. **Submit/Backend:** `POST /api/backend-proxy/search/archetypes/{id}/search` — o arquétipo carrega query+spec pré-definidos e executa como busca normal.

### 4.6 📋 Regras de negócio da busca (valem para os 5 fluxos)

> Estas regras se aplicam **independentemente do tipo** escolhido. São o coração do comportamento da busca — entendê-las é o que separa "renderizar uma tabela" de "replicar o produto".

**a) Créditos & custo**
- Créditos são **debitados por execução de busca** (não por candidato individual revelado), via `CreditService.consume_action` (`credit_service.py:152`), que faz o decremento com **lock de linha** (`with_for_update`) para evitar corrida.
- **Custo Pearch (por candidato):** base `fast` = **1 crédito**; add-ons `+insights` (+1), `+profile_scoring` (+1), `+high_freshness` (+2) — `pearch_service.py:221-224`.
- **Apify é cobrado em USD/BRL, não em créditos internos:** `apify_search` $0.02, `enrich`/`profile_scrape`/`email_finder` $0.01 cada — `consumption_tracking_service.py:20-27`.
- ⚠️ **Saldo insuficiente NÃO bloqueia a busca.** O sistema **retorna os resultados mesmo assim**, com aviso *"Créditos insuficientes… Resultados foram retornados, mas a ação não foi debitada"* (`search.py:413`). Decisão de produto: nunca deixar o recrutador "na mão" — degrada o billing, não a experiência. Quem replicar precisa decidir conscientemente se mantém esse comportamento.

**b) Fairness / anti-discriminação (FairnessGuard)**
- Antes de executar, o `FairnessGuard` **intercepta a query e bloqueia termos discriminatórios** (gênero, raça, idade, religião, etc.) — `fairness_guard.py:153-328`.
- O bloqueio **não retorna erro**: devolve uma **mensagem educativa** explicando a razão legal/ética (`fairness_guard.py:166-171`). É uma regra de compliance (EU AI Act / anti-viés), não um simples validador.

**c) Revelação de contato & LGPD**
- Contatos vêm **mascarados por default** (`show_emails=False`); só são revelados se `show_emails`/`show_phone_numbers=true` (`search.py:142-143`). Revelar via Apify custa $0.01/tentativa.
- Com `require_emails`/`require_phone_numbers`, candidatos **sem contato são descartados** — regra de *"honest diagnostics"* (`search.py:356-368`): o modo de busca não finge ter encontrado quem não pode ser contatado. Os descartados são **persistidos** (§5.5), não perdidos.
- **Base legal LGPD:** Legítimo Interesse para recrutamento (Art. 7º, IX); toda revelação/uso passa por `AuditService` para trilha de auditoria (`_persist.py:6`).

**d) Corte de relevância**
- `EsScoreDropAnalyzer` **corta candidatos abaixo do limiar** de score, com tolerância por `qualification_level`: alta exigência tolera 40% de queda, média 55%, baixa 70% (`es_analyzer.py:12-16`).
- A classificação LLM marca incompatíveis (ex.: Saúde × Tecnologia); o rubric segue BARS com regra **"DO NOT INFER"** (`rubric_evaluation_service.py:335-342`). **Override:** o recrutador relaxa via `strict_filters=false` ou ajustando o `search_spec`.

**e) Dedup & suppression (economia)**
- Resultados Pearch são **deduplicados contra a base local** (`_dedup_pearch_against_local`).
- Até **500 docids já conhecidos** do tenant são enviados como `docid_blacklist` à Pearch (`_persist.py:236-267`, `search.py:145`). **Razão de negócio:** não pagar duas vezes pelo mesmo perfil nem duplicar na UI.

**f) Resiliência & reaproveitamento (economia)**
- Se o circuito da Pearch abre, cai para Apify (se habilitado) — `search.py:160-168`.
- O endpoint **`/snapshot` rehidrata resultados anteriores a custo ZERO de créditos** usando o `search_fingerprint` (`search.py:465-474`). Reabrir uma busca do Histórico não cobra de novo.

**g) Tenant & permissão**
- Todo endpoint usa `Depends(require_company_id)` (`require_company_id.py:116`): resolve o `company_id` do JWT e escopa a sessão.
- **"Rule Zero" (defense-in-depth):** mesmo com RLS no Postgres, **toda query de repositório inclui explicitamente `.where(company_id == company_id)`**. Busca global (paga) exige tenant com `company_id` ativo e saldo/plano gerido pelo `CreditService`.

---

## 5. A tabela de resultados (destino comum)

> **Todos os 5 fluxos terminam aqui.** É o **mesmo componente** (`CandidateSearchResultsView`) para qualquer tipo/fonte. Replique uma vez só.

Arquivo: `plataforma-lia/src/components/.../CandidateSearchResultsView.tsx`.

### 5.1 Estrutura

```mermaid
flowchart TD
    CRV[CandidateSearchResultsView] --> BAB[BulkActionsBar<br/>aparece com seleção]
    CRV --> SCB[SearchControlsBar<br/>sort / filtros / colunas]
    CRV --> CTA[CandidatesTableArea<br/>linhas + paginação]
    CTA --> ROW[Linha do candidato<br/>nome, score, fonte, contato, ⭐]
```

### 5.2 Bulk actions (barra que aparece ao selecionar candidatos)

`onAddToVacancy` · `onAddToList` (Importar p/ lista) · `onShare` · `onBulkEmail` · `onWSIScreening` · `onToggleFavoriteBatch` · `onHide` (ocultar) · **Save to Base** (persistir contatos revelados via `POST /candidates/persist-revealed`).

### 5.3 Controles (SearchControlsBar)

Sort (Match Score · Mais recentes…) · filtros de tabela · config de colunas · paginação (`CandidatesTableArea`).

### 5.4 Por linha

Nome, título/empresa atual, **badge de fonte** (Local/Pearch), **score** (match de vaga ou similaridade), status de contato (revelado/bloqueado), **👍/✖ feedback de busca** (Like/Dislike — §5.8), **⭐ favoritar** (§9), ação "adicionar à lista" (§8).

> ⚠️ **Não confundir** os dois marcadores por linha: **⭐ Favoritar** (§9, bookmark privado persistido por usuário) é **diferente** de **👍/✖ Like/Dislike** (§5.8, sinal de qualidade que **calibra o ranking**). Detalhe e comparação completa em §5.8.

### 5.5 Candidatos descartados

Candidatos filtrados por falta de email/telefone (quando `require_*` ligado) **não somem silenciosamente** — são persistidos em `candidate_searches.discarded_candidates` (JSONB, migração `083_persist_discarded_candidates`) e acessíveis via `GET /api/backend-proxy/search/{search_id}/discarded`. A UI mostra a contagem de descartados (⚠️ no Histórico, §6).

### 5.6 Mapeamento de candidato

`useCandidatesExecuteSearch.ts` → `mapCandidateToInternal` normaliza o `CandidateSearchResultDTO` (de Local, Pearch ou Apify) para o modelo interno único da tabela. **Toda fonte converge nesse mapper** — replicar esse contrato é essencial.

### 5.7 📋 Regras de negócio (tabela de resultados)

- **Persistir contatos revelados ("Save to Base"):** só o que foi revelado/pago pode ser persistido na base local (`POST /candidates/persist-revealed`), com auditoria. Evita "vazar" para a base perfis que o tenant não pagou.
- **Ocultar (`onHide`)** é por usuário/tenant: remove da visão atual sem apagar o candidato.
- **WSI Screening em lote** dispara a triagem apenas para candidatos elegíveis do tenant (escopo `company_id`).
- **Descartados nunca são silenciados** (§5.5): contagem sempre visível — transparência sobre o efeito dos filtros de contato.

---

## 5.8 Like / Dislike (Search Feedback)

> **O que é:** um sinal **👍 Like / ✖ Dislike** por candidato, na própria linha do resultado, que diz à LIA *"este perfil é (ir)relevante para ESTA busca"*. Diferente de ⭐ Favoritar (bookmark) e de Ocultar/Descartar (sumir da visão), o feedback **calibra o ranking**: likes sobem, dislikes descem candidatos parecidos em buscas com os **mesmos critérios**.

### 5.8.1 UI

- Componente: `plataforma-lia/src/components/search/SearchFeedbackButtons.tsx` — **👍 `ThumbsUp` / ✖ `XCircle`** por linha, com **update otimista** (pinta o estado antes da resposta e reverte em erro).
- Renderizado na coluna `"feedback"` da tabela via `CandidateTableCellRenderer.tsx`.
- POST para o proxy `POST /api/backend-proxy/search/feedback` (→ backend `POST /api/v1/search/feedback/`).
- Na **re-hidratação** de uma busca (reabrir do Histórico / re-executar), o front chama `GET /api/backend-proxy/search/feedback/by-search?fingerprint=…` e re-pinta os 👍/✖ que o recrutador já deu **para aquele conjunto de critérios**.

### 5.8.2 Endpoints (`search_feedback.py`, prefix `/search/feedback`)

| Método | Rota | Função |
|---|---|---|
| `POST` | `/search/feedback/` | Cria/alterna/remove o feedback (toggle — ver 5.8.4). Body: `candidate_id`, `feedback_type` (`like`\|`dislike`), `search_fingerprint?`, `job_id?`, `search_query?`, `candidate_score?`, `candidate_name?`, `reason?` |
| `GET` | `/search/feedback/by-search?fingerprint=` | Re-hidratação: `{ feedbacks: {candidate_id: feedback_type}, total }` do usuário para aquele fingerprint |
| `GET` | `/search/feedback/user/all?job_id=` | Todos os feedbacks do usuário (opcionalmente por vaga) |
| `GET` | `/search/feedback/{job_id}` | Feedbacks de uma vaga + agregados `{likes, dislikes}` |
| `DELETE` | `/search/feedback/{feedback_id}` | Remove um feedback do próprio usuário |

### 5.8.3 Tabela `search_feedbacks`

Modelo: `lia-agent-system/app/models/search_feedback.py` (`libs/models/lia_models/search_feedback.py`). Colunas-chave: `id`, **`company_id`** (RLS), `candidate_id`, `job_id?`, `user_id`, `search_query?`, **`search_fingerprint?`**, `feedback_type` (`like`\|`dislike`), `candidate_score?`, `candidate_name?`, `reason?`, timestamps.
- **RLS por `company_id`:** migração `222_add_company_id_rls_search_feedbacks` (deny-by-default; `company_id` casa `app_current_company_id()::text`).
- **Ancoragem por fingerprint:** migração `225_add_search_fingerprint_to_search_feedbacks` adiciona `search_fingerprint` (a "Fase 2"). O fingerprint = `SHA256[:32]` dos **critérios da busca** (query + filtros), gerado no backend (`_generate_search_fingerprint`). É isso que faz o like **valer para aquele contexto de busca**, não globalmente.

### 5.8.4 Lógica de toggle (idempotente por usuário+candidato)

O `POST` resolve o estado existente por **`user_id` + `candidate_id` (+`job_id`)** e decide (`search_feedback.py:48-80`):
- **Mesmo tipo** do que já existe → **remove** (`{action: "removed"}`). Clicar 👍 de novo desfaz o 👍.
- **Tipo diferente** → **alterna** (`{action: "toggled"}`). De 👍 para ✖ atualiza no lugar.
- **Não existia** → **cria** (`{action: "created"}`).

> ⚠️ **Nuance importante:** o toggle é chaveado por `user_id+candidate_id+job_id`, **enquanto a re-hidratação (`/by-search`)** é chaveada por `user_id+search_fingerprint`. Ou seja: o feedback é gravado por candidato, mas **reapresentado por contexto de busca**.

### 5.8.5 Efeito no ranking (+2.5 / −2.5) e o loop adaptativo

- `LIAScoreService._get_calibration_adjustment` aplica **+2.5 pts por like** e **−2.5 pts por dislike**, com a calibração total **capada em ±5** (`lia_score_service.py`). Os feedbacks do contexto atual entram via `load_search_feedback_for_ranking` (resolvendo pelo mesmo fingerprint).
- **Loop adaptativo (`ml_feedback_service`):** acumula o histórico de feedback para derivar `compute_calibration_adjustment` e `compute_job_weights` (ajuste de pesos por vaga, faixa **±30%**) — ou seja, com volume, a plataforma aprende **quais critérios** o recrutador valoriza naquela vaga e re-pondera o ranking, não só soma ±2.5 por candidato.
- ⚠️ `app/shared/services/ml_feedback_service.py` é um **shim** que delega para `app/domains/analytics/services` (ver §19, dupla implementação).

### 5.8.6 📋 Favoritos × Like/Dislike × Ocultar/Descartados (não confundir)

| Mecanismo | O que faz | Persistência | Escopo | Impacto no ranking |
|---|---|---|---|---|
| **⭐ Favoritos** (§9) | Bookmark de candidatos de interesse | Backend (`favorites`/Rails) | Por usuário, tenant-gated | **Nenhum** (só organiza) |
| **👍/✖ Like/Dislike** (§5.8) | Sinal de qualidade do resultado | Backend (`search_feedbacks`, RLS) | Por usuário, ancorado ao **fingerprint** | **Sim:** ±2.5 (cap ±5) + loop adaptativo (pesos ±30%) |
| **Ocultar (`onHide`)** (§5.7) | Some da visão atual | Por usuário/tenant | Sessão/visão | Remove da lista (não recalibra) |
| **Descartados** (§5.5) | Filtrados por falta de contato (`require_*`) | `candidate_searches.discarded_candidates` (JSONB) | Por busca | Excluídos do resultado (regra de honestidade, não preferência) |

---

# PARTE B — GESTÃO DE RESULTADOS

> ⚠️ **Atenção crítica de replicação:** **Histórico** e **Buscas Salvas** hoje são **client-side** (Zustand + `localStorage`, store `lia-talent-funnel-store`). **Não persistem no backend.** Já **Listas** e **Favoritos** persistem no backend. São dois mecanismos diferentes — não assuma uniformidade. (Migrar Histórico/Buscas Salvas para o backend é a próxima tarefa planejada — §19.)

## 6. Histórico

**Componente:** `talent-funnel-tabs/history-tab.tsx`. **Estado:** `useTalentFunnel` + store Zustand `lia-talent-funnel-store` (limite `MAX_HISTORY_ITEMS = 100`).

**Dado por entrada (`SearchHistoryItem`):** `query`, `mode`, `source`, timestamp (relativo), **result count**, **discarded count**, **searchId** (UUID de `candidate_searches`), **fingerprint**.

**Ações:** re-executar (clicar no card → `onReExecuteSearch`) · excluir (🗑️) · salvar (🔖 → vira Busca Salva) · ver descartados (👤❌) · **Limpar Tudo**.

**Persistência backend (log, não a lista):** toda execução grava em `candidate_searches` via `CandidateRepository.record_search` (`candidates_search.py:68`); colunas: `user_id`, `search_query`, `search_filters` (JSONB), `local_results_count`, `global_results_count`, `search_duration_ms`. A *lista* do histórico vive no navegador. Endpoints: `GET /search/{search_id}/discarded` e `GET /candidates/search/snapshot?fingerprint=`.

### 6.1 📋 Regras de negócio (Histórico)
- **Per-user, mas tenant-gated:** o registro é escopado por `user_id`; os candidatos que ele aponta são sempre filtrados por `company_id` (`candidates_search.py:33-36`).
- **`candidate_searches` é RLS-EXEMPT** (`candidates_search.py:53`) — porque guarda *metadado da busca* (atividade do usuário), não dado protegido de candidato. Os *resultados* continuam sob RLS da tabela `candidates`.
- **Retenção/limite:** sem TTL no backend; o front exibe os últimos **100** itens (localStorage). Limpar o navegador apaga a lista local (o log de backend permanece).
- **Descartados (Task #403):** persistidos em `discarded_candidates` para sobreviverem a refresh.
- **Reabrir sem custo:** re-execução por `snapshot`/fingerprint **não cobra créditos** (ver §4.6f).

## 7. Buscas Salvas

**Componente:** `talent-funnel-tabs/saved-searches-tab.tsx`. **Gatilho de salvar:** botão "Salvar" (🔖) no `CandidatesPageHeader` (`:71-81`, só com busca ativa) ou modal "Nova Busca Salva" (`:423-533`).

**Schema (`SavedSearch`, `talent-funnel-store.ts:24-40`):** `id`, `name`, `description`, `query`, `mode`, `source`, `filters`, `entities`, `metadata`, `usageCount`, `isFavorite` (pin), `avgResults`, `lastUsed`, `createdAt`, `updatedAt`.

**Ações:** salvar · editar/renomear · executar (`SearchCard` → "Executar") · excluir (com confirmação) · favoritar (pin no topo).

### 7.1 📋 Regras de negócio (Buscas Salvas)
- **Campos obrigatórios para salvar:** `id`, `name`, `query`, `mode`, `source`, `createdAt` (`talent-funnel-store.ts:25-38`).
- **Persistência client-side:** vivem em `localStorage` (chave `lia-talent-funnel-store`); limite 100. **Não há tabela própria no backend** hoje → não sincronizam entre dispositivos/usuários e somem ao limpar o navegador.
- **Sem compartilhamento entre usuários:** uma busca salva é privada do navegador daquele usuário. Para colaborar, usa-se **Listas** (§8) ou **Shared Searches** (link com token).
- **Sem alertas/agendamento:** modelo "pull" (o usuário re-executa manualmente). Não há worker/cron — é uma oportunidade de produto, não um bug.

## 8. Listas

Coleções **nomeadas e colaborativas** de candidatos (com cor e descrição). Persistem no backend — **dual** (Python + Rails).

**Componente:** `talent-funnel-tabs/lists-tab.tsx` (hook `useListsTab`). **Como adicionar:** bulk action "List" na tabela (`CandidateSearchResultsView.tsx:315` → `onAddToList`) ou botão "UserPlus" no `ListCard`.

**Endpoints (FastAPI):** `GET /candidate-lists` · `POST /candidate-lists` `{name, description, color}` · `PATCH /candidate-lists/{id}` · `POST /candidate-lists/{id}/candidates` `{candidate_ids, notes}` · `POST /candidate-lists/{id}/assign-jobs` `{job_vacancy_ids, candidate_ids?}`.

**Schema:**
- **FastAPI:** `candidate_lists` (`id`, `name`, `description`, `color`, `company_id`, `is_active`) + join `candidate_list_members` (`list_id`, `candidate_id`, `added_by`, `added_at`).
- **Rails (espelho):** `lists` (`id`, `name`, `description`, `color`, `account_id`, `user_id`) + `list_relationships` (polimórfico: `reference_type`, `reference_id`, `list_id`).

### 8.1 📋 Regras de negócio (Listas)
- **Permissões (Pundit, Rails):** policies (`candidate_list_policy.rb`) restringem tudo ao `account_id` do tenant — criar/editar/excluir/compartilhar exige pertencer ao tenant.
- **Soft-delete:** excluir uma lista marca `is_active = False` (`candidate_list_repository.py:125`) — não apaga fisicamente.
- **Dedup de membros:** inserção em lote usa `on_conflict_do_nothing` (`candidate_list_repository.py:198`) — adicionar um candidato já presente é ignorado silenciosamente.
- **Assign-to-jobs:** vincular membros a vagas cria registros `VacancyCandidate` com `stage="sourcing"`, `status="sourced"` (`candidate_list_repository.py:274-275`) — ou seja, entra no funil da vaga já na etapa de sourcing.
- **Conversão de perfil externo:** adicionar um `SourcedProfile` (perfil externo/Pearch) a uma lista **"reivindica" o perfil para a base do tenant** disparando `ConvertToCandidateJob` (vira `Candidate` real). É o ponto onde um perfil de fora entra oficialmente na base.
- **Compartilhamento:** `ShareSearchModal` cria um `SharedSearch` com **token** (`shared_searches_controller.rb`, `shared_search.rb:27`) — acesso por link, enviado por email/WhatsApp.

## 9. Favoritos

"Bookmarks" pessoais — **por recrutador (user)**, dentro do tenant.

**Componente:** `talent-funnel-tabs/favorites-tab.tsx`. **Como favoritar:** ⭐ na linha (`handleFavoriteClick` → modal de nota opcional) ou bulk (`onToggleFavoriteBatch`).

**Endpoints (FastAPI, `candidates/candidates_metadata.py`):** `POST /v1/candidates/{id}/favorite` (toggle) · `PUT /v1/candidates/{id}/favorite` (atualiza `note`/`is_pinned`) · `GET /v1/candidates/favorites/list`. Request `FavoriteCreate`: `{note, is_pinned, source}`.

**Schema:**
- **FastAPI:** `candidate_favorites` (`id`, `candidate_id`, `user_id`, `company_id`, `note`, `is_pinned`); **`UniqueConstraint(candidate_id, user_id)`**.
- **Rails (espelho):** coluna array `favorite_user_ids` na tabela `candidates` (indexada no Elasticsearch → filtro "Meus Favoritos").

### 9.1 📋 Regras de negócio (Favoritos)
- **Per-user dentro do tenant:** favoritar é pessoal (`user_id`), mas restrito ao `company_id` do recrutador (`candidate_favorites_repository.py:72`). Um favorito de um recrutador **não aparece** para outro.
- **Idempotência:** o `toggle_favorite` checa o par `(candidate_id, user_id)` antes de inserir (`candidates_metadata.py:170`), garantindo a `UniqueConstraint`.
- **Pin:** `is_pinned=true` eleva o candidato; listas vêm ordenadas com pinados primeiro (`candidate_favorites_repository.py:84`).
- **Nota opcional:** `note` livre para o recrutador lembrar o contexto/fit.
- **Favoritos × Listas:** favorito = marcador privado e plano (pin + nota) para *um* recrutador rastrear candidatos entre buscas; lista = coleção nomeada, **compartilhável no tenant**, many-to-many.

---

# PARTE C — REFERÊNCIA

## 10. Fontes & escopo

| Fonte | Quando | Como ligar | Custo |
|---|---|---|---|
| **Local** | default | `search_local=true`, `search_pearch=false` | grátis |
| **Híbrida** | enriquecer com externo | `search_local=true`, `search_pearch=true` | créditos + enrich |
| **Global** | só externo | `search_local=false`, `search_pearch=true` | créditos + enrich |

A troca para Híbrida/Global **abre modal de confirmação de custo** (`AlertDialog` em `SmartSearchInput.tsx:353` → `confirmSourceChange`). O front mapeia `searchSource: 'local' | 'hybrid' | 'global'` (`useCandidatesSearch.ts:45`) para os booleans do payload.

## 11. Ranking & scoring

> **Pipeline ponta-a-ponta:** o texto vira candidatos rankeados em **6 estágios**. Os estágios 1–4 são **busca/fusão** (sempre rodam); o estágio 6 (**BARS/rubric**) **só roda quando há `job_id`/JD**. Cada estágio tem parâmetros reais abaixo — replicar exige portar os números, não só o conceito.

```mermaid
flowchart TD
    Q[query + search_spec] --> A[1. Transformação<br/>embedding + full-text + filtros]
    A --> B[2. Fetch local + Pearch<br/>threshold 0.75 · loop de emails]
    B --> C[3. Fusão WRF<br/>alpha + k dinâmicos]
    C --> D[4. Classificação LLM<br/>compatível? + fallback heurístico]
    D --> E[5. Corte de relevância<br/>EsScoreDropAnalyzer]
    E -->|tem job_id/JD| F[6. BARS / rubric<br/>match score 0-99]
    E -->|sem job_id| G[ranking por hybrid/similaridade]
    F --> R[tabela de resultados]
    G --> R
```

### 11.1 Estágio 1 — Transformação do texto (query → sinais)

A mesma query alimenta **três representações** combinadas no estágio de fusão:
- **Semântica (pgvector):** embedding da query; similaridade = `1 - (embedding <=> :embedding::vector)` (cosine). **Threshold semântico padrão `0.75`** (`rag_pipeline_service.py` — `_DEFAULT_SEMANTIC_THRESHOLD`); só entram candidatos com `similaridade >= 0.75`.
- **Textual (full-text/BM25-like):** `ts_rank` com `plainto_tsquery` sobre `name + summary + skills`.
- **Filtros estruturados:** o `search_spec` (entidades das tags, §4.1) vira `EXISTS`/`IN`/`ILIKE`/`overlap` (`pearch_service.py::search_local_candidates`) — ex.: `industries` por operador de sobreposição, `funding_stages`/`institution_tiers`/`timezones` por subquery.

### 11.2 Estágio 2 — Fetch local + Pearch + dedup

- **Local:** RAG híbrido (semântica + textual) sobre PostgreSQL/pgvector + Elasticsearch.
- **Pearch (se `search_pearch=true`):** quando `require_emails` está ligado, roda o **loop de completude** `_accumulate_pearch_with_emails` (`pearch_service.py`): pagina com `docid_blacklist` + `thread_id` até atingir o `target` de candidatos **com email**, buscando `page_limit = min(max(restantes×2, 5), 50)` por página (compensa a atrição do filtro). Guardas: `SEARCH_HYBRID_EMAIL_MAX_PAGES` e `SEARCH_HYBRID_EMAIL_LOOP_DEADLINE_SECONDS`.
- **Dedup:** `_dedup_pearch_against_local` + suppression de até **500 docids** (§4.6e).

### 11.3 Estágio 3 — Fusão (alpha dinâmico + WRF com k dinâmico)

**Hybrid score (blend semântico×textual):** `hybrid_score = alpha × semantic + (1-alpha) × bm25`. O **`alpha` é dinâmico por tipo de termo** (`rag_pipeline_service.py::_detect_query_type`):

| Tipo de query | alpha (peso semântico) | Racional |
|---|---|---|
| Tech/cargo (keywords técnicas) | **0.3** (BM25 domina) | termo exato importa mais |
| Comportamental | **0.7** (semântica domina) | intenção/contexto importam |
| Default | **0.5** | equilíbrio |

**WRF (Weighted Reciprocal Fusion)** funde os rankings ES × pgvector: `score = w_es × 1/(k + rank_es) + w_pgv × 1/(k + rank_pgv)` (`wrf_dynamic_k_service.py:107-109`). **Pesos por `qualification_level`:** alta → ES 0.6 / PGV 0.4; média → 0.5 / 0.5; baixa → ES 0.4 / PGV 0.6.

**`k` é dinâmico** (controla recall × precisão; base: alta=25, média=45, baixa=70):
- **Precisão (↓ k):** se `top_avg >= 0.75` → `k = max(10, base×0.7)`; também reduz se o cluster é apertado (`spread < 0.05`).
- **Recall (↑ k):** se `top_avg <= 0.35` → `k = min(100, base×1.4)`.

### 11.4 Estágio 4 — Classificação de compatibilidade por LLM

`LLMJobClassificationService` (**Gemini Flash** via `generate_with_fallback`) marca cada candidato `compatible: true/false` (post-filter). **Fallback heurístico** `_heuristic_check` por `INCOMPATIBLE_AREAS` (ex.: bloqueia `saúde × tecnologia`) por detecção de área via keywords — usado quando o LLM falha.

### 11.5 Estágio 5 — Corte de relevância (`EsScoreDropAnalyzer`)

`es_analyzer.py` corta a cauda irrelevante por **dois critérios**:
- **Drop adaptativo:** mantém quem tem `score >= top_score × (1 - threshold)`, com `threshold` por `qualification_level` — **alta 40% · média 55% · baixa 70%**.
- **Queda abrupta:** se a diferença entre dois candidatos vizinhos no ranking ultrapassa `média + 2σ`, fixa o `steep_drop_index` como corte (se for mais restritivo que o adaptativo).

### 11.6 Estágio 6 — BARS / rubric scoring (**só com `job_id`/JD**)

> 🎯 **Onde BARS se aplica:** **avaliação de CV contra os requisitos de uma vaga** (fluxo JD ou busca com `job_id`). Produz o **Match Score (0–99)** + `match_summary`. **Onde NÃO se aplica:** a busca textual/semântica inicial (estágios 1–3), a fusão WRF, e os scores de **WSI / comportamental / cultural fit** — que são pipelines **separados** (§ `lia_score_service` faz o ranking unificado combinando rubricas, WSI, prereq e recência com pesos distintos).

`RubricEvaluationService` (`rubric_evaluation_service.py`) usa **BARS (Behaviorally Anchored Rating Scale)**:
- **Escala (pontos):** `Exceeds=100` · `Meets=75` · `Partial=40` · `Missing=0`.
- **Peso por prioridade:** `Essential=3×` · `Important=2×` · `Nice-to-have=1×`.
- **Multiplicador por evidência:** `Explícita=1.0` · `Implícita=0.7` · `Inferida=0.3`.
- **Fórmula:** `Score = Σ(pontos × evidência × prioridade) / Σ(100 × prioridade) × 100`, **cap 99.0** (100 fica reservado a override manual). Falhar um requisito **Essential** zera o score (exclusão).
- **Regra "DO NOT INFER"** (`:335-342`): o avaliador não inventa o que não está no CV; override do recrutador via `strict_filters=false` ou ajuste do `search_spec`.

### 11.7 Ranking unificado (LIA Score) e calibração por feedback

Quando há dados, `LIAScoreService` combina os sinais num **Ranking Score** ponderado por **disponibilidade de dados** (`rubricas/wsi/big_five/prereq/recency`) × `completeness_factor`, e aplica um **ajuste de calibração** (faixa **−5 a +5**) que **inclui o like/dislike do recrutador** (§5.8): `+2.5` por like, `−2.5` por dislike (`load_search_feedback_for_ranking` + `_get_calibration_adjustment`). Detalhe do efeito e do loop adaptativo (`ml_feedback_service`) em **§5.8**.

## 12. Integrações externas (Pearch + Apify)

### 12.1 Pearch AI (fonte global primária)

- **Serviço:** `PearchService` (`app/domains/sourcing/services/pearch_service.py`). **Endpoint:** `POST https://api.pearch.ai/v2/search`. **Auth:** Bearer `PEARCH_API_KEY` (`:153`).
- **Request (`PearchSearchRequest`):** `query`, `type` ("fast"), `insights`, `high_freshness`, `profile_scoring`, `strict_filters`, `require_emails`, `show_emails`, `limit` (1–1000), `custom_filters`, `docid_blacklist`.
- **Response:** `uuid`, `thread_id`, `status`, `total_estimate`, `search_results[]` (cada um `CandidateProfile`) → mapeado p/ `CandidateSearchResultDTO`.
- **Créditos:** `fast=1`, `+insights=1`, `+profile_scoring=1`, `+high_freshness=2`. Tracking: `ConsumptionTrackingService.record_pearch_consumption`.
- **Circuit breaker:** `failure_threshold=3`, `recovery_timeout=15s`. Timeout `HTTP_TIMEOUT_PEARCH_SECONDS`.
- **Dedup:** `_dedup_pearch_against_local`. **Suppression:** até 500 docids em `docid_blacklist`.

### 12.2 Apify (fallback de scraping LinkedIn)

> **LinkedIn não é uma fonte selecionável na UI.** Apify só entra como **fallback** quando o circuito da Pearch está **OPEN** e `APIFY_SEARCH_FALLBACK_ENABLED=true` (`search.py:160`).

- **Serviços:** `ApifyService`, `ApifySearchService`, `ApifyMCPClient` (`mcp.apify.com`), mapper `ApifyProfileMapper`. **Auth:** Bearer `APIFY_API_KEY`.
- **Actors:** busca `curious_coder/linkedin-search`; scrape `dev_fusion/Linkedin-Profile-Scraper`; email `curious_coder/email-finder`.
- **Custos:** search `$0.02`, scrape `$0.01`, email `$0.01`. **Timeouts:** 120s / 30s / 15s. **Circuit:** `failure_threshold=3`, `recovery_timeout=60s`.
- **Enrichment on-demand:** `ApifyService.enrich_candidate_profile` busca email/dados de um perfil específico.

## 13. Filtros de contato

- Flags `require_emails` / `require_phone_numbers` no `SearchRequestDTO` (`_shared.py:491-492`). Ligar na UI abre modal de custo de enriquecimento.
- Filtro aplicado no backend (`search.py:361`); quem não tem contato vai para **descartados** (§5.5).
- **Validação:** `POST /api/backend-proxy/search/validate-contacts` (`validation.py`, `ContactValidationService`): **MX record** (email) e **E.164** (telefone).

## 14. Contratos de API

**Rota de submit principal:** front `POST /api/backend-proxy/search/candidates` (`lib/api/candidate-search.ts:225`) → backend `POST /api/v1/search/candidates` (`candidate_search/search.py:105`; prefixo `/search` em `candidate_search/__init__.py:24`, sob `/api/v1` em `api/routes.py:304`).

### 14.1 Payload (`SearchRequestDTO` — `_shared.py:470`)

```jsonc
{
  "query": "devs frontend sênior em SP, remoto",   // linguagem natural (obrigatório)
  "thread_id": null,                                 // refinamento (opcional)
  "search_spec": { "location": "...", "skills": [] },// entidades extraídas (opcional)
  "search_local": true,                              // fonte
  "search_pearch": false,                            // fonte (default false no lib!)
  "pearch_type": "fast",
  "local_limit": 20,                                 // 1–100
  "pearch_limit": 15,                                // 0–50
  "show_emails": false,
  "show_phone_numbers": false,
  "high_freshness": false,                           // +2 créditos
  "require_emails": false,
  "require_phone_numbers": false,
  "job_vacancy_id": null,
  "exclude_candidate_ids": [],
  "include_discovered": true,
  "job_id": null                                     // se presente → rubric scoring
}
```

### 14.2 Tabela de endpoints (proxy → backend)

| Função | Proxy (front) | Backend |
|---|---|---|
| Busca principal | `POST /api/backend-proxy/search/candidates` | `POST /api/v1/search/candidates` |
| Parse de query | `POST /api/backend-proxy/search/parse-query` | `parse_search_query` (`jd_search.py:304`) |
| Autocomplete | `GET /api/backend-proxy/search/autocomplete` | `get_predictive_suggestions` (`search_assistant.py:494`) |
| Análise/completude | `POST /api/backend-proxy/search-assistant/analyze` | `search_assistant.py:345` |
| Enhance prompt (ghost) | `POST /api/backend-proxy/search/enhance-prompt` | enhance-prompt |
| Busca similar | `POST /api/backend-proxy/search/candidates/similar` | `similar_search.py` |
| Busca por JD | `POST /api/backend-proxy/search/candidates/by-job-description` | jd_search |
| Busca por arquétipo | `POST /api/backend-proxy/search/archetypes/{id}/search` | archetypes |
| Transcrição (voz) | `POST /api/backend-proxy/transcribe/audio` | `POST /api/v1/voice/transcribe` (`voice.py:70`, Gemini) |
| Descartados | `GET /api/backend-proxy/search/{search_id}/discarded` | discarded |
| Snapshot (rehidratar) | `GET /api/backend-proxy/candidates/search/snapshot?fingerprint=` | snapshot (custo 0) |
| Validar contatos | `POST /api/backend-proxy/search/validate-contacts` | `validation.py` |
| Persistir revelados | `POST /api/backend-proxy/candidates/persist-revealed` | `contact_persistence.py` |
| Listas | `.../candidate-lists*` | `candidate_lists.py` |
| Favoritos | `.../v1/candidates/{id}/favorite`, `.../favorites/list` | `candidates_metadata.py:156` |

## 15. Componentes & estado (frontend)

| Hook / store | Responsabilidade |
|---|---|
| `useCandidatesPageCore` | orquestrador (aba ativa, modais, handlers de bulk) |
| `useCandidatesSearchState` | resultados, contagens, créditos, metadata da busca |
| `useCandidatesViewState` | candidato selecionado, sort, paginação |
| `useCandidatesExecuteSearch` | execução da API + `mapCandidateToInternal` |
| `useSmartSearchCore` | estado interno da barra (parsing, autocomplete, enhancement) |
| `useTalentFunnel` | abas Histórico/Buscas Salvas/Listas/Favoritos |
| `candidates-store.ts` (Zustand) | array de candidatos + loading |
| `talent-funnel-store.ts` (Zustand `persist`) | Histórico + Buscas Salvas (**localStorage**) |

## 16. Config & variáveis de ambiente

| Var / flag | Para quê |
|---|---|
| `PEARCH_API_KEY` | auth Pearch |
| `APIFY_API_KEY` | auth Apify |
| `APIFY_SEARCH_FALLBACK_ENABLED` | habilita fallback Apify quando Pearch circuit OPEN |
| `HTTP_TIMEOUT_PEARCH_SECONDS` | timeout Pearch (~30–60s) |
| (Gemini via integração) | transcrição de voz + classificação de vaga |
| (Elasticsearch URL) | índice full-text local |
| (PostgreSQL + extensão `pgvector`) | embeddings + busca semântica |

## 17. 📋 Quadro-resumo de regras de negócio

> Consolidação de todas as regras espalhadas pelo documento. Use como checklist de paridade ao replicar.

| # | Regra | Onde se aplica | Comportamento / razão | Evidência |
|---|---|---|---|---|
| 1 | Crédito debitado **por execução**, com lock de linha | Busca Híbrida/Global | evita corrida no saldo | `credit_service.py:152` |
| 2 | **Saldo insuficiente não bloqueia** | Busca | retorna resultados + aviso, não debita | `search.py:413` |
| 3 | Custo Pearch: base 1 + insights 1 + scoring 1 + freshness 2 (por candidato) | Pearch | precificação de add-ons | `pearch_service.py:221-224` |
| 4 | Apify em **USD/BRL**, não créditos ($0.02/$0.01) | Apify | billing externo separado | `consumption_tracking_service.py:20-27` |
| 5 | Contatos **mascarados por default**; revelar é opt-in e pago | Busca/contato | minimização de PII | `search.py:142-143` |
| 6 | Sem contato + `require_*` → **descartado** (honest diagnostics), mas persistido | Busca/contato | não fingir resultado contatável | `search.py:356-368` |
| 7 | **FairnessGuard** bloqueia termos discriminatórios (msg educativa) | Busca | compliance anti-viés / EU AI Act | `fairness_guard.py:153-328` |
| 8 | LGPD: base legal **Legítimo Interesse (Art. 7 IX)** + AuditService | Busca/contato | trilha legal | `_persist.py:6` |
| 9 | Corte de relevância por `qualification_level` (40/55/70%) | Ranking | poda de irrelevantes | `es_analyzer.py:12-16` |
| 10 | Rubric BARS **"DO NOT INFER"**; override `strict_filters=false` | Ranking (JD) | objetividade | `rubric_evaluation_service.py:335-342` |
| 11 | Dedup Pearch×local + **suppression 500 docids** | Pearch | não pagar 2x / sem duplicata | `_persist.py:236-267`, `search.py:145` |
| 12 | Circuit breaker **Pearch→Apify** | Resiliência | continuidade da busca | `search.py:160-168` |
| 13 | **Snapshot/fingerprint = custo ZERO** | Histórico/Busca | reabrir sem cobrar | `search.py:465-474` |
| 14 | `require_company_id` + RLS + **Rule Zero** (`.where company_id`) | Tudo | isolamento multi-tenant | `require_company_id.py:116` |
| 15 | Histórico **per-user**, 100 itens (front), `candidate_searches` **RLS-EXEMPT** | Histórico | metadado de UX, não PII | `candidates_search.py:53` |
| 16 | Buscas Salvas **client-side**, sem share entre users, sem alertas | Buscas Salvas | limitação atual (→ §19) | `talent-funnel-store.ts:24-40` |
| 17 | Listas: Pundit por `account_id`; **soft-delete**; dedup membros | Listas | colaboração tenant-wide | `candidate_list_repository.py:125,198` |
| 18 | Assign-to-jobs cria `VacancyCandidate` (stage `sourcing`) | Listas | entra no funil da vaga | `candidate_list_repository.py:274-275` |
| 19 | Add de perfil externo → **`ConvertToCandidateJob`** | Listas | perfil externo vira Candidate | `list_relationship_job.rb` |
| 20 | Compartilhar via **token** (`SharedSearch`) | Listas/Share | acesso por link | `shared_search.rb:27` |
| 21 | Favoritos **per-user**, `UniqueConstraint(candidate_id,user_id)`, pin primeiro | Favoritos | marcador privado | `candidate_favorites_repository.py:72,84` |
| 22 | Assistência: **só o ghost text (`enhance-prompt`) usa LLM**; autocomplete/tags/completude são **determinísticos** (dicionário/regex/contagem) | Busca Natural | matar a suposição de "tudo é IA preditiva" | `search_assistant.py:345,494`, `misc_search.py:291` |
| 23 | **BARS/rubric só com `job_id`/JD** (Match 0–99, cap 99); não roda na busca textual/semântica nem no WSI | Ranking (JD) | escopo correto do rubric | `rubric_evaluation_service.py` |
| 24 | **Like/Dislike calibra o ranking** (+2.5/−2.5, cap ±5) + loop adaptativo (pesos ±30%); ancorado por **fingerprint** | Resultados/Ranking | feedback do recrutador re-pondera busca | `lia_score_service.py`, `search_feedback.py` |
| 25 | Feedback de busca: **toggle por `user_id+candidate_id+job_id`**, re-hidratação por `user_id+fingerprint`; RLS por `company_id` | Resultados | sinal por candidato, reapresentado por contexto | `search_feedback.py:48-101`, migrações 222/225 |

## 18. Checklist de replicação em outro ambiente

1. **PostgreSQL + `pgvector`** habilitado; colunas de embedding nas tabelas de candidato.
2. **Elasticsearch** provisionado e índice populado (full-text + `favorite_user_ids`).
3. **Migrations:** `candidate_searches` (+ `discarded_candidates` JSONB), `candidate_lists` + `candidate_list_members`, `candidate_favorites`, array `favorite_user_ids` (Rails).
4. **Secrets:** `PEARCH_API_KEY`, `APIFY_API_KEY`, integração Gemini; definir `APIFY_SEARCH_FALLBACK_ENABLED`.
5. **Proxy Next.js** `/api/backend-proxy/*` → `/api/v1/*` (com repasse de cookies httpOnly).
6. **Backend:** routers `candidate_search`, `search_assistant`, `voice`, `candidate_lists`, `candidates_metadata`.
7. **Frontend:** `candidates-page.tsx` como entry único + hooks/stores da §15.
8. **Tenancy:** `company_id` do JWT filtra tudo; `candidate_searches` permanece RLS-EXEMPT (per-user); aplicar "Rule Zero" em todo repo.
9. **Regras de negócio (§17):** decidir conscientemente sobre cada uma — em especial #2 (saldo insuficiente), #6 (descartados) e #7 (FairnessGuard).
10. **Validar fluxos:** rodar os 5 tipos em Local; depois Híbrida/Global com créditos de teste; smoke de voz (`voice/transcribe` → texto via Gemini).

## 19. Gaps & pontos de atenção

- 🔴 **Histórico e Buscas Salvas são client-side** (`localStorage`): não sincronizam entre dispositivos/usuários, somem ao limpar o navegador, limite 100. **→ Próxima tarefa: migrar para persistência no backend.**
- 🟡 **Buscas Salvas sem alertas/agendamento** — só re-execução manual (oportunidade de produto).
- 🟡 **Persistência dupla (Rails + Python)** para Listas/Favoritos — risco de divergência; definir a fonte-da-verdade ao replicar.
- 🟡 **`search_pearch` default `false`** no lib (`candidate-search.ts:234`) — Híbrida/Global precisam ligar explicitamente, senão a busca vira Local silenciosamente.
- 🟡 **Saldo insuficiente não bloqueia** (#2): replicar isso significa aceitar custo de fornecedor não debitado — decida a política.
- 🟡 **Tamanho da base Pearch inconsistente:** UI afirma **800M+** (`SSIModeNatural.tsx:185-186`), log de health cita **190M+** (`candidates_search.py:216`). Alinhar a fonte do número.
- 🟡 **Autocomplete parece "IA preditiva", mas é determinístico** (dicionário/prefixo, §4.1.1). A UI sugere inteligência contextual; na prática só o ghost text (`enhance-prompt`) usa LLM. Decidir se a expectativa de produto bate com a implementação (ou investir em autocomplete realmente contextual).
- 🟡 **Dupla implementação de serviços** — alguns serviços têm cópia em `app/shared/services` (shim) e a implementação real em `app/domains/*/services` (ex.: `ml_feedback_service` → `app/domains/analytics/services`; padrão similar em `cv_screening`). Definir a **fonte-da-verdade** ao replicar para não portar o shim achando que é a lógica.
- 🟡 **Feedback de busca: toggle por candidato, re-hidratação por fingerprint** (§5.8.4) — chaves diferentes. Um like dado numa busca aparece re-hidratado **só** em buscas com o **mesmo fingerprint** (mesmos critérios); mudou o filtro, muda o fingerprint e o like não reaparece (embora continue gravado por candidato). Confirmar se é o comportamento desejado de produto.
- 🟢 **LinkedIn ≠ fonte selecionável:** é Apify por baixo, só como fallback de circuit breaker.
- 🟢 **`candidate_searches` é RLS-EXEMPT** (metadado per-user) — intencional; confirme que os candidatos apontados continuam guardados por `company_id`.

---

*Documento de handoff — escopo: tipos de busca + abas de gestão (Histórico, Buscas Salvas, Listas, Favoritos), agora com regras de negócio detalhadas por funcionalidade (§4.6, §5.7, §6.1, §7.1, §8.1, §9.1), a mecânica determinística-vs-LLM da camada de assistência (§4.1.1), o pipeline de ranking ponta-a-ponta com parâmetros reais (§11), o Like/Dislike (Search Feedback, §5.8) e o quadro-resumo consolidado (§17). Banco de Talentos será adicionado quando finalizado.*
