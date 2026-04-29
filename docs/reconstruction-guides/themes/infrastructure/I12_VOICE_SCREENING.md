# Theme I12 — Voice Screening — Infrastructure Layer

**Layer:** Infrastructure  |  **Última verificação de código:** 2026-04-24
**Fontes:** `app/domains/voice/`, `app/api/v1/voice.py`, `app/api/v1/gemini_voice.py`, `app/api/v1/twilio_voice.py`, `app/domains/cv_screening/services/wsi_voice_orchestrator.py`

---

## O que é este tema

O Voice Screening é a infraestrutura de **entrevistas de triagem via voz** da LIA. O sistema suporta dois pipelines independentes que chegam ao mesmo resultado (transcrição + scoring WSI):

- **Pipeline A — Twilio PSTN:** chamada telefônica outbound para o celular do candidato. Usa Gemini Flash 2.5 para STT + conversação e OpenAI TTS (voz "nova") para resposta. Custo ~US$0.41/entrevista de 15 min.
- **Pipeline B — Gemini Live Audio (VoIP):** sessão de áudio em tempo real via WebSocket no browser. O Gemini Live processa STT + LLM + TTS de forma nativa. Custo ~US$0.065/entrevista de 15 min.

Ambos os pipelines integram com o subsistema **WSI** (Workplace Skills Index) para geração de perguntas e scoring pós-chamada (Bloom/Dreyfus por pergunta). O LGPD impõe um **hard-block HTTP 451** antes de qualquer chamada se o consentimento do candidato estiver ausente, revogado, ou se o banco de dados estiver indisponível.

**Boundary com temas irmãos:**
- **P5 Wizard WSI** — gera as perguntas WSI usadas neste pipeline (F1-F6); I12 consome as perguntas geradas
- **C2 LGPD PII** — `strip_pii_for_llm_prompt()` + `mask_pii()` aplicados em todos os segmentos de transcrição
- **C1 Fairness** — FairnessGuard L1+L2 em cada resposta da LIA durante a chamada
- **C4 LGPD Art. 20** — `transparency_extras` JSONB + `response_hash` (EU AI Act Art. 12)
- **R1 Circuit Breakers** — `TWILIO_VOICE_CIRCUIT` + `GEMINI_LIVE_CIRCUIT` protegem ambos os pipelines

---

## Arquivos conectados (13 total)

### Camada Código (13 arquivos Python)

| Arquivo | Path canônico | Linhas | Responsabilidade |
|---------|--------------|:---:|-----------------|
| `voice_screening_orchestrator.py` | `app/domains/voice/services/voice_screening_orchestrator.py` | 1695 | Orquestrador principal: sessões PSTN + VoIP, LGPD consent check, FairnessGuard, WSI scoring |
| `wsi_voice_orchestrator.py` | `app/domains/cv_screening/services/wsi_voice_orchestrator.py` | 802 | Metodologia WSI: perguntas → Q/A extraction → Bloom/Dreyfus scoring → eventos |
| `gemini_live_audio_service.py` | `app/domains/voice/services/gemini_live_audio_service.py` | 391 | Sessões Gemini Live Audio (VoIP): lifecycle, system prompt, FairnessGuard por turno |
| `gemini_voice_service.py` | `app/domains/voice/services/gemini_voice_service.py` | 328 | Gemini Flash 2.5 STT standalone (não streaming): transcrição + análise |
| `voice_service.py` | `app/domains/voice/services/voice_service.py` | 334 | OpenAI Whisper STT (legado) + OpenAI TTS (nova voice, usado no PSTN) |
| `voice_screening_analysis.py` | `app/domains/voice/services/voice_screening_analysis.py` | 154 | Análise LLM standalone (fallback do WSIVoiceOrchestrator) |
| `wsi_repository.py` | `app/domains/voice/repositories/wsi_repository.py` | 710 | DAL: `wsi_sessions`, `wsi_questions`, `wsi_responses`, `wsi_response_analyses`, `wsi_results` |
| `voice.py` | `app/api/v1/voice.py` | 235 | REST: transcrição + análise de arquivo de áudio via Gemini STT |
| `gemini_voice.py` | `app/api/v1/gemini_voice.py` | 758 | WebSocket + REST para Gemini Live Audio (VoIP) |
| `twilio_voice.py` | `app/api/v1/twilio_voice.py` | 779 | TwiML webhooks + REST para Twilio PSTN + token VoIP |
| `__init__.py` | `app/domains/voice/__init__.py` | 5 | Package init |
| `services/__init__.py` | `app/domains/voice/services/__init__.py` | 0 | Package init |
| `repositories/__init__.py` | `app/domains/voice/repositories/__init__.py` | 0 | Package init |

