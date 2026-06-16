# TODO: Consolidação policy → hiring_policy

**Data de criação:** 2026-03-13
**Sprint alvo:** VI (pós-Alpha 1 go-live)
**Status:** Pendente

---

## Contexto

Existem dois domínios de política de contratação na plataforma:

| Domínio | Caminho | Arquitetura | Status |
|---------|---------|-------------|--------|
| `hiring_policy` | `app/domains/hiring_policy/` | ReAct Agent consultivo | **Canônico** |
| `policy` | `app/domains/policy/` | Questionário linear 19 perguntas | **Deprecated** |

---

## Diferenças de System Prompt

### hiring_policy (`policy_system_prompt.py`)
- **Arquitetura:** ReAct Agent com ciclo Raciocínio-Ação-Observação
- **Personalidade:** Consultora estratégica de RH (não só coleta dados)
- **Validação:** `validate_policy_compliance` obrigatório antes de salvar
- **Anti-sycophancy:** `ANTI_SYCOPHANCY_BLOCK` e `NEGATION_DETECTION_BLOCK` injetados
- **Benchmarks setoriais:** `get_industry_benchmarks`, calibração por porte/setor
- **HITL:** Ações de alto impacto exigem aprovação formal
- **5 blocos temáticos:** Pipeline/Processo, Agendamento, Comunicação, Triagem, Autonomia LIA
- **FairnessGuard integrado:** Critérios proibidos listados explicitamente
- **Few-shot examples:** 8 cenários de exemplo (compliance, HITL, trade-offs)
- **Raciocínio consultivo:** explica consequências, trade-offs, benchmarks

### policy (`system_prompt.py` → `EXTRACTION_PROMPT` + `REPLY_PROMPT`)
- **Arquitetura:** Extração LLM + resposta sequencial (19 perguntas fixas)
- **Personalidade:** Assistente de coleta de dados
- **Sem validação de compliance** embutida no prompt
- **Sem anti-sycophancy**
- **Sem benchmarks setoriais**
- **Sem calibração por contexto**
- Dois prompts distintos: `EXTRACTION_PROMPT` (extrai valor) + `REPLY_PROMPT` (confirma e avança)

---

## Plano de Merge

### Fase 1 — Pré-condições (antes da Sprint VI)
- [ ] Mapear todos os importadores de `app.domains.policy` no codebase
- [ ] Verificar se `PolicySetupAgent` ainda é invocado em algum router/endpoint ativo
- [ ] Confirmar que `hiring_policy.PolicyReActAgent` cobre todos os casos de uso do questionário linear

### Fase 2 — Migração (Sprint VI)
- [ ] Redirecionar todos os importadores para `app.domains.hiring_policy`
- [ ] Migrar dados de configuração existentes criados via `policy` para o schema de `hiring_policy`
- [ ] Executar testes de regressão: `tests/unit/test_policy_*`

### Fase 3 — Remoção
- [ ] Remover `app/domains/policy/` inteiramente
- [ ] Remover referências em `main.py`, `ci.yml`, docs

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Dados persistidos pelo `PolicySetupAgent` em formato incompatível | Escrever migration Alembic se necessário |
| Endpoints públicos apontando para `policy` | Auditoria de routers antes da remoção |
| Testes quebrados | Rodar `pytest tests/ -k policy` antes e depois |

---

## Referência de Arquivos

```
app/domains/hiring_policy/
  __init__.py                      ← domínio canônico (documentado)
  domain.py                        ← (verificar conteúdo)
  agents/
    policy_react_agent.py          ← agente principal
    policy_system_prompt.py        ← prompt ReAct consultivo
    policy_stage_context.py
    policy_tool_registry.py

app/domains/policy/
  __init__.py                      ← DEPRECATED (documentado)
  agents/
    system_prompt.py               ← EXTRACTION_PROMPT + REPLY_PROMPT (linear)
    agent.py
    stage_context.py
    tool_registry.py
```
