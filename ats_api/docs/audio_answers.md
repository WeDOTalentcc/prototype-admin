# Audio Answers — Technical Reference

## Overview

Answers support audio file attachments via ActiveStorage. Audio can be uploaded through the Interview AI API (public) or the internal Answers API (authenticated).

---

## Answer Model

The `Answer` model uses `has_one_attached :audio_file` from ActiveStorage.

**Supported formats:** `audio/webm`, `audio/ogg`, `audio/mp4`, `audio/mpeg`, `audio/wav`, `audio/x-wav`, `audio/mp3`

**Max file size:** 25 MB

**Key methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `audio_file.attached?` | Boolean | Whether audio is attached |
| `audio_url` | String/nil | Full URL to stream the audio |
| `attach_audio_from_base64(data, content_type:)` | Boolean | Attach audio from base64-encoded string |

---

## API Endpoints

### 1. Interview AI API (Public) — `POST /:account_uid/:token/answer`

Accepts audio via **multipart upload** or **base64**.

#### Option A: Multipart Upload

```bash
curl -X POST "{API_URL}/v1/interview/{account_uid}/{token}/answer" \
  -H "X-Interview-API-Key: {key}" \
  -F "question_id=42" \
  -F "transcription=My answer text..." \
  -F "audio_duration=45.2" \
  -F "audio_file=@recording.webm;type=audio/webm"
```

#### Option B: Base64 (JSON body)

```json
{
  "question_id": 42,
  "transcription": "My answer text...",
  "audio_duration": 45.2,
  "audio_base64": "GkXfo59ChoEBQveBAULygQRC84EI...",
  "audio_content_type": "audio/webm"
}
```

#### Response 201

```json
{
  "answer_id": 789,
  "question_id": 42,
  "status": "saved",
  "has_audio": true,
  "audio_url": "https://api.example.com/rails/active_storage/blobs/..."
}
```

---

### 2. Internal Answers API (Authenticated)

Both `POST` and `PUT` on the answers endpoints accept `audio_file` as a multipart field.

**Endpoints:**
- `POST /v1/evaluations/:uid/answers` (Evaluations context)
- `POST /v1/users/answers` (Users context)
- `POST /v1/users/answers/answers` (Nested answers context)

```bash
curl -X POST "{API_URL}/v1/evaluations/{uid}/answers" \
  -H "Authorization: Bearer {token}" \
  -F "answer[question_id]=42" \
  -F "answer[title]=My answer" \
  -F "answer[description]=Full answer text..." \
  -F "answer[audio_file]=@recording.webm;type=audio/webm"
```

---

### 3. AnswerSerializer — Response Fields

All answer API responses include these audio fields:

| Field | Type | Description |
|-------|------|-------------|
| `audio_url` | string/null | Full URL to stream the audio file |
| `has_audio` | boolean | Whether audio is attached |
| `audio_mime_type` | string/null | MIME type of the attached audio (e.g., `audio/webm`) |

---

## Data Flow

```
Interview AI Client
  │
  ├─ multipart: audio_file param ─────┐
  │                                    │
  └─ JSON: audio_base64 param ────────┤
                                       ▼
                            InterviewApiController
                              #submit_answer
                                       │
                                       ▼
                              Answer.create! + attach_audio
                                       │
                            ┌──────────┴──────────┐
                            │                     │
                    ActiveStorage            Answer record
                    (local disk / S3)       (PostgreSQL)
                            │                     │
                            └──────────┬──────────┘
                                       │
                                       ▼
                              AnswerSerializer
                              (audio_url, has_audio, audio_mime_type)
```

---

## Storage

Audio files are stored via ActiveStorage. Default config uses local disk (`storage/`). In production, configure S3 or GCS in `config/storage.yml`.

The `audio_url` returned by the serializer points to the ActiveStorage blob URL, which handles streaming and content-type negotiation.
