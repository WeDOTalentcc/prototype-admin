# MEMORY — LIA Platform / WeDOTalent

> Arquivo de memória persistente do projeto. Registra marcos, decisões e estado dos sprints ao longo do tempo.

---

## 13/03/2026 — Sprints de Melhoria da Camada de IA (I–V)

Cinco sprints focados em qualidade, robustez e rastreabilidade da camada de inteligência artificial foram concluídos. Total de **130 novos testes** criados e passando.

Diagnóstico completo em: `docs/DIAGNOSTICO_CAMADA_IA_v1.0.md`

### Sprint I — Verificação de Infraestrutura Existente
Confirmação de que as seguintes implementações já estavam presentes (nenhuma alteração necessária):
- FairnessGuard middleware universal
- Consent Hard Block
- WorkOS + Billing circuit breakers
- Audit trail WSI
- HITL policy agent

### Sprint II — Qualidade de Prompts e Detecção Semântica
- `interaction_patterns.py` criado
- Few-shot examples adicionados em 9 agentes
- Chain-of-Thought (CoT) adicionado em 6 prompts
- Negation detection implementado em 8 agentes
- Confidence calibration adicionado em 10 agentes
- Anti-sycophancy reforçado em 7 prompts
- Benchmark setorial integrado

### Sprint III — Contextualização Multi-tenant e Aprendizado Contínuo
- `TenantContextService` criado
- Dynamic alpha no RAG (ajuste por tenant/contexto)
- WRF (Weighted Relevance Factor) conectado ao pipeline
- `LearningLoop` integrado ao model drift service
- `ALPHA1_SECTOR_RULES` adicionado ao PolicyEngine

### Sprint IV — Observabilidade, Dados e Segurança de BD
- `agent_metrics.py` criado — métricas Prometheus por agente
- `golden_dataset_seeder.py` criado — 100 candidatos sintéticos para baseline
- Migration `040` — Row-Level Security (RLS) no PostgreSQL
- RAGAS golden queries configuradas para avaliação do RAG

### Sprint V — Fairness Avançado e Serviços de Suporte
- `FairnessGuard.check_with_layer3()` — Layer 3 LLM com controle de custo
- `RecruiterProfileService` criado
- `WSIAsyncSessionService` criado
- Templates de comunicação adicionados/revisados
