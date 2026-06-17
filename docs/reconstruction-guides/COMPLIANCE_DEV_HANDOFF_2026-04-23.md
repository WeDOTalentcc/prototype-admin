# Compliance — Handoff para o time de dev (2026-04-23)

> Replicação no produto novo (IA repo separada) da camada de compliance end-to-end
> da LIA: Fairness (3 camadas), LGPD (PII masking + audit trail), C3B Layer,
> TenantGuard (multi-tenancy), Protected Attributes SSoT, Right to Contest.
> Este documento é o ponto de entrada; o manual técnico completo é o
> `COMPLIANCE_RECONSTRUCTION_GUIDE.md` (97K, 2.156 linhas).

---

## O que esta camada faz

A camada de compliance é o conjunto de **guarda-corpos obrigatórios** que impedem a LIA de:
- Tomar decisões discriminatórias (gênero, raça, idade, 14 atributos protegidos)
- Vazar PII em logs ou respostas
- Cruzar tenants (company A não pode ver dados da company B)
- Responder a prompts de manipulação ("ignore suas instruções")
- Rodar sem audit trail de decisões
- Negar direito de contestação ao candidato (EU AI Act Art. 86 + LGPD Art. 20)

É a camada **não-negociável**: se falha aqui, a empresa toda quebra — multas LGPD, trabalhistas, potencial EU AI Act. Todas as outras camadas (persona, agentes, tools) devem assumir que compliance está rodando.

---

## Arquitetura: 8 camadas de defesa (C1-C8)

| Camada | Mecanismo | Arquivo no repo LIA (Replit) | Tipo | Blocking |
|--------|-----------|------------------------------|------|----------|
| C1 | `FairnessGuard.check()` — regex 19 categorias, `_PATTERNS_VERSION = 8` | `app/shared/compliance/fairness_guard.py:560` | Computacional | ✅ |
| C2 | `check_implicit_bias()` — 43 termos PT/EN em `IMPLICIT_BIAS_TERMS` | `fairness_guard.py:33-117` | Computacional | Soft warning |
| C3 | `check_semantic()` — `claude-haiku-4-5-20251001`, ativado para `HIGH_IMPACT_ACTIONS` | `fairness_guard.py:807-973` | Inferencial | Condicional |
| C4 | `compliance_block.yaml` — 4 variantes: `decision`/`communication`/`operational`/`defensive` | `app/prompts/shared/compliance_block.yaml` | Inferencial | Diretivo |
| C5 | `guardrails_block.yaml` — 7 seções (identity, prompt_security, multi_tenancy, autonomy, escalation, data_safety, error_handling) | `app/prompts/shared/guardrails_block.yaml` | Inferencial | Diretivo |
| C6 | `protected_attributes.yaml` — 14 atributos SSoT | `app/config/protected_attributes.yaml` | Computacional | ✅ |
| C7 | `fairness_post_check.yaml` — monitoring de saídas (7 domínios, 6 score fields, 5 ranking fields) | `app/config/fairness_post_check.yaml` | Computacional | ✅ |
| C8 | `audit_service.log_decision` — `fairness_audit_log` + `candidate_portal_audit_logs` | `app/shared/compliance/scoring_safeguards.py` + `app/domains/compliance_base.py` | Computacional | Observação |

**Regra de ouro:** YAML é orientação (C4/C5), código é enforcement (C1/C2/C6/C7). Nunca duplicar a lista de atributos no YAML — referenciar `protected_attributes.yaml` (SSoT).

---

## O que muda para o dev no produto novo (IA repo)

### Invariantes obrigatórias

1. **`company_id` SEMPRE do JWT, nunca do payload** — toda query multi-tenant usa `TenantGuard.get_verified_company_id()`. IDOR é gap arquitetural sério.

2. **FairnessGuard é chamado ANTES de LLM em agentes de decisão:**
   ```python
   from app.shared.compliance.fairness_guard import FairnessGuard
   result = FairnessGuard().check(user_input, action="rejection")
   if result.is_blocked:
       return explain_educational(result)
   # prosseguir para LLM
   ```

3. **Audit log em TODA decisão sobre candidato:**
   ```python
   await audit_service.log_decision(
       company_id=company_id,
       subject_id=candidate_id,
       decision_type="cv_screening",
       criteria_used=[...],
       criteria_ignored=[...],  # atributos protegidos sempre aqui
       score_breakdown={...},
   )
   ```

4. **PII nunca em logs** — ADR-006. Logs têm só `candidate_id`, `vacancy_id`, `company_id`. Nunca nome, email completo, CPF, telefone.

