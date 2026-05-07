# ADR-031 — Protected Attributes YAML Governance + LGPD/Fairness Compliance

**Status**: Superseded by ADR-031 v2 (2026-05-06 — v1 P0 premise was wrong; loader path bug fixed in commit ca6f004cf; see ADR-031-v2-protected-attributes-loader-fix.md)
**Data**: 2026-05-06
**Severity**: 🔴 P0 — LGPD/Fairness rodando fail-open em produção
**Sprint**: Q2 Canonical Refactor (Sprint 1 — Estabilização)

---

## Contexto

Audit 2026-05-06 descobriu que o arquivo `app/shared/config/protected_attributes.yaml` **NÃO EXISTE** em produção. Toda execução do backend FastAPI loga:

```
[ProtectedAttributes] Failed to load YAML: [Errno 2] No such file or directory:
'/home/runner/workspace/lia-agent-system/app/shared/config/protected_attributes.yaml'
```

Verificado:

```
$ grep -rn "protected_attributes.yaml" app/
app/shared/compliance/fairness_guard.py:516:# Source of truth: config/protected_attributes.yaml
app/shared/compliance/protected_attributes.py:25: 
  os.path.dirname(__file__), "..", "..", "app", "config", "protected_attributes.yaml"
```

### Impacto

Esse arquivo é a fonte de verdade para **atributos protegidos pela LGPD e fairness**:
- Gênero, raça, religião, idade, estado civil, orientação sexual, deficiência
- Termos discriminatórios em descrições de vagas
- Categorias para fairness check em rankings

**Sem o YAML, FairnessGuard roda fail-open** — não bloqueia conteúdo que deveria bloquear:
- ❌ Job descriptions com termos discriminatórios passam
- ❌ Rankings podem ter adverse impact não detectado
- ❌ EEOC/LGPD compliance check não aplica
- ❌ Sentry breadcrumbs sobre proteção podem vazar PII (sem masking config)

### Severidade

**P0** porque:
- Compliance LGPD exigido por contrato com clientes
- Auditoria externa pode falhar
- Bug latente desde início do projeto (Mar 2026)

---

## Decisão

### 1. **Criar `protected_attributes.yaml` com schema canônico**

Localização canônica: `app/config/protected_attributes.yaml` (NÃO em `app/shared/config/` — código atualizado para apontar para `app/config/`).

Schema:

```yaml
metadata:
  version: "1.0"
  updated_at: "2026-05-06"
  source: "LGPD Art. 5º + Lei 9.029/95 (anti-discriminação) + EEOC Title VII"
  governance: "ADR-031 — Protected Attributes YAML Governance"

# Atributos protegidos (LGPD Art. 11 dados sensíveis)
protected_attributes:
  gender:
    aliases: ["sexo", "gênero", "gender"]
    forbidden_terms_pt:
      - "preferencialmente homem"
      - "preferencialmente mulher"
      - "apenas mulheres"
      - "apenas homens"
      # ...
    fairness_action: "block"

  race_ethnicity:
    aliases: ["raça", "etnia", "cor"]
    forbidden_terms_pt:
      - "preferência racial"
      - "raça branca"
      # ...
    fairness_action: "block"

  age:
    aliases: ["idade"]
    forbidden_terms_pt:
      - "até 30 anos"
      - "máximo 35 anos"
      - "jovem dinâmico"
      - "boa aparência"
      # ...
    fairness_action: "warn"  # algumas restrições etárias são legais (estagiário)

  marital_status:
    # ...

  sexual_orientation:
    # ...

  disability:
    # ...

  religion:
    # ...

# Termos genéricos discriminatórios
discriminatory_terms:
  pt:
    - "boa aparência"
    - "ambiente jovem"
    # ...
  en:
    - "young dynamic"
    # ...

# Categorias para EEOC adverse impact analysis
eeoc_categories:
  - protected_class: "gender"
    threshold: 0.8  # 4/5 rule
  - protected_class: "race"
    threshold: 0.8
  # ...
```

### 2. **Schema validation via JSON Schema**

`app/config/protected_attributes_schema.json` valida estrutura. Loader em `protected_attributes.py` valida no startup. Falha startup se YAML inválido.

### 3. **Sensor pre-commit**

`scripts/check_protected_attributes_yaml_present.py`:
- Verifica que `app/config/protected_attributes.yaml` existe
- Valida schema (required keys present)
- Verifica que todos os 7 atributos protegidos LGPD estão presentes
- Blocking from day 1 (zero tolerance)

### 4. **Versionamento + governance**

- Mudanças no YAML requerem ADR adicional (governance gate)
- `metadata.version` semver
- `metadata.updated_at` para auditoria
- CI validates schema on every PR

### 5. **Observability**

- Sentry breadcrumb `protected_attributes_loaded` no startup com count de termos
- Métrica Prometheus: `protected_attributes_terms_total{type}`
- Log warning se algum check ainda fail-open após Sprint 1

---

## Implementação (Sprint 1 — IMEDIATA)

| Task | Esforço | Skill |
|---|---|---|
| Pesquisar termos discriminatórios PT-BR + EN (LGPD references) | 3h | `/production-quality:modules:compliance-risk` |
| Criar `app/config/protected_attributes.yaml` | 2h | governance |
| Criar JSON Schema validator | 1h | `/canonical-fix` |
| Update `protected_attributes.py` loader: fail-fast se YAML missing | 1h | `/harness-engineering` |
| Tests: FairnessGuard with YAML (positive + negative) | 3h | `/tdd-workflow` |
| Sensor `check_protected_attributes_yaml_present` blocking | 1h | `/harness-engineering` |
| Smoke test E2E em staging | 1h | manual |
| **Total Sprint 1** | **~12h** | |

---

## Consequências

### Positivas
- ✅ LGPD/Fairness compliance funcional (não mais fail-open)
- ✅ Auditoria externa pode validar
- ✅ Rankings com adverse impact detection real
- ✅ Schema canonical para futuros atributos
- ✅ Bug latente fechado

### Negativas
- ⚠️ Algumas vagas existentes podem ser flagged como discriminatórias (cleanup necessário)
- ⚠️ Performance: lookup em YAML carregado em memória (negligível, ~1ms)

### Reversibilidade
Reversível sempre (deletar YAML → fail-open novamente). Mas **NÃO REVERTER** — é compliance crítico.

---

## Métricas de sucesso

- ✅ `protected_attributes.yaml` existe + valid schema
- ✅ Startup logs: zero "Failed to load YAML"
- ✅ FairnessGuard tests: 100% coverage (LGPD 7 atributos)
- ✅ Sensor blocking ativo
- ✅ Sentry breadcrumb confirma loaded
- 📊 Métrica: # vagas existentes flagged (analyse e remediar)

---

## Referências

- LGPD Art. 5º (definições) + Art. 11 (dados sensíveis)
- Lei 9.029/95 (proibição discriminação no recrutamento)
- EEOC Title VII (US standard)
- 4/5 rule for adverse impact analysis
- ADR-006 (No PII in logs) — complementar
- Skill `/production-quality:modules:compliance-risk`
- Sensor pre-commit governance pattern
