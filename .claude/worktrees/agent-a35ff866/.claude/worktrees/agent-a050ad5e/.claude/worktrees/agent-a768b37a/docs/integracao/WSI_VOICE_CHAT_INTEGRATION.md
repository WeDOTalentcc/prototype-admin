# WSI Integration with Voice & Chat Screening

## Overview
WSI (WeDoTalent Skill Index) integrates with existing screening workflows:
- **Voice Screening**: OpenMic.ai → WSI analysis → Score + Report
- **Chat Screening**: WhatsApp/LIA Chat → WSI analysis → Score + Report

## Integration Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     SCREENING WORKFLOWS                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Voice Screening (OpenMic.ai)      Chat Screening (WhatsApp)     │
│  ┌─────────────────────┐          ┌──────────────────────┐      │
│  │ 1. JD Analysis      │          │ 1. JD Analysis       │      │
│  │ 2. Question Gen     │          │ 2. Question Gen      │      │
│  │ 3. Voice Call       │          │ 3. Chat Conversation │      │
│  │ 4. Transcription    │          │ 4. Collect Responses │      │
│  └──────────┬──────────┘          └───────────┬──────────┘      │
│             │                                  │                 │
│             └──────────┬───────────────────────┘                 │
│                        │                                         │
│                        ▼                                         │
│              ┌──────────────────────┐                            │
│              │   WSI Analysis       │                            │
│              │  (wsi_service.py)    │                            │
│              └──────────┬───────────┘                            │
│                         │                                        │
│                         ▼                                        │
│              ┌──────────────────────┐                            │
│              │  PostgreSQL WSI DB   │                            │
│              │  (6 tables)          │                            │
│              └──────────┬───────────┘                            │
│                         │                                        │
│                         ▼                                        │
│              ┌──────────────────────┐                            │
│              │  WSI Results         │                            │
│              │  - Score 1-5         │                            │
│              │  - Structured Report │                            │
│              │  - Candidate Feedback│                            │
│              └──────────────────────┘                            │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## API Integration Points

### 1. Voice Screening Integration (OpenMic.ai)

**Endpoint:** `/api/voice-screening/complete-with-wsi`

**Flow:**
1. OpenMic.ai call completes → transcription ready
2. Backend calls WSI endpoints:
   ```python
   # Generate WSI questions (6-8)
   questions = POST /api/wsi/generate-questions
   
   # Analyze each transcribed response
   for question, answer in transcription:
       analysis = POST /api/wsi/analyze-response
   
   # Calculate final WSI
   wsi_result = POST /api/wsi/calculate-wsi
   
   # Generate report for recruiter
   report = POST /api/wsi/generate-report
   ```

3. Results saved to PostgreSQL → accessible in dashboard

**Implementation File:** `lia-agent-system/app/workflows/voice_screening.py`

---

### 2. Chat Screening Integration (WhatsApp/LIA)

**Endpoint:** `/api/chat-screening/complete-with-wsi`

**Flow:**
1. Candidate completes WhatsApp screening
2. Backend calls WSI endpoints (same as voice)
3. Results displayed in real-time in LIA chat interface

**Implementation File:** `lia-agent-system/app/agents/screening_agent.py`

---

## Database Wiring

### Voice Screening
```python
# When voice screening completes:
session_id = create_wsi_session(
    candidate_id=voice_screening.candidate_id,
    job_vacancy_id=voice_screening.job_id,
    screening_type='voice'
)

# Link voice recording to WSI response
wsi_response_analyses.response_audio_url = openmic_recording_url
```

### Chat Screening
```python
# When chat screening completes:
session_id = create_wsi_session(
    candidate_id=chat_screening.candidate_id,
    job_vacancy_id=chat_screening.job_id,
    screening_type='chat'
)

# Responses already text-based → direct to WSI
```

---

## Frontend Integration (Next.js Dashboard)

### WSI Results Card
```typescript
// Display WSI score in candidate card
<WSIScoreBadge 
  overall_wsi={4.2}
  classification="alto"
  percentile={85}
/>
```

