# WSI Evaluation System — Questions, Scoring & Methodology

Complete reference for the screening question system, WSI scoring pipeline, and AI-powered candidate evaluation.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        EVALUATION LIFECYCLE                         │
│                                                                     │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────┐ │
│  │ CREATE   │───>│ GENERATE Qs  │───>│ ASSIGN TO    │───>│CANDIDATE│
│  │Evaluation│    │ (AI / Manual)│    │ CANDIDATES   │    │ANSWERS │ │
│  └──────────┘    └──────────────┘    └──────────────┘    └───┬───┘ │
│                                                              │     │
│       ┌──────────────────────────────────────────────────────┘     │
│       │                                                            │
│       ▼                                                            │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────┐             │
│  │SCORE EACH│───>│ AGGREGATE    │───>│ AI FEEDBACK  │             │
│  │ ANSWER   │    │ WSI SCORE    │    │ (Qualitative)│             │
│  │(4 framew)│    │(Tech+Behav)  │    │ (LLM)       │             │
│  └──────────┘    └──────────────┘    └──────────────┘             │
│                                                                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 1. Entity Relationships

```
Job (1)──────────(N) Evaluation (1)──────────(N) Question
 │                       │                          │
 │                       │                          │
 │                (N) EvaluationCandidate (N)────(N) Answer
 │                       │                          │
 │                       │                          │
 └───────────────────(1) Apply ─────────(1) Candidate
```

| Entity                  | Purpose                             | Key Fields                                                                                            |
| ----------------------- | ----------------------------------- | ----------------------------------------------------------------------------------------------------- |
| **Evaluation**          | A screening test linked to a job    | `name`, `job_id`, `is_screening`, `is_chatbot`, `chatbot_channel`, `ai_enabled`                       |
| **Question**            | A single question with WSI metadata | `response_type`, `competence_type`, `bloom_level`, `dreyfus_target`, `framework`, `framework_weights` |
| **EvaluationCandidate** | Links a candidate to an evaluation  | `score`, `wsi_classification`, `wsi_level`, `wsi_summary`, `ai_feedback`, `completed`                 |
| **Answer**              | A candidate's response with scoring | `description`, `analysis_data`, `final_skill_score`, `choices` (conversation rounds)                  |

---

## 2. Database Schema

### evaluations

| Column                          | Type      | Description                          |
| ------------------------------- | --------- | ------------------------------------ |
| `name`                          | string    | Evaluation name                      |
| `description`                   | text      | Description                          |
| `job_id`                        | bigint FK | Parent job                           |
| `user_id`                       | bigint FK | Creator                              |
| `account_id`                    | bigint FK | Tenant                               |
| `selective_process_id`          | bigint FK | Pipeline stage where evaluation runs |
| `approved_selective_process_id` | bigint FK | Stage to move approved candidates    |
| `rejected_selective_process_id` | bigint FK | Stage to move rejected candidates    |
| `is_chatbot`                    | boolean   | Chatbot mode enabled                 |
| `ai_enabled`                    | boolean   | AI scoring enabled (default: true)   |
| `chatbot_channel`               | integer   | 0=internal, 1=whatsapp               |
| `is_screening`                  | boolean   | Screening evaluation flag            |
| `is_trigger`                    | boolean   | Auto-trigger on candidate entry      |
| `notification_enabled`          | boolean   | Send notifications on completion     |
| `notification_type`             | integer   | 0=per_candidate, 1=daily, 2=weekly   |
| `introduction_details`          | text      | Custom intro message for candidates  |

### questions

| Column                   | Type      | Description                                                               |
| ------------------------ | --------- | ------------------------------------------------------------------------- |
| `title`                  | string    | Question text                                                             |
| `description`            | text      | Extended description                                                      |
| `details`                | text      | Additional context                                                        |
| `evaluation_id`          | bigint FK | Parent evaluation                                                         |
| `response_type`          | integer   | autodeclaration / contextual / microcase / situational / theoretical      |
| `competence_type`        | string    | "technical" or "behavioral"                                               |
| `bloom_level`            | string    | remember / understand / apply / analyze / create                          |
| `dreyfus_target`         | integer   | Expected maturity level 1-5                                               |
| `ocean_trait`            | string    | openness / conscientiousness / extraversion / agreeableness / neuroticism |
| `framework`              | string    | Primary: cbi / bloom / dreyfus / big_five                                 |
| `framework_weights`      | jsonb     | `{bloom: 0.25, dreyfus: 0.35, big_five: 0.10, cbi_star: 0.30}`            |
| `validation_type_weight` | decimal   | Weight 0-1 by response_type                                               |
| `category`               | string    | padrao / avaliacao / situacional                                          |
| `choices`                | json      | For multiple-choice options                                               |
| `parent_question_id`     | integer   | Sub-question support                                                      |

