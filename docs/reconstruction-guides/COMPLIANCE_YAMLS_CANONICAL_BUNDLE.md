# Compliance — Canonical YAMLs Bundle (2026-04-24)

> Bundle dedicado com **verbatim dos 2 YAMLs canônicos de Compliance**
> (technical config of fairness + protected attributes (SSoT)). Lido direto de `lia-agent-system/` no Replit em 2026-04-24. Tamanho total: 6.3 KB.
>
> **Fonte única de verdade:** o código em `lia-agent-system/`.
> **Guia de navegação:** `COMPLIANCE_RECONSTRUCTION_GUIDE.md`.
> **Handoff dev:** `COMPLIANCE_DEV_HANDOFF_2026-04-23.md` (Card 2 — Compliance).

---

## Como usar este bundle com AI assistants

### Claude Code (CLI)
Adicionar em `CLAUDE.md` do repo novo:
```
## Referência canônica — YAMLs de Compliance
Consulte `COMPLIANCE_YAMLS_CANONICAL_BUNDLE.md` para verbatim de qualquer YAML
da camada de compliance antes de replicar.
```
Claude Code lerá `COMPLIANCE_YAMLS_CANONICAL_BUNDLE.md` automaticamente quando for replicar ou editar qualquer YAML listado.

### Cursor
Salvar em `.cursor/rules/compliance-yamls.mdc`:
```
---
description: Verbatim canônico dos YAMLs da camada de Compliance
alwaysApply: false
---
Este arquivo é a fonte verbatim dos YAMLs de Compliance. Quando usuário pedir
para replicar, editar ou consultar qualquer YAML listado aqui, use o
conteúdo exato deste bundle.
```
Invocar na chat via: `@compliance-yamls replica o <nome>.yaml`

### Manual (ctrl+F)
Busque pelo nome do YAML (ex.: `cv_screening.yaml`). Cada YAML tem header com path canônico + linhas + bloco ```yaml verbatim.

---

## Índice (2 YAMLs)

| # | YAML | Path canônico | Linhas | Versão | Updated |
|---|---|---|---|---|---|
| 1 | `protected_attributes.yaml` | `app/config/protected_attributes.yaml` | 158 | 6 | — |
| 2 | `fairness_post_check.yaml` | `app/config/fairness_post_check.yaml` | 39 | — | — |

---

## Princípios de fidelidade

- Todo byte de YAML foi lido direto de `lia-agent-system/` (Replit) em 2026-04-24. Zero paráfrase, zero invenção.
- **Código é fonte de verdade.** Se divergir do bundle, abrir issue para atualizar o bundle.
- Atualização: triggered por mudança em YAML canônico + revisão trimestral.

## Cross-references com outros bundles

- **Persona + Agent prompts + Platform manifest + Agent templates + Intelligence floor** → `LIA_YAMLS_CANONICAL_BUNDLE.md`
- **Compliance técnico** (protected_attributes, fairness_post_check) → `COMPLIANCE_YAMLS_CANONICAL_BUNDLE.md`
- **Infraestrutura** (tool_permissions, domain_routing, agents_registry, tool_registry_metadata, 17 capabilities) → `INFRASTRUCTURE_YAMLS_CANONICAL_BUNDLE.md`

---

## YAMLs canônicos de Compliance

Technical config consumido pelo FairnessGuard, audit_service e validadores. Não é injetado em prompt — é lido por código Python.

### Arquivo canônico: `app/config/protected_attributes.yaml`

**Linhas:** 158  |  **Bytes:** 5597

```yaml
# Protected Attributes — Single Source of Truth
#
# Every system that needs to know which attributes are protected for anti-discrimination
# purposes MUST consume this file via app.shared.compliance.protected_attributes.
#
# Adding/removing an attribute here propagates to: FairnessGuard, BiasAuditService,
# Learning pattern validation, prompt injection, and any future consumer.
#
# Legal basis: LGPD Art. 11, CLT Art. 373-A, Lei 9.029/95, EU AI Act Annex III item 4.

version: 6  # Bump when adding/removing attributes

