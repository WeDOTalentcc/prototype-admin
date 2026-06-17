# IA Layer — Benefits + PRV Audit

> Data: 2026-04-30 | Fase 4 do plano Benefits+PRV | Maturidade atual: ~45%

## 1. Pré-mapeamento: 17 domínios com agents

| Domínio | Pasta agents/ |
|---------|--------------|
| analytics | app/domains/analytics/agents/ |
| ats_integration | app/domains/ats_integration/agents/ |
| automation | app/domains/automation/agents/ |
| autonomous | app/domains/autonomous/agents/ |
| candidate_self_service | app/domains/candidate_self_service/agents/ |
| communication | app/domains/communication/agents/ |
| company_settings | app/domains/company_settings/agents/ |
| cv_screening | app/domains/cv_screening/agents/ |
| hiring_policy | app/domains/hiring_policy/agents/ |
| interview_scheduling | app/domains/interview_scheduling/agents/ |
| job_management | app/domains/job_management/agents/ |
| offer | app/domains/offer/agents/ |
| pipeline | app/domains/pipeline/agents/ |
| policy | app/domains/policy/agents/ |
| recruiter_assistant | app/domains/recruiter_assistant/agents/ |
| sourcing | app/domains/sourcing/agents/ |
| talent_pool | app/domains/talent_pool/agents/ |

## 2. Pontos de toque IA ↔ Benefits/PRV (5 críticos)

| # | Arquivo | Linha | Status | TODO marker |
|---|---------|-------|--------|-------------|
| 1 | `app/domains/job_management/services/wizard_step_service/stage_salary.py` | 154 | Prosa genérica — sem discriminação por tipo de PRV | `WIZARD-INT:001` |
| 2 | `app/domains/job_management/services/wizard_step_service/stage_salary.py` | 48 | Lista de benefícios sem filtro por elegibilidade/seniority | `WIZARD-INT:002` |
| 3 | `app/orchestrator/action_executor/intents_config.py` | 734 | Sem intents para compensation_policy/PRV/total_package | `WIZARD-INT:003` |
| 4 | `app/domains/offer/services/offer_service.py` | 58 | offered_benefits copiado do snapshot sem validação vs compensation_policy | `WIZARD-INT:004` |
| 5 | `app/domains/analytics/services/compensation_analysis_service.py` | 496 | _analyze_bonus lê política mas não aprende padrões por título×seniority | `LIA-PROACTIVITY:003` |

## 3. Maturidade atual

### Implementado em produção
- FairnessGuard bloqueia discriminação salarial (IMPLICIT_BIAS_TERMS + EN variant)
- Wizard consulta company_benefits (mas como lista de nomes, não estrutura elegibilidade)
- compensation_analysis_service.py lê compensation_policies e compara vs política
- LGPD domain: masking PII, descarte de vagas ATS com mais de 12 meses
- ATS job history (F.3): terceira fonte salarial com fail-open e merge por confiança
- pick_canonical: fusão auditável de 3 fontes (histórico interno, ATS, mercado)

### Gaps identificados
- PRV: wizard trata como prosa "Bônus ou PLR (se aplicável)" — sem tipos discriminados (PLR, bônus meta, stock options, comissão)
- Elegibilidade de benefício por seniority/dept não consultada no wizard antes de apresentar a lista
- Offer agent não valida offered_benefits nem PRV vs compensation_policy vinculada à vaga
- Zero learning loop para PRV patterns por título×seniority (proatividade futura)
- Nenhum intent para compensation_policy workflow (apply, override, confirm_total_package)
- FAIRNESS:001: validação PRV em FairnessGuard.check() ainda não conectada a compensation_policies

## 4. TODO markers plantados nesta fase

| Marker | Arquivo | Linha | Descrição |
|--------|---------|-------|-----------|
| `WIZARD-INT:001` | `wizard_step_service/stage_salary.py` | 154 | Substituir prosa "Bônus ou PLR" por query estruturada a compensation_policies filtrada por seniority/dept |
| `WIZARD-INT:002` | `wizard_step_service/stage_salary.py` | 48 | Filtrar company_benefits por elegibilidade × seniority do job_draft antes de apresentar lista |
| `WIZARD-INT:003` | `orchestrator/action_executor/intents_config.py` | 734 | Adicionar intents: apply_compensation_policy, override_bonus_in_job, confirm_total_package |
| `WIZARD-INT:004` | `offer/services/offer_service.py` | 58 | Carregar compensation_policy vinculada à vaga + validar offered_benefits antes de montar offer |
| `LIA-PROACTIVITY:003` | `analytics/services/compensation_analysis_service.py` | 496 | Aprender padrões de PRV por título×seniority para sugestões proativas |
| `FAIRNESS:001` | `shared/compliance/fairness_guard.py` | 23 | Conectar validação PRV de compensation_policies.applicable_* ao FairnessGuard.check() em runtime |

## 5. Esforço estimado para integração completa

| TODO | Esforço |
|------|---------|
| WIZARD-INT:001 (structured PRV in wizard) | ~40h |
| WIZARD-INT:002 (eligibility × seniority filter) | ~20h |
| WIZARD-INT:003 (new intents) | ~30h |
| WIZARD-INT:004 (offer + PRV validation) | ~30h |
| LIA-PROACTIVITY:003 (ML loop PRV) | ~25h |
| FAIRNESS:001 (FairnessGuard runtime wiring) | ~8h |
| **Total** | **~153h** |

## 6. Próximos passos recomendados

1. Implementar WIZARD-INT:001 + 002 juntos (maior ROI: wizard é o ponto de entrada de toda configuração PRV/benefício)
2. WIZARD-INT:004 antes de liberar fluxo de offer com PRV (evita offer com benefícios inconsistentes vs política)
3. WIZARD-INT:003 para fechar o loop de intenções do orquestrador
4. FAIRNESS:001 como hardening obrigatório antes de produção com compensation_policies ativas
5. LIA-PROACTIVITY:003 como fase ML — iniciar após acumular ~100 vagas com PRV preenchido