### Integration points

- **P5 Wizard WSI** → `_generate_and_store_wsi_questions()` chama `WSIService.generate_screening_questions()` do cv_screening domain
- **C1 Fairness** → `check_fairness()` de `app.shared.compliance.fairness_guard_middleware` chamado em 4 pontos diferentes do pipeline
- **C2 LGPD PII** → `strip_pii_for_llm_prompt()` + `mask_pii()` de `app.shared.pii_masking`
- **C3 LGPD Consent** → `ConsentCheckerService.check_candidate_consent(purpose="ai_screening")` hard-block
- **R1 Circuit Breakers** → `TWILIO_VOICE_CIRCUIT` + `GEMINI_LIVE_CIRCUIT` de `app.shared.resilience.circuit_breaker`
- **I4 LLM Providers** → `get_gemini_client_for_tenant(company_id)` de `app.shared.tenant_llm_context` (BYOK)
- **I9 Data Layer** → tabelas `wsi_sessions`, `wsi_questions`, `wsi_responses`, `wsi_response_analyses`, `wsi_results`
- **C7 Audit Trail** → `response_hash` via `hash_response()` de `app.shared.security.wsi_hashing`

---

## Lógica IN → OUT

### Pipeline A — Twilio PSTN

#### Input
```
POST /api/v1/twilio-voice/initiate
{
    "candidate_id": str,
    "candidate_name": str,
    "phone_number": str,    # formato E.164 (+55...)
    "job_id": str | None,
    "job_title": str,
    "language": str         # default "pt-BR"
}
Authorization: Bearer <JWT com company_id>
```

#### Processing
```
1. verify_consent(candidate_id, company_id, db)
   → ConsentCheckerService.check_candidate_consent(purpose="ai_screening")
   → HTTP 451 se ausente/revogado/DB indisponível

2. TWILIO_VOICE_CIRCUIT.call(twilio_voice_service.make_call)
   → outbound call para phone_number
   → retorna call_sid

3. INSERT wsi_sessions + INSERT wsi_questions (via WSIVoiceOrchestrator)

4. Twilio chama POST /twilio-voice/greeting
   → TwiML: Say(greeting) + Gather(speech, action=/consent-response)

5. POST /twilio-voice/consent-response
   → _parse_consent_speech(): negative-intent precedence
     (qualquer token de negação → deny; ambíguo → deny / LGPD-safe default-deny)
   → YES: TwiML Connect Stream /twilio-voice/audio-stream
   → NO: TwiML Say goodbye; session.status = "declined"

6. WS /twilio-voice/audio-stream (Twilio Bidirectional Media Streams)
   → event=start: bind call_sid; status="in_progress"; persist
   → event=media: buffer (threshold 8000 bytes)
     → process_audio_chunk: μ-law → WAV → Gemini Flash 2.5 STT
     → generate_lia_response: system_prompt (job + WSI questions) + Gemini Flash 2.5 (temp=0.7)
     → FairnessGuard L1+L2 em toda resposta
     → synthesize_lia_response: OpenAI TTS "nova" → MP3 → mp3_to_mulaw → stream
     → persist every 2 turns
   → event=stop: flush buffer; persist

7. POST /twilio-voice/status (CallStatus=completed)
   → finalize_screening(session_id, db)
     → merge transcript → mask_pii
     → WSIVoiceOrchestrator.process_call_completed() [primary]
     → analyze_voice_screening() [fallback]
     → session.status = "completed"
```

#### Output
```python
# /twilio-voice/initiate retorna:
{"session_id": str, "call_sid": str, "status": "initiated" | "fallback" | "failed"}

# Após finalização (via /sessions/{session_id}):
{"session_id": str, "status": "completed", "wsi_result": {...}, "transcript": [...]}
```

---

### Pipeline B — Gemini Live Audio (VoIP)

