# Deepgram - Interfaces e Upload de Gravações

## 1. Endpoint Atualizado

O endpoint `/api/v1/transcribe/audio` foi atualizado para usar **Deepgram** ao invés de Gemini.

**Novos endpoints disponíveis:**
- `POST /api/v1/transcribe/audio` - Transcreve arquivo de áudio enviado
- `POST /api/v1/transcribe/url` - Transcreve áudio de URL (WhatsApp, S3, OpenMic)
- `GET /api/v1/transcribe/status` - Verifica se serviço está configurado

---

## 2. Interfaces Existentes (já são da WeDo Talent)

### Chat com LIA por Voz

**Onde aparece:** 
- Barra de chat da LIA (canto inferior direito da tela)
- Página de chat dedicada (`/chat`)
- Painel expandido da LIA

**Componentes:**
- `AudioRecordButton` - Botão de microfone que grava e transcreve
- `ExpandableAIPrompt` - Barra de chat com botão de voz
- `LiaExpandedPanel` - Painel lateral da LIA

**Como funciona:**
1. Usuário clica no microfone 🎤
2. Grava áudio (webm/mp4)
3. Envia para `/api/backend-proxy/transcribe/audio`
4. Backend transcreve com Deepgram
5. Texto vai para o prompt da LIA

**Screenshot do botão:** O ícone de microfone fica na barra de input da LIA.

---

### Triagem por Telefone (WSI Voice Screening)

**Onde aparece:**
- Botão "Iniciar Triagem por Voz" no preview do candidato
- Modal `WSIVoiceScreeningStatus` - acompanha a chamada em tempo real

**Componentes:**
- `WSIVoiceScreeningStatus` - Modal que mostra status da chamada
- `WSITriagemInviteModal` - Modal para enviar convite de triagem
- `WSIScorecard` - Mostra resultado da triagem WSI

**Como funciona:**
1. Recrutador clica "Iniciar Triagem por Voz"
2. OpenMic.ai faz ligação para o candidato
3. Modal mostra status: Iniciando → Chamando → Em andamento → Processando → Concluído
4. Ao final, áudio é transcrito (Deepgram) e analisado (LIA)
5. Score WSI é gerado e salvo

**Nota:** OpenMic.ai ainda não está configurado (precisa de API key).

---

## 3. Tabs do Candidato

O preview/página do candidato tem **4 abas**:

| Tab | ID | Descrição |
|-----|-----|-----------|
| **Perfil** | `profile` | Informações básicas, skills, experiência |
| **Atividades** | `activities` | Feed de atividades, timeline de eventos |
| **Arquivos** | `files` | Documentos, CVs, anexos |
| **Pareceres** | `opinions` | Pareceres LIA, avaliações WSI |

### Onde os áudios devem ficar:

**Opção 1: Tab Atividades (Recomendado)**
- Cada upload de áudio cria uma atividade
- Aparece na timeline com ícone de áudio
- Mostra transcrição inline
- Melhor para histórico cronológico

**Opção 2: Tab Arquivos**
- Upload fica listado como arquivo
- Permite download do áudio original
- Mostra link para transcrição
- Melhor para acesso rápido ao arquivo

**Decisão sugerida:** Usar **ambos**:
- **Tab Arquivos:** Armazena o arquivo de áudio
- **Tab Atividades:** Registra o evento com transcrição

---

## 4. Plano de Implementação - Upload de Gravações

### 4.1 Backend - Endpoints

```
POST /api/v1/candidates/{id}/audio
  - Recebe arquivo de áudio (MP3, WAV, M4A, WebM)
  - Transcreve com Deepgram
  - Salva arquivo e transcrição
  - Cria atividade no histórico
  - Retorna: audio_id, transcription, duration

GET /api/v1/candidates/{id}/audio
  - Lista todos os áudios do candidato

GET /api/v1/candidates/{id}/audio/{audio_id}
  - Retorna detalhes do áudio (URL, transcrição, metadata)
```

### 4.2 Frontend - Componentes

**Novo componente:** `CandidateAudioUpload`

```tsx
// Onde: plataforma-lia/src/components/candidate/candidate-audio-upload.tsx
interface CandidateAudioUploadProps {
  candidateId: string
  onUploadComplete?: (audio: AudioRecord) => void
}
```

**Integração na Tab Arquivos:**
- Botão "Adicionar gravação" na tab Files
- Permite upload de MP3, WAV, M4A, WebM, OGG
- Mostra progresso de upload e transcrição
- Após concluído, mostra player + transcrição

### 4.3 Banco de Dados

Nova tabela: `candidate_audio_files`

```sql
CREATE TABLE candidate_audio_files (
  id UUID PRIMARY KEY,
  candidate_id VARCHAR(255) NOT NULL,
  job_vacancy_id VARCHAR(255),
  file_url TEXT NOT NULL,
  file_name VARCHAR(255),
  file_size INTEGER,
  mime_type VARCHAR(100),
  duration_seconds FLOAT,
  transcription TEXT,
  transcription_confidence FLOAT,
  transcription_cost FLOAT,
  audio_type VARCHAR(50), -- 'interview', 'screening', 'whatsapp', 'other'
  uploaded_by VARCHAR(255),
  created_at TIMESTAMP DEFAULT NOW(),
  company_id VARCHAR(100) NOT NULL
);
```

---

## 5. Plano de Implementação - Áudios WhatsApp

### 5.1 Fluxo

1. Candidato envia áudio no WhatsApp
2. Webhook WhatsApp recebe evento com `media_url`
3. Backend chama `deepgram.transcribe_audio_url(media_url)`
4. Transcrição é integrada à conversa
5. Áudio + transcrição salvos no candidato

### 5.2 Pré-requisitos

- WhatsApp Business API configurada
- Webhook para receber mensagens
- WHATSAPP_TOKEN configurado

### 5.3 Endpoint Webhook

```
POST /api/v1/webhooks/whatsapp
  - Recebe eventos do WhatsApp
  - Tipo "audio" → transcreve com Deepgram
  - Salva mensagem + transcrição
  - Notifica recrutador
```

---

## 6. Estimativa de Esforço

| Funcionalidade | Esforço | Dependências |
|----------------|---------|--------------|
| ✅ Endpoint Deepgram | Feito | DEEPGRAM_API_KEY |
| Upload de gravações | 8h | Tabela DB, storage |
| Player de áudio | 4h | Frontend |
| Integração WhatsApp | 12h | WhatsApp Business API |
| Triagem por voz | 6h | OpenMic.ai API |

---

## 7. Próximos Passos Recomendados

1. **Imediato:** Testar endpoint Deepgram atualizado
2. **Sprint atual:** Implementar upload de gravações na tab Arquivos
3. **Próximo sprint:** Integrar WhatsApp Business API
4. **Futuro:** Configurar OpenMic.ai para triagens por telefone