attributes:
  - id: genero
    name_pt: "Gênero"
    name_en: "Gender"
    aliases_pt: ["gênero", "genero", "sexo"]
    aliases_en: ["gender", "sex"]
    db_fields: ["gender", "genero", "sex", "sexo"]
    category: identity
    legal_basis: "CLT Art. 373-A, Lei 9.029/95, CF Art. 5º"
    bias_audit_enabled: true
    bias_audit_dimension: gender

  - id: raca_etnia
    name_pt: "Raça/Etnia"
    name_en: "Race/Ethnicity"
    aliases_pt: ["raça", "raca", "etnia", "cor"]
    aliases_en: ["race", "ethnicity", "skin_color", "color"]
    db_fields: ["race", "raca", "ethnicity", "etnia", "skin_color", "cor_pele"]
    category: identity
    legal_basis: "Lei 7.716/89, CF Art. 5º"
    bias_audit_enabled: true
    bias_audit_dimension: race_ethnicity

  - id: idade
    name_pt: "Idade"
    name_en: "Age"
    aliases_pt: ["idade", "data de nascimento", "faixa etária"]
    aliases_en: ["age", "birth_date", "date_of_birth", "age_group"]
    db_fields: ["age", "idade", "birth_date", "data_nascimento", "date_of_birth"]
    category: identity
    legal_basis: "Lei 10.741/03 (Estatuto do Idoso), CF Art. 5º"
    bias_audit_enabled: true
    bias_audit_dimension: age_group

  - id: religiao
    name_pt: "Religião"
    name_en: "Religion"
    aliases_pt: ["religião", "religiao", "fé", "credo"]
    aliases_en: ["religion", "faith", "creed"]
    db_fields: ["religion", "religiao"]
    category: belief
    legal_basis: "CF Art. 5º, VI"
    bias_audit_enabled: false

  - id: orientacao_sexual
    name_pt: "Orientação Sexual"
    name_en: "Sexual Orientation"
    aliases_pt: ["orientação sexual", "orientacao_sexual"]
    aliases_en: ["sexual_orientation", "orientation"]
    db_fields: ["sexual_orientation", "orientacao_sexual"]
    category: identity
    legal_basis: "STF ADO 26"
    bias_audit_enabled: false

  - id: estado_civil
    name_pt: "Estado Civil"
    name_en: "Marital Status"
    aliases_pt: ["estado civil", "estado_civil"]
    aliases_en: ["marital_status", "marital"]
    db_fields: ["marital_status", "estado_civil"]
    category: identity
    legal_basis: "CLT"
    bias_audit_enabled: false

  - id: deficiencia
    name_pt: "Deficiência"
    name_en: "Disability"
    aliases_pt: ["deficiência", "deficiencia", "pcd", "pne"]
    aliases_en: ["disability", "handicap", "impairment"]
    db_fields: ["disability", "deficiencia", "pcd", "diversity_disability"]
    category: health
    legal_basis: "Lei 8.213/91, Lei 13.146/15"
    bias_audit_enabled: true
    bias_audit_dimension: disability

  - id: maternidade_paternidade
    name_pt: "Maternidade/Paternidade"
    name_en: "Maternity/Paternity"
    aliases_pt: ["maternidade", "paternidade", "gravidez", "gestante"]
    aliases_en: ["maternity", "paternity", "pregnancy", "pregnant"]
    db_fields: []
    category: family
    legal_basis: "CLT Art. 373-A, Lei 9.029/95"
    bias_audit_enabled: false

  - id: nacionalidade
    name_pt: "Nacionalidade"
    name_en: "Nationality"
    aliases_pt: ["nacionalidade", "naturalidade", "país de origem"]
    aliases_en: ["nationality", "country_of_origin", "national_origin"]
    db_fields: ["nationality", "nacionalidade"]
    category: identity
    legal_basis: "CF Art. 5º"
    bias_audit_enabled: false

  - id: antecedentes_criminais
    name_pt: "Antecedentes Criminais"
    name_en: "Criminal Record"
    aliases_pt: ["antecedentes criminais", "antecedentes_criminais", "ficha criminal"]
    aliases_en: ["criminal_record", "criminal_history", "background_check"]
    db_fields: []
    category: legal_history
    legal_basis: "CNJ Resolução 65/08, Lei 7.210/84"
    bias_audit_enabled: false

  - id: saude_doenca
    name_pt: "Saúde/Doença"
    name_en: "Health/Disease"
    aliases_pt: ["saúde", "saude", "doença", "doenca", "hiv", "aids"]
    aliases_en: ["health", "disease", "hiv", "aids", "medical_condition"]
    db_fields: []
    category: health
    legal_basis: "Lei 9.029/95, Lei 9.313/96"
    bias_audit_enabled: false

  - id: filiacao_sindical
    name_pt: "Filiação Sindical"
    name_en: "Union Membership"
    aliases_pt: ["filiação sindical", "filiacao_sindical", "sindicato"]
    aliases_en: ["union_membership", "union", "labor_union"]
    db_fields: []
    category: association
    legal_basis: "CLT Art. 543, CF Art. 8º"
    bias_audit_enabled: false

  - id: aparencia_fisica
    name_pt: "Aparência Física"
    name_en: "Physical Appearance"
    aliases_pt: ["aparência física", "aparencia_fisica", "aparência"]
    aliases_en: ["physical_appearance", "appearance", "looks"]
    db_fields: []
    category: identity
    legal_basis: "Lei 9.029/95"
    bias_audit_enabled: false

  - id: regiao
    name_pt: "Região/Origem Geográfica"
    name_en: "Region/Geographic Origin"
    aliases_pt: ["região", "regiao", "origem geográfica"]
    aliases_en: ["region", "geographic_origin", "location"]
    db_fields: ["location_state", "location_city"]
    category: socioeconomic
    legal_basis: "CF Art. 5º (igualdade)"
    bias_audit_enabled: true
    bias_audit_dimension: region
```

### Arquivo canônico: `app/config/fairness_post_check.yaml`

**Linhas:** 39  |  **Bytes:** 897

```yaml
# Fairness Post-Check Configuration
# Defines which domains require fairness analysis on agent OUTPUT.
#
# decision_domains: domains whose outputs (rankings, scores, evaluations)
# are checked for bias. Soft warnings only — never blocks.
#
# To add a domain: add its domain_id to the list below.
# To disable post-check entirely: set enabled: false.

enabled: true

decision_domains:
  - pipeline
  - pipeline_transition
  - cv_screening
  - sourcing
  - autonomous
  - talent_pool
  - recruiter_assistant

# Score field names to look for in DomainResponse.data when checking
# ranking/scoring fairness (demographic distribution analysis).
score_fields:
  - score
  - ranking
  - match_score
  - wsi_score
  - fit_score
  - confidence
  - overall_score

# Ranking list field names in DomainResponse.data
ranking_fields:
  - candidates
  - results
  - ranked_candidates
  - shortlist
  - matches
```

---

*Bundle gerado em 2026-04-24 | Fonte: `lia-agent-system/` no Replit | MD5 sincronizado Mac ↔ Replit*
