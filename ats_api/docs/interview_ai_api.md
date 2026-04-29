# Interview AI API — Endpoint Documentation

Base URL: `{API_URL}/v1/interview/{account_uid}`

## Authentication

All requests require the `X-Interview-API-Key` header:

```
X-Interview-API-Key: <INTERVIEW_AI_API_KEY>
```

The `account_uid` path parameter identifies the tenant/account for multi-tenancy routing.

---

## 1. GET `/:account_uid/:token` — Load Interview Session

Returns session config, questions, candidate/job context.

**Response 200:**
```json
{
  "token": "abc123",
  "status": "pending",
  "interview_type": "technical",
  "duration_minutes": 30,
  "language": "pt-BR",
  "job": { "title": "Backend Developer", "requirements": "..." },
  "candidate": { "name": "João Silva", "email": "joao@email.com" },
  "questions": [
    {
      "id": 42,
      "title": "Experiência com Ruby on Rails",
      "description": "Descreva sua experiência com Rails...",
      "response_type": "open_text",
      "order": 1
    }
  ],
  "evaluation": { "id": 10, "name": "Avaliação Técnica" },
  "company": { "name": "Acme Corp", "interviewer_name": "Lia" }
}
```

---

## 2. POST `/:account_uid/:token/start` — Start Interview

Marks session as active and creates (or links) the `EvaluationCandidate` record.

**Request body:** _none_

**Response 200:**
```json
{
  "status": "active",
  "evaluation_candidate_id": 123
}
```

---

## 3. POST `/:account_uid/:token/answer` — Submit Single Answer

Saves one candidate answer during the interview. Call this endpoint for each question answered.

**Request body:**
```json
{
  "question_id": 42,
  "transcription": "Eu trabalhei com Ruby on Rails por 5 anos, participei de projetos...",
  "audio_duration": 45.2,
  "score": 4.0,
  "analysis_data": {
    "sentiment": "positive",
    "confidence": 0.92
  },
  "ai_evaluation": {
    "strengths": ["Experiência sólida"],
    "weaknesses": ["Faltou detalhes sobre testes"],
    "notes": "Candidato demonstrou conhecimento prático"
  }
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `question_id` | integer | **yes** | Question ID from `questions` array in session config |
| `transcription` | string | **yes** | Full text transcription of the candidate's spoken answer |
| `audio_duration` | float | no | Duration of the audio answer in seconds |
| `audio_file` | file | no | Audio file (multipart upload) — supports webm, ogg, mp4, mpeg, wav, mp3 |
| `audio_base64` | string | no | Audio file as base64 string (alternative to multipart) |
| `audio_content_type` | string | no | MIME type for base64 audio (default: `audio/webm`) |
| `score` | float (0-5) | no | Pre-computed score (can be overridden later by WSI pipeline) |
| `analysis_data` | object | no | Any AI analysis metadata (sentiment, confidence, keywords) |
| `ai_evaluation` | object | no | Structured AI evaluation (strengths, weaknesses, notes) |

**Response 201:**
```json
{
  "answer_id": 789,
  "question_id": 42,
  "status": "saved",
  "has_audio": true,
  "audio_url": "https://api.example.com/rails/active_storage/blobs/.../answer_789.webm"
}
```

**Error 404** (question not found in session):
```json
{ "error": "Question not found in session" }
```

**Error 422** (session not active):
```json
{ "error": "Session is not active" }
```

---

## 4. POST `/:account_uid/:token/complete` — Complete Interview

Marks the session and `EvaluationCandidate` as completed. This triggers the full WSI evaluation pipeline:

1. `EvaluationCandidate` is marked as `completed: true`
2. `after_update_commit` callback fires `get_ai_feedback`
3. `Evaluations::PerCandidateNotificationJob` runs
4. `AiFeedbackService` analyzes all answers
5. Final score is calculated and stored
6. Teams/notifications are sent

**Request body:**
```json
{
  "transcript": "Full interview transcript here...",
  "report": "Summary report of the interview...",
  "score": 78.5,
  "recommendation": "recommended"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `transcript` | text | no | Full interview transcript (all Q&A combined) |
| `report` | text | no | AI-generated interview summary report |
| `score` | float | no | Overall interview score from AI |
| `recommendation` | string | no | AI recommendation (`recommended`, `not_recommended`, `maybe`) |

**Response 200:**
```json
{
  "status": "completed",
  "session_id": 456
}
```

---

## 5. POST `/:account_uid/:token/result` — Save Result (Legacy)

Alternative endpoint that saves results and enqueues `SaveInterviewResultJob`. Use `complete` instead for the standard WSI pipeline flow.

---

## Full Interview Flow

```
1. GET  /:account_uid/:token           → Load session config + questions
2. POST /:account_uid/:token/start     → Mark session active, get evaluation_candidate_id
3. POST /:account_uid/:token/answer    → Submit answer for question 1
4. POST /:account_uid/:token/answer    → Submit answer for question 2
5. POST /:account_uid/:token/answer    → Submit answer for question N
6. POST /:account_uid/:token/complete  → Finish interview → triggers WSI scoring pipeline
```

## Example — Python Integration

```python
import requests

API_URL = "https://api.example.com/v1/interview"
API_KEY = "your-api-key"
ACCOUNT_UID = "account-uid-from-config"
TOKEN = "session-token-from-config"

BASE = f"{API_URL}/{ACCOUNT_UID}"

headers = {
    "X-Interview-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# 1. Load session
session = requests.get(f"{BASE}/{TOKEN}", headers=headers).json()
questions = session["questions"]

# 2. Start interview
requests.post(f"{BASE}/{TOKEN}/start", headers=headers)

# 3. Submit each answer after candidate responds
for question in questions:
    answer_data = {
        "question_id": question["id"],
        "transcription": transcribe_audio(audio_buffer),
        "audio_duration": audio_duration_seconds
    }
    requests.post(
        f"{BASE}/{TOKEN}/answer",
        headers=headers,
        json=answer_data
    )

# 4. Complete interview
requests.post(
    f"{BASE}/{TOKEN}/complete",
    headers=headers,
    json={
        "transcript": full_transcript,
        "report": generate_report(),
        "score": calculate_score(),
        "recommendation": "recommended"
    }
)
```