#### Input
```
POST /api/v1/gemini-voice/start-session
{
    "candidate_id": str,
    "candidate_name": str,
    "job_id": str | None,
    "job_title": str,
    "language": str
}
Authorization: Bearer <JWT com company_id>
```

#### Processing
```
1. verify_consent → HTTP 451 se não concedido

2. GEMINI_LIVE_CIRCUIT check
   → se open → status="fallback", fallback_channel="twilio"

3. GeminiLiveAudioService.create_session()

4. fetch job_context from DB (company_id-filtered)

5. INSERT wsi_sessions
   → retorna {session_id, ws_token, status="ready"}
   → ws_token = HMAC-SHA256(SECRET_KEY, f"{session_id}:{company_id}:{candidate_id}")[:32]

6. WS /gemini-voice/live-stream?session_id=...&ws_token=...
   → validate ws_token (HMAC); close code 4401 se inválido
   → build_system_prompt (job + WSI questions + FairnessGuard + anti-sycophancy)
   → create_live_connection_config (model="gemini-2.5-flash", voice="Aoede", temp=0.7)
   → client.aio.live.connect(model, config) → gemini_session

   Tarefas em paralelo:
   a) receive_from_gemini():
      → audio chunks → send para browser (base64 PCM)
      → text transcripts → process_lia_text() → FairnessGuard
      → turn_complete: suprime áudio se FairnessGuard bloqueou
   b) browser → server:
      → {"type":"audio", "data": "<base64_pcm_16khz>"} → gemini_session.send(LiveClientRealtimeInput)
      → {"type":"text", ...} → gemini_session.send
      → {"type":"end"} → close

7. [finally] finalize_session() → WSI scoring (mesmo que PSTN)
```

#### Output
```json
// WebSocket server → browser
{"type": "audio", "data": "<base64_pcm>", "mime_type": "audio/pcm"}
{"type": "transcript", "role": "candidate"|"lia", "text": "..."}
{"type": "status", "status": "connected"|"in_progress"|"ended"|"timeout"|"error"}
{"type": "metrics", "latency_ms": 123, "tokens": {"input": N, "output": N}}
```

### Escalation / HITL

- **Consentimento negado durante a chamada PSTN:** Twilio encerra a chamada; `session.status = "declined"`. Nenhuma transcrição é armazenada.
- **FairnessGuard bloqueia resposta da LIA:** retorna fallback neutro: `"Poderia me contar mais sobre sua experiência profissional e como ela se relaciona com esta vaga?"` — chamada continua.
- **Circuit breaker aberto (PSTN):** `status="fallback"`, retorna `error="use chat/WhatsApp fallback"` — chamador deve redirecionar.
- **Circuit breaker aberto (VoIP):** `fallback_channel="twilio"` — frontend deve oferecer alternativa.

---

## Componentes Críticos

### VoiceScreeningSession — Dataclass

```python
# app/domains/voice/services/voice_screening_orchestrator.py
@dataclass
class VoiceScreeningSession:
    session_id: str
    candidate_id: str
    candidate_name: str
    job_title: str
    company_id: str
    phone_number: str           # "voip" para chamadas browser
    job_id: str | None
    call_sid: str | None        # Twilio call SID
    status: str = "pending"     # pending/initiated/in_progress/analyzing/completed/failed/fallback/declined
    language: str = "pt-BR"
    transcript_segments: list[dict]
    questions_asked: list[str]
    started_at: datetime | None
    ended_at: datetime | None
    wsi_result: dict | None
    error: str | None
    consent_verified: bool
    job_context: dict | None
    presentation_done: bool
    voice_provider: str = "twilio"   # "twilio" | "gemini_live" | "fallback"
```

### GeminiLiveSession — Dataclass

```python
# app/domains/voice/services/gemini_live_audio_service.py
@dataclass
class GeminiLiveSession:
    session_id: str
    candidate_id, candidate_name, job_title, company_id, job_id: str
    language: str = "pt-BR"
    status: str = "pending"
    voice_provider: str = "gemini_live"
    started_at, ended_at: datetime | None
    transcript_segments: list[dict]     # {"text", "timestamp", "role"}
    questions_asked: list[str]
    token_usage: {"input": int, "output": int}
    turn_latencies_ms: list[float]
    error: str | None
    consent_verified: bool
    job_context: dict | None
    presentation_done: bool

SESSION_TIMEOUT_SECONDS = 1200     # 20 minutos
MAX_TURN_TOKENS = 500
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
```

