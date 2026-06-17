# ADR-017: Modelo de dados do WSI Voice Screening — quem é fonte de verdade

**Status:** Accepted
**Data:** 2026-04-18
**Relacionado:** Auditoria `.local/audit/wsi-screening-e2e-report.md` rev. 5 (P2-2), ADR-016, `database/wsi_schema_corrected.sql`, `database/wsi_schema.sql`

---

## Contexto

Após a remoção do legado OpenMic.ai + Deepgram (auditoria P0-4, 2026-04-18), o pipeline canônico de screening por voz é Twilio Programmable Voice + Gemini Live Audio, orquestrado por `app/domains/voice/services/voice_screening_orchestrator.py`. Sobraram, no banco e nos modelos ORM, **quatro tabelas/grupos de tabelas** que parecem cobrir a mesma jornada e geraram dúvida recorrente sobre "qual delas é a verdade":

| # | Tabela / agregado | Schema | Origem | O que armazena hoje |
|---|---|---|---|---|
| 1 | `wsi_sessions` + `wsi_questions` + `wsi_response_analyses` | `database/wsi_schema_corrected.sql` (canônico — substitui o `wsi_schema.sql` antigo, ainda mantido por compatibilidade de migrations históricas) | Sessão de entrevista WSI **enquanto está acontecendo** | Estado da sessão (status, contexto, configuração da rubrica usada), as N perguntas geradas/usadas, e a análise pergunta-a-pergunta (transcrição, autodeclaração, contexto, Bloom, Dreyfus, gaps). É o que o orquestrador escreve em tempo real. |
| 2 | `wsi_results` | schema: `database/wsi_schema_corrected.sql:65`; ORM: `app/domains/cv_screening/services/wsi_service/models.py` | Resultado final agregado por candidato/vaga | Score WSI consolidado: `technical_wsi`, `behavioral_wsi`, `overall_wsi` (DECIMAL(3,2), CHECK 1–5 — escala atual; ver M16/§17 para migração 0–10), `classification`, `percentile`, `candidate_id`, `job_vacancy_id`. É o que `WSIScoreCalculator` produz no fim do pipeline e o que o restante da plataforma (kanban, comunicação, reports) consome. |
| 3 | `voice_screening_calls` (+ `voice_screening_analyses` 1:1) | `libs/models/lia_models/voice_screening.py` | Camada de telefonia Twilio (legado, nome herdado da era OpenMic) | Metadata bruta da chamada: `call_id` (string Twilio CallSid), `agent_id`, `call_type`/`call_status`/`direction`, `from_number`/`to_number`, `start_timestamp`/`end_timestamp`/`duration_seconds`, `transcript` + `transcript_object`, `webhook_event`/`webhook_timestamp`/`webhook_payload`, `processing_status`. **Não tem score WSI consolidado nem rubric**. **Não tem FK direta para `wsi_sessions`** — é uma store autônoma de chamadas, ligada à entrevista WSI apenas via `candidate_id`/`job_title` (lookup soft). |
| 4 | `wsi_async_session_*` (`wsi_async_session_service.py`) | `app/domains/cv_screening/services/wsi_async_session_service.py` | Sessão WSI **assíncrona** (texto / WhatsApp, sem voz) | Variante para candidatos que respondem por chat ao invés de voz. Reusa `wsi_response_analyses`/`wsi_results` para análise e score; só substitui a captura. |

A confusão histórica vem do fato de o ADR original do WSI ter sido escrito quando só existia (1) e (2), e (3) ter sido criada depois junto com a integração Twilio sem documentar a fronteira. Após a remoção do OpenMic havia risco real de alguém deduzir que (1) ou (3) deveria virar a "tabela única" e quebrar consumidores.

## Decisão

Cada uma das quatro peças tem responsabilidade **diferente** e nenhuma é redundante das outras. A fronteira fica explicitada assim:

### 1. `wsi_sessions` + `wsi_questions` + `wsi_response_analyses` — **estado mutável da sessão WSI**

São o "diário de bordo" da entrevista. Ownership: `app/domains/cv_screening/services/wsi_async_session_service.py` (modo texto) e `app/domains/voice/services/voice_screening_orchestrator.py` (modo voz). São **mutáveis durante a sessão** (status muda, perguntas são adicionadas, análises chegam pergunta-a-pergunta), e ficam **append-only** depois que a sessão é fechada (`status='completed'`).

A coluna que diferencia voz de texto é `wsi_sessions.screening_type` com `CHECK (screening_type IN ('voice', 'chat', 'hybrid'))`.

Quem consome: o próprio orquestrador (para decidir a próxima pergunta), o HITL service (para revisão humana de respostas suspeitas), e o `WSIScoreCalculator` (que lê todas as `wsi_response_analyses` da sessão para produzir `wsi_results`).

### 2. `wsi_results` — **resultado final, um por sessão**

Score WSI consolidado de uma sessão fechada. Ownership: `WSIScoreCalculator` (escrita única no fim do pipeline). A FK `wsi_results.session_id` é `UNIQUE` — **existe no máximo um `wsi_results` por `wsi_sessions`**. Recalibração hoje é **UPDATE in-place** (não há coluna `version` nem snapshot histórico); para o consumidor downstream, vale tratar a linha como "a única verdade atual" daquela sessão. Se precisarmos de versionamento auditável (snapshots imutáveis por re-cálculo), é mudança de schema explícita — ver M09/M16/§17 da auditoria.

