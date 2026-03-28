# Deepgram - Fluxo Completo de Integração

## Visão Geral

O Deepgram é um serviço de **Speech-to-Text (STT)** que será usado para transcrever áudio em texto no WeDo Talent. Ele é mais barato e preciso que o Gemini para transcrição dedicada.

### Custo
- **$0.0043/minuto** (pay-as-you-go)
- **Free tier**: 12.000 minutos/ano (~200 horas)
- Modelo: **Nova-2** (melhor precisão para pt-BR)

---

## Cenários de Uso do Deepgram

### 1. Chat com LIA por Voz (Atual - Ajustar)

**Fluxo:**
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Usuário grava   │────▶│ Frontend envia   │────▶│ Backend         │────▶│ LIA processa    │
│ áudio no chat   │     │ audio.webm       │     │ Deepgram STT    │     │ texto e responde│
└─────────────────┘     └──────────────────┘     └─────────────────┘     └─────────────────┘
```

**Interface Existente:** `AudioRecordButton` em `plataforma-lia/src/components/ui/audio-record-button.tsx`

**Status Atual:**
- ✅ Frontend: Botão de gravação funcional (grava webm/mp4)
- ✅ Frontend: Envia para `/api/backend-proxy/transcribe/audio`
- ⚠️ Backend: Usa Gemini ao invés de Deepgram (precisa ajustar)
- ✅ Backend: DeepgramService já implementado (332 linhas)

**Ajuste Necessário:** Trocar endpoint `/api/v1/transcribe/audio` para usar DeepgramService

---

### 2. Triagem WSI por Texto (Atual)

**Fluxo:**
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Candidato       │────▶│ Chat Web/        │────▶│ LIA faz         │────▶│ Sistema gera    │
│ recebe convite  │     │ WhatsApp         │     │ perguntas WSI   │     │ score WSI       │
└─────────────────┘     └──────────────────┘     └─────────────────┘     └─────────────────┘
```

**Interface Existente:** `WSITriagemInviteModal` - Modal de convite para triagem

**Status:** ✅ Funcional (não usa Deepgram - é texto)

---

### 3. Triagem WSI por Voz/Telefone (OpenMic + Deepgram)

**Fluxo Completo:**
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Recrutador      │────▶│ OpenMic.ai       │────▶│ Candidato       │────▶│ OpenMic grava   │
│ inicia chamada  │     │ faz ligação      │     │ atende telefone │     │ respostas       │
└─────────────────┘     └──────────────────┘     └─────────────────┘     └─────────────────┘
                                                                                   │
                                                                                   ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ LIA analisa     │◀────│ Claude/LangGraph │◀────│ Deepgram        │◀────│ Webhook recebe  │
│ e gera score    │     │ processa texto   │     │ transcreve      │     │ áudio da chamada│
└─────────────────┘     └──────────────────┘     └─────────────────┘     └─────────────────┘
```

**Interfaces Existentes:**
- `WSIVoiceScreeningStatus` - Modal de acompanhamento da chamada
- `WSIScorecard` - Exibe resultado após triagem

**Status:**
- ✅ UI de acompanhamento pronta
- ⚠️ OpenMic.ai não configurado (precisa API key)
- ⚠️ Webhook de recebimento de áudio não implementado
- ✅ DeepgramService pronto para transcrever

---

### 4. Upload de Áudio de Entrevista (Novo)

**Fluxo Proposto:**
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Recrutador      │────▶│ Frontend upload  │────▶│ Backend salva   │────▶│ Deepgram        │
│ sobe arquivo    │     │ audio.mp3        │     │ e envia URL     │     │ transcreve      │
└─────────────────┘     └──────────────────┘     └─────────────────┘     └─────────────────┘
                                                                                   │
                                                                                   ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────────────────────────┐
│ Transcrição     │◀────│ Claude analisa   │◀────│ Texto completo da entrevista disponível│
│ salva no banco  │     │ pontos-chave     │     └─────────────────────────────────────────┘
└─────────────────┘     └──────────────────┘
```

**Status:** 🔴 Não implementado (nova funcionalidade)

---

### 5. Áudio WhatsApp (Integração Futura)

**Fluxo Proposto:**
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Candidato envia │────▶│ WhatsApp         │────▶│ Backend recebe  │────▶│ Deepgram        │
│ áudio no Zap    │     │ Business API     │     │ media_url       │     │ transcreve      │
└─────────────────┘     └──────────────────┘     └─────────────────┘     └─────────────────┘
                                                                                   │
                                                                                   ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────────────────────────┐