### evaluation_candidates

| Column               | Type      | Description                               |
| -------------------- | --------- | ----------------------------------------- |
| `uid`                | string    | Public-facing unique identifier           |
| `candidate_uid`      | string    | Candidate public identifier               |
| `candidate_id`       | bigint FK | Candidate                                 |
| `evaluation_id`      | bigint FK | Evaluation                                |
| `apply_id`           | bigint FK | Application                               |
| `job_id`             | bigint FK | Job                                       |
| `completed`          | boolean   | All questions answered                    |
| `score`              | float     | Final WSI score × 2 (0-10 scale)          |
| `wsi_classification` | string    | Excellent / High / Medium / Regular / Low |
| `wsi_level`          | string    | Dreyfus level name                        |
| `wsi_summary`        | text      | Human-readable summary                    |
| `ai_feedback`        | jsonb     | Full AI qualitative analysis              |
| `is_screening`       | boolean   | Inherited from evaluation                 |
| `session_status`     | string    | active / timeout / closed                 |

### answers

| Column              | Type         | Description                                          |
| ------------------- | ------------ | ---------------------------------------------------- |
| `question_id`       | bigint FK    | Question answered                                    |
| `evaluation_id`     | bigint FK    | Parent evaluation                                    |
| `candidate_id`      | bigint FK    | Who answered                                         |
| `description`       | text         | Candidate's response text                            |
| `choices`           | json         | Conversation rounds `[{question, answer, followup}]` |
| `comments_response` | text         | Raw AI evaluation JSON                               |
| `analysis_data`     | jsonb        | Full deterministic scoring breakdown                 |
| `final_skill_score` | decimal(4,2) | WSI score 0-5 for this skill                         |

---

## 3. WSI Methodology — 4 Scientific Frameworks

The WSI (WeDoTalent Skill Index) integrates 4 scientific frameworks into a unified scoring system:

| Framework            | Source                  | Measures                    | Weight (default) |
| -------------------- | ----------------------- | --------------------------- | ---------------- |
| **Bloom's Taxonomy** | Anderson et al., 2001   | Cognitive level of response | 25%              |
| **Dreyfus Model**    | Dreyfus & Dreyfus, 1980 | Maturity/mastery level 1-5  | 35%              |
| **Big Five (OCEAN)** | Goldberg, 1992          | Behavioral traits           | 10%              |
| **CBI (STAR)**       | McClelland, 1973        | Competency evidence quality | 30%              |

### Bloom Levels

| Level      | Score | Description        | Detection                                              |
| ---------- | ----- | ------------------ | ------------------------------------------------------ |
| remember   | 1     | Recalls facts      | Keywords: "sei", "conheço", "lembro"                   |
| understand | 2     | Explains concepts  | Keywords: "expliquei", "entendi", "conceito"           |
| apply      | 3     | Uses in practice   | Keywords: "apliquei", "implementei", "configurei"      |
| analyze    | 4     | Compares/diagnoses | Keywords: "analisei", "diagnostiquei", "comparei"      |
| create     | 5     | Innovates/designs  | Keywords: "criei", "projetei", "inovei", "arquitetura" |

### Dreyfus Levels

| Level             | Score | Description                      |
| ----------------- | ----- | -------------------------------- |
| Novice            | 1     | Theoretical knowledge only       |
| Advanced Beginner | 2     | Partial, guided application      |
| Competent         | 3     | Stable, consistent execution     |
| Proficient        | 4     | Autonomous, adaptive application |
| Expert            | 5     | Intuitive, contextual mastery    |

### Big Five (OCEAN) Traits

