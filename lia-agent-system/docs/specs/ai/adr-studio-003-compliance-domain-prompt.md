# ADR-Studio-003: ComplianceDomainPrompt como herança obrigatória em todos os domínios agentic

**Status:** ACCEPTED  
**Data:** 2026-06-14  
**Origem:** Auditoria ultracode Agent Studio

---

## Contexto

O Agent Studio da WeDOTalent expõe 22 domínios agentic registrados (analytics, ats_integration, automation, candidate_self_service, communication, company_settings, cv_screening, hiring_policy, interview_intelligence, interview_scheduling, job_management, offer, pipeline, recruiter_assistant, recruitment_campaign, sourcing, talent_intelligence, talent_pool, agent_studio, job_creation, digital_twin, workforce). Cada domínio processa texto livre de recrutadores e/ou candidatos antes de enviá-lo a LLMs. Sem enforcement estrutural, um desenvolvedor pode criar ou registrar um novo domínio que herde diretamente de `DomainPrompt` e jamais aplique FairnessGuard (discriminação em recrutamento — CLT Art. 373-A / Lei 9.029/95), PII Strip (minimização de dados pessoais — LGPD Art. 12 / EU AI Act Art. 13), PromptInjectionGuard ou FactChecker. A falha seria silenciosa: o domínio funcionaria normalmente, a cobertura de compliance simplesmente não existiria. Auditoria de 2026-06-14 confirmou que o FairnessGuard já estava ausente de superfícies como hiring_policy, pipeline_orchestrator e task_planner antes de correção pontual — evidência de que a abordagem de "chamada explícita por método" não é confiável em um codebase com múltiplos desenvolvedores paralelos.

## Decisão

Toda classe de domínio agentic registrada em `_REGISTERED_DOMAINS` DEVE herdar de `ComplianceDomainPrompt` (definida em `app/domains/compliance_base.py`) em vez de herdar diretamente de `DomainPrompt`. `ComplianceDomainPrompt` estende `DomainPrompt` e implementa automaticamente os hooks `pre_process` e `post_process` do ciclo `DomainWorkflow`, aplicando em sequência: Layer 1 — FairnessGuard (viés discriminatório explícito e implícito, com Layer 3 semântica para estágios de alto impacto via `StageContext.is_high_impact`); Layer 2 — PII Strip (CPF, e-mail, telefone, RG, CNPJ, quasi-identificadores) antes do envio ao vendor LLM; Layer 3 — PromptInjectionGuard (fail-safe quando indisponível); e, em `post_process`, FactChecker sobre claims numéricos na resposta. O enforcement é garantido pelo sensor computacional `tests/contract/test_domain_structure_conformance.py`, que parametriza sobre todos os domínios de `_REGISTERED_DOMAINS` e falha em CI (`assert "ComplianceDomainPrompt" in content`) se qualquer `domain.py` não referenciar a classe. O CI bloqueia merge; nenhuma PR que introduza domínio não-conforme pode ser integrada.

## Alternativas Consideradas

1. Middleware FastAPI: interceptar todas as requisições de domínio via middleware HTTP. Descartado porque o middleware opera sobre o payload HTTP já serializado, enquanto a camada de compliance precisa inspecionar o texto natural antes da chamada ao LLM — o que ocorre dentro do método de domínio, não na borda HTTP. Além disso, rotas internas (tool calls entre agentes) não passam pelo middleware FastAPI.
2. Decorator por método: aplicar um decorator `@compliance_required` em cada método `handle` de domínio. Descartado porque decorators são opcionais por natureza — o desenvolvedor precisa lembrar de aplicá-los e o linter não detecta ausência de decorator em método abstrato. A saga de 2026-06-14 (3 endpoints sem cobertura) ocorreu exatamente com chamadas explícitas.
3. Chamadas explícitas por método: cada domínio chama `FairnessGuard().check(...)`, `strip_pii(...)` etc. diretamente no corpo do `handle`. Descartado como padrão primário porque é a abordagem que falhou: auditoria 2026-06-14 encontrou hiring_policy, pipeline_orchestrator e task_planner sem cobertura. Com 22+ domínios e desenvolvimento paralelo, a probabilidade de omissão é estruturalmente alta.
4. Mixin de compliance: definir `ComplianceMixin` sem relação de herança com `DomainPrompt`. Descartado porque mixins Python não garantem ordem de resolução de método (MRO) de forma previsível com herança múltipla, e o sensor de CI exigiria lógica AST mais complexa para detectar composição vs. herança simples.

