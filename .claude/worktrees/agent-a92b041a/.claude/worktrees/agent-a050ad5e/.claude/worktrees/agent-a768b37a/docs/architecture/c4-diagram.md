# Diagrama C4: Arquitetura Multi-Agent LIA

## Context Diagram (Level 1)

```mermaid
graph TB
    Recruiter[Recruiter/HR User]
    LIA[Plataforma LIA<br/>Multi-Agent System]
    Pearch[Pearch AI<br/>Global Candidate DB]
    MSGraph[Microsoft Graph<br/>Calendar API]
    Gupy[Gupy ATS]
    Pandape[Pandapé ATS]
    WhatsApp[WhatsApp Business]
    
    Recruiter -->|Conversational Requests| LIA
    LIA -->|Search Candidates| Pearch
    LIA -->|Schedule Interviews| MSGraph
    LIA -->|Sync Data| Gupy
    LIA -->|Sync Data| Pandape
    LIA -->|Send Messages| WhatsApp
```

## Container Diagram (Level 2)

```mermaid
graph TB
    subgraph "Plataforma LIA"
        Frontend[Next.js Frontend<br/>React + shadcn/ui]
        Orchestrator[Orchestrator Service<br/>FastAPI + LangGraph]
        Agents[6 Specialized Agents]
        Store[Conversation Store<br/>PostgreSQL]
        Cache[Redis Cache]
        Services[Shared Services<br/>ATS Sync + Analytics]
    end
    
    subgraph "Observability"
        LangSmith[LangSmith<br/>LLM Traces]
        Sentry[Sentry<br/>Error Tracking]
        Prometheus[Prometheus + Grafana<br/>Metrics]
    end
    
    Recruiter[Recruiter] -->|HTTPS| Frontend
    Frontend -->|REST API| Orchestrator
    Orchestrator -->|Delegates| Agents
    Agents -->|Read/Write| Store
    Agents -->|Cache| Cache
    Agents -->|Calls| Services
    Orchestrator -.->|Traces| LangSmith
    Orchestrator -.->|Errors| Sentry
    Agents -.->|Metrics| Prometheus
```

## Component Diagram (Level 3) - Orchestrator & Agents

```mermaid
graph TB
    subgraph "Orchestrator Service"
        IntentRouter[Intent Router<br/>Claude Sonnet 4.5]
        Planner[Task Planner]
        PolicyEngine[Policy Engine]
        StateManager[State Manager]
    end
    
    subgraph "Specialized Agents"
        JobIntake[Job Intake Agent<br/>Vacancy Creation]
        Sourcing[Sourcing Agent<br/>2-Tier Search]
        Screening[Screening Agent<br/>Voice + WhatsApp]
        Evaluation[Evaluation Agent<br/>Scoring + Tests]
        Scheduling[Scheduling Agent<br/>Calendar Coordination]
        Communication[Communication Agent<br/>Omnichannel]
    end
    
    subgraph "Shared Services"
        ATSSync[ATS Sync Service<br/>Gupy + Pandapé]
        Analytics[Analytics Service<br/>Dashboards]
    end
    
    IntentRouter --> Planner
    Planner --> PolicyEngine
    PolicyEngine --> StateManager
    StateManager --> JobIntake
    StateManager --> Sourcing
    StateManager --> Screening
    StateManager --> Evaluation
    StateManager --> Scheduling
    StateManager --> Communication
    JobIntake -.-> ATSSync
    Sourcing -.-> ATSSync
    Scheduling -.-> ATSSync
    Communication -.-> Analytics
```

## Agent Interaction Flow

```mermaid
sequenceDiagram
    participant R as Recruiter
    participant O as Orchestrator
    participant JI as Job Intake Agent
    participant S as Sourcing Agent
    participant SC as Screening Agent
    participant E as Evaluation Agent
    participant SH as Scheduling Agent
    participant C as Communication Agent
    participant DB as PostgreSQL Store
    
    R->>O: "Encontre 5 desenvolvedores Python sênior"
    O->>O: Intent Classification
    O->>S: Delegate to Sourcing Agent
    S->>DB: Check local candidates
    S->>S: Query Pearch AI (if needed)
    S-->>O: Return 5 candidates
    O->>SC: Trigger screening workflow
    SC->>SC: Voice screening + filters
    SC-->>O: Return qualified candidates
    O->>E: Evaluate top 3 candidates
    E->>E: Technical scoring + Big Five
    E-->>O: Return scored candidates
    O->>SH: Schedule interviews
    SH->>SH: Check MS Graph availability
    SH-->>O: Interviews scheduled
    O->>C: Send notifications
    C->>C: Email + WhatsApp outreach
    O-->>R: "5 candidates found, 3 qualified, interviews scheduled"
```