| Factor                      | Measures                                   |
| --------------------------- | ------------------------------------------ |
| **O**penness                | Innovation, learning curiosity             |
| **C**onscientiousness       | Rigor, results focus                       |
| **E**xtraversion            | Communication, leadership                  |
| **A**greeableness           | Collaboration, empathy                     |
| **N**euroticism (stability) | Resilience, decision-making under pressure |

### CBI-STAR Components

| Component     | Detects              | Score Impact    |
| ------------- | -------------------- | --------------- |
| **S**ituation | Context described    | Completeness +1 |
| **T**ask      | Challenge identified | Completeness +1 |
| **A**ction    | Steps taken          | Completeness +1 |
| **R**esult    | Outcome measured     | Completeness +1 |

---

## 4. Scoring Pipeline — Step by Step

### Stage 1: Per-Answer Scoring (`ScoreCalculatorService`)

**File:** [app/services/evaluations/score_calculator_service.rb](app/services/evaluations/score_calculator_service.rb)

```
Input:  Answer record (with description, question metadata)
Output: analysis_data (jsonb), final_skill_score (0-5)

Pipeline:
┌─────────────────────────────────────────────────────────────┐
│  1. Extract response text + AI evaluation (comments_response)│
│  2. Parse self_declaration score from AI evaluation          │
│                                                              │
│  3. Run 4 framework classifiers IN PARALLEL:                 │
│     ┌─────────────┐ ┌─────────────┐ ┌──────────┐ ┌────────┐│
│     │BloomClassify│ │DreyfusScore │ │BigFiveAnal│ │CBI Eval││
│     │ → level 1-5 │ │ → level 1-5 │ │ → OCEAN   │ │ → STAR ││
│     └─────────────┘ └─────────────┘ └──────────┘ └────────┘│
│                                                              │
│  4. Calculate context_score from Bloom + Dreyfus + CBI       │
│  5. base_score = (0.6 × self_declaration) + (0.4 × context)  │
│  6. framework_score = weighted sum of all 4 frameworks       │
│  7. weighted = (base_score × 0.6) + (framework_score × 0.4)  │
│  8. Apply penalties (inflation, generic, copied)             │
│  9. Apply bonuses (humility, exceptional evidence)           │
│  10. final_skill_score = clamp(0.0, 5.0)                    │
│                                                              │
│  11. Store analysis_data + final_skill_score on Answer       │
└─────────────────────────────────────────────────────────────┘
```

**Core Formula:**

```
base = (0.6 × SelfDeclaration) + (0.4 × Context)
weighted = (base × 0.6) + (framework_score × 0.4)
final = weighted - penalties + bonuses    [clamped 0-5]
```

**Penalties:**

| Situation        | Value | Detection                         |
| ---------------- | ----- | --------------------------------- |
| Score inflation  | -1.0  | Self-declaration 4-5, context < 2 |
| Generic response | -0.5  | No specific projects/metrics      |
| Lack of context  | -0.3  | < 2 STAR evidences                |
| Appears copied   | -1.0  | Official documentation text       |

**Bonuses:**

| Situation            | Value | Detection                       |
| -------------------- | ----- | ------------------------------- |
| Humility             | +0.5  | Self-declaration 3, context 4-5 |
| Exceptional evidence | +0.3  | Open source, quantified metrics |

### Stage 2: Aggregate Score (`EvaluationAggregateService`)

**File:** [app/services/evaluations/evaluation_aggregate_service.rb](app/services/evaluations/evaluation_aggregate_service.rb)

```
Input:  EvaluationCandidate (with all scored answers)
Output: score (0-10), wsi_classification, wsi_level, wsi_summary

Pipeline:
┌──────────────────────────────────────────────────────────┐
│  1. Collect all answers with final_skill_score            │
│  2. Split by competence_type (technical vs behavioral)    │
│  3. Calculate average for each group                      │
│  4. Apply macro weights (default: 70% tech / 30% behav)  │
│  5. Apply seniority multiplier                            │
│  6. Calculate Dreyfus level (average of all answers)      │
│  7. Classify WSI score                                    │
│  8. Update evaluation_candidate record                    │
└──────────────────────────────────────────────────────────┘
```

**Classification Ranges:**

