# LIA Multi-Agent System - Agent Contracts

This directory contains the contracts (inputs, outputs, responsibilities) for each specialized agent in the LIA multi-agent recruitment system.

## Architecture Overview

The LIA system uses **6 specialized agents** coordinated by a central **Orchestrator**:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Orchestrator                              │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │Intent Router │  │Task Planner  │  │   State Manager    │    │
│  └──────────────┘  └──────────────┘  └────────────────────┘    │
│  ┌──────────────┐                                               │
│  │Policy Engine │                                               │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  Job Intake   │    │   Sourcing    │    │   Screening   │
│     Agent     │    │     Agent     │    │     Agent     │
└───────────────┘    └───────────────┘    └───────────────┘
        ▼                    ▼                    ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  Evaluation   │    │  Scheduling   │    │Communication  │
│     Agent     │    │     Agent     │    │     Agent     │
└───────────────┘    └───────────────┘    └───────────────┘
```

## Agent Registry

| Agent | Intent | Status | Proto-Agent |
|-------|--------|--------|-------------|
| [Job Intake Agent](./job-intake-agent.md) | `job_intake` | 🟢 Implemented | `job_creation.py` |
| [Sourcing Agent](./sourcing-agent.md) | `candidate_search` | 🟢 Implemented | `candidate_search.py` |
| [Screening Agent](./screening-agent.md) | `candidate_screening` | 🟢 Implemented | Voice screening system |
| [Evaluation Agent](./evaluation-agent.md) | `candidate_evaluation` | 🟡 Planned | - |
| [Scheduling Agent](./scheduling-agent.md) | `interview_scheduling` | 🟢 Implemented | `scheduling` workflow |
| [Communication Agent](./communication-agent.md) | `communication` | 🟡 Planned | - |

## Shared Services

| Service | Responsibility | Status |
|---------|---------------|--------|
| **ATS Sync Service** | Bidirectional sync with Gupy + Pandapé | 🟢 Implemented |
| **Analytics Service** | KPI dashboards, predictive insights | 🟡 Planned |

## Quick Reference

### Intent Routing
```python
"Criar vaga de Python" → job_intake → Job Intake Agent
"Buscar 5 candidatos frontend" → candidate_search → Sourcing Agent
"Agendar entrevista com João" → interview_scheduling → Scheduling Agent
```

### Policy Constraints
- Max Pearch searches/day: 10
- Max voice screenings/day: 20
- Bulk email (>10): Requires approval

### State Management
- Conversation store: PostgreSQL (LangGraph checkpointers)
- In-memory cache: MVP (→ Redis for production)
- Cross-agent context: Shared via StateManager

## Documentation

Each agent has a dedicated contract file:
- `job-intake-agent.md` - Vacancy creation/updates
- `sourcing-agent.md` - Candidate search (2-tier)
- `screening-agent.md` - Voice + WhatsApp screening
- `evaluation-agent.md` - Technical/behavioral scoring
- `scheduling-agent.md` - Interview coordination
- `communication-agent.md` - Omnichannel messaging