## Consequências

### Positivas
- Impossível bypassar por esquecimento: o sensor CI parametrizado sobre `_REGISTERED_DOMAINS` bloqueia qualquer domínio que não declare `ComplianceDomainPrompt` — a omissão vira falha de build, não de runtime.
- Ponto único de enforcement: FairnessGuard, PII Strip, PromptInjectionGuard e FactChecker vivem em um único arquivo (`compliance_base.py`, 712 linhas) — ajuste de regra de compliance aplica automaticamente a todos os 22 domínios.
- Audit trail automático: `log_check()` e `FairnessAuditLog` são chamados internamente pelo `pre_process` da classe base, sem necessidade de código nos domínios filhos — cada bloqueio gera registro auditável com `session_id` e `correlation_id`.
- Escalabilidade: novo domínio adicionado a `_REGISTERED_DOMAINS` herda compliance completo sem nenhuma linha extra de código no domínio — o padrão é grátis para quem segue a convenção.
- Conformidade legal por design: LGPD Art. 12 (minimização), CLT Art. 373-A (anti-discriminação em recrutamento) e EU AI Act Art. 13 (transparência) são satisfeitos estruturalmente, não por disciplina individual de desenvolvimento.
- Estágios de alto impacto recebem tratamento diferenciado via `StageContext.is_high_impact`: shortlist, rejeição e oferta ativam Layer 3 semântica do FairnessGuard — granularidade impossível em middleware HTTP genérico.

### Negativas / Trade-offs
- Acoplamento de hierarquia de classes: domínios estão acoplados à classe base de compliance — mudança de interface em `ComplianceDomainPrompt` (assinatura de `pre_process`/`post_process`) pode exigir ajustes em todos os 22 domínios filhos.
- Testes de domínio requerem mock da classe base: testes unitários de lógica de domínio precisam mockar ou stub os hooks de compliance para isolar o comportamento específico do domínio, aumentando complexidade de setup.
- Domínios com regras de compliance divergentes precisam sobrescrever `_compliance_config`: não há como desabilitar compliance para um domínio específico sem override explícito — o que é intencional mas pode gerar fricção em casos de uso internos (ex: domínio de teste ou diagnóstico).
- Latência adicional por domínio: FairnessGuard + PII Strip + PromptInjectionGuard executam em `pre_process` de toda requisição — em domínios de baixo risco (ex: analytics read-only) o custo é pago igualmente, sem otimização seletiva por padrão.

## Sensores

- tests/contract/test_domain_structure_conformance.py — sensor computacional parametrizado sobre `_REGISTERED_DOMAINS` (22 domínios); `TestRegisteredDomains.test_inherits_compliance` verifica presença literal de 'ComplianceDomainPrompt' em cada `domain.py`; executa em CI e bloqueia merge em caso de falha (LIA-C01).
- tests/unit/test_fairness_audit_trail.py — 11 testes verificando que `log_check()` é chamado com `session_id` e `company_id` ao passar por `ComplianceDomainPrompt.pre_process`; detecta regressão no audit trail de FairnessGuard.
- tests/unit/test_fairness_session_correlation.py — 11 testes verificando que `FairnessAuditLog.session_id` e `FairnessPolicyViolation.correlation_id` são preenchidos corretamente; detecta drift no rastreamento de bloqueios entre sessões.

## Arquivos Canônicos

- `/home/runner/workspace/lia-agent-system/app/domains/compliance_base.py`
- `/home/runner/workspace/lia-agent-system/tests/contract/test_domain_structure_conformance.py`
- `/home/runner/workspace/lia-agent-system/app/domains/base.py`
- `/home/runner/workspace/lia-agent-system/app/shared/compliance/fairness_guard.py`