| Range     | Classification | Dreyfus Level     |
| --------- | -------------- | ----------------- |
| 4.5 – 5.0 | Excellent      | Expert            |
| 4.0 – 4.4 | High           | Proficient        |
| 3.0 – 3.9 | Medium         | Competent         |
| 2.0 – 2.9 | Regular        | Advanced Beginner |
| < 2.0     | Low            | Novice            |

**Seniority Weights:**

| Seniority | Technical | Behavioral | Experience | Cultural Fit |
| --------- | --------- | ---------- | ---------- | ------------ |
| junior    | 50%       | 30%        | 10%        | 10%          |
| pleno     | 55%       | 25%        | 10%        | 10%          |
| senior    | 45%       | 25%        | 15%        | 15%          |
| lead      | 35%       | 35%        | 15%        | 15%          |
| manager   | 25%       | 40%        | 15%        | 20%          |

### Stage 3: AI Qualitative Feedback (`AiFeedbackService`)

**File:** [app/services/evaluations/ai_feedback_service.rb](app/services/evaluations/ai_feedback_service.rb)

```
Input:  EvaluationCandidate (with completed answers + WSI scores)
Output: ai_feedback (jsonb) with qualitative analysis

Fields in ai_feedback:
├─ skills_analysis          → Per-skill breakdown
├─ behavioral_analysis      → OCEAN trait evaluation
├─ strengths               → Top 3-5 strengths
├─ weaknesses              → Areas for improvement
├─ recommendation          → APPROVED | ADDITIONAL_ANALYSIS | NOT_RECOMMENDED
├─ full_analysis           → Detailed narrative
├─ summary                 → 2-3 sentence executive summary
└─ next_steps              → Suggested next actions
```

---

## 5. Question Generation — AI Flow

**File:** [app/services/job_suggestion_service.rb](app/services/job_suggestion_service.rb) (method: `generate_evaluation_questions`)

### Input (to AI)

```json
{
  "job": {
    "title": "Senior Ruby Developer",
    "description": "...",
    "skills": ["Ruby on Rails", "PostgreSQL", "Redis", "Docker"],
    "languages": ["Ruby", "JavaScript"],
    "seniority": "senior"
  },
  "wsi_type": "wsi_compact | wsi_compact_plus | query",
  "query": "optional custom instruction"
}
```

### WSI Models

| Model              | Questions | Duration   | Precision | Use Case                                |
| ------------------ | --------- | ---------- | --------- | --------------------------------------- |
| `wsi_compact`      | 6-8       | 5-7 min    | ~90%      | High volume, junior/operational         |
| `wsi_compact_plus` | 8-10      | 6:30-9 min | ~95%      | Critical roles, tech leads, specialized |
| `query`            | 1         | —          | —         | Single question on specific topic       |

### Output (per question)

```json
{
  "title": "De 1 a 5, como avalia seu domínio em Ruby on Rails?",
  "description": "Considere sua experiência prática em projetos reais",
  "response_type": "autodeclaration",
  "competence_type": "technical",
  "bloom_level": "remember",
  "dreyfus_target": 4,
  "ocean_trait": null,
  "framework": "dreyfus",
  "framework_weights": {
    "bloom": 0.2,
    "dreyfus": 0.4,
    "big_five": 0.05,
    "cbi_star": 0.35
  },
  "validation_type_weight": 0.6,
  "category": "avaliacao"
}
```

### Question Types (response_type)

| Type              | Purpose                   | Typical Bloom Level | Weight |
| ----------------- | ------------------------- | ------------------- | ------ |
| `autodeclaration` | Self-assessment 1-5       | remember            | 0.60   |
| `contextual`      | Real-world application    | apply/analyze       | 0.60   |
| `microcase`       | Technical problem solving | analyze/create      | 0.20   |
| `situational`     | Behavioral scenario       | apply               | 0.15   |
| `theoretical`     | Conceptual knowledge      | understand          | 0.05   |

### Question Category

| Category      | Purpose                          |
| ------------- | -------------------------------- |
| `padrao`      | Standard evaluation questions    |
| `avaliacao`   | Skill assessment questions       |
| `situacional` | Behavioral/situational questions |

---

## 6. API Routes

### Authenticated (Recruiter)