### Perguntas de Triagem (Fallback Scriptado — PSTN)

```python
SCREENING_QUESTIONS_PT = [
    "Pode me contar brevemente sobre sua experiência profissional mais recente?",
    "Por que você tem interesse nessa posição?",
    "Quais são suas principais habilidades técnicas relevantes para essa vaga?",
    "Como você prefere trabalhar: em equipe ou de forma mais independente?",
    "Qual sua disponibilidade de início? Está aberto a mudanças ou trabalho remoto?",
]
# Usado quando: WSI question generation falha OU job_id é None
```

### Prioridade de Geração de Perguntas

```
1. Versioned question set  → screening_question_set_service.get_active_version(db, job_vacancy_id)
2. Dynamic WSI             → WSIService.generate_screening_questions(competencies, mode="compact")
   Competências default: Experiência Relevante (0.30), Resolução de Problemas (0.25),
                          Comunicação (0.20), Trabalho em Equipe (0.15), Adaptabilidade (0.10)
3. Gemini autonomous       → sem perguntas armazenadas; Gemini gera ao vivo (STAR methodology)
```

---

## API Endpoints

### REST — Áudio Standalone (Gemini STT)

| Método | Path | Descrição |
|--------|------|-----------|
| `GET` | `/api/v1/voice/health` | Health check (Gemini Flash 2.5 configurado?) |
| `POST` | `/api/v1/voice/transcribe` | STT de arquivo; params: `audio` (file), `language` (form, default pt-BR), `prompt` (form, opcional) |
| `POST` | `/api/v1/voice/analyze` | Análise de áudio; `analysis_type`: full/sentiment/topics/summary |
| `POST` | `/api/v1/voice/interview` | Análise completa de entrevista; params: `audio`, `job_title`, `questions` |

### REST + WebSocket — Gemini Live Audio (VoIP)

| Método | Path | Descrição |
|--------|------|-----------|
| `POST` | `/api/v1/gemini-voice/start-session` | Cria sessão VoIP; valida consent; retorna `session_id`, `ws_token`; rate limit 5/min/IP |
| `WS` | `/api/v1/gemini-voice/live-stream` | Áudio bidirecional; query params: `session_id`, `ws_token`; max 3 concurrent/IP |
| `GET` | `/api/v1/gemini-voice/session/{session_id}` | Status da sessão + resultado WSI |
| `GET` | `/api/v1/gemini-voice/health` | Estado circuit breaker, disponibilidade, custo |

### REST + WebSocket + TwiML — Twilio PSTN

| Método | Path | Descrição |
|--------|------|-----------|
| `POST` | `/api/v1/twilio-voice/initiate` | Inicia chamada outbound; valida consent; retorna `session_id`, `call_sid` |
| `POST` | `/api/v1/twilio-voice/greeting` | TwiML: saudação + Gather de consentimento (valida `X-Twilio-Signature`) |
| `POST` | `/api/v1/twilio-voice/consent-response` | TwiML: parse YES/NO; negative-intent precedence |
| `WS` | `/api/v1/twilio-voice/audio-stream` | Twilio Bidirectional Media Streams; buffer 8000 bytes |
| `POST` | `/api/v1/twilio-voice/status` | Webhook de status Twilio; dispara `finalize_screening()` em `completed` |
| `POST` | `/api/v1/twilio-voice/end-call/{session_id}` | Encerramento programático |
| `GET` | `/api/v1/twilio-voice/sessions/{session_id}` | Status + resultado WSI |
| `POST` | `/api/v1/twilio-voice/voip-token` | Gera Twilio Access Token para VoIP browser (Twilio Client SDK); 1h expiry |
| `POST` | `/api/v1/twilio-voice/voip-connect` | TwiML webhook para VoIP browser → audio-stream |
| `GET` | `/api/v1/twilio-voice/health` | Status Twilio config, VoIP disponível, canais fallback |

---

## Configuração — Variáveis de Ambiente

### Twilio (Pipeline PSTN)