5. **`_FORBIDDEN_FIELDS` é SSoT para candidate-facing tools** (em `explain_candidate_decision.py`). Nunca expor `wsi_score`, `lia_score`, `confidence`, `red_flags`, `factors.weight`, `calibration_weights_used`.

6. **Right to Contest (EU AI Act Art. 86 + LGPD Art. 20) é IMUTÁVEL:**
   - Toda rejeição/feedback automatizado deve incluir aviso de direito de contestação
   - Prazo recomendado: 30 dias
   - `compliance_block.yaml` seção `right_to_contest` já tem o template — não duplicar

### O que NÃO precisa fazer

- **NÃO incluir LGPD/fairness em cada domain YAML manualmente.** O `ComplianceDomainPrompt` injeta automaticamente a variante correta (decision/communication/operational).
- **NÃO criar novo list de atributos protegidos.** Consultar `protected_attributes.yaml`.
- **NÃO criar nova regex de viés em cada feature.** Usar `FairnessGuard.check()` com `action` apropriado.
- **NÃO logar detalhes da query do candidato.** Usar IDs apenas.

---

## O que já está implementado na LIA (Replit) e que deve ser replicado

### Fixes aplicados em 2026-04-23 (estado atual canônico)

| Arquivo canônico | O que está lá | Por que copiar ipsis litteris |
|------------------|---------------|-------------------------------|
| `app/prompts/shared/compliance_block.yaml` | 4 variantes + seção `right_to_contest` (EU AI Act Art. 86 + LGPD Art. 20) em `decision` e `communication` | Base legal nas variantes — não inventar texto novo |
| `app/prompts/domains/autonomous.yaml` | `behavioral_rules` + `hitl_escalation` + `compliance_integration` | Agente cross-domain tier 6 exige fairness antes de ações irreversíveis |
| `app/prompts/domains/culture_analysis.yaml` | Bloco `<compliance_hr>` dentro do `system_prompt` | Big Five é proxy conhecido de viés — guardrails explícitos obrigatórios |
| `app/prompts/domains/orchestrator.yaml` | Prologue de compliance no system_prompt | Ponto de entrada — precisa barrar prompt injection + compliance violations |
| `app/shared/compliance/fairness_guard.py` | L1+L2+L3 completo, Redis cache 1h, `FAIRNESS_LAYER3_ENABLED` configurável | Núcleo do enforcement — replicar com mesmo padrão de classes/camadas |
| `app/config/protected_attributes.yaml` | 14 atributos, versão 6 | SSoT — replicar exatamente |
| `app/config/fairness_post_check.yaml` | `enabled: true`, 7 decision_domains | Output monitoring — replicar |

### Endpoint novo candidate-facing (EU AI Act Art. 86)

```
GET /api/v1/candidate/decisions/explain?candidate_token=<JWT>&vacancy_id=<opcional>
```

- Auth: JWT do candidato (`CANDIDATE_PORTAL_JWT_SECRET`) — nunca JWT do recrutador
- `company_id` derivado do token (anti-IDOR)
- Rate limit: 10/hora, 30/dia
- Sanitização de output via `_sanitize_decision()` — nunca expõe scoring bruto
- Audit log via `log_portal_access()`

Arquivos envolvidos:
- `app/api/v1/candidate_portal_explanation.py` (router novo)
- `app/domains/candidate_self_service/tools/explain_candidate_decision.py` (tool novo)
- `app/domains/candidate_self_service/agents/candidate_tool_registry.py` (3 → 4 tools)
- `app/prompts/domains/candidate_self_service.yaml` (regra 8)
- `tests/test_candidate_portal_explanation.py` (contract tests)

### Flag ativada em produção

`FAIRNESS_LAYER3_ENABLED=true` em `.env`. Runbook operacional: `docs/operations/FAIRNESS_LAYER3_RUNBOOK.md`.

---

## Dependência com outras camadas

```
Persona (LIA_PERSONA_RECONSTRUCTION_GUIDE.md)
   ↓ depende de compliance_block.yaml + guardrails_block.yaml
Compliance (ESTE GUIA)  ← IMPLEMENTAR PRIMEIRO
   ↑ consome protected_attributes.yaml (SSoT)
Infrastructure (INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md)
   ↓ toda tool_handler exige audit_service.log_decision
Resilience (RESILIENCE_LEARNING_RECONSTRUCTION_GUIDE.md)
   ↓ circuit breakers em FairnessGuard L3 (claude-haiku-4-5)
```