| Method   | Endpoint                                             | Purpose                        |
| -------- | ---------------------------------------------------- | ------------------------------ |
| `GET`    | `/v1/users/jobs/:job_id/evaluations`                 | List evaluations for a job     |
| `POST`   | `/v1/users/jobs/:id/suggestion/questions`            | AI-generate WSI questions      |
| `POST`   | `/v1/users/evaluations/evaluations`                  | Create evaluation              |
| `GET`    | `/v1/users/evaluations/evaluations`                  | List evaluations               |
| `GET`    | `/v1/users/evaluations/evaluations/:id`              | Show evaluation                |
| `PATCH`  | `/v1/users/evaluations/evaluations/:id`              | Update evaluation              |
| `DELETE` | `/v1/users/evaluations/evaluations/:id`              | Delete evaluation              |
| `GET`    | `/v1/users/evaluations/:id/dashboard_stats`          | Aggregate stats                |
| `POST`   | `/v1/users/evaluations/:id/:job_id/generate_report`  | Comparative report             |
| `POST`   | `/v1/users/evaluations/process_ai_response`          | Process chatbot AI response    |
| `POST`   | `/v1/users/evaluations/:evaluation_id/questions`     | Create question                |
| `PATCH`  | `/v1/users/evaluations/:evaluation_id/questions/:id` | Update question                |
| `DELETE` | `/v1/users/evaluations/:evaluation_id/questions/:id` | Delete question                |
| `POST`   | `/v1/users/evaluation_candidates`                    | Assign candidate to evaluation |
| `POST`   | `/v1/users/evaluation_candidates/create_collection`  | Bulk assign candidates         |
| `GET`    | `/v1/users/evaluation_candidates`                    | List assigned candidates       |

### Public (Candidate-Facing — No Auth)

| Method | Endpoint                                         | Purpose                      |
| ------ | ------------------------------------------------ | ---------------------------- |
| `GET`  | `/v1/evaluations/:account_uid/:ec_uid`           | Show evaluation info         |
| `GET`  | `/v1/evaluations/:account_uid/:ec_uid/questions` | Get next unanswered question |
| `POST` | `/v1/evaluations/:account_uid/:ec_uid/messages`  | Submit chatbot message       |
| `POST` | `/v1/evaluations/:account_uid/:ec_uid/answers`   | Submit answer                |
| `GET`  | `/v1/evaluations/:account_uid/:ec_uid/answers`   | List answers                 |

---

## 7. Chatbot Channels

### Internal Channel (WebSocket)

- Candidate opens public URL: `{FRONT_URL}/evaluations/{account_uid}/{ec_uid}`
- Frontend connects to `EvaluationChannel` stream: `evaluations:{account_uid}:{ec_uid}`
- Questions served one at a time via ActionCable
- AI responses processed in real-time

### WhatsApp Channel

- Triggered by `Chatbot::EvaluationStarterJob` on `EvaluationCandidate` creation
- Sends WhatsApp template via `Meta::WhatsappService.send_message_by_template`
- Template includes: candidate first name, job title, privacy consent
- Candidate replies → messages processed by AI agent
- Responses sent back via `Meta::WhatsappService`

---

## 8. End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. RECRUITER CREATES EVALUATION                                 │
│    POST /v1/users/evaluations/evaluations                       │
│    { name, job_id, is_chatbot: true, chatbot_channel: 0/1 }    │
│                                                                  │
│ 2. GENERATE WSI QUESTIONS (Optional — can create manually)      │
│    POST /v1/users/jobs/:id/suggestion/questions                 │
│    { wsi_type: "wsi_compact", evaluation_id: 1 }               │
│    → AI generates 6-8 questions with Bloom/Dreyfus/OCEAN/CBI   │
│    → Questions auto-created on evaluation if evaluation_id sent │
│                                                                  │
│ 3. ASSIGN CANDIDATES                                            │
│    POST /v1/users/evaluation_candidates                         │
│    { candidate_id, evaluation_id, apply_id, job_id }            │
│    → Creates EvaluationCandidate record                         │
│    → If WhatsApp: triggers EvaluationStarterJob                 │
│    → Public URL: /evaluations/{account_uid}/{ec_uid}            │
│                                                                  │
│ 4. CANDIDATE TAKES EVALUATION                                   │
│    ┌─ INTERNAL: Opens URL → WebSocket → questions one by one    │
│    └─ WHATSAPP: Receives template → replies → AI processes      │
│                                                                  │
│    For each answer:                                              │
│    a. AI evaluates response → score, is_satisfactory, followup  │
│    b. EvaluationAiResponseService processes:                     │
│       - Creates/updates Answer with conversation rounds          │
│       - ScoreCalculatorService → final_skill_score per answer   │
│       - EvaluationAggregateService → WSI score aggregate        │
│       - Decides: followup? next question? finish?               │
│       - Broadcasts via ActionCable or WhatsApp                  │
│                                                                  │
│ 5. EVALUATION COMPLETES                                         │
│    → EvaluationCandidate.completed = true                       │
│    → Apply status synced                                        │
│    → PerCandidateNotificationJob:                               │
│      - AiFeedbackService → qualitative AI analysis              │
│      - Stores ai_feedback, score, classification, level, summary│
│      - Sends Teams notification to recruiter                    │
│                                                                  │
│ 6. RECRUITER REVIEWS                                            │
│    → Dashboard stats (avg score, completion rate)                │
│    → Per-candidate details (strengths, weaknesses, recommendation)│
│    → Comparative report across all candidates                   │
│    → Decision: approve → move to approved_selective_process     │
│               reject → move to rejected_selective_process       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. File Map