| Variável | Descrição |
|----------|-----------|
| `TWILIO_ACCOUNT_SID` | Account SID do Twilio |
| `TWILIO_AUTH_TOKEN` | Auth Token (validação de assinatura de webhook) |
| `TWILIO_VOICE_NUMBER` | Número de voz Twilio (E.164, ex: `+5511XXXXX`) |
| `TWILIO_TWIML_APP_SID` | TwiML App SID (obrigatório para VoIP browser / Twilio Client SDK) |
| `APP_BASE_URL` | URL pública para callbacks TwiML (ex: `https://staging2.wedotalent.cc`) |

**Fallback:** quando não configurado → `TwilioVoiceUnconfiguredError` → `status="fallback"` com `error="use chat/WhatsApp fallback"`.

### Gemini (Pipeline VoIP + STT)

| Variável | Descrição |
|----------|-----------|
| `AI_INTEGRATIONS_GEMINI_API_KEY` | API key Gemini (também verifica disponibilidade do VoIP) |
| `AI_INTEGRATIONS_GEMINI_BASE_URL` | Base URL via Replit AI Integrations |

**Fallback:** ausência de qualquer uma → `GeminiLiveAudioService.is_available()` retorna False.

### OpenAI (TTS para PSTN + Whisper legado)

| Variável | Descrição |
|----------|-----------|
| `AI_INTEGRATIONS_OPENAI_API_KEY` | Chave primária (verificada primeiro) |
| `OPENAI_API_KEY` | Chave fallback |

### Segurança

| Variável | Descrição |
|----------|-----------|
| `SECRET_KEY` | Segredo HMAC para assinatura do WebSocket token (Pipeline Gemini Live) |
| `APP_SECRET_KEY` | Nome alternativo para o mesmo segredo |

> **Gotcha:** se nenhum dos dois estiver definido, `start-session` cria sessão mas `live-stream` falha com `RuntimeError` na validação do token.

---

## Compliance e Fairness

### LGPD

| Artigo | Implementação | Arquivo |
|--------|--------------|---------|
| Art. 7 — Consentimento | `verify_consent()` hard-block antes de qualquer chamada; HTTP 451 se ausente/revogado/DB indisponível | `voice_screening_orchestrator.py` |
| Art. 12 — Minimização | `strip_pii_for_llm_prompt()` antes de análise LLM; `mask_pii()` antes de logging | `voice_screening_orchestrator.py` |
| Art. 18 — Revogação | Consentimento revogado = mesmo tratamento que ausente (hard-block, sem soft-warning) | `voice_screening_orchestrator.py` |
| Art. 20 — Explicabilidade | `transparency_extras` JSONB em cada `wsi_response_analyses`; `response_hash` para rastreabilidade | `wsi_repository.py` |

**Consent Parsing — Negative-Intent Precedence:**
```python
# tokens de negação: "nao", "no", "nunca", "jamais", "recuso", "nego", "discordo", "nope", "negativo"
# Qualquer token de negação em QUALQUER posição da frase → deny
# Ambíguo → deny (LGPD-safe default-deny)
```

### Fairness (FairnessGuard L1+L2)

FairnessGuard é chamada em **4 pontos** do pipeline:

| Ponto | Arquivo | Trigger |
|-------|---------|---------|
| `GeminiLiveAudioService.process_lia_text()` | `gemini_live_audio_service.py` | Cada utterance da LIA no VoIP |
| `VoiceScreeningOrchestrator.generate_lia_response()` | `voice_screening_orchestrator.py` | Após cada resposta Gemini Flash PSTN |
| `VoiceScreeningOrchestrator._check_fairness_on_response()` | `voice_screening_orchestrator.py` | Perguntas scriptadas/fallback |
| `gemini_live_stream_websocket` on `turn_complete` | `gemini_voice.py` | Cada turno completo VoIP |

**Categorias proibidas (no system prompt):**
- Idade, data de nascimento, geração
- Gênero, identidade de gênero, orientação sexual
- Raça, cor, etnia, naturalidade
- Estado civil, filhos, gravidez, planos de família
- Religião, crenças, filiação política ou sindical
- Condições de saúde, deficiências, uso de medicamentos
- Situação financeira pessoal, endereço residencial
- Aparência física, peso, altura

**Fallback quando bloqueado:**
```
"Poderia me contar mais sobre sua experiência profissional e como ela se relaciona com esta vaga?"
```

### EU AI Act (Art. 12) — Audit Trail