│ LIA responde    │◀────│ LIA processa     │◀────│ Texto do áudio integrado à conversa    │
│ no WhatsApp     │     │ mensagem         │     └─────────────────────────────────────────┘
└─────────────────┘     └──────────────────┘
```

**Status:** 🔴 Não implementado (depende de WhatsApp Business API)

---

## Arquitetura Técnica Atual

### Backend (Pronto)

```
lia-agent-system/
├── app/
│   ├── services/
│   │   └── deepgram_service.py      # ✅ 332 linhas - Serviço completo
│   └── api/v1/
│       └── transcription.py         # ⚠️ Usa Gemini, precisa trocar para Deepgram
```

**DeepgramService - Métodos Disponíveis:**

| Método | Descrição | Status |
|--------|-----------|--------|
| `transcribe_audio_url(url)` | Transcreve de URL (S3, WhatsApp, etc) | ✅ Pronto |
| `transcribe_audio_bytes(data)` | Transcreve de bytes (upload) | ✅ Pronto |
| `estimate_cost(duration)` | Calcula custo estimado | ✅ Pronto |
| `is_configured` | Verifica se API key existe | ✅ Pronto |

### Frontend (Pronto)

```
plataforma-lia/src/
├── components/
│   ├── ui/
│   │   └── audio-record-button.tsx   # ✅ Botão de gravação
│   └── wsi/
│       ├── wsi-voice-screening-status.tsx  # ✅ Modal de chamada
│       ├── wsi-triagem-invite-modal.tsx    # ✅ Modal de convite
│       └── wsi-scorecard.tsx               # ✅ Exibe resultados
├── app/api/backend-proxy/
│   └── transcribe/audio/route.ts     # ✅ Proxy para backend
```

---

## O Que Precisa Ser Feito

### Prioridade 1: Ajustar Endpoint de Transcrição

**Arquivo:** `lia-agent-system/app/api/v1/transcription.py`

**Mudança:** Trocar Gemini por DeepgramService

```python
# ANTES (Gemini)
from google import genai
response = client.models.generate_content(...)

# DEPOIS (Deepgram)
from app.services.deepgram_service import deepgram_service
result = await deepgram_service.transcribe_audio_bytes(content, mimetype)
```

**Esforço:** ~30 minutos

---

### Prioridade 2: Webhook para OpenMic.ai

**Criar:** `lia-agent-system/app/api/v1/webhooks/openmic.py`

**Funcionalidade:**
1. Receber webhook quando chamada terminar
2. Baixar áudio da chamada
3. Transcrever com Deepgram
4. Enviar para LIA processar
5. Salvar score WSI

**Esforço:** ~4 horas

---

### Prioridade 3: Upload de Áudio de Entrevistas (Opcional)

**Criar:**
1. `InterviewAudioUpload` component no frontend
2. `POST /api/v1/interviews/{id}/audio` endpoint
3. Integração com sistema de notas de entrevistas

**Esforço:** ~8 horas

---

## Interfaces que Precisam Ajuste

| Interface | Arquivo | Status | Ajuste Necessário |
|-----------|---------|--------|-------------------|
| AudioRecordButton | `ui/audio-record-button.tsx` | ✅ Pronto | Nenhum |
| WSIVoiceScreeningStatus | `wsi/wsi-voice-screening-status.tsx` | ✅ Pronto | Nenhum |
| WSITriagemInviteModal | `wsi/wsi-triagem-invite-modal.tsx` | ✅ Pronto | Nenhum |
| LIA Chat Panel | `expandable-ai-prompt.tsx` | ✅ Pronto | Nenhum |

**Conclusão:** Todas as interfaces de áudio já existem e estão funcionais. Não há necessidade de criar novas UIs.

---

## Interfaces Novas (Opcionais para Go-Live)

### 1. Upload de Gravação de Entrevista

Permitir que recrutador suba arquivo MP3/WAV de entrevista gravada externamente.

**Onde:** Tab "Entrevistas" na página do candidato

**Componentes:**
- Botão "Fazer upload de gravação"
- Progress bar durante transcrição
- Visualizador de transcrição com timestamps

**Prioridade:** Baixa (pode ser fase 2)

---

### 2. Player de Áudio com Transcrição

Reproduzir áudio da triagem por voz com transcrição sincronizada.

**Onde:** Modal de resultado WSI

**Funcionalidade:**
- Player de áudio
- Transcrição lado a lado
- Highlight da frase sendo falada

**Prioridade:** Baixa (pode ser fase 2)

---

## Estimativa de Custos Deepgram

### Cenário: 100 vagas/mês com triagem por voz

| Item | Cálculo | Custo Mensal |
|------|---------|--------------|
| Triagem por voz (15 min/candidato) | 100 × 10 candidatos × 15 min × $0.0043 | $64.50 |
| Chat por voz (2 min/interação) | 100 × 20 interações × 2 min × $0.0043 | $17.20 |
| Upload de entrevistas (30 min) | 100 × 3 × 30 min × $0.0043 | $38.70 |
| **TOTAL** | | **$120.40/mês** |

Com free tier (12.000 min/ano = 1.000 min/mês), os primeiros ~230 usos são gratuitos.

---

## Resumo Executivo

### O que já temos:
1. ✅ DeepgramService completo no backend (332 linhas)
2. ✅ DEEPGRAM_API_KEY configurada
3. ✅ Interfaces de áudio prontas (gravação, triagem WSI)
4. ✅ Proxy frontend → backend configurado

### O que precisamos ajustar:
1. ⚠️ **Endpoint `/transcribe/audio`** - Trocar Gemini por Deepgram (~30 min)

### O que precisamos criar (para triagem por voz):
1. 🔴 Webhook OpenMic.ai (~4h)
2. 🔴 Configurar API keys OpenMic (~1h)

### Interfaces novas necessárias:
- **Nenhuma para go-live** - todas existem

---

## Próximos Passos Recomendados

1. **Imediato:** Ajustar endpoint de transcrição para usar Deepgram
2. **Sprint 2:** Implementar webhook OpenMic para triagem por voz
3. **Fase 2:** Upload de gravações de entrevistas externas
