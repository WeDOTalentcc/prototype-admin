# Compensation Modeling — Best Practices em ATS/HR Tech

> **Contexto**: Insumo da Fase 2 (PRV) do plano `vams-conectar-ao-replit-effervescent-fairy.md`. Síntese de pesquisa em plataformas líderes para nortear o desenho de UI/UX da seção "Política de Remuneração Variável" no WeDOTalent.
>
> **Autoria**: pesquisa via agent Explore (web research) + síntese local. Última atualização: 2026-04-30.

---

## Resumo Executivo

- **Workday** é a referência mais madura: modelo de Plans tipados (Salary, Bonus, Allowance, Equity, Commission) + Grades + Grade Profiles + Packages + Eligibility Rules.
- **Carta Total Comp** tem a melhor UX tabular: Mid auto-deriva Min/Max ±15% com inline edit.
- **Greenhouse e Lever** focam em workflow simples (Base + Bonus oficiais); resto é custom field + approval workflow para offers fora-da-banda.
- **Levels.fyi** tem o melhor preview de pacote total stacked.
- **Gupy/Kenoby (BR)**: informação pública limitada — não modelam PRV publicamente como objeto.
- **Diferencial competitivo WeDOTalent**: PLR/PPR brasileiros nativos (Lei 10.101/2000), tributação BR, LGPD-by-design.

---

## 1. Plataformas analisadas

| Plataforma | Modelo de Compensation | Diferencial |
|---|---|---|
| **Workday** | Plans tipados (Salary/Bonus/Allowance/Equity/Commission) + Grades + Grade Profiles + Packages + Eligibility Rules | Mais maduro do mercado; alta complexidade |
| **Carta Total Comp** | Tabela inline Min/Mid/Max com Mid auto-deriva ±15%; preview de benchmarks; versionamento explícito | UX premium para inline editing |
| **Greenhouse Recruiting** | Standardized: Base + Bonus oficiais; resto custom; pay rationale obrigatório fora-da-banda | Simplicidade + governance |
| **Lever** | Bandas por role; approval workflow condicionado a min/max; custom fields em offers | Approval gating |
| **Lattice** | Tabela com colunas configuráveis pelo usuário | Flexibilidade UI |
| **Levels.fyi** | Preview de pacote total stacked (base + bonus + RSU + sign-on) com vesting curves | Inspiração para preview lateral |
| **Ravio / Workleap** | Min/Mid/Max ±15-20%; três trilhas (IC/Manager/Exec) | Convergência de mercado |
| **Chief of Staff Network** | Bandas por nível com transparência interna | Comunicação |
| **Gupy / Kenoby (BR)** | Informação pública limitada | n/a |
| **SmartRecruiters** | Approval thresholds; sem banda canônica | Governance |

---

## 2. Doze (12) Best Practices consolidadas

1. **Salary bands em tabela editável inline** (linha por nível, colunas Min/Mid/Max). Permite ver toda a estrutura de uma vez.
2. **Verbas variáveis como tipos discriminados** (`kind`: plr | bonus | commission | equity | spot_bonus | ppr). Nunca um único campo "bônus" amorfo.
3. **Preview lateral em tempo real**: input "cargo + senioridade" → output "salário mediano R$ X + PLR Y% + bônus até Z% = pacote total estimado R$ W".
4. **Versionamento explícito**: "Política V1.2 (efetivo 2026-01-01 → 2026-12-31, aprovado por X em Y)". Histórico imutável.
5. **Elegibilidade como facets** (departamento × seniority × role) com chips multi-select.
6. **Mid auto-deriva Min/Max ±15-20%** (default editável). Reduz fricção; UI mais rápida.
7. **Permission gating** por papel: quem pode editar, aprovar, visualizar. Escalável para org maduras.
8. **Approval workflow** para offers fora-da-banda: rationale obrigatório, route para CEO/HR.
9. **Multi-moeda native** (BRL default, USD/EUR opcional). Empresas globais.
10. **Compatibilidade nativa PLR/PPR brasileiros** (Lei 10.101/2000): tipo de cálculo, periodicidade, base de incidência. Gap em Greenhouse/Lever/Workday.
11. **LGPD-by-design**: masking PII, consent log, audit trail.
12. **Audit trail** para toda mudança: compliance + debug. `revision_history` jsonb com user, timestamp, diff.