```sql
-- response_hash obrigatório e NOT NULL em ambas as tabelas:
wsi_responses.response_hash          TEXT NOT NULL
wsi_response_analyses.response_hash  TEXT NOT NULL
wsi_response_analyses.transparency_extras  JSONB  -- degraded_quality, layer2_degraded_reason

-- Computação do hash:
hash_response(response_text, session_id, question.id)  -- app.shared.security.wsi_hashing
-- Falha no INSERT propaga (FAIL-FAST) — audit trail não pode ser descartado silenciosamente
```

---

## Recuperação de Sessão após Restart

```python
# app/domains/voice/services/voice_screening_orchestrator.py
async def get_or_restore_session(session_id, db) -> VoiceScreeningSession | None:
    # 1. Tenta memória (_sessions dict)
    # 2. Fallback: wsi_sessions.voice_session_state (JSONB) → deserializa via _state_to_session()

# Persiste em:
# - Após initiate_call() bem-sucedido
# - A cada 2 turnos durante audio stream
# - No stop/disconnect do stream
# - Após presentation_done transition
```

---

## Instruções para Claude Code / Cursor

### "Implementa Voice Screening no v5"

**Passo 1 — Dependências**
```bash
pip install twilio google-generativeai openai audioop pydub
# Configurar variáveis de ambiente (ver seção de config)
```

**Passo 2 — Estrutura de domínio**
```bash
# Criar app/domains/voice/ com:
# services/voice_screening_orchestrator.py  ← principal
# services/gemini_live_audio_service.py     ← VoIP
# services/gemini_voice_service.py          ← STT standalone
# services/voice_service.py                 ← TTS + Whisper legado
# services/voice_screening_analysis.py      ← análise fallback
# repositories/wsi_repository.py            ← DAL WSI tables
```

**Passo 3 — Consent check (P0)**
```python
# Antes de QUALQUER chamada — nunca pular:
consent_ok = await consent_checker.check_candidate_consent(
    candidate_id=candidate_id,
    company_id=company_id,       # sempre do JWT
    purpose="ai_screening",
    db=db
)
if not consent_ok:
    raise HTTPException(status_code=451, detail="Consent not granted")
```

**Passo 4 — Circuit breakers**
```python
# Declarar em startup:
TWILIO_VOICE_CIRCUIT = CircuitBreaker(name="twilio_voice", failure_threshold=3)
GEMINI_LIVE_CIRCUIT  = CircuitBreaker(name="gemini_live",  failure_threshold=3)
```

**Passo 5 — FairnessGuard em toda resposta LIA**
```python
result = await check_fairness(lia_response_text)
if result.is_blocked:
    return SAFE_FALLBACK_QUESTION  # nunca return None ou vazio
```

**Passo 6 — response_hash obrigatório**
```python
# Antes de persistir wsi_responses / wsi_response_analyses:
response_hash = hash_response(response_text, session_id, question.id)
# INSERT deve falhar se response_hash é None (constraint NOT NULL)
```

