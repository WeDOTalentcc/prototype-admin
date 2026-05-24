# ADR-031 — Dois sistemas de automation_rules

**Data:** 2026-05-24  
**Status:** Aceito  
**Contexto:** O termo `automation_rules` aparece em dois contextos de código distintos,
causando ambiguidade ao ler ou debugar a plataforma.

## Decisão

Manter os dois sistemas separados com escopo documentado:

### Sistema 1: Stage Automation Rules (company-level) — `app/api/v1/automation_rules.py`

- **Escopo:** regras de negócio configuráveis por empresa
- **Exemplos:** auto-avançar candidatos de estágio, enviar alertas automáticos, disparar notificações
- **Tabela:** `stage_automation_rules` (legada) + dual-write em `communication_automations` (canonical engine)
- **Status:** DEPRECATED-mas-funcional (WT-2022 P3.2, 2026-05-21)
  - UI continua escrevendo via este endpoint (legacy contract)
  - `StageRuleAdapter` faz dual-write em `communication_automations`
  - **Para novas features:** usar `/api/v1/communication-automations` (canonical)

### Sistema 2: Policy Engine Rules (platform-level) — campo `automation_rules` em `CompanyHiringPolicy`

- **Escopo:** políticas de configuração de automação por empresa (JSONB em `company_hiring_policies`)
- **Exemplos:** `auto_screening`, `auto_scheduling`, `auto_stage_advance`, `autonomy_level`
- **Storage:** `company_hiring_policies.automation_rules` (JSONB)
- **Acessado via:** `app/api/v1/hiring_policy.py`, `app/api/v1/ai_config.py`, `app/api/v1/learning_loops_config.py`

## Distinção operacional

| Aspecto | Sistema 1 (Stage Rules) | Sistema 2 (Policy JSONB) |
|---------|------------------------|--------------------------|
| Storage | Tabela dedicada `stage_automation_rules` | JSONB em `company_hiring_policies` |
| Granularidade | Um row por regra, com trigger/conditions/actions | Um campo JSONB com sub-keys |
| Audience | Engine de execução de stages | Configuração de comportamento da LIA |
| Futuro | Migrar para `communication_automations` | Manter em `hiring_policies.automation_rules` |

## Renaming futuro

Quando migração do Sistema 1 para `communication_automations` completar:
- Sistema 1 passa a se chamar definitivamente "communication_automations"
- Sistema 2 pode ser renomeado para `workflow_config` ou `lia_behavior_config` para
  eliminar ambiguidade residual. Deferir até frontend migrado.

## Consequências

- Ao debugar "automation_rules não funciona": identificar primeiro qual sistema
  está envolvido (tabela dedicada vs JSONB em hiring_policies).
- Novos campos de comportamento da LIA vão em System 2 (JSONB em hiring_policies).
- Novas regras de stage automation vão em System 1 via `/communication-automations` (não legado).