---

## 3. Doze (12) Anti-patterns a evitar

1. **JSON cru visível ao usuário**. Recrutador não deve ver `{"items":[{"kind":"plr",...}]}`.
2. **Formulário longo monolítico** sem agrupamento. Quebrar em sub-tabs ou seções colapsáveis.
3. **Falta de preview do impacto**. Editar uma banda sem ver "isso afeta 12 vagas" é cego.
4. **Forçar "tudo ou nada"**. PRV deve ser opcional por vaga (nem toda vaga tem PLR).
5. **Hardcoded em moeda BRL** sem suporte multi-moeda futuro.
6. **Sem versionamento**. Impossível auditar mudança histórica ou justificar decisão de offer.
7. **Elegibilidade em campo livre** (texto solto). Usar facets estruturadas.
8. **Sem validação de overlap** entre policies (duas PRVs concorrentes para mesma seniority).
9. **Schemas que misturam conceitos**: `salary_min` direto na policy E em uma sub-tabela "salary_bands".
10. **Sem rollback** em caso de aprovação errada. Toda mudança deve ser reversível.
11. **UI que não escala** para 50+ políticas. Pensar em busca, filtro, paginação desde o início.
12. **Permission flat** (todos podem tudo). Escalar com role-based access control.

---

## 4. Desenho recomendado para WeDOTalent

### 4.1 Estrutura de sub-tabs no `CompensationPolicyFormModal`

| Sub-tab | UI | Campos-chave |
|---|---|---|
| **Bandas Salariais** | Tabela inline editável | Linha por nível (Junior/Pleno/Sênior/Staff/Principal); colunas Min/Mid/Max; Mid auto-deriva ±15% |
| **Verbas Variáveis** | Tabela tipada (linhas com `kind` discriminator) | PLR, PPR, Bônus, Comissão, Spot Bonus, Equity. Cada `kind` tem sub-form. |
| **Equity** | Opcional (cliffs, vesting curves) | Tipo (RSU/options/phantom), cliff, vesting period, refresh |
| **Elegibilidade** | Facets multi-select | Departamento × Seniority × Role |
| **Vigência & Aprovação** | Campos + timeline | `effective_from/until`, `approved_by`, `version`, `revision_history` |

### 4.2 Schema interno de `variable_compensation` (jsonb)

```json
{
  "items": [
    {
      "kind": "plr",
      "name": "PLR Anual 2026",
      "base": "salary_anual",
      "value_pct": 15,
      "frequency": "annual",
      "trigger": "goal_achievement",
      "trigger_details": { "metric": "EBITDA", "threshold_pct": 80 },
      "applicable_seniority": ["senior", "staff"]
    },
    {
      "kind": "bonus",
      "name": "Bônus Meta Trimestral",
      "base": "salary_mensal",
      "min_pct": 0,
      "max_pct": 30,
      "frequency": "quarterly",
      "trigger": "kpi",
      "kpi": "team_okr_score"
    },
    {
      "kind": "commission",
      "name": "Comissão Vendas",
      "base": "revenue",
      "tiers": [
        { "from_pct": 0, "to_pct": 80, "commission_pct": 2 },
        { "from_pct": 80, "to_pct": 120, "commission_pct": 3.5 },
        { "from_pct": 120, "to_pct": null, "commission_pct": 5 }
      ]
    },
    {
      "kind": "ppr",
      "name": "PPR Lei 10.101/2000",
      "base": "result",
      "value_details": "Negociado anualmente com sindicato",
      "frequency": "annual"
    }
  ]
}
```

### 4.3 Preview lateral (sidebar persistente)

Recalcula em tempo real ao editar:

