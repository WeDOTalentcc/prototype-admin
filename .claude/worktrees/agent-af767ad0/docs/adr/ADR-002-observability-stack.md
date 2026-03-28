# ADR-002: Stack de Observabilidade & Qualidade para Multi-Agent System

**Status:** Aceito  
**Data:** 2025-11-24  
**Decisor:** Equipe Técnica LIA  

## Contexto

Com a implementação de arquitetura multi-agente (Orchestrator + 6 agentes), precisamos definir stack completo de ferramentas para observabilidade, qualidade de código, monitoramento, feature flags e segurança.

## Decisão

### ✅ MUST-HAVE (Blocker para Produção)

#### 1. Observabilidade LLM/Agents
- **LangSmith**
  - Traces completos de orquestração LangGraph
  - Rastreio de latência por agente
  - Custo de tokens e confidence scores
  - **Custo:** Alto em produção, mas essencial

#### 2. Error Tracking
- **Sentry**
  - Frontend (Next.js) + Backend (FastAPI)
  - Stack traces, alertas, session replay
  - **Integração:** Python + TypeScript

#### 3. Métricas de Infraestrutura
- **Prometheus + Grafana**
  - Métricas custom (latência, throughput, taxa de fallback)
  - Open-source, controle total
  - Dashboards por agente

#### 4. Qualidade de Código
- **SonarCloud**
  - Cobre Python + TypeScript
  - Integração GitHub Actions
  - Code smells, duplicação, vulnerabilidades, coverage
  - **Alternativa rejeitada:** CodeClimate (overlap)

#### 5. Segurança
- **Dependabot + Snyk**
  - Dependências vulneráveis
  - Supply chain security
- **GitHub Advanced Security** ou **Semgrep**
  - Secret scanning, CodeQL
- **Replit Secrets**
  - Gestão centralizada de chaves

#### 6. Feature Flags
- **LaunchDarkly** (preferencial)
  - Rollout controlado de cada agente
  - Ativar/desativar sem deploy
- **Alternativa:** PostHog (se quiser consolidar vendor)
- **Open-source:** Unleash (se custo for blocker)

#### 7. Product Analytics
- **PostHog**
  - Analytics, session replay, event pipelines
  - Feature flags integrados
  - **Alternativa rejeitada:** Mixpanel/Amplitude (nice-to-have)

#### 8. Log Aggregation
- **OpenSearch/Elasticsearch**
  - Logs centralizados de todos os agentes
  - Query por intent, agente, user_id

### ⭐ NICE-TO-HAVE (Phase 2)

- **Datadog/New Relic** - APM unificado
- **BetterStack/Pingdom** - Uptime monitoring
- **Mixpanel/Amplitude** - Analytics avançado

### ❌ DESNECESSÁRIO

- **Maxim AI** - Redundante com LangSmith + custom dashboards
- **CodeClimate** - Overlap com SonarCloud

## Justificativa

### LangSmith (Must-Have)
- **Único** com observabilidade específica para LangGraph
- Essencial para debugar orquestração multi-agente
- Traces completos de cada decisão do orchestrator

### Sentry (Must-Have)
- Error tracking frontend/backend consolidado
- Session replay para debugging UX
- Alertas em tempo real

### Prometheus + Grafana (Must-Have)
- Open-source, sem vendor lock-in
- Métricas custom por agente
- Dashboards flexíveis

### SonarCloud (Must-Have)
- CI/CD integrado (GitHub Actions)
- Quality gates automáticos
- Cobre Python + TypeScript

### PostHog (Must-Have)
- Consolida analytics + feature flags
- Reduz número de vendors
- Session replay + event pipelines

### LaunchDarkly (Must-Have)
- Líder de mercado em feature flags
- Critical para rollout gradual de agentes
- Granularidade por usuário/tenant

## Consequências

### Positivas:
- ✅ Observabilidade completa de orquestração multi-agente
- ✅ Debugging eficiente com traces LangSmith
- ✅ Qualidade de código garantida (SonarCloud)
- ✅ Rollout controlado de agentes (LaunchDarkly)
- ✅ Segurança proativa (Snyk, secret scanning)

### Negativas:
- ⚠️ Custo de múltiplos vendors (LangSmith + LaunchDarkly + PostHog)
- ⚠️ Complexidade de setup inicial
- ⚠️ Necessidade de treinamento da equipe

### Mitigações:
- Começar com tier gratuito de cada ferramenta
- Avaliar PostHog como alternativa a LaunchDarkly (reduzir vendors)
- Documentação completa de setup

## Roadmap de Implementação

**Phase 1** (Imediato):
1. Configurar LangSmith + Sentry + Prometheus
2. Habilitar SonarCloud + Dependabot/Snyk no CI/CD
3. Setup PostHog para analytics

**Phase 2** (Após MVP Orchestrator):
4. Configurar LaunchDarkly (ou PostHog feature flags)
5. OpenSearch/Elasticsearch para log aggregation
6. Dashboards Grafana por agente

**Phase 3** (Produção):
7. Alertas e on-call policies
8. Documentação de runbooks
9. Training da equipe

## Custo Estimado (mensal)

- **LangSmith:** ~$100-300 (volume moderado)
- **Sentry:** ~$26 (tier Developer)
- **SonarCloud:** Gratuito (open-source project)
- **Snyk:** Gratuito (open-source project)
- **LaunchDarkly:** ~$20 (Starter) ou PostHog (gratuito)
- **PostHog:** Gratuito até 1M events/mês
- **Prometheus + Grafana:** Gratuito (self-hosted)

**Total:** ~$150-350/mês (pode reduzir para ~$130 com PostHog flags)

## Referências

- LangSmith: https://docs.smith.langchain.com/
- Sentry: https://docs.sentry.io/
- SonarCloud: https://sonarcloud.io/
- PostHog: https://posthog.com/
- LaunchDarkly: https://launchdarkly.com/