## Data Flow Diagram

```mermaid
graph LR
    subgraph "Input Layer"
        UI[User Input<br/>Conversational]
    end
    
    subgraph "Orchestration Layer"
        Intent[Intent Classification]
        Entity[Entity Extraction]
        Router[Agent Router]
    end
    
    subgraph "Execution Layer"
        Agent1[Job Intake]
        Agent2[Sourcing]
        Agent3[Screening]
        Agent4[Evaluation]
        Agent5[Scheduling]
        Agent6[Communication]
    end
    
    subgraph "Persistence Layer"
        Store[(Conversation Store)]
        Cache[(Redis Cache)]
    end
    
    subgraph "Integration Layer"
        Pearch[Pearch AI]
        MSGraph[MS Graph]
        ATS[Gupy/Pandapé]
    end
    
    UI --> Intent
    Intent --> Entity
    Entity --> Router
    Router --> Agent1
    Router --> Agent2
    Router --> Agent3
    Router --> Agent4
    Router --> Agent5
    Router --> Agent6
    Agent2 --> Pearch
    Agent5 --> MSGraph
    Agent1 --> ATS
    Agent2 --> Store
    Agent5 --> Store
    Agent2 --> Cache
```

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 15.5, React, shadcn/ui, Tailwind CSS |
| **Backend** | FastAPI, Python 3.11 |
| **LLM Orchestration** | LangGraph, LangChain |
| **LLM Model** | Claude Sonnet 4.5 (Anthropic) |
| **Database** | PostgreSQL (Replit) |
| **Cache** | Redis |
| **Observability** | LangSmith, Sentry, Prometheus, Grafana |
| **Feature Flags** | LaunchDarkly or PostHog |
| **Analytics** | PostHog |
| **Code Quality** | SonarCloud, Snyk, Dependabot |
| **APIs** | Pearch AI, Microsoft Graph, OpenMic.ai, Gupy, Pandapé |

## Deployment Architecture

```mermaid
graph TB
    subgraph "Replit Platform"
        Frontend[Next.js<br/>Static Export]
        Backend[FastAPI<br/>uvicorn]
        DB[(PostgreSQL<br/>Neon)]
    end
    
    subgraph "External Services"
        Claude[Anthropic<br/>Claude API]
        Pearch[Pearch AI]
        MSGraph[Microsoft<br/>Graph API]
    end
    
    CDN[Replit CDN] --> Frontend
    Frontend --> Backend
    Backend --> DB
    Backend --> Claude
    Backend --> Pearch
    Backend --> MSGraph
```

## Security & Compliance

| Requirement | Implementation |
|------------|----------------|
| **Secret Management** | Replit Secrets + environment variables |
| **API Authentication** | JWT tokens, OAuth 2.0 (MS Graph) |
| **Data Encryption** | TLS 1.3 in transit, PostgreSQL encryption at rest |
| **Secret Scanning** | GitHub Advanced Security, Semgrep |
| **Dependency Security** | Snyk, Dependabot |
| **LGPD Compliance** | Data retention policies, audit logs |

## Scalability Considerations

| Aspect | Strategy |
|--------|----------|
| **Horizontal Scaling** | Stateless agents, shared conversation store |
| **Rate Limiting** | Per-agent token limits, circuit breakers |
| **Caching** | Redis for candidate searches, entity extraction |
| **Database** | Connection pooling, read replicas |
| **LLM Costs** | Token budgets per agent, fallback strategies |

## Observability Metrics

| Metric | Tool |
|--------|------|
| **LLM Traces** | LangSmith |
| **Error Tracking** | Sentry |
| **Latency** | Prometheus |
| **Token Usage** | LangSmith + custom metrics |
| **Agent Performance** | Grafana dashboards |
| **User Analytics** | PostHog |
| **Code Quality** | SonarCloud |