### Detailed Report Modal
```typescript
// Show full WSI analysis when recruiter clicks
<WSIReportModal
  result_id={wsi_result.id}
  candidate_id={candidate.id}
  technical_analysis={...}
  behavioral_analysis={...}
  recommendation={...}
/>
```

---

## Testing Plan

### Unit Tests
```bash
cd lia-agent-system
pytest tests/test_wsi_service.py
pytest tests/test_wsi_endpoints.py
```

### Integration Tests
```python
# Test voice → WSI flow
async def test_voice_screening_wsi_integration():
    # 1. Create mock voice screening
    # 2. Generate questions
    # 3. Analyze responses
    # 4. Calculate WSI
    # 5. Verify results in DB
    
# Test chat → WSI flow
async def test_chat_screening_wsi_integration():
    # Similar flow
```

### End-to-End Tests
1. Complete real voice screening via OpenMic.ai
2. Verify WSI scores appear in dashboard
3. Verify report is accurate
4. Verify candidate receives feedback

---

## Deployment Checklist

### Prerequisites
- ✅ PostgreSQL database with WSI schema
- ✅ WSI service implemented (`wsi_service.py`)
- ✅ API endpoints created (`wsi_endpoints.py`)
- ✅ RAG knowledge base populated (4 docs)
- ⏳ FastAPI router registered
- ⏳ Frontend dashboard components
- ⏳ Voice/chat integrations wired

### Environment Variables
```bash
DATABASE_URL=postgresql://...
ANTHROPIC_API_KEY=sk-ant-...
OPENMIC_API_KEY=...  # For voice screening
```

### Migrations
```bash
# Schema already applied via psql
# Future changes: use Alembic or Drizzle
```

---

## Performance Considerations

### WSI Analysis Time
- **Voice screening**: ~30-45 seconds (6-8 questions)
  - Question generation: 5-10s
  - Response analysis: 3-5s per question (× 6 = 18-30s)
  - WSI calculation: <1s
  - Report generation: 5-10s

- **Chat screening**: Real-time (streamed)
  - Analysis happens per-message
  - Final WSI calculated at end

### Rate Limiting
- ✅ LLM calls use `safe_json_parse()` with fallbacks
- ✅ Dataset generator uses `asyncio.Semaphore(5)`
- ⚠️ Production: Add Redis caching for repeated analyses

### Caching Strategy
```python
# Cache competency suggestions per JD
@cache(ttl=3600)
async def analyze_jd(job_description: str):
    ...

# Cache WSI questions for same competencies
@cache(ttl=7200)
async def generate_questions(competencies: List[Competency]):
    ...
```

---

## Monitoring & Observability

### LangSmith Tracing
```python
# Already configured in wsi_service.py
# Traces available at: https://smith.langchain.com
```

### Metrics to Track
1. **WSI Distribution**: Histogram of overall_wsi scores
2. **Classification Breakdown**: % excelente, alto, medio, regular, baixo
3. **Red Flags Frequency**: Most common red flags detected
4. **Analysis Time**: P50, P95, P99 latency per stage
5. **LLM Costs**: Cost per screening (Claude API usage)

---

## Next Steps (Post-MVP)

1. **Fine-tune Models** (R$ 1.800)
   - Response Analyzer: 15K examples
   - Question Generator: 8K examples
   - A/B test: base vs fine-tuned

2. **Enhance Report Templates**
   - Add industry-specific insights
   - Comparative analysis vs other candidates
   - Predictive success probability

3. **Multi-language Support**
   - English, Spanish screening
   - Translate RAG docs
   - Localize feedback messages

4. **Advanced Analytics**
   - WSI trends over time
   - Recruiter calibration dashboard
   - Candidate experience metrics (NPS)

---

**Status:** WSI core complete ✅  
**Integration:** Documented (implementation pending)  
**Production-Ready:** 80% (needs voice/chat wiring + testing)