### Models

| File                                                                     | Purpose                                             |
| ------------------------------------------------------------------------ | --------------------------------------------------- |
| [app/models/evaluation.rb](app/models/evaluation.rb)                     | Evaluation model with enums, associations, cloning  |
| [app/models/evaluation_candidate.rb](app/models/evaluation_candidate.rb) | Candidate assignment, callbacks for chatbot/scoring |
| [app/models/question.rb](app/models/question.rb)                         | Question with WSI metadata fields                   |
| [app/models/answer.rb](app/models/answer.rb)                             | Answer with scoring data                            |
| [app/models/issue.rb](app/models/issue.rb)                               | Candidate-reported problems during screening        |

### Scoring Services

| File                                                                                                                 | Purpose                                                 |
| -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| [app/services/bloom_classifier.rb](app/services/bloom_classifier.rb)                                                 | Keyword-based Bloom level classification                |
| [app/services/dreyfus_scorer.rb](app/services/dreyfus_scorer.rb)                                                     | Regex-based maturity detection + self-declaration blend |
| [app/services/cbi_evaluator.rb](app/services/cbi_evaluator.rb)                                                       | STAR component extraction via regex                     |
| [app/services/big_five_analyzer.rb](app/services/big_five_analyzer.rb)                                               | OCEAN trait scoring via keywords                        |
| [app/services/evaluations/score_calculator_service.rb](app/services/evaluations/score_calculator_service.rb)         | Orchestrates 4 frameworks → per-answer score            |
| [app/services/evaluations/evaluation_aggregate_service.rb](app/services/evaluations/evaluation_aggregate_service.rb) | Aggregates all answers → WSI final score                |
| [app/services/evaluations/ai_feedback_service.rb](app/services/evaluations/ai_feedback_service.rb)                   | LLM qualitative analysis after scoring                  |

### Question Generation

| File                                                                             | Purpose                                         |
| -------------------------------------------------------------------------------- | ----------------------------------------------- |
| [app/services/job_suggestion_service.rb](app/services/job_suggestion_service.rb) | AI generates WSI questions from job description |

### Chatbot Processing

| File                                                                                             | Purpose                                                           |
| ------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------- |
| [app/services/evaluation_ai_response_service.rb](app/services/evaluation_ai_response_service.rb) | Processes AI chatbot responses, creates answers, triggers scoring |
| [app/services/chatbot/evaluation/starter.rb](app/services/chatbot/evaluation/starter.rb)         | WhatsApp chatbot starter                                          |

### Controllers