**Ordem sugerida de implementação no produto novo:**
1. `TenantGuard` + `protected_attributes.yaml` + `FairnessGuard` L1+L2 (fundação)
2. `AuditService` + `fairness_audit_log` (Alembic migration)
3. `compliance_block.yaml` + `ComplianceDomainPrompt` (injeção automática)
4. `guardrails_block.yaml` + `GuardrailsDomainPrompt`
5. `PII masking` (`pii_masking.py`) + `SecurityPatterns`
6. `FairnessGuard` L3 semântico (depende de LLM provider configurado)
7. `fairness_post_check.yaml` + output monitoring
8. Endpoint candidate-facing Art. 86 (depende de tudo acima)

---

## Validação / Testes no produto novo

Replicar os scripts de lint já existentes na LIA:

| Script | O que verifica |
|--------|----------------|
| `scripts/check_c3b_compliance.py` | Todo agente de decisão chama `pre_compliance()` antes da LLM |
| `scripts/check_fairness_consolidation.py` | Serviços de scoring importam de `fairness_guard` canônico (não fork) |
| `scripts/check_tenant_isolation.py` | Endpoints usam `Depends(get_verified_company_id)` |
| `scripts/check_bulk_actions_compliance.py` | Funções `bulk_*` têm C3B + `log_decision()` |

Rodar `pytest tests/integration/test_persona_invariants.py` e `pytest tests/test_candidate_portal_explanation.py` antes de merge em PR que toque em compliance.

---

## Próximos passos pendentes (contextuais — não bloqueiam replicação)

Itens em aberto documentados em `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §11:

- **P1.2 — Bias audit independente com publicação** — 3 sprints (9 semanas), Q3/2026
- **P1.3 — AI Fact Sheets publicadas** — já entregues (Replit); pendente frontend no site
- **P2.1 — Formalizar classificação EU AI Act Anexo III** — pós 02/08/2026
- **P2.5 — SLA formal de incidentes de fairness** — Q4/2026
- **Certificação ISO/IEC 42001:2023** — 2027

Nenhum desses bloqueia a replicação do código — são trilhos regulatórios paralelos.

---

## Ordem de leitura recomendada

1. Este handoff (30 min) — contexto + invariantes
2. `CANONICAL_FILES_BY_THEME.md` tema 1-4 (Fairness/LGPD/C3B/Segurança) — mapa dos arquivos
3. `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §10 (arquitetura 8 camadas) + §11 (plano) — manual completo
4. Abrir cada arquivo canônico listado acima conforme for implementando

**Fonte única de verdade durante implementação:**
- **Manual navegável:** `COMPLIANCE_RECONSTRUCTION_GUIDE.md` — arquitetura, auditoria, plano P0/P1. Se divergir do código canônico no Replit, **o código é a verdade** — abrir issue para atualizar guia.
- **Bundle verbatim dos 2 YAMLs técnicos de compliance:** `COMPLIANCE_YAMLS_CANONICAL_BUNDLE.md` (12K, 284 linhas — novo 2026-04-24). Contém `protected_attributes.yaml` (SSoT dos 14 atributos) + `fairness_post_check.yaml` verbatim. Use como **context file** em Claude Code (`CLAUDE.md`) ou Cursor (`.cursor/rules/compliance-yamls.mdc`). Instruções de setup no próprio bundle.
- **YAMLs cross-referenciados** (`compliance_block.yaml`, `guardrails_block.yaml`) → ver `LIA_YAMLS_CANONICAL_BUNDLE.md`.

---

## Não fazer

- `git push` — commits locais; push manual pelo Paulo via branch `replit-sync`
- Inventar regras de compliance — sempre citar base legal (Lei 9.029/95, CLT 373-A, LGPD Art. 20, EU AI Act Art. 86)
- Duplicar lista de atributos protegidos em YAMLs — referenciar `protected_attributes.yaml`
- Expor scoring bruto/confidence/weights em response candidate-facing
- Rodar agente de decisão sem FairnessGuard
- Log com PII

---

*Handoff gerado em 2026-04-23 | Próxima revisão: trimestral ou triggered por mudança no `protected_attributes.yaml` ou EU AI Act*

---

## Receitas Executáveis — Thematic Operational Docs

Para implementar qualquer tema deste handoff no v5, consulte os docs operacionais em:

**Mac:** `/Users/paulomoraes/Documents/Python/themes/`
**Replit:** `docs/reconstruction-guides/themes/`
**Índice:** `themes/README.md`

Temas mais relevantes para este handoff: C1 (Fairness), C2 (LGPD PII), C3 (Consent), C4 (Art.20), C5 (Multi-tenancy), C6 (Injection), C7 (Audit), C8 (Policy Engine)