Colunas-chave (todas em escala 1–5 hoje, alvo 0–10 em §17): `technical_wsi`, `behavioral_wsi`, `overall_wsi`, `classification`, `percentile`, `candidate_id`, `job_vacancy_id`.

Quem consome: kanban (`overall_wsi`), comunicação (evidências citáveis nos templates), analytics/benchmark (agregação por setor), DSR/LGPD export. Esta é a **única tabela** que sai do domínio voice/cv_screening — nenhum consumidor de fora deve ler `wsi_response_analyses` ou `wsi_sessions` direto.

### 3. `voice_screening_calls` (+ `voice_screening_analyses`) — **store autônoma de chamadas Twilio**

"Envelope" da ligação Twilio: `call_id` (string CallSid), `agent_id`, status/duração, transcript bruto e structured (`transcript_object`), `webhook_payload` completo para auditoria. Ownership: `app/domains/voice/services/voice_service.py` (callback Twilio). **Não tem FK direta para `wsi_sessions`** — é store autônoma anterior à integração WSI, hoje ligada à entrevista por `candidate_id` + `job_title` (lookup soft no Twilio Voice service).

`voice_screening_analyses` é 1:1 com `voice_screening_calls` (FK `screening_call_id UNIQUE`) e guarda análise IA própria (`basic_overall_score 0-100`, `tech_*`, `analysis_model`) — distinta do score WSI canônico, é uma análise tática "dessa chamada específica" usada para review rápido na página da chamada.

Quem consome: billing (duração agregada Twilio), observabilidade (taxa de drop), runbook de incidente (rastrear `call_id` quando o candidato reclama), e a página de review de chamada individual.

> **Nome herdado:** "voice_screening_calls" e o `agent_id` foram criados na era OpenMic e mantidos por compat de schema/migrations. Hoje `agent_id` é nullable e o store é Twilio-only. Renomeá-los seria mudança destrutiva e não é prioridade (M15 fechou a parte mais visível canonicalizando o comentário de `response_audio_url`).

### 4. `wsi_async_session_*` — **variante texto (sem telefonia)**

Reusa `wsi_response_analyses` e `wsi_results`; substitui apenas a camada de captura (chat / WhatsApp ao invés de Twilio + Gemini Live). Ownership: `app/domains/cv_screening/services/wsi_async_session_service.py`. Não cria nem usa `voice_screening_calls` (não houve ligação). A sessão correspondente em `wsi_sessions` tem `screening_type='chat'`.

### Regra de ouro para novos consumidores

| Quero saber… | Leia… |
|---|---|
| Score WSI consolidado de um candidato/vaga | `wsi_results` (sempre — um por `wsi_sessions.id`) |
| Pergunta exata e resposta da entrevista | `wsi_response_analyses` (via `session_id`) |
| Status atual de uma entrevista em andamento | `wsi_sessions.status` |
| Se o candidato respondeu por chat ou voz | `wsi_sessions.screening_type` (`'voice'` \| `'chat'` \| `'hybrid'`) |
| Metadata bruta de uma chamada Twilio | `voice_screening_calls` (via `call_id` ou `candidate_id` + `job_title`) |
| Análise IA "dessa chamada" para review rápido | `voice_screening_analyses` (via `screening_call_id`) |

Nenhum consumidor de fora dos domínios `voice` e `cv_screening` deve fazer JOIN entre essas tabelas — sempre passe pelos services dos domínios donos.

## Consequências

- **Positivas:** fronteira documentada; novos integradores não precisam mais perguntar "qual tabela usar"; `WSIScoreCalculator` permanece como única porta de escrita de `wsi_results`; remoção do OpenMic não derrubou nenhum consumidor downstream porque (2) é a fonte estável.
- **Riscos remanescentes:** (a) `voice_screening_calls`↔`wsi_sessions` é *soft link* por `candidate_id`+`job_title` — é frágil para casos de candidato com várias vagas no mesmo período; melhoria é adicionar `wsi_session_id UUID NULL` na tabela em PR futuro. (b) O legado `database/wsi_schema.sql` (sem o `_corrected`) ainda está em disco para compatibilidade com migrations históricas; todo schema novo deve referenciar `wsi_schema_corrected.sql`. (c) `wsi_results` faz UPDATE in-place na recalibração — adicionar versionamento explícito é trabalho separado (ver `M16` na auditoria).
- **Quem precisa saber:** times de Kanban, Comunicação, Analytics e DSR. Já estão consumindo `wsi_results` corretamente; este ADR só consolida o contrato.

## Referências

- Auditoria E2E: `.local/audit/wsi-screening-e2e-report.md` rev. 5
- Schemas SQL: `lia-agent-system/database/wsi_schema_corrected.sql` (canônico), `wsi_schema.sql` (legado, somente migrations)
- ORM: `lia-agent-system/lia_models/wsi_result.py`, `lia_models/voice_screening.py`
- Orquestrador: `app/domains/voice/services/voice_screening_orchestrator.py`
- Calculator: `app/domains/cv_screening/services/wsi_score_calculator_v2.py`