### Setup em CLAUDE.md (snippet)
```markdown
## Voice Screening (I12)
- Fonte: themes/infrastructure/I12_VOICE_SCREENING.md
- DOIS pipelines independentes: Twilio PSTN e Gemini Live Audio
- LGPD: verify_consent() é hard-block (HTTP 451) — NUNCA bypassar
- FairnessGuard L1+L2 em toda resposta LIA (4 pontos)
- response_hash NOT NULL (EU AI Act Art. 12) — falha se ausente
- Custos: Twilio ~$0.41/entrevista | Gemini Live ~$0.065/entrevista
- company_id sempre do JWT (multi-tenancy)
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

| Item | Flexível porque |
|------|----------------|
| Provedor TTS (OpenAI → ElevenLabs) | Interface `synthesize_speech(text) → bytes` é abstrata |
| Voz padrão ("nova" → outra) | Parâmetro de configuração |
| Threshold de buffer áudio (8000 bytes) | Parâmetro de tuning de latência |
| Número de turns no histórico de conversa (8) | Parâmetro de contexto |
| Timeout de sessão (1200s) | Operacional |
| Estratégia de persistência de sessão | Pode usar Redis em vez de JSONB se interface for preservada |

### NÃO pode adaptar

| Item | Por quê é imutável |
|------|--------------------|
| `verify_consent()` antes de QUALQUER chamada | LGPD Art. 7 + Art. 18 — sem exceção, mesmo em modo de teste |
| HTTP 451 para consentimento negado | LGPD Art. 7 — código HTTP específico para bloqueio legal |
| FairnessGuard em toda resposta LIA | NYC LL144 + CLT + Lei 9.029/95 |
| `response_hash` NOT NULL em `wsi_responses` | EU AI Act Art. 12 — audit trail imutável |
| `strip_pii_for_llm_prompt()` antes de análise LLM | LGPD Art. 12 — minimização antes do processamento |
| `mask_pii()` antes de logging | LGPD Art. 12 — dados pessoais não vão para logs |
| Negative-intent precedence no consent parsing | LGPD-safe: dúvida → negar (não o contrário) |
| `company_id` do JWT (não do payload) | Multi-tenancy (C5) |

---

## Checklist de completude

### P0 — Críticos (bloqueiam deploy)

- [ ] (P0) `verify_consent()` com HTTP 451 implementado antes de `initiate_call()` e `initiate_voip_session()`
- [ ] (P0) FairnessGuard L1+L2 chamado em toda resposta LIA (4 pontos)
- [ ] (P0) `response_hash` NOT NULL em `wsi_responses` e `wsi_response_analyses`
- [ ] (P0) `strip_pii_for_llm_prompt()` aplicado antes de qualquer análise LLM com transcrição
- [ ] (P0) `mask_pii()` aplicado antes de logging de segmentos de transcrição
- [ ] (P0) `company_id` do JWT em todas as queries (nunca do payload)
- [ ] (P0) TWILIO_VOICE_CIRCUIT + GEMINI_LIVE_CIRCUIT declarados (proteger chamadas externas)
- [ ] (P0) `voice_session_state` JSONB persistido a cada 2 turnos (recuperação de restart)

### P1 — Importantes

- [ ] (P1) Negative-intent precedence no `_parse_consent_speech()` (ambíguo → deny)
- [ ] (P1) HMAC-SHA256 `ws_token` com validação antes de aceitar WebSocket (VoIP)
- [ ] (P1) `get_or_restore_session()` com fallback para JSONB do banco
- [ ] (P1) `SCREENING_QUESTIONS_PT` como último fallback (WSI failed + job_id None)
- [ ] (P1) Prioridade de perguntas: versioned → WSI dynamic → Gemini autonomous
- [ ] (P1) `transparency_extras` JSONB com `degraded_quality` + `layer2_degraded_reason`
- [ ] (P1) `_build_job_context_summary()` limita `description` a 2000 chars (prompt budget)

### P2 — Qualidade

- [ ] (P2) `turn_latencies_ms` coletados + alerta se >500ms (`record_turn_latency`)
- [ ] (P2) `token_usage` rastreado por sessão VoIP (TokenTrackingService)
- [ ] (P2) `SESSION_TIMEOUT_SECONDS = 1200` enforced (is_session_expired)
- [ ] (P2) `list_active_sessions()` retorna lista com PII mascarado (não raw)
- [ ] (P2) `ANTI_SYCOPHANCY_OPERATIONAL` injetado no system prompt de voz

---

## Gotchas e Erros Comuns

### 1. SECRET_KEY ausente quebra WebSocket silenciosamente

```python
# A sessão é criada com sucesso (start-session), mas:
# live-stream falha com RuntimeError ao tentar validar ws_token
# Configurar SECRET_KEY ou APP_SECRET_KEY antes de testar VoIP
```

### 2. Twilio unconfigured não levanta em startup — levanta em runtime

`TwilioVoiceUnconfiguredError` é lançado somente quando `make_call()` é chamado — não no import ou na startup. O `VoiceScreeningOrchestrator` trata e retorna `status="fallback"`, mas o frontend precisa saber que deve redirecionar.

### 3. μ-law ↔ WAV conversão requer audioop

```python
# audioop está deprecated no Python 3.11+ e será removido no 3.13
# Substituir por pydub para transcoding se Python ≥ 3.13:
from pydub import AudioSegment
```

### 4. Gemini Live não persiste transcrição automaticamente

A `GeminiLiveSession` acumula `transcript_segments` em memória. Se o servidor reiniciar DURANTE a chamada, `get_or_restore_session()` recupera do `wsi_sessions.voice_session_state` — mas segmentos não persistidos desde a última `_persist_session_state()` são perdidos.

### 5. Consentimento default-deny em DB indisponível

```python
# verify_consent() quando ConsentCheckerService.check() lança DBError:
# → levanta ConsentNotGrantedError (mesmo que consentimento exista no DB)
# → HTTP 451 (LGPD-safe: incerteza = bloqueio)
# Monitorar taxa de HTTP 451 em staging para detectar indisponibilidade de DB
```

### 6. Twilio Signature em dev

```python
# twilio_voice_service.verify_webhook_signature() retorna True se auth_token não configurado
# Em produção, TWILIO_AUTH_TOKEN obrigatório — sem ele qualquer requisição passa como válida
```

---

## Testes obrigatórios

| Teste | Path sugerido | Cenário |
|-------|--------------|---------|
| Consent hard-block | `tests/unit/test_voice_screening_orchestrator.py` | Candidato sem consentimento → HTTP 451 |
| Consent revogado | `tests/unit/test_voice_screening_orchestrator.py` | Consentimento revogado → mesmo bloco que ausente |
| FairnessGuard bloqueia resposta | `tests/unit/test_voice_screening_orchestrator.py` | LIA responde com texto biased → fallback neutro retornado |
| response_hash NOT NULL | `tests/integration/test_wsi_repository.py` | INSERT sem hash → constraint violation |
| PII mascarado antes de LLM | `tests/unit/test_voice_screening_analysis.py` | Transcrição com CPF/email → PII substituído antes de chamar LLM |
| PSTN fallback sem Twilio | `tests/unit/test_voice_screening_orchestrator.py` | TWILIO_ACCOUNT_SID ausente → status="fallback" |
| VoIP fallback sem Gemini | `tests/unit/test_gemini_live_audio_service.py` | AI_INTEGRATIONS_GEMINI_API_KEY ausente → is_available()=False |
| Circuit breaker aberto | `tests/unit/test_voice_screening_orchestrator.py` | TWILIO_VOICE_CIRCUIT aberto → status="fallback" |
| Sessão recuperada do JSONB | `tests/integration/test_voice_session_recovery.py` | Session não em memória → restaura de wsi_sessions.voice_session_state |
| ws_token inválido | `tests/unit/test_gemini_voice_api.py` | ws_token adulterado → WebSocket close code 4401 |
| Negative-intent consent parsing | `tests/unit/test_twilio_voice_api.py` | "Não tenho certeza" → deny (negação presente) |
| multi-tenant isolation | `tests/security/test_voice_tenant_isolation.py` | Dois tenants com sessões simultâneas → sessions não vazam |

---

## Referências

| Recurso | Localização |
|---------|------------|
| P5 Wizard WSI (geração de perguntas) | `themes/persona/P5_WIZARD_WSI.md` |
| C2 LGPD PII (pii_masking, strip_pii_for_llm_prompt) | `themes/compliance/C2_LGPD_PII_AND_DATA_MINIMIZATION.md` |
| C3 LGPD Consent (ConsentCheckerService) | `themes/compliance/C3_LGPD_CONSENT_AND_DATA_SUBJECT.md` |
| C1 Fairness (FairnessGuard L1+L2) | `themes/compliance/C1_FAIRNESS_AND_ANTI_DISCRIMINATION.md` |
| C4 LGPD Art. 20 (transparency_extras, response_hash) | `themes/compliance/C4_LGPD_ART20_RIGHT_TO_CONTEST.md` |
| C7 Audit Trail (wsi_hashing, AuditCallback) | `themes/compliance/C7_AUDIT_TRAIL_AND_COMPLIANCE_LINT.md` |
| R1 Circuit Breakers (TWILIO_VOICE_CIRCUIT, GEMINI_LIVE_CIRCUIT) | `themes/resilience/R1_CIRCUIT_BREAKERS.md` |
| I4 LLM Providers (get_gemini_client_for_tenant) | `themes/infrastructure/I4_LLM_PROVIDERS.md` |
| I9 Data Layer (WSI tables, migrations) | `themes/infrastructure/I9_DATA_LAYER_AND_MIGRATIONS.md` |
| Handoff LIA Partes A-F | `DEVELOPER_HANDOFF.md` (1204 linhas) |
