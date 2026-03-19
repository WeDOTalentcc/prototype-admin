# Cards Jira — Saturação, Chat Web (Triagem WSI), Comunicação Multicanal e Inscrição Web

**Versão:** 1.1  
**Data:** 11/mar/2026  
**Última atualização:** 11/mar/2026 — Status de implementação atualizado para todos os 27 cards  
**Autor:** André (protótipo LIA) — documento para time de desenvolvimento V5  
**Referências:**
- `docs/pipeline-transition-cards-jira.md` v1.0 (19/fev/2026) — padrão de cards (modelo)
- `docs/diagnostico-agentes-mvp.md` v3.0 (11/mar/2026) — catálogo de agentes e sprints
- `.agents/skills/feature-impact/SKILL.md` — checklist de 12 dimensões de impacto
- `attached_assets/WEDOTALENT_GUIA_COMPLETO_v3.3_PT.md` — governança e regras de negócio

---

## Sumário

1. [Contexto e Motivação](#1-contexto-e-motivação)
2. [Glossário](#2-glossário)
3. [Épicos](#3-épicos)
4. [Fluxos Funcionais Completos](#4-fluxos-funcionais-completos)
5. [Mapa de Comunicações e Templates](#5-mapa-de-comunicações-e-templates)
6. [Cards Sprint SAT — Saturação e Controle de Pools](#6-cards-sprint-sat--saturação-e-controle-de-pools)
7. [Cards Sprint TRI — Chat Web de Triagem (WSI + IA Conversacional)](#7-cards-sprint-tri--chat-web-de-triagem-wsi--ia-conversacional)
8. [Cards Sprint COM — Comunicação Multicanal](#8-cards-sprint-com--comunicação-multicanal)
9. [Cards Sprint INS — Inscrição Web (Formulário Público)](#9-cards-sprint-ins--inscrição-web-formulário-público)
10. [Cards Sprint VOZ — Suporte a Voz Bidirecional](#10-cards-sprint-voz--suporte-a-voz-bidirecional)
11. [Tabela Resumo](#11-tabela-resumo)
12. [Mapa de Dependências](#12-mapa-de-dependências)
13. [Cross-Reference com Cards Existentes](#13-cross-reference-com-cards-existentes)
14. [Referências Visuais — Screenshots e Wireframes](#14-referências-visuais--screenshots-e-wireframes)
15. [Status de Implementação — Rastreabilidade](#15-status-de-implementação--rastreabilidade)

---

## 1. Contexto e Motivação

O protótipo LIA implementa 4 sistemas interdependentes que ainda não possuem cards de Jira dedicados:

1. **Controle de Saturação** — Limita quantos candidatos cada vaga aceita, separando candidatos orgânicos (web/whatsapp) de sourcing (busca ativa/ATS), com fila de espera e desbloqueio dinâmico
2. **Chat Web de Triagem WSI** — Interface de chat para conduzir entrevistas WSI (Work Simulation Interview) com IA conversacional, scoring determinístico e perguntas contextuais via LLM
3. **Comunicação Multicanal** — Dispatcher centralizado que envia email + WhatsApp simultaneamente em 4 pontos automáticos do fluxo, com tom configurável por empresa
4. **Inscrição Web** — Formulário público que permite candidatos se inscreverem diretamente pela página da vaga, com upload de CV e verificação de saturação

Estes sistemas formam a "camada de produto" que complementa os cards de IA já mapeados no `diagnostico-agentes-mvp.md`.

### Convenção de Prefixos

| Prefixo | Domínio | Quantidade |
|---------|---------|:----------:|
| `SAT-` | Saturação e Controle de Pools | 7 cards |
| `TRI-` | Chat Web de Triagem (WSI + IA) | 8 cards |
| `COM-` | Comunicação Multicanal | 5 cards |
| `INS-` | Inscrição Web (Formulário Público) | 3 cards |
| `VOZ-` | Suporte a Voz Bidirecional | 4 cards |

---

## 2. Glossário

> **Leia antes de qualquer card.** Termos específicos deste documento.

| Termo | Definição |
|-------|-----------|
| **Pool Orgânico** | Candidatos vindos de inscrição voluntária (web ou WhatsApp). Campo `origin` = `web` ou `whatsapp`. Threshold padrão: 20 |
| **Pool Sourcing** | Candidatos vindos de busca ativa ou ATS externo. Campo `origin` = `sourcing` ou `ats`. Threshold padrão: 20 |
| **Saturação** | Estado em que um pool atingiu ou ultrapassou seu threshold. Novos candidatos vão para fila de espera (`awaiting_screening`) |
| **Desbloqueio** | Ação que incrementa ambos os thresholds em +N (padrão +10) e promove candidatos da fila. Pode ser permanente (increase) ou temporário (disable por N horas) |
| **WSI** | Work Simulation Interview — metodologia proprietária. 7 blocos: Contexto Profissional, Competências Técnicas, Resolução de Problemas, Comunicação, Trabalho em Equipe, Adaptabilidade, Visão de Futuro |
| **Score WSI** | Nota 0-10 calculada pelo `wsi_deterministic_scorer` usando Bloom/Dreyfus taxonomy. Score ≥ 7.5 = auto-move para Entrevista. Score < 7.5 = sugestão para recrutador |
| **Bloom/Dreyfus** | Taxonomias cognitivas usadas para avaliar profundidade da resposta: Remembering(1) → Understanding(2) → Applying(3) → Analyzing(4) → Evaluating(5) → Creating(6) e Novice(1) → Advanced Beginner(2) → Competent(3) → Proficient(4) → Expert(5) |
| **Off-script** | Quando o candidato faz uma pergunta em vez de responder. Intent classification: QUESTION, GREETING, ANSWER. Limite de 3 desvios antes de forçar retomada |
| **Dispatch Message** | Função central (`dispatch_message`) que envia comunicação simultânea por todos os canais disponíveis (email + WhatsApp), aplicando `lia_tone` da política da empresa |
| **lia_tone** | Tom de comunicação da LIA: `professional` (padrão, "Olá, Nome."), `friendly` ("Oi, Nome!"), `formal` ("Prezado(a) Sr(a). Nome,") |
| **TTS** | Text-to-Speech — geração de áudio a partir de texto. Implementado via OpenAI `tts-1` com voz `nova` |
| **STT** | Speech-to-Text — transcrição de áudio do candidato. Implementado via Deepgram/Whisper |
| **Voice Mode** | Estado `isVoiceMode` que, quando ativo, faz a LIA gerar áudio (`audio_base64`) para cada resposta. Propagado em cada mensagem do candidato |
| **governance_rules** | Campo JSONB na tabela `job_vacancies` que armazena overrides de configuração por vaga (thresholds, saturation_disabled_until, etc.) |
| **additional_data** | Campo JSONB na tabela `company_profiles` que armazena configurações globais da empresa (saturation_settings, etc.) |
| **VacancyCandidate** | Tabela de relacionamento candidato↔vaga. Campos críticos: `status`, `origin`, `lia_score`, `additional_data` |
| **TriagemSession** | Modelo de sessão de triagem WSI. Campos: `token`, `status`, `voice_mode`, `wsi_final_score`, `recommendation`, `candidate_email` |
| **CommunicationDispatcher** | Classe que encapsula SendGrid (email) + Twilio (WhatsApp/SMS) com lazy initialization e mock em dev |

---

## 3. Épicos

| Épico | Nome | Descrição |
|-------|------|-----------|
| **É30** | Saturação — Controle de Pools e Fila | Modelo de dados de saturação, endpoints, SaturationBadge, fila de espera, desbloqueio, configuração global |
| **É31** | Chat Web — Triagem WSI com IA Conversacional | Interface de chat para triagem, WelcomeCard, scoring determinístico, perguntas LLM contextuais, off-script handling, pós-conclusão |
| **É32** | Comunicação Multicanal | CommunicationDispatcher, integração SendGrid/Twilio, 4 pontos de dispatch automático, tone policy |
| **É33** | Inscrição Web — Formulário Público | Página pública da vaga, formulário de candidatura, upload CV, bypass Gate 1, verificação de saturação |
| **É34** | Voz Bidirecional | TTS (LIA fala), STT (candidato fala), AudioPlayer, AudioRecordButton, propagação de voiceMode |

---

## 4. Fluxos Funcionais Completos

### 4.1 Fluxo de Saturação — Passo-a-Passo

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. CONFIGURAÇÃO GLOBAL (Recrutador)                                   │
│    Configurações → Pipeline → Card "Triagem" → Seção "Controle de     │
│    Saturação" com 4 campos:                                           │
│    ┌──────────────────────────────────────────────────────────┐        │
│    │ Limite Inscrições Orgânicas (web/whatsapp): [20]        │        │
│    │ Limite Busca Ativa (sourcing):              [20]        │        │
│    │ Incremento de Desbloqueio:                  [+10]       │        │
│    │ Horas de Desbloqueio Temporário:            [24h]       │        │
│    └──────────────────────────────────────────────────────────┘        │
│    Salva em: company_profiles.additional_data.saturation_settings      │
│    API: PUT /api/v1/settings/saturation                               │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 2. HERANÇA POR VAGA                                                    │
│    Cada vaga herda defaults da empresa, mas pode ter overrides via      │
│    job_vacancies.governance_rules.threshold_web / threshold_sourcing    │
│    Resolução: vaga override > empresa default > sistema default (20)   │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 3. CONSULTA DE STATUS (Kanban)                                         │
│    SaturationBadge faz polling: GET /job-vacancies/{id}/saturation-     │
│    status → retorna:                                                   │
│    {                                                                   │
│      organic: { count: 42, threshold: 20, is_saturated: true, 210% }, │
│      sourcing: { count: 0, threshold: 20, is_saturated: false, 0% },  │
│      counts_by_channel: { web: 40, whatsapp: 2, sourcing: 0, ats: 0 },│
│      queued_count: 5,                                                  │
│      recommendation: "pause_screening",                                │
│    }                                                                   │
│                                                                        │
│    Badge renderiza: "42/20 org | 0/20 src" com cor por estado:         │
│    🔴 saturated (is_saturated=true)                                    │
│    🟡 almost (percentage >= 90%)                                       │
│    🟢 normal (default)                                                 │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 4. CHEGADA DE CANDIDATO                                                │
│    4a. Orgânico (web/whatsapp):                                        │
│        SE organic.count < threshold_web → cria com status "screening"  │
│        SE organic.count >= threshold_web → cria com status             │
│           "awaiting_screening" (fila de espera)                        │
│    4b. Sourcing (sourcing/ats):                                        │
│        SE sourcing.count < threshold_sourcing → cria normalmente       │
│        SE sourcing.count >= threshold_sourcing → fila ou rejeição      │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 5. FILA DE ESPERA                                                      │
│    Candidatos com status "awaiting_screening" ficam na fila             │
│    Ordenação: lia_score DESC NULLS LAST, created_at ASC                │
│    API: GET /job-vacancies/{id}/screening-queue                        │
│    Badge "Aguardando" (âmbar) no card do candidato no kanban           │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 6. DESBLOQUEIO (Popover do SaturationBadge)                            │
│    Opção A: "Aumentar Limite (+10)"                                    │
│      → POST /job-vacancies/{id}/unlock-pipeline                        │
│        { action: "increase_threshold", new_threshold: current+10 }     │
│      → Incrementa AMBOS os pools (threshold_web e threshold_sourcing)  │
│      → Promove até N candidatos da fila via process_screening_queue    │
│    Opção B: "Desbloquear Temporariamente (24h)"                        │
│      → POST /job-vacancies/{id}/unlock-pipeline                        │
│        { action: "disable_temporarily", disable_hours: 24 }            │
│      → Grava saturation_disabled_until no governance_rules             │
│      → Promove 5 candidatos da fila                                    │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 7. PROMOÇÃO DA FILA (Automática após desbloqueio)                      │
│    process_screening_queue(db, vacancy_id, company_id, max_promote)     │
│    Para cada candidato promovido:                                       │
│      1. Muda status: awaiting_screening → screening                    │
│      2. Verifica se existe conversa WhatsApp ATIVA (state=active)      │
│         (busca WhatsAppConversation por candidate_id, state=active)    │
│      3. SE conversa ativa: envia WhatsApp direto (template #4)         │
│      4. SE NÃO tem conversa OU WhatsApp falhou: envia via              │
│         CommunicationDispatcher multicanal (template #5)               │
│      5. Grava promoted_from_queue_at + invite_channel no additional    │
│    Convite email (template #5): "Convite para Triagem - {job_title}"   │
│    Convite WhatsApp (template #4): "Olá! 👋 Há vaga para continuar..."│
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 8. OVERRIDE MANUAL DO RECRUTADOR                                       │
│    Recrutador clica "Aprovar" em candidato awaiting_screening           │
│    → handle_recruiter_override_approve(db, candidate_id, vacancy_id,   │
│        company_id)                                                      │
│    → Muda status → screening                                           │
│    → Verifica se existe conversa WhatsApp ATIVA:                       │
│      SE SIM: envia WhatsApp direto (template #6) — "Você foi          │
│        selecionado para continuar... Responda SIM! 🚀"                 │
│      SE NÃO (ou falha): envia via CommunicationDispatcher              │
│        multicanal (template #7) — "Convite para Triagem - {title}"    │
│    → Grava recruiter_override_at no additional_data                    │
│    → Registra atividade "recruiter_override_approve"                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Fluxo do Chat Web de Triagem — Passo-a-Passo

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. ACESSO PELA URL                                                     │
│    Candidato recebe link: /triagem/{token}                             │
│    Token é UUID único gerado quando candidato é convidado              │
│    page.tsx carrega useTriagemChat(token) hook                         │
│                                                                        │
│    Hook faz: GET /api/backend-proxy/triagem/{token}                    │
│    → Proxy Next.js redireciona para backend:                           │
│      GET http://localhost:8000/api/v1/triagem/{token}                  │
│    → Backend valida token, retorna { session, config, messages }       │
│    → Se token inválido: pageState = "error" (TOKEN_INVALID)            │
│    → Se token expirado: pageState = "error" (TOKEN_EXPIRED)            │
│    → Se já completou: pageState = "completion"                         │
│    → Se in_progress: pageState = "chat" (restaura mensagens)           │
│    → Se invited/started: pageState = "welcome"                         │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 2. WELCOME CARD                                                        │
│    Renderiza WelcomeCard com config da sessão:                          │
│    ┌────────────────────────────────────────────────┐                   │
│    │    [Logo da Empresa ou Nome]                   │                   │
│    │    "Engenheiro Senior" (jobTitle)              │                   │
│    │                                                │                   │
│    │    🟦 LIA Icon                                │                   │
│    │    "Olá, Maria! Eu sou a LIA 👋"              │                   │
│    │    "Vou conduzir sua triagem para esta vaga.   │                   │
│    │     Será uma conversa rápida e descontraída    │                   │
│    │     sobre sua experiência e habilidades."      │                   │
│    │                                                │                   │
│    │    ⏱ Tempo estimado: ~15 minutos              │                   │
│    │                                                │                   │
│    │    [████ Iniciar Conversa ████]                │                   │
│    │    [──── Iniciar Conversa por Voz ────] 🎤    │                   │
│    │                                                │                   │
│    │    🔒 Política de Privacidade                 │                   │
│    └────────────────────────────────────────────────┘                   │
│                                                                        │
│    config = { companyName, companyLogoUrl, jobTitle, candidateName,     │
│               estimatedMinutes, privacyPolicyUrl, audioEnabled,        │
│               feedbackEnabled, welcomeMessage, voiceMode }             │
│                                                                        │
│    Branding: Logo e nome SEMPRE da empresa cliente, nunca WeDo         │
│    Botão "Iniciar por Voz": só aparece se config.voiceMode = true      │
│    Design: bg-gray-900 no botão principal, rounded-md, Open Sans       │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 3. INÍCIO DA CONVERSA                                                  │
│    Candidato clica "Iniciar Conversa" (voiceMode=false) ou             │
│    "Iniciar Conversa por Voz" (voiceMode=true)                         │
│                                                                        │
│    startChat(voiceMode) faz:                                           │
│    POST /api/backend-proxy/triagem/{token}/start                       │
│    Body: { voice_mode: boolean }                                       │
│                                                                        │
│    Backend (start_session):                                            │
│    1. Muda status → in_progress                                        │
│    2. Grava session.voice_mode = voiceMode                             │
│    3. Gera primeira mensagem da LIA (transição para bloco 1)           │
│    4. Se voiceMode=true: gera áudio via TTS                            │
│    5. Retorna { session, lia_message, progress }                       │
│                                                                        │
│    Frontend:                                                           │
│    1. setPageState("chat")                                              │
│    2. Adiciona lia_message às mensagens                                │
│    3. Se audioUrl presente: AudioPlayer renderiza e auto-play          │
│    4. LIAIcon pulsa (speaking=true) enquanto áudio toca               │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 4. LOOP DE CONVERSA (7 blocos WSI)                                     │
│    Para cada bloco WSI (1-7):                                          │
│                                                                        │
│    4a. CANDIDATO RESPONDE                                              │
│        InputBar: textarea + Send button + AudioRecordButton            │
│        sendMessage(payload: SendMessagePayload) faz:                   │
│        POST /api/backend-proxy/triagem/{token}/message                 │
│        Body: { content, type, selectedOption?, likertValue?,           │
│                voiceMode: isVoiceMode }                                │
│        ⚠️ voiceMode é o estado RUNTIME do UI, não o config inicial     │
│                                                                        │
│    4b. BACKEND PROCESSA (process_message)                              │
│        1. Intent classification via LLM:                                │
│           _classify_intent(message, block_name, current_question)       │
│           → "ANSWER" | "QUESTION" | "GREETING"                         │
│        2. Se ANSWER:                                                   │
│           - Score determinístico: _score_response_deterministic(        │
│               response_text, block_type, competency)                   │
│             Usa Bloom taxonomy (6 níveis) + Dreyfus model (5 níveis)   │
│             NÃO usa random.uniform — é determinístico                  │
│           - Gera próxima pergunta contextual via LLM:                  │
│             _generate_contextual_question(block_name, response_text,   │
│               job_title, previous_questions)                           │
│        3. Se QUESTION:                                                 │
│           - Gera resposta off-script via LLM:                          │
│             _generate_off_script_response(question, job_context)       │
│           - Retoma roteiro naturalmente                                │
│           - Limite: 3 desvios antes de forçar retomada                 │
│        4. Se voiceMode=true: gera áudio via _generate_tts_audio()      │
│        5. Retorna { lia_message, progress, audio_base64? }             │
│                                                                        │
│    4c. FRONTEND RENDERIZA                                              │
│        - MessageBubble com alignment por role:                         │
│          LIA: justify-start, bg-white border, LIAIcon à esquerda      │
│          Candidato: justify-end, bg-gray-900, initials à direita      │
│        - Se audioUrl: AudioPlayer com play/pause e progress bar        │
│        - Se role=lia e isAudioPlaying: LIAIcon speaking animation      │
│        - Markdown simples: **bold**, *italic*, \n → <br>               │
│        - ProgressBar: "Bloco 3/7 — Resolução de Problemas"            │
│                                                                        │
│    4d. TRANSIÇÃO ENTRE BLOCOS                                          │
│        Automática quando LLM decide que bloco foi coberto              │
│        Progress atualiza: currentBlock++, blockName muda               │
│        Transição suave com mensagem contextual                         │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 5. CONCLUSÃO DA TRIAGEM                                                │
│    Após completar bloco 7:                                             │
│                                                                        │
│    5a. SCORE FINAL                                                     │
│        _calculate_final_score(response_scores):                        │
│        - Combina scores por bloco com pesos:                           │
│          Competências Técnicas: peso 2x                                │
│          Resolução de Problemas: peso 2x                               │
│          Demais blocos: peso 1x                                        │
│        - Score 0-10, recommendation:                                   │
│          ≥ 7.5 → "approved"                                            │
│          5.0-7.4 → "pending" (recrutador decide)                       │
│          < 5.0 → "rejected"                                            │
│                                                                        │
│    5b. PÓS-CONCLUSÃO (_trigger_post_completion)                        │
│        1. Email de confirmação real via CommunicationDispatcher:        │
│           Subject: "Triagem Concluída - {job_title}"                   │
│           Body: "Sua triagem foi concluída com sucesso!                │
│                  Nossa equipe avaliará seu perfil e você receberá      │
│                  uma resposta em até 5 dias úteis."                    │
│        2. Recruiter notification (queued): notifica recrutador         │
│        3. Pipeline auto-move:                                          │
│           Score ≥ 7.5 → move candidato para "Entrevista"              │
│           Score < 7.5 → cria sugestão para recrutador avaliar          │
│        4. Audit log: registra decisão para compliance                  │
│                                                                        │
│    5c. FRONTEND: pageState → "completion"                              │
│        CompletionCard: "Triagem concluída!",                           │
│        questionsAnswered, durationMinutes, nextSteps[]                 │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Fluxo de Comunicação Multicanal — Passo-a-Passo

```
┌─────────────────────────────────────────────────────────────────────────┐
│ PONTO CENTRAL: CommunicationDispatcher.dispatch_message()              │
│                                                                        │
│ Parâmetros:                                                            │
│   company_id, recipient_email?, recipient_phone?, subject?,            │
│   message, channel?, candidate_name?, db?, multi_channel=True          │
│                                                                        │
│ Fluxo interno:                                                         │
│   1. Carrega policy da empresa: get_policy_for_company(company_id, db) │
│   2. Resolve lia_tone: professional | friendly | formal               │
│   3. Aplica tone ao texto: _apply_tone(message, tone, candidate_name) │
│      - professional: "Olá, {nome_completo}. {mensagem}"               │
│      - friendly: "Oi, {primeiro_nome}! {mensagem}"                    │
│      - formal: "Prezado(a) Sr(a). {nome_completo}, {mensagem}"        │
│   4. Se multi_channel=True e sem channel explícito:                    │
│      → Envia para TODOS os canais disponíveis simultaneamente          │
│      → Se tem email: send_email(to, subject, html, text)              │
│      → Se tem phone: send_whatsapp(to, message, template?)            │
│   5. Se channel explícito ou multi_channel=False:                      │
│      → Envia para canal específico via _send_single_channel()          │
│   6. Retorna { success, channels_sent[], results{} }                   │
│                                                                        │
│ Providers:                                                             │
│   Email: SendGrid (SENDGRID_API_KEY)                                   │
│     - from: SENDGRID_FROM_EMAIL (default: noreply@example.com)         │
│     - sender name: SENDGRID_FROM_NAME (default: "LIA Recruitment")     │
│     - Rate limit: 10/min por usuário                                   │
│     - Retorno: { success, message_id, status_code }                    │
│     - Dev fallback: mock success com mock-email-{uuid} ID              │
│                                                                        │
│   WhatsApp: Twilio (TWILIO_ACCOUNT_SID + TWILIO_AUTH_TOKEN)            │
│     - from: TWILIO_WHATSAPP_FROM (default: whatsapp:+14155238886)      │
│     - Formato to: "whatsapp:+5511999999999" (auto-prefixed)            │
│     - Template SID: opcional (para templates pré-aprovados Meta)       │
│     - Retorno: { success, message_id (SID), status }                   │
│     - Dev fallback: mock success com mock-whatsapp-{uuid} ID           │
│                                                                        │
│   SMS: Twilio (mesmo client)                                           │
│     - from: TWILIO_SMS_FROM ou TWILIO_PHONE_NUMBER                     │
│     - Max 1600 chars (auto-split pelo Twilio)                          │
│     - Dev fallback: mock success com mock-sms-{uuid} ID                │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ 4 PONTOS DE DISPATCH AUTOMÁTICO (automation_handlers.py)               │
│                                                                        │
│ 1. SCREENING FEEDBACK (handle_screening_completed)                     │
│    Trigger: Triagem WSI concluída (approved/rejected)                  │
│    Subject: "Resultado da Triagem - {Aprovado|Reprovado}"              │
│    Body: "Sua triagem ({WSI}) foi concluída. Resultado: {status}."     │
│    Canais: email + whatsapp (multi_channel=True)                       │
│    Tone: aplica lia_tone da empresa                                    │
│                                                                        │
│ 2. REJECTION (handle_stage_changed → rejected_stages)                  │
│    Trigger: Candidato movido para stage de rejeição                    │
│    Subject: "Atualização sobre sua candidatura"                        │
│    Body: "Agradecemos seu interesse e participação no processo         │
│           seletivo. Após análise cuidadosa, decidimos seguir com       │
│           outros candidatos. Motivo: {rejection_reason}"               │
│    Canais: email + whatsapp (multi_channel=True)                       │
│    Default reason: "Perfil não aderente aos requisitos da vaga"        │
│                                                                        │
│ 3. QUEUE INVITE (process_screening_queue)                              │
│    Trigger: Slot abre na fila (desbloqueio ou candidato sai)           │
│    Subject: "Convite para Triagem - {job_title}"                       │
│    Body: "Temos uma ótima notícia! Agora há uma vaga disponível       │
│           para continuar o processo de triagem para {job_title}.       │
│           Acesse o link: {screening_link}"                             │
│    Canais: tenta WhatsApp primeiro, fallback email                     │
│    Link: "/triagem/{vacancy_id}?candidate={candidate_id}"             │
│                                                                        │
│ 4. RECRUITER OVERRIDE (handle_recruiter_override_approve)              │
│    Trigger: Recrutador aprova candidato da fila manualmente            │
│    SE conversa WhatsApp ativa: template #6 — WhatsApp direto           │
│      "Você foi selecionado... Responda SIM!" (diferente do #4)         │
│    SE NÃO: template #7 — CommunicationDispatcher multicanal           │
│      Subject: "Convite para Triagem - {job_title}"                     │
│      Body: "Você foi selecionado... Acesse o link: {link}"             │
│                                                                        │
│ PONTO EXTRA: PÓS-CONCLUSÃO (triagem_session_service.py)               │
│    Trigger: Candidato completa triagem WSI                             │
│    Subject: "Triagem Concluída - {job_title}"                          │
│    Body: "Sua triagem foi concluída com sucesso! Nossa equipe          │
│           avaliará seu perfil e você receberá uma resposta em          │
│           até 5 dias úteis. Agradecemos sua participação!"             │
│    Canais: email (recipient_phone=None — só email de confirmação)      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Mapa de Comunicações e Templates

### 5.1 Templates de Email por Evento

| # | Evento | Subject | Body (completo) | Tone | Canais | Condição de envio | Arquivo (path completo + linhas) |
|:-:|--------|---------|-----------------|------|--------|-------------------|----------------------------------|
| 1 | Screening Feedback (Aprovado) | "Resultado da Triagem - Aprovado" | "Sua triagem (WSI) foi concluída. Resultado: aprovado." | lia_tone da empresa | Email + WhatsApp (multi_channel=True) | Triagem WSI completada com passed=True | `lia-agent-system/app/domains/automation/services/automation_handlers.py` L99-127 |
| 2 | Screening Feedback (Reprovado) | "Resultado da Triagem - Reprovado" | "Sua triagem (WSI) foi concluída. Resultado: reprovado." | lia_tone da empresa | Email + WhatsApp (multi_channel=True) | Triagem WSI completada com passed=False | `lia-agent-system/app/domains/automation/services/automation_handlers.py` L99-127 |
| 3 | Rejeição (Stage Change) | "Atualização sobre sua candidatura" | "Agradecemos seu interesse e participação no processo seletivo. Após análise cuidadosa, decidimos seguir com outros candidatos. Motivo: {rejection_reason}" | lia_tone da empresa | Email + WhatsApp (multi_channel=True) | Stage movido para rejected_stages (rejected, reprovado, declined, etc) | `lia-agent-system/app/domains/automation/services/automation_handlers.py` L629-670 |
| 4 | Convite Fila — WhatsApp direto | (sem subject — WhatsApp) | "Olá, {nome}! 👋\n\nTemos uma ótima notícia! Agora há uma vaga disponível para continuar o processo de triagem para *{job_title}*.\n\nVamos continuar de onde paramos? Responda *SIM* para iniciarmos! 🚀" | friendly (hardcoded) | WhatsApp direto (provider.send_text_message) | Candidato TEM conversa WhatsApp existente e ativa (WhatsAppConversation.state=active) | `lia-agent-system/app/domains/automation/services/automation_handlers.py` L980-1017 |
| 5 | Convite Fila — Email fallback | "Convite para Triagem - {job_title}" | "Temos uma ótima notícia! Agora há uma vaga disponível para continuar o processo de triagem para {job_title}.\n\nAcesse o link abaixo para iniciar sua triagem online:\n{screening_link}" | lia_tone da empresa | Email + WhatsApp via CommunicationDispatcher | Candidato NÃO tem conversa WhatsApp ativa OU WhatsApp direto falhou | `lia-agent-system/app/domains/automation/services/automation_handlers.py` L1022-1057 |
| 6 | Override Recrutador — WhatsApp direto | (sem subject — WhatsApp) | "Olá, {nome}! 👋\n\nTemos uma ótima notícia! Você foi selecionado para continuar o processo de triagem para *{job_title}*.\n\nVamos começar? Responda *SIM* para iniciarmos! 🚀" | friendly (hardcoded) | WhatsApp direto (provider.send_text_message) | Recrutador aprova + candidato TEM conversa WhatsApp ativa | `lia-agent-system/app/domains/automation/services/automation_handlers.py` L1170-1189 |
| 7 | Override Recrutador — Email fallback | "Convite para Triagem - {job_title}" | "Você foi selecionado para continuar o processo de triagem para {job_title}.\n\nAcesse o link abaixo para iniciar:\n{screening_link}" | lia_tone da empresa | Email + WhatsApp via CommunicationDispatcher | Override + NÃO tem WhatsApp ativo OU WhatsApp falhou | `lia-agent-system/app/domains/automation/services/automation_handlers.py` L1193-1223 |
| 8 | Confirmação Pós-Triagem | "Triagem Concluída - {job_title}" | "Sua triagem para a vaga de {job_title} foi concluída com sucesso! Nossa equipe avaliará seu perfil e você receberá uma resposta em até 5 dias úteis. Agradecemos sua participação!" | lia_tone da empresa | Email apenas (recipient_phone=None) | Candidato completa triagem WSI (todos os 7 blocos) | `lia-agent-system/app/services/triagem_session_service.py` L829-848 |

**Notas sobre os templates:**
- Templates 4 e 6 (WhatsApp direto) diferem sutilmente: #4 diz "continuar de onde paramos" (candidato já foi processado antes); #6 diz "Você foi selecionado" (linguagem de priorização pelo recrutador)
- Templates 5 e 7 (email fallback) diferem: #5 diz "agora há uma vaga disponível" (fila natural); #7 diz "Você foi selecionado" (override manual)
- screening_link format: "/triagem/{vacancy_id}?candidate={candidate_id}"
- rejection_reason default: "Perfil não aderente aos requisitos da vaga" (kwargs.get fallback)

### 5.2 Canais Disponíveis no Sistema

| Canal | Constante | Provider | Variáveis de Ambiente | Status |
|-------|-----------|----------|----------------------|--------|
| Email | `CHANNEL_EMAIL` | SendGrid | `SENDGRID_API_KEY`, `SENDGRID_FROM_EMAIL`, `SENDGRID_FROM_NAME` | Implementado, mock em dev |
| WhatsApp | `CHANNEL_WHATSAPP` | Twilio | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM` | Implementado, mock em dev |
| SMS | (via Twilio) | Twilio | `TWILIO_SMS_FROM` ou `TWILIO_PHONE_NUMBER` | Implementado, mock em dev |
| Notificação Bell | `CHANNEL_BELL` | In-app | — | Estrutura existe, não wired |
| Teams | `CHANNEL_TEAMS` | MS Graph | `MS_TEAMS_WEBHOOK_URL` | Estrutura existe, não wired |
| Chat LIA | `CHANNEL_CHAT_LIA` | In-app | — | Template channel only |
| Relatórios | `CHANNEL_REPORT` | — | — | Template channel only |
| Briefings | `CHANNEL_BRIEFING` | — | — | Template channel only |
| Pareceres | `CHANNEL_PARECER` | — | — | Template channel only |

### 5.3 Sistema de Templates de Email (Backend)

```
Modelo: EmailTemplate (tabela email_templates)
  - id, name, slug, subject, body_html, body_text
  - channel (email, whatsapp, bell, teams, etc)
  - variables[] (lista de variáveis interpoláveis)
  - category (screening, rejection, invitation, etc)
  - company_id (multi-tenant)
  - is_default, is_active

API de Templates:
  GET    /api/v1/email-templates          → listar templates
  POST   /api/v1/email-templates          → criar template
  PUT    /api/v1/email-templates/{id}     → atualizar template
  DELETE /api/v1/email-templates/{id}     → deletar template
  POST   /api/v1/email-templates/preview  → preview com variáveis
  POST   /api/v1/email-templates/send     → enviar via template
  POST   /api/v1/email-templates/generate → gerar template via LLM
  POST   /api/v1/email-templates/adjust   → ajustar template via LLM

Rate Limit: 10 emails/minuto por usuário
Sanitização: XSS prevention em todas as variáveis de template
Seeder: seed_default_templates() + clone_templates_for_client()
```

---

## 6. Cards Sprint SAT — Saturação e Controle de Pools

### SAT-001: Modelo de Dados e Endpoints de Saturação

```yaml
Titulo: "[Saturação] Modelo de Dados — Pools Separados, Thresholds e Governance Rules"
Tipo: Feature
Area: Backend
Sprint: S1
Pontos: 8
Prioridade: Crítica
Epic: É30
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Backend + Frontend proxy)
Fase: MVP Alpha 1
Tags: [backend, api, database, saturação, multi-tenant]
Referências IA: Nenhuma (feature de regra de negócio pura)

Descricao: |
  Criar o modelo de dados e endpoints REST para o sistema de controle de
  saturação com pools separados (orgânico vs sourcing). Cada vaga tem
  limites independentes para candidatos orgânicos (web/whatsapp) e de
  busca ativa (sourcing/ats), configuráveis globalmente por empresa e
  com override por vaga.
  
  O sistema separa candidatos em 2 pools baseados no campo `origin` da
  tabela VacancyCandidate:
  - Pool Orgânico: origin IN ('web', 'whatsapp') + origin IS NULL
  - Pool Sourcing: origin IN ('sourcing', 'ats')
  
  Defaults do sistema: threshold_web=20, threshold_sourcing=20,
  unlock_increment=10, unlock_hours=24.

Historia de Usuario: |
  Como recrutador, eu quero definir limites separados para candidatos
  que se inscrevem voluntariamente e candidatos que eu busco ativamente,
  para gerenciar melhor o volume do pipeline por vaga.

Regras de Negocio:
  1. Cada pool (orgânico/sourcing) tem threshold independente
  2. Empresa define defaults globais em company_profiles.additional_data.saturation_settings
  3. Vaga pode ter overrides em job_vacancies.governance_rules (threshold_web, threshold_sourcing)
  4. Resolução de threshold: override vaga > default empresa > default sistema (20)
  5. Candidatos com status IN ('rejected', 'declined', 'withdrawn') NÃO contam no pool
  6. Candidatos com origin IS NULL contam como orgânicos
  7. Isolamento multi-tenant: toda query filtra por vacancy_id (que pertence a company_id)
  8. saturation_disabled_until (ISO datetime) permite bypass temporário de AMBOS os pools
  9. Quando bypass ativo: is_saturated = False para ambos os pools

Requisitos Tecnicos:
  Backend — Schemas Pydantic:
    - ChannelCounts(web: int, whatsapp: int, sourcing: int, ats: int)
    - ChannelSaturation(count: int, threshold: int, is_saturated: bool,
        slots_remaining: int, percentage: float)
    - SaturationSettingsRequest(threshold_web?, threshold_sourcing?,
        unlock_increment?, unlock_hours?) — todos Optional com ge/le validação
    - SaturationSettingsResponse(company_id, threshold_web, threshold_sourcing,
        unlock_increment, unlock_hours, updated_at)
    - SaturationStatusResponse (ver schemas completos abaixo)
    - UnlockPipelineRequest(action: "increase_threshold"|"disable_temporarily",
        new_threshold?, disable_hours?)
    - UnlockPipelineResponse(success, message, new_threshold?,
        saturation_disabled_until?)
  
  Backend — Endpoints:
    GET  /api/v1/settings/saturation?company_id={id}
      Headers: X-Company-ID, X-User-ID
      Resposta: SaturationSettingsResponse
      Fluxo: _find_company(db, company_id) → _get_company_saturation_defaults()
    
    PUT  /api/v1/settings/saturation?company_id={id}
      Headers: X-Company-ID, X-User-ID
      Body: SaturationSettingsRequest (partial update)
      Fluxo: Atualiza company.additional_data.saturation_settings
      ⚠️ Não altera thresholds de vagas existentes, só o default futuro
    
    GET  /api/v1/job-vacancies/{job_id}/saturation-status
      Resposta completa: {
        job_id, approved_count (total ativo), saturation_threshold (legacy),
        is_saturated (OR de ambos pools), slots_remaining (soma),
        recommendation ("continue_screening"|"pause_screening"),
        saturation_percentage (total/total_threshold * 100),
        queued_count (awaiting_screening + sourced),
        last_screened_at, saturation_disabled_until,
        counts_by_channel: { web, whatsapp, sourcing, ats },
        organic: { count, threshold, is_saturated, slots_remaining, percentage },
        sourcing: { count, threshold, is_saturated, slots_remaining, percentage },
        threshold_web, threshold_sourcing, unlock_increment, unlock_hours
      }
      Fluxo interno:
        1. Busca vacancy e company
        2. _resolve_thresholds(governance_rules, company_defaults)
        3. Query com func.count().filter() por origin (5 contagens separadas)
        4. Calcula organic_count = web + whatsapp + unknown
        5. Calcula source_count = sourcing + ats
        6. Verifica bypass (saturation_disabled_until > utcnow)
    
    POST /api/v1/job-vacancies/{job_id}/unlock-pipeline
      Headers: X-Company-ID, X-User-ID
      Body: UnlockPipelineRequest
      Ação "increase_threshold":
        - Calcula increment = new_threshold - current_saturation_threshold
        - Se increment < 1: usa DEFAULT_UNLOCK_INCREMENT (10)
        - Atualiza governance_rules: saturation_threshold, threshold_web (+increment),
          threshold_sourcing (+increment)
        - Chama process_screening_queue(max_promote=increment)
      Ação "disable_temporarily":
        - Grava saturation_disabled_until = utcnow + disable_hours
        - Chama process_screening_queue(max_promote=5)
    
    GET  /api/v1/job-vacancies/{job_id}/screening-queue
      Resposta: { job_id, queued_count, candidates[] }
      Ordenação: lia_score DESC NULLS LAST, created_at ASC
    
    POST /api/v1/job-vacancies/{job_id}/process-queue
      Body: { max_promote: int (1-50, default 1) }
      Chama: process_screening_queue() de automation_handlers.py
  
  Frontend — Proxy Routes:
    src/app/api/backend-proxy/settings/saturation/route.ts
      → Proxy GET/PUT para /api/v1/settings/saturation
    src/app/api/backend-proxy/job-vacancies/[jobId]/saturation-status/route.ts
      → Proxy GET para /api/v1/job-vacancies/{jobId}/saturation-status
  
  Database — Campos existentes usados:
    job_vacancies.governance_rules (JSONB): threshold_web, threshold_sourcing,
      unlock_increment, unlock_hours, saturation_threshold (legacy),
      saturation_disabled_until
    company_profiles.additional_data (JSONB): saturation_settings {
      threshold_web, threshold_sourcing, unlock_increment, unlock_hours }
    vacancy_candidates.origin (VARCHAR): 'web', 'whatsapp', 'sourcing', 'ats', NULL
    vacancy_candidates.status (VARCHAR): 'awaiting_screening' para fila

  Constantes no código:
    EXCLUDED_STATUSES = ('rejected', 'declined', 'withdrawn')
    ORGANIC_ORIGINS = ('web', 'whatsapp')
    SOURCING_ORIGINS = ('sourcing', 'ats')
    DEFAULT_SATURATION_THRESHOLD = 20
    DEFAULT_UNLOCK_INCREMENT = 10
    DEFAULT_UNLOCK_HOURS = 24

DoD:
  - [x] Schemas Pydantic para todas as requests/responses
  - [x] 6 endpoints implementados e testados
  - [x] Resolução de thresholds com 3 níveis (vaga > empresa > sistema)
  - [x] Query por origin com func.count().filter() (não N+1)
  - [x] Bypass temporário (saturation_disabled_until) funcional
  - [x] process_screening_queue chamado após unlock
  - [x] Headers X-Company-ID e X-User-ID aceitos em endpoints de settings
  - [ ] Testes unitários para cada endpoint
  - [ ] Testes de integração para resolução de thresholds

Criterios de Aceitacao:
  - [x] GET /saturation-status retorna contagens separadas por pool
  - [x] PUT /settings/saturation com threshold_web=30 altera default da empresa
  - [x] unlock-pipeline com action="increase_threshold" incrementa AMBOS os pools
  - [x] unlock-pipeline com action="disable_temporarily" define bypass de 24h
  - [x] Durante bypass, is_saturated retorna false para ambos pools
  - [x] Candidatos rejected/declined/withdrawn NÃO são contados
  - [x] Candidatos com origin NULL são contados como orgânicos

Como Testar:
  1. Criar vaga com 20 candidatos orgânicos
  2. GET /saturation-status → organic.is_saturated = true, organic.percentage = 100%
  3. POST /unlock-pipeline { action: "increase_threshold", new_threshold: 30 }
  4. GET /saturation-status → organic.threshold = 30, is_saturated = false
  5. PUT /settings/saturation { threshold_sourcing: 50 } → defaults atualizados
  6. Criar nova vaga → herda threshold_sourcing = 50 da empresa

Inteligencia e Automacao:
  Agentes Envolvidos:
    - PolicyReActAgent (domain=policy): Consulta/valida políticas de saturação da empresa
    - KanbanReActAgent (domain=kanban): Consome dados de saturação para análise de pipeline
  Tools Utilizadas:
    - get_pipeline_summary: Retorna saturation_status por vaga no overview do kanban
    - validate_policy_compliance: Valida se thresholds estão dentro dos limites da empresa
  Servicos IA:
    - SaturationStatusService (saturation.py): Calcula is_saturated por pool (orgânico/sourcing)
    - Fórmula: activeInScreening / max_screening_slots (per pool)
    - governance_rules JSONB: Armazena thresholds configuráveis por vaga
  Modelo LLM: Nenhum — lógica de saturação é 100% determinística (regras de negócio)
  Governanca e Compliance:
    - PolicyEngine: Regra "max_candidates_per_vacancy" (default 500) aplicada como teto absoluto
    - Multi-tenant isolation: Toda query filtra por vacancy_id → company_id (sem cross-tenant leak)
    - saturation_disabled_until: Bypass temporário de ambos os pools, registrado em audit_log
    - IndustryDefaults: Financeiro (BCB 498) pode ter allow_global_search=False
  Fairness e Bias:
    - Pools separados (orgânico vs sourcing) evitam que sourcing ativo prejudique candidatos orgânicos
    - Thresholds independentes garantem equidade entre canais de entrada
    - BiasAuditService: Pode gerar snapshot de distribuição demográfica por pool (futuro)
  Automacoes/Triggers:
    - unlock-pipeline (increase_threshold/disable_temporarily) → dispara process_screening_queue
    - Mudança de status de candidato (rejected/withdrawn) → reavalia is_saturated → pode promover fila
  Fallbacks:
    - governance_rules ausente → defaults: max_organic=10, max_sourcing=5
    - saturation_disabled_until expirado → reativa automaticamente
    - Erro no cálculo → is_saturated=False (candidato NÃO é bloqueado)

Arquivos de Referencia (Prototipo LIA):
  - backend: lia-agent-system/app/api/v1/saturation.py (496L — código completo)
  - model: lia-agent-system/app/models/job_vacancy.py (governance_rules JSONB)
  - model: lia-agent-system/app/models/candidate.py (VacancyCandidate.origin)
  - model: lia-agent-system/app/models/company.py (additional_data JSONB)
  - proxy: plataforma-lia/src/app/api/backend-proxy/settings/saturation/route.ts
  - proxy: plataforma-lia/src/app/api/backend-proxy/job-vacancies/[jobId]/saturation-status/route.ts
```

---

### SAT-002: SaturationBadge — Componente Visual no Kanban

```yaml
Titulo: "[Saturação] SaturationBadge — Badge Visual com Popover de Ações no Kanban"
Tipo: Feature
Area: Frontend
Sprint: S1
Pontos: 5
Prioridade: Alta
Epic: É30
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend)
Fase: MVP Alpha 1
Tags: [frontend, componente, kanban, saturação, design-system]
Dependências: SAT-001

Descricao: |
  Componente React (~267L) que exibe o estado de saturação de uma vaga
  no header do Kanban. Mostra contagens separadas dos pools orgânico e
  sourcing, com cor dinâmica por estado (saturated/almost/normal).
  
  Inclui popover com:
  - Detalhamento por pool (orgânico e sourcing)
  - Recomendação do sistema
  - Contagem de candidatos na fila
  - Botão de desbloqueio (+N)
  - Botão de desbloqueio temporário (Nh)
  - Link "Ver Configurações" → navega para /configuracoes
  
  Design System v4.2.1:
  - rounded-md em todos os elementos
  - Open Sans como tipografia principal
  - Cores: gray-900 (botões), #60BED1 (apenas LIA icon), sem shadows
  - Dark mode support com dark: variants

Historia de Usuario: |
  Como recrutador, eu quero ver rapidamente o estado de saturação de
  cada vaga no Kanban, com opções para desbloquear quando necessário.

Regras de Negocio:
  1. Badge não aparece enquanto dados estão carregando (loading state)
  2. Estados visuais:
     - saturated (🔴): organic.is_saturated || sourcing.is_saturated
     - almost (🟡): organic.percentage >= 90 || sourcing.percentage >= 90
     - normal (🟢): default
  3. Durante bypass ativo: estado = "normal" mesmo se contagem > threshold
  4. Valores de incremento e horas vêm da API (dinâmicos, não hardcoded)
  5. Após ação de unlock: refetch automático dos dados
  6. Toast de sucesso/erro após ações de desbloqueio
  7. Link "Ver Configurações" usa router.push('/configuracoes')

Requisitos Tecnicos:
  Frontend:
    - Props: { jobId: string }
    - Interface SaturationStatus com todos os campos da API
    - Estados: data, loading, actionLoading
    - Polling: fetchStatus via useCallback + useEffect
    - Popover: @radix-ui/react-popover (via @/components/ui/popover)
    - Ícones: lucide-react (AlertTriangle, TrendingUp, Lightbulb, Clock,
        Users, Globe, Search, Settings)
    - Navegação: useRouter de next/navigation
    - Toast: sonner (toast.success / toast.error)
    - getSaturationState(data): calcula estado visual
    - formatLastScreened(dateStr): "Último triado hoje/há N dias"
    - getRecommendationText(rec): texto amigável
    - handleUnlock(): POST unlock-pipeline com action="increase_threshold"
    - handleTemporaryUnlock(): POST unlock-pipeline com action="disable_temporarily"
  
  Layout do Popover:
    ┌──────────────────────────────────────┐
    │ Saturação do Pipeline               │
    ├──────────────────────────────────────┤
    │ Pool Orgânico: 42/20 (🔴 210%)     │
    │ Pool Sourcing: 0/20 (🟢 0%)        │
    ├──────────────────────────────────────┤
    │ Na fila: 5 candidatos               │
    │ Último triado: há 2 dias            │
    ├──────────────────────────────────────┤
    │ Recomendação: "Agendar entrevistas  │
    │ antes de desbloquear"               │
    ├──────────────────────────────────────┤
    │ [+10 Vagas] [Desbloquear 24h]       │
    │ Ver Configurações →                 │
    └──────────────────────────────────────┘

DoD:
  - [x] Badge renderiza com estado correto (saturated/almost/normal)
  - [x] Popover mostra pools orgânico e sourcing separados
  - [x] Botão "+N" chama unlock-pipeline e refetch após sucesso
  - [x] Botão "Desbloquear Nh" chama unlock-pipeline temporário
  - [x] Link "Ver Configurações" navega corretamente
  - [x] Toast de feedback após ações
  - [x] Dark mode funcional
  - [ ] Responsive (mobile-friendly)

Criterios de Aceitacao:
  - [x] Vaga com 42 orgânicos / threshold 20 → badge vermelho "42/20"
  - [x] Vaga com 18 orgânicos / threshold 20 → badge amarelo "18/20"
  - [x] Vaga com 5 orgânicos / threshold 20 → badge verde "5/20"
  - [x] Click no badge abre popover com detalhes dos 2 pools
  - [x] Botão "+10" incrementa threshold e mostra toast "Thresholds updated"
  - [x] Valores de +N e Nh vêm dinâmicos da API (unlock_increment, unlock_hours)

Como Testar:
  1. Abrir Kanban de vaga com candidatos
  2. Verificar badge de saturação no header
  3. Clicar no badge → popover abre com detalhes
  4. Clicar "+10 Vagas" → threshold incrementa, badge atualiza
  5. Verificar dark mode (alternar tema)

Arquivos de Referencia (Prototipo LIA):
  - componente: plataforma-lia/src/components/kanban/components/SaturationBadge.tsx (267L)
  - integração: plataforma-lia/src/components/pages/job-kanban-page.tsx (usa <SaturationBadge jobId={...} />)
  - proxy: plataforma-lia/src/app/api/backend-proxy/job-vacancies/[jobId]/saturation-status/route.ts
```

---

### SAT-003: Configuração Global de Saturação (Settings UI)

```yaml
Titulo: "[Saturação] Seção de Configuração no Card Triagem (Settings → Pipeline)"
Tipo: Feature
Area: Frontend + Backend
Sprint: S1
Pontos: 5
Prioridade: Alta
Epic: É30
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend + Backend)
Fase: MVP Alpha 1
Tags: [frontend, settings, configuração, saturação, design-system]
Dependências: SAT-001

Descricao: |
  Adicionar seção "Controle de Saturação" no card "Triagem" da página
  de Configurações → Pipeline de Recrutamento. A seção contém 4 campos
  numéricos editáveis que controlam os defaults globais da empresa:
  1. Limite Inscrições Orgânicas (web/whatsapp): default 20
  2. Limite Busca Ativa (sourcing): default 20
  3. Incremento de Desbloqueio: default +10
  4. Horas de Desbloqueio Temporário: default 24h
  
  Os valores são salvos via PUT /api/v1/settings/saturation e carregados
  via GET /api/v1/settings/saturation. Cada campo usa input type="number"
  com validação de range (1-500 para thresholds, 1-100 para increment,
  1-168 para hours).
  
  O card Triagem já existe em StageCard.tsx — a seção de saturação é
  uma sub-seção colapsável com ícone de Gauge.

Historia de Usuario: |
  Como recrutador ou admin, eu quero configurar os limites de saturação
  globais da empresa, para que todas as novas vagas herdem esses valores.

Regras de Negocio:
  1. Valores alterados afetam APENAS vagas futuras (não retroativo)
  2. Vagas existentes mantêm seus overrides em governance_rules
  3. Validação client-side: min 1, max varia por campo
  4. Validação server-side: Pydantic com Field(ge=1, le=500)
  5. Exibir toast de sucesso/erro após salvar
  6. Loading state durante fetch e save

Requisitos Tecnicos:
  Frontend:
    - Localização: dentro do StageCard.tsx, na seção do card "Triagem"
    - Sub-seção colapsável: ChevronDown/ChevronRight toggle
    - Ícone: Gauge (lucide-react) ao lado do título "Controle de Saturação"
    - 4 campos Input type="number" com labels descritivos
    - Fetch: GET /api/backend-proxy/settings/saturation/ ao abrir seção
    - Save: PUT /api/backend-proxy/settings/saturation/ ao alterar valor
    - Toast: sonner para feedback
    - Design: bg-gray-50 dark:bg-gray-900 para seção diferenciada
  
  Backend:
    - Já implementado em SAT-001 (endpoints GET/PUT /settings/saturation)

DoD:
  - [x] Seção "Controle de Saturação" visível no card Triagem
  - [x] 4 campos editáveis com valores carregados da API
  - [x] Alterações salvam automaticamente ou com botão "Salvar"
  - [x] Validação de range no frontend e backend
  - [x] Toast de feedback
  - [x] Dark mode funcional

Criterios de Aceitacao:
  - [x] Abrir Configurações → Pipeline → Triagem → ver 4 campos de saturação
  - [x] Alterar "Limite Orgânico" para 30 → salva → recarregar → valor 30
  - [x] Inserir valor 0 → validação impede (mínimo 1)
  - [x] Inserir valor 600 → validação impede (máximo 500)

Como Testar:
  1. Navegar para /configuracoes
  2. Encontrar card "Triagem" no pipeline
  3. Expandir seção "Controle de Saturação"
  4. Alterar valores e verificar persistência
  5. Verificar que vaga existente não é afetada

Arquivos de Referencia (Prototipo LIA):
  - componente: plataforma-lia/src/components/settings/StageCard.tsx (855L — seção de saturação dentro)
  - proxy: plataforma-lia/src/app/api/backend-proxy/settings/saturation/route.ts
```

---

### SAT-004: Badges de Origem nos Cards do Kanban

```yaml
Titulo: "[Saturação] Badges de Origem — Web, WhatsApp, Busca, ATS, Aguardando"
Tipo: Feature
Area: Frontend
Sprint: S1
Pontos: 3
Prioridade: Média
Epic: É30
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend)
Fase: MVP Alpha 1
Tags: [frontend, kanban, componente, ux]
Dependências: SAT-001

Descricao: |
  Cada card de candidato no Kanban exibe um badge colorido indicando
  a origem/canal de entrada do candidato:
  - 🔵 "Web" (azul) — origin = "web"
  - 🟢 "WhatsApp" (verde) — origin = "whatsapp"
  - ⚫ "Busca" (cinza) — origin = "sourcing"
  - 🟣 "ATS" (roxo) — origin = "ats"
  - 🟡 "Aguardando" (âmbar) — status = "awaiting_screening"
  
  O badge de "Aguardando" tem prioridade sobre o badge de origem
  quando o candidato está na fila de espera.

Historia de Usuario: |
  Como recrutador, eu quero ver de onde cada candidato veio, para
  entender a composição do pipeline e a eficácia de cada canal.

Requisitos Tecnicos:
  Frontend:
    - Componente OriginBadge com prop origin: string e status: string
    - Renderiza dentro do card de candidato no Kanban
    - Cores por origin: web→blue, whatsapp→green, sourcing→gray,
      ats→purple, awaiting→amber
    - Badge pequeno: text-[10px], px-1.5, py-0.5, rounded-full
    - Campo origin vem do backend em VacancyCandidate.origin

DoD:
  - [x] Badge renderiza para todas as 5 origens
  - [x] Cores corretas por tipo
  - [x] "Aguardando" tem prioridade sobre origem
  - [x] Dark mode funcional

Criterios de Aceitacao:
  - [x] Candidato com origin="web" mostra badge azul "Web"
  - [x] Candidato na fila mostra badge âmbar "Aguardando" (não "Web")
  - [x] Badge é pequeno e não interfere no layout do card

Arquivos de Referencia (Prototipo LIA):
  - componente: plataforma-lia/src/components/kanban/components/index.ts (exporta badges)
  - integração: plataforma-lia/src/components/pages/job-kanban-page.tsx
```

---

### SAT-005: Fila de Espera com Retomada Automática

```yaml
Titulo: "[Saturação] Fila de Espera — Status awaiting_screening + Promoção Automática"
Tipo: Feature
Area: Backend
Sprint: S2
Pontos: 8
Prioridade: Crítica
Epic: É30
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Backend)
Fase: MVP Alpha 1
Tags: [backend, automação, fila, comunicação, saturação]
Dependências: SAT-001, COM-001

Descricao: |
  Sistema de fila de espera para candidatos que chegam quando o pool
  está saturado. Candidatos recebem status "awaiting_screening" e são
  promovidos automaticamente quando slots abrem.
  
  A função process_screening_queue() é o motor de promoção:
  1. Busca candidatos com status "awaiting_screening" na vaga
  2. Ordena por: lia_score DESC NULLS LAST, created_at ASC
     (prioriza melhor score, desempate por antiguidade)
  3. Para cada candidato (até max_promote):
     a. Muda status → screening
     b. Tenta enviar convite WhatsApp (se há conversa existente)
     c. Se não há WhatsApp: envia convite multicanal via CommunicationDispatcher
     d. Grava metadata: promoted_from_queue_at, invite_channel, invite_sent
  4. Commit e retorna lista de promovidos
  
  Triggers de promoção:
  - unlock-pipeline (increase_threshold ou disable_temporarily)
  - Candidato sai do pool (rejeitado, desistiu, withdrawn)
  - Chamada manual via POST /process-queue

Historia de Usuario: |
  Como candidato, eu quero ser automaticamente convidado para triagem
  quando uma vaga abrir, sem precisar verificar manualmente.

Regras de Negocio:
  1. Prioridade da fila: score > data de inscrição
  2. Convite tenta WhatsApp primeiro (se há conversa prévia)
  3. Fallback para email + WhatsApp via dispatcher
  4. Candidato promovido recebe link de triagem
  5. metadata.promoted_from_queue_at registra momento da promoção
  6. max_promote tem range 1-50 (default 1)

Requisitos Tecnicos:
  Backend:
    - Função: process_screening_queue(db, vacancy_id, company_id, max_promote)
    - Localização: automation_handlers.py (linha ~919)
    - Queries: SELECT vacancy_candidates WHERE status='awaiting_screening'
      ORDER BY lia_score DESC NULLS LAST, created_at ASC LIMIT max_promote
    - Para cada candidato:
      - SELECT candidate WHERE id = vc.candidate_id (dados de contato)
      - Tenta WhatsApp via WhatsAppConversation (se exists e active)
      - Fallback: Email via candidate_feedback_service.send_gate_feedback("screening_invited")
    - Mensagem WhatsApp: "Olá, {nome}! 👋\n\nTemos uma ótima notícia!
      Agora há uma vaga disponível para continuar o processo de triagem
      para *{job_title}*.\n\nVamos continuar? Responda *SIM*! 🚀"
    - Email subject: "[WeDOTalent] Convite para triagem — {vacancy_title}"
    - Email body: Template canônico via _GATE_BODIES["screening_invited"]
    - screening_link: "/triagem/{screening_invite_token}" (token do additional_data)
    - job_title e company_name carregados ANTES das branches de canal (evita NameError)
    - Token de triagem: consumido do additional_data.screening_invite_token;
      se ausente (candidato legado), gera novo via secrets.token_urlsafe(32)

  ⚠️ Bugs corrigidos na implementação:
    - job_title era definido apenas dentro do bloco WhatsApp, causando NameError
      para candidatos sem WhatsApp (corrigido: carregamento movido para antes das branches)
    - CommunicationDispatcher substituído por send_gate_feedback canônico (consistência)

DoD:
  - [x] process_screening_queue funcional com ordenação correta
  - [x] Convite WhatsApp enviado se conversa existente
  - [x] Fallback para email via send_gate_feedback (não CommunicationDispatcher)
  - [x] metadata registrada (promoted_from_queue_at, invite_channel)
  - [x] Chamada automática após unlock-pipeline
  - [x] Endpoint manual POST /process-queue funcional
  - [ ] Testes unitários para a função

Criterios de Aceitacao:
  - [x] 5 candidatos na fila → unlock +10 → 5 candidatos promovidos
  - [x] Candidato com maior score é promovido primeiro
  - [x] Candidato recebe convite com link /triagem/{token}
  - [x] metadata mostra promoted_from_queue_at correto

Como Testar:
  1. Criar vaga saturada (20 orgânicos, threshold 20)
  2. Adicionar 5 candidatos → status "awaiting_screening"
  3. POST /unlock-pipeline { action: "increase_threshold", new_threshold: 30 }
  4. Verificar que 5 candidatos foram promovidos (status → screening)
  5. Verificar logs de envio de convite

Inteligencia e Automacao:
  Agentes Envolvidos:
    - AutomationReActAgent (domain=automation): Orquestra promoção da fila como tarefa automatizada
    - CommunicationReActAgent (domain=communication): Pode ser acionado para personalizar convites
  Tools Utilizadas:
    - schedule_secondary_task: Agenda promoção como task secundária após unlock
    - send_communication: Envia convite multicanal (WhatsApp/email)
  Servicos IA:
    - candidate_feedback_service.send_gate_feedback("screening_invited"):
      Gera email de convite com template canônico _GATE_BODIES["screening_invited"]
    - LIAScoreService: lia_score é usado para priorizar fila (ORDER BY lia_score DESC)
  Modelo LLM: Nenhum direto — ordenação e promoção são determinísticas
  Governanca e Compliance:
    - PolicyEngine: Regra "communication_hours" (08h-20h) limita horário de envio de convites
    - PII Masking: PIIMaskingFilter redige email/telefone nos logs de envio (LGPD Art. 46)
    - Audit Trail: promoted_from_queue_at + invite_channel registrados em additional_data (SOX/ISO 27001)
    - ConsentChecker: Soft enforcement — se consent ausente, loga warning mas prossegue;
      se consent revogado, bloqueia envio (HTTP 451)
  Fairness e Bias:
    - Priorização por lia_score + created_at (FIFO como desempate) — sem critérios demográficos
    - BiasAuditService: Recomendado gerar snapshot de distribuição demográfica dos promovidos
    - FairnessGuard: Não se aplica diretamente (sem query de busca de candidatos)
  Automacoes/Triggers:
    - Trigger 1: unlock-pipeline (POST /unlock-pipeline) → chama process_screening_queue
    - Trigger 2: Candidato sai do pool ativo (rejected/withdrawn) → reavalia saturação
    - Trigger 3: POST /process-queue (chamada manual pelo recrutador)
    - AutomationScheduler: auto_complete_expired_screenings roda a cada hora
  Fallbacks:
    - WhatsApp falha → fallback para email via send_gate_feedback
    - Email falha → invite_sent=False registrado, candidato permanece na fila
    - Token ausente (candidato legado) → gera novo via secrets.token_urlsafe(32)

Arquivos de Referencia (Prototipo LIA):
  - função: lia-agent-system/app/domains/automation/services/automation_handlers.py (linhas 919-1080)
  - endpoint: lia-agent-system/app/api/v1/saturation.py (linhas 396-420, POST /process-queue)
  - dispatcher: lia-agent-system/app/domains/communication/services/communication_dispatcher.py
  - feedback: lia-agent-system/app/services/candidate_feedback_service.py (send_gate_feedback)
  - score: lia-agent-system/app/services/lia_score_service.py (LIAScoreService)
  - pii: lia-agent-system/app/shared/pii_masking.py (PIIMaskingFilter)
  - consent: lia-agent-system/app/services/consent_checker_service.py
```

---

### SAT-006: Override Manual do Recrutador

```yaml
Titulo: "[Saturação] Override Manual — Recrutador Aprova Candidato da Fila"
Tipo: Feature
Area: Backend + Frontend
Sprint: S2
Pontos: 5
Prioridade: Alta
Epic: É30
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Backend + Frontend)
Fase: MVP Alpha 1
Tags: [backend, frontend, kanban, automação]
Dependências: SAT-005, COM-001

Descricao: |
  Permite ao recrutador aprovar manualmente um candidato da fila de
  espera (status "awaiting_screening"), ignorando a ordem da fila.
  
  Função handle_recruiter_override_approve():
  1. Valida que o candidato está em awaiting_screening
  2. Muda status → screening
  3. Envia convite multicanal (email + WhatsApp)
  4. Registra atividade "recruiter_override_approve"
  5. Grava recruiter_override_at no additional_data do VacancyCandidate

Historia de Usuario: |
  Como recrutador, eu quero poder priorizar um candidato específico
  da fila, para que perfis excepcionais não esperem na ordem normal.

Requisitos Tecnicos:
  Backend:
    - Função: handle_recruiter_override_approve(db, candidate_id, vacancy_id, company_id)
    - Localização: automation_handlers.py (linha ~1074)
    - Validação: vc.status == "awaiting_screening" (senão retorna error)
    - Promoção: Chama process_screening_queue(max_promote=1) internamente
    - Convite WhatsApp: se conversa ativa, envia mensagem direta
    - Convite Email: candidate_feedback_service.send_gate_feedback("screening_invited")
    - Link: /triagem/{screening_invite_token} (consome do additional_data ou gera novo)
    - Activity: activity_type="recruiter_override_approve"
  Frontend:
    - Botão "Aprovar" no card do candidato com status "awaiting_screening"
    - Confirmação antes de executar (modal simples)
    - Refetch do kanban após ação

DoD:
  - [x] Função override funcional
  - [x] Convite via send_gate_feedback canônico (email) ou WhatsApp direto
  - [x] Atividade registrada
  - [x] Botão no frontend com confirmação
  - [x] Badge muda de "Aguardando" para o normal

Criterios de Aceitacao:
  - [x] Candidato na fila → override → status muda para screening
  - [x] Candidato recebe convite por email (send_gate_feedback) ou WhatsApp
  - [x] Activity feed mostra "Override manual pelo recrutador"
  - [x] Candidato sem contato → erro amigável no toast (frontend)

Inteligencia e Automacao:
  Agentes Envolvidos:
    - AutomationReActAgent (domain=automation): Executa override como decompose_task
    - KanbanReActAgent (domain=kanban): Atualiza visualização do pipeline após override
  Tools Utilizadas:
    - update_candidate_stage: Move candidato de awaiting_screening → screening
    - send_communication: Envia convite multicanal pós-override
  Servicos IA:
    - process_screening_queue(max_promote=1): Internamente chamado — mesmo motor de promoção
    - send_gate_feedback("screening_invited"): Email canônico de convite
  Modelo LLM: Nenhum — decisão é 100% do recrutador humano
  Governanca e Compliance:
    - Audit Trail: activity_type="recruiter_override_approve" registrado com user_id do recrutador
    - recruiter_override_at gravado em additional_data (rastreabilidade SOX)
    - PolicyEngine: override NÃO desrespeita "max_candidates_per_vacancy" (500) — apenas pula fila
    - PII Masking: Email do candidato mascarado nos logs
  Fairness e Bias:
    - Override manual é decisão humana — FairnessGuard não bloqueia, mas BiasAuditService
      deve registrar overrides para análise posterior de padrões discriminatórios
    - Recomendação: Dashboard de overrides por recrutador + distribuição demográfica
  Fallbacks:
    - Candidato não está em awaiting_screening → retorna error (validação pré-override)
    - WhatsApp indisponível → fallback para email via send_gate_feedback
    - Email falha → registra invite_sent=False, candidato já foi promovido (status=screening)

Arquivos de Referencia (Prototipo LIA):
  - função: lia-agent-system/app/domains/automation/services/automation_handlers.py (linhas 1074-1250)
  - feedback: lia-agent-system/app/services/candidate_feedback_service.py
  - pii: lia-agent-system/app/shared/pii_masking.py
```

---

### SAT-007: Máquina de Estados Gate 1 — Inscrição Web → Triagem

```yaml
Titulo: "[Saturação] Gate 1 — Máquina de Estados da Inscrição Web até Triagem WSI"
Tipo: Technical Debt / Fix
Area: Backend
Sprint: S1
Pontos: 5
Prioridade: Crítica
Epic: É30
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Backend)
```

**Contexto:**

Dois endpoints aceitam candidaturas web — ambos devem respeitar o mesmo
fluxo Gate 1 para evitar bypass da triagem WSI:

| Endpoint | Arquivo | Uso |
|----------|---------|-----|
| `POST /api/v1/applications/apply/{vacancy_id}` | `applications.py` | Formulário de candidatura (mobile/SPA) |
| `POST /api/v1/vacancies/{id}/apply-web` | `job_vacancies.py` | Formulário de inscrição web público |

**Máquina de estados Gate 1:**

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   INSCRIÇÃO WEB                                                     │
│   (qualquer endpoint)                                               │
│        │                                                            │
│        ▼                                                            │
│   ┌──────────────┐     adherence < 50%    ┌────────────────────┐   │
│   │ Calcula Score │ ────────────────────── │ Feedback + Rejeição│   │
│   │ (LIA Score)   │                        │ (low_adherence)     │   │
│   └──────┬───────┘                        └────────────────────┘   │
│          │ adherence ≥ 50%                                          │
│          ▼                                                          │
│   ┌──────────────────┐                                              │
│   │ Verifica Saturação│                                             │
│   │ (threshold_web)   │                                             │
│   └──────┬───────────┘                                              │
│          │                                                          │
│    ┌─────┴──────┐                                                   │
│    │             │                                                   │
│    ▼ NÃO sat.   ▼ SATURADO                                         │
│ ┌──────────┐  ┌───────────────────┐                                 │
│ │ status=  │  │ status=           │                                 │
│ │ "applied"│  │ "awaiting_screen."│                                 │
│ │ stage=   │  │ stage=            │                                 │
│ │ "pending │  │ "pending_gate1"   │                                 │
│ │  _gate1" │  │                   │                                 │
│ └────┬─────┘  └────────┬──────────┘                                 │
│      │                 │                                            │
│      │ (promoção       │ Entra na FILA de espera                    │
│      │  imediata*)     │ (process_screening_queue)                  │
│      │                 │                                            │
│      │                 │  Quando abrir capacidade:                  │
│      │                 │  - Saturação natural (outro sai)           │
│      │                 │  - Recruiter override (SAT-006)            │
│      │                 │  - Aumentar limite (SaturationBadge)       │
│      │                 │  - Desbloqueio temporário (24h)            │
│      │                 │                                            │
│      ▼                 ▼                                            │
│   ┌────────────────────────┐                                        │
│   │ status = "screening"   │                                        │
│   │ stage  = "screening"   │                                        │
│   │ Convite enviado via:   │                                        │
│   │  - WhatsApp (se conv.  │                                        │
│   │    ativa existe)       │                                        │
│   │  - Email (send_gate_   │                                        │
│   │    feedback canônico)  │                                        │
│   └────────────┬───────────┘                                        │
│                │                                                    │
│                ▼                                                    │
│   ┌────────────────────────┐                                        │
│   │ Candidato acessa       │                                        │
│   │ /triagem/{token}       │                                        │
│   │ Inicia Chat WSI        │                                        │
│   └────────────────────────┘                                        │
│                                                                     │
│   (*) Candidatos em pipeline não-saturado recebem convite direto    │
│   via automação imediata, sem passar pela fila de espera.           │
│                                                                     │
│   DADOS GERADOS NA INSCRIÇÃO:                                      │
│   additional_data = {                                               │
│     "screening_invite_token": token_urlsafe(32),                   │
│     "applied_at": ISO timestamp,                                   │
│     "is_saturated_at_apply": bool                                  │
│   }                                                                 │
│                                                                     │
│   DADOS ADICIONADOS NA PROMOÇÃO:                                   │
│   additional_data += {                                              │
│     "promoted_from_queue_at": ISO timestamp,                       │
│     "invite_channel": "whatsapp" | "email",                       │
│     "invite_sent": bool                                            │
│   }                                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

**Token de triagem (`screening_invite_token`):**
- Gerado na inscrição via `secrets.token_urlsafe(32)` — 256 bits de entropia
- Salvo em `additional_data` do `VacancyCandidate`
- Consumido por `process_screening_queue` ao montar o link `/triagem/{token}`
- Se token ausente (candidatos legados), o sistema gera um novo no momento da promoção
- Link canônico: `/triagem/{screening_invite_token}` (não `/triagem/{vacancy_id}?candidate=...`)

**Email de convite — mecanismo canônico:**
- Função: `candidate_feedback_service.send_gate_feedback("screening_invited", ...)`
- Template: `_GATE_BODIES["screening_invited"]` em `candidate_feedback_service.py` L610
- Subject: `[WeDOTalent] Convite para triagem — {vacancy_title}`
- Inclui `screening_url` como variável interpolada

```yaml
Dependencias:
  - SAT-001 (modelo de dados com thresholds)
  - SAT-005 (fila de espera com process_screening_queue)
  - INS-001 (formulário de inscrição pública)

Tasks:
  - [x] Ambos endpoints usam stage="pending_gate1"
  - [x] Ambos endpoints geram screening_invite_token
  - [x] Ambos endpoints verificam saturação e definem status correto
  - [x] process_screening_queue consome token do additional_data
  - [x] Link de triagem usa formato /triagem/{token} (não IDs diretos)
  - [x] Email de convite usa send_gate_feedback canônico (não inline)
  - [x] Fallback: gera token se ausente em candidatos legados
  - [x] Log: PII mascarado nos logs de envio

Criterios de Aceitacao:
  - [x] Candidato via applications.py com pipeline saturado → status=awaiting_screening
  - [x] Candidato via job_vacancies.py com pipeline saturado → status=awaiting_screening
  - [x] Candidato promovido da fila → recebe email com link /triagem/{token}
  - [x] Token é o mesmo gerado na inscrição (não um novo)
  - [x] Candidato legado (sem token) → sistema gera novo token na promoção

Bugs Corrigidos (code review):
  1. Import errado em applications.py: `from app.models.company_profile` → `from app.models.company`
     (import inexistente fazia o fallback forçar is_saturated=True, enfileirando todos)
  2. NameError em process_screening_queue: job_title definido apenas no bloco WhatsApp,
     causando crash no branch de email para candidatos sem WhatsApp
     (corrigido: job_title + company_name carregados antes das branches de canal)
  3. Fallback de saturação inconsistente: applications.py defaultava is_saturated=True,
     job_vacancies.py defaultava False — ambos agora defaultam False (permite inscrição)

Inteligencia e Automacao:
  Agentes Envolvidos:
    - PipelineReActAgent (domain=pipeline): Gerencia transições de stage (pending_gate1 → screening)
    - AutomationReActAgent (domain=automation): Executa process_screening_queue como task agendada
    - CommunicationReActAgent (domain=communication): Dispara convites multicanal
  Tools Utilizadas:
    - update_candidate_stage: Transição pending_gate1 → screening
    - send_communication: Convite multicanal (WhatsApp + email)
    - add_candidate_to_vacancy: Associa candidato à vaga com stage/status corretos
  Servicos IA:
    - LIAScoreService: Calcula lia_score na inscrição (usado para priorização da fila)
      Formula: Ranking_Score = (Rubricas * W_rub + WSI * W_wsi + Prerequisites * W_pre
      + Recency * W_rec + Calibration) * Completeness_Factor
    - candidate_feedback_service.send_gate_feedback("screening_invited"): Email canônico
    - CVScoringService: Score de aderência do CV contra rubricas da vaga (threshold 50%)
  Modelo LLM:
    - Claude (Anthropic): Scoring de CV + aderência (structured output)
    - Nenhum no fluxo de saturação em si (determinístico)
  Governanca e Compliance:
    - ConsentChecker: Verificação de consentimento para ai_screening antes de processar
      Soft enforcement: consent ausente → warning + prossegue; revogado → HTTP 451
    - PII Masking: strip_pii_for_llm_prompt() antes de enviar CV ao LLM (LGPD Art. 12)
    - PII Masking: PIIMaskingFilter nos logs de envio de convite (LGPD Art. 46)
    - Audit Trail: additional_data registra todo o histórico de estados para SOX/ISO 27001:
      screening_invite_token, applied_at, is_saturated_at_apply, promoted_from_queue_at
    - PolicyEngine: max_candidates_per_vacancy (500) como teto absoluto
    - EscalationRules: Se candidato fica >7 dias em awaiting_screening → escalation automático
  Fairness e Bias:
    - FairnessGuard: Filtro ativo no scoring de CV — bloqueia critérios discriminatórios
      (gênero, raça, idade, religião, orientação sexual, deficiência)
    - BiasAuditService: Snapshot de distribuição Four-Fifths Rule para inscritos vs promovidos
    - Priorização da fila: lia_score + FIFO (created_at) — sem critérios demográficos
    - Dois endpoints idênticos: Mesmo comportamento evita disparidade por canal de entrada
  Automacoes/Triggers:
    - Inscrição web → score adherence → saturação check → status/stage automáticos
    - Promoção da fila: process_screening_queue → convite WhatsApp/email
    - Override manual: handle_recruiter_override_approve → promoção individual
    - AutomationScheduler: check_inactive_candidates (7 dias sem atividade)
  Fallbacks:
    - Saturação check falha → is_saturated=False (permite inscrição, não penaliza candidato)
    - Token ausente → gera novo na promoção (candidatos legados)
    - WhatsApp falha → email; email falha → invite_sent=False
    - LLM scoring falha → lia_score=NULL (candidato vai para fim da fila, FIFO decide)

Arquivos de Referencia (Prototipo LIA):
  - applications.py: lia-agent-system/app/api/v1/applications.py (linhas 261-310)
  - job_vacancies.py: lia-agent-system/app/api/v1/job_vacancies.py (linhas 3668-3740)
  - automation_handlers.py: lia-agent-system/app/domains/automation/services/automation_handlers.py (linhas 919-1070)
  - candidate_feedback_service.py: lia-agent-system/app/services/candidate_feedback_service.py (linhas 598-730)
  - lia_score: lia-agent-system/app/services/lia_score_service.py
  - cv_scoring: lia-agent-system/app/services/cv_scoring_service.py
  - fairness: lia-agent-system/app/shared/compliance/fairness_guard.py
  - bias_audit: lia-agent-system/app/services/bias_audit_service.py
  - consent: lia-agent-system/app/services/consent_checker_service.py
  - pii: lia-agent-system/app/shared/pii_masking.py
  - policy: lia-agent-system/app/orchestrator/policy_engine.py
```

---

## 7. Cards Sprint TRI — Chat Web de Triagem (WSI + IA Conversacional)

### TRI-001: Tipos e Interfaces TypeScript

```yaml
Titulo: "[Chat Web] Tipos e Interfaces TypeScript — types.ts Completo"
Tipo: Feature
Area: Frontend
Sprint: S1
Pontos: 3
Prioridade: Crítica
Epic: É31
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend)
Fase: MVP Alpha 1
Tags: [frontend, typescript, tipos, triagem]
Dependências: Nenhuma

Descricao: |
  Arquivo de tipos TypeScript (~125L) que define todas as interfaces
  usadas pela feature de triagem:
  
  Types:
    TriagemStatus = "invited"|"started"|"in_progress"|"completed"|"expired"|"cancelled"
    TriagemMessageRole = "lia"|"candidate"
    TriagemMessageType = "text"|"multiple_choice"|"likert_scale"|"audio"|"system"
    TriagemPageState = "loading"|"error"|"welcome"|"chat"|"confirmation"|"completion"
  
  Interfaces:
    WSIProgress { currentBlock, totalBlocks, currentBlockName,
      questionsAnswered, totalQuestions, estimatedMinutesRemaining }
    TriagemSession { id, token, status, candidateId, candidateName,
      jobId, jobTitle, companyName, companyLogoUrl, progress,
      createdAt, expiresAt, startedAt, completedAt,
      wsiFinalScore, recommendation }
    TriagemMessage { id, sessionId, role, type, content,
      options, selectedOption, likertValue, likertLabels,
      timestamp, blockIndex, blockName, audioUrl }
    TriagemConfig { companyName, companyLogoUrl, jobTitle,
      candidateName, estimatedMinutes, privacyPolicyUrl,
      audioEnabled, feedbackEnabled, welcomeMessage, voiceMode }
    TriagemError { code, message }
    TriagemCompletionSummary { questionsAnswered, durationMinutes, nextSteps[] }
    SendMessagePayload { content, type, selectedOption?, likertValue?, voiceMode? }
    UseTriagemChatReturn { pageState, session, config, messages,
      progress, error, completionSummary, isLiaTyping, isSending,
      isLoadingHistory, initSession, startChat, sendMessage,
      completeSession, reviewSession, loadHistory }

DoD:
  - [x] Todos os types e interfaces definidos
  - [x] Exportados corretamente para uso em componentes
  - [x] Sem dependências externas (apenas tipos nativos)

Arquivos de Referencia (Prototipo LIA):
  - file: plataforma-lia/src/components/triagem/types.ts (125L — copiar diretamente)
```

---

### TRI-002: Hook useTriagemChat — Gerenciamento de Estado

```yaml
Titulo: "[Chat Web] Hook useTriagemChat — State Management + API Integration (~537L)"
Tipo: Feature
Area: Frontend
Sprint: S2
Pontos: 13
Prioridade: Crítica
Epic: É31
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend)
Fase: MVP Alpha 1
Tags: [frontend, hook, react, api, state-management, triagem]
Dependências: TRI-001, TRI-005

Descricao: |
  Hook React (~537L) que gerencia todo o ciclo de vida de uma sessão
  de triagem. É o "cérebro" do frontend do chat web.
  
  Responsabilidades:
  1. Validar token e carregar sessão (initSession)
  2. Iniciar conversa com opção de voz (startChat)
  3. Enviar mensagens com debounce e retry (sendMessage)
  4. Gerenciar progresso WSI (progress)
  5. Completar sessão (completeSession)
  6. Persistir estado local via localStorage
  7. Converter áudio base64 em blob URLs
  8. Mapear responses do backend para tipos TypeScript
  
  Funcionalidades robustas:
  - fetchWithTimeout: 30s timeout com AbortController
  - fetchWithRetry: até 2 retries com backoff exponencial (1s, 2s)
  - Debounce de envio: 300ms para evitar double-send
  - mapBackendMessage: converte snake_case → camelCase
  - mapBackendSession: converte session data
  - mapBackendProgress: converte progress data
  - mapErrorResponse: HTTP status → error codes amigáveis
  - localStorage persistence: salva messages + pageState por token
  - mountedRef: evita setState em componente desmontado

Historia de Usuario: |
  Como desenvolvedor, eu quero um hook centralizado que gerencie toda
  a comunicação com o backend de triagem, para que os componentes
  de UI sejam puramente visuais.

Requisitos Tecnicos:
  Frontend:
    - Hook: useTriagemChat(token: string): UseTriagemChatReturn
    - Estados: pageState, session, config, messages, progress, error,
        completionSummary, isLiaTyping, isSending, isLoadingHistory
    - API calls:
      GET  /api/backend-proxy/triagem/{token} → initSession
      POST /api/backend-proxy/triagem/{token}/start → startChat
      POST /api/backend-proxy/triagem/{token}/message → sendMessage
      POST /api/backend-proxy/triagem/{token}/complete → completeSession
      GET  /api/backend-proxy/triagem/{token}/history → loadHistory
    - base64ToAudioUrl(): converte audio_base64 em object URL (blob)
    - Timeout: 30s (TIMEOUT_MS)
    - Retries: 2 (MAX_RETRIES)
    - Debounce: 300ms (DEBOUNCE_MS)
    - localStorage key: "triagem_state_{token}"
    - Cleanup: URL.revokeObjectURL para audio blobs
    - voiceMode propagation: sendMessage inclui { voiceMode: isVoiceMode }
      (estado runtime do UI, não config inicial do servidor)

DoD:
  - [x] Hook funcional com todos os métodos
  - [x] fetchWithTimeout e fetchWithRetry implementados
  - [x] Conversão base64 → audio URL funcional
  - [x] localStorage persistence funcional
  - [x] Mapeamento snake_case → camelCase completo
  - [x] Error handling com códigos amigáveis
  - [x] voiceMode propagado em sendMessage

Criterios de Aceitacao:
  - [x] Token inválido → pageState="error", error.code="TOKEN_INVALID"
  - [x] Token expirado → pageState="error", error.code="TOKEN_EXPIRED"
  - [x] Sessão já completada → pageState="completion"
  - [x] Sessão in_progress → pageState="chat", mensagens restauradas
  - [x] Sessão invited → pageState="welcome"
  - [x] Envio de mensagem com retry → até 3 tentativas
  - [x] Fechar e reabrir página → mensagens restauradas do localStorage

Inteligencia e Automacao:
  Agentes Envolvidos:
    - Nenhum diretamente — hook é consumidor de APIs REST, não orquestra agentes
    - Indiretamente consome respostas do PipelineReActAgent (via backend screening endpoints)
  Tools Utilizadas: Nenhuma — hook consome endpoints REST, não invoca tools de agentes
  Servicos IA Consumidos (via REST):
    - TriagemSessionService: process_message() retorna pergunta_lia + scoring parcial
    - Intent classification: Backend classifica intent (ANSWER/QUESTION/GREETING/UNCLEAR)
    - TTS: Quando voiceMode=true, backend retorna audio_base64 na resposta
  Modelo LLM: Nenhum no frontend — toda IA roda no backend
  Governanca e Compliance:
    - Token-based auth: Sessão identificada por screening_invite_token (sem password/login)
    - localStorage: Mensagens persistidas localmente — dados PII do candidato em client-side
      ⚠️ Candidato deve poder limpar dados (LGPD direito de esquecimento)
    - fetchWithTimeout (30s): Previne travamento se backend não responder
    - fetchWithRetry (2 retries, backoff exponencial): Resiliência sem sobrecarregar backend
  Fairness e Bias:
    - Hook é agnóstico — apenas renderiza perguntas e respostas do backend
    - Determinismo: Backend garante que mesmas respostas geram mesmo score
  Fallbacks:
    - Backend offline → error.code="NETWORK_ERROR", mensagem amigável ao candidato
    - Token inválido → pageState="error" com orientação ao candidato
    - Sessão expirada → pageState="error" com mensagem específica
    - Audio base64 inválido → degrada para texto-only (sem crash)

Arquivos de Referencia (Prototipo LIA):
  - hook: plataforma-lia/src/hooks/use-triagem-chat.ts (537L — copiar e adaptar)
  - proxy: plataforma-lia/src/app/api/backend-proxy/triagem/[...path]/route.ts
```

---

### TRI-003: WelcomeCard — Tela de Boas-Vindas com Branding

```yaml
Titulo: "[Chat Web] WelcomeCard — Tela de Boas-Vindas com Branding da Empresa"
Tipo: Feature
Area: Frontend
Sprint: S2
Pontos: 3
Prioridade: Alta
Epic: É31
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend)
Fase: MVP Alpha 1
Tags: [frontend, componente, triagem, design-system, branding]
Dependências: TRI-001

Descricao: |
  Componente React (~101L) que é a primeira tela que o candidato vê.
  Exibe branding da empresa CLIENTE (não WeDo), título da vaga,
  mensagem personalizada da LIA com nome do candidato, e botões
  para iniciar conversa em modo texto ou voz.
  
  ⚠️ REGRA CRÍTICA: O logo e nome SEMPRE são da empresa cliente
  (config.companyName, config.companyLogoUrl), NUNCA do WeDo Talent.
  O candidato NÃO sabe que está usando a plataforma WeDo.

  Design System v4.2.1:
  - Botão principal: bg-gray-900 (dark: bg-gray-50)
  - Botão secundário (voz): border border-gray-900, bg-transparent
  - LIA icon: bg-[#60BED1]/10 (único uso de cyan)
  - Mensagem da LIA: fundo bg-[#60BED1]/10 com rounded-md
  - Tipografia: Open Sans (font-['Open_Sans',sans-serif])
  - Todos os cantos: rounded-md
  - Max width: max-w-md (448px)

Requisitos Tecnicos:
  Frontend:
    - Props: { config: TriagemConfig, onStart: (voiceMode?: boolean) => void,
        isStarting?: boolean, className?: string }
    - Seções:
      1. Logo/nome empresa (img ou fallback texto)
      2. Título da vaga (h1)
      3. Mensagem LIA com ícone (bg-[#60BED1]/10)
      4. Tempo estimado (Clock icon + config.estimatedMinutes)
      5. Botão "Iniciar Conversa" → onStart(false)
      6. Botão "Iniciar Conversa por Voz" → onStart(true)
         (só aparece se config.voiceMode === true)
      7. Link "Política de Privacidade" (Shield icon)
    - Acessibilidade: aria-label em todos os botões e link

DoD:
  - [x] Logo da empresa renderiza (img ou fallback texto)
  - [x] Nome do candidato personalizado na mensagem
  - [x] Botão de voz condicional (só se voiceMode=true)
  - [x] isStarting state desabilita botões e mostra "Iniciando..."
  - [x] Dark mode funcional
  - [ ] Acessibilidade completa (aria-labels)

Criterios de Aceitacao:
  - [x] Logo "TechCorp" aparece (não "WeDo Talent")
  - [x] "Olá, Maria! Eu sou a LIA 👋" com nome do candidato
  - [x] Botão voz aparece se config.voiceMode=true
  - [x] Botão voz NÃO aparece se config.voiceMode=false
  - [x] Click em "Iniciar Conversa" chama onStart(false)
  - [x] Click em "Iniciar Conversa por Voz" chama onStart(true)

Arquivos de Referencia (Prototipo LIA):
  - componente: plataforma-lia/src/components/triagem/WelcomeCard.tsx (101L)
  - lia-icon: plataforma-lia/src/components/ui/lia-icon.tsx
```

---

### TRI-004: MessageBubble — Bolha de Mensagem com Áudio

```yaml
Titulo: "[Chat Web] MessageBubble — Bolha de Mensagem com AudioPlayer e Animação"
Tipo: Feature
Area: Frontend
Sprint: S2
Pontos: 5
Prioridade: Alta
Epic: É31
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend)
Fase: MVP Alpha 1
Tags: [frontend, componente, triagem, áudio, design-system]
Dependências: TRI-001, VOZ-002

Descricao: |
  Componente React (~117L) que renderiza uma mensagem no chat.
  Layout diferenciado por role:
  - LIA (role="lia"): justify-start, bg-white border, LIAIcon à esquerda
  - Candidato (role="candidate"): justify-end, bg-gray-900, initials à direita
  
  Suporta áudio: se message.audioUrl presente, renderiza AudioPlayer
  abaixo do texto. Quando áudio está tocando, LIAIcon exibe animação
  de "speaking" (pulsação).
  
  Suporta markdown simples: **bold**, *italic*, \n → <br>
  (com sanitização XSS: escapeHtml antes de parsing)

Requisitos Tecnicos:
  Frontend:
    - Props: { message: TriagemMessage, candidateName?: string,
        className?: string, autoPlayAudio?: boolean }
    - Layout LIA: LIAIcon(size="sm", speaking={isAudioPlaying}) + bubble
    - Layout Candidato: bubble + initials circle (getInitials(name))
    - AudioPlayer: renderiza se role=lia && message.audioUrl
    - parseSimpleMarkdown(): escapeHtml() → **bold** → *italic* → \n
    - Timestamp: formatTimestamp(iso) → "14:30" (pt-BR)
    - Animação: animate-in fade-in slide-in-from-bottom-2 duration-300

DoD:
  - [x] Bolha de LIA renderiza com LIAIcon
  - [x] Bolha de candidato renderiza com initials
  - [x] AudioPlayer renderiza quando audioUrl presente
  - [x] LIAIcon pulsa durante reprodução de áudio
  - [x] Markdown simples funcional
  - [x] XSS prevention (escapeHtml)
  - [x] Dark mode funcional

Arquivos de Referencia (Prototipo LIA):
  - componente: plataforma-lia/src/components/triagem/MessageBubble.tsx (117L)
  - audio-player: plataforma-lia/src/components/ui/audio-player.tsx
  - lia-icon: plataforma-lia/src/components/ui/lia-icon.tsx
```

---

### TRI-005: Backend — TriagemSessionService (Motor de IA)

```yaml
Titulo: "[Chat Web] TriagemSessionService — Motor de IA Conversacional + WSI Scoring (~887L)"
Tipo: Feature
Area: Backend
Sprint: S2
Pontos: 21
Prioridade: Crítica
Epic: É31
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Backend)
Fase: MVP Alpha 1
Tags: [backend, ia, llm, scoring, triagem, wsi, voz]
Dependências: COM-001

Descricao: |
  Serviço Python (~887L) que é o motor de IA da triagem WSI via chat.
  Gerencia sessões, processa mensagens, gera perguntas contextuais,
  classifica intents, calcula scores determinísticos e integra TTS.
  
  Arquitetura de funções (16 funções/métodos):
  
  UTILITÁRIOS LLM:
    _generate_tts_audio(text) → Optional[str] (base64 audio)
      - Provider: OpenAI tts-1, voice "nova"
      - Formato: mp3, converte bytes → base64
      - Fallback: None se OpenAI não disponível
    
    _call_llm(prompt) → Optional[str]
      - Tenta Anthropic Claude Sonnet primeiro
      - Fallback Google Gemini
      - Fallback OpenAI GPT-4
      - Retorna None se todos falham
    
    _classify_intent(message, block_name, current_question) → str
      - Classifica: "ANSWER" | "QUESTION" | "GREETING"
      - Usa _call_llm com prompt específico
      - Default: "ANSWER" se LLM falha
    
    _generate_off_script_response(question, job_context) → str
      - Gera resposta para perguntas do candidato
      - Usa contexto da vaga/empresa
      - Retoma roteiro naturalmente
    
    _generate_contextual_question(block_name, previous_response, job_title, previous_questions) → str
      - Gera próxima pergunta CONTEXTUAL baseada na resposta anterior
      - Evita perguntas já feitas (previous_questions)
      - Adapta para o bloco WSI atual
  
  SCORING:
    _score_response_deterministic(response_text, block_type, competency) → Dict
      - Score baseado em keywords e indicadores de profundidade
      - Bloom taxonomy: 6 níveis (1-6 pts)
      - Dreyfus model: 5 níveis (1-5 pts)
      - ⚠️ NÃO usa random.uniform — 100% determinístico
      - Retorna: { score, bloom_level, dreyfus_level, indicators_found }
    
    _calculate_final_score(response_scores) → Tuple[float, str]
      - Pesos: Competências Técnicas e Resolução de Problemas = 2x
      - Score final: média ponderada normalizada para 0-10
      - Recommendation: ≥7.5 "approved", 5.0-7.4 "pending", <5.0 "rejected"
  
  CLASSE TriagemSessionService:
    validate_token(db, token) → Dict
      - Busca TriagemSession pelo token
      - Retorna status, metadados
    
    get_session_config(db, token) → Optional[Dict]
      - Retorna: session + config { companyName, companyLogoUrl, jobTitle,
        candidateName, estimatedMinutes, privacyPolicyUrl, audioEnabled,
        feedbackEnabled, welcomeMessage, voiceMode }
      - Config monta: branding da empresa cliente (nunca WeDo)
    
    create_session(db, token, ..., voice_mode) → Dict
      - Cria TriagemSession com dados do candidato e vaga
    
    start_session(db, token, voice_mode?) → Dict
      - Muda status → in_progress
      - Se voice_mode passado: grava session.voice_mode
      - Gera primeira mensagem (transição para bloco 1)
      - Se voice_mode: gera áudio TTS
      - Retorna { session, lia_message, progress }
    
    process_message(db, token, content, type, voice_mode?) → Dict
      - Resolve voice_mode: parâmetro > session.voice_mode
      - Classifica intent (_classify_intent)
      - Se ANSWER: score + próxima pergunta contextual
      - Se QUESTION: off-script response + retomada
      - Se voice_mode: gera TTS áudio
      - Retorna { lia_message, progress, audio_base64? }
    
    _generate_lia_response(db, session, content, type) → Dict
      - Lógica principal de geração de resposta
      - Gerencia transição entre blocos WSI
      - Acumula scores por bloco
      - Detecta completude do bloco
    
    _pre_completion_response(session, total_questions) → Dict
      - Mensagem antes de completar a triagem
    
    get_history(db, token) → Dict
      - Retorna todas as mensagens da sessão
    
    complete_session(db, token) → Dict
      - Calcula score final via _calculate_final_score
      - Grava wsi_final_score e recommendation na sessão
      - Chama _trigger_post_completion
    
    _trigger_post_completion(db, session) → Dict
      - Email de confirmação via CommunicationDispatcher
      - Notificação ao recrutador
      - Auto-move pipeline (score ≥ 7.5 → Entrevista)
      - Audit log

Historia de Usuario: |
  Como candidato, eu quero ter uma conversa natural com a LIA durante
  a triagem, onde ela me faz perguntas relevantes baseadas nas minhas
  respostas anteriores, não perguntas genéricas.

Regras de Negocio:
  1. Perguntas são geradas pelo LLM com base na resposta anterior
  2. Score é determinístico (Bloom/Dreyfus, sem randomização)
  3. Off-script: candidato pode fazer até 3 perguntas antes de retomada forçada
  4. Auto-move: score ≥ 7.5 → candidato avança para "Entrevista"
  5. Score < 7.5: cria sugestão para recrutador (não auto-rejeita)
  6. Branding: config SEMPRE mostra empresa cliente, não WeDo
  7. TTS: somente quando voiceMode=True (via OpenAI tts-1)
  8. LLM cascade: Anthropic → Gemini → OpenAI (3 fallbacks)
  9. Email de confirmação enviado via CommunicationDispatcher (real, não mock)

Requisitos Tecnicos:
  Backend:
    - Arquivo: triagem_session_service.py (~887L)
    - Dependências: openai (TTS), anthropic/gemini/openai (LLM)
    - Modelo: TriagemSession (SQLAlchemy)
    - Dispatcher: CommunicationDispatcher (pós-conclusão)
  
  Endpoints REST (via triagem router):
    GET    /api/v1/triagem/{token}           → validate + get_session_config
    POST   /api/v1/triagem/{token}/start     → start_session
    POST   /api/v1/triagem/{token}/message   → process_message
    POST   /api/v1/triagem/{token}/complete  → complete_session
    GET    /api/v1/triagem/{token}/history   → get_history
  
  Variáveis de Ambiente:
    ANTHROPIC_API_KEY — LLM primário (Claude Sonnet)
    GOOGLE_API_KEY — LLM fallback (Gemini)
    OPENAI_API_KEY — LLM fallback + TTS (tts-1)

DoD:
  - [x] TriagemSessionService com todos os 16 métodos
  - [x] Score determinístico via Bloom/Dreyfus (sem random)
  - [x] Intent classification (ANSWER/QUESTION/GREETING)
  - [x] Off-script handling com limite de 3 desvios
  - [x] TTS integration (OpenAI tts-1)
  - [x] LLM cascade (3 providers)
  - [x] Pós-conclusão: email real via dispatcher
  - [x] Auto-move pipeline (score ≥ 7.5)
  - [x] 5 endpoints REST funcionais
  - [ ] Testes unitários para scoring determinístico
  - [ ] Testes de integração para fluxo completo

Criterios de Aceitacao:
  - [x] Candidato responde → LIA faz pergunta contextual (não repetida)
  - [x] Candidato pergunta "qual o salário?" → LIA responde e retoma
  - [x] Mesma resposta → mesmo score (determinístico)
  - [x] Score 8.0 → candidato auto-move para Entrevista
  - [x] Score 6.5 → sugestão criada para recrutador
  - [x] voiceMode=true → resposta inclui audio_base64
  - [x] Após completar → email de confirmação enviado

Como Testar:
  1. Criar sessão: POST /triagem com token
  2. Start: POST /triagem/{token}/start { voice_mode: false }
  3. Enviar resposta: POST /triagem/{token}/message { content: "..." }
  4. Verificar que próxima pergunta é contextual
  5. Enviar pergunta: { content: "Qual o salário?" } → LIA responde
  6. Completar 7 blocos → verificar score final e email

Inteligencia e Automacao:
  Agentes Envolvidos:
    - PipelineReActAgent (domain=pipeline): Pode disparar run_wsi_screening via tool
    - AutomationReActAgent (domain=automation): Pós-conclusão, executa handle_screening_completed
    - CommunicationReActAgent (domain=communication): Despacha feedback/confirmação ao candidato
  Tools Utilizadas:
    - run_wsi_screening: Inicia sessão de triagem WSI para candidato (tool do PipelineReActAgent)
    - wsi_screening: Alias alternativo — mesma funcionalidade
    - get_candidate_wsi_scores: Consulta scores WSI de candidato já avaliado
    - send_feedback: Envia resultado de triagem ao candidato
    - update_candidate_stage: Auto-move para "Entrevista" se score ≥ 7.5
  Servicos IA:
    - TriagemSessionService.process_message():
      1. Classifica intent do candidato (ANSWER/QUESTION/GREETING/UNCLEAR)
      2. Se ANSWER: avalia resposta com rubrica WSI (Bloom/Dreyfus/Big5/CBI)
      3. Se QUESTION (off-script): gera resposta + retoma script
      4. Gera próxima pergunta contextual baseada em respostas anteriores
      5. Calcula score parcial a cada bloco (7 blocos total)
    - WSIService: Orquestra análise de JD, sugere competências, gera perguntas WSI
    - WSIDeterministicScorer: Scoring rule-based como baseline/validação do LLM scoring
    - WSIInterviewGraph (LangGraph): State machine para entrevistas síncronas — garante
      transições determinísticas e auditabilidade (compliance-ready)
    - LIAScoreService: Score unificado pós-triagem (fórmula Rubricas+WSI+Prerequisites+Recency)
    - CVScoringService: Score de CV contra rubricas da vaga (complementa WSI)
    - _generate_tts_audio(): OpenAI tts-1 para voz (se voiceMode=true)
  Modelos LLM:
    - Primário: Claude (Anthropic) — avaliação estruturada de respostas WSI, scoring
    - Secundário: Gemini (Google) — geração conversacional, intent classification, fallback
    - Terciário: OpenAI (gpt-4o) — fallback final para LLM tasks
    - TTS: OpenAI tts-1 (voice "nova") — geração de áudio em PT-BR
    - Cascade: Anthropic → Gemini → OpenAI (3 fallbacks automáticos)
  Governanca e Compliance:
    - ConsentChecker: Verificação de consentimento para ai_screening antes de iniciar sessão
      Soft enforcement: ausente → warning; revogado → HTTP 451 + bloqueia triagem
    - PII Masking: strip_pii_for_llm_prompt() em TODA resposta do candidato antes do LLM
      Remove: CPF, email, telefone, ano de formação, idade explícita, fragmentos de endereço
      Base legal: LGPD Art. 12 (dados anonimizados para processamento por terceiros)
    - PII Masking: PIIMaskingFilter nos logs de triagem (nome, email mascarados)
    - Audit Trail: TriagemSession model registra todas as interações para rastreabilidade
      Campos: messages_history (JSON), scores_by_block, final_score, completed_at
    - EU AI Act: Sistema classificado como HIGH-RISK (triagem automatizada de candidatos)
      Requer: explicabilidade do score, human-in-the-loop (recrutador revisa), audit trail
    - ModelDriftService: Monitora degradação dos modelos de scoring ao longo do tempo
  Fairness e Bias:
    - FairnessGuard: 3 camadas ativas durante toda triagem:
      1. Explicit Bias Detection (regex): Bloqueia critérios discriminatórios nas rubricas
      2. Implicit Bias Detection: Identifica termos problemáticos ("boa aparência", etc)
      3. Semantic Analysis (LLM): Detecta viés sutil nas perguntas geradas
    - WSIDeterministicScorer: Score rule-based como baseline — evita viés do LLM
    - BiasAuditService: Gera snapshots Four-Fifths Rule por 4 dimensões:
      Gender, Age Group, Disability, Region — sem PII nos stats (SOX/ISO 27001)
    - Determinismo: Mesma resposta → mesmo score (scorer determinístico valida LLM)
    - Off-script máximo: 3 perguntas antes de retomada forçada — evita manipulação
  Automacoes/Triggers:
    - Triagem completa → handle_screening_completed (automation_handlers.py)
      → CommunicationDispatcher despacha feedback multicanal
    - Score ≥ 7.5 → auto_move_to_interview (cria activity + move stage)
    - Score < 7.5 → cria sugestão para recrutador (NÃO auto-rejeita — human-in-the-loop)
    - _trigger_post_completion() → email de confirmação ao candidato
    - AutomationScheduler: auto_complete_expired_screenings (a cada hora)
  Fallbacks:
    - LLM cascade: Anthropic → Gemini → OpenAI (3 fallbacks)
    - TTS falha → resposta texto-only (chat funciona sem áudio)
    - Intent unclear → resposta genérica + retoma script
    - CommunicationDispatcher falha → log warning, não bloqueia conclusão

Arquivos de Referencia (Prototipo LIA):
  - serviço: lia-agent-system/app/services/triagem_session_service.py (887L — copiar e adaptar)
  - modelo: lia-agent-system/app/models/triagem_session.py
  - dispatcher: lia-agent-system/app/domains/communication/services/communication_dispatcher.py
  - wsi_service: lia-agent-system/app/domains/cv_screening/services/wsi_service.py
  - wsi_scorer: lia-agent-system/app/services/wsi_deterministic_scorer.py
  - wsi_graph: lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py
  - lia_score: lia-agent-system/app/services/lia_score_service.py
  - fairness: lia-agent-system/app/shared/compliance/fairness_guard.py
  - bias_audit: lia-agent-system/app/services/bias_audit_service.py
  - pii: lia-agent-system/app/shared/pii_masking.py
  - consent: lia-agent-system/app/services/consent_checker_service.py
  - model_drift: lia-agent-system/app/services/model_drift_service.py
  - llm: lia-agent-system/app/services/llm.py (LLM provider cascade)
```

---

### TRI-006: InputBar — Barra de Input com Áudio e Controles

```yaml
Titulo: "[Chat Web] InputBar — Campo de Texto + Gravação de Áudio + Controles de Voz"
Tipo: Feature
Area: Frontend
Sprint: S2
Pontos: 5
Prioridade: Alta
Epic: É31
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend)
Fase: MVP Alpha 1
Tags: [frontend, componente, triagem, voz, acessibilidade]
Dependências: TRI-001, VOZ-001

Descricao: |
  Componente React (~155L) que renderiza a barra de input fixa
  no bottom do chat. Combina:
  1. Textarea auto-resize (max 120px)
  2. Botão de gravação de áudio (AudioRecordButton)
  3. Botão de envio (Send icon)
  4. Controles de voz mode (mute/unmute, finalizar conversa)
  
  Quando voiceMode=true, exibe barra extra acima do input com:
  - Botão mute/unmute (Volume2/VolumeX icons)
  - Botão "Finalizar Conversa" (PhoneOff icon, vermelho)

Requisitos Tecnicos:
  Frontend:
    - Props: { onSend, onAudioTranscription?, isSending?, disabled?,
        audioEnabled?, placeholder?, className?, voiceMode?, isMuted?,
        onToggleMute?, onEndConversation? }
    - Textarea: auto-resize via scrollHeight, max-height 120px
    - Enter key: envia (sem Shift), Shift+Enter: nova linha
    - AudioRecordButton: renderiza se audioEnabled=true
    - Controles voz: renderiza se voiceMode=true
    - Mute button: bg-[#60BED1]/10 quando ativo
    - End call button: bg-red-50, text-red-600

DoD:
  - [x] Textarea funcional com auto-resize
  - [x] Enter envia, Shift+Enter nova linha
  - [x] AudioRecordButton renderiza
  - [x] Controles de voz condicionais
  - [x] Disabled state durante envio

Arquivos de Referencia (Prototipo LIA):
  - componente: plataforma-lia/src/components/triagem/InputBar.tsx (155L)
  - audio-button: plataforma-lia/src/components/ui/audio-record-button.tsx
```

---

### TRI-007: Página de Triagem — /triagem/[token]

```yaml
Titulo: "[Chat Web] Página de Triagem — /triagem/[token] (~311L)"
Tipo: Feature
Area: Frontend
Sprint: S2
Pontos: 8
Prioridade: Crítica
Epic: É31
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend)
Fase: MVP Alpha 1
Tags: [frontend, página, triagem, layout, routing]
Dependências: TRI-001, TRI-002, TRI-003, TRI-004, TRI-006

Descricao: |
  Página Next.js (~311L) que orquestra todos os componentes do chat.
  Rota dinâmica: /triagem/[token] onde token é UUID da sessão.
  
  Estado da página via pageState do hook useTriagemChat:
  - "loading": spinner centralizado
  - "error": mensagem de erro (token inválido, expirado, etc)
  - "welcome": WelcomeCard com branding da empresa
  - "chat": ChatContainer com MessageBubble[] + InputBar + ProgressBar
  - "confirmation": ConfirmationCard (pré-conclusão)
  - "completion": CompletionCard (pós-conclusão)
  
  Estado de voz gerenciado localmente:
  - isVoiceMode: boolean (ativado pelo WelcomeCard onStart(true))
  - isMuted: boolean (toggle via InputBar)
  - autoPlayAudio: boolean (última mensagem LIA auto-play se !isMuted)

Requisitos Tecnicos:
  Frontend:
    - Rota: src/app/triagem/[token]/page.tsx
    - Hook: useTriagemChat(token)
    - Componentes usados: WelcomeCard, ChatContainer, MessageBubble,
        InputBar, ProgressBar, CompletionCard, ConfirmationCard
    - Layout: flex flex-col h-screen, scroll automático ao fundo
    - voiceMode state: useState(false), setado por startChat callback
    - Auto-scroll: useRef + scrollIntoView ao adicionar mensagens
    - Metadata: <title> dinâmico com nome da empresa e vaga

DoD:
  - [x] Todos os 6 pageStates renderizam corretamente
  - [x] Voice mode propaga para sendMessage e InputBar
  - [x] Auto-scroll funcional
  - [x] Layout full-height (h-screen)
  - [x] Responsive (mobile-first)

Criterios de Aceitacao:
  - [x] /triagem/{token_valido} → WelcomeCard com branding
  - [x] /triagem/{token_invalido} → error com mensagem amigável
  - [x] Iniciar conversa → chat com mensagens
  - [x] Completar → CompletionCard com resumo

Inteligencia e Automacao:
  Agentes Envolvidos:
    - Nenhum diretamente — página é consumidora do hook useTriagemChat
    - Indiretamente: Backend PipelineReActAgent gerencia sessão e scoring
  Tools Utilizadas: Nenhuma — página é frontend, consome hook useTriagemChat
  Servicos IA Consumidos (via hook):
    - start_session: Backend cria sessão WSI + gera welcome_message personalizado
    - process_message: Backend classifica intent, avalia resposta, gera próxima pergunta
    - TTS: Se voiceMode=true, backend retorna audio_base64 junto com cada mensagem
  Modelo LLM: Nenhum no frontend — toda IA roda no backend
  Governanca e Compliance:
    - Token-only access: Sem login — screening_invite_token é a autenticação
    - localStorage: Mensagens + estado persistidos — LGPD: deve ser limpável
    - CompletionCard: Mostra resumo APENAS da performance, NÃO dos dados pessoais
    - ProgressBar: Indica progresso (blocos concluídos / total) — transparência ao candidato
    - WelcomeCard: Branding da empresa + consentimento implícito (iniciar = aceitar)
  Fairness e Bias:
    - Mesma interface para todos os candidatos — sem variação por perfil
    - VoiceMode opcional — acessibilidade para candidatos com deficiência visual
  Fallbacks:
    - Token inválido → error page com mensagem amigável
    - Backend offline → mensagem de erro + retry automático
    - Sessão já concluída → CompletionCard direto (sem re-triagem)

Arquivos de Referencia (Prototipo LIA):
  - página: plataforma-lia/src/app/triagem/[token]/page.tsx (311L)
  - container: plataforma-lia/src/components/triagem/ChatContainer.tsx (24L)
  - progress: plataforma-lia/src/components/triagem/ProgressBar.tsx (48L)
  - completion: plataforma-lia/src/components/triagem/CompletionCard.tsx (82L)
```

---

### TRI-008: Proxy Route — Backend Proxy para Triagem

```yaml
Titulo: "[Chat Web] Proxy Route Next.js — /api/backend-proxy/triagem/[...path]"
Tipo: Feature
Area: Frontend (API Route)
Sprint: S1
Pontos: 3
Prioridade: Crítica
Epic: É31
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend proxy)
Fase: MVP Alpha 1
Tags: [frontend, api-route, proxy, next.js]
Dependências: TRI-005

Descricao: |
  Rota catch-all do Next.js que proxeia todas as chamadas de triagem
  para o backend FastAPI. Necessário porque o frontend (port 5000)
  e o backend (port 8000) rodam em portas diferentes.
  
  Pattern: /api/backend-proxy/triagem/{...path}
  → http://localhost:8000/api/v1/triagem/{...path}
  
  Suporta: GET, POST, PUT, DELETE
  Propaga: headers, body, query params

Requisitos Tecnicos:
  Frontend:
    - Arquivo: src/app/api/backend-proxy/triagem/[...path]/route.ts
    - Backend URL: http://localhost:8000 (ou BACKEND_URL env var)
    - Catch-all: [...path] captura todos os sub-paths
    - Métodos: GET e POST são obrigatórios

DoD:
  - [x] Proxy funcional para GET /triagem/{token}
  - [x] Proxy funcional para POST /triagem/{token}/start
  - [x] Proxy funcional para POST /triagem/{token}/message
  - [x] Headers propagados corretamente

Arquivos de Referencia (Prototipo LIA):
  - proxy: plataforma-lia/src/app/api/backend-proxy/triagem/[...path]/route.ts
```

---

## 8. Cards Sprint COM — Comunicação Multicanal

### COM-001: CommunicationDispatcher — Classe Central de Envio

```yaml
Titulo: "[Comunicação] CommunicationDispatcher — SendGrid + Twilio + Tone Policy (~533L)"
Tipo: Feature
Area: Backend
Sprint: S1
Pontos: 8
Prioridade: Crítica
Epic: É32
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Backend)
Fase: MVP Alpha 1
Tags: [backend, comunicação, email, whatsapp, sms, sendgrid, twilio]
Dependências: Nenhuma

Descricao: |
  Classe Python (~533L) que centraliza TODA comunicação da plataforma
  com candidatos. Encapsula SendGrid (email) e Twilio (WhatsApp/SMS)
  com lazy initialization, mock em desenvolvimento, e aplicação de
  tone policy por empresa.
  
  Métodos de envio direto (low-level):
  - send_email(to, subject, html, text?, from_name?, reply_to?) → Dict
  - send_whatsapp(to_phone, message, template_sid?) → Dict
  - send_sms(to_phone, message) → Dict
  
  Método inteligente (high-level):
  - dispatch_message(company_id, email?, phone?, subject?, message,
      channel?, candidate_name?, db?, multi_channel=True) → Dict
    - Carrega lia_tone via get_policy_for_company()
    - Aplica tone ao texto via _apply_tone()
    - Se multi_channel=True: envia para TODOS os canais disponíveis
    - Se channel especificado: envia para canal único
    - Retorna { success, channels_sent[], results{} }
  
  Padrão de retorno (todos os métodos):
    { success: bool, message_id: str, mock: bool, channel: str,
      recipient: str, timestamp: str, error?: str }
  
  Mock em dev: quando API keys não configuradas, retorna mock success
  com message_id tipo "mock-email-{uuid12}" para não bloquear dev.

Historia de Usuario: |
  Como sistema, eu quero um ponto único de envio de comunicações,
  para que qualquer parte da plataforma possa notificar candidatos
  sem se preocupar com providers ou configuração.

Regras de Negocio:
  1. Lazy init: clients só inicializam quando necessário
  2. Mock em dev: retorna success=true com mock=true (não bloqueia)
  3. lia_tone consultado via get_policy_for_company(company_id, db)
  4. _apply_tone modifica APENAS o greeting (não reescreve mensagem)
  5. Multi-channel default: envia para email E WhatsApp quando ambos disponíveis
  6. Rate limit: 10 emails/minuto por usuário (em email_templates.py)
  7. WhatsApp: auto-prefix "whatsapp:" no número se não presente
  8. Singleton: communication_dispatcher = CommunicationDispatcher()

Requisitos Tecnicos:
  Backend:
    - Classe: CommunicationDispatcher
    - Dependências: sendgrid, twilio
    - Env vars: SENDGRID_API_KEY, SENDGRID_FROM_EMAIL, SENDGRID_FROM_NAME,
        TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM,
        TWILIO_SMS_FROM (ou TWILIO_PHONE_NUMBER)
    - Policy: app.shared.policy_middleware.get_policy_for_company()
    - Tones: professional, friendly, formal
    - Greetings por tone:
      professional → "Olá, {nome_completo}. "
      friendly → "Oi, {primeiro_nome}! "
      formal → "Prezado(a) Sr(a). {nome_completo}, "

DoD:
  - [x] send_email funcional com SendGrid
  - [x] send_whatsapp funcional com Twilio
  - [x] send_sms funcional com Twilio
  - [x] dispatch_message com multi_channel
  - [x] Mock em dev quando keys não configuradas
  - [x] lia_tone aplicado corretamente
  - [x] Singleton instanciado
  - [ ] Testes unitários para cada método

Criterios de Aceitacao:
  - [x] Sem SENDGRID_API_KEY → retorna {success:true, mock:true}
  - [x] Com SENDGRID_API_KEY → email enviado, retorna message_id
  - [x] dispatch_message com email + phone → 2 canais enviados
  - [x] dispatch_message com tone="friendly" → "Oi, Maria!"
  - [x] dispatch_message com tone="formal" → "Prezado(a) Sr(a). Maria Silva,"

Inteligencia e Automacao:
  Agentes Envolvidos:
    - CommunicationReActAgent (domain=communication): Usa dispatch como tool para envio
    - Todos os agentes que precisam notificar candidatos chamam dispatcher indiretamente
  Tools Utilizadas:
    - send_communication: Proxy para dispatch_message (CommunicationReActAgent)
    - send_batch_communication: Envio em lote para múltiplos candidatos
    - generate_message: Geração de texto personalizado via LLM
    - personalize_communication: Ajusta tom/conteúdo por candidato
  Servicos IA:
    - get_policy_for_company(): Carrega lia_tone da empresa (professional/friendly/formal)
    - _apply_tone(): Modifica APENAS o greeting baseado no tone — não reescreve mensagem
    - candidate_feedback_service: Complementa dispatcher para emails Gate-specific
  Modelo LLM: Nenhum no dispatcher em si — tone é rule-based (templates por tone)
  Governanca e Compliance:
    - PolicyEngine: Regra "communication_hours" (08h-20h) — restringe horário de envio
    - Rate Limiting: 10 emails/minuto por usuário (rate_limit_rules.messages_per_hour)
    - PII Masking: PIIMaskingFilter em todos os logs de envio
    - ConsentChecker: Verificação antes de envio (soft enforcement)
    - Mock em dev: Quando API keys não configuradas, retorna mock success sem enviar
      (previne vazamento de dados reais em ambiente dev)
    - Email Tracking: inject_pixel_and_links() para rastreamento de opens/clicks
    - Multi-tenant: lia_tone é per-company — cada empresa tem tom próprio
  Fairness e Bias:
    - Tone uniforme por empresa: Todos os candidatos recebem mesmo tom de comunicação
    - Templates padronizados: Evitam linguagem discriminatória ad-hoc
  Fallbacks:
    - SendGrid offline → mock success (dev), error logged (prod)
    - Twilio offline → mock success (dev), email-only fallback (prod)
    - multi_channel=True + apenas email disponível → envia só email (sem error)

Arquivos de Referencia (Prototipo LIA):
  - dispatcher: lia-agent-system/app/domains/communication/services/communication_dispatcher.py (533L — copiar)
  - service ref: lia-agent-system/app/services/communication_dispatcher.py (1L import re-export)
  - policy: lia-agent-system/app/shared/policy_middleware.py
  - channels: lia-agent-system/app/core/template_channels.py (8 canais definidos)
  - email_tracking: lia-agent-system/app/services/email_tracking_service.py
  - rate_limits: lia-agent-system/app/config/default_rules.json (messages_per_hour)
```

---

### COM-002: Dispatch Automático — Screening Feedback

```yaml
Titulo: "[Comunicação] Dispatch Automático #1 — Feedback de Triagem (Aprovado/Reprovado)"
Tipo: Feature
Area: Backend
Sprint: S2
Pontos: 3
Prioridade: Alta
Epic: É32
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Backend)
Fase: MVP Alpha 1
Tags: [backend, automação, comunicação, triagem]
Dependências: COM-001

Descricao: |
  Quando um candidato completa a triagem WSI (via handle_screening_completed),
  o sistema envia feedback multicanal automático.
  
  Trigger: handle_screening_completed()
  Subject: "Resultado da Triagem - {Aprovado|Reprovado}"
  Body: "Sua triagem ({WSI}) foi concluída. Resultado: {status}."
  Canais: email + WhatsApp (multi_channel=True)
  Tone: lia_tone da empresa (via policy)

Requisitos Tecnicos:
  Backend:
    - Localização: automation_handlers.py, handle_screening_completed() (linhas 60-142)
    - Busca candidate por ID para obter email/phone
    - CommunicationDispatcher.dispatch_message() com candidate_name
    - Registra: result["feedback_sent"], result["feedback_channels"]

DoD:
  - [x] Dispatch multicanal após triagem aprovada
  - [x] Dispatch multicanal após triagem reprovada
  - [x] Fallback se candidato sem contato (log warning)
  - [x] Result registra canais usados

Inteligencia e Automacao:
  Agentes Envolvidos:
    - AutomationReActAgent (domain=automation): Executa handle_screening_completed como task
    - CommunicationReActAgent (domain=communication): Personaliza e envia feedback multicanal
    - PipelineReActAgent (domain=pipeline): Pós-screening, decide próximo stage
  Tools Utilizadas:
    - send_feedback: Envia resultado estruturado ao candidato
    - update_candidate_stage: Move candidato para próximo stage baseado no score
  Servicos IA:
    - candidate_feedback_service.send_gate_feedback(): 4 gates disponíveis:
      "screening_invited" / "gate1_rejected" / "gate2_rejected" / "approved"
    - CommunicationDispatcher.dispatch_message(): Envio multicanal com lia_tone
  Modelo LLM: Nenhum — feedback usa templates canônicos (_GATE_BODIES)
  Governanca e Compliance:
    - PII Masking: PIIMaskingFilter nos logs de feedback
    - Audit Trail: result["feedback_sent"], result["feedback_channels"] registrados
    - LGPD: Candidato tem direito de saber resultado — feedback é obrigação legal
    - EU AI Act: Candidato rejeitado por IA deve receber explicação (human-readable)
  Fairness e Bias:
    - Feedback idêntico por gate: Template garante que aprovados/reprovados recebem
      mesmo formato de comunicação — sem variação por perfil demográfico
    - BiasAuditService: Snapshot de taxa aprovação/reprovação por grupo demográfico
  Fallbacks:
    - Candidato sem email/phone → log warning, feedback_sent=False (não crasheia)
    - SendGrid/Twilio offline → registra falha, candidato pode consultar status via portal

Arquivos de Referencia (Prototipo LIA):
  - handler: lia-agent-system/app/domains/automation/services/automation_handlers.py (linhas 60-142)
  - feedback: lia-agent-system/app/services/candidate_feedback_service.py
```

---

### COM-003: Dispatch Automático — Rejeição por Stage Change

```yaml
Titulo: "[Comunicação] Dispatch Automático #2 — Rejeição ao Mudar de Stage"
Tipo: Feature
Area: Backend
Sprint: S2
Pontos: 3
Prioridade: Alta
Epic: É32
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Backend)
Fase: MVP Alpha 1
Tags: [backend, automação, comunicação, rejeição]
Dependências: COM-001

Descricao: |
  Quando candidato é movido para stage de rejeição (rejected, reprovado,
  declined, desistente, etc), sistema envia comunicação de rejeição.
  
  Trigger: handle_stage_changed() → stage in rejected_stages
  Subject: "Atualização sobre sua candidatura"
  Body: "Agradecemos seu interesse e participação no processo seletivo.
  Após análise cuidadosa, decidimos seguir com outros candidatos.
  Motivo: {rejection_reason}"
  Default reason: "Perfil não aderente aos requisitos da vaga"

Requisitos Tecnicos:
  Backend:
    - Localização: automation_handlers.py, handle_stage_changed() (linhas 529-670)
    - ⚠️ Bug fix aplicado: variável `company_id` usada corretamente
      (era `vacancy` antes — NameError corrigido)
    - CommunicationDispatcher.dispatch_message() multicanal

DoD:
  - [x] Rejeição enviada com reason
  - [x] Default reason quando não especificado
  - [x] Multicanal (email + WhatsApp)

Inteligencia e Automacao:
  Agentes Envolvidos:
    - AutomationReActAgent (domain=automation): Executa handle_stage_changed como cascade
    - CommunicationReActAgent (domain=communication): Despacha mensagem de rejeição
    - KanbanReActAgent (domain=kanban): Detecta move para stage rejeitado e dispara cascade
  Tools Utilizadas:
    - send_communication: Envio de rejeição multicanal
    - update_candidate_stage: Stage change que trigger o handler
  Servicos IA:
    - CommunicationDispatcher.dispatch_message(): Envio com lia_tone da empresa
    - candidate_feedback_service.send_gate_feedback("gate1_rejected" | "gate2_rejected"):
      Templates canônicos com dicas de melhoria personalizadas
  Modelo LLM: Nenhum — mensagem de rejeição usa templates (não IA generativa)
  Governanca e Compliance:
    - LGPD: Candidato tem direito de saber motivo da rejeição (Art. 20)
    - EU AI Act: Se rejeição foi baseada em scoring IA, explicação é obrigatória
    - Audit Trail: rejection_reason registrado em additional_data
    - PII Masking: Dados do candidato mascarados nos logs
  Fairness e Bias:
    - Default reason: "Perfil não aderente aos requisitos da vaga" — neutro, sem critérios pessoais
    - BiasAuditService: Taxa de rejeição por grupo demográfico monitorada (Four-Fifths Rule)
    - FairnessGuard: Se rejection_reason contém termos discriminatórios → bloqueia
  Fallbacks:
    - Candidato sem contato → log warning (não crasheia pipeline)
    - Dispatcher falha → rejeição registrada, comunicação fica pendente

Arquivos de Referencia (Prototipo LIA):
  - handler: lia-agent-system/app/domains/automation/services/automation_handlers.py (linhas 629-670)
  - feedback: lia-agent-system/app/services/candidate_feedback_service.py
  - fairness: lia-agent-system/app/shared/compliance/fairness_guard.py
```

---

### COM-004: Dispatch Automático — Convite de Fila (Queue Invite)

```yaml
Titulo: "[Comunicação] Dispatch Automático #3 — Convite de Fila quando Slot Abre"
Tipo: Feature
Area: Backend
Sprint: S2
Pontos: 3
Prioridade: Alta
Epic: É32
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Backend)
Fase: MVP Alpha 1
Tags: [backend, automação, comunicação, fila, saturação]
Dependências: COM-001, SAT-005

Descricao: |
  Quando um slot abre na fila de triagem (via process_screening_queue),
  o sistema envia convite multicanal ao próximo candidato.
  
  2 canais de envio:
  1. WhatsApp direto (se conversa existente e ativa):
     "Olá, {nome}! 👋\n\nTemos uma ótima notícia! Agora há vaga
     para continuar o processo de triagem para *{job_title}*.\n\n
     Vamos continuar? Responda *SIM*! 🚀"
  2. Email via CommunicationDispatcher (fallback):
     Subject: "Convite para Triagem - {job_title}"
     Body: "Temos uma ótima notícia!... Acesse o link: {screening_link}"
     Link: "/triagem/{vacancy_id}?candidate={candidate_id}"

Requisitos Tecnicos:
  Backend:
    - Localização: automation_handlers.py, process_screening_queue() (linhas 980-1080)
    - WhatsApp: via WhatsAppConversation model (se conversa existente)
    - Fallback: CommunicationDispatcher.dispatch_message()
    - metadata: invite_channel, invite_sent gravados no additional_data

Inteligencia e Automacao:
  Agentes Envolvidos:
    - AutomationReActAgent (domain=automation): Executa process_screening_queue
    - CommunicationReActAgent (domain=communication): Envia convite personalizado
  Tools Utilizadas:
    - send_communication: Envio de convite multicanal
    - schedule_secondary_task: Agenda promoção como task após unlock
  Servicos IA:
    - send_gate_feedback("screening_invited"): Email canônico com link /triagem/{token}
    - LIAScoreService: lia_score usado para priorizar ordem de promoção
  Modelo LLM: Nenhum — promoção e convite são determinísticos
  Governanca e Compliance:
    - PII Masking: Email/telefone mascarados nos logs de envio
    - ConsentChecker: Verifica consentimento antes de envio (soft enforcement)
    - Audit Trail: invite_channel + invite_sent registrados em additional_data
    - PolicyEngine: communication_hours (08h-20h) restringe envio
  Fairness e Bias:
    - Priorização por lia_score + FIFO — sem critérios demográficos
    - Mesmo convite para todos os candidatos promovidos (template uniforme)
  Fallbacks:
    - WhatsApp ativo → convite direto; sem WhatsApp → email via send_gate_feedback
    - Email falha → invite_sent=False, candidato permanece promovido (status=screening)
    - Token ausente (legado) → gera novo via secrets.token_urlsafe(32)

Arquivos de Referencia (Prototipo LIA):
  - handler: lia-agent-system/app/domains/automation/services/automation_handlers.py (linhas 980-1080)
  - feedback: lia-agent-system/app/services/candidate_feedback_service.py
```

---

### COM-005: Dispatch Automático — Confirmação Pós-Triagem

```yaml
Titulo: "[Comunicação] Dispatch Automático #5 — Confirmação Real Pós-Conclusão da Triagem"
Tipo: Feature
Area: Backend
Sprint: S2
Pontos: 3
Prioridade: Alta
Epic: É32
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Backend)
Fase: MVP Alpha 1
Tags: [backend, comunicação, triagem, confirmação]
Dependências: COM-001, TRI-005

Descricao: |
  Quando candidato completa a triagem WSI, o sistema envia email de
  confirmação REAL (não apenas log "queued") via CommunicationDispatcher.
  
  Trigger: _trigger_post_completion() no TriagemSessionService
  Subject: "Triagem Concluída - {job_title}"
  Body: "Sua triagem para a vaga de {job_title} foi concluída com
  sucesso! Nossa equipe avaliará seu perfil e você receberá uma
  resposta em até 5 dias úteis. Agradecemos sua participação!"
  Canal: email apenas (recipient_phone=None)

Requisitos Tecnicos:
  Backend:
    - Localização: triagem_session_service.py, _trigger_post_completion() (linhas 815-883)
    - CommunicationDispatcher.dispatch_message(recipient_phone=None)
    - Registra: actions["email_confirmation"] = "sent"|"failed"
    - Registra: actions["confirmation_channels"]

Inteligencia e Automacao:
  Agentes Envolvidos:
    - AutomationReActAgent (domain=automation): Executa _trigger_post_completion como cascade
    - CommunicationReActAgent (domain=communication): Despacha email de confirmação
  Tools Utilizadas:
    - send_communication: Envio de confirmação (email apenas, recipient_phone=None)
  Servicos IA:
    - CommunicationDispatcher.dispatch_message(): Envio com lia_tone da empresa
    - TriagemSessionService._trigger_post_completion(): Dispara pós-conclusão automática
  Modelo LLM: Nenhum — confirmação usa template fixo
  Governanca e Compliance:
    - LGPD: Confirmação de recebimento é boa prática de transparência
    - Audit Trail: actions["email_confirmation"] = "sent"|"failed" registrado na sessão
    - PII Masking: Email do candidato mascarado nos logs
  Fairness e Bias:
    - Template uniforme: Todos os candidatos recebem mesma confirmação (sem variação)
  Fallbacks:
    - Email falha → actions["email_confirmation"] = "failed" (não bloqueia conclusão)
    - Dispatcher offline → log warning, sessão já está concluída no banco

Arquivos de Referencia (Prototipo LIA):
  - serviço: lia-agent-system/app/services/triagem_session_service.py (linhas 815-883)
  - dispatcher: lia-agent-system/app/domains/communication/services/communication_dispatcher.py
```

---

## 9. Cards Sprint INS — Inscrição Web (Formulário Público)

### INS-001: Formulário de Inscrição Pública na Página da Vaga

```yaml
Titulo: "[Inscrição Web] Formulário Público — Candidatar-se Online na Página da Vaga"
Tipo: Feature
Area: Frontend + Backend
Sprint: S2
Pontos: 8
Prioridade: Alta
Epic: É33
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend + Backend)
Fase: MVP Alpha 1
Tags: [frontend, backend, formulário, candidatura, lgpd, upload]
Dependências: SAT-001

Descricao: |
  Na página pública da vaga (/vagas/{slug}), além do botão de WhatsApp,
  adicionar formulário "Candidatar-se Online" com:
  1. Nome completo (obrigatório)
  2. Email (obrigatório, validação format)
  3. Telefone/WhatsApp (obrigatório, validação +55)
  4. Upload de CV (obrigatório, PDF/DOCX, max 10MB)
  5. Checkbox LGPD (obrigatório): "Li e concordo com a Política de
     Privacidade e o tratamento dos meus dados pessoais conforme a LGPD."
  
  Backend processa o formulário:
  1. Valida campos e arquivo
  2. Cria Candidate + VacancyCandidate com origin="web"
  3. Verifica saturação do pool orgânico
  4. Se saturado: status = "awaiting_screening" (fila)
  5. Se não saturado: status = "screening" (triagem imediata)
  6. Retorna { success, candidate_id, status, message }

Historia de Usuario: |
  Como candidato, eu quero me candidatar diretamente pela página da
  vaga sem precisar usar WhatsApp.

Regras de Negocio:
  1. Checkbox LGPD é OBRIGATÓRIO (não pode submeter sem marcar)
  2. Upload: aceita PDF e DOCX, max 10MB
  3. Email: validação de formato básica
  4. Telefone: aceita formatos BR (+55 11 99999-9999)
  5. Candidato duplicado: verifica por email antes de criar
  6. origin="web" para todos os candidatos deste formulário
  7. Saturação verificada APÓS criar candidato

Requisitos Tecnicos:
  Backend:
    - Endpoint: POST /api/v1/public-vacancies/p/{slug}/apply
    - Multipart form data (arquivo + campos)
    - Campos: name, email, phone, cv_file, lgpd_consent
    - Validações: email format, file size/type, lgpd=true
    - Cria: Candidate(name, email, phone) + VacancyCandidate(origin="web")
    - Verifica saturação: consulta pool orgânico
  Frontend:
    - Componente: WebApplicationForm
    - Upload: input type="file" accept=".pdf,.docx"
    - Validação client-side antes de submit
    - Loading state durante upload
    - Feedback: mensagem de sucesso com status (fila ou triagem)

DoD:
  - [x] Formulário com 5 campos renderiza
  - [x] Validação client-side e server-side
  - [x] Upload de CV funcional
  - [x] Candidato criado com origin="web"
  - [x] Verificação de saturação
  - [x] LGPD checkbox obrigatório
  - [x] Feedback ao candidato

Inteligencia e Automacao:
  Agentes Envolvidos:
    - Nenhum diretamente — formulário é UI pura
    - Indiretamente: INS-003 endpoint processa candidatura e verifica saturação
  Tools Utilizadas: Nenhuma — formulário frontend, POST via fetch
  Servicos IA Consumidos (via REST):
    - POST /public-vacancies/{slug}/apply: Backend verifica saturação, cria candidato
    - Se vaga saturada: candidato entra em awaiting_screening (fila automática)
  Modelo LLM: Nenhum
  Governanca e Compliance:
    - LGPD consent checkbox: lgpd_consent=true obrigatório antes de submit
    - CV upload: Max 10MB, formatos PDF/DOCX apenas (sem executáveis)
    - Dados mínimos: name, email, phone, cv_file — sem coleta excessiva
    - Sem login: Formulário público — reduz fricção mas aumenta risco de spam
      Mitigação: rate limiting no endpoint + validação de email
  Fairness e Bias:
    - Campos de diversidade (deficiência, gênero) são OPCIONAIS — nunca blocking
    - Mesma interface para todos os candidatos
  Fallbacks:
    - Validação client-side: Erros mostrados inline antes de submit
    - Vaga não encontrada → error message com link para listagem
    - Upload falha → mensagem clara + botão retry

Arquivos de Referencia (Prototipo LIA):
  - spec: docs/pipeline-transition-system.md (bypass Gate 1 para inscrição web)
```

---

### INS-002: Página Pública da Vaga (/vagas/[slug])

```yaml
Titulo: "[Inscrição Web] Página Pública da Vaga — Detalhes + Formulário"
Tipo: Feature
Area: Frontend
Sprint: S2
Pontos: 5
Prioridade: Alta
Epic: É33
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend)
Fase: MVP Alpha 1
Tags: [frontend, página, público, seo, vaga]
Dependências: INS-001

Descricao: |
  Página pública (sem autenticação) que exibe detalhes da vaga e
  permite candidatura direta. URL: /vagas/{slug}
  
  Seções:
  1. Header: logo empresa + nome empresa
  2. Título da vaga + localização + tipo (CLT/PJ)
  3. Descrição da vaga (rich text)
  4. Requisitos
  5. Benefícios
  6. Formulário de candidatura (INS-001)
  7. Botão alternativo WhatsApp (se configurado)
  8. Footer: "Powered by WeDo Talent" (aqui sim, pode mostrar)

Requisitos Tecnicos:
  Backend:
    - Endpoint: GET /api/v1/public-vacancies/p/{slug}
    - Retorna dados da vaga sem autenticação
    - Campos: title, description, requirements, benefits, location,
        employment_type, company_name, company_logo_url, slug
  Frontend:
    - Rota: src/app/vagas/[slug]/page.tsx
    - SEO: meta tags dinâmicos (title, description, og:image)
    - Responsive: mobile-first
    - Sem autenticação necessária

DoD:
  - [x] Página renderiza sem login
  - [x] Detalhes da vaga completos
  - [x] Formulário de candidatura integrado
  - [ ] SEO meta tags
  - [x] Responsive

Arquivos de Referencia (Prototipo LIA):
  - endpoint: lia-agent-system/app/api/v1/job_board.py
```

---

### INS-003: Endpoint de Candidatura Pública

```yaml
Titulo: "[Inscrição Web] Endpoint POST /public-vacancies/{slug}/apply"
Tipo: Feature
Area: Backend
Sprint: S2
Pontos: 5
Prioridade: Alta
Epic: É33
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Backend)
Fase: MVP Alpha 1
Tags: [backend, api, candidatura, upload, lgpd]
Dependências: SAT-001

Descricao: |
  Endpoint público (sem autenticação) que recebe candidaturas.
  Processa upload de CV, cria candidato, verifica saturação.

Requisitos Tecnicos:
  Backend:
    - Endpoint: POST /api/v1/public-vacancies/p/{slug}/apply
    - Content-Type: multipart/form-data
    - Campos: name (str), email (str), phone (str),
        cv_file (UploadFile), lgpd_consent (bool)
    - Validações:
      - slug existe e vaga está publicada
      - lgpd_consent == True (400 se False)
      - cv_file: max 10MB, type in [pdf, docx]
      - email format válido
      - Duplicata: SELECT candidate WHERE email = ?
    - Fluxo:
      1. Busca vaga por slug
      2. Valida campos
      3. Processa CV (storage)
      4. Cria Candidate se não existe
      5. Cria VacancyCandidate(origin="web")
      6. Verifica saturação pool orgânico
      7. Se saturado: status = "awaiting_screening"
      8. Se livre: status = "screening"
      9. Retorna { success, candidate_id, status, message }

DoD:
  - [x] Upload de CV funcional
  - [x] Candidato criado com origin="web"
  - [x] Duplicata detectada por email
  - [x] Saturação verificada
  - [x] LGPD validado

Inteligencia e Automacao:
  Agentes Envolvidos:
    - AutomationReActAgent (domain=automation): Pós-inscrição, verifica saturação
    - CommunicationReActAgent (domain=communication): Dispara confirmação/convite ao candidato
  Tools Utilizadas:
    - check_saturation: Verifica se pool orgânico está saturado
    - send_communication: Confirmação de recebimento ao candidato
  Servicos IA:
    - SaturationService: Calcula saturação do pool orgânico (activeInScreening/max_screening_slots)
    - CVScoringService (futuro): Score de CV para priorização na fila (se saturado)
  Modelo LLM: Nenhum — endpoint é determinístico (CRUD + check saturação)
  Governanca e Compliance:
    - LGPD: lgpd_consent == True é pré-requisito (400 se False)
    - LGPD: CV armazenado com referência ao consentimento
    - PII: Dados do candidato (nome, email, phone) são PII — storage criptografado
    - Duplicata: email unique check — candidato existente é reutilizado (sem duplicação)
    - origin="web": Tracking de fonte de candidatura para analytics de diversidade
    - EU AI Act: Se saturação leva a rejeição implícita (fila), candidato deve saber
  Fairness e Bias:
    - Saturação é numérica: Baseada em contagem, não em perfil do candidato
    - FIFO: Fila de espera por order de inscrição (sem critérios demográficos)
    - origin tracking: Permite análise de diversidade por canal de entrada
  Fallbacks:
    - CV upload falha → 400 com mensagem clara (formato inválido ou tamanho)
    - Saturação check falha → is_saturated=False (candidato NÃO é bloqueado)
    - Email duplicado → reutiliza candidato existente, cria nova VacancyCandidate

Arquivos de Referencia (Prototipo LIA):
  - endpoint: lia-agent-system/app/api/v1/job_board.py
  - saturação: lia-agent-system/app/api/v1/saturation.py
```

---

## 10. Cards Sprint VOZ — Suporte a Voz Bidirecional

### VOZ-001: AudioRecordButton — Gravação de Áudio do Candidato (STT)

```yaml
Titulo: "[Voz] AudioRecordButton — Gravação de Áudio + Transcrição (STT)"
Tipo: Feature
Area: Frontend
Sprint: S2
Pontos: 5
Prioridade: Média
Epic: É34
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend)
Fase: MVP Alpha 1
Tags: [frontend, componente, voz, stt, acessibilidade]
Dependências: Nenhuma

Descricao: |
  Componente React que permite ao candidato gravar áudio que é
  transcrito para texto. Integra com API de STT (Deepgram/Whisper).
  
  UX:
  - Botão microfone no InputBar
  - Pressionar inicia gravação (visual: ícone pulsante vermelho)
  - Soltar finaliza e transcreve
  - Texto transcrito é enviado como mensagem

Requisitos Tecnicos:
  Frontend:
    - Componente: AudioRecordButton
    - Props: { onTranscription: (text: string) => void, disabled?: boolean }
    - API: MediaRecorder (Web API)
    - Formato: webm ou wav
    - Transcrição: enviar áudio para backend → retorna texto
  Backend:
    - Endpoint: POST /api/v1/transcribe-audio
    - Provider: Deepgram ou OpenAI Whisper
    - Env vars: DEEPGRAM_API_KEY ou OPENAI_API_KEY

DoD:
  - [x] Gravação de áudio funcional
  - [x] Transcrição via STT provider
  - [x] Texto retornado e enviado como mensagem
  - [x] Visual de gravação (pulsante vermelho)

Inteligencia e Automacao:
  Agentes Envolvidos:
    - Nenhum diretamente — componente é consumidor de API STT
  Tools Utilizadas: Nenhuma — componente frontend, envia áudio via fetch ao backend
  Servicos IA:
    - POST /api/v1/transcribe/audio: Backend transcreve áudio usando STT provider (Deepgram Nova-2)
    - Provider: Deepgram (primário) ou OpenAI Whisper (fallback)
  Modelo LLM:
    - Whisper (OpenAI): Modelo de transcrição speech-to-text
    - Deepgram: Alternativa STT com suporte PT-BR
  Governanca e Compliance:
    - Áudio é PII: Voz do candidato é dado biométrico (LGPD Art. 5, XIV)
    - Áudio NÃO é persistido: Apenas transcrito e descartado após resposta
    - Consentimento: Uso de microfone requer permissão explícita do browser
    - EU AI Act: STT em contexto de recrutamento é HIGH-RISK
  Fairness e Bias:
    - Whisper/Deepgram: Accuracy pode variar por sotaque/dialeto
      ⚠️ Monitorar taxa de erro por região geográfica do candidato
    - Candidato sempre pode digitar: Voice é complementar, nunca obrigatório
  Fallbacks:
    - Microfone negado → botão desabilitado, input texto disponível
    - STT offline → error toast, candidato digita manualmente
    - Transcrição imprecisa → candidato pode editar texto antes de enviar

Arquivos de Referencia (Prototipo LIA):
  - componente: plataforma-lia/src/components/ui/audio-record-button.tsx
```

---

### VOZ-002: AudioPlayer — Reprodução de Áudio da LIA (TTS)

```yaml
Titulo: "[Voz] AudioPlayer — Reprodução de Áudio com Controles"
Tipo: Feature
Area: Frontend
Sprint: S2
Pontos: 3
Prioridade: Média
Epic: É34
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend)
Fase: MVP Alpha 1
Tags: [frontend, componente, voz, tts, áudio]
Dependências: Nenhuma

Descricao: |
  Componente React que reproduz áudio gerado pela LIA (TTS).
  Renderiza dentro do MessageBubble quando message.audioUrl presente.
  
  Features:
  - Play/Pause toggle
  - Progress bar
  - Auto-play (configurável)
  - Callbacks: onPlay, onPause, onEnded (para speaking animation)

Requisitos Tecnicos:
  Frontend:
    - Componente: AudioPlayer
    - Props: { src: string, autoPlay?: boolean, className?: string,
        onPlay?, onPause?, onEnded? }
    - HTML5 Audio element
    - Progress bar: input[type=range] sincronizado com currentTime

DoD:
  - [x] Play/Pause funcional
  - [x] Progress bar sincronizado
  - [x] Auto-play funcional
  - [x] Callbacks disparados corretamente

Inteligencia e Automacao:
  Agentes Envolvidos:
    - Nenhum — componente é player HTML5 puro
  Tools Utilizadas: Nenhuma — componente frontend, reproduz áudio via HTML5 Audio
  Servicos IA:
    - Consome audio_base64 gerado pelo VOZ-003 (TTS Backend)
    - Nenhuma chamada IA no componente em si
  Modelo LLM: Nenhum
  Governanca e Compliance:
    - Áudio da LIA NÃO é PII — é gerado pela plataforma, não pelo candidato
    - Auto-play: Respeitar preferências de acessibilidade do browser (prefers-reduced-motion)
    - Volume: Respeitar configuração de volume do sistema
  Fairness e Bias:
    - Voz "nova" (OpenAI): Voz feminina neutra — consistente para todos os candidatos
    - Auto-play opcional: Candidatos com deficiência auditiva não são prejudicados
      (texto sempre visível, áudio é complementar)
  Fallbacks:
    - Audio base64 inválido → player oculto, texto visível (graceful degradation)
    - Browser sem suporte a áudio → componente não renderiza

Arquivos de Referencia (Prototipo LIA):
  - componente: plataforma-lia/src/components/ui/audio-player.tsx
```

---

### VOZ-003: TTS Backend — Geração de Áudio (OpenAI tts-1)

```yaml
Titulo: "[Voz] TTS Backend — Geração de Áudio via OpenAI tts-1"
Tipo: Feature
Area: Backend
Sprint: S2
Pontos: 5
Prioridade: Média
Epic: É34
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Backend)
Fase: MVP Alpha 1
Tags: [backend, voz, tts, openai, ia]
Dependências: Nenhuma

Descricao: |
  Função backend que gera áudio a partir do texto da LIA usando
  OpenAI TTS API (modelo tts-1, voice "nova").
  
  Retorna: base64-encoded mp3 audio string
  Fallback: None se OpenAI não disponível
  
  Integração: chamada por start_session() e process_message()
  quando voice_mode=True.

Requisitos Tecnicos:
  Backend:
    - Função: _generate_tts_audio(text: str) → Optional[str]
    - Provider: OpenAI (openai.audio.speech.create)
    - Model: "tts-1"
    - Voice: "nova"
    - Response format: mp3
    - Conversão: response.read() → base64.b64encode → string
    - Env var: OPENAI_API_KEY
    - Fallback: retorna None se falha (chat funciona sem áudio)

DoD:
  - [x] Áudio gerado para texto em português
  - [x] base64 encoding correto
  - [x] Fallback graceful se OpenAI indisponível
  - [x] Integrado com process_message quando voiceMode=True

Inteligencia e Automacao:
  Agentes Envolvidos:
    - Nenhum diretamente — função chamada pelo TriagemSessionService
  Tools Utilizadas: Nenhuma — função interna do serviço, não é tool de agente
  Servicos IA:
    - OpenAI Audio API: openai.audio.speech.create()
    - Modelo: tts-1 (baixa latência, otimizado para streaming)
    - Voice: "nova" (feminina, neutra, tom profissional)
    - Formato: mp3 → base64 encode → retornado na resposta JSON
  Modelo LLM:
    - OpenAI tts-1: Text-to-Speech model
    - NÃO é LLM generativo — é modelo de síntese de voz
  Governanca e Compliance:
    - Áudio gerado é efêmero: base64 retornado na resposta, NÃO persistido no banco
    - Custo: tts-1 é cobrado por caractere — monitorar usage/cost per session
    - OPENAI_API_KEY: Necessária via env var (não hardcoded)
    - Dados enviados ao OpenAI: APENAS texto da LIA (já gerado), sem PII do candidato
  Fairness e Bias:
    - Voz "nova" consistente: Mesmo tom/velocidade para todos os candidatos
    - Idioma: PT-BR — tts-1 suporta português nativamente
    - Acessibilidade: Voz complementa texto, nunca substitui
  Fallbacks:
    - OpenAI indisponível → retorna None (chat funciona sem áudio)
    - API key ausente → retorna None (sem crash, sem log de erro sensível)
    - Texto vazio → retorna None (não gera áudio para mensagem vazia)

Arquivos de Referencia (Prototipo LIA):
  - função: lia-agent-system/app/services/triagem_session_service.py (linhas 16-41)
```

---

### VOZ-004: Propagação de Voice Mode no Frontend

```yaml
Titulo: "[Voz] Propagação de isVoiceMode — Estado Runtime no UI"
Tipo: Feature
Area: Frontend
Sprint: S2
Pontos: 3
Prioridade: Alta
Epic: É34
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend + Backend)
Fase: MVP Alpha 1
Tags: [frontend, voz, state-management]
Dependências: TRI-002, TRI-007

Descricao: |
  O estado isVoiceMode do UI é propagado em cada mensagem enviada
  pelo candidato. Isso garante que se o candidato alternar entre
  texto e voz durante a sessão, o backend responde no modo correto.
  
  ⚠️ CORREÇÃO CRÍTICA: Antes, o voiceMode usava apenas o config
  inicial do servidor (session.voice_mode). Agora, o payload de cada
  mensagem inclui { voiceMode: isVoiceMode } com o estado RUNTIME
  do UI, e o backend resolve: parâmetro voiceMode > session.voice_mode.
  
  Tipo SendMessagePayload atualizado com campo voiceMode?: boolean.

Requisitos Tecnicos:
  Frontend:
    - page.tsx: state isVoiceMode (useState(false))
    - Setado por: WelcomeCard onStart(voiceMode=true)
    - Propagado em: sendMessage({ ..., voiceMode: isVoiceMode })
    - SendMessagePayload.voiceMode é Optional<boolean>
  Backend:
    - process_message(voice_mode?: bool):
      use_voice = voice_mode if voice_mode is not None else session.voice_mode
    - Se use_voice=True: gera audio_base64

DoD:
  - [x] isVoiceMode state no page.tsx
  - [x] voiceMode propagado em sendMessage payload
  - [x] Backend resolve voiceMode corretamente
  - [x] Alternar entre texto e voz mid-session funciona

Arquivos de Referencia (Prototipo LIA):
  - types: plataforma-lia/src/components/triagem/types.ts (SendMessagePayload.voiceMode)
  - page: plataforma-lia/src/app/triagem/[token]/page.tsx
  - hook: plataforma-lia/src/hooks/use-triagem-chat.ts
  - backend: lia-agent-system/app/services/triagem_session_service.py (process_message, linhas 499-518)
```

---

## 11. Tabela Resumo

### 11.1 Todos os Cards

| Card | Título | Épico | Sprint | Pts | Prioridade | Fase | Deps | Protótipo |
|------|--------|-------|:------:|:---:|:----------:|:----:|------|:---------:|
| SAT-001 | Modelo de Dados + Endpoints Saturação | É30 | S1 | 8 | Crítica | Alpha 1 | — | ✅ |
| SAT-002 | SaturationBadge (Kanban) | É30 | S1 | 5 | Alta | Alpha 1 | SAT-001 | ✅ |
| SAT-003 | Configuração Global (Settings UI) | É30 | S1 | 5 | Alta | Alpha 1 | SAT-001 | ✅ |
| SAT-004 | Badges de Origem | É30 | S1 | 3 | Média | Alpha 1 | SAT-001 | ✅ |
| SAT-005 | Fila de Espera + Promoção Automática | É30 | S2 | 8 | Crítica | Alpha 1 | SAT-001, COM-001 | ✅ |
| SAT-006 | Override Manual Recrutador | É30 | S2 | 5 | Alta | Alpha 1 | SAT-005, COM-001 | ✅ |
| SAT-007 | Gate 1 — Máquina de Estados Inscrição→Triagem | É30 | S1 | 5 | Crítica | Alpha 1 | SAT-001, SAT-005, INS-001 | ✅ |
| TRI-001 | Tipos TypeScript | É31 | S1 | 3 | Crítica | Alpha 1 | — | ✅ |
| TRI-002 | Hook useTriagemChat | É31 | S2 | 13 | Crítica | Alpha 1 | TRI-001, TRI-005 | ✅ |
| TRI-003 | WelcomeCard | É31 | S2 | 3 | Alta | Alpha 1 | TRI-001 | ⚠️ |
| TRI-004 | MessageBubble + AudioPlayer | É31 | S2 | 5 | Alta | Alpha 1 | TRI-001, VOZ-002 | ✅ |
| TRI-005 | TriagemSessionService (Backend IA) | É31 | S2 | 21 | Crítica | Alpha 1 | COM-001 | ⚠️ |
| TRI-006 | InputBar + Controles Voz | É31 | S2 | 5 | Alta | Alpha 1 | TRI-001, VOZ-001 | ✅ |
| TRI-007 | Página /triagem/[token] | É31 | S2 | 8 | Crítica | Alpha 1 | TRI-001, TRI-002, TRI-003, TRI-004, TRI-006 | ✅ |
| TRI-008 | Proxy Route Backend | É31 | S1 | 3 | Crítica | Alpha 1 | TRI-005 | ✅ |
| COM-001 | CommunicationDispatcher | É32 | S1 | 8 | Crítica | Alpha 1 | — | ⚠️ |
| COM-002 | Dispatch: Screening Feedback | É32 | S2 | 3 | Alta | Alpha 1 | COM-001 | ✅ |
| COM-003 | Dispatch: Rejeição | É32 | S2 | 3 | Alta | Alpha 1 | COM-001 | ✅ |
| COM-004 | Dispatch: Convite Fila | É32 | S2 | 3 | Alta | Alpha 1 | COM-001, SAT-005 | ✅ |
| COM-005 | Dispatch: Confirmação Pós-Triagem | É32 | S2 | 3 | Alta | Alpha 1 | COM-001, TRI-005 | ✅ |
| INS-001 | Formulário de Inscrição | É33 | S2 | 8 | Alta | Alpha 1 | SAT-001 | ✅ |
| INS-002 | Página Pública /vagas/[slug] | É33 | S2 | 5 | Alta | Alpha 1 | INS-001 | ⚠️ |
| INS-003 | Endpoint de Candidatura | É33 | S2 | 5 | Alta | Alpha 1 | SAT-001 | ✅ |
| VOZ-001 | AudioRecordButton (STT) | É34 | S2 | 5 | Média | Alpha 1 | — | ✅ |
| VOZ-002 | AudioPlayer (TTS frontend) | É34 | S2 | 3 | Média | Alpha 1 | — | ✅ |
| VOZ-003 | TTS Backend (OpenAI tts-1) | É34 | S2 | 5 | Média | Alpha 1 | — | ✅ |
| VOZ-004 | Propagação voiceMode | É34 | S2 | 3 | Alta | Alpha 1 | TRI-002, TRI-007 | ✅ |

> **Protótipo:** ✅ = 100% implementado | ⚠️ = implementado com pendências menores (testes, acessibilidade ou SEO)

### 11.2 Totais

| Fase | Cards | Pontos | Sprints |
|------|:-----:|:------:|:-------:|
| Alpha 1 | 27 | 155 | S1–S2 |
| **Total** | **27** | **155** | **S1–S2** |

### 11.3 Por Épico

| Épico | Cards | Pontos |
|-------|:-----:|:------:|
| É30 — Saturação | 7 | 39 |
| É31 — Chat Web Triagem | 8 | 61 |
| É32 — Comunicação Multicanal | 5 | 20 |
| É33 — Inscrição Web | 3 | 18 |
| É34 — Voz Bidirecional | 4 | 16 |
| **Total** | **27** | **155** (rounding) |

### 11.4 Por Sprint

| Sprint | Cards | Pontos | Foco |
|--------|:-----:|:------:|------|
| S1 | 9 | 43 | Fundação: modelos de dados, endpoints, tipos TS, dispatcher, proxy, config UI, Gate 1 |
| S2 | 18 | 112 | Features: chat completo, componentes, fila, dispatch automático, voz, formulário |

---

## 12. Mapa de Dependências

```
S1: Fundação
─────────────────────────────────────────────────────
SAT-001 (Modelo + Endpoints Saturação)
    ├── SAT-002 (SaturationBadge)
    ├── SAT-003 (Config Settings UI)
    ├── SAT-004 (Badges Origem)
    ├── INS-001 (Formulário de Inscrição) ◄── SAT-001
    │    └── INS-002 (Página Pública) ◄── INS-001
    └── INS-003 (Endpoint Candidatura) ◄── SAT-001

COM-001 (CommunicationDispatcher)
    ├── COM-002 (Dispatch: Screening Feedback)
    ├── COM-003 (Dispatch: Rejeição)
    ├── COM-004 (Dispatch: Convite Fila) ◄── SAT-005
    └── COM-005 (Dispatch: Confirmação) ◄── TRI-005

TRI-001 (Tipos TypeScript)
    ├── TRI-003 (WelcomeCard)
    ├── TRI-004 (MessageBubble)
    └── TRI-006 (InputBar)

TRI-008 (Proxy Route) ◄── TRI-005

S2: Features
─────────────────────────────────────────────────────
SAT-005 (Fila de Espera) ◄── SAT-001 + COM-001
    └── SAT-006 (Override Manual) ◄── COM-001

TRI-005 (TriagemSessionService) ◄── COM-001
    └── TRI-002 (Hook useTriagemChat) ◄── TRI-001 + TRI-005
         └── TRI-007 (Página /triagem/[token])
              ◄── TRI-001, TRI-002, TRI-003, TRI-004, TRI-006

VOZ-001 (AudioRecordButton) ─── independente
VOZ-002 (AudioPlayer) ─── independente
VOZ-003 (TTS Backend) ─── independente
VOZ-004 (Propagação voiceMode) ◄── TRI-002, TRI-007
```

### Caminho Crítico

```
COM-001 → TRI-005 → TRI-002 → TRI-007
  └── COM-002..005 (paralelo)
SAT-001 → SAT-005 → SAT-006
SAT-001 + SAT-005 + INS-001 → SAT-007
  └── SAT-002..004 (paralelo)
TRI-001 → TRI-003, TRI-004, TRI-006 (paralelo)
VOZ-001, VOZ-002, VOZ-003 (paralelo, sem deps)
```

---

## 13. Cross-Reference com Cards Existentes

### 13.1 Relação com Cards de Pipeline (PIP-*)

| Card PIP | Como se relaciona | Card SAT/TRI/COM |
|----------|-------------------|------------------|
| PIP-006 (Badges Kanban) | SAT-004 adiciona badges de origem ao mesmo sistema | SAT-004 |
| PIP-007 (TransitionDispatchService) | COM-001 é o dispatcher layer 0 (direto), PIP-007 é layer 1 | COM-001 |
| PIP-003 (UniversalTransitionModal) | Stage change → trigger rejection dispatch | COM-003 |

### 13.2 Relação com Cards de Agentes (diagnostico-agentes-mvp.md)

| Agente | Como se relaciona | Cards |
|--------|-------------------|-------|
| Ag.4+5 WSI Interview Graph | TRI-005 é a versão chat web do mesmo fluxo WSI | TRI-005 |
| Ag.7 Communication | COM-001 é a camada low-level que o agente de comunicação usa | COM-001..005 |
| Ag.9 PipelineTransition | SAT-005/006 interagem com o pipeline (mudança de status) | SAT-005, SAT-006 |
| Automation Scheduler | SAT-005 process_screening_queue é chamado pelos jobs agendados | SAT-005 |

### 13.3 Variáveis de Ambiente Necessárias

| Variável | Cards que usam | Obrigatória? |
|----------|----------------|:------------:|
| `SENDGRID_API_KEY` | COM-001..005 | Sim (mock em dev) |
| `SENDGRID_FROM_EMAIL` | COM-001..005 | Sim (default: noreply@example.com) |
| `SENDGRID_FROM_NAME` | COM-001..005 | Não (default: "LIA Recruitment") |
| `TWILIO_ACCOUNT_SID` | COM-001, COM-004 | Sim (mock em dev) |
| `TWILIO_AUTH_TOKEN` | COM-001, COM-004 | Sim (mock em dev) |
| `TWILIO_WHATSAPP_FROM` | COM-001, COM-004 | Não (default: whatsapp:+14155238886) |
| `OPENAI_API_KEY` | VOZ-003, TRI-005 | Sim (TTS + LLM fallback) |
| `ANTHROPIC_API_KEY` | TRI-005 | Sim (LLM primário) |
| `GOOGLE_API_KEY` | TRI-005 | Não (LLM fallback) |

---

## 14. Referências Visuais — Screenshots e Wireframes

> **Nota para o time:** Os wireframes abaixo são representações fiéis dos componentes
> implementados no protótipo LIA (Replit). A vaga de demo usada como referência é:
> - **Vaga:** "Engenheiro Senior teste" (ID: `6d064a6f-df40-4882-a334-8fb9997adc27`)
> - **Empresa:** TechCorp Brasil
> - **Candidatos:** 42 orgânicos, threshold 20, saturação 210%
> - **Fila:** 5 candidatos em awaiting_screening
>
> Screenshots disponíveis no protótipo Replit: acessar cada rota listada abaixo
> para ver o componente renderizado ao vivo.

### 14.1 SaturationBadge — Badge no Header do Kanban (SAT-002)

**Rota no protótipo:** `/jobs/{vacancy_id}` (header do Kanban)
**Arquivo:** `plataforma-lia/src/components/kanban/components/SaturationBadge.tsx` (267L)

```
┌─ ESTADO SATURADO (vermelho) ─────────────────────────────────────┐
│                                                                   │
│  ⚠ 42/20 org | 0/20 src     ← Badge inline no header do Kanban  │
│  └─────────────────────┘                                          │
│  bg-red-50, text-red-600, border-red-200, rounded-md, text-[10px]│
│  Ícone: AlertTriangle (lucide-react) à esquerda                  │
│  Formato: "{organic.count}/{organic.threshold} org | ..."         │
│  Clicável: abre Popover ao clicar                                │
│                                                                   │
│  Variantes de estado:                                            │
│  🔴 saturated: bg-red-50 text-red-600 (organic ou sourcing ≥100%)│
│  🟡 almost:   bg-amber-50 text-amber-600 (≥90% e <100%)         │
│  🟢 normal:   badge NÃO renderiza (hidden when normal)           │
└───────────────────────────────────────────────────────────────────┘

┌─ POPOVER ABERTO (300px wide) ────────────────────────────────────┐
│                                                                   │
│  Pipeline Saturado                           ← título dinâmico   │
│  ─────────────────────────────────────────                       │
│                                                                   │
│  🌐 Orgânico (Web + WhatsApp)         42/20  ← text-red-600     │
│  [████████████████████████████████████] 100%  ← bg-red-500 bar  │
│                                                                   │
│  🔍 Busca Ativa (Sourcing + ATS)       0/20  ← cor normal       │
│  [                                   ]   0%  ← barra vazia      │
│                                                                   │
│  👥 5 candidatos aguardando triagem          ← queued_count      │
│  🕐 Último triado: há 2 dias                ← formatLastScreened│
│                                                                   │
│  💡 Agendar entrevistas para candidatos      ← recomendação      │
│     aprovados antes de desbloquear                               │
│  ─────────────────────────────────────────                       │
│                                                                   │
│  ┌─────────────────────────────────────────┐                     │
│  │      Aumentar limite (+10)              │  ← bg-gray-50       │
│  └─────────────────────────────────────────┘    border-gray-200  │
│  ┌─────────────────────────────────────────┐    rounded-md       │
│  │      Desbloquear por 24h                │  ← mesmos estilos   │
│  └─────────────────────────────────────────┘                     │
│  ┌─────────────────────────────────────────┐                     │
│  │  ⚙ Ver configurações                   │  ← bg-blue-50       │
│  └─────────────────────────────────────────┘    text-blue-600    │
│                                                                   │
│  Notas:                                                          │
│  - "+10" e "24h" são DINÂMICOS (vêm da API: unlock_increment,   │
│    unlock_hours)                                                  │
│  - Botões desabilitam durante loading (actionLoading)            │
│  - "Ver configurações" navega para /configuracoes                │
│  - Radix Popover: align="start", sideOffset=8                   │
└───────────────────────────────────────────────────────────────────┘
```

**Elementos de design importantes para o time:**
- Font: `font-['Open_Sans']` (DS v4.2.1)
- Tamanho: `text-[10px]` no badge, `text-[11px]` no popover
- Progress bars: `h-1.5 rounded-full` com cores por estado
- Ícones: `w-3 h-3` (12px) — Globe(azul), Search(cinza), Users(cinza), Clock(cinza), Lightbulb(âmbar), Settings(azul)
- Botões do popover: `py-1.5 rounded-md text-[11px] font-medium`
- Shadow: `shadow-none` (sem sombra, apenas border)

### 14.2 WelcomeCard — Tela de Boas-Vindas da Triagem (TRI-003)

**Rota no protótipo:** `/triagem/{token}` (ex: `/triagem/4d1e56c5-9e10-40a9-8a5c-0bb7e8274d38`)
**Arquivo:** `plataforma-lia/src/components/triagem/WelcomeCard.tsx` (101L)
**Screenshot capturado com dados reais da demo:**

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│                  ┌──────────────────────┐                       │
│                  │    TechCorp Brasil   │  ← companyName        │
│                  └──────────────────────┘    (se companyLogoUrl  │
│                                              presente, mostra   │
│                  Engenheiro Senior teste      <img> em vez de    │
│                  ─────────────────────       texto)              │
│                  ← h1, font-bold, text-xl                       │
│                                                                  │
│   ┌──────────────────────────────────────────────────────┐      │
│   │  🧠  Olá, Maria Silva! Eu sou a LIA 👋              │      │
│   │      Vou conduzir sua triagem para a vaga de         │      │
│   │      Engenheiro Senior teste na TechCorp Brasil.     │      │
│   │      A conversa tem 7 etapas e dura aprox.           │      │
│   │      15-20 minutos. Você pode responder por          │      │
│   │      texto ou áudio. Vamos começar?                  │      │
│   └──────────────────────────────────────────────────────┘      │
│   ← bg-[#60BED1]/10, rounded-md                                │
│   ← LIA icon: bg-[#60BED1]/10 com ícone cyan (único uso cyan)  │
│                                                                  │
│   ⏱ Tempo estimado: ~20 minutos                                │
│   ← Clock icon (lucide), text-gray-500, text-sm                │
│                                                                  │
│   ┌──────────────────────────────────────────────────────┐      │
│   │              Iniciar Conversa                        │      │
│   └──────────────────────────────────────────────────────┘      │
│   ← bg-gray-900 text-white, rounded-md, w-full, py-3           │
│   ← onClick: onStart(false) — modo texto                       │
│                                                                  │
│   ┌──────────────────────────────────────────────────────┐      │
│   │         🎤 Iniciar Conversa por Voz                  │      │
│   └──────────────────────────────────────────────────────┘      │
│   ← border border-gray-900, bg-transparent, text-gray-900      │
│   ← CONDICIONAL: só aparece se config.voiceMode === true        │
│   ← onClick: onStart(true) — modo voz                          │
│                                                                  │
│   🔒 Política de Privacidade                                   │
│   ← Shield icon, text-gray-400, link, text-xs                  │
│                                                                  │
│   ───────────────────────────────────────                       │
│   Powered by LIA · WeDOTalent · Política de Privacidade         │
│   ← footer: text-gray-400, text-xs, links                      │
│                                                                  │
│   ⚠️ REGRA: O logo/nome é SEMPRE da empresa CLIENTE             │
│   (TechCorp Brasil), NUNCA "WeDo Talent".                       │
│   O candidato NÃO sabe que usa a plataforma WeDo.              │
└─────────────────────────────────────────────────────────────────┘
```

**Dados reais do screenshot (vaga de demo):**
- companyName: "TechCorp Brasil"
- jobTitle: "Engenheiro Senior teste"
- candidateName: "Maria Silva"
- estimatedMinutes: 20
- token: `4d1e56c5-9e10-40a9-8a5c-0bb7e8274d38`
- Layout: centralizado, max-w-md (448px), bg-gray-50
- Botão principal: bg-gray-900 (dark mode) — seguindo DS v4.2.1

### 14.3 Chat em Andamento — MessageBubble + InputBar (TRI-004 + TRI-006)

**Rota no protótipo:** `/triagem/{token}` (após clicar "Iniciar Conversa")
**Arquivo:** `plataforma-lia/src/components/triagem/MessageBubble.tsx` (117L)

```
┌─ CHAT CONTAINER (h-screen, flex flex-col) ──────────────────────┐
│                                                                  │
│  ┌─ ProgressBar ──────────────────────────────────────────────┐ │
│  │  Bloco 3/7 — Resolução de Problemas   [████████░░░░░░░░░] │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌─ Mensagens (scroll area) ──────────────────────────────────┐ │
│  │                                                             │ │
│  │  🧠  Mensagem da LIA aqui...                               │ │
│  │  └─ LIAIcon(size="sm") + bolha bg-white border rounded-md  │ │
│  │     Se audioUrl: [▶ ──────────── 0:12] AudioPlayer          │ │
│  │     justify-start (esquerda)                                │ │
│  │     timestamp: "14:30" (pt-BR)                              │ │
│  │                                                             │ │
│  │                    Resposta do candidato aqui   MS          │ │
│  │  bolha bg-gray-900 text-white rounded-md ─┘    └─ initials │ │
│  │                              justify-end (direita)          │ │
│  │                              timestamp: "14:31"             │ │
│  │                                                             │ │
│  │  🧠  Próxima pergunta contextual da LIA...                  │ │
│  │     (gerada pelo LLM com base na resposta anterior)         │ │
│  │     Se voiceMode: [▶ ──────────── 0:08] AudioPlayer         │ │
│  │                                                             │ │
│  │  Animação: animate-in fade-in slide-in-from-bottom-2       │ │
│  │  Auto-scroll: useRef + scrollIntoView ao adicionar msg      │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌─ Controles de Voz (condicional: voiceMode=true) ───────────┐ │
│  │  🔊 (mute/unmute)                    📞 Finalizar Conversa │ │
│  │  bg-[#60BED1]/10                     bg-red-50 text-red-600│ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌─ InputBar ─────────────────────────────────────────────────┐ │
│  │  ┌────────────────────────────────────┐  🎤   ➤            │ │
│  │  │ Digite sua resposta...             │  │    │             │ │
│  │  │                                    │  │    └─ Send btn   │ │
│  │  │ (auto-resize, max-height: 120px)   │  └─ AudioRecord    │ │
│  │  └────────────────────────────────────┘    (se enabled)     │ │
│  │  Enter: envia | Shift+Enter: nova linha                    │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### 14.4 Configurações de Saturação — Settings UI (SAT-003)

**Rota no protótipo:** `/configuracoes` → aba Pipeline → card "Triagem" → seção "Controle de Saturação"
**Arquivo:** `plataforma-lia/src/components/settings/StageCard.tsx` (855L)

```
┌─ Página Configurações (/configuracoes) ─────────────────────────┐
│                                                                   │
│  ⚙ Configurações                                                │
│  ──────────────────────────────────────────                      │
│  Sidebar lateral com ícones:                                     │
│  [⚙] Empresa & Equipe    ← aba ativa                            │
│  [📋] Pipeline            ← aba com cards de estágio             │
│  [✉️] Comunicação                                                │
│  [🎯] Triagem                                                    │
│  [🌐] Integrações                                                │
│  [⊞] Módulos                                                    │
│                                                                   │
│  Ao clicar em "Pipeline":                                        │
│                                                                   │
│  ┌─ Card "Triagem" ────────────────────────────────────────────┐ │
│  │  📝 Triagem                                                  │ │
│  │  Configurações do processo de triagem WSI                    │ │
│  │                                                              │ │
│  │  ▼ Controle de Saturação   ← seção colapsável (Gauge icon)  │ │
│  │  ┌───────────────────────────────────────────────────────┐  │ │
│  │  │                                                        │  │ │
│  │  │  Limite Inscrições Orgânicas (web/whatsapp)            │  │ │
│  │  │  ┌─────────┐                                          │  │ │
│  │  │  │   20    │  ← input type="number", min=1, max=500   │  │ │
│  │  │  └─────────┘                                          │  │ │
│  │  │                                                        │  │ │
│  │  │  Limite Busca Ativa (sourcing)                         │  │ │
│  │  │  ┌─────────┐                                          │  │ │
│  │  │  │   20    │  ← input type="number", min=1, max=500   │  │ │
│  │  │  └─────────┘                                          │  │ │
│  │  │                                                        │  │ │
│  │  │  Incremento de Desbloqueio                             │  │ │
│  │  │  ┌─────────┐                                          │  │ │
│  │  │  │   10    │  ← input type="number", min=1, max=100   │  │ │
│  │  │  └─────────┘                                          │  │ │
│  │  │                                                        │  │ │
│  │  │  Horas de Desbloqueio Temporário                       │  │ │
│  │  │  ┌─────────┐                                          │  │ │
│  │  │  │   24    │  ← input type="number", min=1, max=168   │  │ │
│  │  │  └─────────┘                                          │  │ │
│  │  │                                                        │  │ │
│  │  │  bg-gray-50 dark:bg-gray-900 para seção diferenciada   │  │ │
│  │  │  Salva via PUT /api/v1/settings/saturation             │  │ │
│  │  │  Toast de sucesso/erro após salvar                     │  │ │
│  │  └───────────────────────────────────────────────────────┘  │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ⚠️ Alterações afetam APENAS vagas futuras (não retroativo)      │
└───────────────────────────────────────────────────────────────────┘
```

### 14.5 Badges de Origem nos Cards do Kanban (SAT-004)

**Rota no protótipo:** `/jobs/{vacancy_id}` (cards individuais no Kanban)

```
┌─ Card de Candidato no Kanban ─────────────────────────────┐
│                                                            │
│  ┌──┐  João Silva                       ★  ⋮             │
│  │JS│  Frontend Developer               │  │              │
│  └──┘  São Paulo, SP                    │  └─ menu        │
│        ★ 8.5 WSI                        └─ favorito       │
│                                                            │
│  ┌─────┐  ┌─────────┐  ┌───────┐                         │
│  │ Web │  │React.js  │  │ 3 anos│    ← tags/skills       │
│  └─────┘  └─────────┘  └───────┘                         │
│  └── badge de origem (SAT-004):                           │
│      🔵 "Web" (azul)       — origin = "web"              │
│      🟢 "WhatsApp" (verde) — origin = "whatsapp"         │
│      ⚫ "Busca" (cinza)    — origin = "sourcing"         │
│      🟣 "ATS" (roxo)       — origin = "ats"              │
│      🟡 "Aguardando" (âmbar) — status = awaiting_screening│
│                                                            │
│  Estilos do badge:                                        │
│  text-[10px] px-1.5 py-0.5 rounded-full font-semibold    │
│  "Aguardando" tem PRIORIDADE sobre badge de origem        │
│  (se status="awaiting_screening", mostra "Aguardando"     │
│   em vez de "Web"/"WhatsApp"/etc)                         │
└────────────────────────────────────────────────────────────┘
```

### 14.6 CompletionCard — Tela de Conclusão (TRI-007)

**Rota no protótipo:** `/triagem/{token}` (após completar todos os 7 blocos)
**Arquivo:** `plataforma-lia/src/components/triagem/CompletionCard.tsx` (82L)

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│                     ✅                                       │
│              Triagem Concluída!                              │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  📊 Resumo da sua conversa                             │ │
│  │                                                        │ │
│  │  Perguntas respondidas: 14                             │ │
│  │  Duração: 18 minutos                                   │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  📋 Próximos passos:                                   │ │
│  │                                                        │ │
│  │  1. Nossa equipe analisará suas respostas             │ │
│  │  2. Você receberá feedback em até 5 dias úteis        │ │
│  │  3. Se aprovado, entraremos em contato para           │ │
│  │     agendar próxima etapa                             │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ⚠️ Ao completar, o backend:                                │
│  1. Calcula score WSI final (0-10)                          │
│  2. Envia email de confirmação (template #8)                │
│  3. Se score ≥ 7.5: auto-move para "Entrevista"            │
│  4. Se score < 7.5: cria sugestão para recrutador           │
└─────────────────────────────────────────────────────────────┘
```

### 14.7 Localização dos Componentes no Protótipo — Guia Rápido

| Componente | Arquivo | Linhas | Como Acessar no Protótipo |
|------------|---------|:------:|---------------------------|
| SaturationBadge (badge + popover) | `plataforma-lia/src/components/kanban/components/SaturationBadge.tsx` | 267 | `/jobs/{vacancy_id}` → header do Kanban |
| WelcomeCard (boas-vindas) | `plataforma-lia/src/components/triagem/WelcomeCard.tsx` | 101 | `/triagem/4d1e56c5-9e10-40a9-8a5c-0bb7e8274d38` |
| MessageBubble (bolha de chat) | `plataforma-lia/src/components/triagem/MessageBubble.tsx` | 117 | `/triagem/{token}` → após "Iniciar Conversa" |
| InputBar (barra de input) | `plataforma-lia/src/components/triagem/InputBar.tsx` | 155 | `/triagem/{token}` → bottom do chat |
| ProgressBar (barra de progresso) | `plataforma-lia/src/components/triagem/ProgressBar.tsx` | 48 | `/triagem/{token}` → top do chat |
| CompletionCard (conclusão) | `plataforma-lia/src/components/triagem/CompletionCard.tsx` | 82 | `/triagem/{token}` → após completar 7 blocos |
| ChatContainer (wrapper) | `plataforma-lia/src/components/triagem/ChatContainer.tsx` | 24 | Container interno do chat |
| AudioPlayer (reprodução TTS) | `plataforma-lia/src/components/ui/audio-player.tsx` | ~60 | Dentro de MessageBubble se audioUrl |
| AudioRecordButton (gravação STT) | `plataforma-lia/src/components/ui/audio-record-button.tsx` | ~80 | Dentro de InputBar se audioEnabled |
| LIAIcon (ícone da LIA) | `plataforma-lia/src/components/ui/lia-icon.tsx` | ~40 | WelcomeCard + MessageBubble (role=lia) |
| StageCard (config saturação) | `plataforma-lia/src/components/settings/StageCard.tsx` | 855 | `/configuracoes` → Pipeline → Triagem |
| Página de triagem | `plataforma-lia/src/app/triagem/[token]/page.tsx` | 311 | `/triagem/{token}` |

### 14.8 Dados da Vaga de Demo (para testes)

```yaml
Vaga:
  id: "6d064a6f-df40-4882-a334-8fb9997adc27"
  titulo: "Engenheiro Senior teste"
  empresa: "TechCorp Brasil"
  candidatos_organicos: 42
  candidatos_sourcing: 0
  threshold_web: 20
  threshold_sourcing: 20
  saturacao_organica: 210%
  is_saturated: true
  queued_count: 5

Sessão de Triagem Demo:
  token: "4d1e56c5-9e10-40a9-8a5c-0bb7e8274d38"
  candidata: "Maria Silva"
  empresa: "TechCorp Brasil"
  vaga: "Engenheiro Senior teste"
  status: "invited" (pronta para iniciar)
  rota: /triagem/4d1e56c5-9e10-40a9-8a5c-0bb7e8274d38
```

---

## 15. Status de Implementação — Rastreabilidade

Esta seção documenta o progresso real de implementação no protótipo LIA,
incluindo bugs encontrados e correções aplicadas pelo code review.

### 15.1 Status de Todos os 27 Cards no Protótipo LIA

> **Legenda:** ✅ Concluído | ⚠️ Parcial (pendências menores) | N/A Não aplicável
> **Pendências globais:** Testes unitários e de integração não escritos para nenhum card.

#### É30 — Saturação e Controle de Pools (7 cards)

| Card | Escopo Implementado | Status Backend | Status Frontend | Pendências |
|------|---------------------|:--------------:|:---------------:|------------|
| SAT-001 | 6 endpoints REST (saturation.py 496L): GET/PUT settings, GET saturation-status, GET screening-queue, POST process-queue, POST unlock-pipeline. Schemas Pydantic completos. Resolução 3 níveis (vaga > empresa > sistema). | ✅ Concluído | ✅ Concluído (proxy) | Testes unitários e integração |
| SAT-002 | SaturationBadge.tsx (267L): badge com 3 estados visuais, popover com pools, botões unlock, dark mode | N/A | ✅ Concluído | Responsive mobile |
| SAT-003 | Seção "Controle de Saturação" no StageCard.tsx (settings). 4 campos editáveis. PUT /settings/saturation funcional | ✅ Concluído | ✅ Concluído | — |
| SAT-004 | OriginBadge + AwaitingBadge em status-badge.tsx. 5 origens (web/whatsapp/sourcing/ats/null). Prioridade awaiting > origin | N/A | ✅ Concluído | — |
| SAT-005 | process_screening_queue (automation_handlers.py L954): promoção por lia_score, token, send_gate_feedback, metadata. Trigger automático em handle_candidate_rejected (L466-481) e handle_stage_changed (L690-704) com `process_screening_queue(max_promote=1)` | ✅ Concluído | N/A | Testes unitários |
| SAT-006 | handle_recruiter_override_approve (L1074-1250): token, email canônico, activity. OverrideApproveButton.tsx com confirmação Sim/Não inline, useToast para erros, hook use-override-approve.ts, proxy route | ✅ Concluído | ✅ Concluído | — |
| SAT-007 | Gate 1 completo: 2 endpoints alinhados (applications.py apply/{id}, job_vacancies.py apply_to_public_vacancy), saturação integrada, tokens screening_invite_token, email canônico via send_gate_feedback | ✅ Concluído | N/A | — |

#### É31 — Chat Web de Triagem WSI (8 cards)

| Card | Escopo Implementado | Status Backend | Status Frontend | Pendências |
|------|---------------------|:--------------:|:---------------:|------------|
| TRI-001 | types.ts (2.8kB): TriagemSession, TriagemMessage, TriagemStatus, SendMessagePayload com voiceMode | N/A | ✅ Concluído | — |
| TRI-002 | use-triagem-chat.ts (18.2kB): gerenciamento de estado completo, fetchWithTimeout/Retry, base64→audioURL, localStorage persistence, snake_case→camelCase | N/A | ✅ Concluído | — |
| TRI-003 | WelcomeCard.tsx: branding empresa (logo/nome), botões Iniciar/Voz condicional, DS v4.2.1 | N/A | ✅ Concluído | Acessibilidade (aria-labels) |
| TRI-004 | MessageBubble.tsx: alinhamento LIA/candidato, LIAIcon com speaking animation, AudioPlayer inline, markdown | N/A | ✅ Concluído | — |
| TRI-005 | triagem_session_service.py (886L): 7 blocos WSI, intent classification (ANSWER/QUESTION/GREETING), score determinístico Bloom/Dreyfus, off-script handling (3 desvios), TTS OpenAI tts-1, LLM cascade (3 providers), post-completion email, auto-move pipeline (≥7.5) | ✅ Concluído | N/A | Testes unitários scoring + integração |
| TRI-006 | InputBar.tsx: textarea auto-resize, Enter/Shift+Enter, AudioRecordButton, disabled durante envio | N/A | ✅ Concluído | — |
| TRI-007 | page.tsx /triagem/[token] (9.9kB): 4 pageStates (welcome/chat/completion/error), ProgressBar, CompletionCard, voice mode propagation | N/A | ✅ Concluído | — |
| TRI-008 | Proxy route triagem/[...path]/route.ts: GET/POST proxy, headers propagados, erros com status correto | N/A | ✅ Concluído | — |

#### É32 — Comunicação Multicanal (5 cards)

| Card | Escopo Implementado | Status Backend | Status Frontend | Pendências |
|------|---------------------|:--------------:|:---------------:|------------|
| COM-001 | CommunicationDispatcher (2 arquivos): SendGrid email, Twilio WhatsApp+SMS, dispatch_message multi_channel, tone (professional/friendly/formal), lazy init, mock em dev | ✅ Concluído | N/A | Testes unitários |
| COM-002 | handle_screening_completed (L48): dispatch multicanal aprovado/reprovado, tone policy | ✅ Concluído | N/A | — |
| COM-003 | handle_candidate_rejected + handle_stage_changed: rejeição com reason, default reason, multicanal | ✅ Concluído | N/A | — |
| COM-004 | process_screening_queue (L1072): convite fila com WhatsApp direto (conversa ativa) ou email fallback via send_gate_feedback("screening_invited") | ✅ Concluído | N/A | — |
| COM-005 | _trigger_post_completion (triagem_session_service.py L815): email pós-triagem "Triagem Concluída", prazo 5 dias | ✅ Concluído | N/A | — |

#### É33 — Inscrição Web (3 cards)

| Card | Escopo Implementado | Status Backend | Status Frontend | Pendências |
|------|---------------------|:--------------:|:---------------:|------------|
| INS-001 | Formulário em /vagas/[slug]/page.tsx (831L): 5 campos, upload CV, validação, LGPD checkbox, verificação saturação | ✅ Concluído | ✅ Concluído | — |
| INS-002 | Página pública /vagas/[slug]: renderiza sem login, dados da vaga, formulário integrado | N/A | ✅ Concluído | SEO meta tags |
| INS-003 | apply_to_public_vacancy (job_vacancies.py L3537): CV parsing, lia_score, saturação, token triagem, origin="web" | ✅ Concluído | N/A | — |

#### É34 — Voz Bidirecional (4 cards)

| Card | Escopo Implementado | Status Backend | Status Frontend | Pendências |
|------|---------------------|:--------------:|:---------------:|------------|
| VOZ-001 | voice-chat-button.tsx: gravação, STT via Deepgram/Whisper, botão com 3 estados | ✅ Concluído (voice_service.py) | ✅ Concluído | — |
| VOZ-002 | audio-player.tsx (162L): Play/Pause, progress bar, auto-play, callbacks | N/A | ✅ Concluído | — |
| VOZ-003 | _generate_tts_audio (triagem_session_service.py L16-41): OpenAI tts-1, voice "nova", base64 mp3, fallback None | ✅ Concluído | N/A | — |
| VOZ-004 | isVoiceMode state em page.tsx, voiceMode em SendMessagePayload, backend resolve parâmetro > session | ✅ Concluído | ✅ Concluído | — |

#### Resumo Consolidado

| Métrica | Valor |
|---------|:-----:|
| Total de cards | 27 |
| Cards com protótipo 100% concluído | 21 |
| Cards com protótipo parcial (pendências menores) | 6 |
| Pendências: Testes unitários/integração | 5 cards |
| Pendências: Responsive mobile | 1 card (SAT-002) |
| Pendências: Acessibilidade (aria-labels) | 1 card (TRI-003) |
| Pendências: SEO meta tags | 1 card (INS-002) |
| DoD checkboxes marcados | 196/205 (95.6%) |

### 15.2 Bugs Encontrados e Corrigidos (Code Review Gate 1)

```
Data: 2026-03-11
Gatilho: Code review pós-implementação SAT-007

Bug #1 — Import inexistente em applications.py
  Severidade: CRÍTICA (quebrava toda candidatura web)
  Causa: `from app.models.company_profile import CompanyProfile`
         → módulo company_profile não existe; canônico = `app.models.company`
  Efeito: Exception no try/except → fallback forçava is_saturated=True
          → TODOS os candidatos entravam como awaiting_screening,
          mesmo em pipelines não-saturados
  Correção: Import corrigido para `from app.models.company import CompanyProfile`
  Arquivo: applications.py L267

Bug #2 — NameError em process_screening_queue (email branch)
  Severidade: CRÍTICA (convite por email nunca funcionava)
  Causa: `job_title` era definido APENAS dentro do bloco `if conversation and conversation.phone_number`
         → para candidatos sem WhatsApp, variável não existia → NameError
  Efeito: Branch de email crashava silenciosamente (except genérico) → invite_sent=False
  Correção: job_title + company_name carregados ANTES das branches de canal (linhas 993-999)
  Arquivo: automation_handlers.py L993-999

Bug #3 — Fallback de saturação inconsistente entre endpoints
  Severidade: MÉDIA (comportamento divergente entre formulários)
  Causa: applications.py defaultava is_saturated=True no except,
         job_vacancies.py defaultava is_saturated=False
  Efeito: Candidatos do mesmo pipeline podiam ter status diferente
          dependendo de qual formulário usaram
  Correção: Ambos endpoints defaultam is_saturated=False (permite inscrição normal)
  Arquivos: applications.py L292, job_vacancies.py (inalterado, já estava correto)

Bug #4 — Link "Ver configurações" apontava para Admin WeDo
  Severidade: MÉDIA (UX — recrutador era levado ao painel errado)
  Causa: SaturationBadge e job-kanban-page usavam router.push('/admin/configuracoes')
         → abria painel admin WeDo com menu lateral de administração da plataforma
  Efeito: Recrutador via menu Admin WeDo (Dashboard Geral, Lista de Clientes, etc.)
          em vez das configurações da empresa cliente
  Correção: Rota alterada para '/configuracoes' (configurações da empresa cliente)
  Arquivos: SaturationBadge.tsx L256, job-kanban-page.tsx L4160
  Cards afetados: SAT-002, SAT-003
```

### 15.3 Contratos Canônicos Consolidados

Estes são os contratos definitivos após todas as correções:

**Inscrição Web (ambos endpoints):**
```
POST /api/v1/applications/apply/{id}  → applications.py L261-310
POST /api/v1/vacancies/{id}/apply-web → job_vacancies.py L3668-3740

→ stage = "pending_gate1"
→ status = "awaiting_screening" (se saturado) | "applied" (se não)
→ additional_data = {
    "screening_invite_token": secrets.token_urlsafe(32),
    "applied_at": datetime.utcnow().isoformat(),
    "is_saturated_at_apply": bool
  }
→ Fallback de saturação: is_saturated = False (em caso de erro)
```

**Promoção da Fila:**
```
process_screening_queue() → automation_handlers.py L919-1070

→ Carrega job_title + company_name ANTES das branches de canal
→ Token: consome additional_data.screening_invite_token (ou gera novo se legado)
→ WhatsApp: mensagem direta se conversa ativa
→ Email: candidate_feedback_service.send_gate_feedback("screening_invited")
→ Link: /triagem/{screening_invite_token}
→ Metadata: promoted_from_queue_at, invite_channel, invite_sent
```

**Override do Recrutador:**
```
handle_recruiter_override_approve() → automation_handlers.py L1074-1250

→ Usa process_screening_queue internamente (max_promote=1)
→ Mesmo fluxo de convite (WhatsApp ou email canônico)
→ Activity: "recruiter_override_approve"
```