- **Input**: cargo (autocomplete) + seniority (chips)
- **Output cards stacked**:
  - 💰 Salário base (mediano da banda): R$ X
  - 🎯 PLR (15% anual): R$ Y
  - 📈 Bônus meta (até 30% trimestral): R$ Z
  - 🏥 Plano de saúde (mensal): R$ W
  - **Total anual estimado: R$ TOTAL**

### 4.4 Diferencial brasileiro (Lei 10.101/2000 — PLR/PPR)

- `kind: "plr"` → Participação nos Lucros e Resultados (PLR): isento de INSS para empregado se pago no máx 2x/ano.
- `kind: "ppr"` → Participação nos Resultados (PPR): vinculado a metas, regulado por convenção coletiva.
- Validação backend: alertar se PLR pago > 2x/ano (perda de vantagem fiscal).

---

## 5. LGPD & Fairness

- **PII em policies**: `approved_by`, `created_by` armazenados como user_id (UUID), nunca em texto livre.
- **Auditoria**: `revision_history` jsonb com user, timestamp, diff (sem PII em valores).
- **Fairness rule (Fase 4 — `// TODO(FAIRNESS:001)` em fairness_guard)**: PRV não pode ter elegibilidade por raça/gênero/idade/estado civil. Bloquear payload com `applicable_*` contendo termos como "homem"/"mulher"/"raça".
- **PRV idêntico para roles equivalentes**: alertar se duas roles do mesmo seniority têm `bonus_pct` divergente sem justificativa em `revision_history`.

---

## 6. Referências externas (URLs)

1. [Greenhouse — Standardized compensation fields](https://support.greenhouse.io/hc/en-us/articles/13250466091803-Standardized-compensation-fields-overview)
2. [Lever — Custom fields in Data Explorer](https://help.lever.co/hc/en-us/articles/20087313612957-Data-Explorer-Incorporating-custom-fields-into-reports)
3. [Workday Compensation Architecture (Workday Navigator)](https://workdaynavigator.com/blog/workday-compensation-architecture/)
4. [Workday Compensation Datasheet (PDF)](https://www.workday.com/content/dam/web/en-us/documents/datasheets/datasheet-workday-compensation.pdf)
5. [Carta Total Comp landing](https://carta.com/equity-management/compensation/)
6. [Carta Total Comp Release Notes](https://releasenotes.carta.com/label/21554)
7. [Rippling + Carta Compensation Bands](https://www.rippling.com/blog/rippling-carta-compensation-bands)
8. [Lattice — Compensation Bands Page Overview](https://help.lattice.com/hc/en-us/articles/6478068511639-Compensation-Bands-Page-Overview)
9. [Levels.fyi Total Compensation Calculator](https://www.levels.fyi/calculator/)
10. [Ravio — compensation framework](https://ravio.com/blog/what-to-include-in-a-best-practice-compensation-framework)
11. [Chief of Staff Network — Designing Compensation Bands](https://www.chiefofstaff.network/blog/designing-compensation-bands-a-comprehensive-guide)
12. [Workleap — Guide to Building Pay Bands](https://workleap.com/blog/guide-to-building-pay-bands)
13. [Lever Salary Transparency](https://www.lever.co/blog/salary-transparency/)
14. [Greenhouse blog — Recruit top talent with competitive compensation](https://www.greenhouse.com/blog/recruit-top-talent-with-competitive-compensation)

---

## 7. Próximos passos (mapeados no plano)

- ✅ Best practices consolidadas (este doc)
- ⏳ Fase 2.2: reescrever model `compensation_policy.py` alinhado ao schema Rails canonical (23 cols)
- ⏳ Fase 2.3: migration alembic
- ⏳ Fase 2.4: repository + router `/api/v1/company/compensation-policies`
- ⏳ Fase 2.5: frontend `compensation-policies/` com 5 sub-tabs + preview lateral
- ⏳ Fase 2.6: proxy `/api/backend-proxy/company/compensation-policies/`
- ⏳ Fase 2.7: bloco editável em Configurações → Dados da Empresa
- ⏳ Fase 2.9: testes pytest + jest

Hooks marcados para integração futura com Wizard LIA: ver §11 do plano (`// TODO(WIZARD-INT)`).