| File                                                                                                                                     | Purpose                                  |
| ---------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| [app/controllers/v1/users/evaluations/evaluations_controller.rb](app/controllers/v1/users/evaluations/evaluations_controller.rb)         | CRUD + dashboard_stats + generate_report |
| [app/controllers/v1/users/evaluation_candidates_controller.rb](app/controllers/v1/users/evaluation_candidates_controller.rb)             | CRUD + create_collection                 |
| [app/controllers/v1/users/jobs/suggestions_controller.rb](app/controllers/v1/users/jobs/suggestions_controller.rb)                       | AI question generation                   |
| [app/controllers/v1/evaluations/evaluation_candidates_controller.rb](app/controllers/v1/evaluations/evaluation_candidates_controller.rb) | Public: show evaluation info             |
| [app/controllers/v1/evaluations/questions_controller.rb](app/controllers/v1/evaluations/questions_controller.rb)                         | Public: serve next unanswered question   |
| [app/controllers/v1/evaluations/answers_controller.rb](app/controllers/v1/evaluations/answers_controller.rb)                             | Public: submit answers + trigger scoring |

### Jobs/Workers

| File                                                                                                             | Purpose                                        |
| ---------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| [app/jobs/chatbot/evaluation_starter_job.rb](app/jobs/chatbot/evaluation_starter_job.rb)                         | Starts WhatsApp chatbot                        |
| [app/jobs/evaluations/per_candidate_notification_job.rb](app/jobs/evaluations/per_candidate_notification_job.rb) | AI feedback + Teams notification on completion |

### Serializers

| File                                                                                                   | Key WSI Fields                                                 |
| ------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------- |
| [app/serializer/evaluation_serializer.rb](app/serializer/evaluation_serializer.rb)                     | is_screening, chatbot_channel, ai_enabled                      |
| [app/serializer/evaluation_candidate_serializer.rb](app/serializer/evaluation_candidate_serializer.rb) | score, wsi_classification, wsi_level, wsi_summary, ai_feedback |
| [app/serializer/question_serializer.rb](app/serializer/question_serializer.rb)                         | All WSI metadata fields                                        |
| [app/serializer/answer_serializer.rb](app/serializer/answer_serializer.rb)                             | analysis_data, final_skill_score                               |

### Reference

| File                                                         | Purpose                                        |
| ------------------------------------------------------------ | ---------------------------------------------- |
| [WSI_METHODOLOGY_REFERENCE.md](WSI_METHODOLOGY_REFERENCE.md) | Full WSI methodology specification (534 lines) |

---

## 10. WebSocket Channels

| Channel                                | Stream                               | Purpose                          |
| -------------------------------------- | ------------------------------------ | -------------------------------- |
| `EvaluationChannel`                    | `evaluations:{account_uid}:{ec_uid}` | Real-time chatbot Q&A (internal) |
| `EvaluationCandidateCollectionChannel` | `{user_id}_collection`               | Bulk operation progress          |

---

## 11. Per-Account Configuration

Both `ScoreCalculatorService` and `EvaluationAggregateService` read from `account.sourcing_config["wsi_scoring"]`:

```json
{
  "wsi_scoring": {
    "framework_weights": {
      "bloom": 0.25,
      "dreyfus": 0.35,
      "big_five": 0.1,
      "cbi_star": 0.3
    },
    "type_weights": {
      "autodeclaration": 0.6,
      "contextual": 0.6,
      "microcase": 0.2
    },
    "penalties": { "score_inflation": 1.0, "generic_response": 0.5 },
    "bonuses": { "humility": 0.5, "exceptional_evidence": 0.3 },
    "macro_distribution": { "technical": 0.7, "behavioral": 0.3 },
    "seniority_weights": {
      "senior": {
        "technical": 0.45,
        "behavioral": 0.25,
        "experience": 0.15,
        "cultural_fit": 0.15
      }
    }
  }
}
```

---

## 12. Key Callbacks & Side Effects

| Event                           | Trigger               | Side Effect                                                           |
| ------------------------------- | --------------------- | --------------------------------------------------------------------- |
| `EvaluationCandidate` created   | `after_create_commit` | Starts WhatsApp chatbot (if channel=whatsapp)                         |
| `EvaluationCandidate` created   | `after_create_commit` | Creates activity log                                                  |
| `EvaluationCandidate` completed | `after_update_commit` | Runs `PerCandidateNotificationJob` → AI feedback + Teams notification |
| `EvaluationCandidate` created   | `before_validation`   | Inherits `is_screening` from evaluation                               |
| `EvaluationCandidate` committed | `after_commit`        | Syncs apply evaluation status                                         |
| Answer created (public)         | Controller logic      | Triggers `ScoreCalculatorService` + `EvaluationAggregateService`      |
