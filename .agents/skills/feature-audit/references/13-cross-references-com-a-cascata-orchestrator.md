# Cross-references com a cascata (orchestrator)

> Parte da skill `feature-audit`. Carregue quando precisar deste topico especifico.

Esta skill e ATIVADA sempre ao final de modo BUILD/REFACTOR/AUDIT pela `lia-orchestrator`. Quando uma dimensao falha, dispare a skill correspondente:

| Dimensao falha | Skill a acionar |
|---|---|
| D1 Integracao, D7 Consistencia, D13 Seguranca/duplicatas | `canonical-fix` |
| D3 UI/DS | `design-standardize` (+ `frontend-design` se for tela nova de entrada) |
| D4 Backend | `backend-quality` |
| D7 Tipos / contratos | `backend-quality` (Pydantic) ou `vue-migration-prep` (props) |
| D9 Arquitetura de agentes, D10 Qualidade LLM, D12 Governanca IA | `ai-architecture` + `lia-compliance` PARTE 1 + PARTE 3 |
| D11 Servicos IA / integracoes | `integration-patterns` |
| D13 Seguranca/PII, D14 Performance | `lia-compliance` PARTE 4 + `backend-quality` PARTE 4 (N+1) |
