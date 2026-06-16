# Política — `require_company=False` em `@tool_handler`

**Versão:** 1.0
**Vigência:** desde 2026-04-17
**Owner:** Compliance + Tech Lead Backend
**Referência:** AUDIT FINAL 2026-04 (item F8 / W7-residual)

---

## 1. Princípio

O decorator `@tool_handler(domain, require_company=True)` é o **default fail-closed**:
qualquer tool que receba ou produza dados de uma empresa deve receber `company_id`
no contexto de execução, sob pena de `RuntimeError`. A flag `require_company=False`
é uma **isenção** — só pode ser usada em tools cujo escopo é genuinamente
*tenant-agnostic* (sem leitura/escrita em dados da empresa).

Cada uso de `require_company=False` em produção precisa cumprir **todos** os critérios:

1. **Sem acesso a banco** com filtro por `company_id`. Tools que consultam tabelas
   tenant-scoped (`vacancy_candidates`, `job_vacancies`, `interviews`, `candidates`,
   `communication_logs`, etc.) **não podem** receber a isenção.
2. **Sem efeitos colaterais sobre dados tenant** (sem create/update/delete em
   entidades de uma empresa).
3. **Comentário inline obrigatório** na linha imediatamente acima do decorator,
   no formato `# require_company=False kept: <razão>`.
4. **Cobertura por module gating** quando o tool depende de plano/feature flag —
   o flag substitui o controle por tenant para evitar exposição lateral.

---

## 2. Inventário canônico (2026-04-17)

Existem **19 ocorrências** de `require_company=False` em `app/domains/**/tools/` e
`app/domains/**/agents/*_tool_registry.py` (auditoria recompilada do report 2026-04
que estimava 23 com base em grep histórico). Todas têm comentário `kept:` justificando.

| # | Arquivo | Linha | Tool | Justificativa | Gate adicional |
|---|---------|-------|------|---------------|----------------|
| 1 | `talent_intelligence/tools/skills_ontology_tools.py` | 20 | get_skill_ontology | Ontologia global de skills — tenant-agnostic | `module="talent_intelligence_pro"` |
| 2 | `talent_intelligence/tools/skills_ontology_tools.py` | 72 | get_skill_adjacency | Grafo global de adjacência — tenant-agnostic | `module="talent_intelligence_pro"` |
| 3 | `talent_intelligence/tools/market_intelligence_tools.py` | 19 | get_market_intelligence | Dados públicos de mercado — tenant-agnostic | `module="talent_intelligence_pro"` |
| 4 | `autonomous/agents/autonomous_tool_registry.py` | 611 | (validate wizard) | Delegates a wizard validator — pure schema validation | n/a |
| 5 | `autonomous/agents/autonomous_tool_registry.py` | 1140 | (consolidate context) | Consolida contexto provido pelo caller — sem DB | n/a |
| 6 | `autonomous/agents/autonomous_tool_registry.py` | 1161 | (clarification question) | Devolve pergunta de clarification ao usuário — sem DB | n/a |
| 7 | `hiring_policy/agents/policy_tool_registry.py` | 235 | (FG validation) | FairnessGuard sobre texto de policy — sem dados tenant | n/a |
| 8 | `hiring_policy/agents/policy_tool_registry.py` | 479 | (industry benchmarks) | Lookup em dict estático `INDUSTRY_BENCHMARKS` | n/a |
| 9 | `hiring_policy/agents/policy_tool_registry.py` | 574 | (impact descriptions) | Dict estático de descrições de impacto | n/a |
| 10 | `pipeline/agents/pipeline_tool_registry.py` | 337 | (NLP intent) | NLP/regex puro sobre texto de input | n/a |
| 11 | `pipeline/agents/pipeline_tool_registry.py` | 428 | (stage transition) | Lógica pura de transição de etapa | n/a |
| 12 | `pipeline/agents/pipeline_tool_registry.py` | 477 | (stub echo) | Stub que devolve dict echo — sem DB | n/a |
| 13 | `pipeline/agents/pipeline_tool_registry.py` | 493 | (message tone) | Formata tom/estilo da mensagem — sem DB | n/a |
| 14 | `pipeline/agents/pipeline_tool_registry.py` | 513 | (FG text check) | FairnessGuard sobre texto — sem DB | n/a |
| 15 | `recruiter_assistant/agents/kanban_tool_registry.py` | 25 | (FG text check) | FairnessGuard sobre texto — sem DB | n/a |
| 16 | `recruiter_assistant/agents/kanban_tool_registry.py` | 833 | (stub recipients) | Stub: ecoa recipients — sem write | n/a |
| 17 | `recruiter_assistant/agents/kanban_tool_registry.py` | 856 | (stub initiation) | Stub: devolve status de iniciação — sem write | n/a |
| 18 | `sourcing/agents/sourcing_tool_registry.py` | 22 | (echo criteria) | Ecoa critérios de input para chat state | n/a |
| 19 | `cv_screening/tools/cv_match_tool.py` | 26 | analyze_cv_match | **TBD por dono (cv_screening)** — tool aceita `company_id` opcional para chamada via chat global; quando presente, filtra `JobVacancy` por company_id. Revisar em ticket dedicado: avaliar flip para `require_company=True` com fail-closed. | n/a |

Distribuição final por domínio:
- pipeline: 5
- autonomous: 3
- hiring_policy: 3
- recruiter_assistant: 3
- talent_intelligence: 3
- cv_screening: 1
- sourcing: 1

> **Paridade YAML × código:** o registry YAML em `app/tools/yaml/` declara metadados
> sem flag de tenant; o controle de `require_company` vive **somente** no decorator
> `@tool_handler` no código. Se o YAML for estendido para conter essa flag no futuro,
> esta tabela passa a ser a fonte canônica e o YAML é gerado a partir dela.

---

## 3. Como adicionar uma nova exceção

1. Documente a tool aqui (acrescente linha à tabela acima) na mesma PR que adiciona
   o `require_company=False`. PRs que aumentam a contagem **sem atualizar este doc
   são bloqueadas em code review**.
2. Adicione o comentário inline `# require_company=False kept: <razão>`.
3. Se o tool depende de um plano/flag, prefira `module="<flag>"` para que
   `module_gating` faça o controle de acesso.
4. Solicite revisão do owner (Compliance + Tech Lead).

---

## 4. Como remover

Sempre que o tool passar a ler/escrever dados tenant, remova `require_company=False`
e o comentário associado, e remova a linha da tabela na mesma PR.

---

## 5. Verificação automática

O script `lia-agent-system/scripts/check_require_company_exemptions.py` (incluído via
F11) compara o grep do código vs. esta tabela. Discrepância => exit code 1.
Roda no job de CI **Backend — Lint & Test** após `ruff check`.
